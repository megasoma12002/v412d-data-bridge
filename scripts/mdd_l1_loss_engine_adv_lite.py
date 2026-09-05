#!/usr/bin/env python3
"""L1 MDD loss-engine adversarial-lite on locked OOF winner (RESEARCH_ONLY).

Locked from OOF (do not retune): L1_FINCAP50_COMBO_50
  FIN_CAP_50 targets + COMBO stress flag + equity scale 0.50

Adv-lite gates (charter):
  - Placebo: scramble COMBO flags; P(MDD improve >= locked challenger) < 0.50
  - Year-split: OOF MDD improve not entirely from a single calendar year

No held-out peek for selection. No live-wire.
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
from e50_early_stack_combined_nav import e16_features, nav_stats, simulate_core
import e22_dividend_accounting as e22div
import mdd_l1_loss_engine_oof as oof

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/mdd-loss-engine/l1_adv_lite"
RESEARCH = ROOT / "research/gaps"

LOCKED = {
    "id": "L1_FINCAP50_COMBO_50",
    "family": "L1-FINCAP-STACK",
    "fin_lo": 0.35,
    "fin_hi": 0.50,
    "flag": "COMBO",
    "scale": 0.50,
}
N_PLACEBO = 24
PLACEBO_SEED = 20260905
PLACEBO_P_MAX = 0.50


def year_mdd(nav: pd.DataFrame, year: int) -> float | None:
    d = nav.copy()
    d["date"] = pd.to_datetime(d["date"])
    g = d[d["date"].dt.year == year].reset_index(drop=True)
    if len(g) < 30:
        return None
    g = g.copy()
    g["nav"] = g["nav"] / float(g["nav"].iloc[0])
    return float(nav_stats(g)["max_drawdown"])


def main() -> None:
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)

    oof_summary = json.loads((RESEARCH / "MDD_L1_OOF_SUMMARY.json").read_text())
    if oof_summary.get("locked_winner") != LOCKED["id"]:
        raise SystemExit(f"OOF locked winner mismatch: {oof_summary.get('locked_winner')}")
    locked_row = oof_summary["winner_row"]
    locked_improve = float(locked_row["mdd_improve_pp"]) / 100.0
    base_oof_mdd = float(oof_summary["base"]["oof_mdd"])
    base_oof_cagr = float(oof_summary["base"]["oof_cagr"])

    print("loading market + building FIN_CAP_50 + COMBO flags ...", flush=True)
    market = oof.load_market()
    dividends = pd.read_csv(oof.DIV_PATH, dtype={"code": str}) if oof.DIV_PATH.exists() else pd.DataFrame()
    prices, _s, _base_t, base_regime = e16_features(market)
    _p, _s2, fin50_target, fin50_regime = oof.e16_features_fin_cap(market, 0.35, 0.50)
    flags = oof.build_stress_flags(prices, base_regime)
    true_flag = flags["COMBO"].astype(bool)

    # Locked challenger (recompute for year-split + artifact)
    print("simulating locked challenger ...", flush=True)
    exposure = oof.exposure_from_flag(true_flag, LOCKED["scale"])
    nav_l, fills_l, meta_l = simulate_core(
        market,
        fin50_target,
        fin50_regime,
        dividends,
        apply_e22=True,
        e22_version=e22div.E22_V2S,
        apply_stock_div=True,
        e45_exposure=exposure,
    )
    nav_l.to_csv(OUT / "outputs" / "locked_daily_nav.csv", index=False)
    fills_l.to_csv(OUT / "outputs" / "locked_fills.csv", index=False)
    oof_l = oof.window_nav_stats(nav_l, oof.OOF_START, oof.OOF_END)
    assert meta_l.get("exact_t1_ok")

    # BASE for year-split compare
    print("simulating BASE for year-split ...", flush=True)
    _p0, _s0, base_target, base_regime2 = e16_features(market)
    nav_b, _f_b, meta_b = simulate_core(
        market,
        base_target,
        base_regime2,
        dividends,
        apply_e22=True,
        e22_version=e22div.E22_V2S,
        apply_stock_div=True,
        e45_exposure=None,
    )
    assert meta_b.get("exact_t1_ok")

    years = list(range(oof.OOF_START.year, oof.OOF_END.year + 1))
    year_rows = []
    for y in years:
        mb = year_mdd(nav_b, y)
        ml = year_mdd(nav_l, y)
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
    dominant_year = max(year_rows, key=lambda r: r["mdd_improve_pp"]) if year_rows else None

    # Placebo flag scrambles (preserve # of True days)
    print(f"running {N_PLACEBO} placebo flag scrambles ...", flush=True)
    rng = np.random.default_rng(PLACEBO_SEED)
    n_true = int(true_flag.sum())
    idx = true_flag.index
    placebo_rows = []
    beat = 0
    for i in range(N_PLACEBO):
        perm = np.zeros(len(idx), dtype=bool)
        choose = rng.choice(len(idx), size=n_true, replace=False)
        perm[choose] = True
        fake = pd.Series(perm, index=idx)
        exp = oof.exposure_from_flag(fake, LOCKED["scale"])
        nav_p, _fp, meta_p = simulate_core(
            market,
            fin50_target,
            fin50_regime,
            dividends,
            apply_e22=True,
            e22_version=e22div.E22_V2S,
            apply_stock_div=True,
            e45_exposure=exp,
        )
        assert meta_p.get("exact_t1_ok")
        st = oof.window_nav_stats(nav_p, oof.OOF_START, oof.OOF_END)
        improve = mdd_delta_pp(base_oof_mdd, st["max_drawdown"]) / 100.0
        _cgb = cagr_delta_pp(base_oof_cagr, st["cagr"], missing_as_zero=True)
        cagr_gb = 0.0 if _cgb is None else _cgb / 100.0
        ge_locked = improve + 1e-12 >= locked_improve
        if ge_locked:
            beat += 1
        placebo_rows.append(
            {
                "placebo_i": i,
                "oof_cagr": st["cagr"],
                "oof_mdd": st["max_drawdown"],
                "mdd_improve_pp": improve * 100.0,
                "cagr_giveback_pp": cagr_gb * 100.0,
                "ge_locked_improve": ge_locked,
            }
        )
        print(
            f"  placebo {i:02d}: MDD improve={improve*100:.2f}pp "
            f"ge_locked={ge_locked}",
            flush=True,
        )

    p_ge = beat / float(N_PLACEBO)
    adv_pass = bool(p_ge < PLACEBO_P_MAX and year_split_ok)
    decision = "ADV_LITE_L1_READY_FOR_HELDOUT" if adv_pass else "STOP_L1_ADV_LITE"

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": decision,
        "live_wire": False,
        "research_only": True,
        "retune_allowed": False,
        "locked": LOCKED,
        "locked_from_oof": {
            "mdd_improve_pp": locked_row["mdd_improve_pp"],
            "cagr_giveback_pp": locked_row["cagr_giveback_pp"],
            "oof_cagr": locked_row["oof_cagr"],
            "oof_mdd": locked_row["oof_mdd"],
        },
        "recomputed_locked_oof": oof_l,
        "exact_t1_ok": bool(meta_l.get("exact_t1_ok")),
        "placebo": {
            "n": N_PLACEBO,
            "seed": PLACEBO_SEED,
            "p_mdd_improve_ge_locked": p_ge,
            "p_max": PLACEBO_P_MAX,
            "n_beat_locked": beat,
            "rows": placebo_rows,
        },
        "year_split": {
            "ok": year_split_ok,
            "n_positive_years": len(positive_years),
            "years": year_rows,
            "dominant_year": dominant_year,
        },
        "adv_pass": adv_pass,
        "next_if_pass": "one held-out (val 2019-2022 + sealed 2023+); dual paper ledgers; no live-wire",
        "next_if_stop": "keep BASE / Track A; do not retune L1 cuts; new charter required",
    }

    (OUT / "reports" / "l1_adv_lite_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (RESEARCH / "MDD_L1_ADV_LITE_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n")
    pd.DataFrame(placebo_rows).to_csv(OUT / "outputs" / "l1_adv_lite_placebos.csv", index=False)
    pd.DataFrame(year_rows).to_csv(OUT / "outputs" / "l1_adv_lite_year_split.csv", index=False)

    lines = [
        "# L1 MDD Loss-Engine — Adversarial-lite",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        "Status: **RESEARCH_ONLY** — no live-wire, no Soft-Frozen edit, no held-out selection.",
        "",
        f"## Decision: `{decision}`",
        "",
        f"- Locked: **{LOCKED['id']}** (FIN_CAP_50 + COMBO × scale {LOCKED['scale']})",
        f"- Locked OOF MDD improve: **{locked_row['mdd_improve_pp']:.2f} pp**; CAGR giveback **{locked_row['cagr_giveback_pp']:.2f} pp**",
        f"- Placebo P(MDD improve ≥ locked) = **{p_ge:.3f}** (gate &lt; {PLACEBO_P_MAX:.2f}; n={N_PLACEBO}, seed={PLACEBO_SEED})",
        f"- Year-split OK: **{year_split_ok}** (positive years={len(positive_years)})",
        f"- Exact T+1: **{meta_l.get('exact_t1_ok')}**",
        "",
        "## Year-split (OOF calendar years)",
        "",
        "| Year | BASE MDD | Locked MDD | Improve pp |",
        "|---:|---:|---:|---:|",
    ]
    for r in year_rows:
        lines.append(
            f"| {r['year']} | {r['base_mdd']:.2%} | {r['locked_mdd']:.2%} | {r['mdd_improve_pp']:+.2f} |"
        )
    lines += [
        "",
        "## Aftermath",
        "",
    ]
    if adv_pass:
        lines += [
            "- Proceed to **one held-out** (val 2019–2022 + sealed 2023→latest).",
            "- Do **not** retune cuts.",
            "- Do **not** live-wire; dual paper ledgers (BASE + L1) on any later promote.",
        ]
    else:
        lines += [
            "- **STOP** L1 adv-lite — keep BASE / Track A.",
            "- No cut retune; new charter required for further loss-engine work.",
        ]
    lines += [
        "",
        "Artifacts:",
        f"- `{OUT / 'reports' / 'l1_adv_lite_summary.json'}`",
        f"- `{OUT / 'outputs' / 'l1_adv_lite_placebos.csv'}`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "MDD_L1_ADV_LITE.md").write_text(md)
    (RESEARCH / "MDD_L1_ADV_LITE.md").write_text(md)
    print(json.dumps({"decision": decision, "p_ge": p_ge, "year_split_ok": year_split_ok}, indent=2))
    print("EXIT:0")


if __name__ == "__main__":
    main()
