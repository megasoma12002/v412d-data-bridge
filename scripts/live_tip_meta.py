#!/usr/bin/env python3
"""Shared live tip cutover stamps for portfolio_state / signals / audits.

Single builder so ACCEPT fields cannot drift across ``live_day_commit`` and
``e21_forward_pipeline``. Soft-Frozen KEEP — stamp strings only.
"""
from __future__ import annotations

from typing import Any

from e16_soft_frozen_base import SOFT_FROZEN_CLIP_FLIP_STAMP
from live_config import (
    E45_STITCH_ROLLBACK,
    KD_OPT,
    LIVE,
    LIVE_COOL_EXPOSURE,
    LIVE_COOL_ID,
    LIVE_CONF_RET3_631L,
    LIVE_CONF_RET3_BALLOT,
    LIVE_CUTOVER_BALLOT,
    LIVE_DH_EXPOSURE,
    LIVE_DH_ID,
    LIVE_FIN_PRIV_BALLOT,
    LIVE_FIN_PRIV_V7_F05,
    LIVE_FIN_WITHIN_SLEEVE,
    LIVE_FUSE_ADDITIVE,
    LIVE_FUSE_SOFT_SELL_BALLOT,
    LIVE_FUSE_SOFT_SELL_BOOST,
    LIVE_PATH3_STRATEGY_CUTOVER,
    LIVE_TEL_T3_BALLOT,
    LIVE_TEL_T3_COOL_INV_VOL20,
    LIVE_TEL_WITHIN_SLEEVE,
    LIVE_TIPSOFT_LIVE_OVERRIDE,
    LIVE_TIPSOFT_LIVE_OVERRIDE_BALLOT,
    LIVE_TIPSOFT_LIVE_OVERRIDE_POLICY,
    TIP_BOOKS_ALIGN_BALLOT,
)


