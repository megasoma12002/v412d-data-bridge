#!/usr/bin/env python3
"""Stage-9A OOF: E45-C1 freeze / orthogonal-defensive controllers (EXPERIMENTAL).

After Stage-8C sleeve/cash saturation. Not an in-place E45 edit.
Bull sleeve remains TECH2+C4. New controller classes:
  - FREEZE_REB: skip C4 rebalance dates while stress detector is on
  - ORTH_DEF: switch to defensive residualized vs momentum_family
  - ORTH_DEF_FREEZE: combine both

Detectors: relative rolling/combo from Stage-8C (share band 5–40%).
Pass: dual gates + util >= BASE-0.005 + (stress_comp > BASE or MDD strictly better).
Selection: 2011–2018 OOF only. No retune of prior locks.
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
from e50a3r1_stage6_risk_overlay_oof import C4, mean_gross_exposure
from e50a3r1_stage7_crisis_challenger_oof import (
    merge_orders_crisis_sleeve,
    orders_on_dates,
    period_metrics,
)
from e50a3r1_stage8c_multisleeve_oof import (
    MIN_STRESS_SHARE,
    MAX_STRESS_SHARE,
    UTIL_SLACK,
    build_oof_state,
    detector_map,
)

# Prefer detectors that passed share band in 8C and are relative
PREFERRED_DETECTORS = [
    "VOL_ROLLP70_NONCRISIS",
    "VOL_ROLLP80_NONCRISIS",
    "COMBO_VOL70_VAL03",
    "COMBO_VOL80_VAL05",
    "ALPHA_STRESS_RISKON_MOMWEAK",
]


def build_orth_def_scores(panel: pl.DataFrame) -> pl.DataFrame:
    """Cross-sectional residual: defensive ~ momentum, take residual (+ low vol)."""
    d = panel.filter(pl.col("date").is_between(OOF_START, OOF_END)).select(
        "date", "code", "industry_category", "trading_money", "unexplained_price_jump",
        "defensive_family_score", "momentum_family_score", "pct_vol_60d",
    )
    pieces = []
    for (day,), g in d.partition_by("date", as_dict=True).items():
        gg = g.drop_nulls(["defensive_family_score", "momentum_family_score"])
        if gg.height < 30:
            continue
        y = gg["defensive_family_score"].to_numpy()
        x = gg["momentum_family_score"].to_numpy()
        x = x - x.mean()
        denom = float(np.dot(x, x))
        beta = float(np.dot(x, y - y.mean()) / denom) if denom > 1e-12 else 0.0
        resid = y - (y.mean() + beta * x)
        out = gg.with_columns(pl.Series("resid", resid))
        out = out.with_columns(
            (
                pl.col("resid")
                - 0.25 * pl.col("pct_vol_60d").fill_null(0.5)
            ).alias("score")
        )
        pieces.append(out.select(
            "date", "code", "industry_category", "trading_money", "unexplained_price_jump", "score"
        ))
    return pl.concat(pieces).sort(["date", "code"]) if pieces else d.head(0)


def freeze_signal_dates(scored: pl.DataFrame, flags: dict[date, bool], every: int) -> list[date]:
    pool = sorted(scored["date"].unique().to_list())
    base = pool[::every]
    # Always keep first rebalance so book is seeded
    out = []
    for i, d in enumerate(base):
        if i == 0 or not flags.get(d, False):
            out.append(d)
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

    print("building OOF state / detectors ...", flush=True)
    state = build_oof_state(panel, labels, execution)
    detectors = detector_map(state)

    print("building BASE C4 + ORTH_DEF sleeve ...", flush=True)
    tech_orders, _ = buffered_orders_ext(scored, calendar, **C4)
    orth_scores = build_orth_def_scores(panel)
    orth_orders, _ = buffered_orders_ext(orth_scores, calendar, **C4)

    rows = []
    for det_name in PREFERRED_DETECTORS:
        flags = detectors[det_name]
        stress_dates = {d for d, on in flags.items() if on}
        share = len(stress_dates) / max(state.height, 1)
        print(f"detector {det_name}: stress_days={len(stress_dates)} ({100*share:.1f}%)", flush=True)
        if share < MIN_STRESS_SHARE or share > MAX_STRESS_SHARE:
            print("  skip share band", flush=True)
            continue

        base = evaluate(tech_orders, execution, f"BASE::{det_name}", stress_dates)
        base.update({"detector": det_name, "is_baseline": True, "controller": "BASE_FULL", "stress_day_share": share})
        rows.append(base)

        # FREEZE_REB: skip rebalances on stress days
        freeze_dates = freeze_signal_dates(scored, flags, C4["rebalance_every"])
        freeze_orders = orders_on_dates(scored, calendar, freeze_dates, C4)
        m = evaluate(freeze_orders, execution, f"FREEZE_REB::{det_name}", stress_dates)
        m.update({"detector": det_name, "is_baseline": False, "controller": "FREEZE_REB", "stress_day_share": share})
        rows.append(m)
        print(f"  FREEZE_REB: util={m['utility']:.4f} boot={m['block_bootstrap_positive_probability']} "
              f"mdd={m['max_drawdown']:.4f} stress_ex={m['s_crisis_mean_excess']} both={m['both_gates_pass']}", flush=True)

        # ORTH_DEF sleeve switch
        sleeve = merge_orders_crisis_sleeve(tech_orders, orth_orders, flags)
        m = evaluate(sleeve, execution, f"ORTH_DEF::{det_name}", stress_dates)
        m.update({"detector": det_name, "is_baseline": False, "controller": "ORTH_DEF", "stress_day_share": share})
        rows.append(m)
        print(f"  ORTH_DEF: util={m['utility']:.4f} boot={m['block_bootstrap_positive_probability']} "
              f"mdd={m['max_drawdown']:.4f} stress_ex={m['s_crisis_mean_excess']} both={m['both_gates_pass']}", flush=True)

        # ORTH_DEF on freeze cadence
        freeze_orth_dates = freeze_signal_dates(orth_scores, flags, C4["rebalance_every"])
        # Use tech freeze dates for bull days; on stress use last orth book via merge on freeze set
        # Practical: merge full orth/tech then rebuild on freeze dates only from scored books
        bull_f = orders_on_dates(scored, calendar, freeze_dates, C4)
        orth_f = orders_on_dates(orth_scores, calendar, freeze_orth_dates, C4)
        combo = merge_orders_crisis_sleeve(bull_f, orth_f, flags)
        m = evaluate(combo, execution, f"ORTH_DEF_FREEZE::{det_name}", stress_dates)
        m.update({"detector": det_name, "is_baseline": False, "controller": "ORTH_DEF_FREEZE", "stress_day_share": share})
        rows.append(m)
        print(f"  ORTH_DEF_FREEZE: util={m['utility']:.4f} boot={m['block_bootstrap_positive_probability']} "
              f"mdd={m['max_drawdown']:.4f} stress_ex={m['s_crisis_mean_excess']} both={m['both_gates_pass']}", flush=True)

    pl.DataFrame(rows).write_csv(out / "outputs" / "stage9a_e45c1_freeze_orth_oof_grid.csv")

    candidates = []
    for tag in sorted(set(r["detector"] for r in rows)):
        base = next(r for r in rows if r["detector"] == tag and r["is_baseline"])
        for r in rows:
            if r["detector"] != tag or r["is_baseline"]:
                continue
            if not r["both_gates_pass"]:
                continue
            util_ok = (r["utility"] or -9) >= (base["utility"] or -9) - UTIL_SLACK
            scomp, bcomp = r["s_crisis_strategy_compound"], base["s_crisis_strategy_compound"]
            sex, bex = r["s_crisis_mean_excess"], base["s_crisis_mean_excess"]
            stress_ok = (
                (sex is not None and bex is not None and sex > bex + 1e-12)
                or (scomp is not None and bcomp is not None and scomp > bcomp + 1e-12)
            )
            mdd_ok = abs(r["max_drawdown"] or 9) + 1e-12 < abs(base["max_drawdown"] or 9)
            if util_ok and (stress_ok or mdd_ok):
                candidates.append({**r, "base_utility": base["utility"], "base_mdd": base["max_drawdown"],
                                   "base_stress_ex": bex, "base_stress_comp": bcomp,
                                   "pass_via_stress": stress_ok, "pass_via_mdd": mdd_ok})

    candidates = sorted(
        candidates,
        key=lambda r: (
            -(r["s_crisis_strategy_compound"] or -9),
            abs(r["max_drawdown"] or 9),
            -(r["utility"] or -9),
        ),
    )
    winner = candidates[0] if candidates else None
    decision = (
        "OOF_NEW_E45C1_CONTROLLER_DUAL_GATE_WINNER"
        if winner
        else "OOF_NO_NEW_E45C1_CONTROLLER_DUAL_GATE_WINNER"
    )

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "STAGE9A_E45C1_FREEZE_ORTH_OOF",
        "window": "2011-2018 OOF only",
        "e45_touched": False,
        "e45_inplace_edit": False,
        "challenger_track": "E45-C1",
        "n_rows": len(rows),
        "n_candidates": len(candidates),
        "research_decision": decision,
        "recommended": winner,
        "top_candidates": candidates[:8],
        "gates_remain_experimental": True,
        "stop_grid_if_no_winner": True,
    }
    (out / "reports" / "stage9a_e45c1_freeze_orth_oof_summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n"
    )

    lines = [
        "# Stage-9A E45-C1 Freeze / Orth-Def OOF",
        "",
        "Separate E45-C1 track. Controllers: FREEZE_REB, ORTH_DEF, ORTH_DEF_FREEZE.",
        "",
        f"## Decision: `{decision}`",
        "",
        "| controller | detector | util | boot | mdd | stress_ex | stress_ret | both |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    show = sorted(rows, key=lambda r: (-(r["both_gates_pass"]), -(r["utility"] or -9)))
    for r in show[:40]:
        lines.append(
            f"| {r['controller']} | {r['detector']} | {r['utility']:.4f} | "
            f"{r['block_bootstrap_positive_probability']:.4f} | {r['max_drawdown']:.4f} | "
            f"{r['s_crisis_mean_excess']} | {r['s_crisis_strategy_compound']} | {r['both_gates_pass']} |"
        )
    if winner:
        lines += [
            "", "## Recommended (OOF — not yet held-out)", "",
            f"- `{winner['controller']}` / `{winner['detector']}`",
            f"- util={winner['utility']:.4f} boot={winner['block_bootstrap_positive_probability']} "
            f"mdd={winner['max_drawdown']:.4f}",
            "", "Next: lock S9A1 and held-out once.", "",
        ]
    else:
        lines += [
            "",
            "No dual-gate freeze/orth winner. **Stop A3-R1 controller grids.**",
            "E45-C1 requires a new stress alpha engine outside TECH2 family remixes.",
            "",
        ]
    lines += ["Artifact: `reports/stage9a_e45c1_freeze_orth_oof_summary.json`", ""]
    (out / "E50-A3-R1_STAGE9A_E45C1_FREEZE_ORTH_OOF.md").write_text("\n".join(lines))
    print(json.dumps({
        "research_decision": decision,
        "n_candidates": len(candidates),
        "winner": None if not winner else {
            "controller": winner["controller"],
            "detector": winner["detector"],
            "utility": winner["utility"],
            "boot": winner["block_bootstrap_positive_probability"],
            "mdd": winner["max_drawdown"],
            "pass_via_stress": winner.get("pass_via_stress"),
            "pass_via_mdd": winner.get("pass_via_mdd"),
        },
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
