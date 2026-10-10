#!/usr/bin/env python3
"""2020 crisis / Mar cliff **signal detection** Stage A (0kbh).

SOAK-SAFE · PARALLEL paper research — **signal ≠ apply**.

Parent 0kbg crisis-overlay sandbox landed ``IP3_Y2020_CRISIS_SANDBOX_MDD_ONLY``
(size overlays hurt held). User follow-up: measure detectors as **signals** —
no LIVE wire · no tip Soft promote · no year-oracle · no size-overlay promote.

Question: which causal lag-1 features best **detect** Mar2020 cliff / 2020
crisis stress days on the L4 twin world (0050 / soft NAV / market), measured by
IC / hit-rate / lead days — without applying exposure?

Verdict taxonomy (SIGNAL Stage A):
- ``SIGNAL_HIT`` — IC/hit clear floors AND not only in-sample year dummy
- ``SIGNAL_WEAK`` / ``SIGNAL_NO_EDGE`` otherwise

Hard constraints:
- Soft KEEP · Path4 OFF · broker false · Exact T+1
- does **not** unlock soak freeze · does **not** recommend LIVE wire
- optional counterfactual cash-gate on top signal is **illustrative only**

Repro: ``PYTHONPATH=scripts python3 scripts/tipsoft_ip3_y2020_crisis_signal_stagea.py``
"""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from cool_c8_proxy_observe_helpers import build_cool_c8_exposure
from e45_paper_harness import window_stats
from ops_repro_ssot import write_ops_and_repro_pointer, write_repro_pointer
from research_metric_helpers import mdd_delta_pp
from stagea_screen_helpers import (
    load_nav_csv as _load_nav,
    nav_from_returns as _nav_from_returns,
    pack_nav_windows as _pack,
    returns_from_nav as _returns,
    tip_lift as _tip,
    utc_now_z as _utc,
    window_delta as _delta,
)

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "tipsoft-ip3-y2020-crisis-signal-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

ALIGN = ROOT / "repro" / "research-live-align-gap-stagea" / "outputs"
LIVESTACK = ROOT / "repro" / "fin-sat-path3-path4-livestack-twin-stageb" / "outputs"
PX_0050 = ROOT / "data" / "telecom_0050_complete" / "0050_2010_latest_ohlcv.csv"
VIX_CANDIDATES = (
    ROOT / "data" / "market" / "vix.csv",
    ROOT / "data" / "market" / "VIX.csv",
    ROOT / "data" / "def_proxies" / "vix.csv",
)

CHARTER_ID = "TIPSOFT_IP3_Y2020_CRISIS_SIGNAL_STAGEA_CHARTER"
SCREEN_ID = "TIPSOFT_IP3_Y2020_CRISIS_SIGNAL_STAGEA_SCREEN"
DECISION_ID = "TIPSOFT_IP3_Y2020_CRISIS_SIGNAL_STAGEA_DECISION_PACK"
REGISTER = "0kbh"
PARENTS = ("0kbg", "0kbf", "0kb4")
MECH = "TIPSOFT_IP3_Y2020_CRISIS_SIGNAL"
LABEL_TAG = "SIGNAL_PARALLEL"

BASE_ID = "L4_LIVE_P3_WITHIN"
SOFT_ID = "L1_SOFT_T1"

MAR2020_START = date(2020, 2, 20)
MAR2020_END = date(2020, 3, 23)
Y2020_START = date(2020, 1, 1)
Y2020_END = date(2020, 12, 31)

# Signal floors (detection, not apply)
IC_ABS_FLOOR = 0.08
# Mar hit evaluated inside local H1-2020 window (not full-sample accuracy)
HIT_FLOOR = 0.58
RECALL_MAR_FLOOR = 0.35
LEAD_DAYS_FLOOR = 3.0
FA_OUTSIDE_2020_CEIL = 0.12
YEAR_DUMMY_IC_ABS_CEIL = 0.55  # if |corr(feat, year2020)| this high → year-dummy risk
OOS_IC_ABS_FLOOR = 0.05  # IC vs stress excl. 2020 must clear this for HIT

# Binary alert threshold: top-quantile of feature (stress-high)
ALERT_Q = 0.90
# Local window for Mar crisis day labeling metrics
MAR_EVAL_START = date(2020, 1, 2)
MAR_EVAL_END = date(2020, 6, 30)


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


