#!/usr/bin/env python3
"""Live↔stack trail-race Stage A (0kb2).

Parent 0kb1 HIT ``MUTE_P3_W63_Tm001__S3_MUTESAT`` wins P3/P3+P4 years but still
loses live-win years (2013–16, 2019–20, 2025). Goal: causal daily switch so
**both** live-edge years and stack-edge years are captured — no year dummies.

Mechanisms:
1. TRAIL_RACE — lag-1 rolling cumret argmax among {LIVE, P3, P3+P4}
2. LIVE_OVERRIDE — keep 0kb1 3-state+sat-mute; force LIVE when live trail-beats stack
3. RACE_vs_CHAMP — race between LIVE and frozen 0kb1 champ returns
4. SOFT_BLEND — shrink stack α toward 0 when live trail-leads

Exact T+1 · Soft KEEP · Path4 live OFF · hybrid T+0 FORBIDDEN · no year-cut.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from cool_c8_proxy_observe_helpers import build_cool_c8_exposure
from fin_sell_quality_helpers import cagr_lift_pp
from ops_repro_ssot import write_ops_and_repro_pointer, write_repro_pointer
from stagea_screen_helpers import (
    utc_now_z as _utc,
    load_nav_csv as _load_nav,
    returns_from_nav as _returns,
    nav_from_returns as _nav_from_returns,
    pack_nav_windows as _pack,
    tip_lift as _tip,
    window_delta as _delta,
)

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "tipsoft-ip3-live-stack-race-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

LIVESTACK = ROOT / "repro" / "fin-sat-path3-path4-livestack-twin-stageb" / "outputs"
ALIGN = ROOT / "repro" / "research-live-align-gap-stagea" / "outputs"
P3_SIG = (
    ROOT / "repro" / "fin-sat-path3-t0-dual-paper-observe" / "outputs" / "p3_t0_state_signal.csv"
)
PARENT_NAV = (
    ROOT
    / "repro"
    / "tipsoft-ip3-trail-prem-mute-stagea"
    / "outputs"
    / "nav_MUTE_P3_W63_Tm001__S3_MUTESAT.csv"
)

CHARTER_ID = "TIPSOFT_IP3_LIVE_STACK_RACE_STAGEA_CHARTER"
SCREEN_ID = "TIPSOFT_IP3_LIVE_STACK_RACE_STAGEA_SCREEN"
DECISION_ID = "TIPSOFT_IP3_LIVE_STACK_RACE_STAGEA_DECISION_PACK"
REGISTER = "0kb2"
PARENTS = ("0kb1", "0kb0", "0kaw")
MECH = "TIPSOFT_IP3_LIVE_STACK_RACE"

BASE_ID = "BASE_LIVE_FUSE_COOL"
CHAMP_ID = "REF_MUTE_S3_SAT_W63"
NEAR_ID = "REF_P3_THETA_NEARPEAK3"
SEALED_MDD_FLOOR_PP = -0.25
TIP_Y_FLOOR_PP = -1.0
HELD_CAGR_FLOOR_PP = 0.10
P3_THETA = 0.005
HELD_EPS_VS_CHAMP = -0.05
YEAR_REGRET_IMPROVE_FLOOR = 0.05
YEAR_WINS_IMPROVE_FLOOR = 1

def _dd_from_peak(nav: pd.DataFrame, win: int = 63) -> pd.Series:
    s = nav.set_index("date")["nav"].astype(float).sort_index()
    peak = s.rolling(win, min_periods=5).max()
    return (s / peak - 1.0).fillna(0.0)

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
    yp, yl, yn, y4 = _year_rets(policy_r), _year_rets(live_r), _year_rets(near_r), _year_rets(p34_r)
    years = sorted(set(yp.index) & set(yl.index) & set(yn.index) & set(y4.index))
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
                "delta_vs_live": round(pol_v - live_v, 4),
                "base_best": base_best,
                "policy_wins": bool(pol_v >= oracle - 1e-6),
                "beats_live": bool(pol_v > live_v + 1e-9),
            }
        )
    mean_pol = float(sum(r["policy"] for r in rows) / len(rows)) if rows else None
    mean_ora = float(sum(r["oracle"] for r in rows) / len(rows)) if rows else None
    mean_live = float(sum(r["live"] for r in rows) / len(rows)) if rows else None
    return {
        "mean_policy": None if mean_pol is None else round(mean_pol, 4),
        "mean_oracle": None if mean_ora is None else round(mean_ora, 4),
        "mean_live": None if mean_live is None else round(mean_live, 4),
        "gap_to_oracle_pp": None
        if mean_pol is None or mean_ora is None
        else round(mean_ora - mean_pol, 4),
        "mean_delta_vs_live_pp": None
        if mean_pol is None or mean_live is None
        else round(mean_pol - mean_live, 4),
        "year_wins": int(year_wins),
        "n_years": len(rows),
        "n_beats_live": int(sum(1 for r in rows if r["beats_live"])),
        "best_counts": best_counts,
        "years": rows,
    }

def _trail_sum(x: pd.Series, w: int) -> pd.Series:
    return x.shift(1).rolling(int(w), min_periods=max(3, int(w) // 3)).sum()

def _three_state_mute_sat(
    nearpeak3: pd.Series,
    sat_lead: pd.Series,
    prem_p3: pd.Series,
    w: int = 63,
    thr: float = -0.01,
) -> tuple[pd.Series, pd.Series]:
    """Frozen 0kb1 champion gate: 3-state + mute when lagW prem_p3 < thr ∧ sat_lead."""
    tr = _trail_sum(prem_p3, w).fillna(0.0)
    mute = ((tr < float(thr)) & sat_lead).to_numpy(dtype=bool)
    want_p3 = nearpeak3.to_numpy(dtype=bool)
    want_p4 = (nearpeak3 & sat_lead).to_numpy(dtype=bool)
    n = len(want_p3)
    i3 = np.zeros(n, dtype=float)
    i4 = np.zeros(n, dtype=float)
    state = 0
    for i in range(n):
        if mute[i] or not want_p3[i]:
            state = 0
        else:
            if state == 0:
                state = 1
            if state >= 1 and want_p4[i] and not mute[i]:
                state = 2
            elif state == 2 and (not want_p4[i] or mute[i]):
                state = 1
        i3[i] = 1.0 if state >= 1 else 0.0
        i4[i] = 1.0 if state >= 2 else 0.0
    idx = nearpeak3.index
    return pd.Series(i3, index=idx), pd.Series(i4, index=idx)

def _race_pick(trails: list[pd.Series], sticky: int = 0) -> np.ndarray:
    """Daily argmax of trails (already lag-1). Optional sticky min-stay on choice."""
    mat = np.column_stack([t.fillna(-1e9).to_numpy(dtype=float) for t in trails])
    raw = np.argmax(mat, axis=1).astype(int)
    if sticky <= 0:
        return raw
    out = raw.copy()
    age = 1
    for i in range(1, len(raw)):
        if out[i - 1] == raw[i]:
            out[i] = raw[i]
            age += 1
        elif age < sticky:
            out[i] = out[i - 1]
            age += 1
        else:
            out[i] = raw[i]
            age = 1
    return out

def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()

    nav_l3 = _load_nav(LIVESTACK / "nav_BASE_LIVE_FUSE_COOL.csv")
    nav_p3 = _load_nav(LIVESTACK / "nav_LIVE_P3_WITHIN.csv")
    soft_l1 = _load_nav(ALIGN / "nav_L1_SOFT_T1.csv")
    p4_book = _load_nav(LIVESTACK / "nav_LIVE_P3_P4_CASH_001.csv")
    parent_nav = _load_nav(PARENT_NAV)
    nav0 = float(nav_l3["nav"].iloc[0])

    r3 = _returns(nav_l3)
    rp3 = _returns(nav_p3)
    r_p4 = _returns(p4_book)
    panel = pd.concat({"r3": r3, "rp3": rp3, "rp4": r_p4}, axis=1, join="inner").dropna(
        how="any"
    )
    prem_p3 = panel["rp3"] - panel["r3"]
    prem_p4 = panel["rp4"] - panel["rp3"]
    live_r = panel["r3"]
    p3_book_r = panel["rp3"]
    p34_book_r = panel["rp4"]

    dd63 = _dd_from_peak(soft_l1, 63).reindex(panel.index).fillna(0.0)
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

    i3_c, i4_c = _three_state_mute_sat(nearpeak3, sat_lead, prem_p3, w=63, thr=-0.01)
    champ_r = live_r + i3_c * prem_p3 + i4_c * prem_p4
    # align parent file returns as sanity ref
    parent_r = _returns(parent_nav).reindex(panel.index).fillna(0.0)

    base_w = _pack(nav_l3)
    champ_nav = _nav_from_returns(champ_r, nav0)
    near_nav = _nav_from_returns(near_r, nav0)
    champ_w = _pack(champ_nav)
    near_w = _pack(near_nav)
    nav_l3.to_csv(OUT / f"nav_{BASE_ID}.csv", index=False)
    champ_nav.to_csv(OUT / f"nav_{CHAMP_ID}.csv", index=False)
    near_nav.to_csv(OUT / f"nav_{NEAR_ID}.csv", index=False)

    champ_yg = _year_oracle_table(champ_r, live_r, near_r, p34_r)
    live_yg = _year_oracle_table(live_r, live_r, near_r, p34_r)
    near_yg = _year_oracle_table(near_r, live_r, near_r, p34_r)
    pd.DataFrame(champ_yg["years"]).to_csv(OUT / "year_oracle_champ_parent.csv", index=False)
    pd.DataFrame(live_yg["years"]).to_csv(OUT / "year_oracle_live.csv", index=False)

    # book return streams for race
    books = {
        "LIVE": live_r,
        "P3": p3_book_r,  # always-on Path3 within book
        "P34": p34_book_r,
        "NEAR": near_r,
        "CHAMP": champ_r,
    }

    arms: dict[str, tuple[str, pd.Series]] = {
        "REF_LIVE": ("REF", live_r),
        "REF_NEAR": ("REF", near_r),
        "REF_CHAMP_S3SAT": ("REF", champ_r),
        "REF_PARENT_NAV": ("REF", parent_r),
    }

    # 1) 3-book trail race LIVE/P3/P34
    for w in (10, 21, 42, 63, 126):
        tl, t3, t4 = _trail_sum(live_r, w), _trail_sum(p3_book_r, w), _trail_sum(p34_book_r, w)
        for sticky in (0, 3, 5, 8):
            pick = _race_pick([tl, t3, t4], sticky=sticky)
            r = np.where(pick == 0, live_r, np.where(pick == 1, p3_book_r, p34_book_r))
            arms[f"RACE_L3P34_W{w}_ST{sticky}"] = (
                "RACE3",
                pd.Series(r, index=panel.index),
            )

    # 2) race LIVE vs NEAR vs NEAR∧sat P34 recon
    for w in (21, 42, 63, 126):
        tl, tn, t34 = _trail_sum(live_r, w), _trail_sum(near_r, w), _trail_sum(p34_r, w)
        for sticky in (0, 5):
            pick = _race_pick([tl, tn, t34], sticky=sticky)
            r = np.where(pick == 0, live_r, np.where(pick == 1, near_r, p34_r))
            arms[f"RACE_L_NEAR_P34_W{w}_ST{sticky}"] = (
                "RACE_RECON",
                pd.Series(r, index=panel.index),
            )

    # 3) race LIVE vs CHAMP (direct dual-edge)
    for w in (10, 21, 42, 63, 126):
        tl, tc = _trail_sum(live_r, w), _trail_sum(champ_r, w)
        for sticky in (0, 3, 5, 8, 13):
            pick = _race_pick([tl, tc], sticky=sticky)
            r = np.where(pick == 0, live_r, champ_r)
            arms[f"RACE_LIVE_CHAMP_W{w}_ST{sticky}"] = (
                "RACE_DUAL",
                pd.Series(r, index=panel.index),
            )
        # margin: only switch to live if live trail leads by margin
        for margin in (0.0, 0.002, 0.005, 0.01):
            lead = (tl - tc).fillna(0.0)
            use_live = (lead > float(margin)).to_numpy()
            r = np.where(use_live, live_r, champ_r)
            arms[f"OVERRIDE_LIVE_W{w}_M{str(margin).replace('.', '')}"] = (
                "OVERRIDE",
                pd.Series(r, index=panel.index),
            )
            # confirm K days live lead
            for k in (2, 3, 5):
                conf = lead > float(margin)
                for j in range(1, k):
                    conf = conf & (lead.shift(j).fillna(0.0) > float(margin))
                r = np.where(conf.to_numpy(), live_r, champ_r)
                arms[f"OVERRIDE_LIVE_W{w}_M{str(margin).replace('.', '')}_K{k}"] = (
                    "OVERRIDE_CONF",
                    pd.Series(r, index=panel.index),
                )

    # 4) soft blend: alpha = clip(0.5 + scale*(tc-tl), 0, 1) on champ prem vs live
    champ_prem = champ_r - live_r
    for w in (21, 42, 63):
        tl, tc = _trail_sum(live_r, w), _trail_sum(champ_r, w)
        edge = (tc - tl).fillna(0.0)
        for scale in (10.0, 20.0, 50.0):
            alpha = (0.5 + float(scale) * edge).clip(0.0, 1.0)
            r = live_r + alpha * champ_prem
            arms[f"BLEND_W{w}_S{int(scale)}"] = ("BLEND", r)

    # Oracle DIAG: same-bar pick best of live/near/p34 — never promote
    best = np.column_stack(
        [live_r.to_numpy(), near_r.to_numpy(), p34_r.to_numpy()]
    )
    pick_o = np.argmax(best, axis=1)
    r_o = np.where(pick_o == 0, live_r, np.where(pick_o == 1, near_r, p34_r))
    arms["ORACLE_DAYBEST_DIAG"] = ("ORACLE", pd.Series(r_o, index=panel.index))

    rows: list[dict[str, Any]] = []
    arms_nav: dict[str, pd.DataFrame] = {
        BASE_ID: nav_l3,
        CHAMP_ID: champ_nav,
        NEAR_ID: near_nav,
    }

    for name, (fam, r) in arms.items():
        r = r.reindex(panel.index).fillna(0.0)
        nav = _nav_from_returns(r, nav0)
        arms_nav[name] = nav
        chal_w = _pack(nav)
        d_live = _delta(base_w, chal_w)
        d_champ = _delta(champ_w, chal_w)
        d_near = _delta(near_w, chal_w)
        tip_live = _tip(nav_l3, nav)
        yg = _year_oracle_table(r, live_r, near_r, p34_r)
        sealed = d_live["sealed_2023_plus"]["mdd_improve_pp"]
        tip_y = (tip_live.get("ytd") or {}).get("cagr_lift_pp")
        held_live = d_live["heldout_2019_plus"]["cagr_lift_pp"]
        held_champ = d_champ["heldout_2019_plus"]["cagr_lift_pp"]
        held_near = d_near["heldout_2019_plus"]["cagr_lift_pp"]
        regret = yg["gap_to_oracle_pp"]
        regret_imp_champ = (
            None
            if regret is None or champ_yg["gap_to_oracle_pp"] is None
            else round(float(champ_yg["gap_to_oracle_pp"]) - float(regret), 4)
        )
        wins = int(yg["year_wins"])
        wins_vs_champ = wins - int(champ_yg["year_wins"])
        wins_vs_live = wins - int(live_yg["year_wins"])
        beats_live_n = int(yg["n_beats_live"])
        sealed_ok = sealed is not None and float(sealed) >= SEALED_MDD_FLOOR_PP
        tip_ok = tip_y is None or float(tip_y) >= TIP_Y_FLOOR_PP
        live_held_ok = held_live is not None and float(held_live) >= HELD_CAGR_FLOOR_PP
        held_pos_champ = (
            held_champ is not None and float(held_champ) > 0 and sealed_ok and tip_ok
        )
        dual_obj = (
            live_held_ok
            and sealed_ok
            and tip_ok
            and held_champ is not None
            and float(held_champ) >= HELD_EPS_VS_CHAMP
            and (
                (
                    regret_imp_champ is not None
                    and float(regret_imp_champ) >= YEAR_REGRET_IMPROVE_FLOOR
                )
                or wins_vs_champ >= YEAR_WINS_IMPROVE_FLOOR
                or beats_live_n >= int(champ_yg["n_beats_live"]) + 1
            )
        )
        strong = bool(held_pos_champ and dual_obj)
        rows.append(
            {
                "arm": name,
                "family": fam,
                "verdict_vs_live": _arm_verdict_vs_live(d_live, tip_live),
                "held_vs_live": held_live,
                "held_vs_champ": held_champ,
                "held_vs_near": held_near,
                "full_vs_live": d_live["full"]["cagr_lift_pp"],
                "sealed_vs_live": sealed,
                "tipY_vs_live": tip_y,
                "year_gap_to_oracle_pp": regret,
                "year_regret_improve_vs_champ_pp": regret_imp_champ,
                "year_wins": wins,
                "year_wins_vs_champ": wins_vs_champ,
                "year_wins_vs_live": wins_vs_live,
                "n_beats_live": beats_live_n,
                "n_beats_live_vs_champ": beats_live_n - int(champ_yg["n_beats_live"]),
                "mean_delta_vs_live_pp": yg["mean_delta_vs_live_pp"],
                "held_pos_vs_champ": bool(held_pos_champ),
                "dual_obj_clear": bool(dual_obj),
                "strong_clear": bool(strong),
                "oracle": fam == "ORACLE",
                "is_ref": fam == "REF",
            }
        )

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "arms_live_stack_race.csv", index=False)
    causal = df[~df["oracle"]].copy()
    mech = causal[~causal["is_ref"]].copy()
    hits = mech[mech["strong_clear"] | mech["held_pos_vs_champ"] | mech["dual_obj_clear"]]
    hits.to_csv(OUT / "race_hits.csv", index=False)

    by_fam = (
        mech.groupby("family")
        .agg(
            n=("arm", "count"),
            n_strong=("strong_clear", "sum"),
            n_held_pos=("held_pos_vs_champ", "sum"),
            n_dual=("dual_obj_clear", "sum"),
            max_held_vs_champ=("held_vs_champ", "max"),
            max_held_vs_live=("held_vs_live", "max"),
            max_regret_imp=("year_regret_improve_vs_champ_pp", "max"),
            max_wins_vs_champ=("year_wins_vs_champ", "max"),
            max_beats_live=("n_beats_live", "max"),
        )
        .reset_index()
    )
    by_fam.to_csv(OUT / "family_summary.csv", index=False)

    ranked = mech.sort_values(
        by=[
            "strong_clear",
            "held_pos_vs_champ",
            "dual_obj_clear",
            "year_wins_vs_champ",
            "n_beats_live_vs_champ",
            "year_regret_improve_vs_champ_pp",
            "held_vs_champ",
            "held_vs_live",
            "sealed_vs_live",
        ],
        ascending=[False, False, False, False, False, False, False, False, False],
    )
    top = ranked.head(20)
    top.to_csv(OUT / "top_arms.csv", index=False)

    strong_hits = mech[mech["strong_clear"]]
    held_hits = mech[mech["held_pos_vs_champ"]]
    dual_hits = mech[mech["dual_obj_clear"]]

    if len(strong_hits):
        champion_row = strong_hits.sort_values(
            by=["year_wins_vs_champ", "n_beats_live", "held_vs_champ", "year_regret_improve_vs_champ_pp"],
            ascending=[False, False, False, False],
        ).iloc[0]
        verdict = "IP3_LIVE_STACK_RACE_HIT"
    elif len(held_hits):
        champion_row = held_hits.sort_values(
            by=["n_beats_live", "year_wins_vs_champ", "held_vs_champ"],
            ascending=[False, False, False],
        ).iloc[0]
        verdict = "IP3_LIVE_STACK_RACE_HIT"
    elif len(dual_hits):
        champion_row = dual_hits.sort_values(
            by=["year_wins_vs_champ", "n_beats_live", "held_vs_champ"],
            ascending=[False, False, False],
        ).iloc[0]
        verdict = "IP3_LIVE_STACK_RACE_SOFT"
    else:
        verdict = "IP3_LIVE_STACK_RACE_NO_EDGE"
        champion_row = ranked.iloc[0] if len(ranked) else None

    n_strong = int(mech["strong_clear"].sum())
    n_held = int(mech["held_pos_vs_champ"].sum())
    n_dual = int(mech["dual_obj_clear"].sum())
    champ = None if champion_row is None else champion_row.to_dict()
    if champ:
        arms_nav[champ["arm"]].to_csv(OUT / f"nav_{champ['arm']}.csv", index=False)
        yg_c = _year_oracle_table(
            _returns(arms_nav[champ["arm"]]), live_r, near_r, p34_r
        )
        pd.DataFrame(yg_c["years"]).to_csv(OUT / "year_oracle_champion.csv", index=False)

    oracle_rows = df[df["oracle"]]
    fam_note = "; ".join(
        f"{r.family}:strong={int(r.n_strong)}/dual={int(r.n_dual)}/held+={int(r.n_held_pos)}/maxΔchamp={r.max_held_vs_champ}/beatsL={int(r.max_beats_live)}"
        for r in by_fam.itertuples()
    )
    optimize = [
        "Objective: causal trail-race / live-override to capture BOTH live-year edge and 0kb1 stack-year edge; no year-cut",
        (
            f"Champion `{champ['arm']}` fam={champ['family']} held_vs_champ={champ['held_vs_champ']} "
            f"held_vs_live={champ['held_vs_live']} regret↑champ={champ['year_regret_improve_vs_champ_pp']} "
            f"winsΔchamp={champ['year_wins_vs_champ']} beats_live={champ['n_beats_live']} "
            f"(parent beats_live={champ_yg['n_beats_live']}) sealed={champ['sealed_vs_live']} tipY={champ['tipY_vs_live']}"
            if champ
            else "No champion"
        ),
        f"Clears: strong={n_strong} · held_pos_vs_champ={n_held} · dual_obj={n_dual} / mech={len(mech)}",
        f"By family: {fam_note}",
        (
            f"Parent CHAMP gap={champ_yg['gap_to_oracle_pp']} wins={champ_yg['year_wins']} "
            f"beats_live={champ_yg['n_beats_live']} · live gap={live_yg['gap_to_oracle_pp']} "
            f"wins={live_yg['year_wins']} · NEAR gap={near_yg['gap_to_oracle_pp']}"
        ),
        (
            f"Oracle DIAG held_vs_champ="
            f"{None if oracle_rows.empty else oracle_rows['held_vs_champ'].max()} "
            f"(same-bar — never promote)"
        ),
        "If IP3_LIVE_STACK_RACE_HIT → draft observe; SOFT → note; NO_EDGE → KEEP 0kb1 DRAFT/HIT parent",
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
        "n_strong_clear": n_strong,
        "n_held_pos_vs_champ": n_held,
        "n_dual_obj_clear": n_dual,
        "parent_champ": {
            "arm": "MUTE_P3_W63_Tm001__S3_MUTESAT",
            "gap_to_oracle_pp": champ_yg["gap_to_oracle_pp"],
            "year_wins": champ_yg["year_wins"],
            "n_beats_live": champ_yg["n_beats_live"],
            "mean_delta_vs_live_pp": champ_yg["mean_delta_vs_live_pp"],
        },
        "family_summary": by_fam.to_dict(orient="records"),
        "champion": champ,
        "top_arms": top.to_dict(orient="records"),
        "optimize_live": optimize,
        "soft_keep": True,
        "path4_live": False,
        "hybrid_t0_carve": False,
        "label": f"{SCREEN_ID}_{generated[:10]}__{verdict}",
    }
    (OUT / "screen.json").write_text(json.dumps(screen, indent=2) + "\n", encoding="utf-8")

    charter_md = "\n".join(
        [
            f"# {CHARTER_ID}",
            "",
            f"Date: {generated[:10]}",
            f"Register: **{REGISTER}** · Parents: {', '.join(PARENTS)}",
            "",
            "## Question",
            "",
            "Can a causal **live↔stack trail-race** (or live-override on 0kb1 "
            "`MUTE_S3_SAT`) capture **both** live-win-year edge and stack-win-year "
            "edge — beating 0kb1 on held or year-wins/regret — without year dummies?",
            "",
            "## Design",
            "",
            "- Parent ref: 0kb1 `MUTE_P3_W63_Tm001__S3_MUTESAT`",
            "- Families: RACE3 · RACE_RECON · RACE_DUAL · OVERRIDE(+confirm) · BLEND",
            "- Success: held+ vs champ, or dual_obj (held≥champ−0.05 + wins/regret/beats_live lift)",
            "- Forbidden: year-cut · lookahead · hybrid T+0 · Path4 live",
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
                "forbidden": ["year_cut", "lookahead_promote", "hybrid_t0", "path4_live"],
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
        f"Register: **{REGISTER}** · mech={len(mech)} · strong={n_strong} · held+={n_held} · dual={n_dual}",
        "",
        "## Parent 0kb1 vs live (year)",
        "",
        f"- CHAMP gap_to_oracle **{champ_yg['gap_to_oracle_pp']}** · wins **{champ_yg['year_wins']}** · "
        f"beats_live years **{champ_yg['n_beats_live']}** · meanΔlive **{champ_yg['mean_delta_vs_live_pp']}**",
        f"- live gap **{live_yg['gap_to_oracle_pp']}** wins **{live_yg['year_wins']}**",
        "",
        "## Family summary",
        "",
        "| Family | n | strong | dual | held+ | maxΔchamp | maxΔlive | max regret↑ | max winsΔ | max beatsL |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in by_fam.to_dict(orient="records"):
        screen_md.append(
            f"| {r['family']} | {r['n']} | {int(r['n_strong'])} | {int(r['n_dual'])} | "
            f"{int(r['n_held_pos'])} | {r['max_held_vs_champ']} | {r['max_held_vs_live']} | "
            f"{r['max_regret_imp']} | {int(r['max_wins_vs_champ'])} | {int(r['max_beats_live'])} |"
        )
    screen_md += [
        "",
        "## Top arms",
        "",
        "| Arm | fam | heldΔchamp | heldΔlive | regret↑ | winsΔ | beatsLΔ | sealed | tipY | vs live |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for r in top.to_dict(orient="records"):
        screen_md.append(
            f"| {r['arm']} | {r['family']} | {r['held_vs_champ']} | {r['held_vs_live']} | "
            f"{r['year_regret_improve_vs_champ_pp']} | {r['year_wins_vs_champ']} | "
            f"{r['n_beats_live_vs_champ']} | {r['sealed_vs_live']} | {r['tipY_vs_live']} | "
            f"{r['verdict_vs_live']} |"
        )
    screen_md += [
        "",
        "## Optimize / disposition",
        "",
        *[f"{i}. {line}" for i, line in enumerate(optimize, 1)],
        "",
        "Repro: `PYTHONPATH=scripts python3 scripts/tipsoft_ip3_live_stack_race_stagea.py`",
        "",
        f"Label: `{screen['label']}`",
        "",
    ]
    write_ops_and_repro_pointer(
        OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", "\n".join(screen_md), kind="screen"
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
                f"- held vs 0kb1 champ: **{(champ or {}).get('held_vs_champ')}**\n"
                f"- held vs live: **{(champ or {}).get('held_vs_live')}**\n"
                f"- year regret↑ vs champ: **{(champ or {}).get('year_regret_improve_vs_champ_pp')}**\n"
                f"- year winsΔ champ: **{(champ or {}).get('year_wins_vs_champ')}** · "
                f"beats_live: **{(champ or {}).get('n_beats_live')}** "
                f"(Δ **{(champ or {}).get('n_beats_live_vs_champ')}**)\n"
                f"- sealed **{(champ or {}).get('sealed_vs_live')}** · tipY **{(champ or {}).get('tipY_vs_live')}**\n"
                f"- clears: strong **{n_strong}** · held+ **{n_held}** · dual **{n_dual}** / {len(mech)}"
                if champ
                else f"- No clear · mech={len(mech)}"
            ),
            "",
            "## Disposition",
            "",
            "- Promote observe only on `IP3_LIVE_STACK_RACE_HIT`",
            "- `IP3_LIVE_STACK_RACE_SOFT` → note · KEEP 0kb1 DRAFT/parent",
            "- `IP3_LIVE_STACK_RACE_NO_EDGE` → KEEP 0kb1 `MUTE_S3_SAT` · Path4 DRAFT",
            "- Soft KEEP · Path4 live OFF · no year-cut · no hybrid T+0",
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
        OPS / f"{DECISION_ID}.md", REP / f"{DECISION_ID}.md", decision_md, kind="decision pack"
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
                "n_held_pos_vs_champ": n_held,
                "n_dual_obj_clear": n_dual,
                "soft_keep": True,
                "path4_live": False,
                "label": f"{DECISION_ID}_{generated[:10]}__{verdict}__NO_LIVE",
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
                "held_vs_champ": None if not champ else champ["held_vs_champ"],
                "held_vs_live": None if not champ else champ["held_vs_live"],
                "year_regret_improve_vs_champ_pp": None
                if not champ
                else champ["year_regret_improve_vs_champ_pp"],
                "year_wins_vs_champ": None if not champ else champ["year_wins_vs_champ"],
                "n_beats_live": None if not champ else champ["n_beats_live"],
                "n_beats_live_vs_champ": None
                if not champ
                else champ["n_beats_live_vs_champ"],
                "n_strong": n_strong,
                "n_held_pos": n_held,
                "n_dual": n_dual,
                "n_mech": len(mech),
                "parent_beats_live": champ_yg["n_beats_live"],
                "parent_gap": champ_yg["gap_to_oracle_pp"],
            },
            indent=2,
        )
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
