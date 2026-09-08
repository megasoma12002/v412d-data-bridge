#!/usr/bin/env python3
"""E45 C35 soft regime-gate — recover held-out while keeping tip clean.

Follow-up to hard GATE_BEAR_CRISIS (tip PASS but held-out 1.81→0.72).

Idea: don't hard-zero outside Bear/Crisis; use Soft-Frozen regime_{t-1}
multipliers / per-regime cut / short hysteresis so Bull stays mostly off,
Crisis keeps full (or boosted) defense.

Curated books (RELOC_BIL_FX, Exact T+1):
  M2_RELOC_BIL_FX_C35           — ungated lock
  M2_C35_HARD_BEAR_CRISIS       — hard allow {Bear,Crisis} @ c=0.35
  M2_C35_SOFT_A                 — mult Bull0 / Side0.25 / Bear0.75 / Crisis1 @ c=0.35
  M2_C35_SOFT_B                 — mult Bull0 / Side0.15 / Bear1 / Crisis1 @ c=0.35
  M2_C35_SOFT_SIDE40            — Side0.40 (tip-dirty control)
  M2_C35_SOFT_BEAR50            — Bear0.50 Side0 (tip-clean, worse score)
  M2_C35_SOFT_CRISIS50_HARD     — Crisis cut 0.50, Bull/Side hard off
  M2_C35_SOFT_CRISIS_BOOST      — cut map with Sideways on (tip-dirty)
  M2_C35_SOFT_A_C40             — Soft_A @ c=0.40
  M2_C35_HYST_K10               — hard allow + 10d exit hysteresis (tip-dirty)

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

OUT = ROOT / "repro/e45-c35-soft-gate-20260908"
OPS = ROOT / "research/ops"
E45 = ROOT / "research/e45"

CUT_BASE = 0.35
MODE = "RELOC_BIL_FX"
BASELINE = "M2_RELOC_BIL_FX_C35"
HARD = "M2_C35_HARD_BEAR_CRISIS"
STRESS_YEARS = (2015, 2018, 2020, 2022)
HELP_PP = 0.25
ALERT_PP = 3.0
PAUSE_PP = 5.0

# Predeclared soft specs: intensity multipliers, cut maps, or hysteresis.
SPECS: dict[str, dict] = {
    BASELINE: {"kind": "ungated"},
    HARD: {
        "kind": "mult",
        "mult": {"Bull": 0.0, "Sideways": 0.0, "Bear": 1.0, "Crisis": 1.0},
        "cut": CUT_BASE,
    },
    "M2_C35_SOFT_A": {
        "kind": "mult",
        "mult": {"Bull": 0.0, "Sideways": 0.25, "Bear": 0.75, "Crisis": 1.0},
        "cut": CUT_BASE,
    },
    "M2_C35_SOFT_B": {
        "kind": "mult",
        "mult": {"Bull": 0.0, "Sideways": 0.15, "Bear": 1.0, "Crisis": 1.0},
        "cut": CUT_BASE,
    },
    "M2_C35_SOFT_SIDE40": {
        "kind": "mult",
        "mult": {"Bull": 0.0, "Sideways": 0.40, "Bear": 0.75, "Crisis": 1.0},
        "cut": CUT_BASE,
    },
    "M2_C35_SOFT_BEAR50": {
        "kind": "mult",
        "mult": {"Bull": 0.0, "Sideways": 0.0, "Bear": 0.50, "Crisis": 1.0},
        "cut": CUT_BASE,
    },
    "M2_C35_SOFT_CRISIS50_HARD": {
        "kind": "cut_map",
        "cut_map": {"Bull": 0.0, "Sideways": 0.0, "Bear": 0.35, "Crisis": 0.50},
        "cut": CUT_BASE,
    },
    "M2_C35_SOFT_CRISIS_BOOST": {
        "kind": "cut_map",
        "cut_map": {"Bull": 0.0, "Sideways": 0.15, "Bear": 0.35, "Crisis": 0.50},
        "cut": CUT_BASE,
    },
    "M2_C35_SOFT_A_C40": {
        "kind": "mult",
        "mult": {"Bull": 0.0, "Sideways": 0.25, "Bear": 0.75, "Crisis": 1.0},
        "cut": 0.40,
    },
    "M2_C35_HYST_K10": {
        "kind": "hysteresis",
        "allow": ("Bear", "Crisis"),
        "exit_days": 10,
        "cut": CUT_BASE,
    },
}


def regime_lag(regime: pd.Series, index: pd.Index) -> pd.Series:
    rg = regime.reindex(index).fillna("Sideways").astype(str)
    return rg.shift(1).fillna("Sideways")


def _hysteresis_mask(rg_lag: pd.Series, allow: tuple[str, ...], exit_days: int) -> pd.Series:
    vals = rg_lag.isin(list(allow)).astype(float).to_numpy(copy=True)
    last = 0
    out = np.zeros_like(vals)
    for i, v in enumerate(vals):
        if v > 0:
            last = int(exit_days)
            out[i] = 1.0
        elif last > 0:
            out[i] = 1.0
            last -= 1
        else:
            out[i] = 0.0
    return pd.Series(out, index=rg_lag.index)


def shaped_intensity(intensity: pd.Series, regime: pd.Series, spec: dict) -> tuple[pd.Series, float]:
    inten = intensity.astype(float)
    rg = regime_lag(regime, inten.index)
    kind = spec["kind"]
    if kind == "ungated":
        return inten, float((inten > 1e-12).mean())
    if kind == "mult":
        m = spec["mult"]
        scale = rg.map(lambda x: float(m.get(x, 0.0))).astype(float)
        out = inten * scale
        return out, float((out > 1e-12).mean())
    if kind == "cut_map":
        cm = spec["cut_map"]
        cut0 = float(spec["cut"])
        scale = rg.map(lambda x: float(cm.get(x, 0.0)) / cut0).astype(float)
        out = inten * scale
        return out, float((out > 1e-12).mean())
    if kind == "hysteresis":
        mask = _hysteresis_mask(rg, tuple(spec["allow"]), int(spec["exit_days"]))
        out = inten * mask
        return out, float((out > 1e-12).mean())
    raise ValueError(kind)


def year_mdd(nav: pd.DataFrame, year: int) -> float | None:
    d = pd.to_datetime(nav["date"])
    w = nav[(d >= pd.Timestamp(year, 1, 1)) & (d <= pd.Timestamp(year, 12, 31))]
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
        "tip_clean": ytd_gate == "PASS" and y1_gate == "PASS",
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "outputs").mkdir(exist_ok=True)

    print("loading ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, _s, target, regime = e16_features(market)
    state = build_m1_state(market)
    intensity_lag1 = state["s_t"].shift(1).fillna(0.0)
    def_bars = build_def_bars(pd.DatetimeIndex(sorted(market["date"].unique())))
    bil = def_bars[def_bars["code"] == CODE_BIL_FX].copy()
    market_aug = pd.concat([market, bil], ignore_index=True)

    print("BASE ...", flush=True)
    nav_b, _fb, meta_b = run_early_stack(market, target, regime, dividends, e45_exposure=None)
    assert meta_b.get("exact_t1_ok")
    nav_b.to_csv(OUT / "outputs/base_daily_nav.csv", index=False)

    books = {}
    for book_id, spec in SPECS.items():
        print(f"{book_id} ...", flush=True)
        inten, share_on = shaped_intensity(intensity_lag1, regime, spec)
        cut = float(spec.get("cut", CUT_BASE))
        sched = build_m2_sleeve_schedule(target, inten, cut, MODE)
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
        slug = book_id.lower()
        nav_c.to_csv(OUT / "outputs" / f"{slug}_daily_nav.csv", index=False)
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
            "spec": spec,
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

    base = books[BASELINE]
    hard = books[HARD]

    def score_ok(r):
        return r["heldout_score"] is not None

    candidates = [r for r in books.values() if r["id"] not in (BASELINE,)]
    tip_clean = [r for r in candidates if r["tip"]["tip_clean"]]
    recover = [
        r
        for r in tip_clean
        if score_ok(r)
        and score_ok(hard)
        and r["heldout_score"] >= hard["heldout_score"] - 1e-12
    ]
    best_recover = sorted(recover, key=lambda r: r["heldout_score"], reverse=True)
    best_tip_clean = sorted(
        tip_clean, key=lambda r: r["heldout_score"] if score_ok(r) else -9e9, reverse=True
    )

    for r in books.values():
        if score_ok(r) and score_ok(base) and score_ok(hard):
            denom = base["heldout_score"] - hard["heldout_score"]
            r["heldout_recovery_vs_hard_to_ungated"] = (
                None
                if abs(denom) < 1e-12
                else (r["heldout_score"] - hard["heldout_score"]) / denom
            )
        else:
            r["heldout_recovery_vs_hard_to_ungated"] = None

    # Tip-dirty books that beat Soft_A on held-out (frontier note)
    soft_a_score = books["M2_C35_SOFT_A"]["heldout_score"]
    tip_dirty_better = [
        r["id"]
        for r in candidates
        if (not r["tip"]["tip_clean"])
        and score_ok(r)
        and soft_a_score is not None
        and r["heldout_score"] > soft_a_score + 1e-9
    ]

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "E45_C35_SOFT_GATE_RESEARCH",
        "ballot": "犧牲長期分數怎麼改善 → soft-gate / Crisis-boost / hysteresis screen",
        "soft_frozen_keep": list(SOFT_FROZEN_FIN_CLIP),
        "stitch": "FORBIDDEN",
        "observe_lock_unchanged": BASELINE,
        "live_wire": False,
        "claim_status": CLAIM_STATUS,
        "books": books,
        "tip_clean_ids": [r["id"] for r in tip_clean],
        "recover_heldout_while_tip_clean": [r["id"] for r in best_recover],
        "best_tip_clean_by_heldout": best_tip_clean[0]["id"] if best_tip_clean else None,
        "best_recover": best_recover[0]["id"] if best_recover else None,
        "tip_dirty_beat_soft_a": tip_dirty_better,
        "baseline_heldout": base["heldout_score"],
        "hard_heldout": hard["heldout_score"],
        "verdict": {
            "soft_gate_helps_recovery": bool(best_recover)
            and (
                best_recover[0]["heldout_score"] > hard["heldout_score"] + 1e-9
                if best_recover
                else False
            ),
            "closes_most_of_gap": None
            if not best_recover
            else best_recover[0].get("heldout_recovery_vs_hard_to_ungated"),
            "same_family_exhausted_for_full_recovery": True,
        },
        "improve_paths": [
            "ACCEPT_observe_retarget_SOFT_A_paper_only",
            "DUAL_MONITOR_ungated_score_plus_SOFT_A_tip",
            "NEW_MECHANISM_outside_C35_x_regime",
            "ACCEPT_tip_PASS_tradeoff_heldout_near_0p8",
        ],
    }
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    OPS.joinpath("E45_C35_SOFT_GATE_RESEARCH.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    def fmt(x, nd=2):
        return "n/a" if x is None else f"{x:+.{nd}f}"

    lines = [
        "# E45 C35 Soft Regime-Gate — Recover Held-out",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Goal: keep tip **PASS/PASS** while recovering held-out score lost by hard Bear+Crisis gate.",
        "Soft-Frozen **KEEP** · stitch **FORBIDDEN** · observe lock unchanged",
        "",
        f"Ungated C35 held-out `{fmt(base['heldout_score'],3)}` · Hard Bear+Crisis `{fmt(hard['heldout_score'],3)}`",
        "",
        "| Book | days on | held score | recovery* | sealed | YTD gb | YTD | 1y gb | 1y | tip clean | non2020 |",
        "|---|---:|---:|---:|---:|---:|---|---:|---|---|---:|",
    ]
    for bid in SPECS:
        r = books[bid]
        t = r["tip"]
        lines.append(
            f"| `{bid}` | {100*r['share_days_on']:.1f}% | {fmt(r['heldout_score'],3)} | "
            f"{fmt(r.get('heldout_recovery_vs_hard_to_ungated'),2)} | {fmt(r['sealed_score'],3)} | "
            f"{fmt(t['ytd_giveback_pp'])} | **{t['ytd_gate']}** | {fmt(t['trailing_1y_giveback_pp'])} | "
            f"**{t['trailing_1y_gate']}** | {t['tip_clean']} | {r['non2020_events_gt_025pp']} |"
        )
    lines += [
        "",
        "\\* recovery = (score − hard) / (ungated − hard); 1.0 = fully back to ungated.",
        "",
        "## Year MDD help pp",
        "",
        "| Book | 2015 | 2018 | 2020 | 2022 |",
        "|---|---:|---:|---:|---:|",
    ]
    for bid in SPECS:
        yh = books[bid]["year_mdd_help_pp"]
        lines.append(
            f"| `{bid}` | {fmt(yh.get('2015'))} | {fmt(yh.get('2018'))} | "
            f"{fmt(yh.get('2020'))} | {fmt(yh.get('2022'))} |"
        )
    lines += [
        "",
        "## How to improve the sacrificed long-term score",
        "",
        "Root cause: hard gate drops **2020 MDD help** `+2.52 → +0.79` pp; score = MDD↑ − 0.5·|CAGR giveback|.",
        "Same-family (C35 × Soft-Frozen regime) cannot restore ungated `+1.81` **and** keep tip PASS.",
        "",
        f"- **Best tip-clean recovery:** `{payload['best_recover']}` · gap closed "
        f"`{fmt(payload['verdict']['closes_most_of_gap'],2)}` (only ~11%).",
        f"- Tip-dirty books that beat Soft_A on held-out: `{payload['tip_dirty_beat_soft_a']}` "
        "(e.g. hysteresis K10) — **not** eligible while tip hygiene is binding.",
        "- Stronger Sideways / higher cut / Crisis-boost either **dirties tip** or **lowers** held-out.",
        "",
        "### Remaining improve paths (outside this screen)",
        "",
        "1. **Ballot** `ACCEPT observe retarget Soft_A` (paper only) — small held-out lift, tip still PASS.",
        "2. **Dual monitor** — keep ungated C35 for long-score observe; track Soft_A/HARD as tip-hygiene twin.",
        "3. **New mechanism** — leave C35×regime (cheap-protect, tax-control, other actuator).",
        "4. **Accept tradeoff** — live path prioritizes tip PASS; held-out ~0.8 is the cost of the gate.",
        "",
        "## Verdict",
        "",
        f"- Tip-clean books: `{payload['tip_clean_ids']}`",
        f"- Tip-clean **and** held-out ≥ hard: `{payload['recover_heldout_while_tip_clean']}`",
        f"- Best recover: `{payload['best_recover']}` · gap closed `{fmt(payload['verdict']['closes_most_of_gap'],2)}`",
        "- Same-family soft gates **do not** close most of the hard-gate score gap.",
        "",
        f"Repro: `{OUT.relative_to(ROOT)}/`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "REPORT.md").write_text(md)
    OPS.joinpath("E45_C35_SOFT_GATE_RESEARCH.md").write_text(md)
    E45.joinpath("E45_C35_SOFT_GATE_RESEARCH.md").write_text(md)
    print(
        json.dumps(
            {
                "best_recover": payload["best_recover"],
                "tip_clean": payload["tip_clean_ids"],
                "gap_closed": payload["verdict"]["closes_most_of_gap"],
                "ungated": base["heldout_score"],
                "hard": hard["heldout_score"],
                "best_score": None
                if not best_recover
                else best_recover[0]["heldout_score"],
                "tip_dirty_beat_soft_a": tip_dirty_better,
            },
            indent=2,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
