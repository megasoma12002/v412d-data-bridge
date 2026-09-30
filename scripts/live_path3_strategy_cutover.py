#!/usr/bin/env python3
"""Path3 strategy cutover — WITHIN_SLEEVE_PATH3 (0kac ACCEPT).

When ``LIVE.live_path3_strategy_cutover`` is True + scope ``WITHIN_SLEEVE_PATH3``:

- Soft Exact T+1 FIN∪TEL suppressed every session (stronger than flip mute)
- Soft Exact T+1 0050 KEEP
- Path3 ledger recon runs daily toward active COMP/SAT book (not flip-only)
- Flip mute is superseded-when-ON
- Broker unchanged (separate ballot)

Soft KEEP · T0_CARVE_FIN_SAT_SWITCH KEEP · overlays KEEP.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from live_soft_path3_coexist_mute import (
    POLICY_MUTE_SOFT_FIN_TEL,
    SOFT_FIN_TEL,
    filter_soft_orders,
)

MECHANISM_ID = "PATH3_STRATEGY_CUTOVER"
SCOPE_WITHIN_SLEEVE_PATH3 = "WITHIN_SLEEVE_PATH3"
SCOPE_FLIP_CARVE_ONLY = "FLIP_CARVE_ONLY"

ACCEPT_BALLOT = (
    "ACCEPT Path3 strategy cutover: WITHIN_SLEEVE_PATH3\n"
    "(Soft clips+0050 Exact T+1 KEEP · Soft FIN/TEL Exact T+1 OFF · Path3 ledger daily ·\n"
    " T0_CARVE_FIN_SAT_SWITCH KEEP · broker false · overlays KEEP)"
)


def is_cutover_on() -> bool:
    try:
        from live_config import LIVE

        return bool(getattr(LIVE, "live_path3_strategy_cutover", False))
    except Exception:
        return False


def cutover_scope() -> str:
    try:
        from live_config import LIVE

        return str(
            getattr(LIVE, "live_path3_strategy_cutover_scope", SCOPE_WITHIN_SLEEVE_PATH3)
            or SCOPE_WITHIN_SLEEVE_PATH3
        )
    except Exception:
        return SCOPE_WITHIN_SLEEVE_PATH3


def is_within_sleeve_cutover() -> bool:
    return is_cutover_on() and cutover_scope() == SCOPE_WITHIN_SLEEVE_PATH3


def daily_path3_recon_enabled() -> bool:
    """True when Path3 ledger/emit may run without flip (WITHIN scope)."""
    return is_within_sleeve_cutover()


def suppress_soft_fin_tel(
    order_rows: Sequence[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Drop Soft Exact T+1 FIN∪TEL; keep Soft 0050 / satellites / Path3 tags."""
    kept, muted, meta = filter_soft_orders(
        order_rows,
        policy=POLICY_MUTE_SOFT_FIN_TEL,
        apply=True,
    )
    out = {
        "mechanism_id": MECHANISM_ID,
        "scope": cutover_scope(),
        "enabled": True,
        "applied": True,
        "policy": POLICY_MUTE_SOFT_FIN_TEL,
        "n_kept": meta.get("n_kept"),
        "n_muted": meta.get("n_muted"),
        "mute_codes": sorted(SOFT_FIN_TEL),
        "muted_codes": meta.get("muted_codes"),
        "muted_order_ids": meta.get("muted_order_ids"),
        "soft_0050_keep": True,
        "supersedes_flip_mute": True,
    }
    return kept, out
