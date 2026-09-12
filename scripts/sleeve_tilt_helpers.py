#!/usr/bin/env python3
"""Shared Sleeve-tilt observe helpers (paper only).

Prior seed observe: SLEEVE_BELOW_MA60_a01 — Soft-Frozen router + 0.10 · 1{sleeve NAV < MA60}
OPERATING observe (2026-09-12 rule-path OPEN): SLEEVE_RSI14_LT30_a0225
  — Soft-Frozen router + 0.225 · 1{sleeve RSI14 < 30} then clip/blend.

Within-sleeve stays LIVE KD_OPT + TEL_EQUAL. Soft-assist observe independent.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import e16_soft_frozen_base as soft
from soft_assist_helpers import LIVE_KD  # noqa: F401 — re-export for callers

PRIOR_OBSERVE_ID = "SLEEVE_BELOW_MA60_a01"
CHAMPION_ID = "SLEEVE_RSI14_LT30_a0225"
BASE_ID = "LIVE_STACK"
SIGNAL_SHORT = "RSI14_LT30"
SIGNAL_KIND = "rsi_lt30"
SIGNAL_WINDOW = 14
ALPHA = 0.225
SIGN = 1.0
HUMAN_OPEN = "OPEN Sleeve-tilt observe: SLEEVE_RSI14_LT30_a0225"


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


def sleeve_rsi_lt_panel(
    sleeve_rets: pd.DataFrame, window: int = 14, thresh: float = 30.0
) -> pd.DataFrame:
    """Causal sleeve-NAV RSI < thresh panel (matches tip-MDD / layer-tilt screens)."""
    nav = (1.0 + sleeve_rets.fillna(0.0)).cumprod()
    out = pd.DataFrame(0.0, index=sleeve_rets.index, columns=list(sleeve_rets.columns))
    for col in sleeve_rets.columns:
        close = nav[col]
        delta = close.diff()
        gain = delta.clip(lower=0.0)
        loss = (-delta).clip(lower=0.0)
        avg_gain = gain.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
        avg_loss = loss.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
        rs = avg_gain / avg_loss.replace(0.0, np.nan)
        rsi = 100.0 - (100.0 / (1.0 + rs))
        out[col] = (rsi < float(thresh)).astype(float)
    return out.fillna(0.0)


def sleeve_signal_panel(sleeve_rets: pd.DataFrame, kind: str, window: int) -> pd.DataFrame:
    if kind == "ma":
        return sleeve_below_ma_panel(sleeve_rets, window=window)
    if kind == "rsi_lt30":
        return sleeve_rsi_lt_panel(sleeve_rets, window=window, thresh=30.0)
    raise ValueError(kind)


def build_champion_target(
    market: pd.DataFrame, sleeve: pd.DataFrame, regime: pd.Series
) -> pd.DataFrame:
    _p, _s, _t, _r, base_score = soft.build_soft_frozen_targets(market)
    tilt = sleeve_signal_panel(sleeve, SIGNAL_KIND, SIGNAL_WINDOW)
    new_score = base_score + float(SIGN) * float(ALPHA) * tilt
    return rebuild_targets_from_score(new_score, regime)
