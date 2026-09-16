#!/usr/bin/env python3
"""Live execution session — pending order fills at open (Exact T+1).

Fill ports share one row schema written via ``live_ledger.append_immutable``.
Default port is paper Exact T+1 (open + slip/fee). Broker adapters plug in later
behind the same ``FillPort`` contract; dry-run / live routing need ACCEPT.
"""
from __future__ import annotations

import os
from datetime import date
from pathlib import Path
from typing import Any, Protocol

import pandas as pd

from live_ledger import BUY_FEE, SELL_FEE, SLIP, TAX_ETF, TAX_STOCK, append_immutable
from tw_share_lots import BOARD_LOT, board_lots

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
    """Pluggable fill backend for pending orders."""

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


def _exact_t1_stats(fills: list[dict[str, Any]]) -> tuple[int, bool]:
    same_bar_fills = 0
    for f in fills:
        sig = pd.to_datetime(f["signal_date"]).normalize()
        fill_dt = pd.to_datetime(f["fill_date"]).normalize()
        if fill_dt <= sig:
            same_bar_fills += 1
    return same_bar_fills, same_bar_fills == 0


def _iter_pending(state_dir: Path, latest: pd.Timestamp) -> pd.DataFrame:
    sdir = Path(state_dir)
    orders_path = sdir / "orders.csv"
    if not orders_path.exists():
        return pd.DataFrame()
    orders = pd.read_csv(orders_path, dtype={"code": str})
    filled: set[str] = set()
    if (sdir / "fills.csv").exists():
        filled = set(pd.read_csv(sdir / "fills.csv", dtype={"code": str}).fill_id.astype(str))
    pending = orders[
        (~orders.order_id.astype(str).isin(filled)) & (pd.to_datetime(orders.signal_date) < latest)
    ].copy()
    pending["_side_rank"] = pending["side"].map({"SELL": 0, "BUY": 1}).fillna(2)
    return pending.sort_values(["signal_date", "_side_rank", "code"])


