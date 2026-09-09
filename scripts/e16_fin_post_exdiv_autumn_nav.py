#!/usr/bin/env python3
"""FIN_POST_EXDIV_KD autumn sleeve — Exact T+1 paper NAV vs FIN_EQUAL / KD_OPT.

Rule (Yahoo K9):
  - After cash-ex, Oct20–Dec10: first K9 < 25 → soft-tilt accumulate ~40 sessions
  - Skip buy on cash/stock ex day only
  - Else near-equal among buy-ok

Soft-Frozen KEEP · live KD_OPT untouched · capital 500M · lot 1000.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e16_soft_frozen_base as soft
from e45_paper_harness import WINDOWS_STANDARD, deltas_vs_base, load_dividends, load_market, window_stats
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
OUT = ROOT / "repro/fin-post-exdiv-autumn-nav-20260909"
RESEARCH = ROOT / "research/ops"

CHARTER_CAPITAL = 500_000_000.0
CHARTER_LOT = BOARD_LOT
TRAIL_ALERT_PP = 3.0
TRAIL_PAUSE_PP = 5.0
AUTUMN = {
    "season_start": (10, 20),
    "season_end": (12, 10),
    "k_thresh": 25.0,
    "hold_days": 40,
    "active_score": 1.5,
}
KD_OPT = {
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


def run_book(market, dividends, target, regime, *, policy, fin_scores, fin_buy_ok):
    return simulate_core(
        market,
        target,
        regime,
        dividends,
        apply_e22=True,
        apply_stock_div=True,
        capital=CHARTER_CAPITAL,
        lot_size=CHARTER_LOT,
        financial_alloc=policy,
        telecom_alloc=TEL_EQUAL,
        fin_name_scores=fin_scores,
        fin_buy_ok=fin_buy_ok,
    )


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "outputs").mkdir(exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.9]

    print("loading ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, _s, target, regime = e16_features(market)
    cal = pd.to_datetime(market["date"]).drop_duplicates().sort_values()

    print("building autumn post-ex + KD_OPT scores ...", flush=True)
    autumn_scores = build_kd_post_exdiv_season_tilt_scores(
        market,
        dividends,
        FIN,
        k_thresh=float(AUTUMN["k_thresh"]),
        season_start=AUTUMN["season_start"],
        season_end=AUTUMN["season_end"],
        active_score=float(AUTUMN["active_score"]),
        hold_days=int(AUTUMN["hold_days"]),
    )
    autumn_buy_ok = build_exdiv_buy_ok(cal, dividends, FIN, also_stock_ex=True)
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
    kd_buy_ok = build_pre_exdiv_window_buy_ok(
        cal, dividends, FIN, pre_days=int(KD_OPT["pre_days"]), also_stock_ex=True
    )

    specs = [
        ("FIN_EQUAL", FIN_EQUAL, None, None),
        ("AUTUMN_POST_EX", FIN_POST_EXDIV_KD, autumn_scores, autumn_buy_ok),
        ("KD_OPT", FIN_PRE_EXDIV_KD, kd_scores, kd_buy_ok),
    ]
    books = {}
    for label, policy, scores, buy_ok in specs:
        print(f"  sim {label} ...", flush=True)
        nav, fills, meta = run_book(
            market,
            dividends,
            target,
            regime,
            policy=policy,
            fin_scores=scores,
            fin_buy_ok=buy_ok,
        )
        assert meta.get("exact_t1_ok"), label
        slug = label.lower()
        nav.to_csv(OUT / "outputs" / f"{slug}_daily_nav.csv", index=False)
        fills.to_csv(OUT / "outputs" / f"{slug}_fills.csv", index=False)
        win = {w: window_stats(nav, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
        books[label] = {"nav": nav, "meta": meta, "windows": win, "n_fills": int(len(fills))}

    base = books["FIN_EQUAL"]
    asof = pd.to_datetime(base["nav"]["date"]).max()
    ranked = []
    for label, book in books.items():
        if label == "FIN_EQUAL":
            continue
        held = score_vs_base(base["windows"]["heldout_2019_plus"], book["windows"]["heldout_2019_plus"])
        sealed = score_vs_base(base["windows"]["sealed_2023_plus"], book["windows"]["sealed_2023_plus"])
        tip = tip_gate(base["nav"], book["nav"], asof)
        tip_clean = tip["ytd"]["gate"] == "PASS" and tip["trailing_1y"]["gate"] == "PASS"
        ranked.append(
            {
                "id": label,
                "n_fills": book["n_fills"],
                "scores": {"heldout_2019_plus": held, "sealed_2023_plus_REPORT_ONLY": sealed},
                "tip_gates": tip,
                "tip_clean": tip_clean,
            }
        )
    ranked.sort(key=lambda r: r["scores"]["heldout_2019_plus"]["score"], reverse=True)

    jb = base["nav"][["date", "nav"]].rename(columns={"nav": "nav_base"})
    for label in ("AUTUMN_POST_EX", "KD_OPT"):
        jc = books[label]["nav"][["date", "nav"]].rename(columns={"nav": f"nav_{label.lower()}"})
        jb = jb.merge(jc, on="date", how="inner")
    jb.to_csv(OUT / "outputs/nav_compare.csv", index=False)

    autumn = next(r for r in ranked if r["id"] == "AUTUMN_POST_EX")
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "FIN_POST_EXDIV_AUTUMN_NAV",
        "status": "PAPER_NAV",
        "live_wire": False,
        "soft_frozen_keep": True,
        "live_kd_opt_unchanged": True,
        "autumn_params": AUTUMN,
        "ranked": ranked,
        "autumn": autumn,
        "verdict": (
            f"AUTUMN_POST_EX held-out score={autumn['scores']['heldout_2019_plus']['score']:+.3f} "
            f"tip_clean={autumn['tip_clean']}. Soft-Frozen KEEP · live KD_OPT untouched."
        ),
    }
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    RESEARCH.joinpath("FIN_POST_EXDIV_AUTUMN_NAV.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    lines = [
        "# FIN post-exdiv autumn — paper NAV",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Soft-Frozen **KEEP** · live **KD_OPT untouched** · live wire **false**",
        "",
        f"Autumn rule: post-ex · {AUTUMN['season_start']}–{AUTUMN['season_end']} · "
        f"K9<{AUTUMN['k_thresh']} · hold≤{AUTUMN['hold_days']}d",
        "",
        "| id | heldout score | MDD↑pp | CAGR giveback | YTD | 1y | tip_clean |",
        "|---|---:|---:|---:|---|---|---|",
    ]
    for r in ranked:
        h = r["scores"]["heldout_2019_plus"]
        tip = r["tip_gates"]
        lines.append(
            f"| `{r['id']}` | {h['score']:.3f} | {h['mdd_improve_pp']:.3f} | "
            f"{h['cagr_giveback_pp']:.3f} | {tip['ytd']['gate']} | {tip['trailing_1y']['gate']} | "
            f"{r['tip_clean']} |"
        )
    lines += [
        "",
        "## Verdict",
        "",
        payload["verdict"],
        "",
        "## Hard rules",
        "",
        "- Soft-Frozen KEEP · no live cutover from this NAV",
        "- Does not replace live KD_OPT",
        "",
        f"Repro: `{OUT.relative_to(ROOT)}/`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "REPORT.md").write_text(md)
    RESEARCH.joinpath("FIN_POST_EXDIV_AUTUMN_NAV.md").write_text(md)
    print(json.dumps({"ranked": ranked, "verdict": payload["verdict"]}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
