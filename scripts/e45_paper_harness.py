#!/usr/bin/env python3
"""Shared harness for E45 paper scripts — kill copy/paste landmines.

Canonical book IDs, claim status, market load, blend exposure, and window stats.
New E45 paper screens MUST import from here instead of redefining locals.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from research_metric_helpers import cagr_delta_pp, mdd_delta_pp
from e50_early_stack_combined_nav import ALL, e16_features, nav_stats, simulate_core
import e45_crisis_core as e45

ROOT = Path(__file__).resolve().parents[1]
MARKET_PATH = ROOT / "forward/e21/live_market.csv"
DIV_PATH = ROOT / "data/dividend_events/e22_dividend_events.csv"

# --- Canonical constants (do not fork these strings in paper scripts) ---
E45_PROFILE_DEFAULT = "E3_VOLTARGET_WINNER"
BOOK_BASE = "BASE_E16_E18_E22_v2s"
# Label honesty: BOOK_BASE is the paper ledger id string. The early-stack may run
# under E22_v2s_tw (TW odd-lot practice) depending on call site — do not infer
# formal E22_v2s books solely from this id. Prefer explicit e22_version kwargs.
BOOK_BASE_RUNTIME_NOTE = "ledger_id_only__check_e22_version_at_call_site"
BOOK_FULL = "CHAL_E45_E3"
BOOK_BLEND_A25 = "BLEND_E45_A25"
BOOK_BLEND_A05 = "BLEND_E45_A05"
CLAIM_STATUS = e45.CLAIMED_MDD_STATUS  # RETIRED_HISTORICAL_NARRATIVE

BANNED_CLAIM_LABELS = (
    "NOT_VERIFIED",
    "NOT_VERIFIED_NO_ARTIFACT_MATCH",
    e45.CLAIMED_MDD_STATUS_LEGACY,
)

WINDOWS_STANDARD: dict[str, tuple[date | None, date | None]] = {
    "full": (None, None),
    "oof_2011_2018": (date(2011, 1, 1), date(2018, 12, 31)),
    "validation_2019_2022": (date(2019, 1, 1), date(2022, 12, 31)),
    "sealed_2023_plus": (date(2023, 1, 1), None),
    "heldout_2019_plus": (date(2019, 1, 1), None),
}

SLEEVE_ALL: tuple[str, ...] | None = None  # whole-book
SLEEVE_FIN_ONLY = ("Financial",)
SLEEVE_FIN_0050 = ("Financial", "0050")


def book_id_for_alpha(alpha: float) -> str:
    """Canonical observe/paper book ID for constant blend α."""
    a = float(alpha)
    if a <= 0:
        return BOOK_BASE
    if a >= 1:
        return BOOK_FULL
    return f"BLEND_E45_A{int(round(a * 100)):02d}"


def load_market(path: Path = MARKET_PATH) -> pd.DataFrame:
    market = pd.read_csv(path, dtype={"code": str})
    market["date"] = pd.to_datetime(market["date"])
    required = set(ALL + ["TAIEX"])
    complete = market.groupby("date")["code"].apply(lambda s: required.issubset(set(s)))
    return market[market["date"].isin(complete[complete].index)].sort_values(["date", "code"])


def load_dividends(path: Path = DIV_PATH) -> pd.DataFrame:
    return pd.read_csv(path, dtype={"code": str}) if path.exists() else pd.DataFrame()


def e45_full_exposure(market: pd.DataFrame, profile: str = E45_PROFILE_DEFAULT) -> pd.Series:
    close_eq = (
        market[market["code"].isin(ALL)]
        .pivot(index="date", columns="code", values="close")
        .sort_index()
        .ffill()
    )
    return e45.compute_exposure(close_eq, profile)["exposure"].astype(float)


def blend_exposure(full: pd.Series, alpha: float) -> pd.Series | None:
    """exposure = (1−α)·1 + α·E45. α<=0 → None (pure BASE)."""
    a = float(alpha)
    if a <= 0:
        return None
    if a >= 1:
        return full.astype(float)
    return ((1.0 - a) + a * full.astype(float)).clip(0.0, 1.0)


def window_stats(
    nav: pd.DataFrame,
    start: date | None,
    end: date | None,
    *,
    min_days: int = 30,
) -> dict:
    d = nav.copy()
    d["date"] = pd.to_datetime(d["date"]).dt.date
    if start is not None:
        d = d[d["date"] >= start]
    if end is not None:
        d = d[d["date"] <= end]
    d = d.reset_index(drop=True)
    if len(d) < min_days:
        return {
            "cagr": None,
            "max_drawdown": None,
            "utility": None,
            "vol": None,
            "n_days": int(len(d)),
        }
    d = d.copy()
    d["nav"] = d["nav"] / float(d["nav"].iloc[0])
    out = nav_stats(d)
    out["n_days"] = int(len(d))
    return out


def run_early_stack(
    market: pd.DataFrame,
    target: pd.DataFrame,
    regime: pd.Series,
    dividends: pd.DataFrame,
    *,
    e45_exposure: pd.Series | None = None,
    e45_sleeve_names: tuple[str, ...] | None = None,
    sleeve_weight_schedule: pd.DataFrame | None = None,
    cost_multiple: float = 1.0,
):
    """Thin wrapper: Exact T+1 early-stack with first-class cost/sleeve kwargs."""
    return simulate_core(
        market,
        target,
        regime,
        dividends,
        apply_e22=True,
        apply_stock_div=True,
        e45_exposure=e45_exposure,
        e45_sleeve_names=e45_sleeve_names,
        sleeve_weight_schedule=sleeve_weight_schedule,
        cost_multiple=float(cost_multiple),
    )


def deltas_vs_base(
    base_stats: dict,
    other_stats: dict,
    *,
    missing_as_zero: bool = True,
) -> dict:
    mdd_pp = mdd_delta_pp(base_stats.get("max_drawdown"), other_stats.get("max_drawdown"))
    cagr_pp = cagr_delta_pp(
        base_stats.get("cagr"), other_stats.get("cagr"), missing_as_zero=missing_as_zero
    )
    score = None
    if mdd_pp is not None and cagr_pp is not None:
        score = mdd_pp - 0.5 * abs(cagr_pp)
    return {
        "mdd_improve_pp": mdd_pp,
        "cagr_giveback_pp": cagr_pp,
        "score": score,
    }


__all__ = [
    "ROOT",
    "MARKET_PATH",
    "DIV_PATH",
    "E45_PROFILE_DEFAULT",
    "BOOK_BASE",
    "BOOK_BASE_RUNTIME_NOTE",
    "BOOK_FULL",
    "BOOK_BLEND_A25",
    "BOOK_BLEND_A05",
    "CLAIM_STATUS",
    "BANNED_CLAIM_LABELS",
    "WINDOWS_STANDARD",
    "SLEEVE_ALL",
    "SLEEVE_FIN_ONLY",
    "SLEEVE_FIN_0050",
    "book_id_for_alpha",
    "load_market",
    "load_dividends",
    "e45_full_exposure",
    "blend_exposure",
    "window_stats",
    "run_early_stack",
    "deltas_vs_base",
    "e16_features",
]
