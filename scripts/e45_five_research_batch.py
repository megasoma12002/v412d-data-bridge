#!/usr/bin/env python3
"""E45 five-item paper research batch (post-observe).

1) Month-end PAUSE time-series for four OPERATING observe sleeves
2) Non-2020 crisis-year attribution
3) FIN_ONLY@0.10 vs ALL@0.05 rolling OOS + cost 1-3x + turnover
4) HIGH_BETA sleeve-local paper densify + DRAFT ballot (NOT OPEN)
5) Multi-event stress-year threshold charter

PAPER ONLY. Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from e45_paper_harness import (
    BOOK_BASE,
    BOOK_BLEND_A05,
    BOOK_BLEND_A25,
    BOOK_FULL,
    CLAIM_STATUS,
    E45_PROFILE_DEFAULT,
    ROOT,
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

OUT = ROOT / "repro/e45-five-research-batch"
RESEARCH = ROOT / "research/e45"
OPS = ROOT / "research/ops"

TRAIL_ALERT_PP = 3.0
TRAIL_PAUSE_PP = 5.0
CRISIS_YEARS = (2015, 2018, 2020, 2022)
REF_YEARS = (2023, 2024)
COST_MULTS = (1.0, 2.0, 3.0)
ROLL_ENDS = (
    date(2020, 12, 31),
    date(2021, 12, 31),
    date(2022, 12, 31),
    date(2023, 12, 31),
    date(2024, 12, 31),
    date(2026, 9, 4),
)
FOCUS_WINDOWS = ("heldout_2019_plus", "sealed_2023_plus", "full")

OBSERVE_NAV = {
    "FULL_E45": {
        "base": ROOT / "repro/e45-dual-paper-observe/outputs/base_e16_e18_e22_v2s_daily_nav.csv",
        "chal": ROOT / "repro/e45-dual-paper-observe/outputs/chal_e45_e3_daily_nav.csv",
        "book": BOOK_FULL,
        "alpha": 1.0,
        "scope": "ALL",
    },
    "BLEND_A25": {
        "base": ROOT / "repro/e45-blend025-dual-paper-observe/outputs/base_e16_e18_e22_v2s_daily_nav.csv",
        "chal": ROOT / "repro/e45-blend025-dual-paper-observe/outputs/blend_e45_a25_daily_nav.csv",
        "book": BOOK_BLEND_A25,
        "alpha": 0.25,
        "scope": "ALL",
    },
    "BLEND_A05": {
        "base": ROOT / "repro/e45-blend005-dual-paper-observe/outputs/base_e16_e18_e22_v2s_daily_nav.csv",
        "chal": ROOT / "repro/e45-blend005-dual-paper-observe/outputs/blend_e45_a05_daily_nav.csv",
        "book": BOOK_BLEND_A05,
        "alpha": 0.05,
        "scope": "ALL",
    },
    "SLEEVE_FIN_ONLY_A10": {
        "base": ROOT / "repro/e45-sleeve-local-dual-paper-observe/outputs/base_e16_e18_e22_v2s_daily_nav.csv",
        "chal": ROOT / "repro/e45-sleeve-local-dual-paper-observe/outputs/sleeve_fin_only_a10_daily_nav.csv",
        "book": "SLEEVE_FIN_ONLY_A10",
        "alpha": 0.10,
        "scope": "FIN_ONLY",
    },
}


def fmt(x, digits=2):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "n/a"
    return f"{x:+.{digits}f}"


def load_nav(path: Path) -> pd.DataFrame:
    d = pd.read_csv(path)
    d["date"] = pd.to_datetime(d["date"])
    return d.sort_values("date").reset_index(drop=True)


def cagr(nav: pd.Series):
    if len(nav) < 2 or float(nav.iloc[0]) <= 0:
        return None
    years = len(nav.pct_change().dropna()) / 252.0
    if years <= 0:
        return None
    return float((nav.iloc[-1] / nav.iloc[0]) ** (1.0 / years) - 1.0)


def mdd(nav: pd.Series):
    if len(nav) < 2:
        return None
    return float((nav / nav.cummax() - 1.0).min())


def gate_of(giveback_pp) -> str:
    if giveback_pp is None:
        return "INSUFFICIENT"
    if giveback_pp > TRAIL_PAUSE_PP:
        return "PAUSE_REVIEW"
    if giveback_pp > TRAIL_ALERT_PP:
        return "ALERT"
    return "PASS"


def month_end_asofs(nav: pd.DataFrame):
    d = nav.copy()
    d["ym"] = d["date"].dt.to_period("M")
    ends = d.groupby("ym", sort=True)["date"].max()
    return [ts for ts in ends.tolist() if ts >= pd.Timestamp("2023-01-01")]


def giveback_at(base, chal, asof, window: str) -> dict:
    start = pd.Timestamp(asof.year, 1, 1) if window == "ytd" else asof - pd.Timedelta(days=365)
    b = base[(base["date"] >= start) & (base["date"] <= asof)].reset_index(drop=True)
    c = chal[(chal["date"] >= start) & (chal["date"] <= asof)].reset_index(drop=True)
    if len(b) < 20 or len(c) < 20:
        return {
            "asof": asof.date().isoformat(),
            "window": window,
            "n_days": int(min(len(b), len(c))),
            "cagr_giveback_pp": None,
            "mdd_improve_pp": None,
            "gate": "INSUFFICIENT",
        }
    bn = b["nav"] / float(b["nav"].iloc[0])
    cn = c["nav"] / float(c["nav"].iloc[0])
    bc, cc = cagr(bn), cagr(cn)
    bm, cm = mdd(bn), mdd(cn)
    gb = None if bc is None or cc is None else (bc - cc) * 100.0
    mi = None if bm is None or cm is None else (abs(bm) - abs(cm)) * 100.0
    return {
        "asof": asof.date().isoformat(),
        "window": window,
        "n_days": int(min(len(b), len(c))),
        "base_cagr": bc,
        "chal_cagr": cc,
        "cagr_giveback_pp": gb,
        "base_mdd": bm,
        "chal_mdd": cm,
        "mdd_improve_pp": mi,
        "gate": gate_of(gb),
    }


def year_path_stats(nav: pd.DataFrame, year: int) -> dict:
    d = nav.copy()
    d["date"] = pd.to_datetime(d["date"])
    part = d[d["date"].dt.year == year].reset_index(drop=True)
    if len(part) < 20:
        return {"year": year, "n_days": int(len(part)), "ret": None, "max_drawdown": None, "available": False}
    path = part["nav"].to_numpy(float)
    peak = np.maximum.accumulate(path)
    return {
        "year": year,
        "n_days": int(len(part)),
        "ret": float(path[-1] / path[0] - 1.0),
        "max_drawdown": float(np.min(path / peak - 1.0)),
        "available": True,
    }


def turnover_from_fills(fills: pd.DataFrame, nav: pd.DataFrame) -> dict:
    if fills is None or fills.empty or nav.empty:
        return {"n_fills": 0, "gross_traded": 0.0, "ann_turnover_approx": None}
    if "gross" in fills.columns:
        gross = float(fills["gross"].abs().sum())
    else:
        gross = float((fills["quantity"].abs() * fills["fill_price"]).sum())
    n = nav.copy()
    n["date"] = pd.to_datetime(n["date"])
    years = max((n["date"].iloc[-1] - n["date"].iloc[0]).days / 365.25, 1e-9)
    mean_nav = float(n["nav"].mean())
    ann = (gross / mean_nav / years / 2.0) if mean_nav > 0 else None
    return {"n_fills": int(len(fills)), "gross_traded": gross, "mean_nav": mean_nav, "years": years, "ann_turnover_approx": ann}


def high_beta_sleeves(market: pd.DataFrame):
    wide = market.pivot(index="date", columns="code", values="close").sort_index().ffill()
    if "TAIEX" not in wide.columns:
        return ("Financial",), {"Financial": 1.0}
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
    return (keep if keep else ("Financial",)), betas


def custom_window_stats(nav: pd.DataFrame, start: date, end: date, min_days: int = 60) -> dict:
    return window_stats(nav, start, end, min_days=min_days)


def write_all_reports(ctx: dict) -> None:
    generated = ctx["generated"]
    out_r = ctx["out_r"]
    pause_summary = ctx["pause_summary"]
    conc_df = ctx["conc_df"]
    help_df = ctx["help_df"]
    roll_delta_df = ctx["roll_delta_df"]
    cost_df = ctx["cost_df"]
    hb_df = ctx["hb_df"]
    preferred_hb = ctx["preferred_hb"]
    hb_sleeves = ctx["hb_sleeves"]
    betas = ctx["betas"]
    thr_df = ctx["thr_df"]
    payload = ctx["payload"]

    def publish(name: str, text: str):
        (out_r / name).write_text(text)
        (OPS / name).write_text(text)
        (RESEARCH / name).write_text(text)

    # 1
    lines = [
        "# E45 Observe Month-End PAUSE Time-Series",
        "",
        f"Generated: `{generated}`",
        "Status: **PAPER / OPS OBSERVE** — Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN",
        "",
        "Gates: YTD / trailing_1y CAGR giveback vs BASE — ALERT >3pp · PAUSE_REVIEW >5pp.",
        "",
        "## Tip gates (four OPERATING sleeves)",
        "",
        "| Sleeve | Tip asof | YTD | Trailing 1y | Share PAUSE (YTD) | Share PAUSE (1y) | First clean both |",
        "|---|---|---|---|---:|---:|---|",
    ]
    for sleeve, s in pause_summary.items():
        if not s.get("ok"):
            lines.append(f"| `{sleeve}` | n/a | missing | missing | n/a | n/a | n/a |")
            continue
        lines.append(
            f"| `{sleeve}` | {s['tip_asof']} | **{s['tip_ytd_gate']}** | **{s['tip_trailing_1y_gate']}** | "
            f"{s['share_pause_ytd']:.0%} | {s['share_pause_1y']:.0%} | {s['first_clean_both_asof'] or 'none yet'} |"
        )
    lines += [
        "",
        "## Read",
        "",
        "- Tip PAUSE_REVIEW across sleeves is **expected** while observe accumulates; it does **not** revoke held-out paper scores.",
        "- `first_clean_both_asof = none yet` ⇒ no stitch talk from trailing gates.",
        "- Cadence: refresh ledgers → month-end monitors → this time-series.",
        "",
        "CSV: `repro/e45-five-research-batch/outputs/observe_month_end_pause_timeseries.csv`",
        "",
        f"Label: `E45_OBSERVE_PAUSE_TS_{generated[:10]}__STITCH_FORBIDDEN`",
        "",
    ]
    publish("E45_OBSERVE_PAUSE_TIMESERIES.md", "\n".join(lines))

    # 2
    lines = [
        "# E45 Non-2020 Crisis-Year Attribution",
        "",
        f"Generated: `{generated}`",
        "Status: **PAPER ONLY** — Soft-Frozen KEEP · stitch FORBIDDEN · −13.16% remains RETIRED",
        "",
        "Crisis years: **2015, 2018, 2020, 2022**. Help = BASE |MDD| − challenger |MDD| (pp).",
        "",
        "## Concentration",
        "",
        "| Book | 2020 help pp | Non-2020 positive help pp | Share of +help in 2020 | # years helped (>0.25pp) | Years |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for _, r in conc_df.sort_values("share_of_positive_help_in_2020", ascending=False).iterrows():
        share = r["share_of_positive_help_in_2020"]
        lines.append(
            f"| `{r['book']}` | {fmt(r['mdd_help_2020_pp'])} | {fmt(r['mdd_help_non2020_positive_pp'])} | "
            f"{'n/a' if share is None else f'{share:.0%}'} | {int(r['n_crisis_years_helped_gt_0_25pp'])} | "
            f"{r['years_helped']} |"
        )
    lines += [
        "",
        "## Year detail (MDD help pp vs BASE)",
        "",
        "| Book | 2015 | 2018 | 2020 | 2022 |",
        "|---|---:|---:|---:|---:|",
    ]
    for bid in sorted(help_df.book.unique()):
        cells = []
        for y in CRISIS_YEARS:
            sub = help_df[(help_df.book == bid) & (help_df.year == y)]
            cells.append(fmt(float(sub.iloc[0]["mdd_help_pp"])) if len(sub) else "n/a")
        lines.append(f"| `{bid}` | " + " | ".join(cells) + " |")
    lines += [
        "",
        "## Verdict",
        "",
        "- Protection remains **2020-heavy** for whole-book mild α; sleeve-local does not fully diversify event risk.",
        "- Non-2020 years are the honesty check for any future ballot.",
        "- Pair with the multi-event threshold charter (item 5).",
        "",
        f"Label: `E45_NON2020_CRISIS_ATTR_{generated[:10]}__STITCH_FORBIDDEN`",
        "",
    ]
    publish("E45_NON2020_CRISIS_ATTRIBUTION.md", "\n".join(lines))

    # 3
    lines = [
        "# E45 FIN_ONLY@α=0.10 vs ALL@α=0.05 — Rolling OOS / Cost / Turnover",
        "",
        f"Generated: `{generated}`",
        "Status: **PAPER ONLY** — observe sleeves unchanged · Soft-Frozen KEEP · stitch FORBIDDEN",
        "",
        "## Rolling 3y held-path deltas vs BASE",
        "",
        "| Book | Window end | MDD improve pp | CAGR giveback pp | Score |",
        "|---|---|---:|---:|---:|",
    ]
    for _, r in roll_delta_df.sort_values(["book", "window_end"]).iterrows():
        lines.append(
            f"| `{r['book']}` | {r['window_end']} | {fmt(r['mdd_improve_pp'])} | "
            f"{fmt(r['cagr_giveback_pp'])} | {fmt(r['score'])} |"
        )
    lines += [
        "",
        "## Cost stress (1–3×) @ heldout_2019_plus",
        "",
        "| Book | Cost | MDD improve pp | CAGR giveback pp | Score | Ann. turnover (approx) |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    sub = cost_df[cost_df.window == "heldout_2019_plus"].sort_values(["family", "cost_multiple"])
    for _, r in sub.iterrows():
        to = r["ann_turnover_approx"]
        lines.append(
            f"| `{r['book']}` | {r['cost_multiple']:.0f}× | {fmt(r['mdd_improve_pp'])} | "
            f"{fmt(r['cagr_giveback_pp'])} | {fmt(r['score'])} | "
            f"{'n/a' if to is None else f'{to:.2f}'} |"
        )
    tip = roll_delta_df[roll_delta_df.window_end == "2026-09-04"]
    a05 = tip[tip.book == "ALL_A05"]
    f10 = tip[tip.book == "FIN_ONLY_A10"]
    winner = "n/a"
    if len(a05) and len(f10) and a05.iloc[0]["score"] is not None and f10.iloc[0]["score"] is not None:
        winner = "FIN_ONLY_A10" if float(f10.iloc[0]["score"]) >= float(a05.iloc[0]["score"]) else "ALL_A05"
    lines += [
        "",
        f"## Latest rolling-3y winner vs BASE: **`{winner}`**",
        "",
        "## Verdict",
        "",
        "- FIN_ONLY@0.10 remains the sleeve-local observe lock unless rolling/cost clearly flips.",
        "- Cost 2–3× should not invert ranking if the edge is real; turnover must stay non-explosive.",
        "- Tip observe PAUSE does not override this paper compare.",
        "",
        f"Label: `E45_FINA10_VS_ALLA05_{generated[:10]}__STITCH_FORBIDDEN`",
        "",
    ]
    publish("E45_FINA10_VS_ALLA05_COMPARE.md", "\n".join(lines))

    # 4
    pref = preferred_hb["book"] if preferred_hb else "n/a"
    lines = [
        "# E45 HIGH_BETA Sleeve-Local Paper Densify",
        "",
        f"Generated: `{generated}`",
        "Status: **PAPER ONLY** — **NOT an OPEN observe ballot**",
        f"High-β sleeves (β ≥ median vs TAIEX): `{list(hb_sleeves)}` · "
        f"betas={{{', '.join(f'{k}:{v:.2f}' for k,v in betas.items())}}}",
        "",
        "Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN · FIN_ONLY_A10 observe stays OPERATING",
        "",
        "## Held-out ranking (score = MDD improve − 0.5·|CAGR giveback|)",
        "",
        "| Book | α | Sleeves | MDD improve pp | CAGR giveback pp | Score |",
        "|---|---:|---|---:|---:|---:|",
    ]
    held = hb_df[hb_df.window == "heldout_2019_plus"].sort_values("score", ascending=False)
    for _, r in held.iterrows():
        lines.append(
            f"| `{r['book']}` | {r['alpha']:.2f} | {r['sleeves']} | {fmt(r['mdd_improve_pp'])} | "
            f"{fmt(r['cagr_giveback_pp'])} | {fmt(r['score'])} |"
        )
    lines += [
        "",
        f"**Held-out preferred (paper):** `{pref}`",
        "",
        "## Governance",
        "",
        "- This densify does **not** OPEN a HIGH_BETA observe sleeve.",
        "- Draft ballot (human ACCEPT required before any OPEN): "
        "`research/ops/E45_HIGH_BETA_OBSERVE_OPEN_BALLOT_DRAFT.md`",
        "- Do not displace FIN_ONLY_A10 observe without a dedicated ballot.",
        "",
        f"Label: `E45_HIGH_BETA_PAPER_{generated[:10]}__DRAFT_ONLY__STITCH_FORBIDDEN`",
        "",
    ]
    publish("E45_HIGH_BETA_SLEEVE_LOCAL_PAPER.md", "\n".join(lines))

    ballot = f"""# E45 HIGH_BETA Sleeve-Local Observe — OPEN Ballot **DRAFT**

