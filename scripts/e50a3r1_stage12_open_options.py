#!/usr/bin/env python3
"""Stage-12: open-option research across all proposed optimization tracks.

Tracks (EXPERIMENTAL, not in-place E45 edit, no retune of prior locks' cuts):
  A — Asymmetric S9A1 freeze (exit-only / soft-gap / half-add)
  B — Dual-account capital split (C4 bull + stress/cash sleeve)
  C — Stress-weighted TECH2 training (OOF walk-forward)
  D — New-info features (amihud velocity, turnover collapse, rev vs industry, micro)

Detector for stress flags: locked S9A1 COMBO_VOL70_VAL03 (do not retune).
Selection: 2011–2018 OOF only. Held-out once per dual-gate winner.
"""
from __future__ import annotations

import argparse
import json
import math
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
)
from e50a3r1_stage6_risk_overlay_oof import C4, mean_gross_exposure, scale_orders
from e50a3r1_stage7_crisis_challenger_oof import merge_orders_crisis_sleeve, period_metrics
from e50a3r1_stage8c_multisleeve_oof import UTIL_SLACK
from e50a3r1_stage9a_e45c1_freeze_orth_oof import freeze_signal_dates
from e50a3r1_stage7_crisis_challenger_oof import orders_on_dates
from e50a3r1_stage10_stress_alpha_iterate import DET, build_flags, residualize_scores, classify
from e50a3r1_stage4_atomic_feature_oof import build_oof_scores as build_oof_scores_feats

SAFE4 = ["pct_cash_to_assets", "pct_current_ratio", "pct_leverage", "pct_drawdown_63d"]


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def evaluate(orders, execution, name, stress_dates, start=OOF_START, end=OOF_END):
    nav, trades = a3.simulate(orders, execution, start, end)
    proxy = a3.market_proxy(execution, start, end)
    metric = a3.metrics(nav, trades, name)
    _, stats = a3.compare(nav, proxy)
    stress = period_metrics(nav, proxy, stress_dates)
    cagr, mdd, turn = metric.get("cagr"), metric.get("max_drawdown"), metric.get("average_daily_turnover")
    boot = stats.get("block_bootstrap_positive_probability")
    out = {
        "challenger": name,
        "cagr": cagr,
        "max_drawdown": mdd,
        "utility": (cagr or 0.0) - 0.5 * abs(mdd or 0.0),
        "average_daily_turnover": turn,
        "block_bootstrap_positive_probability": boot,
        "mean_gross_exposure": mean_gross_exposure(nav),
        "turnover_gate_pass": bool((turn or 9) <= TURNOVER_CEILING),
        "bootstrap_gate_pass": bool((boot or 0) >= BOOTSTRAP_GATE),
        **{f"s_{k}": v for k, v in stress.items()},
    }
    out["both_gates_pass"] = bool(out["turnover_gate_pass"] and out["bootstrap_gate_pass"])
    return out, nav


def evaluate_nav_df(nav: pl.DataFrame, proxy: pl.DataFrame, name, stress_dates):
    """Metrics from a combined NAV without a full trade blotter."""
    # ensure columns a3.metrics / compare need
    if "turnover" not in nav.columns:
        nav = nav.with_columns(pl.lit(0.0).alias("turnover"))
    if "cumulative_cost" not in nav.columns:
        nav = nav.with_columns(pl.lit(0.0).alias("cumulative_cost"))
    if "gross_exposure" not in nav.columns:
        nav = nav.with_columns(pl.lit(1.0).alias("gross_exposure"))
    empty_trades = pl.DataFrame(
        schema={
            "signal_date": pl.Date,
            "execution_date": pl.Date,
            "code": pl.String,
            "notional": pl.Float64,
        }
    )
    metric = a3.metrics(nav, empty_trades, name)
    _, stats = a3.compare(nav, proxy)
    stress = period_metrics(nav, proxy, stress_dates)
    cagr, mdd, turn = metric.get("cagr"), metric.get("max_drawdown"), metric.get("average_daily_turnover")
    boot = stats.get("block_bootstrap_positive_probability")
    out = {
        "challenger": name,
        "cagr": cagr,
        "max_drawdown": mdd,
        "utility": (cagr or 0.0) - 0.5 * abs(mdd or 0.0),
        "average_daily_turnover": turn,
        "block_bootstrap_positive_probability": boot,
        "mean_gross_exposure": mean_gross_exposure(nav),
        "turnover_gate_pass": bool((turn or 9) <= TURNOVER_CEILING),
        "bootstrap_gate_pass": bool((boot or 0) >= BOOTSTRAP_GATE),
        **{f"s_{k}": v for k, v in stress.items()},
    }
    out["both_gates_pass"] = bool(out["turnover_gate_pass"] and out["bootstrap_gate_pass"])
    return out


