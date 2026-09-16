#!/usr/bin/env python3
"""Tests for S3 TWSE same-day ex-list overlay."""
from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

from twse_dividend_delay_estimate import estimate_event
from twse_same_day_ex_list import (
    amendments_from_twse_vs_ledger,
    load_ex_amendments,
    lookup_ex_amendment,
    parse_twt48u_rows,
    parse_twt49u_rows,
    roc_date_to_iso,
    save_ex_amendments,
)
from twse_session_sources import DayRecord, session_dates, settlement_dates


class RocParseTests(unittest.TestCase):
    def test_roc_and_detail(self) -> None:
        self.assertEqual(roc_date_to_iso("115年07月10日"), "2026-07-10")
        self.assertEqual(roc_date_to_iso("2891,20260713"), "2026-07-13")
        self.assertEqual(roc_date_to_iso("2026-07-13"), "2026-07-13")


class ParseTwseTests(unittest.TestCase):
    def test_twt48u(self) -> None:
        rows = parse_twt48u_rows(
            {
                "data": [
                    [
                        "115年07月13日",
                        "2891",
                        "中信金",
                        "息",
                        "0",
                        "0",
                        "0",
                        "1.0",
                        "2891,20260713",
                    ]
                ]
            }
        )
        self.assertEqual(rows[0]["code"], "2891")
        self.assertEqual(rows[0]["ex_date"], "2026-07-13")
        self.assertEqual(rows[0]["source"], "twt48u")

    def test_twt49u(self) -> None:
        rows = parse_twt49u_rows(
            {
                "data": [
                    [
                        "115年07月13日",
                        "2891",
                        "中信金",
                        "30",
                        "29",
                        "1",
                        "息",
                        "0",
                        "0",
                        "0",
                        "0",
                        "2891,20260713",
                    ]
                ]
            }
        )
        self.assertEqual(rows[0]["ex_date"], "2026-07-13")
        self.assertEqual(rows[0]["source"], "twt49u")


class AmendmentDiffTests(unittest.TestCase):
    def test_typhoon_postpone_diff(self) -> None:
        twse = [{"code": "2891", "ex_date": "2026-07-13", "ex_kind": "息", "source": "twt49u"}]
        ledger = [{"code": "2891", "cash_ex_date": "2026-07-10", "stock_ex_date": ""}]
        rows = amendments_from_twse_vs_ledger(twse, ledger)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["amended_ex_date"], "2026-07-13")
        self.assertEqual(rows[0]["leg"], "cash")


class OverlayWireTests(unittest.TestCase):
    def test_estimate_uses_ex_overlay(self) -> None:
        days = [
            DayRecord(date=date(2026, 7, 9), is_session=True, kind="SESSION"),
            DayRecord(
                date=date(2026, 7, 10),
                is_session=False,
                kind="CLOSED_TYPHOON_OR_NODATA",
                is_settlement=False,
            ),
            DayRecord(date=date(2026, 7, 13), is_session=True, kind="SESSION"),
        ]
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "ex.csv"
            save_ex_amendments(
                [
                    {
                        "code": "2891",
                        "original_ex_date": "2026-07-10",
                        "amended_ex_date": "2026-07-13",
                        "leg": "cash",
                        "source": "fixture",
                        "note": "test",
                    }
                ],
                p,
            )
            amd = load_ex_amendments(p)
            r = estimate_event(
                {
                    "code": "2891",
                    "cash_ex_date": "2026-07-10",
                    "cash_payment_date": "2026-08-07",
                },
                sessions=session_dates(days),
                settlements=settlement_dates(days),
                ex_amendments=amd,
            )
            self.assertEqual(r["raw_cash_ex_date"], "2026-07-10")
            self.assertEqual(r["effective_cash_ex_trade"], "2026-07-13")
            self.assertEqual(r["delay_cash_ex_days"], "3")
            self.assertIn("ex_date_amendment", r["notes"])

    def test_lookup(self) -> None:
        amd = {("2891", "2026-07-10", "cash"): "2026-07-13"}
        self.assertEqual(
            lookup_ex_amendment(amd, "2891", "2026-07-10", leg="cash"),
            date(2026, 7, 13),
        )


if __name__ == "__main__":
    unittest.main()
