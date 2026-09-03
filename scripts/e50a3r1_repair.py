#!/usr/bin/env python3
"""E50-A3-R1: regime-aware, exposure-neutral, turnover-buffered repair.

All model and portfolio choices are made with embargoed 2011-2018 OOF data.
The frozen 2019-2022 validation and 2023-latest sealed periods are evaluated
only after the complete R1 configuration has been selected.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e50a3_train_exact_open as a3


FEATURE_SETS = {
    "TECH2": ["momentum_family_score", "defensive_family_score"],
    "PRICE8": [
        "pct_mom_12_1", "pct_mom_126d", "pct_mom_63d", "pct_reversal_5d",
        "pct_vol_60d", "pct_downside_vol_60d", "pct_drawdown_63d", "pct_amihud_20d",
    ],
}
MODEL_GRID = [
    (feature_set, mode, ridge)
    for feature_set in FEATURE_SETS
    for mode in ["GLOBAL", "BREADTH_REGIME"]
    for ridge in [1.0, 10.0]
]
PORTFOLIO_GRID = [
    (top_k, rebalance, exit_multiple, neutralization, industry_cap)
    for top_k in [20, 30]
    for rebalance in [5, 10, 21]
    for exit_multiple in [1.25, 1.5, 2.0]
    for neutralization in ["NONE", "INDUSTRY_LIQUIDITY"]
    for industry_cap in [3, 5]
]
BASELINE = {
    "validation_cagr": 0.014421345710669664,
    "validation_max_drawdown": -0.2793762552259741,
    "sealed_cagr": 0.22259624735024874,
    "sealed_max_drawdown": -0.21365618475204196,
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def add_regime(panel: pl.DataFrame) -> pl.DataFrame:
    daily = (
        panel.group_by("date").agg(
            (pl.col("mom_63d") > 0).mean().alias("breadth_63d"),
            (pl.col("mom_21d") > 0).mean().alias("breadth_21d"),
            pl.col("mom_63d").median().alias("market_median_mom_63d"),
        ).with_columns(
            pl.when((pl.col("breadth_63d") >= 0.50) & (pl.col("market_median_mom_63d") >= 0))
            .then(pl.lit("RISK_ON")).otherwise(pl.lit("RISK_OFF")).alias("alpha_regime")
        )
    )
    return panel.join(daily, on="date", how="left")


@dataclass
class LinearFit:
    intercept: float
    coefficients: np.ndarray
    rows: int


@dataclass
class CandidateModel:
    feature_set: str
    mode: str
    ridge_lambda: float
    fits: dict[str, LinearFit]
    fitted_through: str

    @property
    def features(self) -> list[str]:
        return FEATURE_SETS[self.feature_set]

    def predict(self, df: pl.DataFrame) -> np.ndarray:
        x = df.select([pl.col(c).fill_null(0.5) for c in self.features]).to_numpy() - 0.5
        regimes = df["alpha_regime"].to_numpy()
        out = np.empty(df.height, dtype=float)
        for key, fit in self.fits.items():
            mask = np.ones(df.height, dtype=bool) if key == "ALL" else regimes == key
            out[mask] = fit.intercept + x[mask] @ fit.coefficients
        return out

    def as_dict(self) -> dict:
        return {
            "feature_set": self.feature_set, "features": self.features, "mode": self.mode,
            "ridge_lambda": self.ridge_lambda, "fitted_through": self.fitted_through,
            "fits": {
                key: {"intercept": fit.intercept, "rows": fit.rows,
                      "coefficients": dict(zip(self.features, fit.coefficients.tolist()))}
                for key, fit in self.fits.items()
            },
        }


def fit_one(df: pl.DataFrame, features: list[str], ridge: float) -> LinearFit:
    if df.height < 5_000:
        raise ValueError(f"insufficient regime fit rows: {df.height}")
    x = df.select([pl.col(c).fill_null(0.5) for c in features]).to_numpy() - 0.5
    # Rank labels are already calculated within signal date before this call.
    y = df["target_rank"].to_numpy() - 0.5
    counts = df.group_by("date").len().select("date", pl.col("len").alias("date_n"))
    w = 1.0 / np.maximum(df.select("date").join(counts, on="date")["date_n"].to_numpy(), 1)
    w /= w.mean()
    design = np.column_stack([np.ones(df.height), x])
    gram = design.T @ (design * w[:, None])
    beta = np.linalg.solve(gram + np.diag([0.0] + [ridge] * len(features)), design.T @ (y * w))
    return LinearFit(float(beta[0]), beta[1:], df.height)


def fit_model(df: pl.DataFrame, feature_set: str, mode: str, ridge: float, cutoff: date) -> CandidateModel:
    fit = df.filter((pl.col("date") <= cutoff) & pl.col("target_rank").is_not_null())
    features = FEATURE_SETS[feature_set]
    if mode == "GLOBAL":
        fits = {"ALL": fit_one(fit, features, ridge)}
    else:
        fits = {regime: fit_one(fit.filter(pl.col("alpha_regime") == regime), features, ridge)
                for regime in ["RISK_ON", "RISK_OFF"]}
    return CandidateModel(feature_set, mode, ridge, fits, str(cutoff))


def cross_validate(joined: pl.DataFrame, calendar: list[date]) -> tuple[pl.DataFrame, dict, pl.DataFrame]:
    rows: list[dict] = []
    saved: dict[tuple[str, str, float], list[pl.DataFrame]] = {}
    for feature_set, mode, ridge in MODEL_GRID:
        pieces: list[pl.DataFrame] = []
        fold_means: list[float] = []
        for start_year, end_year in a3.CV_FOLDS:
            start = date(start_year, 1, 1); end = date(end_year, 12, 31)
            cutoff = a3.previous_session(calendar, start, 22)
            model = fit_model(joined, feature_set, mode, ridge, cutoff)
            val = joined.filter(pl.col("date").is_between(start, end))
            pred = val.select("date", "code").with_columns(pl.Series("score", model.predict(val)))
            diagnostic = pred.join(val.select("date", "code", "target_rank"), on=["date", "code"])
            ic = a3.daily_ic(diagnostic)
            mean_ic = float(ic["rank_ic"].mean())
            fold_means.append(mean_ic)
            pieces.append(pred)
            rows.append({"feature_set": feature_set, "mode": mode, "ridge_lambda": ridge,
                         "fold": f"{start_year}_{end_year}", "fit_cutoff": str(cutoff),
                         "mean_rank_ic": mean_ic, "positive_ic_rate": float((ic["rank_ic"] > 0).mean()),
                         "validation_rows": val.height})
        saved[(feature_set, mode, ridge)] = pieces
        rows.append({"feature_set": feature_set, "mode": mode, "ridge_lambda": ridge,
                     "fold": "MEAN", "fit_cutoff": None, "mean_rank_ic": float(np.mean(fold_means)),
                     "positive_ic_rate": None, "validation_rows": sum(x.height for x in pieces)})
    result = pl.DataFrame(rows)
    best = result.filter(pl.col("fold") == "MEAN").sort(
        ["mean_rank_ic", "feature_set", "mode", "ridge_lambda"], descending=[True, False, False, False]
    ).row(0, named=True)
    key = (best["feature_set"], best["mode"], float(best["ridge_lambda"]))
    return result, {"feature_set": key[0], "mode": key[1], "ridge_lambda": key[2],
                    "train_cv_mean_rank_ic": best["mean_rank_ic"]}, pl.concat(saved[key]).sort(["date", "code"])


def add_neutral_score(scored: pl.DataFrame, mode: str) -> pl.DataFrame:
    global_rank = (
        (pl.col("trading_money").rank(method="average").over("date") - 1)
        / (pl.col("trading_money").count().over("date") - 1).clip(lower_bound=1)
    )
    if mode == "NONE":
        return scored.with_columns(pl.col("score").alias("neutral_score"))
    d = scored.with_columns(
        global_rank.alias("liquidity_percentile")
    ).with_columns(
        (pl.col("liquidity_percentile") * 5).floor().clip(upper_bound=4).cast(pl.Int8).alias("liquidity_bucket"),
        (pl.col("score") - pl.col("score").median().over(["date", "industry_category"])).alias("industry_residual"),
    ).with_columns(
        (pl.col("industry_residual") - pl.col("industry_residual").median().over(["date", "liquidity_bucket"])
         + pl.col("score") * 1e-6).alias("neutral_score")
    )
    return d


def buffered_orders(scored: pl.DataFrame, calendar: list[date], top_k: int, rebalance_every: int,
                    exit_multiple: float, neutralization: str, industry_cap: int) -> pl.DataFrame:
    d = add_neutral_score(scored, neutralization)
    signal_dates = sorted(d["date"].unique().to_list())[::rebalance_every]
    next_date = {calendar[i]: calendar[i + 1] for i in range(len(calendar) - 1)}
    groups = {(day,): g for (day,), g in d.filter(pl.col("date").is_in(signal_dates)).partition_by("date", as_dict=True).items()}
    held: list[str] = []
    rows: list[dict] = []
    exit_rank = int(math.ceil(top_k * exit_multiple))
    for day in signal_dates:
        if day not in next_date or (day,) not in groups:
            continue
        candidates = (
            groups[(day,)].filter((pl.col("trading_money") >= 20_000_000) & ~pl.col("unexplained_price_jump"))
            .sort(["neutral_score", "trading_money", "code"], descending=[True, True, False])
        )
        records = candidates.iter_rows(named=True)
        ranked = []
        for i, r in enumerate(records, 1):
            r["rank"] = i; ranked.append(r)
        by_code = {r["code"]: r for r in ranked}
        selected: list[str] = []; industry_counts: dict[str, int] = {}
        for code in held:
            r = by_code.get(code)
            if r is None or r["rank"] > exit_rank:
                continue
            industry = r["industry_category"] or "UNKNOWN"
            if industry_counts.get(industry, 0) < industry_cap:
                selected.append(code); industry_counts[industry] = industry_counts.get(industry, 0) + 1
        for r in ranked:
            if len(selected) >= top_k:
                break
            code = r["code"]; industry = r["industry_category"] or "UNKNOWN"
            if code in selected or industry_counts.get(industry, 0) >= industry_cap:
                continue
            selected.append(code); industry_counts[industry] = industry_counts.get(industry, 0) + 1
        held = selected
        weight = 1.0 / len(selected) if selected else 0.0
        for rank, code in enumerate(selected, 1):
            r = by_code[code]
            rows.append({"signal_date": day, "execution_date": next_date[day], "code": code,
                         "score": float(r["score"]), "neutral_score": float(r["neutral_score"]),
                         "selection_rank": rank, "target_weight": weight})
    return pl.DataFrame(rows).sort(["execution_date", "selection_rank"])


def score_period(joined: pl.DataFrame, model: CandidateModel, start: date, end: date) -> pl.DataFrame:
    d = joined.filter(pl.col("date").is_between(start, end))
    return d.select("date", "code", "industry_category", "trading_money", "unexplained_price_jump").with_columns(
        pl.Series("score", model.predict(d))
    )


def evaluate(scored: pl.DataFrame, execution: pl.DataFrame, calendar: list[date], start: date, end: date,
             cfg: dict, name: str) -> tuple[dict, pl.DataFrame, pl.DataFrame, dict]:
    orders = buffered_orders(scored, calendar, cfg["top_k"], cfg["rebalance_every"],
                             cfg["exit_multiple"], cfg["neutralization"], cfg["industry_cap"])
    nav, trades = a3.simulate(orders, execution, start, end)
    benchmark = a3.market_proxy(execution, start, end)
    metric = a3.metrics(nav, trades, name)
    benchmark_metric = a3.metrics(benchmark, pl.DataFrame(), name + "_MARKET_PROXY")
    _, stats = a3.compare(nav, benchmark)
    return metric, nav, trades, {"benchmark_metric": benchmark_metric, "statistics": stats}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--panel", type=Path, required=True)
    p.add_argument("--prices", type=Path, required=True)
    p.add_argument("--labels", type=Path, required=True)
    p.add_argument("--actions", type=Path, required=True)
    p.add_argument("--a2-qc", type=Path, required=True)
    p.add_argument("--out", type=Path, default=Path("e50a3r1_output"))
    a = p.parse_args(); a.out.mkdir(parents=True, exist_ok=True)
    a2_qc = json.loads(a.a2_qc.read_text())
    if a2_qc["status"] != "PASS": raise RuntimeError("E50-A2 QC is not PASS")
    panel = pl.read_parquet(a.panel).sort(["date", "code"])
    source_labels = pl.read_parquet(a.labels)
    if source_labels.select(pl.struct(["date", "code"]).is_duplicated().sum()).item():
        raise RuntimeError("duplicate source research labels")
    price_scan = pl.scan_parquet(a.prices) if a.prices.suffix == ".parquet" else pl.scan_csv(
        a.prices, schema_overrides={"code": pl.String}, encoding="utf8-lossy")
    schema = price_scan.collect_schema()
    date_expr = pl.col("date") if schema["date"] == pl.Date else pl.col("date").str.to_date()
    prices = price_scan.select(date_expr.alias("date"), "code", "open", "trading_money",
                               "sessions_observed", "base_eligible").collect(engine="streaming")
    execution, partial_sessions = a3.remove_partial_market_sessions(
        a3.build_execution_panel(prices, a3.load_actions(a.actions)))
    calendar = sorted(execution["date"].unique().to_list())
    exact_labels = a3.build_exact_open_labels(panel, execution, calendar)
    joined = a3.target_rank(add_regime(panel).join(
        exact_labels.select("date", "code", a3.LABEL), on=["date", "code"], validate="1:1"))
    model_cv, selection, oof = cross_validate(joined, calendar)
    oof_scored = oof.join(joined.select("date", "code", "industry_category", "trading_money",
                                        "unexplained_price_jump"), on=["date", "code"])
    grid_rows: list[dict] = []
    for top_k, rebalance, exit_multiple, neutralization, industry_cap in PORTFOLIO_GRID:
        cfg = {"top_k": top_k, "rebalance_every": rebalance, "exit_multiple": exit_multiple,
               "neutralization": neutralization, "industry_cap": industry_cap}
        metric, _, _, _ = evaluate(oof_scored, execution, calendar, date(2011, 1, 1), date(2018, 12, 31), cfg, "TRAIN_OOF")
        metric.update(cfg)
        metric["turnover_feasible"] = metric["average_daily_turnover"] <= 0.025
        metric["utility"] = metric["cagr"] - 0.5 * abs(metric["max_drawdown"])
        grid_rows.append(metric)
    portfolio_grid = pl.DataFrame(grid_rows)
    feasible = portfolio_grid.filter(pl.col("turnover_feasible"))
    choice_pool = feasible if feasible.height else portfolio_grid
    chosen = choice_pool.sort(["utility", "cagr"], descending=True).row(0, named=True)
    config = {key: chosen[key] for key in ["top_k", "rebalance_every", "exit_multiple", "neutralization", "industry_cap"]}
    selection.update(config)

    validation_start=date(2019,1,1); validation_end=date(2022,12,31)
    sealed_start=date(2023,1,1); sealed_end=max(calendar)
    val_cutoff=a3.previous_session(calendar, validation_start, 22)
    sealed_cutoff=a3.previous_session(calendar, sealed_start, 22)
    val_model=fit_model(joined, selection["feature_set"], selection["mode"], selection["ridge_lambda"], val_cutoff)
    sealed_model=fit_model(joined, selection["feature_set"], selection["mode"], selection["ridge_lambda"], sealed_cutoff)
    metrics=[]; navs=[]; trades=[]; statistics={}; benchmarks={}; scores=[]
    for name,start,end,model in [
        ("VALIDATION_2019_2022",validation_start,validation_end,val_model),
        ("SEALED_2023_LATEST",sealed_start,sealed_end,sealed_model),
    ]:
        scored=score_period(joined,model,start,end)
        metric,nav,trade,extra=evaluate(scored,execution,calendar,start,end,selection,name)
        metrics.extend([metric,extra["benchmark_metric"]]); statistics[name]=extra["statistics"]
        benchmarks[name]=extra["benchmark_metric"]
        navs.append(nav.with_columns(pl.lit(name).alias("period")))
        trades.append(trade.with_columns(pl.lit(name).alias("period")))
        scores.append(scored.with_columns(pl.lit(name).alias("period")))
    metric_df=pl.DataFrame(metrics)
    all_nav=pl.concat(navs); all_trades=pl.concat(trades,how="diagonal_relaxed"); all_scores=pl.concat(scores)
    val=next(x for x in metrics if x["portfolio"]=="VALIDATION_2019_2022")
    sealed=next(x for x in metrics if x["portfolio"]=="SEALED_2023_LATEST")
    val_bench=benchmarks["VALIDATION_2019_2022"]; sealed_bench=benchmarks["SEALED_2023_LATEST"]
    clock_violations=all_trades.filter(pl.col("execution_date")<=pl.col("signal_date")).height
    engineering_pass=(clock_violations==0 and a2_qc["financial_lookahead_violations"]==0
                      and a2_qc["revenue_lookahead_violations"]==0)
    eligible=(engineering_pass and val["cagr"]>val_bench["cagr"] and sealed["cagr"]>sealed_bench["cagr"]
              and statistics["VALIDATION_2019_2022"]["block_bootstrap_positive_probability"]>=0.70
              and statistics["SEALED_2023_LATEST"]["block_bootstrap_positive_probability"]>=0.70)
    outputs={
        "model_cv.csv":model_cv, "train_repair_grid.csv":portfolio_grid,
        "period_metrics.csv":metric_df, "daily_nav.csv":all_nav, "trades.csv":all_trades,
    }
    for name,frame in outputs.items(): frame.write_csv(a.out/name)
    all_scores.write_parquet(a.out/"causal_scores.parquet",compression="zstd")
    model_payload={"selected_configuration":selection,"validation_model":val_model.as_dict(),"sealed_model":sealed_model.as_dict()}
    (a.out/"frozen_repair_model.json").write_text(json.dumps(model_payload,ensure_ascii=False,indent=2)+"\n")
    report={
        "version":"V4.12-E50-A3-R1","status":"PASS" if engineering_pass else "FAIL",
        "decision":"ELIGIBLE_FOR_E50_A4" if eligible else "RESEARCH_ONLY",
        "generated_at_utc":datetime.now(timezone.utc).isoformat(),"selected_configuration":selection,
        "signal_rows":panel.height,"signal_codes":panel["code"].n_unique(),"mark_to_market_rows":execution.height,
        "execution_clock_violations":clock_violations,"financial_lookahead_violations":a2_qc["financial_lookahead_violations"],
        "revenue_lookahead_violations":a2_qc["revenue_lookahead_violations"],
        "excluded_partial_market_sessions":[str(x) for x in partial_sessions["date"].to_list()],
        "metrics":metrics,"statistics":statistics,"baseline_e50a3":BASELINE,
        "delta_vs_e50a3":{"validation_cagr":val["cagr"]-BASELINE["validation_cagr"],
                           "validation_max_drawdown":val["max_drawdown"]-BASELINE["validation_max_drawdown"],
                           "sealed_cagr":sealed["cagr"]-BASELINE["sealed_cagr"],
                           "sealed_max_drawdown":sealed["max_drawdown"]-BASELINE["sealed_max_drawdown"]},
        "contracts":{"selection_data":"2011-2018 embargoed OOF only","validation":"never used for selection",
                     "signal":"T close","execution":"single T+1 raw open","risk_controller":"E45 not applied in R1"},
    }
    paths=[a.out/x for x in outputs]+[a.out/"causal_scores.parquet",a.out/"frozen_repair_model.json"]
    report["files"]={x.name:{"bytes":x.stat().st_size,"sha256":sha256(x)} for x in paths}
    (a.out/"qc_status.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=="__main__": main()