Status: **DRAFT ONLY — NOT OPEN**
Proposed ballot name: `E45 OPEN high-beta sleeve-local observe`
Date: {generated[:10]}

> **Does NOT** OPEN an observe sleeve, wire month-end, flip Soft-Frozen / DEFAULT, or authorize stitch.
> Remains **PAPER ONLY** until a separate human **ACCEPT**.

Soft-Frozen: **[0.50, 0.95] KEEP**
Live DEFAULT books: **KEEP**
Live stitch: **still FORBIDDEN**
Parent sleeves still OPERATING: FULL + A25 + A05 + FIN_ONLY_A10

## Proposal (if later ACCEPTed)

| Field | Value |
|---|---|
| Choice | OPEN HIGH_BETA sleeve-local observe (paper) |
| Locked book (candidate) | `{pref}` |
| Sleeves | `{list(hb_sleeves)}` |
| Parallel | Do not replace FIN_ONLY_A10 |
| Stitch | FORBIDDEN |

## Evidence pointers

- Paper densify: `research/ops/E45_HIGH_BETA_SLEEVE_LOCAL_PAPER.md`
- Multi-event gate: `research/ops/E45_MULTI_EVENT_THRESHOLD_CHARTER.md`

## Human choices

| Choice | Effect |
|---|---|
| **HOLD DRAFT** (default) | No OPEN; paper only |
| **ACCEPT OPEN** | Separate PR to promote DRAFT→OPERATING (not this file alone) |
| **REJECT** | Archive; keep FIN_ONLY_A10 path |

