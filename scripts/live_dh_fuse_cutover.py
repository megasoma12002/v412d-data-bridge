#!/usr/bin/env python3
"""Live FUSE_ADDITIVE cutover actuators (forward-only) + Soft sell amp.

Human ballots:
  2026-09-13 ``ACCEPT Live cutover: DH_dd06 + FUSE_ADDITIVE`` (DH later replaced by COOL)
  2026-09-26 ``ACCEPT Live cutover: SELL_a75 under COOL (keep FUSE+COOL)``

Live offense twin:
  Soft buy softs + Soft sell amp (live ``SELL_a75`` / boost 0.75) + Sleeve RSI14 α=0.225
  on Soft-Frozen clip + KD_OPT + TEL_EQUAL — then COOL_c8 exposure (defense).

Independent Soft-assist paper observe remains ``SELL_a05`` (boost 0.5).
"""
from __future__ import annotations

from typing import Any

import pandas as pd

import e22_dividend_accounting as e22div
import e45_defend_handoff_helpers as dh
import e45_defend_handoff_stagea_screen as stagea
from e50_early_stack_combined_nav import FIN, e16_features, simulate_core
from fuse_additive_helpers import FUSE_ID, SLEEVE_ALPHA, build_champion_target
from live_config import LIVE_FUSE_SOFT_SELL_BALLOT, LIVE_FUSE_SOFT_SELL_BOOST
from portfolio_capital import DEFAULT_CAPITAL
from sleeve_tilt_helpers import CHAMPION_ID as SLEEVE_ID
from soft_assist_helpers import (
    LIVE_KD,
    OBSERVE_CHAL_ID as SOFT_ID_A05,
    build_observe_buy_scores,
    build_observe_sell_panel,
)
from ta_indicator_catalog import build_low_high_catalog
from tw_share_lots import BOARD_LOT
from within_sleeve_alloc import (
    FIN_PRE_EXDIV_KD,
    TEL_EQUAL,
    build_kd_season_tilt_scores,
    build_pre_exdiv_window_buy_ok,
)

# Live FUSE Soft sell amp (SELL_a75) — coexists with COOL; independent Soft observe stays a05.
SOFT_ID = "SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a75"
SOFT_ID_PRIOR = SOFT_ID_A05
SELL_BOOST_LIVE = float(LIVE_FUSE_SOFT_SELL_BOOST)
HUMAN_ACCEPT_SELL_A75 = LIVE_FUSE_SOFT_SELL_BALLOT

HUMAN_ACCEPT = "ACCEPT Live cutover: DH_dd06 + FUSE_ADDITIVE"
LIVE_RECIPE_ID = "LIVE_FUSE_ADDITIVE_SELL_a75_COOL"
DH_ID = dh.CHAL_ID
DH_ALIAS = dh.CHAL_ALIAS


def _kd_panels(market: pd.DataFrame, dividends: pd.DataFrame):
    cal = pd.DatetimeIndex(pd.to_datetime(market["date"]).drop_duplicates().sort_values())
    kd = build_kd_season_tilt_scores(
        market,
        dividends,
        FIN,
        k_thresh=float(LIVE_KD["k_thresh"]),
        season_start=LIVE_KD["season_start"],
        season_end=LIVE_KD["season_end"],
        pre_days=int(LIVE_KD["pre_days"]),
        active_score=float(LIVE_KD["active_score"]),
    )
    buy_ok = build_pre_exdiv_window_buy_ok(
        cal,
        dividends,
        FIN,
        pre_days=int(LIVE_KD["pre_days"]),
        also_stock_ex=True,
    )
    lows, highs = build_low_high_catalog(market, cal, list(FIN))
    buy = build_observe_buy_scores(kd, lows)
    sell = build_observe_sell_panel(highs, boost=SELL_BOOST_LIVE)
    return kd, buy_ok, buy, sell


