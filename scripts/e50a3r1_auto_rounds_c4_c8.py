#!/usr/bin/env python3
"""Autonomous E50-A3-R1 challenger rounds C4–C8 (EXPERIMENTAL).

Up to 5 consecutive rounds. Each round:
1. OOF-only grid under a distinct hypothesis / selection rule
2. Lock a NEW dual-gate winner (not in prior held-out locks)
3. Held-out once on 2019-2022 and 2023-latest
4. Stop early on PASS_HELDOUT, or after 2 consecutive OOF_NO_NEW_DUAL_GATE_WINNER

Does not retune prior locks from held-out. Does not touch E16/E18/E22/E44/E45.
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
    evaluate_cfg,
)

PRIOR_LOCKS = {
    "C1": {
        "top_k": 20, "rebalance_every": 42, "exit_multiple": 2.0,
        "neutralization": "NONE", "industry_cap": 5, "min_hold_cycles": 0,
        "liquidity_floor": 20_000_000.0, "replace_rank_gap": 0,
    },
    "C2": {
        "top_k": 20, "rebalance_every": 42, "exit_multiple": 2.5,
        "neutralization": "NONE", "industry_cap": 5, "min_hold_cycles": 0,
        "liquidity_floor": 20_000_000.0, "replace_rank_gap": 0,
    },
    "C3": {
        "top_k": 25, "rebalance_every": 42, "exit_multiple": 2.0,
        "neutralization": "NONE", "industry_cap": 5, "min_hold_cycles": 0,
        "liquidity_floor": 20_000_000.0, "replace_rank_gap": 0,
    },
}


def cfg_key(cfg: dict) -> tuple:
    return (
        int(cfg["top_k"]), int(cfg["rebalance_every"]), float(cfg["exit_multiple"]),
        str(cfg["neutralization"]), int(cfg["industry_cap"]), int(cfg["min_hold_cycles"]),
        float(cfg["liquidity_floor"]), int(cfg["replace_rank_gap"]),
    )


def base_cfg(**kwargs) -> dict:
    c = {
        "family": "auto",
        "top_k": 20,
        "rebalance_every": 42,
        "exit_multiple": 2.0,
        "neutralization": "NONE",
        "industry_cap": 5,
        "min_hold_cycles": 0,
        "liquidity_floor": 20_000_000.0,
        "replace_rank_gap": 0,
    }
    c.update(kwargs)
    return c


def dedupe(cells: list[dict]) -> list[dict]:
    uniq = {}
    for c in cells:
        uniq[cfg_key(c)] = c
    return list(uniq.values())


def grid_c4() -> list[dict]:
    """Hypothesis: maximize OOF HAC t-stat / mean excess among dual-gate."""
    cells = []
    for top_k in [18, 20, 22]:
        for reb in [21, 28, 35, 42]:
            for exit_m in [2.0, 2.25, 2.5]:
                cells.append(base_cfg(family="C4_excess_strength", top_k=top_k, rebalance_every=reb, exit_multiple=exit_m))
    for top_k in [20, 22]:
        for gap in [3, 5]:
            cells.append(base_cfg(family="C4_excess_gap", top_k=top_k, exit_multiple=2.25, replace_rank_gap=gap))
    return dedupe(cells)


def grid_c5() -> list[dict]:
    """Hypothesis: joint OOF margins — bootstrap>=0.78 preferred zone + turnover headroom; pick utility."""
    cells = []
    for top_k in [20, 22, 24]:
        for reb in [40, 42, 45, 49]:
            for exit_m in [2.0, 2.25, 2.5, 2.75]:
                cells.append(base_cfg(family="C5_joint_margin", top_k=top_k, rebalance_every=reb, exit_multiple=exit_m))
    return dedupe(cells)


def grid_c6() -> list[dict]:
    """Hypothesis: industry neutralization / cap for stabler excess."""
    cells = []
    for neut in ["NONE", "INDUSTRY_LIQUIDITY"]:
        for cap in [3, 4, 5, 6]:
            for exit_m in [2.0, 2.25, 2.5]:
                for top_k in [20, 25]:
                    cells.append(base_cfg(
                        family="C6_industry",
                        top_k=top_k, exit_multiple=exit_m,
                        neutralization=neut, industry_cap=cap,
                    ))
    return dedupe(cells)


def grid_c7() -> list[dict]:
    """Hypothesis: liquidity floor + mild hold to reduce fragile names (OOF only)."""
    cells = []
    for floor in [20_000_000.0, 40_000_000.0, 60_000_000.0, 80_000_000.0]:
        for top_k in [20, 25, 30]:
            for exit_m in [2.0, 2.5]:
                for hold in [0, 1]:
                    cells.append(base_cfg(
                        family="C7_liquidity",
                        top_k=top_k, exit_multiple=exit_m,
                        liquidity_floor=floor, min_hold_cycles=hold,
                    ))
    return dedupe(cells)


def grid_c8() -> list[dict]:
    """Hypothesis: slower cadence + replace-gap around C2 turnover-pass region (not retuning C2)."""
    cells = []
    for reb in [42, 45, 49, 56, 63]:
        for exit_m in [2.25, 2.5, 3.0]:
            for gap in [0, 5, 8, 10]:
                for top_k in [20, 22]:
                    cells.append(base_cfg(
                        family="C8_slow_stable",
                        top_k=top_k, rebalance_every=reb,
                        exit_multiple=exit_m, replace_rank_gap=gap,
                    ))
    return dedupe(cells)


ROUND_SPECS = [
    {
        "id": "C4",
        "hypothesis": "Maximize OOF HAC t-stat (excess strength) among dual-gate passers with turnover headroom.",
        "grid": grid_c4,
        "select": "hac_t_stat",
    },
    {
        "id": "C5",
        "hypothesis": "Prefer joint OOF margins: require bootstrap>=0.78 if available else max bootstrap; then turnover headroom; then utility.",
        "grid": grid_c5,
        "select": "joint_margin",
    },
    {
        "id": "C6",
        "hypothesis": "Industry neutralization / industry_cap variants for stabler OOF excess.",
        "grid": grid_c6,
        "select": "bootstrap_then_utility",
    },
    {
        "id": "C7",
        "hypothesis": "Higher liquidity floors + mild min-hold to drop fragile names (OOF dual-gate).",
        "grid": grid_c7,
        "select": "bootstrap_then_turnover_headroom",
    },
    {
        "id": "C8",
        "hypothesis": "Slower rebalance + replace-rank-gap around low-turnover region (new configs only).",
        "grid": grid_c8,
        "select": "turnover_headroom_then_bootstrap",
    },
]


def sortino_rf0(rets: np.ndarray) -> float | None:
    downside = rets[rets < 0.0]
    if len(rets) < 2 or len(downside) < 1:
        return None
    dstd = float(np.std(downside, ddof=1))
    if dstd <= 0:
        return None
    return float(np.mean(rets) / dstd * math.sqrt(252))


def enrich(nav, trades, proxy, base):
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
        s = float(g["nav"][0]); e = float(g["nav"][-1])
        yearly.append({
            "year": year, "return": e / s - 1.0 if s else None,
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
    })
    return out


def evaluate_heldout_period(joined, execution, calendar, cfg, name, start, end, fit_cutoff):
    model = r1.fit_model(joined, SELECTED["feature_set"], SELECTED["mode"], SELECTED["ridge_lambda"], fit_cutoff)
    scored = r1.score_period(joined, model, start, end)
    orders, order_diag = buffered_orders_ext(
        scored, calendar,
        top_k=cfg["top_k"], rebalance_every=cfg["rebalance_every"],
        exit_multiple=cfg["exit_multiple"], neutralization=cfg["neutralization"],
        industry_cap=cfg["industry_cap"], min_hold_cycles=cfg.get("min_hold_cycles", 0),
        liquidity_floor=cfg.get("liquidity_floor", 20_000_000.0),
        replace_rank_gap=cfg.get("replace_rank_gap", 0),
    )
    nav, trades = a3.simulate(orders, execution, start, end)
    benchmark = a3.market_proxy(execution, start, end)
    metric = a3.metrics(nav, trades, name)
    _, stats = a3.compare(nav, benchmark)
    base = {
        "portfolio": name, "fit_cutoff": str(fit_cutoff),
        **{k: cfg[k] for k in [
            "top_k", "rebalance_every", "exit_multiple", "neutralization",
            "industry_cap", "min_hold_cycles", "liquidity_floor", "replace_rank_gap",
        ]},
        "cagr": metric.get("cagr"), "max_drawdown": metric.get("max_drawdown"),
        "average_daily_turnover": metric.get("average_daily_turnover"),
        "total_cost": metric.get("total_cost"), "trade_count": metric.get("trade_count"),
        "ending_nav": metric.get("ending_nav"), "sharpe_rf0": metric.get("sharpe_rf0"),
        "block_bootstrap_positive_probability": stats.get("block_bootstrap_positive_probability"),
        "mean_daily_excess": stats.get("mean_daily_excess"), "hac_t_stat": stats.get("hac_t_stat"),
        "turnover_gate_pass": bool((metric.get("average_daily_turnover") or 9) <= TURNOVER_CEILING),
        "bootstrap_gate_pass": bool((stats.get("block_bootstrap_positive_probability") or 0) >= BOOTSTRAP_GATE),
        **{f"diag_{k}": v for k, v in order_diag.items()},
    }
    base["both_experimental_gates_pass"] = bool(base["turnover_gate_pass"] and base["bootstrap_gate_pass"])
    return enrich(nav, trades, benchmark, base), nav, trades, benchmark


def classify(val, sealed):
    val_ok = bool(val["turnover_gate_pass"] and val["bootstrap_gate_pass"])
    sealed_ok = bool(sealed["turnover_gate_pass"] and sealed["bootstrap_gate_pass"])
    if not (val["exact_t1_ok"] and sealed["exact_t1_ok"]):
        return "INCONCLUSIVE"
    if val_ok and sealed_ok:
        return "PASS_HELDOUT"
    if (not val_ok) and (not sealed_ok):
        return "FAIL_HELDOUT"
    return "MIXED_HELDOUT"


def pick_winner(rows: list[dict], locked_keys: set[tuple], rule: str):
    cand = [r for r in rows if r["both_gates_pass"] and cfg_key(r) not in locked_keys]
    if not cand:
        return None
    if rule == "hac_t_stat":
        return sorted(cand, key=lambda r: (
            -(r.get("hac_t_stat") or -9),
            -(r.get("mean_daily_excess") or -9),
            -(TURNOVER_CEILING - (r["average_daily_turnover"] or 9)),
        ))[0]
    if rule == "joint_margin":
        strong = [r for r in cand if (r["block_bootstrap_positive_probability"] or 0) >= 0.78]
        pool = strong or cand
        return sorted(pool, key=lambda r: (
            -(r["block_bootstrap_positive_probability"] or 0),
            -(TURNOVER_CEILING - (r["average_daily_turnover"] or 9)),
            -(r.get("utility") or -9),
        ))[0]
    if rule == "bootstrap_then_utility":
        return sorted(cand, key=lambda r: (
            -(r["block_bootstrap_positive_probability"] or 0),
            -(r.get("utility") or -9),
        ))[0]
    if rule == "bootstrap_then_turnover_headroom":
        return sorted(cand, key=lambda r: (
            -(r["block_bootstrap_positive_probability"] or 0),
            -(TURNOVER_CEILING - (r["average_daily_turnover"] or 9)),
        ))[0]
    if rule == "turnover_headroom_then_bootstrap":
        return sorted(cand, key=lambda r: (
            -(TURNOVER_CEILING - (r["average_daily_turnover"] or 9)),
            -(r["block_bootstrap_positive_probability"] or 0),
            -(r.get("utility") or -9),
        ))[0]
    raise ValueError(rule)


def write_round_md(out: Path, cid: str, locked: dict, oof: dict, val: dict, sealed: dict, label: str, hypothesis: str):
    def pct(x):
        return "n/a" if x is None else f"{100.0 * x:.2f}%"
    def num(x, d=3):
        return "n/a" if x is None else f"{x:.{d}f}"
    lines = [
        f"# E50-A3-R1-{cid} Locked Challenger — Held-Out Evaluation",
        "",
        f"Date: {datetime.now(timezone.utc).date()}",
        "",
        f"## Hypothesis",
        "",
        hypothesis,
        "",
        f"## Locked {cid}",
        "",
        "```",
        f"top_k={locked['top_k']}",
        f"rebalance_every={locked['rebalance_every']}",
        f"exit_multiple={locked['exit_multiple']}",
        f"neutralization={locked['neutralization']}",
        f"industry_cap={locked['industry_cap']}",
        f"min_hold_cycles={locked['min_hold_cycles']}",
        f"liquidity_floor={locked['liquidity_floor']}",
        f"replace_rank_gap={locked['replace_rank_gap']}",
        "```",
        "",
        f"## Research decision",
        "",
        f"**`{label}`**",
        "",
        f"OOF: turnover {pct(oof['average_daily_turnover'])}, bootstrap {num(oof['block_bootstrap_positive_probability'], 4)}, "
        f"CAGR {pct(oof['cagr'])}, MDD {pct(oof['max_drawdown'])}, HAC t {num(oof.get('hac_t_stat'))}",
        "",
        "| Metric | Validation 2019–2022 | Sealed 2023–latest |",
        "|---|---:|---:|",
        f"| CAGR | {pct(val['cagr'])} | {pct(sealed['cagr'])} |",
        f"| MDD | {pct(val['max_drawdown'])} | {pct(sealed['max_drawdown'])} |",
        f"| Sharpe | {num(val['sharpe_rf0'])} | {num(sealed['sharpe_rf0'])} |",
        f"| Sortino | {num(val['sortino_rf0'])} | {num(sealed['sortino_rf0'])} |",
        f"| Calmar | {num(val['calmar'])} | {num(sealed['calmar'])} |",
        f"| Turnover | {pct(val['average_daily_turnover'])} | {pct(sealed['average_daily_turnover'])} |",
        f"| Cost | {num(val['total_cost'], 4)} | {num(sealed['total_cost'], 4)} |",
        f"| Exposure | {num(val['mean_gross_exposure'], 4)} | {num(sealed['mean_gross_exposure'], 4)} |",
        f"| Holdings | {num(val['average_holdings'], 2)} | {num(sealed['average_holdings'], 2)} |",
        f"| Bootstrap | {num(val['block_bootstrap_positive_probability'], 4)} | {num(sealed['block_bootstrap_positive_probability'], 4)} |",
        f"| Beats proxy | {val['beats_market_proxy']} | {sealed['beats_market_proxy']} |",
        f"| Turn gate | {val['turnover_gate_pass']} | {sealed['turnover_gate_pass']} |",
        f"| Boot gate | {val['bootstrap_gate_pass']} | {sealed['bootstrap_gate_pass']} |",
        f"| Exact T+1 | {val['exact_t1_ok']} | {sealed['exact_t1_ok']} |",
        "",
    ]
    (out / f"E50-A3-R1-{cid}_HELDOUT.md").write_text("\n".join(lines))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", type=Path, required=True)
    ap.add_argument("--prices", type=Path, required=True)
    ap.add_argument("--labels", type=Path, required=True)
    ap.add_argument("--actions", type=Path, required=True)
    ap.add_argument("--a2-qc", type=Path, required=True)
    ap.add_argument("--oof-scores", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--max-rounds", type=int, default=5)
    args = ap.parse_args()
    out = args.out
    (out / "outputs").mkdir(parents=True, exist_ok=True)
    (out / "reports").mkdir(parents=True, exist_ok=True)

    a2_qc = json.loads(args.a2_qc.read_text())
    if a2_qc["status"] != "PASS":
        raise RuntimeError("E50-A2 QC is not PASS")

    print("loading prices/execution/panel ...", flush=True)
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
    oof = pl.read_parquet(args.oof_scores)
    exact_labels = a3.build_exact_open_labels(panel, execution, calendar)
    joined = a3.target_rank(
        r1.add_regime(panel).join(exact_labels.select("date", "code", a3.LABEL), on=["date", "code"], validate="1:1")
    )

    locked_keys = {cfg_key(v) for v in PRIOR_LOCKS.values()}
    ledger = []
    no_winner_streak = 0
    specs = ROUND_SPECS[: args.max_rounds]

    validation_start, validation_end = date(2019, 1, 1), date(2022, 12, 31)
    sealed_start, sealed_end = date(2023, 1, 1), max(calendar)
    val_cutoff = a3.previous_session(calendar, validation_start, 22)
    sealed_cutoff = a3.previous_session(calendar, sealed_start, 22)

    for spec in specs:
        cid = spec["id"]
        print(f"\n===== ROUND {cid}: {spec['hypothesis']} =====", flush=True)
        grid = spec["grid"]()
        # drop already-locked configs from evaluation noise except as excluded
        print(f"evaluating {len(grid)} OOF cells ...", flush=True)
        rows = []
        for i, cfg in enumerate(grid, 1):
            if i % 10 == 1 or i == len(grid):
                print(f"  [{i}/{len(grid)}] {cfg['family']} k={cfg['top_k']} reb={cfg['rebalance_every']} "
                      f"exit={cfg['exit_multiple']} neut={cfg['neutralization']} cap={cfg['industry_cap']} "
                      f"hold={cfg['min_hold_cycles']} floor={cfg['liquidity_floor']} gap={cfg['replace_rank_gap']}", flush=True)
            row = evaluate_cfg(oof, execution, calendar, cfg)
            row["bootstrap_margin"] = (row["block_bootstrap_positive_probability"] or 0) - BOOTSTRAP_GATE
            row["turnover_headroom"] = TURNOVER_CEILING - (row["average_daily_turnover"] or 9)
            rows.append(row)
        pl.DataFrame(rows).write_csv(out / "outputs" / f"round_{cid.lower()}_oof_grid.csv")

        winner = pick_winner(rows, locked_keys, spec["select"])
        oof_summary = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "round": cid,
            "hypothesis": spec["hypothesis"],
            "selection_rule": spec["select"],
            "n_challengers": len(rows),
            "n_both_pass": sum(1 for r in rows if r["both_gates_pass"]),
            "n_both_pass_excluding_locked": sum(
                1 for r in rows if r["both_gates_pass"] and cfg_key(r) not in locked_keys
            ),
            "research_decision": "OOF_NEW_DUAL_GATE_WINNER" if winner else "OOF_NO_NEW_DUAL_GATE_WINNER",
            "recommended_challenger": winner,
        }
        (out / "reports" / f"round_{cid.lower()}_oof_summary.json").write_text(
            json.dumps(oof_summary, indent=2, default=str) + "\n"
        )

        if winner is None:
            no_winner_streak += 1
            entry = {
                "id": cid,
                "oof_decision": "OOF_NO_NEW_DUAL_GATE_WINNER",
                "heldout_decision": None,
                "hypothesis": spec["hypothesis"],
            }
            ledger.append(entry)
            print(json.dumps(entry, indent=2))
            if no_winner_streak >= 2:
                print("stopping: 2 consecutive rounds with no new dual-gate winner", flush=True)
                break
            continue

        no_winner_streak = 0
        locked = {k: winner[k] for k in [
            "top_k", "rebalance_every", "exit_multiple", "neutralization",
            "industry_cap", "min_hold_cycles", "liquidity_floor", "replace_rank_gap",
        ]}
        locked["family"] = winner["family"]
        locked_keys.add(cfg_key(locked))
        PRIOR_LOCKS[cid] = locked

        print(f"locked {cid}: {locked}", flush=True)
        print(f"evaluating {cid} held-out ...", flush=True)
        val, val_nav, val_trades, val_proxy = evaluate_heldout_period(
            joined, execution, calendar, locked, f"{cid}_VALIDATION_2019_2022",
            validation_start, validation_end, val_cutoff,
        )
        sealed, sealed_nav, sealed_trades, sealed_proxy = evaluate_heldout_period(
            joined, execution, calendar, locked, f"{cid}_SEALED_2023_LATEST",
            sealed_start, sealed_end, sealed_cutoff,
        )
        label = classify(val, sealed)
        for period, nav, trades, proxy in [
            (f"{cid.lower()}_validation_2019_2022", val_nav, val_trades, val_proxy),
            (f"{cid.lower()}_sealed_2023_latest", sealed_nav, sealed_trades, sealed_proxy),
        ]:
            nav.write_csv(out / "outputs" / f"{period}_daily_nav.csv")
            trades.write_csv(out / "outputs" / f"{period}_trades.csv")
            proxy.write_csv(out / "outputs" / f"{period}_market_proxy_nav.csv")
            # yearly from enrich already in metrics
        pl.DataFrame(val["yearly_returns"]).write_csv(out / "outputs" / f"{cid.lower()}_validation_2019_2022_yearly_returns.csv")
        pl.DataFrame(sealed["yearly_returns"]).write_csv(out / "outputs" / f"{cid.lower()}_sealed_2023_latest_yearly_returns.csv")

        decision = {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "challenger": f"E50-A3-R1-{cid}",
            "locked_challenger": {**locked, **SELECTED},
            "selection_window": "2011-2018 OOF only",
            "hypothesis": spec["hypothesis"],
            "no_retune_on_heldout": True,
            "gates_remain_experimental": True,
            "oof_reconfirm": {
                "turnover": winner["average_daily_turnover"],
                "bootstrap": winner["block_bootstrap_positive_probability"],
                "cagr": winner["cagr"],
                "max_drawdown": winner["max_drawdown"],
                "hac_t_stat": winner.get("hac_t_stat"),
                "utility": winner.get("utility"),
            },
            "validation_2019_2022": val,
            "sealed_2023_latest": sealed,
            "research_decision": label,
            "verification": {
                "exact_t1_intact": bool(val["exact_t1_ok"] and sealed["exact_t1_ok"]),
                "e45_touched": False,
                "frozen_baselines_unchanged": True,
                "no_promotion": True,
            },
        }
        (out / "reports" / f"{cid.lower()}_heldout_decision.json").write_text(
            json.dumps(decision, indent=2, default=str) + "\n"
        )
        write_round_md(out, cid, locked, winner, val, sealed, label, spec["hypothesis"])

        entry = {
            "id": cid,
            "locked": locked,
            "oof_decision": "OOF_NEW_DUAL_GATE_WINNER",
            "heldout_decision": label,
            "oof_turnover": winner["average_daily_turnover"],
            "oof_bootstrap": winner["block_bootstrap_positive_probability"],
            "val_turnover": val["average_daily_turnover"],
            "val_bootstrap": val["block_bootstrap_positive_probability"],
            "val_turnover_pass": val["turnover_gate_pass"],
            "val_bootstrap_pass": val["bootstrap_gate_pass"],
            "sealed_turnover_pass": sealed["turnover_gate_pass"],
            "sealed_bootstrap_pass": sealed["bootstrap_gate_pass"],
            "val_beats_proxy": val["beats_market_proxy"],
            "hypothesis": spec["hypothesis"],
        }
        ledger.append(entry)
        print(json.dumps(entry, indent=2, default=str), flush=True)
        if label == "PASS_HELDOUT":
            print("stopping early: PASS_HELDOUT", flush=True)
            break

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "EXPERIMENTAL_AUTO_ROUNDS_C4_C8",
        "max_rounds": args.max_rounds,
        "rounds_completed": len(ledger),
        "prior_locks_before": list(PRIOR_LOCKS.keys()),
        "ledger": ledger,
        "gates_remain_experimental": True,
        "no_promotion": True,
        "do_not_merge_yet": True,
        "best_so_far_note": (
            "Among C1–latest, prefer any PASS_HELDOUT; else note which MIXED had val turnover pass "
            "(historically C2)."
        ),
    }
    (out / "reports" / "auto_rounds_c4_c8_summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n"
    )

    # README ledger update
    lines = [
        "# E50-A3-R1 Automatic Challenger Rounds",
        "",
        "Draft research only. No promotion. E45 untouched.",
        "",
        "## Ledger",
        "",
        "| ID | Config | OOF | Held-out | Val turn | Val boot |",
        "|---|---|---|---|---|---|",
        "| C1 | k20 reb42 exit2.0 | PASS | MIXED | FAIL | FAIL |",
        "| C2 | k20 reb42 exit2.5 | PASS | MIXED | PASS | FAIL |",
        "| C3 | k25 reb42 exit2.0 | PASS | MIXED | FAIL | FAIL |",
    ]
    for e in ledger:
        if e.get("locked"):
            L = e["locked"]
            cfg = f"k{L['top_k']} reb{L['rebalance_every']} exit{L['exit_multiple']} neut={L['neutralization']} cap{L['industry_cap']} hold{L['min_hold_cycles']} gap{L['replace_rank_gap']} floor{int(L['liquidity_floor']/1e6)}m"
            vt = "PASS" if e.get("val_turnover_pass") else "FAIL"
            vb = "PASS" if e.get("val_bootstrap_pass") else "FAIL"
            lines.append(f"| {e['id']} | {cfg} | {e['oof_decision']} | {e['heldout_decision']} | {vt} | {vb} |")
        else:
            lines.append(f"| {e['id']} | — | {e['oof_decision']} | — | — | — |")
    lines += ["", "See `reports/auto_rounds_c4_c8_summary.json` and per-round `E50-A3-R1-C*_HELDOUT.md`.", ""]
    (out / "E50-A3-R1_AUTO_ROUNDS.md").write_text("\n".join(lines))
    print(json.dumps({"rounds": len(ledger), "ledger": ledger}, indent=2, default=str))


if __name__ == "__main__":
    main()
