#!/usr/bin/env python3
"""Deep 2021–2022 validation excess autopsy for C2/C4/C8.

Diagnosis only — may inspect held-out years. Does NOT retune locked configs.
EXPERIMENTAL. Does not modify E16/E18/E22/E44/E45.
"""
from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl

REFS = ["C2", "C4", "C8"]
WEAK_YEARS = {2021, 2022}


def load(out: Path, tag: str):
    nav = pl.read_csv(out / "outputs" / f"{tag}_validation_2019_2022_daily_nav.csv").with_columns(
        pl.col("date").str.to_date()
    )
    proxy = pl.read_csv(out / "outputs" / f"{tag}_validation_2019_2022_market_proxy_nav.csv").with_columns(
        pl.col("date").str.to_date()
    )
    trades = pl.read_csv(out / "outputs" / f"{tag}_validation_2019_2022_trades.csv").with_columns(
        pl.col("signal_date").str.to_date(),
        pl.col("execution_date").str.to_date(),
        pl.col("code").cast(pl.String),
    )
    return nav, proxy, trades


def excess_daily(nav: pl.DataFrame, proxy: pl.DataFrame) -> pl.DataFrame:
    a = nav.select(
        "date",
        pl.col("nav").pct_change().alias("strategy"),
        "turnover",
        "cumulative_cost",
        "positions",
        "nav",
    )
    b = proxy.select("date", pl.col("nav").pct_change().alias("benchmark"), pl.col("nav").alias("proxy_nav"))
    x = a.join(b, on="date", how="inner").drop_nulls()
    values = x["nav"].to_numpy()
    peak = np.maximum.accumulate(values)
    return x.with_columns(
        (pl.col("strategy") - pl.col("benchmark")).alias("excess"),
        pl.Series("drawdown", values / peak - 1.0),
        pl.col("date").dt.year().alias("year"),
        pl.col("date").dt.month().alias("month"),
    )


