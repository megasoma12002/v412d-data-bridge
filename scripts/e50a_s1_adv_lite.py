#!/usr/bin/env python3
"""E50-A3-S1 Track B adversarial-lite on locked OOF winner (EXPERIMENTAL).

Board rule (DUAL_TRACK_OPERATING_BOARD):
  - Adversarial-lite on **OOF** (2011–2018)
  - placebo util beat rate < 50%
  - not falsified on year-split vs C4

Does NOT open held-out. No cut retune. No live wire.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e50a3_train_exact_open as a3
from e50a3r1_turnover_diagnosis import (
    OOF_END,
    OOF_START,
    buffered_orders_ext,
)
from e50a3r1_stage8c_multisleeve_oof import build_oof_state
from e50a3r1_stage13_adversarial_10rounds import (
    matched_placebo_flags,
    summarize_nav,
    year_slices,
)
from e50a_s1_stress_engine_oof import (
    FAMILIES,
    build_residual_scores,
    detector_flags,
    merge_orders_switch,
    shell_cfg,
)

PLACEBO_N = 12


def sim_switch(bull_scored, stress_scored, calendar, execution, flags, start, end, name, cfg):
    bull_orders, _ = buffered_orders_ext(bull_scored, calendar, **cfg)
    stress_orders, _ = buffered_orders_ext(stress_scored, calendar, **cfg)
    orders = merge_orders_switch(bull_orders, stress_orders, flags)
    nav, trades = a3.simulate(orders, execution, start, end)
    proxy = a3.market_proxy(execution, start, end)
    stress = {d for d, on in flags.items() if on and start <= d <= end}
    return summarize_nav(nav, trades, proxy, name, stress, flags), nav, proxy


def sim_c4(scored, calendar, execution, start, end, name, cfg, stress_dates):
    orders, _ = buffered_orders_ext(scored, calendar, **cfg)
    nav, trades = a3.simulate(orders, execution, start, end)
    proxy = a3.market_proxy(execution, start, end)
    return summarize_nav(nav, trades, proxy, name, stress_dates), nav, proxy


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", type=Path, default=Path("/tmp/a2/causal_factor_panel.parquet"))
    ap.add_argument("--labels", type=Path, default=Path("/tmp/a2/forward_labels_research_only.parquet"))
    ap.add_argument("--prices", type=Path, default=Path("/tmp/a0/point_in_time_universe.csv"))
    ap.add_argument("--actions", type=Path, default=Path("/tmp/a1/corporate_action_ledger.csv.gz"))
    ap.add_argument("--a2-qc", type=Path, default=Path("/tmp/a2/qc_status.json"))
    ap.add_argument(
        "--oof-scores",
        type=Path,
        default=Path("repro/e50a-dual-track/track_b_s1_oof/outputs/oof_scores_selected_model.parquet"),
    )
    ap.add_argument(
        "--oof-summary",
        type=Path,
        default=Path("repro/e50a-dual-track/track_b_s1_oof/reports/s1_oof_summary.json"),
    )
    ap.add_argument("--out", type=Path, default=Path("repro/e50a-dual-track/track_b_s1_adv_lite"))
    ap.add_argument("--placebo-n", type=int, default=PLACEBO_N)
    args = ap.parse_args()
    out = args.out
    (out / "outputs").mkdir(parents=True, exist_ok=True)
    (out / "reports").mkdir(parents=True, exist_ok=True)
    if json.loads(args.a2_qc.read_text())["status"] != "PASS":
        raise RuntimeError("E50-A2 QC is not PASS")

    oof = json.loads(args.oof_summary.read_text())
    if oof.get("research_decision") != "OOF_S1_DUAL_GATE_STRESS_WINNER_READY_FOR_ADV_LITE":
        raise SystemExit(f"OOF not ready for adv-lite: {oof.get('research_decision')}")
    winner = oof["recommended"]
    family = winner["family"]
    det_id = winner["detector"]
    cfg = shell_cfg(winner.get("shell"))
    print(f"locked OOF winner: {family} / {det_id} / shell={cfg}", flush=True)

    panel = pl.read_parquet(args.panel).sort(["date", "code"])
    labels = pl.read_parquet(args.labels)
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

    if not args.oof_scores.exists():
        print(f"missing {args.oof_scores}; rebuilding TECH2 OOF scores ...", flush=True)
        import e50a3r1_repair as r1
        from e50a3r1_turnover_diagnosis import build_oof_scores

        exact_labels = a3.build_exact_open_labels(panel, execution, calendar)
        joined = a3.target_rank(
            r1.add_regime(panel).join(
                exact_labels.select("date", "code", a3.LABEL), on=["date", "code"], validate="1:1"
            )
        )
        scored = build_oof_scores(joined, calendar)
        args.oof_scores.parent.mkdir(parents=True, exist_ok=True)
        scored.write_parquet(args.oof_scores, compression="zstd")
    scored = pl.read_parquet(args.oof_scores).sort(["date", "code"])
    scored = scored.filter(pl.col("date").is_between(OOF_START, OOF_END))
    fam_col = FAMILIES[family]
    stress_scores = build_residual_scores(panel, fam_col, OOF_START, OOF_END)

    state = build_oof_state(panel, labels, execution)
    flags = detector_flags(state)[det_id]
    stress_dates = {d for d, on in flags.items() if on}
    print(f"OOF stress days ({det_id}): {len(stress_dates)}", flush=True)

    c4_pt, c4_nav, c4_px = sim_c4(
        scored, calendar, execution, OOF_START, OOF_END, "REF_C4_OOF", cfg, stress_dates
    )
    s1_pt, s1_nav, s1_px = sim_switch(
        scored, stress_scores, calendar, execution, flags, OOF_START, OOF_END, "S1_OOF", cfg
    )
    print(
        f"OOF C4 util={c4_pt['utility']:.4f} stress_ex={c4_pt['s_crisis_mean_excess']} | "
        f"S1 util={s1_pt['utility']:.4f} stress_ex={s1_pt['s_crisis_mean_excess']}",
        flush=True,
    )

    pool = [d for d in sorted(scored["date"].unique().to_list()) if OOF_START <= d <= OOF_END]
    n_on = sum(1 for d in pool if flags.get(d, False))
    placebo_rows = []
    for i in range(args.placebo_n):
        pf = matched_placebo_flags(flags, pool, n_on, np.random.default_rng(71000 + i))
        pt, _, _ = sim_switch(
            scored, stress_scores, calendar, execution, pf, OOF_START, OOF_END, f"PLC_{i}", cfg
        )
        placebo_rows.append(
            {"i": i, "utility": pt["utility"], "s_crisis_mean_excess": pt["s_crisis_mean_excess"]}
        )
        print(f"  placebo {i+1}/{args.placebo_n} util={pt['utility']:.4f}", flush=True)

    p_util = float(np.mean([r["utility"] >= s1_pt["utility"] for r in placebo_rows])) if placebo_rows else 1.0
    p_stress = float(
        np.mean(
            [
                (r["s_crisis_mean_excess"] or -9) >= (s1_pt["s_crisis_mean_excess"] or -9)
                for r in placebo_rows
            ]
        )
    ) if placebo_rows else 1.0

    y_c4 = year_slices(c4_nav, c4_px)
    y_s1 = year_slices(s1_nav, s1_px)
    years = sorted(set(y_c4) & set(y_s1))
    beat_years = [y for y in years if y_s1[y]["utility"] > y_c4[y]["utility"]]
    edge_util = s1_pt["utility"] - c4_pt["utility"]
    edge_stress = (s1_pt["s_crisis_mean_excess"] or 0) - (c4_pt["s_crisis_mean_excess"] or 0)

    # Board: placebo util beat rate < 50%; year-split not falsified vs C4
    falsified = bool(p_util >= 0.50)
    if edge_util <= 0 and edge_stress <= 0:
        falsified = True
    if len(beat_years) == 0:
        falsified = True
    wounded = (not falsified) and (p_util >= 0.35 or len(beat_years) <= 1)

    decision = "STOP_S1_ADV" if falsified else "ADV_LITE_PASS_READY_FOR_HELDOUT"
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "version_id": "E50-A3-S1",
        "track": "B_STRESS_ENGINE",
        "locked_from_oof": {"family": family, "detector": det_id, "shell": cfg},
        "window": "2011-2018 OOF adversarial-lite",
        "live_wire": False,
        "heldout_opened": False,
        "placebo_n": args.placebo_n,
        "p_placebo_util_ge": p_util,
        "p_placebo_stress_ge": p_stress,
        "oof_years_beat_c4_util": beat_years,
        "oof_edge_util_vs_c4": edge_util,
        "oof_edge_stress_vs_c4": edge_stress,
        "c4_oof": c4_pt,
        "s1_oof": s1_pt,
        "adv_falsified": falsified,
        "adv_wounded": wounded,
        "research_decision": decision,
        "next_if_pass": "one held-out (val+sealed); only PASS_HELDOUT replaces Track A",
        "next_if_stop": "keep Track A S9A1; STOP_S1_ADV — do not retune",
    }
    (out / "reports" / "s1_adv_lite_summary.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
    pl.DataFrame(placebo_rows).write_csv(out / "outputs" / "s1_adv_lite_placebo.csv")
    research = Path("research/e50a")
    (research / "E50A_S1_ADV_LITE_SUMMARY.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
    lines = [
        "# E50-A3-S1 Track B — Adversarial-lite (OOF)",
        "",
        f"Locked: `{family}` / `{det_id}`",
        f"Decision: `{decision}`",
        "",
        f"- Placebo P(util≥): `{p_util:.3f}` (board fail if ≥0.50)",
        f"- Placebo P(stress≥): `{p_stress:.3f}`",
        f"- OOF years util > C4: `{beat_years}`",
        f"- OOF util edge vs C4: `{edge_util:.4f}`",
        f"- OOF stress edge vs C4: `{edge_stress}`",
        "",
        "No held-out in this step. No live wire.",
        "",
    ]
    md = "\n".join(lines)
    (out / "E50A_S1_ADV_LITE.md").write_text(md)
    (research / "E50A_S1_ADV_LITE.md").write_text(md)
    print(json.dumps({"research_decision": decision, "p_util": p_util, "beat_years": beat_years}, indent=2))


if __name__ == "__main__":
    main()
