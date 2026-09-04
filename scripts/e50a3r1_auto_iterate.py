#!/usr/bin/env python3
"""E50-A3-R1 auto-iterate runner — single-axis, hard-stop (EXPERIMENTAL).

Axis-0 (this run): CAUSAL_VALUE_IC monitor rebuild of locked S9A1 cuts.
  - Same cuts: FREEZE_REB × COMBO_VOL70_VAL03 (p70 / val_ic>=0.03 / hys 2/5)
  - Only change: value-IC uses shift>=21 (label horizon) before rolling mean
  - No cut retune. No E45 edit. No gate promotion. No portfolio micro-grid.

Pipeline per candidate:
  L1 OOF screen (2011–2018) vs C4 + published S9A1
  L2 adversarial-lite (placebo util/stress, year-split vs C4)
  L3 one-shot held-out (val + sealed) IFF L1/L2 allow

Hard stops written to ledger:
  STOP_AXIS_OOF_FAIL | STOP_ADV_FALSIFIED | STOP_HELDOUT_NO_BEAT
  | UPDATE_MONITOR_CAUSAL | KEEP_PUBLISHED_S9A1
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
from e50a3r1_turnover_diagnosis import (
    BOOTSTRAP_GATE,
    OOF_END,
    OOF_START,
    TURNOVER_CEILING,
    buffered_orders_ext,
)
from e50a3r1_stage6_risk_overlay_oof import C4, mean_gross_exposure
from e50a3r1_stage7_crisis_challenger_oof import orders_on_dates, period_metrics
from e50a3r1_stage9a_e45c1_freeze_orth_oof import freeze_signal_dates
from e50a3r1_stage9a_s9a1_heldout import S9A1, build_flags
from e50a3r1_stage13_adversarial_10rounds import (
    VAL_END,
    VAL_START,
    SEALED_START,
    build_flags_causal,
    matched_placebo_flags,
    sim_freeze,
    sim_full,
    summarize_nav,
    year_slices,
)

AXIS = "CAUSAL_VALUE_IC_S9A1"
CANDIDATE_ID = "S9A1C"  # causal monitor twin; cuts locked
PLACEBO_N = 12
UTIL_SLACK_OOF = 0.005


def point_from_sim(pt: dict) -> dict:
    keys = [
        "cagr", "max_drawdown", "utility", "average_daily_turnover",
        "block_bootstrap_positive_probability", "mean_gross_exposure",
        "turnover_gate_pass", "bootstrap_gate_pass", "exact_t1_ok",
        "s_crisis_mean_excess", "s_crisis_strategy_compound", "s_crisis_day_share",
        "stress_flag_days",
    ]
    return {k: pt.get(k) for k in keys}


def classify_heldout(val: dict, sealed: dict) -> str:
    val_ok = bool(val["turnover_gate_pass"] and val["bootstrap_gate_pass"])
    sealed_ok = bool(sealed["turnover_gate_pass"] and sealed["bootstrap_gate_pass"])
    t1 = bool(val.get("exact_t1_ok") and sealed.get("exact_t1_ok"))
    if not t1:
        return "INCONCLUSIVE"
    if val_ok and sealed_ok:
        return "PASS_HELDOUT"
    if (not val_ok) and (not sealed_ok):
        return "FAIL_HELDOUT"
    return "MIXED_HELDOUT"


def oof_eval(scored, calendar, execution, flags, name: str, freeze: bool):
    if freeze:
        pt, nav, tr, px, *_ = sim_freeze(
            scored, calendar, execution, flags, OOF_START, OOF_END, name
        )
    else:
        # sim_full ignores flags; stress empty — recompute with empty ok for C4 baseline
        cfg = dict(C4)
        orders, _ = buffered_orders_ext(scored, calendar, **cfg)
        nav, tr = a3.simulate(orders, execution, OOF_START, OOF_END)
        px = a3.market_proxy(execution, OOF_START, OOF_END)
        stress = set()
        pt = summarize_nav(nav, tr, px, name, stress)
    return pt, nav, px


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", type=Path, required=True)
    ap.add_argument("--labels", type=Path, required=True)
    ap.add_argument("--prices", type=Path, required=True)
    ap.add_argument("--actions", type=Path, required=True)
    ap.add_argument("--a2-qc", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--placebo-n", type=int, default=PLACEBO_N)
    args = ap.parse_args()
    out = args.out
    (out / "outputs").mkdir(parents=True, exist_ok=True)
    (out / "reports").mkdir(parents=True, exist_ok=True)
    if json.loads(args.a2_qc.read_text())["status"] != "PASS":
        raise RuntimeError("E50-A2 QC is not PASS")

    ledger = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "AUTO_ITERATE",
        "axis": AXIS,
        "candidate_id": CANDIDATE_ID,
        "incumbent_monitor": "S9A1",
        "incumbent_baseline": "C4",
        "e45_inplace_edit": False,
        "no_retune_cuts": True,
        "no_gate_promotion": True,
        "locked_cuts": {
            "controller": S9A1["controller"],
            "detector": S9A1["detector"],
            "vol_roll_pctl": S9A1["vol_roll_pctl"],
            "val_ic_min": S9A1["val_ic_min"],
            "hysteresis_on": S9A1["hysteresis_on"],
            "hysteresis_off": S9A1["hysteresis_off"],
            "change": "value_ic_shift_ge_label_horizon_21",
        },
        "steps": {},
        "stop_reason": None,
        "decision": None,
    }

    print("loading ...", flush=True)
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
    sealed_end = max(calendar)
    exact_labels = a3.build_exact_open_labels(panel, execution, calendar)
    joined = a3.target_rank(
        r1.add_regime(panel).join(exact_labels.select("date", "code", a3.LABEL), on=["date", "code"], validate="1:1")
    )

    print("flags: published S9A1 + causal S9A1C ...", flush=True)
    flags_pub = build_flags(panel, labels, execution)
    flags_cau = build_flags_causal(panel, labels, execution)

    # ----- fit/score once per window -----
    print("fit/score OOF / VAL / SEALED ...", flush=True)
    oof_cut = a3.previous_session(calendar, OOF_START, 22)
    val_cut = a3.previous_session(calendar, VAL_START, 22)
    sealed_cut = a3.previous_session(calendar, SEALED_START, 22)
    model_oof = r1.fit_model(joined, "TECH2", "BREADTH_REGIME", 1.0, oof_cut)
    scored_oof = r1.score_period(joined, model_oof, OOF_START, OOF_END)
    model_val = r1.fit_model(joined, "TECH2", "BREADTH_REGIME", 1.0, val_cut)
    scored_val = r1.score_period(joined, model_val, VAL_START, VAL_END)
    model_sealed = r1.fit_model(joined, "TECH2", "BREADTH_REGIME", 1.0, sealed_cut)
    scored_sealed = r1.score_period(joined, model_sealed, SEALED_START, sealed_end)

    # ========== L1 OOF ==========
    print("\n=== L1 OOF screen ===", flush=True)
    c4_oof, c4_oof_nav, c4_oof_px = oof_eval(scored_oof, calendar, execution, flags_pub, "C4_OOF", False)
    s9_oof, s9_oof_nav, s9_oof_px = oof_eval(scored_oof, calendar, execution, flags_pub, "S9A1_OOF", True)
    s9c_oof, s9c_oof_nav, s9c_oof_px = oof_eval(scored_oof, calendar, execution, flags_cau, "S9A1C_OOF", True)

    oof_n_pub = sum(1 for d, on in flags_pub.items() if on and OOF_START <= d <= OOF_END)
    oof_n_cau = sum(1 for d, on in flags_cau.items() if on and OOF_START <= d <= OOF_END)
    dual_cau = bool(s9c_oof["turnover_gate_pass"] and s9c_oof["bootstrap_gate_pass"] and s9c_oof["exact_t1_ok"])
    util_ok = s9c_oof["utility"] >= (c4_oof["utility"] - UTIL_SLACK_OOF)
    stress_ok = (s9c_oof["s_crisis_mean_excess"] or -9) >= (c4_oof["s_crisis_mean_excess"] or -9)
    # Prefer causal to not be dramatically worse than published on OOF util
    vs_pub_util = s9c_oof["utility"] - s9_oof["utility"]

    l1_pass = dual_cau and util_ok and (stress_ok or s9c_oof["utility"] >= c4_oof["utility"])
    ledger["steps"]["L1_OOF"] = {
        "c4": point_from_sim(c4_oof),
        "s9a1_published": point_from_sim(s9_oof),
        "s9a1c_causal": point_from_sim(s9c_oof),
        "flag_days_published": oof_n_pub,
        "flag_days_causal": oof_n_cau,
        "dual_gate_causal": dual_cau,
        "util_vs_c4_ok": util_ok,
        "stress_vs_c4_ok": stress_ok,
        "util_minus_published": vs_pub_util,
        "l1_pass": l1_pass,
    }
    print(
        f"  C4 util={c4_oof['utility']:.4f} boot={c4_oof['block_bootstrap_positive_probability']:.3f}",
        flush=True,
    )
    print(
        f"  S9A1 util={s9_oof['utility']:.4f} boot={s9_oof['block_bootstrap_positive_probability']:.3f} "
        f"stress={s9_oof['s_crisis_mean_excess']}",
        flush=True,
    )
    print(
        f"  S9A1C util={s9c_oof['utility']:.4f} boot={s9c_oof['block_bootstrap_positive_probability']:.3f} "
        f"stress={s9c_oof['s_crisis_mean_excess']} dual={dual_cau} L1_pass={l1_pass}",
        flush=True,
    )

    if not l1_pass:
        ledger["stop_reason"] = "STOP_AXIS_OOF_FAIL"
        ledger["decision"] = "KEEP_PUBLISHED_S9A1_CAUSAL_NOT_OOF_COMPETITIVE"
        _write(out, ledger)
        return

    # ========== L2 adversarial-lite ==========
    print("\n=== L2 adversarial-lite (VAL placebo + year split) ===", flush=True)
    # baselines on VAL
    c4_val, c4_val_nav, _, c4_val_px, _ = sim_full(
        scored_val, calendar, execution, VAL_START, VAL_END, "C4_VAL"
    )
    s9_val, s9_val_nav, _, s9_val_px, _, _ = sim_freeze(
        scored_val, calendar, execution, flags_pub, VAL_START, VAL_END, "S9A1_VAL"
    )
    s9c_val, s9c_val_nav, _, s9c_val_px, _, _ = sim_freeze(
        scored_val, calendar, execution, flags_cau, VAL_START, VAL_END, "S9A1C_VAL"
    )

    pool = [d for d in sorted(scored_val["date"].unique().to_list()) if VAL_START <= d <= VAL_END]
    n_on = sum(1 for d in pool if flags_cau.get(d, False))
    placebo_rows = []
    for i in range(args.placebo_n):
        pf = matched_placebo_flags(flags_cau, pool, n_on, np.random.default_rng(51000 + i))
        for d, on in flags_cau.items():
            if d < VAL_START or d > VAL_END:
                pf[d] = on
        pt, *_ = sim_freeze(scored_val, calendar, execution, pf, VAL_START, VAL_END, f"PLC_{i}")
        placebo_rows.append({
            "i": i,
            "utility": pt["utility"],
            "s_crisis_mean_excess": pt["s_crisis_mean_excess"],
        })
        print(f"  placebo {i+1}/{args.placebo_n} util={pt['utility']:.4f}", flush=True)

    p_util = float(np.mean([r["utility"] >= s9c_val["utility"] for r in placebo_rows])) if placebo_rows else 1.0
    p_stress = float(np.mean([
        (r["s_crisis_mean_excess"] or -9) >= (s9c_val["s_crisis_mean_excess"] or -9)
        for r in placebo_rows
    ])) if placebo_rows else 1.0

    y_c4 = year_slices(c4_val_nav, c4_val_px)
    y_cau = year_slices(s9c_val_nav, s9c_val_px)
    years = sorted(set(y_c4) & set(y_cau))
    beat_years = [y for y in years if y_cau[y]["utility"] > y_c4[y]["utility"]]

    adv_falsified = p_stress >= 0.40 or p_util >= 0.40
    adv_wounded = (not adv_falsified) and (p_stress >= 0.20 or len(beat_years) <= 1)
    # also: causal must retain some edge vs C4 on VAL stress OR util
    val_edge_util = s9c_val["utility"] - c4_val["utility"]
    val_edge_stress = (s9c_val["s_crisis_mean_excess"] or 0) - (c4_val["s_crisis_mean_excess"] or 0)
    if val_edge_util <= 0 and val_edge_stress <= 0:
        adv_falsified = True

    ledger["steps"]["L2_ADV_LITE"] = {
        "c4_val": point_from_sim(c4_val),
        "s9a1_val": point_from_sim(s9_val),
        "s9a1c_val": point_from_sim(s9c_val),
        "n_on_causal": n_on,
        "p_placebo_util_ge": p_util,
        "p_placebo_stress_ge": p_stress,
        "val_years_beat_c4_util": beat_years,
        "val_edge_util_vs_c4": val_edge_util,
        "val_edge_stress_vs_c4": val_edge_stress,
        "adv_falsified": adv_falsified,
        "adv_wounded": adv_wounded,
        "placebo_rows": placebo_rows,
    }
    print(
        f"  L2 p_util={p_util:.2f} p_stress={p_stress:.2f} beat_years={beat_years} "
        f"edge_u={val_edge_util:.4f} falsified={adv_falsified}",
        flush=True,
    )

    if adv_falsified:
        ledger["stop_reason"] = "STOP_ADV_FALSIFIED"
        ledger["decision"] = "KEEP_PUBLISHED_S9A1_CAUSAL_ADV_FAIL"
        _write(out, ledger)
        return

    # ========== L3 one-shot held-out ==========
    print("\n=== L3 one-shot held-out (VAL already have; SEALED) ===", flush=True)
    c4_sealed, c4_sealed_nav, _, c4_sealed_px, _ = sim_full(
        scored_sealed, calendar, execution, SEALED_START, sealed_end, "C4_SEALED"
    )
    s9_sealed, s9_sealed_nav, _, s9_sealed_px, _, _ = sim_freeze(
        scored_sealed, calendar, execution, flags_pub, SEALED_START, sealed_end, "S9A1_SEALED"
    )
    s9c_sealed, s9c_sealed_nav, _, s9c_sealed_px, _, _ = sim_freeze(
        scored_sealed, calendar, execution, flags_cau, SEALED_START, sealed_end, "S9A1C_SEALED"
    )

    label = classify_heldout(s9c_val, s9c_sealed)
    # Beat criteria for updating monitor: on VAL, causal not worse than published on util by >3pp
    # AND (stress edge vs C4 > 0 OR util edge vs C4 > 0); sealed util not wrecked vs C4
    sealed_edge_util = s9c_sealed["utility"] - c4_sealed["utility"]
    vs_pub_val_util = s9c_val["utility"] - s9_val["utility"]
    update_ok = (
        label in ("PASS_HELDOUT", "MIXED_HELDOUT")
        and (val_edge_util > 0 or val_edge_stress > 0)
        and sealed_edge_util >= -0.02
        and s9c_val["exact_t1_ok"]
        and s9c_sealed["exact_t1_ok"]
    )
    # Prefer update only if causal is the honest live definition AND still useful vs C4
    # If much worse than published on VAL util, keep published for research archive but
    # still document causal as the required live feed.
    if update_ok and vs_pub_val_util >= -0.03 and not adv_wounded:
        decision = "UPDATE_MONITOR_TO_S9A1C_CAUSAL"
    elif update_ok:
        decision = "UPDATE_MONITOR_FEED_CAUSAL_KEEP_ARCHIVE_S9A1"
    else:
        decision = "KEEP_PUBLISHED_S9A1_CAUSAL_HELDOUT_NO_BEAT"
        ledger["stop_reason"] = "STOP_HELDOUT_NO_BEAT"

    if decision.startswith("UPDATE"):
        ledger["stop_reason"] = "STOP_AXIS_SUCCESS_UPDATE_MONITOR"
    elif ledger["stop_reason"] is None:
        ledger["stop_reason"] = "STOP_HELDOUT_NO_BEAT"

    ledger["steps"]["L3_HELDOUT"] = {
        "heldout_label": label,
        "c4_sealed": point_from_sim(c4_sealed),
        "s9a1_sealed": point_from_sim(s9_sealed),
        "s9a1c_sealed": point_from_sim(s9c_sealed),
        "s9a1c_val": point_from_sim(s9c_val),
        "sealed_edge_util_vs_c4": sealed_edge_util,
        "val_util_minus_published": vs_pub_val_util,
        "update_ok": update_ok,
        "adv_wounded": adv_wounded,
    }
    ledger["decision"] = decision
    print(f"  heldout={label} decision={decision}", flush=True)
    print(
        f"  S9A1C val util={s9c_val['utility']:.4f} boot={s9c_val['block_bootstrap_positive_probability']:.3f} "
        f"sealed util={s9c_sealed['utility']:.4f} boot={s9c_sealed['block_bootstrap_positive_probability']:.3f}",
        flush=True,
    )

    # save navs
    s9c_val_nav.write_csv(out / "outputs" / "auto_s9a1c_val_nav.csv")
    s9c_sealed_nav.write_csv(out / "outputs" / "auto_s9a1c_sealed_nav.csv")
    pl.DataFrame(placebo_rows).write_csv(out / "outputs" / "auto_s9a1c_placebo.csv")

    _write(out, ledger)


def _write(out: Path, ledger: dict) -> None:
    (out / "reports" / "auto_iterate_ledger.json").write_text(
        json.dumps(ledger, indent=2, default=str) + "\n"
    )
    d = ledger.get("decision")
    stop = ledger.get("stop_reason")
    l1 = ledger["steps"].get("L1_OOF", {})
    l2 = ledger["steps"].get("L2_ADV_LITE", {})
    l3 = ledger["steps"].get("L3_HELDOUT", {})
    lines = [
        "# Auto-Iterate Ledger — Causal Value-IC S9A1 (S9A1C)",
        "",
        "**Axis:** `CAUSAL_VALUE_IC_S9A1` — locked cuts; only IC causality fixed.",
        "No E45 edit. No cut retune. No gate promotion. No portfolio micro-grid.",
        "",
        f"## Decision: `{d}`",
        "",
        f"Stop reason: `{stop}`",
        "",
        "## L1 OOF",
        "",
    ]
    if l1:
        lines += [
            f"- L1 pass: `{l1.get('l1_pass')}` dual-gate causal: `{l1.get('dual_gate_causal')}`",
            f"- Flag days OOF published/causal: `{l1.get('flag_days_published')}` / `{l1.get('flag_days_causal')}`",
            f"- C4 util/boot: `{l1['c4']['utility']}` / `{l1['c4']['block_bootstrap_positive_probability']}`",
            f"- S9A1 util/boot/stress: `{l1['s9a1_published']['utility']}` / `{l1['s9a1_published']['block_bootstrap_positive_probability']}` / `{l1['s9a1_published']['s_crisis_mean_excess']}`",
            f"- S9A1C util/boot/stress: `{l1['s9a1c_causal']['utility']}` / `{l1['s9a1c_causal']['block_bootstrap_positive_probability']}` / `{l1['s9a1c_causal']['s_crisis_mean_excess']}`",
            "",
        ]
    lines += ["## L2 Adversarial-lite", ""]
    if l2:
        lines += [
            f"- Placebo P(util≥): `{l2.get('p_placebo_util_ge')}` P(stress≥): `{l2.get('p_placebo_stress_ge')}`",
            f"- VAL years beat C4 util: `{l2.get('val_years_beat_c4_util')}`",
            f"- VAL edge util/stress vs C4: `{l2.get('val_edge_util_vs_c4')}` / `{l2.get('val_edge_stress_vs_c4')}`",
            f"- Falsified/wounded: `{l2.get('adv_falsified')}` / `{l2.get('adv_wounded')}`",
            "",
        ]
    else:
        lines += ["_(skipped)_", ""]
    lines += ["## L3 Held-out", ""]
    if l3:
        lines += [
            f"- Label: `{l3.get('heldout_label')}`",
            f"- Sealed util edge vs C4: `{l3.get('sealed_edge_util_vs_c4')}`",
            f"- VAL util minus published S9A1: `{l3.get('val_util_minus_published')}`",
            "",
        ]
    else:
        lines += ["_(skipped)_", ""]
    lines += [
        "## Operating implication",
        "",
    ]
    if d and d.startswith("UPDATE_MONITOR_TO"):
        lines.append("Switch paper-monitor **definition** to S9A1C (causal IC). Cuts unchanged. Still MIXED / not frozen.")
    elif d and "FEED_CAUSAL" in (d or ""):
        lines.append(
            "Keep archived S9A1 metrics for research continuity; **live paper feed must use S9A1C causal IC**. Still MIXED."
        )
    else:
        lines.append("Do not replace S9A1 with causal twin for now; keep Option-2 caveats. Stop this axis.")
    lines += ["", "Artifact: `reports/auto_iterate_ledger.json`", ""]
    (out / "E50-A3-R1_AUTO_ITERATE_CAUSAL_S9A1C.md").write_text("\n".join(lines))
    print(json.dumps({"decision": d, "stop_reason": stop}, indent=2, default=str))


if __name__ == "__main__":
    main()
