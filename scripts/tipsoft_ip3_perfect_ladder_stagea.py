#!/usr/bin/env python3
"""Stage A: tip Soft → perfection ladder disposition (steps 1–4).

Human asked to research the suggested path (shallow→deep):
1. KEEP status quo (stamps / Path3 WITHIN / Soft FIN/TEL OFF)
2. Path3 intermittent gate + OFF-day fill (freeze / 0050 / cash)
3. Pass → dual-paper observe → ACCEPT apply (−P3T0 emit, not return-blend)
4. Soft FIN/TEL reopen / Path4 / broker — default do not

This pack consolidates 0kb6 apply-path + 0kb7 fill-lock evidence into a
ladder verdict. No new live wire · Soft KEEP · Path4 OFF · broker false.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ops_repro_ssot import write_ops_and_repro_pointer

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "tipsoft-ip3-perfect-ladder-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "TIPSOFT_IP3_PERFECT_LADDER_STAGEA_CHARTER"
SCREEN_ID = "TIPSOFT_IP3_PERFECT_LADDER_STAGEA_SCREEN"
DECISION_ID = "TIPSOFT_IP3_PERFECT_LADDER_STAGEA_DECISION_PACK"
REGISTER = "0kb8"
PARENTS = ("0kb7", "0kb6", "0kb2", "0kac")
MECH = "TIPSOFT_IP3_PERFECT_LADDER"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load(name: str) -> dict[str, Any]:
    return json.loads((OPS / name).read_text(encoding="utf-8"))


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()

    apply = _load("TIPSOFT_IP3_APPLY_PATH_STAGEA_SCREEN.json")
    fill = _load("TIPSOFT_IP3_FILL_LOCK_STAGEA_SCREEN.json")
    observe = _load("TIPSOFT_IP3_LIVE_OVERRIDE_DUAL_PAPER_OBSERVE_OPERATING.json")

    gap = (apply.get("design") or {}).get("paper_gap_vs_L4_live_twin") or {}
    ceil = fill.get("tip_soft_ceiling") or {}
    gate = fill.get("gate") or {}
    fill_arms = {
        a["arm"]: a for a in fill.get("arms") or [] if a.get("clock") == "softcore_t0"
    }
    freeze = fill_arms.get("SC_MUTE_FREEZE") or {}
    ft0050 = fill_arms.get("SC_MUTE_FT_TO_0050") or {}
    ftcash = fill_arms.get("SC_MUTE_FT_TO_CASH") or {}

    steps = [
        {
            "step": 1,
            "id": "KEEP_STATUS_QUO",
            "title": "KEEP 现状（安全默认）",
            "status": "CURRENT",
            "live": {
                "path3_within": True,
                "soft_fin_tel": "OFF",
                "tipsoft_override_wire": "gate_stamps_telemetry",
                "path4": False,
                "broker": False,
            },
            "evidence": {
                "paper_OVERRIDE_vs_L3_held_pp": (observe.get("heldout_delta") or {}).get(
                    "cagr_lift_pp"
                ),
                "paper_OVERRIDE_vs_L3_tipY_pp": ((observe.get("tip") or {}).get("ytd") or {}).get(
                    "cagr_lift_pp"
                ),
                "tip_gap_vs_L4_held_pp": gap.get("held_pp"),
                "tip_gap_vs_L4_tipY_pp": gap.get("tipY_pp"),
                "note": "Live tip ≈ L4 always-WITHIN; paper OVERRIDE edge remains observe-only",
            },
            "go": True,
            "blocker": None,
        },
        {
            "step": 2,
            "id": "P3_INTERMITTENT_PLUS_FILL",
            "title": "Path3 间歇门控 + fill（冻结 / 0050 / 现金）",
            "status": "BLOCKED",
            "target": "tipY → MUTE_S3_SAT / OVERRIDE champ · MDD not worse than L4 floors",
            "evidence": {
                "parents": ["0kb6 APPLY_TIPY_OWNERSHIP_BLOCK", "0kb7 FILL_LOCK_BLOCK"],
                "soft_refill_ceiling_tipY_pp": ceil.get("tipY_vs_L4_pp"),
                "soft_refill_feasible": False,
                "path3_on_pct_mute": gate.get("pct_path3_on"),
                "path3_on_pct_near": gate.get("pct_nearpeak3_on"),
                "softcore_FREEZE_held_pp": freeze.get("held_cagr_lift_pp"),
                "softcore_FT0050_held_pp": ft0050.get("held_cagr_lift_pp"),
                "softcore_FTCASH_held_pp": ftcash.get("held_cagr_lift_pp"),
                "n_softcore_clears": fill.get("n_softcore_clears"),
            },
            "go": False,
            "blocker": (
                "Only Soft FIN/TEL refill recovers tipY; freeze/0050/cash lose held under "
                "~90% Path3-OFF. Soft refill FORBIDDEN under WITHIN KEEP."
            ),
            "reopen_if": [
                "Human ACCEPT Soft FIN/TEL Exact T+1 carve on Path3 OFF days (undo WITHIN intent)",
                "OR new high-ON% Path3 gate + Soft-core fill clears held/tipY/MDD floors (new Stage A)",
            ],
        },
        {
            "step": 3,
            "id": "OBSERVE_THEN_ACCEPT_APPLY",
            "title": "过门 → dual-paper observe → ACCEPT apply（−P3T0 emit）",
            "status": "GATED",
            "depends_on": [2],
            "actuator": "Mute/scale Path3 -P3T0 emit by tipsoft_override_on / MUTE_S3_SAT — not return-blend",
            "go": False,
            "blocker": "Step 2 fill lock not cleared — no observe/ACCEPT apply ballot",
            "non_actions": [
                "No research return-blend on tip order_rows",
                "No broker enable from this ladder",
            ],
        },
        {
            "step": 4,
            "id": "SOFT_REOPEN_PATH4_BROKER",
            "title": "Soft FIN/TEL 重开 / Path4 / broker",
            "status": "DEFAULT_NO",
            "go": False,
            "blocker": "Default do not — separate explicit ACCEPT only; not part of tip Soft apply ladder",
            "default": {
                "soft_fin_tel_reopen": False,
                "path4_live": False,
                "broker_live_write": False,
            },
        },
    ]

    verdict = "LADDER_STEP1_KEEP"
    # If somehow step2 cleared in future packs, would flip — here blocked.
    if fill.get("verdict") == "FILL_LOCK_HIT" and apply.get("verdict") in (
        "APPLY_P3ALPHA_HIT",
        "APPLY_TIPY_OWNERSHIP_BLOCK",
    ):
        # fill hit would reopen step2 even if apply tipY block (different actuator)
        if fill.get("verdict") == "FILL_LOCK_HIT":
            verdict = "LADDER_STEP2_OPEN"
    if fill.get("verdict") == "FILL_LOCK_BLOCK":
        verdict = "LADDER_STEP1_KEEP__STEP2_BLOCKED"

    optimize = [
        "Question: research the suggested perfection ladder (steps 1–4)",
        (
            f"Verdict `{verdict}`: current live = **step 1 KEEP** · "
            f"tip gap vs L4 held **+{gap.get('held_pp')}** tipY **+{gap.get('tipY_pp')}**"
        ),
        (
            f"Step 2 BLOCKED (0kb7): Soft-refill tipY **+{ceil.get('tipY_vs_L4_pp')}** FORBIDDEN · "
            f"MUTE Path3-ON **{gate.get('pct_path3_on')}%** · "
            f"FREEZE held **{freeze.get('held_cagr_lift_pp')}** / "
            f"0050 **{ft0050.get('held_cagr_lift_pp')}** / "
            f"CASH **{ftcash.get('held_cagr_lift_pp')}**"
        ),
        "Step 3 GATED: no dual-paper observe / ACCEPT −P3T0 apply until step 2 clears",
        "Step 4 DEFAULT_NO: Soft FIN/TEL reopen · Path4 · broker stay off unless separate ACCEPT",
        "Disposition: stop perfection chase at step 1; reopen only via step-2 unlock conditions",
        "Soft KEEP · Path4 OFF · broker false · stamps KEEP · no live wire this pack",
    ]

    screen = {
        "id": SCREEN_ID,
        "register": REGISTER,
        "parents": list(PARENTS),
        "generated_at_utc": generated,
        "mech": MECH,
        "verdict": verdict,
        "current_step": 1,
        "steps": steps,
        "priors": {
            "0kb6": apply.get("verdict"),
            "0kb7": fill.get("verdict"),
            "0kb2_observe": observe.get("status"),
        },
        "optimize_live": optimize,
        "soft_keep": True,
        "path4_live": False,
        "broker": False,
        "live_wire": False,
        "label": f"{SCREEN_ID}_{generated[:10]}__{verdict}",
    }
    (OUT / "screen.json").write_text(
        json.dumps(screen, indent=2, default=str) + "\n", encoding="utf-8"
    )
    (OUT / "ladder_steps.json").write_text(
        json.dumps(steps, indent=2, default=str) + "\n", encoding="utf-8"
    )

    charter_md = "\n".join(
        [
            f"# {CHARTER_ID}",
            "",
            f"Date: {generated[:10]}",
            f"Register: **{REGISTER}** · Parents: {', '.join(PARENTS)}",
            "",
            "## Question",
            "",
            "Given 0kb6/0kb7, what is the disposition of the tip Soft → perfection ladder "
            "(KEEP → intermittent Path3+fill → observe/ACCEPT apply → Soft/Path4/broker)?",
            "",
            "## Method",
            "",
            "- Consolidate apply-path + fill-lock screens (no new live actuators)",
            "- Score each ladder step: CURRENT / BLOCKED / GATED / DEFAULT_NO",
            "- State reopen conditions for step 2 only",
            "",
            "## Forbidden",
            "",
            "- Soft FIN/TEL re-enable · Path4 live · broker · year-cut · hybrid T+0 · "
            "apply wire without step-2 clear + dedicated ACCEPT",
            "",
            f"Label: `{CHARTER_ID}_{generated[:10]}`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{CHARTER_ID}.md", REP / f"{CHARTER_ID}.md", charter_md, kind="charter"
    )
    write_ops_and_repro_pointer(
        OPS / f"{CHARTER_ID}.json",
        REP / f"{CHARTER_ID}.json",
        json.dumps(
            {
                "id": CHARTER_ID,
                "register": REGISTER,
                "parents": list(PARENTS),
                "question": "perfection ladder disposition steps 1–4",
                "label": f"{CHARTER_ID}_{generated[:10]}",
            },
            indent=2,
        )
        + "\n",
        kind="charter json",
    )

    screen_lines = [
        f"# {SCREEN_ID}",
        "",
        f"Date: {generated[:10]} · Register: **{REGISTER}** · Verdict: **`{verdict}`**",
        "",
        "| Step | ID | Status | Go? |",
        "|---:|---|---|---|",
    ]
    for s in steps:
        screen_lines.append(
            f"| {s['step']} | `{s['id']}` | **{s['status']}** | {'Y' if s.get('go') else 'N'} |"
        )
    screen_lines += [
        "",
        "### Step detail",
        "",
        f"1. **KEEP** — live stamps + Path3 WITHIN + Soft FIN/TEL OFF · tip gap vs L4 "
        f"held **+{gap.get('held_pp')}** tipY **+{gap.get('tipY_pp')}**",
        f"2. **BLOCKED** — Soft-refill tipY **+{ceil.get('tipY_vs_L4_pp')}** FORBIDDEN · "
        f"Path3-ON **{gate.get('pct_path3_on')}%** · FREEZE/0050/CASH held "
        f"**{freeze.get('held_cagr_lift_pp')}** / **{ft0050.get('held_cagr_lift_pp')}** / "
        f"**{ftcash.get('held_cagr_lift_pp')}**",
        "3. **GATED** — no −P3T0 ACCEPT apply until step 2 clears",
        "4. **DEFAULT_NO** — Soft reopen / Path4 / broker",
        "",
        "## Optimize live",
        "",
    ]
    for i, line in enumerate(optimize, 1):
        screen_lines.append(f"{i}. {line}")
    screen_lines += ["", f"Label: `{screen['label']}`", ""]
    write_ops_and_repro_pointer(
        OPS / f"{SCREEN_ID}.md",
        REP / f"{SCREEN_ID}.md",
        "\n".join(screen_lines),
        kind="screen",
    )
    write_ops_and_repro_pointer(
        OPS / f"{SCREEN_ID}.json",
        REP / f"{SCREEN_ID}.json",
        json.dumps(screen, indent=2, default=str) + "\n",
        kind="screen json",
    )

    decision_md = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: {generated[:10]} · Verdict: **`{verdict}`**",
            f"Register: **{REGISTER}** · Parents: {', '.join(PARENTS)}",
            "",
            "## Answer",
            "",
            "**Stay on ladder step 1 (KEEP). Step 2 is blocked; steps 3–4 do not open.**",
            "",
            f"- Step 1 CURRENT: stamps/telemetry · Path3 WITHIN · Soft FIN/TEL OFF · "
            f"tip gap vs L4 held **+{gap.get('held_pp')}** tipY **+{gap.get('tipY_pp')}**",
            f"- Step 2 BLOCKED (0kb6+0kb7): Soft-refill is only tipY unlock and is FORBIDDEN; "
            f"freeze/0050/cash Soft-core held all negative under Path3-ON ~**{gate.get('pct_path3_on')}%**",
            "- Step 3 GATED: no dual-paper observe / ACCEPT `−P3T0` apply (not return-blend)",
            "- Step 4 DEFAULT_NO: Soft FIN/TEL reopen · Path4 · broker",
            "",
            "## Disposition",
            "",
            "- **Do not** chase perfection via more OVERRIDE paper stacks or soft-α-on-override",
            "- **Do not** open ACCEPT apply until a step-2 unlock clears (see reopen_if)",
            "- Live posture KEEP · Soft KEEP · Path4 OFF · broker false · no wire this pack",
            "",
            "## Reopen step 2 only if",
            "",
            "1. Human ACCEPT Soft FIN/TEL Exact T+1 carve on Path3 OFF days, **or**",
            "2. New Stage A: high-ON% Path3 gate + non-Soft fill clears held / tipY / MDD floors",
            "",
            "## Next (optimize list)",
            "",
        ]
    )
    for i, line in enumerate(optimize, 1):
        decision_md += f"{i}. {line}\n"
    decision_md += f"\nLabel: `{DECISION_ID}_{generated[:10]}__{verdict}__NO_LIVE`\n"
    write_ops_and_repro_pointer(
        OPS / f"{DECISION_ID}.md",
        REP / f"{DECISION_ID}.md",
        decision_md,
        kind="decision pack",
    )
    write_ops_and_repro_pointer(
        OPS / f"{DECISION_ID}.json",
        REP / f"{DECISION_ID}.json",
        json.dumps(
            {
                "id": DECISION_ID,
                "register": REGISTER,
                "parents": list(PARENTS),
                "verdict": verdict,
                "current_step": 1,
                "generated_at_utc": generated,
                "steps": steps,
                "optimize_live": optimize,
                "live_wire": False,
                "label": f"{DECISION_ID}_{generated[:10]}__{verdict}__NO_LIVE",
            },
            indent=2,
            default=str,
        )
        + "\n",
        kind="decision pack json",
    )

    print(json.dumps({"verdict": verdict, "current_step": 1, "steps": [
        {"step": s["step"], "id": s["id"], "status": s["status"], "go": s.get("go")}
        for s in steps
    ]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