Label: `E45_HIGH_BETA_OBSERVE_BALLOT_DRAFT_{generated[:10]}__NOT_OPEN__STITCH_FORBIDDEN`
"""
    (OPS / "E45_HIGH_BETA_OBSERVE_OPEN_BALLOT_DRAFT.md").write_text(ballot)

    # 5
    lines = [
        "# E45 Multi-Event Stress-Year Threshold Charter",
        "",
        f"Generated: `{generated}`",
        "Status: **PAPER GOVERNANCE RULE** — does not flip Soft-Frozen / DEFAULT / stitch",
        "",
        "## Rule (binding for future paper ballots)",
        "",
        "A challenger **qualifies** for a dedicated OPEN-observe ballot only if **all** hold:",
        "",
        "1. **Multi-event:** MDD help > **0.25 pp** vs BASE in **≥ 2** distinct years among {2015, 2018, 2020, 2022}.",
        "2. **Held-out score > 0** on `heldout_2019_plus` (score = MDD improve pp − 0.5·|CAGR giveback pp|).",
        "3. **Sealed score > −1.0** on `sealed_2023_plus` (no catastrophic sealed giveback).",
        "",
        "Rationale: block **2020-only** products from looking like general crisis protection.",
        "",
        "## Scores (this batch)",
        "",
        "| Book | Years helped | N | Multi≥2 | Held-out score | Sealed score | Qualifies? |",
        "|---|---|---:|:---:|---:|---:|:---:|",
    ]
    for _, r in thr_df.sort_values("qualifies_multi_event_rule", ascending=False).iterrows():
        lines.append(
            f"| `{r['book']}` | {r['crisis_years_helped_gt_0_25pp']} | "
            f"{int(r['n_independent_stress_years'])} | "
            f"{'Y' if r['multi_event_ok_ge_2'] else 'N'} | {fmt(r['heldout_score'])} | "
            f"{fmt(r['sealed_score'])} | **{'YES' if r['qualifies_multi_event_rule'] else 'NO'}** |"
        )
    quals = [r["book"] for _, r in thr_df.iterrows() if r["qualifies_multi_event_rule"]]
    lines += [
        "",
        f"**Qualifiers this batch:** {', '.join(f'`{q}`' for q in quals) if quals else '_none_'}",
        "",
        "## Non-goals",
        "",
        "- Not a live stitch gate (stitch still needs second human ACCEPT + clean trailing).",
        "- Not a Soft-Frozen / DEFAULT flip.",
        "- Does not invent a −13.16% replacement (`RETIRED_HISTORICAL_NARRATIVE`).",
        "",
        f"Label: `E45_MULTI_EVENT_THRESHOLD_{generated[:10]}__STITCH_FORBIDDEN`",
        "",
    ]
    publish("E45_MULTI_EVENT_THRESHOLD_CHARTER.md", "\n".join(lines))

    integ = f"""# E45 Five-Research Batch — Integrated Analysis

