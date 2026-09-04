#!/usr/bin/env python3
"""Alpha 3A adversarial-lite (Round-3) — fixed score, no retune, sealed held-out.

Pre-registered:
  Score: z(oi_yoy) - z(amihud_20_lag1) within month (unchanged from Round-2b)
  Portfolio: long top 20% EW vs universe EW
  Dev window: 2019-01 → 2024-12 (stress + cost here only)
  Sealed held-out: 2025-01 → end (report once; never used to change score)

Stresses (all must be checked before opening held-out narrative):
  1) Turnover + cost 20/40/60 bps round-trip on changed weight
  2) Drop high-amihud tercile (illiquid) / drop low-amihud tercile (liquid-only)
  3) Industry cap: max 25% of names from one industry_category
  4) Leave-one-year-out on dev years

Decision (no promotion either way):
  STOP  — dev net-of-40bps excess ≤ 0 OR consec 3y neg in dev OR LOYO fragile
  FAIL_HELD_OUT — dev OK but sealed 2025-26 mean excess ≤ 0
  PASS_ADVERSARIAL_LITE — dev OK and sealed excess > 0
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


def month_end_panel(pit_path: str, start: str = "2019-01-01") -> pd.DataFrame:
    import polars as pl

    df = (
        pl.scan_csv(pit_path, schema_overrides={"code": pl.String})
        .filter(pl.col("date") >= start)
        .select("date", "code", "close", "volume")
        .collect(engine="streaming")
        .to_pandas()
    )
    df["date"] = pd.to_datetime(df["date"])
    df = df.dropna(subset=["close"]).sort_values(["code", "date"])
    df["ym"] = df["date"].dt.to_period("M")
    me = df.groupby(["code", "ym"], as_index=False).tail(1)
    return me.rename(columns={"date": "signal_date", "close": "px"})


def build_panel(feat_dir: Path, pit: str, master: Path) -> pd.DataFrame:
    oi = pd.read_parquet(feat_dir / "operating_income_yoy_pit.parquet")
    ami = pd.read_parquet(feat_dir / "amihud_20_lag1_monthly.parquet")
    oi["available_date"] = pd.to_datetime(oi["available_date"])
    ami["date"] = pd.to_datetime(ami["date"])
    ami["ym"] = ami["date"].dt.to_period("M")

    px = month_end_panel(pit)
    px = px.sort_values(["code", "ym"])
    px["next_px"] = px.groupby("code")["px"].shift(-1)
    px["fwd_ret"] = px["next_px"] / px["px"] - 1
    px = px.dropna(subset=["fwd_ret"])

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

    sm = pd.read_csv(master, dtype={"stock_id": str})
    sm = sm.rename(columns={"stock_id": "code"})
    # current snapshot industry — documented limitation (A0 known boundary)
    ind = sm.groupby("code")["industry_category"].agg(lambda s: s.dropna().iloc[-1] if s.dropna().size else "UNK")
    panel["industry"] = panel["code"].map(ind).fillna("UNK")

    panel["score"] = panel.groupby("ym")["oi_yoy"].transform(zscore) - panel.groupby("ym")[
        "amihud_20_lag1"
    ].transform(zscore)
    panel["year"] = panel["signal_date"].dt.year
    return panel


def pick_long(g: pd.DataFrame, *, frac: float = 0.20, industry_cap: float | None = None) -> pd.DataFrame:
    g = g.dropna(subset=["score", "fwd_ret"]).copy()
    if len(g) < 20:
        return g.iloc[0:0]
    k = max(int(len(g) * frac), 5)
    ranked = g.sort_values("score", ascending=False)
    if industry_cap is None:
        return ranked.head(k)
    # greedy fill with industry name-count cap
    cap_n = max(int(np.floor(k * industry_cap)), 1)
    chosen = []
    counts: dict[str, int] = {}
    for _, row in ranked.iterrows():
        ind = row["industry"]
        if counts.get(ind, 0) >= cap_n:
            continue
        chosen.append(row)
        counts[ind] = counts.get(ind, 0) + 1
        if len(chosen) >= k:
            break
    return pd.DataFrame(chosen)


def monthly_series(panel: pd.DataFrame, picker) -> pd.DataFrame:
    rows = []
    prev_codes: set[str] | None = None
    for ym, g in panel.groupby("ym"):
        top = picker(g)
        if len(top) < 5:
            continue
        codes = set(top["code"].astype(str))
        if prev_codes is None:
            turnover = 1.0  # initial full deploy
        else:
            # one-way turnover ≈ fraction of names replaced
            turnover = 1.0 - len(codes & prev_codes) / max(len(codes), 1)
        rows.append(
            {
                "ym": ym,
                "year": int(pd.Period(ym, freq="M").year),
                "long_ret": float(top["fwd_ret"].mean()),
                "ew_ret": float(g["fwd_ret"].mean()),
                "turnover_one_way": float(turnover),
                "n": int(len(g)),
                "k": int(len(top)),
            }
        )
        prev_codes = codes
    m = pd.DataFrame(rows).set_index("ym").sort_index()
    m["excess_gross"] = m["long_ret"] - m["ew_ret"]
    return m


def apply_cost(m: pd.DataFrame, roundtrip_bps: float) -> pd.Series:
    # cost on long sleeve only; EW benchmark assumed similarly traded → charge turnover * bps on long
    c = m["turnover_one_way"] * (roundtrip_bps / 10000.0)
    return m["long_ret"] - c - m["ew_ret"]


def year_table(excess: pd.Series, years: pd.Series) -> list[dict]:
    out = []
    df = pd.DataFrame({"excess": excess, "year": years})
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


def consec_neg_years(by_year: list[dict], need: int = 3) -> bool:
    ys = sorted([r for r in by_year if r["n_months"] >= 10], key=lambda r: r["year"])
    for i in range(len(ys) - need + 1):
        if all(r["mean_excess"] < 0 for r in ys[i : i + need]):
            return True
    return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--feat-dir", type=Path, default=Path("repro/research-reopen-round2-20260904/alpha_3a_features"))
    ap.add_argument("--out", type=Path, default=Path("repro/alpha3a-adversarial-lite-20260904"))
    ap.add_argument("--pit", default="/tmp/a0/point_in_time_universe.csv")
    ap.add_argument("--master", type=Path, default=Path("/tmp/a0/security_master.csv"))
    args = ap.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    Path("research/reopen").mkdir(parents=True, exist_ok=True)

    print("building panel ...", flush=True)
    panel = build_panel(args.feat_dir, args.pit, args.master)
    panel.to_parquet(out / "panel_monthly.parquet", index=False)

    # --- Development stresses (2019-2024 only) ---
    dev = panel[panel["year"].between(2019, 2024)].copy()
    sealed = panel[panel["year"] >= 2025].copy()

    print("baseline monthly (dev) ...", flush=True)
    m_dev = monthly_series(dev, lambda g: pick_long(g))
    m_all = monthly_series(panel, lambda g: pick_long(g))

    costs = {}
    for bps in (20, 40, 60):
        ex = apply_cost(m_dev, bps)
        costs[f"rt_{bps}bps"] = {
            "mean_excess": float(ex.mean()),
            "by_year": year_table(ex, m_dev["year"]),
            "consec_neg_3y": consec_neg_years(year_table(ex, m_dev["year"])),
            "mean_turnover": float(m_dev["turnover_one_way"].mean()),
        }

    # Liquidity cuts
    def drop_amihud_tercile(g, which: str):
        g = g.copy()
        q1, q2 = g["amihud_20_lag1"].quantile([1 / 3, 2 / 3])
        if which == "drop_illiquid":
            g = g[g["amihud_20_lag1"] <= q2]  # drop top illiquid third
        elif which == "drop_liquid":
            g = g[g["amihud_20_lag1"] >= q1]  # drop most liquid third
        return pick_long(g)

    stress_ports = {
        "drop_illiquid_tercile": monthly_series(dev, lambda g: drop_amihud_tercile(g, "drop_illiquid")),
        "drop_liquid_tercile": monthly_series(dev, lambda g: drop_amihud_tercile(g, "drop_liquid")),
        "industry_cap_25pct": monthly_series(dev, lambda g: pick_long(g, industry_cap=0.25)),
    }
    stress = {}
    for name, mm in stress_ports.items():
        ex = apply_cost(mm, 40)
        stress[name] = {
            "mean_excess_net40": float(ex.mean()),
            "by_year": year_table(ex, mm["year"]),
            "consec_neg_3y": consec_neg_years(year_table(ex, mm["year"])),
        }

    # Leave-one-year-out on net40 baseline
    ex40 = apply_cost(m_dev, 40)
    loyo = []
    for y in sorted(m_dev["year"].unique()):
        mask = m_dev["year"] != y
        loyo.append({"leave_out_year": int(y), "mean_excess_net40_rest": float(ex40[mask].mean())})
    loyo_fragile = sum(1 for r in loyo if r["mean_excess_net40_rest"] <= 0) >= 2

    # Gross baseline for reference
    base_gross = {
        "mean_excess": float(m_dev["excess_gross"].mean()),
        "mean_turnover": float(m_dev["turnover_one_way"].mean()),
        "by_year": year_table(m_dev["excess_gross"], m_dev["year"]),
        "consec_neg_3y": consec_neg_years(year_table(m_dev["excess_gross"], m_dev["year"])),
    }

    dev_gate = {
        "net40_mean_excess_gt_0": costs["rt_40bps"]["mean_excess"] > 0,
        "net40_no_consec_neg_3y": not costs["rt_40bps"]["consec_neg_3y"],
        "loyo_not_fragile": not loyo_fragile,
        "drop_illiquid_net40_gt_m10bps": stress["drop_illiquid_tercile"]["mean_excess_net40"] > -0.001,
        "industry_cap_net40_gt_m10bps": stress["industry_cap_25pct"]["mean_excess_net40"] > -0.001,
    }
    dev_pass = all(dev_gate.values())

    # --- Sealed held-out (opened only for reporting after gates computed) ---
    print("sealed held-out 2025-2026 ...", flush=True)
    m_sealed = monthly_series(sealed, lambda g: pick_long(g))
    sealed_ex40 = apply_cost(m_sealed, 40) if len(m_sealed) else pd.Series(dtype=float)
    sealed_report = {
        "n_months": int(len(m_sealed)),
        "mean_excess_gross": float(m_sealed["excess_gross"].mean()) if len(m_sealed) else None,
        "mean_excess_net40": float(sealed_ex40.mean()) if len(sealed_ex40) else None,
        "by_year": year_table(sealed_ex40, m_sealed["year"]) if len(m_sealed) else [],
        "mean_turnover": float(m_sealed["turnover_one_way"].mean()) if len(m_sealed) else None,
    }
    held_ok = (
        sealed_report["mean_excess_net40"] is not None and sealed_report["mean_excess_net40"] > 0
    )

    if not dev_pass:
        decision = "STOP_THIS_FEATURE_SET"
    elif not held_ok:
        decision = "FAIL_HELD_OUT_STOP"
    else:
        decision = "PASS_ADVERSARIAL_LITE"

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "score_frozen": "z(oi_yoy)-z(amihud_20_lag1)",
        "no_retune": True,
        "promotion": False,
        "dev_window": "2019-2024",
        "sealed_held_out": "2025+",
        "industry_note": "A0 security_master is current snapshot — industry cut is approximate",
        "baseline_dev_gross": base_gross,
        "costs_dev": costs,
        "stress_dev_net40": stress,
        "loyo_net40": loyo,
        "dev_gate": dev_gate,
        "dev_pass": dev_pass,
        "sealed": sealed_report,
        "held_out_pass": held_ok,
        "decision": decision,
        "next_if_pass": "Paper sleeve only after explicit approval; still not SOFT_FROZEN",
        "next_if_stop": "Do not retune this score; new feature family required for another 3A attempt",
    }

    (out / "adversarial_lite_report.json").write_text(json.dumps(report, indent=2, default=str) + "\n")
    m_dev.assign(ym=lambda d: d.index.astype(str)).to_csv(out / "dev_monthly.csv")
    if len(m_sealed):
        m_sealed.assign(ym=lambda d: d.index.astype(str)).to_csv(out / "sealed_monthly.csv")
    Path("research/reopen/ALPHA_3A_ADVERSARIAL_LITE.md").write_text(
        f"""# Alpha 3A Adversarial-Lite

