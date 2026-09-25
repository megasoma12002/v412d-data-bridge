#!/usr/bin/env python3
"""β / 0050 densify under frozen COOL_c8 — Stage A (paper only).

Charter: research/ops/BETA_0050_DENSIFY_UNDER_COOL_STAGEA_CHARTER.md
Live Soft+Sleeve+COOL twin base · Soft-Frozen tip KEEP · no live wire.
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
    build_kd_season_tilt_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "beta-0050-densify-under-cool-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "BETA_0050_DENSIFY_UNDER_COOL_STAGEA_CHARTER"
SCREEN_ID = "BETA_0050_DENSIFY_UNDER_COOL_STAGEA_SCREEN"
HELDOUT = "heldout_2019_plus"
E22_VERSION = e22div.DEFAULT_BOOKS_VERSION
BASE_ID = "BASE_FUSE_COOL"
MDD_FLOOR = -0.15
CAGR_LIFT_PP = 0.20

# (track, fin_lo, fin_hi, tel_lo, tel_hi, etf_lo, etf_hi)
GRID: list[tuple[str, float, float, float, float, float, float]] = [
    ("E_HI", 0.60, 0.90, 0.03, 0.35, 0.00, 0.40),
    ("E_HI", 0.60, 0.90, 0.03, 0.35, 0.00, 0.45),
    ("E_HI", 0.60, 0.90, 0.03, 0.35, 0.00, 0.50),
    ("E_HI_FIN_ROOM", 0.60, 0.85, 0.03, 0.35, 0.00, 0.45),
    ("E_HI_FIN_ROOM", 0.60, 0.85, 0.03, 0.35, 0.00, 0.50),
    ("E_HI_FIN_ROOM", 0.60, 0.80, 0.03, 0.35, 0.00, 0.50),
    ("E_FLOOR", 0.60, 0.90, 0.03, 0.35, 0.05, 0.40),
    ("E_FLOOR", 0.60, 0.85, 0.03, 0.35, 0.10, 0.45),
    ("E_FLOOR", 0.60, 0.80, 0.03, 0.35, 0.10, 0.50),
    ("E_FLOOR_TEL", 0.60, 0.85, 0.05, 0.35, 0.05, 0.45),
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


def _row(base_w, chal_w, tip, *, rid, track, meta, n_fills, mean_tgt):
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
    return {
        "id": rid,
        "track": track,
        "meta": meta,
        "mean_target": mean_tgt,
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
        "hit": bool(cagr_hit and in_band and tip_ok),
    }


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.9]
    for track, *clips in GRID:
        assert clip.feasible(*clips), (track, clips)

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

    live_clips = (
        float(soft.SOFT_FROZEN_FIN_LO),
        float(soft.SOFT_FROZEN_FIN_HI),
        float(soft.SOFT_FROZEN_TEL_LO),
        float(soft.SOFT_FROZEN_TEL_HI),
        float(soft.SOFT_FROZEN_ETF_LO),
        float(soft.SOFT_FROZEN_ETF_HI),
    )
    tgt_live = _target_clips(score_live, regime, live_clips)

    print("offense NAV for BASE cool ...", flush=True)
    fuse_off, _ = _sim(
        market, tgt_live, regime, dividends, scores=buy_live, buy_ok=buy_ok, sell=sell_live
    )
    cool = _cool_from_offense(market, fuse_off)
    cool.to_frame("e45_exposure").to_csv(OUT / "exposure_cool_from_fuse.csv")

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
    base_w = _pack(base_nav)
    base_nav.to_csv(OUT / f"nav_{BASE_ID}.csv", index=False)

    rows = []
    for track, flo, fhi, tlo, thi, elo, ehi in GRID:
        rid = clip.cand_id(flo, fhi, tlo, thi, elo, ehi).replace("CLIP_SEARCH_", "BETA_")
        print(f"  {rid} ...", flush=True)
        clips = (flo, fhi, tlo, thi, elo, ehi)
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
        mean_tgt = {
            "Financial": round(float(tgt["Financial"].mean()), 4),
            "Telecom": round(float(tgt["Telecom"].mean()), 4),
            "0050": round(float(tgt["0050"].mean()), 4),
        }
        rows.append(
            _row(
                base_w,
                _pack(nav),
                tip,
                rid=rid,
                track=track,
                meta={
                    "fin": [flo, fhi],
                    "tel": [tlo, thi],
                    "etf": [elo, ehi],
                },
                n_fills=nf,
                mean_tgt=mean_tgt,
            )
        )

    hits = [r for r in rows if r["hit"]]
    soft_hits = [
        r
        for r in rows
        if r["in_mdd_band"]
        and r["held_cagr_lift_pp"] is not None
        and float(r["held_cagr_lift_pp"]) >= 0.10
        and not r["hit"]
    ]
    tradeoff = [
        r
        for r in rows
        if r["cagr_hit"] and not r["in_mdd_band"]
    ]
    if hits:
        verdict = "BETA_0050_HIT"
    elif soft_hits or any(
        r["in_mdd_band"]
        and r["held_cagr_lift_pp"] is not None
        and float(r["held_cagr_lift_pp"]) > 0
        for r in rows
    ):
        verdict = "BETA_0050_SOFT"
    elif tradeoff:
        verdict = "MDD_TRADEOFF"
    else:
        verdict = "NO_LIFT"

    ranked = sorted(
        rows,
        key=lambda r: (
            -int(r["hit"]),
            -int(r["tip_ok"] and r["in_mdd_band"]),
            -(r["held_cagr_lift_pp"] or -9.0),
        ),
    )

    payload = {
        "schema_version": "beta_0050_densify_under_cool_stagea_v1",
        "charter_id": CHARTER_ID,
        "screen_id": SCREEN_ID,
        "generated_at_utc": _utc(),
        "verdict": verdict,
        "live_wire": False,
        "soft_frozen_keep": True,
        "cool_frozen": True,
        "base_id": BASE_ID,
        "base_windows": base_w,
        "n_challengers": len(rows),
        "hit_ids": [r["id"] for r in hits],
        "best": ranked[0]["id"] if ranked else None,
        "prior_offense_soft": "OFFENSE_CAGR_UNDER_COOL (#282) Soft/Sleeve densify SOFT",
        "rows": ranked,
        "non_actions": [
            "No Soft-Frozen live clip flip from Stage A",
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
        "# β / 0050 densify under COOL — Stage A screen",
        "",
        f"Generated: `{payload['generated_at_utc']}`  ",
        f"Verdict: **`{verdict}`** · base `{BASE_ID}` · Soft-Frozen KEEP · COOL frozen · **no live wire**",
        "",
        f"Base held {fmt_pct(bh['cagr'])} / {fmt_pct(bh['max_drawdown'])}",
        "",
        f"Hits: `{payload['hit_ids']}`",
        "",
        "## Challengers vs BASE_FUSE_COOL",
        "",
        "| id | track | mean 0050 | held CAGR | held MDD | CAGR lift | MDD↑ | band | tip | hit |",
        "|---|---|---:|---:|---:|---:|---:|:---:|:---:|:---:|",
    ]
    for r in ranked:
        lines.append(
            f"| `{r['id']}` | `{r['track']}` | {100 * r['mean_target']['0050']:.1f}% | "
            f"{fmt_pct(r['held_cagr'])} | {fmt_pct(r['held_mdd'])} | "
            f"{fmt_pp(r['held_cagr_lift_pp'])} | {fmt_pp(r['held_mdd_improve_pp'])} | "
            f"{'Y' if r['in_mdd_band'] else 'N'} | {'Y' if r['tip_ok'] else 'N'} | "
            f"{'Y' if r['hit'] else 'N'} |"
        )
    lines += [
        "",
        "## Reading",
        "",
        "- Prior Soft/Sleeve densify under COOL → `OFFENSE_CAGR_SOFT` (#282).",
        "- This screen densifies **0050 clip** (earn 大盤) with FIN lo≥0.60 defense floor.",
        "- Even HIT → paper observe only; live clip flip needs Class D ACCEPT.",
        "",
        f"Repro: `repro/beta-0050-densify-under-cool-stagea/`",
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
        "label": "BETA_0050_DENSIFY_UNDER_COOL_DECISION",
        "generated_at_utc": _utc(),
        "status": "STAGE_A_" + verdict,
        "verdict": verdict,
        "hit_ids": payload["hit_ids"],
        "best": payload["best"],
        "binding": [
            "Soft-Frozen live clip KEEP until Class D ACCEPT",
            "Do not mix 公+民 (0b2 STOP)",
            "COOL live KEEP independent of this paper screen",
        ],
        "next": (
            "Open paper observe ballot on hit_ids"
            if hits
            else "STOP same-grid densify or open new offense mechanism (not Soft knobs / not 公+民)"
        ),
        "charter": f"research/ops/{CHARTER_ID}.md",
        "stage_a": f"research/ops/{SCREEN_ID}.md",
        "order": "research/ops/RESEARCH_ORDER_BETA_DEFENSE.md",
    }
    (OPS / "BETA_0050_DENSIFY_UNDER_COOL_DECISION_PACK.json").write_text(
        json.dumps(decision, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    dlines = [
        "# β / 0050 densify under COOL — Decision Pack",
        "",
        f"Date: 2026-09-25 · `{decision['generated_at_utc']}`  ",
        f"Status: **{verdict}** · Soft-Frozen **KEEP** · live wire **false**",
        "",
        "## Verdict",
        "",
    ]
    if hits:
        dlines += [f"**BETA_0050_HIT** ({len(hits)}):", ""] + [f"- `{x}`" for x in hits]
    else:
        dlines += [
            f"**{verdict}** — finite 0050 densify under COOL did not jointly clear "
            "≥+0.20pp CAGR + |MDD|≤15% + tip OK (or only soft near-misses).",
            "",
        ]
    dlines += ["", "## Binding", ""] + [
        f"{i}. {b}" for i, b in enumerate(decision["binding"], 1)
    ]
    dlines += [
        "",
        f"Next: {decision['next']}",
        "",
        f"Label: `BETA_0050_DENSIFY_UNDER_COOL_DECISION_2026-09-25__{verdict}`",
        "",
    ]
    (OPS / "BETA_0050_DENSIFY_UNDER_COOL_DECISION_PACK.md").write_text(
        "\n".join(dlines) + "\n", encoding="utf-8"
    )
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
