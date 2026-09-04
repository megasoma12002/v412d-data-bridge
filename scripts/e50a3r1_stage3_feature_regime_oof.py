#!/usr/bin/env python3
"""Stage-3 OOF screen: new feature families + new regime definitions.

Selection window: 2011–2018 OOF only.
Portfolio wrapper FIXED to C4 (reference; not retuned).
Does not modify E16/E18/E22/E44/E45 or locked C2/C4/C8 configs.
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
    TURNOVER_CEILING,
    buffered_orders_ext,
    evaluate_cfg,
)

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

# Experimental feature families (beyond TECH2/PRICE8 stage-2 grid).
EXPERIMENTAL_FEATURES = {
    "TECH2": ["momentum_family_score", "defensive_family_score"],  # baseline
    "VALUE2": ["value_family_score", "defensive_family_score"],
    "QUALITY2": ["quality_family_score", "defensive_family_score"],
    "GROWTH2": ["growth_family_score", "momentum_family_score"],
    "VAL_MOM": ["value_family_score", "momentum_family_score"],
    "QUAL_VAL": ["quality_family_score", "value_family_score"],
    "FAMILY3": ["momentum_family_score", "quality_family_score", "growth_family_score"],
    "FAMILY5": [
        "momentum_family_score", "defensive_family_score",
        "quality_family_score", "growth_family_score", "value_family_score",
    ],
}

REGIME_NAMES = [
    "BREADTH_BASE",
    "BREADTH_STRICT55",
    "BREADTH_21",
    "TREND_ONLY",
    "VOL_REGIME",
]


def attach_regime(panel: pl.DataFrame, regime_name: str) -> pl.DataFrame:
    """Attach experimental alpha_regime; drops prior regime cols if present."""
    drop = [c for c in panel.columns if c in {
        "breadth_63d", "breadth_21d", "market_median_mom_63d", "market_median_mom_21d",
        "market_median_vol_60d", "alpha_regime", "vol_high",
    }]
    base = panel.drop(drop) if drop else panel
    daily = base.group_by("date").agg(
        (pl.col("mom_63d") > 0).mean().alias("breadth_63d"),
        (pl.col("mom_21d") > 0).mean().alias("breadth_21d"),
        pl.col("mom_63d").median().alias("market_median_mom_63d"),
        pl.col("mom_21d").median().alias("market_median_mom_21d"),
        pl.col("vol_60d").median().alias("market_median_vol_60d"),
    )
    # Rolling-ish high-vol flag via expanding median of daily median vol (causal: shift 1).
    daily = daily.sort("date").with_columns(
        pl.col("market_median_vol_60d").shift(1).rolling_median(window_size=63, min_samples=21)
        .alias("vol_med_ref")
    )
    if regime_name == "BREADTH_BASE":
        daily = daily.with_columns(
            pl.when((pl.col("breadth_63d") >= 0.50) & (pl.col("market_median_mom_63d") >= 0))
            .then(pl.lit("RISK_ON")).otherwise(pl.lit("RISK_OFF")).alias("alpha_regime")
        )
    elif regime_name == "BREADTH_STRICT55":
        daily = daily.with_columns(
            pl.when((pl.col("breadth_63d") >= 0.55) & (pl.col("market_median_mom_63d") >= 0))
            .then(pl.lit("RISK_ON")).otherwise(pl.lit("RISK_OFF")).alias("alpha_regime")
        )
    elif regime_name == "BREADTH_21":
        daily = daily.with_columns(
            pl.when((pl.col("breadth_21d") >= 0.50) & (pl.col("market_median_mom_21d") >= 0))
            .then(pl.lit("RISK_ON")).otherwise(pl.lit("RISK_OFF")).alias("alpha_regime")
        )
    elif regime_name == "TREND_ONLY":
        daily = daily.with_columns(
            pl.when(pl.col("market_median_mom_63d") >= 0)
            .then(pl.lit("RISK_ON")).otherwise(pl.lit("RISK_OFF")).alias("alpha_regime")
        )
    elif regime_name == "VOL_REGIME":
        # High vol vs recent median -> RISK_OFF; else RISK_ON if breadth ok.
        daily = daily.with_columns(
            pl.when(
                pl.col("vol_med_ref").is_not_null()
                & (pl.col("market_median_vol_60d") > pl.col("vol_med_ref"))
            )
            .then(pl.lit("RISK_OFF"))
            .when((pl.col("breadth_63d") >= 0.50) & (pl.col("market_median_mom_63d") >= 0))
            .then(pl.lit("RISK_ON"))
            .otherwise(pl.lit("RISK_OFF"))
            .alias("alpha_regime")
        )
    else:
        raise ValueError(regime_name)
    return base.join(
        daily.select("date", "breadth_63d", "breadth_21d", "market_median_mom_63d",
                     "market_median_mom_21d", "market_median_vol_60d", "alpha_regime"),
        on="date", how="left",
    )


def fit_model_exp(df: pl.DataFrame, features: list[str], mode: str, ridge: float, cutoff: date) -> r1.CandidateModel:
    # Reuse CandidateModel shell with patched feature list via temporary FEATURE_SETS entry.
    key = "EXP_TMP"
    r1.FEATURE_SETS[key] = features
    model = r1.fit_model(df, key, mode, ridge, cutoff)
    return model


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


def grid() -> list[dict]:
    cells = []
    # Baseline confirm
    cells.append({"feature_set": "TECH2", "regime": "BREADTH_BASE", "mode": "BREADTH_REGIME", "ridge_lambda": 1.0, "is_baseline": True})
    cells.append({"feature_set": "TECH2", "regime": "BREADTH_BASE", "mode": "GLOBAL", "ridge_lambda": 1.0, "is_baseline": False})
    for fs in EXPERIMENTAL_FEATURES:
        for regime in REGIME_NAMES:
            if fs == "TECH2" and regime == "BREADTH_BASE":
                continue  # already covered
            cells.append({
                "feature_set": fs,
                "regime": regime,
                "mode": "BREADTH_REGIME",  # regime-aware fit using attached alpha_regime
                "ridge_lambda": 1.0,
                "is_baseline": False,
            })
    # A few GLOBAL probes on new families under BASE market (no regime split)
    for fs in ["VALUE2", "QUALITY2", "FAMILY3", "FAMILY5"]:
        cells.append({
            "feature_set": fs, "regime": "BREADTH_BASE", "mode": "GLOBAL",
            "ridge_lambda": 1.0, "is_baseline": False,
        })
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

    panel = pl.read_parquet(args.panel).sort(["date", "code"])
    # Ensure family scores exist
    for c in [
        "momentum_family_score", "defensive_family_score", "quality_family_score",
        "growth_family_score", "value_family_score", "mom_21d", "mom_63d", "vol_60d",
    ]:
        if c not in panel.columns:
            raise RuntimeError(f"missing column {c}")

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

    cells = grid()
    print(f"screening {len(cells)} feature×regime cells on OOF ...", flush=True)
    rows = []
    # Cache joined panels by regime
    joined_by_regime: dict[str, pl.DataFrame] = {}
    for i, cell in enumerate(cells, 1):
        fs, regime, mode, lam = cell["feature_set"], cell["regime"], cell["mode"], cell["ridge_lambda"]
        print(f"[{i}/{len(cells)}] {fs} / {regime} / {mode} / λ={lam}", flush=True)
        if regime not in joined_by_regime:
            joined_by_regime[regime] = attach_regime(joined0, regime)
        joined = joined_by_regime[regime]
        features = EXPERIMENTAL_FEATURES[fs]
        scored = build_oof_scores(joined, calendar, features, mode, lam)
        ic = oof_rank_ic(scored)
        cfg = dict(FIXED_PORTFOLIO)
        port = evaluate_cfg(scored.drop(a3.LABEL), execution, calendar, cfg)
        # Regime balance on OOF
        reg_bal = joined.filter(pl.col("date").is_between(date(2011, 1, 1), date(2018, 12, 31))).select(
            "date", "alpha_regime"
        ).unique(subset=["date"])
        risk_on_share = float((reg_bal["alpha_regime"] == "RISK_ON").mean()) if reg_bal.height else None
        row = {
            "feature_set": fs,
            "regime_definition": regime,
            "mode": mode,
            "ridge_lambda": lam,
            "is_baseline": bool(cell["is_baseline"]),
            "n_features": len(features),
            "features": ",".join(features),
            "oof_risk_on_day_share": risk_on_share,
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
            f"boot={row['block_bootstrap_positive_probability']} both={row['both_gates_pass']} "
            f"risk_on_share={risk_on_share}",
            flush=True,
        )

    result = pl.DataFrame(rows).sort(
        ["both_gates_pass", "block_bootstrap_positive_probability", "mean_rank_ic"],
        descending=[True, True, True],
    )
    result.write_csv(out / "outputs" / "stage3_feature_regime_oof_grid.csv")

    baseline = next(r for r in rows if r["is_baseline"])

    # Regime degeneracy vs BREADTH_BASE on OOF (identical RISK_ON day set).
    base_reg_days = (
        joined_by_regime["BREADTH_BASE"]
        .filter(pl.col("date").is_between(date(2011, 1, 1), date(2018, 12, 31)))
        .select("date", "alpha_regime")
        .unique(subset=["date"])
        .sort("date")
    )
    regime_degeneracy: dict[str, dict] = {}
    for rname, jreg in joined_by_regime.items():
        if rname == "BREADTH_BASE":
            continue
        other = (
            jreg.filter(pl.col("date").is_between(date(2011, 1, 1), date(2018, 12, 31)))
            .select("date", "alpha_regime")
            .unique(subset=["date"])
            .sort("date")
        )
        merged = base_reg_days.join(other, on="date", suffix="_x")
        n_dis = int((merged["alpha_regime"] != merged["alpha_regime_x"]).sum())
        regime_degeneracy[rname] = {
            "oof_days": merged.height,
            "disagree_vs_breadth_base": n_dis,
            "identical_to_breadth_base": n_dis == 0,
        }

    def _metric_twin(r: dict) -> bool:
        """Same OOF portfolio/IC fingerprint as baseline (degenerate challenger)."""
        keys = (
            "mean_rank_ic", "average_daily_turnover",
            "block_bootstrap_positive_probability", "cagr", "max_drawdown",
            "mean_daily_excess", "oof_risk_on_day_share",
        )
        return all(
            r.get(k) is not None and baseline.get(k) is not None
            and abs(float(r[k]) - float(baseline[k])) < 1e-12
            for k in keys
        )

    # New winner: dual-gate, not baseline, not regime-degenerate TECH2 twin, not metric twin.
    dual_new = []
    dual_excluded_degenerate = []
    for r in rows:
        if not r["both_gates_pass"]:
            continue
        if r["feature_set"] == "TECH2" and r["regime_definition"] == "BREADTH_BASE":
            continue
        deg = regime_degeneracy.get(r["regime_definition"], {})
        if deg.get("identical_to_breadth_base") and r["feature_set"] == "TECH2":
            dual_excluded_degenerate.append(
                {**r, "exclude_reason": "regime_identical_to_BREADTH_BASE_on_OOF"}
            )
            continue
        if _metric_twin(r):
            dual_excluded_degenerate.append({**r, "exclude_reason": "metric_twin_of_baseline"})
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
    best_ic = sorted(rows, key=lambda r: -(r["mean_rank_ic"] or -9))[0]
    winner = dual_sorted[0] if dual_sorted else None
    decision = (
        "OOF_NEW_FEATURE_REGIME_DUAL_GATE_WINNER"
        if winner
        else "OOF_NO_NEW_FEATURE_REGIME_DUAL_GATE_WINNER"
    )

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "STAGE3_FEATURE_REGIME_OOF",
        "window": "2011-2018 OOF only",
        "fixed_portfolio_reference": "C4",
        "fixed_portfolio": FIXED_PORTFOLIO,
        "baseline": baseline,
        "n_cells": len(rows),
        "n_both_pass": sum(1 for r in rows if r["both_gates_pass"]),
        "n_both_pass_new": len(dual_new),
        "n_both_pass_excluded_degenerate": len(dual_excluded_degenerate),
        "regime_degeneracy_vs_breadth_base": regime_degeneracy,
        "excluded_degenerate_dual_gate": dual_excluded_degenerate,
        "best_ic": best_ic,
        "research_decision": decision,
        "recommended": winner,
        "top_new_dual_gate": dual_sorted[:10],
        "gates_remain_experimental": True,
        "no_retune_C2_C4_C8": True,
        "no_promotion": True,
    }
    (out / "reports" / "stage3_feature_regime_oof_summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n"
    )

    lines = [
        "# Stage-3 New Feature Families × Regime Definitions (OOF)",
        "",
        "Portfolio fixed to **C4 wrapper**. Selection: 2011–2018 OOF only.",
        "",
        f"## Decision: `{decision}`",
        "",
        f"Baseline TECH2 / BREADTH_BASE / BREADTH_REGIME: "
        f"IC={baseline['mean_rank_ic']:.4f}, turn={baseline['average_daily_turnover']:.4f}, "
        f"boot={baseline['block_bootstrap_positive_probability']}",
        "",
        "### Regime degeneracy vs BREADTH_BASE (OOF day labels)",
        "",
    ]
    for rname, info in sorted(regime_degeneracy.items()):
        lines.append(
            f"- `{rname}`: disagree={info['disagree_vs_breadth_base']}/{info['oof_days']}"
            + (" — **identical (not a new regime)**" if info["identical_to_breadth_base"] else "")
        )
    if dual_excluded_degenerate:
        lines += ["", "Excluded dual-gate twins (not counted as new winners):", ""]
        for r in dual_excluded_degenerate:
            lines.append(
                f"- `{r['feature_set']}` / `{r['regime_definition']}` — {r['exclude_reason']}"
            )
    lines += [
        "",
        "| feature | regime | mode | IC | turn | boot | both | CAGR | MDD | risk_on_share |",
        "|---|---|---|---:|---:|---:|---|---:|---:|---:|",
    ]
    for r in result.to_dicts():
        lines.append(
            f"| {r['feature_set']} | {r['regime_definition']} | {r['mode']} | {r['mean_rank_ic']:.4f} | "
            f"{100*r['average_daily_turnover']:.2f}% | {r['block_bootstrap_positive_probability']:.4f} | "
            f"{r['both_gates_pass']} | {100*r['cagr']:.2f}% | {100*r['max_drawdown']:.2f}% | "
            f"{r['oof_risk_on_day_share']:.3f} |"
        )
    if winner:
        lines += [
            "",
            "## Recommended (OOF only — not yet held-out)",
            "",
            f"- feature `{winner['feature_set']}`, regime `{winner['regime_definition']}`, mode `{winner['mode']}`",
            f"- boot `{winner['block_bootstrap_positive_probability']}`, turn `{winner['average_daily_turnover']:.4f}`, "
            f"IC `{winner['mean_rank_ic']:.4f}`",
            "",
            "Next: lock as FR1 and run held-out once (optional follow-up).",
            "",
        ]
    else:
        lines += [
            "",
            "No **genuinely new** feature×regime dual-gate winner beyond TECH2/BREADTH_BASE.",
            "VALUE2/QUALITY2/GROWTH2/FAMILY* and non-degenerate regimes all fail OOF bootstrap.",
            "Do **not** held-out TREND_ONLY (OOF-identical to BREADTH_BASE).",
            "",
        ]
    lines += ["", "Artifact: `reports/stage3_feature_regime_oof_summary.json`", ""]
    (out / "E50-A3-R1_STAGE3_FEATURE_REGIME_OOF.md").write_text("\n".join(lines))
    print(json.dumps({
        "research_decision": decision,
        "n_both_pass_new": len(dual_new),
        "n_both_pass_excluded_degenerate": len(dual_excluded_degenerate),
        "regime_degeneracy_vs_breadth_base": regime_degeneracy,
        "baseline_boot": baseline["block_bootstrap_positive_probability"],
        "winner": None if not winner else {
            "feature_set": winner["feature_set"],
            "regime": winner["regime_definition"],
            "mode": winner["mode"],
            "bootstrap": winner["block_bootstrap_positive_probability"],
            "turnover": winner["average_daily_turnover"],
            "mean_rank_ic": winner["mean_rank_ic"],
        },
        "best_ic": {
            "feature_set": best_ic["feature_set"],
            "regime": best_ic["regime_definition"],
            "mean_rank_ic": best_ic["mean_rank_ic"],
            "both": best_ic["both_gates_pass"],
            "boot": best_ic["block_bootstrap_positive_probability"],
        },
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
