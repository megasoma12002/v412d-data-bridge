#!/usr/bin/env python3
"""FIN EQUAL × KD_OPT λ-mix paper screen — coexistence probe (RESEARCH ONLY).

Question: can λ·FIN_EQUAL + (1−λ)·FIN_PRE_EXDIV_KD (KD_OPT params) improve
tip hygiene and held-out score together vs pure poles / vs MIX_L75?

KD_OPT = KD_APR15_MAY15_Klt30_T15 (Yahoo K9 season + pre-ex T−15 skip-buy).

- Soft-Frozen KEEP · live e21 untouched
- Telecom held at TEL_EQUAL
- Capital 500M · lot 1000 · Exact T+1 · E22_v2s_tw
- λ=1 pure EQUAL · λ=0 pure KD_OPT
"""
from __future__ import annotations

import argparse
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
    FIN_MIX_EQUAL_PRE_EXDIV_KD,
    FIN_PRE_EXDIV_KD,
    TEL_EQUAL,
    build_kd_season_tilt_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/fin-equal-kd-mix-20260909"
RESEARCH = ROOT / "research/ops"

CHARTER_CAPITAL = 500_000_000.0
CHARTER_LOT = BOARD_LOT
LAMBDAS = (1.0, 0.75, 0.5, 0.25, 0.0)
TRAIL_ALERT_PP = 3.0
TRAIL_PAUSE_PP = 5.0
# Paper optimal KD_OPT
KD_OPT = {
    "id": "KD_APR15_MAY15_Klt30_T15",
    "season_start": (4, 15),
    "season_end": (5, 15),
    "k_thresh": 30.0,
    "pre_days": 15,
    "active_score": 1.5,
}


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
            out[wname] = {"giveback_pp": None, "gate": "INSUFFICIENT", "rel_nav": None}
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
            "base_total_ret": float(bn.iloc[-1] - 1),
            "chal_total_ret": float(cn.iloc[-1] - 1),
        }
    return out


