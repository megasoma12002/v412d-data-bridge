#!/usr/bin/env python3
"""FIN within-sleeve multi-paper month-end — thin wrapper over MultiPaperMonitorSpec."""
from __future__ import annotations

from ops_dual_paper_month_end import (
    MultiChallengerSpec,
    MultiPaperMonitorSpec,
    ROOT,
    cli_main_multi,
)

CHAL_RS = "FIN_RS_SOFT_TILT_EXDIV"
CHAL_MIX = "MIX_L75"
CHAL_KD = "KD_OPT"

SPEC = MultiPaperMonitorSpec(
    label="FIN_WITHIN_SLEEVE_MONTH_END_MONITOR",
    ops_stem="FIN_WITHIN_SLEEVE_MONTH_END_MONITOR",
    base_id="FIN_EQUAL",
    base_nav=ROOT
    / "repro/fin-within-sleeve-dual-paper-observe/outputs/base_fin_equal_daily_nav.csv",
    challengers=(
        MultiChallengerSpec(
            chal_id=CHAL_RS,
            slug="fin_rs_soft_tilt_exdiv",
            chal_nav=ROOT
            / "repro/fin-within-sleeve-dual-paper-observe/outputs/fin_rs_soft_tilt_exdiv_daily_nav.csv",
            design_giveback_pp={"heldout_2019_plus": 1.5, "sealed_2023_plus": 2.0},
        ),
        MultiChallengerSpec(
            chal_id=CHAL_MIX,
            slug="fin_mix_l75",
            chal_nav=ROOT
            / "repro/fin-within-sleeve-dual-paper-observe/outputs/fin_mix_l75_daily_nav.csv",
            design_giveback_pp={"heldout_2019_plus": 0.5, "sealed_2023_plus": 0.8},
        ),
        MultiChallengerSpec(
            chal_id=CHAL_KD,
            slug="fin_kd_opt",
            chal_nav=ROOT
            / "repro/fin-within-sleeve-dual-paper-observe/outputs/fin_kd_opt_daily_nav.csv",
            design_giveback_pp={"heldout_2019_plus": 0.5, "sealed_2023_plus": 0.8},
        ),
    ),
    default_out=ROOT / "repro/fin-within-sleeve-dual-paper-observe/month_end",
    ledger_hint="scripts/e16_fin_within_sleeve_dual_paper_ledgers.py",
    missing_msg="Missing FIN within-sleeve dual-paper NAVs.",
    legacy_rs_chal_id=CHAL_RS,
    extra_payload={
        "locked_id": CHAL_RS,
        "mix_id": CHAL_MIX,
        "kd_id": CHAL_KD,
        "kd_optimal_id": "KD_APR15_MAY15_Klt30_T15",
    },
    non_actions=(
        "OPERATING_OBSERVE — paper only",
        "No Soft-Frozen flip",
        "No live e21 FIN within-sleeve wire",
    ),
    md_footer=(
        "- Soft-Frozen KEEP · live FIN equal-split untouched · no cutover from this monitor",
    ),
)

if __name__ == "__main__":
    raise SystemExit(cli_main_multi(SPEC))
