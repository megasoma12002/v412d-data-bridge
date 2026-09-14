#!/usr/bin/env python3
"""Live execution session — pending order fills at open (Exact T+1).

Future broker adapter: replace ``fill_pending_at_open`` with exchange acks while
keeping the same fill row schema written via ``live_ledger.append_immutable``.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from live_ledger import BUY_FEE, SELL_FEE, SLIP, TAX_ETF, TAX_STOCK, append_immutable
from tw_share_lots import BOARD_LOT, board_lots


def fill_pending_at_open(
    *,
    state_dir: Path,
    latest: pd.Timestamp,
    open_prices: dict[str, float],
    pos: dict[str, float],
    cash: float,
) -> tuple[dict[str, float], float, list[dict[str, Any]], int, bool]:
    """Fill prior pending orders at today's open. Mutates pos/cash via returns.

    Returns: pos, cash, fills, same_bar_fills, exact_t1_ok
    """
    sdir = Path(state_dir)
    orders_path = sdir / "orders.csv"
    fills: list[dict[str, Any]] = []
    if not orders_path.exists():
        return pos, cash, fills, 0, True

    orders = pd.read_csv(orders_path, dtype={"code": str})
    filled: set[str] = set()
    if (sdir / "fills.csv").exists():
        filled = set(pd.read_csv(sdir / "fills.csv", dtype={"code": str}).fill_id.astype(str))
    pending = orders[
        (~orders.order_id.astype(str).isin(filled)) & (pd.to_datetime(orders.signal_date) < latest)
    ].copy()
    pending["_side_rank"] = pending["side"].map({"SELL": 0, "BUY": 1}).fillna(2)
    pending = pending.sort_values(["signal_date", "_side_rank", "code"])
    for _, o in pending.iterrows():
        orig_q = int(o.quantity)
        q = orig_q
        side = o.side
        fp = open_prices[o.code] * (1 + SLIP if side == "BUY" else 1 - SLIP)
        gross = q * fp
        fee = gross * (
            BUY_FEE if side == "BUY" else SELL_FEE + (TAX_ETF if o.code == "0050" else TAX_STOCK)
        )
        signed = q if side == "BUY" else -q
        if side == "BUY" and gross + fee > cash:
            afford = board_lots(int(cash / (fp * (1 + BUY_FEE))))
            if afford < orig_q:
                continue
            q = afford
            gross = q * fp
            fee = gross * BUY_FEE
            signed = q
        if q < BOARD_LOT or q % BOARD_LOT != 0:
            continue
        pos[o.code] = pos.get(o.code, 0) + signed
        cash += -gross - fee if side == "BUY" else gross - fee
        fills.append(
            {
                "fill_id": o.order_id,
                "signal_date": o.signal_date,
                "fill_date": latest.date().isoformat(),
                "code": o.code,
                "side": side,
                "quantity": q,
                "fill_price": fp,
                "gross": gross,
                "fees_tax": fee,
                "slippage_bp": SLIP * 10000,
            }
        )
    for f in fills:
        append_immutable(sdir / "fills.csv", f, "fill_id")

    same_bar_fills = 0
    for f in fills:
        sig = pd.to_datetime(f["signal_date"]).normalize()
        fill_dt = pd.to_datetime(f["fill_date"]).normalize()
        if fill_dt <= sig:
            same_bar_fills += 1
    exact_t1_ok = same_bar_fills == 0
    return pos, cash, fills, same_bar_fills, exact_t1_ok
