#!/usr/bin/env python3
"""Held-out for Stage-6B R6B1 = STATIC_085 exposure overlay (EXPERIMENTAL).

Locked at OOF: constant gross exposure 0.85 on C4/TECH2 name selection.
Does NOT retune after held-out. E45 untouched. Alpha features/rules frozen.
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
    TURNOVER_CEILING,
    buffered_orders_ext,
)
from e50a3r1_stage6_risk_overlay_oof import C4, scale_orders, mean_gross_exposure

R6B1 = {
    "challenger_id": "R6B1",
    "overlay": "STATIC_085",
    "exposure": 0.85,
    **C4,
    "feature_set": "TECH2",
    "mode": "BREADTH_REGIME",
    "ridge_lambda": 1.0,
}


def classify(val: dict, sealed: dict) -> str:
    val_ok = bool(val["turnover_gate_pass"] and val["bootstrap_gate_pass"])
    sealed_ok = bool(sealed["turnover_gate_pass"] and sealed["bootstrap_gate_pass"])
    t1_ok = bool(val["exact_t1_ok"] and sealed["exact_t1_ok"])
    if not t1_ok:
        return "INCONCLUSIVE"
    if val_ok and sealed_ok:
        return "PASS_HELDOUT"
    if (not val_ok) and (not sealed_ok):
        return "FAIL_HELDOUT"
    if val_ok != sealed_ok:
        return "MIXED_HELDOUT"
    return "INCONCLUSIVE"


def evaluate_period(joined, execution, calendar, exposure: float, name, start, end, fit_cutoff):
    model = r1.fit_model(joined, "TECH2", "BREADTH_REGIME", 1.0, fit_cutoff)
    scored = r1.score_period(joined, model, start, end)
    orders, _ = buffered_orders_ext(scored, calendar, **C4)
    # constant exposure on all signal dates in period
    exp_map = {d: exposure for d in scored["date"].unique().to_list()}
    # also map any signal dates from orders
    for d in orders["signal_date"].unique().to_list():
        exp_map[d] = exposure
    orders = scale_orders(orders, exp_map)
    nav, trades = a3.simulate(orders, execution, start, end)
    benchmark = a3.market_proxy(execution, start, end)
    metric = a3.metrics(nav, trades, name)
    _, stats = a3.compare(nav, benchmark)
    t = trades.with_columns(pl.col("signal_date").cast(pl.Date), pl.col("execution_date").cast(pl.Date))
    same_bar = int(t.filter(pl.col("execution_date") <= pl.col("signal_date")).height)
    cagr, mdd, turn = metric.get("cagr"), metric.get("max_drawdown"), metric.get("average_daily_turnover")
    boot = stats.get("block_bootstrap_positive_probability")
    pvals = benchmark["nav"].to_numpy()
    years = len(pvals) / 252.0
    proxy_cagr = float(pvals[-1] ** (1.0 / years) - 1.0) if years > 0 else None
    out = {
        "portfolio": name,
        "overlay": "STATIC_085",
        "exposure": exposure,
        "fit_cutoff": str(fit_cutoff),
        "cagr": cagr,
        "max_drawdown": mdd,
        "utility": (cagr or 0.0) - 0.5 * abs(mdd or 0.0),
        "average_daily_turnover": turn,
        "block_bootstrap_positive_probability": boot,
        "mean_daily_excess": stats.get("mean_daily_excess"),
        "hac_t_stat": stats.get("hac_t_stat"),
        "mean_gross_exposure": mean_gross_exposure(nav),
        "market_proxy_cagr": proxy_cagr,
        "beats_market_proxy": bool((cagr or -9) > (proxy_cagr if proxy_cagr is not None else 9)),
        "same_bar_fills": same_bar,
        "exact_t1_ok": same_bar == 0,
        "turnover_gate_pass": bool((turn or 9) <= TURNOVER_CEILING),
        "bootstrap_gate_pass": bool((boot or 0) >= BOOTSTRAP_GATE),
    }
    out["both_experimental_gates_pass"] = bool(out["turnover_gate_pass"] and out["bootstrap_gate_pass"])
    return out, nav, trades, benchmark


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", type=Path, required=True)
    ap.add_argument("--prices", type=Path, required=True)
    ap.add_argument("--actions", type=Path, required=True)
    ap.add_argument("--a2-qc", type=Path, required=True)
    ap.add_argument("--stage6b-summary", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    out = args.out
    (out / "outputs").mkdir(parents=True, exist_ok=True)
    (out / "reports").mkdir(parents=True, exist_ok=True)

    summary = json.loads(args.stage6b_summary.read_text())
    if summary["research_decision"] != "OOF_NEW_MILD_OVERLAY_UTILITY_WINNER":
        raise RuntimeError("Stage-6B did not produce a mild overlay utility winner")
    rec = summary["recommended"]
    if rec["overlay"] != "STATIC_085":
        raise RuntimeError(f"R6B1 lock drift: {rec['overlay']}")

    if json.loads(args.a2_qc.read_text())["status"] != "PASS":
        raise RuntimeError("E50-A2 QC is not PASS")

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
    exact_labels = a3.build_exact_open_labels(panel, execution, calendar)
    joined = a3.target_rank(
        r1.add_regime(panel).join(exact_labels.select("date", "code", a3.LABEL), on=["date", "code"], validate="1:1")
    )

    validation_start, validation_end = date(2019, 1, 1), date(2022, 12, 31)
    sealed_start, sealed_end = date(2023, 1, 1), max(calendar)
    val_cutoff = a3.previous_session(calendar, validation_start, 22)
    sealed_cutoff = a3.previous_session(calendar, sealed_start, 22)

    print("R6B1 validation ...", flush=True)
    val, val_nav, val_trades, val_proxy = evaluate_period(
        joined, execution, calendar, 0.85, "R6B1_VALIDATION_2019_2022",
        validation_start, validation_end, val_cutoff,
    )
    print("R6B1 sealed ...", flush=True)
    sealed, sealed_nav, sealed_trades, sealed_proxy = evaluate_period(
        joined, execution, calendar, 0.85, "R6B1_SEALED_2023_LATEST",
        sealed_start, sealed_end, sealed_cutoff,
    )
    print("C4 full-invest reference validation/sealed ...", flush=True)
    c4_val, _, _, _ = evaluate_period(
        joined, execution, calendar, 1.0, "C4_FULL_VALIDATION_2019_2022",
        validation_start, validation_end, val_cutoff,
    )
    c4_sealed, _, _, _ = evaluate_period(
        joined, execution, calendar, 1.0, "C4_FULL_SEALED_2023_LATEST",
        sealed_start, sealed_end, sealed_cutoff,
    )

    label = classify(val, sealed)
    for tag, nav, trades, proxy in [
        ("r6b1_validation_2019_2022", val_nav, val_trades, val_proxy),
        ("r6b1_sealed_2023_latest", sealed_nav, sealed_trades, sealed_proxy),
    ]:
        nav.write_csv(out / "outputs" / f"{tag}_daily_nav.csv")
        trades.write_csv(out / "outputs" / f"{tag}_trades.csv")
        proxy.write_csv(out / "outputs" / f"{tag}_market_proxy_nav.csv")

    decision = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "STAGE6B_R6B1_HELDOUT",
        "challenger_id": "R6B1",
        "locked_config": R6B1,
        "oof_source_decision": summary["research_decision"],
        "oof_utility": rec["utility"],
        "oof_mdd": rec["max_drawdown"],
        "oof_boot": rec["block_bootstrap_positive_probability"],
        "oof_cagr": rec["cagr"],
        "oof_turn": rec["average_daily_turnover"],
        "no_retune_on_heldout": True,
        "e45_touched": False,
        "gates_remain_experimental": True,
        "research_decision": label,
        "validation_2019_2022": val,
        "sealed_2023_latest": sealed,
        "c4_full_reference_validation": c4_val,
        "c4_full_reference_sealed": c4_sealed,
    }
    (out / "reports" / "stage6b_r6b1_heldout_decision.json").write_text(
        json.dumps(decision, indent=2, default=str) + "\n"
    )
    lines = [
        "# E50-A3-R1-R6B1 STATIC_085 — Held-Out Evaluation",
        "",
        "Locked OOF mild overlay: constant gross **0.85** on C4/TECH2. **No retune. E45 untouched.**",
        "",
        f"## Research decision",
        "",
        f"**`{label}`**",
        "",
        f"OOF: util={rec.get('utility'):.4f}, MDD={rec.get('mdd', rec.get('max_drawdown')):.4f}, "
        f"boot={rec.get('boot', rec.get('block_bootstrap_positive_probability'))}",
        "",
        "| Metric | R6B1 Val | R6B1 Sealed | C4 Full Val | C4 Full Sealed |",
        "|---|---:|---:|---:|---:|",
        f"| CAGR | {100*val['cagr']:.2f}% | {100*sealed['cagr']:.2f}% | {100*c4_val['cagr']:.2f}% | {100*c4_sealed['cagr']:.2f}% |",
        f"| MDD | {100*val['max_drawdown']:.2f}% | {100*sealed['max_drawdown']:.2f}% | {100*c4_val['max_drawdown']:.2f}% | {100*c4_sealed['max_drawdown']:.2f}% |",
        f"| Utility | {val['utility']:.4f} | {sealed['utility']:.4f} | {c4_val['utility']:.4f} | {c4_sealed['utility']:.4f} |",
        f"| Turnover | {100*val['average_daily_turnover']:.2f}% | {100*sealed['average_daily_turnover']:.2f}% | {100*c4_val['average_daily_turnover']:.2f}% | {100*c4_sealed['average_daily_turnover']:.2f}% |",
        f"| Bootstrap | {val['block_bootstrap_positive_probability']:.4f} | {sealed['block_bootstrap_positive_probability']:.4f} | {c4_val['block_bootstrap_positive_probability']:.4f} | {c4_sealed['block_bootstrap_positive_probability']:.4f} |",
        f"| Gross exp | {val['mean_gross_exposure']:.3f} | {sealed['mean_gross_exposure']:.3f} | {c4_val['mean_gross_exposure']:.3f} | {c4_sealed['mean_gross_exposure']:.3f} |",
        f"| Turn gate | {val['turnover_gate_pass']} | {sealed['turnover_gate_pass']} | {c4_val['turnover_gate_pass']} | {c4_sealed['turnover_gate_pass']} |",
        f"| Boot gate | {val['bootstrap_gate_pass']} | {sealed['bootstrap_gate_pass']} | {c4_val['bootstrap_gate_pass']} | {c4_sealed['bootstrap_gate_pass']} |",
        f"| Exact T+1 | {val['exact_t1_ok']} | {sealed['exact_t1_ok']} | {c4_val['exact_t1_ok']} | {c4_sealed['exact_t1_ok']} |",
        "",
        "Artifact: `reports/stage6b_r6b1_heldout_decision.json`",
        "",
    ]
    (out / "E50-A3-R1_STAGE6B_R6B1_HELDOUT.md").write_text("\n".join(lines))
    print(json.dumps({
        "research_decision": label,
        "val_boot": val["block_bootstrap_positive_probability"],
        "val_mdd": val["max_drawdown"],
        "val_cagr": val["cagr"],
        "val_util": val["utility"],
        "sealed_boot": sealed["block_bootstrap_positive_probability"],
        "sealed_mdd": sealed["max_drawdown"],
        "c4_val_boot": c4_val["block_bootstrap_positive_probability"],
        "c4_val_mdd": c4_val["max_drawdown"],
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
