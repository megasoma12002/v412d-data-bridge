#!/usr/bin/env python3
"""Guards for 2026-09-29 tip checklist + UAT readonly PREP + SAT decision artifacts."""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TipCatchup929Tests(unittest.TestCase):
    def test_assert_pending_while_tip_pre_holiday(self) -> None:
        rc = subprocess.call(
            [sys.executable, str(ROOT / "scripts" / "tip_catchup_assert_929.py")],
            cwd=str(ROOT),
        )
        # tip still 2026-09-24 → exit 1 pending
        self.assertEqual(rc, 1)

    def test_checklist_mentions_929_not_928(self) -> None:
        text = (ROOT / "research/ops/TIP_CATCHUP_2026-09-29_CHECKLIST.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("2026-09-29", text)
        self.assertIn("教師節", text)
        self.assertIn("中秋", text)


class UatReadonlyPrepTests(unittest.TestCase):
    def test_prep_waiting_operator(self) -> None:
        from ops_uat_readonly_prep_status import build_report

        r = build_report()
        self.assertTrue(r["execute_blocked"])
        self.assertTrue(r["send_stock_blocked"])
        self.assertTrue(r["send_algo_blocked"])
        self.assertEqual(r["status"], "PREP_OK_WAITING_OPERATOR")
        self.assertFalse(r["gate_violations"])


class SatA20DecisionTests(unittest.TestCase):
    def test_decision_json(self) -> None:
        p = ROOT / "research/ops/SAT_A20_H5_DECISION_2026-09-27.json"
        d = json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual(d["status"], "OPEN_OBSERVE_RECOMMENDED")
        self.assertFalse(d["live_wire"])
        self.assertEqual(d["next_tip_session"], "2026-09-29")


class R5ExampleFixtureTests(unittest.TestCase):
    def test_dropin_example_schema(self) -> None:
        import csv

        p = ROOT / "fixtures/r5_custody_dropin.example.csv"
        rows = list(csv.DictReader(p.open(encoding="utf-8")))
        self.assertGreaterEqual(len(rows), 1)
        self.assertTrue({"fill_id", "settle_date", "settlement_cash"} <= set(rows[0]))


if __name__ == "__main__":
    unittest.main()
