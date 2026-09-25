#!/usr/bin/env python3
"""COOL_c8_f50_d21 paper-observe helpers (R2 Stage B tip-safe FAST winner).

Paper observe only · Soft-Frozen KEEP · no live wire.
Frozen recipe: PROXY x=8% · floor=0.50 · exit=6% · max_dwell=21 · cool=8.
"""
from __future__ import annotations

import pandas as pd

BASE_ID = "LIVE_STACK"
CHAL_ID = "COOL_c8_f50_d21"
STATUS = "OPERATING"
HUMAN_OPEN = "OPEN tip-safe FAST observe: COOL_c8_f50_d21"
SCREEN_ID = "HELD_MDD17_R2_TIPSAFE_FAST_STAGEB_SCREEN"
CHARTER_ID = "HELD_MDD17_R2_TIPSAFE_FAST_STAGEB_CHARTER"
STAGE_B_VERDICT = "TIPSAFE_STRETCH"

# Frozen Stage B tipsafe stretch cell (human ACCEPT MDD floor -15%)
PROXY_X = 0.08
FLOOR = 0.50
EXIT_X = 0.06
MAX_DWELL = 21
COOL = 8

LIVE_WIRE = False
CUTOVER_AUTHORIZED = False


def build_cool_c8_exposure(dates: pd.DatetimeIndex, proxy_mdd63: pd.Series) -> pd.Series:
    """Causal PROXY circuit with post-exit cooldown (COOL_c8_f50_d21 freeze)."""
    px = proxy_mdd63.reindex(dates).fillna(0.0)
    out = pd.Series(1.0, index=dates, dtype=float)
    defending = False
    dwell = 0
    cool_left = 0
    for i in range(len(dates)):
        v = float(px.iloc[i])
        if cool_left > 0:
            cool_left -= 1
            out.iloc[i] = 1.0
            continue
        if not defending:
            if v <= -float(PROXY_X):
                defending = True
                dwell = 0
                out.iloc[i] = float(FLOOR)
            else:
                out.iloc[i] = 1.0
        else:
            dwell += 1
            out.iloc[i] = float(FLOOR)
            if v > -float(EXIT_X) or dwell >= int(MAX_DWELL):
                defending = False
                cool_left = int(COOL)
                out.iloc[i] = 1.0
    return out
