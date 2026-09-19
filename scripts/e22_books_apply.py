#!/usr/bin/env python3
"""Unified E22 books apply router (formal + Stage-B receivable family).

Live DEFAULT after Stage-B tax ACCEPT (2026-09-19): ``E22_v3_recv_pay_tax10``.
TAX0 sibling ``E22_v3_recv_pay_effdelay`` (Stage-E timing) remains routable.
Formal ``E22_v2s_tw_effex`` remains available as preserved cash-on-ex books.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any, Iterable, Sequence

import e22_dividend_accounting as formal
import e22_v3_sandbox_books as sandbox


def is_sandbox_version(version: str) -> bool:
    return str(version) in sandbox.SANDBOX_VERSIONS


def apply_books_for_date(
    day: str,
    positions: dict[str, float],
    cash: float,
    events: Iterable[formal.DivEvent],
    *,
    version: str | None = None,
    skip_keys: set[str] | None = None,
    mark_prices: dict[str, float] | None = None,
    par_table: dict[str, float] | None = None,
    receivables: dict[str, float] | None = None,
    session_dates: Sequence[date] | None = None,
    settlement_dates: Sequence[date] | None = None,
    mops_amendments: dict | None = None,
    calendar_dir: Path | str = formal.CALENDAR_DIR_DEFAULT,
) -> tuple[dict[str, float], float, dict[str, float], Any]:
    """Return ``pos, cash, receivables, apply_result``.

    Sandbox versions mutate/return receivables; formal versions leave
    ``receivables`` unchanged (default empty).
    """
    ver = version or formal.DEFAULT_BOOKS_VERSION
    recv_in = {k: float(v) for k, v in (receivables or {}).items()}

    if is_sandbox_version(ver):
        pos, cash_out, recv_out, res = sandbox.apply_sandbox_for_date(
            day,
            positions,
            cash,
            recv_in,
            events,
            version=ver,
            skip_keys=skip_keys,
            par_table=par_table,
            session_dates=session_dates,
            settlement_dates=settlement_dates,
            mops_amendments=mops_amendments,
        )
        return pos, cash_out, recv_out, res

    pos, cash_out, res = formal.apply_dividends_for_date(
        day,
        positions,
        cash,
        events,
        version=ver,
        skip_keys=skip_keys,
        mark_prices=mark_prices,
        par_table=par_table,
        session_dates=session_dates,
        calendar_dir=calendar_dir,
    )
    return pos, cash_out, recv_in, res


def books_manifest(version: str | None = None) -> dict:
    ver = version or formal.DEFAULT_BOOKS_VERSION
    if is_sandbox_version(ver):
        return sandbox.version_manifest(ver)
    return formal.version_manifest(ver)
