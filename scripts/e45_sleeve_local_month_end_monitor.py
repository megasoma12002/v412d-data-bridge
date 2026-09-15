#!/usr/bin/env python3
"""E45 sleeve-local month-end monitor — thin wrapper over ops_dual_paper_month_end."""
from __future__ import annotations

from ops_dual_paper_month_end import DualPaperMonitorSpec, GAPS, ROOT, cli_main

SPEC = DualPaperMonitorSpec(
    label="E45_SLEEVE_LOCAL_MONTH_END_PAPER_MONITOR",
    ops_stem="E45_SLEEVE_LOCAL_MONTH_END_MONITOR",
    artifact_dir=GAPS,
    base_id="BASE_E16_E18_E22_v2s",
    chal_id="SLEEVE_FIN_ONLY_A10",
    default_out=ROOT / "repro/e45-sleeve-local-dual-paper-observe/month_end",
    base_nav=ROOT
    / "repro/e45-sleeve-local-dual-paper-observe/outputs/base_e16_e18_e22_v2s_daily_nav.csv",
    chal_nav=ROOT
    / "repro/e45-sleeve-local-dual-paper-observe/outputs/sleeve_fin_only_a10_daily_nav.csv",
    ledger_hint="scripts/e45_sleeve_local_dual_paper_ledgers.py",
    missing_msg="Missing E45 sleeve-local dual-paper NAVs.",
    design_giveback_pp={"heldout_2019_plus": 1.25, "sealed_2023_plus": 1.80},
    write_legacy_summary_names=True,
    extra_payload={"stitch_authorized": False, "non_decision_windows": ["mtd"]},
    non_actions=(
        "paper observe only",
        "no Soft-Frozen clip flip",
        "no E45 stitch",
        "no live wire from this monitor",
    ),
)

if __name__ == "__main__":
    raise SystemExit(cli_main(SPEC))
