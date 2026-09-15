#!/usr/bin/env python3
"""FUSE_ADDITIVE dual-paper ledgers — thin wrapper over ops_dual_paper_ledgers."""
from __future__ import annotations

import pandas as pd

from e45_paper_harness import ROOT
from e50_early_stack_combined_nav import FIN, e16_features
from fuse_additive_helpers import (
    BASE_ID,
    FUSE_ID,
    HUMAN_OPEN,
    LIVE_KD,
    SLEEVE_ALPHA,
    SLEEVE_OBSERVE_ID,
    SOFT_OBSERVE_ID,
    STATUS,
    build_champion_target,
    build_observe_buy_scores,
    build_observe_sell_panel,
)
from ops_dual_paper_ledgers import (
    DualPaperLedgerSpec,
    LedgerResult,
    PreparedBooks,
    cli_main,
    live_kd_sim_kwargs,
    preflight_live_kd,
    utc_now,
    write_json_md_pair,
)
from ta_indicator_catalog import build_low_high_catalog
from within_sleeve_alloc import build_kd_season_tilt_scores, build_pre_exdiv_window_buy_ok

OUT = ROOT / "repro/fuse-additive-dual-paper-observe"
OPS = ROOT / "research/ops"


def prepare(market, dividends) -> PreparedBooks:
    _prices, sleeve, target_live, regime = e16_features(market)
    cal = pd.DatetimeIndex(pd.to_datetime(market["date"]).drop_duplicates().sort_values())
    target_chal = build_champion_target(market, sleeve, regime)
    kd_scores = build_kd_season_tilt_scores(
        market,
        dividends,
        FIN,
        k_thresh=float(LIVE_KD["k_thresh"]),
        season_start=LIVE_KD["season_start"],
        season_end=LIVE_KD["season_end"],
        pre_days=int(LIVE_KD["pre_days"]),
        active_score=float(LIVE_KD["active_score"]),
    )
    kd_ok = build_pre_exdiv_window_buy_ok(
        cal, dividends, FIN, pre_days=int(LIVE_KD["pre_days"]), also_stock_ex=True
    )
    lows, highs = build_low_high_catalog(market, cal, list(FIN))
    soft_scores = build_observe_buy_scores(kd_scores, lows)
    soft_sell = build_observe_sell_panel(highs)
    return PreparedBooks(
        base_target=target_live,
        base_regime=regime,
        chal_target=target_chal,
        chal_regime=regime,
        base_kwargs=live_kd_sim_kwargs(scores=kd_scores, buy_ok=kd_ok),
        chal_kwargs=live_kd_sim_kwargs(
            scores=soft_scores, buy_ok=kd_ok, sell_scores=soft_sell
        ),
        context={
            "soft_observe_id": SOFT_OBSERVE_ID,
            "sleeve_observe_id": SLEEVE_OBSERVE_ID,
            "sleeve_alpha": SLEEVE_ALPHA,
        },
    )


def report(result: LedgerResult) -> None:
    held, sealed = result.held, result.sealed or {}
    payload = {
        "generated_at_utc": utc_now(),
        "label": "FUSE_ADDITIVE_DUAL_PAPER_OBSERVE_OPERATING",
        "status": STATUS,
        "live_wire": False,
        "soft_frozen_unchanged": True,
        "human_open": HUMAN_OPEN,
        "books": [BASE_ID, FUSE_ID],
        "base_id": BASE_ID,
        "challenger_id": FUSE_ID,
        "soft_assist_observe": "KEEP_INDEPENDENT",
        "sleeve_tilt_observe": "KEEP_INDEPENDENT",
        "ops_auto_fuse": False,
        "heldout_vs_base": held,
        "sealed_vs_base": sealed,
        "cutover_blocked": True,
    }
    md = [
        "# FUSE_ADDITIVE dual-paper (OPERATING OBSERVE)",
        "",
        f"Human: `{HUMAN_OPEN}` · Soft∥Sleeve KEEP independent · ops auto-fuse FORBIDDEN",
        f"Books: `{BASE_ID}` ∥ `{FUSE_ID}`",
        f"Held-out score **{held.get('score')}** · Sealed **{sealed.get('score')}**",
        "",
        "```bash",
        "python3 scripts/e16_fuse_additive_dual_paper_ledgers.py",
        "```",
        "",
    ]
    write_json_md_pair(
        out_dir=OUT,
        report_stem="fuse_additive_dual_paper_observe",
        payload=payload,
        md_lines=md,
        mirror_dirs=(OPS,),
        mirror_stem="FUSE_ADDITIVE_DUAL_PAPER_OBSERVE",
    )


SPEC = DualPaperLedgerSpec(
    label="FUSE_ADDITIVE_DUAL_PAPER_OBSERVE_OPERATING",
    out_dir=OUT,
    base_id=BASE_ID,
    chal_id=FUSE_ID,
    prepare=prepare,
    base_nav_name="live_stack_daily_nav.csv",
    chal_nav_name="fuse_additive_daily_nav.csv",
    write_fills=False,
    base_targets_name=None,
    soft_frozen_clip=(0.6, 0.9),
    preflight=preflight_live_kd(LIVE_KD),
    report_fn=report,
    status=STATUS,
)

if __name__ == "__main__":
    raise SystemExit(cli_main(SPEC))
