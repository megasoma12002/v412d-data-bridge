#!/usr/bin/env python3
"""Path3×Path4 tip Soft twin under live stack (0kap) — Exact T+1 · Stage B.

**Question:** Against current live ``BASE_LIVE_FUSE_COOL`` (Soft clips + FUSE
``SELL_a75`` + ``COOL_c8``), does Path3 WITHIN and/or Path4 Soft-0050
``OFF_CASH_ETF`` still lift tip/held — i.e. how should live be optimized?

Arms
- ``BASE_LIVE_FUSE_COOL`` — current live paper twin
- ``LIVE_P3_WITHIN`` — Soft clips+0050 KEEP · Path3 ledger mixes drive FIN/TEL scores
- ``LIVE_P3_P4_CASH_{θ}`` — P3 WITHIN + Soft-own Path4 CASH_ETF gate on Soft 0050
- ``LIVE_P4_ONLY_001`` — no Path3; Soft KD KEEP + Path4 CASH θ=0.01

Soft KEEP · broker false · Path4 live OFF · no wire.
Parent Soft-core carve: ``0kao`` / ``P3_P4_COEXIST_HIT``.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import e16_clip_search_challenger as clip
import e16_soft_frozen_base as soft
import e22_dividend_accounting as e22div
import e45_defend_handoff_stagea_screen as stagea
from cool_c8_proxy_observe_helpers import build_cool_c8_exposure
from e16_soft_frozen_base import FIN, TEL
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, load_market, window_stats
from e50_early_stack_combined_nav import e16_features, simulate_core
from fin_sell_quality_helpers import cagr_lift_pp
from live_config import LIVE_FUSE_SOFT_SELL_BOOST
from live_path3_t0_switch_emitter import BOOK_COMP, BOOK_SAT, load_or_build_signal
from ops_repro_ssot import write_ops_and_repro_pointer, write_repro_pointer
from path3_comp_sat_daily_share_ssot import dollar_mix, load_book_shares
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
    FIN_RS_SOFT_TILT,
    TEL_EQUAL,
    TEL_RS_SOFT_TILT,
    build_kd_season_tilt_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "fin-sat-path3-path4-livestack-twin-stageb"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_SAT_PATH3_PATH4_LIVESTACK_TWIN_STAGEB_CHARTER"
SCREEN_ID = "FIN_SAT_PATH3_PATH4_LIVESTACK_TWIN_STAGEB_SCREEN"
DECISION_ID = "FIN_SAT_PATH3_PATH4_LIVESTACK_TWIN_STAGEB_DECISION_PACK"
REGISTER = "0kap"
PARENTS = ("0kao", "0kac", "0kak")

BASE_ID = "BASE_LIVE_FUSE_COOL"
E22_VERSION = e22div.DEFAULT_BOOKS_VERSION
SELL_AMP = float(LIVE_FUSE_SOFT_SELL_BOOST)
ETF = "0050"
SOFT_CORE = list(FIN) + list(TEL) + [ETF]
TRAIL = 63
THETAS = (0.0025, 0.005, 0.01)

SEALED_MDD_FLOOR_PP = -0.25
TIP_Y_FLOOR_PP = -1.0
HELD_CAGR_FLOOR_PP = 0.10


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
            out[wname] = {"cagr_lift_pp": None, "mdd_improve_pp": None}
            continue
        bn = b["nav"].astype(float) / float(b["nav"].iloc[0])
        cn = c["nav"].astype(float) / float(c["nav"].iloc[0])
        b_mdd = float((bn / bn.cummax() - 1.0).min())
        c_mdd = float((cn / cn.cummax() - 1.0).min())
        years = (len(b) - 1) / 252.0
        bc = float(bn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        cc = float(cn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        out[wname] = {
            "cagr_lift_pp": None
            if cagr_lift_pp(bc, cc) is None
            else round(float(cagr_lift_pp(bc, cc)), 4),
            "mdd_improve_pp": round(float(mdd_delta_pp(b_mdd, c_mdd)), 4),
        }
    return out


def _delta_windows(base_w: dict, chal_w: dict) -> dict[str, Any]:
    out = {}
    for k in ("full", "heldout_2019_plus", "sealed_2023_plus"):
        b, c = base_w.get(k) or {}, chal_w.get(k) or {}
        out[k] = {
            "cagr_lift_pp": None
            if cagr_lift_pp(b.get("cagr"), c.get("cagr")) is None
            else round(float(cagr_lift_pp(b.get("cagr"), c.get("cagr"))), 4),
            "mdd_improve_pp": None
            if b.get("max_drawdown") is None or c.get("max_drawdown") is None
            else round(float(mdd_delta_pp(b["max_drawdown"], c["max_drawdown"])), 4),
            "base_cagr": b.get("cagr"),
            "chal_cagr": c.get("cagr"),
            "base_mdd": b.get("max_drawdown"),
            "chal_mdd": c.get("max_drawdown"),
        }
    return out


def yearly_compare(nav_keep: pd.DataFrame, nav_chal: pd.DataFrame) -> list[dict[str, Any]]:
    def _yr(nav: pd.DataFrame) -> dict[int, dict[str, float]]:
        x = nav.copy()
        x["date"] = pd.to_datetime(x["date"])
        x["year"] = x["date"].dt.year
        out: dict[int, dict[str, float]] = {}
        for y, g in x.groupby("year"):
            g = g.reset_index(drop=True)
            if len(g) < 2:
                continue
            bn = g["nav"].astype(float) / float(g["nav"].iloc[0])
            out[int(y)] = {
                "ret": float(bn.iloc[-1] - 1.0),
                "mdd": float((bn / bn.cummax() - 1.0).min()),
            }
        return out

    a, b = _yr(nav_keep), _yr(nav_chal)
    rows = []
    for y in sorted(set(a) | set(b)):
        ka, kb = a.get(y), b.get(y)
        if not ka or not kb:
            continue
        rows.append(
            {
                "year": y,
                "ret_keep_pct": round(ka["ret"] * 100, 4),
                "ret_chal_pct": round(kb["ret"] * 100, 4),
                "ret_lift_pp": round((kb["ret"] - ka["ret"]) * 100, 4),
                "ret_win": bool(kb["ret"] > ka["ret"]),
            }
        )
    return rows


def _arm_verdict(delta: dict[str, Any], tip: dict[str, Any]) -> str:
    held = delta["heldout_2019_plus"]
    sealed = delta["sealed_2023_plus"]
    tip_y = (tip.get("ytd") or {}).get("cagr_lift_pp")
    if held.get("cagr_lift_pp") is None or sealed.get("mdd_improve_pp") is None:
        return "INCOMPLETE"
    held_ok = float(held["cagr_lift_pp"]) >= HELD_CAGR_FLOOR_PP
    sealed_ok = float(sealed["mdd_improve_pp"]) >= SEALED_MDD_FLOOR_PP
    tip_ok = tip_y is None or float(tip_y) >= TIP_Y_FLOOR_PP
    full_ok = float(delta["full"].get("cagr_lift_pp") or 0) > 0
    if held_ok and sealed_ok and tip_ok and full_ok:
        return "HIT"
    if held_ok and sealed_ok and tip_ok:
        return "HELD_HIT"
    if sealed_ok and tip_ok and float(held["cagr_lift_pp"]) > 0.02:
        return "SOFT"
    if float(sealed["mdd_improve_pp"]) < SEALED_MDD_FLOOR_PP:
        return "MDD_BLOCK"
    if tip_y is not None and float(tip_y) < TIP_Y_FLOOR_PP:
        return "TIP_BLOCK"
    return "NO_EDGE"


def _theta_tag(th: float) -> str:
    s = f"{th:.4f}".rstrip("0").rstrip(".")
    return s.replace(".", "")


def _buy(kd, lows, k9_amp: float = 1.0) -> pd.DataFrame:
    out = soft_boost_scores(kd, lows[BUY_LOW_ID], 1.0)
    return soft_boost_scores(out, lows["K9_LT30"], float(k9_amp))


def _sell(highs, amp: float = SELL_AMP) -> pd.DataFrame:
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


def _close_panel(market: pd.DataFrame, codes: list[str]) -> pd.DataFrame:
    m = market[market["code"].isin(codes)].copy()
    m["date"] = pd.to_datetime(m["date"])
    return (
        m.pivot_table(index="date", columns="code", values="close", aggfunc="last")
        .sort_index()
        .astype(float)
        .reindex(columns=codes)
    )


def _trail_rel(r_on: pd.Series, r_off: pd.Series, window: int = TRAIL) -> pd.Series:
    rel = (r_on - r_off).astype(float)
    x = np.log1p(rel.clip(lower=-0.999999))
    return np.expm1(x.rolling(window, min_periods=window).sum())


def _soft_core_on_off_trails(px: pd.DataFrame, soft_tgt: pd.DataFrame) -> pd.Series:
    """Soft-own Path4 feature: Soft sleeve Soft-core ON vs CASH_ETF OFF trail."""
    dates = soft_tgt.index.intersection(px.index)
    # Approximate Soft-core ON weights from Soft sleeve masses + equal within FIN/TEL
    w_on = pd.DataFrame(0.0, index=dates, columns=SOFT_CORE)
    for d in dates:
        fin_m = float(soft_tgt.loc[d, "Financial"])
        tel_m = float(soft_tgt.loc[d, "Telecom"])
        etf_m = float(soft_tgt.loc[d, "0050"])
        for c in FIN:
            w_on.loc[d, c] = fin_m / max(len(FIN), 1)
        for c in TEL:
            w_on.loc[d, c] = tel_m / max(len(TEL), 1)
        w_on.loc[d, ETF] = etf_m
    s = w_on.sum(axis=1).replace(0.0, np.nan)
    w_on = w_on.div(s, axis=0).fillna(0.0)
    w_cash = w_on.copy()
    w_cash[ETF] = 0.0
    rets = px.pct_change().reindex(dates).fillna(0.0)
    r_on = (w_on * rets).sum(axis=1)
    r_cash = (w_cash * rets).sum(axis=1)
    return _trail_rel(r_on, r_cash)


def _path3_mix_score_panels(
    *,
    sig: pd.DataFrame,
    shares_by_book: dict[str, pd.DataFrame],
    px: pd.DataFrame,
    cal: pd.DatetimeIndex,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Daily Path3 within-sleeve dollar mixes as name scores (active COMP/SAT book)."""
    sig = sig.copy()
    sig["date"] = pd.to_datetime(sig["date"]).dt.normalize()
    sig_i = sig.set_index("date").sort_index()
    fin_sc = pd.DataFrame(0.0, index=cal, columns=list(FIN))
    tel_sc = pd.DataFrame(0.0, index=cal, columns=list(TEL))
    for d in cal:
        if d in sig_i.index:
            row = sig_i.loc[d]
            if isinstance(row, pd.DataFrame):
                row = row.iloc[-1]
            book = str(row.get("book") or BOOK_COMP)
        else:
            book = BOOK_COMP
        if book not in shares_by_book:
            book = BOOK_COMP
        pan = shares_by_book[book]
        prior = pan.index[pan.index <= d]
        if len(prior) == 0:
            continue
        shares = pan.loc[prior[-1]].to_dict()
        px_row = px.loc[d] if d in px.index else None
        if px_row is None or px_row.isna().all():
            continue
        prices = {c: float(px_row[c]) for c in SOFT_CORE if c in px_row.index and pd.notna(px_row[c])}
        fm = dollar_mix(shares, prices, FIN)
        tm = dollar_mix(shares, prices, TEL)
        for c, w in fm.items():
            # map mix∈[0,1] → score∈[-2.5, 2.5] so soft_tilt prefers Path3 mass
            fin_sc.loc[d, c] = float(5.0 * w - 2.5)
        for c, w in tm.items():
            tel_sc.loc[d, c] = float(5.0 * w - 2.5)
    return fin_sc, tel_sc