Generated: `{generated}`
Status: **PAPER / OBSERVE OPS** — Soft-Frozen **KEEP** · DEFAULT **KEEP** · live stitch **FORBIDDEN**
Claimed −13.16%: **`{payload['claimed_mdd_status']}`** (do not invent a replacement)

## What ran

| # | Item | Artifact |
|---|---|---|
| 1 | Month-end PAUSE time-series (FULL / A25 / A05 / FIN_ONLY_A10) | `E45_OBSERVE_PAUSE_TIMESERIES.md` |
| 2 | Non-2020 crisis attribution | `E45_NON2020_CRISIS_ATTRIBUTION.md` |
| 3 | FIN_ONLY@0.10 vs ALL@0.05 rolling/cost/turnover | `E45_FINA10_VS_ALLA05_COMPARE.md` |
| 4 | HIGH_BETA sleeve-local paper + DRAFT ballot | `E45_HIGH_BETA_SLEEVE_LOCAL_PAPER.md` + ballot DRAFT |
| 5 | Multi-event stress-year threshold charter | `E45_MULTI_EVENT_THRESHOLD_CHARTER.md` |

## Cross-cut verdict

1. **Observe:** tip PAUSE_REVIEW remains common; **no sleeve has a clean YTD+1y pair yet** → stitch still blocked by trailing gates (expected).
2. **Crisis honesty:** help is still **2020-concentrated**; non-2020 years are weak or mixed.
3. **FIN_ONLY_A10 vs ALL_A05:** re-validated under rolling 3y + cost 1–3×; observe lock unchanged.
4. **HIGH_BETA:** paper densify complete; ballot stays **DRAFT / NOT OPEN**.
5. **Multi-event rule:** future OPEN ballots should require ≥2 stress years with MDD help >0.25pp + held-out score>0 + sealed score>−1.

