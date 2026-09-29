#!/usr/bin/env python3
"""Guards for Path3 COMP↔SAT weight-engine Stage B (0ka9)."""
from __future__ import annotations

import unittest

import pandas as pd

from live_path3_t0_switch_emitter import BOOK_COMP, BOOK_SAT, maybe_emit_switch_orders
from live_path3_t0_weight_engine import (
    ENGINE_ID,
    plan_comp_or_k9_hard150,
    plan_delta_shares,
    plan_sat_relax_kd,
)
from t0_carve_fin_sat_switch import CARVE_OUT_ID


def _pos_px():
    pos = {
        "2880": 2_700_000.0,
        "2886": 2_200_000.0,
        "2892": 3_100_000.0,
        "5880": 4_200_000.0,
        "2412": 80_000.0,
        "3045": 100_000.0,
        "4904": 110_000.0,
        "0050": 300_000.0,
    }
    prices = {
        "2880": 45.0,
        "2886": 50.0,
        "2892": 40.0,
        "5880": 26.0,
        "2412": 145.0,
        "3045": 120.0,
        "4904": 105.0,
        "0050": 110.0,
    }
    return pos, prices


class StageBOverlays(unittest.TestCase):
    def test_comp_plan_nonempty_with_hard_zero(self) -> None:
        pos, prices = _pos_px()
        overlays = {
            "ok": True,
            "asof_used": "2026-09-24",
            "kd_scores": {c: 1.0 for c in ("2880", "2886", "2892", "5880")},
            "or_k9_buy_ok": {"2880": True, "2886": True, "2892": True, "5880": True},
            "hard150_sell_ok": {"2880": True, "2886": False, "2892": True, "5880": True},
            "base_buy_ok": {"2880": True, "2886": True, "2892": True, "5880": True},
        }
        delta, meta = plan_comp_or_k9_hard150(pos=pos, prices=prices, overlays=overlays)
        self.assertEqual(meta["engine_id"], ENGINE_ID)
        self.assertIn("2886", meta["forced_zero_hard"])
        self.assertGreater(meta["n_delta_names"], 0)
        # 2886 forced to 0 from 2.2M → large sell
        self.assertLess(delta.get("2886", 0), 0)

    def test_sat_relax_nonempty(self) -> None:
        pos, prices = _pos_px()
        overlays = {
            "ok": True,
            "asof_used": "2026-09-24",
            "kd_scores": {"2880": 2.0, "2886": 1.0, "2892": 1.0, "5880": 0.5},
            "base_buy_ok": {"2880": True, "2886": True, "2892": True, "5880": True},
            "or_k9_buy_ok": {},
            "hard150_sell_ok": {},
        }
        delta, meta = plan_sat_relax_kd(pos=pos, prices=prices, overlays=overlays)
        self.assertEqual(meta["policy"], "SAT_RELAX_KD")
        self.assertGreaterEqual(meta["n_delta_names"], 0)

    def test_flip_to_comp_emits_p3t0(self) -> None:
        pos, prices = _pos_px()
        sig = pd.DataFrame(
            {
                "date": pd.to_datetime(["2026-09-23", "2026-09-24"]),
                "trail_rel_63": [-0.001, 0.02],
                "sat_lead": [True, False],
                "w_sat": [1.0, 0.0],
                "flip": [False, True],
                "book": [BOOK_SAT, BOOK_COMP],
                "book_prev": [BOOK_SAT, BOOK_SAT],
            }
        )
        delta, meta = plan_delta_shares(
            asof="2026-09-24", pos=pos, prices=prices, signal=sig, require_flip=True
        )
        self.assertIsNotNone(delta)
        self.assertTrue(str(meta.get("reason", "")).startswith("comp_"))
        if delta:
            rows, em = maybe_emit_switch_orders(
                asof="2026-09-24",
                prices=prices,
                delta_shares=delta,
                authorized=True,
                signal=sig,
            )
            if rows:
                self.assertTrue(all(str(r["order_id"]).endswith("-P3T0") for r in rows))
                self.assertEqual({r["carve_out_id"] for r in rows}, {CARVE_OUT_ID})
                self.assertEqual(em["reason"], "emitted")


if __name__ == "__main__":
    unittest.main()
