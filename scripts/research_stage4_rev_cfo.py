#!/usr/bin/env python3
"""Stage 4 — new 3A family: monthly revenue YoY + CFO YoY (no Amihud/OI).

Full path: build features → OOF years → adversarial-lite with sealed 2025+.
No retune of stopped oi+amihud score. No promotion.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


def zscore(s: pd.Series) -> pd.Series:
    mu, sd = s.mean(), s.std()
    if sd is None or sd == 0 or np.isnan(sd):
        return s * 0.0
    return (s - mu) / sd


def build_rev_yoy() -> pd.DataFrame:
    import polars as pl

    rev = (
        pl.scan_csv("/tmp/a1/causal_monthly_revenue.csv.gz", schema_overrides={"stock_id": pl.String})
        .filter(pl.col("available_date").is_not_null() & pl.col("revenue").is_not_null())
        .select(
            pl.col("stock_id").alias("code"),
            "period_end",
            "available_date",
            "revenue",
            "revenue_year",
            "revenue_month",
        )
        .collect(engine="streaming")
        .to_pandas()
    )
    rev["available_date"] = pd.to_datetime(rev["available_date"], errors="coerce")
    rev["period_end"] = pd.to_datetime(rev["period_end"], errors="coerce")
    rev = rev.dropna(subset=["available_date", "revenue"])
    rev = rev.sort_values(["code", "revenue_year", "revenue_month", "available_date"])
    # 12-month lag within code by calendar month index
    rev["ym_key"] = rev["revenue_year"].astype(int) * 12 + rev["revenue_month"].astype(int)
    rev["rev_lag12"] = rev.groupby("code")["revenue"].shift(12)
    # ensure lag is same code and ~12 months apart
    rev["ym_lag"] = rev.groupby("code")["ym_key"].shift(12)
    ok = rev["ym_key"] - rev["ym_lag"] == 12
    rev.loc[~ok, "rev_lag12"] = np.nan
    rev["rev_yoy_12m"] = rev["revenue"] / rev["rev_lag12"].replace(0, np.nan) - 1
    out = rev.dropna(subset=["rev_yoy_12m"])[
        ["code", "available_date", "period_end", "revenue", "rev_yoy_12m"]
    ]
    return out


def build_cfo_yoy() -> pd.DataFrame:
    import polars as pl

    fin = (
        pl.scan_csv("/tmp/a1/causal_financials.csv.gz", schema_overrides={"stock_id": pl.String})
        .filter(
            (pl.col("type") == "CashFlowsFromOperatingActivities")
            & (pl.col("statement") == "cashflow")
            & pl.col("available_date").is_not_null()
        )
        .select(
            pl.col("stock_id").alias("code"),
            "period_end",
            "available_date",
            pl.col("value").alias("cfo"),
        )
        .collect(engine="streaming")
        .to_pandas()
    )
    fin["available_date"] = pd.to_datetime(fin["available_date"], errors="coerce")
    fin["period_end"] = pd.to_datetime(fin["period_end"], errors="coerce")
    fin = fin.dropna(subset=["available_date", "period_end", "cfo"])
    fin = fin.sort_values(["code", "period_end", "available_date"])
    fin["cfo_lag4"] = fin.groupby("code")["cfo"].shift(4)
    fin["cfo_yoy"] = fin["cfo"] / fin["cfo_lag4"].replace(0, np.nan) - 1
    # also allow sign-flip cases via difference scaled — keep simple ratio; drop inf
    fin = fin.replace([np.inf, -np.inf], np.nan).dropna(subset=["cfo_yoy"])
    return fin[["code", "available_date", "period_end", "cfo", "cfo_yoy"]]


def month_end_prices(pit: str, start: str = "2019-01-01") -> pd.DataFrame:
    import polars as pl

    df = (
        pl.scan_csv(pit, schema_overrides={"code": pl.String})
        .filter(pl.col("date") >= start)
        .select("date", "code", "close")
        .collect(engine="streaming")
        .to_pandas()
    )
    df["date"] = pd.to_datetime(df["date"])
    df = df.dropna(subset=["close"]).sort_values(["code", "date"])
    df["ym"] = df["date"].dt.to_period("M")
    me = df.groupby(["code", "ym"], as_index=False).tail(1)
    return me.rename(columns={"date": "signal_date", "close": "px"})


def asof_join(px: pd.DataFrame, feat: pd.DataFrame, col: str) -> pd.DataFrame:
    feat = feat.sort_values(["code", "available_date"])
    rows = []
    for code, g in px.groupby("code"):
        sub = feat[feat["code"] == code]
        if sub.empty:
            continue
        m = pd.merge_asof(
            g.sort_values("signal_date"),
            sub[["available_date", col]].sort_values("available_date"),
            left_on="signal_date",
            right_on="available_date",
            direction="backward",
        )
        rows.append(m)
    return pd.concat(rows, ignore_index=True) if rows else px.copy()


def pick_long(g: pd.DataFrame, frac: float = 0.20, industry_cap: float | None = None) -> pd.DataFrame:
    g = g.dropna(subset=["score", "fwd_ret"]).copy()
    if len(g) < 20:
        return g.iloc[0:0]
    k = max(int(len(g) * frac), 5)
    ranked = g.sort_values("score", ascending=False)
    if industry_cap is None:
        return ranked.head(k)
    cap_n = max(int(np.floor(k * industry_cap)), 1)
    chosen, counts = [], {}
    for _, row in ranked.iterrows():
        ind = row.get("industry", "UNK")
        if counts.get(ind, 0) >= cap_n:
            continue
        chosen.append(row)
        counts[ind] = counts.get(ind, 0) + 1
        if len(chosen) >= k:
            break
    return pd.DataFrame(chosen)


def monthly_series(panel: pd.DataFrame, picker) -> pd.DataFrame:
    rows = []
    prev = None
    for ym, g in panel.groupby("ym"):
        top = picker(g)
        if len(top) < 5:
            continue
        codes = set(top["code"].astype(str))
        turn = 1.0 if prev is None else 1.0 - len(codes & prev) / max(len(codes), 1)
        rows.append(
            {
                "ym": ym,
                "year": int(pd.Period(ym, freq="M").year),
                "long_ret": float(top["fwd_ret"].mean()),
                "ew_ret": float(g["fwd_ret"].mean()),
                "turnover_one_way": float(turn),
            }
        )
        prev = codes
    m = pd.DataFrame(rows).set_index("ym").sort_index()
    m["excess_gross"] = m["long_ret"] - m["ew_ret"]
    return m


def apply_cost(m: pd.DataFrame, bps: float) -> pd.Series:
    return m["long_ret"] - m["turnover_one_way"] * (bps / 10000.0) - m["ew_ret"]


def year_table(excess: pd.Series, years: pd.Series) -> list[dict]:
    df = pd.DataFrame({"excess": excess, "year": years})
    out = []
    for y, g in df.groupby("year"):
        out.append(
            {
                "year": int(y),
                "n_months": int(len(g)),
                "mean_excess": float(g["excess"].mean()),
                "hit_rate": float((g["excess"] > 0).mean()),
            }
        )
    return out


def consec_neg(by_year: list[dict], need: int = 3) -> bool:
    ys = sorted([r for r in by_year if r["n_months"] >= 10], key=lambda r: r["year"])
    for i in range(len(ys) - need + 1):
        if all(r["mean_excess"] < 0 for r in ys[i : i + need]):
            return True
    return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("repro/stage4-rev-cfo-20260904"))
    ap.add_argument("--pit", default="/tmp/a0/point_in_time_universe.csv")
    ap.add_argument("--master", type=Path, default=Path("/tmp/a0/security_master.csv"))
    args = ap.parse_args()
    out = args.out
    feat = out / "features"
    feat.mkdir(parents=True, exist_ok=True)
    Path("research/reopen").mkdir(parents=True, exist_ok=True)

    print("building rev_yoy_12m ...", flush=True)
    rev = build_rev_yoy()
    rev.to_parquet(feat / "rev_yoy_12m_pit.parquet", index=False)
    print(f"  rev rows={len(rev)} codes={rev.code.nunique()}", flush=True)

    print("building cfo_yoy ...", flush=True)
    cfo = build_cfo_yoy()
    cfo.to_parquet(feat / "cfo_yoy_pit.parquet", index=False)
    print(f"  cfo rows={len(cfo)} codes={cfo.code.nunique()}", flush=True)

    print("prices + joins ...", flush=True)
    px = month_end_prices(args.pit)
    px = px.sort_values(["code", "ym"])
    px["next_px"] = px.groupby("code")["px"].shift(-1)
    px["fwd_ret"] = px["next_px"] / px["px"] - 1
    px = px.dropna(subset=["fwd_ret"])

    panel = asof_join(px, rev, "rev_yoy_12m")
    # second asof for cfo — merge on code+signal_date
    cfo2 = cfo.sort_values(["code", "available_date"])
    rows = []
    for code, g in panel.groupby("code"):
        sub = cfo2[cfo2["code"] == code]
        if sub.empty:
            continue
        m = pd.merge_asof(
            g.sort_values("signal_date"),
            sub[["available_date", "cfo_yoy"]].rename(columns={"available_date": "cfo_available"}).sort_values(
                "cfo_available"
            ),
            left_on="signal_date",
            right_on="cfo_available",
            direction="backward",
        )
        rows.append(m)
    panel = pd.concat(rows, ignore_index=True)
    panel = panel.dropna(subset=["rev_yoy_12m", "cfo_yoy", "fwd_ret"])

    sm = pd.read_csv(args.master, dtype={"stock_id": str}).rename(columns={"stock_id": "code"})
    ind = sm.groupby("code")["industry_category"].agg(
        lambda s: s.dropna().iloc[-1] if s.dropna().size else "UNK"
    )
    panel["industry"] = panel["code"].map(ind).fillna("UNK")
    panel["score"] = panel.groupby("ym")["rev_yoy_12m"].transform(zscore) + panel.groupby("ym")[
        "cfo_yoy"
    ].transform(zscore)
    panel["year"] = panel["signal_date"].dt.year
    panel.to_parquet(out / "panel_monthly.parquet", index=False)

    # OOF by year (gross, illustrative)
    m_all = monthly_series(panel, lambda g: pick_long(g))
    oof_years = year_table(m_all["excess_gross"], m_all["year"])

    # Adversarial-lite
    dev = panel[panel["year"].between(2019, 2024)]
    sealed = panel[panel["year"] >= 2025]
    m_dev = monthly_series(dev, lambda g: pick_long(g))
    m_sealed = monthly_series(sealed, lambda g: pick_long(g))

    costs = {}
    for bps in (20, 40, 60):
        ex = apply_cost(m_dev, bps)
        yt = year_table(ex, m_dev["year"])
        costs[f"rt_{bps}bps"] = {
            "mean_excess": float(ex.mean()),
            "by_year": yt,
            "consec_neg_3y": consec_neg(yt),
            "mean_turnover": float(m_dev["turnover_one_way"].mean()),
        }

    def ind_cap(g):
        return pick_long(g, industry_cap=0.25)

    m_ind = monthly_series(dev, ind_cap)
    ex_ind = apply_cost(m_ind, 40)

    ex40 = apply_cost(m_dev, 40)
    loyo = [
        {"leave_out_year": int(y), "mean_excess_net40_rest": float(ex40[m_dev["year"] != y].mean())}
        for y in sorted(m_dev["year"].unique())
    ]
    loyo_fragile = sum(1 for r in loyo if r["mean_excess_net40_rest"] <= 0) >= 2

    sealed_ex40 = apply_cost(m_sealed, 40) if len(m_sealed) else pd.Series(dtype=float)
    sealed_report = {
        "n_months": int(len(m_sealed)),
        "mean_excess_gross": float(m_sealed["excess_gross"].mean()) if len(m_sealed) else None,
        "mean_excess_net40": float(sealed_ex40.mean()) if len(sealed_ex40) else None,
        "by_year": year_table(sealed_ex40, m_sealed["year"]) if len(m_sealed) else [],
    }

    dev_gate = {
        "net40_mean_excess_gt_0": costs["rt_40bps"]["mean_excess"] > 0,
        "net40_no_consec_neg_3y": not costs["rt_40bps"]["consec_neg_3y"],
        "loyo_not_fragile": not loyo_fragile,
        "industry_cap_net40_gt_m10bps": float(ex_ind.mean()) > -0.001,
    }
    dev_pass = all(dev_gate.values())
    held_ok = sealed_report["mean_excess_net40"] is not None and sealed_report["mean_excess_net40"] > 0

    if not dev_pass:
        decision = "STOP_STAGE4_FEATURE_SET"
    elif not held_ok:
        decision = "FAIL_HELD_OUT_STOP"
    else:
        decision = "PASS_ADVERSARIAL_LITE"

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "stage": 4,
        "score_frozen": "z(rev_yoy_12m)+z(cfo_yoy)",
        "excluded_from_stopped_set": ["oi_yoy", "amihud"],
        "promotion": False,
        "oof_gross_by_year": oof_years,
        "costs_dev": costs,
        "industry_cap_net40_mean": float(ex_ind.mean()),
        "loyo_net40": loyo,
        "dev_gate": dev_gate,
        "dev_pass": dev_pass,
        "sealed": sealed_report,
        "held_out_pass": held_ok,
        "decision": decision,
    }
    (out / "stage4_report.json").write_text(json.dumps(report, indent=2, default=str) + "\n")
    m_dev.assign(ym=lambda d: d.index.astype(str)).to_csv(out / "dev_monthly.csv")
    if len(m_sealed):
        m_sealed.assign(ym=lambda d: d.index.astype(str)).to_csv(out / "sealed_monthly.csv")

    md = f"""# Stage 4 — Revenue YoY + CFO YoY

