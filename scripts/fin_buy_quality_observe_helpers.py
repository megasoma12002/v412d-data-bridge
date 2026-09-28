#!/usr/bin/env python3
"""FIN buy-quality A/B/C multi-paper observe helpers.

Paper only · Soft-Frozen KEEP · cutover BLOCKED · no live wire.
Books: BASE_LIVE_FUSE_COOL ∥ A_SEED_MA120 ∥ B_MA120_OR_K9 ∥ C_OR_K9_AND_BELOW_MA60
"""
from __future__ import annotations

BASE_ID = "BASE_LIVE_FUSE_COOL"
A_ID = "A_SEED_MA120"
B_ID = "B_MA120_OR_K9"
C_ID = "C_OR_K9_AND_BELOW_MA60"

BOOK_IDS = (BASE_ID, A_ID, B_ID, C_ID)

STATUS = "OPERATING_OBSERVE"
STAGE_A_VERDICT = "WIN_SOFT"
STAGE_B_VERDICT = "BUY_QUALITY_HIT"
STAGE_C_VERDICT = "HYBRID_PARETO"
PARENT_D_VERDICT = "PARENT_KEEP_B"

HUMAN_OPEN = "OPEN paper observe: FIN buy-quality A/B/C"
HUMAN_ACCEPT_LIVE = (
    "ACCEPT Live cutover: FIN buy-quality "
    "(requires dedicated Class D — not this observe ballot)"
)
