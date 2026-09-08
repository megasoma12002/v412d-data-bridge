#!/usr/bin/env python3
"""Telecom within-sleeve allocation (live + paper).

Human 2026-09-08: ACCEPT live ``TEL_MIN_LOT_PACK`` cutover (+ capital 500M).
Soft-Frozen *sleeve clips* unchanged — this only splits Telecom trade dollars
across 2412/3045/4904 under board-lot 1000.

Stage B paper screen had STOP vs TEL_EQUAL on held-out score; live wire is an
explicit human override (fill priority at operating scale).
"""
from __future__ import annotations

from tw_share_lots import BOARD_LOT, board_lots

TEL_DEFAULT = ("2412", "3045", "4904")

TEL_ALLOC_EQUAL = "TEL_EQUAL"
TEL_ALLOC_MIN_LOT_PACK = "TEL_MIN_LOT_PACK"
TEL_ALLOC_TOP1 = "TEL_TOP1"
TEL_ALLOC_TOP2_EQUAL = "TEL_TOP2_EQUAL"
TEL_ALLOC_POLICIES = (
    TEL_ALLOC_EQUAL,
    TEL_ALLOC_MIN_LOT_PACK,
    TEL_ALLOC_TOP1,
    TEL_ALLOC_TOP2_EQUAL,
)

# Live DEFAULT after human ACCEPT (2026-09-08).
LIVE_TELECOM_ALLOC = TEL_ALLOC_MIN_LOT_PACK


def held_board_qty(pos: dict, code: str, lot_size: int = BOARD_LOT) -> int:
    held = float(pos.get(code, 0.0))
    if lot_size <= 1:
        return int(held)
    return board_lots(held) if lot_size == BOARD_LOT else int(held // lot_size) * lot_size


def lot_qty_from_notional(value: float, price: float, lot_size: int = BOARD_LOT) -> int:
    if price <= 0 or lot_size < 1:
        return 0
    raw = int(abs(float(value)) / float(price))
    if lot_size == 1:
        return raw
    return (raw // lot_size) * lot_size


def allocate_equal_notional(
    codes: list[str] | tuple[str, ...],
    sleeve_dollars: float,
    closes: dict[str, float],
    pos: dict,
    *,
    lot_size: int = BOARD_LOT,
) -> list[tuple[str, str, int]]:
    """Return (code, side, qty) rows for equal notional split."""
    out: list[tuple[str, str, int]] = []
    if abs(sleeve_dollars) < 1e-9 or not codes:
        return out
    per = float(sleeve_dollars) / len(codes)
    side = "BUY" if per > 0 else "SELL"
    for c in codes:
        px = float(closes[c])
        qty = lot_qty_from_notional(per, px, lot_size=lot_size)
        if side == "SELL":
            qty = min(qty, held_board_qty(pos, c, lot_size))
        if qty < (1 if lot_size == 1 else lot_size):
            continue
        out.append((c, side, int(qty)))
    return out


def allocate_telecom_sleeve_orders(
    sleeve_dollars: float,
    closes: dict[str, float],
    pos: dict,
    *,
    policy: str = LIVE_TELECOM_ALLOC,
    tel_codes: list[str] | tuple[str, ...] = TEL_DEFAULT,
    lot_size: int = BOARD_LOT,
    scores: dict[str, float] | None = None,
) -> list[tuple[str, str, int]]:
    """Allocate Telecom sleeve trade dollars under a within-sleeve policy.

    Returns list of (code, side, quantity) with board-lot quantities.
    FIN/0050 callers must not use this — Telecom only.
    """
    tel = list(tel_codes)
    if policy == TEL_ALLOC_EQUAL:
        return allocate_equal_notional(tel, sleeve_dollars, closes, pos, lot_size=lot_size)

    score_map = {c: 0.0 for c in tel}
    if scores:
        for c in tel:
            if c in scores and scores[c] is not None:
                score_map[c] = float(scores[c])

    out: list[tuple[str, str, int]] = []

    if policy == TEL_ALLOC_TOP1:
        active = [max(tel, key=lambda c: (score_map[c], -float(closes[c]), c))]
    elif policy == TEL_ALLOC_TOP2_EQUAL:
        active = sorted(tel, key=lambda c: (score_map[c], -float(closes[c]), c), reverse=True)[:2]
    elif policy == TEL_ALLOC_MIN_LOT_PACK:
        active = None
    else:
        raise ValueError(f"unknown telecom within-sleeve policy: {policy}")

    if active is not None:
        for c in tel:
            if c in active:
                continue
            q = held_board_qty(pos, c, lot_size)
            if q >= (1 if lot_size == 1 else lot_size):
                out.append((c, "SELL", int(q)))

    if abs(sleeve_dollars) < 1e-9:
        return out

    if sleeve_dollars < 0:
        holders = [c for c in tel if held_board_qty(pos, c, lot_size) > 0]
        sell_pool = [c for c in (active or holders) if c in holders] or holders
        out.extend(
            allocate_equal_notional(sell_pool, sleeve_dollars, closes, pos, lot_size=lot_size)
        )
        return out

    if policy in (TEL_ALLOC_TOP1, TEL_ALLOC_TOP2_EQUAL):
        out.extend(
            allocate_equal_notional(active, sleeve_dollars, closes, pos, lot_size=lot_size)
        )
        return out

    # TEL_MIN_LOT_PACK: cheapest-first ≥1 張, then dump remainder.
    remaining = float(sleeve_dollars)
    order_names = sorted(tel, key=lambda c: (float(closes[c]), c))
    bought: list[str] = []
    for c in order_names:
        px = float(closes[c])
        lot_cost = px * lot_size
        if lot_cost <= 0 or remaining + 1e-9 < lot_cost:
            continue
        out.append((c, "BUY", int(lot_size)))
        remaining -= lot_cost
        bought.append(c)
    refill = bought if bought else order_names
    for c in refill:
        px = float(closes[c])
        if px <= 0:
            continue
        extra = lot_qty_from_notional(remaining, px, lot_size=lot_size)
        if extra < lot_size:
            continue
        out.append((c, "BUY", int(extra)))
        remaining -= extra * px
    return out


__all__ = [
    "TEL_DEFAULT",
    "TEL_ALLOC_EQUAL",
    "TEL_ALLOC_MIN_LOT_PACK",
    "TEL_ALLOC_TOP1",
    "TEL_ALLOC_TOP2_EQUAL",
    "TEL_ALLOC_POLICIES",
    "LIVE_TELECOM_ALLOC",
    "held_board_qty",
    "lot_qty_from_notional",
    "allocate_equal_notional",
    "allocate_telecom_sleeve_orders",
]
