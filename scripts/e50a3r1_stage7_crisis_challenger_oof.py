#!/usr/bin/env python3
"""Stage-7 OOF: crisis-period challenger (EXPERIMENTAL).

Goal class (user): high profit, low risk, responsive crisis behavior,
and non-negative (or improved) excess *during* crash/drawdown windows.

Alpha baseline frozen: TECH2 OOF scores + C4 name rules.
This stage adds a sleeve-level crisis controller — NOT an in-place E45 edit.

Selection: 2011–2018 OOF only.
Gates remain EXPERIMENTAL (turnover ≤2.5%, bootstrap ≥0.70).
Additional crisis screen (OOF): crisis-day mean excess vs market proxy
must be ≥ 0, or strictly better than BASE_FULL crisis excess.

Does not retune C2/C4/C8/F1/R6B1. Does not modify E16/E18/E22/E44/E45.
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
    OOF_END,
    OOF_START,
    TURNOVER_CEILING,
    buffered_orders_ext,
)
from e50a3r1_stage6_risk_overlay_oof import (
    C4,
    build_market_state,
    hysteresis,
    mean_gross_exposure,
    scale_orders,
)

# Fixed a priori crisis definition for selection (documented; not tuned on held-out).
# votes: dd120<=-0.10, vol20>=0.22, breadth60<=0.45; crisis if votes>=2 with 2/5 hysteresis.
CRISIS_DEF = {
    "name": "VOTE2_DD10_VOL22_BR45_HYS25",
    "dd_cut": -0.10,
    "vol_cut": 0.22,
    "breadth_cut": 0.45,
    "vote_threshold": 2,
    "on_need": 2,
    "off_need": 5,
}


def attach_crisis(mkt: pl.DataFrame, spec: dict = CRISIS_DEF) -> pl.DataFrame:
    dd = mkt["dd120"].to_numpy()
    vol = mkt["vol20"].to_numpy()
    br = mkt["breadth60"].to_numpy()
    votes = (
        ((~np.isnan(dd)) & (dd <= spec["dd_cut"])).astype(int)
        + ((~np.isnan(vol)) & (vol >= spec["vol_cut"])).astype(int)
        + ((~np.isnan(br)) & (br <= spec["breadth_cut"])).astype(int)
    )
    crisis = hysteresis(votes >= spec["vote_threshold"], spec["on_need"], spec["off_need"])
    return mkt.with_columns(
        pl.Series("crisis_votes", votes),
        pl.Series("crisis", crisis),
    )


def period_metrics(nav: pl.DataFrame, proxy: pl.DataFrame, crisis_dates: set[date]) -> dict:
    a = nav.select("date", pl.col("nav").pct_change().alias("strategy"), "turnover", "nav")
    b = proxy.select("date", pl.col("nav").pct_change().alias("benchmark"))
    x = a.join(b, on="date", how="inner").drop_nulls()
    x = x.with_columns((pl.col("strategy") - pl.col("benchmark")).alias("excess"))
    all_ex = x["excess"].to_numpy()
    crisis_mask = np.array([d in crisis_dates for d in x["date"].to_list()])
    crisis_x = x.filter(pl.Series(crisis_mask))
    other_x = x.filter(~pl.Series(crisis_mask))

    def _sum_ret(df: pl.DataFrame) -> float | None:
        if df.height < 2:
            return None
        # compound strategy returns in window
        r = df["strategy"].fill_null(0.0).to_numpy()
        return float(np.prod(1.0 + r) - 1.0)

    return {
        "n_days": x.height,
        "n_crisis_days": int(crisis_mask.sum()),
        "crisis_day_share": float(crisis_mask.mean()) if len(crisis_mask) else None,
        "crisis_mean_excess": float(crisis_x["excess"].mean()) if crisis_x.height else None,
        "crisis_hit_rate": float((crisis_x["excess"] > 0).mean()) if crisis_x.height else None,
        "crisis_sum_excess": float(crisis_x["excess"].sum()) if crisis_x.height else None,
        "crisis_strategy_compound": _sum_ret(crisis_x),
        "other_mean_excess": float(other_x["excess"].mean()) if other_x.height else None,
        "all_mean_excess": float(np.mean(all_ex)) if len(all_ex) else None,
    }


def build_defensive_scores(panel: pl.DataFrame, calendar: list[date], oof_dates: pl.Series) -> pl.DataFrame:
    """OOF panel slice scored by defensive/vol structure (crisis sleeve)."""
    d = panel.filter(pl.col("date").is_between(OOF_START, OOF_END)).select(
        "date", "code", "industry_category", "trading_money", "unexplained_price_jump",
        "defensive_family_score", "pct_vol_60d", "pct_downside_vol_60d", "pct_drawdown_63d",
    )
    # Prefer high defensive, low vol, less deep drawdown percentile.
    d = d.with_columns(
        (
            pl.col("defensive_family_score").fill_null(0.5)
            - 0.40 * pl.col("pct_vol_60d").fill_null(0.5)
            - 0.30 * pl.col("pct_downside_vol_60d").fill_null(0.5)
            - 0.20 * pl.col("pct_drawdown_63d").fill_null(0.5)
        ).alias("score")
    )
    return d.select(
        "date", "code", "industry_category", "trading_money", "unexplained_price_jump", "score"
    ).sort(["date", "code"])


def merge_orders_crisis_sleeve(
    tech_orders: pl.DataFrame,
    def_orders: pl.DataFrame,
    crisis_by_date: dict[date, bool],
) -> pl.DataFrame:
    """On crisis signal dates use defensive orders; else TECH2/C4 orders."""
    tech = {d: g for (d,), g in tech_orders.partition_by("signal_date", as_dict=True).items()}
    deff = {d: g for (d,), g in def_orders.partition_by("signal_date", as_dict=True).items()}
    dates = sorted(set(tech) | set(deff))
    pieces = []
    for d in dates:
        use_def = bool(crisis_by_date.get(d, False))
        g = deff.get(d) if use_def else tech.get(d)
        if g is None:
            g = tech.get(d) or deff.get(d)
        if g is not None:
            pieces.append(g)
    return pl.concat(pieces).sort(["signal_date", "code"]) if pieces else tech_orders


def add_crisis_rebalance_dates(
    scored: pl.DataFrame,
    calendar: list[date],
    crisis_by_date: dict[date, bool],
    base_every: int,
    min_gap: int = 5,
) -> list[date]:
    """Base grid plus crisis on/off transition dates (responsive entry)."""
    signal_pool = sorted(scored["date"].unique().to_list())
    base = set(signal_pool[::base_every])
    extras: list[date] = []
    last_extra = None
    prev = bool(crisis_by_date.get(signal_pool[0], False)) if signal_pool else False
    cal_index = {d: i for i, d in enumerate(calendar)}
    for d in signal_pool:
        cur = bool(crisis_by_date.get(d, False))
        if cur != prev:
            if last_extra is None or (cal_index[d] - cal_index[last_extra]) >= min_gap:
                extras.append(d)
                last_extra = d
            prev = cur
    return sorted(base | set(extras))


def orders_on_dates(scored: pl.DataFrame, calendar: list[date], signal_dates: list[date], cfg: dict) -> pl.DataFrame:
    """Like buffered_orders_ext but with explicit signal date set."""
    # Reuse buffered_orders_ext by filtering scored to only keep ranks on desired cadence:
    # simplest approach: call buffered_orders_ext then keep only signal_dates — WRONG (stateful holds).
    # Instead temporarily thin the dataframe dates... actually buffered uses [::rebalance_every].
    # Build a fake calendar stride by marking only signal dates present densely.
    # Practical approach: run custom loop copying buffered_orders_ext with provided signal_dates.
    import math as _math
    d = r1.add_neutral_score(scored, cfg["neutralization"])
    next_date = {calendar[i]: calendar[i + 1] for i in range(len(calendar) - 1)}
    groups = {
        (day,): g
        for (day,), g in d.filter(pl.col("date").is_in(signal_dates)).partition_by("date", as_dict=True).items()
    }
    held: list[str] = []
    rows: list[dict] = []
    exit_rank = int(_math.ceil(cfg["top_k"] * cfg["exit_multiple"]))
    for day in signal_dates:
        if day not in next_date or (day,) not in groups:
            continue
        candidates = (
            groups[(day,)]
            .filter((pl.col("trading_money") >= cfg["liquidity_floor"]) & ~pl.col("unexplained_price_jump"))
            .sort(["neutral_score", "trading_money", "code"], descending=[True, True, False])
        )
        ranked = []
        for i, rec in enumerate(candidates.iter_rows(named=True), 1):
            rec["rank"] = i
            ranked.append(rec)
        by_code = {rec["code"]: rec for rec in ranked}
        selected: list[str] = []
        industry_counts: dict[str, int] = {}
        for code in held:
            r = by_code.get(code)
            if r is None or r["rank"] > exit_rank:
                continue
            industry = r["industry_category"] or "UNKNOWN"
            if industry_counts.get(industry, 0) < cfg["industry_cap"]:
                selected.append(code)
                industry_counts[industry] = industry_counts.get(industry, 0) + 1
        for r in ranked:
            if len(selected) >= cfg["top_k"]:
                break
            code = r["code"]
            industry = r["industry_category"] or "UNKNOWN"
            if code in selected or industry_counts.get(industry, 0) >= cfg["industry_cap"]:
                continue
            # replace_rank_gap vs worst held
            if held and cfg.get("replace_rank_gap", 0) > 0:
                held_ranks = [by_code[c]["rank"] for c in held if c in by_code]
                if held_ranks and r["rank"] > min(held_ranks) + cfg["replace_rank_gap"] and len(selected) >= min(len(held), cfg["top_k"]):
                    continue
            selected.append(code)
            industry_counts[industry] = industry_counts.get(industry, 0) + 1
        held = selected
        n = max(len(selected), 1)
        weight = 1.0 / n
        exec_d = next_date[day]
        for code in selected:
            rows.append({
                "signal_date": day,
                "execution_date": exec_d,
                "code": code,
                "target_weight": weight,
                "industry_category": (by_code[code]["industry_category"] if code in by_code else None),
            })
    return pl.DataFrame(rows) if rows else pl.DataFrame(schema={
        "signal_date": pl.Date, "execution_date": pl.Date, "code": pl.String,
        "target_weight": pl.Float64, "industry_category": pl.String,
    })


def evaluate_nav(orders: pl.DataFrame, execution: pl.DataFrame, name: str, crisis_dates: set[date]) -> dict:
    nav, trades = a3.simulate(orders, execution, OOF_START, OOF_END)
    proxy = a3.market_proxy(execution, OOF_START, OOF_END)
    metric = a3.metrics(nav, trades, name)
    _, stats = a3.compare(nav, proxy)
    crisis = period_metrics(nav, proxy, crisis_dates)
    cagr, mdd, turn = metric.get("cagr"), metric.get("max_drawdown"), metric.get("average_daily_turnover")
    boot = stats.get("block_bootstrap_positive_probability")
    out = {
        "challenger": name,
        "cagr": cagr,
        "max_drawdown": mdd,
        "utility": (cagr or 0.0) - 0.5 * abs(mdd or 0.0),
        "average_daily_turnover": turn,
        "block_bootstrap_positive_probability": boot,
        "mean_daily_excess": stats.get("mean_daily_excess"),
        "hac_t_stat": stats.get("hac_t_stat"),
        "mean_gross_exposure": mean_gross_exposure(nav),
        "ending_nav": metric.get("ending_nav"),
        "turnover_gate_pass": bool((turn or 9) <= TURNOVER_CEILING),
        "bootstrap_gate_pass": bool((boot or 0) >= BOOTSTRAP_GATE),
        **{f"c_{k}": v for k, v in crisis.items()},
    }
    out["both_gates_pass"] = bool(out["turnover_gate_pass"] and out["bootstrap_gate_pass"])
    out["crisis_excess_nonneg"] = bool((out["c_crisis_mean_excess"] or -9) >= 0.0)
    return out, nav


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--oof-scores", type=Path, required=True)
    ap.add_argument("--panel", type=Path, required=True)
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

    print("building market crisis state ...", flush=True)
    mkt = attach_crisis(build_market_state(execution))
    mkt_oof = mkt.filter(pl.col("date").is_between(OOF_START, OOF_END))
    crisis_by_date = {r["date"]: bool(r["crisis"]) for r in mkt.iter_rows(named=True)}
    crisis_dates = {d for d, c in crisis_by_date.items() if c and OOF_START <= d <= OOF_END}
    mkt_oof.select("date", "dd120", "vol20", "breadth60", "crisis_votes", "crisis").write_csv(
        out / "outputs" / "stage7_oof_crisis_flags.csv"
    )
    print(
        f"  OOF crisis days={len(crisis_dates)} / {mkt_oof.height} "
        f"({100*len(crisis_dates)/max(mkt_oof.height,1):.1f}%)",
        flush=True,
    )

    print("building TECH2/C4 and DEFENSIVE orders ...", flush=True)
    tech_orders, _ = buffered_orders_ext(scored, calendar, **C4)
    def_scores = build_defensive_scores(panel, calendar, scored["date"])
    def_orders, _ = buffered_orders_ext(def_scores, calendar, **C4)

    # Crisis-responsive date set
    resp_dates = add_crisis_rebalance_dates(scored, calendar, crisis_by_date, C4["rebalance_every"], min_gap=5)
    tech_resp = orders_on_dates(scored, calendar, resp_dates, C4)
    def_resp = orders_on_dates(def_scores, calendar, resp_dates, C4)

    sleeve = merge_orders_crisis_sleeve(tech_orders, def_orders, crisis_by_date)
    sleeve_resp = merge_orders_crisis_sleeve(tech_resp, def_resp, crisis_by_date)

    def _cash_map(orders: pl.DataFrame, crisis_scale: float) -> dict[date, float]:
        return {
            d: (crisis_scale if crisis_by_date.get(d, False) else 1.0)
            for d in orders["signal_date"].unique().to_list()
        }

    challengers: dict[str, pl.DataFrame] = {
        "BASE_FULL": tech_orders,
        "CRISIS_CASH_050": scale_orders(tech_orders, _cash_map(tech_orders, 0.50)),
        "CRISIS_CASH_025": scale_orders(tech_orders, _cash_map(tech_orders, 0.25)),
        "CRISIS_CASH_000": scale_orders(tech_orders, _cash_map(tech_orders, 0.0)),
        "CRISIS_SLEEVE_DEF": sleeve,
        "CRISIS_SLEEVE_DEF_CASH050": scale_orders(sleeve, _cash_map(sleeve, 0.50)),
        "CRISIS_RESP_CASH_050": scale_orders(tech_resp, _cash_map(tech_resp, 0.50)),
        "CRISIS_RESP_SLEEVE_DEF": sleeve_resp,
        "CRISIS_RESP_SLEEVE_DEF_CASH050": scale_orders(sleeve_resp, _cash_map(sleeve_resp, 0.50)),
    }

    rows = []
    for name, orders in challengers.items():
        print(f"evaluating {name} ...", flush=True)
        metrics, nav = evaluate_nav(orders, execution, name, crisis_dates)
        metrics["is_baseline"] = name == "BASE_FULL"
        rows.append(metrics)
        nav.write_csv(out / "outputs" / f"stage7_{name.lower()}_oof_daily_nav.csv")
        print(
            f"  CAGR={metrics['cagr']:.4f} MDD={metrics['max_drawdown']:.4f} util={metrics['utility']:.4f} "
            f"boot={metrics['block_bootstrap_positive_probability']} "
            f"crisis_ex={metrics['c_crisis_mean_excess']} "
            f"crisis_ret={metrics['c_crisis_strategy_compound']} both={metrics['both_gates_pass']}",
            flush=True,
        )

    result = pl.DataFrame(rows).sort(
        ["both_gates_pass", "crisis_excess_nonneg", "utility", "c_crisis_mean_excess"],
        descending=[True, True, True, True],
    )
    result.write_csv(out / "outputs" / "stage7_crisis_challenger_oof_grid.csv")

    baseline = next(r for r in rows if r["is_baseline"])
    dual = [r for r in rows if r["both_gates_pass"] and not r["is_baseline"]]
    # Winner: dual-gate AND (crisis excess >= 0 OR better than baseline crisis excess)
    # AND utility >= baseline utility - small epsilon (don't destroy overall)
    candidates = []
    for r in dual:
        cex = r["c_crisis_mean_excess"]
        bex = baseline["c_crisis_mean_excess"]
        crisis_ok = (cex is not None) and ((cex >= 0.0) or (bex is not None and cex > bex + 1e-8))
        util_ok = (r["utility"] or -9) >= (baseline["utility"] or -9) - 0.01
        if crisis_ok and util_ok:
            candidates.append(r)
        r["crisis_screen_pass"] = bool(crisis_ok)
        r["util_screen_pass"] = bool(util_ok)

    candidates_sorted = sorted(
        candidates,
        key=lambda r: (
            -int(r["crisis_excess_nonneg"]),
            -(r["c_crisis_mean_excess"] or -9),
            -(r["utility"] or -9),
            abs(r["max_drawdown"] or 9),
        ),
    )
    winner = candidates_sorted[0] if candidates_sorted else None
    decision = (
        "OOF_NEW_CRISIS_CHALLENGER_DUAL_GATE_WINNER"
        if winner
        else "OOF_NO_NEW_CRISIS_CHALLENGER_DUAL_GATE_WINNER"
    )

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "STAGE7_CRISIS_CHALLENGER_OOF",
        "window": "2011-2018 OOF only",
        "crisis_definition": CRISIS_DEF,
        "oof_crisis_day_share": baseline["c_crisis_day_share"],
        "oof_n_crisis_days": baseline["c_n_crisis_days"],
        "alpha_frozen": "TECH2 OOF scores + C4 wrapper",
        "e45_touched": False,
        "no_retune_prior_locks": True,
        "baseline": baseline,
        "n_challengers": len(rows),
        "n_both_pass_new": len(dual),
        "n_candidates": len(candidates),
        "research_decision": decision,
        "recommended": winner,
        "top_candidates": candidates_sorted[:5],
        "all_dual_gate": dual,
        "gates_remain_experimental": True,
        "no_promotion": True,
    }
    (out / "reports" / "stage7_crisis_challenger_oof_summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n"
    )

    lines = [
        "# Stage-7 Crisis Challenger OOF",
        "",
        "Frozen alpha: TECH2 + C4. **E45 not edited.** Selection: 2011–2018 OOF.",
        f"Crisis def: `{CRISIS_DEF['name']}` (votes≥2, hysteresis 2/5).",
        f"OOF crisis day share: **{100*(baseline['c_crisis_day_share'] or 0):.1f}%** "
        f"({baseline['c_n_crisis_days']} days).",
        "",
        f"## Decision: `{decision}`",
        "",
        f"Baseline crisis mean excess={baseline['c_crisis_mean_excess']}, "
        f"crisis compound={baseline['c_crisis_strategy_compound']}, "
        f"util={baseline['utility']:.4f}, boot={baseline['block_bootstrap_positive_probability']}",
        "",
        "| challenger | CAGR | MDD | util | boot | crisis_ex | crisis_ret | crisis≥0 | both |",
        "|---|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for r in result.to_dicts():
        lines.append(
            f"| {r['challenger']} | {100*r['cagr']:.2f}% | {100*r['max_drawdown']:.2f}% | {r['utility']:.4f} | "
            f"{r['block_bootstrap_positive_probability']:.4f} | "
            f"{r['c_crisis_mean_excess']:.6f} | "
            f"{100*(r['c_crisis_strategy_compound'] or 0):.2f}% | "
            f"{r['crisis_excess_nonneg']} | {r['both_gates_pass']} |"
        )
    if winner:
        lines += [
            "",
            "## Recommended (OOF only — not yet held-out)",
            "",
            f"- `{winner['challenger']}`",
            f"- util={winner['utility']:.4f}, MDD={winner['max_drawdown']:.4f}, "
            f"boot={winner['block_bootstrap_positive_probability']}",
            f"- crisis_mean_excess={winner['c_crisis_mean_excess']}, "
            f"crisis_compound={winner['c_crisis_strategy_compound']}",
            "",
            "Next: lock as C7A1 and run held-out once (no retune).",
            "",
        ]
    else:
        lines += [
            "",
            "No dual-gate challenger clears the crisis screen without wrecking utility.",
            "Do not held-out near-misses. Do not edit E45 in place.",
            "",
        ]
    lines += ["Artifact: `reports/stage7_crisis_challenger_oof_summary.json`", ""]
    (out / "E50-A3-R1_STAGE7_CRISIS_CHALLENGER_OOF.md").write_text("\n".join(lines))
    print(json.dumps({
        "research_decision": decision,
        "oof_crisis_day_share": baseline["c_crisis_day_share"],
        "baseline_crisis_excess": baseline["c_crisis_mean_excess"],
        "n_candidates": len(candidates),
        "winner": None if not winner else {
            "challenger": winner["challenger"],
            "utility": winner["utility"],
            "mdd": winner["max_drawdown"],
            "boot": winner["block_bootstrap_positive_probability"],
            "crisis_mean_excess": winner["c_crisis_mean_excess"],
            "crisis_compound": winner["c_crisis_strategy_compound"],
        },
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
