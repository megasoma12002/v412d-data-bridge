#!/usr/bin/env python3
"""Shared starting capital for live + paper early-stack.

Restored **3_000_000** (human 2026-09-08: 「先復原成原3M時的條件版本」).

Note: under board-lot 1000 + equal name-split, Soft-Frozen TEL (~6%) often
cannot fund 1 張 per telecom name at 3M — see telecom within-sleeve research
(`TELECOM_WITHIN_SLEEVE_ALLOC_CHARTER.md`). Soft-Frozen clips unchanged.
"""
from __future__ import annotations

DEFAULT_CAPITAL = 3_000_000.0

__all__ = ["DEFAULT_CAPITAL"]
