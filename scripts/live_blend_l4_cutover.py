#!/usr/bin/env python3
"""Live cutover actuators for BLEND_025 + L4_DD_PATH (ACCEPT 2026-09-19 bundle).

Order (forward-only): Soft-Frozen / FUSE target → BLEND_025 → L4_DD_PATH_08_50.
FIN50 is used as the BLEND/L4 cap book only — Soft-Frozen BASE clip stays [0.60, 0.90].
"""
from __future__ import annotations

from typing import Any

import pandas as pd

from e16_fin_cap_oof_challenger import e16_features_fin_cap
from fincap_sealed_cagr_improve_diag import blend_targets
from mdd_l4_loss_engine_oof import dd_path_target

HUMAN_ACCEPT_BLEND = "ACCEPT live Soft-Frozen cutover: BLEND_025"
HUMAN_ACCEPT_L4 = "ACCEPT live L4 cutover: L4_DD_PATH_08_50"
HUMAN_ACCEPT_FIN50_COMPONENT = "ACCEPT FIN_CAP_50 as BLEND_025 component"
BLEND_ALPHA = 0.25
FIN_CAP_LO, FIN_CAP_HI = 0.35, 0.50
L4_DD_THR = -0.08
L4_ID = "L4_DD_PATH_08_50"
BLEND_ID = "BLEND_025"


def fin50_target_for_market(market: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (prices, fin50_target) for FIN_CAP_50 clip."""
    prices, _sleeve, fin50, _reg = e16_features_fin_cap(market, FIN_CAP_LO, FIN_CAP_HI)
    return prices, fin50


def apply_blend025(base_target: pd.DataFrame, market: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    _prices, fin50 = fin50_target_for_market(market)
    out = blend_targets(base_target, fin50, BLEND_ALPHA)
    meta = {
        "enabled": True,
        "id": BLEND_ID,
        "alpha": BLEND_ALPHA,
        "fin_cap": [FIN_CAP_LO, FIN_CAP_HI],
        "human_accept": HUMAN_ACCEPT_BLEND,
        "fin50_component_accept": HUMAN_ACCEPT_FIN50_COMPONENT,
    }
    return out, meta


def apply_l4_dd_path(
    base_target: pd.DataFrame, market: pd.DataFrame
) -> tuple[pd.DataFrame, dict[str, Any]]:
    prices, fin50 = fin50_target_for_market(market)
    out, flag = dd_path_target(base_target, fin50, prices, L4_DD_THR)
    latest = bool(flag.iloc[-1]) if len(flag) else False
    meta = {
        "enabled": True,
        "id": L4_ID,
        "dd_thr": L4_DD_THR,
        "fin_cap": [FIN_CAP_LO, FIN_CAP_HI],
        "dd_path_cap_on_latest": latest,
        "human_accept": HUMAN_ACCEPT_L4,
    }
    return out, meta
