#!/usr/bin/env python3
"""Stage A paper: Soft KD / Bollinger buy soft-score sensitivity (NO hard AND).

Human ask (2026-09-11): try the reasonable versions —
  1) Soft add-score: K9 low and/or BB lower each add weight (never hard-block buys).
  2) Sensitivity on Soft-assist champion: add BB_LOWER as second buy soft (small alpha).
  3) Skip KD∩BB hard-AND buy gates (already ASSIST_NO_LIFT / R3 fail).

Baseline LIVE_KD_OPT. Soft-Frozen KEEP · TEL_EQUAL KEEP · Soft-assist observe UNCHANGED · no live wire.
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
from portfolio_capital import DEFAULT_CAPITAL
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp
from soft_assist_helpers import (
    BUY_LOW_ID,
    CHAMPION_ID,
    LIVE_KD,
    SELL_HIGH_ID,
    SOFT_BOOST,
    soft_boost_scores,
    soft_sell_panel,
)
from ta_indicator_catalog import build_low_high_catalog
from tw_share_lots import BOARD_LOT
from within_sleeve_alloc import (
    FIN_PRE_EXDIV_KD,
    TEL_EQUAL,
    build_kd_season_tilt_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/soft-kd-bb-sensitivity"
OPS = ROOT / "research/ops"
CAPITAL = float(DEFAULT_CAPITAL)
LOT = BOARD_LOT
TRAIL_ALERT_PP = 3.0
TRAIL_PAUSE_PP = 5.0
BASE_ID = "LIVE_KD_OPT"


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


def held_score(base_stats: dict, chal_stats: dict) -> dict:
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


def run_kd(market, target, regime, dividends, *, scores, buy_ok, sell_scores=None):
    nav, fills, meta = simulate_core(
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
        fin_sell_scores=sell_scores,
    )
    assert meta.get("exact_t1_ok")
    return {"nav": nav, "n_fills": int(len(fills)), "meta": meta}


def add_buy_softs(kd_scores: pd.DataFrame, lows: dict, specs: list[tuple[str, float]]) -> pd.DataFrame:
    out = kd_scores.astype(float)
    for lid, boost in specs:
        out = soft_boost_scores(out, lows[lid], float(boost))
    return out


def main() -> int:
    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    OPS.mkdir(parents=True, exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.9]
    import e21_forward_pipeline as e21

    for k in ("season_start", "season_end", "k_thresh", "pre_days", "active_score"):
        if LIVE_KD[k] != e21.KD_OPT[k]:
            raise SystemExit(f"LIVE_KD[{k}] drift vs e21.KD_OPT")
    if e21.LIVE_E45_STITCH:
        raise SystemExit("Refuse screen while LIVE_E45_STITCH is True")

    print("loading ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, _s, target, regime = e16_features(market)
    cal = pd.DatetimeIndex(pd.to_datetime(market["date"]).drop_duplicates().sort_values())
    lows, highs = build_low_high_catalog(market, cal, list(FIN))

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
    sell_rsi6 = soft_sell_panel(highs[SELL_HIGH_ID], boost=SOFT_BOOST)

    jobs: list[tuple[str, str, list[tuple[str, float]], bool]] = [
        (BASE_ID, "base", [], False),
        (CHAMPION_ID, "champion", [(BUY_LOW_ID, SOFT_BOOST)], True),
        ("SOFT_BUY_K9_LT30__SELL_RSI6", "soft_or", [("K9_LT30", 1.0)], True),
        ("SOFT_BUY_K9_LT20__SELL_RSI6", "soft_or", [("K9_LT20", 1.0)], True),
        ("SOFT_BUY_BB_LOWER__SELL_RSI6", "soft_or", [("BB_LOWER", 1.0)], True),
        ("SOFT_BUY_BB_PCTB_LT0__SELL_RSI6", "soft_or", [("BB_PCTB_LT0", 1.0)], True),
        ("SOFT_BUY_K9_LT30_OR_BB_LOWER_a10__SELL_RSI6", "soft_or", [("K9_LT30", 1.0), ("BB_LOWER", 1.0)], True),
        ("SOFT_BUY_K9_LT30_OR_BB_LOWER_a05__SELL_RSI6", "soft_or", [("K9_LT30", 0.5), ("BB_LOWER", 0.5)], True),
        ("SOFT_BUY_K9_LT30_OR_BB_LOWER_a025__SELL_RSI6", "soft_or", [("K9_LT30", 0.25), ("BB_LOWER", 0.25)], True),
        ("SOFT_CHAMP_PLUS_BB_LOWER_a025", "champ_sens", [(BUY_LOW_ID, 1.0), ("BB_LOWER", 0.25)], True),
        ("SOFT_CHAMP_PLUS_BB_LOWER_a05", "champ_sens", [(BUY_LOW_ID, 1.0), ("BB_LOWER", 0.5)], True),
        ("SOFT_CHAMP_PLUS_BB_LOWER_a10", "champ_sens", [(BUY_LOW_ID, 1.0), ("BB_LOWER", 1.0)], True),
        ("SOFT_CHAMP_PLUS_BB_PCTB_LT0_a05", "champ_sens", [(BUY_LOW_ID, 1.0), ("BB_PCTB_LT0", 0.5)], True),
        ("SOFT_CHAMP_PLUS_BB_PCTB_LT0_a10", "champ_sens", [(BUY_LOW_ID, 1.0), ("BB_PCTB_LT0", 1.0)], True),
        ("SOFT_CHAMP_PLUS_K9_LT30_a05", "champ_sens", [(BUY_LOW_ID, 1.0), ("K9_LT30", 0.5)], True),
        ("SOFT_CHAMP_PLUS_K9_LT30_a10", "champ_sens", [(BUY_LOW_ID, 1.0), ("K9_LT30", 1.0)], True),
    ]

    print(f"Stage A books: {len(jobs)} (hard-AND forbidden)", flush=True)
    nav_base = None
    win_base = None
    asof = None
    rows: list[dict] = []

    for i, (book_id, track, buy_specs, use_sell) in enumerate(jobs, 1):
        print(f"  [{i}/{len(jobs)}] {book_id}", flush=True)
        if not buy_specs:
            scores = kd_scores
            sell = None
        else:
            scores = add_buy_softs(kd_scores, lows, buy_specs)
            sell = sell_rsi6 if use_sell else None
        res = run_kd(
            market, target, regime, dividends, scores=scores, buy_ok=kd_ok, sell_scores=sell
        )
        win = {w: window_stats(res["nav"], a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
        if book_id == BASE_ID:
            nav_base = res["nav"]
            win_base = win
            asof = pd.to_datetime(res["nav"]["date"]).max()
            tip = tip_gate(nav_base, nav_base, asof)
            held = {"mdd_improve_pp": 0.0, "cagr_giveback_pp": 0.0, "score": 0.0}
        else:
            tip = tip_gate(nav_base, res["nav"], asof)
            held = held_score(win_base["heldout_2019_plus"], win["heldout_2019_plus"])
        tip_clean = tip["ytd"]["gate"] == "PASS" and tip["trailing_1y"]["gate"] == "PASS"
        coexist = bool(tip_clean and held["score"] > 0)
        rows.append(
            {
                "id": book_id,
                "track": track,
                "buy_soft": "+".join(f"{a}@{b:g}" for a, b in buy_specs) if buy_specs else "none",
                "sell_soft": SELL_HIGH_ID if use_sell else "none",
                "heldout_score": float(held["score"]),
                "mdd_improve_pp": float(held["mdd_improve_pp"]),
                "cagr_giveback_pp": held["cagr_giveback_pp"],
                "tip_ytd": tip["ytd"]["gate"],
                "tip_1y": tip["trailing_1y"]["gate"],
                "tip_clean": tip_clean,
                "coexist": coexist,
                "vs_live_heldout_delta": float(held["score"]),
                "full_cagr": win["full"].get("cagr"),
                "full_mdd": win["full"].get("max_drawdown"),
                "heldout_cagr": win["heldout_2019_plus"].get("cagr"),
                "heldout_mdd": win["heldout_2019_plus"].get("max_drawdown"),
                "sealed_cagr": win["sealed_2023_plus"].get("cagr"),
                "sealed_mdd": win["sealed_2023_plus"].get("max_drawdown"),
                "n_fills": int(res["n_fills"]),
                "is_champion": book_id == CHAMPION_ID,
            }
        )

    def rank_key(r):
        beat = bool(r.get("coexist") and r["id"] != BASE_ID and r["vs_live_heldout_delta"] > 0)
        return (1 if r.get("coexist") else 0, 1 if beat else 0, r["heldout_score"])

    ranked = sorted(rows, key=rank_key, reverse=True)
    beat = [
        r for r in ranked if r["id"] != BASE_ID and r.get("coexist") and r["vs_live_heldout_delta"] > 0
    ]
    champ = next(r for r in ranked if r["id"] == CHAMPION_ID)
    beat_vs_champ = [
        r
        for r in ranked
        if r["id"] not in (BASE_ID, CHAMPION_ID)
        and r.get("tip_clean")
        and r["heldout_score"] > champ["heldout_score"]
    ]
    if beat_vs_champ:
        verdict = "BEATS_CHAMPION"
    elif beat:
        verdict = "BEATS_LIVE_NO_CHAMP_LIFT"
    elif any(r.get("tip_clean") and r["id"] != BASE_ID for r in ranked):
        verdict = "NEAR_NO_LIFT"
    else:
        verdict = "NO_LIFT"

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "SOFT_KD_BB_SENSITIVITY_SCREEN_STAGE_A",
        "status": "PAPER_SCREEN_DONE",
        "live_wire": False,
        "hard_and_forbidden": True,
        "asof": str(pd.Timestamp(asof).date()),
        "n_books": len(rows),
        "verdict": verdict,
        "n_beat_live": len(beat),
        "n_beat_champion": len(beat_vs_champ),
        "beat_live_ids": [r["id"] for r in beat],
        "beat_champion_ids": [r["id"] for r in beat_vs_champ],
        "champion_id": CHAMPION_ID,
        "champion_heldout_score": champ["heldout_score"],
        "top_ids": [r["id"] for r in ranked[:12]],
        "books": ranked,
        "non_actions": [
            "No hard AND KD∩BB buy gate",
            "No Soft-assist observe replace",
            "No live Soft-assist / KD / Soft-Frozen wire",
            "No E45 stitch",
        ],
    }

    pd.DataFrame(ranked).to_csv(OUT / "reports" / "scoreboard.csv", index=False)
    blob = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    (OUT / "reports" / "soft_kd_bb_sensitivity_screen.json").write_text(blob, encoding="utf-8")
    (OPS / "SOFT_KD_BB_SENSITIVITY_SCREEN.json").write_text(blob, encoding="utf-8")

    def pct(x):
        return "—" if x is None else f"{100 * float(x):.2f}%"

    def line(r):
        return (
            f"| `{r['id']}` | {r['track']} | {r['tip_ytd']} | {r['tip_1y']} | "
            f"{r['heldout_score']:.3f} | {r['mdd_improve_pp']:.3f} | "
            f"{pct(r['heldout_cagr'])} | {pct(r['heldout_mdd'])} | "
            f"{pct(r['sealed_cagr'])} | {pct(r['sealed_mdd'])} |"
        )

    lines = [
        "# Soft KD / Bollinger Sensitivity Screen — Stage A",
        "",
        f"Generated: `{payload['generated_at_utc']}` · asof **{payload['asof']}**",
        f"Verdict: **`{verdict}`** · books **{payload['n_books']}** · hard-AND **forbidden**",
        "",
        "## Question",
        "",
        "Do soft (non-blocking) KD-low / BB-lower buy score adds — alone or as second soft on Soft-assist champion — tip-clean beat `LIVE_KD_OPT` or lift the Soft-assist champion?",
        "",
        "## Summary",
        "",
        f"- Beat live: **{payload['n_beat_live']}** → `{payload['beat_live_ids']}`",
        f"- Beat Soft-assist champion: **{payload['n_beat_champion']}** → `{payload['beat_champion_ids']}`",
        f"- Champion `{CHAMPION_ID}` held score: **{champ['heldout_score']:.3f}**",
        "",
        "## Top 12",
        "",
        "| ID | Track | Tip YTD | Tip 1y | Held score | MDDΔpp | Held CAGR | Held MDD | Sealed CAGR | Sealed MDD |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    lines.extend(line(r) for r in ranked[:12])
    lines += [
        "",
        "## Reading",
        "",
        "- Soft OR = additive score boosts (both can fire); **not** boolean AND buy gate.",
        "- Champion sensitivity keeps Soft-assist buy `BELOW_MA120` + sell `RSI6_GT80`, adds BB/K soft.",
        "- Soft-assist observe / live KD unchanged from this screen alone.",
        "",
        "## Non-actions",
        "",
        "- No hard AND · no Soft-assist observe swap · no live wire · no Soft-Frozen / E45 change",
        "",
        "## Label",
        "",
        f"`SOFT_KD_BB_SENSITIVITY_SCREEN_STAGE_A_2026-09-11__{verdict}`",
        "",
    ]
    md = "\n".join(lines)
    (OPS / "SOFT_KD_BB_SENSITIVITY_SCREEN.md").write_text(md, encoding="utf-8")
    (OUT / "reports" / "SOFT_KD_BB_SENSITIVITY_SCREEN.md").write_text(md, encoding="utf-8")
    zh = "\n".join(
        [
            "# Soft KD／布林敏感性 Screen — Stage A（paper）",
            "",
            f"產生：`{payload['generated_at_utc']}` · asof **{payload['asof']}**",
            f"總評：**`{verdict}`** · books **{payload['n_books']}** · **禁止硬 AND**",
            f"- 勝 live：**{payload['n_beat_live']}** → `{payload['beat_live_ids'][:8]}`",
            f"- 勝 Soft-assist 冠軍：**{payload['n_beat_champion']}** → `{payload['beat_champion_ids'][:8]}`",
            "",
            "軟加分（KD低／布林下軌），不是硬擋買。Soft-assist observe／live **KEEP**。",
            "",
            "英文：`SOFT_KD_BB_SENSITIVITY_SCREEN.md`",
            "",
        ]
    )
    (OPS / "SOFT_KD_BB_SENSITIVITY_SCREEN.zh-TW.md").write_text(zh, encoding="utf-8")

    print(
        json.dumps(
            {
                "verdict": verdict,
                "n_books": payload["n_books"],
                "n_beat_live": payload["n_beat_live"],
                "n_beat_champion": payload["n_beat_champion"],
                "beat_live_ids": payload["beat_live_ids"],
                "beat_champion_ids": payload["beat_champion_ids"],
                "top8": payload["top_ids"][:8],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
