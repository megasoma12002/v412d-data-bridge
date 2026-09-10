#!/usr/bin/env python3
"""Round-2 indicator screen: BUY_LOW vs SELL_HIGH (PAPER ONLY).

Charter: research/ops/INDICATOR_BUY_SELL_SCREEN_R2_SPLIT_CHARTER.md

Track A — buy only when low signal (sells equal).
Track B — sell only when high signal (buys equal; no-high → skip sell).

Soft-Frozen KEEP · live wire false · no E45 stitch.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e16_soft_frozen_base as soft
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, load_market, window_stats
from e50_early_stack_combined_nav import FIN, e16_features, simulate_core
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp
from tw_share_lots import BOARD_LOT
from tw_yahoo_kd import yahoo_kd
from within_sleeve_alloc import (
    FIN_EQUAL,
    FIN_EXDIV_SKIP_BUY,
    FIN_PRE_EXDIV_KD,
    TEL_EQUAL,
    build_exdiv_buy_ok,
    build_kd_season_tilt_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/indicator-buy-sell-screen-r2-split"
RESEARCH = ROOT / "research/ops"

CAPITAL = 500_000_000.0
LOT = BOARD_LOT
TRAIL_ALERT_PP = 3.0
TRAIL_PAUSE_PP = 5.0
LIVE_KD = {
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


def sim(
    market,
    target,
    regime,
    dividends,
    *,
    policy,
    scores=None,
    buy_ok=None,
    sell_ok=None,
    sell_scores=None,
):
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
        fin_sell_ok=sell_ok,
        fin_sell_scores=sell_scores,
    )


def build_rsi(close: pd.Series, n: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)
    avg_gain = gain.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    avg_loss = loss.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    return 100.0 - (100.0 / (1.0 + rs))


def bool_panel(cal: pd.DatetimeIndex, codes: list[str]) -> pd.DataFrame:
    return pd.DataFrame(False, index=cal, columns=list(codes))


def build_low_high_panels(market: pd.DataFrame, cal: pd.DatetimeIndex, codes: list[str]):
    m = market.copy()
    m["date"] = pd.to_datetime(m["date"])
    m["code"] = m["code"].astype(str)
    lows = {
        "RSI14_LT30": bool_panel(cal, codes),
        "BB_LOWER": bool_panel(cal, codes),
        "K9_LT30": bool_panel(cal, codes),
        "BELOW_MA60": bool_panel(cal, codes),
    }
    highs = {
        "RSI14_GT70": bool_panel(cal, codes),
        "BB_UPPER": bool_panel(cal, codes),
        "K9_GT70": bool_panel(cal, codes),
        "ABOVE_MA20": bool_panel(cal, codes),
    }
    for c in codes:
        g = (
            m[m["code"] == c]
            .sort_values("date")
            .drop_duplicates("date")
            .set_index("date")
            .reindex(cal)
        )
        close = pd.to_numeric(g["close"], errors="coerce")
        high = pd.to_numeric(g["high"], errors="coerce").fillna(close)
        low = pd.to_numeric(g["low"], errors="coerce").fillna(close)
        rsi = build_rsi(close, 14)
        mid = close.rolling(20, min_periods=20).mean()
        sd = close.rolling(20, min_periods=20).std()
        ma20 = close.rolling(20, min_periods=20).mean()
        ma60 = close.rolling(60, min_periods=60).mean()
        kd = yahoo_kd(high, low, close, n=9)["k"]
        lows["RSI14_LT30"][c] = (rsi < 30.0).fillna(False)
        lows["BB_LOWER"][c] = (close < (mid - 2.0 * sd)).fillna(False)
        lows["K9_LT30"][c] = (kd < 30.0).fillna(False)
        lows["BELOW_MA60"][c] = (close < ma60).fillna(False)
        highs["RSI14_GT70"][c] = (rsi > 70.0).fillna(False)
        highs["BB_UPPER"][c] = (close > (mid + 2.0 * sd)).fillna(False)
        highs["K9_GT70"][c] = (kd > 70.0).fillna(False)
        highs["ABOVE_MA20"][c] = (close > ma20).fillna(False)
    return lows, highs


def and_buy_ok(signal: pd.DataFrame, ex_ok: pd.DataFrame) -> pd.DataFrame:
    out = signal.copy()
    for c in out.columns:
        if c in ex_ok.columns:
            out[c] = out[c] & ex_ok[c].reindex(out.index).fillna(True)
    return out


def rank_key(row: dict) -> tuple:
    tip = row["tip_gates"]
    tip_clean = tip["ytd"]["gate"] == "PASS" and tip["trailing_1y"]["gate"] == "PASS"
    no_pause = tip["ytd"]["gate"] != "PAUSE_REVIEW" and tip["trailing_1y"]["gate"] != "PAUSE_REVIEW"
    held = row["heldout"]["score"]
    beat = bool(row.get("coexist") and (row.get("vs_live_heldout_score_delta") or 0) > 0 and row["id"] != "LIVE_KD_OPT")
    return (1 if tip_clean and held > 0 else 0, 1 if beat else 0, 1 if no_pause else 0, held)


def eval_book(
    *,
    book_id: str,
    track: str,
    nav_eq,
    win_eq,
    nav_live,
    held_live,
    asof,
    market,
    target,
    regime,
    dividends,
    policy,
    scores=None,
    buy_ok=None,
    sell_ok=None,
):
    nav, fills, meta = sim(
        market,
        target,
        regime,
        dividends,
        policy=policy,
        scores=scores,
        buy_ok=buy_ok,
        sell_ok=sell_ok,
    )
    assert meta.get("exact_t1_ok"), book_id
    win = {w: window_stats(nav, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
    tip = tip_gate(nav_eq, nav, asof)
    held = score_vs_base(win_eq["heldout_2019_plus"], win["heldout_2019_plus"])
    tip_clean = tip["ytd"]["gate"] == "PASS" and tip["trailing_1y"]["gate"] == "PASS"
    return {
        "id": book_id,
        "track": track,
        "heldout": held,
        "tip_gates": tip,
        "tip_clean": tip_clean,
        "coexist": bool(tip_clean and held["score"] > 0),
        "vs_live_heldout_score_delta": float(held["score"] - held_live),
        "tip_gates_vs_live": tip_gate(nav_live, nav, asof),
        "n_fills": int(len(fills)),
        "full_cagr": win["full"].get("cagr"),
        "full_mdd": win["full"].get("max_drawdown"),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "outputs").mkdir(exist_ok=True)
    (OUT / "reports").mkdir(exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.9]

    print("loading ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, _s, target, regime = e16_features(market)
    cal = pd.DatetimeIndex(pd.to_datetime(market["date"]).drop_duplicates().sort_values())

    print("anchors EQUAL + LIVE_KD_OPT ...", flush=True)
    nav_eq, _, meta_eq = sim(market, target, regime, dividends, policy=FIN_EQUAL)
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
    nav_live, _, meta_live = sim(
        market,
        target,
        regime,
        dividends,
        policy=FIN_PRE_EXDIV_KD,
        scores=kd_scores,
        buy_ok=kd_ok,
    )
    assert meta_live.get("exact_t1_ok")
    win_live = {w: window_stats(nav_live, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
    held_live = score_vs_base(win_eq["heldout_2019_plus"], win_live["heldout_2019_plus"])["score"]
    live_tip = tip_gate(nav_eq, nav_live, asof)

    rows = [
        {
            "id": "FIN_EQUAL",
            "track": "anchor",
            "heldout": {"mdd_improve_pp": 0.0, "cagr_giveback_pp": 0.0, "score": 0.0},
            "tip_gates": {
                "ytd": {"gate": "PASS", "giveback_pp": 0.0, "rel_nav": 1.0},
                "trailing_1y": {"gate": "PASS", "giveback_pp": 0.0, "rel_nav": 1.0},
            },
            "tip_clean": True,
            "coexist": False,
            "vs_live_heldout_score_delta": float(0.0 - held_live),
            "tip_gates_vs_live": tip_gate(nav_live, nav_eq, asof),
            "n_fills": None,
            "full_cagr": win_eq["full"].get("cagr"),
            "full_mdd": win_eq["full"].get("max_drawdown"),
        },
        {
            "id": "LIVE_KD_OPT",
            "track": "anchor",
            "heldout": score_vs_base(win_eq["heldout_2019_plus"], win_live["heldout_2019_plus"]),
            "tip_gates": live_tip,
            "tip_clean": live_tip["ytd"]["gate"] == "PASS" and live_tip["trailing_1y"]["gate"] == "PASS",
            "coexist": live_tip["ytd"]["gate"] == "PASS"
            and live_tip["trailing_1y"]["gate"] == "PASS"
            and held_live > 0,
            "vs_live_heldout_score_delta": 0.0,
            "tip_gates_vs_live": tip_gate(nav_live, nav_live, asof),
            "n_fills": None,
            "full_cagr": win_live["full"].get("cagr"),
            "full_mdd": win_live["full"].get("max_drawdown"),
        },
    ]

    print("building low/high panels ...", flush=True)
    lows, highs = build_low_high_panels(market, cal, list(FIN))
    ex_ok = build_exdiv_buy_ok(cal, dividends, FIN, also_stock_ex=True)

    # Track A: BUY_LOW — equal buy among low names only; equal sells
    for name, panel in lows.items():
        book_id = f"BUY_LOW_{name}"
        print(f"{book_id} ...", flush=True)
        buy_ok = and_buy_ok(panel, ex_ok)
        rows.append(
            eval_book(
                book_id=book_id,
                track="BUY_LOW",
                nav_eq=nav_eq,
                win_eq=win_eq,
                nav_live=nav_live,
                held_live=held_live,
                asof=asof,
                market=market,
                target=target,
                regime=regime,
                dividends=dividends,
                policy=FIN_EXDIV_SKIP_BUY,
                buy_ok=buy_ok,
            )
        )

    # Track B: SELL_HIGH — equal buys; sell only high names (else skip)
    for name, panel in highs.items():
        book_id = f"SELL_HIGH_{name}"
        print(f"{book_id} ...", flush=True)
        rows.append(
            eval_book(
                book_id=book_id,
                track="SELL_HIGH",
                nav_eq=nav_eq,
                win_eq=win_eq,
                nav_live=nav_live,
                held_live=held_live,
                asof=asof,
                market=market,
                target=target,
                regime=regime,
                dividends=dividends,
                policy=FIN_EXDIV_SKIP_BUY,  # Stage C path enables sell_ok
                buy_ok=ex_ok,  # buys allowed except ex-day
                sell_ok=panel,
            )
        )

    ranked = sorted(rows, key=rank_key, reverse=True)
    by_track = {
        "BUY_LOW": [r for r in ranked if r["track"] == "BUY_LOW"],
        "SELL_HIGH": [r for r in ranked if r["track"] == "SELL_HIGH"],
    }
    coexist = [r for r in ranked if r.get("coexist")]
    beat_live = [
        r
        for r in ranked
        if r.get("coexist")
        and r["id"] != "LIVE_KD_OPT"
        and (r.get("vs_live_heldout_score_delta") or 0) > 0
    ]

    verdict = (
        "PROMOTE_CANDIDATE_TO_DUAL_PAPER"
        if beat_live
        else ("COEXIST_NO_LIFT_VS_LIVE" if coexist else "NO_COEXIST_STOP_OR_AUTOPSY")
    )
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "INDICATOR_BUY_SELL_SCREEN_R2_SPLIT",
        "charter": "research/ops/INDICATOR_BUY_SELL_SCREEN_R2_SPLIT_CHARTER.md",
        "status": "PAPER_SCREEN_DONE",
        "live_wire": False,
        "soft_frozen_clip": soft.SOFT_FROZEN_FIN_CLIP,
        "asof": str(pd.Timestamp(asof).date()),
        "design": {
            "BUY_LOW": "buy only when low signal (AND ex-day skip); sells equal",
            "SELL_HIGH": "sell only when high signal; empty high pool → skip sell; buys equal except ex-day",
        },
        "n_books": len(rows),
        "n_coexist": len(coexist),
        "n_beat_live": len(beat_live),
        "coexist_ids": [r["id"] for r in coexist],
        "beat_live_ids": [r["id"] for r in beat_live],
        "best_buy_low": by_track["BUY_LOW"][0]["id"] if by_track["BUY_LOW"] else None,
        "best_sell_high": by_track["SELL_HIGH"][0]["id"] if by_track["SELL_HIGH"] else None,
        "ranking": [r["id"] for r in ranked],
        "books": ranked,
        "verdict": verdict,
        "non_actions": [
            "No Soft-Frozen flip",
            "No live KD_OPT change",
            "No E45 stitch",
            "No auto cutover",
            "No A+B combine until Round-3 human OPEN",
        ],
    }

    (OUT / "reports" / "indicator_buy_sell_screen_r2_split.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (RESEARCH / "INDICATOR_BUY_SELL_SCREEN_R2_SPLIT.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    def row_line(r: dict) -> str:
        tip = r["tip_gates"]
        h = r["heldout"]
        return (
            f"| `{r['id']}` | {r['track']} | {tip['ytd']['gate']} | {tip['trailing_1y']['gate']} | "
            f"{h['score']:.3f} | {h['mdd_improve_pp']:.3f} | "
            f"{'—' if h['cagr_giveback_pp'] is None else f'{h['cagr_giveback_pp']:.3f}'} | "
            f"{r['vs_live_heldout_score_delta']:.3f} | {'Y' if r.get('coexist') else ''} |"
        )

    lines = [
        "# Indicator Buy/Sell Screen — Round 2 (Buy-Low vs Sell-High)",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Asof: **{payload['asof']}** · Soft-Frozen **{soft.SOFT_FROZEN_FIN_CLIP}** KEEP",
        f"Charter: `INDICATOR_BUY_SELL_SCREEN_R2_SPLIT_CHARTER.md`",
        f"Verdict: **`{verdict}`**",
        "",
        "## Design",
        "",
        "- **BUY_LOW**: only buy when low signal (RSI&lt;30 / BB lower / K9&lt;30 / below MA60); sells equal.",
        "- **SELL_HIGH**: only sell when high signal (RSI&gt;70 / BB upper / K9&gt;70 / above MA20); else **hold**.",
        "",
        "## Summary",
        "",
        f"- Coexist: **{payload['n_coexist']}** → `{payload['coexist_ids']}`",
        f"- Beat live KD_OPT: **{payload['n_beat_live']}** → `{payload['beat_live_ids']}`",
        f"- Best BUY_LOW rank: `{payload['best_buy_low']}`",
        f"- Best SELL_HIGH rank: `{payload['best_sell_high']}`",
        "",
        "## Scoreboard (held-out vs FIN_EQUAL)",
        "",
        "| ID | Track | Tip YTD | Tip 1y | Held score | MDDΔpp | CAGRΔpp | vs live held Δ | Coexist |",
        "|---|---|---|---|---:|---:|---:|---:|:---:|",
    ]
    lines.extend(row_line(r) for r in ranked)
    lines += [
        "",
        "## Reading",
        "",
        "- Tracks are **separate**; do not stitch buy+sell winners without Round-3 OPEN.",
        "- Empty beat-live → keep live KD_OPT.",
        "",
        "## Non-actions",
        "",
        "- No Soft-Frozen / KD_OPT / TEL live change · no E45 stitch · no auto cutover",
        "",
        "## Label",
        "",
        "`INDICATOR_BUY_SELL_SCREEN_R2_SPLIT_2026-09-10`",
        "",
    ]
    md = "\n".join(lines)
    (RESEARCH / "INDICATOR_BUY_SELL_SCREEN_R2_SPLIT.md").write_text(md, encoding="utf-8")
    (OUT / "reports" / "INDICATOR_BUY_SELL_SCREEN_R2_SPLIT.md").write_text(md, encoding="utf-8")
    print(
        json.dumps(
            {
                "verdict": verdict,
                "coexist": payload["coexist_ids"],
                "beat_live": payload["beat_live_ids"],
                "best_buy_low": payload["best_buy_low"],
                "best_sell_high": payload["best_sell_high"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
