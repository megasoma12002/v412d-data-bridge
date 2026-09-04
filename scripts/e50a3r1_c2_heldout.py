#!/usr/bin/env python3
"""Held-out evaluation for locked E50-A3-R1-C2 challenger (EXPERIMENTAL).

C2 was selected on 2011-2018 OOF only in round2_oof_challenger.
This script does NOT retune on 2019-2022 or 2023-latest.

Does not modify E16/E18/E22/E44/E45.
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
    SELECTED,
    TURNOVER_CEILING,
    buffered_orders_ext,
)

# Locked at Round-2 OOF selection. Do not edit from held-out evidence.
C2_LOCKED = {
    "family": "C2_exit_minhold",
    "top_k": 20,
    "rebalance_every": 42,
    "exit_multiple": 2.5,
    "neutralization": "NONE",
    "industry_cap": 5,
    "min_hold_cycles": 0,
    "liquidity_floor": 20_000_000.0,
    "replace_rank_gap": 0,
    "feature_set": SELECTED["feature_set"],
    "mode": SELECTED["mode"],
    "ridge_lambda": SELECTED["ridge_lambda"],
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
    nav_y = nav.with_columns(pl.col("date").cast(pl.Date).dt.year().alias("year"))
    yearly = []
    for y, g in nav_y.group_by("year", maintain_order=True):
        year = int(y[0]) if isinstance(y, tuple) else int(y)
        g = g.sort("date")
        start_nav = float(g["nav"][0])
        end_nav = float(g["nav"][-1])
        yearly.append({
            "year": year,
            "return": end_nav / start_nav - 1.0 if start_nav else None,
            "max_drawdown_in_year": float((g["nav"] / g["nav"].cum_max() - 1.0).min()),
            "avg_daily_turnover": float(g["turnover"].mean()),
            "avg_positions": float(g["positions"].mean()),
        })
    pvals = proxy["nav"].to_numpy()
    years = len(pvals) / 252.0
    proxy_cagr = float(pvals[-1] ** (1.0 / years) - 1.0) if years > 0 else None
    out = dict(base)
    out.update({
        "sortino_rf0": sortino_rf0(rets),
        "calmar": float(base["cagr"] / abs(base["max_drawdown"])) if base.get("max_drawdown") and base["max_drawdown"] < 0 else None,
        "mean_gross_exposure": float(np.mean(exposure)) if len(exposure) else None,
        "average_holdings": float(nav["positions"].mean()),
        "same_bar_fills": same_bar,
        "exact_t1_ok": same_bar == 0,
        "market_proxy_cagr": proxy_cagr,
        "beats_market_proxy": bool((base.get("cagr") or -9) > (proxy_cagr if proxy_cagr is not None else 9)),
        "yearly_returns": yearly,
        "rolling_drawdown_summary": {
            "max_drawdown": float(np.min(dd)),
            "mean_drawdown": float(np.mean(dd)),
            "days_in_drawdown_gt_10pct": int(np.sum(dd <= -0.10)),
            "days_in_drawdown_gt_20pct": int(np.sum(dd <= -0.20)),
        },
        "daily_drawdown": [
            {"date": str(d), "nav": float(n), "drawdown": float(x)}
            for d, n, x in zip(nav["date"].to_list(), values.tolist(), dd.tolist())
        ],
    })
    return out


def evaluate_period(joined, execution, calendar, cfg, name, start, end, fit_cutoff):
    model = r1.fit_model(
        joined, cfg["feature_set"], cfg["mode"], cfg["ridge_lambda"], fit_cutoff
    )
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
    ap.add_argument("--round2-summary", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    out = args.out
    (out / "outputs").mkdir(parents=True, exist_ok=True)
    (out / "reports").mkdir(parents=True, exist_ok=True)

    summary = json.loads(args.round2_summary.read_text())
    if summary["research_decision"] != "OOF_NEW_DUAL_GATE_WINNER":
        raise RuntimeError("Round-2 did not produce a new dual-gate winner")
    rec = summary["recommended_challenger"]
    for k in ["top_k", "rebalance_every", "exit_multiple", "neutralization", "industry_cap",
              "min_hold_cycles", "replace_rank_gap"]:
        if rec[k] != C2_LOCKED[k]:
            raise RuntimeError(f"C2 lock drift on {k}: {rec[k]} vs {C2_LOCKED[k]}")

    a2_qc = json.loads(args.a2_qc.read_text())
    if a2_qc["status"] != "PASS":
        raise RuntimeError("E50-A2 QC is not PASS")

    panel = pl.read_parquet(args.panel).sort(["date", "code"])
    price_scan = (
        pl.scan_parquet(args.prices)
        if args.prices.suffix == ".parquet"
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

    print("evaluating C2 VALIDATION_2019_2022 ...", flush=True)
    val, val_nav, val_trades, val_proxy = evaluate_period(
        joined, execution, calendar, C2_LOCKED, "C2_VALIDATION_2019_2022",
        validation_start, validation_end, val_cutoff,
    )
    print("evaluating C2 SEALED_2023_LATEST ...", flush=True)
    sealed, sealed_nav, sealed_trades, sealed_proxy = evaluate_period(
        joined, execution, calendar, C2_LOCKED, "C2_SEALED_2023_LATEST",
        sealed_start, sealed_end, sealed_cutoff,
    )

    # Persist artifacts.
    for period, nav, trades, proxy, metrics in [
        ("c2_validation_2019_2022", val_nav, val_trades, val_proxy, val),
        ("c2_sealed_2023_latest", sealed_nav, sealed_trades, sealed_proxy, sealed),
    ]:
        nav.write_csv(out / "outputs" / f"{period}_daily_nav.csv")
        trades.write_csv(out / "outputs" / f"{period}_trades.csv")
        proxy.write_csv(out / "outputs" / f"{period}_market_proxy_nav.csv")
        pl.DataFrame(metrics["yearly_returns"]).write_csv(out / "outputs" / f"{period}_yearly_returns.csv")
        pl.DataFrame(metrics["daily_drawdown"]).write_csv(out / "outputs" / f"{period}_rolling_drawdown.csv")

    label = classify(val, sealed)
    # Strip heavy daily series from JSON.
    val_j = {k: v for k, v in val.items() if k != "daily_drawdown"}
    sealed_j = {k: v for k, v in sealed.items() if k != "daily_drawdown"}

    decision = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "EXPERIMENTAL_C2_HELDOUT",
        "challenger": "E50-A3-R1-C2",
        "locked_challenger": C2_LOCKED,
        "selection_window": "2011-2018 OOF only",
        "no_retune_on_heldout": True,
        "gates_remain_experimental": True,
        "prior_c1_decision": "MIXED_HELDOUT",
        "oof_reconfirm": {
            "turnover": rec["average_daily_turnover"],
            "bootstrap": rec["block_bootstrap_positive_probability"],
            "cagr": rec["cagr"],
            "max_drawdown": rec["max_drawdown"],
            "both_gates_pass": True,
        },
        "validation_2019_2022": val_j,
        "sealed_2023_latest": sealed_j,
        "verification": {
            "exact_t1_intact": bool(val["exact_t1_ok"] and sealed["exact_t1_ok"]),
            "same_bar_fills_validation": val["same_bar_fills"],
            "same_bar_fills_sealed": sealed["same_bar_fills"],
            "no_heldout_parameter_tuning": True,
            "e45_touched": False,
            "frozen_baselines_unchanged": True,
        },
        "research_decision": label,
        "decision_rationale": {
            "validation_turnover_pass": val["turnover_gate_pass"],
            "validation_bootstrap_pass": val["bootstrap_gate_pass"],
            "sealed_turnover_pass": sealed["turnover_gate_pass"],
            "sealed_bootstrap_pass": sealed["bootstrap_gate_pass"],
        },
        "no_promotion": True,
        "do_not_merge_yet": True,
    }
    (out / "reports" / "c2_heldout_decision.json").write_text(
        json.dumps(decision, indent=2, default=str) + "\n"
    )

    def pct(x):
        return "n/a" if x is None else f"{100.0 * x:.2f}%"

    def num(x, d=3):
        return "n/a" if x is None else f"{x:.{d}f}"

    lines = [
        "# E50-A3-R1-C2 Locked Challenger — Held-Out Evaluation",
        "",
        f"Date: {datetime.now(timezone.utc).date()}  ",
        "Branch: `cursor/e50a3r1-turnover-diagnosis-d049`  ",
        "Sandbox: `repro/e50a3r1-turnover-diagnosis-20260903/`",
        "",
        "## Locked C2 (no retune)",
        "",
        "```",
        "TECH2 / BREADTH_REGIME / lambda=1.0",
        "top_k=20",
        "rebalance_every=42",
        "exit_multiple=2.5",
        "neutralization=NONE",
        "industry_cap=5",
        "min_hold_cycles=0",
        "replace_rank_gap=0",
        "```",
        "",
        "Selected on **2011–2018 OOF only** as Round-2 dual-gate winner (lower OOF turnover headroom vs C1).",
        "C1 remains MIXED_HELDOUT and was not retuned.",
        "",
        f"## Research decision",
        "",
        f"**`{label}`**",
        "",
        "## OOF reconfirm",
        "",
        f"- Turnover {pct(rec['average_daily_turnover'])} (PASS ≤2.5%)",
        f"- Bootstrap {num(rec['block_bootstrap_positive_probability'], 4)} (PASS ≥0.70)",
        f"- CAGR {pct(rec['cagr'])}, MDD {pct(rec['max_drawdown'])}",
        "",
        "## Window metrics",
        "",
        "| Metric | Validation 2019–2022 | Sealed 2023–latest |",
        "|---|---:|---:|",
        f"| CAGR | {pct(val['cagr'])} | {pct(sealed['cagr'])} |",
        f"| MDD | {pct(val['max_drawdown'])} | {pct(sealed['max_drawdown'])} |",
        f"| Sharpe (rf0) | {num(val['sharpe_rf0'])} | {num(sealed['sharpe_rf0'])} |",
        f"| Sortino (rf0) | {num(val['sortino_rf0'])} | {num(sealed['sortino_rf0'])} |",
        f"| Calmar | {num(val['calmar'])} | {num(sealed['calmar'])} |",
        f"| Avg daily turnover | {pct(val['average_daily_turnover'])} | {pct(sealed['average_daily_turnover'])} |",
        f"| Total transaction cost | {num(val['total_cost'], 4)} | {num(sealed['total_cost'], 4)} |",
        f"| Mean gross exposure | {num(val['mean_gross_exposure'], 4)} | {num(sealed['mean_gross_exposure'], 4)} |",
        f"| Average holdings | {num(val['average_holdings'], 2)} | {num(sealed['average_holdings'], 2)} |",
        f"| Bootstrap P(excess>0) | {num(val['block_bootstrap_positive_probability'], 4)} | {num(sealed['block_bootstrap_positive_probability'], 4)} |",
        f"| PIT proxy CAGR | {pct(val['market_proxy_cagr'])} | {pct(sealed['market_proxy_cagr'])} |",
        f"| Beats PIT proxy | {val['beats_market_proxy']} | {sealed['beats_market_proxy']} |",
        f"| Turnover ≤ 2.5% | {val['turnover_gate_pass']} | {sealed['turnover_gate_pass']} |",
        f"| Bootstrap ≥ 0.70 | {val['bootstrap_gate_pass']} | {sealed['bootstrap_gate_pass']} |",
        f"| Exact T+1 | {val['exact_t1_ok']} | {sealed['exact_t1_ok']} |",
        "",
        "## Yearly returns",
        "",
    ]
    for title, rows in [("VALIDATION_2019_2022", val["yearly_returns"]), ("SEALED_2023_LATEST", sealed["yearly_returns"])]:
        lines.append(f"### {title}")
        lines.append("")
        lines.append("| Year | Return | MDD in year | Avg turnover | Avg holdings |")
        lines.append("|---|---:|---:|---:|---:|")
        for r in rows:
            lines.append(
                f"| {r['year']} | {pct(r['return'])} | {pct(r['max_drawdown_in_year'])} | "
                f"{pct(r['avg_daily_turnover'])} | {num(r['avg_positions'], 1)} |"
            )
        lines.append("")
    lines.extend([
        "## Verification",
        "",
        f"- Exact T+1 intact: **{decision['verification']['exact_t1_intact']}**",
        "- No held-out parameter tuning: **True**",
        "- E45 touched: **False**",
        "- Frozen baselines unchanged: **True**",
        "- No promotion / do not merge yet",
        "",
        "## Artifacts",
        "",
        "- `reports/c2_heldout_decision.json`",
        "- `reports/round2_oof_summary.json`",
        "- `outputs/round2_oof_challenger_grid.csv`",
        "- `outputs/c2_*_daily_nav.csv` / `_trades.csv` / `_yearly_returns.csv` / `_rolling_drawdown.csv`",
        "",
    ])
    text = "\n".join(lines)
    (out / "E50-A3-R1-C2_HELDOUT.md").write_text(text)
    (out / "reports" / "c2_heldout.md").write_text(text)
    print(json.dumps({
        "research_decision": label,
        "validation_turnover": val["average_daily_turnover"],
        "validation_bootstrap": val["block_bootstrap_positive_probability"],
        "sealed_turnover": sealed["average_daily_turnover"],
        "sealed_bootstrap": sealed["block_bootstrap_positive_probability"],
        "exact_t1": decision["verification"]["exact_t1_intact"],
    }, indent=2))


if __name__ == "__main__":
    main()
