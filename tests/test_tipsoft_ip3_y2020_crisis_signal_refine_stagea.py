#!/usr/bin/env python3
"""Smoke tests for Y2020 crisis signal refine Stage A helpers (research-only)."""
from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from tipsoft_ip3_y2020_crisis_signal_refine_stagea import (
    HIT_FLOOR,
    IC_ABS_FLOOR,
    OOS_IC_ABS_FLOOR,
    YEAR_DUMMY_IC_ABS_CEIL,
    _arm_verdict,
    _episode_hold,
    _global_verdict,
    _is_overfit,
    _k_confirm,
    _rolling_pct_flag,
)
from tipsoft_ip3_y2020_crisis_signal_stagea import (
    HIT_FLOOR as P_HIT,
    IC_ABS_FLOOR as P_IC,
    LEAD_DAYS_FLOOR as P_LEAD,
    OOS_IC_ABS_FLOOR as P_OOS,
    RECALL_MAR_FLOOR as P_RECALL,
    YEAR_DUMMY_IC_ABS_CEIL as P_YD,
)


class CrisisSignalRefineHelpers(unittest.TestCase):
    def test_floors_match_0kbh(self) -> None:
        self.assertEqual(IC_ABS_FLOOR, P_IC)
        self.assertEqual(HIT_FLOOR, P_HIT)
        self.assertEqual(OOS_IC_ABS_FLOOR, P_OOS)
        self.assertEqual(YEAR_DUMMY_IC_ABS_CEIL, P_YD)
        self.assertEqual(P_RECALL, 0.35)
        self.assertEqual(P_LEAD, 3.0)

    def test_k_confirm_requires_streak(self) -> None:
        idx = pd.date_range("2020-01-01", periods=10, freq="B")
        flag = pd.Series([0, 1, 1, 1, 0, 1, 0, 0, 0, 0], index=idx, dtype=float)
        k2 = _k_confirm(flag, 2)
        k3 = _k_confirm(flag, 3)
        self.assertEqual(float(k2.iloc[1]), 0.0)  # only 1 day
        self.assertEqual(float(k2.iloc[2]), 1.0)
        self.assertEqual(float(k3.iloc[2]), 0.0)
        self.assertEqual(float(k3.iloc[3]), 1.0)
        self.assertEqual(float(k2.iloc[4]), 0.0)

    def test_episode_hold_min_days(self) -> None:
        idx = pd.date_range("2020-01-01", periods=12, freq="B")
        enter = pd.Series(False, index=idx)
        enter.iloc[2] = True
        ep = _episode_hold(enter, hold=3)
        self.assertEqual(float(ep.iloc[1]), 0.0)
        self.assertEqual(float(ep.iloc[2]), 1.0)
        self.assertEqual(float(ep.iloc[3]), 1.0)
        self.assertEqual(float(ep.iloc[4]), 1.0)
        self.assertEqual(float(ep.iloc[5]), 0.0)

    def test_rolling_pct_no_double_lag(self) -> None:
        idx = pd.date_range("2019-01-01", periods=300, freq="B")
        rng = np.random.default_rng(0)
        x = pd.Series(rng.normal(size=len(idx)), index=idx)
        # Spike at t=200 must be able to fire at t=200 (feature already lag-1)
        x.iloc[200] = 10.0
        flag = _rolling_pct_flag(x, q=0.95, win=60)
        self.assertTrue(bool(flag.iloc[200]))
        # Future spike must not change past flags
        x2 = x.copy()
        x2.iloc[250] = 20.0
        flag2 = _rolling_pct_flag(x2, q=0.95, win=60)
        self.assertEqual(bool(flag.iloc[200]), bool(flag2.iloc[200]))

    def test_overfit_and_verdicts(self) -> None:
        over = {
            "ic_spearman_primary": 0.20,
            "hit_rate_mar": 0.70,
            "recall_mar": 0.50,
            "median_lead_days": 8.0,
            "fa_rate_outside_2020": 0.08,
            "year2020_dummy_abs_ic": 0.80,
            "ic_spearman_oos_ex2020": 0.10,
        }
        self.assertTrue(_is_overfit(over))
        self.assertEqual(_arm_verdict(over), "SIGNAL_OVERFIT")

        mar_only = {
            "ic_spearman_primary": 0.10,
            "hit_rate_mar": 0.70,
            "recall_mar": 0.50,
            "median_lead_days": 8.0,
            "fa_rate_outside_2020": 0.08,
            "year2020_dummy_abs_ic": 0.10,
            "ic_spearman_oos_ex2020": 0.01,  # below OOS floor
        }
        self.assertTrue(_is_overfit(mar_only))
        self.assertEqual(_arm_verdict(mar_only), "SIGNAL_OVERFIT")

        hit = {
            "ic_spearman_primary": 0.20,
            "hit_rate_mar": 0.70,
            "recall_mar": 0.50,
            "median_lead_days": 8.0,
            "fa_rate_outside_2020": 0.08,
            "year2020_dummy_abs_ic": 0.20,
            "ic_spearman_oos_ex2020": 0.10,
        }
        self.assertEqual(_arm_verdict(hit), "SIGNAL_HIT")

        weak_rows = [
            {
                **hit,
                "verdict": "SIGNAL_WEAK",
                "ic_spearman_primary": 0.12,
                "hit_rate_mar": 0.52,
                "recall_mar": 0.30,
                "f1_mar": 0.2,
                "fa_rate_outside_2020": 0.09,
            }
        ]
        g, champ = _global_verdict(weak_rows)
        self.assertEqual(g, "IP3_Y2020_CRISIS_SIGNAL_REFINE_WEAK")
        self.assertIsNotNone(champ)

        over_rows = [{**over, "verdict": "SIGNAL_OVERFIT", "f1_mar": 0.3}]
        g2, _ = _global_verdict(over_rows)
        self.assertEqual(g2, "IP3_Y2020_CRISIS_SIGNAL_REFINE_OVERFIT")


if __name__ == "__main__":
    unittest.main()
