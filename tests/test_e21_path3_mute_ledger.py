#!/usr/bin/env python3
"""e21-style Path3 ledger + Soft mute orchestration guards (0kaa/0kab)."""
from __future__ import annotations

import unittest
from unittest import mock

import pandas as pd

from live_path3_t0_switch_emitter import (
    BOOK_COMP,
    BOOK_SAT,
    maybe_emit_switch_orders,
)
from live_path3_t0_weight_engine import plan_or_none_for_pipeline
from live_soft_path3_coexist_mute import apply_coexist_mute
from path3_comp_sat_daily_share_ssot import ENGINE_ID as ENGINE_LEDGER
from t0_carve_fin_sat_switch import CARVE_OUT_ID


def _flip_signal() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-06-11", "2026-06-12"]),
            "trail_rel_63": [-0.02, -0.02],
            "sat_lead": [False, True],
            "w_sat": [0.0, 1.0],
            "flip": [False, True],
            "book": [BOOK_COMP, BOOK_SAT],
            "book_prev": [BOOK_COMP, BOOK_COMP],
        }
    )


def _soft_rows():
    return [
        {"order_id": "2026-06-12-2880-BUY", "code": "2880", "side": "BUY", "qty": 1000},
        {"order_id": "2026-06-12-2412-SELL", "code": "2412", "side": "SELL", "qty": 1000},
        {"order_id": "2026-06-12-0050-BUY", "code": "0050", "side": "BUY", "qty": 2000},
    ]


class E21Path3MuteLedgerOrchestration(unittest.TestCase):
    """Mirrors e21 order: plan → mute Soft FIN/TEL → emit -P3T0."""

    def test_flip_ledger_mute_then_emit(self) -> None:
        sig = _flip_signal()
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
        fake_delta = {"2880": -1000.0, "2892": 1000.0}
        fake_meta = {
            "engine_id": ENGINE_LEDGER,
            "reason": "ledger_scaled_recon",
            "n_delta_names": 2,
            "policy": "LEDGER_SCALED_RECON",
            "ledger_asof": "2026-06-12",
            "ledger_stale": False,
        }
        with mock.patch(
            "path3_comp_sat_daily_share_ssot.plan_delta_shares_ledger",
            return_value=(fake_delta, fake_meta),
        ):
            deltas, wmeta = plan_or_none_for_pipeline(
                asof="2026-06-12", pos=pos, prices=prices, signal=sig
            )
        self.assertEqual(deltas, fake_delta)
        self.assertEqual(wmeta["weight_engine_mode"], "ledger")
        flip = bool((wmeta.get("switch") or {}).get("flip"))
        self.assertTrue(flip)

        soft_kept, mute_meta = apply_coexist_mute(
            _soft_rows(),
            mute_enabled=True,
            emit_enabled=True,
            flip=flip,
            path3_delta_shares=deltas,
        )
        self.assertTrue(mute_meta["applied"])
        self.assertEqual({r["code"] for r in soft_kept}, {"0050"})

        path3_rows, em = maybe_emit_switch_orders(
            asof="2026-06-12",
            prices=prices,
            delta_shares=deltas,
            authorized=True,
            signal=sig,
        )
        self.assertEqual(em["reason"], "emitted")
        self.assertTrue(all(str(r["order_id"]).endswith("-P3T0") for r in path3_rows))
        self.assertTrue(all(r["carve_out_id"] == CARVE_OUT_ID for r in path3_rows))
        combined = soft_kept + path3_rows
        self.assertTrue(any(r["code"] == "0050" and not str(r["order_id"]).endswith("-P3T0") for r in combined))
        self.assertTrue(any(str(r["order_id"]).endswith("-P3T0") for r in combined))

    def test_flip_empty_path3_still_mutes_soft_fin_tel(self) -> None:
        soft_kept, mute_meta = apply_coexist_mute(
            _soft_rows(),
            mute_enabled=True,
            emit_enabled=True,
            flip=True,
            path3_delta_shares=None,
        )
        self.assertTrue(mute_meta["should_mute"])
        self.assertEqual({r["code"] for r in soft_kept}, {"0050"})


if __name__ == "__main__":
    unittest.main()
