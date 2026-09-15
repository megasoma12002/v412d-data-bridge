#!/usr/bin/env python3
"""FINCAP BLEND_025 dual-paper ledgers — thin wrapper over ops_dual_paper_ledgers."""
from __future__ import annotations

import e22_dividend_accounting as e22div
import pandas as pd
from e16_fin_cap_oof_challenger import e16_features_fin_cap
from e45_paper_harness import ROOT, WINDOWS_STANDARD
from e50_early_stack_combined_nav import ALL, e16_features
from fincap_sealed_cagr_improve_diag import blend_targets
from ops_dual_paper_ledgers import (
    DualPaperLedgerSpec,
    LedgerResult,
    PreparedBooks,
    cli_main,
    utc_now,
    write_json_md_pair,
)

OUT = ROOT / "repro/blend025-dual-paper"
GAPS = ROOT / "research/gaps"
MARKET_PATH = ROOT / "forward/e21/live_market.csv"
DIV_PATH = ROOT / "data/dividend_events/e22_dividend_events.csv"
LOCKED_ID = "BLEND_025"
BLEND_ALPHA = 0.25
FIN_CAP_50 = {"fin_lo": 0.35, "fin_hi": 0.50}


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
    _p2, _s2, fin50_target, _ = e16_features_fin_cap(
        market, FIN_CAP_50["fin_lo"], FIN_CAP_50["fin_hi"]
    )
    blend_target = blend_targets(base_target, fin50_target, BLEND_ALPHA)
    return PreparedBooks(
        base_target=base_target,
        base_regime=base_regime,
        chal_target=blend_target,
        chal_regime=base_regime,
    )


def report(result: LedgerResult) -> None:
    held, sealed = result.held, result.sealed or {}
    payload = {
        "generated_at_utc": utc_now(),
        "label": "BLEND_025_DUAL_PAPER_LEDGERS",
        "status": "OPERATING_OBSERVE",
        "live_wire": False,
        "soft_frozen_default_unchanged": True,
        "locked_id": LOCKED_ID,
        "blend_alpha": BLEND_ALPHA,
        "books": result.books,
        "heldout_delta_vs_base": held,
        "sealed_delta_vs_base": sealed,
        "cutover_blocked": True,
    }
    lines = [
        "# FINCAP BLEND_025 Dual-Paper Ledgers",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Locked: **{LOCKED_ID}** (α={BLEND_ALPHA})",
        f"Held-out score **{held.get('score')}** · Sealed **{sealed.get('score')}**",
        "",
    ]
    write_json_md_pair(
        out_dir=OUT,
        report_stem="blend025_dual_paper",
        payload=payload,
        md_lines=lines,
        mirror_dirs=(GAPS,),
        mirror_stem="BLEND_025_DUAL_PAPER",
    )


SPEC = DualPaperLedgerSpec(
    label="BLEND_025_DUAL_PAPER_LEDGERS",
    out_dir=OUT,
    base_id="BASE_E16",
    chal_id=LOCKED_ID,
    prepare=prepare,
    base_nav_name="base_e16_daily_nav.csv",
    chal_nav_name="blend025_daily_nav.csv",
    compare_chal_col="nav_blend025",
    compare_rel_col="rel_blend025_vs_base",
    base_targets_name="base_e16_targets.csv",
    chal_targets_name="blend025_targets.csv",
    e22_version=e22div.E22_V2S,
    load_market_fn=load_market_complete,
    load_dividends_fn=load_div,
    report_fn=report,
)

if __name__ == "__main__":
    raise SystemExit(cli_main(SPEC))
