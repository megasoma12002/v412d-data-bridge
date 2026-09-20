#!/usr/bin/env python3
"""Unit tests for TWSE annual calendar + typhoon overlays (offline)."""
from __future__ import annotations

import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from twse_session_sources import (
    CapWorkStop,
    DayRecord,
    TAIPEI,
    apply_overlays,
    build_annual_calendar,
    classify_taifex_day_fact,
    holiday_status_for,
    load_calendar_window,
    lookup_day,
    mis_row_open_on,
    nth_session_after,
    parse_taifex_tx_day_session_dates,
    probe_mis_intraday_open,
    probe_session,
    read_calendar_csv,
    session_dates,
    taifex_openapi_tx_day_date,
    write_calendar_csv,
    _classify_work_stop,
    _is_taipei,
    _parse_target_date,
    _parse_target_dates,
)

SAMPLE_SCHEDULE = {
    "queryYear": 2026,
    "data": [
        ["2026-01-01", "中華民國開國紀念日", "依規定放假1日。"],
        ["2026-01-02", "國曆新年開始交易日", "國曆新年開始交易。"],
        ["2026-02-11", "農曆春節前最後交易日", "農曆春節前最後交易。"],
        ["2026-02-12", "市場無交易，僅辦理結算交割作業", ""],
        ["2026-02-13", "市場無交易，僅辦理結算交割作業", ""],
        ["2026-02-16", "農曆除夕及春節", "放假。"],
        ["2026-02-23", "農曆春節後開始交易日", "農曆春節後開始交易。"],
        ["2026-02-27", "和平紀念日", "補假。"],
        ["2026-02-28", "和平紀念日", "依規定放假1日。"],
        ["2026-05-01", "勞動節", "依規定放假1日。"],
    ],
}


class ParserTests(unittest.TestCase):
    def test_classify_afternoon_vs_full(self) -> None:
        self.assertEqual(_classify_work_stop("今天下午已達停止上班及上課標準"), "AFTERNOON")
        self.assertEqual(_classify_work_stop("今天上午停止上班、停止上課"), "MORNING")
        self.assertEqual(_classify_work_stop("8/23已達停止上班及上課標準"), "FULL_DAY")
        self.assertEqual(
            _classify_work_stop("明天未達停止上班、已達停止上課標準"), "SCHOOL_ONLY"
        )

    def test_taipei_city_not_district(self) -> None:
        self.assertTrue(_is_taipei("臺北市", "臺北市:明天停止上班、停止上課"))
        self.assertFalse(_is_taipei("臺北市中正區", "臺北市中正區:明天停止上班"))
        self.assertFalse(_is_taipei("高雄市", "高雄市:停止上班"))

    def test_parse_target_date(self) -> None:
        sent = datetime(2026, 8, 22, 19, 0, tzinfo=TAIPEI)
        self.assertEqual(_parse_target_date("今天停止上班", sent), date(2026, 8, 22))
        self.assertEqual(_parse_target_date("明天停止上班、停止上課", sent), date(2026, 8, 23))
        self.assertEqual(_parse_target_date("8/23已達停止上班及上課標準", sent), date(2026, 8, 23))

    def test_parse_consecutive_target_dates(self) -> None:
        sent = datetime(2026, 8, 2, 19, 0, tzinfo=TAIPEI)
        self.assertEqual(
            _parse_target_dates("臺北市:今天及明天停止上班、停止上課", sent),
            [date(2026, 8, 2), date(2026, 8, 3)],
        )
        self.assertEqual(
            _parse_target_dates("8/3至8/5已達停止上班及上課標準", sent),
            [date(2026, 8, 3), date(2026, 8, 4), date(2026, 8, 5)],
        )

    def test_cap_range_overlay_closes_each_day(self) -> None:
        cal = build_annual_calendar(2026, SAMPLE_SCHEDULE)
        caps = [
            CapWorkStop(
                area="臺北市",
                sent="",
                effective="",
                expires="",
                headline="",
                description="8/3至8/5停止上班",
                status="Actual",
                msg_type="Alert",
                href="",
                target_date=date(2026, 8, 3),
                target_dates=[date(2026, 8, 3), date(2026, 8, 4), date(2026, 8, 5)],
                class_="FULL_DAY",
                is_taipei=True,
            )
        ]
        out = apply_overlays(cal, caps=caps)
        for d in (date(2026, 8, 3), date(2026, 8, 4), date(2026, 8, 5)):
            rec = lookup_day(out, d)
            assert rec is not None
            self.assertFalse(rec.is_session)
            self.assertEqual(rec.kind, "CLOSED_TYPHOON_INTENT")

