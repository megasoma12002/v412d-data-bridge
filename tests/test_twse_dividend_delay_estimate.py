#!/usr/bin/env python3
"""Unit tests for 除權息 delay estimate helpers."""
from __future__ import annotations

import unittest
from datetime import date

from twse_dividend_delay_estimate import effective_ex_trade, effective_payment, estimate_event
from twse_session_sources import DayRecord, session_dates, settlement_dates


def _row(d: date, is_session: bool, kind: str, is_settlement: bool | None = None) -> DayRecord:
    return DayRecord(
        date=d,
        is_session=is_session,
        kind=kind,
        is_settlement=is_settlement,
    )


class EffectiveExTests(unittest.TestCase):
    def test_typhoon_ex_snaps_to_next_session(self) -> None:
        days = [
            _row(date(2026, 7, 9), True, "SESSION"),
            _row(date(2026, 7, 10), False, "CLOSED_TYPHOON_OR_NODATA", False),
            _row(date(2026, 7, 11), False, "WEEKEND", False),
            _row(date(2026, 7, 13), True, "SESSION"),
        ]
        sess = session_dates(days)
        self.assertEqual(effective_ex_trade(date(2026, 7, 10), sess), date(2026, 7, 13))
        self.assertEqual(effective_ex_trade(date(2026, 7, 9), sess), date(2026, 7, 9))


class EffectivePayTests(unittest.TestCase):
    def test_payment_on_typhoon_snaps_to_next_settlement(self) -> None:
        days = [
            _row(date(2026, 7, 9), True, "SESSION"),
            _row(date(2026, 7, 10), False, "CLOSED_TYPHOON_OR_NODATA", False),
            _row(date(2026, 7, 13), True, "SESSION"),
        ]
        settles = settlement_dates(days)
        self.assertEqual(effective_payment(date(2026, 7, 10), settles), date(2026, 7, 13))

    def test_payment_on_fengguan_settlement_only_stays(self) -> None:
        days = [
            _row(date(2026, 2, 11), True, "SESSION"),
            _row(date(2026, 2, 12), False, "SETTLEMENT_ONLY", True),
            _row(date(2026, 2, 13), False, "SETTLEMENT_ONLY", True),
            _row(date(2026, 2, 16), False, "CLOSED_HOLIDAY", False),
        ]
        settles = settlement_dates(days)
        self.assertEqual(effective_payment(date(2026, 2, 12), settles), date(2026, 2, 12))
        # 春节放假 → next settlement (none in this stub after 2/13) — extend
        days.append(_row(date(2026, 2, 23), True, "SESSION"))
        settles = settlement_dates(days)
        self.assertEqual(effective_payment(date(2026, 2, 16), settles), date(2026, 2, 23))

    def test_mops_amendment_wins(self) -> None:
        days = [_row(date(2026, 7, 10), False, "CLOSED_TYPHOON_OR_NODATA", False)]
        settles = settlement_dates(days + [_row(date(2026, 7, 13), True, "SESSION")])
        self.assertEqual(
            effective_payment(
                date(2026, 7, 10), settles, mops_amendment=date(2026, 7, 13)
            ),
            date(2026, 7, 13),
        )


class EstimateRowTests(unittest.TestCase):
    def test_estimate_notes(self) -> None:
        days = [
            _row(date(2026, 7, 9), True, "SESSION"),
            _row(date(2026, 7, 10), False, "CLOSED_TYPHOON_OR_NODATA", False),
            _row(date(2026, 7, 13), True, "SESSION"),
        ]
        r = estimate_event(
            {"code": "2330", "cash_ex_date": "2026-07-10", "cash_payment_date": "2026-07-10"},
            sessions=session_dates(days),
            settlements=settlement_dates(days),
        )
        self.assertEqual(r["effective_ex_trade"], "2026-07-13")
        self.assertEqual(r["effective_payment"], "2026-07-13")
        self.assertIn("ex_snapped", r["notes"])
        self.assertIn("pay_snapped", r["notes"])


if __name__ == "__main__":
    unittest.main()