def run_one(market, dividends, target, regime, *, lam, kd_scores, kd_buy_ok, base_nav):
    if abs(lam - 1.0) < 1e-12:
        policy, mix_lam = FIN_EQUAL, None
        need = False
    elif abs(lam - 0.0) < 1e-12:
        policy, mix_lam = FIN_PRE_EXDIV_KD, None
        need = True
    else:
        policy, mix_lam = FIN_MIX_EQUAL_PRE_EXDIV_KD, float(lam)
        need = True

    nav, fills, meta = simulate_core(
        market,
        target,
        regime,
        dividends,
        apply_e22=True,
        apply_stock_div=True,
        capital=CHARTER_CAPITAL,
        lot_size=CHARTER_LOT,
        financial_alloc=policy,
        telecom_alloc=TEL_EQUAL,
        fin_name_scores=kd_scores if need else None,
        fin_buy_ok=kd_buy_ok if need else None,
        fin_mix_lambda=mix_lam,
    )
    win = {w: window_stats(nav, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
    asof = pd.to_datetime(nav["date"]).max()
    tip = tip_gate(base_nav, nav, asof) if base_nav is not None else None
    qty = pd.to_numeric(fills["quantity"], errors="coerce") if len(fills) else pd.Series(dtype=float)
    board_ok = bool(len(qty) == 0 or ((qty % CHARTER_LOT == 0) & (qty >= CHARTER_LOT)).all())
    book_id = (
        f"KD_MIX_L{int(round(lam * 100)):02d}" if mix_lam is not None else ("KD_OPT" if policy == FIN_PRE_EXDIV_KD else policy)
    )
    return {
        "id": book_id,
        "lambda_equal": float(lam),
        "financial_alloc": policy,
        "fin_mix_lambda": mix_lam,
        "exact_t1_ok": bool(meta.get("exact_t1_ok")),
        "fills_board_lot_ok": board_ok,
        "n_fills": int(len(fills)),
        "windows": win,
        "tip_gates": tip,
        "nav": nav,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lambdas", nargs="*", type=float, default=list(LAMBDAS))
    args = ap.parse_args()
    lambs = [float(x) for x in args.lambdas]
    for x in lambs:
        if not (0.0 <= x <= 1.0):
            raise SystemExit(f"lambda out of range: {x}")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "outputs").mkdir(exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.9]

    print("loading market + dividends ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, _s, target, regime = e16_features(market)
    cal = pd.to_datetime(market["date"]).drop_duplicates().sort_values().to_numpy()

    print(f"building KD_OPT scores ({KD_OPT['id']}) ...", flush=True)
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
    kd_buy_ok = build_pre_exdiv_window_buy_ok(
        cal,
        dividends,
        FIN,
        pre_days=int(KD_OPT["pre_days"]),
        also_stock_ex=True,
    )

    if 1.0 not in lambs:
        lambs = [1.0] + lambs

    results = {}
    base_nav = None
    for i, lam in enumerate(lambs, 1):
        print(f"  [{i}/{len(lambs)}] λ={lam} ...", flush=True)
        row = run_one(
            market,
            dividends,
            target,
            regime,
            lam=lam,
            kd_scores=kd_scores,
            kd_buy_ok=kd_buy_ok,
            base_nav=base_nav,
        )
        assert row["exact_t1_ok"] and row["fills_board_lot_ok"], row["id"]
        if abs(lam - 1.0) < 1e-12:
            base_nav = row["nav"].copy()
            row["tip_gates"] = tip_gate(
                base_nav, row["nav"], pd.to_datetime(row["nav"]["date"]).max()
            )
        results[row["id"]] = row

    base = results["FIN_EQUAL"]
    ranked = []
    for rid, row in results.items():
        if rid == "FIN_EQUAL":
            continue
        held = score_vs_base(base["windows"]["heldout_2019_plus"], row["windows"]["heldout_2019_plus"])
        sealed = score_vs_base(base["windows"]["sealed_2023_plus"], row["windows"]["sealed_2023_plus"])
        tip = row["tip_gates"] or {}
        ytd = tip.get("ytd") or {}
        t1 = tip.get("trailing_1y") or {}
        tip_clean = ytd.get("gate") == "PASS" and t1.get("gate") == "PASS"
        coexist = bool(held["score"] > 0 and tip_clean)
        row["scores"] = {
            "heldout_2019_plus": held,
            "sealed_2023_plus_REPORT_ONLY": sealed,
        }
        row["tip_clean"] = tip_clean
        row["coexist_heldout_pos_and_tip_clean"] = coexist
        ranked.append(row)
    ranked.sort(key=lambda r: r["scores"]["heldout_2019_plus"]["score"], reverse=True)

    any_coexist = any(r["coexist_heldout_pos_and_tip_clean"] for r in ranked)
    best_tip_clean = [r for r in ranked if r["tip_clean"]]
    best_tip_clean.sort(key=lambda r: r["scores"]["heldout_2019_plus"]["score"], reverse=True)

    def slim(row):
        return {k: v for k, v in row.items() if k != "nav"}

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "FIN_EQUAL_KD_OPT_MIX",
        "status": "COEXIST_CANDIDATE_FOUND" if any_coexist else "NO_COEXIST_ON_GRID",
        "definition": (
            f"λ·FIN_EQUAL + (1−λ)·FIN_PRE_EXDIV_KD ({KD_OPT['id']}) "
            "(notional blend, then 整張)"
        ),
        "kd_opt": KD_OPT,
        "live_wire": False,
        "soft_frozen_keep": True,
        "execution_context": {
            "capital": CHARTER_CAPITAL,
            "board_lot": CHARTER_LOT,
            "telecom_held_at": TEL_EQUAL,
        },
        "lambdas": lambs,
        "tip_gates": {"alert_pp": TRAIL_ALERT_PP, "pause_pp": TRAIL_PAUSE_PP},
        "objective_heldout": "mdd_improve_pp - 0.5*|cagr_giveback_pp| vs FIN_EQUAL",
        "coexist_rule": "heldout score > 0 AND tip YTD+1y both PASS (giveback≤3pp)",
        "any_coexist": any_coexist,
        "base": slim(base),
        "challengers": {r["id"]: slim(r) for r in ranked},
        "ranked_heldout": [slim(r) for r in ranked],
        "best_tip_clean_by_heldout": [slim(r) for r in best_tip_clean[:3]],
        "verdict": (
            (
                f"Coexist candidate {best_tip_clean[0]['id']} "
                f"(λ={best_tip_clean[0]['lambda_equal']:.2f}): "
                f"held-out {best_tip_clean[0]['scores']['heldout_2019_plus']['score']:+.3f} "
                "and tip YTD/1y PASS. Soft-Frozen KEEP · no live wire."
            )
            if any_coexist and best_tip_clean
            else "No λ on this grid jointly clears tip PASS (≤3pp) and positive held-out. "
            "Poles trade off; mix interpolates."
        ),
        "coexist_candidate": (
            {
                "id": best_tip_clean[0]["id"],
                "lambda_equal": best_tip_clean[0]["lambda_equal"],
                "heldout_score": best_tip_clean[0]["scores"]["heldout_2019_plus"]["score"],
                "tip_ytd_giveback_pp": (best_tip_clean[0]["tip_gates"] or {})
                .get("ytd", {})
                .get("giveback_pp"),
                "tip_1y_giveback_pp": (best_tip_clean[0]["tip_gates"] or {})
                .get("trailing_1y", {})
                .get("giveback_pp"),
            }
            if any_coexist and best_tip_clean
            else None
        ),
        "compare_note": (
            "vs MIX_L75 (EQUAL×RS): this grid mixes EQUAL×KD_OPT; "
            "does not stack MIX×KD. Soft-Frozen KEEP · cutover still separate ACCEPT."
        ),
    }

    for r in ranked:
        if r["id"] in ("KD_OPT", "KD_MIX_L50", "KD_MIX_L25", "KD_MIX_L75"):
            jb = base["nav"][["date", "nav"]].rename(columns={"nav": "nav_base"})
            jc = r["nav"][["date", "nav"]].rename(columns={"nav": f"nav_{r['id'].lower()}"})
            joined = jb.merge(jc, on="date", how="inner")
            joined.to_csv(OUT / "outputs" / f"nav_compare_{r['id'].lower()}.csv", index=False)

    (OUT / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    RESEARCH.joinpath("FIN_EQUAL_KD_OPT_MIX.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    lines = [
        "# FIN EQUAL × KD_OPT λ-mix — coexistence probe",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Soft-Frozen **KEEP** · live wire **false**",
        f"Status: **{payload['status']}**",
        "",
        f"Definition: `λ·FIN_EQUAL + (1−λ)·FIN_PRE_EXDIV_KD` (`{KD_OPT['id']}`)",
        f"Coexist rule: held-out score > 0 **and** tip YTD+1y both PASS (giveback ≤ {TRAIL_ALERT_PP:.0f}pp)",
        "",
        "## Grid vs `FIN_EQUAL`",
        "",
        "| id | λ(EQUAL) | heldout score | MDD↑pp | CAGR giveback | YTD gate | 1y gate | coexist? |",
        "|---|---:|---:|---:|---:|---|---|---|",
        "| `FIN_EQUAL` | 1.00 | — | — | — | PASS | PASS | — |",
    ]
    for r in ranked:
        h = r["scores"]["heldout_2019_plus"]
        tip = r["tip_gates"] or {}
        ytd = tip.get("ytd") or {}
        t1 = tip.get("trailing_1y") or {}
        lines.append(
            f"| `{r['id']}` | {r['lambda_equal']:.2f} | {h['score']:.3f} | "
            f"{h['mdd_improve_pp']:.3f} | {h['cagr_giveback_pp']:.3f} | "
            f"{ytd.get('gate')} | {t1.get('gate')} | {r['coexist_heldout_pos_and_tip_clean']} |"
        )
    lines += [
        "",
        "## Verdict",
        "",
        payload["verdict"],
        "",
        "## Hard rules",
        "",
        "- Soft-Frozen KEEP · no live wire · no cutover from this probe",
        "- Does not stack MIX_L75×KD (EQUAL×KD only)",
        "- Dual-paper OPERATING observe unchanged until dedicated ballot",
        "",
        f"Repro: `{OUT.relative_to(ROOT)}/`",
        "",
        "```bash",
        "python3 scripts/e16_fin_equal_kd_mix_paper.py",
        "```",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "REPORT.md").write_text(md)
    RESEARCH.joinpath("FIN_EQUAL_KD_OPT_MIX.md").write_text(md)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "any_coexist": any_coexist,
                "ranked": [
                    {
                        "id": r["id"],
                        "lam": r["lambda_equal"],
                        "held": r["scores"]["heldout_2019_plus"]["score"],
                        "ytd": (r["tip_gates"] or {}).get("ytd", {}).get("gate"),
                        "t1": (r["tip_gates"] or {}).get("trailing_1y", {}).get("gate"),
                        "coexist": r["coexist_heldout_pos_and_tip_clean"],
                    }
                    for r in ranked
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
