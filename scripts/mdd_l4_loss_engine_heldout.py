#!/usr/bin/env python3
"""L4 one-shot held-out for locked L4_DD_PATH_08_50 (RESEARCH_ONLY).

Locked: FIN_CAP_50 only while TAIEX DD from 252d peak <= -8%; else Soft-Frozen.
Windows:
  validation 2019-01-01 .. 2022-12-31
  sealed     2023-01-01 .. latest

Pass each: Exact T+1 AND MDD improve >=1.0pp vs BASE AND CAGR giveback <=3.0pp
Both pass -> PASS_HELDOUT_L4; else STOP_L4_HELDOUT_*
No cut retune. No live-wire.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e22_dividend_accounting as e22div
import mdd_l1_loss_engine_oof as oof
from mdd_l4_loss_engine_oof import dd_path_target

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/mdd-loss-engine/l4_heldout"
RESEARCH = ROOT / "research/gaps"

LOCKED_ID = "L4_DD_PATH_08_50"
LOCKED_DD_THR = -0.08
LOCKED_FIN_LO, LOCKED_FIN_HI = 0.35, 0.50
VAL_START, VAL_END = date(2019, 1, 1), date(2022, 12, 31)
SEALED_START = date(2023, 1, 1)
MDD_IMPROVE_MIN = 0.01
CAGR_GIVEBACK_MAX = 0.03


def classify(val_ok: bool, sealed_ok: bool) -> str:
    if val_ok and sealed_ok:
        return "PASS_HELDOUT_L4"
    if (not val_ok) and (not sealed_ok):
        return "STOP_L4_HELDOUT_FAIL"
    return "STOP_L4_HELDOUT_MIXED_KEEP_BASE"


def pack(nav_b, nav_l, meta_b, meta_l, start, end, name):
    b = oof.window_nav_stats(nav_b, start, end)
    l = oof.window_nav_stats(nav_l, start, end)
    mdd_improve = abs(b["max_drawdown"] or 9) - abs(l["max_drawdown"] or 9)
    cagr_gb = (b["cagr"] or 0) - (l["cagr"] or 0)
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
        "l4_cagr": l["cagr"],
        "l4_mdd": l["max_drawdown"],
        "mdd_improve_pp": mdd_improve * 100.0,
        "cagr_giveback_pp": cagr_gb * 100.0,
        "pass": ok,
        "exact_t1_base": bool(meta_b.get("exact_t1_ok")),
        "exact_t1_l4": bool(meta_l.get("exact_t1_ok")),
        "n_days_base": b.get("n_days"),
        "n_days_l4": l.get("n_days"),
        "fail_mdd": mdd_improve < MDD_IMPROVE_MIN,
        "fail_cagr": cagr_gb > CAGR_GIVEBACK_MAX,
    }


def main() -> None:
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)

    adv = json.loads((RESEARCH / "MDD_L4_ADV_LITE_SUMMARY.json").read_text())
    if adv.get("label") != "ADV_LITE_L4_READY_FOR_HELDOUT":
        raise SystemExit(f"adv-lite not ready: {adv.get('label')}")
    if adv.get("locked_id") != LOCKED_ID:
        raise SystemExit(f"locked mismatch: {adv.get('locked_id')}")

    print("simulating BASE + locked L4_DD_PATH_08_50 held-out ...", flush=True)
    market = oof.load_market()
    dividends = (
        pd.read_csv(oof.DIV_PATH, dtype={"code": str}) if oof.DIV_PATH.exists() else pd.DataFrame()
    )
    prices, _s, base_target, base_regime = oof.e16_features(market)
    _p2, _s2, fin50_target, _ = oof.e16_features_fin_cap(market, LOCKED_FIN_LO, LOCKED_FIN_HI)
    locked_target, locked_flag = dd_path_target(
        base_target, fin50_target, prices, LOCKED_DD_THR
    )

    nav_b, fills_b, meta_b = oof.simulate_core(
        market,
        base_target,
        base_regime,
        dividends,
        apply_e22=True,
        e22_version=e22div.E22_V2S,
        apply_stock_div=True,
        e45_exposure=None,
    )
    nav_l, fills_l, meta_l = oof.simulate_core(
        market,
        locked_target,
        base_regime,
        dividends,
        apply_e22=True,
        e22_version=e22div.E22_V2S,
        apply_stock_div=True,
        e45_exposure=None,
    )
    nav_b.to_csv(OUT / "outputs" / "base_daily_nav.csv", index=False)
    nav_l.to_csv(OUT / "outputs" / "locked_daily_nav.csv", index=False)
    fills_b.to_csv(OUT / "outputs" / "base_fills.csv", index=False)
    fills_l.to_csv(OUT / "outputs" / "locked_fills.csv", index=False)

    asof = pd.to_datetime(nav_b["date"]).dt.date.max()
    val = pack(nav_b, nav_l, meta_b, meta_l, VAL_START, VAL_END, "validation")
    sealed = pack(nav_b, nav_l, meta_b, meta_l, SEALED_START, asof, "sealed")
    decision = classify(bool(val["pass"]), bool(sealed["pass"]))

    idx = pd.to_datetime(locked_flag.index).date

    def share(start, end):
        m = (idx >= start) & (idx <= end)
        return float(locked_flag.loc[m].mean()) if m.any() else float("nan")

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": decision,
        "live_wire": False,
        "research_only": True,
        "retune_allowed": False,
        "l1_l2_l3_retune_forbidden": True,
        "soft_frozen_live_clip": [0.50, 0.95],
        "locked_id": LOCKED_ID,
        "locked_params": {
            "dd_thr": LOCKED_DD_THR,
            "fin_lo": LOCKED_FIN_LO,
            "fin_hi": LOCKED_FIN_HI,
        },
        "asof": str(asof),
        "gates": {
            "mdd_improve_pp_min": MDD_IMPROVE_MIN * 100,
            "cagr_giveback_pp_max": CAGR_GIVEBACK_MAX * 100,
            "exact_t1": True,
        },
        "validation": val,
        "sealed": sealed,
        "flag_share": {
            "validation": share(VAL_START, VAL_END),
            "sealed": share(SEALED_START, asof),
        },
        "live_unchanged": True,
        "next_if_pass": "dual-paper only; human PR required before any Soft-Frozen change",
        "next_if_stop": "keep BASE Soft-Frozen; do not promote L4; FIN_CAP_50 paper continues",
    }

    (OUT / "reports" / "l4_heldout_summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n"
    )
    (RESEARCH / "MDD_L4_HELDOUT_SUMMARY.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n"
    )

    lines = [
        "# L4 MDD Path/FINCAP — Held-out",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        "Status: **RESEARCH_ONLY** — no live-wire, Soft-Frozen unchanged.",
        "",
        f"## Decision: `{decision}`",
        "",
        f"- Locked: **{LOCKED_ID}** (TAIEX DD≤{LOCKED_DD_THR:.0%} → FIN[{LOCKED_FIN_LO:.2f},{LOCKED_FIN_HI:.2f}])",
        f"- As-of: `{asof}`",
        f"- Gates: Exact T+1; MDD ≥**{MDD_IMPROVE_MIN*100:.1f}pp**; CAGR giveback ≤**{CAGR_GIVEBACK_MAX*100:.1f}pp** (each window)",
        "",
        "| Window | BASE CAGR | L4 CAGR | CAGR gb pp | BASE MDD | L4 MDD | MDD Δpp | PASS |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for r in (val, sealed):
        lines.append(
            f"| {r['window']} {r['start']}→{r['end']} | {r['base_cagr']:.2%} | {r['l4_cagr']:.2%} | "
            f"{r['cagr_giveback_pp']:+.2f} | {r['base_mdd']:.2%} | {r['l4_mdd']:.2%} | "
            f"{r['mdd_improve_pp']:+.2f} | {'Y' if r['pass'] else ''} |"
        )
    lines += ["", "## Aftermath", ""]
    if decision == "PASS_HELDOUT_L4":
        lines += [
            "- Held-out PASS — still **no auto live-wire**.",
            "- Dual-paper observation only; Soft-Frozen stays **[0.50, 0.95]** until human PR.",
        ]
    else:
        lines += [
            "- **STOP** — keep BASE Soft-Frozen.",
            "- Do not promote L4. Do not retune stopped L1/L2/L3/FIN50 locks.",
            f"- Val pass={val['pass']} (CAGR gb {val['cagr_giveback_pp']:+.2f}pp, MDD {val['mdd_improve_pp']:+.2f}pp); "
            f"Sealed pass={sealed['pass']} (CAGR gb {sealed['cagr_giveback_pp']:+.2f}pp, MDD {sealed['mdd_improve_pp']:+.2f}pp).",
        ]
    lines += [
        "",
        "Artifacts:",
        f"- `{OUT / 'reports/l4_heldout_summary.json'}`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "MDD_L4_HELDOUT.md").write_text(md)
    (RESEARCH / "MDD_L4_HELDOUT.md").write_text(md)
    print(
        json.dumps(
            {
                "label": decision,
                "val_pass": val["pass"],
                "sealed_pass": sealed["pass"],
                "val_cagr_gb_pp": val["cagr_giveback_pp"],
                "sealed_cagr_gb_pp": sealed["cagr_giveback_pp"],
                "val_mdd_pp": val["mdd_improve_pp"],
                "sealed_mdd_pp": sealed["mdd_improve_pp"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
