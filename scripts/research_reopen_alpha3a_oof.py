#!/usr/bin/env python3
"""Alpha 3A Round-2b — minimal OOF probe on new-info features (no promotion).

Uses:
  - operating_income_yoy (PIT available_date)
  - amihud_20_lag1 (monthly)

Protocol lite: expand monthly → next-month return; walk-forward OOF by year;
no TECH2; no retune after looking at full sample (single pre-registered score).
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


def month_end_prices(pit_path: str, start: str = "2019-01-01") -> pd.DataFrame:
    import polars as pl

    df = (
        pl.scan_csv(pit_path, schema_overrides={"code": pl.String})
        .filter(pl.col("date") >= start)
        .select("date", "code", "close")
        .collect(engine="streaming")
        .to_pandas()
    )
    df["date"] = pd.to_datetime(df["date"])
    df = df.dropna(subset=["close"]).sort_values(["code", "date"])
    df["ym"] = df["date"].dt.to_period("M")
    # last close in month
    me = df.groupby(["code", "ym"], as_index=False).tail(1)
    return me.rename(columns={"date": "signal_date", "close": "px"})


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--feat-dir", type=Path, default=Path("repro/research-reopen-round2-20260904/alpha_3a_features"))
    ap.add_argument("--out", type=Path, default=Path("repro/research-reopen-round2-20260904/alpha_3a_oof"))
    ap.add_argument("--pit", default="/tmp/a0/point_in_time_universe.csv")
    args = ap.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    oi = pd.read_parquet(args.feat_dir / "operating_income_yoy_pit.parquet")
    ami = pd.read_parquet(args.feat_dir / "amihud_20_lag1_monthly.parquet")
    oi["available_date"] = pd.to_datetime(oi["available_date"])
    ami["date"] = pd.to_datetime(ami["date"])
    ami["ym"] = ami["date"].dt.to_period("M")

    print("month-end prices ...", flush=True)
    px = month_end_prices(args.pit)
    px = px.sort_values(["code", "ym"])
    px["next_ym"] = px.groupby("code")["ym"].shift(-1)
    px["next_px"] = px.groupby("code")["px"].shift(-1)
    px["fwd_ret"] = px["next_px"] / px["px"] - 1
    px = px.dropna(subset=["fwd_ret"])

    # As-of join OI: latest available_date <= signal_date
    print("joining OI PIT ...", flush=True)
    oi2 = oi.sort_values(["code", "available_date"])
    rows = []
    for code, g in px.groupby("code"):
        sub = oi2[oi2["code"] == code]
        if sub.empty:
            continue
        merged = pd.merge_asof(
            g.sort_values("signal_date"),
            sub[["available_date", "oi_yoy"]].sort_values("available_date"),
            left_on="signal_date",
            right_on="available_date",
            direction="backward",
        )
        rows.append(merged)
    panel = pd.concat(rows, ignore_index=True)
    panel = panel.merge(ami[["code", "ym", "amihud_20_lag1"]], on=["code", "ym"], how="left")
    panel = panel.dropna(subset=["oi_yoy", "amihud_20_lag1", "fwd_ret"])

    # Pre-registered score: z(oi_yoy) - z(amihud) within month (prefer growth, prefer liquidity)
    def zscore(s):
        mu, sd = s.mean(), s.std()
        if sd is None or sd == 0 or np.isnan(sd):
            return s * 0.0
        return (s - mu) / sd

    panel["score"] = panel.groupby("ym")["oi_yoy"].transform(zscore) - panel.groupby("ym")[
        "amihud_20_lag1"
    ].transform(zscore)

    # Long top 20% by score; equal-weight; vs equal-weight all
    def month_port(g):
        g = g.dropna(subset=["score", "fwd_ret"])
        if len(g) < 20:
            return None
        k = max(int(len(g) * 0.20), 5)
        top = g.nlargest(k, "score")
        return pd.Series(
            {
                "long_ret": top["fwd_ret"].mean(),
                "ew_ret": g["fwd_ret"].mean(),
                "n": len(g),
                "k": k,
            }
        )

    monthly = panel.groupby("ym").apply(month_port).dropna()
    monthly["excess"] = monthly["long_ret"] - monthly["ew_ret"]

    # Walk-forward OOF by calendar year: report each year separately (no pooling for selection)
    monthly["year"] = monthly.index.to_timestamp().year
    by_year = []
    for y, g in monthly.groupby("year"):
        by_year.append(
            {
                "year": int(y),
                "n_months": int(len(g)),
                "mean_excess": float(g["excess"].mean()),
                "hit_rate": float((g["excess"] > 0).mean()),
                "long_mean": float(g["long_ret"].mean()),
                "ew_mean": float(g["ew_ret"].mean()),
            }
        )

    # Simple cumulative
    long_nav = (1 + monthly["long_ret"]).cumprod()
    ew_nav = (1 + monthly["ew_ret"]).cumprod()
    excess_nav = (1 + monthly["excess"]).cumprod()

    def stats(nav, rets):
        years = max(len(rets) / 12.0, 1e-9)
        cagr = float(nav.iloc[-1] ** (1 / years) - 1)
        mdd = float((nav / nav.cummax() - 1).min())
        return {"cagr": cagr, "mdd": mdd, "util": cagr - 0.5 * abs(mdd)}

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "n_panel_rows": int(len(panel)),
        "n_months": int(len(monthly)),
        "score": "z(oi_yoy) - z(amihud_20_lag1) within month",
        "portfolio": "long top 20% EW vs universe EW",
        "by_year": by_year,
        "full_sample_illustrative_only": {
            "long": stats(long_nav, monthly["long_ret"]),
            "ew": stats(ew_nav, monthly["ew_ret"]),
            "mean_monthly_excess": float(monthly["excess"].mean()),
        },
        "oof_years_positive_excess": sum(1 for r in by_year if r["mean_excess"] > 0),
        "oof_years_total": len(by_year),
        "decision": None,
        "promotion": False,
    }
    # Decision: need majority of years with positive mean excess AND mean excess > 0 overall in OOF sense
    pos_years = report["oof_years_positive_excess"]
    tot = report["oof_years_total"]
    # Require no 3-year consecutive negative excess block among complete years
    years_sorted = sorted(by_year, key=lambda r: r["year"])
    consec_neg = False
    for i in range(len(years_sorted) - 2):
        w = years_sorted[i : i + 3]
        if all(r["n_months"] >= 12 and r["mean_excess"] < 0 for r in w):
            consec_neg = True
            break
    if (
        tot >= 4
        and pos_years / tot >= 0.6
        and report["full_sample_illustrative_only"]["mean_monthly_excess"] > 0
        and not consec_neg
    ):
        report["decision"] = "PASS_LITE_CONTINUE_TO_ADVERSARIAL"
    elif tot >= 3 and pos_years / tot >= 0.5:
        report["decision"] = "MIXED_CONTINUE_CAUTIOUS"
    else:
        report["decision"] = "WEAK_STOP_OR_NEW_FEATURES"
    if consec_neg and report["decision"].startswith("PASS"):
        report["decision"] = "MIXED_CONTINUE_CAUTIOUS"
        report["decision_note"] = "Consecutive 3-year negative excess block"

    monthly.reset_index().assign(ym=lambda d: d["ym"].astype(str)).to_csv(out / "monthly_oof.csv", index=False)
    (out / "alpha_3a_oof_round2b.json").write_text(json.dumps(report, indent=2) + "\n")
    Path("research/reopen/ALPHA_3A_OOF_ROUND2B.md").write_text(
        f"""# Alpha 3A OOF Round-2b

Score: `z(oi_yoy) - z(amihud)` monthly; long top 20% vs EW.

**Decision:** `{report['decision']}`

| Year | Mean excess | Hit rate |
|---|---:|---:|
"""
        + "\n".join(
            f"| {r['year']} | {100*r['mean_excess']:.2f}% | {100*r['hit_rate']:.0f}% |" for r in by_year
        )
        + "\n\nNo promotion. Not TECH2.\n"
    )
    print(json.dumps({"decision": report["decision"], "by_year": by_year, "mean_excess": report["full_sample_illustrative_only"]["mean_monthly_excess"]}, indent=2))


if __name__ == "__main__":
    main()
