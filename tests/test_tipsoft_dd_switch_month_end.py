#!/usr/bin/env python3
"""Stabilize wiring: DD_SWITCH month-end monitor + pack/alert scan hooks."""
from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TipsoftDdSwitchMonthEndTests(unittest.TestCase):
    def test_monitor_module_importable(self) -> None:
        import tipsoft_ip3_trail42_l4_switch_month_end_monitor as mon

        self.assertEqual(mon.SPEC.chal_id, "TRAIL42_L4_DD_SWITCH")
        self.assertEqual(mon.SPEC.base_id, "L4_LIVE_P3_WITHIN")
        self.assertTrue(mon.SPEC.base_nav.exists())
        self.assertTrue(mon.SPEC.chal_nav.exists())

    def test_pack_includes_dd_switch_steps(self) -> None:
        text = (ROOT / "scripts/ops_month_end_paper_pack.py").read_text(encoding="utf-8")
        self.assertIn("tipsoft_ip3_trail42_l4_switch_month_end", text)
        self.assertIn("tipsoft_ip3_trail42_l4_switch_dual_paper_ledgers", text)

    def test_alert_scan_includes_dd_switch(self) -> None:
        text = (ROOT / "scripts/ops_alert_scan.py").read_text(encoding="utf-8")
        self.assertIn("TIPSOFT_IP3_TRAIL42_L4_SWITCH_JSON", text)
        self.assertIn("tipsoft_ip3_trail42_l4_switch_month_end", text)

    def test_stabilize_ballot_present(self) -> None:
        md = ROOT / "research/ops/TIPSOFT_LIVE_STABILIZE_2026-10-02.md"
        self.assertTrue(md.exists())
        body = md.read_text(encoding="utf-8")
        self.assertIn("請穩定", body)
        self.assertIn("0kbe", body)


if __name__ == "__main__":
    unittest.main()
