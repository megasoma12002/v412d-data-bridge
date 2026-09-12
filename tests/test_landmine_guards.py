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
        import sys

        sys.path.insert(0, str(SCRIPTS))
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
    def test_live_pipeline_has_no_soft_assist_wire(self):
        src = (SCRIPTS / "e21_forward_pipeline.py").read_text(encoding="utf-8")
        for needle in ("soft_assist", "SOFT_BOTH", "BELOW_MA120", "fin_sell_scores"):
            self.assertNotIn(needle, src)
        self.assertIn("LIVE_E45_STITCH = False", src)
        self.assertIn("FIN_PRE_EXDIV_KD", src)

    def test_soft_assist_helpers_match_live_kd_opt(self):
        import sys

        sys.path.insert(0, str(SCRIPTS))
        from soft_assist_helpers import LIVE_KD
        import e21_forward_pipeline as e21

        for k in ("season_start", "season_end", "k_thresh", "pre_days", "active_score"):
            self.assertEqual(LIVE_KD[k], e21.KD_OPT[k], msg=k)

    def test_month_end_monitor_can_use_compare_csv(self):
        src = (SCRIPTS / "e16_soft_assist_month_end_monitor.py").read_text(encoding="utf-8")
        self.assertIn("dual_paper_nav_compare", src)
        self.assertIn("nav_source", src)


class SleeveTiltObserveGuards(unittest.TestCase):
    def test_live_pipeline_has_no_sleeve_tilt_wire(self):
        src = (SCRIPTS / "e21_forward_pipeline.py").read_text(encoding="utf-8")
        for needle in (
            "sleeve_tilt",
            "SLEEVE_BELOW_MA60",
            "BELOW_MA60",
            "build_champion_target",
        ):
            self.assertNotIn(needle, src)

    def test_soft_assist_guard_also_bans_ma60_tilt_marker(self):
        # Soft-assist static ban previously covered MA120 only; MA60 is sleeve-tilt.
        src = (SCRIPTS / "e21_forward_pipeline.py").read_text(encoding="utf-8")
        self.assertNotIn("BELOW_MA60", src)

    def test_ops_alert_scan_includes_observe_monitors(self):
        src = (SCRIPTS / "ops_alert_scan.py").read_text(encoding="utf-8")
        self.assertIn("SOFT_ASSIST_MONTH_END_MONITOR.json", src)
        self.assertIn("SLEEVE_LAYER_TILT_MONTH_END_MONITOR.json", src)

    def test_forward_pipeline_refuses_asof_rewind(self):
        src = (SCRIPTS / "e21_forward_pipeline.py").read_text(encoding="utf-8")
        self.assertIn("cannot silently rewind", src)
        self.assertIn("afford < orig_q", src)


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


if __name__ == "__main__":
    unittest.main()
