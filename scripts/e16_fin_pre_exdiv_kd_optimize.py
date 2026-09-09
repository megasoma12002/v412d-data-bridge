#!/usr/bin/env python3
"""Optimize FIN_PRE_EXDIV_KD sleeve params via Exact T+1 paper NAV (RESEARCH ONLY).

Grid: season window × Yahoo K9 thresh × pre-ex skip days.
Objective (in order):
  1) tip-clean (YTD+1y PASS) AND held-out score > 0  → coexist
  2) else no PAUSE (PASS/ALERT only) maximizing held-out score
  3) else max held-out score

Anchors: FIN_EQUAL · FIN_RS_SOFT_TILT_EXDIV · MIX_L75
Soft-Frozen KEEP · live wire false.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e16_soft_frozen_base as soft
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, load_market, window_stats
from e50_early_stack_combined_nav import FIN, e16_features, simulate_core
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp
from tw_share_lots import BOARD_LOT
from within_sleeve_alloc import (
    FIN_EQUAL,
    FIN_MIX_EQUAL_RS_EXDIV,
    FIN_PRE_EXDIV_KD,
    FIN_RS_SOFT_TILT_EXDIV,
    TEL_EQUAL,
    build_exdiv_buy_ok,
    build_kd_season_tilt_scores,
    build_name_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/fin-pre-exdiv-kd-optimize-20260909"
RESEARCH = ROOT / "research/ops"

CAPITAL = 500_000_000.0
LOT = BOARD_LOT
TRAIL_ALERT_PP = 3.0
TRAIL_PAUSE_PP = 5.0

SEASONS = [
    ("APR", (4, 1), (4, 30)),
    ("APR15_MAY15", (4, 15), (5, 15)),
    ("APR15_MAY31", (4, 15), (5, 31)),
    ("MAY", (5, 1), (5, 31)),
    ("MAY15_JUN10", (5, 15), (6, 10)),  # human default
    ("APR_MAY", (4, 1), (5, 31)),
]
K_THRESH = (20.0, 25.0, 30.0)
PRE_DAYS = (5, 10, 15)
ACTIVE_SCORE = 1.5


def tip_gate(base_nav: pd.DataFrame, chal_nav: pd.DataFrame, asof: pd.Timestamp) -> dict:
    out = {}
    asof = pd.Timestamp(asof)
    b_dates = pd.to_datetime(base_nav["date"])
    c_dates = pd.to_datetime(chal_nav["date"])
    for wname, start in (
        ("ytd", pd.Timestamp(asof.year, 1, 1)),
        ("trailing_1y", asof - pd.Timedelta(days=365)),
    ):
        b = base_nav[(b_dates >= start) & (b_dates <= asof)].reset_index(drop=True)
        c = chal_nav[(c_dates >= start) & (c_dates <= asof)].reset_index(drop=True)
        if len(b) < 20 or len(c) < 20:
            out[wname] = {"giveback_pp": None, "gate": "INSUFFICIENT"}
            continue
        bn = b["nav"] / float(b["nav"].iloc[0])
        cn = c["nav"] / float(c["nav"].iloc[0])
        years = (len(b) - 1) / 252.0
        bc = float(bn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        cc = float(cn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        gb = None if bc is None or cc is None else (bc - cc) * 100
        gate = "PASS"
        if gb is not None and gb > TRAIL_PAUSE_PP:
            gate = "PAUSE_REVIEW"
        elif gb is not None and gb > TRAIL_ALERT_PP:
            gate = "ALERT"
        out[wname] = {
            "giveback_pp": None if gb is None else float(gb),
            "gate": gate,
            "rel_nav": float(cn.iloc[-1] / bn.iloc[-1]),
        }
    return out


def score_vs_base(base_stats: dict, chal_stats: dict) -> dict:
    mdd_pp = mdd_delta_pp(base_stats.get("max_drawdown"), chal_stats.get("max_drawdown"))
    cagr_pp = cagr_delta_pp(
        base_stats.get("cagr"), chal_stats.get("cagr"), missing_as_zero=True
    )
    giveback = abs(float(cagr_pp)) if cagr_pp is not None else 9.0
    return {
        "mdd_improve_pp": float(mdd_pp),
        "cagr_giveback_pp": float(cagr_pp) if cagr_pp is not None else None,
        "score": float(mdd_pp) - 0.5 * giveback,
    }


def sim(market, target, regime, dividends, *, policy, scores=None, buy_ok=None, mix=None):
    return simulate_core(
        market,
        target,
        regime,
        dividends,
        apply_e22=True,
        apply_stock_div=True,
        capital=CAPITAL,
        lot_size=LOT,
        financial_alloc=policy,
        telecom_alloc=TEL_EQUAL,
        fin_name_scores=scores,
        fin_buy_ok=buy_ok,
        fin_mix_lambda=mix,
    )


def rank_key(row: dict) -> tuple:
    tip = row["tip_gates"]
    ytd, t1 = tip["ytd"]["gate"], tip["trailing_1y"]["gate"]
    tip_clean = ytd == "PASS" and t1 == "PASS"
    no_pause = ytd != "PAUSE_REVIEW" and t1 != "PAUSE_REVIEW" and ytd != "INSUFFICIENT"
    held = row["heldout"]["score"]
    coexist = tip_clean and held > 0
    # higher better: coexist, no_pause, held
    return (1 if coexist else 0, 1 if no_pause else 0, held)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "outputs").mkdir(exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.5, 0.95]

    print("loading ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, _s, target, regime = e16_features(market)
    cal = pd.to_datetime(market["date"]).drop_duplicates().sort_values()

    print("BASE FIN_EQUAL ...", flush=True)
    nav_b, fills_b, meta_b = sim(market, target, regime, dividends, policy=FIN_EQUAL)
    assert meta_b.get("exact_t1_ok")
    win_b = {w: window_stats(nav_b, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
    asof = pd.to_datetime(nav_b["date"]).max()
    nav_b.to_csv(OUT / "outputs" / "base_fin_equal_daily_nav.csv", index=False)

    # anchors
    print("anchors RS + MIX_L75 ...", flush=True)
    rs_scores = build_name_scores(market, FIN)
    rs_ok = build_exdiv_buy_ok(cal, dividends, FIN, also_stock_ex=True)
    rows: list[dict] = []
    for label, policy, scores, ok, mix in (
        ("FIN_RS_SOFT_TILT_EXDIV", FIN_RS_SOFT_TILT_EXDIV, rs_scores, rs_ok, None),
        ("MIX_L75", FIN_MIX_EQUAL_RS_EXDIV, rs_scores, rs_ok, 0.75),
    ):
        nav, fills, meta = sim(
            market, target, regime, dividends, policy=policy, scores=scores, buy_ok=ok, mix=mix
        )
        assert meta.get("exact_t1_ok")
        win = {w: window_stats(nav, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
        tip = tip_gate(nav_b, nav, asof)
        held = score_vs_base(win_b["heldout_2019_plus"], win["heldout_2019_plus"])
        sealed = score_vs_base(win_b["sealed_2023_plus"], win["sealed_2023_plus"])
        rows.append(
            {
                "id": label,
                "family": "anchor",
                "season": None,
                "k_thresh": None,
                "pre_days": None,
                "heldout": held,
                "sealed_REPORT_ONLY": sealed,
                "tip_gates": tip,
                "tip_clean": tip["ytd"]["gate"] == "PASS" and tip["trailing_1y"]["gate"] == "PASS",
                "n_fills": int(len(fills)),
            }
        )

    # skip-only controls (no KD tilt)
    print("skip-only controls ...", flush=True)
    for pre in PRE_DAYS:
        ok = build_pre_exdiv_window_buy_ok(cal, dividends, FIN, pre_days=pre, also_stock_ex=True)
        # zero scores → soft-tilt equals equal among buy_ok
        scores = pd.DataFrame(0.0, index=ok.index, columns=list(FIN))
        nav, fills, meta = sim(
            market,
            target,
            regime,
            dividends,
            policy=FIN_PRE_EXDIV_KD,
            scores=scores,
            buy_ok=ok,
        )
        assert meta.get("exact_t1_ok")
        win = {w: window_stats(nav, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
        tip = tip_gate(nav_b, nav, asof)
        held = score_vs_base(win_b["heldout_2019_plus"], win["heldout_2019_plus"])
        sealed = score_vs_base(win_b["sealed_2023_plus"], win["sealed_2023_plus"])
        rows.append(
            {
                "id": f"SKIP_ONLY_T{pre}",
                "family": "skip_only",
                "season": None,
                "k_thresh": None,
                "pre_days": pre,
                "heldout": held,
                "sealed_REPORT_ONLY": sealed,
                "tip_gates": tip,
                "tip_clean": tip["ytd"]["gate"] == "PASS" and tip["trailing_1y"]["gate"] == "PASS",
                "n_fills": int(len(fills)),
            }
        )

    grid = [(s, k, p) for s in SEASONS for k in K_THRESH for p in PRE_DAYS]
    print(f"KD grid sims: {len(grid)} ...", flush=True)
    for i, ((sname, s0, s1), kthr, pre) in enumerate(grid, 1):
        print(f"  [{i}/{len(grid)}] {sname} K<{kthr:g} T-{pre} ...", flush=True)
        scores = build_kd_season_tilt_scores(
            market,
            dividends,
            FIN,
            k_thresh=kthr,
            season_start=s0,
            season_end=s1,
            pre_days=pre,
            active_score=ACTIVE_SCORE,
        )
        ok = build_pre_exdiv_window_buy_ok(
            cal, dividends, FIN, pre_days=pre, also_stock_ex=True
        )
        nav, fills, meta = sim(
            market,
            target,
            regime,
            dividends,
            policy=FIN_PRE_EXDIV_KD,
            scores=scores,
            buy_ok=ok,
        )
        assert meta.get("exact_t1_ok"), (sname, kthr, pre)
        win = {w: window_stats(nav, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
        tip = tip_gate(nav_b, nav, asof)
        held = score_vs_base(win_b["heldout_2019_plus"], win["heldout_2019_plus"])
        sealed = score_vs_base(win_b["sealed_2023_plus"], win["sealed_2023_plus"])
        rid = f"KD_{sname}_Klt{kthr:g}_T{pre}"
        rows.append(
            {
                "id": rid,
                "family": "kd_season",
                "season": sname,
                "season_start": list(s0),
                "season_end": list(s1),
                "k_thresh": kthr,
                "pre_days": pre,
                "active_score": ACTIVE_SCORE,
                "heldout": held,
                "sealed_REPORT_ONLY": sealed,
                "tip_gates": tip,
                "tip_clean": tip["ytd"]["gate"] == "PASS" and tip["trailing_1y"]["gate"] == "PASS",
                "n_fills": int(len(fills)),
                "kd_active_days": {c: int((scores[c] > 0).sum()) for c in FIN},
            }
        )

    ranked = sorted(rows, key=rank_key, reverse=True)
    coexist = [r for r in ranked if r["tip_clean"] and r["heldout"]["score"] > 0]
    no_pause = [
        r
        for r in ranked
        if r["tip_gates"]["ytd"]["gate"] != "PAUSE_REVIEW"
        and r["tip_gates"]["trailing_1y"]["gate"] != "PAUSE_REVIEW"
        and r["heldout"]["score"] > 0
    ]
    best_coexist = coexist[0] if coexist else None
    best_no_pause = no_pause[0] if no_pause else None
    best_held = max(ranked, key=lambda r: r["heldout"]["score"])

    # declare optimal: prefer coexist, else best no-pause, else best held
    if best_coexist:
        optimal = best_coexist
        optimal_rule = "coexist (tip PASS + heldout>0)"
    elif best_no_pause:
        optimal = best_no_pause
        optimal_rule = "no tip PAUSE + max heldout"
    else:
        optimal = best_held
        optimal_rule = "max heldout (tip PAUSE tolerated)"

    # re-sim optimal for nav artifact
    print(f"saving optimal {optimal['id']} ...", flush=True)
    if optimal["family"] == "kd_season":
        scores = build_kd_season_tilt_scores(
            market,
            dividends,
            FIN,
            k_thresh=float(optimal["k_thresh"]),
            season_start=tuple(optimal["season_start"]),
            season_end=tuple(optimal["season_end"]),
            pre_days=int(optimal["pre_days"]),
            active_score=ACTIVE_SCORE,
        )
        ok = build_pre_exdiv_window_buy_ok(
            cal, dividends, FIN, pre_days=int(optimal["pre_days"]), also_stock_ex=True
        )
        nav_o, _, _ = sim(
            market, target, regime, dividends, policy=FIN_PRE_EXDIV_KD, scores=scores, buy_ok=ok
        )
    elif optimal["family"] == "skip_only":
        ok = build_pre_exdiv_window_buy_ok(
            cal, dividends, FIN, pre_days=int(optimal["pre_days"]), also_stock_ex=True
        )
        scores = pd.DataFrame(0.0, index=ok.index, columns=list(FIN))
        nav_o, _, _ = sim(
            market, target, regime, dividends, policy=FIN_PRE_EXDIV_KD, scores=scores, buy_ok=ok
        )
    else:
        nav_o = None
    if nav_o is not None:
        nav_o.to_csv(OUT / "outputs" / f"optimal_{optimal['id'].lower()}_daily_nav.csv", index=False)
        jb = nav_b[["date", "nav"]].rename(columns={"nav": "nav_base"})
        jc = nav_o[["date", "nav"]].rename(columns={"nav": "nav_optimal"})
        jb.merge(jc, on="date", how="inner").to_csv(
            OUT / "outputs" / "nav_compare_optimal.csv", index=False
        )

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "FIN_PRE_EXDIV_KD_OPTIMIZE",
        "status": "OPTIMAL_SELECTED",
        "live_wire": False,
        "soft_frozen_keep": True,
        "objective_order": [
            "coexist: tip YTD+1y PASS and heldout score>0",
            "else: no tip PAUSE, max heldout",
            "else: max heldout",
        ],
        "optimal_selection_rule": optimal_rule,
        "optimal": optimal,
        "best_coexist": best_coexist,
        "best_no_pause": best_no_pause,
        "best_heldout": best_held,
        "n_grid": len(grid),
        "ranked": ranked,
        "verdict": (
            f"Optimal under paper objective: `{optimal['id']}` "
            f"(rule={optimal_rule}) heldout={optimal['heldout']['score']:+.3f} "
            f"tip YTD={optimal['tip_gates']['ytd']['gate']} "
            f"1y={optimal['tip_gates']['trailing_1y']['gate']}. "
            "Soft-Frozen KEEP · no live wire."
        ),
    }
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    RESEARCH.joinpath("FIN_PRE_EXDIV_KD_OPTIMIZE.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    def row_line(r):
        h = r["heldout"]
        t = r["tip_gates"]
        return (
            f"| `{r['id']}` | {h['score']:.3f} | {h['mdd_improve_pp']:.3f} | "
            f"{h['cagr_giveback_pp']:.3f} | {t['ytd']['gate']} | {t['trailing_1y']['gate']} | "
            f"{r['tip_clean']} |"
        )

    lines = [
        "# FIN_PRE_EXDIV_KD — parameter optimize (paper NAV)",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Status: **OPTIMAL_SELECTED** · Soft-Frozen **KEEP** · live wire **false**",
        "",
        "## Objective",
        "",
        "1. tip-clean (YTD+1y PASS) **and** held-out score > 0",
        "2. else no tip PAUSE · max held-out",
        "3. else max held-out",
        "",
        f"## Optimal: `{optimal['id']}`",
        "",
        f"- Selection rule: **{optimal_rule}**",
        f"- Held-out score: **{optimal['heldout']['score']:+.3f}**",
        f"- Tip: YTD **{optimal['tip_gates']['ytd']['gate']}** "
        f"({optimal['tip_gates']['ytd'].get('giveback_pp')}) · "
        f"1y **{optimal['tip_gates']['trailing_1y']['gate']}** "
        f"({optimal['tip_gates']['trailing_1y'].get('giveback_pp')})",
        "",
    ]
    if optimal.get("season"):
        lines += [
            f"- Season: `{optimal['season']}` {optimal.get('season_start')}–{optimal.get('season_end')}",
            f"- K thresh: **< {optimal['k_thresh']}** · pre-ex skip: **T−{optimal['pre_days']}…T0**",
            "",
        ]
    lines += [
        "## Top 12 (ranked)",
        "",
        "| id | heldout | MDD↑ | CAGR gb | YTD | 1y | tip-clean |",
        "|---|---:|---:|---:|---|---|---|",
    ]
    for r in ranked[:12]:
        lines.append(row_line(r))
    lines += [
        "",
        "## Anchors",
        "",
        "| id | heldout | MDD↑ | CAGR gb | YTD | 1y | tip-clean |",
        "|---|---:|---:|---:|---|---|---|",
    ]
    for r in ranked:
        if r["family"] == "anchor":
            lines.append(row_line(r))
    lines += [
        "",
        "## Verdict",
        "",
        payload["verdict"],
        "",
        "## Hard rules",
        "",
        "- Soft-Frozen KEEP · no live wire · optimize ≠ observe OPEN / cutover",
        "",
        f"Repro: `{OUT.relative_to(ROOT)}/`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "REPORT.md").write_text(md)
    RESEARCH.joinpath("FIN_PRE_EXDIV_KD_OPTIMIZE.md").write_text(md)
    print(
        json.dumps(
            {
                "optimal": optimal["id"],
                "rule": optimal_rule,
                "held": optimal["heldout"]["score"],
                "ytd": optimal["tip_gates"]["ytd"]["gate"],
                "t1": optimal["tip_gates"]["trailing_1y"]["gate"],
                "n_coexist": len(coexist),
                "top5": [r["id"] for r in ranked[:5]],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
