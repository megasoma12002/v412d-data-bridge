#!/usr/bin/env python3
"""Stage 6 — non-fundamental 3A probe: securities-lending fee stress.

New PIT family (not fundamental YoY / not stopped oi+amihud remix):
  monthly volume-weighted lend fee_rate from FinMind TaiwanStockSecuritiesLending
  Score: -z(lend_fee_1m)  (prefer cheaper/less-stressed borrow names)
  Long top 20% EW vs universe EW on the existing adversarial monthly panel skeleton.

Dev: 2019-2024; sealed held-out 2025+.
No retune after held-out. No promotion.
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

UA = "v412-stage6-lend-fee/1.0"


def zscore(s: pd.Series) -> pd.Series:
    mu, sd = s.mean(), s.std()
    if sd is None or sd == 0 or np.isnan(sd):
        return s * 0.0
    return (s - mu) / sd


def fetch_lending(code: str, start: str = "2018-01-01", end: str = "2026-09-04") -> pd.DataFrame:
    q = urllib.parse.urlencode(
        {
            "dataset": "TaiwanStockSecuritiesLending",
            "data_id": code,
            "start_date": start,
            "end_date": end,
        }
    )
    req = urllib.request.Request(
        "https://api.finmindtrade.com/api/v4/data?" + q,
        headers={"User-Agent": UA},
    )
    with urllib.request.urlopen(req, timeout=90) as response:
        payload = json.load(response)
    if payload.get("status") != 200:
        return pd.DataFrame()
    rows = payload.get("data") or []
    if not rows:
        return pd.DataFrame()
    d = pd.DataFrame(rows)
    d["code"] = str(code)
    d["date"] = pd.to_datetime(d["date"], errors="coerce")
    d["fee_rate"] = pd.to_numeric(d["fee_rate"], errors="coerce")
    d["volume"] = pd.to_numeric(d["volume"], errors="coerce")
    return d.dropna(subset=["date", "fee_rate"])


def pick_long(g: pd.DataFrame, frac: float = 0.20) -> pd.DataFrame:
    n = max(1, int(np.ceil(len(g) * frac)))
    return g.nlargest(n, "score")


def month_excess(panel: pd.DataFrame, cost_bps: float = 0.0) -> pd.Series:
    rows = []
    prev = set()
    for ym, g in panel.groupby("ym", sort=True):
        long = pick_long(g)
        codes = set(long["code"])
        gross = float(long["fwd_ret"].mean() - g["fwd_ret"].mean())
        turnover = 1.0 if not prev else len(codes.symmetric_difference(prev)) / max(len(codes | prev), 1)
        net = gross - turnover * (cost_bps / 10000.0)
        rows.append((ym, net, gross, turnover))
        prev = codes
    return pd.DataFrame(rows, columns=["ym", "net", "gross", "turnover"]).set_index("ym")


def consec_neg_years(ex: pd.Series, n: int = 3) -> bool:
    if ex.empty:
        return True
    yearly = ex.groupby(ex.index.year).mean() if hasattr(ex.index, "year") else ex
    # ym Period index
    if isinstance(ex.index, pd.PeriodIndex):
        yearly = ex.groupby(ex.index.year).mean()
    vals = yearly.to_numpy()
    if len(vals) < n:
        return False
    for i in range(len(vals) - n + 1):
        if np.all(vals[i : i + n] <= 0):
            return True
    return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--panel",
        default="repro/alpha3a-adversarial-lite-20260904/panel_monthly.parquet",
        help="Reuse monthly fwd_ret skeleton (prices already PIT-built)",
    )
    ap.add_argument("--out", default="repro/stage6-lend-fee-3a-20260904")
    ap.add_argument("--max-codes", type=int, default=80)
    ap.add_argument("--sleep", type=float, default=0.12)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    base = pd.read_parquet(args.panel)
    base["signal_date"] = pd.to_datetime(base["signal_date"])
    if not isinstance(base["ym"].dtype, pd.PeriodDtype):
        base["ym"] = pd.to_datetime(base["signal_date"]).dt.to_period("M")
    # Prefer liquid names with history in panel
    top = base.groupby("code").size().nlargest(args.max_codes).index.astype(str).tolist()
    print(json.dumps({"n_codes_fetch": len(top), "sample": top[:8]}), flush=True)

    chunks = []
    errors = []
    for i, code in enumerate(top):
        try:
            d = fetch_lending(code)
            if len(d):
                chunks.append(d)
            print(f"  lending {i+1}/{len(top)} {code} rows={len(d)}", flush=True)
        except Exception as exc:  # noqa: BLE001
            errors.append({"code": code, "error": str(exc)})
            print(f"  lending FAIL {code}: {exc}", flush=True)
        time.sleep(args.sleep)

    if not chunks:
        raise SystemExit("no lending data fetched")
    lend = pd.concat(chunks, ignore_index=True)
    lend["ym"] = lend["date"].dt.to_period("M")
    # volume-weighted fee within month
    lend["wv"] = lend["fee_rate"] * lend["volume"].clip(lower=0)
    monthly = (
        lend.groupby(["code", "ym"], as_index=False)
        .agg(fee_sum=("wv", "sum"), vol_sum=("volume", "sum"), n_trades=("fee_rate", "count"))
    )
    monthly["lend_fee_1m"] = monthly["fee_sum"] / monthly["vol_sum"].replace(0, np.nan)
    monthly = monthly.dropna(subset=["lend_fee_1m"])
    monthly.to_parquet(out / "lend_fee_1m_monthly.parquet", index=False)

    panel = base.merge(monthly[["code", "ym", "lend_fee_1m"]], on=["code", "ym"], how="inner")
    panel = panel.dropna(subset=["lend_fee_1m", "fwd_ret"])
    panel["score"] = -panel.groupby("ym")["lend_fee_1m"].transform(zscore)
    panel["year"] = panel["signal_date"].dt.year
    panel.to_parquet(out / "panel_monthly.parquet", index=False)

    dev = panel[panel["year"].between(2019, 2024)].copy()
    sealed = panel[panel["year"] >= 2025].copy()

    costs = {}
    for bps in (0, 20, 40, 60):
        ex = month_excess(dev, cost_bps=bps)["net"]
        costs[f"rt_{bps}bps"] = {
            "mean_excess": float(ex.mean()) if len(ex) else None,
            "consec_neg_3y": bool(consec_neg_years(ex, 3)) if len(ex) else True,
            "n_months": int(len(ex)),
        }

    # LOYO on net40
    ex40 = month_excess(dev, cost_bps=40)["net"]
    loyo = []
    for y in sorted(dev["year"].unique()):
        sub = dev[dev["year"] != y]
        s = month_excess(sub, cost_bps=40)["net"]
        loyo.append({"leave_out_year": int(y), "mean_excess_net40_rest": float(s.mean()) if len(s) else None})
    loyo_fragile = sum(1 for r in loyo if (r["mean_excess_net40_rest"] or 0) <= 0) >= 2

    sealed_ex = month_excess(sealed, cost_bps=40)["net"] if len(sealed) else pd.Series(dtype=float)
    sealed_report = {
        "mean_excess_net40": float(sealed_ex.mean()) if len(sealed_ex) else None,
        "n_months": int(len(sealed_ex)),
    }

    gates = {
        "net40_mean_excess_gt_0": (costs["rt_40bps"]["mean_excess"] or 0) > 0,
        "net40_no_consec_neg_3y": not costs["rt_40bps"]["consec_neg_3y"],
        "loyo_not_fragile": not loyo_fragile,
        "coverage_months_dev_ge_36": costs["rt_40bps"]["n_months"] >= 36,
        "codes_ge_40": panel["code"].nunique() >= 40,
    }
    dev_pass = all(gates.values())
    held_ok = sealed_report["mean_excess_net40"] is not None and sealed_report["mean_excess_net40"] > 0

    if not dev_pass:
        decision = "STOP_STAGE6_LEND_FEE_FEATURE_SET"
    elif not held_ok:
        decision = "FAIL_HELD_OUT_STOP"
    else:
        decision = "PASS_ADVERSARIAL_LITE_NO_PROMOTE"

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "stage": 6,
        "feature_set": "-z(lend_fee_1m)_monthly_top20pct",
        "source": "FinMind TaiwanStockSecuritiesLending",
        "n_codes_requested": len(top),
        "n_codes_with_lending": int(monthly["code"].nunique()),
        "n_panel_rows": int(len(panel)),
        "fetch_errors": errors[:20],
        "gates": gates,
        "costs_dev": costs,
        "loyo_net40": loyo,
        "sealed_held_out": sealed_report,
        "dev_pass": dev_pass,
        "held_out_pass": held_ok,
        "decision": decision,
        "promotion": False,
    }
    (out / "stage6_report.json").write_text(json.dumps(report, indent=2, default=str) + "\n")
    (out / "STAGE6_DECISION.md").write_text(
        f"""# Stage 6 Decision — Lending Fee 3A Probe

Feature: `-z(lend_fee_1m)` monthly top-20% vs EW  
Source: FinMind `TaiwanStockSecuritiesLending` (new PIT family)

## Gates (dev 2019–2024)

{json.dumps(gates, indent=2)}

Net40 mean excess: **{costs['rt_40bps']['mean_excess']}**  
Sealed 2025+ net40: **{sealed_report['mean_excess_net40']}**

## Decision

**`{decision}`**

Promotion: **False** (even on PASS — needs explicit approval + locked C4 bar).
"""
    )
    print(json.dumps({"decision": decision, "dev_pass": dev_pass, "held_out_pass": held_ok, "net40": costs["rt_40bps"]["mean_excess"], "sealed": sealed_report["mean_excess_net40"]}, indent=2))


if __name__ == "__main__":
    main()
