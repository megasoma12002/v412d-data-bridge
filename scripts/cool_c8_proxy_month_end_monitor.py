#!/usr/bin/env python3
"""COOL_c8_f50_d21 dual-paper month-end monitor — thin wrapper."""
from __future__ import annotations

from pathlib import Path

from cool_c8_proxy_observe_helpers import BASE_ID, CHAL_ID
from ops_dual_paper_month_end import DualPaperMonitorSpec, ROOT, cli_main

SPEC = DualPaperMonitorSpec(
    label="COOL_C8_PROXY_MONTH_END_MONITOR",
    ops_stem="COOL_C8_PROXY_MONTH_END_MONITOR",
    base_id=BASE_ID,
    chal_id=CHAL_ID,
    default_out=ROOT / "repro/cool-c8-proxy-dual-paper-observe/month_end",
    base_nav=ROOT / "repro/cool-c8-proxy-dual-paper-observe/outputs/live_stack_daily_nav.csv",
    chal_nav=ROOT
    / "repro/cool-c8-proxy-dual-paper-observe/outputs/cool_c8_f50_d21_daily_nav.csv",
    compare_nav=ROOT
    / "repro/cool-c8-proxy-dual-paper-observe/outputs/dual_paper_nav_compare.csv",
    ledger_hint="scripts/cool_c8_proxy_dual_paper_ledgers.py",
    missing_msg="Missing COOL_c8_f50_d21 observe NAV.",
    design_giveback_pp={"heldout_2019_plus": 1.0, "sealed_2023_plus": 5.0},
    non_actions=(
        "paper observe only",
        "no Soft-Frozen clip flip",
        "no live wire from this monitor",
    ),
    md_footer=("- Soft-Frozen KEEP · cutover BLOCKED",),
)

if __name__ == "__main__":
    raise SystemExit(cli_main(SPEC))
