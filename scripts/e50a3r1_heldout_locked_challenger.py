#!/usr/bin/env python3
"""Evaluate the locked E50-A3-R1 OOF turnover challenger on held-out windows.

The challenger configuration is frozen at 2011-2018 OOF selection time.
This script does NOT retune on 2019-2022 or 2023-latest.

EXPERIMENTAL research only. Does not modify E16/E18/E22/E44/E45.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e50a3_train_exact_open as a3
import e50a3r1_repair as r1
from e50a3r1_turnover_diagnosis import (
    BOOTSTRAP_GATE,
    SELECTED,
    TURNOVER_CEILING,
    buffered_orders_ext,
    evaluate_cfg,
)

# Locked at OOF selection. Do not edit from held-out evidence.
LOCKED_CHALLENGER = {
    "family": "reb_buffer_expand",
    "top_k": 20,
    "rebalance_every": 42,
    "exit_multiple": 2.0,
    "neutralization": "NONE",
    "industry_cap": 5,
    "min_hold_cycles": 0,
    "liquidity_floor": 20_000_000.0,
    "replace_rank_gap": 0,
    "feature_set": SELECTED["feature_set"],
    "mode": SELECTED["mode"],
    "ridge_lambda": SELECTED["ridge_lambda"],
}

# Pre-existing R1 selected config (utility winner; failed turnover gate).
R1_SELECTED_REFERENCE = {
    "family": "r1_selected_reference",
    "top_k": 20,
    "rebalance_every": 5,
    "exit_multiple": 2.0,
    "neutralization": "NONE",
    "industry_cap": 5,
    "min_hold_cycles": 0,
    "liquidity_floor": 20_000_000.0,
    "replace_rank_gap": 0,
}


def evaluate_period(
    joined: pl.DataFrame,
    execution: pl.DataFrame,
    calendar: list[date],
    cfg: dict,
    name: str,
    start: date,
    end: date,
    fit_cutoff: date,
) -> dict:
    model = r1.fit_model(
        joined,
        LOCKED_CHALLENGER["feature_set"],
        LOCKED_CHALLENGER["mode"],
        LOCKED_CHALLENGER["ridge_lambda"],
        fit_cutoff,
    )
    scored = r1.score_period(joined, model, start, end)
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
    nav, trades = a3.simulate(orders, execution, start, end)
    benchmark = a3.market_proxy(execution, start, end)
    metric = a3.metrics(nav, trades, name)
    bench_metric = a3.metrics(benchmark, pl.DataFrame(), name + "_MARKET_PROXY")
    _, stats = a3.compare(nav, benchmark)
    out = {
        "portfolio": name,
        "fit_cutoff": str(fit_cutoff),
        **{k: cfg[k] for k in [
            "top_k", "rebalance_every", "exit_multiple", "neutralization",
            "industry_cap", "min_hold_cycles", "liquidity_floor", "replace_rank_gap",
        ]},
        "cagr": metric.get("cagr"),
        "max_drawdown": metric.get("max_drawdown"),
        "average_daily_turnover": metric.get("average_daily_turnover"),
        "total_cost": metric.get("total_cost"),
        "trade_count": metric.get("trade_count"),
        "ending_nav": metric.get("ending_nav"),
        "sharpe_rf0": metric.get("sharpe_rf0"),
        "market_proxy_cagr": bench_metric.get("cagr"),
        "market_proxy_max_drawdown": bench_metric.get("max_drawdown"),
        "beats_market_proxy": bool((metric.get("cagr") or -9) > (bench_metric.get("cagr") or 9)),
        "block_bootstrap_positive_probability": stats.get("block_bootstrap_positive_probability"),
        "mean_daily_excess": stats.get("mean_daily_excess"),
        "hac_t_stat": stats.get("hac_t_stat"),
        "turnover_gate_pass": bool((metric.get("average_daily_turnover") or 9) <= TURNOVER_CEILING),
        "bootstrap_gate_pass": bool((stats.get("block_bootstrap_positive_probability") or 0) >= BOOTSTRAP_GATE),
        **{f"diag_{k}": v for k, v in order_diag.items()},
    }
    out["both_experimental_gates_pass"] = bool(out["turnover_gate_pass"] and out["bootstrap_gate_pass"])
    # Persist NAV/trades for the locked challenger only.
    return out, nav, trades, benchmark


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", type=Path, required=True)
    ap.add_argument("--prices", type=Path, required=True)
    ap.add_argument("--labels", type=Path, required=True)
    ap.add_argument("--actions", type=Path, required=True)
    ap.add_argument("--a2-qc", type=Path, required=True)
    ap.add_argument("--oof-summary", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    out = args.out
    (out / "outputs").mkdir(parents=True, exist_ok=True)
    (out / "reports").mkdir(parents=True, exist_ok=True)

    oof_summary = json.loads(args.oof_summary.read_text())
    recommended = oof_summary["recommended_challenger"]
    # Hard lock: refuse to proceed if OOF dual-gate winner drifted.
    for key in ["top_k", "rebalance_every", "exit_multiple", "neutralization", "industry_cap"]:
        if recommended[key] != LOCKED_CHALLENGER[key]:
            raise RuntimeError(f"OOF recommended challenger drift on {key}: {recommended[key]} vs {LOCKED_CHALLENGER[key]}")
    if not recommended.get("both_gates_pass"):
        raise RuntimeError("OOF recommended challenger did not pass both experimental gates")

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
        date_expr.alias("date"), "code", "open", "trading_money", "sessions_observed", "base_eligible"
    ).collect(engine="streaming")
    execution, _ = a3.remove_partial_market_sessions(
        a3.build_execution_panel(prices, a3.load_actions(args.actions))
    )
    calendar = sorted(execution["date"].unique().to_list())
    exact_labels = a3.build_exact_open_labels(panel, execution, calendar)
    joined = a3.target_rank(
        r1.add_regime(panel).join(exact_labels.select("date", "code", a3.LABEL), on=["date", "code"], validate="1:1")
    )

    validation_start, validation_end = date(2019, 1, 1), date(2022, 12, 31)
    sealed_start, sealed_end = date(2023, 1, 1), max(calendar)
    val_cutoff = a3.previous_session(calendar, validation_start, 22)
    sealed_cutoff = a3.previous_session(calendar, sealed_start, 22)

    rows = []
    # Reconfirm OOF for the locked challenger (no retune).
    print("reconfirming locked challenger on 2011-2018 OOF ...", flush=True)
    oof_scores_path = out / "outputs" / "oof_scores_selected_model.parquet"
    if (Path("repro/e50a3r1-turnover-diagnosis-20260903/outputs/oof_scores_selected_model.parquet")).exists():
        # Prefer already-built OOF scores from diagnosis when present.
        oof_src = Path("repro/e50a3r1-turnover-diagnosis-20260903/outputs/oof_scores_selected_model.parquet")
        oof = pl.read_parquet(oof_src)
    else:
        from e50a3r1_turnover_diagnosis import build_oof_scores
        oof = build_oof_scores(joined, calendar)
        oof.write_parquet(oof_scores_path, compression="zstd")
    oof_row = evaluate_cfg(oof, execution, calendar, LOCKED_CHALLENGER)
    oof_row["portfolio"] = "TRAIN_OOF_LOCKED"
    oof_row["fit_cutoff"] = "walk_forward_folds"
    rows.append(oof_row)

    artifacts = {}
    for label, cfg in [("LOCKED_CHALLENGER", LOCKED_CHALLENGER), ("R1_SELECTED_REFERENCE", R1_SELECTED_REFERENCE)]:
        for name, start, end, cutoff in [
            (f"{label}_VALIDATION_2019_2022", validation_start, validation_end, val_cutoff),
            (f"{label}_SEALED_2023_LATEST", sealed_start, sealed_end, sealed_cutoff),
        ]:
            print(f"evaluating {name} ...", flush=True)
            row, nav, trades, benchmark = evaluate_period(
                joined, execution, calendar, cfg, name, start, end, cutoff
            )
            row["config_label"] = label
            rows.append(row)
            if label == "LOCKED_CHALLENGER":
                period = "VALIDATION_2019_2022" if "VALIDATION" in name else "SEALED_2023_LATEST"
                nav.write_csv(out / "outputs" / f"locked_{period.lower()}_daily_nav.csv")
                trades.write_csv(out / "outputs" / f"locked_{period.lower()}_trades.csv")
                benchmark.write_csv(out / "outputs" / f"locked_{period.lower()}_market_proxy_nav.csv")
                artifacts[period] = {
                    "nav": f"outputs/locked_{period.lower()}_daily_nav.csv",
                    "trades": f"outputs/locked_{period.lower()}_trades.csv",
                }

    result = pl.DataFrame(rows)
    result.write_csv(out / "outputs" / "heldout_period_metrics.csv")

    locked_val = next(r for r in rows if r["portfolio"] == "LOCKED_CHALLENGER_VALIDATION_2019_2022")
    locked_sealed = next(r for r in rows if r["portfolio"] == "LOCKED_CHALLENGER_SEALED_2023_LATEST")
    ref_val = next(r for r in rows if r["portfolio"] == "R1_SELECTED_REFERENCE_VALIDATION_2019_2022")
    ref_sealed = next(r for r in rows if r["portfolio"] == "R1_SELECTED_REFERENCE_SEALED_2023_LATEST")

    decision = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "EXPERIMENTAL_HELDOUT_EVAL",
        "locked_challenger": LOCKED_CHALLENGER,
        "selection_window": "2011-2018 OOF only",
        "no_retune_on_heldout": True,
        "gates_remain_experimental": True,
        "oof_reconfirm": {
            "turnover": oof_row["average_daily_turnover"],
            "bootstrap": oof_row["block_bootstrap_positive_probability"],
            "both_gates_pass": oof_row["both_gates_pass"],
        },
        "validation_2019_2022": locked_val,
        "sealed_2023_latest": locked_sealed,
        "r1_selected_reference_validation": {
            "cagr": ref_val["cagr"],
            "max_drawdown": ref_val["max_drawdown"],
            "average_daily_turnover": ref_val["average_daily_turnover"],
            "block_bootstrap_positive_probability": ref_val["block_bootstrap_positive_probability"],
            "beats_market_proxy": ref_val["beats_market_proxy"],
        },
        "r1_selected_reference_sealed": {
            "cagr": ref_sealed["cagr"],
            "max_drawdown": ref_sealed["max_drawdown"],
            "average_daily_turnover": ref_sealed["average_daily_turnover"],
            "block_bootstrap_positive_probability": ref_sealed["block_bootstrap_positive_probability"],
            "beats_market_proxy": ref_sealed["beats_market_proxy"],
        },
        "promotion_checks_experimental": {
            "oof_turnover_pass": bool(oof_row["turnover_gate_pass"]),
            "oof_bootstrap_pass": bool(oof_row["bootstrap_gate_pass"]),
            "validation_beats_proxy": bool(locked_val["beats_market_proxy"]),
            "sealed_beats_proxy": bool(locked_sealed["beats_market_proxy"]),
            "validation_bootstrap_pass": bool(locked_val["bootstrap_gate_pass"]),
            "sealed_bootstrap_pass": bool(locked_sealed["bootstrap_gate_pass"]),
            "validation_turnover_pass": bool(locked_val["turnover_gate_pass"]),
            "sealed_turnover_pass": bool(locked_sealed["turnover_gate_pass"]),
        },
        "artifacts": artifacts,
        "mdd_warning": {
            "oof_max_drawdown": oof_row["max_drawdown"],
            "validation_max_drawdown": locked_val["max_drawdown"],
            "sealed_max_drawdown": locked_sealed["max_drawdown"],
            "long_term_target_band": "approximately -10% to -15%",
            "note": "MDD remains far from the long-term target; drawdown repair is a later research step and must not weaken HARD_FROZEN causal rules.",
        },
    }
    both_heldout_bootstrap = (
        decision["promotion_checks_experimental"]["validation_bootstrap_pass"]
        and decision["promotion_checks_experimental"]["sealed_bootstrap_pass"]
    )
    both_heldout_proxy = (
        decision["promotion_checks_experimental"]["validation_beats_proxy"]
        and decision["promotion_checks_experimental"]["sealed_beats_proxy"]
    )
    if (
        decision["promotion_checks_experimental"]["oof_turnover_pass"]
        and decision["promotion_checks_experimental"]["oof_bootstrap_pass"]
        and both_heldout_bootstrap
        and both_heldout_proxy
        and decision["promotion_checks_experimental"]["validation_turnover_pass"]
        and decision["promotion_checks_experimental"]["sealed_turnover_pass"]
    ):
        decision["research_decision"] = "EXPERIMENTAL_HELDOUT_PASS_CANDIDATE"
    else:
        decision["research_decision"] = "EXPERIMENTAL_HELDOUT_FAIL_OR_INCOMPLETE"
    decision["next_research_step"] = (
        "If held-out fails on proxy/bootstrap/turnover, diagnose without retuning on held-out; "
        "MDD repair remains a separate challenger after causal gates. Do not touch E45 yet."
    )
    (out / "reports" / "heldout_decision.json").write_text(json.dumps(decision, indent=2, default=str) + "\n")
    print(json.dumps({
        "research_decision": decision["research_decision"],
        "validation_cagr": locked_val["cagr"],
        "validation_mdd": locked_val["max_drawdown"],
        "validation_turnover": locked_val["average_daily_turnover"],
        "validation_bootstrap": locked_val["block_bootstrap_positive_probability"],
        "sealed_cagr": locked_sealed["cagr"],
        "sealed_mdd": locked_sealed["max_drawdown"],
        "sealed_turnover": locked_sealed["average_daily_turnover"],
        "sealed_bootstrap": locked_sealed["block_bootstrap_positive_probability"],
    }, indent=2))


if __name__ == "__main__":
    main()
