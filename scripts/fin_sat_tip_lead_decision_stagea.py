#!/usr/bin/env python3
"""FIN×SAT tip-lead decision-point Stage A (paper).

Charter: research/ops/FIN_SAT_TIP_LEAD_DECISION_STAGEA_CHARTER.md
Parents: 0k9n TIP_LAG_BLOCK · COMP + SAT_RELAX KEEP.
Soft-Frozen KEEP · Exact T+1 · no live · no feature-table expand.
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
REPRO = ROOT / "repro" / "fin-sat-tip-lead-decision-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_SAT_TIP_LEAD_DECISION_STAGEA_CHARTER"
SCREEN_ID = "FIN_SAT_TIP_LEAD_DECISION_STAGEA_SCREEN"
DECISION_ID = "FIN_SAT_TIP_LEAD_DECISION_STAGEA_DECISION_PACK"
BASE_ID = "CTRL_LIVE_A10"

LIVE_NAV = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/ctrl_live_a10_daily_nav.csv"
COMP_NAV = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/comp_h150_x_a20_daily_nav.csv"
SAT_NAV = ROOT / "repro/sat-a20-relax-dual-paper-observe/outputs/sat_a20_relax_daily_nav.csv"
COMP_FILLS = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/comp_h150_x_a20_fills.csv"

THETA = 0.01
HALF_THETA = 0.005
CAGR_FLOOR_PP = 0.10
HELD_MDD_MIN_PP = -0.25
HELD_ABS_MDD_MAX = 0.15
TIP_MDD_MIN_PP = 0.0
TIP_CAGR_MIN_PP = 0.0
VS_SAT_HELD_EXTRA_PP = 0.05
LEAD_KS = (1, 2, 3, 5)
LEAD_FEATS = [
    "crisis",
    "bearcrisis",
    "r0050_63",
    "mdd0050_63",
    "vol0050_21",
    "comp_sells_21",
    "zz08_bear",
    "trail_rel_63",
    "trail_slope_5",
]


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_nav(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)[["date", "nav"]].assign(
        nav=lambda x: x["nav"].astype(float)
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


def _zigzag_bear(close: pd.Series, thr: float = 0.08) -> pd.Series:
    px = close.astype(float).ffill().to_numpy()
    n = len(px)
    bear = np.zeros(n, dtype=float)
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
        bear[i] = 1.0 if is_bear else 0.0
    return pd.Series(bear, index=close.index)


def _switch_nav(comp: pd.DataFrame, sat_nav: pd.DataFrame, use_sat: np.ndarray) -> tuple[pd.DataFrame, dict[str, Any]]:
    m = (
        comp.rename(columns={"nav": "nav_c"})
        .merge(sat_nav.rename(columns={"nav": "nav_s"}), on="date")
        .sort_values("date")
        .reset_index(drop=True)
    )
    u = np.asarray(use_sat, dtype=bool)
    rc = m["nav_c"].pct_change().fillna(0.0)
    rs = m["nav_s"].pct_change().fillna(0.0)
    r = np.where(u, rs.to_numpy(), rc.to_numpy())
    nav = (1.0 + r).cumprod() * float(m["nav_c"].iloc[0])
    flips = int(np.sum(u[1:] != u[:-1])) if len(u) > 1 else 0
    return pd.DataFrame({"date": m["date"].to_numpy(), "nav": nav}), {
        "pct_days_sat": round(float(np.mean(u)) * 100, 2),
        "n_flips": flips,
    }


def _apply_hold(enter: np.ndarray, exit_sig: np.ndarray, *, min_hold: int = 0) -> np.ndarray:
    n = len(enter)
    out = np.zeros(n, dtype=bool)
    on = False
    held = 0
    for i in range(n):
        if not on:
            if enter[i]:
                on = True
                held = 1
        else:
            held += 1
            if held > min_hold and exit_sig[i]:
                on = False
                held = 0
        out[i] = on
    return out


def _eval_row(
    base_w: dict[str, Any],
    chal_w: dict[str, Any],
    tip: dict[str, Any],
    *,
    fam: str,
    sat_held_cagr: float | None,
) -> dict[str, Any]:
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
    shaped = bool(tip_clean and economic and vs_sat_ok)
    return {
        "held_cagr_lift_pp": None if cagr_pp is None else round(float(cagr_pp), 4),
        "held_mdd_pp": None if mdd_pp is None else round(float(mdd_pp), 4),
        "held_abs_mdd": None if abs_mdd is None else round(float(abs_mdd), 6),
        "tip_ytd_cagr_pp": tip_ytd_cagr,
        "tip_1y_cagr_pp": tip_1y_cagr,
        "tip_ytd_mdd_pp": tip_ytd_mdd,
        "tip_1y_mdd_pp": tip_1y_mdd,
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
            "shaped": shaped,
        },
        "hit": bool(fam == "switch" and shaped),
        "ub_shaped": bool(fam == "ub" and shaped),
    }


def _build_panel(dates: pd.DatetimeIndex, comp: pd.DataFrame, sat_nav: pd.DataFrame) -> pd.DataFrame:
    print("building panel ...", flush=True)
    market0 = sat.load_market()
    _p, _s, _t, regime = e16_features(market0)
    reg = pd.Series(regime.values, index=pd.to_datetime(regime.index)).sort_index()
    reg = reg[~reg.index.duplicated(keep="last")]
    px = market0[market0["code"].astype(str) == "0050"].copy()
    px["date"] = pd.to_datetime(px["date"])
    close = px.drop_duplicates("date").set_index("date")["adj_close" if "adj_close" in px.columns else "close"].astype(float)
    close = close[~close.index.duplicated(keep="last")]
    r0050 = close.pct_change()

    c = comp.set_index("date")["nav"].reindex(dates).astype(float)
    s = sat_nav.set_index("date")["nav"].reindex(dates).astype(float)
    rel = c.pct_change() - s.pct_change()

    sells = pd.Series(0.0, index=dates)
    if COMP_FILLS.exists():
        f = pd.read_csv(COMP_FILLS)
        f["fill_date"] = pd.to_datetime(f["fill_date"])
        cnt = f[f["side"].astype(str).str.upper() == "SELL"].groupby("fill_date").size()
        sells = cnt.reindex(dates).fillna(0.0)

    feat = pd.DataFrame({"date": dates})
    feat["regime"] = feat["date"].map(reg)
    feat["close0050"] = feat["date"].map(close)
    feat["rel"] = rel.to_numpy()
    feat["trail_rel_63"] = _trail(pd.Series(feat["rel"]), 63).to_numpy()
    feat["trail_slope_5"] = pd.Series(feat["trail_rel_63"]).diff(5).to_numpy()
    feat["crisis"] = (feat["regime"] == "Crisis").astype(float)
    feat["bearcrisis"] = feat["regime"].isin(["Bear", "Crisis"]).astype(float)
    feat["r0050_63"] = _trail(feat["date"].map(r0050), 63).to_numpy()
    feat["mdd0050_63"] = (
        feat["close0050"]
        .ffill()
        .rolling(63, min_periods=63)
        .apply(lambda w: float((pd.Series(w) / pd.Series(w).cummax() - 1.0).min()), raw=True)
        .to_numpy()
    )
    feat["vol0050_21"] = feat["date"].map(r0050).rolling(21, min_periods=21).std().to_numpy()
    feat["comp_sells_21"] = sells.rolling(21, min_periods=1).sum().to_numpy()
    feat["zz08_bear"] = _zigzag_bear(feat["close0050"]).to_numpy()
    feat["sat_lead"] = feat["trail_rel_63"] <= -THETA
    feat["enter"] = feat["sat_lead"] & ~feat["sat_lead"].shift(1).fillna(False)
    feat["exit"] = (~feat["sat_lead"]) & feat["sat_lead"].shift(1).fillna(False)
    med_sells = float(feat["comp_sells_21"].median(skipna=True))
    feat["sells_hi"] = feat["comp_sells_21"] > med_sells
    for col in LEAD_FEATS + ["sat_lead", "sells_hi"]:
        feat[f"{col}_l1"] = feat[col].shift(1)
    feat["trail_rel_63_l6"] = feat["trail_rel_63"].shift(6)
    feat.attrs["med_sells"] = med_sells
    return feat


def _spearman(x: pd.Series, y: pd.Series) -> float | None:
    a = pd.concat([x, y], axis=1).dropna()
    if len(a) < 60:
        return None
    return float(a.iloc[:, 0].corr(a.iloc[:, 1], method="spearman"))


def _lead_analysis(feat: pd.DataFrame) -> dict[str, Any]:
    y = feat["enter"].astype(float)
    rows: list[dict[str, Any]] = []
    for k in LEAD_KS:
        for f in LEAD_FEATS:
            x = feat[f].shift(k)
            ic = _spearman(x, y)
            # binary lift for high-x → enter (use median split; for crisis use >0.5)
            if f in ("crisis", "bearcrisis", "zz08_bear"):
                hi = x > 0.5
            else:
                hi = x > x.median()
            # for trail_rel / slope: low side predicts enter (COMP lag)
            if f in ("trail_rel_63", "trail_slope_5", "r0050_63", "mdd0050_63"):
                hi = x < x.median()
            base = float(y.mean()) if len(y) else 0.0
            rate = float(y[hi.fillna(False)].mean()) if hi.fillna(False).any() else None
            lift = None if rate is None or base <= 0 else rate / base
            rows.append(
                {
                    "feat": f,
                    "k": k,
                    "ic": None if ic is None else round(ic, 4),
                    "abs_ic": None if ic is None else round(abs(ic), 4),
                    "enter_rate_selected": None if rate is None else round(rate, 4),
                    "base_enter_rate": round(base, 4),
                    "lift": None if lift is None else round(lift, 3),
                }
            )
    rows.sort(key=lambda r: (r["abs_ic"] is None, -(r["abs_ic"] or -1), r["k"]))

    # pre-enter window means
    enter_idx = np.where(feat["enter"].fillna(False).to_numpy())[0]
    pre_rows: list[dict[str, Any]] = []
    for f in LEAD_FEATS:
        base_mean = float(feat[f].mean(skipna=True))
        vals = []
        for i in enter_idx:
            lo = max(0, i - 5)
            hi = i  # exclusive: days -5..-1
            if hi <= lo:
                continue
            vals.append(float(feat[f].iloc[lo:hi].mean()))
        pre_mean = float(np.mean(vals)) if vals else None
        pre_rows.append(
            {
                "feat": f,
                "pre_enter_mean": None if pre_mean is None else round(pre_mean, 6),
                "base_mean": round(base_mean, 6),
                "delta": None if pre_mean is None else round(pre_mean - base_mean, 6),
            }
        )
    pre_rows.sort(key=lambda r: abs(r["delta"] or 0), reverse=True)

    tip = feat["date"] >= (pd.Timestamp(feat["date"].max()) - pd.Timedelta(days=365))
    tip_enters = int((feat["enter"] & tip).sum())
    return {
        "n_enter": int(feat["enter"].sum()),
        "n_exit": int(feat["exit"].sum()),
        "n_enter_tip": tip_enters,
        "top_lead_ic": rows[:12],
        "all_lead_ic": rows,
        "pre_enter_deltas": pre_rows,
        "lead_signal": bool(
            any((r["abs_ic"] or 0) >= 0.08 and r["k"] >= 1 for r in rows[:5])
            or any(abs(r["delta"] or 0) > 0 for r in pre_rows[:3] if r["feat"] in ("crisis", "comp_sells_21", "trail_slope_5"))
        ),
    }


def _verdict(lead: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    sw = [r for r in rows if r["fam"] == "switch"]
    if any(r["eval"]["hit"] for r in sw):
        return "LEAD_HIT"
    ub_ok = any(r["eval"]["ub_shaped"] for r in rows if r["fam"] == "ub")
    causal_tip_fail = all(not r["eval"]["gates"]["tip_cagr"] for r in sw)
    if lead.get("lead_signal") and ub_ok and not any(r["eval"]["hit"] for r in sw):
        # distinguish: if causal still all tip CAGR− keep TIP_LAG_BLOCK when no actionable lead probe edge
        if causal_tip_fail and not any(r["eval"]["gates"]["tip_clean"] for r in sw):
            # lead_signal alone without tip-clean probe → still lag block unless IC strong
            strong = any((r.get("abs_ic") or 0) >= 0.12 for r in (lead.get("top_lead_ic") or []))
            return "LEAD_SIGNAL" if strong else "TIP_LAG_BLOCK"
        return "LEAD_SIGNAL"
    if ub_ok and causal_tip_fail:
        return "TIP_LAG_BLOCK"
    if any(r["eval"]["gates"]["economic"] and r["eval"]["gates"]["tip_mdd"] and not r["eval"]["gates"]["tip_cagr"] for r in sw):
        return "TIP_MDD_ONLY"
    return "NO_EDGE"


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)

    live = _load_nav(LIVE_NAV)
    comp = _load_nav(COMP_NAV)
    sat_nav = _load_nav(SAT_NAV)
    dates = sorted(set(live["date"]) & set(comp["date"]) & set(sat_nav["date"]))
    live = live[live["date"].isin(dates)].reset_index(drop=True)
    comp = comp[comp["date"].isin(dates)].reset_index(drop=True)
    sat_nav = sat_nav[sat_nav["date"].isin(dates)].reset_index(drop=True)

    feat = _build_panel(pd.DatetimeIndex(dates), comp, sat_nav)
    lead = _lead_analysis(feat)
    feat.to_csv(OUT / "tip_lead_panel.csv", index=False)
    (OUT / "tip_lead_diag.json").write_text(json.dumps(lead, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"lead_top": lead["top_lead_ic"][:5], "pre": lead["pre_enter_deltas"][:5]}, ensure_ascii=False), flush=True)

    # masks
    sat_l1 = feat["sat_lead_l1"].fillna(False).to_numpy()
    trail_l1 = feat["trail_rel_63_l1"]
    trail_l6 = feat["trail_rel_63_l6"]
    half = (trail_l1 <= -HALF_THETA).fillna(False).to_numpy()
    slope = (
        (trail_l1 < trail_l6).fillna(False)
        & (trail_l6 <= 0).fillna(False)
        & (trail_l1 <= -HALF_THETA).fillna(False)
    ).to_numpy()
    conf_enter = (
        ((feat["crisis_l1"] > 0.5) | feat["sells_hi_l1"].fillna(False)) & (trail_l1 < 0)
    ).fillna(False).to_numpy()
    conf_exit = (trail_l1 >= 0).fillna(False).to_numpy()
    conf = _apply_hold(conf_enter, conf_exit, min_hold=5)
    lead_or = (
        feat["sat_lead_l1"].fillna(False) | ((feat["crisis_l1"] > 0.5) & (trail_l1 <= -HALF_THETA).fillna(False))
    ).to_numpy()
    # UB enter-1: sat_lead OR day before enter
    ub_m1 = (feat["sat_lead"] | feat["enter"].shift(-1).fillna(False)).fillna(False).to_numpy()
    ub_sd = feat["sat_lead"].fillna(False).to_numpy()

    books: list[dict[str, Any]] = [
        {"id": BASE_ID, "fam": "ctrl"},
        {"id": "REF_SAT_RELAX", "fam": "ref", "use": "sat"},
        {"id": "REF_COMP_H150_A20", "fam": "ref", "use": "comp"},
        {"id": "UB_ENTER_M1", "fam": "ub", "mask": ub_m1},
        {"id": "UB_STATE_SD", "fam": "ub", "mask": ub_sd},
        {"id": "R_SAT_LEAD_L1", "fam": "switch", "mask": sat_l1},
        {"id": "R_HALF_THETA_L1", "fam": "switch", "mask": half},
        {"id": "R_SLOPE_EARLY_L1", "fam": "switch", "mask": slope},
        {"id": "R_CONF_EARLY_L1", "fam": "switch", "mask": conf},
        {"id": "R_LEAD_OR_STATE_L1", "fam": "switch", "mask": lead_or},
    ]

    base_w = _pack(live)
    sat_held = cagr_lift_pp(
        (base_w.get("heldout_2019_plus") or {}).get("cagr"),
        (_pack(sat_nav).get("heldout_2019_plus") or {}).get("cagr"),
    )

    rows: list[dict[str, Any]] = []
    for spec in books:
        bid = spec["id"]
        fam = spec["fam"]
        print(f"{bid} ...", flush=True)
        if fam == "ctrl":
            nav = live.copy()
            meta = {"pct_days_sat": 0.0, "n_flips": 0, "rule": "ctrl"}
        elif fam == "ref":
            nav = sat_nav.copy() if spec["use"] == "sat" else comp.copy()
            meta = {"pct_days_sat": 100.0 if spec["use"] == "sat" else 0.0, "n_flips": 0, "rule": spec["use"]}
        else:
            nav, meta = _switch_nav(comp, sat_nav, spec["mask"])
            meta["rule"] = bid
        nav.to_csv(OUT / f"nav_{bid}.csv", index=False)
        tip = (
            {
                "ytd": {"mdd_improve_pp": 0.0, "cagr_lift_pp": 0.0, "gate": "PASS"},
                "trailing_1y": {"mdd_improve_pp": 0.0, "cagr_lift_pp": 0.0, "gate": "PASS"},
            }
            if bid == BASE_ID
            else _tip(live, nav)
        )
        ev = _eval_row(base_w, _pack(nav), tip, fam=fam, sat_held_cagr=sat_held)
        rows.append({"id": bid, "fam": fam, "meta": meta, "eval": ev, "tip": tip})
        print(json.dumps({"book": bid, "meta": meta, "eval": ev}, ensure_ascii=False), flush=True)

    verdict = _verdict(lead, rows)
    generated = _utc()
    hits = [r for r in rows if r["eval"]["hit"]]
    hits.sort(key=lambda r: float(r["eval"]["held_cagr_lift_pp"] or -9), reverse=True)
    ub_shaped = [r for r in rows if r["eval"]["ub_shaped"]]
    ub_shaped.sort(key=lambda r: float(r["eval"]["held_cagr_lift_pp"] or -9), reverse=True)

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
        "lead": {
            "n_enter": lead["n_enter"],
            "n_exit": lead["n_exit"],
            "n_enter_tip": lead["n_enter_tip"],
            "lead_signal": lead["lead_signal"],
            "top_lead_ic": lead["top_lead_ic"],
            "pre_enter_deltas": lead["pre_enter_deltas"],
        },
        "books": [
            {"id": r["id"], "fam": r["fam"], "meta": r["meta"], "eval": r["eval"], "tip": r["tip"]} for r in rows
        ],
        "register": "0k9o",
    }

    screen_md = "\n".join(
        [
            f"# {SCREEN_ID}",
            "",
            f"Date: 2026-09-28 · Generated `{generated}`",
            f"Status: **{verdict}** · Soft-Frozen **KEEP** · parents **KEEP** · live wire **false**",
            "",
            "## Lead diagnosis",
            "",
            f"- enters={lead['n_enter']} (tip {lead['n_enter_tip']}) · exits={lead['n_exit']} · lead_signal=`{lead['lead_signal']}`",
            "",
            "| feat | k | IC | lift |",
            "|---|---:|---:|---:|",
        ]
        + [
            f"| {r['feat']} | {r['k']} | {r['ic']} | {r['lift']} |"
            for r in lead["top_lead_ic"][:8]
        ]
        + [
            "",
            "## Pre-enter (−5..−1) deltas",
            "",
            "| feat | pre | base | Δ |",
            "|---|---:|---:|---:|",
        ]
        + [
            f"| {r['feat']} | {r['pre_enter_mean']} | {r['base_mean']} | {r['delta']} |"
            for r in lead["pre_enter_deltas"][:6]
        ]
        + [
            "",
            "## Books",
            "",
            "| ID | fam | %SAT | heldCAGR↑ | tipCAGR↑ | tipClean | shaped | mark |",
            "|---|---|---:|---:|---:|---|---|---|",
        ]
        + [
            "| {id} | {fam} | {ps} | {cagr} | {tc} | {clean} | {sh} | {mark} |".format(
                id=r["id"],
                fam=r["fam"],
                ps=r["meta"]["pct_days_sat"],
                cagr=r["eval"]["held_cagr_lift_pp"],
                tc=r["eval"]["tip_ytd_cagr_pp"],
                clean=r["eval"]["gates"]["tip_clean"],
                sh=r["eval"]["gates"]["shaped"],
                mark=("HIT" if r["eval"]["hit"] else ("UB" if r["eval"]["ub_shaped"] else "·")),
            )
            for r in rows
        ]
        + ["", f"Verdict: **`{verdict}`**", "", f"Label: `{SCREEN_ID}_2026-09-28__{verdict}`", ""]
    )

    dlines = [
        f"# {DECISION_ID}",
        "",
        f"Date: 2026-09-28 · Generated `{generated}`",
        f"Status: **{verdict}** · Soft-Frozen **KEEP** · COMPOSITE+SAT_RELAX observes **KEEP** · live wire **false**",
        "",
        f"Charter: `{CHARTER_ID}.md`",
        f"Screen: `{SCREEN_ID}.md`",
        "Parents: 0k9n · register **0k9o**",
        "",
        "## Verdict",
        "",
        f"**`{verdict}`**",
        "",
        "## Reading",
        "",
        f"- enters={lead['n_enter']} tip_enters={lead['n_enter_tip']} · lead_signal=`{lead['lead_signal']}`",
        f"- top IC: {json.dumps(lead['top_lead_ic'][:5], ensure_ascii=False)}",
        f"- pre-enter Δ: {json.dumps(lead['pre_enter_deltas'][:4], ensure_ascii=False)}",
        "",
    ]
    if ub_shaped:
        dlines.append("UB shaped:")
        for r in ub_shaped:
            dlines.append(
                f"- `{r['id']}` held↑ {r['eval']['held_cagr_lift_pp']} tipY↑ {r['eval']['tip_ytd_cagr_pp']}"
            )
        dlines.append("")
    if hits:
        dlines += [f"Champion: `{hits[0]['id']}`", ""]
    else:
        dlines += ["No causal LEAD_HIT.", ""]

    dlines += ["## Books", ""]
    for r in rows:
        if r["fam"] == "ctrl":
            continue
        g = r["eval"]["gates"]
        dlines.append(
            f"- `{r['id']}` ({r['fam']}) · %SAT={r['meta']['pct_days_sat']} · "
            f"held↑ {r['eval']['held_cagr_lift_pp']} tipY↑ {r['eval']['tip_ytd_cagr_pp']} · "
            f"tipClean={g['tip_clean']} shaped={g['shaped']}"
        )
    dlines += [
        "",
        "## Binding",
        "",
        "1. Soft-Frozen / Exact T+1 / COOL / SELL_a75 / live CONF α=0.10 KEEP",
        "2. COMPOSITE + SAT_RELAX observes **KEEP OPEN**",
        "3. Do not expand feature table after peek",
        "4. UB diagnosis only · no observe · no live",
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
        "lead_signal": lead.get("lead_signal"),
        "best_hit": None if not hits else hits[0]["id"],
        "best_ub_shaped": None if not ub_shaped else ub_shaped[0]["id"],
        "charter": f"research/ops/{CHARTER_ID}.md",
        "screen": f"research/ops/{SCREEN_ID}.md",
        "register": "0k9o",
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
    cj = json.loads((OPS / f"{CHARTER_ID}.json").read_text(encoding="utf-8"))
    cj["status"] = "STAGE_A_DONE"
    cj["verdict"] = verdict
    cj["label"] = f"{CHARTER_ID}_2026-09-28__DONE_{verdict}__NO_LIVE_WIRE"
    cj["screen"] = f"research/ops/{SCREEN_ID}.md"
    cj["decision"] = f"research/ops/{DECISION_ID}.md"
    (OPS / f"{CHARTER_ID}.json").write_text(json.dumps(cj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps({"verdict": verdict, "best_hit": None if not hits else hits[0]["id"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
