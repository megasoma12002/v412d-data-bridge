#!/usr/bin/env python3
"""Unit tests for T+2 settlement estimate — typhoon / holiday session skips."""
from __future__ import annotations

import csv
import json
import tempfile
import unittest
import unittest.mock
from datetime import date
from pathlib import Path

from twse_session_sources import DayRecord, session_dates, settlement_dates, write_calendar_csv
from twse_t2_settlement_estimate import (
    estimate_fill,
    run_estimate,
    settlement_cash_for,
    summarize,
)


def _cal_row(d: date, is_session: bool, kind: str) -> DayRecord:
    return DayRecord(date=d, is_session=is_session, kind=kind, name="", source="test", notes="")


class SettlementCashTests(unittest.TestCase):
    def test_buy_sell_signs(self) -> None:
        self.assertEqual(settlement_cash_for("BUY", 1000.0, 1.0), -1001.0)
        self.assertEqual(settlement_cash_for("SELL", 1000.0, 5.0), 995.0)


class TyphoonSessionOffsetTests(unittest.TestCase):
    """2026-07-10 typhoon close must shift T+2 past the closed day."""

    def setUp(self) -> None:
        # Minimal July window around Bawei typhoon
        days = [
            _cal_row(date(2026, 7, 7), True, "SESSION"),
            _cal_row(date(2026, 7, 8), True, "SESSION"),
            _cal_row(date(2026, 7, 9), True, "SESSION"),
            _cal_row(date(2026, 7, 10), False, "CLOSED_TYPHOON_OR_NODATA"),
            _cal_row(date(2026, 7, 11), False, "WEEKEND"),
            _cal_row(date(2026, 7, 12), False, "WEEKEND"),
            _cal_row(date(2026, 7, 13), True, "SESSION"),
            _cal_row(date(2026, 7, 14), True, "SESSION"),
            _cal_row(date(2026, 7, 15), True, "SESSION"),
        ]
        self.sessions = session_dates(days)
        self.calendar = days

    def test_fill_before_typhoon_skips_closed_day(self) -> None:
        # Fill Thu 07-08 → +2 sessions = 07-09, 07-13 (skips Fri typhoon + weekend)
        row = {
            "fill_id": "t-1",
            "fill_date": "2026-07-08",
            "code": "0050",
            "side": "BUY",
            "quantity": 1000,
            "gross": 100000.0,
            "fees_tax": 85.5,
        }
        est = estimate_fill(row, self.sessions, asof=date(2026, 7, 8))
        self.assertEqual(est.settle_date, date(2026, 7, 13))
        # Calendar +2 would wrongly land on typhoon Friday
        self.assertNotEqual(est.settle_date, date(2026, 7, 10))
        self.assertEqual(est.settlement_cash, -100085.5)

    def test_fill_wed_before_typhoon_settles_thu_then_mon(self) -> None:
        # Fill Wed 07-07 → sessions 07-08, 07-09
        row = {
            "fill_id": "t-2",
            "fill_date": "2026-07-07",
            "code": "2330",
            "side": "SELL",
            "quantity": 1,
            "gross": 2000.0,
            "fees_tax": 5.0,
        }
        est = estimate_fill(row, self.sessions, asof=date(2026, 7, 7))
        self.assertEqual(est.settle_date, date(2026, 7, 9))
        self.assertEqual(est.settlement_cash, 1995.0)

    def test_consecutive_typhoon_days_shift_t2_further(self) -> None:
        """Three weekday typhoon closes in a row — T+2 skips the whole streak."""
        days = [
            _cal_row(date(2026, 7, 30), True, "SESSION"),
            _cal_row(date(2026, 7, 31), True, "SESSION"),
            _cal_row(date(2026, 8, 1), False, "WEEKEND"),
            _cal_row(date(2026, 8, 2), False, "WEEKEND"),
            _cal_row(date(2026, 8, 3), False, "CLOSED_TYPHOON_OR_NODATA"),
            _cal_row(date(2026, 8, 4), False, "CLOSED_TYPHOON_OR_NODATA"),
            _cal_row(date(2026, 8, 5), False, "CLOSED_TYPHOON_OR_NODATA"),
            _cal_row(date(2026, 8, 6), True, "SESSION"),
            _cal_row(date(2026, 8, 7), True, "SESSION"),
        ]
        sess = session_dates(days)
        # Fill Fri 7/31 → +2 sessions = Mon streak gone → Thu 8/6, Fri 8/7
        est = estimate_fill(
            {
                "fill_id": "c-1",
                "fill_date": "2026-07-31",
                "code": "0050",
                "side": "BUY",
                "quantity": 1,
                "gross": 100.0,
                "fees_tax": 1.0,
            },
            sess,
            asof=date(2026, 7, 31),
        )
        self.assertEqual(est.settle_date, date(2026, 8, 7))
        # Wrong calendar+2 would be Sun 8/2; even "skip one typhoon Mon" would be wrong
        self.assertNotEqual(est.settle_date, date(2026, 8, 2))
        self.assertNotEqual(est.settle_date, date(2026, 8, 4))
        # Fill Thu 7/30 → T+1=7/31, T+2=8/6 (first open after 3-day streak)
        est2 = estimate_fill(
            {
                "fill_id": "c-2",
                "fill_date": "2026-07-30",
                "code": "0050",
                "side": "BUY",
                "quantity": 1,
                "gross": 100.0,
                "fees_tax": 1.0,
            },
            sess,
            asof=date(2026, 7, 30),
        )
        self.assertEqual(est2.settle_date, date(2026, 8, 6))

    def test_cny_fengguan_settlement_only_days_count_for_t2(self) -> None:
        """封關後「無交易僅交割」仍是 T+2 營業日；春節放假才不算。"""
        days = [
            _cal_row(date(2026, 2, 10), True, "SESSION"),
            _cal_row(date(2026, 2, 11), True, "SESSION"),  # 最後交易日
            DayRecord(
                date=date(2026, 2, 12),
                is_session=False,
                kind="SETTLEMENT_ONLY",
                name="市場無交易，僅辦理結算交割作業",
                is_settlement=True,
            ),
            DayRecord(
                date=date(2026, 2, 13),
                is_session=False,
                kind="SETTLEMENT_ONLY",
                name="市場無交易，僅辦理結算交割作業",
                is_settlement=True,
            ),
            _cal_row(date(2026, 2, 14), False, "WEEKEND"),
            _cal_row(date(2026, 2, 16), False, "CLOSED_HOLIDAY"),
            _cal_row(date(2026, 2, 23), True, "SESSION"),
        ]
        settle_days = settlement_dates(days)
        trade_days = session_dates(days)
        self.assertIn(date(2026, 2, 12), settle_days)
        self.assertNotIn(date(2026, 2, 12), trade_days)
        # 2/10 fill → T+2 = 2/12 (settlement-only)
        est = estimate_fill(
            {
                "fill_id": "ny-1",
                "fill_date": "2026-02-10",
                "code": "0050",
                "side": "SELL",
                "quantity": 1,
                "gross": 100.0,
                "fees_tax": 1.0,
            },
            settle_days,
            asof=date(2026, 2, 10),
        )
        self.assertEqual(est.settle_date, date(2026, 2, 12))
        # 2/11 封關 fill → T+2 = 2/13 (not 開紅盤 2/23)
        est2 = estimate_fill(
            {
                "fill_id": "ny-2",
                "fill_date": "2026-02-11",
                "code": "0050",
                "side": "BUY",
                "quantity": 1,
                "gross": 100.0,
                "fees_tax": 1.0,
            },
            settle_days,
            asof=date(2026, 2, 11),
        )
        self.assertEqual(est2.settle_date, date(2026, 2, 13))
        self.assertNotEqual(est2.settle_date, date(2026, 2, 23))

    def test_holiday_gap_fri_to_next_week(self) -> None:
        days = [
            _cal_row(date(2026, 1, 2), True, "SESSION"),
            _cal_row(date(2026, 1, 5), True, "SESSION"),  # Mon after weekend
            _cal_row(date(2026, 1, 6), True, "SESSION"),
            _cal_row(date(2026, 1, 1), False, "CLOSED_HOLIDAY"),
        ]
        # Build ordered sessions: Jan 2, 5, 6
        sess = sorted(session_dates(days))
        row = {
            "fill_id": "h-1",
            "fill_date": "2026-01-02",
            "code": "0050",
            "side": "BUY",
            "quantity": 1,
            "gross": 100.0,
            "fees_tax": 0.1,
        }
        est = estimate_fill(row, sess, asof=date(2026, 1, 2))
        self.assertEqual(est.settle_date, date(2026, 1, 6))

    def test_cli_roundtrip_does_not_touch_portfolio(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            state = td_path / "state"
            state.mkdir()
            cal = td_path / "twse_sessions_2026.csv"
            write_calendar_csv(self.calendar, cal)
            with (state / "fills.csv").open("w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(
                    f,
                    fieldnames=[
                        "fill_id",
                        "fill_date",
                        "code",
                        "side",
                        "quantity",
                        "gross",
                        "fees_tax",
                    ],
                )
                w.writeheader()
                w.writerow(
                    {
                        "fill_id": "x",
                        "fill_date": "2026-07-08",
                        "code": "0050",
                        "side": "BUY",
                        "quantity": "1000",
                        "gross": "100000",
                        "fees_tax": "85.5",
                    }
                )
            (state / "portfolio_state.json").write_text(
                json.dumps({"cash": 50000.0}), encoding="utf-8"
            )
            before = (state / "portfolio_state.json").read_text(encoding="utf-8")
            estimates, summary = run_estimate(
                state, asof=date(2026, 7, 9), calendar_path=cal
            )
            after = (state / "portfolio_state.json").read_text(encoding="utf-8")
            self.assertEqual(before, after)
            self.assertEqual(estimates[0].settle_date, date(2026, 7, 13))
            self.assertEqual(summary["paper_cash"], 50000.0)
            # asof 07-09 < settle 07-13 → unsettled payable
            self.assertLess(summary["unsettled_net"], 0)


class MissingCalendarYearsTests(unittest.TestCase):
    def test_run_estimate_lists_missing_years(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            state = td_path / "state"
            state.mkdir()
            with (state / "fills.csv").open("w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(
                    f,
                    fieldnames=[
                        "fill_id",
                        "fill_date",
                        "code",
                        "side",
                        "quantity",
                        "gross",
                        "fees_tax",
                    ],
                )
                w.writeheader()
                w.writerow(
                    {
                        "fill_id": "x",
                        "fill_date": "2025-07-08",
                        "code": "0050",
                        "side": "BUY",
                        "quantity": "1",
                        "gross": "100",
                        "fees_tax": "1",
                    }
                )
            (state / "portfolio_state.json").write_text(
                json.dumps({"cash": 1.0}), encoding="utf-8"
            )
            import twse_t2_settlement_estimate as est

            with unittest.mock.patch.object(est, "DEFAULT_CALENDAR_DIR", td_path):
                with self.assertRaises(FileNotFoundError) as ctx:
                    run_estimate(state, asof=date(2026, 7, 9))
            msg = str(ctx.exception)
            self.assertIn("2025", msg)
            self.assertIn("2026", msg)


class SummarizeTests(unittest.TestCase):
    def test_settled_when_asof_past(self) -> None:
        from twse_t2_settlement_estimate import FillSettlement

        e = FillSettlement(
            fill_id="a",
            fill_date=date(2026, 7, 7),
            code="0050",
            side="BUY",
            quantity=1,
            gross=100.0,
            fees_tax=1.0,
            settlement_cash=-101.0,
            settle_date=date(2026, 7, 9),
            sessions_to_settle=0,
        )
        s = summarize([e], asof=date(2026, 7, 9), paper_cash=1000.0)
        self.assertEqual(s["settling_today_net"], -101.0)
        self.assertEqual(s["unsettled_net"], 0.0)
        self.assertEqual(s["settled_cash_estimate"], 1000.0)


if __name__ == "__main__":
    unittest.main()
