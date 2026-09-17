#!/usr/bin/env python3
"""Yuanta SPARK adapter skeleton (offline — no DLL / no network).

Maps Soft-Frozen pending / ``broker_safety`` submit intents ↔ SPARK
``StockOrder`` field shapes and ``SendStockOrder`` OnResponse rows into the
existing ``broker_acks`` / fill schema.

Hard rules:
  - ``API_WIRED = False`` until a separate ACCEPT wires pythonnet + DLL
  - Never import ``YuantaSparkAPI`` / ``pythonnet`` here
  - Soft-Frozen ``fills.csv`` is still gated by ``broker_safety`` + LiveConfig
  - ``BasketNo`` ≤ 32 alphanumeric (official SPARK limit)
  - ``OrderQty`` is 張 (board lots), not shares
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from tw_share_lots import BOARD_LOT, is_board_lot_qty

API_WIRED = False
BASKET_NO_MAX = 32
BASKET_MAP_FILENAME = "spark_basket_map.jsonl"


class SparkNotWiredError(RuntimeError):
    """Raised if code paths attempt a live SPARK call while skeleton-only."""


def assert_not_wired() -> None:
    if API_WIRED:
        return
    # Skeleton stays fail-closed for network entrypoints.
    raise SparkNotWiredError(
        "Yuanta SPARK network client is not wired (API_WIRED=False); "
        "offline mapping only — needs ACCEPT + DLL/pythonnet adapter"
    )


def shares_to_order_qty(shares: int | float) -> int:
    """Convert Soft-Frozen share qty → SPARK ``OrderQty`` (張)."""
    q = int(shares)
    if not is_board_lot_qty(q) or q <= 0:
        raise ValueError(f"not_board_lot_shares:{q}")
    return q // BOARD_LOT


def order_qty_to_shares(order_qty: int | float) -> int:
    """SPARK 張 → Soft-Frozen shares."""
    lots = int(order_qty)
    if lots <= 0:
        raise ValueError(f"nonpositive_order_qty:{lots}")
    return lots * BOARD_LOT


def buy_sell_flag(side: str) -> str:
    s = str(side).strip().upper()
    if s == "BUY":
        return "B"
    if s == "SELL":
        return "S"
    raise ValueError(f"bad_side:{side}")


def side_from_flag(flag: str) -> str:
    f = str(flag).strip().upper()
    if f == "B":
        return "BUY"
    if f == "S":
        return "SELL"
    raise ValueError(f"bad_buy_sell_flag:{flag}")


def basket_no_for(client_order_id: str, *, max_len: int = BASKET_NO_MAX) -> str:
    """Map ``client_order_id`` → SPARK ``BasketNo`` (≤32 A–Z / 0–9).

    Strips non-alnum; if still too long / empty, uses a stable SHA-256 prefix
    so regenerating the same client_order_id yields the same BasketNo.
    """
    coid = str(client_order_id).strip()
    if not coid:
        raise ValueError("empty_client_order_id")
    alnum = re.sub(r"[^A-Za-z0-9]", "", coid)
    if 0 < len(alnum) <= max_len:
        return alnum
    digest = hashlib.sha256(coid.encode("utf-8")).hexdigest()
    # Keep a short human hint when possible, then hash to fill.
    hint = (alnum[:8] if alnum else "Y")[: max(1, max_len - 16)]
    out = (hint + digest)[:max_len]
    if not re.fullmatch(r"[A-Za-z0-9]+", out):
        out = digest[:max_len]
    return out


def append_basket_map(
    state_dir: Path,
    *,
    basket_no: str,
    client_order_id: str,
    order_id: str,
    asof: date,
) -> None:
    out = Path(state_dir) / "broker_preflight"
    out.mkdir(parents=True, exist_ok=True)
    path = out / BASKET_MAP_FILENAME
    with path.open("a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "basket_no": basket_no,
                    "client_order_id": client_order_id,
                    "order_id": order_id,
                    "asof": asof.isoformat(),
                    "recorded_at_utc": datetime.now(tz=timezone.utc).isoformat(),
                    "api_wired": API_WIRED,
                },
                ensure_ascii=False,
            )
            + "\n"
        )


def lookup_client_order_id(state_dir: Path, basket_no: str) -> str | None:
    path = Path(state_dir) / "broker_preflight" / BASKET_MAP_FILENAME
    if not path.exists():
        return None
    found: str | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("basket_no") == basket_no:
            found = str(row.get("client_order_id") or "") or None
    return found


@dataclass
class SparkStockOrderIntent:
    """Offline mirror of SPARK ``StockOrder`` (domestic cash board)."""

    Identify: int
    Account: str
    OrderNo: str
    TradeDate: str  # yyyy/MM/dd
    APCode: int  # 0 = 一般整股
    TradeKind: int  # 0 = 委託單
    OrderType: str  # "0" = 現貨
    StkCode: str
    BuySell: str  # B/S
    PriceFlag: str  # " " limit · M market
    Price: float
    BasketNo: str
    OrderQty: int  # 張
    Time_in_force: str  # 0 ROD
    client_order_id: str
    order_id: str
    shares: int
    status: str = "INTENT_ONLY"
    api_wired: bool = False
    note: str = "Offline skeleton — no SendStockOrder"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def spark_stock_order_fields(self) -> dict[str, Any]:
        """Fields that would be copied onto a live ``StockOrder`` object."""
        return {
            "Identify": self.Identify,
            "Account": self.Account,
            "OrderNo": self.OrderNo,
            "TradeDate": self.TradeDate,
            "APCode": self.APCode,
            "TradeKind": self.TradeKind,
            "OrderType": self.OrderType,
            "StkCode": self.StkCode,
            "BuySell": self.BuySell,
            "PriceFlag": self.PriceFlag,
            "Price": self.Price,
            "BasketNo": self.BasketNo,
            "OrderQty": self.OrderQty,
            "Time_in_force": self.Time_in_force,
        }


def build_stock_order_intent(
    *,
    order_id: str,
    client_order_id: str,
    code: str,
    side: str,
    shares: int,
    asof: date,
    account: str = "",
    identify: int = 1,
    price: float | None = None,
    market_order: bool = False,
) -> SparkStockOrderIntent:
    lots = shares_to_order_qty(shares)
    basket = basket_no_for(client_order_id)
    if market_order:
        price_flag, px = "M", 0.0
    else:
        price_flag, px = " ", float(price or 0.0)
    return SparkStockOrderIntent(
        Identify=int(identify),
        Account=str(account or ""),
        OrderNo="",
        TradeDate=asof.strftime("%Y/%m/%d"),
        APCode=0,
        TradeKind=0,
        OrderType="0",
        StkCode=str(code).strip(),
        BuySell=buy_sell_flag(side),
        PriceFlag=price_flag,
        Price=px,
        BasketNo=basket,
        OrderQty=lots,
        Time_in_force="0",
        client_order_id=str(client_order_id),
        order_id=str(order_id),
        shares=int(shares),
        api_wired=API_WIRED,
    )


def build_intents_from_pending(
    pending_rows: Sequence[Mapping[str, Any]],
    *,
    asof: date,
    account: str = "",
) -> list[SparkStockOrderIntent]:
    from broker_safety import client_order_id_for

    out: list[SparkStockOrderIntent] = []
    for i, row in enumerate(pending_rows, start=1):
        oid = str(row.get("order_id") or "").strip()
        if not oid:
            continue
        coid = str(row.get("client_order_id") or client_order_id_for(oid, asof=asof))
        out.append(
            build_stock_order_intent(
                order_id=oid,
                client_order_id=coid,
                code=str(row.get("code") or ""),
                side=str(row.get("side") or ""),
                shares=int(float(row.get("quantity") or 0)),
                asof=asof,
                account=account,
                identify=i,
            )
        )
    return out


def write_spark_intents(
    state_dir: Path,
    asof: date,
    intents: Sequence[SparkStockOrderIntent],
) -> Path:
    out = Path(state_dir) / "broker_preflight"
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"spark_intents_{asof.isoformat()}.json"
    for intent in intents:
        append_basket_map(
            state_dir,
            basket_no=intent.BasketNo,
            client_order_id=intent.client_order_id,
            order_id=intent.order_id,
            asof=asof,
        )
    payload = {
        "asof": asof.isoformat(),
        "n": len(intents),
        "api_wired": API_WIRED,
        "intents": [i.to_dict() for i in intents],
        "generated_at_utc": datetime.now(tz=timezone.utc).isoformat(),
        "note": "Offline SPARK StockOrder mapping only — no network submit",
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


@dataclass
class SparkSubmitResult:
    ok: bool
    broker_ack: dict[str, Any] | None = None
    reject_reason: str | None = None


def map_send_stock_order_row(
    row: Mapping[str, Any],
    *,
    intent: SparkStockOrderIntent | None = None,
    order_id: str | None = None,
    code: str | None = None,
    side: str | None = None,
    shares: int | None = None,
    fill_price: float | None = None,
    signal_date: str = "",
) -> SparkSubmitResult:
    """Map one OnResponse ``StkOrderData``-like dict → ``broker_acks`` row.

    Expected keys (tolerant): Identify, ReplyCode, OrderNO, ErrType, ErrNO, Advisory.
    """
    try:
        reply = int(row.get("ReplyCode", row.get("reply_code", -1)))
    except (TypeError, ValueError):
        return SparkSubmitResult(ok=False, reject_reason="bad_reply_code")
    if reply != 0:
        err = str(row.get("ErrNO") or row.get("Advisory") or f"reply:{reply}")
        return SparkSubmitResult(ok=False, reject_reason=f"spark_reject:{err}")

    oid = str(
        order_id
        or (intent.order_id if intent else "")
        or row.get("order_id")
        or ""
    ).strip()
    if not oid:
        return SparkSubmitResult(ok=False, reject_reason="missing_order_id")

    c = str(code or (intent.StkCode if intent else "") or row.get("StkCode") or "").strip()
    s = side or (side_from_flag(intent.BuySell) if intent else "")
    if not s and row.get("BuySell"):
        s = side_from_flag(str(row.get("BuySell")))
    q = shares if shares is not None else (intent.shares if intent else None)
    if q is None and "OrderQty" in row:
        q = order_qty_to_shares(row["OrderQty"])
    if not c or not s or q is None:
        return SparkSubmitResult(ok=False, reject_reason="incomplete_ack_map")

    ack: dict[str, Any] = {
        "order_id": oid,
        "code": c,
        "side": s,
        "quantity": int(q),
        "signal_date": str(signal_date or ""),
        "broker_order_no": str(row.get("OrderNO") or row.get("OrderNo") or ""),
        "basket_no": str(intent.BasketNo if intent else row.get("BasketNo") or ""),
        "client_order_id": str(intent.client_order_id if intent else ""),
        "spark_identify": row.get("Identify", row.get("identify")),
        "api_wired": API_WIRED,
    }
    if fill_price is not None:
        ack["fill_price"] = float(fill_price)
    return SparkSubmitResult(ok=True, broker_ack=ack)


def send_stock_order_live(*_a: Any, **_k: Any) -> None:
    """Placeholder for future pythonnet ``SendStockOrder`` — always blocked."""
    assert_not_wired()
