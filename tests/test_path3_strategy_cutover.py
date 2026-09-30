#!/usr/bin/env python3
"""Guards for Path3 strategy cutover WITHIN_SLEEVE_PATH3 (0kac ACCEPT)."""
from __future__ import annotations

import unittest
from unittest import mock

from live_config import (
    LIVE,
    LIVE_PATH3_STRATEGY_CUTOVER,
    LIVE_PATH3_STRATEGY_CUTOVER_SCOPE,
)
from live_path3_strategy_cutover import (
    ACCEPT_BALLOT,
    MECHANISM_ID,
    SCOPE_WITHIN_SLEEVE_PATH3,
    daily_path3_recon_enabled,
    is_cutover_on,
    is_within_sleeve_cutover,
    suppress_soft_fin_tel,
)
from live_path3_t0_switch_emitter import BOOK_COMP, BOOK_SAT, maybe_emit_switch_orders
from live_path3_t0_weight_engine import plan_or_none_for_pipeline
from path3_comp_sat_daily_share_ssot import ENGINE_ID as ENGINE_LEDGER


def _soft_rows():
    return [
        {"order_id": "2026-06-12-2880-BUY", "code": "2880", "side": "BUY", "qty": 1000},
        {"order_id": "2026-06-12-2412-SELL", "code": "2412", "side": "SELL", "qty": 1000},
        {"order_id": "2026-06-12-0050-BUY", "code": "0050", "side": "BUY", "qty": 2000},
        {
            "order_id": "2026-06-12-00631L-BUY",
            "code": "00631L",
            "side": "BUY",
            "qty": 1000,
        },
    ]


def _toy_signal():
    import pandas as pd

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


class CutoverFlagDefaults(unittest.TestCase):
    def test_flag_on_after_accept(self) -> None:
        self.assertTrue(LIVE.live_path3_strategy_cutover)
        self.assertTrue(LIVE_PATH3_STRATEGY_CUTOVER)
        self.assertEqual(LIVE_PATH3_STRATEGY_CUTOVER_SCOPE, SCOPE_WITHIN_SLEEVE_PATH3)
        self.assertTrue(is_cutover_on())
        self.assertTrue(is_within_sleeve_cutover())
        self.assertTrue(daily_path3_recon_enabled())
        self.assertIn("WITHIN_SLEEVE_PATH3", LIVE.live_path3_strategy_cutover_ballot)
        self.assertIn("WITHIN_SLEEVE_PATH3", ACCEPT_BALLOT)


class SuppressSoftFinTel(unittest.TestCase):
    def test_suppresses_fin_tel_keeps_0050_and_satellite(self) -> None:
        kept, meta = suppress_soft_fin_tel(_soft_rows())
        self.assertEqual(meta["mechanism_id"], MECHANISM_ID)
        self.assertTrue(meta["applied"])
        self.assertEqual(meta["n_muted"], 2)
        self.assertEqual({r["code"] for r in kept}, {"0050", "00631L"})
        self.assertTrue(meta["soft_0050_keep"])
        self.assertTrue(meta["supersedes_flip_mute"])


class DailyLedgerWithoutFlip(unittest.TestCase):
    def test_pipeline_no_flip_calls_ledger_under_cutover(self) -> None:
        sig = _toy_signal()
        fake_delta = {"2880": -1000.0}
        fake_meta = {
            "engine_id": ENGINE_LEDGER,
            "reason": "ledger_scaled_recon",
            "n_delta_names": 1,
            "policy": "LEDGER_SCALED_RECON",
        }
        with mock.patch(
            "path3_comp_sat_daily_share_ssot.plan_delta_shares_ledger",
            return_value=(fake_delta, fake_meta),
        ) as mocked:
            delta, meta = plan_or_none_for_pipeline(
                asof="2026-09-23",
                pos={"2880": 1000.0, "0050": 100.0},
                prices={"2880": 40.0, "0050": 100.0},
                signal=sig,
            )
        mocked.assert_called_once()
        self.assertEqual(delta, fake_delta)
        self.assertTrue(meta.get("path3_strategy_cutover_daily"))
        self.assertEqual(meta.get("recon_mode"), "daily_cutover")
        self.assertEqual(meta["reason"], "ledger_scaled_recon")

    def test_emit_allows_no_flip_under_cutover(self) -> None:
        sig = _toy_signal()
        rows, meta = maybe_emit_switch_orders(
            asof="2026-09-23",
            prices={"2880": 40.0},
            delta_shares={"2880": 2000.0},
            authorized=True,
            signal=sig,
        )
        self.assertTrue(meta.get("path3_strategy_cutover_daily"))
        self.assertNotEqual(meta.get("reason"), "no_flip")
        self.assertGreater(len(rows), 0)
        self.assertTrue(all(str(r["order_id"]).endswith("-P3T0") for r in rows))

    def test_status_quo_no_flip_when_cutover_mocked_off(self) -> None:
        sig = _toy_signal()
        with mock.patch(
            "live_path3_strategy_cutover.daily_path3_recon_enabled", return_value=False
        ):
            delta, meta = plan_or_none_for_pipeline(
                asof="2026-09-23",
                pos={"2880": 1000.0},
                prices={"2880": 40.0},
                signal=sig,
            )
            rows, em = maybe_emit_switch_orders(
                asof="2026-09-23",
                prices={"2880": 40.0},
                delta_shares={"2880": 2000.0},
                authorized=True,
                signal=sig,
            )
        self.assertIsNone(delta)
        self.assertEqual(meta["reason"], "no_flip")
        self.assertEqual(em["reason"], "no_flip")
        self.assertEqual(rows, [])


if __name__ == "__main__":
    unittest.main()
