#!/usr/bin/env python3
"""Smoke tests for major DD atlas Stage A helpers (research-only)."""
from __future__ import annotations

import unittest
from datetime import date

import numpy as np
import pandas as pd

from tipsoft_ip3_major_dd_atlas_stagea import (
    CHAMP_ARM,
    CLIFF_N,
    GRIND_MIN,
    PRIMARY_DEPTH_MAJOR,
    PRIMARY_DEPTH_MINOR,
    REF_WINDOWS,
    _classify_from_cross,
    _local_maxima,
    cross_era_score,
    detect_drawdown_episodes,
    global_verdict,
    measure_ref_episodes,
)


class MajorDdAtlasHelpers(unittest.TestCase):
    def test_constants_and_refs(self) -> None:
        self.assertEqual(CHAMP_ARM, "and::rvol63_l4&fuse_prem_neg5")
        self.assertEqual(PRIMARY_DEPTH_MINOR, 0.08)
        self.assertEqual(PRIMARY_DEPTH_MAJOR, 0.10)
        self.assertEqual(CLIFF_N, 20)
        self.assertEqual(GRIND_MIN, 40)
        tags = {r["tag"] for r in REF_WINDOWS}
        self.assertIn("EU_US_2011", tags)
        self.assertIn("TW_CN_2015", tags)
        self.assertIn("Q4_2018", tags)
        self.assertIn("MAR2020_CLIFF", tags)
        self.assertIn("MID2020_RESIDUAL", tags)
        self.assertIn("BEAR_2022", tags)

    def test_detect_cliff_and_grind(self) -> None:
        idx = pd.date_range("2020-02-01", periods=40, freq="B")
        vals = np.full(len(idx), 100.0)
        vals[5:14] = np.linspace(100, 88, 9)
        vals[14:] = np.linspace(88, 100, len(vals) - 14)
        nav = pd.Series(vals, index=idx)
        eps = detect_drawdown_episodes(nav, series="synth", depth_thr=0.08)
        self.assertTrue(any(e.auto_label == "CLIFF" for e in eps))

        idx2 = pd.date_range("2018-09-01", periods=80, freq="B")
        vals2 = np.full(len(idx2), 100.0)
        vals2[5:56] = np.linspace(100, 90, 51)
        vals2[56:] = np.linspace(90, 99, len(vals2) - 56)
        nav2 = pd.Series(vals2, index=idx2)
        eps2 = detect_drawdown_episodes(nav2, series="synth", depth_thr=0.08)
        self.assertTrue(any(e.auto_label == "GRIND" for e in eps2))

    def test_local_maxima_and_ref(self) -> None:
        vals = np.array([1.0, 2.0, 1.5, 3.0, 1.0, 2.5], dtype=float)
        peaks = _local_maxima(vals, order=1)
        self.assertIn(1, peaks)
        self.assertIn(3, peaks)
        idx = pd.date_range("2020-02-01", periods=30, freq="B")
        vals2 = np.full(len(idx), 100.0)
        vals2[5:20] = np.linspace(100, 85, 15)
        vals2[20:] = np.linspace(85, 95, len(vals2) - 20)
        nav = pd.Series(vals2, index=idx)
        refs = measure_ref_episodes(nav, series="synth")
        self.assertTrue(any("MAR2020_CLIFF" in e.ref_tags for e in refs))

    def test_cross_era_and_verdict(self) -> None:
        per = [
            {
                "arm": "base::rvol63_l4",
                "era": "2018",
                "verdict": "OOS_HIT",
            },
            {
                "arm": "base::rvol63_l4",
                "era": "2022",
                "verdict": "OOS_HIT",
            },
            {
                "arm": "base::rvol63_l4",
                "era": "2015",
                "verdict": "OOS_HIT",
            },
            {
                "arm": "base::rvol63_l4",
                "era": "2020_mar",
                "verdict": "OOS_HIT",
            },
            {
                "arm": "base::atr_like_20",
                "era": "2020_mar",
                "verdict": "OOS_HIT",
            },
            {
                "arm": "base::atr_like_20",
                "era": "2018",
                "verdict": "MISS",
            },
        ]
        excl = cross_era_score(per, exclude_mar2020=True)
        incl = cross_era_score(per, exclude_mar2020=False)
        self.assertEqual(excl[0]["arm"], "base::rvol63_l4")
        self.assertGreaterEqual(excl[0]["n_oos_hit"], 3)
        self.assertGreaterEqual(excl[0]["n_non2020_oos_hit"], 1)
        self.assertEqual(_classify_from_cross(excl[0]), "MAJOR_DD_ATLAS_ROBUST")
        self.assertEqual(
            _classify_from_cross(
                {
                    "n_oos_hit": 1,
                    "n_weak": 0,
                    "n_non2020_oos_hit": 0,
                    "eras_oos_hit": ["2020_mar"],
                    "eras_scored": ["2020_mar"],
                }
            ),
            "MAJOR_DD_ATLAS_ERA_SPECIFIC",
        )
        v, d = global_verdict(
            incl,
            excl,
            regime_counts={"CLIFF": 2, "GRIND": 3, "OTHER": 1, "n_major": 6},
        )
        self.assertEqual(v, "MAJOR_DD_ATLAS_ROBUST")
        self.assertIn("0kbj", d["implication"])


if __name__ == "__main__":
    unittest.main()
