#!/usr/bin/env python3
"""E45 M3 PAPER — three-state risk machine on Exact T+1 early-stack.

Frozen v0: research/e45/E45_M3_THREE_STATE_V0_FROZEN.md
Sensor: M1 frozen intensity s_t with hysteresis; action uses state_{t-1}.
References: continuous M1_EQW_C75 + M2_RELOC_TEL_C50 (rebuild, not retuned).

Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN · HIGH_BETA DRAFT/NOT OPEN.
Does NOT invent a replacement for retired claimed-MDD narrative.
Does NOT auto-open Soft-Frozen / stitch ballots even on Section-2 PASS.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from e45_crisis_core import build_m2_sleeve_schedule, build_m3_sleeve_schedule
from e45_m1_state_signal_paper import (
    HELP_PP,
    STRESS_YEARS,
    build_m1_state,
    covid_ex_stats,
    exposure_from_state,
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

OUT = ROOT / "repro/e45-m3-three-state-risk"
RESEARCH = ROOT / "research/e45"
OPS = ROOT / "research/ops"

M3_LABEL = "E45_M3_THREE_STATE_V0_FROZEN_2026-09-06"
COST_MULTS = (0, 1, 2, 3)
FEE_KEYS = ("BUY_FEE", "SELL_FEE", "SLIP", "TAX_STOCK", "TAX_ETF")
FOCUS = ("heldout_2019_plus", "sealed_2023_plus", "full")
WINDOWS = {k: WINDOWS_STANDARD[k] for k in FOCUS}
M3_BOOK = "M3_STATE_V0"
M2_REF = "M2_RELOC_TEL_C50"
M1_REF = "M1_EQW_C75"


def trailing_giveback_diag(base_nav: pd.DataFrame, book_nav: pd.DataFrame) -> dict:
    b = base_nav.copy()
    c = book_nav.copy()
    b["date"] = pd.to_datetime(b["date"])
    c["date"] = pd.to_datetime(c["date"])
    end = min(b["date"].max(), c["date"].max())
    out = {}
    for label, start in (
        ("ytd", pd.Timestamp(year=int(end.year), month=1, day=1)),
        ("trailing_1y", end - pd.Timedelta(days=365)),
    ):
        bb = b[(b["date"] >= start) & (b["date"] <= end)].reset_index(drop=True)
        cc = c[(c["date"] >= start) & (c["date"] <= end)].reset_index(drop=True)
        if len(bb) < 20 or len(cc) < 20:
            out[label] = {"cagr_giveback_pp": None, "mdd_improve_pp": None, "n_days": int(min(len(bb), len(cc)))}
            continue
        bst = window_stats(bb, None, None)
        cst = window_stats(cc, None, None)
        dlt = deltas_vs_base(
            {"cagr": bst.get("cagr"), "max_drawdown": bst.get("max_drawdown")},
            {"cagr": cst.get("cagr"), "max_drawdown": cst.get("max_drawdown")},
        )
        out[label] = {
            "cagr_giveback_pp": dlt["cagr_giveback_pp"],
            "mdd_improve_pp": dlt["mdd_improve_pp"],
            "n_days": int(min(len(bb), len(cc))),
        }
    return out


def main() -> None:
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)
    OPS.mkdir(parents=True, exist_ok=True)

    print("loading market ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, _s, target, regime = e16_features(market)

    print("building M1 intensity + M3 state path ...", flush=True)
    state = build_m1_state(market)
    intensity = state["s_t"].astype(float)
    intensity_lag1 = intensity.shift(1).fillna(0.0)
    state.to_csv(OUT / "outputs" / "m3_sensor_state_features.csv")
    intensity.rename("s_t").to_csv(OUT / "outputs" / "m3_intensity.csv", header=True)

    m3_sched, state_t = build_m3_sleeve_schedule(target, intensity)
    m3_sched.to_csv(OUT / "outputs" / "m3_state_v0_sleeve_schedule.csv")
    state_t.to_csv(OUT / "outputs" / "m3_state_path.csv", header=True)
    occ = {str(k): float(v) for k, v in state_t.value_counts(normalize=True).items()}
    pd.Series(occ, name="share").to_csv(OUT / "outputs" / "m3_state_occupancy.csv", header=True)

    m2_sched = build_m2_sleeve_schedule(target, intensity_lag1, 0.50, "RELOC_TEL")
    m2_sched.to_csv(OUT / "outputs" / f"{M2_REF.lower()}_sleeve_schedule.csv")
    m1_exp = exposure_from_state(state, 0.75)
    m1_exp.rename("exposure").to_csv(OUT / "outputs" / f"{M1_REF.lower()}_exposure.csv", header=True)

    e45_full = e45_full_exposure(market)
    books: list[dict] = [
        {"book": BOOK_BASE, "kind": "ref", "mode": None, "exposure": None, "sleeves": None, "schedule": None},
        {
            "book": BOOK_BLEND_A05,
            "kind": "ref_e45",
            "mode": None,
            "exposure": blend_exposure(e45_full, 0.05),
            "sleeves": None,
            "schedule": None,
        },
        {
            "book": "SLEEVE_FIN_ONLY_A10",
            "kind": "ref_e45_sleeve",
            "mode": None,
            "exposure": blend_exposure(e45_full, 0.10),
            "sleeves": SLEEVE_FIN_ONLY,
            "schedule": None,
        },
        {
            "book": M1_REF,
            "kind": "ref_m1_continuous",
            "mode": "EQW_C75",
            "exposure": m1_exp,
            "sleeves": None,
            "schedule": None,
        },
        {
            "book": M2_REF,
            "kind": "ref_m2_continuous",
            "mode": "RELOC_TEL_C50",
            "exposure": None,
            "sleeves": None,
            "schedule": m2_sched,
        },
        {
            "book": M3_BOOK,
            "kind": "m3_state",
            "mode": "STATE_V0",
            "exposure": None,
            "sleeves": None,
            "schedule": m3_sched,
        },
    ]

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
    metrics.to_csv(OUT / "outputs" / "m3_metrics.csv", index=False)

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
    delta_df.to_csv(OUT / "outputs" / "m3_deltas.csv", index=False)

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
                "heldout_1x_score": d1["score"],
                "sealed_1x_score": d1s["score"],
                "covid_ex_heldout_1x_score": d1["covid_ex_score"],
                "heldout_2x_score": d2["score"],
                **q,
            }
        )
    qual_df = pd.DataFrame(qual_rows)
    qual_df.to_csv(OUT / "outputs" / "m3_section2_qualification.csv", index=False)

    held1 = delta_df[
        (delta_df.window == "heldout_2019_plus") & (delta_df.cost_multiple == 1)
    ].sort_values("score", ascending=False)
    sealed1 = delta_df[
        (delta_df.window == "sealed_2023_plus") & (delta_df.cost_multiple == 1)
    ].sort_values("score", ascending=False)

    m3_q = qual_df[qual_df.book == M3_BOOK].iloc[0]
    m2_q = qual_df[qual_df.book == M2_REF].iloc[0]
    m3_covid = m3_q["covid_ex_heldout_1x_score"]
    m2_covid = m2_q["covid_ex_heldout_1x_score"]
    m3_covid_f = float(m3_covid) if m3_covid == m3_covid and m3_covid is not None else None
    m2_covid_f = float(m2_covid) if m2_covid == m2_covid and m2_covid is not None else None
    beats_m2 = m3_covid_f is not None and m2_covid_f is not None and m3_covid_f >= m2_covid_f
    section2_pass = bool(m3_q["qualifies_section2"])
    stage_pass = bool(section2_pass and beats_m2)
    verdict = "PASS" if stage_pass else "FAIL_AUTOPSY"

    giveback = trailing_giveback_diag(navs[(BOOK_BASE, 1)], navs[(M3_BOOK, 1)])
    pd.DataFrame(
        [
            {
                "m3_section2_pass": section2_pass,
                "m3_covid_ex_score": m3_covid_f,
                "m2_ref_covid_ex_score": m2_covid_f,
                "beats_or_ties_m2_covid_ex": beats_m2,
                "m3_stage_pass": stage_pass,
                "verdict": verdict,
            }
        ]
    ).to_csv(OUT / "outputs" / "m3_stage_pass_vs_m2.csv", index=False)

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PAPER_ONLY",
        "ballot": "E45 M3 three-state risk machine paper screen",
        "m3_freeze": M3_LABEL,
        "honesty": (
            "DEF_TEL=Telecom equity proxy only; discrete states are paper risk regimes; "
            "no Soft-Frozen/stitch auto-open"
        ),
        "sensor": "E45_M1_STATE_VECTOR_V0_FROZEN (hysteresis on s_t; action lag-1)",
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
        "state_occupancy": occ,
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
                "turnover_per_year",
            ]
        ].to_dict(orient="records"),
        "section2_qualification": qual_rows,
        "m3_section2_pass": section2_pass,
        "m3_covid_ex_heldout_1x": m3_covid_f,
        "m2_ref_covid_ex_heldout_1x": m2_covid_f,
        "beats_or_ties_m2_covid_ex": beats_m2,
        "m3_stage_pass": stage_pass,
        "verdict": verdict,
        "giveback_diagnostics_nonbinding": giveback,
        "soft_frozen": "KEEP",
        "live_default": "KEEP",
        "live_stitch": "FORBIDDEN",
        "high_beta_observe": "DRAFT_NOT_OPEN",
        "observe_sleeves_unchanged": True,
        "auto_open_soft_frozen_or_stitch": False,
        "next_if_fail": (
            "Publish autopsy; keep observe E45 sleeves as tax-control refs only; "
            "do not densify E45 alpha; do not open Soft-Frozen/stitch"
        ),
        "next_if_pass": (
            "Charter paper ladder complete; dedicated human ballot still required "
            "before any Soft-Frozen/observe OPEN; stitch remains FORBIDDEN"
        ),
        "non_actions": [
            "No Soft-Frozen / DEFAULT / stitch / HIGH_BETA ballot",
            "No invented replacement for retired claimed-MDD narrative",
            "No E45 same-knob densify as substitute for M3",
            "Do not treat DEF_TEL as cash or duration hedge",
            "Do not auto-OPEN observe from Section-2 PASS alone",
        ],
    }
    (OUT / "reports" / "e45_m3_three_state_risk.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )
    (RESEARCH / "E45_M3_THREE_STATE_RISK.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    lines = [
        "# E45 M3 PAPER — Three-State Risk Machine",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Status: **PAPER ONLY** — Soft-Frozen **KEEP**; DEFAULT **KEEP**; stitch **FORBIDDEN**; "
        "HIGH_BETA **DRAFT / NOT OPEN**.",
        "",
        f"M3 freeze: **`{M3_LABEL}`** (frozen before metrics).",
        f"Honesty: `{payload['honesty']}`",
        "",
        f"## Verdict: **{verdict}**",
        "",
        "## Setup",
        "",
        f"- Books: `{', '.join(payload['books'])}`",
        "- Sensor: M1 frozen `s_t` with hysteresis; action applies `state_{t-1}` (Exact T+1)",
        "- Actions: NORMAL=identity · SLOW_BEAR=RELOC_TEL(u=0.40) · CRASH=RELOC_TEL(u=0.75)",
        f"- Continuous refs: `{M1_REF}`, `{M2_REF}` (rebuild only)",
        "- Cost multiples: 0x/1x/2x/3x; qualify on 1x & 2x",
        f"- Year help threshold: MDD improve > **{HELP_PP} pp** in {list(STRESS_YEARS)}",
        "",
        "## State occupancy (full sample)",
        "",
        "| State | Share |",
        "|---|---:|",
    ]
    for k, v in sorted(occ.items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"| {k} | {v:.1%} |")
    lines += [
        "",
        "## Held-out deltas @1x (incl. COVID-ex score)",
        "",
        "| Book | Kind | Mode | MDD dpp | Giveback | Score | COVID-ex score | Years helped | TO/yr |",
        "|---|---|---|---:|---:|---:|---:|---|---:|",
    ]
    for r in held1.itertuples(index=False):
        lines.append(
            f"| {r.book} | {r.kind} | {r.mode or '—'} | {pp(r.mdd_improve_pp)} | "
            f"{pp(r.cagr_giveback_pp)} | {pp(r.score)} | {pp(r.covid_ex_score)} | "
            f"{r.years_helped or '—'} | {pp(r.turnover_per_year)} |"
        )
    lines += [
        "",
        "## Sealed deltas @1x",
        "",
        "| Book | Kind | Mode | MDD dpp | Giveback | Score | TO/yr |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for r in sealed1.itertuples(index=False):
        lines.append(
            f"| {r.book} | {r.kind} | {r.mode or '—'} | {pp(r.mdd_improve_pp)} | "
            f"{pp(r.cagr_giveback_pp)} | {pp(r.score)} | {pp(r.turnover_per_year)} |"
        )
    lines += [
        "",
        "## M3 stage gate vs continuous M2",
        "",
        f"- M3 Section-2 PASS? **{'YES' if section2_pass else 'NO'}**",
        f"- M3 COVID-ex held-out score: **{pp(m3_covid_f)}**",
        f"- {M2_REF} COVID-ex held-out score: **{pp(m2_covid_f)}**",
        f"- M3 ≥ M2 on COVID-ex? **{'YES' if beats_m2 else 'NO'}**",
        f"- M3 stage PASS? **{'YES' if stage_pass else 'NO'}**",
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
    gb_ytd = giveback.get("ytd", {})
    gb_1y = giveback.get("trailing_1y", {})
    lines += [
        "",
        "## Giveback diagnostics (non-binding)",
        "",
        f"- YTD CAGR giveback vs BASE @1x: **{pp(gb_ytd.get('cagr_giveback_pp'))}** "
        f"(MDD help {pp(gb_ytd.get('mdd_improve_pp'))})",
        f"- Trailing 1y CAGR giveback vs BASE @1x: **{pp(gb_1y.get('cagr_giveback_pp'))}** "
        f"(MDD help {pp(gb_1y.get('mdd_improve_pp'))})",
        "- These diagnostics do **not** open Soft-Frozen / stitch / HIGH_BETA ballots.",
        "",
        "## Read-through (paper)",
        "",
        f"1. M3 book `{M3_BOOK}` Section-2: **{'PASS' if section2_pass else 'FAIL'}**.",
        f"2. Continuous M2 ref COVID-ex comparison: M3 {pp(m3_covid_f)} vs M2 {pp(m2_covid_f)} → "
        f"**{'≥ M2' if beats_m2 else '< M2'}**.",
        f"3. Stage verdict: **{verdict}**.",
        "4. If FAIL: autopsy — discrete machine did not beat continuous M2 and/or missed Section-2; "
        "keep observe E45 sleeves as tax-control refs; do **not** densify E45 α.",
        "5. Even on PASS: **no auto Soft-Frozen / stitch / observe OPEN** — needs dedicated human ballot.",
        "",
        "## Governance",
        "",
        "- Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN · HIGH_BETA DRAFT/NOT OPEN",
        "- Claimed MDD status: `RETIRED_HISTORICAL_NARRATIVE` — no invented replacement",
        "- Freeze doc: `research/e45/E45_M3_THREE_STATE_V0_FROZEN.md`",
        "",
        "## Reproduce",
        "",
        "```bash",
        "python3 scripts/e45_m3_three_state_risk_paper.py",
        "```",
        "",
        "Repro: `repro/e45-m3-three-state-risk/` · Market: `forward/e21/live_market.csv`",
        "",
    ]
    md = "\n".join(lines) + "\n"
    (OUT / "reports" / "e45_m3_three_state_risk.md").write_text(md)
    (RESEARCH / "E45_M3_THREE_STATE_RISK.md").write_text(md)
    (OPS / "E45_M3_THREE_STATE_RISK.md").write_text(
        "\n".join(
            [
                "# Ops pointer — E45 M3 three-state risk machine (paper)",
                "",
                f"Verdict: **{verdict}**",
                "",
                "- Research: `research/e45/E45_M3_THREE_STATE_RISK.md`",
                "- Freeze: `research/e45/E45_M3_THREE_STATE_V0_FROZEN.md`",
                "- Repro: `repro/e45-m3-three-state-risk/`",
                "- Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN",
                "- No auto Soft-Frozen/stitch/observe OPEN from this pack",
                "",
            ]
        )
    )
    print(
        f"DONE verdict={verdict} section2={section2_pass} beats_m2={beats_m2} "
        f"m3_covid={m3_covid_f} m2_covid={m2_covid_f}",
        flush=True,
    )


if __name__ == "__main__":
    main()
