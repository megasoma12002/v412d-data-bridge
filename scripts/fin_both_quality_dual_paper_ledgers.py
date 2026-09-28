#!/usr/bin/env python3
"""FIN both-quality dual-paper ledgers — OPERATING OBSERVE (paper only).

BASE_LIVE_FUSE_COOL ∥ B_OR_K9_x_HARD150 (buy OR_K9 × sell hard NOT_BELOW_MA150).
Soft-Frozen KEEP · SELL_a75 KEEP · Exact T+1 KEEP · COOL_c8 KEEP · no live wire.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import e16_clip_search_challenger as clip
import e16_soft_frozen_base as soft
import e22_dividend_accounting as e22div
import e45_defend_handoff_stagea_screen as stagea
from cool_c8_proxy_observe_helpers import build_cool_c8_exposure
from e45_paper_harness import ROOT, WINDOWS_STANDARD, window_stats
from e50_early_stack_combined_nav import FIN, e16_features, simulate_core
from fin_both_quality_observe_helpers import (
    BASE_ID,
    CHAL_ID,
    HUMAN_OPEN,
    STAGE_B_VERDICT,
    STATUS,
)
from fin_buy_quality_helpers import (
    and_buy_ok,
    below_ma_ok,
    catalog_gate,
    not_gate,
    or_buy_ok,
    raw_close_panel,
)
from live_config import LIVE_FUSE_SOFT_SELL_BOOST
from ops_dual_paper_ledgers import (
    DualPaperLedgerSpec,
    LedgerResult,
    PreparedBooks,
    cli_main,
    live_kd_sim_kwargs,
    preflight_live_kd,
    write_json_md_pair,
)
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
from within_sleeve_alloc import build_kd_season_tilt_scores, build_pre_exdiv_window_buy_ok

OUT = ROOT / "repro/fin-both-quality-dual-paper-observe"
OPS = ROOT / "research/ops"
E22_VERSION = e22div.DEFAULT_BOOKS_VERSION
SELL_AMP = float(LIVE_FUSE_SOFT_SELL_BOOST)
CAPITAL = float(DEFAULT_CAPITAL)
LOT = int(BOARD_LOT)


def _preflight() -> None:
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.8]
    assert abs(SELL_AMP - 0.75) < 1e-12
    preflight_live_kd(LIVE_KD)()


def _buy(kd, lows) -> pd.DataFrame:
    out = soft_boost_scores(kd, lows[BUY_LOW_ID], 1.0)
    return soft_boost_scores(out, lows["K9_LT30"], 1.0)


def _sell(highs) -> pd.DataFrame:
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


def prepare(market: pd.DataFrame, dividends: pd.DataFrame) -> PreparedBooks:
    _p, sleeve, _tgt, regime = e16_features(market)
    cal = pd.DatetimeIndex(pd.to_datetime(market["date"]).drop_duplicates().sort_values())
    lows, highs = build_low_high_catalog(market, cal, list(FIN))
    raw = raw_close_panel(market, cal, list(FIN))
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
    scores = _buy(kd, lows)
    sell = _sell(highs)
    sleeve_sc = _sleeve_score(market, sleeve, LIVE_SLEEVE_ALPHA)
    target = _target_live(sleeve_sc, regime)

    print("offense NAV for cool ...", flush=True)
    off_nav, _, meta = simulate_core(
        market,
        target,
        regime,
        dividends,
        apply_e22=True,
        apply_stock_div=True,
        capital=CAPITAL,
        lot_size=LOT,
        e22_version=E22_VERSION,
        **live_kd_sim_kwargs(scores=scores, buy_ok=base_buy_ok, sell_scores=sell),
    )
    assert meta.get("exact_t1_ok")
    cool = _cool_from_offense(market, off_nav)

    extra = or_buy_ok(catalog_gate(lows["BELOW_MA120"]), catalog_gate(lows["K9_LT30"]))
    chal_buy = and_buy_ok(base_buy_ok, extra)
    sell_ok = not_gate(below_ma_ok(raw, 150))

    chal_kw = live_kd_sim_kwargs(
        scores=scores,
        buy_ok=chal_buy,
        sell_scores=sell,
        e45_exposure=cool.astype(float),
    )
    chal_kw["fin_sell_ok"] = sell_ok

    return PreparedBooks(
        base_target=target,
        base_regime=regime,
        chal_target=target,
        chal_regime=regime,
        base_kwargs=live_kd_sim_kwargs(
            scores=scores,
            buy_ok=base_buy_ok,
            sell_scores=sell,
            e45_exposure=cool.astype(float),
        ),
        chal_kwargs=chal_kw,
        extras={"exposure_cool.csv": cool.rename("e45_exposure")},
        context={"buy": "OR_K9", "sell": "HARD_MA150"},
    )


def report(result: LedgerResult) -> None:
    win_base = pack_windows(result.nav_base)
    win_chal = pack_windows(result.nav_chal)
    tip = tip_windows(result.nav_base, result.nav_chal)
    held_b = win_base.get("heldout_2019_plus") or {}
    held_c = win_chal.get("heldout_2019_plus") or {}
    gb = cagr_delta_pp(held_b.get("cagr"), held_c.get("cagr"), missing_as_zero=True)
    lift = None if gb is None else round(float(-float(gb)), 4)
    mdd_pp = round(float(mdd_delta_pp(held_b.get("max_drawdown"), held_c.get("max_drawdown"))), 4)
    payload = {
        "schema_version": "fin_both_quality_dual_paper_observe_v1",
        "label": "FIN_BOTH_QUALITY_DUAL_PAPER_OBSERVE_OPERATING",
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": STATUS,
        "human_open": HUMAN_OPEN,
        "live_wire": False,
        "cutover_authorized": False,
        "sell_a75_keep": True,
        "base_id": BASE_ID,
        "challenger_id": CHAL_ID,
        "stage_b_verdict": STAGE_B_VERDICT,
        "base_windows": win_base,
        "chal_windows": win_chal,
        "heldout_delta": {"cagr_lift_pp": lift, "mdd_improve_pp": mdd_pp},
        "tip": tip,
        "n_fills_base": int(len(result.fills_base)),
        "n_fills_chal": int(len(result.fills_chal)),
        "non_actions": [
            "Soft-Frozen KEEP — no Class D from observe",
            "SELL_a75 KEEP",
            "No tip rewrite / loss-defer",
            "Cutover BLOCKED until dedicated ACCEPT",
        ],
    }
    md = [
        "# FIN both-quality dual-paper observe — OPERATING",
        "",
        f"- human_open: `{HUMAN_OPEN}`",
        f"- status: **{STATUS}** · live_wire: false · cutover: **BLOCKED** · SELL_a75 KEEP",
        f"- books: `{BASE_ID}` ∥ `{CHAL_ID}`",
        f"- Stage B: `{STAGE_B_VERDICT}`",
        f"- held-out: CAGR↑ {lift} pp · MDD↑ {mdd_pp} pp",
        f"- tip ytd MDD↑ {tip.get('ytd', {}).get('mdd_improve_pp')} · tip 1y MDD↑ {tip.get('trailing_1y', {}).get('mdd_improve_pp')}",
        "",
        "## Non-actions",
        "",
    ]
    md += [f"- {x}" for x in payload["non_actions"]]
    md += ["", "Repro: `repro/fin-both-quality-dual-paper-observe/`", ""]
    write_json_md_pair(
        out_dir=OUT,
        report_stem="FIN_BOTH_QUALITY_DUAL_PAPER_OBSERVE_OPERATING",
        payload=payload,
        md_lines=md,
        mirror_dirs=(OPS,),
    )
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)
    (OUT / "outputs" / "dual_paper_summary.json").write_text(text, encoding="utf-8")
    (OPS / "FIN_BOTH_QUALITY_DUAL_PAPER_OBSERVE.json").write_text(text, encoding="utf-8")


SPEC = DualPaperLedgerSpec(
    label="FIN_BOTH_QUALITY_DUAL_PAPER_OBSERVE_OPERATING",
    out_dir=OUT,
    base_id=BASE_ID,
    chal_id=CHAL_ID,
    prepare=prepare,
    base_nav_name="base_live_fuse_cool_daily_nav.csv",
    chal_nav_name="b_or_k9_x_hard150_daily_nav.csv",
    write_fills=True,
    soft_frozen_clip=(0.6, 0.8),
    preflight=_preflight,
    report_fn=report,
    status=STATUS,
    capital=CAPITAL,
    lot_size=LOT,
    e22_version=E22_VERSION,
)


if __name__ == "__main__":
    raise SystemExit(cli_main(SPEC))
