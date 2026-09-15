#!/usr/bin/env python3
"""E45 M2 BIL_FX month-end monitor — thin wrapper over ops_dual_paper_month_end."""
from __future__ import annotations

from ops_dual_paper_month_end import DualPaperMonitorSpec, ROOT, cli_main

SPEC = DualPaperMonitorSpec(
    label="E45_M2_BIL_FX_MONTH_END_MONITOR",
    ops_stem="E45_M2_BIL_FX_MONTH_END_MONITOR_OPERATING",
    base_id="BASE_E16_E18_E22_v2s",
    chal_id="M2_RELOC_BIL_FX_C35",
    default_out=ROOT / "repro/e45-m2-bil-fx-dual-paper-observe/month_end",
    base_nav=ROOT
    / "repro/e45-m2-bil-fx-dual-paper-observe/outputs/base_e16_e18_e22_v2s_daily_nav.csv",
    chal_nav=ROOT
    / "repro/e45-m2-bil-fx-dual-paper-observe/outputs/m2_reloc_bil_fx_c35_daily_nav.csv",
    ledger_hint="scripts/e45_m2_bil_fx_dual_paper_ledgers.py",
    missing_msg="Missing E45 M2 BIL_FX dual-paper NAVs.",
    design_giveback_pp={"heldout_2019_plus": 2.5, "sealed_2023_plus": 6.0},
    include_score=False,
    extra_payload={
        "operating_observe": True,
        "locked_id": "M2_RELOC_BIL_FX_C35",
        "stitch_authorized": False,
        "def_honesty": "BIL×USDTWD mid proxy — paper DEF only",
    },
    non_actions=(
        "OPERATING_OBSERVE — paper only",
        "No Soft-Frozen / DEFAULT / stitch",
        "No live orders",
    ),
    md_footer=(
        "- Honesty: BIL×USDTWD mid is a paper DEF proxy, not a live tradable book",
    ),
)

if __name__ == "__main__":
    raise SystemExit(cli_main(SPEC))
