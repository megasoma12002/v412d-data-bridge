#!/usr/bin/env python3
"""FIN×SAT COMPOSITE dual-paper month-end monitor — thin wrapper."""
from __future__ import annotations

from fin_sat_composite_observe_helpers import BASE_ID, CHAL_ID
from ops_dual_paper_month_end import DualPaperMonitorSpec, ROOT, cli_main

SPEC = DualPaperMonitorSpec(
    label="FIN_SAT_COMPOSITE_MONTH_END_MONITOR",
    ops_stem="FIN_SAT_COMPOSITE_MONTH_END_MONITOR",
    base_id=BASE_ID,
    chal_id=CHAL_ID,
    default_out=ROOT / "repro/fin-sat-composite-dual-paper-observe/month_end",
    base_nav=ROOT
    / "repro/fin-sat-composite-dual-paper-observe/outputs/ctrl_live_a10_daily_nav.csv",
    chal_nav=ROOT
    / "repro/fin-sat-composite-dual-paper-observe/outputs/comp_h150_x_a20_daily_nav.csv",
    compare_nav=ROOT
    / "repro/fin-sat-composite-dual-paper-observe/outputs/dual_paper_nav_compare.csv",
    ledger_hint="scripts/fin_sat_composite_dual_paper_ledgers.py",
    missing_msg="Missing FIN×SAT COMPOSITE dual-paper observe NAV.",
    design_giveback_pp={"heldout_2019_plus": 1.0, "sealed_2023_plus": 2.0},
    non_actions=(
        "paper observe only",
        "no Soft-Frozen clip flip",
        "no live CONF α densify / HARD150 wire from this monitor",
        "COMPOSITE_HIT observe posture only · cutover BLOCKED",
        "SELL_a75 KEEP · live CONF α=0.10 KEEP",
    ),
    md_footer=("- Soft-Frozen KEEP · cutover BLOCKED · FIN×SAT COMPOSITE COMP_H150_x_A20 observe",),
)

if __name__ == "__main__":
    raise SystemExit(cli_main(SPEC))
