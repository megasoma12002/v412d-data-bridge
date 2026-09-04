#!/usr/bin/env python3
"""Historical research recompute: E22_v2 (cash-only) vs E22_v2s (formal books).

Does NOT rewrite forward/e21 immutable live ledgers.
Writes side-by-side research artifacts only.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from e50_early_stack_combined_nav import ALL, e16_features, nav_stats, simulate_core
import e22_dividend_accounting as e22div

OUT = Path("repro/e22-v2s-historical-recompute")
REPORT = Path("research/e22/E22_V2S_HISTORICAL_RECOMPUTE.md")
SUMMARY_JSON = Path("research/e22/E22_V2S_HISTORICAL_RECOMPUTE.json")


def calendar_year_stats(nav: pd.DataFrame) -> list[dict]:
    d = nav.copy()
    d["date"] = pd.to_datetime(d["date"])
    d["year"] = d["date"].dt.year
    rows = []
    for year, g in d.groupby("year"):
        if len(g) < 5:
            continue
        start = float(g["nav"].iloc[0])
        end = float(g["nav"].iloc[-1])
        ret = end / start - 1.0 if start > 0 else None
        rows.append(
            {
                "year": int(year),
                "n_days": int(len(g)),
                "start_nav": start,
                "end_nav": end,
                "year_return": ret,
            }
        )
    return rows


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)

    market = pd.read_csv("forward/e21/live_market.csv", dtype={"code": str})
    market["date"] = pd.to_datetime(market["date"])
    required = set(ALL + ["TAIEX"])
    complete = market.groupby("date")["code"].apply(lambda s: required.issubset(set(s)))
    market = market[market["date"].isin(complete[complete].index)].sort_values(["date", "code"])
    dividends = pd.read_csv("data/dividend_events/e22_dividend_events.csv", dtype={"code": str})
    _p, _s, target, regime = e16_features(market)

    specs = [
        ("E16_E18_NO_DIV", dict(apply_e22=False, apply_stock_div=False)),
        ("E22_v2", dict(apply_e22=True, apply_stock_div=False, e22_version=e22div.E22_V2)),
        ("E22_v2s", dict(apply_e22=True, apply_stock_div=True, e22_version=e22div.E22_V2S)),
    ]
    results = {}
    for name, cfg in specs:
        print(f"simulating {name} ...", flush=True)
        nav, fills, meta = simulate_core(market, target, regime, dividends, **cfg)
        stats = nav_stats(nav)
        stats["start_nav"] = float(nav["nav"].iloc[0])
        stats["end_nav"] = float(nav["nav"].iloc[-1])
        nav.to_csv(OUT / "outputs" / f"{name.lower()}_daily_nav.csv", index=False)
        fills.to_csv(OUT / "outputs" / f"{name.lower()}_fills.csv", index=False)
        year_rows = calendar_year_stats(nav)
        pd.DataFrame(year_rows).to_csv(OUT / "outputs" / f"{name.lower()}_by_year.csv", index=False)
        results[name] = {"stats": stats, "meta": meta, "by_year": year_rows}
        print(
            f"  {name}: CAGR={stats['cagr']:.4%} MDD={stats['max_drawdown']:.4%} "
            f"end={stats['end_nav']:.0f} stock_ev={meta.get('stock_div_events')}",
            flush=True,
        )

    a = results["E22_v2"]["stats"]
    b = results["E22_v2s"]["stats"]
    z = results["E16_E18_NO_DIV"]["stats"]

    # year delta table
    y2 = {r["year"]: r for r in results["E22_v2"]["by_year"]}
    ys = {r["year"]: r for r in results["E22_v2s"]["by_year"]}
    year_delta = []
    for y in sorted(set(y2) & set(ys)):
        r2, rs = y2[y], ys[y]
        year_delta.append(
            {
                "year": y,
                "e22_v2_return": r2["year_return"],
                "e22_v2s_return": rs["year_return"],
                "delta_return": (rs["year_return"] or 0) - (r2["year_return"] or 0),
            }
        )
    pd.DataFrame(year_delta).to_csv(OUT / "outputs" / "year_delta_v2s_minus_v2.csv", index=False)

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "E22_V2S_HISTORICAL_RESEARCH_RECOMPUTE",
        "governance": {
            "rewrites_live_forward_e21_ledgers": False,
            "preserved_baseline_label": e22div.E22_V2,
            "formal_books_label": e22div.E22_V2S,
            "signal_price": "adj_close",
            "books_price": "raw_close",
        },
        "variants": results,
        "deltas": {
            "v2s_minus_v2_cagr": (b["cagr"] or 0) - (a["cagr"] or 0),
            "v2s_minus_v2_mdd": (b["max_drawdown"] or 0) - (a["max_drawdown"] or 0),
            "v2s_minus_v2_end_nav": (b["end_nav"] or 0) - (a["end_nav"] or 0),
            "v2_minus_nodiv_cagr": (a["cagr"] or 0) - (z["cagr"] or 0),
            "v2s_minus_nodiv_cagr": (b["cagr"] or 0) - (z["cagr"] or 0),
            "stock_div_events_v2s": results["E22_v2s"]["meta"]["stock_div_events"],
            "stock_div_shares_added_v2s": results["E22_v2s"]["meta"]["stock_div_shares_added"],
        },
        "year_delta_v2s_minus_v2": year_delta,
        "decision": {
            "live_historical_nav": "DO_NOT_REWRITE",
            "research_total_return": "USE_E22_V2S_SIDE_BY_SIDE",
            "published_v2_label": "KEEP_AS_CASH_ONLY_BASELINE",
            "formal_books_figure": "E22_v2s",
        },
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2, default=str) + "\n")

    lines = [
        "# E22_v2s Historical Research Recompute",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        "",
        "**Research only.** Does **not** rewrite `forward/e21/` live ledgers.",
        "",
        "## Purpose",
        "",
        "Recompute full-history early-stack NAV under formal books (E22_v2s) and keep",
        "E22_v2 cash-only as a labeled baseline side-by-side.",
        "",
        "## Method",
        "",
        "- Engine: `scripts/e50_early_stack_combined_nav.py` + `e22_dividend_accounting.py`",
        "- Signals: E16 on `adj_close`",
        "- Books: raw `close`; Exact T+1 fills",
        "- E22_v2: cash on `cash_ex_date` only",
        "- E22_v2s: cash + stock share increase on `stock_ex_date`",
        "",
        "## Results",
        "",
        "| Variant | CAGR | MDD | Start NAV | End NAV | Stock events |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name in ["E16_E18_NO_DIV", "E22_v2", "E22_v2s"]:
        st = results[name]["stats"]
        meta = results[name]["meta"]
        lines.append(
            f"| {name} | {100*(st['cagr'] or 0):.2f}% | {100*(st['max_drawdown'] or 0):.2f}% | "
            f"{st['start_nav']:,.0f} | {st['end_nav']:,.0f} | {meta.get('stock_div_events', 0)} |"
        )
    d = summary["deltas"]
    lines += [
        "",
        "### Deltas (v2s − v2)",
        "",
        f"- CAGR: **{100*d['v2s_minus_v2_cagr']:.2f} pp**",
        f"- MDD: `{100*d['v2s_minus_v2_mdd']:.2f} pp`",
        f"- End NAV: `{d['v2s_minus_v2_end_nav']:,.0f}`",
        f"- Stock events / shares added: `{d['stock_div_events_v2s']}` / `{d['stock_div_shares_added_v2s']:,.1f}`",
        "",
        "## Calendar-year returns",
        "",
        "| Year | E22_v2 | E22_v2s | Δ |",
        "|---:|---:|---:|---:|",
    ]
    for row in year_delta:
        lines.append(
            f"| {row['year']} | {100*(row['e22_v2_return'] or 0):.2f}% | "
            f"{100*(row['e22_v2s_return'] or 0):.2f}% | {100*row['delta_return']:.2f} pp |"
        )
    lines += [
        "",
        "## Decision",
        "",
        f"- Live historical NAV: `{summary['decision']['live_historical_nav']}`",
        f"- Research total return: `{summary['decision']['research_total_return']}`",
        f"- Published v2 label: `{summary['decision']['published_v2_label']}`",
        f"- Formal books figure: `{summary['decision']['formal_books_figure']}`",
        "",
        "## Artifacts",
        "",
        f"- `{OUT}/summary.json`",
        f"- `{OUT}/outputs/`",
        f"- `{SUMMARY_JSON}`",
        "",
    ]
    REPORT.write_text("\n".join(lines) + "\n")
    print(json.dumps({"deltas": d, "decision": summary["decision"]}, indent=2, default=str))
    print(f"wrote {REPORT}", flush=True)


if __name__ == "__main__":
    main()
