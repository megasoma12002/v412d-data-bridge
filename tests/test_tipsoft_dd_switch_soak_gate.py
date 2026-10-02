#!/usr/bin/env python3
"""Soak gate wiring tests (post-stabilize cadence)."""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TipsoftDdSwitchSoakGateTests(unittest.TestCase):
    def test_script_runs_and_writes(self) -> None:
        import tipsoft_dd_switch_soak_gate as gate

        payload = gate.collect()
        self.assertIn(payload["status"], ("SOAK_OPEN", "SOAK_PASS"))
        self.assertTrue(payload["checks"]["dd_switch_live"])
        self.assertTrue(payload["checks"]["broker_false"])
        self.assertTrue(payload["checks"]["path4_live_off"])
        gate.write_artifacts(payload)
        self.assertTrue((ROOT / "research/ops/TIPSOFT_DD_SWITCH_SOAK_GATE.md").exists())
        self.assertTrue((ROOT / "research/ops/TIPSOFT_DD_SWITCH_SOAK_GATE.json").exists())

    def test_freeze_lists_present(self) -> None:
        import tipsoft_dd_switch_soak_gate as gate

        payload = gate.collect()
        joined = " ".join(payload["freeze_until_soak_pass"])
        self.assertIn("Soft FIN/TEL", joined)
        self.assertIn("Path4", joined)
        self.assertIn("broker", joined)


if __name__ == "__main__":
    unittest.main()
