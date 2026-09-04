#!/usr/bin/env python3
"""Stage 7 — TX futures open-interest timing overlay on early-stack NAV.

Pre-registered (≤3 books, no retune after sealed look):
  BASE              exposure = 1.0 (E16+E18+E22 ex-date)
  OI_UP_DELEVER     z(ΔOI_60) > +1.0 → exposure 0.70 else 1.0
  OI_DOWN_DELEVER   z(ΔOI_60) < −1.0 → exposure 0.70 else 1.0

PIT: OI through T-1 drives exposure on signal day T (Exact T+1 fills unchanged).
Sealed 2025+ is diagnostic only. No promotion.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e50_early_stack_combined_nav as core

OUT_DEFAULT = Path("repro/stage7-tx-oi-timing-20260904")
UTIL_EPS = 0.002
MDD_EPS = 0.005
Z_WIN = 60
DELEVER = 0.70
Z_THR = 1.0


def nav_stats(nav: pd.Series) -> dict:
    nav = nav.dropna()
    if len(nav) < 3:
        return {"cagr": None, "mdd": None, "util": None, "n": int(len(nav)), "vol": None}
    r = nav.pct_change().dropna()
    years = max(len(r) / 252.0, 1e-9)
    cagr = float((nav.iloc[-1] / nav.iloc[0]) ** (1 / years) - 1)
    mdd = float((nav / nav.cummax() - 1).min())
    return {
        "cagr": cagr,
        "mdd": mdd,
        "util": cagr - 0.5 * abs(mdd),
        "n": int(len(nav)),
        "vol": float(r.std() * np.sqrt(252)),
    }


def load_tx_front_oi(path: Path) -> pd.DataFrame:
    """Daily front-month TX OI from regular session (max volume contract)."""
    raw = pd.read_csv(path)
    raw["date"] = pd.to_datetime(raw["date"], errors="coerce")
    raw["open_interest"] = pd.to_numeric(raw["open_interest"], errors="coerce")
    raw["volume"] = pd.to_numeric(raw["volume"], errors="coerce")
    raw = raw.dropna(subset=["date", "open_interest"])
    raw = raw[raw["futures_id"].astype(str).str.upper() == "TX"]
    # Prefer day session; fall back to any if column missing
    if "trading_session" in raw.columns:
        day = raw[raw["trading_session"].astype(str).str.lower() == "position"]
        if len(day):
            raw = day
    # Front month ≈ highest volume contract that day
    idx = raw.groupby("date")["volume"].idxmax()
    front = raw.loc[idx, ["date", "contract_date", "open_interest", "volume", "close"]].copy()
    front = front.sort_values("date").drop_duplicates("date")
    front["oi"] = front["open_interest"]
    front["doi"] = front["oi"].diff()
    mu = front["doi"].rolling(Z_WIN, min_periods=max(20, Z_WIN // 3)).mean()
    sd = front["doi"].rolling(Z_WIN, min_periods=max(20, Z_WIN // 3)).std()
    front["doi_z"] = (front["doi"] - mu) / sd.replace(0, np.nan)
    return front


def build_exposure(front: pd.DataFrame, mode: str, index: pd.DatetimeIndex) -> pd.Series:
    """Lag OI feature by 1 day for knowledge-time safety."""
    feat = front.set_index("date")["doi_z"].sort_index()
    feat = feat.reindex(index).ffill()
    lagged = feat.shift(1)
    if mode == "BASE":
        exp = pd.Series(1.0, index=index, name="exposure")
    elif mode == "OI_UP_DELEVER":
        exp = pd.Series(1.0, index=index, name="exposure")
        exp[lagged > Z_THR] = DELEVER
    elif mode == "OI_DOWN_DELEVER":
        exp = pd.Series(1.0, index=index, name="exposure")
        exp[lagged < -Z_THR] = DELEVER
    else:
        raise ValueError(mode)
    return exp.fillna(1.0)


def slice_stats(nav_df: pd.DataFrame, start: str | None = None) -> dict:
    s = nav_df.set_index(pd.to_datetime(nav_df["date"]))["nav"]
    if start:
        s = s[s.index >= pd.Timestamp(start)]
    return nav_stats(s)


def beats(challenger: dict, base: dict) -> bool:
    if challenger.get("util") is None or base.get("util") is None:
        return False
    if challenger.get("mdd") is None or base.get("mdd") is None:
        return False
    return (
        challenger["util"] > base["util"] + UTIL_EPS
        and abs(challenger["mdd"]) <= abs(base["mdd"]) + MDD_EPS
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", default="forward/e21/live_market.csv")
    ap.add_argument("--dividends", default="data/dividend_events/e22_dividend_events.csv")
    ap.add_argument("--tx", default="data/research_advanced/finmind_tx_futures_daily.csv")
    ap.add_argument("--out", default=str(OUT_DEFAULT))
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    market = pd.read_csv(args.market, dtype={"code": str})
    market["date"] = pd.to_datetime(market["date"])
    dividends = pd.read_csv(args.dividends, dtype={"code": str})
    front = load_tx_front_oi(Path(args.tx))
    front.to_csv(out / "tx_front_month_oi.csv", index=False)

    print("building E16 targets ...", flush=True)
    _p, _sleeve, target, regime = core.e16_features(market)
    dates = target.index

    modes = ["BASE", "OI_UP_DELEVER", "OI_DOWN_DELEVER"]
    books: dict[str, dict] = {}
    for mode in modes:
        print(f"Stage7 run {mode} ...", flush=True)
        exposure = build_exposure(front, mode, dates)
        exposure.to_csv(out / f"exposure_{mode}.csv", header=True)
        nav, fills, meta = core.simulate_core(
            market,
            target,
            regime,
            dividends,
            apply_e22=True,
            e45_exposure=None if mode == "BASE" else exposure,
        )
        full = slice_stats(nav)
        sealed = slice_stats(nav, start="2025-01-01")
        books[mode] = {
            "stats_full": full,
            "stats_sealed_2025p": sealed,
            "meta": {
                "exact_t1_ok": meta["exact_t1_ok"],
                "same_bar_fills": meta["same_bar_fills"],
                "dividend_cash_total": meta["dividend_cash_total"],
                "n_fills": int(len(fills)),
                "delever_days": int((exposure < 0.999).sum()) if mode != "BASE" else 0,
            },
        }
        nav.to_csv(out / f"{mode}_nav.csv", index=False)
        # fills kept out of default artifact pack (large); Exact T+1 flag is in meta
        del fills

    base = books["BASE"]["stats_full"]
    interesting = []
    for mode in ("OI_UP_DELEVER", "OI_DOWN_DELEVER"):
        if beats(books[mode]["stats_full"], base):
            interesting.append(mode)

    exact_ok = all(books[m]["meta"]["exact_t1_ok"] for m in modes)
    if interesting and exact_ok:
        decision = "STAGE7_TX_OI_INTERESTING_CONTINUE_SANDBOX"
        stance = (
            f"{', '.join(interesting)} clear pre-registered util/MDD bar vs BASE on full sample; "
            "still NO auto-promote. Sealed 2025+ is diagnostic only."
        )
    else:
        decision = "STOP_STAGE7_TX_OI_TIMING_OVERLAY"
        stance = (
            "Neither OI delever overlay clears util+MDD bar vs BASE (or Exact T+1 failed). "
            "Do not retune thresholds after sealed look."
        )

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stage": 7,
        "probe": "TX_front_month_OI_timing_overlay",
        "contract": "EXPERIMENTAL_SANDBOX_NO_PROMOTE",
        "params": {
            "z_window": Z_WIN,
            "z_threshold": Z_THR,
            "delever_exposure": DELEVER,
            "util_eps": UTIL_EPS,
            "mdd_eps": MDD_EPS,
            "oi_lag_days": 1,
        },
        "tx_rows": int(len(front)),
        "tx_date_min": str(front["date"].min().date()),
        "tx_date_max": str(front["date"].max().date()),
        "books": books,
        "interesting_modes": interesting,
        "exact_t1_ok": exact_ok,
        "decision": decision,
        "stance": stance,
        "promotion": False,
        "a0_untouched": True,
        "e22_v2_untouched": True,
    }
    (out / "stage7_tx_oi_report.json").write_text(json.dumps(report, indent=2, default=str) + "\n")

    md = f"""# Stage 7 Decision — TX OI timing overlay

