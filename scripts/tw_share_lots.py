#!/usr/bin/env python3
"""Taiwan share-lot terminology and sizing helpers (live + paper).

Canonical definitions (human 2026-09-07):

  一張 (board lot / 整股 unit)
      = 1000 股. Live and paper order/fill sizing trade in whole 張 only.

  零股 (odd lot)
      = 1～999 股. Exchange odd-lot continuous book can trade these, but this
      project's live/paper early-stack does **not** place 零股 orders — only
      whole 張. Holdings may still show 零股 after stock-dividend integer
      floors until sold down in 張 units.

  畸零股 (fractional share)
      = 0.x 股 (strictly less than 1 share), typically from stock dividends.
      Handled by E22_v2s_tw: cash-in-lieu at **面額** (par),
      ``floor(frac × par)`` NTD (yuan truncate). Not traded as shares.

Do not conflate 零股 (1–999) with 畸零股 (0.x).
"""
from __future__ import annotations

BOARD_LOT = 1000  # 一張 = 1000 股
ODD_LOT_MIN = 1
ODD_LOT_MAX = BOARD_LOT - 1  # 零股 upper bound inclusive


def board_lots(shares: float | int) -> int:
    """Floor share count to whole Taiwan board lots (整股 張 → 股數)."""
    return BOARD_LOT * int(max(0.0, float(shares)) // BOARD_LOT)


def is_board_lot_qty(qty: float | int) -> bool:
    """True iff qty is a positive multiple of 一張 (or zero)."""
    q = int(qty)
    if q == 0:
        return True
    return q >= BOARD_LOT and q % BOARD_LOT == 0


def is_odd_lot_qty(qty: float | int) -> bool:
    """True iff qty is 零股: integer in [1, 999]."""
    try:
        q = int(qty)
    except (TypeError, ValueError):
        return False
    return ODD_LOT_MIN <= q <= ODD_LOT_MAX and float(qty) == float(q)


def is_fractional_share(qty: float) -> bool:
    """True iff qty is 畸零股: 0 < qty < 1."""
    x = float(qty)
    return 0.0 < x < 1.0


__all__ = [
    "BOARD_LOT",
    "ODD_LOT_MIN",
    "ODD_LOT_MAX",
    "board_lots",
    "is_board_lot_qty",
    "is_odd_lot_qty",
    "is_fractional_share",
]
