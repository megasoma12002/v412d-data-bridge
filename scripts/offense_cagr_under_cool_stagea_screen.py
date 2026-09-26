#!/usr/bin/env python3
"""Offense CAGR under frozen COOL_c8 — Stage A paper screen.

Base: live twin Soft+Sleeve+COOL. Soft-Frozen clip KEEP · no live wire.
Tracks: SLEEVE_ALPHA · SOFT_SELL_AMP · SOFT_BUY_AMP · FUSE_SHAPE.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

import e16_soft_frozen_base as soft
import e22_dividend_accounting as e22div
import e45_defend_handoff_stagea_screen as stagea
from cool_c8_proxy_observe_helpers import build_cool_c8_exposure
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, load_market, window_stats
from e50_early_stack_combined_nav import FIN, e16_features, simulate_core
from portfolio_capital import DEFAULT_CAPITAL
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp
from sleeve_tilt_helpers import (
    ALPHA as LIVE_SLEEVE_ALPHA,
    rebuild_targets_from_score,
    sleeve_signal_panel,
)
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
REPRO = ROOT / "repro" / "offense-cagr-under-cool-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "OFFENSE_CAGR_UNDER_COOL_STAGEA_CHARTER"
SCREEN_ID = "OFFENSE_CAGR_UNDER_COOL_STAGEA_SCREEN"
HELDOUT = "heldout_2019_plus"
E22_VERSION = e22div.DEFAULT_BOOKS_VERSION
BASE_ID = "BASE_FUSE_COOL"
MDD_FLOOR = -0.15
CAGR_LIFT_PP = 0.20

SLEEVE_ALPHAS = (0.15, 0.20, 0.225, 0.25, 0.30)
SELL_AMPS = (0.25, 0.50, 0.75, 1.00)
BUY_AMPS = (0.80, 1.00, 1.20, 1.50)  # K9_LT30 additive boost (a10=1.0)


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


def _sim(market, target, regime, dividends, *, scores, buy_ok, sell=None, exposure=None):
    kw: dict[str, Any] = dict(
        apply_e22=True,
        apply_stock_div=True,
        capital=float(DEFAULT_CAPITAL),
        lot_size=int(BOARD_LOT),
        financial_alloc=FIN_PRE_EXDIV_KD,
        telecom_alloc=TEL_EQUAL,
        fin_name_scores=scores,
        fin_buy_ok=buy_ok,
        e22_version=E22_VERSION,
    )
    if sell is not None:
        kw["fin_sell_scores"] = sell
    if exposure is not None:
        kw["e45_exposure"] = exposure.astype(float)
    nav, fills, meta = simulate_core(market, target, regime, dividends, **kw)
    if not bool(meta.get("exact_t1_ok")):
        raise RuntimeError("exact_t1_ok failed")
    return nav, int(len(fills))


def _cool_from_offense(market, offense_nav: pd.DataFrame) -> pd.Series:
    nav_s = stagea._nav_series(offense_nav)
    feat = stagea._risk_features(market, nav_s)
    dates = pd.DatetimeIndex(nav_s.index)
    return build_cool_c8_exposure(dates, feat["proxy_mdd63"])


def _sleeve_target(market, sleeve, regime, alpha: float) -> pd.DataFrame:
    _p, _s, _t, _r, base_score = soft.build_soft_frozen_targets(market)
    tilt = sleeve_signal_panel(sleeve, "rsi_lt30", 14)
    new_score = base_score + float(alpha) * tilt
    return rebuild_targets_from_score(new_score, regime)


def _buy(kd, lows, k9_amp: float) -> pd.DataFrame:
    out = soft_boost_scores(kd, lows[BUY_LOW_ID], 1.0)
    return soft_boost_scores(out, lows["K9_LT30"], float(k9_amp))


def _sell(highs, amp: float) -> pd.DataFrame:
    return soft_sell_panel(highs[SELL_HIGH_ID], boost=float(amp))


def _row(base_w, chal_w, tip, nav, n_fills, rid, track, meta):
    h = chal_w[HELDOUT]
    b = base_w[HELDOUT]
    gb = cagr_delta_pp(b.get("cagr"), h.get("cagr"), missing_as_zero=True)
    # giveback = base - chal; lift_pp = chal - base = -gb
    lift = None if gb is None else round(-float(gb), 4)
    md = mdd_delta_pp(b.get("max_drawdown"), h.get("max_drawdown"))
    tip_ok = (
        tip.get("ytd", {}).get("gate") == "PASS"
        and tip.get("trailing_1y", {}).get("gate") == "PASS"
        and float(tip["ytd"].get("mdd_improve_pp") or -9) >= 0
        and float(tip["trailing_1y"].get("mdd_improve_pp") or -9) >= 0
    )
    mdd = h.get("max_drawdown")
    in_band = mdd is not None and float(mdd) >= float(MDD_FLOOR)
    cagr_hit = lift is not None and float(lift) >= float(CAGR_LIFT_PP)
    return {
        "id": rid,
        "track": track,
        "meta": meta,
        "n_fills": n_fills,
        "windows": chal_w,
        "held_cagr": h.get("cagr"),
        "held_mdd": mdd,
        "held_cagr_lift_pp": lift,
        "held_mdd_improve_pp": round(float(md), 4),
        "in_mdd_band": bool(in_band),
        "tip": tip,
        "tip_ok": bool(tip_ok),
        "cagr_hit": bool(cagr_hit),
    }


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.9]

    print("loading ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, sleeve, target_live, regime = e16_features(market)
    cal = pd.DatetimeIndex(pd.to_datetime(market["date"]).drop_duplicates().sort_values())
    lows, highs = build_low_high_catalog(market, cal, list(FIN))
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

    buy_live = _buy(kd, lows, 1.0)
    sell_live = _sell(highs, 0.50)
    tgt_live = _sleeve_target(market, sleeve, regime, float(LIVE_SLEEVE_ALPHA))

    print("CTRL_FUSE_ONLY (offense ceiling) ...", flush=True)
    fuse_off, _ = _sim(
        market, tgt_live, regime, dividends, scores=buy_live, buy_ok=buy_ok, sell=sell_live
    )
    cool = _cool_from_offense(market, fuse_off)
    cool.to_frame("e45_exposure").to_csv(OUT / "exposure_cool_from_fuse.csv")

    books: dict[str, Any] = {}
    print("BASE_FUSE_COOL ...", flush=True)
    base_nav, n_base = _sim(
        market,
        tgt_live,
        regime,
        dividends,
        scores=buy_live,
        buy_ok=buy_ok,
        sell=sell_live,
        exposure=cool,
    )
    books[BASE_ID] = {"nav": base_nav, "n_fills": n_base, "track": "CTRL", "meta": {}}
    base_w = _pack(base_nav)

    print("CTRL_FUSE_ONLY pack ...", flush=True)
    books["CTRL_FUSE_ONLY"] = {
        "nav": fuse_off,
        "n_fills": None,
        "track": "CTRL",
        "meta": {"cool": False},
    }

    print("CTRL_STACK_COOL ...", flush=True)
    stack_off, _ = _sim(market, target_live, regime, dividends, scores=kd, buy_ok=buy_ok)
    cool_stack = _cool_from_offense(market, stack_off)
    stack_cool, n_sc = _sim(
        market, target_live, regime, dividends, scores=kd, buy_ok=buy_ok, exposure=cool_stack
    )
    books["CTRL_STACK_COOL"] = {
        "nav": stack_cool,
        "n_fills": n_sc,
        "track": "CTRL",
        "meta": {},
    }

    # SLEEVE_ALPHA
    for a in SLEEVE_ALPHAS:
        rid = f"SLEEVE_a{int(round(a * 1000)):04d}"
        if abs(a - float(LIVE_SLEEVE_ALPHA)) < 1e-12:
            continue  # base already
        print(f"  {rid} ...", flush=True)
        tgt = _sleeve_target(market, sleeve, regime, float(a))
        # rebuild cool from this offense
        off, _ = _sim(
            market, tgt, regime, dividends, scores=buy_live, buy_ok=buy_ok, sell=sell_live
        )
        exp = _cool_from_offense(market, off)
        nav, nf = _sim(
            market,
            tgt,
            regime,
            dividends,
            scores=buy_live,
            buy_ok=buy_ok,
            sell=sell_live,
            exposure=exp,
        )
        books[rid] = {
            "nav": nav,
            "n_fills": nf,
            "track": "SLEEVE_ALPHA",
            "meta": {"sleeve_alpha": a},
        }

    # SOFT_SELL_AMP
    for amp in SELL_AMPS:
        if abs(amp - 0.50) < 1e-12:
            continue
        rid = f"SELL_a{int(round(amp * 100)):02d}"
        print(f"  {rid} ...", flush=True)
        sell = _sell(highs, amp)
        off, _ = _sim(
            market, tgt_live, regime, dividends, scores=buy_live, buy_ok=buy_ok, sell=sell
        )
        exp = _cool_from_offense(market, off)
        nav, nf = _sim(
            market,
            tgt_live,
            regime,
            dividends,
            scores=buy_live,
            buy_ok=buy_ok,
            sell=sell,
            exposure=exp,
        )
        books[rid] = {
            "nav": nav,
            "n_fills": nf,
            "track": "SOFT_SELL_AMP",
            "meta": {"sell_amp": amp},
        }

    # SOFT_BUY_AMP
    for amp in BUY_AMPS:
        if abs(amp - 1.00) < 1e-12:
            continue
        rid = f"BUY_k9_a{int(round(amp * 100)):02d}"
        print(f"  {rid} ...", flush=True)
        buy = _buy(kd, lows, amp)
        off, _ = _sim(
            market, tgt_live, regime, dividends, scores=buy, buy_ok=buy_ok, sell=sell_live
        )
        exp = _cool_from_offense(market, off)
        nav, nf = _sim(
            market,
            tgt_live,
            regime,
            dividends,
            scores=buy,
            buy_ok=buy_ok,
            sell=sell_live,
            exposure=exp,
        )
        books[rid] = {
            "nav": nav,
            "n_fills": nf,
            "track": "SOFT_BUY_AMP",
            "meta": {"k9_amp": amp},
        }

    # FUSE_SHAPE
    print("  FUSE_SHAPE soft-only / sleeve-only / half ...", flush=True)
    soft_only_tgt = target_live
    off_s, _ = _sim(
        market,
        soft_only_tgt,
        regime,
        dividends,
        scores=buy_live,
        buy_ok=buy_ok,
        sell=sell_live,
    )
    exp_s = _cool_from_offense(market, off_s)
    nav_s, nf_s = _sim(
        market,
        soft_only_tgt,
        regime,
        dividends,
        scores=buy_live,
        buy_ok=buy_ok,
        sell=sell_live,
        exposure=exp_s,
    )
    books["SHAPE_SOFT_ONLY_COOL"] = {
        "nav": nav_s,
        "n_fills": nf_s,
        "track": "FUSE_SHAPE",
        "meta": {"shape": "soft_only"},
    }

    off_v, _ = _sim(market, tgt_live, regime, dividends, scores=kd, buy_ok=buy_ok)
    exp_v = _cool_from_offense(market, off_v)
    nav_v, nf_v = _sim(
        market, tgt_live, regime, dividends, scores=kd, buy_ok=buy_ok, exposure=exp_v
    )
    books["SHAPE_SLEEVE_ONLY_COOL"] = {
        "nav": nav_v,
        "n_fills": nf_v,
        "track": "FUSE_SHAPE",
        "meta": {"shape": "sleeve_only"},
    }

    tgt_half = _sleeve_target(market, sleeve, regime, float(LIVE_SLEEVE_ALPHA) * 0.5)
    off_h, _ = _sim(
        market, tgt_half, regime, dividends, scores=buy_live, buy_ok=buy_ok, sell=sell_live
    )
    exp_h = _cool_from_offense(market, off_h)
    nav_h, nf_h = _sim(
        market,
        tgt_half,
        regime,
        dividends,
        scores=buy_live,
        buy_ok=buy_ok,
        sell=sell_live,
        exposure=exp_h,
    )
    books["SHAPE_FUSE_HALF_COOL"] = {
        "nav": nav_h,
        "n_fills": nf_h,
        "track": "FUSE_SHAPE",
        "meta": {"shape": "fuse_half", "sleeve_alpha": float(LIVE_SLEEVE_ALPHA) * 0.5},
    }

    rows = []
    for rid, book in books.items():
        nav = book["nav"]
        nav.to_csv(OUT / f"nav_{rid}.csv", index=False)
        w = _pack(nav)
        tip = _tip(base_nav, nav) if rid != BASE_ID else {
            "ytd": {"mdd_improve_pp": 0.0, "cagr_giveback_pp": 0.0, "gate": "PASS"},
            "trailing_1y": {"mdd_improve_pp": 0.0, "cagr_giveback_pp": 0.0, "gate": "PASS"},
        }
        if rid == BASE_ID:
            rows.append(
                {
                    "id": rid,
                    "track": "CTRL",
                    "meta": {"role": "live_base"},
                    "n_fills": book["n_fills"],
                    "windows": w,
                    "held_cagr": w[HELDOUT]["cagr"],
                    "held_mdd": w[HELDOUT]["max_drawdown"],
                    "held_cagr_lift_pp": 0.0,
                    "held_mdd_improve_pp": 0.0,
                    "in_mdd_band": True,
                    "tip": tip,
                    "tip_ok": True,
                    "cagr_hit": False,
                }
            )
        else:
            rows.append(
                _row(
                    base_w,
                    w,
                    tip,
                    nav,
                    book["n_fills"],
                    rid,
                    book["track"],
                    book["meta"],
                )
            )

    hits = [
        r
        for r in rows
        if r["id"] != BASE_ID and r["cagr_hit"] and r["in_mdd_band"] and r["tip_ok"]
    ]
    soft_hits = [
        r
        for r in rows
        if r["id"] != BASE_ID and r["cagr_hit"] and r["in_mdd_band"] and not r["tip_ok"]
    ]
    tradeoff = [
        r for r in rows if r["id"] != BASE_ID and r["cagr_hit"] and not r["in_mdd_band"]
    ]
    if hits:
        verdict = "OFFENSE_CAGR_HIT"
    elif soft_hits:
        verdict = "OFFENSE_CAGR_SOFT"
    elif tradeoff:
        verdict = "MDD_TRADEOFF"
    else:
        verdict = "NO_LIFT"

    rows_sorted = sorted(
        rows,
        key=lambda r: (
            -(r["held_cagr_lift_pp"] if r["held_cagr_lift_pp"] is not None else -9),
            -(r["held_mdd_improve_pp"] if r["held_mdd_improve_pp"] is not None else -9),
        ),
    )

    payload = {
        "schema_version": "offense_cagr_under_cool_stagea_v1",
        "charter_id": CHARTER_ID,
        "screen_id": SCREEN_ID,
        "generated_at_utc": _utc(),
        "verdict": verdict,
        "live_wire": False,
        "soft_frozen_keep": True,
        "cool_frozen": True,
        "base_id": BASE_ID,
        "targets": {
            "held_cagr_lift_pp_min": CAGR_LIFT_PP,
            "held_mdd_floor": MDD_FLOOR,
            "tip_mdd_improve_min": 0.0,
        },
        "n_books": len(rows),
        "n_hits": len(hits),
        "hit_ids": [r["id"] for r in hits],
        "rows": rows_sorted,
        "non_actions": [
            "No Soft-Frozen clip / tip rewrite",
            "No live Soft/Sleeve/FUSE swap from Stage A",
            "No COOL densify / DH re-enable",
        ],
    }

    def fmt_pct(x):
        return "n/a" if x is None else f"{100.0 * float(x):.2f}%"

    def fmt_pp(x):
        return "n/a" if x is None else f"{float(x):+.2f}pp"

    lines = [
        "# Offense CAGR under COOL — Stage A screen",
        "",
        f"Generated: `{payload['generated_at_utc']}`  ",
        f"Verdict: **`{verdict}`** · base `{BASE_ID}` · Soft-Frozen KEEP · COOL frozen · **no live wire**",
        "",
        f"Hits (≥+{CAGR_LIFT_PP}pp CAGR · |MDD|≤15% · tip OK): `{payload['hit_ids']}`",
        "",
        "## Held-out 2019+ (vs BASE_FUSE_COOL)",
        "",
        "| id | track | CAGR | MDD | CAGR lift | MDD↑ | band | tip |",
        "|---|---|---:|---:|---:|---:|:---:|:---:|",
    ]
    for r in rows_sorted:
        lines.append(
            f"| `{r['id']}` | {r['track']} | {fmt_pct(r['held_cagr'])} | {fmt_pct(r['held_mdd'])} "
            f"| {fmt_pp(r['held_cagr_lift_pp'])} | {fmt_pp(r['held_mdd_improve_pp'])} "
            f"| {'Y' if r['in_mdd_band'] else 'N'} | {'Y' if r['tip_ok'] else 'N'} |"
        )
    lines += [
        "",
        "## Reading",
        "",
        "- Lift = challenger CAGR − base (want ≥ +0.20pp).",
        "- Band = held MDD ≥ −15%.",
        "- Tip = YTD and trailing 1y MDD not worse than base.",
        "- Even HIT → paper observe ballot only.",
        "",
        f"Repro: `repro/offense-cagr-under-cool-stagea/`",
        "",
        f"Label: `{SCREEN_ID}_{_utc()[:10]}__{verdict}__NO_LIVE_WIRE`",
        "",
    ]
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    (OUT / "stagea_summary.json").write_text(text, encoding="utf-8")
    (REP / f"{SCREEN_ID}.json").write_text(text, encoding="utf-8")
    (OPS / f"{SCREEN_ID}.json").write_text(text, encoding="utf-8")
    md = "\n".join(lines) + "\n"
    (REP / f"{SCREEN_ID}.md").write_text(md, encoding="utf-8")
    (OPS / f"{SCREEN_ID}.md").write_text(md, encoding="utf-8")
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
