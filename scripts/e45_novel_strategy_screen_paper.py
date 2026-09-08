#!/usr/bin/env python3
"""E45 novel strategy screen — outside exhausted C35×regime soft-mult.

Freeze BEFORE metrics: research/e45/E45_NOVEL_STRATEGY_SCREEN_FROZEN.md

Ideas: DD-armed C35, USDTWD FX sensor, FX-gated Soft_A, FIN-only Soft_A
relocate, Soft_A nest blend-α=0.05.

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
from e45_crisis_core import apply_m2_def_relocate, build_m2_sleeve_schedule
from e45_c35_soft_gate_paper import CUT_BASE, MODE, tip_giveback, year_mdd
from e45_m1_state_signal_paper import build_m1_state
from e45_m2_true_def_relocate_paper import CODE_BIL_FX, DEF_DIR, build_def_bars
from e45_paper_harness import (
    CLAIM_STATUS,
    ROOT,
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
from e50_early_stack_combined_nav import ALL

OUT = ROOT / "repro/e45-novel-strategy-20260908"
OPS = ROOT / "research/ops"
E45 = ROOT / "research/e45"

SOFT_MULT = {"Bull": 0.0, "Sideways": 0.25, "Bear": 0.75, "Crisis": 1.0}
STRESS_YEARS = (2015, 2018, 2020, 2022)
HELP_PP = 0.25
SOFT_A = "SOFT_A"
UNGATED = "UNGATED_C35"


def regime_lag1(regime: pd.Series, index: pd.Index) -> pd.Series:
    return regime.reindex(index).fillna("Sideways").astype(str).shift(1).fillna("Sideways")


def soft_scale(regime: pd.Series, index: pd.Index) -> pd.Series:
    return regime_lag1(regime, index).map(lambda x: float(SOFT_MULT.get(x, 0.0))).astype(float)


def mkt_dd_lag1(market: pd.DataFrame, index: pd.Index, lookback: int = 60) -> pd.Series:
    wide = (
        market[market["code"].isin(ALL)]
        .pivot(index="date", columns="code", values="close")
        .sort_index()
        .ffill()
    )
    px = wide.mean(axis=1)
    peak = px.rolling(lookback, min_periods=max(20, lookback // 3)).max()
    return (px / peak - 1.0).reindex(index).shift(1)


def fx_risk_lag1(index: pd.Index) -> pd.Series:
    fx = pd.read_csv(DEF_DIR / "USDTWD_finmind.csv", parse_dates=["date"]).sort_values("date")
    fx = fx.set_index("date")["usdtwd_mid"].astype(float).reindex(index).ffill()
    x = np.log(fx / fx.shift(1))
    mu = x.rolling(60, min_periods=20).mean()
    sd = x.rolling(60, min_periods=20).std()
    z = (x - mu) / sd.replace(0.0, np.nan)
    fx_map = (z.clip(lower=0.0) / 2.0).clip(0.0, 1.0).fillna(0.0)
    return fx_map.shift(1).fillna(0.0)


def finonly_reloc_schedule(base_targets: pd.DataFrame, intensity_lag1: pd.Series, cut: float) -> pd.DataFrame:
    rows, idx = [], []
    for dt, row in base_targets.iterrows():
        if dt not in intensity_lag1.index:
            continue
        u = float(np.clip(float(cut) * float(intensity_lag1.loc[dt]), 0.0, 1.0))
        w_fin = float(row["Financial"])
        w_tel = float(row["Telecom"])
        w_0050 = float(row["0050"])
        move = w_fin * u
        rows.append(
            {
                "Financial": w_fin - move,
                "Telecom": w_tel,
                "0050": w_0050,
                "DEF": move,
            }
        )
        idx.append(dt)
    return pd.DataFrame(rows, index=pd.DatetimeIndex(idx))


def evaluate(nav_b, nav_c, fills=None, share_on=None):
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
    g = soft_scale(regime, s.index)
    dd = mkt_dd_lag1(market, s.index)
    fx = fx_risk_lag1(s.index)
    e45_full = e45_full_exposure(market)
    a05 = blend_exposure(e45_full, 0.05)

    def_bars = build_def_bars(pd.DatetimeIndex(sorted(market["date"].unique())))
    bil = def_bars[def_bars["code"] == CODE_BIL_FX].copy()
    market_aug = pd.concat([market, bil], ignore_index=True)

    print("BASE ...", flush=True)
    nav_b, _fb, meta_b = run_early_stack(market, target, regime, dividends, e45_exposure=None)
    assert meta_b.get("exact_t1_ok")

    # intensity / schedule specs
    in_dd = dd <= -0.05
    specs: dict[str, dict] = {
        UNGATED: {"inten": s, "finonly": False, "nest_a05": False},
        SOFT_A: {"inten": s * g, "finonly": False, "nest_a05": False},
        "DD05_FULL_ELSE_SOFT": {
            "inten": pd.Series(np.where(in_dd.fillna(False), s, s * g), index=s.index),
            "finonly": False,
            "nest_a05": False,
        },
        "DD05_FULL_ELSE_OFF": {
            "inten": pd.Series(np.where(in_dd.fillna(False), s, 0.0), index=s.index),
            "finonly": False,
            "nest_a05": False,
        },
        "FXZ_RELOC_C35": {"inten": fx, "finonly": False, "nest_a05": False},
        "FXZ_GATE_SOFT_A": {
            "inten": (s * g) * (fx >= 0.5).astype(float),
            "finonly": False,
            "nest_a05": False,
        },
        "FINONLY_SOFT_A": {"inten": s * g, "finonly": True, "nest_a05": False},
        "SOFT_A_NEST_A05": {"inten": s * g, "finonly": False, "nest_a05": True},
    }

    books = {}
    for book_id, spec in specs.items():
        print(f"{book_id} ...", flush=True)
        inten = spec["inten"].astype(float)
        share_on = float((inten > 1e-12).mean())
        if spec["finonly"]:
            sched = finonly_reloc_schedule(target, inten, CUT_BASE)
        else:
            sched = build_m2_sleeve_schedule(target, inten, CUT_BASE, MODE)
        nav_c, fills, meta = run_early_stack(
            market_aug,
            target,
            regime,
            dividends,
            e45_exposure=a05 if spec["nest_a05"] else None,
            sleeve_weight_schedule=sched,
            def_code=CODE_BIL_FX,
            cost_multiple=1.0,
        )
        assert meta.get("exact_t1_ok"), book_id
        nav_c.to_csv(OUT / "outputs" / f"{book_id.lower()}_daily_nav.csv", index=False)
        row = evaluate(nav_b, nav_c, fills=fills, share_on=share_on)
        row.update({"id": book_id, "family": "novel" if book_id not in (UNGATED, SOFT_A) else "baseline"})
        books[book_id] = row

    soft = books[SOFT_A]
    novel = [r for r in books.values() if r["family"] == "novel"]
    tip_clean = [r for r in novel if r["tip"]["tip_clean"]]
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
    # also note tip-dirty that beat soft on score
    dirty_beat = [
        r
        for r in novel
        if (not r["tip"]["tip_clean"])
        and r["heldout_score"] is not None
        and r["heldout_score"] > soft["heldout_score"] + 1e-9
    ]

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "E45_NOVEL_STRATEGY_SCREEN",
        "freeze": "E45_NOVEL_STRATEGY_SCREEN_FROZEN_2026-09-08",
        "ballot": "請想新的策略",
        "soft_frozen_keep": list(SOFT_FROZEN_FIN_CLIP),
        "stitch": "FORBIDDEN",
        "observe_lock_unchanged": "M2_RELOC_BIL_FX_C35",
        "live_wire": False,
        "claim_status": CLAIM_STATUS,
        "books": books,
        "tip_clean_novel": [r["id"] for r in tip_clean],
        "tip_clean_beat_soft_a": [r["id"] for r in beat_soft],
        "tip_dirty_beat_soft_a": [r["id"] for r in dirty_beat],
        "best_tip_clean_novel": best[0]["id"] if best else None,
        "soft_a_heldout": soft["heldout_score"],
        "verdict": {
            "novel_beats_soft_a_tip_clean": bool(beat_soft),
            "operational_stack_unchanged": not bool(beat_soft),
        },
    }
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    OPS.joinpath("E45_NOVEL_STRATEGY_SCREEN.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    lines = [
        "# E45 Novel Strategy Screen",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Ballot: **請想新的策略** · Soft-Frozen **KEEP** · stitch **FORBIDDEN**",
        "Outside exhausted C35×regime soft-mult / Sideways / mid-λ mix.",
        "",
        f"Soft_A held-out `{fmt(soft['heldout_score'],3)}` · Ungated `{fmt(books[UNGATED]['heldout_score'],3)}`",
        "",
        "| Book | family | days on | held | sealed | YTD gb | YTD | 1y gb | 1y | tip | 2020 |",
        "|---|---|---:|---:|---:|---:|---|---:|---|---|---:|",
    ]
    for bid in specs:
        r = books[bid]
        t = r["tip"]
        lines.append(
            f"| `{bid}` | {r['family']} | {100*r['share_days_on']:.1f}% | {fmt(r['heldout_score'],3)} | "
            f"{fmt(r['sealed_score'],3)} | {fmt(t['ytd_giveback_pp'])} | **{t['ytd_gate']}** | "
            f"{fmt(t['trailing_1y_giveback_pp'])} | **{t['trailing_1y_gate']}** | {t['tip_clean']} | "
            f"{fmt(r['year_mdd_help_pp'].get('2020'))} |"
        )
    lines += [
        "",
        "## Verdict",
        "",
        f"- Tip-clean novel: `{payload['tip_clean_novel']}`",
        f"- Tip-clean **and** beat Soft_A: `{payload['tip_clean_beat_soft_a']}`",
        f"- Tip-dirty but score > Soft_A: `{payload['tip_dirty_beat_soft_a']}`",
        f"- Best tip-clean novel: `{payload['best_tip_clean_novel']}`",
        f"- Operational Soft_A+ungated dual stack unchanged? **{payload['verdict']['operational_stack_unchanged']}**",
        "",
        f"Repro: `{OUT.relative_to(ROOT)}/`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "REPORT.md").write_text(md)
    OPS.joinpath("E45_NOVEL_STRATEGY_SCREEN.md").write_text(md)
    E45.joinpath("E45_NOVEL_STRATEGY_SCREEN.md").write_text(md)
    print(
        json.dumps(
            {
                "beat_soft_a": payload["tip_clean_beat_soft_a"],
                "tip_clean": payload["tip_clean_novel"],
                "dirty_beat": payload["tip_dirty_beat_soft_a"],
                "best": payload["best_tip_clean_novel"],
            },
            indent=2,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
