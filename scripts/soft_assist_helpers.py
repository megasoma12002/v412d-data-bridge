#!/usr/bin/env python3
"""Shared Soft-assist score helpers (paper observe + research).

Stage A Soft-assist champion: ``SOFT_BOTH__BELOW_MA120__RSI6_GT80``
Prior operating observe (2026-09-11): ``SOFT_CHAMP_PLUS_K9_LT30_a10``
OPERATING observe challenger (2026-09-12 rule-path OPEN):
  ``SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a05``
  = buy soft ``BELOW_MA120@1`` + ``K9_LT30@1`` + sell soft ``RSI6_GT80@0.5``
  (Soft KD/BB sensitivity Stage A beat-champion buy; sell amp from SELL_a05 ballot;
   additive soft only — no hard AND).

``LIVE_KD`` must stay byte-equal to ``e21_forward_pipeline.KD_OPT`` season /
k_thresh / pre_days / active_score (live SSOT). Do not drift this copy without
updating live — prefer importing from live when wiring a shared module later.
"""
from __future__ import annotations

import pandas as pd

SOFT_BOOST = 1.0
SELL_SOFT_BOOST = 0.5  # operating SELL_a05 amplitude
# Mirror of live KD_OPT (e21_forward_pipeline.KD_OPT) — paper observe only.
LIVE_KD = {
    "season_start": (4, 15),
    "season_end": (5, 15),
    "k_thresh": 30.0,
    "pre_days": 15,
    "active_score": 1.5,
}
CHAMPION_ID = "SOFT_BOTH__BELOW_MA120__RSI6_GT80"
PRIOR_OBSERVE_ID = "SOFT_CHAMP_PLUS_K9_LT30_a10"
OBSERVE_CHAL_ID = "SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a05"
HUMAN_OPEN = "OPEN Soft-assist observe: SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a05"
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
    """Soft-assist Stage A champion buy soft only (``BELOW_MA120``)."""
    return soft_boost_scores(kd_scores, lows[BUY_LOW_ID], SOFT_BOOST)


def build_observe_sell_panel(highs: dict) -> pd.DataFrame:
    """OPERATING observe sell soft (``RSI6_GT80`` @ SELL_a05)."""
    return soft_sell_panel(highs[SELL_HIGH_ID], boost=SELL_SOFT_BOOST)
