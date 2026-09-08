#!/usr/bin/env python3
"""E45 Soft_A × ungated C35 synthetic mix — schedule blend + NAV capital blend.

Freeze BEFORE metrics: research/e45/E45_SOFTA_C35_MIX_FROZEN.md

λ=0 ungated C35 · λ=1 Soft_A · mid = one-book intensity mix (A) and
two-book NAV return mix (B).

Soft-Frozen KEEP · stitch FORBIDDEN · observe lock unchanged.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from e16_soft_frozen_base import SOFT_FROZEN_FIN_CLIP
from e45_crisis_core import build_m2_sleeve_schedule
from e45_c35_soft_gate_paper import CUT_BASE, MODE, tip_giveback, year_mdd
from e45_m1_state_signal_paper import build_m1_state
from e45_m2_true_def_relocate_paper import CODE_BIL_FX, build_def_bars
from e45_paper_harness import (
    CLAIM_STATUS,
    ROOT,
    WINDOWS_STANDARD,
    deltas_vs_base,
    e16_features,
    load_dividends,
    load_market,
    run_early_stack,
    window_stats,
)

OUT = ROOT / "repro/e45-softa-c35-mix-20260908"
OPS = ROOT / "research/ops"
E45 = ROOT / "research/e45"

LAMBDAS = (0.0, 0.25, 0.50, 0.75, 1.0)
SOFT_MULT = {"Bull": 0.0, "Sideways": 0.25, "Bear": 0.75, "Crisis": 1.0}
STRESS_YEARS = (2015, 2018, 2020, 2022)
HELP_PP = 0.25


def regime_lag1(regime: pd.Series, index: pd.Index) -> pd.Series:
    return regime.reindex(index).fillna("Sideways").astype(str).shift(1).fillna("Sideways")


def soft_a_scale(regime: pd.Series, index: pd.Index) -> pd.Series:
    rg = regime_lag1(regime, index)
    return rg.map(lambda x: float(SOFT_MULT.get(x, 0.0))).astype(float)


def evaluate(nav_b: pd.DataFrame, nav_c: pd.DataFrame, fills=None, share_on=None) -> dict:
    win = {w: window_stats(nav_c, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
    vs = {
        w: deltas_vs_base(window_stats(nav_b, a, b), win[w])
        for w, (a, b) in WINDOWS_STANDARD.items()
    }
    year_help = {}
    for y in STRESS_YEARS:
        mb, mc = year_mdd(nav_b, y), year_mdd(nav_c, y)
        year_help[str(y)] = None if mb is None or mc is None else (abs(mb) - abs(mc)) * 100.0
    tip = tip_giveback(nav_b, nav_c)
    held = vs["heldout_2019_plus"]
    return {
        "share_days_on": share_on,
        "heldout_score": held.get("score"),
        "heldout_mdd_improve_pp": held.get("mdd_improve_pp"),
        "heldout_cagr_giveback_pp": held.get("cagr_giveback_pp"),
        "sealed_score": vs["sealed_2023_plus"].get("score"),
        "tip": tip,
        "year_mdd_help_pp": year_help,
        "non2020_events_gt_025pp": int(
            sum(1 for y in (2015, 2018, 2022) if (year_help.get(str(y)) or 0) > HELP_PP)
        ),
        "n_fills": None if fills is None else int(len(fills)),
    }


def nav_from_blend_returns(nav_u: pd.DataFrame, nav_s: pd.DataFrame, lam: float) -> pd.DataFrame:
    a = nav_u.copy()
    b = nav_s.copy()
    a["date"] = pd.to_datetime(a["date"])
    b["date"] = pd.to_datetime(b["date"])
    m = a.merge(b, on="date", suffixes=("_u", "_s"))
    ru = m["nav_u"].pct_change().fillna(0.0)
    rs = m["nav_s"].pct_change().fillna(0.0)
    r = (1.0 - lam) * ru + lam * rs
    nav = (1.0 + r).cumprod()
    return pd.DataFrame({"date": m["date"], "nav": nav})


def fmt(x, nd=2):
    return "n/a" if x is None else f"{x:+.{nd}f}"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "outputs").mkdir(exist_ok=True)
    OPS.mkdir(parents=True, exist_ok=True)
    E45.mkdir(parents=True, exist_ok=True)

    print("loading ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, _s, target, regime = e16_features(market)
    state = build_m1_state(market)
    s = state["s_t"].shift(1).fillna(0.0).astype(float)
    g = soft_a_scale(regime, s.index)
    def_bars = build_def_bars(pd.DatetimeIndex(sorted(market["date"].unique())))
    bil = def_bars[def_bars["code"] == CODE_BIL_FX].copy()
    market_aug = pd.concat([market, bil], ignore_index=True)

    print("BASE ...", flush=True)
    nav_b, _fb, meta_b = run_early_stack(market, target, regime, dividends, e45_exposure=None)
    assert meta_b.get("exact_t1_ok")
    nav_b.to_csv(OUT / "outputs/base_daily_nav.csv", index=False)

    schedule_books = {}
    nav_poles = {}

    for lam in LAMBDAS:
        # inten = s * ((1-λ) + λ*g)
        scale = (1.0 - lam) + lam * g
        inten = s * scale
        share_on = float((inten > 1e-12).mean())
        book_id = f"MIX_SCHED_L{int(round(lam * 100)):02d}"
        print(f"{book_id} ...", flush=True)
        sched = build_m2_sleeve_schedule(target, inten, CUT_BASE, MODE)
        nav_c, fills, meta = run_early_stack(
            market_aug,
            target,
            regime,
            dividends,
            e45_exposure=None,
            sleeve_weight_schedule=sched,
            def_code=CODE_BIL_FX,
            cost_multiple=1.0,
        )
        assert meta.get("exact_t1_ok"), book_id
        nav_c.to_csv(OUT / "outputs" / f"{book_id.lower()}_daily_nav.csv", index=False)
        row = evaluate(nav_b, nav_c, fills=fills, share_on=share_on)
        row.update({"id": book_id, "lambda": lam, "kind": "schedule_mix"})
        schedule_books[book_id] = row
        if abs(lam) < 1e-12:
            nav_poles["ungated"] = nav_c
        if abs(lam - 1.0) < 1e-12:
            nav_poles["soft_a"] = nav_c

    capital_books = {}
    for lam in LAMBDAS:
        book_id = f"MIX_NAV_L{int(round(lam * 100)):02d}"
        print(f"{book_id} ...", flush=True)
        nav_m = nav_from_blend_returns(nav_poles["ungated"], nav_poles["soft_a"], lam)
        nav_m.to_csv(OUT / "outputs" / f"{book_id.lower()}_daily_nav.csv", index=False)
        row = evaluate(nav_b, nav_m, fills=None, share_on=None)
        row.update({"id": book_id, "lambda": lam, "kind": "nav_capital_mix"})
        capital_books[book_id] = row

    soft = schedule_books["MIX_SCHED_L100"]
    ung = schedule_books["MIX_SCHED_L00"]

    def frontier(books: dict) -> dict:
        tip_clean = [r for r in books.values() if r["tip"]["tip_clean"]]
        beat_soft = [
            r
            for r in tip_clean
            if r["heldout_score"] is not None and r["heldout_score"] > soft["heldout_score"] + 1e-9
        ]
        best = sorted(
            tip_clean,
            key=lambda r: r["heldout_score"] if r["heldout_score"] is not None else -9e9,
            reverse=True,
        )
        return {
            "tip_clean_ids": [r["id"] for r in tip_clean],
            "tip_clean_beat_soft_a": [r["id"] for r in beat_soft],
            "best_tip_clean": best[0]["id"] if best else None,
            "best_tip_clean_heldout": None if not best else best[0]["heldout_score"],
            "improves_pareto_vs_soft_a": bool(beat_soft),
        }

    sched_front = frontier(schedule_books)
    nav_front = frontier(capital_books)

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "E45_SOFTA_C35_MIX_RESEARCH",
        "freeze": "E45_SOFTA_C35_MIX_FROZEN_2026-09-08",
        "ballot": "合成一檔 Soft_A×C35 混倉回測",
        "soft_frozen_keep": list(SOFT_FROZEN_FIN_CLIP),
        "stitch": "FORBIDDEN",
        "observe_lock_unchanged": "M2_RELOC_BIL_FX_C35",
        "live_wire": False,
        "claim_status": CLAIM_STATUS,
        "lambdas": list(LAMBDAS),
        "schedule_mix": schedule_books,
        "nav_capital_mix": capital_books,
        "poles": {
            "ungated_heldout": ung["heldout_score"],
            "soft_a_heldout": soft["heldout_score"],
            "ungated_tip": ung["tip"],
            "soft_a_tip": soft["tip"],
        },
        "schedule_frontier": sched_front,
        "nav_frontier": nav_front,
        "verdict": {
            "schedule_mix_beats_soft_a_tip_clean": sched_front["improves_pareto_vs_soft_a"],
            "nav_mix_beats_soft_a_tip_clean": nav_front["improves_pareto_vs_soft_a"],
            "preferred_read": (
                "MIX_IMPROVES_PARETO"
                if sched_front["improves_pareto_vs_soft_a"] or nav_front["improves_pareto_vs_soft_a"]
                else "MIX_INTERPOLATES_POLES__DUAL_MONITOR_STILL_CLEANER_FOR_HONESTY"
            ),
        },
    }
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    OPS.joinpath("E45_SOFTA_C35_MIX_RESEARCH.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    def table(books: dict, title: str) -> list[str]:
        lines = [
            f"## {title}",
            "",
            "| Book | λ | days on | held | sealed | YTD gb | YTD | 1y gb | 1y | tip | 2020 |",
            "|---|---:|---:|---:|---:|---:|---|---:|---|---|---:|",
        ]
        for bid in sorted(books.keys(), key=lambda x: books[x]["lambda"]):
            r = books[bid]
            t = r["tip"]
            days = "n/a" if r["share_days_on"] is None else f"{100*r['share_days_on']:.1f}%"
            lines.append(
                f"| `{bid}` | {r['lambda']:.2f} | {days} | {fmt(r['heldout_score'],3)} | "
                f"{fmt(r['sealed_score'],3)} | {fmt(t['ytd_giveback_pp'])} | **{t['ytd_gate']}** | "
                f"{fmt(t['trailing_1y_giveback_pp'])} | **{t['trailing_1y_gate']}** | "
                f"{t['tip_clean']} | {fmt(r['year_mdd_help_pp'].get('2020'))} |"
            )
        return lines + [""]

    lines = [
        "# E45 Soft_A × Ungated C35 Mix — Research",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Ballot: **合成一檔 Soft_A×C35 混倉** · Soft-Frozen **KEEP** · stitch **FORBIDDEN**",
        "",
        f"Poles: ungated held `{fmt(ung['heldout_score'],3)}` tip dirty · Soft_A held `{fmt(soft['heldout_score'],3)}` tip PASS",
        "",
    ]
    lines += table(schedule_books, "A — Schedule / intensity mix (one fill path)")
    lines += table(capital_books, "B — NAV capital mix (two books, return blend)")
    lines += [
        "## Verdict",
        "",
        f"- Schedule mix tip-clean & > Soft_A: `{sched_front['tip_clean_beat_soft_a']}`",
        f"- NAV mix tip-clean & > Soft_A: `{nav_front['tip_clean_beat_soft_a']}`",
        f"- Preferred read: **`{payload['verdict']['preferred_read']}`**",
        "",
        f"Repro: `{OUT.relative_to(ROOT)}/`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "REPORT.md").write_text(md)
    OPS.joinpath("E45_SOFTA_C35_MIX_RESEARCH.md").write_text(md)
    E45.joinpath("E45_SOFTA_C35_MIX_RESEARCH.md").write_text(md)
    print(
        json.dumps(
            {
                "schedule_beat": sched_front["tip_clean_beat_soft_a"],
                "nav_beat": nav_front["tip_clean_beat_soft_a"],
                "read": payload["verdict"]["preferred_read"],
                "soft_a": soft["heldout_score"],
                "ungated": ung["heldout_score"],
            },
            indent=2,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
