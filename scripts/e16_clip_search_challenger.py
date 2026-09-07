#!/usr/bin/env python3
"""Soft-Frozen clip-box search — RESEARCH ONLY (Stage B).

Charter: research/ops/SOFT_FROZEN_CLIP_SEARCH_CHARTER.md
Decision: ACCEPT clip-search charter (2026-09-07)

- Does NOT edit e16_soft_frozen_base live constants.
- Execution: Exact T+1 · E22_v2s_tw · lot_size=1000 · capital=5_000_000
- Stage B default: FIN locked to Soft-Frozen [0.50, 0.95]; search TEL×ETF grid.
- Selection: held-out 2019+ score; sealed 2023+ report-only after lock.
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e16_soft_frozen_base as soft
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, load_market, window_stats
from e50_early_stack_combined_nav import simulate_core
from portfolio_capital import DEFAULT_CAPITAL  # live default; charter overrides
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp
from tw_share_lots import BOARD_LOT

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/clip-search-20260907"
RESEARCH = ROOT / "research/ops"

CHARTER_CAPITAL = 5_000_000.0
CHARTER_LOT = BOARD_LOT  # 1000

# Predeclared search lists (charter). Stage B locks FIN to Soft-Frozen.
FIN_LO_GRID = [0.45, 0.50, 0.55, 0.60]
FIN_HI_GRID = [0.85, 0.90, 0.95]
TEL_LO_GRID = [0.03, 0.05, 0.08, 0.10, 0.12]
TEL_HI_GRID = [0.25, 0.30, 0.35]
ETF_LO_GRID = [0.00, 0.05, 0.08, 0.10]
ETF_HI_GRID = [0.25, 0.30, 0.35]

LIVE_FIN = (float(soft.SOFT_FROZEN_FIN_LO), float(soft.SOFT_FROZEN_FIN_HI))
LIVE_TEL = (float(soft.SOFT_FROZEN_TEL_LO), float(soft.SOFT_FROZEN_TEL_HI))
LIVE_ETF = (float(soft.SOFT_FROZEN_ETF_LO), float(soft.SOFT_FROZEN_ETF_HI))


def apply_clip_box(cand: np.ndarray, lo: np.ndarray, hi: np.ndarray, start: np.ndarray) -> np.ndarray:
    """Same projection as Soft-Frozen, with challenger lo/hi (does not touch live module)."""
    out = np.clip(np.asarray(cand, dtype=float).copy(), lo, hi)
    for _ in range(64):
        s = float(out.sum())
        if s <= 0:
            return start.copy()
        out = out / s
        clipped = np.clip(out, lo, hi)
        if np.allclose(out, clipped, atol=1e-12, rtol=0.0):
            if abs(float(clipped.sum()) - 1.0) <= 1e-10:
                return clipped
        gap = 1.0 - float(clipped.sum())
        free = (clipped > lo + 1e-15) & (clipped < hi - 1e-15)
        if free.any() and abs(gap) > 1e-12:
            clipped = clipped.copy()
            clipped[free] += gap / float(free.sum())
            out = np.clip(clipped, lo, hi)
            continue
        out = clipped.copy()
        if abs(gap) <= 1e-12:
            return out
        if gap > 0:
            can_up = out < hi - 1e-15
            if not can_up.any():
                return start.copy()
            i = int(np.where(can_up)[0][0])
            out[i] = min(hi[i], out[i] + gap)
        else:
            can_down = out > lo + 1e-15
            if not can_down.any():
                return start.copy()
            i = int(np.where(can_down)[0][0])
            out[i] = max(lo[i], out[i] + gap)
    return start.copy()


def build_targets_with_clips(
    *,
    regime: pd.Series,
    score: pd.DataFrame,
    fin_lo: float,
    fin_hi: float,
    tel_lo: float,
    tel_hi: float,
    etf_lo: float,
    etf_hi: float,
) -> pd.DataFrame:
    """Causal E16 router with challenger clip box (priors/scores match Soft-Frozen)."""
    lo = np.array([fin_lo, tel_lo, etf_lo], dtype=float)
    hi = np.array([fin_hi, tel_hi, etf_hi], dtype=float)
    start = apply_clip_box((lo + hi) / 2.0, lo, hi, soft.START_WEIGHTS.copy())
    out = []
    cur = start.copy()
    for i, _dt in enumerate(score.index):
        pri = soft.REGIME_PRIORS[str(regime.iloc[i])]
        cand = np.maximum(pri + 0.10 * np.clip(score.iloc[i].to_numpy(), -2.0, 2.0), 0.0)
        cand = apply_clip_box(cand, lo, hi, start)
        desired = soft.BLEND_OLD * cur + soft.BLEND_NEW * cand
        desired = apply_clip_box(desired, lo, hi, start)
        if float(np.abs(desired - cur).sum()) >= soft.REBALANCE_L1_MIN:
            cur = desired
        out.append(cur.copy())
    return pd.DataFrame(out, index=score.index, columns=["Financial", "Telecom", "0050"])


def feasible(fin_lo, fin_hi, tel_lo, tel_hi, etf_lo, etf_hi) -> bool:
    if fin_hi - fin_lo < 0.05 - 1e-12:
        return False
    if tel_hi - tel_lo < 0.05 - 1e-12:
        return False
    if etf_hi - etf_lo < 0.05 - 1e-12:
        return False
    if fin_lo + tel_lo + etf_lo > 0.95 + 1e-12:
        return False
    return True


def is_live_tuple(fin_lo, fin_hi, tel_lo, tel_hi, etf_lo, etf_hi) -> bool:
    return (
        abs(fin_lo - LIVE_FIN[0]) < 1e-12
        and abs(fin_hi - LIVE_FIN[1]) < 1e-12
        and abs(tel_lo - LIVE_TEL[0]) < 1e-12
        and abs(tel_hi - LIVE_TEL[1]) < 1e-12
        and abs(etf_lo - LIVE_ETF[0]) < 1e-12
        and abs(etf_hi - LIVE_ETF[1]) < 1e-12
    )


def cand_id(fin_lo, fin_hi, tel_lo, tel_hi, etf_lo, etf_hi) -> str:
    return (
        f"CLIP_SEARCH_F{fin_lo:.2f}-{fin_hi:.2f}"
        f"_T{tel_lo:.2f}-{tel_hi:.2f}"
        f"_E{etf_lo:.2f}-{etf_hi:.2f}"
    )


def score_row(base_stats: dict, chal_stats: dict) -> dict:
    mdd_pp = mdd_delta_pp(base_stats.get("max_drawdown"), chal_stats.get("max_drawdown"))
    cagr_pp = cagr_delta_pp(
        base_stats.get("cagr"), chal_stats.get("cagr"), missing_as_zero=True
    )
    # charter: MDD_improve_pp − 0.5 × |CAGR_giveback_pp|
    # cagr_delta_pp = base − other; positive ⇒ challenger CAGR lower ⇒ giveback
    giveback = abs(float(cagr_pp)) if cagr_pp is not None else 9.0
    score = float(mdd_pp) - 0.5 * giveback
    return {
        "mdd_improve_pp": float(mdd_pp),
        "cagr_giveback_pp": float(cagr_pp) if cagr_pp is not None else None,
        "score": score,
    }


def enumerate_grid(*, lock_fin_soft_frozen: bool) -> list[tuple]:
    fin_pairs = (
        [LIVE_FIN]
        if lock_fin_soft_frozen
        else [(flo, fhi) for flo in FIN_LO_GRID for fhi in FIN_HI_GRID]
    )
    # Stage B default (FIN locked): search floors with Soft-Frozen highs held.
    # Full hi grid available via --expand-fin (also expands FIN).
    tel_his = [LIVE_TEL[1]] if lock_fin_soft_frozen else TEL_HI_GRID
    etf_his = [LIVE_ETF[1]] if lock_fin_soft_frozen else ETF_HI_GRID
    rows = []
    for (flo, fhi), tlo, thi, elo, ehi in itertools.product(
        fin_pairs, TEL_LO_GRID, tel_his, ETF_LO_GRID, etf_his
    ):
        if not feasible(flo, fhi, tlo, thi, elo, ehi):
            continue
        rows.append((flo, fhi, tlo, thi, elo, ehi))
    return rows


def run_one(market, dividends, clips, *, regime, score) -> dict:
    flo, fhi, tlo, thi, elo, ehi = clips
    target = build_targets_with_clips(
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
        capital=CHARTER_CAPITAL,
        lot_size=CHARTER_LOT,
    )
    win = {w: window_stats(nav, a, b) for w, (a, b) in WINDOWS_STANDARD.items()}
    qty = pd.to_numeric(fills["quantity"], errors="coerce") if len(fills) else pd.Series(dtype=float)
    board_ok = bool(len(qty) == 0 or ((qty % CHARTER_LOT == 0) & (qty >= CHARTER_LOT)).all())
    return {
        "id": cand_id(*clips),
        "clips": {
            "fin": [flo, fhi],
            "tel": [tlo, thi],
            "etf": [elo, ehi],
        },
        "is_live_soft_frozen": is_live_tuple(*clips),
        "exact_t1_ok": bool(meta.get("exact_t1_ok")),
        "lot_size": int(meta.get("lot_size", CHARTER_LOT)),
        "capital": CHARTER_CAPITAL,
        "n_fills": int(len(fills)),
        "fills_board_lot_ok": board_ok,
        "mean_target": {
            "Financial": float(target["Financial"].mean()),
            "Telecom": float(target["Telecom"].mean()),
            "0050": float(target["0050"].mean()),
        },
        "windows": win,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Clip-search Stage B (paper only)")
    ap.add_argument(
        "--expand-fin",
        action="store_true",
        help="Also search FIN lo/hi grid (full charter cartesian; slow).",
    )
    ap.add_argument("--top-k", type=int, default=3)
    ap.add_argument("--limit", type=int, default=0, help="Debug: cap challenger count (0=all).")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "outputs").mkdir(exist_ok=True)

    print("loading market + dividends ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _prices, _sleeve, _live_tgt, regime, score = soft.build_soft_frozen_targets(market)

    # Soft-Frozen live module sanity (must remain unchanged).
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.5, 0.95]
    assert soft.SOFT_FROZEN_TEL_LO == 0.03
    assert soft.SOFT_FROZEN_ETF_LO == 0.0

    print("BASE Soft-Frozen control @ 5M/1000 ...", flush=True)
    base = run_one(
        market, dividends, (*LIVE_FIN, *LIVE_TEL, *LIVE_ETF), regime=regime, score=score
    )
    base["id"] = "BASE_SOFT_FROZEN"
    assert base["exact_t1_ok"] and base["fills_board_lot_ok"]

    grid = enumerate_grid(lock_fin_soft_frozen=not args.expand_fin)
    # Exclude exact live tuple from challenger winner pool (still run as control only).
    chal_grid = [g for g in grid if not is_live_tuple(*g)]
    if args.limit > 0:
        chal_grid = chal_grid[: args.limit]
    print(
        f"Stage B challengers: {len(chal_grid)} "
        f"(lock_fin={not args.expand_fin}; live DEFAULT_CAPITAL={DEFAULT_CAPITAL})",
        flush=True,
    )

    rows = []
    for i, clips in enumerate(chal_grid, 1):
        cid = cand_id(*clips)
        print(f"  [{i}/{len(chal_grid)}] {cid}", flush=True)
        try:
            row = run_one(market, dividends, clips, regime=regime, score=score)
        except Exception as exc:  # noqa: BLE001 — research harness continues
            rows.append({"id": cid, "error": str(exc), "clips": list(clips)})
            continue
        held = score_row(base["windows"]["heldout_2019_plus"], row["windows"]["heldout_2019_plus"])
        val = score_row(
            base["windows"]["validation_2019_2022"], row["windows"]["validation_2019_2022"]
        )
        oof = score_row(base["windows"]["oof_2011_2018"], row["windows"]["oof_2011_2018"])
        row["scores"] = {
            "heldout_2019_plus": held,
            "validation_2019_2022": val,
            "oof_2011_2018": oof,
            # sealed intentionally NOT used for selection
        }
        rows.append(row)

    ranked = sorted(
        [r for r in rows if "scores" in r and r.get("exact_t1_ok")],
        key=lambda r: r["scores"]["heldout_2019_plus"]["score"],
        reverse=True,
    )
    top = ranked[: max(1, args.top_k)]
    for r in top:
        # Sealed report after lock only
        sealed = score_row(base["windows"]["sealed_2023_plus"], r["windows"]["sealed_2023_plus"])
        r["scores"]["sealed_2023_plus_REPORT_ONLY"] = sealed
        sealed_mdd_worse_pp = -sealed["mdd_improve_pp"]  # positive if worse
        r["fragile_sealed_mdd"] = bool(sealed_mdd_worse_pp > 2.0 + 1e-12)

    best_score = ranked[0]["scores"]["heldout_2019_plus"]["score"] if ranked else None
    stop = best_score is None or best_score <= 0

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "SOFT_FROZEN_CLIP_SEARCH_STAGE_B",
        "status": "STOP_NO_POSITIVE_HELDOUT_SCORE" if stop else "STAGE_B_CANDIDATES_LOCKED",
        "charter": "research/ops/SOFT_FROZEN_CLIP_SEARCH_CHARTER.md",
        "ballot": "ACCEPT clip-search charter 2026-09-07",
        "live_wire": False,
        "soft_frozen_keep": True,
        "soft_frozen_live_clips": {
            "financial": list(LIVE_FIN),
            "telecom": list(LIVE_TEL),
            "etf_0050": list(LIVE_ETF),
        },
        "execution_context": {
            "capital": CHARTER_CAPITAL,
            "board_lot": CHARTER_LOT,
            "e22_books": "E22_v2s_tw",
            "live_default_capital_untouched": float(DEFAULT_CAPITAL),
        },
        "stage_b_mode": (
            "fin_locked_floors_hi_soft_frozen" if not args.expand_fin else "full_charter_grid"
        ),
        "n_challengers_attempted": len(chal_grid),
        "n_challengers_ok": len(ranked),
        "base": base,
        "top_k_heldout": top,
        "stop_no_positive_heldout_score": stop,
        "objective": "heldout_mdd_improve_pp - 0.5 * abs(cagr_giveback_pp)",
        "all_rows_path": "outputs/stage_b_all_candidates.json",
    }

    (OUT / "outputs" / "stage_b_all_candidates.json").write_text(
        json.dumps({"base_id": base["id"], "rows": rows}, indent=2) + "\n"
    )
    (OUT / "summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    RESEARCH.joinpath("SOFT_FROZEN_CLIP_SEARCH_STAGE_B.json").write_text(
        json.dumps(payload, indent=2) + "\n"
    )

    lines = [
        "# Soft-Frozen Clip Search — Stage B",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Ballot: **ACCEPT clip-search charter** · Soft-Frozen **KEEP**",
        f"Execution: capital **{CHARTER_CAPITAL:,.0f}** · lot **{CHARTER_LOT}** · `E22_v2s_tw`",
        f"Mode: `{payload['stage_b_mode']}` · challengers ok **{payload['n_challengers_ok']}**",
        f"Status: **{payload['status']}**",
        "",
        "## BASE (Soft-Frozen control)",
        "",
        f"- held-out MDD `{base['windows']['heldout_2019_plus'].get('max_drawdown')}` · "
        f"CAGR `{base['windows']['heldout_2019_plus'].get('cagr')}`",
        f"- sealed MDD `{base['windows']['sealed_2023_plus'].get('max_drawdown')}`",
        "",
        "## Top-K by held-out score (sealed report-only)",
        "",
        "| id | heldout score | MDD↑pp | CAGRΔpp | sealed MDD↑pp | fragile? |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for r in top:
        h = r["scores"]["heldout_2019_plus"]
        s = r["scores"]["sealed_2023_plus_REPORT_ONLY"]
        lines.append(
            f"| `{r['id']}` | {h['score']:.3f} | {h['mdd_improve_pp']:.3f} | "
            f"{h['cagr_giveback_pp']:.3f} | {s['mdd_improve_pp']:.3f} | {r['fragile_sealed_mdd']} |"
        )
    lines += [
        "",
        "## Hard rules",
        "",
        "- Soft-Frozen live module untouched",
        "- Sealed not used for selection",
        "- Passing ≠ Class D Soft-Frozen flip",
        "",
        f"Repro: `{OUT.relative_to(ROOT)}/`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "STAGE_B.md").write_text(md)
    RESEARCH.joinpath("SOFT_FROZEN_CLIP_SEARCH_STAGE_B.md").write_text(md)
    print(json.dumps({"status": payload["status"], "top": [t["id"] for t in top]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
