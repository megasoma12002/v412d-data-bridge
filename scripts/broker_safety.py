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
     (open → cooldown half-open probe → close on success)
  7. Process lock (fcntl) around live-write / confirm+reserve
  8. Stable Soft-Frozen order_id via ``live_ledger.make_order_id``
  9. Broker dedupe key (includes qty) + pre-submit confirm (no network)
"""
from __future__ import annotations

import fcntl
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
DEFAULT_CIRCUIT_COOLDOWN_SECONDS = 30.0
BALLOT_FILENAME = "broker_live_write_accept.json"
CIRCUIT_FILENAME = "broker_circuit.json"
CIRCUIT_CLOSED = "closed"
CIRCUIT_OPEN = "open"
CIRCUIT_HALF_OPEN = "half_open"
SUBMIT_LOG_FILENAME = "broker_submit_log.jsonl"
DEDUPE_LOG_FILENAME = "broker_dedupe_log.jsonl"
LOCK_FILENAME = "broker_live.lock"


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
    require_ballot_file: bool = True,
    env_write_live: bool | None = None,
) -> LiveWriteGateResult:
    """Hard gate for mutating Soft-Frozen fills via broker port.

    All of: LiveConfig ACCEPT flag, env ``E21_BROKER_WRITE_LIVE``, and
    a ballot JSON with ``accepted: true`` (``require_ballot_file`` defaults
    True — Soft-Frozen live writes must not rely on env+flag alone).
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


def broker_dedupe_key(
    *,
    client_order_id: str,
    code: str,
    side: str,
    quantity: int,
) -> str:
    """Broker-side dedupe identity (includes qty; stronger than Soft-Frozen order_id)."""
    return (
        f"{str(client_order_id).strip()}|"
        f"{str(code).strip()}|"
        f"{str(side).strip().upper()}|"
        f"{int(quantity)}"
    )


class ProcessLock:
    """Exclusive fcntl lock under ``state_dir/broker_preflight/``.

    Fail-closed: ``blocking=False`` raises ``BlockingIOError`` if another
    process holds the lock (caller must not proceed with live write).
    """

    def __init__(
        self,
        state_dir: Path,
        *,
        name: str = LOCK_FILENAME,
        blocking: bool = True,
    ) -> None:
        self._path = Path(state_dir) / "broker_preflight" / name
        self._blocking = bool(blocking)
        self._fh: Any = None

    def __enter__(self) -> "ProcessLock":
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = open(self._path, "a+", encoding="utf-8")
        flags = fcntl.LOCK_EX if self._blocking else (fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            fcntl.flock(self._fh.fileno(), flags)
        except BlockingIOError:
            self._fh.close()
            self._fh = None
            raise
        self._fh.seek(0)
        self._fh.truncate()
        self._fh.write(
            json.dumps(
                {
                    "pid": os.getpid(),
                    "held_at_utc": datetime.now(tz=timezone.utc).isoformat(),
                }
            )
            + "\n"
        )
        self._fh.flush()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._fh is not None:
            try:
                fcntl.flock(self._fh.fileno(), fcntl.LOCK_UN)
            finally:
                self._fh.close()
                self._fh = None


def already_broker_deduped(state_dir: Path, dedupe_key: str) -> bool:
    path = Path(state_dir) / "broker_preflight" / DEDUPE_LOG_FILENAME
    if not path.exists():
        return False
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as e:
            raise SystemExit(
                f"Corrupt broker dedupe log {path}:{line_no}: {e}. "
                "Repair or quarantine before broker live-write."
            ) from e
        if row.get("dedupe_key") == dedupe_key and row.get("reserved"):
            return True
    return False


def reserve_broker_dedupe(
    state_dir: Path,
    *,
    dedupe_key: str,
    client_order_id: str,
    asof: date,
) -> None:
    out = Path(state_dir) / "broker_preflight"
    out.mkdir(parents=True, exist_ok=True)
    path = out / DEDUPE_LOG_FILENAME
    with path.open("a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "dedupe_key": dedupe_key,
                    "client_order_id": client_order_id,
                    "asof": asof.isoformat(),
                    "reserved": True,
                    "reserved_at_utc": datetime.now(tz=timezone.utc).isoformat(),
                    "api_wired": False,
                },
                ensure_ascii=False,
            )
            + "\n"
        )


@dataclass
class SubmitConfirmResult:
    allowed: bool
    reasons: list[str] = field(default_factory=list)
    dedupe_key: str | None = None


