#!/usr/bin/env python3
"""Tip Soft hybrid runner — Soft Exact T+1 overlays + P3/P4 Exact T+0 carve.

Default research twin template (alignment protocol P2/P3 from 0kar):

- **Soft shell**: Exact T+1 Soft clips + FUSE ``SELL_a75`` + ``COOL_c8``
  (``BASE_LIVE_FUSE_COOL`` / tip Soft live stack)
- **P3/P4 carve premium**: Soft-core T+0 NAV minus Soft-core T+1-lag NAV
  (same-bar carve vs next-open earn), added onto the Soft shell daily returns

This is the promote-gate twin clock: Soft overlays stay Exact T+1; Path3/Path4
mechanism edge is scored as Exact T+0 carve uplift (fill-sim / P3_T0_STATE style).

Soft KEEP · broker false · Path4 live OFF unless a ballot says otherwise.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

# Default reused SSOT NAV paths (0kap / 0kao)
DEFAULT_LIVE_BASE = (
    ROOT / "repro/fin-sat-path3-path4-livestack-twin-stageb/outputs/nav_BASE_LIVE_FUSE_COOL.csv"
)
DEFAULT_LIVE_P3_T1 = (
    ROOT / "repro/fin-sat-path3-path4-livestack-twin-stageb/outputs/nav_LIVE_P3_WITHIN.csv"
)
DEFAULT_SOFTCORE_P3_T0 = (
    ROOT / "repro/fin-sat-path3-path4-coexist-stagea/outputs/nav_REF_P3_WITHIN.csv"
)
DEFAULT_SOFTCORE_P3P4_T0 = (
    ROOT
    / "repro/fin-sat-path3-path4-coexist-stagea/outputs/nav_P3_P4_CASH_00025.csv"
)

RUNNER_ID = "TIP_SOFT_HYBRID_T1_OVERLAY_T0_CARVE"
CARVE_OUT_ID = "T0_CARVE_FIN_SAT_SWITCH"


def load_nav(path: Path | str) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"])
    return (
        df[["date", "nav"]]
        .assign(date=lambda x: pd.to_datetime(x["date"]).dt.normalize(), nav=lambda x: x["nav"].astype(float))
        .sort_values("date")
        .reset_index(drop=True)
    )


def nav_returns(nav: pd.DataFrame) -> pd.Series:
    x = nav.copy()
    x["date"] = pd.to_datetime(x["date"]).dt.normalize()
    s = x.set_index("date")["nav"].astype(float).sort_index()
    return s.pct_change().fillna(0.0)


def softcore_t1_lag_nav(nav_t0: pd.DataFrame) -> pd.DataFrame:
    """Exact T+1 earn proxy: today's Soft-core T+0 return realized next session."""
    r = nav_returns(nav_t0)
    r_t1 = r.shift(1).fillna(0.0)
    out = pd.DataFrame(
        {
            "date": r_t1.index,
            "nav": (1.0 + r_t1).cumprod().to_numpy() * float(nav_t0["nav"].iloc[0]),
        }
    )
    return out.reset_index(drop=True)


def align_returns(*series: pd.Series) -> pd.DataFrame:
    df = pd.concat(series, axis=1, join="inner").dropna(how="any")
    return df


@dataclass(frozen=True)
class HybridSpec:
    """One hybrid arm: Soft Exact T+1 shell + Soft-core T+0 carve premium."""

    arm_id: str
    softcore_t0_path: Path
    shell_nav_path: Path = DEFAULT_LIVE_BASE
    note: str = ""


