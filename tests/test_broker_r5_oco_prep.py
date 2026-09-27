#!/usr/bin/env python3
"""PREP_NOT_OPEN guards — broker submit / R5 observe / OCO intents stay closed."""
from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from tw_share_lots import BOARD_LOT
from yuanta_spark_adapter import (
    API_WIRED,
    OCO_STRATEGY_TYPE,
    SparkNotWiredError,
    build_oco_strategy_intent,
    send_algo_oco_live,
    send_stock_order_live,
    write_spark_oco_intents,
)


class GatesStayClosed(unittest.TestCase):
    def test_api_wired_false(self) -> None:
        self.assertFalse(API_WIRED)
        with self.assertRaises(SparkNotWiredError):
            send_stock_order_live()
        with self.assertRaises(SparkNotWiredError):
            send_algo_oco_live()


class OcoIntentTests(unittest.TestCase):
    def test_build_and_write_oco_intent_only(self) -> None:
        intent = build_oco_strategy_intent(
            code="0050",
            asof=date(2026, 9, 26),
            shares=2 * BOARD_LOT,
            trigger_price_1=150.0,
            order_price_1=149.5,
            trigger_price_2=130.0,
            order_price_2=129.5,
        )
        self.assertEqual(intent.StrategyType, OCO_STRATEGY_TYPE)
        self.assertEqual(intent.status, "INTENT_ONLY")
        self.assertFalse(intent.api_wired)
        self.assertEqual(intent.leg1.OrderQty, 2)
        self.assertEqual(intent.leg1.StkCode, intent.leg2.StkCode)
        with tempfile.TemporaryDirectory() as td:
            path = write_spark_oco_intents(Path(td), date(2026, 9, 26), [intent])
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertTrue(payload["execute_blocked"])
            self.assertFalse(payload["api_wired"])
            self.assertEqual(payload["strategy_type"], 3)


class PrepStatusTests(unittest.TestCase):
    def test_prep_status_ok_not_open(self) -> None:
        from ops_broker_r5_oco_prep_status import build_prep_report

        report = build_prep_report(run_r5=False)
        self.assertTrue(report["execute_blocked"])
        self.assertEqual(report["status"], "PREP_OK_NOT_OPEN")
        self.assertFalse(report["gates"]["broker_live_write_accepted"])
        self.assertFalse(report["gates"]["spark_api_wired"])
        self.assertTrue(report["tracks"]["conditional_oco"]["send_algo_blocked"])
        self.assertTrue(report["tracks"]["real_submit_stock_order"]["send_stock_blocked"])


class R5ObserveAutoTests(unittest.TestCase):
    def test_resolve_prefers_nothing_without_files_or_synth(self) -> None:
        from ops_r5_observe_auto import SYNTH, resolve_custody

        c = resolve_custody(prefer_dropin=True)
        # Synthetic always present in repo — expect synthetic when no drop-in.
        self.assertEqual(c, SYNTH)

    def test_run_observe_synthetic(self) -> None:
        from ops_r5_observe_auto import run_r5_observe

        with tempfile.TemporaryDirectory() as td:
            out = run_r5_observe(
                prefer_dropin=True,
                asof="2026-09-16",
                out_dir=Path(td),
            )
            self.assertTrue(out["reconcile_ran"])
            self.assertTrue(out["observe_only"])
            self.assertTrue(out["execute_blocked"])
            self.assertTrue(out["reconcile_all_ok"])


if __name__ == "__main__":
    unittest.main()
