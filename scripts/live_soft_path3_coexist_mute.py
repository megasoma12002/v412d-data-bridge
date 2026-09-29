#!/usr/bin/env python3
"""Soft↔Path3 flip-day coexistence mute (0kaa).

Mechanism: ``SOFT_PATH3_FLIP_MUTE``
Default policy: ``MUTE_SOFT_FIN_TEL`` — on Path3 flip day (emit ON),
drop Soft Exact T+1 orders for FIN∪TEL even if Path3 deltas are empty
(fail-closed coexistence); keep Soft 0050 / satellites / Path3.

Live flag ``LIVE.live_soft_path3_coexist_mute=True`` after ACCEPT 0kaa (2026-09-29).
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

from e16_soft_frozen_base import FIN, TEL

MECHANISM_ID = "SOFT_PATH3_FLIP_MUTE"
POLICY_MUTE_SOFT_FIN_TEL = "MUTE_SOFT_FIN_TEL"
POLICY_MUTE_SOFT_ALL_SLEEVES = "MUTE_SOFT_ALL_SLEEVES"
POLICY_MUTE_OVERLAP_CODES = "MUTE_OVERLAP_CODES"
POLICY_MUTE_SOFT_ON_FLIP_META = "MUTE_SOFT_ON_FLIP_META"
DEFAULT_POLICY = POLICY_MUTE_SOFT_FIN_TEL

ETF_CODE = "0050"
SOFT_FIN_TEL = frozenset(list(FIN) + list(TEL))
SOFT_ALL_SLEEVES = frozenset(list(SOFT_FIN_TEL) + [ETF_CODE])


def mute_codes_for_policy(
    policy: str,
    *,
    path3_delta_codes: Iterable[str] | None = None,
) -> frozenset[str]:
    p = str(policy or DEFAULT_POLICY)
    if p == POLICY_MUTE_SOFT_ALL_SLEEVES:
        return SOFT_ALL_SLEEVES
    if p == POLICY_MUTE_OVERLAP_CODES:
        return frozenset(str(c) for c in (path3_delta_codes or []))
    # MUTE_SOFT_FIN_TEL and MUTE_SOFT_ON_FLIP_META share FIN∪TEL scope
    return SOFT_FIN_TEL


def should_mute(
    *,
    mute_enabled: bool,
    emit_enabled: bool,
    flip: bool,
    n_path3_delta_names: int = 0,
    policy: str = DEFAULT_POLICY,
) -> bool:
    """Return True when Soft sleeve rows should be filtered before Path3 append.

    ``MUTE_SOFT_FIN_TEL`` / ``MUTE_SOFT_ON_FLIP_META`` / ``MUTE_SOFT_ALL_SLEEVES``:
    mute on flip when emit is ON (even if Path3 plan is empty — coexistence
    fail-closed). ``MUTE_OVERLAP_CODES`` still requires non-empty delta codes.
    """
    if not mute_enabled or not emit_enabled:
        return False
    if not flip:
        return False
    p = str(policy or DEFAULT_POLICY)
    if p == POLICY_MUTE_OVERLAP_CODES:
        return int(n_path3_delta_names) > 0
    return True


def filter_soft_orders(
    order_rows: Sequence[Mapping[str, Any]],
    *,
    policy: str = DEFAULT_POLICY,
    path3_delta_codes: Iterable[str] | None = None,
    apply: bool = True,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Split Soft rows into kept / muted.

    Never drops Path3-tagged rows (``-P3T0`` / ``path3_switch``) if present.
    """
    codes = mute_codes_for_policy(policy, path3_delta_codes=path3_delta_codes)
    kept: list[dict[str, Any]] = []
    muted: list[dict[str, Any]] = []
    if not apply:
        return [dict(r) for r in order_rows], [], {
            "mechanism_id": MECHANISM_ID,
            "policy": policy,
            "applied": False,
            "n_kept": len(order_rows),
            "n_muted": 0,
            "mute_codes": sorted(codes),
        }

    for raw in order_rows:
        row = dict(raw)
        oid = str(row.get("order_id") or "")
        if row.get("path3_switch") or oid.endswith("-P3T0"):
            kept.append(row)
            continue
        code = str(row.get("code") or "")
        if code in codes:
            muted.append(row)
        else:
            kept.append(row)

    meta = {
        "mechanism_id": MECHANISM_ID,
        "policy": str(policy or DEFAULT_POLICY),
        "applied": True,
        "n_kept": len(kept),
        "n_muted": len(muted),
        "mute_codes": sorted(codes),
        "muted_codes": sorted({str(r.get("code")) for r in muted}),
        "muted_order_ids": [r.get("order_id") for r in muted],
    }
    return kept, muted, meta


def apply_coexist_mute(
    order_rows: Sequence[Mapping[str, Any]],
    *,
    mute_enabled: bool,
    emit_enabled: bool,
    flip: bool,
    path3_delta_shares: Mapping[str, float] | None,
    policy: str = DEFAULT_POLICY,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Pipeline helper: maybe mute Soft FIN/TEL before Path3 append."""
    deltas = path3_delta_shares or {}
    n_delta = sum(1 for v in deltas.values() if abs(float(v)) > 1e-12)
    do = should_mute(
        mute_enabled=mute_enabled,
        emit_enabled=emit_enabled,
        flip=bool(flip),
        n_path3_delta_names=n_delta,
        policy=policy,
    )
    kept, muted, meta = filter_soft_orders(
        order_rows,
        policy=policy,
        path3_delta_codes=list(deltas.keys()),
        apply=do,
    )
    meta.update(
        {
            "should_mute": do,
            "mute_enabled": bool(mute_enabled),
            "emit_enabled": bool(emit_enabled),
            "flip": bool(flip),
            "n_path3_delta_names": int(n_delta),
        }
    )
    return kept, meta
