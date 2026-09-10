#!/usr/bin/env python3
"""Paper screen: LIVE_KD_OPT base + indicator assists (buy-low / sell-high).

Charter: research/ops/KD_OPT_INDICATOR_ASSIST_CHARTER.md
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
from ta_indicator_catalog import HIGH_IDS, LOW_IDS, build_low_high_catalog
from tw_share_lots import BOARD_LOT
from within_sleeve_alloc import (
    FIN_EQUAL,
    FIN_PRE_EXDIV_KD,
    TEL_EQUAL,
    build_kd_season_tilt_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/kd-opt-indicator-assist"
RESEARCH = ROOT / "research/ops"
CAPITAL = 500_000_000.0
LOT = BOARD_LOT
TRAIL_ALERT_PP = 3.0
TRAIL_PAUSE_PP = 5.0
LIVE_KD = {
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


def sim(market, target, regime, dividends, *, scores, buy_ok, sell_ok=None):
    return simulate_core(
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
        fin_name_scores=scores,
        fin_buy_ok=buy_ok,
        fin_sell_ok=sell_ok,
    )


def and_panels(a: pd.DataFrame, b: pd.DataFrame) -> pd.DataFrame:
    out = a.copy()
    for c in out.columns:
        if c in b.columns:
            out[c] = out[c].fillna(False) & b[c].reindex(out.index).fillna(False)
    return out


def eval_row(
    *,
    book_id,
    mode,
    assist,
    nav_eq,
    win_eq,
    held_live,
    asof,
    market,
    target,
    regime,
    dividends,
    scores,
    buy_ok,
    sell_ok=None,
):
    nav, fills, meta = sim(
        market, target, regime, dividends, scores=scores, buy_ok=buy_ok, sell_ok=sell_ok
    )
    assert meta.get("exact_t1_ok"), book_id
    win = {w: window_stats(nav, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
    tip = tip_gate(nav_eq, nav, asof)
    held = score_vs_base(win_eq["heldout_2019_plus"], win["heldout_2019_plus"])
    tip_clean = tip["ytd"]["gate"] == "PASS" and tip["trailing_1y"]["gate"] == "PASS"
    return {
        "id": book_id,
        "mode": mode,
        "assist": assist,
        "heldout_score": float(held["score"]),
        "mdd_improve_pp": float(held["mdd_improve_pp"]),
        "cagr_giveback_pp": held["cagr_giveback_pp"],
        "tip_ytd": tip["ytd"]["gate"],
        "tip_1y": tip["trailing_1y"]["gate"],
        "tip_clean": tip_clean,
        "coexist": bool(tip_clean and held["score"] > 0),
        "vs_live_heldout_delta": float(held["score"] - held_live),
        "n_fills": int(len(fills)),
        "full_cagr": win["full"].get("cagr"),
        "full_mdd": win["full"].get("max_drawdown"),
    }


def rank_key(r: dict) -> tuple:
    beat = bool(
        r.get("coexist") and r.get("vs_live_heldout_delta", 0) > 0 and r["id"] != "LIVE_KD_OPT"
    )
    no_pause = r["tip_ytd"] != "PAUSE_REVIEW" and r["tip_1y"] != "PAUSE_REVIEW"
    return (1 if r.get("coexist") else 0, 1 if beat else 0, 1 if no_pause else 0, r["heldout_score"])


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.9]

    print("loading ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, _s, target, regime = e16_features(market)
    cal = pd.DatetimeIndex(pd.to_datetime(market["date"]).drop_duplicates().sort_values())

    print("EQUAL + LIVE_KD_OPT ...", flush=True)
    nav_eq, _, meta_eq = simulate_core(
        market,
        target,
        regime,
        dividends,
        apply_e22=True,
        apply_stock_div=True,
        capital=CAPITAL,
        lot_size=LOT,
        financial_alloc=FIN_EQUAL,
        telecom_alloc=TEL_EQUAL,
    )
    assert meta_eq.get("exact_t1_ok")
    win_eq = {w: window_stats(nav_eq, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
    asof = pd.to_datetime(nav_eq["date"]).max()

    kd_scores = build_kd_season_tilt_scores(
        market,
        dividends,
        FIN,
        k_thresh=float(LIVE_KD["k_thresh"]),
        season_start=LIVE_KD["season_start"],
        season_end=LIVE_KD["season_end"],
        pre_days=int(LIVE_KD["pre_days"]),
        active_score=float(LIVE_KD["active_score"]),
    )
    kd_ok = build_pre_exdiv_window_buy_ok(
        cal, dividends, FIN, pre_days=int(LIVE_KD["pre_days"]), also_stock_ex=True
    )
    nav_live, fills_live, meta_live = sim(
        market, target, regime, dividends, scores=kd_scores, buy_ok=kd_ok
    )
    assert meta_live.get("exact_t1_ok")
    win_live = {w: window_stats(nav_live, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
    held_live_stats = score_vs_base(win_eq["heldout_2019_plus"], win_live["heldout_2019_plus"])
    held_live = float(held_live_stats["score"])
    live_tip = tip_gate(nav_eq, nav_live, asof)

    rows = [
        {
            "id": "LIVE_KD_OPT",
            "mode": "base",
            "assist": "none",
            "heldout_score": held_live,
            "mdd_improve_pp": float(held_live_stats["mdd_improve_pp"]),
            "cagr_giveback_pp": held_live_stats["cagr_giveback_pp"],
            "tip_ytd": live_tip["ytd"]["gate"],
            "tip_1y": live_tip["trailing_1y"]["gate"],
            "tip_clean": live_tip["ytd"]["gate"] == "PASS" and live_tip["trailing_1y"]["gate"] == "PASS",
            "coexist": live_tip["ytd"]["gate"] == "PASS"
            and live_tip["trailing_1y"]["gate"] == "PASS"
            and held_live > 0,
            "vs_live_heldout_delta": 0.0,
            "n_fills": int(len(fills_live)),
            "full_cagr": win_live["full"].get("cagr"),
            "full_mdd": win_live["full"].get("max_drawdown"),
        }
    ]

    print("catalog ...", flush=True)
    lows, highs = build_low_high_catalog(market, cal, list(FIN))

    jobs = []
    for lid in LOW_IDS:
        jobs.append(
            (
                f"KD+BUY_AND_{lid}",
                "KD+BUY_AND_LOW",
                lid,
                and_panels(kd_ok, lows[lid]),
                None,
            )
        )
    for hid in HIGH_IDS:
        jobs.append(
            (
                f"KD+SELL_{hid}",
                "KD+SELL_HIGH",
                hid,
                kd_ok,
                highs[hid],
            )
        )
    for lid in LOW_IDS:
        for hid in HIGH_IDS:
            jobs.append(
                (
                    f"KD+BOTH__{lid}__{hid}",
                    "KD+BOTH",
                    f"{lid}+{hid}",
                    and_panels(kd_ok, lows[lid]),
                    highs[hid],
                )
            )

    total = len(jobs)
    print(f"running {total} assist books ...", flush=True)
    for i, (book_id, mode, assist, buy_ok, sell_ok) in enumerate(jobs, 1):
        if i == 1 or i % 25 == 0 or i == total:
            print(f"  [{i}/{total}] {book_id}", flush=True)
        rows.append(
            eval_row(
                book_id=book_id,
                mode=mode,
                assist=assist,
                nav_eq=nav_eq,
                win_eq=win_eq,
                held_live=held_live,
                asof=asof,
                market=market,
                target=target,
                regime=regime,
                dividends=dividends,
                scores=kd_scores,
                buy_ok=buy_ok,
                sell_ok=sell_ok,
            )
        )

    ranked = sorted(rows, key=rank_key, reverse=True)
    coexist = [r for r in ranked if r.get("coexist")]
    beat_live = [
        r
        for r in ranked
        if r.get("coexist") and r["id"] != "LIVE_KD_OPT" and r.get("vs_live_heldout_delta", 0) > 0
    ]
    near = [
        r
        for r in ranked
        if r["id"] != "LIVE_KD_OPT"
        and r.get("tip_clean")
        and r.get("vs_live_heldout_delta", -9) > -0.05
    ]

    verdict = (
        "ASSIST_BEATS_LIVE"
        if beat_live
        else (
            "ASSIST_NEAR_NO_BEAT"
            if near
            else ("ASSIST_COEXIST_NO_LIFT" if any(r["id"] != "LIVE_KD_OPT" for r in coexist) else "ASSIST_NO_LIFT")
        )
    )

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "KD_OPT_INDICATOR_ASSIST_SCREEN",
        "charter": "research/ops/KD_OPT_INDICATOR_ASSIST_CHARTER.md",
        "status": "PAPER_SCREEN_DONE",
        "live_wire": False,
        "asof": str(pd.Timestamp(asof).date()),
        "base": "LIVE_KD_OPT",
        "n_books": len(rows),
        "n_coexist": len(coexist),
        "n_beat_live": len(beat_live),
        "beat_live_ids": [r["id"] for r in beat_live[:40]],
        "near_ids": [r["id"] for r in near[:40]],
        "top20": [r["id"] for r in ranked[:20]],
        "verdict": verdict,
        "books": ranked,
        "non_actions": [
            "No Soft-Frozen flip",
            "No live KD_OPT change without ACCEPT",
            "No E45 stitch",
        ],
    }

    pd.DataFrame(ranked).to_csv(OUT / "reports" / "assist_scoreboard.csv", index=False)
    (OUT / "reports" / "kd_opt_indicator_assist_screen.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (RESEARCH / "KD_OPT_INDICATOR_ASSIST_SCREEN.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    def line(r):
        cagr = r["cagr_giveback_pp"]
        return (
            f"| `{r['id']}` | {r['mode']} | {r['tip_ytd']} | {r['tip_1y']} | "
            f"{r['heldout_score']:.3f} | {r['mdd_improve_pp']:.3f} | "
            f"{'—' if cagr is None else f'{cagr:.3f}'} | {r['vs_live_heldout_delta']:.3f} | "
            f"{'Y' if r.get('coexist') else ''} |"
        )

    lines = [
        "# KD_OPT + Indicator Assist Screen",
        "",
        f"Generated: `{payload['generated_at_utc']}` · asof **{payload['asof']}**",
        f"Charter: `KD_OPT_INDICATOR_ASSIST_CHARTER.md`",
        f"Verdict: **`{verdict}`**",
        "",
        "## Question",
        "",
        "Does adding low-buy / high-sell indicator **assists on top of LIVE_KD_OPT** beat plain live KD_OPT?",
        "",
        "## Summary",
        "",
        f"- Books: **{payload['n_books']}** (base + buy assists + sell assists + both cross)",
        f"- Coexist: **{payload['n_coexist']}**",
        f"- Beat live: **{payload['n_beat_live']}** → `{payload['beat_live_ids'][:15]}`",
        f"- Near (tip-clean, vs live Δ &gt; −0.05): `{payload['near_ids'][:15]}`",
        "",
        "## Top 20",
        "",
        "| ID | Mode | Tip YTD | Tip 1y | Held | MDDΔpp | CAGRΔpp | vs live Δ | Coexist |",
        "|---|---|---|---|---:|---:|---:|---:|:---:|",
    ]
    lines.extend(line(r) for r in ranked[:20])
    lines += [
        "",
        "## Reading",
        "",
        "- If beat-live empty → **no evidenced assist lift** in this catalog; keep live KD_OPT.",
        "- Soft assist / different thresholds would need a new OPEN.",
        "",
        "## Non-actions",
        "",
        "- No Soft-Frozen / live KD change / E45 stitch from this screen alone",
        "",
        "## Label",
        "",
        "`KD_OPT_INDICATOR_ASSIST_SCREEN_2026-09-10`",
        "",
    ]
    md = "\n".join(lines)
    (RESEARCH / "KD_OPT_INDICATOR_ASSIST_SCREEN.md").write_text(md, encoding="utf-8")
    (OUT / "reports" / "KD_OPT_INDICATOR_ASSIST_SCREEN.md").write_text(md, encoding="utf-8")
    print(
        json.dumps(
            {
                "verdict": verdict,
                "n_books": payload["n_books"],
                "n_beat_live": payload["n_beat_live"],
                "beat_live_ids": payload["beat_live_ids"][:20],
                "top10": payload["top20"][:10],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
