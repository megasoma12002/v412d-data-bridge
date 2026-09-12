#!/usr/bin/env python3
"""Stage A paper: borrow-informed Soft amplitude + Sleeve desensitize (NO fuse).

Borrow map (EXTERNAL_BORROW_NOTES / recent Soft∥Sleeve rounds):
  Note 2 — Soft: finer additive amplitude around observe K9+ (assist, don't replace).
  Note 3 — Sleeve: lower α / neighbor signals; tip MDD hygiene clears Gate-E style ALERTs.
  Notes 4/5 — Soft × Sleeve stay independent; no auto-combo.

Baselines: Soft vs LIVE_KD_OPT · Sleeve vs LIVE_STACK.
Live Soft-Frozen / KD_OPT / TEL_EQUAL / dual observe / E45 OFF UNCHANGED.
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
from portfolio_capital import DEFAULT_CAPITAL
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp
from soft_assist_helpers import (
    BUY_LOW_ID,
    CHAMPION_ID,
    LIVE_KD,
    OBSERVE_CHAL_ID,
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
OUT = ROOT / "repro/soft-sleeve-borrow-promote"
OPS = ROOT / "research/ops"
CAPITAL = float(DEFAULT_CAPITAL)
LOT = BOARD_LOT
TRAIL_ALERT_PP = 3.0
TRAIL_PAUSE_PP = 5.0
SOFT_BASE = "LIVE_KD_OPT"
SLEEVE_BASE = "LIVE_STACK"
SLEEVE_SEED = "SLEEVE_BELOW_MA60_a01"


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
            out[wname] = {
                "giveback_pp": None,
                "gate": "INSUFFICIENT",
                "mdd_improve_pp": None,
                "rel_nav": None,
            }
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
        b_mdd = float((bn / bn.cummax() - 1.0).min())
        c_mdd = float((cn / cn.cummax() - 1.0).min())
        out[wname] = {
            "giveback_pp": None if gb is None else float(gb),
            "gate": gate,
            "mdd_improve_pp": float(mdd_delta_pp(b_mdd, c_mdd)),
            "rel_nav": float(cn.iloc[-1] / bn.iloc[-1]),
        }
    return out


def tip_mdd_clean(tip: dict) -> bool:
    for w in ("ytd", "trailing_1y"):
        md = tip.get(w, {}).get("mdd_improve_pp")
        if md is None or float(md) < 0.0:
            return False
    return True


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


def rebuild_targets_from_score(score: pd.DataFrame, regime: pd.Series) -> pd.DataFrame:
    out = []
    cur = soft.START_WEIGHTS.copy()
    for i, _dt in enumerate(score.index):
        pri = soft.REGIME_PRIORS[str(regime.iloc[i])]
        cand = np.maximum(pri + 0.10 * np.clip(score.iloc[i].to_numpy(), -2.0, 2.0), 0.0)
        cand = soft.apply_soft_frozen_clips(cand)
        desired = soft.BLEND_OLD * cur + soft.BLEND_NEW * cand
        if float(np.abs(desired - cur).sum()) >= soft.REBALANCE_L1_MIN:
            cur = desired
        out.append(cur.copy())
    return pd.DataFrame(out, index=score.index, columns=["Financial", "Telecom", "0050"])


def sleeve_signal_panel(sleeve_rets: pd.DataFrame, kind: str, window: int) -> pd.DataFrame:
    nav = (1.0 + sleeve_rets.fillna(0.0)).cumprod()
    out = pd.DataFrame(0.0, index=sleeve_rets.index, columns=list(sleeve_rets.columns))
    for col in sleeve_rets.columns:
        close = nav[col]
        if kind == "ma":
            min_p = max(20, window // 2)
            ma = close.rolling(window, min_periods=min_p).mean()
            out[col] = (close < ma).astype(float)
        elif kind == "rsi_lt30":
            delta = close.diff()
            gain = delta.clip(lower=0.0)
            loss = (-delta).clip(lower=0.0)
            avg_gain = gain.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
            avg_loss = loss.ewm(alpha=1 / window, adjust=False, min_periods=window).mean()
            rs = avg_gain / avg_loss.replace(0.0, np.nan)
            rsi = 100.0 - (100.0 / (1.0 + rs))
            out[col] = (rsi < 30.0).astype(float)
        else:
            raise ValueError(kind)
    return out.fillna(0.0)


def alpha_tag(a: float) -> str:
    return str(a).replace(".", "")


def book_row(*, book_id, track, tip, held, win, n_fills, extra=None):
    tip_clean = tip["ytd"]["gate"] == "PASS" and tip["trailing_1y"]["gate"] == "PASS"
    mdd_ok = tip_mdd_clean(tip)
    row = {
        "id": book_id,
        "track": track,
        "heldout_score": float(held["score"]),
        "mdd_improve_pp": float(held["mdd_improve_pp"]),
        "cagr_giveback_pp": held["cagr_giveback_pp"],
        "tip_ytd": tip["ytd"]["gate"],
        "tip_1y": tip["trailing_1y"]["gate"],
        "tip_clean": tip_clean,
        "tip_mdd_ytd_pp": tip["ytd"].get("mdd_improve_pp"),
        "tip_mdd_1y_pp": tip["trailing_1y"].get("mdd_improve_pp"),
        "tip_mdd_clean": mdd_ok,
        "promote_shaped": bool(tip_clean and mdd_ok and held["score"] > 0),
        "coexist": bool(tip_clean and held["score"] > 0),
        "full_cagr": win["full"].get("cagr"),
        "full_mdd": win["full"].get("max_drawdown"),
        "heldout_cagr": win["heldout_2019_plus"].get("cagr"),
        "heldout_mdd": win["heldout_2019_plus"].get("max_drawdown"),
        "sealed_cagr": win["sealed_2023_plus"].get("cagr"),
        "sealed_mdd": win["sealed_2023_plus"].get("max_drawdown"),
        "n_fills": int(n_fills),
    }
    if extra:
        row.update(extra)
    return row


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
    _prices, sleeve, target_live, regime = e16_features(market)
    _p, _s, _t, _r, base_score = soft.build_soft_frozen_targets(market)
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
    sell_panels = {
        0.5: soft_sell_panel(highs[SELL_HIGH_ID], boost=0.5),
        1.0: soft_sell_panel(highs[SELL_HIGH_ID], boost=SOFT_BOOST),
        1.5: soft_sell_panel(highs[SELL_HIGH_ID], boost=1.5),
    }

    soft_jobs: list[tuple[str, list[tuple[str, float]], float | None]] = [
        (SOFT_BASE, [], None),
        (CHAMPION_ID, [(BUY_LOW_ID, SOFT_BOOST)], 1.0),
        (OBSERVE_CHAL_ID, [(BUY_LOW_ID, 1.0), ("K9_LT30", 1.0)], 1.0),
        ("SOFT_CHAMP_PLUS_K9_LT30_a025", [(BUY_LOW_ID, 1.0), ("K9_LT30", 0.25)], 1.0),
        ("SOFT_CHAMP_PLUS_K9_LT30_a05", [(BUY_LOW_ID, 1.0), ("K9_LT30", 0.5)], 1.0),
        ("SOFT_CHAMP_PLUS_K9_LT30_a075", [(BUY_LOW_ID, 1.0), ("K9_LT30", 0.75)], 1.0),
        ("SOFT_CHAMP_PLUS_K9_LT30_a125", [(BUY_LOW_ID, 1.0), ("K9_LT30", 1.25)], 1.0),
        ("SOFT_CHAMP_PLUS_K9_LT30_a15", [(BUY_LOW_ID, 1.0), ("K9_LT30", 1.5)], 1.0),
        ("SOFT_CHAMP_PLUS_K9_LT20_a10", [(BUY_LOW_ID, 1.0), ("K9_LT20", 1.0)], 1.0),
        ("SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a05", [(BUY_LOW_ID, 1.0), ("K9_LT30", 1.0)], 0.5),
        ("SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a15", [(BUY_LOW_ID, 1.0), ("K9_LT30", 1.0)], 1.5),
        (
            "SOFT_CHAMP_PLUS_K9_a075_BB_a025",
            [(BUY_LOW_ID, 1.0), ("K9_LT30", 0.75), ("BB_LOWER", 0.25)],
            1.0,
        ),
    ]

    print(f"Soft track books: {len(soft_jobs)}", flush=True)
    soft_rows: list[dict] = []
    soft_nav_base = None
    soft_win_base = None
    asof = None
    for i, (book_id, buy_specs, sell_boost) in enumerate(soft_jobs, 1):
        print(f"  soft [{i}/{len(soft_jobs)}] {book_id}", flush=True)
        if not buy_specs:
            scores = kd_scores
            sell = None
        else:
            scores = add_buy_softs(kd_scores, lows, buy_specs)
            sell = sell_panels[float(sell_boost)] if sell_boost is not None else None
        res = run_kd(
            market, target_live, regime, dividends, scores=scores, buy_ok=kd_ok, sell_scores=sell
        )
        win = {w: window_stats(res["nav"], a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
        if book_id == SOFT_BASE:
            soft_nav_base = res["nav"]
            soft_win_base = win
            asof = pd.to_datetime(res["nav"]["date"]).max()
            tip = tip_gate(soft_nav_base, soft_nav_base, asof)
            held = {"mdd_improve_pp": 0.0, "cagr_giveback_pp": 0.0, "score": 0.0}
        else:
            tip = tip_gate(soft_nav_base, res["nav"], asof)
            held = held_score(soft_win_base["heldout_2019_plus"], win["heldout_2019_plus"])
        soft_rows.append(
            book_row(
                book_id=book_id,
                track="soft",
                tip=tip,
                held=held,
                win=win,
                n_fills=res["n_fills"],
                extra={
                    "buy_soft": "+".join(f"{a}@{b:g}" for a, b in buy_specs) if buy_specs else "none",
                    "sell_soft": f"{SELL_HIGH_ID}@{sell_boost:g}" if sell_boost else "none",
                    "is_observe_ref": book_id == OBSERVE_CHAL_ID,
                },
            )
        )

    sleeve_specs = [
        ("BELOW_MA60", 60, "ma", 0.025),
        ("BELOW_MA60", 60, "ma", 0.05),
        ("BELOW_MA60", 60, "ma", 0.075),
        ("BELOW_MA60", 60, "ma", 0.10),
        ("BELOW_MA60", 60, "ma", 0.125),
        ("BELOW_MA40", 40, "ma", 0.025),
        ("BELOW_MA40", 40, "ma", 0.05),
        ("BELOW_MA40", 40, "ma", 0.10),
        ("RSI14_LT30", 14, "rsi_lt30", 0.10),
        ("RSI14_LT30", 14, "rsi_lt30", 0.15),
        ("RSI14_LT30", 14, "rsi_lt30", 0.20),
    ]

    print("LIVE_STACK ...", flush=True)
    live_res = run_kd(
        market, target_live, regime, dividends, scores=kd_scores, buy_ok=kd_ok
    )
    win_live = {w: window_stats(live_res["nav"], a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
    if asof is None:
        asof = pd.to_datetime(live_res["nav"]["date"]).max()
    sleeve_rows: list[dict] = [
        book_row(
            book_id=SLEEVE_BASE,
            track="sleeve",
            tip=tip_gate(live_res["nav"], live_res["nav"], asof),
            held={"mdd_improve_pp": 0.0, "cagr_giveback_pp": 0.0, "score": 0.0},
            win=win_live,
            n_fills=live_res["n_fills"],
            extra={"signal": "none", "alpha": None, "is_seed": False},
        )
    ]

    print(f"Sleeve track challengers: {len(sleeve_specs)}", flush=True)
    for i, (short, window, kind, alpha) in enumerate(sleeve_specs, 1):
        book_id = f"SLEEVE_{short}_a{alpha_tag(alpha)}"
        print(f"  sleeve [{i}/{len(sleeve_specs)}] {book_id}", flush=True)
        tilt = sleeve_signal_panel(sleeve, kind, window)
        new_score = base_score + 1.0 * float(alpha) * tilt
        new_target = rebuild_targets_from_score(new_score, regime)
        res = run_kd(
            market, new_target, regime, dividends, scores=kd_scores, buy_ok=kd_ok
        )
        win = {w: window_stats(res["nav"], a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
        tip = tip_gate(live_res["nav"], res["nav"], asof)
        held = held_score(win_live["heldout_2019_plus"], win["heldout_2019_plus"])
        sleeve_rows.append(
            book_row(
                book_id=book_id,
                track="sleeve",
                tip=tip,
                held=held,
                win=win,
                n_fills=res["n_fills"],
                extra={
                    "signal": short,
                    "alpha": float(alpha),
                    "is_seed": book_id == SLEEVE_SEED,
                },
            )
        )

    observe_soft = next(r for r in soft_rows if r["id"] == OBSERVE_CHAL_ID)
    soft_ranked = sorted(
        soft_rows,
        key=lambda r: (
            1 if r.get("promote_shaped") else 0,
            1 if r.get("coexist") else 0,
            r["heldout_score"],
        ),
        reverse=True,
    )
    soft_beat_live = [
        r for r in soft_ranked if r["id"] != SOFT_BASE and r.get("coexist") and r["heldout_score"] > 0
    ]
    soft_beat_observe = [
        r
        for r in soft_ranked
        if r["id"] not in (SOFT_BASE, OBSERVE_CHAL_ID, CHAMPION_ID)
        and r.get("tip_clean")
        and r["heldout_score"] > observe_soft["heldout_score"]
    ]
    soft_promote = [
        r
        for r in soft_ranked
        if r["id"] not in (SOFT_BASE, OBSERVE_CHAL_ID)
        and r.get("promote_shaped")
        and r["heldout_score"] > observe_soft["heldout_score"]
    ]
    if soft_promote:
        soft_verdict = "PROMOTE_SHAPED_BEATS_OBSERVE"
    elif soft_beat_observe:
        soft_verdict = "BEATS_OBSERVE_TIP_MDD_ALERT"
    elif soft_beat_live:
        soft_verdict = "BEATS_LIVE_NO_OBSERVE_LIFT"
    elif any(r.get("tip_clean") and r["id"] != SOFT_BASE for r in soft_ranked):
        soft_verdict = "NEAR_NO_LIFT"
    else:
        soft_verdict = "NO_LIFT"

    sleeve_ranked = sorted(
        sleeve_rows,
        key=lambda r: (
            1 if r.get("promote_shaped") else 0,
            1 if r.get("coexist") else 0,
            r["heldout_score"],
        ),
        reverse=True,
    )
    sleeve_promote = [r for r in sleeve_ranked if r["id"] != SLEEVE_BASE and r.get("promote_shaped")]
    sleeve_beat = [r for r in sleeve_ranked if r["id"] != SLEEVE_BASE and r.get("coexist")]
    seed_row = next(r for r in sleeve_ranked if r["id"] == SLEEVE_SEED)
    if sleeve_promote:
        sleeve_verdict = "MDD_CLEAR_BEATS_LIVE"
    elif sleeve_beat:
        sleeve_verdict = "TIP_CLEAN_MDD_ALERT"
    elif any(r.get("tip_clean") and r["id"] != SLEEVE_BASE for r in sleeve_ranked):
        sleeve_verdict = "NEAR_NO_LIFT"
    else:
        sleeve_verdict = "NO_LIFT"

    if soft_verdict == "PROMOTE_SHAPED_BEATS_OBSERVE" or sleeve_verdict == "MDD_CLEAR_BEATS_LIVE":
        overall = "HAS_PROMOTE_SHAPED_CANDIDATE"
    elif soft_beat_observe or sleeve_beat:
        overall = "LIFT_WITHOUT_FULL_PROMOTE_SHAPE"
    else:
        overall = "NO_SUPERIOR_PROMOTE_SHAPED"

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "SOFT_SLEEVE_BORROW_PROMOTE_SCREEN_STAGE_A",
        "charter": "research/ops/SOFT_SLEEVE_BORROW_PROMOTE_CHARTER.md",
        "status": "PAPER_SCREEN_DONE",
        "live_wire": False,
        "soft_x_sleeve_fuse": False,
        "asof": str(pd.Timestamp(asof).date()),
        "borrow_notes": [
            "Note2 soft amplitude assist",
            "Note3 sleeve lower-alpha + tip MDD hygiene",
            "Note4/5 no Soft×Sleeve fuse",
        ],
        "overall_verdict": overall,
        "soft": {
            "verdict": soft_verdict,
            "n_books": len(soft_rows),
            "observe_id": OBSERVE_CHAL_ID,
            "observe_heldout_score": observe_soft["heldout_score"],
            "observe_tip_mdd_clean": observe_soft["tip_mdd_clean"],
            "n_beat_live": len(soft_beat_live),
            "n_beat_observe": len(soft_beat_observe),
            "n_promote_shaped_beats_observe": len(soft_promote),
            "beat_live_ids": [r["id"] for r in soft_beat_live],
            "beat_observe_ids": [r["id"] for r in soft_beat_observe],
            "promote_shaped_ids": [r["id"] for r in soft_promote],
            "books": soft_ranked,
        },
        "sleeve": {
            "verdict": sleeve_verdict,
            "n_books": len(sleeve_rows),
            "seed_id": SLEEVE_SEED,
            "seed_tip_mdd_clean": seed_row["tip_mdd_clean"],
            "seed_heldout_score": seed_row["heldout_score"],
            "n_beat_live": len(sleeve_beat),
            "n_promote_shaped": len(sleeve_promote),
            "beat_live_ids": [r["id"] for r in sleeve_beat],
            "promote_shaped_ids": [r["id"] for r in sleeve_promote],
            "books": sleeve_ranked,
        },
        "non_actions": [
            "No Soft-assist observe swap",
            "No Sleeve-tilt observe swap",
            "No Soft×Sleeve auto-combo",
            "No live Soft-assist / Sleeve-tilt / Soft-Frozen / KD / TEL / E45 wire",
            "No hard-AND indicator reopen",
        ],
    }

    pd.DataFrame(soft_ranked).to_csv(OUT / "reports" / "soft_scoreboard.csv", index=False)
    pd.DataFrame(sleeve_ranked).to_csv(OUT / "reports" / "sleeve_scoreboard.csv", index=False)
    blob = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    (OUT / "reports" / "soft_sleeve_borrow_promote_screen.json").write_text(blob, encoding="utf-8")
    (OPS / "SOFT_SLEEVE_BORROW_PROMOTE_SCREEN.json").write_text(blob, encoding="utf-8")

    def pct(x):
        return "—" if x is None else f"{100 * float(x):.2f}%"

    def soft_line(r):
        return (
            f"| `{r['id']}` | {r.get('buy_soft', '')} | {r['tip_ytd']} | {r['tip_1y']} | "
            f"{'Y' if r['tip_mdd_clean'] else 'N'} | {'Y' if r['promote_shaped'] else 'N'} | "
            f"{r['heldout_score']:.3f} | {r['mdd_improve_pp']:.3f} | "
            f"{pct(r['heldout_cagr'])} | {pct(r['heldout_mdd'])} | "
            f"{pct(r['sealed_cagr'])} | {pct(r['sealed_mdd'])} |"
        )

    def sleeve_line(r):
        a = "—" if r.get("alpha") is None else f"{r['alpha']:.3f}"
        return (
            f"| `{r['id']}` | {r.get('signal')} | {a} | {r['tip_ytd']} | {r['tip_1y']} | "
            f"{'Y' if r['tip_mdd_clean'] else 'N'} | {'Y' if r['promote_shaped'] else 'N'} | "
            f"{r['heldout_score']:.3f} | {r['mdd_improve_pp']:.3f} | "
            f"{pct(r['heldout_cagr'])} | {pct(r['heldout_mdd'])} | "
            f"{pct(r['sealed_cagr'])} | {pct(r['sealed_mdd'])} |"
        )

    lines = [
        "# Soft ∥ Sleeve Borrow-Promote Screen — Stage A",
        "",
        f"Generated: `{payload['generated_at_utc']}` · asof **{payload['asof']}**",
        f"Overall: **`{overall}`** · Soft **`{soft_verdict}`** · Sleeve **`{sleeve_verdict}`**",
        "Soft×Sleeve fuse: **forbidden** · live wire: **false**",
        "",
        "## Question",
        "",
        "Using borrow-informed Stage A (Soft amplitude around K9+; Sleeve lower-α + tip MDD hygiene), "
        "is there a **promote-shaped** paper challenger that tip-clean beats the current observe "
        "(Soft) or clears tip MDD ALERTs while beating LIVE_STACK (Sleeve)?",
        "",
        "## Borrow map",
        "",
        "- Note 2 → Soft additive amplitude grid (assist, not replace)",
        "- Note 3 → Sleeve desensitize + tip YTD/1y MDD ≥ live",
        "- Notes 4/5 → independent tracks only",
        "",
        "## Soft track",
        "",
        f"- Observe ref `{OBSERVE_CHAL_ID}` held **{observe_soft['heldout_score']:.3f}** · tip_mdd_clean **{observe_soft['tip_mdd_clean']}**",
        f"- Beat live: **{len(soft_beat_live)}** → `{[r['id'] for r in soft_beat_live]}`",
        f"- Beat observe: **{len(soft_beat_observe)}** → `{[r['id'] for r in soft_beat_observe]}`",
        f"- Promote-shaped > observe: **{len(soft_promote)}** → `{[r['id'] for r in soft_promote]}`",
        "",
        "| ID | Buy soft | Tip YTD | Tip 1y | Tip MDD clean | Promote-shaped | Held score | MDDΔpp | Held CAGR | Held MDD | Sealed CAGR | Sealed MDD |",
        "|---|---|---|---|:---:|:---:|---:|---:|---:|---:|---:|---:|",
    ]
    lines.extend(soft_line(r) for r in soft_ranked)
    lines += [
        "",
        "## Sleeve track",
        "",
        f"- Seed `{SLEEVE_SEED}` held **{seed_row['heldout_score']:.3f}** · tip_mdd_clean **{seed_row['tip_mdd_clean']}**",
        f"- Beat live (tip-clean+held>0): **{len(sleeve_beat)}** → `{[r['id'] for r in sleeve_beat]}`",
        f"- Promote-shaped (tip+MDD clean+held>0): **{len(sleeve_promote)}** → `{[r['id'] for r in sleeve_promote]}`",
        "",
        "| ID | Signal | α | Tip YTD | Tip 1y | Tip MDD clean | Promote-shaped | Held score | MDDΔpp | Held CAGR | Held MDD | Sealed CAGR | Sealed MDD |",
        "|---|---|---:|---|---|:---:|:---:|---:|---:|---:|---:|---:|---:|",
    ]
    lines.extend(sleeve_line(r) for r in sleeve_ranked)
    lines += [
        "",
        "## Reading",
        "",
        "- **Promote-shaped** = tip YTD+1y PASS **and** tip YTD+1y MDD not worse than base **and** held-out score > 0.",
        "- Soft observe already tip-MDD clean on prior month-end; this grid asks if amplitude neighbors beat it under the same hygiene.",
        "- Sleeve seed is tip-clean but month-end MDD ALERT; this grid seeks lower-α / neighbor signals that clear tip MDD while keeping held > 0.",
        "",
        "## Non-actions",
        "",
    ]
    lines.extend(f"- {x}" for x in payload["non_actions"])
    lines += [
        "",
        "## Label",
        "",
        f"`SOFT_SLEEVE_BORROW_PROMOTE_SCREEN_STAGE_A_{payload['asof']}__{overall}`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "reports" / "SOFT_SLEEVE_BORROW_PROMOTE_SCREEN.md").write_text(md, encoding="utf-8")
    (OPS / "SOFT_SLEEVE_BORROW_PROMOTE_SCREEN.md").write_text(md, encoding="utf-8")

    zh = "\n".join(
        [
            "# Soft ∥ Sleeve 外借促升 Stage A 篩選",
            "",
            f"產生：`{payload['generated_at_utc']}` · asof **{payload['asof']}**",
            f"總判決：**`{overall}`** · Soft **`{soft_verdict}`** · Sleeve **`{sleeve_verdict}`**",
            "Soft×Sleeve 融合：**禁止** · live wire：**否**",
            "",
            "## 問題",
            "",
            "依外借筆記做 Soft 振幅細網 + Sleeve 降敏／tip MDD 衛生，是否出現 **promote-shaped** "
            "優於現有 observe（Soft）或清掉 tip MDD ALERT 且 beat LIVE_STACK（Sleeve）的紙上挑戰者？",
            "",
            f"- Soft：beat live **{len(soft_beat_live)}** · beat observe **{len(soft_beat_observe)}** · "
            f"promote-shaped>observe **{len(soft_promote)}**",
            f"- Sleeve：beat live **{len(sleeve_beat)}** · promote-shaped **{len(sleeve_promote)}** · "
            f"seed tip_mdd_clean **{seed_row['tip_mdd_clean']}**",
            "",
            "詳表見英文 `SOFT_SLEEVE_BORROW_PROMOTE_SCREEN.md`。",
            "",
            "## 非動作",
            "",
            "- 不換 Soft-assist／Sleeve-tilt observe",
            "- 不自動 Soft×Sleeve 融合",
            "- 不改 live Soft-Frozen／KD／TEL／E45",
            "",
            "## Label",
            "",
            f"`SOFT_SLEEVE_BORROW_PROMOTE_SCREEN_STAGE_A_{payload['asof']}__{overall}`",
            "",
        ]
    )
    (OPS / "SOFT_SLEEVE_BORROW_PROMOTE_SCREEN.zh-TW.md").write_text(zh, encoding="utf-8")

    print(
        json.dumps(
            {
                "overall": overall,
                "soft_verdict": soft_verdict,
                "sleeve_verdict": sleeve_verdict,
                "soft_promote": [r["id"] for r in soft_promote],
                "sleeve_promote": [r["id"] for r in sleeve_promote],
                "soft_beat_observe": [r["id"] for r in soft_beat_observe],
                "sleeve_beat": [r["id"] for r in sleeve_beat],
                "seed_tip_mdd_clean": seed_row["tip_mdd_clean"],
            },
            ensure_ascii=False,
            indent=2,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
