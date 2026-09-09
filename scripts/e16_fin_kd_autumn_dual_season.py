#!/usr/bin/env python3
"""KD_OPT × autumn post-ex dual-season paper mix (RESEARCH ONLY).

Dual-season book = spring KD_OPT scores/buy_ok ∪ autumn POST_EXDIV scores/buy_ok
(seasons do not overlap; scores add; buy_ok = AND).

Also λ-mix of sleeve notionals is NOT used — seasons are sequential, so score-union
is the natural mix. Compare:
  - FIN_EQUAL
  - KD_OPT (live reference)
  - AUTUMN_BEST (from optimize JSON, else probe baseline)
  - DUAL_KD_AUTUMN

Stop if DUAL does not improve tip/held-out vs KD_OPT.
Soft-Frozen KEEP · live KD_OPT untouched.
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
from e50_early_stack_combined_nav import FIN, e16_features, simulate_core
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp
from tw_share_lots import BOARD_LOT
from within_sleeve_alloc import (
    FIN_EQUAL,
    FIN_POST_EXDIV_KD,
    FIN_PRE_EXDIV_KD,
    TEL_EQUAL,
    build_exdiv_buy_ok,
    build_kd_post_exdiv_season_tilt_scores,
    build_kd_season_tilt_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/fin-kd-autumn-dual-season-20260909"
RESEARCH = ROOT / "research/ops"
OPT_JSON = RESEARCH / "FIN_POST_EXDIV_AUTUMN_OPTIMIZE.json"

CAPITAL = 500_000_000.0
LOT = BOARD_LOT
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
PROBE_AUTUMN = {
    "id": "AUT_OCT20_DEC10_Klt25_H40",
    "season_start": (10, 20),
    "season_end": (12, 10),
    "k_thresh": 25.0,
    "hold_days": 40,
    "active_score": 1.5,
}


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
    cagr_pp = cagr_delta_pp(
        base_stats.get("cagr"), chal_stats.get("cagr"), missing_as_zero=True
    )
    giveback = abs(float(cagr_pp)) if cagr_pp is not None else 9.0
    return {
        "mdd_improve_pp": float(mdd_pp),
        "cagr_giveback_pp": float(cagr_pp) if cagr_pp is not None else None,
        "score": float(mdd_pp) - 0.5 * giveback,
    }


def load_autumn_params() -> dict:
    if OPT_JSON.exists():
        d = json.loads(OPT_JSON.read_text())
        best = d.get("best_autumn") or {}
        if best.get("season_start") and best.get("season_end"):
            return {
                "id": best["id"],
                "season_start": tuple(best["season_start"]),
                "season_end": tuple(best["season_end"]),
                "k_thresh": float(best["k_thresh"]),
                "hold_days": int(best["hold_days"]),
                "active_score": 1.5,
                "source": "optimize_best",
            }
    return {**PROBE_AUTUMN, "source": "probe_baseline"}


def combine_dual(kd_scores: pd.DataFrame, autumn_scores: pd.DataFrame, kd_ok, autumn_ok):
    idx = kd_scores.index.union(autumn_scores.index).sort_values()
    cols = list(dict.fromkeys(list(kd_scores.columns) + list(autumn_scores.columns)))
    a = kd_scores.reindex(index=idx, columns=cols).fillna(0.0)
    b = autumn_scores.reindex(index=idx, columns=cols).fillna(0.0)
    scores = a + b
    # buy_ok AND — missing treated as True so one side alone does not blank the other
    ok_a = kd_ok.reindex(index=idx, columns=cols)
    ok_b = autumn_ok.reindex(index=idx, columns=cols)
    buy_ok = ok_a.fillna(True) & ok_b.fillna(True)
    return scores, buy_ok


def sim(market, target, regime, dividends, *, policy, scores=None, buy_ok=None):
    return simulate_core(
        market,
        target,
        regime,
        dividends,
        apply_e22=True,
        apply_stock_div=True,
        capital=CAPITAL,
        lot_size=LOT,
        financial_alloc=policy,
        telecom_alloc=TEL_EQUAL,
        fin_name_scores=scores,
        fin_buy_ok=buy_ok,
    )


def pack(label, nav, fills, meta, win_b, nav_b, asof):
    win = {w: window_stats(nav, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
    tip = tip_gate(nav_b, nav, asof)
    held = score_vs_base(win_b["heldout_2019_plus"], win["heldout_2019_plus"])
    sealed = score_vs_base(win_b["sealed_2023_plus"], win["sealed_2023_plus"])
    return {
        "id": label,
        "n_fills": int(len(fills)),
        "exact_t1_ok": bool(meta.get("exact_t1_ok")),
        "scores": {"heldout_2019_plus": held, "sealed_2023_plus_REPORT_ONLY": sealed},
        "tip_gates": tip,
        "tip_clean": tip["ytd"]["gate"] == "PASS" and tip["trailing_1y"]["gate"] == "PASS",
        "nav": nav,
        "windows": win,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "outputs").mkdir(exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.9]

    autumn = load_autumn_params()
    print(f"autumn params ({autumn['source']}): {autumn['id']}", flush=True)

    print("loading ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, _s, target, regime = e16_features(market)
    cal = pd.to_datetime(market["date"]).drop_duplicates().sort_values()

    print("building scores ...", flush=True)
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
    autumn_scores = build_kd_post_exdiv_season_tilt_scores(
        market,
        dividends,
        FIN,
        k_thresh=float(autumn["k_thresh"]),
        season_start=autumn["season_start"],
        season_end=autumn["season_end"],
        active_score=float(autumn["active_score"]),
        hold_days=int(autumn["hold_days"]),
    )
    autumn_ok = build_exdiv_buy_ok(cal, dividends, FIN, also_stock_ex=True)
    dual_scores, dual_ok = combine_dual(kd_scores, autumn_scores, kd_ok, autumn_ok)

    books = {}
    specs = [
        ("FIN_EQUAL", FIN_EQUAL, None, None),
        ("KD_OPT", FIN_PRE_EXDIV_KD, kd_scores, kd_ok),
        ("AUTUMN_BEST", FIN_POST_EXDIV_KD, autumn_scores, autumn_ok),
        ("DUAL_KD_AUTUMN", FIN_PRE_EXDIV_KD, dual_scores, dual_ok),
    ]
    for label, policy, scores, buy_ok in specs:
        print(f"  sim {label} ...", flush=True)
        nav, fills, meta = sim(
            market, target, regime, dividends, policy=policy, scores=scores, buy_ok=buy_ok
        )
        assert meta.get("exact_t1_ok"), label
        slug = label.lower()
        nav.to_csv(OUT / "outputs" / f"{slug}_daily_nav.csv", index=False)
        fills.to_csv(OUT / "outputs" / f"{slug}_fills.csv", index=False)
        books[label] = {"nav": nav, "fills": fills, "meta": meta}

    base = books["FIN_EQUAL"]["nav"]
    asof = pd.to_datetime(base["date"]).max()
    win_b = {w: window_stats(base, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}

    ranked = []
    packed = {}
    for label in ("KD_OPT", "AUTUMN_BEST", "DUAL_KD_AUTUMN"):
        b = books[label]
        row = pack(label, b["nav"], b["fills"], b["meta"], win_b, base, asof)
        packed[label] = row
        ranked.append({k: v for k, v in row.items() if k not in ("nav", "windows")})

    kd_h = packed["KD_OPT"]["scores"]["heldout_2019_plus"]["score"]
    dual = packed["DUAL_KD_AUTUMN"]
    dual_h = dual["scores"]["heldout_2019_plus"]["score"]
    delta = float(dual_h - kd_h)
    lifts = bool(dual["tip_clean"] and dual_h > kd_h + 1e-9)
    status = "STOP" if not lifts else "CANDIDATE"

    jb = base[["date", "nav"]].rename(columns={"nav": "nav_base"})
    for label in ("KD_OPT", "AUTUMN_BEST", "DUAL_KD_AUTUMN"):
        jc = packed[label]["nav"][["date", "nav"]].rename(columns={"nav": f"nav_{label.lower()}"})
        jb = jb.merge(jc, on="date", how="inner")
    jb.to_csv(OUT / "outputs" / "nav_compare.csv", index=False)

    ranked.sort(key=lambda r: r["scores"]["heldout_2019_plus"]["score"], reverse=True)
    verdict = (
        f"DUAL_KD_AUTUMN held-out={dual_h:+.3f} tip_clean={dual['tip_clean']} · "
        f"vs KD_OPT Δ={delta:+.3f} (KD_OPT={kd_h:+.3f}). "
        f"{'No tip/held-out lift → STOP autumn dual-season.' if not lifts else 'Dual beats KD_OPT (paper only).'} "
        f"Autumn=`{autumn['id']}`. Soft-Frozen KEEP · live KD_OPT untouched."
    )
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "FIN_KD_AUTUMN_DUAL_SEASON",
        "status": status,
        "live_wire": False,
        "soft_frozen_keep": True,
        "live_kd_opt_unchanged": True,
        "autumn_params": autumn,
        "kd_opt": KD_OPT,
        "ranked": ranked,
        "dual_vs_kd_opt_heldout_delta": delta,
        "lifts_vs_kd_opt": lifts,
        "verdict": verdict,
        "stop_rule": "No tip/held-out lift vs KD_OPT → STOP",
    }
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    RESEARCH.joinpath("FIN_KD_AUTUMN_DUAL_SEASON.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    lines = [
        "# FIN KD_OPT × autumn — dual-season paper mix",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Status: **{status}** · Soft-Frozen **KEEP** · live **KD_OPT untouched**",
        "",
        f"Autumn sleeve: `{autumn['id']}` ({autumn['source']})",
        f"Dual = KD_OPT scores + autumn scores · buy_ok AND",
        "",
        "| id | heldout | MDD↑pp | CAGR gb | YTD | 1y | tip_clean |",
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
        f"**DUAL vs KD_OPT held-out Δ = {delta:+.3f}** · lifts? **{lifts}**",
        "",
        "## Verdict",
        "",
        verdict,
        "",
        "## Hard rules",
        "",
        "- Soft-Frozen KEEP · no live wire · no cutover",
        "- Does not replace live KD_OPT",
        "",
        f"Repro: `{OUT.relative_to(ROOT)}/`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "REPORT.md").write_text(md)
    RESEARCH.joinpath("FIN_KD_AUTUMN_DUAL_SEASON.md").write_text(md)
    print(json.dumps({"status": status, "delta": delta, "lifts": lifts, "verdict": verdict}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
