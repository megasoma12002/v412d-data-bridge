#!/usr/bin/env python3
"""Offline Yuanta SPARK adapter skeleton tests (no DLL)."""
from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from tw_share_lots import BOARD_LOT
from yuanta_spark_adapter import (
    API_WIRED,
    BASKET_NO_MAX,
    SparkNotWiredError,
    basket_no_for,
    build_intents_from_pending,
    build_stock_order_intent,
    lookup_client_order_id,
    map_send_stock_order_row,
    order_qty_to_shares,
    send_stock_order_live,
    shares_to_order_qty,
    write_spark_intents,
)


class LotAndBasketTests(unittest.TestCase):
    def test_api_not_wired(self) -> None:
        self.assertFalse(API_WIRED)
        with self.assertRaises(SparkNotWiredError):
            send_stock_order_live()

    def test_shares_lots_roundtrip(self) -> None:
        self.assertEqual(shares_to_order_qty(BOARD_LOT), 1)
        self.assertEqual(shares_to_order_qty(3 * BOARD_LOT), 3)
        self.assertEqual(order_qty_to_shares(2), 2 * BOARD_LOT)
        with self.assertRaises(ValueError):
            shares_to_order_qty(500)

    def test_basket_no_alnum_and_max_len(self) -> None:
        short = basket_no_for("o1@2026-07-13")
        self.assertLessEqual(len(short), BASKET_NO_MAX)
        self.assertRegex(short, r"^[A-Za-z0-9]+$")
        long_id = "2026-07-10-0050-BUY@2026-07-13-extra-suffix-makes-this-long"
        b = basket_no_for(long_id)
        self.assertEqual(len(b), BASKET_NO_MAX)
        self.assertEqual(b, basket_no_for(long_id))


class IntentAndAckTests(unittest.TestCase):
    def test_build_intent_fields(self) -> None:
        intent = build_stock_order_intent(
            order_id="2026-07-10-0050-BUY",
            client_order_id="2026-07-10-0050-BUY@2026-07-13",
            code="0050",
            side="BUY",
            shares=BOARD_LOT,
            asof=date(2026, 7, 13),
            account="S98875005091",
        )
        self.assertEqual(intent.OrderQty, 1)
        self.assertEqual(intent.BuySell, "B")
        self.assertEqual(intent.APCode, 0)
        self.assertEqual(intent.TradeDate, "2026/07/13")
        self.assertFalse(intent.api_wired)
        self.assertEqual(intent.status, "INTENT_ONLY")
        self.assertLessEqual(len(intent.BasketNo), BASKET_NO_MAX)
        fields = intent.spark_stock_order_fields()
        self.assertEqual(fields["StkCode"], "0050")
        self.assertEqual(fields["BasketNo"], intent.BasketNo)

    def test_write_intents_and_basket_map(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            pending = [
                {
                    "order_id": "2026-07-10-0050-BUY",
                    "code": "0050",
                    "side": "BUY",
                    "quantity": BOARD_LOT,
                }
            ]
            intents = build_intents_from_pending(
                pending, asof=date(2026, 7, 13), account=""
            )
            path = write_spark_intents(sdir, date(2026, 7, 13), intents)
            self.assertTrue(path.exists())
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertFalse(payload["api_wired"])
            self.assertEqual(payload["n"], 1)
            coid = lookup_client_order_id(sdir, intents[0].BasketNo)
            self.assertEqual(coid, intents[0].client_order_id)

    def test_map_success_ack(self) -> None:
        intent = build_stock_order_intent(
            order_id="o1",
            client_order_id="o1@2026-07-13",
            code="0050",
            side="BUY",
            shares=BOARD_LOT,
            asof=date(2026, 7, 13),
        )
        result = map_send_stock_order_row(
            {"ReplyCode": 0, "OrderNO": "f001", "Identify": 1},
            intent=intent,
            fill_price=100.0,
            signal_date="2026-07-10",
        )
        self.assertTrue(result.ok)
        assert result.broker_ack is not None
        self.assertEqual(result.broker_ack["order_id"], "o1")
        self.assertEqual(result.broker_ack["quantity"], BOARD_LOT)
        self.assertEqual(result.broker_ack["broker_order_no"], "f001")
        self.assertEqual(result.broker_ack["fill_price"], 100.0)

    def test_map_reject(self) -> None:
        intent = build_stock_order_intent(
            order_id="o1",
            client_order_id="o1@2026-07-13",
            code="0050",
            side="SELL",
            shares=BOARD_LOT,
            asof=date(2026, 7, 13),
        )
        result = map_send_stock_order_row(
            {"ReplyCode": 1, "ErrNO": "A005", "Advisory": "cancelled"},
            intent=intent,
        )
        self.assertFalse(result.ok)
        self.assertIn("spark_reject", str(result.reject_reason))


if __name__ == "__main__":
    unittest.main()