def build_hybrid_nav(
    *,
    shell_nav: pd.DataFrame,
    softcore_t0_nav: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """r_hybrid = r_shell_T1 + (r_softcore_T0 − r_softcore_T1lag)."""
    shell_r = nav_returns(shell_nav).rename("r_shell_t1")
    t0_r = nav_returns(softcore_t0_nav).rename("r_carve_t0")
    t1_nav = softcore_t1_lag_nav(softcore_t0_nav)
    t1_r = nav_returns(t1_nav).rename("r_carve_t1lag")
    m = align_returns(shell_r, t0_r, t1_r)
    premium = (m["r_carve_t0"] - m["r_carve_t1lag"]).rename("r_t0_premium")
    r_h = (m["r_shell_t1"] + premium).rename("r_hybrid")
    nav = (1.0 + r_h).cumprod() * float(shell_nav["nav"].iloc[0])
    out = pd.DataFrame({"date": r_h.index, "nav": nav.to_numpy()})
    meta = {
        "runner_id": RUNNER_ID,
        "carve_out_id": CARVE_OUT_ID,
        "shell_fill_timing": "exact_t1",
        "carve_fill_timing": "t0",
        "n_days": int(len(out)),
        "mean_t0_premium": round(float(premium.mean()), 6),
        "sum_t0_premium": round(float(premium.sum()), 6),
        "pct_days_premium_pos": round(float((premium > 0).mean()), 4),
        "start": str(pd.Timestamp(out["date"].iloc[0]).date()),
        "end": str(pd.Timestamp(out["date"].iloc[-1]).date()),
    }
    return out.reset_index(drop=True), meta


def default_hybrid_specs() -> list[HybridSpec]:
    return [
        HybridSpec(
            arm_id="HYBRID_P3_WITHIN_T0",
            softcore_t0_path=DEFAULT_SOFTCORE_P3_T0,
            shell_nav_path=DEFAULT_LIVE_BASE,
            note="Soft Exact T+1 FUSE+COOL + Path3 WITHIN Soft-core T+0 carve premium",
        ),
        HybridSpec(
            arm_id="HYBRID_P3_P4_CASH_00025_T0",
            softcore_t0_path=DEFAULT_SOFTCORE_P3P4_T0,
            shell_nav_path=DEFAULT_LIVE_BASE,
            note="Soft Exact T+1 FUSE+COOL + Path3+Path4 CASH Soft-core T+0 carve premium",
        ),
    ]


def run_default_hybrids(
    *,
    live_base_path: Path = DEFAULT_LIVE_BASE,
    live_p3_t1_path: Path = DEFAULT_LIVE_P3_T1,
) -> dict[str, Any]:
    """Build base + hybrid arms; return navs + metas (no I/O beyond reads)."""
    base = load_nav(live_base_path)
    arms: dict[str, pd.DataFrame] = {"BASE_LIVE_FUSE_COOL": base}
    metas: dict[str, dict[str, Any]] = {
        "BASE_LIVE_FUSE_COOL": {
            "runner_id": RUNNER_ID,
            "kind": "tip_soft_shell",
            "shell_fill_timing": "exact_t1",
            "carve_fill_timing": None,
            "path3": False,
            "path4": False,
        }
    }
    if live_p3_t1_path.exists():
        arms["TIPSOFT_P3_WITHIN_T1"] = load_nav(live_p3_t1_path)
        metas["TIPSOFT_P3_WITHIN_T1"] = {
            "runner_id": RUNNER_ID,
            "kind": "tip_soft_p3_exact_t1_ref",
            "shell_fill_timing": "exact_t1",
            "carve_fill_timing": "exact_t1",
            "path3": True,
            "path4": False,
            "note": "0kap Exact T+1 tip Soft Path3 (no T+0 carve premium)",
        }

    for spec in default_hybrid_specs():
        shell = load_nav(spec.shell_nav_path)
        core = load_nav(spec.softcore_t0_path)
        nav, meta = build_hybrid_nav(shell_nav=shell, softcore_t0_nav=core)
        arms[spec.arm_id] = nav
        metas[spec.arm_id] = {
            **meta,
            "kind": "tip_soft_hybrid",
            "path3": True,
            "path4": "P4" in spec.arm_id,
            "softcore_t0_path": str(spec.softcore_t0_path),
            "shell_nav_path": str(spec.shell_nav_path),
            "note": spec.note,
        }
    return {"arms": arms, "metas": metas}


__all__ = [
    "RUNNER_ID",
    "CARVE_OUT_ID",
    "HybridSpec",
    "load_nav",
    "softcore_t1_lag_nav",
    "build_hybrid_nav",
    "default_hybrid_specs",
    "run_default_hybrids",
]
