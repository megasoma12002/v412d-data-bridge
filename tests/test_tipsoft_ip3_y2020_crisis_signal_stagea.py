#!/usr/bin/env python3
"""Smoke tests for Y2020 crisis signal Stage A helpers (research-only)."""
from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from tipsoft_ip3_y2020_crisis_signal_stagea import (
    _alert_mask,
    _ann_vol,
    _binary_prf,
    _consec_down,
    _detector_verdict,
    _fwd_mdd,
    _median_lead_days,
)


class CrisisSignalHelpers(unittest.TestCase):
    def test_lag1_vol_causal(self) -> None:
        idx = pd.date_range("2020-01-01", periods=80, freq="B")
        r = pd.Series(np.linspace(-0.02, 0.02, len(idx)), index=idx)
        vol = _ann_vol(r, 20)
        self.assertTrue(np.isnan(vol.iloc[0]) or abs(float(vol.iloc[0])) > 0)
        # Same-day spike must not enter lag-1 vol immediately
        r2 = r.copy()
        r2.iloc[40] = -0.50
        vol2 = _ann_vol(r2, 20)
        # Lag-1: same-day spike appears in vol on the *next* bar
        self.assertAlmostEqual(float(vol.iloc[40]), float(vol2.iloc[40]), places=6)
        self.assertNotAlmostEqual(float(vol.iloc[41]), float(vol2.iloc[41]), places=6)

    def test_fwd_mdd_positive_stress(self) -> None:
        idx = pd.date_range("2020-01-01", periods=40, freq="B")
        r = pd.Series([0.0] * 10 + [-0.05] * 10 + [0.0] * 20, index=idx)
        mdd = _fwd_mdd(r, 10)
        # Just before the crash block, forward MDD should be large
        self.assertGreater(float(mdd.iloc[9]), 0.2)

    def test_consec_down_lag1(self) -> None:
        idx = pd.date_range("2020-01-01", periods=10, freq="B")
        r = pd.Series([-0.01, -0.01, -0.01, 0.01, -0.01, 0.0, 0.0, 0.0, 0.0, 0.0], index=idx)
        c = _consec_down(r)
        self.assertTrue(np.isnan(c.iloc[0]) or c.iloc[0] == 0)
        self.assertEqual(float(c.iloc[3]), 3.0)  # three downs ending yesterday

    def test_alert_and_lead(self) -> None:
        idx = pd.date_range("2020-01-02", periods=80, freq="B")
        feat = pd.Series(0.0, index=idx)
        # Spike into Mar window so top-quantile alerts lead the trough
        feat.loc["2020-03-02":"2020-03-20"] = 1.0
        alert = _alert_mask(feat, stress_high=True, q=0.80)
        self.assertTrue(bool(alert.loc["2020-03-10"]))
        lead = _median_lead_days(
            alert,
            window_start=__import__("datetime").date(2020, 2, 20),
            trough=pd.Timestamp("2020-03-23"),
        )
        self.assertIsNotNone(lead)
        self.assertGreaterEqual(float(lead), 0.0)

    def test_binary_prf_and_verdict(self) -> None:
        y = pd.Series([1, 1, 0, 0, 1, 0, 0, 0, 1, 0] * 10)
        p = pd.Series([1, 0, 0, 0, 1, 0, 1, 0, 1, 0] * 10)
        prf = _binary_prf(y, p)
        self.assertIsNotNone(prf["f1"])
        self.assertEqual(
            _detector_verdict(
                {
                    "ic_spearman_primary": 0.20,
                    "hit_rate_mar": 0.70,
                    "recall_mar": 0.50,
                    "median_lead_days": 8.0,
                    "fa_rate_outside_2020": 0.08,
                    "year2020_dummy_abs_ic": 0.20,
                    "ic_spearman_oos_ex2020": 0.10,
                }
            ),
            "SIGNAL_HIT",
        )
        self.assertEqual(
            _detector_verdict(
                {
                    "ic_spearman_primary": 0.20,
                    "hit_rate_mar": 0.70,
                    "recall_mar": 0.50,
                    "median_lead_days": 8.0,
                    "fa_rate_outside_2020": 0.08,
                    "year2020_dummy_abs_ic": 0.80,  # year dummy
                    "ic_spearman_oos_ex2020": 0.10,
                }
            ),
            "SIGNAL_WEAK",
        )
        self.assertEqual(
            _detector_verdict(
                {
                    "ic_spearman_primary": 0.01,
                    "hit_rate_mar": 0.50,
                    "recall_mar": 0.05,
                    "median_lead_days": 0.0,
                    "fa_rate_outside_2020": 0.20,
                    "year2020_dummy_abs_ic": 0.10,
                    "ic_spearman_oos_ex2020": 0.01,
                }
            ),
            "SIGNAL_NO_EDGE",
        )


if __name__ == "__main__":
    unittest.main()
