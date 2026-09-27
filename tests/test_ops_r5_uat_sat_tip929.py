#!/usr/bin/env python3
"""Guards for 2026-09-29 tip checklist + UAT readonly PREP + SAT decision artifacts."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = "2026-09-29"
ASSERT_929 = ROOT / "scripts" / "tip_catchup_assert_929.py"


def _run_assert(state: Path | None = None) -> tuple[int, dict]:
    cmd = [sys.executable, str(ASSERT_929)]
    if state is not None:
        cmd.extend(["--state", str(state)])
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, check=False)
    out = json.loads(proc.stdout)
    return proc.returncode, out


class TipCatchup929Tests(unittest.TestCase):
    def test_assert_exit_matches_live_tip_contract(self) -> None:
        """Live tip: pending→1, PASS→0, stamp/date mismatch→2 (survives post-9/29)."""
        rc, out = _run_assert()
        last = str(out.get("last_date") or "")
        expect = str(out.get("expect_date") or TARGET)
        if last < expect:
            self.assertEqual(rc, 1)
            self.assertTrue(out["pending_holiday_gap"])
            self.assertFalse(out["ok"])
        elif out.get("ok"):
            self.assertEqual(rc, 0)
            self.assertEqual(last, expect)
            self.assertFalse(out["pending_holiday_gap"])
        else:
            self.assertEqual(rc, 2)
            self.assertFalse(out["ok"])

    def test_assert_pending_and_pass_via_temp_state(self) -> None:
        """Fixture paths do not depend on tip advancing."""
        pending = {
            "last_date": "2026-09-24",
            "e22_books_version": "E22_v3_recv_pay_effdelay",
            "cool_exposure_live": True,
            "dh_exposure_live": False,
            "conf_ret3_631l_live": True,
            "fin_priv_v7_f05_live": True,
            "soft_frozen_clip_flip": "ACCEPT_BETA_F0.60-0.80",
        }
        passed = {**pending, "last_date": TARGET}
        with tempfile.TemporaryDirectory() as td:
            p_pending = Path(td) / "pending.json"
            p_pass = Path(td) / "pass.json"
            p_pending.write_text(json.dumps(pending), encoding="utf-8")
            p_pass.write_text(json.dumps(passed), encoding="utf-8")
            rc1, out1 = _run_assert(p_pending)
            self.assertEqual(rc1, 1)
            self.assertTrue(out1["pending_holiday_gap"])
            rc0, out0 = _run_assert(p_pass)
            self.assertEqual(rc0, 0)
            self.assertTrue(out0["ok"])

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
