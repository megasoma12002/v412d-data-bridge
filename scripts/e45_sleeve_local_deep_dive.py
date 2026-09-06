#!/usr/bin/env python3
"""E45 PAPER sleeve-local deep-dive (post P1-P7 — research only).

Densify FIN / FIN+0050 / HIGH_BETA / ALL over alpha in {0.05,0.08,0.10},
cost multiples 1x/2x, plus crisis-year attribution for top held-out books.

Does NOT edit Soft-Frozen / DEFAULT / open observe / authorize stitch.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from e45_paper_harness import (
    BOOK_BASE,
    book_id_for_alpha,
    CLAIM_STATUS,
    E45_PROFILE_DEFAULT,
    ROOT,
    SLEEVE_FIN_0050,
    SLEEVE_FIN_ONLY,
    WINDOWS_STANDARD,
    blend_exposure,
    deltas_vs_base,
    e16_features,
    e45_full_exposure,
    load_dividends,
    load_market,
    run_early_stack,
    window_stats,
)
from e50_early_stack_combined_nav import FIN, TEL

OUT = ROOT / "repro/e45-sleeve-local-deep-dive"
RESEARCH = ROOT / "research/e45"
OPS = ROOT / "research/ops"

ALPHAS = (0.05, 0.08, 0.10)
COST_MULTS = (1.0, 2.0)
CRISIS_YEARS = (2015, 2018, 2020, 2022)
REF_YEARS = (2023, 2024)
FOCUS_WINDOWS = ("heldout_2019_plus", "sealed_2023_plus", "full")


def high_beta_sleeves(market: pd.DataFrame) -> tuple[str, ...]:
    wide = market.pivot(index="date", columns="code", values="close").sort_index().ffill()
    if "TAIEX" not in wide.columns:
        return ("Financial",)
    mkt = np.log(wide["TAIEX"]).diff()
    sleeve_px = {
        "Financial": wide[list(FIN)].mean(axis=1),
        "Telecom": wide[list(TEL)].mean(axis=1),
        "0050": wide["0050"] if "0050" in wide.columns else wide[list(FIN)].mean(axis=1),
    }
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


def book_tag(scope: str, alpha: float, cost: float) -> str:
    """Canonical ALL-scope IDs; sleeve scopes keep scope_A## _C#x labels."""
    a = int(round(alpha * 100))
    c = int(round(cost))
    if scope == "ALL":
        return f"{book_id_for_alpha(alpha)}_C{c}x"
    if scope == "BASE":
        return f"{BOOK_BASE}_C{c}x"
    return f"{scope}_A{a:02d}_C{c}x"


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


