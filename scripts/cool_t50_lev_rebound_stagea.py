#!/usr/bin/env python3
"""COOL exit → buy 00631L (台50正2) rebound pulse; Stage A paper only.

Charter: research/ops/COOL_T50_LEV_REBOUND_STAGEA_CHARTER.md
Soft-Frozen live KEEP · COOL_c8 frozen · no live wire.
Live twin includes Soft sell amp 0.75 (SELL_a75).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

import cool_t50_inv_satellite_stagea as sat
from live_config import LIVE_FUSE_SOFT_SELL_BOOST

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "cool-t50-lev-rebound-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "COOL_T50_LEV_REBOUND_STAGEA_CHARTER"
SCREEN_ID = "COOL_T50_LEV_REBOUND_STAGEA_SCREEN"
DECISION_ID = "COOL_T50_LEV_REBOUND_DECISION_PACK"
BASE_ID = "BASE_LIVE_FUSE_COOL"
OFF_CODE = "00631L"
OFF_PRICE = ROOT / "data" / "def_proxies" / "00631L_ohlcv.csv"

ALPHAS = (0.10, 0.25, 0.50)
HOLDS = (3, 5, 10, 21)
SELL_AMP = float(LIVE_FUSE_SOFT_SELL_BOOST)  # SELL_a75 live twin


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def cool_exits(cool: pd.Series) -> pd.Series:
    """True on first day of each full-exposure streak after defending (<1 → 1)."""
    c = cool.astype(float)
    prev = c.shift(1).fillna(1.0)
    return (prev < 1.0 - 1e-12) & (c >= 1.0 - 1e-12)


def defend_entries(cool: pd.Series) -> pd.Series:
    c = cool.astype(float)
    prev = c.shift(1).fillna(1.0)
    return (prev >= 1.0 - 1e-12) & (c < 1.0 - 1e-12)


def build_rebound_schedule(
    target3: pd.DataFrame,
    cool: pd.Series,
    *,
    alpha: float,
    hold_h: int,
    listed_from: pd.Timestamp,
    entry_mode: str = "exit",
) -> tuple[pd.DataFrame, float, int, int]:
    """entry_mode=exit: COOL exit pulse; defend: wrong-timing control; always: constant α."""
    idx = target3.index
    c = cool.reindex(idx).fillna(1.0).astype(float).clip(0.0, 1.0)
    listed = pd.Series(idx >= listed_from, index=idx)

    if entry_mode == "always":
        off_w = pd.Series(float(alpha), index=idx).where(listed, 0.0)
        n_entries = int(listed.sum())
        pulse_frac = float((off_w > 0).mean())
        pulse_days = int((off_w > 0).sum())
        eq = (1.0 - off_w).clip(lower=0.0)
        # still apply COOL scale on Soft sleeves
        sched = pd.DataFrame(
            {
                "Financial": target3["Financial"].astype(float) * c * eq,
                "Telecom": target3["Telecom"].astype(float) * c * eq,
                "0050": target3["0050"].astype(float) * c * eq,
                "DEF": off_w.astype(float),
            },
            index=idx,
        )
        return sched, pulse_frac, pulse_days, n_entries

    entries = cool_exits(c) if entry_mode == "exit" else defend_entries(c)
    pulse = pd.Series(False, index=idx)
    entry_locs = [i for i, v in enumerate(entries.to_numpy()) if v and bool(listed.iloc[i])]
    n = len(idx)
    for i0 in entry_locs:
        for k in range(int(hold_h)):
            j = i0 + k
            if j < n:
                pulse.iloc[j] = True
    off_w = pd.Series(0.0, index=idx, dtype=float)
    off_w = off_w.where(~pulse, float(alpha))
    off_w = off_w.where(listed, 0.0)
    # Soft under COOL, then fund OFF from remaining equity
    soft_scale = c * (1.0 - off_w).clip(lower=0.0)
    sched = pd.DataFrame(
        {
            "Financial": target3["Financial"].astype(float) * soft_scale,
            "Telecom": target3["Telecom"].astype(float) * soft_scale,
            "0050": target3["0050"].astype(float) * soft_scale,
            "DEF": off_w.astype(float),
        },
        index=idx,
    )
    return sched, float(pulse.mean()), int(pulse.sum()), int(len(entry_locs))


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    assert OFF_PRICE.exists(), OFF_PRICE
    assert sat.soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.8]

    # Point satellite helpers at 00631L without editing that module permanently.
    sat.DEF_CODE = OFF_CODE
    sat.DEF_PRICE = OFF_PRICE

    print("loading ...", flush=True)
    market0 = sat.load_market()
    dividends = sat.load_dividends()
    off = sat.load_inv_bars()
    market, listed_from = sat.attach_inv(market0, off)
    print(f"{OFF_CODE} listed_from={listed_from.date()} rows={len(off)} sell_amp={SELL_AMP}", flush=True)

    from e50_early_stack_combined_nav import FIN, e16_features
    from soft_assist_helpers import LIVE_KD
    from ta_indicator_catalog import build_low_high_catalog
    from within_sleeve_alloc import build_kd_season_tilt_scores, build_pre_exdiv_window_buy_ok

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
    sell_live = sat._sell(highs, SELL_AMP)
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
    n_exits = int(cool_exits(cool).sum())
    defend_frac = float((cool < 1.0 - 1e-12).mean())
    print(f"cool_exits={n_exits} defend_frac={defend_frac:.4f}", flush=True)

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

    books: list[tuple[str, float, int | None, str]] = [(BASE_ID, 0.0, None, "base")]
    for a in ALPHAS:
        for h in HOLDS:
            books.append((f"REB_A{int(a * 100):02d}_H{h}", float(a), int(h), "exit"))
    books.append(("ALWAYS_A25", 0.25, None, "always"))
    books.append(("DEFEND_A25_H5", 0.25, 5, "defend"))

    rows: list[dict[str, Any]] = []
    for i, (bid, alpha, hold_h, mode) in enumerate(books, 1):
        print(f"  [{i}/{len(books)}] {bid} ...", flush=True)
        if mode == "base":
            tip = sat._tip(base_nav, base_nav)
            row = sat._score_row(
                base_w,
                base_w,
                tip,
                rid=bid,
                alpha=0.0,
                mode=mode,
                n_fills=n_base,
                mean_def=0.0,
                defend_frac=defend_frac,
            )
            row["hold_h"] = None
            row["n_entries"] = 0
            row["pulse_frac"] = 0.0
            row["coexist"] = False
            rows.append(row)
            continue
        sched, pulse_frac, pulse_days, n_entries = build_rebound_schedule(
            tgt_live,
            cool,
            alpha=float(alpha),
            hold_h=int(hold_h or 1),
            listed_from=listed_from,
            entry_mode=mode,
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
            alpha=float(alpha),
            mode=mode,
            n_fills=n_fills,
            mean_def=float(sched["DEF"].mean()),
            defend_frac=defend_frac,
        )
        row["hold_h"] = hold_h
        row["n_entries"] = n_entries
        row["pulse_frac"] = round(pulse_frac, 6)
        row["pulse_days"] = pulse_days
        rows.append(row)

    chal = [r for r in rows if r["mode"] == "exit"]
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
        verdict = "COOL_LEV_REBOUND_HIT"
    elif softs:
        verdict = "COOL_LEV_REBOUND_SOFT"
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
        "off_code": OFF_CODE,
        "sell_amp": SELL_AMP,
        "cool_defend_frac": round(defend_frac, 6),
        "n_cool_exits": n_exits,
        "listed_from": str(listed_from.date()),
        "baseline": BASE_ID,
        "baseline_windows": base_w,
        "alphas": list(ALPHAS),
        "holds": list(HOLDS),
        "n_challengers": len(chal),
        "n_coexist": len(hits),
        "coexist_ids": [r["id"] for r in sorted(hits, key=lambda r: -r["score"])],
        "soft_ids": [r["id"] for r in softs],
        "best": (sorted(hits, key=lambda r: -r["score"])[0] if hits else (ranked[0] if ranked else None)),
        "ranked": ranked,
        "controls": [r for r in rows if r["mode"] in ("base", "always", "defend")],
    }
    (REP / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2) + "\n")
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2) + "\n")

    lines = [
        "# COOL × 台50正2（00631L）搶反彈 — Stage A Screen",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Status: **`{verdict}`** · baseline `{BASE_ID}` · Soft-Frozen **KEEP** · live wire **false**",
        f"OFF=`{OFF_CODE}` · sell_amp=**{SELL_AMP:g}** · cool defend_frac=**{defend_frac:.2%}** · exits=**{n_exits}** · listed_from **{listed_from.date()}**",
        "",
        f"Coexist / HIT: **{len(hits)}** / {len(chal)}",
        "",
        "## Ranked (exit-pulse books)",
        "",
        "| book | α | H | CAGR↑ held | CAGR↑ seal | MDD↑ held | MDD↑ seal | tip | coexist |",
        "|---|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for r in ranked:
        tip_ok = "Y" if r["gates"]["tip_mdd_ok"] else "N"
        lines.append(
            f"| `{r['id']}` | {r['alpha']:.2f} | {r['hold_h']} | {r['held_cagr_lift_pp']:+.2f} | "
            f"{r['sealed_cagr_lift_pp']:+.2f} | {r['held_mdd_improve_pp']:+.2f} | "
            f"{r['sealed_mdd_improve_pp']:+.2f} | {tip_ok} | {'Y' if r['coexist'] else 'N'} |"
        )
    always = next(r for r in rows if r["id"] == "ALWAYS_A25")
    defend = next(r for r in rows if r["id"] == "DEFEND_A25_H5")
    lines += [
        "",
        "## Controls",
        "",
        f"`ALWAYS_A25`: held CAGR↑ {always['held_cagr_lift_pp']:+.2f} · sealed MDD↑ {always['sealed_mdd_improve_pp']:+.2f} · tip={'Y' if always['gates']['tip_mdd_ok'] else 'N'} (not promote)",
        f"`DEFEND_A25_H5` (wrong timing): held CAGR↑ {defend['held_cagr_lift_pp']:+.2f} · sealed MDD↑ {defend['sealed_mdd_improve_pp']:+.2f} · tip={'Y' if defend['gates']['tip_mdd_ok'] else 'N'}",
        "",
        "## Binding",
        "",
        "1. Soft-Frozen live + COOL_c8 params **KEEP**.",
        "2. Even HIT → paper observe only; live `00631L` needs Class D ACCEPT.",
        "",
        "Repro: `PYTHONPATH=scripts python3 scripts/cool_t50_lev_rebound_stagea.py`",
        "",
        f"Label: `{SCREEN_ID}_{payload['generated_at_utc'][:10]}__{verdict}`",
        "",
    ]
    md = "\n".join(lines)
    (REP / f"{SCREEN_ID}.md").write_text(md)
    (OPS / f"{SCREEN_ID}.md").write_text(md)

    decision = {
        "label": DECISION_ID,
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
        "# COOL × 00631L 搶反彈 — Decision Pack (Stage A)",
        "",
        f"Date: 2026-09-26 · Generated `{decision['generated_at_utc']}`",
        f"Status: **{verdict}** · Soft-Frozen **KEEP** · live wire **false**",
        "",
        "Human: COOL 結束買 `00631L` 短窗搶反彈 · α×H grid · live twin includes SELL_a75.",
        "",
        f"Coexist / HIT: **{len(hits)}** · SOFT pocket: **{len(softs)}**.",
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
        b = sorted(softs, key=lambda r: -r["score"])[0]
        dlines += [
            f"SOFT best: `{b['id']}` · held CAGR↑ {b['held_cagr_lift_pp']:+.2f} · "
            f"sealed MDD↑ {b['sealed_mdd_improve_pp']:+.2f} (CAGR floor miss).",
            "",
            "Binding: Soft-Frozen KEEP · no live `00631L` without new ACCEPT / objective change.",
            "",
        ]
    else:
        dlines += [
            "No tip-clean MDD-safe lift under predeclared gates.",
            "",
            "Binding: Soft-Frozen KEEP · reopen only with new mechanism or human objective change.",
            "",
        ]
    dlines += [
        "## Refs",
        "",
        f"- Charter: `{CHARTER_ID}.md`",
        f"- Screen: `{SCREEN_ID}.md`",
        "",
        f"Label: `{DECISION_ID}_2026-09-26__{verdict}`",
        "",
    ]
    (OPS / f"{DECISION_ID}.json").write_text(json.dumps(decision, indent=2) + "\n")
    (OPS / f"{DECISION_ID}.md").write_text("\n".join(dlines))
    # Update charter status line via note file stamp
    print(json.dumps({"verdict": verdict, "n_coexist": len(hits), "soft_ids": payload["soft_ids"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
