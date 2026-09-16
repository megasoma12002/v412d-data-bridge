#!/usr/bin/env python3
"""D5: Soft-Frozen E22_v2s_tw_effex credits on effective_ex_trade."""
from __future__ import annotations

import unittest
from datetime import date

import e22_dividend_accounting as formal
from twse_session_sources import DayRecord, session_dates


def _row(d: date, is_session: bool, kind: str, is_settlement: bool | None = None) -> DayRecord:
    return DayRecord(date=d, is_session=is_session, kind=kind, is_settlement=is_settlement)


class EffexBooksTests(unittest.TestCase):
    def setUp(self) -> None:
        self.days = [
            _row(date(2026, 7, 9), True, "SESSION"),
            _row(date(2026, 7, 10), False, "CLOSED_TYPHOON_OR_NODATA", False),
            _row(date(2026, 7, 11), False, "WEEKEND", False),
            _row(date(2026, 7, 13), True, "SESSION"),
        ]
        self.sessions = session_dates(self.days)
        self.ev = formal.DivEvent(
            code="2891",
            kind="cash",
            ex_date="2026-07-10",
            amount=2.5,
            payment_date="2026-08-07",
        )
        self.pos0 = {"2891": 1000.0}

    def test_default_is_effex(self) -> None:
        self.assertEqual(formal.DEFAULT_BOOKS_VERSION, formal.E22_V2S_TW_EFFEX)
        m = formal.version_manifest()
        self.assertEqual(m["cash_timing"], "cash_effective_ex_trade")
        self.assertTrue(m["d5_accept"])

    def test_legacy_tw_still_credits_raw_ex(self) -> None:
        _, cash, res = formal.apply_dividends_for_date(
            "2026-07-10",
            self.pos0,
            0.0,
            [self.ev],
            version=formal.E22_V2S_TW,
            session_dates=self.sessions,
        )
        self.assertAlmostEqual(cash, 2500.0)
        self.assertAlmostEqual(res.cash_credit, 2500.0)

    def test_effex_skips_closed_ex_credits_next_session(self) -> None:
        _, cash0, res0 = formal.apply_dividends_for_date(
            "2026-07-10",
            self.pos0,
            0.0,
            [self.ev],
            version=formal.E22_V2S_TW_EFFEX,
            session_dates=self.sessions,
        )
        self.assertEqual(cash0, 0.0)
        self.assertEqual(res0.cash_credit, 0.0)

        _, cash1, res1 = formal.apply_dividends_for_date(
            "2026-07-13",
            self.pos0,
            0.0,
            [self.ev],
            version=formal.E22_V2S_TW_EFFEX,
            session_dates=self.sessions,
        )
        self.assertAlmostEqual(cash1, 2500.0)
        self.assertAlmostEqual(res1.cash_credit, 2500.0)
        self.assertEqual(res1.details[0]["effective_ex_trade"], "2026-07-13")

    def test_effex_loads_pinned_2026_calendar_when_sessions_omitted(self) -> None:
        _, cash0, _ = formal.apply_dividends_for_date(
            "2026-07-10",
            self.pos0,
            0.0,
            [self.ev],
            version=formal.DEFAULT_BOOKS_VERSION,
        )
        self.assertEqual(cash0, 0.0)
        _, cash1, res1 = formal.apply_dividends_for_date(
            "2026-07-13",
            self.pos0,
            0.0,
            [self.ev],
            version=formal.DEFAULT_BOOKS_VERSION,
        )
        self.assertAlmostEqual(cash1, 2500.0)
        self.assertEqual(res1.details[0]["effective_ex_trade"], "2026-07-13")


if __name__ == "__main__":
    unittest.main()
