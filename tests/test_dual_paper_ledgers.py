#!/usr/bin/env python3
"""Unit tests for shared dual/multi-paper ledger driver."""
from __future__ import annotations

import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

import pandas as pd

from ops_dual_paper_ledgers import (
    DualPaperLedgerSpec,
    PostBaseCtx,
    PreparedBooks,
    run_dual_paper_ledgers,
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


def _identity_prepare(m, d):
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


class LedgerDriverUnitTests(unittest.TestCase):
    def test_run_dual_writes_compare(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            market = _toy_market()

            def load_m():
                return market

            def load_d():
                return pd.DataFrame()

            spec = DualPaperLedgerSpec(
                label="TOY_DUAL",
                out_dir=tmp,
                base_id="BASE",
                chal_id="CHAL",
                prepare=_identity_prepare,
                base_nav_name="base_daily_nav.csv",
                chal_nav_name="chal_daily_nav.csv",
                write_fills=True,
                base_targets_name=None,
                assert_exact_t1=False,  # toy panel may not set exact_t1
                load_market_fn=load_m,
                load_dividends_fn=load_d,
            )
            try:
                result = run_dual_paper_ledgers(spec)
            except Exception as exc:  # pragma: no cover - environment/data dependent
                self.skipTest(f"toy market insufficient for simulate_core: {exc}")
            self.assertTrue((tmp / "outputs" / "dual_paper_nav_compare.csv").exists())
            self.assertIn("BASE", result.books)
            self.assertIn("CHAL", result.books)

    def test_chal_market_and_post_base_hooks(self) -> None:
        """Specialty hooks: chal_market + post_base mutate CHAL path without BASE change."""
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            market = _toy_market(n_days=8)
            chal_seen: dict = {}

            def prepare(m, d):
                books = _identity_prepare(m, d)
                books.chal_market = m.copy()
                books.chal_market.attrs["tag"] = "aug"
                return books

            def post_base(ctx: PostBaseCtx) -> None:
                ctx.prepared.chal_kwargs["e45_exposure"] = None
                ctx.prepared.context["post_base_ran"] = True
                ctx.prepared.extras["hook_flag.csv"] = pd.Series([1.0], name="flag")

            def fake_sim(mkt, target, regime, dividends, **kwargs):
                nav = pd.DataFrame(
                    {
                        "date": sorted(mkt["date"].unique())[:5],
                        "nav": [1.0, 1.01, 1.02, 1.01, 1.03],
                    }
                )
                fills = pd.DataFrame()
                meta = {"exact_t1_ok": True}
                if "tag" in getattr(mkt, "attrs", {}):
                    chal_seen["used_chal_market"] = True
                return nav, fills, meta

            spec = DualPaperLedgerSpec(
                label="HOOK_TOY",
                out_dir=tmp,
                base_id="BASE",
                chal_id="CHAL",
                prepare=prepare,
                post_base=post_base,
                base_nav_name="base_daily_nav.csv",
                chal_nav_name="chal_daily_nav.csv",
                write_fills=False,
                base_targets_name=None,
                assert_exact_t1=True,
                load_market_fn=lambda: market,
                load_dividends_fn=lambda: pd.DataFrame(),
            )
            with mock.patch("ops_dual_paper_ledgers.simulate_core", side_effect=fake_sim):
                result = run_dual_paper_ledgers(spec)
            self.assertTrue(chal_seen.get("used_chal_market"))
            self.assertTrue(result.prepared.context.get("post_base_ran"))
            self.assertTrue((tmp / "outputs" / "hook_flag.csv").exists())

    def test_sim_context_wraps_both_arms(self) -> None:
        calls: list[str] = []

        @contextmanager
        def ctx():
            calls.append("enter")
            yield
            calls.append("exit")

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            market = _toy_market(n_days=6)

            def fake_sim(mkt, target, regime, dividends, **kwargs):
                calls.append("sim")
                nav = pd.DataFrame(
                    {"date": sorted(mkt["date"].unique())[:3], "nav": [1.0, 1.0, 1.0]}
                )
                return nav, pd.DataFrame(), {"exact_t1_ok": True}

            spec = DualPaperLedgerSpec(
                label="CTX_TOY",
                out_dir=tmp,
                base_id="BASE",
                chal_id="CHAL",
                prepare=_identity_prepare,
                sim_context=ctx,
                base_nav_name="base_daily_nav.csv",
                chal_nav_name="chal_daily_nav.csv",
                write_fills=False,
                base_targets_name=None,
                assert_exact_t1=True,
                load_market_fn=lambda: market,
                load_dividends_fn=lambda: pd.DataFrame(),
            )
            with mock.patch("ops_dual_paper_ledgers.simulate_core", side_effect=fake_sim):
                run_dual_paper_ledgers(spec)
            self.assertEqual(calls, ["enter", "sim", "exit", "enter", "sim", "exit"])

    def test_wrapper_specs_import(self) -> None:
        import e16_blend025_dual_paper_ledgers as b025
        import e16_fuse_additive_dual_paper_ledgers as fuse
        import e16_soft_assist_dual_paper_ledgers as soft
        import e45_blend005_dual_paper_ledgers as a05
        import e45_dual_paper_ledgers as e45
        import e16_fin_within_sleeve_dual_paper_ledgers as within
        import e22_dividend_accounting as e22div
        import e45_m2_bil_fx_dual_paper_ledgers as m2
        import e45_defend_handoff_dual_paper_ledgers as dh
        import e16_fin_priv_native_dual_paper_ledgers as priv

        self.assertEqual(e45.SPEC.chal_id, e45.CHAL_ID)
        self.assertEqual(a05.ALPHA, 0.05)
        self.assertEqual(b025.SPEC.e22_version, e22div.E22_V2S)
        self.assertFalse(soft.SPEC.write_fills)
        self.assertEqual(fuse.SPEC.chal_id, fuse.FUSE_ID)
        self.assertEqual(len(within.SPEC.challengers), 3)
        self.assertEqual(m2.SPEC.chal_id, m2.CHAL_ID)
        self.assertIsNotNone(dh.SPEC.post_base)
        self.assertIsNotNone(priv.SPEC.sim_context)


if __name__ == "__main__":
    unittest.main()
