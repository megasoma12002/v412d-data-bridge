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
from live_config import (
    KD_OPT,
    LIVE_CUTOVER_BALLOT,
    LIVE_DH_EXPOSURE,
    LIVE_DH_ID,
    LIVE_E45_BLEND_ALPHA,
    LIVE_E45_BOOK,
    LIVE_E45_STITCH,
    LIVE_FIN_WITHIN_SLEEVE,
    LIVE_FUSE_ADDITIVE,
)
from live_ledger import append_immutable, atomic_write_json


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
) -> None:
    """Persist deferred paper fills + dividends, then atomic state + audit."""
    sdir = Path(state_dir)
    if fill_port_name == "paper":
        for f in fills:
            append_immutable(sdir / "fills.csv", f, "fill_id")
    for row in pending_div_rows:
        append_immutable(div_path, row, "key")
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

    with pd.ExcelWriter(sdir / "E21_forward_dashboard.xlsx", engine="openpyxl") as xw:
        for name, file in [
            ("Signals", "signals.csv"),
            ("NAV", "nav.csv"),
            ("Orders", "orders.csv"),
            ("Fills", "fills.csv"),
            ("Dividends", "dividends_applied.csv"),
        ]:
            p = sdir / file
            if p.exists():
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
        "financial_alloc": LIVE_FIN_WITHIN_SLEEVE,
        "kd_opt_id": KD_OPT["id"],
        "fin_within_sleeve_cutover": "ACCEPT_2026-09-09_KD_OPT",
        "soft_frozen_clip_flip": "ACCEPT_2026-09-09_FINBAND_F0.60-0.90",
        "e45_stitch": LIVE_E45_STITCH,
        "e45_book": LIVE_E45_BOOK if LIVE_E45_STITCH else None,
        "e45_stitch_ballot": None,
        "e45_stitch_rollback": "ACCEPT_2026-09-09_DROP_E45_A05",
        "fuse_additive": bool(LIVE_FUSE_ADDITIVE),
        "dh_exposure_live": bool(LIVE_DH_EXPOSURE),
        "dh_id": LIVE_DH_ID if LIVE_DH_EXPOSURE else None,
        "live_cutover": "ACCEPT_2026-09-13_DH_dd06_FUSE_ADDITIVE",
        "live_cutover_ballot": LIVE_CUTOVER_BALLOT
        if (LIVE_FUSE_ADDITIVE or LIVE_DH_EXPOSURE)
        else None,
        "live_cutover_rollback": "Set LIVE_FUSE_ADDITIVE=False and LIVE_DH_EXPOSURE=False",
    }


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
