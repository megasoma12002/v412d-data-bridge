#!/usr/bin/env python3
"""Unit tests for live modularization (config / ledger / fill core / month-end)."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

import e21_forward_pipeline as e21
import live_config as lc
import live_execution as lex
import live_fill_core as fill_core
import live_ledger as ledger
from ops_dual_paper_month_end import DualPaperMonitorSpec, run_monitor


class LiveConfigTests(unittest.TestCase):
    def test_live_flags_match_pipeline_exports(self) -> None:
        self.assertEqual(e21.LIVE_FUSE_ADDITIVE, lc.LIVE.live_fuse_additive)
        self.assertEqual(e21.LIVE_DH_EXPOSURE, lc.LIVE.live_dh_exposure)
        self.assertFalse(e21.LIVE_E45_STITCH)
        self.assertEqual(e21.KD_OPT["id"], lc.KD_OPT["id"])
        self.assertEqual(e21.E22_BOOKS_VERSION, lc.E22_BOOKS_VERSION)
        self.assertEqual(lc.LIVE.fill_port, "paper")

    def test_append_immutable(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "rows.csv"
            self.assertTrue(ledger.append_immutable(p, {"id": "a", "v": 1}, "id"))
            self.assertFalse(ledger.append_immutable(p, {"id": "a", "v": 2}, "id"))
            self.assertTrue(ledger.append_immutable(p, {"id": "b", "v": 3}, "id"))
            df = pd.read_csv(p)
            self.assertEqual(list(df["id"]), ["a", "b"])
            self.assertEqual(int(df.loc[0, "v"]), 1)


class FillCoreModularizeTests(unittest.TestCase):
    def test_facade_reexports_fill_ports(self) -> None:
        self.assertIs(lex.PaperOpenFillPort, fill_core.PaperOpenFillPort)
        self.assertIs(lex.DryRunFillPort, fill_core.DryRunFillPort)
        self.assertEqual(lex.resolve_fill_port("paper").name, "paper")

    def test_sort_rows_sell_before_buy(self) -> None:
        rows = [
            {"side": "BUY", "code": "2880"},
            {"side": "SELL", "code": "0050"},
            {"side": "BUY", "code": "2412"},
        ]
        out = fill_core.sort_rows_sell_before_buy(rows)
        self.assertEqual([r["side"] for r in out], ["SELL", "BUY", "BUY"])
        self.assertEqual(out[0]["code"], "0050")

    def test_sort_pending_dataframe_sell_before_buy(self) -> None:
        df = pd.DataFrame(
            [
                {"signal_date": "2026-01-02", "side": "BUY", "code": "2880"},
                {"signal_date": "2026-01-02", "side": "SELL", "code": "0050"},
            ]
        )
        out = fill_core.sort_pending_sell_before_buy(df)
        self.assertEqual(list(out["side"]), ["SELL", "BUY"])


class PipelineThinTests(unittest.TestCase):
    def test_pipeline_delegates_to_extracted_modules(self) -> None:
        src = Path(e21.__file__).read_text(encoding="utf-8")
        for needle in (
            "live_session_io",
            "live_e22_day",
            "live_rebalance_orders",
            "live_day_commit",
            "fill_pending_at_open",
        ):
            self.assertIn(needle, src)
        # Day-commit / Excel / path gates should not be inlined in the thin CLI.
        self.assertNotIn("audit_chain.jsonl", src)
        self.assertNotIn("cannot silently rewind", src)


class MonthEndRunnerTests(unittest.TestCase):
    def test_run_monitor_from_compare_csv(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            compare = tmp / "dual_paper_nav_compare.csv"
            dates = pd.date_range("2024-01-01", periods=10, freq="B")
            pd.DataFrame(
                {
                    "date": dates,
                    "nav_base": [1.0 + 0.01 * i for i in range(10)],
                    "nav_chal": [1.0 + 0.012 * i for i in range(10)],
                }
            ).to_csv(compare, index=False)
            out = tmp / "month_end"
            art = tmp / "ops"
            spec = DualPaperMonitorSpec(
                label="TEST_MONITOR",
                ops_stem="TEST_MONITOR_ARCH",
                artifact_dir=art,
                base_id="BASE",
                chal_id="CHAL",
                default_out=out,
                base_nav=tmp / "missing_base.csv",
                chal_nav=tmp / "missing_chal.csv",
                compare_nav=compare,
                ledger_hint="n/a",
            )
            summary = run_monitor(spec, asof="2024-01-12")
            self.assertGreaterEqual(summary["n_windows"], 1)
            self.assertTrue((out / "month_end_monitor.json").exists())
            self.assertTrue((art / "TEST_MONITOR_ARCH.json").exists())
            payload = json.loads((out / "month_end_monitor.json").read_text())
            self.assertEqual(payload["base_id"], "BASE")
            self.assertFalse(payload["live_wire"])


if __name__ == "__main__":
    unittest.main()
