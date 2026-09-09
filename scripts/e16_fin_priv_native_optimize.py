#!/usr/bin/env python3
"""民營金控 native within-sleeve optimize — RESEARCH ONLY.

Soft-Frozen sleeve weights from live FINBAND (公股 features).
Financial dollars → PRIV_R3R4 only.
Baseline: PRIV_EQUAL. Native KD seasons biased to Jun–Jul cash-ex.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e16_soft_frozen_base as soft
import e50_early_stack_combined_nav as e50
from e16_private_fin_holdings_rescreen import (
    PRIV_R3R4,
    PUB_R1,
    TEL,
    build_extended_market,
    held_score,
    tip_gate,
)
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, window_stats
from tw_share_lots import BOARD_LOT
from within_sleeve_alloc import (
    FIN_EQUAL,
    FIN_MIX_EQUAL_PRE_EXDIV_KD,
    FIN_PRE_EXDIV_KD,
    FIN_RS_SOFT_TILT_EXDIV,
    TEL_EQUAL,
    build_exdiv_buy_ok,
    build_kd_season_tilt_scores,
    build_name_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/fin-priv-native-20260909"
RESEARCH = ROOT / "research/ops"

CAPITAL = 500_000_000.0
LOT = BOARD_LOT

# Transplanted 公股 live KD (anchor — expected mismatch for Jun–Jul ex).
PUB_KD_OPT = {
    "id": "TRANSPLANT_PUB_KD_APR15_MAY15_Klt30_T15",
    "season": "APR15_MAY15",
    "season_start": (4, 15),
    "season_end": (5, 15),
    "k_thresh": 30.0,
    "pre_days": 15,
    "active_score": 1.5,
}

SEASONS = [
    ("APR15_MAY15", (4, 15), (5, 15)),  # transplanted 公股 control season
    ("MAY", (5, 1), (5, 31)),
    ("MAY15_JUN15", (5, 15), (6, 15)),
    ("MAY15_JUN30", (5, 15), (6, 30)),
    ("JUN", (6, 1), (6, 30)),
    ("JUN01_JUL15", (6, 1), (7, 15)),
    ("MAY15_JUL15", (5, 15), (7, 15)),
]
K_THRESH = (20.0, 25.0, 30.0)
PRE_DAYS = (5, 10, 15)
ACTIVE_SCORE = 1.5


def run_book(
    market,
    dividends,
    target,
    regime,
    *,
    book_id: str,
    financial_alloc: str,
    fin_scores=None,
    fin_buy_ok=None,
    fin_mix_lambda: float | None = None,
):
    old_fin, old_all = list(e50.FIN), list(e50.ALL)
    e50.FIN = list(PRIV_R3R4)
    e50.ALL = list(PRIV_R3R4) + TEL + ["0050"]
    try:
        nav, fills, meta = e50.simulate_core(
            market,
            target,
            regime,
            dividends,
            apply_e22=True,
            apply_stock_div=True,
            capital=CAPITAL,
            lot_size=LOT,
            financial_alloc=financial_alloc,
            telecom_alloc=TEL_EQUAL,
            fin_name_scores=fin_scores,
            fin_buy_ok=fin_buy_ok,
            fin_mix_lambda=fin_mix_lambda,
        )
        assert meta.get("exact_t1_ok"), book_id
        win = {w: window_stats(nav, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
        return {
            "id": book_id,
            "financial_alloc": financial_alloc,
            "n_fills": int(len(fills)),
            "windows": win,
            "nav": nav,
        }
    finally:
        e50.FIN = old_fin
        e50.ALL = old_all


def kd_book(market, dividends, target, regime, *, season, s0, s1, k_thresh, pre_days):
    cal = pd.to_datetime(market["date"]).drop_duplicates().sort_values()
    codes = list(PRIV_R3R4)
    scores = build_kd_season_tilt_scores(
        market,
        dividends,
        codes,
        k_thresh=float(k_thresh),
        season_start=s0,
        season_end=s1,
        pre_days=int(pre_days),
        active_score=ACTIVE_SCORE,
    )
    buy_ok = build_pre_exdiv_window_buy_ok(
        cal, dividends, codes, pre_days=int(pre_days), also_stock_ex=True
    )
    bid = f"PRIV_KD_{season}_Klt{k_thresh:g}_T{pre_days}"
    row = run_book(
        market,
        dividends,
        target,
        regime,
        book_id=bid,
        financial_alloc=FIN_PRE_EXDIV_KD,
        fin_scores=scores,
        fin_buy_ok=buy_ok,
    )
    row["season"] = season
    row["season_start"] = list(s0)
    row["season_end"] = list(s1)
    row["k_thresh"] = float(k_thresh)
    row["pre_days"] = int(pre_days)
    return row


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    assert soft.FIN == PUB_R1
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.9]

    print("calendar note: PUB cash-ex ~Aug; PRIV cash-ex ~Jun–Jul", flush=True)
    print("building extended market ...", flush=True)
    market = build_extended_market()
    dividends = load_dividends()
    print("Soft-Frozen targets (公股 features) ...", flush=True)
    _p, _s, target, regime = e50.e16_features(market)
    cal = pd.to_datetime(market["date"]).drop_duplicates().sort_values()

    results = {}
    print("baseline PRIV_EQUAL ...", flush=True)
    results["PRIV_EQUAL"] = run_book(
        market, dividends, target, regime, book_id="PRIV_EQUAL", financial_alloc=FIN_EQUAL
    )

    print("anchor transplanted PUB KD_OPT ...", flush=True)
    transplant = kd_book(
        market,
        dividends,
        target,
        regime,
        season=PUB_KD_OPT["season"],
        s0=PUB_KD_OPT["season_start"],
        s1=PUB_KD_OPT["season_end"],
        k_thresh=PUB_KD_OPT["k_thresh"],
        pre_days=PUB_KD_OPT["pre_days"],
    )
    transplant["id"] = PUB_KD_OPT["id"]
    results[PUB_KD_OPT["id"]] = transplant

    print("anchor RS_SOFT_TILT_EXDIV ...", flush=True)
    rs_scores = build_name_scores(market, PRIV_R3R4)
    rs_ok = build_exdiv_buy_ok(cal, dividends, PRIV_R3R4, also_stock_ex=True)
    results["PRIV_RS_SOFT_TILT_EXDIV"] = run_book(
        market,
        dividends,
        target,
        regime,
        book_id="PRIV_RS_SOFT_TILT_EXDIV",
        financial_alloc=FIN_RS_SOFT_TILT_EXDIV,
        fin_scores=rs_scores,
        fin_buy_ok=rs_ok,
    )

    print("anchor MIX_L75 (EQUAL + PRE_EXDIV_KD transplant season) ...", flush=True)
    mix_scores = build_kd_season_tilt_scores(
        market,
        dividends,
        PRIV_R3R4,
        k_thresh=30.0,
        season_start=(4, 15),
        season_end=(5, 15),
        pre_days=15,
        active_score=ACTIVE_SCORE,
    )
    mix_ok = build_pre_exdiv_window_buy_ok(
        cal, dividends, PRIV_R3R4, pre_days=15, also_stock_ex=True
    )
    results["PRIV_MIX_L75_TRANSPLANT"] = run_book(
        market,
        dividends,
        target,
        regime,
        book_id="PRIV_MIX_L75_TRANSPLANT",
        financial_alloc=FIN_MIX_EQUAL_PRE_EXDIV_KD,
        fin_scores=mix_scores,
        fin_buy_ok=mix_ok,
        fin_mix_lambda=0.75,
    )

    grid = [(s, k, p) for s in SEASONS for k in K_THRESH for p in PRE_DAYS]
    # drop exact transplant duplicate already run as anchor
    grid = [
        x
        for x in grid
        if not (
            x[0][0] == "APR15_MAY15"
            and x[1] == 30.0
            and x[2] == 15
        )
    ]
    print(f"native KD grid: {len(grid)} ...", flush=True)
    for i, ((sname, s0, s1), kthr, pre) in enumerate(grid, 1):
        print(f"  [{i}/{len(grid)}] {sname} K<{kthr:g} T-{pre} ...", flush=True)
        row = kd_book(
            market, dividends, target, regime, season=sname, s0=s0, s1=s1, k_thresh=kthr, pre_days=pre
        )
        results[row["id"]] = row

    base = results["PRIV_EQUAL"]
    asof = pd.to_datetime(base["nav"]["date"]).max()

    # optional report-only vs live pub
    live = None
    try:
        old_fin, old_all = list(e50.FIN), list(e50.ALL)
        e50.FIN = list(PUB_R1)
        e50.ALL = list(PUB_R1) + TEL + ["0050"]
        cal2 = pd.to_datetime(market["date"]).drop_duplicates().sort_values()
        ls = build_kd_season_tilt_scores(
            market,
            dividends,
            PUB_R1,
            k_thresh=30.0,
            season_start=(4, 15),
            season_end=(5, 15),
            pre_days=15,
            active_score=1.5,
        )
        lo = build_pre_exdiv_window_buy_ok(cal2, dividends, PUB_R1, pre_days=15, also_stock_ex=True)
        nav, fills, meta = e50.simulate_core(
            market,
            target,
            regime,
            dividends,
            apply_e22=True,
            apply_stock_div=True,
            capital=CAPITAL,
            lot_size=LOT,
            financial_alloc=FIN_PRE_EXDIV_KD,
            telecom_alloc=TEL_EQUAL,
            fin_name_scores=ls,
            fin_buy_ok=lo,
        )
        live = {
            "id": "LIVE_PUB_KD_REPORT_ONLY",
            "windows": {w: window_stats(nav, a, b) for w, (a, b) in WINDOWS_STANDARD.items()},
            "nav": nav,
        }
    finally:
        e50.FIN = old_fin
        e50.ALL = old_all

    ranked = []
    for bid, row in results.items():
        if bid == "PRIV_EQUAL":
            continue
        held = held_score(base["windows"]["heldout_2019_plus"], row["windows"]["heldout_2019_plus"])
        tip = tip_gate(base["nav"], row["nav"], asof)
        tip_clean = tip["ytd"]["gate"] == "PASS" and tip["trailing_1y"]["gate"] == "PASS"
        sealed = held_score(base["windows"]["sealed_2023_plus"], row["windows"]["sealed_2023_plus"])
        vs_live = None
        if live is not None:
            vs_live = held_score(
                live["windows"]["heldout_2019_plus"], row["windows"]["heldout_2019_plus"]
            )["score"]
        ranked.append(
            {
                "id": bid,
                "financial_alloc": row["financial_alloc"],
                "season": row.get("season"),
                "season_start": row.get("season_start"),
                "season_end": row.get("season_end"),
                "k_thresh": row.get("k_thresh"),
                "pre_days": row.get("pre_days"),
                "heldout_score": held["score"],
                "mdd_improve_pp": held["mdd_improve_pp"],
                "cagr_giveback_pp": held["cagr_giveback_pp"],
                "tip_ytd": tip["ytd"]["gate"],
                "tip_1y": tip["trailing_1y"]["gate"],
                "tip_clean": tip_clean,
                "sealed_score_REPORT_ONLY": sealed["score"],
                "vs_live_pub_kd_REPORT_ONLY": vs_live,
                "n_fills": row["n_fills"],
                "coexist": bool(tip_clean and held["score"] > 0),
            }
        )
    ranked.sort(key=lambda r: r["heldout_score"], reverse=True)
    coexist = [r for r in ranked if r["coexist"]]
    no_pause = [
        r
        for r in ranked
        if r["tip_ytd"] != "PAUSE_REVIEW" and r["tip_1y"] != "PAUSE_REVIEW"
    ]
    if coexist:
        status = "OPTIMAL_SELECTED"
        optimal = coexist[0]
        rule = "coexist (tip PASS + heldout>0 vs PRIV_EQUAL)"
    elif no_pause:
        status = "BEST_NO_PAUSE"
        optimal = max(no_pause, key=lambda r: r["heldout_score"])
        rule = "no tip PAUSE · max heldout vs PRIV_EQUAL"
    else:
        status = "STOP_NO_POSITIVE_HELDOUT"
        optimal = ranked[0] if ranked else None
        rule = "max heldout (all tip-dirty or score<=0)"

    abs_rows = {
        bid: {
            "full_cagr": row["windows"]["full"].get("cagr"),
            "full_mdd": row["windows"]["full"].get("max_drawdown"),
            "heldout_cagr": row["windows"]["heldout_2019_plus"].get("cagr"),
            "heldout_mdd": row["windows"]["heldout_2019_plus"].get("max_drawdown"),
        }
        for bid, row in results.items()
    }
    if live is not None:
        abs_rows["LIVE_PUB_KD_REPORT_ONLY"] = {
            "full_cagr": live["windows"]["full"].get("cagr"),
            "full_mdd": live["windows"]["full"].get("max_drawdown"),
            "heldout_cagr": live["windows"]["heldout_2019_plus"].get("cagr"),
            "heldout_mdd": live["windows"]["heldout_2019_plus"].get("max_drawdown"),
        }

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "FIN_PRIV_NATIVE_WITHIN_SLEEVE_OPTIMIZE",
        "status": status,
        "charter": "research/ops/FIN_PRIV_NATIVE_WITHIN_SLEEVE_CHARTER.md",
        "live_wire": False,
        "baseline": "PRIV_EQUAL",
        "universe": PRIV_R3R4,
        "calendar_note": "PUB cash-ex ~Aug; PRIV cash-ex ~Jun–Jul",
        "optimal_rule": rule,
        "optimal": optimal,
        "capital": CAPITAL,
        "lot_size": LOT,
        "n_grid": len(grid),
        "absolute": abs_rows,
        "ranked_vs_priv_equal": ranked,
        "coexist_ids": [r["id"] for r in coexist],
    }
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    RESEARCH.joinpath("FIN_PRIV_NATIVE_WITHIN_SLEEVE_OPTIMIZE.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )
    RESEARCH.joinpath("FIN_PRIV_NATIVE_WITHIN_SLEEVE_CHARTER.json").write_text(
        json.dumps(
            {
                "label": "FIN_PRIV_NATIVE_WITHIN_SLEEVE_CHARTER",
                "status": status,
                "date": "2026-09-09",
                "optimal_id": None if optimal is None else optimal["id"],
            },
            indent=2,
        )
        + "\n"
    )

    lines = [
        "# 民營 native within-sleeve optimize",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Status: **{status}** · baseline **`PRIV_EQUAL`** · Soft-Frozen weights (公股 features) · live wire **false**",
        f"Universe PRIV_R3R4 · capital **{CAPITAL:,.0f}** · lot **{LOT}**",
        f"Calendar: PUB cash-ex ~**Aug** · PRIV ~**Jun–Jul**",
        "",
        f"## Optimal: `{optimal['id'] if optimal else 'none'}`",
        "",
        f"- Rule: **{rule}**",
        f"- Held-out vs PRIV_EQUAL: **{optimal['heldout_score']:+.3f}**" if optimal else "",
        f"- Tip: YTD **{optimal['tip_ytd']}** · 1y **{optimal['tip_1y']}**" if optimal else "",
        f"- Season: `{optimal.get('season')}` {optimal.get('season_start')}–{optimal.get('season_end')} · K<{optimal.get('k_thresh')} · T−{optimal.get('pre_days')}"
        if optimal and optimal.get("season")
        else "",
        "",
        "## Top 15 vs PRIV_EQUAL",
        "",
        "| id | heldout | MDD↑ | CAGR gb | YTD | 1y | tip-clean | vs LIVE_PUB (RO) |",
        "|---|---:|---:|---:|---|---|---|---:|",
    ]
    for r in ranked[:15]:
        vlo = "" if r["vs_live_pub_kd_REPORT_ONLY"] is None else f"{r['vs_live_pub_kd_REPORT_ONLY']:.3f}"
        lines.append(
            f"| `{r['id']}` | {r['heldout_score']:.3f} | {r['mdd_improve_pp']:.3f} | "
            f"{r['cagr_giveback_pp']:.3f} | {r['tip_ytd']} | {r['tip_1y']} | {r['tip_clean']} | {vlo} |"
        )
    lines += [
        "",
        f"- Coexist: `{payload['coexist_ids'] or 'none'}`",
        "- Soft-Frozen membership / live KD_OPT unchanged.",
        "- vs LIVE_PUB_KD is report-only (not selection).",
        "",
        f"Repro: `{OUT.relative_to(ROOT)}/`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "REPORT.md").write_text(md)
    RESEARCH.joinpath("FIN_PRIV_NATIVE_WITHIN_SLEEVE_OPTIMIZE.md").write_text(md)
    print(
        json.dumps(
            {
                "status": status,
                "optimal": optimal,
                "coexist": payload["coexist_ids"],
                "top5": ranked[:5],
            },
            indent=2,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
