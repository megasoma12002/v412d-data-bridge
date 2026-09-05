#!/usr/bin/env python3
"""One-shot held-out for locked FIN_CAP_50 (RESEARCH_ONLY).

Reads OOF summary; does NOT retune caps. Held-out window: 2019-01-01 → latest.
Predeclared held-out pass (frozen before this script runs conceptually with OOF lock):
  - MDD improve vs BASE held-out ≥ 1.0 pp
  - CAGR giveback vs BASE held-out ≤ 3.0 pp
  - Finance max weight on held-out ≤ fin_hi
Only PASS_HELDOUT may propose a live E16 clip change (still requires explicit promote).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

OOF = Path("repro/gap-cagr-finance-concentration/fin_cap_oof/reports/fin_cap_oof_summary.json")
OUT = Path("repro/gap-cagr-finance-concentration/fin_cap_oof")
MDD_IMPROVE_MIN = 0.01
CAGR_GIVEBACK_MAX = 0.03


def main() -> None:
    oof = json.loads(OOF.read_text())
    if oof.get("research_decision") != "OOF_FIN_CAP_PASS_READY_FOR_HELDOUT":
        raise SystemExit(f"OOF not ready: {oof.get('research_decision')}")
    locked = oof["recommended"]
    if locked["name"] != "FIN_CAP_50":
        # Still evaluate whatever OOF locked; do not swap.
        pass
    name = locked["name"]
    base_h = oof["baseline"]["heldout"]
    # find challenger held-out row
    ch = next(c for c in oof["challengers"] if c["name"] == name)
    mdd_improve = abs(base_h["max_drawdown"] or 9) - abs(ch["heldout_mdd"] or 9)
    cagr_giveback = (base_h["cagr"] or 0) - (ch["heldout_cagr"] or 0)

    # weight check on held-out: reload from targets file
    import pandas as pd

    tgt = pd.read_csv(OUT / "outputs" / f"{name.lower()}_targets.csv", index_col=0, parse_dates=True)
    held = tgt.loc[tgt.index >= "2019-01-01", "Financial"]
    cap_ok = bool(held.max() <= locked["fin_hi"] + 1e-6)

    pass_held = bool(
        cap_ok
        and mdd_improve >= MDD_IMPROVE_MIN
        and cagr_giveback <= CAGR_GIVEBACK_MAX
    )
    decision = "PASS_HELDOUT_FIN_CAP" if pass_held else "STOP_FIN_CAP_HELDOUT"

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "RESEARCH_ONLY",
        "live_wire": False,
        "locked_from_oof": locked,
        "heldout_window": "2019-01-01_to_latest",
        "predeclared_heldout_rule": {
            "mdd_improve_min_pp": MDD_IMPROVE_MIN * 100,
            "cagr_giveback_max_pp": CAGR_GIVEBACK_MAX * 100,
            "finance_max_le_fin_hi": True,
        },
        "baseline_heldout": base_h,
        "challenger_heldout": {
            "name": name,
            "cagr": ch["heldout_cagr"],
            "max_drawdown": ch["heldout_mdd"],
            "mean_financial": float(held.mean()),
            "max_financial": float(held.max()),
            "cap_ok": cap_ok,
            "mdd_improve_pp": mdd_improve * 100,
            "cagr_giveback_pp": cagr_giveback * 100,
        },
        "pass_heldout": pass_held,
        "research_decision": decision,
        "promotion": {
            "allowed_now": False,
            "note": (
                "PASS_HELDOUT only unlocks a *proposal* to change live E16 Financial clip. "
                "Requires explicit promote PR; does not auto-edit Soft-Frozen live."
            ),
        },
        "next_if_pass": "Optional promote PR: E16 FIN clip → [0.35,0.50] as named challenger cutover; keep BASE ledger for comparison",
        "next_if_stop": "Keep live E16; stop FIN_CAP axis; do not retune on sealed",
    }
    (OUT / "reports" / "fin_cap_heldout_decision.json").write_text(json.dumps(summary, indent=2) + "\n")
    research = Path("research/gaps")
    (research / "FIN_CAP_HELDOUT_DECISION.json").write_text(json.dumps(summary, indent=2) + "\n")

    lines = [
        "# FIN_CAP Held-out Decision (locked FIN_CAP_50)",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        "",
        f"## Decision: `{decision}`",
        "",
        f"Locked from OOF: `{name}` fin∈[{locked['fin_lo']},{locked['fin_hi']}]",
        "",
        "| | CAGR | MDD |",
        "|---|---:|---:|",
        f"| BASE held-out | {base_h['cagr']} | {base_h['max_drawdown']} |",
        f"| {name} held-out | {ch['heldout_cagr']} | {ch['heldout_mdd']} |",
        "",
        f"- MDD improve: `{mdd_improve*100:.2f}` pp (need ≥{MDD_IMPROVE_MIN*100:.0f})",
        f"- CAGR giveback: `{cagr_giveback*100:.2f}` pp (need ≤{CAGR_GIVEBACK_MAX*100:.0f})",
        f"- Finance max on held-out: `{float(held.max()):.3f}` (cap_ok={cap_ok})",
        "",
    ]
    if pass_held:
        lines += [
            "Held-out **PASS**. Still **not live**. Explicit promote PR required to change E16 clips.",
            "Recommend keeping BASE_E16 paper ledger beside any cutover.",
            "",
        ]
    else:
        lines += [
            "Held-out **FAIL**. `STOP_FIN_CAP_HELDOUT` — keep live E16. Do not retune.",
            "",
        ]
    lines += ["Label: `RESEARCH_FIN_CAP_HELDOUT__NO_LIVE_WIRE`", ""]
    md = "\n".join(lines)
    (OUT / "FIN_CAP_HELDOUT.md").write_text(md)
    (research / "FIN_CAP_HELDOUT.md").write_text(md)
    print(json.dumps({"research_decision": decision, "mdd_improve_pp": mdd_improve * 100,
                      "cagr_giveback_pp": cagr_giveback * 100}, indent=2))


if __name__ == "__main__":
    main()
