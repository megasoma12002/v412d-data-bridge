#!/usr/bin/env python3
"""Shared Soft-assist score helpers (paper observe + research).

Stage A Soft-assist champion / prior observe: ``SOFT_BOTH__BELOW_MA120__RSI6_GT80``
OPERATING observe challenger (2026-09-11): ``SOFT_CHAMP_PLUS_K9_LT30_a10``
  = buy soft ``BELOW_MA120@1`` + ``K9_LT30@1`` + sell soft ``RSI6_GT80``
  (Soft KD/BB sensitivity Stage A beat-champion; additive soft only — no hard AND).

``LIVE_KD`` must stay byte-equal to ``e21_forward_pipeline.KD_OPT`` season /
k_thresh / pre_days / active_score (live SSOT). Do not drift this copy without
updating live — prefer importing from live when wiring a shared module later.
"""
from __future__ import annotations

import pandas as pd

SOFT_BOOST = 1.0
# Mirror of live KD_OPT (e21_forward_pipeline.KD_OPT) — paper observe only.
LIVE_KD = {
    "season_start": (4, 15),
    "season_end": (5, 15),
    "k_thresh": 30.0,
    "pre_days": 15,
    "active_score": 1.5,
}
CHAMPION_ID = "SOFT_BOTH__BELOW_MA120__RSI6_GT80"
PRIOR_OBSERVE_ID = CHAMPION_ID
OBSERVE_CHAL_ID = "SOFT_CHAMP_PLUS_K9_LT30_a10"
BUY_LOW_ID = "BELOW_MA120"
BUY_SOFT_EXTRA = (("K9_LT30", 1.0),)
SELL_HIGH_ID = "RSI6_GT80"


def soft_boost_scores(kd_scores: pd.DataFrame, panel: pd.DataFrame, boost: float) -> pd.DataFrame:
    p = panel.reindex(index=kd_scores.index, columns=kd_scores.columns).fillna(False)
    return kd_scores.astype(float) + float(boost) * p.astype(float)


def soft_sell_panel(
    high_panel: pd.DataFrame, *, base: float = 1.0, boost: float = 1.0
) -> pd.DataFrame:
    return float(base) + float(boost) * high_panel.astype(float)


def build_observe_buy_scores(kd_scores: pd.DataFrame, lows: dict) -> pd.DataFrame:
    """OPERATING observe buy softs (additive; never hard AND)."""
    out = soft_boost_scores(kd_scores, lows[BUY_LOW_ID], SOFT_BOOST)
    for lid, boost in BUY_SOFT_EXTRA:
        out = soft_boost_scores(out, lows[lid], float(boost))
    return out


def build_champion_buy_scores(kd_scores: pd.DataFrame, lows: dict) -> pd.DataFrame:
    """Prior Soft-assist champion buy soft only (``BELOW_MA120``)."""
    return soft_boost_scores(kd_scores, lows[BUY_LOW_ID], SOFT_BOOST)
