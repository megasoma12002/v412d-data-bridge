#!/usr/bin/env python3
"""Stage-2 alpha/model OOF screen (EXPERIMENTAL).

Hypothesis level change: vary feature_set / regime mode / ridge lambda on
2011-2018 OOF only. Portfolio rules FIXED to reference C4 (val-turnover-pass
cluster; best val bootstrap among C2/C4/C8) so this round tests the model, not
another top_k/reb/exit search.

Does not retune C2/C4/C8. Does not modify E16/E18/E22/E44/E45.
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
from e50a3r1_turnover_diagnosis import (
    BOOTSTRAP_GATE,
    OOF_END,
    OOF_START,
    TURNOVER_CEILING,
    buffered_orders_ext,
    evaluate_cfg,
)

# Fixed portfolio wrapper from C4 reference (not retuned).
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

# Baseline locked model used by C1–C8.
BASELINE_MODEL = {
    "feature_set": "TECH2",
    "mode": "BREADTH_REGIME",
    "ridge_lambda": 1.0,
}

MODEL_GRID = [
    (fs, mode, lam)
    for fs in ["TECH2", "PRICE8"]
    for mode in ["GLOBAL", "BREADTH_REGIME"]
    for lam in [0.1, 1.0, 10.0, 100.0]
]


def build_oof_scores_for_model(
    joined: pl.DataFrame, calendar: list[date], feature_set: str, mode: str, ridge: float
) -> pl.DataFrame:
    pieces: list[pl.DataFrame] = []
    for start_year, end_year in a3.CV_FOLDS:
        start = date(start_year, 1, 1)
        end = date(end_year, 12, 31)
        cutoff = a3.previous_session(calendar, start, 22)
        model = r1.fit_model(joined, feature_set, mode, ridge, cutoff)
        val = joined.filter(pl.col("date").is_between(start, end))
        pieces.append(
            val.select(
                "date", "code", "industry_category", "trading_money", "unexplained_price_jump", a3.LABEL
            ).with_columns(pl.Series("score", model.predict(val)))
        )
    return pl.concat(pieces).sort(["date", "code"])


def oof_rank_ic(scored: pl.DataFrame) -> dict:
    # Spearman-ish: corr of score rank vs label rank within date, then mean.
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
        "p10_rank_ic": float(np.quantile(ics, 0.10)) if ics else None,
        "p50_rank_ic": float(np.quantile(ics, 0.50)) if ics else None,
    }


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
    joined = a3.target_rank(
        r1.add_regime(panel).join(exact_labels.select("date", "code", a3.LABEL), on=["date", "code"], validate="1:1")
    )

    rows = []
    print(f"screening {len(MODEL_GRID)} models with FIXED C4 portfolio wrapper on OOF ...", flush=True)
    for i, (fs, mode, lam) in enumerate(MODEL_GRID, 1):
        print(f"[{i}/{len(MODEL_GRID)}] {fs} / {mode} / lambda={lam}", flush=True)
        scored = build_oof_scores_for_model(joined, calendar, fs, mode, lam)
        ic = oof_rank_ic(scored)
        cfg = dict(FIXED_PORTFOLIO)
        cfg["feature_set"] = fs
        cfg["mode"] = mode
        cfg["ridge_lambda"] = lam
        scored_eval = scored.drop(a3.LABEL)
        port = evaluate_cfg(scored_eval, execution, calendar, cfg)
        row = {
            "feature_set": fs,
            "mode": mode,
            "ridge_lambda": float(lam),
            "is_baseline_model": (
                fs == BASELINE_MODEL["feature_set"]
                and mode == BASELINE_MODEL["mode"]
                and float(lam) == float(BASELINE_MODEL["ridge_lambda"])
            ),
            "is_baseline_family": (
                fs == BASELINE_MODEL["feature_set"] and mode == BASELINE_MODEL["mode"]
            ),
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
            f"  IC={row['mean_rank_ic']} turn={row['average_daily_turnover']:.4f} "
            f"boot={row['block_bootstrap_positive_probability']} both={row['both_gates_pass']}",
            flush=True,
        )

    result = pl.DataFrame(rows).sort(
        ["both_gates_pass", "block_bootstrap_positive_probability", "mean_rank_ic"],
        descending=[True, True, True],
    )
    result.write_csv(out / "outputs" / "stage2_model_oof_grid.csv")

    baseline = next(r for r in rows if r["is_baseline_model"])
    # "New model" = different feature_set or mode (lambda-only tweaks of TECH2/BREADTH are not a new hypothesis).
    dual_new = [
        r for r in rows
        if r["both_gates_pass"] and not r["is_baseline_family"]
    ]
    dual_sorted = sorted(
        dual_new,
        key=lambda r: (
            -(r["block_bootstrap_positive_probability"] or 0),
            -(r["mean_rank_ic"] or -9),
            -(r["utility"] or -9),
        ),
    )
    best_ic = sorted(rows, key=lambda r: -(r["mean_rank_ic"] or -9))[0]
    price8_best = sorted(
        [r for r in rows if r["feature_set"] == "PRICE8"],
        key=lambda r: (-(r["block_bootstrap_positive_probability"] or 0), -(r["mean_rank_ic"] or -9)),
    )[0]

    if dual_sorted:
        winner = dual_sorted[0]
        decision = "OOF_NEW_MODEL_DUAL_GATE_WINNER"
    else:
        winner = None
        decision = "OOF_NO_NEW_MODEL_DUAL_GATE_WINNER"

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "STAGE2_MODEL_OOF_SCREEN",
        "window": "2011-2018 OOF only",
        "hypothesis": (
            "Change alpha/model (feature_set, regime mode, ridge lambda) while freezing C4 portfolio wrapper."
        ),
        "fixed_portfolio_reference": "C4",
        "fixed_portfolio": FIXED_PORTFOLIO,
        "baseline_model": BASELINE_MODEL,
        "baseline_oof": baseline,
        "n_models": len(rows),
        "n_both_pass": sum(1 for r in rows if r["both_gates_pass"]),
        "n_both_pass_new_family_or_mode": len(dual_new),
        "best_ic_model": best_ic,
        "best_price8_model": price8_best,
        "research_decision": decision,
        "recommended_model": winner,
        "gates_remain_experimental": True,
        "no_retune_of_C2_C4_C8": True,
        "no_promotion": True,
        "interpretation": (
            "TECH2 + BREADTH_REGIME is required for dual-gate under C4 wrapper; GLOBAL collapses bootstrap. "
            "PRICE8 + BREADTH has similar IC but fails OOF bootstrap (~0.51–0.53). "
            "Lambda is nearly inert for TECH2/BREADTH. No new feature/mode family clears both gates."
        ),
        "next_step": (
            "Do not lock a lambda-only TECH2/BREADTH twin as M1. Keep C2/C4/C8 references. "
            "Next model stage needs features beyond TECH2/PRICE8 or a different regime definition, "
            "still selected on OOF only."
        ),
    }
    (out / "reports" / "stage2_model_oof_summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n"
    )

    lines = [
        "# Stage-2 Alpha/Model OOF Screen",
        "",
        "Portfolio rules fixed to **C4 wrapper**. Model axes only. OOF 2011–2018 only.",
        "",
        f"## Decision: `{decision}`",
        "",
        summary["interpretation"],
        "",
        f"Baseline TECH2/BREADTH/λ=1.0: turnover={baseline['average_daily_turnover']:.4f}, "
        f"bootstrap={baseline['block_bootstrap_positive_probability']}, IC={baseline['mean_rank_ic']:.4f}",
        "",
        f"Best PRICE8: {price8_best['mode']}/λ={price8_best['ridge_lambda']} "
        f"IC={price8_best['mean_rank_ic']:.4f} boot={price8_best['block_bootstrap_positive_probability']} "
        f"both={price8_best['both_gates_pass']}",
        "",
        "| feature | mode | λ | mean IC | turnover | bootstrap | both gates | CAGR | MDD |",
        "|---|---|---:|---:|---:|---:|---|---:|---:|",
    ]
    for r in result.to_dicts():
        lines.append(
            f"| {r['feature_set']} | {r['mode']} | {r['ridge_lambda']} | {r['mean_rank_ic']:.4f} | "
            f"{100*r['average_daily_turnover']:.2f}% | {r['block_bootstrap_positive_probability']:.4f} | "
            f"{r['both_gates_pass']} | {100*r['cagr']:.2f}% | {100*r['max_drawdown']:.2f}% |"
        )
    lines += [
        "",
        "## Implication",
        "",
        summary["next_step"],
        "",
        "Artifacts: `reports/stage2_model_oof_summary.json`, `outputs/stage2_model_oof_grid.csv`",
        "",
    ]
    (out / "E50-A3-R1_STAGE2_MODEL_OOF.md").write_text("\n".join(lines))
    print(json.dumps({
        "research_decision": decision,
        "baseline_bootstrap": baseline["block_bootstrap_positive_probability"],
        "n_both_pass_new_family_or_mode": len(dual_new),
        "best_price8_bootstrap": price8_best["block_bootstrap_positive_probability"],
        "best_ic": {
            "feature_set": best_ic["feature_set"],
            "mode": best_ic["mode"],
            "ridge_lambda": best_ic["ridge_lambda"],
            "mean_rank_ic": best_ic["mean_rank_ic"],
        },
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
