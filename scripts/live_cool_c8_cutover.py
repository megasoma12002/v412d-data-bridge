#!/usr/bin/env python3
"""Live COOL_c8_f50_d21 cutover actuators (forward-only).

Human ballot (2026-09-25):
  ``ACCEPT Live cutover: COOL_c8_f50_d21 (replace DH, keep FUSE)``

Live stack becomes MENU3 twin with PROXY circuit replacing DH_dd06:
  Soft observe softs + Sleeve RSI14 tilt α=0.225 + COOL_c8 exposure
  on Soft-Frozen clip + KD_OPT + TEL_EQUAL.

Does **not** stack with DH — DH live flag must stay False.
"""
from __future__ import annotations

from typing import Any

import pandas as pd

import e45_defend_handoff_stagea_screen as stagea
import live_dh_fuse_cutover as fuse_cut
from cool_c8_proxy_observe_helpers import (
    CHAL_ID,
    COOL,
    EXIT_X,
    FLOOR,
    MAX_DWELL,
    PROXY_X,
    build_cool_c8_exposure,
)

HUMAN_ACCEPT = "ACCEPT Live cutover: COOL_c8_f50_d21 (replace DH, keep FUSE)"
LIVE_RECIPE_ID = "LIVE_COOL_c8_f50_d21_FUSE_ADDITIVE"
COOL_ID = CHAL_ID
STACKING_POLICY = "REPLACE_DH_KEEP_FUSE"


def build_cool_exposure_from_offense(
    market: pd.DataFrame, offense_nav: pd.DataFrame
) -> pd.Series:
    nav_s = stagea._nav_series(offense_nav)
    feat = stagea._risk_features(market, nav_s)
    dates = pd.DatetimeIndex(nav_s.index)
    return build_cool_c8_exposure(dates, feat["proxy_mdd63"])


def cool_exposure_today(
    market: pd.DataFrame, dividends: pd.DataFrame, asof: pd.Timestamp
) -> tuple[float, dict[str, Any]]:
    """Causal COOL exposure on FUSE offense NAV for asof (paper-faithful)."""
    asof = pd.Timestamp(asof).normalize()
    nav, meta = fuse_cut.build_fuse_offense_nav(market, dividends)
    exp = build_cool_exposure_from_offense(market, nav)
    if asof in exp.index and pd.notna(exp.loc[asof]):
        today = float(exp.loc[asof])
    else:
        today = float(exp.dropna().iloc[-1]) if exp.dropna().size else 1.0
    meta = {
        **meta,
        "asof": asof.date().isoformat(),
        "cool_exposure": today,
        "cool_defense_frac": float((exp < 0.999).mean()),
        "proxy_x": float(PROXY_X),
        "floor": float(FLOOR),
        "exit_x": float(EXIT_X),
        "max_dwell": int(MAX_DWELL),
        "cool": int(COOL),
        "cool_id": COOL_ID,
        "stacking_policy": STACKING_POLICY,
        "human_accept": HUMAN_ACCEPT,
        "live_recipe_id": LIVE_RECIPE_ID,
        "dh_replaced": True,
    }
    return today, meta
