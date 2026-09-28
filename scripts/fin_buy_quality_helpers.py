#!/usr/bin/env python3
"""Paper-only FIN buy-quality overlays (Stage A).

AND-filters on ``fin_buy_ok`` + forward win-rate diagnostics.
Soft-Frozen / live tip untouched.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from ta_indicator_catalog import rsi


def close_panel(market: pd.DataFrame, cal: pd.DatetimeIndex, codes: list[str]) -> pd.DataFrame:
    out = pd.DataFrame(index=cal, columns=list(codes), dtype=float)
    for c in codes:
        m = market[market["code"].astype(str) == str(c)].copy()
        if m.empty:
            continue
        m["date"] = pd.to_datetime(m["date"]).dt.normalize()
        m = m.drop_duplicates("date").set_index("date").sort_index()
        if "adj_close" in m.columns and m["adj_close"].notna().any():
            s = m["adj_close"].astype(float)
        else:
            s = m["close"].astype(float)
        out[c] = s.reindex(cal)
    return out


def and_buy_ok(base: pd.DataFrame, extra: pd.DataFrame) -> pd.DataFrame:
    b = base.astype(bool).copy()
    e = extra.reindex(index=b.index, columns=b.columns).fillna(False).astype(bool)
    return b & e


def ret_sign_ok(
    closes: pd.DataFrame,
    *,
    n: int,
    positive: bool,
) -> pd.DataFrame:
    ret = closes.pct_change(int(n))
    if positive:
        return (ret > 0.0).fillna(False)
    return (ret < 0.0).fillna(False)


def catalog_gate(panel: pd.DataFrame) -> pd.DataFrame:
    return panel.fillna(False).astype(bool)


def not_gate(panel: pd.DataFrame) -> pd.DataFrame:
    return (~panel.fillna(False).astype(bool))


def cool1_buy_ok(cal: pd.DatetimeIndex, codes: list[str], cool: pd.Series) -> pd.DataFrame:
    c = cool.reindex(cal).fillna(1.0).astype(float)
    ok_day = c >= 1.0 - 1e-12
    out = pd.DataFrame(False, index=cal, columns=list(codes))
    for col in out.columns:
        out[col] = ok_day.values
    return out


def rsi_lt_ok(closes: pd.DataFrame, thresh: float = 50.0, n: int = 14) -> pd.DataFrame:
    out = pd.DataFrame(False, index=closes.index, columns=closes.columns)
    for c in closes.columns:
        out[c] = (rsi(closes[c].astype(float), n=int(n)) < float(thresh)).fillna(False)
    return out


def forward_win_stats(
    fills: pd.DataFrame,
    closes: pd.DataFrame,
    *,
    codes: set[str],
    side: str = "BUY",
    horizon: int = 21,
) -> dict[str, Any]:
    """Fraction of fills with fwd close return > 0 after ``horizon`` calendar rows."""
    if fills is None or fills.empty:
        return {"n": 0, "wins": 0, "win_rate": None, "mean_fwd": None}
    f = fills.copy()
    f["code"] = f["code"].astype(str)
    f["side"] = f["side"].astype(str).str.upper()
    f["date"] = pd.to_datetime(f["date"]).dt.normalize()
    f = f[(f["side"] == str(side).upper()) & (f["code"].isin(set(codes)))]
    if f.empty:
        return {"n": 0, "wins": 0, "win_rate": None, "mean_fwd": None}

    idx = closes.index
    pos = {d: i for i, d in enumerate(idx)}
    wins = 0
    rets: list[float] = []
    for _, row in f.iterrows():
        d = pd.Timestamp(row["date"]).normalize()
        c = str(row["code"])
        if c not in closes.columns or d not in pos:
            continue
        i0 = pos[d]
        i1 = i0 + int(horizon)
        if i1 >= len(idx):
            continue
        px0 = float(row.get("fill_price") or row.get("price") or np.nan)
        if not np.isfinite(px0) or px0 <= 0:
            px0 = float(closes.iloc[i0][c])
        px1 = float(closes.iloc[i1][c])
        if not np.isfinite(px0) or not np.isfinite(px1) or px0 <= 0:
            continue
        r = px1 / px0 - 1.0
        rets.append(r)
        if r > 0.0:
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
