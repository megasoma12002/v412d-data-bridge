#!/usr/bin/env python3
"""E21 immutable daily forward signal, execution, NAV and audit ledger.

Formal price split:
  - E16 signals: adj_close
  - Books / fills / NAV: raw open/close + E22_v2s_tw (畸零股面額 CIL)
  - Order sizing: 一張 = 1000 股 (整股); no 零股 (1–999) continuous-book orders

Architecture (2026-09-14 modularize):
  - live_config.LiveConfig — live flags / books / capital SSOT
  - live_strategy_targets — Soft-Frozen + FUSE/DH/E45 overlays
  - live_execution — pending fills at open (Exact T+1)
  - live_ledger — immutable CSV append + holdings
CLI entry and day orchestration stay here.
"""
import argparse, hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e22_dividend_accounting as e22div
import e16_soft_frozen_base as soft_frozen
from e16_soft_frozen_base import FIN, TEL
from tw_share_lots import BOARD_LOT, board_lots
from within_sleeve_alloc import (
    allocate_sleeve_orders,
    build_kd_season_tilt_scores,
    build_pre_exdiv_window_buy_ok,
)
from live_config import (
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
    KD_OPT,
    E22_BOOKS_VERSION,
    DIV_PATH,
)
from live_ledger import ALL, append_immutable, holdings
from live_strategy_targets import features, resolve_session_targets
from live_execution import fill_pending_at_open

# Mutable session capital (CLI may override); default from LiveConfig.
CAPITAL = float(LIVE.capital)


