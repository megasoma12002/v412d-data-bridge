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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tw_share_lots import BOARD_LOT

REPO_ROOT = Path(__file__).resolve().parents[1]
CANON_STATE = REPO_ROOT / "forward" / "e21"


# Frozen allowlist removed after authorized replay cleared historical qty=0 fills (2026-09-07).
LEGACY_ZERO_QTY_FILL_IDS = frozenset()


def exact_t1_from_fills(fills: pd.DataFrame, *, fills_required: bool = True) -> dict:
    """Require fill_date strictly after signal_date (calendar day).

    Live default (fills_required=True): empty/missing fills ⇒ Exact T+1 FAIL.
    Research opt-out (fills_required=False): empty fills → ok (nothing to violate).
    Non-empty fills missing the date schema → always fail closed.
    Blank / NaT dates → fail closed (not same-bar-ok).
    """
    if fills.empty:
        return {
            "exact_t1_ok": False if fills_required else True,
            "same_bar_fills": 0,
            "fills_checked": 0,
            "pending_filter": "signal_date < fill_date",
            "schema_ok": True,
            "reason": "fills_missing_or_incomplete" if fills_required else None,
        }
    if "signal_date" not in fills.columns or "fill_date" not in fills.columns:
        return {
            "exact_t1_ok": False,
            "same_bar_fills": -1,
            "fills_checked": int(len(fills)),
            "pending_filter": "signal_date < fill_date",
            "schema_ok": False,
            "reason": "fills_missing_or_incomplete",
        }
    sig = pd.to_datetime(fills["signal_date"], errors="coerce").dt.normalize()
    fill_dt = pd.to_datetime(fills["fill_date"], errors="coerce").dt.normalize()
    if int(sig.isna().sum() + fill_dt.isna().sum()) > 0:
        return {
            "exact_t1_ok": False,
            "same_bar_fills": -1,
            "fills_checked": int(len(fills)),
            "pending_filter": "signal_date < fill_date",
            "schema_ok": False,
            "reason": "fills_date_nat_or_blank",
        }
    same_bar = int((fill_dt <= sig).sum())
    return {
        "exact_t1_ok": same_bar == 0,
        "same_bar_fills": same_bar,
        "fills_checked": int(len(fills)),
        "pending_filter": "signal_date < fill_date",
        "schema_ok": True,
        "reason": None if same_bar == 0 else "same_bar_fills_present",
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
    if not s.is_absolute():
        s = (REPO_ROOT / s).resolve()

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
    fin = sig["e16_financial"].astype(float)
    checks["weights_sum_one"] = bool(
        ((sig[["e16_financial", "e16_telecom", "e16_0050"]].sum(1) - 1).abs() < 1e-8).all()
    )
    # Soft-Frozen sleeve envelope — import bounds, never hardcode.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from e16_soft_frozen_base import (
        FIN,
        TEL,
        SOFT_FROZEN_FIN_HI,
        SOFT_FROZEN_FIN_LO,
        SOFT_FROZEN_TEL_HI,
        SOFT_FROZEN_TEL_LO,
        SOFT_FROZEN_ETF_HI,
        SOFT_FROZEN_ETF_LO,
    )

    tel = sig["e16_telecom"].astype(float)
    etf = sig["e16_0050"].astype(float)
    checks["soft_frozen_fin_clip"] = bool(
        ((fin >= SOFT_FROZEN_FIN_LO - 1e-9) & (fin <= SOFT_FROZEN_FIN_HI + 1e-9)).all()
    )
    checks["soft_frozen_tel_clip"] = bool(
        ((tel >= SOFT_FROZEN_TEL_LO - 1e-9) & (tel <= SOFT_FROZEN_TEL_HI + 1e-9)).all()
    )
    checks["soft_frozen_etf_clip"] = bool(
        ((etf >= SOFT_FROZEN_ETF_LO - 1e-9) & (etf <= SOFT_FROZEN_ETF_HI + 1e-9)).all()
    )
    checks["nav_positive"] = bool((nav.nav_e16_e18 > 0).all())
    checks["no_negative_cash"] = bool((nav.cash >= -1).all())
    checks["date_monotonic"] = bool(
        pd.to_datetime(sig.date).is_monotonic_increasing
        and pd.to_datetime(nav.date).is_monotonic_increasing
    )
    checks["frozen_financial_universe"] = set(FIN).issuperset(
        set(orders.code.astype(str)) - set(TEL + ["0050"])
    )

    fills_path = s / "fills.csv"
    checks["fills_file_present"] = fills_path.exists()
    fills = pd.DataFrame()
    if fills_path.exists():
        fills = pd.read_csv(fills_path, dtype={"code": str})
        checks["fills_unique_id"] = not fills.fill_id.duplicated().any()
        checks["fills_reference_existing_orders"] = set(fills.fill_id.astype(str)).issubset(
            set(orders.order_id.astype(str))
        )
        if "quantity" not in fills.columns:
            checks["fills_positive_qty"] = False
            checks["fills_board_lot_1000"] = False
        else:
            qty = pd.to_numeric(fills["quantity"], errors="coerce")
            legacy = fills["fill_id"].astype(str).isin(LEGACY_ZERO_QTY_FILL_IDS)
            # Fail-closed on qty<=0 except frozen pre-fix residue (no history rewrite).
            checks["fills_positive_qty"] = bool(((qty > 0) | legacy).all() and not qty.isna().any())
            # Taiwan 整股：live fills must be multiples of 一張=1000.
            from tw_share_lots import BOARD_LOT

            checks["fills_board_lot_1000"] = bool(
                ((qty % BOARD_LOT == 0) | legacy).all() and not qty.isna().any()
            )
    else:
        checks["fills_unique_id"] = False
        checks["fills_reference_existing_orders"] = False
        checks["fills_positive_qty"] = False
        checks["fills_board_lot_1000"] = False

    # Live ledgers must have an auditable fills file; empty/missing ⇒ Exact T+1 FAIL.
    t1 = exact_t1_from_fills(fills, fills_required=True)
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
        "exact_t1_reason": t1.get("reason"),
        "schema_ok": t1.get("schema_ok"),
        "live_wire": True,
        "owns_qc_status": True,
        "note": (
            "Fail-closed ledger QC + Exact T+1. Missing/empty fills ⇒ FAIL. "
            "Soft-Frozen clip imported from e16_soft_frozen_base. "
            "This file is owned by e21_qc.py; pipeline writes pipeline_t1_audit.json only."
        ),
    }
    (s / "qc_status.json").write_text(json.dumps(status, indent=2) + "\n")
    print(json.dumps(status, indent=2))
    if status["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
