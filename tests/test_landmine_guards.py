"""Minimal fail-closed guards from project landmine review.

Does not touch Soft-Frozen / DEFAULT / stitch. Fast, no network.
"""
from __future__ import annotations

import importlib.util
import re
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


class BookIdGuards(unittest.TestCase):
    def test_book_id_for_alpha_canonical(self):
        from e45_paper_harness import (
            BOOK_BASE,
            BOOK_BLEND_A05,
            BOOK_BLEND_A25,
            BOOK_FULL,
            book_id_for_alpha,
        )

        self.assertEqual(book_id_for_alpha(0.0), BOOK_BASE)
        self.assertEqual(book_id_for_alpha(0.05), BOOK_BLEND_A05)
        self.assertEqual(book_id_for_alpha(0.25), BOOK_BLEND_A25)
        self.assertEqual(book_id_for_alpha(1.0), BOOK_FULL)
        self.assertTrue(BOOK_BLEND_A05.startswith("BLEND_E45_A"))
        self.assertNotEqual(BOOK_FULL, "FULL_E45")
        self.assertNotIn("REF_BLEND_A", BOOK_BLEND_A05)


class FetchImportGuard(unittest.TestCase):
    def test_fetch_import_has_no_network_side_effect(self):
        import ast

        path = SCRIPTS / "fetch_telecom_0050_ohlcv.py"
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src)
        top = []
        for node in tree.body:
            if isinstance(node, ast.Import):
                top.extend(a.name.split(".", 1)[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                top.append(node.module.split(".", 1)[0])
        for banned in ("pandas", "requests", "yfinance"):
            self.assertNotIn(banned, top)

        spec = importlib.util.spec_from_file_location("fetch_telecom_0050_ohlcv", path)
        mod = importlib.util.module_from_spec(spec)
        t0 = time.time()
        assert spec.loader is not None
        spec.loader.exec_module(mod)
        self.assertLess(time.time() - t0, 3.0)
        self.assertTrue(callable(getattr(mod, "main", None)))


class HygieneArtifactPatterns(unittest.TestCase):
    def test_artifact_bad_patterns_cover_retired_ids(self):
        text = (SCRIPTS / "check_e45_paper_hygiene.py").read_text(encoding="utf-8")
        for needle in (
            r'"FULL_E45"',
            r'"BLEND_A\d{2}"',
            r'"CONST_A\d{2}"',
            r'"REF_BLEND_A\d{2}"',
            r'"CHAL_E45_E3_FULL"',
        ):
            self.assertIn(needle, text)
        for path in (
            "repro/e45-crisis-triggered-alpha/reports/*.json",
            "research/e45/E45_CRISIS_TRIGGERED_ALPHA.json",
            "research/e45/E45_MAXCUT_MILD_PROFILE.json",
        ):
            self.assertIn(path, text)


class PipelineQcOwnership(unittest.TestCase):
    def test_pipeline_does_not_write_qc_status(self):
        src = (SCRIPTS / "e21_forward_pipeline.py").read_text(encoding="utf-8")
        self.assertNotIn('qc_status.json").write_text', src)
        self.assertIn("pipeline_t1_audit.json", src)
        self.assertIn("confirm_e22_version_override", src)


class LiveCapitalWorkflowGuard(unittest.TestCase):
    def test_forward_workflow_does_not_hardcode_obsolete_3m(self):
        yml = (ROOT / ".github/workflows/v412f-forward-paper.yml").read_text(encoding="utf-8")
        self.assertIn("e21_forward_pipeline.py", yml)
        self.assertNotRegex(yml, r"e21_forward_pipeline\.py[^\n]*--capital\s+3000000")
        self.assertNotRegex(yml, r"--capital\s+3_?000_?000")


class SoftAssistObserveGuards(unittest.TestCase):
    def test_live_pipeline_soft_wire_only_via_authorized_fuse(self):
        """Standalone Soft-assist live wire stays banned; FUSE_ADDITIVE ACCEPT allows softs."""
        pipe = (SCRIPTS / "e21_forward_pipeline.py").read_text(encoding="utf-8")
        cfg = (SCRIPTS / "live_config.py").read_text(encoding="utf-8")
        targets = (SCRIPTS / "live_strategy_targets.py").read_text(encoding="utf-8")
        orders = (SCRIPTS / "live_rebalance_orders.py").read_text(encoding="utf-8")
        # Independent Soft-assist observe markers must not be hard-wired into live.
        for needle in ("soft_assist", "SOFT_BOTH", "BELOW_MA120"):
            self.assertNotIn(needle, pipe)
            self.assertNotIn(needle, cfg)
            self.assertNotIn(needle, targets)
            self.assertNotIn(needle, orders)
        self.assertIn("FIN_PRE_EXDIV_KD", cfg)
        # E45 A05 stitch DROPPED — no flip field on LiveConfig; no stitch branch in targets.
        self.assertNotIn("live_e45_stitch:", cfg)
        self.assertIn("E45_A05_STITCH_DROPPED = True", cfg)
        self.assertIn("LIVE_E45_STITCH = False", cfg)
        self.assertNotIn("if cfg.live_e45_stitch", targets)
        # 2026-09-13 ACCEPT Live cutover: DH_dd06 + FUSE_ADDITIVE (MENU3).
        self.assertIn("live_fuse_additive: bool = True", cfg)
        self.assertIn("live_dh_exposure: bool = True", cfg)
        # FUSE routes via cutover helper (extracted from thin pipeline).
        self.assertIn("live_dh_fuse_cutover", targets)
        self.assertIn("live_dh_fuse_cutover", orders)
        self.assertIn("fin_sell_scores", orders)
        self.assertIn("LIVE_FUSE_ADDITIVE", orders)

    def test_soft_assist_helpers_match_live_kd_opt(self):
        from soft_assist_helpers import LIVE_KD
        import e21_forward_pipeline as e21
        from live_config import KD_OPT

        self.assertIs(LIVE_KD, KD_OPT)
        for k in ("season_start", "season_end", "k_thresh", "pre_days", "active_score"):
            self.assertEqual(LIVE_KD[k], e21.KD_OPT[k], msg=k)

    def test_month_end_monitor_can_use_compare_csv(self):
        wrapper = (SCRIPTS / "e16_soft_assist_month_end_monitor.py").read_text(encoding="utf-8")
        runner = (SCRIPTS / "ops_dual_paper_month_end.py").read_text(encoding="utf-8")
        self.assertIn("dual_paper_nav_compare", wrapper)
        self.assertIn("compare_nav", wrapper)
        self.assertIn("nav_source", runner)


class SleeveTiltObserveGuards(unittest.TestCase):
    def test_live_pipeline_sleeve_tilt_only_via_authorized_fuse(self):
        """Standalone Sleeve-tilt live wire stays banned; FUSE routes via cutover helper."""
        pipe = (SCRIPTS / "e21_forward_pipeline.py").read_text(encoding="utf-8")
        cfg = (SCRIPTS / "live_config.py").read_text(encoding="utf-8")
        targets = (SCRIPTS / "live_strategy_targets.py").read_text(encoding="utf-8")
        for needle in (
            "sleeve_tilt",
            "SLEEVE_BELOW_MA60",
            "BELOW_MA60",
            "build_champion_target",
        ):
            self.assertNotIn(needle, pipe)
            self.assertNotIn(needle, cfg)
        self.assertIn("live_fuse_additive: bool = True", cfg)
        self.assertIn("live_dh_fuse_cutover", targets)
        helper = (SCRIPTS / "live_dh_fuse_cutover.py").read_text(encoding="utf-8")
        self.assertIn("build_champion_target", helper)
        # FUSE offense full-history must pin preserved cash-on-ex — not Stage-E
        # DEFAULT — or blank historical payment_date rows fail-closed the live day.
        self.assertIn("PRESERVED_CASH_ON_EX", helper)
        self.assertIn("e22_version=e22div.PRESERVED_CASH_ON_EX", helper)

    def test_soft_assist_guard_also_bans_ma60_tilt_marker(self):
        # Soft-assist static ban previously covered MA120 only; MA60 is sleeve-tilt.
        for name in (
            "e21_forward_pipeline.py",
            "live_strategy_targets.py",
            "live_rebalance_orders.py",
        ):
            src = (SCRIPTS / name).read_text(encoding="utf-8")
            self.assertNotIn("BELOW_MA60", src)

    def test_ops_alert_scan_includes_observe_monitors(self):
        src = (SCRIPTS / "ops_alert_scan.py").read_text(encoding="utf-8")
        self.assertIn("SOFT_ASSIST_MONTH_END_MONITOR.json", src)
        self.assertIn("SLEEVE_LAYER_TILT_MONTH_END_MONITOR.json", src)
        self.assertIn("TIP_LAG_BOOKS", src)
        self.assertIn("R4_ESTIMATE_MISSING", src)

    def test_forward_pipeline_refuses_asof_rewind(self):
        # Session rewind gate lives in live_session_io; fill skip in live_fill_core + e50.
        session_src = (SCRIPTS / "live_session_io.py").read_text(encoding="utf-8")
        core_src = (SCRIPTS / "live_fill_core.py").read_text(encoding="utf-8")
        e50_src = (SCRIPTS / "e50_early_stack_combined_nav.py").read_text(encoding="utf-8")
        self.assertIn("cannot silently rewind", session_src)
        self.assertIn("afford < orig_q", core_src)
        self.assertIn("ACCEPT_2026-09-19_PAPER_LIVE_FILL_SKIP_ALIGN", e50_src)
        self.assertIn("still.append(o)", e50_src)


class FrozenClaimLabel(unittest.TestCase):
    def test_frozen_docs_use_retired_label(self):
        for name in ("FROZEN_GOVERNANCE.md", "FROZEN_STRATEGY_SPEC.md"):
            text = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn("RETIRED_HISTORICAL_NARRATIVE", text)
            # Allow historical quotes only if retired label also present nearby — ban bare status use
            # Simple: file must not claim the handoff MDD is currently NOT_VERIFIED as active status.
            self.assertNotRegex(
                text,
                r"as \*\*NOT_VERIFIED\*\*|（\*\*NOT_VERIFIED\*\*）",
            )



class E22PaymentDateCompletenessGuards(unittest.TestCase):
    def test_soft_frozen_cash_payment_dates_complete(self):
        """Ledger refresh must not re-drop Soft-Frozen cash payment dates (DQ gate)."""
        import pandas as pd

        events = ROOT / "data/dividend_events/e22_dividend_events.csv"
        if not events.is_file():
            self.skipTest("no dividend events ledger")
        soft = {"2880", "2886", "2892", "5880", "2412", "3045", "4904", "0050"}
        df = pd.read_csv(events, dtype=str).fillna("")
        df["code"] = df["code"].astype(str).str.zfill(4)
        cash = df[df["code"].isin(soft) & (pd.to_numeric(df["cash_dividend"], errors="coerce").fillna(0) > 0)]
        blank = cash["cash_payment_date"].astype(str).str.strip() == ""
        self.assertEqual(int(blank.sum()), 0, msg=cash.loc[blank, ["code", "cash_ex_date"]].to_string())


class LiveBooksSsotGuards(unittest.TestCase):
    """Docs/code tip must not resurrect E22_v2s_tw as live DEFAULT."""

    def test_code_default_is_stage_e(self):
        import e22_dividend_accounting as e22div
        from live_config import LiveConfig

        self.assertEqual(e22div.DEFAULT_BOOKS_VERSION, "E22_v3_recv_pay_effdelay")
        self.assertEqual(LiveConfig().e22_books_version, e22div.DEFAULT_BOOKS_VERSION)

    def test_tip_books_match_default_when_present(self):
        import e22_dividend_accounting as e22div
        import json

        tip = ROOT / "forward/e21/portfolio_state.json"
        if not tip.is_file():
            self.skipTest("no tip portfolio_state")
        state = json.loads(tip.read_text(encoding="utf-8"))
        self.assertEqual(state.get("e22_books_version"), e22div.DEFAULT_BOOKS_VERSION)

    def test_handoff_and_readme_do_not_claim_v2s_tw_live_default(self):
        handoff = (ROOT / "HANDOFF.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("E22_v3_recv_pay_effdelay", handoff)
        self.assertIn("E22_v3_recv_pay_effdelay", readme)
        # Ban bare "DEFAULT_BOOKS_VERSION = E22_v2s_tw" as current live claim.
        self.assertNotRegex(
            handoff,
            r"DEFAULT_BOOKS_VERSION\s*=\s*E22_v2s_tw\b",
        )
        self.assertNotRegex(
            readme,
            r"Tip ledger may still show prior `E22_v2s_tw_effex`",
        )


class CashClockSeparationGuards(unittest.TestCase):
    """Fail-closed: R4 settled liquidity must never be written into Soft-Frozen cash."""

    FORBIDDEN_SNIPPETS = (
        'portfolio_state["cash"] = settled',
        "portfolio_state['cash'] = settled",
        'state["cash"] = settled_cash',
        "state['cash'] = settled_cash",
        "cash = settled_cash_estimate",
        '["cash"] = summary["settled_cash_estimate"]',
        "['cash'] = summary['settled_cash_estimate']",
    )

    WATCH_FILES = (
        "e21_forward_pipeline.py",
        "live_ledger.py",
        "live_session_io.py",
        "twse_t2_settlement_estimate.py",
        "cashflow_three_views_report.py",
        "post_forward_e22_verify.py",
        "ops_alert_scan.py",
    )

    def test_no_r4_merge_into_portfolio_cash_in_live_scripts(self):
        for name in self.WATCH_FILES:
            text = (SCRIPTS / name).read_text(encoding="utf-8")
            for snip in self.FORBIDDEN_SNIPPETS:
                self.assertNotIn(snip, text, msg=f"{name} contains forbidden merge: {snip}")

    def test_cashflow_docs_forbid_merge(self):
        cf = (SCRIPTS / "cashflow_three_views_report.py").read_text(encoding="utf-8")
        pf = (SCRIPTS / "post_forward_e22_verify.py").read_text(encoding="utf-8")
        self.assertIn("never merge into portfolio_state.cash", cf)
        self.assertIn("do not merge Exact T+1 / R4 / Stage-E cash clocks", pf)

    def test_broker_live_write_still_fail_closed(self):
        from live_config import LiveConfig
        from yuanta_spark_adapter import API_WIRED

        self.assertFalse(LiveConfig().broker_live_write_accepted)
        self.assertFalse(API_WIRED)


class FuseTipDualClockGuards(unittest.TestCase):
    def test_fuse_offense_pins_preserved_cash_on_ex(self):
        text = (SCRIPTS / "live_dh_fuse_cutover.py").read_text(encoding="utf-8")
        self.assertIn("PRESERVED_CASH_ON_EX", text)
        self.assertIn("E22_v2s_tw_effex", text)
        # Must not silently force Stage-E onto full-history offense rebuild.
        lowered = text.lower().replace("`", "")
        self.assertIn("not live stage-e", lowered)


if __name__ == "__main__":
    unittest.main()
