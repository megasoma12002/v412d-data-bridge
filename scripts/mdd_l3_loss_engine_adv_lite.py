#!/usr/bin/env python3
"""L3 adversarial-lite on locked OOF winner (RESEARCH_ONLY).

Locked from OOF: L3_MILD_35_60 (FIN clip [0.35, 0.60], no gross scale).
Flagless concentration cut → placebo uses null Financial clips [0.50, U],
U~Unif(0.55, 0.95) rather than flag scramble.

Gates:
  - Placebo P(MDD improve >= locked) < 0.50
  - Year-split: OOF MDD improve in >= 2 calendar years
  - Late-bull (2017-2018) CAGR giveback remains <= 1.5pp

No held-out selection. No live-wire. No L1/L2/L3 cut retune.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from research_metric_helpers import mdd_delta_pp, cagr_delta_pp
import e22_dividend_accounting as e22div
import mdd_l1_loss_engine_oof as oof

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/mdd-loss-engine/l3_adv_lite"
RESEARCH = ROOT / "research/gaps"

LOCKED_ID = "L3_MILD_35_60"
LOCKED_FIN_LO, LOCKED_FIN_HI = 0.35, 0.60
OOF_START, OOF_END = date(2012, 12, 4), date(2018, 12, 31)
LATE_BULL_START, LATE_BULL_END = date(2017, 1, 1), date(2018, 12, 31)
N_PLACEBO = 24
PLACEBO_SEED = 20260905
PLACEBO_P_MAX = 0.50
LATE_BULL_CAGR_GIVEBACK_MAX_PP = 1.5


def year_mdd(nav: pd.DataFrame, year: int) -> float | None:
    d = nav.copy()
    d["date"] = pd.to_datetime(d["date"])
    g = d[d["date"].dt.year == year].reset_index(drop=True)
    if len(g) < 30:
        return None
    g = g.copy()
    g["nav"] = g["nav"] / float(g["nav"].iloc[0])
    return float(oof.nav_stats(g)["max_drawdown"])


def main() -> None:
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)

    oof_summary = json.loads((RESEARCH / "MDD_L3_OOF_SUMMARY.json").read_text())
    if oof_summary.get("label") != "OOF_L3_READY_FOR_ADV_LITE":
        raise SystemExit(f"OOF not ready: {oof_summary.get('label')}")
    if oof_summary.get("locked_winner") != LOCKED_ID:
        raise SystemExit(f"locked mismatch: {oof_summary.get('locked_winner')}")
    locked_row = oof_summary["winner_row"]
    locked_improve = float(locked_row["mdd_improve_pp"]) / 100.0

    print("simulating BASE + locked L3_MILD_35_60 ...", flush=True)
    market = oof.load_market()
    dividends = (
        pd.read_csv(oof.DIV_PATH, dtype={"code": str}) if oof.DIV_PATH.exists() else pd.DataFrame()
    )
    _p, _s, base_target, base_regime = oof.e16_features(market)
    _p2, _s2, locked_target, locked_regime = oof.e16_features_fin_cap(
        market, LOCKED_FIN_LO, LOCKED_FIN_HI
    )

    nav_b, _fb, meta_b = oof.simulate_core(
        market,
        base_target,
        base_regime,
        dividends,
        apply_e22=True,
        e22_version=e22div.E22_V2S,
        apply_stock_div=True,
        e45_exposure=None,
    )
    nav_l, _fl, meta_l = oof.simulate_core(
        market,
        locked_target,
        locked_regime,
        dividends,
        apply_e22=True,
        e22_version=e22div.E22_V2S,
        apply_stock_div=True,
        e45_exposure=None,
    )
    if not (meta_b.get("exact_t1_ok") and meta_l.get("exact_t1_ok")):
        raise SystemExit("exact T+1 failed on BASE/locked")

    base_oof = oof.window_nav_stats(nav_b, OOF_START, OOF_END)
    locked_oof = oof.window_nav_stats(nav_l, OOF_START, OOF_END)
    base_late = oof.window_nav_stats(nav_b, LATE_BULL_START, LATE_BULL_END)
    locked_late = oof.window_nav_stats(nav_l, LATE_BULL_START, LATE_BULL_END)

    base_oof_mdd = float(base_oof["max_drawdown"])
    base_oof_cagr = float(base_oof["cagr"])
    late_gb_pp = (float(base_late["cagr"]) - float(locked_late["cagr"])) * 100.0
    late_bull_ok = late_gb_pp <= LATE_BULL_CAGR_GIVEBACK_MAX_PP

    year_rows = []
    for y in range(OOF_START.year, OOF_END.year + 1):
        mb, ml = year_mdd(nav_b, y), year_mdd(nav_l, y)
        if mb is None or ml is None:
            continue
        year_rows.append(
            {
                "year": y,
                "base_mdd": mb,
                "locked_mdd": ml,
                "mdd_improve_pp": (abs(mb) - abs(ml)) * 100.0,
            }
        )
    positive_years = [r for r in year_rows if r["mdd_improve_pp"] > 0]
    year_split_ok = len(positive_years) >= 2

    print(f"running {N_PLACEBO} placebo null Financial clips ...", flush=True)
    rng = np.random.default_rng(PLACEBO_SEED)
    placebo_rows = []
    beat = 0
    for i in range(N_PLACEBO):
        fin_hi = float(rng.uniform(0.55, 0.95))
        _px, _sl, tgt, reg = oof.e16_features_fin_cap(market, 0.50, fin_hi)
        nav_p, _fp, meta_p = oof.simulate_core(
            market,
            tgt,
            reg,
            dividends,
            apply_e22=True,
            e22_version=e22div.E22_V2S,
            apply_stock_div=True,
            e45_exposure=None,
        )
        if not meta_p.get("exact_t1_ok"):
            raise SystemExit(f"placebo {i} failed exact T+1")
        st = oof.window_nav_stats(nav_p, OOF_START, OOF_END)
        improve = mdd_delta_pp(base_oof_mdd, st["max_drawdown"]) / 100.0
        _cgb = cagr_delta_pp(base_oof_cagr, st["cagr"], missing_as_zero=True)
        cagr_gb = 0.0 if _cgb is None else _cgb / 100.0
        ge_locked = improve + 1e-12 >= locked_improve
        if ge_locked:
            beat += 1
        placebo_rows.append(
            {
                "placebo_i": i,
                "fin_lo": 0.50,
                "fin_hi": fin_hi,
                "oof_cagr": st["cagr"],
                "oof_mdd": st["max_drawdown"],
                "mdd_improve_pp": improve * 100.0,
                "cagr_giveback_pp": cagr_gb * 100.0,
                "ge_locked_improve": ge_locked,
            }
        )
        print(
            f"  placebo {i:02d}: fin_hi={fin_hi:.3f} MDDΔ={improve*100:.2f}pp ge_locked={ge_locked}",
            flush=True,
        )

    p_ge = beat / float(N_PLACEBO)
    placebo_ok = p_ge < PLACEBO_P_MAX
    adv_pass = bool(placebo_ok and year_split_ok and late_bull_ok)
    decision = "ADV_LITE_L3_READY_FOR_HELDOUT" if adv_pass else "STOP_L3_ADV_LITE"

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": decision,
        "live_wire": False,
        "research_only": True,
        "retune_allowed": False,
        "l1_retune_forbidden": True,
        "l2_reopen_forbidden": True,
        "soft_frozen_live_clip": [0.50, 0.95],
        "locked_id": LOCKED_ID,
        "locked_params": {"fin_lo": LOCKED_FIN_LO, "fin_hi": LOCKED_FIN_HI},
        "locked_from_oof": {
            "mdd_improve_pp": locked_row["mdd_improve_pp"],
            "cagr_giveback_pp": locked_row["cagr_giveback_pp"],
            "late_bull_cagr_giveback_pp": locked_row["late_bull_cagr_giveback_pp"],
        },
        "recomputed_oof": {
            "base_cagr": base_oof["cagr"],
            "base_mdd": base_oof["max_drawdown"],
            "locked_cagr": locked_oof["cagr"],
            "locked_mdd": locked_oof["max_drawdown"],
            "mdd_improve_pp": (abs(base_oof_mdd) - abs(float(locked_oof["max_drawdown"]))) * 100.0,
            "cagr_giveback_pp": (base_oof_cagr - float(locked_oof["cagr"])) * 100.0,
            "late_bull_cagr_giveback_pp": late_gb_pp,
            "exact_t1_base": bool(meta_b.get("exact_t1_ok")),
            "exact_t1_locked": bool(meta_l.get("exact_t1_ok")),
        },
        "placebo": {
            "type": "null_fin_clip_hi_uniform_0.55_0.95",
            "n": N_PLACEBO,
            "seed": PLACEBO_SEED,
            "p_mdd_improve_ge_locked": p_ge,
            "p_max": PLACEBO_P_MAX,
            "n_beat_locked": beat,
            "ok": placebo_ok,
            "rows": placebo_rows,
        },
        "year_split": {
            "ok": year_split_ok,
            "n_positive_years": len(positive_years),
            "years": year_rows,
        },
        "late_bull_check": {
            "ok": late_bull_ok,
            "cagr_giveback_pp": late_gb_pp,
            "max_pp": LATE_BULL_CAGR_GIVEBACK_MAX_PP,
            "window": {"start": str(LATE_BULL_START), "end": str(LATE_BULL_END)},
        },
        "adv_pass": adv_pass,
        "next_if_pass": "one held-out (val 2019-2022 + sealed 2023+); dual paper only; no live-wire",
        "next_if_stop": "keep BASE; do not retune L3; new charter required",
    }

    (OUT / "reports" / "l3_adv_lite_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (RESEARCH / "MDD_L3_ADV_LITE_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n")
    pd.DataFrame(placebo_rows).to_csv(OUT / "outputs" / "l3_adv_lite_placebos.csv", index=False)
    pd.DataFrame(year_rows).to_csv(OUT / "outputs" / "l3_adv_lite_year_split.csv", index=False)

    lines = [
        "# L3 MDD Sealed-CAGR — Adversarial-lite",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        "Status: **RESEARCH_ONLY** — no live-wire, no Soft-Frozen edit, no held-out selection.",
        "Parents: L1/L2 STOPPED — cut retune forbidden.",
        "",
        f"## Decision: `{decision}`",
        "",
        f"- Locked: **{LOCKED_ID}** (FIN clip [{LOCKED_FIN_LO:.2f}, {LOCKED_FIN_HI:.2f}])",
        f"- Locked OOF MDD improve: **{locked_row['mdd_improve_pp']:.2f} pp**",
        f"- Placebo P(MDD≥locked) = **{p_ge:.3f}** (gate < {PLACEBO_P_MAX:.2f}; null fin_hi U[0.55,0.95])",
        f"- Year-split OK: **{year_split_ok}** (positive years={len(positive_years)})",
        f"- Late-bull CAGR giveback: **{late_gb_pp:.3f} pp** (gate ≤ {LATE_BULL_CAGR_GIVEBACK_MAX_PP})",
        "",
        "## Year-split",
        "",
        "| Year | BASE MDD | Locked MDD | Improve pp |",
        "|---:|---:|---:|---:|",
    ]
    for r in year_rows:
        lines.append(
            f"| {r['year']} | {r['base_mdd']:.2%} | {r['locked_mdd']:.2%} | {r['mdd_improve_pp']:+.2f} |"
        )
    lines += ["", "## Aftermath", ""]
    if adv_pass:
        lines += [
            "- Proceed to **one held-out** (val 2019–2022 + sealed 2023→latest).",
            "- Do **not** retune cuts.",
            "- Do **not** live-wire. Soft-Frozen stays **[0.50, 0.95]**.",
        ]
    else:
        lines += [
            "- **STOP** L3 adv-lite — keep BASE.",
            "- No cut retune; new charter required to continue.",
        ]
    lines += [
        "",
        "Artifacts:",
        f"- `{OUT / 'reports' / 'l3_adv_lite_summary.json'}`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "MDD_L3_ADV_LITE.md").write_text(md)
    (RESEARCH / "MDD_L3_ADV_LITE.md").write_text(md)
    print(
        json.dumps(
            {
                "decision": decision,
                "p_ge": p_ge,
                "year_split_ok": year_split_ok,
                "late_bull_ok": late_bull_ok,
                "late_gb_pp": late_gb_pp,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
