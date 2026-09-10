#!/usr/bin/env python3
"""Finite market-standard TA catalog for buy-low / sell-high gates (PAPER).

Causal daily OHLCV only. Used by indicator combo screens.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from tw_yahoo_kd import yahoo_kd


def rsi(close: pd.Series, n: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)
    avg_gain = gain.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    avg_loss = loss.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    return 100.0 - (100.0 / (1.0 + rs))


def macd_hist(close: pd.Series) -> pd.Series:
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    line = ema12 - ema26
    return line - line.ewm(span=9, adjust=False).mean()


def williams_r(high: pd.Series, low: pd.Series, close: pd.Series, n: int = 14) -> pd.Series:
    hh = high.rolling(n, min_periods=n).max()
    ll = low.rolling(n, min_periods=n).min()
    return -100.0 * (hh - close) / (hh - ll).replace(0.0, np.nan)


def cci(high: pd.Series, low: pd.Series, close: pd.Series, n: int = 20) -> pd.Series:
    tp = (high + low + close) / 3.0
    sma = tp.rolling(n, min_periods=n).mean()
    mad = (tp - sma).abs().rolling(n, min_periods=n).mean()
    return (tp - sma) / (0.015 * mad.replace(0.0, np.nan))


def mfi(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, n: int = 14) -> pd.Series:
    tp = (high + low + close) / 3.0
    mf = tp * volume
    delta = tp.diff()
    pos = mf.where(delta > 0.0, 0.0)
    neg = mf.where(delta < 0.0, 0.0)
    pos_sum = pos.rolling(n, min_periods=n).sum()
    neg_sum = neg.rolling(n, min_periods=n).sum().replace(0.0, np.nan)
    ratio = pos_sum / neg_sum
    return 100.0 - (100.0 / (1.0 + ratio))


def bool_panel(cal: pd.DatetimeIndex, codes: list[str]) -> pd.DataFrame:
    return pd.DataFrame(False, index=cal, columns=list(codes))


LOW_IDS = [
    "RSI14_LT30",
    "RSI6_LT20",
    "K9_LT20",
    "K9_LT30",
    "D9_LT20",
    "WILLR14_LT_N80",
    "CCI20_LT_N100",
    "BB_LOWER",
    "BB_PCTB_LT0",
    "BELOW_MA20",
    "BELOW_MA60",
    "BELOW_MA120",
    "MACD_HIST_NEG",
    "BIAS20_LT_N5",
    "MFI14_LT20",
    "ROC10_LT_N5",
]

HIGH_IDS = [
    "RSI14_GT70",
    "RSI6_GT80",
    "K9_GT70",
    "K9_GT80",
    "D9_GT80",
    "WILLR14_GT_N20",
    "CCI20_GT100",
    "BB_UPPER",
    "BB_PCTB_GT1",
    "ABOVE_MA20",
    "ABOVE_MA60",
    "MACD_HIST_POS",
    "BIAS20_GT5",
    "MFI14_GT80",
    "ROC10_GT5",
]


def build_low_high_catalog(
    market: pd.DataFrame, cal: pd.DatetimeIndex, codes: list[str]
) -> tuple[dict[str, pd.DataFrame], dict[str, pd.DataFrame]]:
    m = market.copy()
    m["date"] = pd.to_datetime(m["date"])
    m["code"] = m["code"].astype(str)
    lows = {k: bool_panel(cal, codes) for k in LOW_IDS}
    highs = {k: bool_panel(cal, codes) for k in HIGH_IDS}

    for c in codes:
        g = (
            m[m["code"] == c]
            .sort_values("date")
            .drop_duplicates("date")
            .set_index("date")
            .reindex(cal)
        )
        close = pd.to_numeric(g["close"], errors="coerce")
        high = pd.to_numeric(g["high"], errors="coerce").fillna(close)
        low = pd.to_numeric(g["low"], errors="coerce").fillna(close)
        vol = pd.to_numeric(g["volume"], errors="coerce").fillna(0.0)
        r14 = rsi(close, 14)
        r6 = rsi(close, 6)
        kd = yahoo_kd(high, low, close, n=9)
        k9, d9 = kd["k"], kd["d"]
        wr = williams_r(high, low, close, 14)
        cc = cci(high, low, close, 20)
        mid = close.rolling(20, min_periods=20).mean()
        sd = close.rolling(20, min_periods=20).std()
        upper = mid + 2.0 * sd
        lower = mid - 2.0 * sd
        pctb = (close - lower) / (upper - lower).replace(0.0, np.nan)
        ma20 = close.rolling(20, min_periods=20).mean()
        ma60 = close.rolling(60, min_periods=60).mean()
        ma120 = close.rolling(120, min_periods=120).mean()
        hist = macd_hist(close)
        bias20 = (close - ma20) / ma20.replace(0.0, np.nan) * 100.0
        mf = mfi(high, low, close, vol, 14)
        roc10 = close.pct_change(10) * 100.0

        lows["RSI14_LT30"][c] = (r14 < 30.0).fillna(False)
        lows["RSI6_LT20"][c] = (r6 < 20.0).fillna(False)
        lows["K9_LT20"][c] = (k9 < 20.0).fillna(False)
        lows["K9_LT30"][c] = (k9 < 30.0).fillna(False)
        lows["D9_LT20"][c] = (d9 < 20.0).fillna(False)
        lows["WILLR14_LT_N80"][c] = (wr < -80.0).fillna(False)
        lows["CCI20_LT_N100"][c] = (cc < -100.0).fillna(False)
        lows["BB_LOWER"][c] = (close < lower).fillna(False)
        lows["BB_PCTB_LT0"][c] = (pctb < 0.0).fillna(False)
        lows["BELOW_MA20"][c] = (close < ma20).fillna(False)
        lows["BELOW_MA60"][c] = (close < ma60).fillna(False)
        lows["BELOW_MA120"][c] = (close < ma120).fillna(False)
        lows["MACD_HIST_NEG"][c] = (hist < 0.0).fillna(False)
        lows["BIAS20_LT_N5"][c] = (bias20 < -5.0).fillna(False)
        lows["MFI14_LT20"][c] = (mf < 20.0).fillna(False)
        lows["ROC10_LT_N5"][c] = (roc10 < -5.0).fillna(False)

        highs["RSI14_GT70"][c] = (r14 > 70.0).fillna(False)
        highs["RSI6_GT80"][c] = (r6 > 80.0).fillna(False)
        highs["K9_GT70"][c] = (k9 > 70.0).fillna(False)
        highs["K9_GT80"][c] = (k9 > 80.0).fillna(False)
        highs["D9_GT80"][c] = (d9 > 80.0).fillna(False)
        highs["WILLR14_GT_N20"][c] = (wr > -20.0).fillna(False)
        highs["CCI20_GT100"][c] = (cc > 100.0).fillna(False)
        highs["BB_UPPER"][c] = (close > upper).fillna(False)
        highs["BB_PCTB_GT1"][c] = (pctb > 1.0).fillna(False)
        highs["ABOVE_MA20"][c] = (close > ma20).fillna(False)
        highs["ABOVE_MA60"][c] = (close > ma60).fillna(False)
        highs["MACD_HIST_POS"][c] = (hist > 0.0).fillna(False)
        highs["BIAS20_GT5"][c] = (bias20 > 5.0).fillna(False)
        highs["MFI14_GT80"][c] = (mf > 80.0).fillna(False)
        highs["ROC10_GT5"][c] = (roc10 > 5.0).fillna(False)

    return lows, highs


def combine_or(panels: list[pd.DataFrame], cal: pd.DatetimeIndex, codes: list[str]) -> pd.DataFrame:
    out = bool_panel(cal, codes)
    for p in panels:
        out = out | p.reindex(index=cal, columns=codes).fillna(False)
    return out


def combine_and(panels: list[pd.DataFrame], cal: pd.DatetimeIndex, codes: list[str]) -> pd.DataFrame:
    out = pd.DataFrame(True, index=cal, columns=list(codes))
    for p in panels:
        out = out & p.reindex(index=cal, columns=codes).fillna(False)
    return out


def combine_majority(
    panels: list[pd.DataFrame], cal: pd.DatetimeIndex, codes: list[str], *, k: int
) -> pd.DataFrame:
    acc = pd.DataFrame(0, index=cal, columns=list(codes), dtype=int)
    for p in panels:
        acc = acc + p.reindex(index=cal, columns=codes).fillna(False).astype(int)
    return acc >= int(k)


__all__ = [
    "LOW_IDS",
    "HIGH_IDS",
    "build_low_high_catalog",
    "combine_or",
    "combine_and",
    "combine_majority",
]
