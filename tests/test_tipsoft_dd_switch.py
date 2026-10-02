#!/usr/bin/env python3
"""Guards for tip Soft Exact T+1 DD_SWITCH tip apply (0kbd ACCEPT)."""
from __future__ import annotations

import unittest
from unittest import mock

import pandas as pd

from live_config import (
    LIVE,
    LIVE_PATH3_STRATEGY_CUTOVER,
    LIVE_TIPSOFT_DD_SWITCH,
    LIVE_TIPSOFT_DD_SWITCH_POLICY,
)
from live_tip_meta import build_cutover_stamps
from live_tipsoft_dd_switch import (
    ACCEPT_BALLOT,
    MECHANISM_ID,
    STAGE_A_ARM_ID,
    TRAIL_THR,
    TRAIL_WINDOW,
    WIRE_MODE,
    apply_to_path3_deltas,
    compute_gate_state,
    flatten_fin_tel_deltas,
    is_on,
    path3_active_series,
    session_meta,
    want_trail_series,
)


class DdSwitchFlagDefaults(unittest.TestCase):
    def test_flag_on_after_accept(self) -> None:
        self.assertTrue(LIVE.live_tipsoft_dd_switch)
        self.assertTrue(LIVE_TIPSOFT_DD_SWITCH)
        self.assertTrue(is_on())
        self.assertEqual(
            LIVE_TIPSOFT_DD_SWITCH_POLICY, "TIPSOFT_P3_TRAIL42_L4_DD_SWITCH"
        )
        self.assertEqual(MECHANISM_ID, "TIPSOFT_P3_TRAIL42_L4_DD_SWITCH")
        self.assertEqual(WIRE_MODE, "path3_gate_ft_cash_apply")
        self.assertEqual(STAGE_A_ARM_ID, "SW_TRAIL_WHEN_TR_DD_GTE_L4")
        self.assertEqual(TRAIL_WINDOW, 42)
        self.assertEqual(TRAIL_THR, -0.01)
        self.assertIn("TIPSOFT_P3_TRAIL42_L4_DD_SWITCH", ACCEPT_BALLOT)
        self.assertIn("NOT stamps-only", ACCEPT_BALLOT)
        self.assertIn("broker false", ACCEPT_BALLOT)

    def test_path3_within_still_on(self) -> None:
        self.assertTrue(LIVE_PATH3_STRATEGY_CUTOVER)
        self.assertTrue(LIVE.live_path3_strategy_cutover)

    def test_broker_stays_false(self) -> None:
        self.assertFalse(LIVE.broker_live_write_accepted)
        gate = compute_gate_state()
        self.assertFalse(gate["broker"])
        meta = session_meta()
        self.assertFalse(meta["tipsoft_dd_switch_broker"])


class Path3ActiveLogic(unittest.TestCase):
    def test_l4_days_always_active(self) -> None:
        idx = pd.date_range("2020-01-01", periods=5, freq="B")
        want = pd.Series([False, False, True, True, True], index=idx)
        t42 = pd.Series([False, True, False, True, False], index=idx)
        active = path3_active_series(want, t42)
        self.assertTrue(bool(active.iloc[0]))  # L4
        self.assertTrue(bool(active.iloc[1]))  # L4
        self.assertFalse(bool(active.iloc[2]))  # TRAIL + TRAIL42 OFF → cash
        self.assertTrue(bool(active.iloc[3]))  # TRAIL + TRAIL42 ON
        self.assertFalse(bool(active.iloc[4]))  # TRAIL + OFF

    def test_flatten_fin_tel_only(self) -> None:
        pos = {"2880": 1000.0, "2412": 500.0, "0050": 2000.0, "2330": 100.0}
        flat = flatten_fin_tel_deltas(pos)
        self.assertEqual(flat["2880"], -1000.0)
        self.assertEqual(flat["2412"], -500.0)
        self.assertNotIn("0050", flat)
        self.assertNotIn("2330", flat)


