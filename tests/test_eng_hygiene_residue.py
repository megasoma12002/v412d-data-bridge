#!/usr/bin/env python3
"""Eng / hygiene residue guards (docs drift, LIVE_KD SSOT, session lock).

Soft-Frozen KEEP · no live cutover · no broker write.
"""
from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

LIVE_KD_LITERAL = re.compile(r"^LIVE_KD\s*=\s*\{", re.M)
CAPITAL_LITERAL_500M = re.compile(
    r"^(?:CAPITAL|CHARTER_CAPITAL|CAPITAL_PRIMARY)\s*=\s*500_000_000(?:\.0)?\s*$",
    re.M,
)


class LiveKdSsotGuards(unittest.TestCase):
    def test_no_live_kd_dict_literals_in_scripts(self) -> None:
        bad: list[str] = []
        for path in sorted(SCRIPTS.glob("*.py")):
            text = path.read_text(encoding="utf-8")
            if LIVE_KD_LITERAL.search(text):
                bad.append(path.name)
        self.assertEqual(bad, [], msg=f"LIVE_KD dict literals: {bad}")

    def test_soft_assist_live_kd_is_live_config(self) -> None:
        from live_config import KD_OPT
        from soft_assist_helpers import LIVE_KD

        self.assertIs(LIVE_KD, KD_OPT)


class CapitalSsotGuards(unittest.TestCase):
    def test_no_500m_capital_assignment_literals(self) -> None:
        """Live 500M must flow from portfolio_capital.DEFAULT_CAPITAL."""
        allow = {"portfolio_capital.py"}
        bad: list[str] = []
        for path in sorted(SCRIPTS.glob("*.py")):
            if path.name in allow:
                continue
            text = path.read_text(encoding="utf-8")
            if CAPITAL_LITERAL_500M.search(text):
                bad.append(path.name)
        self.assertEqual(bad, [], msg=f"500M capital literals: {bad}")


class SessionLockGuards(unittest.TestCase):
    def test_pipeline_acquires_session_lock(self) -> None:
        pipe = (SCRIPTS / "e21_forward_pipeline.py").read_text(encoding="utf-8")
        self.assertIn("acquire_session_lock", pipe)
        self.assertIn("_run_locked_session", pipe)
        self.assertIn("BlockingIOError", pipe)

    def test_session_lock_name_distinct_from_broker(self) -> None:
        from broker_safety import LOCK_FILENAME
        from live_session_io import SESSION_LOCK_NAME

        self.assertEqual(SESSION_LOCK_NAME, "e21_session.lock")
        self.assertNotEqual(SESSION_LOCK_NAME, LOCK_FILENAME)

    def test_session_lock_fail_closed_when_held(self) -> None:
        from live_session_io import acquire_session_lock

        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            with acquire_session_lock(sdir, blocking=False):
                with self.assertRaises(BlockingIOError):
                    with acquire_session_lock(sdir, blocking=False):
                        pass


class DocsTipBooksGuards(unittest.TestCase):
    def test_strategy_debt_board_live_ssot_mentions_v3(self) -> None:
        text = (ROOT / "research" / "STRATEGY_DEBT_BOARD.md").read_text(encoding="utf-8")
        self.assertIn("E22_v3_recv_pay_effdelay", text.split("## Debt-sweep")[0])
        self.assertIn("DROPPED", text)
        self.assertIn("e21_session.lock", text)


if __name__ == "__main__":
    unittest.main()