def confirm_before_broker_submit(
    *,
    state_dir: Path,
    client_order_id: str,
    code: str,
    side: str,
    quantity: int,
    asof: date,
    confirmed: bool,
    config_accepted: bool,
    env_write_live: bool | None = None,
    require_ballot_file: bool = True,
) -> SubmitConfirmResult:
    """Pre-submit confirm for a future broker API adapter (no network).

    Fail-closed unless: explicit ``confirmed=True``, live_write_gate, circuit
    closed, and dedupe key not already reserved. Call under ``ProcessLock``.
    """
    reasons: list[str] = []
    dkey = broker_dedupe_key(
        client_order_id=client_order_id, code=code, side=side, quantity=quantity
    )
    if not confirmed:
        reasons.append("confirmed=False (ops/API adapter must explicitly confirm)")
    gate = live_write_gate(
        config_accepted=config_accepted,
        state_dir=Path(state_dir),
        require_ballot_file=require_ballot_file,
        env_write_live=env_write_live,
    )
    if not gate.allowed:
        reasons.extend(gate.reasons)
    ok_write, circuit = allow_circuit_write(Path(state_dir))
    if not ok_write:
        reasons.append(f"circuit_open:{circuit.last_reason or circuit.mode}")
    if already_broker_deduped(Path(state_dir), dkey):
        reasons.append(f"broker_dedupe_hit:{dkey}")
    if already_submitted(Path(state_dir), client_order_id):
        reasons.append(f"already_submitted:{client_order_id}")
    return SubmitConfirmResult(allowed=not reasons, reasons=reasons, dedupe_key=dkey)


def confirm_and_reserve_broker_submit(
    *,
    state_dir: Path,
    client_order_id: str,
    code: str,
    side: str,
    quantity: int,
    asof: date,
    confirmed: bool,
    config_accepted: bool,
    env_write_live: bool | None = None,
    require_ballot_file: bool = True,
) -> SubmitConfirmResult:
    """Confirm then reserve dedupe key (must run under ProcessLock)."""
    result = confirm_before_broker_submit(
        state_dir=state_dir,
        client_order_id=client_order_id,
        code=code,
        side=side,
        quantity=quantity,
        asof=asof,
        confirmed=confirmed,
        config_accepted=config_accepted,
        env_write_live=env_write_live,
        require_ballot_file=require_ballot_file,
    )
    if result.allowed and result.dedupe_key:
        reserve_broker_dedupe(
            Path(state_dir),
            dedupe_key=result.dedupe_key,
            client_order_id=client_order_id,
            asof=asof,
        )
    return result


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
    expected_coid = client_order_id_for(oid, asof=asof)
    if ack.get("client_order_id") not in (None, ""):
        coid = str(ack.get("client_order_id")).strip()
        if coid != expected_coid:
            return AckValidation(
                ok=False,
                reject_reason=f"client_order_id_mismatch:{coid}!={expected_coid}",
            )
    else:
        coid = expected_coid
    dkey = broker_dedupe_key(
        client_order_id=coid, code=code, side=side, quantity=q
    )
    # Explicit ops/API confirm only — fixture or future SPARK adapter must set
    # ops_confirmed/confirmed; never infer from ack presence alone.
    ops_confirmed = bool(ack.get("ops_confirmed") or ack.get("confirmed"))
    fill = {
        "fill_id": oid,
        "client_order_id": coid,
        "broker_dedupe_key": dkey,
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
        "ops_confirmed": ops_confirmed,
    }
    return AckValidation(ok=True, fill=fill, client_order_id=coid)


@dataclass
class CircuitState:
    open: bool = False
    mode: str = CIRCUIT_CLOSED  # closed | open | half_open
    fail_count: int = 0
    last_reason: str = ""
    opened_at: str = ""
    cooldown_seconds: float = DEFAULT_CIRCUIT_COOLDOWN_SECONDS
    rejections: int = 0
    half_open_probe_used: bool = False
    trips: list[str] = field(default_factory=list)
    load_error: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "open": self.open,
            "mode": self.mode,
            "fail_count": self.fail_count,
            "last_reason": self.last_reason,
            "opened_at": self.opened_at,
            "cooldown_seconds": self.cooldown_seconds,
            "rejections": self.rejections,
            "half_open_probe_used": self.half_open_probe_used,
            "trips": self.trips[-20:],
        }


