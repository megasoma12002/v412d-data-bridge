#!/usr/bin/env python3
"""E45 defend→handoff dual-paper month-end monitor — thin wrapper over ops_dual_paper_month_end."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from e45_defend_handoff_helpers import BASE_ID, CHAL_ID
from ops_dual_paper_month_end import DualPaperMonitorSpec, ROOT, cli_main

SPEC = DualPaperMonitorSpec(
    label="E45_DEFEND_HANDOFF_MONTH_END_MONITOR",
    ops_stem="E45_DEFEND_HANDOFF_MONTH_END_MONITOR",
    base_id=BASE_ID,
    chal_id=CHAL_ID,
    default_out=ROOT / "repro/e45-defend-handoff-dual-paper-observe/month_end",
    base_nav=ROOT / "repro/e45-defend-handoff-dual-paper-observe/outputs/live_stack_daily_nav.csv",
    chal_nav=ROOT
    / "repro/e45-defend-handoff-dual-paper-observe/outputs/dh_dd06_vz1p0_daily_nav.csv",
    compare_nav=ROOT
    / "repro/e45-defend-handoff-dual-paper-observe/outputs/dual_paper_nav_compare.csv",
    ledger_hint="scripts/e45_defend_handoff_dual_paper_ledgers.py",
    missing_msg="Missing E45 defend-handoff observe NAV.",
    design_giveback_pp={"heldout_2019_plus": 2.0, "sealed_2023_plus": 2.0},
    non_actions=(
        "paper observe only",
        "no Soft-Frozen clip flip",
        "no E45 stitch",
        "no live wire from this monitor",
    ),
    md_footer=("- No E45 stitch / Soft-Frozen flip from this monitor",),
)

if __name__ == "__main__":
    raise SystemExit(cli_main(SPEC))
