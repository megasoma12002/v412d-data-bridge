#!/usr/bin/env python3
"""Stage-E: live DEFAULT E22_v3_recv_pay_effdelay via books router."""
from __future__ import annotations

import unittest
from datetime import date

import e22_dividend_accounting as formal
from e22_books_apply import apply_books_for_date, books_manifest, is_sandbox_version
from e22_v3_sandbox_books import E22_V3_RECV_PAY_EFFDELAY
from live_ledger import holdings
from twse_session_sources import DayRecord, session_dates, settlement_dates


def _days() -> list[DayRecord]:
    return [
        DayRecord(date=date(2026, 7, 9), is_session=True, kind="SESSION"),
        DayRecord(
            date=date(2026, 7, 10),
            is_session=False,
            kind="CLOSED_TYPHOON_OR_NODATA",
            is_settlement=False,
        ),
        DayRecord(date=date(2026, 7, 13), is_session=True, kind="SESSION"),
        DayRecord(date=date(2026, 8, 7), is_session=True, kind="SESSION"),
    ]


class StageEDefaultTests(unittest.TestCase):
    def test_default_is_recv_pay_tax10_stage_b(self) -> None:
        # Stage-B tax ACCEPT 2026-09-19 superseded Stage-E TAX0 DEFAULT.
        self.assertEqual(formal.DEFAULT_BOOKS_VERSION, formal.E22_V3_RECV_PAY_TAX10)
        self.assertTrue(is_sandbox_version(formal.DEFAULT_BOOKS_VERSION))

    def test_stage_e_effdelay_still_routable(self) -> None:
        self.assertTrue(is_sandbox_version(E22_V3_RECV_PAY_EFFDELAY))
        self.assertEqual(E22_V3_RECV_PAY_EFFDELAY, "E22_v3_recv_pay_effdelay")

    def test_router_accrues_receivable_on_effective_ex(self) -> None:
        days = _days()
        ev = formal.DivEvent(
            code="2891",
            kind="cash",
            ex_date="2026-07-10",
            amount=1.0,
            payment_date="2026-08-07",
        )
        pos, cash, recv, res = apply_books_for_date(
            "2026-07-13",
            {"2891": 1000.0},
            0.0,
            [ev],
            version=E22_V3_RECV_PAY_EFFDELAY,
            session_dates=session_dates(days),
            settlement_dates=settlement_dates(days),
        )
        self.assertAlmostEqual(cash, 0.0)
        self.assertAlmostEqual(sum(recv.values()), 1000.0)
        self.assertAlmostEqual(res.receivable_credit, 1000.0)
        _, cash2, recv2, res2 = apply_books_for_date(
            "2026-08-07",
            pos,
            cash,
            [ev],
            version=E22_V3_RECV_PAY_EFFDELAY,
            receivables=recv,
            session_dates=session_dates(days),
            settlement_dates=settlement_dates(days),
        )
        self.assertAlmostEqual(cash2, 1000.0)
        self.assertEqual(recv2, {})
        self.assertAlmostEqual(res2.receivable_settled, 1000.0)

    def test_nav_includes_receivable(self) -> None:
        _, _, _, nav = holdings(
            {
                "cash": 100.0,
                "positions": {"0050": 0.0},
                "e22_receivables": {"2880:2026-07-13": 50.0},
            },
            {c: 1.0 for c in __import__("live_ledger").ALL},
        )
        self.assertAlmostEqual(nav, 150.0)

    def test_manifest(self) -> None:
        m = books_manifest(E22_V3_RECV_PAY_EFFDELAY)
        self.assertEqual(m["e22_books_version"], E22_V3_RECV_PAY_EFFDELAY)
        self.assertIn("receivable", m.get("cash_timing", ""))


if __name__ == "__main__":
    unittest.main()
