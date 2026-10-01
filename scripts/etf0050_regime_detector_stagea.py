#!/usr/bin/env python3
"""ETF 0050 regime × local bull/bear detector Stage A (paper).

Charter: research/ops/ETF0050_REGIME_DETECTOR_STAGEA_CHARTER.md
Parents 1d/1e TIP_BLOCK · 1c ASYMM densify CLOSED · Soft-Frozen KEEP · no live.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

import e22_dividend_accounting as e22div
import live_cool_c8_cutover as cool_cut
import live_dh_fuse_cutover as fuse_cut
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, load_market, window_stats
from e50_early_stack_combined_nav import e16_features, simulate_core
from fin_buy_quality_helpers import close_panel, forward_win_stats
from fin_sell_quality_helpers import cagr_lift_pp, forward_sell_win_stats
from live_config import LIVE_FUSE_SOFT_SELL_BOOST
from ops_repro_ssot import write_ops_and_repro_pointer
from portfolio_capital import DEFAULT_CAPITAL
from research_metric_helpers import mdd_delta_pp
from tw_share_lots import BOARD_LOT
from within_sleeve_alloc import FIN_PRE_EXDIV_KD, TEL_EQUAL

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "archive" / "repro" / "etf0050-regime-detector-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "ETF0050_REGIME_DETECTOR_STAGEA_CHARTER"
SCREEN_ID = "ETF0050_REGIME_DETECTOR_STAGEA_SCREEN"
DECISION_ID = "ETF0050_REGIME_DETECTOR_STAGEA_DECISION_PACK"
BASE_ID = "CTRL_BASE"
CODE = "0050"
E22_VERSION = e22div.DEFAULT_BOOKS_VERSION
SELL_AMP = float(LIVE_FUSE_SOFT_SELL_BOOST)

CAGR_FLOOR_PP = 0.15
HELD_MDD_MIN_PP = -0.25
HELD_ABS_MDD_MAX = 0.15
TIP_MDD_MIN_PP = 0.0
WR_FLOOR_PP = 0.5
WIN_H = 21

GRID: list[dict[str, Any]] = [
    {"id": "CTRL_BASE", "track": "ctrl", "buy": None, "sell": None},
    {"id": "REG_BUY_BULL", "track": "reg", "buy": "BULL", "sell": None},
    {"id": "REG_BUY_BULL_SIDE", "track": "reg", "buy": "BULL_SIDE", "sell": None},
    {"id": "REG_SELL_BEAR_CRISIS", "track": "reg", "buy": None, "sell": "BEAR_CRISIS"},
    {"id": "REG_BOTH_TREND", "track": "reg", "buy": "BULL", "sell": "BEAR_CRISIS"},
    {"id": "REG_BOTH_MR", "track": "reg", "buy": "BEAR_CRISIS", "sell": "BULL"},
    {"id": "DET_BUY_MA60_UP", "track": "det", "buy": "MA60_UP", "sell": None},
    {"id": "DET_BUY_MA60_DN", "track": "det", "buy": "MA60_DN", "sell": None},
    {"id": "DET_SELL_MA60_DN", "track": "det", "buy": None, "sell": "MA60_DN"},
    {"id": "DET_SELL_MA60_UP", "track": "det", "buy": None, "sell": "MA60_UP"},
    {"id": "DET_BOTH_TREND", "track": "det", "buy": "MA60_UP", "sell": "MA60_DN"},
    {"id": "DET_BOTH_MR", "track": "det", "buy": "MA60_DN", "sell": "MA60_UP"},
    {"id": "DET_BUY_MACD_POS", "track": "det", "buy": "MACD_POS", "sell": None},
    {"id": "DET_BOTH_MACD", "track": "det", "buy": "MACD_POS", "sell": "MACD_NEG"},
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


def _macd_hist(closes: pd.Series) -> pd.Series:
    s = closes.astype(float)
    ema12 = s.ewm(span=12, adjust=False).mean()
    ema26 = s.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    return macd - signal


def _feats(closes: pd.Series, regime: pd.Series) -> dict[str, pd.Series]:
    s = closes.astype(float)
    idx = s.index
    reg = regime.reindex(idx).fillna("Sideways").astype(str)
    ma60 = s.rolling(60, min_periods=60).mean()
    hist = _macd_hist(s)
    bull = reg.eq("Bull")
    side = reg.eq("Sideways")
    bear = reg.eq("Bear")
    crisis = reg.eq("Crisis")
    return {
        "BULL": bull.fillna(False),
        "BULL_SIDE": (bull | side).fillna(False),
        "BEAR_CRISIS": (bear | crisis).fillna(False),
        "MA60_UP": (s > ma60).fillna(False),
        "MA60_DN": (s < ma60).fillna(False),
        "MACD_POS": (hist > 0.0).fillna(False),
        "MACD_NEG": (hist < 0.0).fillna(False),
    }


def apply_etf_delta_scale(
    target: pd.DataFrame,
    buy_ok: pd.Series,
    sell_ok: pd.Series,
    *,
    damp: float = 0.0,
) -> pd.DataFrame:
    t = target[["Financial", "Telecom", "0050"]].astype(float).copy()
    idx = t.index
    b_ok = buy_ok.reindex(idx).fillna(True).astype(bool)
    s_ok = sell_ok.reindex(idx).fillna(True).astype(bool)
    d = float(damp)
    prev = float(t.iloc[0]["0050"])
    rows = [t.iloc[0].tolist()]
    for i in range(1, len(t)):
        fin = float(t.iloc[i]["Financial"])
        tel = float(t.iloc[i]["Telecom"])
        etf_tgt = float(t.iloc[i]["0050"])
        day = idx[i]
        if etf_tgt > prev + 1e-15 and not bool(b_ok.loc[day]):
            etf = prev + d * (etf_tgt - prev)
        elif etf_tgt < prev - 1e-15 and not bool(s_ok.loc[day]):
            etf = prev + d * (etf_tgt - prev)
        else:
            etf = etf_tgt
        if abs(etf - etf_tgt) > 1e-15:
            residual = etf_tgt - etf
            ft = fin + tel
            if ft > 1e-12:
                fin += residual * fin / ft
                tel += residual * tel / ft
            else:
                fin += residual
            ssum = fin + tel + etf
            if ssum > 1e-12:
                fin, tel, etf = fin / ssum, tel / ssum, etf / ssum
        prev = etf
        rows.append([fin, tel, etf])
    return pd.DataFrame(rows, index=idx, columns=["Financial", "Telecom", "0050"])


def _gate_series(name: str | None, feats: dict[str, pd.Series], always: pd.Series) -> pd.Series:
    if name is None:
        return always
    if name not in feats:
        raise ValueError(f"unknown gate {name}")
    return feats[name].astype(bool)


def _run_stack(market, dividends, target, cool):
    _prices, _sleeve, _t0, regime = e16_features(market)
    _kd, buy_ok, buy, sell = fuse_cut._kd_panels(market, dividends)
    nav, fills, meta = simulate_core(
        market,
        target,
        regime,
        dividends,
        apply_e22=True,
        e22_version=E22_VERSION,
        apply_stock_div=True,
        capital=float(DEFAULT_CAPITAL),
        lot_size=int(BOARD_LOT),
        financial_alloc=FIN_PRE_EXDIV_KD,
        telecom_alloc=TEL_EQUAL,
        fin_name_scores=buy,
        fin_buy_ok=buy_ok,
        fin_sell_scores=sell,
        e45_exposure=cool.astype(float),
    )
    if not bool(meta.get("exact_t1_ok")):
        raise RuntimeError("exact_t1_ok failed")
    return nav, fills, meta


def _family(book_id: str, track: str) -> str:
    if book_id == BASE_ID:
        return "ctrl"
    return track


def _eval_row(
    base_w,
    chal_w,
    tip,
    *,
    book_id,
    track,
    buy_wr,
    sell_wr,
    base_buy_wr,
    base_sell_wr,
):
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
    wr_ok = (buy_pp is not None and float(buy_pp) >= WR_FLOOR_PP) or (
        sell_pp is not None and float(sell_pp) >= WR_FLOOR_PP
    )
    economic = bool(cagr_ok and mdd_ok and band_ok and tip_ok)
    fam = _family(book_id, track)
    hit = bool(economic and wr_ok and fam in ("reg", "det") and book_id != BASE_ID)
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
        "family": fam,
        "track": track,
        "gates": {
            "cagr": bool(cagr_ok),
            "mdd_near_flat": bool(mdd_ok),
            "mdd_band": bool(band_ok),
            "tip_safe": bool(tip_ok),
            "wr_either": bool(wr_ok),
            "economic": economic,
        },
        "hit": hit,
        "cagr_sign": "chal_minus_base",
    }


def _verdict(rows: list[dict[str, Any]]) -> str:
    chal = [r for r in rows if r["id"] != BASE_ID]
    if any(r["eval"]["hit"] for r in chal):
        return "REGIME_DETECTOR_HIT"
    if any(r["eval"]["gates"]["economic"] and not r["eval"]["gates"]["wr_either"] for r in chal):
        return "WIN_SOFT"
    if any(r["eval"]["gates"]["economic"] for r in chal):
        return "WIN_SOFT"
    if any(r["eval"]["gates"]["cagr"] and not r["eval"]["gates"]["tip_safe"] for r in chal):
        return "TIP_BLOCK"
    tip_ok_cagr_short = [
        r
        for r in chal
        if r["eval"]["gates"]["tip_safe"]
        and r["eval"]["gates"]["mdd_near_flat"]
        and r["eval"]["gates"]["mdd_band"]
        and not r["eval"]["gates"]["cagr"]
        and (r["eval"]["held_cagr_lift_pp"] or 0) > 0
    ]
    if tip_ok_cagr_short:
        return "CAGR_SOFT"
    if any(r["eval"]["gates"]["cagr"] and not r["eval"]["gates"]["mdd_near_flat"] for r in chal):
        return "MDD_BLOCK"
    return "NO_EDGE"


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    assert abs(SELL_AMP - 0.75) < 1e-12

    print("loading market ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    cal = pd.DatetimeIndex(pd.to_datetime(sorted(market["date"].unique())))

    print("base FUSE offense + COOL + regime ...", flush=True)
    fuse_nav, _, _ = fuse_cut.build_fuse_offense_sim(market, dividends)
    cool = cool_cut.build_cool_exposure_from_offense(market, fuse_nav)
    cool.to_frame("cool_exposure").to_csv(OUT / "cool_from_fuse.csv")
    base_target = fuse_cut.fuse_target_for_market(market)
    _p, _sleeve, _t, regime = e16_features(market)
    regime = regime.reindex(cal).ffill().fillna("Sideways")
    regime.to_frame("regime").to_csv(OUT / "live_regime.csv")

    closes = close_panel(market, cal, [CODE])[CODE].astype(float)
    feats = _feats(closes, regime)
    always = pd.Series(True, index=cal)

    rows: list[dict[str, Any]] = []
    base_nav = None
    base_w = None
    base_buy_wr = None
    base_sell_wr = None
    code_set = {CODE}

    for spec in GRID:
        bid = str(spec["id"])
        track = str(spec["track"])
        buy_ok = _gate_series(spec.get("buy"), feats, always)
        sell_ok = _gate_series(spec.get("sell"), feats, always)
        if bid == BASE_ID:
            tgt = base_target
        else:
            tgt = apply_etf_delta_scale(base_target, buy_ok, sell_ok, damp=0.0)
        print(f"{bid} ...", flush=True)
        nav, fills, meta = _run_stack(market, dividends, tgt, cool)
        nav.to_csv(OUT / f"nav_{bid}.csv", index=False)
        w = _pack(nav)
        buy_wr = forward_win_stats(fills, closes.to_frame(CODE), codes=code_set, side="BUY", horizon=WIN_H)
        sell_wr = forward_sell_win_stats(fills, closes.to_frame(CODE), codes=code_set, horizon=WIN_H)
        if bid == BASE_ID:
            base_nav = nav
            base_w = w
            base_buy_wr = buy_wr
            base_sell_wr = sell_wr
            tip = {
                "ytd": {"mdd_improve_pp": 0.0, "cagr_lift_pp": 0.0, "gate": "PASS"},
                "trailing_1y": {"mdd_improve_pp": 0.0, "cagr_lift_pp": 0.0, "gate": "PASS"},
            }
        else:
            assert base_nav is not None and base_w is not None
            tip = _tip(base_nav, nav)
        ev = _eval_row(
            base_w or w,
            w,
            tip,
            book_id=bid,
            track=track,
            buy_wr=buy_wr,
            sell_wr=sell_wr,
            base_buy_wr=base_buy_wr,
            base_sell_wr=base_sell_wr,
        )
        rows.append(
            {
                "id": bid,
                "track": track,
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
    payload = {
        "label": f"{SCREEN_ID}_{generated.replace(':', '').replace('-', '')}",
        "generated_at_utc": generated,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "status": "STAGE_A_SCREEN_DONE",
        "verdict": verdict,
        "live_wire": False,
        "soft_frozen_keep": True,
        "sell_a75_keep": True,
        "beta_clip_keep": True,
        "cagr_sign": "chal_minus_base",
        "parents": ["1d_TIP_BLOCK", "1e_TIP_BLOCK", "1c_ASYMM_CAGR_SOFT"],
        "base_id": BASE_ID,
        "gates": {
            "held_cagr_lift_pp": CAGR_FLOOR_PP,
            "held_mdd_pp_floor": HELD_MDD_MIN_PP,
            "held_abs_mdd_max": HELD_ABS_MDD_MAX,
            "tip_mdd_pp_floor": TIP_MDD_MIN_PP,
            "wr_either_pp": WR_FLOOR_PP,
            "win_horizon": WIN_H,
        },
        "books": [
            {
                "id": r["id"],
                "track": r["track"],
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
    }
    screen_md = "\n".join(
        [
            f"# {SCREEN_ID}",
            "",
            f"Date: 2026-09-28 · Generated `{generated}`",
            f"Status: **{verdict}** · Soft-Frozen **KEEP** · β clip **KEEP** · SELL_a75 **KEEP** · live wire **false**",
            "",
            "Tracks: **REG** live Bull/Bear/Crisis/Side · **DET** 0050 MA60/MACD · CAGR↑=chal−base · no clip densify.",
            "",
            "## Books",
            "",
            "| ID | track | CAGR↑pp | MDD↑pp | tip↑ | buyWR↑ | sellWR↑ | HIT |",
            "|---|---|---:|---:|---:|---:|---:|---|",
        ]
        + [
            "| {id} | {tr} | {cagr} | {mdd} | {ytd} | {bwr} | {swr} | {hit} |".format(
                id=r["id"],
                tr=r["track"],
                cagr=r["eval"]["held_cagr_lift_pp"],
                mdd=r["eval"]["held_mdd_pp"],
                ytd=r["eval"]["tip_ytd_mdd_pp"],
                bwr=r["eval"]["buy_win_rate_pp"],
                swr=r["eval"]["sell_win_rate_pp"],
                hit=r["eval"]["hit"],
            )
            for r in rows
        ]
        + ["", f"Verdict: **`{verdict}`**", "", f"Label: `{SCREEN_ID}_2026-09-28__{verdict}`", ""]
    )

    best = next((r for r in rows if r["eval"]["hit"]), None)
    econ = [r for r in rows if r["id"] != BASE_ID and r["eval"]["gates"]["economic"]]
    econ.sort(key=lambda r: float(r["eval"]["held_cagr_lift_pp"] or -9), reverse=True)
    tip_block_cagr = [
        r
        for r in rows
        if r["id"] != BASE_ID and r["eval"]["gates"]["cagr"] and not r["eval"]["gates"]["tip_safe"]
    ]
    tip_block_cagr.sort(key=lambda r: float(r["eval"]["held_cagr_lift_pp"] or -9), reverse=True)

    dlines = [
        f"# {DECISION_ID}",
        "",
        f"Date: 2026-09-28 · Generated `{generated}`",
        f"Status: **{verdict}** · Soft-Frozen **KEEP** · β clip **KEEP** · SELL_a75 **KEEP** · live wire **false**",
        "",
        f"Charter: `{CHARTER_ID}.md`",
        f"Screen: `{SCREEN_ID}.md`",
        "Parents: `1d`/`1e` TIP_BLOCK · `1c` ASYMM densify CLOSED",
        "",
        "## Verdict",
        "",
        f"**`{verdict}`**",
        "",
        "CAGR sign: **chal − base**. REG=live regime · DET=0050 local MA60/MACD.",
        "",
    ]
    if best:
        dlines += [
            (
                f"Best HIT: `{best['id']}` · CAGR↑ {best['eval']['held_cagr_lift_pp']}pp · "
                f"MDD↑ {best['eval']['held_mdd_pp']}pp · tip↑ {best['eval']['tip_ytd_mdd_pp']}"
            ),
            "",
        ]
    elif econ:
        top = econ[0]
        dlines += [
            (
                f"Best economic: `{top['id']}` · CAGR↑ {top['eval']['held_cagr_lift_pp']}pp · "
                f"MDD↑ {top['eval']['held_mdd_pp']}pp"
            ),
            "",
        ]
    elif tip_block_cagr:
        top = tip_block_cagr[0]
        dlines += [
            (
                f"Best CAGR / tip-fail: `{top['id']}` · CAGR↑ {top['eval']['held_cagr_lift_pp']}pp · "
                f"tip↑ {top['eval']['tip_ytd_mdd_pp']}"
            ),
            "",
        ]
    else:
        dlines += ["No book cleared economic gates.", ""]

    dlines += [
        "## Binding",
        "",
        "1. Soft-Frozen β clip / Exact T+1 / **SELL_a75** KEEP",
        "2. Even HIT → paper observe ballot only",
        "3. Do **not** reopen ASYMM clip densify or `1d`/`1e` identical grids",
        "4. Do not expand this finite regime/detector grid after peek",
        "",
        f"Label: `{DECISION_ID}_2026-09-28__{verdict}__NO_LIVE`",
        "",
    ]
    decision = {
        "label": f"{DECISION_ID}_2026-09-28__{verdict}__NO_LIVE",
        "status": verdict,
        "live_wire": False,
        "soft_frozen_keep": True,
        "sell_a75_keep": True,
        "beta_clip_keep": True,
        "cagr_sign": "chal_minus_base",
        "charter": f"research/ops/{CHARTER_ID}.md",
        "screen": f"research/ops/{SCREEN_ID}.md",
        "best_hit": None if best is None else best["id"],
        "best_economic": None if not econ else econ[0]["id"],
        "best_cagr_tip_fail": None if not tip_block_cagr else tip_block_cagr[0]["id"],
        "generated_at_utc": generated,
    }

    write_ops_and_repro_pointer(OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", screen_md, kind="screen")
    write_ops_and_repro_pointer(
        OPS / f"{SCREEN_ID}.json",
        REP / f"{SCREEN_ID}.json",
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        kind="screen",
    )
    write_ops_and_repro_pointer(OPS / f"{DECISION_ID}.md", REP / f"{DECISION_ID}.md", "\n".join(dlines))
    write_ops_and_repro_pointer(
        OPS / f"{DECISION_ID}.json",
        REP / f"{DECISION_ID}.json",
        json.dumps(decision, indent=2, ensure_ascii=False) + "\n",
    )

    for path, repl_open, repl_done in (
        (OPS / f"{CHARTER_ID}.md", "Status: **Stage A OPEN**", f"Status: **Stage A DONE — `{verdict}`**"),
        (OPS / f"{CHARTER_ID}.zh-TW.md", "狀態：**Stage A OPEN**", f"狀態：**Stage A DONE — `{verdict}`**"),
    ):
        if path.exists():
            body = path.read_text(encoding="utf-8")
            body = body.replace(repl_open, repl_done, 1)
            body = body.replace(
                f"{CHARTER_ID}_2026-09-28__OPEN__NO_LIVE_WIRE",
                f"{CHARTER_ID}_2026-09-28__DONE_{verdict}__NO_LIVE_WIRE",
            )
            path.write_text(body, encoding="utf-8")
    cj_path = OPS / f"{CHARTER_ID}.json"
    if cj_path.exists():
        cj = json.loads(cj_path.read_text(encoding="utf-8"))
        cj["status"] = "STAGE_A_DONE"
        cj["verdict"] = verdict
        cj["label"] = f"{CHARTER_ID}_2026-09-28__DONE_{verdict}__NO_LIVE_WIRE"
        cj["screen"] = f"research/ops/{SCREEN_ID}.md"
        cj["decision"] = f"research/ops/{DECISION_ID}.md"
        cj_path.write_text(json.dumps(cj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps({"verdict": verdict, "n_books": len(rows)}, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
