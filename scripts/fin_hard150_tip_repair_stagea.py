#!/usr/bin/env python3
"""FIN HARD150 tip/near-window repair Stage A (paper).

Charter: research/ops/FIN_HARD150_TIP_REPAIR_STAGEA_CHARTER.md
Parent: both-quality Stage B HIT B_OR_K9_x_HARD150 (OPEN observe; tip YTD/1y CAGR PAUSE).
Goal: clear tip CAGR giveback while keeping held economic gates. Soft-Frozen / SELL_a75 KEEP.
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
REPRO = ROOT / "repro" / "fin-hard150-tip-repair-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_HARD150_TIP_REPAIR_STAGEA_CHARTER"
SCREEN_ID = "FIN_HARD150_TIP_REPAIR_STAGEA_SCREEN"
DECISION_ID = "FIN_HARD150_TIP_REPAIR_STAGEA_DECISION_PACK"
BASE_ID = "CTRL_BASE"
LOCK_ID = "LOCK_HARD150"
E22_VERSION = e22div.DEFAULT_BOOKS_VERSION
SELL_AMP = float(LIVE_FUSE_SOFT_SELL_BOOST)

CAGR_FLOOR_PP = 0.15
HELD_MDD_MIN_PP = -0.25
HELD_ABS_MDD_MAX = 0.15
TIP_MDD_MIN_PP = 0.0
TIP_CAGR_ALERT_PP = -3.0
TIP_CAGR_PAUSE_PP = -5.0
TIP_BEAT_LOCK_PP = 3.0
WR_HIT_PP = 0.5
WIN_H = 21

GRID: list[dict[str, Any]] = [
    {"id": "CTRL_BASE", "buy": None, "sell": None},
    {"id": "LOCK_HARD150", "buy": "OR_K9", "sell": "HARD_MA150"},
    {"id": "T_HARD120", "buy": "OR_K9", "sell": "HARD_MA120"},
    {"id": "T_HARD135", "buy": "OR_K9", "sell": "HARD_MA135"},
    {"id": "T_HARD165", "buy": "OR_K9", "sell": "HARD_MA165"},
    {"id": "T_HARD180", "buy": "OR_K9", "sell": "HARD_MA180"},
    {"id": "T_MA120_x_HARD150", "buy": "MA120", "sell": "HARD_MA150"},
    {"id": "T_OR_K9_KD_x_HARD150", "buy": "OR_K9_KD", "sell": "HARD_MA150"},
    {"id": "T_HYBRID_C_x_HARD150", "buy": "HYBRID_C", "sell": "HARD_MA150"},
    {"id": "T_OR_K9_x_HARD150_SEASON", "buy": "OR_K9", "sell": "HARD150_SEASON"},
    {"id": "T_OR_K9_x_DAMP150_d50", "buy": "OR_K9", "sell": "DAMP_MA150_50"},
    {"id": "T_OR_K9_x_HARD150_OR_RSI6", "buy": "OR_K9", "sell": "HARD150_OR_RSI6"},
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


def _buy_extra(name: str | None, *, lows: dict, season: pd.Series) -> pd.DataFrame | None:
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
    season: pd.Series,
) -> tuple[pd.DataFrame, pd.DataFrame | None]:
    if name is None:
        return sell0, None
    if name.startswith("HARD_MA") and name[7:].isdigit():
        w = int(name.replace("HARD_MA", ""))
        return sell0, not_gate(below_ma_ok(raw_closes, w))
    if name == "HARD150_SEASON":
        hard = not_gate(below_ma_ok(raw_closes, 150))
        return sell0, apply_filter_in_season(hard, season, in_season=True)
    if name == "DAMP_MA150_50":
        q = not_gate(below_ma_ok(raw_closes, 150))
        return dampen_sell_when_false(sell0, q, 0.50), None
    if name == "HARD150_OR_RSI6":
        q150 = not_gate(below_ma_ok(raw_closes, 150))
        return sell0, or_buy_ok(q150, catalog_gate(highs["RSI6_GT80"]))
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
    lock_tip: dict | None,
) -> dict[str, Any]:
    held_b = base_w.get("heldout_2019_plus") or {}
    held_c = chal_w.get("heldout_2019_plus") or {}
    cagr_pp = cagr_lift_pp(held_b.get("cagr"), held_c.get("cagr"))
    mdd_pp = mdd_delta_pp(held_b.get("max_drawdown"), held_c.get("max_drawdown"))
    abs_mdd = held_c.get("max_drawdown")
    tip_ytd_mdd = (tip.get("ytd") or {}).get("mdd_improve_pp")
    tip_1y_mdd = (tip.get("trailing_1y") or {}).get("mdd_improve_pp")
    tip_ytd_cagr = (tip.get("ytd") or {}).get("cagr_lift_pp")
    tip_1y_cagr = (tip.get("trailing_1y") or {}).get("cagr_lift_pp")
    tip_mdd_ok = (
        tip_ytd_mdd is not None
        and tip_1y_mdd is not None
        and float(tip_ytd_mdd) >= TIP_MDD_MIN_PP
        and float(tip_1y_mdd) >= TIP_MDD_MIN_PP
    )
    tip_cagr_alert_ok = (
        tip_ytd_cagr is not None
        and tip_1y_cagr is not None
        and float(tip_ytd_cagr) >= TIP_CAGR_ALERT_PP
        and float(tip_1y_cagr) >= TIP_CAGR_ALERT_PP
    )
    tip_cagr_pause_ok = (
        tip_ytd_cagr is not None
        and tip_1y_cagr is not None
        and float(tip_ytd_cagr) >= TIP_CAGR_PAUSE_PP
        and float(tip_1y_cagr) >= TIP_CAGR_PAUSE_PP
    )
    beat_lock = False
    if lock_tip is not None and tip_ytd_cagr is not None and tip_1y_cagr is not None:
        ly = (lock_tip.get("ytd") or {}).get("cagr_lift_pp")
        l1 = (lock_tip.get("trailing_1y") or {}).get("cagr_lift_pp")
        if ly is not None and l1 is not None:
            beat_lock = (
                float(tip_ytd_cagr) >= float(ly) + TIP_BEAT_LOCK_PP
                and float(tip_1y_cagr) >= float(l1) + TIP_BEAT_LOCK_PP
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
    wr_hit = False
    if buy_pp is not None or sell_pp is not None:
        wr_hit = (buy_pp is not None and float(buy_pp) >= WR_HIT_PP) or (
            sell_pp is not None and float(sell_pp) >= WR_HIT_PP
        )
    held_econ = bool(cagr_ok and mdd_ok and band_ok and tip_mdd_ok)
    is_chal = book_id != BASE_ID
    tip_repair_hit = bool(is_chal and held_econ and tip_cagr_alert_ok)
    tip_repair_soft = bool(
        is_chal and held_econ and (tip_cagr_pause_ok or beat_lock) and not tip_cagr_alert_ok
    )
    return {
        "held_cagr_lift_pp": None if cagr_pp is None else round(float(cagr_pp), 4),
        "held_mdd_pp": None if mdd_pp is None else round(float(mdd_pp), 4),
        "held_abs_mdd": None if abs_mdd is None else round(float(abs_mdd), 6),
        "tip_ytd_mdd_pp": tip_ytd_mdd,
        "tip_1y_mdd_pp": tip_1y_mdd,
        "tip_ytd_cagr_pp": tip_ytd_cagr,
        "tip_1y_cagr_pp": tip_1y_cagr,
        "buy_win_rate_pp": buy_pp,
        "sell_win_rate_pp": sell_pp,
        "buy_win_n": buy_wr.get("n"),
        "sell_win_n": sell_wr.get("n"),
        "gates": {
            "held_econ": held_econ,
            "cagr": bool(cagr_ok),
            "mdd_near_flat": bool(mdd_ok),
            "mdd_band": bool(band_ok),
            "tip_mdd_ok": bool(tip_mdd_ok),
            "tip_cagr_alert_ok": bool(tip_cagr_alert_ok),
            "tip_cagr_pause_ok": bool(tip_cagr_pause_ok),
            "beat_lock_tip": bool(beat_lock),
            "wr_hit": bool(wr_hit),
        },
        "tip_repair_hit": tip_repair_hit,
        "tip_repair_soft": tip_repair_soft,
        "cagr_sign": "chal_minus_base",
    }


def _verdict(rows: list[dict[str, Any]]) -> str:
    legal = [r for r in rows if r["id"] != BASE_ID]
    if any(r["eval"]["tip_repair_hit"] for r in legal):
        return "TIP_REPAIR_HIT"
    if any(r["eval"]["tip_repair_soft"] for r in legal):
        return "TIP_REPAIR_SOFT"
    lock = next((r for r in rows if r["id"] == LOCK_ID), None)
    if lock and lock["eval"]["gates"]["held_econ"]:
        return "LOCK_KEEP_NO_TIP_LIFT"
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
    lock_tip: dict | None = None
    fin_set = set(FIN)

    for spec in GRID:
        bid = str(spec["id"])
        extra = _buy_extra(spec.get("buy"), lows=lows, season=season)
        buy_ok = base_buy_ok if extra is None else and_buy_ok(base_buy_ok, extra)
        sell, sell_ok = _sell_overlay(
            spec.get("sell"),
            lows=lows,
            highs=highs,
            raw_closes=raw_closes,
            sell0=sell0,
            season=season,
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
        if bid == LOCK_ID:
            lock_tip = tip
        rows.append(
            {
                "id": bid,
                "windows": w,
                "tip": tip,
                "eval": {},
                "buy_wr": buy_wr,
                "sell_wr": sell_wr,
                "spec": spec,
                "n_fills": int(len(fills)),
                "exact_t1_ok": bool(meta.get("exact_t1_ok")),
            }
        )
        print(json.dumps({"book": bid, "tip": tip}, ensure_ascii=False), flush=True)

    assert base_w is not None
    for r in rows:
        r["eval"] = _eval_row(
            base_w,
            r["windows"],
            r["tip"],
            book_id=r["id"],
            buy_wr=r["buy_wr"],
            sell_wr=r["sell_wr"],
            base_buy_wr=base_buy_wr,
            base_sell_wr=base_sell_wr,
            lock_tip=None if r["id"] in (BASE_ID, LOCK_ID) else lock_tip,
        )
        print(json.dumps({"book": r["id"], "eval": r["eval"]}, ensure_ascii=False), flush=True)

    verdict = _verdict(rows)
    generated = _utc()
    best = None
    for r in rows:
        if r["eval"].get("tip_repair_hit") or r["eval"].get("tip_repair_soft"):
            if best is None or float(r["eval"]["tip_ytd_cagr_pp"] or -999) > float(
                best["eval"]["tip_ytd_cagr_pp"] or -999
            ):
                best = r
    champ = best["id"] if best else None

    payload = {
        "label": f"{SCREEN_ID}_{generated.replace(':', '').replace('-', '')}",
        "generated_at_utc": generated,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "status": "STAGE_A_SCREEN_DONE",
        "verdict": verdict,
        "live_wire": False,
        "sell_a75_keep": True,
        "cagr_sign": "chal_minus_base",
        "parent": "FIN_BOTH_QUALITY HARD150 OPEN observe tip PAUSE",
        "lock_id": LOCK_ID,
        "base_id": BASE_ID,
        "gates": {
            "held_cagr_lift_pp": CAGR_FLOOR_PP,
            "held_mdd_pp_floor": HELD_MDD_MIN_PP,
            "held_abs_mdd_max": HELD_ABS_MDD_MAX,
            "tip_mdd_pp_floor": TIP_MDD_MIN_PP,
            "tip_cagr_alert_pp": TIP_CAGR_ALERT_PP,
            "tip_cagr_pause_pp": TIP_CAGR_PAUSE_PP,
            "tip_beat_lock_pp": TIP_BEAT_LOCK_PP,
            "wr_hit_pp": WR_HIT_PP,
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
            "Soft-Frozen KEEP",
            "SELL_a75 KEEP",
            "OPEN observe HARD150 KEEP until tip repair HIT + human ballot",
            "no live wire from Stage A",
        ],
    }
    screen_md = "\n".join(
        [
            f"# {SCREEN_ID}",
            "",
            f"Date: 2026-09-28 · Generated `{generated}`",
            f"Status: **{verdict}** · Soft-Frozen **KEEP** · SELL_a75 **KEEP** · live wire **false**",
            "",
            "| ID | held CAGR↑ | held MDD↑ | tip YTD CAGR↑ | tip 1y CAGR↑ | HIT | SOFT |",
            "|---|---:|---:|---:|---:|:---:|:---:|",
        ]
        + [
            "| {id} | {cagr} | {mdd} | {ty} | {t1} | {hit} | {soft} |".format(
                id=r["id"],
                cagr=r["eval"]["held_cagr_lift_pp"],
                mdd=r["eval"]["held_mdd_pp"],
                ty=r["eval"]["tip_ytd_cagr_pp"],
                t1=r["eval"]["tip_1y_cagr_pp"],
                hit="Y" if r["eval"]["tip_repair_hit"] else "",
                soft="Y" if r["eval"]["tip_repair_soft"] else "",
            )
            for r in rows
        ]
        + ["", f"Verdict: **`{verdict}`**", f"Label: `{SCREEN_ID}_2026-09-28__{verdict}`", ""]
    )
    write_ops_and_repro_pointer(
        ops_json=OPS / f"{SCREEN_ID}.json",
        ops_md=OPS / f"{SCREEN_ID}.md",
        repro_dir=REPRO,
        payload=payload,
        md_text=screen_md,
        repro_json_name=f"{SCREEN_ID}.json",
        repro_md_name=f"{SCREEN_ID}.md",
    )

    decision_md = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: 2026-09-28 · Generated `{generated}`",
            f"Status: **{verdict}** · Soft-Frozen **KEEP** · SELL_a75 **KEEP** · live wire **false**",
            "",
            f"Charter: `{CHARTER_ID}.md`",
            f"Screen: `{SCREEN_ID}.md`",
            "Parent: HARD150 OPEN observe · tip YTD/1y CAGR PAUSE",
            "",
            "## Verdict",
            "",
            f"**`{verdict}`**",
            "",
            (f"Best tip-repair candidate: **`{champ}`**" if champ else "No tip-repair candidate."),
            "",
            "## Binding",
            "",
            "1. Soft-Frozen / tip / Exact T+1 / **SELL_a75** KEEP",
            "2. HARD150 paper observe stays OPEN until tip repair HIT + new human ballot",
            "3. Even HIT → ballot only; no live wire from Stage A",
            "4. Sell loss-defer remains REJECTED",
            "",
            f"Label: `{DECISION_ID}_2026-09-28__{verdict}__NO_LIVE`",
            "",
        ]
    )
    decision = {
        "label": f"{DECISION_ID}_2026-09-28__{verdict}__NO_LIVE",
        "status": verdict,
        "generated_at_utc": generated,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "screen": f"research/ops/{SCREEN_ID}.md",
        "live_wire": False,
        "sell_a75_keep": True,
        "best_candidate": champ,
        "cagr_sign": "chal_minus_base",
    }
    write_ops_and_repro_pointer(
        ops_json=OPS / f"{DECISION_ID}.json",
        ops_md=OPS / f"{DECISION_ID}.md",
        repro_dir=REPRO,
        payload=decision,
        md_text=decision_md,
        repro_json_name=f"{DECISION_ID}.json",
        repro_md_name=f"{DECISION_ID}.md",
    )

    charter_md = "\n".join(
        [
            "# FIN HARD150 tip/near-window repair — Stage A Charter",
            "",
            "Date: 2026-09-28",
            f"Status: **Stage A DONE — `{verdict}`** · Soft-Frozen live **KEEP** · Exact T+1 **KEEP** · `SELL_a75` **KEEP** · no live wire",
            "Parent: FIN both-quality `B_OR_K9_x_HARD150` OBSERVE OPEN · tip YTD/1y CAGR PAUSE",
            "",
            "Human intent:",
            "",
            "```",
            "OPEN Stage A: FIN HARD150 tip/near-window repair · clear tip CAGR PAUSE · keep held HIT · paper only",
            "```",
            "",
            f"Label: `{CHARTER_ID}_2026-09-28__DONE_{verdict}__NO_LIVE_WIRE`",
            "",
            "## Question",
            "",
            "Can a finite densify around HARD150 clear tip YTD/1y CAGR giveback "
            f"(≥ {TIP_CAGR_ALERT_PP}pp ALERT / ≥ {TIP_CAGR_PAUSE_PP}pp PAUSE) while held economic stays?",
            "",
            "## Gates",
            "",
            f"- held CAGR↑ ≥ +{CAGR_FLOOR_PP}pp · MDD↑ ≥ {HELD_MDD_MIN_PP}pp · tip MDD↑ ≥ 0",
            f"- TIP_REPAIR_HIT: tip YTD & 1y CAGR↑ ≥ {TIP_CAGR_ALERT_PP}pp",
            f"- TIP_REPAIR_SOFT: tip CAGR ≥ {TIP_CAGR_PAUSE_PP}pp OR beat LOCK by ≥ +{TIP_BEAT_LOCK_PP}pp both windows",
            "",
            "## Run",
            "",
            "```bash",
            "PYTHONPATH=scripts python3 scripts/fin_hard150_tip_repair_stagea.py",
            "```",
            "",
        ]
    )
    (OPS / f"{CHARTER_ID}.md").write_text(charter_md, encoding="utf-8")
    (OPS / f"{CHARTER_ID}.json").write_text(
        json.dumps(
            {
                "label": f"{CHARTER_ID}_2026-09-28__DONE_{verdict}__NO_LIVE_WIRE",
                "status": f"DONE_{verdict}",
                "verdict": verdict,
                "live_wire": False,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"verdict": verdict, "n_books": len(rows), "best": champ}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
