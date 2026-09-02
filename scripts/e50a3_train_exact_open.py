#!/usr/bin/env python3
"""V4.12-E50-A3 causal alpha training and exact T+1-open simulation.

The model reads only T-close point-in-time features.  Forward labels are kept
in a separate frame and are joined only inside the trainer.  A target produced
on signal date T can first trade at the next market session's raw open.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl


FAMILY_SETS = {
    "TECH2": ["momentum_family_score", "defensive_family_score"],
    "FAMILY3": ["momentum_family_score", "quality_family_score", "growth_family_score"],
    "FAMILY4": [
        "momentum_family_score", "defensive_family_score",
        "quality_family_score", "growth_family_score",
    ],
}
LAMBDAS = [0.1, 1.0, 10.0]
CV_FOLDS = [(2011, 2012), (2013, 2014), (2015, 2016), (2017, 2018)]
PORTFOLIO_GRID = [(20, 5), (30, 5), (50, 5), (30, 10), (50, 10), (50, 21)]
LABEL = "exact_fwd_21d_open_return"
BUY_COMMISSION = 0.001425
SELL_COMMISSION = 0.001425
SELL_TAX = 0.003
BASE_SLIPPAGE = 0.0005


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def previous_session(dates: list[date], first_date: date, sessions: int = 22) -> date:
    i = int(np.searchsorted(np.asarray(dates, dtype="datetime64[D]"), np.datetime64(first_date)))
    return dates[max(0, i - sessions)]


def target_rank(df: pl.DataFrame) -> pl.DataFrame:
    return df.with_columns(
        pl.when(pl.col(LABEL).is_not_null())
        .then(
            (pl.col(LABEL).rank(method="average").over("date") - 1.0)
            / (pl.col(LABEL).count().over("date") - 1.0).clip(lower_bound=1.0)
        ).otherwise(None).alias("target_rank")
    )


@dataclass
class RidgeModel:
    feature_set: str
    features: list[str]
    ridge_lambda: float
    intercept: float
    coefficients: np.ndarray
    fitted_through: str

    def predict(self, df: pl.DataFrame) -> np.ndarray:
        x = df.select([pl.col(c).fill_null(0.5) for c in self.features]).to_numpy()
        return self.intercept + (x - 0.5) @ self.coefficients

    def as_dict(self) -> dict:
        return {
            "feature_set": self.feature_set,
            "features": self.features,
            "ridge_lambda": self.ridge_lambda,
            "intercept": self.intercept,
            "coefficients": dict(zip(self.features, self.coefficients.tolist())),
            "fitted_through": self.fitted_through,
        }


def fit_ridge(df: pl.DataFrame, feature_set: str, ridge_lambda: float, cutoff: date) -> RidgeModel:
    features = FAMILY_SETS[feature_set]
    fit = df.filter((pl.col("date") <= cutoff) & pl.col("target_rank").is_not_null())
    if fit.height < 10_000:
        raise ValueError(f"insufficient fit rows through {cutoff}: {fit.height}")
    x = fit.select([pl.col(c).fill_null(0.5) for c in features]).to_numpy() - 0.5
    y = fit["target_rank"].to_numpy() - 0.5
    counts = fit.group_by("date").len().select("date", pl.col("len").alias("date_n"))
    w = fit.select("date").join(counts, on="date", how="left")["date_n"].to_numpy()
    w = 1.0 / np.maximum(w, 1)
    w /= w.mean()
    design = np.column_stack([np.ones(len(x)), x])
    gram = design.T @ (design * w[:, None])
    penalty = np.diag([0.0] + [ridge_lambda] * len(features))
    beta = np.linalg.solve(gram + penalty, design.T @ (y * w))
    return RidgeModel(feature_set, features, ridge_lambda, float(beta[0]), beta[1:], str(cutoff))


def daily_ic(scored: pl.DataFrame) -> pl.DataFrame:
    return (
        scored.filter(pl.col("score").is_not_null() & pl.col("target_rank").is_not_null())
        .group_by("date")
        .agg(pl.len().alias("n"), pl.corr("score", "target_rank", method="spearman").alias("rank_ic"))
        .filter(pl.col("n") >= 30)
        .sort("date")
    )


def cross_validate(joined: pl.DataFrame, dates: list[date]) -> tuple[pl.DataFrame, pl.DataFrame, dict]:
    summaries: list[dict] = []
    candidate_oof: dict[tuple[str, float], list[pl.DataFrame]] = {}
    for feature_set in FAMILY_SETS:
        for lam in LAMBDAS:
            pieces: list[pl.DataFrame] = []
            fold_ics: list[float] = []
            for start_year, end_year in CV_FOLDS:
                start = date(start_year, 1, 1)
                end = date(end_year, 12, 31)
                cutoff = previous_session(dates, start, 22)
                model = fit_ridge(joined, feature_set, lam, cutoff)
                val = joined.filter(pl.col("date").is_between(start, end))
                pred = val.select("date", "code").with_columns(pl.Series("score", model.predict(val)))
                pred = pred.join(val.select("date", "code", "target_rank"), on=["date", "code"])
                ic = daily_ic(pred)
                fold_ic = float(ic["rank_ic"].mean()) if ic.height else float("nan")
                fold_ics.append(fold_ic)
                pieces.append(pred.select("date", "code", "score"))
                summaries.append({
                    "feature_set": feature_set, "ridge_lambda": lam,
                    "fold": f"{start_year}_{end_year}", "fit_cutoff": str(cutoff),
                    "validation_rows": val.height, "daily_ic_observations": ic.height,
                    "mean_rank_ic": fold_ic,
                    "positive_ic_rate": float((ic["rank_ic"] > 0).mean()) if ic.height else None,
                })
            candidate_oof[(feature_set, lam)] = pieces
            summaries.append({
                "feature_set": feature_set, "ridge_lambda": lam, "fold": "MEAN",
                "fit_cutoff": None, "validation_rows": sum(x.height for x in pieces),
                "daily_ic_observations": None, "mean_rank_ic": float(np.nanmean(fold_ics)),
                "positive_ic_rate": None,
            })
    summary = pl.DataFrame(summaries)
    means = summary.filter(pl.col("fold") == "MEAN").sort(
        ["mean_rank_ic", "feature_set", "ridge_lambda"], descending=[True, False, False]
    )
    best = means.row(0, named=True)
    key = (best["feature_set"], float(best["ridge_lambda"]))
    oof = pl.concat(candidate_oof[key]).sort(["date", "code"])
    return summary, oof, {"feature_set": key[0], "ridge_lambda": key[1], "train_cv_mean_rank_ic": best["mean_rank_ic"]}


def load_actions(path: Path) -> pl.DataFrame:
    d = pl.read_csv(path, schema_overrides={"stock_id": pl.String}, try_parse_dates=True)
    if d.is_empty():
        return pl.DataFrame(schema={"code": pl.String, "date": pl.Date, "cash_action": pl.Float64, "share_multiplier": pl.Float64})
    return (
        d.with_columns(
            pl.col("effective_date").cast(pl.Date).alias("date"),
            pl.col("cash_per_old_share").cast(pl.Float64, strict=False).fill_null(0.0),
            pl.col("share_multiplier").cast(pl.Float64, strict=False).fill_null(1.0),
        ).filter(pl.col("date").is_not_null())
        .group_by([pl.col("stock_id").alias("code"), "date"])
        .agg(
            pl.col("cash_per_old_share").sum().alias("cash_action"),
            pl.when(pl.col("event_type").is_in(["split_or_reverse_split", "par_value_change"]))
            .then(pl.col("share_multiplier")).otherwise(None).max().fill_null(1.0).alias("structural_multiplier"),
            pl.when(pl.col("event_type").is_in(["stock_dividend", "capital_reduction"]))
            .then(pl.col("share_multiplier")).otherwise(1.0).product().alias("other_multiplier"),
        ).with_columns((pl.col("structural_multiplier") * pl.col("other_multiplier")).alias("share_multiplier"))
        .select("code", "date", "cash_action", "share_multiplier")
    )


def build_execution_panel(prices: pl.DataFrame, actions: pl.DataFrame) -> pl.DataFrame:
    execution = (
        prices.select("date", "code", "open", "trading_money", "sessions_observed", "base_eligible")
        .sort(["code", "date"])
        .join(actions, on=["date", "code"], how="left")
        .with_columns(
            pl.col("cash_action").fill_null(0.0), pl.col("share_multiplier").fill_null(1.0),
            pl.col("open").shift(1).over("code").alias("previous_open"),
        ).with_columns(
            pl.when(pl.col("previous_open").is_not_null() & (pl.col("previous_open") > 0))
            .then((pl.col("open") * pl.col("share_multiplier") + pl.col("cash_action")) / pl.col("previous_open") - 1.0)
            .otherwise(None).alias("open_total_return")
        ).with_columns(
            (
                (pl.col("sessions_observed") > 20)
                & (pl.col("cash_action") == 0.0)
                & (pl.col("share_multiplier") == 1.0)
                & (pl.col("open_total_return").abs() > 0.5)
            ).fill_null(False).alias("unexplained_price_jump")
        ).with_columns(
            pl.when(pl.col("unexplained_price_jump")).then(0.0)
            .otherwise(pl.col("open_total_return")).alias("open_total_return")
        ).with_columns(
            (pl.col("open_total_return").fill_null(0.0) + 1.0).cum_prod().over("code").alias("open_wealth_index")
        ).sort(["date", "code"])
    )
    session_qc = (
        execution.group_by("date").len().sort("date")
        .with_columns(pl.col("len").rolling_median(21, min_samples=5).alias("rolling_session_count"))
        .with_columns(
            pl.when(pl.col("rolling_session_count").is_null()).then(True)
            .otherwise(pl.col("len") >= 0.75 * pl.col("rolling_session_count"))
            .alias("complete_market_session")
        )
    )
    return execution.join(session_qc, on="date", how="left")


def remove_partial_market_sessions(execution: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    gaps = execution.filter(~pl.col("complete_market_session")).select(
        "date", "len", "rolling_session_count"
    ).unique().sort("date")
    clean = (
        execution.filter(pl.col("complete_market_session")).sort(["code", "date"])
        .with_columns(pl.col("open_wealth_index").shift(1).over("code").alias("previous_accepted_wealth"))
        .with_columns(
            pl.when(pl.col("previous_accepted_wealth").is_not_null() & (pl.col("previous_accepted_wealth") > 0))
            .then(pl.col("open_wealth_index") / pl.col("previous_accepted_wealth") - 1.0)
            .otherwise(None).alias("open_total_return")
        ).sort(["date", "code"])
    )
    return clean, gaps


def build_exact_open_labels(panel: pl.DataFrame, execution: pl.DataFrame, calendar: list[date], horizon: int = 21) -> pl.DataFrame:
    """Outcome from T+1 raw open to the raw open horizon sessions later."""
    mapping = []
    for i, signal_date in enumerate(calendar):
        if i + 1 + horizon < len(calendar):
            mapping.append((signal_date, calendar[i + 1], calendar[i + 1 + horizon]))
    clock = pl.DataFrame(mapping, schema=["date", "entry_date", "exit_date"], orient="row")
    wealth = execution.select("date", "code", "open_wealth_index")
    labels = (
        panel.select("date", "code").join(clock, on="date", how="left")
        .join(
            wealth.rename({"date": "entry_date", "open_wealth_index": "entry_wealth"}),
            on=["entry_date", "code"], how="left",
        ).join(
            wealth.rename({"date": "exit_date", "open_wealth_index": "exit_wealth"}),
            on=["exit_date", "code"], how="left",
        ).with_columns(
            pl.when(pl.col("entry_wealth").is_not_null() & (pl.col("entry_wealth") > 0) & pl.col("exit_wealth").is_not_null())
            .then(pl.col("exit_wealth") / pl.col("entry_wealth") - 1.0).otherwise(None).alias(LABEL)
        ).select("date", "code", "entry_date", "exit_date", LABEL)
    )
    return labels.sort(["date", "code"])


def build_orders(scored: pl.DataFrame, calendar: list[date], top_k: int, rebalance_every: int,
                 gross_exposure: float = 1.0) -> pl.DataFrame:
    next_date = {calendar[i]: calendar[i + 1] for i in range(len(calendar) - 1)}
    signal_dates = sorted(scored["date"].unique().to_list())
    rebalance_dates = set(signal_dates[::rebalance_every])
    selected = (
        scored.filter(
            pl.col("date").is_in(list(rebalance_dates))
            & pl.col("score").is_not_null()
            & (pl.col("trading_money") >= 20_000_000)
            & ~pl.col("unexplained_price_jump")
        ).sort(["date", "score", "trading_money", "code"], descending=[False, True, True, False])
        .with_columns(pl.col("score").rank(method="ordinal", descending=True).over("date").alias("selection_rank"))
        .filter(pl.col("selection_rank") <= top_k)
        .with_columns(
            pl.col("date").replace_strict(next_date, default=None).cast(pl.Date).alias("execution_date"),
            (pl.lit(gross_exposure) / pl.len().over("date")).alias("target_weight"),
        ).filter(pl.col("execution_date").is_not_null())
        .select(pl.col("date").alias("signal_date"), "execution_date", "code", "score", "selection_rank", "target_weight")
    )
    return selected.sort(["execution_date", "selection_rank"])


def simulate(orders: pl.DataFrame, execution: pl.DataFrame, start: date, end: date,
             slippage: float = BASE_SLIPPAGE) -> tuple[pl.DataFrame, pl.DataFrame]:
    period_execution = execution.filter(pl.col("date").is_between(start, end))
    days = sorted(period_execution["date"].unique().to_list())
    relevant_codes = orders["code"].unique().to_list()
    period_execution = period_execution.filter(pl.col("code").is_in(relevant_codes))
    rows_by_date = {
        d: {r["code"]: r for r in g.iter_rows(named=True)}
        for (d,), g in period_execution.partition_by("date", as_dict=True).items()
    }
    orders_by_date = {
        d: g for (d,), g in orders.filter(pl.col("execution_date").is_between(start, end)).partition_by("execution_date", as_dict=True).items()
    }
    cash = 1.0
    positions: dict[str, float] = {}
    nav_rows: list[dict] = []
    trade_rows: list[dict] = []
    total_cost = 0.0
    for d in days:
        quotes = rows_by_date.get(d, {})
        stale_positions = 0
        for code in list(positions):
            q = quotes.get(code)
            if q is not None and q["open_total_return"] is not None:
                positions[code] *= 1.0 + float(q["open_total_return"])
            elif q is None:
                stale_positions += 1
        pretrade_nav = cash + sum(positions.values())
        day_turnover = 0.0
        if d in orders_by_date:
            od = orders_by_date[d]
            rebalance_signal_date = od["signal_date"][0]
            targets = {r["code"]: float(r["target_weight"]) for r in od.iter_rows(named=True)}
            signal_lookup = {r["code"]: r["signal_date"] for r in od.iter_rows(named=True)}
            desired = {c: w * pretrade_nav for c, w in targets.items()}
            # Sell first. A missing raw open means the order cannot trade; the position stays frozen.
            for code, value in list(positions.items()):
                if code not in quotes:
                    continue
                want = desired.get(code, 0.0)
                if value > want + 1e-14:
                    gross = value - want
                    cost = gross * (SELL_COMMISSION + SELL_TAX + slippage)
                    positions[code] = want
                    cash += gross - cost
                    total_cost += cost; day_turnover += gross
                    trade_rows.append({"signal_date": rebalance_signal_date, "execution_date": d, "code": code,
                                       "side": "SELL", "gross_value": gross, "cost": cost})
                    if positions[code] <= 1e-14:
                        positions.pop(code, None)
            buy_needs = {c: max(0.0, want - positions.get(c, 0.0)) for c, want in desired.items() if c in quotes}
            total_need = sum(buy_needs.values())
            if total_need > 0 and cash > 0:
                rate = BUY_COMMISSION + slippage
                scale = min(1.0, cash / (total_need * (1.0 + rate)))
                for code, need in buy_needs.items():
                    gross = need * scale
                    if gross <= 1e-14:
                        continue
                    cost = gross * rate
                    positions[code] = positions.get(code, 0.0) + gross
                    cash -= gross + cost
                    total_cost += cost; day_turnover += gross
                    trade_rows.append({"signal_date": signal_lookup[code], "execution_date": d, "code": code,
                                       "side": "BUY", "gross_value": gross, "cost": cost})
        nav = cash + sum(positions.values())
        nav_rows.append({"date": d, "nav": nav, "cash": cash, "positions": len(positions),
                         "stale_positions": stale_positions,
                         "turnover": day_turnover / pretrade_nav if pretrade_nav > 0 else 0.0,
                         "cumulative_cost": total_cost})
    return pl.DataFrame(nav_rows), pl.DataFrame(trade_rows) if trade_rows else pl.DataFrame(schema={
        "signal_date": pl.Date, "execution_date": pl.Date, "code": pl.String,
        "side": pl.String, "gross_value": pl.Float64, "cost": pl.Float64,
    })


def metrics(nav: pl.DataFrame, trades: pl.DataFrame, name: str) -> dict:
    if nav.height < 2:
        return {"portfolio": name, "days": nav.height}
    values = nav["nav"].to_numpy()
    rets = values[1:] / values[:-1] - 1.0
    years = len(rets) / 252.0
    cagr = values[-1] ** (1.0 / years) - 1.0 if years > 0 else 0.0
    peak = np.maximum.accumulate(values)
    max_dd = float(np.min(values / peak - 1.0))
    vol = float(np.std(rets, ddof=1) * math.sqrt(252)) if len(rets) > 1 else 0.0
    return {
        "portfolio": name, "start": str(nav["date"][0]), "end": str(nav["date"][-1]), "days": nav.height,
        "ending_nav": float(values[-1]), "cumulative_return": float(values[-1] - 1.0), "cagr": float(cagr),
        "annualized_volatility": vol, "sharpe_rf0": float(np.mean(rets) / np.std(rets, ddof=1) * math.sqrt(252)) if vol > 0 else None,
        "max_drawdown": max_dd, "calmar": float(cagr / abs(max_dd)) if max_dd < 0 else None,
        "average_daily_turnover": float(nav["turnover"].mean()), "total_cost": float(nav["cumulative_cost"][-1]),
        "trade_count": trades.height,
    }


def market_proxy(execution: pl.DataFrame, start: date, end: date) -> pl.DataFrame:
    daily = (
        execution.filter(
            pl.col("date").is_between(start, end)
            & pl.col("base_eligible")
            & pl.col("open_total_return").is_not_null()
        )
        .group_by("date").agg(pl.col("open_total_return").mean().alias("return"))
        .sort("date").with_columns((pl.col("return") + 1.0).cum_prod().alias("nav"))
    )
    return daily.select("date", "nav").with_columns(pl.lit(0.0).alias("cash"), pl.lit(0).alias("positions"),
                                                     pl.lit(0).alias("stale_positions"),
                                                     pl.lit(0.0).alias("turnover"), pl.lit(0.0).alias("cumulative_cost"))


def hac_mean_test(excess: np.ndarray, lag: int = 21) -> dict:
    x = excess[np.isfinite(excess)]
    n = len(x); mu = float(x.mean()) if n else float("nan")
    z = x - mu
    long_var = float(np.dot(z, z) / n) if n else float("nan")
    for k in range(1, min(lag, n - 1) + 1):
        gamma = float(np.dot(z[k:], z[:-k]) / n)
        long_var += 2.0 * (1.0 - k / (lag + 1.0)) * gamma
    se = math.sqrt(max(long_var, 0.0) / n) if n else float("nan")
    t = mu / se if se > 0 else None
    return {"observations": n, "mean_daily_excess": mu, "nw_lag": lag, "hac_t_stat": t}


def block_bootstrap_probability(excess: np.ndarray, block: int = 21, draws: int = 5000) -> float:
    x = excess[np.isfinite(excess)]
    if len(x) < block:
        return float("nan")
    rng = np.random.default_rng(412503)
    starts = np.arange(0, len(x) - block + 1)
    wins = 0
    blocks_needed = math.ceil(len(x) / block)
    for _ in range(draws):
        sample = np.concatenate([x[s:s + block] for s in rng.choice(starts, blocks_needed)])[:len(x)]
        wins += float(sample.mean() > 0)
    return wins / draws


def compare(nav: pl.DataFrame, benchmark: pl.DataFrame) -> tuple[np.ndarray, dict]:
    a = nav.select("date", pl.col("nav").pct_change().alias("strategy"))
    b = benchmark.select("date", pl.col("nav").pct_change().alias("benchmark"))
    x = a.join(b, on="date", how="inner").drop_nulls()
    excess = (x["strategy"] - x["benchmark"]).to_numpy()
    stat = hac_mean_test(excess)
    stat["block_bootstrap_positive_probability"] = block_bootstrap_probability(excess)
    return excess, stat


def score_period(joined: pl.DataFrame, model: RidgeModel, start: date, end: date,
                 execution_cols: pl.DataFrame) -> pl.DataFrame:
    d = joined.filter(pl.col("date").is_between(start, end))
    return (
        d.select("date", "code").with_columns(pl.Series("score", model.predict(d)))
        .join(execution_cols.select("date", "code", "trading_money", "unexplained_price_jump"), on=["date", "code"], how="left")
        .sort(["date", "code"])
    )


def run_self_test() -> None:
    panel = pl.DataFrame({
        "date": [date(2020, 1, 2), date(2020, 1, 3), date(2020, 1, 6)] * 2,
        "code": ["A"] * 3 + ["B"] * 3,
        "open": [10.0, 11.0, 12.0, 20.0, 20.0, 20.0],
        "trading_money": [1e9] * 6, "sessions_observed": [100] * 6, "base_eligible": [True] * 6,
    }).sort(["code", "date"])
    actions = pl.DataFrame({"code": ["A"], "date": [date(2020, 1, 6)], "cash_action": [1.0], "share_multiplier": [1.0]})
    ex, gaps = remove_partial_market_sessions(build_execution_panel(panel, actions))
    assert gaps.is_empty()
    a = ex.filter((pl.col("code") == "A") & (pl.col("date") == date(2020, 1, 6)))["open_total_return"][0]
    assert abs(a - (13.0 / 11.0 - 1.0)) < 1e-12
    scored = panel.filter(pl.col("date") <= date(2020, 1, 3)).with_columns(
        pl.lit(1.0).alias("score"), pl.lit(False).alias("unexplained_price_jump")
    )
    orders = build_orders(scored, [date(2020, 1, 2), date(2020, 1, 3), date(2020, 1, 6)], 1, 1)
    assert orders.filter(pl.col("signal_date") >= pl.col("execution_date")).is_empty()
    assert orders.filter(pl.col("signal_date") == date(2020, 1, 2))["execution_date"][0] == date(2020, 1, 3)
    print("E50-A3 self-test PASS")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--panel", type=Path)
    p.add_argument("--prices", type=Path)
    p.add_argument("--labels", type=Path)
    p.add_argument("--actions", type=Path)
    p.add_argument("--a2-qc", type=Path)
    p.add_argument("--out", type=Path, default=Path("e50a3_output"))
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args()
    if a.self_test:
        run_self_test(); return
    for required in [a.panel, a.prices, a.labels, a.actions, a.a2_qc]:
        if required is None or not required.exists():
            p.error(f"missing required input: {required}")
    a.out.mkdir(parents=True, exist_ok=True)
    a2_qc = json.loads(a.a2_qc.read_text())
    if a2_qc.get("status") != "PASS":
        raise RuntimeError(f"E50-A2 QC is not PASS: {a2_qc}")
    panel = pl.read_parquet(a.panel).sort(["date", "code"])
    price_scan = (
        pl.scan_parquet(a.prices)
        if a.prices.suffix.lower() == ".parquet"
        else pl.scan_csv(a.prices, schema_overrides={"code": pl.String}, encoding="utf8-lossy")
    )
    price_schema = price_scan.collect_schema()
    date_expr = pl.col("date") if price_schema["date"] == pl.Date else pl.col("date").str.to_date()
    prices = price_scan.select(
        date_expr.alias("date"), "code", "open", "trading_money", "sessions_observed", "base_eligible",
    ).collect(engine="streaming")
    source_labels = pl.read_parquet(a.labels).sort(["date", "code"])
    forbidden = sorted(set(panel.columns) & {LABEL, "fwd_21d_total_return", "fwd_63d_total_return", "target_rank"})
    if forbidden:
        raise RuntimeError(f"research labels leaked into feature panel: {forbidden}")
    if source_labels.select(pl.struct(["date", "code"]).is_duplicated().sum()).item() != 0:
        raise RuntimeError("duplicate E50-A2 research-label keys")
    actions = load_actions(a.actions)
    execution, partial_sessions = remove_partial_market_sessions(build_execution_panel(prices, actions))
    dates = sorted(execution["date"].unique().to_list())
    exact_labels = build_exact_open_labels(panel, execution, dates)
    joined = target_rank(panel.join(exact_labels.select("date", "code", LABEL), on=["date", "code"], how="inner", validate="1:1"))
    cv, oof, selection = cross_validate(joined, dates)
    signal_execution_cols = panel.select("date", "code", "trading_money", "unexplained_price_jump")
    oof_scored = oof.join(signal_execution_cols, on=["date", "code"])
    portfolio_rows: list[dict] = []
    for top_k, interval in PORTFOLIO_GRID:
        orders = build_orders(oof_scored, dates, top_k, interval)
        nav, trades = simulate(orders, execution, date(2011, 1, 1), date(2018, 12, 31))
        m = metrics(nav, trades, f"TOP{top_k}_EVERY{interval}")
        m["utility"] = m["cagr"] - 0.50 * abs(m["max_drawdown"])
        m["top_k"] = top_k; m["rebalance_every"] = interval
        portfolio_rows.append(m)
    portfolio_grid = pl.DataFrame(portfolio_rows).sort(
        ["utility", "cagr", "top_k", "rebalance_every"], descending=[True, True, False, False]
    )
    chosen = portfolio_grid.row(0, named=True)
    selection.update({"top_k": int(chosen["top_k"]), "rebalance_every": int(chosen["rebalance_every"]),
                      "train_cv_portfolio_utility": chosen["utility"]})

    validation_start = date(2019, 1, 1); validation_end = date(2022, 12, 31)
    sealed_start = date(2023, 1, 1); sealed_end = max(dates)
    validation_cutoff = previous_session(dates, validation_start, 22)
    sealed_cutoff = previous_session(dates, sealed_start, 22)
    val_model = fit_ridge(joined, selection["feature_set"], selection["ridge_lambda"], validation_cutoff)
    sealed_model = fit_ridge(joined, selection["feature_set"], selection["ridge_lambda"], sealed_cutoff)
    metric_rows: list[dict] = []
    stats: dict[str, dict] = {}
    nav_parts: list[pl.DataFrame] = []
    trade_parts: list[pl.DataFrame] = []
    score_parts: list[pl.DataFrame] = []
    for period, start, end, model in [
        ("VALIDATION_2019_2022", validation_start, validation_end, val_model),
        ("SEALED_2023_LATEST", sealed_start, sealed_end, sealed_model),
    ]:
        scored = score_period(joined, model, start, end, signal_execution_cols)
        orders = build_orders(scored, dates, selection["top_k"], selection["rebalance_every"])
        nav, trades = simulate(orders, execution, start, end)
        bench = market_proxy(execution, start, end)
        metric_rows.extend([metrics(nav, trades, period), metrics(bench, pl.DataFrame(), period + "_MARKET_PROXY")])
        _, stats[period] = compare(nav, bench)
        nav_parts.append(nav.with_columns(pl.lit(period).alias("period")))
        trade_parts.append(trades.with_columns(pl.lit(period).alias("period")))
        score_parts.append(scored.with_columns(pl.lit(period).alias("period")))
    all_nav = pl.concat(nav_parts)
    all_trades = pl.concat(trade_parts, how="diagonal_relaxed")
    all_scores = pl.concat(score_parts)
    metric_df = pl.DataFrame(metric_rows)
    execution_clock_violations = all_trades.filter(
        pl.col("signal_date").is_not_null() & (pl.col("execution_date") <= pl.col("signal_date"))
    ).height
    duplicate_scores = all_scores.select(pl.struct(["date", "code"]).is_duplicated().sum()).item()
    status = "PASS" if not any([
        execution_clock_violations, duplicate_scores,
        a2_qc.get("financial_lookahead_violations", 1), a2_qc.get("revenue_lookahead_violations", 1),
    ]) else "FAIL"
    val_metric = metric_df.filter(pl.col("portfolio") == "VALIDATION_2019_2022").row(0, named=True)
    sealed_metric = metric_df.filter(pl.col("portfolio") == "SEALED_2023_LATEST").row(0, named=True)
    promotion = (
        status == "PASS" and val_metric["cagr"] > 0 and sealed_metric["cagr"] > 0
        and stats["VALIDATION_2019_2022"]["block_bootstrap_positive_probability"] >= 0.70
        and stats["SEALED_2023_LATEST"]["block_bootstrap_positive_probability"] >= 0.70
    )
    files = {
        "cv_model_selection.csv": cv,
        "train_portfolio_grid.csv": portfolio_grid,
        "period_metrics.csv": metric_df,
        "daily_nav.csv": all_nav,
        "trades.csv": all_trades,
    }
    for name, frame in files.items():
        frame.write_csv(a.out / name)
    all_scores.write_parquet(a.out / "causal_scores.parquet", compression="zstd")
    exact_labels.write_parquet(a.out / "exact_open_labels_research_only.parquet", compression="zstd")
    model_payload = {"selection": selection, "validation_model": val_model.as_dict(), "sealed_model": sealed_model.as_dict()}
    (a.out / "frozen_model.json").write_text(json.dumps(model_payload, indent=2) + "\n")
    report = {
        "version": "V4.12-E50-A3", "status": status, "decision": "ELIGIBLE_FOR_E50_A4" if promotion else "RESEARCH_ONLY",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(), "input_a2_status": a2_qc.get("status"),
        "signal_rows": panel.height, "signal_codes": panel["code"].n_unique(), "signal_dates": panel["date"].n_unique(),
        "mark_to_market_rows": execution.height, "mark_to_market_codes": execution["code"].n_unique(),
        "excluded_partial_market_sessions": partial_sessions.height,
        "excluded_partial_market_session_dates": [str(x) for x in partial_sessions["date"].to_list()],
        "exact_open_label_rows": exact_labels.height,
        "exact_open_label_coverage": exact_labels.select(pl.col(LABEL).is_not_null().mean()).item(),
        "forbidden_feature_columns": forbidden, "prediction_duplicate_keys": duplicate_scores,
        "execution_clock_violations": execution_clock_violations,
        "financial_lookahead_violations": a2_qc.get("financial_lookahead_violations"),
        "revenue_lookahead_violations": a2_qc.get("revenue_lookahead_violations"),
        "selected_configuration": selection,
        "clock_contract": {
            "signal": "features known at T close", "execution": "next market session raw open",
            "training_label": "T+1 raw open to 21 market sessions after entry, corporate-action adjusted",
            "corporate_actions": "open-to-open total return on effective date",
            "unavailable_open": "order not filled; existing position remains frozen until next raw open",
            "validation_fit_cutoff": str(validation_cutoff), "sealed_fit_cutoff": str(sealed_cutoff),
        },
        "cost_contract": {"buy_commission": BUY_COMMISSION, "sell_commission": SELL_COMMISSION,
                          "sell_tax": SELL_TAX, "slippage_each_side": BASE_SLIPPAGE},
        "statistics": stats,
        "metrics": metric_rows,
        "limitations": [
            "E45 crisis multipliers are intentionally not applied in A3; A4 performs the controller handoff.",
            "The market benchmark is a point-in-time base-universe equal-weight mean open-to-open proxy, not a directly tradable index.",
            "Value proxies remain excluded until the historical par-value master is complete.",
        ],
    }
    output_paths = [a.out / x for x in files] + [a.out / "causal_scores.parquet",
                                                  a.out / "exact_open_labels_research_only.parquet",
                                                  a.out / "frozen_model.json"]
    report["files"] = {x.name: {"bytes": x.stat().st_size, "sha256": sha256(x)} for x in output_paths}
    (a.out / "qc_status.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
