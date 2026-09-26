#!/usr/bin/env python3
"""民股金控 Gate V8 — AND-confirm stack Stage A (paper only).

Charter: research/ops/PRIV_FINHC_GATE_V8_CHARTER.md
AND(regime, trend[, cool_full]) carve-out — not a V7 single-gate retune.
Soft-Frozen 公股 R1 KEEP · no live wire.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

import e16_soft_frozen_base as soft
import e50_early_stack_combined_nav as e50
import priv_finhc_cagr_mdd_gate_v7_stagea as v7
from e16_private_fin_holdings_rescreen import PRIV_R3R4, PUB_R1, TEL, build_extended_market
from e45_paper_harness import load_dividends
from soft_assist_helpers import LIVE_KD
from ta_indicator_catalog import build_low_high_catalog
from within_sleeve_alloc import build_kd_season_tilt_scores, build_pre_exdiv_window_buy_ok

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "priv-finhc-gate-v8-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "PRIV_FINHC_GATE_V8_CHARTER"
SCREEN_ID = "PRIV_FINHC_GATE_V8_STAGEA_SCREEN"
BASE_ID = "BASE_LIVE_FUSE_COOL"

REG_TREND = (
    ("REG_BULL", "MA60_0050", "BULL_MA60"),
    ("REG_BULL", "MA120_0050", "BULL_MA120"),
    ("REG_BULL_SIDE", "MA60_0050", "BSIDE_MA60"),
    ("REG_BULL_SIDE", "MA120_0050", "BSIDE_MA120"),
)
PRIV_FRACS = (0.05, 0.08, 0.10)
PRIV_POLS = ("EQUAL", "PRIV_KD_MAY")
COOL_FULL_OPTS = (False, True)


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _and_gate(a: pd.Series, b: pd.Series, cool: pd.Series | None = None) -> pd.Series:
    g = a.reindex(b.index).fillna(0.0).astype(float) * b.fillna(0.0).astype(float)
    if cool is not None:
        c = cool.reindex(g.index).fillna(1.0).astype(float)
        g = g * (c >= 1.0 - 1e-12).astype(float)
    return g.clip(0.0, 1.0)


def _build_books() -> list[dict[str, Any]]:
    books = []
    for reg, trend, tag in REG_TREND:
        for cool_full in COOL_FULL_OPTS:
            for frac in PRIV_FRACS:
                for pol in PRIV_POLS:
                    cool_tag = "_COOL1" if cool_full else ""
                    pol_tag = "EQ" if pol == "EQUAL" else "KDMAY"
                    bid = f"V8_{tag}_F{int(frac * 100):02d}_{pol_tag}{cool_tag}"
                    books.append(
                        {
                            "id": bid,
                            "reg": reg,
                            "trend": trend,
                            "tag": tag,
                            "cool_full": cool_full,
                            "frac": float(frac),
                            "pol": pol,
                        }
                    )
    return books


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.8]
    assert list(soft.FIN) == list(PUB_R1)
    books = _build_books()
    assert len(books) <= 48, len(books)
    print(f"grid size={len(books)}", flush=True)

    print("loading extended market ...", flush=True)
    market = build_extended_market()
    dividends = load_dividends()
    _p, sleeve, _tgt, regime = e50.e16_features(market)
    prices = (
        market.pivot(index="date", columns="code", values="adj_close")
        .sort_index()
        .ffill()
    )
    cal = pd.DatetimeIndex(pd.to_datetime(market["date"]).drop_duplicates().sort_values())
    all_fin = list(PUB_R1) + list(PRIV_R3R4)
    lows, highs = build_low_high_catalog(market, cal, all_fin)

    pub_kd = build_kd_season_tilt_scores(
        market,
        dividends,
        list(PUB_R1),
        k_thresh=float(LIVE_KD["k_thresh"]),
        season_start=LIVE_KD["season_start"],
        season_end=LIVE_KD["season_end"],
        pre_days=int(LIVE_KD["pre_days"]),
        active_score=float(LIVE_KD["active_score"]),
    )
    priv_kd = build_kd_season_tilt_scores(
        market,
        dividends,
        list(PRIV_R3R4),
        k_thresh=float(v7.PRIV_KD_MAY["k_thresh"]),
        season_start=v7.PRIV_KD_MAY["season_start"],
        season_end=v7.PRIV_KD_MAY["season_end"],
        pre_days=int(v7.PRIV_KD_MAY["pre_days"]),
        active_score=float(v7.PRIV_KD_MAY["active_score"]),
    )
    buy_ok = build_pre_exdiv_window_buy_ok(
        cal, dividends, all_fin, pre_days=int(LIVE_KD["pre_days"]), also_stock_ex=True
    )
    buy_live = v7._buy(pub_kd, lows)
    sell_live = v7._sell(highs)
    score_live = v7._sleeve_score(market, sleeve, float(v7.LIVE_SLEEVE_ALPHA))
    tgt_live = v7._target_live(score_live, regime)

    print("offense NAV for cool ...", flush=True)
    old_fin, old_all = list(e50.FIN), list(e50.ALL)
    e50.FIN = list(PUB_R1)
    e50.ALL = list(PUB_R1) + list(TEL) + ["0050"]
    try:
        fuse_off, _, _ = v7._sim_three(
            market,
            tgt_live,
            regime,
            dividends,
            scores=buy_live,
            buy_ok=buy_ok,
            sell=sell_live,
            exposure=pd.Series(1.0, index=tgt_live.index),
        )
        cool = v7._cool_from_offense(market, fuse_off)
        cool.to_frame("cool_exposure").to_csv(OUT / "exposure_cool_from_fuse.csv")

        print(f"{BASE_ID} ...", flush=True)
        base_nav, n_base, _ = v7._sim_three(
            market,
            tgt_live,
            regime,
            dividends,
            scores=buy_live,
            buy_ok=buy_ok,
            sell=sell_live,
            exposure=cool,
        )
    finally:
        e50.FIN = old_fin
        e50.ALL = old_all

    base_nav.to_csv(OUT / f"nav_{BASE_ID}.csv", index=False)
    base_w = v7._pack(base_nav)
    components = v7.build_gates(prices, regime)

    rows = []
    for i, book in enumerate(books, 1):
        bid = book["id"]
        print(f"  [{i}/{len(books)}] {bid} ...", flush=True)
        gate = _and_gate(
            components[book["reg"]],
            components[book["trend"]],
            cool if book["cool_full"] else None,
        )
        four = v7.to_four_sleeve(tgt_live, gate, book["frac"])
        sched = v7.scale_schedule(four, cool)
        nav, n_fills, _ = v7._sim_four(
            market,
            sched,
            regime,
            dividends,
            pub_scores=buy_live,
            priv_scores=priv_kd,
            buy_ok=buy_ok,
            sell=sell_live,
            priv_policy=book["pol"],
        )
        nav.to_csv(OUT / f"nav_{bid}.csv", index=False)
        tip = v7._tip(base_nav, nav)
        row = v7._score_row(
            base_w,
            v7._pack(nav),
            tip,
            rid=bid,
            gate=book["tag"] + ("_COOL1" if book["cool_full"] else ""),
            frac=book["frac"],
            pol=book["pol"],
            n_fills=n_fills,
            mean_priv=float(four["FinPriv"].mean()),
            gate_on_frac=float((gate.fillna(0) > 0).mean()),
        )
        row["cool_full"] = book["cool_full"]
        row["reg"] = book["reg"]
        row["trend"] = book["trend"]
        rows.append(row)

    hits = [r for r in rows if r.get("coexist")]
    hits_sorted = sorted(hits, key=lambda r: -float(r["score"]))
    soft_hits = sorted(
        [
            r
            for r in rows
            if r["gates"]["sealed_mdd"]
            and r["gates"]["held_mdd"]
            and r["gates"]["tip_mdd_ok"]
            and not r["gates"]["held_cagr_floor"]
        ],
        key=lambda r: -float(r["score"]),
    )
    if hits:
        verdict = "PRIV_FINHC_V8_HIT"
    elif soft_hits:
        verdict = "PRIV_FINHC_V8_SOFT"
    elif any(r["gates"]["tip_clean"] for r in rows):
        verdict = "MDD_BLOCK"
    else:
        verdict = "NO_LIFT"

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
        "n_soft": len(soft_hits),
        "n_coexist": len(hits),
        "coexist_ids": [r["id"] for r in hits_sorted],
        "soft_ids": [r["id"] for r in soft_hits],
        "best_soft": soft_hits[0]["id"] if soft_hits else None,
        "best_hit": hits_sorted[0]["id"] if hits_sorted else None,
        "ranked": sorted(rows, key=lambda r: -float(r["score"])),
    }
    (REP / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2) + "\n")
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2) + "\n")

    lines = [
        "# 民股金控 Gate V8 — Stage A Screen",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Status: **{verdict}** · baseline `{BASE_ID}` · Soft-Frozen **KEEP** · live wire **false**",
        f"Charter: `{CHARTER_ID}.md`",
        "",
        f"Coexist / HIT: **{len(hits)}** / {len(rows)} · SOFT pocket: **{len(soft_hits)}**",
        "",
        "## Ranked (by score)",
        "",
        "| book | gate | frac | pol | cool1 | CAGR↑ held | CAGR↑ seal | MDD↑ held | MDD↑ seal | tip | coexist |",
        "|---|---|---:|---|:---:|---:|---:|---:|---:|---|---|",
    ]
    for r in payload["ranked"][:30]:
        tip_ok = "Y" if r["gates"]["tip_mdd_ok"] else "N"
        lines.append(
            f"| `{r['id']}` | {r['gate']} | {r['priv_frac']:.2f} | {r['priv_policy']} | "
            f"{'Y' if r.get('cool_full') else 'N'} | "
            f"{r['held_cagr_lift_pp']:+.2f} | {r['sealed_cagr_lift_pp']:+.2f} | "
            f"{r['held_mdd_improve_pp']:+.2f} | {r['sealed_mdd_improve_pp']:+.2f} | "
            f"{tip_ok} | {'Y' if r['coexist'] else 'N'} |"
        )
    lines += [
        "",
        "## Binding",
        "",
        "1. Soft-Frozen live membership stays **公股 R1** until Class D ACCEPT.",
        "2. Even HIT → paper observe ballot only.",
        "3. Do **not** retune V7 single-gate grid from this screen.",
        "",
        f"Repro: `PYTHONPATH=scripts python3 scripts/priv_finhc_gate_v8_stagea.py`",
        "",
        f"Label: `{SCREEN_ID}_{payload['generated_at_utc'][:10]}__{verdict}`",
        "",
    ]
    md = "\n".join(lines)
    (REP / f"{SCREEN_ID}.md").write_text(md)
    (OPS / f"{SCREEN_ID}.md").write_text(md)

    decision = {
        "label": "PRIV_FINHC_GATE_V8_DECISION",
        "generated_at_utc": _utc(),
        "status": verdict,
        "live_wire": False,
        "soft_frozen_keep": True,
        "n_hits": len(hits),
        "n_soft": len(soft_hits),
        "n_coexist": len(hits),
        "coexist_ids": [r["id"] for r in hits_sorted],
        "soft_ids": [r["id"] for r in soft_hits],
        "best_hit": hits_sorted[0]["id"] if hits_sorted else None,
        "best_soft": soft_hits[0]["id"] if soft_hits else None,
        "best": hits_sorted[0]["id"] if hits_sorted else (soft_hits[0]["id"] if soft_hits else None),
        "charter": f"research/ops/{CHARTER_ID}.md",
        "stage_a": f"research/ops/{SCREEN_ID}.md",
    }
    dlines = [
        "# 民股金控 Gate V8 — Decision Pack (Stage A)",
        "",
        f"Date: 2026-09-25 · Generated `{decision['generated_at_utc']}`",
        f"Status: **{verdict}** · Soft-Frozen **KEEP** · live wire **false**",
        "",
        "## Verdict",
        "",
        f"HIT books: **{len(hits)}** · SOFT pocket: **{len(soft_hits)}** / {len(rows)}.",
        "",
    ]
    if hits_sorted:
        b = hits_sorted[0]
        dlines += [
            f"Best HIT: `{b['id']}` · held CAGR↑ {b['held_cagr_lift_pp']:+.2f} · "
            f"sealed MDD↑ {b['sealed_mdd_improve_pp']:+.2f}",
            "",
            "Next: dual-paper observe ballot — not live.",
            "",
        ]
    elif soft_hits:
        b = soft_hits[0]
        dlines += [
            f"Best SOFT: `{b['id']}` · held CAGR↑ {b['held_cagr_lift_pp']:+.2f} · "
            f"sealed MDD↑ {b['sealed_mdd_improve_pp']:+.2f} (CAGR floor fail)",
            "",
            "Binding: Soft-Frozen KEEP · no V7 retune · reopen only new mechanism or floor change.",
            "",
        ]
    else:
        dlines += [
            "No coexist / soft under predeclared AND-confirm grid.",
            "",
            "Binding: Soft-Frozen 公股 R1 KEEP.",
            "",
        ]
    dlines += [
        f"Label: `PRIV_FINHC_GATE_V8_DECISION_2026-09-25__{verdict}`",
        "",
    ]
    (OPS / "PRIV_FINHC_GATE_V8_DECISION_PACK.json").write_text(json.dumps(decision, indent=2) + "\n")
    (OPS / "PRIV_FINHC_GATE_V8_DECISION_PACK.md").write_text("\n".join(dlines))
    (REP / "PRIV_FINHC_GATE_V8_DECISION_PACK.json").write_text(json.dumps(decision, indent=2) + "\n")
    (REP / "PRIV_FINHC_GATE_V8_DECISION_PACK.md").write_text("\n".join(dlines))
    print(json.dumps({"verdict": verdict, "n_hits": len(hits), "n_soft": len(soft_hits)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
