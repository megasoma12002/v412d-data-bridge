#!/usr/bin/env python3
"""Broker preflight fill port — session gate + fixture ack + Soft-Frozen write gates.

Offline only: no SPARK DLL. Soft-Frozen KEEP until ACCEPT + ballot + env.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from broker_safety import (
    DEFAULT_DAILY_LIVE_FILL_BUDGET,
    ProcessLock,
    already_in_fills_csv,
    already_submitted,
    append_submit_log,
    build_submit_intents,
    confirm_before_broker_submit,
    count_live_submits_today,
    live_write_gate,
    load_circuit,
    record_circuit_success,
    reserve_broker_dedupe,
    trip_circuit,
    validate_ack_against_pending,
    write_submit_intents,
)
from broker_risk import (
    OrderState,
    circuit_access,
    has_blocking_unresolved,
    pre_submit_full_gate,
    record_rate_limit_write,
    run_startup_reconcile,
    transition_order,
)
from live_config import LIVE
from live_fill_core import (
    FILL_ROW_KEYS,
    _exact_t1_stats,
    _iter_pending,
)
from live_ledger import SLIP, append_immutable, fees_tax_for, max_affordable_buy_qty
from tw_share_lots import BOARD_LOT

class BrokerPreflightFillPort:
    """P4: session-gated broker submit + fixture ack adapter + pre-API 防呆.

    Never invents fills when OPEN without acks. Fixture acks under
    ``state_dir/broker_acks/{asof}.json`` map into the canonical fill schema
    and write **shadow** artifacts under ``broker_preflight/`` only.

    Soft-Frozen live ``fills.csv`` / portfolio cash stay untouched unless
    ALL of: ``live_config.broker_live_write_accepted``, ``E21_BROKER_WRITE_LIVE=1``,
    ``broker_live_write_accept.json`` with ``accepted: true``, circuit closed,
    daily budget, ack↔pending match, idempotent client_order_id, process lock,
    and confirm+reserve broker dedupe (see ``broker_safety``).
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
        require_ballot_file: bool = True,
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

    def _write_spark_offline_intents(
        self,
        state_dir: Path,
        *,
        asof: date,
        pending_rows: list[dict[str, Any]],
    ) -> tuple[list[Any], Path]:
        """Map pending → SPARK StockOrder intents (offline; never calls DLL)."""
        from yuanta_spark_adapter import build_intents_from_pending, write_spark_intents

        spark_intents = build_intents_from_pending(pending_rows, asof=asof)
        spark_path = write_spark_intents(state_dir, asof, spark_intents)
        return spark_intents, spark_path

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
        # Seam: offline SPARK StockOrder mapping only (API_WIRED=False; no DLL).
        # Network submit stays in yuanta_spark_adapter.send_stock_order_live (blocked).
        spark_intents, spark_path = self._write_spark_offline_intents(
            sdir, asof=asof, pending_rows=pending_rows
        )
        meta["spark_intents_path"] = str(spark_path.name)
        meta["n_spark_intents"] = len(spark_intents)
        meta["spark_api_wired"] = False

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
            # Same-batch orphans must block other live fills (refresh unresolved).
            reconcile_after = run_startup_reconcile(sdir, asof=asof)
            meta["recovery_after_rejects"] = {
                "n_unresolved": reconcile_after.get("n_unresolved"),
                "n_stale": reconcile_after.get("n_stale"),
            }

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
            # Shadow JSON already written; do not feed fills into live orchestration.
            return pos, cash, [], 0, True

        # Orphan / UNKNOWN same batch → block entire live-write path (shadow only).
        if has_blocking_unresolved(sdir):
            meta["blocked"] = True
            meta["reason"] = "unresolved_orders_present"
            meta["live_fills_written"] = False
            meta["soft_frozen_untouched"] = True
            (block_dir / f"allow_{asof.isoformat()}.json").write_text(
                json.dumps({**meta, "n_fills": len(fills)}, indent=2, ensure_ascii=False)
                + "\n",
                encoding="utf-8",
            )
            return pos, cash, [], 0, True

        # Exact T+1 must pass before any Soft-Frozen fills.csv mutation.
        same_bar, ok = _exact_t1_stats(fills)
        if not ok:
            meta["blocked"] = True
            meta["reason"] = "exact_t1_violation"
            meta["same_bar_fills"] = same_bar
            meta["live_fills_written"] = False
            meta["soft_frozen_untouched"] = True
            (block_dir / f"allow_{asof.isoformat()}.json").write_text(
                json.dumps({**meta, "n_fills": len(fills)}, indent=2, ensure_ascii=False)
                + "\n",
                encoding="utf-8",
            )
            return pos, cash, fills, same_bar, False

        # Live write path — ACCEPT + env + explicit ops_confirmed + budget + cash.
        # Order: confirm (no reserve) → write fills.csv → reserve + submit log
        # so a crash cannot leave dedupe reserved without a fill row.
        already_today = count_live_submits_today(sdir, asof)
        pos_out = dict(pos)
        cash_out = float(cash)
        written = 0
        skipped: list[str] = []
        lifecycle_notes: list[str] = []
        for f in fills:
            coid = str(f.get("client_order_id") or f["fill_id"])
            if already_submitted(sdir, coid) or already_in_fills_csv(sdir, str(f["fill_id"])):
                skipped.append(f"idempotent_skip:{coid}")
                continue
            if already_today + written >= self._daily_live_budget:
                skipped.append(f"daily_budget:{self._daily_live_budget}")
                trip_circuit(sdir, "daily_live_fill_budget")
                break
            q = int(f["quantity"])
            side = str(f["side"])
            code = str(f["code"])
            fp = float(f.get("fill_price") or 0)
            gross = float(f["gross"])
            fee = float(f["fees_tax"])
            if side == "SELL":
                held = float(pos_out.get(code, 0) or 0)
                if held < q:
                    skipped.append(f"insufficient_inventory:{coid}:{held}<{q}")
                    continue
            if side == "BUY" and gross + fee > cash_out:
                afford = max_affordable_buy_qty(cash_out, fp, lot=BOARD_LOT)
                if afford < q:
                    skipped.append(f"insufficient_cash:{coid}")
                    continue
            risk = pre_submit_full_gate(
                sdir,
                code=code,
                side=side,
                quantity=q,
                price=fp or None,
                reference_price=open_prices.get(code),
            )
            if not risk.allowed:
                skipped.append(f"risk_denied:{','.join(risk.reasons)}")
                continue
            # Require explicit ops_confirmed on ack→fill (never hardcode True).
            confirm = confirm_before_broker_submit(
                state_dir=sdir,
                client_order_id=coid,
                code=code,
                side=side,
                quantity=q,
                asof=asof,
                confirmed=bool(f.get("ops_confirmed")),
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
            signed = q if side == "BUY" else -q
            pos_out[code] = pos_out.get(code, 0) + signed
            cash_out += -gross - fee if side == "BUY" else gross - fee
            # Strip non-schema keys before immutable append.
            row = {k: f[k] for k in FILL_ROW_KEYS if k in f}
            # Write fill BEFORE reserve so crash cannot stick on dedupe_hit without fill.
            append_immutable(sdir / "fills.csv", row, "fill_id")
            if confirm.dedupe_key:
                reserve_broker_dedupe(
                    sdir,
                    dedupe_key=confirm.dedupe_key,
                    client_order_id=coid,
                    asof=asof,
                )
            append_submit_log(
                sdir,
                {
                    "asof": asof.isoformat(),
                    "client_order_id": coid,
                    "fill_id": f["fill_id"],
                    "broker_dedupe_key": confirm.dedupe_key,
                    "live_written": True,
                    "code": code,
                    "side": side,
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
                    code=code,
                    side=side,
                    quantity=q,
                    asof=asof,
                    new_state=OrderState.FILLED,
                    filled_qty=q,
                    note="live_fill_written",
                    force=True,
                )
            except ValueError as e:
                lifecycle_notes.append(f"transition_filled:{coid}:{e}")
            written += 1

        meta["live_fills_written"] = written > 0
        meta["soft_frozen_untouched"] = written == 0
        meta["n_live_written"] = written
        meta["live_skips"] = skipped
        if lifecycle_notes:
            meta["lifecycle_notes"] = lifecycle_notes
        (block_dir / f"allow_{asof.isoformat()}.json").write_text(
            json.dumps({**meta, "n_fills": len(fills)}, indent=2, ensure_ascii=False)
            + "\n",
            encoding="utf-8",
        )
        return pos_out, cash_out, fills, same_bar, ok


