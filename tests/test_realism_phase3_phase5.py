#!/usr/bin/env python3
"""Phase 3 (R4/tip-lag alerts) + Phase 5 (div cron) guards."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
ALERT = SCRIPTS / "ops_alert_scan.py"
DIV_WF = ROOT / ".github" / "workflows" / "v412e22-dividend-events.yml"


class Phase3R4TipLagAlerts(unittest.TestCase):
    def test_source_wires_r4_and_tip_lag_codes(self):
        src = ALERT.read_text(encoding="utf-8")
        self.assertIn("R4_ESTIMATE_MISSING", src)
        self.assertIn("R4_ESTIMATE_PRESENT", src)
        self.assertIn("TIP_LAG_BOOKS", src)
        self.assertIn("liquidity view", src.lower())
        self.assertIn("DIV_APPLIED_MISSING_IN_RECV_WINDOW", src)
        self.assertIn("DIV_APPLIED_EMPTY_IN_RECV_WINDOW", src)
        self.assertIn("settlement_cash_estimate", src)

    def test_scan_emits_tip_lag_and_r4_present_on_repo_tip(self):
        if not (ROOT / "forward/e21/settlement_cash_estimate.json").exists():
            self.skipTest("no R4 artifact")
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            rc = subprocess.call(
                [sys.executable, str(ALERT), "--out-dir", str(out), "--report-only"],
                cwd=str(ROOT),
            )
            self.assertEqual(rc, 0)
            payload = json.loads((out / "OPS_ALERTS.json").read_text())
            codes = {a["code"] for a in payload["alerts"]}
            self.assertIn("R4_ESTIMATE_PRESENT", codes)
            self.assertNotIn("R4_ESTIMATE_MISSING", codes)
            # Current tip lags Stage-E until weekday forward.
            gap6 = json.loads((ROOT / "research/ops/E22_GAP6_FIDELITY_KPI.json").read_text())
            obs = (gap6.get("live_ledger") or {}).get("observed_books_version")
            default = (gap6.get("code_wire") or {}).get("default_books_version")
            if obs and default and obs != default:
                self.assertIn("TIP_LAG_BOOKS", codes)
                tip = next(a for a in payload["alerts"] if a["code"] == "TIP_LAG_BOOKS")
                self.assertEqual(tip["severity"], "INFO")


class Phase5DividendCron(unittest.TestCase):
    def test_dividend_workflow_has_weekday_cron(self):
        yml = DIV_WF.read_text(encoding="utf-8")
        self.assertIn("schedule:", yml)
        self.assertIn("0 7 * * 1-5", yml)
        self.assertIn("data/dividend_events", yml)
        self.assertIn("no Soft-Frozen", yml)
        # Fetch-only — must not touch forward/e21.
        self.assertNotIn("forward/e21", yml)


if __name__ == "__main__":
    unittest.main()
