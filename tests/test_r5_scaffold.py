#!/usr/bin/env python3
"""Phase 4 R5 scaffold guards (synthetic custody · no Soft-Frozen / no live-write)."""
from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "fixtures" / "r5_custody_synthetic.csv"
WF = ROOT / ".github" / "workflows" / "r5-broker-reconcile.yml"
EST = ROOT / "forward" / "e21" / "settlement_cash_estimate.csv"


class R5Scaffold(unittest.TestCase):
    def test_synthetic_fixture_exists_and_has_schema(self):
        self.assertTrue(FIX.is_file())
        rows = list(csv.DictReader(FIX.open(encoding="utf-8")))
        self.assertGreater(len(rows), 0)
        self.assertTrue({"fill_id", "settle_date", "settlement_cash"} <= set(rows[0]))

    def test_workflow_is_observe_only(self):
        yml = WF.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch", yml)
        self.assertIn("twse_t2_broker_reconcile.py", yml)
        self.assertIn("r5_custody_synthetic.csv", yml)
        self.assertNotIn("broker_live_write", yml)
        self.assertNotIn("SendAlgo", yml)

    def test_synthetic_reconcile_all_ok(self):
        if not EST.is_file():
            self.skipTest("no R4 estimate in checkout")
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            rc = subprocess.call(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "twse_t2_broker_reconcile.py"),
                    "--estimate",
                    str(EST),
                    "--custody",
                    str(FIX),
                    "--asof",
                    "2026-09-16",
                    "--out-dir",
                    str(out),
                ],
                cwd=str(ROOT),
            )
            self.assertEqual(rc, 0)
            pack = json.loads((out / "t2_broker_reconcile_latest.json").read_text())
            self.assertTrue(pack["all_ok"])
            self.assertEqual(pack["n_mismatches"], 0)

    def test_refuses_external_custody_without_flag(self):
        with tempfile.TemporaryDirectory() as td:
            cust = Path(td) / "external.csv"
            cust.write_text("fill_id,settle_date,settlement_cash\n", encoding="utf-8")
            out = Path(td) / "out"
            rc = subprocess.call(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "twse_t2_broker_reconcile.py"),
                    "--estimate",
                    str(EST) if EST.is_file() else str(cust),
                    "--custody",
                    str(cust),
                    "--out-dir",
                    str(out),
                    "--asof",
                    "2026-09-16",
                ],
                cwd=str(ROOT),
                stderr=subprocess.PIPE,
            )
            self.assertNotEqual(rc, 0)

    def test_refuses_live_tree_out_without_flag(self):
        if not EST.is_file():
            self.skipTest("no R4 estimate in checkout")
        live_out = ROOT / "forward" / "e21" / "broker_reconcile_test_jail"
        try:
            rc = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "twse_t2_broker_reconcile.py"),
                    "--estimate",
                    str(EST),
                    "--custody",
                    str(FIX),
                    "--asof",
                    "2026-09-16",
                    "--out-dir",
                    str(live_out),
                ],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(rc.returncode, 0)
            self.assertIn("Refusing to write R5 reconcile under live tree", rc.stderr + rc.stdout)
        finally:
            # Ensure we did not leave artifacts if somehow written
            if live_out.exists():
                import shutil

                shutil.rmtree(live_out, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
