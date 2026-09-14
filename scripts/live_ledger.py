#!/usr/bin/env python3
"""Live ledger store — immutable CSV append + holdings helpers.

Execution/broker adapters should eventually write fills through the same
append_immutable contract. Soft-Frozen / live flags are not owned here.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from e16_soft_frozen_base import FIN, TEL
from portfolio_capital import DEFAULT_CAPITAL

ALL = FIN + TEL + ["0050"]

# Cost model shared by live session (paper Exact T+1). Broker port may override later.
BUY_FEE = 0.001425 * 0.6
SELL_FEE = 0.001425 * 0.6
TAX_STOCK = 0.003
TAX_ETF = 0.001
SLIP = 0.0005


def append_immutable(path: Path | str, row: dict[str, Any], key: str) -> bool:
    """Append one row if ``key`` is new. Never rewrite history. Returns True if written."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    new = pd.DataFrame([row])
    if p.exists():
        old = pd.read_csv(p, dtype={"code": str})
        hit = old[old[key].astype(str) == str(row[key])]
        if len(hit):
            return False
        new = pd.concat([old, new], ignore_index=True)
    new.to_csv(p, index=False)
    return True


def holdings(
    state: dict[str, Any],
    prices: dict[str, float],
    *,
    capital: float = DEFAULT_CAPITAL,
) -> tuple[dict[str, float], float, dict[str, float], float]:
    pos = {c: float(state.get("positions", {}).get(c, 0)) for c in ALL}
    cash = float(state.get("cash", capital))
    vals = {c: pos[c] * prices[c] for c in ALL}
    nav = cash + sum(vals.values())
    return pos, cash, vals, nav


class LedgerStore:
    """Filesystem ledger under a state directory (canonical: forward/e21)."""

    def __init__(self, state_dir: Path | str):
        self.state_dir = Path(state_dir)

    def path(self, name: str) -> Path:
        return self.state_dir / name

    def append(self, name: str, row: dict[str, Any], key: str) -> bool:
        return append_immutable(self.path(name), row, key)
