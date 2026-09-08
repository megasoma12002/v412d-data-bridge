#!/usr/bin/env python3
"""E45 M3 v1 PAPER — three-state machine on RELOC_BIL_FX (true DEF).

Frozen BEFORE metrics: research/e45/E45_M3_THREE_STATE_BIL_FX_V1_FROZEN.md

Why: v0 (RELOC_TEL) FAIL_AUTOPSY; M2 §2 winners use BIL_FX. Continue new-mechanism
ladder outside C35×Soft-Frozen-regime soft-mult.

Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN · no live wire · no invent MDD.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from e45_crisis_core import (
    build_m2_sleeve_schedule,
    build_m3_sleeve_schedule,
    build_m3_sleeve_schedule_bil_fx,
)
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
from e45_m2_true_def_relocate_paper import CODE_BIL_FX, build_def_bars
from e45_paper_harness import (
    BOOK_BASE,
    BOOK_BLEND_A05,
    CLAIM_STATUS,
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

OUT = ROOT / "repro/e45-m3-bil-fx-v1-20260908"
RESEARCH = ROOT / "research/e45"
OPS = ROOT / "research/ops"

M3_LABEL = "E45_M3_THREE_STATE_BIL_FX_V1_FROZEN_2026-09-08"
COST_MULTS = (0, 1, 2, 3)
FOCUS = ("heldout_2019_plus", "sealed_2023_plus", "full")
WINDOWS = {k: WINDOWS_STANDARD[k] for k in FOCUS}
M3_BOOK = "M3_BIL_FX_V1"
M2_REF = "M2_RELOC_BIL_FX_C35"
M3_V0 = "M3_STATE_V0"
ALERT_PP = 3.0
PAUSE_PP = 5.0


def tip_giveback(base: pd.DataFrame, chal: pd.DataFrame) -> dict:
    asof = min(pd.to_datetime(base["date"]).max(), pd.to_datetime(chal["date"]).max())

    def one(window: str):
        start = pd.Timestamp(asof.year, 1, 1) if window == "ytd" else asof - pd.Timedelta(days=365)
        b = base[(pd.to_datetime(base["date"]) >= start) & (pd.to_datetime(base["date"]) <= asof)]
        c = chal[(pd.to_datetime(chal["date"]) >= start) & (pd.to_datetime(chal["date"]) <= asof)]
        if len(b) < 20 or len(c) < 20:
            return None, "INSUFFICIENT"
        sb = window_stats(b.reset_index(drop=True), None, None)
        sc = window_stats(c.reset_index(drop=True), None, None)
        if sb.get("cagr") is None or sc.get("cagr") is None:
            return None, "INSUFFICIENT"
        g = (sb["cagr"] - sc["cagr"]) * 100.0
        gate = "PAUSE_REVIEW" if g > PAUSE_PP else ("ALERT" if g > ALERT_PP else "PASS")
        return g, gate

    ytd_g, ytd_gate = one("ytd")
    y1_g, y1_gate = one("trailing_1y")
    return {
        "asof": asof.date().isoformat(),
        "ytd_giveback_pp": ytd_g,
        "ytd_gate": ytd_gate,
        "trailing_1y_giveback_pp": y1_g,
        "trailing_1y_gate": y1_gate,
        "tip_clean": ytd_gate == "PASS" and y1_gate == "PASS",
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "outputs").mkdir(exist_ok=True)
    (OUT / "reports").mkdir(exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)
    OPS.mkdir(parents=True, exist_ok=True)

    print("loading ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, _s, target, regime = e16_features(market)
    state = build_m1_state(market)
    intensity = state["s_t"].astype(float)
    intensity_lag1 = intensity.shift(1).fillna(0.0)

    def_bars = build_def_bars(pd.DatetimeIndex(sorted(market["date"].unique())))
    bil = def_bars[def_bars["code"] == CODE_BIL_FX].copy()
    market_aug = pd.concat([market, bil], ignore_index=True)

    print("schedules ...", flush=True)
    m3_v1_sched, state_t = build_m3_sleeve_schedule_bil_fx(target, intensity)
    m3_v0_sched, _ = build_m3_sleeve_schedule(target, intensity)
    m2_sched = build_m2_sleeve_schedule(target, intensity_lag1, 0.35, "RELOC_BIL_FX")
    m3_v1_sched.to_csv(OUT / "outputs/m3_bil_fx_v1_sleeve_schedule.csv")
    state_t.to_csv(OUT / "outputs/m3_state_path.csv", header=True)
    occ = {str(k): float(v) for k, v in state_t.value_counts(normalize=True).items()}
    pd.Series(occ, name="share").to_csv(OUT / "outputs/m3_state_occupancy.csv", header=True)

    e45_full = e45_full_exposure(market)
    books: list[dict] = [
        {"book": BOOK_BASE, "kind": "ref", "mode": None, "exposure": None, "sleeves": None, "schedule": None, "aug": False},
        {
            "book": BOOK_BLEND_A05,
            "kind": "ref_e45",
            "mode": None,
            "exposure": blend_exposure(e45_full, 0.05),
            "sleeves": None,
            "schedule": None,
            "aug": False,
        },
        {
            "book": "SLEEVE_FIN_ONLY_A10",
            "kind": "ref_e45_sleeve",
            "mode": None,
            "exposure": blend_exposure(e45_full, 0.10),
            "sleeves": SLEEVE_FIN_ONLY,
            "schedule": None,
            "aug": False,
        },
        {
            "book": M2_REF,
            "kind": "ref_m2_continuous",
            "mode": "RELOC_BIL_FX_C35",
            "exposure": None,
            "sleeves": None,
            "schedule": m2_sched,
            "aug": True,
        },
        {
            "book": M3_V0,
            "kind": "ref_m3_v0_tel",
            "mode": "STATE_V0_TEL",
            "exposure": None,
            "sleeves": None,
            "schedule": m3_v0_sched,
            "aug": False,
        },
        {
            "book": M3_BOOK,
            "kind": "m3_bil_fx_v1",
            "mode": "STATE_V1_BIL_FX",
            "exposure": None,
            "sleeves": None,
            "schedule": m3_v1_sched,
            "aug": True,
        },
    ]

    rows: list[dict] = []
    navs: dict[tuple[str, int], pd.DataFrame] = {}
    for spec in books:
        mkt = market_aug if spec["aug"] else market
        for mult in COST_MULTS:
            print(f"sim {spec['book']} x{mult} ...", flush=True)
            nav, fills, meta = run_early_stack(
                mkt,
                target,
                regime,
                dividends,
                e45_exposure=spec["exposure"],
                e45_sleeve_names=spec["sleeves"],
                sleeve_weight_schedule=spec["schedule"],
                def_code=CODE_BIL_FX if spec["aug"] else None,
                cost_multiple=float(mult),
            )
            assert meta.get("exact_t1_ok"), spec["book"]
            tag = f"{spec['book'].lower()}_x{mult}"
            nav.to_csv(OUT / "outputs" / f"{tag}_daily_nav.csv", index=False)
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
                        "n_days": st.get("n_days"),
                        "n_fills": to["n_fills"],
                        "fees_tax_sum": to["fees_tax_sum"],
                        "turnover_per_year": to["turnover_per_year"],
                        "exact_t1_ok": bool(meta.get("exact_t1_ok")),
                    }
                )
    metrics = pd.DataFrame(rows)
    metrics.to_csv(OUT / "outputs/m3_bil_fx_v1_metrics.csv", index=False)

    deltas: list[dict] = []
    tip_by_book: dict[str, dict] = {}
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
                    (metrics.book == BOOK_BASE) & (metrics.cost_multiple == mult) & (metrics.window == w)
                ].iloc[0]
                cstat = metrics[
                    (metrics.book == book) & (metrics.cost_multiple == mult) & (metrics.window == w)
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
                        "covid_ex_score": cex_d["score"] if w == "heldout_2019_plus" else None,
                        "years_helped": ",".join(str(y) for y in years_helped),
                        "year_help_2015": year_helps.get(2015),
                        "year_help_2018": year_helps.get(2018),
                        "year_help_2020": year_helps.get(2020),
                        "year_help_2022": year_helps.get(2022),
                        "turnover_per_year": float(
                            metrics[
                                (metrics.book == book)
                                & (metrics.cost_multiple == mult)
                                & (metrics.window == "full")
                            ].iloc[0]["turnover_per_year"]
                        ),
                    }
                )
            if mult == 1:
                tip_by_book[book] = tip_giveback(base_nav, book_nav)

    qual_rows: list[dict] = []
    for spec in books:
        book = spec["book"]
        held1 = next(
            d
            for d in deltas
            if d["book"] == book and d["cost_multiple"] == 1 and d["window"] == "heldout_2019_plus"
        )
        held2 = next(
            d
            for d in deltas
            if d["book"] == book and d["cost_multiple"] == 2 and d["window"] == "heldout_2019_plus"
        )
        sealed1 = next(
            d
            for d in deltas
            if d["book"] == book and d["cost_multiple"] == 1 and d["window"] == "sealed_2023_plus"
        )
        years = [int(y) for y in held1["years_helped"].split(",") if y]
        cost_ok = (
            held1["score"] is not None
            and held1["score"] >= 0
            and (held1["mdd_improve_pp"] or 0) > 0
            and held2["score"] is not None
            and held2["score"] >= 0
            and (held2["mdd_improve_pp"] or 0) > 0
        )
        q = qualify_row(
            years,
            held1["score"],
            sealed1["score"],
            held1["covid_ex_score"],
            cost_ok,
        )
        qual_rows.append(
            {
                "book": book,
                "kind": spec["kind"],
                **q,
                "heldout_score": held1["score"],
                "sealed_score": sealed1["score"],
                "covid_ex_score": held1["covid_ex_score"],
                "tip": tip_by_book.get(book),
            }
        )

    delta_df = pd.DataFrame(deltas)
    delta_df.to_csv(OUT / "outputs/m3_bil_fx_v1_deltas.csv", index=False)
    qual_df = pd.DataFrame(qual_rows)
    qual_df.to_csv(OUT / "outputs/m3_bil_fx_v1_section2.csv", index=False)

    m3q = next(r for r in qual_rows if r["book"] == M3_BOOK)
    m2q = next(r for r in qual_rows if r["book"] == M2_REF)
    m3_pass_s2 = bool(m3q["qualifies_section2"])
    m3_ge_m2_cex = (
        m3q["covid_ex_score"] is not None
        and m2q["covid_ex_score"] is not None
        and m3q["covid_ex_score"] >= m2q["covid_ex_score"] - 1e-12
    )
    stage_pass = m3_pass_s2 and m3_ge_m2_cex
    verdict = "PASS" if stage_pass else "FAIL_AUTOPSY"

    held1 = {
        r["book"]: next(
            d
            for d in deltas
            if d["book"] == r["book"] and d["cost_multiple"] == 1 and d["window"] == "heldout_2019_plus"
        )
        for r in qual_rows
    }

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "E45_M3_BIL_FX_V1",
        "freeze": M3_LABEL,
        "soft_frozen_keep": [0.5, 0.95],
        "stitch": "FORBIDDEN",
        "observe_lock_unchanged": M2_REF,
        "live_wire": False,
        "claim_status": CLAIM_STATUS,
        "state_occupancy": occ,
        "section2": qual_rows,
        "heldout_1x": {b: held1[b] for b in held1},
        "tip_diagnostics_1x": tip_by_book,
        "stage_gate": {
            "m3_section2_pass": m3_pass_s2,
            "m3_covid_ex": m3q["covid_ex_score"],
            "m2_c35_covid_ex": m2q["covid_ex_score"],
            "m3_ge_m2_covid_ex": m3_ge_m2_cex,
            "stage_pass": stage_pass,
            "verdict": verdict,
        },
        "read": [
            "M3 v1 swaps v0 RELOC_TEL → RELOC_BIL_FX; hysteresis unchanged.",
            "Not a Soft-Frozen regime soft-gate on continuous C35.",
            "Even on PASS: no auto Soft-Frozen / stitch / observe OPEN.",
        ],
    }
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    RESEARCH.joinpath("E45_M3_BIL_FX_V1.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    OPS.joinpath("E45_M3_BIL_FX_V1.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")

    lines = [
        "# E45 M3 PAPER — Three-State + RELOC_BIL_FX (v1)",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Status: **PAPER ONLY** — Soft-Frozen **KEEP**; DEFAULT **KEEP**; stitch **FORBIDDEN**.",
        f"Freeze: **`{M3_LABEL}`** (frozen before metrics).",
        "Honesty: `BIL_FX=BIL×USDTWD mid (FX risk; mid optimistic); discrete states paper-only; not C35×regime soft-mult`",
        "",
        f"## Verdict: **{verdict}**",
        "",
        "## State occupancy",
        "",
        "| State | Share |",
        "|---|---:|",
    ]
    for k, v in sorted(occ.items()):
        lines.append(f"| `{k}` | {100*v:.1f}% |")
    lines += [
        "",
        "## Held-out deltas @1x (incl. COVID-ex)",
        "",
        "| Book | Kind | MDD↑pp | Giveback | Score | COVID-ex | Years | tip clean |",
        "|---|---|---:|---:|---:|---:|---|---|",
    ]
    for r in sorted(qual_rows, key=lambda x: -(x["heldout_score"] or -9e9)):
        h = held1[r["book"]]
        t = tip_by_book[r["book"]]
        lines.append(
            f"| `{r['book']}` | {r['kind']} | {pp(h['mdd_improve_pp'])} | {pp(h['cagr_giveback_pp'])} | "
            f"{pp(h['score'])} | {pp(h['covid_ex_score'])} | {h['years_helped'] or '—'} | {t['tip_clean']} |"
        )
    lines += [
        "",
        "## Section-2 qualification",
        "",
        "| Book | Multi≥2 | Strict non-COVID≥2 | Held>0 | Sealed>-1 | COVID-ex>0 | Cost1-2x | PASS |",
        "|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]
    for r in qual_rows:
        lines.append(
            f"| `{r['book']}` | {yn(r['multi_event'])} | {yn(r['strict_noncovid_multi'])} | "
            f"{yn(r['heldout_score_pos'])} | {yn(r['sealed_score_ok'])} | {yn(r['covid_ex_heldout_pos'])} | "
            f"{yn(r['cost_1x_2x_ok'])} | {'YES' if r['qualifies_section2'] else 'NO'} |"
        )
    lines += [
        "",
        "## Stage gate vs continuous M2 C35",
        "",
        f"- M3 Section-2 PASS? **{'YES' if m3_pass_s2 else 'NO'}**",
        f"- M3 COVID-ex: `{pp(m3q['covid_ex_score'])}` · M2 C35 COVID-ex: `{pp(m2q['covid_ex_score'])}` · M3≥M2? **{'YES' if m3_ge_m2_cex else 'NO'}**",
        f"- Stage verdict: **{verdict}**",
        "",
        "## Tip diagnostics @1x (non-binding)",
        "",
        "| Book | YTD gb | YTD | 1y gb | 1y |",
        "|---|---:|---|---:|---|",
    ]
    for bid, t in tip_by_book.items():
        lines.append(
            f"| `{bid}` | {pp(t['ytd_giveback_pp'])} | **{t['ytd_gate']}** | "
            f"{pp(t['trailing_1y_giveback_pp'])} | **{t['trailing_1y_gate']}** |"
        )
    lines += [
        "",
        "## Read-through",
        "",
        "1. Ladder continuation after M3-TEL fail: swap actuator to true DEF `RELOC_BIL_FX`.",
        "2. Do **not** treat this as Soft_A / hard-regime soft-mult on ungated C35.",
        "3. If FAIL: autopsy; keep M2 C35 observe + Soft_A tip twin options; continue other new sensors/actuators — do **not** densify C35×regime knobs.",
        "4. Even on PASS: dedicated human ballot required for any observe OPEN; stitch still FORBIDDEN.",
        "",
        f"Repro: `{OUT.relative_to(ROOT)}/`",
        "",
        "```bash",
        "python3 scripts/e45_m3_bil_fx_v1_paper.py",
        "```",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "REPORT.md").write_text(md)
    (OUT / "reports" / "E45_M3_BIL_FX_V1.md").write_text(md)
    RESEARCH.joinpath("E45_M3_BIL_FX_V1.md").write_text(md)
    OPS.joinpath("E45_M3_BIL_FX_V1.md").write_text(md)
    print(json.dumps(payload["stage_gate"], indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
