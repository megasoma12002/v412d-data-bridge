#!/usr/bin/env python3
"""Guards for full-repo review hardenings (path/port split, T+1 NaT, fail-closed logs)."""
from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

import pandas as pd

from broker_risk import RiskConfig, pre_submit_risk_check
from broker_safety import (
    already_broker_deduped,
    already_submitted,
    count_live_submits_today,
)
from live_day_commit import commit_day_books
from live_fill_core import _exact_t1_stats
from live_session_io import CANON_STATE, assert_canonical_live_paths


class CanonicalPathPortSplit(unittest.TestCase):
    def test_canon_state_refuses_broker_even_with_allow_noncanonical(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            assert_canonical_live_paths(
                state_dir=CANON_STATE,
                market_path=CANON_STATE / "live_market.csv",
                fill_port_name="broker",
                allow_noncanonical=True,
            )
        self.assertIn("Soft-Frozen canonical", str(ctx.exception))

    def test_research_copy_allows_dry_run_with_flag(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            market = sdir / "m.csv"
            market.write_text("date,code\n", encoding="utf-8")
            # Should not raise
            assert_canonical_live_paths(
                state_dir=sdir,
                market_path=market,
                fill_port_name="dry_run",
                allow_noncanonical=True,
            )


class ExactT1NatFailClosed(unittest.TestCase):
    def test_missing_dates_count_as_violation(self) -> None:
        same, ok = _exact_t1_stats(
            [{"signal_date": None, "fill_date": "2026-07-13"}]
        )
        self.assertEqual(same, 1)
        self.assertFalse(ok)

    def test_valid_t1_ok(self) -> None:
        same, ok = _exact_t1_stats(
            [{"signal_date": "2026-07-10", "fill_date": "2026-07-13"}]
        )
        self.assertEqual(same, 0)
        self.assertTrue(ok)


class RiskConfigCorruptFailClosed(unittest.TestCase):
    def test_corrupt_risk_json_panics(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            pref = sdir / "broker_preflight"
            pref.mkdir(parents=True)
            (pref / "broker_risk.json").write_text("{not-json", encoding="utf-8")
            cfg = RiskConfig.load(sdir)
            self.assertTrue(cfg.panic)
            r = pre_submit_risk_check(
                sdir, code="0050", side="BUY", quantity=1000, price=100.0
            )
            self.assertFalse(r.allowed)


class BrokerLogCorruptFailClosed(unittest.TestCase):
    def test_corrupt_submit_log_raises(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            pref = sdir / "broker_preflight"
            pref.mkdir(parents=True)
            (pref / "broker_submit_log.jsonl").write_text(
                "{bad\n", encoding="utf-8"
            )
            with self.assertRaises(SystemExit):
                already_submitted(sdir, "x")
            with self.assertRaises(SystemExit):
                count_live_submits_today(sdir, date(2026, 7, 13))

    def test_corrupt_dedupe_log_raises(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            pref = sdir / "broker_preflight"
            pref.mkdir(parents=True)
            (pref / "broker_dedupe_log.jsonl").write_text("{bad\n", encoding="utf-8")
            with self.assertRaises(SystemExit):
                already_broker_deduped(sdir, "k")


class DayCommitPaperOnly(unittest.TestCase):
    def test_paper_commits_fills_broker_does_not(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            fills = [
                {
                    "fill_id": "o1",
                    "signal_date": "2026-07-10",
                    "fill_date": "2026-07-13",
                    "code": "0050",
                    "side": "BUY",
                    "quantity": 1000,
                    "fill_price": 100.0,
                    "gross": 100000.0,
                    "fees_tax": 20.0,
                    "slippage_bp": 5.0,
                }
            ]
            state_path = sdir / "portfolio_state.json"
            commit_day_books(
                state_dir=sdir,
                fill_port_name="broker",
                fills=fills,
                pending_div_rows=[],
                div_path=sdir / "dividends_applied.csv",
                state_path=state_path,
                state_payload={"cash": 1.0, "positions": {}, "last_date": "2026-07-13"},
                signal={"date": "2026-07-13"},
                navrow={"date": "2026-07-13", "nav_e16_e18": 1.0},
                order_rows=[],
                applied_details=[],
                asof_iso="2026-07-13",
            )
            self.assertFalse((sdir / "fills.csv").exists())
            self.assertTrue(state_path.exists())

            commit_day_books(
                state_dir=sdir,
                fill_port_name="paper",
                fills=fills,
                pending_div_rows=[],
                div_path=sdir / "dividends_applied.csv",
                state_path=state_path,
                state_payload={"cash": 1.0, "positions": {}, "last_date": "2026-07-13"},
                signal={"date": "2026-07-13"},
                navrow={"date": "2026-07-13", "nav_e16_e18": 1.0},
                order_rows=[],
                applied_details=[],
                asof_iso="2026-07-13",
            )
            self.assertTrue((sdir / "fills.csv").exists())
            df = pd.read_csv(sdir / "fills.csv")
            self.assertEqual(list(df["fill_id"]), ["o1"])


if __name__ == "__main__":
    unittest.main()
