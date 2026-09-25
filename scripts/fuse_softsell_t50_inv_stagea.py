#!/usr/bin/env python3
"""FUSE Soft-sell active → hold 00632R; sell when Soft-sell clears. Stage A.

Charter: research/ops/FUSE_SOFTSELL_T50_INV_CHARTER.md
FUSE is always-on; gate = Soft RSI6_GT80 on any FIN name.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import cool_t50_inv_satellite_stagea as sat
import e16_soft_frozen_base as soft
from soft_assist_helpers import SELL_HIGH_ID
from ta_indicator_catalog import build_low_high_catalog
from e50_early_stack_combined_nav import FIN, e16_features
from soft_assist_helpers import LIVE_KD
from within_sleeve_alloc import build_kd_season_tilt_scores, build_pre_exdiv_window_buy_ok

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "fuse-softsell-t50-inv-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FUSE_SOFTSELL_T50_INV_CHARTER"
SCREEN_ID = "FUSE_SOFTSELL_T50_INV_STAGEA_SCREEN"
BASE_ID = sat.BASE_ID
DEF_CODE = sat.DEF_CODE

ALPHAS = (0.50, 1.00)
HOLD_H = (1, 2)
DEF_UNIT = 0.25  # portfolio weight unit while gated


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def soft_sell_gate(highs: dict, index: pd.DatetimeIndex) -> pd.Series:
    """True when any Financial name has RSI6_GT80."""
    panel = highs[SELL_HIGH_ID]
    fin_cols = [c for c in FIN if c in panel.columns]
    g = panel[fin_cols].astype(bool).any(axis=1)
    return g.reindex(index).fillna(False).astype(bool)


def build_sched(target3, cool, gate, *, alpha, mode, hold_h, listed_from):
    idx = target3.index
    c = cool.reindex(idx).fillna(1.0).astype(float).clip(0.0, 1.0)
    g = gate.reindex(idx).fillna(False).astype(bool)
    listed = pd.Series(idx >= listed_from, index=idx)
    if mode == "dwell":
        on = g & listed
    else:
        # pulse from Soft-sell entries
        prev = g.shift(1).fillna(False)
        entries = g & ~prev & listed
        on = pd.Series(False, index=idx)
        locs = [i for i, v in enumerate(entries.to_numpy()) if v]
        n = len(idx)
        for i0 in locs:
            for k in range(int(hold_h)):
                j = i0 + k
                if j < n:
                    on.iloc[j] = True
    def_w = pd.Series(0.0, index=idx, dtype=float)
    def_w = def_w.where(~on, float(alpha) * float(DEF_UNIT))
    return pd.DataFrame(
        {
            "Financial": target3["Financial"].astype(float) * c,
            "Telecom": target3["Telecom"].astype(float) * c,
            "0050": target3["0050"].astype(float) * c,
            "DEF": def_w.astype(float),
        },
        index=idx,
    ), float(on.mean()), int(on.sum())


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.8]

    print("loading ...", flush=True)
    market0 = sat.load_market()
    dividends = sat.load_dividends()
    inv = sat.load_inv_bars()
    market, listed_from = sat.attach_inv(market0, inv)

    _p, sleeve, _tgt, regime = e16_features(market0)
    cal = pd.DatetimeIndex(pd.to_datetime(market0["date"]).drop_duplicates().sort_values())
    lows, highs = build_low_high_catalog(market0, cal, list(FIN))
    kd = build_kd_season_tilt_scores(
        market0,
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
    buy_live = sat._buy(kd, lows)
    sell_live = sat._sell(highs)
    score_live = sat._sleeve_score(market0, sleeve, float(sat.LIVE_SLEEVE_ALPHA))
    tgt_live = sat._target_live(score_live, regime)
    gate = soft_sell_gate(highs, tgt_live.index)
    gate_frac = float(gate.mean())
    print(f"soft_sell_frac={gate_frac:.4f} listed_from={listed_from.date()}", flush=True)

    fuse_off, _, _ = sat._sim(
        market0, tgt_live, regime, dividends,
        scores=buy_live, buy_ok=buy_ok, sell=sell_live,
        exposure=pd.Series(1.0, index=tgt_live.index),
    )
    cool = sat._cool_from_offense(market0, fuse_off)
    cool.to_frame("cool_exposure").to_csv(OUT / "exposure_cool.csv")

    print(f"{BASE_ID} ...", flush=True)
    base_nav, n_base, _ = sat._sim(
        market0, tgt_live, regime, dividends,
        scores=buy_live, buy_ok=buy_ok, sell=sell_live, exposure=cool,
    )
    base_nav.to_csv(OUT / f"nav_{BASE_ID}.csv", index=False)
    base_w = sat._pack(base_nav)

    books = []
    for a in ALPHAS:
        books.append((f"SS_DWELL_A{int(a*100):02d}", float(a), "dwell", 0))
        for h in HOLD_H:
            books.append((f"SS_PULSE_H{h}_A{int(a*100):02d}", float(a), "pulse", int(h)))

    rows = []
    tip0 = sat._tip(base_nav, base_nav)
    br = sat._score_row(
        base_w, base_w, tip0, rid=BASE_ID, alpha=0.0, mode="base",
        n_fills=n_base, mean_def=0.0, defend_frac=gate_frac,
    )
    br["coexist"] = False
    rows.append(br)

    for i, (bid, alpha, mode, hold_h) in enumerate(books, 1):
        print(f"  [{i}/{len(books)}] {bid} ...", flush=True)
        sched, on_frac, on_days = build_sched(
            tgt_live, cool, gate, alpha=alpha, mode=mode, hold_h=hold_h, listed_from=listed_from
        )
        sched.to_csv(OUT / f"schedule_{bid}.csv")
        nav, n_fills, _ = sat._sim(
            market, tgt_live, regime, dividends,
            scores=buy_live, buy_ok=buy_ok, sell=sell_live, schedule=sched,
        )
        nav.to_csv(OUT / f"nav_{bid}.csv", index=False)
        tip = sat._tip(base_nav, nav)
        row = sat._score_row(
            base_w, sat._pack(nav), tip, rid=bid, alpha=alpha, mode=mode,
            n_fills=n_fills, mean_def=float(sched["DEF"].mean()), defend_frac=on_frac,
        )
        row["hold_h"] = hold_h
        row["on_days"] = on_days
        rows.append(row)

    chal = [r for r in rows if r["id"] != BASE_ID]
    hits = [r for r in chal if r["coexist"]]
    softs = [
        r for r in chal
        if r["gates"]["sealed_mdd"] and r["gates"]["held_mdd"] and r["gates"]["tip_mdd_ok"]
        and not r["gates"]["held_cagr_floor"]
    ]
    if hits:
        verdict = "FUSE_INV_HIT"
    elif softs:
        verdict = "FUSE_INV_SOFT"
    elif any(r["gates"]["tip_clean"] for r in chal):
        verdict = "MDD_BLOCK"
    else:
        verdict = "NO_LIFT"

    ranked = sorted(chal, key=lambda r: -float(r["score"]))
    payload = {
        "generated_at_utc": _utc(),
        "label": SCREEN_ID,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "status": verdict,
        "live_wire": False,
        "soft_frozen_keep": True,
        "soft_sell_frac": round(gate_frac, 6),
        "def_code": DEF_CODE,
        "baseline": BASE_ID,
        "baseline_windows": base_w,
        "n_challengers": len(chal),
        "n_coexist": len(hits),
        "coexist_ids": [r["id"] for r in sorted(hits, key=lambda r: -r["score"])],
        "soft_ids": [r["id"] for r in softs],
        "best": (sorted(hits, key=lambda r: -r["score"])[0] if hits else (ranked[0] if ranked else None)),
        "ranked": ranked,
        "note": "FUSE always-on; gate=Soft RSI6_GT80 any FIN",
    }
    (REP / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2) + "\n")
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2) + "\n")

    lines = [
        "# FUSE Soft-sell × 台50反1 — Stage A Screen",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Status: **{verdict}** · Soft-Frozen **KEEP** · live wire **false**",
        f"Gate=Soft RSI6_GT80 any FIN · frac=**{gate_frac:.2%}** · DEF=`{DEF_CODE}`",
        "",
        f"Coexist / HIT: **{len(hits)}** / {len(chal)}",
        "",
        "| book | mode | α | CAGR↑ held | CAGR↑ seal | MDD↑ held | MDD↑ seal | tip | coexist |",
        "|---|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for r in ranked:
        tip_ok = "Y" if r["gates"]["tip_mdd_ok"] else "N"
        lines.append(
            f"| `{r['id']}` | {r['mode']} | {r['alpha']:.2f} | "
            f"{r['held_cagr_lift_pp']:+.2f} | {r['sealed_cagr_lift_pp']:+.2f} | "
            f"{r['held_mdd_improve_pp']:+.2f} | {r['sealed_mdd_improve_pp']:+.2f} | "
            f"{tip_ok} | {'Y' if r['coexist'] else 'N'} |"
        )
    lines += [
        "",
        "Repro: `PYTHONPATH=scripts python3 scripts/fuse_softsell_t50_inv_stagea.py`",
        "",
        f"Label: `{SCREEN_ID}_{payload['generated_at_utc'][:10]}__{verdict}`",
        "",
    ]
    md = "\n".join(lines)
    (REP / f"{SCREEN_ID}.md").write_text(md)
    (OPS / f"{SCREEN_ID}.md").write_text(md)

    decision = {
        "label": "FUSE_SOFTSELL_T50_INV_DECISION",
        "generated_at_utc": _utc(),
        "status": verdict,
        "live_wire": False,
        "n_coexist": len(hits),
        "coexist_ids": payload["coexist_ids"],
        "soft_ids": payload["soft_ids"],
        "best": None if not payload["best"] else payload["best"]["id"],
        "charter": f"research/ops/{CHARTER_ID}.md",
        "stage_a": f"research/ops/{SCREEN_ID}.md",
    }
    dlines = [
        "# FUSE Soft-sell × 台50反1 — Decision Pack",
        "",
        f"Date: 2026-09-25 · Generated `{decision['generated_at_utc']}`",
        f"Status: **{verdict}** · Soft-Frozen **KEEP** · live wire **false**",
        "",
        "FUSE is always-on; gate = Soft-sell RSI6_GT80 on any FIN.",
        f"Soft-sell day frac ≈ **{gate_frac:.2%}**.",
        "",
        f"Coexist / HIT: **{len(hits)}**.",
        "",
    ]
    if hits:
        b = sorted(hits, key=lambda r: -r["score"])[0]
        dlines += [f"Best: `{b['id']}` · held CAGR↑ {b['held_cagr_lift_pp']:+.2f} · sealed MDD↑ {b['sealed_mdd_improve_pp']:+.2f}", ""]
    elif softs:
        b = softs[0]
        dlines += [f"SOFT: `{b['id']}` · held CAGR↑ {b['held_cagr_lift_pp']:+.2f} · sealed MDD↑ {b['sealed_mdd_improve_pp']:+.2f}", ""]
    else:
        dlines += ["No tip-clean MDD-safe CAGR lift.", ""]
    dlines += [
        "Binding: Soft-Frozen KEEP · no live 00632R.",
        "",
        f"Label: `FUSE_SOFTSELL_T50_INV_DECISION_2026-09-25__{verdict}`",
        "",
    ]
    (OPS / "FUSE_SOFTSELL_T50_INV_DECISION_PACK.json").write_text(json.dumps(decision, indent=2) + "\n")
    (OPS / "FUSE_SOFTSELL_T50_INV_DECISION_PACK.md").write_text("\n".join(dlines))
    print(json.dumps({"verdict": verdict, "n_coexist": len(hits), "soft_ids": payload["soft_ids"], "soft_sell_frac": gate_frac}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
