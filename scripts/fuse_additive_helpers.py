#!/usr/bin/env python3
"""Soft×Sleeve FUSE_ADDITIVE paper-observe helpers.

OPERATING fuse observe (2026-09-12 ballot OPEN):
  ``FUSE_ADDITIVE`` = Soft observe softs (buy+sell) + Sleeve observe RSI14 tilt α=0.225
  on ``LIVE_STACK`` in one ``simulate_core`` book.

Third paper track beside Soft-assist and Sleeve-tilt observes.
Does **not** auto-fuse the two independent observes into live.
Live Soft-Frozen / KD / TEL / Soft / Sleeve wires remain unchanged.
"""
from __future__ import annotations

from soft_assist_helpers import (
    LIVE_KD,
    OBSERVE_CHAL_ID as SOFT_OBSERVE_ID,
    build_observe_buy_scores,
    build_observe_sell_panel,
)
from sleeve_tilt_helpers import (
    ALPHA as SLEEVE_ALPHA,
    CHAMPION_ID as SLEEVE_OBSERVE_ID,
    build_champion_target,
)

BASE_ID = "LIVE_STACK"
FUSE_ID = "FUSE_ADDITIVE"
HUMAN_OPEN = "OPEN Soft×Sleeve fuse observe: FUSE_ADDITIVE"
STATUS = "OPERATING_OBSERVE"
EVIDENCE = "research/ops/SOFT_SLEEVE_PAPER_FUSE_STAGEA_SCREEN.md"
