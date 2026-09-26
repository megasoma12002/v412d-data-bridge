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
    E45_STITCH_ROLLBACK,
    KD_OPT,
    LIVE_COOL_EXPOSURE,
    LIVE_COOL_ID,
    LIVE_CUTOVER_BALLOT,
    LIVE_DH_EXPOSURE,
    LIVE_DH_ID,
    LIVE_FIN_PRIV_BALLOT,
    LIVE_FIN_PRIV_V7_F05,
    LIVE_FIN_WITHIN_SLEEVE,
    LIVE_FUSE_ADDITIVE,
    LIVE_FUSE_SOFT_SELL_BALLOT,
    LIVE_FUSE_SOFT_SELL_BOOST,
    TIP_BOOKS_ALIGN_BALLOT,
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
    """Persist day ledgers then atomic portfolio_state (ACCEPT day-commit atomicity).

    Order (crash window shrink):
      1) orders / signals / nav (immutable CSV)
      2) deferred paper fills + dividends_applied
      3) portfolio_state.json last (atomic_write_json)
      4) audit_chain + dashboard

    Soft-Frozen KEEP — never rewrite existing rows (append_immutable first-key wins).
    """
    sdir = Path(state_dir)
    for o in order_rows:
        append_immutable(sdir / "orders.csv", o, "order_id")
    append_immutable(sdir / "signals.csv", signal, "date")
    append_immutable(sdir / "nav.csv", navrow, "date")
    if fill_port_name == "paper":
        for f in fills:
            append_immutable(sdir / "fills.csv", f, "fill_id")
    for row in pending_div_rows:
        append_immutable(div_path, row, "key")
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
        "financial_alloc": LIVE_FIN_WITHIN_SLEEVE,
        "kd_opt_id": KD_OPT["id"],
        "fin_within_sleeve_cutover": "ACCEPT_2026-09-09_KD_OPT",
        "soft_frozen_clip_flip": "ACCEPT_2026-09-09_FINBAND_F0.60-0.90",
        "e45_stitch": False,
        "e45_book": None,
        "e45_stitch_ballot": None,
        "e45_stitch_rollback": E45_STITCH_ROLLBACK,
        "tip_books_align_ballot": TIP_BOOKS_ALIGN_BALLOT,
        "fuse_additive": bool(LIVE_FUSE_ADDITIVE),
        "fuse_soft_sell_boost": float(LIVE_FUSE_SOFT_SELL_BOOST) if LIVE_FUSE_ADDITIVE else None,
        "fuse_soft_sell_ballot": LIVE_FUSE_SOFT_SELL_BALLOT if LIVE_FUSE_ADDITIVE else None,
        "fuse_soft_sell_cutover": (
            "ACCEPT_2026-09-26_SELL_A75_UNDER_COOL" if LIVE_FUSE_ADDITIVE else None
        ),
        "dh_exposure_live": bool(LIVE_DH_EXPOSURE),
        "dh_id": LIVE_DH_ID if LIVE_DH_EXPOSURE else None,
        "cool_exposure_live": bool(LIVE_COOL_EXPOSURE),
        "cool_id": LIVE_COOL_ID if LIVE_COOL_EXPOSURE else None,
        "live_cutover": "ACCEPT_2026-09-25_COOL_c8_REPLACE_DH_KEEP_FUSE",
        "live_cutover_ballot": LIVE_CUTOVER_BALLOT
        if (LIVE_FUSE_ADDITIVE or LIVE_DH_EXPOSURE or LIVE_COOL_EXPOSURE)
        else None,
        "live_cutover_rollback": (
            "Set LIVE_COOL_EXPOSURE=False; optional restore LIVE_DH_EXPOSURE=True "
            "only with dedicated ACCEPT; LIVE_FUSE_ADDITIVE independent; "
            "SELL_a75 → set live_fuse_soft_sell_boost=0.5"
        ),
        "fin_priv_v7_f05_live": bool(LIVE_FIN_PRIV_V7_F05),
        "fin_priv_ballot": LIVE_FIN_PRIV_BALLOT if LIVE_FIN_PRIV_V7_F05 else None,
        "fin_priv_cutover": (
            "ACCEPT_2026-09-25_CLASSD_FINPRIV_V7_F05" if LIVE_FIN_PRIV_V7_F05 else None
        ),
        "fin_priv_rollback": (
            "Set LIVE_FIN_PRIV_V7_F05=False (live_config.live_fin_priv_v7_f05); "
            "gate-off path force-sells PRIV holdings"
            if LIVE_FIN_PRIV_V7_F05
            else None
        ),
    }


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
