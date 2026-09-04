#!/usr/bin/env python3
"""Stage-7B OOF: stricter crisis windows + mild crisis cash (EXPERIMENTAL).

7A: vote≥2 crisis already had positive baseline crisis excess; all overlays
failed dual gates. 7B uses a stricter OOF crisis definition (deep DD / votes≥3)
and only mild cash scales so bootstrap has a chance.

E45 untouched. Alpha TECH2+C4 frozen. OOF 2011–2018 only.
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
from e50a3r1_turnover_diagnosis import buffered_orders_ext
from e50a3r1_stage6_risk_overlay_oof import C4, build_market_state, hysteresis, scale_orders
from e50a3r1_stage7_crisis_challenger_oof import evaluate_nav, build_defensive_scores, merge_orders_crisis_sleeve

STRICT_CRISIS = {
    "name": "STRICT_DD15_OR_VOTE3_HYS25",
    "dd_cut": -0.15,
    "vol_cut": 0.25,
    "breadth_cut": 0.40,
    "vote_threshold": 3,
    "on_need": 2,
    "off_need": 5,
}


def attach_strict_crisis(mkt: pl.DataFrame) -> pl.DataFrame:
    dd = mkt["dd120"].to_numpy()
    vol = mkt["vol20"].to_numpy()
    br = mkt["breadth60"].to_numpy()
    votes = (
        ((~np.isnan(dd)) & (dd <= STRICT_CRISIS["dd_cut"])).astype(int)
        + ((~np.isnan(vol)) & (vol >= STRICT_CRISIS["vol_cut"])).astype(int)
        + ((~np.isnan(br)) & (br <= STRICT_CRISIS["breadth_cut"])).astype(int)
    )
    # Strict: deep DD alone OR votes>=3
    raw = ((~np.isnan(dd)) & (dd <= STRICT_CRISIS["dd_cut"])) | (votes >= STRICT_CRISIS["vote_threshold"])
    crisis = hysteresis(raw, STRICT_CRISIS["on_need"], STRICT_CRISIS["off_need"])
    return mkt.with_columns(pl.Series("crisis_votes", votes), pl.Series("crisis", crisis))


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
    panel = pl.read_parquet(args.panel).sort(["date", "code"])
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

    mkt = attach_strict_crisis(build_market_state(execution))
    from e50a3r1_turnover_diagnosis import OOF_START, OOF_END
    mkt_oof = mkt.filter(pl.col("date").is_between(OOF_START, OOF_END))
    crisis_by_date = {r["date"]: bool(r["crisis"]) for r in mkt.iter_rows(named=True)}
    crisis_dates = {d for d, c in crisis_by_date.items() if c and OOF_START <= d <= OOF_END}
    mkt_oof.select("date", "dd120", "vol20", "breadth60", "crisis_votes", "crisis").write_csv(
        out / "outputs" / "stage7b_oof_strict_crisis_flags.csv"
    )
    print(f"strict OOF crisis days={len(crisis_dates)}/{mkt_oof.height}", flush=True)

    tech_orders, _ = buffered_orders_ext(scored, calendar, **C4)
    def_scores = build_defensive_scores(panel, calendar, scored["date"])
    def_orders, _ = buffered_orders_ext(def_scores, calendar, **C4)
    sleeve = merge_orders_crisis_sleeve(tech_orders, def_orders, crisis_by_date)

    def cmap(orders, scale):
        return {d: (scale if crisis_by_date.get(d, False) else 1.0) for d in orders["signal_date"].unique().to_list()}

    challengers = {
        "BASE_FULL": tech_orders,
        "STRICT_CASH_090": scale_orders(tech_orders, cmap(tech_orders, 0.90)),
        "STRICT_CASH_085": scale_orders(tech_orders, cmap(tech_orders, 0.85)),
        "STRICT_CASH_080": scale_orders(tech_orders, cmap(tech_orders, 0.80)),
        "STRICT_CASH_070": scale_orders(tech_orders, cmap(tech_orders, 0.70)),
        "STRICT_SLEEVE_DEF": sleeve,
        "STRICT_SLEEVE_DEF_CASH085": scale_orders(sleeve, cmap(sleeve, 0.85)),
    }

    rows = []
    for name, orders in challengers.items():
        print(f"evaluating {name} ...", flush=True)
        metrics, nav = evaluate_nav(orders, execution, name, crisis_dates)
        metrics["is_baseline"] = name == "BASE_FULL"
        rows.append(metrics)
        print(
            f"  CAGR={metrics['cagr']:.4f} MDD={metrics['max_drawdown']:.4f} util={metrics['utility']:.4f} "
            f"boot={metrics['block_bootstrap_positive_probability']} "
            f"crisis_ex={metrics['c_crisis_mean_excess']} both={metrics['both_gates_pass']}",
            flush=True,
        )

    result = pl.DataFrame(rows).sort(
        ["both_gates_pass", "crisis_excess_nonneg", "utility", "c_crisis_mean_excess"],
        descending=[True, True, True, True],
    )
    result.write_csv(out / "outputs" / "stage7b_strict_crisis_oof_grid.csv")
    baseline = next(r for r in rows if r["is_baseline"])
    dual = [r for r in rows if r["both_gates_pass"] and not r["is_baseline"]]
    candidates = []
    for r in dual:
        cex, bex = r["c_crisis_mean_excess"], baseline["c_crisis_mean_excess"]
        crisis_ok = cex is not None and ((cex >= 0.0) or (bex is not None and cex > bex + 1e-8))
        # Prefer improved crisis compound OR improved utility
        compound_ok = (r["c_crisis_strategy_compound"] or -9) > (baseline["c_crisis_strategy_compound"] or -9)
        util_ok = (r["utility"] or -9) >= (baseline["utility"] or -9) - 0.005
        if crisis_ok and util_ok and (compound_ok or (r["utility"] or -9) > (baseline["utility"] or -9)):
            candidates.append(r)

    candidates = sorted(
        candidates,
        key=lambda r: (
            -(r["c_crisis_strategy_compound"] or -9),
            -(r["utility"] or -9),
            abs(r["max_drawdown"] or 9),
        ),
    )
    winner = candidates[0] if candidates else None
    decision = (
        "OOF_NEW_STRICT_CRISIS_CHALLENGER_DUAL_GATE_WINNER"
        if winner
        else "OOF_NO_NEW_STRICT_CRISIS_CHALLENGER_DUAL_GATE_WINNER"
    )
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "STAGE7B_STRICT_CRISIS_OOF",
        "crisis_definition": STRICT_CRISIS,
        "oof_crisis_day_share": baseline["c_crisis_day_share"],
        "baseline": baseline,
        "n_challengers": len(rows),
        "n_both_pass_new": len(dual),
        "n_candidates": len(candidates),
        "research_decision": decision,
        "recommended": winner,
        "e45_touched": False,
        "gates_remain_experimental": True,
        "no_promotion": True,
    }
    (out / "reports" / "stage7b_strict_crisis_oof_summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n"
    )
    lines = [
        "# Stage-7B Strict Crisis Challenger OOF",
        "",
        f"Crisis def: `{STRICT_CRISIS['name']}`. OOF crisis share={100*(baseline['c_crisis_day_share'] or 0):.1f}%.",
        "",
        f"## Decision: `{decision}`",
        "",
        "| challenger | CAGR | MDD | util | boot | crisis_ex | crisis_ret | both |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for r in result.to_dicts():
        lines.append(
            f"| {r['challenger']} | {100*r['cagr']:.2f}% | {100*r['max_drawdown']:.2f}% | {r['utility']:.4f} | "
            f"{r['block_bootstrap_positive_probability']:.4f} | {r['c_crisis_mean_excess']:.6f} | "
            f"{100*(r['c_crisis_strategy_compound'] or 0):.2f}% | {r['both_gates_pass']} |"
        )
    if winner:
        lines += ["", f"Recommended: `{winner['challenger']}` — lock C7B1, held-out once.", ""]
    else:
        lines += ["", "No strict-crisis dual-gate winner with crisis improvement.", ""]
    lines += ["Artifact: `reports/stage7b_strict_crisis_oof_summary.json`", ""]
    (out / "E50-A3-R1_STAGE7B_STRICT_CRISIS_OOF.md").write_text("\n".join(lines))
    print(json.dumps({
        "research_decision": decision,
        "oof_crisis_day_share": baseline["c_crisis_day_share"],
        "baseline_crisis_excess": baseline["c_crisis_mean_excess"],
        "baseline_crisis_compound": baseline["c_crisis_strategy_compound"],
        "n_candidates": len(candidates),
        "winner": None if not winner else {
            "challenger": winner["challenger"],
            "boot": winner["block_bootstrap_positive_probability"],
            "utility": winner["utility"],
            "crisis_compound": winner["c_crisis_strategy_compound"],
        },
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
