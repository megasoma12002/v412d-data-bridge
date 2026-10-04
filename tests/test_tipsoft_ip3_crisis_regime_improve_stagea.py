#!/usr/bin/env python3
"""Smoke tests for crisis regime-improve Stage A helpers (research-only)."""
from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from tipsoft_ip3_crisis_regime_improve_stagea import (
    CHAMP_0KBI,
    CLIFF_SCALES,
    GRIND_SCALES,
    HELD_CAGR_FLOOR_PP,
    MAJOR_DD_WINDOWS,
    PARENTS,
    REGISTER,
    ROUTER_SPECS,
    _arm_verdict,
    _cross_era_flags,
    _duration_in_dd,
    build_router_features,
    classify_regime,
    cliff_sleeve_alert,
    global_verdict_from_counts,
    grind_sleeve_alert,
    regime_exposure,
)


class CrisisRegimeImproveHelpers(unittest.TestCase):
    def test_constants(self) -> None:
        self.assertEqual(REGISTER, "0kbm")
        self.assertEqual(PARENTS, ("0kbl", "0kbk", "0kbj", "0kbf"))
        self.assertEqual(CHAMP_0KBI, "and::rvol63_l4&fuse_prem_neg5")
        self.assertEqual(HELD_CAGR_FLOOR_PP, 0.10)
        self.assertEqual(len(ROUTER_SPECS), 3)
        self.assertLessEqual(len(CLIFF_SCALES) * len(GRIND_SCALES) * len(ROUTER_SPECS) + 9, 40)
        eras = {w["era"] for w in MAJOR_DD_WINDOWS}
        self.assertEqual(eras, {"2015", "2018", "2022"})

    def test_duration_and_classify_causal(self) -> None:
        idx = pd.date_range("2020-02-01", periods=30, freq="B")
        dd = pd.Series(0.0, index=idx)
        dd.iloc[5:20] = np.linspace(0.02, 0.12, 15)
        dur = _duration_in_dd(dd, enter=0.05)
        # lag-1: first day of enter should not yet count as duration on same bar
        self.assertTrue(np.isnan(dur.iloc[0]) or dur.iloc[0] == 0.0)

        feats = pd.DataFrame(index=idx)
        feats["dd_mag"] = dd
        feats["dd_vel"] = dd.diff(5).fillna(0.0) / 5.0
        feats["rvol_spike"] = 1.5
        feats["dur_dd_05"] = _duration_in_dd(dd, enter=0.05)
        feats["dur_dd_08"] = _duration_in_dd(dd, enter=0.08)
        reg = classify_regime(
            feats,
            vel_floor=0.004,
            cliff_max_days=20,
            grind_min_days=40,
            dd_enter=0.05,
            rvol_spike_mult=1.25,
        )
        self.assertIn("CLIFF_RISK", set(reg.unique()) | {"NORMAL"})
        # Long slow grind
        idx2 = pd.date_range("2018-09-01", periods=80, freq="B")
        dd2 = pd.Series(0.0, index=idx2)
        dd2.iloc[5:65] = np.linspace(0.01, 0.10, 60)
        feats2 = pd.DataFrame(index=idx2)
        feats2["dd_mag"] = dd2
        feats2["dd_vel"] = 0.001  # below cliff vel
        feats2["rvol_spike"] = 1.0
        feats2["dur_dd_05"] = _duration_in_dd(dd2, enter=0.05)
        feats2["dur_dd_08"] = _duration_in_dd(dd2, enter=0.08)
        reg2 = classify_regime(
            feats2,
            vel_floor=0.004,
            cliff_max_days=20,
            grind_min_days=40,
            dd_enter=0.05,
            rvol_spike_mult=1.25,
        )
        self.assertTrue((reg2 == "GRIND_RISK").any())

    def test_sleeves_and_exposure(self) -> None:
        idx = pd.date_range("2020-01-01", periods=10, freq="B")
        feats = pd.DataFrame(index=idx)
        feats["rvol20"] = [0.1] * 9 + [0.9]
        feats["atr"] = 0.01
        feats["consec_down"] = 0.0
        feats["below_ma200"] = 0.0
        feats["cool_defend"] = [0.0] * 5 + [1.0] * 5
        feats["fuse_prem_neg5"] = 0.0
        feats["rvol63"] = 0.1
        # force rvol alert via high last values relative to quantile
        feats.loc[feats.index[-1], "rvol20"] = 10.0
        g = grind_sleeve_alert(feats)
        self.assertTrue(bool(g.any()))

        regime = pd.Series(["NORMAL"] * 10, index=idx, dtype=object)
        regime.iloc[2] = "CLIFF_RISK"
        regime.iloc[6] = "GRIND_RISK"
        c_alert = pd.Series([False] * 10, index=idx)
        c_alert.iloc[2] = True
        g_alert = pd.Series([False] * 10, index=idx)
        g_alert.iloc[6] = True
        exp = regime_exposure(
            regime,
            cliff_alert=c_alert,
            grind_alert=g_alert,
            cliff_scale=0.0,
            grind_scale=0.7,
        )
        self.assertEqual(float(exp.iloc[2]), 0.0)
        self.assertEqual(float(exp.iloc[6]), 0.7)
        self.assertEqual(float(exp.iloc[0]), 1.0)

    def test_verdict_taxonomy(self) -> None:
        self.assertEqual(
            _arm_verdict(
                held=0.20,
                sealed=0.0,
                tip_y=0.0,
                y20_mdd_imp=1.0,
                mar_mdd_imp=0.0,
                cross_era_ok=True,
                cross_era_any_improve=True,
                cross_era_all_worse=False,
            ),
            "HIT",
        )
        self.assertEqual(
            _arm_verdict(
                held=-0.20,
                sealed=0.0,
                tip_y=0.0,
                y20_mdd_imp=1.0,
                mar_mdd_imp=1.0,
                cross_era_ok=True,
                cross_era_any_improve=True,
                cross_era_all_worse=False,
            ),
            "MDD_ONLY",
        )
        self.assertEqual(
            _arm_verdict(
                held=0.20,
                sealed=0.0,
                tip_y=0.0,
                y20_mdd_imp=1.0,
                mar_mdd_imp=1.0,
                cross_era_ok=True,
                cross_era_any_improve=False,
                cross_era_all_worse=True,
            ),
            "OVERFIT",
        )
        self.assertEqual(
            _arm_verdict(
                held=0.20,
                sealed=0.0,
                tip_y=0.0,
                y20_mdd_imp=0.0,
                mar_mdd_imp=0.0,
                cross_era_ok=True,
                cross_era_any_improve=False,
                cross_era_all_worse=False,
            ),
            "HELD_BLOCK",
        )
        self.assertEqual(
            global_verdict_from_counts(
                n_hit=1, n_mdd_only=0, n_held_block=0, n_overfit=0, champ_verdict="HIT"
            ),
            "CRISIS_REGIME_IMPROVE_HIT",
        )
        self.assertEqual(
            global_verdict_from_counts(
                n_hit=0, n_mdd_only=2, n_held_block=0, n_overfit=1, champ_verdict="MDD_ONLY"
            ),
            "CRISIS_REGIME_IMPROVE_MDD_ONLY",
        )
        any_imp, all_worse, ok, n_imp, n_worse = _cross_era_flags(
            {"2015": 0.1, "2018": -0.2, "2022": None}
        )
        self.assertTrue(any_imp)
        self.assertFalse(all_worse)
        self.assertEqual(n_imp, 1)
        self.assertEqual(n_worse, 1)

    def test_build_router_features_columns(self) -> None:
        idx = pd.date_range("2019-01-01", periods=120, freq="B")
        panel = pd.DataFrame(
            {
                "date": idx,
                "dd63_l4": np.linspace(0, 0.1, len(idx)),
                "rvol20_l4": np.linspace(0.1, 0.3, len(idx)),
                "rvol63_l4": np.linspace(0.1, 0.25, len(idx)),
                "atr_like_20": 0.01,
                "consec_down_mkt": 0.0,
                "below_ma200": 0.0,
                "cool_defend_l1": 0.0,
                "fuse_prem_neg5": 0.0,
                "neg_gap_ma200": 0.0,
            }
        )
        feats = build_router_features(panel)
        for col in ("dd_mag", "dd_vel", "rvol_spike", "dur_dd_05", "dur_dd_08"):
            self.assertIn(col, feats.columns)


if __name__ == "__main__":
    unittest.main()
