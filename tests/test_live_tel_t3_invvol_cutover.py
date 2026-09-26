#!/usr/bin/env python3
"""Unit tests for live T3_COOL_INV_VOL20 cutover helpers."""
from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

import live_tel_t3_invvol_cutover as tel_t3
from within_sleeve_alloc import TEL_EQUAL, TEL_RS_SOFT_TILT


def _toy_market(n: int = 80) -> pd.DataFrame:
    dates = pd.bdate_range("2024-01-02", periods=n)
    rows = []
    rng = np.random.default_rng(0)
    for code, vol in (("2412", 0.01), ("3045", 0.02), ("4904", 0.015)):
        px = 100.0 * np.cumprod(1.0 + rng.normal(0.0, vol, size=n))
        for d, p in zip(dates, px):
            rows.append(
                {
                    "date": d,
                    "code": code,
                    "adj_close": float(p),
                    "close": float(p),
                    "open": float(p),
                    "high": float(p),
                    "low": float(p),
                    "volume": 1_000_000.0,
                }
            )
    return pd.DataFrame(rows)


class TestTelT3Cutover(unittest.TestCase):
    def test_scores_build(self):
        m = _toy_market()
        panel = tel_t3.build_inv_vol20_scores(m)
        self.assertEqual(list(panel.columns), ["2412", "3045", "4904"])
        self.assertGreater(len(panel.dropna(how="all")), 20)

    def test_policy_off_defense_equal(self):
        policy, active, meta = tel_t3.resolve_tel_policy(
            cool_exposure=1.0, scores_ok=True
        )
        self.assertEqual(policy, TEL_EQUAL)
        self.assertFalse(active)
        self.assertFalse(meta["defending"])

    def test_policy_defend_tilt(self):
        policy, active, meta = tel_t3.resolve_tel_policy(
            cool_exposure=0.5, scores_ok=True
        )
        self.assertEqual(policy, TEL_RS_SOFT_TILT)
        self.assertTrue(active)
        self.assertTrue(meta["defending"])

    def test_policy_fail_closed(self):
        policy, active, _meta = tel_t3.resolve_tel_policy(
            cool_exposure=0.5, scores_ok=False
        )
        self.assertEqual(policy, TEL_EQUAL)
        self.assertFalse(active)

    def test_scores_for_asof(self):
        m = _toy_market()
        asof = pd.Timestamp(m["date"].max())
        scores, meta = tel_t3.scores_for_asof(m, asof)
        self.assertTrue(meta["ok"])
        self.assertIsNotNone(scores)
        assert scores is not None
        self.assertEqual(set(scores.keys()), {"2412", "3045", "4904"})


if __name__ == "__main__":
    unittest.main()
