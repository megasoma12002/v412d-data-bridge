#!/usr/bin/env python3
"""Guards for tip Soft Exact T+1 LIVE_OVERRIDE live wire (0kb2 ACCEPT)."""
from __future__ import annotations

import inspect
import unittest
from pathlib import Path
from unittest import mock

import pandas as pd

from live_config import (
    LIVE,
    LIVE_PATH3_STRATEGY_CUTOVER,
    LIVE_TIPSOFT_LIVE_OVERRIDE,
    LIVE_TIPSOFT_LIVE_OVERRIDE_POLICY,
)
from live_soft_path3_coexist_mute import apply_coexist_mute
from live_tip_meta import build_cutover_stamps
from live_tipsoft_live_override import (
    ACCEPT_BALLOT,
    CONFIRM_K,
    DEFAULT_POLICY_NAV,
    MARGIN,
    MECHANISM_ID,
    STAGE_A_ARM_ID,
    STAGE_A_POLICY_NAV,
    WINDOW,
    WIRE_MODE,
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
        self.assertEqual(WIRE_MODE, "gate_stamps_telemetry")
        self.assertEqual(STAGE_A_ARM_ID, "OVERRIDE_LIVE_W42_M0005_K3")
        self.assertIn("TIPSOFT_P3_LIVE_OVERRIDE_W42_M05_K3", ACCEPT_BALLOT)
        self.assertIn("Path3 WITHIN_SLEEVE KEEP", ACCEPT_BALLOT)
        self.assertIn("broker false", ACCEPT_BALLOT)

    def test_path3_within_still_on(self) -> None:
        self.assertTrue(LIVE_PATH3_STRATEGY_CUTOVER)
        self.assertTrue(LIVE.live_path3_strategy_cutover)

    def test_broker_stays_false(self) -> None:
        self.assertFalse(LIVE.broker_live_write_accepted)
        gate = compute_gate_state()
        self.assertFalse(gate["broker"])
        meta = session_meta()
        self.assertFalse(meta["tipsoft_live_override_broker"])


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

    def test_k_edge_needs_three_consecutive(self) -> None:
        idx = pd.date_range("2020-01-01", periods=80, freq="B")
        live = pd.Series(0.0, index=idx)
        champ = pd.Series(0.0, index=idx)
        live.iloc[-50:] = 0.02
        # Break confirm chain: drop lead on day -2 so K=3 fails at tip.
        live.iloc[-2] = -1.0
        mask = override_mask(live, champ, window=42, margin=0.005, k=3)
        self.assertFalse(bool(mask.iloc[-1]))

    def test_lag1_causal_same_bar_spike_ignored(self) -> None:
        idx = pd.date_range("2020-01-01", periods=80, freq="B")
        live = pd.Series(0.0, index=idx)
        champ = pd.Series(0.0, index=idx)
        # Same-bar tip spike only — lag-1 rolling must not fire early.
        live.iloc[-1] = 5.0
        mask = override_mask(live, champ, window=42, margin=0.005, k=3)
        self.assertFalse(bool(mask.iloc[-1]))


class GateAndSessionMeta(unittest.TestCase):
    def test_compute_gate_ok(self) -> None:
        gate = compute_gate_state()
        self.assertTrue(gate["ok"])
        self.assertTrue(gate["enabled"])
        self.assertEqual(gate["wire_mode"], "gate_stamps_telemetry")
        self.assertFalse(gate["return_blend_applied"])
        self.assertIn(gate["override_on"], (True, False))
        self.assertTrue(gate["path3_within_sleeve_keep"])
        self.assertTrue(gate["soft_fin_tel_stay_off"])
        self.assertFalse(gate["path4_live"])
        self.assertIn("force_live_shell_diag", gate)
        self.assertNotIn("force_live_shell", gate)

    def test_session_meta_flat_columns(self) -> None:
        meta = session_meta()
        self.assertTrue(meta["tipsoft_live_override_live"])
        self.assertEqual(meta["tipsoft_live_override_wire_mode"], "gate_stamps_telemetry")
        self.assertEqual(
            meta["tipsoft_live_override_policy"], "TIPSOFT_P3_LIVE_OVERRIDE_W42_M05_K3"
        )
        self.assertTrue(meta["tipsoft_live_override_path3_within_keep"])
        self.assertTrue(meta["tipsoft_live_override_soft_fin_tel_stay_off"])
        self.assertFalse(meta["tipsoft_override_return_blend_applied"])
        self.assertIn("tipsoft_override_on", meta)
        self.assertIn("tipsoft_override_asof", meta)
        self.assertIn("tipsoft_override_ok", meta)
        self.assertIn("tipsoft_override_stale", meta)
        self.assertIn("tipsoft_override_reason", meta)
        self.assertNotIn("tipsoft_live_override_gate", meta)
        stamps = build_cutover_stamps()
        self.assertTrue(stamps["tipsoft_live_override_live"])
        self.assertEqual(stamps["tipsoft_live_override_wire_mode"], "gate_stamps_telemetry")
        self.assertIn("ACCEPT_2026-09-30", stamps["tipsoft_live_override_cutover"])
        self.assertFalse(stamps["tipsoft_override_return_blend_applied"])
        self.assertFalse(stamps["tipsoft_live_override_broker"])

    def test_nav_stale_fail_loud(self) -> None:
        gate = compute_gate_state(market_tip="2099-01-01")
        self.assertFalse(gate["ok"])
        self.assertTrue(gate["stale"])
        self.assertEqual(gate["reason"], "nav_stale")
        self.assertIsNone(gate["override_on"])

    def test_missing_nav_fail_loud(self) -> None:
        missing = Path("/tmp/tipsoft_override_missing_nav_does_not_exist.csv")
        gate = compute_gate_state(live_nav_path=missing, champ_nav_path=missing)
        self.assertFalse(gate["ok"])
        self.assertEqual(gate["reason"], "missing_nav")
        self.assertIsNone(gate["override_on"])

    def test_m05_alias_equals_stage_a_m0005_nav(self) -> None:
        """M3: policy …_M05_K3 ≡ Stage A arm …_M0005_K3 (margin 0.005)."""
        self.assertTrue(DEFAULT_POLICY_NAV.is_file())
        self.assertTrue(STAGE_A_POLICY_NAV.is_file())
        a = pd.read_csv(DEFAULT_POLICY_NAV, parse_dates=["date"])
        b = pd.read_csv(STAGE_A_POLICY_NAV, parse_dates=["date"])
        merged = a.merge(b, on="date", suffixes=("_obs", "_sa"))
        self.assertGreater(len(merged), 100)
        delta = (merged["nav_obs"] - merged["nav_sa"]).abs().max()
        self.assertLessEqual(float(delta), 1e-9)

    def test_is_on_import_error_only(self) -> None:
        src = inspect.getsource(is_on)
        self.assertIn("except ImportError", src)
        self.assertNotIn("except Exception", src)


class SoftFinTelStayOffWithOverride(unittest.TestCase):
    def test_mute_still_applies_when_override_on(self) -> None:
        soft_rows = [
            {"order_id": "2026-06-12-2880-BUY", "code": "2880", "side": "BUY", "qty": 1000},
            {"order_id": "2026-06-12-2412-SELL", "code": "2412", "side": "SELL", "qty": 1000},
            {"order_id": "2026-06-12-0050-BUY", "code": "0050", "side": "BUY", "qty": 2000},
        ]
        with mock.patch(
            "live_tipsoft_live_override.compute_gate_state",
            return_value={
                "ok": True,
                "stale": False,
                "reason": "ok",
                "asof": "2026-06-12",
                "panel_tip": "2026-06-12",
                "override_on": True,
            },
        ):
            meta = session_meta("2026-06-12")
        self.assertTrue(meta["tipsoft_override_on"])
        self.assertFalse(meta["tipsoft_override_return_blend_applied"])
        # Soft FIN/TEL still muted by coexist mute (Path3 WITHIN KEEP).
        kept, mute_meta = apply_coexist_mute(
            soft_rows,
            mute_enabled=True,
            emit_enabled=True,
            flip=True,
            path3_delta_shares={"2880": -1000.0},
        )
        self.assertTrue(mute_meta["applied"] or mute_meta.get("should_mute"))
        self.assertEqual({r["code"] for r in kept}, {"0050"})


class E21OrderRowsInvariant(unittest.TestCase):
    def test_pipeline_spreads_meta_after_orders_no_blend(self) -> None:
        """H1/L1: e21 stamps tipsoft meta via overlays; does not blend order_rows."""
        root = Path(__file__).resolve().parents[1] / "scripts"
        e21 = (root / "e21_forward_pipeline.py").read_text(encoding="utf-8")
        overlays = (root / "live_day_overlays.py").read_text(encoding="utf-8")
        self.assertIn("apply_path3_tipsoft_overlays", e21)
        self.assertIn("overlay_signal_fields", e21)
        self.assertIn("session_meta(asof, market_tip=asof)", overlays)
        self.assertNotIn("tipsoft_live_override_ballot_text", e21)
        self.assertNotIn("tipsoft_live_override_policy_id", e21)
        # No return-blend apply helper referenced in pipeline / overlays.
        for src in (e21, overlays):
            self.assertNotIn("where(conf", src)
            self.assertNotIn(
                "return_blend",
                src.lower().replace("tipsoft_override_return_blend_applied", ""),
            )


if __name__ == "__main__":
    unittest.main()
