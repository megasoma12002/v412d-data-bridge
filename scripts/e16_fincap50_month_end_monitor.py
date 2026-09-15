#!/usr/bin/env python3
"""FIN_CAP_50 month-end monitor — thin wrapper (flat_trail; no sealed window)."""
from __future__ import annotations

from ops_dual_paper_month_end import DualPaperMonitorSpec, GAPS, ROOT, cli_main

SPEC = DualPaperMonitorSpec(
    label="FIN_CAP_50_MONTH_END_PAPER_MONITOR",
    ops_stem="FIN_CAP_50_MONTH_END_MONITOR",
    artifact_dir=GAPS,
    base_id="BASE_E16",
    chal_id="FIN_CAP_50",
    default_out=ROOT / "repro/fincap50-dual-paper/month_end",
    base_nav=ROOT / "repro/fincap50-dual-paper/outputs/base_e16_daily_nav.csv",
    chal_nav=ROOT / "repro/fincap50-dual-paper/outputs/fincap50_daily_nav.csv",
    ledger_hint="scripts/e16_fincap50_dual_paper_ledgers.py",
    missing_msg="Missing FIN_CAP_50 dual-paper NAVs.",
    alert_policy="flat_trail",
    design_giveback_pp={},
    include_score=False,
    write_legacy_summary_names=True,
    window_keys=("mtd", "ytd", "trailing_1y", "heldout_2019_plus", "full"),
    flat_trail_windows=("heldout_2019_plus", "ytd", "trailing_1y"),
    extra_payload={
        "authoritative_go_live_status": "NOT_READY_SEALED_CAGR",
        "cutover_blocked": True,
        "cutover_authorized": False,
    },
    non_actions=(
        "paper monitor only",
        "no Soft-Frozen clip flip",
        "go-live stays NOT_READY_SEALED_CAGR until human re-verify",
    ),
)

if __name__ == "__main__":
    raise SystemExit(cli_main(SPEC))
