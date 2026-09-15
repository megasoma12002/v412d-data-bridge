#!/usr/bin/env python3
"""E45 dual-paper month-end monitor — thin wrapper over ops_dual_paper_month_end."""
from __future__ import annotations

from ops_dual_paper_month_end import DualPaperMonitorSpec, GAPS, ROOT, cli_main

SPEC = DualPaperMonitorSpec(
    label="E45_MONTH_END_PAPER_MONITOR",
    ops_stem="E45_MONTH_END_MONITOR",
    artifact_dir=GAPS,
    base_id="BASE_E16_E18_E22_v2s",
    chal_id="CHAL_E45_E3",
    default_out=ROOT / "repro/e45-dual-paper-observe/month_end",
    base_nav=ROOT / "repro/e45-dual-paper-observe/outputs/base_e16_e18_e22_v2s_daily_nav.csv",
    chal_nav=ROOT / "repro/e45-dual-paper-observe/outputs/chal_e45_e3_daily_nav.csv",
    ledger_hint="scripts/e45_dual_paper_ledgers.py",
    missing_msg="Missing E45 dual-paper NAVs.",
    design_giveback_pp={"heldout_2019_plus": 5.65, "sealed_2023_plus": 9.40},
    write_legacy_summary_names=True,
    extra_payload={
        "stitch_authorized": False,
        "cutover_authorized": False,
        "non_decision_windows": ["mtd"],
    },
    non_actions=(
        "paper observe only",
        "no Soft-Frozen clip flip",
        "no E45 stitch",
        "no live wire from this monitor",
    ),
    md_footer=("- Stitch / Soft-Frozen flip still require a separate human ACCEPT PR",),
)

if __name__ == "__main__":
    raise SystemExit(cli_main(SPEC))
