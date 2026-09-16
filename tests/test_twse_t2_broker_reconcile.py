#!/usr/bin/env python3
"""Tests for R5 T+2 broker/custody reconcile pack."""
from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path

from twse_t2_broker_reconcile import reconcile, write_pack


class ReconcileTests(unittest.TestCase):
    def test_fill_id_match(self) -> None:
        est = [
            {
                "fill_id": "o1",
                "settle_date": "2026-07-13",
                "settlement_cash": -100085.5,
            }
        ]
        cust = [
            {
                "fill_id": "o1",
                "settle_date": "2026-07-13",
                "settlement_cash": -100085.5,
            }
        ]
        pack = reconcile(est, cust, asof=date(2026, 7, 13))
        self.assertTrue(pack["all_ok"])
        self.assertEqual(pack["n_matched_ok"], 1)

    def test_mismatch(self) -> None:
        est = [{"fill_id": "o1", "settle_date": "2026-07-13", "settlement_cash": -100.0}]
        cust = [{"fill_id": "o1", "settle_date": "2026-07-13", "settlement_cash": -90.0}]
        pack = reconcile(est, cust, asof=date(2026, 7, 13), tol=1.0)
        self.assertFalse(pack["all_ok"])
        self.assertEqual(pack["n_mismatches"], 1)

    def test_aggregate_by_date(self) -> None:
        est = [
            {"settle_date": "2026-07-13", "settlement_cash": -50.0},
            {"settle_date": "2026-07-13", "settlement_cash": -50.0},
        ]
        cust = [{"settle_date": "2026-07-13", "settlement_cash_net": -100.0}]
        pack = reconcile(est, cust, asof=date(2026, 7, 13))
        self.assertTrue(pack["all_ok"])

    def test_write_pack(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = write_pack(
                reconcile([], [], asof=date(2026, 7, 13)),
                Path(td),
            )
            self.assertTrue(path.exists())
            self.assertTrue((Path(td) / "t2_broker_reconcile_latest.json").exists())


if __name__ == "__main__":
    unittest.main()
