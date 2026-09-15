#!/usr/bin/env python3
"""E45 blend-α=0.25 dual-paper ledgers — thin wrapper (observe archived 2026-09-13)."""
from __future__ import annotations

import e16_soft_frozen_base as soft_frozen
import e45_crisis_core as e45
from e45_paper_harness import BOOK_BASE, BOOK_BLEND_A25, CLAIM_STATUS, E45_PROFILE_DEFAULT, ROOT
from ops_dual_paper_ledgers import (
    DualPaperLedgerSpec,
    LedgerResult,
    cli_main,
    prepare_e45_exposure_pair,
    standard_metric_table,
    utc_now,
    write_json_md_pair,
)

OUT = ROOT / "repro/e45-blend025-dual-paper-observe"
RESEARCH = ROOT / "research/e45"
BASE_ID = BOOK_BASE
CHAL_ID = BOOK_BLEND_A25
ALPHA = 0.25


def prepare(market, dividends):
    return prepare_e45_exposure_pair(
        market,
        dividends,
        alpha=ALPHA,
        exposure_csv_name="blend_e45_a25_exposure.csv",
        exposure_series_name="e45_blend_a25_exposure",
    )


def report(result: LedgerResult) -> None:
    held, sealed = result.held, result.sealed or {}
    payload = {
        "generated_at_utc": utc_now(),
        "label": "E45_BLEND025_DUAL_PAPER_OBSERVE_SLEEVE",
        "status": "ARCHIVED_OBSERVE",
        "archived": True,
        "live_wire": False,
        "soft_frozen_default_unchanged": True,
        "stitch_authorized": False,
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
        "books": result.books,
        "heldout_delta_vs_base": held,
        "sealed_delta_vs_base": sealed,
    }
    lines = [
        "# E45 Blend-α=0.25 Dual-Paper Observe (ARCHIVED)",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Status: **ARCHIVED OBSERVE** (2026-09-13) — Soft-Frozen unchanged; stitch FORBIDDEN.",
        "",
        *standard_metric_table(result.books),
        "",
        "`E45_BLEND025_DUAL_PAPER_OBSERVE_SLEEVE`",
        "",
    ]
    write_json_md_pair(
        out_dir=OUT,
        report_stem="e45_blend025_dual_paper_observe",
        payload=payload,
        md_lines=lines,
        mirror_dirs=(RESEARCH,),
        mirror_stem="E45_BLEND025_DUAL_PAPER_OBSERVE",
    )


SPEC = DualPaperLedgerSpec(
    label="E45_BLEND025_DUAL_PAPER_OBSERVE_SLEEVE",
    out_dir=OUT,
    base_id=BASE_ID,
    chal_id=CHAL_ID,
    prepare=prepare,
    base_nav_name="base_e16_e18_e22_v2s_daily_nav.csv",
    chal_nav_name="blend_e45_a25_daily_nav.csv",
    compare_chal_col="nav_blend_e45_a25",
    compare_rel_col="rel_blend_vs_base",
    status="ARCHIVED_OBSERVE",
    report_fn=report,
)

if __name__ == "__main__":
    raise SystemExit(cli_main(SPEC))
