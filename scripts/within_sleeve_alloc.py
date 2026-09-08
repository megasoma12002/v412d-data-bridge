#!/usr/bin/env python3
"""Generic within-sleeve name allocation (paper research + optional live).

Used for Financial / Telecom multi-name sleeves under board-lot 1000.
Soft-Frozen *sleeve clips* are unchanged — this only splits sleeve trade dollars
across member codes.
"""
from __future__ import annotations

from tw_share_lots import BOARD_LOT, board_lots

POLICY_EQUAL = "EQUAL"
POLICY_MIN_LOT_PACK = "MIN_LOT_PACK"
POLICY_SCORE_LOT_PACK = "SCORE_LOT_PACK"
POLICY_DIVERSIFY_PACK = "DIVERSIFY_PACK"
POLICY_TOP1 = "TOP1"
POLICY_TOP2_EQUAL = "TOP2_EQUAL"

# Predeclared ids
FIN_EQUAL = "FIN_EQUAL"
FIN_MIN_LOT_PACK = "FIN_MIN_LOT_PACK"
FIN_TOP1 = "FIN_TOP1"
FIN_TOP2_EQUAL = "FIN_TOP2_EQUAL"
FIN_ALLOC_POLICIES = (FIN_EQUAL, FIN_MIN_LOT_PACK, FIN_TOP1, FIN_TOP2_EQUAL)

TEL_EQUAL = "TEL_EQUAL"
TEL_MIN_LOT_PACK = "TEL_MIN_LOT_PACK"
TEL_SCORE_LOT_PACK = "TEL_SCORE_LOT_PACK"
TEL_DIVERSIFY_PACK = "TEL_DIVERSIFY_PACK"
TEL_TOP1 = "TEL_TOP1"
TEL_TOP2_EQUAL = "TEL_TOP2_EQUAL"
TEL_ALLOC_POLICIES = (
    TEL_EQUAL,
    TEL_MIN_LOT_PACK,
    TEL_SCORE_LOT_PACK,
    TEL_DIVERSIFY_PACK,
    TEL_TOP1,
    TEL_TOP2_EQUAL,
)


def policy_kind(policy_id: str) -> str:
    if policy_id in (FIN_EQUAL, TEL_EQUAL):
        return POLICY_EQUAL
    if policy_id.endswith("_SCORE_LOT_PACK"):
        return POLICY_SCORE_LOT_PACK
    if policy_id.endswith("_DIVERSIFY_PACK"):
        return POLICY_DIVERSIFY_PACK
    if policy_id.endswith("_MIN_LOT_PACK"):
        return POLICY_MIN_LOT_PACK
    if policy_id.endswith("_TOP1"):
        return POLICY_TOP1
    if policy_id.endswith("_TOP2_EQUAL"):
        return POLICY_TOP2_EQUAL
    raise ValueError(f"unknown within-sleeve policy id: {policy_id}")


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


def _coalesce_orders(rows: list[tuple[str, str, int]]) -> list[tuple[str, str, int]]:
    acc: dict[tuple[str, str], int] = {}
    for code, side, qty in rows:
        if qty < 1:
            continue
        key = (code, side)
        acc[key] = acc.get(key, 0) + int(qty)
    side_rank = {"SELL": 0, "BUY": 1}
    keys = sorted(acc.keys(), key=lambda k: (side_rank.get(k[1], 9), k[0]))
    return [(c, s, acc[(c, s)]) for c, s in keys]


def allocate_equal_notional(
    codes: list[str] | tuple[str, ...],
    sleeve_dollars: float,
    closes: dict[str, float],
    pos: dict,
    *,
    lot_size: int = BOARD_LOT,
) -> list[tuple[str, str, int]]:
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


def _pack_one_lot_then_dump(
    names: list[str],
    sleeve_dollars: float,
    closes: dict[str, float],
    *,
    lot_size: int,
    order_names: list[str],
    dump_equal: bool,
) -> list[tuple[str, str, int]]:
    """≥1 張 along order_names; remainder dump to first or equal-split among bought."""
    out: list[tuple[str, str, int]] = []
    remaining = float(sleeve_dollars)
    bought: list[str] = []
    for c in order_names:
        px = float(closes[c])
        lot_cost = px * lot_size
        if lot_cost <= 0 or remaining + 1e-9 < lot_cost:
            continue
        out.append((c, "BUY", int(lot_size)))
        remaining -= lot_cost
        bought.append(c)
    if remaining < lot_size * min(float(closes[c]) for c in names if float(closes[c]) > 0):
        return out
    if dump_equal and bought:
        out.extend(
            allocate_equal_notional(bought, remaining, closes, {c: 0 for c in bought}, lot_size=lot_size)
        )
        return out
    # dump into order (first gets most)
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