def autopsy_ref(tag: str, nav, proxy, trades, panel: pl.DataFrame, daily_mkt: pl.DataFrame) -> dict:
    x = excess_daily(nav, proxy).join(daily_mkt, on="date", how="left")
    weak = x.filter(pl.col("year").is_in(list(WEAK_YEARS)))
    strong = x.filter(~pl.col("year").is_in(list(WEAK_YEARS)))

    # Monthly decomposition in weak years
    monthly = (
        weak.group_by(["year", "month"]).agg(
            pl.col("excess").sum().alias("sum_excess"),
            pl.col("strategy").sum().alias("sum_strategy"),
            pl.col("benchmark").sum().alias("sum_benchmark"),
            pl.col("turnover").mean().alias("avg_turnover"),
            pl.col("positions").mean().alias("avg_positions"),
            pl.col("drawdown").min().alias("min_drawdown"),
            pl.col("breadth_63d").mean().alias("avg_breadth_63d"),
            pl.col("market_median_mom_63d").mean().alias("avg_mkt_mom"),
            pl.col("alpha_regime_baseline").mode().first().alias("modal_regime"),
            pl.len().alias("days"),
        ).sort(["year", "month"])
    )

    # Regime-conditioned excess in weak vs strong years
    def regime_stats(df: pl.DataFrame) -> dict:
        out = {}
        for reg in ["RISK_ON", "RISK_OFF"]:
            g = df.filter(pl.col("alpha_regime_baseline") == reg)
            out[reg] = {
                "days": g.height,
                "mean_excess": float(g["excess"].mean()) if g.height else None,
                "hit_rate": float((g["excess"] > 0).mean()) if g.height else None,
                "avg_turnover": float(g["turnover"].mean()) if g.height else None,
            }
        return out

    # Trades in weak years: industry / names
    weak_trades = trades.filter(pl.col("signal_date").dt.year().is_in(list(WEAK_YEARS)))
    buys = weak_trades.filter(pl.col("side") == "BUY")
    sells = weak_trades.filter(pl.col("side") == "SELL")
    ind = (
        buys.join(
            panel.select("date", "code", "industry_category").rename({"date": "signal_date"}),
            on=["signal_date", "code"], how="left",
        )
        .group_by("industry_category")
        .agg(pl.col("gross_value").sum().alias("gross"), pl.len().alias("n"))
        .sort("gross", descending=True)
    )
    total_g = float(ind["gross"].sum()) or 1.0

    # Names with largest sell gross in weak years (proxy for exits / losers rotated)
    sell_names = (
        sells.group_by("code").agg(pl.col("gross_value").sum().alias("gross"), pl.len().alias("n"))
        .sort("gross", descending=True).head(15).to_dicts()
    )
    buy_names = (
        buys.group_by("code").agg(pl.col("gross_value").sum().alias("gross"), pl.len().alias("n"))
        .sort("gross", descending=True).head(15).to_dicts()
    )

    # Cost intensity: weak vs other
    def cost_delta(df):
        if df.height < 2:
            return 0.0
        return float(df["cumulative_cost"][-1] - df["cumulative_cost"][0])

    # Correlate daily excess with breadth / mom within weak years
    def corr(a, b):
        aa = a.to_numpy(); bb = b.to_numpy()
        m = np.isfinite(aa) & np.isfinite(bb)
        if m.sum() < 30:
            return None
        return float(np.corrcoef(aa[m], bb[m])[0, 1])

    return {
        "reference": tag,
        "weak_years": sorted(WEAK_YEARS),
        "weak_vs_other": {
            "weak_mean_excess": float(weak["excess"].mean()),
            "other_mean_excess": float(strong["excess"].mean()),
            "weak_hit_rate": float((weak["excess"] > 0).mean()),
            "other_hit_rate": float((strong["excess"] > 0).mean()),
            "weak_avg_turnover": float(weak["turnover"].mean()),
            "other_avg_turnover": float(strong["turnover"].mean()),
            "weak_cost_delta": cost_delta(weak.sort("date")),
            "other_cost_delta": cost_delta(strong.sort("date")),
            "weak_min_drawdown": float(weak["drawdown"].min()),
            "other_min_drawdown": float(strong["drawdown"].min()),
        },
        "regime_conditioned": {
            "weak_years": regime_stats(weak),
            "other_years": regime_stats(strong),
        },
        "monthly_weak_years": monthly.to_dicts(),
        "worst_3_months": monthly.sort("sum_excess").head(3).to_dicts(),
        "corr_weak_excess_vs": {
            "breadth_63d": corr(weak["excess"], weak["breadth_63d"]),
            "market_median_mom_63d": corr(weak["excess"], weak["market_median_mom_63d"]),
            "turnover": corr(weak["excess"], weak["turnover"]),
            "drawdown": corr(weak["excess"], weak["drawdown"]),
        },
        "industry_buys_weak": {
            "top5": [
                {**r, "share": float(r["gross"]) / total_g} for r in ind.head(5).to_dicts()
            ],
            "top_share": float(ind["gross"][0]) / total_g if ind.height else None,
            "n_industries": ind.height,
        },
        "top_buy_names_weak": buy_names,
        "top_sell_names_weak": sell_names,
        "trade_counts_weak": {"buys": buys.height, "sells": sells.height},
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--panel", type=Path, required=True)
    args = ap.parse_args()
    out = args.out
    panel = pl.read_parquet(args.panel).select(
        "date", "code", "industry_category", "mom_21d", "mom_63d", "vol_60d"
    ).with_columns(pl.col("code").cast(pl.String))

    # Baseline regime features (same definition as r1.add_regime)
    daily_mkt = (
        panel.group_by("date").agg(
            (pl.col("mom_63d") > 0).mean().alias("breadth_63d"),
            (pl.col("mom_21d") > 0).mean().alias("breadth_21d"),
            pl.col("mom_63d").median().alias("market_median_mom_63d"),
            pl.col("vol_60d").median().alias("market_median_vol_60d"),
        ).with_columns(
            pl.when((pl.col("breadth_63d") >= 0.50) & (pl.col("market_median_mom_63d") >= 0))
            .then(pl.lit("RISK_ON")).otherwise(pl.lit("RISK_OFF")).alias("alpha_regime_baseline")
        )
    )

    reports = {}
    for tag in REFS:
        nav, proxy, trades = load(out, tag.lower())
        reports[tag] = autopsy_ref(tag, nav, proxy, trades, panel, daily_mkt)

    # Cross-ref: months where all three had negative sum excess
    months = {}
    for tag, rep in reports.items():
        for m in rep["monthly_weak_years"]:
            key = (m["year"], m["month"])
            months.setdefault(key, []).append((tag, m["sum_excess"], m["avg_turnover"], m.get("modal_regime")))
    common_bad = []
    for key, xs in sorted(months.items()):
        if len(xs) == 3 and all(v[1] < 0 for v in xs):
            common_bad.append({"year": key[0], "month": key[1], "by_ref": xs})

    synthesis = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "STAGE3_2021_2022_EXCESS_AUTOPSY",
        "no_retune": True,
        "references": REFS,
        "reports": reports,
        "common_negative_excess_months_all_refs": common_bad,
        "headline_findings": [],
        "research_implication": (
            "2021–2022 excess failure is shared across C2/C4/C8 and concentrated in specific months; "
            "portfolio micro-differences do not remove it. Next leverage should be new alpha features / "
            "regime definitions selected on OOF, not retuning these locks."
        ),
    }

    # Headline bullets derived from C4 (best bootstrap among refs)
    c4 = reports["C4"]["weak_vs_other"]
    synthesis["headline_findings"] = [
        f"C4 weak-year mean daily excess {c4['weak_mean_excess']:.6f} vs other-years {c4['other_mean_excess']:.6f}",
        f"C4 weak-year turnover {c4['weak_avg_turnover']:.4f} vs other {c4['other_avg_turnover']:.4f}",
        f"Common negative-excess months across C2/C4/C8: {len(common_bad)}",
        f"C4 weak-year RISK_ON excess={reports['C4']['regime_conditioned']['weak_years']['RISK_ON']['mean_excess']}, "
        f"RISK_OFF={reports['C4']['regime_conditioned']['weak_years']['RISK_OFF']['mean_excess']}",
    ]

    (out / "reports" / "stage3_2021_2022_excess_autopsy.json").write_text(
        json.dumps(synthesis, indent=2, default=str) + "\n"
    )

    lines = [
        "# Stage-3 Deep Autopsy: 2021–2022 Validation Excess",
        "",
        "Diagnosis only for **C2 / C4 / C8**. **No retune. No promotion.**",
        "",
        "## Headlines",
        "",
    ]
    for h in synthesis["headline_findings"]:
        lines.append(f"- {h}")
    lines += ["", "## Common bad months (all three refs negative excess)", ""]
    for m in common_bad:
        lines.append(f"- {m['year']}-{int(m['month']):02d}: " + ", ".join(
            f"{t}={v:.4f}" for t, v, _, _ in m["by_ref"]
        ))
    for tag, rep in reports.items():
        w = rep["weak_vs_other"]
        lines += [
            f"## {tag}",
            "",
            f"| | 2021–2022 | 2019–2020 |",
            f"|---|---:|---:|",
            f"| Mean daily excess | {w['weak_mean_excess']:.6f} | {w['other_mean_excess']:.6f} |",
            f"| Hit rate | {100*w['weak_hit_rate']:.1f}% | {100*w['other_hit_rate']:.1f}% |",
            f"| Avg turnover | {100*w['weak_avg_turnover']:.2f}% | {100*w['other_avg_turnover']:.2f}% |",
            f"| Cost Δ | {w['weak_cost_delta']:.4f} | {w['other_cost_delta']:.4f} |",
            f"| Min DD | {100*w['weak_min_drawdown']:.2f}% | {100*w['other_min_drawdown']:.2f}% |",
            "",
            "Regime split (weak years):",
            "",
        ]
        for reg, st in rep["regime_conditioned"]["weak_years"].items():
            lines.append(
                f"- {reg}: days={st['days']}, mean_excess={st['mean_excess']}, "
                f"hit={st['hit_rate']}, turnover={st['avg_turnover']}"
            )
        lines += ["", "Corr(excess, ·) in weak years:", ""]
        for k, v in rep["corr_weak_excess_vs"].items():
            lines.append(f"- {k}: {v}")
        lines += ["", "Top industries (buy gross, weak years):", ""]
        for r in rep["industry_buys_weak"]["top5"]:
            lines.append(f"- {r['industry_category']}: share={r['share']:.3f}, n={r['n']}")
        lines.append("")
    lines += [
        "## Implication",
        "",
        synthesis["research_implication"],
        "",
        "Artifact: `reports/stage3_2021_2022_excess_autopsy.json`",
        "",
    ]
    (out / "E50-A3-R1_STAGE3_2021_2022_AUTOPSY.md").write_text("\n".join(lines))
    print(json.dumps({
        "common_bad_months": len(common_bad),
        "headlines": synthesis["headline_findings"],
        "c4_weak_vs_other": c4,
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