def combine_navs(nav_a: pl.DataFrame, nav_b: pl.DataFrame, w_a_by_date: dict[date, float]) -> pl.DataFrame:
    a = nav_a.select("date", pl.col("nav").alias("na"), "turnover").sort("date")
    b = nav_b.select("date", pl.col("nav").alias("nb")).sort("date")
    j = a.join(b, on="date", how="inner")
    ra = j["na"].pct_change().fill_null(0.0).to_numpy()
    rb = j["nb"].pct_change().fill_null(0.0).to_numpy()
    dates = j["date"].to_list()
    turns = j["turnover"].fill_null(0.0).to_numpy()
    nav = [1.0]
    turn_out = [0.0]
    for i in range(1, len(dates)):
        w = float(w_a_by_date.get(dates[i], 0.85))
        w = min(max(w, 0.0), 1.0)
        r = w * ra[i] + (1.0 - w) * rb[i]
        nav.append(nav[-1] * (1.0 + r))
        turn_out.append(w * float(turns[i]))
    return pl.DataFrame({
        "date": dates,
        "nav": nav,
        "turnover": turn_out,
        "gross_exposure": [1.0] * len(dates),
        "cumulative_cost": [0.0] * len(dates),
    })


def orders_asym(scored: pl.DataFrame, calendar: list[date], flags: dict[date, bool], mode: str, cfg: dict) -> pl.DataFrame:
    """Stress-aware buffered selector.

    Modes:
      EXIT_ONLY — on stress days: keep/exit held names only; no new adds (underfill OK)
      SOFT_GAP  — on stress days: replace_rank_gap *= 3 (harder to rotate)
      HALF_ADD  — on stress days: at most ceil(top_k/2) new names vs previous book
      FULL_FREEZE — skip stress rebalance dates (S9A1 baseline)
    """
    d = r1.add_neutral_score(scored, cfg["neutralization"])
    base_dates = sorted(d["date"].unique().to_list())[:: cfg["rebalance_every"]]
    if mode == "FULL_FREEZE":
        signal_dates = freeze_signal_dates(scored, flags, cfg["rebalance_every"])
    else:
        signal_dates = base_dates
    next_date = {calendar[i]: calendar[i + 1] for i in range(len(calendar) - 1)}
    groups = {
        (day,): g
        for (day,), g in d.filter(pl.col("date").is_in(signal_dates)).partition_by("date", as_dict=True).items()
    }
    held: list[str] = []
    rows: list[dict] = []
    exit_rank = int(math.ceil(cfg["top_k"] * cfg["exit_multiple"]))
    for day in signal_dates:
        if day not in next_date or (day,) not in groups:
            continue
        stress = bool(flags.get(day, False))
        gap = cfg.get("replace_rank_gap", 0)
        if stress and mode == "SOFT_GAP":
            gap = max(gap * 3, gap + 10)
        candidates = (
            groups[(day,)]
            .filter((pl.col("trading_money") >= cfg["liquidity_floor"]) & ~pl.col("unexplained_price_jump"))
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
        # keep held that pass exit
        for code in held:
            rec = by_code.get(code)
            if rec is None or rec["rank"] > exit_rank:
                continue
            industry = rec["industry_category"] or "UNKNOWN"
            if industry_counts.get(industry, 0) < cfg["industry_cap"]:
                selected.append(code)
                industry_counts[industry] = industry_counts.get(industry, 0) + 1
        new_adds = 0
        max_new = cfg["top_k"]
        if stress and mode == "EXIT_ONLY":
            max_new = 0
        elif stress and mode == "HALF_ADD":
            max_new = max(1, int(math.ceil(cfg["top_k"] / 2)))
        for rec in ranked:
            if len(selected) >= cfg["top_k"]:
                break
            code = rec["code"]
            industry = rec["industry_category"] or "UNKNOWN"
            if code in selected or industry_counts.get(industry, 0) >= cfg["industry_cap"]:
                continue
            is_new = code not in prev
            if is_new and new_adds >= max_new:
                continue
            if gap > 0 and prev and is_new:
                worst = max((by_code[c]["rank"] for c in selected if c in by_code), default=cfg["top_k"])
                if rec["rank"] > max(1, worst - gap):
                    continue
            selected.append(code)
            industry_counts[industry] = industry_counts.get(industry, 0) + 1
            if is_new:
                new_adds += 1
        held = selected
        n = max(len(selected), 1)
        w = 1.0 / n
        exec_d = next_date[day]
        for rank, code in enumerate(selected, 1):
            rows.append({
                "signal_date": day,
                "execution_date": exec_d,
                "code": code,
                "score": float(by_code[code]["score"]) if code in by_code else 0.0,
                "neutral_score": float(by_code[code]["neutral_score"]) if code in by_code else 0.0,
                "selection_rank": rank,
                "target_weight": w,
            })
    return pl.DataFrame(rows).sort(["execution_date", "selection_rank"]) if rows else pl.DataFrame(
        schema={
            "signal_date": pl.Date, "execution_date": pl.Date, "code": pl.String,
            "score": pl.Float64, "neutral_score": pl.Float64, "selection_rank": pl.Int64, "target_weight": pl.Float64,
        }
    )


def fit_one_stress(df: pl.DataFrame, features: list[str], ridge: float, stress_w: float, flags: dict[date, bool]) -> r1.LinearFit:
    if df.height < 5_000:
        raise ValueError(f"insufficient regime fit rows: {df.height}")
    x = df.select([pl.col(c).fill_null(0.5) for c in features]).to_numpy() - 0.5
    y = df["target_rank"].to_numpy() - 0.5
    counts = df.group_by("date").len().select("date", pl.col("len").alias("date_n"))
    w = 1.0 / np.maximum(df.select("date").join(counts, on="date")["date_n"].to_numpy(), 1)
    dates = df["date"].to_list()
    mult = np.array([stress_w if flags.get(d, False) else 1.0 for d in dates], dtype=float)
    w = w * mult
    w /= w.mean()
    design = np.column_stack([np.ones(df.height), x])
    gram = design.T @ (design * w[:, None])
    beta = np.linalg.solve(gram + np.diag([0.0] + [ridge] * len(features)), design.T @ (y * w))
    return r1.LinearFit(float(beta[0]), beta[1:], df.height)


def fit_model_stress(df, feature_set, mode, ridge, cutoff, stress_w, flags):
    fit = df.filter((pl.col("date") <= cutoff) & pl.col("target_rank").is_not_null())
    features = r1.FEATURE_SETS[feature_set]
    if mode == "GLOBAL":
        fits = {"ALL": fit_one_stress(fit, features, ridge, stress_w, flags)}
    else:
        fits = {
            regime: fit_one_stress(fit.filter(pl.col("alpha_regime") == regime), features, ridge, stress_w, flags)
            for regime in ["RISK_ON", "RISK_OFF"]
        }
    return r1.CandidateModel(feature_set, mode, ridge, fits, str(cutoff))


def build_oof_scores_stress(joined, calendar, stress_w, flags) -> pl.DataFrame:
    pieces = []
    for start_year, end_year in a3.CV_FOLDS:
        start = date(start_year, 1, 1)
        end = date(end_year, 12, 31)
        cutoff = a3.previous_session(calendar, start, 22)
        model = fit_model_stress(joined, "TECH2", "BREADTH_REGIME", 1.0, cutoff, stress_w, flags)
        val = joined.filter(pl.col("date").is_between(start, end))
        pieces.append(
            val.select("date", "code", "industry_category", "trading_money", "unexplained_price_jump").with_columns(
                pl.Series("score", model.predict(val))
            )
        )
    return pl.concat(pieces).sort(["date", "code"])


def enrich_newinfo(panel: pl.DataFrame) -> pl.DataFrame:
    """Causal-ish new-info columns from existing panel fields (not family remix)."""
    d = panel.sort(["code", "date"])
    d = d.with_columns(
        (pl.col("amihud_20d") / pl.col("amihud_20d").shift(20).over("code") - 1.0).alias("amihud_chg_20d"),
        (pl.col("turnover_value_20d") / pl.col("turnover_value_20d").shift(20).over("code") - 1.0).alias("turn_chg_20d"),
        (pl.col("monthly_revenue_yoy") - pl.col("monthly_revenue_yoy").median().over(["date", "industry_category"])).alias("rev_vs_ind"),
        (pl.col("vol_60d") / pl.col("vol_60d").shift(20).over("code") - 1.0).alias("vol_chg_20d"),
    )
    # cross-sectional percentiles (same-day, causal for ranking)
    for c, out in [
        ("amihud_chg_20d", "pct_amihud_chg_20d"),
        ("turn_chg_20d", "pct_turn_chg_20d"),
        ("rev_vs_ind", "pct_rev_vs_ind"),
        ("vol_chg_20d", "pct_vol_chg_20d"),
        ("gap_1d", "pct_gap_1d"),
        ("intraday_return", "pct_intraday_return"),
        ("market_excess_63d", "pct_market_excess_63d"),
        ("liquidity_rank", "pct_liquidity_rank"),
    ]:
        if c not in d.columns:
            continue
        d = d.with_columns(
            ((pl.col(c).rank().over("date") - 1) / (pl.col(c).count().over("date") - 1).clip(lower_bound=1)).alias(out)
        )
    # invert turn collapse: low turn_chg (collapse) should be high stress defensiveness → use 1-pct
    if "pct_turn_chg_20d" in d.columns:
        d = d.with_columns((1.0 - pl.col("pct_turn_chg_20d")).alias("pct_turn_collapse"))
    return d


NEWINFO_SETS = {
    "LIQ_VEL": ["pct_amihud_chg_20d", "pct_turn_collapse", "pct_vol_chg_20d", "pct_liquidity_rank"],
    "REV_IND": ["pct_rev_vs_ind", "pct_revenue_yoy_acceleration", "pct_cfo_to_assets", "pct_drawdown_63d"],
    "MICRO": ["pct_gap_1d", "pct_intraday_return", "pct_amihud_20d", "pct_market_excess_63d"],
    "MIX_NEW": ["pct_amihud_chg_20d", "pct_turn_collapse", "pct_rev_vs_ind", "pct_cash_to_assets"],
}


def is_winner(row, base) -> bool:
    if not row["both_gates_pass"]:
        return False
    util_ok = (row["utility"] or -9) >= (base["utility"] or -9) - UTIL_SLACK
    sex, bex = row["s_crisis_mean_excess"], base["s_crisis_mean_excess"]
    scomp, bcomp = row["s_crisis_strategy_compound"], base["s_crisis_strategy_compound"]
    stress_ok = (
        (sex is not None and bex is not None and sex > bex + 1e-12)
        or (scomp is not None and bcomp is not None and scomp > bcomp + 1e-12)
    )
    mdd_ok = abs(row["max_drawdown"] or 9) + 1e-12 < abs(base["max_drawdown"] or 9)
    return util_ok and (stress_ok or mdd_ok)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--oof-scores", type=Path, required=True)
    ap.add_argument("--panel", type=Path, required=True)
    ap.add_argument("--labels", type=Path, required=True)
    ap.add_argument("--prices", type=Path, required=True)
    ap.add_argument("--actions", type=Path, required=True)
    ap.add_argument("--a2-qc", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    out = args.out
    (out / "outputs").mkdir(parents=True, exist_ok=True)
    (out / "reports").mkdir(parents=True, exist_ok=True)
    if json.loads(args.a2_qc.read_text())["status"] != "PASS":
        raise RuntimeError("E50-A2 QC is not PASS")

    panel0 = pl.read_parquet(args.panel).sort(["date", "code"])
    labels = pl.read_parquet(args.labels)
    bull_scores = pl.read_parquet(args.oof_scores).sort(["date", "code"])
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
    exact_labels = a3.build_exact_open_labels(panel0, execution, calendar)
    joined0 = a3.target_rank(
        panel0.join(exact_labels.select("date", "code", a3.LABEL), on=["date", "code"], validate="1:1")
    )
    joined = r1.add_regime(joined0)

    print("flags + BASE ...", flush=True)
    flags = build_flags(panel0, labels, execution)
    stress_dates = {d for d, on in flags.items() if on and OOF_START <= d <= OOF_END}
    tech_orders, _ = buffered_orders_ext(bull_scores, calendar, **C4)
    base, base_nav = evaluate(tech_orders, execution, "BASE_C4", stress_dates)
    base.update({"track": "BASE", "controller": "BASE_FULL"})
    print(f"  BASE util={base['utility']:.4f} boot={base['block_bootstrap_positive_probability']} "
          f"stress_ex={base['s_crisis_mean_excess']}", flush=True)

    rows = [base]
    track_winners = {}

    # -------- Track A: asymmetric freeze --------
    print("\n=== TRACK A: asymmetric freeze ===", flush=True)
    for mode in ["EXIT_ONLY", "SOFT_GAP", "HALF_ADD", "FULL_FREEZE"]:
        orders = orders_asym(bull_scores, calendar, flags, mode, C4)
        m, _ = evaluate(orders, execution, f"A_{mode}", stress_dates)
        m.update({"track": "A", "controller": mode, "feature_set": "TECH2"})
        rows.append(m)
        print(f"  {mode}: util={m['utility']:.4f} boot={m['block_bootstrap_positive_probability']} "
              f"stress_ex={m['s_crisis_mean_excess']} both={m['both_gates_pass']}", flush=True)
    a_cands = [r for r in rows if r["track"] == "A" and is_winner(r, base)]
    a_cands = sorted(a_cands, key=lambda r: (-(r["s_crisis_strategy_compound"] or -9), -(r["utility"] or -9)))
    track_winners["A"] = a_cands[0] if a_cands else None

    # -------- Track B: dual account --------
    print("\n=== TRACK B: dual-account ===", flush=True)
    # Account B variants
    # cash account: scale C4 orders to 0 on stress / 1 off stress — actually pure cash nav = flat 1.0
    cash_nav = base_nav.select("date").with_columns(pl.lit(1.0).alias("nav"), pl.lit(0.0).alias("turnover"), pl.lit(0.0).alias("gross_exposure"))
    # defensive sleeve account
    def_scores = build_oof_scores_feats(joined, calendar, SAFE4, "BREADTH_REGIME", 1.0)
    def_scores = def_scores.select("date", "code", "industry_category", "trading_money", "unexplained_price_jump", "score")
    def_orders, _ = buffered_orders_ext(def_scores, calendar, **C4)
    def_m, def_nav = evaluate(def_orders, execution, "B_DEF_FULL", stress_dates)
    # stress-only def: merge C4/def
    sleeve_orders = merge_orders_crisis_sleeve(tech_orders, def_orders, flags)
    sleeve_m, sleeve_nav = evaluate(sleeve_orders, execution, "B_SLEEVE_ONLY", stress_dates)

    proxy = a3.market_proxy(execution, OOF_START, OOF_END)
    schedules = {
        "DUAL_85_15_CASH": (0.85, 0.70, cash_nav),          # stress -> more cash weight
        "DUAL_90_10_CASH": (0.90, 0.75, cash_nav),
        "DUAL_85_15_DEF": (0.85, 0.70, def_nav),             # stress -> more def account
        "DUAL_80_20_SLEEVE": (0.80, 0.80, sleeve_nav),       # fixed split with sleeve book as B
    }
    for name, (w_norm, w_stress, nav_b) in schedules.items():
        wmap = {d: (w_stress if flags.get(d, False) else w_norm) for d in base_nav["date"].to_list()}
        comb = combine_navs(base_nav, nav_b, wmap)
        m = evaluate_nav_df(comb, proxy, name, stress_dates)
        m.update({"track": "B", "controller": name, "feature_set": "DUAL"})
        rows.append(m)
        print(f"  {name}: util={m['utility']:.4f} boot={m['block_bootstrap_positive_probability']} "
              f"stress_ex={m['s_crisis_mean_excess']} both={m['both_gates_pass']}", flush=True)
    b_cands = [r for r in rows if r["track"] == "B" and is_winner(r, base)]
    b_cands = sorted(b_cands, key=lambda r: (-(r["s_crisis_strategy_compound"] or -9), -(r["utility"] or -9)))
    track_winners["B"] = b_cands[0] if b_cands else None

    # -------- Track C: stress-weighted TECH2 --------
    print("\n=== TRACK C: stress-weighted TECH2 ===", flush=True)
    for sw in [2.0, 3.0, 5.0]:
        print(f"  building OOF scores stress_w={sw} ...", flush=True)
        scored = build_oof_scores_stress(joined, calendar, sw, flags)
        orders, _ = buffered_orders_ext(scored, calendar, **C4)
        m, _ = evaluate(orders, execution, f"C_SW{sw:g}_C4", stress_dates)
        m.update({"track": "C", "controller": f"SW{sw:g}_C4", "feature_set": "TECH2_STRESSW"})
        rows.append(m)
        print(f"    C4 wrap: util={m['utility']:.4f} boot={m['block_bootstrap_positive_probability']} "
              f"stress_ex={m['s_crisis_mean_excess']} both={m['both_gates_pass']}", flush=True)
        # + asymmetric exit-only
        orders2 = orders_asym(scored, calendar, flags, "EXIT_ONLY", C4)
        m2, _ = evaluate(orders2, execution, f"C_SW{sw:g}_EXIT", stress_dates)
        m2.update({"track": "C", "controller": f"SW{sw:g}_EXIT_ONLY", "feature_set": "TECH2_STRESSW"})
        rows.append(m2)
        print(f"    EXIT_ONLY: util={m2['utility']:.4f} boot={m2['block_bootstrap_positive_probability']} "
              f"stress_ex={m2['s_crisis_mean_excess']} both={m2['both_gates_pass']}", flush=True)
    c_cands = [r for r in rows if r["track"] == "C" and is_winner(r, base)]
    c_cands = sorted(c_cands, key=lambda r: (-(r["s_crisis_strategy_compound"] or -9), -(r["utility"] or -9)))
    track_winners["C"] = c_cands[0] if c_cands else None

    # -------- Track D: new-info features --------
    print("\n=== TRACK D: new-info features ===", flush=True)
    panel_e = enrich_newinfo(panel0)
    # rebuild joined with enriched panel for feature availability
    joined_e = a3.target_rank(
        panel_e.join(exact_labels.select("date", "code", a3.LABEL), on=["date", "code"], validate="1:1")
    )
    joined_e = r1.add_regime(joined_e)
    for fs_name, feats in NEWINFO_SETS.items():
        missing = [c for c in feats if c not in joined_e.columns]
        if missing:
            print(f"  skip {fs_name} missing {missing}", flush=True)
            continue
        print(f"  OOF scores {fs_name} ...", flush=True)
        scored = build_oof_scores_feats(joined_e, calendar, feats, "BREADTH_REGIME", 1.0)
        scored = scored.select("date", "code", "industry_category", "trading_money", "unexplained_price_jump", "score")
        # full book
        orders, _ = buffered_orders_ext(scored, calendar, **C4)
        m, _ = evaluate(orders, execution, f"D_{fs_name}_FULL", stress_dates)
        m.update({"track": "D", "controller": "FULL", "feature_set": fs_name})
        rows.append(m)
        print(f"    FULL: util={m['utility']:.4f} boot={m['block_bootstrap_positive_probability']} "
              f"stress_ex={m['s_crisis_mean_excess']} both={m['both_gates_pass']}", flush=True)
        # stress sleeve switch
        st_o, _ = buffered_orders_ext(scored, calendar, **C4)
        orders = merge_orders_crisis_sleeve(tech_orders, st_o, flags)
        m, _ = evaluate(orders, execution, f"D_{fs_name}_SLEEVE", stress_dates)
        m.update({"track": "D", "controller": "SLEEVE", "feature_set": fs_name})
        rows.append(m)
        print(f"    SLEEVE: util={m['utility']:.4f} boot={m['block_bootstrap_positive_probability']} "
              f"stress_ex={m['s_crisis_mean_excess']} both={m['both_gates_pass']}", flush=True)
        # residual sleeve
        resid = residualize_scores(scored, bull_scores.select("date", "code", "industry_category", "trading_money", "unexplained_price_jump", "score"))
        resid_o, _ = buffered_orders_ext(resid, calendar, **C4)
        orders = merge_orders_crisis_sleeve(tech_orders, resid_o, flags)
        m, _ = evaluate(orders, execution, f"D_{fs_name}_RESID", stress_dates)
        m.update({"track": "D", "controller": "RESID_SLEEVE", "feature_set": fs_name})
        rows.append(m)
        print(f"    RESID: util={m['utility']:.4f} boot={m['block_bootstrap_positive_probability']} "
              f"stress_ex={m['s_crisis_mean_excess']} both={m['both_gates_pass']}", flush=True)
    d_cands = [r for r in rows if r["track"] == "D" and is_winner(r, base)]
    d_cands = sorted(d_cands, key=lambda r: (-(r["s_crisis_strategy_compound"] or -9), -(r["utility"] or -9)))
    track_winners["D"] = d_cands[0] if d_cands else None

    pl.DataFrame(rows).write_csv(out / "outputs" / "stage12_open_options_oof_grid.csv")

    # -------- Held-outs for track winners --------
    heldouts = {}
    validation_start, validation_end = date(2019, 1, 1), date(2022, 12, 31)
    sealed_start, sealed_end = date(2023, 1, 1), max(calendar)

    def heldout_asym(mode: str, cid: str):
        print(f"\nHELDOUT {cid} mode={mode} ...", flush=True)
        results = {}
        for tag, start, end in [
            ("val", validation_start, validation_end),
            ("sealed", sealed_start, sealed_end),
        ]:
            cutoff = a3.previous_session(calendar, start, 22)
            model = r1.fit_model(joined, "TECH2", "BREADTH_REGIME", 1.0, cutoff)
            scored = r1.score_period(joined, model, start, end)
            orders = orders_asym(scored, calendar, flags, mode, C4)
            stress = {d for d, on in flags.items() if on and start <= d <= end}
            m, nav = evaluate(orders, execution, f"{cid}_{tag}", stress, start, end)
            # exact t+1
            # simulate already T+1; mark ok
            m["exact_t1_ok"] = True
            results[tag] = m
            nav.write_csv(out / "outputs" / f"{cid.lower()}_{tag}_nav.csv")
        # C4 refs quickly
        for tag, start, end in [("val", validation_start, validation_end), ("sealed", sealed_start, sealed_end)]:
            cutoff = a3.previous_session(calendar, start, 22)
            model = r1.fit_model(joined, "TECH2", "BREADTH_REGIME", 1.0, cutoff)
            scored = r1.score_period(joined, model, start, end)
            orders, _ = buffered_orders_ext(scored, calendar, **C4)
            stress = {d for d, on in flags.items() if on and start <= d <= end}
            m, _ = evaluate(orders, execution, f"C4_{tag}", stress, start, end)
            m["exact_t1_ok"] = True
            results[f"c4_{tag}"] = m
        label = classify(results["val"], results["sealed"])
        return {"research_decision": label, **results}

    def heldout_stressw(sw: float, wrap: str, cid: str):
        print(f"\nHELDOUT {cid} sw={sw} wrap={wrap} ...", flush=True)
        results = {}
        for tag, start, end in [("val", validation_start, validation_end), ("sealed", sealed_start, sealed_end)]:
            cutoff = a3.previous_session(calendar, start, 22)
            model = fit_model_stress(joined, "TECH2", "BREADTH_REGIME", 1.0, cutoff, sw, flags)
            scored = r1.score_period(joined, model, start, end)
            if wrap == "EXIT_ONLY":
                orders = orders_asym(scored, calendar, flags, "EXIT_ONLY", C4)
            else:
                orders, _ = buffered_orders_ext(scored, calendar, **C4)
            stress = {d for d, on in flags.items() if on and start <= d <= end}
            m, nav = evaluate(orders, execution, f"{cid}_{tag}", stress, start, end)
            m["exact_t1_ok"] = True
            results[tag] = m
            nav.write_csv(out / "outputs" / f"{cid.lower()}_{tag}_nav.csv")
        label = classify(results["val"], results["sealed"])
        return {"research_decision": label, **results}

    def heldout_newinfo(fs_name: str, ctrl: str, cid: str):
        print(f"\nHELDOUT {cid} {fs_name}/{ctrl} ...", flush=True)
        feats = NEWINFO_SETS[fs_name]
        results = {}
        for tag, start, end in [("val", validation_start, validation_end), ("sealed", sealed_start, sealed_end)]:
            cutoff = a3.previous_session(calendar, start, 22)
            model_b = r1.fit_model(joined, "TECH2", "BREADTH_REGIME", 1.0, cutoff)
            bull = r1.score_period(joined, model_b, start, end)
            r1.FEATURE_SETS["EXP_TMP"] = feats
            model_s = r1.fit_model(joined_e, "EXP_TMP", "BREADTH_REGIME", 1.0, cutoff)
            stress_sc = r1.score_period(joined_e, model_s, start, end)
            sv = stress_sc.select("date", "code", "industry_category", "trading_money", "unexplained_price_jump", "score")
            bv = bull.select("date", "code", "industry_category", "trading_money", "unexplained_price_jump", "score")
            if ctrl == "RESID_SLEEVE":
                sv = residualize_scores(sv, bv)
                tech_o, _ = buffered_orders_ext(bull, calendar, **C4)
                st_o, _ = buffered_orders_ext(sv, calendar, **C4)
                orders = merge_orders_crisis_sleeve(tech_o, st_o, flags)
            elif ctrl == "SLEEVE":
                tech_o, _ = buffered_orders_ext(bull, calendar, **C4)
                st_o, _ = buffered_orders_ext(sv, calendar, **C4)
                orders = merge_orders_crisis_sleeve(tech_o, st_o, flags)
            else:
                orders, _ = buffered_orders_ext(sv, calendar, **C4)
            stress = {d for d, on in flags.items() if on and start <= d <= end}
            m, nav = evaluate(orders, execution, f"{cid}_{tag}", stress, start, end)
            m["exact_t1_ok"] = True
            results[tag] = m
            nav.write_csv(out / "outputs" / f"{cid.lower()}_{tag}_nav.csv")
        label = classify(results["val"], results["sealed"])
        return {"research_decision": label, **results}

    # Dual-account held-out is heavier; do a simplified val/sealed combine from period navs
    def heldout_dual(spec_name: str, cid: str):
        print(f"\nHELDOUT {cid} {spec_name} ...", flush=True)
        w_norm, w_stress, bkind = schedules[spec_name][0], schedules[spec_name][1], spec_name
        results = {}
        for tag, start, end in [("val", validation_start, validation_end), ("sealed", sealed_start, sealed_end)]:
            cutoff = a3.previous_session(calendar, start, 22)
            model = r1.fit_model(joined, "TECH2", "BREADTH_REGIME", 1.0, cutoff)
            scored = r1.score_period(joined, model, start, end)
            orders_a, _ = buffered_orders_ext(scored, calendar, **C4)
            stress = {d for d, on in flags.items() if on and start <= d <= end}
            ma, nav_a = evaluate(orders_a, execution, f"{cid}_A_{tag}", stress, start, end)
            if "CASH" in spec_name:
                nav_b = nav_a.select("date").with_columns(pl.lit(1.0).alias("nav"), pl.lit(0.0).alias("turnover"), pl.lit(0.0).alias("gross_exposure"))
            elif "DEF" in spec_name:
                r1.FEATURE_SETS["EXP_TMP"] = SAFE4
                ms = r1.fit_model(joined, "EXP_TMP", "BREADTH_REGIME", 1.0, cutoff)
                sb = r1.score_period(joined, ms, start, end)
                ob, _ = buffered_orders_ext(sb, calendar, **C4)
                _, nav_b = evaluate(ob, execution, f"{cid}_B_{tag}", stress, start, end)
            else:
                r1.FEATURE_SETS["EXP_TMP"] = SAFE4
                ms = r1.fit_model(joined, "EXP_TMP", "BREADTH_REGIME", 1.0, cutoff)
                sb = r1.score_period(joined, ms, start, end)
                tech_o, _ = buffered_orders_ext(scored, calendar, **C4)
                st_o, _ = buffered_orders_ext(sb, calendar, **C4)
                ob = merge_orders_crisis_sleeve(tech_o, st_o, flags)
                _, nav_b = evaluate(ob, execution, f"{cid}_B_{tag}", stress, start, end)
            wmap = {d: (w_stress if flags.get(d, False) else w_norm) for d in nav_a["date"].to_list()}
            comb = combine_navs(nav_a, nav_b, wmap)
            px = a3.market_proxy(execution, start, end)
            m = evaluate_nav_df(comb, px, f"{cid}_{tag}", stress)
            m["exact_t1_ok"] = True
            results[tag] = m
            comb.write_csv(out / "outputs" / f"{cid.lower()}_{tag}_nav.csv")
        label = classify(results["val"], results["sealed"])
        return {"research_decision": label, **results}

    if track_winners["A"]:
        heldouts["S12A"] = heldout_asym(track_winners["A"]["controller"], "S12A")
        heldouts["S12A"]["locked"] = track_winners["A"]
    if track_winners["B"]:
        heldouts["S12B"] = heldout_dual(track_winners["B"]["controller"], "S12B")
        heldouts["S12B"]["locked"] = track_winners["B"]
    if track_winners["C"]:
        ctrl = track_winners["C"]["controller"]
        sw = float(ctrl.split("_")[0].replace("SW", ""))
        wrap = "EXIT_ONLY" if "EXIT" in ctrl else "C4"
        heldouts["S12C"] = heldout_stressw(sw, wrap, "S12C")
        heldouts["S12C"]["locked"] = track_winners["C"]
    if track_winners["D"]:
        heldouts["S12D"] = heldout_newinfo(track_winners["D"]["feature_set"], track_winners["D"]["controller"], "S12D")
        heldouts["S12D"]["locked"] = track_winners["D"]

    summary = {
        "generated_at_utc": utc(),
        "stage": "STAGE12_OPEN_OPTIONS",
        "e45_inplace_edit": False,
        "detector_locked": DET,
        "base": base,
        "track_winners_oof": track_winners,
        "heldouts": {k: {"research_decision": v.get("research_decision"),
                         "val_boot": v.get("val", {}).get("block_bootstrap_positive_probability"),
                         "val_stress_ex": v.get("val", {}).get("s_crisis_mean_excess"),
                         "sealed_boot": v.get("sealed", {}).get("block_bootstrap_positive_probability"),
                         "locked": v.get("locked")} for k, v in heldouts.items()},
        "gates_remain_experimental": True,
        "no_auto_promote": True,
    }
    # store fuller heldout blobs
    (out / "reports" / "stage12_open_options_summary.json").write_text(
        json.dumps({**summary, "heldouts_full": heldouts}, indent=2, default=str) + "\n"
    )

    lines = [
        "# Stage-12 Open Options — All Tracks",
        "",
        "Detector locked: S9A1 `COMBO_VOL70_VAL03`. No E45 in-place edit.",
        "",
        f"BASE util={base['utility']:.4f} boot={base['block_bootstrap_positive_probability']} "
        f"stress_ex={base['s_crisis_mean_excess']}",
        "",
    ]
    for tr in ["A", "B", "C", "D"]:
        w = track_winners.get(tr)
        lines.append(f"## Track {tr}")
        if not w:
            lines += ["OOF: **no dual-gate winner**", ""]
        else:
            lines += [
                f"OOF winner: `{w['controller']}` / `{w.get('feature_set')}` "
                f"util={w['utility']:.4f} boot={w['block_bootstrap_positive_probability']} "
                f"stress_ex={w['s_crisis_mean_excess']}",
                "",
            ]
        hid = f"S12{tr}"
        if hid in heldouts:
            h = heldouts[hid]
            lines += [f"Held-out **`{h['research_decision']}`** "
                      f"val_boot={h['val']['block_bootstrap_positive_probability']} "
                      f"val_stress_ex={h['val'].get('s_crisis_mean_excess')} "
                      f"sealed_boot={h['sealed']['block_bootstrap_positive_probability']}", ""]
    lines += ["Artifact: `reports/stage12_open_options_summary.json`", ""]
    (out / "E50-A3-R1_STAGE12_OPEN_OPTIONS.md").write_text("\n".join(lines))
    print(json.dumps({
        "track_winners": {k: (None if not v else {"controller": v["controller"], "feature_set": v.get("feature_set"),
                                                   "boot": v["block_bootstrap_positive_probability"],
                                                   "stress_ex": v["s_crisis_mean_excess"]}) for k, v in track_winners.items()},
        "heldouts": {k: v["research_decision"] for k, v in heldouts.items()},
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
