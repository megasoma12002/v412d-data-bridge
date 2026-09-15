#!/usr/bin/env python3
"""Unit tests for installable package layout (pyproject; no sys.path hacks)."""
from __future__ import annotations

import importlib
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
SYS_PATH_HACK = re.compile(r"sys\.path\.(?:insert|append)\s*\(")


class PyprojectLayoutTests(unittest.TestCase):
    def test_pyproject_and_setup_exist(self) -> None:
        self.assertTrue((ROOT / "pyproject.toml").is_file())
        self.assertTrue((ROOT / "setup.py").is_file())
        text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('name = "e21-ops"', text)
        self.assertIn('"" = "scripts"', text)

    def test_live_modules_import_without_path_hack(self) -> None:
        lc = importlib.import_module("live_config")
        e21 = importlib.import_module("e21_forward_pipeline")
        self.assertEqual(e21.LIVE_FUSE_ADDITIVE, lc.LIVE.live_fuse_additive)
        self.assertFalse(e21.LIVE_E45_STITCH)
        self.assertEqual(lc.LIVE.capital, 500_000_000.0)

    def test_no_sys_path_hacks_in_scripts_or_tests(self) -> None:
        offenders: list[str] = []
        for base in (SCRIPTS, ROOT / "tests"):
            for path in sorted(base.glob("*.py")):
                text = path.read_text(encoding="utf-8")
                for m in SYS_PATH_HACK.finditer(text):
                    line = text.count("\n", 0, m.start()) + 1
                    if text.splitlines()[line - 1].lstrip().startswith("#"):
                        continue
                    offenders.append(f"{path.relative_to(ROOT)}:{line}")
        self.assertEqual(offenders, [], msg=f"sys.path hacks remain: {offenders}")


if __name__ == "__main__":
    unittest.main()
