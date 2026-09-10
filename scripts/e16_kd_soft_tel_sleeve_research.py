#!/usr/bin/env python3
"""Paper research: soft-assist + KD retune + TEL/sleeve indicators.

Charter: research/ops/KD_SOFT_TEL_SLEEVE_RESEARCH_CHARTER.md

Tracks
  A Soft assist — score boost / sell soft-tilt (not hard gates)
  B KD retune — season × K × pre-ex grid vs LIVE_KD_OPT (paper only)
  C TEL / sleeve — Telecom within-sleeve + E16 sleeve-score tilts
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
from e50_early_stack_combined_nav import FIN, TEL, e16_features, simulate_core
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp
from ta_indicator_catalog import HIGH_IDS, LOW_IDS, build_low_high_catalog
from tw_share_lots import BOARD_LOT
from within_sleeve_alloc import (
    FIN_EQUAL,
    FIN_PRE_EXDIV_KD,
    TEL_EQUAL,
    TEL_PRE_EXDIV_KD,
    TEL_RS_SOFT_TILT,
    TEL_RS_SOFT_TILT_EXDIV,
    build_kd_season_tilt_scores,
    build_name_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/kd-soft-tel-sleeve-research"
RESEARCH = ROOT / "research/ops"
CAPITAL = 500_000_000.0
LOT = BOARD_LOT
TRAIL_ALERT_PP = 3.0
TRAIL_PAUSE_PP = 5.0
SOFT_BOOST = 1.0

LIVE_KD = {
    "season_start": (4, 15),
    "season_end": (5, 15),
    "k_thresh": 30.0,
    "pre_days": 15,
    "active_score": 1.5,
}

SEASONS = [
    ("APR", (4, 1), (4, 30)),
    ("APR15_MAY15", (4, 15), (5, 15)),
    ("APR15_MAY31", (4, 15), (5, 31)),
    ("MAY", (5, 1), (5, 31)),
    ("MAY15_JUN10", (5, 15), (6, 10)),
    ("APR_MAY", (4, 1), (5, 31)),
]
K_THRESH = (15.0, 20.0, 25.0, 30.0, 35.0)
PRE_DAYS = (5, 10, 15, 20)

SLEEVE_TILT_ALPHAS = (0.10, 0.20)
SLEEVE_SIGNAL_IDS = (
    "SLEEVE_RSI14_LT30",
    "SLEEVE_RSI14_GT70",
    "SLEEVE_BELOW_MA60",
    "SLEEVE_ABOVE_MA60",
    "SLEEVE_MOM20_NEG",
    "SLEEVE_MOM20_POS",
)


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


def soft_boost_scores(kd_scores: pd.DataFrame, panel: pd.DataFrame, boost: float) -> pd.DataFrame:
    p = panel.reindex(index=kd_scores.index, columns=kd_scores.columns).fillna(False)
    return kd_scores.astype(float) + float(boost) * p.astype(float)


def soft_sell_panel(high_panel: pd.DataFrame, *, base: float = 1.0, boost: float = 1.0) -> pd.DataFrame:
    return float(base) + float(boost) * high_panel.astype(float)


def rebuild_targets_from_score(score: pd.DataFrame, regime: pd.Series) -> pd.DataFrame:
    """Same Soft-Frozen clip/blend loop as e16_soft_frozen_base, with replaced score."""
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


def sleeve_indicator_tilt(
    sleeve_rets: pd.DataFrame, signal_id: str
) -> pd.DataFrame:
    """Causal ±1 sleeve-level signal panel (date × sleeve)."""
    nav = (1.0 + sleeve_rets.fillna(0.0)).cumprod()
    out = pd.DataFrame(0.0, index=sleeve_rets.index, columns=list(sleeve_rets.columns))
    for col in sleeve_rets.columns:
        close = nav[col]
        if signal_id == "SLEEVE_RSI14_LT30":
            delta = close.diff()
            gain = delta.clip(lower=0.0)
            loss = (-delta).clip(lower=0.0)
            avg_gain = gain.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
            avg_loss = loss.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
            rs = avg_gain / avg_loss.replace(0.0, np.nan)
            rsi = 100.0 - (100.0 / (1.0 + rs))
            out[col] = (rsi < 30.0).astype(float)
        elif signal_id == "SLEEVE_RSI14_GT70":
            delta = close.diff()
            gain = delta.clip(lower=0.0)
            loss = (-delta).clip(lower=0.0)
            avg_gain = gain.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
            avg_loss = loss.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
            rs = avg_gain / avg_loss.replace(0.0, np.nan)
            rsi = 100.0 - (100.0 / (1.0 + rs))
            out[col] = (rsi > 70.0).astype(float)
        elif signal_id == "SLEEVE_BELOW_MA60":
            ma = close.rolling(60, min_periods=40).mean()
            out[col] = (close < ma).astype(float)
        elif signal_id == "SLEEVE_ABOVE_MA60":
            ma = close.rolling(60, min_periods=40).mean()
            out[col] = (close > ma).astype(float)
        elif signal_id == "SLEEVE_MOM20_NEG":
            mom = close / close.shift(20) - 1.0
            out[col] = (mom < 0.0).astype(float)
        elif signal_id == "SLEEVE_MOM20_POS":
            mom = close / close.shift(20) - 1.0
            out[col] = (mom > 0.0).astype(float)
        else:
            raise ValueError(signal_id)
    return out.fillna(0.0)


def sim(
    market,
    target,
    regime,
    dividends,
    *,
    fin_scores=None,
    fin_buy_ok=None,
    fin_sell_scores=None,
    telecom_alloc=TEL_EQUAL,
    tel_scores=None,
    tel_buy_ok=None,
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
        financial_alloc=FIN_PRE_EXDIV_KD if fin_scores is not None else FIN_EQUAL,
        telecom_alloc=telecom_alloc,
        fin_name_scores=fin_scores,
        fin_buy_ok=fin_buy_ok,
        fin_sell_scores=fin_sell_scores,
        tel_name_scores=tel_scores,
        tel_buy_ok=tel_buy_ok,
    )


def eval_book(
    *,
    book_id,
    track,
    detail,
    nav_eq,
    win_eq,
    held_live,
    asof,
    market,
    target,
    regime,
    dividends,
    fin_scores=None,
    fin_buy_ok=None,
    fin_sell_scores=None,
    telecom_alloc=TEL_EQUAL,
    tel_scores=None,
    tel_buy_ok=None,
):
    # EQUAL baseline books use FIN_EQUAL (no KD scores)
    if fin_scores is None and book_id.startswith("EQUAL_"):
        nav, fills, meta = simulate_core(
            market,
            target,
            regime,
            dividends,
            apply_e22=True,
            apply_stock_div=True,
            capital=CAPITAL,
            lot_size=LOT,
            financial_alloc=FIN_EQUAL,
            telecom_alloc=telecom_alloc,
            tel_name_scores=tel_scores,
            tel_buy_ok=tel_buy_ok,
        )
    else:
        nav, fills, meta = sim(
            market,
            target,
            regime,
            dividends,
            fin_scores=fin_scores,
            fin_buy_ok=fin_buy_ok,
            fin_sell_scores=fin_sell_scores,
            telecom_alloc=telecom_alloc,
            tel_scores=tel_scores,
            tel_buy_ok=tel_buy_ok,
        )
    assert meta.get("exact_t1_ok"), book_id
    win = {w: window_stats(nav, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
    tip = tip_gate(nav_eq, nav, asof)
    held = score_vs_base(win_eq["heldout_2019_plus"], win["heldout_2019_plus"])
    tip_clean = tip["ytd"]["gate"] == "PASS" and tip["trailing_1y"]["gate"] == "PASS"
    return {
        "id": book_id,
        "track": track,
        "detail": detail,
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
        r.get("coexist")
        and r.get("vs_live_heldout_delta", 0) > 0
        and r["id"] != "LIVE_KD_OPT"
    )
    no_pause = r["tip_ytd"] != "PAUSE_REVIEW" and r["tip_1y"] != "PAUSE_REVIEW"
    return (
        1 if r.get("coexist") else 0,
        1 if beat else 0,
        1 if no_pause else 0,
        r["heldout_score"],
    )


def track_verdict(rows: list[dict], live_id: str = "LIVE_KD_OPT") -> str:
    beat = [
        r
        for r in rows
        if r.get("coexist") and r["id"] != live_id and r.get("vs_live_heldout_delta", 0) > 0
    ]
    coexist_other = [r for r in rows if r.get("coexist") and r["id"] != live_id]
    near = [
        r
        for r in rows
        if r["id"] != live_id
        and r.get("tip_clean")
        and r.get("vs_live_heldout_delta", -9) > -0.05
    ]
    if beat:
        return "BEATS_LIVE"
    if near:
        return "NEAR_NO_BEAT"
    if coexist_other:
        return "COEXIST_NO_LIFT"
    return "NO_LIFT"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.9]

    print("loading ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    prices, sleeve, target, regime = e16_features(market)
    # recover diagnostic score for sleeve tilts
    _p, _s, _t, _r, base_score = soft.build_soft_frozen_targets(market)
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

    live_row = eval_book(
        book_id="LIVE_KD_OPT",
        track="base",
        detail="live_lock",
        nav_eq=nav_eq,
        win_eq=win_eq,
        held_live=0.0,
        asof=asof,
        market=market,
        target=target,
        regime=regime,
        dividends=dividends,
        fin_scores=kd_scores,
        fin_buy_ok=kd_ok,
    )
    held_live = float(live_row["heldout_score"])
    live_row["vs_live_heldout_delta"] = 0.0
    rows: list[dict] = [live_row]

    print("catalog FIN ...", flush=True)
    fin_lows, fin_highs = build_low_high_catalog(market, cal, list(FIN))
    print("catalog TEL ...", flush=True)
    tel_lows, _tel_highs = build_low_high_catalog(market, cal, list(TEL))
    tel_rs = build_name_scores(market, TEL)
    tel_kd = build_kd_season_tilt_scores(
        market,
        dividends,
        TEL,
        k_thresh=float(LIVE_KD["k_thresh"]),
        season_start=LIVE_KD["season_start"],
        season_end=LIVE_KD["season_end"],
        pre_days=int(LIVE_KD["pre_days"]),
        active_score=float(LIVE_KD["active_score"]),
    )
    tel_ok = build_pre_exdiv_window_buy_ok(
        cal, dividends, TEL, pre_days=int(LIVE_KD["pre_days"]), also_stock_ex=True
    )

    # ---- Track A: soft assist ----
    soft_jobs = []
    for lid in LOW_IDS:
        soft_jobs.append(
            (
                f"SOFT_BUY_{lid}",
                "soft_assist",
                f"buy_boost={SOFT_BOOST}|{lid}",
                soft_boost_scores(kd_scores, fin_lows[lid], SOFT_BOOST),
                kd_ok,
                None,
            )
        )
    for hid in HIGH_IDS:
        soft_jobs.append(
            (
                f"SOFT_SELL_{hid}",
                "soft_assist",
                f"sell_tilt={SOFT_BOOST}|{hid}",
                kd_scores,
                kd_ok,
                soft_sell_panel(fin_highs[hid], boost=SOFT_BOOST),
            )
        )
    # BOTH: singles cross is large; keep a compact both = buy boost + sell tilt for each pair
    # of the prior-best families only would bias; do full cross like hard assist.
    for lid in LOW_IDS:
        for hid in HIGH_IDS:
            soft_jobs.append(
                (
                    f"SOFT_BOTH__{lid}__{hid}",
                    "soft_assist",
                    f"both|{lid}+{hid}",
                    soft_boost_scores(kd_scores, fin_lows[lid], SOFT_BOOST),
                    kd_ok,
                    soft_sell_panel(fin_highs[hid], boost=SOFT_BOOST),
                )
            )

    print(f"Track A soft-assist: {len(soft_jobs)} books ...", flush=True)
    for i, (book_id, track, detail, scores, buy_ok, sell_sc) in enumerate(soft_jobs, 1):
        if i == 1 or i % 40 == 0 or i == len(soft_jobs):
            print(f"  [A {i}/{len(soft_jobs)}] {book_id}", flush=True)
        rows.append(
            eval_book(
                book_id=book_id,
                track=track,
                detail=detail,
                nav_eq=nav_eq,
                win_eq=win_eq,
                held_live=held_live,
                asof=asof,
                market=market,
                target=target,
                regime=regime,
                dividends=dividends,
                fin_scores=scores,
                fin_buy_ok=buy_ok,
                fin_sell_scores=sell_sc,
            )
        )

    # ---- Track B: KD retune ----
    kd_jobs = []
    for sname, s0, s1 in SEASONS:
        for kth in K_THRESH:
            for pred in PRE_DAYS:
                if (
                    sname == "APR15_MAY15"
                    and float(kth) == 30.0
                    and int(pred) == 15
                ):
                    continue  # live lock already in rows
                kid = f"KD_{sname}_Klt{int(kth)}_T{int(pred)}"
                kd_jobs.append((kid, sname, s0, s1, float(kth), int(pred)))

    print(f"Track B KD retune: {len(kd_jobs)} books ...", flush=True)
    for i, (book_id, sname, s0, s1, kth, pred) in enumerate(kd_jobs, 1):
        if i == 1 or i % 25 == 0 or i == len(kd_jobs):
            print(f"  [B {i}/{len(kd_jobs)}] {book_id}", flush=True)
        sc = build_kd_season_tilt_scores(
            market,
            dividends,
            FIN,
            k_thresh=kth,
            season_start=s0,
            season_end=s1,
            pre_days=pred,
            active_score=float(LIVE_KD["active_score"]),
        )
        ok = build_pre_exdiv_window_buy_ok(
            cal, dividends, FIN, pre_days=pred, also_stock_ex=True
        )
        rows.append(
            eval_book(
                book_id=book_id,
                track="kd_retune",
                detail=f"{sname}|K<{kth}|T-{pred}",
                nav_eq=nav_eq,
                win_eq=win_eq,
                held_live=held_live,
                asof=asof,
                market=market,
                target=target,
                regime=regime,
                dividends=dividends,
                fin_scores=sc,
                fin_buy_ok=ok,
            )
        )

    # ---- Track C: TEL + sleeve ----
    tel_jobs = []
    # live FIN + challenger TEL policies
    tel_jobs.append(
        (
            "TEL_RS_SOFT_TILT",
            "tel_sleeve",
            "tel=RS_SOFT",
            target,
            TEL_RS_SOFT_TILT,
            tel_rs,
            None,
        )
    )
    tel_jobs.append(
        (
            "TEL_RS_SOFT_TILT_EXDIV",
            "tel_sleeve",
            "tel=RS_SOFT_EXDIV",
            target,
            TEL_RS_SOFT_TILT_EXDIV,
            tel_rs,
            tel_ok,
        )
    )
    tel_jobs.append(
        (
            "TEL_PRE_EXDIV_KD_LIVEPARAMS",
            "tel_sleeve",
            "tel=PRE_EXDIV_KD",
            target,
            TEL_PRE_EXDIV_KD,
            tel_kd,
            tel_ok,
        )
    )
    for lid in LOW_IDS:
        # soft tilt TEL scores from low indicator (1 when low else 0) + tiny base
        sc = 0.25 + tel_lows[lid].astype(float)
        tel_jobs.append(
            (
                f"TEL_SOFT_BUY_{lid}",
                "tel_sleeve",
                f"tel_soft|{lid}",
                target,
                TEL_RS_SOFT_TILT,
                sc,
                None,
            )
        )

    # Sleeve-level tilts (keep live within-sleeve KD + TEL_EQUAL)
    for sig in SLEEVE_SIGNAL_IDS:
        tilt = sleeve_indicator_tilt(sleeve, sig)
        # Oversold-style signals boost sleeve; overbought-style dampen
        sign = (
            +1.0
            if sig
            in (
                "SLEEVE_RSI14_LT30",
                "SLEEVE_BELOW_MA60",
                "SLEEVE_MOM20_NEG",
            )
            else -1.0
        )
        for alpha in SLEEVE_TILT_ALPHAS:
            new_score = base_score + float(sign) * float(alpha) * tilt
            new_target = rebuild_targets_from_score(new_score, regime)
            short = sig.removeprefix("SLEEVE_")
            tel_jobs.append(
                (
                    f"SLEEVE_{short}_a{str(alpha).replace('.', '')}",
                    "tel_sleeve",
                    f"sleeve|{sig}|a={alpha}|sign={sign}",
                    new_target,
                    TEL_EQUAL,
                    None,
                    None,
                )
            )

    print(f"Track C TEL/sleeve: {len(tel_jobs)} books ...", flush=True)
    for i, job in enumerate(tel_jobs, 1):
        book_id, track, detail, tgt, tel_alloc, tsc, tok = job
        if i == 1 or i % 10 == 0 or i == len(tel_jobs):
            print(f"  [C {i}/{len(tel_jobs)}] {book_id}", flush=True)
        rows.append(
            eval_book(
                book_id=book_id,
                track=track,
                detail=detail,
                nav_eq=nav_eq,
                win_eq=win_eq,
                held_live=held_live,
                asof=asof,
                market=market,
                target=tgt,
                regime=regime,
                dividends=dividends,
                fin_scores=kd_scores,
                fin_buy_ok=kd_ok,
                telecom_alloc=tel_alloc,
                tel_scores=tsc,
                tel_buy_ok=tok,
            )
        )

    ranked = sorted(rows, key=rank_key, reverse=True)
    by_track = {
        "soft_assist": [r for r in ranked if r["track"] == "soft_assist"],
        "kd_retune": [r for r in ranked if r["track"] == "kd_retune"],
        "tel_sleeve": [r for r in ranked if r["track"] == "tel_sleeve"],
        "base": [r for r in ranked if r["track"] == "base"],
    }
    verdicts = {t: track_verdict(by_track[t] + by_track["base"]) for t in ("soft_assist", "kd_retune", "tel_sleeve")}
    # For track verdicts, only compare books in that track (+ live)
    for t in ("soft_assist", "kd_retune", "tel_sleeve"):
        verdicts[t] = track_verdict(by_track[t] + by_track["base"])

    beat_all = [
        r
        for r in ranked
        if r.get("coexist") and r["id"] != "LIVE_KD_OPT" and r.get("vs_live_heldout_delta", 0) > 0
    ]
    overall = (
        "BEATS_LIVE"
        if beat_all
        else (
            "NEAR_NO_BEAT"
            if any(
                r["id"] != "LIVE_KD_OPT"
                and r.get("tip_clean")
                and r.get("vs_live_heldout_delta", -9) > -0.05
                for r in ranked
            )
            else (
                "COEXIST_NO_LIFT"
                if any(r.get("coexist") and r["id"] != "LIVE_KD_OPT" for r in ranked)
                else "NO_LIFT"
            )
        )
    )

    def top_ids(track: str, n: int = 10) -> list[str]:
        return [r["id"] for r in by_track[track][:n]]

    def beat_ids(track: str) -> list[str]:
        return [
            r["id"]
            for r in by_track[track]
            if r.get("coexist") and r.get("vs_live_heldout_delta", 0) > 0
        ]

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "KD_SOFT_TEL_SLEEVE_RESEARCH_SCREEN",
        "charter": "research/ops/KD_SOFT_TEL_SLEEVE_RESEARCH_CHARTER.md",
        "status": "PAPER_SCREEN_DONE",
        "live_wire": False,
        "asof": str(pd.Timestamp(asof).date()),
        "live_heldout_score": held_live,
        "n_books": len(rows),
        "n_beat_live": len(beat_all),
        "beat_live_ids": [r["id"] for r in beat_all[:40]],
        "overall_verdict": overall,
        "track_verdicts": verdicts,
        "track_top": {t: top_ids(t) for t in ("soft_assist", "kd_retune", "tel_sleeve")},
        "track_beat": {t: beat_ids(t) for t in ("soft_assist", "kd_retune", "tel_sleeve")},
        "top20": [r["id"] for r in ranked[:20]],
        "books": ranked,
        "non_actions": [
            "No Soft-Frozen flip",
            "No live KD_OPT micro-tune / change without ACCEPT",
            "No live TEL_EQUAL flip",
            "No E45 stitch",
        ],
    }

    pd.DataFrame(ranked).to_csv(OUT / "reports" / "scoreboard.csv", index=False)
    (OUT / "reports" / "kd_soft_tel_sleeve_research_screen.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (RESEARCH / "KD_SOFT_TEL_SLEEVE_RESEARCH_SCREEN.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    def line(r):
        cagr = r["cagr_giveback_pp"]
        return (
            f"| `{r['id']}` | {r['track']} | {r['tip_ytd']} | {r['tip_1y']} | "
            f"{r['heldout_score']:.3f} | {r['mdd_improve_pp']:.3f} | "
            f"{'—' if cagr is None else f'{cagr:.3f}'} | {r['vs_live_heldout_delta']:.3f} | "
            f"{'Y' if r.get('coexist') else ''} |"
        )

    def section(track: str, title: str) -> list[str]:
        books = by_track[track]
        return [
            f"## {title}",
            "",
            f"Verdict: **`{verdicts[track]}`** · books **{len(books)}** · "
            f"beat-live **{len(beat_ids(track))}** → `{beat_ids(track)[:12]}`",
            "",
            "| ID | Track | Tip YTD | Tip 1y | Held | MDDΔpp | CAGRΔpp | vs live Δ | Coexist |",
            "|---|---|---|---|---:|---:|---:|---:|:---:|",
            *[line(r) for r in books[:12]],
            "",
        ]

    lines = [
        "# KD Soft / TEL / Sleeve Research Screen",
        "",
        f"Generated: `{payload['generated_at_utc']}` · asof **{payload['asof']}**",
        f"Charter: `KD_SOFT_TEL_SLEEVE_RESEARCH_CHARTER.md`",
        f"Overall: **`{overall}`** · live held-out **{held_live:.3f}**",
        "",
        "## Question",
        "",
        "Do soft score assists, KD season/threshold retunes, or Telecom/sleeve-layer "
        "indicators beat **`LIVE_KD_OPT`** (with Soft-Frozen KEEP)?",
        "",
        "## Summary",
        "",
        f"- Books: **{payload['n_books']}**",
        f"- Beat live (any track): **{payload['n_beat_live']}** → `{payload['beat_live_ids'][:20]}`",
        f"- Soft assist: `{verdicts['soft_assist']}`",
        f"- KD retune: `{verdicts['kd_retune']}`",
        f"- TEL/sleeve: `{verdicts['tel_sleeve']}`",
        "",
        "## Top 20 (all tracks)",
        "",
        "| ID | Track | Tip YTD | Tip 1y | Held | MDDΔpp | CAGRΔpp | vs live Δ | Coexist |",
        "|---|---|---|---|---:|---:|---:|---:|:---:|",
    ]
    lines.extend(line(r) for r in ranked[:20])
    lines.append("")
    lines.extend(section("soft_assist", "Track A — Soft assist"))
    lines.extend(section("kd_retune", "Track B — KD season / threshold retune"))
    lines.extend(section("tel_sleeve", "Track C — Telecom / sleeve indicators"))
    lines += [
        "## Reading",
        "",
        "- Soft assist ≠ hard AND filter (R1–R3 / assist screen); weights only.",
        "- KD retune is **paper**; FIN posture still locks live micro-tune unless ACCEPT.",
        "- TEL/sleeve keeps Soft-Frozen clips; no Class-D flip from this screen.",
        "",
        "## Non-actions",
        "",
        "- No Soft-Frozen / live KD / live TEL / E45 stitch from this screen alone",
        "",
        "## Label",
        "",
        "`KD_SOFT_TEL_SLEEVE_RESEARCH_SCREEN_2026-09-10`",
        "",
    ]
    md = "\n".join(lines)
    (RESEARCH / "KD_SOFT_TEL_SLEEVE_RESEARCH_SCREEN.md").write_text(md, encoding="utf-8")
    (OUT / "reports" / "KD_SOFT_TEL_SLEEVE_RESEARCH_SCREEN.md").write_text(md, encoding="utf-8")

    # compact zh-TW summary
    zh = "\n".join(
        [
            "# KD 軟輔助／電信／Sleeve 研究結果（paper）",
            "",
            f"產生：`{payload['generated_at_utc']}` · asof **{payload['asof']}**",
            f"總評：**`{overall}`** · live held-out **{held_live:.3f}**",
            "",
            f"- 軟輔助：`{verdicts['soft_assist']}`",
            f"- KD 重調：`{verdicts['kd_retune']}`",
            f"- 電信／sleeve：`{verdicts['tel_sleeve']}`",
            f"- 勝過 live：**{payload['n_beat_live']}** → `{payload['beat_live_ids'][:15]}`",
            "",
            "Live **KD_OPT**／**TEL_EQUAL**／Soft-Frozen **KEEP**；FIN posture 禁止 live 微調。",
            "",
        ]
    )
    (RESEARCH / "KD_SOFT_TEL_SLEEVE_RESEARCH_SCREEN.zh-TW.md").write_text(zh, encoding="utf-8")

    print(
        json.dumps(
            {
                "overall_verdict": overall,
                "track_verdicts": verdicts,
                "n_books": payload["n_books"],
                "n_beat_live": payload["n_beat_live"],
                "beat_live_ids": payload["beat_live_ids"][:20],
                "top10": payload["top20"][:10],
                "live_heldout": held_live,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
