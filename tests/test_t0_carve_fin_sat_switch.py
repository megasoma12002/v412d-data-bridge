#!/usr/bin/env python3
"""Guards for named T0_CARVE_FIN_SAT_SWITCH same-bar fill allowlist."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import pandas as pd

from live_config import LIVE, LIVE_T0_CARVE_FIN_SAT_SWITCH_FILL
from live_fill_core import PaperOpenFillPort, _exact_t1_stats, _iter_pending
from t0_carve_fin_sat_switch import (
    ACCEPT_FILL_LINE,
    CARVE_OUT_ID,
    authorize_same_bar_fill,
    is_live_fill_authorized,
    tag_order,
)


class T0CarveFlagDefaultOff(unittest.TestCase):
    def test_live_flag_on_after_accept(self) -> None:
        self.assertTrue(LIVE.live_t0_carve_fin_sat_switch_fill)
        self.assertTrue(LIVE_T0_CARVE_FIN_SAT_SWITCH_FILL)
        self.assertTrue(is_live_fill_authorized())
        self.assertIn("ACCEPT Live fill carve-out", LIVE.live_t0_carve_fin_sat_switch_ballot)

    def test_untagged_same_bar_still_fails(self) -> None:
        same, ok = _exact_t1_stats(
            [{"signal_date": "2026-09-24", "fill_date": "2026-09-24"}],
            carve_authorized=False,
        )
        self.assertEqual(same, 1)
        self.assertFalse(ok)

    def test_tagged_same_bar_ok_only_when_authorized(self) -> None:
        fill = {
            "signal_date": "2026-09-24",
            "fill_date": "2026-09-24",
            "carve_out_id": CARVE_OUT_ID,
        }
        same_off, ok_off = _exact_t1_stats([fill], carve_authorized=False)
        self.assertEqual(same_off, 1)
        self.assertFalse(ok_off)
        same_on, ok_on = _exact_t1_stats([fill], carve_authorized=True)
        self.assertEqual(same_on, 0)
        self.assertTrue(ok_on)

    def test_tag_order_sets_id(self) -> None:
        row = tag_order({"order_id": "x", "code": "0050", "side": "BUY"})
        self.assertEqual(row["carve_out_id"], CARVE_OUT_ID)
        self.assertTrue(authorize_same_bar_fill(row, authorized=True))
        self.assertFalse(authorize_same_bar_fill(row, authorized=False))


class T0CarvePendingFilter(unittest.TestCase):
    def test_same_day_tagged_pending_only_when_auth(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            pd.DataFrame(
                [
                    {
                        "order_id": "o1",
                        "signal_date": "2026-09-24",
                        "code": "0050",
                        "side": "BUY",
                        "quantity": 1000,
                        "reference_close": 100.0,
                        "carve_out_id": CARVE_OUT_ID,
                    },
                    {
                        "order_id": "o2",
                        "signal_date": "2026-09-23",
                        "code": "0050",
                        "side": "BUY",
                        "quantity": 1000,
                        "reference_close": 99.0,
                    },
                ]
            ).to_csv(sdir / "orders.csv", index=False)
            latest = pd.Timestamp("2026-09-24")
            off = _iter_pending(sdir, latest, carve_authorized=False)
            self.assertEqual(set(off.order_id.astype(str)), {"o2"})
            on = _iter_pending(sdir, latest, carve_authorized=True)
            self.assertEqual(set(on.order_id.astype(str)), {"o1", "o2"})

    def test_paper_port_fills_carve_moc_when_auth(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            sdir = Path(td)
            pd.DataFrame(
                [
                    {
                        "order_id": "c1",
                        "signal_date": "2026-09-24",
                        "code": "0050",
                        "side": "BUY",
                        "quantity": 1000,
                        "reference_close": 120.0,
                        "carve_out_id": CARVE_OUT_ID,
                    }
                ]
            ).to_csv(sdir / "orders.csv", index=False)
            port = PaperOpenFillPort()
            with mock.patch(
                "live_fill_core.is_live_fill_authorized", return_value=True
            ):
                pos, cash, fills, same, ok = port.fill_pending(
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
            # MOC uses reference_close 120, not open 100
            self.assertGreater(float(fills[0]["fill_price"]), 115.0)


class T0CarveAcceptLineDocumented(unittest.TestCase):
    def test_accept_line_mentions_carve_id(self) -> None:
        self.assertIn(CARVE_OUT_ID, ACCEPT_FILL_LINE)
        self.assertIn("same-bar", ACCEPT_FILL_LINE)


if __name__ == "__main__":
    unittest.main()
