#!/usr/bin/env python3
"""Stage-4B: feature attribution on shared 2021–2022 bad months (diagnosis only).

Uses C2/C4/C8 common negative-excess months from Stage-3 autopsy.
Compares univariate rank IC of atomic features in bad months vs other validation
months, and buy-vs-universe feature tilts for C4 trades.

Diagnosis may inspect held-out years. Does NOT select / retune / promote.
"""
from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import polars as pl

ATOMIC = [
    "pct_mom_12_1", "pct_mom_63d", "pct_mom_126d", "pct_reversal_5d",
    "pct_vol_60d", "pct_downside_vol_60d", "pct_drawdown_63d", "pct_amihud_20d",
    "pct_roa_ttm", "pct_roe_ttm", "pct_cfo_to_assets", "pct_accruals_to_assets",
    "pct_leverage", "pct_book_to_price_proxy", "pct_earnings_yield_proxy", "pct_sales_yield_proxy",
    "pct_monthly_revenue_yoy", "pct_revenue_3m_yoy", "pct_revenue_yoy_acceleration",
    "pct_revenue_growth_yoy", "pct_net_income_growth_yoy", "pct_asset_growth_yoy",
    "momentum_family_score", "defensive_family_score", "quality_family_score",
    "growth_family_score", "value_family_score",
]
# Research forward return used as ranking label for diagnosis (not for selection).
LABEL = "fwd_21d_total_return"


def day_rank_ic(df: pl.DataFrame, feature: str, label: str) -> float | None:
    g = df.drop_nulls([feature, label])
    if g.height < 30:
        return None
    sr = g[feature].rank().to_numpy()
    lr = g[label].rank().to_numpy()
    if np.std(sr) == 0 or np.std(lr) == 0:
        return None
    return float(np.corrcoef(sr, lr)[0, 1])


def mean_ic_by_bucket(panel: pl.DataFrame, bad_keys: set[tuple[int, int]], features: list[str]) -> list[dict]:
    rows = []
    dates = panel.select(
        "date",
        pl.col("date").dt.year().alias("year"),
        pl.col("date").dt.month().alias("month"),
    ).unique().sort("date")
    bad_dates = set(
        dates.filter(
            pl.struct(["year", "month"]).map_elements(
                lambda s: (s["year"], s["month"]) in bad_keys, return_dtype=pl.Boolean
            )
        )["date"].to_list()
    )
    # faster: build year-month mark
    panel = panel.with_columns(
        pl.col("date").dt.year().alias("year"),
        pl.col("date").dt.month().alias("month"),
    )
    for feat in features:
        if feat not in panel.columns or label_col(panel) not in panel.columns:
            continue
        label = label_col(panel)
        bad_ics, other_ics = [], []
        for day in panel["date"].unique().to_list():
            day_df = panel.filter(pl.col("date") == day)
            ic = day_rank_ic(day_df, feat, label)
            if ic is None:
                continue
            y, m = int(day_df["year"][0]), int(day_df["month"][0])
            if (y, m) in bad_keys:
                bad_ics.append(ic)
            elif 2019 <= y <= 2022:
                other_ics.append(ic)
        rows.append({
            "feature": feat,
            "bad_month_mean_ic": float(np.mean(bad_ics)) if bad_ics else None,
            "bad_month_n_days": len(bad_ics),
            "other_val_mean_ic": float(np.mean(other_ics)) if other_ics else None,
            "other_val_n_days": len(other_ics),
            "delta_ic_bad_minus_other": (
                float(np.mean(bad_ics) - np.mean(other_ics)) if bad_ics and other_ics else None
            ),
        })
    return sorted(rows, key=lambda r: (r["delta_ic_bad_minus_other"] is not None, r["delta_ic_bad_minus_other"] or -9))


def label_col(panel: pl.DataFrame) -> str:
    for c in [LABEL, "forward_excess_21d", "target_rank"]:
        if c in panel.columns:
            return c
    raise RuntimeError("no label column")


