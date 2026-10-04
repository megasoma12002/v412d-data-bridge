#!/usr/bin/env python3
"""Smoke tests for hist crisis signal OOS Stage A helpers (research-only)."""
from __future__ import annotations

import unittest
from datetime import date

import numpy as np
import pandas as pd

from tipsoft_ip3_crisis_signal_hist_oos_stagea import (
    CHAMP_ARM,
    EPISODES,
    MIN_EPISODE_BARS,
    OOS_FA_CEIL,
    OOS_HIT_FLOOR,
    OOS_IC_ABS_FLOOR,
    OOS_LEAD_DAYS_FLOOR,
    OOS_RECALL_FLOOR,
    TARGET_ARMS,
    _decade_noncrisis_mask,
    _episode_coverage,
    _global_verdict,
    _local_trough,
    _oos_verdict,
    _spearman_n,
)


class CrisisSignalHistOosHelpers(unittest.TestCase):
    def test_floors_and_targets(self) -> None:
        self.assertEqual(CHAMP_ARM, "and::rvol63_l4&fuse_prem_neg5")
        self.assertIn(CHAMP_ARM, TARGET_ARMS)
        self.assertIn("kconfirm2::fuse_prem_neg5", TARGET_ARMS)
        self.assertIn("base::rvol20_l4", TARGET_ARMS)
        self.assertGreaterEqual(OOS_IC_ABS_FLOOR, 0.05)
        self.assertGreaterEqual(OOS_HIT_FLOOR, 0.50)
        self.assertGreaterEqual(OOS_RECALL_FLOOR, 0.25)
        self.assertGreaterEqual(OOS_LEAD_DAYS_FLOOR, 3.0)
        self.assertLessEqual(OOS_FA_CEIL, 0.20)

    def test_episodes_include_required_cores(self) -> None:
        ids = {e.eid for e in EPISODES}
        self.assertIn("GFC_2008", ids)
        self.assertIn("TW_CN_2015", ids)
        self.assertIn("MAR2020", ids)
        required = [e for e in EPISODES if e.required_for_global]
        self.assertEqual({e.eid for e in required}, {"GFC_2008", "TW_CN_2015"})
        mar = next(e for e in EPISODES if e.eid == "MAR2020")
        self.assertTrue(mar.in_sample_ref)

    def test_episode_coverage_fail_loud_before_panel(self) -> None:
        idx = pd.date_range("2012-12-04", periods=500, freq="B")
        gfc = next(e for e in EPISODES if e.eid == "GFC_2008")
        cov = _episode_coverage(
            gfc,
            idx,
            coverage={"nav_start": "2012-12-04", "mkt_0050_start": "2010-01-04"},
        )
        self.assertFalse(cov["available"])
        self.assertTrue(cov["fail_loud"])
        self.assertIn("precedes panel_start", str(cov["reason"]))

    def test_episode_coverage_available_when_overlap(self) -> None:
        idx = pd.date_range("2012-12-04", periods=2000, freq="B")
        y2015 = next(e for e in EPISODES if e.eid == "TW_CN_2015")
        cov = _episode_coverage(
            y2015,
            idx,
            coverage={"nav_start": "2012-12-04", "mkt_0050_start": "2010-01-04"},
        )
        self.assertTrue(cov["available"])
        self.assertGreaterEqual(int(cov["n_bars_episode"]), MIN_EPISODE_BARS)

    def test_local_trough_is_argmin(self) -> None:
        idx = pd.date_range("2015-06-01", periods=40, freq="B")
        px = pd.Series(np.linspace(100, 80, len(idx)), index=idx)
        px.iloc[25] = 70.0
        trough = _local_trough(px, date(2015, 6, 1), date(2015, 9, 30))
        self.assertEqual(pd.Timestamp(trough).date(), idx[25].date())

    def test_decade_noncrisis_mask_excludes_crisis_years(self) -> None:
        idx = pd.date_range("2010-01-01", periods=2600, freq="B")
        mask = _decade_noncrisis_mask(idx, decade_start=2010, crisis_years={2015})
        years = idx.year
        self.assertFalse(bool(mask[years == 2015].any()))
        self.assertFalse(bool(mask[years == 2018].any()))  # known crisis in decade map
        self.assertTrue(bool(mask[years == 2014].any()))

    def test_oos_verdict_taxonomy(self) -> None:
        hit = {
            "coverage_available": True,
            "ic_spearman_fwd_mdd_10": 0.12,
            "hit_rate_episode": 0.60,
            "recall_episode": 0.40,
            "f1_episode": 0.35,
            "median_lead_days": 10.0,
            "fa_rate_decade_noncrisis": 0.08,
        }
        self.assertEqual(_oos_verdict(hit), "OOS_HIT")
        weak = {
            "coverage_available": True,
            "ic_spearman_fwd_mdd_10": 0.04,
            "hit_rate_episode": 0.52,
            "recall_episode": 0.22,
            "f1_episode": 0.10,
            "median_lead_days": 2.0,
            "fa_rate_decade_noncrisis": 0.10,
        }
        self.assertEqual(_oos_verdict(weak), "OOS_WEAK")
        miss = {
            "coverage_available": True,
            "ic_spearman_fwd_mdd_10": 0.01,
            "hit_rate_episode": 0.40,
            "recall_episode": 0.05,
            "f1_episode": 0.05,
            "median_lead_days": 0.0,
            "fa_rate_decade_noncrisis": 0.20,
        }
        self.assertEqual(_oos_verdict(miss), "OOS_MISS")
        # Negative IC = anti-predictive in episode — not WEAK credit
        anti = {
            "coverage_available": True,
            "ic_spearman_fwd_mdd_10": -0.29,
            "hit_rate_episode": 0.42,
            "recall_episode": 0.0,
            "f1_episode": 0.0,
            "median_lead_days": None,
            "fa_rate_decade_noncrisis": 0.02,
        }
        self.assertEqual(_oos_verdict(anti), "OOS_MISS")
        self.assertEqual(_oos_verdict({"coverage_available": False}), "NO_DATA")

    def test_global_verdict_partial_and_overfit(self) -> None:
        def _row(ep: str, v: str) -> dict:
            return {"arm": CHAMP_ARM, "episode": ep, "verdict": v}

        # 2015 HIT, 2008 NO_DATA → PARTIAL
        rows = [
            _row("GFC_2008", "NO_DATA"),
            _row("TW_CN_2015", "OOS_HIT"),
            _row("MAR2020", "OOS_HIT"),
        ]
        cov = {
            "GFC_2008": {"available": False},
            "TW_CN_2015": {"available": True},
        }
        g, d = _global_verdict(rows, episode_cov=cov)
        self.assertEqual(g, "IP3_CRISIS_SIGNAL_HIST_OOS_PARTIAL")
        self.assertEqual(d["hist_hits"], ["TW_CN_2015"])

        # 2015 MISS, Mar HIT → OVERFIT_2020
        rows2 = [
            _row("GFC_2008", "NO_DATA"),
            _row("TW_CN_2015", "OOS_MISS"),
            _row("MAR2020", "OOS_HIT"),
        ]
        g2, _ = _global_verdict(rows2, episode_cov=cov)
        self.assertEqual(g2, "IP3_CRISIS_SIGNAL_HIST_OOS_OVERFIT_2020")

        # both HIT → ROBUST
        rows3 = [
            _row("GFC_2008", "OOS_HIT"),
            _row("TW_CN_2015", "OOS_HIT"),
            _row("MAR2020", "OOS_HIT"),
        ]
        cov3 = {"GFC_2008": {"available": True}, "TW_CN_2015": {"available": True}}
        g3, _ = _global_verdict(rows3, episode_cov=cov3)
        self.assertEqual(g3, "IP3_CRISIS_SIGNAL_HIST_OOS_ROBUST")

    def test_spearman_n_min_bars(self) -> None:
        idx = pd.date_range("2015-01-01", periods=30, freq="B")
        x = pd.Series(np.arange(len(idx), dtype=float), index=idx)
        y = x + 1.0
        self.assertIsNone(_spearman_n(x, y, min_n=40))
        idx2 = pd.date_range("2015-01-01", periods=50, freq="B")
        x2 = pd.Series(np.arange(len(idx2), dtype=float), index=idx2)
        y2 = x2 * 2.0
        v = _spearman_n(x2, y2, min_n=40)
        self.assertIsNotNone(v)
        self.assertGreater(float(v), 0.9)


if __name__ == "__main__":
    unittest.main()
