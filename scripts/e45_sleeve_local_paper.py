#!/usr/bin/env python3
"""E45 PAPER sleeve-local overlay (roadmap #6 — research only).

Apply E45 exposure only to selected sleeves (FIN / high-β), not whole book.
Scopes:
  ALL          — standard full-book exposure (reference)
  FIN_ONLY     — scale Financial sleeve only
  FIN_0050     — scale Financial + 0050 (leave Telecom)
  HIGH_BETA    — scale sleeves with hist |β|> median vs TAIEX

Does NOT edit Soft-Frozen / DEFAULT / observe / stitch.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from research_metric_helpers import mdd_delta_pp, cagr_delta_pp
from e50_early_stack_combined_nav import ALL, FIN, e16_features, nav_stats, simulate_core
import e45_crisis_core as e45

from e45_paper_harness import (
    BOOK_BASE,
    BOOK_BLEND_A05,
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


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/e45-sleeve-local"
RESEARCH = ROOT / "research/e45"
OPS = ROOT / "research/ops"
MARKET_PATH = ROOT / "forward/e21/live_market.csv"
DIV_PATH = ROOT / "data/dividend_events/e22_dividend_events.csv"

ALPHAS = (0.05, 0.25, 1.00)
WINDOWS = {k: WINDOWS_STANDARD[k] for k in ("full", "heldout_2019_plus", "sealed_2023_plus")}
FOCUS = ("heldout_2019_plus", "sealed_2023_plus", "full")




def high_beta_sleeves(market: pd.DataFrame) -> tuple[str, ...]:
    """Estimate sleeve daily returns vs TAIEX; keep sleeves with β >= median."""
    wide = market.pivot(index="date", columns="code", values="close").sort_index().ffill()
    if "TAIEX" not in wide.columns:
        return ("Financial",)
    mkt = np.log(wide["TAIEX"]).diff()
    sleeve_px = {
        "Financial": wide[list(FIN)].mean(axis=1),
        "Telecom": wide[[c for c in ALL if c not in FIN and c != "0050"]].mean(axis=1)
        if any(c not in FIN and c != "0050" for c in ALL)
        else wide[list(FIN)].mean(axis=1),
        "0050": wide["0050"] if "0050" in wide.columns else wide[list(FIN)].mean(axis=1),
    }
    # Fix Telecom codes from stack
    from e50_early_stack_combined_nav import TEL
    sleeve_px["Telecom"] = wide[list(TEL)].mean(axis=1)
    betas = {}
    for name, px in sleeve_px.items():
        r = np.log(px).diff()
        df = pd.concat([r, mkt], axis=1).dropna()
        df.columns = ["s", "m"]
        var = float(df["m"].var())
        betas[name] = float(df["s"].cov(df["m"]) / var) if var > 0 else 0.0
    med = float(np.median(list(betas.values())))
    keep = tuple(sorted([k for k, b in betas.items() if b >= med - 1e-12], key=lambda x: -betas[x]))
    return keep if keep else ("Financial",)



def pp(x):
    return "n/a" if x is None else f"{x:+.2f}"


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
    hb = high_beta_sleeves(market)
    print(f"high_beta_sleeves={hb}", flush=True)

    scopes = [
        (BOOK_BASE, None, 0.0, None),
        (BOOK_BLEND_A05, "ALL", 0.05, None),
        (BOOK_BLEND_A25, "ALL", 0.25, None),
        (BOOK_FULL, "ALL", 1.00, None),
        ("FIN_ONLY_A05", "FIN_ONLY", 0.05, ("Financial",)),
        ("FIN_ONLY_A25", "FIN_ONLY", 0.25, ("Financial",)),
        ("FIN_ONLY_FULL", "FIN_ONLY", 1.00, ("Financial",)),
        ("FIN_0050_A05", "FIN_0050", 0.05, ("Financial", "0050")),
        ("FIN_0050_A25", "FIN_0050", 0.25, ("Financial", "0050")),
        ("HIGH_BETA_A05", "HIGH_BETA", 0.05, hb),
        ("HIGH_BETA_A25", "HIGH_BETA", 0.25, hb),
    ]

    books = {}
    rows = []
    for book, scope_name, alpha, sleeves in scopes:
        exp = blend(e45_full, alpha)
        print(f"sim {book} scope={scope_name} alpha={alpha} sleeves={sleeves} ...", flush=True)
        nav, fills, meta = simulate_core(
            market, target, regime, dividends,
            apply_e22=True, apply_stock_div=True, e45_exposure=exp,
            e45_sleeve_names=sleeves,
        )
        tag = book.lower()
        nav.to_csv(OUT / "outputs" / f"{tag}_daily_nav.csv", index=False)
        fills.to_csv(OUT / "outputs" / f"{tag}_fills.csv", index=False)
        win = {w: window_stats(nav, a, b) for w, (a, b) in WINDOWS.items()}
        books[book] = {
            "book": book, "scope": scope_name, "alpha": float(alpha),
            "sleeves": list(sleeves) if sleeves else None,
            "mean_e45_exposure": meta.get("mean_e45_exposure"),
            "windows": win,
        }
        for w, st in win.items():
            rows.append({
                "book": book, "scope": scope_name, "alpha": float(alpha),
                "sleeves": ",".join(sleeves) if sleeves else "",
                "window": w, **{k: st.get(k) for k in ("cagr", "max_drawdown", "utility", "vol", "n_days")},
            })

    pd.DataFrame(rows).to_csv(OUT / "outputs" / "sleeve_local_window_metrics.csv", index=False)

    deltas = []
    base_w = books[BOOK_BASE]["windows"]
    for book, meta in books.items():
        for w in FOCUS:
            b, c = base_w[w], meta["windows"][w]
            mdd_pp = mdd_delta_pp(b.get("max_drawdown"), c.get("max_drawdown"))
            cagr_pp = cagr_delta_pp(b.get("cagr"), c.get("cagr"), missing_as_zero=True)
            score = None if mdd_pp is None or cagr_pp is None else mdd_pp - 0.5 * abs(cagr_pp)
            deltas.append({
                "book": book, "scope": meta["scope"], "alpha": meta["alpha"],
                "sleeves": meta["sleeves"], "window": w,
                "mdd_improve_pp": mdd_pp, "cagr_giveback_pp": cagr_pp, "score": score,
                "book_cagr": c.get("cagr"), "base_cagr": b.get("cagr"),
                "book_mdd": c.get("max_drawdown"), "base_mdd": b.get("max_drawdown"),
            })
    delta_df = pd.DataFrame(deltas)
    delta_df.to_csv(OUT / "outputs" / "sleeve_local_deltas_vs_base.csv", index=False)

    held = delta_df[(delta_df.window == "heldout_2019_plus") & (delta_df.book != BOOK_BASE)].sort_values("score", ascending=False)
    preferred = None if held.empty else held.iloc[0].to_dict()
    # compare FIN_ONLY_A05 vs BLEND_E45_A05 (ALL-scope)
    fin = held[held.book == "FIN_ONLY_A05"]
    all05 = held[held.book == BOOK_BLEND_A05]

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PAPER_ONLY",
        "ballot": "E45 PAPER sleeve-local overlay",
        "roadmap_priority": 6,
        "high_beta_sleeves": list(hb),
        "heldout_preferred": preferred,
        "soft_frozen": "KEEP",
        "live_stitch": "FORBIDDEN",
        "observe_sleeves_unchanged": True,
    }
    (OUT / "reports" / "e45_sleeve_local.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    (RESEARCH / "E45_SLEEVE_LOCAL.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")

    lines = [
        "# E45 PAPER Sleeve-Local Overlay",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Status: **PAPER ONLY** — Soft-Frozen **KEEP**; stitch **FORBIDDEN**; observe unchanged.",
        "",
        f"High-β sleeves (β≥median vs TAIEX): **{', '.join(hb)}**",
        "",
        "## Held-out deltas vs BASE",
        "",
        "| Book | Scope | α | Sleeves | MDD Δpp | Giveback pp | Score |",
        "|---|---|---:|---|---:|---:|---:|",
    ]
    for _, r in held.iterrows():
        sleeves = ",".join(r["sleeves"]) if isinstance(r["sleeves"], list) else (r["sleeves"] or "")
        lines.append(
            f"| {r['book']} | {r['scope']} | {r['alpha']:.2f} | {sleeves} | "
            f"{pp(r['mdd_improve_pp'])} | {pp(r['cagr_giveback_pp'])} | {pp(r['score'])} |"
        )

    lines += ["", "## Sealed deltas vs BASE", "",
              "| Book | Scope | α | MDD Δpp | Giveback pp | Score |",
              "|---|---|---:|---:|---:|---:|"]
    sealed = delta_df[(delta_df.window == "sealed_2023_plus") & (delta_df.book != BOOK_BASE)].sort_values("score", ascending=False)
    for _, r in sealed.iterrows():
        lines.append(
            f"| {r['book']} | {r['scope']} | {r['alpha']:.2f} | "
            f"{pp(r['mdd_improve_pp'])} | {pp(r['cagr_giveback_pp'])} | {pp(r['score'])} |"
        )

    lines += ["", "## Read-through (paper)", ""]
    if preferred:
        lines.append(f"1. Held-out preferred: **`{preferred['book']}`** (scope={preferred['scope']}, α={preferred['alpha']}).")
    if not fin.empty and not all05.empty:
        f, a = fin.iloc[0], all05.iloc[0]
        if f["score"] > a["score"]:
            lines.append(
                f"2. **FIN_ONLY_A05 beats BLEND_E45_A05** on held-out score ({f['score']:.3f} vs {a['score']:.3f}) — "
                "localizing cut can reduce CAGR tax."
            )
        else:
            lines.append(
                f"2. FIN_ONLY_A05 does **not** beat BLEND_E45_A05 on held-out score ({f['score']:.3f} vs {a['score']:.3f})."
            )
    lines += [
        "3. Does **not** open observe / authorize stitch.",
        "",
        "## Governance",
        "",
        "- Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN · retired MDD narrative",
        "",
        "## Reproduce",
        "",
        "```bash",
        "python3 scripts/e45_sleeve_local_paper.py",
        "```",
        "",
    ]
    memo = "\n".join(lines) + "\n"
    (RESEARCH / "E45_SLEEVE_LOCAL.md").write_text(memo)
    (OUT / "reports" / "E45_SLEEVE_LOCAL.md").write_text(memo)
    (OPS / "E45_SLEEVE_LOCAL.md").write_text(
        "# E45 PAPER Sleeve-Local — Ops pointer\n\n"
        "Ballot: `E45 PAPER sleeve-local overlay` — **PAPER ONLY** (roadmap #6)\n\n"
        "Primary: `research/e45/E45_SLEEVE_LOCAL.md`\n"
        "Repro: `repro/e45-sleeve-local/`\n\n"
        "```bash\npython3 scripts/e45_sleeve_local_paper.py\n```\n"
    )
    print("DONE", flush=True)
    if preferred:
        print(f"heldout preferred: {preferred['book']} score={preferred['score']}", flush=True)


if __name__ == "__main__":
    main()
