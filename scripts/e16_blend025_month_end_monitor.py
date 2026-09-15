#!/usr/bin/env python3
"""FINCAP BLEND_025 month-end monitor — thin wrapper (flat_trail alert policy)."""
from __future__ import annotations

from ops_dual_paper_month_end import DualPaperMonitorSpec, GAPS, ROOT, cli_main

SPEC = DualPaperMonitorSpec(
    label="BLEND_025_MONTH_END_PAPER_MONITOR",
    ops_stem="BLEND_025_MONTH_END_MONITOR",
    artifact_dir=GAPS,
    base_id="BASE_E16",
    chal_id="BLEND_025",
    default_out=ROOT / "repro/blend025-dual-paper/month_end",
    base_nav=ROOT / "repro/blend025-dual-paper/outputs/base_e16_daily_nav.csv",
    chal_nav=ROOT / "repro/blend025-dual-paper/outputs/blend025_daily_nav.csv",
    ledger_hint="scripts/e16_blend025_dual_paper_ledgers.py",
    missing_msg="Missing BLEND_025 dual-paper NAVs.",
    alert_policy="flat_trail",
    design_giveback_pp={},
    include_score=False,
    write_legacy_summary_names=True,
    flat_trail_windows=(
        "heldout_2019_plus",
        "sealed_2023_plus",
        "ytd",
        "trailing_1y",
    ),
    extra_payload={
        "locked_id": "BLEND_025",
        "cutover_authorized": False,
        "cutover_blocked": True,
        "non_decision_windows": ["mtd"],
        "decision_alert_windows": [
            "heldout_2019_plus",
            "sealed_2023_plus",
            "ytd",
            "trailing_1y",
        ],
    },
    non_actions=(
        "paper observe only",
        "no Soft-Frozen clip flip",
        "cutover always blocked on this observe sleeve",
    ),
)

if __name__ == "__main__":
    raise SystemExit(cli_main(SPEC))
