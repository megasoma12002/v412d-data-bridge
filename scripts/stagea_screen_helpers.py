#!/usr/bin/env python3
"""Shared Stage A screen I/O — pack windows / tip hygiene / UTC stamp / nav IO.

Research-only. Soft-Frozen live KEEP. Prefer importing these over copy-pasting
``_utc`` / ``_pack`` / ``_tip`` / ``_load_nav`` into new Stage A scripts.

Two tip conventions (do not mix):
- ``tip_hygiene`` — ``cagr_giveback_pp`` = base−chal (historical cool/satellite)
- ``tip_lift`` — ``cagr_lift_pp`` = chal−base (tipsoft / fin_sat Stage A)
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from e45_paper_harness import WINDOWS_STANDARD, window_stats
from fin_sell_quality_helpers import cagr_lift_pp
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp


def utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_nav_csv(path: Path | str) -> pd.DataFrame:
    """Canonical ``date``/``nav`` loader used by tipsoft Stage A screens."""
    df = pd.read_csv(path, parse_dates=["date"])
    return (
        df[["date", "nav"]]
        .assign(
            date=lambda x: pd.to_datetime(x["date"]).dt.normalize(),
            nav=lambda x: x["nav"].astype(float),
        )
        .sort_values("date")
        .reset_index(drop=True)
    )


def returns_from_nav(nav: pd.DataFrame) -> pd.Series:
    s = nav.set_index("date")["nav"].astype(float).sort_index()
    return s.pct_change().fillna(0.0)


def nav_from_returns(r: pd.Series, nav0: float) -> pd.DataFrame:
    nav = (1.0 + r.fillna(0.0)).cumprod() * float(nav0)
    return pd.DataFrame({"date": nav.index, "nav": nav.to_numpy()}).reset_index(drop=True)


def pack_nav_windows(
    nav: pd.DataFrame,
    windows: dict[str, tuple[str, str]] | None = None,
) -> dict[str, Any]:
    """Standard heldout/sealed (etc.) CAGR/MDD pack from a NAV frame."""
    wins = WINDOWS_STANDARD if windows is None else windows
    out: dict[str, Any] = {}
    for k, (a, b) in wins.items():
        st = window_stats(nav, a, b)
        out[k] = {
            "cagr": None if st.get("cagr") is None else round(float(st["cagr"]), 6),
            "max_drawdown": None
            if st.get("max_drawdown") is None
            else round(float(st["max_drawdown"]), 6),
            "n_days": int(st.get("n_days") or 0),
        }
    return out


def tip_hygiene(
    base_nav: pd.DataFrame,
    chal_nav: pd.DataFrame,
) -> dict[str, Any]:
    """YTD + trailing-1y tip pack vs BASE (MDD improve / CAGR giveback).

    ``gate`` is ``PASS`` whenever the window has enough days; score rows apply
    ``tip_mdd_tol_pp`` separately (historical Stage A contract).
    Uses ``cagr_giveback_pp`` (= base−chal pp).
    """
    return _tip_windows(base_nav, chal_nav, lift_mode=False)


def tip_lift(
    base_nav: pd.DataFrame,
    chal_nav: pd.DataFrame,
    *,
    include_gate: bool = False,
) -> dict[str, Any]:
    """YTD + trailing-1y tip pack with ``cagr_lift_pp`` (= chal−base pp).

    Tipsoft / fin_sat Stage A contract. Set ``include_gate=True`` for dual-paper
    observe payloads that also stamp ``gate``.
    """
    return _tip_windows(base_nav, chal_nav, lift_mode=True, include_gate=include_gate)


def _tip_windows(
    base_nav: pd.DataFrame,
    chal_nav: pd.DataFrame,
    *,
    lift_mode: bool,
    include_gate: bool = False,
) -> dict[str, Any]:
    asof = pd.Timestamp(pd.to_datetime(base_nav["date"]).max())
    b_dates = pd.to_datetime(base_nav["date"])
    c_dates = pd.to_datetime(chal_nav["date"])
    out: dict[str, Any] = {}
    cagr_key = "cagr_lift_pp" if lift_mode else "cagr_giveback_pp"
    for wname, start in (
        ("ytd", pd.Timestamp(asof.year, 1, 1)),
        ("trailing_1y", asof - pd.Timedelta(days=365)),
    ):
        b = base_nav[(b_dates >= start) & (b_dates <= asof)].reset_index(drop=True)
        c = chal_nav[(c_dates >= start) & (c_dates <= asof)].reset_index(drop=True)
        if len(b) < 20 or len(c) < 20:
            row: dict[str, Any] = {
                cagr_key: None,
                "mdd_improve_pp": None,
            }
            if include_gate or not lift_mode:
                row["gate"] = "INSUFFICIENT"
            # tip_hygiene always has gate; tipsoft tip_lift historically omits it
            if not lift_mode:
                out[wname] = {
                    "mdd_improve_pp": None,
                    "cagr_giveback_pp": None,
                    "gate": "INSUFFICIENT",
                }
            else:
                out[wname] = row
            continue
        bn = b["nav"].astype(float) / float(b["nav"].iloc[0])
        cn = c["nav"].astype(float) / float(c["nav"].iloc[0])
        b_mdd = float((bn / bn.cummax() - 1.0).min())
        c_mdd = float((cn / cn.cummax() - 1.0).min())
        years = (len(b) - 1) / 252.0
        bc = float(bn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        cc = float(cn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        if lift_mode:
            lift = cagr_lift_pp(bc, cc)
            cagr_pp = None if lift is None else round(float(lift), 4)
        else:
            gb = cagr_delta_pp(bc, cc)
            cagr_pp = None if gb is None else round(float(gb), 4)
        row = {
            cagr_key: cagr_pp,
            "mdd_improve_pp": round(float(mdd_delta_pp(b_mdd, c_mdd)), 4),
        }
        if include_gate or not lift_mode:
            row["gate"] = "PASS"
        if not lift_mode:
            out[wname] = {
                "mdd_improve_pp": row["mdd_improve_pp"],
                "cagr_giveback_pp": cagr_pp,
                "gate": "PASS",
            }
        else:
            out[wname] = row
    return out


def window_delta(
    base_w: dict[str, Any],
    chal_w: dict[str, Any],
    keys: tuple[str, ...] = ("full", "heldout_2019_plus", "sealed_2023_plus"),
) -> dict[str, Any]:
    """Window CAGR lift / MDD improve deltas (tipsoft Stage A contract)."""
    out: dict[str, Any] = {}
    for k in keys:
        b, c = base_w.get(k) or {}, chal_w.get(k) or {}
        lift = cagr_lift_pp(b.get("cagr"), c.get("cagr"))
        out[k] = {
            "cagr_lift_pp": None if lift is None else round(float(lift), 4),
            "mdd_improve_pp": None
            if b.get("max_drawdown") is None or c.get("max_drawdown") is None
            else round(float(mdd_delta_pp(b["max_drawdown"], c["max_drawdown"])), 4),
        }
    return out
