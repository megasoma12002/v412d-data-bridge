#!/usr/bin/env python3
"""Shared ops observe helpers — cashflow / R4 / Stage-E labels.

Soft-Frozen KEEP. No tip invent. No broker promote.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from e22_dividend_accounting import (
    DEFAULT_BOOKS_VERSION as STAGE_E_DEFAULT,
    PRESERVED_CASH_ON_EX,
)

R4_SUMMARY_KEYS = (
    "settling_today_net",
    "unsettled_net",
    "paper_cash",
    "settled_cash_estimate",
)

# R4 identity: settled ≈ paper - unsettled (float tolerance)
R4_IDENTITY_TOL = 1.0  # NT$1


def load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def as_float(x: Any) -> float | None:
    if x is None:
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def receivable_total(state: dict) -> float:
    recv = state.get("e22_receivables") or {}
    if not isinstance(recv, dict):
        return 0.0
    return float(sum(float(v) for v in recv.values()))


def r4_artifacts_present(state_dir: Path) -> bool:
    """True when both R4 CSV and JSON exist and are non-empty."""
    csv_path = state_dir / "settlement_cash_estimate.csv"
    json_path = state_dir / "settlement_cash_estimate.json"
    if not csv_path.is_file() or not json_path.is_file():
        return False
    if csv_path.stat().st_size <= 0 or json_path.stat().st_size <= 0:
        return False
    return True


def r4_summary(state_dir: Path, *, tol: float = R4_IDENTITY_TOL) -> dict:
    payload = load_json(state_dir / "settlement_cash_estimate.json")
    if not payload:
        return {"present": False}
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else payload
    paper = as_float(summary.get("paper_cash"))
    unsettled = as_float(summary.get("unsettled_net"))
    settled = as_float(summary.get("settled_cash_estimate"))
    identity_ok = None
    identity_delta = None
    if paper is not None and unsettled is not None and settled is not None:
        identity_delta = paper - unsettled - settled
        identity_ok = abs(identity_delta) <= float(tol)
    missing_keys = [k for k in R4_SUMMARY_KEYS if summary.get(k) is None]
    return {
        "present": True,
        "asof": summary.get("asof"),
        "paper_cash": paper,
        "settled_cash_estimate": settled,
        "unsettled_net": unsettled,
        "settling_today_net": as_float(summary.get("settling_today_net")),
        "n_unsettled": summary.get("n_unsettled"),
        "identity_ok": identity_ok,
        "identity_delta": identity_delta,
        "missing_summary_keys": missing_keys,
        "note": summary.get("note")
        or "liquidity view NOT portfolio cash / NOT NAV",
    }


__all__ = [
    "STAGE_E_DEFAULT",
    "PRESERVED_CASH_ON_EX",
    "R4_SUMMARY_KEYS",
    "R4_IDENTITY_TOL",
    "load_json",
    "as_float",
    "receivable_total",
    "r4_artifacts_present",
    "r4_summary",
]
