#!/usr/bin/env python3
"""Live FinPriv Gate V7 Bull+Side F05 cutover (forward-only).

Human Class D ballot (2026-09-25):
  ``ACCEPT Class D: FinPriv V7 F05``

Mechanism (paper twin ``V7_REG_BULL_SIDE_F05_KDMAY``):
  - Soft-Frozen stays 3-sleeve router (公股 features / clips KEEP)
  - When regime ∈ {Bull, Sideways}: carve ``priv_frac=0.05`` of Financial
    dollars to FinPriv (PRIV_KD_MAY); remainder FinPub (KD_OPT)
  - When gate off: FinPriv target 0 — sell down any PRIV holdings

Fail-closed: missing/stale FinPriv prices for asof → gate forced off + audit flag.
Does **not** rewrite tip history · broker live-write still PREP-only.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from e16_private_fin_holdings_rescreen import PRIV_R3R4, PUB_R1
from tw_share_lots import BOARD_LOT, board_lots
from within_sleeve_alloc import FIN_PRE_EXDIV_KD

HUMAN_ACCEPT = "ACCEPT Class D: FinPriv V7 F05"
# Nested within-sleeve policies (paper twin): FinPub KD_OPT · FinPriv PRIV_KD_MAY→PRE_EXDIV_KD
PUB_NESTED_POLICY = FIN_PRE_EXDIV_KD
PRIV_NESTED_POLICY = FIN_PRE_EXDIV_KD
LIVE_RECIPE_ID = "LIVE_FINPRIV_V7_REG_BULL_SIDE_F05_KDMAY"
GATE_ID = "REG_BULL_SIDE"
PRIV_FRAC = 0.05
PRIV_POLICY = "PRIV_KD_MAY"
PRIV_KD_MAY = {
    "id": "PRIV_KD_MAY_Klt25_T15",
    "season_start": (5, 1),
    "season_end": (5, 31),
    "k_thresh": 25.0,
    "pre_days": 15,
    "active_score": 1.5,
}
PRIV_CODES = list(PRIV_R3R4)
PUB_CODES = list(PUB_R1)
PRIVATE_ADJ = Path(__file__).resolve().parents[1] / "data/market/private_fin_adjusted.csv"


def gate_reg_bull_side(regime_today: str) -> bool:
    return str(regime_today) in ("Bull", "Sideways")


def load_priv_panel() -> pd.DataFrame:
    if not PRIVATE_ADJ.exists():
        return pd.DataFrame()
    adj = pd.read_csv(PRIVATE_ADJ, dtype={"code": str})
    adj["date"] = pd.to_datetime(adj["date"])
    return adj


def load_priv_prices_for_asof(asof: pd.Timestamp) -> dict[str, float]:
    """Latest available adj/close ≤ asof for PRIV codes (empty if panel missing)."""
    adj = load_priv_panel()
    if adj.empty:
        return {}
    asof = pd.Timestamp(asof).normalize()
    sub = adj[adj["date"] <= asof]
    if sub.empty:
        return {}
    last = sub.sort_values("date").groupby("code", sort=False).tail(1)
    col = "adjusted_close" if "adjusted_close" in last.columns else "adj_close"
    if col not in last.columns:
        return {}
    out: dict[str, float] = {}
    for _, row in last.iterrows():
        c = str(row["code"])
        if c in PRIV_CODES and pd.notna(row[col]):
            out[c] = float(row[col])
    return out


def load_priv_opens_for_asof(asof: pd.Timestamp) -> dict[str, float]:
    """Latest available adj/open ≤ asof for PRIV codes (fallback to close)."""
    adj = load_priv_panel()
    if adj.empty:
        return {}
    asof = pd.Timestamp(asof).normalize()
    sub = adj[adj["date"] <= asof]
    if sub.empty:
        return {}
    last = sub.sort_values("date").groupby("code", sort=False).tail(1)
    out: dict[str, float] = {}
    for _, row in last.iterrows():
        c = str(row["code"])
        if c not in PRIV_CODES:
            continue
        if "adjusted_open" in last.columns and pd.notna(row.get("adjusted_open")):
            out[c] = float(row["adjusted_open"])
        elif "adjusted_close" in last.columns and pd.notna(row.get("adjusted_close")):
            out[c] = float(row["adjusted_close"])
    return out


def priv_prices_fresh_enough(
    asof: pd.Timestamp, max_lag_days: int = 5
) -> tuple[bool, dict[str, Any]]:
    """Require PRIV panel coverage within max_lag calendar days of asof."""
    meta: dict[str, Any] = {"max_lag_days": int(max_lag_days)}
    adj = load_priv_panel()
    if adj.empty:
        meta["reason"] = "missing_private_fin_adjusted"
        return False, meta
    asof = pd.Timestamp(asof).normalize()
    missing = []
    lags = {}
    for c in PRIV_CODES:
        sub = adj[(adj["code"] == c) & (adj["date"] <= asof)]
        if sub.empty:
            missing.append(c)
            continue
        dmax = pd.Timestamp(sub["date"].max()).normalize()
        lag = int((asof - dmax).days)
        lags[c] = lag
        if lag > int(max_lag_days):
            missing.append(c)
    meta["lags"] = lags
    meta["stale_or_missing"] = missing
    ok = len(missing) == 0
    meta["reason"] = None if ok else "stale_or_missing_priv_px"
    return ok, meta


def resolve_gate(
    *,
    regime_today: str,
    asof: pd.Timestamp,
) -> tuple[bool, dict[str, Any]]:
    """Return (gate_on, audit meta). Fail-closed on stale/missing PRIV px."""
    want = gate_reg_bull_side(regime_today)
    fresh, px_meta = priv_prices_fresh_enough(asof)
    meta = {
        "gate_id": GATE_ID,
        "regime": str(regime_today),
        "want_gate": bool(want),
        "priv_frac": float(PRIV_FRAC),
        "priv_policy": PRIV_POLICY,
        "human_accept": HUMAN_ACCEPT,
        "live_recipe_id": LIVE_RECIPE_ID,
        **px_meta,
    }
    if want and not fresh:
        meta["gate_on"] = False
        meta["fin_priv_skipped_missing_px"] = True
        return False, meta
    meta["gate_on"] = bool(want)
    meta["fin_priv_skipped_missing_px"] = False
    return bool(want), meta


def pub_share_for_gate(gate_on: bool) -> float:
    """mix_lambda for FIN_DUAL_PUB_PRIV = FinPub share of Financial dollars."""
    if not gate_on:
        return 1.0
    return float(1.0 - PRIV_FRAC)


def fin_universe_live(gate_enabled: bool) -> list[str]:
    """Codes that may appear in Financial holdings when Class D live."""
    if gate_enabled:
        return list(PUB_CODES) + list(PRIV_CODES)
    return list(PUB_CODES)


def holdings_universe_class_d() -> list[str]:
    """NAV/positions universe when Class D FinPriv live (Soft-Frozen FIN + PRIV)."""
    from e16_soft_frozen_base import FIN, TEL

    return list(FIN) + list(PRIV_CODES) + list(TEL) + ["0050"]


def merge_priv_session_prices(
    prices: dict[str, float],
    *,
    asof: pd.Timestamp,
    opens: dict[str, float] | None = None,
) -> tuple[dict[str, float], dict[str, float] | None, dict[str, Any]]:
    """Merge last PRIV close (and optional open) into session price maps."""
    px = dict(prices)
    priv_closes = load_priv_prices_for_asof(asof)
    px.update(priv_closes)
    op_out = dict(opens) if opens is not None else None
    if op_out is not None:
        op_out.update(load_priv_opens_for_asof(asof))
    meta = {
        "priv_closes_merged": sorted(priv_closes.keys()),
        "n_priv_closes": len(priv_closes),
    }
    return px, op_out, meta


def priv_panel_as_market(asof: pd.Timestamp | None = None) -> pd.DataFrame:
    """Shape private_fin_adjusted as a market fragment for KD / buy_ok panels."""
    adj = load_priv_panel()
    if adj.empty:
        return pd.DataFrame(
            columns=["date", "code", "open", "high", "low", "close", "adj_close", "volume"]
        )
    if asof is not None:
        asof = pd.Timestamp(asof).normalize()
        adj = adj[adj["date"] <= asof]
    out = pd.DataFrame(
        {
            "date": adj["date"],
            "code": adj["code"].astype(str),
            "open": adj.get("adjusted_open", adj.get("adjusted_close")),
            "high": adj.get("adjusted_high", adj.get("adjusted_close")),
            "low": adj.get("adjusted_low", adj.get("adjusted_close")),
            "close": adj["adjusted_close"]
            if "adjusted_close" in adj.columns
            else adj["adj_close"],
            "adj_close": adj["adjusted_close"]
            if "adjusted_close" in adj.columns
            else adj["adj_close"],
            "volume": adj.get("volume", 0),
        }
    )
    return out[out["code"].isin(PRIV_CODES)].copy()


def force_sell_priv_order_rows(
    *,
    pos: dict[str, float],
    prices: dict[str, float],
    signal_date: date,
    make_order_id,
) -> list[dict[str, Any]]:
    """Gate-off unwind: SELL all PRIV board lots held (skip names without price)."""
    rows: list[dict[str, Any]] = []
    for c in PRIV_CODES:
        qty = board_lots(float(pos.get(c, 0)))
        if qty < BOARD_LOT:
            continue
        px = float(prices.get(c, 0.0) or 0.0)
        if px <= 0:
            continue
        oid = make_order_id(signal_date=signal_date, code=c, side="SELL")
        rows.append(
            {
                "order_id": oid,
                "signal_date": signal_date.isoformat(),
                "code": c,
                "side": "SELL",
                "quantity": int(qty),
                "reference_close": px,
            }
        )
    return rows
