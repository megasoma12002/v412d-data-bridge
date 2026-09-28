#!/usr/bin/env python3
"""Paper-only FIN sell-quality overlays (Stage A).

Hard ``fin_sell_ok`` gates on top of live SELL_a75 scores.
CAGR lift = chal − base (negate helper giveback). Soft-Frozen / tip untouched.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from fin_buy_quality_helpers import (
    catalog_gate,
    close_panel,
    cool1_buy_ok,
    not_gate,
    raw_close_panel,
    ret_sign_ok,
)
from ta_indicator_catalog import rsi


def above_ma_ok(closes: pd.DataFrame, window: int) -> pd.DataFrame:
    out = pd.DataFrame(False, index=closes.index, columns=closes.columns)
    w = int(window)
    for c in closes.columns:
        s = closes[c].astype(float)
        ma = s.rolling(w, min_periods=w).mean()
        out[c] = (s > ma).fillna(False)
    return out


def rsi_gt_ok(closes: pd.DataFrame, thresh: float, n: int = 14) -> pd.DataFrame:
    out = pd.DataFrame(False, index=closes.index, columns=closes.columns)
    for c in closes.columns:
        out[c] = (rsi(closes[c].astype(float), n=int(n)) > float(thresh)).fillna(False)
    return out


def cagr_lift_pp(base_cagr: float | None, chal_cagr: float | None) -> float | None:
    """Challenger − base in pp. Uses research helper giveback (base−chal) then negates."""
    from research_metric_helpers import cagr_delta_pp

    gb = cagr_delta_pp(base_cagr, chal_cagr)
    if gb is None:
        return None
    return float(-float(gb))


def forward_sell_win_stats(
    fills: pd.DataFrame,
    closes: pd.DataFrame,
    *,
    codes: set[str],
    horizon: int = 21,
) -> dict[str, Any]:
    """Sell win = fwd adj-close return < 0 after ``horizon`` (price fell after sell)."""
    if fills is None or fills.empty:
        return {"n": 0, "wins": 0, "win_rate": None, "mean_fwd": None}
    f = fills.copy()
    f["code"] = f["code"].astype(str)
    f["side"] = f["side"].astype(str).str.upper()
    date_col = "fill_date" if "fill_date" in f.columns else "date"
    f[date_col] = pd.to_datetime(f[date_col]).dt.normalize()
    f = f[(f["side"] == "SELL") & (f["code"].isin({str(c) for c in codes}))]
    if f.empty:
        return {"n": 0, "wins": 0, "win_rate": None, "mean_fwd": None}

    idx = closes.index
    pos = {pd.Timestamp(d).normalize(): i for i, d in enumerate(idx)}
    wins = 0
    rets: list[float] = []
    for _, row in f.iterrows():
        d = pd.Timestamp(row[date_col]).normalize()
        c = str(row["code"])
        if c not in closes.columns or d not in pos:
            continue
        i0 = pos[d]
        i1 = i0 + int(horizon)
        if i1 >= len(idx):
            continue
        px0 = float(closes.iloc[i0][c])
        px1 = float(closes.iloc[i1][c])
        if not np.isfinite(px0) or not np.isfinite(px1) or px0 <= 0:
            continue
        r = px1 / px0 - 1.0
        rets.append(r)
        if r < 0.0:
            wins += 1
    n = len(rets)
    if n < 1:
        return {"n": 0, "wins": 0, "win_rate": None, "mean_fwd": None}
    return {
        "n": int(n),
        "wins": int(wins),
        "win_rate": round(100.0 * wins / n, 4),
        "mean_fwd": round(float(np.mean(rets)) * 100.0, 4),
    }


__all__ = [
    "above_ma_ok",
    "cagr_lift_pp",
    "catalog_gate",
    "close_panel",
    "cool1_buy_ok",
    "forward_sell_win_stats",
    "not_gate",
    "raw_close_panel",
    "ret_sign_ok",
    "rsi_gt_ok",
]
