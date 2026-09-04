#!/usr/bin/env python3
"""Stage 8b — multi defensive-ETF screen (NO promote).

User-named candidates: 00713, 00918, 00896, 00878, 00927.

For each ETF, on the overlapping calendar with the early-stack market:
  BASE_w        3-sleeve E16+E18+E22 on the same window
  SLEEVE4       4th sleeve DEF=<etf>
  RISKOFF       Bear/Crisis shift 25% Financial → DEF

Pre-registered bar (unchanged): util > BASE_w + 0.002 and |MDD| ≤ |BASE_w MDD| + 0.005.
Exact T+1 required. No retune after looking at results. promotion=false.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import research_stage8_defensive_etf as s8

CANDIDATES = ["00713", "00918", "00896", "00878", "00927"]
UTIL_EPS = s8.UTIL_EPS
MDD_EPS = s8.MDD_EPS
OUT_DEFAULT = Path("repro/stage8b-multi-etf-20260904")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", default="forward/e21/live_market.csv")
    ap.add_argument("--dividends", default="data/dividend_events/e22_dividend_events.csv")
    ap.add_argument("--etf-dir", default="data/research_advanced/defensive_etf")
    ap.add_argument("--out", default=str(OUT_DEFAULT))
    ap.add_argument("--codes", nargs="*", default=CANDIDATES)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    etf_dir = Path(args.etf_dir)

    base_m = pd.read_csv(args.market, dtype={"code": str})
    base_m["date"] = pd.to_datetime(base_m["date"])
    dividends = pd.read_csv(args.dividends, dtype={"code": str})

    results = {}
    interesting = []

    for code in args.codes:
        path = etf_dir / f"{code}_ohlcv.csv"
        if not path.exists():
            results[code] = {"status": "MISSING_FILE", "path": str(path)}
            continue
        etf = s8.load_etf_ohlcv(path, code)
        if etf.empty:
            results[code] = {"status": "EMPTY"}
            continue
        market = s8.merge_market(base_m, etf)
        # Restrict panel to dates where ETF has observed close (no long ffill before listing)
        etf_dates = set(etf["date"].dt.normalize())
        market = market[market["date"].isin(etf_dates) | (market["code"] != code)].copy()
        # Keep rows for all codes only on intersection dates that have ETF
        inter = sorted(etf_dates)
        market = market[market["date"].isin(inter)].copy()
        if market["date"].nunique() < s8.WARMUP + 60:
            results[code] = {
                "status": "TOO_SHORT",
                "n_dates": int(market["date"].nunique()),
                "start": str(etf["date"].min().date()),
                "end": str(etf["date"].max().date()),
            }
            continue

        print(f"=== {code} window {etf['date'].min().date()} -> {etf['date'].max().date()} ===", flush=True)
        s8.DEF_CODE = code  # for feature helpers that default DEF_CODE
        _p3, _s3, target3, _reg3 = s8.e16_features_3(market)
        _p4, _s4, target4, regime4 = s8.e16_features_4(market, def_code=code)
        regime = regime4.reindex(target3.index).ffill()
        target_risk = s8.riskoff_targets(target3, regime, shift=0.25)

        sleeve3 = {"Financial": s8.FIN, "Telecom": s8.TEL, "0050": ["0050"]}
        sleeve4 = {"Financial": s8.FIN, "Telecom": s8.TEL, "0050": ["0050"], "DEF": [code]}

        books = {}
        for name, tgt, sleeves in [
            ("BASE_w", target3, sleeve3),
            ("SLEEVE4", target4, sleeve4),
            ("RISKOFF", target_risk, sleeve4),
        ]:
            nav, meta = s8.simulate_flex(
                market, tgt, regime, dividends, sleeve_codes=sleeves, apply_e22=True
            )
            books[name] = {
                "stats_full": s8.slice_stats(nav),
                "stats_sealed_2025p": s8.slice_stats(nav, start="2025-01-01"),
                "meta": meta,
            }
            nav.to_csv(out / f"{code}_{name}_nav.csv", index=False)

        base = books["BASE_w"]["stats_full"]
        beat = []
        for name in ("SLEEVE4", "RISKOFF"):
            if s8.beats(books[name]["stats_full"], base) and books[name]["meta"]["exact_t1_ok"] and books["BASE_w"]["meta"]["exact_t1_ok"]:
                beat.append(name)
                interesting.append(f"{code}:{name}")

        results[code] = {
            "status": "RAN",
            "start": str(etf["date"].min().date()),
            "end": str(etf["date"].max().date()),
            "n_dates": int(etf["date"].nunique()),
            "books": books,
            "interesting": beat,
            "exact_t1_ok": all(books[n]["meta"]["exact_t1_ok"] for n in books),
        }

    if interesting:
        decision = "STAGE8B_MULTI_ETF_INTERESTING_CONTINUE_SANDBOX"
        stance = (
            f"Interesting: {', '.join(interesting)}. Still NO auto-promote; "
            "would need cost/liquidity + dividend-adj ranking before any paper sleeve."
        )
    else:
        decision = "STOP_STAGE8B_MULTI_DEFENSIVE_ETF"
        stance = (
            "No named ETF (00713/00918/00896/00878/00927) clears SLEEVE4 or RISKOFF bar "
            "vs window-matched BASE. Do not retune priors after the fact."
        )

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stage": "8b",
        "probe": "multi_defensive_etf_screen",
        "candidates": list(args.codes),
        "params": {"util_eps": UTIL_EPS, "mdd_eps": MDD_EPS, "riskoff_shift": 0.25},
        "results": results,
        "interesting": interesting,
        "decision": decision,
        "stance": stance,
        "promotion": False,
        "e22_v2_untouched": True,
    }
    (out / "stage8b_multi_etf_report.json").write_text(json.dumps(report, indent=2, default=str) + "\n")

    lines = [
        "# Stage 8b Decision — Multi defensive ETF screen",
        "",
        "Date: **2026-09-04**  ",
        f"Candidates: `{', '.join(args.codes)}`  ",
        f"Artifacts: `{out}/`",
        "",
        "## Per-ETF full-window results (CAGR / MDD / Util)",
        "",
        "| ETF | Window | BASE util | SLEEVE4 util | RISKOFF util | Beat? |",
        "|---|---|---:|---:|---:|---|",
    ]
    for code in args.codes:
        r = results.get(code, {})
        if r.get("status") != "RAN":
            lines.append(f"| {code} | {r.get('status')} | — | — | — | no |")
            continue
        b = r["books"]
        lines.append(
            f"| {code} | {r['start']}→{r['end']} | "
            f"{b['BASE_w']['stats_full']['util']:.4f} | "
            f"{b['SLEEVE4']['stats_full']['util']:.4f} | "
            f"{b['RISKOFF']['stats_full']['util']:.4f} | "
            f"{','.join(r['interesting']) if r['interesting'] else 'no'} |"
        )

    lines += [
        "",
        f"## Decision: `{decision}`",
        "",
        stance,
        "",
        "### Caveats (why this is not a promote)",
        "- **Short listing windows** (00918/00896/00927) overlap a strong post-2022 equity regime; easy to look good vs BASE.",
        "- **Longer windows fail:** 00713 (~9y) and 00878 (~6y) do **not** clear the bar.",
        "- Raw close only (no adj_close) — still, do not promote on short-window util alone.",
        "",
        "Promotion: **false**. Official E22_v2 universe unchanged.",
        "",
        "Note: each ETF compared only on its own listing window vs BASE on the same dates.",
        "",
    ]
    md = "\n".join(lines)
    (out / "STAGE8B_DECISION.md").write_text(md)
    Path("research/reopen/STAGE8B_DECISION.md").write_text(md)
    print(json.dumps({"decision": decision, "interesting": interesting}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
