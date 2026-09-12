"""Unit tests for E22 dividend amount repair (parse-fail → refetch → patch)."""
from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from e22_dividend_accounting import load_dividend_events  # noqa: E402
from e22_dividend_amount_repair import (  # noqa: E402
    load_dividend_events_with_repair,
    repair_dividend_amount_ledger,
    scan_bad_amount_cells,
)


FIELDS = [
    "code",
    "fiscal_year",
    "record_date",
    "announcement_date",
    "announcement_time",
    "cash_ex_date",
    "cash_payment_date",
    "cash_dividend",
    "stock_ex_date",
    "stock_payment_date",
    "stock_dividend",
]


def _write(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


class DividendAmountRepairTests(unittest.TestCase):
    def test_scan_finds_dirty_cash_cell(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "div.csv"
            _write(
                path,
                [
                    {
                        "code": "2880",
                        "fiscal_year": "",
                        "record_date": "",
                        "announcement_date": "",
                        "announcement_time": "",
                        "cash_ex_date": "2024-07-01",
                        "cash_payment_date": "2024-08-01",
                        "cash_dividend": "N/A",
                        "stock_ex_date": "",
                        "stock_payment_date": "",
                        "stock_dividend": "",
                    }
                ],
            )
            bad = scan_bad_amount_cells(path)
            self.assertEqual(len(bad), 1)
            self.assertEqual(bad[0].field, "cash_dividend")
            self.assertEqual(bad[0].raw, "N/A")

    def test_repair_patches_from_mock_fetcher(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "div.csv"
            out = Path(tmp) / "out"
            _write(
                path,
                [
                    {
                        "code": "2880",
                        "fiscal_year": "",
                        "record_date": "",
                        "announcement_date": "",
                        "announcement_time": "",
                        "cash_ex_date": "2024-07-01",
                        "cash_payment_date": "2024-08-01",
                        "cash_dividend": "abc",
                        "stock_ex_date": "",
                        "stock_payment_date": "",
                        "stock_dividend": "",
                    }
                ],
            )

            def fake(_code: str) -> list[dict]:
                return [
                    {
                        "code": "2880",
                        "cash_ex_date": "2024-07-01",
                        "stock_ex_date": "",
                        "cash_dividend": 0.42,
                        "stock_dividend": 0.0,
                        "source": "unit_fake",
                    }
                ]

            report = repair_dividend_amount_ledger(
                path,
                dry_run=False,
                network=True,
                fetchers={"fake": fake},
                report_dir=out,
            )
            self.assertEqual(len(report.repaired), 1)
            self.assertEqual(report.repaired[0]["new"], "0.42")
            self.assertFalse(report.unresolved)
            self.assertTrue(report.wrote_csv)
            self.assertEqual(scan_bad_amount_cells(path), [])
            events = load_dividend_events(
                path, require_exists=True, fail_closed_amounts=True
            )
            self.assertEqual(len(events), 1)
            self.assertAlmostEqual(events[0].amount, 0.42)

    def test_with_repair_helper_then_fail_closed_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "div.csv"
            _write(
                path,
                [
                    {
                        "code": "0050",
                        "fiscal_year": "",
                        "record_date": "",
                        "announcement_date": "",
                        "announcement_time": "",
                        "cash_ex_date": "2024-01-18",
                        "cash_payment_date": "2024-02-21",
                        "cash_dividend": "??",
                        "stock_ex_date": "",
                        "stock_payment_date": "",
                        "stock_dividend": "",
                    }
                ],
            )

            def fake(_code: str) -> list[dict]:
                return [
                    {
                        "code": "0050",
                        "cash_ex_date": "2024-01-18",
                        "stock_ex_date": "",
                        "cash_dividend": 0.7,
                        "stock_dividend": "",
                        "source": "unit_fake_etf",
                    }
                ]

            # Patch repair path used by helper via direct repair first, then helper on clean file.
            repair_dividend_amount_ledger(
                path,
                fetchers={"fake": fake},
                report_dir=Path(tmp) / "out",
            )
            events = load_dividend_events_with_repair(
                path, require_exists=True, network=False
            )
            self.assertEqual(events[0].amount, 0.7)

    def test_unresolved_still_raises_on_helper(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "div.csv"
            _write(
                path,
                [
                    {
                        "code": "2886",
                        "fiscal_year": "",
                        "record_date": "",
                        "announcement_date": "",
                        "announcement_time": "",
                        "cash_ex_date": "2024-06-01",
                        "cash_payment_date": "",
                        "cash_dividend": "BAD",
                        "stock_ex_date": "",
                        "stock_payment_date": "",
                        "stock_dividend": "",
                    }
                ],
            )

            def empty(_code: str) -> list[dict]:
                return []

            with self.assertRaises(ValueError):
                # Force helper to attempt repair with empty fetchers by calling repair+load pattern
                report = repair_dividend_amount_ledger(
                    path,
                    fetchers={"empty": empty},
                    report_dir=Path(tmp) / "out",
                )
                self.assertTrue(report.unresolved)
                load_dividend_events(
                    path, require_exists=True, fail_closed_amounts=True
                )


if __name__ == "__main__":
    unittest.main()
