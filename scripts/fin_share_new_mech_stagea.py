#!/usr/bin/env python3
"""FIN-share new-mechanism Stage A — CLIP / COND / SKEW / CASH / SAT_REF (paper).

Charter: research/ops/FIN_SHARE_NEW_MECH_STAGEA_CHARTER.md
Soft-Frozen live KEEP · Exact T+1 KEEP · L1=0.05 KEEP · no live wire.
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
from e45_paper_harness import load_dividends, load_market
from live_config import LIVE_FUSE_SOFT_SELL_BOOST
from soft_assist_helpers import LIVE_KD
from ta_indicator_catalog import build_low_high_catalog
from within_sleeve_alloc import build_kd_season_tilt_scores, build_pre_exdiv_window_buy_ok

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "fin-share-new-mech-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_SHARE_NEW_MECH_STAGEA_CHARTER"
SCREEN_ID = "FIN_SHARE_NEW_MECH_STAGEA_SCREEN"
DECISION_ID = "FIN_SHARE_NEW_MECH_DECISION_PACK"
BASE_ID = "BASE_LIVE_CONF"
OFF_CODE = "00631L"
OFF_PRICE = ROOT / "data" / "def_proxies" / "00631L_ohlcv.csv"
SELL_AMP = float(LIVE_FUSE_SOFT_SELL_BOOST)

CAGR_FLOOR_PP = 0.20
HELD_MDD_MIN_PP = -0.50
SEALED_MDD_MIN_PP = 0.0
TIP_MDD_TOL_PP = -0.50

LIVE_CLIPS = (
    float(soft.SOFT_FROZEN_FIN_LO),
    float(soft.SOFT_FROZEN_FIN_HI),
    float(soft.SOFT_FROZEN_TEL_LO),
    float(soft.SOFT_FROZEN_TEL_HI),
    float(soft.SOFT_FROZEN_ETF_LO),
    float(soft.SOFT_FROZEN_ETF_HI),
)


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _gate_mask(regime: pd.Series, gate: str) -> pd.Series:
    rg = regime.astype(str)
    if gate == "REG_BULL":
        return rg == "Bull"
    if gate == "REG_BULL_SIDE":
        return rg.isin(["Bull", "Sideways"])
    raise ValueError(gate)


def build_clip_targets(
    *,
    regime: pd.Series,
    score: pd.DataFrame,
    clips: tuple[float, ...],
) -> pd.DataFrame:
    return clip.build_targets_with_clips(
        regime=regime,
        score=score,
        fin_lo=clips[0],
        fin_hi=clips[1],
        tel_lo=clips[2],
        tel_hi=clips[3],
        etf_lo=clips[4],
        etf_hi=clips[5],
    )


def build_cond_targets(
    *,
    regime: pd.Series,
    score: pd.DataFrame,
    gate: str,
    on_clips: tuple[float, ...],
    off_clips: tuple[float, ...] = LIVE_CLIPS,
) -> pd.DataFrame:
    """Regime-conditional clip boxes (FIN cap when gate on)."""
    mask = _gate_mask(regime, gate).reindex(score.index).fillna(False)
    on_lo = np.array([on_clips[0], on_clips[2], on_clips[4]], dtype=float)
    on_hi = np.array([on_clips[1], on_clips[3], on_clips[5]], dtype=float)
    off_lo = np.array([off_clips[0], off_clips[2], off_clips[4]], dtype=float)
    off_hi = np.array([off_clips[1], off_clips[3], off_clips[5]], dtype=float)
    live_lo = np.array([LIVE_CLIPS[0], LIVE_CLIPS[2], LIVE_CLIPS[4]], dtype=float)
    live_hi = np.array([LIVE_CLIPS[1], LIVE_CLIPS[3], LIVE_CLIPS[5]], dtype=float)
    start = clip.apply_clip_box(
        (live_lo + live_hi) / 2.0, live_lo, live_hi, soft.START_WEIGHTS.copy()
    )
    out = []
    cur = start.copy()
    for i, _dt in enumerate(score.index):
        lo = on_lo if bool(mask.iloc[i]) else off_lo
        hi = on_hi if bool(mask.iloc[i]) else off_hi
        pri = soft.REGIME_PRIORS[str(regime.iloc[i])]
        cand = np.maximum(pri + 0.10 * np.clip(score.iloc[i].to_numpy(), -2.0, 2.0), 0.0)
        cand = clip.apply_clip_box(cand, lo, hi, start)
        desired = soft.BLEND_OLD * cur + soft.BLEND_NEW * cand
        desired = clip.apply_clip_box(desired, lo, hi, start)
        if float(np.abs(desired - cur).sum()) >= float(soft.REBALANCE_L1_MIN):
            cur = desired
        out.append(cur.copy())
    return pd.DataFrame(out, index=score.index, columns=["Financial", "Telecom", "0050"])


def apply_cool_skew(
    tgt: pd.DataFrame,
    cool: pd.Series,
    *,
    mode: str,
) -> pd.DataFrame:
    """Skew COOL cut toward FIN. Returns 3-sleeve schedule (no DEF yet)."""
    idx = tgt.index
    c = cool.reindex(idx).fillna(1.0).astype(float).clip(0.0, 1.0)
    fin = tgt["Financial"].astype(float)
    tel = tgt["Telecom"].astype(float)
    etf = tgt["0050"].astype(float)
    if mode == "FIN_ONLY":
        # Only Financial is scaled by cool; TEL/0050 full; cash = fin*(1-cool)
        fin_s = fin * c
        tel_s = tel
        etf_s = etf
    elif mode == "FIN_HEAVY":
        # FIN gets full cool cut; others get half-cut: scale = 0.5+0.5*cool
        other = 0.5 + 0.5 * c
        fin_s = fin * c
        tel_s = tel * other
        etf_s = etf * other
    else:
        raise ValueError(mode)
    return pd.DataFrame(
        {"Financial": fin_s, "Telecom": tel_s, "0050": etf_s},
        index=idx,
    )


def apply_cash_floor(tgt: pd.DataFrame, cool: pd.Series, *, floor: float) -> pd.DataFrame:
    """Scale Soft by cool*(1-floor); residual cash."""
    idx = tgt.index
    c = cool.reindex(idx).fillna(1.0).astype(float).clip(0.0, 1.0)
    scale = c * (1.0 - float(floor))
    return pd.DataFrame(
        {
            "Financial": tgt["Financial"].astype(float) * scale,
            "Telecom": tgt["Telecom"].astype(float) * scale,
            "0050": tgt["0050"].astype(float) * scale,
        },
        index=idx,
    )


def attach_conf(
    soft3: pd.DataFrame,
    cool: pd.Series,
    *,
    alpha: float,
    hold_h: int,
    listed_from: pd.Timestamp,
    ret1: pd.Series,
    ret3: pd.Series,
    proxy: pd.Series,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Build CONF pulse on Soft sleeves already cool/cash/skew scaled.

    Reconstruct Soft from soft3 / cool so CONF funding uses residual equity.
    """
    # soft3 already includes cool (and skew/cash). Treat as post-cool Soft;
    # CONF: reduce Soft further by (1-off) and add DEF.
    idx = soft3.index
    c = cool.reindex(idx).fillna(1.0).astype(float).clip(0.0, 1.0)
    # Recover pre-cool Soft weights where possible for CONF entry logic
    # Entry uses cool exits + RET3; sizing from soft3 columns.
    listed = pd.Series(idx >= listed_from, index=idx)
    exits = reb.cool_exits(c)
    entry = exits & listed & (ret3.reindex(idx) > 0)
    pulse = pd.Series(False, index=idx)
    entry_locs = [i for i, v in enumerate(entry.to_numpy()) if bool(v)]
    n = len(idx)
    for i0 in entry_locs:
        for k in range(int(hold_h)):
            j = i0 + k
            if j < n and bool(listed.iloc[j]):
                pulse.iloc[j] = True
    off_w = pd.Series(0.0, index=idx, dtype=float)
    off_w = off_w.where(~pulse, float(alpha))
    off_w = off_w.where(listed, 0.0)
    # soft3 sum may be <1 (cash); fund OFF from remaining headroom then shrink Soft
    soft_sum = soft3.sum(axis=1).astype(float).clip(lower=0.0)
    # Cap off by free cash-like residual + soft shrink
    headroom = (1.0 - soft_sum).clip(lower=0.0)
    # Prefer funding from headroom; if off > headroom, shrink Soft
    take_soft = (off_w - headroom).clip(lower=0.0)
    shrink = pd.Series(1.0, index=idx, dtype=float)
    need = take_soft > 1e-12
    shrink = shrink.where(~need, (soft_sum - take_soft).clip(lower=0.0) / soft_sum.where(soft_sum > 1e-12, 1.0))
    soft_scaled = soft3.mul(shrink, axis=0)
    # If headroom covers off, soft unchanged; DEF = off
    sched = pd.DataFrame(
        {
            "Financial": soft_scaled["Financial"].astype(float),
            "Telecom": soft_scaled["Telecom"].astype(float),
            "0050": soft_scaled["0050"].astype(float),
            "DEF": off_w.astype(float),
        },
        index=idx,
    )
    meta = {
        "n_entries": int(len(entry_locs)),
        "pulse_frac": float(pulse.mean()),
        "mean_off": float(off_w.mean()),
        "mean_fin": float(sched["Financial"].mean()),
        "mean_soft": float(sched[["Financial", "Telecom", "0050"]].sum(axis=1).mean()),
    }
    return sched, meta