class AnnualCalendarTests(unittest.TestCase):
    def test_build_integrates_holidays_and_weekends(self) -> None:
        cal = build_annual_calendar(2026, SAMPLE_SCHEDULE)
        self.assertEqual(len(cal), 365)
        jan1 = lookup_day(cal, date(2026, 1, 1))
        assert jan1 is not None
        self.assertFalse(jan1.is_session)
        self.assertEqual(jan1.kind, "CLOSED_HOLIDAY")
        jan2 = lookup_day(cal, date(2026, 1, 2))
        assert jan2 is not None
        self.assertTrue(jan2.is_session)
        self.assertEqual(jan2.kind, "SESSION")
        # 封關後交割日：無交易但 is_settlement
        d212 = lookup_day(cal, date(2026, 2, 12))
        assert d212 is not None
        self.assertFalse(d212.is_session)
        self.assertTrue(d212.is_settlement)
        self.assertEqual(d212.kind, "SETTLEMENT_ONLY")
        d216 = lookup_day(cal, date(2026, 2, 16))
        assert d216 is not None
        self.assertFalse(d216.is_session)
        self.assertFalse(d216.is_settlement)
        # 2026-02-28 is Saturday + holiday → closed holiday, not bare weekend
        feb28 = lookup_day(cal, date(2026, 2, 28))
        assert feb28 is not None
        self.assertFalse(feb28.is_session)
        self.assertEqual(feb28.kind, "CLOSED_HOLIDAY")
        sat = lookup_day(cal, date(2026, 9, 12))
        assert sat is not None
        self.assertEqual(sat.kind, "WEEKEND")

    def test_typhoon_overlay_on_planned_session(self) -> None:
        cal = build_annual_calendar(2026, SAMPLE_SCHEDULE)
        caps = [
            CapWorkStop(
                area="臺北市",
                sent="",
                effective="",
                expires="",
                headline="",
                description="",
                status="Actual",
                msg_type="Alert",
                href="",
                target_date=date(2026, 7, 10),
                class_="FULL_DAY",
                is_taipei=True,
            )
        ]
        out = apply_overlays(cal, caps=caps, mi_closed=[date(2026, 7, 24)])
        d710 = lookup_day(out, date(2026, 7, 10))
        assert d710 is not None
        self.assertFalse(d710.is_session)
        self.assertEqual(d710.kind, "CLOSED_TYPHOON_INTENT")
        d724 = lookup_day(out, date(2026, 7, 24))
        assert d724 is not None
        self.assertFalse(d724.is_session)
        self.assertEqual(d724.kind, "CLOSED_TYPHOON_OR_NODATA")
        # holiday not overwritten by mi
        jan1 = lookup_day(out, date(2026, 1, 1))
        assert jan1 is not None
        self.assertEqual(jan1.kind, "CLOSED_HOLIDAY")

    def test_nth_session_after_skips_holiday(self) -> None:
        cal = build_annual_calendar(2026, SAMPLE_SCHEDULE)
        # 2025-12-31 not in cal; use 2026-01-01 closed → next sessions
        sess = session_dates(cal)
        # Last session of 2025 isn't here; from 2025-12-31 equivalent: after Dec 31
        # After 2025-12-31: Jan 1 closed, Jan 2 is OPEN_MARKER session
        # nth after 2025-12-31 within 2026 cal: first session is Jan 2
        # Use start=2026-01-01 (closed): first after is Jan 2
        self.assertEqual(nth_session_after(sess, date(2026, 1, 1), 1), date(2026, 1, 2))
        # T+2 from Jan 2 fill → +2 sessions
        self.assertEqual(nth_session_after(sess, date(2026, 1, 2), 2), date(2026, 1, 6))

    def test_csv_roundtrip(self) -> None:
        cal = build_annual_calendar(2026, SAMPLE_SCHEDULE)
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "twse_sessions_2026.csv"
            write_calendar_csv(cal, p)
            back = read_calendar_csv(p)
            self.assertEqual(len(back), 365)
            self.assertEqual(lookup_day(back, date(2026, 5, 1)).kind, "CLOSED_HOLIDAY")

    def test_probe_uses_annual_calendar(self) -> None:
        cal = build_annual_calendar(2026, SAMPLE_SCHEDULE)
        p = probe_session(
            date(2026, 1, 1),
            use_network=False,
            calendar=cal,
        )
        self.assertEqual(p.status, "CLOSED_HOLIDAY")
        self.assertFalse(p.is_session)

    def test_probe_weekend_holiday_label(self) -> None:
        p = probe_session(
            date(2026, 2, 28),
            use_network=False,
            holiday_schedule=SAMPLE_SCHEDULE,
        )
        self.assertEqual(p.status, "CLOSED_HOLIDAY")
        self.assertFalse(p.broker_submit_allowed)

    def test_mi_index_intraday_unknown(self) -> None:
        p = probe_session(
            date(2026, 9, 16),
            use_network=False,
            holiday_schedule={"data": []},
            caps=[],
            mis_payloads=[{"rtcode": "0000", "msgArray": []}],
            mi_payload={"stat": "很抱歉，沒有符合條件的資料!", "tables": []},
            now_taipei=datetime(2026, 9, 16, 9, 30, tzinfo=TAIPEI),
        )
        self.assertEqual(p.status, "UNKNOWN")
        self.assertFalse(p.broker_submit_allowed)

    def test_mis_intraday_open_allows_broker(self) -> None:
        mis = {
            "rtcode": "0000",
            "msgArray": [
                {
                    "c": "0050",
                    "d": "20260916",
                    "o": "106.1500",
                    "t": "09:30:00",
                    "v": "100",
                }
            ],
        }
        p = probe_session(
            date(2026, 9, 16),
            use_network=False,
            holiday_schedule={"data": []},
            caps=[],
            mis_payloads=[mis],
            mi_payload={"stat": "很抱歉，沒有符合條件的資料!", "tables": []},
            now_taipei=datetime(2026, 9, 16, 9, 30, tzinfo=TAIPEI),
        )
        self.assertEqual(p.status, "OPEN")
        self.assertTrue(p.broker_submit_allowed)
        self.assertTrue(p.sources["mis_quote"]["open"])

    def test_mis_prior_day_not_open(self) -> None:
        mis = {
            "rtcode": "0000",
            "msgArray": [{"c": "0050", "d": "20260915", "o": "106.0000", "t": "13:30:00"}],
        }
        self.assertFalse(mis_row_open_on(date(2026, 9, 16), mis["msgArray"][0]))
        verdict = probe_mis_intraday_open(
            date(2026, 9, 16),
            watchlist=["tse_0050.tw"],
            payloads=[mis],
        )
        self.assertFalse(verdict["open"])


