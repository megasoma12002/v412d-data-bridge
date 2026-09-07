#!/usr/bin/env python3
"""Shared starting capital for live + paper early-stack.

Sized so Soft-Frozen Telecom floor (3%) can still fund **3×1 張** at ~2026
telecom prices (~NT$100–140 → ~NT$357k for three board lots):

  357k / 0.03 ≈ 11.9M  → round up to **15_000_000**

Prior default 3M left TEL target (~6%) too small for any 1 張 after equal
name-split (board-lot 1000), so live telecom holdings went to zero.
"""
from __future__ import annotations

DEFAULT_CAPITAL = 15_000_000.0

__all__ = ["DEFAULT_CAPITAL"]
