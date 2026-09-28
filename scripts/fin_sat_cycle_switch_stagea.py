#!/usr/bin/env python3
"""FIN×SAT 週期互斥切換 Stage A — ZigZag / regime-confirm / month-qtr (paper).

Charter: research/ops/FIN_SAT_CYCLE_SWITCH_STAGEA_CHARTER.md
Parents: 0k9g TIP_MDD_ONLY (year oracle not actionable) · COMP + SAT_RELAX KEEP.
NOT calendar-year switch · Soft-Frozen KEEP · no live · no peek-fit.
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
REPRO = ROOT / "repro" / "fin-sat-cycle-switch-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_SAT_CYCLE_SWITCH_STAGEA_CHARTER"
SCREEN_ID = "FIN_SAT_CYCLE_SWITCH_STAGEA_SCREEN"
DECISION_ID = "FIN_SAT_CYCLE_SWITCH_STAGEA_DECISION_PACK"
BASE_ID = "CTRL_LIVE_A10"

LIVE_NAV = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/ctrl_live_a10_daily_nav.csv"
COMP_NAV = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/comp_h150_x_a20_daily_nav.csv"
SAT_NAV = ROOT / "repro/sat-a20-relax-dual-paper-observe/outputs/sat_a20_relax_daily_nav.csv"

CAGR_FLOOR_PP = 0.10
HELD_MDD_MIN_PP = -0.25
HELD_ABS_MDD_MAX = 0.15
TIP_MDD_MIN_PP = 0.0
TIP_CAGR_MIN_PP = 0.0
VS_SAT_HELD_EXTRA_PP = 0.05

GRID: list[dict[str, Any]] = [
    {"id": "CTRL_LIVE_A10", "fam": "ctrl", "rule": "ctrl"},
    {"id": "REF_SAT_RELAX", "fam": "ref", "rule": "always_sat"},
    {"id": "REF_COMP_H150_A20", "fam": "ref", "rule": "always_comp"},
    {"id": "SW_ZZ08_BEAR_SAT", "fam": "switch", "rule": "zigzag", "thr": 0.08},
    {"id": "SW_ZZ12_BEAR_SAT", "fam": "switch", "rule": "zigzag", "thr": 0.12},
    {"id": "SW_CRISIS_K5", "fam": "switch", "rule": "regime_confirm", "labels": ("Crisis",), "k": 5},
    {"id": "SW_BEARCRISIS_K5", "fam": "switch", "rule": "regime_confirm", "labels": ("Bear", "Crisis"), "k": 5},
    {"id": "SW_MONTH_REL63", "fam": "switch", "rule": "period_rel", "freq": "M", "lookback": 63},
    {"id": "SW_QTR_REL126", "fam": "switch", "rule": "period_rel", "freq": "Q", "lookback": 126},
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


def _trail_ret(r: pd.Series, lookback: int) -> pd.Series:
    return (1.0 + r).rolling(lookback, min_periods=lookback).apply(
        lambda x: float(np.prod(x) - 1.0), raw=True
    )


def _zigzag_bear(close: pd.Series, thr: float) -> pd.Series:
    """True on peak→trough (bear half-cycle). Causal: state updates on close[t], use lag-1 outside."""
    px = close.astype(float).to_numpy()
    n = len(px)
    bear = np.zeros(n, dtype=bool)
    if n == 0:
        return pd.Series(bear, index=close.index)
    extreme = float(px[0])
    is_bear = False  # start assuming uptrend half until thr break
    bear[0] = False
    for i in range(1, n):
        p = float(px[i])
        if not is_bear:
            # uptrend: tracking peak; flip to bear if down thr from peak
            extreme = max(extreme, p)
            if extreme > 0 and (p / extreme - 1.0) <= -thr:
                is_bear = True
                extreme = p  # new trough candidate
        else:
            extreme = min(extreme, p)
            if extreme > 0 and (p / extreme - 1.0) >= thr:
                is_bear = False
                extreme = p
        bear[i] = is_bear
    return pd.Series(bear, index=close.index)


def _confirm_mask(raw: pd.Series, k: int) -> pd.Series:
    """Enter True after k consecutive True; exit after k consecutive False."""
    vals = raw.fillna(False).astype(bool).to_numpy()
    n = len(vals)
    out = np.zeros(n, dtype=bool)
    state = False
    run_t = 0
    run_f = 0
    for i in range(n):
        if vals[i]:
            run_t += 1
            run_f = 0
        else:
            run_f += 1
            run_t = 0
        if not state and run_t >= k:
            state = True
        elif state and run_f >= k:
            state = False
        out[i] = state
    return pd.Series(out, index=raw.index)


def _build_panel(dates: pd.DatetimeIndex, comp: pd.DataFrame, sat_nav: pd.DataFrame) -> pd.DataFrame:
    print("loading market + regime + 0050 ...", flush=True)
    market0 = sat.load_market()
    _p, _sleeve, _t, regime = e16_features(market0)
    reg = pd.Series(regime.values, index=pd.to_datetime(regime.index)).sort_index()
    reg = reg[~reg.index.duplicated(keep="last")]

    px = market0[market0["code"].astype(str) == "0050"].copy()
    px["date"] = pd.to_datetime(px["date"])
    px = px.sort_values("date").drop_duplicates("date")
    close = px.set_index("date")["adj_close" if "adj_close" in px.columns else "close"].astype(float)
    close = close[~close.index.duplicated(keep="last")]

    feat = pd.DataFrame({"date": dates})
    feat["regime"] = feat["date"].map(reg)
    feat["close0050"] = feat["date"].map(close)
    # parent daily returns for period-rel
    c = comp.set_index("date")["nav"].reindex(dates).astype(float)
    s = sat_nav.set_index("date")["nav"].reindex(dates).astype(float)
    feat["rc"] = c.pct_change().to_numpy()
    feat["rs"] = s.pct_change().to_numpy()
    feat["trail_c63"] = _trail_ret(pd.Series(feat["rc"]), 63).to_numpy()
    feat["trail_s63"] = _trail_ret(pd.Series(feat["rs"]), 63).to_numpy()
    feat["trail_c126"] = _trail_ret(pd.Series(feat["rc"]), 126).to_numpy()
    feat["trail_s126"] = _trail_ret(pd.Series(feat["rs"]), 126).to_numpy()

    zz08 = _zigzag_bear(feat["close0050"].ffill(), 0.08)
    zz12 = _zigzag_bear(feat["close0050"].ffill(), 0.12)
    feat["zz08_bear"] = zz08.to_numpy()
    feat["zz12_bear"] = zz12.to_numpy()

    # lag-1 causal copies
    for col in (
        "regime",
        "zz08_bear",
        "zz12_bear",
        "trail_c63",
        "trail_s63",
        "trail_c126",
        "trail_s126",
    ):
        feat[f"{col}_l1"] = feat[col].shift(1)
    return feat


def _period_rel_use_sat(feat: pd.DataFrame, *, freq: str, lookback: int) -> pd.Series:
    """At each period end, compare trail; apply choice to all days of NEXT period (causal)."""
    df = feat[["date", f"trail_c{lookback}_l1", f"trail_s{lookback}_l1"]].copy()
    df["period"] = df["date"].dt.to_period(freq)
    # signal available on last day of period uses l1 trails that day
    ends = df.groupby("period", sort=True).tail(1).copy()
    ends["pick_sat"] = ends[f"trail_c{lookback}_l1"] < ends[f"trail_s{lookback}_l1"]
    # map period -> next period's pick: shift picks forward one period
    ends = ends.sort_values("period")
    ends["next_period"] = ends["period"].shift(-1)
    # For period P's days, use pick decided at end of P-1
    pick_for = ends.dropna(subset=["next_period"]).set_index("next_period")["pick_sat"]
    mapped = df["period"].map(pick_for)
    # cold start: COMP (False)
    return mapped.fillna(False).astype(bool)


def _use_sat(feat: pd.DataFrame, spec: dict[str, Any]) -> pd.Series:
    rule = str(spec["rule"])
    if rule == "always_sat":
        return pd.Series(True, index=feat.index)
    if rule == "always_comp":
        return pd.Series(False, index=feat.index)
    if rule == "ctrl":
        raise ValueError("ctrl")
    if rule == "zigzag":
        thr = float(spec["thr"])
        col = "zz08_bear_l1" if abs(thr - 0.08) < 1e-12 else "zz12_bear_l1"
        return feat[col].fillna(False).astype(bool)
    if rule == "regime_confirm":
        labels = set(spec["labels"])
        k = int(spec["k"])
        raw = feat["regime_l1"].isin(labels)
        return _confirm_mask(raw, k)
    if rule == "period_rel":
        return _period_rel_use_sat(feat, freq=str(spec["freq"]), lookback=int(spec["lookback"]))
    raise ValueError(rule)


def _switch_nav(comp: pd.DataFrame, sat_nav: pd.DataFrame, feat: pd.DataFrame, spec: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    m = (
        comp.rename(columns={"nav": "nav_c"})
        .merge(sat_nav.rename(columns={"nav": "nav_s"}), on="date")
        .merge(feat, on="date", how="left")
        .sort_values("date")
        .reset_index(drop=True)
    )
    use_sat = _use_sat(m, spec)
    rc = m["nav_c"].pct_change().fillna(0.0)
    rs = m["nav_s"].pct_change().fillna(0.0)
    r = np.where(use_sat.to_numpy(), rs.to_numpy(), rc.to_numpy())
    nav = (1.0 + r).cumprod() * float(m["nav_c"].iloc[0])
    flips = int(np.sum(use_sat.to_numpy()[1:] != use_sat.to_numpy()[:-1])) if len(use_sat) > 1 else 0
    # cycle count approx = flips/2
    meta = {
        "pct_days_sat": round(float(use_sat.mean()) * 100.0, 2),
        "n_flips": flips,
        "n_cycles_est": flips // 2,
        "n_days": int(len(m)),
        "rule": str(spec.get("rule")),
    }
    return pd.DataFrame({"date": m["date"].to_numpy(), "nav": nav}), meta


def _episode_diag(feat: pd.DataFrame, comp: pd.DataFrame, sat_nav: pd.DataFrame) -> list[dict[str, Any]]:
    """Regime-episode COMP vs SAT (not calendar year)."""
    m = (
        feat[["date", "regime"]]
        .merge(comp.rename(columns={"nav": "nav_c"}), on="date")
        .merge(sat_nav.rename(columns={"nav": "nav_s"}), on="date")
        .sort_values("date")
        .reset_index(drop=True)
    )
    m["regime"] = m["regime"].fillna("Sideways")
    # episode id
    ep = (m["regime"] != m["regime"].shift(1)).cumsum()
    m["ep"] = ep
    rows: list[dict[str, Any]] = []
    for _, g in m.groupby("ep"):
        if len(g) < 5:
            continue
        rc = float(g["nav_c"].iloc[-1]) / float(g["nav_c"].iloc[0]) - 1.0
        rs = float(g["nav_s"].iloc[-1]) / float(g["nav_s"].iloc[0]) - 1.0
        rows.append(
            {
                "regime": str(g["regime"].iloc[0]),
                "start": str(g["date"].iloc[0].date()),
                "end": str(g["date"].iloc[-1].date()),
                "n_days": int(len(g)),
                "comp_ret_pct": round(rc * 100.0, 2),
                "sat_ret_pct": round(rs * 100.0, 2),
                "comp_minus_sat_pp": round((rc - rs) * 100.0, 2),
                "winner": "COMP" if rc > rs else ("SAT" if rs > rc else "TIE"),
            }
        )
    return rows


def _episode_summary(episodes: list[dict[str, Any]]) -> dict[str, Any]:
    df = pd.DataFrame(episodes)
    if df.empty:
        return {}
    out: dict[str, Any] = {}
    for reg, g in df.groupby("regime"):
        out[str(reg)] = {
            "n_episodes": int(len(g)),
            "mean_len": round(float(g["n_days"].mean()), 1),
            "comp_win_rate": round(float((g["winner"] == "COMP").mean()) * 100.0, 1),
            "mean_comp_minus_sat_pp": round(float(g["comp_minus_sat_pp"].mean()), 3),
        }
    return out


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
        "cagr_sign": "chal_minus_base",
    }


def _verdict(rows: list[dict[str, Any]]) -> str:
    switches = [r for r in rows if r["fam"] == "switch"]
    if any(r["eval"]["hit"] for r in switches):
        return "CYCLE_HIT"
    if any(
        r["eval"]["gates"]["tip_clean"]
        and r["eval"]["gates"]["economic"]
        and not r["eval"]["gates"]["vs_sat_held"]
        for r in switches
    ):
        return "TIP_CLEAN_SOFT"
    if any(
        r["eval"]["gates"]["tip_mdd"]
        and not r["eval"]["gates"]["tip_cagr"]
        and r["eval"]["gates"]["economic"]
        for r in rows
        if r["id"] != BASE_ID
    ):
        return "TIP_MDD_ONLY"
    if any(
        r["eval"]["gates"]["cagr"] and not r["eval"]["gates"]["tip_mdd"]
        for r in rows
        if r["id"] != BASE_ID
    ):
        return "TIP_BLOCK"
    if switches:
        return "DIAG_ONLY"
    return "NO_EDGE"


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    for p in (LIVE_NAV, COMP_NAV, SAT_NAV):
        if not p.exists():
            raise FileNotFoundError(p)

    print("loading parent NAVs ...", flush=True)
    live = _load_nav(LIVE_NAV)
    comp = _load_nav(COMP_NAV)
    sat_nav = _load_nav(SAT_NAV)
    dates = sorted(set(live["date"]) & set(comp["date"]) & set(sat_nav["date"]))
    live = live[live["date"].isin(dates)].reset_index(drop=True)
    comp = comp[comp["date"].isin(dates)].reset_index(drop=True)
    sat_nav = sat_nav[sat_nav["date"].isin(dates)].reset_index(drop=True)

    feat = _build_panel(pd.DatetimeIndex(dates), comp, sat_nav)
    episodes = _episode_diag(feat, comp, sat_nav)
    ep_sum = _episode_summary(episodes)
    pd.DataFrame(episodes).to_csv(OUT / "regime_episodes_comp_vs_sat.csv", index=False)
    (OUT / "episode_summary.json").write_text(json.dumps(ep_sum, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"episode_summary": ep_sum}, ensure_ascii=False), flush=True)

    base_w = _pack(live)
    sat_w = _pack(sat_nav)
    sat_held = cagr_lift_pp(
        (base_w.get("heldout_2019_plus") or {}).get("cagr"),
        (sat_w.get("heldout_2019_plus") or {}).get("cagr"),
    )

    rows: list[dict[str, Any]] = []
    for spec in GRID:
        bid = str(spec["id"])
        fam = str(spec["fam"])
        print(f"{bid} {spec.get('rule')} ...", flush=True)
        if fam == "ctrl":
            nav = live.copy()
            meta = {"pct_days_sat": 0.0, "n_flips": 0, "n_cycles_est": 0, "n_days": int(len(nav)), "rule": "ctrl"}
        else:
            nav, meta = _switch_nav(comp, sat_nav, feat, spec)
        nav.to_csv(OUT / f"nav_{bid}.csv", index=False)
        wpack = _pack(nav)
        tip = (
            {
                "ytd": {"mdd_improve_pp": 0.0, "cagr_lift_pp": 0.0, "gate": "PASS"},
                "trailing_1y": {"mdd_improve_pp": 0.0, "cagr_lift_pp": 0.0, "gate": "PASS"},
            }
            if bid == BASE_ID
            else _tip(live, nav)
        )
        ev = _eval_row(base_w, wpack, tip, fam=fam, sat_held_cagr=sat_held)
        rows.append({"id": bid, "fam": fam, "meta": meta, "windows": wpack, "tip": tip, "eval": ev, "spec": spec})
        print(json.dumps({"book": bid, "meta": meta, "eval": ev}, ensure_ascii=False), flush=True)

    verdict = _verdict(rows)
    generated = _utc()
    payload = {
        "label": f"{SCREEN_ID}_{generated.replace(':', '').replace('-', '')}",
        "generated_at_utc": generated,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "status": "STAGE_A_SCREEN_DONE",
        "verdict": verdict,
        "live_wire": False,
        "soft_frozen_keep": True,
        "parent_observes_keep": True,
        "not_year_switch": True,
        "sat_held_cagr_lift_pp": None if sat_held is None else round(float(sat_held), 4),
        "episode_summary": ep_sum,
        "gates": {
            "held_cagr_lift_pp": CAGR_FLOOR_PP,
            "held_mdd_pp_floor": HELD_MDD_MIN_PP,
            "tip_cagr_pp_floor": TIP_CAGR_MIN_PP,
            "tip_mdd_pp_floor": TIP_MDD_MIN_PP,
            "vs_sat_held_extra_pp": VS_SAT_HELD_EXTRA_PP,
        },
        "books": [
            {
                "id": r["id"],
                "fam": r["fam"],
                "meta": r["meta"],
                "windows": r["windows"],
                "tip": r["tip"],
                "eval": r["eval"],
            }
            for r in rows
        ],
    }

    screen_md = "\n".join(
        [
            f"# {SCREEN_ID}",
            "",
            f"Date: 2026-09-28 · Generated `{generated}`",
            f"Status: **{verdict}** · Soft-Frozen **KEEP** · parent observes **KEEP** · live wire **false** · **not year-switch**",
            "",
            "Cycle switches: ZigZag half-cycle · regime confirm K=5 · month/quarter REL · HIT tip-clean+held+vsSAT.",
            "",
            "## Regime-episode summary (not calendar year)",
            "",
            "```json",
            json.dumps(ep_sum, indent=2, ensure_ascii=False),
            "```",
            "",
            "## Books",
            "",
            "| ID | fam | %SAT | flips | cycles~ | heldCAGR↑ | tipCAGR↑ | tipClean | vsSAT | HIT |",
            "|---|---|---:|---:|---:|---:|---:|---|---|---|",
        ]
        + [
            "| {id} | {fam} | {ps} | {fl} | {cy} | {cagr} | {tc} | {clean} | {vs} | {hit} |".format(
                id=r["id"],
                fam=r["fam"],
                ps=r["meta"]["pct_days_sat"],
                fl=r["meta"]["n_flips"],
                cy=r["meta"].get("n_cycles_est", 0),
                cagr=r["eval"]["held_cagr_lift_pp"],
                tc=r["eval"]["tip_ytd_cagr_pp"],
                clean=r["eval"]["gates"]["tip_clean"],
                vs=r["eval"]["gates"]["vs_sat_held"],
                hit=r["eval"]["hit"],
            )
            for r in rows
        ]
        + ["", f"Verdict: **`{verdict}`**", "", f"Label: `{SCREEN_ID}_2026-09-28__{verdict}`", ""]
    )

    hits = [r for r in rows if r["eval"]["hit"]]
    hits.sort(key=lambda r: float(r["eval"]["held_cagr_lift_pp"] or -9), reverse=True)
    best = hits[0] if hits else None
    tip_clean_econ = [
        r
        for r in rows
        if r["fam"] == "switch" and r["eval"]["gates"]["tip_clean"] and r["eval"]["gates"]["economic"]
    ]
    tip_clean_econ.sort(key=lambda r: float(r["eval"]["held_cagr_lift_pp"] or -9), reverse=True)

    dlines = [
        f"# {DECISION_ID}",
        "",
        f"Date: 2026-09-28 · Generated `{generated}`",
        f"Status: **{verdict}** · Soft-Frozen **KEEP** · COMPOSITE+SAT_RELAX observes **KEEP** · live wire **false** · **not year-switch**",
        "",
        f"Charter: `{CHARTER_ID}.md`",
        f"Screen: `{SCREEN_ID}.md`",
        "Parents: 0k9g mutex TIP_MDD_ONLY · COMPOSITE · SAT_RELAX · register **0k9h**",
        "",
        "## Verdict",
        "",
        f"**`{verdict}`**",
        "",
        f"SAT held CAGR↑ = {None if sat_held is None else round(float(sat_held), 4)}pp.",
        "",
        "## Cycle diagnosis",
        "",
        f"Regime-episode COMP win-rate / mean Δpp: `{json.dumps(ep_sum, ensure_ascii=False)}`",
        "",
    ]
    if best:
        dlines += [
            f"Champion: `{best['id']}` · held CAGR↑ {best['eval']['held_cagr_lift_pp']} · %SAT {best['meta']['pct_days_sat']}",
            "",
            "Even HIT → observe ballot **DRAFT only** · parents KEEP · no live.",
            "",
        ]
    elif tip_clean_econ:
        top = tip_clean_econ[0]
        dlines += [
            f"Best tip-clean economic: `{top['id']}` · held CAGR↑ {top['eval']['held_cagr_lift_pp']} · vs_sat={top['eval']['gates']['vs_sat_held']}",
            "",
        ]
    else:
        dlines += ["No cycle switch cleared tip-clean economic gates.", ""]

    dlines += ["## Switch books", ""]
    for r in rows:
        if r["fam"] != "switch":
            continue
        g = r["eval"]["gates"]
        dlines.append(
            f"- `{r['id']}` · %SAT={r['meta']['pct_days_sat']} flips={r['meta']['n_flips']} · "
            f"heldCAGR↑ {r['eval']['held_cagr_lift_pp']} tipCAGR↑ {r['eval']['tip_ytd_cagr_pp']} · "
            f"tipClean={g['tip_clean']} econ={g['economic']} vsSAT={g['vs_sat_held']}"
        )
    dlines += [
        "",
        "## Binding",
        "",
        "1. Soft-Frozen / Exact T+1 / COOL / SELL_a75 / live CONF α=0.10 KEEP",
        "2. COMPOSITE + SAT_RELAX observes **KEEP OPEN**",
        "3. **Not year-switch** · do not promote calendar oracle",
        "4. Do not expand cycle thresholds after peek",
        "5. Even HIT → paper observe ballot DRAFT only · no live wire",
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
        "not_year_switch": True,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "screen": f"research/ops/{SCREEN_ID}.md",
        "best_hit": None if best is None else best["id"],
        "best_tip_clean_economic_switch": None if not tip_clean_econ else tip_clean_econ[0]["id"],
        "episode_summary": ep_sum,
        "sat_held_cagr_lift_pp": None if sat_held is None else round(float(sat_held), 4),
        "register": "0k9h",
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
            body = path.read_text(encoding="utf-8")
            body = body.replace(open_s, done_s, 1)
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
        cj_path.write_text(json.dumps(cj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps({"verdict": verdict, "n_books": len(rows), "sat_held": sat_held}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
