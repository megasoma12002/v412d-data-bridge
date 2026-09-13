#!/usr/bin/env python3
"""E45 defend→handoff paper-observe helpers (DH_dd06_vz1p0).

LIVE WIRED 2026-09-13 with FUSE_ADDITIVE (see live_dh_fuse_cutover.py). E45 stitch remains FORBIDDEN.
Frozen Stage A winner: dd=6%, vol_z=1.0, SHRINK=0.50.
"""
from __future__ import annotations

BASE_ID = "LIVE_STACK"
CHAL_ID = "DH_dd06_vz1p0"
CHAL_ALIAS = "DH_dd06"
STATUS = "LIVE_WIRED"
HUMAN_OPEN = "OPEN E45 defend-handoff observe: DH_dd06_vz1p0"
SCREEN_ID = "E45_DEFEND_HANDOFF_STAGEA_SCREEN"
CHARTER_ID = "E45_DEFEND_HANDOFF_PAPER_CHARTER"
STAGE_A_VERDICT = "HANDOFF_PROMOTE_SHAPED"

# Frozen Stage A best cell
DD_THRESHOLD = 0.06
VOL_Z_THRESHOLD = 1.0
SHRINK = 0.50

LIVE_WIRE = True
STITCH_AUTHORIZED = False
HUMAN_ACCEPT = "ACCEPT Live cutover: DH_dd06 + FUSE_ADDITIVE"
