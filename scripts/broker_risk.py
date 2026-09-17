#!/usr/bin/env python3
"""Broker risk, order lifecycle, rate-limit, recovery (pre–real API).

Complements ``broker_safety`` with patterns aligned to public Yuanta SPARK
broker-server practice (idempotency / circuit / risk / reconcile) — still
**no network client**. Soft-Frozen live writes remain behind ACCEPT gates.

Features:
  1. Order state machine (PENDING→…→FILLED/CANCELLED/REJECTED/UNKNOWN)
  2. Pre-submit risk: panic switch, code blacklist, qty / notional caps
  3. Rate limit (per-minute write budget)
  4. Startup reconcile → unresolved list + manual resolve
  5. Circuit write-block vs read-ok helper
  6. Optional webhook alert stub (URL from env; fail-open on network errors)
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from broker_safety import load_circuit
from tw_share_lots import BOARD_LOT, is_board_lot_qty

ORDER_STATE_FILENAME = "broker_order_states.jsonl"
UNRESOLVED_FILENAME = "broker_unresolved.json"
RISK_CONFIG_FILENAME = "broker_risk.json"
PANIC_FILENAME = "broker_panic.json"
RATE_LIMIT_FILENAME = "broker_rate_limit.jsonl"
ALERT_LOG_FILENAME = "broker_alert_log.jsonl"

ENV_WEBHOOK = "E21_BROKER_ALERT_WEBHOOK"
DEFAULT_MAX_QTY_SHARES = 50 * BOARD_LOT  # 50 張
DEFAULT_MAX_NOTIONAL = 5_000_000.0  # NT$
DEFAULT_MAX_WRITES_PER_MINUTE = 30
DEFAULT_PRICE_DEVIATION = 0.15  # ±15% vs reference


class OrderState(str, Enum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    ACCEPTED = "ACCEPTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    UNKNOWN = "UNKNOWN"


_ALLOWED_TRANSITIONS: dict[OrderState, set[OrderState]] = {
    OrderState.PENDING: {
        OrderState.SUBMITTED,
        OrderState.REJECTED,
        OrderState.CANCELLED,
        OrderState.UNKNOWN,
    },
    OrderState.SUBMITTED: {
        OrderState.ACCEPTED,
        OrderState.REJECTED,
        OrderState.CANCELLED,
        OrderState.FILLED,
        OrderState.PARTIALLY_FILLED,
        OrderState.UNKNOWN,
    },
    OrderState.ACCEPTED: {
        OrderState.PARTIALLY_FILLED,
        OrderState.FILLED,
        OrderState.CANCELLED,
        OrderState.UNKNOWN,
    },
    OrderState.PARTIALLY_FILLED: {
        OrderState.PARTIALLY_FILLED,
        OrderState.FILLED,
        OrderState.CANCELLED,
        OrderState.UNKNOWN,
    },
    OrderState.FILLED: set(),
    OrderState.CANCELLED: set(),
    OrderState.REJECTED: set(),
    OrderState.UNKNOWN: {
        OrderState.FILLED,
        OrderState.CANCELLED,
        OrderState.REJECTED,
        OrderState.UNKNOWN,
    },
}


@dataclass
class OrderLifecycle:
    client_order_id: str
    order_id: str
    code: str
    side: str
    quantity: int
    state: str
    asof: str
    filled_qty: int = 0
    broker_order_no: str = ""
    updated_at_utc: str = ""
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _preflight(state_dir: Path) -> Path:
    out = Path(state_dir) / "broker_preflight"
    out.mkdir(parents=True, exist_ok=True)
    return out


def _utcnow() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def append_order_state(state_dir: Path, row: Mapping[str, Any]) -> None:
    path = _preflight(state_dir) / ORDER_STATE_FILENAME
    payload = dict(row)
    payload.setdefault("updated_at_utc", _utcnow())
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")


def load_order_states(state_dir: Path) -> dict[str, OrderLifecycle]:
    """Latest state per client_order_id."""
    path = _preflight(state_dir) / ORDER_STATE_FILENAME
    out: dict[str, OrderLifecycle] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        coid = str(row.get("client_order_id") or "").strip()
        if not coid:
            continue
        out[coid] = OrderLifecycle(
            client_order_id=coid,
            order_id=str(row.get("order_id") or ""),
            code=str(row.get("code") or ""),
            side=str(row.get("side") or "").upper(),
            quantity=int(float(row.get("quantity") or 0)),
            state=str(row.get("state") or OrderState.UNKNOWN.value),
            asof=str(row.get("asof") or ""),
            filled_qty=int(float(row.get("filled_qty") or 0)),
            broker_order_no=str(row.get("broker_order_no") or ""),
            updated_at_utc=str(row.get("updated_at_utc") or ""),
            note=str(row.get("note") or ""),
        )
    return out


def _as_state(v: OrderState | str) -> OrderState:
    if isinstance(v, OrderState):
        return v
    return OrderState(str(v))


def transition_order(
    state_dir: Path,
    *,
    client_order_id: str,
    order_id: str,
    code: str,
    side: str,
    quantity: int,
    asof: date,
    new_state: OrderState | str,
    filled_qty: int | None = None,
    broker_order_no: str = "",
    note: str = "",
    force: bool = False,
) -> OrderLifecycle:
    """Append a state transition; refuse illegal moves unless ``force`` (manual resolve)."""
    target = _as_state(new_state)
    cur = load_order_states(state_dir).get(client_order_id)
    if cur is None:
        prev: OrderState | None = None
    else:
        prev = OrderState(cur.state)

    if prev is not None and not force:
        allowed = _ALLOWED_TRANSITIONS.get(prev, set())
        if target != prev and target not in allowed:
            raise ValueError(f"illegal_transition:{prev.value}->{target.value}:{client_order_id}")

    fq = 0 if cur is None else cur.filled_qty
    if filled_qty is not None:
        fq = int(filled_qty)
    row = OrderLifecycle(
        client_order_id=client_order_id,
        order_id=order_id or (cur.order_id if cur else ""),
        code=code or (cur.code if cur else ""),
        side=(side or (cur.side if cur else "")).upper(),
        quantity=int(quantity if quantity else (cur.quantity if cur else 0)),
        state=target.value,
        asof=asof.isoformat(),
        filled_qty=fq,
        broker_order_no=broker_order_no or (cur.broker_order_no if cur else ""),
        updated_at_utc=_utcnow(),
        note=note or (cur.note if cur else ""),
    )
    append_order_state(state_dir, row.to_dict())
    return row


# --- Risk -----------------------------------------------------------------


@dataclass
class RiskConfig:
    panic: bool = False
    blacklist: list[str] = field(default_factory=list)
    max_qty_shares: int = DEFAULT_MAX_QTY_SHARES
    max_notional: float = DEFAULT_MAX_NOTIONAL
    max_price_deviation: float = DEFAULT_PRICE_DEVIATION
    max_writes_per_minute: int = DEFAULT_MAX_WRITES_PER_MINUTE

    @classmethod
    def load(cls, state_dir: Path) -> "RiskConfig":
        path = _preflight(state_dir) / RISK_CONFIG_FILENAME
        cfg = cls()
        if path.exists():
            try:
                obj = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                obj = {}
            if isinstance(obj, dict):
                cfg.panic = bool(obj.get("panic", cfg.panic))
                cfg.blacklist = [str(x) for x in (obj.get("blacklist") or [])]
                cfg.max_qty_shares = int(obj.get("max_qty_shares") or cfg.max_qty_shares)
                cfg.max_notional = float(obj.get("max_notional") or cfg.max_notional)
                cfg.max_price_deviation = float(
                    obj.get("max_price_deviation") or cfg.max_price_deviation
                )
                cfg.max_writes_per_minute = int(
                    obj.get("max_writes_per_minute") or cfg.max_writes_per_minute
                )
        panic_path = _preflight(state_dir) / PANIC_FILENAME
        if panic_path.exists():
            try:
                pobj = json.loads(panic_path.read_text(encoding="utf-8"))
                if isinstance(pobj, dict) and "panic" in pobj:
                    cfg.panic = bool(pobj.get("panic"))
            except (OSError, json.JSONDecodeError):
                cfg.panic = True
        return cfg

    def save(self, state_dir: Path) -> Path:
        path = _preflight(state_dir) / RISK_CONFIG_FILENAME
        path.write_text(
            json.dumps(asdict(self), indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        return path


def set_panic(state_dir: Path, panic: bool, *, reason: str = "") -> None:
    path = _preflight(state_dir) / PANIC_FILENAME
    path.write_text(
        json.dumps(
            {"panic": bool(panic), "reason": reason, "updated_at_utc": _utcnow()},
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    cfg = RiskConfig.load(state_dir)
    cfg.panic = bool(panic)
    cfg.save(state_dir)
    emit_alert(
        state_dir,
        kind="panic_on" if panic else "panic_off",
        message=reason or ("panic enabled" if panic else "panic cleared"),
    )


@dataclass
class RiskCheckResult:
    allowed: bool
    reasons: list[str] = field(default_factory=list)


def pre_submit_risk_check(
    state_dir: Path,
    *,
    code: str,
    side: str,
    quantity: int,
    price: float | None = None,
    reference_price: float | None = None,
) -> RiskCheckResult:
    """Fail-closed risk gate before broker submit / live fill write."""
    cfg = RiskConfig.load(state_dir)
    reasons: list[str] = []
    if cfg.panic:
        reasons.append("panic_enabled")
    code_s = str(code).strip()
    if code_s in set(cfg.blacklist):
        reasons.append(f"blacklist:{code_s}")
    q = int(quantity)
    if not is_board_lot_qty(q) or q <= 0:
        reasons.append(f"not_board_lot:{q}")
    if q > int(cfg.max_qty_shares):
        reasons.append(f"qty_cap:{q}>{cfg.max_qty_shares}")
    px = float(price) if price not in (None, "") else None
    if px is not None and px > 0:
        notional = abs(px * q)
        if notional > float(cfg.max_notional):
            reasons.append(f"notional_cap:{notional}>{cfg.max_notional}")
        ref = float(reference_price) if reference_price not in (None, "") else None
        if ref is not None and ref > 0:
            dev = abs(px - ref) / ref
            if dev > float(cfg.max_price_deviation):
                reasons.append(f"price_deviation:{dev:.4f}>{cfg.max_price_deviation}")
    side_u = str(side).upper()
    if side_u not in ("BUY", "SELL"):
        reasons.append(f"bad_side:{side}")
    return RiskCheckResult(allowed=not reasons, reasons=reasons)


# --- Rate limit -----------------------------------------------------------


def _rate_limit_count_last_minute(state_dir: Path, *, now: float | None = None) -> int:
    path = _preflight(state_dir) / RATE_LIMIT_FILENAME
    if not path.exists():
        return 0
    now_f = time.time() if now is None else float(now)
    n = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        ts = float(row.get("ts") or 0)
        if now_f - ts <= 60.0 and row.get("write"):
            n += 1
    return n


def check_rate_limit(state_dir: Path, *, now: float | None = None) -> RiskCheckResult:
    cfg = RiskConfig.load(state_dir)
    n = _rate_limit_count_last_minute(state_dir, now=now)
    if n >= int(cfg.max_writes_per_minute):
        return RiskCheckResult(
            allowed=False,
            reasons=[f"rate_limited:{n}>={cfg.max_writes_per_minute}/min"],
        )
    return RiskCheckResult(allowed=True)


def record_rate_limit_write(state_dir: Path, *, client_order_id: str = "") -> None:
    path = _preflight(state_dir) / RATE_LIMIT_FILENAME
    with path.open("a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "ts": time.time(),
                    "write": True,
                    "client_order_id": client_order_id,
                    "at_utc": _utcnow(),
                }
            )
            + "\n"
        )


# --- Circuit read/write split --------------------------------------------


@dataclass
class CircuitAccess:
    writes_allowed: bool
    reads_allowed: bool
    reason: str = ""


def circuit_access(state_dir: Path) -> CircuitAccess:
    """When circuit is open: block writes, allow reads (queries / shadow)."""
    c = load_circuit(state_dir)
    if c.open:
        return CircuitAccess(
            writes_allowed=False,
            reads_allowed=True,
            reason=f"circuit_open:{c.last_reason}",
        )
    return CircuitAccess(writes_allowed=True, reads_allowed=True)


# --- Recovery -------------------------------------------------------------


TERMINAL_OK = {OrderState.FILLED.value, OrderState.CANCELLED.value, OrderState.REJECTED.value}
NEEDS_RESOLVE = {
    OrderState.UNKNOWN.value,
    OrderState.SUBMITTED.value,
    OrderState.ACCEPTED.value,
    OrderState.PARTIALLY_FILLED.value,
}


def run_startup_reconcile(state_dir: Path, *, asof: date | None = None) -> dict[str, Any]:
    """Scan lifecycle log; mark non-terminal / unknown as unresolved for humans."""
    states = load_order_states(state_dir)
    unresolved: list[dict[str, Any]] = []
    for coid, row in states.items():
        if row.state in TERMINAL_OK:
            continue
        if row.state in NEEDS_RESOLVE or row.state == OrderState.PENDING.value:
            # PENDING with no submit is fine overnight; only flag if submitted-ish or UNKNOWN
            if row.state == OrderState.PENDING.value:
                continue
            unresolved.append(row.to_dict())
    payload = {
        "asof": (asof or date.today()).isoformat(),
        "n_unresolved": len(unresolved),
        "unresolved": unresolved,
        "reconciled_at_utc": _utcnow(),
        "note": "Manual resolve via resolve_unresolved_order() before live writes",
    }
    path = _preflight(state_dir) / UNRESOLVED_FILENAME
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if unresolved:
        emit_alert(
            state_dir,
            kind="recovery_unresolved",
            message=f"{len(unresolved)} broker orders need manual resolve",
        )
    return payload


def load_unresolved(state_dir: Path) -> dict[str, Any]:
    path = _preflight(state_dir) / UNRESOLVED_FILENAME
    if not path.exists():
        return {"n_unresolved": 0, "unresolved": []}
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"n_unresolved": 0, "unresolved": []}
    return obj if isinstance(obj, dict) else {"n_unresolved": 0, "unresolved": []}


def has_blocking_unresolved(state_dir: Path) -> bool:
    return int(load_unresolved(state_dir).get("n_unresolved") or 0) > 0


def resolve_unresolved_order(
    state_dir: Path,
    client_order_id: str,
    *,
    final_state: OrderState | str,
    note: str = "manual_resolve",
    asof: date | None = None,
) -> OrderLifecycle:
    """Human ACCEPT-style resolve for UNKNOWN / stuck orders."""
    states = load_order_states(state_dir)
    cur = states.get(client_order_id)
    if cur is None:
        raise KeyError(f"unknown_client_order_id:{client_order_id}")
    target = _as_state(final_state)
    if target not in (
        OrderState.FILLED,
        OrderState.CANCELLED,
        OrderState.REJECTED,
    ):
        raise ValueError(f"resolve_requires_terminal:{target.value}")
    row = transition_order(
        state_dir,
        client_order_id=client_order_id,
        order_id=cur.order_id,
        code=cur.code,
        side=cur.side,
        quantity=cur.quantity,
        asof=asof or date.today(),
        new_state=target,
        filled_qty=cur.quantity if target == OrderState.FILLED else cur.filled_qty,
        broker_order_no=cur.broker_order_no,
        note=note,
        force=True,
    )
    # Refresh unresolved snapshot
    run_startup_reconcile(state_dir, asof=asof or date.today())
    emit_alert(
        state_dir,
        kind="recovery_resolved",
        message=f"{client_order_id} -> {target.value}",
    )
    return row


# --- Combined pre-submit gate --------------------------------------------


@dataclass
class PreSubmitGateResult:
    allowed: bool
    reasons: list[str] = field(default_factory=list)


def pre_submit_full_gate(
    state_dir: Path,
    *,
    code: str,
    side: str,
    quantity: int,
    price: float | None = None,
    reference_price: float | None = None,
) -> PreSubmitGateResult:
    """Aggregate risk + rate limit + circuit write + unresolved blocking."""
    reasons: list[str] = []
    access = circuit_access(state_dir)
    if not access.writes_allowed:
        reasons.append(access.reason or "writes_blocked")
    if has_blocking_unresolved(state_dir):
        reasons.append("unresolved_orders_present")
    risk = pre_submit_risk_check(
        state_dir,
        code=code,
        side=side,
        quantity=quantity,
        price=price,
        reference_price=reference_price,
    )
    if not risk.allowed:
        reasons.extend(risk.reasons)
    rate = check_rate_limit(state_dir)
    if not rate.allowed:
        reasons.extend(rate.reasons)
    return PreSubmitGateResult(allowed=not reasons, reasons=reasons)


# --- Alerts ---------------------------------------------------------------


def emit_alert(state_dir: Path, *, kind: str, message: str) -> None:
    """Append local alert log; optionally POST JSON to webhook (best-effort)."""
    path = _preflight(state_dir) / ALERT_LOG_FILENAME
    row = {
        "kind": kind,
        "message": message,
        "at_utc": _utcnow(),
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    url = os.environ.get(ENV_WEBHOOK, "").strip()
    if not url:
        return
    try:
        data = json.dumps({"text": f"[broker:{kind}] {message}", **row}).encode("utf-8")
        req = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"}, method="POST"
        )
        with urllib.request.urlopen(req, timeout=3) as resp:  # noqa: S310
            resp.read()
    except (urllib.error.URLError, TimeoutError, OSError):
        # Fail-open: never block trading path on alert delivery.
        return


def list_alerts(state_dir: Path, *, limit: int = 50) -> list[dict[str, Any]]:
    path = _preflight(state_dir) / ALERT_LOG_FILENAME
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows[-limit:]
