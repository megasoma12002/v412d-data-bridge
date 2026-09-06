#!/usr/bin/env python3
"""E45 PAPER α cost/turnover stress (roadmap #4 — research only).

For mild blend alphas {0.00, 0.05, 0.10, 0.25, 1.00}, stress Exact-T+1
early-stack under fee multiples 0×/1×/2×/3× and report turnover.

Does NOT edit Soft-Frozen, DEFAULT, observe sleeves, or authorize stitch.
Does NOT retune frozen E3_VOLTARGET_WINNER.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

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
OUT = ROOT / "repro/e45-alpha-cost-turnover"
RESEARCH = ROOT / "research/e45"
OPS = ROOT / "research/ops"
MARKET_PATH = ROOT / "forward/e21/live_market.csv"
DIV_PATH = ROOT / "data/dividend_events/e22_dividend_events.csv"

ALPHAS = (0.00, 0.05, 0.10, 0.25, 1.00)
COST_MULTS = (0, 1, 2, 3)
FEE_KEYS = ("BUY_FEE", "SELL_FEE", "SLIP", "TAX_STOCK", "TAX_ETF")
FOCUS = ("heldout_2019_plus", "full")
WINDOWS = {
    "full": (None, None),
    "heldout_2019_plus": (date(2019, 1, 1), None),
    "sealed_2023_plus": (date(2023, 1, 1), None),
}






def turnover_metrics(nav: pd.DataFrame, fills: pd.DataFrame) -> dict:
    n = nav.copy()
    n["date"] = pd.to_datetime(n["date"])
    years = max((n["date"].iloc[-1] - n["date"].iloc[0]).days / 365.25, 1e-9)
    mean_nav = float(n["nav"].mean()) if len(n) else None
    if fills is None or len(fills) == 0:
        return {"n_fills": 0, "fees_tax_sum": 0.0, "gross_traded": 0.0, "turnover_per_year": 0.0, "years": years}
    f = fills.copy()
    fee_col = "fees_tax" if "fees_tax" in f.columns else ("fees_tax" if "fees_tax" in f.columns else None)
    # try common names
    for c in ("fees_tax", "fee_tax", "fees"):
        if c in f.columns:
            fee_col = c
            break
    gross_col = "gross" if "gross" in f.columns else None
    fees = float(pd.to_numeric(f[fee_col], errors="coerce").fillna(0).sum()) if fee_col else 0.0
    gross = float(pd.to_numeric(f[gross_col], errors="coerce").fillna(0).abs().sum()) if gross_col else 0.0
    to = (gross / mean_nav / years) if mean_nav and mean_nav > 0 else None
    return {
        "n_fills": int(len(f)),
        "fees_tax_sum": fees,
        "gross_traded": gross,
        "turnover_per_year": to,
        "years": float(years),
        "mean_nav": mean_nav,
    }


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

    rows = []
    for alpha in ALPHAS:
        exp = blend(e45_full, alpha)
        bid = book_id(alpha)
        for mult in COST_MULTS:
            print(f"sim {bid} alpha={alpha:.2f} cost×{mult} ...", flush=True)
            nav, fills, meta = simulate_core(
                market, target, regime, dividends,
                apply_e22=True, apply_stock_div=True, e45_exposure=exp,
                cost_multiple=float(mult),
            )
            tag = f"{bid.lower()}_x{mult}"
            nav.to_csv(OUT / "outputs" / f"{tag}_daily_nav.csv", index=False)
            fills.to_csv(OUT / "outputs" / f"{tag}_fills.csv", index=False)
            to = turnover_metrics(nav, fills)
            wins = {w: window_stats(nav, a, b) for w, (a, b) in WINDOWS.items()}
            for w, st in wins.items():
                rows.append({
                    "book": bid,
                    "alpha": float(alpha),
                    "cost_multiple": int(mult),
                    "window": w,
                    "cagr": st.get("cagr"),
                    "max_drawdown": st.get("max_drawdown"),
                    "utility": st.get("utility"),
                    "vol": st.get("vol"),
                    "n_days": st.get("n_days"),
                    "n_fills": to["n_fills"],
                    "fees_tax_sum": to["fees_tax_sum"],
                    "turnover_per_year": to["turnover_per_year"],
                    "mean_e45_exposure": meta.get("mean_e45_exposure"),
                    "exact_t1_ok": bool(meta.get("exact_t1_ok")),
                })

    metrics = pd.DataFrame(rows)
    metrics.to_csv(OUT / "outputs" / "alpha_cost_turnover_metrics.csv", index=False)

    # deltas vs BASE at same cost multiple
    deltas = []
    for mult in COST_MULTS:
        base = metrics[(metrics.book == book_id(0.0)) & (metrics.cost_multiple == mult)]
        for alpha in ALPHAS:
            bid = book_id(alpha)
            for w in FOCUS:
                b = base[base.window == w].iloc[0]
                c = metrics[(metrics.book == bid) & (metrics.cost_multiple == mult) & (metrics.window == w)].iloc[0]
                mdd_pp = mdd_delta_pp(b["max_drawdown"], c["max_drawdown"])
                cagr_pp = cagr_delta_pp(b["cagr"], c["cagr"], missing_as_zero=True)
                score = None if mdd_pp is None or cagr_pp is None else mdd_pp - 0.5 * abs(cagr_pp)
                deltas.append({
                    "book": bid,
                    "alpha": float(alpha),
                    "cost_multiple": int(mult),
                    "window": w,
                    "mdd_improve_pp": mdd_pp,
                    "cagr_giveback_pp": cagr_pp,
                    "score": score,
                    "turnover_per_year": c["turnover_per_year"],
                    "fees_tax_sum": c["fees_tax_sum"],
                    "n_fills": c["n_fills"],
                    "book_cagr": c["cagr"],
                    "base_cagr": b["cagr"],
                    "book_mdd": c["max_drawdown"],
                    "base_mdd": b["max_drawdown"],
                })
    delta_df = pd.DataFrame(deltas)
    delta_df.to_csv(OUT / "outputs" / "alpha_cost_turnover_deltas.csv", index=False)

    # held-out 1× ranking among alpha>0
    held1 = delta_df[(delta_df.window == "heldout_2019_plus") & (delta_df.cost_multiple == 1) & (delta_df.alpha > 0)].copy()
    held1 = held1.sort_values("score", ascending=False)
    preferred = None if held1.empty else held1.iloc[0].to_dict()

    # Does mild α still beat BASE on score at 2× and 3×?
    survival = []
    for alpha in (0.05, 0.10, 0.25):
        for mult in COST_MULTS:
            r = delta_df[(delta_df.alpha == alpha) & (delta_df.cost_multiple == mult) & (delta_df.window == "heldout_2019_plus")].iloc[0]
            survival.append({
                "alpha": alpha,
                "cost_multiple": mult,
                "mdd_improve_pp": r["mdd_improve_pp"],
                "cagr_giveback_pp": r["cagr_giveback_pp"],
                "score": r["score"],
                "score_nonneg": r["score"] is not None and r["score"] >= 0,
                "mdd_still_helps": r["mdd_improve_pp"] is not None and r["mdd_improve_pp"] > 0,
            })

    # turnover vs BASE at 1×
    to_cmp = []
    for alpha in ALPHAS:
        bid = book_id(alpha)
        r = metrics[(metrics.book == bid) & (metrics.cost_multiple == 1) & (metrics.window == "full")].iloc[0]
        b = metrics[(metrics.book == book_id(0.0)) & (metrics.cost_multiple == 1) & (metrics.window == "full")].iloc[0]
        to_cmp.append({
            "book": bid,
            "alpha": alpha,
            "turnover_per_year": r["turnover_per_year"],
            "base_turnover_per_year": b["turnover_per_year"],
            "turnover_delta": None if r["turnover_per_year"] is None else r["turnover_per_year"] - b["turnover_per_year"],
            "n_fills": r["n_fills"],
            "fees_tax_sum_1x": r["fees_tax_sum"],
        })

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PAPER_ONLY",
        "ballot": "E45 PAPER alpha cost/turnover stress",
        "roadmap_priority": 4,
        "profile": E45_PROFILE_DEFAULT,
        "alphas": list(ALPHAS),
        "cost_multiples": list(COST_MULTS),
        "fee_keys_scaled": list(FEE_KEYS),
        "soft_frozen": "KEEP",
        "live_stitch": "FORBIDDEN",
        "observe_sleeves_unchanged": True,
        "heldout_1x_preferred": preferred,
        "survival_heldout": survival,
        "turnover_vs_base_1x": to_cmp,
    }
    (OUT / "reports" / "e45_alpha_cost_turnover.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    (RESEARCH / "E45_ALPHA_COST_TURNOVER.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")

    lines = [
        "# E45 PAPER Alpha Cost / Turnover Stress",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Status: **PAPER ONLY** — Soft-Frozen **KEEP**; live stitch **FORBIDDEN**; observe unchanged.",
        "",
        "## Setup",
        "",
        f"- Profile: frozen `{E45_PROFILE_DEFAULT}`",
        f"- Alphas: {', '.join(str(a) for a in ALPHAS)}",
        f"- Cost multiples: {', '.join(str(m)+'×' for m in COST_MULTS)} on `{', '.join(FEE_KEYS)}`",
        "- Turnover: annualized |gross traded| / mean NAV",
        "",
        "## Held-out deltas vs BASE (by cost ×)",
        "",
        "| Book | α | ×cost | MDD Δpp | Giveback pp | Score | TO/yr | fees |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    sub = delta_df[delta_df.window == "heldout_2019_plus"].sort_values(["cost_multiple", "alpha"])
    for _, r in sub.iterrows():
        lines.append(
            f"| {r['book']} | {r['alpha']:.2f} | {r['cost_multiple']} | "
            f"{pp(r['mdd_improve_pp'])} | {pp(r['cagr_giveback_pp'])} | "
            f"{pp(r['score'])} | {r['turnover_per_year']:.3f} | {r['fees_tax_sum']:.0f} |"
        )

    lines += [
        "",
        "## Mild-α survival on held-out (score≥0 / MDD helps)",
        "",
        "| α | ×cost | MDD Δpp | Giveback | Score | score≥0 | MDD>0 |",
        "|---:|---:|---:|---:|---:|:---:|:---:|",
    ]
    for s in survival:
        lines.append(
            f"| {s['alpha']:.2f} | {s['cost_multiple']} | {pp(s['mdd_improve_pp'])} | "
            f"{pp(s['cagr_giveback_pp'])} | {pp(s['score'])} | "
            f"{'Y' if s['score_nonneg'] else 'N'} | {'Y' if s['mdd_still_helps'] else 'N'} |"
        )

    lines += [
        "",
        "## Turnover vs BASE at 1× (full sample)",
        "",
        "| Book | α | TO/yr | ΔTO vs BASE | fills | fees@1× |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for t in to_cmp:
        lines.append(
            f"| {t['book']} | {t['alpha']:.2f} | {t['turnover_per_year']:.3f} | "
            f"{pp(t['turnover_delta'])} | {t['n_fills']} | {t['fees_tax_sum_1x']:.0f} |"
        )

    a05_ok_3x = next(s for s in survival if s["alpha"] == 0.05 and s["cost_multiple"] == 3)
    lines += [
        "",
        "## Read-through (paper)",
        "",
        f"1. Held-out @1× preferred among α>0: **`{preferred['book'] if preferred else 'n/a'}`**.",
        f"2. α=0.05 at 3× cost: score≥0={'YES' if a05_ok_3x['score_nonneg'] else 'NO'}; "
        f"MDD help={'YES' if a05_ok_3x['mdd_still_helps'] else 'NO'}.",
        "3. Compare turnover deltas — mild α should not explode trading vs BASE.",
        "4. Does **not** open observe / authorize stitch.",
        "",
        "## Governance",
        "",
        "- Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN · −13.16% RETIRED",
        "",
        "## Reproduce",
        "",
        "```bash",
        "python3 scripts/e45_alpha_cost_turnover_paper.py",
        "```",
        "",
    ]
    memo = "\n".join(lines) + "\n"
    (RESEARCH / "E45_ALPHA_COST_TURNOVER.md").write_text(memo)
    (OUT / "reports" / "E45_ALPHA_COST_TURNOVER.md").write_text(memo)
    (OPS / "E45_ALPHA_COST_TURNOVER.md").write_text(
        "# E45 PAPER Alpha Cost/Turnover — Ops pointer\n\n"
        "Ballot: `E45 PAPER alpha cost/turnover stress` — **PAPER ONLY** (roadmap #4)\n\n"
        "Primary: `research/e45/E45_ALPHA_COST_TURNOVER.md`\n"
        "Repro: `repro/e45-alpha-cost-turnover/`\n\n"
        "```bash\npython3 scripts/e45_alpha_cost_turnover_paper.py\n```\n"
    )
    print("DONE", flush=True)
    if preferred:
        print(f"heldout@1x preferred: {preferred['book']} score={preferred['score']}", flush=True)


if __name__ == "__main__":
    main()
