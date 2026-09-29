#!/usr/bin/env python3
"""Guards for Path3 COMP↔SAT weight-engine Stage A proxy (0ka8)."""
from __future__ import annotations

import unittest
from unittest import mock

import pandas as pd

from e16_soft_frozen_base import FIN, TEL
from live_path3_t0_switch_emitter import BOOK_COMP, BOOK_SAT, maybe_emit_switch_orders
from live_path3_t0_weight_engine import (
    ENGINE_ID,
    plan_delta_shares,
    plan_sat_equal_recon,
)
from t0_carve_fin_sat_switch import CARVE_OUT_ID


def _toy_signal() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-09-23", "2026-09-24"]),
            "trail_rel_63": [-0.02, -0.02],
            "sat_lead": [False, True],
            "w_sat": [0.0, 1.0],
            "flip": [False, True],
            "book": [BOOK_COMP, BOOK_SAT],
            "book_prev": [BOOK_COMP, BOOK_COMP],
        }
    )


class WeightEngineSatRecon(unittest.TestCase):
    def test_equal_recon_nonempty_delta(self) -> None:
        pos = {
            "2880": 2_000_000.0,
            "2886": 1_000_000.0,
            "2892": 1_000_000.0,
            "5880": 1_000_000.0,
            "2412": 50_000.0,
            "3045": 50_000.0,
            "4904": 50_000.0,
            "0050": 100_000.0,
        }
        prices = {
            "2880": 40.0,
            "2886": 40.0,
            "2892": 40.0,
            "5880": 40.0,
            "2412": 100.0,
            "3045": 100.0,
            "4904": 100.0,
            "0050": 100.0,
        }
        delta, meta = plan_sat_equal_recon(pos=pos, prices=prices)
        self.assertEqual(meta["engine_id"], ENGINE_ID)
        self.assertGreater(meta["n_delta_names"], 0)
        self.assertIn("2880", delta)
        # 0050 KEEP — not in delta
        self.assertNotIn("0050", delta)

    def test_flip_to_sat_emits_tagged_p3t0(self) -> None:
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
        sig = _toy_signal()
        delta, meta = plan_delta_shares(
            asof="2026-09-24", pos=pos, prices=prices, signal=sig, require_flip=True
        )
        self.assertIsNotNone(delta)
        self.assertEqual(meta["reason"], "sat_equal_recon")
        self.assertGreater(len(delta or {}), 0)
        rows, em = maybe_emit_switch_orders(
            asof="2026-09-24",
            prices=prices,
            delta_shares=delta,
            authorized=True,
            signal=sig,
        )
        self.assertGreater(len(rows), 0)
        self.assertEqual(em["reason"], "emitted")
        self.assertTrue(all(str(r["order_id"]).endswith("-P3T0") for r in rows))
        self.assertTrue(all(r["carve_out_id"] == CARVE_OUT_ID for r in rows))

    def test_no_flip_returns_none(self) -> None:
        sig = _toy_signal()
        delta, meta = plan_delta_shares(
            asof="2026-09-23",
            pos={"2880": 1000.0},
            prices={"2880": 40.0},
            signal=sig,
            require_flip=True,
        )
        self.assertIsNone(delta)
        self.assertEqual(meta["reason"], "no_flip")

    def test_comp_identity_empty(self) -> None:
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
            asof="2026-09-24",
            pos={"2880": 1000.0, "2886": 1000.0},
            prices={"2880": 40.0, "2886": 40.0},
            signal=sig,
            require_flip=True,
        )
        self.assertEqual(delta, {})
        self.assertEqual(meta["reason"], "comp_identity_proxy_no_delta")


if __name__ == "__main__":
    unittest.main()