def buy_tilt(trades: pl.DataFrame, panel: pl.DataFrame, bad_keys: set[tuple[int, int]], features: list[str]) -> list[dict]:
    buys = trades.filter(pl.col("side") == "BUY").with_columns(
        pl.col("signal_date").dt.year().alias("year"),
        pl.col("signal_date").dt.month().alias("month"),
    )
    bad_buys = buys.filter(
        pl.struct(["year", "month"]).map_elements(
            lambda s: (s["year"], s["month"]) in bad_keys, return_dtype=pl.Boolean
        )
    )
    if bad_buys.height == 0:
        return []
    joined = bad_buys.join(
        panel.rename({"date": "signal_date"}),
        on=["signal_date", "code"],
        how="left",
    )
    out = []
    for feat in features:
        if feat not in joined.columns:
            continue
        # universe same days
        days = bad_buys["signal_date"].unique().to_list()
        uni = panel.filter(pl.col("date").is_in(days)).drop_nulls([feat])
        buy_vals = joined.drop_nulls([feat])[feat].to_numpy()
        uni_vals = uni[feat].to_numpy()
        if len(buy_vals) < 5 or len(uni_vals) < 30:
            continue
        out.append({
            "feature": feat,
            "buy_mean": float(np.mean(buy_vals)),
            "universe_mean": float(np.mean(uni_vals)),
            "tilt_buy_minus_uni": float(np.mean(buy_vals) - np.mean(uni_vals)),
            "n_buys": int(len(buy_vals)),
        })
    return sorted(out, key=lambda r: abs(r["tilt_buy_minus_uni"]), reverse=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--panel", type=Path, required=True)
    ap.add_argument("--labels", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--autopsy-json", type=Path, required=True)
    args = ap.parse_args()
    out = args.out
    (out / "reports").mkdir(parents=True, exist_ok=True)

    autopsy = json.loads(args.autopsy_json.read_text())
    bad = [
        (int(m["year"]), int(m["month"]))
        for m in autopsy["common_negative_excess_months_all_refs"]
    ]
    bad_keys = set(bad)

    panel = pl.read_parquet(args.panel).sort(["date", "code"])
    labels = pl.read_parquet(args.labels)
    # normalize label name
    lab_cols = labels.columns
    label_name = LABEL if LABEL in lab_cols else [c for c in lab_cols if "excess" in c or "forward" in c][0]
    if "date" in labels.columns and labels["date"].dtype != pl.Date:
        labels = labels.with_columns(pl.col("date").str.to_date())
    panel = panel.join(
        labels.select("date", "code", pl.col(label_name).alias(LABEL)),
        on=["date", "code"],
        how="left",
    )

    print("computing bad-month univariate ICs ...", flush=True)
    # Speed: iterate days once
    feats = [f for f in ATOMIC if f in panel.columns]
    panel_val = panel.filter(
        pl.col("date").is_between(date(2019, 1, 1), date(2022, 12, 31))
    ).with_columns(
        pl.col("date").dt.year().alias("year"),
        pl.col("date").dt.month().alias("month"),
    )
    ic_accum = {f: {"bad": [], "other": []} for f in feats}
    for day in panel_val["date"].unique().to_list():
        day_df = panel_val.filter(pl.col("date") == day)
        y, m = int(day_df["year"][0]), int(day_df["month"][0])
        bucket = "bad" if (y, m) in bad_keys else "other"
        for feat in feats:
            ic = day_rank_ic(day_df, feat, LABEL)
            if ic is not None:
                ic_accum[feat][bucket].append(ic)

    ic_rows = []
    for feat, buckets in ic_accum.items():
        bad_ics, other_ics = buckets["bad"], buckets["other"]
        ic_rows.append({
            "feature": feat,
            "bad_month_mean_ic": float(np.mean(bad_ics)) if bad_ics else None,
            "bad_month_n_days": len(bad_ics),
            "other_val_mean_ic": float(np.mean(other_ics)) if other_ics else None,
            "other_val_n_days": len(other_ics),
            "delta_ic_bad_minus_other": (
                float(np.mean(bad_ics) - np.mean(other_ics)) if bad_ics and other_ics else None
            ),
        })
    ic_rows = sorted(
        ic_rows,
        key=lambda r: (r["delta_ic_bad_minus_other"] is not None, r["delta_ic_bad_minus_other"] or -99),
        reverse=True,
    )

    trades_path = out / "outputs" / "c4_validation_2019_2022_trades.csv"
    tilt_rows = []
    if trades_path.exists():
        trades = pl.read_csv(trades_path).with_columns(
            pl.col("signal_date").str.to_date(),
            pl.col("code").cast(pl.String),
        )
        print("computing C4 buy tilts in bad months ...", flush=True)
        tilt_rows = buy_tilt(trades, panel, bad_keys, feats)
    else:
        print(f"WARNING: missing {trades_path}; skipping buy tilts", flush=True)

    # Also OOF mean IC for guidance (selection-safe summary, not used to pick here)
    print("computing OOF univariate ICs (context only) ...", flush=True)
    panel_oof = panel.filter(pl.col("date").is_between(date(2011, 1, 1), date(2018, 12, 31)))
    oof_rows = []
    for feat in feats:
        ics = []
        for day in panel_oof["date"].unique().to_list():
            ic = day_rank_ic(panel_oof.filter(pl.col("date") == day), feat, LABEL)
            if ic is not None:
                ics.append(ic)
        oof_rows.append({
            "feature": feat,
            "oof_mean_ic": float(np.mean(ics)) if ics else None,
            "oof_n_days": len(ics),
        })
    oof_rows = sorted(oof_rows, key=lambda r: r["oof_mean_ic"] or -9, reverse=True)

    # Merge guidance table
    oof_map = {r["feature"]: r for r in oof_rows}
    guidance = []
    for r in ic_rows:
        o = oof_map.get(r["feature"], {})
        guidance.append({**r, **o})

    # Features that stay relatively resilient in bad months (higher delta) AND positive OOF IC
    resilient = [
        r for r in guidance
        if (r.get("oof_mean_ic") or 0) > 0.02
        and (r.get("delta_ic_bad_minus_other") or -9) > -0.02
    ][:10]
    fragile = [
        r for r in guidance
        if (r.get("oof_mean_ic") or 0) > 0.02
        and (r.get("delta_ic_bad_minus_other") is not None)
        and r["delta_ic_bad_minus_other"] < -0.03
    ][:10]

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "STAGE4_BAD_MONTH_ATTRIBUTION",
        "diagnosis_only": True,
        "no_retune": True,
        "no_selection_from_heldout": True,
        "common_bad_months": [{"year": y, "month": m} for y, m in sorted(bad_keys)],
        "n_bad_months": len(bad_keys),
        "univariate_ic_bad_vs_other_val": guidance,
        "oof_univariate_ic_context": oof_rows,
        "c4_buy_tilts_bad_months": tilt_rows[:20],
        "relatively_resilient_features": resilient,
        "fragile_in_bad_months": fragile,
        "research_implication": (
            "Bad-month IC gaps show which atomic signals weaken in shared failure months; "
            "use only as navigation for OOF atomic screens — do not select on held-out deltas."
        ),
    }
    (out / "reports" / "stage4_bad_month_attribution.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n"
    )

    lines = [
        "# Stage-4B Bad-Month Feature Attribution (Diagnosis Only)",
        "",
        "Shared C2/C4/C8 negative-excess months from Stage-3. **No retune. No held-out selection.**",
        "",
        f"Bad months (n={len(bad_keys)}): "
        + ", ".join(f"{y}-{m:02d}" for y, m in sorted(bad_keys)),
        "",
        "## Univariate rank IC: bad months vs other 2019–2022",
        "",
        "| feature | bad IC | other IC | Δ | OOF IC |",
        "|---|---:|---:|---:|---:|",
    ]
    for r in guidance[:25]:
        lines.append(
            f"| {r['feature']} | {r['bad_month_mean_ic']:.4f} | {r['other_val_mean_ic']:.4f} | "
            f"{r['delta_ic_bad_minus_other']:.4f} | {(r.get('oof_mean_ic') or 0):.4f} |"
        )
    lines += ["", "## Relatively resilient (OOF IC>0.02 and Δ>-0.02)", ""]
    for r in resilient:
        lines.append(
            f"- `{r['feature']}`: bad={r['bad_month_mean_ic']:.4f}, other={r['other_val_mean_ic']:.4f}, "
            f"OOF={r['oof_mean_ic']:.4f}"
        )
    lines += ["", "## Fragile in bad months (OOF IC>0.02 and Δ<-0.03)", ""]
    for r in fragile:
        lines.append(
            f"- `{r['feature']}`: bad={r['bad_month_mean_ic']:.4f}, other={r['other_val_mean_ic']:.4f}, "
            f"Δ={r['delta_ic_bad_minus_other']:.4f}"
        )
    if tilt_rows:
        lines += ["", "## C4 buy tilts in bad months (vs same-day universe)", ""]
        for r in tilt_rows[:12]:
            lines.append(
                f"- `{r['feature']}`: tilt={r['tilt_buy_minus_uni']:.4f} "
                f"(buy={r['buy_mean']:.3f}, uni={r['universe_mean']:.3f})"
            )
    lines += [
        "",
        "## Implication",
        "",
        summary["research_implication"],
        "",
        "Artifact: `reports/stage4_bad_month_attribution.json`",
        "",
    ]
    (out / "E50-A3-R1_STAGE4_BAD_MONTH_ATTRIBUTION.md").write_text("\n".join(lines))
    print(json.dumps({
        "n_bad_months": len(bad_keys),
        "top_resilient": [r["feature"] for r in resilient[:5]],
        "top_fragile": [r["feature"] for r in fragile[:5]],
        "top_tilts": [r["feature"] for r in tilt_rows[:5]],
    }, indent=2))


if __name__ == "__main__":
    main()
