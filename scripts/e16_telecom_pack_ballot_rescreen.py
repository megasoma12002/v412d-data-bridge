#!/usr/bin/env python3
"""Re-screen Telecom pack policies under live FIN KD_OPT @ 500M (ballot evidence).

Paper only. Soft-Frozen KEEP. Compares TEL_EQUAL vs pack challengers with
Financial held at FIN_PRE_EXDIV_KD (live).
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
    TEL_DIVERSIFY_PACK,
    TEL_EQUAL,
    TEL_MIN_LOT_PACK,
    TEL_SCORE_LOT_PACK,
    TEL_TOP1,
    TEL_TOP2_EQUAL,
    build_kd_season_tilt_scores,
    build_name_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/telecom-pack-ballot-rescreen-20260909"
RESEARCH = ROOT / "research/ops"
CAPITAL = 500_000_000.0
LOT = BOARD_LOT
TRAIL_ALERT_PP = 3.0
TRAIL_PAUSE_PP = 5.0
KD_OPT = {
    "season_start": (4, 15),
    "season_end": (5, 15),
    "k_thresh": 30.0,
    "pre_days": 15,
    "active_score": 1.5,
}
POLICIES = [
    TEL_EQUAL,
    TEL_DIVERSIFY_PACK,
    TEL_SCORE_LOT_PACK,
    TEL_MIN_LOT_PACK,
    TEL_TOP2_EQUAL,
    TEL_TOP1,
]


def tip_gate(base_nav, chal_nav, asof):
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
        out[wname] = {"giveback_pp": None if gb is None else float(gb), "gate": gate}
    return out


def held_score(base_s, chal_s):
    mdd = mdd_delta_pp(base_s.get("max_drawdown"), chal_s.get("max_drawdown"))
    cagr = cagr_delta_pp(base_s.get("cagr"), chal_s.get("cagr"), missing_as_zero=True)
    gb = abs(float(cagr)) if cagr is not None else 9.0
    return {
        "mdd_improve_pp": float(mdd),
        "cagr_giveback_pp": float(cagr) if cagr is not None else None,
        "score": float(mdd) - 0.5 * gb,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.9]
    print("loading ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, _s, target, regime = e16_features(market)
    cal = pd.to_datetime(market["date"]).drop_duplicates().sort_values()
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

    navs = {}
    wins = {}
    tips = {}
    for i, pol in enumerate(POLICIES, 1):
        print(f"  [{i}/{len(POLICIES)}] {pol} ...", flush=True)
        need_scores = pol in (TEL_TOP1, TEL_TOP2_EQUAL, TEL_SCORE_LOT_PACK)
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
            telecom_alloc=pol,
            fin_name_scores=fin_scores,
            fin_buy_ok=fin_buy_ok,
            tel_name_scores=tel_scores if need_scores else None,
        )
        assert meta.get("exact_t1_ok"), pol
        navs[pol] = nav
        wins[pol] = {w: window_stats(nav, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
        end_pos = meta.get("end_positions") or {}
        tips[pol] = {
            "positions": {c: float(end_pos.get(c, 0.0)) for c in TEL},
            "n_names": sum(1 for c in TEL if abs(float(end_pos.get(c, 0.0))) >= LOT - 1e-9),
            "n_fills": int(len(fills)),
        }

    asof = pd.to_datetime(navs[TEL_EQUAL]["date"]).max()
    ranked = []
    for pol in POLICIES:
        if pol == TEL_EQUAL:
            continue
        held = held_score(wins[TEL_EQUAL]["heldout_2019_plus"], wins[pol]["heldout_2019_plus"])
        tip = tip_gate(navs[TEL_EQUAL], navs[pol], asof)
        ranked.append(
            {
                "id": pol,
                "heldout_score": held["score"],
                "mdd_improve_pp": held["mdd_improve_pp"],
                "cagr_giveback_pp": held["cagr_giveback_pp"],
                "tip_ytd": tip["ytd"]["gate"],
                "tip_1y": tip["trailing_1y"]["gate"],
                "tip_clean": tip["ytd"]["gate"] == "PASS" and tip["trailing_1y"]["gate"] == "PASS",
                "tip_tel_names": tips[pol]["n_names"],
                "tip_positions": tips[pol]["positions"],
                "n_fills": tips[pol]["n_fills"],
            }
        )
    ranked.sort(key=lambda r: r["heldout_score"], reverse=True)
    best = ranked[0]
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "TELECOM_PACK_BALLOT_RESCREEN",
        "live_wire": False,
        "soft_frozen_clip": list(soft.SOFT_FROZEN_FIN_CLIP),
        "financial_held_at": "FIN_PRE_EXDIV_KD / KD_OPT",
        "capital": CAPITAL,
        "lot_size": LOT,
        "base_id": TEL_EQUAL,
        "ranked": ranked,
        "recommended": best["id"] if best["tip_clean"] and best["heldout_score"] > 0 else None,
        "prior_stage_c_best": "TEL_DIVERSIFY_PACK",
        "note": "Rescreen under live FIN KD_OPT for pack cutover ballot honesty",
    }
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    RESEARCH.joinpath("TELECOM_PACK_BALLOT_RESCREEN.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )
    lines = [
        "# Telecom pack ballot re-screen (under live FIN KD_OPT)",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Capital **{CAPITAL:,.0f}** · Soft-Frozen **{soft.SOFT_FROZEN_FIN_CLIP}** · FIN=`KD_OPT` · live wire **false**",
        "",
        "## vs TEL_EQUAL",
        "",
        "| id | heldout score | MDD↑pp | CAGR gb | YTD | 1y | tip_clean | tip #TEL |",
        "|---|---:|---:|---:|---|---|---|---:|",
    ]
    for r in ranked:
        lines.append(
            f"| `{r['id']}` | {r['heldout_score']:.3f} | {r['mdd_improve_pp']:.3f} | "
            f"{r['cagr_giveback_pp']:.3f} | {r['tip_ytd']} | {r['tip_1y']} | {r['tip_clean']} | "
            f"{r['tip_tel_names']} |"
        )
    lines += [
        "",
        f"Recommended for ballot: **`{payload['recommended']}`**"
        if payload["recommended"]
        else "",
        "",
        f"Repro: `{OUT.relative_to(ROOT)}/`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "REPORT.md").write_text(md)
    RESEARCH.joinpath("TELECOM_PACK_BALLOT_RESCREEN.md").write_text(md)
    print(json.dumps({"recommended": payload["recommended"], "ranked": ranked}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
