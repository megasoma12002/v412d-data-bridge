#!/usr/bin/env python3
"""E45 C35 + Soft-Frozen regime gate — PAPER research.

Ballot: 「研究 C35 + 多空閘門」

Hypothesis: C35 tip giveback is high because M1 intensity fires defense
in Bull/Sideways; gate relocate to Bear/Crisis (or not-Bull) should cut
recent giveback while keeping crisis MDD help.

Books (all RELOC_BIL_FX @ c=0.35, Exact T+1 lag-1 sensor + lag-1 regime):
  M2_RELOC_BIL_FX_C35              — ungated baseline (observe lock)
  M2_C35_GATE_NOT_BULL             — off in Bull
  M2_C35_GATE_BEAR_CRISIS          — on only in Bear/Crisis
  M2_C35_GATE_CRISIS_ONLY          — on only in Crisis

Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN · no observe lock flip.
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
from e45_m1_state_signal_paper import build_m1_state
from e45_m2_true_def_relocate_paper import CODE_BIL_FX, build_def_bars
from e45_paper_harness import (
    BOOK_BASE,
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
from research_metric_helpers import mdd_delta_pp

OUT = ROOT / "repro/e45-c35-regime-gate-20260908"
OPS = ROOT / "research/ops"
E45 = ROOT / "research/e45"

CUT = 0.35
MODE = "RELOC_BIL_FX"
BASELINE = "M2_RELOC_BIL_FX_C35"
STRESS_YEARS = (2015, 2018, 2020, 2022)
HELP_PP = 0.25
ALERT_PP = 3.0
PAUSE_PP = 5.0

# Predeclared gates (lag-1 Soft-Frozen regime allows these labels).
GATES = {
    BASELINE: None,  # ungated
    "M2_C35_GATE_NOT_BULL": frozenset({"Bear", "Crisis", "Sideways"}),
    "M2_C35_GATE_BEAR_CRISIS": frozenset({"Bear", "Crisis"}),
    "M2_C35_GATE_CRISIS_ONLY": frozenset({"Crisis"}),
}


def gate_intensity(intensity: pd.Series, regime: pd.Series, allow: frozenset[str] | None) -> pd.Series:
    """Apply lag-1 regime allow-list to intensity (already lag-1)."""
    if allow is None:
        return intensity.astype(float)
    rg = regime.reindex(intensity.index).fillna("Sideways").astype(str)
    # For Exact T+1 honesty: regime used with intensity should be lag-1 as well.
    rg_lag = rg.shift(1).fillna("Sideways")
    out = intensity.astype(float).copy()
    out[~rg_lag.isin(list(allow))] = 0.0
    return out


def year_mdd(nav: pd.DataFrame, year: int) -> float | None:
    w = nav[(pd.to_datetime(nav["date"]) >= pd.Timestamp(year, 1, 1))
            & (pd.to_datetime(nav["date"]) <= pd.Timestamp(year, 12, 31))]
    if len(w) < 20:
        return None
    path = w["nav"].to_numpy(dtype=float)
    peak = np.maximum.accumulate(path)
    return float(np.min(path / peak - 1.0))


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
    }


def run_book(market_aug, target, regime, dividends, intensity_eff, book_id: str):
    sched = build_m2_sleeve_schedule(target, intensity_eff, CUT, MODE)
    nav, fills, meta = run_early_stack(
        market_aug,
        target,
        regime,
        dividends,
        e45_exposure=None,
        sleeve_weight_schedule=sched,
        def_code=CODE_BIL_FX,
        cost_multiple=1.0,
    )
    return nav, fills, meta, sched


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
    intensity_lag1 = state["s_t"].shift(1).fillna(0.0)
    def_bars = build_def_bars(pd.DatetimeIndex(sorted(market["date"].unique())))
    bil_bars = def_bars[def_bars["code"] == CODE_BIL_FX].copy()
    market_aug = pd.concat([market, bil_bars], ignore_index=True)

    print("BASE sim ...", flush=True)
    nav_b, fills_b, meta_b = run_early_stack(
        market, target, regime, dividends, e45_exposure=None
    )
    nav_b.to_csv(OUT / "outputs/base_daily_nav.csv", index=False)

    books = {}
    for book_id, allow in GATES.items():
        print(f"{book_id} ...", flush=True)
        inten = gate_intensity(intensity_lag1, regime, allow)
        share_on = float((inten > 1e-12).mean()) if len(inten) else 0.0
        nav_c, fills_c, meta_c, sched = run_book(
            market_aug, target, regime, dividends, inten, book_id
        )
        slug = book_id.lower()
        nav_c.to_csv(OUT / "outputs" / f"{slug}_daily_nav.csv", index=False)
        sched.to_csv(OUT / "outputs" / f"{slug}_sleeve_schedule.csv")
        win = {w: window_stats(nav_c, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
        vs = {
            w: deltas_vs_base(window_stats(nav_b, a, b), win[w])
            for w, (a, b) in WINDOWS_STANDARD.items()
        }
        year_help = {}
        for y in STRESS_YEARS:
            mb, mc = year_mdd(nav_b, y), year_mdd(nav_c, y)
            year_help[str(y)] = None if mb is None or mc is None else (abs(mb) - abs(mc)) * 100.0
        non2020 = [year_help[str(y)] for y in (2015, 2018, 2022) if year_help.get(str(y)) is not None]
        n_non2020 = sum(1 for x in non2020 if x is not None and x > HELP_PP)
        n_multi = sum(1 for y in STRESS_YEARS if (year_help.get(str(y)) or 0) > HELP_PP)
        tip = tip_giveback(nav_b, nav_c)
        held = vs["heldout_2019_plus"]
        sealed = vs["sealed_2023_plus"]
        books[book_id] = {
            "allow_regimes": None if allow is None else sorted(allow),
            "share_days_intensity_on": share_on,
            "exact_t1_ok": bool(meta_c.get("exact_t1_ok")),
            "windows_vs_base": vs,
            "year_mdd_help_pp": year_help,
            "non2020_events_gt_025pp": int(n_non2020),
            "multi_events_gt_025pp": int(n_multi),
            "tip": tip,
            "heldout_score": held.get("score"),
            "heldout_mdd_improve_pp": held.get("mdd_improve_pp"),
            "heldout_cagr_giveback_pp": held.get("cagr_giveback_pp"),
            "sealed_score": sealed.get("score"),
            "n_fills": int(len(fills_c)),
        }
        assert meta_c.get("exact_t1_ok"), book_id

    base_row = books[BASELINE]
    ranked = sorted(
        [b for k, b in books.items() if k != BASELINE],
        key=lambda r: (r["heldout_score"] is not None, r["heldout_score"] or -9e9),
        reverse=True,
    )
    # attach ids
    for k, v in books.items():
        v["id"] = k
    ranked = sorted(
        [v for k, v in books.items() if k != BASELINE],
        key=lambda r: r["heldout_score"] if r["heldout_score"] is not None else -9e9,
        reverse=True,
    )

    beat_c35 = [
        r["id"]
        for r in ranked
        if r["heldout_score"] is not None
        and base_row["heldout_score"] is not None
        and r["heldout_score"] > base_row["heldout_score"]
    ]
    tip_improve = [
        r["id"]
        for r in ranked
        if (r["tip"].get("ytd_giveback_pp") is not None)
        and (base_row["tip"].get("ytd_giveback_pp") is not None)
        and r["tip"]["ytd_giveback_pp"] < base_row["tip"]["ytd_giveback_pp"] - 0.5
    ]

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "E45_C35_REGIME_GATE_RESEARCH",
        "ballot": "研究 C35 + 多空閘門",
        "soft_frozen_keep": list(SOFT_FROZEN_FIN_CLIP),
        "default_books_keep": "E22_v2s_tw",
        "stitch": "FORBIDDEN",
        "observe_lock_unchanged": BASELINE,
        "live_wire": False,
        "claim_status": CLAIM_STATUS,
        "cut": CUT,
        "mode": MODE,
        "sensor": "M1 s_{t-1} × Soft-Frozen regime_{t-1} gate",
        "books": books,
        "ranked_vs_c35_heldout": [r["id"] for r in ranked],
        "beat_c35_heldout": beat_c35,
        "tip_ytd_giveback_improved_vs_c35": tip_improve,
        "verdict": {
            "best_heldout": ranked[0]["id"] if ranked else None,
            "baseline_tip_ytd_gate": base_row["tip"]["ytd_gate"],
            "hypothesis_supported": bool(beat_c35 or tip_improve),
        },
    }
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    OPS.joinpath("E45_C35_REGIME_GATE_RESEARCH.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    def fmt(x, nd=2):
        return "n/a" if x is None else f"{x:+.{nd}f}"

    lines = [
        "# E45 C35 + Regime Gate — Research",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Ballot: **研究 C35 + 多空閘門** · Soft-Frozen **KEEP** · stitch **FORBIDDEN** · observe lock **unchanged**",
        f"Claimed MDD narrative: **`{CLAIM_STATUS}`**",
        "",
        "Sensor: M1 `s_{t-1}` · Actuator: `RELOC_BIL_FX` @ **c=0.35** · Gate: Soft-Frozen `regime_{t-1}` allow-list",
        "",
        "## Results vs BASE (and vs ungated C35)",
        "",
        "| Book | allow | days on | held score | MDD↑pp | CAGR giveback | sealed score | YTD gb | YTD gate | 1y gb | 1y gate | non2020>0.25 |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|---:|---|---:|",
    ]
    order = [BASELINE] + [r["id"] for r in ranked]
    for bid in order:
        r = books[bid]
        t = r["tip"]
        lines.append(
            f"| `{bid}` | `{r['allow_regimes']}` | {100*r['share_days_intensity_on']:.1f}% | "
            f"{fmt(r['heldout_score'],3)} | {fmt(r['heldout_mdd_improve_pp'])} | "
            f"{fmt(r['heldout_cagr_giveback_pp'])} | {fmt(r['sealed_score'],3)} | "
            f"{fmt(t['ytd_giveback_pp'])} | **{t['ytd_gate']}** | {fmt(t['trailing_1y_giveback_pp'])} | "
            f"**{t['trailing_1y_gate']}** | {r['non2020_events_gt_025pp']} |"
        )
    lines += [
        "",
        "## Year MDD help pp",
        "",
        "| Book | 2015 | 2018 | 2020 | 2022 |",
        "|---|---:|---:|---:|---:|",
    ]
    for bid in order:
        yh = books[bid]["year_mdd_help_pp"]
        lines.append(
            f"| `{bid}` | {fmt(yh.get('2015'))} | {fmt(yh.get('2018'))} | "
            f"{fmt(yh.get('2020'))} | {fmt(yh.get('2022'))} |"
        )
    lines += [
        "",
        "## Verdict",
        "",
        f"- Beat ungated C35 on held-out score: `{beat_c35 or 'none'}`",
        f"- Tip YTD giveback improved (>0.5pp lower) vs C35: `{tip_improve or 'none'}`",
        f"- Best held-out gated book: `{payload['verdict']['best_heldout']}`",
        "- Observe lock stays **`M2_RELOC_BIL_FX_C35`** until dedicated retarget ACCEPT.",
        "",
        "## Hard non-actions",
        "",
        "- Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN · no live wire · no invent MDD",
        "",
        f"Repro: `{OUT.relative_to(ROOT)}/`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "REPORT.md").write_text(md)
    OPS.joinpath("E45_C35_REGIME_GATE_RESEARCH.md").write_text(md)
    E45.joinpath("E45_C35_REGIME_GATE_RESEARCH.md").write_text(md)
    print(json.dumps({
        "best_heldout": payload["verdict"]["best_heldout"],
        "beat_c35": beat_c35,
        "tip_improve": tip_improve,
        "c35_tip": base_row["tip"],
    }, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
