#!/usr/bin/env python3
"""E45 Sideways-conditional C35 gate — tip PASS + recover held-out vs Soft_A.

Freeze BEFORE metrics: research/e45/E45_SIDEWAYS_CONDITIONAL_FROZEN.md

Not another Sideways mult grid (0.15–0.50 already screened). Conditional open:
  CONT / HIGH_S / DD / MAX consecutive.

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
from e45_c35_soft_gate_paper import (
    CUT_BASE,
    HARD,
    MODE,
    tip_giveback,
    year_mdd,
)
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
from e50_early_stack_combined_nav import ALL

OUT = ROOT / "repro/e45-sideways-conditional-20260908"
OPS = ROOT / "research/ops"
E45 = ROOT / "research/e45"

BASELINE = "M2_RELOC_BIL_FX_C35"
SOFT_A = "M2_C35_SOFT_A"
STRESS_YEARS = (2015, 2018, 2020, 2022)
HELP_PP = 0.25
SIDE_MULT = 0.25
BEAR_MULT = 0.75
CRISIS_MULT = 1.0


def regime_lag(regime: pd.Series, index: pd.Index, n: int = 1) -> pd.Series:
    rg = regime.reindex(index).fillna("Sideways").astype(str)
    out = rg
    for _ in range(n):
        out = out.shift(1).fillna("Sideways")
    return out


def mkt_drawdown_lag1(market: pd.DataFrame, index: pd.Index, lookback: int = 60) -> pd.Series:
    wide = (
        market[market["code"].isin(ALL)]
        .pivot(index="date", columns="code", values="close")
        .sort_index()
        .ffill()
    )
    px = wide.mean(axis=1)
    peak = px.rolling(lookback, min_periods=max(20, lookback // 3)).max()
    dd = px / peak - 1.0
    return dd.reindex(index).shift(1)  # lag-1 honesty


def shaped(inten: pd.Series, regime: pd.Series, kind: str, dd: pd.Series | None = None) -> tuple[pd.Series, float]:
    s = inten.astype(float)
    rg1 = regime_lag(regime, s.index, 1)
    rg2 = regime_lag(regime, s.index, 2)
    scale = pd.Series(0.0, index=s.index)

    bear = rg1 == "Bear"
    crisis = rg1 == "Crisis"
    side = rg1 == "Sideways"

    if kind == "ungated":
        return s, float((s > 1e-12).mean())
    if kind == "hard":
        # Match prior hard gate: Bear/Crisis @ 1.0, Sideways off
        scale = scale.where(~bear, 1.0)
        scale = scale.where(~crisis, 1.0)
        out = s * scale
        return out, float((out > 1e-12).mean())
    if kind == "soft_a":
        scale = scale.where(~bear, BEAR_MULT)
        scale = scale.where(~crisis, CRISIS_MULT)
        scale = scale.where(~side, SIDE_MULT)
        out = s * scale
        return out, float((out > 1e-12).mean())

    # Conditional Sideways family: Soft_A Bear/Crisis + conditional Sideways
    scale = scale.where(~bear, BEAR_MULT)
    scale = scale.where(~crisis, CRISIS_MULT)

    side_on = pd.Series(False, index=s.index)
    if kind == "side_cont":
        side_on = side & rg2.isin(["Bear", "Crisis"])
    elif kind == "side_high_s80":
        thr = float(s.quantile(0.80))
        side_on = side & (s >= thr)
    elif kind == "side_dd05":
        assert dd is not None
        side_on = side & (dd <= -0.05)
    elif kind == "side_dd10":
        assert dd is not None
        side_on = side & (dd <= -0.10)
    elif kind in {"side_max10", "side_max20"}:
        max_n = 10 if kind == "side_max10" else 20
        # Soft_A Sideways but cap consecutive Sideways-on days
        run = 0
        flags = []
        for is_side in side.tolist():
            if is_side:
                run += 1
                flags.append(run <= max_n)
            else:
                run = 0
                flags.append(False)
        side_on = pd.Series(flags, index=s.index)
    else:
        raise ValueError(kind)

    scale = scale.where(~side_on, SIDE_MULT)
    # Sideways days that fail condition stay 0 (already)
    out = s * scale
    return out, float((out > 1e-12).mean())


SPECS = {
    BASELINE: "ungated",
    HARD: "hard",
    SOFT_A: "soft_a",
    "M2_C35_SIDE_CONT": "side_cont",
    "M2_C35_SIDE_HIGH_S80": "side_high_s80",
    "M2_C35_SIDE_DD05": "side_dd05",
    "M2_C35_SIDE_DD10": "side_dd10",
    "M2_C35_SIDE_MAX10": "side_max10",
    "M2_C35_SIDE_MAX20": "side_max20",
}


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
    inten = state["s_t"].shift(1).fillna(0.0).astype(float)
    dd = mkt_drawdown_lag1(market, inten.index, 60)
    def_bars = build_def_bars(pd.DatetimeIndex(sorted(market["date"].unique())))
    bil = def_bars[def_bars["code"] == CODE_BIL_FX].copy()
    market_aug = pd.concat([market, bil], ignore_index=True)

    print("BASE ...", flush=True)
    nav_b, _fb, meta_b = run_early_stack(market, target, regime, dividends, e45_exposure=None)
    assert meta_b.get("exact_t1_ok")

    books = {}
    for book_id, kind in SPECS.items():
        print(f"{book_id} ...", flush=True)
        shaped_i, share_on = shaped(inten, regime, kind, dd=dd)
        if kind == "ungated":
            shaped_i = inten
            share_on = float((inten > 1e-12).mean())
        sched = build_m2_sleeve_schedule(target, shaped_i, CUT_BASE, MODE)
        nav_c, fills_c, meta_c = run_early_stack(
            market_aug,
            target,
            regime,
            dividends,
            e45_exposure=None,
            sleeve_weight_schedule=sched,
            def_code=CODE_BIL_FX,
            cost_multiple=1.0,
        )
        assert meta_c.get("exact_t1_ok"), book_id
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
        books[book_id] = {
            "id": book_id,
            "kind": kind,
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
            "n_fills": int(len(fills_c)),
        }

    soft = books[SOFT_A]
    hard = books[HARD]
    ung = books[BASELINE]
    denom = (ung["heldout_score"] or 0) - (hard["heldout_score"] or 0)
    for r in books.values():
        r["recovery_vs_hard_to_ungated"] = (
            None
            if abs(denom) < 1e-12 or r["heldout_score"] is None
            else (r["heldout_score"] - hard["heldout_score"]) / denom
        )

    challengers = [r for r in books.values() if r["id"] not in (BASELINE, HARD, SOFT_A)]
    tip_clean = [r for r in challengers if r["tip"]["tip_clean"]]
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

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "E45_SIDEWAYS_CONDITIONAL_RESEARCH",
        "freeze": "E45_SIDEWAYS_CONDITIONAL_FROZEN_2026-09-08",
        "ballot": "側盤怎麼辦 / tip vs held-out — conditional Sideways screen",
        "soft_frozen_keep": list(SOFT_FROZEN_FIN_CLIP),
        "stitch": "FORBIDDEN",
        "observe_lock_unchanged": BASELINE,
        "live_wire": False,
        "claim_status": CLAIM_STATUS,
        "books": books,
        "tip_clean_challengers": [r["id"] for r in tip_clean],
        "tip_clean_beat_soft_a": [r["id"] for r in beat_soft],
        "best_tip_clean_challenger": best[0]["id"] if best else None,
        "soft_a_heldout": soft["heldout_score"],
        "verdict": {
            "sideways_conditional_beats_soft_a_tip_clean": bool(beat_soft),
            "residue_closed": not bool(beat_soft),
        },
    }
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    OPS.joinpath("E45_SIDEWAYS_CONDITIONAL_RESEARCH.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    def fmt(x, nd=2):
        return "n/a" if x is None else f"{x:+.{nd}f}"

    lines = [
        "# E45 Sideways-Conditional Gate — Research",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Goal: tip **PASS** and held-out **> Soft_A** via conditional Sideways (not mult grid).",
        "Soft-Frozen **KEEP** · stitch **FORBIDDEN** · observe lock unchanged",
        "",
        f"Soft_A held-out `{fmt(soft['heldout_score'],3)}` · Hard `{fmt(hard['heldout_score'],3)}` · Ungated `{fmt(ung['heldout_score'],3)}`",
        "",
        "| Book | kind | days on | held | recovery | sealed | YTD gb | YTD | 1y gb | 1y | tip | 2020 |",
        "|---|---|---:|---:|---:|---:|---:|---|---:|---|---|---:|",
    ]
    for bid in SPECS:
        r = books[bid]
        t = r["tip"]
        lines.append(
            f"| `{bid}` | {r['kind']} | {100*r['share_days_on']:.1f}% | {fmt(r['heldout_score'],3)} | "
            f"{fmt(r.get('recovery_vs_hard_to_ungated'),2)} | {fmt(r['sealed_score'],3)} | "
            f"{fmt(t['ytd_giveback_pp'])} | **{t['ytd_gate']}** | {fmt(t['trailing_1y_giveback_pp'])} | "
            f"**{t['trailing_1y_gate']}** | {t['tip_clean']} | {fmt(r['year_mdd_help_pp'].get('2020'))} |"
        )
    lines += [
        "",
        "## Verdict",
        "",
        f"- Tip-clean challengers: `{payload['tip_clean_challengers']}`",
        f"- Tip-clean **and** beat Soft_A: `{payload['tip_clean_beat_soft_a']}`",
        f"- Best tip-clean challenger: `{payload['best_tip_clean_challenger']}`",
        f"- Residue closed (no Soft_A beater)? **{payload['verdict']['residue_closed']}**",
        "",
        f"Repro: `{OUT.relative_to(ROOT)}/`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "REPORT.md").write_text(md)
    OPS.joinpath("E45_SIDEWAYS_CONDITIONAL_RESEARCH.md").write_text(md)
    E45.joinpath("E45_SIDEWAYS_CONDITIONAL_RESEARCH.md").write_text(md)
    print(
        json.dumps(
            {
                "beat_soft_a": payload["tip_clean_beat_soft_a"],
                "tip_clean": payload["tip_clean_challengers"],
                "best": payload["best_tip_clean_challenger"],
                "residue_closed": payload["verdict"]["residue_closed"],
                "soft_a": soft["heldout_score"],
            },
            indent=2,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
