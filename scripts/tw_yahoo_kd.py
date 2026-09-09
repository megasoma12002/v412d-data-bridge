"""Yahoo Finance Taiwan KD (K9/D9) — recursive form used on tw.stock.yahoo.com.

RSV(n) = 100 * (C - L_n) / (H_n - L_n)
K_t = (2/3)*K_{t-1} + (1/3)*RSV_t
D_t = (2/3)*D_{t-1} + (1/3)*K_t
J_t = 3*K_t - 2*D_t   (often labeled K3D2 on Yahoo)

The trailing \"9\" in K9/D9 is the RSV lookback, not SMA(9) of RSV.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def yahoo_kd(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    *,
    n: int = 9,
    seed: float | None = None,
) -> pd.DataFrame:
    """Return DataFrame columns: rsv, k, d, j (index aligned to close)."""
    high = pd.to_numeric(high, errors="coerce")
    low = pd.to_numeric(low, errors="coerce")
    close = pd.to_numeric(close, errors="coerce")
    hh = high.rolling(n, min_periods=n).max()
    ll = low.rolling(n, min_periods=n).min()
    denom = (hh - ll).replace(0, np.nan)
    rsv = (close - ll) / denom * 100.0

    k = np.full(len(close), np.nan, dtype=float)
    d = np.full(len(close), np.nan, dtype=float)
    started = False
    prev_k = 50.0 if seed is None else float(seed)
    prev_d = 50.0 if seed is None else float(seed)
    rsv_vals = rsv.to_numpy(dtype=float)
    for i, r in enumerate(rsv_vals):
        if not np.isfinite(r):
            continue
        if not started:
            prev_k = prev_d = float(r) if seed is None else float(seed)
            started = True
        else:
            prev_k = (2.0 / 3.0) * prev_k + (1.0 / 3.0) * float(r)
            prev_d = (2.0 / 3.0) * prev_d + (1.0 / 3.0) * prev_k
        k[i] = prev_k
        d[i] = prev_d

    out = pd.DataFrame(
        {
            "rsv": rsv.to_numpy(dtype=float),
            "k": k,
            "d": d,
        },
        index=close.index,
    )
    out["j"] = 3.0 * out["k"] - 2.0 * out["d"]
    return out


__all__ = ["yahoo_kd"]