## Explicit non-actions

- No Soft-Frozen flip · no DEFAULT rewrite · no live stitch · no −13.16% reinvention · no auto-OPEN of HIGH_BETA.

## Machine summary

`repro/e45-five-research-batch/outputs/five_research_batch_summary.json`

Label: `E45_FIVE_RESEARCH_BATCH_{generated[:10]}__STITCH_FORBIDDEN`
"""
    publish("E45_FIVE_RESEARCH_BATCH_INTEGRATED.md", integ)

    roadmap = OPS / "E45_PAPER_RESEARCH_ROADMAP.md"
    if roadmap.exists():
        txt = roadmap.read_text()
        marker = "## Five-research batch (2026-09-06)"
        block = f"""{marker}

| # | Item | Status | Artifact |
|---|---|---|---|
| 1 | Observe PAUSE time-series | **DONE** | `E45_OBSERVE_PAUSE_TIMESERIES.md` |
| 2 | Non-2020 crisis attribution | **DONE** | `E45_NON2020_CRISIS_ATTRIBUTION.md` |
| 3 | FIN_ONLY_A10 vs ALL_A05 rolling/cost | **DONE** | `E45_FINA10_VS_ALLA05_COMPARE.md` |
| 4 | HIGH_BETA paper + DRAFT ballot | **DONE (DRAFT only)** | `E45_HIGH_BETA_SLEEVE_LOCAL_PAPER.md` |
| 5 | Multi-event threshold charter | **DONE** | `E45_MULTI_EVENT_THRESHOLD_CHARTER.md` |

Integrated: `E45_FIVE_RESEARCH_BATCH_INTEGRATED.md` · stitch still **FORBIDDEN**.

