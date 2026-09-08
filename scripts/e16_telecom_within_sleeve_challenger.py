#!/usr/bin/env python3
"""Telecom within-sleeve allocation — RESEARCH ONLY (Stage B).

Charter: research/ops/TELECOM_WITHIN_SLEEVE_ALLOC_CHARTER.md
Ballot: ACCEPT telecom within-sleeve charter

- Soft-Frozen sleeve clips untouched (FIN/TEL/0050 live bounds KEEP).
- Live e21 equal-split NOT wired.
- Execution: Exact T+1 · E22_v2s_tw · lot_size=1000 · capital=3_000_000
- Selection: held-out 2019+ score vs TEL_EQUAL; sealed 2023+ report-only.
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
from e50_early_stack_combined_nav import (
    TEL,
    TEL_ALLOC_EQUAL,
    TEL_ALLOC_MIN_LOT_PACK,
    TEL_ALLOC_POLICIES,
    TEL_ALLOC_TOP1,
    TEL_ALLOC_TOP2_EQUAL,
    build_tel_name_scores,
    e16_features,
    simulate_core,
)
from portfolio_capital import DEFAULT_CAPITAL
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp
from tw_share_lots import BOARD_LOT

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/telecom-within-sleeve-20260908"
RESEARCH = ROOT / "research/ops"

CHARTER_CAPITAL = 3_000_000.0
CHARTER_LOT = BOARD_LOT  # 1000

POLICIES = list(TEL_ALLOC_POLICIES)


def score_vs_base(base_stats: dict, chal_stats: dict) -> dict:
    mdd_pp = mdd_delta_pp(base_stats.get("max_drawdown"), chal_stats.get("max_drawdown"))
    cagr_pp = cagr_delta_pp(
        base_stats.get("cagr"), chal_stats.get("cagr"), missing_as_zero=True
    )
    # charter: MDD_improve_pp − 0.5 × |CAGR_giveback_pp|
    # cagr_delta_pp = base − other; positive ⇒ challenger CAGR lower ⇒ giveback
    giveback = abs(float(cagr_pp)) if cagr_pp is not None else 9.0
    return {
        "mdd_improve_pp": float(mdd_pp),
        "cagr_giveback_pp": float(cagr_pp) if cagr_pp is not None else None,
        "score": float(mdd_pp) - 0.5 * giveback,
    }


def tip_telecom_diagnostics(nav: pd.DataFrame, meta: dict) -> dict:
    tip = nav.iloc[-1] if len(nav) else None
    end_pos = meta.get("end_positions") or {}
    tel_held = {c: float(end_pos.get(c, 0.0)) for c in TEL}
    names_with_lot = sum(1 for v in tel_held.values() if abs(v) >= CHARTER_LOT - 1e-9)
    zero_days = int((nav["tel_board_names"] == 0).sum()) if "tel_board_names" in nav.columns else None
    n = len(nav)
    # Scale band: days while NAV still near starting capital (illustrates 3M board-lot bind).
    near3m = nav[nav["nav"] <= 4_000_000.0] if len(nav) else nav
    return {
        "tip_date": None if tip is None else str(tip["date"]),
        "tip_nav": None if tip is None else float(tip["nav"]),
        "tip_cash": None if tip is None else float(tip["cash"]),
        "tip_cash_weight": None
        if tip is None or float(tip["nav"]) <= 0
        else float(tip["cash"]) / float(tip["nav"]),
        "tip_pre_telecom": None if tip is None else float(tip["pre_telecom"]),
        "tip_tgt_telecom": None if tip is None else float(tip["tgt_telecom"]),
        "tip_tel_positions": tel_held,
        "tip_tel_names_with_board_lot": int(names_with_lot),
        "mean_pre_telecom": float(nav["pre_telecom"].mean()) if len(nav) else None,
        "pct_days_tel_zero_board": None if not n or zero_days is None else zero_days / n,
        "mean_tel_board_names": float(nav["tel_board_names"].mean())
        if "tel_board_names" in nav.columns and len(nav)
        else None,
        "near_3m_band": {
            "n_days": int(len(near3m)),
            "pct_days_tel_zero_board": None
            if len(near3m) == 0 or "tel_board_names" not in near3m.columns
            else float((near3m["tel_board_names"] == 0).mean()),
            "mean_pre_telecom": None
            if len(near3m) == 0
            else float(near3m["pre_telecom"].mean()),
            "mean_cash_weight": None
            if len(near3m) == 0
            else float((near3m["cash"] / near3m["nav"]).mean()),
        },
    }


def run_policy(
    market: pd.DataFrame,
    dividends: pd.DataFrame,
    target: pd.DataFrame,
    regime: pd.Series,
    *,
    policy: str,
    tel_scores: pd.DataFrame | None,
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
        telecom_alloc=policy,
        tel_name_scores=tel_scores,
    )
    win = {w: window_stats(nav, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
    qty = pd.to_numeric(fills["quantity"], errors="coerce") if len(fills) else pd.Series(dtype=float)
    board_ok = bool(len(qty) == 0 or ((qty % CHARTER_LOT == 0) & (qty >= CHARTER_LOT)).all())
    return {
        "id": policy,
        "telecom_alloc": policy,
        "exact_t1_ok": bool(meta.get("exact_t1_ok")),
        "lot_size": int(meta.get("lot_size", CHARTER_LOT)),
        "capital": CHARTER_CAPITAL,
        "n_fills": int(len(fills)),
        "fills_board_lot_ok": board_ok,
        "windows": win,
        "tip": tip_telecom_diagnostics(nav, meta),
        "meta_end": meta.get("end_positions"),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Telecom within-sleeve Stage B (paper only)")
    ap.add_argument(
        "--policies",
        nargs="*",
        default=POLICIES,
        help=f"Subset of {POLICIES}",
    )
    args = ap.parse_args()
    policies = list(args.policies)
    for p in policies:
        if p not in TEL_ALLOC_POLICIES:
            raise SystemExit(f"unknown policy {p}; expected one of {TEL_ALLOC_POLICIES}")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "outputs").mkdir(exist_ok=True)

    # Soft-Frozen live sanity (must remain unchanged).
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.5, 0.95]
    assert soft.SOFT_FROZEN_TEL_LO == 0.03
    assert soft.SOFT_FROZEN_TEL_HI == 0.35
    assert soft.SOFT_FROZEN_ETF_LO == 0.0
    assert float(DEFAULT_CAPITAL) == CHARTER_CAPITAL

    print("loading market + dividends ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _prices, _sleeve, target, regime = e16_features(market)
    tel_scores = build_tel_name_scores(market)

    results: dict[str, dict] = {}
    for i, policy in enumerate(policies, 1):
        print(f"  [{i}/{len(policies)}] {policy} @ 3M/1000 ...", flush=True)
        need_scores = policy in (TEL_ALLOC_TOP1, TEL_ALLOC_TOP2_EQUAL)
        results[policy] = run_policy(
            market,
            dividends,
            target,
            regime,
            policy=policy,
            tel_scores=tel_scores if need_scores else None,
        )
        r = results[policy]
        assert r["exact_t1_ok"], f"{policy} Exact T+1 failed"
        assert r["fills_board_lot_ok"], f"{policy} board-lot fills failed"

    base = results[TEL_ALLOC_EQUAL]
    ranked_rows = []
    for policy, row in results.items():
        if policy == TEL_ALLOC_EQUAL:
            continue
        held = score_vs_base(base["windows"]["heldout_2019_plus"], row["windows"]["heldout_2019_plus"])
        val = score_vs_base(
            base["windows"]["validation_2019_2022"], row["windows"]["validation_2019_2022"]
        )
        oof = score_vs_base(base["windows"]["oof_2011_2018"], row["windows"]["oof_2011_2018"])
        row["scores"] = {
            "heldout_2019_plus": held,
            "validation_2019_2022": val,
            "oof_2011_2018": oof,
        }
        ranked_rows.append(row)

    ranked = sorted(
        ranked_rows,
        key=lambda r: r["scores"]["heldout_2019_plus"]["score"],
        reverse=True,
    )
    top = ranked[:2]
    for r in top:
        sealed = score_vs_base(base["windows"]["sealed_2023_plus"], r["windows"]["sealed_2023_plus"])
        r["scores"]["sealed_2023_plus_REPORT_ONLY"] = sealed
        sealed_mdd_worse_pp = -sealed["mdd_improve_pp"]
        r["fragile_sealed_mdd"] = bool(sealed_mdd_worse_pp > 2.0 + 1e-12)

    best_score = ranked[0]["scores"]["heldout_2019_plus"]["score"] if ranked else None
    stop = best_score is None or best_score <= 0

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "TELECOM_WITHIN_SLEEVE_ALLOC_STAGE_B",
        "status": "STOP_NO_POSITIVE_HELDOUT_SCORE" if stop else "STAGE_B_CANDIDATES_LOCKED",
        "charter": "research/ops/TELECOM_WITHIN_SLEEVE_ALLOC_CHARTER.md",
        "ballot": "ACCEPT telecom within-sleeve charter",
        "live_wire": False,
        "soft_frozen_keep": True,
        "soft_frozen_live_clips": {
            "financial": [soft.SOFT_FROZEN_FIN_LO, soft.SOFT_FROZEN_FIN_HI],
            "telecom": [soft.SOFT_FROZEN_TEL_LO, soft.SOFT_FROZEN_TEL_HI],
            "etf_0050": [soft.SOFT_FROZEN_ETF_LO, soft.SOFT_FROZEN_ETF_HI],
        },
        "execution_context": {
            "capital": CHARTER_CAPITAL,
            "board_lot": CHARTER_LOT,
            "e22_books": "E22_v2s_tw",
            "live_default_capital": float(DEFAULT_CAPITAL),
            "live_e21_equal_split_untouched": True,
        },
        "base_id": TEL_ALLOC_EQUAL,
        "policies": policies,
        "base": base,
        "challengers": {r["id"]: r for r in ranked_rows},
        "top_k_heldout": top,
        "stop_no_positive_heldout_score": stop,
        "objective": "heldout_mdd_improve_pp - 0.5 * abs(cagr_giveback_pp) vs TEL_EQUAL",
        "all_rows_path": "outputs/stage_b_all_policies.json",
    }

    (OUT / "outputs" / "stage_b_all_policies.json").write_text(
        json.dumps({"base_id": TEL_ALLOC_EQUAL, "results": results}, indent=2, default=str) + "\n"
    )
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    RESEARCH.joinpath("TELECOM_WITHIN_SLEEVE_ALLOC_STAGE_B.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    lines = [
        "# Telecom Within-Sleeve Allocation — Stage B",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Ballot: **ACCEPT telecom within-sleeve charter** · Soft-Frozen **KEEP**",
        f"Execution: capital **{CHARTER_CAPITAL:,.0f}** · lot **{CHARTER_LOT}** · `E22_v2s_tw`",
        f"Status: **{payload['status']}**",
        "Live wire: **false** (e21 equal-split untouched)",
        "",
        "## BASE (`TEL_EQUAL`)",
        "",
        f"- held-out MDD `{base['windows']['heldout_2019_plus'].get('max_drawdown')}` · "
        f"CAGR `{base['windows']['heldout_2019_plus'].get('cagr')}`",
        f"- tip TEL weight `{base['tip'].get('tip_pre_telecom')}` · "
        f"names w/ 張 `{base['tip'].get('tip_tel_names_with_board_lot')}` · "
        f"cash w `{base['tip'].get('tip_cash_weight')}`",
        f"- tip positions `{base['tip'].get('tip_tel_positions')}`",
        f"- pct days TEL zero-board `{base['tip'].get('pct_days_tel_zero_board')}` · "
        f"near-3M band `{base['tip'].get('near_3m_band')}`",
        "",
        "## Challengers vs BASE (held-out score; sealed report-only for top ≤2)",
        "",
        "| id | heldout score | MDD↑pp | CAGRΔpp | tip TEL w | tip #names | pct TEL=0 | near3M TEL=0 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in ranked:
        h = r["scores"]["heldout_2019_plus"]
        tip = r["tip"]
        near = tip.get("near_3m_band") or {}
        lines.append(
            f"| `{r['id']}` | {h['score']:.3f} | {h['mdd_improve_pp']:.3f} | "
            f"{h['cagr_giveback_pp']:.3f} | {tip.get('tip_pre_telecom'):.4f} | "
            f"{tip.get('tip_tel_names_with_board_lot')} | "
            f"{tip.get('pct_days_tel_zero_board'):.3f} | "
            f"{near.get('pct_days_tel_zero_board'):.3f} |"
        )
    if top:
        lines += [
            "",
            "## Top ≤2 sealed report-only",
            "",
            "| id | sealed MDD↑pp | fragile (>2pp worse)? | tip positions |",
            "|---|---:|---|---|",
        ]
        for r in top:
            s = r["scores"]["sealed_2023_plus_REPORT_ONLY"]
            lines.append(
                f"| `{r['id']}` | {s['mdd_improve_pp']:.3f} | {r['fragile_sealed_mdd']} | "
                f"`{r['tip'].get('tip_tel_positions')}` |"
            )
    lines += [
        "",
        "## Hard rules",
        "",
        "- Soft-Frozen sleeve clip module untouched",
        "- Sealed not used for selection",
        "- Passing ≠ live within-sleeve cutover (needs later ballot)",
        "",
        f"Repro: `{OUT.relative_to(ROOT)}/`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "STAGE_B.md").write_text(md)
    RESEARCH.joinpath("TELECOM_WITHIN_SLEEVE_ALLOC_STAGE_B.md").write_text(md)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "top": [t["id"] for t in top],
                "best_heldout_score": best_score,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
