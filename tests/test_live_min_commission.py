#!/usr/bin/env python3
"""Tests for live fee model — min commission floor (ACCEPT gap close)."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from live_execution import PaperOpenFillPort
from live_ledger import (
    BUY_FEE,
    MIN_COMMISSION,
    SELL_FEE,
    TAX_ETF,
    TAX_STOCK,
    commission,
    fees_tax_for,
    max_affordable_buy_qty,
)
from tw_share_lots import BOARD_LOT


class CommissionHelperTests(unittest.TestCase):
    def test_rate_binds_on_large_gross(self) -> None:
        gross = 1_000_000.0
        self.assertAlmostEqual(commission(gross, BUY_FEE), gross * BUY_FEE)
        self.assertGreater(gross * BUY_FEE, MIN_COMMISSION)

    def test_floor_binds_on_small_gross(self) -> None:
        # 1000 * 10 = 10_000 → rate * 0.000855 = 8.55 < 20
        gross = 10_000.0
        self.assertAlmostEqual(commission(gross, BUY_FEE), MIN_COMMISSION)
        self.assertLess(gross * BUY_FEE, MIN_COMMISSION)

    def test_zero_rate_no_floor(self) -> None:
        self.assertEqual(commission(10_000.0, 0.0), 0.0)

    def test_buy_fees_tax(self) -> None:
        self.assertAlmostEqual(fees_tax_for(side="BUY", code="2330", gross=10_000.0), 20.0)

    def test_sell_fees_tax_includes_stock_tax(self) -> None:
        gross = 10_000.0
        got = fees_tax_for(side="SELL", code="2330", gross=gross)
        self.assertAlmostEqual(got, MIN_COMMISSION + gross * TAX_STOCK)

    def test_sell_etf_tax(self) -> None:
        gross = 10_000.0
        got = fees_tax_for(side="SELL", code="0050", gross=gross)
        self.assertAlmostEqual(got, MIN_COMMISSION + gross * TAX_ETF)

    def test_afford_under_min_commission(self) -> None:
        # Cash just enough for 1000@10 + NT$20 floor
        fp = 10.0
        cash = 10_000.0 + MIN_COMMISSION
        self.assertEqual(max_affordable_buy_qty(cash, fp), BOARD_LOT)
        self.assertEqual(max_affordable_buy_qty(cash - 1.0, fp), 0)


class PaperFillMinCommissionTests(unittest.TestCase):
    def test_paper_fill_applies_floor(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            pd.DataFrame(
                [
                    {
                        "order_id": "o1",
                        "signal_date": "2026-09-15",
                        "code": "2880",
                        "side": "BUY",
                        "quantity": BOARD_LOT,
                    }
                ]
            ).to_csv(sdir / "orders.csv", index=False)
            port = PaperOpenFillPort()
            # open 10 → slipped buy price = 10 * 1.0005 = 10.005
            # gross ≈ 10005; rate fee ≈ 8.55 → floor 20
            pos, cash, fills, _, ok = port.fill_pending(
                state_dir=sdir,
                latest=pd.Timestamp("2026-09-16"),
                open_prices={"2880": 10.0},
                pos={},
                cash=1_000_000.0,
            )
            self.assertTrue(ok)
            self.assertEqual(len(fills), 1)
            self.assertAlmostEqual(fills[0]["fees_tax"], MIN_COMMISSION)
            self.assertAlmostEqual(cash, 1_000_000.0 - fills[0]["gross"] - MIN_COMMISSION)
            # Paper port defers fills.csv to pipeline day-commit.
            self.assertFalse((sdir / "fills.csv").exists())


if __name__ == "__main__":
    unittest.main()
