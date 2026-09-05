#!/usr/bin/env python3
"""Fail-closed QC for E21 forward ledgers.

Canonical live tree: ``forward/e21``. Writes ``qc_status.json`` including
Exact T+1 fields so a post-pipeline QC run does not drop pipeline audits.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

CANON_STATE = Path("forward/e21")


def exact_t1_from_fills(fills: pd.DataFrame) -> dict:
    """Require fill_date strictly after signal_date (calendar day)."""
    if fills.empty or "signal_date" not in fills.columns or "fill_date" not in fills.columns:
        return {
            "exact_t1_ok": True,
            "same_bar_fills": 0,
            "fills_checked": int(len(fills)),
            "pending_filter": "signal_date < fill_date",
        }
    sig = pd.to_datetime(fills["signal_date"]).dt.normalize()
    fill_dt = pd.to_datetime(fills["fill_date"]).dt.normalize()
    same_bar = int((fill_dt <= sig).sum())
    return {
        "exact_t1_ok": same_bar == 0,
        "same_bar_fills": same_bar,
        "fills_checked": int(len(fills)),
        "pending_filter": "signal_date < fill_date",
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Fail-closed QC for E21 forward ledgers")
    ap.add_argument("--state-dir", default=str(CANON_STATE))
    ap.add_argument(
        "--allow-noncanonical-paths",
        action="store_true",
        help="Permit state dirs outside forward/e21 (research only).",
    )
    a = ap.parse_args()
    s = Path(a.state_dir)

    if not a.allow_noncanonical_paths and s.resolve() != CANON_STATE.resolve():
        raise SystemExit(
            "Refusing non-canonical live path. Use --state-dir forward/e21 "
            "or pass --allow-noncanonical-paths for research."
        )

    checks: dict = {}
    sig = pd.read_csv(s / "signals.csv")
    nav = pd.read_csv(s / "nav.csv")
    orders = pd.read_csv(s / "orders.csv", dtype={"code": str})

    checks["signals_unique_date"] = not sig.date.duplicated().any()
    checks["nav_unique_date"] = not nav.date.duplicated().any()
    checks["orders_unique_id"] = not orders.order_id.duplicated().any()
    checks["weights_sum_one"] = bool(
        ((sig[["e16_financial", "e16_telecom", "e16_0050"]].sum(1) - 1).abs() < 1e-8).all()
    )
    checks["nav_positive"] = bool((nav.nav_e16_e18 > 0).all())
    checks["no_negative_cash"] = bool((nav.cash >= -1).all())
    checks["date_monotonic"] = bool(
        pd.to_datetime(sig.date).is_monotonic_increasing
        and pd.to_datetime(nav.date).is_monotonic_increasing
    )
    checks["frozen_financial_universe"] = set(["2880", "2886", "2892", "5880"]).issuperset(
        set(orders.code.astype(str)) - set(["2412", "3045", "4904", "0050"])
    )

    fills = pd.DataFrame()
    if (s / "fills.csv").exists():
        fills = pd.read_csv(s / "fills.csv", dtype={"code": str})
        checks["fills_unique_id"] = not fills.fill_id.duplicated().any()
        checks["fills_reference_existing_orders"] = set(fills.fill_id.astype(str)).issubset(
            set(orders.order_id.astype(str))
        )

    t1 = exact_t1_from_fills(fills)
    checks["exact_t1_ok"] = bool(t1["exact_t1_ok"])

    audit = [
        json.loads(x)
        for x in (s / "audit_chain.jsonl").read_text().splitlines()
        if x.strip()
    ]
    checks["audit_unique_date"] = len({x["date"] for x in audit}) == len(audit)
    checks["audit_chain_links"] = all(
        audit[i]["previous_hash"] == audit[i - 1]["hash"] for i in range(1, len(audit))
    )

    all_pass = all(checks.values())
    status = {
        "status": "PASS" if all_pass else "FAIL",
        "checks": checks,
        "signal_rows": len(sig),
        "nav_rows": len(nav),
        "order_rows": len(orders),
        # Preserve Exact T+1 audit fields (do not drop after pipeline write).
        "exact_t1_ok": t1["exact_t1_ok"],
        "same_bar_fills": t1["same_bar_fills"],
        "fills_checked": t1["fills_checked"],
        "pending_filter": t1["pending_filter"],
        "live_wire": True,
        "note": "Fail-closed ledger QC + Exact T+1. Soft-Frozen clip unchanged by research.",
    }
    (s / "qc_status.json").write_text(json.dumps(status, indent=2) + "\n")
    print(json.dumps(status, indent=2))
    if status["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
