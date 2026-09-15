#!/usr/bin/env python3
"""L4_DD_PATH_08_50 month-end monitor — thin wrapper (l4 alert policy)."""
from __future__ import annotations

from ops_dual_paper_month_end import DualPaperMonitorSpec, GAPS, ROOT, cli_main

SPEC = DualPaperMonitorSpec(
    label="L4_DD_PATH_MONTH_END_PAPER_MONITOR",
    ops_stem="L4_DD_PATH_MONTH_END_MONITOR",
    artifact_dir=GAPS,
    base_id="BASE_E16",
    chal_id="L4_DD_PATH_08_50",
    default_out=ROOT / "repro/l4-dd-path-dual-paper/month_end",
    base_nav=ROOT / "repro/l4-dd-path-dual-paper/outputs/base_e16_daily_nav.csv",
    chal_nav=ROOT / "repro/l4-dd-path-dual-paper/outputs/l4_dd_path_daily_nav.csv",
    ledger_hint="scripts/e16_l4_dd_path_dual_paper_ledgers.py",
    missing_msg="Missing L4 dual-paper NAVs.",
    alert_policy="l4",
    design_giveback_pp={},
    include_score=False,
    coerce_none_cagr_to_zero=True,
    write_legacy_summary_names=True,
    window_keys=(
        "mtd",
        "ytd",
        "trailing_1y",
        "sealed_2023_plus",
        "heldout_2019_plus",
        "full",
    ),
    fixed_windows=(("validation_2019_2022", "2019-01-01", "2022-12-31"),),
    research_gate_windows=("sealed_2023_plus", "validation_2019_2022"),
    ops_trail_windows=("ytd", "trailing_1y"),
    extra_payload={
        "locked_id": "L4_DD_PATH_08_50",
        "non_decision_windows": ["mtd"],
        "decision_alert_windows": [
            "validation_2019_2022",
            "sealed_2023_plus",
            "ytd",
            "trailing_1y",
        ],
    },
    non_actions=(
        "paper monitor only",
        "no Soft-Frozen clip flip",
        "cutover requires separate human PR",
    ),
)

if __name__ == "__main__":
    raise SystemExit(cli_main(SPEC))
