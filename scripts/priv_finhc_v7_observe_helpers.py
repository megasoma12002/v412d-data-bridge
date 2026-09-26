#!/usr/bin/env python3
"""民股 Gate V7 Bull+Side F05 dual-paper observe — shared constants (paper only)."""
from __future__ import annotations

BASE_ID = "BASE_LIVE_FUSE_COOL"
CHAL_ID = "V7_REG_BULL_SIDE_F05_KDMAY"
HUMAN_OPEN = (
    "OPEN observe: 民股 V7 Bull+Side F05 近持平"
)
STATUS = "OPERATING_OBSERVE"
STAGE_A_VERDICT = "PRIV_FINHC_SOFT"
NEAR_FLAT_NOTE = (
    "human OPEN near-flat observe: held CAGR↑ +0.18pp (short of +0.20 HIT floor) · "
    "sealed MDD↑ +0.14pp · tip OK · Soft-Frozen 公股 R1 KEEP"
)

# Frozen Stage A SOFT champion (do not retune after sealed peek)
GATE_ID = "REG_BULL_SIDE"
PRIV_FRAC = 0.05
PRIV_POLICY = "PRIV_KD_MAY"
