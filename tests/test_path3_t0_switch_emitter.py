#!/usr/bin/env python3
"""Guards for Path3 T0 switch order emitter PREP (flag OFF)."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import pandas as pd

from live_config import LIVE, LIVE_T0_CARVE_FIN_SAT_SWITCH_EMIT
from live_fill_core import PaperOpenFillPort
from live_path3_t0_switch_emitter import (
    ACCEPT_EMIT_LINE,
    BOOK_COMP,
    BOOK_SAT,
    build_sat_lead_signal,
    build_tagged_switch_order_rows,
    is_emit_authorized,
    make_path3_switch_order_id,
    maybe_emit_switch_orders,
    propose_switch_ledger,
    switch_meta_for_asof,
)
from t0_carve_fin_sat_switch import CARVE_OUT_ID, authorize_same_bar_fill


class Path3EmitterFlagDefaultOff(unittest.TestCase):
    def test_live_emit_flag_default_false(self) -> None:
        self.assertFalse(LIVE.live_t0_carve_fin_sat_switch_emit)
        self.assertFalse(LIVE_T0_CARVE_FIN_SAT_SWITCH_EMIT)
        self.assertFalse(is_emit_authorized())

    def test_accept_emit_line_mentions_carve(self) -> None:
        self.assertIn(CARVE_OUT_ID, ACCEPT_EMIT_LINE)
        self.assertIn("emitter", ACCEPT_EMIT_LINE.lower())


class Path3EmitterOrderBuilder(unittest.TestCase):
    def test_tagged_rows_have_carve_and_distinct_oid(self) -> None:
        rows, meta = build_tagged_switch_order_rows(
            signal_date="2026-09-24",
            delta_shares={"0050": 2000, "2881": -1500},
            prices={"0050": 100.0, "2881": 50.0},
        )
        self.assertEqual(meta["n_orders"], 2)
        self.assertEqual({r["carve_out_id"] for r in rows}, {CARVE_OUT_ID})
        self.assertTrue(all(authorize_same_bar_fill(r, authorized=True) for r in rows))
        self.assertTrue(all(str(r["order_id"]).endswith("-P3T0") for r in rows))
        # SELL before BUY
        self.assertEqual(rows[0]["side"], "SELL")
        self.assertEqual(rows[1]["side"], "BUY")

    def test_order_id_distinct_from_soft_frozen(self) -> None:
        oid = make_path3_switch_order_id(
            signal_date="2026-09-24", code="0050", side="BUY"
        )
        self.assertEqual(oid, "2026-09-24-0050-BUY-P3T0")

    def test_maybe_emit_fail_closed_without_deltas(self) -> None:
        sig = pd.DataFrame(
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
        rows, meta = maybe_emit_switch_orders(
            asof="2026-09-24",
            prices={"0050": 100.0},
            delta_shares=None,
            authorized=True,
            signal=sig,
        )
        self.assertEqual(rows, [])
        self.assertEqual(meta["reason"], "weight_engine_not_wired")

    def test_maybe_emit_off_flag(self) -> None:
        rows, meta = maybe_emit_switch_orders(
            asof="2026-09-24",
            prices={"0050": 100.0},
            delta_shares={"0050": 1000},
            authorized=False,
        )
        self.assertEqual(rows, [])
        self.assertEqual(meta["reason"], "emit_flag_off")

    def test_maybe_emit_on_flip_with_deltas(self) -> None:
        sig = pd.DataFrame(
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
        rows, meta = maybe_emit_switch_orders(
            asof="2026-09-24",
            prices={"0050": 100.0},
            delta_shares={"0050": 1000},
            authorized=True,
            signal=sig,
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(meta["reason"], "emitted")
        self.assertEqual(rows[0]["carve_out_id"], CARVE_OUT_ID)
        self.assertEqual(rows[0]["code"], "0050")

    def test_paper_fill_same_bar_when_fill_auth(self) -> None:
        rows, _ = build_tagged_switch_order_rows(
            signal_date="2026-09-24",
            delta_shares={"0050": 1000},
            prices={"0050": 120.0},
        )
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            pd.DataFrame(rows).to_csv(sdir / "orders.csv", index=False)
            port = PaperOpenFillPort()
            with mock.patch(
                "live_fill_core.is_live_fill_authorized", return_value=True
            ):
                _pos, _cash, fills, _same, ok = port.fill_pending(
                    state_dir=sdir,
                    latest=pd.Timestamp("2026-09-24"),
                    open_prices={"0050": 100.0},
                    pos={},
                    cash=1_000_000.0,
                )
            self.assertTrue(ok)
            self.assertEqual(len(fills), 1)
            self.assertEqual(fills[0]["carve_out_id"], CARVE_OUT_ID)
            self.assertEqual(fills[0]["fill_policy"], "T0_CARVE_MOC_REF_CLOSE")
            self.assertGreater(float(fills[0]["fill_price"]), 115.0)


class Path3EmitterSignal(unittest.TestCase):
    def test_build_signal_and_propose(self) -> None:
        import numpy as np

        dates = pd.date_range("2020-01-02", periods=80, freq="B")
        comp = pd.DataFrame(
            {"date": dates, "nav": 1.0 + 0.001 * np.arange(len(dates), dtype=float)}
        )
        sat_nav = 1.0 + 0.001 * np.arange(len(dates), dtype=float)
        sat_nav[-10:] = sat_nav[-11] * (0.99 ** np.arange(1, 11))
        sat = pd.DataFrame({"date": dates, "nav": sat_nav})
        sig = build_sat_lead_signal(comp, sat, theta=0.01)
        self.assertIn("flip", sig.columns)
        self.assertIn("book", sig.columns)
        ledger = propose_switch_ledger(sig)
        self.assertGreaterEqual(len(ledger), 0)
        meta = switch_meta_for_asof(dates[-1], signal=sig)
        self.assertTrue(meta["ok"])


if __name__ == "__main__":
    unittest.main()
