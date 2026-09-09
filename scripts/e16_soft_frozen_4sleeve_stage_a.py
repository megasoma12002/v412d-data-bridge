#!/usr/bin/env python3
"""Soft-Frozen 4-sleeve Stage A clip grid — RESEARCH ONLY.

Charter: research/ops/SOFT_FROZEN_4SLEEVE_CHARTER.md
Live Soft-Frozen SSOT untouched.
"""
from __future__ import annotations

import itertools
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e16_soft_frozen_base as soft
import e16_soft_frozen_4sleeve as sf4
import e50_early_stack_combined_nav as e50
from e16_private_fin_holdings_rescreen import build_extended_market, held_score, tip_gate
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, window_stats
from tw_share_lots import BOARD_LOT
from within_sleeve_alloc import FIN_EQUAL, FIN_PRE_EXDIV_KD, TEL_EQUAL, build_kd_season_tilt_scores, build_pre_exdiv_window_buy_ok

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/soft-frozen-4sleeve-20260909"
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

FINPUB_CLIPS = [(0.50, 0.85), (0.55, 0.90), (0.60, 0.90)]
FINPRIV_CLIPS = [(0.00, 0.20), (0.05, 0.25), (0.10, 0.30), (0.00, 0.30)]
PRIOR_PRIV = [0.15, 0.25]
PRIV_POLICIES = [FIN_EQUAL, FIN_PRE_EXDIV_KD]


def cand_id(pub_lo, pub_hi, priv_lo, priv_hi, prior_frac, priv_pol: str) -> str:
    tag = "EQ" if priv_pol == FIN_EQUAL else "KD"
    return (
        f"SF4_P{int(pub_lo*100)}-{int(pub_hi*100)}"
        f"_V{int(priv_lo*100)}-{int(priv_hi*100)}"
        f"_F{int(prior_frac*100)}_{tag}"
    )


