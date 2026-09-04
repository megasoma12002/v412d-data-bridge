#!/usr/bin/env python3
"""Stage-6 OOF: risk overlays to raise utility / cut MDD (EXPERIMENTAL).

Alpha frozen: TECH2 OOF scores + C4 portfolio name selection.
Hypothesis class: sleeve exposure scaling (cash buffer) — NOT E45 in-place,
NOT retuning C2/C4/C8/F1 features/rules.

Selection: 2011–2018 OOF only.
Gates remain EXPERIMENTAL (turnover ≤2.5%, bootstrap ≥0.70).
Primary rank among dual-gate passers: utility = CAGR - 0.5*|MDD|, then MDD.
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

C4 = {
    "top_k": 22,
    "rebalance_every": 42,
    "exit_multiple": 2.25,
    "neutralization": "NONE",
    "industry_cap": 5,
    "min_hold_cycles": 0,
    "liquidity_floor": 20_000_000.0,
    "replace_rank_gap": 5,
}


def build_market_state(execution: pl.DataFrame) -> pl.DataFrame:
    """Causal market EW path + risk features (T-known)."""
    daily = (
        execution.group_by("date")
        .agg(
            pl.col("open_total_return").mean().alias("ew_ret"),
            (pl.col("open_total_return") > 0).mean().alias("breadth_1d"),
        )
        .sort("date")
        .with_columns(
            (1.0 + pl.col("ew_ret").fill_null(0.0)).cum_prod().alias("ew_nav"),
        )
    )
    # Rolling vol / DD / breadth60 using only past+current (rolling includes T; overlay applied at T+1 via execution_date)
    rets = daily["ew_ret"].fill_null(0.0).to_numpy()
    nav = daily["ew_nav"].to_numpy()
    n = len(rets)
    vol20 = np.full(n, np.nan)
    dd120 = np.full(n, np.nan)
    breadth60 = np.full(n, np.nan)
    peak = nav[0]
    for i in range(n):
        peak = max(peak, nav[i])
        if i >= 19:
            w = rets[i - 19 : i + 1]
            vol20[i] = float(np.std(w, ddof=1) * math.sqrt(252)) if np.std(w, ddof=1) > 0 else 0.0
        if i >= 59:
            # approx breadth: fraction of last 60 days with positive EW ret
            breadth60[i] = float(np.mean(rets[i - 59 : i + 1] > 0))
        # dd vs rolling 120 peak
        lo = max(0, i - 119)
        peak120 = float(np.max(nav[lo : i + 1]))
        dd120[i] = nav[i] / peak120 - 1.0 if peak120 > 0 else 0.0

    # Strategy-independent regime (same definition as r1.add_regime needs panel; use EW mom proxy)
    # RISK_ON if 63d EW return >=0 and breadth60>=0.5
    ew_mom63 = np.full(n, np.nan)
    for i in range(n):
        if i >= 63 and nav[i - 63] > 0:
            ew_mom63[i] = nav[i] / nav[i - 63] - 1.0
    risk_on = (ew_mom63 >= 0) & (breadth60 >= 0.5)

    return daily.with_columns(
        pl.Series("vol20", vol20),
        pl.Series("dd120", dd120),
        pl.Series("breadth60", breadth60),
        pl.Series("ew_mom63", ew_mom63),
        pl.Series("risk_on", risk_on),
    )


def hysteresis(raw_flags: np.ndarray, on_need: int = 2, off_need: int = 5) -> np.ndarray:
    state, on_c, off_c = False, 0, 0
    out = np.zeros(len(raw_flags), dtype=bool)
    for i, flag in enumerate(raw_flags):
        if bool(flag):
            on_c += 1
            off_c = 0
            if on_c >= on_need:
                state = True
        else:
            off_c += 1
            on_c = 0
            if off_c >= off_need:
                state = False
        out[i] = state
    return out


def exposure_schedules(mkt: pl.DataFrame) -> dict[str, pl.DataFrame]:
    """Named exposure series indexed by date (gross ∈ [0,1])."""
    dates = mkt["date"].to_list()
    vol = mkt["vol20"].to_numpy()
    dd = mkt["dd120"].to_numpy()
    breadth = mkt["breadth60"].to_numpy()
    risk_on = mkt["risk_on"].to_numpy()
    n = len(dates)

    def series(vals: np.ndarray, name: str) -> pl.DataFrame:
        return pl.DataFrame({"date": dates, "exposure": vals.astype(float), "overlay": [name] * n})

    schedules = {
        "BASE_FULL": series(np.ones(n), "BASE_FULL"),
        "STATIC_070": series(np.full(n, 0.70), "STATIC_070"),
        "STATIC_050": series(np.full(n, 0.50), "STATIC_050"),
    }

    # RISK_OFF de-risk
    mom = mkt["ew_mom63"].to_numpy()
    exp = np.ones(n)
    for i in range(n):
        if np.isnan(mom[i]) or np.isnan(breadth[i]):
            exp[i] = 1.0
        elif (mom[i] >= 0) and (breadth[i] >= 0.5):
            exp[i] = 1.0
        else:
            exp[i] = 0.50
    schedules["REGIME_OFF_050"] = series(exp, "REGIME_OFF_050")

    # Soft DD brake on market EW (with hysteresis)
    raw = dd <= -0.10
    crisis = hysteresis(np.nan_to_num(raw.astype(float), nan=0.0) > 0.5)
    exp = np.ones(n)
    for i in range(n):
        if crisis[i]:
            exp[i] = 0.40 if (not np.isnan(dd[i]) and dd[i] <= -0.15) else 0.70
    schedules["DD_BRAKE"] = series(exp, "DD_BRAKE")

    # Vol target 15% annualized
    target = 0.15
    exp = np.ones(n)
    for i in range(n):
        if not np.isnan(vol[i]) and vol[i] > 1e-8:
            exp[i] = float(np.clip(target / vol[i], 0.25, 1.0))
    schedules["VOL_TARGET_15"] = series(exp, "VOL_TARGET_15")

    # Graduated votes (E1-inspired, sleeve-only — not E45)
    votes = (
        ((~np.isnan(dd)) & (dd <= -0.08)).astype(int)
        + ((~np.isnan(vol)) & (vol >= 0.22)).astype(int)
        + ((~np.isnan(breadth)) & (breadth <= 0.45)).astype(int)
    )
    exp = np.ones(n)
    for i in range(n):
        v = int(votes[i])
        if v >= 3:
            exp[i] = 0.40
        elif v >= 2:
            exp[i] = 0.70
    # smooth with hysteresis on votes>=2
    crisis2 = hysteresis(votes >= 2)
    exp2 = np.ones(n)
    for i in range(n):
        if crisis2[i]:
            exp2[i] = 0.40 if votes[i] >= 3 else 0.70
    schedules["VOTE_CRISIS"] = series(exp2, "VOTE_CRISIS")

    # Combined: min(vol target, dd brake)
    exp = np.minimum(
        schedules["VOL_TARGET_15"]["exposure"].to_numpy(),
        schedules["DD_BRAKE"]["exposure"].to_numpy(),
    )
    schedules["VOL15_x_DD"] = series(exp, "VOL15_x_DD")

    return schedules


def scale_orders(orders: pl.DataFrame, exposure_by_date: dict[date, float]) -> pl.DataFrame:
    rows = []
    for r in orders.iter_rows(named=True):
        sig = r["signal_date"]
        # Prefer signal_date exposure (known at T); fallback 1.0
        e = float(exposure_by_date.get(sig, 1.0))
        if math.isnan(e):
            e = 1.0
        e = float(np.clip(e, 0.0, 1.0))
        rr = dict(r)
        rr["target_weight"] = float(r["target_weight"]) * e
        rr["overlay_exposure"] = e
        rows.append(rr)
    return pl.DataFrame(rows)


def mean_gross_exposure(nav: pl.DataFrame) -> float:
    cash = nav["cash"].to_numpy()
    nav_v = nav["nav"].to_numpy()
    exp = 1.0 - cash / np.where(nav_v == 0, np.nan, nav_v)
    exp = exp[np.isfinite(exp)]
    return float(np.mean(exp)) if len(exp) else None


def evaluate_overlay(orders: pl.DataFrame, execution: pl.DataFrame, name: str) -> dict:
    nav, trades = a3.simulate(orders, execution, OOF_START, OOF_END)
    benchmark = a3.market_proxy(execution, OOF_START, OOF_END)
    metric = a3.metrics(nav, trades, name)
    _, stats = a3.compare(nav, benchmark)
    cagr = metric.get("cagr")
    mdd = metric.get("max_drawdown")
    turn = metric.get("average_daily_turnover")
    boot = stats.get("block_bootstrap_positive_probability")
    utility = (cagr or 0.0) - 0.5 * abs(mdd or 0.0)
    out = {
        "overlay": name,
        "cagr": cagr,
        "max_drawdown": mdd,
        "utility": utility,
        "average_daily_turnover": turn,
        "block_bootstrap_positive_probability": boot,
        "mean_daily_excess": stats.get("mean_daily_excess"),
        "hac_t_stat": stats.get("hac_t_stat"),
        "mean_gross_exposure": mean_gross_exposure(nav),
        "ending_nav": metric.get("ending_nav"),
        "total_cost": metric.get("total_cost"),
        "turnover_gate_pass": bool((turn or 9) <= TURNOVER_CEILING),
        "bootstrap_gate_pass": bool((boot or 0) >= BOOTSTRAP_GATE),
    }
    out["both_gates_pass"] = bool(out["turnover_gate_pass"] and out["bootstrap_gate_pass"])
    return out, nav


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--oof-scores", type=Path, required=True)
    ap.add_argument("--panel", type=Path, required=True)
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

    scored = pl.read_parquet(args.oof_scores).sort(["date", "code"])
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

    print("building locked C4 orders from TECH2 OOF scores ...", flush=True)
    base_orders, _ = buffered_orders_ext(scored, calendar, **C4)
    print(f"  order rows={base_orders.height}", flush=True)

    print("building market risk state ...", flush=True)
    mkt = build_market_state(execution)
    schedules = exposure_schedules(mkt)
    # persist exposure paths
    pl.concat([s for s in schedules.values()]).write_csv(out / "outputs" / "stage6_exposure_schedules.csv")

    rows = []
    navs = {}
    for name, sched in schedules.items():
        print(f"evaluating overlay {name} ...", flush=True)
        exp_map = {r["date"]: float(r["exposure"]) for r in sched.iter_rows(named=True)}
        orders = scale_orders(base_orders, exp_map) if name != "BASE_FULL" else base_orders
        metrics, nav = evaluate_overlay(orders, execution, name)
        metrics["is_baseline"] = name == "BASE_FULL"
        metrics["mean_schedule_exposure"] = float(sched["exposure"].mean())
        rows.append(metrics)
        navs[name] = nav
        print(
            f"  CAGR={metrics['cagr']:.4f} MDD={metrics['max_drawdown']:.4f} util={metrics['utility']:.4f} "
            f"turn={metrics['average_daily_turnover']:.4f} boot={metrics['block_bootstrap_positive_probability']} "
            f"gross={metrics['mean_gross_exposure']:.3f} both={metrics['both_gates_pass']}",
            flush=True,
        )

    result = pl.DataFrame(rows).sort(
        ["both_gates_pass", "utility", "max_drawdown", "cagr"],
        descending=[True, True, False, True],
    )
    result.write_csv(out / "outputs" / "stage6_risk_overlay_oof_grid.csv")
    for name, nav in navs.items():
        nav.write_csv(out / "outputs" / f"stage6_{name.lower()}_oof_daily_nav.csv")

    baseline = next(r for r in rows if r["is_baseline"])
    dual = [r for r in rows if r["both_gates_pass"] and not r["is_baseline"]]
    # Prefer improved utility vs baseline among dual-gate; else best utility dual-gate
    improved = [r for r in dual if (r["utility"] or -9) > (baseline["utility"] or -9)]
    improved_mdd = [r for r in dual if abs(r["max_drawdown"] or 9) < abs(baseline["max_drawdown"] or 9)]
    dual_sorted = sorted(
        dual,
        key=lambda r: (
            -((r["utility"] or -9)),
            abs(r["max_drawdown"] or 9),
            -(r["cagr"] or -9),
            -(r["block_bootstrap_positive_probability"] or 0),
        ),
    )
    winner = None
    decision = "OOF_NO_NEW_RISK_OVERLAY_DUAL_GATE_WINNER"
    if improved:
        winner = sorted(
            improved,
            key=lambda r: (-(r["utility"] or -9), abs(r["max_drawdown"] or 9)),
        )[0]
        decision = "OOF_NEW_RISK_OVERLAY_UTILITY_WINNER"
    elif dual_sorted:
        # dual-gate but no utility improvement — report best dual, not auto-heldout unless utility↑ or MDD↓ meaningfully
        cand = dual_sorted[0]
        if cand in improved_mdd or (cand["utility"] or -9) >= (baseline["utility"] or -9) - 1e-12:
            winner = cand
            decision = "OOF_NEW_RISK_OVERLAY_DUAL_GATE_WINNER"
        else:
            decision = "OOF_NO_NEW_RISK_OVERLAY_DUAL_GATE_WINNER"

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "STAGE6_RISK_OVERLAY_OOF",
        "window": "2011-2018 OOF only",
        "alpha_frozen": "TECH2 OOF scores + C4 wrapper",
        "e45_touched": False,
        "no_retune_C2_C4_C8_F1": True,
        "baseline": baseline,
        "n_overlays": len(rows),
        "n_both_pass_new": len(dual),
        "n_utility_improved_dual_gate": len(improved),
        "n_mdd_improved_dual_gate": len(improved_mdd),
        "research_decision": decision,
        "recommended": winner,
        "top_dual_gate": dual_sorted[:5],
        "gates_remain_experimental": True,
        "no_promotion": True,
        "note": "Overlays scale target_weight only; E45 not edited. Near-misses must not be held-out.",
    }
    (out / "reports" / "stage6_risk_overlay_oof_summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n"
    )

    lines = [
        "# Stage-6 Risk Overlay OOF (Profit ↑ / MDD ↓)",
        "",
        "Alpha frozen: **TECH2 scores + C4 name selection**. Sleeve exposure overlays only.",
        "Selection: 2011–2018 OOF. **E45 not touched.** Gates EXPERIMENTAL.",
        "",
        f"## Decision: `{decision}`",
        "",
        f"Baseline BASE_FULL: CAGR={baseline['cagr']:.4f}, MDD={baseline['max_drawdown']:.4f}, "
        f"util={baseline['utility']:.4f}, turn={baseline['average_daily_turnover']:.4f}, "
        f"boot={baseline['block_bootstrap_positive_probability']}",
        "",
        "| overlay | CAGR | MDD | utility | turn | boot | gross | both |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for r in result.to_dicts():
        lines.append(
            f"| {r['overlay']} | {100*r['cagr']:.2f}% | {100*r['max_drawdown']:.2f}% | {r['utility']:.4f} | "
            f"{100*r['average_daily_turnover']:.2f}% | {r['block_bootstrap_positive_probability']:.4f} | "
            f"{r['mean_gross_exposure']:.3f} | {r['both_gates_pass']} |"
        )
    if winner:
        lines += [
            "",
            "## Recommended (OOF only — not yet held-out)",
            "",
            f"- `{winner['overlay']}` util={winner['utility']:.4f} "
            f"CAGR={winner['cagr']:.4f} MDD={winner['max_drawdown']:.4f} "
            f"boot={winner['block_bootstrap_positive_probability']}",
            "",
            "Next: lock as R6A1 and run held-out once.",
            "",
        ]
    else:
        lines += [
            "",
            "No dual-gate overlay that improves utility (or qualifies) vs BASE_FULL.",
            "Do not held-out near-misses. Do not retune alpha.",
            "",
        ]
    lines += [
        "",
        "## Research note",
        "",
        "Raising CAGR while cutting MDD on a fully invested sleeve usually needs **risk budget** "
        "(cash/exposure), not another TECH2 tilt. This stage tests that class under OOF dual gates.",
        "",
        "Artifact: `reports/stage6_risk_overlay_oof_summary.json`",
        "",
    ]
    (out / "E50-A3-R1_STAGE6_RISK_OVERLAY_OOF.md").write_text("\n".join(lines))
    print(json.dumps({
        "research_decision": decision,
        "baseline_utility": baseline["utility"],
        "baseline_mdd": baseline["max_drawdown"],
        "n_both_pass_new": len(dual),
        "winner": None if not winner else {
            "overlay": winner["overlay"],
            "utility": winner["utility"],
            "cagr": winner["cagr"],
            "max_drawdown": winner["max_drawdown"],
            "boot": winner["block_bootstrap_positive_probability"],
            "turn": winner["average_daily_turnover"],
        },
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
