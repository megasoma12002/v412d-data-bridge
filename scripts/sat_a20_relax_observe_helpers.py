#!/usr/bin/env python3
"""SAT_A20_RELAX dual-paper observe helpers (tip-first densify α=0.20 H=5).

Paper only · Soft-Frozen KEEP · live CONF α=0.10 KEEP · COMPOSITE observe KEEP · cutover BLOCKED.
Books: CTRL_LIVE_A10 ∥ SAT_A20_RELAX
"""
from __future__ import annotations

BASE_ID = "CTRL_LIVE_A10"
CHAL_ID = "SAT_A20_RELAX"
OFF_CODE = "00631L"
BASE_ALPHA = 0.10
CHAL_ALPHA = 0.20
HOLD_H = 5
CONFIRM = "RET3"
STATUS = "OPERATING_OBSERVE"
STAGE_A_VERDICT = "SAT_RELAX_HIT"
HUMAN_OPEN = (
    "OPEN paper observe: SAT_A20_RELAX (Stage A SAT_RELAX_HIT · tip-first densify)"
)
HUMAN_ACCEPT_LIVE = (
    "ACCEPT Live densify: SAT_A20_RELAX (flip live CONF α 0.10→0.20 — dedicated ACCEPT)"
)
