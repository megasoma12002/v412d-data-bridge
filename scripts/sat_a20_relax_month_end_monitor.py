#!/usr/bin/env python3
"""SAT_A20_RELAX dual-paper month-end monitor — thin wrapper."""
from __future__ import annotations

from ops_dual_paper_month_end import DualPaperMonitorSpec, ROOT, cli_main
from sat_a20_relax_observe_helpers import BASE_ID, CHAL_ID

SPEC = DualPaperMonitorSpec(
    label="SAT_A20_RELAX_MONTH_END_MONITOR",
    ops_stem="SAT_A20_RELAX_MONTH_END_MONITOR",
    base_id=BASE_ID,
    chal_id=CHAL_ID,
    default_out=ROOT / "repro/sat-a20-relax-dual-paper-observe/month_end",
    base_nav=ROOT / "repro/sat-a20-relax-dual-paper-observe/outputs/ctrl_live_a10_daily_nav.csv",
    chal_nav=ROOT / "repro/sat-a20-relax-dual-paper-observe/outputs/sat_a20_relax_daily_nav.csv",
    compare_nav=ROOT / "repro/sat-a20-relax-dual-paper-observe/outputs/dual_paper_nav_compare.csv",
    ledger_hint="scripts/sat_a20_relax_dual_paper_ledgers.py",
    missing_msg="Missing SAT_A20_RELAX dual-paper observe NAV.",
    design_giveback_pp={"heldout_2019_plus": 1.0, "sealed_2023_plus": 5.0},
    non_actions=(
        "paper observe only",
        "no Soft-Frozen clip flip",
        "no live CONF α densify from this monitor",
        "SAT_RELAX_HIT tip-first posture · cutover BLOCKED",
        "COMPOSITE observe KEEP (parallel)",
    ),
    md_footer=("- Soft-Frozen KEEP · cutover BLOCKED · SAT_A20_RELAX tip-first observe",),
)

if __name__ == "__main__":
    raise SystemExit(cli_main(SPEC))
