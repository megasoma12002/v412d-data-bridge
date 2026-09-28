#!/usr/bin/env python3
"""FIN both-quality dual-paper month-end monitor — thin wrapper."""
from __future__ import annotations

from fin_both_quality_observe_helpers import BASE_ID, CHAL_ID
from ops_dual_paper_month_end import DualPaperMonitorSpec, ROOT, cli_main

SPEC = DualPaperMonitorSpec(
    label="FIN_BOTH_QUALITY_MONTH_END_MONITOR",
    ops_stem="FIN_BOTH_QUALITY_MONTH_END_MONITOR",
    base_id=BASE_ID,
    chal_id=CHAL_ID,
    default_out=ROOT / "repro/fin-both-quality-dual-paper-observe/month_end",
    base_nav=ROOT
    / "repro/fin-both-quality-dual-paper-observe/outputs/base_live_fuse_cool_daily_nav.csv",
    chal_nav=ROOT
    / "repro/fin-both-quality-dual-paper-observe/outputs/b_or_k9_x_hard150_daily_nav.csv",
    compare_nav=ROOT
    / "repro/fin-both-quality-dual-paper-observe/outputs/dual_paper_nav_compare.csv",
    ledger_hint="scripts/fin_both_quality_dual_paper_ledgers.py",
    missing_msg="Missing FIN both-quality dual-paper observe NAV.",
    design_giveback_pp={"heldout_2019_plus": 1.0, "sealed_2023_plus": 2.0},
    non_actions=(
        "paper observe only",
        "no Soft-Frozen clip flip",
        "no live both-quality wire from this monitor",
        "SELL_a75 KEEP · cutover BLOCKED",
    ),
    md_footer=("- Soft-Frozen KEEP · cutover BLOCKED · FIN both-quality HARD150 observe",),
)

if __name__ == "__main__":
    raise SystemExit(cli_main(SPEC))
