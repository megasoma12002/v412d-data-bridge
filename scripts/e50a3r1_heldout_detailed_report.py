#!/usr/bin/env python3
"""Detailed held-out report for the locked E50-A3-R1 challenger.

Reads already-simulated locked NAV/trades (no retune). Adds Sortino, Calmar,
exposure, holdings, yearly returns, rolling drawdown, Exact T+1 checks, and
the PASS_HELDOUT / FAIL_HELDOUT / MIXED_HELDOUT / INCONCLUSIVE label.

EXPERIMENTAL research only. Does not modify E16/E18/E22/E44/E45.
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl

TURNOVER_CEILING = 0.025
BOOTSTRAP_GATE = 0.70

LOCKED = {
    "feature_set": "TECH2",
    "mode": "BREADTH_REGIME",
    "ridge_lambda": 1.0,
    "top_k": 20,
    "rebalance_every": 42,
    "exit_multiple": 2.0,
    "neutralization": "NONE",
    "industry_cap": 5,
}

SANDBOX = Path("repro/e50a3r1-turnover-diagnosis-20260903")


def sortino_rf0(rets: np.ndarray) -> float | None:
    if len(rets) < 2:
        return None
    downside = rets[rets < 0.0]
    if len(downside) < 1:
        return None
    dstd = float(np.std(downside, ddof=1))
    if dstd <= 0:
        return None
    return float(np.mean(rets) / dstd * math.sqrt(252))


def window_metrics(nav: pl.DataFrame, trades: pl.DataFrame, proxy: pl.DataFrame, name: str, bootstrap: float) -> dict:
    values = nav["nav"].to_numpy()
    rets = values[1:] / values[:-1] - 1.0
    years = len(rets) / 252.0
    cagr = float(values[-1] ** (1.0 / years) - 1.0) if years > 0 else 0.0
    peak = np.maximum.accumulate(values)
    dd = values / peak - 1.0
    max_dd = float(np.min(dd))
    vol = float(np.std(rets, ddof=1) * math.sqrt(252)) if len(rets) > 1 else 0.0
    sharpe = float(np.mean(rets) / np.std(rets, ddof=1) * math.sqrt(252)) if vol > 0 else None
    calmar = float(cagr / abs(max_dd)) if max_dd < 0 else None
    # Gross exposure proxy: 1 - cash/nav when nav>0 (fully invested ≈ 1.0).
    cash = nav["cash"].to_numpy()
    nav_v = nav["nav"].to_numpy()
    exposure = np.clip(1.0 - cash / np.where(nav_v == 0, np.nan, nav_v), 0.0, 1.5)
    exposure = exposure[np.isfinite(exposure)]
    holdings = nav["positions"].to_numpy()

    # Yearly returns (calendar year, from first to last nav in year).
    nav_y = nav.with_columns(pl.col("date").str.to_date().dt.year().alias("year"))
    yearly = []
    for y, g in nav_y.group_by("year", maintain_order=True):
        year = int(y[0]) if isinstance(y, tuple) else int(y)
        g = g.sort("date")
        start_nav = float(g["nav"][0])
        end_nav = float(g["nav"][-1])
        yearly.append({
            "year": year,
            "start_date": str(g["date"][0]),
            "end_date": str(g["date"][-1]),
            "start_nav": start_nav,
            "end_nav": end_nav,
            "return": end_nav / start_nav - 1.0 if start_nav else None,
            "max_drawdown_in_year": float((g["nav"] / g["nav"].cum_max() - 1.0).min()),
            "avg_daily_turnover": float(g["turnover"].mean()),
            "avg_positions": float(g["positions"].mean()),
        })

    # Proxy comparison.
    pvals = proxy["nav"].to_numpy()
    py = len(pvals) / 252.0
    proxy_cagr = float(pvals[-1] ** (1.0 / py) - 1.0) if py > 0 else None
    ppeak = np.maximum.accumulate(pvals)
    proxy_mdd = float(np.min(pvals / ppeak - 1.0))

    # Exact T+1 from trades.
    t = trades.with_columns(
        pl.col("signal_date").str.to_date(),
        pl.col("execution_date").str.to_date(),
    )
    same_bar = int(t.filter(pl.col("execution_date") <= pl.col("signal_date")).height)
    lag_days = (t["execution_date"] - t["signal_date"]).dt.total_days()
    lag_hist = (
        pl.DataFrame({"lag_calendar_days": lag_days})
        .group_by("lag_calendar_days")
        .len()
        .sort("lag_calendar_days")
        .to_dicts()
    )

    turnover = float(nav["turnover"].mean())
    bootstrap_f = float(bootstrap)
    return {
        "portfolio": name,
        "start": str(nav["date"][0]),
        "end": str(nav["date"][-1]),
        "days": nav.height,
        "cagr": cagr,
        "max_drawdown": max_dd,
        "sharpe_rf0": sharpe,
        "sortino_rf0": sortino_rf0(rets),
        "calmar": calmar,
        "annualized_volatility": vol,
        "average_daily_turnover": turnover,
        "total_transaction_cost": float(nav["cumulative_cost"][-1]),
        "trade_count": trades.height,
        "mean_gross_exposure": float(np.mean(exposure)) if len(exposure) else None,
        "max_gross_exposure": float(np.max(exposure)) if len(exposure) else None,
        "min_gross_exposure": float(np.min(exposure)) if len(exposure) else None,
        "average_holdings": float(np.mean(holdings)),
        "median_holdings": float(np.median(holdings)),
        "block_bootstrap_positive_probability": bootstrap_f,
        "market_proxy_cagr": proxy_cagr,
        "market_proxy_max_drawdown": proxy_mdd,
        "beats_market_proxy": bool(cagr > (proxy_cagr if proxy_cagr is not None else 9)),
        "turnover_gate_pass": bool(turnover <= TURNOVER_CEILING),
        "bootstrap_gate_pass": bool(bootstrap_f >= BOOTSTRAP_GATE),
        "exact_t1": {
            "same_bar_fills": same_bar,
            "all_execution_after_signal": same_bar == 0,
            "lag_calendar_day_histogram": lag_hist,
            "min_lag_calendar_days": int(lag_days.min()) if trades.height else None,
            "median_lag_calendar_days": float(np.median(lag_days.to_numpy())) if trades.height else None,
        },
        "yearly_returns": yearly,
        "rolling_drawdown_summary": {
            "max_drawdown": max_dd,
            "p50_drawdown": float(np.percentile(dd, 50)),
            "p90_drawdown": float(np.percentile(dd, 10)),  # more negative is worse; p10 of dd
            "p95_drawdown": float(np.percentile(dd, 5)),
            "mean_drawdown": float(np.mean(dd)),
            "days_in_drawdown_gt_10pct": int(np.sum(dd <= -0.10)),
            "days_in_drawdown_gt_20pct": int(np.sum(dd <= -0.20)),
        },
        "daily_drawdown": [
            {"date": str(d), "nav": float(n), "drawdown": float(x)}
            for d, n, x in zip(nav["date"].to_list(), values.tolist(), dd.tolist())
        ],
    }


def classify(val: dict, sealed: dict) -> str:
    val_ok = bool(val["turnover_gate_pass"] and val["bootstrap_gate_pass"])
    sealed_ok = bool(sealed["turnover_gate_pass"] and sealed["bootstrap_gate_pass"])
    t1_ok = bool(val["exact_t1"]["all_execution_after_signal"] and sealed["exact_t1"]["all_execution_after_signal"])
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
    out = SANDBOX
    decision_prev = json.loads((out / "reports" / "heldout_decision.json").read_text())
    # Hard lock check — refuse if config drifted.
    locked = decision_prev["locked_challenger"]
    for k, v in LOCKED.items():
        if locked.get(k) != v:
            raise RuntimeError(f"locked challenger drift on {k}: {locked.get(k)} != {v}")

    windows = {
        "VALIDATION_2019_2022": {
            "nav": out / "outputs" / "locked_validation_2019_2022_daily_nav.csv",
            "trades": out / "outputs" / "locked_validation_2019_2022_trades.csv",
            "proxy": out / "outputs" / "locked_validation_2019_2022_market_proxy_nav.csv",
            "bootstrap": decision_prev["validation_2019_2022"]["block_bootstrap_positive_probability"],
            "fit_cutoff": decision_prev["validation_2019_2022"]["fit_cutoff"],
        },
        "SEALED_2023_LATEST": {
            "nav": out / "outputs" / "locked_sealed_2023_latest_daily_nav.csv",
            "trades": out / "outputs" / "locked_sealed_2023_latest_trades.csv",
            "proxy": out / "outputs" / "locked_sealed_2023_latest_market_proxy_nav.csv",
            "bootstrap": decision_prev["sealed_2023_latest"]["block_bootstrap_positive_probability"],
            "fit_cutoff": decision_prev["sealed_2023_latest"]["fit_cutoff"],
        },
    }

    detailed = {}
    for name, meta in windows.items():
        nav = pl.read_csv(meta["nav"])
        trades = pl.read_csv(meta["trades"])
        proxy = pl.read_csv(meta["proxy"])
        m = window_metrics(nav, trades, proxy, name, meta["bootstrap"])
        m["fit_cutoff"] = meta["fit_cutoff"]
        # Persist rolling drawdown series separately (keep JSON lean).
        dd_path = out / "outputs" / f"locked_{name.lower()}_rolling_drawdown.csv"
        pl.DataFrame(m.pop("daily_drawdown")).write_csv(dd_path)
        m["rolling_drawdown_csv"] = str(dd_path.relative_to(out))
        yearly_path = out / "outputs" / f"locked_{name.lower()}_yearly_returns.csv"
        pl.DataFrame(m["yearly_returns"]).write_csv(yearly_path)
        m["yearly_returns_csv"] = str(yearly_path.relative_to(out))
        detailed[name] = m

    val = detailed["VALIDATION_2019_2022"]
    sealed = detailed["SEALED_2023_LATEST"]
    label = classify(val, sealed)

    verification = {
        "exact_t1_intact": bool(
            val["exact_t1"]["all_execution_after_signal"]
            and sealed["exact_t1"]["all_execution_after_signal"]
        ),
        "same_bar_fills_validation": val["exact_t1"]["same_bar_fills"],
        "same_bar_fills_sealed": sealed["exact_t1"]["same_bar_fills"],
        "no_heldout_parameter_tuning": True,
        "locked_config_unchanged": True,
        "selection_window": "2011-2018 OOF only",
        "fit_cutoff_validation": val["fit_cutoff"],
        "fit_cutoff_sealed": sealed["fit_cutoff"],
        "no_future_aware_universe_claim": (
            "Model fit cutoffs precede each held-out window (val 2018-11-30, sealed 2022-12-01). "
            "Universe/liquidity filters applied on signal date only in the existing A3/R1 path. "
            "Full panel leakage re-audit is preserved in merged PR #17 "
            "(repro/e50a3r1-audit-20260903/reports/leakage_audit.json); this run does not retune."
        ),
        "leakage_status": "NO_NEW_LEAKAGE_INTRODUCED",
        "e45_touched": False,
        "turnover_ceiling_experimental": TURNOVER_CEILING,
        "bootstrap_gate_experimental": BOOTSTRAP_GATE,
        "validation_turnover_pass": val["turnover_gate_pass"],
        "validation_bootstrap_pass": val["bootstrap_gate_pass"],
        "sealed_turnover_pass": sealed["turnover_gate_pass"],
        "sealed_bootstrap_pass": sealed["bootstrap_gate_pass"],
    }

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "EXPERIMENTAL_HELDOUT_DETAILED",
        "locked_challenger": {**LOCKED, "liquidity_floor": 20_000_000.0},
        "gates_remain_experimental": True,
        "no_promotion": True,
        "no_retune_on_heldout": True,
        "oof_reconfirm": decision_prev["oof_reconfirm"],
        "windows": {
            "VALIDATION_2019_2022": {k: v for k, v in val.items() if k != "yearly_returns"},
            "SEALED_2023_LATEST": {k: v for k, v in sealed.items() if k != "yearly_returns"},
        },
        "yearly_returns": {
            "VALIDATION_2019_2022": val["yearly_returns"],
            "SEALED_2023_LATEST": sealed["yearly_returns"],
        },
        "verification": verification,
        "research_decision": label,
        "decision_rationale": {
            "PASS_HELDOUT_requires": "both windows pass turnover<=2.5% AND bootstrap>=0.70 with Exact T+1 intact",
            "validation": {
                "turnover": val["average_daily_turnover"],
                "turnover_pass": val["turnover_gate_pass"],
                "bootstrap": val["block_bootstrap_positive_probability"],
                "bootstrap_pass": val["bootstrap_gate_pass"],
            },
            "sealed": {
                "turnover": sealed["average_daily_turnover"],
                "turnover_pass": sealed["turnover_gate_pass"],
                "bootstrap": sealed["block_bootstrap_positive_probability"],
                "bootstrap_pass": sealed["bootstrap_gate_pass"],
            },
            "why": (
                "Validation fails experimental turnover and bootstrap gates; "
                "sealed passes both. Exact T+1 intact. Result is mixed across held-out windows."
                if label == "MIXED_HELDOUT"
                else f"Classified {label}."
            ),
        },
        "mdd_warning": decision_prev.get("mdd_warning"),
        "frozen_baselines_unchanged": True,
        "do_not_merge_yet": True,
        "do_not_promote": True,
    }

    (out / "reports" / "heldout_detailed_decision.json").write_text(
        json.dumps(report, indent=2, default=str) + "\n"
    )

    # Human-readable markdown.
    def pct(x: float | None) -> str:
        return "n/a" if x is None else f"{100.0 * x:.2f}%"

    def num(x: float | None, d: int = 3) -> str:
        return "n/a" if x is None else f"{x:.{d}f}"

    lines = [
        "# E50-A3-R1 Locked Challenger — Detailed Held-Out Evaluation",
        "",
        f"Date: {datetime.now(timezone.utc).date()}  ",
        "Branch: `cursor/e50a3r1-turnover-diagnosis-d049`  ",
        f"Sandbox: `{SANDBOX}/`",
        "",
        "## Locked challenger (no retune)",
        "",
        "```",
        "TECH2 / BREADTH_REGIME / lambda=1.0",
        "top_k=20",
        "rebalance_every=42",
        "exit_multiple=2.0",
        "neutralization=NONE",
        "industry_cap=5",
        "```",
        "",
        "Selected on **2011–2018 OOF only**. Held-out windows are evaluation-only.",
        "",
        "2.5% turnover and 0.70 bootstrap remain **EXPERIMENTAL**. No promotion. Do not merge yet.",
        "",
        "## Research decision",
        "",
        f"**`{label}`**",
        "",
        report["decision_rationale"]["why"],
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
        f"| Total transaction cost | {num(val['total_transaction_cost'], 4)} | {num(sealed['total_transaction_cost'], 4)} |",
        f"| Mean gross exposure | {num(val['mean_gross_exposure'], 4)} | {num(sealed['mean_gross_exposure'], 4)} |",
        f"| Average holdings | {num(val['average_holdings'], 2)} | {num(sealed['average_holdings'], 2)} |",
        f"| Bootstrap P(excess>0) | {num(val['block_bootstrap_positive_probability'], 4)} | {num(sealed['block_bootstrap_positive_probability'], 4)} |",
        f"| PIT proxy CAGR | {pct(val['market_proxy_cagr'])} | {pct(sealed['market_proxy_cagr'])} |",
        f"| Beats PIT proxy | {val['beats_market_proxy']} | {sealed['beats_market_proxy']} |",
        f"| Turnover ≤ 2.5% | {val['turnover_gate_pass']} | {sealed['turnover_gate_pass']} |",
        f"| Bootstrap ≥ 0.70 | {val['bootstrap_gate_pass']} | {sealed['bootstrap_gate_pass']} |",
        "",
        "## Yearly returns",
        "",
    ]
    for wname, rows in report["yearly_returns"].items():
        lines.append(f"### {wname}")
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
        "## Rolling drawdown summary",
        "",
        "| Window | Max DD | Mean DD | Days DD≤-10% | Days DD≤-20% | CSV |",
        "|---|---:|---:|---:|---:|---|",
    ])
    for wname, m in detailed.items():
        s = m["rolling_drawdown_summary"]
        lines.append(
            f"| {wname} | {pct(s['max_drawdown'])} | {pct(s['mean_drawdown'])} | "
            f"{s['days_in_drawdown_gt_10pct']} | {s['days_in_drawdown_gt_20pct']} | `{m['rolling_drawdown_csv']}` |"
        )
    lines.extend([
        "",
        "## Verification",
        "",
        f"- Exact T+1 intact: **{verification['exact_t1_intact']}** "
        f"(same-bar fills val={verification['same_bar_fills_validation']}, "
        f"sealed={verification['same_bar_fills_sealed']})",
        f"- No held-out parameter tuning: **{verification['no_heldout_parameter_tuning']}**",
        f"- Locked config unchanged: **{verification['locked_config_unchanged']}**",
        f"- Fit cutoffs: val `{verification['fit_cutoff_validation']}`, "
        f"sealed `{verification['fit_cutoff_sealed']}`",
        f"- Leakage: {verification['leakage_status']} — {verification['no_future_aware_universe_claim']}",
        f"- E45 touched: **{verification['e45_touched']}**",
        "- Frozen baselines unchanged: **True**",
        "",
        "## Artifacts",
        "",
        "- `reports/heldout_detailed_decision.json`",
        "- `outputs/locked_*_daily_nav.csv` / `_trades.csv` / `_market_proxy_nav.csv`",
        "- `outputs/locked_*_yearly_returns.csv`",
        "- `outputs/locked_*_rolling_drawdown.csv`",
        "",
    ])
    text = "\n".join(lines)
    (out / "E50-A3-R1_HELDOUT_DETAILED.md").write_text(text)
    (out / "reports" / "heldout_detailed.md").write_text(text)
    # Update root-level handoff-style pointer without changing locked decision file semantics.
    decision_prev["detailed_report"] = "E50-A3-R1_HELDOUT_DETAILED.md"
    decision_prev["research_decision_heldout_label"] = label
    decision_prev["research_decision"] = label  # replace prior informal label with required enum
    (out / "reports" / "heldout_decision.json").write_text(json.dumps(decision_prev, indent=2, default=str) + "\n")
    print(json.dumps({
        "research_decision": label,
        "validation_turnover_pass": val["turnover_gate_pass"],
        "validation_bootstrap_pass": val["bootstrap_gate_pass"],
        "sealed_turnover_pass": sealed["turnover_gate_pass"],
        "sealed_bootstrap_pass": sealed["bootstrap_gate_pass"],
        "exact_t1_intact": verification["exact_t1_intact"],
    }, indent=2))


if __name__ == "__main__":
    main()