def _detector_verdict(row: dict[str, Any]) -> str:
    ic = row.get("ic_spearman_primary")
    hit = row.get("hit_rate_mar")
    recall = row.get("recall_mar")
    lead = row.get("median_lead_days")
    fa = row.get("fa_rate_outside_2020")
    yd = row.get("year2020_dummy_abs_ic")
    oos = row.get("ic_spearman_oos_ex2020")
    if ic is None or hit is None:
        return "INCOMPLETE"
    year_dummy = yd is not None and float(yd) >= YEAR_DUMMY_IC_ABS_CEIL
    oos_ok = oos is not None and abs(float(oos)) >= OOS_IC_ABS_FLOOR
    hit_ok = float(hit) >= HIT_FLOOR and (
        recall is not None and float(recall) >= RECALL_MAR_FLOOR
    )
    floors = (
        abs(float(ic)) >= IC_ABS_FLOOR
        and hit_ok
        and (lead is not None and float(lead) >= LEAD_DAYS_FLOOR)
        and (fa is None or float(fa) <= FA_OUTSIDE_2020_CEIL)
        and (not year_dummy)
        and oos_ok
    )
    if floors:
        return "SIGNAL_HIT"
    weak = abs(float(ic)) >= 0.04 or (
        hit is not None and float(hit) >= 0.54 and recall is not None and float(recall) >= 0.20
    )
    if weak and not year_dummy:
        return "SIGNAL_WEAK"
    if year_dummy and abs(float(ic)) >= IC_ABS_FLOOR:
        return "SIGNAL_WEAK"  # in-sample only
    return "SIGNAL_NO_EDGE"


def _champ_key(r: dict[str, Any]) -> tuple:
    """Rank detectors for Mar-cliff detection: IC × local hit/recall × lead."""
    ic = abs(float(r.get("ic_spearman_primary") or 0))
    hit = float(r.get("hit_rate_mar") or 0)
    rec = float(r.get("recall_mar") or 0)
    f1 = float(r.get("f1_mar") or 0)
    lead = r.get("median_lead_days")
    lead_v = 0.0 if lead is None or (isinstance(lead, float) and lead != lead) else float(lead)
    fa = float(r.get("fa_rate_outside_2020") or 1.0)
    # Prefer detectors that both correlate with fwd stress AND fire into Mar window
    composite = ic * (0.35 + hit) * (0.35 + rec + f1) * (0.5 + min(lead_v, 21.0) / 21.0)
    return (composite, ic, hit, rec, lead_v, -fa)


def _global_verdict(rows: list[dict[str, Any]]) -> tuple[str, dict[str, Any] | None]:
    if not rows:
        return "IP3_Y2020_CRISIS_SIGNAL_NO_EDGE", None
    hits = [r for r in rows if r.get("verdict") == "SIGNAL_HIT"]
    weaks = [r for r in rows if r.get("verdict") == "SIGNAL_WEAK"]
    if hits:
        champ = sorted(hits, key=_champ_key, reverse=True)[0]
        return "IP3_Y2020_CRISIS_SIGNAL_HIT", champ
    if weaks:
        champ = sorted(weaks, key=_champ_key, reverse=True)[0]
        return "IP3_Y2020_CRISIS_SIGNAL_WEAK", champ
    champ = sorted(rows, key=_champ_key, reverse=True)[0]
    return "IP3_Y2020_CRISIS_SIGNAL_NO_EDGE", champ


