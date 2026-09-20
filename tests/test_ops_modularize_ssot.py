#!/usr/bin/env python3
"""Guards for ops modularize SSOT: fees, lots, calendar cache, observe helpers."""
from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
CAL_DIR = ROOT / "data" / "calendars"


class FeeUniverseSsot(unittest.TestCase):
    def test_e50_reexports_live_ledger_constants(self) -> None:
        import e50_early_stack_combined_nav as e50
        import live_ledger as ll
        import e16_soft_frozen_base as soft

        self.assertIs(e50.FIN, ll.FIN)
        self.assertIs(e50.TEL, ll.TEL)
        self.assertEqual(e50.FIN, soft.FIN)
        self.assertEqual(e50.BUY_FEE, ll.BUY_FEE)
        self.assertEqual(e50.TAX_STOCK, ll.TAX_STOCK)
        self.assertEqual(e50.SLIP, ll.SLIP)
        src = (SCRIPTS / "e50_early_stack_combined_nav.py").read_text(encoding="utf-8")
        self.assertNotIn("BUY_FEE = 0.001425", src)
        self.assertIn("fees_tax_for", src)
        self.assertIn("cached_load_calendar_window", src)

    def test_fees_tax_for_cost_multiple_override(self) -> None:
        from live_ledger import BUY_FEE, fees_tax_for

        base = fees_tax_for(side="BUY", code="2880", gross=100_000.0)
        scaled = fees_tax_for(
            side="BUY", code="2880", gross=100_000.0, buy_fee=BUY_FEE * 2.0
        )
        self.assertAlmostEqual(scaled, base * 2.0)
        sell = fees_tax_for(side="SELL", code="0050", gross=100_000.0)
        self.assertGreater(sell, fees_tax_for(side="BUY", code="0050", gross=100_000.0))


class LotQtyModule(unittest.TestCase):
    def test_lot_qty_in_tw_share_lots(self) -> None:
        from tw_share_lots import BOARD_LOT, lot_qty
        import e50_early_stack_combined_nav as e50

        self.assertEqual(lot_qty(100_000, 100.0), 1000)
        self.assertEqual(lot_qty(100_000, 100.0, lot_size=1), 1000)
        self.assertIs(e50.lot_qty, lot_qty)
        self.assertEqual(BOARD_LOT, 1000)


class CalendarCache(unittest.TestCase):
    def test_cached_load_y_minus_1(self) -> None:
        from twse_session_sources import (
            cached_load_calendar_window,
            clear_calendar_window_cache,
        )

        clear_calendar_window_cache()
        sessions, settlements = cached_load_calendar_window(
            2026, calendar_dir=CAL_DIR, span=1, soft_miss=False
        )
        self.assertIsNotNone(sessions)
        assert sessions is not None and settlements is not None
        self.assertTrue(any(d.year == 2026 for d in sessions))
        # Adjacent year included only when CSV is pinned in repo.
        y2025 = CAL_DIR / "twse_sessions_2025.csv"
        if y2025.exists():
            self.assertTrue(any(d.year == 2025 for d in sessions + settlements))
        # cache hit returns equal copies
        s2, t2 = cached_load_calendar_window(
            2026, calendar_dir=CAL_DIR, span=1, soft_miss=False
        )
        self.assertEqual(sessions, s2)
        self.assertEqual(settlements, t2)
        soft_s, soft_t = cached_load_calendar_window(
            2099, calendar_dir=CAL_DIR, span=1, soft_miss=True
        )
        self.assertIsNone(soft_s)
        self.assertIsNone(soft_t)


class ObserveHelpers(unittest.TestCase):
    def test_stage_e_from_e22_accounting(self) -> None:
        from e22_dividend_accounting import DEFAULT_BOOKS_VERSION, PRESERVED_CASH_ON_EX
        from ops_observe_helpers import (
            PRESERVED_CASH_ON_EX as P,
            STAGE_E_DEFAULT,
            receivable_total,
            r4_summary,
        )

        self.assertEqual(STAGE_E_DEFAULT, DEFAULT_BOOKS_VERSION)
        self.assertEqual(P, PRESERVED_CASH_ON_EX)
        self.assertEqual(receivable_total({"e22_receivables": {"a": 1.5, "b": 2.5}}), 4.0)
        # live tip R4 present
        r4 = r4_summary(ROOT / "forward/e21")
        self.assertTrue(r4.get("present"))
        self.assertIn("settled_cash_estimate", r4)

    def test_cashflow_and_alert_import_helpers(self) -> None:
        cashflow = (SCRIPTS / "cashflow_three_views_report.py").read_text(encoding="utf-8")
        alert = (SCRIPTS / "ops_alert_scan.py").read_text(encoding="utf-8")
        self.assertIn("from ops_observe_helpers import", cashflow)
        self.assertIn("from ops_observe_helpers import", alert)
        self.assertNotIn('STAGE_E_DEFAULT = "E22_v3_recv_pay_effdelay"', cashflow)
        self.assertNotIn('STAGE_E_DEFAULT = "E22_v3_recv_pay_effdelay"', alert)


if __name__ == "__main__":
    unittest.main()
