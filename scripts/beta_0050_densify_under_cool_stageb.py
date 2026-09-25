#!/usr/bin/env python3
"""β / 0050 densify under COOL — Stage B: MDD flat + CAGR lift (paper only).

Charter: research/ops/BETA_0050_DENSIFY_UNDER_COOL_STAGEB_CHARTER.md
Fine grid FIN hi∈[0.80,0.85] × ETF hi — Soft-Frozen KEEP · no live wire.
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
    build_kd_season_tilt_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "beta-0050-densify-under-cool-stageb"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "BETA_0050_DENSIFY_UNDER_COOL_STAGEB_CHARTER"
SCREEN_ID = "BETA_0050_DENSIFY_UNDER_COOL_STAGEB_SCREEN"
HELDOUT = "heldout_2019_plus"
E22_VERSION = e22div.DEFAULT_BOOKS_VERSION
BASE_ID = "BASE_FUSE_COOL"
MDD_FLOOR = -0.15
CAGR_LIFT_PP = 0.20

FIN_HI = (0.80, 0.82, 0.83, 0.84, 0.85)
ETF_HI = (0.40, 0.42, 0.45, 0.48, 0.50)


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


def _buy(kd, lows) -> pd.DataFrame:
    out = soft_boost_scores(kd, lows[BUY_LOW_ID], 1.0)
    return soft_boost_scores(out, lows["K9_LT30"], 1.0)


def _sell(highs) -> pd.DataFrame:
    return soft_sell_panel(highs[SELL_HIGH_ID], boost=0.50)


def _sleeve_score(market, sleeve, alpha: float) -> pd.DataFrame:
    _p, _s, _t, _r, base_score = soft.build_soft_frozen_targets(market)
    tilt = sleeve_signal_panel(sleeve, "rsi_lt30", 14)
    return base_score + float(alpha) * tilt


def _target_clips(score, regime, clips):
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


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.8]

    grid = []
    for fhi in FIN_HI:
        for ehi in ETF_HI:
            clips = (0.60, float(fhi), 0.03, 0.35, 0.00, float(ehi))
            assert clip.feasible(*clips), clips
            grid.append(clips)

    print("loading ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, sleeve, _t, regime = e16_features(market)
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

    live_clips = (
        float(soft.SOFT_FROZEN_FIN_LO),
        float(soft.SOFT_FROZEN_FIN_HI),
        float(soft.SOFT_FROZEN_TEL_LO),
        float(soft.SOFT_FROZEN_TEL_HI),
        float(soft.SOFT_FROZEN_ETF_LO),
        float(soft.SOFT_FROZEN_ETF_HI),
    )
    tgt_live = _target_clips(score_live, regime, live_clips)

    print("BASE_FUSE_COOL ...", flush=True)
    fuse_off, _ = _sim(
        market, tgt_live, regime, dividends, scores=buy_live, buy_ok=buy_ok, sell=sell_live
    )
    cool = _cool_from_offense(market, fuse_off)
    base_nav, _ = _sim(
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
    for clips in grid:
        flo, fhi, tlo, thi, elo, ehi = clips
        rid = clip.cand_id(flo, fhi, tlo, thi, elo, ehi).replace("CLIP_SEARCH_", "B2_")
        print(f"  {rid} ...", flush=True)
        tgt = _target_clips(score_live, regime, clips)
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
        chal_w = _pack(nav)
        h, b = chal_w[HELDOUT], base_w[HELDOUT]
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
        rows.append(
            {
                "id": rid,
                "meta": {"fin": [flo, fhi], "tel": [tlo, thi], "etf": [elo, ehi]},
                "mean_target": {
                    "Financial": round(float(tgt["Financial"].mean()), 4),
                    "Telecom": round(float(tgt["Telecom"].mean()), 4),
                    "0050": round(float(tgt["0050"].mean()), 4),
                },
                "n_fills": nf,
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
            }
        )

    hits = [r for r in rows if r["hit"]]
    held_only = [r for r in rows if r["held_flat_tip_fail"]]
    if hits:
        verdict = "MDD_FLAT_CAGR_HIT"
    elif held_only:
        verdict = "HELD_FLAT_TIP_FAIL"
    else:
        verdict = "NO_FLAT_LIFT"

    ranked = sorted(
        rows,
        key=lambda r: (
            -int(r["hit"]),
            -int(r["mdd_flat"] and r["cagr_ok"]),
            -int(r["tip_ok"]),
            -(r["held_cagr_lift_pp"] or -9),
            -r["held_mdd_improve_pp"],
        ),
    )

    payload = {
        "schema_version": "beta_0050_densify_under_cool_stageb_v1",
        "charter_id": CHARTER_ID,
        "screen_id": SCREEN_ID,
        "generated_at_utc": _utc(),
        "verdict": verdict,
        "live_wire": False,
        "soft_frozen_keep": True,
        "objective": "held MDD↑≥0 · CAGR lift≥+0.20pp · tip MDD OK · |MDD|≤15%",
        "base_id": BASE_ID,
        "base_windows": base_w,
        "n_challengers": len(rows),
        "hit_ids": [r["id"] for r in hits],
        "held_flat_tip_fail_ids": [r["id"] for r in held_only],
        "best": ranked[0]["id"] if ranked else None,
        "rows": ranked,
        "non_actions": [
            "No Soft-Frozen live clip flip from Stage B",
            "No 公+民 mix",
            "No COOL retune",
        ],
    }

    def fmt_pct(x):
        return "n/a" if x is None else f"{100.0 * float(x):.2f}%"

    def fmt_pp(x):
        return "n/a" if x is None else f"{float(x):+.2f}pp"

    bh = base_w[HELDOUT]
    lines = [
        "# β / 0050 densify under COOL — Stage B (MDD flat + CAGR)",
        "",
        f"Generated: `{payload['generated_at_utc']}`  ",
        f"Verdict: **`{verdict}`** · base `{BASE_ID}` · Soft-Frozen KEEP · **no live wire**",
        "",
        f"Base held {fmt_pct(bh['cagr'])} / {fmt_pct(bh['max_drawdown'])}",
        "",
        f"Hits (MDD flat + CAGR + tip): `{payload['hit_ids']}`",
        f"Held-flat tip-fail: `{payload['held_flat_tip_fail_ids']}`",
        "",
        "| id | mean 0050 | CAGR lift | MDD↑ | band | tip | flat+cagr | hit |",
        "|---|---:|---:|---:|:---:|:---:|:---:|:---:|",
    ]
    for r in ranked:
        flat_cagr = r["mdd_flat"] and r["cagr_ok"]
        lines.append(
            f"| `{r['id']}` | {100 * r['mean_target']['0050']:.1f}% | "
            f"{fmt_pp(r['held_cagr_lift_pp'])} | {fmt_pp(r['held_mdd_improve_pp'])} | "
            f"{'Y' if r['in_mdd_band'] else 'N'} | {'Y' if r['tip_ok'] else 'N'} | "
            f"{'Y' if flat_cagr else 'N'} | {'Y' if r['hit'] else 'N'} |"
        )
    lines += [
        "",
        "## Reading",
        "",
        "- Objective: **MDD 持平 (↑≥0) + CAGR ≥+0.20pp + tip OK**.",
        "- Stage A HIT had CAGR↑ with MDD slightly worse; Stage B seeks joint flat.",
        "- Even HIT → paper observe only.",
        "",
        f"Label: `{SCREEN_ID}_{_utc()[:10]}__{verdict}__NO_LIVE_WIRE`",
        "",
    ]
    md = "\n".join(lines) + "\n"
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    (OUT / "stageb_summary.json").write_text(text, encoding="utf-8")
    (REP / f"{SCREEN_ID}.json").write_text(text, encoding="utf-8")
    (OPS / f"{SCREEN_ID}.json").write_text(text, encoding="utf-8")
    (REP / f"{SCREEN_ID}.md").write_text(md, encoding="utf-8")
    (OPS / f"{SCREEN_ID}.md").write_text(md, encoding="utf-8")

    decision = {
        "label": "BETA_0050_DENSIFY_UNDER_COOL_STAGEB_DECISION",
        "generated_at_utc": _utc(),
        "status": "STAGE_B_" + verdict,
        "verdict": verdict,
        "hit_ids": payload["hit_ids"],
        "held_flat_tip_fail_ids": payload["held_flat_tip_fail_ids"],
        "best": payload["best"],
        "objective": payload["objective"],
        "binding": [
            "Soft-Frozen live clip KEEP until Class D ACCEPT",
            "Human objective: MDD flat + CAGR improve",
            "No live wire from Stage B",
        ],
        "next": (
            "Open paper observe on hit_ids"
            if hits
            else (
                "Held flat exists but tip fails — tip-safe densify or new mechanism"
                if held_only
                else "NO_FLAT_LIFT on this fine grid — do not expand same axes after peek"
            )
        ),
        "charter": f"research/ops/{CHARTER_ID}.md",
        "stage_b": f"research/ops/{SCREEN_ID}.md",
    }
    (OPS / "BETA_0050_DENSIFY_UNDER_COOL_STAGEB_DECISION_PACK.json").write_text(
        json.dumps(decision, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    dlines = [
        "# β / 0050 densify under COOL — Stage B Decision Pack",
        "",
        f"Date: 2026-09-25 · `{decision['generated_at_utc']}`  ",
        f"Status: **{verdict}** · Soft-Frozen **KEEP** · live wire **false**",
        "",
        f"Objective: {payload['objective']}",
        "",
        "## Verdict",
        "",
    ]
    if hits:
        dlines += [f"**MDD_FLAT_CAGR_HIT** ({len(hits)}):", ""] + [f"- `{x}`" for x in hits]
    elif held_only:
        dlines += [
            "**HELD_FLAT_TIP_FAIL** — held MDD flat + CAGR OK for some; tip MDD fails.",
            "",
        ] + [f"- `{x}`" for x in held_only[:8]]
    else:
        dlines += ["**NO_FLAT_LIFT** — no book jointly clears MDD↑≥0 + CAGR≥+0.20pp in band.", ""]
    dlines += [
        "",
        "## Binding",
        "",
    ] + [f"{i}. {b}" for i, b in enumerate(decision["binding"], 1)]
    dlines += [
        "",
        f"Next: {decision['next']}",
        "",
        f"Label: `BETA_0050_STAGEB_DECISION_2026-09-25__{verdict}`",
        "",
    ]
    (OPS / "BETA_0050_DENSIFY_UNDER_COOL_STAGEB_DECISION_PACK.md").write_text(
        "\n".join(dlines) + "\n", encoding="utf-8"
    )
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
