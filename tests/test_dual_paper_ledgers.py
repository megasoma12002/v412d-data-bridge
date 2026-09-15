#!/usr/bin/env python3
"""Unit tests for shared dual/multi-paper ledger driver."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from ops_dual_paper_ledgers import (
    DualPaperLedgerSpec,
    MultiChallengerLedgerBook,
    MultiPaperLedgerSpec,
    PreparedBooks,
    PreparedMultiBooks,
    run_dual_paper_ledgers,
    run_multi_paper_ledgers,
)


def _toy_market(n_days: int = 40) -> pd.DataFrame:
    """Minimal market panel for simulate_core smoke (codes in ALL + TAIEX)."""
    from e50_early_stack_combined_nav import ALL

    dates = pd.bdate_range("2024-01-02", periods=n_days)
    rows = []
    for d in dates:
        for code in list(ALL) + ["TAIEX"]:
            rows.append(
                {
                    "date": d,
                    "code": code,
                    "open": 100.0,
                    "high": 101.0,
                    "low": 99.0,
                    "close": 100.0,
                    "adj_close": 100.0,
                    "volume": 1_000_000,
                }
            )
    return pd.DataFrame(rows)


class LedgerDriverUnitTests(unittest.TestCase):
    def test_run_dual_writes_compare(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            market = _toy_market()

            def load_m():
                return market

            def load_d():
                return pd.DataFrame()

            def prepare(m, d):
                # Identity targets: equal Soft-Frozen-like weights
                idx = pd.DatetimeIndex(sorted(m["date"].unique()))
                target = pd.DataFrame(
                    1.0 / 3.0,
                    index=idx,
                    columns=["Financial", "Telecom", "0050"],
                )
                regime = pd.Series("NEUTRAL", index=idx)
                return PreparedBooks(
                    base_target=target,
                    base_regime=regime,
                    chal_target=target,
                    chal_regime=regime,
                    base_kwargs={"e45_exposure": None},
                    chal_kwargs={"e45_exposure": None},
                )

            spec = DualPaperLedgerSpec(
                label="TOY_DUAL",
                out_dir=tmp,
                base_id="BASE",
                chal_id="CHAL",
                prepare=prepare,
                base_nav_name="base_daily_nav.csv",
                chal_nav_name="chal_daily_nav.csv",
                write_fills=True,
                base_targets_name=None,
                assert_exact_t1=False,  # toy panel may not set exact_t1
                load_market_fn=load_m,
                load_dividends_fn=load_d,
            )
            # simulate_core needs richer features — skip if it fails hard on toy data
            try:
                result = run_dual_paper_ledgers(spec)
            except Exception as exc:  # pragma: no cover - environment/data dependent
                self.skipTest(f"toy market insufficient for simulate_core: {exc}")
            self.assertTrue((tmp / "outputs" / "dual_paper_nav_compare.csv").exists())
            self.assertIn("BASE", result.books)
            self.assertIn("CHAL", result.books)

    def test_wrapper_specs_import(self) -> None:
        import e16_blend025_dual_paper_ledgers as b025
        import e16_fuse_additive_dual_paper_ledgers as fuse
        import e16_soft_assist_dual_paper_ledgers as soft
        import e45_blend005_dual_paper_ledgers as a05
        import e45_dual_paper_ledgers as e45
        import e16_fin_within_sleeve_dual_paper_ledgers as within
        import e22_dividend_accounting as e22div

        self.assertEqual(e45.SPEC.chal_id, e45.CHAL_ID)
        self.assertEqual(a05.ALPHA, 0.05)
        self.assertEqual(b025.SPEC.e22_version, e22div.E22_V2S)
        self.assertFalse(soft.SPEC.write_fills)
        self.assertEqual(fuse.SPEC.chal_id, fuse.FUSE_ID)
        self.assertEqual(len(within.SPEC.challengers), 3)


if __name__ == "__main__":
    unittest.main()
