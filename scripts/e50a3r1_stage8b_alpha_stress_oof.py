#!/usr/bin/env python3
"""Stage-8B OOF: alpha-stress controllers (EXPERIMENTAL).

Uses causal detectors motivated by Stage-8A diagnosis:
  - bad months are NON crisis_vote2
  - elevated cross-sectional vol (mkt_vol_60d)
  - elevated trailing value IC (val_ic_lag21)
Thresholds are screened on OOF only (not refit on 2021–22).

Controllers on frozen TECH2+C4:
  - mild/med cash when stress on
  - switch to value/defensive sleeve when stress on

Pass: dual gates + stress-window mean excess >= BASE stress excess
      + utility >= BASE utility - 0.005
E45 untouched. No retune of prior locks.
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
from e50a3r1_stage6_risk_overlay_oof import C4, scale_orders, mean_gross_exposure
from e50a3r1_stage7_crisis_challenger_oof import (
    attach_crisis,
    period_metrics,
    merge_orders_crisis_sleeve,
)
from e50a3r1_stage6_risk_overlay_oof import build_market_state
from e50a3r1_stage8a_failure_signature import build_daily_panel_state, trailing_ic


def build_oof_state(panel, labels, execution) -> pl.DataFrame:
    state = build_daily_panel_state(panel)
    mkt = attach_crisis(build_market_state(execution))
    ic_val = trailing_ic(panel, labels, "value_family_score", 21).rename(
        {"ic": "val_ic_same_day", "ic_lag1": "val_ic_lag1", "ic_lag21": "val_ic_lag21"}
    )
    ic_mom = trailing_ic(panel, labels, "momentum_family_score", 21).rename(
        {"ic": "mom_ic_same_day", "ic_lag1": "mom_ic_lag1", "ic_lag21": "mom_ic_lag21"}
    )
    return (
        state.join(
            mkt.select("date", "vol20", "dd120", "crisis").rename({"crisis": "crisis_vote2"}),
            on="date", how="left",
        )
        .join(ic_val.select("date", "val_ic_lag21"), on="date", how="left")
        .join(ic_mom.select("date", "mom_ic_lag21"), on="date", how="left")
        .filter(pl.col("date").is_between(OOF_START, OOF_END))
    )


def detector_flags(state: pl.DataFrame, kind: str, vol_min: float, val_ic_min: float) -> dict[date, bool]:
    rows = state.to_dicts()
    out = {}
    for r in rows:
        d = r["date"]
        not_crisis = not bool(r.get("crisis_vote2") or False)
        vol_ok = r.get("mkt_vol_60d") is not None and r["mkt_vol_60d"] >= vol_min
        val_ok = r.get("val_ic_lag21") is not None and r["val_ic_lag21"] >= val_ic_min
        if kind == "HIGH_VOL_NONCRISIS":
            out[d] = bool(not_crisis and vol_ok)
        elif kind == "VAL_WORKS_NONCRISIS":
            out[d] = bool(not_crisis and val_ok)
        elif kind == "COMBO_VOL_VAL_NONCRISIS":
            out[d] = bool(not_crisis and vol_ok and val_ok)
        else:
            raise ValueError(kind)
    return out


def build_value_scores(panel: pl.DataFrame) -> pl.DataFrame:
    d = panel.filter(pl.col("date").is_between(OOF_START, OOF_END)).select(
        "date", "code", "industry_category", "trading_money", "unexplained_price_jump",
        "value_family_score", "defensive_family_score", "pct_vol_60d", "pct_book_to_price_proxy",
    )
    d = d.with_columns(
        (
            0.55 * pl.col("value_family_score").fill_null(0.5)
            + 0.25 * pl.col("defensive_family_score").fill_null(0.5)
            + 0.20 * pl.col("pct_book_to_price_proxy").fill_null(0.5)
            - 0.15 * pl.col("pct_vol_60d").fill_null(0.5)
        ).alias("score")
    )
    return d.select(
        "date", "code", "industry_category", "trading_money", "unexplained_price_jump", "score"
    )


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

    print("building OOF state / detectors ...", flush=True)
    state = build_oof_state(panel, labels, execution)
    vol_p50 = float(state["mkt_vol_60d"].drop_nulls().quantile(0.50))
    vol_p70 = float(state["mkt_vol_60d"].drop_nulls().quantile(0.70))
    vol_p80 = float(state["mkt_vol_60d"].drop_nulls().quantile(0.80))
    print(f"  OOF mkt_vol_60d p50={vol_p50:.4f} p70={vol_p70:.4f} p80={vol_p80:.4f}", flush=True)

    print("building baseline TECH2/C4 and VALUE sleeve orders ...", flush=True)
    tech_orders, _ = buffered_orders_ext(scored, calendar, **C4)
    val_scores = build_value_scores(panel)
    val_orders, _ = buffered_orders_ext(val_scores, calendar, **C4)

    # Detector grid (OOF quantiles / fixed IC cuts)
    detector_specs = []
    for kind, vol_min, val_min in [
        ("HIGH_VOL_NONCRISIS", vol_p70, 0.0),
        ("HIGH_VOL_NONCRISIS", vol_p80, 0.0),
        ("VAL_WORKS_NONCRISIS", 0.0, 0.03),
        ("VAL_WORKS_NONCRISIS", 0.0, 0.05),
        ("COMBO_VOL_VAL_NONCRISIS", vol_p70, 0.03),
        ("COMBO_VOL_VAL_NONCRISIS", vol_p70, 0.05),
        ("COMBO_VOL_VAL_NONCRISIS", vol_p80, 0.03),
    ]:
        detector_specs.append((kind, vol_min, val_min))

    rows = []
    # Baseline once per unique stress set — evaluate BASE under each detector's stress window
    for kind, vol_min, val_min in detector_specs:
        flags = detector_flags(state, kind, vol_min, val_min)
        stress_dates = {d for d, on in flags.items() if on}
        tag = f"{kind}_vol{vol_min:.3f}_valic{val_min:.2f}"
        print(f"detector {tag}: stress_days={len(stress_dates)} ({100*len(stress_dates)/max(state.height,1):.1f}%)", flush=True)

        base = evaluate(tech_orders, execution, f"BASE::{tag}", stress_dates)
        base["detector"] = tag
        base["is_baseline"] = True
        base["controller"] = "BASE_FULL"
        base["stress_day_share"] = len(stress_dates) / max(state.height, 1)
        rows.append(base)

        # Controllers
        for scale, cname in [(0.90, "CASH_090"), (0.85, "CASH_085"), (0.70, "CASH_070")]:
            orders = scale_orders(
                tech_orders,
                {d: (scale if flags.get(d, False) else 1.0) for d in tech_orders["signal_date"].unique().to_list()},
            )
            m = evaluate(orders, execution, f"{cname}::{tag}", stress_dates)
            m.update({"detector": tag, "is_baseline": False, "controller": cname, "stress_day_share": base["stress_day_share"]})
            rows.append(m)
            print(
                f"  {cname}: util={m['utility']:.4f} boot={m['block_bootstrap_positive_probability']} "
                f"stress_ex={m['s_crisis_mean_excess']} both={m['both_gates_pass']}",
                flush=True,
            )

        sleeve = merge_orders_crisis_sleeve(tech_orders, val_orders, flags)
        for cname, orders, scale in [
            ("SLEEVE_VALUE", sleeve, None),
            ("SLEEVE_VALUE_CASH085", None, 0.85),
        ]:
            if scale is not None:
                orders = scale_orders(
                    sleeve,
                    {d: (scale if flags.get(d, False) else 1.0) for d in sleeve["signal_date"].unique().to_list()},
                )
            m = evaluate(orders, execution, f"{cname}::{tag}", stress_dates)
            m.update({"detector": tag, "is_baseline": False, "controller": cname, "stress_day_share": base["stress_day_share"]})
            rows.append(m)
            print(
                f"  {cname}: util={m['utility']:.4f} boot={m['block_bootstrap_positive_probability']} "
                f"stress_ex={m['s_crisis_mean_excess']} both={m['both_gates_pass']}",
                flush=True,
            )

    result = pl.DataFrame(rows)
    result.write_csv(out / "outputs" / "stage8b_alpha_stress_oof_grid.csv")

    # Winner: per detector compare controllers to that detector's BASE
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
            util_ok = (r["utility"] or -9) >= (base["utility"] or -9) - 0.005
            if stress_improved and util_ok:
                candidates.append({**r, "base_utility": base["utility"], "base_stress_ex": bex, "base_stress_comp": bcomp})

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
        "OOF_NEW_ALPHA_STRESS_CONTROLLER_DUAL_GATE_WINNER"
        if winner
        else "OOF_NO_NEW_ALPHA_STRESS_CONTROLLER_DUAL_GATE_WINNER"
    )

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "STAGE8B_ALPHA_STRESS_OOF",
        "window": "2011-2018 OOF only",
        "alpha_frozen": "TECH2 OOF scores + C4 wrapper",
        "e45_touched": False,
        "vol_quantiles": {"p50": vol_p50, "p70": vol_p70, "p80": vol_p80},
        "n_rows": len(rows),
        "n_candidates": len(candidates),
        "research_decision": decision,
        "recommended": winner,
        "top_candidates": candidates[:8],
        "gates_remain_experimental": True,
        "no_promotion": True,
    }
    (out / "reports" / "stage8b_alpha_stress_oof_summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n"
    )

    # compact table: best controller per detector + bases
    lines = [
        "# Stage-8B Alpha-Stress Controller OOF",
        "",
        "Detectors from 8A (non-crisis + high XS vol / value IC). Selection: OOF only.",
        "",
        f"## Decision: `{decision}`",
        "",
        f"OOF vol p70={vol_p70:.4f} p80={vol_p80:.4f}",
        "",
        "| challenger | detector | util | boot | stress_ex | stress_ret | both |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    show = sorted(
        rows,
        key=lambda r: (
            -(r["both_gates_pass"]),
            -(r["s_crisis_mean_excess"] or -9),
            -(r["utility"] or -9),
        ),
    )
    for r in show[:40]:
        lines.append(
            f"| {r['controller']} | {r['detector']} | {r['utility']:.4f} | "
            f"{r['block_bootstrap_positive_probability']:.4f} | {r['s_crisis_mean_excess']} | "
            f"{r['s_crisis_strategy_compound']} | {r['both_gates_pass']} |"
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
            "Next: lock S8B1 and held-out once.",
            "",
        ]
    else:
        lines += ["", "No dual-gate controller improves OOF stress-window PnL vs BASE.", ""]
    lines += ["Artifact: `reports/stage8b_alpha_stress_oof_summary.json`", ""]
    (out / "E50-A3-R1_STAGE8B_ALPHA_STRESS_OOF.md").write_text("\n".join(lines))
    print(json.dumps({
        "research_decision": decision,
        "n_candidates": len(candidates),
        "winner": None if not winner else {
            "controller": winner["controller"],
            "detector": winner["detector"],
            "utility": winner["utility"],
            "boot": winner["block_bootstrap_positive_probability"],
            "stress_ex": winner["s_crisis_mean_excess"],
            "stress_ret": winner["s_crisis_strategy_compound"],
        },
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
