#!/usr/bin/env python3
"""E22_v2 — official SOFT_FROZEN cash_ex_date dividend path.

Version: E22_v2_CASH_EX_OFFICIAL_PATH
Approved: 2026-09-04

Same E16 targets / Exact T+1 / fees as E21, plus cash dividend credits on
``cash_ex_date``. Writes only under ``forward/e22_v2/``.

Preserves ``scripts/e21_forward_pipeline.py`` and ``forward/e21/`` forever
(read-only baseline without dividend cash in the fill loop).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e21_forward_pipeline as e21

VERSION_ID = "E22_v2_CASH_EX_OFFICIAL_PATH"
PACKAGE = "e22_v2"
DEFAULT_STATE = "forward/e22_v2"
APPROVED_AT = "2026-09-04"
APPROVAL_PHRASE = (
    "APPROVE E22_v2_CASH_EX_OFFICIAL_PATH — wire cash_ex_date credits into "
    "official exec path as new SOFT_FROZEN version; preserve forward/e21 forever."
)

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


def init_cutover_from_e21(sdir: Path, e21_dir: Path) -> dict:
    """Seed e22_v2 from live E21 without rewriting E21 or backfilling dividends."""
    if sdir.exists() and (sdir / "config.json").exists():
        cfg = json.loads((sdir / "config.json").read_text())
        if cfg.get("version_id") == VERSION_ID and not cfg.get("allow_recutover"):
            raise RuntimeError(f"{sdir} already initialized as {VERSION_ID}")

    sdir.mkdir(parents=True, exist_ok=True)
    e21_state = json.loads((e21_dir / "portfolio_state.json").read_text())
    seed_date = e21_state.get("last_date")
    seed_nav = float(e21_state.get("last_nav", 0.0))

    state = {
        "cash": float(e21_state["cash"]),
        "positions": {k: float(v) for k, v in e21_state.get("positions", {}).items()},
        "last_date": seed_date,
        "last_nav": seed_nav,
        "dividend_cash_total": 0.0,
        "package": PACKAGE,
        "version_id": VERSION_ID,
        "cutover_from": "forward/e21",
        "cutover_seed_date": seed_date,
        "cutover_note": "Inherited E21 positions/cash; no dividend backfill into prior E21 history",
    }
    (sdir / "portfolio_state.json").write_text(json.dumps(state, indent=2) + "\n")

    # Carry only unfilled E21 orders so Exact T+1 continues on the next session.
    pending_n = 0
    if (e21_dir / "orders.csv").exists():
        orders = pd.read_csv(e21_dir / "orders.csv", dtype={"code": str})
        filled = set()
        if (e21_dir / "fills.csv").exists():
            filled = set(pd.read_csv(e21_dir / "fills.csv").fill_id.astype(str))
        pending = orders[~orders.order_id.astype(str).isin(filled)].copy()
        pending_n = int(len(pending))
        if pending_n:
            pending.to_csv(sdir / "orders.csv", index=False)

    # Cutover seed NAV row (continuity marker — not a rewritten E21 history).
    seed_row = {
        "date": seed_date,
        "nav_e16_e18_e22": seed_nav,
        "cash": state["cash"],
        "pre_financial": None,
        "pre_telecom": None,
        "pre_0050": None,
        "target_l1_gap": None,
        "orders_created": 0,
        "fills_processed": 0,
        "dividend_credit": 0.0,
        "dividend_cash_total": 0.0,
        "row_kind": "CUTOVER_SEED",
    }
    pd.DataFrame([seed_row]).to_csv(sdir / "nav.csv", index=False)

    # Optional: copy last E21 signal as seed diagnostics (weights still sum to 1).
    if (e21_dir / "signals.csv").exists():
        sig = pd.read_csv(e21_dir / "signals.csv")
        last = sig[sig.date.astype(str) == str(seed_date)].tail(1).copy()
        if len(last):
            last = last.iloc[0].to_dict()
            last["e22_dividend_credit"] = 0.0
            last["row_kind"] = "CUTOVER_SEED"
            last["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
            pd.DataFrame([last]).to_csv(sdir / "signals.csv", index=False)

    stamp = datetime.now(timezone.utc).isoformat()
    config = {
        "package": PACKAGE,
        "version_id": VERSION_ID,
        "status": "SOFT_FROZEN",
        "governance_class": "SOFT_FROZEN",
        "approved_at": APPROVED_AT,
        "approval_phrase": APPROVAL_PHRASE,
        "modifies_e21": False,
        "preserves_e21_forever": True,
        "official_script": "scripts/e22_v2_forward_pipeline.py",
        "official_state_dir": str(sdir),
        "market_source": "forward/e21/live_market.csv",
        "dividends": "data/dividend_events/e22_dividend_events.csv",
        "cutover_from": "forward/e21",
        "cutover_seed_date": seed_date,
        "pending_orders_carried": pending_n,
        "prior_versions_readable": [
            "forward/e21/",
            "forward/e22_challenger/",
            "data/dividend_events/e22_dividend_events.csv",
        ],
        "generated_at_utc": stamp,
    }
    (sdir / "config.json").write_text(json.dumps(config, indent=2) + "\n")
    (sdir / "cutover_manifest.json").write_text(
        json.dumps(
            {
                "version_id": VERSION_ID,
                "cutover_at_utc": stamp,
                "seed_date": seed_date,
                "seed_nav": seed_nav,
                "pending_orders_carried": pending_n,
                "dividend_backfill": False,
                "e21_preserved": True,
            },
            indent=2,
        )
        + "\n"
    )

    audit = sdir / "audit_chain.jsonl"
    payload = json.dumps(
        {"date": seed_date, "event": "CUTOVER_SEED", "config": config, "previous_hash": "GENESIS"},
        sort_keys=True,
        default=str,
    )
    h = hashlib.sha256(payload.encode()).hexdigest()
    audit.write_text(
        json.dumps({"date": seed_date, "previous_hash": "GENESIS", "hash": h, "event": "CUTOVER_SEED"})
        + "\n"
    )

    (sdir / "README.md").write_text(
        f"""# E22_v2 Official Forward

