#!/usr/bin/env python3
"""Smoke tests for Y2020 crisis sandbox Stage A helpers (research-only)."""
from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from tipsoft_ip3_y2020_crisis_sandbox_stagea import (
    _ann_vol,
    _apply_exposure,
    _arm_verdict,
    _ma200_exposure,
    _mdd_throttle_returns,
    _vol_target_exposure,
)


class CrisisSandboxHelpers(unittest.TestCase):
    def test_lag1_vol_and_ma_causal(self) -> None:
        idx = pd.date_range("2020-01-01", periods=250, freq="B")
        r = pd.Series(np.linspace(-0.02, 0.02, len(idx)), index=idx)
        vol = _ann_vol(r, 20)
        # First usable values must ignore same-day return (shift-1)
        self.assertTrue(np.isnan(vol.iloc[0]) or vol.iloc[0] != r.iloc[0])
        px = pd.Series(np.linspace(100, 80, len(idx)), index=idx)  # declining → below MA
        exp = _ma200_exposure(px, cash_level=0.0)
        self.assertEqual(exp.iloc[0], 1.0)  # insufficient MA → not below
        self.assertLessEqual(float(exp.iloc[-1]), 0.0 + 1e-12)

    def test_vol_target_floors(self) -> None:
        idx = pd.date_range("2019-01-01", periods=120, freq="B")
        rng = np.random.default_rng(0)
        r = pd.Series(rng.normal(0, 0.03, len(idx)), index=idx)
        exp = _vol_target_exposure(r, win=20, target=0.10, floor=0.30)
        self.assertGreaterEqual(float(exp.dropna().min()), 0.30 - 1e-9)
        self.assertLessEqual(float(exp.max()), 1.0 + 1e-9)
        out = _apply_exposure(r, exp)
        self.assertEqual(len(out), len(r))

    def test_mdd_throttle_halts(self) -> None:
        idx = pd.date_range("2020-02-01", periods=40, freq="B")
        # Sharp drawdown then flat
        r = pd.Series([-0.05] * 10 + [0.0] * 30, index=idx)
        out_r, out_e = _mdd_throttle_returns(r, None, dd10=-0.10, dd15=-0.15, scale10=0.5)
        self.assertTrue((out_e <= 1.0).all())
        # After deep DD, exposure should hit halt
        self.assertEqual(float(out_e.iloc[-1]), 0.0)
        self.assertAlmostEqual(float(out_r.iloc[-1]), 0.0)

    def test_verdict_hit_vs_mdd_only(self) -> None:
        self.assertEqual(
            _arm_verdict(
                held=0.15,
                sealed=0.0,
                tip_y=0.0,
                y20_mdd_imp=1.0,
                mar_mdd_imp=2.0,
            ),
            "HIT",
        )
        self.assertEqual(
            _arm_verdict(
                held=-0.5,
                sealed=0.0,
                tip_y=0.0,
                y20_mdd_imp=2.0,
                mar_mdd_imp=5.0,
            ),
            "MDD_ONLY",
        )
        self.assertEqual(
            _arm_verdict(
                held=0.20,
                sealed=-0.5,
                tip_y=0.0,
                y20_mdd_imp=2.0,
                mar_mdd_imp=5.0,
            ),
            "MDD_BLOCK",
        )


if __name__ == "__main__":
    unittest.main()
