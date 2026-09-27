#!/usr/bin/env python3
"""Next-mechanism Stage A — SAT densify / E16 score / FinPriv reopen (paper).

Charter: research/ops/NEXT_MECH_STAGEA_CHARTER.md
Soft-Frozen clips KEEP · Exact T+1 KEEP · L1=0.05 KEEP · no live wire.
Base = live twin FUSE+COOL+L1=0.05+CONF_RET3_A10_H5 (00631L).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import cool_t50_inv_satellite_stagea as sat
import cool_t50_lev_rebound_stagea as reb
import cool_t50_lev_short_assist_stagea as short
import e16_clip_search_challenger as clip
import e16_soft_frozen_base as soft
import e50_early_stack_combined_nav as e50
import priv_finhc_cagr_mdd_gate_v7_stagea as v7
from e16_private_fin_holdings_rescreen import PRIV_R3R4, PUB_R1, TEL, build_extended_market
from e45_paper_harness import load_dividends, load_market
from live_config import LIVE_FUSE_SOFT_SELL_BOOST
from soft_assist_helpers import LIVE_KD
from ta_indicator_catalog import build_low_high_catalog
from within_sleeve_alloc import build_kd_season_tilt_scores, build_pre_exdiv_window_buy_ok

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "next-mech-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "NEXT_MECH_STAGEA_CHARTER"
SCREEN_ID = "NEXT_MECH_STAGEA_SCREEN"
DECISION_ID = "NEXT_MECH_STAGEA_DECISION_PACK"
BASE_ID = "BASE_LIVE_CONF"
OFF_CODE = "00631L"
OFF_PRICE = ROOT / "data" / "def_proxies" / "00631L_ohlcv.csv"
SELL_AMP = float(LIVE_FUSE_SOFT_SELL_BOOST)

# Charter gates (heldout vs BASE_LIVE_CONF)
CAGR_FLOOR_PP = 0.20
HELD_MDD_MIN_PP = -0.50
# Tip / sealed hygiene (align with short-assist / V8)
SEALED_MDD_MIN_PP = 0.0
TIP_MDD_TOL_PP = -0.50

LIVE_BULL_PRIOR = soft.REGIME_PRIORS["Bull"].copy()
E16_BULL_E20_PRIOR = np.array([0.70, 0.10, 0.20], dtype=float)  # FIN/TEL/0050
LIVE_SCORE_W = (0.35, 0.35, 0.20, 0.10)  # m20, m60, −vol, d60
E16_M20_050_W = (0.50, 0.25, 0.15, 0.10)


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _and_gate(a: pd.Series, b: pd.Series, cool: pd.Series | None = None) -> pd.Series:
    g = a.reindex(b.index).fillna(0.0).astype(float) * b.fillna(0.0).astype(float)
    if cool is not None:
        c = cool.reindex(g.index).fillna(1.0).astype(float)
        g = g * (c >= 1.0 - 1e-12).astype(float)
    return g.clip(0.0, 1.0)


def _rebuild_e16_targets(
    market: pd.DataFrame,
    *,
    bull_prior: np.ndarray | None = None,
    score_w: tuple[float, float, float, float] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.DataFrame]:
    """Causal Soft-Frozen router with optional Bull prior / score-weight override."""
    prices = (
        market.pivot(index="date", columns="code", values="adj_close")
        .sort_index()
        .ffill()
    )
    rets = prices.pct_change(fill_method=None).fillna(0.0)
    sleeve = pd.DataFrame(
        {
            "Financial": rets[list(soft.FIN)].mean(axis=1),
            "Telecom": rets[list(soft.TEL)].mean(axis=1),
            "0050": rets["0050"],
        }
    )
    taiex = prices["TAIEX"]
    tr = taiex.pct_change()
    ma = taiex.rolling(200).mean()
    vol = tr.rolling(20).std() * np.sqrt(252)
    dd = taiex / taiex.rolling(252, min_periods=120).max() - 1.0
    regime = pd.Series("Sideways", index=prices.index)
    regime[(taiex > ma) & (vol < 0.25)] = "Bull"
    regime[taiex < ma] = "Bear"
    regime[(vol > 0.35) | (dd < -0.15)] = "Crisis"

    nav = (1.0 + sleeve).cumprod()
    m20 = nav / nav.shift(20) - 1.0
    m60 = nav / nav.shift(60) - 1.0
    sv = sleeve.rolling(20).std() * np.sqrt(252)
    d60 = nav / nav.rolling(60, min_periods=20).max() - 1.0

    def _z(x: pd.DataFrame) -> pd.DataFrame:
        return x.sub(x.mean(axis=1), axis=0).div(
            x.std(axis=1).replace(0.0, np.nan), axis=0
        ).fillna(0.0)

    w = score_w if score_w is not None else LIVE_SCORE_W
    score = w[0] * _z(m20) + w[1] * _z(m60) - w[2] * _z(sv) + w[3] * _z(d60)

    priors = {k: v.copy() for k, v in soft.REGIME_PRIORS.items()}
    if bull_prior is not None:
        priors["Bull"] = np.asarray(bull_prior, dtype=float).copy()

    out = []
    cur = soft.apply_soft_frozen_clips(soft.START_WEIGHTS.copy())
    for i, _dt in enumerate(prices.index):
        pri = priors[str(regime.iloc[i])]
        cand = np.maximum(pri + 0.10 * np.clip(score.iloc[i].to_numpy(), -2.0, 2.0), 0.0)
        cand = soft.apply_soft_frozen_clips(cand)
        desired = soft.BLEND_OLD * cur + soft.BLEND_NEW * cand
        desired = soft.apply_soft_frozen_clips(desired)
        if float(np.abs(desired - cur).sum()) >= float(soft.REBALANCE_L1_MIN):
            cur = desired
        out.append(cur.copy())
    target = pd.DataFrame(out, index=prices.index, columns=["Financial", "Telecom", "0050"])
    return sleeve, target, regime, score


def _score_row(
    base_w,
    chal_w,
    tip,
    *,
    rid: str,
    track: str,
    n_fills: int,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    h, s = chal_w[sat.HELDOUT], chal_w[sat.SEALED]
    bh, bs = base_w[sat.HELDOUT], base_w[sat.SEALED]
    held_cagr_lift = sat.cagr_delta_pp(bh.get("cagr"), h.get("cagr"), missing_as_zero=True)
    sealed_cagr_lift = sat.cagr_delta_pp(bs.get("cagr"), s.get("cagr"), missing_as_zero=True)
    if held_cagr_lift is not None:
        held_cagr_lift = -float(held_cagr_lift)
    if sealed_cagr_lift is not None:
        sealed_cagr_lift = -float(sealed_cagr_lift)
    held_mdd_up = float(sat.mdd_delta_pp(bh.get("max_drawdown"), h.get("max_drawdown")))
    sealed_mdd_up = float(sat.mdd_delta_pp(bs.get("max_drawdown"), s.get("max_drawdown")))
    tip_clean = tip.get("ytd", {}).get("gate") == "PASS" and tip.get("trailing_1y", {}).get("gate") == "PASS"
    tip_mdd_ok = tip_clean and float(tip["ytd"].get("mdd_improve_pp") or -9) >= TIP_MDD_TOL_PP and float(
        tip["trailing_1y"].get("mdd_improve_pp") or -9
    ) >= TIP_MDD_TOL_PP
    cagr_hit = held_cagr_lift is not None and held_cagr_lift >= CAGR_FLOOR_PP
    mdd_hit = held_mdd_up >= HELD_MDD_MIN_PP
    gates = {
        "tip_clean": bool(tip_clean),
        "tip_mdd_ok": bool(tip_mdd_ok),
        "sealed_mdd": sealed_mdd_up >= SEALED_MDD_MIN_PP,
        "held_mdd": bool(mdd_hit),
        "held_cagr_floor": bool(cagr_hit),
    }
    # Charter MECH_HIT = CAGR + MDD; tip/sealed are hygiene for coexist
    mech_hit = bool(cagr_hit and mdd_hit and tip_mdd_ok and sealed_mdd_up >= SEALED_MDD_MIN_PP)
    cagr_soft = bool(mdd_hit and tip_mdd_ok and sealed_mdd_up >= SEALED_MDD_MIN_PP and not cagr_hit)
    score = (
        0.50 * ((held_cagr_lift or 0.0) + (sealed_cagr_lift or 0.0))
        + 0.50 * (held_mdd_up + sealed_mdd_up)
        - 0.25 * max(0.0, -(held_cagr_lift or 0.0))
    )
    return {
        "id": rid,
        "track": track,
        "n_fills": n_fills,
        "meta": meta or {},
        "windows": chal_w,
        "held_cagr_lift_pp": None if held_cagr_lift is None else round(held_cagr_lift, 4),
        "sealed_cagr_lift_pp": None if sealed_cagr_lift is None else round(sealed_cagr_lift, 4),
        "held_mdd_improve_pp": round(held_mdd_up, 4),
        "sealed_mdd_improve_pp": round(sealed_mdd_up, 4),
        "tip": tip,
        "gates": gates,
        "mech_hit": mech_hit,
        "cagr_soft": cagr_soft,
        "score": round(float(score), 4),
    }


def _apply_conf(
    tgt: pd.DataFrame,
    cool: pd.Series,
    *,
    alpha: float,
    hold_h: int,
    listed_from: pd.Timestamp,
    ret1: pd.Series,
    ret3: pd.Series,
    proxy: pd.Series,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    return short.build_schedule(
        tgt,
        cool,
        alpha=float(alpha),
        hold_h=int(hold_h),
        listed_from=listed_from,
        track="CONFIRM",
        confirm="RET3",
        ret1=ret1,
        ret3=ret3,
        proxy=proxy,
    )


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.8]
    assert float(soft.REBALANCE_L1_MIN) == 0.05
    assert OFF_PRICE.exists(), OFF_PRICE
    assert list(soft.FIN) == list(PUB_R1)

    # Point satellite DEF helpers at 00631L
    sat.DEF_CODE = OFF_CODE
    sat.DEF_PRICE = OFF_PRICE
    short.OFF_CODE = OFF_CODE
    short.OFF_PRICE = OFF_PRICE

    print("loading equity + 00631L ...", flush=True)
    market0 = load_market()
    dividends = load_dividends()
    off = sat.load_inv_bars()
    market_off, listed_from = sat.attach_inv(market0, off)
    print(f"{OFF_CODE} listed_from={listed_from.date()} sell_amp={SELL_AMP}", flush=True)

    _p, sleeve, _tgt0, regime0 = e50.e16_features(market0)
    cal = pd.DatetimeIndex(pd.to_datetime(market0["date"]).drop_duplicates().sort_values())
    lows, highs = build_low_high_catalog(market0, cal, list(soft.FIN))
    kd = build_kd_season_tilt_scores(
        market0,
        dividends,
        soft.FIN,
        k_thresh=float(LIVE_KD["k_thresh"]),
        season_start=LIVE_KD["season_start"],
        season_end=LIVE_KD["season_end"],
        pre_days=int(LIVE_KD["pre_days"]),
        active_score=float(LIVE_KD["active_score"]),
    )
    buy_ok = build_pre_exdiv_window_buy_ok(
        cal, dividends, soft.FIN, pre_days=int(LIVE_KD["pre_days"]), also_stock_ex=True
    )
    buy_live = sat._buy(kd, lows)
    sell_live = sat._sell(highs, SELL_AMP)
    score_live = sat._sleeve_score(market0, sleeve, float(sat.LIVE_SLEEVE_ALPHA))
    tgt_live = sat._target_live(score_live, regime0)

    print("offense + cool ...", flush=True)
    fuse_off, _, _ = sat._sim(
        market0,
        tgt_live,
        regime0,
        dividends,
        scores=buy_live,
        buy_ok=buy_ok,
        sell=sell_live,
        exposure=pd.Series(1.0, index=tgt_live.index),
    )
    cool = sat._cool_from_offense(market0, fuse_off)
    cool.to_frame("cool_exposure").to_csv(OUT / "exposure_cool.csv")
    n_exits = int(reb.cool_exits(cool).sum())
    defend_frac = float((cool < 1.0 - 1e-12).mean())
    print(f"cool_exits={n_exits} defend_frac={defend_frac:.4f}", flush=True)

    ret1, ret3 = short._0050_rets(market0, pd.DatetimeIndex(tgt_live.index))
    proxy = sat.stagea._risk_features(market0, sat.stagea._nav_series(fuse_off))["proxy_mdd63"]
    proxy = proxy.reindex(tgt_live.index).ffill()

    books: list[dict[str, Any]] = [
        {"id": BASE_ID, "track": "BASE", "alpha": 0.10, "hold_h": 5},
        {"id": "SAT_A15_H5", "track": "SAT", "alpha": 0.15, "hold_h": 5},
        {"id": "SAT_A20_H5", "track": "SAT", "alpha": 0.20, "hold_h": 5},
        {"id": "SAT_A10_H8", "track": "SAT", "alpha": 0.10, "hold_h": 8},
        {
            "id": "E16_BULL_E20",
            "track": "E16",
            "alpha": 0.10,
            "hold_h": 5,
            "bull_prior": E16_BULL_E20_PRIOR,
            "score_w": None,
        },
        {
            "id": "E16_M20_050",
            "track": "E16",
            "alpha": 0.10,
            "hold_h": 5,
            "bull_prior": None,
            "score_w": E16_M20_050_W,
        },
        {"id": "PRIV_V8BEST_F08", "track": "PRIV", "frac": 0.08},
        {"id": "PRIV_V8BEST_F10", "track": "PRIV", "frac": 0.10},
    ]
    assert len(books) == 8, len(books)

    rows: list[dict[str, Any]] = []
    base_nav: pd.DataFrame | None = None
    base_w: dict[str, Any] | None = None

    # --- SAT + E16 path (3-sleeve + CONF DEF) ---
    for book in books:
        if book["track"] == "PRIV":
            continue
        bid = book["id"]
        print(f"  [{bid}] ...", flush=True)
        if book["track"] == "E16":
            _sl, tgt, regime, _sc = _rebuild_e16_targets(
                market0,
                bull_prior=book.get("bull_prior"),
                score_w=book.get("score_w"),
            )
            # Rebuild cool on challenger offense for causal COOL under new router
            fuse_c, _, _ = sat._sim(
                market0,
                tgt,
                regime,
                dividends,
                scores=buy_live,
                buy_ok=buy_ok,
                sell=sell_live,
                exposure=pd.Series(1.0, index=tgt.index),
            )
            cool_c = sat._cool_from_offense(market0, fuse_c)
            proxy_c = sat.stagea._risk_features(market0, sat.stagea._nav_series(fuse_c))[
                "proxy_mdd63"
            ].reindex(tgt.index).ffill()
            ret1_c, ret3_c = short._0050_rets(market0, pd.DatetimeIndex(tgt.index))
            sched, meta = _apply_conf(
                tgt,
                cool_c,
                alpha=float(book["alpha"]),
                hold_h=int(book["hold_h"]),
                listed_from=listed_from,
                ret1=ret1_c,
                ret3=ret3_c,
                proxy=proxy_c,
            )
            nav, n_fills, _ = sat._sim(
                market_off,
                tgt,
                regime,
                dividends,
                scores=buy_live,
                buy_ok=buy_ok,
                sell=sell_live,
                schedule=sched,
            )
        else:
            # BASE + SAT densify share live tgt/cool; only CONF α/H changes
            sched, meta = _apply_conf(
                tgt_live,
                cool,
                alpha=float(book["alpha"]),
                hold_h=int(book["hold_h"]),
                listed_from=listed_from,
                ret1=ret1,
                ret3=ret3,
                proxy=proxy,
            )
            nav, n_fills, _ = sat._sim(
                market_off,
                tgt_live,
                regime0,
                dividends,
                scores=buy_live,
                buy_ok=buy_ok,
                sell=sell_live,
                schedule=sched,
            )

        nav.to_csv(OUT / f"nav_{bid}.csv", index=False)
        sched.to_csv(OUT / f"schedule_{bid}.csv")
        if bid == BASE_ID:
            base_nav = nav
            base_w = sat._pack(nav)
            tip = sat._tip(base_nav, base_nav)
            row = _score_row(
                base_w,
                base_w,
                tip,
                rid=bid,
                track="BASE",
                n_fills=n_fills,
                meta={
                    "alpha": book["alpha"],
                    "hold_h": book["hold_h"],
                    "n_entries": meta.get("n_entries"),
                    "pulse_frac": meta.get("pulse_frac"),
                    "mean_off": meta.get("mean_off"),
                },
            )
            row["mech_hit"] = False
            row["cagr_soft"] = False
            rows.append(row)
            continue

        assert base_nav is not None and base_w is not None
        tip = sat._tip(base_nav, nav)
        row = _score_row(
            base_w,
            sat._pack(nav),
            tip,
            rid=bid,
            track=book["track"],
            n_fills=n_fills,
            meta={
                "alpha": book.get("alpha"),
                "hold_h": book.get("hold_h"),
                "n_entries": meta.get("n_entries"),
                "pulse_frac": meta.get("pulse_frac"),
                "mean_off": meta.get("mean_off"),
                "bull_prior": None
                if book.get("bull_prior") is None
                else [float(x) for x in book["bull_prior"]],
                "score_w": book.get("score_w"),
            },
        )
        rows.append(row)

    # --- PRIV path (V8-best densify; FinPriv+COOL; no CONF stack — harness limit) ---
    print("loading extended market for PRIV ...", flush=True)
    market_x = build_extended_market()
    _px, sleeve_x, _tgt_x, regime_x = e50.e16_features(market_x)
    prices_x = (
        market_x.pivot(index="date", columns="code", values="adj_close")
        .sort_index()
        .ffill()
    )
    cal_x = pd.DatetimeIndex(pd.to_datetime(market_x["date"]).drop_duplicates().sort_values())
    all_fin = list(PUB_R1) + list(PRIV_R3R4)
    lows_x, highs_x = build_low_high_catalog(market_x, cal_x, all_fin)
    pub_kd = build_kd_season_tilt_scores(
        market_x,
        dividends,
        list(PUB_R1),
        k_thresh=float(LIVE_KD["k_thresh"]),
        season_start=LIVE_KD["season_start"],
        season_end=LIVE_KD["season_end"],
        pre_days=int(LIVE_KD["pre_days"]),
        active_score=float(LIVE_KD["active_score"]),
    )
    priv_kd = build_kd_season_tilt_scores(
        market_x,
        dividends,
        list(PRIV_R3R4),
        k_thresh=float(v7.PRIV_KD_MAY["k_thresh"]),
        season_start=v7.PRIV_KD_MAY["season_start"],
        season_end=v7.PRIV_KD_MAY["season_end"],
        pre_days=int(v7.PRIV_KD_MAY["pre_days"]),
        active_score=float(v7.PRIV_KD_MAY["active_score"]),
    )
    buy_ok_x = build_pre_exdiv_window_buy_ok(
        cal_x, dividends, all_fin, pre_days=int(LIVE_KD["pre_days"]), also_stock_ex=True
    )
    buy_pub = v7._buy(pub_kd, lows_x)
    sell_x = v7._sell(highs_x)
    score_x = v7._sleeve_score(market_x, sleeve_x, float(v7.LIVE_SLEEVE_ALPHA))
    tgt_x = v7._target_live(score_x, regime_x)

    old_fin, old_all = list(e50.FIN), list(e50.ALL)
    e50.FIN = list(PUB_R1)
    e50.ALL = list(PUB_R1) + list(TEL) + ["0050"]
    try:
        fuse_x, _, _ = v7._sim_three(
            market_x,
            tgt_x,
            regime_x,
            dividends,
            scores=buy_pub,
            buy_ok=buy_ok_x,
            sell=sell_x,
            exposure=pd.Series(1.0, index=tgt_x.index),
        )
        cool_x = v7._cool_from_offense(market_x, fuse_x)
        components = v7.build_gates(prices_x, regime_x)
        for book in books:
            if book["track"] != "PRIV":
                continue
            bid = book["id"]
            frac = float(book["frac"])
            print(f"  [{bid}] frac={frac} BSIDE_MA120_COOL1 ...", flush=True)
            gate = _and_gate(
                components["REG_BULL_SIDE"],
                components["MA120_0050"],
                cool_x,
            )
            four = v7.to_four_sleeve(tgt_x, gate, frac)
            sched = v7.scale_schedule(four, cool_x)
            sched.to_csv(OUT / f"schedule_{bid}.csv")
            nav, n_fills, _ = v7._sim_four(
                market_x,
                sched,
                regime_x,
                dividends,
                pub_scores=buy_pub,
                priv_scores=priv_kd,
                buy_ok=buy_ok_x,
                sell=sell_x,
                priv_policy="PRIV_KD_MAY",
            )
            nav.to_csv(OUT / f"nav_{bid}.csv", index=False)
            assert base_nav is not None and base_w is not None
            tip = sat._tip(base_nav, nav)
            row = _score_row(
                base_w,
                sat._pack(nav),
                tip,
                rid=bid,
                track="PRIV",
                n_fills=n_fills,
                meta={
                    "tag": "BSIDE_MA120_COOL1",
                    "frac": frac,
                    "pol": "PRIV_KD_MAY",
                    "mean_priv": float(four["FinPriv"].mean()),
                    "gate_on_frac": float((gate.fillna(0) > 0).mean()),
                    "note": "PRIV stack = FinPriv+COOL only (no CONF DEF; harness limit)",
                },
            )
            rows.append(row)
    finally:
        e50.FIN = old_fin
        e50.ALL = old_all

    chal = [r for r in rows if r["track"] != "BASE"]
    hits = [r for r in chal if r["mech_hit"]]
    softs = [r for r in chal if r["cagr_soft"]]
    any_cagr = any(r["gates"]["held_cagr_floor"] for r in chal)

    if hits:
        verdict = "MECH_HIT"
    elif softs and not any_cagr:
        verdict = "CAGR_SOFT"
    elif not any_cagr:
        verdict = "CLOSE_OBSERVE_RECOMMENDED"
    else:
        # CAGR cleared somewhere but MDD/tip blocked
        verdict = "NO_LIFT"

    ranked = sorted(chal, key=lambda r: -float(r["score"]))
    by_track: dict[str, list[str]] = {}
    for r in ranked:
        by_track.setdefault(r["track"], []).append(r["id"])

    payload = {
        "generated_at_utc": _utc(),
        "label": SCREEN_ID,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "status": verdict,
        "live_wire": False,
        "soft_frozen_keep": True,
        "exact_t1_keep": True,
        "l1_min": float(soft.REBALANCE_L1_MIN),
        "sell_amp": SELL_AMP,
        "off_code": OFF_CODE,
        "n_cool_exits": n_exits,
        "cool_defend_frac": round(defend_frac, 6),
        "listed_from": str(listed_from.date()),
        "baseline": BASE_ID,
        "baseline_windows": base_w,
        "gates": {
            "held_cagr_lift_pp_min": CAGR_FLOOR_PP,
            "held_mdd_improve_pp_min": HELD_MDD_MIN_PP,
        },
        "n_challengers": len(chal),
        "n_mech_hit": len(hits),
        "n_cagr_soft": len(softs),
        "mech_hit_ids": [r["id"] for r in sorted(hits, key=lambda r: -r["score"])],
        "cagr_soft_ids": [r["id"] for r in softs],
        "best": (
            sorted(hits, key=lambda r: -r["score"])[0]["id"]
            if hits
            else (ranked[0]["id"] if ranked else None)
        ),
        "ranked": ranked,
        "by_track": by_track,
        "live_bull_prior": [float(x) for x in LIVE_BULL_PRIOR],
        "live_score_w": list(LIVE_SCORE_W),
    }
    (REP / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2) + "\n")
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2) + "\n")

    lines = [
        "# Next-mechanism Stage A — Screen",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Status: **`{verdict}`** · Soft-Frozen **KEEP** · Exact T+1 **KEEP** · L1=**0.05** · live wire **false**",
        f"Base: `{BASE_ID}` = FUSE+COOL+CONF_RET3 α=0.10 H=5 · OFF=`{OFF_CODE}` · sell_amp=**{SELL_AMP:g}**",
        f"cool_exits=**{n_exits}** · defend_frac=**{defend_frac:.2%}**",
        "",
        f"MECH_HIT: **{len(hits)}** · CAGR_SOFT: **{len(softs)}** / {len(chal)} challengers",
        "",
        "## Ranked",
        "",
        "| book | track | CAGR↑h | CAGR↑s | MDD↑h | MDD↑s | tip | hit | soft |",
        "|---|---|---:|---:|---:|---:|---|---|---|",
    ]
    for r in ranked:
        tip_ok = "Y" if r["gates"]["tip_mdd_ok"] else "N"
        lines.append(
            f"| `{r['id']}` | {r['track']} | "
            f"{r['held_cagr_lift_pp']:+.2f} | {r['sealed_cagr_lift_pp']:+.2f} | "
            f"{r['held_mdd_improve_pp']:+.2f} | {r['sealed_mdd_improve_pp']:+.2f} | "
            f"{tip_ok} | {'Y' if r['mech_hit'] else 'N'} | {'Y' if r['cagr_soft'] else 'N'} |"
        )
    base_row = next(r for r in rows if r["id"] == BASE_ID)
    bh = base_w[sat.HELDOUT] if base_w else {}
    lines += [
        "",
        "## Base windows (heldout)",
        "",
        f"`{BASE_ID}` CAGR={bh.get('cagr')} · MDD={bh.get('max_drawdown')} · "
        f"pulse_frac={base_row['meta'].get('pulse_frac')}",
        "",
        "## Binding",
        "",
        "1. Soft-Frozen clips · Exact T+1 · L1=0.05 **KEEP**.",
        "2. Even MECH_HIT → paper only; **at most one** track for ACCEPT discussion.",
        "3. PRIV books omit CONF DEF (simulate_core FinPriv+DEF not co-supported).",
        "",
        "Repro: `PYTHONPATH=scripts python3 scripts/next_mech_stagea.py`",
        "",
        f"Label: `{SCREEN_ID}_{payload['generated_at_utc'][:10]}__{verdict}`",
        "",
    ]
    md = "\n".join(lines)
    (REP / f"{SCREEN_ID}.md").write_text(md)
    (OPS / f"{SCREEN_ID}.md").write_text(md)

    decision = {
        "label": DECISION_ID,
        "generated_at_utc": _utc(),
        "status": verdict,
        "live_wire": False,
        "soft_frozen_keep": True,
        "exact_t1_keep": True,
        "n_mech_hit": len(hits),
        "n_cagr_soft": len(softs),
        "mech_hit_ids": payload["mech_hit_ids"],
        "cagr_soft_ids": payload["cagr_soft_ids"],
        "best": payload["best"],
        "charter": f"research/ops/{CHARTER_ID}.md",
        "stage_a": f"research/ops/{SCREEN_ID}.md",
        "tracks": ["SAT", "E16", "PRIV", "CLOSE"],
        "baseline": BASE_ID,
    }
    dlines = [
        "# Next-mechanism Stage A — Decision Pack",
        "",
        f"Date: 2026-09-27 · Generated `{decision['generated_at_utc']}`",
        f"Status: **{verdict}** · Soft-Frozen **KEEP** · Exact T+1 **KEEP** · live wire **false**",
        "",
        "Tracks: SAT (CONF densify) · E16 (Bull prior / score) · PRIV (V8-best densify) · CLOSE (meta)",
        "",
        f"MECH_HIT: **{len(hits)}** · CAGR_SOFT: **{len(softs)}**.",
        "",
    ]
    if hits:
        b = sorted(hits, key=lambda r: -r["score"])[0]
        dlines += [
            f"Best: `{b['id']}` ({b['track']}) · held CAGR↑ **{b['held_cagr_lift_pp']:+.2f}** · "
            f"held MDD↑ **{b['held_mdd_improve_pp']:+.2f}**",
            "",
            "Next: paper observe / ACCEPT discussion for **one** track only. No live wire from this pack.",
            "",
        ]
    elif softs:
        b = sorted(softs, key=lambda r: -r["score"])[0]
        dlines += [
            f"CAGR_SOFT best: `{b['id']}` ({b['track']}) · held CAGR↑ {b['held_cagr_lift_pp']:+.2f} · "
            f"held MDD↑ {b['held_mdd_improve_pp']:+.2f}.",
            "",
            "Reading: MDD near-flat but CAGR gate (+0.20pp) not cleared.",
            "",
            "Binding: Soft-Frozen KEEP · no live without new ACCEPT.",
            "",
        ]
    elif verdict == "CLOSE_OBSERVE_RECOMMENDED":
        dlines += [
            "No challenger cleared held CAGR ≥ +0.20pp vs `BASE_LIVE_CONF`.",
            "",
            "Reading: satellite densify / E16 rewrite / V8-best FinPriv densify do not open a CAGR path "
            "under predeclared gates. Recommend **CLOSE observe** on this menu; reopen only with a "
            "**new** mechanism (not densify these cells).",
            "",
            "Binding: Soft-Frozen KEEP · Exact T+1 KEEP · L1=0.05 KEEP · no live wire.",
            "",
        ]
    else:
        dlines += [
            "CAGR cleared somewhere but MDD/tip hygiene blocked MECH_HIT.",
            "",
            "Binding: Soft-Frozen KEEP · no live wire.",
            "",
        ]
    dlines += [
        "## Refs",
        "",
        f"- Charter: `{CHARTER_ID}.md`",
        f"- Screen: `{SCREEN_ID}.md`",
        "- Parent: earn-beta `CLOSE_OBSERVE_RECOMMENDED`",
        "",
        f"Label: `{DECISION_ID}_2026-09-27__{verdict}`",
        "",
    ]
    (OPS / f"{DECISION_ID}.json").write_text(json.dumps(decision, indent=2) + "\n")
    (OPS / f"{DECISION_ID}.md").write_text("\n".join(dlines))
    (REP / f"{DECISION_ID}.json").write_text(json.dumps(decision, indent=2) + "\n")
    (REP / f"{DECISION_ID}.md").write_text("\n".join(dlines))

    # zh-TW brief
    zh = [
        "# 下一層機制 Stage A — 決策包",
        "",
        f"狀態：**{verdict}** · Soft-Frozen／Exact T+1／L1=0.05 **KEEP** · 不進 live",
        "",
        f"HIT：**{len(hits)}** · SOFT：**{len(softs)}** · best：`{payload['best']}`",
        "",
        "複現：`PYTHONPATH=scripts python3 scripts/next_mech_stagea.py`",
        "",
    ]
    (OPS / f"{DECISION_ID}.zh-TW.md").write_text("\n".join(zh))

    print(
        json.dumps(
            {
                "verdict": verdict,
                "n_mech_hit": len(hits),
                "n_cagr_soft": len(softs),
                "mech_hit_ids": payload["mech_hit_ids"],
                "top3": [r["id"] for r in ranked[:3]],
                "top3_cagr": [r["held_cagr_lift_pp"] for r in ranked[:3]],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
