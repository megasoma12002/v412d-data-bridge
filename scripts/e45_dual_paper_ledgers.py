#!/usr/bin/env python3
"""E45 dual-paper ledgers — thin wrapper over ops_dual_paper_ledgers (α=1.0 full)."""
from __future__ import annotations

from pathlib import Path

import e16_soft_frozen_base as soft_frozen
import e45_crisis_core as e45
from e45_paper_harness import BOOK_BASE, BOOK_FULL, CLAIM_STATUS, E45_PROFILE_DEFAULT, ROOT
from ops_dual_paper_ledgers import (
    DualPaperLedgerSpec,
    LedgerResult,
    cli_main,
    prepare_e45_exposure_pair,
    standard_metric_table,
    utc_now,
    write_json_md_pair,
)

OUT = ROOT / "repro/e45-dual-paper-observe"
RESEARCH = ROOT / "research/e45"
BASE_ID = BOOK_BASE
CHAL_ID = BOOK_FULL


def prepare(market, dividends):
    return prepare_e45_exposure_pair(
        market,
        dividends,
        alpha=1.0,
        exposure_csv_name="chal_e45_e3_exposure.csv",
        exposure_series_name="e45_e3_exposure",
    )


def report(result: LedgerResult) -> None:
    held, sealed = result.held, result.sealed or {}
    payload = {
        "generated_at_utc": utc_now(),
        "label": "E45_DUAL_PAPER_OBSERVE_SLEEVE",
        "status": "OPERATING_OBSERVE",
        "live_wire": False,
        "soft_frozen_default_unchanged": True,
        "stitch_authorized": False,
        "cutover_authorized": False,
        "ballot": "E45 OPEN dual-paper observe",
        "base_id": BASE_ID,
        "locked_challenger": CHAL_ID,
        "e45_profile": E45_PROFILE_DEFAULT,
        "claim_status": CLAIM_STATUS,
        "primary_comparable_mdd": e45.PRIMARY_COMPARABLE_MDD,
        "current_live_clip": {
            "financial_lo": soft_frozen.SOFT_FROZEN_FIN_LO,
            "financial_hi": soft_frozen.SOFT_FROZEN_FIN_HI,
        },
        "exact_t1": {
            "base": result.books[BASE_ID]["exact_t1_ok"],
            "chal_e45_e3": result.books[CHAL_ID]["exact_t1_ok"],
        },
        "books": result.books,
        "heldout_delta_vs_base": held,
        "sealed_delta_vs_base": sealed,
        "ops_checklist": [
            "Keep Soft-Frozen live default = BASE until a separate stitch / cutover PR",
            "Run BASE + CHAL_E45_E3 paper ledgers in parallel with month-end monitor",
            "Re-check YTD / trailing_1y PAUSE gates each month-end (observe ≠ promote)",
            "Do not silent-edit Soft-Frozen; do not rewrite forward/e21 history",
            "Observe sleeve ≠ stitch license; second human stitch ACCEPT still required",
            "Never cite the retired handoff MDD narrative; use dated lineage / challenger MDDs only",
        ],
        "non_goals": [
            "Auto live-wire / four-layer stitch from this observe sleeve",
            "Soft-Frozen clip flip",
            "DEFAULT books flip away from E22_v2s_tw",
            "Invent replacement for retired MDD narrative",
        ],
    }
    lines = [
        "# E45 Dual-Paper Observe Sleeve",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Status: **OPERATING OBSERVE** — Soft-Frozen live default **unchanged**; live stitch **FORBIDDEN**.",
        "",
        "## Locked paper books",
        "",
        f"- **{BASE_ID}**: Soft-Frozen early-stack Exact T+1",
        f"- **{CHAL_ID}**: same stack + full E45 `{E45_PROFILE_DEFAULT}` exposure",
        f"- Retired MDD narrative: **`{CLAIM_STATUS}`** (do not cite)",
        "",
        "## Dual paper metrics",
        "",
        *standard_metric_table(result.books),
        "",
        f"Held-out vs BASE: MDD improve **{held.get('mdd_improve_pp')} pp**; "
        f"CAGR giveback **{held.get('cagr_giveback_pp')} pp**.",
        f"Sealed vs BASE: MDD improve **{sealed.get('mdd_improve_pp')} pp**; "
        f"CAGR giveback **{sealed.get('cagr_giveback_pp')} pp**.",
        "",
        "## Label",
        "",
        "`E45_DUAL_PAPER_OBSERVE_SLEEVE`",
        "",
    ]
    write_json_md_pair(
        out_dir=OUT,
        report_stem="e45_dual_paper_observe",
        payload=payload,
        md_lines=lines,
        mirror_dirs=(RESEARCH,),
        mirror_stem="E45_DUAL_PAPER_OBSERVE",
    )


SPEC = DualPaperLedgerSpec(
    label="E45_DUAL_PAPER_OBSERVE_SLEEVE",
    out_dir=OUT,
    base_id=BASE_ID,
    chal_id=CHAL_ID,
    prepare=prepare,
    base_nav_name="base_e16_e18_e22_v2s_daily_nav.csv",
    chal_nav_name="chal_e45_e3_daily_nav.csv",
    compare_chal_col="nav_chal_e45_e3",
    compare_rel_col="rel_chal_vs_base",
    report_fn=report,
)

if __name__ == "__main__":
    raise SystemExit(cli_main(SPEC))
