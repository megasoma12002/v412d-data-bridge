"""Unit tests for month-end data freshness (ops only; no network)."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import ops_month_end_data_freshness as fr  # noqa: E402


class FreshnessTests(unittest.TestCase):
    def test_live_market_tip(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "live_market.csv"
            tip = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%d")
            p.write_text(
                "date,code,close\n2020-01-01,2880,10\n" + f"{tip},2880,11\n",
                encoding="utf-8",
            )
            row = fr.live_market_tip(p)
            self.assertTrue(row["exists"])
            self.assertEqual(row["tip_date"], tip)
            self.assertEqual(row["age_cal_days"], 2)

    def test_collect_fresh_ok_with_fixtures(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            market = tmp / "live_market.csv"
            tip = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
            market.write_text(f"date,code,close\n{tip},2880,11\n", encoding="utf-8")
            events = tmp / "e22_dividend_events.csv"
            events.write_text("code,cash_dividend\n2880,1.0\n", encoding="utf-8")
            fetch = tmp / "e22_dividend_fetch_status.json"
            fetch.write_text(json.dumps({"status": "PASS", "rows": 1}), encoding="utf-8")
            shadow = tmp / "DATA_SOURCE_SHADOW_RECONCILE.json"
            shadow.write_text(
                json.dumps(
                    {
                        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                        "all_ok": True,
                        "n_drift": 0,
                    }
                ),
                encoding="utf-8",
            )
            old = (
                fr.LIVE_MARKET,
                fr.E22_EVENTS,
                fr.E22_FETCH_STATUS,
                fr.E22_KPI,
                fr.SHADOW,
            )
            try:
                fr.LIVE_MARKET = market
                fr.E22_EVENTS = events
                fr.E22_FETCH_STATUS = fetch
                fr.E22_KPI = tmp / "missing_kpi.json"
                fr.SHADOW = shadow
                payload = fr.collect_freshness(
                    market_max_age=7, e22_max_age=45, shadow_max_age=45
                )
                self.assertTrue(payload["fresh_ok"])
                self.assertEqual(payload["hard_warnings"], [])
                self.assertEqual(payload["live_market"]["tip_date"], tip)
            finally:
                (
                    fr.LIVE_MARKET,
                    fr.E22_EVENTS,
                    fr.E22_FETCH_STATUS,
                    fr.E22_KPI,
                    fr.SHADOW,
                ) = old

    def test_stale_market_is_hard(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            market = tmp / "live_market.csv"
            tip = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
            market.write_text(f"date,code,close\n{tip},2880,11\n", encoding="utf-8")
            events = tmp / "e22.csv"
            events.write_text("code\n2880\n", encoding="utf-8")
            old = (
                fr.LIVE_MARKET,
                fr.E22_EVENTS,
                fr.E22_FETCH_STATUS,
                fr.E22_KPI,
                fr.SHADOW,
            )
            try:
                fr.LIVE_MARKET = market
                fr.E22_EVENTS = events
                fr.E22_FETCH_STATUS = tmp / "no_fetch.json"
                fr.E22_KPI = tmp / "no_kpi.json"
                fr.SHADOW = tmp / "no_shadow.json"
                payload = fr.collect_freshness(market_max_age=7, e22_max_age=45)
                self.assertFalse(payload["fresh_ok"])
                self.assertTrue(
                    any(w.startswith("live_market_tip_stale") for w in payload["hard_warnings"])
                )
            finally:
                (
                    fr.LIVE_MARKET,
                    fr.E22_EVENTS,
                    fr.E22_FETCH_STATUS,
                    fr.E22_KPI,
                    fr.SHADOW,
                ) = old


if __name__ == "__main__":
    unittest.main()
