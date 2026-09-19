#!/usr/bin/env python3
"""Sandbox effdelay: simulate typhoon postponed ex / payment credit."""
from __future__ import annotations

import unittest
from datetime import date

import e22_dividend_accounting as formal
import e22_v3_sandbox_books as sandbox
from twse_session_sources import DayRecord, session_dates, settlement_dates


def _row(d: date, is_session: bool, kind: str, is_settlement: bool | None = None) -> DayRecord:
    return DayRecord(date=d, is_session=is_session, kind=kind, is_settlement=is_settlement)


class EffDelaySandboxTests(unittest.TestCase):
    def setUp(self) -> None:
        self.days = [
            _row(date(2026, 7, 9), True, "SESSION"),
            _row(date(2026, 7, 10), False, "CLOSED_TYPHOON_OR_NODATA", False),
            _row(date(2026, 7, 11), False, "WEEKEND", False),
            _row(date(2026, 7, 13), True, "SESSION"),
            _row(date(2026, 8, 7), True, "SESSION"),
        ]
        self.sessions = session_dates(self.days)
        self.settlements = settlement_dates(self.days)
        self.ev = formal.DivEvent(
            code="2891",
            kind="cash",
            ex_date="2026-07-10",
            amount=2.5,
            payment_date="2026-08-07",
        )
        self.pos0 = {"2891": 1000.0}

    def test_raw_recv_pay_accrues_on_closed_ex(self) -> None:
        _, cash, recv, res = sandbox.apply_sandbox_for_date(
            "2026-07-10",
            self.pos0,
            0.0,
            {},
            [self.ev],
            version=sandbox.E22_V3_RECV_PAY,
        )
        self.assertEqual(cash, 0.0)
        self.assertAlmostEqual(sum(recv.values()), 2500.0)
        self.assertAlmostEqual(res.receivable_credit, 2500.0)

    def test_effdelay_skips_closed_ex_accrues_next_session(self) -> None:
        _, cash, recv, res = sandbox.apply_sandbox_for_date(
            "2026-07-10",
            self.pos0,
            0.0,
            {},
            [self.ev],
            version=sandbox.E22_V3_RECV_PAY_EFFDELAY,
            session_dates=self.sessions,
            settlement_dates=self.settlements,
        )
        self.assertEqual(cash, 0.0)
        self.assertEqual(recv, {})
        self.assertEqual(res.receivable_credit, 0.0)

        _, cash2, recv2, res2 = sandbox.apply_sandbox_for_date(
            "2026-07-13",
            self.pos0,
            0.0,
            {},
            [self.ev],
            version=sandbox.E22_V3_RECV_PAY_EFFDELAY,
            session_dates=self.sessions,
            settlement_dates=self.settlements,
        )
        self.assertEqual(cash2, 0.0)
        self.assertAlmostEqual(sum(recv2.values()), 2500.0)
        self.assertAlmostEqual(res2.receivable_credit, 2500.0)
        self.assertEqual(res2.details[0]["effective_ex_trade"], "2026-07-13")

    def test_effdelay_payment_snaps_off_typhoon(self) -> None:
        ev = formal.DivEvent(
            code="2891",
            kind="cash",
            ex_date="2026-07-09",
            amount=2.5,
            payment_date="2026-07-10",  # typhoon → settle 07-13
        )
        pos, cash, recv, _ = sandbox.apply_sandbox_for_date(
            "2026-07-09",
            self.pos0,
            0.0,
            {},
            [ev],
            version=sandbox.E22_V3_RECV_PAY_EFFDELAY,
            session_dates=self.sessions,
            settlement_dates=self.settlements,
        )
        self.assertAlmostEqual(sum(recv.values()), 2500.0)

        # raw pay day: no settle under effdelay
        _, cash_t, recv_t, res_t = sandbox.apply_sandbox_for_date(
            "2026-07-10",
            pos,
            cash,
            recv,
            [ev],
            version=sandbox.E22_V3_RECV_PAY_EFFDELAY,
            session_dates=self.sessions,
            settlement_dates=self.settlements,
        )
        self.assertEqual(res_t.receivable_settled, 0.0)
        self.assertAlmostEqual(sum(recv_t.values()), 2500.0)

        _, cash_s, recv_s, res_s = sandbox.apply_sandbox_for_date(
            "2026-07-13",
            pos,
            cash_t,
            recv_t,
            [ev],
            version=sandbox.E22_V3_RECV_PAY_EFFDELAY,
            session_dates=self.sessions,
            settlement_dates=self.settlements,
        )
        self.assertAlmostEqual(res_s.receivable_settled, 2500.0)
        self.assertAlmostEqual(cash_s, 2500.0)
        self.assertEqual(recv_s, {})
        self.assertEqual(res_s.details[0]["effective_payment"], "2026-07-13")

    def test_formal_legacy_tw_still_credits_raw_ex(self) -> None:
        _, cash, res = formal.apply_dividends_for_date(
            "2026-07-10",
            self.pos0,
            0.0,
            [self.ev],
            version=formal.E22_V2S_TW,
        )
        self.assertAlmostEqual(cash, 2500.0)
        self.assertAlmostEqual(res.cash_credit, 2500.0)

    def test_default_is_recv_pay_tax10_after_stage_b(self) -> None:
        # Stage-B tax ACCEPT supersedes Stage-E TAX0 as live DEFAULT.
        self.assertEqual(formal.DEFAULT_BOOKS_VERSION, formal.E22_V3_RECV_PAY_TAX10)
        self.assertEqual(formal.E22_V3_RECV_PAY_EFFDELAY, "E22_v3_recv_pay_effdelay")
        self.assertEqual(formal.PRESERVED_CASH_ON_EX, formal.E22_V2S_TW_EFFEX)


if __name__ == "__main__":
    unittest.main()
