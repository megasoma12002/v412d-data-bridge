#!/usr/bin/env python3
"""Phase 0–1 post-forward verify guards (no Soft-Frozen / no promote)."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
WF = ROOT / ".github" / "workflows" / "v412f-forward-paper.yml"
WF2 = ROOT / ".github" / "workflows" / "post-forward-e22-verify.yml"


class PostForwardVerifyScript(unittest.TestCase):
    def test_r4_assert_fails_when_missing(self):
        with tempfile.TemporaryDirectory() as td:
            state = Path(td)
            rc = subprocess.call(
                [
                    sys.executable,
                    str(SCRIPTS / "post_forward_e22_verify.py"),
                    "--state-dir",
                    str(state),
                    "--require-r4",
                    "--skip-qc",
                    "--report-only",
                ],
                cwd=str(ROOT),
            )
            # report-only still exits non-zero before writing when assert raises SystemExit
            self.assertNotEqual(rc, 0)

    def test_r4_assert_ok_and_tip_lag_does_not_fail(self):
        """Against live forward/e21: R4 present; tip may lag Stage-E — gate must PASS."""
        state = ROOT / "forward" / "e21"
        if not (state / "settlement_cash_estimate.json").exists():
            self.skipTest("no R4 artifact in checkout")
        rc = subprocess.call(
            [
                sys.executable,
                str(SCRIPTS / "post_forward_e22_verify.py"),
                "--state-dir",
                str(state),
                "--require-r4",
                "--skip-qc",
                "--fail-on",
                "critical",
            ],
            cwd=str(ROOT),
        )
        self.assertEqual(rc, 0)
        payload = json.loads((ROOT / "research/ops/POST_FORWARD_E22_VERIFY.json").read_text())
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["failures"], [])
        self.assertTrue(payload["steps"]["r4_assert"]["ok"])
        # Current tip may lag; must be recorded without failing.
        if payload.get("tip_lag"):
            self.assertTrue(any("TIP_LAG" in n for n in payload.get("notes") or []))


class ForwardWorkflowPhase01(unittest.TestCase):
    def test_v412f_wires_phase0_and_phase1(self):
        yml = WF.read_text(encoding="utf-8")
        self.assertIn("settlement_cash_estimate.csv", yml)
        self.assertIn("Phase 0", yml)
        self.assertIn("post_forward_e22_verify.py", yml)
        self.assertIn("--require-r4", yml)
        self.assertIn("--skip-qc", yml)
        self.assertIn("POST_FORWARD_E22_VERIFY", yml)
        # Still no obsolete capital hardcode.
        self.assertNotRegex(yml, r"--capital\s+3_?000_?000")

    def test_standalone_verify_workflow_exists(self):
        self.assertTrue(WF2.is_file())
        yml = WF2.read_text(encoding="utf-8")
        self.assertIn("post_forward_e22_verify.py", yml)
        self.assertIn("workflow_run", yml)
        self.assertIn("V4.12-F E21 Daily Forward Paper", yml)


if __name__ == "__main__":
    unittest.main()
