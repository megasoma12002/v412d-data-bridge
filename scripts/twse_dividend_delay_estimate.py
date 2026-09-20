#!/usr/bin/env python3
"""除權息入帳延後 estimate (observe-only).

Snaps:
  - ex trading day → next ``is_session`` if board closed that day
  - payment day → next ``is_settlement`` if not a settlement business day
    (optional MOPS amendment overrides)

Emits separate cash / stock legs when both are present on a row.

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
    load_calendar_window,
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


def _snap_leg(
    raw: str,
    *,
    kind: str,
    sessions: Sequence[date],
    settlements: Sequence[date],
    mops_pay: date | None,
) -> tuple[str, str, list[str]]:
    """Return (effective_iso, delay_days_str, notes)."""
    notes: list[str] = []
    if not raw:
        return "", "", notes
    try:
        d = date.fromisoformat(raw)
    except ValueError:
        notes.append(f"bad_{kind}_date")
        return "", "", notes

    if kind.endswith("ex"):
        bounds = sorted(sessions)
        if bounds and (d < bounds[0] or d > bounds[-1]):
            notes.append(f"{kind}_outside_calendar")
            return raw, "0", notes
        eff = effective_ex_trade(d, sessions)
        if eff != d:
            notes.append(f"{kind}_snapped_to_next_session")
        return eff.isoformat(), str((eff - d).days), notes

    bounds = sorted(settlements)
    if bounds and (d < bounds[0] or d > bounds[-1]):
        notes.append(f"{kind}_outside_calendar")
        return raw, "0", notes
    eff = effective_payment(d, settlements, mops_amendment=mops_pay)
    if mops_pay is not None:
        notes.append(f"{kind}_mops_amendment")
    elif eff != d:
        notes.append(f"{kind}_snapped_to_next_settlement")
    return eff.isoformat(), str((eff - d).days), notes


def estimate_event(
    row: dict[str, Any],
    *,
    sessions: Sequence[date],
    settlements: Sequence[date],
    mops_pay: date | None = None,
    mops_amendments: dict[tuple[str, str], str] | None = None,
    ex_amendments: dict | None = None,
) -> dict[str, Any]:
    cash_ex = str(row.get("cash_ex_date") or "").strip()[:10]
    stock_ex = str(row.get("stock_ex_date") or "").strip()[:10]
    cash_pay = str(row.get("cash_payment_date") or "").strip()[:10]
    stock_pay = str(row.get("stock_payment_date") or "").strip()[:10]
    code = str(row.get("code") or "")
    # Legacy single-field aliases (tests / ad-hoc rows)
    if not cash_ex and not stock_ex:
        cash_ex = str(row.get("ex_date") or "").strip()[:10]
    if not cash_pay and not stock_pay:
        cash_pay = str(row.get("payment_date") or "").strip()[:10]

    raw_cash_ex, raw_stock_ex = cash_ex, stock_ex

    # S3: resolve amended ex (TWSE list) per leg; snap that date if still closed.
    def _ex_override(leg: str, raw: str) -> date | None:
        if not ex_amendments or not raw:
            return None
        from twse_same_day_ex_list import lookup_ex_amendment

        return lookup_ex_amendment(ex_amendments, code, raw, leg=leg)

    cash_ex_amd = _ex_override("cash", cash_ex)
    stock_ex_amd = _ex_override("stock", stock_ex)

    # Per-leg MOPS overlay (cash/stock pay); explicit mops_pay wins for cash.
    def _mops_for(pay: str, *, cash_leg: bool) -> date | None:
        if cash_leg and mops_pay is not None:
            return mops_pay
        if not mops_amendments or not pay:
            return None
        from e22_mops_payment_amendments import lookup_amendment

        return lookup_amendment(
            mops_amendments, code, pay, leg=("cash" if cash_leg else "stock")
        )

    out: dict[str, Any] = {
        "code": code,
        "raw_cash_ex_date": raw_cash_ex,
        "raw_stock_ex_date": raw_stock_ex,
        "raw_cash_payment_date": cash_pay,
        "raw_stock_payment_date": stock_pay,
        "effective_cash_ex_trade": "",
        "effective_stock_ex_trade": "",
        "effective_cash_payment": "",
        "effective_stock_payment": "",
        "delay_cash_ex_days": "",
        "delay_stock_ex_days": "",
        "delay_cash_pay_days": "",
        "delay_stock_pay_days": "",
        # Compat aliases (primary cash leg, else stock)
        "raw_ex_date": raw_cash_ex or raw_stock_ex,
        "raw_payment_date": cash_pay or stock_pay,
        "effective_ex_trade": "",
        "effective_payment": "",
        "delay_ex_days": "",
        "delay_pay_days": "",
        "notes": "",
        # Gap 6.9c observe: Soft-Frozen credits stock/CIL on ex, not payment
        "gap69c_stock_pay_observe": "",
    }
    notes: list[str] = []

    def _snap_ex_leg(
        raw: str, *, kind: str, amd: date | None
    ) -> tuple[str, str, list[str]]:
        if not raw:
            return "", "", []
        try:
            d0 = date.fromisoformat(raw)
        except ValueError:
            return "", "", [f"bad_{kind}_date"]
        leg_notes: list[str] = []
        if amd is not None:
            leg_notes.append(f"{kind}_date_amendment")
            # Snap amended day if somehow still closed
            eff = effective_ex_trade(amd, sessions)
            if eff != amd:
                leg_notes.append(f"{kind}_snapped_to_next_session")
            return eff.isoformat(), str((eff - d0).days), leg_notes
        return _snap_leg(
            raw, kind=kind, sessions=sessions, settlements=settlements, mops_pay=None
        )

    for raw, kind, eff_key, delay_key, amd in (
        (cash_ex, "cash_ex", "effective_cash_ex_trade", "delay_cash_ex_days", cash_ex_amd),
        (stock_ex, "stock_ex", "effective_stock_ex_trade", "delay_stock_ex_days", stock_ex_amd),
    ):
        eff, delay, leg_notes = _snap_ex_leg(raw, kind=kind, amd=amd)
        out[eff_key] = eff
        out[delay_key] = delay
        notes.extend(leg_notes)

    for raw, kind, eff_key, delay_key in (
        (cash_pay, "cash_pay", "effective_cash_payment", "delay_cash_pay_days"),
        (stock_pay, "stock_pay", "effective_stock_payment", "delay_stock_pay_days"),
    ):
        leg_mops = _mops_for(raw, cash_leg=(kind == "cash_pay"))
        eff, delay, leg_notes = _snap_leg(
            raw, kind=kind, sessions=sessions, settlements=settlements, mops_pay=leg_mops
        )
        out[eff_key] = eff
        out[delay_key] = delay
        notes.extend(leg_notes)

    out["effective_ex_trade"] = out["effective_cash_ex_trade"] or out["effective_stock_ex_trade"]
    out["effective_payment"] = out["effective_cash_payment"] or out["effective_stock_payment"]
    out["delay_ex_days"] = out["delay_cash_ex_days"] or out["delay_stock_ex_days"]
    out["delay_pay_days"] = out["delay_cash_pay_days"] or out["delay_stock_pay_days"]
    if out["raw_stock_payment_date"] or out["effective_stock_payment"]:
        out["gap69c_stock_pay_observe"] = (
            "Soft-Frozen books credit stock/CIL on stock_ex (effex); "
            f"stock_payment_date={out['raw_stock_payment_date'] or 'n/a'} "
            f"effective_stock_payment={out['effective_stock_payment'] or 'n/a'} "
            "(observe-only; no books flip)"
        )
    # Compat note tokens expected by early unit tests
    compat = []
    for n in notes:
        if n.endswith("_snapped_to_next_session"):
            compat.append("ex_snapped_to_next_session")
        elif n.endswith("_snapped_to_next_settlement"):
            compat.append("pay_snapped_to_next_settlement")
        elif n.endswith("_mops_amendment"):
            compat.append("mops_amendment")
        elif n.endswith("_ex_date_amendment"):
            compat.append("ex_date_amendment")
        elif n.endswith("_outside_calendar"):
            if "ex" in n:
                compat.append("ex_outside_calendar")
            else:
                compat.append("pay_outside_calendar")
        elif n.startswith("bad_"):
            if "ex" in n:
                compat.append("bad_ex_date")
            else:
                compat.append("bad_payment_date")
    # Prefer specific notes; keep compat tokens for grep stability
    merged = notes + [c for c in compat if c not in notes]
    out["notes"] = ";".join(dict.fromkeys(merged))
    return out


def _row_has_delay(r: dict[str, Any]) -> bool:
    for k in (
        "delay_cash_ex_days",
        "delay_stock_ex_days",
        "delay_cash_pay_days",
        "delay_stock_pay_days",
        "delay_ex_days",
        "delay_pay_days",
    ):
        v = r.get(k)
        if v not in ("", "0", None):
            return True
    return False


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
        default=None,
        help=(
            "Single TWSE sessions CSV. Default: load_calendar_window(center_year) "
            "with center from --calendar-year or max event year / asof."
        ),
    )
    ap.add_argument(
        "--calendar-year",
        type=int,
        default=0,
        help="Center year for load_calendar_window when --calendar unset (0=infer)",
    )
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--summary-json", type=Path, default=None)
    ap.add_argument(
        "--mops-amendments",
        type=Path,
        default=ROOT / "data" / "dividend_events" / "mops_payment_amendments.csv",
        help="D4 overlay CSV (code,original_payment_date,amended_payment_date)",
    )
    ap.add_argument(
        "--ex-amendments",
        type=Path,
        default=ROOT / "data" / "dividend_events" / "ex_date_amendments.csv",
        help="S3 overlay CSV (code,original_ex_date,amended_ex_date,leg)",
    )
    ap.add_argument("--limit", type=int, default=0, help="Max rows (0=all)")
    a = ap.parse_args()

    events = load_events(a.events)
    if a.limit > 0:
        events = events[: a.limit]

    if a.calendar is not None:
        cal = read_calendar_csv(a.calendar)
        sessions = session_dates(cal)
        settlements = settlement_dates(cal)
    else:
        years: set[int] = set()
        for e in events:
            for key in (
                "cash_ex_date",
                "cash_payment_date",
                "stock_ex_date",
                "stock_payment_date",
            ):
                raw = str(e.get(key) or "")[:10]
                if len(raw) == 10:
                    try:
                        years.add(int(raw[:4]))
                    except ValueError:
                        pass
        if a.calendar_year:
            years.add(int(a.calendar_year))
        if not years:
            years.add(date.today().year)
        sessions_acc: list[date] = []
        settlements_acc: list[date] = []
        loaded = False
        # Prefer explicit center; else union every event year that has a CSV
        # (plus Y±1 neighbors via load_calendar_window).
        centers = (
            [int(a.calendar_year)]
            if a.calendar_year
            else sorted(years, reverse=True)
        )
        seen_centers: set[int] = set()
        for center in centers:
            if center in seen_centers:
                continue
            seen_centers.add(center)
            try:
                s, t = load_calendar_window(
                    center, calendar_dir=DEFAULT_CALENDAR_DIR, span=1
                )
            except FileNotFoundError:
                continue
            sessions_acc.extend(s)
            settlements_acc.extend(t)
            loaded = True
            if a.calendar_year:
                break
        if not loaded:
            # Tip / asof year last resort
            sessions_acc, settlements_acc = load_calendar_window(
                date.today().year, calendar_dir=DEFAULT_CALENDAR_DIR, span=1
            )
        sessions = sorted(set(sessions_acc))
        settlements = sorted(set(settlements_acc))

    from e22_mops_payment_amendments import load_amendments
    from twse_same_day_ex_list import load_ex_amendments

    amendments = load_amendments(a.mops_amendments) if a.mops_amendments else {}
    ex_amd = load_ex_amendments(a.ex_amendments) if a.ex_amendments else {}
    rows = [
        estimate_event(
            r,
            sessions=sessions,
            settlements=settlements,
            mops_amendments=amendments,
            ex_amendments=ex_amd,
        )
        for r in events
    ]
    delayed = [r for r in rows if _row_has_delay(r)]
    stock_pay_rows = [r for r in rows if r.get("raw_stock_payment_date")]
    summary: dict[str, Any] = {
        "n_events": len(rows),
        "n_with_any_delay": len(delayed),
        "n_with_ex_amendment": sum(1 for r in rows if "ex_date_amendment" in r.get("notes", "")),
        "n_stock_payment_legs": len(stock_pay_rows),
        "gap69c_note": (
            "Soft-Frozen credits stock/CIL on effective_ex_trade; "
            "stock_payment_date is observe-only (Gap 6.9c)"
        ),
        "calendar": str(a.calendar),
        "note": "observe-only; Soft-Frozen books untouched",
        "delayed_sample": [
            {
                "code": r["code"],
                "raw_ex_date": r["raw_ex_date"],
                "effective_ex_trade": r["effective_ex_trade"],
                "raw_payment_date": r["raw_payment_date"],
                "effective_payment": r["effective_payment"],
                "effective_stock_payment": r.get("effective_stock_payment"),
                "notes": r["notes"],
            }
            for r in delayed[:20]
        ],
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
    summary["out"] = str(out_path)
    summary_path = a.summary_json
    if summary_path is None:
        summary_path = out_path.with_suffix(".summary.json")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary["summary_json"] = str(summary_path)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
