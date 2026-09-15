#!/usr/bin/env python3
"""FIN_CAP_50 dual-paper ledgers — thin wrapper over ops_dual_paper_ledgers."""
from __future__ import annotations

from pathlib import Path

import e22_dividend_accounting as e22div
import pandas as pd
from e16_fin_cap_oof_challenger import e16_features_fin_cap
from e45_paper_harness import ROOT, WINDOWS_STANDARD
from e50_early_stack_combined_nav import ALL, e16_features
from ops_dual_paper_ledgers import (
    DualPaperLedgerSpec,
    LedgerResult,
    PreparedBooks,
    cli_main,
    utc_now,
    write_json_md_pair,
)

OUT = ROOT / "repro/fincap50-dual-paper"
GAPS = ROOT / "research/gaps"
MARKET_PATH = ROOT / "forward/e21/live_market.csv"
DIV_PATH = ROOT / "data/dividend_events/e22_dividend_events.csv"
FIN_CAP_50 = {"fin_lo": 0.35, "fin_hi": 0.50}
WINDOWS = {
    k: WINDOWS_STANDARD[k]
    for k in ("full", "oof_2011_2018", "heldout_2019_plus", "sealed_2023_plus")
}


def load_market_complete() -> pd.DataFrame:
    market = pd.read_csv(MARKET_PATH, dtype={"code": str})
    market["date"] = pd.to_datetime(market["date"])
    required = set(ALL + ["TAIEX"])
    complete = market.groupby("date")["code"].apply(lambda s: required.issubset(set(s)))
    return market[market["date"].isin(complete[complete].index)].sort_values(["date", "code"])


def load_div() -> pd.DataFrame:
    return pd.read_csv(DIV_PATH, dtype={"code": str}) if DIV_PATH.exists() else pd.DataFrame()


def prepare(market, dividends) -> PreparedBooks:
    _p, _s, base_target, base_regime = e16_features(market)
    _p2, _s2, cap_target, cap_regime = e16_features_fin_cap(
        market, FIN_CAP_50["fin_lo"], FIN_CAP_50["fin_hi"]
    )
    return PreparedBooks(
        base_target=base_target,
        base_regime=base_regime,
        chal_target=cap_target,
        chal_regime=cap_regime,
        base_kwargs={},
        chal_kwargs={},
    )


def report(result: LedgerResult) -> None:
    held = result.held
    payload = {
        "generated_at_utc": utc_now(),
        "label": "FIN_CAP_50_DUAL_PAPER_LEDGERS",
        "status": "PROMOTE_PROPOSAL_SUPPORT",
        "live_wire": False,
        "soft_frozen_default_unchanged": True,
        "authoritative_go_live_status": "NOT_READY_SEALED_CAGR",
        "base_id": "BASE_E16",
        "challenger_id": "FIN_CAP_50",
        "books": result.books,
        "heldout_delta_vs_base": held,
        "cutover_blocked": True,
    }
    lines = [
        "# FIN_CAP_50 Dual-Paper Ledgers",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Status: **PROMOTE PROPOSAL SUPPORT** — Soft-Frozen unchanged · go-live NOT_READY_SEALED_CAGR",
        "",
        f"Held-out MDD improve **{held.get('mdd_improve_pp')} pp** · giveback **{held.get('cagr_giveback_pp')} pp**",
        "",
    ]
    write_json_md_pair(
        out_dir=OUT,
        report_stem="fincap50_dual_paper",
        payload=payload,
        md_lines=lines,
        mirror_dirs=(GAPS,),
        mirror_stem="FIN_CAP_50_DUAL_PAPER",
    )


SPEC = DualPaperLedgerSpec(
    label="FIN_CAP_50_DUAL_PAPER_LEDGERS",
    out_dir=OUT,
    base_id="BASE_E16",
    chal_id="FIN_CAP_50",
    prepare=prepare,
    base_nav_name="base_e16_daily_nav.csv",
    chal_nav_name="fincap50_daily_nav.csv",
    compare_chal_col="nav_fincap50",
    compare_rel_col="rel_fincap50_vs_base",
    base_targets_name="base_e16_targets.csv",
    chal_targets_name="fincap50_targets.csv",
    e22_version=e22div.E22_V2S,
    windows=WINDOWS,
    load_market_fn=load_market_complete,
    load_dividends_fn=load_div,
    report_fn=report,
    status="PROMOTE_PROPOSAL_SUPPORT",
)

if __name__ == "__main__":
    raise SystemExit(cli_main(SPEC))
