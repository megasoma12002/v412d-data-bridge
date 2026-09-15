#!/usr/bin/env python3
"""E45 sleeve-local FIN_ONLY α=0.10 dual-paper ledgers — thin wrapper."""
from __future__ import annotations

from e45_paper_harness import (
    BOOK_BASE,
    CLAIM_STATUS,
    E45_PROFILE_DEFAULT,
    ROOT,
    SLEEVE_FIN_ONLY,
)
from ops_dual_paper_ledgers import (
    DualPaperLedgerSpec,
    LedgerResult,
    cli_main,
    prepare_e45_exposure_pair,
    standard_metric_table,
    utc_now,
    write_json_md_pair,
)

OUT = ROOT / "repro/e45-sleeve-local-dual-paper-observe"
RESEARCH = ROOT / "research/e45"
BASE_ID = BOOK_BASE
CHAL_ID = "SLEEVE_FIN_ONLY_A10"
ALPHA = 0.10


def prepare(market, dividends):
    return prepare_e45_exposure_pair(
        market,
        dividends,
        alpha=ALPHA,
        exposure_csv_name="sleeve_fin_only_a10_exposure.csv",
        exposure_series_name="e45_sleeve_fin_only_a10_exposure",
        e45_sleeve_names=SLEEVE_FIN_ONLY,
    )


def report(result: LedgerResult) -> None:
    held, sealed = result.held, result.sealed or {}
    payload = {
        "generated_at_utc": utc_now(),
        "label": "E45_SLEEVE_LOCAL_DUAL_PAPER_OBSERVE_SLEEVE",
        "status": "OPERATING_OBSERVE",
        "live_wire": False,
        "soft_frozen_default_unchanged": True,
        "stitch_authorized": False,
        "cutover_authorized": False,
        "ballot": "E45 ACCEPT OPEN sleeve-local observe",
        "base_id": BASE_ID,
        "locked_challenger": CHAL_ID,
        "blend_alpha": ALPHA,
        "e45_profile": E45_PROFILE_DEFAULT,
        "e45_sleeve_names": list(SLEEVE_FIN_ONLY),
        "claim_status": CLAIM_STATUS,
        "exact_t1": {
            "base": result.books[BASE_ID]["exact_t1_ok"],
            "sleeve_fin_only_a10": result.books[CHAL_ID]["exact_t1_ok"],
        },
        "books": result.books,
        "heldout_delta_vs_base": held,
        "sealed_delta_vs_base": sealed,
        "ops_checklist": [
            "Keep Soft-Frozen live default = BASE until a separate stitch / cutover PR",
            "Observe sleeve ≠ stitch license",
            "Leave FULL + A25 + A05 observe sleeves operating in parallel",
        ],
        "non_goals": [
            "Auto live-wire / stitch",
            "Soft-Frozen clip flip",
            "Retire FULL / A25 / A05 observe without separate ballot",
        ],
    }
    lines = [
        "# E45 Sleeve-Local FIN_ONLY α=0.10 Dual-Paper Observe Sleeve",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Status: **OPERATING OBSERVE** — Soft-Frozen unchanged; stitch FORBIDDEN.",
        "",
        f"- **{BASE_ID}** ∥ **{CHAL_ID}** sleeves={list(SLEEVE_FIN_ONLY)} α={ALPHA}",
        "",
        *standard_metric_table(result.books),
        "",
        f"Held-out score {held.get('score')} · Sealed score {sealed.get('score')}",
        "",
        "`E45_SLEEVE_LOCAL_DUAL_PAPER_OBSERVE_SLEEVE`",
        "",
    ]
    write_json_md_pair(
        out_dir=OUT,
        report_stem="e45_sleeve_local_dual_paper_observe",
        payload=payload,
        md_lines=lines,
        mirror_dirs=(RESEARCH,),
        mirror_stem="E45_SLEEVE_LOCAL_DUAL_PAPER_OBSERVE",
    )


SPEC = DualPaperLedgerSpec(
    label="E45_SLEEVE_LOCAL_DUAL_PAPER_OBSERVE_SLEEVE",
    out_dir=OUT,
    base_id=BASE_ID,
    chal_id=CHAL_ID,
    prepare=prepare,
    base_nav_name="base_e16_e18_e22_v2s_daily_nav.csv",
    chal_nav_name="sleeve_fin_only_a10_daily_nav.csv",
    compare_chal_col="nav_sleeve_fin_only_a10",
    compare_rel_col="rel_sleeve_vs_base",
    report_fn=report,
)

if __name__ == "__main__":
    raise SystemExit(cli_main(SPEC))