Score: `z(rev_yoy_12m) + z(cfo_yoy)` (not OI/Amihud).

## Decision: `{decision}`

### Dev gates (2019–2024)
```json
{json.dumps(dev_gate, indent=2)}
```

| Cost | Mean excess |
|---|---:|
| 20 bps | {100*costs['rt_20bps']['mean_excess']:.3f}% |
| 40 bps | {100*costs['rt_40bps']['mean_excess']:.3f}% |
| 60 bps | {100*costs['rt_60bps']['mean_excess']:.3f}% |

Sealed 2025+ net40: **{(f"{100*sealed_report['mean_excess_net40']:.3f}%" if sealed_report['mean_excess_net40'] is not None else "n/a")}**

No promotion. Artifact: `{out}/stage4_report.json`
"""
    (out / "STAGE4_DECISION.md").write_text(md)
    Path("research/reopen/STAGE4_DECISION.md").write_text(md)
    Path("research/reopen/stage4_report.json").write_text(json.dumps(report, indent=2, default=str) + "\n")
    print(json.dumps({"decision": decision, "dev_pass": dev_pass, "held_out_pass": held_ok, "net40": costs["rt_40bps"]["mean_excess"], "sealed_net40": sealed_report["mean_excess_net40"]}, indent=2))


if __name__ == "__main__":
    main()
