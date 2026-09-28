#!/usr/bin/env python3
"""Paper-only FIN buy-quality overlays (Stage A/B).

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


def or_buy_ok(a: pd.DataFrame, b: pd.DataFrame) -> pd.DataFrame:
    x = a.fillna(False).astype(bool)
    y = b.reindex(index=x.index, columns=x.columns).fillna(False).astype(bool)
    return x | y


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


def below_ma_ok(closes: pd.DataFrame, window: int) -> pd.DataFrame:
    out = pd.DataFrame(False, index=closes.index, columns=closes.columns)
    w = int(window)
    for c in closes.columns:
        s = closes[c].astype(float)
        ma = s.rolling(w, min_periods=w).mean()
        out[c] = (s < ma).fillna(False)
    return out


def kd_season_mask(
    cal: pd.DatetimeIndex,
    *,
    season_start: tuple[int, int],
    season_end: tuple[int, int],
) -> pd.Series:
    """Boolean series True on calendar days inside [start, end] inclusive (month/day)."""
    sm, sd = int(season_start[0]), int(season_start[1])
    em, ed = int(season_end[0]), int(season_end[1])
    out = []
    for d in cal:
        md = (int(d.month), int(d.day))
        if (sm, sd) <= (em, ed):
            ok = (sm, sd) <= md <= (em, ed)
        else:
            ok = md >= (sm, sd) or md <= (em, ed)
        out.append(bool(ok))
    return pd.Series(out, index=cal, dtype=bool)


def apply_filter_in_season(
    gate: pd.DataFrame,
    season: pd.Series,
    *,
    in_season: bool,
) -> pd.DataFrame:
    """When season matches, require ``gate``; otherwise pass-through True."""
    s = season.reindex(gate.index).fillna(False).astype(bool)
    if not in_season:
        s = ~s
    out = pd.DataFrame(True, index=gate.index, columns=gate.columns)
    g = gate.fillna(False).astype(bool)
    for c in out.columns:
        out[c] = np.where(s.values, g[c].values, True)
    return out.astype(bool)


def forward_win_stats(
    fills: pd.DataFrame,
    closes: pd.DataFrame,
    *,
    codes: set[str],
    side: str = "BUY",
    horizon: int = 21,
) -> dict[str, Any]:
    """Fraction of fills with fwd adj-close return > 0 after ``horizon`` rows."""
    if fills is None or fills.empty:
        return {"n": 0, "wins": 0, "win_rate": None, "mean_fwd": None}
    f = fills.copy()
    f["code"] = f["code"].astype(str)
    f["side"] = f["side"].astype(str).str.upper()
    date_col = "fill_date" if "fill_date" in f.columns else "date"
    f[date_col] = pd.to_datetime(f[date_col]).dt.normalize()
    f = f[(f["side"] == str(side).upper()) & (f["code"].isin({str(c) for c in codes}))]
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
