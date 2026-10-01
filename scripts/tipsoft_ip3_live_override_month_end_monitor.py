#!/usr/bin/env python3
"""TIPSOFT_P3_LIVE_OVERRIDE_W42_M05_K3 dual-paper month-end monitor — thin wrapper."""
from __future__ import annotations

from ops_dual_paper_month_end import DualPaperMonitorSpec, ROOT, cli_main

SPEC = DualPaperMonitorSpec(
    label="TIPSOFT_IP3_LIVE_OVERRIDE_MONTH_END_MONITOR",
    ops_stem="TIPSOFT_IP3_LIVE_OVERRIDE_MONTH_END_MONITOR",
    base_id="BASE_LIVE_FUSE_COOL",
    chal_id="OVERRIDE_LIVE_W42_M05_K3",
    default_out=ROOT / "repro/tipsoft-ip3-live-override-paper-observe/month_end",
    base_nav=ROOT
    / "repro/tipsoft-ip3-live-override-paper-observe/outputs/nav_BASE_LIVE_FUSE_COOL.csv",
    chal_nav=ROOT
    / "repro/tipsoft-ip3-live-override-paper-observe/outputs/nav_OVERRIDE_LIVE_W42_M05_K3.csv",
    compare_nav=ROOT
    / "repro/tipsoft-ip3-live-override-paper-observe/outputs/dual_paper_nav_compare.csv",
    ledger_hint="scripts/tipsoft_ip3_live_override_dual_paper_ledgers.py",
    missing_msg="Missing TIPSOFT_P3_LIVE_OVERRIDE dual-paper observe NAV.",
    design_giveback_pp={"heldout_2019_plus": 1.0, "sealed_2023_plus": 5.0},
    non_actions=(
        "paper observe only",
        "no Soft-Frozen clip flip",
        "no Path4 live",
        "hybrid Soft-core T+0 carve FORBIDDEN",
        "year-cut FORBIDDEN",
        "Exact T+1 LIVE_OVERRIDE posture · cutover BLOCKED",
    ),
    md_footer=(
        "- Soft KEEP · Path4 OFF · hybrid T+0 carve FORBIDDEN · cutover BLOCKED",
    ),
)

if __name__ == "__main__":
    raise SystemExit(cli_main(SPEC))
