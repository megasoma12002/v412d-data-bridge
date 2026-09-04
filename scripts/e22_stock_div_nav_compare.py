#!/usr/bin/env python3
"""Quick cash-only vs stock-share-increase NAV compare (challenger sandbox)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from e50_early_stack_combined_nav import ALL, e16_features, nav_stats, simulate_core

OUT = Path("repro/e22-stock-div-nav-compare")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    market = pd.read_csv("forward/e21/live_market.csv", dtype={"code": str})
    market["date"] = pd.to_datetime(market["date"])
    required = set(ALL + ["TAIEX"])
    complete = market.groupby("date")["code"].apply(lambda s: required.issubset(set(s)))
    market = market[market["date"].isin(complete[complete].index)].sort_values(["date", "code"])
    dividends = pd.read_csv("data/dividend_events/e22_dividend_events.csv", dtype={"code": str})
    _p, _s, target, regime = e16_features(market)

    rows = {}
    for name, stock in [("cash_only", False), ("cash_plus_stock", True)]:
        nav, _fills, meta = simulate_core(
            market,
            target,
            regime,
            dividends,
            apply_e22=True,
            apply_stock_div=stock,
        )
        stats = nav_stats(nav)
        nav.to_csv(OUT / f"{name}_daily_nav.csv", index=False)
        rows[name] = {"stats": stats, "meta": meta}
        print(
            f"{name}: CAGR={stats['cagr']:.4%} MDD={stats['max_drawdown']:.4%} "
            f"stock_events={meta['stock_div_events']} shares+={meta['stock_div_shares_added']}",
            flush=True,
        )

    a, b = rows["cash_only"]["stats"], rows["cash_plus_stock"]["stats"]
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "governance": {
            "label": "EXPERIMENTAL_CHALLENGER",
            "e22_v2_official_still_cash_only": True,
        },
        "unit_note": "stock_dividend FinMind 元/股; shares *= 1 + stock/10 on stock_ex_date",
        "variants": rows,
        "delta_cagr": (b["cagr"] or 0) - (a["cagr"] or 0),
        "delta_mdd": (b["max_drawdown"] or 0) - (a["max_drawdown"] or 0),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
    print(json.dumps({"delta_cagr": summary["delta_cagr"], "delta_mdd": summary["delta_mdd"]}, indent=2))


if __name__ == "__main__":
    main()
