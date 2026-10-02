#!/usr/bin/env python3
"""TIPSOFT_P3_TRAIL42_L4_DD_SWITCH dual-paper month-end monitor — thin wrapper.

LIVE tip apply KEEP (0kbd) · dual-paper observe KEEP · Soft FIN/TEL OFF ·
Path4 OFF · broker false · year-switch FORBIDDEN.
"""
from __future__ import annotations

from ops_dual_paper_month_end import DualPaperMonitorSpec, ROOT, cli_main

SPEC = DualPaperMonitorSpec(
    label="TIPSOFT_IP3_TRAIL42_L4_SWITCH_MONTH_END_MONITOR",
    ops_stem="TIPSOFT_IP3_TRAIL42_L4_SWITCH_MONTH_END_MONITOR",
    base_id="L4_LIVE_P3_WITHIN",
    chal_id="TRAIL42_L4_DD_SWITCH",
    default_out=ROOT / "repro/tipsoft-ip3-trail42-l4-switch-paper-observe/month_end",
    base_nav=ROOT
    / "repro/tipsoft-ip3-trail42-l4-switch-paper-observe/outputs/nav_L4_LIVE_P3_WITHIN.csv",
    chal_nav=ROOT
    / "repro/tipsoft-ip3-trail42-l4-switch-paper-observe/outputs/nav_TRAIL42_L4_DD_SWITCH.csv",
    compare_nav=ROOT
    / "repro/tipsoft-ip3-trail42-l4-switch-paper-observe/outputs/dual_paper_nav_compare.csv",
    ledger_hint="scripts/tipsoft_ip3_trail42_l4_switch_dual_paper_ledgers.py",
    missing_msg="Missing TIPSOFT_P3_TRAIL42_L4_DD_SWITCH dual-paper observe NAV.",
    design_giveback_pp={"heldout_2019_plus": 1.0, "sealed_2023_plus": 5.0},
    non_actions=(
        "LIVE tip apply KEEP (path3_gate_ft_cash_apply)",
        "dual-paper observe KEEP (live twin monitor)",
        "no Soft-Frozen clip flip",
        "Soft FIN/TEL Exact T+1 stay OFF",
        "Path4 live OFF",
        "broker false",
        "year-switch FORBIDDEN",
        "no Soft-refill / no Path4 / no broker from this monitor",
    ),
    md_footer=(
        "- Soft KEEP · DD_SWITCH tip apply KEEP · Path3 WITHIN KEEP · "
        "Path4 OFF · broker false · year-switch FORBIDDEN",
    ),
    extra_payload={
        "policy_id": "TIPSOFT_P3_TRAIL42_L4_DD_SWITCH",
        "register": "0kbd",
        "live_tip_apply": True,
        "wire_mode": "path3_gate_ft_cash_apply",
        "stabilize_parent": "0kbe",
    },
)

if __name__ == "__main__":
    raise SystemExit(cli_main(SPEC))
