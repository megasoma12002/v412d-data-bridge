#!/usr/bin/env python3
"""Guards for Path3 COMP/SAT daily share SSOT (0kab)."""
from __future__ import annotations

import unittest

from path3_comp_sat_daily_share_ssot import (
    ENGINE_ID,
    dollar_mix,
    plan_delta_ledger_scaled,
    shares_panel_from_long,
)
import pandas as pd


class LedgerScaledRecon(unittest.TestCase):
    def test_scale_mix_produces_fin_delta(self) -> None:
        live_pos = {
            "2880": 2_700_000.0,
            "2886": 2_200_000.0,
            "2892": 3_100_000.0,
            "5880": 4_200_000.0,
            "2412": 80_000.0,
            "3045": 100_000.0,
            "4904": 110_000.0,
            "0050": 300_000.0,
        }
        prices = {
            "2880": 45.0,
            "2886": 50.0,
            "2892": 40.0,
            "5880": 26.0,
            "2412": 145.0,
            "3045": 120.0,
            "4904": 105.0,
            "0050": 110.0,
        }
        # Paper ledger heavily tilted to 2880 within FIN
        ledger = {
            "2880": 5_000_000.0,
            "2886": 500_000.0,
            "2892": 500_000.0,
            "5880": 500_000.0,
            "2412": 100_000.0,
            "3045": 100_000.0,
            "4904": 100_000.0,
            "0050": 200_000.0,
        }
        delta, meta = plan_delta_ledger_scaled(
            live_pos=live_pos, prices=prices, ledger_shares=ledger, keep_0050=True
        )
        self.assertEqual(meta["engine_id"], ENGINE_ID)
        self.assertGreater(meta["n_delta_names"], 0)
        self.assertNotIn("0050", delta)
        self.assertIn("2880", meta["fin_mix"])
        self.assertGreater(meta["fin_mix"]["2880"], 0.4)

    def test_panel_from_long(self) -> None:
        df = pd.DataFrame(
            [
                {"date": "2026-01-02", "code": "2880", "shares": 1000},
                {"date": "2026-01-02", "code": "2886", "shares": 2000},
                {"date": "2026-01-03", "code": "2880", "shares": 1500},
            ]
        )
        pan = shares_panel_from_long(df)
        self.assertEqual(len(pan), 2)
        self.assertEqual(float(pan.loc[pd.Timestamp("2026-01-03"), "2880"]), 1500.0)

    def test_dollar_mix_sums_one(self) -> None:
        mix = dollar_mix({"2880": 1000, "2886": 1000}, {"2880": 40.0, "2886": 60.0}, ["2880", "2886"])
        self.assertAlmostEqual(sum(mix.values()), 1.0, places=6)


if __name__ == "__main__":
    unittest.main()
