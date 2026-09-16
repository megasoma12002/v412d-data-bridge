#!/usr/bin/env python3
"""Tests for P2 forward session gate + P4 broker preflight port."""
from __future__ import annotations

import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

from live_execution import BrokerPreflightFillPort, resolve_fill_port
from twse_forward_session_gate import run_gate, should_skip_forward
from twse_session_sources import DayRecord, write_calendar_csv
from tw_share_lots import BOARD_LOT


class SessionGateTests(unittest.TestCase):
    def test_should_skip_when_not_session(self) -> None:
        self.assertTrue(should_skip_forward(is_session=False, status="WEEKEND"))
        self.assertFalse(should_skip_forward(is_session=True, status="OPEN"))

    def test_gate_writes_skip_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            cal = Path(td) / "cal.csv"
            write_calendar_csv(
                [
                    DayRecord(
                        date=date(2026, 7, 10),
                        is_session=False,
                        kind="CLOSED_TYPHOON_OR_NODATA",
                        is_settlement=False,
                    )
                ],
                cal,
            )
            out = Path(td) / "forward"
            payload = run_gate(
                asof=date(2026, 7, 10),
                out_dir=out,
                use_network=False,
                calendar_path=cal,
            )
            self.assertTrue(payload["skipped"])
            self.assertTrue((out / "session_skip.json").exists())
            data = json.loads((out / "session_skip.json").read_text(encoding="utf-8"))
            self.assertEqual(data["status"], "CLOSED_TYPHOON_OR_NODATA")


class BrokerPreflightTests(unittest.TestCase):
    def test_resolve_broker_port(self) -> None:
        port = resolve_fill_port("broker")
        self.assertEqual(port.name, "broker")
        self.assertIsInstance(port, BrokerPreflightFillPort)

    def test_blocks_when_not_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            pd.DataFrame(
                [
                    {
                        "order_id": "o1",
                        "signal_date": "2026-07-09",
                        "code": "0050",
                        "side": "BUY",
                        "quantity": BOARD_LOT,
                    }
                ]
            ).to_csv(sdir / "orders.csv", index=False)
            port = BrokerPreflightFillPort(
                probe_fn=lambda _d: SimpleNamespace(
                    status="UNKNOWN",
                    broker_submit_allowed=False,
                    is_session=False,
                    notes=["test"],
                )
            )
            pos, cash, fills, _, ok = port.fill_pending(
                state_dir=sdir,
                latest=pd.Timestamp("2026-07-10"),
                open_prices={"0050": 100.0},
                pos={},
                cash=1_000_000.0,
            )
            self.assertEqual(fills, [])
            self.assertEqual(pos, {})
            self.assertEqual(cash, 1_000_000.0)
            self.assertTrue(ok)
            self.assertFalse((sdir / "fills.csv").exists())
            self.assertTrue((sdir / "broker_preflight" / "block_2026-07-10.json").exists())

    def test_open_still_no_live_fills_without_adapter(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            port = BrokerPreflightFillPort(
                probe_fn=lambda _d: SimpleNamespace(
                    status="OPEN",
                    broker_submit_allowed=True,
                    is_session=True,
                    notes=["open"],
                )
            )
            pos, cash, fills, _, ok = port.fill_pending(
                state_dir=sdir,
                latest=pd.Timestamp("2026-07-13"),
                open_prices={"0050": 100.0},
                pos={},
                cash=1_000_000.0,
            )
            self.assertEqual(fills, [])
            self.assertFalse((sdir / "fills.csv").exists())
            self.assertTrue(ok)
            allow = json.loads(
                (sdir / "broker_preflight" / "allow_2026-07-13.json").read_text(encoding="utf-8")
            )
            self.assertFalse(allow["blocked"])
            self.assertFalse(allow["live_fills_written"])

    def test_fixture_acks_shadow_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            pd.DataFrame(
                [
                    {
                        "order_id": "o1",
                        "signal_date": "2026-07-10",
                        "code": "0050",
                        "side": "BUY",
                        "quantity": BOARD_LOT,
                    }
                ]
            ).to_csv(sdir / "orders.csv", index=False)
            ack_dir = sdir / "broker_acks"
            ack_dir.mkdir(parents=True)
            (ack_dir / "2026-07-13.json").write_text(
                json.dumps(
                    {
                        "acks": [
                            {
                                "order_id": "o1",
                                "code": "0050",
                                "side": "BUY",
                                "quantity": BOARD_LOT,
                                "fill_price": 100.0,
                                "signal_date": "2026-07-10",
                            }
                        ]
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            port = BrokerPreflightFillPort(
                probe_fn=lambda _d: SimpleNamespace(
                    status="OPEN",
                    broker_submit_allowed=True,
                    is_session=True,
                    notes=["open"],
                ),
                write_live=False,
            )
            pos, cash, fills, _, ok = port.fill_pending(
                state_dir=sdir,
                latest=pd.Timestamp("2026-07-13"),
                open_prices={"0050": 100.0},
                pos={},
                cash=1_000_000.0,
            )
            self.assertEqual(len(fills), 1)
            self.assertEqual(fills[0]["fill_id"], "o1")
            self.assertEqual(pos, {})
            self.assertEqual(cash, 1_000_000.0)
            self.assertFalse((sdir / "fills.csv").exists())
            self.assertTrue(ok)
            shadow = sdir / "broker_preflight" / "fills_2026-07-13.json"
            self.assertTrue(shadow.exists())
            payload = json.loads(shadow.read_text(encoding="utf-8"))
            self.assertEqual(payload["n_fills"], 1)
            self.assertFalse(payload["live_fills_written"])


if __name__ == "__main__":
    unittest.main()