def build_fuse_offense_nav(
    market: pd.DataFrame, dividends: pd.DataFrame
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Paper-faithful FUSE_ADDITIVE offense book (no DH), Exact T+1.

    Pin E22 books to preserved cash-on-ex ``E22_v2s_tw_effex`` (not live Stage-E
    DEFAULT). Full-history DH/FUSE exposure must not fail-closed on blank
    historical ``payment_date`` rows that Stage-E recv_pay requires. Live day
    books still apply Stage-E via ``live_e22_day``.
    """
    _prices, sleeve, _target, regime = e16_features(market)
    _kd, buy_ok, buy, sell = _kd_panels(market, dividends)
    target = build_champion_target(market, sleeve, regime)
    nav, fills, meta = simulate_core(
        market,
        target,
        regime,
        dividends,
        apply_e22=True,
        e22_version=e22div.PRESERVED_CASH_ON_EX,
        apply_stock_div=True,
        capital=float(DEFAULT_CAPITAL),
        lot_size=int(BOARD_LOT),
        financial_alloc=FIN_PRE_EXDIV_KD,
        telecom_alloc=TEL_EQUAL,
        fin_name_scores=buy,
        fin_buy_ok=buy_ok,
        fin_sell_scores=sell,
    )
    if not bool(meta.get("exact_t1_ok")):
        raise RuntimeError("FUSE offense exact_t1_ok failed")
    return nav, {
        "fuse_id": FUSE_ID,
        "soft_id": SOFT_ID,
        "soft_id_prior_observe": SOFT_ID_PRIOR,
        "soft_sell_boost": float(SELL_BOOST_LIVE),
        "sleeve_id": SLEEVE_ID,
        "sleeve_alpha": float(SLEEVE_ALPHA),
        "n_fills": int(len(fills)),
        "dh_id": DH_ID,
        "e22_books_version": e22div.PRESERVED_CASH_ON_EX,
    }


def build_dh_exposure_from_offense(
    market: pd.DataFrame, offense_nav: pd.DataFrame
) -> pd.Series:
    nav_s = stagea._nav_series(offense_nav)
    feat = stagea._risk_features(market, nav_s)
    dates = pd.DatetimeIndex(nav_s.index)
    return stagea._build_exposure(
        dates, feat, float(dh.DD_THRESHOLD), float(dh.VOL_Z_THRESHOLD)
    )


def fuse_soft_panels_for_asof(
    market: pd.DataFrame, dividends: pd.DataFrame, asof: pd.Timestamp
) -> tuple[dict[str, float] | None, dict[str, bool] | None, dict[str, float] | None]:
    """Today's FIN soft buy scores / KD buy_ok / soft sell scores for live orders."""
    _kd, buy_ok, buy, sell = _kd_panels(market, dividends)
    asof = pd.Timestamp(asof).normalize()
    scores = None
    if asof in buy.index:
        scores = {
            c: float(buy.loc[asof, c])
            for c in FIN
            if c in buy.columns and pd.notna(buy.loc[asof, c])
        }
    ok = None
    if asof in buy_ok.index:
        ok = {c: bool(buy_ok.loc[asof, c]) for c in FIN if c in buy_ok.columns}
    sell_scores = None
    if asof in sell.index:
        sell_scores = {
            c: float(sell.loc[asof, c])
            for c in FIN
            if c in sell.columns and pd.notna(sell.loc[asof, c])
        }
    return scores, ok, sell_scores


def fuse_target_for_market(market: pd.DataFrame) -> pd.DataFrame:
    """Sleeve RSI champion target path used by live FUSE_ADDITIVE."""
    _prices, sleeve, _target, regime = e16_features(market)
    return build_champion_target(market, sleeve, regime)


def dh_exposure_today(
    market: pd.DataFrame, dividends: pd.DataFrame, asof: pd.Timestamp
) -> tuple[float, dict[str, Any]]:
    """Causal DH exposure on FUSE offense NAV for asof (paper-faithful MENU3)."""
    asof = pd.Timestamp(asof).normalize()
    nav, meta = build_fuse_offense_nav(market, dividends)
    exp = build_dh_exposure_from_offense(market, nav)
    if asof in exp.index and pd.notna(exp.loc[asof]):
        today = float(exp.loc[asof])
    else:
        today = float(exp.dropna().iloc[-1]) if exp.dropna().size else 1.0
    meta = {
        **meta,
        "asof": asof.date().isoformat(),
        "dh_exposure": today,
        "dh_defense_frac": float((exp < 0.999).mean()),
        "shrink": float(dh.SHRINK),
        "dd_threshold": float(dh.DD_THRESHOLD),
        "vol_z_threshold": float(dh.VOL_Z_THRESHOLD),
        "human_accept": HUMAN_ACCEPT,
        "live_recipe_id": LIVE_RECIPE_ID,
    }
    return today, meta
