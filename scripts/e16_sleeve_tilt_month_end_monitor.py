#!/usr/bin/env python3
"""Sleeve-tilt dual-paper month-end monitor — thin wrapper over ops_dual_paper_month_end."""
from __future__ import annotations

from pathlib import Path

from sleeve_tilt_helpers import BASE_ID, CHAMPION_ID
from ops_dual_paper_month_end import DualPaperMonitorSpec, ROOT, cli_main

SPEC = DualPaperMonitorSpec(
    label="SLEEVE_LAYER_TILT_MONTH_END_MONITOR",
    ops_stem="SLEEVE_LAYER_TILT_MONTH_END_MONITOR",
    base_id=BASE_ID,
    chal_id=CHAMPION_ID,
    default_out=ROOT / "repro/sleeve-tilt-dual-paper-observe/month_end",
    base_nav=ROOT / "repro/sleeve-tilt-dual-paper-observe/outputs/live_stack_daily_nav.csv",
    chal_nav=ROOT
    / "repro/sleeve-tilt-dual-paper-observe/outputs/sleeve_rsi14_lt30_a0225_daily_nav.csv",
    compare_nav=ROOT / "repro/sleeve-tilt-dual-paper-observe/outputs/dual_paper_nav_compare.csv",
    ledger_hint="scripts/e16_sleeve_tilt_dual_paper_ledgers.py",
    missing_msg="Missing Sleeve-tilt observe NAV.",
    extra_payload={"soft_assist_observe": "KEEP_INDEPENDENT"},
    non_actions=(
        "paper observe only",
        "no Soft-Frozen clip flip",
        "no live Sleeve-tilt wire",
        "Soft-assist observe KEEP independent",
    ),
    md_footer=("- No live Sleeve-tilt wire / Soft-Frozen clip flip",),
)

if __name__ == "__main__":
    raise SystemExit(cli_main(SPEC))
