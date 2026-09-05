#!/usr/bin/env python3
"""E45 paper feasibility gates F1–F7 (charter-aligned, rigorous).

Does not authorize live. Does not modify E45 strategy logic.
Writes only reports/f1_f7_gates.json (+ pack copy) — never clobbers
SEAL_LOCK.json or the sealed study verdict owned by seal_pack.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from e45_feasibility_common import (  # noqa: E402
    CLAIMED_MDD_INTERPRETATION,
    CLAIMED_MDD_LABEL,
    DEFAULT_LIVE_BOOKS,
    LOCKED_E3_WINNER,
    VERIFIED_CLOSEST_LINEAGE_VAL_MDD,
    VERIFIED_E3_LOCKED_VAL_MDD,
    VERIFIED_EARLY_STACK_PLUS_E45_E3_MDD,
    cagr_calendar,
    claim_dict,
    dumps_json,
    load_json,
    mdd,
    official_status_dict,
    refuse_superseded_pack,
    verify_output_manifest,
)
from e45_crisis_core import E3_WINNER  # noqa: E402
from e22_dividend_accounting import DEFAULT_BOOKS_VERSION  # noqa: E402

BASE_NAV = "e16_e18_e22_daily_nav.csv"
CHAL_NAV = "e16_e18_e22_e45_e3_daily_nav.csv"
BASE_FILLS = "e16_e18_e22_fills.csv"
CHAL_FILLS = "e16_e18_e22_e45_e3_fills.csv"
CAGR_GIVEBACK_MAX_PP = 2.0
F5_EXCEPTION_MIN_CRISIS_IMPROVE_PP = 1.0
F5_EXCEPTION_MIN_YEARS_BETTER = 2
F5_EXCEPTION_MAX_YEARS_WORSE = 0
F5_EXCEPTION_REQUIRE_FULL_MDD_BETTER = True


def same_bar_fills(path: Path) -> int:
    f = pd.read_csv(path)
    cols = {c.lower(): c for c in f.columns}
    for sig_k, fill_k in (
        ("signal_date", "fill_date"),
        ("decision_date", "fill_date"),
        ("signal_date", "exec_date"),
    ):
        if sig_k in cols and fill_k in cols:
            s = pd.to_datetime(f[cols[sig_k]])
            e = pd.to_datetime(f[cols[fill_k]])
            return int((s == e).sum())
    return -1


def f1_artifact_honesty(pack: Path) -> dict:
    try:
        verify = verify_output_manifest(pack)
        hash_ok = True
    except SystemExit as exc:
        hash_ok = False
        verify = {"ok": False, "error": str(exc)}
    label_ok = CLAIMED_MDD_LABEL == "NOT_VERIFIED_HISTORICAL_NARRATIVE"
    interp_ok = CLAIMED_MDD_INTERPRETATION == "EARLY_NON_RIGOROUS_RESEARCH_RESULT"
    ok = hash_ok and label_ok and interp_ok
    return {
        "id": "F1",
        "name": "artifact_honesty",
        "pass": ok,
        "hash_verify": verify,
        "claim": claim_dict(),
        "notes": "Dated INPUT/OUTPUT manifests required; −13.16% cannot be PASS evidence.",
    }


def f2_exact_t1(pack: Path) -> dict:
    sb_b = same_bar_fills(pack / "outputs" / BASE_FILLS)
    sb_c = same_bar_fills(pack / "outputs" / CHAL_FILLS)
    exact_ok = sb_b == 0 and sb_c == 0
    summary_path = pack / "reports" / "early_stack_combined_nav_summary.json"
    if summary_path.exists():
        summary = load_json(summary_path)
        for key in ("E16_E18_E22", "E16_E18_E22_E45_E3"):
            meta = summary.get("variants", {}).get(key, {}).get("meta", {})
            if "exact_t1_ok" in meta:
                exact_ok = exact_ok and bool(meta["exact_t1_ok"])
            if "same_bar_fills" in meta:
                exact_ok = exact_ok and int(meta["same_bar_fills"]) == 0
    return {
        "id": "F2",
        "name": "exact_t1",
        "pass": bool(exact_ok),
        "same_bar_fills_baseline": sb_b,
        "same_bar_fills_challenger": sb_c,
    }


def f3_crisis_mdd(base: pd.DataFrame, chal: pd.DataFrame) -> dict:
    crisis = base["regime"].astype(str) == "Crisis"
    bm = mdd(base.loc[crisis, "nav"])
    cm = mdd(chal.loc[crisis, "nav"])
    improve_pp = (cm - bm) * 100.0
    return {
        "id": "F3",
        "name": "crisis_mdd",
        "pass": bool(improve_pp > 0),
        "baseline_crisis_path_mdd": bm,
        "challenger_crisis_path_mdd": cm,
        "improvement_pp": improve_pp,
    }


def f4_full_sample_mdd(base: pd.DataFrame, chal: pd.DataFrame) -> dict:
    bm = mdd(base["nav"])
    cm = mdd(chal["nav"])
    improve_pp = (cm - bm) * 100.0
    return {
        "id": "F4",
        "name": "full_sample_mdd",
        "pass": bool(cm >= bm - 1e-12),
        "baseline_mdd": bm,
        "challenger_mdd": cm,
        "improvement_pp": improve_pp,
    }


def f5_cagr_giveback(base: pd.DataFrame, chal: pd.DataFrame) -> dict:
    b_cagr = cagr_calendar(base["nav"], base["date"])
    c_cagr = cagr_calendar(chal["nav"], chal["date"])
    giveback_pp = (b_cagr - c_cagr) * 100.0
    within = giveback_pp <= CAGR_GIVEBACK_MAX_PP + 1e-9

    tmp = base.copy()
    tmp["year"] = tmp["date"].dt.year
    years = []
    for y, g in tmp.groupby("year"):
        if (g["regime"] == "Crisis").sum() < 5:
            continue
        idx = g.index
        years.append(
            {
                "year": int(y),
                "crisis_days": int((g["regime"] == "Crisis").sum()),
                "baseline_mdd": mdd(base.loc[idx, "nav"]),
                "challenger_mdd": mdd(chal.loc[idx, "nav"]),
            }
        )
    better = sum(1 for r in years if r["challenger_mdd"] > r["baseline_mdd"] + 1e-12)
    worse = sum(1 for r in years if r["challenger_mdd"] < r["baseline_mdd"] - 1e-12)
    crisis_path = f3_crisis_mdd(base, chal)
    full_mdd = f4_full_sample_mdd(base, chal)
    exception = (
        (not within)
        and crisis_path["improvement_pp"] >= F5_EXCEPTION_MIN_CRISIS_IMPROVE_PP
        and better >= F5_EXCEPTION_MIN_YEARS_BETTER
        and worse <= F5_EXCEPTION_MAX_YEARS_WORSE
        and (
            full_mdd["improvement_pp"] > 0
            if F5_EXCEPTION_REQUIRE_FULL_MDD_BETTER
            else True
        )
    )
    return {
        "id": "F5",
        "name": "cagr_giveback",
        "pass": bool(within or exception),
        "giveback_pp": giveback_pp,
        "max_pp": CAGR_GIVEBACK_MAX_PP,
        "baseline_cagr": b_cagr,
        "challenger_cagr": c_cagr,
        "within_limit": within,
        "crisis_dominates_exception": bool(exception),
        "exception_rules": {
            "min_crisis_improve_pp": F5_EXCEPTION_MIN_CRISIS_IMPROVE_PP,
            "min_years_better": F5_EXCEPTION_MIN_YEARS_BETTER,
            "max_years_worse": F5_EXCEPTION_MAX_YEARS_WORSE,
            "require_full_mdd_better": F5_EXCEPTION_REQUIRE_FULL_MDD_BETTER,
        },
        "crisis_years_better": better,
        "crisis_years_worse": worse,
        "crisis_years": years,
        "crisis_path_improvement_pp": crisis_path["improvement_pp"],
        "full_mdd_improvement_pp": full_mdd["improvement_pp"],
    }


def f6_no_retune() -> dict:
    mismatches = []
    for k, exp in LOCKED_E3_WINNER.items():
        got = E3_WINNER.get(k)
        if got != exp:
            mismatches.append({"key": k, "expected": exp, "got": got})
    status_path = ROOT / "research" / "v412e2e3" / "e3_status.json"
    status_mismatch = []
    if status_path.exists():
        winner = load_json(status_path).get("winner", {})
        for k, exp in LOCKED_E3_WINNER.items():
            if winner.get(k) != exp:
                status_mismatch.append({"key": k, "expected": exp, "got": winner.get(k)})
    ok = len(mismatches) == 0 and len(status_mismatch) == 0
    return {
        "id": "F6",
        "name": "no_retune",
        "pass": ok,
        "locked_e3": LOCKED_E3_WINNER,
        "module_e3_subset": {k: E3_WINNER.get(k) for k in LOCKED_E3_WINNER},
        "module_mismatches": mismatches,
        "e3_status_mismatches": status_mismatch,
        "notes": "Compares e45_crisis_core.E3_WINNER to locked e3_status.json winner.",
    }


def f7_live_untouched() -> dict:
    live_ok = DEFAULT_BOOKS_VERSION == DEFAULT_LIVE_BOOKS
    accidental = []
    for rel in (
        "scripts/e22_dividend_accounting.py",
        "scripts/e21_forward_pipeline.py",
        "forward/e21/live_config.json",
    ):
        p = ROOT / rel
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        for needle in ("E45_E3", "e45_equity_scale", "build_e45"):
            if needle in text:
                accidental.append(f"{rel}:{needle}")
    status = official_status_dict()
    status_ok = (
        status["E45_STITCH_STATUS"] == "DEFERRED"
        and status["E45_LIVE_AUTHORIZATION"] == "NO"
        and status["E45_GOVERNANCE_CLASS"] == "SOFT_FROZEN_CRITICAL"
    )
    ok = live_ok and status_ok and len(accidental) == 0
    return {
        "id": "F7",
        "name": "live_untouched",
        "pass": ok,
        "DEFAULT_BOOKS_VERSION": DEFAULT_BOOKS_VERSION,
        "required_default": DEFAULT_LIVE_BOOKS,
        "official_status": status,
        "accidental_live_markers": accidental,
        "notes": "Paper-only; live default and stitch/auth status must remain unchanged.",
    }


def evaluate(pack: Path) -> dict:
    refuse_superseded_pack(pack)
    base = pd.read_csv(pack / "outputs" / BASE_NAV)
    chal = pd.read_csv(pack / "outputs" / CHAL_NAV)
    base["date"] = pd.to_datetime(base["date"])
    chal["date"] = pd.to_datetime(chal["date"])
    if len(base) != len(chal):
        raise SystemExit(f"NAV length mismatch: base={len(base)} chal={len(chal)}")

    gates = [
        f1_artifact_honesty(pack),
        f2_exact_t1(pack),
        f3_crisis_mdd(base, chal),
        f4_full_sample_mdd(base, chal),
        f5_cagr_giveback(base, chal),
        f6_no_retune(),
        f7_live_untouched(),
    ]
    gate_map = {
        f"{g['id']}_{g['name']}": {k: v for k, v in g.items() if k != "id"} for g in gates
    }
    all_pass = all(g["pass"] for g in gates)

    full = {
        "baseline_cagr": cagr_calendar(base["nav"], base["date"]),
        "challenger_cagr": cagr_calendar(chal["nav"], chal["date"]),
        "baseline_mdd": mdd(base["nav"]),
        "challenger_mdd": mdd(chal["nav"]),
        "n_days": int(len(base)),
        "mean_e45_scale_baseline": float(base["e45_equity_scale"].mean()),
        "mean_e45_scale_challenger": float(chal["e45_equity_scale"].mean()),
    }
    full["cagr_giveback_pp"] = (full["baseline_cagr"] - full["challenger_cagr"]) * 100.0
    full["mdd_improvement_pp"] = (full["challenger_mdd"] - full["baseline_mdd"]) * 100.0
    crisis_gate = next(g for g in gates if g["id"] == "F3")

    return {
        "schema": "e45_feasibility_gates_f1_f7.v2",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "pack_dir": str(pack),
        "charter": "research/e45/E45_FEASIBILITY_CHARTER.md",
        "baseline": "E16_E18_E22_v2s",
        "challenger": "E16_E18_E22_v2s_E45_E3",
        "full_sample": full,
        "crisis_path": {
            "baseline_mdd": crisis_gate["baseline_crisis_path_mdd"],
            "challenger_mdd": crisis_gate["challenger_crisis_path_mdd"],
            "mdd_improvement_pp": crisis_gate["improvement_pp"],
        },
        "gates": gate_map,
        "all_pass": all_pass,
        "claim": claim_dict(),
        "verified_anchors": {
            "closest_lineage_val_mdd": VERIFIED_CLOSEST_LINEAGE_VAL_MDD,
            "e3_locked_val_mdd": VERIFIED_E3_LOCKED_VAL_MDD,
            "early_stack_plus_e45_e3_mdd": VERIFIED_EARLY_STACK_PLUS_E45_E3_MDD,
        },
        "official_status_unchanged": official_status_dict(),
        "seal_note": (
            "Gate evidence only. SEAL_LOCK.json / study verdict owned by "
            "e45_feasibility_seal_pack.py — this script must not overwrite them."
        ),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--pack-dir",
        type=Path,
        default=ROOT / "repro/e45-feasibility-study-regen-20260905",
    )
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    pack = args.pack_dir.resolve()
    payload = evaluate(pack)

    out = args.out or (ROOT / "reports" / "f1_f7_gates.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(dumps_json(payload), encoding="utf-8")
    pack_out = pack / "reports" / "f1_f7_gates.json"
    pack_out.parent.mkdir(parents=True, exist_ok=True)
    pack_out.write_text(dumps_json(payload), encoding="utf-8")

    print(
        dumps_json(
            {
                "all_pass": payload["all_pass"],
                "gates": {k: v["pass"] for k, v in payload["gates"].items()},
                "out": str(out),
                "pack_out": str(pack_out),
            }
        )
    )
    if not payload["all_pass"]:
        failed = [k for k, v in payload["gates"].items() if not v["pass"]]
        print(f"FAILED gates: {failed}", file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