def main():
    global CAPITAL
    ap = argparse.ArgumentParser()
    # Canonical live tree is forward/e21 (nav/orders/signals). Legacy e21_data/e21_state
    # defaults created a second un-audited book — refuse unless explicitly overridden.
    ap.add_argument("--market", default="forward/e21/live_market.csv")
    ap.add_argument("--state-dir", default="forward/e21")
    ap.add_argument("--capital", type=float, default=CAPITAL)
    ap.add_argument("--dividends", default=str(DIV_PATH))
    ap.add_argument(
        "--no-div-amount-repair",
        action="store_true",
        help="Do not auto-refetch/patch dirty dividend amount cells (still fail-closed).",
    )
    ap.add_argument(
        "--e22-version",
        default=E22_BOOKS_VERSION,
        choices=[e22div.E22_V2, e22div.E22_V2S, e22div.E22_V2S_CIL, e22div.E22_V2S_TW],
    )
    ap.add_argument(
        "--confirm-e22-version-override",
        action="store_true",
        help="Required when --e22-version differs from live DEFAULT (E22_v2s_tw).",
    )
    ap.add_argument(
        "--allow-noncanonical-paths",
        action="store_true",
        help="Permit market/state paths outside forward/e21 (research only).",
    )
    ap.add_argument(
        "--asof",
        default=None,
        help="Process this session date (YYYY-MM-DD) instead of market max (replay/ops).",
    )
    a = ap.parse_args()
    if a.e22_version != E22_BOOKS_VERSION and not a.confirm_e22_version_override:
        raise SystemExit(
            f"--e22-version={a.e22_version!r} overrides live DEFAULT {E22_BOOKS_VERSION!r}; "
            "pass --confirm-e22-version-override to proceed (research/ops only)."
        )
    CAPITAL = a.capital
    sdir = Path(a.state_dir)
    market_path = Path(a.market)
    if not a.allow_noncanonical_paths:
        canon_state = Path("forward/e21").resolve()
        canon_market = (Path("forward/e21") / "live_market.csv").resolve()
        if sdir.resolve() != canon_state or market_path.resolve() != canon_market:
            raise SystemExit(
                "Refusing non-canonical live paths. Use --market forward/e21/live_market.csv "
                "and --state-dir forward/e21, or pass --allow-noncanonical-paths for research."
            )
    sdir.mkdir(parents=True, exist_ok=True)
    m = pd.read_csv(market_path, dtype={"code": str})
    m.date = pd.to_datetime(m.date)
    m = m.sort_values(["date", "code"])
    required = set(ALL + ["TAIEX"])
    available = m.groupby("date").code.apply(lambda x: required.issubset(set(x)))
    common = available[available].index
    if len(common) == 0:
        raise RuntimeError("no complete common trading date for all required instruments")
    if a.asof:
        asof = pd.Timestamp(a.asof).normalize()
        if asof not in common:
            raise SystemExit(f"--asof {a.asof} is not a complete common trading date in market")
        latest = asof
    else:
        latest = common.max()
    m = m[m.date <= latest]
    day = m[m.date == latest].set_index("code")
    missing = [c for c in ALL + ["TAIEX"] if c not in day.index]
    if missing:
        raise RuntimeError(f"latest snapshot incomplete {latest.date()}: {missing}")
    px, sleeve, target, e20, diag = features(m)
    tw, _e20w, tw_pre_dh, dh_exposure_today, e45_exposure_today, _fuse_meta, _dh_meta = (
        resolve_session_targets(m, target, latest, a.dividends, LIVE)
    )
    e20w = e20.iloc[-1]
    prices = day.close.astype(float).to_dict()
    state_path = sdir / "portfolio_state.json"
    state = (
        json.loads(state_path.read_text())
        if state_path.exists()
        else {"cash": a.capital, "positions": {}, "last_date": None}
    )
    # Fail-closed: never rewind behind last_date (would rewrite portfolio_state while
    # immutable fills/orders skip via append_immutable — silent book corruption).
    prior_last = state.get("last_date")
    if prior_last:
        prior_ts = pd.Timestamp(prior_last).normalize()
        if latest < prior_ts:
            raise SystemExit(
                f"Refusing session {latest.date()} behind portfolio last_date={prior_last}. "
                "Replay/rebuild requires an explicit wipe path; --asof cannot silently rewind."
            )
    pos, cash, vals, nav = holdings(state, prices, capital=a.capital)
    op = day.open.astype(float).to_dict()
    orders_path = sdir / "orders.csv"
    pos, cash, fills, same_bar_fills, exact_t1_ok = fill_pending_at_open(
        state_dir=sdir, latest=latest, open_prices=op, pos=pos, cash=cash
    )
    audit = {
        "date": latest.date().isoformat(),
        "exact_t1_ok": exact_t1_ok,
        "same_bar_fills": same_bar_fills,
        "fills_checked": len(fills),
        "pending_filter": "signal_date < fill_date",
        "soft_frozen_financial_clip": [soft_frozen.SOFT_FROZEN_FIN_LO, soft_frozen.SOFT_FROZEN_FIN_HI],
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
        "live_cutover_ballot": LIVE_CUTOVER_BALLOT if (LIVE_FUSE_ADDITIVE or LIVE_DH_EXPOSURE) else None,
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

    # E22 formal books on today's ex-date (forward-only; idempotent via applied keys).
    # Live: fail-closed amounts; if dirty cells exist, repair once via refetch then reload.
    # Escape: --no-div-amount-repair (still fail-closed). Soft-Frozen / books unchanged.
    if getattr(a, "no_div_amount_repair", False):
        div_events = e22div.load_dividend_events(
            a.dividends, require_exists=True, fail_closed_amounts=True
        )
    else:
        from e22_dividend_amount_repair import load_dividend_events_with_repair

        div_events = load_dividend_events_with_repair(
            a.dividends, require_exists=True, network=True
        )
    skip = set(state.get("e22_applied_keys") or [])
    div_path = sdir / "dividends_applied.csv"
    if div_path.exists():
        skip |= set(pd.read_csv(div_path)["key"].astype(str))
    pos, cash, applied = e22div.apply_dividends_for_date(
        latest.date().isoformat(),
        pos,
        cash,
        div_events,
        version=a.e22_version,
        skip_keys=skip,
        mark_prices=prices,
    )
    for d in applied.details:
        row = {
            "key": d["key"],
            "date": latest.date().isoformat(),
            "kind": d["kind"],
            "code": d["code"],
            "ex_date": d.get("ex_date"),
            "payment_date": d.get("payment_date", ""),
            "amount_per_share": d.get("amount_per_share"),
            "cash_credit": d.get("cash_credit", 0.0),
            "shares_added": d.get("shares_added", 0.0),
            "fractional_shares": d.get("fractional_shares", 0.0),
            "cil_cash_credit": d.get("cil_cash_credit", 0.0),
            "mark_price": d.get("mark_price", ""),
            "version": d.get("version", a.e22_version),
        }
        append_immutable(div_path, row, "key")
        skip.add(d["key"])

    pos, cash, vals, nav = holdings({"positions": pos, "cash": cash}, prices, capital=a.capital)
    sleeve_vals = {
        "Financial": sum(vals[c] for c in FIN),
        "Telecom": sum(vals[c] for c in TEL),
        "0050": vals["0050"],
    }
    pre = {k: v / nav for k, v in sleeve_vals.items()}
    gap = {k: float(tw[k] - pre[k]) for k in pre}
    l1 = sum(abs(v) for v in gap.values())
    trade = np.zeros(3)
    if max(abs(v) for v in gap.values()) >= 0.015:
        trade = np.array([gap["Financial"], gap["Telecom"], gap["0050"]]) * 0.75
        if abs(trade).sum() > 0.20:
            trade *= 0.20 / abs(trade).sum()
    sleeve_trade = dict(zip(["Financial", "Telecom", "0050"], trade))
    # KD_OPT panels for Financial within-sleeve (forward-only cutover).
    div_df = (
        pd.read_csv(a.dividends, dtype={"code": str})
        if Path(a.dividends).exists()
        else pd.DataFrame()
    )
    cal = pd.to_datetime(m["date"]).drop_duplicates().sort_values()
    kd_scores = build_kd_season_tilt_scores(
        m,
        div_df,
        FIN,
        k_thresh=float(KD_OPT["k_thresh"]),
        season_start=KD_OPT["season_start"],
        season_end=KD_OPT["season_end"],
        pre_days=int(KD_OPT["pre_days"]),
        active_score=float(KD_OPT["active_score"]),
    )
    kd_buy_ok = build_pre_exdiv_window_buy_ok(
        cal,
        div_df,
        FIN,
        pre_days=int(KD_OPT["pre_days"]),
        also_stock_ex=True,
    )
    fin_scores_today = None
    if latest in kd_scores.index:
        fin_scores_today = {
            c: float(kd_scores.loc[latest, c])
            for c in FIN
            if c in kd_scores.columns and pd.notna(kd_scores.loc[latest, c])
        }
    fin_buy_ok_today = None
    if latest in kd_buy_ok.index:
        fin_buy_ok_today = {
            c: bool(kd_buy_ok.loc[latest, c])
            for c in FIN
            if c in kd_buy_ok.columns
        }
    fin_sell_scores_today = None
    # FUSE_ADDITIVE live: Soft observe buy/sell softs on top of KD_OPT panels.
    if LIVE_FUSE_ADDITIVE:
        import live_dh_fuse_cutover as live_cut

        soft_scores, soft_ok, soft_sell = live_cut.fuse_soft_panels_for_asof(
            m, div_df, latest
        )
        if soft_scores is not None:
            fin_scores_today = soft_scores
        if soft_ok is not None:
            fin_buy_ok_today = soft_ok
        fin_sell_scores_today = soft_sell

    order_rows = []
    # Financial: LIVE KD_OPT (+ FUSE softs when LIVE_FUSE_ADDITIVE)
    fin_dollars = float(sleeve_trade["Financial"]) * nav
    if abs(fin_dollars) >= 1e-9:
        for c, side, qty in allocate_sleeve_orders(
            fin_dollars,
            {x: float(prices[x]) for x in FIN},
            pos,
            policy_id=LIVE_FIN_WITHIN_SLEEVE,
            codes=FIN,
            lot_size=BOARD_LOT,
            scores=fin_scores_today,
            buy_ok=fin_buy_ok_today,
            sell_scores=fin_sell_scores_today,
        ):
            if qty < BOARD_LOT or qty % BOARD_LOT != 0:
                continue
            oid = f"{latest.date()}-{c}-{side}"
            order_rows.append(
                {
                    "order_id": oid,
                    "signal_date": latest.date().isoformat(),
                    "code": c,
                    "side": side,
                    "quantity": int(qty),
                    "reference_close": prices[c],
                }
            )
    # Telecom + 0050: keep equal-split within sleeve
    for sleeve_name, codes in [("Telecom", TEL), ("0050", ["0050"])]:
        value = sleeve_trade[sleeve_name] * nav / len(codes)
        for c in codes:
            # Taiwan 整股：1 張 = 1000 股
            qty = board_lots(abs(value) / prices[c])
            if qty < BOARD_LOT:
                continue
            side = "BUY" if value > 0 else "SELL"
            if side == "SELL":
                qty = min(qty, board_lots(pos.get(c, 0)))
            if qty < BOARD_LOT:
                continue
            oid = f"{latest.date()}-{c}-{side}"
            order_rows.append(
                {
                    "order_id": oid,
                    "signal_date": latest.date().isoformat(),
                    "code": c,
                    "side": side,
                    "quantity": qty,
                    "reference_close": prices[c],
                }
            )
    # Persist SELL before BUY so CSV order matches fill preference.
    order_rows.sort(key=lambda o: (0 if o["side"] == "SELL" else 1, o["code"]))
    for o in order_rows:
        append_immutable(orders_path, o, "order_id")
    stamp = datetime.now(timezone.utc).isoformat()
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
        "live_cutover_ballot": LIVE_CUTOVER_BALLOT if (LIVE_FUSE_ADDITIVE or LIVE_DH_EXPOSURE) else None,
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
        "e22_cash_credit": applied.cash_credit,
        "e22_stock_shares_added": applied.stock_shares_added,
    }
    append_immutable(sdir / "nav.csv", navrow, "date")
    state = {
        "cash": cash,
        "positions": pos,
        "last_date": latest.date().isoformat(),
        "last_nav": nav,
        "e22_books_version": a.e22_version,
        "e22_applied_keys": sorted(skip),
        "e22_manifest": e22div.version_manifest(a.e22_version),
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
        "live_cutover_ballot": LIVE_CUTOVER_BALLOT if (LIVE_FUSE_ADDITIVE or LIVE_DH_EXPOSURE) else None,
        "live_cutover_rollback": "Set LIVE_FUSE_ADDITIVE=False and LIVE_DH_EXPOSURE=False",
    }
    state_path.write_text(json.dumps(state, indent=2) + "\n")
    # Hash-chain audit: each row commits to the prior row and today's immutable outputs.
    audit_chain = sdir / "audit_chain.jsonl"
    prev = "GENESIS"
    if audit_chain.exists():
        lines = audit_chain.read_text().splitlines()
        prev = json.loads(lines[-1])["hash"] if lines else prev
        if any(json.loads(x)["date"] == latest.date().isoformat() for x in lines):
            prev = None
    if prev:
        payload = json.dumps(
            {
                "date": latest.date().isoformat(),
                "signal": signal,
                "nav": navrow,
                "orders": order_rows,
                "fills": fills,
                "dividends": applied.details,
                "previous_hash": prev,
            },
            sort_keys=True,
            default=str,
        )
        h = hashlib.sha256(payload.encode()).hexdigest()
        with audit_chain.open("a") as f:
            f.write(json.dumps({"date": latest.date().isoformat(), "previous_hash": prev, "hash": h}) + "\n")
    # Human-friendly Excel dashboard.
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
