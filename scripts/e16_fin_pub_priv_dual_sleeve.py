#!/usr/bin/env python3
"""金融公 / 金融民 dual-sleeve Stage A — RESEARCH ONLY.

Soft-Frozen sleeve weights unchanged (Financial / Telecom / 0050 from FINBAND).
Financial *dollars* split: pub_share → 公股 R1, (1−pub_share) → 民營 R3R4.
Router features still Soft-Frozen 公股-only (soft.FIN).

Contrast vs PRIVATE_FIN_HOLDINGS Stage A (replace Financial names entirely).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
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
OUT = ROOT / "repro/fin-pub-priv-dual-sleeve-20260909"
RESEARCH = ROOT / "research/ops"

CAPITAL = 500_000_000.0
LOT = BOARD_LOT

KD_OPT = {
    "id": "KD_APR15_MAY15_Klt30_T15",
    "season_start": (4, 15),
    "season_end": (5, 15),
    "k_thresh": 30.0,
    "pre_days": 15,
    "active_score": 1.5,
}

# pub_share grid: 1.0 = live-equivalent control under dual machinery
PUB_SHARES = [1.0, 0.85, 0.75, 0.60, 0.50]
PRIV_POLICIES = [FIN_EQUAL, FIN_PRE_EXDIV_KD]


def run_book(
    market,
    dividends,
    target,
    regime,
    *,
    book_id: str,
    pub_share: float,
    priv_policy: str,
):
    fin_codes = list(PUB_R1) + list(PRIV_R3R4)
    old_fin, old_all = list(e50.FIN), list(e50.ALL)
    e50.FIN = fin_codes
    e50.ALL = fin_codes + TEL + ["0050"]
    try:
        cal = pd.to_datetime(market["date"]).drop_duplicates().sort_values()
        need_kd = True  # 公股 always KD_OPT; scores shared when 民 also KD
        fin_scores = None
        fin_buy_ok = None
        if need_kd:
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

        if abs(pub_share - 1.0) < 1e-12 and priv_policy == FIN_EQUAL:
            # Exact live path control: PUB only + KD (no dual machinery)
            e50.FIN = list(PUB_R1)
            e50.ALL = list(PUB_R1) + TEL + ["0050"]
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
        else:
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
                fin_name_scores=fin_scores,
                fin_buy_ok=fin_buy_ok,
                fin_mix_lambda=float(pub_share),
                fin_dual_pub_codes=PUB_R1,
                fin_dual_priv_codes=PRIV_R3R4,
                fin_dual_pub_policy=FIN_PRE_EXDIV_KD,
                fin_dual_priv_policy=priv_policy,
            )
        assert meta.get("exact_t1_ok"), book_id
        win = {w: window_stats(nav, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
        end_pos = meta.get("end_positions") or {}
        tip_pub = sum(1 for c in PUB_R1 if abs(float(end_pos.get(c, 0.0))) >= LOT - 1e-9)
        tip_priv = sum(1 for c in PRIV_R3R4 if abs(float(end_pos.get(c, 0.0))) >= LOT - 1e-9)
        return {
            "id": book_id,
            "pub_share": float(pub_share),
            "priv_policy": priv_policy,
            "n_fills": int(len(fills)),
            "windows": win,
            "nav": nav,
            "tip_pub_names": int(tip_pub),
            "tip_priv_names": int(tip_priv),
        }
    finally:
        e50.FIN = old_fin
        e50.ALL = old_all


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "outputs").mkdir(exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.9]
    assert soft.FIN == PUB_R1

    print("building extended market ...", flush=True)
    market = build_extended_market()
    dividends = load_dividends()
    print("Soft-Frozen targets (公股 features) ...", flush=True)
    _p, _s, target, regime = e50.e16_features(market)

    books_spec = []
    # Baseline live intent
    books_spec.append(("LIVE_PUB_KD", 1.0, FIN_EQUAL))  # special-cased to pure PUB KD
    for share in PUB_SHARES:
        if abs(share - 1.0) < 1e-12:
            continue  # covered by LIVE_PUB_KD
        for priv_pol in PRIV_POLICIES:
            tag = "EQ" if priv_pol == FIN_EQUAL else "KD"
            books_spec.append((f"DUAL_P{int(round(share*100))}_{tag}", share, priv_pol))

    results = {}
    for i, (bid, share, priv_pol) in enumerate(books_spec, 1):
        print(f"  [{i}/{len(books_spec)}] {bid} pub_share={share} priv={priv_pol} ...", flush=True)
        results[bid] = run_book(
            market, dividends, target, regime, book_id=bid, pub_share=share, priv_policy=priv_pol
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
                "pub_share": row["pub_share"],
                "priv_policy": row["priv_policy"],
                "heldout_score": held["score"],
                "mdd_improve_pp": held["mdd_improve_pp"],
                "cagr_giveback_pp": held["cagr_giveback_pp"],
                "tip_ytd": tip["ytd"]["gate"],
                "tip_1y": tip["trailing_1y"]["gate"],
                "tip_clean": tip_clean,
                "sealed_score_REPORT_ONLY": sealed["score"],
                "tip_pub_names": row["tip_pub_names"],
                "tip_priv_names": row["tip_priv_names"],
                "n_fills": row["n_fills"],
                "coexist": bool(tip_clean and held["score"] > 0),
            }
        )
    ranked.sort(key=lambda r: r["heldout_score"], reverse=True)
    coexist = [r for r in ranked if r["coexist"]]
    if coexist:
        status = "STAGE_A_CANDIDATES"
    elif any(r["heldout_score"] > 0 for r in ranked):
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
            "pub_share": row["pub_share"],
            "priv_policy": row["priv_policy"],
        }

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "FIN_PUB_PRIV_DUAL_SLEEVE_RESCREEN",
        "status": status,
        "charter": "research/ops/FIN_PUB_PRIV_DUAL_SLEEVE_CHARTER.md",
        "live_wire": False,
        "soft_frozen_clip": list(soft.SOFT_FROZEN_FIN_CLIP),
        "router_features": "Soft-Frozen 公股 R1 only",
        "mechanism": "Split Soft-Frozen Financial dollars into 金融公+金融民 (coexist)",
        "baseline": "LIVE_PUB_KD",
        "capital": CAPITAL,
        "lot_size": LOT,
        "pub_r1": PUB_R1,
        "priv_r3r4": PRIV_R3R4,
        "kd_probe": KD_OPT,
        "absolute": abs_rows,
        "ranked_vs_live_pub_kd": ranked,
        "coexist_ids": [r["id"] for r in coexist],
    }
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    RESEARCH.joinpath("FIN_PUB_PRIV_DUAL_SLEEVE_RESCREEN.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    lines = [
        "# 金融公 / 金融民 dual-sleeve — Stage A re-screen",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Status: **{status}** · Soft-Frozen **{soft.SOFT_FROZEN_FIN_CLIP}** · baseline **`LIVE_PUB_KD`** · live wire **false**",
        "Mechanism: Soft-Frozen Financial weight kept; dollars split 公股/民營 coexist.",
        f"Capital **{CAPITAL:,.0f}** · lot **{LOT}** · Telecom=`TEL_EQUAL` · 公 within=`KD_OPT`",
        "",
        "## Absolute",
        "",
        "| book | pub_share | priv | full CAGR | full MDD | heldout CAGR | heldout MDD |",
        "|---|---:|---|---:|---:|---:|---:|",
    ]
    for bid in ["LIVE_PUB_KD"] + [r["id"] for r in ranked]:
        a = abs_rows[bid]
        lines.append(
            f"| `{bid}` | {a['pub_share']:.2f} | `{a['priv_policy']}` | "
            f"{a['full_cagr']*100:.2f}% | {a['full_mdd']*100:.2f}% | "
            f"{a['heldout_cagr']*100:.2f}% | {a['heldout_mdd']*100:.2f}% |"
        )
    lines += [
        "",
        "## vs LIVE_PUB_KD",
        "",
        "| book | heldout score | MDD↑pp | CAGR gb | YTD | 1y | tip_clean | tip公/民 | coexist |",
        "|---|---:|---:|---:|---|---|---|---|---|",
    ]
    for r in ranked:
        lines.append(
            f"| `{r['id']}` | {r['heldout_score']:.3f} | {r['mdd_improve_pp']:.3f} | "
            f"{r['cagr_giveback_pp']:.3f} | {r['tip_ytd']} | {r['tip_1y']} | {r['tip_clean']} | "
            f"{r['tip_pub_names']}/{r['tip_priv_names']} | {r['coexist']} |"
        )
    lines += [
        "",
        "## Reading",
        "",
        f"- Coexist (tip-clean + held-out>0): `{payload['coexist_ids'] or 'none'}`",
        "- Not the same as PRIV-replace Stage A — here 公股 stays in book.",
        "- Soft-Frozen router features remain 公股; no live 4-sleeve Soft-Frozen rewrite this Stage.",
        "- No live wire from this screen.",
        "",
        f"Repro: `{OUT.relative_to(ROOT)}/`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "REPORT.md").write_text(md)
    RESEARCH.joinpath("FIN_PUB_PRIV_DUAL_SLEEVE_RESCREEN.md").write_text(md)
    print(json.dumps({"status": status, "ranked": ranked, "coexist": payload["coexist_ids"]}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
