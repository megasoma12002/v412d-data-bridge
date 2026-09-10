#!/usr/bin/env python3
"""Round-1 indicator buy/sell screen (PAPER ONLY).

Charter: research/ops/INDICATOR_BUY_SELL_CHARTER.md

Fixes Soft-Frozen sleeve + TEL_EQUAL. Challenges FIN within-sleeve
scoring with RSI / MACD / MA / Bollinger / volume vs live KD_OPT.

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
from within_sleeve_alloc import (
    FIN_EQUAL,
    FIN_PRE_EXDIV_KD,
    FIN_RS_SOFT_TILT_EXDIV,
    TEL_EQUAL,
    build_exdiv_buy_ok,
    build_kd_season_tilt_scores,
    build_name_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/indicator-buy-sell-screen-r1"
RESEARCH = ROOT / "research/ops"

CAPITAL = 500_000_000.0
LOT = BOARD_LOT
TRAIL_ALERT_PP = 3.0
TRAIL_PAUSE_PP = 5.0
ACTIVE = 1.5
LIVE_KD = {
    "id": "KD_APR15_MAY15_Klt30_T15",
    "season_start": (4, 15),
    "season_end": (5, 15),
    "k_thresh": 30.0,
    "pre_days": 15,
    "active_score": ACTIVE,
}
SEASON = ("APR15_MAY15", (4, 15), (5, 15))


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


def _panel(market: pd.DataFrame, codes: list[str]) -> dict[str, pd.DataFrame]:
    m = market.copy()
    m["date"] = pd.to_datetime(m["date"])
    m["code"] = m["code"].astype(str)
    out = {}
    for c in codes:
        g = (
            m[m["code"] == c]
            .sort_values("date")
            .drop_duplicates("date")
            .set_index("date")
        )
        out[c] = g
    return out


def _empty_scores(cal: pd.DatetimeIndex, codes: list[str]) -> pd.DataFrame:
    return pd.DataFrame(0.0, index=cal, columns=list(codes))


def build_rsi(close: pd.Series, n: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)
    avg_gain = gain.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    avg_loss = loss.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    return 100.0 - (100.0 / (1.0 + rs))


def build_macd_hist(close: pd.Series) -> pd.Series:
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd - signal


def season_first_hit_scores(
    cal: pd.DatetimeIndex,
    panels: dict[str, pd.DataFrame],
    dividends: pd.DataFrame,
    codes: list[str],
    *,
    trigger: pd.DataFrame,
    season_start: tuple[int, int],
    season_end: tuple[int, int],
    pre_days: int,
    active_score: float = ACTIVE,
) -> pd.DataFrame:
    """Like KD season: first True in season starts accumulation until pre-ex window."""
    scores = _empty_scores(cal, codes)
    d = dividends.copy() if dividends is not None and len(dividends) else pd.DataFrame()
    if len(d):
        d["code"] = d["code"].astype(str)
        d["cash_ex_date"] = pd.to_datetime(d["cash_ex_date"], errors="coerce")
    pos = {dt: i for i, dt in enumerate(cal)}
    years = sorted({dt.year for dt in cal})
    for c in codes:
        ex_list = []
        if len(d):
            ex_list = sorted(
                pd.to_datetime(d.loc[d["code"] == c, "cash_ex_date"], errors="coerce")
                .dropna()
                .unique()
            )
        trig = trigger[c].reindex(cal).fillna(False).astype(bool)
        for year in years:
            start = pd.Timestamp(year, season_start[0], season_start[1])
            end = pd.Timestamp(year, season_end[0], season_end[1])
            ex = None
            for ex0 in ex_list:
                if pd.Timestamp(ex0) >= start:
                    later = cal[cal >= pd.Timestamp(ex0)]
                    if len(later):
                        ex = later[0]
                        break
            if ex is None:
                continue
            i_ex = pos[ex]
            i_pre0 = max(0, i_ex - int(pre_days))
            season_mask = (cal >= start) & (cal <= end) & (cal < ex)
            if not bool(season_mask.any()):
                continue
            hits = trig.loc[season_mask]
            hits = hits[hits]
            if hits.empty:
                continue
            sig = hits.index[0]
            i_sig = pos[sig]
            i_end = i_pre0 - 1
            if i_end < i_sig:
                continue
            scores.iloc[i_sig : i_end + 1, scores.columns.get_loc(c)] = float(active_score)
    return scores


def always_on_scores(cal: pd.DatetimeIndex, trigger: pd.DataFrame, codes: list[str]) -> pd.DataFrame:
    scores = _empty_scores(cal, codes)
    for c in codes:
        t = trigger[c].reindex(cal).fillna(False).astype(bool)
        scores.loc[t, c] = ACTIVE
    return scores


def build_triggers(panels: dict[str, pd.DataFrame], cal: pd.DatetimeIndex, codes: list[str]) -> dict[str, pd.DataFrame]:
    rsi_os = _empty_scores(cal, codes).astype(bool)
    macd_pos = _empty_scores(cal, codes).astype(bool)
    ma_gold = _empty_scores(cal, codes).astype(bool)
    bb_low = _empty_scores(cal, codes).astype(bool)
    vol_up = _empty_scores(cal, codes).astype(bool)
    for c in codes:
        g = panels[c].reindex(cal)
        close = pd.to_numeric(g["close"], errors="coerce")
        vol = pd.to_numeric(g["volume"], errors="coerce")
        rsi = build_rsi(close, 14)
        hist = build_macd_hist(close)
        ma20 = close.rolling(20, min_periods=20).mean()
        ma60 = close.rolling(60, min_periods=60).mean()
        mid = close.rolling(20, min_periods=20).mean()
        sd = close.rolling(20, min_periods=20).std()
        lower = mid - 2.0 * sd
        vma = vol.rolling(20, min_periods=20).mean()
        rsi_os[c] = (rsi < 30.0).fillna(False)
        macd_pos[c] = (hist > 0.0).fillna(False)
        ma_gold[c] = ((close > ma20) & (ma20 > ma60)).fillna(False)
        bb_low[c] = (close < lower).fillna(False)
        vol_up[c] = ((vol > vma) & (close > close.shift(1))).fillna(False)
    return {
        "RSI14_OS": rsi_os,
        "MACD_HIST": macd_pos,
        "MA_GOLD": ma_gold,
        "BB_LOWER": bb_low,
        "VOL_UP": vol_up,
    }


def rank_key(row: dict) -> tuple:
    tip = row["tip_gates"]
    ytd, t1 = tip["ytd"]["gate"], tip["trailing_1y"]["gate"]
    tip_clean = ytd == "PASS" and t1 == "PASS"
    no_pause = ytd != "PAUSE_REVIEW" and t1 != "PAUSE_REVIEW" and ytd != "INSUFFICIENT"
    held = row["heldout"]["score"]
    vs_live = row.get("vs_live_heldout_score_delta")
    beat_live = vs_live is not None and vs_live > 0 and tip_clean
    return (
        1 if tip_clean and held > 0 else 0,
        1 if beat_live else 0,
        1 if no_pause else 0,
        held,
    )


def eval_book(
    *,
    book_id: str,
    family: str,
    nav_equal: pd.DataFrame,
    win_equal: dict,
    nav_live: pd.DataFrame | None,
    held_live_score: float | None,
    asof: pd.Timestamp,
    market,
    target,
    regime,
    dividends,
    policy,
    scores,
    buy_ok,
) -> dict:
    nav, fills, meta = sim(
        market, target, regime, dividends, policy=policy, scores=scores, buy_ok=buy_ok
    )
    assert meta.get("exact_t1_ok"), book_id
    win = {w: window_stats(nav, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
    tip = tip_gate(nav_equal, nav, asof)
    held = score_vs_base(win_equal["heldout_2019_plus"], win["heldout_2019_plus"])
    sealed = score_vs_base(win_equal["sealed_2023_plus"], win["sealed_2023_plus"])
    tip_vs_live = tip_gate(nav_live, nav, asof) if nav_live is not None else None
    vs_live_delta = (
        None if held_live_score is None else float(held["score"] - held_live_score)
    )
    tip_clean = tip["ytd"]["gate"] == "PASS" and tip["trailing_1y"]["gate"] == "PASS"
    return {
        "id": book_id,
        "family": family,
        "heldout": held,
        "sealed_REPORT_ONLY": sealed,
        "tip_gates_vs_equal": tip,
        "tip_gates": tip,
        "tip_gates_vs_live": tip_vs_live,
        "tip_clean": tip_clean,
        "coexist": bool(tip_clean and held["score"] > 0),
        "vs_live_heldout_score_delta": vs_live_delta,
        "n_fills": int(len(fills)),
        "full_cagr": win["full"].get("cagr"),
        "full_mdd": win["full"].get("max_drawdown"),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "outputs").mkdir(exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.9]

    print("loading ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, _s, target, regime = e16_features(market)
    cal = pd.DatetimeIndex(pd.to_datetime(market["date"]).drop_duplicates().sort_values())
    panels = _panel(market, list(FIN))

    print("BASE FIN_EQUAL ...", flush=True)
    nav_eq, _, meta_eq = sim(market, target, regime, dividends, policy=FIN_EQUAL)
    assert meta_eq.get("exact_t1_ok")
    win_eq = {w: window_stats(nav_eq, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
    asof = pd.to_datetime(nav_eq["date"]).max()
    nav_eq.to_csv(OUT / "outputs" / "base_fin_equal_daily_nav.csv", index=False)

    print("LIVE_KD_OPT ...", flush=True)
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
        family="anchor",
        nav_equal=nav_eq,
        win_equal=win_eq,
        nav_live=None,
        held_live_score=None,
        asof=asof,
        market=market,
        target=target,
        regime=regime,
        dividends=dividends,
        policy=FIN_PRE_EXDIV_KD,
        scores=kd_scores,
        buy_ok=kd_ok,
    )
    nav_live, _, _ = sim(
        market,
        target,
        regime,
        dividends,
        policy=FIN_PRE_EXDIV_KD,
        scores=kd_scores,
        buy_ok=kd_ok,
    )
    held_live = live_row["heldout"]["score"]
    live_row["vs_live_heldout_score_delta"] = 0.0
    live_row["tip_gates_vs_live"] = tip_gate(nav_live, nav_live, asof)

    print("anchor RS_EXDIV ...", flush=True)
    rs_scores = build_name_scores(market, FIN)
    rs_ok = build_exdiv_buy_ok(cal, dividends, FIN, also_stock_ex=True)
    rs_row = eval_book(
        book_id="FIN_RS_SOFT_TILT_EXDIV",
        family="anchor",
        nav_equal=nav_eq,
        win_equal=win_eq,
        nav_live=nav_live,
        held_live_score=held_live,
        asof=asof,
        market=market,
        target=target,
        regime=regime,
        dividends=dividends,
        policy=FIN_RS_SOFT_TILT_EXDIV,
        scores=rs_scores,
        buy_ok=rs_ok,
    )

    equal_row = {
        "id": "FIN_EQUAL",
        "family": "anchor",
        "heldout": {"mdd_improve_pp": 0.0, "cagr_giveback_pp": 0.0, "score": 0.0},
        "sealed_REPORT_ONLY": {"mdd_improve_pp": 0.0, "cagr_giveback_pp": 0.0, "score": 0.0},
        "tip_gates": {
            "ytd": {"giveback_pp": 0.0, "gate": "PASS", "rel_nav": 1.0},
            "trailing_1y": {"giveback_pp": 0.0, "gate": "PASS", "rel_nav": 1.0},
        },
        "tip_gates_vs_equal": {
            "ytd": {"giveback_pp": 0.0, "gate": "PASS", "rel_nav": 1.0},
            "trailing_1y": {"giveback_pp": 0.0, "gate": "PASS", "rel_nav": 1.0},
        },
        "tip_gates_vs_live": tip_gate(nav_live, nav_eq, asof),
        "tip_clean": True,
        "coexist": False,
        "vs_live_heldout_score_delta": float(0.0 - held_live),
        "n_fills": None,
        "full_cagr": win_eq["full"].get("cagr"),
        "full_mdd": win_eq["full"].get("max_drawdown"),
    }

    print("building indicator triggers ...", flush=True)
    trig = build_triggers(panels, cal, list(FIN))
    season_name, s0, s1 = SEASON
    pre = int(LIVE_KD["pre_days"])
    pre_ok = build_pre_exdiv_window_buy_ok(cal, dividends, FIN, pre_days=pre, also_stock_ex=True)
    ex_ok = build_exdiv_buy_ok(cal, dividends, FIN, also_stock_ex=True)

    challengers: list[tuple[str, str, pd.DataFrame, pd.DataFrame, str]] = []
    for key, label in (
        ("RSI14_OS", "RSI14_OS_SEASON"),
        ("MACD_HIST", "MACD_HIST_SEASON"),
        ("MA_GOLD", "MA_GOLD_SEASON"),
        ("BB_LOWER", "BB_LOWER_SEASON"),
    ):
        scores = season_first_hit_scores(
            cal,
            panels,
            dividends,
            list(FIN),
            trigger=trig[key],
            season_start=s0,
            season_end=s1,
            pre_days=pre,
        )
        challengers.append((label, "season", scores, pre_ok, FIN_PRE_EXDIV_KD))
    for key, label in (
        ("RSI14_OS", "RSI14_OS_ALWAYS"),
        ("MACD_HIST", "MACD_HIST_ALWAYS"),
        ("MA_GOLD", "MA_GOLD_ALWAYS"),
        ("VOL_UP", "VOL_UP_ALWAYS"),
    ):
        scores = always_on_scores(cal, trig[key], list(FIN))
        challengers.append((label, "always", scores, ex_ok, FIN_RS_SOFT_TILT_EXDIV))

    rows = [equal_row, live_row, rs_row]
    for book_id, family, scores, buy_ok, policy in challengers:
        print(f"challenger {book_id} ...", flush=True)
        rows.append(
            eval_book(
                book_id=book_id,
                family=family,
                nav_equal=nav_eq,
                win_equal=win_eq,
                nav_live=nav_live,
                held_live_score=held_live,
                asof=asof,
                market=market,
                target=target,
                regime=regime,
                dividends=dividends,
                policy=policy,
                scores=scores,
                buy_ok=buy_ok,
            )
        )

    ranked = sorted(rows, key=rank_key, reverse=True)
    coexist = [r for r in ranked if r.get("coexist")]
    beat_live = [
        r
        for r in ranked
        if r.get("coexist")
        and r.get("vs_live_heldout_score_delta") is not None
        and r["vs_live_heldout_score_delta"] > 0
        and r["id"] != "LIVE_KD_OPT"
    ]

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "INDICATOR_BUY_SELL_SCREEN_R1",
        "charter": "research/ops/INDICATOR_BUY_SELL_CHARTER.md",
        "status": "PAPER_SCREEN_DONE",
        "live_wire": False,
        "soft_frozen_clip": soft.SOFT_FROZEN_FIN_CLIP,
        "asof": str(pd.Timestamp(asof).date()),
        "capital": CAPITAL,
        "lot": LOT,
        "live_kd_opt": LIVE_KD,
        "season_lock": {"name": season_name, "start": list(s0), "end": list(s1)},
        "n_books": len(rows),
        "n_coexist": len(coexist),
        "n_beat_live": len(beat_live),
        "ranking": [r["id"] for r in ranked],
        "coexist_ids": [r["id"] for r in coexist],
        "beat_live_ids": [r["id"] for r in beat_live],
        "books": ranked,
        "verdict": (
            "PROMOTE_CANDIDATE_TO_DUAL_PAPER"
            if beat_live
            else ("COEXIST_NO_LIFT_VS_LIVE" if coexist else "NO_COEXIST_STOP_OR_AUTOPSY")
        ),
        "non_actions": [
            "No Soft-Frozen flip",
            "No live KD_OPT change",
            "No E45 stitch",
            "No auto cutover",
        ],
    }
    (OUT / "reports").mkdir(exist_ok=True)
    (OUT / "reports" / "indicator_buy_sell_screen_r1.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (RESEARCH / "INDICATOR_BUY_SELL_SCREEN_R1.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# Indicator Buy/Sell Screen — Round 1",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Asof NAV: **{payload['asof']}** · Soft-Frozen **{soft.SOFT_FROZEN_FIN_CLIP}** KEEP",
        f"Charter: `INDICATOR_BUY_SELL_CHARTER.md`",
        f"Verdict: **`{payload['verdict']}`**",
        "",
        "## Summary",
        "",
        f"- Books screened: **{payload['n_books']}**",
        f"- Coexist (tip PASS + held-out&gt;0 vs EQUAL): **{payload['n_coexist']}** → `{payload['coexist_ids']}`",
        f"- Beat live KD_OPT on held-out (and tip-clean): **{payload['n_beat_live']}** → `{payload['beat_live_ids']}`",
        "",
        "## Scoreboard (held-out vs FIN_EQUAL)",
        "",
        "| ID | Family | Tip YTD | Tip 1y | Held score | MDDΔpp | CAGRΔpp | vs live held Δ | Coexist |",
        "|---|---|---|---|---:|---:|---:|---:|:---:|",
    ]
    for r in ranked:
        tip = r["tip_gates"]
        h = r["heldout"]
        lines.append(
            "| `{id}` | {fam} | {ytd} | {t1} | {hs:.3f} | {mdd:.3f} | {cagr} | {vl} | {co} |".format(
                id=r["id"],
                fam=r["family"],
                ytd=tip["ytd"]["gate"],
                t1=tip["trailing_1y"]["gate"],
                hs=float(h["score"]),
                mdd=float(h["mdd_improve_pp"]),
                cagr=("—" if h["cagr_giveback_pp"] is None else f"{h['cagr_giveback_pp']:.3f}"),
                vl=(
                    "—"
                    if r.get("vs_live_heldout_score_delta") is None
                    else f"{r['vs_live_heldout_score_delta']:.3f}"
                ),
                co="Y" if r.get("coexist") else "",
            )
        )
    lines += [
        "",
        "## Reading",
        "",
        "- Coexist ≠ live promote.",
        "- Beat-live list empty → keep live KD_OPT; Round-2 only if human OPEN (e.g. TEL indicators / sleeve-router).",
        "- Soft-Frozen / live wire unchanged.",
        "",
        "## Non-actions",
        "",
        "- No Soft-Frozen flip / no live KD_OPT retune / no E45 stitch / no auto cutover",
        "",
        "## Label",
        "",
        "`INDICATOR_BUY_SELL_SCREEN_R1_2026-09-10`",
        "",
    ]
    md = "\n".join(lines)
    (RESEARCH / "INDICATOR_BUY_SELL_SCREEN_R1.md").write_text(md, encoding="utf-8")
    (OUT / "reports" / "INDICATOR_BUY_SELL_SCREEN_R1.md").write_text(md, encoding="utf-8")
    print(json.dumps({"verdict": payload["verdict"], "coexist": payload["coexist_ids"], "beat_live": payload["beat_live_ids"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