Score frozen: `z(oi_yoy) - z(amihud)`. No retune. Dev 2019–2024; sealed 2025+.

## Decision: `{decision}`

### Dev gates
```json
{json.dumps(dev_gate, indent=2)}
```

### Cost (dev)
| Round-trip | Mean excess |
|---|---:|
| 20 bps | {100*costs['rt_20bps']['mean_excess']:.3f}% |
| 40 bps | {100*costs['rt_40bps']['mean_excess']:.3f}% |
| 60 bps | {100*costs['rt_60bps']['mean_excess']:.3f}% |

Mean one-way turnover: **{100*base_gross['mean_turnover']:.1f}%**/month

### Sealed held-out (2025+)
Mean excess net 40 bps: **{(f"{100*sealed_report['mean_excess_net40']:.3f}%" if sealed_report["mean_excess_net40"] is not None else "n/a")}**

### Promotion
**False** — even on PASS, needs separate approval for paper sleeve.

Artifact: `repro/alpha3a-adversarial-lite-20260904/adversarial_lite_report.json`
"""
    )
    print(json.dumps({"decision": decision, "dev_pass": dev_pass, "held_out_pass": held_ok, "net40": costs["rt_40bps"]["mean_excess"], "sealed_net40": sealed_report["mean_excess_net40"]}, indent=2))


if __name__ == "__main__":
    main()
