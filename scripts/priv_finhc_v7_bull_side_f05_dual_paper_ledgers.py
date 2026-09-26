#!/usr/bin/env python3
"""民股 Gate V7 Bull+Side F05 dual-paper ledgers — OPERATING OBSERVE (paper only).

BASE_LIVE_FUSE_COOL ∥ V7_REG_BULL_SIDE_F05_KDMAY under frozen COOL.
Soft-Frozen 公股 R1 KEEP · no live wire · cutover BLOCKED.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

import e16_soft_frozen_base as soft
import e45_defend_handoff_stagea_screen as stagea
import e50_early_stack_combined_nav as e50
import priv_finhc_cagr_mdd_gate_v7_stagea as v7
from cool_c8_proxy_observe_helpers import build_cool_c8_exposure
from e16_private_fin_holdings_rescreen import PRIV_R3R4, PUB_R1, TEL, build_extended_market
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, window_stats
from portfolio_capital import DEFAULT_CAPITAL
from priv_finhc_v7_observe_helpers import (
    BASE_ID,
    CHAL_ID,
    GATE_ID,
    HUMAN_OPEN,
    NEAR_FLAT_NOTE,
    PRIV_FRAC,
    PRIV_POLICY,
    STAGE_A_VERDICT,
    STATUS,
)
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp
from soft_assist_helpers import LIVE_KD
from ta_indicator_catalog import build_low_high_catalog
from tw_share_lots import BOARD_LOT
from within_sleeve_alloc import build_kd_season_tilt_scores, build_pre_exdiv_window_buy_ok

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/priv-finhc-v7-bull-side-f05-dual-paper-observe"
OPS = ROOT / "research/ops"
CAPITAL = float(DEFAULT_CAPITAL)
LOT = int(BOARD_LOT)


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def held_score(base_stats: dict, chal_stats: dict) -> dict:
    mdd_pp = mdd_delta_pp(base_stats.get("max_drawdown"), chal_stats.get("max_drawdown"))
    cagr_pp = cagr_delta_pp(
        base_stats.get("cagr"), chal_stats.get("cagr"), missing_as_zero=True
    )
    giveback = abs(float(cagr_pp)) if cagr_pp is not None else 9.0
    return {
        "mdd_improve_pp": float(mdd_pp),
        "cagr_giveback_pp": float(cagr_pp) if cagr_pp is not None else None,
        "cagr_lift_pp": None if cagr_pp is None else float(-float(cagr_pp)),
        "score": float(mdd_pp) - 0.5 * giveback,
    }


def pack_windows(nav: pd.DataFrame) -> dict:
    out = {}
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


def tip_windows(base_nav: pd.DataFrame, chal_nav: pd.DataFrame) -> dict:
    return v7._tip(base_nav, chal_nav)


def main() -> int:
    for d in (OUT / "outputs", OUT / "reports", OPS):
        d.mkdir(parents=True, exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.8]
    assert list(soft.FIN) == list(PUB_R1)

    print("loading extended market ...", flush=True)
    market = build_extended_market()
    dividends = load_dividends()
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
        k_thresh=float(v7.PRIV_KD_MAY["k_thresh"]),
        season_start=v7.PRIV_KD_MAY["season_start"],
        season_end=v7.PRIV_KD_MAY["season_end"],
        pre_days=int(v7.PRIV_KD_MAY["pre_days"]),
        active_score=float(v7.PRIV_KD_MAY["active_score"]),
    )
    buy_ok = build_pre_exdiv_window_buy_ok(
        cal, dividends, all_fin, pre_days=int(LIVE_KD["pre_days"]), also_stock_ex=True
    )
    buy_live = v7._buy(pub_kd, lows)
    sell_live = v7._sell(highs)
    score_live = v7._sleeve_score(market, sleeve, float(v7.LIVE_SLEEVE_ALPHA))
    tgt_live = v7._target_live(score_live, regime)

    print("offense NAV for cool ...", flush=True)
    old_fin, old_all = list(e50.FIN), list(e50.ALL)
    e50.FIN = list(PUB_R1)
    e50.ALL = list(PUB_R1) + list(TEL) + ["0050"]
    try:
        fuse_off, _, _ = v7._sim_three(
            market,
            tgt_live,
            regime,
            dividends,
            scores=buy_live,
            buy_ok=buy_ok,
            sell=sell_live,
            exposure=pd.Series(1.0, index=tgt_live.index),
        )
        cool = v7._cool_from_offense(market, fuse_off)
        cool.to_frame("cool_exposure").to_csv(OUT / "outputs/exposure_cool_from_fuse.csv")

        print(f"{BASE_ID} ...", flush=True)
        base_nav, n_base, meta_b = v7._sim_three(
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

    base_nav.to_csv(OUT / "outputs/base_live_fuse_cool_daily_nav.csv", index=False)
    tgt_live.to_csv(OUT / "outputs/base_targets.csv")

    gates = v7.build_gates(prices, regime)
    gate = gates[GATE_ID]
    four = v7.to_four_sleeve(tgt_live, gate, float(PRIV_FRAC))
    sched = v7.scale_schedule(four, cool)
    sched.to_csv(OUT / "outputs/chal_sleeve_schedule.csv")

    print(f"{CHAL_ID} ...", flush=True)
    chal_nav, n_chal, meta_c = v7._sim_four(
        market,
        sched,
        regime,
        dividends,
        pub_scores=buy_live,
        priv_scores=priv_kd,
        buy_ok=buy_ok,
        sell=sell_live,
        priv_policy=PRIV_POLICY,
    )
    chal_nav.to_csv(OUT / "outputs/v7_bull_side_f05_kdmay_daily_nav.csv", index=False)

    # Compare frame
    b = base_nav.rename(columns={"nav": "nav_base"})[["date", "nav_base"]]
    c = chal_nav.rename(columns={"nav": "nav_chal"})[["date", "nav_chal"]]
    compare = b.merge(c, on="date", how="inner")
    compare["rel_chal_vs_base"] = compare["nav_chal"] / compare["nav_base"]
    compare.to_csv(OUT / "outputs/dual_paper_nav_compare.csv", index=False)

    win_base = pack_windows(base_nav)
    win_chal = pack_windows(chal_nav)
    held = held_score(win_base["heldout_2019_plus"], win_chal["heldout_2019_plus"])
    sealed = held_score(
        win_base.get("sealed_2023_plus") or {},
        win_chal.get("sealed_2023_plus") or {},
    )
    tip = tip_windows(base_nav, chal_nav)

    operating: dict[str, Any] = {
        "generated_at_utc": _utc(),
        "human_open": HUMAN_OPEN,
        "near_flat_note": NEAR_FLAT_NOTE,
        "status": STATUS,
        "live_wire": False,
        "cutover": "BLOCKED",
        "base_id": BASE_ID,
        "chal_id": CHAL_ID,
        "stage_a_verdict": STAGE_A_VERDICT,
        "gate": GATE_ID,
        "priv_frac": PRIV_FRAC,
        "priv_policy": PRIV_POLICY,
        "n_fills_base": n_base,
        "n_fills_chal": n_chal,
        "exact_t1_ok_base": bool(meta_b.get("exact_t1_ok")),
        "exact_t1_ok_chal": bool(meta_c.get("exact_t1_ok")),
        "mean_finpriv": round(float(four["FinPriv"].mean()), 6),
        "gate_on_frac": round(float((gate.fillna(0) > 0).mean()), 6),
        "windows_base": win_base,
        "windows_chal": win_chal,
        "heldout_2019_plus": held,
        "sealed_2023_plus": sealed,
        "tip": tip,
    }
    (OUT / "reports/PRIV_FINHC_V7_BULL_SIDE_F05_DUAL_PAPER_OBSERVE_OPERATING.json").write_text(
        json.dumps(operating, indent=2) + "\n"
    )
    (OPS / "PRIV_FINHC_V7_BULL_SIDE_F05_DUAL_PAPER_OBSERVE_OPERATING.json").write_text(
        json.dumps(operating, indent=2) + "\n"
    )
    (OPS / "PRIV_FINHC_V7_BULL_SIDE_F05_DUAL_PAPER_OBSERVE.json").write_text(
        json.dumps(operating, indent=2) + "\n"
    )

    md_lines = [
        "# 民股 Gate V7 Bull+Side F05 dual-paper observe — OPERATING",
        "",
        f"- human_open: `{HUMAN_OPEN}`",
        f"- near-flat: {NEAR_FLAT_NOTE}",
        f"- status: **{STATUS}** · live_wire: false · cutover: **BLOCKED**",
        f"- books: `{BASE_ID}` ∥ `{CHAL_ID}`",
        f"- Stage A: `{STAGE_A_VERDICT}`",
        f"- gate `{GATE_ID}` · priv_frac {PRIV_FRAC} · policy `{PRIV_POLICY}`",
        f"- held-out: CAGR lift {held.get('cagr_lift_pp')} pp · MDD↑ {held.get('mdd_improve_pp')} pp",
        f"- sealed: CAGR lift {sealed.get('cagr_lift_pp')} pp · MDD↑ {sealed.get('mdd_improve_pp')} pp",
        f"- tip ytd MDD↑ {tip.get('ytd', {}).get('mdd_improve_pp')} · tip 1y MDD↑ {tip.get('trailing_1y', {}).get('mdd_improve_pp')}",
        "",
        "## Non-actions",
        "",
        "- Soft-Frozen 公股 R1 KEEP — no Class D FinPriv expand from observe",
        "- No tip history rewrite",
        "- Cutover BLOCKED until dedicated ACCEPT",
        "",
        f"Repro: `repro/priv-finhc-v7-bull-side-f05-dual-paper-observe/`",
        "",
    ]
    md = "\n".join(md_lines)
    (OUT / "reports/PRIV_FINHC_V7_BULL_SIDE_F05_DUAL_PAPER_OBSERVE_OPERATING.md").write_text(md)
    (OUT / "PRIV_FINHC_V7_BULL_SIDE_F05_DUAL_PAPER_OBSERVE_OPERATING.md").write_text(md)
    (OPS / "PRIV_FINHC_V7_BULL_SIDE_F05_DUAL_PAPER_OBSERVE_OPERATING.md").write_text(md)

    print(
        json.dumps(
            {
                "status": STATUS,
                "held_cagr_lift_pp": held.get("cagr_lift_pp"),
                "held_mdd_improve_pp": held.get("mdd_improve_pp"),
                "sealed_mdd_improve_pp": sealed.get("mdd_improve_pp"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
