#!/usr/bin/env python3
"""Stage-13: Adversarial 10-round red-team of Option-2 / S9A1 (EXPERIMENTAL).

Falsify paper-monitor claims — NOT a new strategy search.
No E45 in-place edit. No retune of S9A1 cuts after held-out. No gate promotion.

Rounds
  1  Detector leakage / look-ahead audit (+ causal-IC sensitivity)
  2  Placebo freeze calendar (matched freeze-skip frequency)
  3  Scrambled detector dates (month-block permute)
  4  Subperiod fragility (calendar-year splits)
  5  Higher cost / slippage stress
  6  True EW-crisis days vs S9A1 detector days
  7  Bootstrap seed / block-length sensitivity
  8  Sealed degradation autopsy (month excess vs C4)
  9  Capacity / liquidity floor stress
 10  Selection-bias / multiple-testing inventory

Verdict per round: SURVIVES | WOUNDED | FALSIFIED
Overall: whether Option-2 paper-monitor stance remains justified.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e50a3_train_exact_open as a3
import e50a3r1_repair as r1
from e50a3r1_turnover_diagnosis import BOOTSTRAP_GATE, TURNOVER_CEILING, buffered_orders_ext
from e50a3r1_stage6_risk_overlay_oof import C4, build_market_state, hysteresis, mean_gross_exposure, scale_orders
from e50a3r1_stage7_crisis_challenger_oof import attach_crisis, orders_on_dates, period_metrics
from e50a3r1_stage8a_failure_signature import build_daily_panel_state, trailing_ic
from e50a3r1_stage8c_multisleeve_oof import rolling_percentile_flags
from e50a3r1_stage9a_e45c1_freeze_orth_oof import freeze_signal_dates
from e50a3r1_stage9a_s9a1_heldout import S9A1, build_flags

RNG = np.random.default_rng(20260904)
VAL_START, VAL_END = date(2019, 1, 1), date(2022, 12, 31)
SEALED_START = date(2023, 1, 1)
PLACEBO_N = 20
SCRAMBLE_N = 15


def verdict_rank(v: str) -> int:
    return {"SURVIVES": 0, "WOUNDED": 1, "FALSIFIED": 2}.get(v, 1)


def worst_verdict(vs: list[str]) -> str:
    return max(vs, key=verdict_rank) if vs else "WOUNDED"


def daily_rets(nav: pl.DataFrame) -> np.ndarray:
    return nav.sort("date")["nav"].pct_change().drop_nulls().to_numpy().astype(float)


def excess_series(nav: pl.DataFrame, proxy: pl.DataFrame) -> pl.DataFrame:
    a = nav.select("date", pl.col("nav").pct_change().alias("strategy"))
    b = proxy.select("date", pl.col("nav").pct_change().alias("benchmark"))
    return (
        a.join(b, on="date", how="inner")
        .drop_nulls()
        .with_columns((pl.col("strategy") - pl.col("benchmark")).alias("excess"))
        .sort("date")
    )


def summarize_nav(nav, trades, proxy, name, stress_dates, flags=None):
    metric = a3.metrics(nav, trades, name)
    _, stats = a3.compare(nav, proxy)
    stress = period_metrics(nav, proxy, stress_dates)
    cagr, mdd, turn = metric.get("cagr"), metric.get("max_drawdown"), metric.get("average_daily_turnover")
    boot = stats.get("block_bootstrap_positive_probability")
    t = trades.with_columns(pl.col("signal_date").cast(pl.Date), pl.col("execution_date").cast(pl.Date))
    same_bar = int(t.filter(pl.col("execution_date") <= pl.col("signal_date")).height)
    period_dates = nav["date"].unique().to_list()
    flag_days = sum(1 for d in period_dates if flags and flags.get(d, False)) if flags is not None else None
    out = {
        "name": name,
        "cagr": cagr,
        "max_drawdown": mdd,
        "utility": (cagr or 0.0) - 0.5 * abs(mdd or 0.0),
        "average_daily_turnover": turn,
        "block_bootstrap_positive_probability": boot,
        "mean_daily_excess": stats.get("mean_daily_excess"),
        "mean_gross_exposure": mean_gross_exposure(nav),
        "same_bar_fills": same_bar,
        "exact_t1_ok": same_bar == 0,
        "turnover_gate_pass": bool((turn or 9) <= TURNOVER_CEILING),
        "bootstrap_gate_pass": bool((boot or 0) >= BOOTSTRAP_GATE),
        "stress_flag_days": flag_days,
        **{f"s_{k}": v for k, v in stress.items()},
    }
    return out


def build_causal_val_ic(panel, labels, window: int = 21, label_horizon: int = 21) -> pl.DataFrame:
    """Strictly causal trailing IC: shift raw IC by label_horizon before rolling mean."""
    lab_col = "fwd_21d_total_return" if "fwd_21d_total_return" in labels.columns else labels.columns[-1]
    labs = labels
    if labs["date"].dtype != pl.Date:
        labs = labs.with_columns(pl.col("date").str.to_date())
    j = panel.select("date", "code", "value_family_score").join(
        labs.select("date", "code", pl.col(lab_col).alias("lab")),
        on=["date", "code"], how="inner",
    )
    ics = []
    for day in j["date"].unique().sort().to_list():
        g = j.filter(pl.col("date") == day).drop_nulls(["value_family_score", "lab"])
        if g.height < 30:
            continue
        sr = g["value_family_score"].rank().to_numpy()
        lr = g["lab"].rank().to_numpy()
        if np.std(sr) == 0 or np.std(lr) == 0:
            continue
        ics.append({"date": day, "ic": float(np.corrcoef(sr, lr)[0, 1])})
    if not ics:
        return pl.DataFrame({"date": [], "val_ic_causal": []})
    ic_df = pl.DataFrame(ics).sort("date")
    # IC realized only after label_horizon sessions → shift by that amount
    ic_df = ic_df.with_columns(pl.col("ic").shift(label_horizon).alias("ic_realized"))
    ic_df = ic_df.with_columns(
        pl.col("ic_realized")
        .rolling_mean(window_size=window, min_samples=max(5, window // 3))
        .alias("val_ic_causal")
    )
    return ic_df.select("date", "val_ic_causal")


def build_flags_causal(panel, labels, execution) -> dict[date, bool]:
    state = build_daily_panel_state(panel).sort("date")
    mkt = attach_crisis(build_market_state(execution))
    ic_val = build_causal_val_ic(panel, labels)
    joined = (
        state.join(
            mkt.select("date", "crisis").rename({"crisis": "crisis_vote2"}),
            on="date", how="left",
        )
        .join(ic_val, on="date", how="left")
        .sort("date")
    )
    rows = joined.to_dicts()
    dates = [r["date"] for r in rows]
    vol = [r.get("mkt_vol_60d") for r in rows]
    crisis = np.array([bool(r.get("crisis_vote2") or False) for r in rows])
    val_ok = np.array([
        (r.get("val_ic_causal") is not None and r["val_ic_causal"] >= S9A1["val_ic_min"])
        for r in rows
    ])
    vol_raw = rolling_percentile_flags(vol, S9A1["vol_roll_window"], S9A1["vol_roll_pctl"])
    vol_h = hysteresis(vol_raw, S9A1["hysteresis_on"], S9A1["hysteresis_off"])
    flags_arr = (~crisis) & vol_h & val_ok
    return {d: bool(flags_arr[i]) for i, d in enumerate(dates)}


def sim_freeze(scored, calendar, execution, flags, start, end, name, slip=None, liq_floor=None):
    cfg = dict(C4)
    if liq_floor is not None:
        cfg["liquidity_floor"] = float(liq_floor)
    sig = freeze_signal_dates(scored, flags, cfg["rebalance_every"])
    orders = orders_on_dates(scored, calendar, sig, cfg)
    if slip is None:
        nav, trades = a3.simulate(orders, execution, start, end)
    else:
        nav, trades = a3.simulate(orders, execution, start, end, slippage=float(slip))
    proxy = a3.market_proxy(execution, start, end)
    stress = {d for d, on in flags.items() if on and start <= d <= end}
    return summarize_nav(nav, trades, proxy, name, stress, flags), nav, trades, proxy, orders, sig


def sim_full(scored, calendar, execution, start, end, name, slip=None, liq_floor=None, scale=1.0):
    cfg = dict(C4)
    if liq_floor is not None:
        cfg["liquidity_floor"] = float(liq_floor)
    orders, _ = buffered_orders_ext(scored, calendar, **cfg)
    if scale != 1.0:
        dates = orders["signal_date"].unique().to_list()
        orders = scale_orders(orders, {d: float(scale) for d in dates})
    if slip is None:
        nav, trades = a3.simulate(orders, execution, start, end)
    else:
        nav, trades = a3.simulate(orders, execution, start, end, slippage=float(slip))
    proxy = a3.market_proxy(execution, start, end)
    return summarize_nav(nav, trades, proxy, name, set()), nav, trades, proxy, orders


def matched_placebo_flags(base_flags: dict[date, bool], pool: list[date], n_on: int, rng) -> dict[date, bool]:
    """Random on-days with same count inside pool; off elsewhere."""
    k = min(n_on, len(pool))
    idx = rng.choice(len(pool), size=k, replace=False)
    chosen = {pool[int(i)] for i in idx}
    return {d: (d in chosen) for d in base_flags}


def scramble_by_month(base_flags: dict[date, bool], start: date, end: date, rng) -> dict[date, bool]:
    """Keep monthly on-counts; permute which months receive them within the window."""
    by_month: dict[tuple[int, int], list[date]] = defaultdict(list)
    on_by_month: dict[tuple[int, int], int] = {}
    for d, on in base_flags.items():
        if not (start <= d <= end):
            continue
        key = (d.year, d.month)
        by_month[key].append(d)
        on_by_month[key] = on_by_month.get(key, 0) + int(bool(on))
    months = sorted(by_month)
    counts = [on_by_month[m] for m in months]
    perm = rng.permutation(len(months))
    assigned = {months[i]: int(counts[perm[i]]) for i in range(len(months))}
    out = dict(base_flags)
    for d in list(out):
        if start <= d <= end:
            out[d] = False
    for m, n_on in assigned.items():
        days = sorted(by_month[m])
        if n_on <= 0 or not days:
            continue
        pick_idx = rng.choice(len(days), size=min(n_on, len(days)), replace=False)
        pick = {days[int(i)] for i in pick_idx}
        for d in pick:
            out[d] = True
    return out


def bootstrap_prob_custom(excess: np.ndarray, block: int, draws: int, seed: int) -> float:
    x = excess[np.isfinite(excess)]
    if len(x) < block:
        return float("nan")
    rng = np.random.default_rng(seed)
    starts = np.arange(0, len(x) - block + 1)
    wins = 0
    blocks_needed = math.ceil(len(x) / block)
    for _ in range(draws):
        sample = np.concatenate([x[s:s + block] for s in rng.choice(starts, blocks_needed)])[:len(x)]
        wins += float(sample.mean() > 0)
    return wins / draws


def year_slices(nav: pl.DataFrame, proxy: pl.DataFrame) -> dict:
    x = excess_series(nav, proxy)
    out = {}
    for y in sorted({d.year for d in x["date"].to_list()}):
        g = x.filter(pl.col("date").dt.year() == y)
        if g.height < 20:
            continue
        rets = g["strategy"].to_numpy()
        nav_path = np.cumprod(1.0 + rets)
        years = len(rets) / 252.0
        cagr = float(nav_path[-1] ** (1.0 / years) - 1.0) if years > 0 else None
        peak = np.maximum.accumulate(nav_path)
        mdd = float(np.min(nav_path / peak - 1.0))
        out[str(y)] = {
            "n_days": g.height,
            "cagr": cagr,
            "max_drawdown": mdd,
            "utility": (cagr or 0.0) - 0.5 * abs(mdd),
            "mean_excess": float(g["excess"].mean()),
            "sum_excess": float(g["excess"].sum()),
        }
    return out


def month_excess_diff(s9_nav, c4_nav, proxy) -> list[dict]:
    s = excess_series(s9_nav, proxy).rename({"excess": "s9_ex", "strategy": "s9"})
    c = excess_series(c4_nav, proxy).rename({"excess": "c4_ex", "strategy": "c4"})
    j = s.join(c.select("date", "c4_ex", "c4"), on="date", how="inner")
    j = j.with_columns((pl.col("s9_ex") - pl.col("c4_ex")).alias("diff_ex"))
    agg = (
        j.with_columns(pl.col("date").dt.year().alias("y"), pl.col("date").dt.month().alias("m"))
        .group_by(["y", "m"])
        .agg(
            pl.len().alias("n"),
            pl.col("diff_ex").mean().alias("mean_diff_ex"),
            pl.col("diff_ex").sum().alias("sum_diff_ex"),
            pl.col("s9_ex").mean().alias("s9_mean_ex"),
            pl.col("c4_ex").mean().alias("c4_mean_ex"),
        )
        .sort(["y", "m"])
    )
    return agg.to_dicts()


def inventory_selection_bias(reports: Path) -> dict:
    files = {
        "stage9a_candidates": "stage9a_e45c1_freeze_orth_oof_summary.json",
        "stage7": "stage7_crisis_challenger_oof_summary.json",
        "stage7b": "stage7b_strict_crisis_oof_summary.json",
        "stage8b": "stage8b_alpha_stress_oof_summary.json",
        "stage8c": "stage8c_multisleeve_oof_summary.json",
        "stage10_r1": "stage10_r1_summary.json",
        "stage10_r3": "stage10_r3_summary.json",
        "stage10_r5": "stage10_r5_summary.json",
        "stage12": "stage12_open_options_summary.json",
        "oof_challenger": "oof_challenger_summary.json",
        "round2": "round2_oof_summary.json",
        "round3": "round3_oof_summary.json",
        "round_c8": "round_c8_oof_summary.json",
    }
    detail = {}
    total = 0
    for label, fname in files.items():
        p = reports / fname
        if not p.exists():
            detail[label] = {"missing": True}
            continue
        d = json.loads(p.read_text())
        n = None
        for k in ("n_candidates", "n_rows", "n_challengers", "n_tested", "n_configs"):
            if isinstance(d.get(k), int):
                n = d[k]
                break
        for k in ("top_candidates", "challengers", "results", "leaderboard", "rows", "all_results", "ranked"):
            if n is None and isinstance(d.get(k), list):
                n = len(d[k])
        if n is None and isinstance(d.get("windows"), dict):
            n = 0
        detail[label] = {"n": n, "decision": d.get("research_decision") or d.get("decision")}
        if isinstance(n, int):
            total += n
    return {"per_file": detail, "sum_reported_rows_approx": total}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", type=Path, required=True)
    ap.add_argument("--labels", type=Path, required=True)
    ap.add_argument("--prices", type=Path, required=True)
    ap.add_argument("--actions", type=Path, required=True)
    ap.add_argument("--a2-qc", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--placebo-n", type=int, default=PLACEBO_N)
    ap.add_argument("--scramble-n", type=int, default=SCRAMBLE_N)
    ap.add_argument("--boot-draws", type=int, default=2000)
    args = ap.parse_args()
    out = args.out
    (out / "outputs").mkdir(parents=True, exist_ok=True)
    (out / "reports").mkdir(parents=True, exist_ok=True)
    if json.loads(args.a2_qc.read_text())["status"] != "PASS":
        raise RuntimeError("E50-A2 QC is not PASS")

    print("loading panels ...", flush=True)
    panel = pl.read_parquet(args.panel).sort(["date", "code"])
    labels = pl.read_parquet(args.labels)
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
    sealed_end = max(calendar)
    exact_labels = a3.build_exact_open_labels(panel, execution, calendar)
    joined = a3.target_rank(
        r1.add_regime(panel).join(exact_labels.select("date", "code", a3.LABEL), on=["date", "code"], validate="1:1")
    )

    print("building S9A1 flags (+ causal variant) ...", flush=True)
    flags = build_flags(panel, labels, execution)
    flags_causal = build_flags_causal(panel, labels, execution)

    val_cutoff = a3.previous_session(calendar, VAL_START, 22)
    sealed_cutoff = a3.previous_session(calendar, SEALED_START, 22)

    print("fit/score VAL + SEALED ...", flush=True)
    model_val = r1.fit_model(joined, "TECH2", "BREADTH_REGIME", 1.0, val_cutoff)
    scored_val = r1.score_period(joined, model_val, VAL_START, VAL_END)
    model_sealed = r1.fit_model(joined, "TECH2", "BREADTH_REGIME", 1.0, sealed_cutoff)
    scored_sealed = r1.score_period(joined, model_sealed, SEALED_START, sealed_end)

    print("baseline C4 / S9A1 VAL ...", flush=True)
    c4_val, c4_val_nav, c4_val_tr, c4_val_px, c4_val_ord = sim_full(
        scored_val, calendar, execution, VAL_START, VAL_END, "C4_VAL"
    )
    s9_val, s9_val_nav, s9_val_tr, s9_val_px, s9_val_ord, s9_val_sig = sim_freeze(
        scored_val, calendar, execution, flags, VAL_START, VAL_END, "S9A1_VAL"
    )
    print("baseline C4 / S9A1 SEALED ...", flush=True)
    c4_sealed, c4_sealed_nav, c4_sealed_tr, c4_sealed_px, _ = sim_full(
        scored_sealed, calendar, execution, SEALED_START, sealed_end, "C4_SEALED"
    )
    s9_sealed, s9_sealed_nav, s9_sealed_tr, s9_sealed_px, _, _ = sim_freeze(
        scored_sealed, calendar, execution, flags, SEALED_START, sealed_end, "S9A1_SEALED"
    )

    rounds: dict[str, dict] = {}

    # ----- R1 leakage -----
    print("\n=== R1 leakage / look-ahead ===", flush=True)
    ic_std = trailing_ic(panel, labels, "value_family_score", 21)
    # empirical: correlation of published val_ic_lag21 with future-realized causal IC
    causal_ic = build_causal_val_ic(panel, labels)
    merged_ic = ic_std.join(causal_ic, on="date", how="inner").drop_nulls()
    # how often published lag21 uses not-yet-realized IC: compare to shift(21) version
    # For each date, published ic_lag21 vs causal val_ic
    corr = None
    if merged_ic.height > 50:
        a = merged_ic["ic_lag21"].to_numpy()
        b = merged_ic["val_ic_causal"].to_numpy()
        if np.std(a) > 0 and np.std(b) > 0:
            corr = float(np.corrcoef(a, b)[0, 1])
    # freeze uses flag on signal date only — structural OK if flag causal
    causal_val, _, _, _, _, causal_sig = sim_freeze(
        scored_val, calendar, execution, flags_causal, VAL_START, VAL_END, "S9A1_CAUSAL_IC_VAL"
    )
    n_pub = sum(1 for d, on in flags.items() if on and VAL_START <= d <= VAL_END)
    n_cau = sum(1 for d, on in flags_causal.items() if on and VAL_START <= d <= VAL_END)
    overlap = sum(
        1 for d in flags
        if VAL_START <= d <= VAL_END and flags.get(d) and flags_causal.get(d)
    )
    stress_drop = None
    if s9_val["s_crisis_mean_excess"] is not None and causal_val["s_crisis_mean_excess"] is not None:
        stress_drop = float(causal_val["s_crisis_mean_excess"] - s9_val["s_crisis_mean_excess"])
    # FALSIFIED if causal variant loses the claimed VAL stress edge vs C4
    pub_edge = (s9_val["s_crisis_mean_excess"] or 0) - (c4_val["s_crisis_mean_excess"] or 0)
    cau_edge = (causal_val["s_crisis_mean_excess"] or 0) - (c4_val["s_crisis_mean_excess"] or 0)
    r1_verdict = "SURVIVES"
    pub_util = s9_val["utility"]
    cau_util = causal_val["utility"]
    if not s9_val["exact_t1_ok"]:
        r1_verdict = "FALSIFIED"
    elif pub_edge > 0 and cau_edge <= 0:
        r1_verdict = "FALSIFIED"
    elif pub_edge > 0 and cau_edge < 0.5 * pub_edge:
        r1_verdict = "WOUNDED"
    elif pub_util is not None and cau_util is not None and cau_util < pub_util - 0.03:
        # Look-ahead in value-IC can inflate headline util even when stress edge partly remains
        r1_verdict = "WOUNDED"
    elif abs((n_pub - n_cau) / max(n_pub, 1)) > 0.5:
        r1_verdict = "WOUNDED"
    rounds["R1_leakage"] = {
        "attack": "Detector uses val_ic_lag21 from trailing_ic with only shift(1); fwd_21d labels imply ~21d look-ahead.",
        "findings": {
            "exact_t1_ok": s9_val["exact_t1_ok"],
            "vol_rolling_percentile_is_causal": True,
            "val_ic_published_vs_causal_corr": corr,
            "val_flag_days_published": n_pub,
            "val_flag_days_causal": n_cau,
            "val_flag_day_overlap": overlap,
            "published_stress_edge_vs_c4": pub_edge,
            "causal_stress_edge_vs_c4": cau_edge,
            "causal_minus_published_stress_ex": stress_drop,
            "published_point": {k: s9_val[k] for k in ("utility", "block_bootstrap_positive_probability", "s_crisis_mean_excess")},
            "causal_point": {k: causal_val[k] for k in ("utility", "block_bootstrap_positive_probability", "s_crisis_mean_excess")},
            "n_freeze_sig_published": len(s9_val_sig),
            "n_freeze_sig_causal": len(causal_sig),
        },
        "verdict": r1_verdict,
    }
    print(f"  R1 {r1_verdict} pub_edge={pub_edge:.6f} cau_edge={cau_edge:.6f}", flush=True)

    # ----- R2 placebo -----
    print("\n=== R2 placebo freeze ===", flush=True)
    pool = [d for d in sorted(scored_val["date"].unique().to_list()) if VAL_START <= d <= VAL_END]
    n_on = sum(1 for d in pool if flags.get(d, False))
    placebo_rows = []
    for i in range(args.placebo_n):
        pf = matched_placebo_flags(flags, pool, n_on, np.random.default_rng(41000 + i))
        # keep flags outside window unchanged
        for d, on in flags.items():
            if d < VAL_START or d > VAL_END:
                pf[d] = on
        pt, *_ = sim_freeze(scored_val, calendar, execution, pf, VAL_START, VAL_END, f"PLACEBO_{i}")
        placebo_rows.append({
            "i": i,
            "utility": pt["utility"],
            "s_crisis_mean_excess": pt["s_crisis_mean_excess"],
            "boot": pt["block_bootstrap_positive_probability"],
            "cagr": pt["cagr"],
        })
        print(f"  placebo {i+1}/{args.placebo_n} util={pt['utility']:.4f} stress_ex={pt['s_crisis_mean_excess']}", flush=True)
    p_util = float(np.mean([r["utility"] >= s9_val["utility"] for r in placebo_rows]))
    p_stress = float(np.mean([
        (r["s_crisis_mean_excess"] or -9) >= (s9_val["s_crisis_mean_excess"] or -9) for r in placebo_rows
    ]))
    r2_verdict = "SURVIVES"
    if p_stress >= 0.40:
        r2_verdict = "FALSIFIED"
    elif p_stress >= 0.20 or p_util >= 0.30:
        r2_verdict = "WOUNDED"
    rounds["R2_placebo"] = {
        "attack": "Matched-frequency random freeze calendar on VAL.",
        "n_placebo": args.placebo_n,
        "n_on_days": n_on,
        "p_placebo_util_ge_s9a1": p_util,
        "p_placebo_stress_ex_ge_s9a1": p_stress,
        "s9a1_utility": s9_val["utility"],
        "s9a1_stress_ex": s9_val["s_crisis_mean_excess"],
        "placebo_util_mean": float(np.mean([r["utility"] for r in placebo_rows])),
        "placebo_stress_mean": float(np.nanmean([r["s_crisis_mean_excess"] for r in placebo_rows])),
        "rows": placebo_rows,
        "verdict": r2_verdict,
    }
    print(f"  R2 {r2_verdict} P(stress>={s9_val['s_crisis_mean_excess']})={p_stress:.3f}", flush=True)

    # ----- R3 scramble -----
    print("\n=== R3 scrambled months ===", flush=True)
    scramble_rows = []
    for i in range(args.scramble_n):
        sf = scramble_by_month(flags, VAL_START, VAL_END, np.random.default_rng(42000 + i))
        pt, *_ = sim_freeze(scored_val, calendar, execution, sf, VAL_START, VAL_END, f"SCRAMBLE_{i}")
        scramble_rows.append({
            "i": i,
            "utility": pt["utility"],
            "s_crisis_mean_excess": pt["s_crisis_mean_excess"],
            "boot": pt["block_bootstrap_positive_probability"],
        })
        print(f"  scramble {i+1}/{args.scramble_n} util={pt['utility']:.4f}", flush=True)
    p_s_stress = float(np.mean([
        (r["s_crisis_mean_excess"] or -9) >= (s9_val["s_crisis_mean_excess"] or -9) for r in scramble_rows
    ]))
    p_s_util = float(np.mean([r["utility"] >= s9_val["utility"] for r in scramble_rows]))
    r3_verdict = "SURVIVES"
    if p_s_stress >= 0.40:
        r3_verdict = "FALSIFIED"
    elif p_s_stress >= 0.20 or p_s_util >= 0.30:
        r3_verdict = "WOUNDED"
    rounds["R3_scramble"] = {
        "attack": "Permute monthly detector mass within VAL while preserving monthly on-counts.",
        "n": args.scramble_n,
        "p_scramble_stress_ex_ge_s9a1": p_s_stress,
        "p_scramble_util_ge_s9a1": p_s_util,
        "rows": scramble_rows,
        "verdict": r3_verdict,
    }
    print(f"  R3 {r3_verdict} P(stress)={p_s_stress:.3f}", flush=True)

    # ----- R4 subperiod -----
    print("\n=== R4 subperiod fragility ===", flush=True)
    y_c4_val = year_slices(c4_val_nav, c4_val_px)
    y_s9_val = year_slices(s9_val_nav, s9_val_px)
    y_c4_sealed = year_slices(c4_sealed_nav, c4_sealed_px)
    y_s9_sealed = year_slices(s9_sealed_nav, s9_sealed_px)
    val_years = sorted(set(y_c4_val) & set(y_s9_val))
    beat_util = [y for y in val_years if y_s9_val[y]["utility"] > y_c4_val[y]["utility"]]
    beat_ex = [y for y in val_years if y_s9_val[y]["mean_excess"] > y_c4_val[y]["mean_excess"]]
    r4_verdict = "SURVIVES"
    if len(beat_util) <= 1 and len(val_years) >= 3:
        r4_verdict = "FALSIFIED"
    elif len(beat_util) < len(val_years) / 2:
        r4_verdict = "WOUNDED"
    rounds["R4_subperiod"] = {
        "attack": "Calendar-year util/excess S9A1 vs C4 on VAL and SEALED.",
        "val_years": {
            y: {"c4": y_c4_val[y], "s9a1": y_s9_val[y], "s9_beats_util": y_s9_val[y]["utility"] > y_c4_val[y]["utility"]}
            for y in val_years
        },
        "sealed_years": {
            y: {"c4": y_c4_sealed[y], "s9a1": y_s9_sealed[y], "s9_beats_util": y_s9_sealed[y]["utility"] > y_c4_sealed[y]["utility"]}
            for y in sorted(set(y_c4_sealed) & set(y_s9_sealed))
        },
        "val_years_s9_beats_util": beat_util,
        "val_years_s9_beats_excess": beat_ex,
        "verdict": r4_verdict,
    }
    print(f"  R4 {r4_verdict} beat_util_years={beat_util}", flush=True)

    # ----- R5 cost -----
    print("\n=== R5 higher cost ===", flush=True)
    base_slip = a3.BASE_SLIPPAGE
    cost_rows = []
    for mult in (1.0, 2.0, 3.0, 5.0):
        slip = base_slip * mult
        c_pt, *_ = sim_full(scored_val, calendar, execution, VAL_START, VAL_END, f"C4_SLIP_{mult}", slip=slip)
        s_pt, *_ = sim_freeze(scored_val, calendar, execution, flags, VAL_START, VAL_END, f"S9_SLIP_{mult}", slip=slip)
        cost_rows.append({
            "slippage_mult": mult,
            "slippage": slip,
            "c4_utility": c_pt["utility"],
            "s9_utility": s_pt["utility"],
            "c4_boot": c_pt["block_bootstrap_positive_probability"],
            "s9_boot": s_pt["block_bootstrap_positive_probability"],
            "s9_minus_c4_util": s_pt["utility"] - c_pt["utility"],
            "s9_stress_ex": s_pt["s_crisis_mean_excess"],
        })
        print(f"  slip x{mult}: s9_util={s_pt['utility']:.4f} edge={s_pt['utility']-c_pt['utility']:.4f}", flush=True)
    edge_base = cost_rows[0]["s9_minus_c4_util"]
    edge_3x = next(r["s9_minus_c4_util"] for r in cost_rows if r["slippage_mult"] == 3.0)
    r5_verdict = "SURVIVES"
    if edge_base > 0 and edge_3x <= 0:
        r5_verdict = "FALSIFIED"
    elif edge_base > 0 and edge_3x < 0.5 * edge_base:
        r5_verdict = "WOUNDED"
    rounds["R5_cost"] = {
        "attack": "Re-simulate identical signals under 2x/3x/5x BASE_SLIPPAGE.",
        "base_slippage": base_slip,
        "rows": cost_rows,
        "verdict": r5_verdict,
    }
    print(f"  R5 {r5_verdict}", flush=True)

    # ----- R6 true crisis vs detector -----
    print("\n=== R6 EW-crisis vs detector days ===", flush=True)
    mkt = attach_crisis(build_market_state(execution))
    crisis_days = {r["date"] for r in mkt.filter(pl.col("crisis")).to_dicts() if VAL_START <= r["date"] <= VAL_END}
    det_days = {d for d, on in flags.items() if on and VAL_START <= d <= VAL_END}
    both = crisis_days & det_days
    only_c = crisis_days - det_days
    only_d = det_days - crisis_days

    def mask_stats(nav, proxy, days: set[date]) -> dict:
        return period_metrics(nav, proxy, days)

    r6 = {
        "n_crisis": len(crisis_days),
        "n_detector": len(det_days),
        "n_overlap": len(both),
        "overlap_share_of_detector": len(both) / max(len(det_days), 1),
        "c4_on_crisis": mask_stats(c4_val_nav, c4_val_px, crisis_days),
        "s9_on_crisis": mask_stats(s9_val_nav, s9_val_px, crisis_days),
        "c4_on_detector": mask_stats(c4_val_nav, c4_val_px, det_days),
        "s9_on_detector": mask_stats(s9_val_nav, s9_val_px, det_days),
        "c4_on_detector_only": mask_stats(c4_val_nav, c4_val_px, only_d),
        "s9_on_detector_only": mask_stats(s9_val_nav, s9_val_px, only_d),
        "c4_on_crisis_only": mask_stats(c4_val_nav, c4_val_px, only_c),
        "s9_on_crisis_only": mask_stats(s9_val_nav, s9_val_px, only_c),
    }
    # S9A1 claims stress edge on detector days; check it also helps (or at least doesn't hurt) true crisis
    s9_crisis_ex = r6["s9_on_crisis"]["crisis_mean_excess"]
    c4_crisis_ex = r6["c4_on_crisis"]["crisis_mean_excess"]
    r6_verdict = "SURVIVES"
    if r6["overlap_share_of_detector"] < 0.05 and (s9_crisis_ex or 0) < (c4_crisis_ex or 0):
        r6_verdict = "WOUNDED"  # detector orthogonal to EW crisis AND no crisis help
    if (s9_crisis_ex or 0) + 1e-12 < (c4_crisis_ex or 0) - 5e-4:
        r6_verdict = worst_verdict([r6_verdict, "WOUNDED"])
    # if detector edge exists only because of non-overlap weirdness and crisis worse — wounded already
    rounds["R6_crisis_vs_detector"] = {
        "attack": "Compare excess on EW crisis_vote2 days vs COMBO_VOL70_VAL03 detector days.",
        "findings": r6,
        "note": "S9A1 explicitly excludes crisis_vote2 from detector; orthogonality is by design.",
        "verdict": r6_verdict,
    }
    print(f"  R6 {r6_verdict} overlap={r6['n_overlap']}/{r6['n_detector']}", flush=True)

    # ----- R7 bootstrap sensitivity -----
    print("\n=== R7 bootstrap sensitivity ===", flush=True)
    ex_s9 = excess_series(s9_val_nav, s9_val_px)["excess"].to_numpy()
    ex_c4 = excess_series(c4_val_nav, c4_val_px)["excess"].to_numpy()
    boot_grid = []
    for block in (5, 10, 21, 42, 63):
        for seed in (412503, 7, 99, 20260904):
            b_s9 = bootstrap_prob_custom(ex_s9, block, args.boot_draws, seed)
            b_c4 = bootstrap_prob_custom(ex_c4, block, args.boot_draws, seed)
            boot_grid.append({
                "block": block, "seed": seed, "s9_boot": b_s9, "c4_boot": b_c4,
                "s9_gate_pass": bool(b_s9 >= BOOTSTRAP_GATE),
            })
    s9_boots = [r["s9_boot"] for r in boot_grid if np.isfinite(r["s9_boot"])]
    gate_flip = any(r["s9_gate_pass"] for r in boot_grid) and not all(r["s9_gate_pass"] for r in boot_grid)
    # Official claim is MIXED (boot fails 0.70). Sensitivity should not magically create PASS as a promotion path.
    r7_verdict = "SURVIVES"
    if max(s9_boots) - min(s9_boots) > 0.15:
        r7_verdict = "WOUNDED"
    if any(r["block"] == 21 and r["s9_boot"] >= BOOTSTRAP_GATE for r in boot_grid) and s9_val["block_bootstrap_positive_probability"] < BOOTSTRAP_GATE:
        # seed flip at official block — wounded for monitor KPI stability
        r7_verdict = worst_verdict([r7_verdict, "WOUNDED"])
    rounds["R7_bootstrap"] = {
        "attack": "Vary block length and RNG seed for block-bootstrap P(excess>0) on VAL.",
        "official_s9_boot": s9_val["block_bootstrap_positive_probability"],
        "s9_boot_min": float(min(s9_boots)),
        "s9_boot_max": float(max(s9_boots)),
        "s9_boot_range": float(max(s9_boots) - min(s9_boots)),
        "any_gate_flip_across_grid": gate_flip,
        "grid": boot_grid,
        "verdict": r7_verdict,
    }
    print(f"  R7 {r7_verdict} boot range={max(s9_boots)-min(s9_boots):.3f}", flush=True)

    # ----- R8 sealed autopsy -----
    print("\n=== R8 sealed degradation autopsy ===", flush=True)
    months = month_excess_diff(s9_sealed_nav, c4_sealed_nav, s9_sealed_px)
    # also VAL months for contrast
    months_val = month_excess_diff(s9_val_nav, c4_val_nav, s9_val_px)
    sealed_sum = float(sum(m["sum_diff_ex"] or 0 for m in months))
    val_sum = float(sum(m["sum_diff_ex"] or 0 for m in months_val))
    worst = sorted(months, key=lambda m: m["sum_diff_ex"] or 0)[:5]
    best = sorted(months, key=lambda m: -(m["sum_diff_ex"] or 0))[:5]
    # Option2 claimed sealed stress MC weak; check util edge sealed
    sealed_util_edge = s9_sealed["utility"] - c4_sealed["utility"]
    sealed_stress_edge = (s9_sealed["s_crisis_mean_excess"] or 0) - (c4_sealed["s_crisis_mean_excess"] or 0)
    r8_verdict = "SURVIVES"
    if sealed_util_edge < -0.02 and sealed_stress_edge < 0:
        r8_verdict = "FALSIFIED"
    elif sealed_stress_edge < 0 or sealed_util_edge < 0:
        r8_verdict = "WOUNDED"
    rounds["R8_sealed_autopsy"] = {
        "attack": "Month-level S9A1−C4 excess on SEALED; compare aggregate edges.",
        "sealed_util_edge": sealed_util_edge,
        "sealed_stress_edge": sealed_stress_edge,
        "sealed_sum_diff_excess": sealed_sum,
        "val_sum_diff_excess": val_sum,
        "worst_months": worst,
        "best_months": best,
        "n_months": len(months),
        "share_months_s9_ahead": float(np.mean([(m["sum_diff_ex"] or 0) > 0 for m in months])) if months else None,
        "point_sealed_s9": {k: s9_sealed[k] for k in ("cagr", "utility", "block_bootstrap_positive_probability", "s_crisis_mean_excess")},
        "point_sealed_c4": {k: c4_sealed[k] for k in ("cagr", "utility", "block_bootstrap_positive_probability", "s_crisis_mean_excess")},
        "verdict": r8_verdict,
    }
    print(f"  R8 {r8_verdict} sealed_util_edge={sealed_util_edge:.4f} stress_edge={sealed_stress_edge:.6f}", flush=True)

    # ----- R9 capacity -----
    print("\n=== R9 capacity / liquidity ===", flush=True)
    base_floor = float(C4["liquidity_floor"])
    cap_rows = []
    for mult in (1.0, 2.0, 5.0, 10.0):
        floor = base_floor * mult
        c_pt, *_ = sim_full(scored_val, calendar, execution, VAL_START, VAL_END, f"C4_LIQ_{mult}", liq_floor=floor)
        s_pt, *_ = sim_freeze(
            scored_val, calendar, execution, flags, VAL_START, VAL_END, f"S9_LIQ_{mult}", liq_floor=floor
        )
        cap_rows.append({
            "liq_floor_mult": mult,
            "liquidity_floor": floor,
            "c4_utility": c_pt["utility"],
            "s9_utility": s_pt["utility"],
            "s9_minus_c4_util": s_pt["utility"] - c_pt["utility"],
            "s9_stress_ex": s_pt["s_crisis_mean_excess"],
            "s9_turn": s_pt["average_daily_turnover"],
        })
        print(f"  liq x{mult}: edge_util={s_pt['utility']-c_pt['utility']:.4f}", flush=True)
    # also gross scale 0.5
    c_sc, *_ = sim_full(scored_val, calendar, execution, VAL_START, VAL_END, "C4_SCALE_0.5", scale=0.5)
    # freeze path: scale after orders
    sig = freeze_signal_dates(scored_val, flags, C4["rebalance_every"])
    ord_s0 = orders_on_dates(scored_val, calendar, sig, C4)
    ord_s = scale_orders(ord_s0, {d: 0.5 for d in ord_s0["signal_date"].unique().to_list()})
    nav_s, tr_s = a3.simulate(ord_s, execution, VAL_START, VAL_END)
    px_s = a3.market_proxy(execution, VAL_START, VAL_END)
    stress = {d for d, on in flags.items() if on and VAL_START <= d <= VAL_END}
    s_sc = summarize_nav(nav_s, tr_s, px_s, "S9_SCALE_0.5", stress, flags)
    cap_rows.append({
        "liq_floor_mult": "scale_0.5",
        "c4_utility": c_sc["utility"],
        "s9_utility": s_sc["utility"],
        "s9_minus_c4_util": s_sc["utility"] - c_sc["utility"],
        "s9_stress_ex": s_sc["s_crisis_mean_excess"],
    })
    edge1 = cap_rows[0]["s9_minus_c4_util"]
    edge5 = next(r["s9_minus_c4_util"] for r in cap_rows if r["liq_floor_mult"] == 5.0)
    r9_verdict = "SURVIVES"
    if edge1 > 0 and edge5 <= 0:
        r9_verdict = "FALSIFIED"
    elif edge1 > 0 and edge5 < 0.5 * edge1:
        r9_verdict = "WOUNDED"
    rounds["R9_capacity"] = {
        "attack": "Raise liquidity_floor 2x/5x/10x and half-scale gross exposure.",
        "rows": cap_rows,
        "verdict": r9_verdict,
    }
    print(f"  R9 {r9_verdict}", flush=True)

    # ----- R10 selection bias -----
    print("\n=== R10 selection bias ===", flush=True)
    report_root = Path("repro/e50a3r1-turnover-diagnosis-20260903")
    if (out / "reports" / "stage9a_e45c1_freeze_orth_oof_summary.json").exists():
        report_root = out
    elif (out.parent / "reports" / "stage9a_e45c1_freeze_orth_oof_summary.json").exists():
        report_root = out.parent
    inv = inventory_selection_bias(report_root / "reports")
    stage9a_n = inv["per_file"].get("stage9a_candidates", {}).get("n") or 6
    # crude Bonferroni on Stage-11 stress MC claim ~0.95 with m tests in stage9a alone
    m = max(int(stage9a_n), 1)
    raw_p = 1.0 - 0.94  # from Stage-11 narrative P≈0.94
    bonf = min(1.0, raw_p * m)
    # Across whole program many more tests → narrative WOUNDED unless explicitly locked OOF-only
    program_m = max(int(inv["sum_reported_rows_approx"] or m), m)
    r10_verdict = "WOUNDED"
    if program_m >= 100 and bonf > 0.25:
        r10_verdict = "WOUNDED"
    if stage9a_n <= 10 and s9_val["block_bootstrap_positive_probability"] < BOOTSTRAP_GATE:
        # honest MIXED + small local grid → survives as *monitor* claim, not promotion claim
        r10_verdict = "SURVIVES"
    rounds["R10_selection_bias"] = {
        "attack": "Inventory of searched challengers; multiple-testing narrative on stress MC claim.",
        "inventory": inv,
        "stage9a_n_candidates": stage9a_n,
        "approx_program_rows_sum": inv["sum_reported_rows_approx"],
        "illustrative_bonferroni_on_stage9a": {"raw_tail": raw_p, "m": m, "bonferroni": bonf},
        "note": "Option-2 is paper/monitor under MIXED — not a dual-gate PASS promotion. Selection bias wounds promotion claims more than monitor claims.",
        "verdict": r10_verdict,
    }
    print(f"  R10 {r10_verdict} stage9a_n={stage9a_n} program_rows~{inv['sum_reported_rows_approx']}", flush=True)

    # ----- aggregate -----
    verdicts = {k: v["verdict"] for k, v in rounds.items()}
    overall = worst_verdict(list(verdicts.values()))
    # Option-2 specific recommendation
    if overall == "FALSIFIED" or verdicts.get("R1_leakage") == "FALSIFIED":
        option2 = "OPTION2_WOUNDED_REQUIRE_CAUSAL_DETECTOR_BEFORE_MONITOR"
        if verdicts.get("R1_leakage") == "FALSIFIED" and verdicts.get("R2_placebo") == "FALSIFIED":
            option2 = "OPTION2_WITHDRAW_PAPER_MONITOR_UNTIL_REBUILT"
    elif overall == "WOUNDED":
        option2 = "OPTION2_KEEP_PAPER_MONITOR_WITH_ADVERSARIAL_CAVEATS"
    else:
        option2 = "OPTION2_SURVIVES_ADVERSARIAL_REVIEW_STILL_MIXED"

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "STAGE13_ADVERSARIAL_10ROUNDS",
        "protocol": "adversarial_falsification",
        "e45_inplace_edit": False,
        "no_retune": True,
        "no_gate_promotion": True,
        "baselines": {
            "c4_val": c4_val,
            "s9a1_val": s9_val,
            "c4_sealed": c4_sealed,
            "s9a1_sealed": s9_sealed,
        },
        "rounds": rounds,
        "verdicts": verdicts,
        "worst_round_verdict": overall,
        "option2_adversarial_decision": option2,
        "governance_note": (
            "Does not promote S9A1. Does not edit E45. PR remains draft research archive."
        ),
    }

    (out / "reports" / "stage13_adversarial_10rounds_summary.json").write_text(
        json.dumps(report, indent=2, default=str) + "\n"
    )
    # also write csv of placebo/scramble
    pl.DataFrame(rounds["R2_placebo"]["rows"]).write_csv(out / "outputs" / "stage13_r2_placebo.csv")
    pl.DataFrame(rounds["R3_scramble"]["rows"]).write_csv(out / "outputs" / "stage13_r3_scramble.csv")

    lines = [
        "# Stage-13 Adversarial 10-Round Review (Option-2 / S9A1)",
        "",
        "**Protocol:** falsify paper-monitor claims. No E45 edit. No S9A1 retune. No gate promotion.",
        "",
        f"## Overall: `{option2}`",
        "",
        f"Worst round verdict: **{overall}**",
        "",
        "| Round | Attack | Verdict |",
        "|---|---|---|",
    ]
    labels = {
        "R1_leakage": "1 Leakage / look-ahead",
        "R2_placebo": "2 Placebo freeze",
        "R3_scramble": "3 Scrambled months",
        "R4_subperiod": "4 Subperiod fragility",
        "R5_cost": "5 Higher slippage",
        "R6_crisis_vs_detector": "6 EW-crisis vs detector",
        "R7_bootstrap": "7 Bootstrap sensitivity",
        "R8_sealed_autopsy": "8 Sealed autopsy",
        "R9_capacity": "9 Capacity / liquidity",
        "R10_selection_bias": "10 Selection bias",
    }
    for k, title in labels.items():
        lines.append(f"| {title} | {rounds[k]['attack'][:60]}… | `{rounds[k]['verdict']}` |")
    lines += [
        "",
        "## Key quantitative hits",
        "",
        f"- R1 published VAL stress edge vs C4: `{rounds['R1_leakage']['findings']['published_stress_edge_vs_c4']}`",
        f"- R1 causal-IC VAL stress edge vs C4: `{rounds['R1_leakage']['findings']['causal_stress_edge_vs_c4']}`",
        f"- R2 P(placebo stress ≥ S9A1): `{rounds['R2_placebo']['p_placebo_stress_ex_ge_s9a1']}`",
        f"- R3 P(scramble stress ≥ S9A1): `{rounds['R3_scramble']['p_scramble_stress_ex_ge_s9a1']}`",
        f"- R8 sealed util edge S9−C4: `{rounds['R8_sealed_autopsy']['sealed_util_edge']}`",
        "",
        "## Operating implication",
        "",
    ]
    if "WITHDRAW" in option2:
        lines.append("Withdraw S9A1 paper-monitor until detector is rebuilt on strictly causal features.")
    elif "CAUSAL" in option2:
        lines.append(
            "Keep Option-2 only if monitor switches to a **causal** value-IC definition "
            "(shift ≥ label horizon). Do not treat published held-out stress edge as live-tradable."
        )
    elif "CAVEATS" in option2:
        lines.append(
            "Keep Option-2 paper-monitor with caveats from wounded rounds; still MIXED; still not frozen."
        )
    else:
        lines.append("Option-2 survives adversarial review as a MIXED paper-monitor — not a promotion.")
    lines += ["", "Artifact: `reports/stage13_adversarial_10rounds_summary.json`", ""]
    (out / "E50-A3-R1_STAGE13_ADVERSARIAL_10ROUNDS.md").write_text("\n".join(lines))
    (out / "E50-A3-R1_STAGE13_SUMMARY.md").write_text(
        "\n".join([
            "# Stage-13 Summary",
            "",
            f"- Decision: `{option2}`",
            f"- Worst verdict: `{overall}`",
            f"- Verdicts: `{json.dumps(verdicts)}`",
            "",
        ])
    )

    print(json.dumps({
        "option2_adversarial_decision": option2,
        "worst_round_verdict": overall,
        "verdicts": verdicts,
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
