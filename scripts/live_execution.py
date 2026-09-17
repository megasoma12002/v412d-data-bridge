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

from broker_safety import (
    DEFAULT_DAILY_LIVE_FILL_BUDGET,
    ProcessLock,
    already_in_fills_csv,
    already_submitted,
    append_submit_log,
    build_submit_intents,
    confirm_and_reserve_broker_submit,
    count_live_submits_today,
    live_write_gate,
    load_circuit,
    record_circuit_success,
    trip_circuit,
    validate_ack_against_pending,
    write_submit_intents,
)
from broker_risk import (
    OrderState,
    circuit_access,
    pre_submit_full_gate,
    record_rate_limit_write,
    run_startup_reconcile,
    transition_order,
)
from live_config import LIVE
from live_ledger import (
    BUY_FEE,
    SELL_FEE,
    SLIP,
    TAX_ETF,
    TAX_STOCK,
    append_immutable,
    fees_tax_for,
    max_affordable_buy_qty,
)
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
        fee = fees_tax_for(side=side, code=str(o.code), gross=gross)
        signed = q if side == "BUY" else -q
        if side == "BUY" and gross + fee > cash:
            afford = max_affordable_buy_qty(cash, fp, lot=BOARD_LOT)
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
    """P4: session-gated broker submit + fixture ack adapter + pre-API 防呆.

    Never invents fills when OPEN without acks. Fixture acks under
    ``state_dir/broker_acks/{asof}.json`` map into the canonical fill schema
    and write **shadow** artifacts under ``broker_preflight/`` only.

    Soft-Frozen live ``fills.csv`` / portfolio cash stay untouched unless
    ALL of: ``live_config.broker_live_write_accepted``, ``E21_BROKER_WRITE_LIVE=1``,
    circuit closed, daily budget, ack↔pending match, idempotent client_order_id,
    process lock, and confirm+reserve broker dedupe (see ``broker_safety``).
    No real broker network client is wired here.
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
        config_accepted: bool | None = None,
        require_ballot_file: bool = False,
        daily_live_budget: int = DEFAULT_DAILY_LIVE_FILL_BUDGET,
    ) -> None:
        self._probe_fn = probe_fn
        self._use_network = use_network
        self._calendar = calendar
        # Explicit ctor override only; env alone never bypasses LiveConfig ACCEPT.
        self._write_live_override = write_live
        self._config_accepted = (
            bool(LIVE.broker_live_write_accepted)
            if config_accepted is None
            else bool(config_accepted)
        )
        self._require_ballot_file = bool(require_ballot_file)
        self._daily_live_budget = int(daily_live_budget)

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
        asof: date,
        open_prices: dict[str, float],
        pending: pd.DataFrame,
    ) -> tuple[list[dict[str, Any]], list[str]]:
        """Map fixture broker acks → canonical fill rows; reject orphans/mismatches."""
        pending_by_id = (
            {str(r.order_id): r for _, r in pending.iterrows()} if not pending.empty else {}
        )
        fills: list[dict[str, Any]] = []
        rejects: list[str] = []
        for ack in acks:
            result = validate_ack_against_pending(
                ack,
                pending_by_id,
                asof=asof,
                open_prices=open_prices,
                slip=SLIP,
                fees_tax_fn=fees_tax_for,
            )
            if not result.ok or result.fill is None:
                rejects.append(str(result.reject_reason or "unknown_reject"))
                continue
            fills.append(result.fill)
        return fills, rejects

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

        sdir = Path(state_dir)
        block_dir = sdir / "broker_preflight"
        block_dir.mkdir(parents=True, exist_ok=True)
        asof = latest.date() if hasattr(latest, "date") else pd.Timestamp(latest).date()
        try:
            with ProcessLock(sdir, blocking=False):
                return self._fill_pending_locked(
                    state_dir=sdir,
                    latest=latest,
                    asof=asof,
                    open_prices=open_prices,
                    pos=pos,
                    cash=cash,
                )
        except BlockingIOError:
            meta = {
                "port": self.name,
                "asof": asof.isoformat(),
                "blocked": True,
                "reason": "process_lock_held",
                "live_fills_written": False,
                "soft_frozen_untouched": True,
                "api_wired": False,
            }
            (block_dir / f"block_{asof.isoformat()}.json").write_text(
                json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            return pos, cash, [], 0, True

    def _fill_pending_locked(
        self,
        *,
        state_dir: Path,
        latest: pd.Timestamp,
        asof: date,
        open_prices: dict[str, float],
        pos: dict[str, float],
        cash: float,
    ) -> tuple[dict[str, float], float, list[dict[str, Any]], int, bool]:
        import json

        from twse_session_sources import probe_session

        if self._probe_fn is not None:
            probe = self._probe_fn(asof)
        else:
            probe = probe_session(
                asof, use_network=self._use_network, calendar=self._calendar
            )
        sdir = Path(state_dir)
        block_dir = sdir / "broker_preflight"
        block_dir.mkdir(parents=True, exist_ok=True)
        gate = live_write_gate(
            config_accepted=self._config_accepted,
            state_dir=sdir,
            require_ballot_file=self._require_ballot_file,
            env_write_live=(
                None if self._write_live_override is None else bool(self._write_live_override)
            ),
        )
        circuit = load_circuit(sdir)
        access = circuit_access(sdir)
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
            "live_write_gate_allowed": gate.allowed,
            "live_write_gate_reasons": list(gate.reasons),
            "circuit_open": circuit.open,
            "circuit_mode": circuit.mode,
            "writes_allowed": access.writes_allowed,
            "reads_allowed": access.reads_allowed,
            "process_lock": True,
            "api_wired": False,
        }
        if not meta["broker_submit_allowed"]:
            meta["blocked"] = True
            meta["reason"] = f"broker submit blocked: {meta['status']}"
            (block_dir / f"block_{asof.isoformat()}.json").write_text(
                json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            return pos, cash, [], 0, True

        if not access.writes_allowed:
            meta["blocked"] = True
            meta["reason"] = access.reason or f"circuit_open:{circuit.last_reason}"
            (block_dir / f"block_{asof.isoformat()}.json").write_text(
                json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
            return pos, cash, [], 0, True

        # Startup reconcile: stuck SUBMITTED/UNKNOWN etc. must be manually resolved.
        reconcile = run_startup_reconcile(sdir, asof=asof)
        meta["recovery"] = {
            "n_unresolved": reconcile.get("n_unresolved"),
            "n_stale": reconcile.get("n_stale"),
            "writes_allowed": circuit_access(sdir).writes_allowed,
        }

        acks = self._load_acks(sdir, asof)
        meta["blocked"] = False
        meta["fixture_acks"] = len(acks)
        pending = _iter_pending(sdir, latest)
        pending_rows = pending.to_dict(orient="records") if not pending.empty else []
        intents = build_submit_intents(pending_rows, asof=asof)
        intent_path = write_submit_intents(sdir, asof, intents)
        meta["submit_intents_path"] = str(intent_path.name)
        meta["n_submit_intents"] = len(intents)
        for it in intents:
            try:
                transition_order(
                    sdir,
                    client_order_id=it.client_order_id,
                    order_id=it.order_id,
                    code=it.code,
                    side=it.side,
                    quantity=it.quantity,
                    asof=asof,
                    new_state=OrderState.PENDING,
                    note="submit_intent",
                )
            except ValueError:
                pass

        fills, rejects = self._acks_to_fills(
            acks, asof=asof, open_prices=open_prices, pending=pending
        )
        meta["ack_rejects"] = rejects
        if rejects:
            for reason in rejects:
                trip_circuit(sdir, reason)
                # Best-effort: mark unknown reject path when order_id parseable
                if reason.startswith("ack_not_in_pending:"):
                    emit_oid = reason.split(":", 1)[-1]
                    try:
                        from broker_safety import client_order_id_for

                        transition_order(
                            sdir,
                            client_order_id=client_order_id_for(emit_oid, asof=asof),
                            order_id=emit_oid,
                            code="",
                            side="BUY",
                            quantity=BOARD_LOT,
                            asof=asof,
                            new_state=OrderState.UNKNOWN,
                            note=reason,
                            force=True,
                        )
                    except Exception:  # noqa: BLE001
                        pass

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
            "note": (
                "fixture ack mapped; shadow only unless live_write_gate "
                "(ACCEPT + E21_BROKER_WRITE_LIVE) passes"
            ),
        }
        (block_dir / f"fills_{asof.isoformat()}.json").write_text(
            json.dumps(shadow, indent=2, ensure_ascii=False, default=str) + "\n",
            encoding="utf-8",
        )
        (block_dir / f"allow_{asof.isoformat()}.json").write_text(
            json.dumps(
                {
                    **meta,
                    "n_fills": len(fills),
                    "shadow_path": f"fills_{asof.isoformat()}.json",
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

        if not gate.allowed:
            same_bar, ok = _exact_t1_stats(fills)
            return pos, cash, fills, same_bar, ok

        # Live write path — ACCEPT + env + confirm/reserve + budget + idempotency.
        already_today = count_live_submits_today(sdir, asof)
        pos_out = dict(pos)
        cash_out = float(cash)
        written = 0
        skipped: list[str] = []
        for f in fills:
            coid = str(f.get("client_order_id") or f["fill_id"])
            if already_submitted(sdir, coid) or already_in_fills_csv(sdir, str(f["fill_id"])):
                skipped.append(f"idempotent_skip:{coid}")
                continue
            if already_today + written >= self._daily_live_budget:
                skipped.append(f"daily_budget:{self._daily_live_budget}")
                trip_circuit(sdir, "daily_live_fill_budget")
                break
            risk = pre_submit_full_gate(
                sdir,
                code=str(f["code"]),
                side=str(f["side"]),
                quantity=int(f["quantity"]),
                price=float(f.get("fill_price") or 0) or None,
                reference_price=open_prices.get(str(f["code"])),
            )
            if not risk.allowed:
                skipped.append(f"risk_denied:{','.join(risk.reasons)}")
                continue
            # Ack-validated live write counts as confirmed for fixture path;
            # future API adapters must pass confirmed only after explicit ops/API ACK.
            confirm = confirm_and_reserve_broker_submit(
                state_dir=sdir,
                client_order_id=coid,
                code=str(f["code"]),
                side=str(f["side"]),
                quantity=int(f["quantity"]),
                asof=asof,
                confirmed=True,
                config_accepted=self._config_accepted,
                env_write_live=(
                    None
                    if self._write_live_override is None
                    else bool(self._write_live_override)
                ),
                require_ballot_file=self._require_ballot_file,
            )
            if not confirm.allowed:
                skipped.append(f"confirm_denied:{','.join(confirm.reasons)}")
                continue
            q = int(f["quantity"])
            signed = q if f["side"] == "BUY" else -q
            gross = float(f["gross"])
            fee = float(f["fees_tax"])
            pos_out[f["code"]] = pos_out.get(f["code"], 0) + signed
            cash_out += -gross - fee if f["side"] == "BUY" else gross - fee
            # Strip non-schema keys before immutable append.
            row = {k: f[k] for k in FILL_ROW_KEYS if k in f}
            append_immutable(sdir / "fills.csv", row, "fill_id")
            append_submit_log(
                sdir,
                {
                    "asof": asof.isoformat(),
                    "client_order_id": coid,
                    "fill_id": f["fill_id"],
                    "broker_dedupe_key": confirm.dedupe_key,
                    "live_written": True,
                    "code": f["code"],
                    "side": f["side"],
                    "quantity": q,
                },
            )
            record_rate_limit_write(sdir, client_order_id=coid)
            record_circuit_success(sdir)
            try:
                transition_order(
                    sdir,
                    client_order_id=coid,
                    order_id=str(f["fill_id"]),
                    code=str(f["code"]),
                    side=str(f["side"]),
                    quantity=q,
                    asof=asof,
                    new_state=OrderState.FILLED,
                    filled_qty=q,
                    note="live_fill_written",
                    force=True,
                )
            except ValueError:
                pass
            written += 1

        meta["live_fills_written"] = written > 0
        meta["soft_frozen_untouched"] = written == 0
        meta["n_live_written"] = written
        meta["live_skips"] = skipped
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
