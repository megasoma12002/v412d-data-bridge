#!/usr/bin/env python3
"""Unit tests for DualPaperMonitorSpec alert policies + multi-paper runner."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from ops_dual_paper_month_end import (
    DualPaperMonitorSpec,
    MultiChallengerSpec,
    MultiPaperMonitorSpec,
    build_alerts,
    compare_windows,
    run_monitor,
    run_multi_monitor,
)


def _nav_csv(path: Path, start: str, n: int, start_nav: float, daily_ret: float) -> None:
    dates = pd.bdate_range(start, periods=n)
    nav = [start_nav]
    for _ in range(1, n):
        nav.append(nav[-1] * (1.0 + daily_ret))
    pd.DataFrame({"date": dates, "nav": nav}).to_csv(path, index=False)


class AlertPolicyTests(unittest.TestCase):
    def test_default_design_buffer(self) -> None:
        rows = [
            {
                "window": "ytd",
                "mdd_improve_pp": 1.0,
                "cagr_giveback_pp": 1.0,
            },
            {
                "window": "heldout_2019_plus",
                "mdd_improve_pp": 1.0,
                "cagr_giveback_pp": 4.0,  # > 0.5+2.0
            },
        ]
        spec = DualPaperMonitorSpec(
            label="T",
            base_id="B",
            chal_id="C",
            default_out=Path("."),
            base_nav=Path("missing_b"),
            chal_nav=Path("missing_c"),
        )
        alerts = build_alerts(spec, rows)
        self.assertTrue(any("heldout_2019_plus" in a and "design" in a for a in alerts))

    def test_flat_trail_pause(self) -> None:
        rows = [
            {
                "window": "ytd",
                "mdd_improve_pp": 0.5,
                "cagr_giveback_pp": 6.0,
            }
        ]
        spec = DualPaperMonitorSpec(
            label="T",
            base_id="B",
            chal_id="BLEND_025",
            default_out=Path("."),
            base_nav=Path("x"),
            chal_nav=Path("y"),
            alert_policy="flat_trail",
            design_giveback_pp={},
            flat_trail_windows=("ytd",),
        )
        alerts = build_alerts(spec, rows)
        self.assertTrue(any(a.startswith("PAUSE_REVIEW:") for a in alerts))

    def test_l4_ops_trail_no_mdd(self) -> None:
        rows = [
            {
                "window": "ytd",
                "mdd_improve_pp": -1.0,  # worse MDD — must NOT alert on ops trail
                "cagr_giveback_pp": 1.0,
            },
            {
                "window": "sealed_2023_plus",
                "mdd_improve_pp": -1.0,
                "cagr_giveback_pp": 1.0,
            },
        ]
        spec = DualPaperMonitorSpec(
            label="T",
            base_id="B",
            chal_id="L4_DD_PATH_08_50",
            default_out=Path("."),
            base_nav=Path("x"),
            chal_nav=Path("y"),
            alert_policy="l4",
            design_giveback_pp={},
        )
        alerts = build_alerts(spec, rows)
        self.assertTrue(any("sealed" in a and "MDD" in a for a in alerts))
        self.assertFalse(any("ytd" in a and "MDD" in a for a in alerts))


class RunnerIntegrationTests(unittest.TestCase):
    def test_run_monitor_writes_gaps_stem(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            base = tmp / "base.csv"
            chal = tmp / "chal.csv"
            _nav_csv(base, "2023-01-02", 40, 1.0, 0.001)
            _nav_csv(chal, "2023-01-02", 40, 1.0, 0.0005)
            art = tmp / "gaps"
            out = tmp / "out"
            spec = DualPaperMonitorSpec(
                label="TEST_GAPS",
                ops_stem="TEST_GAPS_MONITOR",
                artifact_dir=art,
                base_id="BASE",
                chal_id="CHAL",
                default_out=out,
                base_nav=base,
                chal_nav=chal,
                write_legacy_summary_names=True,
            )
            summary = run_monitor(spec, asof="2023-02-28")
            self.assertGreaterEqual(summary["n_windows"], 1)
            self.assertTrue((out / "month_end_monitor.json").exists())
            self.assertTrue((out / "MONTH_END_MONITOR.md").exists())
            self.assertTrue((art / "TEST_GAPS_MONITOR.json").exists())
            payload = json.loads((art / "TEST_GAPS_MONITOR.json").read_text())
            self.assertFalse(payload["live_wire"])
            self.assertEqual(payload["challenger_id"], "CHAL")

    def test_fixed_window_validation(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            base = tmp / "base.csv"
            chal = tmp / "chal.csv"
            # Need history covering 2019-2022 validation
            _nav_csv(base, "2019-01-02", 800, 1.0, 0.0002)
            _nav_csv(chal, "2019-01-02", 800, 1.0, 0.0001)
            rows = compare_windows(
                pd.read_csv(base, parse_dates=["date"]),
                pd.read_csv(chal, parse_dates=["date"]),
                pd.Timestamp("2022-06-01"),
                window_keys=("mtd", "full"),
                fixed_windows=(("validation_2019_2022", "2019-01-01", "2022-12-31"),),
            )
            names = {r["window"] for r in rows}
            self.assertIn("validation_2019_2022", names)

    def test_multi_paper_runner(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            base = tmp / "base.csv"
            c1 = tmp / "c1.csv"
            c2 = tmp / "c2.csv"
            _nav_csv(base, "2023-01-02", 50, 1.0, 0.001)
            _nav_csv(c1, "2023-01-02", 50, 1.0, 0.0008)
            _nav_csv(c2, "2023-01-02", 50, 1.0, 0.0012)
            art = tmp / "ops"
            out = tmp / "out"
            spec = MultiPaperMonitorSpec(
                label="MULTI_TEST",
                ops_stem="MULTI_TEST",
                artifact_dir=art,
                base_id="BASE",
                base_nav=base,
                challengers=(
                    MultiChallengerSpec(chal_id="C1", chal_nav=c1),
                    MultiChallengerSpec(chal_id="C2", chal_nav=c2),
                ),
                default_out=out,
                legacy_rs_chal_id="C1",
            )
            summary = run_multi_monitor(spec, asof="2023-03-15")
            self.assertEqual(len(summary["payload"]["challengers"]), 2)
            self.assertTrue((art / "MULTI_TEST.json").exists())
            self.assertTrue((out / "month_end_windows_rs_legacy.csv").exists())


class WrapperImportTests(unittest.TestCase):
    def test_wrappers_expose_spec(self) -> None:
        import e16_blend025_month_end_monitor as b025
        import e16_fincap50_month_end_monitor as fin50
        import e16_fin_priv_native_month_end_monitor as priv
        import e16_fin_within_sleeve_month_end_monitor as within
        import e16_l4_dd_path_month_end_monitor as l4
        import e45_month_end_monitor as e45

        self.assertEqual(b025.SPEC.alert_policy, "flat_trail")
        self.assertEqual(fin50.SPEC.alert_policy, "flat_trail")
        self.assertNotIn("sealed_2023_plus", fin50.SPEC.window_keys)
        self.assertEqual(l4.SPEC.alert_policy, "l4")
        self.assertEqual(priv.SPEC.chal_id, "PRIV_KD_MAY_Klt25_T15")
        self.assertEqual(e45.SPEC.design_giveback_pp["heldout_2019_plus"], 5.65)
        self.assertEqual(len(within.SPEC.challengers), 3)


if __name__ == "__main__":
    unittest.main()
