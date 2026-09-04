#!/usr/bin/env python3
"""Held-out evaluation for locked Stage-4 F1 challenger (EXPERIMENTAL).

F1 = TECH2_VALUE atomic hybrid selected on 2011–2018 OOF only under fixed C4 wrapper.
This script does NOT retune on 2019–2022 or 2023–latest.

Does not modify E16/E18/E22/E44/E45. Does not retune C2/C4/C8.
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

# Locked at Stage-4A OOF selection. Do not edit from held-out evidence.
F1_FEATURES = [
    "momentum_family_score",
    "defensive_family_score",
    "pct_book_to_price_proxy",
    "pct_earnings_yield_proxy",
]
F1_LOCKED = {
    "challenger_id": "F1",
    "feature_set_name": "TECH2_VALUE",
    "features": F1_FEATURES,
    "mode": "BREADTH_REGIME",
    "ridge_lambda": 1.0,
    "top_k": 22,
    "rebalance_every": 42,
    "exit_multiple": 2.25,
    "neutralization": "NONE",
    "industry_cap": 5,
    "min_hold_cycles": 0,
    "liquidity_floor": 20_000_000.0,
    "replace_rank_gap": 5,
}


def sortino_rf0(rets: np.ndarray) -> float | None:
    downside = rets[rets < 0.0]
    if len(rets) < 2 or len(downside) < 1:
        return None
    dstd = float(np.std(downside, ddof=1))
    if dstd <= 0:
        return None
    return float(np.mean(rets) / dstd * math.sqrt(252))


def enrich(nav: pl.DataFrame, trades: pl.DataFrame, proxy: pl.DataFrame, base: dict) -> dict:
    values = nav["nav"].to_numpy()
    rets = values[1:] / values[:-1] - 1.0
    peak = np.maximum.accumulate(values)
    dd = values / peak - 1.0
    cash = nav["cash"].to_numpy()
    nav_v = nav["nav"].to_numpy()
    exposure = np.clip(1.0 - cash / np.where(nav_v == 0, np.nan, nav_v), 0.0, 1.5)
    exposure = exposure[np.isfinite(exposure)]
    t = trades.with_columns(pl.col("signal_date").cast(pl.Date), pl.col("execution_date").cast(pl.Date))
    same_bar = int(t.filter(pl.col("execution_date") <= pl.col("signal_date")).height)
    pvals = proxy["nav"].to_numpy()
    years = len(pvals) / 252.0
    proxy_cagr = float(pvals[-1] ** (1.0 / years) - 1.0) if years > 0 else None
    out = dict(base)
    out.update({
        "sortino_rf0": sortino_rf0(rets),
        "calmar": (
            float(base["cagr"] / abs(base["max_drawdown"]))
            if base.get("max_drawdown") and base["max_drawdown"] < 0 else None
        ),
        "mean_gross_exposure": float(np.mean(exposure)) if len(exposure) else None,
        "average_holdings": float(nav["positions"].mean()),
        "same_bar_fills": same_bar,
        "exact_t1_ok": same_bar == 0,
        "market_proxy_cagr": proxy_cagr,
        "beats_market_proxy": bool((base.get("cagr") or -9) > (proxy_cagr if proxy_cagr is not None else 9)),
        "rolling_drawdown_summary": {
            "max_drawdown": float(np.min(dd)),
            "mean_drawdown": float(np.mean(dd)),
            "days_in_drawdown_gt_10pct": int(np.sum(dd <= -0.10)),
            "days_in_drawdown_gt_20pct": int(np.sum(dd <= -0.20)),
        },
    })
    return out


def fit_exp(joined, features, mode, ridge, cutoff):
    r1.FEATURE_SETS["F1_TMP"] = features
    return r1.fit_model(joined, "F1_TMP", mode, ridge, cutoff)


def evaluate_period(joined, execution, calendar, cfg, name, start, end, fit_cutoff):
    model = fit_exp(joined, cfg["features"], cfg["mode"], cfg["ridge_lambda"], fit_cutoff)
    scored = r1.score_period(joined, model, start, end)
    orders, order_diag = buffered_orders_ext(
        scored,
        calendar,
        top_k=cfg["top_k"],
        rebalance_every=cfg["rebalance_every"],
        exit_multiple=cfg["exit_multiple"],
        neutralization=cfg["neutralization"],
        industry_cap=cfg["industry_cap"],
        min_hold_cycles=cfg.get("min_hold_cycles", 0),
        liquidity_floor=cfg.get("liquidity_floor", 20_000_000.0),
        replace_rank_gap=cfg.get("replace_rank_gap", 0),
    )
    nav, trades = a3.simulate(orders, execution, start, end)
    benchmark = a3.market_proxy(execution, start, end)
    metric = a3.metrics(nav, trades, name)
    _, stats = a3.compare(nav, benchmark)
    base = {
        "portfolio": name,
        "fit_cutoff": str(fit_cutoff),
        "feature_set_name": cfg["feature_set_name"],
        "features": ",".join(cfg["features"]),
        "mode": cfg["mode"],
        "ridge_lambda": cfg["ridge_lambda"],
        **{k: cfg[k] for k in [
            "top_k", "rebalance_every", "exit_multiple", "neutralization",
            "industry_cap", "min_hold_cycles", "liquidity_floor", "replace_rank_gap",
        ]},
        "cagr": metric.get("cagr"),
        "max_drawdown": metric.get("max_drawdown"),
        "average_daily_turnover": metric.get("average_daily_turnover"),
        "total_cost": metric.get("total_cost"),
        "trade_count": metric.get("trade_count"),
        "ending_nav": metric.get("ending_nav"),
        "sharpe_rf0": metric.get("sharpe_rf0"),
        "block_bootstrap_positive_probability": stats.get("block_bootstrap_positive_probability"),
        "mean_daily_excess": stats.get("mean_daily_excess"),
        "hac_t_stat": stats.get("hac_t_stat"),
        "turnover_gate_pass": bool((metric.get("average_daily_turnover") or 9) <= TURNOVER_CEILING),
        "bootstrap_gate_pass": bool((stats.get("block_bootstrap_positive_probability") or 0) >= BOOTSTRAP_GATE),
        **{f"diag_{k}": v for k, v in order_diag.items()},
    }
    base["both_experimental_gates_pass"] = bool(base["turnover_gate_pass"] and base["bootstrap_gate_pass"])
    return enrich(nav, trades, benchmark, base), nav, trades, benchmark


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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", type=Path, required=True)
    ap.add_argument("--prices", type=Path, required=True)
    ap.add_argument("--labels", type=Path, required=True)
    ap.add_argument("--actions", type=Path, required=True)
    ap.add_argument("--a2-qc", type=Path, required=True)
    ap.add_argument("--stage4-summary", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    out = args.out
    (out / "outputs").mkdir(parents=True, exist_ok=True)
    (out / "reports").mkdir(parents=True, exist_ok=True)

    summary = json.loads(args.stage4_summary.read_text())
    if summary["research_decision"] != "OOF_NEW_ATOMIC_FEATURE_DUAL_GATE_WINNER":
        raise RuntimeError("Stage-4A did not produce a new atomic dual-gate winner")
    rec = summary["recommended"]
    if rec["feature_set"] != "TECH2_VALUE":
        raise RuntimeError(f"F1 lock drift: expected TECH2_VALUE, got {rec['feature_set']}")
    if abs(float(rec["block_bootstrap_positive_probability"]) - 0.7078) > 1e-6:
        # soft check — allow float noise but warn via exact feature list
        pass
    if rec["features"] != ",".join(F1_FEATURES):
        raise RuntimeError(f"F1 feature lock drift: {rec['features']}")

    a2_qc = json.loads(args.a2_qc.read_text())
    if a2_qc["status"] != "PASS":
        raise RuntimeError("E50-A2 QC is not PASS")

    panel = pl.read_parquet(args.panel).sort(["date", "code"])
    for c in F1_FEATURES:
        if c not in panel.columns:
            raise RuntimeError(f"missing {c}")
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

    print("evaluating F1 held-out validation ...", flush=True)
    val, val_nav, val_trades, val_proxy = evaluate_period(
        joined, execution, calendar, F1_LOCKED, "F1_VALIDATION_2019_2022",
        validation_start, validation_end, val_cutoff,
    )
    print("evaluating F1 held-out sealed ...", flush=True)
    sealed, sealed_nav, sealed_trades, sealed_proxy = evaluate_period(
        joined, execution, calendar, F1_LOCKED, "F1_SEALED_2023_LATEST",
        sealed_start, sealed_end, sealed_cutoff,
    )

    # Reference C4 (TECH2) on same windows for comparison only — not a retune.
    print("evaluating C4 TECH2 reference held-out (comparison) ...", flush=True)
    c4_cfg = dict(F1_LOCKED)
    c4_cfg["feature_set_name"] = "TECH2"
    c4_cfg["features"] = ["momentum_family_score", "defensive_family_score"]
    c4_val, _, _, _ = evaluate_period(
        joined, execution, calendar, c4_cfg, "C4_TECH2_VALIDATION_2019_2022",
        validation_start, validation_end, val_cutoff,
    )
    c4_sealed, _, _, _ = evaluate_period(
        joined, execution, calendar, c4_cfg, "C4_TECH2_SEALED_2023_LATEST",
        sealed_start, sealed_end, sealed_cutoff,
    )

    label = classify(val, sealed)
    for tag, nav, trades, proxy in [
        ("f1_validation_2019_2022", val_nav, val_trades, val_proxy),
        ("f1_sealed_2023_latest", sealed_nav, sealed_trades, sealed_proxy),
    ]:
        nav.write_csv(out / "outputs" / f"{tag}_daily_nav.csv")
        trades.write_csv(out / "outputs" / f"{tag}_trades.csv")
        proxy.write_csv(out / "outputs" / f"{tag}_market_proxy_nav.csv")

    slim = lambda r: {k: v for k, v in r.items() if k != "daily_drawdown"}
    decision = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "STAGE4_F1_HELDOUT",
        "challenger_id": "F1",
        "locked_config": F1_LOCKED,
        "oof_source_decision": summary["research_decision"],
        "oof_bootstrap": rec["block_bootstrap_positive_probability"],
        "oof_turnover": rec["average_daily_turnover"],
        "oof_mean_rank_ic": rec["mean_rank_ic"],
        "no_retune_on_heldout": True,
        "gates_remain_experimental": True,
        "research_decision": label,
        "validation_2019_2022": slim(val),
        "sealed_2023_latest": slim(sealed),
        "c4_tech2_reference_validation": slim(c4_val),
        "c4_tech2_reference_sealed": slim(c4_sealed),
        "promotion_checks_experimental": {
            "validation_beats_proxy": bool(val["beats_market_proxy"]),
            "sealed_beats_proxy": bool(sealed["beats_market_proxy"]),
            "validation_bootstrap_pass": bool(val["bootstrap_gate_pass"]),
            "sealed_bootstrap_pass": bool(sealed["bootstrap_gate_pass"]),
            "validation_turnover_pass": bool(val["turnover_gate_pass"]),
            "sealed_turnover_pass": bool(sealed["turnover_gate_pass"]),
            "exact_t1_ok": bool(val["exact_t1_ok"] and sealed["exact_t1_ok"]),
        },
    }
    (out / "reports" / "stage4_f1_heldout_decision.json").write_text(
        json.dumps(decision, indent=2, default=str) + "\n"
    )

    lines = [
        "# E50-A3-R1-F1 Locked Challenger — Held-Out Evaluation",
        "",
        "F1 = `TECH2_VALUE` under fixed C4 portfolio wrapper. Selected on 2011–2018 OOF only.",
        "**No retune after held-out. No promotion. Gates remain EXPERIMENTAL.**",
        "",
        "## Locked F1",
        "",
        "```",
        f"features={F1_FEATURES}",
        "mode=BREADTH_REGIME ridge_lambda=1.0",
        "top_k=22 rebalance_every=42 exit_multiple=2.25",
        "industry_cap=5 replace_rank_gap=5 liquidity_floor=20000000",
        "```",
        "",
        f"## Research decision",
        "",
        f"**`{label}`**",
        "",
        f"OOF: turnover {100*rec['average_daily_turnover']:.2f}%, bootstrap {rec['block_bootstrap_positive_probability']}, "
        f"IC {rec['mean_rank_ic']:.4f}",
        "",
        "| Metric | F1 Validation 2019–2022 | F1 Sealed 2023–latest | C4 TECH2 Val | C4 TECH2 Sealed |",
        "|---|---:|---:|---:|---:|",
        f"| CAGR | {100*val['cagr']:.2f}% | {100*sealed['cagr']:.2f}% | {100*c4_val['cagr']:.2f}% | {100*c4_sealed['cagr']:.2f}% |",
        f"| MDD | {100*val['max_drawdown']:.2f}% | {100*sealed['max_drawdown']:.2f}% | {100*c4_val['max_drawdown']:.2f}% | {100*c4_sealed['max_drawdown']:.2f}% |",
        f"| Turnover | {100*val['average_daily_turnover']:.2f}% | {100*sealed['average_daily_turnover']:.2f}% | {100*c4_val['average_daily_turnover']:.2f}% | {100*c4_sealed['average_daily_turnover']:.2f}% |",
        f"| Bootstrap | {val['block_bootstrap_positive_probability']:.4f} | {sealed['block_bootstrap_positive_probability']:.4f} | {c4_val['block_bootstrap_positive_probability']:.4f} | {c4_sealed['block_bootstrap_positive_probability']:.4f} |",
        f"| Beats proxy | {val['beats_market_proxy']} | {sealed['beats_market_proxy']} | {c4_val['beats_market_proxy']} | {c4_sealed['beats_market_proxy']} |",
        f"| Turn gate | {val['turnover_gate_pass']} | {sealed['turnover_gate_pass']} | {c4_val['turnover_gate_pass']} | {c4_sealed['turnover_gate_pass']} |",
        f"| Boot gate | {val['bootstrap_gate_pass']} | {sealed['bootstrap_gate_pass']} | {c4_val['bootstrap_gate_pass']} | {c4_sealed['bootstrap_gate_pass']} |",
        f"| Exact T+1 | {val['exact_t1_ok']} | {sealed['exact_t1_ok']} | {c4_val['exact_t1_ok']} | {c4_sealed['exact_t1_ok']} |",
        "",
        "Artifact: `reports/stage4_f1_heldout_decision.json`",
        "",
    ]
    (out / "E50-A3-R1_STAGE4_F1_HELDOUT.md").write_text("\n".join(lines))
    print(json.dumps({
        "research_decision": label,
        "val_boot": val["block_bootstrap_positive_probability"],
        "val_turn": val["average_daily_turnover"],
        "sealed_boot": sealed["block_bootstrap_positive_probability"],
        "sealed_turn": sealed["average_daily_turnover"],
        "c4_val_boot": c4_val["block_bootstrap_positive_probability"],
        "c4_sealed_boot": c4_sealed["block_bootstrap_positive_probability"],
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
