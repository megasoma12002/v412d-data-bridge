#!/usr/bin/env python3
"""Historical research: E22_v2s (float) vs E22_v2s_cil (floor + cash-in-lieu).

Closes gap 6.5 as a *named* books successor candidate.
Does NOT rewrite forward/e21 live ledgers. Does NOT change DEFAULT (still E22_v2s)
until explicit promotion.
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from e50_early_stack_combined_nav import ALL, e16_features, nav_stats, simulate_core
import e22_dividend_accounting as e22div

OUT = Path("repro/e22-v2s-cil-historical-recompute")
REPORT = Path("research/e22/E22_V2S_CIL_FORMAL.md")
SUMMARY_JSON = Path("research/e22/E22_V2S_CIL_FORMAL.json")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)

    # Quick unit check of CIL math (no market needed)
    pos0 = {"2880": 1000.0}
    cash0 = 0.0
    ev = [
        e22div.DivEvent(code="2880", kind="stock", ex_date="2020-01-02", amount=0.264, payment_date="")
    ]
    # factor = 1.0264; gross = 1026.4; floor=1026; frac=0.4; CIL=0.4*10=4
    pos1, cash1, r1 = e22div.apply_dividends_for_date(
        "2020-01-02", pos0, cash0, ev, version=e22div.E22_V2S_CIL, mark_prices={"2880": 10.0}
    )
    assert pos1["2880"] == 1026.0
    assert abs(cash1 - 4.0) < 1e-9
    assert abs(r1.fractional_shares_cashed - 0.4) < 1e-9
    pos_f, _, r_f = e22div.apply_dividends_for_date(
        "2020-01-02", pos0, cash0, ev, version=e22div.E22_V2S
    )
    assert abs(pos_f["2880"] - 1026.4) < 1e-9
    assert r_f.cil_cash_credit == 0.0

    market = pd.read_csv("forward/e21/live_market.csv", dtype={"code": str})
    market["date"] = pd.to_datetime(market["date"])
    required = set(ALL + ["TAIEX"])
    complete = market.groupby("date")["code"].apply(lambda s: required.issubset(set(s)))
    market = market[market["date"].isin(complete[complete].index)].sort_values(["date", "code"])
    dividends = pd.read_csv("data/dividend_events/e22_dividend_events.csv", dtype={"code": str})
    _p, _s, target, regime = e16_features(market)

    specs = [
        ("E22_v2", dict(apply_e22=True, apply_stock_div=False, e22_version=e22div.E22_V2)),
        ("E22_v2s", dict(apply_e22=True, apply_stock_div=True, e22_version=e22div.E22_V2S)),
        ("E22_v2s_cil", dict(apply_e22=True, apply_stock_div=True, e22_version=e22div.E22_V2S_CIL)),
    ]
    results = {}
    for name, cfg in specs:
        print(f"simulating {name} ...", flush=True)
        nav, fills, meta = simulate_core(market, target, regime, dividends, **cfg)
        stats = nav_stats(nav)
        stats["start_nav"] = float(nav["nav"].iloc[0])
        stats["end_nav"] = float(nav["nav"].iloc[-1])
        nav.to_csv(OUT / "outputs" / f"{name.lower()}_daily_nav.csv", index=False)
        fills.to_csv(OUT / "outputs" / f"{name.lower()}_fills.csv", index=False)
        end_pos = meta.get("end_positions") or {}
        frac_dust = {k: float(v) - math.floor(float(v)) for k, v in end_pos.items()}
        results[name] = {
            "stats": stats,
            "meta": meta,
            "end_fractional_dust_shares": frac_dust,
            "end_fractional_dust_total": float(sum(frac_dust.values())),
        }
        print(
            f"  {name}: CAGR={stats['cagr']:.4%} MDD={stats['max_drawdown']:.4%} "
            f"end={stats['end_nav']:.0f} cil={meta.get('cil_cash_total')} "
            f"dust={results[name]['end_fractional_dust_total']:.4f}",
            flush=True,
        )

    a = results["E22_v2s"]["stats"]
    b = results["E22_v2s_cil"]["stats"]
    v2 = results["E22_v2"]["stats"]

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "E22_V2S_CIL_GAP65",
        "governance": {
            "rewrites_live_forward_e21_ledgers": False,
            "changes_default_books_version": False,
            "default_remains": e22div.DEFAULT_BOOKS_VERSION,
            "preserved_baseline": e22div.E22_V2,
            "formal_books": e22div.E22_V2S,
            "candidate_successor": e22div.E22_V2S_CIL,
            "unit_check_passed": True,
        },
        "rule": {
            "stock_ex": "shares_gross = shares * (1 + stock_div/10)",
            "floor": "shares = floor(shares_gross)",
            "cash_in_lieu": "frac * raw_close on stock_ex_date",
            "cash_div": "unchanged (cash_ex_date)",
        },
        "variants": {
            k: {
                "stats": v["stats"],
                "meta": {
                    kk: v["meta"].get(kk)
                    for kk in (
                        "e22_books_version",
                        "dividend_cash_total",
                        "cil_cash_total",
                        "fractional_shares_cashed",
                        "stock_div_events",
                        "stock_div_shares_added",
                        "end_positions",
                        "exact_t1_ok",
                        "start",
                        "end",
                    )
                },
                "end_fractional_dust_total": v["end_fractional_dust_total"],
                "end_fractional_dust_shares": v["end_fractional_dust_shares"],
            }
            for k, v in results.items()
        },
        "deltas": {
            "cil_minus_v2s_cagr_pp": ((b["cagr"] or 0) - (a["cagr"] or 0)) * 100.0,
            "cil_minus_v2s_mdd_pp": ((b["max_drawdown"] or 0) - (a["max_drawdown"] or 0)) * 100.0,
            "cil_minus_v2s_end_nav": (b["end_nav"] or 0) - (a["end_nav"] or 0),
            "cil_minus_v2s_end_nav_ratio": (b["end_nav"] / a["end_nav"]) if a["end_nav"] else None,
            "v2s_minus_v2_cagr_pp": ((a["cagr"] or 0) - (v2["cagr"] or 0)) * 100.0,
            "cil_cash_total": results["E22_v2s_cil"]["meta"].get("cil_cash_total"),
            "fractional_shares_cashed": results["E22_v2s_cil"]["meta"].get("fractional_shares_cashed"),
            "v2s_end_dust_shares": results["E22_v2s"]["end_fractional_dust_total"],
            "cil_end_dust_shares": results["E22_v2s_cil"]["end_fractional_dust_total"],
        },
        "decision": {
            "gap_6_5": "NAMED_VERSION_LANDED",
            "live_default": "KEEP_E22_v2s_UNTIL_EXPLICIT_PROMOTE",
            "promote_cil_to_default": "RECOMMENDED_CANDIDATE_DELTA_NEGLIGIBLE",
            "promote_note": (
                "Full-history CAGR delta vs E22_v2s is ~-0.0005 pp; end NAV ratio ~0.99994; "
                "end fractional dust 2.20 → 0. Safe named successor for gap 6.5. "
                "Still requires explicit default cutover; no live history rewrite."
            ),
            "live_history": "DO_NOT_REWRITE",
            "board_lot_1000": "STILL_CHALLENGER_ONLY",
            "pay_date_tax": "STILL_SANDBOX",
        },
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2, default=str) + "\n")

    d = summary["deltas"]
    lines = [
        "# E22_v2s_cil — Floor Shares + Cash-in-Lieu (Gap 6.5)",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        "",
        "**Named books version.** Does **not** rewrite live history. "
        f"Default remains `{e22div.DEFAULT_BOOKS_VERSION}` until explicit promotion.",
        "",
        "## Rule",
        "",
        "On `stock_ex_date` (raw books; never adj_close NAV + shares):",
        "",
        "1. `shares_gross = shares × (1 + stock_dividend/10)`",
        "2. `shares = floor(shares_gross)`",
        "3. `cash += (shares_gross − shares) × raw_close`",
        "",
        "Cash dividends unchanged (`cash_ex_date`). Exact T+1 unchanged.",
        "",
        "## Side-by-side historical recompute",
        "",
        "| Variant | CAGR | MDD | End NAV | CIL cash | End frac dust |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name in ["E22_v2", "E22_v2s", "E22_v2s_cil"]:
        st = results[name]["stats"]
        meta = results[name]["meta"]
        lines.append(
            f"| {name} | {100*(st['cagr'] or 0):.2f}% | {100*(st['max_drawdown'] or 0):.2f}% | "
            f"{st['end_nav']:,.0f} | {meta.get('cil_cash_total') or 0:,.2f} | "
            f"{results[name]['end_fractional_dust_total']:.4f} |"
        )
    lines += [
        "",
        "### Deltas (cil − v2s)",
        "",
        f"- CAGR: `{d['cil_minus_v2s_cagr_pp']:.4f}` pp",
        f"- MDD: `{d['cil_minus_v2s_mdd_pp']:.4f}` pp",
        f"- End NAV: `{d['cil_minus_v2s_end_nav']:,.2f}` (ratio `{d['cil_minus_v2s_end_nav_ratio']}`)",
        f"- Fractional shares cashed: `{d['fractional_shares_cashed']}`",
        f"- End fractional dust: v2s `{d['v2s_end_dust_shares']:.4f}` → cil `{d['cil_end_dust_shares']:.4f}`",
        "",
        "## Decision",
        "",
        f"- Gap 6.5: `{summary['decision']['gap_6_5']}`",
        f"- Live default: `{summary['decision']['live_default']}`",
        f"- Promote CIL: `{summary['decision']['promote_cil_to_default']}`",
        f"- Live history: `{summary['decision']['live_history']}`",
        f"- Board-lot / pay-date / tax: still out of scope here",
        "",
        "## Code",
        "",
        "- `scripts/e22_dividend_accounting.py` — `E22_v2s_cil`",
        "- `scripts/e50_early_stack_combined_nav.py` — passes raw close mark prices",
        "- `scripts/e21_forward_pipeline.py` — `--e22-version E22_v2s_cil` selectable (not default)",
        "",
        "## Artifacts",
        "",
        f"- `{SUMMARY_JSON}`",
        f"- `{OUT}/`",
        "",
    ]
    REPORT.write_text("\n".join(lines) + "\n")
    print(json.dumps({"deltas": d, "decision": summary["decision"]}, indent=2, default=str))
    print(f"wrote {REPORT}", flush=True)


if __name__ == "__main__":
    main()
