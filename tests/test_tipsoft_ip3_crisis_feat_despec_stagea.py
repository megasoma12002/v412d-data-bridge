#!/usr/bin/env python3
"""Smoke tests for crisis feature despec Stage A helpers (research-only)."""
from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from tipsoft_ip3_crisis_feat_despec_stagea import (
    BASE_FEATURES,
    CHAMP_0KBI,
    ERA_KEYS,
    ERAS,
    HIT_NON2020_MIN,
    NON2020_ERAS,
    PARENTS,
    REGISTER,
    RVOL_FEATURES,
    _arm_despec_verdict,
    _k_confirm,
    _rolling_z,
    _vs_long_median,
    cross_era_aggregate,
    global_verdict,
    leave_one_era_out,
)


class CrisisFeatDespecHelpers(unittest.TestCase):
    def test_constants(self) -> None:
        self.assertEqual(REGISTER, "0kbn")
        self.assertEqual(PARENTS, ("0kbm", "0kbl", "0kbk", "0kbj", "0kbf"))
        self.assertEqual(CHAMP_0KBI, "and::rvol63_l4&fuse_prem_neg5")
        self.assertEqual(HIT_NON2020_MIN, 2)
        self.assertEqual(set(ERA_KEYS), {"2015", "2018", "2022", "2020"})
        self.assertEqual(set(NON2020_ERAS), {"2015", "2018", "2022"})
        for feat in (
            "rvol20_l4",
            "rvol63_l4",
            "atr_like_20",
            "neg_gap_ma200",
            "dd63_l4",
            "fuse_prem_neg5",
            "fuse_neg_flag",
            "cool_defend_l1",
            "consec_down_mkt",
        ):
            self.assertIn(feat, BASE_FEATURES)
        self.assertTrue(set(RVOL_FEATURES).issubset(set(BASE_FEATURES)))
        self.assertEqual(len(ERAS), 4)

    def test_transforms_causal_shape(self) -> None:
        idx = pd.date_range("2015-01-01", periods=600, freq="B")
        x = pd.Series(np.linspace(0.1, 0.5, len(idx)) + np.sin(np.arange(len(idx)) / 20) * 0.05, index=idx)
        z = _rolling_z(x, 252)
        self.assertEqual(len(z), len(x))
        # early window mostly NaN
        self.assertTrue(z.iloc[:50].isna().mean() > 0.5)
        vm = _vs_long_median(x, 252)
        self.assertEqual(len(vm), len(x))
        flag = (x > x.median()).astype(float)
        k2 = _k_confirm(flag, 2)
        self.assertTrue(((k2 == 0) | (k2 == 1)).all())
        # k-confirm should be stricter (fewer ones) than raw flag
        self.assertLessEqual(float(k2.sum()), float(flag.sum()))

    def test_cross_era_and_verdicts(self) -> None:
        per = []
        for era, ic, v in (
            ("2015", 0.12, "ERA_HIT"),
            ("2018", 0.10, "ERA_HIT"),
            ("2022", 0.09, "ERA_WEAK"),
            ("2020", 0.15, "ERA_HIT"),
        ):
            per.append(
                {
                    "arm": "z252::rvol63_l4",
                    "family": "zscore",
                    "era": era,
                    "ic_spearman": ic,
                    "verdict": v,
                }
            )
        # 2020-only arm
        for era, ic, v in (
            ("2015", 0.01, "MISS"),
            ("2018", 0.00, "MISS"),
            ("2022", -0.02, "MISS"),
            ("2020", 0.20, "ERA_HIT"),
        ):
            per.append(
                {
                    "arm": "raw::fuse_prem_neg5",
                    "family": "raw",
                    "era": era,
                    "ic_spearman": ic,
                    "verdict": v,
                }
            )
        cross = cross_era_aggregate(per)
        self.assertEqual(cross[0]["arm"], "z252::rvol63_l4")
        self.assertGreaterEqual(cross[0]["n_non2020_hit"], 2)

        hit_glob = {
            "ic_spearman_primary": 0.12,
            "ic_spearman_oos_ex2020": 0.10,
            "year2020_dummy_abs_ic": 0.20,
            "fa_rate_outside_2020": 0.05,
        }
        self.assertEqual(_arm_despec_verdict(cross[0], hit_glob), "HIT")

        still = next(r for r in cross if r["arm"] == "raw::fuse_prem_neg5")
        self.assertEqual(_arm_despec_verdict(still, hit_glob), "STILL_SPEC")

        arm_rows = [
            {
                **cross[0],
                **hit_glob,
                "despec_verdict": "HIT",
            },
            {
                **still,
                **hit_glob,
                "despec_verdict": "STILL_SPEC",
            },
        ]
        v, champ = global_verdict(arm_rows)
        self.assertEqual(v, "CRISIS_FEAT_DESPEC_HIT")
        self.assertEqual(champ["arm"], "z252::rvol63_l4")

    def test_loo_selects_on_train_eras(self) -> None:
        per = []
        # Arm A strong on 2015/2018/2022, weak on 2020
        for era, ic, v in (
            ("2015", 0.15, "ERA_HIT"),
            ("2018", 0.14, "ERA_HIT"),
            ("2022", 0.13, "ERA_HIT"),
            ("2020", 0.02, "MISS"),
        ):
            per.append(
                {
                    "arm": "A",
                    "family": "zscore",
                    "era": era,
                    "ic_spearman": ic,
                    "verdict": v,
                    "hit_rate": 0.6,
                    "recall": 0.4,
                }
            )
        # Arm B strong only on 2020
        for era, ic, v in (
            ("2015", 0.01, "MISS"),
            ("2018", 0.01, "MISS"),
            ("2022", 0.01, "MISS"),
            ("2020", 0.25, "ERA_HIT"),
        ):
            per.append(
                {
                    "arm": "B",
                    "family": "raw",
                    "era": era,
                    "ic_spearman": ic,
                    "verdict": v,
                    "hit_rate": 0.6,
                    "recall": 0.4,
                }
            )
        loo = leave_one_era_out(per, candidate_arms=["A", "B"])
        by_held = {r["held_out_era"]: r for r in loo}
        # When holding out 2020, train on non-2020 → should pick A
        self.assertEqual(by_held["2020"]["selected_arm"], "A")
        # When holding out 2015, A still dominates train (2018/2022/2020 mean)
        self.assertEqual(by_held["2015"]["selected_arm"], "A")

    def test_no_forbidden_feature_names(self) -> None:
        forbidden_tokens = ("year_dummy", "month_", "calendar_", "episode_label", "mar2020_flag")
        for feat in BASE_FEATURES:
            low = feat.lower()
            for tok in forbidden_tokens:
                self.assertNotIn(tok, low)


if __name__ == "__main__":
    unittest.main()
