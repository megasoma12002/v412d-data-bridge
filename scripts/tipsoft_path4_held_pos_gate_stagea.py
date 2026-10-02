#!/usr/bin/env python3
"""Path4 held-positive gate search Stage A (0kay).

Parent 0kax: Path4 under NEARPEAK3 can HIT vs live, but all screened gates were
``NO_EDGE`` vs ``P3_THETA_NEARPEAK3`` (held ≤0 vs observe champion).

This pack densifies Path4-only gates with fixed I_p3=NEARPEAK3, hunting for
``held_cagr_lift_pp > 0`` vs NEARPEAK3-only while keeping sealed/tip floors vs live.

Exact T+1 only · hybrid T+0 carve FORBIDDEN · Soft KEEP · Path4 live OFF.
"""
from __future__ import annotations

import json
from itertools import product
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
REPRO = ROOT / "repro" / "tipsoft-path4-held-pos-gate-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

LIVESTACK = ROOT / "repro" / "fin-sat-path3-path4-livestack-twin-stageb" / "outputs"
ALIGN = ROOT / "repro" / "research-live-align-gap-stagea" / "outputs"
HARDEN = ROOT / "repro" / "meta-detect-sealed-mdd-harden-stagea" / "outputs"
P3_SIG = (
    ROOT / "repro" / "fin-sat-path3-t0-dual-paper-observe" / "outputs" / "p3_t0_state_signal.csv"
)

CHARTER_ID = "TIPSOFT_PATH4_HELD_POS_GATE_STAGEA_CHARTER"
SCREEN_ID = "TIPSOFT_PATH4_HELD_POS_GATE_STAGEA_SCREEN"
DECISION_ID = "TIPSOFT_PATH4_HELD_POS_GATE_STAGEA_DECISION_PACK"
REGISTER = "0kay"
PARENTS = ("0kax", "0kaw", "0kau")
MECH = "TIPSOFT_PATH4_HELD_POS_GATE"

BASE_ID = "BASE_LIVE_FUSE_COOL"
NEAR_ID = "REF_P3_THETA_NEARPEAK3"
SEALED_MDD_FLOOR_PP = -0.25
TIP_Y_FLOOR_PP = -1.0
HELD_CAGR_FLOOR_PP = 0.10
P3_THETA = 0.005
VS_NEAR_HELD_FLOOR = 0.0  # must be strictly positive vs NEARPEAK3

def _dd_from_peak(nav: pd.DataFrame, win: int = 63) -> pd.Series:
    s = nav.set_index("date")["nav"].astype(float).sort_index()
    peak = s.rolling(win, min_periods=5).max()
    return (s / peak - 1.0).fillna(0.0)

def _proxy_mdd63(nav: pd.DataFrame) -> pd.Series:
    s = nav.set_index("date")["nav"].astype(float).sort_index()
    peak = s.cummax()
    dd = s / peak - 1.0
    return dd.rolling(63, min_periods=5).min().fillna(0.0)

def _arm_verdict(delta: dict[str, Any], tip: dict[str, Any]) -> str:
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

