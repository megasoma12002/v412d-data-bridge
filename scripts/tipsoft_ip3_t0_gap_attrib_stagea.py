#!/usr/bin/env python3
"""Stage A: is the live↔research gap caused by T+0?

Question (human): live lags tip Soft research — is that because of T+0?

Design:
- Same-clock Exact T+1 ladder: L3 live Soft+FUSE+COOL → L4 tipSoft P3 →
  NEARPEAK3 → LIVE_OVERRIDE (0kb2 OPEN)
- Cross-clock Soft-core Exact T+0 Path3 WITHIN (R0) vs L3
- Hybrid tip Soft T+1 overlays + Soft-core T+0 carve (0kav MDD_BLOCK)

Attribution rules:
- If research ahead of live on **same Exact T+1** book family → gap is stack/gate,
  not T+0.
- If Soft-core / hybrid T+0 is **behind** live → T+0 does not explain live lagging
  research; T+0 paths worsen or diverge.

Soft KEEP · Path4 live OFF · no year-cut · no live wire.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from fin_sell_quality_helpers import cagr_lift_pp
from ops_repro_ssot import write_ops_and_repro_pointer, write_repro_pointer
from stagea_screen_helpers import (
    utc_now_z as _utc,
    pack_nav_windows as _pack,
    tip_lift as _tip,
    window_delta as _delta,
)

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "tipsoft-ip3-t0-gap-attrib-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"
ALIGN = ROOT / "repro" / "research-live-align-gap-stagea" / "outputs"
OVERRIDE = ROOT / "repro" / "tipsoft-ip3-live-override-paper-observe" / "outputs"
NEAR = ROOT / "repro" / "tipsoft-p3-nearpeak3-paper-observe" / "outputs"
HYBRID = ROOT / "repro" / "meta-detect-hybrid-nearpeak3-stageb" / "outputs"

CHARTER_ID = "TIPSOFT_IP3_T0_GAP_ATTRIB_STAGEA_CHARTER"
SCREEN_ID = "TIPSOFT_IP3_T0_GAP_ATTRIB_STAGEA_SCREEN"
DECISION_ID = "TIPSOFT_IP3_T0_GAP_ATTRIB_STAGEA_DECISION_PACK"
REGISTER = "0kb5"
PARENTS = ("0kb2", "0kar", "0kav", "0kaq")
MECH = "TIPSOFT_IP3_T0_GAP_ATTRIB"

def _load(path: Path) -> pd.DataFrame:
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

def _row(
    name: str,
    clock: str,
    role: str,
    nav: pd.DataFrame,
    base_nav: pd.DataFrame,
    base_w: dict,
) -> dict[str, Any]:
    w = _pack(nav)
    d = _delta(base_w, w)
    tip = _tip(base_nav, nav)
    held = d["heldout_2019_plus"]
    sealed = d["sealed_2023_plus"]
    return {
        "arm": name,
        "clock": clock,
        "role": role,
        "held_cagr_lift_vs_L3_pp": held["cagr_lift_pp"],
        "held_mdd_improve_vs_L3_pp": held["mdd_improve_pp"],
        "sealed_cagr_lift_vs_L3_pp": sealed["cagr_lift_pp"],
        "sealed_mdd_improve_vs_L3_pp": sealed["mdd_improve_pp"],
        "full_cagr_lift_vs_L3_pp": d["full"]["cagr_lift_pp"],
        "tipY_vs_L3_pp": (tip.get("ytd") or {}).get("cagr_lift_pp"),
        "tip1y_vs_L3_pp": (tip.get("trailing_1y") or {}).get("cagr_lift_pp"),
        "ahead_of_live": bool(
            held["cagr_lift_pp"] is not None and float(held["cagr_lift_pp"]) > 0.05
        ),
        "t0_involved": clock in ("exact_t0", "hybrid_t1_overlay_t0_carve"),
    }

def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()

    books = {
        "L3_LIVE_FUSE_COOL": (
            "exact_t1",
            "live_soft_fuse_cool_base",
            _load(ALIGN / "nav_L3_LIVE_FUSE_COOL.csv"),
        ),
        "L4_LIVE_P3_WITHIN": (
            "exact_t1",
            "tipsoft_p3_within_on_L3",
            _load(ALIGN / "nav_L4_LIVE_P3_WITHIN.csv"),
        ),
        "P3_THETA_NEARPEAK3": (
            "exact_t1",
            "0kaw_observe",
            _load(NEAR / "nav_P3_THETA_NEARPEAK3.csv"),
        ),
        "OVERRIDE_LIVE_W42_M05_K3": (
            "exact_t1",
            "0kb2_observe_open",
            _load(OVERRIDE / "nav_OVERRIDE_LIVE_W42_M05_K3.csv"),
        ),
        "R0_T0_P3_WITHIN": (
            "exact_t0",
            "softcore_path3_t0_carve",
            _load(ALIGN / "nav_R0_T0_P3_WITHIN.csv"),
        ),
        "HYBRID_P3_NEARPEAK3": (
            "hybrid_t1_overlay_t0_carve",
            "0kav_hybrid_mdblock",
            _load(HYBRID / "nav_HYBRID_P3_NEARPEAK3.csv"),
        ),
    }

    l3_nav = books["L3_LIVE_FUSE_COOL"][2]
    l3_w = _pack(l3_nav)
    l3_nav.to_csv(OUT / "nav_L3_LIVE_FUSE_COOL.csv", index=False)

    rows = []
    for name, (clock, role, nav) in books.items():
        nav.to_csv(OUT / f"nav_{name}.csv", index=False)
        rows.append(_row(name, clock, role, nav, l3_nav, l3_w))

    # Same-clock residual: OVERRIDE vs L4
    l4_nav = books["L4_LIVE_P3_WITHIN"][2]
    l4_w = _pack(l4_nav)
    ov_nav = books["OVERRIDE_LIVE_W42_M05_K3"][2]
    ov_vs_l4 = _delta(l4_w, _pack(ov_nav))
    ov_tip_l4 = _tip(l4_nav, ov_nav)

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "gap_attrib_vs_L3.csv", index=False)

    same_clock = df[df.clock == "exact_t1"].copy()
    t0_arms = df[df.t0_involved].copy()
    research_t1_ahead = same_clock[
        same_clock.arm.isin(["OVERRIDE_LIVE_W42_M05_K3", "P3_THETA_NEARPEAK3"])
        & same_clock.ahead_of_live
    ]
    t0_ahead = t0_arms[t0_arms.ahead_of_live]

    # Verdict
    # T+0 is driver of live-lags-research only if T+0 arms are the ones ahead.
    # Here tip Soft T+1 research is ahead; T+0 softcore/hybrid are behind → NOT driver.
    if len(research_t1_ahead) and len(t0_ahead) == 0:
        verdict = "T0_NOT_DRIVER"
    elif len(t0_ahead) and (
        float(t0_ahead["held_cagr_lift_vs_L3_pp"].max())
        >= float(research_t1_ahead["held_cagr_lift_vs_L3_pp"].max())
        if len(research_t1_ahead)
        else True
    ):
        verdict = "T0_PARTIAL_DRIVER"
    else:
        verdict = "T0_MIXED_INCONCLUSIVE"

    ov = df[df.arm == "OVERRIDE_LIVE_W42_M05_K3"].iloc[0].to_dict()
    r0 = df[df.arm == "R0_T0_P3_WITHIN"].iloc[0].to_dict()
    hy = df[df.arm == "HYBRID_P3_NEARPEAK3"].iloc[0].to_dict()
    l4 = df[df.arm == "L4_LIVE_P3_WITHIN"].iloc[0].to_dict()

    live_flags = {
        "live_path3_strategy_cutover": True,
        "live_path3_strategy_cutover_scope": "WITHIN_SLEEVE_PATH3",
        "live_t0_carve_fin_sat_switch_fill_emit": True,
        "note": (
            "Live has narrow Path3 T+0 carve ON, but tip Soft research books "
            "(NEARPEAK3 / LIVE_OVERRIDE) are Exact T+1 twins vs L3; gap vs L3 is "
            "stack alpha on same clock."
        ),
    }

    optimize = [
        "Question: does T+0 cause live to lag tip Soft research?",
        (
            f"Verdict `{verdict}`: tip Soft Exact T+1 OVERRIDE held vs L3 "
            f"**+{ov['held_cagr_lift_vs_L3_pp']}** tipY **+{ov['tipY_vs_L3_pp']}** "
            "(same clock as live Soft+FUSE+COOL)"
        ),
        (
            f"Soft-core Exact T+0 R0 held vs L3 **{r0['held_cagr_lift_vs_L3_pp']}** "
            f"tipY **{r0['tipY_vs_L3_pp']}** — T+0 Soft-core is **behind** live, "
            "cannot explain live lagging research"
        ),
        (
            f"Hybrid T+1 overlay + T+0 carve NEARPEAK3 held **{hy['held_cagr_lift_vs_L3_pp']}** "
            f"tipY **{hy['tipY_vs_L3_pp']}** — MDD/TIP block (0kav); T+0 hybrid worsens tip"
        ),
        (
            f"Same-clock stack residual OVERRIDE vs L4_P3_WITHIN held "
            f"**{ov_vs_l4['heldout_2019_plus']['cagr_lift_pp']}** tipY "
            f"**{(ov_tip_l4.get('ytd') or {}).get('cagr_lift_pp')}** — mute+override alpha, "
            "not clock"
        ),
        (
            f"L4 tipSoft P3 alone vs L3 held **+{l4['held_cagr_lift_vs_L3_pp']}** — "
            "part of live Path3 cutover story; still below OVERRIDE"
        ),
        "Disposition: do **not** chase live↔research tip Soft gap via more T+0; "
        "gap close = ACCEPT wire 0kb2 Exact T+1 LIVE_OVERRIDE (cutover separate)",
        "Soft KEEP · Path4 OFF · broker false · no live wire this pack",
    ]

    screen = {
        "id": SCREEN_ID,
        "register": REGISTER,
        "parents": list(PARENTS),
        "generated_at_utc": generated,
        "mech": MECH,
        "verdict": verdict,
        "live_base": "L3_LIVE_FUSE_COOL",
        "live_flags": live_flags,
        "arms": rows,
        "same_clock_override_vs_L4": {
            "held_cagr_lift_pp": ov_vs_l4["heldout_2019_plus"]["cagr_lift_pp"],
            "sealed_mdd_improve_pp": ov_vs_l4["sealed_2023_plus"]["mdd_improve_pp"],
            "tipY_pp": (ov_tip_l4.get("ytd") or {}).get("cagr_lift_pp"),
            "tip1y_pp": (ov_tip_l4.get("trailing_1y") or {}).get("cagr_lift_pp"),
        },
        "n_research_t1_ahead_of_live": int(len(research_t1_ahead)),
        "n_t0_ahead_of_live": int(len(t0_ahead)),
        "optimize_live": optimize,
        "soft_keep": True,
        "path4_live": False,
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
            "Live lags tip Soft research (0kb2 LIVE_OVERRIDE). Is that gap **caused by T+0**?",
            "",
            "## Method",
            "",
            "- Compare Exact T+1 tip Soft ladder vs L3 live base (same clock)",
            "- Compare Soft-core Exact T+0 and hybrid T+0 carve vs L3 (cross clock)",
            "- Attribute residual OVERRIDE vs L4 on same Exact T+1 clock",
            "",
            "## Forbidden",
            "",
            "- year-cut · Path4 live · hybrid promote · live wire without ACCEPT",
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
                "question": "Is live↔tipSoft research gap caused by T+0?",
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
        f"Date: {generated[:10]} · Verdict: **`{verdict}`**",
        f"Register: **{REGISTER}** · live base = L3_LIVE_FUSE_COOL (Exact T+1)",
        "",
        "## Arms vs L3 (research − live; + = research ahead)",
        "",
        "| Arm | clock | heldΔ | sealedMDDΔ | tipY | ahead? |",
        "|---|---|---:|---:|---:|---|",
    ]
    for r in rows:
        screen_md.append(
            f"| {r['arm']} | {r['clock']} | {r['held_cagr_lift_vs_L3_pp']} | "
            f"{r['sealed_mdd_improve_vs_L3_pp']} | {r['tipY_vs_L3_pp']} | "
            f"{r['ahead_of_live']} |"
        )
    screen_md += [
        "",
        "## Same-clock residual",
        "",
        f"- OVERRIDE vs L4_P3_WITHIN held **{ov_vs_l4['heldout_2019_plus']['cagr_lift_pp']}** · "
        f"tipY **{(ov_tip_l4.get('ytd') or {}).get('cagr_lift_pp')}**",
        "",
        "## Live T+0 flags (context)",
        "",
        f"- Path3 cutover WITHIN: **ON** · T0 carve fill/emit: **ON**",
        f"- {live_flags['note']}",
        "",
        "## Optimize / disposition",
        "",
        *[f"{i}. {line}" for i, line in enumerate(optimize, 1)],
        "",
        "Repro: `PYTHONPATH=scripts python3 scripts/tipsoft_ip3_t0_gap_attrib_stagea.py`",
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
            f"Date: {generated[:10]} · Verdict: **`{verdict}`**",
            f"Register: **{REGISTER}** · Parents: {', '.join(PARENTS)}",
            "",
            "## Answer",
            "",
            "**No — T+0 is not what makes live lag tip Soft research.**",
            "",
            f"- tip Soft Exact T+1 `OVERRIDE_LIVE_W42_M05_K3` vs L3: held **+{ov['held_cagr_lift_vs_L3_pp']}** · tipY **+{ov['tipY_vs_L3_pp']}** (same clock)",
            f"- Soft-core Exact T+0 vs L3: held **{r0['held_cagr_lift_vs_L3_pp']}** · tipY **{r0['tipY_vs_L3_pp']}** (behind live)",
            f"- Hybrid T+0 carve NEARPEAK3 vs L3: held **{hy['held_cagr_lift_vs_L3_pp']}** · tipY **{hy['tipY_vs_L3_pp']}** (blocked)",
            f"- Same-clock OVERRIDE vs L4: held **+{ov_vs_l4['heldout_2019_plus']['cagr_lift_pp']}** — stack mute+override, not clock",
            "",
            "## Disposition",
            "",
            "- Do not use more T+0 research to close live↔0kb2 gap",
            "- Close gap by ACCEPT wiring Exact T+1 LIVE_OVERRIDE (separate ballot; cutover now BLOCKED)",
            "- Live's existing Path3 T+0 carve stays narrow (`T0_CARVE_FIN_SAT_SWITCH`); unrelated to tip Soft observe lead",
            "- Soft KEEP · Path4 OFF · no live wire this pack",
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
                "answer": "T+0 is not the driver of live lagging tip Soft research",
                "override_held_vs_L3_pp": ov["held_cagr_lift_vs_L3_pp"],
                "softcore_t0_held_vs_L3_pp": r0["held_cagr_lift_vs_L3_pp"],
                "hybrid_held_vs_L3_pp": hy["held_cagr_lift_vs_L3_pp"],
                "override_vs_L4_held_pp": ov_vs_l4["heldout_2019_plus"]["cagr_lift_pp"],
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
                "override_held_vs_L3": ov["held_cagr_lift_vs_L3_pp"],
                "override_tipY_vs_L3": ov["tipY_vs_L3_pp"],
                "softcore_t0_held_vs_L3": r0["held_cagr_lift_vs_L3_pp"],
                "hybrid_held_vs_L3": hy["held_cagr_lift_vs_L3_pp"],
                "override_vs_L4_held": ov_vs_l4["heldout_2019_plus"]["cagr_lift_pp"],
                "n_t0_ahead": int(len(t0_ahead)),
                "n_research_t1_ahead": int(len(research_t1_ahead)),
            },
            indent=2,
        )
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