Date: **2026-09-04**  
Probe: front-month TX `open_interest` Δ z-score → equity exposure overlay on early-stack (E16+E18+E22 ex-date)  
Artifacts: `{out}/`

## Pre-registered params
- z-window={Z_WIN}, |z| threshold={Z_THR}, delever exposure={DELEVER}
- OI lag=1 trading day; Exact T+1 preserved
- Bar: util > BASE + {UTIL_EPS} and |MDD| ≤ |BASE MDD| + {MDD_EPS}

## Full-sample results

| Book | CAGR | MDD | Util | Delever days |
|---|---:|---:|---:|---:|
| BASE | {books['BASE']['stats_full']['cagr']:.4f} | {books['BASE']['stats_full']['mdd']:.4f} | {books['BASE']['stats_full']['util']:.4f} | 0 |
| OI_UP_DELEVER | {books['OI_UP_DELEVER']['stats_full']['cagr']:.4f} | {books['OI_UP_DELEVER']['stats_full']['mdd']:.4f} | {books['OI_UP_DELEVER']['stats_full']['util']:.4f} | {books['OI_UP_DELEVER']['meta']['delever_days']} |
| OI_DOWN_DELEVER | {books['OI_DOWN_DELEVER']['stats_full']['cagr']:.4f} | {books['OI_DOWN_DELEVER']['stats_full']['mdd']:.4f} | {books['OI_DOWN_DELEVER']['stats_full']['util']:.4f} | {books['OI_DOWN_DELEVER']['meta']['delever_days']} |

Exact T+1: **{'PASS' if exact_ok else 'FAIL'}**

## Sealed 2025+ (diagnostic only — no retune)

| Book | Util |
|---|---:|
| BASE | {books['BASE']['stats_sealed_2025p']['util']} |
| OI_UP_DELEVER | {books['OI_UP_DELEVER']['stats_sealed_2025p']['util']} |
| OI_DOWN_DELEVER | {books['OI_DOWN_DELEVER']['stats_sealed_2025p']['util']} |

## Decision: `{decision}`

{stance}

Promotion: **false**. Official path remains E22_v2. Do not reopen stopped 3A/Stage4/Stage6 feature sets.
"""
    (out / "STAGE7_DECISION.md").write_text(md)
    print(json.dumps({"decision": decision, "interesting": interesting, "exact_t1_ok": exact_ok}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
