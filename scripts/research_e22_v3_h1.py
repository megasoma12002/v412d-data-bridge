#!/usr/bin/env python3
"""E22_v3 H1 sandbox — payment_date vs cash_ex_date credit (challenger only).

Prereq: e22_dividend_events.csv now has complete cash_payment_date (Yahoo backfill).
Baseline preserved: E22_v2_CASH_EX_OFFICIAL_PATH / forward/e22_v2/

Does not edit SOFT_FROZEN ledgers. Does not promote.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e50_early_stack_combined_nav as core
import research_reopen_round2 as r2

OUT_DEFAULT = Path("repro/e22-v3-h1-20260904")


def coverage(div: pd.DataFrame) -> dict:
    d = div.copy()
    d["cash_dividend"] = pd.to_numeric(d["cash_dividend"], errors="coerce")
    cash = d[d["cash_dividend"] > 0]
    pay_ok = cash["cash_payment_date"].fillna("").astype(str).str.strip().ne("")
    return {
        "n_cash_events": int(len(cash)),
        "n_with_payment_date": int(pay_ok.sum()),
        "frac_with_payment_date": float(pay_ok.mean()) if len(cash) else 0.0,
        "n_missing_payment_date": int((~pay_ok).sum()),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", default="forward/e21/live_market.csv")
    ap.add_argument("--dividends", default="data/dividend_events/e22_dividend_events.csv")
    ap.add_argument("--out", default=str(OUT_DEFAULT))
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    market = pd.read_csv(args.market, dtype={"code": str})
    market["date"] = pd.to_datetime(market["date"])
    dividends = pd.read_csv(args.dividends, dtype={"code": str})
    cov = coverage(dividends)
    print(json.dumps({"coverage": cov}, ensure_ascii=False), flush=True)
    if cov["frac_with_payment_date"] < 0.99:
        raise SystemExit("H1 requires near-complete cash_payment_date coverage")

    _, _, target, regime = core.e16_features(market)

    books = {}
    # Control + H1 primary pair + H2 tax grid (≤3 pts, pre-registered)
    configs = [
        ("NO_DIV", dict(apply_e22=False)),
        ("EX_DATE_TAX0", dict(apply_e22=True, div_credit_on="cash_ex_date", div_tax_haircut=0.0)),
        ("PAY_DATE_TAX0", dict(apply_e22=True, div_credit_on="cash_payment_date", div_tax_haircut=0.0)),
        ("EX_DATE_TAX10", dict(apply_e22=True, div_credit_on="cash_ex_date", div_tax_haircut=0.10)),
        ("PAY_DATE_TAX10", dict(apply_e22=True, div_credit_on="cash_payment_date", div_tax_haircut=0.10)),
        ("EX_DATE_TAX20", dict(apply_e22=True, div_credit_on="cash_ex_date", div_tax_haircut=0.20)),
    ]

    for name, cfg in configs:
        print(f"H1 run {name} ...", flush=True)
        apply = cfg.pop("apply_e22")
        nav, meta = r2.simulate_core_flex(
            market, target, regime, dividends, apply_e22=apply, **cfg
        )
        stats = r2.nav_stats(nav.set_index(pd.to_datetime(nav["date"]))["nav"])
        books[name] = {"stats": stats, "meta": meta}
        nav.to_csv(out / f"{name}_nav.csv", index=False)

    ex = books["EX_DATE_TAX0"]["stats"]
    pay = books["PAY_DATE_TAX0"]["stats"]
    # Pre-registered bar (same as Round-2): material util lift without worse MDD
    util_eps = 0.002
    mdd_eps = 0.005
    pay_beats = (
        pay["util"] is not None
        and ex["util"] is not None
        and pay["util"] > ex["util"] + util_eps
        and abs(pay["mdd"]) <= abs(ex["mdd"]) + mdd_eps
    )
    exact_ok = all(books[k]["meta"]["exact_t1_ok"] for k in books)

    ranking = sorted(
        ((k, v["stats"]["util"]) for k, v in books.items() if v["stats"]["util"] is not None),
        key=lambda x: x[1],
        reverse=True,
    )

    if pay_beats:
        decision = "H1_PAY_DATE_INTERESTING_CONTINUE_SANDBOX"
        stance = "Challenger payment-date credit clears pre-registered bar vs ex-date; still NO auto-promote."
    else:
        decision = "KEEP_E22_V2_EX_DATE_BASELINE"
        stance = "With complete payment dates, payment-date credit does not beat ex-date on util+MDD bar; keep E22_v2."

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "package": "e22_v3_h1",
        "baseline": "E22_v2_CASH_EX_OFFICIAL_PATH",
        "hypothesis": "H1_credit_on_payment_date_vs_ex_date",
        "market": args.market,
        "dividends": args.dividends,
        "coverage": cov,
        "decision_bar": {"util_eps": util_eps, "mdd_eps": mdd_eps},
        "pay_vs_ex": {
            "pay_cagr": pay["cagr"],
            "ex_cagr": ex["cagr"],
            "pay_mdd": pay["mdd"],
            "ex_mdd": ex["mdd"],
            "pay_util": pay["util"],
            "ex_util": ex["util"],
            "delta_util": (pay["util"] - ex["util"]) if pay["util"] is not None and ex["util"] is not None else None,
            "delta_cagr": (pay["cagr"] - ex["cagr"]) if pay["cagr"] is not None and ex["cagr"] is not None else None,
            "pay_beats_ex": pay_beats,
            "pay_div_cash_total": books["PAY_DATE_TAX0"]["meta"]["dividend_cash_total"],
            "ex_div_cash_total": books["EX_DATE_TAX0"]["meta"]["dividend_cash_total"],
        },
        "util_ranking": ranking,
        "books": {
            k: {**v["stats"], **{f"meta_{mk}": mv for mk, mv in v["meta"].items()}}
            for k, v in books.items()
        },
        "exact_t1_all_ok": exact_ok,
        "decision": decision,
        "stance": stance,
        "promotion": False,
        "modifies_e22_v2": False,
    }
    (out / "e22_v3_h1_report.json").write_text(json.dumps(report, indent=2, default=str) + "\n")

    md = f"""# E22_v3 H1 — Payment Date vs Ex Date

