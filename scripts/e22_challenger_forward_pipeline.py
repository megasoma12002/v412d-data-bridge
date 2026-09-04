#!/usr/bin/env python3
"""E22 challenger forward package (EXPERIMENTAL) — G5 gap fill.

Paper-parallel copy of the E21 daily loop with cash dividend credits on
``cash_ex_date``. Writes only under ``forward/e22_challenger/``.

Does NOT edit ``scripts/e21_forward_pipeline.py`` or ``forward/e21/`` ledgers.
Promotion to a new SOFT_FROZEN E22 version still requires explicit approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

# Reuse E21 constants / feature logic via import of the frozen script module path.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import e21_forward_pipeline as e21

FIN = e21.FIN
TEL = e21.TEL
ALL = e21.ALL
BUY_FEE = e21.BUY_FEE
SELL_FEE = e21.SELL_FEE
TAX_STOCK = e21.TAX_STOCK
TAX_ETF = e21.TAX_ETF
SLIP = e21.SLIP
CAPITAL = e21.CAPITAL
append_immutable = e21.append_immutable
features = e21.features
holdings = e21.holdings


def load_div_map(path: Path) -> dict:
    if not path.exists():
        return {}
    d = pd.read_csv(path, dtype={"code": str})
    d["cash_ex_date"] = pd.to_datetime(d["cash_ex_date"], errors="coerce")
    d["cash_dividend"] = pd.to_numeric(d["cash_dividend"], errors="coerce")
    d = d.dropna(subset=["cash_ex_date", "cash_dividend"])
    d = d[d["code"].isin(ALL)]
    out: dict[str, list[tuple[str, float]]] = {}
    for _, row in d.iterrows():
        key = pd.Timestamp(row["cash_ex_date"]).date().isoformat()
        out.setdefault(key, []).append((str(row["code"]), float(row["cash_dividend"])))
    return out


def process_one_day(
    m: pd.DataFrame,
    sdir: Path,
    capital: float,
    div_map: dict,
    asof: pd.Timestamp,
) -> dict:
    """Run one E21-equivalent day with E22 dividend credit after fills."""
    required = set(ALL + ["TAIEX"])
    available = m.groupby("date").code.apply(lambda x: required.issubset(set(x)))
    common = available[available].index
    common = common[common <= asof]
    if len(common) == 0:
        raise RuntimeError(f"no complete common trading date <= {asof.date()}")
    latest = common.max()
    m = m[m.date <= latest]
    day = m[m.date == latest].set_index("code")
    missing = [c for c in ALL + ["TAIEX"] if c not in day.index]
    if missing:
        raise RuntimeError(f"latest snapshot incomplete {latest.date()}: {missing}")

    px, sleeve, target, e20, diag = features(m)
    tw = target.iloc[-1]
    e20w = e20.iloc[-1]
    prices = day.close.astype(float).to_dict()
    state_path = sdir / "portfolio_state.json"
    state = (
        json.loads(state_path.read_text())
        if state_path.exists()
        else {"cash": capital, "positions": {}, "last_date": None, "dividend_cash_total": 0.0}
    )
    pos, cash, vals, nav = holdings(state, prices)

    # Fill prior pending orders at today's open (Exact T+1).
    op = day.open.astype(float).to_dict()
    orders_path = sdir / "orders.csv"
    fills = []
    if orders_path.exists():
        orders = pd.read_csv(orders_path, dtype={"code": str})
        filled = set()
        if (sdir / "fills.csv").exists():
            filled = set(pd.read_csv(sdir / "fills.csv").fill_id.astype(str))
        pending = orders[
            (~orders.order_id.astype(str).isin(filled))
            & (pd.to_datetime(orders.signal_date) < latest)
        ]
        for _, o in pending.iterrows():
            q = int(o.quantity)
            side = o.side
            fp = op[o.code] * (1 + SLIP if side == "BUY" else 1 - SLIP)
            gross = q * fp
            fee = gross * (BUY_FEE if side == "BUY" else SELL_FEE + (TAX_ETF if o.code == "0050" else TAX_STOCK))
            signed = q if side == "BUY" else -q
            if side == "BUY" and gross + fee > cash:
                q = max(0, int(cash / (fp * (1 + BUY_FEE))))
                gross = q * fp
                fee = gross * BUY_FEE
                signed = q
            pos[o.code] = pos.get(o.code, 0) + signed
            cash += -gross - fee if side == "BUY" else gross - fee
            fills.append(
                {
                    "fill_id": o.order_id,
                    "signal_date": o.signal_date,
                    "fill_date": latest.date().isoformat(),
                    "code": o.code,
                    "side": side,
                    "quantity": q,
                    "fill_price": fp,
                    "gross": gross,
                    "fees_tax": fee,
                    "slippage_bp": SLIP * 10000,
                }
            )
    for f in fills:
        append_immutable(sdir / "fills.csv", f, "fill_id")

    # E22: credit cash dividends on ex-date for current holdings
    day_key = latest.date().isoformat()
    day_div = 0.0
    for code, cdiv in div_map.get(day_key, []):
        sh = float(pos.get(code, 0) or 0)
        if sh > 0 and cdiv > 0:
            credit = sh * cdiv
            cash += credit
            day_div += credit

    pos, cash, vals, nav = holdings({"positions": pos, "cash": cash}, prices)
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
    order_rows = []
    for sleeve_name, codes in [("Financial", FIN), ("Telecom", TEL), ("0050", ["0050"])]:
        value = sleeve_trade[sleeve_name] * nav / len(codes)
        for c in codes:
            qty = int(abs(value) / prices[c])
            if qty < 1:
                continue
            side = "BUY" if value > 0 else "SELL"
            qty = min(qty, int(pos.get(c, 0))) if side == "SELL" else qty
            if qty < 1:
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
        "e22_dividend_credit": day_div,
    }
    append_immutable(sdir / "signals.csv", signal, "date")
    div_total = float(state.get("dividend_cash_total", 0.0)) + day_div
    navrow = {
        "date": latest.date().isoformat(),
        "nav_e16_e18_e22": nav,
        "cash": cash,
        "pre_financial": pre["Financial"],
        "pre_telecom": pre["Telecom"],
        "pre_0050": pre["0050"],
        "target_l1_gap": l1,
        "orders_created": len(order_rows),
        "fills_processed": len(fills),
        "dividend_credit": day_div,
        "dividend_cash_total": div_total,
    }
    append_immutable(sdir / "nav.csv", navrow, "date")
    state = {
        "cash": cash,
        "positions": pos,
        "last_date": latest.date().isoformat(),
        "last_nav": nav,
        "dividend_cash_total": div_total,
        "package": "e22_challenger",
    }
    state_path.write_text(json.dumps(state, indent=2) + "\n")

    audit = sdir / "audit_chain.jsonl"
    prev = "GENESIS"
    if audit.exists():
        lines = audit.read_text().splitlines()
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
                "previous_hash": prev,
            },
            sort_keys=True,
            default=str,
        )
        h = hashlib.sha256(payload.encode()).hexdigest()
        with audit.open("a") as f:
            f.write(json.dumps({"date": latest.date().isoformat(), "previous_hash": prev, "hash": h}) + "\n")

    return {
        "date": latest.date().isoformat(),
        "nav": nav,
        "orders": len(order_rows),
        "fills": len(fills),
        "dividend_credit": day_div,
        "regime": diag["regime"],
    }


def run_qc(sdir: Path) -> dict:
    checks = {}
    sig = pd.read_csv(sdir / "signals.csv")
    nav = pd.read_csv(sdir / "nav.csv")
    orders = pd.read_csv(sdir / "orders.csv", dtype={"code": str})
    checks["signals_unique_date"] = not sig.date.duplicated().any()
    checks["nav_unique_date"] = not nav.date.duplicated().any()
    checks["orders_unique_id"] = not orders.order_id.duplicated().any()
    checks["weights_sum_one"] = bool(
        ((sig[["e16_financial", "e16_telecom", "e16_0050"]].sum(1) - 1).abs() < 1e-8).all()
    )
    checks["nav_positive"] = bool((nav.nav_e16_e18_e22 > 0).all())
    checks["no_negative_cash"] = bool((nav.cash >= -1).all())
    checks["date_monotonic"] = bool(
        pd.to_datetime(sig.date).is_monotonic_increasing
        and pd.to_datetime(nav.date).is_monotonic_increasing
    )
    checks["frozen_financial_universe"] = set(["2880", "2886", "2892", "5880"]).issuperset(
        set(orders.code.astype(str)) - set(["2412", "3045", "4904", "0050"])
    )
    if (sdir / "fills.csv").exists():
        fills = pd.read_csv(sdir / "fills.csv", dtype={"code": str})
        checks["fills_unique_id"] = not fills.fill_id.duplicated().any()
        checks["fills_reference_existing_orders"] = set(fills.fill_id.astype(str)).issubset(
            set(orders.order_id.astype(str))
        )
        # Exact T+1: fill_date > signal_date
        fd = pd.to_datetime(fills.fill_date)
        sd = pd.to_datetime(fills.signal_date)
        checks["exact_t1_fills"] = bool((fd > sd).all())
    audit = [json.loads(x) for x in (sdir / "audit_chain.jsonl").read_text().splitlines() if x.strip()]
    checks["audit_unique_date"] = len({x["date"] for x in audit}) == len(audit)
    checks["audit_chain_links"] = all(
        audit[i]["previous_hash"] == audit[i - 1]["hash"] for i in range(1, len(audit))
    )

    # Side-by-side vs E21 on shared dates
    compare = {}
    e21_path = Path("forward/e21/nav.csv")
    if e21_path.exists():
        e21n = pd.read_csv(e21_path, parse_dates=["date"])
        both = nav.copy()
        both["date"] = pd.to_datetime(both["date"])
        both = both.merge(e21n[["date", "nav_e16_e18"]], on="date", how="inner")
        if len(both):
            both["nav_lift"] = both["nav_e16_e18_e22"] - both["nav_e16_e18"]
            compare = {
                "n_overlap_sessions": int(len(both)),
                "final_e21_nav": float(both["nav_e16_e18"].iloc[-1]),
                "final_e22_challenger_nav": float(both["nav_e16_e18_e22"].iloc[-1]),
                "final_nav_lift": float(both["nav_lift"].iloc[-1]),
                "total_dividend_cash": float(nav["dividend_cash_total"].iloc[-1]),
            }

    status = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "signal_rows": int(len(sig)),
        "nav_rows": int(len(nav)),
        "order_rows": int(len(orders)),
        "compare_vs_e21": compare,
        "package": "forward/e22_challenger",
        "modifies_e21": False,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (sdir / "qc_status.json").write_text(json.dumps(status, indent=2) + "\n")
    return status


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", default="forward/e21/live_market.csv")
    ap.add_argument("--state-dir", default="forward/e22_challenger")
    ap.add_argument("--dividends", default="data/dividend_events/e22_dividend_events.csv")
    ap.add_argument("--capital", type=float, default=CAPITAL)
    ap.add_argument(
        "--bootstrap-from",
        default=None,
        help="ISO date to start paper replay (default: first E21 nav date if present, else last market date only)",
    )
    ap.add_argument("--reset", action="store_true", help="Wipe challenger state dir before bootstrap")
    args = ap.parse_args()

    sdir = Path(args.state_dir)
    if args.reset and sdir.exists():
        for p in sdir.glob("*"):
            if p.is_file():
                p.unlink()

    sdir.mkdir(parents=True, exist_ok=True)
    m = pd.read_csv(args.market, dtype={"code": str})
    m.date = pd.to_datetime(m.date)
    m = m.sort_values(["date", "code"])
    div_map = load_div_map(Path(args.dividends))

    # Determine replay calendar
    e21_nav = Path("forward/e21/nav.csv")
    if args.bootstrap_from:
        start = pd.Timestamp(args.bootstrap_from)
    elif e21_nav.exists():
        start = pd.to_datetime(pd.read_csv(e21_nav)["date"]).min()
    else:
        start = m.date.max()

    required = set(ALL + ["TAIEX"])
    available = m.groupby("date").code.apply(lambda x: required.issubset(set(x)))
    days = available[available].index
    days = days[days >= start].sort_values()
    if len(days) == 0:
        raise RuntimeError("no bootstrap days")

    results = []
    for dt in days:
        # Idempotent: skip if nav already has this date
        if (sdir / "nav.csv").exists():
            existing = set(pd.read_csv(sdir / "nav.csv")["date"].astype(str))
            if str(dt.date()) in existing:
                continue
        results.append(process_one_day(m, sdir, args.capital, div_map, dt))

    config = {
        "package": "forward/e22_challenger",
        "status": "PAPER_EXPERIMENTAL",
        "modifies_e21": False,
        "recommendation": "RECOMMEND_WIRE_E22_DIVIDENDS_INTO_OFFICIAL_EXEC_PATH_VIA_NEW_VERSION",
        "bootstrap_from": start.date().isoformat(),
        "n_days_processed": len(results),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (sdir / "config.json").write_text(json.dumps(config, indent=2) + "\n")
    qc = run_qc(sdir)

    md = f"""# E22 Challenger Forward (paper parallel)

**Status:** `PAPER_EXPERIMENTAL`

- Path: `forward/e22_challenger/`
- Same E16 targets / Exact T+1 as E21
- **Plus** cash dividend credits on `cash_ex_date`
- Does **not** edit `forward/e21/`

## QC

`{qc['status']}`

Compare vs E21: `{json.dumps(qc.get('compare_vs_e21', {}), default=str)}`

## Next (governance)

1. Keep paper-running beside live E21
2. Explicit approval → new SOFT_FROZEN E22 version
3. Never rewrite historical E21 fills
"""
    (sdir / "README.md").write_text(md)
    Path("research/e22").mkdir(parents=True, exist_ok=True)
    Path("research/e22/E22_CHALLENGER_FORWARD.md").write_text(md)
    print(json.dumps({"qc": qc["status"], "processed": len(results), "compare": qc.get("compare_vs_e21")}, indent=2, default=str))
    if qc["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
