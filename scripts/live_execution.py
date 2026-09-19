#!/usr/bin/env python3
"""Live execution session — facade for fill ports (Exact T+1).

Implementation split for cleanliness:
  - ``live_fill_core`` — paper / dry_run + pending helpers
  - ``live_fill_broker`` — BrokerPreflightFillPort

Stable imports remain ``from live_execution import …``. Soft-Frozen KEEP;
``afford < orig_q`` live skip policy lives in ``live_fill_core._paper_fill_rows``.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pandas as pd

from live_fill_broker import BrokerPreflightFillPort
from live_fill_core import (
    DEFAULT_FILL_PORT,
    ENV_FILL_PORT,
    FILL_ROW_KEYS,
    DryRunFillPort,
    FillPort,
    PaperOpenFillPort,
    _exact_t1_stats,
    _iter_pending,
    _paper_fill_rows,
    sort_pending_sell_before_buy,
    sort_rows_sell_before_buy,
)

# Re-export broker daily budget constant used by tests/ctors.
from broker_safety import DEFAULT_DAILY_LIVE_FILL_BUDGET  # noqa: F401

_PORTS: dict[str, type] = {
    PaperOpenFillPort.name: PaperOpenFillPort,
    DryRunFillPort.name: DryRunFillPort,
    BrokerPreflightFillPort.name: BrokerPreflightFillPort,
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


__all__ = [
    "DEFAULT_DAILY_LIVE_FILL_BUDGET",
    "DEFAULT_FILL_PORT",
    "ENV_FILL_PORT",
    "FILL_ROW_KEYS",
    "BrokerPreflightFillPort",
    "DryRunFillPort",
    "FillPort",
    "PaperOpenFillPort",
    "_exact_t1_stats",
    "_iter_pending",
    "_paper_fill_rows",
    "fill_pending_at_open",
    "resolve_fill_port",
    "sort_pending_sell_before_buy",
    "sort_rows_sell_before_buy",
]
