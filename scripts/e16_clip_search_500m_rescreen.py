#!/usr/bin/env python3
"""Soft-Frozen clip top-K rescreen @ live capital 500M (paper only).

Re-runs Stage B locked top-3 TEL/ETF floor challengers vs Soft-Frozen BASE
at DEFAULT_CAPITAL (500M) · lot 1000 · Exact T+1 · E22_v2s_tw.

Optionally wires live FIN within-sleeve KD_OPT so the screen matches current
live stack (clip change on top of KD_OPT). Soft-Frozen module constants are
NOT edited.

Soft-Frozen KEEP · Class D flip still needs human ACCEPT.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e16_clip_search_challenger as clip
import e16_soft_frozen_base as soft
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, load_market, window_stats
from e50_early_stack_combined_nav import FIN, simulate_core
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
OUT = ROOT / "repro/clip-search-500m-rescreen-20260909"
RESEARCH = ROOT / "research/ops"

# Stage B locked top-K (FIN = Soft-Frozen)
TOP_K = [
    (0.50, 0.95, 0.08, 0.35, 0.05, 0.35),  # score 0.396 @ 5M
    (0.50, 0.95, 0.10, 0.35, 0.00, 0.35),
    (0.50, 0.95, 0.08, 0.35, 0.00, 0.35),
]
KD_OPT = {
    "id": "KD_APR15_MAY15_Klt30_T15",
    "season_start": (4, 15),
    "season_end": (5, 15),
    "k_thresh": 30.0,
    "pre_days": 15,
    "active_score": 1.5,
}
TRAIL_ALERT_PP = 3.0
TRAIL_PAUSE_PP = 5.0


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


def run_one(market, dividends, clips, *, regime, score, kd_scores, kd_ok):
    flo, fhi, tlo, thi, elo, ehi = clips
    target = clip.build_targets_with_clips(
        regime=regime,
        score=score,
        fin_lo=flo,
        fin_hi=fhi,
        tel_lo=tlo,
        tel_hi=thi,
        etf_lo=elo,
        etf_hi=ehi,
    )
    nav, fills, meta = simulate_core(
        market,
        target,
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
    )
    win = {w: window_stats(nav, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
    return {
        "id": clip.cand_id(*clips),
        "clips": {"fin": [flo, fhi], "tel": [tlo, thi], "etf": [elo, ehi]},
        "is_live_soft_frozen": clip.is_live_tuple(*clips),
        "exact_t1_ok": bool(meta.get("exact_t1_ok")),
        "n_fills": int(len(fills)),
        "windows": win,
        "nav": nav,
        "mean_target": {
            "Financial": float(target["Financial"].mean()),
            "Telecom": float(target["Telecom"].mean()),
            "0050": float(target["0050"].mean()),
        },
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "outputs").mkdir(exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.9]
    assert abs(DEFAULT_CAPITAL - 500_000_000.0) < 1.0

    print("loading ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, _s, _t, regime, score = soft.build_soft_frozen_targets(market)
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

    live = (*clip.LIVE_FIN, *clip.LIVE_TEL, *clip.LIVE_ETF)
    print("BASE Soft-Frozen + KD_OPT @ 500M ...", flush=True)
    base = run_one(market, dividends, live, regime=regime, score=score, kd_scores=kd_scores, kd_ok=kd_ok)
    base["id"] = "BASE_SOFT_FROZEN_KD_OPT"
    assert base["exact_t1_ok"]
    asof = pd.to_datetime(base["nav"]["date"]).max()

    ranked = []
    for i, clips in enumerate(TOP_K, 1):
        cid = clip.cand_id(*clips)
        print(f"  [{i}/{len(TOP_K)}] {cid} ...", flush=True)
        row = run_one(market, dividends, clips, regime=regime, score=score, kd_scores=kd_scores, kd_ok=kd_ok)
        assert row["exact_t1_ok"], cid
        held = clip.score_row(base["windows"]["heldout_2019_plus"], row["windows"]["heldout_2019_plus"])
        sealed = clip.score_row(base["windows"]["sealed_2023_plus"], row["windows"]["sealed_2023_plus"])
        tip = tip_gate(base["nav"], row["nav"], asof)
        tip_clean = tip["ytd"]["gate"] == "PASS" and tip["trailing_1y"]["gate"] == "PASS"
        pack = {
            "id": row["id"],
            "clips": row["clips"],
            "n_fills": row["n_fills"],
            "mean_target": row["mean_target"],
            "scores": {"heldout_2019_plus": held, "sealed_2023_plus_REPORT_ONLY": sealed},
            "tip_gates": tip,
            "tip_clean": tip_clean,
            "windows": {
                w: {
                    "cagr": row["windows"][w].get("cagr"),
                    "max_drawdown": row["windows"][w].get("max_drawdown"),
                }
                for w in ("full", "heldout_2019_plus", "sealed_2023_plus")
            },
        }
        ranked.append(pack)
        slug = row["id"].lower().replace(".", "p")
        row["nav"].to_csv(OUT / "outputs" / f"{slug}_daily_nav.csv", index=False)

    ranked.sort(key=lambda r: r["scores"]["heldout_2019_plus"]["score"], reverse=True)
    best = ranked[0]
    base_w = {
        w: {
            "cagr": base["windows"][w].get("cagr"),
            "max_drawdown": base["windows"][w].get("max_drawdown"),
        }
        for w in ("full", "heldout_2019_plus", "sealed_2023_plus")
    }
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "SOFT_FROZEN_CLIP_500M_RESCREEN",
        "status": "PAPER_RESCREEN",
        "live_wire": False,
        "soft_frozen_keep": True,
        "capital": float(DEFAULT_CAPITAL),
        "lot_size": BOARD_LOT,
        "fin_within_sleeve": KD_OPT["id"],
        "base": {
            "id": base["id"],
            "clips": {
                "fin": list(clip.LIVE_FIN),
                "tel": list(clip.LIVE_TEL),
                "etf": list(clip.LIVE_ETF),
            },
            "windows": base_w,
            "n_fills": base["n_fills"],
        },
        "ranked": ranked,
        "recommended_observe_id": best["id"],
        "verdict": (
            f"Best @500M+KD_OPT `{best['id']}` held-out={best['scores']['heldout_2019_plus']['score']:+.3f} "
            f"tip_clean={best['tip_clean']}. Soft-Frozen KEEP · Class D flip needs ACCEPT."
        ),
    }
    base["nav"].to_csv(OUT / "outputs" / "base_soft_frozen_kd_opt_daily_nav.csv", index=False)
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    RESEARCH.joinpath("SOFT_FROZEN_CLIP_500M_RESCREEN.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    lines = [
        "# Soft-Frozen clip top-K — 500M rescreen (paper)",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Status: **PAPER_RESCREEN** · Soft-Frozen **KEEP** · live wire **false**",
        f"Stack: capital **{DEFAULT_CAPITAL:,.0f}** · lot **{BOARD_LOT}** · FIN within-sleeve **`{KD_OPT['id']}`**",
        "",
        "## BASE (live Soft-Frozen + KD_OPT)",
        "",
        f"| window | CAGR | MDD |",
        f"|---|---:|---:|",
    ]
    for w in ("full", "heldout_2019_plus", "sealed_2023_plus"):
        st = base_w[w]
        lines.append(f"| `{w}` | {st['cagr']*100:.2f}% | {st['max_drawdown']*100:.2f}% |")
    lines += [
        "",
        "## Challengers (Stage B top-K @ 500M)",
        "",
        "| id | heldout score | MDD↑pp | CAGR gb | YTD | 1y | tip_clean |",
        "|---|---:|---:|---:|---|---|---|",
    ]
    for r in ranked:
        h = r["scores"]["heldout_2019_plus"]
        tip = r["tip_gates"]
        lines.append(
            f"| `{r['id']}` | {h['score']:.3f} | {h['mdd_improve_pp']:.3f} | "
            f"{h['cagr_giveback_pp']:.3f} | {tip['ytd']['gate']} | {tip['trailing_1y']['gate']} | "
            f"{r['tip_clean']} |"
        )
    lines += [
        "",
        "## Verdict",
        "",
        payload["verdict"],
        "",
        f"Recommended Stage E observe id: **`{best['id']}`**",
        "",
        "## Hard rules",
        "",
        "- Soft-Frozen live constants untouched",
        "- Passing ≠ Class D flip",
        "- Flip ballot: `SOFT_FROZEN_CLIP_FLIP_BALLOT_DRAFT.md`",
        "",
        f"Repro: `{OUT.relative_to(ROOT)}/`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "REPORT.md").write_text(md)
    RESEARCH.joinpath("SOFT_FROZEN_CLIP_500M_RESCREEN.md").write_text(md)
    print(json.dumps({"best": best["id"], "heldout": best["scores"]["heldout_2019_plus"], "tip_clean": best["tip_clean"], "verdict": payload["verdict"]}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
