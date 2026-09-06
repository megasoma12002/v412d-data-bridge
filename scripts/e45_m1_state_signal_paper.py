#!/usr/bin/env python3
"""E45 M1 PAPER — new state-signal family (sensor) on Exact T+1 early-stack.

Frozen v0 vector: research/e45/E45_M1_STATE_VECTOR_V0_FROZEN.md
Primary engine is NOT E45 crisis core. BLEND_E45_A05 / SLEEVE_FIN_ONLY_A10 are refs.

Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN · HIGH_BETA DRAFT/NOT OPEN.
Does NOT invent a replacement for retired claimed-MDD narrative.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from e50_early_stack_combined_nav import ALL, FIN
from e45_paper_harness import (
    BOOK_BASE,
    BOOK_BLEND_A05,
    CLAIM_STATUS,
    DIV_PATH,
    E45_PROFILE_DEFAULT,
    MARKET_PATH,
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

OUT = ROOT / "repro/e45-m1-state-signal"
RESEARCH = ROOT / "research/e45"
OPS = ROOT / "research/ops"
SHOCK_PATH = ROOT / "forward/e10s2/e10s2_taiex.csv"

STATE_VECTOR_LABEL = "E45_M1_STATE_VECTOR_V0_FROZEN_2026-09-06"
COST_MULTS = (0, 1, 2, 3)
FEE_KEYS = ("BUY_FEE", "SELL_FEE", "SLIP", "TAX_STOCK", "TAX_ETF")
FOCUS = ("heldout_2019_plus", "sealed_2023_plus", "full")
WINDOWS = {k: WINDOWS_STANDARD[k] for k in FOCUS}
STRESS_YEARS = (2015, 2018, 2020, 2022)
HELP_PP = 0.25


def pp(x) -> str:
    if x is None or (isinstance(x, float) and (np.isnan(x) or np.isinf(x))):
        return "n/a"
    return f"{x:+.2f}"


def yn(flag: bool) -> str:
    return "Y" if flag else "N"


def turnover_metrics(nav: pd.DataFrame, fills: pd.DataFrame) -> dict:
    n = nav.copy()
    n["date"] = pd.to_datetime(n["date"])
    years = max((n["date"].iloc[-1] - n["date"].iloc[0]).days / 365.25, 1e-9)
    mean_nav = float(n["nav"].mean()) if len(n) else None
    if fills is None or len(fills) == 0:
        return {
            "n_fills": 0,
            "fees_tax_sum": 0.0,
            "gross_traded": 0.0,
            "turnover_per_year": 0.0,
            "years": float(years),
            "mean_nav": mean_nav,
        }
    f = fills.copy()
    fee_col = next((c for c in ("fees_tax", "fee_tax", "fees") if c in f.columns), None)
    gross_col = "gross" if "gross" in f.columns else None
    fees = float(pd.to_numeric(f[fee_col], errors="coerce").fillna(0).sum()) if fee_col else 0.0
    gross = (
        float(pd.to_numeric(f[gross_col], errors="coerce").fillna(0).abs().sum())
        if gross_col
        else 0.0
    )
    to = (gross / mean_nav / years) if mean_nav and mean_nav > 0 else None
    return {
        "n_fills": int(len(f)),
        "fees_tax_sum": fees,
        "gross_traded": gross,
        "turnover_per_year": to,
        "years": float(years),
        "mean_nav": mean_nav,
    }


def _rolling_percentile(x: pd.Series, window: int = 252) -> pd.Series:
    def _pct(arr: np.ndarray) -> float:
        if len(arr) < 20 or np.all(np.isnan(arr)):
            return np.nan
        v = arr[-1]
        if np.isnan(v):
            return np.nan
        hist = arr[~np.isnan(arr)]
        if len(hist) < 20:
            return np.nan
        return float((hist <= v).mean())

    return x.rolling(window, min_periods=60).apply(_pct, raw=True)


def build_m1_state(market: pd.DataFrame) -> pd.DataFrame:
    """Frozen v0 features + intensity s_t (pre-lag)."""
    wide = (
        market.pivot(index="date", columns="code", values="close")
        .sort_index()
        .ffill()
    )
    if "TAIEX" not in wide.columns:
        raise RuntimeError("TAIEX missing from live_market — cannot build M1 state")
    taiex = wide["TAIEX"].astype(float)
    logret = np.log(taiex).diff()
    peak_252 = taiex.rolling(252, min_periods=60).max()
    dd = 1.0 - taiex / peak_252
    r_dd = (dd / 0.20).clip(0.0, 1.0)

    vol20 = logret.rolling(20, min_periods=10).std()
    r_vol = _rolling_percentile(vol20, 252).fillna(0.0).clip(0.0, 1.0)

    eq = wide[[c for c in ALL if c in wide.columns]].astype(float)
    sma120 = eq.rolling(120, min_periods=60).mean()
    breadth = (eq > sma120).sum(axis=1) / eq.notna().sum(axis=1).replace(0, np.nan)
    r_breadth = (1.0 - breadth).clip(0.0, 1.0)

    fin_cols = [c for c in FIN if c in wide.columns]
    fin = eq[fin_cols].mean(axis=1)
    rel = np.log((fin / taiex).replace(0, np.nan))
    z = (rel - rel.rolling(60, min_periods=30).mean()) / rel.rolling(60, min_periods=30).std()
    r_finrel = (np.maximum(0.0, -z) / 2.0).clip(0.0, 1.0)

    shock = pd.Series(0.0, index=wide.index)
    if SHOCK_PATH.exists():
        sh = pd.read_csv(SHOCK_PATH)
        sh["date"] = pd.to_datetime(sh["date"])
        sh = sh.set_index("date").sort_index()
        if "shock_combined" in sh.columns:
            shock = (
                sh["shock_combined"].astype(bool).astype(float).reindex(wide.index).fillna(0.0)
            )

    feats = pd.DataFrame(
        {
            "R_DD": r_dd,
            "R_VOL": r_vol,
            "R_BREADTH": r_breadth,
            "R_FINREL": r_finrel,
            "R_SHOCK": shock,
        },
        index=wide.index,
    )
    feats["s_t"] = feats.mean(axis=1, skipna=True).clip(0.0, 1.0)
    return feats


def exposure_from_state(state: pd.DataFrame, cut: float) -> pd.Series:
    """exposure_t = 1 - c * s_{t-1}."""
    s_lag = state["s_t"].shift(1).fillna(0.0)
    return (1.0 - float(cut) * s_lag).clip(0.0, 1.0)


def year_mdd(nav: pd.DataFrame, year: int) -> float | None:
    d = nav.copy()
    d["date"] = pd.to_datetime(d["date"])
    part = d[(d["date"] >= f"{year}-01-01") & (d["date"] <= f"{year}-12-31")].reset_index(
        drop=True
    )
    if len(part) < 30:
        return None
    part = part.copy()
    part["nav"] = part["nav"] / float(part["nav"].iloc[0])
    st = window_stats(part, None, None, min_days=30)
    return st.get("max_drawdown")


def year_mdd_help_pp(base_nav: pd.DataFrame, book_nav: pd.DataFrame, year: int) -> float | None:
    b = year_mdd(base_nav, year)
    c = year_mdd(book_nav, year)
    if b is None or c is None:
        return None
    return (abs(float(b)) - abs(float(c))) * 100.0


def covid_ex_stats(nav: pd.DataFrame) -> dict:
    d = nav.copy()
    d["date"] = pd.to_datetime(d["date"])
    d = d[
        (d["date"] >= "2019-01-01")
        & ~((d["date"] >= "2020-01-01") & (d["date"] <= "2020-12-31"))
    ]
    d = d.reset_index(drop=True)
    if len(d) < 30:
        return {"cagr": None, "max_drawdown": None, "n_days": int(len(d))}
    d = d.copy()
    d["nav"] = d["nav"] / float(d["nav"].iloc[0])
    return window_stats(d, None, None, min_days=30)


def qualify_row(
    years_helped: list[int],
    held_score,
    sealed_score,
    covid_ex_score,
    cost_ok: bool,
) -> dict:
    multi = len(years_helped) >= 2
    strict = len([y for y in years_helped if y in (2015, 2018, 2022)]) >= 2
    held_ok = held_score is not None and held_score > 0
    sealed_ok = sealed_score is not None and sealed_score > -1.0
    covid_ok = covid_ex_score is not None and covid_ex_score > 0
    qualifies = bool(multi and held_ok and sealed_ok and strict and covid_ok and cost_ok)
    return {
        "multi_event": multi,
        "strict_noncovid_multi": strict,
        "heldout_score_pos": held_ok,
        "sealed_score_ok": sealed_ok,
        "covid_ex_heldout_pos": covid_ok,
        "cost_1x_2x_ok": cost_ok,
        "qualifies_section2": qualifies,
        "years_helped": years_helped,
        "n_years_helped": len(years_helped),
    }


def main() -> None:
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)
    OPS.mkdir(parents=True, exist_ok=True)

    print("loading market ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, _s, target, regime = e16_features(market)

    print(f"building frozen state {STATE_VECTOR_LABEL} ...", flush=True)
    state = build_m1_state(market)
    state.to_csv(OUT / "outputs" / "m1_state_features.csv")
    state.describe().to_csv(OUT / "outputs" / "m1_state_feature_summary.csv")

    e45_full = e45_full_exposure(market)
    books: list[dict] = [
        {"book": BOOK_BASE, "kind": "ref", "exposure": None, "sleeves": None, "cut": 0.0},
        {
            "book": BOOK_BLEND_A05,
            "kind": "ref_e45",
            "exposure": blend_exposure(e45_full, 0.05),
            "sleeves": None,
            "cut": None,
        },
        {
            "book": "SLEEVE_FIN_ONLY_A10",
            "kind": "ref_e45_sleeve",
            "exposure": blend_exposure(e45_full, 0.10),
            "sleeves": SLEEVE_FIN_ONLY,
            "cut": None,
        },
        {
            "book": "M1_EQW_C25",
            "kind": "m1",
            "exposure": exposure_from_state(state, 0.25),
            "sleeves": None,
            "cut": 0.25,
        },
        {
            "book": "M1_EQW_C50",
            "kind": "m1",
            "exposure": exposure_from_state(state, 0.50),
            "sleeves": None,
            "cut": 0.50,
        },
        {
            "book": "M1_EQW_C75",
            "kind": "m1",
            "exposure": exposure_from_state(state, 0.75),
            "sleeves": None,
            "cut": 0.75,
        },
        {
            "book": "M1_EQW_C50_FIN",
            "kind": "m1_sleeve",
            "exposure": exposure_from_state(state, 0.50),
            "sleeves": SLEEVE_FIN_ONLY,
            "cut": 0.50,
        },
    ]

    for b in books:
        if b["exposure"] is not None:
            b["exposure"].rename("exposure").to_csv(
                OUT / "outputs" / f"{b['book'].lower()}_exposure.csv", header=True
            )

    rows = []
    navs: dict[tuple[str, int], pd.DataFrame] = {}
    for spec in books:
        for mult in COST_MULTS:
            print(f"sim {spec['book']} costx{mult} ...", flush=True)
            nav, fills, meta = run_early_stack(
                market,
                target,
                regime,
                dividends,
                e45_exposure=spec["exposure"],
                e45_sleeve_names=spec["sleeves"],
                cost_multiple=float(mult),
            )
            tag = f"{spec['book'].lower()}_x{mult}"
            nav.to_csv(OUT / "outputs" / f"{tag}_daily_nav.csv", index=False)
            fills.to_csv(OUT / "outputs" / f"{tag}_fills.csv", index=False)
            navs[(spec["book"], int(mult))] = nav
            to = turnover_metrics(nav, fills)
            for w, (a, b_) in WINDOWS.items():
                st = window_stats(nav, a, b_)
                rows.append(
                    {
                        "book": spec["book"],
                        "kind": spec["kind"],
                        "cut": spec["cut"],
                        "sleeves": ",".join(spec["sleeves"]) if spec["sleeves"] else "",
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
                    }
                )
    metrics = pd.DataFrame(rows)
    metrics.to_csv(OUT / "outputs" / "m1_metrics.csv", index=False)

    deltas = []
    for mult in COST_MULTS:
        base_nav = navs[(BOOK_BASE, int(mult))]
        for spec in books:
            book = spec["book"]
            book_nav = navs[(book, int(mult))]
            year_helps = {y: year_mdd_help_pp(base_nav, book_nav, y) for y in STRESS_YEARS}
            years_helped = [y for y, h in year_helps.items() if h is not None and h > HELP_PP]
            cex_d = deltas_vs_base(covid_ex_stats(base_nav), covid_ex_stats(book_nav))
            for w in FOCUS:
                bstat = metrics[
                    (metrics.book == BOOK_BASE)
                    & (metrics.cost_multiple == mult)
                    & (metrics.window == w)
                ].iloc[0]
                cstat = metrics[
                    (metrics.book == book)
                    & (metrics.cost_multiple == mult)
                    & (metrics.window == w)
                ].iloc[0]
                dlt = deltas_vs_base(
                    {"cagr": bstat["cagr"], "max_drawdown": bstat["max_drawdown"]},
                    {"cagr": cstat["cagr"], "max_drawdown": cstat["max_drawdown"]},
                )
                deltas.append(
                    {
                        "book": book,
                        "kind": spec["kind"],
                        "cut": spec["cut"],
                        "sleeves": ",".join(spec["sleeves"]) if spec["sleeves"] else "",
                        "cost_multiple": int(mult),
                        "window": w,
                        "mdd_improve_pp": dlt["mdd_improve_pp"],
                        "cagr_giveback_pp": dlt["cagr_giveback_pp"],
                        "score": dlt["score"],
                        "covid_ex_mdd_improve_pp": cex_d["mdd_improve_pp"],
                        "covid_ex_cagr_giveback_pp": cex_d["cagr_giveback_pp"],
                        "covid_ex_score": cex_d["score"],
                        "help_2015_pp": year_helps[2015],
                        "help_2018_pp": year_helps[2018],
                        "help_2020_pp": year_helps[2020],
                        "help_2022_pp": year_helps[2022],
                        "years_helped": ",".join(str(y) for y in years_helped),
                        "n_years_helped": len(years_helped),
                        "turnover_per_year": cstat["turnover_per_year"],
                        "fees_tax_sum": cstat["fees_tax_sum"],
                    }
                )
    delta_df = pd.DataFrame(deltas)
    delta_df.to_csv(OUT / "outputs" / "m1_deltas.csv", index=False)

    qual_rows = []
    for spec in books:
        book = spec["book"]
        d1 = delta_df[
            (delta_df.book == book)
            & (delta_df.cost_multiple == 1)
            & (delta_df.window == "heldout_2019_plus")
        ].iloc[0]
        d1s = delta_df[
            (delta_df.book == book)
            & (delta_df.cost_multiple == 1)
            & (delta_df.window == "sealed_2023_plus")
        ].iloc[0]
        d2 = delta_df[
            (delta_df.book == book)
            & (delta_df.cost_multiple == 2)
            & (delta_df.window == "heldout_2019_plus")
        ].iloc[0]
        years = [int(y) for y in str(d1["years_helped"]).split(",") if y]
        cost_ok = (
            d1["score"] is not None
            and d1["score"] >= 0
            and d1["mdd_improve_pp"] is not None
            and d1["mdd_improve_pp"] > 0
            and d2["score"] is not None
            and d2["score"] >= 0
            and d2["mdd_improve_pp"] is not None
            and d2["mdd_improve_pp"] > 0
        )
        q = qualify_row(years, d1["score"], d1s["score"], d1["covid_ex_score"], cost_ok)
        qual_rows.append(
            {
                "book": book,
                "kind": spec["kind"],
                "heldout_1x_score": d1["score"],
                "sealed_1x_score": d1s["score"],
                "covid_ex_heldout_1x_score": d1["covid_ex_score"],
                "heldout_2x_score": d2["score"],
                **q,
            }
        )
    qual_df = pd.DataFrame(qual_rows)
    qual_df.to_csv(OUT / "outputs" / "m1_section2_qualification.csv", index=False)

    m1_qualifiers = qual_df[
        (qual_df.kind.str.startswith("m1")) & (qual_df.qualifies_section2)
    ]["book"].tolist()
    any_m1_pass = len(m1_qualifiers) > 0

    held1 = delta_df[
        (delta_df.window == "heldout_2019_plus") & (delta_df.cost_multiple == 1)
    ].sort_values("score", ascending=False)
    best_m1 = held1[held1.kind.str.startswith("m1")]
    preferred_m1 = None if best_m1.empty else best_m1.iloc[0].to_dict()

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PAPER_ONLY",
        "ballot": "E45 M1 new state-signal paper screen",
        "state_vector": STATE_VECTOR_LABEL,
        "honesty": "equity_taiex_proxy_sensor__no_rates_fx_credit_in_repo",
        "profile_ref_e45_only": E45_PROFILE_DEFAULT,
        "claim_status": CLAIM_STATUS,
        "market_path": str(MARKET_PATH.relative_to(ROOT)),
        "div_path": str(DIV_PATH.relative_to(ROOT)),
        "shock_path": str(SHOCK_PATH.relative_to(ROOT)) if SHOCK_PATH.exists() else None,
        "books": [b["book"] for b in books],
        "cost_multiples": list(COST_MULTS),
        "fee_keys_scaled": list(FEE_KEYS),
        "score_formula": "mdd_improve_pp - 0.5 * abs(cagr_giveback_pp)",
        "help_threshold_pp": HELP_PP,
        "stress_years": list(STRESS_YEARS),
        "heldout_1x_ranking": held1[
            [
                "book",
                "kind",
                "score",
                "mdd_improve_pp",
                "cagr_giveback_pp",
                "covid_ex_score",
                "years_helped",
            ]
        ].to_dict(orient="records"),
        "preferred_m1_heldout_1x": preferred_m1,
        "section2_qualification": qual_rows,
        "m1_section2_qualifiers": m1_qualifiers,
        "m1_section2_any_pass": any_m1_pass,
        "soft_frozen": "KEEP",
        "live_default": "KEEP",
        "live_stitch": "FORBIDDEN",
        "high_beta_observe": "DRAFT_NOT_OPEN",
        "observe_sleeves_unchanged": True,
        "next_if_fail": (
            "Publish autopsy; do not densify E45 alpha; M2 DEF sleeve still allowed per charter"
        ),
        "non_actions": [
            "No Soft-Frozen / DEFAULT / stitch / HIGH_BETA ballot",
            "No invented replacement for retired claimed-MDD narrative",
            "No E45 same-knob densify as substitute for M1",
        ],
    }
    (OUT / "reports" / "e45_m1_state_signal.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )
    (RESEARCH / "E45_M1_STATE_SIGNAL.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    lines = [
        "# E45 M1 PAPER — New State-Signal Family (Sensor)",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Status: **PAPER ONLY** — Soft-Frozen **KEEP**; DEFAULT **KEEP**; stitch **FORBIDDEN**; "
        "HIGH_BETA **DRAFT / NOT OPEN**.",
        "",
        f"State vector: **`{STATE_VECTOR_LABEL}`** (frozen before metrics).",
        f"Honesty: `{payload['honesty']}` — not a true macro sensor.",
        "",
        "## Setup",
        "",
        f"- Books: `{', '.join(b['book'] for b in books)}`",
        f"- Cost multiples: {', '.join(str(m) + 'x' for m in COST_MULTS)} on `{', '.join(FEE_KEYS)}`",
        "- Score: `mdd_improve_pp - 0.5*|cagr_giveback_pp|` vs BASE at same cost x",
        f"- Year help threshold: MDD improve > **{HELP_PP} pp** in {{2015,2018,2020,2022}}",
        "- Exposure lag: 1 trading day (`s_{t-1}`)",
        "",
        "## Held-out deltas @1x (incl. COVID-ex score)",
        "",
        "| Book | Kind | MDD dpp | Giveback | Score | COVID-ex score | Years helped |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for _, r in held1.iterrows():
        lines.append(
            f"| {r['book']} | {r['kind']} | {pp(r['mdd_improve_pp'])} | {pp(r['cagr_giveback_pp'])} | "
            f"{pp(r['score'])} | {pp(r['covid_ex_score'])} | {r['years_helped'] or '—'} |"
        )

    lines += [
        "",
        "## Sealed deltas @1x",
        "",
        "| Book | Kind | MDD dpp | Giveback | Score |",
        "|---|---|---:|---:|---:|",
    ]
    sealed1 = delta_df[
        (delta_df.window == "sealed_2023_plus") & (delta_df.cost_multiple == 1)
    ].sort_values("score", ascending=False)
    for _, r in sealed1.iterrows():
        lines.append(
            f"| {r['book']} | {r['kind']} | {pp(r['mdd_improve_pp'])} | "
            f"{pp(r['cagr_giveback_pp'])} | {pp(r['score'])} |"
        )

    lines += [
        "",
        "## Cost stress — held-out scores by x",
        "",
        "| Book | 0x | 1x | 2x | 3x |",
        "|---|---:|---:|---:|---:|",
    ]
    for spec in books:
        scores = []
        for mult in COST_MULTS:
            r = delta_df[
                (delta_df.book == spec["book"])
                & (delta_df.cost_multiple == mult)
                & (delta_df.window == "heldout_2019_plus")
            ].iloc[0]
            scores.append(pp(r["score"]))
        lines.append(f"| {spec['book']} | " + " | ".join(scores) + " |")

    lines += [
        "",
        "## Section-2 qualification (binding)",
        "",
        "| Book | Multi>=2 | Strict non-COVID>=2 | Held>0 | Sealed>-1 | COVID-ex>0 | Cost1-2x | PASS |",
        "|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]
    for _, r in qual_df.iterrows():
        lines.append(
            f"| {r['book']} | {yn(r['multi_event'])} | {yn(r['strict_noncovid_multi'])} | "
            f"{yn(r['heldout_score_pos'])} | {yn(r['sealed_score_ok'])} | "
            f"{yn(r['covid_ex_heldout_pos'])} | {yn(r['cost_1x_2x_ok'])} | "
            f"{'YES' if r['qualifies_section2'] else 'NO'} |"
        )

    pref = preferred_m1 or {}
    lines += [
        "",
        "## Read-through (paper)",
        "",
        f"1. Best M1 on held-out @1x: **`{pref.get('book', 'n/a')}`** "
        f"(score {pp(pref.get('score'))}; COVID-ex {pp(pref.get('covid_ex_score'))}; "
        f"years `{pref.get('years_helped') or '—'}`).",
        f"2. Any M1 clears full Section-2 (incl. strict non-COVID + COVID-ex>0 + cost 1-2x)? "
        f"**{'YES -> ' + ', '.join(m1_qualifiers) if any_m1_pass else 'NO'}**.",
        "3. If NO: this is an **autopsy**, not a license to densify E45 alpha. Charter allows M2 "
        "(DEF sleeve relocate) even after M1 fail.",
        "4. Does **not** open Soft-Frozen / DEFAULT / stitch / HIGH_BETA ballots.",
        "",
        "## Governance",
        "",
        "- Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN · HIGH_BETA DRAFT/NOT OPEN",
        f"- Claimed MDD status: `{CLAIM_STATUS}` — no invented replacement",
        "- Freeze doc: `research/e45/E45_M1_STATE_VECTOR_V0_FROZEN.md`",
        "",
        "## Reproduce",
        "",
        "```bash",
        "python3 scripts/e45_m1_state_signal_paper.py",
        "```",
        "",
        f"Repro: `repro/e45-m1-state-signal/` · Market: `{MARKET_PATH.relative_to(ROOT)}`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "reports" / "e45_m1_state_signal.md").write_text(md + "\n")
    (RESEARCH / "E45_M1_STATE_SIGNAL.md").write_text(md + "\n")
    (OPS / "E45_M1_STATE_SIGNAL.md").write_text(
        "\n".join(
            [
                "# E45 M1 New State-Signal — Ops pointer",
                "",
                "Ballot: `E45 M1 new state-signal paper screen` — **PAPER ONLY**",
                "",
                "Freeze: `research/e45/E45_M1_STATE_VECTOR_V0_FROZEN.md`",
                "Primary: `research/e45/E45_M1_STATE_SIGNAL.md`",
                "Repro: `repro/e45-m1-state-signal/`",
                "",
                "```bash",
                "python3 scripts/e45_m1_state_signal_paper.py",
                "```",
                "",
                "Governance: Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN · "
                "HIGH_BETA DRAFT/NOT OPEN · no E45 same-knob densify substitute",
                "",
            ]
        )
    )

    print("done", flush=True)
    print(
        f"preferred_m1={pref.get('book')} score={pref.get('score')} "
        f"covid_ex={pref.get('covid_ex_score')} section2_pass={any_m1_pass}",
        flush=True,
    )


if __name__ == "__main__":
    main()