def allocate_sleeve_orders(
    sleeve_dollars: float,
    closes: dict[str, float],
    pos: dict,
    *,
    policy_id: str,
    codes: list[str] | tuple[str, ...],
    lot_size: int = BOARD_LOT,
    scores: dict[str, float] | None = None,
) -> list[tuple[str, str, int]]:
    """Allocate one sleeve's trade dollars across member codes.

    Returns coalesced (code, side, qty) rows (board-lot).
    """
    names = list(codes)
    kind = policy_kind(policy_id)
    if kind == POLICY_EQUAL:
        return allocate_equal_notional(names, sleeve_dollars, closes, pos, lot_size=lot_size)

    score_map = {c: 0.0 for c in names}
    if scores:
        for c in names:
            if c in scores and scores[c] is not None:
                score_map[c] = float(scores[c])

    out: list[tuple[str, str, int]] = []
    if kind == POLICY_TOP1:
        active = [max(names, key=lambda c: (score_map[c], -float(closes[c]), c))]
    elif kind == POLICY_TOP2_EQUAL:
        active = sorted(names, key=lambda c: (score_map[c], -float(closes[c]), c), reverse=True)[:2]
    elif kind in (POLICY_MIN_LOT_PACK, POLICY_SCORE_LOT_PACK, POLICY_DIVERSIFY_PACK):
        active = None
    else:
        raise ValueError(f"unsupported policy kind: {kind}")

    if active is not None:
        for c in names:
            if c in active:
                continue
            q = held_board_qty(pos, c, lot_size)
            if q >= (1 if lot_size == 1 else lot_size):
                out.append((c, "SELL", int(q)))

    if abs(sleeve_dollars) < 1e-9:
        return _coalesce_orders(out)

    if sleeve_dollars < 0:
        holders = [c for c in names if held_board_qty(pos, c, lot_size) > 0]
        sell_pool = [c for c in (active or holders) if c in holders] or holders
        out.extend(
            allocate_equal_notional(sell_pool, sleeve_dollars, closes, pos, lot_size=lot_size)
        )
        return _coalesce_orders(out)

    if kind in (POLICY_TOP1, POLICY_TOP2_EQUAL):
        out.extend(
            allocate_equal_notional(active, sleeve_dollars, closes, pos, lot_size=lot_size)
        )
        return _coalesce_orders(out)

    if kind == POLICY_SCORE_LOT_PACK:
        order_names = sorted(names, key=lambda c: (score_map[c], -float(closes[c]), c), reverse=True)
        out.extend(
            _pack_one_lot_then_dump(
                names, sleeve_dollars, closes, lot_size=lot_size, order_names=order_names, dump_equal=False
            )
        )
        return _coalesce_orders(out)

    if kind == POLICY_DIVERSIFY_PACK:
        # Prefer covering as many names as possible (cheap-first for affordability),
        # then equal-split remainder among names that already have ≥1 張.
        order_names = sorted(names, key=lambda c: (float(closes[c]), c))
        out.extend(
            _pack_one_lot_then_dump(
                names, sleeve_dollars, closes, lot_size=lot_size, order_names=order_names, dump_equal=True
            )
        )
        return _coalesce_orders(out)

    # MIN_LOT_PACK (cheapest-first, dump remainder into cheapest)
    order_names = sorted(names, key=lambda c: (float(closes[c]), c))
    out.extend(
        _pack_one_lot_then_dump(
            names, sleeve_dollars, closes, lot_size=lot_size, order_names=order_names, dump_equal=False
        )
    )
    return _coalesce_orders(out)


def build_name_scores(market, codes: list[str] | tuple[str, ...]):
    """Causal within-sleeve name scores from adj_close momentum (TOP1/TOP2/SCORE pack)."""
    import numpy as np
    import pandas as pd

    m = market.copy()
    m["date"] = pd.to_datetime(m["date"])
    adj = (
        m.pivot(index="date", columns="code", values="adj_close")
        .sort_index()
        .ffill()
    )
    for c in codes:
        if c not in adj.columns:
            raise ValueError(f"missing code {c} in market adj_close")
    panel = adj[list(codes)]
    rets = panel.pct_change()
    m20 = rets.rolling(20, min_periods=10).mean()
    m60 = rets.rolling(60, min_periods=20).mean()

    def _xz(df: pd.DataFrame) -> pd.DataFrame:
        mu = df.mean(axis=1)
        sd = df.std(axis=1).replace(0.0, np.nan)
        return df.sub(mu, axis=0).div(sd, axis=0).fillna(0.0)

    return (0.5 * _xz(m20) + 0.5 * _xz(m60)).clip(-3.0, 3.0)


__all__ = [
    "POLICY_EQUAL",
    "POLICY_MIN_LOT_PACK",
    "POLICY_SCORE_LOT_PACK",
    "POLICY_DIVERSIFY_PACK",
    "POLICY_TOP1",
    "POLICY_TOP2_EQUAL",
    "FIN_EQUAL",
    "FIN_MIN_LOT_PACK",
    "FIN_TOP1",
    "FIN_TOP2_EQUAL",
    "FIN_ALLOC_POLICIES",
    "TEL_EQUAL",
    "TEL_MIN_LOT_PACK",
    "TEL_SCORE_LOT_PACK",
    "TEL_DIVERSIFY_PACK",
    "TEL_TOP1",
    "TEL_TOP2_EQUAL",
    "TEL_ALLOC_POLICIES",
    "policy_kind",
    "held_board_qty",
    "lot_qty_from_notional",
    "allocate_equal_notional",
    "allocate_sleeve_orders",
    "build_name_scores",
]
