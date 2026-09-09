#!/usr/bin/env python3
"""Small-search FIN_POST_EXDIV_KD autumn params via Exact T+1 paper NAV.

Grid (小搜): season window × Yahoo K9 thresh × hold_days.
Objective (in order):
  1) tip-clean (YTD+1y PASS) AND held-out score > 0
  2) else no PAUSE maximizing held-out
  3) else max held-out

Anchors: FIN_EQUAL · KD_OPT (live reference, untouched).
Soft-Frozen KEEP · live wire false · stop if no lift vs KD_OPT.
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
    FIN_POST_EXDIV_KD,
    FIN_PRE_EXDIV_KD,
    TEL_EQUAL,
    build_exdiv_buy_ok,
    build_kd_post_exdiv_season_tilt_scores,
    build_kd_season_tilt_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/fin-post-exdiv-autumn-optimize-20260909"
RESEARCH = ROOT / "research/ops"

CAPITAL = 500_000_000.0
LOT = BOARD_LOT
TRAIL_ALERT_PP = 3.0
TRAIL_PAUSE_PP = 5.0
ACTIVE_SCORE = 1.5

SEASONS = [
    ("OCT20_DEC10", (10, 20), (12, 10)),  # probe baseline
    ("OCT1_DEC15", (10, 1), (12, 15)),
    ("OCT15_NOV30", (10, 15), (11, 30)),
    ("NOV1_DEC15", (11, 1), (12, 15)),
]
K_THRESH = (20.0, 25.0, 30.0)
HOLD_DAYS = (20, 40, 60)

KD_OPT = {
    "id": "KD_APR15_MAY15_Klt30_T15",
    "season_start": (4, 15),
    "season_end": (5, 15),
    "k_thresh": 30.0,
    "pre_days": 15,
    "active_score": 1.5,
}


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


def sim(market, target, regime, dividends, *, policy, scores=None, buy_ok=None):
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
    )


def rank_key(row: dict) -> tuple:
    tip = row["tip_gates"]
    ytd, t1 = tip["ytd"]["gate"], tip["trailing_1y"]["gate"]
    tip_clean = ytd == "PASS" and t1 == "PASS"
    no_pause = ytd != "PAUSE_REVIEW" and t1 != "PAUSE_REVIEW" and ytd != "INSUFFICIENT"
    held = row["heldout"]["score"]
    coexist = tip_clean and held > 0
    return (1 if coexist else 0, 1 if no_pause else 0, held)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "outputs").mkdir(exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.9]

    print("loading ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, _s, target, regime = e16_features(market)
    cal = pd.to_datetime(market["date"]).drop_duplicates().sort_values()

    print("BASE FIN_EQUAL ...", flush=True)
    nav_b, _fills_b, meta_b = sim(market, target, regime, dividends, policy=FIN_EQUAL)
    assert meta_b.get("exact_t1_ok")
    win_b = {w: window_stats(nav_b, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
    asof = pd.to_datetime(nav_b["date"]).max()

    print("anchor KD_OPT ...", flush=True)
    kd_scores = build_kd_season_tilt_scores(
        market,
        dividends,
        FIN,
        k_thresh=float(KD_OPT["k_thresh"]),
        season_start=KD_OPT["season_start"],
        season_end=KD_OPT["season_end"],
        pre_days=int(KD_OPT["pre_days"]),
        active_score=float(KD_OPT["active_score"]),
    )
    kd_ok = build_pre_exdiv_window_buy_ok(
        cal, dividends, FIN, pre_days=int(KD_OPT["pre_days"]), also_stock_ex=True
    )
    autumn_ok = build_exdiv_buy_ok(cal, dividends, FIN, also_stock_ex=True)

    rows: list[dict] = []
    nav_kd, fills_kd, meta_kd = sim(
        market, target, regime, dividends, policy=FIN_PRE_EXDIV_KD, scores=kd_scores, buy_ok=kd_ok
    )
    assert meta_kd.get("exact_t1_ok")
    win_kd = {w: window_stats(nav_kd, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
    tip_kd = tip_gate(nav_b, nav_kd, asof)
    held_kd = score_vs_base(win_b["heldout_2019_plus"], win_kd["heldout_2019_plus"])
    sealed_kd = score_vs_base(win_b["sealed_2023_plus"], win_kd["sealed_2023_plus"])
    kd_row = {
        "id": "KD_OPT",
        "family": "anchor",
        "season": "APR15_MAY15",
        "k_thresh": KD_OPT["k_thresh"],
        "hold_days": None,
        "heldout": held_kd,
        "sealed_REPORT_ONLY": sealed_kd,
        "tip_gates": tip_kd,
        "tip_clean": tip_kd["ytd"]["gate"] == "PASS" and tip_kd["trailing_1y"]["gate"] == "PASS",
        "n_fills": int(len(fills_kd)),
        "vs_kd_opt_heldout_delta": 0.0,
    }
    rows.append(kd_row)

    grid = [(s, k, h) for s in SEASONS for k in K_THRESH for h in HOLD_DAYS]
    print(f"autumn grid sims: {len(grid)} ...", flush=True)
    for i, ((sname, s0, s1), kthr, hold) in enumerate(grid, 1):
        rid = f"AUT_{sname}_Klt{kthr:g}_H{hold}"
        print(f"  [{i}/{len(grid)}] {rid} ...", flush=True)
        scores = build_kd_post_exdiv_season_tilt_scores(
            market,
            dividends,
            FIN,
            k_thresh=float(kthr),
            season_start=s0,
            season_end=s1,
            active_score=ACTIVE_SCORE,
            hold_days=int(hold),
        )
        nav, fills, meta = sim(
            market,
            target,
            regime,
            dividends,
            policy=FIN_POST_EXDIV_KD,
            scores=scores,
            buy_ok=autumn_ok,
        )
        assert meta.get("exact_t1_ok"), rid
        win = {w: window_stats(nav, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
        tip = tip_gate(nav_b, nav, asof)
        held = score_vs_base(win_b["heldout_2019_plus"], win["heldout_2019_plus"])
        sealed = score_vs_base(win_b["sealed_2023_plus"], win["sealed_2023_plus"])
        rows.append(
            {
                "id": rid,
                "family": "autumn",
                "season": sname,
                "season_start": list(s0),
                "season_end": list(s1),
                "k_thresh": float(kthr),
                "hold_days": int(hold),
                "heldout": held,
                "sealed_REPORT_ONLY": sealed,
                "tip_gates": tip,
                "tip_clean": tip["ytd"]["gate"] == "PASS" and tip["trailing_1y"]["gate"] == "PASS",
                "n_fills": int(len(fills)),
                "vs_kd_opt_heldout_delta": float(held["score"] - held_kd["score"]),
            }
        )

    autumn_rows = [r for r in rows if r["family"] == "autumn"]
    autumn_rows_sorted = sorted(autumn_rows, key=rank_key, reverse=True)
    best = autumn_rows_sorted[0]
    baseline = next(
        r
        for r in autumn_rows
        if r["season"] == "OCT20_DEC10" and r["k_thresh"] == 25.0 and r["hold_days"] == 40
    )
    beats_kd = bool(
        best["tip_clean"]
        and best["heldout"]["score"] > held_kd["score"] + 1e-9
        and best["vs_kd_opt_heldout_delta"] > 0
    )
    improves_baseline = bool(rank_key(best) > rank_key(baseline) or best["id"] != baseline["id"])

    verdict_status = "STOP" if not beats_kd else "CANDIDATE"
    verdict = (
        f"Best autumn `{best['id']}` held-out={best['heldout']['score']:+.3f} "
        f"tip_clean={best['tip_clean']} · vs KD_OPT Δ={best['vs_kd_opt_heldout_delta']:+.3f}. "
        f"KD_OPT held-out={held_kd['score']:+.3f}. "
        f"{'No tip/held-out lift vs KD_OPT → STOP.' if not beats_kd else 'Beats KD_OPT on tip+held-out (paper only).'} "
        f"Soft-Frozen KEEP · live KD_OPT untouched."
    )

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "FIN_POST_EXDIV_AUTUMN_OPTIMIZE",
        "status": verdict_status,
        "live_wire": False,
        "soft_frozen_keep": True,
        "live_kd_opt_unchanged": True,
        "grid": {
            "seasons": [s[0] for s in SEASONS],
            "k_thresh": list(K_THRESH),
            "hold_days": list(HOLD_DAYS),
            "n_grid": len(grid),
        },
        "kd_opt_anchor": kd_row,
        "baseline_probe": baseline,
        "best_autumn": best,
        "beats_kd_opt": beats_kd,
        "improves_vs_probe_baseline": improves_baseline,
        "ranked_autumn_top10": autumn_rows_sorted[:10],
        "all_rows": sorted(rows, key=rank_key, reverse=True),
        "verdict": verdict,
        "stop_rule": "No tip/held-out lift vs KD_OPT → STOP further autumn research",
    }
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    RESEARCH.joinpath("FIN_POST_EXDIV_AUTUMN_OPTIMIZE.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    flat = []
    for r in autumn_rows_sorted:
        flat.append(
            {
                "id": r["id"],
                "season": r["season"],
                "k_thresh": r["k_thresh"],
                "hold_days": r["hold_days"],
                "heldout_score": r["heldout"]["score"],
                "mdd_improve_pp": r["heldout"]["mdd_improve_pp"],
                "cagr_giveback_pp": r["heldout"]["cagr_giveback_pp"],
                "ytd": r["tip_gates"]["ytd"]["gate"],
                "t1y": r["tip_gates"]["trailing_1y"]["gate"],
                "tip_clean": r["tip_clean"],
                "vs_kd_opt_heldout_delta": r["vs_kd_opt_heldout_delta"],
            }
        )
    pd.DataFrame(flat).to_csv(OUT / "outputs" / "autumn_grid_ranked.csv", index=False)

    lines = [
        "# FIN_POST_EXDIV_KD — autumn parameter small-search (paper)",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Status: **{verdict_status}** · Soft-Frozen **KEEP** · live **KD_OPT untouched**",
        "",
        f"Grid: {len(SEASONS)} seasons × {len(K_THRESH)} K × {len(HOLD_DAYS)} hold = **{len(grid)}**",
        "",
        "## Anchors",
        "",
        f"| id | heldout | tip_clean |",
        f"|---|---:|---|",
        f"| `KD_OPT` | {held_kd['score']:.3f} | {kd_row['tip_clean']} |",
        f"| probe baseline `OCT20_DEC10 Klt25 H40` | {baseline['heldout']['score']:.3f} | {baseline['tip_clean']} |",
        "",
        "## Best autumn",
        "",
        f"- **`{best['id']}`** held-out **{best['heldout']['score']:+.3f}** · tip_clean={best['tip_clean']}",
        f"- vs KD_OPT Δ held-out **{best['vs_kd_opt_heldout_delta']:+.3f}**",
        f"- Beats KD_OPT (tip+held-out)? **{beats_kd}**",
        "",
        "## Top 10 autumn",
        "",
        "| id | heldout | MDD↑ | CAGR gb | YTD | 1y | vs KD Δ |",
        "|---|---:|---:|---:|---|---|---:|",
    ]
    for r in autumn_rows_sorted[:10]:
        h = r["heldout"]
        tip = r["tip_gates"]
        lines.append(
            f"| `{r['id']}` | {h['score']:.3f} | {h['mdd_improve_pp']:.3f} | "
            f"{h['cagr_giveback_pp']:.3f} | {tip['ytd']['gate']} | {tip['trailing_1y']['gate']} | "
            f"{r['vs_kd_opt_heldout_delta']:+.3f} |"
        )
    lines += [
        "",
        "## Verdict",
        "",
        verdict,
        "",
        "## Hard rules",
        "",
        "- Soft-Frozen KEEP · no live wire · no cutover from this search",
        "- Dual-season follow-up: `FIN_KD_AUTUMN_DUAL_SEASON.md`",
        "",
        f"Repro: `{OUT.relative_to(ROOT)}/`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "REPORT.md").write_text(md)
    RESEARCH.joinpath("FIN_POST_EXDIV_AUTUMN_OPTIMIZE.md").write_text(md)
    print(
        json.dumps(
            {
                "status": verdict_status,
                "best": best["id"],
                "best_heldout": best["heldout"]["score"],
                "kd_opt_heldout": held_kd["score"],
                "beats_kd_opt": beats_kd,
                "verdict": verdict,
            },
            indent=2,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
