#!/usr/bin/env python3
"""E50-A3-R1 turnover diagnosis and OOF-only challenger screen.

EXPERIMENTAL research tooling. Does not modify E16/E18/E22/E44/E45,
does not rebuild A0/A1/A2, and does not evaluate 2019-2022 or 2023-latest
for parameter selection.

Selection and diagnosis window: embargoed 2011-2018 OOF only.
Exact T+1 simulator is reused from e50a3_train_exact_open.simulate.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e50a3_train_exact_open as a3
import e50a3r1_repair as r1

OOF_START = date(2011, 1, 1)
OOF_END = date(2018, 12, 31)
TURNOVER_CEILING = 0.025
BOOTSTRAP_GATE = 0.70
SELECTED = {
    "feature_set": "TECH2",
    "mode": "BREADTH_REGIME",
    "ridge_lambda": 1.0,
}


def build_oof_scores(joined: pl.DataFrame, calendar: list[date]) -> pl.DataFrame:
    """Walk-forward OOF scores for the already-selected R1 model family only."""
    pieces: list[pl.DataFrame] = []
    for start_year, end_year in a3.CV_FOLDS:
        start = date(start_year, 1, 1)
        end = date(end_year, 12, 31)
        cutoff = a3.previous_session(calendar, start, 22)
        model = r1.fit_model(
            joined, SELECTED["feature_set"], SELECTED["mode"], SELECTED["ridge_lambda"], cutoff
        )
        val = joined.filter(pl.col("date").is_between(start, end))
        pieces.append(
            val.select(
                "date", "code", "industry_category", "trading_money", "unexplained_price_jump"
            ).with_columns(pl.Series("score", model.predict(val)))
        )
    return pl.concat(pieces).sort(["date", "code"])


def buffered_orders_ext(
    scored: pl.DataFrame,
    calendar: list[date],
    top_k: int,
    rebalance_every: int,
    exit_multiple: float,
    neutralization: str,
    industry_cap: int,
    min_hold_cycles: int = 0,
    liquidity_floor: float = 20_000_000.0,
    replace_rank_gap: int = 0,
) -> tuple[pl.DataFrame, dict]:
    """Causal buffered selector with optional min-hold and replace-gap (EXPERIMENTAL)."""
    d = r1.add_neutral_score(scored, neutralization)
    signal_dates = sorted(d["date"].unique().to_list())[::rebalance_every]
    next_date = {calendar[i]: calendar[i + 1] for i in range(len(calendar) - 1)}
    groups = {
        (day,): g
        for (day,), g in d.filter(pl.col("date").is_in(signal_dates)).partition_by("date", as_dict=True).items()
    }
    held: list[str] = []
    hold_age: dict[str, int] = {}
    rows: list[dict] = []
    exit_rank = int(math.ceil(top_k * exit_multiple))
    diag = {
        "rebalance_events": 0,
        "forced_rank_exits": 0,
        "liquidity_or_missing_exits": 0,
        "min_hold_blocks": 0,
        "replace_gap_blocks": 0,
        "jaccard": [],
        "one_way_name_churn": [],
        "names_held": [],
    }
    for day in signal_dates:
        if day not in next_date or (day,) not in groups:
            continue
        candidates = (
            groups[(day,)]
            .filter((pl.col("trading_money") >= liquidity_floor) & ~pl.col("unexplained_price_jump"))
            .sort(["neutral_score", "trading_money", "code"], descending=[True, True, False])
        )
        ranked = []
        for i, rec in enumerate(candidates.iter_rows(named=True), 1):
            rec["rank"] = i
            ranked.append(rec)
        by_code = {rec["code"]: rec for rec in ranked}
        prev = list(held)
        selected: list[str] = []
        industry_counts: dict[str, int] = {}
        for code in held:
            rec = by_code.get(code)
            age = hold_age.get(code, 0) + 1
            if rec is None:
                diag["liquidity_or_missing_exits"] += 1
                continue
            if rec["rank"] > exit_rank:
                if age < min_hold_cycles:
                    diag["min_hold_blocks"] += 1
                else:
                    diag["forced_rank_exits"] += 1
                    continue
            industry = rec["industry_category"] or "UNKNOWN"
            if industry_counts.get(industry, 0) < industry_cap:
                selected.append(code)
                industry_counts[industry] = industry_counts.get(industry, 0) + 1
        for rec in ranked:
            if len(selected) >= top_k:
                break
            code = rec["code"]
            industry = rec["industry_category"] or "UNKNOWN"
            if code in selected or industry_counts.get(industry, 0) >= industry_cap:
                continue
            if replace_rank_gap > 0 and prev and code not in prev:
                # Only admit a new name if it clears the current worst held rank by a gap.
                worst_held_rank = max(
                    (by_code[c]["rank"] for c in selected if c in by_code),
                    default=top_k,
                )
                if rec["rank"] > max(1, worst_held_rank - replace_rank_gap):
                    diag["replace_gap_blocks"] += 1
                    continue
            selected.append(code)
            industry_counts[industry] = industry_counts.get(industry, 0) + 1
        new_age = {}
        for code in selected:
            new_age[code] = hold_age.get(code, 0) + 1 if code in hold_age or code in held else 1
        hold_age = new_age
        held = selected
        diag["rebalance_events"] += 1
        diag["names_held"].append(len(selected))
        if prev:
            inter = len(set(prev) & set(selected))
            union = len(set(prev) | set(selected)) or 1
            diag["jaccard"].append(inter / union)
            diag["one_way_name_churn"].append(
                (len(set(prev) - set(selected)) + len(set(selected) - set(prev))) / (2 * max(len(prev), 1))
            )
        weight = 1.0 / len(selected) if selected else 0.0
        for rank, code in enumerate(selected, 1):
            rec = by_code[code]
            rows.append(
                {
                    "signal_date": day,
                    "execution_date": next_date[day],
                    "code": code,
                    "score": float(rec["score"]),
                    "neutral_score": float(rec["neutral_score"]),
                    "selection_rank": rank,
                    "target_weight": weight,
                }
            )
    summary = {
        "rebalance_events": diag["rebalance_events"],
        "forced_rank_exits": diag["forced_rank_exits"],
        "liquidity_or_missing_exits": diag["liquidity_or_missing_exits"],
        "min_hold_blocks": diag["min_hold_blocks"],
        "replace_gap_blocks": diag["replace_gap_blocks"],
        "mean_jaccard": float(np.mean(diag["jaccard"])) if diag["jaccard"] else None,
        "mean_one_way_name_churn": float(np.mean(diag["one_way_name_churn"])) if diag["one_way_name_churn"] else None,
        "mean_names_held": float(np.mean(diag["names_held"])) if diag["names_held"] else None,
        "exit_rank": exit_rank,
    }
    orders = pl.DataFrame(rows).sort(["execution_date", "selection_rank"]) if rows else pl.DataFrame(
        schema={
            "signal_date": pl.Date,
            "execution_date": pl.Date,
            "code": pl.String,
            "score": pl.Float64,
            "neutral_score": pl.Float64,
            "selection_rank": pl.Int64,
            "target_weight": pl.Float64,
        }
    )
    return orders, summary


def score_autocorr(scored: pl.DataFrame, sample_dates: list[date]) -> dict:
    """Cross-sectional rank autocorrelation of scores across consecutive signal dates."""
    dates = sorted(sample_dates)
    corrs = []
    for a, b in zip(dates[:-1], dates[1:]):
        left = scored.filter(pl.col("date") == a).select("code", pl.col("score").alias("sa"))
        right = scored.filter(pl.col("date") == b).select("code", pl.col("score").alias("sb"))
        both = left.join(right, on="code", how="inner")
        if both.height < 30:
            continue
        sa = both["sa"].rank().to_numpy()
        sb = both["sb"].rank().to_numpy()
        if np.std(sa) == 0 or np.std(sb) == 0:
            continue
        corrs.append(float(np.corrcoef(sa, sb)[0, 1]))
    return {
        "pairs": len(corrs),
        "mean_rank_autocorr": float(np.mean(corrs)) if corrs else None,
        "p10_rank_autocorr": float(np.quantile(corrs, 0.10)) if corrs else None,
        "p50_rank_autocorr": float(np.quantile(corrs, 0.50)) if corrs else None,
    }


def universe_churn(scored: pl.DataFrame, liquidity_floor: float, sample_every: int = 5) -> dict:
    dates = sorted(scored["date"].unique().to_list())[::sample_every]
    j = []
    sizes = []
    for a, b in zip(dates[:-1], dates[1:]):
        ca = set(
            scored.filter((pl.col("date") == a) & (pl.col("trading_money") >= liquidity_floor) & ~pl.col("unexplained_price_jump"))[
                "code"
            ].to_list()
        )
        cb = set(
            scored.filter((pl.col("date") == b) & (pl.col("trading_money") >= liquidity_floor) & ~pl.col("unexplained_price_jump"))[
                "code"
            ].to_list()
        )
        if not ca or not cb:
            continue
        sizes.append(len(ca))
        j.append(len(ca & cb) / len(ca | cb))
    return {
        "mean_eligible_names": float(np.mean(sizes)) if sizes else None,
        "mean_eligible_jaccard": float(np.mean(j)) if j else None,
    }


def evaluate_cfg(
    scored: pl.DataFrame,
    execution: pl.DataFrame,
    calendar: list[date],
    cfg: dict,
) -> dict:
    orders, order_diag = buffered_orders_ext(
        scored,
        calendar,
        top_k=cfg["top_k"],
        rebalance_every=cfg["rebalance_every"],
        exit_multiple=cfg["exit_multiple"],
        neutralization=cfg["neutralization"],
        industry_cap=cfg["industry_cap"],
        min_hold_cycles=cfg.get("min_hold_cycles", 0),
        liquidity_floor=cfg.get("liquidity_floor", 20_000_000.0),
        replace_rank_gap=cfg.get("replace_rank_gap", 0),
    )
    nav, trades = a3.simulate(orders, execution, OOF_START, OOF_END)
    benchmark = a3.market_proxy(execution, OOF_START, OOF_END)
    metric = a3.metrics(nav, trades, "TRAIN_OOF")
    _, stats = a3.compare(nav, benchmark)
    rebalance_days = max(1, int(math.ceil(metric.get("days", 1) / max(cfg["rebalance_every"], 1))))
    out = {
        **cfg,
        "cagr": metric.get("cagr"),
        "max_drawdown": metric.get("max_drawdown"),
        "average_daily_turnover": metric.get("average_daily_turnover"),
        "total_cost": metric.get("total_cost"),
        "trade_count": metric.get("trade_count"),
        "ending_nav": metric.get("ending_nav"),
        "utility": (metric.get("cagr") or 0.0) - 0.5 * abs(metric.get("max_drawdown") or 0.0),
        "block_bootstrap_positive_probability": stats.get("block_bootstrap_positive_probability"),
        "mean_daily_excess": stats.get("mean_daily_excess"),
        "hac_t_stat": stats.get("hac_t_stat"),
        "turnover_gate_pass": bool((metric.get("average_daily_turnover") or 9) <= TURNOVER_CEILING),
        "bootstrap_gate_pass": bool((stats.get("block_bootstrap_positive_probability") or 0) >= BOOTSTRAP_GATE),
        "implied_avg_rebalance_day_turnover": (metric.get("average_daily_turnover") or 0) * cfg["rebalance_every"],
        **{f"diag_{k}": v for k, v in order_diag.items()},
    }
    out["both_gates_pass"] = bool(out["turnover_gate_pass"] and out["bootstrap_gate_pass"])
    return out


def challenger_grid() -> list[dict]:
    """Focused EXPERIMENTAL challengers beyond / around the current R1 grid."""
    cells: list[dict] = []
    # Current-grid extremes (reference, already known from baseline grid).
    for top_k, reb, exit_m, neut, cap in [
        (20, 5, 2.0, "NONE", 5),
        (20, 21, 2.0, "NONE", 5),
        (30, 21, 2.0, "NONE", 5),
        (30, 21, 2.0, "NONE", 3),
        (20, 10, 2.0, "NONE", 5),
    ]:
        cells.append(
            {
                "family": "current_grid_reference",
                "top_k": top_k,
                "rebalance_every": reb,
                "exit_multiple": exit_m,
                "neutralization": neut,
                "industry_cap": cap,
                "min_hold_cycles": 0,
                "liquidity_floor": 20_000_000.0,
                "replace_rank_gap": 0,
            }
        )
    # Longer rebalance / wider buffer / larger book.
    for top_k in [20, 30, 40]:
        for reb in [21, 42, 63]:
            for exit_m in [2.0, 3.0, 4.0, 5.0]:
                cells.append(
                    {
                        "family": "reb_buffer_expand",
                        "top_k": top_k,
                        "rebalance_every": reb,
                        "exit_multiple": exit_m,
                        "neutralization": "NONE",
                        "industry_cap": 5,
                        "min_hold_cycles": 0,
                        "liquidity_floor": 20_000_000.0,
                        "replace_rank_gap": 0,
                    }
                )
    # Minimum holding cycles on top of low-turnover corners.
    for reb, exit_m, hold in [(21, 2.0, 2), (21, 3.0, 2), (21, 2.0, 3), (42, 2.0, 2), (42, 3.0, 2)]:
        cells.append(
            {
                "family": "min_hold",
                "top_k": 30,
                "rebalance_every": reb,
                "exit_multiple": exit_m,
                "neutralization": "NONE",
                "industry_cap": 5,
                "min_hold_cycles": hold,
                "liquidity_floor": 20_000_000.0,
                "replace_rank_gap": 0,
            }
        )
    # Higher liquidity floors.
    for floor in [50_000_000.0, 100_000_000.0]:
        for reb, exit_m in [(21, 2.0), (21, 3.0), (42, 2.0), (42, 3.0)]:
            cells.append(
                {
                    "family": "liquidity_floor",
                    "top_k": 30,
                    "rebalance_every": reb,
                    "exit_multiple": exit_m,
                    "neutralization": "NONE",
                    "industry_cap": 5,
                    "min_hold_cycles": 0,
                    "liquidity_floor": floor,
                    "replace_rank_gap": 0,
                }
            )
    # Replace-rank gap (admit new names only with a clear rank advantage).
    for gap in [5, 10]:
        for reb, exit_m in [(21, 2.0), (21, 3.0), (42, 2.0)]:
            cells.append(
                {
                    "family": "replace_rank_gap",
                    "top_k": 30,
                    "rebalance_every": reb,
                    "exit_multiple": exit_m,
                    "neutralization": "NONE",
                    "industry_cap": 5,
                    "min_hold_cycles": 0,
                    "liquidity_floor": 20_000_000.0,
                    "replace_rank_gap": gap,
                }
            )
    # Industry neutralization check at low-turnover settings.
    for reb, exit_m in [(21, 2.0), (42, 2.0), (42, 3.0)]:
        cells.append(
            {
                "family": "neutralization",
                "top_k": 30,
                "rebalance_every": reb,
                "exit_multiple": exit_m,
                "neutralization": "INDUSTRY_LIQUIDITY",
                "industry_cap": 5,
                "min_hold_cycles": 0,
                "liquidity_floor": 20_000_000.0,
                "replace_rank_gap": 0,
            }
        )
    # Deduplicate.
    uniq = {}
    for c in cells:
        key = tuple(sorted((k, c[k]) for k in c if k != "family"))
        uniq[key] = c
    return list(uniq.values())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", type=Path, required=True)
    ap.add_argument("--prices", type=Path, required=True)
    ap.add_argument("--labels", type=Path, required=True)
    ap.add_argument("--actions", type=Path, required=True)
    ap.add_argument("--a2-qc", type=Path, required=True)
    ap.add_argument("--baseline-grid", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "reports").mkdir(exist_ok=True)
    (out / "outputs").mkdir(exist_ok=True)

    a2_qc = json.loads(args.a2_qc.read_text())
    if a2_qc["status"] != "PASS":
        raise RuntimeError("E50-A2 QC is not PASS")

    panel = pl.read_parquet(args.panel).sort(["date", "code"])
    price_scan = (
        pl.scan_parquet(args.prices)
        if args.prices.suffix == ".parquet"
        else pl.scan_csv(args.prices, schema_overrides={"code": pl.String}, encoding="utf8-lossy")
    )
    schema = price_scan.collect_schema()
    date_expr = pl.col("date") if schema["date"] == pl.Date else pl.col("date").str.to_date()
    prices = price_scan.select(
        date_expr.alias("date"),
        "code",
        "open",
        "trading_money",
        "sessions_observed",
        "base_eligible",
    ).collect(engine="streaming")
    execution, _ = a3.remove_partial_market_sessions(
        a3.build_execution_panel(prices, a3.load_actions(args.actions))
    )
    calendar = sorted(execution["date"].unique().to_list())
    exact_labels = a3.build_exact_open_labels(panel, execution, calendar)
    joined = a3.target_rank(
        r1.add_regime(panel).join(exact_labels.select("date", "code", a3.LABEL), on=["date", "code"], validate="1:1")
    )

    print("building 2011-2018 OOF scores for TECH2/BREADTH_REGIME/lambda=1.0 ...", flush=True)
    oof = build_oof_scores(joined, calendar)
    oof.write_parquet(out / "outputs" / "oof_scores_selected_model.parquet", compression="zstd")

    # Root-cause diagnostics on signal stability / universe / current lowest-turnover cell.
    signal_dates_5 = sorted(oof["date"].unique().to_list())[::5]
    signal_dates_21 = sorted(oof["date"].unique().to_list())[::21]
    root = {
        "selected_model": SELECTED,
        "window": {"start": str(OOF_START), "end": str(OOF_END)},
        "gates_experimental": {
            "turnover_ceiling": TURNOVER_CEILING,
            "bootstrap_cutoff": BOOTSTRAP_GATE,
        },
        "score_autocorr_every_5": score_autocorr(oof, signal_dates_5),
        "score_autocorr_every_21": score_autocorr(oof, signal_dates_21),
        "universe_churn_20m": universe_churn(oof, 20_000_000.0, sample_every=5),
        "universe_churn_50m": universe_churn(oof, 50_000_000.0, sample_every=5),
        "baseline_grid_summary": {},
    }
    baseline = pl.read_csv(args.baseline_grid)
    root["baseline_grid_summary"] = {
        "n_cells": baseline.height,
        "feasible_cells": int(baseline.filter(pl.col("turnover_feasible")).height),
        "turnover_min": float(baseline["average_daily_turnover"].min()),
        "turnover_median": float(baseline["average_daily_turnover"].median()),
        "turnover_max": float(baseline["average_daily_turnover"].max()),
        "lowest_turnover_cell": baseline.sort("average_daily_turnover").row(0, named=True),
        "best_utility_cell": baseline.sort(["utility", "cagr"], descending=True).row(0, named=True),
        "by_rebalance_mean_turnover": {
            str(r["rebalance_every"]): float(r["average_daily_turnover"])
            for r in baseline.group_by("rebalance_every").agg(pl.col("average_daily_turnover").mean()).iter_rows(named=True)
        },
        "by_exit_mean_turnover": {
            str(r["exit_multiple"]): float(r["average_daily_turnover"])
            for r in baseline.group_by("exit_multiple").agg(pl.col("average_daily_turnover").mean()).iter_rows(named=True)
        },
    }

    # Deep diagnose current selected and lowest-turnover cells.
    deep_cfgs = [
        {"label": "selected_utility", "top_k": 20, "rebalance_every": 5, "exit_multiple": 2.0,
         "neutralization": "NONE", "industry_cap": 5, "min_hold_cycles": 0,
         "liquidity_floor": 20_000_000.0, "replace_rank_gap": 0, "family": "deep"},
        {"label": "lowest_turnover_current_grid", "top_k": 30, "rebalance_every": 21, "exit_multiple": 2.0,
         "neutralization": "NONE", "industry_cap": 5, "min_hold_cycles": 0,
         "liquidity_floor": 20_000_000.0, "replace_rank_gap": 0, "family": "deep"},
    ]
    deep_rows = []
    for cfg in deep_cfgs:
        row = evaluate_cfg(oof, execution, calendar, cfg)
        deep_rows.append(row)
    root["deep_current_cells"] = deep_rows
    (out / "reports" / "root_cause_diagnostics.json").write_text(json.dumps(root, indent=2, default=str) + "\n")

    print(f"evaluating {len(challenger_grid())} OOF-only challenger cells ...", flush=True)
    results = []
    for i, cfg in enumerate(challenger_grid(), 1):
        row = evaluate_cfg(oof, execution, calendar, cfg)
        results.append(row)
        if i % 10 == 0 or row["both_gates_pass"]:
            print(
                f"[{i}/{len(challenger_grid())}] reb={cfg['rebalance_every']} exit={cfg['exit_multiple']} "
                f"top_k={cfg['top_k']} hold={cfg.get('min_hold_cycles',0)} liq={cfg.get('liquidity_floor')} "
                f"to={row['average_daily_turnover']:.4f} boot={row['block_bootstrap_positive_probability']:.3f} "
                f"both={row['both_gates_pass']}",
                flush=True,
            )
    result_df = pl.DataFrame(results).sort(
        ["both_gates_pass", "turnover_gate_pass", "utility", "cagr"],
        descending=[True, True, True, True],
    )
    result_df.write_csv(out / "outputs" / "oof_challenger_grid.csv")

    passing = result_df.filter(pl.col("both_gates_pass"))
    turnover_pass = result_df.filter(pl.col("turnover_gate_pass"))
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "window": "2011-01-01 to 2018-12-31 OOF only",
        "no_2019_plus_selection": True,
        "n_challengers": result_df.height,
        "n_turnover_pass": turnover_pass.height,
        "n_bootstrap_pass": int(result_df.filter(pl.col("bootstrap_gate_pass")).height),
        "n_both_pass": passing.height,
        "best_turnover": result_df.sort("average_daily_turnover").row(0, named=True),
        "best_utility_among_turnover_pass": (
            turnover_pass.sort(["utility", "cagr"], descending=True).row(0, named=True)
            if turnover_pass.height
            else None
        ),
        "best_both_gates": passing.sort(["utility", "cagr"], descending=True).row(0, named=True) if passing.height else None,
        "recommended_challenger": None,
        "gates_remain_experimental": True,
    }
    if passing.height:
        summary["recommended_challenger"] = summary["best_both_gates"]
    elif turnover_pass.height:
        summary["recommended_challenger"] = summary["best_utility_among_turnover_pass"]
        summary["recommendation_note"] = (
            "No cell passed both gates. Recommend the best turnover-feasible cell for further "
            "diagnosis only; do not open 2019+/sealed evaluation yet."
        )
    else:
        summary["recommended_challenger"] = summary["best_turnover"]
        summary["recommendation_note"] = (
            "No cell passed the 2.5% turnover gate. Recommend the lowest-turnover challenger as "
            "the next structural diagnosis target; do not open 2019+/sealed evaluation yet."
        )
    (out / "reports" / "oof_challenger_summary.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
    print(json.dumps({"n_both_pass": summary["n_both_pass"], "n_turnover_pass": summary["n_turnover_pass"]}, indent=2))


if __name__ == "__main__":
    main()
