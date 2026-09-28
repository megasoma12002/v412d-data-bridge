#!/usr/bin/env python3
"""FIN buy-quality A/B/C multi-paper ledgers — OPERATING OBSERVE (paper only).

BASE_LIVE_FUSE_COOL ∥ A_SEED_MA120 ∥ B_MA120_OR_K9 ∥ C_OR_K9_AND_BELOW_MA60
Soft-Frozen KEEP · Exact T+1 KEEP · COOL_c8 KEEP · no live wire · cutover BLOCKED.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

import e16_clip_search_challenger as clip
import e16_soft_frozen_base as soft
import e22_dividend_accounting as e22div
import e45_defend_handoff_stagea_screen as stagea
from cool_c8_proxy_observe_helpers import build_cool_c8_exposure
from e45_paper_harness import ROOT
from e50_early_stack_combined_nav import FIN, e16_features, simulate_core
from fin_buy_quality_helpers import and_buy_ok, catalog_gate, or_and_exception, or_buy_ok
from fin_buy_quality_observe_helpers import (
    A_ID,
    B_ID,
    BASE_ID,
    C_ID,
    HUMAN_OPEN,
    PARENT_D_VERDICT,
    STAGE_A_VERDICT,
    STAGE_B_VERDICT,
    STAGE_C_VERDICT,
    STATUS,
)
from live_config import LIVE_FUSE_SOFT_SELL_BOOST
from ops_dual_paper_ledgers import (
    MultiChallengerLedgerBook,
    MultiLedgerResult,
    MultiPaperLedgerSpec,
    PreparedMultiBooks,
    cli_main_multi,
    live_kd_sim_kwargs,
    preflight_live_kd,
    utc_now,
    write_json_md_pair,
)
from portfolio_capital import DEFAULT_CAPITAL
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp
from sleeve_tilt_helpers import ALPHA as LIVE_SLEEVE_ALPHA, sleeve_signal_panel
from soft_assist_helpers import (
    BUY_LOW_ID,
    LIVE_KD,
    SELL_HIGH_ID,
    soft_boost_scores,
    soft_sell_panel,
)
from ta_indicator_catalog import build_low_high_catalog
from tw_share_lots import BOARD_LOT
from within_sleeve_alloc import (
    build_kd_season_tilt_scores,
    build_pre_exdiv_window_buy_ok,
)

OUT = ROOT / "repro/fin-buy-quality-dual-paper-observe"
OPS = ROOT / "research/ops"
E22_VERSION = e22div.DEFAULT_BOOKS_VERSION
SELL_AMP = float(LIVE_FUSE_SOFT_SELL_BOOST)
CAPITAL = float(DEFAULT_CAPITAL)
LOT = int(BOARD_LOT)


def _preflight() -> None:
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.8]
    preflight_live_kd(LIVE_KD)()


def _buy(kd, lows, k9_amp: float = 1.0) -> pd.DataFrame:
    out = soft_boost_scores(kd, lows[BUY_LOW_ID], 1.0)
    return soft_boost_scores(out, lows["K9_LT30"], float(k9_amp))


def _sell(highs, amp: float = SELL_AMP) -> pd.DataFrame:
    return soft_sell_panel(highs[SELL_HIGH_ID], boost=float(amp))


def _sleeve_score(market, sleeve, alpha: float) -> pd.DataFrame:
    _p, _s, _t, _r, base_score = soft.build_soft_frozen_targets(market)
    tilt = sleeve_signal_panel(sleeve, "rsi_lt30", 14)
    return base_score + float(alpha) * tilt


def _target_live(score, regime):
    return clip.build_targets_with_clips(
        regime=regime,
        score=score,
        fin_lo=float(soft.SOFT_FROZEN_FIN_LO),
        fin_hi=float(soft.SOFT_FROZEN_FIN_HI),
        tel_lo=float(soft.SOFT_FROZEN_TEL_LO),
        tel_hi=float(soft.SOFT_FROZEN_TEL_HI),
        etf_lo=float(soft.SOFT_FROZEN_ETF_LO),
        etf_hi=float(soft.SOFT_FROZEN_ETF_HI),
    )


def _cool_from_offense(market, offense_nav: pd.DataFrame) -> pd.Series:
    nav_s = stagea._nav_series(offense_nav)
    feat = stagea._risk_features(market, nav_s)
    dates = pd.DatetimeIndex(nav_s.index)
    return build_cool_c8_exposure(dates, feat["proxy_mdd63"])


def _held_score(base_stats: dict, chal_stats: dict) -> dict[str, Any]:
    mdd_pp = mdd_delta_pp(base_stats.get("max_drawdown"), chal_stats.get("max_drawdown"))
    cagr_pp = cagr_delta_pp(
        base_stats.get("cagr"), chal_stats.get("cagr"), missing_as_zero=True
    )
    giveback = abs(float(cagr_pp)) if cagr_pp is not None else 9.0
    return {
        "mdd_improve_pp": None if mdd_pp is None else round(float(mdd_pp), 4),
        "cagr_giveback_pp": None if cagr_pp is None else round(float(cagr_pp), 4),
        "cagr_lift_pp": None if cagr_pp is None else round(float(-float(cagr_pp)), 4),
        "score": None if mdd_pp is None else round(float(mdd_pp) - 0.5 * giveback, 4),
    }


def prepare(market: pd.DataFrame, dividends: pd.DataFrame) -> PreparedMultiBooks:
    _p, sleeve, _tgt, regime = e16_features(market)
    cal = pd.DatetimeIndex(pd.to_datetime(market["date"]).drop_duplicates().sort_values())
    lows, highs = build_low_high_catalog(market, cal, list(FIN))
    kd = build_kd_season_tilt_scores(
        market,
        dividends,
        list(FIN),
        k_thresh=float(LIVE_KD["k_thresh"]),
        season_start=LIVE_KD["season_start"],
        season_end=LIVE_KD["season_end"],
        pre_days=int(LIVE_KD["pre_days"]),
        active_score=float(LIVE_KD["active_score"]),
    )
    base_buy_ok = build_pre_exdiv_window_buy_ok(
        cal, dividends, list(FIN), pre_days=int(LIVE_KD["pre_days"]), also_stock_ex=True
    )
    scores = _buy(kd, lows)
    sell = _sell(highs)
    sleeve_sc = _sleeve_score(market, sleeve, LIVE_SLEEVE_ALPHA)
    target = _target_live(sleeve_sc, regime)

    print("offense NAV for cool ...", flush=True)
    off_kw = live_kd_sim_kwargs(scores=scores, buy_ok=base_buy_ok, sell_scores=sell)
    off_nav, _fills, _meta = simulate_core(
        market,
        target,
        regime,
        dividends,
        apply_e22=True,
        apply_stock_div=True,
        capital=CAPITAL,
        lot_size=LOT,
        e22_version=E22_VERSION,
        **off_kw,
    )
    cool = _cool_from_offense(market, off_nav)

    hard = catalog_gate(lows["BELOW_MA120"])
    a_extra = hard
    b_extra = or_buy_ok(hard, catalog_gate(lows["K9_LT30"]))
    c_extra = or_and_exception(
        hard, catalog_gate(lows["K9_LT30"]), catalog_gate(lows["BELOW_MA60"])
    )

    def _kw(buy_ok: pd.DataFrame) -> dict[str, Any]:
        return live_kd_sim_kwargs(
            scores=scores,
            buy_ok=buy_ok,
            sell_scores=sell,
            e45_exposure=cool.astype(float),
        )

    return PreparedMultiBooks(
        base_target=target,
        base_regime=regime,
        base_kwargs=_kw(base_buy_ok),
        challengers={
            A_ID: (target, regime, _kw(and_buy_ok(base_buy_ok, a_extra)), {}),
            B_ID: (target, regime, _kw(and_buy_ok(base_buy_ok, b_extra)), {}),
            C_ID: (target, regime, _kw(and_buy_ok(base_buy_ok, c_extra)), {}),
        },
        context={
            "cool_frac_defense": float((cool < 0.999).mean()),
            "filters": {
                A_ID: "BELOW_MA120",
                B_ID: "BELOW_MA120 OR K9_LT30",
                C_ID: "BELOW_MA120 OR (K9_LT30 AND BELOW_MA60)",
            },
        },
    )


def report(result: MultiLedgerResult) -> None:
    win_base = result.books[BASE_ID]["windows"]
    held_by: dict[str, Any] = {}
    sealed_by: dict[str, Any] = {}
    for cid in (A_ID, B_ID, C_ID):
        win_c = result.books[cid]["windows"]
        held_by[cid] = _held_score(
            win_base.get("heldout_2019_plus") or {},
            win_c.get("heldout_2019_plus") or {},
        )
        sealed_by[cid] = _held_score(
            win_base.get("sealed_2023_plus") or {},
            win_c.get("sealed_2023_plus") or {},
        )

    payload = {
        "generated_at_utc": utc_now(),
        "label": "FIN_BUY_QUALITY_DUAL_PAPER_OBSERVE_OPERATING",
        "human_open": HUMAN_OPEN,
        "status": STATUS,
        "live_wire": False,
        "cutover": "BLOCKED",
        "cutover_blocked": True,
        "soft_frozen_unchanged": True,
        "base_id": BASE_ID,
        "challengers": [A_ID, B_ID, C_ID],
        "stage_a_verdict": STAGE_A_VERDICT,
        "stage_b_verdict": STAGE_B_VERDICT,
        "stage_c_verdict": STAGE_C_VERDICT,
        "parent_d_verdict": PARENT_D_VERDICT,
        "filters": result.prepared.context.get("filters"),
        "cool_frac_defense": result.prepared.context.get("cool_frac_defense"),
        "books": result.books,
        "heldout_2019_plus": held_by,
        "sealed_2023_plus": sealed_by,
        "non_actions": [
            "paper observe only",
            "no Soft-Frozen clip flip",
            "no tip history rewrite",
            "no live buy-quality wire without dedicated Class D ACCEPT",
        ],
    }
    md = [
        "# FIN buy-quality A/B/C multi-paper observe — OPERATING",
        "",
        f"- human_open: `{HUMAN_OPEN}`",
        f"- status: **{STATUS}** · live_wire: false · cutover: **BLOCKED**",
        f"- books: `{BASE_ID}` ∥ `{A_ID}` ∥ `{B_ID}` ∥ `{C_ID}`",
        f"- Stage A `{STAGE_A_VERDICT}` · B `{STAGE_B_VERDICT}` · C `{STAGE_C_VERDICT}` · D `{PARENT_D_VERDICT}`",
        f"- A held CAGRΔ {held_by[A_ID].get('cagr_lift_pp')}pp · MDD↑ {held_by[A_ID].get('mdd_improve_pp')}pp",
        f"- B held CAGRΔ {held_by[B_ID].get('cagr_lift_pp')}pp · MDD↑ {held_by[B_ID].get('mdd_improve_pp')}pp",
        f"- C held CAGRΔ {held_by[C_ID].get('cagr_lift_pp')}pp · MDD↑ {held_by[C_ID].get('mdd_improve_pp')}pp",
        "- (CAGRΔ = chal−base; Stage packs printed base−chal as the numeric CAGR column)",
        "",
        "## Non-actions",
        "",
    ]
    md += [f"- {x}" for x in payload["non_actions"]]
    md += ["", "Repro: `repro/fin-buy-quality-dual-paper-observe/`", ""]

    write_json_md_pair(
        out_dir=OUT,
        report_stem="FIN_BUY_QUALITY_DUAL_PAPER_OBSERVE_OPERATING",
        payload=payload,
        md_lines=md,
        mirror_dirs=(OPS,),
    )
    # Alias stem used by ops pack / alert scan peers
    text = (OUT / "reports/FIN_BUY_QUALITY_DUAL_PAPER_OBSERVE_OPERATING.json").read_text(
        encoding="utf-8"
    )
    (OPS / "FIN_BUY_QUALITY_DUAL_PAPER_OBSERVE.json").write_text(text, encoding="utf-8")


SPEC = MultiPaperLedgerSpec(
    label="FIN_BUY_QUALITY_DUAL_PAPER_OBSERVE_OPERATING",
    out_dir=OUT,
    base_id=BASE_ID,
    base_nav_name="base_live_fuse_cool_daily_nav.csv",
    prepare=prepare,
    challengers=(
        MultiChallengerLedgerBook(
            chal_id=A_ID,
            nav_name="a_seed_ma120_daily_nav.csv",
            compare_col="nav_a_seed_ma120",
        ),
        MultiChallengerLedgerBook(
            chal_id=B_ID,
            nav_name="b_ma120_or_k9_daily_nav.csv",
            compare_col="nav_b_ma120_or_k9",
        ),
        MultiChallengerLedgerBook(
            chal_id=C_ID,
            nav_name="c_or_k9_and_below_ma60_daily_nav.csv",
            compare_col="nav_c_or_k9_and_below_ma60",
        ),
    ),
    write_fills=False,
    base_targets_name=None,
    soft_frozen_clip=(0.6, 0.8),
    e22_version=E22_VERSION,
    preflight=_preflight,
    report_fn=report,
    status=STATUS,
    capital=CAPITAL,
    lot_size=LOT,
)


if __name__ == "__main__":
    raise SystemExit(cli_main_multi(SPEC))