class TaifexOverlayTests(unittest.TestCase):
    SAMPLE_CSV = (
        "交易日期,契約,到期月份(週別),開盤價,最高價,最低價,收盤價,漲跌價,漲跌%,成交量,"
        "結算價,未沖銷契約數,最後最佳買價,最後最佳賣價,歷史最高價,歷史最低價,"
        "是否因訊息面暫停交易,交易時段,價差對單式委託成交量\n"
        "2026/07/09,TX,202607,1,1,1,1,0,0%,1,1,1,1,1,1,1,,一般,\n"
        "2026/07/09,TX,202607,1,1,1,1,0,0%,1,-,-,1,1,1,1,,盤後,\n"
        "2026/07/10,MXF,202607,1,1,1,1,0,0%,1,1,1,1,1,1,1,,一般,\n"
    )

    def test_parse_tx_day_only(self) -> None:
        days = parse_taifex_tx_day_session_dates(self.SAMPLE_CSV)
        self.assertEqual(days, {date(2026, 7, 9)})

    def test_classify_history_typhoon_vs_open(self) -> None:
        hist = {date(2026, 7, 9)}
        self.assertEqual(
            classify_taifex_day_fact(date(2026, 7, 9), history_open_days=hist), "OPEN"
        )
        self.assertEqual(
            classify_taifex_day_fact(date(2026, 7, 10), history_open_days=hist), "CLOSED"
        )
        self.assertEqual(
            classify_taifex_day_fact(
                date(2026, 9, 16),
                history_open_days=hist,
                now_taipei=datetime(2026, 9, 16, 9, 50, tzinfo=TAIPEI),
            ),
            "UNKNOWN",
        )

    def test_openapi_latest_date(self) -> None:
        payload = [
            {
                "Date": "20260915",
                "Contract": "TX",
                "TradingSession": "一般",
            },
            {
                "Date": "20260915",
                "Contract": "TX",
                "TradingSession": "盤後",
            },
        ]
        self.assertEqual(taifex_openapi_tx_day_date(payload), date(2026, 9, 15))
        self.assertEqual(
            classify_taifex_day_fact(date(2026, 9, 16), openapi_payload=payload),
            "UNKNOWN",
        )
        self.assertEqual(
            classify_taifex_day_fact(date(2026, 9, 15), openapi_payload=payload),
            "OPEN",
        )

    def test_taifex_overlay_marks_typhoon(self) -> None:
        cal = build_annual_calendar(2026, SAMPLE_SCHEDULE)
        out = apply_overlays(cal, taifex_closed=[date(2026, 7, 10)])
        d710 = lookup_day(out, date(2026, 7, 10))
        assert d710 is not None
        self.assertFalse(d710.is_session)
        self.assertEqual(d710.kind, "CLOSED_TYPHOON_OR_NODATA")
        self.assertIn("taifex_tx", d710.source)


class CalendarWindowTests(unittest.TestCase):
    def test_center_missing_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(FileNotFoundError) as ctx:
                load_calendar_window(2099, calendar_dir=td, span=1)
            self.assertIn("2099", str(ctx.exception))

    def test_loads_center_and_optional_neighbors(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            days = [
                DayRecord(
                    date=date(2026, 7, 13),
                    is_session=True,
                    kind="SESSION",
                    name="",
                    source="t",
                    notes="",
                    is_settlement=True,
                )
            ]
            write_calendar_csv(days, td_path / "twse_sessions_2026.csv")
            sessions, settlements = load_calendar_window(2026, calendar_dir=td_path, span=1)
            self.assertEqual(sessions, [date(2026, 7, 13)])
            self.assertEqual(settlements, [date(2026, 7, 13)])


if __name__ == "__main__":
    unittest.main()