def main() -> None:
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)
    OPS.mkdir(parents=True, exist_ok=True)

    print("loading ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, _s, target, regime = e16_features(market)
    e45_full = e45_full_exposure(market, E45_PROFILE_DEFAULT)
    hb = high_beta_sleeves(market)
    print(f"high_beta_sleeves={hb}", flush=True)

    scopes = [
        ("ALL", None),
        ("FIN_ONLY", SLEEVE_FIN_ONLY),
        ("FIN_0050", SLEEVE_FIN_0050),
        ("HIGH_BETA", hb),
    ]

    books = {}
    navs = {}
    rows = []

    for cost in COST_MULTS:
        base_id = f"{BOOK_BASE}_C{int(cost)}x"
        print(f"sim {base_id} ...", flush=True)
        nav_b, fills_b, meta_b = run_early_stack(
            market, target, regime, dividends, e45_exposure=None, cost_multiple=cost
        )
        tag = base_id.lower()
        nav_b.to_csv(OUT / "outputs" / f"{tag}_daily_nav.csv", index=False)
        fills_b.to_csv(OUT / "outputs" / f"{tag}_fills.csv", index=False)
        win = {w: window_stats(nav_b, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
        books[base_id] = {
            "book": base_id,
            "scope": "BASE",
            "alpha": 0.0,
            "cost_multiple": float(cost),
            "sleeves": None,
            "mean_e45_exposure": meta_b.get("mean_e45_exposure"),
            "windows": win,
        }
        navs[base_id] = nav_b
        for w, st in win.items():
            rows.append({
                "book": base_id, "scope": "BASE", "alpha": 0.0,
                "cost_multiple": float(cost), "sleeves": "", "window": w,
                **{k: st.get(k) for k in ("cagr", "max_drawdown", "utility", "vol", "n_days")},
            })

        for scope_name, sleeves in scopes:
            for alpha in ALPHAS:
                bid = book_tag(scope_name, alpha, cost)
                exp = blend_exposure(e45_full, alpha)
                print(f"sim {bid} sleeves={sleeves} ...", flush=True)
                nav, fills, meta = run_early_stack(
                    market, target, regime, dividends,
                    e45_exposure=exp, e45_sleeve_names=sleeves, cost_multiple=cost,
                )
                tag = bid.lower()
                nav.to_csv(OUT / "outputs" / f"{tag}_daily_nav.csv", index=False)
                fills.to_csv(OUT / "outputs" / f"{tag}_fills.csv", index=False)
                win = {w: window_stats(nav, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
                books[bid] = {
                    "book": bid, "scope": scope_name, "alpha": float(alpha),
                    "cost_multiple": float(cost),
                    "sleeves": list(sleeves) if sleeves else None,
                    "mean_e45_exposure": meta.get("mean_e45_exposure"),
                    "windows": win,
                }
                navs[bid] = nav
                for w, st in win.items():
                    rows.append({
                        "book": bid, "scope": scope_name, "alpha": float(alpha),
                        "cost_multiple": float(cost),
                        "sleeves": ",".join(sleeves) if sleeves else "",
                        "window": w,
                        **{k: st.get(k) for k in ("cagr", "max_drawdown", "utility", "vol", "n_days")},
                    })

    pd.DataFrame(rows).to_csv(OUT / "outputs" / "sleeve_local_deep_window_metrics.csv", index=False)

    deltas = []
    for bid, meta in books.items():
        if meta["scope"] == "BASE":
            continue
        base_id = f"{BOOK_BASE}_C{int(meta['cost_multiple'])}x"
        base_w = books[base_id]["windows"]
        for w in FOCUS_WINDOWS:
            dlt = deltas_vs_base(base_w[w], meta["windows"][w])
            deltas.append({
                "book": bid, "scope": meta["scope"], "alpha": meta["alpha"],
                "cost_multiple": meta["cost_multiple"], "sleeves": meta["sleeves"],
                "window": w, **dlt,
                "book_cagr": meta["windows"][w].get("cagr"),
                "base_cagr": base_w[w].get("cagr"),
                "book_mdd": meta["windows"][w].get("max_drawdown"),
                "base_mdd": base_w[w].get("max_drawdown"),
            })
    delta_df = pd.DataFrame(deltas)
    delta_df.to_csv(OUT / "outputs" / "sleeve_local_deep_deltas_vs_base.csv", index=False)

    held_c1 = delta_df[
        (delta_df.window == "heldout_2019_plus") & (delta_df.cost_multiple == 1.0)
    ].sort_values("score", ascending=False)
    held_c2 = delta_df[
        (delta_df.window == "heldout_2019_plus") & (delta_df.cost_multiple == 2.0)
    ].sort_values("score", ascending=False)
    preferred = None if held_c1.empty else held_c1.iloc[0].to_dict()

    attr_books = [f"{BOOK_BASE}_C1x"]
    if preferred:
        attr_books.append(preferred["book"])
    for extra in held_c1["book"].head(3).tolist():
        if extra not in attr_books:
            attr_books.append(extra)
    for must in ("BLEND_E45_A05_C1x", "FIN_0050_A05_C1x", "HIGH_BETA_A05_C1x"):
        if must in books and must not in attr_books:
            attr_books.append(must)

    year_rows = []
    for bid in attr_books:
        nav = navs[bid]
        for y in list(CRISIS_YEARS) + list(REF_YEARS):
            st = year_stats(nav, y)
            year_rows.append({"book": bid, **st})
    pd.DataFrame(year_rows).to_csv(OUT / "outputs" / "sleeve_local_deep_year_stats.csv", index=False)

    year_deltas = []
    base_years = {r["year"]: r for r in year_rows if r["book"] == f"{BOOK_BASE}_C1x"}
    for bid in attr_books:
        if bid == f"{BOOK_BASE}_C1x":
            continue
        for y in list(CRISIS_YEARS) + list(REF_YEARS):
            b = base_years.get(y)
            c = next((r for r in year_rows if r["book"] == bid and r["year"] == y), None)
            if not b or not c or not b.get("available") or not c.get("available"):
                continue
            mdd_pp = None
            if b["max_drawdown"] is not None and c["max_drawdown"] is not None:
                mdd_pp = (abs(b["max_drawdown"]) - abs(c["max_drawdown"])) * 100.0
            ret_pp = None
            if b["ret"] is not None and c["ret"] is not None:
                ret_pp = (c["ret"] - b["ret"]) * 100.0
            year_deltas.append({
                "book": bid, "year": y,
                "mdd_improve_pp": mdd_pp, "ret_delta_pp": ret_pp,
                "is_crisis": y in CRISIS_YEARS,
            })
    yd_df = pd.DataFrame(year_deltas)
    yd_df.to_csv(OUT / "outputs" / "sleeve_local_deep_year_deltas.csv", index=False)

    share_2020 = None
    if preferred is not None and len(yd_df):
        pref_yd = yd_df[(yd_df.book == preferred["book"]) & (yd_df.is_crisis)]
        pos = float(pref_yd[pref_yd.mdd_improve_pp > 0]["mdd_improve_pp"].sum())
        y2020 = pref_yd[pref_yd.year == 2020]["mdd_improve_pp"]
        if pos > 0 and len(y2020) and y2020.iloc[0] is not None and float(y2020.iloc[0]) > 0:
            share_2020 = float(y2020.iloc[0] / pos)

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PAPER_ONLY",
        "ballot": "E45 PAPER sleeve-local deep-dive",
        "parent": "E45_PAPER_P1_P7_INTEGRATED_ANALYSIS",
        "high_beta_sleeves": list(hb),
        "alphas": list(ALPHAS),
        "cost_multiples": list(COST_MULTS),
        "heldout_preferred_c1x": preferred,
        "heldout_top5_c1x": held_c1.head(5).to_dict(orient="records"),
        "heldout_top5_c2x": held_c2.head(5).to_dict(orient="records"),
        "preferred_crisis_mdd_share_2020": share_2020,
        "claim_status": CLAIM_STATUS,
        "soft_frozen": "KEEP",
        "live_stitch": "FORBIDDEN",
        "observe_open_from_this": False,
    }
    (OUT / "reports" / "e45_sleeve_local_deep_dive.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )
    (RESEARCH / "E45_SLEEVE_LOCAL_DEEP_DIVE.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    lines = [
        "# E45 PAPER Sleeve-Local Deep-Dive",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Status: **PAPER ONLY** — Soft-Frozen **KEEP**; stitch **FORBIDDEN**; does **not** auto-OPEN observe.",
        "",
        f"High-beta sleeves (beta>=median vs TAIEX): **{', '.join(hb)}**",
        (
            f"Grid: alpha in {{{', '.join(str(a) for a in ALPHAS)}}} · "
            f"cost in {{{', '.join(str(int(c)) + 'x' for c in COST_MULTS)}}} · "
            "scopes ALL / FIN_ONLY / FIN_0050 / HIGH_BETA"
        ),
        "",
        "## Held-out deltas vs BASE @ 1x cost",
        "",
        "| Book | Scope | alpha | MDD dpp | Giveback pp | Score |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for _, r in held_c1.iterrows():
        lines.append(
            f"| {r['book']} | {r['scope']} | {r['alpha']:.2f} | "
            f"{pp(r['mdd_improve_pp'])} | {pp(r['cagr_giveback_pp'])} | {pp(r['score'])} |"
        )
    lines += [
        "",
        "## Held-out deltas vs BASE @ 2x cost",
        "",
        "| Book | Scope | alpha | MDD dpp | Giveback pp | Score |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for _, r in held_c2.iterrows():
        lines.append(
            f"| {r['book']} | {r['scope']} | {r['alpha']:.2f} | "
            f"{pp(r['mdd_improve_pp'])} | {pp(r['cagr_giveback_pp'])} | {pp(r['score'])} |"
        )
    sealed = delta_df[
        (delta_df.window == "sealed_2023_plus") & (delta_df.cost_multiple == 1.0)
    ].sort_values("score", ascending=False)
    lines += [
        "",
        "## Sealed deltas vs BASE @ 1x cost",
        "",
        "| Book | Scope | alpha | MDD dpp | Giveback pp | Score |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for _, r in sealed.iterrows():
        lines.append(
            f"| {r['book']} | {r['scope']} | {r['alpha']:.2f} | "
            f"{pp(r['mdd_improve_pp'])} | {pp(r['cagr_giveback_pp'])} | {pp(r['score'])} |"
        )
    lines += ["", "## Crisis-year MDD improve vs BASE (selected books)", ""]
    if len(yd_df):
        pivot = yd_df[yd_df.is_crisis].pivot_table(
            index="book", columns="year", values="mdd_improve_pp", aggfunc="first"
        )
        yrs = [y for y in CRISIS_YEARS if y in pivot.columns]
        header = "| Book | " + " | ".join(str(y) for y in yrs) + " |"
        sep = "|---|" + "|".join(["---:"] * len(yrs)) + "|"
        lines += [header, sep]
        for bid in pivot.index:
            cells = [pp(pivot.loc[bid, y] if y in pivot.columns else None) for y in yrs]
            lines.append(f"| {bid} | " + " | ".join(cells) + " |")

    lines += ["", "## Read-through (paper)", ""]
    if preferred:
        lines.append(
            f"1. Held-out preferred @1x: **`{preferred['book']}`** "
            f"(scope={preferred['scope']}, alpha={preferred['alpha']}, score={preferred['score']:.3f})."
        )
    if share_2020 is not None:
        lines.append(
            f"2. Preferred book's share of positive crisis-year MDD help in **2020**: "
            f"**{share_2020:.1%}** (same concentration risk as whole-book A05)."
        )
    all05 = held_c1[held_c1.book == "BLEND_E45_A05_C1x"]
    best_sl = held_c1[held_c1.scope != "ALL"]
    if not all05.empty and not best_sl.empty:
        a, s = all05.iloc[0], best_sl.iloc[0]
        if s["score"] > a["score"]:
            lines.append(
                f"3. Best sleeve-local (`{s['book']}`, score {s['score']:.3f}) **beats** "
                f"`BLEND_E45_A05_C1x` ({a['score']:.3f}) — structure edge holds on denser grid."
            )
        else:
            lines.append(
                f"3. Best sleeve-local (`{s['book']}`, score {s['score']:.3f}) does **not** beat "
                f"`BLEND_E45_A05_C1x` ({a['score']:.3f}) on denser grid."
            )
    if preferred:
        twin = held_c2[
            (held_c2.scope == preferred["scope"]) & (held_c2.alpha == preferred["alpha"])
        ]
        if not twin.empty:
            t = twin.iloc[0]
            lines.append(
                f"4. Preferred twin @2x (`{t['book']}`) score **{t['score']:.3f}** "
                f"(1x was {preferred['score']:.3f}) — cost stress check."
            )
    lines += [
        "5. Does **not** open sleeve-local observe or authorize stitch from this memo.",
        "6. Whole-book **blend-alpha=0.05 observe OPEN** is a separate ballot (`E45_BLEND005_OBSERVE_OPEN.md`).",
        "",
        "## Governance",
        "",
        f"- Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN · retired MDD narrative `{CLAIM_STATUS}`",
        "",
        "## Reproduce",
        "",
        "```bash",
        "python3 scripts/e45_sleeve_local_deep_dive.py",
        "```",
        "",
    ]
    memo = "\n".join(lines) + "\n"
    (RESEARCH / "E45_SLEEVE_LOCAL_DEEP_DIVE.md").write_text(memo)
    (OUT / "reports" / "E45_SLEEVE_LOCAL_DEEP_DIVE.md").write_text(memo)
    (OPS / "E45_SLEEVE_LOCAL_DEEP_DIVE.md").write_text(
        "# E45 PAPER Sleeve-Local Deep-Dive — Ops pointer\n\n"
        "Ballot: `E45 PAPER sleeve-local deep-dive` — **PAPER ONLY**\n\n"
        "Primary: `research/e45/E45_SLEEVE_LOCAL_DEEP_DIVE.md`\n"
        "Repro: `repro/e45-sleeve-local-deep-dive/`\n\n"
        "```bash\npython3 scripts/e45_sleeve_local_deep_dive.py\n```\n"
    )
    print("DONE", flush=True)
    if preferred:
        print(f"heldout preferred: {preferred['book']} score={preferred['score']}", flush=True)


if __name__ == "__main__":
    main()