**Version:** `{VERSION_ID}`  
**Status:** `SOFT_FROZEN` (approved {APPROVED_AT})

- Official script: `scripts/e22_v2_forward_pipeline.py`
- State: `forward/e22_v2/`
- Mechanism: Exact T+1 + cash dividend credit on `cash_ex_date`
- Cutover seed date: `{seed_date}` (inherited from E21; **no** dividend backfill)
- Preserved forever: `forward/e21/`

## Daily run

```bash
python scripts/e22_v2_forward_pipeline.py
python scripts/e22_v2_qc.py
```
"""
    )
    return config


def process_one_day(
    m: pd.DataFrame,
    sdir: Path,
    capital: float,
    div_map: dict,
    asof: pd.Timestamp,
) -> dict:
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
        else {
            "cash": capital,
            "positions": {},
            "last_date": None,
            "dividend_cash_total": 0.0,
            "package": PACKAGE,
            "version_id": VERSION_ID,
        }
    )
    pos, cash, vals, nav = holdings(state, prices)

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
            fee = gross * (
                BUY_FEE if side == "BUY" else SELL_FEE + (TAX_ETF if o.code == "0050" else TAX_STOCK)
            )
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
        "row_kind": "LIVE",
        **diag,
        "e16_financial": tw.Financial,
        "e16_telecom": tw.Telecom,
        "e16_0050": tw["0050"],
        "e20_financial": e20w.Financial,
        "e20_telecom": e20w.Telecom,
        "e20_0050": e20w["0050"],
        "e22_dividend_credit": day_div,
        "e22_version": VERSION_ID,
    }
    # Replace cutover seed signal for same date if re-running seed day as live
    sig_path = sdir / "signals.csv"
    if sig_path.exists():
        old = pd.read_csv(sig_path)
        if (old.date.astype(str) == latest.date().isoformat()).any() and "row_kind" in old.columns:
            seed_only = old[
                (old.date.astype(str) == latest.date().isoformat()) & (old.row_kind == "CUTOVER_SEED")
            ]
            if len(seed_only) and len(old) == len(seed_only):
                # allow overwrite of sole cutover seed row with first live recompute
                old = old[old.date.astype(str) != latest.date().isoformat()]
                old.to_csv(sig_path, index=False)
    append_immutable(sig_path, signal, "date")

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
        "row_kind": "LIVE",
    }
    nav_path = sdir / "nav.csv"
    if nav_path.exists():
        oldn = pd.read_csv(nav_path)
        if (oldn.date.astype(str) == latest.date().isoformat()).any() and "row_kind" in oldn.columns:
            seed_only = oldn[
                (oldn.date.astype(str) == latest.date().isoformat())
                & (oldn.row_kind == "CUTOVER_SEED")
            ]
            if len(seed_only):
                # Keep cutover seed; do not duplicate same date as LIVE until next session
                if str(state.get("last_date")) == latest.date().isoformat() and not fills and not order_rows:
                    pass
    appended = append_immutable(nav_path, navrow, "date")
    if not appended and nav_path.exists():
        # Idempotent daily rerun
        pass

    state = {
        "cash": cash,
        "positions": pos,
        "last_date": latest.date().isoformat(),
        "last_nav": nav,
        "dividend_cash_total": div_total,
        "package": PACKAGE,
        "version_id": VERSION_ID,
        "cutover_from": state.get("cutover_from", "forward/e21"),
        "cutover_seed_date": state.get("cutover_seed_date"),
    }
    state_path.write_text(json.dumps(state, indent=2) + "\n")

    audit = sdir / "audit_chain.jsonl"
    prev = "GENESIS"
    if audit.exists():
        lines = [x for x in audit.read_text().splitlines() if x.strip()]
        prev = json.loads(lines[-1])["hash"] if lines else prev
        if any(json.loads(x).get("date") == latest.date().isoformat() and json.loads(x).get("event") != "CUTOVER_SEED" for x in lines):
            prev = None
        elif any(json.loads(x).get("date") == latest.date().isoformat() for x in lines):
            # allow first live hash after cutover seed on same calendar date only if new event
            if any(json.loads(x).get("event") == "LIVE" and json.loads(x).get("date") == latest.date().isoformat() for x in lines):
                prev = None
    if prev:
        payload = json.dumps(
            {
                "date": latest.date().isoformat(),
                "event": "LIVE",
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
            f.write(
                json.dumps(
                    {
                        "date": latest.date().isoformat(),
                        "previous_hash": prev,
                        "hash": h,
                        "event": "LIVE",
                    }
                )
                + "\n"
            )

    return {
        "date": latest.date().isoformat(),
        "nav": nav,
        "orders": len(order_rows),
        "fills": len(fills),
        "dividend_credit": day_div,
        "regime": diag["regime"],
        "version_id": VERSION_ID,
    }


def run_qc(sdir: Path) -> dict:
    checks = {}
    sig = pd.read_csv(sdir / "signals.csv")
    nav = pd.read_csv(sdir / "nav.csv")
    checks["signals_unique_date"] = not sig.date.duplicated().any()
    checks["nav_unique_date"] = not nav.date.duplicated().any()
    if "e16_financial" in sig.columns:
        live_sig = sig if "row_kind" not in sig.columns else sig[sig.row_kind != "CUTOVER_SEED"]
        if len(live_sig) == 0:
            live_sig = sig
        checks["weights_sum_one"] = bool(
            ((live_sig[["e16_financial", "e16_telecom", "e16_0050"]].sum(1) - 1).abs() < 1e-8).all()
        )
    checks["nav_positive"] = bool((nav.nav_e16_e18_e22 > 0).all())
    checks["no_negative_cash"] = bool((nav.cash >= -1).all())
    checks["date_monotonic"] = bool(
        pd.to_datetime(sig.date).is_monotonic_increasing
        and pd.to_datetime(nav.date).is_monotonic_increasing
    )
    if (sdir / "orders.csv").exists():
        orders = pd.read_csv(sdir / "orders.csv", dtype={"code": str})
        checks["orders_unique_id"] = not orders.order_id.duplicated().any()
        checks["frozen_financial_universe"] = set(["2880", "2886", "2892", "5880"]).issuperset(
            set(orders.code.astype(str)) - set(["2412", "3045", "4904", "0050"])
        )
        if (sdir / "fills.csv").exists():
            fills = pd.read_csv(sdir / "fills.csv", dtype={"code": str})
            checks["fills_unique_id"] = not fills.fill_id.duplicated().any()
            checks["fills_reference_existing_orders"] = set(fills.fill_id.astype(str)).issubset(
                set(orders.order_id.astype(str))
            )
            fd = pd.to_datetime(fills.fill_date)
            sd = pd.to_datetime(fills.signal_date)
            checks["exact_t1_fills"] = bool((fd > sd).all())
    if (sdir / "audit_chain.jsonl").exists():
        audit = [json.loads(x) for x in (sdir / "audit_chain.jsonl").read_text().splitlines() if x.strip()]
        checks["audit_chain_links"] = all(
            audit[i]["previous_hash"] == audit[i - 1]["hash"] for i in range(1, len(audit))
        )
    cfg_ok = False
    if (sdir / "config.json").exists():
        cfg = json.loads((sdir / "config.json").read_text())
        cfg_ok = cfg.get("version_id") == VERSION_ID and cfg.get("status") == "SOFT_FROZEN"
    checks["config_soft_frozen_v2"] = cfg_ok
    checks["e21_untouched_marker"] = not (sdir / ".." / "e21" / "nav.csv").samefile(sdir / "nav.csv") if (sdir / "nav.csv").exists() else True

    # Verify e21 nav still exists and was not appended with e22 columns as rewrite
    e21_nav = Path("forward/e21/nav.csv")
    checks["e21_ledger_present"] = e21_nav.exists()
    if e21_nav.exists():
        e21cols = set(pd.read_csv(e21_nav, nrows=1).columns)
        checks["e21_not_rewritten_as_e22"] = "nav_e16_e18" in e21cols and "dividend_cash_total" not in e21cols

    status = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "signal_rows": int(len(sig)),
        "nav_rows": int(len(nav)),
        "version_id": VERSION_ID,
        "package": PACKAGE,
        "modifies_e21": False,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (sdir / "qc_status.json").write_text(json.dumps(status, indent=2) + "\n")
    return status


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", default="forward/e21/live_market.csv")
    ap.add_argument("--state-dir", default=DEFAULT_STATE)
    ap.add_argument("--e21-dir", default="forward/e21")
    ap.add_argument("--dividends", default="data/dividend_events/e22_dividend_events.csv")
    ap.add_argument("--capital", type=float, default=CAPITAL)
    ap.add_argument(
        "--init-cutover-from-e21",
        action="store_true",
        help="Seed forward/e22_v2 from E21 state (no dividend backfill)",
    )
    ap.add_argument(
        "--asof",
        default=None,
        help="Process a single as-of date (default: latest complete market date)",
    )
    args = ap.parse_args()
    sdir = Path(args.state_dir)

    if args.init_cutover_from_e21:
        cfg = init_cutover_from_e21(sdir, Path(args.e21_dir))
        qc = run_qc(sdir)
        print(json.dumps({"init": cfg, "qc": qc}, indent=2, default=str))
        if qc["status"] != "PASS":
            raise SystemExit(1)
        return

    if not (sdir / "config.json").exists():
        raise RuntimeError("e22_v2 not initialized; run with --init-cutover-from-e21 first")

    m = pd.read_csv(args.market, dtype={"code": str})
    m.date = pd.to_datetime(m.date)
    m = m.sort_values(["date", "code"])
    div_map = load_div_map(Path(args.dividends))
    asof = pd.Timestamp(args.asof) if args.asof else m.date.max()
    result = process_one_day(m, sdir, args.capital, div_map, asof)
    qc = run_qc(sdir)
    print(json.dumps({"result": result, "qc": qc["status"]}, indent=2, default=str))
    if qc["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
