#!/usr/bin/env python3
"""Smoke tests for cliff vs grind Stage A helpers (research-only)."""
from __future__ import annotations

import unittest
from datetime import date

import numpy as np
import pandas as pd

from tipsoft_ip3_crisis_cliff_vs_grind_stagea import (
    CHAMP_ARM,
    CLIFF_N_DAYS,
    GRIND_MIN_DAYS,
    PRIMARY_CLIFF_N,
    PRIMARY_DEPTH,
    PRIMARY_GRIND_MIN,
    REF_WINDOWS,
    _local_maxima,
    _mask_for_episodes,
    _specialize,
    detect_drawdown_episodes,
    global_verdict,
    measure_ref_episodes,
)


class CliffVsGrindHelpers(unittest.TestCase):
    def test_constants_and_refs(self) -> None:
        self.assertEqual(CHAMP_ARM, "and::rvol63_l4&fuse_prem_neg5")
        self.assertEqual(PRIMARY_DEPTH, 0.08)
        self.assertIn(PRIMARY_CLIFF_N, CLIFF_N_DAYS)
        self.assertIn(PRIMARY_GRIND_MIN, GRIND_MIN_DAYS)
        tags = {r["tag"] for r in REF_WINDOWS}
        self.assertIn("MAR2020_CLIFF", tags)
        self.assertIn("TW_CN_2015", tags)
        self.assertIn("Q4_2018", tags)
        self.assertIn("MID2020_RESIDUAL", tags)

    def test_detect_cliff_episode(self) -> None:
        # Peak then sharp 12% drop in 8 days, then recover
        idx = pd.date_range("2020-02-01", periods=40, freq="B")
        vals = np.full(len(idx), 100.0)
        vals[5:14] = np.linspace(100, 88, 9)  # ~12% in 8 steps
        vals[14:] = np.linspace(88, 100, len(vals) - 14)
        nav = pd.Series(vals, index=idx)
        eps = detect_drawdown_episodes(
            nav, series="synth", depth_thr=0.08, cliff_n=15, grind_min=40
        )
        self.assertGreaterEqual(len(eps), 1)
        self.assertTrue(any(e.auto_label == "CLIFF" for e in eps))
        cliff = next(e for e in eps if e.auto_label == "CLIFF")
        self.assertLessEqual(cliff.ttm_days, 15)
        self.assertGreaterEqual(cliff.depth, 0.08)

    def test_detect_grind_episode(self) -> None:
        # Slow 10% decline over 50 business days
        idx = pd.date_range("2018-09-01", periods=80, freq="B")
        vals = np.full(len(idx), 100.0)
        vals[5:56] = np.linspace(100, 90, 51)
        vals[56:] = np.linspace(90, 99, len(vals) - 56)
        nav = pd.Series(vals, index=idx)
        eps = detect_drawdown_episodes(
            nav, series="synth", depth_thr=0.08, cliff_n=15, grind_min=40
        )
        self.assertTrue(any(e.auto_label == "GRIND" for e in eps))
        grind = next(e for e in eps if e.auto_label == "GRIND")
        self.assertGreaterEqual(grind.ttm_days, 40)

    def test_mask_for_episodes(self) -> None:
        idx = pd.date_range("2020-02-01", periods=40, freq="B")
        vals = np.full(len(idx), 100.0)
        vals[5:14] = np.linspace(100, 88, 9)
        vals[14:] = 100.0
        nav = pd.Series(vals, index=idx)
        eps = detect_drawdown_episodes(
            nav, series="synth", depth_thr=0.08, cliff_n=15, grind_min=40
        )
        m = _mask_for_episodes(idx, eps, label="CLIFF")
        self.assertTrue(bool(m.any()))

    def test_local_maxima_and_ref_measure(self) -> None:
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
        self.assertTrue(any(e.ref_tags == ["MAR2020_CLIFF"] for e in refs))
        mar = next(e for e in refs if e.ref_tags == ["MAR2020_CLIFF"])
        self.assertEqual(mar.auto_label, "CLIFF")

    def test_specialize_and_global_verdict(self) -> None:
        cliff_spec = {
            "arm": CHAMP_ARM,
            "family": "and_combo",
            "cliff": {
                "verdict": "REGIME_HIT",
                "ic_spearman_fwd_mdd_10": 0.15,
                "hit_rate": 0.60,
                "recall": 0.40,
            },
            "grind": {
                "verdict": "REGIME_MISS",
                "ic_spearman_fwd_mdd_10": 0.01,
                "hit_rate": 0.45,
                "recall": 0.05,
            },
            "ic_delta_cliff_minus_grind": 0.14,
            "hit_delta_cliff_minus_grind": 0.15,
        }
        self.assertEqual(_specialize(cliff_spec), "CLIFF_SPECIALIST")
        no_split = {
            "arm": "base::rvol20_l4",
            "family": "baseline",
            "cliff": {
                "verdict": "REGIME_WEAK",
                "ic_spearman_fwd_mdd_10": 0.06,
                "hit_rate": 0.52,
                "recall": 0.25,
            },
            "grind": {
                "verdict": "REGIME_WEAK",
                "ic_spearman_fwd_mdd_10": 0.05,
                "hit_rate": 0.51,
                "recall": 0.22,
            },
            "ic_delta_cliff_minus_grind": 0.01,
            "hit_delta_cliff_minus_grind": 0.01,
        }
        self.assertEqual(_specialize(no_split), "NO_SPLIT")
        g, d = global_verdict([cliff_spec, no_split])
        self.assertIn(
            g,
            (
                "CLIFF_GRIND_SPLIT_HIT",
                "CLIFF_GRIND_SPLIT_WEAK",
            ),
        )
        self.assertEqual(d["champ_specialize"], "CLIFF_SPECIALIST")
        self.assertTrue(
            "cliff" in d["implication"].lower() or "grind" in d["implication"].lower()
        )


if __name__ == "__main__":
    unittest.main()