def _apply_cash_etf_gate(target: pd.DataFrame, off_lead: pd.Series) -> pd.DataFrame:
    """Park Soft 0050 → 0 on OFF days; FIN/TEL absolute KEEP (cash residual)."""
    out = target.copy()
    lead = off_lead.reindex(out.index).fillna(False).astype(bool)
    out.loc[lead, ETF] = 0.0
    return out


def _sim(
    market,
    target,
    regime,
    dividends,
    *,
    scores,
    buy_ok,
    sell,
    exposure,
    financial_alloc: str,
    telecom_alloc: str,
    tel_scores=None,
):
    kw: dict[str, Any] = {
        "apply_e22": True,
        "apply_stock_div": True,
        "capital": float(DEFAULT_CAPITAL),
        "lot_size": int(BOARD_LOT),
        "financial_alloc": financial_alloc,
        "telecom_alloc": telecom_alloc,
        "fin_name_scores": scores,
        "fin_buy_ok": buy_ok,
        "fin_sell_scores": sell,
        "e45_exposure": exposure.astype(float),
        "e22_version": E22_VERSION,
    }
    if tel_scores is not None:
        kw["tel_name_scores"] = tel_scores
    nav, fills, meta = simulate_core(market, target, regime, dividends, **kw)
    if not bool(meta.get("exact_t1_ok")):
        raise RuntimeError("exact_t1_ok failed")
    return nav, fills, meta


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.8]
    assert abs(SELL_AMP - 0.75) < 1e-12, f"SELL_a75 KEEP required, got amp={SELL_AMP}"

    print("loading market / soft / path3 ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    prices, sleeve, _turn, regime = e16_features(market)
    _ = prices
    cal = pd.DatetimeIndex(pd.to_datetime(sorted(market["date"].unique())))
    lows, highs = build_low_high_catalog(market, cal, list(FIN))
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
    scores_live = _buy(kd, lows)
    sell = _sell(highs)
    sleeve_sc = _sleeve_score(market, sleeve, LIVE_SLEEVE_ALPHA)
    target = _target_live(sleeve_sc, regime)

    px = _close_panel(market, SOFT_CORE)
    shares = {
        BOOK_COMP: load_book_shares(BOOK_COMP),
        BOOK_SAT: load_book_shares(BOOK_SAT),
    }
    sig = load_or_build_signal()
    fin_p3, tel_p3 = _path3_mix_score_panels(
        sig=sig, shares_by_book=shares, px=px, cal=cal
    )
    trail = _soft_core_on_off_trails(px, target)
    trail.to_frame("trail_rel_on_cash_etf_63").to_csv(OUT / "path4_soft_own_trail.csv")

    print("offense NAV for frozen cool ...", flush=True)
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
        fin_name_scores=scores_live,
        fin_buy_ok=base_buy_ok,
        fin_sell_scores=sell,
        e22_version=E22_VERSION,
    )
    cool = _cool_from_offense(market, off_nav)
    cool.to_frame("e45_exposure").to_csv(OUT / "exposure_cool_from_fuse.csv")

    arms: dict[str, pd.DataFrame] = {}
    metas: dict[str, dict[str, Any]] = {}

    def _run(arm: str, tgt, *, fin_sc, tel_sc, fin_alloc, tel_alloc, buy_ok, meta_extra):
        print(f"{arm} ...", flush=True)
        nav, fills, meta = _sim(
            market,
            tgt,
            regime,
            dividends,
            scores=fin_sc,
            buy_ok=buy_ok,
            sell=sell,
            exposure=cool,
            financial_alloc=fin_alloc,
            telecom_alloc=tel_alloc,
            tel_scores=tel_sc,
        )
        nav.to_csv(OUT / f"nav_{arm}.csv", index=False)
        fills.to_csv(OUT / f"fills_{arm}.csv", index=False)
        arms[arm] = nav
        metas[arm] = {
            "n_fills": int(len(fills)),
            "exact_t1_ok": bool(meta.get("exact_t1_ok")),
            "financial_alloc": fin_alloc,
            "telecom_alloc": tel_alloc,
            **meta_extra,
        }

    _run(
        BASE_ID,
        target,
        fin_sc=scores_live,
        tel_sc=None,
        fin_alloc=FIN_PRE_EXDIV_KD,
        tel_alloc=TEL_EQUAL,
        buy_ok=base_buy_ok,
        meta_extra={"kind": "live_base", "path3": False, "path4": False},
    )

    _run(
        "LIVE_P3_WITHIN",
        target,
        fin_sc=fin_p3,
        tel_sc=tel_p3,
        fin_alloc=FIN_RS_SOFT_TILT,
        tel_alloc=TEL_RS_SOFT_TILT,
        buy_ok=None,
        meta_extra={"kind": "live_p3_within", "path3": True, "path4": False},
    )

    for th in THETAS:
        lead = (trail <= -float(th)) & trail.notna()
        lead = lead.reindex(target.index).fillna(False)
        tgt_p4 = _apply_cash_etf_gate(target, lead)
        name = f"LIVE_P3_P4_CASH_{_theta_tag(th)}"
        _run(
            name,
            tgt_p4,
            fin_sc=fin_p3,
            tel_sc=tel_p3,
            fin_alloc=FIN_RS_SOFT_TILT,
            tel_alloc=TEL_RS_SOFT_TILT,
            buy_ok=None,
            meta_extra={
                "kind": "live_p3_p4_cash_etf",
                "path3": True,
                "path4": True,
                "theta": th,
                "n_off_days": int(lead.sum()),
                "pct_off": round(float(lead.mean()), 4),
                "off_book": "CASH_ETF",
            },
        )

    lead001 = (trail <= -0.01) & trail.notna()
    lead001 = lead001.reindex(target.index).fillna(False)
    _run(
        "LIVE_P4_ONLY_001",
        _apply_cash_etf_gate(target, lead001),
        fin_sc=scores_live,
        tel_sc=None,
        fin_alloc=FIN_PRE_EXDIV_KD,
        tel_alloc=TEL_EQUAL,
        buy_ok=base_buy_ok,
        meta_extra={
            "kind": "live_p4_only",
            "path3": False,
            "path4": True,
            "theta": 0.01,
            "n_off_days": int(lead001.sum()),
            "pct_off": round(float(lead001.mean()), 4),
            "off_book": "CASH_ETF",
        },
    )

    base = arms[BASE_ID]
    bw = _pack(base)
    rows = []
    for arm, nav in arms.items():
        if arm == BASE_ID:
            continue
        delta = _delta_windows(bw, _pack(nav))
        tip = _tip(base, nav)
        yearly = yearly_compare(base, nav)
        ret_w = int(sum(1 for r in yearly if r["ret_win"]))
        ret_l = int(sum(1 for r in yearly if not r["ret_win"]))
        v = _arm_verdict(delta, tip)
        rows.append(
            {
                "arm": arm,
                "verdict_vs_live": v,
                "full_cagr_lift_pp": delta["full"]["cagr_lift_pp"],
                "held_cagr_lift_pp": delta["heldout_2019_plus"]["cagr_lift_pp"],
                "sealed_mdd_improve_pp": delta["sealed_2023_plus"]["mdd_improve_pp"],
                "tip_ytd_cagr_lift_pp": (tip.get("ytd") or {}).get("cagr_lift_pp"),
                "tip_1y_cagr_lift_pp": (tip.get("trailing_1y") or {}).get("cagr_lift_pp"),
                "yearly_ret_wl": f"{ret_w}-{ret_l}",
                "meta": metas.get(arm, {}),
                "delta": delta,
                "tip": tip,
                "yearly": yearly,
            }
        )

    def _rank(r: dict[str, Any]) -> tuple[float, float, float]:
        return (
            float(r["held_cagr_lift_pp"] or -999),
            float(r["tip_ytd_cagr_lift_pp"] or -999),
            float(r["sealed_mdd_improve_pp"] or -999),
        )

    hit = [r for r in rows if r["verdict_vs_live"] in {"HIT", "HELD_HIT"}]
    if hit:
        champion = max(hit, key=_rank)
        pack_verdict = "LIVESTACK_TWIN_HIT"
    else:
        soft_rows = [r for r in rows if r["verdict_vs_live"] == "SOFT"]
        if soft_rows:
            champion = max(soft_rows, key=_rank)
            pack_verdict = "LIVESTACK_TWIN_SOFT"
        else:
            champion = max(rows, key=_rank)
            pack_verdict = f"LIVESTACK_TWIN_{champion['verdict_vs_live']}"

    p3_only = next((r for r in rows if r["arm"] == "LIVE_P3_WITHIN"), None)
    p4_only = next((r for r in rows if r["arm"] == "LIVE_P4_ONLY_001"), None)
    p3p4 = [r for r in rows if (r.get("meta") or {}).get("kind") == "live_p3_p4_cash_etf"]

    # Live optimization recommendation
    rec: list[str] = []
    if p3_only and p3_only["verdict_vs_live"] in {"HIT", "HELD_HIT", "SOFT"}:
        rec.append(
            f"Promote Path3 WITHIN on live stack first "
            f"(`LIVE_P3_WITHIN` {p3_only['verdict_vs_live']} held "
            f"{p3_only['held_cagr_lift_pp']} tipY {p3_only['tip_ytd_cagr_lift_pp']})"
        )
    elif p3_only:
        rec.append(
            f"Path3 WITHIN tip Soft twin "
            f"{p3_only['verdict_vs_live']} vs live — do not cut over on tip Soft alone; "
            f"held {p3_only['held_cagr_lift_pp']} tipY {p3_only['tip_ytd_cagr_lift_pp']}"
        )
    best_p3p4 = max(p3p4, key=_rank) if p3p4 else None
    if best_p3p4 and best_p3p4["verdict_vs_live"] in {"HIT", "HELD_HIT"}:
        if p3_only and float(best_p3p4["held_cagr_lift_pp"] or 0) > float(
            p3_only["held_cagr_lift_pp"] or 0
        ) + 0.05:
            rec.append(
                f"After P3 live: Stage B Path4 CASH_ETF `{best_p3p4['arm']}` "
                f"adds held edge — ballot later (still Path4 live OFF now)"
            )
        else:
            rec.append(
                f"P3+P4 `{best_p3p4['arm']}` HIT but ≤ P3-only edge — "
                "keep Soft sticky 0050; Path4 live OFF"
            )
    elif best_p3p4:
        rec.append(
            f"P3+P4 best `{best_p3p4['arm']}` = {best_p3p4['verdict_vs_live']} "
            "under live stack — Path4 live OFF; Soft 0050 sticky KEEP"
        )
    if p4_only and p4_only["verdict_vs_live"] in {"HIT", "HELD_HIT"}:
        rec.append(
            f"P4-only under Soft KD also {p4_only['verdict_vs_live']} — "
            "still sequence after P3 observe; OFF=CASH_ETF only"
        )
    rec.append("COOL_c8 + FUSE SELL_a75 + Soft clips KEEP on all arms (frozen cool)")
    rec.append("Soft KEEP · broker false · Path4 live flag OFF · no wire this pack")

    summary = [
        {
            "arm": r["arm"],
            "verdict_vs_live": r["verdict_vs_live"],
            "full_cagr_lift_pp": r["full_cagr_lift_pp"],
            "held_cagr_lift_pp": r["held_cagr_lift_pp"],
            "sealed_mdd_improve_pp": r["sealed_mdd_improve_pp"],
            "tip_ytd_cagr_lift_pp": r["tip_ytd_cagr_lift_pp"],
            "tip_1y_cagr_lift_pp": r["tip_1y_cagr_lift_pp"],
            "yearly_ret_wl": r["yearly_ret_wl"],
            **{f"meta_{k}": v for k, v in (r["meta"] or {}).items()},
        }
        for r in rows
    ]
    pd.DataFrame(summary).to_csv(OUT / "arms_vs_live.csv", index=False)
    pd.DataFrame(champion["yearly"]).to_csv(
        OUT / "yearly_champion_vs_live.csv", index=False
    )

    screen = {
        "generated_at_utc": generated,
        "register": REGISTER,
        "parents": list(PARENTS),
        "mech": "PATH3_PATH4_LIVESTACK_TWIN",
        "verdict": pack_verdict,
        "fill_timing": "exact_t1",
        "base": BASE_ID,
        "champion_arm": champion["arm"],
        "live_stack": {
            "soft_clips": True,
            "fuse_sell_a75": True,
            "cool_c8": True,
            "cool_frozen_from_base_offense": True,
        },
        "arms_vs_live": summary,
        "champion": {
            "arm": champion["arm"],
            "verdict_vs_live": champion["verdict_vs_live"],
            "delta": champion["delta"],
            "tip": champion["tip"],
            "meta": champion["meta"],
        },
        "live_p3_within": p3_only,
        "live_p4_only_001": p4_only,
        "optimize_live": rec,
        "gates": {
            "held_cagr_floor_pp": HELD_CAGR_FLOOR_PP,
            "sealed_mdd_floor_pp": SEALED_MDD_FLOOR_PP,
            "tip_y_floor_pp": TIP_Y_FLOOR_PP,
        },
    }
    (OUT / "screen.json").write_text(json.dumps(screen, indent=2, default=str) + "\n")

    charter = "\n".join(
        [
            f"# {CHARTER_ID}",
            "",
            f"Date: {generated[:10]}",
            "Status: **Stage B — tip Soft twin under live stack** · Soft **KEEP** · "
            "broker **false** · Path4 live **OFF**",
            f"Register: **{REGISTER}** · Parents: {', '.join(PARENTS)}",
            "",
            "## Question",
            "",
            "Against ``BASE_LIVE_FUSE_COOL``, how should live be optimized among "
            "Path3 WITHIN / Path4 Soft-0050 CASH_ETF / neither?",
            "",
            "## Live stack (frozen)",
            "",
            "- Soft clips F[0.60,0.80] T[0.03,0.35] E[0.00,0.50]",
            "- FUSE Soft sell ``SELL_a75`` · COOL_c8 from BASE offense",
            "- Exact T+1 · E22 books",
            "",
            "## Non-goals",
            "",
            "- Path4 live wire · OFF_RENORM · broker · Soft clip flip",
            "",
            f"Label: `{CHARTER_ID}_{generated[:10]}__LIVESTACK_TWIN__NO_LIVE`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{CHARTER_ID}.md", REP / f"{CHARTER_ID}.md", charter, kind="charter"
    )
    (OPS / f"{CHARTER_ID}.json").write_text(
        json.dumps(
            {
                "id": CHARTER_ID,
                "register": REGISTER,
                "parents": list(PARENTS),
                "mech": "PATH3_PATH4_LIVESTACK_TWIN",
                "soft_keep": True,
                "broker": False,
                "path4_live": False,
            },
            indent=2,
        )
        + "\n"
    )
    write_repro_pointer(OPS / f"{CHARTER_ID}.json", REP / f"{CHARTER_ID}.json", kind="charter")

    def _fmt(r: dict) -> str:
        return (
            f"| {r['arm']} | {r['verdict_vs_live']} | {r['held_cagr_lift_pp']} | "
            f"{r['full_cagr_lift_pp']} | {r['sealed_mdd_improve_pp']} | "
            f"{r['tip_ytd_cagr_lift_pp']} | {r['tip_1y_cagr_lift_pp']} | "
            f"{r['yearly_ret_wl']} |"
        )

    screen_md = "\n".join(
        [
            f"# {SCREEN_ID}",
            "",
            f"Date: {generated[:10]} · Verdict: **`{pack_verdict}`** · "
            f"champion=**`{champion['arm']}`** · fill=`exact_t1`",
            f"Register: **{REGISTER}** · base=`{BASE_ID}`",
            "",
            "## Arms vs live stack",
            "",
            "| Arm | vs live | held | full | sealed MDD↑ | tipY | tip1y | ret W–L |",
            "|---|---|---:|---:|---:|---:|---:|---|",
            *[_fmt(r) for r in summary],
            "",
            f"## Champion `{champion['arm']}` yearly vs live",
            "",
            "| Year | Live ret% | Chal ret% | Ret lift pp |",
            "|---:|---:|---:|---:|",
            *[
                f"| {y['year']} | {y['ret_keep_pct']:.2f} | {y['ret_chal_pct']:.2f} | "
                f"{y['ret_lift_pp']:+.2f} |"
                for y in champion["yearly"]
            ],
            "",
            "## Optimize live",
            "",
            *[f"{i+1}. {s}" for i, s in enumerate(rec)],
            "",
            "Repro: `PYTHONPATH=scripts python3 "
            "scripts/fin_sat_path3_path4_livestack_twin_stageb.py`",
            "",
            f"Label: `{SCREEN_ID}_{generated[:10]}__{pack_verdict}`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", screen_md, kind="screen"
    )
    (OPS / f"{SCREEN_ID}.json").write_text(
        json.dumps(screen, indent=2, default=str) + "\n"
    )
    write_repro_pointer(OPS / f"{SCREEN_ID}.json", REP / f"{SCREEN_ID}.json", kind="screen")

    decision = {
        "label": f"{DECISION_ID}_{generated[:10]}__{pack_verdict}__NO_LIVE",
        "verdict": pack_verdict,
        "register": REGISTER,
        "parents": list(PARENTS),
        "mech": "PATH3_PATH4_LIVESTACK_TWIN",
        "champion_arm": champion["arm"],
        "held_cagr_lift_pp": champion["held_cagr_lift_pp"],
        "tip_ytd_cagr_lift_pp": champion["tip_ytd_cagr_lift_pp"],
        "sealed_mdd_improve_pp": champion["sealed_mdd_improve_pp"],
        "optimize_live": rec,
        "soft_keep": True,
        "broker": False,
        "path4_live": False,
    }
    decision_md = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: {generated[:10]} · Verdict: **`{pack_verdict}`** · "
            f"champion=**`{champion['arm']}`**",
            f"Register: **{REGISTER}** · base **{BASE_ID}**",
            "",
            "## Champion vs live",
            "",
            f"- held CAGR lift: **{champion['held_cagr_lift_pp']}** pp",
            f"- full CAGR lift: **{champion['full_cagr_lift_pp']}** pp",
            f"- sealed MDD improve: **{champion['sealed_mdd_improve_pp']}** pp",
            f"- tipY / tip1y: **{champion['tip_ytd_cagr_lift_pp']}** / "
            f"**{champion['tip_1y_cagr_lift_pp']}**",
            "",
            "## How to optimize live",
            "",
            *[f"{i+1}. {s}" for i, s in enumerate(rec)],
            "",
            f"Label: `{decision['label']}`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{DECISION_ID}.md",
        REP / f"{DECISION_ID}.md",
        decision_md,
        kind="decision pack",
    )
    (OPS / f"{DECISION_ID}.json").write_text(json.dumps(decision, indent=2) + "\n")
    write_repro_pointer(
        OPS / f"{DECISION_ID}.json", REP / f"{DECISION_ID}.json", kind="decision pack"
    )

    print(
        json.dumps(
            {
                "verdict": pack_verdict,
                "champion": champion["arm"],
                "held_cagr_lift_pp": champion["held_cagr_lift_pp"],
                "full_cagr_lift_pp": champion["full_cagr_lift_pp"],
                "sealed_mdd_improve_pp": champion["sealed_mdd_improve_pp"],
                "tip_ytd_cagr_lift_pp": champion["tip_ytd_cagr_lift_pp"],
                "tip_1y_cagr_lift_pp": champion["tip_1y_cagr_lift_pp"],
                "p3_within_verdict": None if not p3_only else p3_only["verdict_vs_live"],
                "p3_within_held": None if not p3_only else p3_only["held_cagr_lift_pp"],
                "p3_within_tipy": None if not p3_only else p3_only["tip_ytd_cagr_lift_pp"],
                "optimize_live": rec,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
