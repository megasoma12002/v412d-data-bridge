#!/usr/bin/env python3
"""民股金控 Gate V7 — max CAGR × min MDD Stage A (paper only).

Charter: research/ops/PRIV_FINHC_CAGR_MDD_GATE_V7_CHARTER.md
Gated carve-out of Financial sleeve → FinPriv when gate opens.
Soft-Frozen live KEEP · no tip rewrite · no live wire.
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
import e50_early_stack_combined_nav as e50
from cool_c8_proxy_observe_helpers import build_cool_c8_exposure
from e16_private_fin_holdings_rescreen import PRIV_R3R4, PUB_R1, TEL, build_extended_market
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, window_stats
from portfolio_capital import DEFAULT_CAPITAL
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp
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
    FIN_EQUAL,
    FIN_PRE_EXDIV_KD,
    TEL_EQUAL,
    build_kd_season_tilt_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "priv-finhc-cagr-mdd-gate-v7-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "PRIV_FINHC_CAGR_MDD_GATE_V7_CHARTER"
SCREEN_ID = "PRIV_FINHC_CAGR_MDD_GATE_V7_STAGEA_SCREEN"
HELDOUT = "heldout_2019_plus"
SEALED = "sealed_2023_plus"
E22_VERSION = e22div.DEFAULT_BOOKS_VERSION
BASE_ID = "BASE_LIVE_FUSE_COOL"

CAGR_FLOOR_PP = 0.20
HELD_MDD_MIN_PP = -0.25
SEALED_MDD_MIN_PP = 0.0
TIP_MDD_TOL_PP = -0.5

PRIV_KD_MAY = {
    "id": "PRIV_KD_MAY_Klt25_T15",
    "season_start": (5, 1),
    "season_end": (5, 31),
    "k_thresh": 25.0,
    "pre_days": 15,
    "active_score": 1.5,
}

GATES = ("REG_BULL", "REG_BULL_SIDE", "MA60_0050", "MA120_0050", "RS60_PRIV_GT_PUB")
PRIV_FRACS = (0.05, 0.10, 0.15)
PRIV_POLS = ("EQUAL", "PRIV_KD_MAY")


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
            out[wname] = {"mdd_improve_pp": None, "cagr_giveback_pp": None, "gate": "INSUFFICIENT"}
            continue
        bn = b["nav"].astype(float) / float(b["nav"].iloc[0])
        cn = c["nav"].astype(float) / float(c["nav"].iloc[0])
        b_mdd = float((bn / bn.cummax() - 1.0).min())
        c_mdd = float((cn / cn.cummax() - 1.0).min())
        years = (len(b) - 1) / 252.0
        bc = float(bn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        cc = float(cn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        gb = cagr_delta_pp(bc, cc)
        out[wname] = {
            "mdd_improve_pp": round(float(mdd_delta_pp(b_mdd, c_mdd)), 4),
            "cagr_giveback_pp": None if gb is None else round(float(gb), 4),
            "gate": "PASS",
        }
    return out


def _buy(kd, lows, k9_amp: float = 1.0) -> pd.DataFrame:
    out = soft_boost_scores(kd, lows[BUY_LOW_ID], 1.0)
    return soft_boost_scores(out, lows["K9_LT30"], float(k9_amp))


def _sell(highs, amp: float = 0.50) -> pd.DataFrame:
    return soft_sell_panel(highs[SELL_HIGH_ID], boost=float(amp))


def _sleeve_score(market, sleeve, alpha: float) -> pd.DataFrame:
    _p, _s, _t, _r, base_score = soft.build_soft_frozen_targets(market)
    tilt = sleeve_signal_panel(sleeve, "rsi_lt30", 14)
    return base_score + float(alpha) * tilt


def _target_live(score: pd.DataFrame, regime: pd.Series) -> pd.DataFrame:
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


def _ew_ret(prices: pd.DataFrame, codes: list[str], win: int = 60) -> pd.Series:
    sub = prices[codes].astype(float)
    r = sub.pct_change(win, fill_method=None).mean(axis=1)
    return r


def build_gates(prices: pd.DataFrame, regime: pd.Series) -> dict[str, pd.Series]:
    idx = prices.index
    rg = regime.reindex(idx).ffill()
    px50 = prices["0050"].astype(float)
    ma60 = px50.rolling(60, min_periods=60).mean()
    ma120 = px50.rolling(120, min_periods=120).mean()
    rs_priv = _ew_ret(prices, list(PRIV_R3R4), 60)
    rs_pub = _ew_ret(prices, list(PUB_R1), 60)
    return {
        "REG_BULL": (rg == "Bull").astype(float),
        "REG_BULL_SIDE": rg.isin(["Bull", "Sideways"]).astype(float),
        "MA60_0050": (px50 > ma60).astype(float),
        "MA120_0050": (px50 > ma120).astype(float),
        "RS60_PRIV_GT_PUB": (rs_priv > rs_pub).astype(float),
        "ALWAYS": pd.Series(1.0, index=idx),
        "NEVER": pd.Series(0.0, index=idx),
    }


def to_four_sleeve(target3: pd.DataFrame, gate: pd.Series, priv_frac: float) -> pd.DataFrame:
    """Carve FinPriv from Financial when gate=1; TEL/0050 unchanged."""
    g = gate.reindex(target3.index).fillna(0.0).astype(float).clip(0.0, 1.0)
    f = float(priv_frac)
    fin = target3["Financial"].astype(float)
    priv = fin * g * f
    pub = fin - priv
    out = pd.DataFrame(
        {
            "FinPub": pub,
            "FinPriv": priv,
            "Telecom": target3["Telecom"].astype(float),
            "0050": target3["0050"].astype(float),
        },
        index=target3.index,
    )
    return out


def scale_schedule(four: pd.DataFrame, cool: pd.Series) -> pd.DataFrame:
    """Apply COOL as equity scale (sum < 1 → residual cash)."""
    c = cool.reindex(four.index).fillna(1.0).astype(float).clip(0.0, 1.0)
    return four.mul(c, axis=0)


def _sim_three(market, target, regime, dividends, *, scores, buy_ok, sell, exposure):
    nav, fills, meta = e50.simulate_core(
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
        fin_buy_ok=buy_ok,
        fin_sell_scores=sell,
        e45_exposure=exposure.astype(float),
        e22_version=E22_VERSION,
    )
    if not bool(meta.get("exact_t1_ok")):
        raise RuntimeError("exact_t1_ok failed (3-sleeve)")
    return nav, int(len(fills)), meta


def _sim_four(
    market,
    schedule,
    regime,
    dividends,
    *,
    pub_scores,
    priv_scores,
    buy_ok,
    sell,
    priv_policy: str,
):
    fin_codes = list(PUB_R1) + list(PRIV_R3R4)
    old_fin, old_all = list(e50.FIN), list(e50.ALL)
    e50.FIN = fin_codes
    e50.ALL = fin_codes + list(TEL) + ["0050"]
    try:
        combined = pub_scores.copy()
        for c in PRIV_R3R4:
            if c in priv_scores.columns:
                combined[c] = priv_scores[c]
        scores = combined if priv_policy == "PRIV_KD_MAY" else pub_scores
        priv_alloc = FIN_EQUAL if priv_policy == "EQUAL" else FIN_PRE_EXDIV_KD
        # Target columns overridden by sleeve_weight_schedule each day.
        tgt = schedule.copy()
        nav, fills, meta = e50.simulate_core(
            market,
            tgt,
            regime,
            dividends,
            apply_e22=True,
            apply_stock_div=True,
            capital=float(DEFAULT_CAPITAL),
            lot_size=int(BOARD_LOT),
            financial_alloc=FIN_PRE_EXDIV_KD,
            telecom_alloc=TEL_EQUAL,
            fin_name_scores=scores,
            fin_buy_ok=buy_ok,
            fin_sell_scores=sell,
            fin_pub_codes=list(PUB_R1),
            fin_priv_codes=list(PRIV_R3R4),
            fin_pub_alloc=FIN_PRE_EXDIV_KD,
            fin_priv_alloc=priv_alloc,
            sleeve_weight_schedule=schedule,
            e22_version=E22_VERSION,
        )
        if not bool(meta.get("exact_t1_ok")):
            raise RuntimeError("exact_t1_ok failed (4-sleeve)")
        return nav, int(len(fills)), meta
    finally:
        e50.FIN = old_fin
        e50.ALL = old_all


def _score_row(base_w, chal_w, tip, *, rid, gate, frac, pol, n_fills, mean_priv, gate_on_frac):
    h = chal_w[HELDOUT]
    s = chal_w[SEALED]
    bh = base_w[HELDOUT]
    bs = base_w[SEALED]
    held_cagr_lift = cagr_delta_pp(bh.get("cagr"), h.get("cagr"), missing_as_zero=True)
    # cagr_delta_pp(base, chal) as giveback: negative ⇒ chal higher. Flip to lift.
    if held_cagr_lift is not None:
        held_cagr_lift = -float(held_cagr_lift)
    sealed_cagr_lift = cagr_delta_pp(bs.get("cagr"), s.get("cagr"), missing_as_zero=True)
    if sealed_cagr_lift is not None:
        sealed_cagr_lift = -float(sealed_cagr_lift)
    held_mdd_up = float(mdd_delta_pp(bh.get("max_drawdown"), h.get("max_drawdown")))
    sealed_mdd_up = float(mdd_delta_pp(bs.get("max_drawdown"), s.get("max_drawdown")))
    tip_clean = tip.get("ytd", {}).get("gate") == "PASS" and tip.get("trailing_1y", {}).get("gate") == "PASS"
    tip_mdd_ok = tip_clean and float(tip["ytd"].get("mdd_improve_pp") or -9) >= TIP_MDD_TOL_PP and float(
        tip["trailing_1y"].get("mdd_improve_pp") or -9
    ) >= TIP_MDD_TOL_PP
    gates = {
        "tip_clean": bool(tip_clean),
        "tip_mdd_ok": bool(tip_mdd_ok),
        "sealed_mdd": sealed_mdd_up >= SEALED_MDD_MIN_PP,
        "held_mdd": held_mdd_up >= HELD_MDD_MIN_PP,
        "held_cagr_floor": held_cagr_lift is not None and held_cagr_lift >= CAGR_FLOOR_PP,
    }
    coexist = all(gates.values())
    score = (
        0.50 * ((held_cagr_lift or 0.0) + (sealed_cagr_lift or 0.0))
        + 0.50 * (held_mdd_up + sealed_mdd_up)
        - 0.25 * max(0.0, -(held_cagr_lift or 0.0))
    )
    return {
        "id": rid,
        "gate": gate,
        "priv_frac": frac,
        "priv_policy": pol,
        "n_fills": n_fills,
        "mean_finpriv": round(float(mean_priv), 6),
        "gate_on_frac": round(float(gate_on_frac), 6),
        "windows": chal_w,
        "held_cagr_lift_pp": None if held_cagr_lift is None else round(held_cagr_lift, 4),
        "sealed_cagr_lift_pp": None if sealed_cagr_lift is None else round(sealed_cagr_lift, 4),
        "held_mdd_improve_pp": round(held_mdd_up, 4),
        "sealed_mdd_improve_pp": round(sealed_mdd_up, 4),
        "tip": tip,
        "gates": gates,
        "coexist": bool(coexist),
        "score": round(float(score), 4),
    }


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.8]
    assert list(soft.FIN) == list(PUB_R1)

    print("loading extended market ...", flush=True)
    market = build_extended_market()
    dividends = load_dividends()
    # Soft-Frozen features from 公股-only panel columns present in extended market.
    _p, sleeve, _tgt, regime = e50.e16_features(market)
    prices = (
        market.pivot(index="date", columns="code", values="adj_close")
        .sort_index()
        .ffill()
    )
    cal = pd.DatetimeIndex(pd.to_datetime(market["date"]).drop_duplicates().sort_values())
    all_fin = list(PUB_R1) + list(PRIV_R3R4)
    lows, highs = build_low_high_catalog(market, cal, all_fin)

    pub_kd = build_kd_season_tilt_scores(
        market,
        dividends,
        list(PUB_R1),
        k_thresh=float(LIVE_KD["k_thresh"]),
        season_start=LIVE_KD["season_start"],
        season_end=LIVE_KD["season_end"],
        pre_days=int(LIVE_KD["pre_days"]),
        active_score=float(LIVE_KD["active_score"]),
    )
    priv_kd = build_kd_season_tilt_scores(
        market,
        dividends,
        list(PRIV_R3R4),
        k_thresh=float(PRIV_KD_MAY["k_thresh"]),
        season_start=PRIV_KD_MAY["season_start"],
        season_end=PRIV_KD_MAY["season_end"],
        pre_days=int(PRIV_KD_MAY["pre_days"]),
        active_score=float(PRIV_KD_MAY["active_score"]),
    )
    buy_ok = build_pre_exdiv_window_buy_ok(
        cal, dividends, all_fin, pre_days=int(LIVE_KD["pre_days"]), also_stock_ex=True
    )
    buy_live = _buy(pub_kd, lows)
    sell_live = _sell(highs)
    score_live = _sleeve_score(market, sleeve, float(LIVE_SLEEVE_ALPHA))
    tgt_live = _target_live(score_live, regime)

    print("offense NAV for cool ...", flush=True)
    # 3-sleeve offense uses PUB-only FIN universe
    old_fin, old_all = list(e50.FIN), list(e50.ALL)
    e50.FIN = list(PUB_R1)
    e50.ALL = list(PUB_R1) + list(TEL) + ["0050"]
    try:
        fuse_off, _, _ = _sim_three(
            market,
            tgt_live,
            regime,
            dividends,
            scores=buy_live,
            buy_ok=buy_ok,
            sell=sell_live,
            exposure=pd.Series(1.0, index=tgt_live.index),
        )
        cool = _cool_from_offense(market, fuse_off)
        cool.to_frame("cool_exposure").to_csv(OUT / "exposure_cool_from_fuse.csv")

        print(f"{BASE_ID} ...", flush=True)
        base_nav, n_base, _ = _sim_three(
            market,
            tgt_live,
            regime,
            dividends,
            scores=buy_live,
            buy_ok=buy_ok,
            sell=sell_live,
            exposure=cool,
        )
    finally:
        e50.FIN = old_fin
        e50.ALL = old_all

    base_nav.to_csv(OUT / f"nav_{BASE_ID}.csv", index=False)
    base_w = _pack(base_nav)

    gates = build_gates(prices, regime)
    books: list[tuple[str, str, float, str]] = []
    books.append((BASE_ID, "NEVER", 0.0, "EQUAL"))
    books.append(("ALWAYS_F10_EQ", "ALWAYS", 0.10, "EQUAL"))
    for g in GATES:
        for frac in PRIV_FRACS:
            for pol in PRIV_POLS:
                tag = "EQ" if pol == "EQUAL" else "KDMAY"
                books.append((f"V7_{g}_F{int(frac*100):02d}_{tag}", g, float(frac), pol))

    rows = []
    for i, (bid, gid, frac, pol) in enumerate(books, 1):
        print(f"  [{i}/{len(books)}] {bid} ...", flush=True)
        if bid == BASE_ID:
            tip = _tip(base_nav, base_nav)
            row = _score_row(
                base_w,
                base_w,
                tip,
                rid=bid,
                gate=gid,
                frac=frac,
                pol=pol,
                n_fills=n_base,
                mean_priv=0.0,
                gate_on_frac=0.0,
            )
            row["coexist"] = False  # control
            row["is_control"] = True
            rows.append(row)
            continue

        gate = gates[gid]
        four = to_four_sleeve(tgt_live, gate, frac)
        sched = scale_schedule(four, cool)
        mean_priv = float(four["FinPriv"].mean())
        gate_on = float((gate.fillna(0) > 0).mean())
        nav, n_fills, _ = _sim_four(
            market,
            sched,
            regime,
            dividends,
            pub_scores=buy_live,
            priv_scores=priv_kd,
            buy_ok=buy_ok,
            sell=sell_live,
            priv_policy=pol,
        )
        nav.to_csv(OUT / f"nav_{bid}.csv", index=False)
        chal_w = _pack(nav)
        tip = _tip(base_nav, nav)
        row = _score_row(
            base_w,
            chal_w,
            tip,
            rid=bid,
            gate=gid,
            frac=frac,
            pol=pol,
            n_fills=n_fills,
            mean_priv=mean_priv,
            gate_on_frac=gate_on,
        )
        row["is_control"] = bid.startswith("ALWAYS")
        rows.append(row)

    chal_rows = [r for r in rows if r["id"] != BASE_ID]
    hits = [r for r in chal_rows if r.get("coexist")]
    hits_sorted = sorted(hits, key=lambda r: -float(r["score"]))
    soft_hits = [
        r
        for r in chal_rows
        if r["gates"]["sealed_mdd"]
        and r["gates"]["held_mdd"]
        and r["gates"]["tip_mdd_ok"]
        and not r["gates"]["held_cagr_floor"]
    ]
    if hits:
        verdict = "PRIV_FINHC_HIT"
    elif soft_hits:
        verdict = "PRIV_FINHC_SOFT"
    elif any(r["gates"]["tip_clean"] for r in chal_rows):
        verdict = "MDD_BLOCK"
    else:
        verdict = "NO_LIFT"

    payload = {
        "generated_at_utc": _utc(),
        "label": SCREEN_ID,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "status": verdict,
        "live_wire": False,
        "soft_frozen_keep": True,
        "baseline": BASE_ID,
        "baseline_windows": base_w,
        "n_challengers": len(chal_rows),
        "n_coexist": len(hits),
        "coexist_ids": [r["id"] for r in hits_sorted],
        "best": hits_sorted[0] if hits_sorted else (sorted(chal_rows, key=lambda r: -float(r["score"]))[0] if chal_rows else None),
        "ranked": sorted(chal_rows, key=lambda r: -float(r["score"])),
        "controls": [r for r in rows if r["id"] == BASE_ID or r.get("is_control")],
    }
    # Drop nested nav-sized tip noise for JSON size — tip already compact.
    (REP / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2) + "\n")
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2) + "\n")

    lines = [
        f"# 民股金控 Gate V7 — Stage A Screen",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Status: **{verdict}** · baseline `{BASE_ID}` · Soft-Frozen **KEEP** · live wire **false**",
        f"Charter: `{CHARTER_ID}.md`",
        "",
        f"Coexist / HIT: **{len(hits)}** / {len(chal_rows)}",
        "",
        "## Ranked (by score)",
        "",
        "| book | gate | frac | pol | CAGR↑ held | CAGR↑ seal | MDD↑ held | MDD↑ seal | tip | coexist |",
        "|---|---|---:|---|---:|---:|---:|---:|---|---|",
    ]
    for r in payload["ranked"][:25]:
        tip_ok = "Y" if r["gates"]["tip_mdd_ok"] else "N"
        lines.append(
            f"| `{r['id']}` | {r['gate']} | {r['priv_frac']:.2f} | {r['priv_policy']} | "
            f"{r['held_cagr_lift_pp']:+.2f} | {r['sealed_cagr_lift_pp']:+.2f} | "
            f"{r['held_mdd_improve_pp']:+.2f} | {r['sealed_mdd_improve_pp']:+.2f} | "
            f"{tip_ok} | {'Y' if r['coexist'] else 'N'} |"
        )
    lines += [
        "",
        "## Binding",
        "",
        "1. Soft-Frozen live membership stays **公股 R1** until Class D ACCEPT.",
        "2. Even HIT → paper observe ballot only.",
        "3. Do not retune N1–V6 / dollar-split / SF4 clip grids from this screen.",
        "",
        f"Repro: `PYTHONPATH=scripts python3 scripts/priv_finhc_cagr_mdd_gate_v7_stagea.py`",
        "",
        f"Label: `{SCREEN_ID}_{payload['generated_at_utc'][:10]}__{verdict}`",
        "",
    ]
    md = "\n".join(lines)
    (REP / f"{SCREEN_ID}.md").write_text(md)
    (OPS / f"{SCREEN_ID}.md").write_text(md)

    decision = {
        "label": "PRIV_FINHC_CAGR_MDD_GATE_V7_DECISION",
        "generated_at_utc": _utc(),
        "status": verdict,
        "live_wire": False,
        "n_coexist": len(hits),
        "coexist_ids": [r["id"] for r in hits_sorted],
        "best": hits_sorted[0]["id"] if hits_sorted else None,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "stage_a": f"research/ops/{SCREEN_ID}.md",
    }
    dlines = [
        "# 民股金控 Gate V7 — Decision Pack (Stage A)",
        "",
        f"Date: 2026-09-25 · Generated `{decision['generated_at_utc']}`",
        f"Status: **{verdict}** · Soft-Frozen **KEEP** · live wire **false**",
        "",
        "## Verdict",
        "",
        f"Coexist books: **{len(hits)}**.",
        "",
    ]
    if hits_sorted:
        b = hits_sorted[0]
        dlines += [
            f"Best: `{b['id']}` · score **{b['score']:+.3f}** · "
            f"held CAGR↑ {b['held_cagr_lift_pp']:+.2f} · sealed MDD↑ {b['sealed_mdd_improve_pp']:+.2f}",
            "",
            "Next: dual-paper observe ballot (Stage B) — not live.",
            "",
        ]
    else:
        dlines += [
            "No coexist under predeclared max-CAGR / min-MDD gates.",
            "",
            "Binding: Soft-Frozen 公股 R1 KEEP · reopen only with new mechanism or human objective change.",
            "",
        ]
    dlines += [
        f"Label: `PRIV_FINHC_CAGR_MDD_GATE_V7_DECISION_2026-09-25__{verdict}`",
        "",
    ]
    (OPS / "PRIV_FINHC_CAGR_MDD_GATE_V7_DECISION_PACK.json").write_text(
        json.dumps(decision, indent=2) + "\n"
    )
    (OPS / "PRIV_FINHC_CAGR_MDD_GATE_V7_DECISION_PACK.md").write_text("\n".join(dlines))
    print(json.dumps({"verdict": verdict, "n_coexist": len(hits)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