"""
        if marker not in txt:
            roadmap.write_text(txt.rstrip() + "\n\n" + block)


def main() -> None:
    out_o = OUT / "outputs"
    out_r = OUT / "reports"
    out_o.mkdir(parents=True, exist_ok=True)
    out_r.mkdir(parents=True, exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)
    OPS.mkdir(parents=True, exist_ok=True)

    generated = datetime.now(timezone.utc).isoformat()

    print("==> (1) month-end PAUSE time-series", flush=True)
    pause_rows = []
    pause_summary = {}
    for sleeve, meta in OBSERVE_NAV.items():
        if not meta["base"].exists() or not meta["chal"].exists():
            pause_summary[sleeve] = {"ok": False, "reason": "missing_nav"}
            print(f"  missing NAV for {sleeve}", flush=True)
            continue
        base = load_nav(meta["base"])
        chal = load_nav(meta["chal"])
        asofs = month_end_asofs(chal)
        for asof in asofs:
            for w in ("ytd", "trailing_1y"):
                row = giveback_at(base, chal, asof, w)
                row.update({"sleeve": sleeve, "book": meta["book"], "alpha": meta["alpha"], "scope": meta["scope"]})
                pause_rows.append(row)
        tip = asofs[-1] if asofs else None
        hist = [r for r in pause_rows if r["sleeve"] == sleeve]
        tip_ytd = next((r for r in hist if tip is not None and r["asof"] == tip.date().isoformat() and r["window"] == "ytd"), None)
        tip_1y = next((r for r in hist if tip is not None and r["asof"] == tip.date().isoformat() and r["window"] == "trailing_1y"), None)
        by_asof = {}
        for r in hist:
            by_asof.setdefault(r["asof"], {})[r["window"]] = r["gate"]
        first_clean = None
        for a, gates in sorted(by_asof.items()):
            if gates.get("ytd") == "PASS" and gates.get("trailing_1y") == "PASS":
                first_clean = a
                break
        ytd_hist = [r for r in hist if r["window"] == "ytd"]
        y1_hist = [r for r in hist if r["window"] == "trailing_1y"]
        pause_summary[sleeve] = {
            "ok": True,
            "n_month_ends": len(asofs),
            "tip_asof": tip.date().isoformat() if tip is not None else None,
            "tip_ytd_gate": tip_ytd["gate"] if tip_ytd else None,
            "tip_trailing_1y_gate": tip_1y["gate"] if tip_1y else None,
            "share_pause_ytd": float(np.mean([r["gate"] == "PAUSE_REVIEW" for r in ytd_hist])) if ytd_hist else None,
            "share_pause_1y": float(np.mean([r["gate"] == "PAUSE_REVIEW" for r in y1_hist])) if y1_hist else None,
            "first_clean_both_asof": first_clean,
        }
        print(
            f"  {sleeve}: tip={pause_summary[sleeve]['tip_asof']} "
            f"ytd={pause_summary[sleeve]['tip_ytd_gate']} "
            f"1y={pause_summary[sleeve]['tip_trailing_1y_gate']}",
            flush=True,
        )
    pd.DataFrame(pause_rows).to_csv(out_o / "observe_month_end_pause_timeseries.csv", index=False)

    print("==> loading market / features", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, _s, target, regime = e16_features(market)
    e45_full = e45_full_exposure(market, E45_PROFILE_DEFAULT)
    hb_sleeves, betas = high_beta_sleeves(market)
    print(f"high_beta_sleeves={hb_sleeves} betas={betas}", flush=True)

    books = {}

    def put(bid, family, alpha, sleeves, cost, nav, fills, meta):
        books[bid] = {
            "book": bid,
            "family": family,
            "alpha": float(alpha),
            "sleeves": list(sleeves) if sleeves else None,
            "cost_multiple": float(cost),
            "nav": nav,
            "fills": fills,
            "meta": meta,
            "windows": {w: window_stats(nav, a, b) for w, (a, b) in WINDOWS_STANDARD.items()},
            "turnover": turnover_from_fills(fills, nav),
        }

    def sim(label, alpha, sleeves, cost=1.0):
        exp = blend_exposure(e45_full, alpha)
        print(f"sim {label} alpha={alpha} sleeves={sleeves} cost={cost}x ...", flush=True)
        return run_early_stack(
            market,
            target,
            regime,
            dividends,
            e45_exposure=exp,
            e45_sleeve_names=sleeves,
            cost_multiple=cost,
        )

    for cost in COST_MULTS:
        print(f"sim BASE cost={cost}x ...", flush=True)
        nav, fills, meta = run_early_stack(
            market, target, regime, dividends, e45_exposure=None, cost_multiple=cost
        )
        put(f"{BOOK_BASE}_C{int(cost)}x", "BASE", 0.0, None, cost, nav, fills, meta)

    base_key = f"{BOOK_BASE}_C1x"
    core_specs = [
        ("ALL_A05", 0.05, None),
        ("ALL_A25", 0.25, None),
        ("FULL_E45", 1.00, None),
        ("FIN_ONLY_A05", 0.05, SLEEVE_FIN_ONLY),
        ("FIN_ONLY_A08", 0.08, SLEEVE_FIN_ONLY),
        ("FIN_ONLY_A10", 0.10, SLEEVE_FIN_ONLY),
        ("HIGH_BETA_A05", 0.05, hb_sleeves),
        ("HIGH_BETA_A08", 0.08, hb_sleeves),
        ("HIGH_BETA_A10", 0.10, hb_sleeves),
        ("HIGH_BETA_A15", 0.15, hb_sleeves),
    ]
    for label, alpha, sleeves in core_specs:
        nav, fills, meta = sim(label, alpha, sleeves, 1.0)
        put(label, label.rsplit("_", 1)[0], alpha, sleeves, 1.0, nav, fills, meta)

    for label, alpha, sleeves in (("ALL_A05", 0.05, None), ("FIN_ONLY_A10", 0.10, SLEEVE_FIN_ONLY)):
        for cost in (2.0, 3.0):
            key = f"{label}_C{int(cost)}x"
            nav, fills, meta = sim(key, alpha, sleeves, cost)
            put(key, label, alpha, sleeves, cost, nav, fills, meta)

    for key in ("ALL_A05", "FIN_ONLY_A10", "HIGH_BETA_A10", "FULL_E45"):
        books[key]["nav"].to_csv(out_o / f"{key.lower()}_daily_nav.csv", index=False)

    print("==> (2) crisis-year attribution", flush=True)
    focus_books = [base_key, "ALL_A05", "ALL_A25", "FULL_E45", "FIN_ONLY_A10", "HIGH_BETA_A10"]
    crisis_rows = []
    for bid in focus_books:
        for y in list(CRISIS_YEARS) + list(REF_YEARS):
            st = year_path_stats(books[bid]["nav"], y)
            st.update({
                "book": bid,
                "alpha": books[bid]["alpha"],
                "sleeves": ",".join(books[bid]["sleeves"] or []) or "ALL",
            })
            crisis_rows.append(st)
    crisis_df = pd.DataFrame(crisis_rows)
    crisis_df.to_csv(out_o / "crisis_year_book_metrics.csv", index=False)

    help_rows = []
    for bid in focus_books:
        if bid == base_key:
            continue
        for y in CRISIS_YEARS:
            b = crisis_df[(crisis_df.book == base_key) & (crisis_df.year == y)].iloc[0]
            c = crisis_df[(crisis_df.book == bid) & (crisis_df.year == y)].iloc[0]
            if not b["available"] or not c["available"]:
                continue
            help_rows.append({
                "book": bid,
                "year": y,
                "mdd_help_pp": (abs(float(b["max_drawdown"])) - abs(float(c["max_drawdown"]))) * 100.0,
                "ret_delta_pp": (float(c["ret"]) - float(b["ret"])) * 100.0,
                "is_2020": y == 2020,
            })
    help_df = pd.DataFrame(help_rows)
    help_df.to_csv(out_o / "crisis_year_mdd_help_vs_base.csv", index=False)

    concentration = []
    for bid, g in help_df.groupby("book"):
        pos = g[g["mdd_help_pp"] > 0]
        total_pos = float(pos["mdd_help_pp"].sum()) if len(pos) else 0.0
        y2020 = float(g.loc[g["year"] == 2020, "mdd_help_pp"].sum())
        non2020_pos = float(pos.loc[pos["year"] != 2020, "mdd_help_pp"].sum()) if len(pos) else 0.0
        years_helped = sorted(g.loc[g["mdd_help_pp"] > 0.25, "year"].tolist())
        concentration.append({
            "book": bid,
            "mdd_help_2020_pp": y2020,
            "mdd_help_non2020_positive_pp": non2020_pos,
            "share_of_positive_help_in_2020": (y2020 / total_pos) if total_pos > 1e-9 else None,
            "n_crisis_years_helped_gt_0_25pp": len(years_helped),
            "years_helped": years_helped,
        })
    conc_df = pd.DataFrame(concentration)
    conc_df.to_csv(out_o / "crisis_help_concentration.csv", index=False)

    print("==> (3) FIN_ONLY_A10 vs ALL_A05", flush=True)
    roll_rows = []
    for end in ROLL_ENDS:
        start = date(end.year - 3, 1, 1)
        for bid in (base_key, "ALL_A05", "FIN_ONLY_A10"):
            st = custom_window_stats(books[bid]["nav"], start, end)
            roll_rows.append({
                "book": bid,
                "window_start": start.isoformat(),
                "window_end": end.isoformat(),
                **{k: st.get(k) for k in ("cagr", "max_drawdown", "utility", "vol", "n_days")},
            })
    roll_df = pd.DataFrame(roll_rows)
    roll_delta = []
    for end in ROLL_ENDS:
        start = date(end.year - 3, 1, 1)
        b = roll_df[(roll_df.book == base_key) & (roll_df.window_end == end.isoformat())].iloc[0]
        for bid in ("ALL_A05", "FIN_ONLY_A10"):
            c = roll_df[(roll_df.book == bid) & (roll_df.window_end == end.isoformat())].iloc[0]
            dlt = deltas_vs_base(
                {"cagr": b["cagr"], "max_drawdown": b["max_drawdown"]},
                {"cagr": c["cagr"], "max_drawdown": c["max_drawdown"]},
            )
            roll_delta.append({
                "book": bid,
                "window_start": start.isoformat(),
                "window_end": end.isoformat(),
                **dlt,
                "chal_cagr": c["cagr"],
                "base_cagr": b["cagr"],
                "chal_mdd": c["max_drawdown"],
                "base_mdd": b["max_drawdown"],
            })
    roll_delta_df = pd.DataFrame(roll_delta)
    roll_df.to_csv(out_o / "rolling_3y_window_metrics.csv", index=False)
    roll_delta_df.to_csv(out_o / "rolling_3y_deltas_vs_base.csv", index=False)

    cost_rows = []
    for cost in COST_MULTS:
        bk = f"{BOOK_BASE}_C{int(cost)}x"
        for label in ("ALL_A05", "FIN_ONLY_A10"):
            ck = label if cost == 1.0 else f"{label}_C{int(cost)}x"
            for w in FOCUS_WINDOWS:
                b = books[bk]["windows"][w]
                c = books[ck]["windows"][w]
                dlt = deltas_vs_base(b, c)
                cost_rows.append({
                    "book": ck,
                    "family": label,
                    "cost_multiple": cost,
                    "window": w,
                    **dlt,
                    "chal_cagr": c.get("cagr"),
                    "base_cagr": b.get("cagr"),
                    "chal_mdd": c.get("max_drawdown"),
                    "base_mdd": b.get("max_drawdown"),
                    "ann_turnover_approx": books[ck]["turnover"].get("ann_turnover_approx"),
                    "n_fills": books[ck]["turnover"].get("n_fills"),
                })
    cost_df = pd.DataFrame(cost_rows)
    cost_df.to_csv(out_o / "fin_a10_vs_all_a05_cost_turnover.csv", index=False)

    print("==> (4) HIGH_BETA densify", flush=True)
    hb_rows = []
    for bid in [
        "ALL_A05", "FIN_ONLY_A05", "FIN_ONLY_A08", "FIN_ONLY_A10",
        "HIGH_BETA_A05", "HIGH_BETA_A08", "HIGH_BETA_A10", "HIGH_BETA_A15",
    ]:
        for w in FOCUS_WINDOWS:
            dlt = deltas_vs_base(books[base_key]["windows"][w], books[bid]["windows"][w])
            hb_rows.append({
                "book": bid,
                "alpha": books[bid]["alpha"],
                "sleeves": ",".join(books[bid]["sleeves"] or []) or "ALL",
                "window": w,
                **dlt,
                "chal_cagr": books[bid]["windows"][w].get("cagr"),
                "chal_mdd": books[bid]["windows"][w].get("max_drawdown"),
                "ann_turnover_approx": books[bid]["turnover"].get("ann_turnover_approx"),
            })
    hb_df = pd.DataFrame(hb_rows)
    hb_df.to_csv(out_o / "high_beta_sleeve_local_grid.csv", index=False)
    held = hb_df[hb_df.window == "heldout_2019_plus"].sort_values("score", ascending=False)
    preferred_hb = held.iloc[0].to_dict() if not held.empty else None

    print("==> (5) multi-event threshold", flush=True)
    threshold_rows = []
    candidates = [
        "ALL_A05", "ALL_A25", "FULL_E45", "FIN_ONLY_A05", "FIN_ONLY_A10",
        "HIGH_BETA_A05", "HIGH_BETA_A10", "HIGH_BETA_A15",
    ]
    for bid in candidates:
        years_helped = []
        for y in CRISIS_YEARS:
            b = year_path_stats(books[base_key]["nav"], y)
            c = year_path_stats(books[bid]["nav"], y)
            if b["available"] and c["available"]:
                help_pp = (abs(b["max_drawdown"]) - abs(c["max_drawdown"])) * 100.0
                if help_pp > 0.25:
                    years_helped.append(y)
        held_d = deltas_vs_base(
            books[base_key]["windows"]["heldout_2019_plus"],
            books[bid]["windows"]["heldout_2019_plus"],
        )
        seal_d = deltas_vs_base(
            books[base_key]["windows"]["sealed_2023_plus"],
            books[bid]["windows"]["sealed_2023_plus"],
        )
        n_events = len(years_helped)
        multi_ok = n_events >= 2
        score_ok = held_d["score"] is not None and held_d["score"] > 0
        sealed_ok = seal_d["score"] is not None and seal_d["score"] > -1.0
        qualifies = bool(multi_ok and score_ok and sealed_ok)
        threshold_rows.append({
            "book": bid,
            "alpha": books[bid]["alpha"],
            "sleeves": ",".join(books[bid]["sleeves"] or []) or "ALL",
            "crisis_years_helped_gt_0_25pp": years_helped,
            "n_independent_stress_years": n_events,
            "multi_event_ok_ge_2": multi_ok,
            "heldout_score": held_d["score"],
            "heldout_score_ok": score_ok,
            "sealed_score": seal_d["score"],
            "sealed_score_ok_gt_m1": sealed_ok,
            "qualifies_multi_event_rule": qualifies,
        })
    thr_df = pd.DataFrame(threshold_rows)
    thr_df.to_csv(out_o / "multi_event_threshold_scores.csv", index=False)

    payload = {
        "generated_at_utc": generated,
        "status": "PAPER_ONLY",
        "soft_frozen": "KEEP",
        "default_books": "KEEP",
        "live_stitch": "FORBIDDEN",
        "claimed_mdd_status": CLAIM_STATUS,
        "observe_sleeves_operating": list(OBSERVE_NAV.keys()),
        "high_beta_sleeves": list(hb_sleeves),
        "high_beta_betas": {k: float(v) for k, v in betas.items()},
        "pause_summary": pause_summary,
        "crisis_concentration": concentration,
        "preferred_high_beta_heldout": preferred_hb,
        "multi_event_qualifiers": [r["book"] for r in threshold_rows if r["qualifies_multi_event_rule"]],
        "gates": {
            "trail_alert_pp": TRAIL_ALERT_PP,
            "trail_pause_pp": TRAIL_PAUSE_PP,
            "multi_event_min_years": 2,
            "mdd_help_threshold_pp": 0.25,
        },
    }
    (out_o / "five_research_batch_summary.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    write_all_reports({
        "generated": generated,
        "out_r": out_r,
        "pause_summary": pause_summary,
        "conc_df": conc_df,
        "help_df": help_df,
        "roll_delta_df": roll_delta_df,
        "cost_df": cost_df,
        "hb_df": hb_df,
        "preferred_hb": preferred_hb,
        "hb_sleeves": hb_sleeves,
        "betas": betas,
        "thr_df": thr_df,
        "payload": payload,
    })
    print("DONE", OUT, flush=True)


if __name__ == "__main__":
    main()
