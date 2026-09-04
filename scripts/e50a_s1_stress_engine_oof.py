#!/usr/bin/env python3
"""E50-A3-S1 Track B OOF screen — residual stress books (EXPERIMENTAL).

Families (charter): S1-QRES / S1-DEFRES / S1-VALRES = family ~ momentum residual.
Detector class (charter): not crisis_vote2 + rolling-252d mkt_vol_60d pctl ∈ {0.70,0.80}
  + optional val_ic_lag21 ∈ {0.00,0.03}; hysteresis 2/5.
Controller: switch to S1 stress book while flag on; else REF_C4 (TECH2+C4).

Selection: 2011–2018 OOF only. No TECH2 remix. No live wire. No held-out in this script.
Winner rule: dual-gate + stress excess ≥ REF_C4 (+ ≥ Track A when same stress days / A flags).
"""
from __future__ import annotations

import argparse
import itertools
import json
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
    OOF_END,
    OOF_START,
    TURNOVER_CEILING,
    buffered_orders_ext,
    build_oof_scores,
)
from e50a3r1_stage6_risk_overlay_oof import C4, hysteresis, mean_gross_exposure
from e50a3r1_stage7_crisis_challenger_oof import (
    merge_orders_crisis_sleeve,
    orders_on_dates,
    period_metrics,
)
from e50a3r1_stage8c_multisleeve_oof import (
    MAX_STRESS_SHARE,
    MIN_STRESS_SHARE,
    UTIL_SLACK,
    build_oof_state,
    rolling_percentile_flags,
)
from e50a3r1_stage9a_e45c1_freeze_orth_oof import freeze_signal_dates

FAMILIES = {
    "S1-QRES": "quality_family_score",
    "S1-DEFRES": "defensive_family_score",
    "S1-VALRES": "value_family_score",
}

# Charter detector class (OOF-chosen cuts only)
DETECTOR_GRID = [
    {"id": "VOL70", "vol_pctl": 0.70, "val_ic_min": None},
    {"id": "VOL80", "vol_pctl": 0.80, "val_ic_min": None},
    {"id": "COMBO_VOL70_VAL00", "vol_pctl": 0.70, "val_ic_min": 0.00},
    {"id": "COMBO_VOL70_VAL03", "vol_pctl": 0.70, "val_ic_min": 0.03},
    {"id": "COMBO_VOL80_VAL00", "vol_pctl": 0.80, "val_ic_min": 0.00},
    {"id": "COMBO_VOL80_VAL03", "vol_pctl": 0.80, "val_ic_min": 0.03},
]

SHELL_GRID = [
    {"top_k": tk, "rebalance_every": reb, "exit_multiple": ex}
    for tk, reb, ex in itertools.product([20, 22, 30], [42, 63], [2.0, 2.25])
]

HYS_ON, HYS_OFF = 2, 5
TRACK_A_DETECTOR = "COMBO_VOL70_VAL03"


def build_residual_scores(panel: pl.DataFrame, family_col: str, date_start: date, date_end: date) -> pl.DataFrame:
    """Cross-sectional residual: family ~ momentum; score = resid - 0.25*pct_vol_60d."""
    d = panel.filter(pl.col("date").is_between(date_start, date_end)).select(
        "date",
        "code",
        "industry_category",
        "trading_money",
        "unexplained_price_jump",
        family_col,
        "momentum_family_score",
        "pct_vol_60d",
    )
    pieces: list[pl.DataFrame] = []
    for (day,), g in d.partition_by("date", as_dict=True).items():
        gg = g.drop_nulls([family_col, "momentum_family_score"])
        if gg.height < 30:
            continue
        y = gg[family_col].to_numpy()
        x = gg["momentum_family_score"].to_numpy()
        x = x - x.mean()
        denom = float(np.dot(x, x))
        beta = float(np.dot(x, y - y.mean()) / denom) if denom > 1e-12 else 0.0
        resid = y - (y.mean() + beta * x)
        out = gg.with_columns(pl.Series("resid", resid))
        out = out.with_columns(
            (pl.col("resid") - 0.25 * pl.col("pct_vol_60d").fill_null(0.5)).alias("score")
        )
        pieces.append(
            out.select(
                "date",
                "code",
                "industry_category",
                "trading_money",
                "unexplained_price_jump",
                "score",
            )
        )
    return pl.concat(pieces).sort(["date", "code"]) if pieces else d.head(0)


