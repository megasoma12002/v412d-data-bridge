#!/usr/bin/env python3
"""Shared Sleeve-tilt observe helpers (paper only).

Champion: SLEEVE_BELOW_MA60_a01 — Soft-Frozen router score + 0.10 · 1{sleeve NAV < MA60}
then clip/blend. Within-sleeve stays LIVE KD_OPT + TEL_EQUAL. Soft-assist observe independent.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import e16_soft_frozen_base as soft
from soft_assist_helpers import LIVE_KD

CHAMPION_ID = "SLEEVE_BELOW_MA60_a01"
BASE_ID = "LIVE_STACK"
SIGNAL_SHORT = "BELOW_MA60"
ALPHA = 0.10
SIGN = 1.0
HUMAN_OPEN = "OPEN Sleeve-tilt observe: SLEEVE_BELOW_MA60_a01"


def rebuild_targets_from_score(score: pd.DataFrame, regime: pd.Series) -> pd.DataFrame:
    out = []
    cur = soft.START_WEIGHTS.copy()
    for i, _dt in enumerate(score.index):
        pri = soft.REGIME_PRIORS[str(regime.iloc[i])]
        cand = np.maximum(pri + 0.10 * np.clip(score.iloc[i].to_numpy(), -2.0, 2.0), 0.0)
        cand = soft.apply_soft_frozen_clips(cand)
        desired = soft.BLEND_OLD * cur + soft.BLEND_NEW * cand
        if float(np.abs(desired - cur).sum()) >= soft.REBALANCE_L1_MIN:
            cur = desired
        out.append(cur.copy())
    return pd.DataFrame(out, index=score.index, columns=["Financial", "Telecom", "0050"])


def sleeve_below_ma_panel(sleeve_rets: pd.DataFrame, window: int = 60) -> pd.DataFrame:
    nav = (1.0 + sleeve_rets.fillna(0.0)).cumprod()
    out = pd.DataFrame(0.0, index=sleeve_rets.index, columns=list(sleeve_rets.columns))
    min_p = max(20, window // 2)
    for col in sleeve_rets.columns:
        close = nav[col]
        ma = close.rolling(window, min_periods=min_p).mean()
        out[col] = (close < ma).astype(float)
    return out.fillna(0.0)


def build_champion_target(
    market: pd.DataFrame, sleeve: pd.DataFrame, regime: pd.Series
) -> pd.DataFrame:
    _p, _s, _t, _r, base_score = soft.build_soft_frozen_targets(market)
    tilt = sleeve_below_ma_panel(sleeve, window=60)
    new_score = base_score + float(SIGN) * float(ALPHA) * tilt
    return rebuild_targets_from_score(new_score, regime)