def build_cutover_stamps() -> dict[str, Any]:
    """Canonical tip meta flags (no cash/positions — those stay call-site)."""
    return {
        "financial_alloc": LIVE_FIN_WITHIN_SLEEVE,
        "kd_opt_id": KD_OPT["id"],
        "fin_within_sleeve_cutover": "ACCEPT_2026-09-09_KD_OPT",
        "telecom_alloc": (
            "TEL_T3_COOL_INV_VOL20" if LIVE_TEL_T3_COOL_INV_VOL20 else LIVE_TEL_WITHIN_SLEEVE
        ),
        "tel_t3_cool_inv_vol20_live": bool(LIVE_TEL_T3_COOL_INV_VOL20),
        "tel_t3_ballot": LIVE_TEL_T3_BALLOT if LIVE_TEL_T3_COOL_INV_VOL20 else None,
        "tel_t3_cutover": (
            "ACCEPT_2026-09-26_TEL_T3_COOL_INV_VOL20" if LIVE_TEL_T3_COOL_INV_VOL20 else None
        ),
        "tel_t3_rollback": (
            "Set LIVE_TEL_T3_COOL_INV_VOL20=False (live_config.live_tel_t3_cool_inv_vol20); "
            "reverts Telecom to TEL_EQUAL equal-split"
            if LIVE_TEL_T3_COOL_INV_VOL20
            else None
        ),
        "soft_frozen_clip_flip": SOFT_FROZEN_CLIP_FLIP_STAMP,
        "e45_stitch": False,
        "e45_book": None,
        "e45_stitch_ballot": None,
        "e45_stitch_rollback": E45_STITCH_ROLLBACK,
        "tip_books_align_ballot": TIP_BOOKS_ALIGN_BALLOT,
        "fuse_additive": bool(LIVE_FUSE_ADDITIVE),
        "fuse_soft_sell_boost": float(LIVE_FUSE_SOFT_SELL_BOOST) if LIVE_FUSE_ADDITIVE else None,
        "fuse_soft_sell_ballot": LIVE_FUSE_SOFT_SELL_BALLOT if LIVE_FUSE_ADDITIVE else None,
        "fuse_soft_sell_cutover": (
            "ACCEPT_2026-09-26_SELL_A75_UNDER_COOL" if LIVE_FUSE_ADDITIVE else None
        ),
        "dh_exposure_live": bool(LIVE_DH_EXPOSURE),
        "dh_id": LIVE_DH_ID if LIVE_DH_EXPOSURE else None,
        "cool_exposure_live": bool(LIVE_COOL_EXPOSURE),
        "cool_id": LIVE_COOL_ID if LIVE_COOL_EXPOSURE else None,
        "live_cutover": "ACCEPT_2026-09-25_COOL_c8_REPLACE_DH_KEEP_FUSE",
        "live_cutover_ballot": LIVE_CUTOVER_BALLOT
        if (LIVE_FUSE_ADDITIVE or LIVE_DH_EXPOSURE or LIVE_COOL_EXPOSURE)
        else None,
        "live_cutover_rollback": (
            "Set LIVE_COOL_EXPOSURE=False; optional restore LIVE_DH_EXPOSURE=True "
            "only with dedicated ACCEPT; LIVE_FUSE_ADDITIVE independent; "
            "SELL_a75 → set live_fuse_soft_sell_boost=0.5"
        ),
        "fin_priv_v7_f05_live": bool(LIVE_FIN_PRIV_V7_F05),
        "fin_priv_ballot": LIVE_FIN_PRIV_BALLOT if LIVE_FIN_PRIV_V7_F05 else None,
        "fin_priv_cutover": (
            "ACCEPT_2026-09-25_CLASSD_FINPRIV_V7_F05" if LIVE_FIN_PRIV_V7_F05 else None
        ),
        "fin_priv_rollback": (
            "Set LIVE_FIN_PRIV_V7_F05=False (live_config.live_fin_priv_v7_f05); "
            "gate-off path force-sells PRIV holdings"
            if LIVE_FIN_PRIV_V7_F05
            else None
        ),
        "conf_ret3_631l_live": bool(LIVE_CONF_RET3_631L),
        "conf_ret3_ballot": LIVE_CONF_RET3_BALLOT if LIVE_CONF_RET3_631L else None,
        "conf_ret3_cutover": (
            "ACCEPT_2026-09-26_CONF_RET3_A10_H5_00631L" if LIVE_CONF_RET3_631L else None
        ),
        "conf_ret3_rollback": (
            "Set LIVE_CONF_RET3_631L=False (live_config.live_conf_ret3_631l); "
            "next tip day force-flats 00631L when off_weight=0"
            if LIVE_CONF_RET3_631L
            else None
        ),
        "tipsoft_live_override_live": bool(LIVE_TIPSOFT_LIVE_OVERRIDE),
        "tipsoft_live_override_wire_mode": (
            "gate_stamps_telemetry" if LIVE_TIPSOFT_LIVE_OVERRIDE else None
        ),
        "tipsoft_live_override_policy": (
            LIVE_TIPSOFT_LIVE_OVERRIDE_POLICY if LIVE_TIPSOFT_LIVE_OVERRIDE else None
        ),
        "tipsoft_live_override_ballot": (
            LIVE_TIPSOFT_LIVE_OVERRIDE_BALLOT if LIVE_TIPSOFT_LIVE_OVERRIDE else None
        ),
        "tipsoft_live_override_cutover": (
            "ACCEPT_2026-09-30_TIPSOFT_P3_LIVE_OVERRIDE_W42_M05_K3"
            if LIVE_TIPSOFT_LIVE_OVERRIDE
            else None
        ),
        "tipsoft_live_override_rollback": (
            "Set LIVE.live_tipsoft_live_override=False "
            "(live_config.live_tipsoft_live_override); tip Soft Exact T+1 "
            "LIVE_OVERRIDE gate stamps off; Path3 WITHIN / Soft FIN/TEL unchanged"
            if LIVE_TIPSOFT_LIVE_OVERRIDE
            else None
        ),
        # LIVE-derived coexistence (not hardcoded wishful stamps).
        "tipsoft_live_override_path3_within_keep": bool(LIVE_PATH3_STRATEGY_CUTOVER),
        "tipsoft_live_override_soft_fin_tel_stay_off": bool(LIVE_PATH3_STRATEGY_CUTOVER),
        "tipsoft_live_override_path4_live": bool(getattr(LIVE, "live_path4", False)),
        "tipsoft_live_override_broker": bool(LIVE.broker_live_write_accepted),
        "tipsoft_override_return_blend_applied": False,
    }
