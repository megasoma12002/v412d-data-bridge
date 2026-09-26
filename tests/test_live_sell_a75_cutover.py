#!/usr/bin/env python3
"""SELL_a75 under COOL live cutover unit tests."""
from __future__ import annotations

import unittest


class SellA75LiveCutoverTests(unittest.TestCase):
    def test_live_config_boost_and_ballot(self) -> None:
        from live_config import (
            LIVE_COOL_EXPOSURE,
            LIVE_FUSE_ADDITIVE,
            LIVE_FUSE_SOFT_SELL_BALLOT,
            LIVE_FUSE_SOFT_SELL_BOOST,
        )
        import live_dh_fuse_cutover as cut

        self.assertTrue(LIVE_FUSE_ADDITIVE)
        self.assertTrue(LIVE_COOL_EXPOSURE)
        self.assertAlmostEqual(float(LIVE_FUSE_SOFT_SELL_BOOST), 0.75)
        self.assertEqual(
            LIVE_FUSE_SOFT_SELL_BALLOT,
            "ACCEPT Live cutover: SELL_a75 under COOL (keep FUSE+COOL)",
        )
        self.assertAlmostEqual(cut.SELL_BOOST_LIVE, 0.75)
        self.assertEqual(cut.HUMAN_ACCEPT_SELL_A75, LIVE_FUSE_SOFT_SELL_BALLOT)
        self.assertIn("SELL_a75", cut.SOFT_ID)

    def test_independent_soft_observe_stays_a05(self) -> None:
        from soft_assist_helpers import OBSERVE_CHAL_ID, SELL_SOFT_BOOST

        self.assertAlmostEqual(float(SELL_SOFT_BOOST), 0.5)
        self.assertIn("SELL_a05", OBSERVE_CHAL_ID)

    def test_observe_sell_panel_boost_override(self) -> None:
        import pandas as pd
        from soft_assist_helpers import SELL_HIGH_ID, build_observe_sell_panel

        idx = pd.DatetimeIndex(["2026-01-02", "2026-01-03"])
        cols = ["2884"]
        highs = {
            SELL_HIGH_ID: pd.DataFrame(True, index=idx, columns=cols),
        }
        a05 = build_observe_sell_panel(highs)
        a75 = build_observe_sell_panel(highs, boost=0.75)
        self.assertAlmostEqual(float(a05.iloc[0, 0]), 1.5)
        self.assertAlmostEqual(float(a75.iloc[0, 0]), 1.75)


if __name__ == "__main__":
    unittest.main()
