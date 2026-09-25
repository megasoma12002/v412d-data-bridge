#!/usr/bin/env python3
"""Within-sleeve FinPub/TEL micro under frozen Soft+Sleeve+COOL — Stage A (paper).

Charter: research/ops/WITHIN_SLEEVE_COOL_MICRO_STAGEA_CHARTER.md
Soft-Frozen tip KEEP · no live wire · no 公+民.
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
from e50_early_stack_combined_nav import FIN, TEL, build_tel_name_scores, e16_features, simulate_core
from portfolio_capital import DEFAULT_CAPITAL
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp
from sleeve_tilt_helpers import (
    ALPHA as LIVE_SLEEVE_ALPHA,
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
    TEL_MIN_LOT_PACK,
    TEL_RS_SOFT_TILT,
    TEL_RS_SOFT_TILT_EXDIV,
    TEL_TOP2_EQUAL,
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
DECISION_ID = "WITHIN_SLEEVE_COOL_MICRO_DECISION_PACK"
HELDOUT = "heldout_2019_plus"
E22_VERSION = e22div.DEFAULT_BOOKS_VERSION
BASE_ID = "BASE_LIVE_FUSE_COOL"
MDD_FLOOR = -0.15
CAGR_LIFT_PP = 0.20
CAGR_SOFT_PP = 0.10

SEASONS: dict[str, tuple[tuple[int, int], tuple[int, int]]] = {
    "APR15_MAY15": ((4, 15), (5, 15)),
    "MAY1_MAY31": ((5, 1), (5, 31)),
    "APR1_MAY15": ((4, 1), (5, 15)),
}

# Predeclared FIN_KD_MICRO — exclude exact live KD_OPT (Apr15–May15 · K30 · T15).
FIN_KD_GRID: list[tuple[str, float, int]] = [
    ("APR15_MAY15", 25.0, 10),
    ("APR15_MAY15", 25.0, 15),
    ("APR15_MAY15", 25.0, 20),
    ("APR15_MAY15", 30.0, 10),
    ("APR15_MAY15", 30.0, 20),
    ("APR15_MAY15", 35.0, 10),
    ("APR15_MAY15", 35.0, 15),
    ("APR15_MAY15", 35.0, 20),
    ("MAY1_MAY31", 25.0, 15),
    ("MAY1_MAY31", 30.0, 15),
    ("MAY1_MAY31", 35.0, 15),
    ("APR1_MAY15", 30.0, 15),
]

# TEL_MICRO — skip TEL_EQUAL control; FIN stays live KD_OPT.
TEL_GRID: list[tuple[str, str]] = [
    ("TEL_RS_SOFT", TEL_RS_SOFT_TILT),
    ("TEL_MIN_LOT", TEL_MIN_LOT_PACK),
    ("TEL_RS_SOFT_EXDIV", TEL_RS_SOFT_TILT_EXDIV),
    ("TEL_TOP2", TEL_TOP2_EQUAL),
]


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _fin_id(season: str, k: float, pre: int) -> str:
    return f"FIN_KD_{season}_K{int(k)}_T{int(pre)}"


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
    telecom_alloc: str = TEL_EQUAL,
    tel_scores=None,
    tel_buy_ok=None,
):
    kw: dict[str, Any] = dict(
        apply_e22=True,
        apply_stock_div=True,
        capital=float(DEFAULT_CAPITAL),
        lot_size=int(BOARD_LOT),
        financial_alloc=FIN_PRE_EXDIV_KD,
        telecom_alloc=telecom_alloc,
        fin_name_scores=scores,
        fin_buy_ok=buy_ok,
        e22_version=E22_VERSION,
    )
    if sell is not None:
        kw["fin_sell_scores"] = sell
    if exposure is not None:
        kw["e45_exposure"] = exposure.astype(float)
    if tel_scores is not None:
        kw["tel_name_scores"] = tel_scores
    if tel_buy_ok is not None:
        kw["tel_buy_ok"] = tel_buy_ok
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


def _target_clips(score: pd.DataFrame, regime: pd.Series, clips: tuple[float, ...]) -> pd.DataFrame:
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


def _kd_bundle(market, dividends, cal, season: str, k: float, pre: int):
    ss, se = SEASONS[season]
    scores = build_kd_season_tilt_scores(
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
    return scores, buy_ok


def _row(base_w, chal_w, tip, *, rid, track, meta, n_fills):
    h = chal_w[HELDOUT]
    b = base_w[HELDOUT]
    gb = cagr_delta_pp(b.get("cagr"), h.get("cagr"), missing_as_zero=True)
    lift = None if gb is None else round(-float(gb), 4)
    md = round(float(mdd_delta_pp(b.get("max_drawdown"), h.get("max_drawdown"))), 4)
    tip_ok = (
        tip.get("ytd", {}).get("gate") == "PASS"
        and tip.get("trailing_1y", {}).get("gate") == "PASS"
        and float(tip["ytd"].get("mdd_improve_pp") or -9) >= 0
        and float(tip["trailing_1y"].get("mdd_improve_pp") or -9) >= 0
    )
    mdd = h.get("max_drawdown")
    in_band = mdd is not None and float(mdd) >= float(MDD_FLOOR)
    cagr_ok = lift is not None and float(lift) >= float(CAGR_LIFT_PP)
    mdd_flat = float(md) >= 0.0
    hit = bool(cagr_ok and mdd_flat and tip_ok and in_band)
    held_flat_tip_fail = bool(cagr_ok and mdd_flat and in_band and not tip_ok)
    soft_cagr = (
        lift is not None
        and float(lift) >= float(CAGR_SOFT_PP)
        and in_band
        and not hit
        and not held_flat_tip_fail
    )
    return {
        "id": rid,
        "track": track,
        "meta": meta,
        "n_fills": n_fills,
        "windows": chal_w,
        "held_cagr": h.get("cagr"),
        "held_mdd": mdd,
        "held_cagr_lift_pp": lift,
        "held_mdd_improve_pp": md,
        "in_mdd_band": bool(in_band),
        "tip": tip,
        "tip_ok": bool(tip_ok),
        "cagr_ok": bool(cagr_ok),
        "mdd_flat": bool(mdd_flat),
        "hit": hit,
        "held_flat_tip_fail": held_flat_tip_fail,
        "cagr_soft": bool(soft_cagr),
    }


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)

    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.8]
    assert soft.SOFT_FROZEN_TEL_CLIP == [0.03, 0.35]
    assert soft.SOFT_FROZEN_ETF_CLIP == [0.0, 0.5]
    assert float(LIVE_KD["k_thresh"]) == 30.0
    assert tuple(LIVE_KD["season_start"]) == (4, 15)
    assert tuple(LIVE_KD["season_end"]) == (5, 15)
    assert int(LIVE_KD["pre_days"]) == 15
    live_dup = ("APR15_MAY15", 30.0, 15)
    assert live_dup not in FIN_KD_GRID, "FIN grid must exclude exact live KD_OPT"
    assert len(FIN_KD_GRID) >= 10
    assert len(FIN_KD_GRID) + len(TEL_GRID) <= 24

    print("loading ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, sleeve, _tgt_live, regime = e16_features(market)
    cal = pd.DatetimeIndex(pd.to_datetime(market["date"]).drop_duplicates().sort_values())
    lows, highs = build_low_high_catalog(market, cal, list(FIN))

    print("live KD_OPT scores ...", flush=True)
    kd_live, buy_ok_live = _kd_bundle(
        market,
        dividends,
        cal,
        "APR15_MAY15",
        float(LIVE_KD["k_thresh"]),
        int(LIVE_KD["pre_days"]),
    )
    buy_live = _buy(kd_live, lows)
    sell_live = _sell(highs)
    score_live = _sleeve_score(market, sleeve, float(LIVE_SLEEVE_ALPHA))

    live_clips = (
        float(soft.SOFT_FROZEN_FIN_LO),
        float(soft.SOFT_FROZEN_FIN_HI),
        float(soft.SOFT_FROZEN_TEL_LO),
        float(soft.SOFT_FROZEN_TEL_HI),
        float(soft.SOFT_FROZEN_ETF_LO),
        float(soft.SOFT_FROZEN_ETF_HI),
    )
    tgt_live = _target_clips(score_live, regime, live_clips)

    print("offense NAV for BASE cool (frozen COOL) ...", flush=True)
    fuse_off, _ = _sim(
        market, tgt_live, regime, dividends, scores=buy_live, buy_ok=buy_ok_live, sell=sell_live
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
        buy_ok=buy_ok_live,
        sell=sell_live,
        exposure=cool,
    )
    base_w = _pack(base_nav)
    base_nav.to_csv(OUT / f"nav_{BASE_ID}.csv", index=False)

    tel_rs = build_tel_name_scores(market)
    tel_ok = build_pre_exdiv_window_buy_ok(
        cal, dividends, TEL, pre_days=int(LIVE_KD["pre_days"]), also_stock_ex=True
    )

    rows: list[dict[str, Any]] = []

    for season, kth, pred in FIN_KD_GRID:
        rid = _fin_id(season, kth, pred)
        print(f"  {rid} ...", flush=True)
        kd, buy_ok = _kd_bundle(market, dividends, cal, season, kth, pred)
        buy = _buy(kd, lows)
        nav, nf = _sim(
            market,
            tgt_live,
            regime,
            dividends,
            scores=buy,
            buy_ok=buy_ok,
            sell=sell_live,
            exposure=cool,
        )
        nav.to_csv(OUT / f"nav_{rid}.csv", index=False)
        tip = _tip(base_nav, nav)
        rows.append(
            _row(
                base_w,
                _pack(nav),
                tip,
                rid=rid,
                track="FIN_KD_MICRO",
                meta={
                    "season": season,
                    "season_start": list(SEASONS[season][0]),
                    "season_end": list(SEASONS[season][1]),
                    "k_thresh": float(kth),
                    "pre_days": int(pred),
                    "telecom_alloc": TEL_EQUAL,
                },
                n_fills=nf,
            )
        )

    for rid, tel_alloc in TEL_GRID:
        print(f"  {rid} ...", flush=True)
        tel_scores = None
        tel_buy = None
        if tel_alloc in (TEL_RS_SOFT_TILT, TEL_RS_SOFT_TILT_EXDIV):
            tel_scores = tel_rs
        if tel_alloc == TEL_RS_SOFT_TILT_EXDIV:
            tel_buy = tel_ok
        nav, nf = _sim(
            market,
            tgt_live,
            regime,
            dividends,
            scores=buy_live,
            buy_ok=buy_ok_live,
            sell=sell_live,
            exposure=cool,
            telecom_alloc=tel_alloc,
            tel_scores=tel_scores,
            tel_buy_ok=tel_buy,
        )
        nav.to_csv(OUT / f"nav_{rid}.csv", index=False)
        tip = _tip(base_nav, nav)
        rows.append(
            _row(
                base_w,
                _pack(nav),
                tip,
                rid=rid,
                track="TEL_MICRO",
                meta={
                    "fin": "KD_OPT_LIVE",
                    "telecom_alloc": tel_alloc,
                },
                n_fills=nf,
            )
        )

    hits = [r for r in rows if r["hit"]]
    held_only = [r for r in rows if r["held_flat_tip_fail"]]
    soft_hits = [r for r in rows if r["cagr_soft"]]
    if hits:
        verdict = "WITHIN_SLEEVE_MICRO_HIT"
    elif held_only:
        verdict = "HELD_FLAT_TIP_FAIL"
    elif soft_hits or any(
        r["in_mdd_band"]
        and r["held_cagr_lift_pp"] is not None
        and float(r["held_cagr_lift_pp"]) > 0
        for r in rows
    ):
        verdict = "CAGR_SOFT"
    else:
        verdict = "NO_FLAT_LIFT"

    ranked = sorted(
        rows,
        key=lambda r: (
            -int(r["hit"]),
            -int(r["mdd_flat"] and r["cagr_ok"]),
            -int(r["tip_ok"]),
            -(r["held_cagr_lift_pp"] or -9.0),
            -r["held_mdd_improve_pp"],
        ),
    )

    payload = {
        "schema_version": "within_sleeve_cool_micro_stagea_v1",
        "charter_id": CHARTER_ID,
        "screen_id": SCREEN_ID,
        "generated_at_utc": _utc(),
        "verdict": verdict,
        "live_wire": False,
        "soft_frozen_keep": True,
        "cool_frozen": True,
        "objective": (
            "held CAGR≥+0.20pp · held MDD↑≥0 · tip YTD+1y MDD↑≥0 · |MDD|≤15%"
        ),
        "base_id": BASE_ID,
        "base_windows": base_w,
        "base_n_fills": n_base,
        "n_challengers": len(rows),
        "n_fin_kd": len(FIN_KD_GRID),
        "n_tel": len(TEL_GRID),
        "hit_ids": [r["id"] for r in hits],
        "held_flat_tip_fail_ids": [r["id"] for r in held_only],
        "cagr_soft_ids": [r["id"] for r in soft_hits],
        "best": ranked[0]["id"] if ranked else None,
        "live_kd_opt": {
            "id": LIVE_KD["id"],
            "season_start": list(LIVE_KD["season_start"]),
            "season_end": list(LIVE_KD["season_end"]),
            "k_thresh": float(LIVE_KD["k_thresh"]),
            "pre_days": int(LIVE_KD["pre_days"]),
        },
        "soft_frozen_clips": {
            "fin": list(soft.SOFT_FROZEN_FIN_CLIP),
            "tel": list(soft.SOFT_FROZEN_TEL_CLIP),
            "etf": list(soft.SOFT_FROZEN_ETF_CLIP),
        },
        "rows": ranked,
        "non_actions": [
            "No Soft-Frozen live clip / tip rewrite from Stage A",
            "No live KD_OPT / TEL_EQUAL wire from Stage A",
            "No 公+民 mix / FinPriv expand",
            "No COOL retune / DH re-enable",
        ],
    }

    def fmt_pct(x):
        return "n/a" if x is None else f"{100.0 * float(x):.2f}%"

    def fmt_pp(x):
        return "n/a" if x is None else f"{float(x):+.2f}pp"

    bh = base_w[HELDOUT]
    lines = [
        "# Within-sleeve FinPub/TEL micro under COOL — Stage A screen",
        "",
        f"Generated: `{payload['generated_at_utc']}`  ",
        f"Verdict: **`{verdict}`** · base `{BASE_ID}` · Soft-Frozen KEEP · COOL frozen · **no live wire**",
        "",
        f"Base held {fmt_pct(bh['cagr'])} / {fmt_pct(bh['max_drawdown'])}",
        "",
        f"Hits: `{payload['hit_ids']}` · held-flat tip-fail: `{payload['held_flat_tip_fail_ids']}`",
        "",
        "## Challengers vs BASE_LIVE_FUSE_COOL",
        "",
        "| id | track | held CAGR | held MDD | CAGR lift | MDD↑ | band | tip | hit |",
        "|---|---|---:|---:|---:|---:|:---:|:---:|:---:|",
    ]
    for r in ranked:
        lines.append(
            f"| `{r['id']}` | `{r['track']}` | "
            f"{fmt_pct(r['held_cagr'])} | {fmt_pct(r['held_mdd'])} | "
            f"{fmt_pp(r['held_cagr_lift_pp'])} | {fmt_pp(r['held_mdd_improve_pp'])} | "
            f"{'Y' if r['in_mdd_band'] else 'N'} | {'Y' if r['tip_ok'] else 'N'} | "
            f"{'Y' if r['hit'] else 'N'} |"
        )
    lines += [
        "",
        "## Reading",
        "",
        "- Soft-Frozen clips KEEP F[0.60,0.80] T[0.03,0.35] E[0.00,0.50].",
        "- FIN_KD_MICRO varies only KD season/K/pre; TEL stays EQUAL.",
        "- TEL_MICRO varies only telecom_alloc; FIN stays live KD_OPT.",
        "- Even HIT → paper observe only; live KD/TEL flip needs ACCEPT.",
        "",
        f"Repro: `repro/within-sleeve-cool-micro-stagea/`",
        "",
        f"Label: `{SCREEN_ID}_{_utc()[:10]}__{verdict}__NO_LIVE_WIRE`",
        "",
    ]
    md = "\n".join(lines) + "\n"
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    (OUT / "stagea_summary.json").write_text(text, encoding="utf-8")
    (REP / f"{SCREEN_ID}.json").write_text(text, encoding="utf-8")
    (OPS / f"{SCREEN_ID}.json").write_text(text, encoding="utf-8")
    (REP / f"{SCREEN_ID}.md").write_text(md, encoding="utf-8")
    (OPS / f"{SCREEN_ID}.md").write_text(md, encoding="utf-8")

    decision = {
        "label": "WITHIN_SLEEVE_COOL_MICRO_DECISION",
        "generated_at_utc": _utc(),
        "status": "STAGE_A_" + verdict,
        "verdict": verdict,
        "hit_ids": payload["hit_ids"],
        "held_flat_tip_fail_ids": payload["held_flat_tip_fail_ids"],
        "best": payload["best"],
        "binding": [
            "Soft-Frozen live clip KEEP until Class D ACCEPT",
            "Live KD_OPT + TEL_EQUAL KEEP until dedicated ACCEPT",
            "Do not mix 公+民 (0b2 STOP)",
            "COOL live KEEP independent of this paper screen",
        ],
        "next": (
            "Open paper observe ballot on hit_ids"
            if hits
            else (
                "STOP same-grid within-sleeve micro densify; next lever ≠ Soft-Frozen clip / ≠ 公+民"
                if verdict == "NO_FLAT_LIFT"
                else "Do not live-wire; optional observe only if near-flat tip-clean narrative holds"
            )
        ),
        "charter": f"research/ops/{CHARTER_ID}.md",
        "stage_a": f"research/ops/{SCREEN_ID}.md",
        "order": "research/ops/RESEARCH_ORDER_BETA_DEFENSE.md",
    }
    (OPS / f"{DECISION_ID}.json").write_text(
        json.dumps(decision, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    dlines = [
        "# Within-sleeve FinPub/TEL micro under COOL — Decision Pack",
        "",
        f"Date: 2026-09-25 · `{decision['generated_at_utc']}`  ",
        f"Status: **{verdict}** · Soft-Frozen **KEEP** · live wire **false**",
        "",
        "## Verdict",
        "",
    ]
    if hits:
        dlines += [f"**WITHIN_SLEEVE_MICRO_HIT** ({len(hits)}):", ""] + [
            f"- `{x}`" for x in hits
        ]
    elif verdict == "HELD_FLAT_TIP_FAIL":
        dlines += [
            "**HELD_FLAT_TIP_FAIL** — held MDD flat + CAGR≥+0.20 for some; tip MDD fails.",
            "",
        ]
    elif verdict == "CAGR_SOFT":
        dlines += [
            "**CAGR_SOFT** — band CAGR lift present but short of joint "
            "≥+0.20pp + MDD↑≥0 + tip OK.",
            "",
        ]
    else:
        dlines += [
            "**NO_FLAT_LIFT** — no book jointly clears MDD↑≥0 + CAGR≥+0.20pp in band.",
            "",
        ]
    dlines += ["", "## Binding", ""] + [
        f"{i}. {b}" for i, b in enumerate(decision["binding"], 1)
    ]
    dlines += [
        "",
        f"Next: {decision['next']}",
        "",
        f"Label: `WITHIN_SLEEVE_COOL_MICRO_DECISION_2026-09-25__{verdict}`",
        "",
    ]
    (OPS / f"{DECISION_ID}.md").write_text("\n".join(dlines) + "\n", encoding="utf-8")

    repro_readme = [
        "# within-sleeve-cool-micro-stagea repro",
        "",
        f"Verdict: `{verdict}` · base `{BASE_ID}` · no live wire",
        "",
        "```bash",
        "PYTHONPATH=scripts python3 scripts/within_sleeve_cool_micro_stagea.py",
        "```",
        "",
        f"Charter: `research/ops/{CHARTER_ID}.md`",
        f"Screen: `research/ops/{SCREEN_ID}.md`",
        "",
    ]
    (REPRO / "README.md").write_text("\n".join(repro_readme) + "\n", encoding="utf-8")

    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
