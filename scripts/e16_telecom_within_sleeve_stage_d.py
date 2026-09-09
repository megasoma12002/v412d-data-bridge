#!/usr/bin/env python3
"""Telecom within-sleeve Stage D — async per-name timing (FIN-parallel, RESEARCH ONLY).

Human: 「電信三檔也做跟金融股一樣拆開的研究」
- Soft-Frozen KEEP (live FINBAND SSOT)
- Live wire false
- Financial held at FIN_PRE_EXDIV_KD / KD_OPT (live) to isolate Telecom
- Capital 500M · lot 1000 · Exact T+1 · E22_v2s_tw
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e16_soft_frozen_base as soft
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, load_market, window_stats
from e50_early_stack_combined_nav import FIN, TEL, e16_features, simulate_core
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp
from tw_share_lots import BOARD_LOT
from within_sleeve_alloc import (
    FIN_PRE_EXDIV_KD,
    TEL_EQUAL,
    TEL_EXDIV_SKIP_BUY,
    TEL_MIX_EQUAL_RS_EXDIV,
    TEL_RS_SOFT_TILT,
    TEL_RS_SOFT_TILT_EXDIV,
    build_exdiv_buy_ok,
    build_kd_season_tilt_scores,
    build_name_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/telecom-within-sleeve-async-20260909"
RESEARCH = ROOT / "research/ops"

CAPITAL = 500_000_000.0
LOT = BOARD_LOT
TRAIL_ALERT_PP = 3.0
TRAIL_PAUSE_PP = 5.0
MIX_L75 = 0.75
KD_OPT = {
    "id": "KD_APR15_MAY15_Klt30_T15",
    "season_start": (4, 15),
    "season_end": (5, 15),
    "k_thresh": 30.0,
    "pre_days": 15,
    "active_score": 1.5,
}

STAGE_D = (
    TEL_EQUAL,
    TEL_RS_SOFT_TILT,
    TEL_EXDIV_SKIP_BUY,
    TEL_RS_SOFT_TILT_EXDIV,
    TEL_MIX_EQUAL_RS_EXDIV,
)
SCORE_POLICIES = {TEL_RS_SOFT_TILT, TEL_RS_SOFT_TILT_EXDIV, TEL_MIX_EQUAL_RS_EXDIV}
BUY_OK_POLICIES = {TEL_EXDIV_SKIP_BUY, TEL_RS_SOFT_TILT_EXDIV, TEL_MIX_EQUAL_RS_EXDIV}


def tip_gate(base_nav: pd.DataFrame, chal_nav: pd.DataFrame, asof: pd.Timestamp) -> dict:
    out = {}
    asof = pd.Timestamp(asof)
    b_dates = pd.to_datetime(base_nav["date"])
    c_dates = pd.to_datetime(chal_nav["date"])
    for wname, start in (
        ("ytd", pd.Timestamp(asof.year, 1, 1)),
        ("trailing_1y", asof - pd.Timedelta(days=365)),
    ):
        b = base_nav[(b_dates >= start) & (b_dates <= asof)].reset_index(drop=True)
        c = chal_nav[(c_dates >= start) & (c_dates <= asof)].reset_index(drop=True)
        if len(b) < 20 or len(c) < 20:
            out[wname] = {"giveback_pp": None, "gate": "INSUFFICIENT"}
            continue
        bn = b["nav"] / float(b["nav"].iloc[0])
        cn = c["nav"] / float(c["nav"].iloc[0])
        years = (len(b) - 1) / 252.0
        bc = float(bn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        cc = float(cn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        gb = None if bc is None or cc is None else (bc - cc) * 100
        gate = "PASS"
        if gb is not None and gb > TRAIL_PAUSE_PP:
            gate = "PAUSE_REVIEW"
        elif gb is not None and gb > TRAIL_ALERT_PP:
            gate = "ALERT"
        out[wname] = {
            "giveback_pp": None if gb is None else float(gb),
            "gate": gate,
            "rel_nav": float(cn.iloc[-1] / bn.iloc[-1]),
        }
    return out


def score_vs_base(base_stats: dict, chal_stats: dict) -> dict:
    mdd_pp = mdd_delta_pp(base_stats.get("max_drawdown"), chal_stats.get("max_drawdown"))
    cagr_pp = cagr_delta_pp(base_stats.get("cagr"), chal_stats.get("cagr"), missing_as_zero=True)
    giveback = abs(float(cagr_pp)) if cagr_pp is not None else 9.0
    return {
        "mdd_improve_pp": float(mdd_pp),
        "cagr_giveback_pp": float(cagr_pp) if cagr_pp is not None else None,
        "score": float(mdd_pp) - 0.5 * giveback,
    }


def tip_tel(nav: pd.DataFrame, meta: dict) -> dict:
    tip = nav.iloc[-1] if len(nav) else None
    end_pos = meta.get("end_positions") or {}
    tel_held = {c: float(end_pos.get(c, 0.0)) for c in TEL}
    names_with_lot = sum(1 for v in tel_held.values() if abs(v) >= LOT - 1e-9)
    return {
        "tip_date": None if tip is None else str(tip["date"]),
        "tip_nav": None if tip is None else float(tip["nav"]),
        "tip_cash_weight": None
        if tip is None or float(tip["nav"]) <= 0
        else float(tip["cash"]) / float(tip["nav"]),
        "tip_pre_telecom": None if tip is None else float(tip["pre_telecom"]),
        "tip_tel_positions": tel_held,
        "tip_tel_names_with_board_lot": int(names_with_lot),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "outputs").mkdir(exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.9]

    print("loading ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, _s, target, regime = e16_features(market)
    cal = pd.to_datetime(market["date"]).drop_duplicates().sort_values()
    # Live FIN KD_OPT panels (held fixed).
    fin_scores = build_kd_season_tilt_scores(
        market,
        dividends,
        FIN,
        k_thresh=float(KD_OPT["k_thresh"]),
        season_start=KD_OPT["season_start"],
        season_end=KD_OPT["season_end"],
        pre_days=int(KD_OPT["pre_days"]),
        active_score=float(KD_OPT["active_score"]),
    )
    fin_buy_ok = build_pre_exdiv_window_buy_ok(
        cal, dividends, FIN, pre_days=int(KD_OPT["pre_days"]), also_stock_ex=True
    )
    tel_scores = build_name_scores(market, TEL)
    tel_buy_ok = build_exdiv_buy_ok(cal.to_numpy(), dividends, TEL, also_stock_ex=True)
    skip_counts = (~tel_buy_ok).sum().to_dict()
    print(f"  TEL exdiv skip-buy day-counts: {skip_counts}", flush=True)

    navs = {}
    results = {}
    for i, policy in enumerate(STAGE_D, 1):
        print(f"  [{i}/{len(STAGE_D)}] {policy} ...", flush=True)
        nav, fills, meta = simulate_core(
            market,
            target,
            regime,
            dividends,
            apply_e22=True,
            apply_stock_div=True,
            capital=CAPITAL,
            lot_size=LOT,
            financial_alloc=FIN_PRE_EXDIV_KD,
            telecom_alloc=policy,
            fin_name_scores=fin_scores,
            fin_buy_ok=fin_buy_ok,
            tel_name_scores=tel_scores if policy in SCORE_POLICIES else None,
            tel_buy_ok=tel_buy_ok if policy in BUY_OK_POLICIES else None,
            tel_mix_lambda=MIX_L75 if policy == TEL_MIX_EQUAL_RS_EXDIV else None,
        )
        assert meta.get("exact_t1_ok"), policy
        win = {w: window_stats(nav, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
        navs[policy] = nav
        results[policy] = {
            "id": policy,
            "n_fills": int(len(fills)),
            "windows": win,
            "tip": tip_tel(nav, meta),
        }

    base = results[TEL_EQUAL]
    asof = pd.to_datetime(navs[TEL_EQUAL]["date"]).max()
    ranked = []
    for policy, row in results.items():
        if policy == TEL_EQUAL:
            continue
        held = score_vs_base(base["windows"]["heldout_2019_plus"], row["windows"]["heldout_2019_plus"])
        tip = tip_gate(navs[TEL_EQUAL], navs[policy], asof)
        row["scores"] = {
            "heldout_2019_plus": held,
            "sealed_2023_plus_REPORT_ONLY": score_vs_base(
                base["windows"]["sealed_2023_plus"], row["windows"]["sealed_2023_plus"]
            ),
        }
        row["tip_gates"] = tip
        row["tip_clean"] = tip["ytd"]["gate"] == "PASS" and tip["trailing_1y"]["gate"] == "PASS"
        ranked.append(row)

    ranked.sort(key=lambda r: r["scores"]["heldout_2019_plus"]["score"], reverse=True)
    best = ranked[0]["scores"]["heldout_2019_plus"]["score"] if ranked else None
    tip_clean_pos = [r for r in ranked if r["tip_clean"] and r["scores"]["heldout_2019_plus"]["score"] > 0]
    if tip_clean_pos:
        status = "STAGE_D_CANDIDATES_LOCKED"
    elif best is not None and best > 0:
        status = "STAGE_D_SCORE_POSITIVE_TIP_DIRTY"
    else:
        status = "STOP_NO_POSITIVE_HELDOUT_SCORE"

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "TELECOM_WITHIN_SLEEVE_ASYNC_STAGE_D",
        "status": status,
        "charter": "research/ops/TELECOM_WITHIN_SLEEVE_ASYNC_CHARTER.md",
        "live_wire": False,
        "soft_frozen_clip": list(soft.SOFT_FROZEN_FIN_CLIP),
        "financial_held_at": "FIN_PRE_EXDIV_KD / KD_OPT",
        "capital": CAPITAL,
        "lot_size": LOT,
        "mix_lambda": MIX_L75,
        "exdiv_skip_buy_day_counts": {str(k): int(v) for k, v in skip_counts.items()},
        "base_id": TEL_EQUAL,
        "ranked": [
            {
                "id": r["id"],
                "heldout_score": r["scores"]["heldout_2019_plus"]["score"],
                "mdd_improve_pp": r["scores"]["heldout_2019_plus"]["mdd_improve_pp"],
                "cagr_giveback_pp": r["scores"]["heldout_2019_plus"]["cagr_giveback_pp"],
                "tip_clean": r["tip_clean"],
                "tip_ytd": r["tip_gates"]["ytd"]["gate"],
                "tip_1y": r["tip_gates"]["trailing_1y"]["gate"],
                "tip_tel_names": r["tip"]["tip_tel_names_with_board_lot"],
                "tip_positions": r["tip"]["tip_tel_positions"],
            }
            for r in ranked
        ],
        "tip_clean_positive": [r["id"] for r in tip_clean_pos],
    }
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    RESEARCH.joinpath("TELECOM_WITHIN_SLEEVE_ASYNC_STAGE_D.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    lines = [
        "# Telecom Within-Sleeve Async — Stage D (FIN-parallel)",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Human: **電信三檔也做跟金融股一樣拆開的研究**",
        f"Status: **{status}** · Soft-Frozen **{soft.SOFT_FROZEN_FIN_CLIP}** · FIN=`KD_OPT` · live wire **false**",
        f"Capital **{CAPITAL:,.0f}** · lot **{LOT}** · BASE=`TEL_EQUAL`",
        "",
        f"Ex-div skip-buy day counts: `{skip_counts}`",
        "",
        "## vs TEL_EQUAL (held-out)",
        "",
        "| id | heldout score | MDD↑pp | CAGR gb | YTD | 1y | tip_clean | tip #TEL |",
        "|---|---:|---:|---:|---|---|---|---:|",
    ]
    for r in ranked:
        h = r["scores"]["heldout_2019_plus"]
        tip = r["tip_gates"]
        lines.append(
            f"| `{r['id']}` | {h['score']:.3f} | {h['mdd_improve_pp']:.3f} | {h['cagr_giveback_pp']:.3f} | "
            f"{tip['ytd']['gate']} | {tip['trailing_1y']['gate']} | {r['tip_clean']} | "
            f"{r['tip']['tip_tel_names_with_board_lot']} |"
        )
    lines += [
        "",
        "## Reading",
        "",
        f"- Tip-clean + held-out>0: `{payload['tip_clean_positive'] or 'none'}`",
        "- Prior pack Stage C (`TEL_DIVERSIFY_PACK`) remains separate evidence @ 500M.",
        "- No live Telecom cutover from this screen.",
        "",
        f"Repro: `{OUT.relative_to(ROOT)}/`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "STAGE_D.md").write_text(md)
    RESEARCH.joinpath("TELECOM_WITHIN_SLEEVE_ASYNC_STAGE_D.md").write_text(md)
    print(json.dumps({"status": status, "ranked": payload["ranked"]}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
