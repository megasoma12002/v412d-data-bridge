#!/usr/bin/env python3
"""Stage-10: five-round iterative stress-alpha search (EXPERIMENTAL / E45-C1).

Keeps TECH2+C4 as bull sleeve. Screens *new* stress return engines
(atomic/hybrid features not family-score remixes) switched by the S9A1
detector that traveled on held-out (COMBO_VOL70_VAL03).

Rounds adapt:
  R1 screen stress feature sleeves
  R2 held-out if winner else residual/short-rev expansion
  R3 held-out or freeze+sleeve hybrid / industry residual
  R4 blend near-misses or liquidity-safety set
  R5 finalize: held-out last lock if any, else stop + summary

Does not retune C2/C4/C8/F1/R6B1/S8B1/S8C1/S9A1 detector cuts after held-out.
Not an in-place E45 edit. OOF selection 2011–2018 only.
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
from e50a3r1_stage4_atomic_feature_oof import fit_model_exp, build_oof_scores as build_oof_scores_feats
from e50a3r1_stage6_risk_overlay_oof import C4, build_market_state, hysteresis, mean_gross_exposure
from e50a3r1_stage7_crisis_challenger_oof import (
    attach_crisis,
    merge_orders_crisis_sleeve,
    orders_on_dates,
    period_metrics,
)
from e50a3r1_stage8a_failure_signature import build_daily_panel_state, trailing_ic
from e50a3r1_stage8c_multisleeve_oof import rolling_percentile_flags, UTIL_SLACK
from e50a3r1_stage9a_e45c1_freeze_orth_oof import freeze_signal_dates

# Locked S9A1 detector (do not retune cuts)
DET = {
    "name": "COMBO_VOL70_VAL03",
    "vol_roll_window": 252,
    "vol_roll_pctl": 0.70,
    "val_ic_min": 0.03,
    "hysteresis_on": 2,
    "hysteresis_off": 5,
}

STRESS_SETS_R1 = {
    "QUAL4": ["pct_roa_ttm", "pct_roe_ttm", "pct_cfo_to_assets", "pct_accruals_to_assets"],
    "VALUE3": ["pct_book_to_price_proxy", "pct_earnings_yield_proxy", "pct_sales_yield_proxy"],
    "REV3": ["pct_monthly_revenue_yoy", "pct_revenue_3m_yoy", "pct_revenue_yoy_acceleration"],
    "DEF3": ["pct_vol_60d", "pct_downside_vol_60d", "pct_drawdown_63d"],
    "QUAL_VALUE": [
        "pct_roa_ttm", "pct_cfo_to_assets",
        "pct_book_to_price_proxy", "pct_earnings_yield_proxy",
    ],
    "REV_QUAL": [
        "pct_monthly_revenue_yoy", "pct_revenue_yoy_acceleration",
        "pct_roa_ttm", "pct_cfo_to_assets",
    ],
    "SAFE4": ["pct_cash_to_assets", "pct_current_ratio", "pct_leverage", "pct_drawdown_63d"],
    "LIQ_DEF": ["pct_amihud_20d", "pct_vol_60d", "pct_downside_vol_60d", "pct_cfo_to_assets"],
}

STRESS_SETS_R2_EXTRA = {
    "SHORT_REV": ["pct_reversal_5d", "pct_mom_63d", "pct_vol_60d", "pct_amihud_20d"],
    "GROW_QUAL": [
        "pct_revenue_growth_yoy", "pct_net_income_growth_yoy",
        "pct_roa_ttm", "pct_cfo_to_assets",
    ],
    "MARGIN_SAFE": [
        "pct_gross_margin_ttm", "pct_operating_margin_ttm",
        "pct_cash_to_assets", "pct_drawdown_63d",
    ],
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


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
    val_ok = np.array([
        (r.get("val_ic_lag21") is not None and r["val_ic_lag21"] >= DET["val_ic_min"]) for r in rows
    ])
    vol_h = hysteresis(
        rolling_percentile_flags(vol, DET["vol_roll_window"], DET["vol_roll_pctl"]),
        DET["hysteresis_on"], DET["hysteresis_off"],
    )
    arr = (~crisis) & vol_h & val_ok
    return {d: bool(arr[i]) for i, d in enumerate(dates)}


def residualize_scores(stress: pl.DataFrame, bull: pl.DataFrame) -> pl.DataFrame:
    """Cross-sectional residual of stress score vs bull score (OOF dates)."""
    j = stress.select("date", "code", "industry_category", "trading_money", "unexplained_price_jump",
                      pl.col("score").alias("s_stress")).join(
        bull.select("date", "code", pl.col("score").alias("s_bull")),
        on=["date", "code"], how="inner",
    )
    pieces = []
    for (day,), g in j.partition_by("date", as_dict=True).items():
        gg = g.drop_nulls(["s_stress", "s_bull"])
        if gg.height < 30:
            continue
        y = gg["s_stress"].to_numpy()
        x = gg["s_bull"].to_numpy()
        x = x - x.mean()
        denom = float(np.dot(x, x))
        beta = float(np.dot(x, y - y.mean()) / denom) if denom > 1e-12 else 0.0
        resid = y - (y.mean() + beta * x)
        pieces.append(gg.with_columns(pl.Series("score", resid)).select(
            "date", "code", "industry_category", "trading_money", "unexplained_price_jump", "score"
        ))
    return pl.concat(pieces).sort(["date", "code"]) if pieces else stress


def industry_neutralize(scored: pl.DataFrame) -> pl.DataFrame:
    return (
        scored.with_columns(
            (pl.col("score") - pl.col("score").mean().over(["date", "industry_category"])).alias("score")
        )
        .sort(["date", "code"])
    )


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


def pick_candidates(rows: list[dict]) -> list[dict]:
    bases = {r["detector"]: r for r in rows if r.get("is_baseline")}
    cands = []
    for r in rows:
        if r.get("is_baseline"):
            continue
        base = bases.get(r["detector"])
        if base is None or not r["both_gates_pass"]:
            continue
        util_ok = (r["utility"] or -9) >= (base["utility"] or -9) - UTIL_SLACK
        sex, bex = r["s_crisis_mean_excess"], base["s_crisis_mean_excess"]
        scomp, bcomp = r["s_crisis_strategy_compound"], base["s_crisis_strategy_compound"]
        stress_ok = (
            (sex is not None and bex is not None and sex > bex + 1e-12)
            or (scomp is not None and bcomp is not None and scomp > bcomp + 1e-12)
        )
        if util_ok and stress_ok:
            cands.append({**r, "base_utility": base["utility"], "base_stress_ex": bex, "base_stress_comp": bcomp})
    return sorted(
        cands,
        key=lambda r: (-(r["s_crisis_strategy_compound"] or -9), -(r["utility"] or -9), abs(r["max_drawdown"] or 9)),
    )


def screen_sleeves(
    *,
    tech_orders,
    bull_scores,
    joined,
    calendar,
    execution,
    flags,
    stress_dates,
    feature_sets: dict[str, list[str]],
    controllers: list[str],
    round_tag: str,
) -> list[dict]:
    share = len(stress_dates) / max(sum(1 for d in flags if OOF_START <= d <= OOF_END), 1)
    # more accurate share from stress_dates vs OOF days in tech orders
    oof_days = sorted({d for d in flags if OOF_START <= d <= OOF_END})
    share = len(stress_dates) / max(len(oof_days), 1)
    rows = []
    base = evaluate(tech_orders, execution, f"BASE::{round_tag}", stress_dates)
    base.update({
        "detector": DET["name"], "is_baseline": True, "controller": "BASE_FULL",
        "feature_set": "TECH2", "stress_day_share": share, "round": round_tag,
    })
    rows.append(base)
    print(f"  BASE util={base['utility']:.4f} boot={base['block_bootstrap_positive_probability']} "
          f"stress_ex={base['s_crisis_mean_excess']}", flush=True)

    score_cache: dict[str, pl.DataFrame] = {}
    for fs_name, feats in feature_sets.items():
        print(f"  building OOF scores {fs_name} ...", flush=True)
        scored = build_oof_scores_feats(joined, calendar, feats, "BREADTH_REGIME", 1.0)
        scored = scored.select("date", "code", "industry_category", "trading_money", "unexplained_price_jump", "score")
        score_cache[fs_name] = scored
        stress_orders, _ = buffered_orders_ext(scored, calendar, **C4)

        for ctrl in controllers:
            if ctrl == "SLEEVE":
                orders = merge_orders_crisis_sleeve(tech_orders, stress_orders, flags)
            elif ctrl == "SLEEVE_FREEZE":
                # freeze cadence on bull; on stress dates use stress book when a freeze-allowed reb hits
                freeze_dates = freeze_signal_dates(bull_scores, flags, C4["rebalance_every"])
                bull_f = orders_on_dates(bull_scores, calendar, freeze_dates, C4)
                # stress rebalance only on non-frozen? use same freeze dates for stress book continuity
                stress_f = orders_on_dates(scored, calendar, freeze_dates, C4)
                orders = merge_orders_crisis_sleeve(bull_f, stress_f, flags)
            elif ctrl == "RESID_SLEEVE":
                resid = residualize_scores(scored, bull_scores)
                resid_orders, _ = buffered_orders_ext(resid, calendar, **C4)
                orders = merge_orders_crisis_sleeve(tech_orders, resid_orders, flags)
            elif ctrl == "INDNEUT_SLEEVE":
                neut = industry_neutralize(scored)
                neut_orders, _ = buffered_orders_ext(neut, calendar, **C4)
                orders = merge_orders_crisis_sleeve(tech_orders, neut_orders, flags)
            elif ctrl == "FULL":
                orders = stress_orders
            else:
                raise ValueError(ctrl)
            name = f"{ctrl}::{fs_name}"
            m = evaluate(orders, execution, f"{name}::{round_tag}", stress_dates)
            m.update({
                "detector": DET["name"], "is_baseline": False, "controller": ctrl,
                "feature_set": fs_name, "stress_day_share": share, "round": round_tag,
            })
            rows.append(m)
            print(
                f"    {name}: util={m['utility']:.4f} boot={m['block_bootstrap_positive_probability']} "
                f"stress_ex={m['s_crisis_mean_excess']} both={m['both_gates_pass']}",
                flush=True,
            )
    return rows


def write_round_report(out: Path, round_id: str, decision: str, rows: list[dict], winner, note: str):
    (out / "reports").mkdir(parents=True, exist_ok=True)
    (out / "outputs").mkdir(parents=True, exist_ok=True)
    pl.DataFrame(rows).write_csv(out / "outputs" / f"stage10_{round_id}_oof_grid.csv")
    summary = {
        "generated_at_utc": utc_now(),
        "stage": f"STAGE10_{round_id.upper()}",
        "detector_locked": DET,
        "research_decision": decision,
        "n_rows": len(rows),
        "recommended": winner,
        "note": note,
        "e45_inplace_edit": False,
        "no_retune_s9a1_detector": True,
    }
    (out / "reports" / f"stage10_{round_id}_summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n"
    )
    lines = [
        f"# Stage-10 {round_id.upper()} — Stress Alpha OOF",
        "",
        f"Detector locked: `{DET['name']}` (S9A1). {note}",
        "",
        f"## Decision: `{decision}`",
        "",
        "| controller | feature_set | util | boot | stress_ex | stress_ret | both |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    show = sorted(rows, key=lambda r: (-(r["both_gates_pass"]), -(r["s_crisis_mean_excess"] or -9), -(r["utility"] or -9)))
    for r in show[:40]:
        lines.append(
            f"| {r['controller']} | {r['feature_set']} | {r['utility']:.4f} | "
            f"{r['block_bootstrap_positive_probability']:.4f} | {r['s_crisis_mean_excess']} | "
            f"{r['s_crisis_strategy_compound']} | {r['both_gates_pass']} |"
        )
    if winner:
        lines += [
            "", "## Recommended", "",
            f"- `{winner['controller']}` / `{winner['feature_set']}`",
            f"- util={winner['utility']:.4f} boot={winner['block_bootstrap_positive_probability']} "
            f"stress_ex={winner['s_crisis_mean_excess']}",
            "",
        ]
    (out / f"E50-A3-R1_STAGE10_{round_id.upper()}.md").write_text("\n".join(lines) + "\n")
    return summary


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


def run_heldout(out: Path, panel, labels, joined, execution, calendar, flags, lock: dict) -> dict:
    """One-shot held-out for a locked stress-sleeve config."""
    validation_start, validation_end = date(2019, 1, 1), date(2022, 12, 31)
    sealed_start, sealed_end = date(2023, 1, 1), max(calendar)
    val_cutoff = a3.previous_session(calendar, validation_start, 22)
    sealed_cutoff = a3.previous_session(calendar, sealed_start, 22)

    feats = lock["features"]
    ctrl = lock["controller"]
    fs_name = lock["feature_set"]

    def eval_period(start, end, fit_cutoff, freeze_combo: bool, use_stress_sleeve: bool, name):
        model_bull = r1.fit_model(joined, "TECH2", "BREADTH_REGIME", 1.0, fit_cutoff)
        bull_scored = r1.score_period(joined, model_bull, start, end)

        r1.FEATURE_SETS["EXP_TMP"] = feats
        model_s = r1.fit_model(joined, "EXP_TMP", "BREADTH_REGIME", 1.0, fit_cutoff)
        stress_scored = r1.score_period(joined, model_s, start, end)
        stress_view = stress_scored.select(
            "date", "code", "industry_category", "trading_money", "unexplained_price_jump", "score"
        )
        bull_view = bull_scored.select(
            "date", "code", "industry_category", "trading_money", "unexplained_price_jump", "score"
        )

        if ctrl == "RESID_SLEEVE":
            stress_view = residualize_scores(stress_view, bull_view)
        elif ctrl == "INDNEUT_SLEEVE":
            stress_view = industry_neutralize(stress_view)

        if not use_stress_sleeve:
            orders, _ = buffered_orders_ext(bull_scored, calendar, **C4)
        elif ctrl in ("SLEEVE", "RESID_SLEEVE", "INDNEUT_SLEEVE"):
            tech_o, _ = buffered_orders_ext(bull_scored, calendar, **C4)
            st_o, _ = buffered_orders_ext(stress_view, calendar, **C4)
            orders = merge_orders_crisis_sleeve(tech_o, st_o, flags)
        elif ctrl == "SLEEVE_FREEZE":
            fd = freeze_signal_dates(bull_scored, flags, C4["rebalance_every"])
            bull_f = orders_on_dates(bull_scored, calendar, fd, C4)
            st_f = orders_on_dates(stress_view, calendar, fd, C4)
            orders = merge_orders_crisis_sleeve(bull_f, st_f, flags)
        else:
            orders, _ = buffered_orders_ext(stress_view, calendar, **C4)

        nav, trades = a3.simulate(orders, execution, start, end)
        proxy = a3.market_proxy(execution, start, end)
        metric = a3.metrics(nav, trades, name)
        _, stats = a3.compare(nav, proxy)
        period_stress = {d for d, on in flags.items() if on and start <= d <= end}
        stress = period_metrics(nav, proxy, period_stress)
        t = trades.with_columns(pl.col("signal_date").cast(pl.Date), pl.col("execution_date").cast(pl.Date))
        same_bar = int(t.filter(pl.col("execution_date") <= pl.col("signal_date")).height)
        cagr, mdd, turn = metric.get("cagr"), metric.get("max_drawdown"), metric.get("average_daily_turnover")
        boot = stats.get("block_bootstrap_positive_probability")
        period_dates = bull_scored["date"].unique().to_list()
        stress_on = sum(1 for d in period_dates if flags.get(d, False))
        out = {
            "portfolio": name,
            "cagr": cagr,
            "max_drawdown": mdd,
            "utility": (cagr or 0.0) - 0.5 * abs(mdd or 0.0),
            "average_daily_turnover": turn,
            "block_bootstrap_positive_probability": boot,
            "mean_gross_exposure": mean_gross_exposure(nav),
            "same_bar_fills": same_bar,
            "exact_t1_ok": same_bar == 0,
            "turnover_gate_pass": bool((turn or 9) <= TURNOVER_CEILING),
            "bootstrap_gate_pass": bool((boot or 0) >= BOOTSTRAP_GATE),
            "stress_flag_share": stress_on / max(len(period_dates), 1),
            **{f"s_{k}": v for k, v in stress.items()},
        }
        return out, nav, trades, proxy

    print("  held-out validation ...", flush=True)
    val, val_nav, val_tr, val_px = eval_period(
        validation_start, validation_end, val_cutoff, False, True, f"{lock['id']}_VAL"
    )
    print("  held-out sealed ...", flush=True)
    sealed, sealed_nav, sealed_tr, sealed_px = eval_period(
        sealed_start, sealed_end, sealed_cutoff, False, True, f"{lock['id']}_SEALED"
    )
    print("  C4 reference ...", flush=True)
    c4_val, _, _, _ = eval_period(validation_start, validation_end, val_cutoff, False, False, "C4_VAL")
    c4_sealed, _, _, _ = eval_period(sealed_start, sealed_end, sealed_cutoff, False, False, "C4_SEALED")

    label = classify(val, sealed)
    for tag, nav, tr, px in [
        (f"{lock['id'].lower()}_validation_2019_2022", val_nav, val_tr, val_px),
        (f"{lock['id'].lower()}_sealed_2023_latest", sealed_nav, sealed_tr, sealed_px),
    ]:
        nav.write_csv(out / "outputs" / f"{tag}_daily_nav.csv")
        tr.write_csv(out / "outputs" / f"{tag}_trades.csv")
        px.write_csv(out / "outputs" / f"{tag}_market_proxy_nav.csv")

    decision = {
        "generated_at_utc": utc_now(),
        "challenger_id": lock["id"],
        "locked_config": lock,
        "research_decision": label,
        "validation_2019_2022": val,
        "sealed_2023_latest": sealed,
        "c4_full_reference_validation": c4_val,
        "c4_full_reference_sealed": c4_sealed,
        "no_retune_on_heldout": True,
        "e45_inplace_edit": False,
    }
    (out / "reports" / f"stage10_{lock['id'].lower()}_heldout_decision.json").write_text(
        json.dumps(decision, indent=2, default=str) + "\n"
    )
    md = [
        f"# {lock['id']} Held-Out (Stage-10 stress alpha)",
        "",
        f"**`{label}`** — controller `{ctrl}` feature `{fs_name}` detector `{DET['name']}`",
        "",
        "| Metric | Challenger Val | Challenger Sealed | C4 Val | C4 Sealed |",
        "|---|---:|---:|---:|---:|",
        f"| CAGR | {100*val['cagr']:.2f}% | {100*sealed['cagr']:.2f}% | {100*c4_val['cagr']:.2f}% | {100*c4_sealed['cagr']:.2f}% |",
        f"| MDD | {100*val['max_drawdown']:.2f}% | {100*sealed['max_drawdown']:.2f}% | {100*c4_val['max_drawdown']:.2f}% | {100*c4_sealed['max_drawdown']:.2f}% |",
        f"| Bootstrap | {val['block_bootstrap_positive_probability']:.4f} | {sealed['block_bootstrap_positive_probability']:.4f} | {c4_val['block_bootstrap_positive_probability']:.4f} | {c4_sealed['block_bootstrap_positive_probability']:.4f} |",
        f"| Stress share | {100*val['stress_flag_share']:.1f}% | {100*sealed['stress_flag_share']:.1f}% | — | — |",
        f"| Stress excess | {val['s_crisis_mean_excess']} | {sealed['s_crisis_mean_excess']} | {c4_val['s_crisis_mean_excess']} | {c4_sealed['s_crisis_mean_excess']} |",
        f"| Boot gate | {val['bootstrap_gate_pass']} | {sealed['bootstrap_gate_pass']} | {c4_val['bootstrap_gate_pass']} | {c4_sealed['bootstrap_gate_pass']} |",
        "",
    ]
    (out / f"E50-A3-R1_STAGE10_{lock['id']}_HELDOUT.md").write_text("\n".join(md))
    print(json.dumps({
        "research_decision": label,
        "val_boot": val["block_bootstrap_positive_probability"],
        "val_stress_ex": val["s_crisis_mean_excess"],
        "c4_val_stress_ex": c4_val["s_crisis_mean_excess"],
        "sealed_boot": sealed["block_bootstrap_positive_probability"],
    }, indent=2, default=str), flush=True)
    return decision


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--oof-scores", type=Path, required=True)
    ap.add_argument("--panel", type=Path, required=True)
    ap.add_argument("--labels", type=Path, required=True)
    ap.add_argument("--prices", type=Path, required=True)
    ap.add_argument("--actions", type=Path, required=True)
    ap.add_argument("--a2-qc", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--max-rounds", type=int, default=5)
    args = ap.parse_args()
    out = args.out
    (out / "outputs").mkdir(parents=True, exist_ok=True)
    (out / "reports").mkdir(parents=True, exist_ok=True)
    if json.loads(args.a2_qc.read_text())["status"] != "PASS":
        raise RuntimeError("E50-A2 QC is not PASS")

    panel = pl.read_parquet(args.panel).sort(["date", "code"])
    labels = pl.read_parquet(args.labels)
    bull_scores = pl.read_parquet(args.oof_scores).sort(["date", "code"])
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
    exact_labels = a3.build_exact_open_labels(panel, execution, calendar)
    joined = a3.target_rank(
        r1.add_regime(panel).join(exact_labels.select("date", "code", a3.LABEL), on=["date", "code"], validate="1:1")
    )

    print("building S9A1 detector flags ...", flush=True)
    flags = build_flags(panel, labels, execution)
    stress_dates = {d for d, on in flags.items() if on and OOF_START <= d <= OOF_END}
    print(f"  OOF stress days={len(stress_dates)}", flush=True)
    tech_orders, _ = buffered_orders_ext(bull_scores, calendar, **C4)

    history = []
    pending_heldout_lock = None
    last_near_misses = []
    feature_pool = dict(STRESS_SETS_R1)
    heldout_done_ids = set()

    for round_num in range(1, args.max_rounds + 1):
        rid = f"r{round_num}"
        print(f"\n======== STAGE-10 ROUND {round_num} ========", flush=True)

        # If previous round produced a lock pending held-out, do held-out this round
        if pending_heldout_lock and pending_heldout_lock["id"] not in heldout_done_ids:
            print(f"Round {round_num}: held-out {pending_heldout_lock['id']} ...", flush=True)
            ho = run_heldout(out, panel, labels, joined, execution, calendar, flags, pending_heldout_lock)
            history.append({"round": round_num, "type": "heldout", "decision": ho})
            heldout_done_ids.add(pending_heldout_lock["id"])
            label = ho["research_decision"]
            pending_heldout_lock = None
            if label == "PASS_HELDOUT":
                history.append({"round": round_num, "type": "stop", "reason": "PASS_HELDOUT"})
                break
            # Continue to next round's OOF expansion (do not double-screen this round)
            continue

        # Normal OOF round scheduling
        post_heldout = bool(history) and history[-1].get("type") == "heldout"
        if round_num == 1:
            feature_pool = dict(STRESS_SETS_R1)
            controllers = ["SLEEVE", "SLEEVE_FREEZE"]
            note = "R1: atomic/hybrid stress sleeves on locked S9A1 detector"
        elif post_heldout or round_num == 2:
            feature_pool = {**STRESS_SETS_R2_EXTRA, "SAFE4": STRESS_SETS_R1["SAFE4"], "LIQ_DEF": STRESS_SETS_R1["LIQ_DEF"], "QUAL_VALUE": STRESS_SETS_R1["QUAL_VALUE"]}
            controllers = ["RESID_SLEEVE", "SLEEVE", "SLEEVE_FREEZE"]
            note = f"R{round_num}: residual/short-rev expansion" + (" after held-out" if post_heldout else "")
        elif round_num == 3:
            feature_pool = {
                "QUAL_VALUE": STRESS_SETS_R1["QUAL_VALUE"],
                "SAFE4": STRESS_SETS_R1["SAFE4"],
                "SHORT_REV": STRESS_SETS_R2_EXTRA["SHORT_REV"],
                "LIQ_DEF": STRESS_SETS_R1["LIQ_DEF"],
            }
            controllers = ["INDNEUT_SLEEVE", "SLEEVE_FREEZE", "RESID_SLEEVE"]
            note = "R3: industry-neutral + freeze hybrids"
        elif round_num == 4:
            feature_pool = {
                "BLEND_SAFE_QUAL": list(dict.fromkeys(STRESS_SETS_R1["SAFE4"] + STRESS_SETS_R1["QUAL4"])),
                "BLEND_LIQ_VALUE": list(dict.fromkeys(STRESS_SETS_R1["LIQ_DEF"] + STRESS_SETS_R1["VALUE3"])),
                "BLEND_REV_SAFE": list(dict.fromkeys(STRESS_SETS_R1["REV3"] + STRESS_SETS_R1["SAFE4"])),
            }
            controllers = ["SLEEVE", "RESID_SLEEVE", "SLEEVE_FREEZE"]
            note = "R4: blended stress feature packs"
        else:
            feature_pool = {
                "QUAL_VALUE": STRESS_SETS_R1["QUAL_VALUE"],
                "BLEND_SAFE_QUAL": list(dict.fromkeys(STRESS_SETS_R1["SAFE4"] + STRESS_SETS_R1["QUAL4"])),
                "SHORT_REV": STRESS_SETS_R2_EXTRA["SHORT_REV"],
                "MARGIN_SAFE": STRESS_SETS_R2_EXTRA["MARGIN_SAFE"],
            }
            controllers = ["RESID_SLEEVE", "INDNEUT_SLEEVE", "SLEEVE_FREEZE"]
            note = "R5: final OOF pass on best-themed packs"

        rows = screen_sleeves(
            tech_orders=tech_orders, bull_scores=bull_scores, joined=joined, calendar=calendar,
            execution=execution, flags=flags, stress_dates=stress_dates,
            feature_sets=feature_pool, controllers=controllers, round_tag=rid,
        )
        cands = pick_candidates(rows)
        winner = cands[0] if cands else None
        decision = "OOF_NEW_STRESS_ALPHA_DUAL_GATE_WINNER" if winner else "OOF_NO_NEW_STRESS_ALPHA_DUAL_GATE_WINNER"
        write_round_report(out, rid, decision, rows, winner, note)
        history.append({"round": round_num, "type": "oof", "decision": decision, "winner": winner, "note": note})
        last_near_misses = cands[:5] if cands else [
            r for r in sorted(rows, key=lambda x: (-(x["both_gates_pass"]), -(x["utility"] or -9)))
            if not r.get("is_baseline")
        ][:5]

        if winner:
            pending_heldout_lock = {
                "id": f"S10R{round_num}",
                "controller": winner["controller"],
                "feature_set": winner["feature_set"],
                "features": feature_pool[winner["feature_set"]],
                "detector": DET["name"],
            }
            continue

    # If still pending held-out after loop, run it
    if pending_heldout_lock and pending_heldout_lock["id"] not in heldout_done_ids:
        print(f"\nFinal held-out for {pending_heldout_lock['id']} ...", flush=True)
        ho = run_heldout(out, panel, labels, joined, execution, calendar, flags, pending_heldout_lock)
        history.append({"round": "final", "type": "heldout", "decision": ho})
        heldout_done_ids.add(pending_heldout_lock["id"])

    # Master summary
    master = {
        "generated_at_utc": utc_now(),
        "stage": "STAGE10_FIVE_ROUND_STRESS_ALPHA",
        "detector_locked": DET,
        "max_rounds": args.max_rounds,
        "history": history,
        "heldout_ids": sorted(heldout_done_ids),
        "e45_inplace_edit": False,
        "stop_controller_grids_prior": True,
        "gates_remain_experimental": True,
    }
    (out / "reports" / "stage10_five_round_summary.json").write_text(
        json.dumps(master, indent=2, default=str) + "\n"
    )
    lines = [
        "# Stage-10 Five-Round Stress Alpha Iteration",
        "",
        "New stress return engines on locked S9A1 detector. TECH2+C4 = bull sleeve.",
        "",
    ]
    for h in history:
        if h["type"] == "oof" or h["type"] == "oof_after_heldout":
            w = h.get("winner")
            wdesc = "none" if not w else f"{w.get('controller')}/{w.get('feature_set')}"
            lines.append(f"- Round {h['round']}: `{h['decision']}` winner={wdesc}")
        elif h["type"] == "heldout":
            d = h["decision"]
            lines.append(
                f"- Held-out {d.get('challenger_id')}: **`{d.get('research_decision')}`** "
                f"val_boot={d['validation_2019_2022']['block_bootstrap_positive_probability']} "
                f"stress_ex={d['validation_2019_2022'].get('s_crisis_mean_excess')}"
            )
        elif h["type"] == "stop":
            lines.append(f"- STOP: {h.get('reason')}")
    lines += ["", "Artifact: `reports/stage10_five_round_summary.json`", ""]
    (out / "E50-A3-R1_STAGE10_FIVE_ROUND_SUMMARY.md").write_text("\n".join(lines))
    print(json.dumps({
        "n_history": len(history),
        "heldout_ids": sorted(heldout_done_ids),
        "final_decisions": [
            (h.get("decision") if isinstance(h.get("decision"), str)
             else h.get("decision", {}).get("research_decision"))
            for h in history
        ],
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
