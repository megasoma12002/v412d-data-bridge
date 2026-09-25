#!/usr/bin/env python3
"""Soft-assist dual-paper ledgers — thin wrapper over ops_dual_paper_ledgers."""
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
from portfolio_capital import DEFAULT_CAPITAL
from soft_assist_helpers import (
    BUY_LOW_ID,
    BUY_SOFT_EXTRA,
    HUMAN_OPEN,
    LIVE_KD,
    OBSERVE_CHAL_ID,
    PRIOR_OBSERVE_ID,
    SELL_HIGH_ID,
    SELL_SOFT_BOOST,
    SOFT_BOOST,
    build_observe_buy_scores,
    soft_sell_panel,
)
from ta_indicator_catalog import build_low_high_catalog
from tw_share_lots import BOARD_LOT
from within_sleeve_alloc import build_kd_season_tilt_scores, build_pre_exdiv_window_buy_ok

OUT = ROOT / "repro/soft-assist-dual-paper-observe"
OPS = ROOT / "research/ops"
BASE_ID = "LIVE_KD_OPT"
CHAL_ID = OBSERVE_CHAL_ID
CHAL_NAV_NAME = "soft_champ_plus_k9_lt30_a10_sell_a05_daily_nav.csv"


def prepare(market, dividends) -> PreparedBooks:
    _p, _s, target, regime = e16_features(market)
    cal = pd.DatetimeIndex(pd.to_datetime(market["date"]).drop_duplicates().sort_values())
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
    soft_sell = soft_sell_panel(highs[SELL_HIGH_ID], boost=SELL_SOFT_BOOST)
    return PreparedBooks(
        base_target=target,
        base_regime=regime,
        chal_target=target,
        chal_regime=regime,
        base_kwargs=live_kd_sim_kwargs(scores=kd_scores, buy_ok=kd_ok),
        chal_kwargs=live_kd_sim_kwargs(
            scores=soft_scores, buy_ok=kd_ok, sell_scores=soft_sell
        ),
        context={
            "buy_soft_desc": "+".join(
                [f"{BUY_LOW_ID}@{SOFT_BOOST:g}"] + [f"{a}@{b:g}" for a, b in BUY_SOFT_EXTRA]
            ),
        },
    )


def report(result: LedgerResult) -> None:
    held, sealed = result.held, result.sealed or {}
    buy_soft_desc = result.prepared.context.get("buy_soft_desc", "")
    payload = {
        "generated_at_utc": utc_now(),
        "label": "SOFT_ASSIST_DUAL_PAPER_OBSERVE_OPERATING",
        "status": "OPERATING_OBSERVE",
        "live_wire": False,
        "soft_frozen_unchanged": True,
        "human_open": HUMAN_OPEN,
        "prior_observe_id": PRIOR_OBSERVE_ID,
        "books": [BASE_ID, CHAL_ID],
        "capital": float(DEFAULT_CAPITAL),
        "lot_size": int(BOARD_LOT),
        "base_id": BASE_ID,
        "challenger_id": CHAL_ID,
        "soft_assist": {
            "buy_low_id": BUY_LOW_ID,
            "buy_soft_extra": [{"id": a, "boost": b} for a, b in BUY_SOFT_EXTRA],
            "buy_soft_desc": buy_soft_desc,
            "sell_high_id": SELL_HIGH_ID,
            "buy_boost": SOFT_BOOST,
            "sell_boost": SELL_SOFT_BOOST,
        },
        "heldout_vs_base": held,
        "sealed_vs_base": sealed,
        "fills": {
            BASE_ID: int(len(result.fills_base)),
            CHAL_ID: int(len(result.fills_chal)),
        },
        "default_status": "KEEP_OBSERVE",
        "cutover_blocked": True,
    }
    md = [
        "# Soft-assist dual-paper (OPERATING OBSERVE)",
        "",
        f"Status: `OPERATING_OBSERVE` · paper only · Soft-Frozen KEEP · live wire false",
        f"Human: `{HUMAN_OPEN}`",
        f"Books: `{BASE_ID}` ∥ `{CHAL_ID}`",
        f"Buy soft: `{buy_soft_desc}` · sell soft: `{SELL_HIGH_ID}@{SELL_SOFT_BOOST:g}`",
        "",
        f"Held-out score **{held.get('score')}** · Sealed score **{sealed.get('score')}**",
        "",
        "```bash",
        "python3 scripts/e16_soft_assist_dual_paper_ledgers.py",
        "```",
        "",
    ]
    write_json_md_pair(
        out_dir=OUT,
        report_stem="soft_assist_dual_paper_observe",
        payload=payload,
        md_lines=md,
        mirror_dirs=(OPS,),
        mirror_stem="SOFT_ASSIST_DUAL_PAPER_OBSERVE",
    )
    # Preserve historical ops MD alias used by alert/docs consumers.
    (OPS / "SOFT_ASSIST_DUAL_PAPER_OBSERVE_OPERATING.md").write_text(
        "\n".join(md) + "\n", encoding="utf-8"
    )


SPEC = DualPaperLedgerSpec(
    label="SOFT_ASSIST_DUAL_PAPER_OBSERVE_OPERATING",
    out_dir=OUT,
    base_id=BASE_ID,
    chal_id=CHAL_ID,
    prepare=prepare,
    base_nav_name="live_kd_opt_daily_nav.csv",
    chal_nav_name=CHAL_NAV_NAME,
    write_fills=False,
    base_targets_name=None,
    soft_frozen_clip=(0.6, 0.8),
    preflight=preflight_live_kd(LIVE_KD, refuse_soft_assist_leak=True),
    report_fn=report,
)

if __name__ == "__main__":
    raise SystemExit(cli_main(SPEC))
