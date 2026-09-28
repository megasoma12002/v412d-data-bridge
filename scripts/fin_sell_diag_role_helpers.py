#!/usr/bin/env python3
"""FIN sell **diagnostic role** helpers — label fills; never gate ``fin_sell_ok``.

Attribute panels for conditional sell win-rate on live SELL_a75 fills only.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from ta_indicator_catalog import macd_hist


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


def raw_ohlcv_panels(
    market: pd.DataFrame, cal: pd.DatetimeIndex, codes: list[str]
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    close = pd.DataFrame(index=cal, columns=list(codes), dtype=float)
    high = pd.DataFrame(index=cal, columns=list(codes), dtype=float)
    low = pd.DataFrame(index=cal, columns=list(codes), dtype=float)
    vol = pd.DataFrame(index=cal, columns=list(codes), dtype=float)
    for c in codes:
        m = market[market["code"].astype(str) == str(c)].copy()
        if m.empty:
            continue
        m["date"] = pd.to_datetime(m["date"]).dt.normalize()
        m = m.drop_duplicates("date").set_index("date").sort_index()
        close[c] = pd.to_numeric(m["close"], errors="coerce").reindex(cal)
        high[c] = pd.to_numeric(m["high"], errors="coerce").reindex(cal)
        low[c] = pd.to_numeric(m["low"], errors="coerce").reindex(cal)
        vol[c] = pd.to_numeric(m["volume"], errors="coerce").reindex(cal)
    return close, high, low, vol


def persist_ok(panel: pd.DataFrame, n: int) -> pd.DataFrame:
    p = panel.fillna(False).astype(bool)
    n = int(n)
    if n <= 1:
        return p
    acc = p.astype(int)
    for lag in range(1, n):
        acc = acc + p.shift(lag).fillna(False).astype(bool).astype(int)
    return (acc >= n).astype(bool)


def down_days_ok(closes: pd.DataFrame, n: int) -> pd.DataFrame:
    ret = closes.pct_change(1)
    neg = (ret < 0.0).fillna(False)
    return persist_ok(neg, int(n))


def breakdown_ok(closes: pd.DataFrame, lows: pd.DataFrame, window: int) -> pd.DataFrame:
    w = int(window)
    prior_low = lows.shift(1).rolling(w, min_periods=w).min()
    return (closes.astype(float) < prior_low.astype(float)).fillna(False)


def volume_spike_ok(volume: pd.DataFrame, *, ma: int = 20, mult: float = 1.5) -> pd.DataFrame:
    out = pd.DataFrame(False, index=volume.index, columns=volume.columns)
    for c in volume.columns:
        v = volume[c].astype(float)
        m = v.rolling(int(ma), min_periods=int(ma)).mean()
        out[c] = (v > float(mult) * m).fillna(False)
    return out


def atr14(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
    prev = close.shift(1)
    tr = pd.concat(
        [(high - low).abs(), (high - prev).abs(), (low - prev).abs()],
        axis=1,
    ).max(axis=1)
    return tr.rolling(14, min_periods=14).mean()


def atr_expand_ok(
    high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame, *, lookback: int = 5
) -> pd.DataFrame:
    out = pd.DataFrame(False, index=close.index, columns=close.columns)
    lb = int(lookback)
    for c in close.columns:
        a = atr14(high[c].astype(float), low[c].astype(float), close[c].astype(float))
        out[c] = (a > a.shift(lb)).fillna(False)
    return out


def macd_flip_neg_ok(closes: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(False, index=closes.index, columns=closes.columns)
    for c in closes.columns:
        h = macd_hist(closes[c].astype(float))
        out[c] = ((h < 0.0) & (h.shift(1) >= 0.0)).fillna(False)
    return out


def sell_fill_forward_rows(
    fills: pd.DataFrame,
    closes: pd.DataFrame,
    *,
    codes: set[str],
    horizon: int = 21,
) -> pd.DataFrame:
    """One row per evaluable FIN SELL fill with fwd return / win flag."""
    if fills is None or fills.empty:
        return pd.DataFrame(columns=["fill_date", "code", "fwd_ret", "win"])
    f = fills.copy()
    f["code"] = f["code"].astype(str)
    f["side"] = f["side"].astype(str).str.upper()
    date_col = "fill_date" if "fill_date" in f.columns else "date"
    f[date_col] = pd.to_datetime(f[date_col]).dt.normalize()
    f = f[(f["side"] == "SELL") & (f["code"].isin({str(c) for c in codes}))].copy()
    if f.empty:
        return pd.DataFrame(columns=["fill_date", "code", "fwd_ret", "win"])

    idx = closes.index
    pos = {pd.Timestamp(d).normalize(): i for i, d in enumerate(idx)}
    rows: list[dict[str, Any]] = []
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
        rows.append(
            {
                "fill_date": d,
                "code": c,
                "fwd_ret": float(r),
                "win": bool(r < 0.0),
            }
        )
    return pd.DataFrame(rows)


def lookup_attr(panel: pd.DataFrame, date: pd.Timestamp, code: str) -> bool:
    d = pd.Timestamp(date).normalize()
    c = str(code)
    if c not in panel.columns or d not in panel.index:
        return False
    return bool(panel.loc[d, c])


def conditional_wr(
    events: pd.DataFrame,
    mask: pd.Series,
    *,
    base_rate: float,
) -> dict[str, Any]:
    """Win-rate on ``mask`` True subset vs unconditional ``base_rate`` (percent)."""
    m = mask.fillna(False).astype(bool)
    sub = events.loc[m]
    n = int(len(sub))
    if n < 1:
        return {
            "n": 0,
            "wins": 0,
            "win_rate": None,
            "wr_lift_pp": None,
            "coverage": 0.0,
            "mean_fwd": None,
        }
    wins = int(sub["win"].sum())
    rate = 100.0 * wins / n
    cov = 100.0 * n / max(len(events), 1)
    return {
        "n": n,
        "wins": wins,
        "win_rate": round(rate, 4),
        "wr_lift_pp": round(rate - float(base_rate), 4),
        "coverage": round(cov, 4),
        "mean_fwd": round(float(sub["fwd_ret"].mean()) * 100.0, 4),
    }


__all__ = [
    "atr_expand_ok",
    "breakdown_ok",
    "close_panel",
    "conditional_wr",
    "down_days_ok",
    "lookup_attr",
    "macd_flip_neg_ok",
    "persist_ok",
    "raw_ohlcv_panels",
    "sell_fill_forward_rows",
    "volume_spike_ok",
]
