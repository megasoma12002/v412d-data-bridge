#!/usr/bin/env python3
"""FIN×SAT COMPOSITE dual-paper observe helpers.

Paper only · Soft-Frozen KEEP · SELL_a75 KEEP · live CONF α=0.10 KEEP · cutover BLOCKED.
Books: CTRL_LIVE_A10 ∥ COMP_H150_x_A20 (OR_K9 × HARD150 × CONF α=0.20 H=5)
"""
from __future__ import annotations

BASE_ID = "CTRL_LIVE_A10"
CHAL_ID = "COMP_H150_x_A20"
OFF_CODE = "00631L"
BASE_ALPHA = 0.10
CHAL_ALPHA = 0.20
HOLD_H = 5
CONFIRM = "RET3"
BUY_OVERLAY = "OR_K9"
SELL_OVERLAY = "HARD150"
STATUS = "OPERATING_OBSERVE"
STAGE_A_VERDICT = "COMPOSITE_HIT"
HUMAN_OPEN = (
    "OPEN paper observe: FIN×SAT COMPOSITE COMP_H150_x_A20 (Stage A COMPOSITE_HIT)"
)
HUMAN_ACCEPT_LIVE = (
    "ACCEPT Live cutover: FIN×SAT COMPOSITE COMP_H150_x_A20 "
    "(requires dedicated Class D — not this observe ballot)"
)
