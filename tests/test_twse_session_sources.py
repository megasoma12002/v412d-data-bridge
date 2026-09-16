#!/usr/bin/env python3
"""Unit tests for TWSE session / typhoon signal parsers (offline)."""
from __future__ import annotations

import unittest
from datetime import date, datetime
from zoneinfo import ZoneInfo

from twse_session_sources import (
    CapWorkStop,
    TAIPEI,
    _classify_work_stop,
    _is_taipei,
    _parse_target_date,
    holiday_status_for,
    probe_session,
    taipei_typhoon_intent,
)


class ParserTests(unittest.TestCase):
    def test_classify_afternoon_vs_full(self) -> None:
        self.assertEqual(
            _classify_work_stop("今天下午已達停止上班及上課標準"),
            "AFTERNOON",
        )
        self.assertEqual(
            _classify_work_stop("今天上午停止上班、停止上課"),
            "MORNING",
        )
        self.assertEqual(
            _classify_work_stop("8/23已達停止上班及上課標準"),
            "FULL_DAY",
        )
        self.assertEqual(
            _classify_work_stop("明天未達停止上班、已達停止上課標準"),
            "SCHOOL_ONLY",
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

    def test_holiday_schedule_offline(self) -> None:
        sched = {
            "data": [
                ["2026-01-01", "中華民國開國紀念日", "依規定放假1日。"],
                ["2026-01-02", "國曆新年開始交易日", "國曆新年開始交易。"],
            ]
        }
        self.assertEqual(holiday_status_for(date(2026, 1, 1), sched), "CLOSED_HOLIDAY")
        self.assertEqual(holiday_status_for(date(2026, 1, 2), sched), "OPEN_MARKER")
        self.assertIsNone(holiday_status_for(date(2026, 3, 3), sched))

    def test_taipei_intent_closes(self) -> None:
        caps = [
            CapWorkStop(
                area="臺北市",
                sent="2026-07-09T20:00:00+08:00",
                effective="",
                expires="",
                headline="停班課通知",
                description="[停班停課通知]臺北市:7/10停止上班、停止上課。",
                status="Actual",
                msg_type="Alert",
                href="x",
                target_date=date(2026, 7, 10),
                class_="FULL_DAY",
                is_taipei=True,
            )
        ]
        intent = taipei_typhoon_intent(date(2026, 7, 10), caps)
        self.assertTrue(intent["closes_twse"])

    def test_probe_weekend_and_holiday_and_cap(self) -> None:
        weekend = probe_session(date(2026, 9, 12), use_network=False)
        self.assertEqual(weekend.status, "WEEKEND")
        self.assertFalse(weekend.broker_submit_allowed)

        sched = {"data": [["2026-01-01", "中華民國開國紀念日", "放假"]]}
        hol = probe_session(
            date(2026, 1, 1),
            use_network=False,
            holiday_schedule=sched,
            caps=[],
            mi_payload={"stat": "OK", "tables": [1]},
        )
        self.assertEqual(hol.status, "CLOSED_HOLIDAY")

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
                class_="MORNING",
                is_taipei=True,
            )
        ]
        typ = probe_session(
            date(2026, 7, 10),
            use_network=False,
            holiday_schedule={"data": []},
            caps=caps,
            mi_payload={"stat": "很抱歉", "tables": []},
            now_taipei=datetime(2026, 7, 10, 8, 0, tzinfo=TAIPEI),
        )
        self.assertEqual(typ.status, "CLOSED_TYPHOON_INTENT")
        self.assertFalse(typ.broker_submit_allowed)

    def test_mi_index_intraday_unknown(self) -> None:
        # Open weekday, no CAP, MI empty at 09:00 → UNKNOWN (not closed)
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
