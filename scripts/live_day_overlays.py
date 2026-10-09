#!/usr/bin/env python3
"""Live day overlay orchestration — Path3 WITHIN / T0 emit / tipsoft.

Extracted from ``e21_forward_pipeline`` so the CLI stays thin. Behavior-preserving
for Soft clips, Exact T+1 fills, broker, Path4 OFF.

Order of application (KEEP):
1. Path3 strategy cutover WITHIN → suppress Soft FIN/TEL
2. Soft↔Path3 coexist mute (superseded when WITHIN ON)
3. Path3 T0 weight plan → **DD_SWITCH tip apply** (may flatten FIN∪TEL→cash) → emit
4. tip Soft LIVE_OVERRIDE gate stamps / telemetry (no ``order_rows`` mutation)
5. tip Soft DD_SWITCH session stamps
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from live_config import (
    LIVE_PATH3_STRATEGY_CUTOVER,
    LIVE_PATH3_STRATEGY_CUTOVER_BALLOT,
    LIVE_PATH3_STRATEGY_CUTOVER_SCOPE,
    LIVE_PATH3_WEIGHT_ENGINE_BALLOT,
    LIVE_PATH3_WEIGHT_ENGINE_MODE,
    LIVE_SOFT_PATH3_COEXIST_MUTE,
    LIVE_SOFT_PATH3_COEXIST_MUTE_BALLOT,
    LIVE_SOFT_PATH3_COEXIST_MUTE_POLICY,
    LIVE_T0_CARVE_FIN_SAT_SWITCH_EMIT,
    LIVE_T0_CARVE_FIN_SAT_SWITCH_EMIT_BALLOT,
    LIVE_TIPSOFT_DD_SWITCH,
    LIVE_TIPSOFT_LIVE_OVERRIDE,
)


@dataclass
class DayOverlayResult:
    order_rows: list[dict[str, Any]]
    path3_cutover_meta: dict[str, Any]
    path3_emit_meta: dict[str, Any]
    path3_weight_meta: dict[str, Any]
    soft_path3_mute_meta: dict[str, Any]
    tipsoft_override_meta: dict[str, Any]
    tipsoft_dd_meta: dict[str, Any]


def apply_path3_tipsoft_overlays(
    order_rows: list[dict[str, Any]],
    *,
    asof: pd.Timestamp,
    pos: dict[str, float],
    prices: dict[str, float],
) -> DayOverlayResult:
    """Apply Path3 + tipsoft overlay steps; return rows + stamp metas."""
    import live_path3_strategy_cutover as p3_cut

    path3_cutover_meta: dict[str, Any] = {
        "enabled": bool(LIVE_PATH3_STRATEGY_CUTOVER),
        "scope": LIVE_PATH3_STRATEGY_CUTOVER_SCOPE,
        "applied": False,
        "n_muted": 0,
    }
    cutover_within = bool(p3_cut.is_within_sleeve_cutover())
    if cutover_within and not LIVE_T0_CARVE_FIN_SAT_SWITCH_EMIT:
        raise RuntimeError('Path3 daily cutover requires an active replacement planner')

    path3_emit_meta: dict[str, Any] = {
        "enabled": bool(LIVE_T0_CARVE_FIN_SAT_SWITCH_EMIT)
    }
    path3_weight_meta: dict[str, Any] = {
        "engine_id": None,
        "reason": "emit_flag_off",
        "weight_engine_mode": LIVE_PATH3_WEIGHT_ENGINE_MODE,
    }
    soft_path3_mute_meta: dict[str, Any] = {
        "enabled": bool(LIVE_SOFT_PATH3_COEXIST_MUTE),
        "policy": LIVE_SOFT_PATH3_COEXIST_MUTE_POLICY,
        "applied": False,
        "n_muted": 0,
        "superseded_by_cutover": cutover_within,
    }
    tipsoft_dd_apply_meta: dict[str, Any] = {"tipsoft_dd_switch_live": False}

    if LIVE_T0_CARVE_FIN_SAT_SWITCH_EMIT:
        import live_path3_t0_switch_emitter as path3_em
        import live_path3_t0_weight_engine as path3_we
        import live_soft_path3_coexist_mute as soft_p3_mute

        path3_deltas, path3_weight_meta = path3_we.plan_or_none_for_pipeline(
            asof=asof,
            pos=pos,
            prices=prices,
        )
        if cutover_within and path3_deltas is None:
            raise RuntimeError('Path3 daily cutover blocked before Soft suppression: '+str(path3_weight_meta.get('reason')))
        # tip Soft Exact T+1 DD_SWITCH tip apply (0kbd ACCEPT) — may flatten
        # FIN∪TEL→cash on TRAIL-selected Path3 OFF days (−P3T0). Not stamps-only.
        if LIVE_TIPSOFT_DD_SWITCH:
            import live_tipsoft_dd_switch as tipsoft_dd

            path3_deltas, tipsoft_dd_apply_meta = tipsoft_dd.apply_to_path3_deltas(
                path3_deltas,
                pos,
                asof,
                market_tip=asof,
            )
            path3_weight_meta = dict(path3_weight_meta)
            path3_weight_meta["tipsoft_dd_switch"] = tipsoft_dd_apply_meta
            if cutover_within and not (tipsoft_dd_apply_meta.get('gate') or {}).get('ok'):
                raise RuntimeError('DD gate invalid before Path3 cutover: '+str(tipsoft_dd_apply_meta.get('reason')))
        flip = bool((path3_weight_meta.get("switch") or {}).get("flip"))
        if cutover_within:
            order_rows, path3_cutover_meta = p3_cut.suppress_soft_fin_tel(order_rows)
            path3_cutover_meta["ballot"] = LIVE_PATH3_STRATEGY_CUTOVER_BALLOT
            soft_path3_mute_meta = {
                "enabled": bool(LIVE_SOFT_PATH3_COEXIST_MUTE),
                "policy": LIVE_SOFT_PATH3_COEXIST_MUTE_POLICY,
                "applied": False,
                "n_muted": 0,
                "superseded_by_cutover": True,
                "ballot": LIVE_SOFT_PATH3_COEXIST_MUTE_BALLOT,
            }
        else:
            order_rows, soft_path3_mute_meta = soft_p3_mute.apply_coexist_mute(
                order_rows,
                mute_enabled=bool(LIVE_SOFT_PATH3_COEXIST_MUTE),
                emit_enabled=True,
                flip=flip,
                path3_delta_shares=path3_deltas,
                policy=str(LIVE_SOFT_PATH3_COEXIST_MUTE_POLICY),
            )
            soft_path3_mute_meta["ballot"] = LIVE_SOFT_PATH3_COEXIST_MUTE_BALLOT
            soft_path3_mute_meta["superseded_by_cutover"] = False
        path3_orders, path3_emit_meta = path3_em.maybe_emit_switch_orders(
            asof=asof,
            prices=prices,
            delta_shares=path3_deltas,
            authorized=True,
        )
        order_rows.extend(path3_orders)
        path3_emit_meta["enabled"] = True
        path3_emit_meta["weight_engine"] = path3_weight_meta
        path3_emit_meta["path3_strategy_cutover"] = cutover_within
        path3_emit_meta["tipsoft_dd_switch"] = tipsoft_dd_apply_meta
    else:
        path3_emit_meta["reason"] = "emit_flag_off"

    # tip Soft Exact T+1 LIVE_OVERRIDE — gate stamps / telemetry only.
    tipsoft_override_meta: dict[str, Any] = {"tipsoft_live_override_live": False}
    if LIVE_TIPSOFT_LIVE_OVERRIDE:
        import live_tipsoft_live_override as tipsoft_ov

        tipsoft_override_meta = tipsoft_ov.session_meta(asof, market_tip=asof)

    # tip Soft Exact T+1 DD_SWITCH session stamps (0kbd ACCEPT tip apply).
    tipsoft_dd_meta: dict[str, Any] = {"tipsoft_dd_switch_live": False}
    if LIVE_TIPSOFT_DD_SWITCH:
        import live_tipsoft_dd_switch as tipsoft_dd

        tipsoft_dd_meta = tipsoft_dd.session_meta(asof, market_tip=asof)

    return DayOverlayResult(
        order_rows=order_rows,
        path3_cutover_meta=path3_cutover_meta,
        path3_emit_meta=path3_emit_meta,
        path3_weight_meta=path3_weight_meta,
        soft_path3_mute_meta=soft_path3_mute_meta,
        tipsoft_override_meta=tipsoft_override_meta,
        tipsoft_dd_meta=tipsoft_dd_meta,
    )


def overlay_signal_fields(ov: DayOverlayResult) -> dict[str, Any]:
    """Flatten overlay metas into ``signals.csv`` columns."""
    path3_emit_meta = ov.path3_emit_meta
    path3_weight_meta = ov.path3_weight_meta
    soft_path3_mute_meta = ov.soft_path3_mute_meta
    path3_cutover_meta = ov.path3_cutover_meta
    return {
        "path3_t0_emit_live": bool(LIVE_T0_CARVE_FIN_SAT_SWITCH_EMIT),
        "path3_t0_emit_ballot": LIVE_T0_CARVE_FIN_SAT_SWITCH_EMIT_BALLOT
        if LIVE_T0_CARVE_FIN_SAT_SWITCH_EMIT
        else None,
        "path3_t0_emit_reason": path3_emit_meta.get("reason"),
        "path3_t0_n_orders": int(path3_emit_meta.get("n_orders") or 0),
        "path3_t0_weight_engine_mode": LIVE_PATH3_WEIGHT_ENGINE_MODE,
        "path3_t0_weight_engine_ballot": LIVE_PATH3_WEIGHT_ENGINE_BALLOT,
        "path3_t0_weight_engine_id": path3_weight_meta.get("engine_id"),
        "path3_t0_weight_reason": path3_weight_meta.get("reason"),
        "path3_t0_weight_n_delta_names": path3_weight_meta.get("n_delta_names"),
        "soft_path3_coexist_mute_live": bool(LIVE_SOFT_PATH3_COEXIST_MUTE),
        "soft_path3_coexist_mute_ballot": LIVE_SOFT_PATH3_COEXIST_MUTE_BALLOT
        if LIVE_SOFT_PATH3_COEXIST_MUTE
        else None,
        "soft_path3_coexist_mute_policy": soft_path3_mute_meta.get("policy"),
        "soft_path3_coexist_mute_applied": bool(soft_path3_mute_meta.get("applied")),
        "soft_path3_coexist_mute_n_muted": int(soft_path3_mute_meta.get("n_muted") or 0),
        "soft_path3_coexist_mute_superseded_by_cutover": bool(
            soft_path3_mute_meta.get("superseded_by_cutover")
        ),
        "path3_strategy_cutover_live": bool(LIVE_PATH3_STRATEGY_CUTOVER),
        "path3_strategy_cutover_scope": LIVE_PATH3_STRATEGY_CUTOVER_SCOPE,
        "path3_strategy_cutover_ballot": LIVE_PATH3_STRATEGY_CUTOVER_BALLOT
        if LIVE_PATH3_STRATEGY_CUTOVER
        else None,
        "path3_strategy_cutover_applied": bool(path3_cutover_meta.get("applied")),
        "path3_strategy_cutover_n_muted": int(path3_cutover_meta.get("n_muted") or 0),
        **ov.tipsoft_override_meta,
        **ov.tipsoft_dd_meta,
    }