def detector_flags(state: pl.DataFrame) -> dict[str, dict[date, bool]]:
    rows = state.to_dicts()
    dates = [r["date"] for r in rows]
    vol = [r.get("mkt_vol_60d") for r in rows]
    val_ic = [r.get("val_ic_lag21") for r in rows]
    crisis = np.array([bool(r.get("crisis_vote2") or False) for r in rows])
    out: dict[str, dict[date, bool]] = {}
    for spec in DETECTOR_GRID:
        vol_raw = rolling_percentile_flags(vol, 252, spec["vol_pctl"])
        vol_h = hysteresis(vol_raw, HYS_ON, HYS_OFF)
        if spec["val_ic_min"] is None:
            arr = (~crisis) & vol_h
        else:
            val_ok = np.array(
                [(v is not None and v >= spec["val_ic_min"]) for v in val_ic]
            )
            arr = (~crisis) & vol_h & val_ok
        out[spec["id"]] = {d: bool(arr[i]) for i, d in enumerate(dates)}
    return out


def shell_cfg(base: dict | None = None) -> dict:
    cfg = dict(C4)
    if base:
        cfg.update(base)
    return cfg


def evaluate(orders, execution, name: str, stress_dates: set[date], start: date, end: date) -> dict:
    nav, trades = a3.simulate(orders, execution, start, end)
    proxy = a3.market_proxy(execution, start, end)
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