def _patch_register(verdict: str, champ: dict[str, Any] | None, day: str) -> None:
    reg = OPS / "HUMAN_DECISION_REGISTER.md"
    rt = reg.read_text(encoding="utf-8")
    c = champ or {}
    new_row = (
        f"| 0kbh | 2020 crisis / Mar cliff **signal detect** (no apply) | "
        f"**STAGE A `{verdict}`** ({day}) | "
        f"Parents 0kbg/0kbf/0kb4 · **SIGNAL/PARALLEL** · Exact T+1 lag-1 · "
        f"top `{c.get('detector')}` IC **{c.get('ic_spearman_primary')}** · "
        f"hit(Mar) **{c.get('hit_rate_mar')}** · lead **{c.get('median_lead_days')}**d · "
        f"FA≠2020 **{c.get('fa_rate_outside_2020')}** · "
        f"**signal≠apply** · soak freeze unchanged · Soft KEEP · Path4 OFF · "
        f"broker false · no live · `{DECISION_ID}.md` |"
    )
    lines = rt.splitlines()
    out: list[str] = []
    replaced = False
    for line in lines:
        if line.startswith("| 0kbh |"):
            out.append(new_row)
            replaced = True
        else:
            out.append(line)
    if not replaced:
        insert_at = None
        for i, line in enumerate(out):
            if line.startswith("| 0kbf |") or line.startswith("| 0kbg |"):
                insert_at = i + 1
                break
        if insert_at is None:
            for i, line in enumerate(out):
                if line.startswith("| 0kb4 |"):
                    insert_at = i + 1
                    break
        if insert_at is not None:
            out.insert(insert_at, new_row)
        else:
            out.append(new_row)
    reg.write_text("\n".join(out) + "\n", encoding="utf-8")


def _patch_ops_status(verdict: str, champ: dict[str, Any] | None, day: str) -> None:
    ops = OPS / "OPS_STATUS.md"
    ot = ops.read_text(encoding="utf-8")
    c = champ or {}
    line = (
        f"**Y2020 crisis signal detect (SIGNAL/PARALLEL {day}):** Stage A **`{verdict}`** · "
        f"register **0kbh** · top `{c.get('detector')}` IC **{c.get('ic_spearman_primary')}** · "
        f"hit(Mar) **{c.get('hit_rate_mar')}** · lead **{c.get('median_lead_days')}**d · "
        f"vs 0kbg MDD_ONLY size overlays · **signal≠apply** · soak freeze unchanged · "
        f"Soft KEEP · Path4 OFF · no live · `{DECISION_ID}.md`  "
    )
    ot2, n = re.subn(
        r"\*\*Y2020 crisis signal detect \(SIGNAL/PARALLEL [^)]+\):\*\*.*",
        line,
        ot,
        count=1,
    )
    if n:
        ops.write_text(ot2, encoding="utf-8")
        return
    needle = "DD_SWITCH soak gate (2026-10-03 cadence):"
    idx = ot.find(needle)
    if idx < 0:
        needle = "2020 defend/off-peak knife"
        idx = ot.find(needle)
    if idx >= 0:
        end = ot.find("\n", idx) + 1
        ops.write_text(ot[:end] + line + "\n" + ot[end:], encoding="utf-8")


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


