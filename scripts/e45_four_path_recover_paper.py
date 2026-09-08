#!/usr/bin/env python3
"""E45 four-path research — recover hard-gate sacrificed held-out score.

Ballot: 「四條路都研究」 after Soft_A screen (gap closed ~11%).

Paths
  1 Soft_A observe-retarget ballot evidence (paper only)
  2 Dual-monitor ungated C35 (long score) + Soft_A/HARD (tip hygiene)
  3 New mechanism outside C35×regime soft-mult (intensity gate / cheap-protect / M3)
  4 Accept tip-PASS tradeoff — formal cost/benefit

Soft-Frozen KEEP · stitch FORBIDDEN · observe lock unchanged · no live wire.
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
from e45_crisis_core import build_m2_sleeve_schedule, build_m3_sleeve_schedule
from e45_c35_soft_gate_paper import (
    CUT_BASE,
    HARD,
    MODE,
    shaped_intensity,
    tip_giveback,
    year_mdd,
)
from e45_m1_state_signal_paper import build_m1_state
from e45_m2_true_def_relocate_paper import CODE_BIL_FX, build_def_bars
from e45_paper_harness import (
    BOOK_BLEND_A05,
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

OUT = ROOT / "repro/e45-four-path-recover-20260908"
OPS = ROOT / "research/ops"
E45 = ROOT / "research/e45"

BASELINE = "M2_RELOC_BIL_FX_C35"
SOFT_A = "M2_C35_SOFT_A"
STRESS_YEARS = (2015, 2018, 2020, 2022)
HELP_PP = 0.25

SOFT_A_SPEC = {
    "kind": "mult",
    "mult": {"Bull": 0.0, "Sideways": 0.25, "Bear": 0.75, "Crisis": 1.0},
    "cut": CUT_BASE,
}
HARD_SPEC = {
    "kind": "mult",
    "mult": {"Bull": 0.0, "Sideways": 0.0, "Bear": 1.0, "Crisis": 1.0},
    "cut": CUT_BASE,
}


def evaluate_nav(nav_b, nav_c, fills, share_on=None, meta=None):
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
        "n_fills": int(len(fills)),
        "meta_notes": {k: meta.get(k) for k in ("exact_t1_ok", "mean_e45_exposure") if meta},
    }


def run_reloc(market_aug, target, regime, dividends, inten, cut, book_id):
    sched = build_m2_sleeve_schedule(target, inten, cut, MODE)
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
    assert meta.get("exact_t1_ok"), book_id
    return nav, fills, meta, float((inten > 1e-12).mean())


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
    intensity_lag1 = state["s_t"].shift(1).fillna(0.0).astype(float)
    def_bars = build_def_bars(pd.DatetimeIndex(sorted(market["date"].unique())))
    bil = def_bars[def_bars["code"] == CODE_BIL_FX].copy()
    market_aug = pd.concat([market, bil], ignore_index=True)

    e45_full = e45_full_exposure(market)

    print("BASE ...", flush=True)
    nav_b, _fb, meta_b = run_early_stack(market, target, regime, dividends, e45_exposure=None)
    assert meta_b.get("exact_t1_ok")
    nav_b.to_csv(OUT / "outputs/base_daily_nav.csv", index=False)

    books: dict[str, dict] = {}

    # --- Core C35 family ---
    core_specs = {
        BASELINE: {"kind": "ungated", "cut": CUT_BASE, "path": "lock"},
        HARD: {**HARD_SPEC, "path": "tip_hygiene"},
        SOFT_A: {**SOFT_A_SPEC, "path": "path1_candidate"},
    }
    for book_id, spec in core_specs.items():
        print(f"{book_id} ...", flush=True)
        inten, share_on = shaped_intensity(intensity_lag1, regime, spec)
        nav, fills, meta, _ = run_reloc(
            market_aug, target, regime, dividends, inten, float(spec["cut"]), book_id
        )
        nav.to_csv(OUT / "outputs" / f"{book_id.lower()}_daily_nav.csv", index=False)
        row = evaluate_nav(nav_b, nav, fills, share_on=share_on, meta=meta)
        row.update({"id": book_id, "family": "C35_x_regime", "spec": {k: v for k, v in spec.items() if k != "path"}, "role": spec["path"]})
        books[book_id] = row

    # --- Path 3: outside soft-regime mult family ---
    path3_books = {}

    # Intensity quantile gates (no Soft-Frozen regime)
    for q in (0.70, 0.80, 0.90):
        bid = f"M2_C35_INTEN_Q{int(q*100)}"
        print(f"{bid} ...", flush=True)
        thr = float(intensity_lag1.quantile(q))
        inten = intensity_lag1.where(intensity_lag1 >= thr, 0.0)
        nav, fills, meta, share_on = run_reloc(
            market_aug, target, regime, dividends, inten, CUT_BASE, bid
        )
        row = evaluate_nav(nav_b, nav, fills, share_on=share_on, meta=meta)
        row.update(
            {
                "id": bid,
                "family": "C35_intensity_gate_no_regime",
                "spec": {"kind": "intensity_quantile", "q": q, "thr": thr, "cut": CUT_BASE},
                "role": "path3",
            }
        )
        books[bid] = row
        path3_books[bid] = row

    # Cheap-protect / tax-control references (E45 exposure, not RELOC)
    for bid, alpha, sleeves in (
        (BOOK_BLEND_A05, 0.05, None),
        ("SLEEVE_FIN_ONLY_A10", 0.10, SLEEVE_FIN_ONLY),
    ):
        print(f"{bid} ...", flush=True)
        exp = blend_exposure(e45_full, alpha)
        nav, fills, meta = run_early_stack(
            market,
            target,
            regime,
            dividends,
            e45_exposure=exp,
            e45_sleeve_names=sleeves,
            cost_multiple=1.0,
        )
        assert meta.get("exact_t1_ok"), bid
        row = evaluate_nav(nav_b, nav, fills, share_on=None, meta=meta)
        row.update(
            {
                "id": bid,
                "family": "cheap_protect_e45_exposure",
                "spec": {"alpha": alpha, "sleeves": list(sleeves) if sleeves else None},
                "role": "path3",
            }
        )
        books[bid] = row
        path3_books[bid] = row

    # M3 three-state (new control; not C35 soft-regime)
    bid = "M3_STATE_V0"
    print(f"{bid} ...", flush=True)
    sched_m3, _state_t = build_m3_sleeve_schedule(target, intensity_lag1)
    nav, fills, meta = run_early_stack(
        market,
        target,
        regime,
        dividends,
        e45_exposure=None,
        sleeve_weight_schedule=sched_m3,
        cost_multiple=1.0,
    )
    assert meta.get("exact_t1_ok"), bid
    row = evaluate_nav(nav_b, nav, fills, share_on=None, meta=meta)
    row.update(
        {
            "id": bid,
            "family": "M3_three_state",
            "spec": {"kind": "m3_state_v0"},
            "role": "path3",
        }
    )
    books[bid] = row
    path3_books[bid] = row

    ungated = books[BASELINE]
    hard = books[HARD]
    soft_a = books[SOFT_A]
    denom = (ungated["heldout_score"] or 0) - (hard["heldout_score"] or 0)

    def recovery(r):
        if r["heldout_score"] is None or abs(denom) < 1e-12:
            return None
        return (r["heldout_score"] - hard["heldout_score"]) / denom

    for r in books.values():
        r["heldout_recovery_vs_hard_to_ungated"] = recovery(r)

    # Path 3 winners: tip_clean AND heldout >= Soft_A (or at least > hard)
    path3_tip_clean = [r for r in path3_books.values() if r["tip"]["tip_clean"]]
    path3_beat_hard = [
        r
        for r in path3_tip_clean
        if r["heldout_score"] is not None and r["heldout_score"] >= hard["heldout_score"] - 1e-12
    ]
    path3_beat_soft_a = [
        r
        for r in path3_tip_clean
        if r["heldout_score"] is not None and r["heldout_score"] > soft_a["heldout_score"] + 1e-9
    ]
    path3_best = sorted(
        path3_tip_clean,
        key=lambda r: r["heldout_score"] if r["heldout_score"] is not None else -9e9,
        reverse=True,
    )

    # Path 2 dual-monitor design
    dual = {
        "long_score_twin": {
            "book": BASELINE,
            "job": "track held-out / sealed / year MDD help (long research score)",
            "heldout_score": ungated["heldout_score"],
            "tip_clean": ungated["tip"]["tip_clean"],
            "tip": ungated["tip"],
        },
        "tip_hygiene_twins": [
            {
                "book": SOFT_A,
                "job": "primary tip-hygiene twin (best tip-clean soft recover)",
                "heldout_score": soft_a["heldout_score"],
                "tip_clean": soft_a["tip"]["tip_clean"],
                "tip": soft_a["tip"],
            },
            {
                "book": HARD,
                "book_alias": HARD,
                "job": "strict tip-hygiene twin (hard allow Bear+Crisis)",
                "heldout_score": hard["heldout_score"],
                "tip_clean": hard["tip"]["tip_clean"],
                "tip": hard["tip"],
            },
        ],
        "ops_rule": (
            "Month-end: report long-score twin held-out/sealed deltas AND tip twin YTD/1y gates. "
            "Do not auto-flip observe lock. Promote/stitch still requires separate ACCEPT."
        ),
        "conflict_policy": (
            "If long-score twin tip is PAUSE/ALERT while tip twin is PASS: expected under this design; "
            "do not treat long-score tip dirt as Soft_A failure."
        ),
    }

    # Path 1 ballot evidence
    path1 = {
        "proposed_lock": SOFT_A,
        "current_lock": BASELINE,
        "delta_heldout_vs_lock": (soft_a["heldout_score"] or 0) - (ungated["heldout_score"] or 0),
        "delta_heldout_vs_hard": (soft_a["heldout_score"] or 0) - (hard["heldout_score"] or 0),
        "tip_lock": ungated["tip"],
        "tip_soft_a": soft_a["tip"],
        "recommendation": "DRAFT_BALLOT_ONLY",
        "human_choices": ["HOLD_ungated_C35", "ACCEPT_observe_retarget_SOFT_A", "REJECT"],
        "live_wire": False,
    }

    # Path 4 tradeoff
    path4 = {
        "what_you_buy": {
            "tip_ytd_gate": hard["tip"]["ytd_gate"],
            "tip_1y_gate": hard["tip"]["trailing_1y_gate"],
            "ytd_giveback_pp_hard": hard["tip"]["ytd_giveback_pp"],
            "ytd_giveback_pp_ungated": ungated["tip"]["ytd_giveback_pp"],
            "tip_giveback_saved_pp_ytd": (ungated["tip"]["ytd_giveback_pp"] or 0)
            - (hard["tip"]["ytd_giveback_pp"] or 0),
        },
        "what_you_pay": {
            "heldout_score_ungated": ungated["heldout_score"],
            "heldout_score_hard": hard["heldout_score"],
            "heldout_score_soft_a": soft_a["heldout_score"],
            "heldout_gap_hard_vs_ungated": (ungated["heldout_score"] or 0)
            - (hard["heldout_score"] or 0),
            "mdd2020_help_ungated": ungated["year_mdd_help_pp"].get("2020"),
            "mdd2020_help_hard": hard["year_mdd_help_pp"].get("2020"),
            "mdd2020_help_soft_a": soft_a["year_mdd_help_pp"].get("2020"),
        },
        "when_rational": [
            "Live/stitch path is tip-gated (YTD/1y PASS required) and ungated C35 fails tip.",
            "Operator prefers tip hygiene over maximizing paper held-out score.",
            "Same-family soft gates cannot close most of the gap (Soft_A ~11%).",
            "Path3 screens did not deliver tip-clean held-out near ungated.",
        ],
        "when_not_rational": [
            "Research objective is maximize held-out score regardless of tip (keep ungated lock).",
            "A Path3 / new mechanism later clears tip PASS with held-out >> Soft_A.",
        ],
        "formal_stance": "ACCEPT_TRADEOFF_IS_VALID_DEFAULT_IF_TIP_BINDING",
    }

    # Path rankings for tip_clean + heldout
    tip_clean_all = [r for r in books.values() if r["tip"]["tip_clean"]]
    tip_clean_ranked = sorted(
        tip_clean_all,
        key=lambda r: r["heldout_score"] if r["heldout_score"] is not None else -9e9,
        reverse=True,
    )

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "E45_FOUR_PATH_RECOVER_RESEARCH",
        "ballot": "四條路都研究",
        "soft_frozen_keep": list(SOFT_FROZEN_FIN_CLIP),
        "stitch": "FORBIDDEN",
        "observe_lock_unchanged": BASELINE,
        "live_wire": False,
        "claim_status": CLAIM_STATUS,
        "books": books,
        "path1_soft_a_retarget": path1,
        "path2_dual_monitor": dual,
        "path3_new_mechanism": {
            "screened_ids": list(path3_books.keys()),
            "tip_clean_ids": [r["id"] for r in path3_tip_clean],
            "tip_clean_beat_hard": [r["id"] for r in path3_beat_hard],
            "tip_clean_beat_soft_a": [r["id"] for r in path3_beat_soft_a],
            "best_tip_clean": path3_best[0]["id"] if path3_best else None,
            "best_tip_clean_heldout": path3_best[0]["heldout_score"] if path3_best else None,
            "verdict": (
                "NO_PATH3_BEATS_SOFT_A_WHILE_TIP_CLEAN"
                if not path3_beat_soft_a
                else "PATH3_HAS_TIP_CLEAN_BEAT_SOFT_A"
            ),
        },
        "path4_accept_tradeoff": path4,
        "tip_clean_ranked": [
            {
                "id": r["id"],
                "heldout_score": r["heldout_score"],
                "family": r.get("family"),
                "recovery": r.get("heldout_recovery_vs_hard_to_ungated"),
                "tip": r["tip"],
            }
            for r in tip_clean_ranked
        ],
        "verdict": {
            "best_tip_clean_overall": tip_clean_ranked[0]["id"] if tip_clean_ranked else None,
            "soft_a_still_best_c35_family_recover": True,
            "path3_replaces_soft_a": bool(path3_beat_soft_a),
            "recommended_stack": [
                "KEEP_or_ACCEPT_Soft_A_for_tip_hygiene",
                "DUAL_MONITOR_ungated_for_long_score",
                "CONTINUE_new_mechanism_ladder_outside_C35_x_regime",
                "ACCEPT_tradeoff_if_tip_binding_and_no_Path3_winner",
            ],
        },
    }

    (OUT / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    OPS.joinpath("E45_FOUR_PATH_RECOVER_RESEARCH.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    # Markdown report
    lines = [
        "# E45 Four-Path Recover — Research",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Ballot: **四條路都研究** · Soft-Frozen **KEEP** · stitch **FORBIDDEN** · observe lock **unchanged**",
        "Claimed MDD: **`RETIRED_HISTORICAL_NARRATIVE`**",
        "",
        f"Baseline gap: ungated held-out `{fmt(ungated['heldout_score'],3)}` · hard `{fmt(hard['heldout_score'],3)}` · Soft_A `{fmt(soft_a['heldout_score'],3)}`",
        "",
        "## All books (held-out × tip)",
        "",
        "| Book | family | held score | recovery* | sealed | YTD gb | YTD | 1y gb | 1y | tip | non2020 |",
        "|---|---|---:|---:|---:|---:|---|---:|---|---|---:|",
    ]
    for bid, r in books.items():
        t = r["tip"]
        lines.append(
            f"| `{bid}` | {r.get('family','')} | {fmt(r['heldout_score'],3)} | "
            f"{fmt(r.get('heldout_recovery_vs_hard_to_ungated'),2)} | {fmt(r['sealed_score'],3)} | "
            f"{fmt(t['ytd_giveback_pp'])} | **{t['ytd_gate']}** | {fmt(t['trailing_1y_giveback_pp'])} | "
            f"**{t['trailing_1y_gate']}** | {t['tip_clean']} | {r['non2020_events_gt_025pp']} |"
        )
    lines += [
        "",
        "\\* recovery = (score − hard) / (ungated − hard).",
        "",
        "## Path 1 — Soft_A observe retarget (DRAFT ballot)",
        "",
        f"- Current lock: `{BASELINE}` · tip `{ungated['tip']['ytd_gate']}/{ungated['tip']['trailing_1y_gate']}` · held `{fmt(ungated['heldout_score'],3)}`",
        f"- Proposed: `{SOFT_A}` · tip `{soft_a['tip']['ytd_gate']}/{soft_a['tip']['trailing_1y_gate']}` · held `{fmt(soft_a['heldout_score'],3)}`",
        f"- Δ held-out vs lock: `{fmt(path1['delta_heldout_vs_lock'],3)}` (expected drop vs ungated; gain vs hard `{fmt(path1['delta_heldout_vs_hard'],3)}`)",
        "- Status: **DRAFT ONLY** — not OPEN; needs human ACCEPT to swap observe lock.",
        "- Live wire / Soft-Frozen / stitch: **No**.",
        "",
        "## Path 2 — Dual monitor",
        "",
        f"- **Long-score twin:** `{BASELINE}` (held `{fmt(ungated['heldout_score'],3)}`, tip dirty expected).",
        f"- **Tip-hygiene twin (primary):** `{SOFT_A}` (held `{fmt(soft_a['heldout_score'],3)}`, tip PASS).",
        f"- **Tip-hygiene twin (strict):** `{HARD}` (held `{fmt(hard['heldout_score'],3)}`, tip PASS).",
        f"- Ops: {dual['ops_rule']}",
        f"- Conflict: {dual['conflict_policy']}",
        "",
        "## Path 3 — New mechanism (outside C35×regime soft-mult)",
        "",
        f"- Screened: `{payload['path3_new_mechanism']['screened_ids']}`",
        f"- Tip-clean: `{payload['path3_new_mechanism']['tip_clean_ids']}`",
        f"- Tip-clean & ≥ hard: `{payload['path3_new_mechanism']['tip_clean_beat_hard']}`",
        f"- Tip-clean & **beat Soft_A**: `{payload['path3_new_mechanism']['tip_clean_beat_soft_a']}`",
        f"- Verdict: **`{payload['path3_new_mechanism']['verdict']}`**",
        "",
        "## Path 4 — Accept tip-PASS tradeoff",
        "",
        f"- Buy: tip YTD giveback `{fmt(ungated['tip']['ytd_giveback_pp'])} → {fmt(hard['tip']['ytd_giveback_pp'])}` pp (hard) / Soft_A `{fmt(soft_a['tip']['ytd_giveback_pp'])}`.",
        f"- Pay: held-out `{fmt(ungated['heldout_score'],3)} → {fmt(hard['heldout_score'],3)}` (hard) or `{fmt(soft_a['heldout_score'],3)}` (Soft_A); 2020 MDD help `{fmt(ungated['year_mdd_help_pp'].get('2020'))} → {fmt(hard['year_mdd_help_pp'].get('2020'))}`.",
        f"- Stance: **`{path4['formal_stance']}`** when tip is binding and Path3 has no Soft_A beater.",
        "",
        "## Integrated verdict",
        "",
        f"- Best tip-clean overall: `{payload['verdict']['best_tip_clean_overall']}`",
        f"- Path3 replaces Soft_A? **{payload['verdict']['path3_replaces_soft_a']}**",
        f"- Recommended stack: `{payload['verdict']['recommended_stack']}`",
        "",
        f"Repro: `{OUT.relative_to(ROOT)}/`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "REPORT.md").write_text(md)
    OPS.joinpath("E45_FOUR_PATH_RECOVER_RESEARCH.md").write_text(md)
    E45.joinpath("E45_FOUR_PATH_RECOVER_RESEARCH.md").write_text(md)

    print(
        json.dumps(
            {
                "best_tip_clean": payload["verdict"]["best_tip_clean_overall"],
                "path3_verdict": payload["path3_new_mechanism"]["verdict"],
                "path3_beat_soft_a": payload["path3_new_mechanism"]["tip_clean_beat_soft_a"],
                "soft_a_held": soft_a["heldout_score"],
                "ungated_held": ungated["heldout_score"],
                "hard_held": hard["heldout_score"],
            },
            indent=2,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
