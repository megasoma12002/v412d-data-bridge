#!/usr/bin/env python3
"""Live day-commit — deferred fills/divs + atomic portfolio_state + audit."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from e22_books_apply import books_manifest
from live_ledger import append_immutable, append_immutable_many, atomic_write_json
from live_tip_meta import build_cutover_stamps


def commit_day_books(
    *,
    state_dir: Path,
    fill_port_name: str,
    fills: list[dict[str, Any]],
    pending_div_rows: list[dict[str, Any]],
    div_path: Path,
    state_path: Path,
    state_payload: dict[str, Any],
    signal: dict[str, Any],
    navrow: dict[str, Any],
    order_rows: list[dict[str, Any]],
    applied_details: list,
    asof_iso: str,
    write_excel_dashboard: bool = True,
) -> None:
    """Persist day ledgers then atomic portfolio_state (ACCEPT day-commit atomicity).

    Order (crash window shrink):
      1) orders / signals / nav (immutable CSV, batched where possible)
      2) deferred paper fills + dividends_applied
      3) portfolio_state.json last (atomic_write_json)
      4) audit_chain + optional dashboard

    Soft-Frozen KEEP — never rewrite existing rows (append_immutable first-key wins).
    """
    sdir = Path(state_dir)
    append_immutable_many(sdir / "orders.csv", list(order_rows), "order_id")
    append_immutable(sdir / "signals.csv", signal, "date")
    append_immutable(sdir / "nav.csv", navrow, "date")
    if fill_port_name == "paper":
        append_immutable_many(sdir / "fills.csv", list(fills), "fill_id")
    append_immutable_many(div_path, list(pending_div_rows), "key")
    # State last — assert_no_uncommitted_ledger detects orphans if we die above.
    atomic_write_json(state_path, state_payload)

    audit_chain = sdir / "audit_chain.jsonl"
    prev = "GENESIS"
    if audit_chain.exists():
        lines = audit_chain.read_text(encoding="utf-8").splitlines()
        prev = json.loads(lines[-1])["hash"] if lines else prev
        if any(json.loads(x)["date"] == asof_iso for x in lines):
            prev = None
    if prev:
        payload = json.dumps(
            {
                "date": asof_iso,
                "signal": signal,
                "nav": navrow,
                "orders": order_rows,
                "fills": fills,
                "dividends": applied_details,
                "previous_hash": prev,
            },
            sort_keys=True,
            default=str,
        )
        h = hashlib.sha256(payload.encode()).hexdigest()
        with audit_chain.open("a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {"date": asof_iso, "previous_hash": prev, "hash": h}
                )
                + "\n"
            )

    if write_excel_dashboard:
        sheet_sources = [
            ("Signals", "signals.csv"),
            ("NAV", "nav.csv"),
            ("Orders", "orders.csv"),
            ("Fills", "fills.csv"),
            ("Dividends", "dividends_applied.csv"),
        ]
        present = [(name, sdir / file) for name, file in sheet_sources if (sdir / file).exists()]
        if present:
            with pd.ExcelWriter(sdir / "E21_forward_dashboard.xlsx", engine="openpyxl") as xw:
                for name, p in present:
                    pd.read_csv(p).to_excel(xw, sheet_name=name, index=False)


def build_portfolio_state_payload(
    *,
    cash: float,
    pos: dict[str, float],
    receivables: dict[str, float],
    latest_iso: str,
    nav: float,
    e22_version: str,
    skip: set[str],
) -> dict[str, Any]:
    return {
        "cash": cash,
        "positions": pos,
        "e22_receivables": receivables,
        "last_date": latest_iso,
        "last_nav": nav,
        "e22_books_version": e22_version,
        "e22_applied_keys": sorted(skip),
        "e22_manifest": books_manifest(e22_version),
        "stage_e_recv_accept": "ACCEPT_2026-09-16_E22_v3_recv_pay_effdelay",
        **build_cutover_stamps(),
    }


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