def score_detectors(panel: pd.DataFrame) -> list[dict[str, Any]]:
    label_prefixes = (
        "fwd_",
        "in_mar",
        "in_y2020",
        "l4_dd_cross_",
        "soft_dd_cross_",
    )
    feat_cols = [
        c
        for c in panel.columns
        if c not in ("date", "year2020_dummy")
        and not any(c.startswith(p) for p in label_prefixes)
    ]

    primary_label = "fwd_mdd_10"
    mar_label = "in_mar2020"
    stress_bin = "l4_dd_cross_8"
    p = panel.copy()
    p["date"] = pd.to_datetime(p["date"])
    p = p.set_index("date").sort_index()
    trough = pd.Timestamp(MAR2020_END)
    local = (p.index.date >= MAR_EVAL_START) & (p.index.date <= MAR_EVAL_END)

    rows: list[dict[str, Any]] = []
    y_primary = p[primary_label]
    y_mar = p[mar_label]
    y_stress = p[stress_bin]
    y_year = p["year2020_dummy"]
    ex2020 = y_year < 0.5

    for col in feat_cols:
        x = p[col]
        sp = _spearman(x, y_primary)
        # Orient: stress-high means positive association with fwd MDD
        stress_high = True if sp is None else (float(sp) >= 0)
        # If IC negative, flip orientation for alerts (feature is "safety" not stress)
        x_stress = x if stress_high else -x
        sp_s = _spearman(x_stress, y_primary)
        pe_s = _pearson(x_stress, y_primary)
        sp_mar = _spearman(x_stress, y_mar)
        sp_stress = _spearman(x_stress, y_stress)
        sp_oos = _spearman(x_stress[ex2020], y_primary[ex2020])
        yd = _spearman(x_stress, y_year)
        yd_abs = None if yd is None else abs(float(yd))

        alert = _alert_mask(x_stress, stress_high=True, q=ALERT_Q)
        # Mar metrics inside H1-2020 local window (balanced vs full-sample TN flood)
        prf_mar = _binary_prf(y_mar[local].astype(bool), alert[local])
        prf_stress = _binary_prf(y_stress.astype(bool), alert)

        alert_out = alert & (y_year < 0.5)
        n_alert_out = int(alert_out.sum())
        n_out = int((y_year < 0.5).sum())
        fa = (n_alert_out / n_out) if n_out else None
        out_prf = _binary_prf(y_stress[ex2020].astype(bool), alert[ex2020])

        lead = _median_lead_days(alert, window_start=MAR2020_START, trough=trough)
        cross_idx = p.index[(y_year > 0.5) & (p["l4_dd_cross_8"] > 0.5)]
        lead_cross = None
        if len(cross_idx):
            first_cross = pd.Timestamp(cross_idx[0])
            lead_cross = _median_lead_days(
                alert, window_start=date(2020, 2, 1), trough=first_cross
            )

        row = {
            "detector": col,
            "stress_high_orientation": bool(stress_high),
            "ic_spearman_primary": None if sp_s is None else round(float(sp_s), 4),
            "ic_pearson_primary": None if pe_s is None else round(float(pe_s), 4),
            "ic_spearman_mar": None if sp_mar is None else round(float(sp_mar), 4),
            "ic_spearman_ddcross8": None if sp_stress is None else round(float(sp_stress), 4),
            "ic_spearman_oos_ex2020": None if sp_oos is None else round(float(sp_oos), 4),
            "year2020_dummy_abs_ic": None if yd_abs is None else round(float(yd_abs), 4),
            "hit_rate_mar": prf_mar["hit_rate"],
            "precision_mar": prf_mar["precision"],
            "recall_mar": prf_mar["recall"],
            "f1_mar": prf_mar["f1"],
            "hit_rate_ddcross8": prf_stress["hit_rate"],
            "f1_ddcross8": prf_stress["f1"],
            "fa_rate_outside_2020": None if fa is None else round(float(fa), 4),
            "precision_stress_ex2020": out_prf["precision"],
            "median_lead_days": None if lead is None else round(float(lead), 2),
            "lead_to_first_dd8": None if lead_cross is None else round(float(lead_cross), 2),
            "primary_label": primary_label,
            "alert_q": ALERT_Q,
            "n_alert": int(alert.sum()),
        }
        row["verdict"] = _detector_verdict(row)
        rows.append(row)

    rows.sort(
        key=lambda r: (
            r["verdict"] == "SIGNAL_HIT",
            r["verdict"] == "SIGNAL_WEAK",
            *_champ_key(r),
        ),
        reverse=True,
    )
    return rows


