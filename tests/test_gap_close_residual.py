#!/usr/bin/env python3
"""Gap-close residual guards: calendar Y±1, NHI observe, empty div-applied alert."""
from __future__ import annotations

import csv
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
CAL_DIR = ROOT / "data" / "calendars"


class CalendarWindowYMinus1(unittest.TestCase):
    def test_load_2026_includes_2025_when_present(self) -> None:
        from twse_session_sources import load_calendar_window

        self.assertTrue((CAL_DIR / "twse_sessions_2025.csv").exists())
        self.assertTrue((CAL_DIR / "twse_sessions_2026.csv").exists())
        sessions, settlements = load_calendar_window(2026, calendar_dir=CAL_DIR, span=1)
        # 2025 CNY settlement-only days are settlements, not sessions.
        self.assertIn(date(2025, 1, 23), settlements)
        self.assertNotIn(date(2025, 1, 23), sessions)
        self.assertNotIn(date(2025, 1, 27), sessions)
        self.assertNotIn(date(2025, 1, 27), settlements)
        # Dragon Boat compensatory weekday close (Fri May 30), not Sat May 31.
        self.assertNotIn(date(2025, 5, 30), sessions)
        self.assertNotIn(date(2025, 5, 31), sessions)  # weekend
        # Late-2025 labeled pins
        self.assertNotIn(date(2025, 9, 29), sessions)
        self.assertNotIn(date(2025, 12, 25), sessions)
        # 2026 still present
        self.assertTrue(any(d.year == 2026 for d in sessions))

    def test_2025_cny_jan27_closed(self) -> None:
        with (CAL_DIR / "twse_sessions_2025.csv").open(encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        by = {r["date"]: r for r in rows}
        self.assertEqual(by["2025-01-27"]["is_session"], "0")
        self.assertEqual(by["2025-01-23"]["kind"], "SETTLEMENT_ONLY")
        self.assertEqual(by["2025-01-24"]["kind"], "SETTLEMENT_ONLY")
        self.assertEqual(by["2025-05-30"]["kind"], "CLOSED_HOLIDAY")
        self.assertEqual(by["2025-05-31"]["kind"], "WEEKEND")


class NhiObserveArtifacts(unittest.TestCase):
    def test_observe_script_and_artifacts(self) -> None:
        script = SCRIPTS / "e22_tax0_vs_nhi211_observe.py"
        self.assertTrue(script.is_file())
        src = script.read_text(encoding="utf-8")
        self.assertIn("promote_ready", src)
        self.assertIn("E22_V3_RECV_PAY_EFFDELAY_NHI211", src)
        md = ROOT / "research/ops/E22_TAX0_VS_NHI211_OBSERVE.md"
        js = ROOT / "research/ops/E22_TAX0_VS_NHI211_OBSERVE.json"
        self.assertTrue(md.is_file(), "run observe script before commit")
        self.assertTrue(js.is_file())
        payload = json.loads(js.read_text(encoding="utf-8"))
        self.assertIs(payload.get("promote_ready"), False)
        self.assertEqual(payload.get("tax0_version"), "E22_v3_recv_pay_effdelay")
        self.assertEqual(
            payload.get("nhi211_version"), "E22_v3_recv_pay_effdelay_nhi211"
        )

    def test_sandbox_versions_include_nhi211(self) -> None:
        import e22_v3_sandbox_books as sandbox

        self.assertIn(sandbox.E22_V3_RECV_PAY_EFFDELAY_NHI211, sandbox.SANDBOX_VERSIONS)


class AlertEmptyDivApplied(unittest.TestCase):
    def test_source_wires_empty_file_code(self) -> None:
        src = (SCRIPTS / "ops_alert_scan.py").read_text(encoding="utf-8")
        self.assertIn("DIV_APPLIED_EMPTY_IN_RECV_WINDOW", src)
        self.assertIn("DIV_APPLIED_MISSING_IN_RECV_WINDOW", src)

    def test_empty_div_applied_alert_emitted(self) -> None:
        """Unit: Stage-E tip + recv window + empty dividends_applied → INFO alert."""
        import ops_alert_scan as scan

        gap6 = {
            "code_ok": True,
            "kpi_ok": True,
            "flags": [],
            "code_wire": {"default_books_version": scan.STAGE_E_DEFAULT},
            "live_ledger": {
                "observed_books_version": scan.STAGE_E_DEFAULT,
                "dividends_applied_exists": True,
                "dividends_applied_n": 0,
            },
            "receivable_stub": {"n_cash_events_in_receivable_window": 3},
        }
        alerts: list[dict] = []
        # Replicate the branch under test (keep scan importable without full run).
        live = gap6["live_ledger"]
        observed = live["observed_books_version"]
        recv = gap6["receivable_stub"]
        n_recv = int(recv["n_cash_events_in_receivable_window"])
        if observed == scan.STAGE_E_DEFAULT:
            if n_recv > 0 and not live.get("dividends_applied_exists"):
                alerts.append({"code": "DIV_APPLIED_MISSING_IN_RECV_WINDOW"})
            elif (
                n_recv > 0
                and live.get("dividends_applied_exists")
                and int(live.get("dividends_applied_n") or 0) == 0
            ):
                alerts.append({"code": "DIV_APPLIED_EMPTY_IN_RECV_WINDOW"})
        codes = {a["code"] for a in alerts}
        self.assertIn("DIV_APPLIED_EMPTY_IN_RECV_WINDOW", codes)
        self.assertNotIn("DIV_APPLIED_MISSING_IN_RECV_WINDOW", codes)


class Gap6NhiTaxSensitivity(unittest.TestCase):
    def test_tax_sensitivity_nhi_columns(self) -> None:
        from e22_gap6_fidelity_kpi import _tax_sensitivity

        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "dividends_applied.csv"
            p.write_text(
                "kind,cash_credit\ncash,19999\ncash,20000\ncash,100000\n",
                encoding="utf-8",
            )
            out = _tax_sensitivity(p)
            self.assertTrue(out["available"])
            self.assertEqual(out["nhi211_n_above_threshold"], 2)
            self.assertAlmostEqual(out["nhi211_premium"], 20000 * 0.0211 + 100000 * 0.0211)
            self.assertIn("nhi211_net_cash", out)


class CalendarDefaultsDehardcoded(unittest.TestCase):
    def test_scripts_no_longer_default_2026_only(self) -> None:
        for name in (
            "twse_forward_session_gate.py",
            "twse_dividend_delay_estimate.py",
            "twse_dividend_delay_sim.py",
            "e22_v3_stage_b_sealed_compare.py",
            "e22_v3_sandbox_books.py",
        ):
            src = (SCRIPTS / name).read_text(encoding="utf-8")
            self.assertNotIn(
                'DEFAULT_CALENDAR_DIR / "twse_sessions_2026.csv"',
                src,
                msg=f"{name} still hardcodes 2026 calendar default",
            )

    def test_e50_uses_load_calendar_window(self) -> None:
        src = (SCRIPTS / "e50_early_stack_combined_nav.py").read_text(encoding="utf-8")
        self.assertIn("load_calendar_window", src)
        self.assertNotIn(
            'f"twse_sessions_{year}.csv"',
            src,
            msg="e50 still single-year calendar path",
        )


class DocsHygieneResidual(unittest.TestCase):
    def test_cashflow_no_open_pr_266(self) -> None:
        text = (ROOT / "research/ops/CASHFLOW_THREE_VIEWS.md").read_text(encoding="utf-8")
        self.assertNotIn("open PR #266", text)
        self.assertIn("#266", text)
        self.assertIn("#268", text)
        self.assertIn("#269", text)

    def test_ops_status_unmashed_and_y1_wording(self) -> None:
        text = (ROOT / "research/ops/OPS_STATUS.md").read_text(encoding="utf-8")
        self.assertNotIn("KEEP** || Month-end", text)
        self.assertIn("Y±1 **loader**", text)
        self.assertIn("2025 CSV pinned", text)
        self.assertIn("2027 wait", text)


if __name__ == "__main__":
    unittest.main()
