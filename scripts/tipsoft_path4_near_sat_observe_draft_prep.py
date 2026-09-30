#!/usr/bin/env python3
"""DRAFT paper/observe ballot prep for Path4 held-pos gate (0kay HIT).

Champion: ``P4_C001_NEAR&SAT`` — tip Soft Exact T+1 NEARPEAK3 + Path4 CASH_001
only when sat_lead (on NEARPEAK3 days).

Awaiting human OPEN. Soft KEEP · Path4 live OFF · hybrid T+0 FORBIDDEN.
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from ops_repro_ssot import write_ops_and_repro_pointer, write_repro_pointer

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "tipsoft-path4-held-pos-gate-stagea"
OUT = REPRO / "outputs"
OPS = ROOT / "research" / "ops"
REP = REPRO / "reports"

REGISTER = "0kay"
POLICY_ID = "P4_C001_NEAR_AND_SAT"
ARM_ID = "P4_C001_NEAR&SAT"
BALLOT_ID = "TIPSOFT_PATH4_NEAR_SAT_OBSERVE_BALLOT_DRAFT"
CAND_ID = "TIPSOFT_PATH4_NEAR_SAT_PAPER_OBSERVE_CANDIDATE"
CUTOVER_ID = "CUTOVER_CHECKLIST_TIPSOFT_PATH4_NEAR_SAT"

HUMAN_OPEN = (
    "OPEN paper observe: TIPSOFT_P4_C001_NEAR_AND_SAT "
    "(tip Soft Exact T+1 · NEARPEAK3 + Path4 CASH_001 on sat_lead · NOT hybrid T+0)"
)


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()
    day = generated[:10]

    src = OUT / f"nav_{ARM_ID}.csv"
    if not src.exists():
        raise SystemExit(f"missing champion NAV {src}")
    # filesystem-safe copy name
    dst = OUT / f"nav_{POLICY_ID}.csv"
    shutil.copy2(src, dst)

    screen = json.loads((OUT / "screen.json").read_text(encoding="utf-8"))
    ch = screen.get("champion") or {}

    ballot = {
        "id": BALLOT_ID,
        "status": "DRAFT",
        "date": day,
        "register": REGISTER,
        "parents": ["0kay", "0kaw"],
        "policy_id": POLICY_ID,
        "arm_id": ARM_ID,
        "clock": "exact_t1",
        "path4_book": "LIVE_P3_P4_CASH_001",
        "gate": "I_p3=NEARPEAK3 AND I_p4=(NEARPEAK3 ∧ sat_lead) with CASH_001 premium",
        "hybrid_t0_carve": False,
        "live_wire": False,
        "cutover_blocked": True,
        "soft_keep": True,
        "path4_live": False,
        "held_vs_nearpeak3_pp": ch.get("held_vs_near"),
        "sealed_vs_live_pp": ch.get("sealed_vs_live"),
        "tipY_vs_live_pp": ch.get("tipY_vs_live"),
        "open_line": HUMAN_OPEN,
        "label": f"{BALLOT_ID}_{day}__AWAITING_OPEN__NO_LIVE",
    }
    ballot_md = "\n".join(
        [
            f"# {BALLOT_ID}",
            "",
            f"Date: {day}",
            "Status: **DRAFT — awaiting human OPEN** · Soft KEEP · Path4 live OFF · "
            "hybrid T+0 carve **FORBIDDEN** · cutover **BLOCKED**",
            "",
            "## Proposed human line",
            "",
            "```",
            HUMAN_OPEN,
            "```",
            "",
            "## Champion",
            "",
            f"- `{ARM_ID}` / policy `{POLICY_ID}`",
            "- tip Soft Exact T+1 Soft+FUSE+COOL + P3 NEARPEAK3",
            "- Path4 CASH_001 premium only when NEARPEAK3 ∧ sat_lead",
            f"- held vs NEARPEAK3 **+{ch.get('held_vs_near')}** pp · "
            f"sealed vs live **{ch.get('sealed_vs_live')}** · "
            f"tipY vs live **+{ch.get('tipY_vs_live')}**",
            "- 0kay Stage A **`PATH4_HELD_POS_HIT`**",
            "",
            "## Non-goals",
            "",
            "- Live wire / Soft-Frozen flip / always-on Path4 / hybrid T+0 carve",
            "- Replace 0kaw NEARPEAK3 observe (this stacks on top)",
            "",
            "## Evidence",
            "",
            "- `TIPSOFT_PATH4_HELD_POS_GATE_STAGEA_DECISION_PACK.md`",
            f"- Repro NAV: `repro/tipsoft-path4-held-pos-gate-stagea/outputs/nav_{POLICY_ID}.csv`",
            "",
            f"Label: `{ballot['label']}`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{BALLOT_ID}.md", REP / f"{BALLOT_ID}.md", ballot_md, kind="ballot draft"
    )
    (OPS / f"{BALLOT_ID}.json").write_text(json.dumps(ballot, indent=2) + "\n", encoding="utf-8")
    write_repro_pointer(OPS / f"{BALLOT_ID}.json", REP / f"{BALLOT_ID}.json", kind="ballot draft")

    cand = {
        "id": CAND_ID,
        "status": "PAPER_OBSERVE_CANDIDATE_DRAFT",
        "register": REGISTER,
        "policy_id": POLICY_ID,
        "parent_observe": "TIPSOFT_P3_THETA_NEARPEAK3",
        "hybrid_t0_carve": False,
        "path4_live": False,
        "live_wire": False,
        "open_line": HUMAN_OPEN,
        "metrics": {
            "held_vs_near": ch.get("held_vs_near"),
            "sealed_vs_live": ch.get("sealed_vs_live"),
            "tipY_vs_live": ch.get("tipY_vs_live"),
        },
        "label": f"{CAND_ID}_{day}__DRAFT",
    }
    write_ops_and_repro_pointer(
        OPS / f"{CAND_ID}.md",
        REP / f"{CAND_ID}.md",
        "\n".join(
            [
                f"# {CAND_ID}",
                "",
                f"Date: {day} · Status: **PAPER_OBSERVE_CANDIDATE_DRAFT**",
                f"Stacks on 0kaw NEARPEAK3 observe · Path4 CASH_001 ∩ sat_lead",
                f"Ballot: `{BALLOT_ID}.md`",
                "",
                f"Label: `{cand['label']}`",
                "",
            ]
        ),
        kind="candidate",
    )
    (OPS / f"{CAND_ID}.json").write_text(json.dumps(cand, indent=2) + "\n", encoding="utf-8")
    write_repro_pointer(OPS / f"{CAND_ID}.json", REP / f"{CAND_ID}.json", kind="candidate")

    cut = "\n".join(
        [
            f"# {CUTOVER_ID}",
            "",
            f"Date: {day}",
            "Status: **BLOCKED**",
            "",
            "- DRAFT observe only · no live Path4 wire",
            "- Soft KEEP · hybrid T+0 FORBIDDEN",
            "",
            f"Label: `{CUTOVER_ID}_{day}__BLOCKED`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{CUTOVER_ID}.md", REP / f"{CUTOVER_ID}.md", cut, kind="cutover checklist"
    )

    print(json.dumps({"ballot": BALLOT_ID, "open_line": HUMAN_OPEN, "status": "DRAFT"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