def _paper_fill_rows(
    *,
    pending: pd.DataFrame,
    latest: pd.Timestamp,
    open_prices: dict[str, float],
    pos: dict[str, float],
    cash: float,
) -> tuple[dict[str, float], float, list[dict[str, Any]]]:
    fills: list[dict[str, Any]] = []
    for _, o in pending.iterrows():
        orig_q = int(o.quantity)
        q = orig_q
        side = o.side
        fp = open_prices[o.code] * (1 + SLIP if side == "BUY" else 1 - SLIP)
        gross = q * fp
        fee = gross * (
            BUY_FEE if side == "BUY" else SELL_FEE + (TAX_ETF if o.code == "0050" else TAX_STOCK)
        )
        signed = q if side == "BUY" else -q
        if side == "BUY" and gross + fee > cash:
            afford = board_lots(int(cash / (fp * (1 + BUY_FEE))))
            if afford < orig_q:
                continue
            q = afford
            gross = q * fp
            fee = gross * BUY_FEE
            signed = q
        if q < BOARD_LOT or q % BOARD_LOT != 0:
            continue
        pos[o.code] = pos.get(o.code, 0) + signed
        cash += -gross - fee if side == "BUY" else gross - fee
        fills.append(
            {
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
        )
    return pos, cash, fills


class PaperOpenFillPort:
    """Paper Exact T+1: fill prior pending at today's open + slip/fee model."""

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
        pending = _iter_pending(state_dir, latest)
        if pending.empty:
            return pos, cash, [], 0, True
        pos, cash, fills = _paper_fill_rows(
            pending=pending,
            latest=latest,
            open_prices=open_prices,
            pos=pos,
            cash=cash,
        )
        sdir = Path(state_dir)
        for f in fills:
            append_immutable(sdir / "fills.csv", f, "fill_id")
        same_bar, ok = _exact_t1_stats(fills)
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

        pending = _iter_pending(state_dir, latest)
        # Work on copies so live pos/cash stay unchanged.
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
        same_bar, ok = _exact_t1_stats(fills)
        # Return original pos/cash so pipeline does not book dry-run fills.
        return pos, cash, fills, same_bar, ok


class BrokerPreflightFillPort:
    """P4: session-gated broker submit + optional fixture ack adapter.

    Never invents fills when OPEN without acks. Fixture acks under
    ``state_dir/broker_acks/{asof}.json`` map into the canonical fill schema
    and write **shadow** artifacts under ``broker_preflight/`` only.

    Soft-Frozen live ``fills.csv`` / portfolio cash stay untouched unless
    ``E21_BROKER_WRITE_LIVE=1`` **and** acks are present (separate live-routing
    ACCEPT; default off).
    """

    name = "broker"
    ENV_WRITE_LIVE = "E21_BROKER_WRITE_LIVE"

    def __init__(
        self,
        *,
        probe_fn=None,
        use_network: bool = True,
        calendar=None,
        write_live: bool | None = None,
    ) -> None:
        self._probe_fn = probe_fn
        self._use_network = use_network
        self._calendar = calendar
        if write_live is None:
            write_live = os.environ.get(self.ENV_WRITE_LIVE, "").strip() in (
                "1",
                "true",
                "TRUE",
                "yes",
            )
        self._write_live = bool(write_live)

    def _load_acks(self, state_dir: Path, asof: date) -> list[dict[str, Any]]:
        path = Path(state_dir) / "broker_acks" / f"{asof.isoformat()}.json"
        if not path.exists():
            return []
        import json

        obj = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(obj, list):
            return [dict(x) for x in obj]
        if isinstance(obj, dict):
            acks = obj.get("acks") or obj.get("fills") or []
            return [dict(x) for x in acks]
        return []

    def _acks_to_fills(
        self,
        acks: list[dict[str, Any]],
        *,
        latest: pd.Timestamp,
        open_prices: dict[str, float],
        pending: pd.DataFrame,
    ) -> list[dict[str, Any]]:
        """Map fixture broker acks → canonical fill rows (no portfolio mutate)."""
        pending_by_id = {
            str(r.order_id): r for _, r in pending.iterrows()
        } if not pending.empty else {}
        fills: list[dict[str, Any]] = []
        for ack in acks:
            oid = str(ack.get("order_id") or ack.get("fill_id") or "").strip()
            if not oid:
                continue
            order = pending_by_id.get(oid)
            code = str(ack.get("code") or (order.code if order is not None else "") or "")
            side = str(ack.get("side") or (order.side if order is not None else "") or "").upper()
            try:
                q = int(float(ack.get("quantity") or (order.quantity if order is not None else 0)))
            except (TypeError, ValueError):
                continue
            if q < BOARD_LOT or q % BOARD_LOT != 0:
                continue
            if side not in ("BUY", "SELL") or not code:
                continue
            if "fill_price" in ack and ack["fill_price"] not in (None, ""):
                fp = float(ack["fill_price"])
            else:
                px = open_prices.get(code)
                if px is None:
                    continue
                fp = px * (1 + SLIP if side == "BUY" else 1 - SLIP)
            gross = q * fp
            fee = gross * (
                BUY_FEE if side == "BUY" else SELL_FEE + (TAX_ETF if code == "0050" else TAX_STOCK)
            )
            sig = (
                str(ack.get("signal_date") or "")
                or (str(order.signal_date) if order is not None else "")
            )
            fills.append(
                {
                    "fill_id": oid,
                    "signal_date": sig,
                    "fill_date": latest.date().isoformat(),
                    "code": code,
                    "side": side,
                    "quantity": q,
                    "fill_price": fp,
                    "gross": gross,
                    "fees_tax": fee,
                    "slippage_bp": SLIP * 10000,
                    "broker_ack": True,
                }
            )
        return fills

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

        from twse_session_sources import probe_session

        asof = latest.date() if hasattr(latest, "date") else pd.Timestamp(latest).date()
        if self._probe_fn is not None:
            probe = self._probe_fn(asof)
        else:
            probe = probe_session(
                asof, use_network=self._use_network, calendar=self._calendar
            )
        sdir = Path(state_dir)
        block_dir = sdir / "broker_preflight"
        block_dir.mkdir(parents=True, exist_ok=True)
        meta: dict[str, Any] = {
            "port": self.name,
            "asof": asof.isoformat(),
            "status": getattr(probe, "status", "UNKNOWN"),
            "broker_submit_allowed": bool(getattr(probe, "broker_submit_allowed", False)),
            "is_session": bool(getattr(probe, "is_session", False)),
            "notes": list(getattr(probe, "notes", []) or []),
            "live_fills_written": False,
            "soft_frozen_untouched": True,
            "fixture_acks": 0,
        }
        if not meta["broker_submit_allowed"]:
            meta["blocked"] = True
            meta["reason"] = f"broker submit blocked: {meta['status']}"
            (block_dir / f"block_{asof.isoformat()}.json").write_text(
                json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            return pos, cash, [], 0, True

        acks = self._load_acks(sdir, asof)
        meta["blocked"] = False
        meta["fixture_acks"] = len(acks)
        pending = _iter_pending(sdir, latest)
        fills = self._acks_to_fills(
            acks, latest=latest, open_prices=open_prices, pending=pending
        )

        if not acks:
            meta["note"] = (
                "session OPEN preflight passed; no broker_acks fixture — "
                "refusing to invent fills. Soft-Frozen untouched."
            )
            (block_dir / f"allow_{asof.isoformat()}.json").write_text(
                json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            return pos, cash, [], 0, True

        shadow = {
            **meta,
            "n_fills": len(fills),
            "fills": fills,
            "note": "fixture ack mapped; shadow only unless E21_BROKER_WRITE_LIVE=1",
        }
        (block_dir / f"fills_{asof.isoformat()}.json").write_text(
            json.dumps(shadow, indent=2, ensure_ascii=False, default=str) + "\n",
            encoding="utf-8",
        )
        (block_dir / f"allow_{asof.isoformat()}.json").write_text(
            json.dumps(
                {**meta, "n_fills": len(fills), "shadow_path": f"fills_{asof.isoformat()}.json"},
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

        if not self._write_live:
            same_bar, ok = _exact_t1_stats(fills)
            # Shadow: return original pos/cash; pipeline must not book these fills.
            return pos, cash, fills, same_bar, ok

        # Live write path (explicit ACCEPT env) — still session-gated + ack-only.
        pos_out = dict(pos)
        cash_out = float(cash)
        for f in fills:
            q = int(f["quantity"])
            signed = q if f["side"] == "BUY" else -q
            gross = float(f["gross"])
            fee = float(f["fees_tax"])
            pos_out[f["code"]] = pos_out.get(f["code"], 0) + signed
            cash_out += -gross - fee if f["side"] == "BUY" else gross - fee
            append_immutable(sdir / "fills.csv", f, "fill_id")
        meta["live_fills_written"] = True
        meta["soft_frozen_untouched"] = False
        (block_dir / f"allow_{asof.isoformat()}.json").write_text(
            json.dumps({**meta, "n_fills": len(fills)}, indent=2, ensure_ascii=False)
            + "\n",
            encoding="utf-8",
        )
        same_bar, ok = _exact_t1_stats(fills)
        return pos_out, cash_out, fills, same_bar, ok


_PORTS: dict[str, type] = {
    PaperOpenFillPort.name: PaperOpenFillPort,
    DryRunFillPort.name: DryRunFillPort,
    BrokerPreflightFillPort.name: BrokerPreflightFillPort,
}


def resolve_fill_port(name: str | None = None) -> FillPort:
    """Resolve fill port from explicit name, else ``E21_FILL_PORT``, else paper."""
    raw = (name or os.environ.get(ENV_FILL_PORT) or DEFAULT_FILL_PORT).strip().lower()
    if raw not in _PORTS:
        known = ", ".join(sorted(_PORTS))
        raise SystemExit(f"Unknown fill port {raw!r}; known: {known}")
    return _PORTS[raw]()


def fill_pending_at_open(
    *,
    state_dir: Path,
    latest: pd.Timestamp,
    open_prices: dict[str, float],
    pos: dict[str, float],
    cash: float,
    fill_port: str | FillPort | None = None,
) -> tuple[dict[str, float], float, list[dict[str, Any]], int, bool]:
    """Fill prior pending orders. Default port = paper Exact T+1 (unchanged)."""
    port: FillPort
    if isinstance(fill_port, str) or fill_port is None:
        port = resolve_fill_port(fill_port)
    else:
        port = fill_port
    return port.fill_pending(
        state_dir=state_dir,
        latest=latest,
        open_prices=open_prices,
        pos=pos,
        cash=cash,
    )
