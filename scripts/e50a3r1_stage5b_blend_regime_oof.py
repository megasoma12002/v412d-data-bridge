#!/usr/bin/env python3
"""Stage-5B OOF: score blends + regime-conditional feature switch (EXPERIMENTAL).

Follow-up after Stage-5A found no dual-gate winner (best near-miss MOM_ORTH_DEF
boot≈0.66). Selection: 2011–2018 OOF only. C4 portfolio wrapper fixed.

Does not retune C2/C4/C8/F1. Does not modify E16/E18/E22/E44/E45.
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
from e50a3r1_stage5_horizon_structure_oof import attach_engineered, FEATURE_SETS as S5_FEATURES

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

TECH2 = ["momentum_family_score", "defensive_family_score"]
DEF4 = ["pct_vol_60d", "pct_downside_vol_60d", "pct_drawdown_63d", "pct_amihud_20d"]
MOM_ORTH_DEF = S5_FEATURES["MOM_ORTH_DEF"]


def fit_exp(df, features, mode, ridge, cutoff):
    r1.FEATURE_SETS["EXP_TMP"] = features
    return r1.fit_model(df, "EXP_TMP", mode, ridge, cutoff)


def oof_scores_for_features(joined, calendar, features, mode="BREADTH_REGIME", ridge=1.0):
    pieces = []
    for start_year, end_year in a3.CV_FOLDS:
        start, end = date(start_year, 1, 1), date(end_year, 12, 31)
        cutoff = a3.previous_session(calendar, start, 22)
        model = fit_exp(joined, features, mode, ridge, cutoff)
        val = joined.filter(pl.col("date").is_between(start, end))
        pieces.append(
            val.select(
                "date", "code", "industry_category", "trading_money", "unexplained_price_jump",
                a3.LABEL, "alpha_regime",
            ).with_columns(pl.Series("score", model.predict(val)))
        )
    return pl.concat(pieces).sort(["date", "code"])


def oof_rank_ic(scored: pl.DataFrame) -> dict:
    ics = []
    for day in scored["date"].unique().to_list():
        g = scored.filter(pl.col("date") == day).drop_nulls([a3.LABEL, "score"])
        if g.height < 30:
            continue
        sr, lr = g["score"].rank().to_numpy(), g[a3.LABEL].rank().to_numpy()
        if np.std(sr) == 0 or np.std(lr) == 0:
            continue
        ics.append(float(np.corrcoef(sr, lr)[0, 1]))
    return {
        "n_days": len(ics),
        "mean_rank_ic": float(np.mean(ics)) if ics else None,
        "p50_rank_ic": float(np.quantile(ics, 0.50)) if ics else None,
    }


def blend_scores(a: pl.DataFrame, b: pl.DataFrame, w_a: float) -> pl.DataFrame:
    j = a.select("date", "code", "industry_category", "trading_money", "unexplained_price_jump", a3.LABEL, "score").join(
        b.select("date", "code", pl.col("score").alias("score_b")),
        on=["date", "code"], validate="1:1",
    )
    return j.with_columns(
        (w_a * pl.col("score") + (1.0 - w_a) * pl.col("score_b")).alias("score")
    ).drop("score_b")


def regime_pick_scores(on_df: pl.DataFrame, off_df: pl.DataFrame) -> pl.DataFrame:
    """Use ON-model score on RISK_ON days and OFF-model score on RISK_OFF days."""
    j = on_df.select(
        "date", "code", "industry_category", "trading_money", "unexplained_price_jump",
        a3.LABEL, "alpha_regime", "score",
    ).join(
        off_df.select("date", "code", pl.col("score").alias("score_off")),
        on=["date", "code"], validate="1:1",
    )
    return j.with_columns(
        pl.when(pl.col("alpha_regime") == "RISK_ON")
        .then(pl.col("score"))
        .otherwise(pl.col("score_off"))
        .alias("score")
    ).drop("score_off")


def eval_cell(name, scored, execution, calendar, baseline_boot=None):
    ic = oof_rank_ic(scored)
    port = evaluate_cfg(scored.drop([c for c in [a3.LABEL, "alpha_regime"] if c in scored.columns]), execution, calendar, dict(FIXED_PORTFOLIO))
    row = {
        "cell_id": name,
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
    ic_s = "None" if row["mean_rank_ic"] is None else f"{row['mean_rank_ic']:.4f}"
    print(
        f"  {name}: IC={ic_s} turn={row['average_daily_turnover']:.4f} "
        f"boot={row['block_bootstrap_positive_probability']} both={row['both_gates_pass']}",
        flush=True,
    )
    return row


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

    if json.loads(args.a2_qc.read_text())["status"] != "PASS":
        raise RuntimeError("E50-A2 QC is not PASS")

    panel = attach_engineered(pl.read_parquet(args.panel).sort(["date", "code"]))
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
    labels = a3.build_exact_open_labels(panel, execution, calendar, horizon=21)
    joined = a3.target_rank(
        r1.add_regime(panel).join(labels.select("date", "code", a3.LABEL), on=["date", "code"], validate="1:1")
    )

    print("building base OOF scores ...", flush=True)
    s_tech2 = oof_scores_for_features(joined, calendar, TECH2)
    s_def4 = oof_scores_for_features(joined, calendar, DEF4)
    s_orth = oof_scores_for_features(joined, calendar, MOM_ORTH_DEF)

    rows = []
    print("baseline TECH2", flush=True)
    rows.append({**eval_cell("TECH2", s_tech2, execution, calendar), "is_baseline": True, "family": "baseline"})

    for w, name in [(0.7, "BLEND_TECH2_70_DEF4_30"), (0.5, "BLEND_TECH2_50_DEF4_50"), (0.3, "BLEND_TECH2_30_DEF4_70")]:
        print(f"blend w_tech2={w}", flush=True)
        rows.append({
            **eval_cell(name, blend_scores(s_tech2, s_def4, w), execution, calendar),
            "is_baseline": False, "family": "blend",
        })
    print("blend TECH2 + MOM_ORTH_DEF 50/50", flush=True)
    rows.append({
        **eval_cell("BLEND_TECH2_50_ORTHDEF_50", blend_scores(s_tech2, s_orth, 0.5), execution, calendar),
        "is_baseline": False, "family": "blend",
    })

    print("regime pick TECH2(ON)/DEF4(OFF)", flush=True)
    rows.append({
        **eval_cell(
            "REGIME_PICK_TECH2_ON_DEF4_OFF",
            regime_pick_scores(s_tech2, s_def4),
            execution, calendar,
        ),
        "is_baseline": False, "family": "regime_pick",
    })
    print("regime pick TECH2(ON)/MOM_ORTH_DEF(OFF)", flush=True)
    rows.append({
        **eval_cell(
            "REGIME_PICK_TECH2_ON_ORTHDEF_OFF",
            regime_pick_scores(s_tech2, s_orth),
            execution, calendar,
        ),
        "is_baseline": False, "family": "regime_pick",
    })
    print("regime pick DEF4(ON)/TECH2(OFF) — inverted probe", flush=True)
    rows.append({
        **eval_cell(
            "REGIME_PICK_DEF4_ON_TECH2_OFF",
            regime_pick_scores(s_def4, s_tech2),
            execution, calendar,
        ),
        "is_baseline": False, "family": "regime_pick_probe",
    })

    result = pl.DataFrame(rows).sort(
        ["both_gates_pass", "block_bootstrap_positive_probability", "mean_rank_ic"],
        descending=[True, True, True],
    )
    result.write_csv(out / "outputs" / "stage5b_blend_regime_oof_grid.csv")

    baseline = next(r for r in rows if r["is_baseline"])
    dual_new = [r for r in rows if r["both_gates_pass"] and not r["is_baseline"]]
    dual_sorted = sorted(
        dual_new,
        key=lambda r: (-(r["block_bootstrap_positive_probability"] or 0), -(r["mean_rank_ic"] or -9)),
    )
    winner = dual_sorted[0] if dual_sorted else None
    decision = (
        "OOF_NEW_BLEND_REGIME_DUAL_GATE_WINNER"
        if winner
        else "OOF_NO_NEW_BLEND_REGIME_DUAL_GATE_WINNER"
    )
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "STAGE5B_BLEND_REGIME_OOF",
        "window": "2011-2018 OOF only",
        "fixed_portfolio_reference": "C4",
        "baseline": {k: baseline[k] for k in baseline if k != "family"},
        "n_cells": len(rows),
        "n_both_pass_new": len(dual_new),
        "research_decision": decision,
        "recommended": winner,
        "top_new_dual_gate": dual_sorted[:5],
        "gates_remain_experimental": True,
        "no_retune_C2_C4_C8_F1": True,
        "no_promotion": True,
    }
    (out / "reports" / "stage5b_blend_regime_oof_summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n"
    )
    lines = [
        "# Stage-5B Score Blend + Regime-Conditional OOF",
        "",
        "C4 wrapper fixed. 2011–2018 OOF only. Follow-up to Stage-5A (no dual-gate winner).",
        "",
        f"## Decision: `{decision}`",
        "",
        "| cell | IC | turn | boot | both | CAGR | MDD |",
        "|---|---:|---:|---:|---|---:|---:|",
    ]
    for r in result.to_dicts():
        lines.append(
            f"| {r['cell_id']} | {r['mean_rank_ic']:.4f} | {100*r['average_daily_turnover']:.2f}% | "
            f"{r['block_bootstrap_positive_probability']:.4f} | {r['both_gates_pass']} | "
            f"{100*r['cagr']:.2f}% | {100*r['max_drawdown']:.2f}% |"
        )
    if winner:
        lines += ["", f"Recommended: `{winner['cell_id']}` — lock S5B1 and held-out once.", ""]
    else:
        lines += ["", "No new blend/regime-switch dual-gate winner.", ""]
    lines += ["Artifact: `reports/stage5b_blend_regime_oof_summary.json`", ""]
    (out / "E50-A3-R1_STAGE5B_BLEND_REGIME_OOF.md").write_text("\n".join(lines))
    print(json.dumps({
        "research_decision": decision,
        "n_both_pass_new": len(dual_new),
        "winner": None if not winner else {
            "cell_id": winner["cell_id"],
            "boot": winner["block_bootstrap_positive_probability"],
            "turn": winner["average_daily_turnover"],
            "ic": winner["mean_rank_ic"],
        },
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
