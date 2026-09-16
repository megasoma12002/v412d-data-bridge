#!/usr/bin/env python3
"""除權息入帳延後 estimate (observe-only).

Snaps:
  - ex trading day → next ``is_session`` if board closed that day
  - payment day → next ``is_settlement`` if not a settlement business day
    (optional MOPS amendment overrides)

Does **not** mutate Soft-Frozen books / ``e22_dividend_accounting`` apply path.
See ``research/ops/TWSE_DIVIDEND_CREDIT_DELAY_CHARTER.md``.
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Sequence

from twse_session_sources import (
    DEFAULT_CALENDAR_DIR,
    nth_session_after,
    nth_settlement_after,
    read_calendar_csv,
    session_dates,
    settlement_dates,
)

ROOT = Path(__file__).resolve().parents[1]


def effective_ex_trade(ex_day: date, sessions: Sequence[date]) -> date:
    """Board ex trading day: if closed, first open session on/after."""
    sess = sorted(sessions)
    if not sess:
        raise ValueError("empty session list")
    if ex_day < sess[0] or ex_day > sess[-1]:
        return ex_day  # outside pinned calendar — leave raw
    if ex_day in sess:
        return ex_day
    return nth_session_after(sess, ex_day - timedelta(days=1), 1)


def effective_payment(
    pay_day: date,
    settlements: Sequence[date],
    *,
    mops_amendment: date | None = None,
) -> date:
    """Cash payment business day; MOPS amendment wins when provided."""
    if mops_amendment is not None:
        return mops_amendment
    settles = sorted(settlements)
    if not settles:
        raise ValueError("empty settlement list")
    if pay_day < settles[0] or pay_day > settles[-1]:
        return pay_day
    if pay_day in settles:
        return pay_day
    return nth_settlement_after(settles, pay_day - timedelta(days=1), 1)


def estimate_event(
    row: dict[str, Any],
    *,
    sessions: Sequence[date],
    settlements: Sequence[date],
    mops_pay: date | None = None,
) -> dict[str, Any]:
    raw_ex = str(row.get("cash_ex_date") or row.get("stock_ex_date") or row.get("ex_date") or "").strip()[:10]
    raw_pay = str(
        row.get("cash_payment_date") or row.get("stock_payment_date") or row.get("payment_date") or ""
    ).strip()[:10]
    out: dict[str, Any] = {
        "code": str(row.get("code") or ""),
        "raw_ex_date": raw_ex,
        "raw_payment_date": raw_pay,
        "effective_ex_trade": "",
        "effective_payment": "",
        "delay_ex_days": "",
        "delay_pay_days": "",
        "notes": "",
    }
    notes: list[str] = []
    if raw_ex:
        try:
            ex_d = date.fromisoformat(raw_ex)
            sess_sorted = sorted(sessions)
            if sess_sorted and (ex_d < sess_sorted[0] or ex_d > sess_sorted[-1]):
                out["effective_ex_trade"] = raw_ex
                out["delay_ex_days"] = "0"
                notes.append("ex_outside_calendar")
            else:
                eff_ex = effective_ex_trade(ex_d, sessions)
                out["effective_ex_trade"] = eff_ex.isoformat()
                out["delay_ex_days"] = str((eff_ex - ex_d).days)
                if eff_ex != ex_d:
                    notes.append("ex_snapped_to_next_session")
        except ValueError:
            notes.append("bad_ex_date")
    if raw_pay:
        try:
            pay_d = date.fromisoformat(raw_pay)
            settle_sorted = sorted(settlements)
            if settle_sorted and (pay_d < settle_sorted[0] or pay_d > settle_sorted[-1]):
                out["effective_payment"] = raw_pay
                out["delay_pay_days"] = "0"
                notes.append("pay_outside_calendar")
            else:
                eff_pay = effective_payment(pay_d, settlements, mops_amendment=mops_pay)
                out["effective_payment"] = eff_pay.isoformat()
                out["delay_pay_days"] = str((eff_pay - pay_d).days)
                if mops_pay is not None:
                    notes.append("mops_amendment")
                elif eff_pay != pay_d:
                    notes.append("pay_snapped_to_next_settlement")
        except ValueError:
            notes.append("bad_payment_date")
    out["notes"] = ";".join(notes)
    return out


def load_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
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
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--limit", type=int, default=0, help="Max rows (0=all)")
    a = ap.parse_args()

    cal = read_calendar_csv(a.calendar)
    sessions = session_dates(cal)
    settlements = settlement_dates(cal)
    events = load_events(a.events)
    if a.limit > 0:
        events = events[: a.limit]

    rows = [
        estimate_event(r, sessions=sessions, settlements=settlements) for r in events
    ]
    delayed = [r for r in rows if r.get("delay_ex_days") not in ("", "0") or r.get("delay_pay_days") not in ("", "0")]
    summary = {
        "n_events": len(rows),
        "n_with_any_delay": len(delayed),
        "calendar": str(a.calendar),
        "note": "observe-only; Soft-Frozen books untouched",
    }
    out_path = a.out
    if out_path is None:
        out_path = ROOT / "repro" / "div-delay" / "dividend_delay_estimate.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if rows:
        fields = list(rows[0].keys())
        with out_path.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)
    print(json.dumps({**summary, "out": str(out_path)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
