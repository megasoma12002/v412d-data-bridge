#!/usr/bin/env python3
"""民營 native dual-paper month-end monitor — thin wrapper over ops_dual_paper_month_end."""
from __future__ import annotations

from ops_dual_paper_month_end import DualPaperMonitorSpec, ROOT, cli_main

SPEC = DualPaperMonitorSpec(
    label="FIN_PRIV_NATIVE_MONTH_END_MONITOR",
    ops_stem="FIN_PRIV_NATIVE_MONTH_END_MONITOR",
    base_id="PRIV_EQUAL",
    chal_id="PRIV_KD_MAY_Klt25_T15",
    default_out=ROOT / "repro/fin-priv-native-dual-paper-observe/month_end",
    base_nav=ROOT / "repro/fin-priv-native-dual-paper-observe/outputs/priv_equal_daily_nav.csv",
    chal_nav=ROOT
    / "repro/fin-priv-native-dual-paper-observe/outputs/priv_kd_may_klt25_t15_daily_nav.csv",
    compare_nav=ROOT
    / "repro/fin-priv-native-dual-paper-observe/outputs/dual_paper_nav_compare.csv",
    ledger_hint="scripts/e16_fin_priv_native_dual_paper_ledgers.py",
    missing_msg="Missing 民營 native observe NAV.",
    md_title="民營 native month-end monitor",
    non_actions=(
        "paper observe only",
        "no Soft-Frozen flip",
        "no live e21 universe expansion",
    ),
    md_footer=("- Hard rules: no live wire / no Soft-Frozen flip",),
)

if __name__ == "__main__":
    raise SystemExit(cli_main(SPEC))
