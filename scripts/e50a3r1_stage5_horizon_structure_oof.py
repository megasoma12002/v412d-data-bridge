#!/usr/bin/env python3
"""Stage-5 OOF screen: horizon + orthogonal/defensive structure (EXPERIMENTAL).

Beyond saturated Stage-1..4 layers (portfolio rules, TECH2/PRICE8×λ, family×regime,
TECH2_VALUE F1). Selection: 2011–2018 OOF only. Portfolio FIXED to C4 wrapper.

Hypotheses:
  H1 — train on exact-open 63d labels (same portfolio eval path)
  H2 — defensive/vol structure without value tilt redo
  H3 — cross-sectional orthogonalization of momentum vs value/defensive
  H4 — simple mom×inv-vol interaction feature

Does not retune C2/C4/C8/F1. Does not modify E16/E18/E22/E44/E45.
Does not re-screen TECH2_VALUE / family recombinations / PRICE8.
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

# Feature recipes (columns must exist after attach_engineered).
FEATURE_SETS: dict[str, list[str]] = {
    "TECH2": ["momentum_family_score", "defensive_family_score"],
    "TECH2_DEF": [
        "momentum_family_score", "defensive_family_score",
        "pct_vol_60d", "pct_drawdown_63d",
    ],
    "DEF4": [
        "pct_vol_60d", "pct_downside_vol_60d", "pct_drawdown_63d", "pct_amihud_20d",
    ],
    "DEF_VALUE": [
        "defensive_family_score", "pct_vol_60d",
        "pct_book_to_price_proxy", "pct_earnings_yield_proxy",
    ],
    "DEF_ONLY": ["defensive_family_score", "pct_vol_60d", "pct_downside_vol_60d"],
    "TECH2_INTER": ["mom_x_invvol", "defensive_family_score"],
    "MOM_ORTH_VAL": ["mom_resid_vs_value", "defensive_family_score"],
    "MOM_ORTH_DEF": ["mom_resid_vs_defensive", "pct_vol_60d", "pct_drawdown_63d"],
    "ORTH_DEF_VAL": [
        "mom_resid_vs_value", "defensive_family_score",
        "pct_vol_60d", "pct_book_to_price_proxy",
    ],
}


def attach_engineered(panel: pl.DataFrame) -> pl.DataFrame:
    """Causal cross-sectional orth / interaction features (within date only)."""
    d = panel.with_columns(
        (pl.col("momentum_family_score") * (1.0 - pl.col("pct_vol_60d").fill_null(0.5)))
        .alias("mom_x_invvol")
    )

    def _add_resid(df: pl.DataFrame, y: str, x: str, out: str) -> pl.DataFrame:
        # Per-date OLS residual of y on x (intercept + slope).
        stats = (
            df.group_by("date")
            .agg(
                pl.col(y).mean().alias("_ym"),
                pl.col(x).mean().alias("_xm"),
                ((pl.col(x) - pl.col(x).mean()) * (pl.col(y) - pl.col(y).mean())).sum().alias("_sxy"),
                ((pl.col(x) - pl.col(x).mean()) ** 2).sum().alias("_sxx"),
            )
            .with_columns(
                (pl.col("_sxy") / pl.col("_sxx").clip(lower_bound=1e-12)).alias("_beta")
            )
        )
        return (
            df.join(stats.select("date", "_ym", "_xm", "_beta"), on="date", how="left")
            .with_columns(
                (pl.col(y) - pl.col("_ym") - pl.col("_beta") * (pl.col(x) - pl.col("_xm"))).alias(out)
            )
            .drop(["_ym", "_xm", "_beta"])
        )

    d = _add_resid(d, "momentum_family_score", "pct_book_to_price_proxy", "mom_resid_vs_value")
    d = _add_resid(d, "momentum_family_score", "defensive_family_score", "mom_resid_vs_defensive")
    return d


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


def build_joined(panel: pl.DataFrame, execution: pl.DataFrame, calendar: list[date], horizon: int) -> pl.DataFrame:
    labels = a3.build_exact_open_labels(panel, execution, calendar, horizon=horizon)
    # Column name remains a3.LABEL regardless of horizon (training target only).
    joined0 = a3.target_rank(
        panel.join(labels.select("date", "code", a3.LABEL), on=["date", "code"], validate="1:1")
    )
    return r1.add_regime(joined0)


def grid() -> list[dict]:
    cells = []
    # Baseline confirm (h21 TECH2)
    cells.append({"feature_set": "TECH2", "horizon": 21, "is_baseline": True})
    # H2/H3/H4 at h21
    for fs in ["TECH2_DEF", "DEF4", "DEF_VALUE", "DEF_ONLY", "TECH2_INTER", "MOM_ORTH_VAL", "MOM_ORTH_DEF", "ORTH_DEF_VAL"]:
        cells.append({"feature_set": fs, "horizon": 21, "is_baseline": False})
    # H1: horizon 63 on selected structures (+ baseline)
    for fs in ["TECH2", "TECH2_DEF", "DEF_VALUE", "TECH2_INTER", "MOM_ORTH_VAL", "ORTH_DEF_VAL"]:
        cells.append({"feature_set": fs, "horizon": 63, "is_baseline": False})
    return cells


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

    panel0 = pl.read_parquet(args.panel).sort(["date", "code"])
    panel = attach_engineered(panel0)
    needed = sorted({c for feats in FEATURE_SETS.values() for c in feats})
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

    joined_by_h: dict[int, pl.DataFrame] = {}
    cells = grid()
    print(f"screening {len(cells)} stage-5 cells on OOF ...", flush=True)
    rows = []
    for i, cell in enumerate(cells, 1):
        fs, horizon = cell["feature_set"], cell["horizon"]
        tag = f"{fs}_H{horizon}"
        print(f"[{i}/{len(cells)}] {tag} / BREADTH_REGIME / λ=1.0", flush=True)
        if horizon not in joined_by_h:
            joined_by_h[horizon] = build_joined(panel, execution, calendar, horizon)
        joined = joined_by_h[horizon]
        features = FEATURE_SETS[fs]
        scored = build_oof_scores(joined, calendar, features, "BREADTH_REGIME", 1.0)
        ic = oof_rank_ic(scored)
        port = evaluate_cfg(scored.drop(a3.LABEL), execution, calendar, dict(FIXED_PORTFOLIO))
        row = {
            "cell_id": tag,
            "feature_set": fs,
            "train_horizon": horizon,
            "mode": "BREADTH_REGIME",
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
    result.write_csv(out / "outputs" / "stage5_horizon_structure_oof_grid.csv")

    baseline = next(r for r in rows if r["is_baseline"])
    dual_new, excluded = [], []
    for r in rows:
        if not r["both_gates_pass"] or r["is_baseline"]:
            continue
        if metric_twin(r, baseline):
            excluded.append({**r, "exclude_reason": "metric_twin_of_baseline"})
            continue
        # Exclude pure TECH2_H63 if identical feature set only differs by horizon but twin-like — still allow if metrics differ
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
        "OOF_NEW_HORIZON_STRUCTURE_DUAL_GATE_WINNER"
        if winner
        else "OOF_NO_NEW_HORIZON_STRUCTURE_DUAL_GATE_WINNER"
    )

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "STAGE5_HORIZON_STRUCTURE_OOF",
        "window": "2011-2018 OOF only",
        "fixed_portfolio_reference": "C4",
        "fixed_portfolio": FIXED_PORTFOLIO,
        "hypotheses": ["H1_horizon63", "H2_defensive_structure", "H3_orthogonal_mom", "H4_mom_invvol_interaction"],
        "baseline": baseline,
        "n_cells": len(rows),
        "n_both_pass": sum(1 for r in rows if r["both_gates_pass"]),
        "n_both_pass_new": len(dual_new),
        "excluded": excluded,
        "best_ic": best_ic,
        "research_decision": decision,
        "recommended": winner,
        "top_new_dual_gate": dual_sorted[:10],
        "gates_remain_experimental": True,
        "no_retune_C2_C4_C8_F1": True,
        "no_promotion": True,
    }
    (out / "reports" / "stage5_horizon_structure_oof_summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n"
    )

    lines = [
        "# Stage-5 Horizon + Structure OOF",
        "",
        "Portfolio fixed to **C4 wrapper**. Selection: 2011–2018 OOF only.",
        "Hypotheses: train horizon 63d; defensive/vol structure; mom orthogonalization; mom×inv-vol.",
        "Does **not** redo TECH2_VALUE / family×regime / PRICE8.",
        "",
        f"## Decision: `{decision}`",
        "",
        f"Baseline TECH2_H21: IC={baseline['mean_rank_ic']:.4f}, turn={baseline['average_daily_turnover']:.4f}, "
        f"boot={baseline['block_bootstrap_positive_probability']}",
        "",
        "| cell | h | IC | turn | boot | both | CAGR | MDD |",
        "|---|---:|---:|---:|---:|---|---:|---:|",
    ]
    for r in result.to_dicts():
        lines.append(
            f"| {r['cell_id']} | {r['train_horizon']} | {r['mean_rank_ic']:.4f} | "
            f"{100 * r['average_daily_turnover']:.2f}% | {r['block_bootstrap_positive_probability']:.4f} | "
            f"{r['both_gates_pass']} | {100 * r['cagr']:.2f}% | {100 * r['max_drawdown']:.2f}% |"
        )
    if winner:
        lines += [
            "",
            "## Recommended (OOF only — not yet held-out)",
            "",
            f"- `{winner['cell_id']}` features=`{winner['features']}`",
            f"- boot `{winner['block_bootstrap_positive_probability']}`, turn `{winner['average_daily_turnover']:.4f}`, "
            f"IC `{winner['mean_rank_ic']:.4f}`",
            "",
            "Next: lock as S5A1 and run held-out once.",
            "",
        ]
    else:
        lines += [
            "",
            "No new horizon/structure dual-gate winner beyond TECH2_H21.",
            "",
        ]
    lines += ["Artifact: `reports/stage5_horizon_structure_oof_summary.json`", ""]
    (out / "E50-A3-R1_STAGE5_HORIZON_STRUCTURE_OOF.md").write_text("\n".join(lines))
    print(json.dumps({
        "research_decision": decision,
        "n_both_pass_new": len(dual_new),
        "winner": None if not winner else {
            "cell_id": winner["cell_id"],
            "feature_set": winner["feature_set"],
            "train_horizon": winner["train_horizon"],
            "bootstrap": winner["block_bootstrap_positive_probability"],
            "turnover": winner["average_daily_turnover"],
            "mean_rank_ic": winner["mean_rank_ic"],
            "features": winner["features"],
        },
        "best_ic": {
            "cell_id": best_ic["cell_id"],
            "mean_rank_ic": best_ic["mean_rank_ic"],
            "both": best_ic["both_gates_pass"],
            "boot": best_ic["block_bootstrap_positive_probability"],
        },
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
