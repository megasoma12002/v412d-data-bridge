#!/usr/bin/env python3
"""Unit tests for live fill ports (paper Exact T+1 + dry_run shadow)."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from live_execution import (
    DEFAULT_FILL_PORT,
    DryRunFillPort,
    FILL_ROW_KEYS,
    PaperOpenFillPort,
    fill_pending_at_open,
    resolve_fill_port,
)
from live_ledger import SLIP
from tw_share_lots import BOARD_LOT


class FillPortTests(unittest.TestCase):
    def test_resolve_default_paper(self) -> None:
        port = resolve_fill_port(None)
        self.assertEqual(port.name, DEFAULT_FILL_PORT)
        self.assertIsInstance(port, PaperOpenFillPort)

    def test_resolve_unknown_exits(self) -> None:
        with self.assertRaises(SystemExit):
            resolve_fill_port("shioaji")

    def test_paper_returns_fills_defers_csv(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            sig = "2024-01-02"
            fill_day = pd.Timestamp("2024-01-03")
            pd.DataFrame(
                [
                    {
                        "order_id": "o1",
                        "signal_date": sig,
                        "code": "0050",
                        "side": "BUY",
                        "quantity": BOARD_LOT,
                    }
                ]
            ).to_csv(sdir / "orders.csv", index=False)
            pos: dict[str, float] = {}
            cash = 50_000_000.0
            open_prices = {"0050": 100.0}
            pos2, cash2, fills, same_bar, ok = fill_pending_at_open(
                state_dir=sdir,
                latest=fill_day,
                open_prices=open_prices,
                pos=pos,
                cash=cash,
                fill_port="paper",
            )
            self.assertTrue(ok)
            self.assertEqual(same_bar, 0)
            self.assertEqual(len(fills), 1)
            # Pipeline day-commit owns fills.csv append (with portfolio_state).
            self.assertFalse((sdir / "fills.csv").exists())
            row = fills[0]
            for k in FILL_ROW_KEYS:
                self.assertIn(k, row)
            self.assertEqual(row["fill_id"], "o1")
            self.assertAlmostEqual(row["fill_price"], 100.0 * (1 + SLIP))
            self.assertEqual(pos2["0050"], BOARD_LOT)
            self.assertLess(cash2, cash)

    def test_dry_run_shadow_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            pd.DataFrame(
                [
                    {
                        "order_id": "o2",
                        "signal_date": "2024-01-02",
                        "code": "0050",
                        "side": "BUY",
                        "quantity": BOARD_LOT,
                    }
                ]
            ).to_csv(sdir / "orders.csv", index=False)
            pos = {"0050": 0.0}
            cash = 50_000_000.0
            pos2, cash2, fills, _, ok = fill_pending_at_open(
                state_dir=sdir,
                latest=pd.Timestamp("2024-01-03"),
                open_prices={"0050": 100.0},
                pos=dict(pos),
                cash=cash,
                fill_port=DryRunFillPort(),
            )
            self.assertTrue(ok)
            self.assertEqual(len(fills), 1)
            self.assertFalse((sdir / "fills.csv").exists())
            self.assertEqual(pos2, pos)
            self.assertEqual(cash2, cash)
            shadow = sdir / "broker_dryrun" / "fills_2024-01-03.json"
            self.assertTrue(shadow.exists())
            payload = json.loads(shadow.read_text(encoding="utf-8"))
            self.assertFalse(payload["live_fills_written"])
            self.assertEqual(payload["n_fills"], 1)


if __name__ == "__main__":
    unittest.main()
