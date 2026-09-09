#!/usr/bin/env python3
"""Shared starting capital for live + paper early-stack.

Live capital **500_000_000** (human ACCEPT 2026-09-09: 「ACCEPT live capital 500M」).

Prior: 3M (2026-09-08 restore) ← 15M (2026-09-07) ← 3M.
Board-lot 1000 KEEP. Soft-Frozen clips unchanged.
See research/ops/CAPITAL_500M_2026-09-09.md.
"""
from __future__ import annotations

DEFAULT_CAPITAL = 500_000_000.0

__all__ = ["DEFAULT_CAPITAL"]
