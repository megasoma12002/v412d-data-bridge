#!/usr/bin/env python3
"""E22 books day apply helpers for the live forward pipeline."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import e22_dividend_accounting as e22div
from e22_books_apply import apply_books_for_date, is_sandbox_version


def load_div_events_for_live(
    dividends_path: Path | str,
    *,
    no_repair: bool,
    apply_repair: bool,
) -> list:
    """Fail-closed dividend load; CSV rewrite only with apply_repair."""
    path = Path(dividends_path)
    if no_repair:
        return e22div.load_dividend_events(
            path, require_exists=True, fail_closed_amounts=True
        )
    if apply_repair:
        from e22_dividend_amount_repair import load_dividend_events_with_repair

        return load_dividend_events_with_repair(
            path, require_exists=True, network=True
        )
    from e22_dividend_amount_repair import scan_bad_amount_cells

    if path.exists() and scan_bad_amount_cells(path):
        raise SystemExit(
            f"Dirty dividend amount cells in {path}; "
            "re-run with --apply-div-amount-repair to patch CSV, "
            "or --no-div-amount-repair after manual fix."
        )
    return e22div.load_dividend_events(
        path, require_exists=True, fail_closed_amounts=True
    )


def apply_e22_day(
    *,
    asof_iso: str,
    pos: dict[str, float],
    cash: float,
    div_events: list,
    e22_version: str,
    skip: set[str],
    prices: dict[str, float],
    receivables: dict[str, float],
) -> tuple[dict[str, float], float, dict[str, float], Any, list[dict]]:
    """Apply books; return pos, cash, receivables, applied, pending_div_rows."""
    sessions = None
    settlements = None
    mops_amd = None
    if is_sandbox_version(e22_version) or e22_version in e22div.EFFEX_VERSIONS:
        from twse_session_sources import (
            DEFAULT_CALENDAR_DIR,
            read_calendar_csv,
            session_dates,
            settlement_dates,
        )

        y = int(str(asof_iso)[:4])
        cal_path = DEFAULT_CALENDAR_DIR / f"twse_sessions_{y}.csv"
        if cal_path.exists():
            cal_rows = read_calendar_csv(cal_path)
            sessions = session_dates(cal_rows)
            settlements = settlement_dates(cal_rows)
        elif e22_version == e22div.DEFAULT_BOOKS_VERSION or e22_version == e22div.E22_V3_RECV_PAY_EFFDELAY:
            raise SystemExit(
                f"TWSE session calendar required for live DEFAULT books {e22_version!r} "
                f"but missing: {cal_path}. Add calendar or override --e22-version with "
                "--confirm-e22-version-override for research."
            )
        if is_sandbox_version(e22_version):
            from e22_mops_payment_amendments import load_amendments

            mops_amd = load_amendments()

    pos, cash, receivables, applied = apply_books_for_date(
        asof_iso,
        pos,
        cash,
        div_events,
        version=e22_version,
        skip_keys=skip,
        mark_prices=prices,
        receivables=receivables,
        session_dates=sessions,
        settlement_dates=settlements,
        mops_amendments=mops_amd,
    )
    pending_div_rows: list[dict] = []
    for d in applied.details:
        pending_div_rows.append(
            {
                "key": d["key"],
                "date": asof_iso,
                "kind": d["kind"],
                "code": d["code"],
                "ex_date": d.get("ex_date"),
                "payment_date": d.get("payment_date", ""),
                "amount_per_share": d.get("amount_per_share", d.get("gross_credit", "")),
                "cash_credit": d.get("cash_credit", 0.0),
                "receivable_credit": d.get("receivable_credit", 0.0),
                "shares_added": d.get("shares_added", 0.0),
                "fractional_shares": d.get("fractional_shares", 0.0),
                "cil_cash_credit": d.get("cil_cash_credit", 0.0),
                "mark_price": d.get("mark_price", ""),
                "effective_ex_trade": d.get("effective_ex_trade", ""),
                "effective_payment": d.get("effective_payment", ""),
                "version": d.get("version", e22_version),
            }
        )
        skip.add(d["key"])
    return pos, cash, receivables, applied, pending_div_rows
