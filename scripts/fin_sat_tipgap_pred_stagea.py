#!/usr/bin/env python3
"""FIN×SAT tip-gap predictor Stage A — feature IC / tip contrast / cycle overlap / probes.

Charter: research/ops/FIN_SAT_TIPGAP_PRED_STAGEA_CHARTER.md
Parents: 0k9h TIP_MDD_ONLY · COMP + SAT_RELAX KEEP.
Methods open within pre-registered feature table · Soft-Frozen KEEP · no live.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import cool_t50_inv_satellite_stagea as sat
from e45_paper_harness import WINDOWS_STANDARD, window_stats
from e50_early_stack_combined_nav import e16_features
from fin_sell_quality_helpers import cagr_lift_pp
from ops_repro_ssot import write_ops_and_repro_pointer
from research_metric_helpers import mdd_delta_pp

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "fin-sat-tipgap-pred-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_SAT_TIPGAP_PRED_STAGEA_CHARTER"
SCREEN_ID = "FIN_SAT_TIPGAP_PRED_STAGEA_SCREEN"
DECISION_ID = "FIN_SAT_TIPGAP_PRED_STAGEA_DECISION_PACK"
BASE_ID = "CTRL_LIVE_A10"

LIVE_NAV = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/ctrl_live_a10_daily_nav.csv"
COMP_NAV = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/comp_h150_x_a20_daily_nav.csv"
SAT_NAV = ROOT / "repro/sat-a20-relax-dual-paper-observe/outputs/sat_a20_relax_daily_nav.csv"
COMP_FILLS = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/comp_h150_x_a20_fills.csv"

CAGR_FLOOR_PP = 0.10
HELD_MDD_MIN_PP = -0.25
HELD_ABS_MDD_MAX = 0.15
TIP_MDD_MIN_PP = 0.0
TIP_CAGR_MIN_PP = 0.0
VS_SAT_HELD_EXTRA_PP = 0.05
IC_ABS_MIN = 0.04
HIT_RATE_MIN = 0.52
MAX_PROBES = 3
FWD = 21

# Pre-registered features for IC (lag-1 already applied in panel columns named *_l1)
FEAT_COLS = [
    "crisis_l1",
    "bearcrisis_l1",
    "zz08_bear_l1",
    "zz12_bear_l1",
    "mdd0050_63_l1",
    "r0050_63_l1",
    "vol0050_21_l1",
    "trail_rel_21_l1",
    "trail_rel_63_l1",
    "comp_sells_21_l1",
    "month_sin_l1",
    "month_cos_l1",
]


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_nav(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    return (
        df.sort_values("date")
        .reset_index(drop=True)[["date", "nav"]]
        .assign(nav=lambda x: x["nav"].astype(float))
    )


def _pack(nav: pd.DataFrame) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, (a, b) in WINDOWS_STANDARD.items():
        st = window_stats(nav, a, b)
        out[k] = {
            "cagr": None if st.get("cagr") is None else round(float(st["cagr"]), 6),
            "max_drawdown": None
            if st.get("max_drawdown") is None
            else round(float(st["max_drawdown"]), 6),
            "n_days": int(st.get("n_days") or 0),
        }
    return out


def _tip(base_nav: pd.DataFrame, chal_nav: pd.DataFrame) -> dict[str, Any]:
    asof = pd.Timestamp(pd.to_datetime(base_nav["date"]).max())
    b_dates = pd.to_datetime(base_nav["date"])
    c_dates = pd.to_datetime(chal_nav["date"])
    out: dict[str, Any] = {}
    for wname, start in (
        ("ytd", pd.Timestamp(asof.year, 1, 1)),
        ("trailing_1y", asof - pd.Timedelta(days=365)),
    ):
        b = base_nav[(b_dates >= start) & (b_dates <= asof)].reset_index(drop=True)
        c = chal_nav[(c_dates >= start) & (c_dates <= asof)].reset_index(drop=True)
        if len(b) < 20 or len(c) < 20:
            out[wname] = {"mdd_improve_pp": None, "cagr_lift_pp": None, "gate": "INSUFFICIENT"}
            continue
        bn = b["nav"].astype(float) / float(b["nav"].iloc[0])
        cn = c["nav"].astype(float) / float(c["nav"].iloc[0])
        b_mdd = float((bn / bn.cummax() - 1.0).min())
        c_mdd = float((cn / cn.cummax() - 1.0).min())
        years = (len(b) - 1) / 252.0
        bc = float(bn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        cc = float(cn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        lift = cagr_lift_pp(bc, cc)
        out[wname] = {
            "mdd_improve_pp": round(float(mdd_delta_pp(b_mdd, c_mdd)), 4),
            "cagr_lift_pp": None if lift is None else round(float(lift), 4),
            "gate": "PASS",
        }
    return out


def _trail(r: pd.Series, n: int) -> pd.Series:
    return (1.0 + r).rolling(n, min_periods=n).apply(lambda x: float(np.prod(x) - 1.0), raw=True)


def _fwd_sum(x: pd.Series, n: int) -> pd.Series:
    # sum of next n days (not including today): x[t+1]…x[t+n]
    acc = pd.Series(0.0, index=x.index)
    for i in range(1, n + 1):
        acc = acc + x.shift(-i)
    # require full window
    valid = pd.Series(True, index=x.index)
    for i in range(1, n + 1):
        valid &= x.shift(-i).notna()
    return acc.where(valid)


def _zigzag_bear(close: pd.Series, thr: float) -> pd.Series:
    px = close.astype(float).ffill().to_numpy()
    n = len(px)
    bear = np.zeros(n, dtype=bool)
    if n == 0:
        return pd.Series(bear, index=close.index)
    extreme = float(px[0])
    is_bear = False
    for i in range(1, n):
        p = float(px[i])
        if not is_bear:
            extreme = max(extreme, p)
            if extreme > 0 and (p / extreme - 1.0) <= -thr:
                is_bear = True
                extreme = p
        else:
            extreme = min(extreme, p)
            if extreme > 0 and (p / extreme - 1.0) >= thr:
                is_bear = False
                extreme = p
        bear[i] = is_bear
    return pd.Series(bear, index=close.index)


def _build_panel(dates: pd.DatetimeIndex, comp: pd.DataFrame, sat_nav: pd.DataFrame) -> pd.DataFrame:
    print("building feature panel ...", flush=True)
    market0 = sat.load_market()
    _p, _s, _t, regime = e16_features(market0)
    reg = pd.Series(regime.values, index=pd.to_datetime(regime.index)).sort_index()
    reg = reg[~reg.index.duplicated(keep="last")]

    px = market0[market0["code"].astype(str) == "0050"].copy()
    px["date"] = pd.to_datetime(px["date"])
    px = px.sort_values("date").drop_duplicates("date")
    close = px.set_index("date")["adj_close" if "adj_close" in px.columns else "close"].astype(float)
    close = close[~close.index.duplicated(keep="last")]
    r0050 = close.pct_change()

    c = comp.set_index("date")["nav"].reindex(dates).astype(float)
    s = sat_nav.set_index("date")["nav"].reindex(dates).astype(float)
    rc = c.pct_change()
    rs = s.pct_change()
    rel = rc - rs

    # COMP SELL intensity
    sells = pd.Series(0.0, index=dates)
    if COMP_FILLS.exists():
        f = pd.read_csv(COMP_FILLS)
        f["fill_date"] = pd.to_datetime(f["fill_date"])
        f = f[f["side"].astype(str).str.upper() == "SELL"]
        cnt = f.groupby("fill_date").size()
        sells = cnt.reindex(dates).fillna(0.0)

    feat = pd.DataFrame({"date": dates})
    feat["regime"] = feat["date"].map(reg)
    feat["close0050"] = feat["date"].map(close)
    feat["rc"] = rc.to_numpy()
    feat["rs"] = rs.to_numpy()
    feat["rel"] = rel.to_numpy()
    feat["comp_sells"] = sells.to_numpy()

    feat["crisis"] = (feat["regime"] == "Crisis").astype(float)
    feat["bearcrisis"] = feat["regime"].isin(["Bear", "Crisis"]).astype(float)
    feat["zz08_bear"] = _zigzag_bear(feat["close0050"], 0.08).astype(float).to_numpy()
    feat["zz12_bear"] = _zigzag_bear(feat["close0050"], 0.12).astype(float).to_numpy()
    feat["mdd0050_63"] = (
        feat["close0050"]
        .ffill()
        .rolling(63, min_periods=63)
        .apply(lambda w: float((pd.Series(w) / pd.Series(w).cummax() - 1.0).min()), raw=True)
        .to_numpy()
    )
    feat["r0050_63"] = _trail(feat["date"].map(r0050), 63).to_numpy()
    feat["vol0050_21"] = feat["date"].map(r0050).rolling(21, min_periods=21).std().to_numpy()
    feat["trail_rel_21"] = _trail(pd.Series(feat["rel"]), 21).to_numpy()
    feat["trail_rel_63"] = _trail(pd.Series(feat["rel"]), 63).to_numpy()
    feat["comp_sells_21"] = pd.Series(feat["comp_sells"]).rolling(21, min_periods=1).sum().to_numpy()
    month = feat["date"].dt.month.astype(float)
    feat["month_sin"] = np.sin(2 * np.pi * month / 12.0)
    feat["month_cos"] = np.cos(2 * np.pi * month / 12.0)

    # forward relative return (for IC target) — diagnosis only, not used as switch input
    feat["fwd_rel_21"] = _fwd_sum(pd.Series(feat["rel"]), FWD).to_numpy()

    # tip-drag day: trailing 63d rel < 0 (COMP lagging)
    feat["trail_drag"] = (pd.Series(feat["trail_rel_63"]) < 0).astype(float)

    for col in [
        "crisis",
        "bearcrisis",
        "zz08_bear",
        "zz12_bear",
        "mdd0050_63",
        "r0050_63",
        "vol0050_21",
        "trail_rel_21",
        "trail_rel_63",
        "comp_sells_21",
        "month_sin",
        "month_cos",
        "trail_drag",
    ]:
        feat[f"{col}_l1"] = feat[col].shift(1)

    return feat


def _ic_table(feat: pd.DataFrame) -> list[dict[str, Any]]:
    y = feat["fwd_rel_21"]
    rows: list[dict[str, Any]] = []
    for col in FEAT_COLS:
        x = feat[col]
        m = pd.DataFrame({"x": x, "y": y}).dropna()
        if len(m) < 100:
            continue
        ic = float(m["x"].corr(m["y"]))
        # sign hit: predict y>0 when x aligns with sign(ic)
        if abs(ic) < 1e-12 or np.isnan(ic):
            hit = None
        else:
            pred = np.sign(ic) * np.sign(m["x"].replace(0, np.nan))
            # for binary-ish: use x > median as positive feature state
            med = float(m["x"].median())
            state = (m["x"] > med).astype(float)
            # if IC>0, high x → high y (COMP lead); SAT switch wants COMP lag ⇒ use low x
            pred_pos = state if ic > 0 else 1.0 - state
            actual_pos = (m["y"] > 0).astype(float)
            hit = float((pred_pos == actual_pos).mean())
        rows.append(
            {
                "feat": col,
                "ic": None if ic != ic else round(ic, 4),
                "abs_ic": None if ic != ic else round(abs(ic), 4),
                "sign_hit": None if hit is None else round(hit, 4),
                "n": int(len(m)),
                "ic_gate": bool(
                    ic == ic
                    and abs(ic) >= IC_ABS_MIN
                    and hit is not None
                    and hit >= HIT_RATE_MIN
                ),
                # switch to SAT when feature predicts COMP lag (fwd_rel < 0)
                # if IC>0: high feat → COMP lead → SAT when feat low
                # if IC<0: high feat → COMP lag → SAT when feat high
                "sat_when_high": bool(ic == ic and ic < 0),
            }
        )
    rows.sort(key=lambda r: float(r["abs_ic"] or 0), reverse=True)
    return rows


def _window_contrast(feat: pd.DataFrame, live: pd.DataFrame) -> dict[str, Any]:
    asof = pd.Timestamp(live["date"].max())
    windows = {
        "ytd": (pd.Timestamp(asof.year, 1, 1), asof),
        "trailing_1y": (asof - pd.Timedelta(days=365), asof),
        "heldout_2019_plus": (pd.Timestamp("2019-01-01"), asof),
        "full": (feat["date"].min(), asof),
    }
    keys = [
        "crisis",
        "bearcrisis",
        "zz08_bear",
        "mdd0050_63",
        "r0050_63",
        "vol0050_21",
        "trail_rel_63",
        "comp_sells_21",
        "trail_drag",
        "rel",
    ]
    out: dict[str, Any] = {}
    for wname, (a, b) in windows.items():
        g = feat[(feat["date"] >= a) & (feat["date"] <= b)]
        stats: dict[str, Any] = {"n_days": int(len(g))}
        for k in keys:
            s = g[k]
            stats[k] = None if s.isna().all() else round(float(s.mean()), 6)
        # fraction drag days
        stats["pct_trail_drag"] = None if g["trail_drag"].isna().all() else round(float(g["trail_drag"].mean()) * 100, 2)
        out[wname] = stats
    # tip vs held contrast
    tip = out["trailing_1y"]
    held = out["heldout_2019_plus"]
    contrast = {}
    for k in keys + ["pct_trail_drag"]:
        a, b_ = tip.get(k), held.get(k)
        contrast[k] = None if a is None or b_ is None else round(float(a) - float(b_), 6)
    out["tip1y_minus_held"] = contrast
    return out


def _cycle_overlap(feat: pd.DataFrame, live: pd.DataFrame) -> dict[str, Any]:
    asof = pd.Timestamp(live["date"].max())
    tip = feat[(feat["date"] >= asof - pd.Timedelta(days=365)) & (feat["date"] <= asof)].copy()
    drag = tip["trail_drag"] > 0.5
    base_rate = float(drag.mean()) if len(tip) else 0.0
    out: dict[str, Any] = {"tip_drag_base_rate": round(base_rate * 100, 2), "n_tip": int(len(tip))}
    for name, mask in (
        ("crisis", tip["crisis"] > 0.5),
        ("bearcrisis", tip["bearcrisis"] > 0.5),
        ("zz08_bear", tip["zz08_bear"] > 0.5),
        ("zz12_bear", tip["zz12_bear"] > 0.5),
        ("sells21_hi", tip["comp_sells_21"] > tip["comp_sells_21"].median()),
        ("rel63_neg", tip["trail_rel_63"] < 0),
    ):
        m = mask.fillna(False)
        if m.sum() < 5:
            out[name] = {"n": int(m.sum()), "drag_rate": None, "lift_pp": None}
            continue
        rate = float(drag[m].mean())
        out[name] = {
            "n": int(m.sum()),
            "drag_rate": round(rate * 100, 2),
            "lift_pp": round((rate - base_rate) * 100, 2),
        }
    return out


def _worst_months(feat: pd.DataFrame) -> list[dict[str, Any]]:
    g = feat.dropna(subset=["rel"]).copy()
    g["ym"] = g["date"].dt.to_period("M")
    rows = []
    for ym, sub in g.groupby("ym"):
        if len(sub) < 10:
            continue
        rel_sum = float(sub["rel"].sum())
        rows.append(
            {
                "month": str(ym),
                "rel_sum_pp": round(rel_sum * 100, 3),
                "winner": "SAT" if rel_sum < 0 else "COMP",
                "pct_crisis": round(float(sub["crisis"].mean()) * 100, 2),
                "pct_zz08": round(float(sub["zz08_bear"].mean()) * 100, 2),
                "mean_sells21": round(float(sub["comp_sells_21"].mean()), 2),
                "mean_vol21": None
                if sub["vol0050_21"].isna().all()
                else round(float(sub["vol0050_21"].mean()), 5),
            }
        )
    rows.sort(key=lambda r: r["rel_sum_pp"])
    return rows[:12]  # worst 12 COMP-lag months


def _probe_use_sat(feat: pd.DataFrame, feat_name: str, sat_when_high: bool) -> pd.Series:
    x = feat[feat_name]
    med = float(x.dropna().median()) if x.notna().any() else 0.0
    high = x > med
    use = high if sat_when_high else ~high
    return use.fillna(False).astype(bool)


def _switch_nav(comp: pd.DataFrame, sat_nav: pd.DataFrame, use_sat: pd.Series, dates: pd.DatetimeIndex) -> tuple[pd.DataFrame, dict[str, Any]]:
    m = (
        comp.rename(columns={"nav": "nav_c"})
        .merge(sat_nav.rename(columns={"nav": "nav_s"}), on="date")
        .sort_values("date")
        .reset_index(drop=True)
    )
    # align use_sat by date
    u = pd.Series(use_sat.values, index=dates).reindex(m["date"]).fillna(False).astype(bool)
    rc = m["nav_c"].pct_change().fillna(0.0)
    rs = m["nav_s"].pct_change().fillna(0.0)
    r = np.where(u.to_numpy(), rs.to_numpy(), rc.to_numpy())
    nav = (1.0 + r).cumprod() * float(m["nav_c"].iloc[0])
    flips = int(np.sum(u.to_numpy()[1:] != u.to_numpy()[:-1])) if len(u) > 1 else 0
    return pd.DataFrame({"date": m["date"].to_numpy(), "nav": nav}), {
        "pct_days_sat": round(float(u.mean()) * 100, 2),
        "n_flips": flips,
        "n_days": int(len(m)),
    }


def _eval_row(base_w, chal_w, tip, *, fam: str, sat_held_cagr: float | None) -> dict[str, Any]:
    held_b = base_w.get("heldout_2019_plus") or {}
    held_c = chal_w.get("heldout_2019_plus") or {}
    cagr_pp = cagr_lift_pp(held_b.get("cagr"), held_c.get("cagr"))
    mdd_pp = mdd_delta_pp(held_b.get("max_drawdown"), held_c.get("max_drawdown"))
    abs_mdd = held_c.get("max_drawdown")
    tip_ytd_mdd = (tip.get("ytd") or {}).get("mdd_improve_pp")
    tip_1y_mdd = (tip.get("trailing_1y") or {}).get("mdd_improve_pp")
    tip_ytd_cagr = (tip.get("ytd") or {}).get("cagr_lift_pp")
    tip_1y_cagr = (tip.get("trailing_1y") or {}).get("cagr_lift_pp")
    tip_mdd_ok = (
        tip_ytd_mdd is not None
        and tip_1y_mdd is not None
        and float(tip_ytd_mdd) >= TIP_MDD_MIN_PP
        and float(tip_1y_mdd) >= TIP_MDD_MIN_PP
    )
    tip_cagr_ok = (
        tip_ytd_cagr is not None
        and tip_1y_cagr is not None
        and float(tip_ytd_cagr) >= TIP_CAGR_MIN_PP
        and float(tip_1y_cagr) >= TIP_CAGR_MIN_PP
    )
    cagr_ok = cagr_pp is not None and float(cagr_pp) >= CAGR_FLOOR_PP
    mdd_ok = mdd_pp is not None and float(mdd_pp) >= HELD_MDD_MIN_PP
    band_ok = abs_mdd is not None and abs(float(abs_mdd)) <= HELD_ABS_MDD_MAX
    vs_sat_ok = (
        cagr_pp is not None
        and sat_held_cagr is not None
        and float(cagr_pp) >= float(sat_held_cagr) + VS_SAT_HELD_EXTRA_PP
    )
    tip_clean = bool(tip_mdd_ok and tip_cagr_ok)
    economic = bool(cagr_ok and mdd_ok and band_ok and tip_mdd_ok)
    hit = bool(fam == "switch" and tip_clean and economic and vs_sat_ok)
    return {
        "held_cagr_lift_pp": None if cagr_pp is None else round(float(cagr_pp), 4),
        "held_mdd_pp": None if mdd_pp is None else round(float(mdd_pp), 4),
        "held_abs_mdd": None if abs_mdd is None else round(float(abs_mdd), 6),
        "tip_ytd_mdd_pp": tip_ytd_mdd,
        "tip_1y_mdd_pp": tip_1y_mdd,
        "tip_ytd_cagr_pp": tip_ytd_cagr,
        "tip_1y_cagr_pp": tip_1y_cagr,
        "family": fam,
        "gates": {
            "cagr": bool(cagr_ok),
            "mdd_near_flat": bool(mdd_ok),
            "mdd_band": bool(band_ok),
            "tip_mdd": bool(tip_mdd_ok),
            "tip_cagr": bool(tip_cagr_ok),
            "tip_clean": tip_clean,
            "economic": economic,
            "vs_sat_held": bool(vs_sat_ok),
        },
        "hit": hit,
    }


def _verdict(ic_rows: list[dict[str, Any]], probe_rows: list[dict[str, Any]]) -> str:
    if any(r["eval"]["hit"] for r in probe_rows if r["fam"] == "switch"):
        return "GAP_PRED_HIT"
    ready = [r for r in ic_rows if r.get("ic_gate")]
    if ready:
        # if probes exist and all tip_mdd economic without tip_cagr
        if probe_rows and any(
            r["eval"]["gates"]["tip_mdd"]
            and not r["eval"]["gates"]["tip_cagr"]
            and r["eval"]["gates"]["economic"]
            for r in probe_rows
            if r["fam"] == "switch"
        ):
            return "TIP_MDD_ONLY"
        return "GAP_FEAT_READY"
    # weak: tip contrast still reported
    if probe_rows and any(
        r["eval"]["gates"]["tip_mdd"] and not r["eval"]["gates"]["tip_cagr"] and r["eval"]["gates"]["economic"]
        for r in probe_rows
        if r["fam"] == "switch"
    ):
        return "TIP_MDD_ONLY"
    return "GAP_FEAT_WEAK"


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)

    print("loading NAVs ...", flush=True)
    live = _load_nav(LIVE_NAV)
    comp = _load_nav(COMP_NAV)
    sat_nav = _load_nav(SAT_NAV)
    dates = sorted(set(live["date"]) & set(comp["date"]) & set(sat_nav["date"]))
    live = live[live["date"].isin(dates)].reset_index(drop=True)
    comp = comp[comp["date"].isin(dates)].reset_index(drop=True)
    sat_nav = sat_nav[sat_nav["date"].isin(dates)].reset_index(drop=True)
    didx = pd.DatetimeIndex(dates)

    feat = _build_panel(didx, comp, sat_nav)
    feat.to_csv(OUT / "feature_panel.csv", index=False)

    ic_rows = _ic_table(feat)
    pd.DataFrame(ic_rows).to_csv(OUT / "leading_ic_table.csv", index=False)
    print(json.dumps({"top_ic": ic_rows[:5]}, ensure_ascii=False), flush=True)

    contrast = _window_contrast(feat, live)
    (OUT / "window_contrast.json").write_text(json.dumps(contrast, indent=2, ensure_ascii=False) + "\n")
    overlap = _cycle_overlap(feat, live)
    (OUT / "cycle_overlap_tip.json").write_text(json.dumps(overlap, indent=2, ensure_ascii=False) + "\n")
    worst = _worst_months(feat)
    pd.DataFrame(worst).to_csv(OUT / "worst_comp_lag_months.csv", index=False)

    base_w = _pack(live)
    sat_w = _pack(sat_nav)
    sat_held = cagr_lift_pp(
        (base_w.get("heldout_2019_plus") or {}).get("cagr"),
        (sat_w.get("heldout_2019_plus") or {}).get("cagr"),
    )

    # refs + probes
    books: list[dict[str, Any]] = []
    # CTRL / REF
    for bid, fam, nav0 in (
        ("CTRL_LIVE_A10", "ctrl", live),
        ("REF_SAT_RELAX", "ref", sat_nav),
        ("REF_COMP_H150_A20", "ref", comp),
    ):
        nav0.to_csv(OUT / f"nav_{bid}.csv", index=False)
        tip = (
            {
                "ytd": {"mdd_improve_pp": 0.0, "cagr_lift_pp": 0.0, "gate": "PASS"},
                "trailing_1y": {"mdd_improve_pp": 0.0, "cagr_lift_pp": 0.0, "gate": "PASS"},
            }
            if bid == BASE_ID
            else _tip(live, nav0)
        )
        ev = _eval_row(base_w, _pack(nav0), tip, fam=fam, sat_held_cagr=sat_held)
        books.append({"id": bid, "fam": fam, "meta": {"rule": fam}, "eval": ev, "tip": tip})

    gated = [r for r in ic_rows if r.get("ic_gate")][:MAX_PROBES]
    # if fewer than MAX pass, still probe top abs IC up to 1 for diagnosis? Charter: only IC gate → probes
    for i, fr in enumerate(gated):
        fname = fr["feat"]
        bid = f"PRB_{fname.upper().replace('_L1','')}"[:28]
        print(f"probe {bid} sat_when_high={fr['sat_when_high']} ...", flush=True)
        use = _probe_use_sat(feat, fname, bool(fr["sat_when_high"]))
        nav, meta = _switch_nav(comp, sat_nav, use, didx)
        meta["feat"] = fname
        meta["ic"] = fr["ic"]
        meta["sat_when_high"] = fr["sat_when_high"]
        nav.to_csv(OUT / f"nav_{bid}.csv", index=False)
        tip = _tip(live, nav)
        ev = _eval_row(base_w, _pack(nav), tip, fam="switch", sat_held_cagr=sat_held)
        books.append({"id": bid, "fam": "switch", "meta": meta, "eval": ev, "tip": tip})
        print(json.dumps({"book": bid, "meta": meta, "eval": ev}, ensure_ascii=False), flush=True)

    verdict = _verdict(ic_rows, books)
    generated = _utc()

    # Recommend next cycle definition from evidence
    top = ic_rows[0] if ic_rows else None
    tip_c = contrast.get("tip1y_minus_held") or {}
    recommendation = {
        "binding_gap": "tip_cagr_drag_timing",
        "best_leading_feat": None if top is None else top["feat"],
        "best_ic": None if top is None else top["ic"],
        "ic_gate_feats": [r["feat"] for r in gated],
        "tip_vs_held_highlights": {
            k: tip_c.get(k)
            for k in ("trail_rel_63", "comp_sells_21", "vol0050_21", "crisis", "zz08_bear", "pct_trail_drag")
        },
        "cycle_overlap_tip": overlap,
        "note": (
            "Prefer features that lead fwd_rel_21 and lift tip-drag overlap; "
            "do not return to calendar year switch."
        ),
    }

    payload = {
        "label": f"{SCREEN_ID}_{generated.replace(':', '').replace('-', '')}",
        "generated_at_utc": generated,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "status": "STAGE_A_SCREEN_DONE",
        "verdict": verdict,
        "live_wire": False,
        "soft_frozen_keep": True,
        "parent_observes_keep": True,
        "sat_held_cagr_lift_pp": None if sat_held is None else round(float(sat_held), 4),
        "leading_ic": ic_rows,
        "window_contrast": contrast,
        "cycle_overlap_tip": overlap,
        "worst_comp_lag_months": worst,
        "recommendation": recommendation,
        "books": [
            {"id": b["id"], "fam": b["fam"], "meta": b["meta"], "eval": b["eval"], "tip": b["tip"]} for b in books
        ],
    }

    ic_md = [
        "| feat | IC | \|IC\| | signHit | gate | sat_when_high |",
        "|---|---:|---:|---:|---|---|",
    ]
    for r in ic_rows:
        ic_md.append(
            f"| {r['feat']} | {r['ic']} | {r['abs_ic']} | {r['sign_hit']} | {r['ic_gate']} | {r['sat_when_high']} |"
        )

    screen_md = "\n".join(
        [
            f"# {SCREEN_ID}",
            "",
            f"Date: 2026-09-28 · Generated `{generated}`",
            f"Status: **{verdict}** · Soft-Frozen **KEEP** · parents **KEEP** · live wire **false**",
            "",
            "Tip-gap prediction: leading IC · tip vs held contrast · cycle overlap · ≤3 IC-gated probes.",
            "",
            "## Leading IC (fwd_rel_21)",
            "",
            *ic_md,
            "",
            "## Tip1y − held feature contrast",
            "",
            "```json",
            json.dumps(contrast.get("tip1y_minus_held", {}), indent=2, ensure_ascii=False),
            "```",
            "",
            "## Cycle overlap on tip-drag days",
            "",
            "```json",
            json.dumps(overlap, indent=2, ensure_ascii=False),
            "```",
            "",
            "## Worst COMP-lag months",
            "",
            "| month | rel_sum_pp | crisis% | zz08% | sells21 |",
            "|---|---:|---:|---:|---:|",
        ]
        + [
            f"| {r['month']} | {r['rel_sum_pp']} | {r['pct_crisis']} | {r['pct_zz08']} | {r['mean_sells21']} |"
            for r in worst[:8]
        ]
        + [
            "",
            "## Books / probes",
            "",
            "| ID | fam | heldCAGR↑ | tipCAGR↑ | tipClean | HIT |",
            "|---|---|---:|---:|---|---|",
        ]
        + [
            f"| {b['id']} | {b['fam']} | {b['eval']['held_cagr_lift_pp']} | {b['eval']['tip_ytd_cagr_pp']} | "
            f"{b['eval']['gates']['tip_clean']} | {b['eval']['hit']} |"
            for b in books
        ]
        + [
            "",
            "## Recommendation",
            "",
            "```json",
            json.dumps(recommendation, indent=2, ensure_ascii=False),
            "```",
            "",
            f"Verdict: **`{verdict}`**",
            "",
            f"Label: `{SCREEN_ID}_2026-09-28__{verdict}`",
            "",
        ]
    )

    hits = [b for b in books if b["eval"]["hit"]]
    dlines = [
        f"# {DECISION_ID}",
        "",
        f"Date: 2026-09-28 · Generated `{generated}`",
        f"Status: **{verdict}** · Soft-Frozen **KEEP** · COMPOSITE+SAT_RELAX observes **KEEP** · live wire **false**",
        "",
        f"Charter: `{CHARTER_ID}.md`",
        f"Screen: `{SCREEN_ID}.md`",
        "Parents: 0k9h cycle TIP_MDD_ONLY · register **0k9i**",
        "",
        "## Verdict",
        "",
        f"**`{verdict}`**",
        "",
        "## What gap to predict",
        "",
        "Binding gap = **tip CAGR drag timing** (when COMP HARD lags SAT), not held lift / not calendar year.",
        "",
        f"- Best leading feat: `{recommendation['best_leading_feat']}` IC={recommendation['best_ic']}",
        f"- IC-gated feats: {recommendation['ic_gate_feats']}",
        f"- Tip1y−held: `{json.dumps(recommendation['tip_vs_held_highlights'], ensure_ascii=False)}`",
        f"- Tip-drag cycle overlap: `{json.dumps(overlap, ensure_ascii=False)}`",
        "",
    ]
    if hits:
        dlines += [f"Probe HIT: `{hits[0]['id']}`", ""]
    elif gated:
        dlines += [
            "IC-gated features exist but probes did not clear tip-clean HIT — next charter should build **cycle around these feats**, not re-scan.",
            "",
        ]
    else:
        dlines += [
            "No feature cleared IC gate — tip contrast may still guide qualitative next cycle (see tip1y−held / overlap).",
            "",
        ]

    dlines += [
        "## Binding",
        "",
        "1. Soft-Frozen / Exact T+1 / COOL / SELL_a75 / live CONF α=0.10 KEEP",
        "2. COMPOSITE + SAT_RELAX observes **KEEP OPEN**",
        "3. Do not calendar-year switch · do not expand feature table after this scan",
        "4. Even GAP_PRED_HIT → observe ballot DRAFT only · no live",
        "",
        f"Label: `{DECISION_ID}_2026-09-28__{verdict}__NO_LIVE`",
        "",
    ]

    decision = {
        "label": f"{DECISION_ID}_2026-09-28__{verdict}__NO_LIVE",
        "status": verdict,
        "live_wire": False,
        "soft_frozen_keep": True,
        "parent_observes_keep": True,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "screen": f"research/ops/{SCREEN_ID}.md",
        "recommendation": recommendation,
        "ic_gate_feats": [r["feat"] for r in gated],
        "register": "0k9i",
        "generated_at_utc": generated,
    }

    write_ops_and_repro_pointer(OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", screen_md, kind="screen")
    write_ops_and_repro_pointer(
        OPS / f"{SCREEN_ID}.json",
        REP / f"{SCREEN_ID}.json",
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        kind="screen",
    )
    write_ops_and_repro_pointer(OPS / f"{DECISION_ID}.md", REP / f"{DECISION_ID}.md", "\n".join(dlines))
    write_ops_and_repro_pointer(
        OPS / f"{DECISION_ID}.json",
        REP / f"{DECISION_ID}.json",
        json.dumps(decision, indent=2, ensure_ascii=False) + "\n",
    )

    for path, open_s, done_s in (
        (OPS / f"{CHARTER_ID}.md", "Status: **Stage A OPEN**", f"Status: **Stage A DONE — `{verdict}`**"),
        (OPS / f"{CHARTER_ID}.zh-TW.md", "狀態：**Stage A OPEN**", f"狀態：**Stage A DONE — `{verdict}`**"),
    ):
        if path.exists():
            body = path.read_text(encoding="utf-8").replace(open_s, done_s, 1)
            body = body.replace(
                f"{CHARTER_ID}_2026-09-28__OPEN__NO_LIVE_WIRE",
                f"{CHARTER_ID}_2026-09-28__DONE_{verdict}__NO_LIVE_WIRE",
            )
            path.write_text(body, encoding="utf-8")
    cj_path = OPS / f"{CHARTER_ID}.json"
    if cj_path.exists():
        cj = json.loads(cj_path.read_text(encoding="utf-8"))
        cj["status"] = "STAGE_A_DONE"
        cj["verdict"] = verdict
        cj["label"] = f"{CHARTER_ID}_2026-09-28__DONE_{verdict}__NO_LIVE_WIRE"
        cj["screen"] = f"research/ops/{SCREEN_ID}.md"
        cj["decision"] = f"research/ops/{DECISION_ID}.md"
        cj["recommendation"] = recommendation
        cj_path.write_text(json.dumps(cj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps({"verdict": verdict, "recommendation": recommendation}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
