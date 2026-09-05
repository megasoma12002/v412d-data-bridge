#!/usr/bin/env python3
"""E21 immutable daily forward signal, execution, NAV and audit ledger.

Formal price split:
  - E16 signals: adj_close
  - Books / fills / NAV: raw open/close + E22_v2s dividend accounting
"""
import argparse, hashlib, json, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e22_dividend_accounting as e22div

FIN = ["2880", "2886", "2892", "5880"]
TEL = ["2412", "3045", "4904"]
ALL = FIN + TEL + ["0050"]
CAPITAL = 3_000_000.0
BUY_FEE = 0.001425 * 0.6
SELL_FEE = 0.001425 * 0.6
TAX_STOCK = 0.003
TAX_ETF = 0.001
SLIP = 0.0005
E22_BOOKS_VERSION = e22div.DEFAULT_BOOKS_VERSION  # E22_v2s formal books
DIV_PATH = Path("data/dividend_events/e22_dividend_events.csv")


def append_immutable(path, row, key):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    new = pd.DataFrame([row])
    if p.exists():
        old = pd.read_csv(p, dtype={"code": str})
        hit = old[old[key].astype(str) == str(row[key])]
        if len(hit):
            # Idempotent rerun: preserve original record; never rewrite history.
            return False
        new = pd.concat([old, new], ignore_index=True)
    new.to_csv(p, index=False)
    return True


def features(m):
    """Live Soft-Frozen E16 targets (Financial clip [0.50, 0.95]).

    Research mirror: `e50_early_stack_combined_nav.e16_features` — keep in sync.
    Challenger clips: `e16_fin_cap_oof_challenger.e16_features_fin_cap` only.
    """
    p = m.pivot(index="date", columns="code", values="adj_close").sort_index().ffill()
    r = p.pct_change(fill_method=None).fillna(0)
    sleeve = pd.DataFrame({"Financial": r[FIN].mean(1), "Telecom": r[TEL].mean(1), "0050": r["0050"]})
    tc = p["TAIEX"]
    tr = tc.pct_change()
    ma = tc.rolling(200).mean()
    vol = tr.rolling(20).std() * np.sqrt(252)
    dd = tc / tc.rolling(252, min_periods=120).max() - 1
    reg = pd.Series("Sideways", index=p.index)
    reg[(tc > ma) & (vol < 0.25)] = "Bull"
    reg[tc < ma] = "Bear"
    reg[(vol > 0.35) | (dd < -0.15)] = "Crisis"
    nav = (1 + sleeve).cumprod()
    m20 = nav / nav.shift(20) - 1
    m60 = nav / nav.shift(60) - 1
    sv = sleeve.rolling(20).std() * np.sqrt(252)
    d60 = nav / nav.rolling(60, min_periods=20).max() - 1
    z = lambda x: x.sub(x.mean(1), axis=0).div(x.std(1).replace(0, np.nan), axis=0).fillna(0)
    score = 0.35 * z(m20) + 0.35 * z(m60) - 0.20 * z(sv) + 0.10 * z(d60)
    # Rebuild frozen E16 target history causally.
    out = []
    cur = np.array([0.9, 0.1, 0.0])
    for i, dt in enumerate(p.index):
        rg = reg.iloc[i]
        pri = {
            "Bull": np.array([0.85, 0.05, 0.10]),
            "Crisis": np.array([0.60, 0.35, 0.05]),
            "Bear": np.array([0.70, 0.25, 0.05]),
            "Sideways": np.array([0.85, 0.10, 0.05]),
        }[rg]
        cand = np.maximum(pri + 0.10 * np.clip(score.iloc[i].to_numpy(), -2, 2), 0)
        cand[0] = np.clip(cand[0], 0.50, 0.95)
        cand[1] = np.clip(cand[1], 0.03, 0.35)
        cand[2] = np.clip(cand[2], 0, 0.35)
        cand /= cand.sum()
        desired = 0.75 * cur + 0.25 * cand
        if np.abs(desired - cur).sum() >= 0.02:
            cur = desired
        out.append(cur.copy())
    target = pd.DataFrame(out, index=p.index, columns=["Financial", "Telecom", "0050"])
    # E19 alert-only.
    defensive = (sleeve.Financial + sleeve["0050"]) / 2
    corr = sleeve.Telecom.rolling(20).corr(defensive)
    te = (1 + sleeve.Telecom).rolling(20).apply(np.prod, raw=True) - 1
    me = (1 + defensive).rolling(20).apply(np.prod, raw=True) - 1
    tv = sleeve.Telecom.rolling(20).std()
    mv = defensive.rolling(20).std()
    pts = (
        (corr > 0.55).astype(int)
        + (te - me < -0.02).astype(int)
        + (tv > mv * 1.15).astype(int)
        + (te < -0.04).astype(int)
    )
    alert = pts >= 2
    # E20 shadow: all three confirmations for 3 days, +3 days under E19 alert.
    price_ok = tc > tc.rolling(20).mean()
    vol_ok = vol < vol.shift(10)
    rel = (1 + sleeve.Financial).cumprod() / (1 + sleeve["0050"]).cumprod()
    rs_ok = rel / rel.shift(20) - 1 >= 0
    conf = price_ok.astype(int) + vol_ok.astype(int) + rs_ok.astype(int)
    streak = []
    n = 0
    for v in (conf >= 3).fillna(False):
        n = n + 1 if v else 0
        streak.append(n)
    e20 = target.copy()
    latest = len(e20) - 1
    req = 6 if alert.iloc[latest] else 3
    if reg.iloc[latest] == "Crisis" and streak[latest] < req:
        release = max(0, e20.iloc[latest, 0] - 0.75)
        e20.iloc[latest, 0] -= release
        e20.iloc[latest, 1] += release
    diag = {
        "regime": reg.iloc[-1],
        "score_financial": score.iloc[-1, 0],
        "score_telecom": score.iloc[-1, 1],
        "score_0050": score.iloc[-1, 2],
        "e19_points": int(pts.iloc[-1]),
        "e19_alert": bool(alert.iloc[-1]),
        "e20_confirmations": int(conf.iloc[-1]),
        "e20_streak": int(streak[-1]),
    }
    return p, sleeve, target, e20, diag


