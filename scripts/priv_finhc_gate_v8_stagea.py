#!/usr/bin/env python3
"""民股金控 Gate V8 — AND-confirm stack Stage A (paper only).

Charter: research/ops/PRIV_FINHC_GATE_V8_CHARTER.md
FinPriv carve-out only when ALL active confirms are on (regime ∧ trend [∧ cool_full]).
Soft-Frozen live KEEP · no tip rewrite · no live wire · Class A research.
Do NOT retune/expand the V7 single-gate grid after sealed peek.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import e16_soft_frozen_base as soft
import e22_dividend_accounting as e22div
import e50_early_stack_combined_nav as e50
from e16_private_fin_holdings_rescreen import PRIV_R3R4, PUB_R1, TEL, build_extended_market
from e45_paper_harness import load_dividends
from portfolio_capital import DEFAULT_CAPITAL
from sleeve_tilt_helpers import ALPHA as LIVE_SLEEVE_ALPHA
from soft_assist_helpers import LIVE_KD
from ta_indicator_catalog import build_low_high_catalog
from within_sleeve_alloc import build_kd_season_tilt_scores, build_pre_exdiv_window_buy_ok

# Reuse V7 helpers (same capital / Exact T+1 / E22 / tip / score).
from priv_finhc_cagr_mdd_gate_v7_stagea import (  # noqa: E402
    BASE_ID,
    CAGR_FLOOR_PP,
    PRIV_KD_MAY,
    _buy,
    _cool_from_offense,
    _pack,
    _score_row,
    _sell,
    _sim_four,
    _sim_three,
    _sleeve_score,
    _target_live,
    _tip,
    build_gates,
    scale_schedule,
    to_four_sleeve,
)

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "priv-finhc-gate-v8-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "PRIV_FINHC_GATE_V8_CHARTER"
SCREEN_ID = "PRIV_FINHC_GATE_V8_STAGEA_SCREEN"
DECISION_ID = "PRIV_FINHC_GATE_V8_DECISION_PACK"
E22_VERSION = e22div.DEFAULT_BOOKS_VERSION

# Predeclared AND grid — do not expand after peek.
AND_PAIRS = (
    ("BULL", "REG_BULL", "MA60", "MA60_0050"),
    ("BULL", "REG_BULL", "MA120", "MA120_0050"),
    ("BSIDE", "REG_BULL_SIDE", "MA60", "MA60_0050"),
    ("BSIDE", "REG_BULL_SIDE", "MA120", "MA120_0050"),
)
COOL_FULL_OPTS = (False, True)
PRIV_FRACS = (0.05, 0.08, 0.10)
PRIV_POLS = ("EQUAL", "PRIV_KD_MAY")
MAX_CHALLENGERS = 48


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _and_gate(
    gates: dict[str, pd.Series],
    regime_gid: str,
    trend_gid: str,
    cool: pd.Series,
    cool_full: bool,
) -> pd.Series:
    """Elementwise product of active confirms."""
    g = gates[regime_gid].astype(float) * gates[trend_gid].astype(float)
    if cool_full:
        c1 = (cool.reindex(g.index).fillna(0.0).astype(float) >= 1.0 - 1e-12).astype(float)
        g = g * c1
    return g.clip(0.0, 1.0)


def _book_id(reg_tag: str, trend_tag: str, frac: float, pol: str, cool_full: bool) -> str:
    tag = "EQ" if pol == "EQUAL" else "KDMAY"
    rid = f"V8_{reg_tag}_{trend_tag}_F{int(round(frac * 100)):02d}_{tag}"
    if cool_full:
        rid += "_COOL1"
    return rid


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.8]
    assert list(soft.FIN) == list(PUB_R1)
    assert abs(float(DEFAULT_CAPITAL) - 500_000_000.0) < 1.0

    n_chal = len(AND_PAIRS) * len(COOL_FULL_OPTS) * len(PRIV_FRACS) * len(PRIV_POLS)
    assert n_chal <= MAX_CHALLENGERS, f"grid {n_chal} exceeds cap {MAX_CHALLENGERS}"

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
        k_thresh=float(PRIV_KD_MAY["k_thresh"]),
        season_start=PRIV_KD_MAY["season_start"],
        season_end=PRIV_KD_MAY["season_end"],
        pre_days=int(PRIV_KD_MAY["pre_days"]),
        active_score=float(PRIV_KD_MAY["active_score"]),
    )
    buy_ok = build_pre_exdiv_window_buy_ok(
        cal, dividends, all_fin, pre_days=int(LIVE_KD["pre_days"]), also_stock_ex=True
    )
    buy_live = _buy(pub_kd, lows)
    sell_live = _sell(highs)
    score_live = _sleeve_score(market, sleeve, float(LIVE_SLEEVE_ALPHA))
    tgt_live = _target_live(score_live, regime)

    print("offense NAV for cool ...", flush=True)
    old_fin, old_all = list(e50.FIN), list(e50.ALL)
    e50.FIN = list(PUB_R1)
    e50.ALL = list(PUB_R1) + list(TEL) + ["0050"]
    try:
        fuse_off, _, _ = _sim_three(
            market,
            tgt_live,
            regime,
            dividends,
            scores=buy_live,
            buy_ok=buy_ok,
            sell=sell_live,
            exposure=pd.Series(1.0, index=tgt_live.index),
        )
        cool = _cool_from_offense(market, fuse_off)
        cool.to_frame("cool_exposure").to_csv(OUT / "exposure_cool_from_fuse.csv")

        print(f"{BASE_ID} ...", flush=True)
        base_nav, n_base, _ = _sim_three(
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
    base_w = _pack(base_nav)
    gates = build_gates(prices, regime)

    books: list[tuple[str, str, str, float, str, bool]] = []
    books.append((BASE_ID, "NEVER", "NEVER", 0.0, "EQUAL", False))
    for reg_tag, reg_gid, trend_tag, trend_gid in AND_PAIRS:
        for cool_full in COOL_FULL_OPTS:
            for frac in PRIV_FRACS:
                for pol in PRIV_POLS:
                    bid = _book_id(reg_tag, trend_tag, frac, pol, cool_full)
                    books.append((bid, reg_gid, trend_gid, float(frac), pol, cool_full))

    assert sum(1 for b in books if b[0] != BASE_ID) == n_chal

    rows: list[dict[str, Any]] = []
    for i, (bid, reg_gid, trend_gid, frac, pol, cool_full) in enumerate(books, 1):
        print(f"  [{i}/{len(books)}] {bid} ...", flush=True)
        if bid == BASE_ID:
            tip = _tip(base_nav, base_nav)
            row = _score_row(
                base_w,
                base_w,
                tip,
                rid=bid,
                gate="NEVER",
                frac=frac,
                pol=pol,
                n_fills=n_base,
                mean_priv=0.0,
                gate_on_frac=0.0,
            )
            row["coexist"] = False
            row["is_control"] = True
            row["and_pair"] = None
            row["cool_full"] = False
            rows.append(row)
            continue

        gate = _and_gate(gates, reg_gid, trend_gid, cool, cool_full)
        four = to_four_sleeve(tgt_live, gate, frac)
        sched = scale_schedule(four, cool)
        mean_priv = float(four["FinPriv"].mean())
        gate_on = float((gate.fillna(0) > 0).mean())
        nav, n_fills, _ = _sim_four(
            market,
            sched,
            regime,
            dividends,
            pub_scores=buy_live,
            priv_scores=priv_kd,
            buy_ok=buy_ok,
            sell=sell_live,
            priv_policy=pol,
        )
        nav.to_csv(OUT / f"nav_{bid}.csv", index=False)
        chal_w = _pack(nav)
        tip = _tip(base_nav, nav)
        and_label = f"{reg_gid}∧{trend_gid}" + ("∧COOL1" if cool_full else "")
        row = _score_row(
            base_w,
            chal_w,
            tip,
            rid=bid,
            gate=and_label,
            frac=frac,
            pol=pol,
            n_fills=n_fills,
            mean_priv=mean_priv,
            gate_on_frac=gate_on,
        )
        row["is_control"] = False
        row["and_pair"] = f"{reg_gid}∧{trend_gid}"
        row["cool_full"] = bool(cool_full)
        rows.append(row)

    chal_rows = [r for r in rows if r["id"] != BASE_ID]
    hits = [r for r in chal_rows if r.get("coexist")]
    hits_sorted = sorted(hits, key=lambda r: -float(r["score"]))
    soft_hits = [
        r
        for r in chal_rows
        if r["gates"]["sealed_mdd"]
        and r["gates"]["held_mdd"]
        and r["gates"]["tip_mdd_ok"]
        and not r["gates"]["held_cagr_floor"]
    ]
    soft_sorted = sorted(soft_hits, key=lambda r: -float(r["score"]))

    if hits:
        verdict = "PRIV_FINHC_V8_HIT"
    elif soft_hits:
        verdict = "PRIV_FINHC_V8_SOFT"
    elif any(r["gates"]["tip_clean"] for r in chal_rows):
        verdict = "MDD_BLOCK"
    else:
        verdict = "NO_LIFT"

    best_hit = hits_sorted[0] if hits_sorted else None
    best_soft = soft_sorted[0] if soft_sorted else None
    best_any = (
        best_hit
        or best_soft
        or (sorted(chal_rows, key=lambda r: -float(r["score"]))[0] if chal_rows else None)
    )

    payload = {
        "generated_at_utc": _utc(),
        "label": SCREEN_ID,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "status": verdict,
        "live_wire": False,
        "soft_frozen_keep": True,
        "mechanism": "and_confirm_carve_out_v8",
        "baseline": BASE_ID,
        "baseline_windows": base_w,
        "n_challengers": len(chal_rows),
        "n_hits": len(hits),
        "n_soft": len(soft_hits),
        "hit_ids": [r["id"] for r in hits_sorted],
        "soft_ids": [r["id"] for r in soft_sorted],
        "best_hit": best_hit,
        "best_soft": best_soft,
        "best": best_any,
        "ranked": sorted(chal_rows, key=lambda r: -float(r["score"])),
        "controls": [r for r in rows if r.get("is_control")],
        "grid": {
            "and_pairs": [f"{a}∧{b}" for _, a, _, b in AND_PAIRS],
            "cool_full": list(COOL_FULL_OPTS),
            "priv_frac": list(PRIV_FRACS),
            "priv_policy": list(PRIV_POLS),
            "max_challengers": MAX_CHALLENGERS,
        },
        "e22_version": E22_VERSION,
        "capital": float(DEFAULT_CAPITAL),
        "held_cagr_floor_pp": CAGR_FLOOR_PP,
    }
    (REP / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2) + "\n")
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2) + "\n")

    lines = [
        "# 民股金控 Gate V8 — Stage A Screen (AND-confirm)",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Status: **{verdict}** · baseline `{BASE_ID}` · Soft-Frozen **KEEP** · live wire **false**",
        f"Charter: `{CHARTER_ID}.md`",
        f"Mechanism: AND stack (regime ∧ trend [∧ cool_full]) · challengers **{len(chal_rows)}** / cap {MAX_CHALLENGERS}",
        "",
        f"HIT: **{len(hits)}** · SOFT pocket: **{len(soft_hits)}**",
        "",
        "## Ranked (by score)",
        "",
        "| book | AND gate | frac | pol | cool1 | CAGR↑ held | CAGR↑ seal | MDD↑ held | MDD↑ seal | tip | HIT |",
        "|---|---|---:|---|---|---:|---:|---:|---:|---|---|",
    ]
    for r in payload["ranked"][:30]:
        tip_ok = "Y" if r["gates"]["tip_mdd_ok"] else "N"
        cool1 = "Y" if r.get("cool_full") else "N"
        lines.append(
            f"| `{r['id']}` | {r['gate']} | {r['priv_frac']:.2f} | {r['priv_policy']} | {cool1} | "
            f"{r['held_cagr_lift_pp']:+.2f} | {r['sealed_cagr_lift_pp']:+.2f} | "
            f"{r['held_mdd_improve_pp']:+.2f} | {r['sealed_mdd_improve_pp']:+.2f} | "
            f"{tip_ok} | {'Y' if r['coexist'] else 'N'} |"
        )
    lines += [
        "",
        "## Soft pocket (sealed MDD OK · tip OK · CAGR short of +0.20)",
        "",
    ]
    if soft_sorted:
        lines += [
            "| book | held CAGR↑ | sealed MDD↑ | held MDD↑ | score |",
            "|---|---:|---:|---:|---:|",
        ]
        for r in soft_sorted[:10]:
            lines.append(
                f"| `{r['id']}` | {r['held_cagr_lift_pp']:+.2f} | "
                f"{r['sealed_mdd_improve_pp']:+.2f} | {r['held_mdd_improve_pp']:+.2f} | "
                f"{r['score']:+.3f} |"
            )
    else:
        lines.append("_none_")
    lines += [
        "",
        "## Binding",
        "",
        "1. Soft-Frozen live membership stays **公股 R1** until Class D ACCEPT.",
        "2. Even HIT → paper observe ballot only.",
        "3. Do **not** retune/expand the V7 single-gate grid after sealed peek.",
        "4. Do **not** expand this V8 AND grid after sealed peek.",
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
        "hit_ids": [r["id"] for r in hits_sorted],
        "soft_ids": [r["id"] for r in soft_sorted],
        "best_hit": best_hit["id"] if best_hit else None,
        "best_soft": best_soft["id"] if best_soft else None,
        "best_hit_metrics": None
        if not best_hit
        else {
            "held_cagr_lift_pp": best_hit["held_cagr_lift_pp"],
            "sealed_cagr_lift_pp": best_hit["sealed_cagr_lift_pp"],
            "held_mdd_improve_pp": best_hit["held_mdd_improve_pp"],
            "sealed_mdd_improve_pp": best_hit["sealed_mdd_improve_pp"],
            "score": best_hit["score"],
            "gate": best_hit["gate"],
            "priv_frac": best_hit["priv_frac"],
        },
        "best_soft_metrics": None
        if not best_soft
        else {
            "held_cagr_lift_pp": best_soft["held_cagr_lift_pp"],
            "sealed_cagr_lift_pp": best_soft["sealed_cagr_lift_pp"],
            "held_mdd_improve_pp": best_soft["held_mdd_improve_pp"],
            "sealed_mdd_improve_pp": best_soft["sealed_mdd_improve_pp"],
            "score": best_soft["score"],
            "gate": best_soft["gate"],
            "priv_frac": best_soft["priv_frac"],
        },
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
        f"HIT / coexist: **{len(hits)}** · SOFT pocket: **{len(soft_hits)}** / {len(chal_rows)} challengers.",
        "",
    ]
    if hits_sorted:
        b = hits_sorted[0]
        dlines += [
            f"Best HIT: `{b['id']}` · score **{b['score']:+.3f}** · "
            f"held CAGR↑ {b['held_cagr_lift_pp']:+.2f} · sealed MDD↑ {b['sealed_mdd_improve_pp']:+.2f}",
            "",
            "Next: dual-paper observe ballot (Stage B) — not live.",
            "",
        ]
    elif soft_sorted:
        b = soft_sorted[0]
        dlines += [
            f"Best SOFT: `{b['id']}` · score **{b['score']:+.3f}** · "
            f"held CAGR↑ {b['held_cagr_lift_pp']:+.2f} (short of +0.20) · "
            f"sealed MDD↑ {b['sealed_mdd_improve_pp']:+.2f}",
            "",
            "SOFT ≠ observe authorize by default — needs human ballot.",
            "",
        ]
    else:
        dlines += [
            "No HIT / SOFT under predeclared AND-confirm gates.",
            "",
        ]
    dlines += [
        "## Binding",
        "",
        "1. Soft-Frozen Financial membership stays **公股 R1**.",
        "2. Do **not** live-expand 民股金控 from this Stage A.",
        "3. Do **not** retune/expand V7 single-gate grid or this V8 AND grid after sealed peek.",
        "4. Re-open only with a **new** mechanism or human objective change.",
        "",
        "## Refs",
        "",
        f"- Charter: `{CHARTER_ID}.md`",
        f"- Stage A: `{SCREEN_ID}.md`",
        "- Prior: V7 SOFT observe · N1–V6 STOP · 0b2 STOP",
        "",
        f"Label: `PRIV_FINHC_GATE_V8_DECISION_2026-09-25__{verdict}`",
        "",
    ]
    (OPS / f"{DECISION_ID}.json").write_text(json.dumps(decision, indent=2) + "\n")
    (OPS / f"{DECISION_ID}.md").write_text("\n".join(dlines))
    (REP / f"{DECISION_ID}.json").write_text(json.dumps(decision, indent=2) + "\n")
    (REP / f"{DECISION_ID}.md").write_text("\n".join(dlines))

    # Also update charter status stamp lightly via sidecar note in decision only.
    print(
        json.dumps(
            {
                "verdict": verdict,
                "n_hits": len(hits),
                "n_soft": len(soft_hits),
                "best_hit": decision["best_hit"],
                "best_soft": decision["best_soft"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
