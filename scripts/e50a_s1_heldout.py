#!/usr/bin/env python3
"""E50-A3-S1 Track B one-shot held-out (RESEARCH_ONLY).

Locked from OOF + adv-lite (do not retune):
  family: S1-QRES
  detector: COMBO_VOL80_VAL00
  controller: SWITCH_S1_BOOK
  shell: C4

Windows:
  validation 2019-01-01 .. 2022-12-31
  sealed    2023-01-01 .. latest

Pass both: dual-gate (TO≤2.5% + boot≥0.70 EXPERIMENTAL) AND stress mean excess ≥ REF_C4.
No live-wire. No cut retune.
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
import e50a3r1_repair as r1
from e50a3r1_turnover_diagnosis import BOOTSTRAP_GATE, TURNOVER_CEILING, buffered_orders_ext
from e50a3r1_stage6_risk_overlay_oof import C4, build_market_state, hysteresis, mean_gross_exposure
from e50a3r1_stage7_crisis_challenger_oof import attach_crisis, period_metrics
from e50a3r1_stage8a_failure_signature import build_daily_panel_state, trailing_ic
from e50a3r1_stage8c_multisleeve_oof import rolling_percentile_flags
from e50a_s1_stress_engine_oof import FAMILIES, build_residual_scores, merge_orders_switch, shell_cfg

VAL_START, VAL_END = date(2019, 1, 1), date(2022, 12, 31)
SEALED_START = date(2023, 1, 1)
LOCKED = {
    "family": "S1-QRES",
    "detector": "COMBO_VOL80_VAL00",
    "vol_pctl": 0.80,
    "val_ic_min": 0.00,
    "hysteresis_on": 2,
    "hysteresis_off": 5,
}


def classify(val: dict, sealed: dict) -> str:
    if not (val.get("exact_t1_ok") and sealed.get("exact_t1_ok")):
        return "INCONCLUSIVE"
    val_ok = bool(val["both_gates_pass"] and val["stress_beats_c4"])
    sealed_ok = bool(sealed["both_gates_pass"] and sealed["stress_beats_c4"])
    if val_ok and sealed_ok:
        return "PASS_HELDOUT"
    if (not val_ok) and (not sealed_ok):
        return "FAIL_HELDOUT"
    return "MIXED_HELDOUT"


def build_flags(panel, labels, execution) -> dict[date, bool]:
    state = build_daily_panel_state(panel).sort("date")
    mkt = attach_crisis(build_market_state(execution))
    ic_val = trailing_ic(panel, labels, "value_family_score", 21)
    joined = (
        state.join(mkt.select("date", "crisis").rename({"crisis": "crisis_vote2"}), on="date", how="left")
        .join(ic_val.select("date", "ic_lag21").rename({"ic_lag21": "val_ic_lag21"}), on="date", how="left")
        .sort("date")
    )
    rows = joined.to_dicts()
    dates = [r["date"] for r in rows]
    vol = [r.get("mkt_vol_60d") for r in rows]
    crisis = np.array([bool(r.get("crisis_vote2") or False) for r in rows])
    val_ok = np.array(
        [(r.get("val_ic_lag21") is not None and r["val_ic_lag21"] >= LOCKED["val_ic_min"]) for r in rows]
    )
    vol_h = hysteresis(
        rolling_percentile_flags(vol, 252, LOCKED["vol_pctl"]),
        LOCKED["hysteresis_on"],
        LOCKED["hysteresis_off"],
    )
    arr = (~crisis) & vol_h & val_ok
    return {d: bool(arr[i]) for i, d in enumerate(dates)}


def walk_forward_scores(joined: pl.DataFrame, calendar: list[date], start: date, end: date) -> pl.DataFrame:
    pieces = []
    years = sorted({d.year for d in calendar if start <= d <= end})
    for y in years:
        lo, hi = max(date(y, 1, 1), start), min(date(y, 12, 31), end)
        cutoff = a3.previous_session(calendar, lo, 22)
        model = r1.fit_model(joined, "TECH2", "BREADTH_REGIME", 1.0, cutoff)
        piece = r1.score_period(joined, model, lo, hi)
        if piece.height:
            pieces.append(piece)
    return pl.concat(pieces).sort(["date", "code"]) if pieces else joined.head(0)


def evaluate_window(bull, stress, calendar, execution, flags, start, end, name, cfg) -> dict:
    bull_o, _ = buffered_orders_ext(bull, calendar, **cfg)
    stress_o, _ = buffered_orders_ext(stress, calendar, **cfg)
    switched = merge_orders_switch(bull_o, stress_o, flags)
    stress_dates = {d for d, on in flags.items() if on and start <= d <= end}

    nav_s, tr_s = a3.simulate(switched, execution, start, end)
    nav_c, tr_c = a3.simulate(bull_o, execution, start, end)
    proxy = a3.market_proxy(execution, start, end)

    m_s = a3.metrics(nav_s, tr_s, name)
    _, st_s = a3.compare(nav_s, proxy)
    pm_s = period_metrics(nav_s, proxy, stress_dates)
    m_c = a3.metrics(nav_c, tr_c, f"C4::{name}")
    pm_c = period_metrics(nav_c, proxy, stress_dates)

    t = tr_s.with_columns(pl.col("signal_date").cast(pl.Date), pl.col("execution_date").cast(pl.Date))
    same = int(t.filter(pl.col("execution_date") <= pl.col("signal_date")).height)
    sex = pm_s.get("crisis_mean_excess")
    cex = pm_c.get("crisis_mean_excess")
    out = {
        "window": name,
        "cagr": m_s.get("cagr"),
        "max_drawdown": m_s.get("max_drawdown"),
        "utility": (m_s.get("cagr") or 0) - 0.5 * abs(m_s.get("max_drawdown") or 0),
        "average_daily_turnover": m_s.get("average_daily_turnover"),
        "block_bootstrap_positive_probability": st_s.get("block_bootstrap_positive_probability"),
        "mean_gross_exposure": mean_gross_exposure(nav_s),
        "turnover_gate_pass": bool((m_s.get("average_daily_turnover") or 9) <= TURNOVER_CEILING),
        "bootstrap_gate_pass": bool((st_s.get("block_bootstrap_positive_probability") or 0) >= BOOTSTRAP_GATE),
        "exact_t1_ok": same == 0,
        "stress_day_share": len(stress_dates) / max(nav_s.height, 1),
        "s_crisis_mean_excess": sex,
        "c4_cagr": m_c.get("cagr"),
        "c4_max_drawdown": m_c.get("max_drawdown"),
        "c4_s_crisis_mean_excess": cex,
        "stress_beats_c4": bool(sex is not None and cex is not None and sex > cex + 1e-12),
    }
    out["both_gates_pass"] = bool(out["turnover_gate_pass"] and out["bootstrap_gate_pass"])
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", type=Path, default=Path("/tmp/a2/causal_factor_panel.parquet"))
    ap.add_argument("--labels", type=Path, default=Path("/tmp/a2/forward_labels_research_only.parquet"))
    ap.add_argument("--prices", type=Path, default=Path("/tmp/a0/point_in_time_universe.csv"))
    ap.add_argument("--actions", type=Path, default=Path("/tmp/a1/corporate_action_ledger.csv.gz"))
    ap.add_argument("--a2-qc", type=Path, default=Path("/tmp/a2/qc_status.json"))
    ap.add_argument(
        "--adv-summary",
        type=Path,
        default=Path("repro/e50a-dual-track/track_b_s1_adv_lite/reports/s1_adv_lite_summary.json"),
    )
    ap.add_argument("--out", type=Path, default=Path("repro/e50a-dual-track/track_b_s1_heldout"))
    args = ap.parse_args()
    out = args.out
    (out / "outputs").mkdir(parents=True, exist_ok=True)
    (out / "reports").mkdir(parents=True, exist_ok=True)
    if json.loads(args.a2_qc.read_text())["status"] != "PASS":
        raise RuntimeError("E50-A2 QC is not PASS")
    adv = json.loads(args.adv_summary.read_text())
    if adv.get("research_decision") != "ADV_LITE_PASS_READY_FOR_HELDOUT":
        raise SystemExit(f"adv-lite not ready: {adv.get('research_decision')}")

    locked = adv.get("locked_from_oof") or {}
    family = locked.get("family") or LOCKED["family"]
    det_id = locked.get("detector") or LOCKED["detector"]
    cfg = shell_cfg(locked.get("shell"))
    print(f"locked held-out: {family} / {det_id}", flush=True)

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
    sealed_end = calendar[-1]

    print("walk-forward TECH2 + residual scores ...", flush=True)
    exact = a3.build_exact_open_labels(panel, execution, calendar)
    joined = a3.target_rank(
        r1.add_regime(panel).join(exact.select("date", "code", a3.LABEL), on=["date", "code"], validate="1:1")
    )
    bull = walk_forward_scores(joined, calendar, VAL_START, sealed_end)
    stress = build_residual_scores(panel, FAMILIES[family], VAL_START, sealed_end)
    flags = build_flags(panel, labels, execution)

    print("validation 2019-2022 ...", flush=True)
    val = evaluate_window(
        bull.filter(pl.col("date").is_between(VAL_START, VAL_END)),
        stress.filter(pl.col("date").is_between(VAL_START, VAL_END)),
        calendar,
        execution,
        flags,
        VAL_START,
        VAL_END,
        "validation_2019_2022",
        cfg,
    )
    print(
        f"  val boot={val['block_bootstrap_positive_probability']} to={val['average_daily_turnover']} "
        f"stress_ex={val['s_crisis_mean_excess']} vs_c4={val['stress_beats_c4']} dual={val['both_gates_pass']}",
        flush=True,
    )

    print(f"sealed 2023-{sealed_end} ...", flush=True)
    sealed = evaluate_window(
        bull.filter(pl.col("date") >= SEALED_START),
        stress.filter(pl.col("date") >= SEALED_START),
        calendar,
        execution,
        flags,
        SEALED_START,
        sealed_end,
        "sealed_2023_latest",
        cfg,
    )
    print(
        f"  sealed boot={sealed['block_bootstrap_positive_probability']} to={sealed['average_daily_turnover']} "
        f"stress_ex={sealed['s_crisis_mean_excess']} vs_c4={sealed['stress_beats_c4']} dual={sealed['both_gates_pass']}",
        flush=True,
    )

    label = classify(val, sealed)
    decision = {
        "PASS_HELDOUT": "PASS_HELDOUT_S1",
        "MIXED_HELDOUT": "MIXED_HELDOUT_S1_KEEP_TRACK_A",
        "FAIL_HELDOUT": "STOP_S1_HELDOUT_KEEP_TRACK_A",
        "INCONCLUSIVE": "INCONCLUSIVE_S1_KEEP_TRACK_A",
    }[label]

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "version_id": "E50-A3-S1",
        "track": "B_STRESS_ENGINE",
        "live_wire": False,
        "retune_allowed": False,
        "locked": {"family": family, "detector": det_id, "shell": cfg, **LOCKED},
        "validation_2019_2022": val,
        "sealed_2023_latest": sealed,
        "heldout_label": label,
        "research_decision": decision,
        "promotion": {
            "replaces_track_a_paper_monitor": decision == "PASS_HELDOUT_S1",
            "live_wire": False,
        },
    }
    (out / "reports" / "s1_heldout_decision.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
    research = Path("research/e50a")
    (research / "E50A_S1_HELDOUT_DECISION.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
    lines = [
        "# E50-A3-S1 Track B — Held-out",
        "",
        f"Locked: `{family}` / `{det_id}`",
        f"Label: `{label}`",
        f"Decision: `{decision}`",
        "",
        "| Window | CAGR | MDD | TO | Boot | Stress ex | vs C4 | dual |",
        "|---|---:|---:|---:|---:|---:|---|---|",
        f"| val | {val['cagr']} | {val['max_drawdown']} | {val['average_daily_turnover']} | "
        f"{val['block_bootstrap_positive_probability']} | {val['s_crisis_mean_excess']} | "
        f"{val['stress_beats_c4']} | {val['both_gates_pass']} |",
        f"| sealed | {sealed['cagr']} | {sealed['max_drawdown']} | {sealed['average_daily_turnover']} | "
        f"{sealed['block_bootstrap_positive_probability']} | {sealed['s_crisis_mean_excess']} | "
        f"{sealed['stress_beats_c4']} | {sealed['both_gates_pass']} |",
        "",
        "No cut retune. No live wire.",
        "",
    ]
    md = "\n".join(lines)
    (out / "E50A_S1_HELDOUT.md").write_text(md)
    (research / "E50A_S1_HELDOUT.md").write_text(md)
    print(json.dumps({"research_decision": decision, "heldout_label": label}, indent=2))


if __name__ == "__main__":
    main()
