#!/usr/bin/env python3
"""FIN both-quality Stage B — WR densify on joint seed (paper).

Charter: research/ops/FIN_BOTH_QUALITY_STAGEB_CHARTER.md
Parent Stage A WIN_SOFT · seed BOTH_OR_K9_x_HARD120 · KEEP SELL_a75 · CAGR=chal−base.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

import e16_clip_search_challenger as clip
import e16_soft_frozen_base as soft
import e22_dividend_accounting as e22div
import e45_defend_handoff_stagea_screen as stagea
from cool_c8_proxy_observe_helpers import build_cool_c8_exposure
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, load_market, window_stats
from e50_early_stack_combined_nav import FIN, e16_features, simulate_core
from fin_buy_quality_helpers import (
    and_buy_ok,
    apply_filter_in_season,
    below_ma_ok,
    catalog_gate,
    close_panel,
    forward_win_stats,
    kd_season_mask,
    or_and_exception,
    or_buy_ok,
    raw_close_panel,
)
from fin_sell_quality_helpers import (
    cagr_lift_pp,
    dampen_sell_when_false,
    forward_sell_win_stats,
    not_gate,
)
from live_config import LIVE_FUSE_SOFT_SELL_BOOST
from ops_repro_ssot import write_ops_and_repro_pointer
from portfolio_capital import DEFAULT_CAPITAL
from research_metric_helpers import mdd_delta_pp
from sleeve_tilt_helpers import ALPHA as LIVE_SLEEVE_ALPHA, sleeve_signal_panel
from soft_assist_helpers import (
    BUY_LOW_ID,
    LIVE_KD,
    SELL_HIGH_ID,
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
REPRO = ROOT / "repro" / "fin-both-quality-stageb"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_BOTH_QUALITY_STAGEB_CHARTER"
SCREEN_ID = "FIN_BOTH_QUALITY_STAGEB_SCREEN"
DECISION_ID = "FIN_BOTH_QUALITY_STAGEB_DECISION_PACK"
BASE_ID = "CTRL_BASE"
SEED_ID = "SEED_OR_K9_x_HARD120"
E22_VERSION = e22div.DEFAULT_BOOKS_VERSION
SELL_AMP = float(LIVE_FUSE_SOFT_SELL_BOOST)

CAGR_FLOOR_PP = 0.15
HELD_MDD_MIN_PP = -0.25
HELD_ABS_MDD_MAX = 0.15
TIP_MDD_MIN_PP = 0.0
WR_HIT_PP = 0.5
WR_OBS_PP = -0.5
WIN_H = 21

GRID: list[dict[str, Any]] = [
    {"id": "CTRL_BASE", "buy": None, "sell": None},
    {"id": "SEED_OR_K9_x_HARD120", "buy": "OR_K9", "sell": "HARD_MA120"},
    {"id": "SEED_MA120_x_HARD120", "buy": "MA120", "sell": "HARD_MA120"},
    {"id": "B_OR_K9_x_HARD90", "buy": "OR_K9", "sell": "HARD_MA90"},
    {"id": "B_OR_K9_x_HARD100", "buy": "OR_K9", "sell": "HARD_MA100"},
    {"id": "B_OR_K9_x_HARD150", "buy": "OR_K9", "sell": "HARD_MA150"},
    {"id": "B_OR_K9_x_HARD120_AND_RSI6", "buy": "OR_K9", "sell": "HARD120_AND_RSI6"},
    {"id": "B_OR_K9_x_HARD120_AND_RSI14", "buy": "OR_K9", "sell": "HARD120_AND_RSI14"},
    {"id": "B_OR_K9_x_HARD120_AND_K9", "buy": "OR_K9", "sell": "HARD120_AND_K9"},
    {"id": "B_OR_K9_x_HARD120_OR_RSI6", "buy": "OR_K9", "sell": "HARD120_OR_RSI6"},
    {"id": "B_HYBRID_C_x_HARD120", "buy": "HYBRID_C", "sell": "HARD_MA120"},
    {"id": "B_OR_K9_KD_x_HARD120", "buy": "OR_K9_KD", "sell": "HARD_MA120"},
    {"id": "B_OR_K9_x_DAMP120_d25", "buy": "OR_K9", "sell": "DAMP_MA120_25"},
]


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _pack(nav: pd.DataFrame) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, (a, b) in WINDOWS_STANDARD.items():
        st = window_stats(nav, a, b)
        out[k] = {
            "cagr": None if st.get("cagr") is None else round(float(st["cagr"]), 6),
            "max_drawdown": None
            if st.get("max_drawdown") is None
            else round(float(st["max_drawdown"]), 6),
            "n_days": int(st.get("n_days") or 0),
        }
    return out


def _tip(base_nav: pd.DataFrame, chal_nav: pd.DataFrame) -> dict[str, Any]:
    asof = pd.Timestamp(pd.to_datetime(base_nav["date"]).max())
    b_dates = pd.to_datetime(base_nav["date"])
    c_dates = pd.to_datetime(chal_nav["date"])
    out: dict[str, Any] = {}
    for wname, start in (
        ("ytd", pd.Timestamp(asof.year, 1, 1)),
        ("trailing_1y", asof - pd.Timedelta(days=365)),
    ):
        b = base_nav[(b_dates >= start) & (b_dates <= asof)].reset_index(drop=True)
        c = chal_nav[(c_dates >= start) & (c_dates <= asof)].reset_index(drop=True)
        if len(b) < 20 or len(c) < 20:
            out[wname] = {"mdd_improve_pp": None, "cagr_lift_pp": None, "gate": "INSUFFICIENT"}
            continue
        bn = b["nav"].astype(float) / float(b["nav"].iloc[0])
        cn = c["nav"].astype(float) / float(c["nav"].iloc[0])
        b_mdd = float((bn / bn.cummax() - 1.0).min())
        c_mdd = float((cn / cn.cummax() - 1.0).min())
        years = (len(b) - 1) / 252.0
        bc = float(bn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        cc = float(cn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        out[wname] = {
            "mdd_improve_pp": round(float(mdd_delta_pp(b_mdd, c_mdd)), 4),
            "cagr_lift_pp": None
            if (lift := cagr_lift_pp(bc, cc)) is None
            else round(float(lift), 4),
            "gate": "PASS",
        }
    return out


def _buy_scores(kd, lows, k9_amp: float = 1.0) -> pd.DataFrame:
    out = soft_boost_scores(kd, lows[BUY_LOW_ID], 1.0)
    return soft_boost_scores(out, lows["K9_LT30"], float(k9_amp))


def _sell_base(highs, amp: float = SELL_AMP) -> pd.DataFrame:
    return soft_sell_panel(highs[SELL_HIGH_ID], boost=float(amp))


def _sleeve_score(market, sleeve, alpha: float) -> pd.DataFrame:
    _p, _s, _t, _r, base_score = soft.build_soft_frozen_targets(market)
    tilt = sleeve_signal_panel(sleeve, "rsi_lt30", 14)
    return base_score + float(alpha) * tilt


def _target_live(score, regime):
    return clip.build_targets_with_clips(
        regime=regime,
        score=score,
        fin_lo=float(soft.SOFT_FROZEN_FIN_LO),
        fin_hi=float(soft.SOFT_FROZEN_FIN_HI),
        tel_lo=float(soft.SOFT_FROZEN_TEL_LO),
        tel_hi=float(soft.SOFT_FROZEN_TEL_HI),
        etf_lo=float(soft.SOFT_FROZEN_ETF_LO),
        etf_hi=float(soft.SOFT_FROZEN_ETF_HI),
    )


def _cool_from_offense(market, offense_nav: pd.DataFrame) -> pd.Series:
    nav_s = stagea._nav_series(offense_nav)
    feat = stagea._risk_features(market, nav_s)
    dates = pd.DatetimeIndex(nav_s.index)
    return build_cool_c8_exposure(dates, feat["proxy_mdd63"])


def _buy_extra(
    name: str | None,
    *,
    lows: dict,
    season: pd.Series,
) -> pd.DataFrame | None:
    if name is None:
        return None
    hard = catalog_gate(lows["BELOW_MA120"])
    if name == "MA120":
        return hard
    if name == "OR_K9":
        return or_buy_ok(hard, catalog_gate(lows["K9_LT30"]))
    if name == "HYBRID_C":
        return or_and_exception(hard, catalog_gate(lows["K9_LT30"]), catalog_gate(lows["BELOW_MA60"]))
    if name == "OR_K9_KD":
        gate = or_buy_ok(hard, catalog_gate(lows["K9_LT30"]))
        return apply_filter_in_season(gate, season, in_season=True)
    raise ValueError(f"unknown buy {name}")


def _sell_overlay(
    name: str | None,
    *,
    lows: dict,
    highs: dict,
    raw_closes: pd.DataFrame,
    sell0: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame | None]:
    if name is None:
        return sell0, None
    q120 = not_gate(lows["BELOW_MA120"])
    if name == "HARD_MA120":
        return sell0, q120
    if name == "HARD_MA60":
        return sell0, not_gate(lows["BELOW_MA60"])
    if name.startswith("HARD_MA") and name[7:].isdigit():
        w = int(name.replace("HARD_MA", ""))
        return sell0, not_gate(below_ma_ok(raw_closes, w))
    if name == "HARD120_AND_RSI6":
        return sell0, and_buy_ok(q120, catalog_gate(highs["RSI6_GT80"]))
    if name == "HARD120_AND_RSI14":
        return sell0, and_buy_ok(q120, catalog_gate(highs["RSI14_GT70"]))
    if name == "HARD120_AND_K9":
        return sell0, and_buy_ok(q120, catalog_gate(highs["K9_GT70"]))
    if name == "HARD120_OR_RSI6":
        return sell0, or_buy_ok(q120, catalog_gate(highs["RSI6_GT80"]))
    if name == "DAMP_MA120_25":
        return dampen_sell_when_false(sell0, q120, 0.25), None
    if name == "DAMP_MA120_50":
        return dampen_sell_when_false(sell0, q120, 0.50), None
    raise ValueError(f"unknown sell {name}")


def _sim(market, target, regime, dividends, *, scores, buy_ok, sell, exposure, sell_ok=None):
    kw: dict[str, Any] = {
        "apply_e22": True,
        "apply_stock_div": True,
        "capital": float(DEFAULT_CAPITAL),
        "lot_size": int(BOARD_LOT),
        "financial_alloc": FIN_PRE_EXDIV_KD,
        "telecom_alloc": TEL_EQUAL,
        "fin_name_scores": scores,
        "fin_buy_ok": buy_ok,
        "fin_sell_scores": sell,
        "e45_exposure": exposure.astype(float),
        "e22_version": E22_VERSION,
    }
    if sell_ok is not None:
        kw["fin_sell_ok"] = sell_ok
    nav, fills, meta = simulate_core(market, target, regime, dividends, **kw)
    if not bool(meta.get("exact_t1_ok")):
        raise RuntimeError("exact_t1_ok failed")
    return nav, fills, meta


def _eval_row(
    base_w: dict,
    chal_w: dict,
    tip: dict,
    *,
    book_id: str,
    buy_wr: dict,
    sell_wr: dict,
    base_buy_wr: dict | None,
    base_sell_wr: dict | None,
) -> dict[str, Any]:
    held_b = base_w.get("heldout_2019_plus") or {}
    held_c = chal_w.get("heldout_2019_plus") or {}
    cagr_pp = cagr_lift_pp(held_b.get("cagr"), held_c.get("cagr"))
    mdd_pp = mdd_delta_pp(held_b.get("max_drawdown"), held_c.get("max_drawdown"))
    abs_mdd = held_c.get("max_drawdown")
    tip_ytd = (tip.get("ytd") or {}).get("mdd_improve_pp")
    tip_1y = (tip.get("trailing_1y") or {}).get("mdd_improve_pp")
    tip_ok = (
        tip_ytd is not None
        and tip_1y is not None
        and float(tip_ytd) >= TIP_MDD_MIN_PP
        and float(tip_1y) >= TIP_MDD_MIN_PP
    )
    cagr_ok = cagr_pp is not None and float(cagr_pp) >= CAGR_FLOOR_PP
    mdd_ok = mdd_pp is not None and float(mdd_pp) >= HELD_MDD_MIN_PP
    band_ok = abs_mdd is not None and abs(float(abs_mdd)) <= HELD_ABS_MDD_MAX
    buy_pp = None
    if base_buy_wr and base_buy_wr.get("win_rate") is not None and buy_wr.get("win_rate") is not None:
        buy_pp = round(float(buy_wr["win_rate"]) - float(base_buy_wr["win_rate"]), 4)
    sell_pp = None
    if base_sell_wr and base_sell_wr.get("win_rate") is not None and sell_wr.get("win_rate") is not None:
        sell_pp = round(float(sell_wr["win_rate"]) - float(base_sell_wr["win_rate"]), 4)
    wr_hit = (buy_pp is not None and float(buy_pp) >= WR_HIT_PP) or (
        sell_pp is not None and float(sell_pp) >= WR_HIT_PP
    )
    wr_obs = (buy_pp is not None and float(buy_pp) >= WR_OBS_PP) or (
        sell_pp is not None and float(sell_pp) >= WR_OBS_PP
    )
    # Prefer either-side: if one side missing, still allow the other
    if buy_pp is None and sell_pp is None:
        wr_hit = False
        wr_obs = False
    elif buy_pp is None:
        wr_hit = sell_pp is not None and float(sell_pp) >= WR_HIT_PP
        wr_obs = sell_pp is not None and float(sell_pp) >= WR_OBS_PP
    elif sell_pp is None:
        wr_hit = float(buy_pp) >= WR_HIT_PP
        wr_obs = float(buy_pp) >= WR_OBS_PP
    else:
        wr_hit = float(buy_pp) >= WR_HIT_PP or float(sell_pp) >= WR_HIT_PP
        wr_obs = float(buy_pp) >= WR_OBS_PP or float(sell_pp) >= WR_OBS_PP

    economic = bool(cagr_ok and mdd_ok and band_ok and tip_ok)
    is_chal = book_id != BASE_ID
    hit = bool(economic and wr_hit and is_chal)
    observe_ok = bool(economic and wr_obs and is_chal)
    return {
        "held_cagr_lift_pp": None if cagr_pp is None else round(float(cagr_pp), 4),
        "held_mdd_pp": None if mdd_pp is None else round(float(mdd_pp), 4),
        "held_abs_mdd": None if abs_mdd is None else round(float(abs_mdd), 6),
        "tip_ytd_mdd_pp": tip_ytd,
        "tip_1y_mdd_pp": tip_1y,
        "buy_win_rate_pp": buy_pp,
        "sell_win_rate_pp": sell_pp,
        "buy_win_n": buy_wr.get("n"),
        "sell_win_n": sell_wr.get("n"),
        "gates": {
            "cagr": bool(cagr_ok),
            "mdd_near_flat": bool(mdd_ok),
            "mdd_band": bool(band_ok),
            "tip_safe": bool(tip_ok),
            "wr_hit": bool(wr_hit),
            "wr_obs": bool(wr_obs),
            "economic": economic,
        },
        "hit": hit,
        "observe_ok": observe_ok,
        "cagr_sign": "chal_minus_base",
    }


def _verdict(rows: list[dict[str, Any]]) -> str:
    legal = [r for r in rows if r["id"] != BASE_ID]
    if any(r["eval"]["hit"] for r in legal):
        return "BOTH_QUALITY_HIT"
    seed = next((r for r in rows if r["id"] == SEED_ID), None)
    micros = [r for r in legal if r["id"] != SEED_ID and not str(r["id"]).startswith("SEED_")]
    if any(r["eval"]["hit"] for r in micros):
        return "BOTH_QUALITY_HIT"
    obs = [r for r in legal if r["eval"]["observe_ok"]]
    if obs:
        # If seed observe-ok and no micro beats seed on WR among economic
        if seed and seed["eval"]["observe_ok"]:
            better = [
                r
                for r in micros
                if r["eval"]["gates"]["economic"]
                and r["eval"]["gates"]["wr_hit"] is False
                and r["eval"]["observe_ok"]
                and float(r["eval"]["held_cagr_lift_pp"] or -9)
                > float(seed["eval"]["held_cagr_lift_pp"] or -9) + 0.05
            ]
            if not any(r["eval"]["gates"]["wr_hit"] for r in micros) and not better:
                # check if any micro improves WR while economic
                wr_better = [
                    r
                    for r in micros
                    if r["eval"]["gates"]["economic"]
                    and max(
                        float(r["eval"]["buy_win_rate_pp"] or -99),
                        float(r["eval"]["sell_win_rate_pp"] or -99),
                    )
                    > max(
                        float(seed["eval"]["buy_win_rate_pp"] or -99),
                        float(seed["eval"]["sell_win_rate_pp"] or -99),
                    )
                    + 0.25
                ]
                if not wr_better:
                    return "PARENT_KEEP"
        return "OBSERVE_RECOMMENDED"
    if any(r["eval"]["gates"]["economic"] for r in legal):
        return "WIN_SOFT"
    if any(r["eval"]["gates"]["cagr"] for r in legal):
        return "MDD_BLOCK"
    return "NO_EDGE"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    REP.mkdir(parents=True, exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.8]
    assert abs(SELL_AMP - 0.75) < 1e-12

    market = load_market()
    dividends = load_dividends()
    _p, sleeve, _t, regime = e16_features(market)
    cal = pd.DatetimeIndex(pd.to_datetime(sorted(market["date"].unique())))
    lows, highs = build_low_high_catalog(market, cal, list(FIN))
    closes = close_panel(market, cal, list(FIN))
    raw_closes = raw_close_panel(market, cal, list(FIN))
    season = kd_season_mask(
        cal,
        season_start=LIVE_KD["season_start"],
        season_end=LIVE_KD["season_end"],
    )
    kd = build_kd_season_tilt_scores(
        market,
        dividends,
        list(FIN),
        k_thresh=float(LIVE_KD["k_thresh"]),
        season_start=LIVE_KD["season_start"],
        season_end=LIVE_KD["season_end"],
        pre_days=int(LIVE_KD["pre_days"]),
        active_score=float(LIVE_KD["active_score"]),
    )
    base_buy_ok = build_pre_exdiv_window_buy_ok(
        cal, dividends, list(FIN), pre_days=int(LIVE_KD["pre_days"]), also_stock_ex=True
    )
    scores = _buy_scores(kd, lows)
    sell0 = _sell_base(highs)
    sleeve_sc = _sleeve_score(market, sleeve, LIVE_SLEEVE_ALPHA)
    target = _target_live(sleeve_sc, regime)

    print("offense NAV for cool ...", flush=True)
    off_nav, _f, _m = simulate_core(
        market,
        target,
        regime,
        dividends,
        apply_e22=True,
        apply_stock_div=True,
        capital=float(DEFAULT_CAPITAL),
        lot_size=int(BOARD_LOT),
        financial_alloc=FIN_PRE_EXDIV_KD,
        telecom_alloc=TEL_EQUAL,
        fin_name_scores=scores,
        fin_buy_ok=base_buy_ok,
        fin_sell_scores=sell0,
        e22_version=E22_VERSION,
    )
    cool = _cool_from_offense(market, off_nav)

    rows: list[dict[str, Any]] = []
    base_nav = None
    base_w = None
    base_buy_wr: dict[str, Any] | None = None
    base_sell_wr: dict[str, Any] | None = None
    fin_set = set(FIN)

    for spec in GRID:
        bid = str(spec["id"])
        extra = _buy_extra(spec.get("buy"), lows=lows, season=season)
        buy_ok = base_buy_ok if extra is None else and_buy_ok(base_buy_ok, extra)
        sell, sell_ok = _sell_overlay(
            spec.get("sell"), lows=lows, highs=highs, raw_closes=raw_closes, sell0=sell0
        )
        print(f"{bid} ...", flush=True)
        nav, fills, meta = _sim(
            market,
            target,
            regime,
            dividends,
            scores=scores,
            buy_ok=buy_ok,
            sell=sell,
            exposure=cool,
            sell_ok=sell_ok,
        )
        nav.to_csv(OUT / f"nav_{bid}.csv", index=False)
        fills.to_csv(OUT / f"fills_{bid}.csv", index=False)
        w = _pack(nav)
        buy_wr = forward_win_stats(fills, closes, codes=fin_set, side="BUY", horizon=WIN_H)
        sell_wr = forward_sell_win_stats(fills, closes, codes=fin_set, horizon=WIN_H)
        if bid == BASE_ID:
            base_nav = nav
            base_w = w
            base_buy_wr = buy_wr
            base_sell_wr = sell_wr
            tip = {
                "ytd": {"mdd_improve_pp": 0.0, "cagr_lift_pp": 0.0, "gate": "PASS"},
                "trailing_1y": {"mdd_improve_pp": 0.0, "cagr_lift_pp": 0.0, "gate": "PASS"},
            }
        else:
            assert base_nav is not None and base_w is not None
            tip = _tip(base_nav, nav)
        ev = _eval_row(
            base_w or w,
            w,
            tip,
            book_id=bid,
            buy_wr=buy_wr,
            sell_wr=sell_wr,
            base_buy_wr=base_buy_wr,
            base_sell_wr=base_sell_wr,
        )
        rows.append(
            {
                "id": bid,
                "windows": w,
                "tip": tip,
                "eval": ev,
                "buy_wr": buy_wr,
                "sell_wr": sell_wr,
                "spec": spec,
                "n_fills": int(len(fills)),
                "exact_t1_ok": bool(meta.get("exact_t1_ok")),
            }
        )
        print(json.dumps({"book": bid, "eval": ev}, ensure_ascii=False), flush=True)

    verdict = _verdict(rows)
    generated = _utc()
    payload = {
        "label": f"{SCREEN_ID}_{generated.replace(':', '').replace('-', '')}",
        "generated_at_utc": generated,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "status": "STAGE_B_SCREEN_DONE",
        "verdict": verdict,
        "live_wire": False,
        "sell_a75_keep": True,
        "cagr_sign": "chal_minus_base",
        "parent_stage_a": "WIN_SOFT",
        "seed_id": SEED_ID,
        "base_id": BASE_ID,
        "gates": {
            "held_cagr_lift_pp": CAGR_FLOOR_PP,
            "held_mdd_pp_floor": HELD_MDD_MIN_PP,
            "held_abs_mdd_max": HELD_ABS_MDD_MAX,
            "tip_mdd_pp_floor": TIP_MDD_MIN_PP,
            "wr_hit_pp": WR_HIT_PP,
            "wr_obs_pp": WR_OBS_PP,
            "win_horizon": WIN_H,
        },
        "books": [
            {
                "id": r["id"],
                "windows": r["windows"],
                "tip": r["tip"],
                "eval": r["eval"],
                "buy_wr": r["buy_wr"],
                "sell_wr": r["sell_wr"],
                "spec": r["spec"],
                "n_fills": r["n_fills"],
                "exact_t1_ok": r["exact_t1_ok"],
            }
            for r in rows
        ],
        "binding": [
            "Soft-Frozen / Exact T+1 / COOL / SELL_a75 KEEP",
            "CAGR↑ = chal − base",
            "Stage B densify for WR around Stage A seed",
            "Sell loss-defer REJECTED",
            "No live wire from Stage B",
        ],
    }
    screen_md = "\n".join(
        [
            f"# {SCREEN_ID}",
            "",
            f"Date: 2026-09-28 · Generated `{generated}`",
            f"Status: **{verdict}** · Soft-Frozen **KEEP** · SELL_a75 **KEEP** · live wire **false**",
            "",
            f"Parent Stage A `WIN_SOFT` · seed `{SEED_ID}` · CAGR↑=chal−base · WR HIT≥{WR_HIT_PP}pp.",
            "",
            "## Books",
            "",
            "| ID | CAGR↑pp | MDD↑pp | tip↑ | buyWR↑ | sellWR↑ | HIT | obs |",
            "|---|---:|---:|---:|---:|---:|---|---|",
        ]
        + [
            "| {id} | {cagr} | {mdd} | {ytd} | {bwr} | {swr} | {hit} | {obs} |".format(
                id=r["id"],
                cagr=r["eval"]["held_cagr_lift_pp"],
                mdd=r["eval"]["held_mdd_pp"],
                ytd=r["eval"]["tip_ytd_mdd_pp"],
                bwr=r["eval"]["buy_win_rate_pp"],
                swr=r["eval"]["sell_win_rate_pp"],
                hit=r["eval"]["hit"],
                obs=r["eval"]["observe_ok"],
            )
            for r in rows
        ]
        + [
            "",
            f"Verdict: **`{verdict}`**",
            "",
            f"Label: `{SCREEN_ID}_2026-09-28__{verdict}`",
            "",
        ]
    )
    (OPS / f"{SCREEN_ID}.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (OPS / f"{SCREEN_ID}.md").write_text(screen_md, encoding="utf-8")
    (REP / f"{SCREEN_ID}.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (REP / f"{SCREEN_ID}.md").write_text(screen_md, encoding="utf-8")

    best = next((r for r in rows if r["eval"]["hit"]), None)
    obs = [r for r in rows if r["eval"]["observe_ok"] and r["id"] != BASE_ID]
    obs.sort(
        key=lambda r: (
            float(r["eval"]["held_cagr_lift_pp"] or -9),
            max(float(r["eval"]["buy_win_rate_pp"] or -99), float(r["eval"]["sell_win_rate_pp"] or -99)),
        ),
        reverse=True,
    )

    dlines = [
        f"# {DECISION_ID}",
        "",
        f"Date: 2026-09-28 · Generated `{generated}`",
        f"Status: **{verdict}** · Soft-Frozen **KEEP** · SELL_a75 **KEEP** · live wire **false**",
        "",
        f"Charter: `{CHARTER_ID}.md`",
        f"Screen: `{SCREEN_ID}.md`",
        f"Parent: Stage A `WIN_SOFT` · seed `{SEED_ID}`",
        "",
        "## Verdict",
        "",
        f"**`{verdict}`**",
        "",
        "CAGR sign: **chal − base**. WR densify around joint seed.",
        "",
    ]
    if best:
        dlines += [
            (
                f"Best HIT: `{best['id']}` · CAGR↑ {best['eval']['held_cagr_lift_pp']}pp · "
                f"MDD↑ {best['eval']['held_mdd_pp']}pp · buyWR↑ {best['eval']['buy_win_rate_pp']} · "
                f"sellWR↑ {best['eval']['sell_win_rate_pp']}"
            ),
            "",
        ]
    elif obs:
        top = obs[0]
        dlines += [
            (
                f"Best observe-eligible: `{top['id']}` · CAGR↑ {top['eval']['held_cagr_lift_pp']}pp · "
                f"MDD↑ {top['eval']['held_mdd_pp']}pp · buyWR↑ {top['eval']['buy_win_rate_pp']} · "
                f"sellWR↑ {top['eval']['sell_win_rate_pp']}"
            ),
            "",
        ]
    else:
        dlines += ["No book cleared HIT or observe-eligible WR floors.", ""]

    dlines += [
        "## Binding",
        "",
        "1. Soft-Frozen / tip / Exact T+1 / **SELL_a75** KEEP",
        "2. Even HIT / OBSERVE → paper ballot only",
        "3. Sell loss-defer remains REJECTED",
        "",
        f"Label: `{DECISION_ID}_2026-09-28__{verdict}__NO_LIVE`",
        "",
    ]
    decision = {
        "label": f"{DECISION_ID}_2026-09-28__{verdict}__NO_LIVE",
        "status": verdict,
        "live_wire": False,
        "sell_a75_keep": True,
        "cagr_sign": "chal_minus_base",
        "charter": f"research/ops/{CHARTER_ID}.md",
        "screen": f"research/ops/{SCREEN_ID}.md",
        "best_hit": None if best is None else best["id"],
        "best_observe": None if not obs else obs[0]["id"],
        "generated_at_utc": generated,
    }
    write_ops_and_repro_pointer(
        OPS / f"{DECISION_ID}.json",
        REP / f"{DECISION_ID}.json",
        json.dumps(decision, indent=2, ensure_ascii=False) + "\n",
    )
    write_ops_and_repro_pointer(
        OPS / f"{DECISION_ID}.md",
        REP / f"{DECISION_ID}.md",
        "\n".join(dlines),
    )

    for path, old, new in (
        (
            OPS / f"{CHARTER_ID}.md",
            "Status: **Stage B OPEN**",
            f"Status: **Stage B DONE — `{verdict}`**",
        ),
        (
            OPS / f"{CHARTER_ID}.zh-TW.md",
            "狀態：**Stage B OPEN**",
            f"狀態：**Stage B DONE — `{verdict}`**",
        ),
    ):
        txt = path.read_text(encoding="utf-8")
        if old in txt:
            path.write_text(txt.replace(old, new, 1), encoding="utf-8")

    (OPS / f"{CHARTER_ID}.json").write_text(
        json.dumps(
            {
                "label": f"{CHARTER_ID}_2026-09-28__DONE_{verdict}__NO_LIVE_WIRE",
                "status": "DONE",
                "verdict": verdict,
                "date": "2026-09-28",
                "live_wire": False,
                "sell_a75_keep": True,
                "cagr_sign": "chal_minus_base",
                "seed": SEED_ID,
                "charter": f"research/ops/{CHARTER_ID}.md",
                "script": "scripts/fin_both_quality_stageb.py",
                "screen": f"research/ops/{SCREEN_ID}.md",
                "decision": f"research/ops/{DECISION_ID}.md",
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"verdict": verdict, "n_books": len(rows)}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
