#!/usr/bin/env python3
"""TEL both-quality Stage A — buy×sell quality on Telecom sleeve (paper).

Charter: research/ops/TEL_BOTH_QUALITY_STAGEA_CHARTER.md
Live twin: Soft-Frozen + FUSE SELL_a75 + COOL + FIN KD_OPT + TEL T3 (INV_VOL20 cool-gated).
FIN stays KD_OPT; only TEL overlays challenged. Soft-Frozen KEEP · no live wire.
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
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, load_market, window_stats
from e50_early_stack_combined_nav import FIN, TEL, e16_features, simulate_core
from fin_buy_quality_helpers import (
    and_buy_ok,
    below_ma_ok,
    catalog_gate,
    close_panel,
    forward_win_stats,
    or_buy_ok,
    raw_close_panel,
    rsi_lt_ok,
)
from fin_sell_quality_helpers import (
    cagr_lift_pp,
    dampen_sell_when_false,
    forward_sell_win_stats,
    not_gate,
)
from live_config import LIVE_FUSE_SOFT_SELL_BOOST
from live_tel_t3_invvol_cutover import build_inv_vol20_scores
from ops_repro_ssot import write_ops_and_repro_pointer
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
    TEL_RS_SOFT_TILT,
    TEL_RS_SOFT_TILT_EXDIV,
    build_kd_season_tilt_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "archive" / "repro" / "tel-both-quality-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "TEL_BOTH_QUALITY_STAGEA_CHARTER"
SCREEN_ID = "TEL_BOTH_QUALITY_STAGEA_SCREEN"
DECISION_ID = "TEL_BOTH_QUALITY_STAGEA_DECISION_PACK"
BASE_ID = "CTRL_BASE"
E22_VERSION = e22div.DEFAULT_BOOKS_VERSION
SELL_AMP = float(LIVE_FUSE_SOFT_SELL_BOOST)

CAGR_FLOOR_PP = 0.15
HELD_MDD_MIN_PP = -0.25
HELD_ABS_MDD_MAX = 0.15
TIP_MDD_MIN_PP = 0.0
WR_HIT_PP = 0.5
WIN_H = 21

GRID: list[dict[str, Any]] = [
    {"id": "CTRL_BASE", "buy": None, "sell": None},
    {"id": "BUY_MA60", "buy": "MA60", "sell": None},
    {"id": "BUY_MA120", "buy": "MA120", "sell": None},
    {"id": "BUY_OR_K9", "buy": "OR_K9", "sell": None},
    {"id": "BUY_RSI14_LT40", "buy": "RSI14_LT40", "sell": None},
    {"id": "SELL_HARD_MA60", "buy": None, "sell": "HARD_MA60"},
    {"id": "SELL_HARD_MA120", "buy": None, "sell": "HARD_MA120"},
    {"id": "SELL_DAMP_MA60_d50", "buy": None, "sell": "DAMP_MA60_50"},
    {"id": "BOTH_MA60_x_HARD60", "buy": "MA60", "sell": "HARD_MA60"},
    {"id": "BOTH_OR_K9_x_HARD60", "buy": "OR_K9", "sell": "HARD_MA60"},
    {"id": "BOTH_MA120_x_HARD120", "buy": "MA120", "sell": "HARD_MA120"},
    {"id": "BOTH_OR_K9_x_HARD120", "buy": "OR_K9", "sell": "HARD_MA120"},
]


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
            out[wname] = {"mdd_improve_pp": None, "cagr_lift_pp": None, "gate": "INSUFFICIENT"}
            continue
        bn = b["nav"].astype(float) / float(b["nav"].iloc[0])
        cn = c["nav"].astype(float) / float(c["nav"].iloc[0])
        b_mdd = float((bn / bn.cummax() - 1.0).min())
        c_mdd = float((cn / cn.cummax() - 1.0).min())
        years = (len(b) - 1) / 252.0
        bc = float(bn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        cc = float(cn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        out[wname] = {
            "mdd_improve_pp": round(float(mdd_delta_pp(b_mdd, c_mdd)), 4),
            "cagr_lift_pp": None
            if (lift := cagr_lift_pp(bc, cc)) is None
            else round(float(lift), 4),
            "gate": "PASS",
        }
    return out


def cool_gate_scores(scores: pd.DataFrame, cool: pd.Series) -> pd.DataFrame:
    out = scores.copy().astype(float)
    c = cool.reindex(out.index).fillna(1.0).astype(float)
    off = c >= 1.0 - 1e-12
    out.loc[off, :] = 0.0
    return out


def _buy_extra(name: str | None, *, lows: dict, raw_closes: pd.DataFrame) -> pd.DataFrame | None:
    if name is None:
        return None
    if name == "MA60":
        return catalog_gate(lows["BELOW_MA60"]) if "BELOW_MA60" in lows else below_ma_ok(raw_closes, 60)
    if name == "MA120":
        return catalog_gate(lows["BELOW_MA120"]) if "BELOW_MA120" in lows else below_ma_ok(raw_closes, 120)
    if name == "OR_K9":
        hard = catalog_gate(lows["BELOW_MA60"]) if "BELOW_MA60" in lows else below_ma_ok(raw_closes, 60)
        return or_buy_ok(hard, catalog_gate(lows["K9_LT30"]))
    if name == "RSI14_LT40":
        return rsi_lt_ok(raw_closes, thresh=40.0, n=14)
    raise ValueError(f"unknown buy {name}")


def _sell_overlay(
    name: str | None, *, lows: dict, raw_closes: pd.DataFrame, sell0: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame | None]:
    """Return (tel_sell_scores, tel_sell_ok). sell0 is a TEL-shaped score panel (ones)."""
    if name is None:
        return sell0, None
    if name == "HARD_MA60":
        return sell0, not_gate(below_ma_ok(raw_closes, 60))
    if name == "HARD_MA120":
        return sell0, not_gate(below_ma_ok(raw_closes, 120))
    if name == "DAMP_MA60_50":
        q = not_gate(below_ma_ok(raw_closes, 60))
        return dampen_sell_when_false(sell0, q, 0.50), None
    raise ValueError(f"unknown sell {name}")


def _sim(
    market,
    target,
    regime,
    dividends,
    *,
    fin_scores,
    fin_buy_ok,
    fin_sell,
    tel_scores,
    tel_buy_ok,
    tel_sell,
    tel_sell_ok,
    exposure,
    telecom_alloc: str,
):
    kw: dict[str, Any] = {
        "apply_e22": True,
        "apply_stock_div": True,
        "capital": float(DEFAULT_CAPITAL),
        "lot_size": int(BOARD_LOT),
        "financial_alloc": FIN_PRE_EXDIV_KD,
        "telecom_alloc": telecom_alloc,
        "fin_name_scores": fin_scores,
        "fin_buy_ok": fin_buy_ok,
        "fin_sell_scores": fin_sell,
        "tel_name_scores": tel_scores,
        "e45_exposure": exposure.astype(float),
        "e22_version": E22_VERSION,
    }
    if tel_buy_ok is not None:
        kw["tel_buy_ok"] = tel_buy_ok
    if tel_sell_ok is not None:
        kw["tel_sell_ok"] = tel_sell_ok
    if tel_sell is not None:
        kw["tel_sell_scores"] = tel_sell
    nav, fills, meta = simulate_core(market, target, regime, dividends, **kw)
    if not bool(meta.get("exact_t1_ok")):
        raise RuntimeError("exact_t1_ok failed")
    return nav, fills, meta


def _eval_row(base_w, chal_w, tip, *, book_id, buy_wr, sell_wr, base_buy_wr, base_sell_wr):
    held_b = base_w.get("heldout_2019_plus") or {}
    held_c = chal_w.get("heldout_2019_plus") or {}
    cagr_pp = cagr_lift_pp(held_b.get("cagr"), held_c.get("cagr"))
    mdd_pp = mdd_delta_pp(held_b.get("max_drawdown"), held_c.get("max_drawdown"))
    abs_mdd = held_c.get("max_drawdown")
    tip_ytd = (tip.get("ytd") or {}).get("mdd_improve_pp")
    tip_1y = (tip.get("trailing_1y") or {}).get("mdd_improve_pp")
    tip_ok = (
        tip_ytd is not None
        and tip_1y is not None
        and float(tip_ytd) >= TIP_MDD_MIN_PP
        and float(tip_1y) >= TIP_MDD_MIN_PP
    )
    cagr_ok = cagr_pp is not None and float(cagr_pp) >= CAGR_FLOOR_PP
    mdd_ok = mdd_pp is not None and float(mdd_pp) >= HELD_MDD_MIN_PP
    band_ok = abs_mdd is not None and abs(float(abs_mdd)) <= HELD_ABS_MDD_MAX
    buy_pp = None
    if base_buy_wr and base_buy_wr.get("win_rate") is not None and buy_wr.get("win_rate") is not None:
        buy_pp = round(float(buy_wr["win_rate"]) - float(base_buy_wr["win_rate"]), 4)
    sell_pp = None
    if base_sell_wr and base_sell_wr.get("win_rate") is not None and sell_wr.get("win_rate") is not None:
        sell_pp = round(float(sell_wr["win_rate"]) - float(base_sell_wr["win_rate"]), 4)
    wr_hit = (buy_pp is not None and float(buy_pp) >= WR_HIT_PP) or (
        sell_pp is not None and float(sell_pp) >= WR_HIT_PP
    )
    economic = bool(cagr_ok and mdd_ok and band_ok and tip_ok)
    is_chal = book_id != BASE_ID
    return {
        "held_cagr_lift_pp": None if cagr_pp is None else round(float(cagr_pp), 4),
        "held_mdd_pp": None if mdd_pp is None else round(float(mdd_pp), 4),
        "held_abs_mdd": None if abs_mdd is None else round(float(abs_mdd), 6),
        "tip_ytd_mdd_pp": tip_ytd,
        "tip_1y_mdd_pp": tip_1y,
        "buy_win_rate_pp": buy_pp,
        "sell_win_rate_pp": sell_pp,
        "buy_win_n": buy_wr.get("n"),
        "sell_win_n": sell_wr.get("n"),
        "gates": {
            "cagr": bool(cagr_ok),
            "mdd_near_flat": bool(mdd_ok),
            "mdd_band": bool(band_ok),
            "tip_safe": bool(tip_ok),
            "wr_hit": bool(wr_hit),
            "economic": economic,
        },
        "hit": bool(economic and wr_hit and is_chal),
        "observe_ok": bool(economic and is_chal),
        "cagr_sign": "chal_minus_base",
    }


def _verdict(rows):
    legal = [r for r in rows if r["id"] != BASE_ID]
    if any(r["eval"]["hit"] for r in legal):
        return "TEL_QUALITY_HIT"
    if any(r["eval"]["gates"]["economic"] for r in legal):
        return "WIN_SOFT"
    if any(r["eval"]["gates"]["cagr"] for r in legal):
        return "MDD_BLOCK"
    return "NO_EDGE"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    REP.mkdir(parents=True, exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.8]

    market = load_market()
    dividends = load_dividends()
    _p, sleeve, _t, regime = e16_features(market)
    cal = pd.DatetimeIndex(pd.to_datetime(sorted(market["date"].unique())))
    lows_t, highs_t = build_low_high_catalog(market, cal, list(TEL))
    closes_t = close_panel(market, cal, list(TEL))
    raw_t = raw_close_panel(market, cal, list(TEL))
    lows_f, highs_f = build_low_high_catalog(market, cal, list(FIN))

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
    fin_buy_ok = build_pre_exdiv_window_buy_ok(
        cal, dividends, list(FIN), pre_days=int(LIVE_KD["pre_days"]), also_stock_ex=True
    )
    fin_scores = soft_boost_scores(kd, lows_f[BUY_LOW_ID], 1.0)
    fin_scores = soft_boost_scores(fin_scores, lows_f["K9_LT30"], 1.0)
    fin_sell = soft_sell_panel(highs_f[SELL_HIGH_ID], boost=float(SELL_AMP))

    _p2, _s2, _t2, _r2, base_score = soft.build_soft_frozen_targets(market)
    tilt = sleeve_signal_panel(sleeve, "rsi_lt30", 14)
    sleeve_sc = base_score + float(LIVE_SLEEVE_ALPHA) * tilt
    target = clip.build_targets_with_clips(
        regime=regime,
        score=sleeve_sc,
        fin_lo=float(soft.SOFT_FROZEN_FIN_LO),
        fin_hi=float(soft.SOFT_FROZEN_FIN_HI),
        tel_lo=float(soft.SOFT_FROZEN_TEL_LO),
        tel_hi=float(soft.SOFT_FROZEN_TEL_HI),
        etf_lo=float(soft.SOFT_FROZEN_ETF_LO),
        etf_hi=float(soft.SOFT_FROZEN_ETF_HI),
    )

    print("offense NAV for cool ...", flush=True)
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
        fin_name_scores=fin_scores,
        fin_buy_ok=fin_buy_ok,
        fin_sell_scores=fin_sell,
        e22_version=E22_VERSION,
    )
    cool = build_cool_c8_exposure(
        pd.DatetimeIndex(stagea._nav_series(off_nav).index),
        stagea._risk_features(market, stagea._nav_series(off_nav))["proxy_mdd63"],
    )
    inv = build_inv_vol20_scores(market).reindex(cal).fillna(0.0)
    tel_scores = cool_gate_scores(inv, cool)
    tel_sell0 = pd.DataFrame(1.0, index=cal, columns=list(TEL))

    rows = []
    base_nav = base_w = None
    base_buy_wr = base_sell_wr = None
    tel_set = set(TEL)

    for spec in GRID:
        bid = str(spec["id"])
        extra = _buy_extra(spec.get("buy"), lows=lows_t, raw_closes=raw_t)
        tel_buy = extra  # None = no gate
        tel_sell, tel_sell_ok = _sell_overlay(
            spec.get("sell"), lows=lows_t, raw_closes=raw_t, sell0=tel_sell0
        )
        # Buy overlays need EXDIV policy so buy_ok is honored (plain RS_SOFT_TILT ignores buy_ok).
        # Sell-only / CTRL keep T3 twin: RS_SOFT_TILT + cool-gated INV_VOL scores.
        if extra is not None:
            telecom_alloc = TEL_RS_SOFT_TILT_EXDIV
        else:
            telecom_alloc = TEL_RS_SOFT_TILT
        print(f"{bid} ...", flush=True)
        nav, fills, meta = _sim(
            market,
            target,
            regime,
            dividends,
            fin_scores=fin_scores,
            fin_buy_ok=fin_buy_ok,
            fin_sell=fin_sell,
            tel_scores=tel_scores,
            tel_buy_ok=tel_buy,
            tel_sell=tel_sell,
            tel_sell_ok=tel_sell_ok,
            exposure=cool,
            telecom_alloc=telecom_alloc,
        )
        nav.to_csv(OUT / f"nav_{bid}.csv", index=False)
        fills.to_csv(OUT / f"fills_{bid}.csv", index=False)
        w = _pack(nav)
        buy_wr = forward_win_stats(fills, closes_t, codes=tel_set, side="BUY", horizon=WIN_H)
        sell_wr = forward_sell_win_stats(fills, closes_t, codes=tel_set, horizon=WIN_H)
        if bid == BASE_ID:
            base_nav, base_w = nav, w
            base_buy_wr, base_sell_wr = buy_wr, sell_wr
            tip = {
                "ytd": {"mdd_improve_pp": 0.0, "cagr_lift_pp": 0.0, "gate": "PASS"},
                "trailing_1y": {"mdd_improve_pp": 0.0, "cagr_lift_pp": 0.0, "gate": "PASS"},
            }
        else:
            tip = _tip(base_nav, nav)
        ev = _eval_row(
            base_w or w,
            w,
            tip,
            book_id=bid,
            buy_wr=buy_wr,
            sell_wr=sell_wr,
            base_buy_wr=base_buy_wr,
            base_sell_wr=base_sell_wr,
        )
        rows.append(
            {
                "id": bid,
                "windows": w,
                "tip": tip,
                "eval": ev,
                "buy_wr": buy_wr,
                "sell_wr": sell_wr,
                "spec": spec,
                "n_fills": int(len(fills)),
                "exact_t1_ok": bool(meta.get("exact_t1_ok")),
            }
        )
        print(json.dumps({"book": bid, "eval": ev}, ensure_ascii=False), flush=True)

    verdict = _verdict(rows)
    generated = _utc()
    best = next((r["id"] for r in rows if r["eval"]["hit"]), None)
    if best is None:
        best = next((r["id"] for r in rows if r["eval"]["gates"]["economic"] and r["id"] != BASE_ID), None)

    payload = {
        "label": f"{SCREEN_ID}_{generated.replace(':', '').replace('-', '')}",
        "generated_at_utc": generated,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "status": "STAGE_A_SCREEN_DONE",
        "verdict": verdict,
        "live_wire": False,
        "soft_frozen_keep": True,
        "cagr_sign": "chal_minus_base",
        "base_id": BASE_ID,
        "gates": {
            "held_cagr_lift_pp": CAGR_FLOOR_PP,
            "held_mdd_pp_floor": HELD_MDD_MIN_PP,
            "held_abs_mdd_max": HELD_ABS_MDD_MAX,
            "tip_mdd_pp_floor": TIP_MDD_MIN_PP,
            "wr_hit_pp": WR_HIT_PP,
            "win_horizon": WIN_H,
        },
        "books": [
            {
                "id": r["id"],
                "windows": r["windows"],
                "tip": r["tip"],
                "eval": r["eval"],
                "buy_wr": r["buy_wr"],
                "sell_wr": r["sell_wr"],
                "spec": r["spec"],
                "n_fills": r["n_fills"],
                "exact_t1_ok": r["exact_t1_ok"],
            }
            for r in rows
        ],
        "binding": [
            "Soft-Frozen KEEP",
            "FIN KD_OPT KEEP",
            "TEL T3 cool-gated INV_VOL base",
            "no live wire from Stage A",
        ],
    }
    screen_md = "\n".join(
        [
            f"# {SCREEN_ID}",
            "",
            f"Date: 2026-09-28 · Generated `{generated}`",
            f"Status: **{verdict}** · Soft-Frozen **KEEP** · live wire **false**",
            "",
            "| ID | CAGR↑ | MDD↑ | tip YTD MDD↑ | buyWR↑ | sellWR↑ | HIT |",
            "|---|---:|---:|---:|---:|---:|:---:|",
        ]
        + [
            "| {id} | {c} | {m} | {t} | {b} | {s} | {h} |".format(
                id=r["id"],
                c=r["eval"]["held_cagr_lift_pp"],
                m=r["eval"]["held_mdd_pp"],
                t=r["eval"]["tip_ytd_mdd_pp"],
                b=r["eval"]["buy_win_rate_pp"],
                s=r["eval"]["sell_win_rate_pp"],
                h="Y" if r["eval"]["hit"] else "",
            )
            for r in rows
        ]
        + ["", f"Verdict: **`{verdict}`**", f"Label: `{SCREEN_ID}_2026-09-28__{verdict}`", ""]
    )
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OPS / f"{SCREEN_ID}.md").write_text(screen_md, encoding="utf-8")
    (REP / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (REP / f"{SCREEN_ID}.md").write_text(screen_md, encoding="utf-8")

    decision = {
        "label": f"{DECISION_ID}_2026-09-28__{verdict}__NO_LIVE",
        "status": verdict,
        "generated_at_utc": generated,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "screen": f"research/ops/{SCREEN_ID}.md",
        "live_wire": False,
        "best_candidate": best,
        "cagr_sign": "chal_minus_base",
    }
    decision_md = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: 2026-09-28 · Generated `{generated}`",
            f"Status: **{verdict}** · Soft-Frozen **KEEP** · live wire **false**",
            "",
            f"Charter: `{CHARTER_ID}.md`",
            f"Screen: `{SCREEN_ID}.md`",
            "",
            "## Verdict",
            "",
            f"**`{verdict}`**",
            "",
            f"Best: **`{best}`**" if best else "No candidate.",
            "",
            "## Binding",
            "",
            "1. Soft-Frozen / Exact T+1 / COOL / FIN KD_OPT / SELL_a75 KEEP",
            "2. Even HIT → ballot only; no live TEL flip from Stage A",
            "3. Live T3_COOL_INV_VOL20 KEEP unless dedicated ACCEPT",
            "",
            f"Label: `{DECISION_ID}_2026-09-28__{verdict}__NO_LIVE`",
            "",
        ]
    )
    write_ops_and_repro_pointer(OPS / f"{DECISION_ID}.json", REP / f"{DECISION_ID}.json", json.dumps(decision, indent=2, ensure_ascii=False) + "\n")
    write_ops_and_repro_pointer(OPS / f"{DECISION_ID}.md", REP / f"{DECISION_ID}.md", decision_md)

    charter_md = "\n".join(
        [
            "# TEL both-quality Stage A — buy×sell (paper)",
            "",
            "Date: 2026-09-28",
            f"Status: **Stage A DONE — `{verdict}`** · Soft-Frozen **KEEP** · no live wire",
            "Parent live: Soft-Frozen + FUSE + SELL_a75 + COOL + FIN KD_OPT + TEL T3",
            "",
            "Human intent:",
            "",
            "```",
            "OPEN Stage A: TEL within-sleeve 買賣品質 · CAGR/MDD + WR · FIN KD_OPT KEEP · paper only",
            "```",
            "",
            f"Label: `{CHARTER_ID}_2026-09-28__DONE_{verdict}__NO_LIVE_WIRE`",
            "",
            "## Run",
            "",
            "```bash",
            "PYTHONPATH=scripts python3 scripts/tel_both_quality_stagea.py",
            "```",
            "",
        ]
    )
    (OPS / f"{CHARTER_ID}.md").write_text(charter_md, encoding="utf-8")
    (OPS / f"{CHARTER_ID}.json").write_text(
        json.dumps({"label": f"{CHARTER_ID}_2026-09-28__DONE_{verdict}__NO_LIVE_WIRE", "status": f"DONE_{verdict}", "verdict": verdict, "live_wire": False}, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"verdict": verdict, "n_books": len(rows), "best": best}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
