#!/usr/bin/env python3
"""Shared Stage A screen I/O — pack windows / tip hygiene / UTC stamp.

Research-only. Soft-Frozen live KEEP. Prefer importing these over copy-pasting
``_utc`` / ``_pack`` / ``_tip`` into new Stage A scripts.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd

from e45_paper_harness import WINDOWS_STANDARD, window_stats
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp


def utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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
    """
    asof = pd.Timestamp(pd.to_datetime(base_nav["date"]).max())
    b_dates = pd.to_datetime(base_nav["date"])
    c_dates = pd.to_datetime(chal_nav["date"])
    out: dict[str, Any] = {}
    for wname, start in (
        ("ytd", pd.Timestamp(asof.year, 1, 1)),
        ("trailing_1y", asof - pd.Timedelta(days=365)),
    ):
        b = base_nav[(b_dates >= start) & (b_dates <= asof)].reset_index(drop=True)
        c = chal_nav[(c_dates >= start) & (c_dates <= asof)].reset_index(drop=True)
        if len(b) < 20 or len(c) < 20:
            out[wname] = {
                "mdd_improve_pp": None,
                "cagr_giveback_pp": None,
                "gate": "INSUFFICIENT",
            }
            continue
        bn = b["nav"].astype(float) / float(b["nav"].iloc[0])
        cn = c["nav"].astype(float) / float(c["nav"].iloc[0])
        b_mdd = float((bn / bn.cummax() - 1.0).min())
        c_mdd = float((cn / cn.cummax() - 1.0).min())
        years = (len(b) - 1) / 252.0
        bc = float(bn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        cc = float(cn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        gb = cagr_delta_pp(bc, cc)
        out[wname] = {
            "mdd_improve_pp": round(float(mdd_delta_pp(b_mdd, c_mdd)), 4),
            "cagr_giveback_pp": None if gb is None else round(float(gb), 4),
            "gate": "PASS",
        }
    return out
