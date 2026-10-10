#!/usr/bin/env python3
"""Live fill core — paper Exact T+1 + dry_run shadow ports.

Broker preflight lives in ``live_fill_broker``. Import via ``live_execution``
facade for stable call sites.

Named carve-out ``T0_CARVE_FIN_SAT_SWITCH`` may allow tagged same-bar fills
only when ``LIVE.live_t0_carve_fin_sat_switch_fill`` is True (default False).
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Protocol

import pandas as pd

from live_ledger import (
    SLIP,
    fees_tax_for,
    max_affordable_buy_qty,
)
from t0_carve_fin_sat_switch import (
    CARVE_OUT_ID,
    ORDER_TAG_COL,
    authorize_same_bar_fill,
    is_live_fill_authorized,
)
from tw_share_lots import BOARD_LOT

# Canonical fill row keys (broker ports must map acks into this schema).
FILL_ROW_KEYS = (
    "fill_id",
    "signal_date",
    "fill_date",
    "code",
    "side",
    "quantity",
    "fill_price",
    "gross",
    "fees_tax",
    "slippage_bp",
)

DEFAULT_FILL_PORT = "paper"
ENV_FILL_PORT = "E21_FILL_PORT"


class FillPort(Protocol):
    name: str

    def fill_pending(
        self,
        *,
        state_dir: Path,
        latest: pd.Timestamp,
        open_prices: dict[str, float],
        pos: dict[str, float],
        cash: float,
    ) -> tuple[dict[str, float], float, list[dict[str, Any]], int, bool]:
        """Return pos, cash, fills, same_bar_fills, exact_t1_ok."""
        ...


def _exact_t1_stats(
    fills: list[dict[str, Any]],
    *,
    carve_authorized: bool | None = None,
) -> tuple[int, bool]:
    """Return (same_bar_count, exact_t1_ok). Missing/NaT dates fail closed.

    When ``carve_authorized`` (default: live flag) is True, fills tagged
    ``carve_out_id=T0_CARVE_FIN_SAT_SWITCH`` are excluded from same-bar violations.
    Untagged / other fills still fail closed on same-bar.
    """
    auth = is_live_fill_authorized() if carve_authorized is None else bool(carve_authorized)
    same_bar_fills = 0
    for f in fills:
        sig = pd.to_datetime(f.get("signal_date"), errors="coerce")
        fill_dt = pd.to_datetime(f.get("fill_date"), errors="coerce")
        if pd.isna(sig) or pd.isna(fill_dt):
            same_bar_fills += 1
            continue
        sig_n = sig.normalize()
        fill_n = fill_dt.normalize()
        if fill_n <= sig_n:
            if fill_n == sig_n and authorize_same_bar_fill(f, authorized=auth):
                continue
            same_bar_fills += 1
    return same_bar_fills, same_bar_fills == 0


def _side_rank(side: object) -> int:
    s = str(side or "").strip().upper()
    if s == "SELL":
        return 0
    if s == "BUY":
        return 1
    return 2


def sort_rows_sell_before_buy(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Stable SELL-before-BUY for list-of-dict pending (research simulate_core)."""
    return sorted(
        rows,
        key=lambda o: (_side_rank(o.get("side")), str(o.get("code") or "")),
    )


def sort_pending_sell_before_buy(pending: pd.DataFrame) -> pd.DataFrame:
    """Stable SELL-before-BUY within signal_date (live + research shared)."""
    if pending.empty:
        return pending
    out = pending.copy()
    out["_side_rank"] = out["side"].map(_side_rank)
    return out.sort_values(["signal_date", "_side_rank", "code"])


def _iter_pending(
    state_dir: Path,
    latest: pd.Timestamp,
    *,
    carve_authorized: bool | None = None,
) -> pd.DataFrame:
    """Pending Exact T+1: ``signal_date < latest``.

    When carve-out fill is authorized, also include same-day orders tagged
    ``carve_out_id=T0_CARVE_FIN_SAT_SWITCH`` (``signal_date == latest``).
    """
    sdir = Path(state_dir)
    orders_path = sdir / "orders.csv"
    if not orders_path.exists():
        return pd.DataFrame()
    orders = pd.read_csv(orders_path, dtype={"code": str})
    filled: set[str] = set()
    if (sdir / "fills.csv").exists():
        filled = set(pd.read_csv(sdir / "fills.csv", dtype={"code": str}).fill_id.astype(str))
    unfilled = ~orders.order_id.astype(str).isin(filled)
    from live_order_lifecycle import cancelled_ids
    unfilled &= ~orders.order_id.astype(str).isin(cancelled_ids(sdir))
    sig = pd.to_datetime(orders["signal_date"], errors="coerce")
    latest_n = pd.Timestamp(latest).normalize()
    prior = unfilled & (sig < latest_n)
    auth = is_live_fill_authorized() if carve_authorized is None else bool(carve_authorized)
    if auth and ORDER_TAG_COL in orders.columns:
        tagged = orders[ORDER_TAG_COL].astype(str).str.strip() == CARVE_OUT_ID
        if "execution_clock" in orders:
            tagged &= orders.execution_clock != "NEXT_SESSION_OPEN"
        same_day = unfilled & tagged & (sig.dt.normalize() == latest_n)
        pending = orders[prior | same_day].copy()
    else:
        pending = orders[prior].copy()
    return sort_pending_sell_before_buy(pending)


