#!/usr/bin/env python3
"""TWSE T+2 settlement cash estimate (observe-only).

``settle_date = nth_settlement_after(settlement_days, fill_date, 2)``.

Settlement business days include normal trading sessions **and** 封關後
「市場無交易，僅辦理結算交割」days — but **not** weekends, 春节放假, or
typhoon full closes (應屆交割顺延).

Does **not** mutate ``portfolio_state`` / ``nav.csv`` / ``fills.csv`` / Soft-Frozen.
Exact T+1 paper cash ≠ custody T+2 settled cash.
"""
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Sequence
from zoneinfo import ZoneInfo

from twse_session_sources import (
    DEFAULT_CALENDAR_DIR,
    DayRecord,
    nth_settlement_after,
    read_calendar_csv,
    settlement_dates,
)

TAIPEI = ZoneInfo("Asia/Taipei")
ROOT = Path(__file__).resolve().parents[1]


@dataclass
class FillSettlement:
    fill_id: str
    fill_date: date
    code: str
    side: str
    quantity: float
    gross: float
    fees_tax: float
    settlement_cash: float
    settle_date: date
    sessions_to_settle: int

    def to_row(self) -> dict[str, Any]:
        return {
            "fill_id": self.fill_id,
            "fill_date": self.fill_date.isoformat(),
            "code": self.code,
            "side": self.side,
            "quantity": self.quantity,
            "gross": self.gross,
            "fees_tax": self.fees_tax,
            "settlement_cash": self.settlement_cash,
            "settle_date": self.settle_date.isoformat(),
            "sessions_to_settle": self.sessions_to_settle,
        }


def settlement_cash_for(side: str, gross: float, fees_tax: float) -> float:
    s = str(side).upper()
    if s == "BUY":
        return -(float(gross) + float(fees_tax))
    if s == "SELL":
        return float(gross) - float(fees_tax)
    raise ValueError(f"unknown side: {side!r}")


def sessions_remaining(sessions: Sequence[date], asof: date, settle: date) -> int:
    """How many open sessions from asof to settle inclusive of settle if asof < settle."""
    if settle <= asof:
        return 0
    return sum(1 for d in sessions if asof < d <= settle)


def estimate_fill(row: dict[str, Any], sessions: Sequence[date], *, asof: date) -> FillSettlement:
    fill_d = date.fromisoformat(str(row["fill_date"]))
    side = str(row["side"])
    gross = float(row["gross"])
    fees = float(row["fees_tax"])
    settle = nth_settlement_after(sessions, fill_d, 2)
    return FillSettlement(
        fill_id=str(row.get("fill_id") or ""),
        fill_date=fill_d,
        code=str(row.get("code") or ""),
        side=side,
        quantity=float(row.get("quantity") or 0),
        gross=gross,
        fees_tax=fees,
        settlement_cash=settlement_cash_for(side, gross, fees),
        settle_date=settle,
        sessions_to_settle=sessions_remaining(sessions, asof, settle),
    )


def load_fills_csv(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_paper_cash(state_dir: Path) -> float | None:
    p = state_dir / "portfolio_state.json"
    if not p.exists():
        return None
    obj = json.loads(p.read_text(encoding="utf-8"))
    cash = obj.get("cash")
    return float(cash) if cash is not None else None


def load_sessions(
    *,
    calendar_path: Path | None = None,
    year: int | None = None,
    calendar: Sequence[DayRecord] | None = None,
) -> list[date]:
    """Load **settlement** business days for T+2 (not trading-only sessions)."""
    if calendar is not None:
        return settlement_dates(calendar)
    path = calendar_path
    if path is None:
        y = year or datetime.now(tz=TAIPEI).year
        path = DEFAULT_CALENDAR_DIR / f"twse_sessions_{y}.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"session calendar missing: {path} (build via twse_session_sources.py --build-year)"
        )
    return settlement_dates(read_calendar_csv(path))


