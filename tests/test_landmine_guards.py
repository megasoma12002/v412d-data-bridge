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


if __name__ == "__main__":
    unittest.main()


class PipelineQcOwnership(unittest.TestCase):
    def test_pipeline_does_not_write_qc_status(self):
        src = (SCRIPTS / "e21_forward_pipeline.py").read_text(encoding="utf-8")
        self.assertNotIn('qc_status.json").write_text', src)
        self.assertIn("pipeline_t1_audit.json", src)
        self.assertIn("confirm_e22_version_override", src)


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

