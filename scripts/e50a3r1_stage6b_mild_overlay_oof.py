#!/usr/bin/env python3
"""Stage-6B OOF: mild risk overlays (follow-up).

Stage-6A showed aggressive de-risking improves utility/MDD but kills
bootstrap vs market proxy. This round tests gentler exposure scales only.

Alpha frozen TECH2+C4. E45 untouched. OOF 2011–2018 only.
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
from e50a3r1_turnover_diagnosis import buffered_orders_ext
from e50a3r1_stage6_risk_overlay_oof import (
    C4,
    build_market_state,
    evaluate_overlay,
    hysteresis,
    scale_orders,
)

def mild_schedules(mkt: pl.DataFrame) -> dict[str, pl.DataFrame]:
    dates = mkt["date"].to_list()
    n = len(dates)
    vol = mkt["vol20"].to_numpy()
    dd = mkt["dd120"].to_numpy()
    breadth = mkt["breadth60"].to_numpy()
    mom = mkt["ew_mom63"].to_numpy()

    def series(vals, name):
        return pl.DataFrame({"date": dates, "exposure": vals.astype(float), "overlay": [name] * n})

    out = {"BASE_FULL": series(np.ones(n), "BASE_FULL")}
    for g in [0.95, 0.90, 0.85]:
        out[f"STATIC_{int(g*100):03d}"] = series(np.full(n, g), f"STATIC_{int(g*100):03d}")

    # mild RISK_OFF -> 0.85
    exp = np.ones(n)
    for i in range(n):
        if np.isnan(mom[i]) or np.isnan(breadth[i]):
            exp[i] = 1.0
        elif mom[i] >= 0 and breadth[i] >= 0.5:
            exp[i] = 1.0
        else:
            exp[i] = 0.85
    out["REGIME_OFF_085"] = series(exp, "REGIME_OFF_085")

    # mild DD: -12% -> 0.90, -20% -> 0.75 with hysteresis
    raw = (~np.isnan(dd)) & (dd <= -0.12)
    crisis = hysteresis(raw)
    exp = np.ones(n)
    for i in range(n):
        if crisis[i]:
            exp[i] = 0.75 if (not np.isnan(dd[i]) and dd[i] <= -0.20) else 0.90
    out["DD_BRAKE_MILD"] = series(exp, "DD_BRAKE_MILD")

    # vol target 18% and 20% (less aggressive than 15%)
    for target, name in [(0.18, "VOL_TARGET_18"), (0.20, "VOL_TARGET_20")]:
        exp = np.ones(n)
        for i in range(n):
            if not np.isnan(vol[i]) and vol[i] > 1e-8:
                exp[i] = float(np.clip(target / vol[i], 0.50, 1.0))
        out[name] = series(exp, name)

    # mild vote: votes>=3 -> 0.80 only
    votes = (
        ((~np.isnan(dd)) & (dd <= -0.10)).astype(int)
        + ((~np.isnan(vol)) & (vol >= 0.25)).astype(int)
        + ((~np.isnan(breadth)) & (breadth <= 0.40)).astype(int)
    )
    crisis = hysteresis(votes >= 3)
    exp = np.where(crisis, 0.80, 1.0).astype(float)
    out["VOTE_SEVERE_080"] = series(exp, "VOTE_SEVERE_080")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--oof-scores", type=Path, required=True)
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
    base_orders, _ = buffered_orders_ext(scored, calendar, **C4)
    mkt = build_market_state(execution)
    schedules = mild_schedules(mkt)

    rows = []
    for name, sched in schedules.items():
        print(f"evaluating {name} ...", flush=True)
        exp_map = {r["date"]: float(r["exposure"]) for r in sched.iter_rows(named=True)}
        orders = base_orders if name == "BASE_FULL" else scale_orders(base_orders, exp_map)
        metrics, _ = evaluate_overlay(orders, execution, name)
        metrics["is_baseline"] = name == "BASE_FULL"
        metrics["mean_schedule_exposure"] = float(sched["exposure"].mean())
        rows.append(metrics)
        print(
            f"  CAGR={metrics['cagr']:.4f} MDD={metrics['max_drawdown']:.4f} util={metrics['utility']:.4f} "
            f"boot={metrics['block_bootstrap_positive_probability']} both={metrics['both_gates_pass']}",
            flush=True,
        )

    result = pl.DataFrame(rows).sort(
        ["both_gates_pass", "utility", "max_drawdown", "cagr"],
        descending=[True, True, False, True],
    )
    result.write_csv(out / "outputs" / "stage6b_mild_overlay_oof_grid.csv")
    baseline = next(r for r in rows if r["is_baseline"])
    dual = [r for r in rows if r["both_gates_pass"] and not r["is_baseline"]]
    improved = [r for r in dual if (r["utility"] or -9) > (baseline["utility"] or -9)]
    winner = None
    if improved:
        winner = sorted(improved, key=lambda r: (-(r["utility"] or -9), abs(r["max_drawdown"] or 9)))[0]
        decision = "OOF_NEW_MILD_OVERLAY_UTILITY_WINNER"
    elif dual:
        decision = "OOF_MILD_OVERLAY_DUAL_GATE_NO_UTILITY_GAIN"
        winner = sorted(dual, key=lambda r: (-(r["utility"] or -9), abs(r["max_drawdown"] or 9)))[0]
    else:
        decision = "OOF_NO_NEW_MILD_OVERLAY_DUAL_GATE_WINNER"

    # Only recommend held-out if utility improved under dual gates
    recommended = winner if decision == "OOF_NEW_MILD_OVERLAY_UTILITY_WINNER" else None

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "STAGE6B_MILD_OVERLAY_OOF",
        "window": "2011-2018 OOF only",
        "alpha_frozen": "TECH2 OOF scores + C4 wrapper",
        "e45_touched": False,
        "baseline": baseline,
        "n_overlays": len(rows),
        "n_both_pass_new": len(dual),
        "n_utility_improved_dual_gate": len(improved),
        "research_decision": decision,
        "recommended": recommended,
        "top_dual_gate": sorted(dual, key=lambda r: -(r["utility"] or -9))[:5],
        "gates_remain_experimental": True,
        "no_promotion": True,
    }
    (out / "reports" / "stage6b_mild_overlay_oof_summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n"
    )
    lines = [
        "# Stage-6B Mild Risk Overlay OOF",
        "",
        "Follow-up to 6A (aggressive overlays cut MDD/utility-loss but fail bootstrap).",
        "",
        f"## Decision: `{decision}`",
        "",
        f"Baseline util={baseline['utility']:.4f} MDD={baseline['max_drawdown']:.4f} boot={baseline['block_bootstrap_positive_probability']}",
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
    if recommended:
        lines += ["", f"Recommended: `{recommended['overlay']}` — lock R6B1, held-out once.", ""]
    else:
        lines += ["", "No mild overlay clears dual gates with utility gain vs BASE_FULL.", ""]
    lines += ["Artifact: `reports/stage6b_mild_overlay_oof_summary.json`", ""]
    (out / "E50-A3-R1_STAGE6B_MILD_OVERLAY_OOF.md").write_text("\n".join(lines))
    print(json.dumps({
        "research_decision": decision,
        "n_both_pass_new": len(dual),
        "n_utility_improved": len(improved),
        "winner": None if not recommended else {
            "overlay": recommended["overlay"],
            "utility": recommended["utility"],
            "mdd": recommended["max_drawdown"],
            "boot": recommended["block_bootstrap_positive_probability"],
        },
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
