#!/usr/bin/env python3
"""E50-A3-R1 Round-3 OOF challenger screen (EXPERIMENTAL).

Hypothesis: among dual-gate OOF passers, prioritize higher block-bootstrap
positive probability (excess stability margin) while keeping turnover <= 2.5%
with some headroom. Round-2 preferred lowest turnover and left higher-bootstrap
book-size cells unused for held-out.

Rules:
- Selection window: 2011-2018 OOF only
- Exclude locked C1 and C2 configs (already held-out once each)
- Same TECH2 / BREADTH_REGIME / lambda=1.0 scores
- Does not modify E16/E18/E22/E44/E45
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e50a3_train_exact_open as a3
from e50a3r1_turnover_diagnosis import (
    BOOTSTRAP_GATE,
    SELECTED,
    TURNOVER_CEILING,
    evaluate_cfg,
)

C1_LOCKED = {
    "top_k": 20, "rebalance_every": 42, "exit_multiple": 2.0,
    "neutralization": "NONE", "industry_cap": 5, "min_hold_cycles": 0,
    "liquidity_floor": 20_000_000.0, "replace_rank_gap": 0,
}
C2_LOCKED = {
    "top_k": 20, "rebalance_every": 42, "exit_multiple": 2.5,
    "neutralization": "NONE", "industry_cap": 5, "min_hold_cycles": 0,
    "liquidity_floor": 20_000_000.0, "replace_rank_gap": 0,
}


def cfg_key(cfg: dict) -> tuple:
    return (
        cfg["top_k"], cfg["rebalance_every"], float(cfg["exit_multiple"]),
        cfg["neutralization"], cfg["industry_cap"], cfg["min_hold_cycles"],
        float(cfg["liquidity_floor"]), cfg["replace_rank_gap"],
    )


def is_prior_locked(cfg: dict) -> bool:
    k = cfg_key(cfg)
    return k in {cfg_key(C1_LOCKED), cfg_key(C2_LOCKED)}


def round3_grid() -> list[dict]:
    cells: list[dict] = []

    def add(family: str, **kwargs) -> None:
        base = {
            "family": family,
            "top_k": 25,
            "rebalance_every": 42,
            "exit_multiple": 2.0,
            "neutralization": "NONE",
            "industry_cap": 5,
            "min_hold_cycles": 0,
            "liquidity_floor": 20_000_000.0,
            "replace_rank_gap": 0,
        }
        base.update(kwargs)
        cells.append(base)

    # Book-size neighborhood (Round-2 high-bootstrap region).
    for top_k in [22, 24, 25, 28, 30]:
        for exit_m in [2.0, 2.25, 2.5]:
            for gap in [0, 5]:
                add("C3_book_bootstrap", top_k=top_k, exit_multiple=exit_m, replace_rank_gap=gap)

    # Rebalance neighborhood at top_k=25.
    for reb in [35, 40, 42, 45, 49]:
        for exit_m in [2.0, 2.25]:
            add("C3_reb_bootstrap", top_k=25, rebalance_every=reb, exit_multiple=exit_m)

    # Mild min-hold at high-bootstrap corner.
    for hold in [1, 2]:
        for top_k in [25, 28]:
            add("C3_minhold_bootstrap", top_k=top_k, exit_multiple=2.0, min_hold_cycles=hold)

    # Industry cap stress at top_k=25.
    for cap in [4, 6]:
        add("C3_industry_cap", top_k=25, industry_cap=cap, exit_multiple=2.0)

    # Keep C1/C2 as reference rows (excluded from winner).
    add("C1_REFERENCE", **C1_LOCKED)
    add("C2_REFERENCE", **C2_LOCKED)

    uniq: dict[tuple, dict] = {}
    for c in cells:
        uniq[cfg_key(c)] = c
    return list(uniq.values())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", type=Path, required=True)
    ap.add_argument("--prices", type=Path, required=True)
    ap.add_argument("--labels", type=Path, required=True)
    ap.add_argument("--actions", type=Path, required=True)
    ap.add_argument("--a2-qc", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--oof-scores", type=Path, required=True)
    args = ap.parse_args()
    out = args.out
    (out / "outputs").mkdir(parents=True, exist_ok=True)
    (out / "reports").mkdir(parents=True, exist_ok=True)

    a2_qc = json.loads(args.a2_qc.read_text())
    if a2_qc["status"] != "PASS":
        raise RuntimeError("E50-A2 QC is not PASS")

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
    oof = pl.read_parquet(args.oof_scores)

    grid = round3_grid()
    print(f"evaluating {len(grid)} Round-3 OOF challengers ...", flush=True)
    rows = []
    for i, cfg in enumerate(grid, 1):
        print(
            f"[{i}/{len(grid)}] {cfg['family']} top_k={cfg['top_k']} reb={cfg['rebalance_every']} "
            f"exit={cfg['exit_multiple']} hold={cfg['min_hold_cycles']} gap={cfg['replace_rank_gap']} "
            f"cap={cfg['industry_cap']}",
            flush=True,
        )
        row = evaluate_cfg(oof, execution, calendar, cfg)
        row["is_prior_locked"] = is_prior_locked(cfg)
        row["feature_set"] = SELECTED["feature_set"]
        row["mode"] = SELECTED["mode"]
        row["ridge_lambda"] = SELECTED["ridge_lambda"]
        # Bootstrap margin above experimental gate.
        row["bootstrap_margin"] = (row["block_bootstrap_positive_probability"] or 0) - BOOTSTRAP_GATE
        row["turnover_headroom"] = TURNOVER_CEILING - (row["average_daily_turnover"] or 9)
        rows.append(row)

    result = pl.DataFrame(rows).sort(
        ["both_gates_pass", "block_bootstrap_positive_probability", "turnover_headroom"],
        descending=[True, True, True],
    )
    result.write_csv(out / "outputs" / "round3_oof_challenger_grid.csv")

    both_new = [r for r in rows if r["both_gates_pass"] and not r["is_prior_locked"]]
    # Prefer higher bootstrap, then more turnover headroom, then utility.
    both_new_sorted = sorted(
        both_new,
        key=lambda r: (
            -(r["block_bootstrap_positive_probability"] or 0),
            -(r["turnover_headroom"] or -9),
            -(r.get("utility") or -9),
        ),
    )
    c1 = next(r for r in rows if cfg_key(r) == cfg_key(C1_LOCKED))
    c2 = next(r for r in rows if cfg_key(r) == cfg_key(C2_LOCKED))

    if both_new_sorted:
        winner = both_new_sorted[0]
        decision = "OOF_NEW_DUAL_GATE_WINNER"
    else:
        winner = None
        decision = "OOF_NO_NEW_DUAL_GATE_WINNER"

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "round": "E50-A3-R1-C3",
        "window": "2011-01-01 to 2018-12-31 OOF only",
        "no_2019_plus_selection": True,
        "hypothesis": (
            "Maximize OOF bootstrap margin among dual-gate passers with turnover headroom; "
            "explore book-size neighborhood left unused by Round-2 turnover-first rule."
        ),
        "selection_rule": (
            "Exclude C1/C2. Among NEW dual-gate passers: max bootstrap, then max turnover "
            "headroom vs 2.5%, then utility."
        ),
        "model_locked": SELECTED,
        "excluded_locked": {"C1": C1_LOCKED, "C2": C2_LOCKED},
        "c1_oof_reconfirm": {
            "turnover": c1["average_daily_turnover"],
            "bootstrap": c1["block_bootstrap_positive_probability"],
        },
        "c2_oof_reconfirm": {
            "turnover": c2["average_daily_turnover"],
            "bootstrap": c2["block_bootstrap_positive_probability"],
        },
        "n_challengers": len(rows),
        "n_turnover_pass": sum(1 for r in rows if r["turnover_gate_pass"]),
        "n_bootstrap_pass": sum(1 for r in rows if r["bootstrap_gate_pass"]),
        "n_both_pass": sum(1 for r in rows if r["both_gates_pass"]),
        "n_both_pass_excluding_locked": len(both_new),
        "gates": {"turnover_ceiling": TURNOVER_CEILING, "bootstrap_gate": BOOTSTRAP_GATE},
        "gates_remain_experimental": True,
        "research_decision": decision,
        "recommended_challenger": winner,
        "top_new_dual_gate_by_bootstrap": both_new_sorted[:10],
    }
    (out / "reports" / "round3_oof_summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n"
    )
    print(json.dumps({
        "research_decision": decision,
        "n_both_pass_excluding_locked": len(both_new),
        "winner": None if winner is None else {
            "family": winner["family"],
            "top_k": winner["top_k"],
            "rebalance_every": winner["rebalance_every"],
            "exit_multiple": winner["exit_multiple"],
            "industry_cap": winner["industry_cap"],
            "min_hold_cycles": winner["min_hold_cycles"],
            "replace_rank_gap": winner["replace_rank_gap"],
            "turnover": winner["average_daily_turnover"],
            "bootstrap": winner["block_bootstrap_positive_probability"],
            "bootstrap_margin": winner["bootstrap_margin"],
            "turnover_headroom": winner["turnover_headroom"],
            "cagr": winner["cagr"],
            "max_drawdown": winner["max_drawdown"],
        },
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
