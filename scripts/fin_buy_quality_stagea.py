#!/usr/bin/env python3
"""FIN buy-quality Stage A — paper only (win-rate + MDD + CAGR).

Charter: research/ops/FIN_BUY_QUALITY_STAGEA_CHARTER.md
Soft-Frozen KEEP · Exact T+1 KEEP · COOL_c8 KEEP · no live wire.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

import e16_clip_search_challenger as clip
import e16_soft_frozen_base as soft
import e22_dividend_accounting as e22div
import e45_defend_handoff_stagea_screen as stagea
from cool_c8_proxy_observe_helpers import build_cool_c8_exposure
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, load_market, window_stats
from e50_early_stack_combined_nav import FIN, e16_features, simulate_core
from fin_buy_quality_helpers import (
    and_buy_ok,
    catalog_gate,
    close_panel,
    cool1_buy_ok,
    forward_win_stats,
    not_gate,
    ret_sign_ok,
    rsi_lt_ok,
)
from live_config import LIVE_FUSE_SOFT_SELL_BOOST
from ops_repro_ssot import write_ops_and_repro_pointer
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
    FIN_PRE_EXDIV_KD,
    TEL_EQUAL,
    build_kd_season_tilt_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "fin-buy-quality-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_BUY_QUALITY_STAGEA_CHARTER"
SCREEN_ID = "FIN_BUY_QUALITY_STAGEA_SCREEN"
DECISION_ID = "FIN_BUY_QUALITY_STAGEA_DECISION_PACK"
BASE_ID = "CTRL_BASE"
E22_VERSION = e22div.DEFAULT_BOOKS_VERSION
SELL_AMP = float(LIVE_FUSE_SOFT_SELL_BOOST)

CAGR_FLOOR_PP = 0.15
HELD_MDD_MIN_PP = -0.25
HELD_ABS_MDD_MAX = 0.15
TIP_MDD_MIN_PP = 0.0
WIN_RATE_FLOOR_PP = 2.0
WIN_H = 21

GRID: list[dict[str, Any]] = [
    {"id": "CTRL_BASE", "filter": None},
    {"id": "Q_BELOW_MA60", "filter": "BELOW_MA60"},
    {"id": "Q_BELOW_MA120", "filter": "BELOW_MA120"},
    {"id": "Q_NOT_RSI14_GT70", "filter": "NOT_RSI14_GT70"},
    {"id": "Q_RSI14_LT50", "filter": "RSI14_LT50"},
    {"id": "Q_ABOVE_MA60", "filter": "ABOVE_MA60"},
    {"id": "Q_RET5_POS", "filter": "RET5_POS"},
    {"id": "Q_RET10_POS", "filter": "RET10_POS"},
    {"id": "Q_COOL1_ONLY", "filter": "COOL1_ONLY"},
    {"id": "Q_RET5_NEG", "filter": "RET5_NEG"},
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


def _sim(market, target, regime, dividends, *, scores, buy_ok, sell, exposure):
    nav, fills, meta = simulate_core(
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
        raise RuntimeError("exact_t1_ok failed")
    return nav, fills, meta


def _build_filter(
    name: str | None,
    *,
    lows: dict,
    highs: dict,
    closes: pd.DataFrame,
    cool: pd.Series,
    cal: pd.DatetimeIndex,
) -> pd.DataFrame | None:
    if name is None:
        return None
    codes = list(FIN)
    if name == "BELOW_MA60":
        return catalog_gate(lows["BELOW_MA60"])
    if name == "BELOW_MA120":
        return catalog_gate(lows["BELOW_MA120"])
    if name == "NOT_RSI14_GT70":
        return not_gate(highs["RSI14_GT70"])
    if name == "RSI14_LT50":
        return rsi_lt_ok(closes, thresh=50.0, n=14)
    if name == "ABOVE_MA60":
        return catalog_gate(highs["ABOVE_MA60"])
    if name == "RET5_POS":
        return ret_sign_ok(closes, n=5, positive=True)
    if name == "RET10_POS":
        return ret_sign_ok(closes, n=10, positive=True)
    if name == "COOL1_ONLY":
        return cool1_buy_ok(cal, codes, cool)
    if name == "RET5_NEG":
        return ret_sign_ok(closes, n=5, positive=False)
    raise ValueError(f"unknown filter {name}")


def _eval_row(
    base_w: dict,
    chal_w: dict,
    tip: dict,
    *,
    book_id: str,
    buy_wr: dict,
    sell_wr: dict,
    base_buy_wr: dict | None,
) -> dict[str, Any]:
    held_b = base_w.get("heldout_2019_plus") or {}
    held_c = chal_w.get("heldout_2019_plus") or {}
    cagr_pp = cagr_delta_pp(held_b.get("cagr"), held_c.get("cagr"))
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
    base_rate = None if base_buy_wr is None else base_buy_wr.get("win_rate")
    chal_rate = buy_wr.get("win_rate")
    wr_pp = None
    if base_rate is not None and chal_rate is not None:
        wr_pp = round(float(chal_rate) - float(base_rate), 4)
    wr_ok = wr_pp is not None and float(wr_pp) >= WIN_RATE_FLOOR_PP
    neg = book_id.endswith("NEG")
    hit = bool(
        cagr_ok and mdd_ok and band_ok and tip_ok and wr_ok and not neg and book_id != BASE_ID
    )
    return {
        "held_cagr_pp": None if cagr_pp is None else round(float(cagr_pp), 4),
        "held_mdd_pp": None if mdd_pp is None else round(float(mdd_pp), 4),
        "held_abs_mdd": None if abs_mdd is None else round(float(abs_mdd), 6),
        "tip_ytd_mdd_pp": tip_ytd,
        "tip_1y_mdd_pp": tip_1y,
        "buy_win_rate": chal_rate,
        "buy_win_rate_pp": wr_pp,
        "buy_win_n": buy_wr.get("n"),
        "sell_win_rate": sell_wr.get("win_rate"),
        "sell_win_n": sell_wr.get("n"),
        "gates": {
            "cagr": bool(cagr_ok),
            "mdd_near_flat": bool(mdd_ok),
            "mdd_band": bool(band_ok),
            "tip_safe": bool(tip_ok),
            "buy_win_rate": bool(wr_ok),
        },
        "hit": hit,
    }


def _verdict(rows: list[dict[str, Any]]) -> str:
    legal = [r for r in rows if r["id"] != BASE_ID and not str(r["id"]).endswith("NEG")]
    if any(r["eval"]["hit"] for r in legal):
        return "BUY_QUALITY_HIT"
    win_soft = [
        r
        for r in legal
        if r["eval"]["gates"]["cagr"]
        and r["eval"]["gates"]["mdd_near_flat"]
        and r["eval"]["gates"]["mdd_band"]
        and r["eval"]["gates"]["tip_safe"]
        and not r["eval"]["gates"]["buy_win_rate"]
    ]
    if win_soft:
        return "WIN_SOFT"
    cagr_soft = [
        r
        for r in legal
        if r["eval"]["gates"]["mdd_near_flat"]
        and r["eval"]["gates"]["mdd_band"]
        and r["eval"]["gates"]["tip_safe"]
        and not r["eval"]["gates"]["cagr"]
    ]
    if cagr_soft:
        return "CAGR_SOFT"
    mdd_block = any(
        (r["eval"]["held_mdd_pp"] is not None and float(r["eval"]["held_mdd_pp"]) < HELD_MDD_MIN_PP)
        or not r["eval"]["gates"]["tip_safe"]
        for r in legal
    )
    if mdd_block:
        return "MDD_BLOCK"
    return "NO_LIFT"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    REP.mkdir(parents=True, exist_ok=True)

    market = load_market()
    dividends = load_dividends()
    prices, sleeve, _turn, regime = e16_features(market)
    _ = prices
    cal = pd.DatetimeIndex(pd.to_datetime(sorted(market["date"].unique())))
    lows, highs = build_low_high_catalog(market, cal, list(FIN))
    closes = close_panel(market, cal, list(FIN))
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

    off_nav, _fills, _meta = simulate_core(
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
        fin_buy_ok=base_buy_ok,
        fin_sell_scores=sell,
        e22_version=E22_VERSION,
    )
    cool = _cool_from_offense(market, off_nav)

    rows: list[dict[str, Any]] = []
    base_nav = None
    base_w = None
    base_buy_wr: dict[str, Any] | None = None
    fin_set = set(FIN)

    for spec in GRID:
        bid = str(spec["id"])
        extra = _build_filter(
            spec.get("filter"),
            lows=lows,
            highs=highs,
            closes=closes,
            cool=cool,
            cal=cal,
        )
        buy_ok = base_buy_ok if extra is None else and_buy_ok(base_buy_ok, extra)
        nav, fills, meta = _sim(
            market,
            target,
            regime,
            dividends,
            scores=scores,
            buy_ok=buy_ok,
            sell=sell,
            exposure=cool,
        )
        nav.to_csv(OUT / f"nav_{bid}.csv", index=False)
        fills.to_csv(OUT / f"fills_{bid}.csv", index=False)
        w = _pack(nav)
        buy_wr = forward_win_stats(fills, closes, codes=fin_set, side="BUY", horizon=WIN_H)
        sell_wr = forward_win_stats(fills, closes, codes=fin_set, side="SELL", horizon=WIN_H)
        if bid == BASE_ID:
            base_nav = nav
            base_w = w
            base_buy_wr = buy_wr
            tip = {
                "ytd": {"mdd_improve_pp": 0.0, "cagr_giveback_pp": 0.0, "gate": "PASS"},
                "trailing_1y": {"mdd_improve_pp": 0.0, "cagr_giveback_pp": 0.0, "gate": "PASS"},
            }
        else:
            assert base_nav is not None and base_w is not None
            tip = _tip(base_nav, nav)
        ev = _eval_row(
            base_w or w,
            w,
            tip,
            book_id=bid,
            buy_wr=buy_wr,
            sell_wr=sell_wr,
            base_buy_wr=base_buy_wr,
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
            }
        )
        print(json.dumps({"book": bid, "eval": ev}, ensure_ascii=False))

    verdict = _verdict(rows)
    generated = _utc()
    payload = {
        "label": f"{SCREEN_ID}_{generated.replace(':', '').replace('-', '')}",
        "generated_at_utc": generated,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "status": "STAGE_A_SCREEN_DONE",
        "verdict": verdict,
        "live_wire": False,
        "soft_frozen_keep": True,
        "exact_t1_keep": True,
        "cool_keep": True,
        "base_id": BASE_ID,
        "gates": {
            "held_cagr_pp": CAGR_FLOOR_PP,
            "held_mdd_pp_floor": HELD_MDD_MIN_PP,
            "held_abs_mdd_max": HELD_ABS_MDD_MAX,
            "tip_mdd_pp_floor": TIP_MDD_MIN_PP,
            "buy_win_rate_pp": WIN_RATE_FLOOR_PP,
            "buy_win_horizon": WIN_H,
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
            }
            for r in rows
        ],
        "binding": [
            "Soft-Frozen live KEEP — Stage A does not authorize buy-filter live wire",
            "Exact T+1 KEEP",
            "COOL_c8 KEEP",
            "Win-rate is diagnostic on FIN BUY fwd H=21; not tip rewrite",
            "Sell loss-defer is out of scope (separate rejected track)",
        ],
    }
    screen_md = "\n".join(
        [
            f"# {SCREEN_ID}",
            "",
            f"Date: 2026-09-28 · Generated `{generated}`",
            f"Status: **{verdict}** · Soft-Frozen **KEEP** · live wire **false**",
            "",
            f"Base `{BASE_ID}` = live Soft-Frozen + FUSE SELL_a75 + COOL_c8 · Exact T+1.",
            f"Buy win-rate = FIN BUY fwd H={WIN_H} ret&gt;0.",
            "",
            "## Books",
            "",
            "| ID | held CAGR↑pp | held MDD↑pp | tip MDD↑pp | buy WR% | buy WR↑pp | HIT |",
            "|---|---:|---:|---:|---:|---:|---|",
        ]
        + [
            "| {id} | {cagr} | {mdd} | {ytd} | {wr} | {wrpp} | {hit} |".format(
                id=r["id"],
                cagr=r["eval"]["held_cagr_pp"],
                mdd=r["eval"]["held_mdd_pp"],
                ytd=r["eval"]["tip_ytd_mdd_pp"],
                wr=r["eval"]["buy_win_rate"],
                wrpp=r["eval"]["buy_win_rate_pp"],
                hit=r["eval"]["hit"],
            )
            for r in rows
        ]
        + [
            "",
            f"Verdict: **`{verdict}`**",
            "",
            f"Label: `{SCREEN_ID}_2026-09-28__{verdict}`",
            "",
        ]
    )

    (OPS / f"{SCREEN_ID}.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (OPS / f"{SCREEN_ID}.md").write_text(screen_md, encoding="utf-8")
    (REP / f"{SCREEN_ID}.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (REP / f"{SCREEN_ID}.md").write_text(screen_md, encoding="utf-8")

    best = next((r for r in rows if r["eval"]["hit"]), None)
    dlines = [
        f"# {DECISION_ID}",
        "",
        f"Date: 2026-09-28 · Generated `{generated}`",
        f"Status: **{verdict}** · Soft-Frozen **KEEP** · Exact T+1 **KEEP** · COOL **KEEP** · live wire **false**",
        "",
        f"Charter: `{CHARTER_ID}.md`",
        f"Screen: `{SCREEN_ID}.md`",
        "",
        "## Verdict",
        "",
        f"**`{verdict}`**",
        "",
    ]
    if best:
        dlines += [
            (
                f"Best HIT book: `{best['id']}` · held CAGR↑ {best['eval']['held_cagr_pp']}pp · "
                f"held MDD↑ {best['eval']['held_mdd_pp']}pp · buy WR↑ {best['eval']['buy_win_rate_pp']}pp"
            ),
            "",
        ]
    dlines += [
        "## Binding",
        "",
        "1. Soft-Frozen / tip / Exact T+1 KEEP",
        "2. Even HIT → paper observe ballot only (separate ACCEPT for live)",
        "3. Win-rate is diagnostic; not FIFO/tip rewrite",
        "4. Sell loss-defer remains out of scope",
        "",
        f"Label: `{DECISION_ID}_2026-09-28__{verdict}__NO_LIVE`",
        "",
    ]
    decision = {
        "label": f"{DECISION_ID}_2026-09-28__{verdict}__NO_LIVE",
        "status": verdict,
        "live_wire": False,
        "soft_frozen_keep": True,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "screen": f"research/ops/{SCREEN_ID}.md",
        "best_hit": None if best is None else best["id"],
        "generated_at_utc": generated,
    }
    write_ops_and_repro_pointer(
        OPS / f"{DECISION_ID}.json",
        REP / f"{DECISION_ID}.json",
        json.dumps(decision, indent=2, ensure_ascii=False) + "\n",
    )
    write_ops_and_repro_pointer(
        OPS / f"{DECISION_ID}.md",
        REP / f"{DECISION_ID}.md",
        "\n".join(dlines),
    )

    ch = (OPS / f"{CHARTER_ID}.md").read_text(encoding="utf-8")
    ch2 = ch.replace(
        "Status: **Stage A OPEN**",
        f"Status: **Stage A DONE — `{verdict}`**",
        1,
    )
    if ch2 != ch:
        (OPS / f"{CHARTER_ID}.md").write_text(ch2, encoding="utf-8")
    zh = (OPS / f"{CHARTER_ID}.zh-TW.md").read_text(encoding="utf-8")
    zh2 = zh.replace(
        "狀態：**Stage A OPEN**",
        f"狀態：**Stage A DONE — `{verdict}`**",
        1,
    )
    if zh2 != zh:
        (OPS / f"{CHARTER_ID}.zh-TW.md").write_text(zh2, encoding="utf-8")

    print(json.dumps({"verdict": verdict, "n_books": len(rows)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
