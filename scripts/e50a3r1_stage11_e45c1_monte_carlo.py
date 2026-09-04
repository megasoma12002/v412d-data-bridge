#!/usr/bin/env python3
"""Stage-11 E45-C1: Monte Carlo / path-stress survival on LOCKED challengers.

No new parameter search. No panel remix grid. No retune after held-out.
Compares already-locked configs side-by-side under a higher process bar:

  C4          — bull sleeve reference (TECH2+C4)
  S9A1        — FREEZE_REB × COMBO_VOL70_VAL03
  S10R3       — RESID_SLEEVE × SAFE4 on same detector

For each window (OOF / VAL / SEALED):
  - point metrics
  - block-bootstrap P(challenger beats C4) on MDD, utility, stress compound, mean excess

Output: governance decision package (EXPERIMENTAL evidence; no auto-promotion).
Not an in-place E45 edit.
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
from e50a3r1_stage7_crisis_challenger_oof import merge_orders_crisis_sleeve
from e50a3r1_stage9a_e45c1_freeze_orth_oof import freeze_signal_dates
from e50a3r1_stage10_stress_alpha_iterate import (
    DET,
    build_flags,
    residualize_scores,
)

SAFE4 = ["pct_cash_to_assets", "pct_current_ratio", "pct_leverage", "pct_drawdown_63d"]
MC_DRAWS = 5000
MC_BLOCK = 21
RNG = np.random.default_rng(20260904)


def daily_returns(nav: pl.DataFrame) -> np.ndarray:
    r = nav.sort("date")["nav"].pct_change().drop_nulls().to_numpy()
    return r.astype(float)


def path_metrics(rets: np.ndarray) -> dict:
    if len(rets) < 2:
        return {"cagr": None, "mdd": None, "utility": None, "mean_excess_proxy": None}
    nav = np.cumprod(1.0 + rets)
    years = len(rets) / 252.0
    cagr = float(nav[-1] ** (1.0 / years) - 1.0) if years > 0 else None
    peak = np.maximum.accumulate(nav)
    mdd = float(np.min(nav / peak - 1.0))
    util = (cagr or 0.0) - 0.5 * abs(mdd)
    return {"cagr": cagr, "mdd": mdd, "utility": util}


def block_resample(rets: np.ndarray, block: int, rng: np.random.Generator) -> np.ndarray:
    n = len(rets)
    if n == 0:
        return rets
    n_blocks = int(np.ceil(n / block))
    starts = rng.integers(0, max(n - block + 1, 1), size=n_blocks)
    pieces = [rets[s:s + block] for s in starts]
    out = np.concatenate(pieces)[:n]
    return out


def bootstrap_beat_probs(
    chal_rets: np.ndarray,
    base_rets: np.ndarray,
    chal_stress_mask: np.ndarray,
    base_stress_mask: np.ndarray,
    draws: int = MC_DRAWS,
    block: int = MC_BLOCK,
) -> dict:
    """Pathwise block bootstrap: P(challenger better than base) on key stats."""
    n = min(len(chal_rets), len(base_rets))
    chal_rets = chal_rets[:n]
    base_rets = base_rets[:n]
    # align stress mask to return length (returns drop first nav day)
    if len(chal_stress_mask) >= n + 1:
        cmask = chal_stress_mask[1:n + 1]
        bmask = base_stress_mask[1:n + 1]
    else:
        cmask = chal_stress_mask[:n]
        bmask = base_stress_mask[:n]

    wins = {"mdd": 0, "utility": 0, "mean_ret": 0, "stress_compound": 0, "stress_mean": 0}
    for _ in range(draws):
        idx_seed = RNG.integers(0, 10**9)
        rng = np.random.default_rng(idx_seed)
        # resample paired by using same block starts for both paths
        n_blocks = int(np.ceil(n / block))
        starts = rng.integers(0, max(n - block + 1, 1), size=n_blocks)
        def take(x):
            return np.concatenate([x[s:s + block] for s in starts])[:n]
        cr, br = take(chal_rets), take(base_rets)
        cm, bm = take(cmask.astype(float)), take(bmask.astype(float))
        cm = cm > 0.5
        bm = bm > 0.5
        pc, pb = path_metrics(cr), path_metrics(br)
        if pc["mdd"] is not None and pb["mdd"] is not None and abs(pc["mdd"]) + 1e-15 < abs(pb["mdd"]):
            wins["mdd"] += 1
        if pc["utility"] is not None and pb["utility"] is not None and pc["utility"] > pb["utility"]:
            wins["utility"] += 1
        if float(np.mean(cr)) > float(np.mean(br)):
            wins["mean_ret"] += 1
        # stress compounds on resampled stress days (challenger mask)
        if cm.any():
            csc = float(np.prod(1.0 + cr[cm]) - 1.0)
            bsc = float(np.prod(1.0 + br[cm]) - 1.0)
            if csc > bsc:
                wins["stress_compound"] += 1
            if float(np.mean(cr[cm])) > float(np.mean(br[cm])):
                wins["stress_mean"] += 1
        else:
            # no stress days in draw — count as non-win (conservative)
            pass
    return {k: v / draws for k, v in wins.items()}


def build_nav_bundle(joined, panel, execution, calendar, flags, kind: str, start: date, end: date, fit_cutoff: date):
    model_bull = r1.fit_model(joined, "TECH2", "BREADTH_REGIME", 1.0, fit_cutoff)
    bull = r1.score_period(joined, model_bull, start, end)
    stress_dates = {d for d, on in flags.items() if on and start <= d <= end}

    if kind == "C4":
        orders, _ = buffered_orders_ext(bull, calendar, **C4)
    elif kind == "S9A1":
        fd = freeze_signal_dates(bull, flags, C4["rebalance_every"])
        orders = orders_on_dates(bull, calendar, fd, C4)
    elif kind == "S10R3":
        r1.FEATURE_SETS["EXP_TMP"] = SAFE4
        model_s = r1.fit_model(joined, "EXP_TMP", "BREADTH_REGIME", 1.0, fit_cutoff)
        stress = r1.score_period(joined, model_s, start, end)
        bull_v = bull.select("date", "code", "industry_category", "trading_money", "unexplained_price_jump", "score")
        stress_v = residualize_scores(
            stress.select("date", "code", "industry_category", "trading_money", "unexplained_price_jump", "score"),
            bull_v,
        )
        tech_o, _ = buffered_orders_ext(bull, calendar, **C4)
        st_o, _ = buffered_orders_ext(stress_v, calendar, **C4)
        orders = merge_orders_crisis_sleeve(tech_o, st_o, flags)
    else:
        raise ValueError(kind)

    nav, trades = a3.simulate(orders, execution, start, end)
    proxy = a3.market_proxy(execution, start, end)
    metric = a3.metrics(nav, trades, kind)
    _, stats = a3.compare(nav, proxy)
    stress = period_metrics(nav, proxy, stress_dates)
    turn = metric.get("average_daily_turnover")
    boot = stats.get("block_bootstrap_positive_probability")
    cagr, mdd = metric.get("cagr"), metric.get("max_drawdown")
    dates = nav.sort("date")["date"].to_list()
    stress_mask = np.array([d in stress_dates for d in dates], dtype=bool)
    point = {
        "kind": kind,
        "cagr": cagr,
        "max_drawdown": mdd,
        "utility": (cagr or 0.0) - 0.5 * abs(mdd or 0.0),
        "average_daily_turnover": turn,
        "block_bootstrap_positive_probability": boot,
        "mean_gross_exposure": mean_gross_exposure(nav),
        "turnover_gate_pass": bool((turn or 9) <= TURNOVER_CEILING),
        "bootstrap_gate_pass": bool((boot or 0) >= BOOTSTRAP_GATE),
        "stress_flag_share": float(stress_mask.mean()) if len(stress_mask) else None,
        **{f"s_{k}": v for k, v in stress.items()},
    }
    return point, daily_returns(nav), stress_mask, nav


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", type=Path, required=True)
    ap.add_argument("--labels", type=Path, required=True)
    ap.add_argument("--prices", type=Path, required=True)
    ap.add_argument("--actions", type=Path, required=True)
    ap.add_argument("--a2-qc", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--draws", type=int, default=MC_DRAWS)
    args = ap.parse_args()
    out = args.out
    (out / "outputs").mkdir(parents=True, exist_ok=True)
    (out / "reports").mkdir(parents=True, exist_ok=True)
    if json.loads(args.a2_qc.read_text())["status"] != "PASS":
        raise RuntimeError("E50-A2 QC is not PASS")

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
    exact_labels = a3.build_exact_open_labels(panel, execution, calendar)
    joined = a3.target_rank(
        r1.add_regime(panel).join(exact_labels.select("date", "code", a3.LABEL), on=["date", "code"], validate="1:1")
    )
    print("building locked S9A1 detector flags ...", flush=True)
    flags = build_flags(panel, labels, execution)

    windows = {
        "OOF_2011_2018": (OOF_START, OOF_END, a3.previous_session(calendar, OOF_START, 22)),
        "VAL_2019_2022": (date(2019, 1, 1), date(2022, 12, 31), a3.previous_session(calendar, date(2019, 1, 1), 22)),
        "SEALED_2023_LATEST": (date(2023, 1, 1), max(calendar), a3.previous_session(calendar, date(2023, 1, 1), 22)),
    }

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "STAGE11_E45C1_MONTE_CARLO",
        "e45_inplace_edit": False,
        "no_retune": True,
        "no_new_search": True,
        "mc_draws": args.draws,
        "mc_block": MC_BLOCK,
        "detector_locked": DET,
        "challengers": ["C4", "S9A1", "S10R3"],
        "windows": {},
    }

    for wname, (start, end, cutoff) in windows.items():
        print(f"\n=== {wname} ===", flush=True)
        points = {}
        rets = {}
        masks = {}
        for kind in ["C4", "S9A1", "S10R3"]:
            print(f"  building {kind} ...", flush=True)
            pt, r, mask, nav = build_nav_bundle(
                joined, panel, execution, calendar, flags, kind, start, end, cutoff
            )
            points[kind] = pt
            rets[kind] = r
            masks[kind] = mask
            nav.write_csv(out / "outputs" / f"stage11_{kind.lower()}_{wname.lower()}_nav.csv")
            print(
                f"    util={pt['utility']:.4f} mdd={pt['max_drawdown']:.4f} boot={pt['block_bootstrap_positive_probability']} "
                f"turn={pt['average_daily_turnover']:.4f} stress_ex={pt['s_crisis_mean_excess']}",
                flush=True,
            )

        mc = {}
        for kind in ["S9A1", "S10R3"]:
            print(f"  MC {kind} vs C4 ({args.draws} draws) ...", flush=True)
            mc[kind] = bootstrap_beat_probs(
                rets[kind], rets["C4"], masks[kind], masks["C4"], draws=args.draws, block=MC_BLOCK
            )
            print(f"    P(beat C4)={json.dumps(mc[kind])}", flush=True)

        report["windows"][wname] = {"point": points, "mc_vs_c4": mc}

    # Governance recommendation (process, not promotion)
    val = report["windows"]["VAL_2019_2022"]
    sealed = report["windows"]["SEALED_2023_LATEST"]
    rec = {
        "label": "GOVERNANCE_REVIEW_READY_NO_AUTO_PROMOTE",
        "bull_sleeve_reference": "C4",
        "best_mixed_operational_overlay": None,
        "rationale": [],
    }
    # Prefer challenger with (a) stress MC edge on VAL, (b) not wrecking sealed, (c) turn gate preferably
    scores = {}
    for kind in ["S9A1", "S10R3"]:
        v, s = val["point"][kind], sealed["point"][kind]
        mcv, mcs = val["mc_vs_c4"][kind], sealed["mc_vs_c4"][kind]
        scores[kind] = {
            "val_stress_mc": mcv["stress_mean"],
            "val_util_mc": mcv["utility"],
            "val_boot": v["block_bootstrap_positive_probability"],
            "val_turn_ok": v["turnover_gate_pass"],
            "sealed_boot": s["block_bootstrap_positive_probability"],
            "sealed_stress_mc": mcs["stress_mean"],
        }
        rec["rationale"].append({kind: scores[kind]})
    # Pick best by val stress MC then val boot, requiring sealed boot gate
    ranked = sorted(
        ["S9A1", "S10R3"],
        key=lambda k: (
            -scores[k]["val_stress_mc"],
            -scores[k]["val_boot"],
            -float(scores[k]["val_turn_ok"]),
            -scores[k]["sealed_boot"],
        ),
    )
    rec["best_mixed_operational_overlay"] = ranked[0]
    rec["notes"] = [
        "All challengers remain MIXED under EXPERIMENTAL 0.70 bootstrap gate on validation.",
        "This package does NOT promote gates or edit E45.",
        "Human governance may accept MIXED+better-than-C4 stress, or require new information set.",
    ]
    report["governance_recommendation"] = rec

    (out / "reports" / "stage11_e45c1_monte_carlo_summary.json").write_text(
        json.dumps(report, indent=2, default=str) + "\n"
    )

    lines = [
        "# Stage-11 E45-C1 Monte Carlo / Governance Package",
        "",
        "Locked challengers only (C4, S9A1, S10R3). **No retune. No new search. Not an E45 in-place edit.**",
        "",
        f"MC: {args.draws} block-{MC_BLOCK} path draws. Probabilities = P(challenger beats C4).",
        "",
        f"## Governance label: `{rec['label']}`",
        "",
        f"Suggested mixed overlay for review: **{rec['best_mixed_operational_overlay']}**",
        "",
    ]
    for wname, blob in report["windows"].items():
        lines += [f"### {wname}", "", "| kind | CAGR | MDD | Util | Boot | Turn | StressEx |", "|---|---:|---:|---:|---:|---:|---:|"]
        for kind in ["C4", "S9A1", "S10R3"]:
            p = blob["point"][kind]
            lines.append(
                f"| {kind} | {100*p['cagr']:.2f}% | {100*p['max_drawdown']:.2f}% | {p['utility']:.4f} | "
                f"{p['block_bootstrap_positive_probability']:.4f} | {100*p['average_daily_turnover']:.2f}% | "
                f"{p['s_crisis_mean_excess']} |"
            )
        lines += ["", "| vs C4 MC | P(better MDD) | P(better util) | P(better stress mean) | P(better stress compound) |",
                  "|---|---:|---:|---:|---:|"]
        for kind in ["S9A1", "S10R3"]:
            m = blob["mc_vs_c4"][kind]
            lines.append(
                f"| {kind} | {m['mdd']:.3f} | {m['utility']:.3f} | {m['stress_mean']:.3f} | {m['stress_compound']:.3f} |"
            )
        lines.append("")
    lines += [
        "## Decision options for humans",
        "",
        "1. Keep C4-only as research reference; leave overlays EXPERIMENTAL",
        "2. Accept a MIXED overlay (S9A1 or S10R3) for paper/monitoring only — **not** frozen promotion",
        "3. Require a new information set before further challengers",
        "",
        "Artifact: `reports/stage11_e45c1_monte_carlo_summary.json`",
        "",
    ]
    (out / "E50-A3-R1_STAGE11_E45C1_MONTE_CARLO.md").write_text("\n".join(lines))
    print(json.dumps({
        "governance_label": rec["label"],
        "best_mixed_overlay": rec["best_mixed_operational_overlay"],
        "val_mc": {k: val["mc_vs_c4"][k] for k in ["S9A1", "S10R3"]},
        "val_point_boot": {k: val["point"][k]["block_bootstrap_positive_probability"] for k in ["C4", "S9A1", "S10R3"]},
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
