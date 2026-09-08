#!/usr/bin/env python3
"""Shared starting capital for live + paper early-stack.

Human 2026-09-08: **「A接受 B 500m」** —
  A) live within-sleeve ``TEL_MIN_LOT_PACK``
  B) ``DEFAULT_CAPITAL = 500_000_000``

Soft-Frozen sleeve clips unchanged. Board-lot 1000 KEEP.
See `CAPITAL_500M_TEL_MINLOT_2026-09-08.md`.
"""
from __future__ import annotations

DEFAULT_CAPITAL = 500_000_000.0

__all__ = ["DEFAULT_CAPITAL"]
