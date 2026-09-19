#!/usr/bin/env python3
"""Live 民營 native universe helpers (ACCEPT 2026-09-19).

When ``LiveConfig.live_fin_priv_native`` is True, Soft-Frozen FIN dollars route to
``PRIV_R3R4`` with within-sleeve ``PRIV_KD_MAY_Klt25_T15``. Live market is extended
from ``data/market/private_fin_adjusted.csv`` when priv codes are absent.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from within_sleeve_alloc import FIN_PRE_EXDIV_KD

HUMAN_ACCEPT = "ACCEPT live FIN 民營 native cutover: PRIV_KD_MAY_Klt25_T15"
PRIV_KD = {
    "id": "PRIV_KD_MAY_Klt25_T15",
    "season_start": (5, 1),
    "season_end": (5, 31),
    "k_thresh": 25.0,
    "pre_days": 15,
    "active_score": 1.5,
}
PRIV_FIN = ["2884", "2885", "2890", "2891", "2881", "2882"]
TEL = ["2412", "3045", "4904"]
ROOT = Path(__file__).resolve().parents[1]
PRIVATE_ADJ = ROOT / "data/market/private_fin_adjusted.csv"


def _panel_from_private_adj() -> pd.DataFrame:
    """Synthesize raw OHLCV from ``private_fin_adjusted`` when TW12 is absent."""
    adj = pd.read_csv(PRIVATE_ADJ, dtype={"code": str})
    adj["date"] = pd.to_datetime(adj["date"])
    ac = adj["adjusted_close"].astype(float)
    rc = adj["raw_close"].astype(float)
    factor = rc / ac.replace(0.0, pd.NA)
    factor = factor.fillna(1.0)
    return pd.DataFrame(
        {
            "date": adj["date"],
            "code": adj["code"].astype(str),
            "open": adj["adjusted_open"].astype(float) * factor,
            "high": adj["adjusted_high"].astype(float) * factor,
            "low": adj["adjusted_low"].astype(float) * factor,
            "close": rc,
            "volume": adj["volume"].astype(float),
            "adj_close": ac,
        }
    )


def extend_market_for_priv(market: pd.DataFrame) -> pd.DataFrame:
    """Ensure PRIV_R3R4 rows exist by merging private_fin_adjusted panel.

    When priv tip lags Soft-Frozen tip, forward-fill last priv OHLCV onto live
    calendar dates so the session can price PRIV_R3R4 (ops debt until priv feed catches up).
    """
    m = market.copy()
    m["code"] = m["code"].astype(str)
    m["date"] = pd.to_datetime(m["date"])
    have = set(m["code"])
    need = [c for c in PRIV_FIN if c not in have]
    live_dates = pd.DatetimeIndex(sorted(m["date"].unique()))
    if not PRIVATE_ADJ.exists():
        raise SystemExit(
            f"live_fin_priv_native requires priv OHLCV; missing {PRIVATE_ADJ} "
            f"(need codes {need or PRIV_FIN})"
        )
    extra = _panel_from_private_adj()
    extra = extra[extra["code"].isin(PRIV_FIN)].copy()
    # Align columns with live market when possible.
    for col in m.columns:
        if col not in extra.columns:
            extra[col] = pd.NA
    cols = [c for c in m.columns if c in extra.columns]
    extra = extra[cols]
    # Forward-fill each priv code onto the live Soft-Frozen calendar.
    filled_parts: list[pd.DataFrame] = []
    for code in PRIV_FIN:
        sub = extra[extra["code"] == code].sort_values("date")
        if sub.empty:
            raise SystemExit(f"live_fin_priv_native: no rows for {code} in {PRIVATE_ADJ}")
        sub = sub.set_index("date").reindex(live_dates)
        sub["code"] = code
        # ffill OHLCV; remaining leading NaNs use first available.
        num_cols = [c for c in sub.columns if c not in {"code"}]
        sub[num_cols] = sub[num_cols].ffill().bfill()
        sub = sub.reset_index().rename(columns={"index": "date"})
        filled_parts.append(sub)
    priv_panel = pd.concat(filled_parts, ignore_index=True)
    # Drop any existing priv rows then concat filled panel (prefer filled tip).
    m = m[~m["code"].isin(PRIV_FIN)]
    out = pd.concat([m, priv_panel], ignore_index=True)
    return out.sort_values(["date", "code"]).drop_duplicates(["date", "code"], keep="last")


def apply_priv_universe_globals() -> tuple[list[str], list[str]]:
    """Patch e50 / soft_frozen / live_ledger FIN lists for the process; return (fin, all)."""
    import e16_soft_frozen_base as soft
    import e50_early_stack_combined_nav as e50
    import live_ledger as ll
    import live_strategy_targets as lst

    fin = list(PRIV_FIN)
    all_codes = list(PRIV_FIN) + TEL + ["0050"]
    soft.FIN = fin
    e50.FIN = fin
    e50.ALL = all_codes
    ll.ALL = all_codes
    lst.ALL = all_codes
    return fin, all_codes


def priv_kd_policy() -> str:
    """Within-sleeve policy id (KD season params live in PRIV_KD / live_config)."""
    return FIN_PRE_EXDIV_KD
