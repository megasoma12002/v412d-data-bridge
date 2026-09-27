#!/usr/bin/env python3
"""Shared sleeve-gap → trade sizing (live tip + paper ``simulate_core``).

These constants are **not** Soft-Frozen ``REBALANCE_L1_MIN`` (router L1).
Do not unify ``SLEEVE_GAP_TRIGGER`` (0.015) with ``REBALANCE_L1_MIN`` (0.05).
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np

# Paper Exact T+1 + live rebalance order sizing (historical literals).
SLEEVE_GAP_TRIGGER = 0.015
SLEEVE_TRADE_SCALE = 0.75
SLEEVE_TRADE_L1_CAP = 0.20
CORE_SLEEVE_NAMES = ("Financial", "Telecom", "0050")


def sleeve_trade_vector(
    gap: Mapping[str, float],
    sleeve_names: Sequence[str],
    *,
    gap_trigger: float = SLEEVE_GAP_TRIGGER,
    trade_scale: float = SLEEVE_TRADE_SCALE,
    l1_cap: float = SLEEVE_TRADE_L1_CAP,
) -> np.ndarray:
    """Return trade fractions aligned to ``sleeve_names`` (may include DEF/OFF)."""
    trade = np.zeros(len(sleeve_names), dtype=float)
    if not gap:
        return trade
    if max(abs(float(v)) for v in gap.values()) >= float(gap_trigger):
        trade = np.array([float(gap[n]) for n in sleeve_names], dtype=float) * float(
            trade_scale
        )
        s = float(abs(trade).sum())
        if s > float(l1_cap):
            trade *= float(l1_cap) / s
    return trade


def sleeve_trade_from_gap(
    pre: Mapping[str, float],
    target: Mapping[str, float],
    *,
    sleeve_names: Sequence[str] = CORE_SLEEVE_NAMES,
    gap_trigger: float = SLEEVE_GAP_TRIGGER,
    trade_scale: float = SLEEVE_TRADE_SCALE,
    l1_cap: float = SLEEVE_TRADE_L1_CAP,
) -> tuple[dict[str, float], float]:
    """Core Soft sleeves gap → trade dict + L1 distance."""
    names = list(sleeve_names)
    gap = {k: float(target[k] - pre[k]) for k in pre}
    l1 = float(sum(abs(v) for v in gap.values()))
    trade = sleeve_trade_vector(
        gap,
        names,
        gap_trigger=gap_trigger,
        trade_scale=trade_scale,
        l1_cap=l1_cap,
    )
    return dict(zip(names, (float(x) for x in trade))), l1
