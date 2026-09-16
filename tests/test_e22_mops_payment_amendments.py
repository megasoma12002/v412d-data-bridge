#!/usr/bin/env python3
"""Tests for D4 MOPS payment amendment overlay."""
from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

from e22_mops_payment_amendments import (
    amendments_from_mops_vs_ledger,
    load_amendments,
    lookup_amendment,
    parse_amendment_text,
    save_amendments,
)
from twse_dividend_delay_estimate import estimate_event
from twse_session_sources import DayRecord, session_dates, settlement_dates
import e22_dividend_accounting as formal
import e22_v3_sandbox_books as sandbox


def _row(d: date, is_session: bool, kind: str, is_settlement: bool | None = None) -> DayRecord:
    return DayRecord(date=d, is_session=is_session, kind=kind, is_settlement=is_settlement)


class ParseAmendmentTests(unittest.TestCase):
    def test_parse_chinese_postpone(self) -> None:
        text = "原訂現金股利發放日為115年7月10日，因颱風顺延至7月13日辦理。"
        rows = parse_amendment_text(text, default_code="2891")
        self.assertTrue(rows)
        self.assertEqual(rows[0]["original_payment_date"], "2026-07-10")
        self.assertEqual(rows[0]["amended_payment_date"], "2026-07-13")
        self.assertEqual(rows[0]["code"], "2891")

    def test_parse_iso_arrow(self) -> None:
        text = "原發放日 2026-07-10 → 2026-07-13"
        rows = parse_amendment_text(text, default_code="2330")
        self.assertEqual(rows[0]["amended_payment_date"], "2026-07-13")

    def test_mops_vs_ledger_diff(self) -> None:
        rows = amendments_from_mops_vs_ledger(
            [{"code": "2891", "cash_ex_date": "2026-07-10", "cash_payment_date": "2026-07-13"}],
            [{"code": "2891", "cash_ex_date": "2026-07-10", "cash_payment_date": "2026-07-10"}],
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["amended_payment_date"], "2026-07-13")


class OverlayWireTests(unittest.TestCase):
    def test_estimate_uses_overlay(self) -> None:
        days = [
            _row(date(2026, 7, 9), True, "SESSION"),
            _row(date(2026, 7, 10), False, "CLOSED_TYPHOON_OR_NODATA", False),
            _row(date(2026, 7, 13), True, "SESSION"),
        ]
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "amd.csv"
            save_amendments(
                [
                    {
                        "code": "2891",
                        "original_payment_date": "2026-07-10",
                        "amended_payment_date": "2026-07-13",
                        "source": "fixture",
                        "note": "test",
                    }
                ],
                p,
            )
            amd = load_amendments(p)
            r = estimate_event(
                {
                    "code": "2891",
                    "cash_ex_date": "2026-07-09",
                    "cash_payment_date": "2026-07-10",
                },
                sessions=session_dates(days),
                settlements=settlement_dates(days),
                mops_amendments=amd,
            )
            self.assertEqual(r["effective_cash_payment"], "2026-07-13")
            self.assertIn("mops_amendment", r["notes"])

    def test_effdelay_sandbox_mops_wins(self) -> None:
        days = [
            _row(date(2026, 7, 9), True, "SESSION"),
            _row(date(2026, 7, 10), False, "CLOSED_TYPHOON_OR_NODATA", False),
            _row(date(2026, 7, 13), True, "SESSION"),
        ]
        amd = {("2891", "2026-07-10"): "2026-07-13"}
        ev = formal.DivEvent(
            code="2891",
            kind="cash",
            ex_date="2026-07-09",
            amount=1.0,
            payment_date="2026-07-10",
        )
        pos, cash, recv, _ = sandbox.apply_sandbox_for_date(
            "2026-07-09",
            {"2891": 1000.0},
            0.0,
            {},
            [ev],
            version=sandbox.E22_V3_RECV_PAY_EFFDELAY,
            session_dates=session_dates(days),
            settlement_dates=settlement_dates(days),
            mops_amendments=amd,
        )
        self.assertAlmostEqual(sum(recv.values()), 1000.0)
        _, cash2, recv2, res2 = sandbox.apply_sandbox_for_date(
            "2026-07-13",
            pos,
            cash,
            recv,
            [ev],
            version=sandbox.E22_V3_RECV_PAY_EFFDELAY,
            session_dates=session_dates(days),
            settlement_dates=settlement_dates(days),
            mops_amendments=amd,
        )
        self.assertAlmostEqual(cash2, 1000.0)
        self.assertEqual(recv2, {})
        self.assertEqual(res2.details[0]["effective_payment"], "2026-07-13")

    def test_parse_stock_dividend_leg(self) -> None:
        text = "原訂股票股利發放日為115年7月10日，因颱風顺延至7月13日辦理。"
        rows = parse_amendment_text(text, default_code="2330")
        self.assertTrue(rows)
        self.assertEqual(rows[0]["leg"], "stock")
        self.assertEqual(rows[0]["amended_payment_date"], "2026-07-13")

    def test_stock_leg_lookup(self) -> None:
        amd = {("2330", "2026-07-10", "stock"): "2026-07-13"}
        self.assertEqual(
            lookup_amendment(amd, "2330", "2026-07-10", leg="stock"),
            date(2026, 7, 13),
        )
        self.assertIsNone(lookup_amendment(amd, "2330", "2026-07-10", leg="cash"))

    def test_lookup(self) -> None:
        amd = {("2891", "2026-07-10"): "2026-07-13"}
        self.assertEqual(lookup_amendment(amd, "2891", "2026-07-10"), date(2026, 7, 13))
        self.assertIsNone(lookup_amendment(amd, "2891", "2026-08-07"))


if __name__ == "__main__":
    unittest.main()
