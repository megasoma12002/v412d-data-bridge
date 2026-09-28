"""P3_T0_STATE dual-paper observe helpers (Path3 · Exact T+0 carve-out)."""
from __future__ import annotations

BASE_ID = "CTRL_LIVE_A10"
CHAL_ID = "P3_T0_STATE"
THETA = 0.01
STATUS = "OPERATING_OBSERVE"
STAGE_A_VERDICT = "T0_ONLY_EDGE"
CARVE_OUT_ID = "T0_CARVE_FIN_SAT_SWITCH"
HUMAN_ACCEPT = (
    "ACCEPT T+0 carve-out + OPEN paper observe: P3_T0_STATE "
    "(FIN×SAT Path3 · T0_CARVE_FIN_SAT_SWITCH)"
)
HUMAN_OPEN = HUMAN_ACCEPT
