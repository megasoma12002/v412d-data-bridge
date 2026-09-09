#!/usr/bin/env python3
"""Soft-Frozen 4-sleeve challenger router — RESEARCH ONLY.

Sleeves: FinPub / FinPriv / Telecom / 0050 with independent clip boxes.
Does **not** edit live ``e16_soft_frozen_base`` constants.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import e16_soft_frozen_base as soft

PUB_R1 = ["2880", "2886", "2892", "5880"]
PRIV_R3R4 = ["2884", "2885", "2890", "2891", "2881", "2882"]
TEL = list(soft.TEL)
SLEEVE_COLS = ["FinPub", "FinPriv", "Telecom", "0050"]

# Live Soft-Frozen TEL/ETF clips (frozen for Stage A).
TEL_LO, TEL_HI = soft.SOFT_FROZEN_TEL_LO, soft.SOFT_FROZEN_TEL_HI
ETF_LO, ETF_HI = soft.SOFT_FROZEN_ETF_LO, soft.SOFT_FROZEN_ETF_HI

BLEND_OLD = soft.BLEND_OLD
BLEND_NEW = soft.BLEND_NEW
REBALANCE_L1_MIN = soft.REBALANCE_L1_MIN

# Legacy 3-sleeve regime priors (Financial, Telecom, 0050).
_LEGACY_PRIORS = soft.REGIME_PRIORS


def apply_clip_box(cand: np.ndarray, lo: np.ndarray, hi: np.ndarray, start: np.ndarray) -> np.ndarray:
    """Same projection family as Soft-Frozen / clip-search (box ∩ simplex)."""
    out = np.clip(np.asarray(cand, dtype=float).copy(), lo, hi)
    for _ in range(64):
        s = float(out.sum())
        if s <= 0:
            return start.copy()
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
        out = clipped.copy()
        if abs(gap) <= 1e-12:
            return out
        if gap > 0:
            can_up = out < hi - 1e-15
            if not can_up.any():
                return start.copy()
            i = int(np.where(can_up)[0][0])
            out[i] = min(hi[i], out[i] + gap)
        else:
            can_down = out > lo + 1e-15
            if not can_down.any():
                return start.copy()
            i = int(np.where(can_down)[0][0])
            out[i] = max(lo[i], out[i] + gap)
    return start.copy()


def split_prior(fin_tel_etf: np.ndarray, prior_priv_frac: float) -> np.ndarray:
    """Map legacy 3-vector prior → FinPub/FinPriv/Telecom/0050."""
    fin, tel, etf = (float(x) for x in fin_tel_etf)
    frac = float(prior_priv_frac)
    if frac < 0.0 or frac > 1.0:
        raise ValueError("prior_priv_frac must be in [0,1]")
    return np.array([fin * (1.0 - frac), fin * frac, tel, etf], dtype=float)


def build_4sleeve_targets(
    market: pd.DataFrame,
    *,
    fin_pub_lo: float,
    fin_pub_hi: float,
    fin_priv_lo: float,
    fin_priv_hi: float,
    prior_priv_frac: float,
    pub_codes: list[str] | None = None,
    priv_codes: list[str] | None = None,
):
    """Causal 4-sleeve targets; regime from TAIEX (same Soft-Frozen rules)."""
    pub = list(pub_codes or PUB_R1)
    priv = list(priv_codes or PRIV_R3R4)
    lo = np.array([fin_pub_lo, fin_priv_lo, TEL_LO, ETF_LO], dtype=float)
    hi = np.array([fin_pub_hi, fin_priv_hi, TEL_HI, ETF_HI], dtype=float)
    if float(lo.sum()) > 1.0 + 1e-12:
        raise ValueError(f"infeasible floors sum={lo.sum()}")
    start = apply_clip_box((lo + hi) / 2.0, lo, hi, split_prior(soft.START_WEIGHTS, prior_priv_frac))

    prices = (
        market.pivot(index="date", columns="code", values="adj_close")
        .sort_index()
        .ffill()
    )
    rets = prices.pct_change(fill_method=None).fillna(0.0)
    # Equal-weight sleeve returns within each membership.
    sleeve = pd.DataFrame(
        {
            "FinPub": rets[pub].mean(axis=1),
            "FinPriv": rets[priv].mean(axis=1) if priv else 0.0,
            "Telecom": rets[TEL].mean(axis=1),
            "0050": rets["0050"],
        },
        index=prices.index,
    )
    if not priv:
        sleeve["FinPriv"] = 0.0

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
    cur = start.copy()
    for i, _dt in enumerate(prices.index):
        pri = split_prior(_LEGACY_PRIORS[str(regime.iloc[i])], prior_priv_frac)
        cand = np.maximum(pri + 0.10 * np.clip(score.iloc[i].to_numpy(), -2.0, 2.0), 0.0)
        cand = apply_clip_box(cand, lo, hi, start)
        desired = BLEND_OLD * cur + BLEND_NEW * cand
        desired = apply_clip_box(desired, lo, hi, start)
        if float(np.abs(desired - cur).sum()) >= REBALANCE_L1_MIN:
            cur = desired
        out.append(cur.copy())

    target = pd.DataFrame(out, index=prices.index, columns=SLEEVE_COLS)
    return prices, sleeve, target, regime, score
