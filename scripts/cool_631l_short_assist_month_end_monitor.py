#!/usr/bin/env python3
"""00631L CONF_RET3_A10_H5 dual-paper month-end monitor — thin wrapper."""
from __future__ import annotations

from pathlib import Path

from cool_631l_short_assist_observe_helpers import BASE_ID, CHAL_ID
from ops_dual_paper_month_end import DualPaperMonitorSpec, ROOT, cli_main

SPEC = DualPaperMonitorSpec(
    label="COOL_631L_SHORT_ASSIST_MONTH_END_MONITOR",
    ops_stem="COOL_631L_SHORT_ASSIST_MONTH_END_MONITOR",
    base_id=BASE_ID,
    chal_id=CHAL_ID,
    default_out=ROOT / "repro/cool-631l-short-assist-dual-paper-observe/month_end",
    base_nav=ROOT
    / "repro/cool-631l-short-assist-dual-paper-observe/outputs/base_live_fuse_cool_daily_nav.csv",
    chal_nav=ROOT
    / "repro/cool-631l-short-assist-dual-paper-observe/outputs/conf_ret3_a10_h5_daily_nav.csv",
    compare_nav=ROOT
    / "repro/cool-631l-short-assist-dual-paper-observe/outputs/dual_paper_nav_compare.csv",
    ledger_hint="scripts/cool_631l_short_assist_dual_paper_ledgers.py",
    missing_msg="Missing 00631L short-assist observe NAV.",
    design_giveback_pp={"heldout_2019_plus": 1.0, "sealed_2023_plus": 5.0},
    non_actions=(
        "paper observe only",
        "no Soft-Frozen clip flip",
        "no live 00631L membership from this monitor",
        "SHORT_ASSIST_HIT observe posture only",
    ),
    md_footer=("- Soft-Frozen KEEP · cutover BLOCKED · CONF_RET3_A10_H5 observe",),
)

if __name__ == "__main__":
    raise SystemExit(cli_main(SPEC))
