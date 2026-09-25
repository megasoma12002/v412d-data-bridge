#!/usr/bin/env python3
"""E45 defend→handoff helpers (DH_dd06_vz1p0).

LIVE WIRED 2026-09-13 with FUSE_ADDITIVE; **replaced forward-only** 2026-09-25 by
``COOL_c8_f50_d21`` (keep FUSE) — see ``live_cool_c8_cutover.py``.
E45 stitch remains FORBIDDEN. Frozen Stage A winner recorded for paper observe.
"""
from __future__ import annotations

BASE_ID = "LIVE_STACK"
CHAL_ID = "DH_dd06_vz1p0"
CHAL_ALIAS = "DH_dd06"
STATUS = "REPLACED_BY_COOL_C8"
HUMAN_OPEN = "OPEN E45 defend-handoff observe: DH_dd06_vz1p0"
SCREEN_ID = "E45_DEFEND_HANDOFF_STAGEA_SCREEN"
CHARTER_ID = "E45_DEFEND_HANDOFF_PAPER_CHARTER"
STAGE_A_VERDICT = "HANDOFF_PROMOTE_SHAPED"

# Frozen Stage A best cell
DD_THRESHOLD = 0.06
VOL_Z_THRESHOLD = 1.0
SHRINK = 0.50

LIVE_WIRE = False  # replaced 2026-09-25 by COOL_c8 (LIVE_DH_EXPOSURE=False)
STITCH_AUTHORIZED = False
HUMAN_ACCEPT = "ACCEPT Live cutover: DH_dd06 + FUSE_ADDITIVE"
REPLACED_BY = "COOL_c8_f50_d21"
REPLACED_BALLOT = "ACCEPT Live cutover: COOL_c8_f50_d21 (replace DH, keep FUSE)"
