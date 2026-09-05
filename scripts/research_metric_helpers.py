#!/usr/bin/env python3
"""Small helpers for research NAV deltas — never treat 0.0 as missing via `or`."""
from __future__ import annotations


def abs_mdd(x: float | None, default: float = 9.0) -> float:
    """abs(MDD); None → default. 0.0 is a valid MDD."""
    return abs(default if x is None else float(x))


def cagr_value(x: float | None, default: float | None = 0.0) -> float | None:
    """Return CAGR; None → default (may itself be None to preserve missing)."""
    if x is None:
        return default
    return float(x)


def mdd_delta_pp(
    base_mdd: float | None,
    other_mdd: float | None,
    *,
    missing_default: float = 9.0,
) -> float:
    """BASE |MDD| − OTHER |MDD| in percentage points."""
    return (abs_mdd(base_mdd, missing_default) - abs_mdd(other_mdd, missing_default)) * 100.0


def cagr_delta_pp(
    base_cagr: float | None,
    other_cagr: float | None,
    *,
    missing_as_zero: bool = False,
) -> float | None:
    """BASE CAGR − OTHER CAGR in percentage points.

    If either side is None and missing_as_zero is False → None.
    If missing_as_zero is True → treat None as 0.0 (legacy scorers).
    """
    if base_cagr is None or other_cagr is None:
        if not missing_as_zero:
            return None
        b = 0.0 if base_cagr is None else float(base_cagr)
        o = 0.0 if other_cagr is None else float(other_cagr)
        return (b - o) * 100.0
    return (float(base_cagr) - float(other_cagr)) * 100.0
