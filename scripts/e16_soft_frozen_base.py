#!/usr/bin/env python3
"""Soft-Frozen E16 BASE sleeve — single source of truth for live + research.

Live Financial clip: **[0.50, 0.95]** (Soft-Frozen). Do not edit these bounds
without an explicit human cutover PR. Challenger clips belong in
`e16_fin_cap_oof_challenger` only.

Both `e21_forward_pipeline.features` and `e50_early_stack_combined_nav.e16_features`
must call `build_soft_frozen_targets` so clip/prior/blend cannot drift apart.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# Universe (TW ETF sleeve membership) — keep identical across live/research.
FIN = ["2880", "2886", "2892", "5880"]
TEL = ["2412", "3045", "4904"]
SLEEVE_COLS = ["Financial", "Telecom", "0050"]

# Soft-Frozen live clip bounds (authoritative).
SOFT_FROZEN_FIN_LO = 0.50
SOFT_FROZEN_FIN_HI = 0.95
SOFT_FROZEN_TEL_LO = 0.03
SOFT_FROZEN_TEL_HI = 0.35
SOFT_FROZEN_ETF_LO = 0.00
SOFT_FROZEN_ETF_HI = 0.35
# Canonical list form for JSON / monitors (import this — do not re-type 0.50/0.95).
SOFT_FROZEN_FIN_CLIP = [SOFT_FROZEN_FIN_LO, SOFT_FROZEN_FIN_HI]

# Causal blend / rebalance threshold (shared).
START_WEIGHTS = np.array([0.90, 0.10, 0.00], dtype=float)
BLEND_OLD = 0.75
BLEND_NEW = 0.25
REBALANCE_L1_MIN = 0.02

REGIME_PRIORS = {
    "Bull": np.array([0.85, 0.05, 0.10], dtype=float),
    "Crisis": np.array([0.60, 0.35, 0.05], dtype=float),
    "Bear": np.array([0.70, 0.25, 0.05], dtype=float),
    "Sideways": np.array([0.85, 0.10, 0.05], dtype=float),
}


def apply_soft_frozen_clips(cand: np.ndarray) -> np.ndarray:
    """Project sleeve weights onto Soft-Frozen box ∩ simplex (sum=1).

    Plain clip-then-divide can push Financial **below** 0.50 (e.g. clip to
    [0.50, 0.35, 0.35] → renormalize → FIN≈0.417). Iterate a bounded
    projection so live targets cannot leave the Soft-Frozen envelope.
    """
    lo = np.array(
        [SOFT_FROZEN_FIN_LO, SOFT_FROZEN_TEL_LO, SOFT_FROZEN_ETF_LO], dtype=float
    )
    hi = np.array(
        [SOFT_FROZEN_FIN_HI, SOFT_FROZEN_TEL_HI, SOFT_FROZEN_ETF_HI], dtype=float
    )
    out = np.clip(np.asarray(cand, dtype=float).copy(), lo, hi)
    for _ in range(64):
        s = float(out.sum())
        if s <= 0:
            return START_WEIGHTS.copy()
        out = out / s
        clipped = np.clip(out, lo, hi)
        if np.allclose(out, clipped, atol=1e-12, rtol=0.0):
            if abs(float(clipped.sum()) - 1.0) <= 1e-10:
                return clipped
        gap = 1.0 - float(clipped.sum())
        free = (clipped > lo + 1e-15) & (clipped < hi - 1e-15)
        if free.any() and abs(gap) > 1e-12:
            clipped = clipped.copy()
            clipped[free] += gap / float(free.sum())
            out = np.clip(clipped, lo, hi)
            continue
        # No free coordinate: push the gap onto a bound that can still move.
        out = clipped.copy()
        if abs(gap) <= 1e-12:
            return out
        if gap > 0:
            can_up = out < hi - 1e-15
            if not can_up.any():
                return START_WEIGHTS.copy()
            i = int(np.where(can_up)[0][0])
            out[i] = min(hi[i], out[i] + gap)
        else:
            can_down = out > lo + 1e-15
            if not can_down.any():
                return START_WEIGHTS.copy()
            i = int(np.where(can_down)[0][0])
            out[i] = max(lo[i], out[i] + gap)
    # Last resort: authoritative start weights (known in-envelope).
    return START_WEIGHTS.copy()


def build_soft_frozen_targets(market: pd.DataFrame):
    """Causal Soft-Frozen E16 target history from adj_close panel.

    Returns
    -------
    prices : DataFrame
        adj_close pivot (date × code), ffilled.
    sleeve : DataFrame
        daily sleeve returns Financial / Telecom / 0050.
    target : DataFrame
        Soft-Frozen target weights (clipped to live bands).
    regime : Series
        Bull / Bear / Crisis / Sideways.
    score : DataFrame
        sleeve score used by the router (for diagnostics).
    """
    prices = (
        market.pivot(index="date", columns="code", values="adj_close")
        .sort_index()
        .ffill()
    )
    rets = prices.pct_change(fill_method=None).fillna(0.0)
    sleeve = pd.DataFrame(
        {
            "Financial": rets[FIN].mean(axis=1),
            "Telecom": rets[TEL].mean(axis=1),
            "0050": rets["0050"],
        }
    )
    taiex = prices["TAIEX"]
    tr = taiex.pct_change()
    ma = taiex.rolling(200).mean()
    vol = tr.rolling(20).std() * np.sqrt(252)
    dd = taiex / taiex.rolling(252, min_periods=120).max() - 1.0
    regime = pd.Series("Sideways", index=prices.index)
    regime[(taiex > ma) & (vol < 0.25)] = "Bull"
    regime[taiex < ma] = "Bear"
    regime[(vol > 0.35) | (dd < -0.15)] = "Crisis"

    nav = (1.0 + sleeve).cumprod()
    m20 = nav / nav.shift(20) - 1.0
    m60 = nav / nav.shift(60) - 1.0
    sv = sleeve.rolling(20).std() * np.sqrt(252)
    d60 = nav / nav.rolling(60, min_periods=20).max() - 1.0

    def _z(x: pd.DataFrame) -> pd.DataFrame:
        return x.sub(x.mean(axis=1), axis=0).div(
            x.std(axis=1).replace(0.0, np.nan), axis=0
        ).fillna(0.0)

    score = 0.35 * _z(m20) + 0.35 * _z(m60) - 0.20 * _z(sv) + 0.10 * _z(d60)

    out = []
    cur = START_WEIGHTS.copy()
    for i, _dt in enumerate(prices.index):
        pri = REGIME_PRIORS[str(regime.iloc[i])]
        cand = np.maximum(pri + 0.10 * np.clip(score.iloc[i].to_numpy(), -2.0, 2.0), 0.0)
        cand = apply_soft_frozen_clips(cand)
        desired = BLEND_OLD * cur + BLEND_NEW * cand
        if float(np.abs(desired - cur).sum()) >= REBALANCE_L1_MIN:
            cur = desired
        out.append(cur.copy())

    target = pd.DataFrame(out, index=prices.index, columns=["Financial", "Telecom", "0050"])
    return prices, sleeve, target, regime, score
