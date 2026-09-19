#!/usr/bin/env python3
"""E21 immutable daily forward signal, execution, NAV and audit ledger.

Formal price split:
  - E16 signals: adj_close
  - Books / fills / NAV: raw open/close + E22_v3_recv_pay_effdelay
  - Order sizing: 一張 = 1000 股 (整股)

Architecture (modularize cleanup):
  - live_config / live_strategy_targets / live_execution
  - live_session_io · live_e22_day · live_rebalance_orders · live_day_commit
CLI + day orchestration only live here.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import e22_dividend_accounting as e22div
import e16_soft_frozen_base as soft_frozen
import e22_v3_sandbox_books as e22sandbox
from e16_soft_frozen_base import FIN, TEL
from live_config import (
    DIV_PATH,
    E22_BOOKS_VERSION,
    KD_OPT,
    LIVE,
    LIVE_CUTOVER_BALLOT,
    LIVE_DH_EXPOSURE,
    LIVE_DH_ID,
    LIVE_E45_BLEND_ALPHA,
    LIVE_E45_BOOK,
    LIVE_E45_PROFILE,
    LIVE_E45_STITCH,
    LIVE_FIN_WITHIN_SLEEVE,
    LIVE_FUSE_ADDITIVE,
)
from live_day_commit import (
    build_portfolio_state_payload,
    commit_day_books,
    utc_now_iso,
)
from live_e22_day import apply_e22_day, load_div_events_for_live
from live_execution import fill_pending_at_open, resolve_fill_port
from live_ledger import ALL, append_immutable, holdings
from live_rebalance_orders import build_live_order_rows, sleeve_trade_from_gap
from live_session_io import (
    CANON_MARKET,
    CANON_STATE,
    REPO_ROOT,
    assert_canonical_live_paths,
    assert_session_preflight,
    load_market_session,
    load_portfolio_state,
    resolve_fill_port_name,
    resolve_repo_path,
)
from live_strategy_targets import features, resolve_session_targets

CAPITAL = float(LIVE.capital)


def main() -> None:
    global CAPITAL
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", default="forward/e21/live_market.csv")
    ap.add_argument("--state-dir", default="forward/e21")
    ap.add_argument("--capital", type=float, default=CAPITAL)
    ap.add_argument("--dividends", default=str(DIV_PATH))
    ap.add_argument("--no-div-amount-repair", action="store_true")
    ap.add_argument("--apply-div-amount-repair", action="store_true")
    ap.add_argument(
        "--e22-version",
        default=E22_BOOKS_VERSION,
        choices=[
            e22div.E22_V2,
            e22div.E22_V2S,
            e22div.E22_V2S_CIL,
            e22div.E22_V2S_TW,
            e22div.E22_V2S_TW_EFFEX,
            e22div.E22_V3_RECV_PAY_EFFDELAY,
            e22sandbox.E22_V3_RECV_PAY,
            e22sandbox.E22_V3_TAX10,
            e22sandbox.E22_V3_TAX20,
            e22sandbox.E22_V3_RECV_PAY_TAX10,
            e22sandbox.E22_V3_RECV_PAY_TAX20,
        ],
    )
    ap.add_argument("--confirm-e22-version-override", action="store_true")
    ap.add_argument("--allow-noncanonical-paths", action="store_true")
    ap.add_argument("--asof", default=None)
    ap.add_argument("--fill-port", default=None)
    a = ap.parse_args()
    if a.e22_version != E22_BOOKS_VERSION and not a.confirm_e22_version_override:
        raise SystemExit(
            f"--e22-version={a.e22_version!r} overrides live DEFAULT {E22_BOOKS_VERSION!r}; "
            "pass --confirm-e22-version-override to proceed (research/ops only)."
        )
    CAPITAL = a.capital
    sdir = resolve_repo_path(a.state_dir)
    market_path = resolve_repo_path(a.market)
    fill_port_name = resolve_fill_port_name(a.fill_port)
    assert_canonical_live_paths(
        state_dir=sdir,
        market_path=market_path,
        fill_port_name=fill_port_name,
        allow_noncanonical=a.allow_noncanonical_paths,
    )
    sdir.mkdir(parents=True, exist_ok=True)

    m, latest, day = load_market_session(market_path, asof=a.asof)
    px, sleeve, target, e20, diag = features(m)
    tw, _e20w, tw_pre_dh, dh_exposure_today, e45_exposure_today, _fuse_meta, _dh_meta = (
        resolve_session_targets(m, target, latest, a.dividends, LIVE)
    )
    e20w = e20.iloc[-1]
    prices = day.close.astype(float).to_dict()
    state_path = sdir / "portfolio_state.json"
    state = load_portfolio_state(sdir, capital=a.capital)
    assert_session_preflight(sdir, state, latest)

    pos, cash, vals, nav = holdings(state, prices, capital=a.capital)
    op = day.open.astype(float).to_dict()
    fill_port = resolve_fill_port(fill_port_name)
    pos, cash, fills, same_bar_fills, exact_t1_ok = fill_pending_at_open(
        state_dir=sdir,
        latest=latest,
        open_prices=op,
        pos=pos,
        cash=cash,
        fill_port=fill_port,
    )
    audit = {
        "date": latest.date().isoformat(),
        "exact_t1_ok": exact_t1_ok,
        "same_bar_fills": same_bar_fills,
        "fills_checked": len(fills),
        "fill_port": fill_port.name,
        "pending_filter": "signal_date < fill_date",
        "soft_frozen_financial_clip": [
            soft_frozen.SOFT_FROZEN_FIN_LO,
            soft_frozen.SOFT_FROZEN_FIN_HI,
        ],
        "financial_alloc": LIVE_FIN_WITHIN_SLEEVE,
        "kd_opt_id": KD_OPT["id"],
        "e45_stitch": LIVE_E45_STITCH,
        "e45_book": LIVE_E45_BOOK if LIVE_E45_STITCH else None,
        "e45_profile": LIVE_E45_PROFILE if LIVE_E45_STITCH else None,
        "e45_blend_alpha": LIVE_E45_BLEND_ALPHA if LIVE_E45_STITCH else None,
        "e45_exposure": float(e45_exposure_today) if LIVE_E45_STITCH else None,
        "fuse_additive": bool(LIVE_FUSE_ADDITIVE),
        "dh_exposure_live": bool(LIVE_DH_EXPOSURE),
        "dh_id": LIVE_DH_ID if LIVE_DH_EXPOSURE else None,
        "dh_exposure": float(dh_exposure_today) if LIVE_DH_EXPOSURE else None,
        "e16_financial_pre_dh": float(tw_pre_dh["Financial"]) if LIVE_DH_EXPOSURE else None,
        "live_cutover_ballot": LIVE_CUTOVER_BALLOT
        if (LIVE_FUSE_ADDITIVE or LIVE_DH_EXPOSURE)
        else None,
        "live_wire": True,
        "owns_qc_status": False,
        "note": (
            "Pipeline Exact T+1 audit only. qc_status.json is owned by e21_qc.py; "
            "this file is pipeline_t1_audit.json."
        ),
    }
    (sdir / "pipeline_t1_audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    if not exact_t1_ok:
        raise SystemExit(
            f"Exact T+1 violation: {same_bar_fills} same-bar fill(s) on {latest.date()}"
        )

    div_events = load_div_events_for_live(
        a.dividends,
        no_repair=bool(a.no_div_amount_repair),
        apply_repair=bool(a.apply_div_amount_repair),
    )
    skip = set(state.get("e22_applied_keys") or [])
    div_path = sdir / "dividends_applied.csv"
    if div_path.exists():
        import pandas as pd

        skip |= set(pd.read_csv(div_path)["key"].astype(str))
    receivables = {
        str(k): float(v) for k, v in (state.get("e22_receivables") or {}).items()
    }
    pos, cash, receivables, applied, pending_div_rows = apply_e22_day(
        asof_iso=latest.date().isoformat(),
        pos=pos,
        cash=cash,
        div_events=div_events,
        e22_version=a.e22_version,
        skip=skip,
        prices=prices,
        receivables=receivables,
    )

    pos, cash, vals, nav = holdings(
        {"positions": pos, "cash": cash, "e22_receivables": receivables},
        prices,
        capital=a.capital,
    )
    sleeve_vals = {
        "Financial": sum(vals[c] for c in FIN),
        "Telecom": sum(vals[c] for c in TEL),
        "0050": vals["0050"],
    }
    pre = {k: v / nav for k, v in sleeve_vals.items()}
    sleeve_trade, l1 = sleeve_trade_from_gap(pre, tw)
    orders_path = sdir / "orders.csv"
    order_rows = build_live_order_rows(
        market=m,
        latest=latest,
        prices=prices,
        pos=pos,
        nav=nav,
        sleeve_trade=sleeve_trade,
        dividends_path=a.dividends,
    )
    for o in order_rows:
        append_immutable(orders_path, o, "order_id")

    stamp = utc_now_iso()
    signal = {
        "date": latest.date().isoformat(),
        "generated_at_utc": stamp,
        "data_max_date": latest.date().isoformat(),
        **diag,
        "e16_financial": tw.Financial,
        "e16_telecom": tw.Telecom,
        "e16_0050": tw["0050"],
        "e20_financial": e20w.Financial,
        "e20_telecom": e20w.Telecom,
        "e20_0050": e20w["0050"],
        "financial_alloc": LIVE_FIN_WITHIN_SLEEVE,
        "kd_opt_id": KD_OPT["id"],
        "e45_stitch": LIVE_E45_STITCH,
        "e45_book": LIVE_E45_BOOK if LIVE_E45_STITCH else None,
        "e45_blend_alpha": LIVE_E45_BLEND_ALPHA if LIVE_E45_STITCH else None,
        "e45_exposure": float(e45_exposure_today) if LIVE_E45_STITCH else None,
        "fuse_additive": bool(LIVE_FUSE_ADDITIVE),
        "dh_exposure_live": bool(LIVE_DH_EXPOSURE),
        "dh_id": LIVE_DH_ID if LIVE_DH_EXPOSURE else None,
        "dh_exposure": float(dh_exposure_today) if LIVE_DH_EXPOSURE else None,
        "e16_financial_pre_dh": float(tw_pre_dh["Financial"]) if LIVE_DH_EXPOSURE else None,
        "e16_telecom_pre_dh": float(tw_pre_dh["Telecom"]) if LIVE_DH_EXPOSURE else None,
        "e16_0050_pre_dh": float(tw_pre_dh["0050"]) if LIVE_DH_EXPOSURE else None,
        "live_cutover_ballot": LIVE_CUTOVER_BALLOT
        if (LIVE_FUSE_ADDITIVE or LIVE_DH_EXPOSURE)
        else None,
    }
    append_immutable(sdir / "signals.csv", signal, "date")
    navrow = {
        "date": latest.date().isoformat(),
        "nav_e16_e18": nav,
        "cash": cash,
        "pre_financial": pre["Financial"],
        "pre_telecom": pre["Telecom"],
        "pre_0050": pre["0050"],
        "target_l1_gap": l1,
        "orders_created": len(order_rows),
        "fills_processed": len(fills),
        "exact_t1_ok": exact_t1_ok,
        "same_bar_fills": same_bar_fills,
        "e22_version": a.e22_version,
        "e22_cash_credit": float(getattr(applied, "cash_credit", 0.0) or 0.0),
        "e22_receivable_credit": float(getattr(applied, "receivable_credit", 0.0) or 0.0),
        "e22_receivable_settled": float(getattr(applied, "receivable_settled", 0.0) or 0.0),
        "e22_stock_shares_added": float(getattr(applied, "stock_shares_added", 0.0) or 0.0),
        "e22_receivable_balance": float(sum(receivables.values())),
    }
    append_immutable(sdir / "nav.csv", navrow, "date")

    state_payload = build_portfolio_state_payload(
        cash=cash,
        pos=pos,
        receivables=receivables,
        latest_iso=latest.date().isoformat(),
        nav=nav,
        e22_version=a.e22_version,
        skip=skip,
    )
    commit_day_books(
        state_dir=sdir,
        fill_port_name=fill_port.name,
        fills=fills,
        pending_div_rows=pending_div_rows,
        div_path=div_path,
        state_path=state_path,
        state_payload=state_payload,
        signal=signal,
        navrow=navrow,
        order_rows=order_rows,
        applied_details=applied.details,
        asof_iso=latest.date().isoformat(),
    )
    print(
        json.dumps(
            {
                "status": "PASS",
                "date": latest.date().isoformat(),
                "nav": nav,
                "orders": len(order_rows),
                "fills": len(fills),
                "exact_t1_ok": exact_t1_ok,
                "same_bar_fills": same_bar_fills,
                "regime": diag["regime"],
                "e19_alert": diag["e19_alert"],
                "e22_version": a.e22_version,
                "e22_cash_credit": applied.cash_credit,
                "e22_stock_shares_added": applied.stock_shares_added,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
