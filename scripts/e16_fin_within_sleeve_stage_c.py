#!/usr/bin/env python3
"""Financial within-sleeve Stage C — ex-div skip-buy + RS soft-tilt (RESEARCH ONLY).

Human rationale: 各檔各做各的 — cash/stock ex-dates differ; relative strength timing differs.
Stage B (TOP1/TOP2/MIN_LOT_PACK) already STOP'd. Stage C tests softer per-name timing
without hard concentration.

- Soft-Frozen sleeve clips untouched.
- Live e21 NOT wired.
- Telecom held at TEL_EQUAL.
- Execution: Exact T+1 · E22_v2s_tw · lot_size=1000 · capital=500_000_000
- Selection: held-out 2019+ vs FIN_EQUAL; sealed report-only.
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
    FIN_ALLOC_POLICIES,
    FIN_EQUAL,
    FIN_EXDIV_SKIP_BUY,
    FIN_RS_SOFT_TILT,
    FIN_RS_SOFT_TILT_EXDIV,
    TEL_EQUAL,
    build_exdiv_buy_ok,
    build_name_scores,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/fin-within-sleeve-stagec-20260908"
RESEARCH = ROOT / "research/ops"

CHARTER_CAPITAL = 500_000_000.0
CHARTER_LOT = BOARD_LOT
STAGE_C_POLICIES = (
    FIN_EQUAL,
    FIN_RS_SOFT_TILT,
    FIN_EXDIV_SKIP_BUY,
    FIN_RS_SOFT_TILT_EXDIV,
)
SCORE_POLICIES = {FIN_RS_SOFT_TILT, FIN_RS_SOFT_TILT_EXDIV}
BUY_OK_POLICIES = {FIN_EXDIV_SKIP_BUY, FIN_RS_SOFT_TILT_EXDIV}


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


def tip_fin_diagnostics(nav: pd.DataFrame, meta: dict) -> dict:
    tip = nav.iloc[-1] if len(nav) else None
    end_pos = meta.get("end_positions") or {}
    fin_held = {c: float(end_pos.get(c, 0.0)) for c in FIN}
    names_with_lot = sum(1 for v in fin_held.values() if abs(v) >= CHARTER_LOT - 1e-9)
    return {
        "tip_date": None if tip is None else str(tip["date"]),
        "tip_nav": None if tip is None else float(tip["nav"]),
        "tip_cash_weight": None
        if tip is None or float(tip["nav"]) <= 0
        else float(tip["cash"]) / float(tip["nav"]),
        "tip_pre_financial": None if tip is None else float(tip["pre_financial"]),
        "tip_pre_telecom": None if tip is None else float(tip["pre_telecom"]),
        "tip_fin_positions": fin_held,
        "tip_fin_names_with_board_lot": int(names_with_lot),
        "mean_pre_financial": float(nav["pre_financial"].mean()) if len(nav) else None,
    }


def run_policy(
    market,
    dividends,
    target,
    regime,
    *,
    policy: str,
    fin_scores,
    fin_buy_ok,
) -> dict:
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
        fin_name_scores=fin_scores if policy in SCORE_POLICIES else None,
        fin_buy_ok=fin_buy_ok if policy in BUY_OK_POLICIES else None,
    )
    win = {w: window_stats(nav, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
    qty = pd.to_numeric(fills["quantity"], errors="coerce") if len(fills) else pd.Series(dtype=float)
    board_ok = bool(len(qty) == 0 or ((qty % CHARTER_LOT == 0) & (qty >= CHARTER_LOT)).all())
    return {
        "id": policy,
        "financial_alloc": policy,
        "telecom_alloc": TEL_EQUAL,
        "exact_t1_ok": bool(meta.get("exact_t1_ok")),
        "lot_size": int(meta.get("lot_size", CHARTER_LOT)),
        "capital": CHARTER_CAPITAL,
        "n_fills": int(len(fills)),
        "fills_board_lot_ok": board_ok,
        "windows": win,
        "tip": tip_fin_diagnostics(nav, meta),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="FIN within-sleeve Stage C (paper only)")
    ap.add_argument("--policies", nargs="*", default=list(STAGE_C_POLICIES))
    args = ap.parse_args()
    policies = list(args.policies)
    for p in policies:
        if p not in FIN_ALLOC_POLICIES:
            raise SystemExit(f"unknown policy {p}")
    if FIN_EQUAL not in policies:
        policies = [FIN_EQUAL] + policies

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "outputs").mkdir(exist_ok=True)

    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.9]
    assert soft.SOFT_FROZEN_TEL_LO == 0.03

    print("loading market + dividends ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, _s, target, regime = e16_features(market)
    cal = (
        pd.to_datetime(market["date"]).drop_duplicates().sort_values().to_numpy()
    )
    fin_scores = build_name_scores(market, FIN)
    fin_buy_ok = build_exdiv_buy_ok(cal, dividends, FIN, also_stock_ex=True)
    skip_counts = (~fin_buy_ok).sum().to_dict()
    print(f"  exdiv skip-buy day-counts per name: {skip_counts}", flush=True)

    results: dict[str, dict] = {}
    for i, policy in enumerate(policies, 1):
        print(f"  [{i}/{len(policies)}] {policy} @ 500M/1000 ...", flush=True)
        results[policy] = run_policy(
            market,
            dividends,
            target,
            regime,
            policy=policy,
            fin_scores=fin_scores,
            fin_buy_ok=fin_buy_ok,
        )
        r = results[policy]
        assert r["exact_t1_ok"] and r["fills_board_lot_ok"], policy

    base = results[FIN_EQUAL]
    ranked_rows = []
    for policy, row in results.items():
        if policy == FIN_EQUAL:
            continue
        held = score_vs_base(base["windows"]["heldout_2019_plus"], row["windows"]["heldout_2019_plus"])
        row["scores"] = {
            "heldout_2019_plus": held,
            "validation_2019_2022": score_vs_base(
                base["windows"]["validation_2019_2022"], row["windows"]["validation_2019_2022"]
            ),
            "oof_2011_2018": score_vs_base(
                base["windows"]["oof_2011_2018"], row["windows"]["oof_2011_2018"]
            ),
        }
        ranked_rows.append(row)

    ranked = sorted(
        ranked_rows, key=lambda r: r["scores"]["heldout_2019_plus"]["score"], reverse=True
    )
    top = ranked[:2]
    for r in top:
        sealed = score_vs_base(base["windows"]["sealed_2023_plus"], r["windows"]["sealed_2023_plus"])
        r["scores"]["sealed_2023_plus_REPORT_ONLY"] = sealed
        r["fragile_sealed_mdd"] = bool(-sealed["mdd_improve_pp"] > 2.0 + 1e-12)

    best = ranked[0]["scores"]["heldout_2019_plus"]["score"] if ranked else None
    stop = best is None or best <= 0

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "FIN_WITHIN_SLEEVE_ALLOC_STAGE_C",
        "status": "STOP_NO_POSITIVE_HELDOUT_SCORE" if stop else "STAGE_C_CANDIDATES_LOCKED",
        "charter": "research/ops/FIN_WITHIN_SLEEVE_ALLOC_CHARTER.md",
        "human_rationale": "各檔各做各的 — ex-div dates + RS timing differ across FIN names",
        "stage_b": "STOP_NO_POSITIVE_HELDOUT_SCORE (hard concentrate / min-lot)",
        "ballot": "金融也研究分開",
        "live_wire": False,
        "soft_frozen_keep": True,
        "execution_context": {
            "capital": CHARTER_CAPITAL,
            "board_lot": CHARTER_LOT,
            "e22_books": "E22_v2s_tw",
            "telecom_held_at": TEL_EQUAL,
        },
        "exdiv_skip_buy_day_counts": {str(k): int(v) for k, v in skip_counts.items()},
        "base_id": FIN_EQUAL,
        "base": base,
        "challengers": {r["id"]: r for r in ranked_rows},
        "top_k_heldout": top,
        "stop_no_positive_heldout_score": stop,
        "objective": "heldout_mdd_improve_pp - 0.5 * abs(cagr_giveback_pp) vs FIN_EQUAL",
        "policies": list(STAGE_C_POLICIES),
    }

    (OUT / "outputs" / "stage_c_all_policies.json").write_text(
        json.dumps({"base_id": FIN_EQUAL, "results": results}, indent=2, default=str) + "\n"
    )
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    RESEARCH.joinpath("FIN_WITHIN_SLEEVE_ALLOC_STAGE_C.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    lines = [
        "# Financial Within-Sleeve Allocation — Stage C",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Human: **各檔各做各的**（除權息日不同 · 個股強弱時間不同）",
        "Ballot: **金融也研究分開** · Soft-Frozen **KEEP** · live wire **false**",
        f"Execution: capital **{CHARTER_CAPITAL:,.0f}** · lot **{CHARTER_LOT}** · Telecom=`TEL_EQUAL`",
        f"Status: **{payload['status']}**",
        "",
        "Stage B (hard TOP1/TOP2/MIN_LOT) already **STOP**. Stage C = softer per-name timing.",
        "",
        "## Policies",
        "",
        "| id | Rule |",
        "|---|---|",
        "| `FIN_EQUAL` | Equal split 4 names (BASE) |",
        "| `FIN_RS_SOFT_TILT` | Buy $ soft-tilt by causal mom score; sells equal |",
        "| `FIN_EXDIV_SKIP_BUY` | Skip buy on cash/stock ex-date for that name only |",
        "| `FIN_RS_SOFT_TILT_EXDIV` | Soft-tilt buys among non-exdiv names |",
        "",
        f"Ex-div skip-buy day counts: `{skip_counts}`",
        "",
        "## BASE (`FIN_EQUAL`)",
        "",
        f"- held-out MDD `{base['windows']['heldout_2019_plus'].get('max_drawdown')}` · "
        f"CAGR `{base['windows']['heldout_2019_plus'].get('cagr')}`",
        f"- tip FIN w `{base['tip'].get('tip_pre_financial')}` · "
        f"names w/ 張 `{base['tip'].get('tip_fin_names_with_board_lot')}` · "
        f"cash w `{base['tip'].get('tip_cash_weight')}`",
        "",
        "## Challengers vs BASE",
        "",
        "| id | heldout score | MDD↑pp | CAGRΔpp | tip FIN w | tip #names | tip cash w |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in ranked:
        h = r["scores"]["heldout_2019_plus"]
        tip = r["tip"]
        lines.append(
            f"| `{r['id']}` | {h['score']:.3f} | {h['mdd_improve_pp']:.3f} | "
            f"{h['cagr_giveback_pp']:.3f} | {tip.get('tip_pre_financial'):.4f} | "
            f"{tip.get('tip_fin_names_with_board_lot')} | {tip.get('tip_cash_weight'):.4f} |"
        )
    if top:
        lines += [
            "",
            "## Top ≤2 sealed report-only",
            "",
            "| id | sealed MDD↑pp | fragile? | tip positions |",
            "|---|---:|---|---|",
        ]
        for r in top:
            s = r["scores"]["sealed_2023_plus_REPORT_ONLY"]
            lines.append(
                f"| `{r['id']}` | {s['mdd_improve_pp']:.3f} | {r['fragile_sealed_mdd']} | "
                f"`{r['tip'].get('tip_fin_positions')}` |"
            )
    lines += [
        "",
        "## Hard rules",
        "",
        "- Soft-Frozen sleeve clip module untouched",
        "- Live e21 FIN equal-split untouched",
        "- Sealed not used for selection",
        "- Stage B STOP stands; Stage C does not reopen hard concentration",
        "",
        f"Repro: `{OUT.relative_to(ROOT)}/`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "STAGE_C.md").write_text(md)
    RESEARCH.joinpath("FIN_WITHIN_SLEEVE_ALLOC_STAGE_C.md").write_text(md)
    print(
        json.dumps(
            {"status": payload["status"], "top": [t["id"] for t in top], "best": best},
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
