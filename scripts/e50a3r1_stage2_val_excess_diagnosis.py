#!/usr/bin/env python3
"""Stage-2 diagnosis: why C2/C4/C8 validation excess is unstable.

Read-only vs locked configs. May inspect 2019-2022 held-out artifacts for
diagnosis only. Does NOT retune C2/C4/C8 and does not promote anything.

EXPERIMENTAL research tooling. Does not modify E16/E18/E22/E44/E45.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl

REFS = {
    "C2": {
        "top_k": 20, "rebalance_every": 42, "exit_multiple": 2.5,
        "neutralization": "NONE", "industry_cap": 5, "min_hold_cycles": 0,
        "liquidity_floor": 20_000_000.0, "replace_rank_gap": 0,
    },
    "C4": {
        "top_k": 22, "rebalance_every": 42, "exit_multiple": 2.25,
        "neutralization": "NONE", "industry_cap": 5, "min_hold_cycles": 0,
        "liquidity_floor": 20_000_000.0, "replace_rank_gap": 5,
    },
    "C8": {
        "top_k": 22, "rebalance_every": 42, "exit_multiple": 2.25,
        "neutralization": "NONE", "industry_cap": 5, "min_hold_cycles": 0,
        "liquidity_floor": 20_000_000.0, "replace_rank_gap": 10,
    },
}


def load_window(out: Path, tag: str, window: str):
    nav = pl.read_csv(out / "outputs" / f"{tag}_{window}_daily_nav.csv").with_columns(
        pl.col("date").str.to_date()
    )
    proxy = pl.read_csv(out / "outputs" / f"{tag}_{window}_market_proxy_nav.csv").with_columns(
        pl.col("date").str.to_date()
    )
    trades = pl.read_csv(out / "outputs" / f"{tag}_{window}_trades.csv").with_columns(
        pl.col("signal_date").str.to_date(),
        pl.col("execution_date").str.to_date(),
    )
    return nav, proxy, trades


def excess_frame(nav: pl.DataFrame, proxy: pl.DataFrame) -> pl.DataFrame:
    a = nav.select("date", pl.col("nav").pct_change().alias("strategy"), "turnover", "cumulative_cost", "positions")
    b = proxy.select("date", pl.col("nav").pct_change().alias("benchmark"))
    return a.join(b, on="date", how="inner").drop_nulls().with_columns(
        (pl.col("strategy") - pl.col("benchmark")).alias("excess"),
        pl.col("date").dt.year().alias("year"),
        pl.col("date").dt.month().alias("month"),
    )


def diagnose_one(tag: str, nav, proxy, trades, panel: pl.DataFrame | None) -> dict:
    x = excess_frame(nav, proxy)
    rets = x["excess"].to_numpy()
    # Yearly excess / strategy / turnover
    yearly = []
    for (year,), g in x.group_by("year", maintain_order=True):
        y = int(year)
        gg = g.sort("date")
        # reconstruct year nav from strategy returns
        s = (1.0 + gg["strategy"]).cum_prod()
        b = (1.0 + gg["benchmark"]).cum_prod()
        yearly.append({
            "year": y,
            "strategy_return": float(s[-1] - 1.0),
            "benchmark_return": float(b[-1] - 1.0),
            "excess_return_approx": float(s[-1] - b[-1]),
            "mean_daily_excess": float(gg["excess"].mean()),
            "daily_excess_hit_rate": float((gg["excess"] > 0).mean()),
            "avg_daily_turnover": float(gg["turnover"].mean()),
            "cost_delta": float(gg["cumulative_cost"][-1] - gg["cumulative_cost"][0]),
            "avg_positions": float(gg["positions"].mean()),
            "days": gg.height,
        })

    # Worst excess months
    monthly = (
        x.group_by(["year", "month"]).agg(
            pl.col("excess").sum().alias("sum_excess"),
            pl.col("strategy").sum().alias("sum_strategy"),
            pl.col("turnover").mean().alias("avg_turnover"),
            pl.len().alias("days"),
        ).sort("sum_excess")
    )
    worst_months = monthly.head(8).to_dicts()
    best_months = monthly.sort("sum_excess", descending=True).head(5).to_dicts()

    # Drawdown overlap: when strategy in deep DD, is excess also negative?
    values = nav["nav"].to_numpy()
    peak = np.maximum.accumulate(values)
    dd = values / peak - 1.0
    nav2 = nav.with_columns(pl.Series("drawdown", dd))
    joined = x.join(nav2.select("date", "drawdown"), on="date", how="left")
    deep = joined.filter(pl.col("drawdown") <= -0.10)
    mild = joined.filter(pl.col("drawdown") > -0.05)

    # Trade / crowding diagnostics
    buys = trades.filter(pl.col("side") == "BUY").with_columns(pl.col("code").cast(pl.String))
    names = trades.with_columns(pl.col("code").cast(pl.String)).group_by("code").agg(
        pl.len().alias("n_trades"),
        pl.col("gross_value").sum().alias("gross"),
        pl.col("cost").sum().alias("cost"),
    ).sort("gross", descending=True)
    top10_share = float(names.head(10)["gross"].sum() / names["gross"].sum()) if names.height else None

    industry_conc = None
    if panel is not None and buys.height:
        # industry of buy signals
        ind = (
            buys.join(
                panel.select("date", "code", "industry_category").rename({"date": "signal_date"}),
                on=["signal_date", "code"],
                how="left",
            )
            .group_by("industry_category")
            .agg(pl.col("gross_value").sum().alias("gross"), pl.len().alias("n"))
            .sort("gross", descending=True)
        )
        total = float(ind["gross"].sum()) or 1.0
        industry_conc = {
            "top_industry": ind["industry_category"][0] if ind.height else None,
            "top_industry_gross_share": float(ind["gross"][0] / total) if ind.height else None,
            "top3_gross_share": float(ind.head(3)["gross"].sum() / total) if ind.height else None,
            "n_industries": ind.height,
            "top5": ind.head(5).to_dicts(),
        }

    return {
        "reference": tag,
        "days": x.height,
        "mean_daily_excess": float(np.mean(rets)),
        "daily_excess_hit_rate": float(np.mean(rets > 0)),
        "excess_vol": float(np.std(rets, ddof=1)),
        "total_cost": float(nav["cumulative_cost"][-1]),
        "mean_turnover": float(nav["turnover"].mean()),
        "max_drawdown": float(np.min(dd)),
        "yearly": yearly,
        "worst_excess_months": worst_months,
        "best_excess_months": best_months,
        "deep_dd_le_10pct": {
            "days": deep.height,
            "mean_excess": float(deep["excess"].mean()) if deep.height else None,
            "hit_rate": float((deep["excess"] > 0).mean()) if deep.height else None,
        },
        "mild_dd_gt_neg5pct": {
            "days": mild.height,
            "mean_excess": float(mild["excess"].mean()) if mild.height else None,
            "hit_rate": float((mild["excess"] > 0).mean()) if mild.height else None,
        },
        "crowding": {
            "unique_names_traded": names.height,
            "top10_gross_share": top10_share,
            "trade_count": trades.height,
            "buy_count": buys.height,
        },
        "industry_concentration": industry_conc,
        "no_retune": True,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--panel", type=Path, default=None)
    args = ap.parse_args()
    out = args.out
    panel = pl.read_parquet(args.panel).select("date", "code", "industry_category") if args.panel else None

    reports = {}
    for tag in REFS:
        nav, proxy, trades = load_window(out, tag.lower(), "validation_2019_2022")
        reports[tag] = diagnose_one(tag, nav, proxy, trades, panel)
        # also sealed summary yearly for context (diagnosis allowed)
        snav, sproxy, strades = load_window(out, tag.lower(), "sealed_2023_latest")
        reports[tag]["sealed_yearly"] = diagnose_one(tag + "_SEALED", snav, sproxy, strades, panel)["yearly"]

    # Cross-reference synthesis
    synthesis = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "STAGE2_VAL_EXCESS_DIAGNOSIS",
        "references_frozen": REFS,
        "no_retune": True,
        "no_promotion": True,
        "reports": reports,
        "findings": [],
    }

    # Identify common weak years
    weak = {}
    for tag, rep in reports.items():
        for y in rep["yearly"]:
            weak.setdefault(y["year"], []).append((tag, y["mean_daily_excess"], y["excess_return_approx"]))
    common_weak_years = []
    for year, xs in sorted(weak.items()):
        if all(v[1] < 0 for v in xs):
            common_weak_years.append({"year": year, "by_ref": xs})

    synthesis["findings"].append({
        "item": "common_negative_excess_years_validation",
        "years": common_weak_years,
        "note": "Years where all C2/C4/C8 had negative mean daily excess vs PIT proxy.",
    })
    # Cost vs excess
    cost_note = []
    for tag, rep in reports.items():
        cost_note.append({
            "ref": tag,
            "total_cost": rep["total_cost"],
            "mean_turnover": rep["mean_turnover"],
            "mean_daily_excess": rep["mean_daily_excess"],
            "top10_gross_share": rep["crowding"]["top10_gross_share"],
            "top_industry_share": (rep["industry_concentration"] or {}).get("top_industry_gross_share"),
        })
    synthesis["findings"].append({"item": "cost_crowding_snapshot", "rows": cost_note})
    synthesis["findings"].append({
        "item": "drawdown_state_dependence",
        "rows": {
            tag: {
                "deep_dd_mean_excess": rep["deep_dd_le_10pct"]["mean_excess"],
                "mild_dd_mean_excess": rep["mild_dd_gt_neg5pct"]["mean_excess"],
            }
            for tag, rep in reports.items()
        },
        "note": "If deep-drawdown excess << mild, validation failure is crisis/regime-linked, not only average turnover.",
    })
    synthesis["research_implication"] = (
        "Do not retune C2/C4/C8. Next stage should change the alpha/model hypothesis on OOF "
        "(feature family / regime / lambda), because portfolio-rule variants that already clear "
        "validation turnover still fail excess bootstrap in the same weak years."
    )

    (out / "reports" / "stage2_val_excess_diagnosis.json").write_text(
        json.dumps(synthesis, indent=2, default=str) + "\n"
    )

    # Markdown
    lines = [
        "# Stage-2 Validation Excess Diagnosis (C2 / C4 / C8)",
        "",
        "Diagnosis only. **No retune. No promotion.**",
        "",
        "## Purpose",
        "",
        "Explain why references that pass validation turnover still fail bootstrap ≥ 0.70 on 2019–2022.",
        "",
    ]
    for tag, rep in reports.items():
        lines += [
            f"## {tag}",
            "",
            f"- Mean daily excess: `{rep['mean_daily_excess']:.6f}`",
            f"- Excess hit rate: `{rep['daily_excess_hit_rate']:.3f}`",
            f"- Mean turnover: `{100*rep['mean_turnover']:.2f}%`, total cost `{rep['total_cost']:.4f}`",
            f"- Max DD: `{100*rep['max_drawdown']:.2f}%`",
            f"- Top10 name gross share: `{rep['crowding']['top10_gross_share']:.3f}`",
            f"- Industry top share: `{(rep['industry_concentration'] or {}).get('top_industry_gross_share')}` "
            f"({(rep['industry_concentration'] or {}).get('top_industry')})",
            "",
            "| Year | Strat | Proxy | Excess≈ | Mean d.excess | Hit | Turnover | CostΔ |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for y in rep["yearly"]:
            lines.append(
                f"| {y['year']} | {100*y['strategy_return']:.1f}% | {100*y['benchmark_return']:.1f}% | "
                f"{100*y['excess_return_approx']:.1f}% | {y['mean_daily_excess']:.5f} | "
                f"{100*y['daily_excess_hit_rate']:.1f}% | {100*y['avg_daily_turnover']:.2f}% | {y['cost_delta']:.3f} |"
            )
        lines += ["", "Worst excess months:", ""]
        for m in rep["worst_excess_months"][:5]:
            lines.append(f"- {m['year']}-{int(m['month']):02d}: sum_excess={m['sum_excess']:.4f}, turnover={100*m['avg_turnover']:.2f}%")
        lines.append("")
    lines += [
        "## Synthesis",
        "",
        synthesis["research_implication"],
        "",
        "Artifact: `reports/stage2_val_excess_diagnosis.json`",
        "",
    ]
    (out / "E50-A3-R1_STAGE2_VAL_EXCESS_DIAGNOSIS.md").write_text("\n".join(lines))
    print(json.dumps({
        "common_weak_years": common_weak_years,
        "cost_crowding": cost_note,
        "drawdown_state": synthesis["findings"][2]["rows"],
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
