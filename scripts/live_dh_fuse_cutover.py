#!/usr/bin/env python3
"""Live DH_dd06 + FUSE_ADDITIVE cutover actuators (forward-only).

Human ballot (2026-09-13):
  ``ACCEPT Live cutover: DH_dd06 + FUSE_ADDITIVE``

Live stack becomes MENU3 paper twin:
  Soft observe softs + Sleeve RSI14 tilt α=0.225 + DH_dd06 exposure
  on Soft-Frozen clip + KD_OPT + TEL_EQUAL.

"""
from __future__ import annotations

from typing import Any

import pandas as pd

import e45_defend_handoff_helpers as dh
import e45_defend_handoff_stagea_screen as stagea
from e50_early_stack_combined_nav import FIN, e16_features, simulate_core
from fuse_additive_helpers import FUSE_ID, SLEEVE_ALPHA, build_champion_target
from portfolio_capital import DEFAULT_CAPITAL
from sleeve_tilt_helpers import CHAMPION_ID as SLEEVE_ID
from soft_assist_helpers import (
    LIVE_KD,
    OBSERVE_CHAL_ID as SOFT_ID,
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

HUMAN_ACCEPT = "ACCEPT Live cutover: DH_dd06 + FUSE_ADDITIVE"
LIVE_RECIPE_ID = "LIVE_DH_dd06_FUSE_ADDITIVE"
DH_ID = dh.CHAL_ID
DH_ALIAS = dh.CHAL_ALIAS


def _kd_panels(market: pd.DataFrame, dividends: pd.DataFrame):
    from live_config import LIVE

    fin = list(FIN)
    kd_src = LIVE_KD
    if LIVE.live_fin_priv_native:
        from live_priv_native_cutover import PRIV_FIN

        fin = list(PRIV_FIN)
        kd_src = LIVE.priv_kd
    cal = pd.DatetimeIndex(pd.to_datetime(market["date"]).drop_duplicates().sort_values())
    kd = build_kd_season_tilt_scores(
        market,
        dividends,
        fin,
        k_thresh=float(kd_src["k_thresh"]),
        season_start=kd_src["season_start"],
        season_end=kd_src["season_end"],
        pre_days=int(kd_src["pre_days"]),
        active_score=float(kd_src["active_score"]),
    )
    buy_ok = build_pre_exdiv_window_buy_ok(
        cal,
        dividends,
        fin,
        pre_days=int(kd_src["pre_days"]),
        also_stock_ex=True,
    )
    lows, highs = build_low_high_catalog(market, cal, list(fin))
    buy = build_observe_buy_scores(kd, lows)
    sell = build_observe_sell_panel(highs)
    return kd, buy_ok, buy, sell


def build_fuse_offense_nav(
    market: pd.DataFrame, dividends: pd.DataFrame
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Paper-faithful FUSE_ADDITIVE offense book (no DH), Exact T+1."""
    _prices, sleeve, _target, regime = e16_features(market)
    _kd, buy_ok, buy, sell = _kd_panels(market, dividends)
    target = build_champion_target(market, sleeve, regime)
    nav, fills, meta = simulate_core(
        market,
        target,
        regime,
        dividends,
        apply_e22=True,
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
        "sleeve_id": SLEEVE_ID,
        "sleeve_alpha": float(SLEEVE_ALPHA),
        "n_fills": int(len(fills)),
        "dh_id": DH_ID,
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
    from live_config import LIVE

    fin = list(FIN)
    if LIVE.live_fin_priv_native:
        from live_priv_native_cutover import PRIV_FIN

        fin = list(PRIV_FIN)
    _kd, buy_ok, buy, sell = _kd_panels(market, dividends)
    asof = pd.Timestamp(asof).normalize()
    scores = None
    if asof in buy.index:
        scores = {
            c: float(buy.loc[asof, c])
            for c in fin
            if c in buy.columns and pd.notna(buy.loc[asof, c])
        }
    ok = None
    if asof in buy_ok.index:
        ok = {c: bool(buy_ok.loc[asof, c]) for c in fin if c in buy_ok.columns}
    sell_scores = None
    if asof in sell.index:
        sell_scores = {
            c: float(sell.loc[asof, c])
            for c in fin
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