Date: **{datetime.now(timezone.utc).date().isoformat()}**  
Baseline: **`E22_v2_CASH_EX_OFFICIAL_PATH`** (unchanged)  
Sandbox: `{out}`

## Coverage

| Metric | Value |
|---|---|
| Cash events | {cov['n_cash_events']} |
| With payment date | {cov['n_with_payment_date']} ({cov['frac_with_payment_date']:.1%}) |
| Missing | {cov['n_missing_payment_date']} |

## H1 result (TAX0)

| Book | CAGR | MDD | Util |
|---|---:|---:|---:|
| EX_DATE (v2 rule) | {ex['cagr']:.4%} | {ex['mdd']:.4%} | {ex['util']:.6f} |
| PAY_DATE (H1) | {pay['cagr']:.4%} | {pay['mdd']:.4%} | {pay['util']:.6f} |
| Δ (pay − ex) | {(pay['cagr']-ex['cagr']):.4%} | | {(pay['util']-ex['util']):.6f} |

Pre-registered bar: util lift > **{util_eps}** and MDD not worse by > **{mdd_eps}**.  
`pay_beats_ex` = **{pay_beats}**  
Exact T+1 all books: **{exact_ok}**

## Decision

**`{decision}`**

{stance}

- Promotion: **False** (needs explicit approval even if interesting)
- Official path remains ex-date credit under `forward/e22_v2/`
"""
    (out / "E22_V3_H1_DECISION.md").write_text(md)
    print(json.dumps({"decision": decision, "pay_beats_ex": pay_beats, "delta_util": report["pay_vs_ex"]["delta_util"]}, indent=2))


if __name__ == "__main__":
    main()
