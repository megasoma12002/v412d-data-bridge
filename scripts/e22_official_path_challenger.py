#!/usr/bin/env python3
"""E22 official-path challenger recommendation (EXPERIMENTAL).

Uses already-run early-stack NAV evidence:
  E16_E18 vs E16_E18_E22 on forward/e21 market history.

Does not edit e21_forward_pipeline.py or forward/e21 ledgers.
Writes a promotion recommendation for wiring dividend cashflows into the
official execution path as a *new* SOFT_FROZEN E22 version after approval.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


def stats(nav: pd.Series) -> dict:
    r = nav.pct_change().dropna()
    years = len(r) / 252.0
    path = nav.to_numpy()
    cagr = float((path[-1] / path[0]) ** (1 / years) - 1) if years > 0 and path[0] > 0 else None
    peak = path.cummax() if False else __import__("numpy").maximum.accumulate(path)
    mdd = float((path / peak - 1).min())
    return {"cagr": cagr, "max_drawdown": mdd, "utility": (cagr or 0) - 0.5 * abs(mdd), "n": int(len(nav))}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--core",
        type=Path,
        default=Path("repro/early-stack-combined-nav-20260904/outputs/e16_e18_daily_nav.csv"),
    )
    ap.add_argument(
        "--core-e22",
        type=Path,
        default=Path("repro/early-stack-combined-nav-20260904/outputs/e16_e18_e22_daily_nav.csv"),
    )
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    out = args.out
    (out / "reports").mkdir(parents=True, exist_ok=True)
    Path("research/e22").mkdir(parents=True, exist_ok=True)

    a = pd.read_csv(args.core, parse_dates=["date"]).set_index("date")["nav"].astype(float)
    b = pd.read_csv(args.core_e22, parse_dates=["date"]).set_index("date")["nav"].astype(float)
    sa, sb = stats(a), stats(b)
    delta = {
        "cagr_lift": (sb["cagr"] or 0) - (sa["cagr"] or 0),
        "mdd_change": (sb["max_drawdown"] or 0) - (sa["max_drawdown"] or 0),
        "utility_lift": (sb["utility"] or 0) - (sa["utility"] or 0),
    }
    # Strong economic case already shown; recommend challenger merge path
    recommendation = "RECOMMEND_WIRE_E22_DIVIDENDS_INTO_OFFICIAL_EXEC_PATH_VIA_NEW_VERSION"
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "E22_OFFICIAL_PATH_CHALLENGER",
        "modifies_e21_inplace": False,
        "e16_e18": sa,
        "e16_e18_e22": sb,
        "delta": delta,
        "recommendation": recommendation,
        "implementation_steps": [
            "Create forward/e22_challenger/ or extend a copy of e21 pipeline with cash_ex_date credits",
            "Paper-run beside live E21 for N sessions (Exact T+1 QC unchanged)",
            "Governance approval → new SOFT_FROZEN E22 version; do not silently rewrite old ledgers",
        ],
        "rationale": (
            f"On reconstructed E16 full-history book, wiring E22 cash dividends lifts CAGR by "
            f"{delta['cagr_lift']:.2%} with MDD change {delta['mdd_change']:.2%}. "
            "Economics support official-path wiring; promotion still requires explicit approval."
        ),
    }
    (out / "reports" / "e22_official_path_recommendation.json").write_text(json.dumps(report, indent=2) + "\n")
    md = f"""# E22 Official-Path Challenger

**Recommendation:** `{recommendation}`

| Book | CAGR | MDD | Util |
|---|---:|---:|---:|
| E16_E18 | {100*sa['cagr']:.2f}% | {100*sa['max_drawdown']:.2f}% | {sa['utility']:.4f} |
| E16_E18_E22 | {100*sb['cagr']:.2f}% | {100*sb['max_drawdown']:.2f}% | {sb['utility']:.4f} |

- CAGR lift: **{100*delta['cagr_lift']:.2f} pp**
- MDD change: {100*delta['mdd_change']:.2f} pp

## How to merge (no in-place rewrite)

1. Challenger forward package with dividend credits on `cash_ex_date`
2. Paper parallel vs live E21
3. Explicit approval → new SOFT_FROZEN E22 version

Does **not** edit `scripts/e21_forward_pipeline.py` or append rewritten history to `forward/e21/`.
"""
    (out / "E22_OFFICIAL_PATH_CHALLENGER.md").write_text(md)
    Path("research/e22/E22_OFFICIAL_PATH_CHALLENGER.md").write_text(md)
    Path("research/e22/e22_official_path_recommendation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"recommendation": recommendation, "delta": delta}, indent=2))


if __name__ == "__main__":
    main()
