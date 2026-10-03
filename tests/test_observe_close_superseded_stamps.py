#!/usr/bin/env python3
"""Hygiene: superseded observe OPEN stamps stay SUPERSEDED_CLOSED.

Soft-Frozen KEEP · no live cutover · no broker write.
Canonical close batch: OBSERVE_CLOSE_SUPERSEDED_2026-10-01.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "research" / "ops"

# tip Soft old stack OPEN JSONs closed by OBSERVE_CLOSE_SUPERSEDED_2026-10-01
CLOSED_OPEN_JSON = (
    "TIPSOFT_P3_NEARPEAK3_DUAL_PAPER_OBSERVE_OPEN.json",
    "TIPSOFT_IP3_HIGHON_CASH_DUAL_PAPER_OBSERVE_OPEN.json",
    "TIPSOFT_IP3_TRAIL42_CASH_DUAL_PAPER_OBSERVE_OPEN.json",
)

# Path3 paper shadows — MD-only OPEN pointers (no OPEN JSON)
CLOSED_OPEN_MD = (
    "FIN_SAT_COMPOSITE_DUAL_PAPER_OBSERVE_OPEN.md",
    "SAT_A20_RELAX_DUAL_PAPER_OBSERVE_OPEN.md",
    "FIN_SAT_PATH3_T0_DUAL_PAPER_OBSERVE_OPEN.md",
)

# Observe KEEP twins — must remain open/operating
KEEP_OPEN_JSON = (
    "TIPSOFT_IP3_TRAIL42_L4_SWITCH_DUAL_PAPER_OBSERVE_OPEN.json",
    "TIPSOFT_IP3_LIVE_OVERRIDE_DUAL_PAPER_OBSERVE_OPEN.json",
)


class ObserveCloseSupersededStampTests(unittest.TestCase):
    def test_closed_open_json_status_and_label(self) -> None:
        for name in CLOSED_OPEN_JSON:
            path = OPS / name
            self.assertTrue(path.exists(), msg=name)
            doc = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(doc.get("status"), "SUPERSEDED_CLOSED", msg=name)
            self.assertEqual(doc.get("closed_by"), "OBSERVE_CLOSE_SUPERSEDED_2026-10-01", msg=name)
            label = str(doc.get("label") or "")
            self.assertIn("SUPERSEDED_CLOSED", label, msg=f"{name} label={label}")
            self.assertNotIn("__OBSERVE_OPEN__", label, msg=f"{name} label={label}")

    def test_closed_open_md_status_line(self) -> None:
        for name in CLOSED_OPEN_MD:
            text = (OPS / name).read_text(encoding="utf-8")
            self.assertIn("SUPERSEDED_CLOSED", text, msg=name)
            self.assertIn("OBSERVE_CLOSE_SUPERSEDED_2026-10-01", text, msg=name)

    def test_keep_open_twins_not_closed(self) -> None:
        for name in KEEP_OPEN_JSON:
            doc = json.loads((OPS / name).read_text(encoding="utf-8"))
            status = str(doc.get("status") or "")
            # LIVE_OVERRIDE uses OPEN_OPERATING; DD_SWITCH uses OBSERVE_OPEN
            self.assertIn(
                status,
                ("OBSERVE_OPEN", "OPEN_OPERATING"),
                msg=f"{name} unexpected status={status}",
            )


if __name__ == "__main__":
    unittest.main()
