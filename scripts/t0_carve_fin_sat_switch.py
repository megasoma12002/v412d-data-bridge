#!/usr/bin/env python3
"""Named Exact T+0 fill carve-out: T0_CARVE_FIN_SAT_SWITCH (Path3 only).

Policy parent: research/ops/FIN_SAT_T0_CARVEOUT_POLICY_BALLOT_EXECUTED_ACCEPT.md
Stage A: 0k9t ORACLE_ONLY — hybrid/MOC tip−; same-bar needed for tip.

Live fill allowlist stays **OFF** until a dedicated ACCEPT flips
``LIVE.live_t0_carve_fin_sat_switch_fill``. Soft-Frozen / global Exact T+1 KEEP.
"""
from __future__ import annotations

from typing import Any, Mapping

CARVE_OUT_ID = "T0_CARVE_FIN_SAT_SWITCH"
ORDER_TAG_COL = "carve_out_id"
MECHANISM = "P3_T0_STATE"
SCOPE = "FIN×SAT COMP↔SAT day-switch orders only — not Soft-Frozen sleeve fills"

# Human ACCEPT line to enable live same-bar fill allowlist (not yet executed).
ACCEPT_FILL_LINE = (
    "ACCEPT Live fill carve-out: T0_CARVE_FIN_SAT_SWITCH same-bar "
    "(Path3 P3_T0_STATE only · Soft-Frozen Exact T+1 KEEP elsewhere)"
)


def is_live_fill_authorized() -> bool:
    """True only after ACCEPT flips LiveConfig flag (default False)."""
    try:
        from live_config import LIVE

        return bool(getattr(LIVE, "live_t0_carve_fin_sat_switch_fill", False))
    except Exception:
        return False


def is_carve_tagged(row: Mapping[str, Any] | object) -> bool:
    """Order/fill row tagged for this carve-out."""
    if isinstance(row, Mapping):
        raw = row.get(ORDER_TAG_COL)
    else:
        raw = getattr(row, ORDER_TAG_COL, None)
    return str(raw or "").strip() == CARVE_OUT_ID


def tag_order(row: dict[str, Any]) -> dict[str, Any]:
    """Return a copy tagged for Path3 T+0 carve-out fills."""
    out = dict(row)
    out[ORDER_TAG_COL] = CARVE_OUT_ID
    out["carve_mechanism"] = MECHANISM
    return out


def authorize_same_bar_fill(row: Mapping[str, Any] | object, *, authorized: bool | None = None) -> bool:
    """Same-bar fill allowed iff live flag on AND row tagged."""
    auth = is_live_fill_authorized() if authorized is None else bool(authorized)
    clock = row.get("execution_clock") if isinstance(row, Mapping) else getattr(row, "execution_clock", None)
    return auth and is_carve_tagged(row) and clock != "NEXT_SESSION_OPEN"