class GateAndApply(unittest.TestCase):
    def test_compute_gate_ok(self) -> None:
        gate = compute_gate_state()
        self.assertTrue(gate["ok"], gate)
        self.assertFalse(gate["stale"])
        self.assertIn(gate["fill"], ("WITHIN", "FT_TO_CASH"))
        self.assertIsInstance(gate["want_trail"], bool)
        self.assertIsInstance(gate["path3_active"], bool)
        self.assertFalse(gate["return_blend_applied"])
        self.assertTrue(gate["tip_apply"])

    def test_stale_fail_loud(self) -> None:
        tip = pd.Timestamp("2099-01-01")
        gate = compute_gate_state(tip, market_tip=tip)
        self.assertFalse(gate["ok"])
        self.assertTrue(gate["stale"])
        self.assertEqual(gate["reason"], "nav_stale")
        self.assertIsNone(gate["path3_active"])

    def test_apply_within_keeps_deltas(self) -> None:
        deltas = {"2880": 10.0, "2412": -5.0}
        with mock.patch(
            "live_tipsoft_dd_switch.compute_gate_state",
            return_value={
                "ok": True,
                "path3_active": True,
                "fill": "WITHIN",
                "want_trail": False,
                "trail42_on": True,
                "reason": "ok",
                "asof": "2026-09-29",
                "stale": False,
            },
        ):
            out, meta = apply_to_path3_deltas(deltas, {"2880": 100.0}, "2026-09-29")
        self.assertEqual(out, deltas)
        self.assertEqual(meta["fill"], "WITHIN")
        self.assertTrue(meta["applied"])

    def test_apply_off_flattens(self) -> None:
        deltas = {"2880": 10.0}
        pos = {"2880": 1000.0, "2892": 200.0, "0050": 50.0}
        with mock.patch(
            "live_tipsoft_dd_switch.compute_gate_state",
            return_value={
                "ok": True,
                "path3_active": False,
                "fill": "FT_TO_CASH",
                "want_trail": True,
                "trail42_on": False,
                "reason": "ok",
                "asof": "2026-09-29",
                "stale": False,
            },
        ):
            out, meta = apply_to_path3_deltas(deltas, pos, "2026-09-29")
        self.assertEqual(out["2880"], -1000.0)
        self.assertEqual(out["2892"], -200.0)
        self.assertNotIn("0050", out)
        self.assertEqual(meta["fill"], "FT_TO_CASH")

    def test_apply_stale_fail_closed_keeps_within(self) -> None:
        deltas = {"2880": 10.0}
        with mock.patch(
            "live_tipsoft_dd_switch.compute_gate_state",
            return_value={
                "ok": False,
                "path3_active": None,
                "fill": None,
                "reason": "nav_stale",
                "stale": True,
            },
        ):
            out, meta = apply_to_path3_deltas(deltas, {"2880": 100.0}, "2099-01-01")
        self.assertEqual(out, deltas)
        self.assertEqual(meta["reason"], "nav_stale")
        self.assertFalse(meta["applied"])


class SessionAndTipMeta(unittest.TestCase):
    def test_session_meta_keys(self) -> None:
        meta = session_meta()
        self.assertTrue(meta["tipsoft_dd_switch_live"])
        self.assertEqual(meta["tipsoft_dd_switch_wire_mode"], WIRE_MODE)
        self.assertFalse(meta["tipsoft_dd_return_blend_applied"])
        self.assertTrue(meta["tipsoft_dd_switch_path3_within_keep"])
        self.assertTrue(meta["tipsoft_dd_switch_soft_fin_tel_stay_off"])

    def test_cutover_stamps_include_dd_switch(self) -> None:
        stamps = build_cutover_stamps()
        self.assertTrue(stamps["tipsoft_dd_switch_live"])
        self.assertEqual(
            stamps["tipsoft_dd_switch_policy"], "TIPSOFT_P3_TRAIL42_L4_DD_SWITCH"
        )
        self.assertEqual(stamps["tipsoft_dd_switch_wire_mode"], WIRE_MODE)
        self.assertFalse(stamps["tipsoft_dd_switch_broker"])

    def test_want_trail_series_nonempty(self) -> None:
        s = want_trail_series()
        self.assertGreater(len(s), 100)
        self.assertTrue(set(s.unique()).issubset({True, False}))


if __name__ == "__main__":
    unittest.main()
