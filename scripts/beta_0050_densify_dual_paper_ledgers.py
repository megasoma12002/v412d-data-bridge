#!/usr/bin/env python3
"""β densify dual-paper ledgers — OPERATING OBSERVE (paper only).

LIVE_FUSE_COOL ∥ BETA_F0.60-0.80_E0.00-0.50 under frozen COOL.
Soft-Frozen live clip KEEP · no live wire · cutover BLOCKED.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import e16_clip_search_challenger as clip
import e16_soft_frozen_base as soft
import e45_defend_handoff_stagea_screen as stagea
from beta_0050_densify_observe_helpers import (
    BASE_ID,
    CHAL_ETF,
    CHAL_FIN,
    CHAL_ID,
    CHAL_TEL,
    HUMAN_OPEN,
    NEAR_FLAT_NOTE,
    STAGE_A_VERDICT,
    STATUS,
)
from cool_c8_proxy_observe_helpers import build_cool_c8_exposure
from e45_paper_harness import WINDOWS_STANDARD, window_stats
from e50_early_stack_combined_nav import FIN, e16_features, simulate_core
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

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/beta-0050-densify-dual-paper-observe"
OPS = ROOT / "research/ops"
CAPITAL = float(DEFAULT_CAPITAL)
LOT = int(BOARD_LOT)


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
            out[wname] = {
                "mdd_improve_pp": None,
                "cagr_giveback_pp": None,
                "gate": "INSUFFICIENT",
            }
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


def _sleeve_score(market, sleeve) -> pd.DataFrame:
    _p, _s, _t, _r, base_score = soft.build_soft_frozen_targets(market)
    tilt = sleeve_signal_panel(sleeve, "rsi_lt30", 14)
    return base_score + float(LIVE_SLEEVE_ALPHA) * tilt


def _target(score, regime, clips):
    flo, fhi, tlo, thi, elo, ehi = clips
    return clip.build_targets_with_clips(
        regime=regime,
        score=score,
        fin_lo=flo,
        fin_hi=fhi,
        tel_lo=tlo,
        tel_hi=thi,
        etf_lo=elo,
        etf_hi=ehi,
    )


def _cool(market, offense_nav: pd.DataFrame) -> pd.Series:
    nav_s = stagea._nav_series(offense_nav)
    feat = stagea._risk_features(market, nav_s)
    dates = pd.DatetimeIndex(nav_s.index)
    return build_cool_c8_exposure(dates, feat["proxy_mdd63"])


def _preflight() -> None:
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.8]
    preflight_live_kd(LIVE_KD)()


def prepare(market: pd.DataFrame, dividends: pd.DataFrame) -> PreparedBooks:
    _p, sleeve, _tgt, regime = e16_features(market)
    cal = pd.DatetimeIndex(pd.to_datetime(market["date"]).drop_duplicates().sort_values())
    kd = build_kd_season_tilt_scores(
        market,
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
    lows, highs = build_low_high_catalog(market, cal, list(FIN))
    buy = soft_boost_scores(soft_boost_scores(kd, lows[BUY_LOW_ID], 1.0), lows["K9_LT30"], 1.0)
    sell = soft_sell_panel(highs[SELL_HIGH_ID], boost=0.50)
    score = _sleeve_score(market, sleeve)

    live_clips = (
        float(soft.SOFT_FROZEN_FIN_LO),
        float(soft.SOFT_FROZEN_FIN_HI),
        float(soft.SOFT_FROZEN_TEL_LO),
        float(soft.SOFT_FROZEN_TEL_HI),
        float(soft.SOFT_FROZEN_ETF_LO),
        float(soft.SOFT_FROZEN_ETF_HI),
    )
    chal_clips = (*CHAL_FIN, *CHAL_TEL, *CHAL_ETF)
    tgt_base = _target(score, regime, live_clips)
    tgt_chal = _target(score, regime, chal_clips)

    # Offense NAVs → per-book COOL exposure (frozen recipe).
    off_b, _, meta_b = simulate_core(
        market,
        tgt_base,
        regime,
        dividends,
        apply_e22=True,
        apply_stock_div=True,
        capital=CAPITAL,
        lot_size=LOT,
        **live_kd_sim_kwargs(scores=buy, buy_ok=buy_ok, sell_scores=sell),
    )
    assert meta_b.get("exact_t1_ok")
    off_c, _, meta_c = simulate_core(
        market,
        tgt_chal,
        regime,
        dividends,
        apply_e22=True,
        apply_stock_div=True,
        capital=CAPITAL,
        lot_size=LOT,
        **live_kd_sim_kwargs(scores=buy, buy_ok=buy_ok, sell_scores=sell),
    )
    assert meta_c.get("exact_t1_ok")
    cool_b = _cool(market, off_b)
    cool_c = _cool(market, off_c)

    return PreparedBooks(
        base_target=tgt_base,
        base_regime=regime,
        chal_target=tgt_chal,
        chal_regime=regime,
        base_kwargs=live_kd_sim_kwargs(
            scores=buy, buy_ok=buy_ok, sell_scores=sell, e45_exposure=cool_b.astype(float)
        ),
        chal_kwargs=live_kd_sim_kwargs(
            scores=buy, buy_ok=buy_ok, sell_scores=sell, e45_exposure=cool_c.astype(float)
        ),
        extras={
            "exposure_LIVE_FUSE_COOL.csv": cool_b.rename("e45_exposure"),
            "exposure_BETA_0050.csv": cool_c.rename("e45_exposure"),
        },
        context={
            "chal_clips": {
                "fin": list(CHAL_FIN),
                "tel": list(CHAL_TEL),
                "etf": list(CHAL_ETF),
            },
            "mean_0050_base": round(float(tgt_base["0050"].mean()), 4),
            "mean_0050_chal": round(float(tgt_chal["0050"].mean()), 4),
        },
    )


def report(result: LedgerResult) -> None:
    win_base = pack_windows(result.nav_base)
    win_chal = pack_windows(result.nav_chal)
    held = held_score(win_base["heldout_2019_plus"], win_chal["heldout_2019_plus"])
    sealed = held_score(
        win_base.get("sealed_2023_plus") or {},
        win_chal.get("sealed_2023_plus") or {},
    )
    tip = tip_windows(result.nav_base, result.nav_chal)
    payload = {
        "schema_version": "beta_0050_densify_dual_paper_observe_v1",
        "label": "BETA_0050_DENSIFY_DUAL_PAPER_OBSERVE_OPERATING",
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": STATUS,
        "human_open": HUMAN_OPEN,
        "near_flat_note": NEAR_FLAT_NOTE,
        "live_wire": False,
        "cutover_authorized": False,
        "base_id": BASE_ID,
        "challenger_id": CHAL_ID,
        "stage_a_verdict": STAGE_A_VERDICT,
        "chal_clips": result.prepared.context.get("chal_clips"),
        "mean_0050": {
            "base": result.prepared.context.get("mean_0050_base"),
            "chal": result.prepared.context.get("mean_0050_chal"),
        },
        "soft_frozen_fin_clip_live": list(soft.SOFT_FROZEN_FIN_CLIP),
        "base_windows": win_base,
        "chal_windows": win_chal,
        "heldout_delta": held,
        "sealed_delta": sealed,
        "tip": tip,
        "n_fills_base": int(len(result.fills_base)),
        "n_fills_chal": int(len(result.fills_chal)),
        "non_actions": [
            "Soft-Frozen live clip KEEP — no Class D flip from observe",
            "No tip history rewrite",
            "No 公+民 mix",
            "Cutover BLOCKED until dedicated ACCEPT",
        ],
    }
    md = [
        "# β / 0050 densify dual-paper observe — OPERATING",
        "",
        f"- human_open: `{HUMAN_OPEN}`",
        f"- near-flat: {NEAR_FLAT_NOTE}",
        f"- status: **{STATUS}** · live_wire: false · cutover: **BLOCKED**",
        f"- books: `{BASE_ID}` ∥ `{CHAL_ID}`",
        f"- Stage A: `{STAGE_A_VERDICT}`",
        f"- held-out: CAGR lift {held.get('cagr_lift_pp')} pp · MDD↑ {held.get('mdd_improve_pp')} pp",
        f"- tip ytd MDD↑ {tip.get('ytd', {}).get('mdd_improve_pp')} · tip 1y MDD↑ {tip.get('trailing_1y', {}).get('mdd_improve_pp')}",
        "",
        "## Non-actions",
        "",
    ]
    md += [f"- {x}" for x in payload["non_actions"]]
    md += ["", "Repro: `repro/beta-0050-densify-dual-paper-observe/`", ""]

    write_json_md_pair(
        out_dir=OUT,
        report_stem="BETA_0050_DENSIFY_DUAL_PAPER_OBSERVE_OPERATING",
        payload=payload,
        md_lines=md,
        mirror_dirs=(OPS,),
    )
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    (OUT / "outputs" / "dual_paper_summary.json").write_text(text, encoding="utf-8")
    (OPS / "BETA_0050_DENSIFY_DUAL_PAPER_OBSERVE.json").write_text(text, encoding="utf-8")


SPEC = DualPaperLedgerSpec(
    label="BETA_0050_DENSIFY_DUAL_PAPER_OBSERVE_OPERATING",
    out_dir=OUT,
    base_id=BASE_ID,
    chal_id=CHAL_ID,
    prepare=prepare,
    base_nav_name="live_fuse_cool_daily_nav.csv",
    chal_nav_name="beta_0050_densify_daily_nav.csv",
    write_fills=False,
    base_targets_name=None,
    soft_frozen_clip=(0.6, 0.8),
    preflight=_preflight,
    report_fn=report,
    status=STATUS,
    capital=CAPITAL,
    lot_size=LOT,
)


if __name__ == "__main__":
    raise SystemExit(cli_main(SPEC))
