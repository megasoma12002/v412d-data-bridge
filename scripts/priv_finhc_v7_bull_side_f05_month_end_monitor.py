#!/usr/bin/env python3
"""民股 Gate V7 Bull+Side F05 dual-paper month-end monitor — thin wrapper."""
from __future__ import annotations

from pathlib import Path

from ops_dual_paper_month_end import DualPaperMonitorSpec, ROOT, cli_main
from priv_finhc_v7_observe_helpers import BASE_ID, CHAL_ID

SPEC = DualPaperMonitorSpec(
    label="PRIV_FINHC_V7_BULL_SIDE_F05_MONTH_END_MONITOR",
    ops_stem="PRIV_FINHC_V7_BULL_SIDE_F05_MONTH_END_MONITOR",
    base_id=BASE_ID,
    chal_id=CHAL_ID,
    default_out=ROOT / "repro/priv-finhc-v7-bull-side-f05-dual-paper-observe/month_end",
    base_nav=ROOT
    / "repro/priv-finhc-v7-bull-side-f05-dual-paper-observe/outputs/base_live_fuse_cool_daily_nav.csv",
    chal_nav=ROOT
    / "repro/priv-finhc-v7-bull-side-f05-dual-paper-observe/outputs/v7_bull_side_f05_kdmay_daily_nav.csv",
    compare_nav=ROOT
    / "repro/priv-finhc-v7-bull-side-f05-dual-paper-observe/outputs/dual_paper_nav_compare.csv",
    ledger_hint="scripts/priv_finhc_v7_bull_side_f05_dual_paper_ledgers.py",
    missing_msg="Missing 民股 V7 Bull+Side F05 observe NAV.",
    design_giveback_pp={"heldout_2019_plus": 1.0, "sealed_2023_plus": 5.0},
    non_actions=(
        "paper observe only",
        "no Soft-Frozen FinPriv expand",
        "no live wire from this monitor",
        "near-flat CAGR SOFT is observe posture only",
    ),
    md_footer=("- Soft-Frozen 公股 R1 KEEP · cutover BLOCKED · near-flat observe",),
)

if __name__ == "__main__":
    raise SystemExit(cli_main(SPEC))
