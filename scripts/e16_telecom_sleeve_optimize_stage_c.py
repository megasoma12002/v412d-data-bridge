#!/usr/bin/env python3
"""Telecom within-sleeve optimization — RESEARCH Stage C.

Ballot: human 「電信這條再研究一下怎麼優化以及各項數據是否有變好」

- Soft-Frozen KEEP · live wire NOT auto-flipped by this screen
- FIN held at FIN_EQUAL (isolate Telecom)
- Primary exec: capital 500M · lot 1000 · Exact T+1 · E22_v2s_tw
- Also report 3M sensitivity for fill / score context
- Compare vs TEL_EQUAL and vs live-intent TEL_MIN_LOT_PACK
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e16_soft_frozen_base as soft
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, load_market, window_stats
from e50_early_stack_combined_nav import TEL, e16_features, simulate_core
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp
from tw_share_lots import BOARD_LOT
from within_sleeve_alloc import (
    FIN_EQUAL,
    TEL_ALLOC_POLICIES,
    TEL_DIVERSIFY_PACK,
    TEL_EQUAL,
    TEL_MIN_LOT_PACK,
    TEL_SCORE_LOT_PACK,
    TEL_TOP1,
    TEL_TOP2_EQUAL,
    build_name_scores,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/telecom-sleeve-optimize-20260908"
RESEARCH = ROOT / "research/ops"

CAPITAL_PRIMARY = 500_000_000.0
CAPITAL_SENS = 3_000_000.0
LOT = BOARD_LOT

STAGE_C_POLICIES = [
    TEL_EQUAL,
    TEL_MIN_LOT_PACK,
    TEL_SCORE_LOT_PACK,
    TEL_DIVERSIFY_PACK,
    TEL_TOP2_EQUAL,
    TEL_TOP1,
]


def score_vs(base: dict, chal: dict) -> dict:
    mdd_pp = mdd_delta_pp(base.get("max_drawdown"), chal.get("max_drawdown"))
    cagr_pp = cagr_delta_pp(base.get("cagr"), chal.get("cagr"), missing_as_zero=True)
    giveback = abs(float(cagr_pp)) if cagr_pp is not None else 9.0
    return {
        "mdd_improve_pp": float(mdd_pp),
        "cagr_delta_pp_base_minus_chal": float(cagr_pp) if cagr_pp is not None else None,
        "cagr_giveback_pp": giveback,
        "score": float(mdd_pp) - 0.5 * giveback,
        "cagr": chal.get("cagr"),
        "max_drawdown": chal.get("max_drawdown"),
        "utility": chal.get("utility"),
        "vol": chal.get("vol"),
    }


def hhi_from_pos(pos: dict, codes) -> float:
    vals = [max(0.0, float(pos.get(c, 0.0))) for c in codes]
    s = sum(vals)
    if s <= 0:
        return 0.0
    w = [v / s for v in vals]
    return float(sum(x * x for x in w))


def tip_diag(nav: pd.DataFrame, meta: dict) -> dict:
    tip = nav.iloc[-1]
    end_pos = meta.get("end_positions") or {}
    tel_pos = {c: float(end_pos.get(c, 0.0)) for c in TEL}
    n_names = sum(1 for v in tel_pos.values() if abs(v) >= LOT - 1e-9)
    zero = float((nav["tel_board_names"] == 0).mean()) if "tel_board_names" in nav.columns else None
    near = nav[nav["nav"] <= 4_000_000.0] if len(nav) else nav
    return {
        "tip_date": str(tip["date"]),
        "tip_nav": float(tip["nav"]),
        "tip_cash_weight": float(tip["cash"]) / float(tip["nav"]) if float(tip["nav"]) else None,
        "tip_pre_telecom": float(tip["pre_telecom"]),
        "tip_pre_financial": float(tip["pre_financial"]),
        "tip_tel_positions": tel_pos,
        "tip_tel_names": int(n_names),
        "tip_tel_hhi": hhi_from_pos(tel_pos, TEL),
        "mean_pre_telecom": float(nav["pre_telecom"].mean()),
        "pct_days_tel_zero": zero,
        "near3m_pct_tel_zero": None
        if len(near) == 0 or "tel_board_names" not in near.columns
        else float((near["tel_board_names"] == 0).mean()),
        "n_fills": int(meta.get("n_fills", 0)),
    }


def run_one(market, dividends, target, regime, tel_scores, *, policy: str, capital: float) -> dict:
    need = policy in (TEL_TOP1, TEL_TOP2_EQUAL, TEL_SCORE_LOT_PACK)
    nav, fills, meta = simulate_core(
        market,
        target,
        regime,
        dividends,
        apply_e22=True,
        apply_stock_div=True,
        capital=capital,
        lot_size=LOT,
        financial_alloc=FIN_EQUAL,
        telecom_alloc=policy,
        tel_name_scores=tel_scores if need else None,
    )
    win = {w: window_stats(nav, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
    qty = pd.to_numeric(fills["quantity"], errors="coerce") if len(fills) else pd.Series(dtype=float)
    board_ok = bool(len(qty) == 0 or ((qty % LOT == 0) & (qty >= LOT)).all())
    return {
        "id": policy,
        "capital": capital,
        "exact_t1_ok": bool(meta.get("exact_t1_ok")),
        "fills_board_lot_ok": board_ok,
        "windows": win,
        "tip": tip_diag(nav, meta),
    }


def enrich(base_row: dict, row: dict) -> dict:
    out = dict(row)
    out["scores"] = {
        "heldout_2019_plus": score_vs(
            base_row["windows"]["heldout_2019_plus"], row["windows"]["heldout_2019_plus"]
        ),
        "validation_2019_2022": score_vs(
            base_row["windows"]["validation_2019_2022"], row["windows"]["validation_2019_2022"]
        ),
        "oof_2011_2018": score_vs(
            base_row["windows"]["oof_2011_2018"], row["windows"]["oof_2011_2018"]
        ),
        "sealed_2023_plus_REPORT_ONLY": score_vs(
            base_row["windows"]["sealed_2023_plus"], row["windows"]["sealed_2023_plus"]
        ),
        "full": score_vs(base_row["windows"]["full"], row["windows"]["full"]),
    }
    # vs live-intent MIN_LOT_PACK filled later
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-3m", action="store_true")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "outputs").mkdir(exist_ok=True)

    assert soft.SOFT_FROZEN_FIN_CLIP == [0.5, 0.95]
    assert soft.SOFT_FROZEN_TEL_LO == 0.03

    print("loading ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, _s, target, regime = e16_features(market)
    tel_scores = build_name_scores(market, TEL)

    def run_capital(capital: float) -> dict:
        print(f"== capital {capital:,.0f} ==", flush=True)
        rows = {}
        for i, pol in enumerate(STAGE_C_POLICIES, 1):
            print(f"  [{i}/{len(STAGE_C_POLICIES)}] {pol}", flush=True)
            r = run_one(market, dividends, target, regime, tel_scores, policy=pol, capital=capital)
            assert r["exact_t1_ok"] and r["fills_board_lot_ok"], pol
            rows[pol] = r
        base = rows[TEL_EQUAL]
        minlot = rows[TEL_MIN_LOT_PACK]
        enriched = {}
        for pol, r in rows.items():
            e = enrich(base, r)
            e["vs_min_lot_pack"] = {
                "heldout_2019_plus": score_vs(
                    minlot["windows"]["heldout_2019_plus"], r["windows"]["heldout_2019_plus"]
                ),
                "sealed_2023_plus_REPORT_ONLY": score_vs(
                    minlot["windows"]["sealed_2023_plus"], r["windows"]["sealed_2023_plus"]
                ),
            }
            enriched[pol] = e
        ranked = sorted(
            [e for p, e in enriched.items() if p != TEL_EQUAL],
            key=lambda r: r["scores"]["heldout_2019_plus"]["score"],
            reverse=True,
        )
        best = ranked[0]["scores"]["heldout_2019_plus"]["score"] if ranked else None
        # improve vs EQUAL?
        beat_equal = [r["id"] for r in ranked if r["scores"]["heldout_2019_plus"]["score"] > 0]
        # improve vs MIN_LOT?
        beat_min = [
            r["id"]
            for r in ranked
            if r["id"] != TEL_MIN_LOT_PACK and r["vs_min_lot_pack"]["heldout_2019_plus"]["score"] > 0
        ]
        return {
            "capital": capital,
            "base_id": TEL_EQUAL,
            "live_intent_id": TEL_MIN_LOT_PACK,
            "rows": enriched,
            "ranked_vs_equal": ranked,
            "beat_equal_heldout": beat_equal,
            "beat_min_lot_heldout": beat_min,
            "best_heldout_score_vs_equal": best,
            "status": (
                "IMPROVE_VS_EQUAL"
                if beat_equal
                else "NO_IMPROVE_VS_EQUAL"
            ),
        }

    primary = run_capital(CAPITAL_PRIMARY)
    sens = None if args.skip_3m else run_capital(CAPITAL_SENS)

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "TELECOM_WITHIN_SLEEVE_OPTIMIZE_STAGE_C",
        "ballot": "電信這條再研究一下怎麼優化以及各項數據是否有變好",
        "live_wire": False,
        "soft_frozen_keep": True,
        "note": (
            "Paper optimization screen. Does not auto-change live TEL_MIN_LOT_PACK "
            "cutover (#126). Soft-Frozen clips KEEP."
        ),
        "policies": STAGE_C_POLICIES,
        "primary_500m": primary,
        "sensitivity_3m": sens,
    }

    (OUT / "summary.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")
    RESEARCH.joinpath("TELECOM_WITHIN_SLEEVE_OPTIMIZE_STAGE_C.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    def table_block(block: dict, title: str) -> list[str]:
        lines = [
            f"## {title}",
            "",
            f"Status vs EQUAL: **{block['status']}** · beat EQUAL: `{block['beat_equal_heldout']}` · "
            f"beat MIN_LOT: `{block['beat_min_lot_heldout']}`",
            "",
            "| id | heldout score vs EQ | MDD↑pp | CAGRΔpp | sealed MDD↑pp | tip TEL w | #names | HHI | pct TEL=0 | fills |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
        # EQUAL first
        eq = block["rows"][TEL_EQUAL]
        h = eq["scores"]["heldout_2019_plus"]
        s = eq["scores"]["sealed_2023_plus_REPORT_ONLY"]
        tip = eq["tip"]
        lines.append(
            f"| `{TEL_EQUAL}` | 0.000 | 0.000 | 0.000 | 0.000 | "
            f"{tip['tip_pre_telecom']:.4f} | {tip['tip_tel_names']} | {tip['tip_tel_hhi']:.3f} | "
            f"{tip['pct_days_tel_zero']:.3f} | {tip['n_fills']} |"
        )
        for r in block["ranked_vs_equal"]:
            h = r["scores"]["heldout_2019_plus"]
            s = r["scores"]["sealed_2023_plus_REPORT_ONLY"]
            tip = r["tip"]
            lines.append(
                f"| `{r['id']}` | {h['score']:.3f} | {h['mdd_improve_pp']:.3f} | "
                f"{h['cagr_delta_pp_base_minus_chal']:.3f} | {s['mdd_improve_pp']:.3f} | "
                f"{tip['tip_pre_telecom']:.4f} | {tip['tip_tel_names']} | {tip['tip_tel_hhi']:.3f} | "
                f"{tip['pct_days_tel_zero']:.3f} | {tip['n_fills']} |"
            )
        lines += [
            "",
            "### vs live-intent `TEL_MIN_LOT_PACK` (held-out)",
            "",
            "| id | score vs MIN_LOT | MDD↑pp | CAGRΔpp | tip positions |",
            "|---|---:|---:|---:|---|",
        ]
        for pol in STAGE_C_POLICIES:
            if pol == TEL_MIN_LOT_PACK:
                continue
            r = block["rows"][pol]
            v = r["vs_min_lot_pack"]["heldout_2019_plus"]
            lines.append(
                f"| `{pol}` | {v['score']:.3f} | {v['mdd_improve_pp']:.3f} | "
                f"{v['cagr_delta_pp_base_minus_chal']:.3f} | `{r['tip']['tip_tel_positions']}` |"
            )
        lines.append("")
        return lines

    md = [
        "# Telecom Within-Sleeve Optimize — Stage C",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Ballot: **電信優化再研究** · Soft-Frozen **KEEP** · live wire **false** (no auto flip of #126)",
        "",
        "New challengers: `TEL_SCORE_LOT_PACK` (score-first pack) · `TEL_DIVERSIFY_PACK` (1張覆蓋後餘額均分)",
        "",
    ]
    md += table_block(primary, "Primary @ 500M")
    if sens:
        md += table_block(sens, "Sensitivity @ 3M")
    md += [
        "## Verdict guide",
        "",
        "- held-out score > 0 vs `TEL_EQUAL` ⇒ metric improve on charter objective",
        "- HHI↓ / #names↑ ⇒ less concentration than cheapest-pack",
        "- Passing ≠ Soft-Frozen flip ≠ auto live cutover change",
        "",
        f"Repro: `{OUT.relative_to(ROOT)}/`",
        "",
    ]
    text = "\n".join(md)
    (OUT / "STAGE_C.md").write_text(text)
    RESEARCH.joinpath("TELECOM_WITHIN_SLEEVE_OPTIMIZE_STAGE_C.md").write_text(text)
    print(
        json.dumps(
            {
                "primary_status": primary["status"],
                "beat_equal": primary["beat_equal_heldout"],
                "beat_min_lot": primary["beat_min_lot_heldout"],
                "sens_status": None if not sens else sens["status"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
