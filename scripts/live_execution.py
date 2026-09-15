#!/usr/bin/env python3
"""Live execution session — pending order fills at open (Exact T+1).

Fill ports share one row schema written via ``live_ledger.append_immutable``.
Default port is paper Exact T+1 (open + slip/fee). Broker adapters plug in later
behind the same ``FillPort`` contract; dry-run / live routing need ACCEPT.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Protocol

import pandas as pd

from live_ledger import BUY_FEE, SELL_FEE, SLIP, TAX_ETF, TAX_STOCK, append_immutable
from tw_share_lots import BOARD_LOT, board_lots

# Canonical fill row keys (broker ports must map acks into this schema).
FILL_ROW_KEYS = (
    "fill_id",
    "signal_date",
    "fill_date",
    "code",
    "side",
    "quantity",
    "fill_price",
    "gross",
    "fees_tax",
    "slippage_bp",
)

DEFAULT_FILL_PORT = "paper"
ENV_FILL_PORT = "E21_FILL_PORT"


class FillPort(Protocol):
    """Pluggable fill backend for pending orders."""

    name: str

    def fill_pending(
        self,
        *,
        state_dir: Path,
        latest: pd.Timestamp,
        open_prices: dict[str, float],
        pos: dict[str, float],
        cash: float,
    ) -> tuple[dict[str, float], float, list[dict[str, Any]], int, bool]:
        """Return pos, cash, fills, same_bar_fills, exact_t1_ok."""
        ...


def _exact_t1_stats(fills: list[dict[str, Any]]) -> tuple[int, bool]:
    same_bar_fills = 0
    for f in fills:
        sig = pd.to_datetime(f["signal_date"]).normalize()
        fill_dt = pd.to_datetime(f["fill_date"]).normalize()
        if fill_dt <= sig:
            same_bar_fills += 1
    return same_bar_fills, same_bar_fills == 0


def _iter_pending(state_dir: Path, latest: pd.Timestamp) -> pd.DataFrame:
    sdir = Path(state_dir)
    orders_path = sdir / "orders.csv"
    if not orders_path.exists():
        return pd.DataFrame()
    orders = pd.read_csv(orders_path, dtype={"code": str})
    filled: set[str] = set()
    if (sdir / "fills.csv").exists():
        filled = set(pd.read_csv(sdir / "fills.csv", dtype={"code": str}).fill_id.astype(str))
    pending = orders[
        (~orders.order_id.astype(str).isin(filled)) & (pd.to_datetime(orders.signal_date) < latest)
    ].copy()
    pending["_side_rank"] = pending["side"].map({"SELL": 0, "BUY": 1}).fillna(2)
    return pending.sort_values(["signal_date", "_side_rank", "code"])


def _paper_fill_rows(
    *,
    pending: pd.DataFrame,
    latest: pd.Timestamp,
    open_prices: dict[str, float],
    pos: dict[str, float],
    cash: float,
) -> tuple[dict[str, float], float, list[dict[str, Any]]]:
    fills: list[dict[str, Any]] = []
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
    return pos, cash, fills


class PaperOpenFillPort:
    """Paper Exact T+1: fill prior pending at today's open + slip/fee model."""

    name = "paper"

    def fill_pending(
        self,
        *,
        state_dir: Path,
        latest: pd.Timestamp,
        open_prices: dict[str, float],
        pos: dict[str, float],
        cash: float,
    ) -> tuple[dict[str, float], float, list[dict[str, Any]], int, bool]:
        pending = _iter_pending(state_dir, latest)
        if pending.empty:
            return pos, cash, [], 0, True
        pos, cash, fills = _paper_fill_rows(
            pending=pending,
            latest=latest,
            open_prices=open_prices,
            pos=pos,
            cash=cash,
        )
        sdir = Path(state_dir)
        for f in fills:
            append_immutable(sdir / "fills.csv", f, "fill_id")
        same_bar, ok = _exact_t1_stats(fills)
        return pos, cash, fills, same_bar, ok


class DryRunFillPort:
    """Shadow port: same pricing as paper, writes under ``broker_dryrun/`` only.

    Does **not** append to live ``fills.csv`` and does **not** mutate portfolio
    for the live session — used to diff broker mapping later.
    """

    name = "dry_run"

    def fill_pending(
        self,
        *,
        state_dir: Path,
        latest: pd.Timestamp,
        open_prices: dict[str, float],
        pos: dict[str, float],
        cash: float,
    ) -> tuple[dict[str, float], float, list[dict[str, Any]], int, bool]:
        import json

        pending = _iter_pending(state_dir, latest)
        # Work on copies so live pos/cash stay unchanged.
        pos_shadow = dict(pos)
        cash_shadow = float(cash)
        if pending.empty:
            fills: list[dict[str, Any]] = []
        else:
            pos_shadow, cash_shadow, fills = _paper_fill_rows(
                pending=pending,
                latest=latest,
                open_prices=open_prices,
                pos=pos_shadow,
                cash=cash_shadow,
            )
        out = Path(state_dir) / "broker_dryrun"
        out.mkdir(parents=True, exist_ok=True)
        payload = {
            "port": self.name,
            "fill_date": latest.date().isoformat(),
            "n_fills": len(fills),
            "fills": fills,
            "live_fills_written": False,
            "note": "Shadow only — live fills.csv / portfolio_state untouched",
        }
        (out / f"fills_{latest.date().isoformat()}.json").write_text(
            json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8"
        )
        same_bar, ok = _exact_t1_stats(fills)
        # Return original pos/cash so pipeline does not book dry-run fills.
        return pos, cash, fills, same_bar, ok


_PORTS: dict[str, type] = {
    PaperOpenFillPort.name: PaperOpenFillPort,
    DryRunFillPort.name: DryRunFillPort,
}


def resolve_fill_port(name: str | None = None) -> FillPort:
    """Resolve fill port from explicit name, else ``E21_FILL_PORT``, else paper."""
    raw = (name or os.environ.get(ENV_FILL_PORT) or DEFAULT_FILL_PORT).strip().lower()
    if raw not in _PORTS:
        known = ", ".join(sorted(_PORTS))
        raise SystemExit(f"Unknown fill port {raw!r}; known: {known}")
    return _PORTS[raw]()


def fill_pending_at_open(
    *,
    state_dir: Path,
    latest: pd.Timestamp,
    open_prices: dict[str, float],
    pos: dict[str, float],
    cash: float,
    fill_port: str | FillPort | None = None,
) -> tuple[dict[str, float], float, list[dict[str, Any]], int, bool]:
    """Fill prior pending orders. Default port = paper Exact T+1 (unchanged)."""
    port: FillPort
    if isinstance(fill_port, str) or fill_port is None:
        port = resolve_fill_port(fill_port)
    else:
        port = fill_port
    return port.fill_pending(
        state_dir=state_dir,
        latest=latest,
        open_prices=open_prices,
        pos=pos,
        cash=cash,
    )
