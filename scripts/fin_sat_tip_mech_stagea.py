#!/usr/bin/env python3
"""FIN×SAT tip new-mech Stage A — COOL-conditional HARD + SAT-relax (paper).

Charter: research/ops/FIN_SAT_TIP_MECH_STAGEA_CHARTER.md
Parents: 0k9c TIP_MDD_ONLY · ABC-A LOCK_KEEP_NO_TIP_LIFT (season exhausted).
Soft-Frozen / SELL_a75 / live CONF α=0.10 KEEP · COMPOSITE observe KEEP · no live wire.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

import cool_t50_inv_satellite_stagea as sat
import cool_t50_lev_short_assist_stagea as short
import e16_clip_search_challenger as clip
import e16_soft_frozen_base as soft
import e22_dividend_accounting as e22div
import e45_defend_handoff_stagea_screen as stagea
from cool_c8_proxy_observe_helpers import build_cool_c8_exposure
from e45_paper_harness import WINDOWS_STANDARD, window_stats
from e50_early_stack_combined_nav import FIN, e16_features, simulate_core
from fin_buy_quality_helpers import (
    and_buy_ok,
    below_ma_ok,
    catalog_gate,
    close_panel,
    forward_win_stats,
    not_gate,
    or_buy_ok,
    raw_close_panel,
)
from fin_sell_quality_helpers import cagr_lift_pp, forward_sell_win_stats
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
REPRO = ROOT / "repro" / "fin-sat-tip-mech-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_SAT_TIP_MECH_STAGEA_CHARTER"
SCREEN_ID = "FIN_SAT_TIP_MECH_STAGEA_SCREEN"
DECISION_ID = "FIN_SAT_TIP_MECH_STAGEA_DECISION_PACK"
BASE_ID = "CTRL_LIVE_A10"
OFF_CODE = "00631L"
E22_VERSION = e22div.DEFAULT_BOOKS_VERSION
SELL_AMP = float(LIVE_FUSE_SOFT_SELL_BOOST)
HOLD_H = 5
CONFIRM = "RET3"

CAGR_FLOOR_PP = 0.10
HELD_MDD_MIN_PP = -0.25
HELD_ABS_MDD_MAX = 0.15
TIP_MDD_MIN_PP = 0.0
TIP_CAGR_MIN_PP = 0.0
SAT_CAGR_FLOOR_PP = 0.05
SAT_HELD_MDD_MIN_PP = -0.40
WIN_H = 21

GRID: list[dict[str, Any]] = [
    {"id": "CTRL_LIVE_A10", "fam": "ctrl", "buy": None, "sell": None, "alpha": 0.10},
    {"id": "REF_COMP_H150_A20", "fam": "ref", "buy": "OR_K9", "sell": "HARD150", "alpha": 0.20},
    {"id": "MECH_H150_COOLON_A10", "fam": "mech", "buy": "OR_K9", "sell": "HARD150_COOLON", "alpha": 0.10},
    {"id": "MECH_H150_COOLOFF_A10", "fam": "mech", "buy": "OR_K9", "sell": "HARD150_COOLOFF", "alpha": 0.10},
    {"id": "MECH_H150_COOLON_A15", "fam": "mech", "buy": "OR_K9", "sell": "HARD150_COOLON", "alpha": 0.15},
    {"id": "MECH_H150_COOLOFF_A15", "fam": "mech", "buy": "OR_K9", "sell": "HARD150_COOLOFF", "alpha": 0.15},
    {"id": "MECH_H150_COOLON_A20", "fam": "mech", "buy": "OR_K9", "sell": "HARD150_COOLON", "alpha": 0.20},
    {"id": "SAT_A15_RELAX", "fam": "sat", "buy": None, "sell": None, "alpha": 0.15},
    {"id": "SAT_A20_RELAX", "fam": "sat", "buy": None, "sell": None, "alpha": 0.20},
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


def _buy_scores(kd, lows) -> pd.DataFrame:
    out = soft_boost_scores(kd, lows[BUY_LOW_ID], 1.0)
    return soft_boost_scores(out, lows["K9_LT30"], 1.0)


def _sell_base(highs) -> pd.DataFrame:
    return soft_sell_panel(highs[SELL_HIGH_ID], boost=SELL_AMP)


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


def _overlays(
    buy_name: str | None,
    sell_name: str | None,
    *,
    base_buy_ok: pd.DataFrame,
    lows: dict,
    raw: pd.DataFrame,
    cool: pd.Series | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame | None]:
    buy_ok = base_buy_ok
    if buy_name == "OR_K9":
        extra = or_buy_ok(catalog_gate(lows["BELOW_MA120"]), catalog_gate(lows["K9_LT30"]))
        buy_ok = and_buy_ok(base_buy_ok, extra)
    elif buy_name is not None:
        raise ValueError(buy_name)
    sell_ok = None
    if sell_name is None:
        return buy_ok, None
    hard = not_gate(below_ma_ok(raw, 150))
    if sell_name == "HARD150":
        sell_ok = hard
    elif sell_name == "HARD120":
        sell_ok = not_gate(below_ma_ok(raw, 120))
    elif sell_name in ("HARD150_COOLON", "HARD150_COOLOFF"):
        if cool is None:
            raise ValueError("cool required for conditional HARD")
        c = cool.reindex(hard.index).fillna(1.0).astype(float)
        if sell_name == "HARD150_COOLON":
            active = c < 1.0 - 1e-12
        else:
            active = c >= 1.0 - 1e-12
        mask = pd.DataFrame({col: active.to_numpy() for col in hard.columns}, index=hard.index)
        # When condition active: HARD gate; else unrestricted (True).
        sell_ok = hard.where(mask, True)
    else:
        raise ValueError(sell_name)
    return buy_ok, sell_ok


def _sim(
    market,
    target,
    regime,
    dividends,
    *,
    scores,
    buy_ok,
    sell,
    schedule,
    sell_ok=None,
):
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
        "e22_version": E22_VERSION,
        "sleeve_weight_schedule": schedule,
        "def_code": OFF_CODE,
    }
    if sell_ok is not None:
        kw["fin_sell_ok"] = sell_ok
    nav, fills, meta = simulate_core(market, target, regime, dividends, **kw)
    if not bool(meta.get("exact_t1_ok")):
        raise RuntimeError("exact_t1_ok failed")
    return nav, fills, meta


def _eval_row(
    base_w,
    chal_w,
    tip,
    *,
    book_id,
    fam,
    buy_wr,
    sell_wr,
    base_buy_wr,
    base_sell_wr,
):
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
    tip_cagr_ok = (
        tip_ytd_cagr is not None
        and tip_1y_cagr is not None
        and float(tip_ytd_cagr) >= TIP_CAGR_MIN_PP
        and float(tip_1y_cagr) >= TIP_CAGR_MIN_PP
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
    economic = bool(cagr_ok and mdd_ok and band_ok and tip_mdd_ok)
    tip_clean = bool(tip_mdd_ok and tip_cagr_ok)
    sat_cagr_ok = cagr_pp is not None and float(cagr_pp) >= SAT_CAGR_FLOOR_PP
    sat_mdd_ok = mdd_pp is not None and float(mdd_pp) >= SAT_HELD_MDD_MIN_PP
    sat_econ = bool(sat_cagr_ok and sat_mdd_ok and band_ok and tip_clean)
    hit = False
    if fam == "mech" and book_id != BASE_ID:
        hit = bool(economic and tip_cagr_ok)
    elif fam == "sat" and book_id != BASE_ID:
        hit = bool(sat_econ)
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
        "family": fam,
        "gates": {
            "cagr": bool(cagr_ok),
            "mdd_near_flat": bool(mdd_ok),
            "mdd_band": bool(band_ok),
            "tip_mdd": bool(tip_mdd_ok),
            "tip_cagr": bool(tip_cagr_ok),
            "tip_clean": tip_clean,
            "economic": economic,
            "sat_cagr": bool(sat_cagr_ok),
            "sat_mdd": bool(sat_mdd_ok),
            "sat_econ": sat_econ,
        },
        "hit": hit,
        "cagr_sign": "chal_minus_base",
    }


def _verdict(rows: list[dict[str, Any]]) -> str:
    mech_hits = [r for r in rows if r["fam"] == "mech" and r["eval"]["hit"]]
    sat_hits = [r for r in rows if r["fam"] == "sat" and r["eval"]["hit"]]
    if mech_hits:
        return "MECH_HIT"
    if sat_hits:
        return "SAT_RELAX_HIT"
    tip_mdd_only = [
        r
        for r in rows
        if r["id"] != BASE_ID
        and r["eval"]["gates"]["tip_mdd"]
        and not r["eval"]["gates"]["tip_cagr"]
        and (r["eval"]["gates"]["economic"] or r["eval"]["gates"]["sat_econ"])
    ]
    if tip_mdd_only:
        return "TIP_MDD_ONLY"
    chal = [r for r in rows if r["id"] != BASE_ID]
    if any(r["eval"]["gates"].get("cagr") and not r["eval"]["gates"]["tip_mdd"] for r in chal):
        return "TIP_BLOCK"
    if any(
        r["eval"]["gates"]["tip_clean"]
        and (r["eval"]["held_cagr_lift_pp"] or 0) > 0
        and not r["eval"]["hit"]
        for r in chal
    ):
        return "HELD_SOFT"
    return "NO_EDGE"


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.8]
    assert abs(SELL_AMP - 0.75) < 1e-12

    sat.DEF_CODE = OFF_CODE
    sat.DEF_PRICE = ROOT / "data/def_proxies/00631L_ohlcv.csv"
    assert sat.DEF_PRICE.exists(), sat.DEF_PRICE

    print("loading ...", flush=True)
    market0 = sat.load_market()
    dividends = sat.load_dividends()
    off = sat.load_inv_bars()
    market, listed_from = sat.attach_inv(market0, off)

    _p, sleeve, _t, regime = e16_features(market0)
    cal = pd.DatetimeIndex(pd.to_datetime(market0["date"]).drop_duplicates().sort_values())
    lows, highs = build_low_high_catalog(market0, cal, list(FIN))
    raw = raw_close_panel(market0, cal, list(FIN))
    closes = close_panel(market0, cal, list(FIN))
    kd = build_kd_season_tilt_scores(
        market0,
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
    sleeve_sc = _sleeve_score(market0, sleeve, LIVE_SLEEVE_ALPHA)
    tgt_live = _target_live(sleeve_sc, regime)

    print("offense NAV for cool ...", flush=True)
    off_nav, _, _ = simulate_core(
        market0,
        tgt_live,
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
    cool = _cool_from_offense(market0, off_nav)
    nav_s = stagea._nav_series(off_nav)
    feat = stagea._risk_features(market0, nav_s)
    proxy = feat["proxy_mdd63"].reindex(tgt_live.index).fillna(0.0)
    ret1, ret3 = short._0050_rets(market0, tgt_live.index)
    off_px = short._off_close(off, tgt_live.index)

    rows: list[dict[str, Any]] = []
    base_nav = None
    base_w = None
    base_buy_wr = None
    base_sell_wr = None
    fin_set = set(FIN)

    for spec in GRID:
        bid = str(spec["id"])
        fam = str(spec["fam"])
        alpha = float(spec["alpha"])
        buy_ok, sell_ok = _overlays(
            spec.get("buy"),
            spec.get("sell"),
            base_buy_ok=base_buy_ok,
            lows=lows,
            raw=raw,
            cool=cool,
        )
        print(f"{bid} α={alpha} ...", flush=True)
        sched, meta_s = short.build_schedule(
            tgt_live,
            cool,
            alpha=alpha,
            hold_h=HOLD_H,
            listed_from=listed_from,
            track="CONFIRM",
            confirm=CONFIRM,
            ret1=ret1,
            ret3=ret3,
            proxy=proxy,
            off_px=off_px,
        )
        nav, fills, meta = _sim(
            market,
            tgt_live,
            regime,
            dividends,
            scores=scores,
            buy_ok=buy_ok,
            sell=sell0,
            schedule=sched,
            sell_ok=sell_ok,
        )
        nav.to_csv(OUT / f"nav_{bid}.csv", index=False)
        sched.to_csv(OUT / f"sched_{bid}.csv")
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
            fam=fam,
            buy_wr=buy_wr,
            sell_wr=sell_wr,
            base_buy_wr=base_buy_wr,
            base_sell_wr=base_sell_wr,
        )
        rows.append(
            {
                "id": bid,
                "fam": fam,
                "alpha": alpha,
                "windows": w,
                "tip": tip,
                "eval": ev,
                "buy_wr": buy_wr,
                "sell_wr": sell_wr,
                "spec": spec,
                "sched_meta": meta_s,
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
        "status": "STAGE_A_SCREEN_DONE",
        "verdict": verdict,
        "live_wire": False,
        "soft_frozen_keep": True,
        "sell_a75_keep": True,
        "live_conf_a10_keep": True,
        "cagr_sign": "chal_minus_base",
        "base_id": BASE_ID,
        "gates": {
            "held_cagr_lift_pp": CAGR_FLOOR_PP,
            "held_mdd_pp_floor": HELD_MDD_MIN_PP,
            "held_abs_mdd_max": HELD_ABS_MDD_MAX,
            "tip_mdd_pp_floor": TIP_MDD_MIN_PP,
            "tip_cagr_pp_floor": TIP_CAGR_MIN_PP,
            "sat_held_cagr_lift_pp": SAT_CAGR_FLOOR_PP,
            "sat_held_mdd_pp_floor": SAT_HELD_MDD_MIN_PP,
            "win_horizon": WIN_H,
        },
        "books": [
            {
                "id": r["id"],
                "fam": r["fam"],
                "alpha": r["alpha"],
                "windows": r["windows"],
                "tip": r["tip"],
                "eval": r["eval"],
                "buy_wr": r["buy_wr"],
                "sell_wr": r["sell_wr"],
                "spec": r["spec"],
                "sched_meta": r["sched_meta"],
                "n_fills": r["n_fills"],
                "exact_t1_ok": r["exact_t1_ok"],
            }
            for r in rows
        ],
    }
    screen_md = "\n".join(
        [
            f"# {SCREEN_ID}",
            "",
            f"Date: 2026-09-28 · Generated `{generated}`",
            f"Status: **{verdict}** · Soft-Frozen **KEEP** · SELL_a75 **KEEP** · live CONF α=0.10 **KEEP** · COMPOSITE observe **KEEP** · live wire **false**",
            "",
            "Tip new-mech: COOL-conditional HARD150 · OR SAT_RELAX held gates · tip CAGR binding.",
            "",
            "## Books",
            "",
            "| ID | fam | α | heldCAGR↑ | heldMDD↑ | tipMDD↑ | tipCAGR↑ | tipClean | HIT |",
            "|---|---|---:|---:|---:|---:|---:|---|---|",
        ]
        + [
            "| {id} | {fam} | {a} | {cagr} | {mdd} | {tm} | {tc} | {clean} | {hit} |".format(
                id=r["id"],
                fam=r["fam"],
                a=r["alpha"],
                cagr=r["eval"]["held_cagr_lift_pp"],
                mdd=r["eval"]["held_mdd_pp"],
                tm=r["eval"]["tip_ytd_mdd_pp"],
                tc=r["eval"]["tip_ytd_cagr_pp"],
                clean=r["eval"]["gates"]["tip_clean"],
                hit=r["eval"]["hit"],
            )
            for r in rows
        ]
        + ["", f"Verdict: **`{verdict}`**", "", f"Label: `{SCREEN_ID}_2026-09-28__{verdict}`", ""]
    )

    hits = [r for r in rows if r["eval"]["hit"]]
    hits.sort(
        key=lambda r: (
            1 if r["fam"] == "mech" else 0,
            float(r["eval"]["tip_ytd_cagr_pp"] or -99),
            float(r["eval"]["held_cagr_lift_pp"] or -9),
        ),
        reverse=True,
    )
    best = hits[0] if hits else None
    mech_econ = [r for r in rows if r["fam"] == "mech" and r["eval"]["gates"]["economic"]]
    sat_near = [r for r in rows if r["fam"] == "sat" and r["eval"]["gates"]["tip_clean"]]
    sat_near.sort(key=lambda r: float(r["eval"]["held_cagr_lift_pp"] or -9), reverse=True)

    dlines = [
        f"# {DECISION_ID}",
        "",
        f"Date: 2026-09-28 · Generated `{generated}`",
        f"Status: **{verdict}** · Soft-Frozen **KEEP** · SELL_a75 **KEEP** · live CONF α=0.10 **KEEP** · COMPOSITE observe **KEEP** · live wire **false**",
        "",
        f"Charter: `{CHARTER_ID}.md`",
        f"Screen: `{SCREEN_ID}.md`",
        "Parents: 0k9c TIP_MDD_ONLY · ABC-A LOCK_KEEP_NO_TIP_LIFT",
        "",
        "## Verdict",
        "",
        f"**`{verdict}`**",
        "",
        "Tracks: COOL-conditional HARD150 (strict) · SAT_RELAX (held CAGR≥+0.05 · MDD≥−0.40).",
        "",
    ]
    if best:
        dlines += [
            (
                f"Champion: `{best['id']}` · fam={best['fam']} · tipCAGR↑ YTD {best['eval']['tip_ytd_cagr_pp']} · "
                f"held CAGR↑ {best['eval']['held_cagr_lift_pp']}pp · tipMDD↑ {best['eval']['tip_ytd_mdd_pp']}"
            ),
            "",
            "Even HIT → observe ballot **DRAFT only** · COMPOSITE observe KEEP · no live.",
            "",
        ]
    elif sat_near:
        top = sat_near[0]
        dlines += [
            (
                f"Best SAT tip-clean: `{top['id']}` · tipCAGR↑ YTD {top['eval']['tip_ytd_cagr_pp']} · "
                f"held CAGR↑ {top['eval']['held_cagr_lift_pp']} · held MDD↑ {top['eval']['held_mdd_pp']} · "
                f"sat_econ={top['eval']['gates']['sat_econ']}"
            ),
            "",
        ]
    elif mech_econ:
        top = mech_econ[0]
        dlines += [
            (
                f"Best mech economic (tip CAGR fail): `{top['id']}` · held CAGR↑ {top['eval']['held_cagr_lift_pp']} · "
                f"tipCAGR↑ YTD {top['eval']['tip_ytd_cagr_pp']}"
            ),
            "",
        ]
    else:
        dlines += ["No mech/sat book cleared tip-clean economic gates.", ""]

    dlines += [
        "## Binding",
        "",
        "1. Soft-Frozen / Exact T+1 / COOL / **SELL_a75** / live CONF α=0.10 KEEP",
        "2. COMPOSITE observe **KEEP OPEN**",
        "3. Do not reopen HARD×α densify or season tip-repair grids",
        "4. Even HIT → paper observe ballot DRAFT only · no live",
        "",
        f"Label: `{DECISION_ID}_2026-09-28__{verdict}__NO_LIVE`",
        "",
    ]
    decision = {
        "label": f"{DECISION_ID}_2026-09-28__{verdict}__NO_LIVE",
        "status": verdict,
        "live_wire": False,
        "soft_frozen_keep": True,
        "sell_a75_keep": True,
        "live_conf_a10_keep": True,
        "composite_observe_keep": True,
        "cagr_sign": "chal_minus_base",
        "charter": f"research/ops/{CHARTER_ID}.md",
        "screen": f"research/ops/{SCREEN_ID}.md",
        "best_hit": None if best is None else best["id"],
        "best_sat_tip_clean": None if not sat_near else sat_near[0]["id"],
        "best_mech_economic": None if not mech_econ else mech_econ[0]["id"],
        "generated_at_utc": generated,
    }

    write_ops_and_repro_pointer(OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", screen_md, kind="screen")
    write_ops_and_repro_pointer(
        OPS / f"{SCREEN_ID}.json",
        REP / f"{SCREEN_ID}.json",
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        kind="screen",
    )
    write_ops_and_repro_pointer(OPS / f"{DECISION_ID}.md", REP / f"{DECISION_ID}.md", "\n".join(dlines))
    write_ops_and_repro_pointer(
        OPS / f"{DECISION_ID}.json",
        REP / f"{DECISION_ID}.json",
        json.dumps(decision, indent=2, ensure_ascii=False) + "\n",
    )

    for path, open_s, done_s in (
        (OPS / f"{CHARTER_ID}.md", "Status: **Stage A OPEN**", f"Status: **Stage A DONE — `{verdict}`**"),
        (OPS / f"{CHARTER_ID}.zh-TW.md", "狀態：**Stage A OPEN**", f"狀態：**Stage A DONE — `{verdict}`**"),
    ):
        if path.exists():
            body = path.read_text(encoding="utf-8")
            body = body.replace(open_s, done_s, 1)
            body = body.replace(
                f"{CHARTER_ID}_2026-09-28__OPEN__NO_LIVE_WIRE",
                f"{CHARTER_ID}_2026-09-28__DONE_{verdict}__NO_LIVE_WIRE",
            )
            path.write_text(body, encoding="utf-8")
    cj_path = OPS / f"{CHARTER_ID}.json"
    if cj_path.exists():
        cj = json.loads(cj_path.read_text(encoding="utf-8"))
        cj["status"] = "STAGE_A_DONE"
        cj["verdict"] = verdict
        cj["label"] = f"{CHARTER_ID}_2026-09-28__DONE_{verdict}__NO_LIVE_WIRE"
        cj["screen"] = f"research/ops/{SCREEN_ID}.md"
        cj["decision"] = f"research/ops/{DECISION_ID}.md"
        cj_path.write_text(json.dumps(cj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps({"verdict": verdict, "n_books": len(rows)}, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
