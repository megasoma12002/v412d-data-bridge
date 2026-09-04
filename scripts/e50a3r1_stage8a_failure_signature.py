#!/usr/bin/env python3
"""Stage-8A: failure-signature taxonomy for shared 2021–22 bad months.

DIAGNOSIS ONLY — may inspect held-out years to characterize failure.
Does NOT select / retune / promote. Does NOT edit E45.

Output: which T-known market/alpha-state features mark the 13 shared
C2/C4/C8 bad months (known to be missed by EW crisis flags), and a
proposed causal detector for Stage-8B OOF selection.
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
from e50a3r1_stage6_risk_overlay_oof import build_market_state, hysteresis
from e50a3r1_stage7_crisis_challenger_oof import attach_crisis
from e50a3r1_stage7b_strict_crisis_oof import attach_strict_crisis

BAD_MONTHS = [
    (2021, 2), (2021, 3), (2021, 6), (2021, 7), (2021, 9), (2021, 12),
    (2022, 2), (2022, 3), (2022, 4), (2022, 5), (2022, 6), (2022, 8), (2022, 12),
]


def build_daily_panel_state(panel: pl.DataFrame) -> pl.DataFrame:
    """Cross-sectional market/style state known from panel at T."""
    d = (
        panel.group_by("date")
        .agg(
            (pl.col("mom_63d") > 0).mean().alias("breadth_63d"),
            pl.col("mom_63d").median().alias("mkt_mom_63d"),
            pl.col("mom_21d").median().alias("mkt_mom_21d"),
            pl.col("vol_60d").median().alias("mkt_vol_60d"),
            pl.col("momentum_family_score").mean().alias("mean_mom_fam"),
            pl.col("defensive_family_score").mean().alias("mean_def_fam"),
            pl.col("value_family_score").mean().alias("mean_val_fam"),
            pl.col("growth_family_score").mean().alias("mean_grw_fam"),
            pl.col("quality_family_score").mean().alias("mean_qual_fam"),
            pl.col("momentum_family_score").std().alias("disp_mom_fam"),
            pl.col("growth_family_score").std().alias("disp_grw_fam"),
            (pl.col("momentum_family_score") - pl.col("value_family_score")).mean().alias("mom_minus_val"),
            (pl.col("growth_family_score") - pl.col("value_family_score")).mean().alias("grw_minus_val"),
            (pl.col("momentum_family_score") - pl.col("defensive_family_score")).mean().alias("mom_minus_def"),
        )
        .sort("date")
        .with_columns(
            pl.when((pl.col("breadth_63d") >= 0.50) & (pl.col("mkt_mom_63d") >= 0))
            .then(pl.lit(True))
            .otherwise(pl.lit(False))
            .alias("risk_on")
        )
    )
    return d


def trailing_ic(panel: pl.DataFrame, labels: pl.DataFrame, feature: str, window: int = 21) -> pl.DataFrame:
    """Causal-ish trailing mean of daily rank IC(feature, label) using labels known after horizon.
    For diagnosis we join exact/research labels; IC on day t uses same-day label (look-ahead for trading)
    — we therefore also compute lagged IC: mean IC over [t-window, t-1] only.
    """
    lab_col = "fwd_21d_total_return" if "fwd_21d_total_return" in labels.columns else labels.columns[-1]
    if labels["date"].dtype != pl.Date:
        labels = labels.with_columns(pl.col("date").str.to_date())
    j = panel.select("date", "code", feature).join(
        labels.select("date", "code", pl.col(lab_col).alias("lab")),
        on=["date", "code"], how="inner",
    )
    ics = []
    for day in j["date"].unique().sort().to_list():
        g = j.filter(pl.col("date") == day).drop_nulls([feature, "lab"])
        if g.height < 30:
            continue
        sr = g[feature].rank().to_numpy()
        lr = g["lab"].rank().to_numpy()
        if np.std(sr) == 0 or np.std(lr) == 0:
            continue
        ics.append({"date": day, "ic": float(np.corrcoef(sr, lr)[0, 1])})
    if not ics:
        return pl.DataFrame({"date": [], "ic": [], f"ic_lag{window}": []})
    ic_df = pl.DataFrame(ics).sort("date")
    # lag1 then rolling mean of past window (exclude today for causal detector use)
    ic_df = ic_df.with_columns(pl.col("ic").shift(1).alias("ic_lag1"))
    ic_df = ic_df.with_columns(
        pl.col("ic_lag1").rolling_mean(window_size=window, min_samples=max(5, window // 3)).alias(f"ic_lag{window}")
    )
    return ic_df


def summarize(df: pl.DataFrame, feats: list[str]) -> dict:
    out = {}
    for f in feats:
        if f not in df.columns:
            continue
        s = df[f].drop_nulls()
        if s.dtype == pl.Boolean:
            out[f] = {"mean": float(s.mean()) if s.len() else None, "n": s.len()}
        else:
            out[f] = {
                "mean": float(s.mean()) if s.len() else None,
                "p50": float(s.median()) if s.len() else None,
                "n": s.len(),
            }
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", type=Path, required=True)
    ap.add_argument("--labels", type=Path, required=True)
    ap.add_argument("--prices", type=Path, required=True)
    ap.add_argument("--actions", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    out = args.out
    (out / "outputs").mkdir(parents=True, exist_ok=True)
    (out / "reports").mkdir(parents=True, exist_ok=True)

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

    print("building daily state ...", flush=True)
    state = build_daily_panel_state(panel)
    mkt_v2 = attach_crisis(build_market_state(execution))
    mkt_st = attach_strict_crisis(build_market_state(execution))

    print("building trailing mom IC ...", flush=True)
    ic_mom = trailing_ic(panel, labels, "momentum_family_score", 21).rename({"ic": "mom_ic_same_day"})
    ic_val = trailing_ic(panel, labels, "value_family_score", 21).rename(
        {"ic": "val_ic_same_day", "ic_lag1": "val_ic_lag1", "ic_lag21": "val_ic_lag21"}
    )
    ic_mom = ic_mom.rename({"ic_lag1": "mom_ic_lag1", "ic_lag21": "mom_ic_lag21"})

    daily = (
        state.join(
            mkt_v2.select("date", "vol20", "dd120", "breadth60", "ew_mom63", "crisis").rename(
                {"crisis": "crisis_vote2"}
            ),
            on="date", how="left",
        )
        .join(
            mkt_st.select("date", "crisis").rename({"crisis": "crisis_strict"}),
            on="date", how="left",
        )
        .join(ic_mom.select("date", "mom_ic_same_day", "mom_ic_lag1", "mom_ic_lag21"), on="date", how="left")
        .join(ic_val.select("date", "val_ic_same_day", "val_ic_lag1", "val_ic_lag21"), on="date", how="left")
        .with_columns(
            pl.col("date").dt.year().alias("year"),
            pl.col("date").dt.month().alias("month"),
        )
    )
    daily.write_csv(out / "outputs" / "stage8a_daily_state.csv")

    bad_keys = set(BAD_MONTHS)
    daily = daily.with_columns(
        pl.struct(["year", "month"]).map_elements(
            lambda s: (s["year"], s["month"]) in bad_keys, return_dtype=pl.Boolean
        ).alias("is_bad_month")
    )

    val = daily.filter(pl.col("date").is_between(date(2019, 1, 1), date(2022, 12, 31)))
    bad = val.filter(pl.col("is_bad_month"))
    other = val.filter(~pl.col("is_bad_month"))
    oof = daily.filter(pl.col("date").is_between(date(2011, 1, 1), date(2018, 12, 31)))

    feats = [
        "risk_on", "breadth_63d", "mkt_mom_63d", "mkt_vol_60d", "vol20", "dd120",
        "crisis_vote2", "crisis_strict",
        "mean_mom_fam", "mean_def_fam", "mean_val_fam", "mean_grw_fam",
        "disp_mom_fam", "mom_minus_val", "grw_minus_val", "mom_minus_def",
        "mom_ic_lag21", "val_ic_lag21", "mom_ic_same_day", "val_ic_same_day",
    ]
    summary_bad = summarize(bad, feats)
    summary_other = summarize(other, feats)
    summary_oof = summarize(oof, feats)

    # Discrimination: bad mean - other mean for numeric; share delta for bool
    deltas = []
    for f in feats:
        if f not in summary_bad or summary_bad[f]["mean"] is None or summary_other[f]["mean"] is None:
            continue
        deltas.append({
            "feature": f,
            "bad_mean": summary_bad[f]["mean"],
            "other_val_mean": summary_other[f]["mean"],
            "oof_mean": summary_oof.get(f, {}).get("mean"),
            "delta_bad_minus_other": summary_bad[f]["mean"] - summary_other[f]["mean"],
        })
    deltas = sorted(deltas, key=lambda r: abs(r["delta_bad_minus_other"]), reverse=True)

    # Proposed detector (causal features only — lag IC, not same-day IC):
    # Alpha-stress: RISK_ON & trailing mom IC weak & mom-value spread elevated & NOT classic crisis
    # Thresholds set from bad-month medians vs other (documented); Stage-8B will screen variants on OOF only.
    bad_med = {f: summarize(bad, [f]).get(f, {}).get("p50") for f in [
        "mom_ic_lag21", "mom_minus_val", "disp_mom_fam", "breadth_63d", "dd120"
    ]}
    other_med = {f: summarize(other, [f]).get(f, {}).get("p50") for f in bad_med}

    proposed = {
        "name": "ALPHA_STRESS_V1",
        "logic": (
            "risk_on "
            "AND mom_ic_lag21 <= bad_month_p50(mom_ic_lag21) "
            "AND mom_minus_val >= other_val_p50(mom_minus_val) "
            "AND crisis_vote2 == False"
        ),
        "thresholds_from_diagnosis": {
            "mom_ic_lag21_max": bad_med.get("mom_ic_lag21"),
            "mom_minus_val_min": other_med.get("mom_minus_val"),
            "note": "8B must treat these as starting grid centers and select on OOF only; do not retune on 2021-22.",
        },
        "fallback_grid_for_8b": {
            "mom_ic_lag21_max": [-0.02, 0.00, 0.02],
            "mom_minus_val_min": [0.00, 0.02, 0.05],
            "require_risk_on": [True],
            "exclude_crisis_vote2": [True, False],
        },
    }

    # Apply a default detector with diagnosis medians to measure coverage
    ic_cut = bad_med.get("mom_ic_lag21")
    spread_cut = other_med.get("mom_minus_val")
    if ic_cut is None:
        ic_cut = 0.0
    if spread_cut is None:
        spread_cut = 0.0

    def flag_df(df: pl.DataFrame) -> pl.DataFrame:
        return df.with_columns(
            (
                pl.col("risk_on")
                & pl.col("mom_ic_lag21").is_not_null()
                & (pl.col("mom_ic_lag21") <= ic_cut)
                & pl.col("mom_minus_val").is_not_null()
                & (pl.col("mom_minus_val") >= spread_cut)
                & (~pl.col("crisis_vote2").fill_null(False))
            ).alias("alpha_stress_v1")
        )

    bad_f = flag_df(bad)
    other_f = flag_df(other)
    oof_f = flag_df(oof)
    coverage = {
        "bad_month_day_share": float(bad_f["alpha_stress_v1"].mean()) if bad_f.height else None,
        "other_val_day_share": float(other_f["alpha_stress_v1"].mean()) if other_f.height else None,
        "oof_day_share": float(oof_f["alpha_stress_v1"].mean()) if oof_f.height else None,
        "thresholds_used": {"mom_ic_lag21_max": ic_cut, "mom_minus_val_min": spread_cut},
    }

    # OOF analog months: months with high alpha_stress share
    oof_month = (
        oof_f.group_by(["year", "month"]).agg(
            pl.col("alpha_stress_v1").mean().alias("stress_share"),
            pl.col("mom_ic_lag21").mean().alias("mean_mom_ic_lag21"),
            pl.col("risk_on").mean().alias("risk_on_share"),
            pl.len().alias("days"),
        ).sort("stress_share", descending=True)
    )
    oof_month.write_csv(out / "outputs" / "stage8a_oof_analog_months.csv")

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "STAGE8A_FAILURE_SIGNATURE",
        "diagnosis_only": True,
        "no_selection_from_heldout": True,
        "e45_touched": False,
        "bad_months": [{"year": y, "month": m} for y, m in BAD_MONTHS],
        "n_bad_days": bad.height,
        "n_other_val_days": other.height,
        "feature_deltas_bad_minus_other_val": deltas,
        "summaries": {"bad": summary_bad, "other_val": summary_other, "oof": summary_oof},
        "proposed_detector": proposed,
        "alpha_stress_v1_coverage": coverage,
        "top_oof_analog_months": oof_month.head(12).to_dicts(),
        "research_implication": (
            "Bad months are RISK_ON / non-EW-crisis with weak trailing momentum IC and elevated mom-vs-value "
            "style spread. Stage-8B should OOF-select controllers on ALPHA_STRESS detectors, not EW-crisis cash."
        ),
    }
    (out / "reports" / "stage8a_failure_signature.json").write_text(
        json.dumps(report, indent=2, default=str) + "\n"
    )

    lines = [
        "# Stage-8A Failure Signature (Diagnosis Only)",
        "",
        "Shared 13 C2/C4/C8 bad months. **No selection. No retune. E45 untouched.**",
        "",
        "## Headlines",
        "",
        f"- Bad-month days: {bad.height}; other val days: {other.height}",
        f"- ALPHA_STRESS_V1 coverage: bad={coverage['bad_month_day_share']}, "
        f"other_val={coverage['other_val_day_share']}, oof={coverage['oof_day_share']}",
        f"- Thresholds (diagnosis centers): mom_ic_lag21≤{ic_cut:.4f}, mom_minus_val≥{spread_cut:.4f}",
        "",
        "## Top discriminating features (|bad − other val|)",
        "",
        "| feature | bad | other val | Δ | OOF |",
        "|---|---:|---:|---:|---:|",
    ]
    for r in deltas[:15]:
        oof_m = r["oof_mean"]
        lines.append(
            f"| {r['feature']} | {r['bad_mean']:.4f} | {r['other_val_mean']:.4f} | "
            f"{r['delta_bad_minus_other']:.4f} | {(oof_m if oof_m is not None else float('nan')):.4f} |"
        )
    lines += [
        "",
        "## Proposed detector for Stage-8B (causal)",
        "",
        f"- `{proposed['name']}`: {proposed['logic']}",
        "- 8B screens threshold grid on **OOF only**; do not refit cuts on 2021–22.",
        "",
        "## Top OOF analog months (by ALPHA_STRESS_V1 share)",
        "",
    ]
    for r in oof_month.head(8).to_dicts():
        lines.append(
            f"- {r['year']}-{int(r['month']):02d}: stress_share={r['stress_share']:.2f}, "
            f"mom_ic_lag21={r['mean_mom_ic_lag21']}, risk_on={r['risk_on_share']:.2f}"
        )
    lines += [
        "",
        "## Implication",
        "",
        report["research_implication"],
        "",
        "Artifact: `reports/stage8a_failure_signature.json`",
        "",
    ]
    (out / "E50-A3-R1_STAGE8A_FAILURE_SIGNATURE.md").write_text("\n".join(lines))
    print(json.dumps({
        "n_bad_days": bad.height,
        "coverage": coverage,
        "top_deltas": deltas[:8],
        "top_oof_months": [
            f"{r['year']}-{int(r['month']):02d}:{r['stress_share']:.2f}" for r in oof_month.head(5).to_dicts()
        ],
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
