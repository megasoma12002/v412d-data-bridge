#!/usr/bin/env python3
"""FIN×SAT COMPOSITE dual-paper ledgers — OPERATING OBSERVE (paper only).

CTRL_LIVE_A10 (live CONF α=0.10) ∥ COMP_H150_x_A20 (OR_K9 × HARD150 × CONF α=0.20 H=5).
Soft-Frozen KEEP · SELL_a75 KEEP · Exact T+1 KEEP · COOL_c8 KEEP · no live wire.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from stagea_screen_helpers import (
    utc_now_z as _utc,
    pack_nav_windows as pack_windows,
    tip_lift,
)

def tip_windows(base_nav, chal_nav):
    """Dual-paper tip pack (cagr_lift_pp + gate)."""
    return tip_lift(base_nav, chal_nav, include_gate=True)

import cool_t50_inv_satellite_stagea as sat
import cool_t50_lev_short_assist_stagea as short
import e16_clip_search_challenger as clip
import e16_soft_frozen_base as soft
import e22_dividend_accounting as e22div
import e45_defend_handoff_stagea_screen as stagea
from cool_c8_proxy_observe_helpers import build_cool_c8_exposure
from e50_early_stack_combined_nav import FIN, e16_features, simulate_core
from fin_buy_quality_helpers import (
    and_buy_ok,
    below_ma_ok,
    catalog_gate,
    not_gate,
    or_buy_ok,
    raw_close_panel,
)
from fin_sat_composite_observe_helpers import (
    BASE_ALPHA,
    BASE_ID,
    BUY_OVERLAY,
    CHAL_ALPHA,
    CHAL_ID,
    CONFIRM,
    HOLD_H,
    HUMAN_OPEN,
    OFF_CODE,
    SELL_OVERLAY,
    STAGE_A_VERDICT,
    STATUS,
)
from fin_sell_quality_helpers import cagr_lift_pp
from live_config import LIVE_FUSE_SOFT_SELL_BOOST
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
OUT = ROOT / "repro/fin-sat-composite-dual-paper-observe"
OPS = ROOT / "research/ops"
E22_VERSION = e22div.DEFAULT_BOOKS_VERSION
SELL_AMP = float(LIVE_FUSE_SOFT_SELL_BOOST)

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

def _sim(market, target, regime, dividends, *, scores, buy_ok, sell, schedule, sell_ok=None):
    kw = {
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

def main() -> int:
    for d in (OUT / "outputs", OUT / "reports", OPS):
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

    extra = or_buy_ok(catalog_gate(lows["BELOW_MA120"]), catalog_gate(lows["K9_LT30"]))
    chal_buy = and_buy_ok(base_buy_ok, extra)
    sell_ok = not_gate(below_ma_ok(raw, 150))

    def _run(book_id: str, alpha: float, buy_ok, sell_ok_panel):
        print(f"{book_id} α={alpha} ...", flush=True)
        sched, _meta = short.build_schedule(
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
        nav, fills, _ = _sim(
            market,
            tgt_live,
            regime,
            dividends,
            scores=scores,
            buy_ok=buy_ok,
            sell=sell0,
            schedule=sched,
            sell_ok=sell_ok_panel,
        )
        return nav, sched, fills

    base_nav, base_sched, base_fills = _run(BASE_ID, BASE_ALPHA, base_buy_ok, None)
    chal_nav, chal_sched, chal_fills = _run(CHAL_ID, CHAL_ALPHA, chal_buy, sell_ok)

    out_dir = OUT / "outputs"
    base_nav.to_csv(out_dir / "ctrl_live_a10_daily_nav.csv", index=False)
    chal_nav.to_csv(out_dir / "comp_h150_x_a20_daily_nav.csv", index=False)
    base_sched.to_csv(out_dir / "schedule_ctrl_live_a10.csv")
    chal_sched.to_csv(out_dir / "schedule_comp_h150_x_a20.csv")
    base_fills.to_csv(out_dir / "ctrl_live_a10_fills.csv", index=False)
    chal_fills.to_csv(out_dir / "comp_h150_x_a20_fills.csv", index=False)
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
    lift = cagr_lift_pp(base_w[held].get("cagr"), chal_w[held].get("cagr"))
    lift = None if lift is None else round(float(lift), 4)
    held_mdd = round(
        float(mdd_delta_pp(base_w[held].get("max_drawdown"), chal_w[held].get("max_drawdown"))),
        4,
    )

    payload = {
        "generated_at_utc": _utc(),
        "schema_version": "fin_sat_composite_dual_paper_observe_v1",
        "label": "FIN_SAT_COMPOSITE_DUAL_PAPER_OBSERVE_OPERATING",
        "status": STATUS,
        "human_open": HUMAN_OPEN,
        "live_wire": False,
        "cutover_authorized": False,
        "soft_frozen_keep": True,
        "sell_a75_keep": True,
        "live_conf_a10_keep": True,
        "base_id": BASE_ID,
        "challenger_id": CHAL_ID,
        "base_alpha": BASE_ALPHA,
        "chal_alpha": CHAL_ALPHA,
        "hold_h": HOLD_H,
        "confirm": CONFIRM,
        "buy_overlay": BUY_OVERLAY,
        "sell_overlay": SELL_OVERLAY,
        "stage_a_verdict": STAGE_A_VERDICT,
        "base_windows": base_w,
        "chal_windows": chal_w,
        "heldout_delta": {"cagr_lift_pp": lift, "mdd_improve_pp": held_mdd},
        "tip": tip,
        "n_fills_base": int(len(base_fills)),
        "n_fills_chal": int(len(chal_fills)),
        "non_actions": [
            "Soft-Frozen KEEP — no Class D from observe",
            "SELL_a75 KEEP · live CONF α=0.10 KEEP",
            "Do not Gate-H Soft×Sleeve fuse",
            "Cutover BLOCKED until dedicated ACCEPT",
        ],
    }
    md = "\n".join(
        [
            "# FIN×SAT COMPOSITE dual-paper observe — OPERATING",
            "",
            f"- human_open: `{HUMAN_OPEN}`",
            f"- status: **{STATUS}** · live_wire: false · cutover: **BLOCKED** · Soft-Frozen KEEP · SELL_a75 KEEP · live CONF α=0.10 KEEP",
            f"- books: `{BASE_ID}` (α={BASE_ALPHA}) ∥ `{CHAL_ID}` (α={CHAL_ALPHA} · {BUY_OVERLAY}×{SELL_OVERLAY})",
            f"- Stage A: `{STAGE_A_VERDICT}`",
            f"- held-out: CAGR↑ {lift} pp · MDD↑ {held_mdd} pp",
            f"- tip ytd MDD↑ {tip.get('ytd', {}).get('mdd_improve_pp')} · tip 1y MDD↑ {tip.get('trailing_1y', {}).get('mdd_improve_pp')}",
            "",
            "## Non-actions",
            "",
            *[f"- {x}" for x in payload["non_actions"]],
            "",
            "Repro: `repro/fin-sat-composite-dual-paper-observe/`",
            "",
        ]
    )
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    (OUT / "reports" / "FIN_SAT_COMPOSITE_DUAL_PAPER_OBSERVE_OPERATING.json").write_text(
        text, encoding="utf-8"
    )
    (OUT / "reports" / "FIN_SAT_COMPOSITE_DUAL_PAPER_OBSERVE_OPERATING.md").write_text(
        md, encoding="utf-8"
    )
    (OPS / "FIN_SAT_COMPOSITE_DUAL_PAPER_OBSERVE_OPERATING.json").write_text(text, encoding="utf-8")
    (OPS / "FIN_SAT_COMPOSITE_DUAL_PAPER_OBSERVE_OPERATING.md").write_text(md, encoding="utf-8")
    (OPS / "FIN_SAT_COMPOSITE_DUAL_PAPER_OBSERVE.json").write_text(text, encoding="utf-8")
    (out_dir / "dual_paper_summary.json").write_text(text, encoding="utf-8")
    print(json.dumps({"status": STATUS, "cagr_lift_pp": lift, "mdd_pp": held_mdd}, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
