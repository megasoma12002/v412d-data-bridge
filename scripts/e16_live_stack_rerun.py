#!/usr/bin/env python3
"""Re-screen current live stack vs pre-big-win Soft-Frozen+KD_OPT (paper).

Books @ 500M · lot 1000 · Exact T+1 · E22_v2s_tw · FIN KD_OPT:
  OLD_SF_KD      Soft-Frozen FIN [0.50, 0.95] · no E45
  FINBAND_KD     Soft-Frozen FIN [0.60, 0.90] · no E45
  OLD_SF_KD_A05  Soft-Frozen FIN [0.50, 0.95] · BLEND_E45_A05
  NEW_LIVE       Soft-Frozen FIN [0.60, 0.90] · BLEND_E45_A05  ← current live

Writes research/ops/LIVE_STACK_RERUN_*.{md,json} + repro/.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e16_clip_search_challenger as clip
import e16_soft_frozen_base as soft
import e45_crisis_core as e45
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, load_market, window_stats
from e50_early_stack_combined_nav import FIN, TEL, simulate_core
from portfolio_capital import DEFAULT_CAPITAL
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp
from tw_share_lots import BOARD_LOT
from within_sleeve_alloc import (
    FIN_PRE_EXDIV_KD,
    TEL_EQUAL,
    build_kd_season_tilt_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/live-stack-rerun-20260909"
RESEARCH = ROOT / "research/ops"
ALL = FIN + TEL + ["0050"]
ALPHA = 0.05
TRAIL_ALERT_PP = 3.0
TRAIL_PAUSE_PP = 5.0
KD_OPT = {
    "id": "KD_APR15_MAY15_Klt30_T15",
    "season_start": (4, 15),
    "season_end": (5, 15),
    "k_thresh": 30.0,
    "pre_days": 15,
    "active_score": 1.5,
}


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
            "rel_nav": float(cn.iloc[-1] / bn.iloc[-1]),
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
    _p, _s, _t, regime, score_df = soft.build_soft_frozen_targets(market)
    cal = pd.to_datetime(market["date"]).drop_duplicates().sort_values()
    kd_scores = build_kd_season_tilt_scores(
        market,
        dividends,
        FIN,
        k_thresh=float(KD_OPT["k_thresh"]),
        season_start=KD_OPT["season_start"],
        season_end=KD_OPT["season_end"],
        pre_days=int(KD_OPT["pre_days"]),
        active_score=float(KD_OPT["active_score"]),
    )
    kd_ok = build_pre_exdiv_window_buy_ok(
        cal, dividends, FIN, pre_days=int(KD_OPT["pre_days"]), also_stock_ex=True
    )
    close_eq = (
        market[market["code"].isin(ALL)]
        .pivot(index="date", columns="code", values="close")
        .sort_index()
        .ffill()
    )
    e45_full = e45.compute_exposure(close_eq, "E3_VOLTARGET_WINNER")["exposure"]
    e45_blend = ((1.0 - ALPHA) * 1.0 + ALPHA * e45_full.astype(float)).clip(0.0, 1.0)

    def make_targets(flo, fhi):
        return clip.build_targets_with_clips(
            regime=regime,
            score=score_df,
            fin_lo=flo,
            fin_hi=fhi,
            tel_lo=0.03,
            tel_hi=0.35,
            etf_lo=0.0,
            etf_hi=0.35,
        )

    def run(label, tgt, e45_exp=None):
        print(f"  sim {label} ...", flush=True)
        nav, fills, meta = simulate_core(
            market,
            tgt,
            regime,
            dividends,
            apply_e22=True,
            apply_stock_div=True,
            capital=float(DEFAULT_CAPITAL),
            lot_size=BOARD_LOT,
            financial_alloc=FIN_PRE_EXDIV_KD,
            telecom_alloc=TEL_EQUAL,
            fin_name_scores=kd_scores,
            fin_buy_ok=kd_ok,
            e45_exposure=e45_exp,
        )
        assert meta.get("exact_t1_ok"), label
        win = {w: window_stats(nav, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
        slug = label.lower()
        nav.to_csv(OUT / "outputs" / f"{slug}_daily_nav.csv", index=False)
        fills.to_csv(OUT / "outputs" / f"{slug}_fills.csv", index=False)
        return {"nav": nav, "windows": win, "n_fills": int(len(fills))}

    books = {
        "OLD_SF_KD": run("OLD_SF_KD", make_targets(0.50, 0.95), None),
        "FINBAND_KD": run("FINBAND_KD", make_targets(0.60, 0.90), None),
        "OLD_SF_KD_A05": run("OLD_SF_KD_A05", make_targets(0.50, 0.95), e45_blend),
        "NEW_LIVE": run("NEW_LIVE", make_targets(0.60, 0.90), e45_blend),
    }
    base = books["OLD_SF_KD"]
    asof = pd.to_datetime(base["nav"]["date"]).max()

    abs_rows = {}
    for label, book in books.items():
        abs_rows[label] = {
            w: {
                "cagr": book["windows"][w].get("cagr"),
                "max_drawdown": book["windows"][w].get("max_drawdown"),
            }
            for w in ("full", "heldout_2019_plus", "sealed_2023_plus")
        }

    vs = {}
    for label in ("FINBAND_KD", "OLD_SF_KD_A05", "NEW_LIVE"):
        book = books[label]
        held = held_score(base["windows"]["heldout_2019_plus"], book["windows"]["heldout_2019_plus"])
        sealed = held_score(base["windows"]["sealed_2023_plus"], book["windows"]["sealed_2023_plus"])
        tip = tip_gate(base["nav"], book["nav"], asof)
        vs[label] = {
            "heldout_2019_plus": held,
            "sealed_2023_plus_REPORT_ONLY": sealed,
            "tip_gates": tip,
            "tip_clean": tip["ytd"]["gate"] == "PASS" and tip["trailing_1y"]["gate"] == "PASS",
            "n_fills": book["n_fills"],
        }

    jb = base["nav"][["date", "nav"]].rename(columns={"nav": "nav_old_sf_kd"})
    for label in ("FINBAND_KD", "OLD_SF_KD_A05", "NEW_LIVE"):
        jc = books[label]["nav"][["date", "nav"]].rename(columns={"nav": f"nav_{label.lower()}"})
        jb = jb.merge(jc, on="date", how="inner")
    jb.to_csv(OUT / "outputs" / "nav_compare.csv", index=False)

    new = vs["NEW_LIVE"]
    verdict = (
        f"NEW_LIVE (FINBAND+KD+A05) vs OLD_SF_KD held-out score={new['heldout_2019_plus']['score']:+.3f} "
        f"tip_clean={new['tip_clean']} "
        f"YTD={new['tip_gates']['ytd']['gate']} 1y={new['tip_gates']['trailing_1y']['gate']}. "
        f"Live Soft-Frozen={soft.SOFT_FROZEN_FIN_CLIP}."
    )
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "LIVE_STACK_RERUN",
        "status": "PAPER_RERUN",
        "capital": float(DEFAULT_CAPITAL),
        "lot_size": BOARD_LOT,
        "kd_opt": KD_OPT,
        "live_soft_frozen_clip": list(soft.SOFT_FROZEN_FIN_CLIP),
        "books": {
            "OLD_SF_KD": "Soft-Frozen FIN [0.50,0.95] + KD_OPT",
            "FINBAND_KD": "Soft-Frozen FIN [0.60,0.90] + KD_OPT",
            "OLD_SF_KD_A05": "Soft-Frozen FIN [0.50,0.95] + KD_OPT + BLEND_E45_A05",
            "NEW_LIVE": "Soft-Frozen FIN [0.60,0.90] + KD_OPT + BLEND_E45_A05 (current live)",
        },
        "absolute": abs_rows,
        "vs_old_sf_kd": vs,
        "verdict": verdict,
    }
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    RESEARCH.joinpath("LIVE_STACK_RERUN.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    lines = [
        "# Live stack paper re-run (post FINBAND + E45 A05)",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Capital **{DEFAULT_CAPITAL:,.0f}** · lot **{BOARD_LOT}** · KD_OPT · Soft-Frozen live **{soft.SOFT_FROZEN_FIN_CLIP}**",
        "",
        "## Absolute",
        "",
        "| book | full CAGR | full MDD | heldout CAGR | heldout MDD | sealed CAGR | sealed MDD |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for label in ("OLD_SF_KD", "FINBAND_KD", "OLD_SF_KD_A05", "NEW_LIVE"):
        a = abs_rows[label]
        lines.append(
            f"| `{label}` | {a['full']['cagr']*100:.2f}% | {a['full']['max_drawdown']*100:.2f}% | "
            f"{a['heldout_2019_plus']['cagr']*100:.2f}% | {a['heldout_2019_plus']['max_drawdown']*100:.2f}% | "
            f"{a['sealed_2023_plus']['cagr']*100:.2f}% | {a['sealed_2023_plus']['max_drawdown']*100:.2f}% |"
        )
    lines += [
        "",
        "## vs OLD_SF_KD (pre big-win)",
        "",
        "| book | heldout score | MDD↑pp | CAGR gb | YTD | 1y | tip_clean |",
        "|---|---:|---:|---:|---|---|---|",
    ]
    for label in ("FINBAND_KD", "OLD_SF_KD_A05", "NEW_LIVE"):
        r = vs[label]
        h = r["heldout_2019_plus"]
        tip = r["tip_gates"]
        lines.append(
            f"| `{label}` | {h['score']:.3f} | {h['mdd_improve_pp']:.3f} | {h['cagr_giveback_pp']:.3f} | "
            f"{tip['ytd']['gate']} | {tip['trailing_1y']['gate']} | {r['tip_clean']} |"
        )
    lines += [
        "",
        "## Verdict",
        "",
        verdict,
        "",
        f"Repro: `{OUT.relative_to(ROOT)}/`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "REPORT.md").write_text(md)
    RESEARCH.joinpath("LIVE_STACK_RERUN.md").write_text(md)
    print(json.dumps({"verdict": verdict, "vs": {k: v["heldout_2019_plus"] for k, v in vs.items()}}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
