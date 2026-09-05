#!/usr/bin/env python3
"""FIN_CAP_50 go-live research verification (RESEARCH_ONLY — no Soft-Frozen flip).

Refreshes Exact T+1 BASE vs FIN_CAP_50 paper books and scores cutover readiness.

Gates (all required for READY_FOR_HUMAN_CUTOVER_PR):
  A) Exact T+1 on both books
  B) Combined held-out 2019+: MDD improve >=1.0pp AND CAGR giveback <=3.0pp
  C) Sealed 2023+:         MDD improve >=1.0pp AND CAGR giveback <=3.0pp
     (required after L1/L2/L3 sealed CAGR failures)
  D) Soft-Frozen live clip remains [0.50, 0.95] (this harness never flips it)
  E) No PAUSE_REVIEW on trailing windows (CAGR giveback >5pp)

Does NOT edit live clips. Does NOT open cutover automatically.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from e50_early_stack_combined_nav import ALL, e16_features, nav_stats, simulate_core
import e22_dividend_accounting as e22div
from e16_fin_cap_oof_challenger import e16_features_fin_cap
from e16_soft_frozen_base import SOFT_FROZEN_FIN_HI, SOFT_FROZEN_FIN_LO

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/fincap50-go-live-verify"
RESEARCH = ROOT / "research/gaps"
MARKET_PATH = ROOT / "forward/e21/live_market.csv"
DIV_PATH = ROOT / "data/dividend_events/e22_dividend_events.csv"

# Expected Soft-Frozen live clip — must match e16_soft_frozen_base (single source of truth).
SOFT_FROZEN_LIVE = (float(SOFT_FROZEN_FIN_LO), float(SOFT_FROZEN_FIN_HI))
EXPECTED_SOFT_FROZEN_LIVE = (0.50, 0.95)
FIN_CAP_50 = (0.35, 0.50)
MDD_IMPROVE_MIN_PP = 1.0
CAGR_GIVEBACK_MAX_PP = 3.0
PAUSE_CAGR_GIVEBACK_PP = 5.0


def load_market() -> pd.DataFrame:
    market = pd.read_csv(MARKET_PATH, dtype={"code": str})
    market["date"] = pd.to_datetime(market["date"])
    required = set(ALL + ["TAIEX"])
    complete = market.groupby("date")["code"].apply(lambda s: required.issubset(set(s)))
    return market[market["date"].isin(complete[complete].index)].sort_values(["date", "code"])


def window_stats(nav: pd.DataFrame, start: date, end: date) -> dict:
    d = nav.copy()
    d["date"] = pd.to_datetime(d["date"]).dt.date
    d = d[(d["date"] >= start) & (d["date"] <= end)].reset_index(drop=True)
    if len(d) < 30:
        return {"cagr": None, "max_drawdown": None, "n_days": int(len(d))}
    d = d.copy()
    d["nav"] = d["nav"] / float(d["nav"].iloc[0])
    out = nav_stats(d)
    out["n_days"] = int(len(d))
    return out


def score_window(nav_b: pd.DataFrame, nav_l: pd.DataFrame, start: date, end: date, name: str) -> dict:
    b = window_stats(nav_b, start, end)
    l = window_stats(nav_l, start, end)
    if b["cagr"] is None or l["cagr"] is None:
        return {
            "window": name,
            "start": str(start),
            "end": str(end),
            "base_cagr": None,
            "base_mdd": None,
            "fincap50_cagr": None,
            "fincap50_mdd": None,
            "mdd_improve_pp": None,
            "cagr_giveback_pp": None,
            "n_days": b["n_days"],
            "pass": False,
            "fail_reasons": ["insufficient_days"],
        }
    mdd_pp = (abs(b["max_drawdown"]) - abs(l["max_drawdown"])) * 100.0
    cagr_gb_pp = (b["cagr"] - l["cagr"]) * 100.0
    reasons: list[str] = []
    if mdd_pp < MDD_IMPROVE_MIN_PP:
        reasons.append("mdd_improve")
    if cagr_gb_pp > CAGR_GIVEBACK_MAX_PP:
        reasons.append("cagr_giveback")
    return {
        "window": name,
        "start": str(start),
        "end": str(end),
        "base_cagr": b["cagr"],
        "base_mdd": b["max_drawdown"],
        "fincap50_cagr": l["cagr"],
        "fincap50_mdd": l["max_drawdown"],
        "mdd_improve_pp": mdd_pp,
        "cagr_giveback_pp": cagr_gb_pp,
        "n_days": b["n_days"],
        "pass": len(reasons) == 0,
        "fail_reasons": reasons,
    }


def month_end_monitor(nav_b: pd.DataFrame, nav_l: pd.DataFrame, asof: date) -> dict:
    windows = [
        score_window(nav_b, nav_l, date.fromordinal(asof.toordinal() - 365), asof, "trailing_1y"),
        score_window(nav_b, nav_l, date(asof.year, 1, 1), asof, "ytd"),
        score_window(nav_b, nav_l, date(2019, 1, 1), asof, "heldout_2019_plus"),
    ]
    alerts = []
    pause = False
    for w in windows:
        gb = w.get("cagr_giveback_pp")
        mdd = w.get("mdd_improve_pp")
        if gb is None:
            continue
        if gb > PAUSE_CAGR_GIVEBACK_PP:
            alerts.append({"window": w["window"], "level": "PAUSE_REVIEW", "cagr_giveback_pp": gb})
            pause = True
        elif gb > CAGR_GIVEBACK_MAX_PP:
            alerts.append(
                {"window": w["window"], "level": "EXTEND_OBSERVATION", "cagr_giveback_pp": gb}
            )
        if mdd is not None and mdd < 0:
            alerts.append(
                {"window": w["window"], "level": "MDD_WORSE_THAN_BASE", "mdd_improve_pp": mdd}
            )
    return {"asof": str(asof), "windows": windows, "alerts": alerts, "pause_review": pause}


def main() -> None:
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)

    print("loading market + dividends ...", flush=True)
    market = load_market()
    dividends = pd.read_csv(DIV_PATH, dtype={"code": str}) if DIV_PATH.exists() else pd.DataFrame()

    print("simulating BASE Soft-Frozen Exact T+1 ...", flush=True)
    _p, _s, base_target, base_regime = e16_features(market)
    nav_b, _fb, meta_b = simulate_core(
        market,
        base_target,
        base_regime,
        dividends,
        apply_e22=True,
        e22_version=e22div.E22_V2S,
        apply_stock_div=True,
    )

    print("simulating FIN_CAP_50 Exact T+1 ...", flush=True)
    _p2, _s2, cap_target, cap_regime = e16_features_fin_cap(market, FIN_CAP_50[0], FIN_CAP_50[1])
    nav_l, _fl, meta_l = simulate_core(
        market,
        cap_target,
        cap_regime,
        dividends,
        apply_e22=True,
        e22_version=e22div.E22_V2S,
        apply_stock_div=True,
    )

    nav_b.to_csv(OUT / "outputs" / "base_daily_nav.csv", index=False)
    nav_l.to_csv(OUT / "outputs" / "fincap50_daily_nav.csv", index=False)

    asof = min(
        pd.to_datetime(nav_b["date"]).dt.date.max(),
        pd.to_datetime(nav_l["date"]).dt.date.max(),
    )
    gate_a = bool(meta_b.get("exact_t1_ok")) and bool(meta_l.get("exact_t1_ok"))
    combined = score_window(nav_b, nav_l, date(2019, 1, 1), asof, "heldout_2019_plus")
    val = score_window(nav_b, nav_l, date(2019, 1, 1), date(2022, 12, 31), "validation_2019_2022")
    sealed = score_window(nav_b, nav_l, date(2023, 1, 1), asof, "sealed_2023_plus")
    mon = month_end_monitor(nav_b, nav_l, asof)

    gate_b = bool(combined["pass"])
    gate_c = bool(sealed["pass"])
    # Gate D: Soft-Frozen live clip must still equal the module single source of truth.
    gate_d = (
        abs(SOFT_FROZEN_LIVE[0] - EXPECTED_SOFT_FROZEN_LIVE[0]) < 1e-12
        and abs(SOFT_FROZEN_LIVE[1] - EXPECTED_SOFT_FROZEN_LIVE[1]) < 1e-12
        and abs(float(SOFT_FROZEN_FIN_LO) - EXPECTED_SOFT_FROZEN_LIVE[0]) < 1e-12
        and abs(float(SOFT_FROZEN_FIN_HI) - EXPECTED_SOFT_FROZEN_LIVE[1]) < 1e-12
    )
    gate_e = not bool(mon["pause_review"])
    ready = gate_a and gate_b and gate_c and gate_d and gate_e

    if ready:
        label = "READY_FOR_HUMAN_CUTOVER_PR"
        research_decision = "GO_LIVE_VERIFY_PASS__HUMAN_CUTOVER_PR_REQUIRED"
    elif gate_a and gate_b and (not gate_c):
        label = "NOT_READY_SEALED_CAGR"
        research_decision = "GO_LIVE_VERIFY_BLOCKED_SEALED_CAGR__KEEP_SOFT_FROZEN"
    else:
        label = "NOT_READY_FOR_LIVE"
        research_decision = "GO_LIVE_VERIFY_FAIL__KEEP_SOFT_FROZEN"

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": label,
        "research_decision": research_decision,
        "live_wire": False,
        "soft_frozen_live_clip": list(SOFT_FROZEN_LIVE),
        "challenger_clip": list(FIN_CAP_50),
        "asof": str(asof),
        "gates": {
            "A_exact_t1": {
                "pass": gate_a,
                "base": bool(meta_b.get("exact_t1_ok")),
                "fincap50": bool(meta_l.get("exact_t1_ok")),
            },
            "B_heldout_2019_plus": {
                "pass": gate_b,
                "mdd_improve_pp": combined["mdd_improve_pp"],
                "cagr_giveback_pp": combined["cagr_giveback_pp"],
                "fail_reasons": combined["fail_reasons"],
            },
            "C_sealed_2023_plus": {
                "pass": gate_c,
                "mdd_improve_pp": sealed["mdd_improve_pp"],
                "cagr_giveback_pp": sealed["cagr_giveback_pp"],
                "fail_reasons": sealed["fail_reasons"],
            },
            "D_soft_frozen_unchanged": {
                "pass": gate_d,
                "clip": list(SOFT_FROZEN_LIVE),
                "expected_clip": list(EXPECTED_SOFT_FROZEN_LIVE),
                "module_source": "scripts/e16_soft_frozen_base.py",
                "module_clip": [float(SOFT_FROZEN_FIN_LO), float(SOFT_FROZEN_FIN_HI)],
                "rule": "SOFT_FROZEN_FIN_LO/HI must remain [0.50, 0.95]; no hardcoded True",
            },
            "E_no_pause_review": {
                "pass": gate_e,
                "pause_review": mon["pause_review"],
                "n_alerts": len(mon["alerts"]),
            },
        },
        "windows": {
            "heldout_2019_plus": combined,
            "validation_2019_2022": val,
            "sealed_2023_plus": sealed,
        },
        "month_end_monitor": mon,
        "cutover_policy": {
            "auto_flip_forbidden": True,
            "requires_human_pr": True,
            "requires_all_gates_abcde": True,
            "note": "Legacy PASS on 2019+ alone is insufficient after L1/L2/L3 sealed CAGR failures.",
        },
    }

    (OUT / "reports" / "fincap50_go_live_verify.json").write_text(json.dumps(summary, indent=2) + "\n")
    (RESEARCH / "FIN_CAP_50_GO_LIVE_VERIFY.json").write_text(json.dumps(summary, indent=2) + "\n")

    lines = [
        "# FIN_CAP_50 Go-Live Research Verification",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        f"As-of: `{asof}`",
        "Status: **RESEARCH_ONLY** — Soft-Frozen live clip **not** changed.",
        "",
        f"## Decision: `{label}`",
        "",
        f"Research decision: `{research_decision}`",
        "",
        "### Gates",
        "",
        "| Gate | Rule | Result |",
        "|---|---|---|",
        f"| A Exact T+1 | both books | {'PASS' if gate_a else 'FAIL'} |",
        (
            f"| B Held-out 2019+ | MDD≥1pp & CAGR gb≤3pp | "
            f"{'PASS' if gate_b else 'FAIL'} "
            f"(MDD {combined['mdd_improve_pp']:+.2f}pp; CAGR gb {combined['cagr_giveback_pp']:+.2f}pp) |"
        ),
        (
            f"| C Sealed 2023+ | MDD≥1pp & CAGR gb≤3pp | "
            f"{'PASS' if gate_c else 'FAIL'} "
            f"(MDD {sealed['mdd_improve_pp']:+.2f}pp; CAGR gb {sealed['cagr_giveback_pp']:+.2f}pp) |"
        ),
        f"| D Soft-Frozen | stays [0.50, 0.95] | {'PASS' if gate_d else 'FAIL'} |",
        f"| E Month-end | no PAUSE_REVIEW | {'PASS' if gate_e else 'FAIL'} |",
        "",
        "### Windows",
        "",
        "| Window | BASE CAGR | BASE MDD | FIN50 CAGR | FIN50 MDD | MDD Δpp | CAGR gb pp | PASS |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for w in (combined, val, sealed):
        lines.append(
            f"| {w['window']} | {w['base_cagr']:.2%} | {w['base_mdd']:.2%} | "
            f"{w['fincap50_cagr']:.2%} | {w['fincap50_mdd']:.2%} | "
            f"{w['mdd_improve_pp']:+.2f} | {w['cagr_giveback_pp']:+.2f} | "
            f"{'Y' if w['pass'] else 'N'} |"
        )
    lines += ["", "### Month-end alerts", ""]
    if not mon["alerts"]:
        lines.append("- none")
    else:
        for a in mon["alerts"]:
            lines.append(f"- `{a['level']}` on `{a['window']}` — {a}")
    lines += ["", "## Aftermath", ""]
    if ready:
        lines += [
            "- Research verification **PASS** under sealed-aware gates.",
            "- Still requires a **separate human cutover PR** to change Soft-Frozen to [0.35, 0.50].",
            "- Keep BASE paper ledger indefinitely.",
        ]
    else:
        lines += [
            "- **Do not cut over live.** Soft-Frozen stays **[0.50, 0.95]**.",
            "- Continue dual-paper month-end observation only.",
            "- If blocked on sealed CAGR: new charter required (do not retune FIN_CAP_50 lock).",
        ]
    lines += [
        "",
        "Artifacts:",
        f"- `{OUT / 'reports' / 'fincap50_go_live_verify.json'}`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "FIN_CAP_50_GO_LIVE_VERIFY.md").write_text(md)
    (RESEARCH / "FIN_CAP_50_GO_LIVE_VERIFY.md").write_text(md)
    print(
        json.dumps(
            {
                "label": label,
                "research_decision": research_decision,
                "gate_a": gate_a,
                "gate_b": gate_b,
                "gate_c": gate_c,
                "gate_e": gate_e,
                "combined_cagr_gb_pp": combined["cagr_giveback_pp"],
                "sealed_cagr_gb_pp": sealed["cagr_giveback_pp"],
                "sealed_mdd_pp": sealed["mdd_improve_pp"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
