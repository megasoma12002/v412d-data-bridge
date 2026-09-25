#!/usr/bin/env python3
"""Asymmetric 0050 Bull densify under COOL — Stage A (paper only).

Charter: research/ops/ASYMM_0050_BULL_DENSIFY_UNDER_COOL_STAGEA_CHARTER.md
Densify 0050 only when Bull (or Bull+Sideways); rest keeps live or prior FINBAND.
Soft-Frozen live KEEP · no live wire.
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
    build_kd_season_tilt_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "asymm-0050-bull-densify-under-cool-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "ASYMM_0050_BULL_DENSIFY_UNDER_COOL_STAGEA_CHARTER"
SCREEN_ID = "ASYMM_0050_BULL_DENSIFY_UNDER_COOL_STAGEA_SCREEN"
HELDOUT = "heldout_2019_plus"
E22_VERSION = e22div.DEFAULT_BOOKS_VERSION
BASE_ID = "BASE_LIVE_FUSE_COOL"
MDD_FLOOR = -0.15
CAGR_LIFT_PP = 0.20

LIVE_CLIPS = (
    float(soft.SOFT_FROZEN_FIN_LO),
    float(soft.SOFT_FROZEN_FIN_HI),
    float(soft.SOFT_FROZEN_TEL_LO),
    float(soft.SOFT_FROZEN_TEL_HI),
    float(soft.SOFT_FROZEN_ETF_LO),
    float(soft.SOFT_FROZEN_ETF_HI),
)
# Prior FINBAND (pre β densify flip) — defense restore option.
PRIOR_FINBAND = (0.60, 0.90, 0.03, 0.35, 0.00, 0.35)


def _build_grid() -> list[dict[str, Any]]:
    """Finite predeclared books — do not expand after peek."""
    books: list[dict[str, Any]] = []
    # BULL_E_HI
    for ehi in (0.55, 0.60, 0.65):
        bull = (0.60, 0.80, 0.03, 0.35, 0.00, float(ehi))
        books.append(
            {
                "id": f"ASYMM_BULL_E{ehi:.2f}",
                "track": "BULL_E_HI",
                "gate": "REG_BULL",
                "bull_clips": bull,
                "rest_clips": LIVE_CLIPS,
            }
        )
    # BULL_FIN_ROOM
    for fhi in (0.75, 0.78):
        for ehi in (0.55, 0.60, 0.65):
            bull = (0.60, float(fhi), 0.03, 0.35, 0.00, float(ehi))
            books.append(
                {
                    "id": f"ASYMM_BULL_F{fhi:.2f}_E{ehi:.2f}",
                    "track": "BULL_FIN_ROOM",
                    "gate": "REG_BULL",
                    "bull_clips": bull,
                    "rest_clips": LIVE_CLIPS,
                }
            )
    # BULL_SIDE_FIN_ROOM
    for fhi in (0.75, 0.78):
        for ehi in (0.55, 0.60, 0.65):
            bull = (0.60, float(fhi), 0.03, 0.35, 0.00, float(ehi))
            books.append(
                {
                    "id": f"ASYMM_BSIDE_F{fhi:.2f}_E{ehi:.2f}",
                    "track": "BULL_SIDE_FIN_ROOM",
                    "gate": "REG_BULL_SIDE",
                    "bull_clips": bull,
                    "rest_clips": LIVE_CLIPS,
                }
            )
    # BULL_OFF_DEF_REST
    for fhi in (0.75, 0.78):
        for ehi in (0.55, 0.60):
            bull = (0.60, float(fhi), 0.03, 0.35, 0.00, float(ehi))
            books.append(
                {
                    "id": f"ASYMM_BULL_DEF_F{fhi:.2f}_E{ehi:.2f}",
                    "track": "BULL_OFF_DEF_REST",
                    "gate": "REG_BULL",
                    "bull_clips": bull,
                    "rest_clips": PRIOR_FINBAND,
                }
            )
    return books


GRID = _build_grid()


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


def _buy(kd, lows, k9_amp: float = 1.0) -> pd.DataFrame:
    out = soft_boost_scores(kd, lows[BUY_LOW_ID], 1.0)
    return soft_boost_scores(out, lows["K9_LT30"], float(k9_amp))


def _sell(highs, amp: float = 0.50) -> pd.DataFrame:
    return soft_sell_panel(highs[SELL_HIGH_ID], boost=float(amp))


def _sleeve_score(market, sleeve, alpha: float) -> pd.DataFrame:
    _p, _s, _t, _r, base_score = soft.build_soft_frozen_targets(market)
    tilt = sleeve_signal_panel(sleeve, "rsi_lt30", 14)
    return base_score + float(alpha) * tilt


def _gate_mask(regime: pd.Series, gate: str) -> pd.Series:
    rg = regime.astype(str)
    if gate == "REG_BULL":
        return rg == "Bull"
    if gate == "REG_BULL_SIDE":
        return rg.isin(["Bull", "Sideways"])
    raise ValueError(f"unknown gate {gate}")


def build_asymm_targets(
    *,
    regime: pd.Series,
    score: pd.DataFrame,
    gate: str,
    bull_clips: tuple[float, ...],
    rest_clips: tuple[float, ...],
) -> pd.DataFrame:
    """Causal E16 router with regime-conditional clip boxes (continuous blend)."""
    mask = _gate_mask(regime, gate).reindex(score.index).fillna(False)
    flo, fhi, tlo, thi, elo, ehi = bull_clips
    rlo = rest_clips
    bull_lo = np.array([flo, tlo, elo], dtype=float)
    bull_hi = np.array([fhi, thi, ehi], dtype=float)
    rest_lo = np.array([rlo[0], rlo[2], rlo[4]], dtype=float)
    rest_hi = np.array([rlo[1], rlo[3], rlo[5]], dtype=float)
    # Start from live mid-box (stable).
    live_lo = np.array([LIVE_CLIPS[0], LIVE_CLIPS[2], LIVE_CLIPS[4]], dtype=float)
    live_hi = np.array([LIVE_CLIPS[1], LIVE_CLIPS[3], LIVE_CLIPS[5]], dtype=float)
    start = clip.apply_clip_box(
        (live_lo + live_hi) / 2.0, live_lo, live_hi, soft.START_WEIGHTS.copy()
    )
    out = []
    cur = start.copy()
    for i, _dt in enumerate(score.index):
        on = bool(mask.iloc[i])
        lo = bull_lo if on else rest_lo
        hi = bull_hi if on else rest_hi
        pri = soft.REGIME_PRIORS[str(regime.iloc[i])]
        cand = np.maximum(pri + 0.10 * np.clip(score.iloc[i].to_numpy(), -2.0, 2.0), 0.0)
        cand = clip.apply_clip_box(cand, lo, hi, start)
        desired = soft.BLEND_OLD * cur + soft.BLEND_NEW * cand
        desired = clip.apply_clip_box(desired, lo, hi, start)
        if float(np.abs(desired - cur).sum()) >= soft.REBALANCE_L1_MIN:
            cur = desired
        out.append(cur.copy())
    return pd.DataFrame(out, index=score.index, columns=["Financial", "Telecom", "0050"])


def _target_live(score: pd.DataFrame, regime: pd.Series) -> pd.DataFrame:
    return clip.build_targets_with_clips(
        regime=regime,
        score=score,
        fin_lo=LIVE_CLIPS[0],
        fin_hi=LIVE_CLIPS[1],
        tel_lo=LIVE_CLIPS[2],
        tel_hi=LIVE_CLIPS[3],
        etf_lo=LIVE_CLIPS[4],
        etf_hi=LIVE_CLIPS[5],
    )


def _row(base_w, chal_w, tip, *, rid, track, gate, meta, n_fills, mean_tgt, gate_on_frac):
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
        "gate": gate,
        "meta": meta,
        "mean_target": mean_tgt,
        "gate_on_frac": round(float(gate_on_frac), 4),
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
        "mdd_flat": bool(mdd_flat),
        "flat_cagr": bool(mdd_flat and cagr_hit and in_band),
        "hit": bool(mdd_flat and cagr_hit and in_band and tip_ok),
    }


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.8]
    assert soft.SOFT_FROZEN_ETF_CLIP == [0.0, 0.5]
    for book in GRID:
        assert clip.feasible(*book["bull_clips"]), book["id"]
        assert clip.feasible(*book["rest_clips"]), book["id"]

    print(f"grid size={len(GRID)}", flush=True)
    print("loading ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, sleeve, _tgt_live, regime = e16_features(market)
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
    buy_live = _buy(kd, lows)
    sell_live = _sell(highs)
    score_live = _sleeve_score(market, sleeve, float(LIVE_SLEEVE_ALPHA))
    tgt_live = _target_live(score_live, regime)

    print("offense NAV for BASE cool ...", flush=True)
    fuse_off, _ = _sim(
        market, tgt_live, regime, dividends, scores=buy_live, buy_ok=buy_ok, sell=sell_live
    )
    cool = _cool_from_offense(market, fuse_off)
    cool.to_frame("e45_exposure").to_csv(OUT / "exposure_cool_from_fuse.csv")

    print(f"{BASE_ID} ...", flush=True)
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
    base_w = _pack(base_nav)
    base_nav.to_csv(OUT / f"nav_{BASE_ID}.csv", index=False)

    rows = []
    for i, book in enumerate(GRID, 1):
        rid = book["id"]
        print(f"  [{i}/{len(GRID)}] {rid} ...", flush=True)
        tgt = build_asymm_targets(
            regime=regime,
            score=score_live,
            gate=book["gate"],
            bull_clips=book["bull_clips"],
            rest_clips=book["rest_clips"],
        )
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
        nav.to_csv(OUT / f"nav_{rid}.csv", index=False)
        tip = _tip(base_nav, nav)
        mean_tgt = {
            "Financial": round(float(tgt["Financial"].mean()), 4),
            "Telecom": round(float(tgt["Telecom"].mean()), 4),
            "0050": round(float(tgt["0050"].mean()), 4),
        }
        gate_on = float(_gate_mask(regime, book["gate"]).mean())
        rows.append(
            _row(
                base_w,
                _pack(nav),
                tip,
                rid=rid,
                track=book["track"],
                gate=book["gate"],
                meta={
                    "bull_clips": list(book["bull_clips"]),
                    "rest_clips": list(book["rest_clips"]),
                },
                n_fills=nf,
                mean_tgt=mean_tgt,
                gate_on_frac=gate_on,
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
        verdict = "ASYMM_MDD_FLAT_HIT"
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
        "flat_tip_fail_ids": [r["id"] for r in flat_tip_fail],
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

    bh = base_w[HELDOUT]
    lines = [
        "# Asymmetric 0050 Bull densify under COOL — Stage A Screen",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Verdict: **`{verdict}`** · base `{BASE_ID}` · Soft-Frozen KEEP · **no live wire**",
        "",
        f"Base held {100*float(bh.get('cagr') or 0):.2f}% / {100*float(bh.get('max_drawdown') or 0):.2f}%",
        "",
        f"Hits (MDD flat + CAGR + tip): `{[r['id'] for r in hits]}`",
        f"Held-flat tip-fail: `{[r['id'] for r in flat_tip_fail]}`",
        f"CAGR soft (MDD flat + tip, CAGR short): `{[r['id'] for r in soft_cagr]}`",
        "",
        "| id | track | gate | mean 0050 | CAGR lift | MDD↑ | band | tip | flat+cagr | hit |",
        "|---|---|---|---:|---:|---:|:---:|:---:|:---:|:---:|",
    ]
    for r in payload["ranked"]:
        lines.append(
            f"| `{r['id']}` | {r['track']} | {r['gate']} | "
            f"{100*float(r['mean_target']['0050']):.1f}% | "
            f"{r['held_cagr_lift_pp']:+.2f}pp | {r['held_mdd_improve_pp']:+.2f}pp | "
            f"{'Y' if r['in_mdd_band'] else 'N'} | "
            f"{'Y' if r['tip_ok'] else 'N'} | "
            f"{'Y' if r['flat_cagr'] else 'N'} | "
            f"{'Y' if r['hit'] else 'N'} |"
        )
    lines += [
        "",
        "## Reading",
        "",
        "- Objective: **MDD 持平 (↑≥0) + CAGR ≥+0.20pp + tip OK** under Bull-only densify.",
        "- Live Soft-Frozen already densified F[0.60,0.80] E[0.00,0.50]; this screen densifies **further in Bull**.",
        "- Even HIT → paper observe only.",
        "",
        f"Repro: `PYTHONPATH=scripts python3 scripts/asymm_0050_bull_densify_under_cool_stagea.py`",
        "",
        f"Label: `{SCREEN_ID}_{payload['generated_at_utc'][:10]}__{verdict}__NO_LIVE_WIRE`",
        "",
    ]
    md = "\n".join(lines)
    (REP / f"{SCREEN_ID}.md").write_text(md)
    (OPS / f"{SCREEN_ID}.md").write_text(md)

    decision = {
        "label": "ASYMM_0050_BULL_DENSIFY_UNDER_COOL_DECISION",
        "generated_at_utc": _utc(),
        "status": verdict,
        "live_wire": False,
        "n_hits": len(hits),
        "hit_ids": [r["id"] for r in hits],
        "best": hits[0]["id"] if hits else None,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "stage_a": f"research/ops/{SCREEN_ID}.md",
    }
    dlines = [
        "# Asymmetric 0050 Bull densify under COOL — Decision Pack (Stage A)",
        "",
        f"Date: 2026-09-25 · Generated `{decision['generated_at_utc']}`",
        f"Status: **{verdict}** · Soft-Frozen **KEEP** · live wire **false**",
        "",
        "## Verdict",
        "",
        f"HIT books: **{len(hits)}** / {len(rows)}.",
        "",
    ]
    if hits:
        b = hits[0]
        dlines += [
            f"Best: `{b['id']}` · held CAGR↑ **{b['held_cagr_lift_pp']:+.2f}pp** · "
            f"MDD↑ **{b['held_mdd_improve_pp']:+.2f}pp** · tip OK",
            "",
            "Next: dual-paper observe ballot — not live.",
            "",
        ]
    elif flat_tip_fail:
        b = flat_tip_fail[0]
        dlines += [
            f"Held-flat tip-fail best: `{b['id']}` · held CAGR↑ {b['held_cagr_lift_pp']:+.2f}pp · "
            f"MDD↑ {b['held_mdd_improve_pp']:+.2f}pp · tip fail",
            "",
            "Binding: Soft-Frozen KEEP · tip-clean MDD-flat joint still missing.",
            "",
        ]
    else:
        dlines += [
            "No MDD-flat + CAGR≥+0.20 under predeclared asymmetric grid.",
            "",
            "Binding: Soft-Frozen KEEP · reopen only with new mechanism or human objective change.",
            "",
        ]
    dlines += [
        f"Label: `ASYMM_0050_BULL_DENSIFY_UNDER_COOL_DECISION_2026-09-25__{verdict}`",
        "",
    ]
    (OPS / "ASYMM_0050_BULL_DENSIFY_UNDER_COOL_DECISION_PACK.json").write_text(
        json.dumps(decision, indent=2) + "\n"
    )
    (OPS / "ASYMM_0050_BULL_DENSIFY_UNDER_COOL_DECISION_PACK.md").write_text("\n".join(dlines))
    (REP / "ASYMM_0050_BULL_DENSIFY_UNDER_COOL_DECISION_PACK.json").write_text(
        json.dumps(decision, indent=2) + "\n"
    )
    (REP / "ASYMM_0050_BULL_DENSIFY_UNDER_COOL_DECISION_PACK.md").write_text("\n".join(dlines))

    # Update charter status line lightly via sidecar note only — charter stays OPEN until screen done.
    print(json.dumps({"verdict": verdict, "n_hits": len(hits), "n_books": len(rows)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
