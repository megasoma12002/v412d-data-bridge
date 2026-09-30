#!/usr/bin/env python3
"""Guards for tip Soft Exact T+1 LIVE_OVERRIDE live wire (0kb2 ACCEPT)."""
from __future__ import annotations

import unittest

import pandas as pd

from live_config import (
    LIVE,
    LIVE_PATH3_STRATEGY_CUTOVER,
    LIVE_TIPSOFT_LIVE_OVERRIDE,
    LIVE_TIPSOFT_LIVE_OVERRIDE_POLICY,
)
from live_tip_meta import build_cutover_stamps
from live_tipsoft_live_override import (
    ACCEPT_BALLOT,
    CONFIRM_K,
    MARGIN,
    MECHANISM_ID,
    WINDOW,
    compute_gate_state,
    is_on,
    override_mask,
    session_meta,
)


class TipsoftOverrideFlagDefaults(unittest.TestCase):
    def test_flag_on_after_accept(self) -> None:
        self.assertTrue(LIVE.live_tipsoft_live_override)
        self.assertTrue(LIVE_TIPSOFT_LIVE_OVERRIDE)
        self.assertTrue(is_on())
        self.assertEqual(
            LIVE_TIPSOFT_LIVE_OVERRIDE_POLICY, "TIPSOFT_P3_LIVE_OVERRIDE_W42_M05_K3"
        )
        self.assertEqual(MECHANISM_ID, "TIPSOFT_P3_LIVE_OVERRIDE_W42_M05_K3")
        self.assertEqual(WINDOW, 42)
        self.assertEqual(MARGIN, 0.005)
        self.assertEqual(CONFIRM_K, 3)
        self.assertIn("TIPSOFT_P3_LIVE_OVERRIDE_W42_M05_K3", ACCEPT_BALLOT)
        self.assertIn("Path3 WITHIN_SLEEVE KEEP", ACCEPT_BALLOT)
        self.assertIn("broker false", ACCEPT_BALLOT)

    def test_path3_within_still_on(self) -> None:
        self.assertTrue(LIVE_PATH3_STRATEGY_CUTOVER)
        self.assertTrue(LIVE.live_path3_strategy_cutover)


class OverrideMaskCausal(unittest.TestCase):
    def test_requires_k_confirm_days(self) -> None:
        idx = pd.date_range("2020-01-01", periods=80, freq="B")
        live = pd.Series(0.0, index=idx)
        champ = pd.Series(0.0, index=idx)
        # last 50 days: live beats champ by ~0.02/day → trail lead >> 0.005
        live.iloc[-50:] = 0.02
        mask = override_mask(live, champ, window=42, margin=0.005, k=3)
        self.assertFalse(bool(mask.iloc[10]))
        self.assertTrue(bool(mask.iloc[-1]))


class GateAndSessionMeta(unittest.TestCase):
    def test_compute_gate_ok(self) -> None:
        gate = compute_gate_state()
        self.assertTrue(gate["ok"])
        self.assertTrue(gate["enabled"])
        self.assertIn(gate["override_on"], (True, False))
        self.assertTrue(gate["path3_within_sleeve_keep"])
        self.assertTrue(gate["soft_fin_tel_stay_off"])
        self.assertFalse(gate["path4_live"])

    def test_session_meta_and_tip_stamps(self) -> None:
        meta = session_meta()
        self.assertTrue(meta["tipsoft_live_override_live"])
        self.assertEqual(
            meta["tipsoft_live_override_policy"], "TIPSOFT_P3_LIVE_OVERRIDE_W42_M05_K3"
        )
        self.assertTrue(meta["tipsoft_live_override_path3_within_keep"])
        self.assertTrue(meta["tipsoft_live_override_soft_fin_tel_stay_off"])
        stamps = build_cutover_stamps()
        self.assertTrue(stamps["tipsoft_live_override_live"])
        self.assertIn("ACCEPT_2026-09-30", stamps["tipsoft_live_override_cutover"])


if __name__ == "__main__":
    unittest.main()
