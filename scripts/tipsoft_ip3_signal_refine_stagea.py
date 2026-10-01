#!/usr/bin/env python3
"""I_p3 causal signal refine Stage A (0kaz).

Parent insight (0kay / yearly census): live vs NEARPEAK3 vs P3+P4 mix by year —
some years no-stack wins, some P3, rare P3+P4. Do **not** year-cut; refine daily
``I_p3`` (and optionally ``I_p4``) with causal confirms/mutes so stack days keep
edge and non-edge days fall back to live Soft+FUSE+COOL.

Exact T+1 only · hybrid T+0 FORBIDDEN · Soft KEEP · Path4 live OFF.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

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
REPRO = ROOT / "repro" / "tipsoft-ip3-signal-refine-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

LIVESTACK = ROOT / "repro" / "fin-sat-path3-path4-livestack-twin-stageb" / "outputs"
ALIGN = ROOT / "repro" / "research-live-align-gap-stagea" / "outputs"
HARDEN = ROOT / "repro" / "meta-detect-sealed-mdd-harden-stagea" / "outputs"
P3_SIG = (
    ROOT / "repro" / "fin-sat-path3-t0-dual-paper-observe" / "outputs" / "p3_t0_state_signal.csv"
)

CHARTER_ID = "TIPSOFT_IP3_SIGNAL_REFINE_STAGEA_CHARTER"
SCREEN_ID = "TIPSOFT_IP3_SIGNAL_REFINE_STAGEA_SCREEN"
DECISION_ID = "TIPSOFT_IP3_SIGNAL_REFINE_STAGEA_DECISION_PACK"
REGISTER = "0kaz"
PARENTS = ("0kay", "0kaw", "0kau")
MECH = "TIPSOFT_IP3_SIGNAL_REFINE"

BASE_ID = "BASE_LIVE_FUSE_COOL"
NEAR_ID = "REF_P3_THETA_NEARPEAK3"
P34_ID = "REF_P4_C001_NEAR_AND_SAT"
SEALED_MDD_FLOOR_PP = -0.25
TIP_Y_FLOOR_PP = -1.0
HELD_CAGR_FLOOR_PP = 0.10
P3_THETA = 0.005
VS_NEAR_HELD_FLOOR = 0.0
YEAR_GAP_IMPROVE_FLOOR = 0.05  # pp mean year-ret closer to oracle vs NEAR

def _dd_from_peak(nav: pd.DataFrame, win: int = 63) -> pd.Series:
    s = nav.set_index("date")["nav"].astype(float).sort_index()
    peak = s.rolling(win, min_periods=5).max()
    return (s / peak - 1.0).fillna(0.0)

def _proxy_mdd63(nav: pd.DataFrame) -> pd.Series:
    s = nav.set_index("date")["nav"].astype(float).sort_index()
    peak = s.cummax()
    dd = s / peak - 1.0
    return dd.rolling(63, min_periods=5).min().fillna(0.0)

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

def _year_oracle_gap(
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
            "n_years": 0,
            "best_counts": {},
        }
    rows = []
    best_counts = {"live": 0, "P3": 0, "P3+P4": 0, "policy": 0}
    for y in years:
        live_v, near_v, p34_v, pol_v = float(yl[y]), float(yn[y]), float(y4[y]), float(yp[y])
        oracle = max(live_v, near_v, p34_v)
        # which baseline book wins (ignore policy for census)
        base_best = max(
            [("live", live_v), ("P3", near_v), ("P3+P4", p34_v)], key=lambda t: t[1]
        )[0]
        best_counts[base_best] += 1
        if pol_v >= oracle - 1e-9:
            best_counts["policy"] += 1
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
            }
        )
    mean_pol = float(sum(r["policy"] for r in rows) / len(rows))
    mean_ora = float(sum(r["oracle"] for r in rows) / len(rows))
    return {
        "mean_policy": round(mean_pol, 4),
        "mean_oracle": round(mean_ora, 4),
        "gap_to_oracle_pp": round(mean_ora - mean_pol, 4),
        "n_years": len(rows),
        "best_counts": best_counts,
        "years": rows,
    }

def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()

    nav_l3 = _load_nav(LIVESTACK / "nav_BASE_LIVE_FUSE_COOL.csv")
    nav_p3 = _load_nav(LIVESTACK / "nav_LIVE_P3_WITHIN.csv")
    soft_l1 = _load_nav(ALIGN / "nav_L1_SOFT_T1.csv")
    near_nav = _load_nav(HARDEN / "nav_P3_THETA_NEARPEAK3.csv")
    # champion Path4 from 0kay (filesystem-safe copy preferred)
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
    p34_nav = _load_nav(p34_path)
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

    soft_r = _returns(soft_l1).reindex(panel.index).fillna(0.0)
    soft_r5 = soft_r.shift(1).rolling(5, min_periods=3).sum().fillna(0.0)
    soft_r21 = soft_r.shift(1).rolling(21, min_periods=10).sum().fillna(0.0)
    prem_p3_lag5 = prem_p3.shift(1).rolling(5, min_periods=3).sum().fillna(0.0)
    prem_p3_lag10 = prem_p3.shift(1).rolling(10, min_periods=5).sum().fillna(0.0)
    not_bleed = prem_p3_lag5 >= 0.0
    lag5_pos = prem_p3_lag5 > 0.0
    lag10_pos = prem_p3_lag10 > 1e-4
    proxy05 = proxy > -0.05
    proxy08 = proxy > -0.08
    peak2 = dd63 >= -0.02
    peak1 = dd63 >= -0.01
    trail01 = trail.abs() >= 0.01
    trail02 = trail.abs() >= 0.02
    soft_r5_pos = soft_r5 > 0
    soft_r5_neg = soft_r5 < 0
    soft_r21_pos = soft_r21 > 0

    # Align ref NAVs onto panel and rebuild ref returns from stored navs
    near_r_full = _returns(near_nav).reindex(panel.index).fillna(0.0)
    p34_r_full = _returns(p34_nav).reindex(panel.index).fillna(0.0)
    # Prefer premium reconstruct for NEAR so refine is consistent:
    near_r = live_r + nearpeak3.astype(float) * prem_p3
    # 0kay champion: I_p3=NEAR, I_p4=NEAR&sat_lead
    p34_r = live_r + nearpeak3.astype(float) * prem_p3 + (nearpeak3 & sat_lead).astype(
        float
    ) * prem_p4

    # Causal I_p3 refinements (subset of NEARPEAK3 unless REPLACE_ noted)
    i_p3_cands: dict[str, pd.Series] = {
        "NEAR": nearpeak3,
        "NEAR&SAT": nearpeak3 & sat_lead,
        "NEAR&COMP": nearpeak3 & (~sat_lead),
        "NEAR&RISKON": nearpeak3 & risk_on,
        "NEAR&DEFEND": nearpeak3 & defending,
        "NEAR&NOTBLEED": nearpeak3 & not_bleed,
        "NEAR&LAG5POS": nearpeak3 & lag5_pos,
        "NEAR&LAG10POS": nearpeak3 & lag10_pos,
        "NEAR&R5POS": nearpeak3 & soft_r5_pos,
        "NEAR&R5NEG": nearpeak3 & soft_r5_neg,
        "NEAR&R21POS": nearpeak3 & soft_r21_pos,
        "NEAR&PROXY05": nearpeak3 & proxy05,
        "NEAR&PROXY08": nearpeak3 & proxy08,
        "NEAR&PEAK2": nearpeak3 & peak2,
        "NEAR&PEAK1": nearpeak3 & peak1,
        "NEAR&TRAIL01": nearpeak3 & trail01,
        "NEAR&TRAIL02": nearpeak3 & trail02,
        "NEAR&SAT&RISKON": nearpeak3 & sat_lead & risk_on,
        "NEAR&SAT&NOTBLEED": nearpeak3 & sat_lead & not_bleed,
        "NEAR&SAT&R5POS": nearpeak3 & sat_lead & soft_r5_pos,
        "NEAR&RISKON&NOTBLEED": nearpeak3 & risk_on & not_bleed,
        "NEAR&RISKON&R5POS": nearpeak3 & risk_on & soft_r5_pos,
        "NEAR&NOTBLEED&R5POS": nearpeak3 & not_bleed & soft_r5_pos,
        "NEAR&MUTE_R5NEG": nearpeak3 & (~soft_r5_neg),
        "NEAR&MUTE_DEFEND": nearpeak3 & (~defending),
        "NEAR&MUTE_BLEED": nearpeak3 & not_bleed,  # alias clarity
        "NEAR&MUTE_COMP": nearpeak3 & sat_lead,  # mute COMP_LEAD days
        "THETA&SAT": p3_theta & sat_lead,  # drop nearpeak, keep θ
        "THETA&RISKON&SAT": p3_theta & risk_on & sat_lead,
        "THETA&NOTBLEED": p3_theta & not_bleed,
    }
    # Lookahead DIAG only
    i_p3_oracle = nearpeak3 & (prem_p3 > 0)  # same-bar — DIAG
    i_p3_cands["ORACLE_POS_DIAG"] = i_p3_oracle

    # I_p4 modes given I_p3
    p4_modes = {
        "P4OFF": lambda i3: pd.Series(False, index=panel.index),
        "P4_SAT": lambda i3: i3 & sat_lead,
        "P4_NEAR_SAT": lambda i3: nearpeak3 & sat_lead,  # classic 0kay (may exceed i3)
        "P4_DEFEND": lambda i3: i3 & defending,
        "P4_NOTBLEED": lambda i3: i3 & not_bleed,
    }

    base_w = _pack(nav_l3)
    # Use reconstructed near/p34 for consistent apples-to-apples
    near_nav_r = _nav_from_returns(near_r, nav0)
    p34_nav_r = _nav_from_returns(p34_r, nav0)
    near_w = _pack(near_nav_r)
    near_nav_r.to_csv(OUT / f"nav_{NEAR_ID}.csv", index=False)
    p34_nav_r.to_csv(OUT / f"nav_{P34_ID}.csv", index=False)
    nav_l3.to_csv(OUT / f"nav_{BASE_ID}.csv", index=False)

    near_year_gap = _year_oracle_gap(near_r, live_r, near_r, p34_r)
    live_year_gap = _year_oracle_gap(live_r, live_r, near_r, p34_r)
    p34_year_gap = _year_oracle_gap(p34_r, live_r, near_r, p34_r)

    rows: list[dict[str, Any]] = []
    arms_nav: dict[str, pd.DataFrame] = {
        BASE_ID: nav_l3,
        NEAR_ID: near_nav_r,
        P34_ID: p34_nav_r,
    }

    for gname, i3 in i_p3_cands.items():
        i3 = i3.reindex(panel.index).fillna(False).astype(bool)
        for p4name, p4fn in p4_modes.items():
            # Skip redundant: NEAR + P4OFF is the ref; ORACLE only with P4OFF + P4_SAT
            if gname == "ORACLE_POS_DIAG" and p4name not in ("P4OFF", "P4_SAT"):
                continue
            i4 = p4fn(i3).reindex(panel.index).fillna(False).astype(bool)
            # Path4 must never fire without Path3 stack intent
            i4 = i4 & i3
            arm = f"{gname}__{p4name}"
            r = live_r + i3.astype(float) * prem_p3 + i4.astype(float) * prem_p4
            nav = _nav_from_returns(r, nav0)
            arms_nav[arm] = nav
            chal_w = _pack(nav)
            d_live = _delta(base_w, chal_w)
            d_near = _delta(near_w, chal_w)
            tip_live = _tip(nav_l3, nav)
            tip_near = _tip(near_nav_r, nav)
            yg = _year_oracle_gap(r, live_r, near_r, p34_r)
            held_vs_near = d_near["heldout_2019_plus"]["cagr_lift_pp"]
            sealed_vs_live = d_live["sealed_2023_plus"]["mdd_improve_pp"]
            tip_vs_live = (tip_live.get("ytd") or {}).get("cagr_lift_pp")
            gap = yg["gap_to_oracle_pp"]
            near_gap = near_year_gap["gap_to_oracle_pp"]
            gap_improve = (
                None
                if gap is None or near_gap is None
                else round(float(near_gap) - float(gap), 4)
            )
            held_pos = (
                held_vs_near is not None
                and float(held_vs_near) > VS_NEAR_HELD_FLOOR
                and sealed_vs_live is not None
                and float(sealed_vs_live) >= SEALED_MDD_FLOOR_PP
                and (tip_vs_live is None or float(tip_vs_live) >= TIP_Y_FLOOR_PP)
            )
            gap_close = (
                gap_improve is not None
                and float(gap_improve) >= YEAR_GAP_IMPROVE_FLOOR
                and sealed_vs_live is not None
                and float(sealed_vs_live) >= SEALED_MDD_FLOOR_PP
                and (tip_vs_live is None or float(tip_vs_live) >= TIP_Y_FLOOR_PP)
                and d_live["heldout_2019_plus"]["cagr_lift_pp"] is not None
                and float(d_live["heldout_2019_plus"]["cagr_lift_pp"]) >= HELD_CAGR_FLOOR_PP
            )
            rows.append(
                {
                    "arm": arm,
                    "i_p3": gname,
                    "i_p4": p4name,
                    "pct_p3_on": round(float(i3.mean()) * 100, 2),
                    "pct_p4_on": round(float(i4.mean()) * 100, 2),
                    "verdict_vs_live": _arm_verdict_vs_live(d_live, tip_live),
                    "held_vs_live": d_live["heldout_2019_plus"]["cagr_lift_pp"],
                    "full_vs_live": d_live["full"]["cagr_lift_pp"],
                    "sealed_vs_live": sealed_vs_live,
                    "tipY_vs_live": tip_vs_live,
                    "held_vs_near": held_vs_near,
                    "sealed_vs_near": d_near["sealed_2023_plus"]["mdd_improve_pp"],
                    "tipY_vs_near": (tip_near.get("ytd") or {}).get("cagr_lift_pp"),
                    "year_gap_to_oracle_pp": gap,
                    "year_gap_improve_vs_near_pp": gap_improve,
                    "year_mean_policy": yg["mean_policy"],
                    "held_pos_vs_near": bool(held_pos),
                    "year_gap_close": bool(gap_close),
                    "oracle": gname == "ORACLE_POS_DIAG",
                }
            )

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "arms_signal_refine.csv", index=False)

    causal = df[~df["oracle"]].copy()
    # I_p3 refine = gate differs from plain NEARPEAK3 (Path4-on-NEAR is 0kay, not refine)
    causal["is_ip3_refine"] = causal["i_p3"] != "NEAR"
    causal["is_path4_on_near"] = (causal["i_p3"] == "NEAR") & (causal["i_p4"] != "P4OFF")
    p4off = causal[causal["i_p4"] == "P4OFF"].copy()
    refine = causal[causal["is_ip3_refine"]].copy()

    hits = refine[refine["held_pos_vs_near"] | refine["year_gap_close"]].copy()
    hits.to_csv(OUT / "refine_hits.csv", index=False)
    p4off.to_csv(OUT / "arms_p4off_only.csv", index=False)

    causal_sorted = refine.sort_values(
        by=[
            "held_pos_vs_near",
            "year_gap_close",
            "held_vs_near",
            "year_gap_improve_vs_near_pp",
            "sealed_vs_live",
            "tipY_vs_live",
        ],
        ascending=[False, False, False, False, False, False],
    )
    top = causal_sorted.head(15)
    top.to_csv(OUT / "top_arms.csv", index=False)

    champion_row = None
    soft_row = None
    held_refine = refine[refine["held_pos_vs_near"]]
    gap_refine = refine[refine["year_gap_close"]]
    if len(held_refine):
        champion_row = held_refine.sort_values(
            by=["held_vs_near", "year_gap_improve_vs_near_pp", "sealed_vs_live", "tipY_vs_live"],
            ascending=[False, False, False, False],
        ).iloc[0]
    if len(gap_refine):
        soft_row = gap_refine.sort_values(
            by=["held_vs_near", "year_gap_improve_vs_near_pp", "sealed_vs_live", "tipY_vs_live"],
            ascending=[False, False, False, False],
        ).iloc[0]

    n_held = int(refine["held_pos_vs_near"].sum())
    n_gap = int(refine["year_gap_close"].sum())
    n_p4off_held_pos = int(p4off["held_pos_vs_near"].sum())
    p4off_max_held = None if p4off.empty else float(p4off["held_vs_near"].max())
    p4off_max_gap_imp = (
        None if p4off.empty else float(p4off["year_gap_improve_vs_near_pp"].max())
    )
    path4_confirm = causal[causal["is_path4_on_near"] & causal["held_pos_vs_near"]]
    oracle_rows = df[df["oracle"]]

    if champion_row is not None and bool(champion_row["held_pos_vs_near"]):
        verdict = "IP3_REFINE_HIT"
    elif n_p4off_held_pos == 0:
        # no pure I_p3 held+; year-gap closers exist but hurt held → KEEP NEAR
        verdict = "IP3_REFINE_NO_EDGE"
        if soft_row is not None and champion_row is None:
            champion_row = soft_row  # report best gap-soft as note champion
    elif (
        soft_row is not None
        and bool(soft_row["year_gap_close"])
        and float(soft_row["held_vs_near"] or 0) > -0.25
    ):
        verdict = "IP3_YEAR_GAP_SOFT"
        champion_row = soft_row
    else:
        verdict = "NO_EDGE_KEEP_NEAR"

    champ = None if champion_row is None else champion_row.to_dict()
    if champ:
        arm = champ["arm"]
        arms_nav[arm].to_csv(OUT / f"nav_{arm}.csv", index=False)

    optimize = [
        "Objective: causal daily refine of I_p3 (± I_p4) so stack-on days beat live edge and off days fall back to live; close year-oracle gap without year dummies",
        (
            f"Champion `{champ['arm']}` held_vs_near={champ['held_vs_near']} "
            f"gap_improve={champ['year_gap_improve_vs_near_pp']} "
            f"sealed_vs_live={champ['sealed_vs_live']} tipY={champ['tipY_vs_live']} "
            f"live={champ['verdict_vs_live']}"
            if champ
            else "No I_p3-refine champion clearing held_pos (held>-0) or soft year_gap floors"
        ),
        (
            f"I_p3-refine held_pos clears: n={n_held} · year_gap_close n={n_gap} / "
            f"screened_refine={len(refine)} (excl plain NEAR±P4)"
        ),
        (
            f"P4OFF-only max held_vs_near={p4off_max_held} · max gap_improve={p4off_max_gap_imp} · "
            f"held_pos n={n_p4off_held_pos}"
        ),
        (
            f"Path4-on-NEAR held_pos confirms (0kay): n={len(path4_confirm)} "
            f"{'' if path4_confirm.empty else path4_confirm.iloc[0]['arm']}"
        ),
        (
            f"NEAR year gap_to_oracle={near_year_gap['gap_to_oracle_pp']} · "
            f"live gap={live_year_gap['gap_to_oracle_pp']} · "
            f"P34 gap={p34_year_gap['gap_to_oracle_pp']}"
        ),
        (
            f"Oracle DIAG best held_vs_near="
            f"{None if oracle_rows.empty else oracle_rows['held_vs_near'].max()} "
            f"(lookahead — never promote)"
        ),
        "If IP3_REFINE_HIT → draft observe; IP3_YEAR_GAP_SOFT → note only; "
        "IP3_REFINE_NO_EDGE → KEEP 0kaw NEARPEAK3 · Path4 DRAFT 0kay only",
        "Soft KEEP · Path4 live OFF · hybrid T+0 FORBIDDEN · no year-cut · no wire",
    ]

    screen = {
        "id": SCREEN_ID,
        "register": REGISTER,
        "parents": list(PARENTS),
        "generated_at_utc": generated,
        "mech": MECH,
        "verdict": verdict,
        "n_gates_screened": len(causal),
        "n_ip3_refine_screened": len(refine),
        "n_held_pos_vs_near": n_held,
        "n_year_gap_close": n_gap,
        "n_p4off_held_pos": n_p4off_held_pos,
        "p4off_max_held_vs_near": p4off_max_held,
        "p4off_max_gap_improve": p4off_max_gap_imp,
        "path4_on_near_held_pos_n": int(len(path4_confirm)),
        "champion": champ,
        "near_year_oracle": {
            k: near_year_gap[k]
            for k in ("mean_policy", "mean_oracle", "gap_to_oracle_pp", "n_years", "best_counts")
        },
        "live_year_oracle": {
            k: live_year_gap[k]
            for k in ("mean_policy", "mean_oracle", "gap_to_oracle_pp", "n_years", "best_counts")
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

    # --- charter / screen / decision packs ---
    charter_md = "\n".join(
        [
            f"# {CHARTER_ID}",
            "",
            f"Date: {generated[:10]}",
            f"Register: **{REGISTER}** · Parents: {', '.join(PARENTS)}",
            "",
            "## Question",
            "",
            "Can causal daily confirms/mutes refine `I_p3` (and optionally `I_p4`) so "
            "stack-on days keep research edge and other days fall back to live Soft, "
            "closing the year-book oracle gap **without year dummies**?",
            "",
            "## Design",
            "",
            "- Base: `BASE_LIVE_FUSE_COOL` Exact T+1",
            "- Ref: `I_p3=NEARPEAK3` (0kaw) · optional Path4 `NEAR∧sat_lead` CASH_001 (0kay)",
            "- Challengers: NEAR ∧ confirm / NEAR ∧ ¬mute / θ variants · P4 OFF/SAT/DEFEND/NOTBLEED",
            "- Success: `held_vs_near > 0` + live sealed/tip floors **or** year_gap_improve ≥ "
            f"{YEAR_GAP_IMPROVE_FLOOR}pp with live held floor",
            "- Forbidden: year cuts · lookahead promote · hybrid T+0 · Path4 live wire",
            "",
            f"Label: `{CHARTER_ID}_{generated[:10]}`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{CHARTER_ID}.md", REP / f"{CHARTER_ID}.md", charter_md, kind="charter"
    )
    charter_json = {
        "id": CHARTER_ID,
        "register": REGISTER,
        "parents": list(PARENTS),
        "mech": MECH,
        "date": generated[:10],
        "forbidden": ["year_cut", "lookahead_promote", "hybrid_t0", "path4_live"],
    }
    (OPS / f"{CHARTER_ID}.json").write_text(
        json.dumps(charter_json, indent=2) + "\n", encoding="utf-8"
    )
    write_repro_pointer(OPS / f"{CHARTER_ID}.json", REP / f"{CHARTER_ID}.json", kind="charter")

    screen_md_lines = [
        f"# {SCREEN_ID}",
        "",
        f"Date: {generated[:10]} · Verdict: **`{verdict}`** · champion=**`{(champ or {}).get('arm')}`**",
        f"Register: **{REGISTER}** · screened_refine={len(refine)} · held_pos={n_held} · year_gap_close={n_gap}",
        "",
        "## Year-oracle baseline",
        "",
        f"- live gap_to_oracle **{live_year_gap['gap_to_oracle_pp']}** pp · "
        f"NEAR **{near_year_gap['gap_to_oracle_pp']}** · P34 **{p34_year_gap['gap_to_oracle_pp']}**",
        f"- base_best counts (live/P3/P3+P4): `{near_year_gap['best_counts']}`",
        "",
        "## Top causal arms",
        "",
        "| Arm | heldΔNEAR | gap↑vsNEAR | sealedΔlive | tipYΔlive | vs live | p3% | p4% |",
        "|---|---:|---:|---:|---:|---|---:|---:|",
    ]
    for r in top.to_dict(orient="records"):
        screen_md_lines.append(
            f"| {r['arm']} | {r['held_vs_near']} | {r['year_gap_improve_vs_near_pp']} | "
            f"{r['sealed_vs_live']} | {r['tipY_vs_live']} | {r['verdict_vs_live']} | "
            f"{r['pct_p3_on']} | {r['pct_p4_on']} |"
        )
    if not oracle_rows.empty:
        o = oracle_rows.sort_values("held_vs_near", ascending=False).iloc[0]
        screen_md_lines += [
            "",
            "## Oracle DIAG (lookahead)",
            "",
            f"| {o['arm']} | heldΔNEAR {o['held_vs_near']} | gap↑ {o['year_gap_improve_vs_near_pp']} | "
            f"sealed {o['sealed_vs_live']} | tipY {o['tipY_vs_live']} |",
        ]
    screen_md_lines += [
        "",
        "## Optimize / disposition",
        "",
        *[f"{i}. {line}" for i, line in enumerate(optimize, 1)],
        "",
        "Repro: `PYTHONPATH=scripts python3 scripts/tipsoft_ip3_signal_refine_stagea.py`",
        "",
        f"Label: `{screen['label']}`",
        "",
    ]
    screen_md = "\n".join(screen_md_lines)
    write_ops_and_repro_pointer(
        OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", screen_md, kind="screen"
    )
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(screen, indent=2) + "\n", encoding="utf-8")
    write_repro_pointer(OPS / f"{SCREEN_ID}.json", REP / f"{SCREEN_ID}.json", kind="screen")

    decision_md = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: {generated[:10]} · Verdict: **`{verdict}`** · champion=**`{(champ or {}).get('arm')}`**",
            f"Register: **{REGISTER}**",
            "",
            "## Result",
            "",
            (
                f"- held vs NEARPEAK3: **{(champ or {}).get('held_vs_near')}** pp\n"
                f"- year_gap improve vs NEAR: **{(champ or {}).get('year_gap_improve_vs_near_pp')}** pp\n"
                f"- sealed vs live: **{(champ or {}).get('sealed_vs_live')}** pp\n"
                f"- tipY vs live: **{(champ or {}).get('tipY_vs_live')}** pp\n"
                f"- held_pos clears: **{n_held}** · year_gap_close: **{n_gap}** / {len(causal)}"
                if champ
                else f"- No arm cleared held_pos or year_gap floors · screened={len(causal)}"
            ),
            "",
            "## Disposition",
            "",
            "- Promote refined observe only on `IP3_REFINE_HIT`",
            "- `IP3_YEAR_GAP_SOFT` → research note only · KEEP 0kaw NEARPEAK3",
            "- `IP3_REFINE_NO_EDGE` → KEEP NEARPEAK3 observe · Path4 DRAFT (0kay) · no I_p3 replace",
            "- Else KEEP NEARPEAK3 observe · Path4 DRAFT (0kay) only · Path4 live OFF",
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
    decision_json = {
        "id": DECISION_ID,
        "register": REGISTER,
        "parents": list(PARENTS),
        "verdict": verdict,
        "champion": champ,
        "n_held_pos_vs_near": n_held,
        "n_year_gap_close": n_gap,
        "soft_keep": True,
        "path4_live": False,
        "hybrid_t0_carve": False,
        "label": f"{DECISION_ID}_{generated[:10]}__{verdict}__NO_LIVE",
    }
    (OPS / f"{DECISION_ID}.json").write_text(
        json.dumps(decision_json, indent=2) + "\n", encoding="utf-8"
    )
    write_repro_pointer(
        OPS / f"{DECISION_ID}.json", REP / f"{DECISION_ID}.json", kind="decision pack"
    )

    # persist year tables for NEAR / champion
    pd.DataFrame(near_year_gap["years"]).to_csv(OUT / "year_oracle_near.csv", index=False)
    if champ:
        yg_c = _year_oracle_gap(
            _returns(arms_nav[champ["arm"]]), live_r, near_r, p34_r
        )
        pd.DataFrame(yg_c["years"]).to_csv(OUT / "year_oracle_champion.csv", index=False)

    print(
        json.dumps(
            {
                "verdict": verdict,
                "champion": None if not champ else champ["arm"],
                "held_vs_near": None if not champ else champ["held_vs_near"],
                "year_gap_improve_vs_near_pp": None
                if not champ
                else champ["year_gap_improve_vs_near_pp"],
                "n_held_pos": n_held,
                "n_year_gap_close": n_gap,
                "near_gap_to_oracle": near_year_gap["gap_to_oracle_pp"],
            },
            indent=2,
        )
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
