#!/usr/bin/env python3
"""E16 core API surface (thin wrapper — not a new frozen version).

G5 ticket T4: give G2 / research consumers a stable import name for E16
membership constants and causal target reconstruction without editing
``scripts/e21_forward_pipeline.py``.

Implementation re-exports from ``e50_early_stack_combined_nav`` (which already
mirrors E21 feature logic as a read-only copy). Does **not** promote E16,
does **not** touch ``forward/e21/``.
"""
from __future__ import annotations

from e50_early_stack_combined_nav import (
    ALL,
    BUY_FEE,
    CAPITAL,
    FIN,
    SELL_FEE,
    SLIP,
    TAX_ETF,
    TAX_STOCK,
    TEL,
    WARMUP_DAYS,
    e16_features,
    lot_qty,
    simulate_core,
)

MODULE_ID = "E16_CORE_API"
MODULE_STATUS = "WRAPPER_NOT_A_FROZEN_VERSION"
WRAPS = "scripts/e50_early_stack_combined_nav.py"
OFFICIAL_LIVE = "scripts/e21_forward_pipeline.py / forward/e21/"

__all__ = [
    "MODULE_ID",
    "MODULE_STATUS",
    "WRAPS",
    "OFFICIAL_LIVE",
    "FIN",
    "TEL",
    "ALL",
    "BUY_FEE",
    "SELL_FEE",
    "TAX_STOCK",
    "TAX_ETF",
    "SLIP",
    "CAPITAL",
    "WARMUP_DAYS",
    "e16_features",
    "lot_qty",
    "simulate_core",
]


if __name__ == "__main__":
    import json

    print(
        json.dumps(
            {
                "module_id": MODULE_ID,
                "status": MODULE_STATUS,
                "wraps": WRAPS,
                "official_live": OFFICIAL_LIVE,
                "universe": ALL,
            },
            indent=2,
        )
    )
