#!/usr/bin/env python3
"""E45 M2 PAPER — cash/DEF sleeve relocate actuator on Exact T+1 early-stack.

Frozen v0: research/e45/E45_M2_DEF_SLEEVE_V0_FROZEN.md
Sensor: M1 frozen intensity s_{t-1} (M1 Section-2 FAIL does not block M2).
Ablations: SHRINK vs RELOC_TEL vs HYBRID_TEL at c in {0.50, 0.75}.

Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN · HIGH_BETA DRAFT/NOT OPEN.
Does NOT invent a replacement for retired claimed-MDD narrative.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from e45_crisis_core import build_m2_sleeve_schedule
from e45_m1_state_signal_paper import (
    HELP_PP,
    STRESS_YEARS,
    build_m1_state,
    covid_ex_stats,
    pp,
    qualify_row,
    turnover_metrics,
    year_mdd_help_pp,
    yn,
)
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

OUT = ROOT / "repro/e45-m2-def-sleeve-relocate"
RESEARCH = ROOT / "research/e45"
OPS = ROOT / "research/ops"

DEF_SLEEVE_LABEL = "E45_M2_DEF_SLEEVE_V0_FROZEN_2026-09-06"
COST_MULTS = (0, 1, 2, 3)
FEE_KEYS = ("BUY_FEE", "SELL_FEE", "SLIP", "TAX_STOCK", "TAX_ETF")
FOCUS = ("heldout_2019_plus", "sealed_2023_plus", "full")
WINDOWS = {k: WINDOWS_STANDARD[k] for k in FOCUS}


def main() -> None:
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)
    OPS.mkdir(parents=True, exist_ok=True)

    print("loading market ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, _s, target, regime = e16_features(market)

    print("building M1 intensity (frozen sensor, lag-1 actuator) ...", flush=True)
    state = build_m1_state(market)
    intensity_lag1 = state["s_t"].shift(1).fillna(0.0)
    state.to_csv(OUT / "outputs" / "m2_sensor_state_features.csv")
    intensity_lag1.rename("s_lag1").to_csv(OUT / "outputs" / "m2_intensity_lag1.csv", header=True)

    e45_full = e45_full_exposure(market)
    m2_specs = [
        ("M2_SHRINK_C50", "SHRINK", 0.50, "m2_shrink"),
        ("M2_SHRINK_C75", "SHRINK", 0.75, "m2_shrink"),
        ("M2_RELOC_TEL_C50", "RELOC_TEL", 0.50, "m2_reloc"),
        ("M2_RELOC_TEL_C75", "RELOC_TEL", 0.75, "m2_reloc"),
        ("M2_HYBRID_TEL_C50", "HYBRID_TEL", 0.50, "m2_hybrid"),
        ("M2_HYBRID_TEL_C75", "HYBRID_TEL", 0.75, "m2_hybrid"),
    ]
    books: list[dict] = [
        {
            "book": BOOK_BASE,
            "kind": "ref",
            "mode": None,
            "cut": None,
            "exposure": None,
            "sleeves": None,
            "schedule": None,
        },
        {
            "book": BOOK_BLEND_A05,
            "kind": "ref_e45",
            "mode": None,
            "cut": None,
            "exposure": blend_exposure(e45_full, 0.05),
            "sleeves": None,
            "schedule": None,
        },
        {
            "book": "SLEEVE_FIN_ONLY_A10",
            "kind": "ref_e45_sleeve",
            "mode": None,
            "cut": None,
            "exposure": blend_exposure(e45_full, 0.10),
            "sleeves": SLEEVE_FIN_ONLY,
            "schedule": None,
        },
    ]
    for book, mode, cut, kind in m2_specs:
        sched = build_m2_sleeve_schedule(target, intensity_lag1, cut, mode)
        sched.to_csv(OUT / "outputs" / f"{book.lower()}_sleeve_schedule.csv")
        books.append(
            {
                "book": book,
                "kind": kind,
                "mode": mode,
                "cut": cut,
                "exposure": None,
                "sleeves": None,
                "schedule": sched,
            }
        )

    rows: list[dict] = []
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
                sleeve_weight_schedule=spec["schedule"],
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
                        "mode": spec["mode"],
                        "cut": spec["cut"],
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
    metrics.to_csv(OUT / "outputs" / "m2_metrics.csv", index=False)

    deltas: list[dict] = []
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
                        "mode": spec["mode"],
                        "cut": spec["cut"],
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
    delta_df.to_csv(OUT / "outputs" / "m2_deltas.csv", index=False)

    qual_rows: list[dict] = []
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
            and float(d1["score"]) >= 0
            and d1["mdd_improve_pp"] is not None
            and float(d1["mdd_improve_pp"]) > 0
            and d2["score"] is not None
            and float(d2["score"]) >= 0
            and d2["mdd_improve_pp"] is not None
            and float(d2["mdd_improve_pp"]) > 0
        )
        q = qualify_row(years, d1["score"], d1s["score"], d1["covid_ex_score"], cost_ok)
        qual_rows.append(
            {
                "book": book,
                "kind": spec["kind"],
                "mode": spec["mode"],
                "cut": spec["cut"],
                "heldout_1x_score": d1["score"],
                "sealed_1x_score": d1s["score"],
                "covid_ex_heldout_1x_score": d1["covid_ex_score"],
                "heldout_2x_score": d2["score"],
                **q,
            }
        )
    qual_df = pd.DataFrame(qual_rows)
    qual_df.to_csv(OUT / "outputs" / "m2_section2_qualification.csv", index=False)

    m2_mask = qual_df.kind.astype(str).str.startswith("m2")
    m2_qualifiers = qual_df[m2_mask & qual_df.qualifies_section2]["book"].tolist()
    any_m2_pass = len(m2_qualifiers) > 0

    held1 = delta_df[
        (delta_df.window == "heldout_2019_plus") & (delta_df.cost_multiple == 1)
    ].sort_values("score", ascending=False)
    sealed1 = delta_df[
        (delta_df.window == "sealed_2023_plus") & (delta_df.cost_multiple == 1)
    ].sort_values("score", ascending=False)

    pass_vs_shrink: list[dict] = []
    for cut in (0.50, 0.75):
        shrink_book = f"M2_SHRINK_C{int(cut * 100):02d}"
        shrink = delta_df[
            (delta_df.book == shrink_book)
            & (delta_df.cost_multiple == 1)
            & (delta_df.window == "heldout_2019_plus")
        ].iloc[0]
        for mode, pref in (("RELOC_TEL", "M2_RELOC_TEL"), ("HYBRID_TEL", "M2_HYBRID_TEL")):
            book = f"{pref}_C{int(cut * 100):02d}"
            chal = delta_df[
                (delta_df.book == book)
                & (delta_df.cost_multiple == 1)
                & (delta_df.window == "heldout_2019_plus")
            ].iloc[0]
            qrow = qual_df[qual_df.book == book].iloc[0]
            beats = (
                chal["covid_ex_score"] is not None
                and shrink["covid_ex_score"] is not None
                and float(chal["covid_ex_score"]) > float(shrink["covid_ex_score"])
            )
            rule4_or_5 = bool(qrow["strict_noncovid_multi"] or qrow["covid_ex_heldout_pos"])
            pass_vs_shrink.append(
                {
                    "book": book,
                    "cut": cut,
                    "mode": mode,
                    "covid_ex_score": chal["covid_ex_score"],
                    "shrink_covid_ex_score": shrink["covid_ex_score"],
                    "beats_shrink_covid_ex": beats,
                    "rule4_or_5": rule4_or_5,
                    "m2_stage_pass": bool(beats and rule4_or_5),
                    "qualifies_section2": bool(qrow["qualifies_section2"]),
                }
            )
    stage_pass_df = pd.DataFrame(pass_vs_shrink)
    stage_pass_df.to_csv(OUT / "outputs" / "m2_stage_pass_vs_shrink.csv", index=False)
    any_stage_pass = bool(stage_pass_df["m2_stage_pass"].any())

    preferred = None
    m2_held = held1[held1.kind.astype(str).str.startswith("m2")]
    if not m2_held.empty:
        preferred = m2_held.iloc[0].to_dict()

    verdict = "PASS" if any_stage_pass else "FAIL_AUTOPSY"
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PAPER_ONLY",
        "ballot": "E45 M2 DEF sleeve relocate paper screen",
        "def_sleeve": DEF_SLEEVE_LABEL,
        "honesty": (
            "DEF_TEL=Telecom equity proxy only; no cash/duration ETF in live_market; "
            "DEF_CASH0 shrink control yields 0%"
        ),
        "sensor": "E45_M1_STATE_VECTOR_V0_FROZEN (lag-1 intensity)",
        "profile_ref_e45_only": E45_PROFILE_DEFAULT,
        "claim_status": CLAIM_STATUS,
        "market_path": str(MARKET_PATH.relative_to(ROOT)),
        "div_path": str(DIV_PATH.relative_to(ROOT)),
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
                "mode",
                "score",
                "mdd_improve_pp",
                "cagr_giveback_pp",
                "covid_ex_score",
                "years_helped",
            ]
        ].to_dict(orient="records"),
        "preferred_m2_heldout_1x": preferred,
        "section2_qualification": qual_rows,
        "m2_section2_qualifiers": m2_qualifiers,
        "m2_section2_any_pass": any_m2_pass,
        "m2_stage_pass_vs_shrink": pass_vs_shrink,
        "m2_stage_any_pass": any_stage_pass,
        "verdict": verdict,
        "soft_frozen": "KEEP",
        "live_default": "KEEP",
        "live_stitch": "FORBIDDEN",
        "high_beta_observe": "DRAFT_NOT_OPEN",
        "observe_sleeves_unchanged": True,
        "next_if_fail": (
            "Publish autopsy; DEF proxy may be too weak without cash/duration ingest; "
            "do not densify E45 alpha; M3 blocked until M2 pass or charter amendment"
        ),
        "non_actions": [
            "No Soft-Frozen / DEFAULT / stitch / HIGH_BETA ballot",
            "No invented replacement for retired claimed-MDD narrative",
            "No E45 same-knob densify as substitute for M2",
            "Do not treat DEF_TEL as cash or duration hedge",
        ],
    }

    (OUT / "reports" / "e45_m2_def_sleeve_relocate.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )
    (RESEARCH / "E45_M2_DEF_SLEEVE_RELOCATE.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    lines = [
        "# E45 M2 PAPER — Cash / DEF Sleeve Relocate (Actuator)",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Status: **PAPER ONLY** — Soft-Frozen **KEEP**; DEFAULT **KEEP**; stitch **FORBIDDEN**; "
        "HIGH_BETA **DRAFT / NOT OPEN**.",
        "",
        f"DEF freeze: **`{DEF_SLEEVE_LABEL}`** (frozen before metrics).",
        f"Honesty: `{payload['honesty']}`",
        "",
        f"## Verdict: **{verdict}**",
        "",
        "## Setup",
        "",
        f"- Books: `{', '.join(payload['books'])}`",
        "- Sensor: M1 frozen intensity `s_{{t-1}}` (Exact T+1 actuator lag)",
        "- Modes: SHRINK (cash@0) · RELOC_TEL · HYBRID_TEL; cuts 0.50 / 0.75",
        "- Cost multiples: 0x, 1x, 2x, 3x on BUY_FEE/SELL_FEE/SLIP/TAX_STOCK/TAX_ETF",
        "- Score: `mdd_improve_pp - 0.5*|cagr_giveback_pp|` vs BASE at same cost x",
        f"- Year help threshold: MDD improve > **{HELP_PP} pp** in {list(STRESS_YEARS)}",
        "",
        "## Held-out deltas @1x (incl. COVID-ex score)",
        "",
        "| Book | Kind | Mode | MDD dpp | Giveback | Score | COVID-ex score | Years helped |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    for r in held1.itertuples(index=False):
        lines.append(
            f"| {r.book} | {r.kind} | {r.mode or '—'} | {pp(r.mdd_improve_pp)} | "
            f"{pp(r.cagr_giveback_pp)} | {pp(r.score)} | {pp(r.covid_ex_score)} | "
            f"{r.years_helped or '—'} |"
        )
    lines += [
        "",
        "## Sealed deltas @1x",
        "",
        "| Book | Kind | Mode | MDD dpp | Giveback | Score |",
        "|---|---|---|---:|---:|---:|",
    ]
    for r in sealed1.itertuples(index=False):
        lines.append(
            f"| {r.book} | {r.kind} | {r.mode or '—'} | {pp(r.mdd_improve_pp)} | "
            f"{pp(r.cagr_giveback_pp)} | {pp(r.score)} |"
        )
    lines += [
        "",
        "## M2 stage gate vs matched SHRINK (COVID-ex held-out @1x)",
        "",
        "| Book | Beats shrink COVID-ex | Rule4∨5 | Stage PASS | §2 PASS |",
        "|---|:---:|:---:|:---:|:---:|",
    ]
    for r in pass_vs_shrink:
        lines.append(
            f"| {r['book']} | {yn(r['beats_shrink_covid_ex'])} | {yn(r['rule4_or_5'])} | "
            f"{yn(r['m2_stage_pass'])} | {yn(r['qualifies_section2'])} |"
        )
    lines += [
        "",
        "## Section-2 qualification (binding)",
        "",
        "| Book | Multi≥2 | Strict non-COVID≥2 | Held>0 | Sealed>-1 | COVID-ex>0 | Cost1-2x | PASS |",
        "|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]
    for r in qual_rows:
        lines.append(
            f"| {r['book']} | {yn(r['multi_event'])} | {yn(r['strict_noncovid_multi'])} | "
            f"{yn(r['heldout_score_pos'])} | {yn(r['sealed_score_ok'])} | "
            f"{yn(r['covid_ex_heldout_pos'])} | {yn(r['cost_1x_2x_ok'])} | "
            f"{'YES' if r['qualifies_section2'] else 'NO'} |"
        )
    if preferred:
        lines += [
            "",
            "## Read-through (paper)",
            "",
            f"1. Best M2 on held-out @1x: **`{preferred['book']}`** "
            f"(score {pp(preferred['score'])}; COVID-ex {pp(preferred['covid_ex_score'])}; "
            f"years `{preferred['years_helped'] or '—'}`).",
            f"2. Any M2 clears full Section-2? "
            f"**{'YES: ' + ', '.join(m2_qualifiers) if any_m2_pass else 'NO'}**.",
            f"3. M2 stage pass (relocate/hybrid beats shrink on COVID-ex and rule 4∨5)? "
            f"**{'YES' if any_stage_pass else 'NO'}**.",
            "4. If NO: autopsy — DEF_TEL equity proxy may be too weak without cash/duration ingest; "
            "do **not** densify E45 alpha; M3 stays blocked pending charter amendment or stronger DEF data.",
            "5. Does **not** open Soft-Frozen / DEFAULT / stitch / HIGH_BETA ballots.",
        ]
    lines += [
        "",
        "## Governance",
        "",
        "- Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN · HIGH_BETA DRAFT/NOT OPEN",
        "- Claimed MDD status: `RETIRED_HISTORICAL_NARRATIVE` — no invented replacement",
        "- Freeze doc: `research/e45/E45_M2_DEF_SLEEVE_V0_FROZEN.md`",
        "",
        "## Reproduce",
        "",
        "```bash",
        "python3 scripts/e45_m2_def_sleeve_relocate_paper.py",
        "```",
        "",
        "Repro: `repro/e45-m2-def-sleeve-relocate/` · Market: `forward/e21/live_market.csv`",
        "",
    ]
    md = "\n".join(lines) + "\n"
    (OUT / "reports" / "e45_m2_def_sleeve_relocate.md").write_text(md)
    (RESEARCH / "E45_M2_DEF_SLEEVE_RELOCATE.md").write_text(md)
    (OPS / "E45_M2_DEF_SLEEVE_RELOCATE.md").write_text(
        "\n".join(
            [
                "# Ops pointer — E45 M2 DEF sleeve relocate (paper)",
                "",
                f"Verdict: **{verdict}**",
                "",
                "- Research: `research/e45/E45_M2_DEF_SLEEVE_RELOCATE.md`",
                "- Freeze: `research/e45/E45_M2_DEF_SLEEVE_V0_FROZEN.md`",
                "- Repro: `repro/e45-m2-def-sleeve-relocate/`",
                "- Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN",
                "",
            ]
        )
    )
    print(f"DONE verdict={verdict} stage_pass={any_stage_pass} section2={any_m2_pass}", flush=True)


if __name__ == "__main__":
    main()