def _paper_fill_rows(
    *,
    pending: pd.DataFrame,
    latest: pd.Timestamp,
    open_prices: dict[str, float],
    pos: dict[str, float],
    cash: float,
    carve_authorized: bool | None = None,
) -> tuple[dict[str, float], float, list[dict[str, Any]]]:
    """Live paper policy: underfunded BUY skips entirely when afford < orig_q.

    Carve-tagged same-bar fills (signal_date == fill_date) price off
    ``reference_close`` when present (MOC proxy); else open+slip.
    """
    auth = is_live_fill_authorized() if carve_authorized is None else bool(carve_authorized)
    fills: list[dict[str, Any]] = []
    latest_n = pd.Timestamp(latest).normalize()
    for _, o in pending.iterrows():
        orig_q = int(o.quantity)
        q = orig_q
        side = o.side
        sig = pd.to_datetime(o.signal_date, errors="coerce")
        same_bar = bool(pd.notna(sig) and sig.normalize() == latest_n)
        use_moc = same_bar and authorize_same_bar_fill(o, authorized=auth)
        if pd.isna(sig) or sig.normalize() > latest_n or (same_bar and not use_moc):
            continue
        if use_moc and "reference_close" in pending.columns and pd.notna(
            getattr(o, "reference_close", None)
        ):
            raw_px = float(o.reference_close)
            fp = raw_px * (1 + SLIP if side == "BUY" else 1 - SLIP)
        else:
            fp = open_prices[o.code] * (1 + SLIP if side == "BUY" else 1 - SLIP)
        gross = q * fp
        fee = fees_tax_for(side=side, code=str(o.code), gross=gross)
        signed = q if side == "BUY" else -q
        if side == "SELL":
            held = float(pos.get(o.code, 0) or 0)
            if held < q:
                continue
        if side == "BUY" and gross + fee > cash:
            afford = max_affordable_buy_qty(cash, fp, lot=BOARD_LOT)
            # Live landmine policy: skip (do not partial-fill / burn order_id).
            if afford < orig_q:
                continue
            q = afford
            gross = q * fp
            fee = fees_tax_for(side="BUY", code=str(o.code), gross=gross)
            signed = q
        if q < BOARD_LOT or q % BOARD_LOT != 0:
            continue
        pos[o.code] = pos.get(o.code, 0) + signed
        cash += -gross - fee if side == "BUY" else gross - fee
        row = {
            "fill_id": o.order_id,
            "signal_date": o.signal_date,
            "fill_date": latest.date().isoformat(),
            "code": o.code,
            "side": side,
            "quantity": q,
            "fill_price": fp,
            "gross": gross,
            "fees_tax": fee,
            "slippage_bp": SLIP * 10000,
        }
        if ORDER_TAG_COL in pending.columns:
            tag = getattr(o, ORDER_TAG_COL, None)
            if tag is not None and str(tag).strip():
                row[ORDER_TAG_COL] = str(tag).strip()
        if "execution_clock" in pending.columns:
            row["execution_clock"] = getattr(o, "execution_clock", None)
        if use_moc:
            row["fill_policy"] = "T0_CARVE_MOC_REF_CLOSE"
        fills.append(row)
    return pos, cash, fills


class PaperOpenFillPort:
    """Paper Exact T+1: fill prior pending at today's open + slip/fee model.

    Optional named carve-out: tagged Path3 switch orders may fill same-bar
    when ``LIVE.live_t0_carve_fin_sat_switch_fill`` is True.
    """

    name = "paper"

    def fill_pending(
        self,
        *,
        state_dir: Path,
        latest: pd.Timestamp,
        open_prices: dict[str, float],
        pos: dict[str, float],
        cash: float,
    ) -> tuple[dict[str, float], float, list[dict[str, Any]], int, bool]:
        auth = is_live_fill_authorized()
        pending = _iter_pending(state_dir, latest, carve_authorized=auth)
        if pending.empty:
            return pos, cash, [], 0, True
        pos, cash, fills = _paper_fill_rows(
            pending=pending,
            latest=latest,
            open_prices=open_prices,
            pos=pos,
            cash=cash,
            carve_authorized=auth,
        )
        # Defer fills.csv append to pipeline day-commit (with portfolio_state)
        # to shrink crash window between immutable CSV and state JSON.
        same_bar, ok = _exact_t1_stats(fills, carve_authorized=auth)
        return pos, cash, fills, same_bar, ok


class DryRunFillPort:
    """Shadow port: same pricing as paper, writes under ``broker_dryrun/`` only.

    Does **not** append to live ``fills.csv`` and does **not** mutate portfolio
    for the live session — used to diff broker mapping later.
    """

    name = "dry_run"

    def fill_pending(
        self,
        *,
        state_dir: Path,
        latest: pd.Timestamp,
        open_prices: dict[str, float],
        pos: dict[str, float],
        cash: float,
    ) -> tuple[dict[str, float], float, list[dict[str, Any]], int, bool]:
        import json

        pending = _iter_pending(state_dir, latest, carve_authorized=is_live_fill_authorized())
        pos_shadow = dict(pos)
        cash_shadow = float(cash)
        if pending.empty:
            fills: list[dict[str, Any]] = []
        else:
            pos_shadow, cash_shadow, fills = _paper_fill_rows(
                pending=pending,
                latest=latest,
                open_prices=open_prices,
                pos=pos_shadow,
                cash=cash_shadow,
                carve_authorized=is_live_fill_authorized(),
            )
        out = Path(state_dir) / "broker_dryrun"
        out.mkdir(parents=True, exist_ok=True)
        payload = {
            "port": self.name,
            "fill_date": latest.date().isoformat(),
            "n_fills": len(fills),
            "fills": fills,
            "live_fills_written": False,
            "note": "Shadow only — live fills.csv / portfolio_state untouched",
        }
        (out / f"fills_{latest.date().isoformat()}.json").write_text(
            json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8"
        )
        same_bar, ok = _exact_t1_stats(fills, carve_authorized=is_live_fill_authorized())
        return pos, cash, fills, same_bar, ok
