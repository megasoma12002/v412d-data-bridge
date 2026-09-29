#!/usr/bin/env python3
"""Path3 COMP↔SAT weight engine — Stage A proxy (0ka8).

Engine ID: ``P3_SOFT_SLEEVE_EQ_RECON_PROXY``

On flip to SAT: freeze Soft sleeve dollar notionals from live pos, rebuild
FIN/TEL equal-share targets, ``delta = target − pos`` (0050 kept).
On flip to COMP: identity proxy (current Soft within-sleeve = dest) → empty
deltas (Stage B owns full OR_K9×HARD150).

Soft-Frozen KEEP · broker false · cutover BLOCKED · emit/fill already ON (0ka7).
"""
from __future__ import annotations

from typing import Any, Mapping

import pandas as pd

from e16_soft_frozen_base import FIN, TEL
from live_path3_t0_switch_emitter import (
    BOOK_COMP,
    BOOK_SAT,
    switch_meta_for_asof,
)
from tw_share_lots import BOARD_LOT, board_lots

ENGINE_ID = "P3_SOFT_SLEEVE_EQ_RECON_PROXY"
ETF_CODE = "0050"


def _fpos(pos: Mapping[str, float]) -> dict[str, float]:
    return {str(k): float(v) for k, v in pos.items() if abs(float(v)) > 1e-12}


def _fpx(prices: Mapping[str, float]) -> dict[str, float]:
    return {str(k): float(v) for k, v in prices.items() if float(v) > 0}


def sleeve_notional(codes: list[str] | tuple[str, ...], pos: Mapping[str, float], prices: Mapping[str, float]) -> float:
    return float(
        sum(float(pos.get(c, 0.0)) * float(prices[c]) for c in codes if c in prices and float(prices[c]) > 0)
    )


def equal_target_shares(
    codes: list[str] | tuple[str, ...],
    *,
    sleeve_dollars: float,
    prices: Mapping[str, float],
) -> dict[str, float]:
    """Equal-dollar target shares (board-lot) for a sleeve."""
    names = [c for c in codes if c in prices and float(prices[c]) > 0]
    if not names or sleeve_dollars <= 1e-9:
        return {c: 0.0 for c in names}
    per = float(sleeve_dollars) / len(names)
    out: dict[str, float] = {}
    for c in names:
        out[c] = float(board_lots(per / float(prices[c])))
    return out


def plan_sat_equal_recon(
    *,
    pos: Mapping[str, float],
    prices: Mapping[str, float],
) -> tuple[dict[str, float], dict[str, Any]]:
    """SAT dest = FIN_EQUAL + TEL_EQUAL; 0050 / other names keep current shares."""
    p = _fpos(pos)
    px = _fpx(prices)
    fin_dol = sleeve_notional(FIN, p, px)
    tel_dol = sleeve_notional(TEL, p, px)
    fin_t = equal_target_shares(FIN, sleeve_dollars=fin_dol, prices=px)
    tel_t = equal_target_shares(TEL, sleeve_dollars=tel_dol, prices=px)

    dest = dict(p)
    for c in FIN:
        dest[c] = float(fin_t.get(c, 0.0))
    for c in TEL:
        dest[c] = float(tel_t.get(c, 0.0))
    # 0050 KEEP
    if ETF_CODE in p:
        dest[ETF_CODE] = float(p[ETF_CODE])

    delta: dict[str, float] = {}
    for c in sorted(set(dest) | set(p)):
        d = float(dest.get(c, 0.0)) - float(p.get(c, 0.0))
        if abs(d) >= float(BOARD_LOT) - 1e-9:
            delta[c] = d

    meta = {
        "engine_id": ENGINE_ID,
        "dest_book": BOOK_SAT,
        "fin_notional": round(fin_dol, 2),
        "tel_notional": round(tel_dol, 2),
        "n_delta_names": len(delta),
        "delta_shares": {k: round(v, 1) for k, v in delta.items()},
        "dest_shares_fin_tel": {**fin_t, **tel_t},
    }
    return delta, meta


def plan_delta_shares(
    *,
    asof: pd.Timestamp | str,
    pos: Mapping[str, float],
    prices: Mapping[str, float],
    signal: pd.DataFrame | None = None,
    require_flip: bool = True,
) -> tuple[dict[str, float] | None, dict[str, Any]]:
    """Return ``delta_shares`` for Path3 emitter, or None if not applicable.

    None means pipeline should keep fail-closed (not invent Soft qty).
    Empty dict ``{}`` means flip handled but identity / no lot-level change.
    """
    sw = switch_meta_for_asof(asof, signal=signal)
    meta: dict[str, Any] = {
        "engine_id": ENGINE_ID,
        "switch": sw,
        "asof": str(pd.Timestamp(asof).date()),
    }
    if not sw.get("ok"):
        meta["reason"] = sw.get("reason") or "signal_unavailable"
        return None, meta
    if require_flip and not sw.get("flip"):
        meta["reason"] = "no_flip"
        return None, meta

    book = str(sw.get("book") or "")
    meta["dest_book"] = book

    if book == BOOK_SAT or "SAT" in book:
        delta, plan_meta = plan_sat_equal_recon(pos=pos, prices=prices)
        meta.update(plan_meta)
        meta["reason"] = "sat_equal_recon" if delta else "sat_equal_recon_empty"
        return delta, meta

    if book == BOOK_COMP or "COMP" in book:
        meta["reason"] = "comp_identity_proxy_no_delta"
        meta["note"] = (
            "Stage A COMP dest = current Soft within-sleeve (identity). "
            "Full OR_K9×HARD150 = Stage B."
        )
        meta["n_delta_names"] = 0
        meta["delta_shares"] = {}
        return {}, meta

    meta["reason"] = "unknown_book"
    return None, meta


def plan_or_none_for_pipeline(
    *,
    asof: pd.Timestamp | str,
    pos: Mapping[str, float],
    prices: Mapping[str, float],
    signal: pd.DataFrame | None = None,
) -> tuple[dict[str, float] | None, dict[str, Any]]:
    """e21 hook helper: None keeps ``weight_engine_not_wired``; dict (even empty) wires plan."""
    delta, meta = plan_delta_shares(
        asof=asof, pos=pos, prices=prices, signal=signal, require_flip=True
    )
    if delta is None:
        return None, meta
    # Empty dict still "wired" — emitter will return empty_after_lot_filter / emitted 0
    return delta, meta
