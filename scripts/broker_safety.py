#!/usr/bin/env python3
"""Broker live-write safeguards (pre–real API).

Fail-closed helpers used by ``BrokerPreflightFillPort`` before any Soft-Frozen
``fills.csv`` mutation. No broker network client lives here — only gates that a
future API adapter must pass.

Gates:
  1. Session preflight (caller) — OPEN + broker_submit_allowed
  2. Hard ACCEPT: ``live_config.broker_live_write_accepted`` AND env
     ``E21_BROKER_WRITE_LIVE=1`` (and optional ballot file)
  3. Ack must match a pending order (code/side/qty)
  4. Idempotent client_order_id / fill_id — no duplicate live submits
  5. Daily live-write budget
  6. Circuit breaker after repeated rejects / reconcile trip
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from tw_share_lots import BOARD_LOT

ENV_WRITE_LIVE = "E21_BROKER_WRITE_LIVE"
DEFAULT_DAILY_LIVE_FILL_BUDGET = 50
DEFAULT_CIRCUIT_FAIL_THRESHOLD = 3
BALLOT_FILENAME = "broker_live_write_accept.json"
CIRCUIT_FILENAME = "broker_circuit.json"
SUBMIT_LOG_FILENAME = "broker_submit_log.jsonl"


def env_truthy(name: str) -> bool:
    return os.environ.get(name, "").strip() in ("1", "true", "TRUE", "yes", "YES")


@dataclass
class LiveWriteGateResult:
    allowed: bool
    reasons: list[str] = field(default_factory=list)
    ballot_path: str | None = None


def load_accept_ballot(state_dir: Path) -> dict[str, Any] | None:
    """Optional ops ballot under state_dir confirming live-write ACCEPT."""
    path = Path(state_dir) / BALLOT_FILENAME
    if not path.exists():
        return None
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return obj if isinstance(obj, dict) else None


def live_write_gate(
    *,
    config_accepted: bool,
    state_dir: Path,
    require_ballot_file: bool = False,
    env_write_live: bool | None = None,
) -> LiveWriteGateResult:
    """Hard gate for mutating Soft-Frozen fills via broker port.

    All of: LiveConfig ACCEPT flag, env ``E21_BROKER_WRITE_LIVE``, and
    (if ``require_ballot_file``) a ballot JSON with ``accepted: true``.
    """
    reasons: list[str] = []
    env_ok = env_truthy(ENV_WRITE_LIVE) if env_write_live is None else bool(env_write_live)
    if not config_accepted:
        reasons.append("live_config.broker_live_write_accepted=False (ACCEPT PR required)")
    if not env_ok:
        reasons.append(f"{ENV_WRITE_LIVE} not set to 1/true")
    ballot = load_accept_ballot(state_dir)
    ballot_path = str(Path(state_dir) / BALLOT_FILENAME)
    if require_ballot_file:
        if ballot is None:
            reasons.append(f"missing {BALLOT_FILENAME}")
        elif not bool(ballot.get("accepted")):
            reasons.append(f"{BALLOT_FILENAME} accepted!=true")
    elif ballot is not None and ballot.get("accepted") is False:
        reasons.append(f"{BALLOT_FILENAME} explicitly rejected")
    return LiveWriteGateResult(
        allowed=not reasons,
        reasons=reasons,
        ballot_path=ballot_path if ballot is not None else None,
    )


@dataclass
class AckValidation:
    ok: bool
    fill: dict[str, Any] | None = None
    reject_reason: str | None = None
    client_order_id: str | None = None


def client_order_id_for(order_id: str, *, asof: date) -> str:
    """Stable idempotent id for submit/ack (order_id + fill date)."""
    return f"{str(order_id).strip()}@{asof.isoformat()}"


def _pending_field(order: Any, name: str) -> Any:
    if isinstance(order, dict):
        return order.get(name)
    if hasattr(order, name):
        return getattr(order, name)
    # pandas Series
    try:
        return order[name]
    except Exception:  # noqa: BLE001
        return None


def validate_ack_against_pending(
    ack: Mapping[str, Any],
    pending_by_id: Mapping[str, Any],
    *,
    asof: date,
    open_prices: Mapping[str, float],
    slip: float,
    fees_tax_fn,
) -> AckValidation:
    """Require ack to match a pending order; refuse orphans / mismatches."""
    oid = str(ack.get("order_id") or ack.get("fill_id") or "").strip()
    if not oid:
        return AckValidation(ok=False, reject_reason="missing_order_id")
    order = pending_by_id.get(oid)
    if order is None:
        return AckValidation(ok=False, reject_reason=f"ack_not_in_pending:{oid}")

    o_code = str(_pending_field(order, "code") or "").strip()
    o_side = str(_pending_field(order, "side") or "").strip().upper()
    try:
        o_qty = int(float(_pending_field(order, "quantity") or 0))
    except (TypeError, ValueError):
        return AckValidation(ok=False, reject_reason=f"bad_pending_qty:{oid}")

    a_code = str(ack.get("code") or "").strip()
    a_side = str(ack.get("side") or "").strip().upper()
    try:
        a_qty = (
            int(float(ack["quantity"]))
            if "quantity" in ack and ack["quantity"] not in (None, "")
            else o_qty
        )
    except (TypeError, ValueError):
        return AckValidation(ok=False, reject_reason=f"bad_ack_qty:{oid}")

    if a_code and a_code != o_code:
        return AckValidation(ok=False, reject_reason=f"code_mismatch:{a_code}!={o_code}")
    if a_side and a_side != o_side:
        return AckValidation(ok=False, reject_reason=f"side_mismatch:{a_side}!={o_side}")
    if a_qty != o_qty:
        return AckValidation(ok=False, reject_reason=f"qty_mismatch:{a_qty}!={o_qty}")
    if o_qty < BOARD_LOT or o_qty % BOARD_LOT != 0:
        return AckValidation(ok=False, reject_reason=f"not_board_lot:{o_qty}")
    if o_side not in ("BUY", "SELL"):
        return AckValidation(ok=False, reject_reason=f"bad_side:{o_side}")

    code, side, q = o_code, o_side, o_qty
    if "fill_price" in ack and ack["fill_price"] not in (None, ""):
        try:
            fp = float(ack["fill_price"])
        except (TypeError, ValueError):
            return AckValidation(ok=False, reject_reason=f"bad_fill_price:{oid}")
        if fp <= 0:
            return AckValidation(ok=False, reject_reason=f"nonpositive_fill_price:{oid}")
    else:
        px = open_prices.get(code)
        if px is None or float(px) <= 0:
            return AckValidation(ok=False, reject_reason=f"missing_open_price:{code}")
        fp = float(px) * (1 + slip if side == "BUY" else 1 - slip)

    gross = q * fp
    fee = float(fees_tax_fn(side=side, code=code, gross=gross))
    sig = str(ack.get("signal_date") or _pending_field(order, "signal_date") or "")
    coid = str(ack.get("client_order_id") or client_order_id_for(oid, asof=asof))
    fill = {
        "fill_id": oid,
        "client_order_id": coid,
        "signal_date": sig,
        "fill_date": asof.isoformat(),
        "code": code,
        "side": side,
        "quantity": q,
        "fill_price": fp,
        "gross": gross,
        "fees_tax": fee,
        "slippage_bp": slip * 10000,
        "broker_ack": True,
    }
    return AckValidation(ok=True, fill=fill, client_order_id=coid)


@dataclass
class CircuitState:
    open: bool = False
    fail_count: int = 0
    last_reason: str = ""
    opened_at: str = ""
    trips: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "open": self.open,
            "fail_count": self.fail_count,
            "last_reason": self.last_reason,
            "opened_at": self.opened_at,
            "trips": self.trips[-20:],
        }


def load_circuit(state_dir: Path) -> CircuitState:
    path = Path(state_dir) / "broker_preflight" / CIRCUIT_FILENAME
    if not path.exists():
        return CircuitState()
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return CircuitState()
    return CircuitState(
        open=bool(obj.get("open")),
        fail_count=int(obj.get("fail_count") or 0),
        last_reason=str(obj.get("last_reason") or ""),
        opened_at=str(obj.get("opened_at") or ""),
        trips=list(obj.get("trips") or []),
    )


def save_circuit(state_dir: Path, circuit: CircuitState) -> Path:
    out = Path(state_dir) / "broker_preflight"
    out.mkdir(parents=True, exist_ok=True)
    path = out / CIRCUIT_FILENAME
    path.write_text(json.dumps(circuit.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def trip_circuit(
    state_dir: Path,
    reason: str,
    *,
    threshold: int = DEFAULT_CIRCUIT_FAIL_THRESHOLD,
) -> CircuitState:
    c = load_circuit(state_dir)
    c.fail_count += 1
    c.last_reason = reason
    c.trips.append(f"{datetime.now(tz=timezone.utc).isoformat()}:{reason}")
    if c.fail_count >= threshold:
        c.open = True
        c.opened_at = datetime.now(tz=timezone.utc).isoformat()
    save_circuit(state_dir, c)
    return c


def reset_circuit(state_dir: Path) -> CircuitState:
    c = CircuitState()
    save_circuit(state_dir, c)
    return c


def count_live_submits_today(state_dir: Path, asof: date) -> int:
    path = Path(state_dir) / "broker_preflight" / SUBMIT_LOG_FILENAME
    if not path.exists():
        return 0
    n = 0
    day = asof.isoformat()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if str(row.get("asof") or "")[:10] == day and row.get("live_written"):
            n += 1
    return n


def append_submit_log(state_dir: Path, row: Mapping[str, Any]) -> None:
    out = Path(state_dir) / "broker_preflight"
    out.mkdir(parents=True, exist_ok=True)
    path = out / SUBMIT_LOG_FILENAME
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(dict(row), ensure_ascii=False, default=str) + "\n")


def already_submitted(state_dir: Path, client_order_id: str) -> bool:
    """Idempotency: client_order_id already logged as live_written."""
    path = Path(state_dir) / "broker_preflight" / SUBMIT_LOG_FILENAME
    if not path.exists():
        return False
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("client_order_id") == client_order_id and row.get("live_written"):
            return True
    return False


def already_in_fills_csv(state_dir: Path, fill_id: str) -> bool:
    fills = Path(state_dir) / "fills.csv"
    if not fills.exists():
        return False
    import csv

    with fills.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if str(row.get("fill_id") or "") == str(fill_id):
                return True
    return False


@dataclass
class SubmitIntent:
    """Skeleton for a future broker API submit (no network)."""

    client_order_id: str
    order_id: str
    code: str
    side: str
    quantity: int
    asof: str
    status: str = "INTENT_ONLY"  # never auto-sent without API adapter

    def to_dict(self) -> dict[str, Any]:
        return {
            "client_order_id": self.client_order_id,
            "order_id": self.order_id,
            "code": self.code,
            "side": self.side,
            "quantity": self.quantity,
            "asof": self.asof,
            "status": self.status,
            "note": "No broker API wired — intent artifact only",
        }


def build_submit_intents(
    pending_rows: Sequence[Mapping[str, Any]],
    *,
    asof: date,
) -> list[SubmitIntent]:
    out: list[SubmitIntent] = []
    for row in pending_rows:
        oid = str(row.get("order_id") or "").strip()
        if not oid:
            continue
        out.append(
            SubmitIntent(
                client_order_id=client_order_id_for(oid, asof=asof),
                order_id=oid,
                code=str(row.get("code") or ""),
                side=str(row.get("side") or "").upper(),
                quantity=int(float(row.get("quantity") or 0)),
                asof=asof.isoformat(),
            )
        )
    return out


def write_submit_intents(state_dir: Path, asof: date, intents: Sequence[SubmitIntent]) -> Path:
    out = Path(state_dir) / "broker_preflight"
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"submit_intents_{asof.isoformat()}.json"
    payload = {
        "asof": asof.isoformat(),
        "n": len(intents),
        "intents": [i.to_dict() for i in intents],
        "generated_at_utc": datetime.now(tz=timezone.utc).isoformat(),
        "api_wired": False,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
