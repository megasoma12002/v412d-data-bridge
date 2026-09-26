#!/usr/bin/env python3
"""COOL defend-entry pulse: buy 00632R for H sessions then sell. Stage A paper.

Charter: research/ops/COOL_T50_INV_PULSE_CHARTER.md
Parent full-dwell satellite was COOL_INV_SOFT (CAGR↓). Soft-Frozen KEEP.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

import cool_t50_inv_satellite_stagea as sat
import e16_soft_frozen_base as soft
from cool_c8_proxy_observe_helpers import FLOOR

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "cool-t50-inv-pulse-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "COOL_T50_INV_PULSE_CHARTER"
SCREEN_ID = "COOL_T50_INV_PULSE_STAGEA_SCREEN"
BASE_ID = sat.BASE_ID
DEF_CODE = sat.DEF_CODE
HELDOUT = sat.HELDOUT
SEALED = sat.SEALED

HOLD_H = (1, 2, 3, 5)
ALPHAS = (0.50, 1.00)
PULSE_UNIT = 1.0 - float(FLOOR)  # 0.50 residual while defending


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def defend_entries(cool: pd.Series) -> pd.Series:
    """True on first day of each defending streak (1 → <1)."""
    c = cool.astype(float)
    prev = c.shift(1).fillna(1.0)
    return (prev >= 1.0 - 1e-12) & (c < 1.0 - 1e-12)


def build_pulse_schedule(
    target3: pd.DataFrame,
    cool: pd.Series,
    *,
    alpha: float,
    hold_h: int,
    listed_from: pd.Timestamp,
) -> pd.DataFrame:
    idx = target3.index
    c = cool.reindex(idx).fillna(1.0).astype(float).clip(0.0, 1.0)
    entries = defend_entries(c)
    listed = pd.Series(idx >= listed_from, index=idx)
    # Pulse mask: H sessions from each entry (inclusive)
    pulse = pd.Series(False, index=idx)
    entry_locs = [i for i, v in enumerate(entries.to_numpy()) if v and bool(listed.iloc[i])]
    n = len(idx)
    for i0 in entry_locs:
        for k in range(int(hold_h)):
            j = i0 + k
            if j < n:
                pulse.iloc[j] = True
    def_w = pd.Series(0.0, index=idx, dtype=float)
    def_w = def_w.where(~pulse, float(alpha) * float(PULSE_UNIT))
    # No DEF before listing
    def_w = def_w.where(listed, 0.0)
    sched = pd.DataFrame(
        {
            "Financial": target3["Financial"].astype(float) * c,
            "Telecom": target3["Telecom"].astype(float) * c,
            "0050": target3["0050"].astype(float) * c,
            "DEF": def_w.astype(float),
        },
        index=idx,
    )
    return sched, float(pulse.mean()), int(pulse.sum()), int(len(entry_locs))


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.8]

    print("loading ...", flush=True)
    market0 = sat.load_market()
    dividends = sat.load_dividends()
    inv = sat.load_inv_bars()
    market, listed_from = sat.attach_inv(market0, inv)

    from e50_early_stack_combined_nav import FIN, e16_features
    from soft_assist_helpers import LIVE_KD
    from within_sleeve_alloc import build_kd_season_tilt_scores, build_pre_exdiv_window_buy_ok
    from ta_indicator_catalog import build_low_high_catalog

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

    print("offense + cool ...", flush=True)
    fuse_off, _, _ = sat._sim(
        market0,
        tgt_live,
        regime,
        dividends,
        scores=buy_live,
        buy_ok=buy_ok,
        sell=sell_live,
        exposure=pd.Series(1.0, index=tgt_live.index),
    )
    cool = sat._cool_from_offense(market0, fuse_off)
    cool.to_frame("cool_exposure").to_csv(OUT / "exposure_cool.csv")
    n_entries = int(defend_entries(cool).sum())
    print(f"defend_entries={n_entries} listed_from={listed_from.date()}", flush=True)

    print(f"{BASE_ID} ...", flush=True)
    base_nav, n_base, _ = sat._sim(
        market0,
        tgt_live,
        regime,
        dividends,
        scores=buy_live,
        buy_ok=buy_ok,
        sell=sell_live,
        exposure=cool,
    )
    base_nav.to_csv(OUT / f"nav_{BASE_ID}.csv", index=False)
    base_w = sat._pack(base_nav)

    books: list[tuple[str, float, int]] = []
    for h in HOLD_H:
        for a in ALPHAS:
            books.append((f"PULSE_H{h}_A{int(a*100):02d}", float(a), int(h)))

    rows = []
    tip0 = sat._tip(base_nav, base_nav)
    base_row = sat._score_row(
        base_w,
        base_w,
        tip0,
        rid=BASE_ID,
        alpha=0.0,
        mode="base",
        n_fills=n_base,
        mean_def=0.0,
        defend_frac=float((cool < 1 - 1e-12).mean()),
    )
    base_row["coexist"] = False
    base_row["hold_h"] = 0
    base_row["n_entries"] = n_entries
    rows.append(base_row)

    for i, (bid, alpha, hold_h) in enumerate(books, 1):
        print(f"  [{i}/{len(books)}] {bid} ...", flush=True)
        sched, pulse_frac, pulse_days, n_ent = build_pulse_schedule(
            tgt_live, cool, alpha=alpha, hold_h=hold_h, listed_from=listed_from
        )
        sched.to_csv(OUT / f"schedule_{bid}.csv")
        nav, n_fills, _ = sat._sim(
            market,
            tgt_live,
            regime,
            dividends,
            scores=buy_live,
            buy_ok=buy_ok,
            sell=sell_live,
            schedule=sched,
        )
        nav.to_csv(OUT / f"nav_{bid}.csv", index=False)
        tip = sat._tip(base_nav, nav)
        row = sat._score_row(
            base_w,
            sat._pack(nav),
            tip,
            rid=bid,
            alpha=alpha,
            mode="pulse",
            n_fills=n_fills,
            mean_def=float(sched["DEF"].mean()),
            defend_frac=pulse_frac,
        )
        row["hold_h"] = hold_h
        row["pulse_days"] = pulse_days
        row["n_entries"] = n_ent
        rows.append(row)

    chal = [r for r in rows if r["mode"] == "pulse"]
    hits = [r for r in chal if r["coexist"]]
    softs = [
        r
        for r in chal
        if r["gates"]["sealed_mdd"]
        and r["gates"]["held_mdd"]
        and r["gates"]["tip_mdd_ok"]
        and not r["gates"]["held_cagr_floor"]
    ]
    if hits:
        verdict = "COOL_INV_PULSE_HIT"
    elif softs:
        verdict = "COOL_INV_PULSE_SOFT"
    elif any(r["gates"]["tip_clean"] for r in chal):
        verdict = "MDD_BLOCK"
    else:
        verdict = "NO_LIFT"

    ranked = sorted(chal, key=lambda r: -float(r["score"]))
    payload = {
        "generated_at_utc": _utc(),
        "label": SCREEN_ID,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "parent": "research/ops/COOL_T50_INV_SATELLITE_DECISION_PACK.md",
        "status": verdict,
        "live_wire": False,
        "soft_frozen_keep": True,
        "def_code": DEF_CODE,
        "n_defend_entries": n_entries,
        "listed_from": str(listed_from.date()),
        "baseline": BASE_ID,
        "baseline_windows": base_w,
        "n_challengers": len(chal),
        "n_coexist": len(hits),
        "coexist_ids": [r["id"] for r in sorted(hits, key=lambda r: -r["score"])],
        "soft_ids": [r["id"] for r in softs],
        "best": (sorted(hits, key=lambda r: -r["score"])[0] if hits else (ranked[0] if ranked else None)),
        "ranked": ranked,
    }
    (REP / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2) + "\n")
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2) + "\n")

    lines = [
        "# COOL × 台50反1 極短期脈衝 — Stage A Screen",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Status: **{verdict}** · baseline `{BASE_ID}` · Soft-Frozen **KEEP** · live wire **false**",
        f"DEF=`{DEF_CODE}` · defend_entries=**{n_entries}** · listed_from **{listed_from.date()}**",
        "",
        f"Coexist / HIT: **{len(hits)}** / {len(chal)}",
        "",
        "## Ranked",
        "",
        "| book | H | α | CAGR↑ held | CAGR↑ seal | MDD↑ held | MDD↑ seal | tip | coexist |",
        "|---|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for r in ranked:
        tip_ok = "Y" if r["gates"]["tip_mdd_ok"] else "N"
        lines.append(
            f"| `{r['id']}` | {r['hold_h']} | {r['alpha']:.2f} | "
            f"{r['held_cagr_lift_pp']:+.2f} | {r['sealed_cagr_lift_pp']:+.2f} | "
            f"{r['held_mdd_improve_pp']:+.2f} | {r['sealed_mdd_improve_pp']:+.2f} | "
            f"{tip_ok} | {'Y' if r['coexist'] else 'N'} |"
        )
    lines += [
        "",
        "## Binding",
        "",
        "1. Soft-Frozen live + COOL_c8 **KEEP**.",
        "2. Parent full-dwell satellite remains SOFT (CAGR↓); pulse is the short-hold test.",
        "3. Even HIT → paper observe only.",
        "",
        "Repro: `PYTHONPATH=scripts python3 scripts/cool_t50_inv_pulse_stagea.py`",
        "",
        f"Label: `{SCREEN_ID}_{payload['generated_at_utc'][:10]}__{verdict}`",
        "",
    ]
    md = "\n".join(lines)
    (REP / f"{SCREEN_ID}.md").write_text(md)
    (OPS / f"{SCREEN_ID}.md").write_text(md)

    decision = {
        "label": "COOL_T50_INV_PULSE_DECISION",
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
        "# COOL × 台50反1 極短期脈衝 — Decision Pack",
        "",
        f"Date: 2026-09-25 · Generated `{decision['generated_at_utc']}`",
        f"Status: **{verdict}** · Soft-Frozen **KEEP** · live wire **false**",
        "",
        f"Pulse: defend-entry → hold H∈{list(HOLD_H)} · α∈{list(ALPHAS)} · then sell.",
        f"Defend entries in sample: **{n_entries}**.",
        "",
        f"Coexist / HIT: **{len(hits)}**.",
        "",
    ]
    if hits:
        b = sorted(hits, key=lambda r: -r["score"])[0]
        dlines += [
            f"Best: `{b['id']}` · held CAGR↑ **{b['held_cagr_lift_pp']:+.2f}** · "
            f"sealed MDD↑ **{b['sealed_mdd_improve_pp']:+.2f}**",
            "",
            "Next: paper observe ballot — not live.",
            "",
        ]
    elif softs:
        b = softs[0]
        dlines += [
            f"SOFT: `{b['id']}` · held CAGR↑ {b['held_cagr_lift_pp']:+.2f} · "
            f"sealed MDD↑ {b['sealed_mdd_improve_pp']:+.2f}.",
            "",
            "Binding: Soft-Frozen KEEP · no live `00632R`.",
            "",
        ]
    else:
        dlines += [
            "No tip-clean MDD-safe CAGR lift under pulse grid.",
            "",
            "Binding: Soft-Frozen KEEP · pulse does not rescue parent CAGR↓ pattern by default.",
            "",
        ]
    dlines += [f"Label: `COOL_T50_INV_PULSE_DECISION_2026-09-25__{verdict}`", ""]
    (OPS / "COOL_T50_INV_PULSE_DECISION_PACK.json").write_text(json.dumps(decision, indent=2) + "\n")
    (OPS / "COOL_T50_INV_PULSE_DECISION_PACK.md").write_text("\n".join(dlines))
    print(json.dumps({"verdict": verdict, "n_coexist": len(hits), "soft_ids": payload["soft_ids"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