def summarize(
    estimates: Sequence[FillSettlement],
    *,
    asof: date,
    paper_cash: float | None,
) -> dict[str, Any]:
    settling_today = [e for e in estimates if e.settle_date == asof]
    unsettled = [e for e in estimates if e.settle_date > asof]
    payables = sum(e.settlement_cash for e in unsettled if e.settlement_cash < 0)
    receivables = sum(e.settlement_cash for e in unsettled if e.settlement_cash > 0)
    unsettled_net = payables + receivables
    settling_today_net = sum(e.settlement_cash for e in settling_today)
    settled_est = None if paper_cash is None else float(paper_cash) - unsettled_net
    return {
        "asof": asof.isoformat(),
        "n_fills": len(estimates),
        "settling_today_net": settling_today_net,
        "n_settling_today": len(settling_today),
        "unsettled_payables": payables,
        "unsettled_receivables": receivables,
        "unsettled_net": unsettled_net,
        "n_unsettled": len(unsettled),
        "paper_cash": paper_cash,
        "settled_cash_estimate": settled_est,
        "note": (
            "settled_cash_estimate ≈ paper_cash - unsettled_net; "
            "liquidity view only — not NAV. Typhoon/holiday skipped via session calendar."
        ),
    }


def run_estimate(
    state_dir: Path,
    *,
    asof: date,
    calendar_path: Path | None = None,
) -> tuple[list[FillSettlement], dict[str, Any]]:
    fills = load_fills_csv(state_dir / "fills.csv")
    years = {date.fromisoformat(str(r["fill_date"])).year for r in fills}
    years.add(asof.year)
    sessions: list[date] = []
    if calendar_path is not None:
        sessions = load_sessions(calendar_path=calendar_path)
    else:
        for y in sorted(years):
            path = DEFAULT_CALENDAR_DIR / f"twse_sessions_{y}.csv"
            if path.exists():
                sessions.extend(load_sessions(calendar_path=path, year=y))
            elif y == max(years):
                # Fall back to asof-year path error from load_sessions
                sessions.extend(load_sessions(year=y))
    sessions = sorted(set(sessions))
    estimates = [estimate_fill(r, sessions, asof=asof) for r in fills]
    summary = summarize(estimates, asof=asof, paper_cash=load_paper_cash(state_dir))
    return estimates, summary


def write_outputs(
    estimates: Sequence[FillSettlement],
    summary: dict[str, Any],
    out_dir: Path,
) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "settlement_cash_estimate.csv"
    json_path = out_dir / "settlement_cash_estimate.json"
    fields = list(FillSettlement(
        fill_id="", fill_date=date(2020, 1, 1), code="", side="BUY",
        quantity=0, gross=0, fees_tax=0, settlement_cash=0,
        settle_date=date(2020, 1, 1), sessions_to_settle=0,
    ).to_row().keys())
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for e in estimates:
            w.writerow(e.to_row())
    payload = {"summary": summary, "fills": [e.to_row() for e in estimates]}
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return csv_path, json_path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--state-dir", type=Path, default=ROOT / "forward" / "e21")
    ap.add_argument("--asof", default=None, help="YYYY-MM-DD (default: Taipei today)")
    ap.add_argument(
        "--calendar",
        type=Path,
        default=None,
        help="Override twse_sessions_YYYY.csv (single-year)",
    )
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Write CSV/JSON here (default: state-dir; observe-only)",
    )
    ap.add_argument("--stdout-json", action="store_true")
    a = ap.parse_args()
    asof = date.fromisoformat(a.asof) if a.asof else datetime.now(tz=TAIPEI).date()
    estimates, summary = run_estimate(a.state_dir, asof=asof, calendar_path=a.calendar)
    out_dir = a.out_dir or a.state_dir
    csv_path, json_path = write_outputs(estimates, summary, out_dir)
    report = {
        "summary": summary,
        "out_csv": str(csv_path),
        "out_json": str(json_path),
    }
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