def holdings(state, prices):
    pos = {c: float(state.get("positions", {}).get(c, 0)) for c in ALL}
    cash = float(state.get("cash", CAPITAL))
    vals = {c: pos[c] * prices[c] for c in ALL}
    nav = cash + sum(vals.values())
    return pos, cash, vals, nav


def main():
    global CAPITAL
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", default="e21_data/live_market.csv")
    ap.add_argument("--state-dir", default="e21_state")
    ap.add_argument("--capital", type=float, default=CAPITAL)
    ap.add_argument("--dividends", default=str(DIV_PATH))
    ap.add_argument(
        "--e22-version",
        default=E22_BOOKS_VERSION,
        choices=[e22div.E22_V2, e22div.E22_V2S, e22div.E22_V2S_CIL, e22div.E22_V2S_TW],
    )
    a = ap.parse_args()
    CAPITAL = a.capital
    sdir = Path(a.state_dir)
    sdir.mkdir(parents=True, exist_ok=True)
    m = pd.read_csv(a.market, dtype={"code": str})
    m.date = pd.to_datetime(m.date)
    m = m.sort_values(["date", "code"])
    required = set(ALL + ["TAIEX"])
    available = m.groupby("date").code.apply(lambda x: required.issubset(set(x)))
    common = available[available].index
    if len(common) == 0:
        raise RuntimeError("no complete common trading date for all required instruments")
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
        else {"cash": a.capital, "positions": {}, "last_date": None}
    )
    pos, cash, vals, nav = holdings(state, prices)
    # Fill prior pending orders at today's open (raw open).
    op = day.open.astype(float).to_dict()
    orders_path = sdir / "orders.csv"
    fills = []
    if orders_path.exists():
        orders = pd.read_csv(orders_path, dtype={"code": str})
        filled = set()
        if (sdir / "fills.csv").exists():
            filled = set(pd.read_csv(sdir / "fills.csv").fill_id.astype(str))
        pending = orders[(~orders.order_id.astype(str).isin(filled)) & (pd.to_datetime(orders.signal_date) < latest)]
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

    # E22 formal books on today's ex-date (forward-only; idempotent via applied keys).
    div_events = e22div.load_dividend_events(a.dividends)
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
    for sleeve, codes in [("Financial", FIN), ("Telecom", TEL), ("0050", ["0050"])]:
        value = sleeve_trade[sleeve] * nav / len(codes)
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
    }
    state_path.write_text(json.dumps(state, indent=2) + "\n")
    # Hash-chain audit: each row commits to the prior row and today's immutable outputs.
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
                "dividends": applied.details,
                "previous_hash": prev,
            },
            sort_keys=True,
            default=str,
        )
        h = hashlib.sha256(payload.encode()).hexdigest()
        with audit.open("a") as f:
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