def stress_beats(challenger: dict, baseline: dict) -> bool:
    sex, bex = challenger.get("s_crisis_mean_excess"), baseline.get("s_crisis_mean_excess")
    scomp, bcomp = challenger.get("s_crisis_strategy_compound"), baseline.get("s_crisis_strategy_compound")
    return (
        (sex is not None and bex is not None and sex > bex + 1e-12)
        or (scomp is not None and bcomp is not None and scomp > bcomp + 1e-12)
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", type=Path, default=Path("/tmp/a2/causal_factor_panel.parquet"))
    ap.add_argument("--labels", type=Path, default=Path("/tmp/a2/forward_labels_research_only.parquet"))
    ap.add_argument("--prices", type=Path, default=Path("/tmp/a0/point_in_time_universe.csv"))
    ap.add_argument("--actions", type=Path, default=Path("/tmp/a1/corporate_action_ledger.csv.gz"))
    ap.add_argument("--a2-qc", type=Path, default=Path("/tmp/a2/qc_status.json"))
    ap.add_argument("--oof-scores", type=Path, default=None, help="Optional cached TECH2 OOF scores")
    ap.add_argument("--out", type=Path, default=Path("repro/e50a-dual-track/track_b_s1_oof"))
    ap.add_argument("--skip-shell-expand", action="store_true")
    args = ap.parse_args()
    out = args.out
    (out / "outputs").mkdir(parents=True, exist_ok=True)
    (out / "reports").mkdir(parents=True, exist_ok=True)
    if json.loads(args.a2_qc.read_text())["status"] != "PASS":
        raise RuntimeError("E50-A2 QC is not PASS")

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

    if args.oof_scores and args.oof_scores.exists():
        print(f"loading OOF scores: {args.oof_scores}", flush=True)
        scored = pl.read_parquet(args.oof_scores).sort(["date", "code"])
    else:
        print("building TECH2 OOF scores (2011–2018) ...", flush=True)
        exact_labels = a3.build_exact_open_labels(panel, execution, calendar)
        joined = a3.target_rank(
            r1.add_regime(panel).join(
                exact_labels.select("date", "code", a3.LABEL), on=["date", "code"], validate="1:1"
            )
        )
        scored = build_oof_scores(joined, calendar)
        scored.write_parquet(out / "outputs" / "oof_scores_selected_model.parquet", compression="zstd")

    print("building OOF state / charter detectors ...", flush=True)
    state = build_oof_state(panel, labels, execution)
    detectors = detector_flags(state)

    print("building residual stress books ...", flush=True)
    residual_scores = {
        fam: build_residual_scores(panel, col, OOF_START, OOF_END) for fam, col in FAMILIES.items()
    }
    for fam, sc in residual_scores.items():
        print(f"  {fam}: rows={sc.height}", flush=True)
        sc.write_parquet(out / "outputs" / f"scores_{fam.replace('-', '_').lower()}.parquet", compression="zstd")

    primary_shell = shell_cfg()
    print("building REF_C4 + residual orders (primary C4 shell) ...", flush=True)
    tech_orders, _ = buffered_orders_ext(scored, calendar, **primary_shell)
    residual_orders = {
        fam: buffered_orders_ext(sc, calendar, **primary_shell)[0] for fam, sc in residual_scores.items()
    }

    # Track A incumbent on its locked detector (FREEZE_REB) for same-day stress compare
    track_a_by_det: dict[str, dict] = {}
    if TRACK_A_DETECTOR in detectors:
        a_flags = detectors[TRACK_A_DETECTOR]
        a_stress = {d for d, on in a_flags.items() if on}
        freeze_dates = freeze_signal_dates(scored, a_flags, primary_shell["rebalance_every"])
        freeze_orders = orders_on_dates(scored, calendar, freeze_dates, primary_shell)
        track_a_by_det[TRACK_A_DETECTOR] = evaluate(
            freeze_orders, execution, f"TRACK_A_S9A1::{TRACK_A_DETECTOR}", a_stress, OOF_START, OOF_END
        )
        print(
            f"Track A S9A1 OOF: boot={track_a_by_det[TRACK_A_DETECTOR]['block_bootstrap_positive_probability']} "
            f"stress_ex={track_a_by_det[TRACK_A_DETECTOR]['s_crisis_mean_excess']}",
            flush=True,
        )

    rows: list[dict] = []
    for det_name, flags in detectors.items():
        stress_dates = {d for d, on in flags.items() if on}
        share = len(stress_dates) / max(state.height, 1)
        print(f"detector {det_name}: stress_days={len(stress_dates)} ({100 * share:.1f}%)", flush=True)
        if share < MIN_STRESS_SHARE or share > MAX_STRESS_SHARE:
            print("  skip share band", flush=True)
            continue

        base = evaluate(tech_orders, execution, f"REF_C4::{det_name}", stress_dates, OOF_START, OOF_END)
        base.update(
            {
                "detector": det_name,
                "family": "REF_C4",
                "is_baseline": True,
                "controller": "REF_C4",
                "stress_day_share": share,
                "shell": primary_shell,
                "pass_phase": "primary_c4_shell",
            }
        )
        rows.append(base)

        for fam, sleeve in residual_orders.items():
            switched = merge_orders_crisis_sleeve(tech_orders, sleeve, flags)
            m = evaluate(switched, execution, f"{fam}::{det_name}", stress_dates, OOF_START, OOF_END)
            m.update(
                {
                    "detector": det_name,
                    "family": fam,
                    "is_baseline": False,
                    "controller": "SWITCH_S1_BOOK",
                    "stress_day_share": share,
                    "shell": primary_shell,
                    "pass_phase": "primary_c4_shell",
                }
            )
            rows.append(m)
            print(
                f"  {fam}: util={m['utility']:.4f} boot={m['block_bootstrap_positive_probability']} "
                f"to={m['average_daily_turnover']:.4f} stress_ex={m['s_crisis_mean_excess']} "
                f"both={m['both_gates_pass']}",
                flush=True,
            )

    def collect_candidates(row_list: list[dict]) -> list[dict]:
        cands = []
        for tag in sorted({r["detector"] for r in row_list}):
            base = next(r for r in row_list if r["detector"] == tag and r["is_baseline"])
            track_a = track_a_by_det.get(tag)
            for r in row_list:
                if r["detector"] != tag or r["is_baseline"]:
                    continue
                if not r["both_gates_pass"]:
                    continue
                util_ok = (r["utility"] or -9) >= (base["utility"] or -9) - UTIL_SLACK
                vs_c4 = stress_beats(r, base)
                vs_a = True
                if track_a is not None:
                    vs_a = stress_beats(r, track_a)
                if util_ok and vs_c4 and vs_a:
                    cands.append(
                        {
                            **r,
                            "base_utility": base["utility"],
                            "base_stress_ex": base.get("s_crisis_mean_excess"),
                            "base_stress_comp": base.get("s_crisis_strategy_compound"),
                            "track_a_stress_ex": None if track_a is None else track_a.get("s_crisis_mean_excess"),
                            "beats_c4_stress": vs_c4,
                            "beats_track_a_stress": None if track_a is None else vs_a,
                        }
                    )
        return sorted(
            cands,
            key=lambda r: (
                -(r["s_crisis_strategy_compound"] or -9),
                -(r["utility"] or -9),
                abs(r["max_drawdown"] or 9),
            ),
        )

    candidates = collect_candidates(rows)

    # Shell expand for primary survivors (and near-miss dual-gate family×detector for discovery)
    shell_rows: list[dict] = []
    if not args.skip_shell_expand:
        expand_keys = {(c["family"], c["detector"]) for c in candidates}
        if not expand_keys:
            # near-miss: dual-gate but stress not yet beating C4 — still try shell once
            for r in rows:
                if r["is_baseline"] or not r["both_gates_pass"]:
                    continue
                expand_keys.add((r["family"], r["detector"]))
            expand_keys = set(list(expand_keys)[:6])  # cap
        print(f"shell expand for {len(expand_keys)} family×detector keys ...", flush=True)
        for fam, det_name in sorted(expand_keys):
            flags = detectors[det_name]
            stress_dates = {d for d, on in flags.items() if on}
            share = len(stress_dates) / max(state.height, 1)
            sc = residual_scores[fam]
            for shell in SHELL_GRID:
                cfg = shell_cfg(shell)
                if cfg == primary_shell:
                    continue
                tech_s, _ = buffered_orders_ext(scored, calendar, **cfg)
                sleeve_s, _ = buffered_orders_ext(sc, calendar, **cfg)
                base = evaluate(tech_s, execution, f"REF_C4::{det_name}::{cfg}", stress_dates, OOF_START, OOF_END)
                base.update(
                    {
                        "detector": det_name,
                        "family": "REF_C4",
                        "is_baseline": True,
                        "controller": "REF_C4",
                        "stress_day_share": share,
                        "shell": cfg,
                        "pass_phase": "shell_expand",
                    }
                )
                shell_rows.append(base)
                switched = merge_orders_crisis_sleeve(tech_s, sleeve_s, flags)
                m = evaluate(
                    switched, execution, f"{fam}::{det_name}::{cfg}", stress_dates, OOF_START, OOF_END
                )
                m.update(
                    {
                        "detector": det_name,
                        "family": fam,
                        "is_baseline": False,
                        "controller": "SWITCH_S1_BOOK",
                        "stress_day_share": share,
                        "shell": cfg,
                        "pass_phase": "shell_expand",
                    }
                )
                shell_rows.append(m)
                print(
                    f"  expand {fam}/{det_name}/k={cfg['top_k']}/reb={cfg['rebalance_every']}/ex={cfg['exit_multiple']}: "
                    f"both={m['both_gates_pass']} stress_ex={m['s_crisis_mean_excess']}",
                    flush=True,
                )

    all_rows = rows + shell_rows
    # Flatten shell dict for CSV
    flat = []
    for r in all_rows:
        fr = {k: v for k, v in r.items() if k != "shell"}
        sh = r.get("shell") or {}
        fr["top_k"] = sh.get("top_k")
        fr["rebalance_every"] = sh.get("rebalance_every")
        fr["exit_multiple"] = sh.get("exit_multiple")
        flat.append(fr)
    pl.DataFrame(flat).write_csv(out / "outputs" / "s1_oof_grid.csv")

    candidates = collect_candidates(all_rows)
    winner = candidates[0] if candidates else None
    decision = (
        "OOF_S1_DUAL_GATE_STRESS_WINNER_READY_FOR_ADV_LITE"
        if winner
        else "STOP_S1_OOF"
    )

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "version_id": "E50-A3-S1",
        "track": "B_STRESS_ENGINE",
        "window": "2011-2018 OOF only",
        "live_wire": False,
        "e45_inplace_edit": False,
        "forbidden_tech2_remix": True,
        "families": list(FAMILIES.keys()),
        "detectors": [d["id"] for d in DETECTOR_GRID],
        "primary_shell": primary_shell,
        "shell_expand": not args.skip_shell_expand,
        "n_rows": len(all_rows),
        "n_candidates": len(candidates),
        "research_decision": decision,
        "recommended": winner,
        "top_candidates": candidates[:8],
        "track_a_oof_reference": track_a_by_det,
        "gates_remain_experimental": True,
        "next_if_winner": "adversarial-lite on OOF; then one held-out; only PASS_HELDOUT replaces Track A",
        "next_if_stop": "keep Track A S9A1 paper/monitor; do not retune S1 cuts",
    }
    (out / "reports" / "s1_oof_summary.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")

    # Research status mirrors
    research = Path("research/e50a")
    research.mkdir(parents=True, exist_ok=True)
    (research / "E50A_S1_OOF_SUMMARY.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")

    lines = [
        "# E50-A3-S1 Track B — OOF Screen",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        "",
        "**EXPERIMENTAL.** No live wire. No held-out in this step.",
        "",
        f"## Decision: `{decision}`",
        "",
        f"Rows={len(all_rows)} candidates={len(candidates)}",
        "",
        "| family | detector | shell | util | boot | TO | stress_ex | both |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    show = sorted(
        [r for r in all_rows if not r["is_baseline"]],
        key=lambda r: (-(r["both_gates_pass"]), -(r["s_crisis_mean_excess"] or -9), -(r["utility"] or -9)),
    )[:40]
    for r in show:
        sh = r.get("shell") or {}
        shell_s = f"k{sh.get('top_k')}/r{sh.get('rebalance_every')}/e{sh.get('exit_multiple')}"
        lines.append(
            f"| {r['family']} | {r['detector']} | {shell_s} | {r['utility']:.4f} | "
            f"{r['block_bootstrap_positive_probability']:.4f} | {r['average_daily_turnover']:.4f} | "
            f"{r['s_crisis_mean_excess']} | {r['both_gates_pass']} |"
        )
    if winner:
        sh = winner.get("shell") or {}
        lines += [
            "",
            "## Recommended (OOF only — not held-out)",
            "",
            f"- family `{winner['family']}` detector `{winner['detector']}`",
            f"- shell top_k={sh.get('top_k')} reb={sh.get('rebalance_every')} exit={sh.get('exit_multiple')}",
            f"- util={winner['utility']:.4f} boot={winner['block_bootstrap_positive_probability']} "
            f"stress_ex={winner['s_crisis_mean_excess']}",
            "",
            "Next: adversarial-lite → one held-out. Only `PASS_HELDOUT` replaces Track A.",
            "",
        ]
    else:
        lines += [
            "",
            "`STOP_S1_OOF`: no dual-gate + stress≥C4 (and ≥Track A when comparable) winner.",
            "**Keep Track A.** Do not retune S1 cuts after this stop.",
            "",
        ]
    lines += [
        "Artifacts:",
        f"- `{out / 'reports' / 's1_oof_summary.json'}`",
        f"- `{out / 'outputs' / 's1_oof_grid.csv'}`",
        "",
    ]
    md = "\n".join(lines)
    (out / "E50A_S1_OOF_SCREEN.md").write_text(md)
    (research / "E50A_S1_OOF_SCREEN.md").write_text(md)
    print(json.dumps({"research_decision": decision, "n_candidates": len(candidates), "winner": winner}, indent=2, default=str))


if __name__ == "__main__":
    main()