def _counterfactual_cash_gate(
    panel: pd.DataFrame,
    detector: str,
    *,
    stress_high: bool,
    base_nav: pd.DataFrame,
) -> dict[str, Any]:
    """Illustrative only: lag-1 alert → cash on L4 returns; report held/Mar MDD."""
    p = panel.copy()
    p["date"] = pd.to_datetime(p["date"])
    x = p.set_index("date")[detector]
    x_stress = x if stress_high else -x
    alert = _alert_mask(x_stress, stress_high=True)
    # Exact T+1: alert already uses lag-1 features; cash on alert day
    r = _returns(base_nav)
    exp = pd.Series(np.where(alert.reindex(r.index).fillna(False), 0.0, 1.0), index=r.index)
    chal_r = (exp * r).astype(float)
    nav0 = float(base_nav["nav"].iloc[0])
    chal = _nav_from_returns(chal_r, nav0)
    base_w = _pack(base_nav)
    chal_w = _pack(chal)
    d = _delta(base_w, chal_w)
    tip = _tip(base_nav, chal)
    base_mar = window_stats(base_nav, MAR2020_START, MAR2020_END, min_days=10).get(
        "max_drawdown"
    )
    chal_mar = window_stats(chal, MAR2020_START, MAR2020_END, min_days=10).get(
        "max_drawdown"
    )
    mar_imp = (
        None
        if base_mar is None or chal_mar is None
        else round(float(mdd_delta_pp(float(base_mar), float(chal_mar))), 4)
    )
    return {
        "note": "ILLUSTRATIVE ONLY — not HIT path; signal≠apply; no size-overlay promote",
        "detector": detector,
        "held_cagr_lift_pp": d["heldout_2019_plus"]["cagr_lift_pp"],
        "sealed_mdd_improve_pp": d["sealed_2023_plus"]["mdd_improve_pp"],
        "tipY_cagr_lift_pp": (tip.get("ytd") or {}).get("cagr_lift_pp"),
        "mar2020_mdd_improve_pp": mar_imp,
        "base_mar2020_mdd": None if base_mar is None else round(float(base_mar), 6),
        "chal_mar2020_mdd": None if chal_mar is None else round(float(chal_mar), 6),
        "pct_cash_days": round(float((exp < 0.5).mean()) * 100, 2),
    }


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()
    day = generated[:10]

    panel, meta = build_panel()
    panel.to_csv(OUT / "panel_crisis_signal.csv", index=False)
    rows = score_detectors(panel)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "detectors_scored.csv", index=False)

    verdict, champ = _global_verdict(rows)
    n_hit = int(sum(1 for r in rows if r["verdict"] == "SIGNAL_HIT"))
    n_weak = int(sum(1 for r in rows if r["verdict"] == "SIGNAL_WEAK"))
    n_no = int(sum(1 for r in rows if r["verdict"] == "SIGNAL_NO_EDGE"))
    top = rows[:15]

    l4_path = ROOT / meta["base_path"]
    base_nav = _load_nav(l4_path)
    cf = None
    if champ is not None:
        cf = _counterfactual_cash_gate(
            panel,
            champ["detector"],
            stress_high=bool(champ.get("stress_high_orientation", True)),
            base_nav=base_nav,
        )
        (OUT / "counterfactual_illustrative.json").write_text(
            json.dumps(cf, indent=2) + "\n", encoding="utf-8"
        )

    floors = {
        "ic_abs_floor": IC_ABS_FLOOR,
        "hit_floor": HIT_FLOOR,
        "recall_mar_floor": RECALL_MAR_FLOOR,
        "lead_days_floor": LEAD_DAYS_FLOOR,
        "fa_outside_2020_ceil": FA_OUTSIDE_2020_CEIL,
        "year_dummy_ic_abs_ceil": YEAR_DUMMY_IC_ABS_CEIL,
        "oos_ic_abs_floor": OOS_IC_ABS_FLOOR,
        "alert_q": ALERT_Q,
        "primary_label": "fwd_mdd_10",
        "mar_eval_window": [str(MAR_EVAL_START), str(MAR_EVAL_END)],
    }

    compare = {
        "0kbg": {
            "register": "0kbg",
            "verdict": "IP3_Y2020_CRISIS_SANDBOX_MDD_ONLY",
            "note": (
                "0kbg size overlays cut Mar MDD but held≪0. This pack measures the same "
                "crisis family as **signals** (IC/hit/lead) without exposure apply."
            ),
        },
        "0kb4": {
            "register": "0kb4",
            "verdict": "IP3_Y2020_DEFEND_NO_EDGE",
            "note": "Defend/FUSE knives on 0kb2 — different family from crisis signal detect.",
        },
        "0kbf": {
            "register": "0kbf",
            "verdict": "SOAK_OPEN",
            "note": "Soak freeze unchanged — signal Stage A does not unlock SOAK_PASS.",
        },
    }

    optimize = [
        "Objective: lag-1 causal detectors for Mar2020 / 2020 crisis stress — IC/hit/lead; no exposure apply",
        (
            f"Top `{champ['detector']}` IC={champ.get('ic_spearman_primary')} "
            f"hit(Mar)={champ.get('hit_rate_mar')} lead={champ.get('median_lead_days')}d "
            f"FA≠2020={champ.get('fa_rate_outside_2020')} verdict={champ.get('verdict')}"
            if champ
            else "No detector scored"
        ),
        f"Clears: SIGNAL_HIT={n_hit} · SIGNAL_WEAK={n_weak} · SIGNAL_NO_EDGE={n_no} / n={len(rows)}",
        "vs 0kbg: MDD_ONLY size overlays hurt held → signal-only fork",
        "Disposition: signal≠apply · soak freeze unchanged · no LIVE wire · no tip Soft promote · no year-oracle",
        "Soft KEEP · Path4 OFF · broker false · Exact T+1",
        (
            f"Illustrative CF cash-gate: held={cf.get('held_cagr_lift_pp')} "
            f"MarMDD↑={cf.get('mar2020_mdd_improve_pp')} (NOT HIT path)"
            if cf
            else "No CF"
        ),
    ]

    screen = {
        "id": SCREEN_ID,
        "register": REGISTER,
        "parents": list(PARENTS),
        "generated_at_utc": generated,
        "mech": MECH,
        "label_tag": LABEL_TAG,
        "verdict": verdict,
        "signal_not_apply": True,
        "soak_unlock": False,
        "live_wire_recommend": False,
        "size_overlay_promote": False,
        "year_oracle": False,
        "n_detectors": len(rows),
        "n_signal_hit": n_hit,
        "n_signal_weak": n_weak,
        "n_signal_no_edge": n_no,
        "floors": floors,
        "meta": meta,
        "compare_parents": compare,
        "champion": champ,
        "top_detectors": top,
        "counterfactual_illustrative": cf,
        "optimize_live": optimize,
        "soft_keep": True,
        "path4_live": False,
        "broker": False,
        "exact_t1": True,
        "label": f"{SCREEN_ID}_{day}__{verdict}__{LABEL_TAG}",
    }
    (OUT / "screen.json").write_text(json.dumps(screen, indent=2, default=str) + "\n", encoding="utf-8")
    (OUT / "base_diag.json").write_text(json.dumps({"meta": meta, "floors": floors}, indent=2) + "\n", encoding="utf-8")

    charter_md = "\n".join(
        [
            f"# {CHARTER_ID}",
            "",
            f"Date: {day}",
            f"Register: **{REGISTER}** · Parents: {', '.join(PARENTS)}",
            f"Label: **{LABEL_TAG}** · SOAK-SAFE parallel · **signal ≠ apply**",
            "",
            "## Question",
            "",
            "Which causal lag-1 features best **detect** Mar2020 cliff / 2020 crisis "
            "stress days on the L4 twin world (0050 / soft NAV / market), measured by "
            "IC / hit-rate / lead days — without applying exposure?",
            "",
            "## Labels",
            "",
            "- Forward N-day MDD / crash return (5/10/20) on L4 & 0050",
            f"- In Mar2020 window {MAR2020_START}→{MAR2020_END}",
            "- Soft/L4 NAV dd-from-peak crossing −5%/−8%/−10%",
            "",
            "## Detectors (lag-1 causal)",
            "",
            "- Realized vol 20/63 (L4 & 0050)",
            "- ATR-like range 20",
            "- 0050 vs MA60/MA120/MA200 (neg gap / below flags)",
            "- dd63 (mkt/L4/soft) · proxy_mdd63 · COOL defend · FUSE-prem proxies",
            "- Consecutive down days",
            "- VIX proxy if available else skip · breadth skip if unavailable",
            "",
            "## Metrics / verdict",
            "",
            f"- Spearman/Pearson IC vs `{floors['primary_label']}` · Mar hit P/R/F1 · lead days · FA outside 2020",
            f"- Floors: |IC|≥{IC_ABS_FLOOR} · hit≥{HIT_FLOOR} · lead≥{LEAD_DAYS_FLOOR}d · "
            f"FA≤{FA_OUTSIDE_2020_CEIL} · OOS|IC|≥{OOS_IC_ABS_FLOOR} · not year-dummy",
            "- `SIGNAL_HIT` / `SIGNAL_WEAK` / `SIGNAL_NO_EDGE`",
            "",
            "## Hard constraints",
            "",
            "- Soft KEEP · Path4 OFF · broker false · Exact T+1",
            "- **signal ≠ apply** · no tip Soft promote · no year-oracle",
            "- does **not** unlock soak freeze · no LIVE wire · no size-overlay promote",
            "- vs 0kbg: size overlays MDD_ONLY → this fork is detection-only",
            "",
            f"Label: `{CHARTER_ID}_{day}__{LABEL_TAG}`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{CHARTER_ID}.md", REP / f"{CHARTER_ID}.md", charter_md, kind="charter"
    )
    (OPS / f"{CHARTER_ID}.json").write_text(
        json.dumps(
            {
                "id": CHARTER_ID,
                "register": REGISTER,
                "parents": list(PARENTS),
                "mech": MECH,
                "label_tag": LABEL_TAG,
                "date": day,
                "signal_not_apply": True,
                "floors": floors,
                "forbidden": [
                    "live_wire",
                    "tip_apply",
                    "soft_fin_tel_accept",
                    "path4_live",
                    "broker",
                    "year_oracle",
                    "size_overlay_promote",
                    "soak_unlock",
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    write_repro_pointer(OPS / f"{CHARTER_ID}.json", REP / f"{CHARTER_ID}.json", kind="charter")

    screen_md = [
        f"# {SCREEN_ID}",
        "",
        f"Date: {day} · Verdict: **`{verdict}`** · top=**`{(champ or {}).get('detector')}`**",
        f"Register: **{REGISTER}** · **{LABEL_TAG}** · n={len(rows)} · "
        f"HIT={n_hit} · WEAK={n_weak} · NO_EDGE={n_no}",
        "",
        "## Meta",
        "",
        f"- base `{meta['base_id']}` `{meta['base_path']}` · soft `{meta['soft_id']}`",
        f"- Mar2020 {MAR2020_START}→{MAR2020_END} · primary label `fwd_mdd_10`",
        f"- skipped: {', '.join(meta['skipped_detectors']) or '(none)'}",
        "",
        "## Floors",
        "",
        f"- |IC|≥**{IC_ABS_FLOOR}** · hit(H1'20)≥**{HIT_FLOOR}** · recall(Mar)≥**{RECALL_MAR_FLOOR}** · "
        f"lead≥**{LEAD_DAYS_FLOOR}**d · FA≠2020≤**{FA_OUTSIDE_2020_CEIL}** · "
        f"OOS|IC|≥**{OOS_IC_ABS_FLOOR}** · year-dummy|IC|<**{YEAR_DUMMY_IC_ABS_CEIL}**",
        "",
        "## Parents",
        "",
        f"- 0kbg: {compare['0kbg']['note']}",
        f"- 0kb4: {compare['0kb4']['note']}",
        f"- 0kbf: {compare['0kbf']['note']}",
        "",
        "## Top detectors",
        "",
        "| Detector | IC(sp) | IC OOS | hit(Mar) | F1(Mar) | lead d | FA≠2020 | yr-dummy | verdict |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for r in top:
        screen_md.append(
            f"| {r['detector']} | {r['ic_spearman_primary']} | {r['ic_spearman_oos_ex2020']} | "
            f"{r['hit_rate_mar']} | {r['f1_mar']} | {r['median_lead_days']} | "
            f"{r['fa_rate_outside_2020']} | {r['year2020_dummy_abs_ic']} | {r['verdict']} |"
        )
    if cf:
        screen_md += [
            "",
            "## Counterfactual (illustrative only)",
            "",
            f"- cash-gate on `{cf['detector']}`: held **{cf['held_cagr_lift_pp']}** · "
            f"Mar MDD↑ **{cf['mar2020_mdd_improve_pp']}** · cash days **{cf['pct_cash_days']}%**",
            f"- {cf['note']}",
        ]
    screen_md += [
        "",
        "## Optimize / disposition",
        "",
        *[f"{i}. {line}" for i, line in enumerate(optimize, 1)],
        "",
        "Repro: `PYTHONPATH=scripts python3 scripts/tipsoft_ip3_y2020_crisis_signal_stagea.py`",
        "",
        f"Label: `{screen['label']}`",
        "",
    ]
    write_ops_and_repro_pointer(
        OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", "\n".join(screen_md), kind="screen"
    )
    (OPS / f"{SCREEN_ID}.json").write_text(
        json.dumps(screen, indent=2, default=str) + "\n", encoding="utf-8"
    )
    write_repro_pointer(OPS / f"{SCREEN_ID}.json", REP / f"{SCREEN_ID}.json", kind="screen")

    decision_md = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: {day} · Verdict: **`{verdict}`** · top=**`{(champ or {}).get('detector')}`**",
            f"Register: **{REGISTER}** · Parents: {', '.join(PARENTS)} · **{LABEL_TAG}**",
            "",
            "## Result",
            "",
            (
                f"- IC (Spearman vs fwd_mdd_10): **{(champ or {}).get('ic_spearman_primary')}** "
                f"(OOS ex-2020 **{(champ or {}).get('ic_spearman_oos_ex2020')}**)\n"
                f"- hit(Mar) **{(champ or {}).get('hit_rate_mar')}** · "
                f"P/R/F1 **{(champ or {}).get('precision_mar')}**/"
                f"**{(champ or {}).get('recall_mar')}**/"
                f"**{(champ or {}).get('f1_mar')}**\n"
                f"- median lead into Mar trough: **{(champ or {}).get('median_lead_days')}**d\n"
                f"- FA rate outside 2020: **{(champ or {}).get('fa_rate_outside_2020')}** · "
                f"year-dummy |IC|: **{(champ or {}).get('year2020_dummy_abs_ic')}**\n"
                f"- clears: SIGNAL_HIT **{n_hit}** · WEAK **{n_weak}** · NO_EDGE **{n_no}**"
                if champ
                else f"- No clear · n={len(rows)}"
            ),
            "",
            "## Disposition",
            "",
            "- **SIGNAL / PARALLEL** — detection only; **signal ≠ apply**",
            "- Does **not** unlock soak freeze · does **not** recommend LIVE wire",
            "- No tip Soft promote · no year-oracle · no size-overlay promote",
            "- vs 0kbg `IP3_Y2020_CRISIS_SANDBOX_MDD_ONLY`: size overlays hurt held → signal fork",
            "- Soft KEEP · Path4 OFF · broker false · Exact T+1",
            (
                f"- Illustrative CF (not HIT path): held={cf.get('held_cagr_lift_pp')} "
                f"MarMDD↑={cf.get('mar2020_mdd_improve_pp')}"
                if cf
                else "- No CF"
            ),
            "",
            "## Next",
            "",
            *[f"{i}. {line}" for i, line in enumerate(optimize, 1)],
            "",
            f"Label: `{DECISION_ID}_{day}__{verdict}__{LABEL_TAG}__NO_LIVE`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{DECISION_ID}.md", REP / f"{DECISION_ID}.md", decision_md, kind="decision pack"
    )
    (OPS / f"{DECISION_ID}.json").write_text(
        json.dumps(
            {
                "id": DECISION_ID,
                "register": REGISTER,
                "parents": list(PARENTS),
                "label_tag": LABEL_TAG,
                "verdict": verdict,
                "champion": champ,
                "n_signal_hit": n_hit,
                "n_signal_weak": n_weak,
                "n_signal_no_edge": n_no,
                "signal_not_apply": True,
                "soak_unlock": False,
                "live_wire_recommend": False,
                "size_overlay_promote": False,
                "counterfactual_illustrative": cf,
                "compare_parents": compare,
                "soft_keep": True,
                "path4_live": False,
                "broker": False,
                "label": f"{DECISION_ID}_{day}__{verdict}__{LABEL_TAG}__NO_LIVE",
            },
            indent=2,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )
    write_repro_pointer(
        OPS / f"{DECISION_ID}.json", REP / f"{DECISION_ID}.json", kind="decision pack"
    )

    _patch_register(verdict, champ, day)
    _patch_ops_status(verdict, champ, day)

    summary = {
        "verdict": verdict,
        "champion": None if not champ else champ["detector"],
        "ic_spearman_primary": None if not champ else champ.get("ic_spearman_primary"),
        "hit_rate_mar": None if not champ else champ.get("hit_rate_mar"),
        "median_lead_days": None if not champ else champ.get("median_lead_days"),
        "fa_rate_outside_2020": None if not champ else champ.get("fa_rate_outside_2020"),
        "ic_spearman_oos_ex2020": None if not champ else champ.get("ic_spearman_oos_ex2020"),
        "n_signal_hit": n_hit,
        "n_signal_weak": n_weak,
        "n_signal_no_edge": n_no,
        "n_detectors": len(rows),
        "signal_not_apply": True,
        "soak_unlock": False,
        "live_wire_recommend": False,
        "label_tag": LABEL_TAG,
        "register": REGISTER,
        "counterfactual_illustrative": None
        if not cf
        else {
            "held_cagr_lift_pp": cf.get("held_cagr_lift_pp"),
            "mar2020_mdd_improve_pp": cf.get("mar2020_mdd_improve_pp"),
        },
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
