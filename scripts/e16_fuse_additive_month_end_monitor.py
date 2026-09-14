#!/usr/bin/env python3
"""FUSE_ADDITIVE dual-paper month-end monitor — thin wrapper over ops_dual_paper_month_end."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fuse_additive_helpers import BASE_ID, FUSE_ID
from ops_dual_paper_month_end import DualPaperMonitorSpec, ROOT, cli_main

SPEC = DualPaperMonitorSpec(
    label="FUSE_ADDITIVE_MONTH_END_MONITOR",
    ops_stem="FUSE_ADDITIVE_MONTH_END_MONITOR",
    base_id=BASE_ID,
    chal_id=FUSE_ID,
    default_out=ROOT / "repro/fuse-additive-dual-paper-observe/month_end",
    base_nav=ROOT / "repro/fuse-additive-dual-paper-observe/outputs/live_stack_daily_nav.csv",
    chal_nav=ROOT / "repro/fuse-additive-dual-paper-observe/outputs/fuse_additive_daily_nav.csv",
    compare_nav=ROOT / "repro/fuse-additive-dual-paper-observe/outputs/dual_paper_nav_compare.csv",
    ledger_hint="scripts/e16_fuse_additive_dual_paper_ledgers.py",
    missing_msg="Missing FUSE_ADDITIVE observe NAV.",
    extra_payload={
        "soft_assist_observe": "KEEP_INDEPENDENT",
        "sleeve_tilt_observe": "KEEP_INDEPENDENT",
        "ops_auto_fuse": False,
    },
    non_actions=(
        "paper observe only",
        "no Soft-Frozen clip flip",
        "no live Sleeve-tilt wire",
        "Soft-assist observe KEEP independent",
        "Sleeve-tilt observe KEEP independent",
        "ops auto-fuse still FORBIDDEN",
    ),
    md_title=None,
    md_footer=("- No live FUSE_ADDITIVE wire / Soft-Frozen clip flip / Soft∥Sleeve auto-fuse",),
)

if __name__ == "__main__":
    raise SystemExit(cli_main(SPEC))
