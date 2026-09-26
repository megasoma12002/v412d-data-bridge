#!/usr/bin/env python3
"""Fail-closed QC for E21 forward ledgers.

Canonical live tree: ``forward/e21``. Writes ``qc_status.json`` including
Exact T+1 fields so a post-pipeline QC run does not drop pipeline audits.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

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
    sleeve_sum = sig[["e16_financial", "e16_telecom", "e16_0050"]].sum(1)
    # Soft-Frozen Financial envelope — import bounds, never hardcode.
    # Forward-only: tip rows before CLIP_FLIP_ASOF may use PRIOR_FIN_HI.
    from e16_soft_frozen_base import (
        FIN,
        TEL,
        SOFT_FROZEN_FIN_LO,
        soft_frozen_fin_hi_for_dates,
    )

    fin_hi = soft_frozen_fin_hi_for_dates(sig["date"])
    fin_hi.index = sig.index

    # Risk overlay (legacy DH or live COOL) may scale sleeve weights (<1 → residual cash).
    # Prefer pre-overlay Financial for Soft-Frozen clip when recorded. Mixed tip
    # history (DH then COOL) is handled row-wise.
    has_cool = "cool_exposure" in sig.columns and sig["cool_exposure"].notna().any()
    has_dh = "dh_exposure" in sig.columns and sig["dh_exposure"].notna().any()
    if has_cool or has_dh:
        nan_s = pd.Series(float("nan"), index=sig.index, dtype=float)
        cool = (
            sig["cool_exposure"].astype(float)
            if "cool_exposure" in sig.columns
            else nan_s.copy()
        )
        dh = (
            sig["dh_exposure"].astype(float)
            if "dh_exposure" in sig.columns
            else nan_s.copy()
        )
        # Prefer COOL when both present on a row (should not happen after stack refuse).
        exp = cool.where(cool.notna(), dh).fillna(1.0)
        checks["weights_sum_one"] = bool(((sleeve_sum - exp).abs() < 1e-6).all())
        if (
            "e16_financial_pre_cool" in sig.columns
            and sig["e16_financial_pre_cool"].notna().any()
        ):
            pre_cool = sig["e16_financial_pre_cool"].astype(float)
        else:
            pre_cool = nan_s.copy()
        if (
            "e16_financial_pre_dh" in sig.columns
            and sig["e16_financial_pre_dh"].notna().any()
        ):
            pre_dh = sig["e16_financial_pre_dh"].astype(float)
        else:
            pre_dh = nan_s.copy()
        fin_clip = pre_cool.where(pre_cool.notna(), pre_dh)
        need_scale = fin_clip.isna() & (exp > 0)
        fin_clip = fin_clip.where(~need_scale, fin / exp.replace(0.0, float("nan")))
        ok = fin_clip.isna() | (
            (fin_clip >= SOFT_FROZEN_FIN_LO - 1e-9) & (fin_clip <= fin_hi + 1e-9)
        )
        checks["soft_frozen_fin_clip"] = bool(ok.all())
    else:
        checks["weights_sum_one"] = bool(((sleeve_sum - 1).abs() < 1e-8).all())
        checks["soft_frozen_fin_clip"] = bool(
            ((fin >= SOFT_FROZEN_FIN_LO - 1e-9) & (fin <= fin_hi + 1e-9)).all()
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
    # Class D FinPriv ACCEPT: allow PRIV_R3R4 in Financial orders when live flag on.
    try:
        from live_config import LIVE_FIN_PRIV_V7_F05
    except Exception:
        LIVE_FIN_PRIV_V7_F05 = False
    if LIVE_FIN_PRIV_V7_F05:
        import live_finhc_v7_f05_cutover as finpriv

        allowed_fin = set(FIN) | set(finpriv.PRIV_CODES)
        checks["frozen_financial_universe"] = allowed_fin.issuperset(
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

    # Tip nav.e22_version must be present and match portfolio_state books
    # (DEFAULT cutover is a separate ACCEPT — do not fail-closed on tip≠DEFAULT).
    if "e22_version" not in nav.columns or nav.empty:
        checks["nav_tip_e22_version_present"] = False
        checks["nav_tip_matches_state_books"] = False
    else:
        tip_ver = nav.iloc[-1].get("e22_version")
        tip_ok = (
            tip_ver is not None
            and not (isinstance(tip_ver, float) and pd.isna(tip_ver))
            and str(tip_ver).strip() != ""
        )
        checks["nav_tip_e22_version_present"] = bool(tip_ok)
        state_path = s / "portfolio_state.json"
        if tip_ok and state_path.exists():
            try:
                st = json.loads(state_path.read_text(encoding="utf-8"))
                checks["nav_tip_matches_state_books"] = str(
                    st.get("e22_books_version") or ""
                ).strip() == str(tip_ver).strip()
            except (OSError, json.JSONDecodeError):
                checks["nav_tip_matches_state_books"] = False
        else:
            checks["nav_tip_matches_state_books"] = False

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
