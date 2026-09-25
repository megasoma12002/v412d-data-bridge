#!/usr/bin/env python3
"""Tests for ACCEPT deferred-ops harden (atomicity gate + tip-write gate + sandbox refuse)."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


class TipWriteGateTests(unittest.TestCase):
    def test_gate_passes_on_current_tip(self):
        from forward_tip_write_gate import main

        self.assertEqual(main(), 0)

    def test_gate_fails_when_ok_false(self):
        from forward_tip_write_gate import main

        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            post = td_path / "POST_FORWARD_E22_VERIFY.json"
            tip = td_path / "portfolio_state.json"
            post.write_text(json.dumps({"ok": False, "failures": ["x"]}) + "\n")
            tip.write_text(json.dumps({"e22_books_version": "E22_v3_recv_pay_effdelay"}) + "\n")
            with mock.patch("forward_tip_write_gate.POST", post):
                with mock.patch("forward_tip_write_gate.TIP", tip):
                    self.assertEqual(main(), 1)


class StageESandboxRefuseTests(unittest.TestCase):
    def test_refuses_forward_e21_out_dir(self):
        import subprocess
        import sys

        bad = ROOT / "forward" / "e21" / "should_not_write"
        proc = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "e22_stage_e_full_history_sandbox.py"),
                "--out-dir",
                str(bad),
            ],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("Refusing", proc.stderr + proc.stdout)


if __name__ == "__main__":
    unittest.main()
