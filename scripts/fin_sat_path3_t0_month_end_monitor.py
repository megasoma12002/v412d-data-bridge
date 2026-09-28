#!/usr/bin/env python3
"""P3_T0_STATE dual-paper month-end monitor — thin wrapper."""
from __future__ import annotations

from fin_sat_path3_t0_observe_helpers import BASE_ID, CHAL_ID
from ops_dual_paper_month_end import DualPaperMonitorSpec, ROOT, cli_main

SPEC = DualPaperMonitorSpec(
    label="FIN_SAT_PATH3_T0_MONTH_END_MONITOR",
    ops_stem="FIN_SAT_PATH3_T0_MONTH_END_MONITOR",
    base_id=BASE_ID,
    chal_id=CHAL_ID,
    default_out=ROOT / "repro/fin-sat-path3-t0-dual-paper-observe/month_end",
    base_nav=ROOT / "repro/fin-sat-path3-t0-dual-paper-observe/outputs/ctrl_live_a10_daily_nav.csv",
    chal_nav=ROOT / "repro/fin-sat-path3-t0-dual-paper-observe/outputs/p3_t0_state_daily_nav.csv",
    compare_nav=ROOT / "repro/fin-sat-path3-t0-dual-paper-observe/outputs/dual_paper_nav_compare.csv",
    ledger_hint="scripts/fin_sat_path3_t0_dual_paper_ledgers.py",
    missing_msg="Missing P3_T0_STATE dual-paper observe NAV.",
    design_giveback_pp={"heldout_2019_plus": 1.0, "sealed_2023_plus": 5.0},
    non_actions=(
        "paper observe only",
        "Exact T+0 carve-out T0_CARVE_FIN_SAT_SWITCH only — no expand",
        "no Soft-Frozen clip flip",
        "no live wire / CONF α flip from this monitor",
        "COMPOSITE + SAT_RELAX observes KEEP",
        "cutover BLOCKED",
    ),
    md_footer=("- Soft-Frozen clips KEEP · T0 carve Path3 only · cutover BLOCKED",),
)

if __name__ == "__main__":
    raise SystemExit(cli_main(SPEC))
