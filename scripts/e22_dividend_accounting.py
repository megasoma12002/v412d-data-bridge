#!/usr/bin/env python3
"""E22 dividend accounting — formal books vs cash-only baseline.

Formal rule (E22_v2s):
  - Signals (E16): may use adj_close
  - Books / NAV / fills: raw open/close only
  - Cash dividend: credit cash on cash_ex_date
  - Stock dividend: shares *= (1 + stock_dividend/10) on stock_ex_date
    (FinMind 元/股, par 10). Never combine adj_close NAV with share increase.

E22_v2 (preserved): cash credit only — SOFT_FROZEN cash-only baseline label.

Do not silently rewrite E22_v2 semantics; call sites must pick a version id.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

E22_V2 = "E22_v2"  # cash-only baseline (preserved)
E22_V2S = "E22_v2s"  # formal books: cash + stock share increase
DEFAULT_BOOKS_VERSION = E22_V2S

DIV_PATH_DEFAULT = Path("data/dividend_events/e22_dividend_events.csv")


def stock_share_factor(yuan_per_share: float) -> float:
    """FinMind stock_dividend is 元/股 at par 10."""
    return 1.0 + float(yuan_per_share) / 10.0


@dataclass(frozen=True)
class DivEvent:
    code: str
    kind: str  # "cash" | "stock"
    ex_date: str  # YYYY-MM-DD
    amount: float  # cash 元/股 or stock 元/股
    payment_date: str = ""


@dataclass
class DivApplyResult:
    cash_credit: float = 0.0
    stock_shares_added: float = 0.0
    cash_events: int = 0
    stock_events: int = 0
    details: list | None = None

    def __post_init__(self) -> None:
        if self.details is None:
            self.details = []


def load_dividend_events(path: Path | str = DIV_PATH_DEFAULT) -> list[DivEvent]:
    path = Path(path)
    if not path.exists():
        return []
    out: list[DivEvent] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            code = str(row.get("code") or "").strip()
            try:
                cash = float(row.get("cash_dividend") or 0)
            except ValueError:
                cash = 0.0
            try:
                stock = float(row.get("stock_dividend") or 0)
            except ValueError:
                stock = 0.0
            cash_ex = str(row.get("cash_ex_date") or "").strip()[:10]
            stock_ex = str(row.get("stock_ex_date") or "").strip()[:10]
            if code and cash_ex and cash > 0:
                out.append(
                    DivEvent(
                        code=code,
                        kind="cash",
                        ex_date=cash_ex,
                        amount=cash,
                        payment_date=str(row.get("cash_payment_date") or "").strip()[:10],
                    )
                )
            if code and stock_ex and stock > 0:
                out.append(
                    DivEvent(
                        code=code,
                        kind="stock",
                        ex_date=stock_ex,
                        amount=stock,
                        payment_date=str(row.get("stock_payment_date") or "").strip()[:10],
                    )
                )
    return out


def events_on_date(events: Iterable[DivEvent], day: str) -> list[DivEvent]:
    day = str(day)[:10]
    return [e for e in events if e.ex_date == day]


def apply_dividends_for_date(
    day: str,
    positions: dict[str, float],
    cash: float,
    events: Iterable[DivEvent],
    *,
    version: str = DEFAULT_BOOKS_VERSION,
    skip_keys: set[str] | None = None,
) -> tuple[dict[str, float], float, DivApplyResult]:
    """Apply E22 dividends for one calendar/trading date onto books.

    Idempotent when ``skip_keys`` contains ``f\"{kind}:{code}:{ex_date}\"``.
    """
    version = version or DEFAULT_BOOKS_VERSION
    if version not in {E22_V2, E22_V2S}:
        raise ValueError(f"unknown E22 books version: {version}")
    skip = skip_keys or set()
    pos = {k: float(v) for k, v in positions.items()}
    cash_out = float(cash)
    result = DivApplyResult()
    day = str(day)[:10]

    for ev in events_on_date(events, day):
        key = f"{ev.kind}:{ev.code}:{ev.ex_date}"
        if key in skip:
            continue
        sh = float(pos.get(ev.code, 0.0) or 0.0)
        if sh <= 0:
            continue
        if ev.kind == "cash":
            credit = sh * ev.amount
            cash_out += credit
            result.cash_credit += credit
            result.cash_events += 1
            result.details.append(
                {
                    "key": key,
                    "kind": "cash",
                    "code": ev.code,
                    "ex_date": ev.ex_date,
                    "payment_date": ev.payment_date,
                    "amount_per_share": ev.amount,
                    "shares": sh,
                    "cash_credit": credit,
                    "version": version,
                }
            )
        elif ev.kind == "stock":
            if version == E22_V2:
                # cash-only baseline: ignore stock share increase
                continue
            add = sh * (stock_share_factor(ev.amount) - 1.0)
            pos[ev.code] = sh + add
            result.stock_shares_added += add
            result.stock_events += 1
            result.details.append(
                {
                    "key": key,
                    "kind": "stock",
                    "code": ev.code,
                    "ex_date": ev.ex_date,
                    "payment_date": ev.payment_date,
                    "amount_per_share": ev.amount,
                    "share_factor": stock_share_factor(ev.amount),
                    "shares_before": sh,
                    "shares_added": add,
                    "version": version,
                }
            )
    return pos, cash_out, result


def version_manifest(version: str = DEFAULT_BOOKS_VERSION) -> dict:
    return {
        "e22_books_version": version,
        "preserved_baseline": E22_V2,
        "formal_books": E22_V2S,
        "signal_price": "adj_close",
        "books_price": "raw_open_close",
        "cash_timing": "cash_ex_date",
        "stock_timing": "stock_ex_date" if version == E22_V2S else "not_applied",
        "stock_factor": "1 + stock_dividend/10" if version == E22_V2S else None,
        "forbids_adj_close_nav_with_stock_shares": True,
    }
