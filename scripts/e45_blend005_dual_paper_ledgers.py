#!/usr/bin/env python3
"""E45 blend-α=0.05 dual-paper ledgers — thin wrapper over ops_dual_paper_ledgers."""
from __future__ import annotations

import e16_soft_frozen_base as soft_frozen
import e45_crisis_core as e45
from e45_paper_harness import BOOK_BASE, CLAIM_STATUS, E45_PROFILE_DEFAULT, ROOT
from ops_dual_paper_ledgers import (
    DualPaperLedgerSpec,
    LedgerResult,
    cli_main,
    prepare_e45_exposure_pair,
    standard_metric_table,
    utc_now,
    write_json_md_pair,
)

OUT = ROOT / "repro/e45-blend005-dual-paper-observe"
RESEARCH = ROOT / "research/e45"
BASE_ID = BOOK_BASE
CHAL_ID = "BLEND_E45_A05"
ALPHA = 0.05


def prepare(market, dividends):
    return prepare_e45_exposure_pair(
        market,
        dividends,
        alpha=ALPHA,
        exposure_csv_name="blend_e45_a05_exposure.csv",
        exposure_series_name="e45_blend_a05_exposure",
    )


def report(result: LedgerResult) -> None:
    held, sealed = result.held, result.sealed or {}
    payload = {
        "generated_at_utc": utc_now(),
        "label": "E45_BLEND005_DUAL_PAPER_OBSERVE_SLEEVE",
        "status": "OPERATING_OBSERVE",
        "live_wire": False,
        "soft_frozen_default_unchanged": True,
        "stitch_authorized": False,
        "cutover_authorized": False,
        "ballot": "E45 OPEN blend-α=0.05 observe",
        "base_id": BASE_ID,
        "locked_challenger": CHAL_ID,
        "blend_alpha": ALPHA,
        "e45_profile": E45_PROFILE_DEFAULT,
        "claim_status": CLAIM_STATUS,
        "primary_comparable_mdd": e45.PRIMARY_COMPARABLE_MDD,
        "current_live_clip": {
            "financial_lo": soft_frozen.SOFT_FROZEN_FIN_LO,
            "financial_hi": soft_frozen.SOFT_FROZEN_FIN_HI,
        },
        "exact_t1": {
            "base": result.books[BASE_ID]["exact_t1_ok"],
            "blend_e45_a05": result.books[CHAL_ID]["exact_t1_ok"],
        },
        "books": result.books,
        "heldout_delta_vs_base": held,
        "sealed_delta_vs_base": sealed,
        "ops_checklist": [
            "Keep Soft-Frozen live default = BASE until a separate stitch / cutover PR",
            "Run BASE + BLEND_E45_A05 paper ledgers in parallel with month-end monitor",
            "Re-check YTD / trailing_1y PAUSE gates each month-end (observe ≠ promote)",
            "Do not silent-edit Soft-Frozen; do not rewrite forward/e21 history",
            "Observe sleeve ≠ stitch license",
        ],
        "non_goals": [
            "Auto live-wire / stitch from this observe sleeve",
            "Soft-Frozen clip flip",
            "DEFAULT books flip away from E22_v2s_tw",
        ],
    }
    lines = [
        "# E45 Blend-α=0.05 Dual-Paper Observe Sleeve",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Status: **OPERATING OBSERVE** — Soft-Frozen live default **unchanged**; live stitch **FORBIDDEN**.",
        "",
        f"- **{BASE_ID}** ∥ **{CHAL_ID}** (α={ALPHA})",
        "",
        *standard_metric_table(result.books),
        "",
        f"Held-out: MDD {held.get('mdd_improve_pp')} pp · giveback {held.get('cagr_giveback_pp')} pp",
        f"Sealed: MDD {sealed.get('mdd_improve_pp')} pp · giveback {sealed.get('cagr_giveback_pp')} pp",
        "",
        "`E45_BLEND005_DUAL_PAPER_OBSERVE_SLEEVE`",
        "",
    ]
    write_json_md_pair(
        out_dir=OUT,
        report_stem="e45_blend005_dual_paper_observe",
        payload=payload,
        md_lines=lines,
        mirror_dirs=(RESEARCH,),
        mirror_stem="E45_BLEND005_DUAL_PAPER_OBSERVE",
    )


SPEC = DualPaperLedgerSpec(
    label="E45_BLEND005_DUAL_PAPER_OBSERVE_SLEEVE",
    out_dir=OUT,
    base_id=BASE_ID,
    chal_id=CHAL_ID,
    prepare=prepare,
    base_nav_name="base_e16_e18_e22_v2s_daily_nav.csv",
    chal_nav_name="blend_e45_a05_daily_nav.csv",
    compare_chal_col="nav_blend_e45_a05",
    compare_rel_col="rel_blend_vs_base",
    report_fn=report,
)

if __name__ == "__main__":
    raise SystemExit(cli_main(SPEC))
