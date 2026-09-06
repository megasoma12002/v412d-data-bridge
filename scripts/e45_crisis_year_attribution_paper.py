#!/usr/bin/env python3
"""E45 PAPER crisis-year attribution for blend-α (roadmap #5 — research only).

Attribute defense to calendar crisis years for α ∈ {0, 0.05, 0.10, 0.25, 1.0}.
Years: 2011(partial), 2015, 2018, 2020, 2022 (+ 2024 non-crisis ref).

Does NOT edit Soft-Frozen / DEFAULT / observe / stitch. Frozen E3 untouched.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from research_metric_helpers import mdd_delta_pp, cagr_delta_pp
from e50_early_stack_combined_nav import ALL, e16_features, nav_stats, simulate_core
import e45_crisis_core as e45

from e45_paper_harness import (
    BOOK_BASE,
    BOOK_BLEND_A25,
    BOOK_FULL,
    CLAIM_STATUS,
    E45_PROFILE_DEFAULT,
    MARKET_PATH,
    DIV_PATH,
    ROOT,
    WINDOWS_STANDARD,
    blend_exposure,
    book_id_for_alpha,
    deltas_vs_base,
    e16_features,
    e45_full_exposure,
    load_dividends,
    load_market,
    run_early_stack,
    window_stats,
)
blend = blend_exposure  # harness alias
book_id = book_id_for_alpha  # harness alias


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/e45-crisis-year-attribution"
RESEARCH = ROOT / "research/e45"
OPS = ROOT / "research/ops"
MARKET_PATH = ROOT / "forward/e21/live_market.csv"
DIV_PATH = ROOT / "data/dividend_events/e22_dividend_events.csv"

ALPHAS = (0.00, 0.05, 0.10, 0.25, 1.00)
CRISIS_YEARS = (2011, 2015, 2018, 2020, 2022)
REF_YEARS = (2023, 2024)





def year_stats(nav: pd.DataFrame, year: int) -> dict:
    d = nav.copy()
    d["date"] = pd.to_datetime(d["date"])
    part = d[d["date"].dt.year == year].reset_index(drop=True)
    if len(part) < 20:
        return {"year": year, "n_days": int(len(part)), "ret": None, "max_drawdown": None, "available": False}
    path = part["nav"].to_numpy(float)
    ret = float(path[-1] / path[0] - 1.0)
    peak = np.maximum.accumulate(path)
    mdd = float(np.min(path / peak - 1.0))
    return {"year": year, "n_days": int(len(part)), "ret": ret, "max_drawdown": mdd, "available": True}


def pp(x):
    return "n/a" if x is None else f"{x:+.2f}"


def pct(x):
    return "n/a" if x is None else f"{x:.2%}"


def main() -> None:
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)
    OPS.mkdir(parents=True, exist_ok=True)

    print("loading ...", flush=True)
    market = load_market()
    dividends = pd.read_csv(DIV_PATH, dtype={"code": str}) if DIV_PATH.exists() else pd.DataFrame()
    _p, _s, target, regime = e16_features(market)
    close_eq = (
        market[market["code"].isin(ALL)]
        .pivot(index="date", columns="code", values="close")
        .sort_index()
        .ffill()
    )
    e45_full = e45.compute_exposure(close_eq, E45_PROFILE_DEFAULT)["exposure"]

    navs = {}
    rows = []
    for alpha in ALPHAS:
        bid = book_id(alpha)
        print(f"sim {bid} ...", flush=True)
        nav, fills, meta = simulate_core(
            market, target, regime, dividends,
            apply_e22=True, apply_stock_div=True, e45_exposure=blend(e45_full, alpha),
        )
        nav.to_csv(OUT / "outputs" / f"{bid.lower()}_daily_nav.csv", index=False)
        navs[bid] = nav
        for y in list(CRISIS_YEARS) + list(REF_YEARS):
            st = year_stats(nav, y)
            st.update({"book": bid, "alpha": float(alpha), "mean_e45_exposure": meta.get("mean_e45_exposure")})
            rows.append(st)

    year_df = pd.DataFrame(rows)
    year_df.to_csv(OUT / "outputs" / "crisis_year_book_metrics.csv", index=False)

    # deltas vs BASE per year
    deltas = []
    for alpha in ALPHAS:
        bid = book_id(alpha)
        for y in list(CRISIS_YEARS) + list(REF_YEARS):
            b = year_df[(year_df.book == book_id(0.0)) & (year_df.year == y)].iloc[0]
            c = year_df[(year_df.book == bid) & (year_df.year == y)].iloc[0]
            if not b["available"] or not c["available"]:
                deltas.append({
                    "book": bid, "alpha": float(alpha), "year": y,
                    "ret_delta_pp": None, "mdd_improve_pp": None, "available": False,
                    "book_ret": c["ret"], "base_ret": b["ret"], "book_mdd": c["max_drawdown"], "base_mdd": b["max_drawdown"],
                })
                continue
            # ret_delta_pp: book - base (negative = lag)
            ret_pp = (c["ret"] - b["ret"]) * 100.0
            mdd_pp = mdd_delta_pp(b["max_drawdown"], c["max_drawdown"])
            deltas.append({
                "book": bid, "alpha": float(alpha), "year": y,
                "ret_delta_pp": ret_pp, "mdd_improve_pp": mdd_pp, "available": True,
                "book_ret": c["ret"], "base_ret": b["ret"], "book_mdd": c["max_drawdown"], "base_mdd": b["max_drawdown"],
                "n_days": c["n_days"],
            })
    delta_df = pd.DataFrame(deltas)
    delta_df.to_csv(OUT / "outputs" / "crisis_year_deltas_vs_base.csv", index=False)

    # concentration: share of total MDD improvement across crisis years for each alpha
    conc = []
    for alpha in ALPHAS:
        if alpha <= 0:
            continue
        sub = delta_df[(delta_df.alpha == alpha) & (delta_df.year.isin(CRISIS_YEARS)) & (delta_df.available)]
        mdds = sub["mdd_improve_pp"].fillna(0).clip(lower=0)
        total = float(mdds.sum())
        for _, r in sub.iterrows():
            share = None if total <= 1e-12 else float((0.0 if r["mdd_improve_pp"] is None else max(float(r["mdd_improve_pp"]), 0.0)) / total)
            conc.append({
                "alpha": float(alpha), "book": book_id(alpha), "year": int(r["year"]),
                "mdd_improve_pp": r["mdd_improve_pp"], "share_of_positive_mdd_improve": share,
            })
    conc_df = pd.DataFrame(conc)
    conc_df.to_csv(OUT / "outputs" / "crisis_year_mdd_concentration.csv", index=False)

    # which year dominates for A05
    a05 = conc_df[conc_df.alpha == 0.05].sort_values("mdd_improve_pp", ascending=False)
    top_year = None if a05.empty else a05.iloc[0].to_dict()

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PAPER_ONLY",
        "ballot": "E45 PAPER crisis-year attribution",
        "roadmap_priority": 5,
        "profile": E45_PROFILE_DEFAULT,
        "alphas": list(ALPHAS),
        "crisis_years": list(CRISIS_YEARS),
        "ref_years": list(REF_YEARS),
        "note_2011": "partial year (market starts ~2011-12)",
        "soft_frozen": "KEEP",
        "live_stitch": "FORBIDDEN",
        "a05_top_crisis_year": top_year,
    }
    (OUT / "reports" / "e45_crisis_year_attribution.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    (RESEARCH / "E45_CRISIS_YEAR_ATTRIBUTION.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")

    lines = [
        "# E45 PAPER Crisis-Year Attribution (blend-α)",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Status: **PAPER ONLY** — Soft-Frozen **KEEP**; stitch **FORBIDDEN**; observe unchanged.",
        "",
        "## Setup",
        "",
        f"- Profile: `{E45_PROFILE_DEFAULT}` (frozen)",
        f"- Alphas: {', '.join(str(a) for a in ALPHAS)}",
        f"- Crisis years: {', '.join(str(y) for y in CRISIS_YEARS)} (2011 partial)",
        f"- Ref years: {', '.join(str(y) for y in REF_YEARS)}",
        "",
        "## Per-year deltas vs BASE",
        "",
        "| Book | α | Year | Ret Δpp | MDD Δpp | BASE MDD | Book MDD | n |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, r in delta_df.sort_values(["year", "alpha"]).iterrows():
        if not r["available"]:
            continue
        lines.append(
            f"| {r['book']} | {r['alpha']:.2f} | {int(r['year'])} | {pp(r['ret_delta_pp'])} | "
            f"{pp(r['mdd_improve_pp'])} | {pct(r['base_mdd'])} | {pct(r['book_mdd'])} | {int(r['n_days'])} |"
        )

    lines += [
        "",
        "## α=0.05 MDD-help concentration (crisis years)",
        "",
        "| Year | MDD Δpp | Share of positive help |",
        "|---:|---:|---:|",
    ]
    for _, r in a05.iterrows():
        sh = "n/a" if r["share_of_positive_mdd_improve"] is None else f"{100*r['share_of_positive_mdd_improve']:.1f}%"
        lines.append(f"| {int(r['year'])} | {pp(r['mdd_improve_pp'])} | {sh} |")

    lines += [
        "",
        "## Read-through (paper)",
        "",
        f"1. For α=0.05, largest crisis-year MDD help: "
        + (f"**{int(top_year['year'])}** ({pp(top_year['mdd_improve_pp'])} pp)." if top_year else "n/a"),
        "2. Check whether protection is diversified across 2015/2018/2020/2022 or single-year dominated.",
        "3. Ref years (2023/2024) show calm-period tax (ret Δ typically negative).",
        "4. Does **not** open observe / authorize stitch.",
        "",
        "## Governance",
        "",
        "- Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN · retired MDD narrative",
        "",
        "## Reproduce",
        "",
        "```bash",
        "python3 scripts/e45_crisis_year_attribution_paper.py",
        "```",
        "",
    ]
    memo = "\n".join(lines) + "\n"
    (RESEARCH / "E45_CRISIS_YEAR_ATTRIBUTION.md").write_text(memo)
    (OUT / "reports" / "E45_CRISIS_YEAR_ATTRIBUTION.md").write_text(memo)
    (OPS / "E45_CRISIS_YEAR_ATTRIBUTION.md").write_text(
        "# E45 PAPER Crisis-Year Attribution — Ops pointer\n\n"
        "Ballot: `E45 PAPER crisis-year attribution` — **PAPER ONLY** (roadmap #5)\n\n"
        "Primary: `research/e45/E45_CRISIS_YEAR_ATTRIBUTION.md`\n"
        "Repro: `repro/e45-crisis-year-attribution/`\n\n"
        "```bash\npython3 scripts/e45_crisis_year_attribution_paper.py\n```\n"
    )
    print("DONE", flush=True)
    if top_year:
        print(f"a05 top year: {int(top_year['year'])} mdd={top_year['mdd_improve_pp']:+.3f}", flush=True)


if __name__ == "__main__":
    main()