def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()

    nav_l3 = _load_nav(LIVESTACK / "nav_BASE_LIVE_FUSE_COOL.csv")
    nav_p3 = _load_nav(LIVESTACK / "nav_LIVE_P3_WITHIN.csv")
    soft_l1 = _load_nav(ALIGN / "nav_L1_SOFT_T1.csv")
    near = _load_nav(HARDEN / "nav_P3_THETA_NEARPEAK3.csv")
    nav0 = float(nav_l3["nav"].iloc[0])

    p4_books = {
        "C00025": _load_nav(LIVESTACK / "nav_LIVE_P3_P4_CASH_00025.csv"),
        "C0005": _load_nav(LIVESTACK / "nav_LIVE_P3_P4_CASH_0005.csv"),
        "C001": _load_nav(LIVESTACK / "nav_LIVE_P3_P4_CASH_001.csv"),
    }

    r3 = _returns(nav_l3)
    rp3 = _returns(nav_p3)
    panel = pd.concat({"r3": r3, "rp3": rp3}, axis=1, join="inner")
    for bk, nav in p4_books.items():
        panel[f"r_{bk}"] = _returns(nav)
    panel = panel.dropna(how="any")
    prem_p3 = panel["rp3"] - panel["r3"]
    prem_p4 = {bk: panel[f"r_{bk}"] - panel["rp3"] for bk in p4_books}

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
    i_p3 = p3_theta & (dd63 >= -0.03)

    soft_r = _returns(soft_l1).reindex(panel.index).fillna(0.0)
    soft_r5 = soft_r.shift(1).rolling(5, min_periods=3).sum().fillna(0.0)
    soft_r21 = soft_r.shift(1).rolling(21, min_periods=5).sum().fillna(0.0)

    # Build candidate Path4 gates (causal)
    gates: dict[str, pd.Series] = {}
    gates["OFF"] = pd.Series(False, index=panel.index)
    gates["ALWAYS"] = pd.Series(True, index=panel.index)
    gates["SAME_NEAR"] = i_p3.copy()
    gates["RISKON"] = risk_on.copy()
    gates["DEFEND"] = defending.copy()
    gates["SAT_LEAD"] = sat_lead.copy()
    gates["COMP_LEAD"] = (~sat_lead).copy()
    gates["SOFT_R5_POS"] = soft_r5 > 0
    gates["SOFT_R5_NEG"] = soft_r5 < 0
    gates["SOFT_R21_POS"] = soft_r21 > 0
    gates["SOFT_R21_NEG"] = soft_r21 < 0
    for peak in (0.01, 0.02, 0.03, 0.05):
        gates[f"PEAK{int(peak*100)}"] = dd63 >= -peak
    for th in (0.005, 0.01, 0.015, 0.02):
        gates[f"TRAIL{th}"] = trail.abs() >= th
    # lag prem gates per book C00025 (primary)
    p4_primary = prem_p4["C00025"]
    for k, thr in product((3, 5, 10, 21), (0.0, 1e-4, 5e-4, 1e-3)):
        lag = p4_primary.shift(1).rolling(k, min_periods=max(2, k // 2)).sum().fillna(0.0)
        gates[f"LAG{k}_GT{thr:g}"] = lag > thr
        gates[f"LAG{k}_GE0"] = lag >= 0.0
    # sign of last day premium
    gates["LAG1_POS"] = p4_primary.shift(1).fillna(0.0) > 0
    gates["LAG1_NEG"] = p4_primary.shift(1).fillna(0.0) < 0
    # AND with NEARPEAK3
    base_and = {
        "NEAR&LAG1_POS": i_p3 & gates["LAG1_POS"],
        "NEAR&LAG5_GE0": i_p3 & gates["LAG5_GE0"],
        "NEAR&LAG5_GT0": i_p3 & (p4_primary.shift(1).rolling(5, min_periods=3).sum().fillna(0.0) > 0),
        "NEAR&LAG5_GT1e-4": i_p3 & gates["LAG5_GT0.0001"],
        "NEAR&LAG10_GT1e-4": i_p3 & gates["LAG10_GT0.0001"],
        "NEAR&SAT": i_p3 & sat_lead,
        "NEAR&COMP": i_p3 & (~sat_lead),
        "NEAR&RISKON": i_p3 & risk_on,
        "NEAR&DEFEND": i_p3 & defending,
        "NEAR&R5POS": i_p3 & (soft_r5 > 0),
        "NEAR&R5NEG": i_p3 & (soft_r5 < 0),
        "NEAR&R21POS": i_p3 & (soft_r21 > 0),
        "NEAR&PEAK1": i_p3 & (dd63 >= -0.01),
        "NEAR&PEAK2": i_p3 & (dd63 >= -0.02),
        "NEAR&TRAIL01": i_p3 & (trail.abs() >= 0.01),
        "NEAR&TRAIL02": i_p3 & (trail.abs() >= 0.02),
        "NEAR&LAG1POS&RISKON": i_p3 & gates["LAG1_POS"] & risk_on,
        "NEAR&LAG5GT1e4&R5POS": i_p3 & gates["LAG5_GT0.0001"] & (soft_r5 > 0),
    }
    gates.update(base_and)
    # Oracle diagnostic (lookahead)
    gates["ORACLE_POS_DIAG"] = p4_primary > 0

    arms: dict[str, pd.DataFrame] = {BASE_ID: nav_l3, NEAR_ID: near}
    metas: dict[str, dict[str, Any]] = {
        BASE_ID: {"kind": "base", "pct_p4_on": 0.0},
        NEAR_ID: {"kind": "nearpeak3_ref", "pct_p4_on": 0.0, "note": "0kaw Exact T+1 NEARPEAK3"},
    }
    nav_l3.to_csv(OUT / f"nav_{BASE_ID}.csv", index=False)
    near.to_csv(OUT / f"nav_{NEAR_ID}.csv", index=False)

    # NEARPEAK3 reconstructed for premium attach (align length)
    r_near = panel["r3"] + i_p3.astype(float) * prem_p3

    rows: list[dict[str, Any]] = []
    bw = _pack(nav_l3)
    nw = _pack(near)

    # Evaluate gate × book (cap grid: skip pure OFF duplicates)
    eval_gates = {k: v for k, v in gates.items() if k != "OFF"}
    # Prefer AND-with-NEAR and lag gates first; still eval all
    for book, prem in prem_p4.items():
        for gname, gate in eval_gates.items():
            # Oracle only on primary book
            if gname == "ORACLE_POS_DIAG" and book != "C00025":
                continue
            # Sparse: require some ON days
            g = gate.reindex(panel.index).fillna(False).astype(bool)
            pct = float(g.mean())
            if pct <= 0.0 and gname != "ORACLE_POS_DIAG":
                continue
            # Don't evaluate always-on on non-primary for speed? Keep all books.
            r = r_near + g.astype(float) * prem
            nav = _nav_from_returns(r, nav0)
            arm = f"P4_{book}_{gname}"
            # Skip writing every NAV to disk to keep pack lean — only top later
            cw = _pack(nav)
            delta_live = _delta(bw, cw)
            tip_live = _tip(nav_l3, nav)
            delta_near = _delta(nw, cw)
            tip_near = _tip(near, nav)
            v_live = _arm_verdict(delta_live, tip_live)
            v_near = _arm_verdict(delta_near, tip_near)
            held_vs_near = delta_near["heldout_2019_plus"]["cagr_lift_pp"]
            sealed_vs_live = delta_live["sealed_2023_plus"]["mdd_improve_pp"]
            tip_vs_live = (tip_live.get("ytd") or {}).get("cagr_lift_pp")
            pos = (
                held_vs_near is not None
                and float(held_vs_near) > VS_NEAR_HELD_FLOOR
                and sealed_vs_live is not None
                and float(sealed_vs_live) >= SEALED_MDD_FLOOR_PP
                and (tip_vs_live is None or float(tip_vs_live) >= TIP_Y_FLOOR_PP)
            )
            rows.append(
                {
                    "arm": arm,
                    "book": book,
                    "gate": gname,
                    "pct_p4_on": round(pct * 100, 2),
                    "verdict_vs_live": v_live,
                    "verdict_vs_near": v_near,
                    "held_vs_live": delta_live["heldout_2019_plus"]["cagr_lift_pp"],
                    "full_vs_live": delta_live["full"]["cagr_lift_pp"],
                    "sealed_vs_live": sealed_vs_live,
                    "tipY_vs_live": tip_vs_live,
                    "held_vs_near": held_vs_near,
                    "sealed_vs_near": delta_near["sealed_2023_plus"]["mdd_improve_pp"],
                    "tipY_vs_near": (tip_near.get("ytd") or {}).get("cagr_lift_pp"),
                    "held_pos_vs_near": bool(pos),
                    "oracle": gname == "ORACLE_POS_DIAG",
                    "nav": nav,
                }
            )

    # Rank: held_pos first, then held_vs_near, sealed_vs_live, tip
    def _rank(r: dict[str, Any]) -> tuple:
        return (
            0 if r["held_pos_vs_near"] and not r["oracle"] else 1,
            0 if r["verdict_vs_live"] in ("HIT", "HELD_HIT", "SOFT") else 1,
            0 if (r["held_vs_near"] or -999) > 0 else 1,
            -(r["held_vs_near"] or -999),
            -(r["sealed_vs_live"] or -999),
            -(r["tipY_vs_live"] or -999),
        )

    eligible = [r for r in rows if not r["oracle"]]
    oracle = [r for r in rows if r["oracle"]]
    pos_hits = [r for r in eligible if r["held_pos_vs_near"]]
    champion = sorted(eligible, key=_rank)[0] if eligible else None
    best_pos = sorted(pos_hits, key=_rank)[0] if pos_hits else None
    oracle_best = sorted(oracle, key=lambda r: -(r["held_vs_near"] or -999))[0] if oracle else None

    if best_pos:
        verdict = "PATH4_HELD_POS_HIT"
        champion = best_pos
    elif champion and (champion["held_vs_near"] or -1) > 0:
        # positive held but failed sealed/tip floors
        verdict = "PATH4_HELD_POS_OTHER_BLOCK"
    elif oracle_best and (oracle_best["held_vs_near"] or -1) > 0:
        verdict = "PATH4_HELD_POS_ORACLE_ONLY"
    else:
        verdict = "PATH4_HELD_POS_NO_EDGE"

    # Persist top arms NAVs
    top = sorted(eligible, key=_rank)[:12]
    if best_pos and best_pos not in top:
        top = [best_pos] + top
    if oracle_best:
        top = top + [oracle_best]
    saved = set()
    for r in top:
        if r["arm"] in saved:
            continue
        r["nav"].to_csv(OUT / f"nav_{r['arm']}.csv", index=False)
        saved.add(r["arm"])

    # Summary tables without nav objects
    def _slim(r: dict[str, Any]) -> dict[str, Any]:
        return {k: v for k, v in r.items() if k != "nav"}

    slim_rows = [_slim(r) for r in rows]
    pd.DataFrame(slim_rows).sort_values(
        ["held_pos_vs_near", "held_vs_near", "sealed_vs_live"],
        ascending=[False, False, False],
    ).to_csv(OUT / "arms_vs_nearpeak3.csv", index=False)

    # Top positive / near-miss
    near_miss = sorted(
        [r for r in eligible if (r["held_vs_near"] or -999) > -0.05],
        key=lambda r: -(r["held_vs_near"] or -999),
    )[:20]
    pd.DataFrame([_slim(r) for r in near_miss]).to_csv(OUT / "top_near_miss.csv", index=False)
    if pos_hits:
        pd.DataFrame([_slim(r) for r in sorted(pos_hits, key=_rank)]).to_csv(
            OUT / "held_pos_hits.csv", index=False
        )

    n_pos = len(pos_hits)
    n_pos_held_only = sum(1 for r in eligible if (r["held_vs_near"] or -999) > 0)

    optimize = [
        "Objective: Path4 gate with held_vs_NEARPEAK3 > 0 and live sealed/tip floors",
        (
            f"Champion `{champion['arm']}` held_vs_near={champion['held_vs_near']} "
            f"sealed_vs_live={champion['sealed_vs_live']} tipY={champion['tipY_vs_live']} "
            f"live={champion['verdict_vs_live']} near={champion['verdict_vs_near']}"
            if champion
            else "No champion"
        ),
        (
            f"held_pos_vs_near clears floors: n={n_pos} / screened={len(eligible)}"
        ),
        f"any held_vs_near>0 (ignoring floors): n={n_pos_held_only}",
        (
            f"Oracle DIAG `{oracle_best['arm']}` held_vs_near={oracle_best['held_vs_near']} "
            f"(lookahead — never promote)"
            if oracle_best
            else "No oracle"
        ),
        "If PATH4_HELD_POS_HIT → draft observe on top of 0kaw; else Path4 OFF KEEP",
        "Soft KEEP · Path4 live OFF · hybrid T+0 FORBIDDEN · no wire",
    ]

    screen = {
        "id": SCREEN_ID,
        "register": REGISTER,
        "parents": list(PARENTS),
        "generated_at_utc": generated,
        "mech": MECH,
        "verdict": verdict,
        "n_gates_screened": len(eligible),
        "n_held_pos_floor_clear": n_pos,
        "n_held_pos_raw": n_pos_held_only,
        "champion": _slim(champion) if champion else None,
        "best_held_pos": _slim(best_pos) if best_pos else None,
        "oracle": _slim(oracle_best) if oracle_best else None,
        "top_near_miss": [_slim(r) for r in near_miss[:10]],
        "optimize_live": optimize,
        "soft_keep": True,
        "broker": False,
        "path4_live": False,
        "hybrid_t0_carve": False,
        "label": f"{SCREEN_ID}_{generated[:10]}__{verdict}",
    }
    (OUT / "screen.json").write_text(json.dumps(screen, indent=2) + "\n", encoding="utf-8")

    def _md_top(rs: list[dict[str, Any]], n: int = 12) -> str:
        lines = [
            "| Arm | heldΔNEAR | sealedΔlive | tipYΔlive | vs live | vs NEAR | p4% |",
            "|---|---:|---:|---:|---|---|---:|",
        ]
        for r in rs[:n]:
            lines.append(
                f"| {r['arm']} | {r['held_vs_near']} | {r['sealed_vs_live']} | "
                f"{r['tipY_vs_live']} | {r['verdict_vs_live']} | {r['verdict_vs_near']} | "
                f"{r['pct_p4_on']} |"
            )
        return "\n".join(lines)

    show = sorted(eligible, key=_rank)[:12]
    if oracle_best:
        show_oracle = [oracle_best]
    else:
        show_oracle = []

    charter_md = "\n".join(
        [
            f"# {CHARTER_ID}",
            "",
            f"Date: {generated[:10]}",
            "Status: **Stage A — Path4 gate search for +held vs NEARPEAK3**",
            f"Register: **{REGISTER}** · Parents: {', '.join(PARENTS)}",
            "",
            "## Question",
            "",
            "Is there a causal Path4 gate such that held CAGR vs "
            "`P3_THETA_NEARPEAK3` is strictly positive while live sealed/tip floors hold?",
            "",
            "## Method",
            "",
            "- Fix I_p3 = NEARPEAK3; vary I_p4 × {CASH_00025,0005,001}",
            "- Lag/sign/trail/peak/regime/Soft-momentum gates (causal)",
            "- Success: held_vs_near > 0 AND sealed_vs_live ≥ −0.25 AND tipY_vs_live ≥ −1",
            "",
            f"Label: `{CHARTER_ID}_{generated[:10]}__HELD_POS_SEARCH`",
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
                "hybrid_t0_carve": False,
                "path4_live": False,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    write_repro_pointer(OPS / f"{CHARTER_ID}.json", REP / f"{CHARTER_ID}.json", kind="charter")

    screen_md = "\n".join(
        [
            f"# {SCREEN_ID}",
            "",
            f"Date: {generated[:10]} · Verdict: **`{verdict}`** · "
            f"champion=**`{(champion or {}).get('arm')}`**",
            f"Register: **{REGISTER}** · screened={len(eligible)} · "
            f"held_pos_floor_clear={n_pos} · held_pos_raw={n_pos_held_only}",
            "",
            "## Top causal arms (ranked)",
            "",
            _md_top(show),
            "",
            "## Oracle DIAG (lookahead)",
            "",
            _md_top(show_oracle) if show_oracle else "_none_",
            "",
            "## Optimize / disposition",
            "",
            *[f"{i}. {x}" for i, x in enumerate(optimize, 1)],
            "",
            "Repro: `PYTHONPATH=scripts python3 "
            "scripts/tipsoft_path4_held_pos_gate_stagea.py`",
            "",
            f"Label: `{screen['label']}`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", screen_md, kind="screen"
    )
    (OPS / f"{SCREEN_ID}.json").write_text(
        json.dumps(screen, indent=2) + "\n", encoding="utf-8"
    )
    write_repro_pointer(OPS / f"{SCREEN_ID}.json", REP / f"{SCREEN_ID}.json", kind="screen")

    ch = screen["champion"] or {}
    decision = {
        "label": f"{DECISION_ID}_{generated[:10]}__{verdict}__NO_LIVE",
        "verdict": verdict,
        "register": REGISTER,
        "parents": list(PARENTS),
        "mech": MECH,
        "champion": screen["champion"],
        "best_held_pos": screen.get("best_held_pos"),
        "oracle": screen.get("oracle"),
        "n_held_pos_floor_clear": n_pos,
        "n_held_pos_raw": n_pos_held_only,
        "optimize_live": optimize,
        "soft_keep": True,
        "broker": False,
        "path4_live": False,
        "hybrid_t0_carve": False,
        "wire": False,
    }
    decision_md = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: {generated[:10]} · Verdict: **`{verdict}`** · "
            f"champion=**`{ch.get('arm')}`**",
            f"Register: **{REGISTER}**",
            "",
            "## Result",
            "",
            f"- held vs NEARPEAK3: **{ch.get('held_vs_near')}** pp",
            f"- sealed vs live: **{ch.get('sealed_vs_live')}** pp",
            f"- tipY vs live: **{ch.get('tipY_vs_live')}** pp",
            f"- held_pos floor clears: **{n_pos}** / {len(eligible)}",
            "",
            "## Disposition",
            "",
            "- Promote Path4 observe only on `PATH4_HELD_POS_HIT`",
            "- Otherwise Path4 live OFF KEEP on top of 0kaw NEARPEAK3 observe",
            "",
            "## Next",
            "",
            *[f"{i}. {x}" for i, x in enumerate(optimize, 1)],
            "",
            f"Label: `{decision['label']}`",
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
        json.dumps(decision, indent=2) + "\n", encoding="utf-8"
    )
    write_repro_pointer(
        OPS / f"{DECISION_ID}.json", REP / f"{DECISION_ID}.json", kind="decision pack"
    )

    summary = {
        "verdict": verdict,
        "champion": (champion or {}).get("arm"),
        "held_vs_near": (champion or {}).get("held_vs_near"),
        "sealed_vs_live": (champion or {}).get("sealed_vs_live"),
        "tipY_vs_live": (champion or {}).get("tipY_vs_live"),
        "n_held_pos_floor_clear": n_pos,
        "n_held_pos_raw": n_pos_held_only,
        "oracle_held_vs_near": (oracle_best or {}).get("held_vs_near"),
        "optimize_live": optimize,
    }
    print(json.dumps(summary, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
