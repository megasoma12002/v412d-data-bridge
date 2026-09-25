#!/usr/bin/env python3
"""Within-sleeve FinPub/TEL micro under COOL — Stage A (paper only).

Charter: research/ops/WITHIN_SLEEVE_COOL_MICRO_STAGEA_CHARTER.md
Soft-Frozen clips KEEP · live KD_OPT/TEL_EQUAL as base · no live wire.
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
    TEL_EXDIV_SKIP_BUY,
    TEL_MIN_LOT_PACK,
    TEL_RS_SOFT_TILT,
    build_kd_season_tilt_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "within-sleeve-cool-micro-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "WITHIN_SLEEVE_COOL_MICRO_STAGEA_CHARTER"
SCREEN_ID = "WITHIN_SLEEVE_COOL_MICRO_STAGEA_SCREEN"
HELDOUT = "heldout_2019_plus"
E22_VERSION = e22div.DEFAULT_BOOKS_VERSION
BASE_ID = "BASE_LIVE_FUSE_COOL"
MDD_FLOOR = -0.15
CAGR_LIFT_PP = 0.20

# (id, season_start, season_end, k_thresh, pre_days) — exclude exact live KD_OPT
FIN_KD_GRID = [
    ("FIN_KD_A15M15_K25_T10", (4, 15), (5, 15), 25.0, 10),
    ("FIN_KD_A15M15_K25_T15", (4, 15), (5, 15), 25.0, 15),
    ("FIN_KD_A15M15_K25_T20", (4, 15), (5, 15), 25.0, 20),
    ("FIN_KD_A15M15_K35_T10", (4, 15), (5, 15), 35.0, 10),
    ("FIN_KD_A15M15_K35_T15", (4, 15), (5, 15), 35.0, 15),
    ("FIN_KD_A15M15_K35_T20", (4, 15), (5, 15), 35.0, 20),
    ("FIN_KD_MAY_K25_T15", (5, 1), (5, 31), 25.0, 15),
    ("FIN_KD_MAY_K30_T15", (5, 1), (5, 31), 30.0, 15),
    ("FIN_KD_A01M15_K30_T10", (4, 1), (5, 15), 30.0, 10),
    ("FIN_KD_A01M15_K30_T15", (4, 1), (5, 15), 30.0, 15),
]
TEL_GRID = [
    ("TEL_RS_SOFT_TILT", TEL_RS_SOFT_TILT),
    ("TEL_MIN_LOT_PACK", TEL_MIN_LOT_PACK),
    ("TEL_EXDIV_SKIP_BUY", TEL_EXDIV_SKIP_BUY),
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


def _sim(
    market,
    target,
    regime,
    dividends,
    *,
    scores,
    buy_ok,
    sell=None,
    exposure=None,
    financial_alloc=FIN_PRE_EXDIV_KD,
    telecom_alloc=TEL_EQUAL,
):
    kw: dict[str, Any] = dict(
        apply_e22=True,
        apply_stock_div=True,
        capital=float(DEFAULT_CAPITAL),
        lot_size=int(BOARD_LOT),
        financial_alloc=financial_alloc,
        telecom_alloc=telecom_alloc,
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


def _buy(kd, lows, k9_amp: float = 1.0) -> pd.DataFrame:
    out = soft_boost_scores(kd, lows[BUY_LOW_ID], 1.0)
    return soft_boost_scores(out, lows["K9_LT30"], float(k9_amp))


def _sell(highs, amp: float = 0.50) -> pd.DataFrame:
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


def _row(base_w, chal_w, tip, *, rid, track, meta, n_fills):
    h = chal_w[HELDOUT]
    b = base_w[HELDOUT]
    gb = cagr_delta_pp(b.get("cagr"), h.get("cagr"), missing_as_zero=True)
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
    mdd_flat = float(md) >= 0.0
    return {
        "id": rid,
        "track": track,
        "meta": meta,
        "n_fills": n_fills,
        "windows": chal_w,
        "held_cagr_lift_pp": lift,
        "held_mdd_improve_pp": round(float(md), 4),
        "in_mdd_band": bool(in_band),
        "tip": tip,
        "tip_ok": bool(tip_ok),
        "cagr_hit": bool(cagr_hit),
        "mdd_flat": bool(mdd_flat),
        "flat_cagr": bool(mdd_flat and cagr_hit and in_band),
        "hit": bool(mdd_flat and cagr_hit and in_band and tip_ok),
    }


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.8]
    assert soft.SOFT_FROZEN_ETF_CLIP == [0.0, 0.5]
    # live KD_OPT must not appear in FIN grid
    live_tuple = (
        tuple(LIVE_KD["season_start"]),
        tuple(LIVE_KD["season_end"]),
        float(LIVE_KD["k_thresh"]),
        int(LIVE_KD["pre_days"]),
    )
    for _id, ss, se, k, pre in FIN_KD_GRID:
        assert (ss, se, float(k), int(pre)) != live_tuple, _id

    print(f"grid FIN={len(FIN_KD_GRID)} TEL={len(TEL_GRID)}", flush=True)
    print("loading ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, sleeve, _tgt, regime = e16_features(market)
    cal = pd.DatetimeIndex(pd.to_datetime(market["date"]).drop_duplicates().sort_values())
    lows, highs = build_low_high_catalog(market, cal, list(FIN))
    score_live = _sleeve_score(market, sleeve, float(LIVE_SLEEVE_ALPHA))
    tgt_live = _target_live(score_live, regime)
    sell_live = _sell(highs)

    # Live KD scores for base + TEL track
    kd_live = build_kd_season_tilt_scores(
        market,
        dividends,
        FIN,
        k_thresh=float(LIVE_KD["k_thresh"]),
        season_start=LIVE_KD["season_start"],
        season_end=LIVE_KD["season_end"],
        pre_days=int(LIVE_KD["pre_days"]),
        active_score=float(LIVE_KD["active_score"]),
    )
    buy_ok_live = build_pre_exdiv_window_buy_ok(
        cal, dividends, FIN, pre_days=int(LIVE_KD["pre_days"]), also_stock_ex=True
    )
    buy_live = _buy(kd_live, lows)

    print("offense NAV for BASE cool ...", flush=True)
    fuse_off, _ = _sim(
        market, tgt_live, regime, dividends, scores=buy_live, buy_ok=buy_ok_live, sell=sell_live
    )
    cool = _cool_from_offense(market, fuse_off)
    cool.to_frame("e45_exposure").to_csv(OUT / "exposure_cool_from_fuse.csv")

    print(f"{BASE_ID} ...", flush=True)
    base_nav, _ = _sim(
        market,
        tgt_live,
        regime,
        dividends,
        scores=buy_live,
        buy_ok=buy_ok_live,
        sell=sell_live,
        exposure=cool,
    )
    base_w = _pack(base_nav)
    base_nav.to_csv(OUT / f"nav_{BASE_ID}.csv", index=False)

    rows = []
    n_total = len(FIN_KD_GRID) + len(TEL_GRID)
    i = 0
    for rid, ss, se, k, pre in FIN_KD_GRID:
        i += 1
        print(f"  [{i}/{n_total}] {rid} ...", flush=True)
        kd = build_kd_season_tilt_scores(
            market,
            dividends,
            FIN,
            k_thresh=float(k),
            season_start=ss,
            season_end=se,
            pre_days=int(pre),
            active_score=float(LIVE_KD["active_score"]),
        )
        buy_ok = build_pre_exdiv_window_buy_ok(
            cal, dividends, FIN, pre_days=int(pre), also_stock_ex=True
        )
        buy = _buy(kd, lows)
        off, _ = _sim(market, tgt_live, regime, dividends, scores=buy, buy_ok=buy_ok, sell=sell_live)
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
        nav.to_csv(OUT / f"nav_{rid}.csv", index=False)
        rows.append(
            _row(
                base_w,
                _pack(nav),
                _tip(base_nav, nav),
                rid=rid,
                track="FIN_KD_MICRO",
                meta={"season_start": list(ss), "season_end": list(se), "k_thresh": k, "pre_days": pre},
                n_fills=nf,
            )
        )

    for rid, tel_pol in TEL_GRID:
        i += 1
        print(f"  [{i}/{n_total}] {rid} ...", flush=True)
        off, _ = _sim(
            market,
            tgt_live,
            regime,
            dividends,
            scores=buy_live,
            buy_ok=buy_ok_live,
            sell=sell_live,
            telecom_alloc=tel_pol,
        )
        exp = _cool_from_offense(market, off)
        nav, nf = _sim(
            market,
            tgt_live,
            regime,
            dividends,
            scores=buy_live,
            buy_ok=buy_ok_live,
            sell=sell_live,
            exposure=exp,
            telecom_alloc=tel_pol,
        )
        nav.to_csv(OUT / f"nav_{rid}.csv", index=False)
        rows.append(
            _row(
                base_w,
                _pack(nav),
                _tip(base_nav, nav),
                rid=rid,
                track="TEL_MICRO",
                meta={"telecom_alloc": tel_pol},
                n_fills=nf,
            )
        )

    hits = [r for r in rows if r["hit"]]
    flat_tip_fail = [r for r in rows if r["flat_cagr"] and not r["tip_ok"]]
    soft_cagr = [
        r
        for r in rows
        if r["mdd_flat"]
        and r["tip_ok"]
        and r["in_mdd_band"]
        and not r["cagr_hit"]
        and r["held_cagr_lift_pp"] is not None
        and float(r["held_cagr_lift_pp"]) > 0
    ]
    if hits:
        verdict = "WITHIN_SLEEVE_MICRO_HIT"
    elif flat_tip_fail:
        verdict = "HELD_FLAT_TIP_FAIL"
    elif soft_cagr:
        verdict = "CAGR_SOFT"
    else:
        verdict = "NO_FLAT_LIFT"

    payload = {
        "generated_at_utc": _utc(),
        "label": SCREEN_ID,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "status": verdict,
        "live_wire": False,
        "soft_frozen_keep": True,
        "baseline": BASE_ID,
        "baseline_windows": base_w,
        "n_challengers": len(rows),
        "n_hits": len(hits),
        "hit_ids": [r["id"] for r in hits],
        "soft_ids": [r["id"] for r in soft_cagr],
        "ranked": sorted(
            rows,
            key=lambda r: (
                -int(r["hit"]),
                -int(r["flat_cagr"]),
                -float(r["held_cagr_lift_pp"] or -9),
                -float(r["held_mdd_improve_pp"]),
            ),
        ),
    }
    (REP / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2) + "\n")
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2) + "\n")

    lines = [
        "# Within-sleeve COOL micro — Stage A Screen",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Verdict: **`{verdict}`** · base `{BASE_ID}` · Soft-Frozen KEEP · **no live wire**",
        "",
        f"Hits: `{[r['id'] for r in hits]}`",
        f"Held-flat tip-fail: `{[r['id'] for r in flat_tip_fail]}`",
        f"CAGR soft: `{[r['id'] for r in soft_cagr]}`",
        "",
        "| id | track | CAGR lift | MDD↑ | band | tip | flat+cagr | hit |",
        "|---|---|---:|---:|:---:|:---:|:---:|:---:|",
    ]
    for r in payload["ranked"]:
        lines.append(
            f"| `{r['id']}` | {r['track']} | {r['held_cagr_lift_pp']:+.2f}pp | "
            f"{r['held_mdd_improve_pp']:+.2f}pp | "
            f"{'Y' if r['in_mdd_band'] else 'N'} | {'Y' if r['tip_ok'] else 'N'} | "
            f"{'Y' if r['flat_cagr'] else 'N'} | {'Y' if r['hit'] else 'N'} |"
        )
    lines += [
        "",
        f"Repro: `PYTHONPATH=scripts python3 scripts/within_sleeve_cool_micro_stagea.py`",
        "",
        f"Label: `{SCREEN_ID}_{payload['generated_at_utc'][:10]}__{verdict}`",
        "",
    ]
    md = "\n".join(lines)
    (REP / f"{SCREEN_ID}.md").write_text(md)
    (OPS / f"{SCREEN_ID}.md").write_text(md)

    decision = {
        "label": "WITHIN_SLEEVE_COOL_MICRO_DECISION",
        "generated_at_utc": _utc(),
        "status": verdict,
        "live_wire": False,
        "n_hits": len(hits),
        "hit_ids": [r["id"] for r in hits],
        "soft_ids": [r["id"] for r in soft_cagr],
        "best": hits[0]["id"] if hits else (soft_cagr[0]["id"] if soft_cagr else None),
        "charter": f"research/ops/{CHARTER_ID}.md",
        "stage_a": f"research/ops/{SCREEN_ID}.md",
    }
    dlines = [
        "# Within-sleeve COOL micro — Decision Pack (Stage A)",
        "",
        f"Date: 2026-09-25 · Generated `{decision['generated_at_utc']}`",
        f"Status: **{verdict}** · Soft-Frozen **KEEP** · live wire **false**",
        "",
        f"HIT: **{len(hits)}** · SOFT CAGR: **{len(soft_cagr)}** / {len(rows)}.",
        "",
    ]
    if hits:
        b = hits[0]
        dlines.append(
            f"Best: `{b['id']}` · CAGR↑ {b['held_cagr_lift_pp']:+.2f} · MDD↑ {b['held_mdd_improve_pp']:+.2f}"
        )
    elif soft_cagr:
        b = soft_cagr[0]
        dlines.append(
            f"Best SOFT: `{b['id']}` · CAGR↑ {b['held_cagr_lift_pp']:+.2f} · MDD↑ {b['held_mdd_improve_pp']:+.2f}"
        )
    else:
        dlines.append("No MDD-flat + CAGR≥+0.20 under predeclared micro grid.")
    dlines += ["", f"Label: `WITHIN_SLEEVE_COOL_MICRO_DECISION_2026-09-25__{verdict}`", ""]
    (OPS / "WITHIN_SLEEVE_COOL_MICRO_DECISION_PACK.json").write_text(json.dumps(decision, indent=2) + "\n")
    (OPS / "WITHIN_SLEEVE_COOL_MICRO_DECISION_PACK.md").write_text("\n".join(dlines))
    (REP / "WITHIN_SLEEVE_COOL_MICRO_DECISION_PACK.json").write_text(json.dumps(decision, indent=2) + "\n")
    (REP / "WITHIN_SLEEVE_COOL_MICRO_DECISION_PACK.md").write_text("\n".join(dlines))
    print(json.dumps({"verdict": verdict, "n_hits": len(hits), "n_soft": len(soft_cagr)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
