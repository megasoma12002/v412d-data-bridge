#!/usr/bin/env python3
"""Engineering P0–P2 opt guards (cache, batch append, sleeve gap, tip stamps)."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd

import e16_soft_frozen_base as soft
import e22_dividend_accounting as e22div
import live_day_commit as day
import live_dh_fuse_cutover as fuse
import live_ledger as ledger
from sleeve_gap_trade import (
    SLEEVE_GAP_TRIGGER,
    sleeve_trade_from_gap,
    sleeve_trade_vector,
)
from stagea_screen_helpers import pack_nav_windows, tip_hygiene, utc_now_z


class AppendImmutableManyTests(unittest.TestCase):
    def test_batch_first_key_wins(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "rows.csv"
            n = ledger.append_immutable_many(
                p,
                [
                    {"id": "a", "v": 1},
                    {"id": "a", "v": 99},
                    {"id": "b", "v": 2},
                ],
                "id",
            )
            self.assertEqual(n, 2)
            df = pd.read_csv(p)
            self.assertEqual(list(df["id"]), ["a", "b"])
            self.assertEqual(int(df.loc[0, "v"]), 1)
            n2 = ledger.append_immutable_many(
                p, [{"id": "a", "v": 3}, {"id": "c", "v": 4}], "id"
            )
            self.assertEqual(n2, 1)
            df2 = pd.read_csv(p)
            self.assertEqual(list(df2["id"]), ["a", "b", "c"])
            self.assertEqual(int(df2.loc[0, "v"]), 1)

    def test_single_delegates(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "one.csv"
            self.assertTrue(ledger.append_immutable(p, {"id": "x", "v": 1}, "id"))
            self.assertFalse(ledger.append_immutable(p, {"id": "x", "v": 2}, "id"))


class SleeveGapTradeTests(unittest.TestCase):
    def test_live_helper_matches_vector(self) -> None:
        pre = {"Financial": 0.70, "Telecom": 0.15, "0050": 0.15}
        tgt = {"Financial": 0.60, "Telecom": 0.20, "0050": 0.20}
        trade, l1 = sleeve_trade_from_gap(pre, tgt)
        self.assertGreater(l1, 0.0)
        gap = {k: tgt[k] - pre[k] for k in pre}
        vec = sleeve_trade_vector(gap, ["Financial", "Telecom", "0050"])
        for i, k in enumerate(["Financial", "Telecom", "0050"]):
            self.assertAlmostEqual(trade[k], float(vec[i]), places=12)

    def test_below_trigger_zero(self) -> None:
        pre = {"Financial": 0.70, "Telecom": 0.15, "0050": 0.15}
        tgt = {
            "Financial": 0.70 + SLEEVE_GAP_TRIGGER * 0.5,
            "Telecom": 0.15,
            "0050": 0.15 - SLEEVE_GAP_TRIGGER * 0.5,
        }
        trade, _ = sleeve_trade_from_gap(pre, tgt)
        self.assertTrue(all(abs(v) < 1e-15 for v in trade.values()))

    def test_not_confused_with_rebalance_l1(self) -> None:
        self.assertNotAlmostEqual(SLEEVE_GAP_TRIGGER, soft.REBALANCE_L1_MIN)


class DividendFrameParityTests(unittest.TestCase):
    def test_frame_matches_csv(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "div.csv"
            p.write_text(
                "code,cash_dividend,stock_dividend,cash_ex_date,stock_ex_date,"
                "cash_payment_date,stock_payment_date\n"
                "2880,1.5,0,2024-06-01,,2024-07-01,\n"
                "2412,0,1.0,,2024-08-01,,2024-09-01\n",
                encoding="utf-8",
            )
            from_csv = e22div.load_dividend_events(p)
            df = pd.read_csv(p, dtype={"code": str})
            from_df = e22div.dividend_events_from_frame(df)
            self.assertEqual(len(from_csv), len(from_df))
            for a, b in zip(from_csv, from_df):
                self.assertEqual(a, b)


class SoftFrozenHooksTests(unittest.TestCase):
    def test_default_identical_to_override_none(self) -> None:
        # Tiny synthetic panel — identity of kwargs path
        dates = pd.bdate_range("2020-01-02", periods=300)
        rows = []
        for d in dates:
            for code, px in (
                ("2880", 20.0),
                ("2886", 21.0),
                ("2892", 22.0),
                ("5880", 23.0),
                ("2412", 100.0),
                ("3045", 101.0),
                ("4904", 102.0),
                ("0050", 50.0),
                ("TAIEX", 15000.0),
            ):
                rows.append(
                    {
                        "date": d,
                        "code": code,
                        "adj_close": px,
                        "close": px,
                        "open": px,
                    }
                )
        m = pd.DataFrame(rows)
        _p1, s1, t1, r1, sc1 = soft.build_soft_frozen_targets(m)
        _p2, s2, t2, r2, sc2 = soft.build_soft_frozen_targets(
            m, regime_priors=None, score_weights=None, rebalance_l1_min=None
        )
        pd.testing.assert_frame_equal(t1, t2)
        pd.testing.assert_series_equal(r1, r2)
        pd.testing.assert_frame_equal(sc1, sc2)
        pd.testing.assert_frame_equal(s1, s2)


class ClipFlipStampTests(unittest.TestCase):
    def test_portfolio_state_stamp_is_beta_not_finband(self) -> None:
        payload = day.build_portfolio_state_payload(
            cash=1.0,
            pos={},
            receivables={},
            latest_iso="2026-09-26",
            nav=1.0,
            e22_version="E22_v3_recv_pay_effdelay",
            skip=set(),
        )
        self.assertEqual(payload["soft_frozen_clip_flip"], soft.SOFT_FROZEN_CLIP_FLIP_STAMP)
        self.assertIn("BETA", payload["soft_frozen_clip_flip"])
        self.assertNotIn("FINBAND", payload["soft_frozen_clip_flip"])


class FuseOffenseCacheTests(unittest.TestCase):
    def test_second_call_hits_cache(self) -> None:
        fuse.clear_fuse_offense_cache()
        m = pd.DataFrame({"date": ["2020-01-02"], "code": ["0050"], "close": [1.0]})
        d = pd.DataFrame()
        fake_nav = pd.DataFrame({"date": ["2020-01-02"], "nav": [1.0]})
        fake_meta = {"fuse_id": "TEST"}
        with mock.patch.object(
            fuse,
            "build_fuse_offense_sim",
            return_value=(fake_nav, pd.DataFrame(), dict(fake_meta)),
        ) as sim:
            n1, m1 = fuse.build_fuse_offense_nav(m, d)
            n2, m2 = fuse.build_fuse_offense_nav(m, d)
            self.assertEqual(sim.call_count, 1)
            self.assertFalse(m1.get("fuse_offense_cache_hit"))
            self.assertTrue(m2.get("fuse_offense_cache_hit"))
            pd.testing.assert_frame_equal(n1, n2)
        fuse.clear_fuse_offense_cache()


class StageAHelpersTests(unittest.TestCase):
    def test_utc_and_pack_smoke(self) -> None:
        self.assertTrue(utc_now_z().endswith("Z"))
        nav = pd.DataFrame(
            {
                "date": pd.bdate_range("2023-01-03", periods=40),
                "nav": np.linspace(1.0, 1.1, 40),
            }
        )
        pack = pack_nav_windows(nav)
        self.assertIn("heldout_2019_plus", pack)
        tip = tip_hygiene(nav, nav)
        self.assertIn("ytd", tip)


class CommitExcelOptionalTests(unittest.TestCase):
    def test_skip_excel(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            day.commit_day_books(
                state_dir=sdir,
                fill_port_name="dry_run",
                fills=[],
                pending_div_rows=[],
                div_path=sdir / "dividends_applied.csv",
                state_path=sdir / "portfolio_state.json",
                state_payload={"cash": 1.0, "last_date": "2026-01-02"},
                signal={"date": "2026-01-02", "x": 1},
                navrow={"date": "2026-01-02", "nav": 1.0},
                order_rows=[],
                applied_details=[],
                asof_iso="2026-01-02",
                write_excel_dashboard=False,
            )
            self.assertFalse((sdir / "E21_forward_dashboard.xlsx").exists())
            self.assertTrue((sdir / "signals.csv").exists())


if __name__ == "__main__":
    unittest.main()
