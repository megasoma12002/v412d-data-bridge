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

        self.assertEqual(main([]), 0)

    def test_gate_fails_when_ok_false(self):
        from forward_tip_write_gate import evaluate

        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            post = td_path / "POST_FORWARD_E22_VERIFY.json"
            tip = td_path / "portfolio_state.json"
            qc = td_path / "qc_status.json"
            post.write_text(json.dumps({"ok": False, "failures": ["x"]}) + "\n")
            tip.write_text(json.dumps({"e22_books_version": "E22_v3_recv_pay_effdelay"}) + "\n")
            qc.write_text(json.dumps({"status": "PASS", "exact_t1_ok": True}) + "\n")
            ok, failures = evaluate(post_path=post, tip_path=tip, qc_path=qc)
            self.assertFalse(ok)
            self.assertTrue(any("ok!=true" in f for f in failures))

    def test_gate_fails_when_qc_missing(self):
        from forward_tip_write_gate import evaluate

        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            post = td_path / "POST_FORWARD_E22_VERIFY.json"
            tip = td_path / "portfolio_state.json"
            qc = td_path / "qc_status.json"
            post.write_text(json.dumps({"ok": True}) + "\n")
            tip.write_text(json.dumps({"e22_books_version": "E22_v3_recv_pay_effdelay"}) + "\n")
            ok, failures = evaluate(post_path=post, tip_path=tip, qc_path=qc)
            self.assertFalse(ok)
            self.assertTrue(any("qc_status" in f for f in failures))

    def test_gate_fails_when_exact_t1_false(self):
        from forward_tip_write_gate import evaluate

        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            post = td_path / "POST_FORWARD_E22_VERIFY.json"
            tip = td_path / "portfolio_state.json"
            qc = td_path / "qc_status.json"
            post.write_text(json.dumps({"ok": True}) + "\n")
            tip.write_text(json.dumps({"e22_books_version": "E22_v3_recv_pay_effdelay"}) + "\n")
            qc.write_text(json.dumps({"status": "PASS", "exact_t1_ok": False}) + "\n")
            ok, failures = evaluate(post_path=post, tip_path=tip, qc_path=qc)
            self.assertFalse(ok)
            self.assertTrue(any("exact_t1_ok" in f for f in failures))

    def test_gate_fails_when_qc_status_fail(self):
        from forward_tip_write_gate import evaluate

        with tempfile.TemporaryDirectory() as td:
            td_path = Path(td)
            post = td_path / "POST_FORWARD_E22_VERIFY.json"
            tip = td_path / "portfolio_state.json"
            qc = td_path / "qc_status.json"
            post.write_text(json.dumps({"ok": True}) + "\n")
            tip.write_text(json.dumps({"e22_books_version": "E22_v3_recv_pay_effdelay"}) + "\n")
            qc.write_text(json.dumps({"status": "FAIL", "exact_t1_ok": True}) + "\n")
            ok, failures = evaluate(post_path=post, tip_path=tip, qc_path=qc)
            self.assertFalse(ok)
            self.assertTrue(any("status=" in f for f in failures))


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
