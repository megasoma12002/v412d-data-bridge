"""P3_T0_STATE dual-paper observe helpers (Path3 · Exact T+0 carve-out)."""
from __future__ import annotations

BASE_ID = "CTRL_LIVE_A10"
CHAL_ID = "P3_T0_STATE"
THETA = 0.005
THETA_PRIOR = 0.01
STATUS = "OPERATING_OBSERVE"
STAGE_A_VERDICT = "T0_ONLY_EDGE"
CARVE_OUT_ID = "T0_CARVE_FIN_SAT_SWITCH"
HUMAN_ACCEPT = (
    "ACCEPT T+0 carve-out + OPEN paper observe: P3_T0_STATE "
    "(FIN×SAT Path3 · T0_CARVE_FIN_SAT_SWITCH)"
)
HUMAN_RETUNE_THETA = (
    "ACCEPT Path3 observe retune: SAT_LEAD θ=0.005 "
    "(P3_T0_STATE · T0_CARVE_FIN_SAT_SWITCH · parents 0ka3–0ka6)"
)
HUMAN_OPEN = HUMAN_ACCEPT