def _parse_opened_at(opened_at: str) -> datetime | None:
    text = str(opened_at or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def load_circuit(state_dir: Path) -> CircuitState:
    """Load circuit; corrupt/unreadable file → fail-closed OPEN (blocks writes)."""
    path = Path(state_dir) / "broker_preflight" / CIRCUIT_FILENAME
    if not path.exists():
        return CircuitState()
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return CircuitState(
            open=True,
            mode=CIRCUIT_OPEN,
            last_reason="circuit_corrupt_fail_closed",
            opened_at=datetime.now(tz=timezone.utc).isoformat(),
            load_error=True,
        )
    if not isinstance(obj, dict):
        return CircuitState(
            open=True,
            mode=CIRCUIT_OPEN,
            last_reason="circuit_invalid_fail_closed",
            opened_at=datetime.now(tz=timezone.utc).isoformat(),
            load_error=True,
        )
    mode = str(obj.get("mode") or "").strip().lower()
    opened = bool(obj.get("open"))
    if not mode:
        mode = CIRCUIT_OPEN if opened else CIRCUIT_CLOSED
    if mode not in (CIRCUIT_CLOSED, CIRCUIT_OPEN, CIRCUIT_HALF_OPEN):
        mode = CIRCUIT_OPEN if opened else CIRCUIT_CLOSED
    return CircuitState(
        open=opened or mode in (CIRCUIT_OPEN, CIRCUIT_HALF_OPEN),
        mode=mode,
        fail_count=int(obj.get("fail_count") or 0),
        last_reason=str(obj.get("last_reason") or ""),
        opened_at=str(obj.get("opened_at") or ""),
        cooldown_seconds=float(obj.get("cooldown_seconds") or DEFAULT_CIRCUIT_COOLDOWN_SECONDS),
        rejections=int(obj.get("rejections") or 0),
        half_open_probe_used=bool(obj.get("half_open_probe_used")),
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
    """Record a failure; open after consecutive threshold (re-opens from half_open)."""
    c = load_circuit(state_dir)
    if c.load_error:
        # Keep fail-closed corrupt state; still record reason.
        c.last_reason = f"{c.last_reason};{reason}" if c.last_reason else reason
        save_circuit(state_dir, c)
        return c
    c.fail_count += 1
    c.last_reason = reason
    c.trips.append(f"{datetime.now(tz=timezone.utc).isoformat()}:{reason}")
    if c.fail_count >= threshold or c.mode == CIRCUIT_HALF_OPEN:
        c.open = True
        c.mode = CIRCUIT_OPEN
        c.opened_at = datetime.now(tz=timezone.utc).isoformat()
        c.half_open_probe_used = False
    save_circuit(state_dir, c)
    return c


def record_circuit_success(state_dir: Path) -> CircuitState:
    """Close breaker after a successful write (incl. half-open probe)."""
    c = load_circuit(state_dir)
    if c.load_error:
        return c
    c.open = False
    c.mode = CIRCUIT_CLOSED
    c.fail_count = 0
    c.last_reason = ""
    c.opened_at = ""
    c.half_open_probe_used = False
    save_circuit(state_dir, c)
    return c


def allow_circuit_write(
    state_dir: Path, *, consume_probe: bool = True
) -> tuple[bool, CircuitState]:
    """Whether a write may proceed; OPEN→HALF_OPEN after cooldown for one probe.

    Fail-closed: corrupt circuit, or OPEN with missing/unparseable opened_at,
    blocks writes. Half-open allows exactly one probe until success/trip.

    ``consume_probe=False`` peeks without burning the half-open slot (for
    ``circuit_access`` / preflight). Confirm/submit paths must use default True.
    """
    c = load_circuit(state_dir)
    if c.load_error:
        return False, c
    if c.mode == CIRCUIT_CLOSED and not c.open:
        return True, c
    if c.mode == CIRCUIT_HALF_OPEN:
        if c.half_open_probe_used:
            c.rejections += 1
            save_circuit(state_dir, c)
            return False, c
        if consume_probe:
            c.half_open_probe_used = True
            save_circuit(state_dir, c)
        return True, c
    # OPEN (or legacy open=True): wait for cooldown then allow a half-open probe
    opened = _parse_opened_at(c.opened_at)
    if opened is None:
        # Missing timestamp while open → do not auto-probe (fail-closed).
        c.rejections += 1
        c.last_reason = c.last_reason or "circuit_open_missing_opened_at"
        save_circuit(state_dir, c)
        return False, c
    now = datetime.now(tz=timezone.utc)
    elapsed = (now - opened).total_seconds()
    if elapsed >= float(c.cooldown_seconds):
        c.mode = CIRCUIT_HALF_OPEN
        c.open = True
        if consume_probe:
            c.half_open_probe_used = True
        else:
            c.half_open_probe_used = False
        save_circuit(state_dir, c)
        return True, c
    c.rejections += 1
    save_circuit(state_dir, c)
    return False, c


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
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as e:
            raise SystemExit(
                f"Corrupt broker submit log {path}:{line_no}: {e}. "
                "Repair before counting live submits."
            ) from e
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
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as e:
            raise SystemExit(
                f"Corrupt broker submit log {path}:{line_no}: {e}. "
                "Repair before idempotency check."
            ) from e
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
    status: str = "INTENT_ONLY"  # never auto-sent without API adapter + confirm

    def to_dict(self) -> dict[str, Any]:
        dkey = broker_dedupe_key(
            client_order_id=self.client_order_id,
            code=self.code,
            side=self.side,
            quantity=self.quantity,
        )
        return {
            "client_order_id": self.client_order_id,
            "order_id": self.order_id,
            "code": self.code,
            "side": self.side,
            "quantity": self.quantity,
            "asof": self.asof,
            "broker_dedupe_key": dkey,
            "status": self.status,
            "require_confirm_before_submit": True,
            "note": "No broker API wired — intent artifact only; confirm_and_reserve required",
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
