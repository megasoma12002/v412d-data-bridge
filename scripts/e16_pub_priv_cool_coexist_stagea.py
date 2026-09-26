#!/usr/bin/env python3
"""公股＋民營並存 under frozen COOL_c8 — Stage A (paper only).

Charter: research/ops/PUB_PRIV_COOL_COEXIST_STAGEA_CHARTER.md
Soft-Frozen live SSOT untouched · no e21 universe expand.
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
import e50_early_stack_combined_nav as e50
from cool_c8_proxy_observe_helpers import build_cool_c8_exposure
from e16_private_fin_holdings_rescreen import PRIV_R3R4, PUB_R1, TEL, tip_gate
from e16_pub_priv_coexist_mdd_stage_a import build_extended_market, tip_mdd_ok
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, window_stats
from portfolio_capital import DEFAULT_CAPITAL
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp
from tw_share_lots import BOARD_LOT
from within_sleeve_alloc import (
    FIN_DUAL_PUB_PRIV,
    FIN_EQUAL,
    FIN_PRE_EXDIV_KD,
    TEL_EQUAL,
    build_kd_season_tilt_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/pub-priv-cool-coexist-stagea"
REP = OUT / "reports"
OPS = ROOT / "research/ops"
CAPITAL = float(DEFAULT_CAPITAL)
LOT = int(BOARD_LOT)
E22_VERSION = e22div.DEFAULT_BOOKS_VERSION

CHARTER_ID = "PUB_PRIV_COOL_COEXIST_STAGEA_CHARTER"
SCREEN_ID = "PUB_PRIV_COOL_COEXIST_STAGEA_SCREEN"
HELDOUT = "heldout_2019_plus"
SEALED = "sealed_2023_plus"

PUB_SHARES = (0.90, 0.85, 0.80, 0.75)
PRIV_POLICIES = (FIN_EQUAL, FIN_PRE_EXDIV_KD)
HELDOUT_GB_CAP = 3.0
TIP_MDD_TOL_PP = -0.5

KD_OPT = {
    "season_start": (4, 15),
    "season_end": (5, 15),
    "k_thresh": 30.0,
    "pre_days": 15,
    "active_score": 1.5,
}


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _kd_panels(market, dividends, fin_codes):
    cal = pd.DatetimeIndex(pd.to_datetime(market["date"]).drop_duplicates().sort_values())
    scores = build_kd_season_tilt_scores(
        market,
        dividends,
        fin_codes,
        k_thresh=float(KD_OPT["k_thresh"]),
        season_start=KD_OPT["season_start"],
        season_end=KD_OPT["season_end"],
        pre_days=int(KD_OPT["pre_days"]),
        active_score=float(KD_OPT["active_score"]),
    )
    buy_ok = build_pre_exdiv_window_buy_ok(
        cal, dividends, fin_codes, pre_days=int(KD_OPT["pre_days"]), also_stock_ex=True
    )
    return scores, buy_ok


def _pack_windows(nav: pd.DataFrame) -> dict[str, Any]:
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


def _cool(market, nav: pd.DataFrame) -> pd.Series:
    nav_s = stagea._nav_series(nav)
    feat = stagea._risk_features(market, nav_s)
    dates = pd.DatetimeIndex(nav_s.index)
    return build_cool_c8_exposure(dates, feat["proxy_mdd63"])


def _sim(market, target, regime, dividends, *, fin_codes, financial_alloc, **extra):
    old_fin, old_all = list(e50.FIN), list(e50.ALL)
    e50.FIN = list(fin_codes)
    e50.ALL = list(fin_codes) + list(TEL) + ["0050"]
    try:
        scores, buy_ok = _kd_panels(market, dividends, fin_codes)
        kw: dict[str, Any] = dict(
            apply_e22=True,
            apply_stock_div=True,
            e22_version=E22_VERSION,
            capital=CAPITAL,
            lot_size=LOT,
            financial_alloc=financial_alloc,
            telecom_alloc=TEL_EQUAL,
            fin_name_scores=scores,
            fin_buy_ok=buy_ok,
        )
        kw.update(extra)
        nav, fills, meta = e50.simulate_core(market, target, regime, dividends, **kw)
        if not bool(meta.get("exact_t1_ok")):
            raise RuntimeError(f"exact_t1_ok failed for {financial_alloc}")
        return nav, fills, meta
    finally:
        e50.FIN = old_fin
        e50.ALL = old_all


def _with_cool(market, target, regime, dividends, *, fin_codes, financial_alloc, **extra):
    off, fills0, meta0 = _sim(
        market, target, regime, dividends, fin_codes=fin_codes, financial_alloc=financial_alloc, **extra
    )
    exp = _cool(market, off)
    nav, fills, meta = _sim(
        market,
        target,
        regime,
        dividends,
        fin_codes=fin_codes,
        financial_alloc=financial_alloc,
        e45_exposure=exp.astype(float),
        **extra,
    )
    return nav, fills, meta, exp, off


def _score_row(base_w, chal_w, base_nav, chal_nav, *, rid, mech, meta, asof):
    tip = tip_gate(base_nav, chal_nav, asof)
    tip_m = tip_mdd_ok(base_nav, chal_nav, asof)
    bh, ch = base_w[HELDOUT], chal_w[HELDOUT]
    bs, cs = base_w[SEALED], chal_w[SEALED]
    mdd_h = mdd_delta_pp(bh.get("max_drawdown"), ch.get("max_drawdown"))
    mdd_s = mdd_delta_pp(bs.get("max_drawdown"), cs.get("max_drawdown"))
    gb_h = cagr_delta_pp(bh.get("cagr"), ch.get("cagr"), missing_as_zero=True)
    gb_h = 0.0 if gb_h is None else float(gb_h)
    tip_clean = tip["ytd"]["gate"] == "PASS" and tip["trailing_1y"]["gate"] == "PASS"
    tip_mdd_pass = bool(tip_m["ok"])
    held_ok = float(mdd_h) >= 0.0
    sealed_ok = float(mdd_s) >= 0.0
    gb_ok = gb_h <= HELDOUT_GB_CAP
    score = float(mdd_h) + 0.5 * float(mdd_s) - 0.25 * max(0.0, gb_h)
    coexist = bool(tip_clean and tip_mdd_pass and held_ok and sealed_ok and gb_ok and score > 0)
    return {
        "id": rid,
        "mechanism": mech,
        "meta": meta,
        "windows": chal_w,
        "held_cagr": ch.get("cagr"),
        "held_mdd": ch.get("max_drawdown"),
        "sealed_cagr": cs.get("cagr"),
        "sealed_mdd": cs.get("max_drawdown"),
        "held_mdd_improve_pp": round(float(mdd_h), 4),
        "sealed_mdd_improve_pp": round(float(mdd_s), 4),
        "held_cagr_giveback_pp": round(gb_h, 4),
        "held_cagr_lift_pp": round(-gb_h, 4),
        "score_mdd": round(score, 4),
        "tip": tip,
        "tip_mdd": tip_m,
        "tip_clean": tip_clean,
        "tip_mdd_ok": tip_mdd_pass,
        "held_mdd_ok": held_ok,
        "sealed_mdd_ok": sealed_ok,
        "giveback_ok": gb_ok,
        "coexist": coexist,
    }


def main() -> int:
    for d in (OUT / "outputs", REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.9]
    assert soft.FIN == PUB_R1

    print("loading extended market ...", flush=True)
    market = build_extended_market()
    dividends = load_dividends()
    _p, _s, target, regime = e50.e16_features(market)

    books: dict[str, Any] = {}

    print("BASE_PUB_KD_COOL ...", flush=True)
    base_nav, _, _, base_exp, _ = _with_cool(
        market,
        target,
        regime,
        dividends,
        fin_codes=PUB_R1,
        financial_alloc=FIN_PRE_EXDIV_KD,
    )
    books["BASE_PUB_KD_COOL"] = {"nav": base_nav, "exp": base_exp}
    base_w = _pack_windows(base_nav)
    base_exp.to_frame("e45_exposure").to_csv(OUT / "outputs" / "exposure_BASE_PUB_KD_COOL.csv")
    asof = pd.Timestamp(pd.to_datetime(base_nav["date"]).max())

    rows = []
    for share in PUB_SHARES:
        for pol in PRIV_POLICIES:
            tag = "EQ" if pol == FIN_EQUAL else "KD"
            rid = f"DUAL_p{int(share * 100):02d}_{tag}_COOL"
            print(f"  {rid} ...", flush=True)
            nav, fills, meta, exp, _ = _with_cool(
                market,
                target,
                regime,
                dividends,
                fin_codes=list(PUB_R1) + list(PRIV_R3R4),
                financial_alloc=FIN_DUAL_PUB_PRIV,
                fin_mix_lambda=float(share),
                fin_dual_pub_codes=PUB_R1,
                fin_dual_priv_codes=PRIV_R3R4,
                fin_dual_pub_policy=FIN_PRE_EXDIV_KD,
                fin_dual_priv_policy=pol,
            )
            books[rid] = {"nav": nav, "exp": exp}
            end_pos = meta.get("end_positions") or {}
            row = _score_row(
                base_w,
                _pack_windows(nav),
                base_nav,
                nav,
                rid=rid,
                mech="DUAL_SPLIT_COOL",
                meta={
                    "pub_share": float(share),
                    "priv_policy": pol,
                    "tip_pub": sum(
                        1 for c in PUB_R1 if abs(float(end_pos.get(c, 0.0))) >= LOT - 1e-9
                    ),
                    "tip_priv": sum(
                        1
                        for c in PRIV_R3R4
                        if abs(float(end_pos.get(c, 0.0))) >= LOT - 1e-9
                    ),
                    "n_fills": int(len(fills)),
                },
                asof=asof,
            )
            rows.append(row)

    for rid, book in books.items():
        book["nav"].to_csv(OUT / "outputs" / f"nav_{rid}.csv", index=False)

    coexist = [r for r in rows if r["coexist"]]
    held_only = [
        r
        for r in rows
        if r["tip_clean"]
        and r["tip_mdd_ok"]
        and r["held_mdd_ok"]
        and r["giveback_ok"]
        and not r["sealed_mdd_ok"]
    ]
    if coexist:
        verdict = "COOL_COEXIST_HIT"
    elif held_only:
        verdict = "HELD_ONLY"
    else:
        verdict = "NO_COEXIST"

    ranked = sorted(rows, key=lambda r: (-r["score_mdd"], -r["held_cagr_lift_pp"]))

    payload = {
        "schema_version": "pub_priv_cool_coexist_stagea_v1",
        "charter_id": CHARTER_ID,
        "screen_id": SCREEN_ID,
        "generated_at_utc": _utc(),
        "verdict": verdict,
        "live_wire": False,
        "soft_frozen_keep": True,
        "cool_frozen": True,
        "base_id": "BASE_PUB_KD_COOL",
        "e22_books_version": E22_VERSION,
        "base_windows": base_w,
        "n_challengers": len(rows),
        "coexist_ids": [r["id"] for r in coexist],
        "held_only_ids": [r["id"] for r in held_only],
        "best": ranked[0]["id"] if ranked else None,
        "rows": ranked,
        "prior_stop": "PUB_PRIV_COEXIST_MDD_DECISION_PACK (0 sealed coexist pre-COOL)",
        "non_actions": [
            "No Soft-Frozen live membership change",
            "No e21 universe expand from Stage A",
            "No DH re-enable / stack",
        ],
    }

    def fmt_pct(x):
        return "n/a" if x is None else f"{100.0 * float(x):.2f}%"

    def fmt_pp(x):
        return "n/a" if x is None else f"{float(x):+.2f}pp"

    bh = base_w[HELDOUT]
    bs = base_w[SEALED]
    lines = [
        "# 公股＋民營並存 under COOL — Stage A screen",
        "",
        f"Generated: `{payload['generated_at_utc']}`  ",
        f"Verdict: **`{verdict}`** · base `BASE_PUB_KD_COOL` · Soft-Frozen KEEP · COOL frozen · **no live wire**",
        "",
        f"Base held {fmt_pct(bh['cagr'])} / {fmt_pct(bh['max_drawdown'])} · "
        f"sealed {fmt_pct(bs['cagr'])} / {fmt_pct(bs['max_drawdown'])}",
        "",
        f"Coexist: `{payload['coexist_ids']}` · Held-only: `{payload['held_only_ids']}`",
        "",
        "## Challengers vs BASE_PUB_KD_COOL",
        "",
        "| id | pub% | priv | held CAGR | held MDD | sealed MDD | MDD↑h | MDD↑s | CAGR lift | tip | coexist |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|:---:|:---:|",
    ]
    for r in ranked:
        m = r["meta"]
        lines.append(
            f"| `{r['id']}` | {100 * m['pub_share']:.0f} | `{m['priv_policy']}` | "
            f"{fmt_pct(r['held_cagr'])} | {fmt_pct(r['held_mdd'])} | {fmt_pct(r['sealed_mdd'])} | "
            f"{fmt_pp(r['held_mdd_improve_pp'])} | {fmt_pp(r['sealed_mdd_improve_pp'])} | "
            f"{fmt_pp(r['held_cagr_lift_pp'])} | "
            f"{'Y' if r['tip_clean'] and r['tip_mdd_ok'] else 'N'} | "
            f"{'Y' if r['coexist'] else 'N'} |"
        )
    lines += [
        "",
        "## Reading",
        "",
        "- Prior STOP had 0 sealed-MDD coexist without COOL.",
        "- This screen freezes live `COOL_c8` on every book.",
        "- Even HIT → paper observe only; live universe expand needs ACCEPT.",
        "",
        f"Repro: `repro/pub-priv-cool-coexist-stagea/`",
        "",
        f"Label: `{SCREEN_ID}_{_utc()[:10]}__{verdict}__NO_LIVE_WIRE`",
        "",
    ]

    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    (OUT / "outputs" / "stagea_summary.json").write_text(text, encoding="utf-8")
    (REP / f"{SCREEN_ID}.json").write_text(text, encoding="utf-8")
    (OPS / f"{SCREEN_ID}.json").write_text(text, encoding="utf-8")
    md = "\n".join(lines) + "\n"
    (REP / f"{SCREEN_ID}.md").write_text(md, encoding="utf-8")
    (OPS / f"{SCREEN_ID}.md").write_text(md, encoding="utf-8")

    # Decision pack
    status = "STAGE_A_" + verdict
    decision = {
        "label": "PUB_PRIV_COOL_COEXIST_DECISION",
        "generated_at_utc": _utc(),
        "status": status,
        "verdict": verdict,
        "coexist_ids": payload["coexist_ids"],
        "held_only_ids": payload["held_only_ids"],
        "best": payload["best"],
        "binding": [
            "Soft-Frozen Financial membership stays 公股 R1 until dedicated ACCEPT",
            "Do not live-expand e21 universe from this Stage A",
            "COOL live KEEP independent of this paper screen",
        ],
        "next": (
            "Open Stage B dual-paper observe on coexist_ids"
            if coexist
            else "STOP or new mechanism — COOL alone did not clear sealed coexist"
        ),
        "charter": f"research/ops/{CHARTER_ID}.md",
        "stage_a": f"research/ops/{SCREEN_ID}.md",
    }
    (OPS / "PUB_PRIV_COOL_COEXIST_DECISION_PACK.json").write_text(
        json.dumps(decision, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    dlines = [
        "# 公股＋民營並存 under COOL — Decision Pack",
        "",
        f"Date: 2026-09-25 · `{decision['generated_at_utc']}`  ",
        f"Status: **{verdict}** · Soft-Frozen **KEEP** · live wire **false**",
        "",
        "## Verdict",
        "",
    ]
    if coexist:
        dlines += [f"**COOL_COEXIST_HIT** ({len(coexist)}):", ""] + [
            f"- `{x}`" for x in decision["coexist_ids"]
        ]
    elif held_only:
        dlines += [
            "**HELD_ONLY** — tip+held MDD OK for some books; **sealed MDD still fails** (same binding pattern as pre-COOL STOP).",
            "",
            "Held-only ids:",
            "",
        ] + [f"- `{x}`" for x in decision["held_only_ids"]]
    else:
        dlines += [
            "**NO_COEXIST** — frozen COOL does not unlock 公+民 MDD coexist on this finite dollar-split grid.",
            "",
        ]
    dlines += [
        "",
        "## Binding",
        "",
    ] + [f"{i}. {b}" for i, b in enumerate(decision["binding"], 1)]
    dlines += [
        "",
        f"Next: {decision['next']}",
        "",
        f"Label: `PUB_PRIV_COOL_COEXIST_DECISION_2026-09-25__{verdict}`",
        "",
    ]
    (OPS / "PUB_PRIV_COOL_COEXIST_DECISION_PACK.md").write_text(
        "\n".join(dlines) + "\n", encoding="utf-8"
    )
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
