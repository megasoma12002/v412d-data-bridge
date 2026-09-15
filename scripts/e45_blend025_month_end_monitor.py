#!/usr/bin/env python3
"""E45 blend-α=0.25 month-end monitor — thin wrapper (observe archived; pack disabled)."""
from __future__ import annotations

from ops_dual_paper_month_end import DualPaperMonitorSpec, GAPS, ROOT, cli_main

SPEC = DualPaperMonitorSpec(
    label="E45_BLEND025_MONTH_END_PAPER_MONITOR",
    ops_stem="E45_BLEND025_MONTH_END_MONITOR",
    artifact_dir=GAPS,
    base_id="BASE_E16_E18_E22_v2s",
    chal_id="BLEND_E45_A25",
    default_out=ROOT / "repro/e45-blend025-dual-paper-observe/month_end",
    base_nav=ROOT / "repro/e45-blend025-dual-paper-observe/outputs/base_e16_e18_e22_v2s_daily_nav.csv",
    chal_nav=ROOT / "repro/e45-blend025-dual-paper-observe/outputs/blend_e45_a25_daily_nav.csv",
    ledger_hint="scripts/e45_blend025_dual_paper_ledgers.py",
    missing_msg="Missing E45 blend025 dual-paper NAVs.",
    design_giveback_pp={"heldout_2019_plus": 2.83, "sealed_2023_plus": 4.36},
    write_legacy_summary_names=True,
    status="ARCHIVED_OBSERVE",
    extra_payload={
        "stitch_authorized": False,
        "archived": True,
        "non_decision_windows": ["mtd"],
    },
    non_actions=(
        "observe archived 2026-09-13",
        "paper only",
        "no Soft-Frozen clip flip",
        "no E45 stitch",
    ),
)

if __name__ == "__main__":
    raise SystemExit(cli_main(SPEC))
