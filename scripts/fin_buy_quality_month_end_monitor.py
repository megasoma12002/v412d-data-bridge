#!/usr/bin/env python3
"""FIN buy-quality A/B/C multi-paper month-end monitor — thin wrapper."""
from __future__ import annotations

from fin_buy_quality_observe_helpers import A_ID, B_ID, BASE_ID, C_ID
from ops_dual_paper_month_end import (
    MultiChallengerSpec,
    MultiPaperMonitorSpec,
    ROOT,
    cli_main_multi,
)

SPEC = MultiPaperMonitorSpec(
    label="FIN_BUY_QUALITY_MONTH_END_MONITOR",
    ops_stem="FIN_BUY_QUALITY_MONTH_END_MONITOR",
    base_id=BASE_ID,
    base_nav=ROOT
    / "repro/fin-buy-quality-dual-paper-observe/outputs/base_live_fuse_cool_daily_nav.csv",
    challengers=(
        MultiChallengerSpec(
            chal_id=A_ID,
            slug="a_seed_ma120",
            chal_nav=ROOT
            / "repro/fin-buy-quality-dual-paper-observe/outputs/a_seed_ma120_daily_nav.csv",
            design_giveback_pp={"heldout_2019_plus": 1.0, "sealed_2023_plus": 2.0},
        ),
        MultiChallengerSpec(
            chal_id=B_ID,
            slug="b_ma120_or_k9",
            chal_nav=ROOT
            / "repro/fin-buy-quality-dual-paper-observe/outputs/b_ma120_or_k9_daily_nav.csv",
            design_giveback_pp={"heldout_2019_plus": 1.0, "sealed_2023_plus": 2.0},
        ),
        MultiChallengerSpec(
            chal_id=C_ID,
            slug="c_or_k9_and_below_ma60",
            chal_nav=ROOT
            / "repro/fin-buy-quality-dual-paper-observe/outputs/"
            "c_or_k9_and_below_ma60_daily_nav.csv",
            design_giveback_pp={"heldout_2019_plus": 1.0, "sealed_2023_plus": 2.0},
        ),
    ),
    default_out=ROOT / "repro/fin-buy-quality-dual-paper-observe/month_end",
    ledger_hint="scripts/fin_buy_quality_dual_paper_ledgers.py",
    missing_msg="Missing FIN buy-quality multi-paper observe NAV.",
    non_actions=(
        "paper observe only",
        "no Soft-Frozen clip flip",
        "no live buy-quality wire from this monitor",
        "A/B/C observe posture only · cutover BLOCKED",
    ),
    md_footer=(
        "- Soft-Frozen KEEP · cutover BLOCKED · FIN buy-quality A/B/C observe",
    ),
)

if __name__ == "__main__":
    raise SystemExit(cli_main_multi(SPEC))
