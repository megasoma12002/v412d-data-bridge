#!/usr/bin/env python3
"""Sleeve-tilt dual-paper ledgers — thin wrapper over ops_dual_paper_ledgers."""
from __future__ import annotations

import pandas as pd

from e45_paper_harness import ROOT
from e50_early_stack_combined_nav import FIN, e16_features
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
from sleeve_tilt_helpers import (
    ALPHA,
    BASE_ID,
    CHAMPION_ID,
    HUMAN_OPEN,
    LIVE_KD,
    PRIOR_OBSERVE_ID,
    SIGNAL_SHORT,
    build_champion_target,
)
from within_sleeve_alloc import build_kd_season_tilt_scores, build_pre_exdiv_window_buy_ok

OUT = ROOT / "repro/sleeve-tilt-dual-paper-observe"
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
    kw = live_kd_sim_kwargs(scores=kd_scores, buy_ok=kd_ok)
    return PreparedBooks(
        base_target=target_live,
        base_regime=regime,
        chal_target=target_chal,
        chal_regime=regime,
        base_kwargs=kw,
        chal_kwargs=dict(kw),
        context={"alpha": ALPHA, "signal": SIGNAL_SHORT, "prior": PRIOR_OBSERVE_ID},
    )


def report(result: LedgerResult) -> None:
    held, sealed = result.held, result.sealed or {}
    payload = {
        "generated_at_utc": utc_now(),
        "label": "SLEEVE_LAYER_TILT_DUAL_PAPER_OBSERVE_OPERATING",
        "status": "OPERATING_OBSERVE",
        "live_wire": False,
        "soft_frozen_unchanged": True,
        "human_open": HUMAN_OPEN,
        "prior_observe_id": PRIOR_OBSERVE_ID,
        "books": [BASE_ID, CHAMPION_ID],
        "base_id": BASE_ID,
        "challenger_id": CHAMPION_ID,
        "sleeve_tilt": {"alpha": ALPHA, "signal": SIGNAL_SHORT},
        "heldout_vs_base": held,
        "sealed_vs_base": sealed,
        "soft_assist_observe": "KEEP_INDEPENDENT",
        "ops_auto_fuse": False,
        "cutover_blocked": True,
    }
    md = [
        "# Sleeve-tilt dual-paper (OPERATING OBSERVE)",
        "",
        f"Human: `{HUMAN_OPEN}` · Soft-assist independent · no fuse",
        f"Books: `{BASE_ID}` ∥ `{CHAMPION_ID}` (α={ALPHA}, {SIGNAL_SHORT})",
        f"Held-out score **{held.get('score')}** · Sealed **{sealed.get('score')}**",
        "",
        "```bash",
        "python3 scripts/e16_sleeve_tilt_dual_paper_ledgers.py",
        "```",
        "",
    ]
    write_json_md_pair(
        out_dir=OUT,
        report_stem="sleeve_tilt_dual_paper_observe",
        payload=payload,
        md_lines=md,
        mirror_dirs=(OPS,),
        mirror_stem="SLEEVE_LAYER_TILT_DUAL_PAPER_OBSERVE",
    )


SPEC = DualPaperLedgerSpec(
    label="SLEEVE_LAYER_TILT_DUAL_PAPER_OBSERVE_OPERATING",
    out_dir=OUT,
    base_id=BASE_ID,
    chal_id=CHAMPION_ID,
    prepare=prepare,
    base_nav_name="live_stack_daily_nav.csv",
    chal_nav_name="sleeve_rsi14_lt30_a0225_daily_nav.csv",
    write_fills=False,
    base_targets_name=None,
    soft_frozen_clip=(0.6, 0.9),
    preflight=preflight_live_kd(LIVE_KD),
    report_fn=report,
)

if __name__ == "__main__":
    raise SystemExit(cli_main(SPEC))
