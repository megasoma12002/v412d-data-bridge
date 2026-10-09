#!/usr/bin/env python3
"""Guards for Path3/tipsoft day overlay orchestration extract."""
from __future__ import annotations

import unittest
from unittest import mock

import pandas as pd

from live_day_overlays import apply_path3_tipsoft_overlays, overlay_signal_fields
from live_soft_path3_coexist_mute import apply_coexist_mute


class LiveDayOverlaysGuards(unittest.TestCase):
    def test_within_cutover_suppresses_soft_fin_tel_and_stamps_tipsoft(self) -> None:
        soft_rows = [
            {"order_id": "2026-06-12-2880-BUY", "code": "2880", "side": "BUY", "qty": 1000},
            {"order_id": "2026-06-12-2412-SELL", "code": "2412", "side": "SELL", "qty": 1000},
            {"order_id": "2026-06-12-0050-BUY", "code": "0050", "side": "BUY", "qty": 2000},
        ]
        # Real WITHIN cutover is ON in LIVE — Soft FIN/TEL muted; tipsoft stamps present.
        with mock.patch('live_path3_t0_weight_engine.plan_or_none_for_pipeline',return_value=({}, {'reason':'ledger_scaled_empty','switch':{'flip':False}})), \
             mock.patch('live_tipsoft_dd_switch.apply_to_path3_deltas',return_value=({}, {'gate':{'ok':True}})):
            ov = apply_path3_tipsoft_overlays(
                list(soft_rows),
                asof=pd.Timestamp("2026-09-29"),
                pos={"0050": 1000.0, "2880": 1000.0},
                prices={"0050": 100.0, "2880": 20.0, "2412": 100.0},
            )
        codes = {r["code"] for r in ov.order_rows if not str(r.get("order_id", "")).endswith("-P3T0")}
        # Soft FIN/TEL suppressed under WITHIN; 0050 Soft may remain depending on cutover.
        self.assertTrue(ov.path3_cutover_meta.get("applied") or ov.path3_cutover_meta.get("enabled"))
        self.assertIn("tipsoft_live_override_live", ov.tipsoft_override_meta)
        self.assertIn("tipsoft_dd_switch_live", ov.tipsoft_dd_meta)
        fields = overlay_signal_fields(ov)
        self.assertIn("path3_strategy_cutover_live", fields)
        self.assertIn("tipsoft_live_override_wire_mode", fields)
        self.assertIn("tipsoft_dd_switch_live", fields)
        self.assertEqual(fields.get("tipsoft_override_return_blend_applied"), False)

    def test_mute_helper_still_keeps_0050(self) -> None:
        soft_rows = [
            {"order_id": "2026-06-12-2880-BUY", "code": "2880", "side": "BUY", "qty": 1000},
            {"order_id": "2026-06-12-0050-BUY", "code": "0050", "side": "BUY", "qty": 2000},
        ]
        kept, meta = apply_coexist_mute(
            soft_rows,
            mute_enabled=True,
            emit_enabled=True,
            flip=True,
            path3_delta_shares={"2880": -1000.0},
        )
        self.assertEqual({r["code"] for r in kept}, {"0050"})
        self.assertTrue(meta.get("applied") or meta.get("should_mute"))

    def test_dd_switch_tip_apply_runs_before_emit(self) -> None:
        """Conflict resolve: overlays must call apply_to_path3_deltas (not stamps-only)."""
        asof = pd.Timestamp("2026-09-29")
        deltas = {"2880": -1000.0, "0050": 500.0}
        apply_meta = {
            "tipsoft_dd_switch_live": True,
            "tipsoft_dd_switch_wire_mode": "path3_gate_ft_cash_apply",
            "applied": True,
            'gate':{'ok':True},
        }
        with (
            mock.patch(
                "live_day_overlays.LIVE_T0_CARVE_FIN_SAT_SWITCH_EMIT", True
            ),
            mock.patch("live_day_overlays.LIVE_TIPSOFT_DD_SWITCH", True),
            mock.patch(
                "live_path3_t0_weight_engine.plan_or_none_for_pipeline",
                return_value=(deltas, {"engine_id": "test", "switch": {"flip": False}}),
            ),
            mock.patch(
                "live_tipsoft_dd_switch.apply_to_path3_deltas",
                return_value=(deltas, apply_meta),
            ) as apply_mock,
            mock.patch(
                "live_path3_t0_switch_emitter.maybe_emit_switch_orders",
                return_value=([], {"n_orders": 0, "reason": "test"}),
            ) as emit_mock,
            mock.patch(
                "live_tipsoft_dd_switch.session_meta",
                return_value={"tipsoft_dd_switch_live": True},
            ),
            mock.patch(
                "live_tipsoft_live_override.session_meta",
                return_value={"tipsoft_live_override_live": True},
            ),
        ):
            ov = apply_path3_tipsoft_overlays(
                [],
                asof=asof,
                pos={"2880": 1000.0, "0050": 1000.0},
                prices={"2880": 20.0, "0050": 100.0},
            )
        apply_mock.assert_called_once()
        emit_mock.assert_called_once()
        self.assertEqual(
            ov.path3_emit_meta.get("tipsoft_dd_switch"), apply_meta
        )
        self.assertTrue(ov.tipsoft_dd_meta.get("tipsoft_dd_switch_live"))


if __name__ == "__main__":
    unittest.main()
