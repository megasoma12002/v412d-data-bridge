#!/usr/bin/env python3
"""Class D FinPriv V7 F05 live cutover unit tests."""
from __future__ import annotations

import unittest
from datetime import date
from pathlib import Path

import pandas as pd

import live_finhc_v7_f05_cutover as cut


class FinPrivV7F05CutoverTests(unittest.TestCase):
    def test_gate_bull_side_only(self) -> None:
        self.assertTrue(cut.gate_reg_bull_side("Bull"))
        self.assertTrue(cut.gate_reg_bull_side("Sideways"))
        self.assertFalse(cut.gate_reg_bull_side("Bear"))
        self.assertFalse(cut.gate_reg_bull_side("Crisis"))

    def test_pub_share(self) -> None:
        self.assertAlmostEqual(cut.pub_share_for_gate(True), 0.95)
        self.assertAlmostEqual(cut.pub_share_for_gate(False), 1.0)

    def test_priv_panel_fresh_vs_live_asof(self) -> None:
        ok, meta = cut.priv_prices_fresh_enough(pd.Timestamp("2026-09-24"))
        self.assertTrue(ok, msg=meta)
        self.assertFalse(meta.get("stale_or_missing"))

    def test_resolve_gate_fail_closed_on_stale(self) -> None:
        # Far-future asof vs tip → lag > 5d → fail-closed even if Bull.
        gate_on, meta = cut.resolve_gate(
            regime_today="Bull", asof=pd.Timestamp("2099-01-01")
        )
        self.assertFalse(gate_on)
        self.assertTrue(meta["fin_priv_skipped_missing_px"])
        self.assertTrue(meta["want_gate"])

    def test_resolve_gate_on_when_fresh_bull(self) -> None:
        gate_on, meta = cut.resolve_gate(
            regime_today="Bull", asof=pd.Timestamp("2026-09-24")
        )
        self.assertTrue(gate_on, msg=meta)
        self.assertFalse(meta["fin_priv_skipped_missing_px"])

    def test_force_sell_priv(self) -> None:
        def _oid(*, signal_date, code, side):
            return f"{signal_date}_{code}_{side}"

        rows = cut.force_sell_priv_order_rows(
            pos={"2884": 5000, "2880": 1000, "2885": 500},
            prices={"2884": 45.0, "2885": 70.0},
            signal_date=date(2026, 9, 24),
            make_order_id=_oid,
        )
        codes = {r["code"] for r in rows}
        self.assertEqual(codes, {"2884"})  # 2885 below board lot; 2880 not PRIV
        self.assertEqual(rows[0]["side"], "SELL")
        self.assertEqual(rows[0]["quantity"], 5000)

    def test_live_config_flag(self) -> None:
        from live_config import LIVE_FIN_PRIV_BALLOT, LIVE_FIN_PRIV_V7_F05

        self.assertTrue(LIVE_FIN_PRIV_V7_F05)
        self.assertEqual(LIVE_FIN_PRIV_BALLOT, cut.HUMAN_ACCEPT)
        self.assertTrue(cut.PRIVATE_ADJ.exists())


if __name__ == "__main__":
    unittest.main()
