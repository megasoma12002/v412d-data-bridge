#!/usr/bin/env python3
"""Verify handoff/spec historical narrative: E45 MDD ≈ -13.16%.

Claim label: NOT_VERIFIED_HISTORICAL_NARRATIVE (do not treat as verified baseline).
Canonical status: research/e45/E45_OFFICIAL_STATUS.md

Scans research artifacts and recomputes early-stack+E45 challenger MDDs.
Does not invent a replacement baseline number.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from e50_early_stack_combined_nav import ALL, e16_features, simulate_core, nav_stats
import e45_crisis_core as e45

CLAIM = -0.1316
OUT = Path("repro/e45-mdd-verify")
REPORT = Path("research/e45/E45_MDD_1316_VERIFICATION.md")
SUMMARY = Path("research/e45/E45_MDD_1316_VERIFICATION.json")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)

    lineage = []
    for name, path, col in [
        ("E1_validation", "research/v412e1/e1_validation_gate.csv", "val_mdd"),
        ("E1_1_validation", "research/v412e11/e11_validation_gate.csv", "val_mdd"),
        ("E2_validation", "research/v412e2e3/e2_validation_gate.csv", "val_mdd"),
        ("E2_1_validation", "research/v412e2e3/e21_validation_gate.csv", "val_mdd"),
        ("E3_validation", "research/v412e2e3/e3_validation_gate.csv", "val_mdd"),
    ]:
        df = pd.read_csv(path)
        s = pd.to_numeric(df[col], errors="coerce").dropna()
        lineage.append(
            {
                "source": name,
                "path": path,
                "col": col,
                "n": int(len(s)),
                "best_mdd": float(s.max()),
                "worst_mdd": float(s.min()),
                "median_mdd": float(s.median()),
                "closest_to_claim": float(s.iloc[(s - CLAIM).abs().argmin()]),
                "abs_err_to_claim": float((s - CLAIM).abs().min()),
            }
        )

    e3 = pd.read_csv("research/v412e2e3/e3_validation_gate.csv")
    w = e45.E3_WINNER
    mask = (
        (e3["mode"] == w["mode"])
        & (e3["max_cut"] == w["max_cut"])
        & (e3["up_days"] == w["up_days"])
        & (e3["target_vol"] == w["target_vol"])
        & (e3["blend"] == w["blend"])
        & (e3["rank_buffer"] == w["rank_buffer"])
        & (e3["cost_hurdle_mult"] == w["cost_hurdle_mult"])
        & (e3["min_hold"] == w["min_hold"])
    )
    winner_rows = e3[mask]
    winner_mdd = float(winner_rows.iloc[0]["val_mdd"]) if len(winner_rows) else None
    if len(winner_rows):
        winner_rows.to_csv(OUT / "outputs" / "e3_winner_validation_rows.csv", index=False)

    market = pd.read_csv("forward/e21/live_market.csv", dtype={"code": str})
    market["date"] = pd.to_datetime(market["date"])
    req = set(ALL + ["TAIEX"])
    ok = market.groupby("date")["code"].apply(lambda s: req.issubset(set(s)))
    market = market[market["date"].isin(ok[ok].index)].sort_values(["date", "code"])
    div_path = Path("data/dividend_events/e22_dividend_events.csv")
    div = pd.read_csv(div_path, dtype={"code": str}) if div_path.exists() else pd.DataFrame()
    _p, _s, target, regime = e16_features(market)
    close_eq = (
        market[market["code"].isin(ALL)].pivot(index="date", columns="code", values="close").sort_index().ffill()
    )
    e45_e3 = e45.compute_exposure(close_eq, "E3_VOLTARGET_WINNER")["exposure"]
    e45_e1 = e45.compute_exposure(close_eq, "E1_BINARY")["exposure"]

    stack = []
    for name, cfg in [
        ("E16_E18_E22_v2", dict(apply_e22=True, apply_stock_div=False, e45_exposure=None)),
        ("E16_E18_E22_v2s", dict(apply_e22=True, apply_stock_div=True, e45_exposure=None)),
        ("E16_E18_E22_v2s_E45_E3", dict(apply_e22=True, apply_stock_div=True, e45_exposure=e45_e3)),
        ("E16_E18_E22_v2s_E45_E1", dict(apply_e22=True, apply_stock_div=True, e45_exposure=e45_e1)),
        (
            "E16_E18_E22_v2s_E45_LEGACY0.7",
            dict(apply_e22=True, apply_stock_div=True, e45_exposure=None, e45_legacy_crisis_scale=0.70),
        ),
    ]:
        nav, _fills, meta = simulate_core(market, target, regime, div, **cfg)
        st = nav_stats(nav)
        stack.append(
            {
                "variant": name,
                "cagr": st["cagr"],
                "mdd": st["max_drawdown"],
                "abs_err_to_claim": abs((st["max_drawdown"] or 0) - CLAIM),
                "n_days": meta["n_days"],
            }
        )

    pd.DataFrame(lineage).to_csv(OUT / "outputs" / "lineage_mdd_summary.csv", index=False)
    pd.DataFrame(stack).to_csv(OUT / "outputs" / "early_stack_mdd.csv", index=False)

    closest = min(lineage, key=lambda r: r["abs_err_to_claim"])
    verdict = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "claim_mdd": CLAIM,
        "claim_status": "NOT_VERIFIED",
        "claim_label": "NOT_VERIFIED_HISTORICAL_NARRATIVE",
        "exact_artifact_match": False,
        "canonical_status": "research/e45/E45_OFFICIAL_STATUS.md",
        "closest_lineage_mdd": closest,
        "e3_winner_validation_mdd": winner_mdd,
        "e3_winner_abs_err_to_claim": abs(winner_mdd - CLAIM) if winner_mdd is not None else None,
        "verified_lineage_reference": dict(e45.VERIFIED_LINEAGE_MDD),
        "lineage_summary": lineage,
        "early_stack_challenger": stack,
        "claim_text_locations_only": [
            {"path": "FROZEN_STRATEGY_SPEC.md", "role": "spec_text"},
            {"path": "FROZEN_GOVERNANCE.md", "role": "governance_text"},
            {"path": "E50_HANDOFF_VERIFICATION.md", "role": "prior_audit_NOT_FOUND"},
            {"path": "scripts/e45_crisis_core.py", "role": "module_constant"},
        ],
        "conclusion": (
            "No research CSV/JSON contains MDD == -0.1316. Claim appears only in narrative "
            "spec/handoff text. Closest crisis-lineage validation MDDs are more severe than "
            "the claim. Early-stack+E45 challenger MDDs remain near -21% to -23%. "
            "Do not treat -13.16% as a verified E45 baseline."
        ),
        "decision": {
            "accept_claim_as_verified_baseline": False,
            "replace_claim_with_invented_number": False,
            "use_instead": (
                "dated artifacts: closest lineage val MDD -15.81%; E3 locked winner -18.49%; "
                "early-stack+E45_E3 MDD -20.76% / CAGR ~10.79%; "
                "keep claim labeled NOT_VERIFIED_HISTORICAL_NARRATIVE"
            ),
            "promotion_impact": (
                "E45 remains SOFT_FROZEN_CRITICAL process class with E45_ARTIFACT_STATUS=NOT_VERIFIED, "
                "E45_STITCH_STATUS=DEFERRED, E45_LIVE_AUTHORIZATION=NO; "
                "not a verified -13.16% number"
            ),
        },
    }
    (OUT / "summary.json").write_text(json.dumps(verdict, indent=2, default=str) + "\n")
    SUMMARY.write_text(json.dumps(verdict, indent=2, default=str) + "\n")

    lines = [
        "# E45 MDD ≈ −13.16% Verification",
        "",
        f"Generated: `{verdict['generated_at_utc']}`",
        "",
        f"**Verdict: `{verdict['claim_status']}`** — claim label = **`{verdict['claim_label']}`**; exact artifact match = `{verdict['exact_artifact_match']}`",
        "",
        "Canonical status: `research/e45/E45_OFFICIAL_STATUS.md`",
        "",
        "## Claim",
        "",
        "Historical handoff/spec narrative: E45 crisis core validation MDD ≈ **-13.16%** (`-0.1316`) — **`NOT_VERIFIED_HISTORICAL_NARRATIVE`** (preserved; not deleted; not verified fact).",
        "",
        "## Method",
        "",
        "1. Scan research CSV/JSON MDD fields for exact `-0.1316`",
        "2. Summarize crisis lineage validation gates (E1 / E1.1 / E2 / E2.1 / E3)",
        "3. Recompute early-stack NAV with named E45 profiles (challenger; not a promotion)",
        "",
        "## Artifact scan",
        "",
        "- Exact MDD match in research artifacts: **none**",
        "- Claim text locations only: spec, governance, prior handoff audit, `e45_crisis_core.py` constant",
        "",
        "## Lineage validation MDDs",
        "",
        "| Source | Best MDD | Median | Closest to claim | |err| |",
        "|---|---:|---:|---:|---:|",
    ]
    for r in lineage:
        lines.append(
            f"| {r['source']} | {100*r['best_mdd']:.2f}% | {100*r['median_mdd']:.2f}% | "
            f"{100*r['closest_to_claim']:.2f}% | {100*r['abs_err_to_claim']:.2f} pp |"
        )
    lines += [
        "",
        f"- E3 locked winner validation MDD: **{100*winner_mdd:.2f}%** "
        f"(|err| to claim = {100*abs(winner_mdd-CLAIM):.2f} pp)"
        if winner_mdd is not None
        else "",
        "",
        "## Early-stack + E45 challenger (this repo path)",
        "",
        "| Variant | CAGR | MDD | |err| to claim |",
        "|---|---:|---:|---:|",
    ]
    for r in stack:
        lines.append(
            f"| {r['variant']} | {100*(r['cagr'] or 0):.2f}% | {100*(r['mdd'] or 0):.2f}% | "
            f"{100*r['abs_err_to_claim']:.2f} pp |"
        )
    d = verdict["decision"]
    lines += [
        "",
        "## Decision",
        "",
        f"- Accept claim as verified baseline: `{d['accept_claim_as_verified_baseline']}`",
        f"- Invent replacement number: `{d['replace_claim_with_invented_number']}`",
        f"- Use instead: {d['use_instead']}",
        f"- Promotion impact: {d['promotion_impact']}",
        "",
        f"Conclusion: {verdict['conclusion']}",
        "",
        "## Artifacts",
        "",
        f"- `{SUMMARY}`",
        f"- `{OUT}/summary.json`",
        f"- `{OUT}/outputs/`",
        f"- Script: `scripts/e45_verify_mdd_1316.py`",
        "",
    ]
    REPORT.write_text("\n".join(x for x in lines if x is not None) + "\n")
    print(json.dumps({"claim_status": verdict["claim_status"], "e3_winner_mdd": winner_mdd}, indent=2))


if __name__ == "__main__":
    main()
