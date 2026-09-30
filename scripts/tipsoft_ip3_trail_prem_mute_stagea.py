#!/usr/bin/env python3
"""I_p3 trailing-premium mute Stage A (0kb1).

After 0kaz (AND confirm NO_EDGE) and 0kb0 (asymm/soft-α YEAR_SOFT, held+ = 0):
raise year-wins / cut year-regret vs oracle **without year dummies**.

Pipeline:
1. DIAG census of live-win years / drag episodes (NEARon ∧ prem_p3 hurt)
2. Causal trailing prem mute → 3-state LIVE / P3 / P3+P4
3. Rank by year-regret / year-wins with held ≥ NEAR−ε + sealed/tip floors

Exact T+1 only · hybrid T+0 FORBIDDEN · Soft KEEP · Path4 live OFF · no year-cut.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from cool_c8_proxy_observe_helpers import build_cool_c8_exposure
from e45_paper_harness import WINDOWS_STANDARD, window_stats
from fin_sell_quality_helpers import cagr_lift_pp
from ops_repro_ssot import write_ops_and_repro_pointer, write_repro_pointer
from research_metric_helpers import mdd_delta_pp

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "tipsoft-ip3-trail-prem-mute-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

LIVESTACK = ROOT / "repro" / "fin-sat-path3-path4-livestack-twin-stageb" / "outputs"
ALIGN = ROOT / "repro" / "research-live-align-gap-stagea" / "outputs"
HARDEN = ROOT / "repro" / "meta-detect-sealed-mdd-harden-stagea" / "outputs"
P3_SIG = (
    ROOT / "repro" / "fin-sat-path3-t0-dual-paper-observe" / "outputs" / "p3_t0_state_signal.csv"
)

CHARTER_ID = "TIPSOFT_IP3_TRAIL_PREM_MUTE_STAGEA_CHARTER"
SCREEN_ID = "TIPSOFT_IP3_TRAIL_PREM_MUTE_STAGEA_SCREEN"
DECISION_ID = "TIPSOFT_IP3_TRAIL_PREM_MUTE_STAGEA_DECISION_PACK"
REGISTER = "0kb1"
PARENTS = ("0kb0", "0kaz", "0kay", "0kaw")
MECH = "TIPSOFT_IP3_TRAIL_PREM_MUTE"

BASE_ID = "BASE_LIVE_FUSE_COOL"
NEAR_ID = "REF_P3_THETA_NEARPEAK3"
P34_ID = "REF_P4_C001_NEAR_AND_SAT"
SEALED_MDD_FLOOR_PP = -0.25
TIP_Y_FLOOR_PP = -1.0
HELD_CAGR_FLOOR_PP = 0.10
P3_THETA = 0.005
# held can be slightly under NEAR if year-wins / regret clearly improve
HELD_EPS_VS_NEAR = -0.05
HELD_SOFT_EPS_VS_NEAR = -0.15  # YEAR_SOFT near-miss band
YEAR_REGRET_IMPROVE_FLOOR = 0.05
YEAR_WINS_IMPROVE_FLOOR = 1  # at least +1 year win vs NEAR


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_nav(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"])
    return (
        df[["date", "nav"]]
        .assign(
            date=lambda x: pd.to_datetime(x["date"]).dt.normalize(),
            nav=lambda x: x["nav"].astype(float),
        )
        .sort_values("date")
        .reset_index(drop=True)
    )


def _returns(nav: pd.DataFrame) -> pd.Series:
    s = nav.set_index("date")["nav"].astype(float).sort_index()
    return s.pct_change().fillna(0.0)


def _nav_from_returns(r: pd.Series, nav0: float) -> pd.DataFrame:
    nav = (1.0 + r.fillna(0.0)).cumprod() * float(nav0)
    return pd.DataFrame({"date": nav.index, "nav": nav.to_numpy()}).reset_index(drop=True)


def _dd_from_peak(nav: pd.DataFrame, win: int = 63) -> pd.Series:
    s = nav.set_index("date")["nav"].astype(float).sort_index()
    peak = s.rolling(win, min_periods=5).max()
    return (s / peak - 1.0).fillna(0.0)


def _proxy_mdd63(nav: pd.DataFrame) -> pd.Series:
    s = nav.set_index("date")["nav"].astype(float).sort_index()
    peak = s.cummax()
    dd = s / peak - 1.0
    return dd.rolling(63, min_periods=5).min().fillna(0.0)


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
            out[wname] = {"cagr_lift_pp": None, "mdd_improve_pp": None}
            continue
        bn = b["nav"].astype(float) / float(b["nav"].iloc[0])
        cn = c["nav"].astype(float) / float(c["nav"].iloc[0])
        b_mdd = float((bn / bn.cummax() - 1.0).min())
        c_mdd = float((cn / cn.cummax() - 1.0).min())
        years = (len(b) - 1) / 252.0
        bc = float(bn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        cc = float(cn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        out[wname] = {
            "cagr_lift_pp": None
            if cagr_lift_pp(bc, cc) is None
            else round(float(cagr_lift_pp(bc, cc)), 4),
            "mdd_improve_pp": round(float(mdd_delta_pp(b_mdd, c_mdd)), 4),
        }
    return out


def _delta(base_w: dict, chal_w: dict) -> dict[str, Any]:
    out = {}
    for k in ("full", "heldout_2019_plus", "sealed_2023_plus"):
        b, c = base_w.get(k) or {}, chal_w.get(k) or {}
        out[k] = {
            "cagr_lift_pp": None
            if cagr_lift_pp(b.get("cagr"), c.get("cagr")) is None
            else round(float(cagr_lift_pp(b.get("cagr"), c.get("cagr"))), 4),
            "mdd_improve_pp": None
            if b.get("max_drawdown") is None or c.get("max_drawdown") is None
            else round(float(mdd_delta_pp(b["max_drawdown"], c["max_drawdown"])), 4),
        }
    return out


def _arm_verdict_vs_live(delta: dict[str, Any], tip: dict[str, Any]) -> str:
    held = delta["heldout_2019_plus"]
    sealed = delta["sealed_2023_plus"]
    tip_y = (tip.get("ytd") or {}).get("cagr_lift_pp")
    if held.get("cagr_lift_pp") is None or sealed.get("mdd_improve_pp") is None:
        return "INCOMPLETE"
    held_ok = float(held["cagr_lift_pp"]) >= HELD_CAGR_FLOOR_PP
    sealed_ok = float(sealed["mdd_improve_pp"]) >= SEALED_MDD_FLOOR_PP
    tip_ok = tip_y is None or float(tip_y) >= TIP_Y_FLOOR_PP
    full_ok = float(delta["full"].get("cagr_lift_pp") or 0) > 0
    if held_ok and sealed_ok and tip_ok and full_ok:
        return "HIT"
    if held_ok and sealed_ok and tip_ok:
        return "HELD_HIT"
    if sealed_ok and tip_ok and float(held["cagr_lift_pp"]) > 0.02:
        return "SOFT"
    if float(sealed["mdd_improve_pp"]) < SEALED_MDD_FLOOR_PP:
        return "MDD_BLOCK"
    if tip_y is not None and float(tip_y) < TIP_Y_FLOOR_PP:
        return "TIP_BLOCK"
    return "NO_EDGE"


def _year_rets(r: pd.Series) -> pd.Series:
    df = r.copy().to_frame("r")
    df["year"] = df.index.year
    out = {}
    for y, g in df.groupby("year"):
        if len(g) < 2:
            continue
        out[int(y)] = float((1.0 + g["r"]).prod() - 1.0) * 100.0
    return pd.Series(out, dtype=float)


def _year_oracle_table(
    policy_r: pd.Series, live_r: pd.Series, near_r: pd.Series, p34_r: pd.Series
) -> dict[str, Any]:
    yp = _year_rets(policy_r)
    yl = _year_rets(live_r)
    yn = _year_rets(near_r)
    y4 = _year_rets(p34_r)
    years = sorted(set(yp.index) & set(yl.index) & set(yn.index) & set(y4.index))
    if not years:
        return {
            "mean_policy": None,
            "mean_oracle": None,
            "gap_to_oracle_pp": None,
            "year_wins": 0,
            "n_years": 0,
            "best_counts": {},
            "years": [],
        }
    rows = []
    best_counts = {"live": 0, "P3": 0, "P3+P4": 0}
    year_wins = 0
    for y in years:
        live_v, near_v, p34_v, pol_v = float(yl[y]), float(yn[y]), float(y4[y]), float(yp[y])
        oracle = max(live_v, near_v, p34_v)
        base_best = max(
            [("live", live_v), ("P3", near_v), ("P3+P4", p34_v)], key=lambda t: t[1]
        )[0]
        best_counts[base_best] += 1
        # win if within 1e-6 of oracle (ties count)
        if pol_v >= oracle - 1e-6:
            year_wins += 1
        rows.append(
            {
                "year": y,
                "live": round(live_v, 4),
                "P3": round(near_v, 4),
                "P3+P4": round(p34_v, 4),
                "policy": round(pol_v, 4),
                "oracle": round(oracle, 4),
                "gap": round(oracle - pol_v, 4),
                "base_best": base_best,
                "policy_wins": bool(pol_v >= oracle - 1e-6),
            }
        )
    mean_pol = float(sum(r["policy"] for r in rows) / len(rows))
    mean_ora = float(sum(r["oracle"] for r in rows) / len(rows))
    return {
        "mean_policy": round(mean_pol, 4),
        "mean_oracle": round(mean_ora, 4),
        "gap_to_oracle_pp": round(mean_ora - mean_pol, 4),
        "year_wins": int(year_wins),
        "n_years": len(rows),
        "best_counts": best_counts,
        "years": rows,
    }


def _episodes(mask: np.ndarray, dates: pd.DatetimeIndex) -> list[dict[str, Any]]:
    """Contiguous True runs → episode records."""
    out = []
    n = len(mask)
    i = 0
    while i < n:
        if not mask[i]:
            i += 1
            continue
        j = i
        while j < n and mask[j]:
            j += 1
        out.append(
            {
                "start": str(pd.Timestamp(dates[i]).date()),
                "end": str(pd.Timestamp(dates[j - 1]).date()),
                "n_days": int(j - i),
                "year_start": int(pd.Timestamp(dates[i]).year),
            }
        )
        i = j
    return out


def _build_census(
    panel_index: pd.DatetimeIndex,
    nearpeak3: pd.Series,
    prem_p3: pd.Series,
    prem_p4: pd.Series,
    sat_lead: pd.Series,
    risk_on: pd.Series,
    dd63: pd.Series,
    trail: pd.Series,
    live_r: pd.Series,
    near_r: pd.Series,
    p34_r: pd.Series,
) -> dict[str, Any]:
    yg = _year_oracle_table(near_r, live_r, near_r, p34_r)
    live_win_years = {r["year"] for r in yg["years"] if r["base_best"] == "live"}
    p3_win_years = {r["year"] for r in yg["years"] if r["base_best"] == "P3"}
    p34_win_years = {r["year"] for r in yg["years"] if r["base_best"] == "P3+P4"}

    years = pd.Series(panel_index.year, index=panel_index)
    near_on = nearpeak3.astype(bool)
    # drag day: NEAR on and same-bar prem hurts (DIAG only for labeling)
    drag = near_on & (prem_p3 < 0)
    help_ = near_on & (prem_p3 > 0)
    live_year = years.isin(live_win_years)
    p3_year = years.isin(p3_win_years)

    drag_live = (drag & live_year).to_numpy()
    drag_p3y = (drag & p3_year).to_numpy()
    eps_live = _episodes(drag_live, panel_index)
    eps_p3 = _episodes(drag_p3y, panel_index)

    def _feat(mask: pd.Series) -> dict[str, Any]:
        m = mask.fillna(False)
        if int(m.sum()) == 0:
            return {"n_days": 0}
        return {
            "n_days": int(m.sum()),
            "pct_sat_lead": round(float(sat_lead[m].mean()) * 100, 2),
            "pct_risk_on": round(float(risk_on[m].mean()) * 100, 2),
            "mean_dd63": round(float(dd63[m].mean()), 4),
            "mean_trail_abs": round(float(trail[m].abs().mean()), 4),
            "mean_prem_p3": round(float(prem_p3[m].mean()) * 10000, 4),  # bp
            "sum_prem_p3_pp": round(float(prem_p3[m].sum()) * 100, 4),
        }

    year_rows = []
    for r in yg["years"]:
        y = r["year"]
        m = (years == y) & near_on
        year_rows.append(
            {
                **r,
                "near_on_days": int(m.sum()),
                "drag_days": int((m & (prem_p3 < 0)).sum()),
                "help_days": int((m & (prem_p3 > 0)).sum()),
                "sum_prem_p3_pp": round(float(prem_p3[m].sum()) * 100, 4),
                "sum_prem_p4_pp": round(float(prem_p4[m & sat_lead].sum()) * 100, 4),
            }
        )

    census = {
        "live_win_years": sorted(live_win_years),
        "p3_win_years": sorted(p3_win_years),
        "p34_win_years": sorted(p34_win_years),
        "near_year_oracle": {
            k: yg[k]
            for k in (
                "mean_policy",
                "mean_oracle",
                "gap_to_oracle_pp",
                "year_wins",
                "n_years",
                "best_counts",
            )
        },
        "feat_drag_in_live_win_years": _feat(drag & live_year),
        "feat_help_in_live_win_years": _feat(help_ & live_year),
        "feat_drag_in_p3_win_years": _feat(drag & p3_year),
        "feat_help_in_p3_win_years": _feat(help_ & p3_year),
        "feat_near_all": _feat(near_on),
        "n_drag_episodes_live_win_years": len(eps_live),
        "n_drag_episodes_p3_win_years": len(eps_p3),
        "top_drag_episodes_live_win": sorted(eps_live, key=lambda e: -e["n_days"])[:12],
        "top_drag_episodes_p3_win": sorted(eps_p3, key=lambda e: -e["n_days"])[:8],
        "year_rows": year_rows,
        "note": (
            "Drag/help uses same-bar prem_p3 for DIAG census only; "
            "mute gates below are lag-1 causal."
        ),
    }
    return census


def _trail_sum(x: pd.Series, w: int) -> pd.Series:
    return x.shift(1).rolling(int(w), min_periods=max(3, int(w) // 3)).sum()


def _three_state(
    want_p3: np.ndarray,
    want_p4: np.ndarray,
    mute_p3: np.ndarray,
    mute_p4: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Causal 3-state: LIVE=0 / P3=1 / P3+P4=2 → (i3, i4) float masks."""
    n = len(want_p3)
    i3 = np.zeros(n, dtype=float)
    i4 = np.zeros(n, dtype=float)
    state = 0
    for i in range(n):
        if mute_p3[i] or not want_p3[i]:
            state = 0
        else:
            # desire at least P3
            if state == 0:
                state = 1
            if state >= 1 and want_p4[i] and not mute_p4[i]:
                state = 2
            elif state == 2 and (not want_p4[i] or mute_p4[i]):
                state = 1
        i3[i] = 1.0 if state >= 1 else 0.0
        i4[i] = 1.0 if state >= 2 else 0.0
    return i3, i4


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()

    nav_l3 = _load_nav(LIVESTACK / "nav_BASE_LIVE_FUSE_COOL.csv")
    nav_p3 = _load_nav(LIVESTACK / "nav_LIVE_P3_WITHIN.csv")
    soft_l1 = _load_nav(ALIGN / "nav_L1_SOFT_T1.csv")
    p34_path = (
        ROOT
        / "repro"
        / "tipsoft-path4-held-pos-gate-stagea"
        / "outputs"
        / "nav_P4_C001_NEAR_AND_SAT.csv"
    )
    if not p34_path.exists():
        p34_path = (
            ROOT
            / "repro"
            / "tipsoft-path4-held-pos-gate-stagea"
            / "outputs"
            / "nav_P4_C001_NEAR&SAT.csv"
        )
    nav0 = float(nav_l3["nav"].iloc[0])
    p4_book = _load_nav(LIVESTACK / "nav_LIVE_P3_P4_CASH_001.csv")

    r3 = _returns(nav_l3)
    rp3 = _returns(nav_p3)
    r_p4 = _returns(p4_book)
    panel = pd.concat({"r3": r3, "rp3": rp3, "rp4": r_p4}, axis=1, join="inner").dropna(
        how="any"
    )
    prem_p3 = panel["rp3"] - panel["r3"]
    prem_p4 = panel["rp4"] - panel["rp3"]
    live_r = panel["r3"]

    proxy = _proxy_mdd63(soft_l1).reindex(panel.index).fillna(0.0)
    dd63 = _dd_from_peak(soft_l1, 63).reindex(panel.index).fillna(0.0)
    cool_exp = build_cool_c8_exposure(panel.index, proxy)
    risk_on = cool_exp >= 0.999
    defending = ~risk_on

    sig = pd.read_csv(P3_SIG, parse_dates=["date"])
    sig["date"] = pd.to_datetime(sig["date"]).dt.normalize()
    sig = sig.set_index("date").reindex(panel.index)
    trail = sig["trail_rel_63"].astype(float)
    sat_lead = sig["sat_lead"].fillna(False).astype(bool)
    p3_theta = (trail.abs() >= float(P3_THETA)).fillna(False)
    nearpeak3 = p3_theta & (dd63 >= -0.03)

    near_r = live_r + nearpeak3.astype(float) * prem_p3
    p34_r = (
        live_r
        + nearpeak3.astype(float) * prem_p3
        + (nearpeak3 & sat_lead).astype(float) * prem_p4
    )

    census = _build_census(
        panel.index,
        nearpeak3,
        prem_p3,
        prem_p4,
        sat_lead,
        risk_on,
        dd63,
        trail,
        live_r,
        near_r,
        p34_r,
    )
    (OUT / "live_win_episode_census.json").write_text(
        json.dumps(census, indent=2) + "\n", encoding="utf-8"
    )
    pd.DataFrame(census["year_rows"]).to_csv(OUT / "year_census.csv", index=False)
    pd.DataFrame(census["top_drag_episodes_live_win"]).to_csv(
        OUT / "drag_episodes_live_win.csv", index=False
    )

    base_w = _pack(nav_l3)
    near_nav_r = _nav_from_returns(near_r, nav0)
    p34_nav_r = _nav_from_returns(p34_r, nav0)
    near_w = _pack(near_nav_r)
    near_nav_r.to_csv(OUT / f"nav_{NEAR_ID}.csv", index=False)
    p34_nav_r.to_csv(OUT / f"nav_{P34_ID}.csv", index=False)
    nav_l3.to_csv(OUT / f"nav_{BASE_ID}.csv", index=False)

    near_yg = _year_oracle_table(near_r, live_r, near_r, p34_r)
    live_yg = _year_oracle_table(live_r, live_r, near_r, p34_r)
    p34_yg = _year_oracle_table(p34_r, live_r, near_r, p34_r)

    # Trailing prem features (causal lag-1)
    trail_feats: dict[str, pd.Series] = {}
    for w in (5, 10, 21, 42, 50, 63):
        trail_feats[f"P3_W{w}"] = _trail_sum(prem_p3, w)
        # stack-on-only trail: prem when NEAR would be on, else 0 (still lag-1 via _trail_sum)
        stack_p3 = prem_p3.where(nearpeak3.shift(1).fillna(False), 0.0)
        trail_feats[f"P3ON_W{w}"] = _trail_sum(stack_p3, w)
        trail_feats[f"P4_W{w}"] = _trail_sum(prem_p4, w)

    want_p3 = nearpeak3.to_numpy(dtype=bool)
    want_p4 = (nearpeak3 & sat_lead).to_numpy(dtype=bool)
    # alternate want: NEAR∧risk_on for mutex-flavored enter
    want_p3_risk = (nearpeak3 & risk_on).to_numpy(dtype=bool)
    want_p4_risk = (nearpeak3 & risk_on & sat_lead).to_numpy(dtype=bool)

    arms: dict[str, tuple[str, pd.Series, pd.Series]] = {}
    # Refs
    arms["REF_NEAR_P4OFF"] = (
        "REF",
        nearpeak3.astype(float),
        pd.Series(0.0, index=panel.index),
    )
    arms["REF_NEAR_P4SAT"] = (
        "REF",
        nearpeak3.astype(float),
        (nearpeak3 & sat_lead).astype(float),
    )

    def _tlabel(x: float) -> str:
        return str(float(x)).replace("-", "m").replace(".", "")

    # Trailing mute grids (dense on W42/W63 — prior screen sweet spot)
    windows = (5, 10, 21, 42, 50, 63)
    thresh_p3 = (0.0, -0.0005, -0.001, -0.002, -0.005, -0.01)
    thresh_p4 = (0.0, -0.001, -0.005)

    for w in windows:
        # keep outer windows lighter
        thr_list = thresh_p3 if w in (42, 50, 63) else (0.0, -0.002, -0.01)
        for thr in thr_list:
            for feat_key, prefix in (
                (f"P3_W{w}", f"MUTE_P3_W{w}"),
                (f"P3ON_W{w}", f"MUTE_P3ON_W{w}"),
            ):
                if feat_key not in trail_feats:
                    # W50 uses W42/W63 feats only for P3ON alias via rolling
                    trail_feats[f"P3_W{w}"] = _trail_sum(prem_p3, w)
                    stack_p3 = prem_p3.where(nearpeak3.shift(1).fillna(False), 0.0)
                    trail_feats[f"P3ON_W{w}"] = _trail_sum(stack_p3, w)
                    trail_feats[f"P4_W{w}"] = _trail_sum(prem_p4, w)
                tr = trail_feats[feat_key].fillna(0.0)
                mute = (tr < float(thr)).to_numpy(dtype=bool)
                i3 = (nearpeak3.to_numpy(dtype=bool) & (~mute)).astype(float)
                arms[f"{prefix}_T{_tlabel(thr)}__BIN"] = (
                    "MUTE_BIN",
                    pd.Series(i3, index=panel.index),
                    pd.Series(0.0, index=panel.index),
                )
                # soft mute: trail-neg → α=0.5 instead of hard off
                soft = nearpeak3.astype(float).to_numpy()
                soft = soft.copy()
                soft[mute] = soft[mute] * 0.5
                arms[f"{prefix}_T{_tlabel(thr)}__SOFT05"] = (
                    "MUTE_SOFT",
                    pd.Series(soft, index=panel.index),
                    pd.Series(0.0, index=panel.index),
                )
                # census-shaped: mute only when trail-neg AND sat_lead (drag richer in sat)
                mute_sat = mute & sat_lead.to_numpy(dtype=bool)
                a3s, a4s = _three_state(want_p3, want_p4, mute_sat, mute_sat)
                arms[f"{prefix}_T{_tlabel(thr)}__S3_MUTESAT"] = (
                    "MUTE_S3_SAT",
                    pd.Series(a3s, index=panel.index),
                    pd.Series(a4s, index=panel.index),
                )
                for t4 in thresh_p4:
                    tr4 = trail_feats[f"P4_W{w}"].fillna(0.0)
                    mute4 = (tr4 < float(t4)).to_numpy(dtype=bool)
                    a3, a4 = _three_state(want_p3, want_p4, mute, mute4)
                    arms[f"{prefix}_T{_tlabel(thr)}__S3_P4T{_tlabel(t4)}"] = (
                        "MUTE_S3",
                        pd.Series(a3, index=panel.index),
                        pd.Series(a4, index=panel.index),
                    )
                if w in (42, 50, 63) and thr in (0.0, -0.001, -0.01):
                    mute_def = mute | defending.to_numpy(dtype=bool)
                    a3, a4 = _three_state(
                        want_p3, want_p4, mute_def, mute | defending.to_numpy(dtype=bool)
                    )
                    arms[f"{prefix}_T{_tlabel(thr)}__S3_MUTEXDEF"] = (
                        "MUTE_S3_MUTEX",
                        pd.Series(a3, index=panel.index),
                        pd.Series(a4, index=panel.index),
                    )

    # Risk-on enter + trail mute (smaller grid)
    for w in (21, 42, 63):
        for thr in (0.0, -0.001, -0.01):
            tr = trail_feats[f"P3_W{w}"].fillna(0.0)
            mute = (tr < float(thr)).to_numpy(dtype=bool)
            a3, a4 = _three_state(want_p3_risk, want_p4_risk, mute, mute)
            arms[f"MUTE_RISKON_W{w}_T{_tlabel(thr)}__S3"] = (
                "MUTE_RISKON",
                pd.Series(a3, index=panel.index),
                pd.Series(a4, index=panel.index),
            )

    # Confirm-style: mute requires trail negative for K consecutive days
    for w in (21, 42, 63):
        tr = trail_feats[f"P3_W{w}"].fillna(0.0)
        neg = tr < 0.0
        for k in (2, 3, 5):
            conf = neg.copy()
            for j in range(1, k):
                conf = conf & neg.shift(j).fillna(False)
            mute = conf.to_numpy(dtype=bool)
            a3, a4 = _three_state(want_p3, want_p4, mute, mute)
            arms[f"MUTE_CONF_W{w}_K{k}__S3"] = (
                "MUTE_CONF",
                pd.Series(a3, index=panel.index),
                pd.Series(a4, index=panel.index),
            )

    # Oracle DIAG: mute when next-bar / same-bar prem negative — never promote
    arms["ORACLE_MUTE_NEG_DIAG"] = (
        "ORACLE",
        (nearpeak3 & (prem_p3 > 0)).astype(float),
        (nearpeak3 & sat_lead & (prem_p4 > 0)).astype(float),
    )

    # Attach P4SAT on BIN / SOFT05 arms that were P4OFF-only
    extra_bin = {}
    for name, (fam, i3, i4) in list(arms.items()):
        if fam == "MUTE_BIN" and name.endswith("__BIN"):
            i4s = ((i3 > 0.5) & sat_lead).astype(float)
            extra_bin[name.replace("__BIN", "__BIN_P4SAT")] = ("MUTE_BIN", i3, i4s)
        if fam == "MUTE_SOFT" and name.endswith("__SOFT05"):
            i4s = ((i3 > 1e-12) & sat_lead).astype(float) * i3.clip(0, 1)
            extra_bin[name.replace("__SOFT05", "__SOFT05_P4SAT")] = ("MUTE_SOFT", i3, i4s)
    arms.update(extra_bin)

    rows: list[dict[str, Any]] = []
    arms_nav: dict[str, pd.DataFrame] = {
        BASE_ID: nav_l3,
        NEAR_ID: near_nav_r,
        P34_ID: p34_nav_r,
    }

    for name, (fam, i3, i4) in arms.items():
        i3 = i3.reindex(panel.index).fillna(0.0).astype(float).clip(0, 1)
        i4 = i4.reindex(panel.index).fillna(0.0).astype(float).clip(0, 1)
        i4 = i4 * (i3 > 1e-12).astype(float)
        r = live_r + i3 * prem_p3 + i4 * prem_p4
        nav = _nav_from_returns(r, nav0)
        arms_nav[name] = nav
        chal_w = _pack(nav)
        d_live = _delta(base_w, chal_w)
        d_near = _delta(near_w, chal_w)
        tip_live = _tip(nav_l3, nav)
        yg = _year_oracle_table(r, live_r, near_r, p34_r)
        held_vs_near = d_near["heldout_2019_plus"]["cagr_lift_pp"]
        sealed_vs_live = d_live["sealed_2023_plus"]["mdd_improve_pp"]
        tip_vs_live = (tip_live.get("ytd") or {}).get("cagr_lift_pp")
        gap = yg["gap_to_oracle_pp"]
        near_gap = near_yg["gap_to_oracle_pp"]
        regret_improve = (
            None
            if gap is None or near_gap is None
            else round(float(near_gap) - float(gap), 4)
        )
        wins = int(yg["year_wins"])
        wins_vs_near = wins - int(near_yg["year_wins"])
        held_ok_eps = (
            held_vs_near is not None and float(held_vs_near) >= HELD_EPS_VS_NEAR
        )
        sealed_ok = sealed_vs_live is not None and float(sealed_vs_live) >= SEALED_MDD_FLOOR_PP
        tip_ok = tip_vs_live is None or float(tip_vs_live) >= TIP_Y_FLOOR_PP
        live_held_ok = (
            d_live["heldout_2019_plus"]["cagr_lift_pp"] is not None
            and float(d_live["heldout_2019_plus"]["cagr_lift_pp"]) >= HELD_CAGR_FLOOR_PP
        )
        held_pos = (
            held_vs_near is not None
            and float(held_vs_near) > 0
            and sealed_ok
            and tip_ok
        )
        year_signal = regret_improve is not None and (
            float(regret_improve) >= YEAR_REGRET_IMPROVE_FLOOR
            or wins_vs_near >= YEAR_WINS_IMPROVE_FLOOR
        )
        year_obj = (
            held_ok_eps
            and sealed_ok
            and tip_ok
            and live_held_ok
            and year_signal
        )
        year_soft = (
            held_vs_near is not None
            and float(held_vs_near) >= HELD_SOFT_EPS_VS_NEAR
            and sealed_ok
            and tip_ok
            and live_held_ok
            and year_signal
            and not year_obj
        )
        # Strong: held+ AND (regret or wins)
        strong = held_pos and year_obj
        rows.append(
            {
                "arm": name,
                "family": fam,
                "pct_p3_on": round(float((i3 > 1e-12).mean()) * 100, 2),
                "pct_p4_on": round(float((i4 > 1e-12).mean()) * 100, 2),
                "verdict_vs_live": _arm_verdict_vs_live(d_live, tip_live),
                "held_vs_live": d_live["heldout_2019_plus"]["cagr_lift_pp"],
                "full_vs_live": d_live["full"]["cagr_lift_pp"],
                "sealed_vs_live": sealed_vs_live,
                "tipY_vs_live": tip_vs_live,
                "held_vs_near": held_vs_near,
                "year_gap_to_oracle_pp": gap,
                "year_regret_improve_vs_near_pp": regret_improve,
                "year_wins": wins,
                "year_wins_vs_near": wins_vs_near,
                "year_mean_policy": yg["mean_policy"],
                "held_pos_vs_near": bool(held_pos),
                "year_obj_clear": bool(year_obj),
                "year_soft_clear": bool(year_soft),
                "strong_clear": bool(strong),
                "oracle": fam == "ORACLE",
                "is_ref": fam == "REF",
            }
        )

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "arms_trail_prem_mute.csv", index=False)

    causal = df[~df["oracle"]].copy()
    mech = causal[~causal["is_ref"]].copy()
    hits = mech[
        mech["held_pos_vs_near"]
        | mech["year_obj_clear"]
        | mech["year_soft_clear"]
        | mech["strong_clear"]
    ]
    hits.to_csv(OUT / "trail_mute_hits.csv", index=False)

    by_fam = (
        mech.groupby("family")
        .agg(
            n=("arm", "count"),
            n_held_pos=("held_pos_vs_near", "sum"),
            n_year_obj=("year_obj_clear", "sum"),
            n_year_soft=("year_soft_clear", "sum"),
            n_strong=("strong_clear", "sum"),
            max_held_vs_near=("held_vs_near", "max"),
            max_regret_improve=("year_regret_improve_vs_near_pp", "max"),
            max_wins_vs_near=("year_wins_vs_near", "max"),
        )
        .reset_index()
    )
    by_fam.to_csv(OUT / "family_summary.csv", index=False)

    ranked = mech.sort_values(
        by=[
            "strong_clear",
            "held_pos_vs_near",
            "year_obj_clear",
            "year_soft_clear",
            "year_wins_vs_near",
            "year_regret_improve_vs_near_pp",
            "held_vs_near",
            "sealed_vs_live",
            "tipY_vs_live",
        ],
        ascending=[False, False, False, False, False, False, False, False, False],
    )
    top = ranked.head(20)
    top.to_csv(OUT / "top_arms.csv", index=False)

    strong_hits = mech[mech["strong_clear"]]
    held_hits = mech[mech["held_pos_vs_near"]]
    year_hits = mech[mech["year_obj_clear"]]
    soft_hits = mech[mech["year_soft_clear"]]

    champion_row = None
    if len(strong_hits):
        champion_row = strong_hits.sort_values(
            by=["year_wins_vs_near", "year_regret_improve_vs_near_pp", "held_vs_near"],
            ascending=[False, False, False],
        ).iloc[0]
        verdict = "IP3_TRAIL_MUTE_HIT"
    elif len(held_hits):
        champion_row = held_hits.sort_values(
            by=["year_wins_vs_near", "year_regret_improve_vs_near_pp", "held_vs_near"],
            ascending=[False, False, False],
        ).iloc[0]
        verdict = "IP3_TRAIL_MUTE_HIT"
    elif len(year_hits):
        champion_row = year_hits.sort_values(
            by=["year_wins_vs_near", "year_regret_improve_vs_near_pp", "held_vs_near"],
            ascending=[False, False, False],
        ).iloc[0]
        verdict = "IP3_TRAIL_YEAR_SOFT"
    elif len(soft_hits):
        champion_row = soft_hits.sort_values(
            by=["year_wins_vs_near", "year_regret_improve_vs_near_pp", "held_vs_near"],
            ascending=[False, False, False],
        ).iloc[0]
        verdict = "IP3_TRAIL_YEAR_SOFT"
    else:
        verdict = "IP3_TRAIL_MUTE_NO_EDGE"
        if len(mech):
            champion_row = ranked.iloc[0]

    n_held = int(mech["held_pos_vs_near"].sum())
    n_year = int(mech["year_obj_clear"].sum())
    n_year_soft = int(mech["year_soft_clear"].sum())
    n_strong = int(mech["strong_clear"].sum())
    champ = None if champion_row is None else champion_row.to_dict()
    if champ:
        arms_nav[champ["arm"]].to_csv(OUT / f"nav_{champ['arm']}.csv", index=False)
        yg_c = _year_oracle_table(
            _returns(arms_nav[champ["arm"]]), live_r, near_r, p34_r
        )
        pd.DataFrame(yg_c["years"]).to_csv(OUT / "year_oracle_champion.csv", index=False)

    pd.DataFrame(near_yg["years"]).to_csv(OUT / "year_oracle_near.csv", index=False)
    oracle_rows = df[df["oracle"]]

    fam_note = "; ".join(
        f"{r.family}:strong={int(r.n_strong)}/year={int(r.n_year_obj)}/soft={int(r.n_year_soft)}/held+={int(r.n_held_pos)}/maxΔ={r.max_held_vs_near}/winsΔ={int(r.max_wins_vs_near)}"
        for r in by_fam.itertuples()
    )

    optimize = [
        "Objective: trailing prem mute + 3-state LIVE/P3/P3+P4 to raise year-wins / cut year-regret vs oracle; held ≥ NEAR−0.05; sealed/tip floors; no year-cut",
        (
            f"Champion `{champ['arm']}` fam={champ['family']} held_vs_near={champ['held_vs_near']} "
            f"regret↑={champ['year_regret_improve_vs_near_pp']} winsΔ={champ['year_wins_vs_near']} "
            f"wins={champ['year_wins']} sealed={champ['sealed_vs_live']} tipY={champ['tipY_vs_live']} "
            f"live={champ['verdict_vs_live']}"
            if champ
            else "No champion"
        ),
        f"Clears: strong={n_strong} · held_pos={n_held} · year_obj={n_year} · year_soft={n_year_soft} / mech={len(mech)}",
        f"By family: {fam_note}",
        (
            f"NEAR gap={near_yg['gap_to_oracle_pp']} wins={near_yg['year_wins']}/{near_yg['n_years']} · "
            f"live gap={live_yg['gap_to_oracle_pp']} wins={live_yg['year_wins']} · "
            f"P34 gap={p34_yg['gap_to_oracle_pp']} wins={p34_yg['year_wins']} · "
            f"best_counts={near_yg['best_counts']}"
        ),
        (
            f"Census live-win years={census['live_win_years']} · "
            f"drag_eps={census['n_drag_episodes_live_win_years']} · "
            f"drag_feat={census['feat_drag_in_live_win_years']}"
        ),
        (
            f"Oracle DIAG held_vs_near="
            f"{None if oracle_rows.empty else oracle_rows['held_vs_near'].max()} "
            f"(lookahead — never promote)"
        ),
        "If IP3_TRAIL_MUTE_HIT → draft observe; IP3_TRAIL_YEAR_SOFT → note only; "
        "IP3_TRAIL_MUTE_NO_EDGE → KEEP 0kaw NEARPEAK3 · Path4 DRAFT 0kay",
        "Soft KEEP · Path4 live OFF · hybrid T+0 FORBIDDEN · no year-cut · no wire",
    ]

    screen = {
        "id": SCREEN_ID,
        "register": REGISTER,
        "parents": list(PARENTS),
        "generated_at_utc": generated,
        "mech": MECH,
        "verdict": verdict,
        "n_mech_screened": len(mech),
        "n_held_pos_vs_near": n_held,
        "n_year_obj_clear": n_year,
        "n_year_soft_clear": n_year_soft,
        "n_strong_clear": n_strong,
        "family_summary": by_fam.to_dict(orient="records"),
        "champion": champ,
        "census_summary": {
            "live_win_years": census["live_win_years"],
            "p3_win_years": census["p3_win_years"],
            "p34_win_years": census["p34_win_years"],
            "n_drag_episodes_live_win_years": census["n_drag_episodes_live_win_years"],
            "feat_drag_in_live_win_years": census["feat_drag_in_live_win_years"],
            "feat_help_in_p3_win_years": census["feat_help_in_p3_win_years"],
            "near_year_oracle": census["near_year_oracle"],
        },
        "near_year_oracle": {
            k: near_yg[k]
            for k in (
                "mean_policy",
                "mean_oracle",
                "gap_to_oracle_pp",
                "year_wins",
                "n_years",
                "best_counts",
            )
        },
        "oracle_diag": None
        if oracle_rows.empty
        else oracle_rows.sort_values("held_vs_near", ascending=False).iloc[0].to_dict(),
        "top_arms": top.to_dict(orient="records"),
        "optimize_live": optimize,
        "soft_keep": True,
        "path4_live": False,
        "hybrid_t0_carve": False,
        "broker": False,
        "label": f"{SCREEN_ID}_{generated[:10]}__{verdict}",
    }
    (OUT / "screen.json").write_text(json.dumps(screen, indent=2) + "\n", encoding="utf-8")

    # --- packs ---
    charter_md = "\n".join(
        [
            f"# {CHARTER_ID}",
            "",
            f"Date: {generated[:10]}",
            f"Register: **{REGISTER}** · Parents: {', '.join(PARENTS)}",
            "",
            "## Question",
            "",
            "Can a **live-win episode census** plus **causal trailing prem mute** "
            "(3-state LIVE / P3 / P3+P4, year-regret / year-wins objective) raise "
            "yearly win-rate and cut regret vs oracle while held ≥ NEAR−ε and "
            "drawdown floors hold — without year dummies?",
            "",
            "## Design",
            "",
            "- Base: `BASE_LIVE_FUSE_COOL` Exact T+1 · Ref NEARPEAK3 / Path4 NEAR∧sat",
            "- DIAG census: live-win years drag episodes (NEAR on ∧ prem_p3<0) — not a gate",
            "- Mute: lag-1 rolling sum(prem_p3)/prem_on / confirm-K · optional COOL mutex",
            "- 3-state: enter P3 on NEAR∧¬mute; P4 on sat∧¬mute4; else LIVE",
            "- Success: `strong` = held+ vs NEAR + year obj; or `year_obj` with held≥NEAR−0.05",
            "- Forbidden: year-cut · lookahead promote · hybrid T+0 · Path4 live · re-grid 0kb0 latch",
            "",
            f"Label: `{CHARTER_ID}_{generated[:10]}`",
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
                "date": generated[:10],
                "forbidden": [
                    "year_cut",
                    "lookahead_promote",
                    "hybrid_t0",
                    "path4_live",
                    "repeat_0kb0_asymm_grid",
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
        f"Date: {generated[:10]} · Verdict: **`{verdict}`** · champion=**`{(champ or {}).get('arm')}`**",
        f"Register: **{REGISTER}** · mech={len(mech)} · strong={n_strong} · held_pos={n_held} · year_obj={n_year} · year_soft={n_year_soft}",
        "",
        "## Live-win episode census (DIAG)",
        "",
        f"- live-win years: `{census['live_win_years']}`",
        f"- P3-win years: `{census['p3_win_years']}` · P3+P4: `{census['p34_win_years']}`",
        f"- drag episodes in live-win years: **{census['n_drag_episodes_live_win_years']}**",
        f"- drag feat (live-win): `{census['feat_drag_in_live_win_years']}`",
        f"- help feat (P3-win): `{census['feat_help_in_p3_win_years']}`",
        "",
        "## Year-oracle baseline",
        "",
        f"- NEAR gap **{near_yg['gap_to_oracle_pp']}** · wins **{near_yg['year_wins']}/{near_yg['n_years']}** · `{near_yg['best_counts']}`",
        f"- live gap **{live_yg['gap_to_oracle_pp']}** wins **{live_yg['year_wins']}** · "
        f"P34 gap **{p34_yg['gap_to_oracle_pp']}** wins **{p34_yg['year_wins']}**",
        "",
        "## Family summary",
        "",
        "| Family | n | strong | year_obj | year_soft | held+ | max heldΔ | max regret↑ | max winsΔ |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in by_fam.to_dict(orient="records"):
        screen_md.append(
            f"| {r['family']} | {r['n']} | {int(r['n_strong'])} | {int(r['n_year_obj'])} | "
            f"{int(r['n_year_soft'])} | {int(r['n_held_pos'])} | {r['max_held_vs_near']} | "
            f"{r['max_regret_improve']} | {int(r['max_wins_vs_near'])} |"
        )
    screen_md += [
        "",
        "## Top arms",
        "",
        "| Arm | fam | heldΔNEAR | regret↑ | winsΔ | wins | sealed | tipY | vs live | p3% | p4% |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|---:|---:|",
    ]
    for r in top.to_dict(orient="records"):
        screen_md.append(
            f"| {r['arm']} | {r['family']} | {r['held_vs_near']} | {r['year_regret_improve_vs_near_pp']} | "
            f"{r['year_wins_vs_near']} | {r['year_wins']} | {r['sealed_vs_live']} | {r['tipY_vs_live']} | "
            f"{r['verdict_vs_live']} | {r['pct_p3_on']} | {r['pct_p4_on']} |"
        )
    if not oracle_rows.empty:
        o = oracle_rows.sort_values("held_vs_near", ascending=False).iloc[0]
        screen_md += [
            "",
            "## Oracle DIAG",
            "",
            f"| {o['arm']} | heldΔNEAR {o['held_vs_near']} | regret↑ {o['year_regret_improve_vs_near_pp']} | "
            f"winsΔ {o['year_wins_vs_near']} |",
        ]
    screen_md += [
        "",
        "## Optimize / disposition",
        "",
        *[f"{i}. {line}" for i, line in enumerate(optimize, 1)],
        "",
        "Repro: `PYTHONPATH=scripts python3 scripts/tipsoft_ip3_trail_prem_mute_stagea.py`",
        "",
        f"Label: `{screen['label']}`",
        "",
    ]
    write_ops_and_repro_pointer(
        OPS / f"{SCREEN_ID}.md",
        REP / f"{SCREEN_ID}.md",
        "\n".join(screen_md),
        kind="screen",
    )
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(screen, indent=2) + "\n", encoding="utf-8")
    write_repro_pointer(OPS / f"{SCREEN_ID}.json", REP / f"{SCREEN_ID}.json", kind="screen")

    decision_md = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: {generated[:10]} · Verdict: **`{verdict}`** · champion=**`{(champ or {}).get('arm')}`**",
            f"Register: **{REGISTER}** · Parents: {', '.join(PARENTS)}",
            "",
            "## Result",
            "",
            (
                f"- family: **{(champ or {}).get('family')}**\n"
                f"- held vs NEARPEAK3: **{(champ or {}).get('held_vs_near')}** pp\n"
                f"- year regret improve: **{(champ or {}).get('year_regret_improve_vs_near_pp')}** pp\n"
                f"- year wins: **{(champ or {}).get('year_wins')}** (Δ vs NEAR **{(champ or {}).get('year_wins_vs_near')}**)\n"
                f"- sealed vs live: **{(champ or {}).get('sealed_vs_live')}** · tipY **{(champ or {}).get('tipY_vs_live')}**\n"
                f"- clears: strong **{n_strong}** · held_pos **{n_held}** · year_obj **{n_year}** · year_soft **{n_year_soft}** / {len(mech)}"
                if champ
                else f"- No clear · mech={len(mech)}"
            ),
            "",
            "## Disposition",
            "",
            "- Promote observe only on `IP3_TRAIL_MUTE_HIT`",
            "- `IP3_TRAIL_YEAR_SOFT` → research note · KEEP 0kaw NEARPEAK3",
            "- `IP3_TRAIL_MUTE_NO_EDGE` → KEEP NEARPEAK3 · Path4 DRAFT (0kay)",
            "- Soft KEEP · Path4 live OFF · hybrid T+0 FORBIDDEN · no year-cut",
            "",
            "## Next",
            "",
            *[f"{i}. {line}" for i, line in enumerate(optimize, 1)],
            "",
            f"Label: `{DECISION_ID}_{generated[:10]}__{verdict}__NO_LIVE`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{DECISION_ID}.md",
        REP / f"{DECISION_ID}.md",
        decision_md,
        kind="decision pack",
    )
    (OPS / f"{DECISION_ID}.json").write_text(
        json.dumps(
            {
                "id": DECISION_ID,
                "register": REGISTER,
                "parents": list(PARENTS),
                "verdict": verdict,
                "champion": champ,
                "n_strong_clear": n_strong,
                "n_held_pos_vs_near": n_held,
                "n_year_obj_clear": n_year,
                "n_year_soft_clear": n_year_soft,
                "census_summary": screen["census_summary"],
                "soft_keep": True,
                "path4_live": False,
                "hybrid_t0_carve": False,
                "label": f"{DECISION_ID}_{generated[:10]}__{verdict}__NO_LIVE`",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    write_repro_pointer(
        OPS / f"{DECISION_ID}.json", REP / f"{DECISION_ID}.json", kind="decision pack"
    )

    print(
        json.dumps(
            {
                "verdict": verdict,
                "champion": None if not champ else champ["arm"],
                "family": None if not champ else champ["family"],
                "held_vs_near": None if not champ else champ["held_vs_near"],
                "year_regret_improve_vs_near_pp": None
                if not champ
                else champ["year_regret_improve_vs_near_pp"],
                "year_wins": None if not champ else champ["year_wins"],
                "year_wins_vs_near": None if not champ else champ["year_wins_vs_near"],
                "n_strong": n_strong,
                "n_held_pos": n_held,
                "n_year_obj": n_year,
                "n_year_soft": n_year_soft,
                "n_mech": len(mech),
                "live_win_years": census["live_win_years"],
                "near_wins": near_yg["year_wins"],
                "near_gap": near_yg["gap_to_oracle_pp"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
