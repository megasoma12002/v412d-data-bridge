#!/usr/bin/env python3
"""Soft-assist dual-paper month-end monitor — thin wrapper over ops_dual_paper_month_end."""
from __future__ import annotations

from pathlib import Path

from soft_assist_helpers import OBSERVE_CHAL_ID
from ops_dual_paper_month_end import DualPaperMonitorSpec, ROOT, cli_main

SPEC = DualPaperMonitorSpec(
    label="SOFT_ASSIST_MONTH_END_MONITOR",
    ops_stem="SOFT_ASSIST_MONTH_END_MONITOR",
    base_id="LIVE_KD_OPT",
    chal_id=OBSERVE_CHAL_ID,
    default_out=ROOT / "repro/soft-assist-dual-paper-observe/month_end",
    base_nav=ROOT / "repro/soft-assist-dual-paper-observe/outputs/live_kd_opt_daily_nav.csv",
    chal_nav=ROOT
    / "repro/soft-assist-dual-paper-observe/outputs/soft_champ_plus_k9_lt30_a10_sell_a05_daily_nav.csv",
    compare_nav=ROOT / "repro/soft-assist-dual-paper-observe/outputs/dual_paper_nav_compare.csv",
    ledger_hint="scripts/e16_soft_assist_dual_paper_ledgers.py",
    missing_msg="Missing Soft-assist observe NAV.",
    non_actions=(
        "paper observe only",
        "no Soft-Frozen clip flip",
        "no Soft-assist live wire",
    ),
    md_footer=("- No Soft-assist live wire / Soft-Frozen clip flip",),
)

if __name__ == "__main__":
    raise SystemExit(cli_main(SPEC))