def run_live_pub_kd(market, dividends):
    old_fin, old_all = list(e50.FIN), list(e50.ALL)
    e50.FIN = list(sf4.PUB_R1)
    e50.ALL = list(sf4.PUB_R1) + list(sf4.TEL) + ["0050"]
    try:
        _p, _s, target, regime = e50.e16_features(market)
        cal = pd.to_datetime(market["date"]).drop_duplicates().sort_values()
        fin_scores = build_kd_season_tilt_scores(
            market,
            dividends,
            sf4.PUB_R1,
            k_thresh=float(KD_OPT["k_thresh"]),
            season_start=KD_OPT["season_start"],
            season_end=KD_OPT["season_end"],
            pre_days=int(KD_OPT["pre_days"]),
            active_score=float(KD_OPT["active_score"]),
        )
        fin_buy_ok = build_pre_exdiv_window_buy_ok(
            cal, dividends, sf4.PUB_R1, pre_days=int(KD_OPT["pre_days"]), also_stock_ex=True
        )
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
            fin_name_scores=fin_scores,
            fin_buy_ok=fin_buy_ok,
        )
        assert meta.get("exact_t1_ok")
        win = {w: window_stats(nav, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
        return {"id": "LIVE_PUB_KD", "nav": nav, "windows": win, "n_fills": int(len(fills)), "meta": meta}
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
    fin_codes = list(sf4.PUB_R1) + list(sf4.PRIV_R3R4)
    e50.FIN = fin_codes
    e50.ALL = fin_codes + list(sf4.TEL) + ["0050"]
    try:
        _prices, _sleeve, target4, regime, _score = sf4.build_4sleeve_targets(
            market,
            fin_pub_lo=pub_lo,
            fin_pub_hi=pub_hi,
            fin_priv_lo=priv_lo,
            fin_priv_hi=priv_hi,
            prior_priv_frac=prior_frac,
        )
        cal = pd.to_datetime(market["date"]).drop_duplicates().sort_values()
        fin_scores = build_kd_season_tilt_scores(
            market,
            dividends,
            fin_codes,
            k_thresh=float(KD_OPT["k_thresh"]),
            season_start=KD_OPT["season_start"],
            season_end=KD_OPT["season_end"],
            pre_days=int(KD_OPT["pre_days"]),
            active_score=float(KD_OPT["active_score"]),
        )
        fin_buy_ok = build_pre_exdiv_window_buy_ok(
            cal, dividends, fin_codes, pre_days=int(KD_OPT["pre_days"]), also_stock_ex=True
        )
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
            fin_name_scores=fin_scores,
            fin_buy_ok=fin_buy_ok,
            fin_pub_codes=sf4.PUB_R1,
            fin_priv_codes=sf4.PRIV_R3R4,
            fin_pub_alloc=FIN_PRE_EXDIV_KD,
            fin_priv_alloc=priv_pol,
        )
        assert meta.get("exact_t1_ok"), book_id
        win = {w: window_stats(nav, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
        end_pos = meta.get("end_positions") or {}
        tip_pub = sum(1 for c in sf4.PUB_R1 if abs(float(end_pos.get(c, 0.0))) >= LOT - 1e-9)
        tip_priv = sum(1 for c in sf4.PRIV_R3R4 if abs(float(end_pos.get(c, 0.0))) >= LOT - 1e-9)
        mean_w = target4[["FinPub", "FinPriv", "Telecom", "0050"]].mean().to_dict()
        return {
            "id": book_id,
            "nav": nav,
            "windows": win,
            "n_fills": int(len(fills)),
            "tip_pub_names": int(tip_pub),
            "tip_priv_names": int(tip_priv),
            "mean_weights": {k: float(v) for k, v in mean_w.items()},
            "clips": {
                "fin_pub": [pub_lo, pub_hi],
                "fin_priv": [priv_lo, priv_hi],
                "prior_priv_frac": prior_frac,
                "priv_policy": priv_pol,
            },
        }
    finally:
        e50.FIN = old_fin
        e50.ALL = old_all


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.9]
    assert soft.FIN == sf4.PUB_R1

    print("building extended market ...", flush=True)
    market = build_extended_market()
    dividends = load_dividends()

    print("baseline LIVE_PUB_KD ...", flush=True)
    results = {"LIVE_PUB_KD": run_live_pub_kd(market, dividends)}

    # Sanity control: FinPriv [0,0]
    print("control SF4_CTRL_PUB_ONLY ...", flush=True)
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

    grid = []
    for (plo, phi), (vlo, vhi), frac, pol in itertools.product(
        FINPUB_CLIPS, FINPRIV_CLIPS, PRIOR_PRIV, PRIV_POLICIES
    ):
        if (phi - plo) < 0.10 - 1e-12:
            continue
        if (vhi - vlo) < 0.15 - 1e-12 and not (vlo == 0.0 and vhi == 0.0):
            continue
        if plo + vlo + soft.SOFT_FROZEN_TEL_LO + soft.SOFT_FROZEN_ETF_LO > 1.0 + 1e-12:
            continue
        grid.append((plo, phi, vlo, vhi, frac, pol))

    print(f"Stage A challengers: {len(grid)}", flush=True)
    for i, (plo, phi, vlo, vhi, frac, pol) in enumerate(grid, 1):
        bid = cand_id(plo, phi, vlo, vhi, frac, pol)
        print(f"  [{i}/{len(grid)}] {bid} ...", flush=True)
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

    base = results["LIVE_PUB_KD"]
    asof = pd.to_datetime(base["nav"]["date"]).max()
    ranked = []
    for bid, row in results.items():
        if bid == "LIVE_PUB_KD":
            continue
        held = held_score(base["windows"]["heldout_2019_plus"], row["windows"]["heldout_2019_plus"])
        tip = tip_gate(base["nav"], row["nav"], asof)
        tip_clean = tip["ytd"]["gate"] == "PASS" and tip["trailing_1y"]["gate"] == "PASS"
        sealed = held_score(base["windows"]["sealed_2023_plus"], row["windows"]["sealed_2023_plus"])
        ranked.append(
            {
                "id": bid,
                "heldout_score": held["score"],
                "mdd_improve_pp": held["mdd_improve_pp"],
                "cagr_giveback_pp": held["cagr_giveback_pp"],
                "tip_ytd": tip["ytd"]["gate"],
                "tip_1y": tip["trailing_1y"]["gate"],
                "tip_clean": tip_clean,
                "sealed_score_REPORT_ONLY": sealed["score"],
                "tip_pub_names": row.get("tip_pub_names"),
                "tip_priv_names": row.get("tip_priv_names"),
                "mean_weights": row.get("mean_weights"),
                "clips": row.get("clips"),
                "n_fills": row["n_fills"],
                "is_control": bid == "SF4_CTRL_PUB_ONLY",
                "coexist": bool(tip_clean and held["score"] > 0 and bid != "SF4_CTRL_PUB_ONLY"),
            }
        )
    ranked.sort(key=lambda r: r["heldout_score"], reverse=True)
    coexist = [r for r in ranked if r["coexist"]]
    if coexist:
        status = "STAGE_A_CANDIDATES"
    elif any(r["heldout_score"] > 0 and not r["is_control"] for r in ranked):
        status = "STAGE_A_SCORE_POSITIVE_TIP_DIRTY"
    else:
        status = "STOP_NO_POSITIVE_HELDOUT_VS_LIVE_PUB_KD"

    abs_rows = {}
    for bid, row in results.items():
        a = row["windows"]
        abs_rows[bid] = {
            "full_cagr": a["full"].get("cagr"),
            "full_mdd": a["full"].get("max_drawdown"),
            "heldout_cagr": a["heldout_2019_plus"].get("cagr"),
            "heldout_mdd": a["heldout_2019_plus"].get("max_drawdown"),
        }

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "SOFT_FROZEN_4SLEEVE_STAGE_A",
        "status": status,
        "charter": "research/ops/SOFT_FROZEN_4SLEEVE_CHARTER.md",
        "live_wire": False,
        "soft_frozen_live_ssot_unchanged": True,
        "baseline": "LIVE_PUB_KD",
        "capital": CAPITAL,
        "lot_size": LOT,
        "n_challengers": len(grid),
        "absolute": abs_rows,
        "ranked_vs_live_pub_kd": ranked,
        "coexist_ids": [r["id"] for r in coexist],
        "best_non_control": next((r["id"] for r in ranked if not r["is_control"]), None),
    }
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    RESEARCH.joinpath("SOFT_FROZEN_4SLEEVE_STAGE_A.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )
    RESEARCH.joinpath("SOFT_FROZEN_4SLEEVE_CHARTER.json").write_text(
        json.dumps(
            {
                "label": "SOFT_FROZEN_4SLEEVE_CHARTER",
                "status": "STAGE_A_" + ("CANDIDATES" if coexist else "STOP"),
                "date": "2026-09-09",
                "rescreen_status": status,
            },
            indent=2,
        )
        + "\n"
    )

    lines = [
        "# Soft-Frozen 4-sleeve Stage A",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Status: **{status}** · live Soft-Frozen SSOT **unchanged** · baseline **`LIVE_PUB_KD`**",
        f"Challengers: **{len(grid)}** · capital **{CAPITAL:,.0f}** · lot **{LOT}**",
        "",
        "## Top vs LIVE_PUB_KD (excl. control ranks still listed)",
        "",
        "| book | heldout score | MDD↑pp | CAGR gb | tip | tip公/民 | coexist |",
        "|---|---:|---:|---:|---|---|---|",
    ]
    for r in ranked[:15]:
        lines.append(
            f"| `{r['id']}` | {r['heldout_score']:.3f} | {r['mdd_improve_pp']:.3f} | "
            f"{r['cagr_giveback_pp']:.3f} | {r['tip_ytd']}/{r['tip_1y']} | "
            f"{r.get('tip_pub_names')}/{r.get('tip_priv_names')} | {r['coexist']} |"
        )
    lines += [
        "",
        f"- Coexist: `{payload['coexist_ids'] or 'none'}`",
        f"- Best non-control: `{payload['best_non_control']}`",
        "- Class D Soft-Frozen flip **not** authorized from this Stage alone.",
        "",
        f"Repro: `{OUT.relative_to(ROOT)}/`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "REPORT.md").write_text(md)
    RESEARCH.joinpath("SOFT_FROZEN_4SLEEVE_STAGE_A.md").write_text(md)
    print(json.dumps({"status": status, "coexist": payload["coexist_ids"], "top": ranked[:5]}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
