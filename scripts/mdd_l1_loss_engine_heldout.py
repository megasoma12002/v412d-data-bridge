#!/usr/bin/env python3
"""L1 MDD loss-engine one-shot held-out on locked winner (RESEARCH_ONLY).

Locked (no retune): L1_FINCAP50_COMBO_50
  FIN_CAP_50 + COMBO stress flag + equity scale 0.50

Windows (charter):
  validation: 2019-01-01 .. 2022-12-31
  sealed:     2023-01-01 .. latest

Pass each window: Exact T+1 AND MDD improve >=1.0pp vs BASE AND CAGR giveback <=3.0pp
Both pass -> PASS_HELDOUT_L1; else STOP_L1_HELDOUT_*
No live-wire. Dual paper ledgers only on later explicit promote.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from research_metric_helpers import mdd_delta_pp, cagr_delta_pp
from e50_early_stack_combined_nav import e16_features, nav_stats, simulate_core
import e22_dividend_accounting as e22div
import mdd_l1_loss_engine_oof as oof

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/mdd-loss-engine/l1_heldout"
RESEARCH = ROOT / "research/gaps"

LOCKED_ID = "L1_FINCAP50_COMBO_50"
VAL_START, VAL_END = date(2019, 1, 1), date(2022, 12, 31)
SEALED_START = date(2023, 1, 1)

MDD_IMPROVE_MIN = 0.01
CAGR_GIVEBACK_MAX = 0.03


def classify(val_ok: bool, sealed_ok: bool) -> str:
    if val_ok and sealed_ok:
        return "PASS_HELDOUT_L1"
    if (not val_ok) and (not sealed_ok):
        return "STOP_L1_HELDOUT_FAIL"
    return "STOP_L1_HELDOUT_MIXED"


def main() -> None:
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)

    adv = json.loads((RESEARCH / "MDD_L1_ADV_LITE_SUMMARY.json").read_text())
    if adv.get("label") != "ADV_LITE_L1_READY_FOR_HELDOUT":
        raise SystemExit(f"adv-lite not ready: {adv.get('label')}")
    if adv.get("locked", {}).get("id") != LOCKED_ID:
        raise SystemExit(f"locked mismatch: {adv.get('locked')}")

    print("loading market + building BASE / FIN_CAP_50 / COMBO ...", flush=True)
    market = oof.load_market()
    dividends = pd.read_csv(oof.DIV_PATH, dtype={"code": str}) if oof.DIV_PATH.exists() else pd.DataFrame()
    prices, _s, base_target, base_regime = e16_features(market)
    _p, _s2, fin50_target, fin50_regime = oof.e16_features_fin_cap(market, 0.35, 0.50)
    flags = oof.build_stress_flags(prices, base_regime)
    exposure = oof.exposure_from_flag(flags["COMBO"].astype(bool), 0.50)

    print("simulating BASE ...", flush=True)
    nav_b, fills_b, meta_b = simulate_core(
        market,
        base_target,
        base_regime,
        dividends,
        apply_e22=True,
        e22_version=e22div.E22_V2S,
        apply_stock_div=True,
        e45_exposure=None,
    )
    print("simulating locked L1 ...", flush=True)
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
    nav_b.to_csv(OUT / "outputs" / "base_daily_nav.csv", index=False)
    nav_l.to_csv(OUT / "outputs" / "locked_daily_nav.csv", index=False)
    fills_l.to_csv(OUT / "outputs" / "locked_fills.csv", index=False)

    sealed_end = pd.to_datetime(nav_b["date"]).dt.date.max()

    def pack(nav_base, nav_l1, start, end, name):
        b = oof.window_nav_stats(nav_base, start, end)
        l = oof.window_nav_stats(nav_l1, start, end)
        mdd_improve = mdd_delta_pp(b["max_drawdown"], l["max_drawdown"]) / 100.0
        _cgb = cagr_delta_pp(b["cagr"], l["cagr"], missing_as_zero=True)
        cagr_gb = 0.0 if _cgb is None else _cgb / 100.0
        ok = bool(
            meta_b.get("exact_t1_ok")
            and meta_l.get("exact_t1_ok")
            and b["max_drawdown"] is not None
            and l["max_drawdown"] is not None
            and mdd_improve >= MDD_IMPROVE_MIN
            and cagr_gb <= CAGR_GIVEBACK_MAX
        )
        return {
            "window": name,
            "start": str(start),
            "end": str(end),
            "base_cagr": b["cagr"],
            "base_mdd": b["max_drawdown"],
            "l1_cagr": l["cagr"],
            "l1_mdd": l["max_drawdown"],
            "mdd_improve_pp": mdd_improve * 100.0,
            "cagr_giveback_pp": cagr_gb * 100.0,
            "pass": ok,
            "exact_t1_base": bool(meta_b.get("exact_t1_ok")),
            "exact_t1_l1": bool(meta_l.get("exact_t1_ok")),
            "n_days_base": b.get("n_days"),
            "n_days_l1": l.get("n_days"),
        }

    val = pack(nav_b, nav_l, VAL_START, VAL_END, "validation_2019_2022")
    sealed = pack(nav_b, nav_l, SEALED_START, sealed_end, "sealed_2023_latest")
    label = classify(val["pass"], sealed["pass"])
    # research decision mapping
    if label == "PASS_HELDOUT_L1":
        research_decision = "PASS_HELDOUT_L1_DUAL_PAPER_ONLY"
    elif label == "STOP_L1_HELDOUT_MIXED":
        research_decision = "STOP_L1_HELDOUT_MIXED_KEEP_BASE"
    else:
        research_decision = "STOP_L1_HELDOUT_FAIL_KEEP_BASE"

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "heldout_label": label,
        "research_decision": research_decision,
        "live_wire": False,
        "retune_allowed": False,
        "locked_id": LOCKED_ID,
        "gates": {
            "mdd_improve_pp_min": MDD_IMPROVE_MIN * 100,
            "cagr_giveback_pp_max": CAGR_GIVEBACK_MAX * 100,
            "exact_t1": True,
        },
        "validation_2019_2022": val,
        "sealed_2023_latest": sealed,
        "promotion": {
            "replaces_live": False,
            "dual_paper_ledgers_allowed": label == "PASS_HELDOUT_L1",
            "note": "Even on PASS, live stays BASE until explicit cutover PR",
        },
    }

    (OUT / "reports" / "l1_heldout_decision.json").write_text(json.dumps(summary, indent=2) + "\n")
    (RESEARCH / "MDD_L1_HELDOUT_DECISION.json").write_text(json.dumps(summary, indent=2) + "\n")

    lines = [
        "# L1 MDD Loss-Engine — Held-out",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        f"Locked: `{LOCKED_ID}` (no retune)",
        f"Label: `{label}`",
        f"Research decision: `{research_decision}`",
        "",
        "| Window | BASE CAGR | BASE MDD | L1 CAGR | L1 MDD | MDD Δpp | CAGR giveback pp | PASS |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
        (
            f"| val 2019–2022 | {val['base_cagr']:.2%} | {val['base_mdd']:.2%} | "
            f"{val['l1_cagr']:.2%} | {val['l1_mdd']:.2%} | {val['mdd_improve_pp']:+.2f} | "
            f"{val['cagr_giveback_pp']:+.2f} | {'Y' if val['pass'] else 'N'} |"
        ),
        (
            f"| sealed 2023+ | {sealed['base_cagr']:.2%} | {sealed['base_mdd']:.2%} | "
            f"{sealed['l1_cagr']:.2%} | {sealed['l1_mdd']:.2%} | {sealed['mdd_improve_pp']:+.2f} | "
            f"{sealed['cagr_giveback_pp']:+.2f} | {'Y' if sealed['pass'] else 'N'} |"
        ),
        "",
        "No cut retune. No live-wire.",
        "",
    ]
    if label == "PASS_HELDOUT_L1":
        lines += [
            "Aftermath: dual **paper** ledgers (BASE + L1) may be proposed in a separate promote PR; live default stays BASE.",
        ]
    else:
        lines += [
            "Aftermath: keep BASE / Track A; L1 axis stops under this cut; new charter required to continue.",
        ]
    md = "\n".join(lines)
    (OUT / "MDD_L1_HELDOUT.md").write_text(md)
    (RESEARCH / "MDD_L1_HELDOUT.md").write_text(md)
    print(json.dumps({"heldout_label": label, "research_decision": research_decision, "val_pass": val["pass"], "sealed_pass": sealed["pass"]}, indent=2))
    print("EXIT:0")


if __name__ == "__main__":
    main()
