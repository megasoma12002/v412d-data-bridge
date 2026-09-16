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
    TAIPEI,
    apply_overlays,
    build_annual_calendar,
    holiday_status_for,
    lookup_day,
    nth_session_after,
    probe_session,
    read_calendar_csv,
    session_dates,
    write_calendar_csv,
    _classify_work_stop,
    _is_taipei,
    _parse_target_date,
)

SAMPLE_SCHEDULE = {
    "queryYear": 2026,
    "data": [
        ["2026-01-01", "中華民國開國紀念日", "依規定放假1日。"],
        ["2026-01-02", "國曆新年開始交易日", "國曆新年開始交易。"],
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
            mi_payload={"stat": "很抱歉，沒有符合條件的資料!", "tables": []},
            now_taipei=datetime(2026, 9, 16, 9, 0, tzinfo=TAIPEI),
        )
        self.assertEqual(p.status, "UNKNOWN")
        self.assertFalse(p.broker_submit_allowed)


if __name__ == "__main__":
    unittest.main()
