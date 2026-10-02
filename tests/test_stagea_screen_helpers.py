#!/usr/bin/env python3
"""Guards for Stage A shared helpers (research-only; Soft-Frozen untouched)."""
from __future__ import annotations

import ast
import unittest
from pathlib import Path

import pandas as pd

from stagea_screen_helpers import (
    load_nav_csv,
    nav_from_returns,
    pack_nav_windows,
    returns_from_nav,
    tip_hygiene,
    tip_lift,
    utc_now_z,
    window_delta,
)

ROOT = Path(__file__).resolve().parents[1]
BASE_NAV = (
    ROOT
    / "repro/tipsoft-ip3-live-override-paper-observe/outputs/nav_BASE_LIVE_FUSE_COOL.csv"
)
CHAL_NAV = (
    ROOT
    / "repro/tipsoft-ip3-live-override-paper-observe/outputs/nav_OVERRIDE_LIVE_W42_M05_K3.csv"
)

# Tipsoft Stage A screens that must import the harness (no local helper clones).
_TIPSOFT_STAGEA = sorted(
    set(ROOT.glob("scripts/tipsoft*_stagea.py"))
    | set(ROOT.glob("scripts/tipsoft_*_stagea.py"))
)

_BANNED_LOCAL_DEFS = {
    "_utc",
    "_load_nav",
    "_pack",
    "_tip",
    "_delta",
    "_returns",
    "_nav_from_returns",
}


class StageAHelperSemantics(unittest.TestCase):
    def test_pack_and_tip_contracts(self) -> None:
        base = load_nav_csv(BASE_NAV)
        chal = load_nav_csv(CHAL_NAV)
        pack = pack_nav_windows(base)
        self.assertIn("heldout_2019_plus", pack)
        self.assertIn("sealed_2023_plus", pack)
        lift = tip_lift(base, chal)
        hyg = tip_hygiene(base, chal)
        # Opposite CAGR conventions must not be mixed.
        self.assertAlmostEqual(
            float(lift["ytd"]["cagr_lift_pp"]),
            -float(hyg["ytd"]["cagr_giveback_pp"]),
            places=4,
        )
        self.assertEqual(
            lift["ytd"]["mdd_improve_pp"], hyg["ytd"]["mdd_improve_pp"]
        )
        self.assertNotIn("gate", lift["ytd"])
        self.assertEqual(hyg["ytd"]["gate"], "PASS")
        delta = window_delta(pack_nav_windows(base), pack_nav_windows(chal))
        self.assertIn("cagr_lift_pp", delta["heldout_2019_plus"])
        r = returns_from_nav(base)
        rebuilt = nav_from_returns(r, float(base["nav"].iloc[0]))
        # pct_change round-trip is float64-noisy on long series; relative tol.
        self.assertAlmostEqual(
            float(rebuilt["nav"].iloc[-1]),
            float(base["nav"].iloc[-1]),
            delta=1e-3,
        )
        self.assertTrue(utc_now_z().endswith("Z"))

    def test_tip_lift_with_gate(self) -> None:
        base = load_nav_csv(BASE_NAV)
        chal = load_nav_csv(CHAL_NAV)
        tip = tip_lift(base, chal, include_gate=True)
        self.assertEqual(tip["ytd"]["gate"], "PASS")


class TipsoftStageAHarnessHygiene(unittest.TestCase):
    def test_tipsoft_stagea_import_helpers_no_local_clones(self) -> None:
        self.assertGreaterEqual(len(_TIPSOFT_STAGEA), 7)
        offenders: list[str] = []
        for path in _TIPSOFT_STAGEA:
            text = path.read_text(encoding="utf-8")
            if "from stagea_screen_helpers import" not in text:
                offenders.append(f"{path.name}:missing_import")
                continue
            tree = ast.parse(text)
            for node in tree.body:
                if isinstance(node, ast.FunctionDef) and node.name in _BANNED_LOCAL_DEFS:
                    offenders.append(f"{path.name}:local_def_{node.name}")
        self.assertEqual(offenders, [], msg=f"tipsoft Stage A hygiene: {offenders}")


if __name__ == "__main__":
    unittest.main()
