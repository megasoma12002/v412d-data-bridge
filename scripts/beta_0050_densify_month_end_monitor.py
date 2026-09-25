#!/usr/bin/env python3
"""β densify dual-paper month-end monitor — thin wrapper."""
from __future__ import annotations

from pathlib import Path

from beta_0050_densify_observe_helpers import BASE_ID, CHAL_ID
from ops_dual_paper_month_end import DualPaperMonitorSpec, ROOT, cli_main

SPEC = DualPaperMonitorSpec(
    label="BETA_0050_DENSIFY_MONTH_END_MONITOR",
    ops_stem="BETA_0050_DENSIFY_MONTH_END_MONITOR",
    base_id=BASE_ID,
    chal_id=CHAL_ID,
    default_out=ROOT / "repro/beta-0050-densify-dual-paper-observe/month_end",
    base_nav=ROOT
    / "repro/beta-0050-densify-dual-paper-observe/outputs/live_fuse_cool_daily_nav.csv",
    chal_nav=ROOT
    / "repro/beta-0050-densify-dual-paper-observe/outputs/beta_0050_densify_daily_nav.csv",
    compare_nav=ROOT
    / "repro/beta-0050-densify-dual-paper-observe/outputs/dual_paper_nav_compare.csv",
    ledger_hint="scripts/beta_0050_densify_dual_paper_ledgers.py",
    missing_msg="Missing β densify observe NAV.",
    design_giveback_pp={"heldout_2019_plus": 1.0, "sealed_2023_plus": 5.0},
    non_actions=(
        "paper observe only",
        "no Soft-Frozen clip flip",
        "no live wire from this monitor",
        "near-flat MDD ACCEPT is observe posture only",
    ),
    md_footer=("- Soft-Frozen KEEP · cutover BLOCKED · near-flat observe",),
)

if __name__ == "__main__":
    raise SystemExit(cli_main(SPEC))
