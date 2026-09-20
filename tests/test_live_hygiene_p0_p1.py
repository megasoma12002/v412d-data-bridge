#!/usr/bin/env python3
"""Tests for ledger commit guards, path gates, and paper SELL-before-BUY."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import pandas as pd

from live_ledger import assert_no_uncommitted_ledger, atomic_write_json
from tw_share_lots import BOARD_LOT


class UncommittedLedgerTests(unittest.TestCase):
    def test_fills_after_last_date_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            pd.DataFrame(
                [
                    {
                        "fill_id": "o1",
                        "fill_date": "2026-09-16",
                        "signal_date": "2026-09-15",
                        "code": "0050",
                        "side": "BUY",
                        "quantity": BOARD_LOT,
                    }
                ]
            ).to_csv(sdir / "fills.csv", index=False)
            with self.assertRaises(SystemExit) as ctx:
                assert_no_uncommitted_ledger(sdir, "2026-09-15")
            self.assertIn("Uncommitted fills", str(ctx.exception))

    def test_committed_ok(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            pd.DataFrame(
                [
                    {
                        "fill_id": "o1",
                        "fill_date": "2026-09-15",
                        "signal_date": "2026-09-14",
                        "code": "0050",
                        "side": "BUY",
                        "quantity": BOARD_LOT,
                    }
                ]
            ).to_csv(sdir / "fills.csv", index=False)
            assert_no_uncommitted_ledger(sdir, "2026-09-15")

    def test_orders_after_last_date_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            pd.DataFrame(
                [
                    {
                        "order_id": "ord1",
                        "signal_date": "2026-09-16",
                        "code": "0050",
                        "side": "BUY",
                        "quantity": BOARD_LOT,
                    }
                ]
            ).to_csv(sdir / "orders.csv", index=False)
            with self.assertRaises(SystemExit) as ctx:
                assert_no_uncommitted_ledger(sdir, "2026-09-15")
            self.assertIn("Uncommitted orders", str(ctx.exception))

    def test_nav_after_last_date_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            pd.DataFrame(
                [{"date": "2026-09-16", "nav": 1.0, "cash": 1.0}]
            ).to_csv(sdir / "nav.csv", index=False)
            with self.assertRaises(SystemExit) as ctx:
                assert_no_uncommitted_ledger(sdir, "2026-09-15")
            self.assertIn("Uncommitted nav", str(ctx.exception))

    def test_atomic_write_json(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "state.json"
            atomic_write_json(path, {"a": 1})
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["a"], 1)


class ForwardWorkflowAllowFlags(unittest.TestCase):
    def test_workflow_has_live_allow_flags(self) -> None:
        root = Path(__file__).resolve().parents[1]
        yml = (root / ".github/workflows/v412f-forward-paper.yml").read_text(encoding="utf-8")
        self.assertIn("--allow-live-market-overwrite", yml)
        self.assertIn("--allow-live-tree-out", yml)
        self.assertIn("--out-dir forward/e21", yml)
        self.assertIn("last_date", yml)

    def test_pipeline_tax_versions_removed_from_choices(self) -> None:
        import e21_forward_pipeline as pipe

        src = Path(pipe.__file__).read_text(encoding="utf-8")
        choices = src.split("choices=[", 1)[1].split("]", 1)[0]
        self.assertNotIn("E22_V3_TAX10", choices)
        self.assertNotIn("E22_V3_TAX20", choices)
        self.assertNotIn("RECV_PAY_TAX", choices)
        self.assertIn("E22_V3_RECV_PAY,", choices)
        self.assertIn("confirm_e22_version_override", src)


class BuildMarketPathGateTests(unittest.TestCase):
    def test_refuses_canonical_live_market(self) -> None:
        import e21_build_market as bm

        with mock.patch(
            "sys.argv",
            [
                "e21_build_market.py",
                "--financial-raw",
                "x",
                "--financial-adjusted",
                "x",
                "--telecom-0050-raw",
                "x",
                "--telecom-adjusted",
                "x",
                "--etf0050-adjusted",
                "x",
                "--taiex",
                "x",
                "--out",
                "forward/e21/live_market.csv",
            ],
        ):
            with self.assertRaises(SystemExit) as ctx:
                bm.main()
            self.assertIn("Refusing to overwrite canonical live market", str(ctx.exception))


class T2EstimatePathGateTests(unittest.TestCase):
    def test_refuses_live_tree_out(self) -> None:
        import twse_t2_settlement_estimate as est

        with tempfile.TemporaryDirectory() as td:
            # Point ROOT at temp so live_tree check uses test paths via patch
            live = Path(td) / "forward" / "e21"
            live.mkdir(parents=True)
            with mock.patch.object(est, "ROOT", Path(td)):
                with mock.patch(
                    "sys.argv",
                    [
                        "twse_t2_settlement_estimate.py",
                        "--state-dir",
                        str(live),
                        "--out-dir",
                        str(live),
                        "--asof",
                        "2026-09-15",
                    ],
                ):
                    with mock.patch.object(
                        est,
                        "run_estimate",
                        return_value=([], {"asof": "2026-09-15", "n_fills": 0}),
                    ):
                        with self.assertRaises(SystemExit) as ctx:
                            est.main()
                        self.assertIn("Refusing to write T+2 estimate", str(ctx.exception))


class PaperSellBeforeBuyTests(unittest.TestCase):
    def test_iter_pending_sells_first(self) -> None:
        from live_execution import _iter_pending

        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            pd.DataFrame(
                [
                    {
                        "order_id": "b1",
                        "signal_date": "2026-09-14",
                        "code": "0050",
                        "side": "BUY",
                        "quantity": BOARD_LOT,
                    },
                    {
                        "order_id": "s1",
                        "signal_date": "2026-09-14",
                        "code": "2880",
                        "side": "SELL",
                        "quantity": BOARD_LOT,
                    },
                ]
            ).to_csv(sdir / "orders.csv", index=False)
            pending = _iter_pending(sdir, pd.Timestamp("2026-09-15"))
            sides = list(pending["side"])
            self.assertEqual(sides[0], "SELL")
            self.assertEqual(sides[1], "BUY")


if __name__ == "__main__":
    unittest.main()
