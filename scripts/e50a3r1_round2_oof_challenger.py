#!/usr/bin/env python3
"""E50-A3-R1 Round-2 OOF challenger screen (EXPERIMENTAL).

Hypothesis: around locked C1 (top_k=20, reb=42, exit=2.0), add mild
min-hold / replace-gap / slight rebalance-buffer changes to create OOF
turnover headroom while keeping bootstrap >= 0.70.

Rules:
- Selection window: 2011-2018 OOF only
- Do NOT retune locked C1 from held-out evidence
- C1 is reference only; a NEW dual-gate winner is required to proceed
- Same TECH2 / BREADTH_REGIME / lambda=1.0 scores (no model retune)
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
import e50a3r1_repair as r1
from e50a3r1_turnover_diagnosis import (
    BOOTSTRAP_GATE,
    SELECTED,
    TURNOVER_CEILING,
    build_oof_scores,
    evaluate_cfg,
)

# Locked Round-1 challenger — reference only; do not re-select as "new".
C1_LOCKED = {
    "top_k": 20,
    "rebalance_every": 42,
    "exit_multiple": 2.0,
    "neutralization": "NONE",
    "industry_cap": 5,
    "min_hold_cycles": 0,
    "liquidity_floor": 20_000_000.0,
    "replace_rank_gap": 0,
}


def cfg_key(cfg: dict) -> tuple:
    return (
        cfg["top_k"],
        cfg["rebalance_every"],
        float(cfg["exit_multiple"]),
        cfg["neutralization"],
        cfg["industry_cap"],
        cfg["min_hold_cycles"],
        float(cfg["liquidity_floor"]),
        cfg["replace_rank_gap"],
    )


def round2_grid() -> list[dict]:
    cells: list[dict] = []

    def add(family: str, **kwargs) -> None:
        base = {
            "family": family,
            "top_k": 20,
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

    # C1 reference (already held-out once).
    add("C1_REFERENCE", **C1_LOCKED)

    # Exit buffer + min-hold around reb=42 / top_k=20.
    for exit_m in [2.0, 2.25, 2.5, 3.0]:
        for hold in [0, 1, 2]:
            add(
                "C2_exit_minhold",
                exit_multiple=exit_m,
                min_hold_cycles=hold,
            )

    # Replace-rank gap at C1 corner and mild exit widen.
    for gap in [3, 5, 8]:
        for exit_m in [2.0, 2.5]:
            for hold in [0, 1]:
                add(
                    "C2_replace_gap",
                    exit_multiple=exit_m,
                    min_hold_cycles=hold,
                    replace_rank_gap=gap,
                )

    # Rebalance neighborhood (not held-out retune of 42 — OOF search only).
    for reb in [35, 40, 45, 49, 56]:
        for exit_m in [2.0, 2.5]:
            for hold in [0, 1]:
                add(
                    "C2_reb_neighborhood",
                    rebalance_every=reb,
                    exit_multiple=exit_m,
                    min_hold_cycles=hold,
                )

    # Slightly larger book with stability.
    for top_k in [25, 30]:
        for hold in [0, 1]:
            for gap in [0, 5]:
                add(
                    "C2_book_size",
                    top_k=top_k,
                    exit_multiple=2.0,
                    min_hold_cycles=hold,
                    replace_rank_gap=gap,
                )

    # Combined mild stabilizer (exit 2.5 + hold 1 + gap 5) across reb neighborhood.
    for reb in [42, 45, 49]:
        add(
            "C2_combined_stabilizer",
            rebalance_every=reb,
            exit_multiple=2.5,
            min_hold_cycles=1,
            replace_rank_gap=5,
        )

    uniq: dict[tuple, dict] = {}
    for c in cells:
        uniq[cfg_key(c)] = c
    return list(uniq.values())


def is_c1(cfg: dict) -> bool:
    return cfg_key(cfg) == cfg_key(C1_LOCKED)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", type=Path, required=True)
    ap.add_argument("--prices", type=Path, required=True)
    ap.add_argument("--labels", type=Path, required=True)
    ap.add_argument("--actions", type=Path, required=True)
    ap.add_argument("--a2-qc", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--oof-scores", type=Path, default=None)
    args = ap.parse_args()
    out = args.out
    (out / "outputs").mkdir(parents=True, exist_ok=True)
    (out / "reports").mkdir(parents=True, exist_ok=True)

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

    oof_path = args.oof_scores or (out / "outputs" / "oof_scores_selected_model.parquet")
    if oof_path.exists():
        print(f"loading existing OOF scores from {oof_path} ...", flush=True)
        oof = pl.read_parquet(oof_path)
    else:
        print("building OOF scores ...", flush=True)
        exact_labels = a3.build_exact_open_labels(panel, execution, calendar)
        joined = a3.target_rank(
            r1.add_regime(panel).join(
                exact_labels.select("date", "code", a3.LABEL), on=["date", "code"], validate="1:1"
            )
        )
        oof = build_oof_scores(joined, calendar)
        oof.write_parquet(out / "outputs" / "oof_scores_selected_model.parquet", compression="zstd")

    grid = round2_grid()
    print(f"evaluating {len(grid)} Round-2 OOF challengers ...", flush=True)
    rows = []
    for i, cfg in enumerate(grid, 1):
        print(
            f"[{i}/{len(grid)}] {cfg['family']} top_k={cfg['top_k']} reb={cfg['rebalance_every']} "
            f"exit={cfg['exit_multiple']} hold={cfg['min_hold_cycles']} gap={cfg['replace_rank_gap']}",
            flush=True,
        )
        row = evaluate_cfg(oof, execution, calendar, cfg)
        row["is_c1_reference"] = is_c1(cfg)
        row["feature_set"] = SELECTED["feature_set"]
        row["mode"] = SELECTED["mode"]
        row["ridge_lambda"] = SELECTED["ridge_lambda"]
        rows.append(row)

    result = pl.DataFrame(rows).sort(
        ["both_gates_pass", "average_daily_turnover", "block_bootstrap_positive_probability"],
        descending=[True, False, True],
    )
    result.write_csv(out / "outputs" / "round2_oof_challenger_grid.csv")

    both = [r for r in rows if r["both_gates_pass"]]
    both_new = [r for r in both if not r["is_c1_reference"]]
    # Prefer more turnover headroom (lower OOF turnover), then higher bootstrap, then utility.
    both_new_sorted = sorted(
        both_new,
        key=lambda r: (
            r["average_daily_turnover"],
            -(r["block_bootstrap_positive_probability"] or 0),
            -(r.get("utility") or -9),
        ),
    )
    c1_row = next(r for r in rows if r["is_c1_reference"])

    if both_new_sorted:
        winner = both_new_sorted[0]
        decision = "OOF_NEW_DUAL_GATE_WINNER"
    else:
        winner = None
        decision = "OOF_NO_NEW_DUAL_GATE_WINNER"

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "round": "E50-A3-R1-C2",
        "window": "2011-01-01 to 2018-12-31 OOF only",
        "no_2019_plus_selection": True,
        "model_locked": SELECTED,
        "c1_reference_locked": C1_LOCKED,
        "c1_oof_reconfirm": {
            "turnover": c1_row["average_daily_turnover"],
            "bootstrap": c1_row["block_bootstrap_positive_probability"],
            "both_gates_pass": c1_row["both_gates_pass"],
            "cagr": c1_row["cagr"],
            "max_drawdown": c1_row["max_drawdown"],
        },
        "n_challengers": len(rows),
        "n_turnover_pass": sum(1 for r in rows if r["turnover_gate_pass"]),
        "n_bootstrap_pass": sum(1 for r in rows if r["bootstrap_gate_pass"]),
        "n_both_pass": len(both),
        "n_both_pass_excluding_c1": len(both_new),
        "gates": {"turnover_ceiling": TURNOVER_CEILING, "bootstrap_gate": BOOTSTRAP_GATE},
        "gates_remain_experimental": True,
        "research_decision": decision,
        "recommended_challenger": winner,
        "all_new_dual_gate_winners": both_new_sorted[:10],
        "selection_rule": (
            "Among NEW (non-C1) OOF dual-gate passers, prefer lower average_daily_turnover "
            "(headroom vs 2.5%), then higher bootstrap, then higher utility. "
            "C1 remains held-out-exhausted and must not be retuned."
        ),
        "next_step": (
            "If OOF_NEW_DUAL_GATE_WINNER: lock C2 and run held-out once on 2019-2022 and 2023-latest. "
            "If OOF_NO_NEW_DUAL_GATE_WINNER: stop; do not inspect held-out for failed OOF cells; "
            "design a different hypothesis (still OOF-only)."
        ),
    }
    (out / "reports" / "round2_oof_summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n"
    )
    print(json.dumps({
        "research_decision": decision,
        "n_both_pass_excluding_c1": len(both_new),
        "winner": None if winner is None else {
            "family": winner["family"],
            "top_k": winner["top_k"],
            "rebalance_every": winner["rebalance_every"],
            "exit_multiple": winner["exit_multiple"],
            "min_hold_cycles": winner["min_hold_cycles"],
            "replace_rank_gap": winner["replace_rank_gap"],
            "turnover": winner["average_daily_turnover"],
            "bootstrap": winner["block_bootstrap_positive_probability"],
            "cagr": winner["cagr"],
            "max_drawdown": winner["max_drawdown"],
        },
        "c1_turnover": c1_row["average_daily_turnover"],
        "c1_bootstrap": c1_row["block_bootstrap_positive_probability"],
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
