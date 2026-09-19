#!/usr/bin/env python3
"""公股＋民營並存 × MDD Stage A — RESEARCH ONLY.

Charter: research/ops/PUB_PRIV_COEXIST_MDD_CHARTER.md
Soft-Frozen live SSOT untouched · no e21 wire.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import e16_soft_frozen_4sleeve as sf4
import e16_soft_frozen_base as soft
import e50_early_stack_combined_nav as e50
from e16_private_fin_holdings_rescreen import (
    PRIV_R3R4,
    PUB_R1,
    TEL,
    build_extended_market,
    held_score,
    tip_gate,
)
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, window_stats
from research_metric_helpers import mdd_delta_pp
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
OUT = ROOT / "repro/pub-priv-coexist-mdd-stagea"
RESEARCH = ROOT / "research/ops"
CAPITAL = 500_000_000.0
LOT = BOARD_LOT

KD_OPT = {
    "season_start": (4, 15),
    "season_end": (5, 15),
    "k_thresh": 30.0,
    "pre_days": 15,
    "active_score": 1.5,
}

# Mechanism A — dollar-split (predeclared)
PUB_SHARES = [0.90, 0.85, 0.80, 0.75]
PRIV_POLICIES = [FIN_EQUAL, FIN_PRE_EXDIV_KD]

# Mechanism B — 4-sleeve compact MDD grid (predeclared)
FINPUB_CLIP = (0.60, 0.90)
FINPRIV_CLIPS = [(0.00, 0.15), (0.00, 0.20), (0.05, 0.20), (0.05, 0.25)]
PRIOR_PRIV = [0.10, 0.15]

HELDOUT_GB_CAP = 3.0
TIP_MDD_TOL_PP = -0.5


def _kd_panels(market, dividends, codes):
    cal = pd.to_datetime(market["date"]).drop_duplicates().sort_values()
    scores = build_kd_season_tilt_scores(
        market,
        dividends,
        codes,
        k_thresh=float(KD_OPT["k_thresh"]),
        season_start=KD_OPT["season_start"],
        season_end=KD_OPT["season_end"],
        pre_days=int(KD_OPT["pre_days"]),
        active_score=float(KD_OPT["active_score"]),
    )
    buy_ok = build_pre_exdiv_window_buy_ok(
        cal, dividends, codes, pre_days=int(KD_OPT["pre_days"]), also_stock_ex=True
    )
    return scores, buy_ok


def _pack(nav, fills, meta, **extra):
    assert meta.get("exact_t1_ok")
    win = {w: window_stats(nav, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
    return {"nav": nav, "windows": win, "n_fills": int(len(fills)), "meta": meta, **extra}


def tip_mdd_ok(base_nav: pd.DataFrame, chal_nav: pd.DataFrame, asof: pd.Timestamp) -> dict:
    """YTD/1y MDD↑ vs baseline; ok if both ≥ TIP_MDD_TOL_PP."""
    out: dict = {}
    asof = pd.Timestamp(asof)
    b_dates = pd.to_datetime(base_nav["date"])
    c_dates = pd.to_datetime(chal_nav["date"])
    ok_all = True
    for wname, start in (
        ("ytd", pd.Timestamp(asof.year, 1, 1)),
        ("trailing_1y", asof - pd.Timedelta(days=365)),
    ):
        b = base_nav[(b_dates >= start) & (b_dates <= asof)].reset_index(drop=True)
        c = chal_nav[(c_dates >= start) & (c_dates <= asof)].reset_index(drop=True)
        if len(b) < 20 or len(c) < 20:
            out[wname] = {"mdd_improve_pp": None, "ok": False}
            ok_all = False
            continue
        bn = b["nav"].astype(float) / float(b["nav"].iloc[0])
        cn = c["nav"].astype(float) / float(c["nav"].iloc[0])
        b_mdd = float((bn / bn.cummax() - 1.0).min())
        c_mdd = float((cn / cn.cummax() - 1.0).min())
        mdd_pp = float(mdd_delta_pp(b_mdd, c_mdd))
        ok = mdd_pp >= TIP_MDD_TOL_PP
        out[wname] = {"mdd_improve_pp": round(mdd_pp, 4), "ok": ok}
        ok_all = ok_all and ok
    out["ok"] = ok_all
    return out


def score_mdd(held: dict, sealed: dict) -> float:
    gb = held.get("cagr_giveback_pp")
    gb_pen = max(0.0, float(gb)) if gb is not None else 9.0
    return float(held["mdd_improve_pp"]) + 0.5 * float(sealed["mdd_improve_pp"]) - 0.25 * gb_pen


def run_live_pub_kd(market, dividends):
    old_fin, old_all = list(e50.FIN), list(e50.ALL)
    e50.FIN = list(PUB_R1)
    e50.ALL = list(PUB_R1) + list(TEL) + ["0050"]
    try:
        _p, _s, target, regime = e50.e16_features(market)
        scores, buy_ok = _kd_panels(market, dividends, PUB_R1)
        nav, fills, meta = e50.simulate_core(
            market,
            target,
            regime,
            dividends,
            apply_e22=True,
            apply_stock_div=True,
            capital=CAPITAL,
            lot_size=LOT,
            financial_alloc=FIN_PRE_EXDIV_KD,
            telecom_alloc=TEL_EQUAL,
            fin_name_scores=scores,
            fin_buy_ok=buy_ok,
        )
        return _pack(nav, fills, meta, id="LIVE_PUB_KD", mechanism="BASELINE")
    finally:
        e50.FIN = old_fin
        e50.ALL = old_all


def run_dual(market, dividends, target, regime, *, book_id: str, pub_share: float, priv_pol: str):
    old_fin, old_all = list(e50.FIN), list(e50.ALL)
    fin_codes = list(PUB_R1) + list(PRIV_R3R4)
    e50.FIN = fin_codes
    e50.ALL = fin_codes + list(TEL) + ["0050"]
    try:
        scores, buy_ok = _kd_panels(market, dividends, fin_codes)
        nav, fills, meta = e50.simulate_core(
            market,
            target,
            regime,
            dividends,
            apply_e22=True,
            apply_stock_div=True,
            capital=CAPITAL,
            lot_size=LOT,
            financial_alloc=FIN_DUAL_PUB_PRIV,
            telecom_alloc=TEL_EQUAL,
            fin_name_scores=scores,
            fin_buy_ok=buy_ok,
            fin_mix_lambda=float(pub_share),
            fin_dual_pub_codes=PUB_R1,
            fin_dual_priv_codes=PRIV_R3R4,
            fin_dual_pub_policy=FIN_PRE_EXDIV_KD,
            fin_dual_priv_policy=priv_pol,
        )
        end_pos = meta.get("end_positions") or {}
        return _pack(
            nav,
            fills,
            meta,
            id=book_id,
            mechanism="DUAL_SPLIT",
            pub_share=float(pub_share),
            priv_policy=priv_pol,
            tip_pub=sum(1 for c in PUB_R1 if abs(float(end_pos.get(c, 0.0))) >= LOT - 1e-9),
            tip_priv=sum(1 for c in PRIV_R3R4 if abs(float(end_pos.get(c, 0.0))) >= LOT - 1e-9),
        )
    finally:
        e50.FIN = old_fin
        e50.ALL = old_all


def run_sf4(
    market,
    dividends,
    *,
    book_id: str,
    pub_lo,
    pub_hi,
    priv_lo,
    priv_hi,
    prior_frac,
    priv_pol: str,
):
    old_fin, old_all = list(e50.FIN), list(e50.ALL)
    fin_codes = list(PUB_R1) + list(PRIV_R3R4)
    e50.FIN = fin_codes
    e50.ALL = fin_codes + list(TEL) + ["0050"]
    try:
        _prices, _sleeve, target4, regime, _score = sf4.build_4sleeve_targets(
            market,
            fin_pub_lo=pub_lo,
            fin_pub_hi=pub_hi,
            fin_priv_lo=priv_lo,
            fin_priv_hi=priv_hi,
            prior_priv_frac=prior_frac,
        )
        scores, buy_ok = _kd_panels(market, dividends, fin_codes)
        nav, fills, meta = e50.simulate_core(
            market,
            target4,
            regime,
            dividends,
            apply_e22=True,
            apply_stock_div=True,
            capital=CAPITAL,
            lot_size=LOT,
            financial_alloc=FIN_PRE_EXDIV_KD,
            telecom_alloc=TEL_EQUAL,
            fin_name_scores=scores,
            fin_buy_ok=buy_ok,
            fin_pub_codes=PUB_R1,
            fin_priv_codes=PRIV_R3R4,
            fin_pub_alloc=FIN_PRE_EXDIV_KD,
            fin_priv_alloc=priv_pol,
        )
        end_pos = meta.get("end_positions") or {}
        return _pack(
            nav,
            fills,
            meta,
            id=book_id,
            mechanism="SF4_CLIP",
            fin_pub_clip=[pub_lo, pub_hi],
            fin_priv_clip=[priv_lo, priv_hi],
            prior_priv_frac=float(prior_frac),
            priv_policy=priv_pol,
            tip_pub=sum(1 for c in PUB_R1 if abs(float(end_pos.get(c, 0.0))) >= LOT - 1e-9),
            tip_priv=sum(1 for c in PRIV_R3R4 if abs(float(end_pos.get(c, 0.0))) >= LOT - 1e-9),
        )
    finally:
        e50.FIN = old_fin
        e50.ALL = old_all


def rank_row(base, row, asof):
    held = held_score(base["windows"]["heldout_2019_plus"], row["windows"]["heldout_2019_plus"])
    sealed = held_score(base["windows"]["sealed_2023_plus"], row["windows"]["sealed_2023_plus"])
    tip = tip_gate(base["nav"], row["nav"], asof)
    tip_clean = tip["ytd"]["gate"] == "PASS" and tip["trailing_1y"]["gate"] == "PASS"
    tip_m = tip_mdd_ok(base["nav"], row["nav"], asof)
    gb = held.get("cagr_giveback_pp")
    gb_ok = gb is not None and float(gb) <= HELDOUT_GB_CAP
    sm = score_mdd(held, sealed)
    coexist = bool(
        tip_clean
        and tip_m["ok"]
        and float(held["mdd_improve_pp"]) >= 0.0
        and float(sealed["mdd_improve_pp"]) >= 0.0
        and gb_ok
        and sm > 0.0
    )
    return {
        "id": row["id"],
        "mechanism": row.get("mechanism"),
        "pub_share": row.get("pub_share"),
        "fin_pub_clip": row.get("fin_pub_clip"),
        "fin_priv_clip": row.get("fin_priv_clip"),
        "prior_priv_frac": row.get("prior_priv_frac"),
        "priv_policy": row.get("priv_policy"),
        "score_mdd": round(sm, 4),
        "heldout_mdd_improve_pp": round(float(held["mdd_improve_pp"]), 4),
        "sealed_mdd_improve_pp": round(float(sealed["mdd_improve_pp"]), 4),
        "heldout_cagr_giveback_pp": None if gb is None else round(float(gb), 4),
        "legacy_heldout_score": round(float(held["score"]), 4),
        "tip_ytd": tip["ytd"]["gate"],
        "tip_1y": tip["trailing_1y"]["gate"],
        "tip_clean": tip_clean,
        "tip_mdd_ok": tip_m["ok"],
        "tip_mdd_ytd_pp": tip_m["ytd"].get("mdd_improve_pp"),
        "tip_mdd_1y_pp": tip_m["trailing_1y"].get("mdd_improve_pp"),
        "tip_pub": row.get("tip_pub"),
        "tip_priv": row.get("tip_priv"),
        "n_fills": row["n_fills"],
        "gates": {
            "tip_clean": tip_clean,
            "tip_mdd_ok": tip_m["ok"],
            "heldout_mdd": float(held["mdd_improve_pp"]) >= 0.0,
            "sealed_mdd": float(sealed["mdd_improve_pp"]) >= 0.0,
            "giveback_cap": gb_ok,
            "score_mdd_pos": sm > 0.0,
        },
        "coexist": coexist,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "outputs").mkdir(exist_ok=True)
    assert list(soft.SOFT_FROZEN_FIN_CLIP) == [0.6, 0.9]
    assert soft.FIN == PUB_R1

    print("building extended market ...", flush=True)
    market = build_extended_market()
    dividends = load_dividends()

    print("baseline LIVE_PUB_KD ...", flush=True)
    base = run_live_pub_kd(market, dividends)
    results = {"LIVE_PUB_KD": base}

    print("Soft-Frozen 公股 targets for dual-split ...", flush=True)
    old_fin, old_all = list(e50.FIN), list(e50.ALL)
    e50.FIN = list(PUB_R1)
    e50.ALL = list(PUB_R1) + list(TEL) + ["0050"]
    try:
        _p, _s, target3, regime3 = e50.e16_features(market)
    finally:
        e50.FIN = old_fin
        e50.ALL = old_all

    dual_specs = []
    for share in PUB_SHARES:
        for pol in PRIV_POLICIES:
            tag = "EQ" if pol == FIN_EQUAL else "KD"
            dual_specs.append((f"DUAL_P{int(round(share * 100))}_{tag}", share, pol))

    for i, (bid, share, pol) in enumerate(dual_specs, 1):
        print(f"  dual [{i}/{len(dual_specs)}] {bid} ...", flush=True)
        results[bid] = run_dual(
            market, dividends, target3, regime3, book_id=bid, pub_share=share, priv_pol=pol
        )

    print("SF4 control PUB_ONLY ...", flush=True)
    results["SF4_CTRL_PUB_ONLY"] = run_sf4(
        market,
        dividends,
        book_id="SF4_CTRL_PUB_ONLY",
        pub_lo=0.60,
        pub_hi=0.90,
        priv_lo=0.0,
        priv_hi=0.0,
        prior_frac=0.0,
        priv_pol=FIN_EQUAL,
    )

    sf4_specs = []
    for plo, phi in FINPRIV_CLIPS:
        for frac in PRIOR_PRIV:
            for pol in PRIV_POLICIES:
                tag = "EQ" if pol == FIN_EQUAL else "KD"
                bid = (
                    f"SF4_P60-90_V{int(plo * 100)}-{int(phi * 100)}"
                    f"_F{int(frac * 100)}_{tag}"
                )
                sf4_specs.append((bid, FINPUB_CLIP[0], FINPUB_CLIP[1], plo, phi, frac, pol))

    for i, (bid, plo, phi, vlo, vhi, frac, pol) in enumerate(sf4_specs, 1):
        print(f"  sf4 [{i}/{len(sf4_specs)}] {bid} ...", flush=True)
        results[bid] = run_sf4(
            market,
            dividends,
            book_id=bid,
            pub_lo=plo,
            pub_hi=phi,
            priv_lo=vlo,
            priv_hi=vhi,
            prior_frac=frac,
            priv_pol=pol,
        )

    asof = pd.to_datetime(base["nav"]["date"]).max()
    ranked = []
    for bid, row in results.items():
        if bid == "LIVE_PUB_KD":
            continue
        ranked.append(rank_row(base, row, asof))
    ranked.sort(key=lambda r: r["score_mdd"], reverse=True)
    coexist = [r for r in ranked if r["coexist"]]

    if coexist:
        status = "STAGE_A_CANDIDATES"
    elif any(r["score_mdd"] > 0 and r["heldout_mdd_improve_pp"] >= 0 for r in ranked):
        status = "STAGE_A_SCORE_POS_GATES_FAIL"
    else:
        status = "STOP_NO_MDD_COEXIST_VS_LIVE_PUB_KD"

    # Persist NAVs for top-5 + baseline + coexist
    keep_ids = {"LIVE_PUB_KD"} | {r["id"] for r in coexist} | {r["id"] for r in ranked[:5]}
    for bid in keep_ids:
        results[bid]["nav"].to_csv(OUT / "outputs" / f"{bid}_daily_nav.csv", index=False)

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "PUB_PRIV_COEXIST_MDD_STAGE_A",
        "status": status,
        "charter": "research/ops/PUB_PRIV_COEXIST_MDD_CHARTER.md",
        "live_wire": False,
        "soft_frozen_clip": list(soft.SOFT_FROZEN_FIN_CLIP),
        "baseline": "LIVE_PUB_KD",
        "capital": CAPITAL,
        "lot_size": LOT,
        "asof": str(pd.Timestamp(asof).date()),
        "n_challengers": len(ranked),
        "objective": {
            "score_mdd": "MDD_held + 0.5*MDD_sealed - 0.25*max(0, CAGR_gb_held)",
            "heldout_giveback_cap_pp": HELDOUT_GB_CAP,
            "tip_mdd_tol_pp": TIP_MDD_TOL_PP,
        },
        "ranked_vs_live_pub_kd": ranked,
        "coexist_ids": [r["id"] for r in coexist],
        "best": ranked[0] if ranked else None,
    }
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    RESEARCH.joinpath("PUB_PRIV_COEXIST_MDD_STAGE_A.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    def pct(x):
        return "n/a" if x is None else f"{100.0 * float(x):.2f}%"

    abs_base = base["windows"]
    lines = [
        "# 公股＋民營並存 × MDD — Stage A",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Status: **{status}** · baseline **`LIVE_PUB_KD`** · Soft-Frozen **KEEP** · live wire **false**",
        f"Charter: `PUB_PRIV_COEXIST_MDD_CHARTER.md` · asof **{payload['asof']}** · challengers **{len(ranked)}**",
        "",
        f"Baseline heldout CAGR/MDD: **{pct(abs_base['heldout_2019_plus'].get('cagr'))}** / "
        f"**{pct(abs_base['heldout_2019_plus'].get('max_drawdown'))}**",
        f"Baseline sealed CAGR/MDD: **{pct(abs_base['sealed_2023_plus'].get('cagr'))}** / "
        f"**{pct(abs_base['sealed_2023_plus'].get('max_drawdown'))}**",
        "",
        "## Coexist",
        "",
    ]
    if coexist:
        for r in coexist:
            lines.append(f"- `{r['id']}` · score_mdd **{r['score_mdd']}** · mech `{r['mechanism']}`")
    else:
        lines.append("- **None**")
    lines += [
        "",
        "## Ranked vs LIVE_PUB_KD (by score_mdd)",
        "",
        "| book | mech | score_mdd | MDD↑ held | MDD↑ sealed | CAGR gb | tip | tipMDD | coexist |",
        "|---|---|---:|---:|---:|---:|---|---|---|",
    ]
    for r in ranked:
        lines.append(
            f"| `{r['id']}` | `{r['mechanism']}` | {r['score_mdd']:.3f} | "
            f"{r['heldout_mdd_improve_pp']:+.2f} | {r['sealed_mdd_improve_pp']:+.2f} | "
            f"{r['heldout_cagr_giveback_pp']} | "
            f"{'Y' if r['tip_clean'] else 'N'} | {'Y' if r['tip_mdd_ok'] else 'N'} | "
            f"{'Y' if r['coexist'] else 'N'} |"
        )
    lines += [
        "",
        "## Binding",
        "",
        "1. Soft-Frozen live membership stays **公股 R1** until Class D ACCEPT.",
        "2. Do **not** promote `#257` priv-replace from this screen.",
        "3. Coexist → open dual-paper observe ballot (Stage B); else **STOP** this objective.",
        "",
        "Repro: `PYTHONPATH=scripts python3 scripts/e16_pub_priv_coexist_mdd_stage_a.py`",
        f"Repro dir: `{OUT.relative_to(ROOT)}/`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "STAGE_A.md").write_text(md)
    RESEARCH.joinpath("PUB_PRIV_COEXIST_MDD_STAGE_A.md").write_text(md)

    decision = {
        "generated_at_utc": payload["generated_at_utc"],
        "label": "PUB_PRIV_COEXIST_MDD_DECISION",
        "status": status,
        "live_wire": False,
        "soft_frozen_keep": True,
        "coexist_ids": payload["coexist_ids"],
        "best": payload["best"],
        "next": (
            "Open Stage B dual-paper observe on coexist_ids"
            if coexist
            else "STOP — no MDD coexist; do not expand live universe; keep 公股 Soft-Frozen"
        ),
        "charter": "research/ops/PUB_PRIV_COEXIST_MDD_CHARTER.md",
        "stage_a": "research/ops/PUB_PRIV_COEXIST_MDD_STAGE_A.md",
    }
    RESEARCH.joinpath("PUB_PRIV_COEXIST_MDD_DECISION_PACK.json").write_text(
        json.dumps(decision, indent=2, default=str) + "\n"
    )
    dlines = [
        "# 公股＋民營並存 × MDD — Decision Pack (Stage A)",
        "",
        f"Date: 2026-09-19 · Generated `{decision['generated_at_utc']}`",
        f"Status: **{status}** · Soft-Frozen **KEEP** · live wire **false**",
        "",
        "## Verdict",
        "",
    ]
    if coexist:
        dlines += [
            f"**STAGE A CANDIDATES** ({len(coexist)}):",
            "",
            *[f"- `{x}`" for x in decision["coexist_ids"]],
            "",
            "Next: Stage B dual-paper observe ballot (paper only).",
        ]
    else:
        best = decision.get("best") or {}
        dlines += [
            "**STOP** — no book cleared MDD coexist gates vs `LIVE_PUB_KD`.",
            "",
            f"Best by score_mdd: `{best.get('id')}` · score **{best.get('score_mdd')}** · "
            f"held MDD↑ **{best.get('heldout_mdd_improve_pp')}** · "
            f"sealed MDD↑ **{best.get('sealed_mdd_improve_pp')}**",
            "",
            "Binding: keep Soft-Frozen 公股 R1 · do not live-expand 民營 · "
            "do not merge priv-replace as 並存 substitute.",
        ]
    dlines += [
        "",
        "## Refs",
        "",
        "- Charter: `PUB_PRIV_COEXIST_MDD_CHARTER.md`",
        "- Stage A: `PUB_PRIV_COEXIST_MDD_STAGE_A.md`",
        "- Prior STOP: dual-sleeve · 4-sleeve · private holdings",
        "",
        f"Label: `PUB_PRIV_COEXIST_MDD_DECISION_2026-09-19__{status}`",
        "",
    ]
    RESEARCH.joinpath("PUB_PRIV_COEXIST_MDD_DECISION_PACK.md").write_text("\n".join(dlines))

    print(json.dumps({"status": status, "coexist": payload["coexist_ids"], "best": payload["best"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
