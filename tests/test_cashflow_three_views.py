#!/usr/bin/env python3
"""Cashflow three-views report — unit + tip smoke."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

from cashflow_three_views_report import (
    STAGE_E_DEFAULT,
    build_report,
    receivable_total,
)


class ReceivableTotalTests(unittest.TestCase):
    def test_empty(self) -> None:
        self.assertEqual(receivable_total({}), 0.0)
        self.assertEqual(receivable_total({"e22_receivables": None}), 0.0)

    def test_sum(self) -> None:
        self.assertEqual(
            receivable_total({"e22_receivables": {"2330": 100.5, "2880": 50.25}}),
            150.75,
        )


class BuildReportFixtureTests(unittest.TestCase):
    def test_three_views_and_r4_identity(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            state = Path(td)
            (state / "portfolio_state.json").write_text(
                json.dumps(
                    {
                        "last_date": "2026-09-16",
                        "cash": 1000.0,
                        "e22_books_version": STAGE_E_DEFAULT,
                        "e22_receivables": {"0050": 40.0},
                    }
                ),
                encoding="utf-8",
            )
            (state / "settlement_cash_estimate.json").write_text(
                json.dumps(
                    {
                        "summary": {
                            "asof": "2026-09-16",
                            "paper_cash": 1000.0,
                            "unsettled_net": 200.0,
                            "settled_cash_estimate": 800.0,
                            "settling_today_net": 0.0,
                            "n_unsettled": 1,
                        }
                    }
                ),
                encoding="utf-8",
            )
            report = build_report(state)
            self.assertFalse(report["views"]["C_stage_e_div_cashflow"]["tip_lag"])
            self.assertEqual(report["views"]["A_paper_exact_t1"]["cash"], 1000.0)
            self.assertEqual(
                report["views"]["B_r4_settled_liquidity"]["settled_cash_estimate"], 800.0
            )
            self.assertTrue(report["views"]["B_r4_settled_liquidity"]["identity_ok"])
            self.assertEqual(
                report["views"]["C_stage_e_div_cashflow"]["cash_plus_receivable"], 1040.0
            )
            self.assertEqual(report["warnings"], [])
            self.assertTrue(
                any("Phase 2 tip catch-up CONFIRMED" in n for n in report["next_ops"])
            )
            self.assertFalse(
                any("Weekday tip →" in n for n in report["next_ops"])
            )

    def test_r4_asof_mismatch_warning_and_cross_check(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            state = Path(td)
            (state / "portfolio_state.json").write_text(
                json.dumps(
                    {
                        "last_date": "2026-09-16",
                        "cash": 1000.0,
                        "e22_books_version": STAGE_E_DEFAULT,
                        "e22_receivables": {},
                    }
                ),
                encoding="utf-8",
            )
            (state / "settlement_cash_estimate.json").write_text(
                json.dumps(
                    {
                        "summary": {
                            "asof": "2026-09-15",
                            "paper_cash": 1000.0,
                            "unsettled_net": 0.0,
                            "settled_cash_estimate": 1000.0,
                            "settling_today_net": 0.0,
                        }
                    }
                ),
                encoding="utf-8",
            )
            report = build_report(state)
            self.assertTrue(report["cross_checks"]["r4_asof_mismatch"])
            self.assertFalse(report["cross_checks"]["r4_asof_matches_last_date"])
            self.assertTrue(any("R4_ASOF_MISMATCH" in w for w in report["warnings"]))

    def test_fail_on_r4_asof_mismatch_cli(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            state = Path(td)
            (state / "portfolio_state.json").write_text(
                json.dumps(
                    {
                        "last_date": "2026-09-16",
                        "cash": 1000.0,
                        "e22_books_version": STAGE_E_DEFAULT,
                    }
                ),
                encoding="utf-8",
            )
            (state / "settlement_cash_estimate.json").write_text(
                json.dumps(
                    {
                        "summary": {
                            "asof": "2026-09-10",
                            "paper_cash": 1000.0,
                            "unsettled_net": 0.0,
                            "settled_cash_estimate": 1000.0,
                            "settling_today_net": 0.0,
                        }
                    }
                ),
                encoding="utf-8",
            )
            rc = subprocess.call(
                [
                    sys.executable,
                    str(SCRIPTS / "cashflow_three_views_report.py"),
                    "--state-dir",
                    str(state),
                    "--fail-on-r4-asof-mismatch",
                ],
                cwd=str(ROOT),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self.assertEqual(rc, 1)

    def test_tip_lag_warning_on_preserved_books(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            state = Path(td)
            (state / "portfolio_state.json").write_text(
                json.dumps(
                    {
                        "last_date": "2026-09-16",
                        "cash": 50415.5,
                        "e22_books_version": "E22_v2s_tw_effex",
                    }
                ),
                encoding="utf-8",
            )
            (state / "settlement_cash_estimate.json").write_text(
                json.dumps(
                    {
                        "summary": {
                            "asof": "2026-09-16",
                            "paper_cash": 50415.5,
                            "unsettled_net": 49393.3,
                            "settled_cash_estimate": 1022.2,
                            "settling_today_net": 0.0,
                        }
                    }
                ),
                encoding="utf-8",
            )
            report = build_report(state)
            self.assertTrue(report["views"]["C_stage_e_div_cashflow"]["tip_lag"])
            self.assertTrue(any("TIP_LAG" in w for w in report["warnings"]))
            self.assertTrue(any("Weekday tip →" in n for n in report["next_ops"]))
            self.assertFalse(
                any("Phase 2 tip catch-up CONFIRMED" in n for n in report["next_ops"])
            )


class TipSmokeTests(unittest.TestCase):
    def test_cli_against_forward_e21(self) -> None:
        state = ROOT / "forward" / "e21"
        if not (state / "portfolio_state.json").is_file():
            self.skipTest("no tip portfolio_state")
        rc = subprocess.call(
            [
                sys.executable,
                str(SCRIPTS / "cashflow_three_views_report.py"),
                "--state-dir",
                str(state),
                "--fail-on-r4-identity",
            ],
            cwd=str(ROOT),
        )
        self.assertEqual(rc, 0)

    def test_ssot_files_exist(self) -> None:
        self.assertTrue((ROOT / "research" / "ops" / "CASHFLOW_THREE_VIEWS.md").is_file())
        self.assertTrue((ROOT / "research" / "ops" / "CASHFLOW_THREE_VIEWS.json").is_file())
        self.assertTrue(
            (ROOT / "research" / "ops" / "TIP_CATCHUP_MONDAY_CHECKLIST.md").is_file()
        )
        self.assertTrue(
            (ROOT / "research" / "ops" / "NHI_DIVIDEND_SUPPLEMENTAL_PREMIUM_NOTE.md").is_file()
        )


if __name__ == "__main__":
    unittest.main()
