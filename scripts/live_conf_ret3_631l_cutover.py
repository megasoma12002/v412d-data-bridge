#!/usr/bin/env python3
"""Live CONF_RET3_A10_H5 × 00631L short-assist cutover (forward-only).

Human ballot (2026-09-26):
  ``CONF_RET3_A10_H5 accept live``
  Normalized: ``ACCEPT Live cutover: CONF_RET3_A10_H5 (00631L short-assist under COOL)``

Paper twin: COOL exit · 0050 RET3>0 confirm · α=0.10 · H=5 · OFF=`00631L`.
Soft-Frozen clips / FUSE / COOL / SELL_a75 / FinPriv V7 **KEEP**.
Does **not** rewrite tip history · broker live-write still PREP-only.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any, Callable

import pandas as pd

import cool_t50_lev_rebound_stagea as reb
import live_cool_c8_cutover as cool_cut
import live_dh_fuse_cutover as fuse_cut
from tw_share_lots import BOARD_LOT, board_lots

HUMAN_ACCEPT = (
    "ACCEPT Live cutover: CONF_RET3_A10_H5 (00631L short-assist under COOL)"
)
LIVE_RECIPE_ID = "LIVE_CONF_RET3_A10_H5_00631L"
OFF_CODE = "00631L"
ALPHA = 0.10
HOLD_H = 5
CONFIRM = "RET3"
OFF_PRICE = Path(__file__).resolve().parents[1] / "data/def_proxies/00631L_ohlcv.csv"


def load_off_panel() -> pd.DataFrame:
    if not OFF_PRICE.exists():
        return pd.DataFrame()
    raw = pd.read_csv(OFF_PRICE, parse_dates=["date"], dtype={"code": str})
    raw["code"] = OFF_CODE
    return raw


def load_off_prices_for_asof(asof: pd.Timestamp) -> dict[str, float]:
    """Latest close ≤ asof for 00631L (empty if panel missing / pre-list)."""
    adj = load_off_panel()
    if adj.empty:
        return {}
    asof = pd.Timestamp(asof).normalize()
    sub = adj[adj["date"] <= asof]
    if sub.empty:
        return {}
    row = sub.sort_values("date").iloc[-1]
    if pd.isna(row.get("close")):
        return {}
    return {OFF_CODE: float(row["close"])}


def load_off_opens_for_asof(asof: pd.Timestamp) -> dict[str, float]:
    adj = load_off_panel()
    if adj.empty:
        return {}
    asof = pd.Timestamp(asof).normalize()
    sub = adj[adj["date"] <= asof]
    if sub.empty:
        return {}
    row = sub.sort_values("date").iloc[-1]
    if "open" in row.index and pd.notna(row.get("open")):
        return {OFF_CODE: float(row["open"])}
    if pd.isna(row.get("close")):
        return {}
    return {OFF_CODE: float(row["close"])}


def merge_off_session_prices(
    prices: dict[str, float],
    *,
    asof: pd.Timestamp,
    opens: dict[str, float] | None = None,
) -> tuple[dict[str, float], dict[str, float] | None, dict[str, Any]]:
    """Inject 00631L close/open into session price maps (fail-visible if missing)."""
    px = dict(prices)
    op = None if opens is None else dict(opens)
    meta: dict[str, Any] = {"off_code": OFF_CODE, "source": str(OFF_PRICE)}
    closes = load_off_prices_for_asof(asof)
    if not closes:
        meta["ok"] = False
        meta["reason"] = "missing_00631L_proxy"
        return px, op, meta
    px.update(closes)
    if op is not None:
        op.update(load_off_opens_for_asof(asof))
    meta["ok"] = True
    meta["close"] = float(closes[OFF_CODE])
    return px, op, meta


def _0050_ret3(market: pd.DataFrame, idx: pd.DatetimeIndex) -> pd.Series:
    m = market.copy()
    m["date"] = pd.to_datetime(m["date"])
    sub = m[m["code"].astype(str) == "0050"].sort_values("date")
    px = sub.set_index("date")["close"].astype(float).reindex(idx).ffill()
    return px.pct_change(3)


def off_weight_series(
    market: pd.DataFrame, dividends: pd.DataFrame
) -> tuple[pd.Series, dict[str, Any]]:
    """Causal CONF_RET3 α×H OFF weights on FUSE+COOL offense path (paper twin)."""
    nav, fuse_meta = fuse_cut.build_fuse_offense_nav(market, dividends)
    cool = cool_cut.build_cool_exposure_from_offense(market, nav)
    idx = pd.DatetimeIndex(cool.index)
    c = cool.reindex(idx).fillna(1.0).astype(float).clip(0.0, 1.0)
    listed_from = pd.Timestamp("2014-10-31")
    listed = pd.Series(idx >= listed_from, index=idx)
    exits = reb.cool_exits(c)
    ret3 = _0050_ret3(market, idx)
    entry = exits & listed & (ret3.reindex(idx) > 0)

    pulse = pd.Series(False, index=idx)
    entry_locs = [i for i, v in enumerate(entry.to_numpy()) if bool(v)]
    n = len(idx)
    for i0 in entry_locs:
        for k in range(int(HOLD_H)):
            j = i0 + k
            if j < n and bool(listed.iloc[j]):
                pulse.iloc[j] = True

    off_w = pd.Series(0.0, index=idx, dtype=float)
    off_w = off_w.where(~pulse, float(ALPHA))
    off_w = off_w.where(listed, 0.0)
    meta = {
        **fuse_meta,
        "confirm": CONFIRM,
        "alpha": float(ALPHA),
        "hold_h": int(HOLD_H),
        "off_code": OFF_CODE,
        "n_entries": int(len(entry_locs)),
        "pulse_frac": round(float((off_w > 0).mean()), 6),
        "mean_off": round(float(off_w.mean()), 6),
        "human_accept": HUMAN_ACCEPT,
        "live_recipe_id": LIVE_RECIPE_ID,
    }
    return off_w, meta


def off_weight_today(
    market: pd.DataFrame, dividends: pd.DataFrame, asof: pd.Timestamp
) -> tuple[float, dict[str, Any]]:
    """OFF weight for tip asof (0 when not in confirmed pulse)."""
    asof = pd.Timestamp(asof).normalize()
    off_w, meta = off_weight_series(market, dividends)
    if asof in off_w.index and pd.notna(off_w.loc[asof]):
        today = float(off_w.loc[asof])
    else:
        today = float(off_w.dropna().iloc[-1]) if off_w.dropna().size else 0.0
    px_ok = bool(load_off_prices_for_asof(asof))
    if today > 0 and not px_ok:
        # Fail-closed: no price → no OFF target (do not invent).
        today = 0.0
        meta = {**meta, "forced_off_missing_px": True}
    meta = {
        **meta,
        "asof": asof.date().isoformat(),
        "off_weight": float(today),
        "pulse_active": bool(today > 0),
        "px_ok": px_ok,
    }
    return today, meta


def apply_off_to_soft_targets(
    tw: pd.Series | dict[str, float], off_w: float
) -> dict[str, float]:
    """Scale Soft sleeves by (1 − OFF); OFF dollars sit outside Soft router."""
    w = float(max(0.0, min(1.0, off_w)))
    scale = 1.0 - w
    return {
        "Financial": float(tw["Financial"]) * scale,
        "Telecom": float(tw["Telecom"]) * scale,
        "0050": float(tw["0050"]) * scale,
    }


def build_off_order_rows(
    *,
    pos: dict[str, float],
    prices: dict[str, float],
    nav: float,
    off_w: float,
    signal_date: date,
    make_order_id: Callable[..., str],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Board-lot rebalance 00631L to target weight ``off_w`` (0 → force flat)."""
    meta: dict[str, Any] = {
        "off_code": OFF_CODE,
        "off_weight": float(off_w),
        "enabled": True,
    }
    if OFF_CODE not in prices or float(prices[OFF_CODE]) <= 0:
        meta["skipped_missing_px"] = True
        # Still try force-sell if we somehow hold without px — cannot.
        return [], meta

    px = float(prices[OFF_CODE])
    cur_sh = float(pos.get(OFF_CODE, 0.0) or 0.0)
    tgt_val = float(off_w) * float(nav)
    cur_val = cur_sh * px
    delta = tgt_val - cur_val
    rows: list[dict[str, Any]] = []

    if abs(float(off_w)) < 1e-12:
        # Pulse off → sell all board lots.
        qty = board_lots(cur_sh)
        if qty >= BOARD_LOT:
            oid = make_order_id(signal_date=signal_date, code=OFF_CODE, side="SELL")
            rows.append(
                {
                    "order_id": oid,
                    "signal_date": signal_date.isoformat(),
                    "code": OFF_CODE,
                    "side": "SELL",
                    "quantity": int(qty),
                    "reference_close": px,
                }
            )
        meta["force_flat"] = True
        meta["n_orders"] = len(rows)
        return rows, meta

    qty = board_lots(abs(delta) / px)
    if qty < BOARD_LOT:
        meta["n_orders"] = 0
        meta["below_lot"] = True
        return rows, meta
    side = "BUY" if delta > 0 else "SELL"
    if side == "SELL":
        qty = min(qty, board_lots(cur_sh))
    if qty < BOARD_LOT:
        meta["n_orders"] = 0
        return rows, meta
    oid = make_order_id(signal_date=signal_date, code=OFF_CODE, side=side)
    rows.append(
        {
            "order_id": oid,
            "signal_date": signal_date.isoformat(),
            "code": OFF_CODE,
            "side": side,
            "quantity": int(qty),
            "reference_close": px,
        }
    )
    meta["n_orders"] = len(rows)
    meta["side"] = side
    return rows, meta


def holdings_universe_with_off(base: list[str]) -> list[str]:
    out = list(base)
    if OFF_CODE not in out:
        out.append(OFF_CODE)
    return out


def etf_codes_with_off(base: frozenset[str] | set[str]) -> frozenset[str]:
    return frozenset(set(base) | {OFF_CODE})
