#!/usr/bin/env python3
"""Build the V4.12-E50-A2 point-in-time Taiwan equity factor layer.

Feature rows are signal-date rows. Fundamentals and revenue are joined only
when their E50-A1 available_date is no later than the signal date. Forward
returns are emitted into a physically separate research-label file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import polars as pl


PRICE_FEATURES = [
    "mom_21d", "mom_63d", "mom_126d", "mom_252d", "mom_12_1",
    "reversal_5d", "vol_20d", "vol_60d", "downside_vol_60d",
    "drawdown_63d", "amihud_20d", "turnover_value_20d", "gap_1d",
    "intraday_return", "market_excess_63d",
]

FUNDAMENTAL_FEATURES = [
    "gross_margin_ttm", "operating_margin_ttm", "roa_ttm", "roe_ttm",
    "cfo_to_assets", "accruals_to_assets", "leverage", "current_ratio",
    "cash_to_assets", "asset_growth_yoy", "revenue_growth_yoy",
    "net_income_growth_yoy", "gross_margin_change_yoy", "book_to_price_proxy",
    "earnings_yield_proxy", "sales_yield_proxy",
]

REVENUE_FEATURES = ["monthly_revenue_yoy", "revenue_3m_yoy", "revenue_yoy_acceleration"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_div(num: pl.Expr, den: pl.Expr) -> pl.Expr:
    return pl.when(den.is_not_null() & den.is_finite() & (den.abs() > 1e-12)).then(num / den).otherwise(None)


def load_actions(path: Path) -> pl.DataFrame:
    d = pl.read_csv(path, schema_overrides={"stock_id": pl.String}, try_parse_dates=True)
    if d.is_empty():
        return pl.DataFrame({
            "code": pl.Series([], dtype=pl.String),
            "date": pl.Series([], dtype=pl.Date),
            "cash_action": pl.Series([], dtype=pl.Float64),
            "share_multiplier": pl.Series([], dtype=pl.Float64),
        })
    return (
        d.with_columns(
            pl.col("effective_date").cast(pl.Date).alias("date"),
            pl.col("cash_per_old_share").cast(pl.Float64, strict=False).fill_null(0.0),
            pl.col("share_multiplier").cast(pl.Float64, strict=False).fill_null(1.0),
        )
        .filter(pl.col("date").is_not_null())
        .group_by([pl.col("stock_id").alias("code"), "date"])
        .agg(
            pl.col("cash_per_old_share").sum().alias("cash_action"),
            # FinMind can publish one economic split in both SplitPrice and
            # ParValueChange. Apply the structural ratio once, not twice.
            pl.when(pl.col("event_type").is_in(["split_or_reverse_split", "par_value_change"]))
            .then(pl.col("share_multiplier")).otherwise(None).max().fill_null(1.0)
            .alias("structural_multiplier"),
            pl.when(pl.col("event_type").is_in(["stock_dividend", "capital_reduction"]))
            .then(pl.col("share_multiplier")).otherwise(1.0).product()
            .alias("other_share_multiplier"),
        )
        .with_columns((pl.col("structural_multiplier") * pl.col("other_share_multiplier")).alias("share_multiplier"))
        .select("code", "date", "cash_action", "share_multiplier")
    )


def build_price_layer(a0_path: Path, actions_path: Path) -> tuple[pl.DataFrame, pl.DataFrame]:
    schema = {
        "code": pl.String,
        "date": pl.String,
        "industry_category": pl.String,
        "open": pl.Float64,
        "high": pl.Float64,
        "low": pl.Float64,
        "close": pl.Float64,
        "volume": pl.Float64,
        "trading_money": pl.Float64,
        "avg_money_20d": pl.Float64,
        "median_money_60d": pl.Float64,
        "liquidity_rank": pl.Float64,
        "sessions_observed": pl.Int64,
        "base_eligible": pl.Boolean,
        "alpha_universe": pl.Boolean,
    }
    source = (
        pl.scan_parquet(str(a0_path / "*.parquet"))
        if a0_path.is_dir()
        else pl.scan_csv(a0_path, schema_overrides=schema)
    )
    prices = (
        source
        .select(list(schema))
        .with_columns(pl.col("date").str.to_date())
        .collect(engine="streaming")
        .sort(["code", "date"])
    )
    actions = load_actions(actions_path)
    prices = (
        prices.join(actions, on=["code", "date"], how="left")
        .with_columns(
            pl.col("cash_action").fill_null(0.0),
            pl.col("share_multiplier").fill_null(1.0),
            pl.col("close").shift(1).over("code").alias("prev_close"),
        )
        .with_columns(
            safe_div(
                pl.col("close") * pl.col("share_multiplier") + pl.col("cash_action"),
                pl.col("prev_close"),
            ).sub(1.0).alias("computed_total_return_1d"),
            safe_div(
                pl.col("open") * pl.col("share_multiplier") + pl.col("cash_action"),
                pl.col("prev_close"),
            ).sub(1.0).alias("computed_gap_1d"),
            safe_div(pl.col("close"), pl.col("open")).sub(1.0).alias("intraday_return"),
        )
        .with_columns(
            (
                (pl.col("sessions_observed") > 20)
                & (pl.col("cash_action") == 0)
                & (pl.col("share_multiplier") == 1)
                & ((pl.col("computed_total_return_1d") > 0.5) | (pl.col("computed_total_return_1d") < -0.5))
            ).fill_null(False).alias("unexplained_price_jump"),
        )
        .with_columns(
            pl.when(pl.col("unexplained_price_jump")).then(0.0)
            .otherwise(pl.col("computed_total_return_1d")).alias("total_return_1d"),
            pl.when(pl.col("unexplained_price_jump")).then(pl.col("intraday_return"))
            .otherwise(pl.col("computed_gap_1d")).alias("gap_1d"),
        )
        .with_columns(
            pl.when(pl.col("total_return_1d") > -0.999999)
            .then((pl.col("total_return_1d") + 1.0).log())
            .otherwise(None)
            .alias("log_total_return"),
        )
    )
    market = (
        prices.filter(pl.col("base_eligible") & pl.col("total_return_1d").is_not_null())
        .group_by("date")
        .agg(pl.col("total_return_1d").median().alias("market_return_1d"))
        .sort("date")
    )
    prices = prices.join(market, on="date", how="left").with_columns(
        pl.when(pl.col("market_return_1d") > -0.999999)
        .then((pl.col("market_return_1d") + 1.0).log())
        .otherwise(None)
        .alias("market_log_return")
    )
    for window, name in [(5, "ret_5d"), (21, "mom_21d"), (63, "mom_63d"),
                         (126, "mom_126d"), (252, "mom_252d")]:
        prices = prices.with_columns(
            pl.col("log_total_return").rolling_sum(window_size=window, min_samples=window)
            .over("code").exp().sub(1.0).alias(name)
        )
    prices = prices.with_columns(
        pl.col("log_total_return").shift(21).rolling_sum(window_size=231, min_samples=220)
        .over("code").exp().sub(1.0).alias("mom_12_1"),
        (-pl.col("ret_5d")).alias("reversal_5d"),
        (pl.col("total_return_1d").rolling_std(20, min_samples=20).over("code") * (252.0 ** 0.5)).alias("vol_20d"),
        (pl.col("total_return_1d").rolling_std(60, min_samples=50).over("code") * (252.0 ** 0.5)).alias("vol_60d"),
        (
            pl.when(pl.col("total_return_1d") < 0).then(pl.col("total_return_1d") ** 2).otherwise(0.0)
            .rolling_mean(60, min_samples=50).over("code").sqrt() * (252.0 ** 0.5)
        ).alias("downside_vol_60d"),
        (pl.col("log_total_return").cum_sum().over("code").exp()).alias("wealth_index"),
        (pl.col("total_return_1d").abs() / pl.col("trading_money").clip(lower_bound=1.0) * 1e9)
        .rolling_mean(20, min_samples=15).over("code").alias("amihud_20d"),
        pl.col("trading_money").rolling_mean(20, min_samples=15).over("code").alias("turnover_value_20d"),
        ((pl.col("log_total_return") - pl.col("market_log_return"))
         .rolling_sum(63, min_samples=50).over("code").exp().sub(1.0)).alias("market_excess_63d"),
    ).with_columns(
        safe_div(
            pl.col("wealth_index"),
            pl.col("wealth_index").rolling_max(63, min_samples=20).over("code"),
        ).sub(1.0).alias("drawdown_63d"),
        (
            pl.col("wealth_index").shift(-22).over("code") /
            pl.col("wealth_index").shift(-1).over("code") - 1.0
        ).alias("fwd_21d_total_return"),
        (
            pl.col("wealth_index").shift(-64).over("code") /
            pl.col("wealth_index").shift(-1).over("code") - 1.0
        ).alias("fwd_63d_total_return"),
    )
    labels = prices.filter(pl.col("alpha_universe")).select(
        "date", "code", "fwd_21d_total_return", "fwd_63d_total_return"
    )
    feature_rows = prices.filter(pl.col("alpha_universe")).select(
        "date", "code", "industry_category", "open", "close", "trading_money",
        "avg_money_20d", "median_money_60d", "liquidity_rank", "unexplained_price_jump", *PRICE_FEATURES,
    )
    return feature_rows.sort(["code", "date"]), labels.sort(["date", "code"])


def metric_expr(key: str, aliases: list[str]) -> pl.Expr:
    return pl.coalesce([pl.col(a) for a in aliases if a]).alias(key)


def build_financial_snapshots(path: Path) -> pl.DataFrame:
    income = ["Revenue", "GrossProfit", "OperatingIncome", "EquityAttributableToOwnersOfParent",
              "IncomeAfterTaxes", "NetIncome", "TotalConsolidatedProfitForThePeriod", "EPS"]
    balance = ["TotalAssets", "Liabilities", "EquityAttributableToOwnersOfParent", "Equity",
               "CurrentAssets", "CurrentLiabilities", "CashAndCashEquivalents", "Inventories",
               "AccountsReceivableNet", "OrdinaryShare", "CapitalStock"]
    cashflow = ["NetCashInflowFromOperatingActivities", "CashFlowsFromOperatingActivities"]
    keep = set(income + balance + cashflow)
    d = (
        pl.scan_csv(path, schema_overrides={"stock_id": pl.String})
        .filter(pl.col("type").is_in(list(keep)))
        .select("stock_id", "statement", "period_end", "available_date", "type", "value")
        .with_columns(
            pl.col("period_end").str.to_date(),
            pl.col("available_date").str.to_date(),
            (pl.col("statement") + pl.lit("__") + pl.col("type")).alias("metric"),
        )
        .collect(engine="streaming")
        .pivot(on="metric", index=["stock_id", "period_end", "available_date"], values="value", aggregate_function="last")
        .sort(["stock_id", "period_end"])
    )
    def c(name: str) -> pl.Expr:
        return pl.col(name) if name in d.columns else pl.lit(None, dtype=pl.Float64)
    d = d.with_columns(
        c("income__Revenue").alias("revenue_q"),
        c("income__GrossProfit").alias("gross_profit_q"),
        c("income__OperatingIncome").alias("operating_income_q"),
        pl.coalesce([c("income__EquityAttributableToOwnersOfParent"), c("income__IncomeAfterTaxes"),
                     c("income__NetIncome"), c("income__TotalConsolidatedProfitForThePeriod")]).alias("net_income_q"),
        c("income__EPS").alias("eps_q"),
        c("balance__TotalAssets").alias("total_assets"),
        c("balance__Liabilities").alias("liabilities"),
        pl.coalesce([c("balance__EquityAttributableToOwnersOfParent"), c("balance__Equity")]).alias("equity"),
        c("balance__CurrentAssets").alias("current_assets"),
        c("balance__CurrentLiabilities").alias("current_liabilities"),
        c("balance__CashAndCashEquivalents").alias("cash"),
        c("balance__Inventories").alias("inventories"),
        c("balance__AccountsReceivableNet").alias("accounts_receivable"),
        pl.coalesce([c("balance__OrdinaryShare"), c("balance__CapitalStock")]).alias("ordinary_share_capital"),
        pl.coalesce([c("cashflow__NetCashInflowFromOperatingActivities"),
                     c("cashflow__CashFlowsFromOperatingActivities")]).alias("cfo_cumulative"),
        pl.col("period_end").dt.year().alias("fiscal_year"),
        pl.col("period_end").dt.quarter().alias("fiscal_quarter"),
        (pl.col("period_end").dt.year() * 4 + pl.col("period_end").dt.quarter()).alias("quarter_index"),
    )
    d = d.with_columns(
        pl.col("cfo_cumulative").shift(1).over(["stock_id", "fiscal_year"]).alias("prior_cfo_cumulative"),
    ).with_columns(
        pl.when(pl.col("fiscal_quarter") == 1).then(pl.col("cfo_cumulative"))
        .otherwise(pl.col("cfo_cumulative") - pl.col("prior_cfo_cumulative")).alias("cfo_q"),
        (pl.col("quarter_index") - pl.col("quarter_index").shift(3).over("stock_id") == 3).alias("four_quarters_complete"),
    )
    for raw, ttm in [("revenue_q", "revenue_ttm"), ("gross_profit_q", "gross_profit_ttm"),
                     ("operating_income_q", "operating_income_ttm"), ("net_income_q", "net_income_ttm"),
                     ("cfo_q", "cfo_ttm")]:
        d = d.with_columns(
            pl.when(pl.col("four_quarters_complete"))
            .then(pl.col(raw).rolling_sum(4, min_samples=4).over("stock_id"))
            .otherwise(None).alias(ttm)
        )
    d = d.with_columns(
        ((pl.col("total_assets") + pl.col("total_assets").shift(4).over("stock_id")) / 2).alias("avg_assets_yoy"),
        ((pl.col("equity") + pl.col("equity").shift(4).over("stock_id")) / 2).alias("avg_equity_yoy"),
        pl.col("revenue_ttm").shift(4).over("stock_id").alias("revenue_ttm_lag4"),
        pl.col("net_income_ttm").shift(4).over("stock_id").alias("net_income_ttm_lag4"),
        pl.col("total_assets").shift(4).over("stock_id").alias("assets_lag4"),
        safe_div(pl.col("gross_profit_ttm"), pl.col("revenue_ttm")).alias("gross_margin_ttm"),
        safe_div(pl.col("operating_income_ttm"), pl.col("revenue_ttm")).alias("operating_margin_ttm"),
    ).with_columns(
        safe_div(pl.col("net_income_ttm"), pl.col("avg_assets_yoy")).alias("roa_ttm"),
        safe_div(pl.col("net_income_ttm"), pl.col("avg_equity_yoy")).alias("roe_ttm"),
        safe_div(pl.col("cfo_ttm"), pl.col("avg_assets_yoy")).alias("cfo_to_assets"),
        safe_div(pl.col("net_income_ttm") - pl.col("cfo_ttm"), pl.col("avg_assets_yoy")).alias("accruals_to_assets"),
        safe_div(pl.col("liabilities"), pl.col("total_assets")).alias("leverage"),
        safe_div(pl.col("current_assets"), pl.col("current_liabilities")).alias("current_ratio"),
        safe_div(pl.col("cash"), pl.col("total_assets")).alias("cash_to_assets"),
        safe_div(pl.col("total_assets"), pl.col("assets_lag4")).sub(1.0).alias("asset_growth_yoy"),
        safe_div(pl.col("revenue_ttm"), pl.col("revenue_ttm_lag4")).sub(1.0).alias("revenue_growth_yoy"),
        safe_div(pl.col("net_income_ttm"), pl.col("net_income_ttm_lag4")).sub(1.0).alias("net_income_growth_yoy"),
        (pl.col("gross_margin_ttm") - pl.col("gross_margin_ttm").shift(4).over("stock_id")).alias("gross_margin_change_yoy"),
    )
    return d.select(
        pl.col("stock_id").alias("code"), "period_end", pl.col("available_date").alias("financial_available_date"),
        "total_assets", "equity", "ordinary_share_capital", "revenue_ttm", "net_income_ttm",
        *[x for x in FUNDAMENTAL_FEATURES if not x.endswith("_proxy")],
    ).sort(["code", "financial_available_date"])


def build_revenue_snapshots(path: Path) -> pl.DataFrame:
    d = (
        pl.read_csv(path, schema_overrides={"stock_id": pl.String}, try_parse_dates=True)
        .with_columns(
            pl.col("period_end").cast(pl.Date), pl.col("available_date").cast(pl.Date),
            pl.col("revenue").cast(pl.Float64, strict=False),
        ).sort(["stock_id", "period_end"])
        .with_columns(
            pl.col("revenue").shift(12).over("stock_id").alias("revenue_lag12"),
            pl.col("revenue").rolling_sum(3, min_samples=3).over("stock_id").alias("revenue_3m"),
        ).with_columns(
            pl.col("revenue_3m").shift(12).over("stock_id").alias("revenue_3m_lag12"),
            safe_div(pl.col("revenue"), pl.col("revenue_lag12")).sub(1.0).alias("monthly_revenue_yoy"),
        ).with_columns(
            safe_div(pl.col("revenue_3m"), pl.col("revenue_3m_lag12")).sub(1.0).alias("revenue_3m_yoy"),
            (pl.col("monthly_revenue_yoy") - pl.col("monthly_revenue_yoy").shift(3).over("stock_id")).alias("revenue_yoy_acceleration"),
        )
    )
    return d.select(
        pl.col("stock_id").alias("code"), pl.col("period_end").alias("revenue_period_end"),
        pl.col("available_date").alias("revenue_available_date"), *REVENUE_FEATURES,
    ).sort(["code", "revenue_available_date"])


def percentile_expr(column: str, descending: bool = False) -> pl.Expr:
    rank = pl.col(column).rank(method="average", descending=descending).over("date")
    count = pl.col(column).count().over("date")
    return pl.when(pl.col(column).is_not_null() & (count > 1)).then((rank - 1) / (count - 1)).otherwise(None)


def build_panel(price: pl.DataFrame, financial: pl.DataFrame, revenue: pl.DataFrame) -> pl.DataFrame:
    panel = (
        price.sort(["code", "date"])
        .join_asof(financial, left_on="date", right_on="financial_available_date", by="code", strategy="backward")
        .join_asof(revenue, left_on="date", right_on="revenue_available_date", by="code", strategy="backward")
        .with_columns(
            (pl.col("close") * (pl.col("ordinary_share_capital") / 10.0)).alias("market_cap_proxy"),
            (pl.col("date") - pl.col("financial_available_date")).dt.total_days().alias("financial_age_days"),
            (pl.col("date") - pl.col("revenue_available_date")).dt.total_days().alias("revenue_age_days"),
        ).with_columns(
            safe_div(pl.col("equity"), pl.col("market_cap_proxy")).alias("book_to_price_proxy"),
            safe_div(pl.col("net_income_ttm"), pl.col("market_cap_proxy")).alias("earnings_yield_proxy"),
            safe_div(pl.col("revenue_ttm"), pl.col("market_cap_proxy")).alias("sales_yield_proxy"),
        )
    )
    positive = {
        "mom_12_1": False, "mom_126d": False, "mom_63d": False, "reversal_5d": False,
        "vol_60d": True, "downside_vol_60d": True, "drawdown_63d": False, "amihud_20d": True,
        "gross_margin_ttm": False, "operating_margin_ttm": False, "roa_ttm": False,
        "roe_ttm": False, "cfo_to_assets": False, "accruals_to_assets": True,
        "leverage": True, "current_ratio": False, "cash_to_assets": False,
        "asset_growth_yoy": True, "revenue_growth_yoy": False, "net_income_growth_yoy": False,
        "gross_margin_change_yoy": False, "book_to_price_proxy": False,
        "earnings_yield_proxy": False, "sales_yield_proxy": False,
        "monthly_revenue_yoy": False, "revenue_3m_yoy": False,
        "revenue_yoy_acceleration": False,
    }
    panel = panel.with_columns([
        percentile_expr(col, descending=desc).alias(f"pct_{col}") for col, desc in positive.items()
    ])
    def mean_available(cols: list[str], name: str) -> pl.Expr:
        return pl.mean_horizontal([pl.col(c) for c in cols]).alias(name)
    panel = panel.with_columns(
        mean_available(["pct_mom_12_1", "pct_mom_126d", "pct_mom_63d"], "momentum_family_score"),
        mean_available(["pct_vol_60d", "pct_downside_vol_60d", "pct_drawdown_63d", "pct_amihud_20d"], "defensive_family_score"),
        mean_available(["pct_roa_ttm", "pct_roe_ttm", "pct_cfo_to_assets", "pct_accruals_to_assets",
                        "pct_leverage", "pct_gross_margin_ttm", "pct_operating_margin_ttm"], "quality_family_score"),
        mean_available(["pct_revenue_growth_yoy", "pct_net_income_growth_yoy", "pct_gross_margin_change_yoy",
                        "pct_monthly_revenue_yoy", "pct_revenue_3m_yoy", "pct_revenue_yoy_acceleration"], "growth_family_score"),
        mean_available(["pct_book_to_price_proxy", "pct_earnings_yield_proxy", "pct_sales_yield_proxy"], "value_family_score"),
    )
    return panel.sort(["date", "code"])


def qc(panel: pl.DataFrame, labels: pl.DataFrame, source_rows: dict[str, int]) -> dict:
    feature_cols = PRICE_FEATURES + FUNDAMENTAL_FEATURES + REVENUE_FEATURES
    coverage = {
        c: round(panel.select(pl.col(c).is_not_null().mean()).item(), 6) if c in panel.columns else 0.0
        for c in feature_cols
    }
    fin_leak = panel.filter(pl.col("financial_available_date").is_not_null() & (pl.col("financial_available_date") > pl.col("date"))).height
    rev_leak = panel.filter(pl.col("revenue_available_date").is_not_null() & (pl.col("revenue_available_date") > pl.col("date"))).height
    dup = panel.select(pl.struct(["date", "code"]).is_duplicated().sum()).item()
    label_dup = labels.select(pl.struct(["date", "code"]).is_duplicated().sum()).item()
    rank_cols = [c for c in panel.columns if c.startswith("pct_")] + [c for c in panel.columns if c.endswith("_family_score")]
    bad_ranks = sum(panel.filter(pl.col(c).is_not_null() & ((pl.col(c) < 0) | (pl.col(c) > 1))).height for c in rank_cols)
    status = "PASS" if not any([fin_leak, rev_leak, dup, label_dup, bad_ranks]) and panel.height > 700_000 else "FAIL"
    return {
        "version": "V4.12-E50-A2", "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "signal_rows": panel.height, "signal_dates": panel["date"].n_unique(), "signal_codes": panel["code"].n_unique(),
        "label_rows": labels.height, "financial_lookahead_violations": fin_leak,
        "revenue_lookahead_violations": rev_leak, "duplicate_feature_keys": dup,
        "duplicate_label_keys": label_dup, "out_of_range_rank_values": bad_ranks,
        "unexplained_price_jump_rows": panel.filter(pl.col("unexplained_price_jump")).height,
        "feature_coverage": coverage, "source_rows": source_rows,
        "contracts": {
            "signal_clock": "features known at T close; execution belongs to E50-A3 exact T+1 open simulator",
            "fundamental_join": "latest available_date <= signal date",
            "corporate_actions": "cash and share multipliers enter total return only on effective date",
            "labels": "physically separate; forbidden as model inputs",
            "valuation_warning": "market cap proxy assumes TWD10 par capital; keep as research-only until par-value master is complete",
        },
    }


def build_univariate_diagnostics(panel: pl.DataFrame, labels: pl.DataFrame) -> pl.DataFrame:
    """Point estimates only; overlapping-label inference is deferred to E50-A3."""
    joined = panel.select(
        "date", "code", *[c for c in panel.columns if c.startswith("pct_") or c.endswith("_family_score")]
    ).join(labels, on=["date", "code"], how="inner")
    periods = {
        "TRAIN_2005_2018": (pl.date(2005, 1, 1), pl.date(2018, 12, 31)),
        "VALIDATION_2019_2022": (pl.date(2019, 1, 1), pl.date(2022, 12, 31)),
    }
    factors = [c for c in joined.columns if c.startswith("pct_") or c.endswith("_family_score")]
    labels_to_test = ["fwd_21d_total_return", "fwd_63d_total_return"]
    rows: list[dict] = []
    for period, (start, end) in periods.items():
        sample = joined.filter(pl.col("date").is_between(start, end))
        for factor in factors:
            for label in labels_to_test:
                daily = (
                    sample.filter(pl.col(factor).is_not_null() & pl.col(label).is_not_null())
                    .group_by("date")
                    .agg(
                        pl.len().alias("n"),
                        pl.corr(factor, label, method="spearman").alias("rank_ic"),
                        (
                            pl.col(label).filter(pl.col(factor) >= 0.9).mean()
                            - pl.col(label).filter(pl.col(factor) <= 0.1).mean()
                        ).alias("top_bottom_spread"),
                    )
                    .filter(pl.col("n") >= 30)
                )
                if daily.is_empty():
                    rows.append({"period": period, "factor": factor, "label": label,
                                 "daily_observations": 0, "mean_rank_ic": None,
                                 "median_rank_ic": None, "positive_ic_rate": None,
                                 "mean_top_bottom_spread": None})
                else:
                    s = daily.select(
                        pl.len().alias("daily_observations"),
                        pl.col("rank_ic").mean().alias("mean_rank_ic"),
                        pl.col("rank_ic").median().alias("median_rank_ic"),
                        (pl.col("rank_ic") > 0).mean().alias("positive_ic_rate"),
                        pl.col("top_bottom_spread").mean().alias("mean_top_bottom_spread"),
                    ).row(0, named=True)
                    rows.append({"period": period, "factor": factor, "label": label, **s})
    return pl.DataFrame(rows).sort(["period", "label", "mean_rank_ic"], descending=[False, False, True])


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--a0", type=Path, required=True)
    p.add_argument("--financials", type=Path, required=True)
    p.add_argument("--revenue", type=Path, required=True)
    p.add_argument("--actions", type=Path, required=True)
    p.add_argument("--out", type=Path, default=Path("e50a2_output"))
    a = p.parse_args(); a.out.mkdir(parents=True, exist_ok=True)
    price, labels = build_price_layer(a.a0, a.actions)
    financial = build_financial_snapshots(a.financials)
    revenue = build_revenue_snapshots(a.revenue)
    panel = build_panel(price, financial, revenue)
    panel_path = a.out / "causal_factor_panel.parquet"
    label_path = a.out / "forward_labels_research_only.parquet"
    fin_path = a.out / "financial_factor_snapshots.parquet"
    rev_path = a.out / "monthly_revenue_factor_snapshots.parquet"
    diagnostic_path = a.out / "univariate_ic_diagnostics.csv"
    panel.write_parquet(panel_path, compression="zstd", statistics=True)
    labels.write_parquet(label_path, compression="zstd", statistics=True)
    financial.write_parquet(fin_path, compression="zstd", statistics=True)
    revenue.write_parquet(rev_path, compression="zstd", statistics=True)
    diagnostics = build_univariate_diagnostics(panel, labels)
    diagnostics.write_csv(diagnostic_path)
    a0_scan = pl.scan_parquet(str(a.a0 / "*.parquet")) if a.a0.is_dir() else pl.scan_csv(a.a0)
    status = qc(panel, labels, {
        "a0_price_rows": a0_scan.select(pl.len()).collect().item(),
        "financial_snapshot_rows": financial.height, "revenue_snapshot_rows": revenue.height,
    })
    status["diagnostic_rows"] = diagnostics.height
    status["files"] = {x.name: {"bytes": x.stat().st_size, "sha256": sha256(x)} for x in [panel_path, label_path, fin_path, rev_path, diagnostic_path]}
    (a.out / "qc_status.json").write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n")
    (a.out / "factor_dictionary.json").write_text(json.dumps({
        "price_features": PRICE_FEATURES, "fundamental_features": FUNDAMENTAL_FEATURES,
        "revenue_features": REVENUE_FEATURES,
        "family_scores": ["momentum_family_score", "defensive_family_score", "quality_family_score", "growth_family_score", "value_family_score"],
        "rank_convention": "0=least desirable, 1=most desirable within each signal date",
    }, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(status, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
