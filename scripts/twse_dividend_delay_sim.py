#!/usr/bin/env python3
"""Simulate 除權息入帳延後 cash timing (sandbox only).

Compares three clocks on a held position day-walk:
  - Soft-Frozen formal: cash on raw ``cash_ex_date``
  - ``E22_v3_recv_pay``: receivable on raw ex; cash on raw payment
  - ``E22_v3_recv_pay_effdelay``: receivable on effective ex; cash on effective pay

Does **not** mutate Soft-Frozen / DEFAULT books.
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import e22_dividend_accounting as formal
import e22_v3_sandbox_books as sandbox
from twse_dividend_delay_estimate import effective_ex_trade, effective_payment
from twse_session_sources import (
    DEFAULT_CALENDAR_DIR,
    read_calendar_csv,
    session_dates,
    settlement_dates,
)

ROOT = Path(__file__).resolve().parents[1]


def _daterange(start: date, end: date) -> list[str]:
    out: list[str] = []
    d = start
    while d <= end:
        out.append(d.isoformat())
        d += timedelta(days=1)
    return out


def _detail_keys(res: Any) -> set[str]:
    keys: set[str] = set()
    for d in getattr(res, "details", None) or []:
        if isinstance(d, dict) and d.get("key"):
            keys.add(str(d["key"]))
    return keys


def simulate_event(
    ev: formal.DivEvent,
    *,
    shares: float,
    sessions: list[date],
    settlements: list[date],
) -> dict[str, Any]:
    raw_ex = date.fromisoformat(ev.ex_date)
    raw_pay = date.fromisoformat(ev.payment_date) if ev.payment_date else raw_ex
    eff_ex = effective_ex_trade(raw_ex, sessions)
    eff_pay = (
        effective_payment(raw_pay, settlements) if ev.payment_date else eff_ex
    )
    start = min(raw_ex, eff_ex) - timedelta(days=1)
    end = max(raw_pay, eff_pay) + timedelta(days=1)
    days = _daterange(start, end)

    clocks = {
        "formal_raw_ex": formal.E22_V2S_TW,
        "formal_effex": formal.E22_V2S_TW_EFFEX,
        "recv_pay": sandbox.E22_V3_RECV_PAY,
        "recv_pay_effdelay": sandbox.E22_V3_RECV_PAY_EFFDELAY,
    }
    timelines: dict[str, list[dict[str, Any]]] = {k: [] for k in clocks}
    cash_first: dict[str, str | None] = {k: None for k in clocks}
    recv_first: dict[str, str | None] = {k: None for k in clocks}

    for label, version in clocks.items():
        pos = {ev.code: float(shares)}
        cash = 0.0
        recv: dict[str, float] = {}
        skip: set[str] = set()
        for day in days:
            if version in formal.KNOWN_VERSIONS:
                pos, cash, res = formal.apply_dividends_for_date(
                    day,
                    pos,
                    cash,
                    [ev],
                    version=version,
                    skip_keys=skip,
                    session_dates=sessions,
                )
                skip |= _detail_keys(res)
                recv_sum = 0.0
                recv_credit = 0.0
                settled = float(res.cash_credit)
                if settled > 0 and cash_first[label] is None:
                    cash_first[label] = day
            else:
                pos, cash, recv, res = sandbox.apply_sandbox_for_date(
                    day,
                    pos,
                    cash,
                    recv,
                    [ev],
                    version=version,
                    skip_keys=skip,
                    session_dates=sessions,
                    settlement_dates=settlements,
                )
                skip |= _detail_keys(res)
                recv_sum = float(sum(recv.values()))
                recv_credit = float(res.receivable_credit)
                settled = float(res.receivable_settled)
                if recv_credit > 0 and recv_first[label] is None:
                    recv_first[label] = day
                if settled > 0 and cash_first[label] is None:
                    cash_first[label] = day
            timelines[label].append(
                {
                    "date": day,
                    "cash": round(cash, 6),
                    "receivable": round(recv_sum, 6),
                    "cash_credit": round(float(res.cash_credit), 6),
                    "receivable_credit": round(
                        float(getattr(res, "receivable_credit", 0.0) or 0.0), 6
                    ),
                    "receivable_settled": round(
                        float(getattr(res, "receivable_settled", 0.0) or 0.0), 6
                    ),
                }
            )

    return {
        "code": ev.code,
        "amount": ev.amount,
        "shares": shares,
        "gross": round(float(shares) * float(ev.amount), 6),
        "raw_ex_date": ev.ex_date,
        "raw_payment_date": ev.payment_date,
        "effective_ex_trade": eff_ex.isoformat(),
        "effective_payment": eff_pay.isoformat(),
        "delay_ex_days": (eff_ex - raw_ex).days,
        "delay_pay_days": (eff_pay - raw_pay).days,
        "first_receivable_date": recv_first,
        "first_cash_date": cash_first,
        "soft_frozen_default": formal.DEFAULT_BOOKS_VERSION,
        "d5_accept": True,
        "timelines": timelines,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--code", default="2891")
    ap.add_argument("--ex-date", default="2026-07-10", help="Match cash_ex_date")
    ap.add_argument("--shares", type=float, default=1000.0)
    ap.add_argument(
        "--events",
        type=Path,
        default=ROOT / "data" / "dividend_events" / "e22_dividend_events.csv",
    )
    ap.add_argument(
        "--calendar",
        type=Path,
        default=DEFAULT_CALENDAR_DIR / "twse_sessions_2026.csv",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "repro" / "div-delay" / "delay_sim_2891.json",
    )
    ap.add_argument(
        "--synthetic-pay-on-ex",
        action="store_true",
        help="Force payment_date=ex_date to demo bank-day snap (typhoon pay delay)",
    )
    a = ap.parse_args()

    cal = read_calendar_csv(a.calendar)
    sessions = session_dates(cal)
    settlements = settlement_dates(cal)

    events = [
        e
        for e in formal.load_dividend_events(a.events)
        if e.code == a.code and e.kind == "cash" and e.ex_date == a.ex_date
    ]
    if not events:
        # Synthetic fallback for demos when ledger lacks the row
        events = [
            formal.DivEvent(
                code=a.code,
                kind="cash",
                ex_date=a.ex_date,
                amount=2.50024,
                payment_date=a.ex_date if a.synthetic_pay_on_ex else "2026-08-07",
            )
        ]
    ev = events[0]
    if a.synthetic_pay_on_ex:
        ev = formal.DivEvent(
            code=ev.code,
            kind=ev.kind,
            ex_date=ev.ex_date,
            amount=ev.amount,
            payment_date=ev.ex_date,
        )

    result = simulate_event(
        ev, shares=a.shares, sessions=sessions, settlements=settlements
    )
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Compact CSV of cash dates
    csv_path = a.out.with_suffix(".cash_dates.csv")
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "clock",
                "first_receivable_date",
                "first_cash_date",
                "raw_ex_date",
                "effective_ex_trade",
                "raw_payment_date",
                "effective_payment",
            ],
        )
        w.writeheader()
        for clock in ("formal_raw_ex", "formal_effex", "recv_pay", "recv_pay_effdelay"):
            w.writerow(
                {
                    "clock": clock,
                    "first_receivable_date": result["first_receivable_date"].get(clock) or "",
                    "first_cash_date": result["first_cash_date"].get(clock) or "",
                    "raw_ex_date": result["raw_ex_date"],
                    "effective_ex_trade": result["effective_ex_trade"],
                    "raw_payment_date": result["raw_payment_date"],
                    "effective_payment": result["effective_payment"],
                }
            )

    summary = {
        "out": str(a.out),
        "cash_dates_csv": str(csv_path),
        "code": result["code"],
        "raw_ex_date": result["raw_ex_date"],
        "effective_ex_trade": result["effective_ex_trade"],
        "raw_payment_date": result["raw_payment_date"],
        "effective_payment": result["effective_payment"],
        "first_cash_date": result["first_cash_date"],
        "first_receivable_date": result["first_receivable_date"],
        "soft_frozen_untouched": True,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
