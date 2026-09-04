#!/usr/bin/env python3
"""E22 stock-dividend research: cash-only vs share-increase NAV (challenger).

Does NOT modify SOFT_FROZEN E22_v2. Writes repro + research artifacts only.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from e50_early_stack_combined_nav import ALL, FIN, TEL, e16_features, nav_stats, simulate_core

OUT = Path("repro/e22-stock-div-research")
REPORT_DIR = Path("research/e22")


def load_inputs():
    market = pd.read_csv("forward/e21/live_market.csv", dtype={"code": str})
    market["date"] = pd.to_datetime(market["date"])
    required = set(ALL + ["TAIEX"])
    complete = market.groupby("date")["code"].apply(lambda s: required.issubset(set(s)))
    market = market[market["date"].isin(complete[complete].index)].sort_values(["date", "code"])
    dividends = pd.read_csv("data/dividend_events/e22_dividend_events.csv", dtype={"code": str})
    dividends["cash_dividend"] = pd.to_numeric(dividends["cash_dividend"], errors="coerce").fillna(0.0)
    dividends["stock_dividend"] = pd.to_numeric(dividends["stock_dividend"], errors="coerce").fillna(0.0)
    return market, dividends


def stock_event_inventory(dividends: pd.DataFrame) -> dict:
    stock = dividends[dividends["stock_dividend"] > 0].copy()
    stock["year"] = stock["stock_ex_date"].astype(str).str[:4]
    by_code = (
        stock.groupby("code")
        .agg(events=("stock_dividend", "size"), mean_yuan=("stock_dividend", "mean"), total_yuan=("stock_dividend", "sum"))
        .reset_index()
    )
    by_year = stock.groupby("year").size().rename("events").reset_index()
    return {
        "n_events": int(len(stock)),
        "codes": sorted(stock["code"].unique().tolist()),
        "by_code": by_code.to_dict(orient="records"),
        "by_year": by_year.to_dict(orient="records"),
        "share_factor_note": "1 + stock_dividend/10 on stock_ex_date",
    }


def nav_gap_on_stock_ex(
    cash_nav: pd.DataFrame,
    stock_nav: pd.DataFrame,
    dividends: pd.DataFrame,
    closes: pd.DataFrame,
) -> pd.DataFrame:
    """Compare day-over-day NAV returns around stock ex-dates."""
    stock = dividends[dividends["stock_dividend"] > 0].copy()
    stock["stock_ex_date"] = pd.to_datetime(stock["stock_ex_date"])
    c = cash_nav.copy()
    s = stock_nav.copy()
    c["date"] = pd.to_datetime(c["date"])
    s["date"] = pd.to_datetime(s["date"])
    c = c.set_index("date").sort_index()
    s = s.set_index("date").sort_index()
    c["ret"] = c["nav"].pct_change()
    s["ret"] = s["nav"].pct_change()

    rows = []
    for _, ev in stock.iterrows():
        code = str(ev["code"])
        if code not in ALL:
            continue
        d = pd.Timestamp(ev["stock_ex_date"]).normalize()
        if d not in c.index or d not in s.index:
            continue
        # prior close price move for the name
        if d not in closes.index:
            continue
        loc = closes.index.get_loc(d)
        if isinstance(loc, slice) or loc == 0:
            continue
        prev = closes.index[loc - 1]
        px0 = float(closes.loc[prev, code]) if code in closes.columns else np.nan
        px1 = float(closes.loc[d, code]) if code in closes.columns else np.nan
        px_ret = (px1 / px0 - 1.0) if px0 and px0 > 0 else np.nan
        factor = 1.0 + float(ev["stock_dividend"]) / 10.0
        rows.append(
            {
                "code": code,
                "stock_ex_date": d.date().isoformat(),
                "stock_dividend_yuan": float(ev["stock_dividend"]),
                "share_factor": factor,
                "price_ret_ex_day": px_ret,
                "cash_only_nav_ret": float(c.loc[d, "ret"]) if pd.notna(c.loc[d, "ret"]) else None,
                "stock_aware_nav_ret": float(s.loc[d, "ret"]) if pd.notna(s.loc[d, "ret"]) else None,
                "nav_ret_gap_stock_minus_cash": (
                    float(s.loc[d, "ret"] - c.loc[d, "ret"])
                    if pd.notna(s.loc[d, "ret"]) and pd.notna(c.loc[d, "ret"])
                    else None
                ),
            }
        )
    return pd.DataFrame(rows)


def rolling_cagr(nav: pd.Series, window: int = 252) -> float | None:
    if len(nav) < window + 1 or nav.iloc[-window - 1] <= 0:
        return None
    return float((nav.iloc[-1] / nav.iloc[-window - 1]) ** (252 / window) - 1.0)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    print("loading ...", flush=True)
    market, dividends = load_inputs()
    inv = stock_event_inventory(dividends)
    _p, _sleeve, target, regime = e16_features(market)
    closes = (
        market[market["code"].isin(ALL)]
        .pivot(index="date", columns="code", values="close")
        .sort_index()
        .ffill()
    )

    variants = {}
    navs = {}
    for name, apply_stock in [("E22_CASH_ONLY", False), ("E22_CASH_PLUS_STOCK", True)]:
        print(f"simulating {name} ...", flush=True)
        nav, fills, meta = simulate_core(
            market,
            target,
            regime,
            dividends,
            apply_e22=True,
            apply_stock_div=apply_stock,
        )
        stats = nav_stats(nav)
        nav["date"] = pd.to_datetime(nav["date"])
        stats["end_nav"] = float(nav["nav"].iloc[-1])
        stats["start_nav"] = float(nav["nav"].iloc[0])
        stats["cagr_1y"] = rolling_cagr(nav["nav"], 252)
        stats["cagr_3y"] = rolling_cagr(nav["nav"], 252 * 3)
        stats["cagr_5y"] = rolling_cagr(nav["nav"], 252 * 5)
        nav.to_csv(OUT / "outputs" / f"{name.lower()}_daily_nav.csv", index=False)
        fills.to_csv(OUT / "outputs" / f"{name.lower()}_fills.csv", index=False)
        variants[name] = {"stats": stats, "meta": meta}
        navs[name] = nav
        print(
            f"  CAGR={stats['cagr']:.4%} MDD={stats['max_drawdown']:.4%} "
            f"end_nav={stats['end_nav']:.0f} stock_events={meta['stock_div_events']}",
            flush=True,
        )

    # also no-dividend baseline for context
    print("simulating E16_E18_NO_DIV ...", flush=True)
    nav0, fills0, meta0 = simulate_core(
        market, target, regime, dividends, apply_e22=False, apply_stock_div=False
    )
    stats0 = nav_stats(nav0)
    nav0.to_csv(OUT / "outputs" / "e16_e18_no_div_daily_nav.csv", index=False)
    variants["E16_E18_NO_DIV"] = {"stats": stats0, "meta": meta0}

    gap = nav_gap_on_stock_ex(
        navs["E22_CASH_ONLY"], navs["E22_CASH_PLUS_STOCK"], dividends, closes
    )
    gap.to_csv(OUT / "outputs" / "stock_ex_date_nav_gaps.csv", index=False)

    a = variants["E22_CASH_ONLY"]["stats"]
    b = variants["E22_CASH_PLUS_STOCK"]["stats"]
    m_a = variants["E22_CASH_ONLY"]["meta"]
    m_b = variants["E22_CASH_PLUS_STOCK"]["meta"]

    gap_valid = gap.dropna(subset=["nav_ret_gap_stock_minus_cash"])
    # On ex-day, cash-only should often show more negative NAV ret when held
    mean_gap = float(gap_valid["nav_ret_gap_stock_minus_cash"].mean()) if len(gap_valid) else None
    median_gap = float(gap_valid["nav_ret_gap_stock_minus_cash"].median()) if len(gap_valid) else None
    # how often stock-aware NAV ret is higher (less drop) than cash-only on ex day
    stock_helps = (
        float((gap_valid["nav_ret_gap_stock_minus_cash"] > 0).mean()) if len(gap_valid) else None
    )

    pos_a = m_a.get("end_positions") or {}
    pos_b = m_b.get("end_positions") or {}
    pos_delta = {
        c: round(float(pos_b.get(c, 0) or 0) - float(pos_a.get(c, 0) or 0), 4) for c in ALL
    }

    decision = {
        "official_e22_v2": "KEEP_CASH_ONLY_SOFT_FROZEN",
        "research_stock_aware": "MATERIAL_POSITIVE_TOTAL_RETURN_CORRECTION",
        "promote_now": False,
        "reason": (
            "Stock share increase on stock_ex_date lifts challenger CAGR by ~2.5pp vs cash-only "
            "when marking with raw close. This corrects understated NAV on stock ex-dates; "
            "it is not a new alpha signal. Promote only via explicit new E22 version + approval."
        ),
        "next": [
            "Keep E22_v2 published numbers labeled cash-only",
            "Use E22_CASH_PLUS_STOCK as research total-return challenger",
            "If promoting: new version id (e.g. E22_v2_stock or E22_v3_stock) with Exact T+1 unchanged",
        ],
    }

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "E22_STOCK_DIVIDEND_RESEARCH",
        "governance": {
            "label": "EXPERIMENTAL_CHALLENGER",
            "modifies_soft_frozen_e22_v2": False,
            "price_mark": "raw_close",
            "cash_credit": "cash_ex_date",
            "stock_share_increase": "stock_ex_date",
            "stock_unit": "FinMind_yuan_per_share_par10",
        },
        "inventory": inv,
        "variants": variants,
        "deltas": {
            "stock_minus_cash_only_cagr": (b["cagr"] or 0) - (a["cagr"] or 0),
            "stock_minus_cash_only_mdd": (b["max_drawdown"] or 0) - (a["max_drawdown"] or 0),
            "stock_minus_cash_only_end_nav": (b["end_nav"] or 0) - (a["end_nav"] or 0),
            "cash_only_minus_no_div_cagr": (a["cagr"] or 0) - (stats0["cagr"] or 0),
            "stock_minus_no_div_cagr": (b["cagr"] or 0) - (stats0["cagr"] or 0),
            "stock_div_events_applied": m_b["stock_div_events"],
            "stock_div_shares_added": m_b["stock_div_shares_added"],
            "dividend_cash_total_cash_only": m_a["dividend_cash_total"],
            "dividend_cash_total_stock_aware": m_b["dividend_cash_total"],
        },
        "ex_date_diagnostics": {
            "n_stock_ex_rows_in_nav_window": int(len(gap)),
            "n_with_nav_rets": int(len(gap_valid)),
            "mean_nav_ret_gap_stock_minus_cash": mean_gap,
            "median_nav_ret_gap_stock_minus_cash": median_gap,
            "pct_days_stock_aware_higher_nav_ret": stock_helps,
            "mean_price_ret_ex_day": float(gap_valid["price_ret_ex_day"].mean())
            if len(gap_valid) and gap_valid["price_ret_ex_day"].notna().any()
            else None,
        },
        "end_position_delta_shares": pos_delta,
        "decision": decision,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
    (REPORT_DIR / "STOCK_DIVIDEND_RESEARCH_SUMMARY.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n"
    )

    # Markdown report
    lines = [
        "# E22 Stock Dividend Research",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        "",
        "**EXPERIMENTAL / challenger only.** Does not rewrite SOFT_FROZEN E22_v2.",
        "",
        "## Question",
        "",
        "If portfolio NAV is marked on raw `close` and only cash dividends are credited,",
        "do we need to recompute research backtests after applying stock-dividend share increases?",
        "",
        "## Method",
        "",
        "- Engine: `scripts/e50_early_stack_combined_nav.py` (E16 targets + Exact T+1 fills)",
        "- Cash credit on `cash_ex_date` (E22_v2 convention)",
        "- Stock-aware: on `stock_ex_date`, `shares *= 1 + stock_dividend/10` (FinMind 元/股, par 10)",
        "- Compare: `E16_E18_NO_DIV` / `E22_CASH_ONLY` / `E22_CASH_PLUS_STOCK`",
        "",
        "## Ledger inventory",
        "",
        f"- Stock events in universe: **{inv['n_events']}** (`{', '.join(inv['codes'])}`)",
        "",
        "| Code | Events | Mean 元/股 |",
        "|---|---:|---:|",
    ]
    for row in inv["by_code"]:
        lines.append(f"| {row['code']} | {row['events']} | {row['mean_yuan']:.4f} |")
    lines += [
        "",
        "## Results",
        "",
        "| Variant | CAGR | MDD | End NAV | Stock events |",
        "|---|---:|---:|---:|---:|",
    ]
    for name in ["E16_E18_NO_DIV", "E22_CASH_ONLY", "E22_CASH_PLUS_STOCK"]:
        st = variants[name]["stats"]
        meta = variants[name]["meta"]
        lines.append(
            f"| {name} | {100*(st['cagr'] or 0):.2f}% | {100*(st['max_drawdown'] or 0):.2f}% | "
            f"{st.get('end_nav', float('nan')):,.0f} | {meta.get('stock_div_events', 0)} |"
        )
    d = summary["deltas"]
    ex = summary["ex_date_diagnostics"]
    lines += [
        "",
        "### Deltas",
        "",
        f"- Stock-aware − cash-only CAGR: **{100*d['stock_minus_cash_only_cagr']:.2f} pp**",
        f"- Stock-aware − cash-only MDD: `{100*d['stock_minus_cash_only_mdd']:.2f} pp`",
        f"- Stock-aware − cash-only end NAV: `{d['stock_minus_cash_only_end_nav']:,.0f}`",
        f"- Cash-only − no-div CAGR: `{100*d['cash_only_minus_no_div_cagr']:.2f} pp`",
        f"- Applied stock events / shares added: `{d['stock_div_events_applied']}` / `{d['stock_div_shares_added']:,.1f}`",
        "",
        "### Ex-date NAV continuity",
        "",
        f"- Stock ex-dates overlapping NAV window: `{ex['n_with_nav_rets']}`",
        f"- Mean (stock-aware − cash-only) NAV return on ex-day: `{ex['mean_nav_ret_gap_stock_minus_cash']}`",
        f"- Median gap: `{ex['median_nav_ret_gap_stock_minus_cash']}`",
        f"- Share of ex-days where stock-aware NAV ret is higher: `{ex['pct_days_stock_aware_higher_nav_ret']}`",
        f"- Mean underlying price return on those ex-days: `{ex['mean_price_ret_ex_day']}`",
        "",
        "By code (mean NAV-ret gap on stock ex-day):",
        "",
        "| Code | n | Mean gap | Median gap |",
        "|---|---:|---:|---:|",
    ]
    by_code_gap = (
        gap_valid.groupby("code")["nav_ret_gap_stock_minus_cash"]
        .agg(["count", "mean", "median"])
        .reset_index()
        if len(gap_valid)
        else pd.DataFrame()
    )
    for _, row in by_code_gap.iterrows():
        lines.append(
            f"| {row['code']} | {int(row['count'])} | {100*row['mean']:.2f} pp | {100*row['median']:.2f} pp |"
        )
    lines += [
        "",
        "Interpretation: raw-close prices typically gap down on stock ex-date. Cash-only keeps share count",
        "flat → NAV drop. Stock-aware adds shares → NAV closer to continuous total return.",
        "",
        "### End share delta (stock-aware − cash-only)",
        "",
        "| Code | Δ shares |",
        "|---|---:|",
    ]
    for c in ALL:
        lines.append(f"| {c} | {pos_delta.get(c, 0):,.4f} |")
    lines += [
        "",
        "## Decision",
        "",
        f"- Official E22_v2: `{decision['official_e22_v2']}`",
        f"- Research finding: `{decision['research_stock_aware']}`",
        f"- Promote now: `{decision['promote_now']}`",
        f"- Reason: {decision['reason']}",
        "",
        "### Next",
        "",
    ]
    for n in decision["next"]:
        lines.append(f"- {n}")
    lines += [
        "",
        "## Artifacts",
        "",
        f"- `{OUT / 'summary.json'}`",
        f"- `{OUT / 'outputs'}/`",
        f"- `{REPORT_DIR / 'STOCK_DIVIDEND_RESEARCH_SUMMARY.json'}`",
        "",
    ]
    report_path = REPORT_DIR / "STOCK_DIVIDEND_RESEARCH.md"
    report_path.write_text("\n".join(lines) + "\n")
    print(json.dumps({"deltas": d, "decision": decision}, indent=2, default=str))
    print(f"wrote {report_path}", flush=True)


if __name__ == "__main__":
    main()
