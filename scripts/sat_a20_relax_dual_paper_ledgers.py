#!/usr/bin/env python3
"""SAT_A20_RELAX dual-paper ledgers — OPERATING OBSERVE (paper only).

CTRL_LIVE_A10 (α=0.10) ∥ SAT_A20_RELAX (α=0.20 H=5 RET3) under COOL.
Soft-Frozen KEEP · COMPOSITE observe KEEP · no live α flip · cutover BLOCKED.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import cool_t50_inv_satellite_stagea as sat
import cool_t50_lev_short_assist_stagea as short
import e45_defend_handoff_stagea_screen as stagea
from e45_paper_harness import WINDOWS_STANDARD, window_stats
from live_config import LIVE_FUSE_SOFT_SELL_BOOST
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp
from sat_a20_relax_observe_helpers import (
    BASE_ALPHA,
    BASE_ID,
    CHAL_ALPHA,
    CHAL_ID,
    CONFIRM,
    HOLD_H,
    HUMAN_OPEN,
    OFF_CODE,
    STAGE_A_VERDICT,
    STATUS,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/sat-a20-relax-dual-paper-observe"
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
            out[wname] = {"mdd_improve_pp": None, "cagr_lift_pp": None, "gate": "INSUFFICIENT"}
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
            "cagr_lift_pp": None if gb is None else round(float(-float(gb)), 4),
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

    def _run(book_id: str, alpha: float):
        print(f"{book_id} α={alpha} ...", flush=True)
        sched, meta = short.build_schedule(
            tgt_live,
            cool,
            alpha=float(alpha),
            hold_h=int(HOLD_H),
            listed_from=listed_from,
            track="CONFIRM",
            confirm=CONFIRM,
            ret1=ret1,
            ret3=ret3,
            proxy=proxy,
            off_px=off_px,
        )
        nav, n_fills, _ = sat._sim(
            market,
            tgt_live,
            regime,
            dividends,
            scores=buy_live,
            buy_ok=buy_ok,
            sell=sell_live,
            schedule=sched,
        )
        return nav, sched, n_fills, meta

    base_nav, base_sched, n_base, _ = _run(BASE_ID, BASE_ALPHA)
    chal_nav, chal_sched, n_chal, _ = _run(CHAL_ID, CHAL_ALPHA)

    out_dir = OUT / "outputs"
    base_nav.to_csv(out_dir / "ctrl_live_a10_daily_nav.csv", index=False)
    chal_nav.to_csv(out_dir / "sat_a20_relax_daily_nav.csv", index=False)
    base_sched.to_csv(out_dir / "schedule_ctrl_live_a10.csv")
    chal_sched.to_csv(out_dir / "schedule_sat_a20_relax.csv")
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
    gb = cagr_delta_pp(base_w[held].get("cagr"), chal_w[held].get("cagr"), missing_as_zero=True)
    lift = None if gb is None else round(float(-float(gb)), 4)
    held_mdd = round(
        float(mdd_delta_pp(base_w[held].get("max_drawdown"), chal_w[held].get("max_drawdown"))),
        4,
    )

    payload = {
        "generated_at_utc": _utc(),
        "schema_version": "sat_a20_relax_dual_paper_observe_v1",
        "label": "SAT_A20_RELAX_DUAL_PAPER_OBSERVE_OPERATING",
        "status": STATUS,
        "human_open": HUMAN_OPEN,
        "live_wire": False,
        "cutover_authorized": False,
        "soft_frozen_keep": True,
        "live_conf_a10_keep": True,
        "composite_observe_keep": True,
        "base_id": BASE_ID,
        "challenger_id": CHAL_ID,
        "base_alpha": BASE_ALPHA,
        "chal_alpha": CHAL_ALPHA,
        "hold_h": HOLD_H,
        "confirm": CONFIRM,
        "stage_a_verdict": STAGE_A_VERDICT,
        "base_windows": base_w,
        "chal_windows": chal_w,
        "heldout_delta": {"cagr_lift_pp": lift, "mdd_improve_pp": held_mdd},
        "tip": tip,
        "n_fills_base": int(n_base) if isinstance(n_base, (int, float)) else None,
        "n_fills_chal": int(n_chal) if isinstance(n_chal, (int, float)) else None,
        "non_actions": [
            "Soft-Frozen KEEP",
            "COMPOSITE COMP_H150_x_A20 observe KEEP (parallel tip-first track)",
            "Do not flip live CONF α to 0.20 from observe",
            "Cutover BLOCKED until dedicated ACCEPT",
        ],
    }
    md = "\n".join(
        [
            "# SAT_A20_RELAX dual-paper observe — OPERATING",
            "",
            f"- human_open: `{HUMAN_OPEN}`",
            f"- status: **{STATUS}** · live_wire: false · cutover: **BLOCKED** · Soft-Frozen KEEP · live CONF α=0.10 KEEP",
            f"- books: `{BASE_ID}` (α={BASE_ALPHA}) ∥ `{CHAL_ID}` (α={CHAL_ALPHA})",
            f"- Stage A: `{STAGE_A_VERDICT}` · COMPOSITE observe **KEEP**",
            f"- held-out: CAGR↑ {lift} pp · MDD↑ {held_mdd} pp",
            f"- tip ytd MDD↑ {tip.get('ytd', {}).get('mdd_improve_pp')} · tip 1y MDD↑ {tip.get('trailing_1y', {}).get('mdd_improve_pp')}",
            f"- tip ytd CAGR↑ {tip.get('ytd', {}).get('cagr_lift_pp')} · tip 1y CAGR↑ {tip.get('trailing_1y', {}).get('cagr_lift_pp')}",
            "",
            "## Non-actions",
            "",
            *[f"- {x}" for x in payload["non_actions"]],
            "",
            "Repro: `repro/sat-a20-relax-dual-paper-observe/`",
            "",
        ]
    )
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    (OUT / "reports" / "SAT_A20_RELAX_DUAL_PAPER_OBSERVE_OPERATING.json").write_text(
        text, encoding="utf-8"
    )
    (OUT / "reports" / "SAT_A20_RELAX_DUAL_PAPER_OBSERVE_OPERATING.md").write_text(
        md, encoding="utf-8"
    )
    (OPS / "SAT_A20_RELAX_DUAL_PAPER_OBSERVE_OPERATING.json").write_text(text, encoding="utf-8")
    (OPS / "SAT_A20_RELAX_DUAL_PAPER_OBSERVE_OPERATING.md").write_text(md, encoding="utf-8")
    (OPS / "SAT_A20_RELAX_DUAL_PAPER_OBSERVE.json").write_text(text, encoding="utf-8")
    (out_dir / "dual_paper_summary.json").write_text(text, encoding="utf-8")
    print(json.dumps({"status": STATUS, "cagr_lift_pp": lift, "mdd_pp": held_mdd}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
