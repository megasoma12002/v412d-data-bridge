#!/usr/bin/env python3
"""Sandbox NHI211: Stage-E timing + threshold supplemental premium."""
from __future__ import annotations

import unittest
from datetime import date

import e22_dividend_accounting as formal
import e22_v3_sandbox_books as sandbox
from nhi_dividend_supplemental_premium import NHI_SUPPLEMENTAL_RATE
from twse_session_sources import DayRecord, session_dates, settlement_dates


def _row(d: date, is_session: bool, kind: str, is_settlement: bool | None = None) -> DayRecord:
    return DayRecord(date=d, is_session=is_session, kind=kind, is_settlement=is_settlement)


class Nhi211SandboxTests(unittest.TestCase):
    def setUp(self) -> None:
        self.days = [
            _row(date(2026, 7, 9), True, "SESSION"),
            _row(date(2026, 7, 13), True, "SESSION"),
            _row(date(2026, 8, 7), True, "SESSION"),
        ]
        self.sessions = session_dates(self.days)
        self.settlements = settlement_dates(self.days)

    def test_below_threshold_matches_tax0(self) -> None:
        ev = formal.DivEvent(
            code="2891",
            kind="cash",
            ex_date="2026-07-13",
            amount=1.0,
            payment_date="2026-08-07",
        )
        pos = {"2891": 1000.0}  # gross 1000 < 20k
        _, _, recv0, _ = sandbox.apply_sandbox_for_date(
            "2026-07-13",
            pos,
            0.0,
            {},
            [ev],
            version=sandbox.E22_V3_RECV_PAY_EFFDELAY,
            session_dates=self.sessions,
            settlement_dates=self.settlements,
        )
        _, _, recv1, res1 = sandbox.apply_sandbox_for_date(
            "2026-07-13",
            pos,
            0.0,
            {},
            [ev],
            version=sandbox.E22_V3_RECV_PAY_EFFDELAY_NHI211,
            session_dates=self.sessions,
            settlement_dates=self.settlements,
        )
        self.assertAlmostEqual(sum(recv0.values()), sum(recv1.values()))
        self.assertAlmostEqual(sum(recv1.values()), 1000.0)
        self.assertEqual(res1.details[0]["premium_twd"], 0.0)

    def test_at_threshold_applies_211(self) -> None:
        ev = formal.DivEvent(
            code="2891",
            kind="cash",
            ex_date="2026-07-13",
            amount=20.0,
            payment_date="2026-08-07",
        )
        pos = {"2891": 1000.0}  # gross 20_000
        _, _, recv, res = sandbox.apply_sandbox_for_date(
            "2026-07-13",
            pos,
            0.0,
            {},
            [ev],
            version=sandbox.E22_V3_RECV_PAY_EFFDELAY_NHI211,
            session_dates=self.sessions,
            settlement_dates=self.settlements,
        )
        expected_net = 20_000.0 * (1.0 - NHI_SUPPLEMENTAL_RATE)
        self.assertAlmostEqual(sum(recv.values()), expected_net)
        self.assertAlmostEqual(res.details[0]["premium_twd"], 20_000.0 * NHI_SUPPLEMENTAL_RATE)
        self.assertFalse(sandbox.version_manifest(sandbox.E22_V3_RECV_PAY_EFFDELAY_NHI211)["promote_ready"])
        self.assertTrue(
            sandbox.version_manifest(sandbox.E22_V3_RECV_PAY_EFFDELAY_NHI211)[
                "cashflow_precision_sandbox"
            ]
        )

    def test_settle_pays_net_receivable(self) -> None:
        ev = formal.DivEvent(
            code="2891",
            kind="cash",
            ex_date="2026-07-13",
            amount=20.0,
            payment_date="2026-08-07",
        )
        pos = {"2891": 1000.0}
        _, cash1, recv1, _ = sandbox.apply_sandbox_for_date(
            "2026-07-13",
            pos,
            0.0,
            {},
            [ev],
            version=sandbox.E22_V3_RECV_PAY_EFFDELAY_NHI211,
            session_dates=self.sessions,
            settlement_dates=self.settlements,
        )
        _, cash2, recv2, res2 = sandbox.apply_sandbox_for_date(
            "2026-08-07",
            pos,
            cash1,
            recv1,
            [ev],
            version=sandbox.E22_V3_RECV_PAY_EFFDELAY_NHI211,
            session_dates=self.sessions,
            settlement_dates=self.settlements,
        )
        expected_net = 20_000.0 * (1.0 - NHI_SUPPLEMENTAL_RATE)
        self.assertAlmostEqual(cash2, expected_net)
        self.assertEqual(recv2, {})
        self.assertAlmostEqual(res2.receivable_settled, expected_net)


if __name__ == "__main__":
    unittest.main()
