#!/usr/bin/env python3
"""Stage-8C OOF: multi-sleeve portfolio challenger (EXPERIMENTAL / E45-class bar).

After S8B1 MIXED_HELDOUT: cash on TECH2 fails transfer (absolute vol cut over-fires).
This stage treats TECH2+C4 as the *bull sleeve* and screens a *separate* stress
return engine (defensive / value / quality) switched by causal relative detectors.

NOT an in-place E45 edit. Does not retune C2/C4/C8/F1/R6B1/S8B1.
Selection: 2011–2018 OOF only.
Pass: dual gates + stress-window PnL strictly better than BASE + util >= BASE-0.005.
Detectors use rolling percentile ranks (travel better than locked absolute p80).
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
from e50a3r1_turnover_diagnosis import (
    BOOTSTRAP_GATE,
    OOF_END,
    OOF_START,
    TURNOVER_CEILING,
    buffered_orders_ext,
)
from e50a3r1_stage6_risk_overlay_oof import (
    C4,
    build_market_state,
    hysteresis,
    mean_gross_exposure,
    scale_orders,
)
from e50a3r1_stage7_crisis_challenger_oof import (
    attach_crisis,
    build_defensive_scores,
    merge_orders_crisis_sleeve,
    period_metrics,
)
from e50a3r1_stage8a_failure_signature import build_daily_panel_state, trailing_ic
from e50a3r1_stage8b_alpha_stress_oof import build_value_scores


MIN_STRESS_SHARE = 0.05
MAX_STRESS_SHARE = 0.40
UTIL_SLACK = 0.005


def rolling_percentile_flags(values: list[float | None], window: int, pctl: float) -> np.ndarray:
    """Causal rolling percentile: flag when x_t >= percentile(x_{t-window:t-1}, pctl)."""
    out = np.zeros(len(values), dtype=bool)
    hist: list[float] = []
    for i, v in enumerate(values):
        if v is None or (isinstance(v, float) and np.isnan(v)):
            out[i] = False
        else:
            if len(hist) >= max(60, window // 4):
                # use up to `window` prior observations
                ref = hist[-window:] if len(hist) >= window else hist
                thr = float(np.quantile(ref, pctl))
                out[i] = bool(v >= thr)
            else:
                out[i] = False
            hist.append(float(v))
    return out


def build_oof_state(panel, labels, execution) -> pl.DataFrame:
    state = build_daily_panel_state(panel)
    mkt = attach_crisis(build_market_state(execution))
    ic_val = trailing_ic(panel, labels, "value_family_score", 21).rename(
        {"ic_lag21": "val_ic_lag21"}
    )
    ic_mom = trailing_ic(panel, labels, "momentum_family_score", 21).rename(
        {"ic_lag21": "mom_ic_lag21"}
    )
    return (
        state.join(
            mkt.select("date", "vol20", "dd120", "crisis").rename({"crisis": "crisis_vote2"}),
            on="date", how="left",
        )
        .join(ic_val.select("date", "val_ic_lag21"), on="date", how="left")
        .join(ic_mom.select("date", "mom_ic_lag21"), on="date", how="left")
        .filter(pl.col("date").is_between(OOF_START, OOF_END))
        .sort("date")
    )


def build_quality_scores(panel: pl.DataFrame) -> pl.DataFrame:
    d = panel.filter(pl.col("date").is_between(OOF_START, OOF_END)).select(
        "date", "code", "industry_category", "trading_money", "unexplained_price_jump",
        "quality_family_score", "defensive_family_score", "pct_vol_60d", "pct_drawdown_63d",
    )
    d = d.with_columns(
        (
            0.50 * pl.col("quality_family_score").fill_null(0.5)
            + 0.30 * pl.col("defensive_family_score").fill_null(0.5)
            - 0.20 * pl.col("pct_vol_60d").fill_null(0.5)
            - 0.10 * pl.col("pct_drawdown_63d").fill_null(0.5)
        ).alias("score")
    )
    return d.select(
        "date", "code", "industry_category", "trading_money", "unexplained_price_jump", "score"
    )


def detector_map(state: pl.DataFrame) -> dict[str, dict[date, bool]]:
    """Relative / causal detectors. Keys are stable names for reporting."""
    rows = state.to_dicts()
    dates = [r["date"] for r in rows]
    vol = [r.get("mkt_vol_60d") for r in rows]
    val_ic = [r.get("val_ic_lag21") for r in rows]
    mom_ic = [r.get("mom_ic_lag21") for r in rows]
    crisis = np.array([bool(r.get("crisis_vote2") or False) for r in rows])
    risk_on = np.array([bool(r.get("risk_on") or False) for r in rows])

    vol_p70 = rolling_percentile_flags(vol, 252, 0.70)
    vol_p80 = rolling_percentile_flags(vol, 252, 0.80)
    # hysteresis to reduce flicker
    vol_p70_h = hysteresis(vol_p70, 2, 5)
    vol_p80_h = hysteresis(vol_p80, 2, 5)

    # value-works: trailing IC above fixed pre-reg cuts (not refit on held-out)
    val_ok_03 = np.array([(v is not None and v >= 0.03) for v in val_ic])
    val_ok_05 = np.array([(v is not None and v >= 0.05) for v in val_ic])
    mom_weak = np.array([(v is not None and v <= 0.0) for v in mom_ic])

    raw = {
        "VOL_ROLLP70_NONCRISIS": (~crisis) & vol_p70_h,
        "VOL_ROLLP80_NONCRISIS": (~crisis) & vol_p80_h,
        "VAL_WORKS_03_NONCRISIS": (~crisis) & val_ok_03,
        "VAL_WORKS_05_NONCRISIS": (~crisis) & val_ok_05,
        "COMBO_VOL70_VAL03": (~crisis) & vol_p70_h & val_ok_03,
        "COMBO_VOL80_VAL05": (~crisis) & vol_p80_h & val_ok_05,
        "ALPHA_STRESS_RISKON_MOMWEAK": risk_on & (~crisis) & mom_weak & vol_p70_h,
        "CRISIS_OR_VOL80": crisis | vol_p80_h,
    }
    out: dict[str, dict[date, bool]] = {}
    for name, arr in raw.items():
        out[name] = {d: bool(arr[i]) for i, d in enumerate(dates)}
    return out


def evaluate(orders, execution, name, stress_dates: set[date]):
    nav, trades = a3.simulate(orders, execution, OOF_START, OOF_END)
    proxy = a3.market_proxy(execution, OOF_START, OOF_END)
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
    return out


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

    scored = pl.read_parquet(args.oof_scores).sort(["date", "code"])
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

    print("building OOF state / relative detectors ...", flush=True)
    state = build_oof_state(panel, labels, execution)
    detectors = detector_map(state)

    print("building bull TECH2/C4 + stress sleeves ...", flush=True)
    tech_orders, _ = buffered_orders_ext(scored, calendar, **C4)
    oof_dates = state["date"]
    def_scores = build_defensive_scores(panel, calendar, oof_dates)
    val_scores = build_value_scores(panel)
    qual_scores = build_quality_scores(panel)
    def_orders, _ = buffered_orders_ext(def_scores, calendar, **C4)
    val_orders, _ = buffered_orders_ext(val_scores, calendar, **C4)
    qual_orders, _ = buffered_orders_ext(qual_scores, calendar, **C4)

    sleeve_book = {
        "SLEEVE_DEF": def_orders,
        "SLEEVE_VAL": val_orders,
        "SLEEVE_QUAL": qual_orders,
    }

    rows = []
    for det_name, flags in detectors.items():
        stress_dates = {d for d, on in flags.items() if on}
        share = len(stress_dates) / max(state.height, 1)
        print(f"detector {det_name}: stress_days={len(stress_dates)} ({100*share:.1f}%)", flush=True)
        if share < MIN_STRESS_SHARE or share > MAX_STRESS_SHARE:
            print(f"  skip (share outside [{MIN_STRESS_SHARE},{MAX_STRESS_SHARE}])", flush=True)
            continue

        base = evaluate(tech_orders, execution, f"BASE::{det_name}", stress_dates)
        base.update({
            "detector": det_name,
            "is_baseline": True,
            "controller": "BASE_FULL",
            "stress_day_share": share,
        })
        rows.append(base)

        for sleeve_name, sleeve_orders in sleeve_book.items():
            switched = merge_orders_crisis_sleeve(tech_orders, sleeve_orders, flags)
            for cname, orders, scale in [
                (sleeve_name, switched, None),
                (f"{sleeve_name}_CASH085", None, 0.85),
            ]:
                if scale is not None:
                    orders = scale_orders(
                        switched,
                        {d: (scale if flags.get(d, False) else 1.0)
                         for d in switched["signal_date"].unique().to_list()},
                    )
                m = evaluate(orders, execution, f"{cname}::{det_name}", stress_dates)
                m.update({
                    "detector": det_name,
                    "is_baseline": False,
                    "controller": cname,
                    "stress_day_share": share,
                })
                rows.append(m)
                print(
                    f"  {cname}: util={m['utility']:.4f} boot={m['block_bootstrap_positive_probability']} "
                    f"stress_ex={m['s_crisis_mean_excess']} both={m['both_gates_pass']}",
                    flush=True,
                )

    result = pl.DataFrame(rows)
    result.write_csv(out / "outputs" / "stage8c_multisleeve_oof_grid.csv")

    candidates = []
    for tag in sorted(set(r["detector"] for r in rows)):
        base = next(r for r in rows if r["detector"] == tag and r["is_baseline"])
        for r in rows:
            if r["detector"] != tag or r["is_baseline"]:
                continue
            if not r["both_gates_pass"]:
                continue
            sex, bex = r["s_crisis_mean_excess"], base["s_crisis_mean_excess"]
            scomp, bcomp = r["s_crisis_strategy_compound"], base["s_crisis_strategy_compound"]
            stress_improved = (
                (sex is not None and bex is not None and sex > bex + 1e-12)
                or (scomp is not None and bcomp is not None and scomp > bcomp + 1e-12)
            )
            util_ok = (r["utility"] or -9) >= (base["utility"] or -9) - UTIL_SLACK
            if stress_improved and util_ok:
                candidates.append({
                    **r,
                    "base_utility": base["utility"],
                    "base_stress_ex": bex,
                    "base_stress_comp": bcomp,
                })

    candidates = sorted(
        candidates,
        key=lambda r: (
            -(r["s_crisis_strategy_compound"] or -9),
            -(r["utility"] or -9),
            abs(r["max_drawdown"] or 9),
        ),
    )
    winner = candidates[0] if candidates else None
    decision = (
        "OOF_NEW_MULTISLEEVE_DUAL_GATE_WINNER"
        if winner
        else "OOF_NO_NEW_MULTISLEEVE_DUAL_GATE_WINNER"
    )

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "STAGE8C_MULTISLEEVE_OOF",
        "window": "2011-2018 OOF only",
        "bull_sleeve": "TECH2 OOF scores + C4 wrapper",
        "stress_sleeves": list(sleeve_book.keys()),
        "e45_touched": False,
        "e45_inplace_edit": False,
        "absolute_vol_cut_forbidden": True,
        "min_stress_share": MIN_STRESS_SHARE,
        "max_stress_share": MAX_STRESS_SHARE,
        "n_rows": len(rows),
        "n_candidates": len(candidates),
        "research_decision": decision,
        "recommended": winner,
        "top_candidates": candidates[:10],
        "gates_remain_experimental": True,
        "no_promotion": True,
        "no_retune_prior_locks": True,
    }
    (out / "reports" / "stage8c_multisleeve_oof_summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n"
    )

    lines = [
        "# Stage-8C Multi-Sleeve Portfolio Challenger OOF",
        "",
        "E45-class process bar. TECH2+C4 = bull sleeve; stress sleeves = DEF/VAL/QUAL.",
        "Detectors = rolling vol percentile / value-IC / combo (no absolute OOF p80 lock).",
        "",
        f"## Decision: `{decision}`",
        "",
        f"Stress share band: [{MIN_STRESS_SHARE:.0%}, {MAX_STRESS_SHARE:.0%}]",
        "",
        "| controller | detector | util | boot | stress_ex | stress_ret | share | both |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    show = sorted(
        rows,
        key=lambda r: (
            -(r["both_gates_pass"]),
            -(r["s_crisis_mean_excess"] or -9),
            -(r["utility"] or -9),
        ),
    )
    for r in show[:50]:
        lines.append(
            f"| {r['controller']} | {r['detector']} | {r['utility']:.4f} | "
            f"{r['block_bootstrap_positive_probability']:.4f} | {r['s_crisis_mean_excess']} | "
            f"{r['s_crisis_strategy_compound']} | {100*r['stress_day_share']:.1f}% | "
            f"{r['both_gates_pass']} |"
        )
    if winner:
        lines += [
            "",
            "## Recommended (OOF — not yet held-out)",
            "",
            f"- controller `{winner['controller']}` detector `{winner['detector']}`",
            f"- util={winner['utility']:.4f} boot={winner['block_bootstrap_positive_probability']} "
            f"stress_ex={winner['s_crisis_mean_excess']} stress_ret={winner['s_crisis_strategy_compound']}",
            "",
            "Next: lock S8C1 and held-out once.",
            "",
        ]
    else:
        lines += [
            "",
            "No dual-gate multi-sleeve controller improves OOF stress-window PnL vs BASE.",
            "Escalate: document bull-sleeve-only + open higher-bar architecture outside this grid.",
            "",
        ]
    lines += ["Artifact: `reports/stage8c_multisleeve_oof_summary.json`", ""]
    (out / "E50-A3-R1_STAGE8C_MULTISLEEVE_OOF.md").write_text("\n".join(lines))
    print(json.dumps({
        "research_decision": decision,
        "n_candidates": len(candidates),
        "n_rows": len(rows),
        "winner": None if not winner else {
            "controller": winner["controller"],
            "detector": winner["detector"],
            "utility": winner["utility"],
            "boot": winner["block_bootstrap_positive_probability"],
            "stress_ex": winner["s_crisis_mean_excess"],
            "stress_ret": winner["s_crisis_strategy_compound"],
            "share": winner["stress_day_share"],
        },
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
