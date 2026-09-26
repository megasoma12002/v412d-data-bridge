#!/usr/bin/env python3
"""00631L CONF_RET3_A10_H5 dual-paper ledgers — OPERATING OBSERVE (paper only).

BASE_LIVE_FUSE_COOL ∥ CONF_RET3_A10_H5 (COOL exit + 0050 RET3 confirm · α=0.10 · H=5).
Soft-Frozen KEEP · no live wire · cutover BLOCKED.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import cool_t50_inv_satellite_stagea as sat
import cool_t50_lev_rebound_stagea as reb
import cool_t50_lev_short_assist_stagea as short
import e45_defend_handoff_stagea_screen as stagea
from cool_631l_short_assist_observe_helpers import (
    ALPHA,
    BASE_ID,
    CHAL_ID,
    CONFIRM,
    HOLD_H,
    HUMAN_OPEN,
    OFF_CODE,
    STAGE_A_VERDICT,
    STATUS,
)
from e45_paper_harness import WINDOWS_STANDARD, window_stats
from live_config import LIVE_FUSE_SOFT_SELL_BOOST
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/cool-631l-short-assist-dual-paper-observe"
OPS = ROOT / "research/ops"
SELL_AMP = float(LIVE_FUSE_SOFT_SELL_BOOST)


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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
    asof = pd.Timestamp(pd.to_datetime(base_nav["date"]).max())
    b_dates = pd.to_datetime(base_nav["date"])
    c_dates = pd.to_datetime(chal_nav["date"])
    out = {}
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


def main() -> int:
    for d in (OUT / "outputs", OUT / "reports", OPS):
        d.mkdir(parents=True, exist_ok=True)

    sat.DEF_CODE = OFF_CODE
    sat.DEF_PRICE = ROOT / "data/def_proxies/00631L_ohlcv.csv"

    print("loading ...", flush=True)
    market0 = sat.load_market()
    dividends = sat.load_dividends()
    off = sat.load_inv_bars()
    market, listed_from = sat.attach_inv(market0, off)

    from e50_early_stack_combined_nav import FIN, e16_features
    from soft_assist_helpers import LIVE_KD
    from ta_indicator_catalog import build_low_high_catalog
    from within_sleeve_alloc import build_kd_season_tilt_scores, build_pre_exdiv_window_buy_ok

    _p, sleeve, _tgt, regime = e16_features(market0)
    cal = pd.DatetimeIndex(pd.to_datetime(market0["date"]).drop_duplicates().sort_values())
    lows, highs = build_low_high_catalog(market0, cal, list(FIN))
    kd = build_kd_season_tilt_scores(
        market0,
        dividends,
        FIN,
        k_thresh=float(LIVE_KD["k_thresh"]),
        season_start=LIVE_KD["season_start"],
        season_end=LIVE_KD["season_end"],
        pre_days=int(LIVE_KD["pre_days"]),
        active_score=float(LIVE_KD["active_score"]),
    )
    buy_ok = build_pre_exdiv_window_buy_ok(
        cal, dividends, FIN, pre_days=int(LIVE_KD["pre_days"]), also_stock_ex=True
    )
    buy_live = sat._buy(kd, lows)
    sell_live = sat._sell(highs, SELL_AMP)
    score_live = sat._sleeve_score(market0, sleeve, float(sat.LIVE_SLEEVE_ALPHA))
    tgt_live = sat._target_live(score_live, regime)

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
    nav_s = stagea._nav_series(fuse_off)
    feat = stagea._risk_features(market0, nav_s)
    proxy = feat["proxy_mdd63"].reindex(tgt_live.index).fillna(0.0)
    ret1, ret3 = short._0050_rets(market0, tgt_live.index)
    off_px = short._off_close(off, tgt_live.index)

    print(f"{BASE_ID} ...", flush=True)
    base_nav, n_base, _ = sat._sim(
        market0,
        tgt_live,
        regime,
        dividends,
        scores=buy_live,
        buy_ok=buy_ok,
        sell=sell_live,
        exposure=cool,
    )
    print(f"{CHAL_ID} ...", flush=True)
    sched, meta = short.build_schedule(
        tgt_live,
        cool,
        alpha=float(ALPHA),
        hold_h=int(HOLD_H),
        listed_from=listed_from,
        track="CONFIRM",
        confirm=CONFIRM,
        ret1=ret1,
        ret3=ret3,
        proxy=proxy,
        off_px=off_px,
    )
    chal_nav, n_chal, _ = sat._sim(
        market,
        tgt_live,
        regime,
        dividends,
        scores=buy_live,
        buy_ok=buy_ok,
        sell=sell_live,
        schedule=sched,
    )

    out_dir = OUT / "outputs"
    base_nav.to_csv(out_dir / "base_live_fuse_cool_daily_nav.csv", index=False)
    chal_nav.to_csv(out_dir / "conf_ret3_a10_h5_daily_nav.csv", index=False)
    sched.to_csv(out_dir / "schedule_conf_ret3_a10_h5.csv")
    compare = pd.DataFrame(
        {
            "date": pd.to_datetime(base_nav["date"]),
            "nav_base": base_nav["nav"].astype(float).to_numpy(),
            "nav_chal": chal_nav["nav"].astype(float).to_numpy(),
        }
    )
    compare.to_csv(out_dir / "dual_paper_nav_compare.csv", index=False)

    base_w = pack_windows(base_nav)
    chal_w = pack_windows(chal_nav)
    tip = tip_windows(base_nav, chal_nav)
    held = "heldout_2019_plus"
    sealed = "sealed_2023_plus"
    held_cagr_lift = cagr_delta_pp(base_w[held].get("cagr"), chal_w[held].get("cagr"), missing_as_zero=True)
    if held_cagr_lift is not None:
        held_cagr_lift = -float(held_cagr_lift)
    sealed_mdd = float(mdd_delta_pp(base_w[sealed].get("max_drawdown"), chal_w[sealed].get("max_drawdown")))
    held_mdd = float(mdd_delta_pp(base_w[held].get("max_drawdown"), chal_w[held].get("max_drawdown")))

    payload = {
        "generated_at_utc": _utc(),
        "schema_version": "cool_631l_short_assist_dual_paper_observe_v1",
        "status": STATUS,
        "live_wire": False,
        "cutover": "BLOCKED",
        "human_open": HUMAN_OPEN,
        "stage_a_verdict": STAGE_A_VERDICT,
        "base_id": BASE_ID,
        "chal_id": CHAL_ID,
        "off_code": OFF_CODE,
        "alpha": ALPHA,
        "hold_h": HOLD_H,
        "confirm": CONFIRM,
        "sell_amp": SELL_AMP,
        "listed_from": str(listed_from.date()),
        "n_fills_base": n_base,
        "n_fills_chal": n_chal,
        "schedule_meta": meta,
        "windows_base": base_w,
        "windows_chal": chal_w,
        "tip": tip,
        "held_cagr_lift_pp": None if held_cagr_lift is None else round(held_cagr_lift, 4),
        "held_mdd_improve_pp": round(held_mdd, 4),
        "sealed_mdd_improve_pp": round(sealed_mdd, 4),
        "soft_frozen_keep": True,
    }
    (OUT / "reports" / "COOL_631L_SHORT_ASSIST_DUAL_PAPER_OBSERVE.json").write_text(
        json.dumps(payload, indent=2) + "\n"
    )
    (OPS / "COOL_631L_SHORT_ASSIST_DUAL_PAPER_OBSERVE.json").write_text(
        json.dumps(payload, indent=2) + "\n"
    )
    (OPS / "COOL_631L_SHORT_ASSIST_DUAL_PAPER_OBSERVE_OPERATING.json").write_text(
        json.dumps({**payload, "status": "OPERATING_OBSERVE"}, indent=2) + "\n"
    )
    print(
        json.dumps(
            {
                "status": STATUS,
                "held_cagr_lift_pp": payload["held_cagr_lift_pp"],
                "sealed_mdd_improve_pp": payload["sealed_mdd_improve_pp"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
