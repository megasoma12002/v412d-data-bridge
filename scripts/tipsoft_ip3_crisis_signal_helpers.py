#!/usr/bin/env python3
"""Vendored crisis-signal helpers from tipsoft 0kbh (unmerged PR #427).

SOAK-SAFE · detection utilities only — used by cliff-vs-grind (0kbk) and
major-DD atlas (0kbl) Stage A packs.
Standalone: does not require 0kbh/0kbi/0kbj scripts on the branch.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from cool_c8_proxy_observe_helpers import build_cool_c8_exposure
from e45_paper_harness import window_stats
from research_metric_helpers import mdd_delta_pp
from stagea_screen_helpers import (
    load_nav_csv as _load_nav,
    nav_from_returns as _nav_from_returns,
    pack_nav_windows as _pack,
    returns_from_nav as _returns,
    tip_lift as _tip,
    window_delta as _delta,
)

ROOT = Path(__file__).resolve().parents[1]
ALIGN = ROOT / "repro" / "research-live-align-gap-stagea" / "outputs"
LIVESTACK = ROOT / "repro" / "fin-sat-path3-path4-livestack-twin-stageb" / "outputs"
PX_0050 = ROOT / "data" / "telecom_0050_complete" / "0050_2010_latest_ohlcv.csv"
VIX_CANDIDATES = (
    ROOT / "data" / "market" / "vix.csv",
    ROOT / "data" / "market" / "VIX.csv",
    ROOT / "data" / "def_proxies" / "vix.csv",
)

BASE_ID = "L4_LIVE_P3_WITHIN"
SOFT_ID = "L1_SOFT_T1"
MAR2020_START = date(2020, 2, 20)
MAR2020_END = date(2020, 3, 23)
Y2020_START = date(2020, 1, 1)
Y2020_END = date(2020, 12, 31)
ALERT_Q = 0.90
def _ann_vol(r: pd.Series, win: int) -> pd.Series:
    """Lag-1 causal realized vol (annualized)."""
    return r.shift(1).rolling(int(win), min_periods=max(5, int(win) // 3)).std() * np.sqrt(252.0)


def _dd_from_peak(nav_s: pd.Series, win: int = 63) -> pd.Series:
    peak = nav_s.rolling(int(win), min_periods=5).max()
    return (nav_s / peak - 1.0).fillna(0.0)


def _proxy_mdd63(nav_s: pd.Series) -> pd.Series:
    peak = nav_s.cummax()
    dd = nav_s / peak - 1.0
    return dd.rolling(63, min_periods=5).min().fillna(0.0)


def _load_0050_ohlcv(idx: pd.DatetimeIndex) -> pd.DataFrame:
    px = pd.read_csv(PX_0050, parse_dates=["date"])
    px["date"] = pd.to_datetime(px["date"]).dt.normalize()
    close_col = "adjusted_close" if "adjusted_close" in px.columns else "close"
    out = px.set_index("date")[["open", "high", "low", "close", close_col]].astype(float)
    out = out.rename(columns={close_col: "adj_close"}).sort_index()
    return out.reindex(idx).ffill()


def _try_load_vix(idx: pd.DatetimeIndex) -> pd.Series | None:
    for path in VIX_CANDIDATES:
        if not path.exists():
            continue
        df = pd.read_csv(path)
        dcol = "date" if "date" in df.columns else df.columns[0]
        vcol = next(
            (c for c in ("vix", "VIX", "close", "adj_close", "value") if c in df.columns),
            None,
        )
        if vcol is None:
            continue
        s = df.assign(date=pd.to_datetime(df[dcol]).dt.normalize()).set_index("date")[vcol]
        return s.astype(float).sort_index().reindex(idx).ffill()
    return None


def _fwd_mdd(r: pd.Series, n: int) -> pd.Series:
    """Forward N-day max drawdown magnitude (positive = stress). Causal labels only."""
    # Path of cumulative return over next n days from each t (excluding t itself)
    vals = r.to_numpy(dtype=float)
    out = np.full(len(vals), np.nan)
    for i in range(len(vals) - n):
        path = np.cumprod(1.0 + vals[i + 1 : i + 1 + n])
        peak = np.maximum.accumulate(path)
        dd = path / peak - 1.0
        out[i] = float(-dd.min())  # magnitude
    return pd.Series(out, index=r.index)


def _fwd_ret(r: pd.Series, n: int) -> pd.Series:
    vals = r.to_numpy(dtype=float)
    out = np.full(len(vals), np.nan)
    for i in range(len(vals) - n):
        out[i] = float(np.prod(1.0 + vals[i + 1 : i + 1 + n]) - 1.0)
    return pd.Series(out, index=r.index)


def _consec_down(r: pd.Series) -> pd.Series:
    """Lag-1 count of consecutive down days ending yesterday."""
    down = (r < 0).astype(int)
    # count streak ending at t, then shift(1)
    streak = np.zeros(len(r), dtype=float)
    for i in range(len(r)):
        if i == 0:
            streak[i] = float(down.iloc[i])
        else:
            streak[i] = float(down.iloc[i]) * (streak[i - 1] + 1.0) if down.iloc[i] else 0.0
    return pd.Series(streak, index=r.index).shift(1)


def _pearson(x: pd.Series, y: pd.Series) -> float | None:
    m = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(m) < 80:
        return None
    v = float(m["x"].corr(m["y"], method="pearson"))
    return None if v != v else v


def _spearman(x: pd.Series, y: pd.Series) -> float | None:
    """Spearman via average ranks + Pearson (no scipy dependency)."""
    m = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(m) < 80:
        return None
    rx = m["x"].rank(method="average")
    ry = m["y"].rank(method="average")
    v = float(rx.corr(ry, method="pearson"))
    return None if v != v else v


def _binary_prf(y_true: pd.Series, y_pred: pd.Series) -> dict[str, float | None]:
    m = pd.DataFrame({"t": y_true.astype(bool), "p": y_pred.astype(bool)}).dropna()
    if len(m) < 20:
        return {"precision": None, "recall": None, "f1": None, "hit_rate": None, "n": 0}
    tp = int((m["t"] & m["p"]).sum())
    fp = int((~m["t"] & m["p"]).sum())
    fn = int((m["t"] & ~m["p"]).sum())
    tn = int((~m["t"] & ~m["p"]).sum())
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) else 0.0
    hit = (tp + tn) / len(m)
    return {
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1": round(f1, 4),
        "hit_rate": round(hit, 4),
        "n": int(len(m)),
    }


def _alert_mask(feat: pd.Series, *, stress_high: bool, q: float = ALERT_Q) -> pd.Series:
    x = feat.dropna()
    if len(x) < 50:
        return pd.Series(False, index=feat.index)
    if stress_high:
        thr = float(x.quantile(q))
        return (feat >= thr).fillna(False)
    thr = float(x.quantile(1.0 - q))
    return (feat <= thr).fillna(False)


def _median_lead_days(
    alert: pd.Series,
    *,
    window_start: date,
    trough: pd.Timestamp,
) -> float | None:
    """Median calendar lead of first alert in [window_start, trough] before trough."""
    a = alert.copy()
    if not isinstance(a.index, pd.DatetimeIndex):
        # Allow callers to pass a date-aligned series; otherwise refuse.
        return None
    idx = pd.DatetimeIndex(pd.to_datetime(a.index))
    w0 = pd.Timestamp(window_start)
    mask = (idx >= w0) & (idx <= trough) & a.fillna(False).to_numpy()
    hits = idx[mask]
    if len(hits) == 0:
        return None
    first = pd.Timestamp(hits[0])
    return float((trough - first).days)


def build_panel() -> tuple[pd.DataFrame, dict[str, Any]]:
    l4_path = ALIGN / "nav_L4_LIVE_P3_WITHIN.csv"
    if not l4_path.exists():
        l4_path = LIVESTACK / "nav_LIVE_P3_WITHIN.csv"
    soft_path = ALIGN / "nav_L1_SOFT_T1.csv"
    l4 = _load_nav(l4_path)
    soft = _load_nav(soft_path)
    r_l4 = _returns(l4)
    r_soft = _returns(soft).reindex(r_l4.index).fillna(0.0)
    ohlcv = _load_0050_ohlcv(r_l4.index)
    px = ohlcv["adj_close"]
    r_mkt = px.pct_change().fillna(0.0)

    nav_l4_s = l4.set_index("date")["nav"].astype(float).reindex(r_l4.index).ffill()
    nav_soft_s = soft.set_index("date")["nav"].astype(float).reindex(r_l4.index).ffill()

    # Labels (not lagged — future info for scoring only)
    labels: dict[str, pd.Series] = {}
    for n in (5, 10, 20):
        labels[f"fwd_mdd_{n}"] = _fwd_mdd(r_l4, n)
        labels[f"fwd_ret_crash_{n}"] = -_fwd_ret(r_l4, n)  # positive = crash
        labels[f"fwd_mkt_mdd_{n}"] = _fwd_mdd(r_mkt, n)

    idx = r_l4.index
    in_mar = pd.Series(
        (idx.date >= MAR2020_START) & (idx.date <= MAR2020_END),
        index=idx,
    )
    in_y2020 = pd.Series(
        (idx.date >= Y2020_START) & (idx.date <= Y2020_END),
        index=idx,
    )
    labels["in_mar2020"] = in_mar.astype(float)
    labels["in_y2020"] = in_y2020.astype(float)

    # Soft/L4 NAV dd-from-peak crossing labels (same-day state; detectors are lag-1)
    for name, s in (("l4", nav_l4_s), ("soft", nav_soft_s)):
        dd = s / s.cummax() - 1.0
        for thr in (0.05, 0.08, 0.10):
            labels[f"{name}_dd_cross_{int(thr*100)}"] = (dd <= -thr).astype(float)

    # Detectors — all lag-1 causal
    feats: dict[str, pd.Series] = {}
    feats["rvol20_l4"] = _ann_vol(r_l4, 20)
    feats["rvol63_l4"] = _ann_vol(r_l4, 63)
    feats["rvol20_mkt"] = _ann_vol(r_mkt, 20)
    feats["rvol63_mkt"] = _ann_vol(r_mkt, 63)

    atr = ((ohlcv["high"] - ohlcv["low"]) / px.replace(0, np.nan)).fillna(0.0)
    feats["atr_like_20"] = atr.shift(1).rolling(20, min_periods=5).mean()

    for w in (60, 120, 200):
        ma = px.rolling(w, min_periods=max(30, w // 2)).mean()
        # negative when below MA → stress-high via -gap
        gap = (px / ma - 1.0).shift(1)
        feats[f"neg_gap_ma{w}"] = -gap
        feats[f"below_ma{w}"] = (px.shift(1) < ma.shift(1)).astype(float)

    feats["dd63_mkt"] = (-_dd_from_peak(px, 63)).shift(1)
    feats["dd63_l4"] = (-_dd_from_peak(nav_l4_s, 63)).shift(1)
    feats["dd63_soft"] = (-_dd_from_peak(nav_soft_s, 63)).shift(1)
    feats["proxy_mdd63_soft"] = (-_proxy_mdd63(nav_soft_s)).shift(1)

    cool_exp = build_cool_c8_exposure(idx, _proxy_mdd63(nav_soft_s))
    # COOL defending = exposure < 1; lag-1 (yesterday defending → today signal)
    feats["cool_defend_l1"] = (cool_exp < 0.999).astype(float).shift(1)
    # FUSE-like: Soft vs L4 trail prem (positive Soft premium bite when Soft>L4 briefly)
    soft_trail5 = r_soft.rolling(5, min_periods=3).sum().shift(1)
    l4_trail5 = r_l4.rolling(5, min_periods=3).sum().shift(1)
    fuse_prem = (soft_trail5 - l4_trail5).fillna(0.0)
    feats["fuse_prem_neg5"] = (-fuse_prem).clip(lower=0.0)
    feats["fuse_neg_flag"] = (fuse_prem < -0.005).astype(float)

    feats["consec_down_mkt"] = _consec_down(r_mkt)
    feats["consec_down_l4"] = _consec_down(r_l4)

    vix = _try_load_vix(idx)
    skipped: list[str] = []
    if vix is not None:
        feats["vix_l1"] = vix.shift(1)
        feats["vix_chg5_l1"] = vix.pct_change(5).shift(1)
    else:
        skipped.append("VIX proxy (no data file)")
    skipped.append("breadth (no series available)")

    panel = pd.DataFrame({"date": idx})
    panel = panel.set_index("date")
    for k, s in feats.items():
        panel[k] = s
    for k, s in labels.items():
        panel[k] = s
    panel["year2020_dummy"] = in_y2020.astype(float)

    meta = {
        "base_id": BASE_ID,
        "soft_id": SOFT_ID,
        "base_path": str(l4_path.relative_to(ROOT)),
        "soft_path": str(soft_path.relative_to(ROOT)),
        "n_days": int(len(panel)),
        "mar2020_window": [str(MAR2020_START), str(MAR2020_END)],
        "skipped_detectors": skipped,
        "feature_cols": sorted(feats.keys()),
        "label_cols": sorted(labels.keys()),
        "vix_available": vix is not None,
    }
    return panel.reset_index(), meta


def _rank_pct(s: pd.Series) -> pd.Series:
    return s.rank(method="average", pct=True)


def _orient_stress(x: pd.Series, y_primary: pd.Series) -> tuple[pd.Series, bool]:
    sp = _spearman(x, y_primary)
    stress_high = True if sp is None else (float(sp) >= 0)
    return (x if stress_high else -x), stress_high


def build_detector_arms(panel: pd.DataFrame) -> tuple[dict[str, pd.Series], dict[str, dict[str, Any]]]:
    """Minimal 0kbh singles + 0kbi AND champ for cliff/grind lift (vendored)."""
    p = panel.copy()
    p["date"] = pd.to_datetime(p["date"])
    p = p.set_index("date").sort_index()
    y_primary = p["fwd_mdd_10"]

    singles = (
        "rvol20_l4",
        "rvol63_l4",
        "atr_like_20",
        "neg_gap_ma200",
        "dd63_l4",
        "fuse_prem_neg5",
        "fuse_neg_flag",
        "cool_defend_l1",
        "proxy_mdd63_soft",
        "rvol20_mkt",
        "consec_down_mkt",
    )
    oriented: dict[str, pd.Series] = {}
    for col in singles:
        if col not in p.columns:
            continue
        xs, _ = _orient_stress(p[col], y_primary)
        oriented[col] = xs

    arms: dict[str, pd.Series] = {}
    meta: dict[str, dict[str, Any]] = {}
    for col, xs in oriented.items():
        name = f"base::{col}"
        arms[name] = xs
        meta[name] = {"family": "baseline", "alert_override": None}

    ranks = {c: _rank_pct(xs) for c, xs in oriented.items()}
    # 0kbi champ
    a, b = "rvol63_l4", "fuse_prem_neg5"
    if a in ranks and b in ranks:
        name = f"and::{a}&{b}"
        arms[name] = pd.concat([ranks[a], ranks[b]], axis=1).min(axis=1)
        meta[name] = {"family": "and_combo", "alert_override": None, "is_0kbi_champ": True}
    # useful OR pair from 0kbi HIT list
    for a2, b2 in (
        ("rvol20_l4", "atr_like_20"),
        ("rvol20_l4", "fuse_prem_neg5"),
        ("neg_gap_ma200", "dd63_l4"),
    ):
        if a2 in ranks and b2 in ranks:
            oname = f"or::{a2}|{b2}"
            arms[oname] = pd.concat([ranks[a2], ranks[b2]], axis=1).max(axis=1)
            meta[oname] = {"family": "or_combo", "alert_override": None}
    return arms, meta


def counterfactual_cash_gate(
    panel: pd.DataFrame,
    score: pd.Series,
    *,
    base_nav: pd.DataFrame,
    alert: pd.Series | None = None,
    window_start: date | None = None,
    window_end: date | None = None,
    label: str = "full",
) -> dict[str, Any]:
    """Illustrative only: lag-1 alert → cash on L4 returns; report held/MDD."""
    p = panel.copy()
    p["date"] = pd.to_datetime(p["date"])
    idx = p.set_index("date").index
    xs = score.reindex(idx)
    if alert is None:
        alert = _alert_mask(xs, stress_high=True, q=ALERT_Q)
    else:
        alert = alert.reindex(idx).fillna(False).astype(bool)
    r = _returns(base_nav)
    exp = pd.Series(np.where(alert.reindex(r.index).fillna(False), 0.0, 1.0), index=r.index)
    chal_r = (exp * r).astype(float)
    nav0 = float(base_nav["nav"].iloc[0])
    chal = _nav_from_returns(chal_r, nav0)
    base_w = _pack(base_nav)
    chal_w = _pack(chal)
    d = _delta(base_w, chal_w)
    tip = _tip(base_nav, chal)
    out: dict[str, Any] = {
        "note": "ILLUSTRATIVE ONLY — signal≠apply; no size-overlay / tip Soft promote",
        "label": label,
        "held_cagr_lift_pp": d["heldout_2019_plus"]["cagr_lift_pp"],
        "sealed_mdd_improve_pp": d["sealed_2023_plus"]["mdd_improve_pp"],
        "tipY_cagr_lift_pp": (tip.get("ytd") or {}).get("cagr_lift_pp"),
        "pct_cash_days": round(float((exp < 0.5).mean()) * 100, 2),
    }
    if window_start is not None and window_end is not None:
        base_m = window_stats(base_nav, window_start, window_end, min_days=5).get("max_drawdown")
        chal_m = window_stats(chal, window_start, window_end, min_days=5).get("max_drawdown")
        mar_imp = (
            None
            if base_m is None or chal_m is None
            else round(float(mdd_delta_pp(float(base_m), float(chal_m))), 4)
        )
        out["window"] = [str(window_start), str(window_end)]
        out["window_mdd_improve_pp"] = mar_imp
        out["base_window_mdd"] = None if base_m is None else round(float(base_m), 6)
        out["chal_window_mdd"] = None if chal_m is None else round(float(chal_m), 6)
    return out

