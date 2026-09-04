#!/usr/bin/env python3
"""Stage-4A: OOF screen of atomic (non-family-score) feature sets.

Selection: 2011–2018 OOF only.
Portfolio wrapper FIXED to C4. Regime FIXED to baseline BREADTH (via r1.add_regime).
Mode FIXED to BREADTH_REGIME, λ=1.0 (Stage-2 showed λ nearly inert; GLOBAL collapses).

Does not retune C2/C4/C8. Does not modify E16/E18/E22/E44/E45.
Does not re-screen family-score recombinations or PRICE8 (already Stage-2/3).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e50a3_train_exact_open as a3
import e50a3r1_repair as r1
from e50a3r1_turnover_diagnosis import evaluate_cfg

FIXED_PORTFOLIO = {
    "family": "FIXED_C4_WRAPPER",
    "top_k": 22,
    "rebalance_every": 42,
    "exit_multiple": 2.25,
    "neutralization": "NONE",
    "industry_cap": 5,
    "min_hold_cycles": 0,
    "liquidity_floor": 20_000_000.0,
    "replace_rank_gap": 5,
}

# Atomic / hybrid feature sets beyond family-score recombinations and full PRICE8.
ATOMIC_FEATURES: dict[str, list[str]] = {
    "TECH2": ["momentum_family_score", "defensive_family_score"],  # baseline
    "MOM3": ["pct_mom_12_1", "pct_mom_63d", "pct_mom_126d"],
    "DEF3": ["pct_vol_60d", "pct_downside_vol_60d", "pct_drawdown_63d"],
    "QUAL4": ["pct_roa_ttm", "pct_roe_ttm", "pct_cfo_to_assets", "pct_accruals_to_assets"],
    "VALUE3": ["pct_book_to_price_proxy", "pct_earnings_yield_proxy", "pct_sales_yield_proxy"],
    "REV3": ["pct_monthly_revenue_yoy", "pct_revenue_3m_yoy", "pct_revenue_yoy_acceleration"],
    "GROW3": ["pct_revenue_growth_yoy", "pct_net_income_growth_yoy", "pct_asset_growth_yoy"],
    "MOM_QUAL": ["pct_mom_12_1", "pct_mom_63d", "pct_roa_ttm", "pct_cfo_to_assets"],
    "MOM_VALUE": ["pct_mom_12_1", "pct_mom_63d", "pct_book_to_price_proxy", "pct_earnings_yield_proxy"],
    "MOM_REV": ["pct_mom_12_1", "pct_mom_63d", "pct_monthly_revenue_yoy", "pct_revenue_yoy_acceleration"],
    "QUAL_VALUE": [
        "pct_roa_ttm", "pct_cfo_to_assets",
        "pct_book_to_price_proxy", "pct_earnings_yield_proxy",
    ],
    "REV_QUAL": [
        "pct_monthly_revenue_yoy", "pct_revenue_yoy_acceleration",
        "pct_roa_ttm", "pct_cfo_to_assets",
    ],
    # Augment baseline with one atomic block (still OOF-selected).
    "TECH2_REV": [
        "momentum_family_score", "defensive_family_score",
        "pct_monthly_revenue_yoy", "pct_revenue_yoy_acceleration",
    ],
    "TECH2_QUAL": [
        "momentum_family_score", "defensive_family_score",
        "pct_roa_ttm", "pct_cfo_to_assets",
    ],
    "TECH2_VALUE": [
        "momentum_family_score", "defensive_family_score",
        "pct_book_to_price_proxy", "pct_earnings_yield_proxy",
    ],
}


def fit_model_exp(df: pl.DataFrame, features: list[str], mode: str, ridge: float, cutoff: date) -> r1.CandidateModel:
    key = "EXP_TMP"
    r1.FEATURE_SETS[key] = features
    return r1.fit_model(df, key, mode, ridge, cutoff)


def build_oof_scores(joined: pl.DataFrame, calendar: list[date], features: list[str], mode: str, ridge: float) -> pl.DataFrame:
    pieces = []
    for start_year, end_year in a3.CV_FOLDS:
        start = date(start_year, 1, 1)
        end = date(end_year, 12, 31)
        cutoff = a3.previous_session(calendar, start, 22)
        model = fit_model_exp(joined, features, mode, ridge, cutoff)
        val = joined.filter(pl.col("date").is_between(start, end))
        pieces.append(
            val.select(
                "date", "code", "industry_category", "trading_money", "unexplained_price_jump", a3.LABEL
            ).with_columns(pl.Series("score", model.predict(val)))
        )
    return pl.concat(pieces).sort(["date", "code"])


def oof_rank_ic(scored: pl.DataFrame) -> dict:
    ics = []
    label = a3.LABEL
    for day in scored["date"].unique().to_list():
        g = scored.filter(pl.col("date") == day).drop_nulls([label, "score"])
        if g.height < 30:
            continue
        sr = g["score"].rank().to_numpy()
        lr = g[label].rank().to_numpy()
        if np.std(sr) == 0 or np.std(lr) == 0:
            continue
        ics.append(float(np.corrcoef(sr, lr)[0, 1]))
    return {
        "n_days": len(ics),
        "mean_rank_ic": float(np.mean(ics)) if ics else None,
        "p50_rank_ic": float(np.quantile(ics, 0.50)) if ics else None,
    }


def metric_twin(row: dict, baseline: dict) -> bool:
    keys = (
        "mean_rank_ic", "average_daily_turnover",
        "block_bootstrap_positive_probability", "cagr", "max_drawdown",
        "mean_daily_excess",
    )
    return all(
        row.get(k) is not None and baseline.get(k) is not None
        and abs(float(row[k]) - float(baseline[k])) < 1e-12
        for k in keys
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", type=Path, required=True)
    ap.add_argument("--prices", type=Path, required=True)
    ap.add_argument("--labels", type=Path, required=True)
    ap.add_argument("--actions", type=Path, required=True)
    ap.add_argument("--a2-qc", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    out = args.out
    (out / "outputs").mkdir(parents=True, exist_ok=True)
    (out / "reports").mkdir(parents=True, exist_ok=True)

    a2_qc = json.loads(args.a2_qc.read_text())
    if a2_qc["status"] != "PASS":
        raise RuntimeError("E50-A2 QC is not PASS")

    panel = pl.read_parquet(args.panel).sort(["date", "code"])
    needed = sorted({c for feats in ATOMIC_FEATURES.values() for c in feats})
    missing = [c for c in needed if c not in panel.columns]
    if missing:
        raise RuntimeError(f"missing columns: {missing}")

    price_scan = (
        pl.scan_parquet(args.prices) if args.prices.suffix == ".parquet"
        else pl.scan_csv(args.prices, schema_overrides={"code": pl.String}, encoding="utf8-lossy")
    )
    schema = price_scan.collect_schema()
    date_expr = pl.col("date") if schema["date"] == pl.Date else pl.col("date").str.to_date()
    prices = price_scan.select(
        date_expr.alias("date"), "code", "open", "trading_money", "sessions_observed", "base_eligible"
    ).collect(engine="streaming")
    execution, _ = a3.remove_partial_market_sessions(
        a3.build_execution_panel(prices, a3.load_actions(args.actions))
    )
    calendar = sorted(execution["date"].unique().to_list())
    exact_labels = a3.build_exact_open_labels(panel, execution, calendar)
    joined0 = a3.target_rank(
        panel.join(exact_labels.select("date", "code", a3.LABEL), on=["date", "code"], validate="1:1")
    )
    joined = r1.add_regime(joined0)

    cells = [{"feature_set": fs, "is_baseline": fs == "TECH2"} for fs in ATOMIC_FEATURES]
    # Confirm GLOBAL collapse once on baseline only (not a search axis).
    cells.append({"feature_set": "TECH2", "is_baseline": False, "mode_override": "GLOBAL", "tag": "TECH2_GLOBAL"})

    print(f"screening {len(cells)} atomic feature cells on OOF ...", flush=True)
    rows = []
    for i, cell in enumerate(cells, 1):
        fs = cell["feature_set"]
        mode = cell.get("mode_override", "BREADTH_REGIME")
        tag = cell.get("tag", fs)
        features = ATOMIC_FEATURES[fs]
        print(f"[{i}/{len(cells)}] {tag} / {mode} / λ=1.0 n={len(features)}", flush=True)
        scored = build_oof_scores(joined, calendar, features, mode, 1.0)
        ic = oof_rank_ic(scored)
        port = evaluate_cfg(scored.drop(a3.LABEL), execution, calendar, dict(FIXED_PORTFOLIO))
        row = {
            "feature_set": tag,
            "base_feature_set": fs,
            "mode": mode,
            "ridge_lambda": 1.0,
            "is_baseline": bool(cell["is_baseline"]),
            "n_features": len(features),
            "features": ",".join(features),
            **ic,
            "average_daily_turnover": port["average_daily_turnover"],
            "block_bootstrap_positive_probability": port["block_bootstrap_positive_probability"],
            "cagr": port["cagr"],
            "max_drawdown": port["max_drawdown"],
            "utility": port["utility"],
            "mean_daily_excess": port["mean_daily_excess"],
            "hac_t_stat": port["hac_t_stat"],
            "turnover_gate_pass": port["turnover_gate_pass"],
            "bootstrap_gate_pass": port["bootstrap_gate_pass"],
            "both_gates_pass": port["both_gates_pass"],
        }
        rows.append(row)
        print(
            f"  IC={row['mean_rank_ic']:.4f} turn={row['average_daily_turnover']:.4f} "
            f"boot={row['block_bootstrap_positive_probability']} both={row['both_gates_pass']}",
            flush=True,
        )

    result = pl.DataFrame(rows).sort(
        ["both_gates_pass", "block_bootstrap_positive_probability", "mean_rank_ic"],
        descending=[True, True, True],
    )
    result.write_csv(out / "outputs" / "stage4_atomic_feature_oof_grid.csv")

    baseline = next(r for r in rows if r["is_baseline"])
    dual_new, excluded = [], []
    for r in rows:
        if not r["both_gates_pass"] or r["is_baseline"]:
            continue
        if r["feature_set"] == "TECH2_GLOBAL":
            excluded.append({**r, "exclude_reason": "global_probe_not_new_family"})
            continue
        if metric_twin(r, baseline):
            excluded.append({**r, "exclude_reason": "metric_twin_of_baseline"})
            continue
        dual_new.append(r)
    dual_sorted = sorted(
        dual_new,
        key=lambda r: (
            -(r["block_bootstrap_positive_probability"] or 0),
            -(r["mean_rank_ic"] or -9),
            -(r["utility"] or -9),
        ),
    )
    best_ic = max(rows, key=lambda r: (r["mean_rank_ic"] is not None, r["mean_rank_ic"] or -9))
    winner = dual_sorted[0] if dual_sorted else None
    decision = (
        "OOF_NEW_ATOMIC_FEATURE_DUAL_GATE_WINNER"
        if winner
        else "OOF_NO_NEW_ATOMIC_FEATURE_DUAL_GATE_WINNER"
    )

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "STAGE4_ATOMIC_FEATURE_OOF",
        "window": "2011-2018 OOF only",
        "fixed_portfolio_reference": "C4",
        "fixed_portfolio": FIXED_PORTFOLIO,
        "fixed_mode": "BREADTH_REGIME",
        "fixed_lambda": 1.0,
        "baseline": baseline,
        "n_cells": len(rows),
        "n_both_pass": sum(1 for r in rows if r["both_gates_pass"]),
        "n_both_pass_new": len(dual_new),
        "excluded_degenerate_or_probe": excluded,
        "best_ic": best_ic,
        "research_decision": decision,
        "recommended": winner,
        "top_new_dual_gate": dual_sorted[:10],
        "gates_remain_experimental": True,
        "no_retune_C2_C4_C8": True,
        "no_promotion": True,
    }
    (out / "reports" / "stage4_atomic_feature_oof_summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n"
    )

    lines = [
        "# Stage-4A Atomic Feature Families (OOF)",
        "",
        "Portfolio fixed to **C4 wrapper**. Regime/mode: baseline BREADTH + `BREADTH_REGIME`, λ=1.0.",
        "Selection: 2011–2018 OOF only. No family-score recombinations / no PRICE8 redo.",
        "",
        f"## Decision: `{decision}`",
        "",
        f"Baseline TECH2: IC={baseline['mean_rank_ic']:.4f}, turn={baseline['average_daily_turnover']:.4f}, "
        f"boot={baseline['block_bootstrap_positive_probability']}",
        "",
        "| feature_set | mode | n | IC | turn | boot | both | CAGR | MDD |",
        "|---|---|---:|---:|---:|---:|---|---:|---:|",
    ]
    for r in result.to_dicts():
        lines.append(
            f"| {r['feature_set']} | {r['mode']} | {r['n_features']} | {r['mean_rank_ic']:.4f} | "
            f"{100 * r['average_daily_turnover']:.2f}% | {r['block_bootstrap_positive_probability']:.4f} | "
            f"{r['both_gates_pass']} | {100 * r['cagr']:.2f}% | {100 * r['max_drawdown']:.2f}% |"
        )
    if winner:
        lines += [
            "",
            "## Recommended (OOF only — not yet held-out)",
            "",
            f"- `{winner['feature_set']}` features=`{winner['features']}`",
            f"- boot `{winner['block_bootstrap_positive_probability']}`, turn `{winner['average_daily_turnover']:.4f}`, "
            f"IC `{winner['mean_rank_ic']:.4f}`",
            "",
            "Next: lock as F1 and run held-out once.",
            "",
        ]
    else:
        lines += [
            "",
            "No new atomic/hybrid feature set clears dual gates beyond TECH2.",
            "Do **not** held-out metric twins or GLOBAL probe.",
            "",
        ]
    if excluded:
        lines += ["Excluded dual-gate / probe cells:", ""]
        for r in excluded:
            lines.append(f"- `{r['feature_set']}` — {r['exclude_reason']}")
        lines.append("")
    lines += ["Artifact: `reports/stage4_atomic_feature_oof_summary.json`", ""]
    (out / "E50-A3-R1_STAGE4_ATOMIC_FEATURE_OOF.md").write_text("\n".join(lines))
    print(json.dumps({
        "research_decision": decision,
        "n_both_pass_new": len(dual_new),
        "winner": None if not winner else {
            "feature_set": winner["feature_set"],
            "bootstrap": winner["block_bootstrap_positive_probability"],
            "turnover": winner["average_daily_turnover"],
            "mean_rank_ic": winner["mean_rank_ic"],
        },
        "best_ic": {
            "feature_set": best_ic["feature_set"],
            "mean_rank_ic": best_ic["mean_rank_ic"],
            "both": best_ic["both_gates_pass"],
            "boot": best_ic["block_bootstrap_positive_probability"],
        },
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
