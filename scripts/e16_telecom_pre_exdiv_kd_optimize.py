#!/usr/bin/env python3
"""Optimize TEL_PRE_EXDIV_KD sleeve params (FIN-parallel, RESEARCH ONLY).

Telecom cash-ex concentrated Jun–Aug → summer season grid.
Hold Financial at live KD_OPT. Soft-Frozen KEEP. Live wire false.
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
    TEL_PRE_EXDIV_KD,
    build_kd_season_tilt_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/telecom-pre-exdiv-kd-optimize-20260909"
RESEARCH = ROOT / "research/ops"

CAPITAL = 500_000_000.0
LOT = BOARD_LOT
TRAIL_ALERT_PP = 3.0
TRAIL_PAUSE_PP = 5.0
ACTIVE_SCORE = 1.5

# Live FIN KD_OPT (held fixed)
FIN_KD = {
    "season_start": (4, 15),
    "season_end": (5, 15),
    "k_thresh": 30.0,
    "pre_days": 15,
    "active_score": 1.5,
}

# Telecom ex-div ~ Jun–Aug
SEASONS = [
    ("JUN", (6, 1), (6, 30)),
    ("JUN15_JUL31", (6, 15), (7, 31)),
    ("JUL", (7, 1), (7, 31)),
    ("JUL15_AUG15", (7, 15), (8, 15)),
    ("JUN_AUG", (6, 1), (8, 31)),
    ("MAY15_AUG15", (5, 15), (8, 15)),
]
K_THRESH = (20.0, 25.0, 30.0)
PRE_DAYS = (5, 10, 15)


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
        out[wname] = {
            "giveback_pp": None if gb is None else float(gb),
            "gate": gate,
        }
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
    (OUT / "outputs").mkdir(exist_ok=True)
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
        k_thresh=float(FIN_KD["k_thresh"]),
        season_start=FIN_KD["season_start"],
        season_end=FIN_KD["season_end"],
        pre_days=int(FIN_KD["pre_days"]),
        active_score=float(FIN_KD["active_score"]),
    )
    fin_buy_ok = build_pre_exdiv_window_buy_ok(
        cal, dividends, FIN, pre_days=int(FIN_KD["pre_days"]), also_stock_ex=True
    )

    print("  BASE TEL_EQUAL ...", flush=True)
    base_nav, base_fills, base_meta = simulate_core(
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
    assert base_meta.get("exact_t1_ok")
    base_win = {w: window_stats(base_nav, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
    asof = pd.to_datetime(base_nav["date"]).max()

    rows = []
    total = len(SEASONS) * len(K_THRESH) * len(PRE_DAYS)
    n = 0
    for sid, s0, s1 in SEASONS:
        for kth in K_THRESH:
            for pred in PRE_DAYS:
                n += 1
                cid = f"TEL_KD_{sid}_Klt{int(kth)}_T{pred}"
                print(f"  [{n}/{total}] {cid} ...", flush=True)
                tel_scores = build_kd_season_tilt_scores(
                    market,
                    dividends,
                    TEL,
                    k_thresh=float(kth),
                    season_start=s0,
                    season_end=s1,
                    pre_days=int(pred),
                    active_score=ACTIVE_SCORE,
                )
                tel_buy_ok = build_pre_exdiv_window_buy_ok(
                    cal, dividends, TEL, pre_days=int(pred), also_stock_ex=True
                )
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
                    telecom_alloc=TEL_PRE_EXDIV_KD,
                    fin_name_scores=fin_scores,
                    fin_buy_ok=fin_buy_ok,
                    tel_name_scores=tel_scores,
                    tel_buy_ok=tel_buy_ok,
                )
                assert meta.get("exact_t1_ok"), cid
                win = {w: window_stats(nav, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
                held = held_score(base_win["heldout_2019_plus"], win["heldout_2019_plus"])
                tip = tip_gate(base_nav, nav, asof)
                tip_clean = tip["ytd"]["gate"] == "PASS" and tip["trailing_1y"]["gate"] == "PASS"
                no_pause = tip["ytd"]["gate"] != "PAUSE_REVIEW" and tip["trailing_1y"]["gate"] != "PAUSE_REVIEW"
                rows.append(
                    {
                        "id": cid,
                        "season": sid,
                        "season_start": list(s0),
                        "season_end": list(s1),
                        "k_thresh": float(kth),
                        "pre_days": int(pred),
                        "heldout_score": held["score"],
                        "mdd_improve_pp": held["mdd_improve_pp"],
                        "cagr_giveback_pp": held["cagr_giveback_pp"],
                        "tip_ytd": tip["ytd"]["gate"],
                        "tip_1y": tip["trailing_1y"]["gate"],
                        "tip_clean": tip_clean,
                        "no_pause": no_pause,
                        "n_fills": int(len(fills)),
                        "coexist": bool(tip_clean and held["score"] > 0),
                    }
                )

    coexist = [r for r in rows if r["coexist"]]
    no_pause_pos = [r for r in rows if r["no_pause"] and r["heldout_score"] > 0]
    if coexist:
        pick_pool = coexist
        pick_rule = "tip_clean_and_heldout_gt0"
    elif no_pause_pos:
        pick_pool = no_pause_pos
        pick_rule = "no_pause_max_heldout"
    else:
        pick_pool = rows
        pick_rule = "max_heldout_only"
    best = sorted(pick_pool, key=lambda r: r["heldout_score"], reverse=True)[0]
    top5 = sorted(rows, key=lambda r: r["heldout_score"], reverse=True)[:5]

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "TELECOM_PRE_EXDIV_KD_OPTIMIZE",
        "live_wire": False,
        "soft_frozen_clip": list(soft.SOFT_FROZEN_FIN_CLIP),
        "financial_held_at": "FIN_PRE_EXDIV_KD / KD_OPT",
        "capital": CAPITAL,
        "lot_size": LOT,
        "grid": {
            "seasons": [s[0] for s in SEASONS],
            "k_thresh": list(K_THRESH),
            "pre_days": list(PRE_DAYS),
            "n": total,
        },
        "selection_rule": pick_rule,
        "best": best,
        "n_coexist": len(coexist),
        "n_no_pause_pos": len(no_pause_pos),
        "top5_heldout": top5,
        "all_rows": rows,
    }
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    RESEARCH.joinpath("TELECOM_PRE_EXDIV_KD_OPTIMIZE.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )
    pd.DataFrame(rows).to_csv(OUT / "outputs" / "grid.csv", index=False)

    lines = [
        "# Telecom PRE_EXDIV_KD optimize (FIN-parallel)",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Soft-Frozen **{soft.SOFT_FROZEN_FIN_CLIP}** · FIN=`KD_OPT` · live wire **false** · capital **{CAPITAL:,.0f}**",
        f"Grid: seasons={ [s[0] for s in SEASONS] } · K={list(K_THRESH)} · T={list(PRE_DAYS)} · n={total}",
        "",
        f"## Best (`{pick_rule}`)",
        "",
        f"- **`{best['id']}`** held-out **{best['heldout_score']:+.3f}** · tip {best['tip_ytd']}/{best['tip_1y']} · "
        f"coexist={best['coexist']}",
        f"- season {best['season']} · K&lt;{best['k_thresh']} · T−{best['pre_days']}",
        "",
        f"Coexist count: **{len(coexist)}** · no-PAUSE & score>0: **{len(no_pause_pos)}**",
        "",
        "## Top5 by held-out",
        "",
        "| id | score | MDD↑ | CAGR gb | YTD | 1y | coexist |",
        "|---|---:|---:|---:|---|---|---|",
    ]
    for r in top5:
        lines.append(
            f"| `{r['id']}` | {r['heldout_score']:.3f} | {r['mdd_improve_pp']:.3f} | "
            f"{r['cagr_giveback_pp']:.3f} | {r['tip_ytd']} | {r['tip_1y']} | {r['coexist']} |"
        )
    lines += [
        "",
        "## Hard rules",
        "",
        "- Soft-Frozen / live e21 Telecom EQUAL untouched",
        "- No live cutover from this grid",
        "",
        f"Repro: `{OUT.relative_to(ROOT)}/`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "REPORT.md").write_text(md)
    RESEARCH.joinpath("TELECOM_PRE_EXDIV_KD_OPTIMIZE.md").write_text(md)
    print(json.dumps({"best": best, "n_coexist": len(coexist), "top5": top5}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
