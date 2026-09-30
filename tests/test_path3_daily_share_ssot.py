#!/usr/bin/env python3
"""Guards for Path3 COMP/SAT daily share SSOT (0kab)."""
from __future__ import annotations

import unittest

import pandas as pd

from path3_comp_sat_daily_share_ssot import (
    ENGINE_ID,
    dollar_mix,
    plan_delta_ledger_scaled,
    plan_delta_shares_ledger,
    shares_asof_detail,
    shares_panel_from_long,
)


def _live_pos() -> dict[str, float]:
    return {
        "2880": 2_700_000.0,
        "2886": 2_200_000.0,
        "2892": 3_100_000.0,
        "5880": 4_200_000.0,
        "2412": 80_000.0,
        "3045": 100_000.0,
        "4904": 110_000.0,
        "0050": 300_000.0,
    }


def _prices() -> dict[str, float]:
    return {
        "2880": 45.0,
        "2886": 50.0,
        "2892": 40.0,
        "5880": 26.0,
        "2412": 145.0,
        "3045": 120.0,
        "4904": 105.0,
        "0050": 110.0,
    }


def _fin_heavy_ledger() -> dict[str, float]:
    return {
        "2880": 5_000_000.0,
        "2886": 500_000.0,
        "2892": 500_000.0,
        "5880": 500_000.0,
        "2412": 100_000.0,
        "3045": 100_000.0,
        "4904": 100_000.0,
        "0050": 200_000.0,
    }


class LedgerScaledRecon(unittest.TestCase):
    def test_scale_mix_produces_fin_delta(self) -> None:
        delta, meta = plan_delta_ledger_scaled(
            live_pos=_live_pos(),
            prices=_prices(),
            ledger_shares=_fin_heavy_ledger(),
            keep_0050=True,
        )
        self.assertEqual(meta["engine_id"], ENGINE_ID)
        self.assertGreater(meta["n_delta_names"], 0)
        self.assertNotIn("0050", delta)
        self.assertIn("2880", meta["fin_mix"])
        self.assertGreater(meta["fin_mix"]["2880"], 0.4)
        self.assertFalse(meta["equal_fallback"])

    def test_empty_mix_fail_closed_keeps_live(self) -> None:
        # Ledger has FIN names but prices missing → mix empty → keep live (no equal recon)
        ledger = {"2880": 1_000_000.0, "2886": 1_000_000.0, "2412": 50_000.0}
        prices = {"2412": 145.0, "0050": 110.0}  # no FIN prices
        live = {"2880": 1000.0, "2886": 2000.0, "2412": 100.0, "0050": 50.0}
        delta, meta = plan_delta_ledger_scaled(
            live_pos=live, prices=prices, ledger_shares=ledger, keep_0050=True
        )
        self.assertTrue(meta["fin_mix_empty"])
        self.assertFalse(meta["equal_fallback"])
        self.assertNotIn("2880", delta)
        self.assertNotIn("2886", delta)

    def test_empty_mix_equal_fallback_opt_in(self) -> None:
        ledger = {"2880": 1_000_000.0, "2886": 1_000_000.0}
        prices = {"2412": 145.0}  # no FIN prices → mix empty
        live = {"2880": 1000.0, "2886": 2000.0, "2412": 100.0}
        delta, meta = plan_delta_ledger_scaled(
            live_pos=live,
            prices=prices,
            ledger_shares=ledger,
            keep_0050=True,
            allow_equal_fallback=True,
        )
        self.assertTrue(meta["fin_mix_empty"])
        self.assertTrue(meta["equal_fallback"])

    def test_panel_from_long(self) -> None:
        df = pd.DataFrame(
            [
                {"date": "2026-01-02", "code": "2880", "shares": 1000},
                {"date": "2026-01-02", "code": "2886", "shares": 2000},
                {"date": "2026-01-03", "code": "2880", "shares": 1500},
            ]
        )
        pan = shares_panel_from_long(df)
        self.assertEqual(len(pan), 2)
        self.assertEqual(float(pan.loc[pd.Timestamp("2026-01-03"), "2880"]), 1500.0)

    def test_dollar_mix_sums_one(self) -> None:
        mix = dollar_mix(
            {"2880": 1000, "2886": 1000},
            {"2880": 40.0, "2886": 60.0},
            ["2880", "2886"],
        )
        self.assertAlmostEqual(sum(mix.values()), 1.0, places=6)


class SharesAsofDetail(unittest.TestCase):
    def test_returns_ledger_asof_and_panel_end(self) -> None:
        pan = shares_panel_from_long(
            pd.DataFrame(
                [
                    {"date": "2026-09-20", "code": "2880", "shares": 1000},
                    {"date": "2026-09-24", "code": "2880", "shares": 1500},
                ]
            )
        )
        shares, led_asof, panel_end = shares_asof_detail(
            "COMP_H150_x_A20", "2026-09-29", panel=pan
        )
        self.assertEqual(shares.get("2880"), 1500.0)
        self.assertEqual(led_asof, pd.Timestamp("2026-09-24"))
        self.assertEqual(panel_end, pd.Timestamp("2026-09-24"))


class PlanDeltaSharesLedgerStale(unittest.TestCase):
    def _panels(self) -> dict[str, pd.DataFrame]:
        pan = shares_panel_from_long(
            pd.DataFrame(
                [
                    {"date": "2026-09-24", "code": "2880", "shares": 5_000_000},
                    {"date": "2026-09-24", "code": "2886", "shares": 500_000},
                    {"date": "2026-09-24", "code": "2892", "shares": 500_000},
                    {"date": "2026-09-24", "code": "5880", "shares": 500_000},
                    {"date": "2026-09-24", "code": "2412", "shares": 100_000},
                    {"date": "2026-09-24", "code": "3045", "shares": 100_000},
                    {"date": "2026-09-24", "code": "4904", "shares": 100_000},
                    {"date": "2026-09-24", "code": "0050", "shares": 200_000},
                ]
            )
        )
        return {"SAT_A20_RELAX": pan, "COMP_H150_x_A20": pan}

    def test_stale_asof_fail_closed(self) -> None:
        delta, meta = plan_delta_shares_ledger(
            asof="2026-09-29",
            dest_book="SAT_A20_RELAX",
            live_pos=_live_pos(),
            prices=_prices(),
            panels=self._panels(),
            max_stale_calendar_days=0,
        )
        self.assertIsNone(delta)
        self.assertEqual(meta["reason"], "ledger_stale")
        self.assertTrue(meta["ledger_stale"])
        self.assertEqual(meta["ledger_asof"], "2026-09-24")
        self.assertEqual(meta["ledger_lag_calendar_days"], 5)

    def test_same_day_asof_ok(self) -> None:
        delta, meta = plan_delta_shares_ledger(
            asof="2026-09-24",
            dest_book="SAT_A20_RELAX",
            live_pos=_live_pos(),
            prices=_prices(),
            panels=self._panels(),
            max_stale_calendar_days=0,
        )
        self.assertIsNotNone(delta)
        self.assertFalse(meta.get("ledger_stale", True))
        self.assertEqual(meta["ledger_asof"], "2026-09-24")
        self.assertEqual(meta["reason"], "ledger_scaled_recon")
        self.assertGreater(meta["n_delta_names"], 0)


if __name__ == "__main__":
    unittest.main()