def _score_row(
    base_w,
    chal_w,
    tip,
    *,
    rid: str,
    track: str,
    n_fills: int,
    meta: dict[str, Any],
    base_mean_fin: float,
) -> dict[str, Any]:
    h, s = chal_w[sat.HELDOUT], chal_w[sat.SEALED]
    bh, bs = base_w[sat.HELDOUT], base_w[sat.SEALED]
    held_cagr = sat.cagr_delta_pp(bh.get("cagr"), h.get("cagr"), missing_as_zero=True)
    sealed_cagr = sat.cagr_delta_pp(bs.get("cagr"), s.get("cagr"), missing_as_zero=True)
    if held_cagr is not None:
        held_cagr = -float(held_cagr)
    if sealed_cagr is not None:
        sealed_cagr = -float(sealed_cagr)
    held_mdd = float(sat.mdd_delta_pp(bh.get("max_drawdown"), h.get("max_drawdown")))
    sealed_mdd = float(sat.mdd_delta_pp(bs.get("max_drawdown"), s.get("max_drawdown")))
    tip_clean = tip.get("ytd", {}).get("gate") == "PASS" and tip.get("trailing_1y", {}).get("gate") == "PASS"
    tip_mdd_ok = tip_clean and float(tip["ytd"].get("mdd_improve_pp") or -9) >= TIP_MDD_TOL_PP and float(
        tip["trailing_1y"].get("mdd_improve_pp") or -9
    ) >= TIP_MDD_TOL_PP
    cagr_ok = held_cagr is not None and held_cagr >= CAGR_FLOOR_PP
    mdd_ok = held_mdd >= HELD_MDD_MIN_PP
    mean_fin = float(meta.get("mean_fin") or 0.0)
    fin_down = mean_fin < base_mean_fin - 1e-4
    mech_hit = bool(cagr_ok and mdd_ok)
    cagr_soft = bool(mdd_ok and not cagr_ok)
    gates = {
        "held_cagr_floor": bool(cagr_ok),
        "held_mdd": bool(mdd_ok),
        "sealed_mdd": sealed_mdd >= SEALED_MDD_MIN_PP,
        "tip_mdd_ok": bool(tip_mdd_ok),
        "fin_down": bool(fin_down),
    }
    score = (
        0.45 * ((held_cagr or 0.0) + (sealed_cagr or 0.0))
        + 0.40 * (held_mdd + sealed_mdd)
        + 0.15 * max(0.0, base_mean_fin - mean_fin) * 100.0
        - 0.25 * max(0.0, -(held_cagr or 0.0))
    )
    return {
        "id": rid,
        "track": track,
        "n_fills": n_fills,
        "meta": meta,
        "mean_fin": round(mean_fin, 6),
        "fin_down_pp": round((base_mean_fin - mean_fin) * 100.0, 4),
        "windows": chal_w,
        "held_cagr_lift_pp": None if held_cagr is None else round(held_cagr, 4),
        "sealed_cagr_lift_pp": None if sealed_cagr is None else round(sealed_cagr, 4),
        "held_mdd_improve_pp": round(held_mdd, 4),
        "sealed_mdd_improve_pp": round(sealed_mdd, 4),
        "tip": tip,
        "gates": gates,
        "mech_hit": mech_hit,
        "cagr_soft": cagr_soft,
        "score": round(float(score), 4),
    }


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.8]
    assert float(soft.REBALANCE_L1_MIN) == 0.05
    assert OFF_PRICE.exists(), OFF_PRICE

    sat.DEF_CODE = OFF_CODE
    sat.DEF_PRICE = OFF_PRICE
    short.OFF_CODE = OFF_CODE
    short.OFF_PRICE = OFF_PRICE

    print("loading ...", flush=True)
    market0 = load_market()
    dividends = load_dividends()
    off = sat.load_inv_bars()
    market_off, listed_from = sat.attach_inv(market0, off)

    _p, sleeve, _t0, regime = e50.e16_features(market0)
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
    tgt_live = sat._target_live(score_live, regime)

    print("offense + cool ...", flush=True)
    fuse_off, _, _ = sat._sim(
        market0,
        tgt_live,
        regime,
        dividends,
        scores=buy_live,
        buy_ok=buy_ok,
        sell=sell_live,
        exposure=pd.Series(1.0, index=tgt_live.index),
    )
    cool = sat._cool_from_offense(market0, fuse_off)
    cool.to_frame("cool_exposure").to_csv(OUT / "exposure_cool.csv")
    n_exits = int(reb.cool_exits(cool).sum())
    ret1, ret3 = short._0050_rets(market0, pd.DatetimeIndex(tgt_live.index))
    proxy = sat.stagea._risk_features(market0, sat.stagea._nav_series(fuse_off))[
        "proxy_mdd63"
    ].reindex(tgt_live.index).ffill()

    books: list[dict[str, Any]] = [
        {"id": BASE_ID, "track": "BASE", "kind": "base"},
        # CLIP — Soft flip candidates
        {"id": "CLIP_F070", "track": "CLIP", "kind": "clip", "fhi": 0.70},
        {"id": "CLIP_F072", "track": "CLIP", "kind": "clip", "fhi": 0.72},
        {"id": "CLIP_F075", "track": "CLIP", "kind": "clip", "fhi": 0.75},
        # COND — regime FIN cap
        {"id": "COND_BULL_F070", "track": "COND", "kind": "cond", "gate": "REG_BULL", "fhi": 0.70},
        {"id": "COND_BULL_F072", "track": "COND", "kind": "cond", "gate": "REG_BULL", "fhi": 0.72},
        {"id": "COND_BSIDE_F070", "track": "COND", "kind": "cond", "gate": "REG_BULL_SIDE", "fhi": 0.70},
        # SKEW — COOL cut FIN first
        {"id": "SKEW_FIN_ONLY", "track": "SKEW", "kind": "skew", "mode": "FIN_ONLY"},
        {"id": "SKEW_FIN_HEAVY", "track": "SKEW", "kind": "skew", "mode": "FIN_HEAVY"},
        # CASH floor
        {"id": "CASH_F05", "track": "CASH", "kind": "cash", "floor": 0.05},
        {"id": "CASH_F10", "track": "CASH", "kind": "cash", "floor": 0.10},
        # SAT reference
        {"id": "SAT_A20_H5", "track": "SAT_REF", "kind": "sat", "alpha": 0.20, "hold_h": 5},
    ]
    assert len(books) == 12, len(books)

    rows: list[dict[str, Any]] = []
    base_nav = None
    base_w = None
    base_mean_fin = 0.0

    for book in books:
        bid = book["id"]
        print(f"  [{bid}] ...", flush=True)
        kind = book["kind"]
        conf_alpha, conf_h = 0.10, 5

        if kind == "base":
            soft3 = tgt_live.mul(cool.reindex(tgt_live.index).fillna(1.0), axis=0)
            tgt_use = tgt_live
            regime_use = regime
        elif kind == "clip":
            fhi = float(book["fhi"])
            clips = (0.60, fhi, 0.03, 0.35, 0.00, 0.50)
            assert clip.feasible(*clips), bid
            tgt_use = build_clip_targets(regime=regime, score=score_live, clips=clips)
            # rebuild cool on challenger offense for causal stack
            fuse_c, _, _ = sat._sim(
                market0,
                tgt_use,
                regime,
                dividends,
                scores=buy_live,
                buy_ok=buy_ok,
                sell=sell_live,
                exposure=pd.Series(1.0, index=tgt_use.index),
            )
            cool_c = sat._cool_from_offense(market0, fuse_c)
            soft3 = tgt_use.mul(cool_c.reindex(tgt_use.index).fillna(1.0), axis=0)
            cool_for_conf = cool_c
            regime_use = regime
            proxy_c = sat.stagea._risk_features(market0, sat.stagea._nav_series(fuse_c))[
                "proxy_mdd63"
            ].reindex(tgt_use.index).ffill()
            ret1_c, ret3_c = short._0050_rets(market0, pd.DatetimeIndex(tgt_use.index))
        elif kind == "cond":
            fhi = float(book["fhi"])
            on = (0.60, fhi, 0.03, 0.35, 0.00, 0.50)
            assert clip.feasible(*on), bid
            tgt_use = build_cond_targets(
                regime=regime, score=score_live, gate=book["gate"], on_clips=on
            )
            fuse_c, _, _ = sat._sim(
                market0,
                tgt_use,
                regime,
                dividends,
                scores=buy_live,
                buy_ok=buy_ok,
                sell=sell_live,
                exposure=pd.Series(1.0, index=tgt_use.index),
            )
            cool_c = sat._cool_from_offense(market0, fuse_c)
            soft3 = tgt_use.mul(cool_c.reindex(tgt_use.index).fillna(1.0), axis=0)
            cool_for_conf = cool_c
            regime_use = regime
            proxy_c = sat.stagea._risk_features(market0, sat.stagea._nav_series(fuse_c))[
                "proxy_mdd63"
            ].reindex(tgt_use.index).ffill()
            ret1_c, ret3_c = short._0050_rets(market0, pd.DatetimeIndex(tgt_use.index))
        elif kind == "skew":
            tgt_use = tgt_live
            soft3 = apply_cool_skew(tgt_live, cool, mode=book["mode"])
            cool_for_conf = cool
            regime_use = regime
            proxy_c, ret1_c, ret3_c = proxy, ret1, ret3
        elif kind == "cash":
            tgt_use = tgt_live
            soft3 = apply_cash_floor(tgt_live, cool, floor=float(book["floor"]))
            cool_for_conf = cool
            regime_use = regime
            proxy_c, ret1_c, ret3_c = proxy, ret1, ret3
        elif kind == "sat":
            tgt_use = tgt_live
            soft3 = tgt_live.mul(cool.reindex(tgt_live.index).fillna(1.0), axis=0)
            conf_alpha, conf_h = float(book["alpha"]), int(book["hold_h"])
            cool_for_conf = cool
            regime_use = regime
            proxy_c, ret1_c, ret3_c = proxy, ret1, ret3
        else:
            raise ValueError(kind)

        if kind == "base":
            cool_for_conf = cool
            proxy_c, ret1_c, ret3_c = proxy, ret1, ret3

        sched, meta = attach_conf(
            soft3,
            cool_for_conf,
            alpha=conf_alpha,
            hold_h=conf_h,
            listed_from=listed_from,
            ret1=ret1_c,
            ret3=ret3_c,
            proxy=proxy_c,
        )
        meta = {
            **meta,
            "kind": kind,
            "gate": book.get("gate"),
            "fhi": book.get("fhi"),
            "floor": book.get("floor"),
            "skew_mode": book.get("mode"),
            "conf_alpha": conf_alpha,
            "conf_h": conf_h,
        }
        sched.to_csv(OUT / f"schedule_{bid}.csv")
        nav, n_fills, _ = sat._sim(
            market_off,
            tgt_use,
            regime_use,
            dividends,
            scores=buy_live,
            buy_ok=buy_ok,
            sell=sell_live,
            schedule=sched,
        )
        nav.to_csv(OUT / f"nav_{bid}.csv", index=False)

        if bid == BASE_ID:
            base_nav = nav
            base_w = sat._pack(nav)
            base_mean_fin = float(meta["mean_fin"])
            tip = sat._tip(base_nav, base_nav)
            row = _score_row(
                base_w,
                base_w,
                tip,
                rid=bid,
                track="BASE",
                n_fills=n_fills,
                meta=meta,
                base_mean_fin=base_mean_fin,
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
            meta=meta,
            base_mean_fin=base_mean_fin,
        )
        rows.append(row)

    chal = [r for r in rows if r["track"] != "BASE"]
    hits = [r for r in chal if r["mech_hit"]]
    fin_hits = [r for r in hits if r["track"] != "SAT_REF"]
    sat_hits = [r for r in hits if r["track"] == "SAT_REF"]
    softs = [r for r in chal if r["cagr_soft"] and r["track"] != "SAT_REF"]
    fin_down_only = [
        r
        for r in chal
        if r["gates"]["fin_down"]
        and not r["mech_hit"]
        and not r["cagr_soft"]
        and r["track"] != "SAT_REF"
    ]
    any_cagr = any(
        r["gates"]["held_cagr_floor"] for r in chal if r["track"] != "SAT_REF"
    )

    if fin_hits:
        verdict = "MECH_HIT"
    elif sat_hits and not fin_hits:
        # Parent CONF densify still HIT; FIN-share actuators did not clear gates
        verdict = "SAT_REF_ONLY"
    elif softs and not any_cagr:
        verdict = "CAGR_SOFT"
    elif fin_down_only and not any_cagr:
        verdict = "FIN_DOWN_NO_LIFT"
    elif not any_cagr:
        verdict = "CLOSE_OBSERVE_RECOMMENDED"
    else:
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
        "baseline": BASE_ID,
        "base_mean_fin": round(base_mean_fin, 6),
        "n_cool_exits": n_exits,
        "gates": {
            "held_cagr_lift_pp_min": CAGR_FLOOR_PP,
            "held_mdd_improve_pp_min": HELD_MDD_MIN_PP,
        },
        "n_challengers": len(chal),
        "n_mech_hit": len(hits),
        "n_fin_share_hit": len(fin_hits),
        "n_cagr_soft": len(softs),
        "mech_hit_ids": [r["id"] for r in sorted(hits, key=lambda r: -r["score"])],
        "fin_share_hit_ids": [r["id"] for r in sorted(fin_hits, key=lambda r: -r["score"])],
        "cagr_soft_ids": [r["id"] for r in softs],
        "fin_down_ids": [r["id"] for r in chal if r["gates"]["fin_down"]],
        "best": (
            sorted(fin_hits, key=lambda r: -r["score"])[0]["id"]
            if fin_hits
            else (
                sorted(sat_hits, key=lambda r: -r["score"])[0]["id"]
                if sat_hits
                else (ranked[0]["id"] if ranked else None)
            )
        ),
        "ranked": ranked,
        "by_track": by_track,
        "baseline_windows": base_w,
    }
    (REP / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2) + "\n")
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2) + "\n")

    lines = [
        "# FIN-share new-mechanism Stage A — Screen",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Status: **`{verdict}`** · Soft-Frozen **KEEP** · Exact T+1 **KEEP** · live wire **false**",
        f"Base `{BASE_ID}` mean FIN=**{base_mean_fin:.2%}** · cool_exits=**{n_exits}**",
        "",
        f"MECH_HIT: **{len(hits)}** (FIN-share HIT: **{len(fin_hits)}**) · CAGR_SOFT: **{len(softs)}** / {len(chal)}",
        "",
        "## Ranked",
        "",
        "| book | track | FIN↓pp | mean FIN | CAGR↑h | MDD↑h | MDD↑s | tip | hit |",
        "|---|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for r in ranked:
        tip_ok = "Y" if r["gates"]["tip_mdd_ok"] else "N"
        lines.append(
            f"| `{r['id']}` | {r['track']} | {r['fin_down_pp']:+.2f} | {r['mean_fin']:.2%} | "
            f"{r['held_cagr_lift_pp']:+.2f} | {r['held_mdd_improve_pp']:+.2f} | "
            f"{r['sealed_mdd_improve_pp']:+.2f} | {tip_ok} | {'Y' if r['mech_hit'] else 'N'} |"
        )
    lines += [
        "",
        "## Binding",
        "",
        "1. Soft-Frozen live clips KEEP until dedicated CLIP ACCEPT.",
        "2. Exact T+1 · L1=0.05 KEEP.",
        "3. Even MECH_HIT → paper only; at most one track for ACCEPT discussion.",
        "",
        "Repro: `PYTHONPATH=scripts python3 scripts/fin_share_new_mech_stagea.py`",
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
        "n_mech_hit": len(hits),
        "n_fin_share_hit": len(fin_hits),
        "mech_hit_ids": payload["mech_hit_ids"],
        "fin_share_hit_ids": payload["fin_share_hit_ids"],
        "cagr_soft_ids": payload["cagr_soft_ids"],
        "fin_down_ids": payload["fin_down_ids"],
        "best": payload["best"],
        "base_mean_fin": payload["base_mean_fin"],
        "charter": f"research/ops/{CHARTER_ID}.md",
        "stage_a": f"research/ops/{SCREEN_ID}.md",
        "tracks": ["CLIP", "COND", "SKEW", "CASH", "SAT_REF"],
    }
    dlines = [
        "# FIN-share new-mechanism — Decision Pack (Stage A)",
        "",
        f"Date: 2026-09-27 · Generated `{decision['generated_at_utc']}`",
        f"Status: **{verdict}** · Soft-Frozen **KEEP** · Exact T+1 **KEEP** · live wire **false**",
        "",
        "Tracks: CLIP · COND · SKEW · CASH · SAT_REF",
        "",
        f"MECH_HIT: **{len(hits)}** · FIN-share HIT: **{len(fin_hits)}** · CAGR_SOFT: **{len(softs)}** · FIN↓ books: **{len(payload['fin_down_ids'])}**",
        f"Base mean FIN: **{base_mean_fin:.2%}**",
        "",
    ]
    if verdict == "MECH_HIT" and fin_hits:
        b = sorted(fin_hits, key=lambda r: -r["score"])[0]
        dlines += [
            f"Best FIN-share: `{b['id']}` ({b['track']}) · held CAGR↑ **{b['held_cagr_lift_pp']:+.2f}** · "
            f"held MDD↑ **{b['held_mdd_improve_pp']:+.2f}** · FIN↓ **{b['fin_down_pp']:+.2f}pp**",
            "",
            "Next: paper observe / ACCEPT discussion for **one** track. "
            "CLIP HIT ⇒ Soft-Frozen flip ballot only.",
            "",
        ]
    elif verdict == "SAT_REF_ONLY":
        dlines += [
            "FIN-share actuators (CLIP / COND / SKEW / CASH) **do not** clear CAGR+MDD gates.",
            "",
            "They often **lower mean FIN** (good for the ratio question) but **give back CAGR**.",
            "",
            f"Only parent reference `SAT_A20_H5` remains MECH_HIT (CONF densify — not a FIN-share lever).",
            "",
            "Reading: cutting Soft FIN share is not a free lunch under the live twin. "
            "Keep Soft-Frozen clips; tip ~87% FIN is mostly **lot drift** (fix on next open via L1=0.05), "
            "not a clip rewrite.",
            "",
            "Binding: Soft-Frozen KEEP · Exact T+1 KEEP · L1=0.05 KEEP · no live wire. "
            "SAT_A20 remains the only ACCEPT-discussion candidate from recent menus.",
            "",
        ]
    elif verdict == "CAGR_SOFT":
        dlines += [
            "MDD gate OK somewhere but CAGR floor (+0.20pp) not cleared.",
            "",
            "Binding: Soft-Frozen KEEP · no live wire.",
            "",
        ]
    elif verdict == "FIN_DOWN_NO_LIFT":
        dlines += [
            "Mechanisms **do** lower mean FIN vs base, but none clear CAGR/MDD gates.",
            "",
            "Reading: cutting FIN share alone is not a free lunch under live twin.",
            "",
            "Binding: Soft-Frozen KEEP · Exact T+1 KEEP · L1=0.05 KEEP · no live wire.",
            "",
        ]
    elif verdict == "CLOSE_OBSERVE_RECOMMENDED":
        dlines += [
            "No CAGR path and no useful FIN↓ coexist under predeclared gates.",
            "",
            "Recommend CLOSE observe on this FIN-share menu; reopen only with a newer mechanism.",
            "",
        ]
    else:
        dlines += [
            "CAGR cleared somewhere but MDD blocked.",
            "",
            "Binding: Soft-Frozen KEEP · no live wire.",
            "",
        ]
    dlines += [
        "## Refs",
        "",
        f"- Charter: `{CHARTER_ID}.md`",
        f"- Screen: `{SCREEN_ID}.md`",
        "- Parent next-mech: `NEXT_MECH_STAGEA_DECISION_PACK.md`",
        "- Prior Asymm: `ASYMM_0050_BULL_DENSIFY_UNDER_COOL_DECISION_PACK.md`",
        "",
        f"Label: `{DECISION_ID}_2026-09-27__{verdict}`",
        "",
    ]
    (OPS / f"{DECISION_ID}.json").write_text(json.dumps(decision, indent=2) + "\n")
    (OPS / f"{DECISION_ID}.md").write_text("\n".join(dlines))
    (REP / f"{DECISION_ID}.json").write_text(json.dumps(decision, indent=2) + "\n")
    (REP / f"{DECISION_ID}.md").write_text("\n".join(dlines))
    (OPS / f"{DECISION_ID}.zh-TW.md").write_text(
        "\n".join(
            [
                "# 金融比重新機制 — 決策包",
                "",
                f"狀態：**{verdict}** · Soft-Frozen／Exact T+1／L1 **KEEP** · 不進 live",
                f"HIT：**{len(hits)}** · best：`{payload['best']}` · base FIN：**{base_mean_fin:.2%}**",
                "",
                "複現：`PYTHONPATH=scripts python3 scripts/fin_share_new_mech_stagea.py`",
                "",
            ]
        )
    )

    print(
        json.dumps(
            {
                "verdict": verdict,
                "n_mech_hit": len(hits),
                "mech_hit_ids": payload["mech_hit_ids"],
                "base_mean_fin": round(base_mean_fin, 4),
                "top5": [
                    {
                        "id": r["id"],
                        "track": r["track"],
                        "fin_down_pp": r["fin_down_pp"],
                        "cagr": r["held_cagr_lift_pp"],
                        "mdd": r["held_mdd_improve_pp"],
                        "hit": r["mech_hit"],
                    }
                    for r in ranked[:5]
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
