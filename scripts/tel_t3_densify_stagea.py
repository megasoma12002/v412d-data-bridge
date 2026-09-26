#!/usr/bin/env python3
"""TEL within-sleeve densify Stage A — T3 amp/depth/blend · T2 half · near-flat +0.15.

Charter: research/ops/TEL_T3_DENSIFY_STAGEA_CHARTER.md
Parent: TEL_WITHIN_SOFT · T3_COOL_INV_VOL20 +0.16pp · Soft-Frozen KEEP · no live wire.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

import tel_within_sleeve_stagea as tw
from within_sleeve_alloc import TEL_RS_SOFT_TILT

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "tel-t3-densify-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "TEL_T3_DENSIFY_STAGEA_CHARTER"
SCREEN_ID = "TEL_T3_DENSIFY_STAGEA_SCREEN"
DECISION_ID = "TEL_T3_DENSIFY_DECISION_PACK"
BASE_ID = tw.BASE_ID
NEARFLAT_FLOOR_PP = 0.15


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def cool_gate_depth(scores: pd.DataFrame, cool: pd.Series, cool_lt: float) -> pd.DataFrame:
    """Active only when cool < cool_lt; else equal (zeros). cool_lt=1.0 ≡ parent T3."""
    out = scores.copy().astype(float)
    c = cool.reindex(out.index).fillna(1.0).astype(float)
    inactive = c >= float(cool_lt) - 1e-12
    out.loc[inactive, :] = 0.0
    return out


def prop_cool_scores(scores: pd.DataFrame, cool: pd.Series, amp: float) -> pd.DataFrame:
    """Always available but scaled by defense depth (1−cool) × amp."""
    c = cool.reindex(scores.index).fillna(1.0).astype(float)
    depth = (1.0 - c).clip(lower=0.0, upper=1.0)
    return scores.astype(float).mul(depth, axis=0) * float(amp)


def blend_scores(inv_vol: pd.DataFrame, dist60: pd.DataFrame, lam: float) -> pd.DataFrame:
    """λ·DIST60 + (1−λ)·INV_VOL20, clipped."""
    lam = float(lam)
    return ((lam * dist60) + ((1.0 - lam) * inv_vol)).clip(-3.0, 3.0)


def build_challengers() -> list[dict[str, Any]]:
    books: list[dict[str, Any]] = []
    # P1 T3 densify
    for amp in (0.50, 1.00, 1.50):
        for cool_lt in (1.00, 0.50):
            for blend in (0.00, 0.50):
                rid = f"D3_A{int(amp * 100):03d}_C{int(cool_lt * 100):03d}_B{int(blend * 100):02d}"
                books.append(
                    {
                        "id": rid,
                        "track": "P1_T3_DENSIFY",
                        "mode": "cool_gate",
                        "amp": amp,
                        "cool_lt": cool_lt,
                        "blend": blend,
                    }
                )
    # P2 T2 half-open
    for amp in (0.25, 0.50, 0.75, 1.00):
        books.append(
            {
                "id": f"T2_ALWAYS_A{int(amp * 100):02d}",
                "track": "P2_T2_HALF",
                "mode": "always",
                "amp": amp,
                "cool_lt": None,
                "blend": 0.0,
            }
        )
    for amp in (0.50, 1.00):
        books.append(
            {
                "id": f"T2_PROP_A{int(amp * 100):02d}",
                "track": "P2_T2_HALF",
                "mode": "prop",
                "amp": amp,
                "cool_lt": None,
                "blend": 0.0,
            }
        )
    return books


def _score_row(base_w, chal_w, tip, *, rid, track, meta, n_fills) -> dict[str, Any]:
    row = tw._score_row(base_w, chal_w, tip, rid=rid, track=track, meta=meta, n_fills=n_fills)
    lift = row.get("held_cagr_lift_pp")
    mdd_ok = row["gates"]["tip_mdd_ok"] and row["gates"]["held_mdd"] and row["gates"]["sealed_mdd"]
    nearflat = bool(
        mdd_ok and lift is not None and float(lift) >= float(NEARFLAT_FLOOR_PP)
    )
    # soft under densify: MDD OK but short of nearflat floor
    soft_nf = bool(mdd_ok and not nearflat and not row["hit"])
    row["gates"]["held_cagr_nearflat"] = bool(
        lift is not None and float(lift) >= float(NEARFLAT_FLOOR_PP)
    )
    row["nearflat"] = nearflat and not row["hit"]
    row["soft"] = soft_nf  # redefine soft vs parent: short of +0.15
    # keep hit = full +0.20 gates from parent helper
    return row


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    assert tw.soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.8]
    assert abs(tw.SELL_AMP - 0.75) < 1e-9

    books = build_challengers()
    print(f"challengers={len(books)} sell_amp={tw.SELL_AMP}", flush=True)
    print("loading ...", flush=True)
    market = tw.load_market()
    dividends = tw.load_dividends()
    _p, sleeve, _tgt, regime = tw.e16_features(market)
    cal = pd.DatetimeIndex(pd.to_datetime(market["date"]).drop_duplicates().sort_values())
    lows, highs = tw.build_low_high_catalog(market, cal, list(tw.FIN))
    score_live = tw._sleeve_score(market, sleeve, float(tw.LIVE_SLEEVE_ALPHA))
    tgt_live = tw._target_live(score_live, regime)
    sell_live = tw._sell(highs)

    kd_live = tw.build_kd_season_tilt_scores(
        market,
        dividends,
        tw.FIN,
        k_thresh=float(tw.LIVE_KD["k_thresh"]),
        season_start=tw.LIVE_KD["season_start"],
        season_end=tw.LIVE_KD["season_end"],
        pre_days=int(tw.LIVE_KD["pre_days"]),
        active_score=float(tw.LIVE_KD["active_score"]),
    )
    buy_ok_live = tw.build_pre_exdiv_window_buy_ok(
        cal, dividends, tw.FIN, pre_days=int(tw.LIVE_KD["pre_days"]), also_stock_ex=True
    )
    buy_live = tw._buy(kd_live, lows)

    print("building TEL score families ...", flush=True)
    families = tw.build_score_family(market, cal)
    inv = families["INV_VOL20"]
    dist = families["DIST60"]

    print("offense NAV for BASE cool ...", flush=True)
    fuse_off, _ = tw._sim(
        market, tgt_live, regime, dividends, scores=buy_live, buy_ok=buy_ok_live, sell=sell_live
    )
    cool_base = tw._cool_from_offense(market, fuse_off)
    cool_base.to_frame("e45_exposure").to_csv(OUT / "exposure_cool_from_fuse.csv")

    print(f"{BASE_ID} ...", flush=True)
    base_nav, _ = tw._sim(
        market,
        tgt_live,
        regime,
        dividends,
        scores=buy_live,
        buy_ok=buy_ok_live,
        sell=sell_live,
        exposure=cool_base,
    )
    base_w = tw._pack(base_nav)
    base_nav.to_csv(OUT / f"nav_{BASE_ID}.csv", index=False)

    rows: list[dict[str, Any]] = []
    for i, book in enumerate(books, 1):
        rid = book["id"]
        print(f"  [{i}/{len(books)}] {rid} ...", flush=True)
        raw = blend_scores(inv, dist, book["blend"]) * float(book["amp"])
        # offense pass for cool rebuild (use ungated raw for always; cool modes use raw then gate)
        off, _ = tw._sim(
            market,
            tgt_live,
            regime,
            dividends,
            scores=buy_live,
            buy_ok=buy_ok_live,
            sell=sell_live,
            telecom_alloc=TEL_RS_SOFT_TILT,
            tel_scores=raw,
        )
        cool = tw._cool_from_offense(market, off)
        mode = book["mode"]
        if mode == "cool_gate":
            tel_scores = cool_gate_depth(raw, cool, float(book["cool_lt"]))
        elif mode == "prop":
            # re-apply prop on unscaled blend then * amp already in raw — use raw with prop depth/amp
            # raw already has amp; prop should scale by depth only
            c = cool.reindex(raw.index).fillna(1.0).astype(float)
            depth = (1.0 - c).clip(0.0, 1.0)
            tel_scores = raw.astype(float).mul(depth, axis=0)
        else:  # always
            tel_scores = raw

        nav, nf = tw._sim(
            market,
            tgt_live,
            regime,
            dividends,
            scores=buy_live,
            buy_ok=buy_ok_live,
            sell=sell_live,
            exposure=cool,
            telecom_alloc=TEL_RS_SOFT_TILT,
            tel_scores=tel_scores,
        )
        nav.to_csv(OUT / f"nav_{rid}.csv", index=False)
        cool.to_frame("e45_exposure").to_csv(OUT / f"exposure_{rid}.csv")
        rows.append(
            _score_row(
                base_w,
                tw._pack(nav),
                tw._tip(base_nav, nav),
                rid=rid,
                track=book["track"],
                meta={
                    "telecom_alloc": TEL_RS_SOFT_TILT,
                    "mode": mode,
                    "amp": book["amp"],
                    "cool_lt": book["cool_lt"],
                    "blend": book["blend"],
                    "sell_amp": tw.SELL_AMP,
                },
                n_fills=nf,
            )
        )

    hits = [r for r in rows if r["hit"]]
    nearflats = [r for r in rows if r["nearflat"]]
    softs = [r for r in rows if r["soft"]]
    tip_ok_rows = [r for r in rows if r["gates"]["tip_mdd_ok"]]
    mdd_block = [
        r for r in tip_ok_rows if not (r["gates"]["held_mdd"] and r["gates"]["sealed_mdd"])
    ]

    if hits:
        verdict = "TEL_DENSIFY_HIT"
    elif nearflats:
        verdict = "TEL_NEARFLAT_READY"
    elif softs:
        verdict = "TEL_DENSIFY_SOFT"
    elif mdd_block:
        verdict = "MDD_BLOCK"
    else:
        verdict = "NO_LIFT"

    ranked = sorted(
        rows,
        key=lambda r: (
            -int(r["hit"]),
            -int(r["nearflat"]),
            -int(r["soft"]),
            -float(r["held_cagr_lift_pp"] or -9),
            -float(r["sealed_mdd_improve_pp"]),
            -float(r["held_mdd_improve_pp"]),
        ),
    )
    payload = {
        "generated_at_utc": _utc(),
        "label": SCREEN_ID,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "parent": "research/ops/TEL_WITHIN_SLEEVE_DECISION_PACK.md",
        "status": verdict,
        "live_wire": False,
        "soft_frozen_keep": True,
        "baseline": BASE_ID,
        "sell_amp": tw.SELL_AMP,
        "nearflat_floor_pp": NEARFLAT_FLOOR_PP,
        "cagr_floor_pp": tw.CAGR_FLOOR_PP,
        "baseline_windows": base_w,
        "n_challengers": len(rows),
        "n_hits": len(hits),
        "n_nearflat": len(nearflats),
        "n_soft": len(softs),
        "hit_ids": [r["id"] for r in ranked if r["hit"]],
        "nearflat_ids": [r["id"] for r in ranked if r["nearflat"]],
        "soft_ids": [r["id"] for r in ranked if r["soft"]],
        "mdd_block_ids": [r["id"] for r in mdd_block],
        "ranked": ranked,
    }
    (REP / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2) + "\n")
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2) + "\n")

    lines = [
        "# TEL T3 densify / T2 half / near-flat — Stage A Screen",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Verdict: **`{verdict}`** · base `{BASE_ID}` · Soft-Frozen KEEP · **no live wire**",
        f"Floors: HIT +{tw.CAGR_FLOOR_PP:.2f}pp · near-flat +{NEARFLAT_FLOOR_PP:.2f}pp",
        "",
        f"HIT: `{payload['hit_ids']}`",
        f"NEARFLAT: `{payload['nearflat_ids']}`",
        f"SOFT (<+0.15): `{payload['soft_ids']}`",
        f"MDD_BLOCK: `{payload['mdd_block_ids']}`",
        "",
        "| id | track | CAGR↑h | MDD↑h | MDD↑s | tip | nf | hit |",
        "|---|---|---:|---:|---:|:---:|:---:|:---:|",
    ]
    for r in ranked:
        lines.append(
            f"| `{r['id']}` | {r['track']} | {r['held_cagr_lift_pp']:+.2f}pp | "
            f"{r['held_mdd_improve_pp']:+.2f}pp | {r['sealed_mdd_improve_pp']:+.2f}pp | "
            f"{'Y' if r['gates']['tip_mdd_ok'] else 'N'} | "
            f"{'Y' if r['nearflat'] or r['hit'] else 'N'} | {'Y' if r['hit'] else 'N'} |"
        )
    lines += [
        "",
        "Repro: `PYTHONPATH=scripts python3 scripts/tel_t3_densify_stagea.py`",
        "",
        f"Label: `{SCREEN_ID}_{payload['generated_at_utc'][:10]}__{verdict}`",
        "",
    ]
    md = "\n".join(lines)
    (REP / f"{SCREEN_ID}.md").write_text(md)
    (OPS / f"{SCREEN_ID}.md").write_text(md)

    best = ranked[0] if ranked else None
    best_hit = next((r for r in ranked if r["hit"]), None)
    best_nf = next((r for r in ranked if r["nearflat"]), None)
    best_soft = next((r for r in ranked if r["soft"]), None)

    if hits:
        nxt = "Open paper observe ballot on hit_ids (no live from Stage A)"
    elif nearflats:
        nxt = (
            "NEARFLAT_READY under floor +0.15 — needs human ACCEPT near-flat ballot "
            "(paper observe only; ≠ live wire)"
        )
    elif softs:
        nxt = "STOP densify same axes; CAGR still short of near-flat +0.15"
    else:
        nxt = "STOP densify; next lever ≠ Soft-Frozen / ≠ reopen STOP KD"

    decision = {
        "label": DECISION_ID,
        "generated_at_utc": _utc(),
        "status": verdict,
        "verdict": verdict,
        "live_wire": False,
        "n_hits": len(hits),
        "n_nearflat": len(nearflats),
        "n_soft": len(softs),
        "hit_ids": payload["hit_ids"],
        "nearflat_ids": payload["nearflat_ids"],
        "soft_ids": payload["soft_ids"],
        "mdd_block_ids": payload["mdd_block_ids"],
        "best": best["id"] if best else None,
        "best_metrics": None
        if best is None
        else {
            "id": best["id"],
            "track": best["track"],
            "held_cagr_lift_pp": best.get("held_cagr_lift_pp"),
            "held_mdd_improve_pp": best.get("held_mdd_improve_pp"),
            "sealed_mdd_improve_pp": best.get("sealed_mdd_improve_pp"),
            "gates": best.get("gates"),
            "hit": best.get("hit"),
            "nearflat": best.get("nearflat"),
            "soft": best.get("soft"),
            "meta": best.get("meta"),
        },
        "path_summary": {
            "P1_T3_DENSIFY": {
                "n": sum(1 for r in rows if r["track"] == "P1_T3_DENSIFY"),
                "hits": [r["id"] for r in ranked if r["track"] == "P1_T3_DENSIFY" and r["hit"]],
                "nearflat": [
                    r["id"] for r in ranked if r["track"] == "P1_T3_DENSIFY" and r["nearflat"]
                ],
            },
            "P2_T2_HALF": {
                "n": sum(1 for r in rows if r["track"] == "P2_T2_HALF"),
                "hits": [r["id"] for r in ranked if r["track"] == "P2_T2_HALF" and r["hit"]],
                "nearflat": [
                    r["id"] for r in ranked if r["track"] == "P2_T2_HALF" and r["nearflat"]
                ],
                "sealed_mdd_ok": [
                    r["id"]
                    for r in ranked
                    if r["track"] == "P2_T2_HALF" and r["gates"]["sealed_mdd"]
                ],
            },
            "P3_NEARFLAT": {
                "floor_pp": NEARFLAT_FLOOR_PP,
                "ready_ids": payload["nearflat_ids"] + payload["hit_ids"],
                "accept_needed": bool(nearflats or hits),
            },
        },
        "binding": [
            "Soft-Frozen live clip KEEP until Class D ACCEPT",
            "Live KD_OPT + TEL_EQUAL KEEP until dedicated ACCEPT",
            "Near-flat READY ≠ human ACCEPT ≠ live wire",
            "Do not reopen TEL_PRE_EXDIV_KD / async STOP",
            "CONF_RET3 / 00631L orthogonal KEEP",
        ],
        "next": nxt,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "stage_a": f"research/ops/{SCREEN_ID}.md",
        "order": "research/ops/RESEARCH_ORDER_BETA_DEFENSE.md",
    }

    dlines = [
        "# TEL T3 densify / T2 half / near-flat — Decision Pack",
        "",
        f"Date: 2026-09-26 · Generated `{decision['generated_at_utc']}`",
        f"Status: **{verdict}** · Soft-Frozen **KEEP** · live wire **false**",
        "",
        f"HIT (+0.20): **{len(hits)}** · NEARFLAT (+0.15): **{len(nearflats)}** · "
        f"SOFT: **{len(softs)}** · MDD_BLOCK: **{len(mdd_block)}** / {len(rows)}.",
        "",
    ]
    if best_hit:
        b = best_hit
        dlines.append(
            f"Best HIT: `{b['id']}` · CAGR↑h {b['held_cagr_lift_pp']:+.2f} · "
            f"MDD↑h {b['held_mdd_improve_pp']:+.2f} · MDD↑s {b['sealed_mdd_improve_pp']:+.2f}"
        )
    elif best_nf:
        b = best_nf
        dlines.append(
            f"Best NEARFLAT: `{b['id']}` · CAGR↑h {b['held_cagr_lift_pp']:+.2f} · "
            f"MDD↑h {b['held_mdd_improve_pp']:+.2f} · MDD↑s {b['sealed_mdd_improve_pp']:+.2f}"
        )
        dlines.append("")
        dlines.append(
            "Clears near-flat floor +0.15 + MDD/tip · short of HIT +0.20 · "
            "**needs human ACCEPT** for paper observe (≠ live)."
        )
    elif best_soft:
        b = best_soft
        dlines.append(
            f"Best SOFT: `{b['id']}` · CAGR↑h {b['held_cagr_lift_pp']:+.2f} · "
            f"MDD↑h {b['held_mdd_improve_pp']:+.2f} · MDD↑s {b['sealed_mdd_improve_pp']:+.2f}"
        )
    elif best:
        dlines.append(
            f"Best by CAGR: `{best['id']}` · CAGR↑h {best['held_cagr_lift_pp']:+.2f} · "
            f"MDD↑s {best['sealed_mdd_improve_pp']:+.2f}"
        )

    dlines += [
        "",
        "## Paths",
        "",
        f"- P1 T3 densify: hits={decision['path_summary']['P1_T3_DENSIFY']['hits']} "
        f"nearflat={decision['path_summary']['P1_T3_DENSIFY']['nearflat']}",
        f"- P2 T2 half: sealed_mdd_ok={decision['path_summary']['P2_T2_HALF']['sealed_mdd_ok']} "
        f"nearflat={decision['path_summary']['P2_T2_HALF']['nearflat']}",
        f"- P3 near-flat ready_ids={decision['path_summary']['P3_NEARFLAT']['ready_ids']}",
        "",
        "## Binding",
        "",
    ] + [f"{i}. {b}" for i, b in enumerate(decision["binding"], 1)]
    dlines += [
        "",
        f"Next: {decision['next']}",
        "",
        f"Label: `{DECISION_ID}_2026-09-26__{verdict}`",
        "",
    ]
    for path in (OPS, REP):
        (path / f"{DECISION_ID}.json").write_text(json.dumps(decision, indent=2) + "\n")
        (path / f"{DECISION_ID}.md").write_text("\n".join(dlines) + "\n")
    (OUT / "stagea_summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(
        json.dumps(
            {
                "verdict": verdict,
                "n_hits": len(hits),
                "n_nearflat": len(nearflats),
                "n_soft": len(softs),
                "best": decision["best"],
                "best_metrics": decision["best_metrics"],
                "path_summary": decision["path_summary"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
