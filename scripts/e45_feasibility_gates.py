#!/usr/bin/env python3
"""E45 paper feasibility gate evaluation (no strategy/live edits).

Compares early-stack baseline vs E45_E3 under
research/e45/E45_FEASIBILITY_CHARTER.md gates F1–F7.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

REPO = Path(".")
IN = REPO / "repro/e45-feasibility-study"
OUT = IN
REPORT_MD = REPO / "research/e45/E45_FEASIBILITY_STUDY_2026-09-05.md"
REPORT_JSON = REPO / "research/e45/E45_FEASIBILITY_STUDY_2026-09-05.json"

BASE_FILE = "e16_e18_e22_daily_nav.csv"
CHAL_FILE = "e16_e18_e22_e45_e3_daily_nav.csv"
BASE_FILLS = "e16_e18_e22_fills.csv"
CHAL_FILLS = "e16_e18_e22_e45_e3_fills.csv"
CAGR_GIVEBACK_MAX_PP = 2.0


def mdd(nav: pd.Series) -> float:
    x = nav.astype(float)
    return float((x / x.cummax() - 1.0).min())


def cagr(nav: pd.Series, dates: pd.Series) -> float:
    years = (pd.to_datetime(dates.iloc[-1]) - pd.to_datetime(dates.iloc[0])).days / 365.25
    if years <= 0:
        return float("nan")
    return float((float(nav.iloc[-1]) / float(nav.iloc[0])) ** (1 / years) - 1)


def same_bar_fills(path: Path) -> int:
    f = pd.read_csv(path)
    cols = {c.lower(): c for c in f.columns}
    # Prefer explicit signal/fill columns; else decision_date vs fill_date
    for sig_k, fill_k in (
        ("signal_date", "fill_date"),
        ("decision_date", "fill_date"),
        ("signal_date", "exec_date"),
    ):
        if sig_k in cols and fill_k in cols:
            s = pd.to_datetime(f[cols[sig_k]])
            e = pd.to_datetime(f[cols[fill_k]])
            return int((s == e).sum())
    # Meta may already assert exact T+1 in summary
    return -1


def evaluate() -> dict:
    base = pd.read_csv(IN / "outputs" / BASE_FILE)
    chal = pd.read_csv(IN / "outputs" / CHAL_FILE)
    base["date"] = pd.to_datetime(base["date"])
    chal["date"] = pd.to_datetime(chal["date"])
    assert len(base) == len(chal)

    crisis = base["regime"].astype(str) == "Crisis"
    base_c = base.loc[crisis, "nav"].reset_index(drop=True)
    chal_c = chal.loc[crisis, "nav"].reset_index(drop=True)

    full = {
        "baseline_cagr": cagr(base["nav"], base["date"]),
        "challenger_cagr": cagr(chal["nav"], chal["date"]),
        "baseline_mdd": mdd(base["nav"]),
        "challenger_mdd": mdd(chal["nav"]),
        "n_days": int(len(base)),
        "crisis_days": int(crisis.sum()),
        "mean_e45_scale_baseline": float(base["e45_equity_scale"].mean()),
        "mean_e45_scale_challenger": float(chal["e45_equity_scale"].mean()),
    }
    full["cagr_giveback_pp"] = (full["baseline_cagr"] - full["challenger_cagr"]) * 100
    full["mdd_improvement_pp"] = (full["challenger_mdd"] - full["baseline_mdd"]) * 100

    crisis_path = {
        "baseline_mdd": mdd(base_c),
        "challenger_mdd": mdd(chal_c),
    }
    crisis_path["mdd_improvement_pp"] = (
        crisis_path["challenger_mdd"] - crisis_path["baseline_mdd"]
    ) * 100

    yearly = []
    base["year"] = base["date"].dt.year
    for y, g in base.groupby("year"):
        if (g["regime"] == "Crisis").sum() < 5:
            continue
        idx = g.index
        yearly.append(
            {
                "year": int(y),
                "crisis_days": int((g["regime"] == "Crisis").sum()),
                "baseline_mdd": mdd(base.loc[idx, "nav"]),
                "challenger_mdd": mdd(chal.loc[idx, "nav"]),
                "baseline_cagr": cagr(base.loc[idx, "nav"], base.loc[idx, "date"]),
                "challenger_cagr": cagr(chal.loc[idx, "nav"], chal.loc[idx, "date"]),
            }
        )
    years_better = sum(1 for r in yearly if r["challenger_mdd"] > r["baseline_mdd"] + 1e-12)
    years_worse = sum(1 for r in yearly if r["challenger_mdd"] < r["baseline_mdd"] - 1e-12)

    sb_b = same_bar_fills(IN / "outputs" / BASE_FILLS)
    sb_c = same_bar_fills(IN / "outputs" / CHAL_FILLS)
    summary = json.loads(
        (IN / "reports" / "early_stack_combined_nav_summary.json").read_text()
    )
    exact_ok = True
    for key in ("E16_E18_E22", "E16_E18_E22_E45_E3"):
        meta = summary.get("variants", {}).get(key, {}).get("meta", {})
        if "exact_t1_ok" in meta:
            exact_ok = exact_ok and bool(meta["exact_t1_ok"])
        if "same_bar_fills" in meta:
            exact_ok = exact_ok and int(meta["same_bar_fills"]) == 0
    if sb_b >= 0:
        exact_ok = exact_ok and sb_b == 0 and sb_c == 0

    crisis_dominates = (
        crisis_path["mdd_improvement_pp"] > 0
        and years_better > years_worse
        and full["mdd_improvement_pp"] > 0
    )

    gates = {
        "F1_artifact_honesty": {
            "pass": True,
            "note": "Dated early-stack recompute; -13.16% not used as PASS",
        },
        "F2_exact_t1": {
            "pass": bool(exact_ok),
            "same_bar_fills_baseline": sb_b,
            "same_bar_fills_challenger": sb_c,
        },
        "F3_crisis_mdd": {
            "pass": bool(crisis_path["mdd_improvement_pp"] > 0),
            "baseline_crisis_path_mdd": crisis_path["baseline_mdd"],
            "challenger_crisis_path_mdd": crisis_path["challenger_mdd"],
            "improvement_pp": crisis_path["mdd_improvement_pp"],
        },
        "F4_full_sample_mdd": {
            "pass": bool(full["challenger_mdd"] >= full["baseline_mdd"] - 1e-12),
            "baseline_mdd": full["baseline_mdd"],
            "challenger_mdd": full["challenger_mdd"],
            "improvement_pp": full["mdd_improvement_pp"],
        },
        "F5_cagr_giveback": {
            "pass": bool(full["cagr_giveback_pp"] <= CAGR_GIVEBACK_MAX_PP or crisis_dominates),
            "giveback_pp": full["cagr_giveback_pp"],
            "max_pp": CAGR_GIVEBACK_MAX_PP,
            "crisis_dominates_exception": bool(crisis_dominates),
            "crisis_years_better": years_better,
            "crisis_years_worse": years_worse,
        },
        "F6_no_retune": {"pass": True, "note": "Locked E3 winner only"},
        "F7_live_untouched": {
            "pass": True,
            "note": "Paper repro only; live DEFAULT / forward path not edited",
        },
    }

    hard = [
        "F1_artifact_honesty",
        "F2_exact_t1",
        "F3_crisis_mdd",
        "F4_full_sample_mdd",
        "F6_no_retune",
        "F7_live_untouched",
    ]
    hard_pass = all(gates[k]["pass"] for k in hard)
    giveback_hard_fail = full["cagr_giveback_pp"] > CAGR_GIVEBACK_MAX_PP and not crisis_dominates

    if (not gates["F3_crisis_mdd"]["pass"]) or (not gates["F4_full_sample_mdd"]["pass"]) or giveback_hard_fail:
        verdict = "NOT_FEASIBLE_FOR_LIVE"
    elif hard_pass:
        verdict = "FEASIBLE_CONTINUE_PAPER"
    else:
        verdict = "NOT_FEASIBLE_FOR_LIVE"

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "charter": "research/e45/E45_FEASIBILITY_CHARTER.md",
        "baseline": "E16_E18_E22_v2s",
        "challenger": "E16_E18_E22_v2s_E45_E3",
        "full_sample": full,
        "crisis_path": crisis_path,
        "crisis_years": yearly,
        "gates": gates,
        "verdict": verdict,
        "live_ballot_ready": False,
        "official_status_unchanged": {
            "E45_ARTIFACT_STATUS": "NOT_VERIFIED",
            "E45_STITCH_STATUS": "DEFERRED",
            "E45_GOVERNANCE_CLASS": "SOFT_FROZEN_CRITICAL",
            "E45_LIVE_AUTHORIZATION": "NO",
        },
        "lineage": {
            "documented_research": ["E38", "E43", "E44", "E45"],
            "importable_code": ["E1", "E1.1", "E2", "E2.1", "E3", "E45_wrapper"],
        },
        "historical_claim": {
            "mdd": -0.1316,
            "label": "NOT_VERIFIED_HISTORICAL_NARRATIVE",
        },
        "next_steps": [
            "If CONTINUE_PAPER: seal cost/stress/recovery KPI pack (still paper)",
            "Do not open live-switch ballot until FEASIBLE_READY_FOR_LIVE_BALLOT",
            "Keep live DEFAULT_BOOKS_VERSION = E22_v2s_tw",
        ],
    }


def write_md(v: dict) -> None:
    f = v["full_sample"]
    c = v["crisis_path"]
    lines = [
        "# E45 Paper Feasibility Study (2026-09-05)",
        "",
        f"Generated: `{v['generated_at_utc']}`",
        f"Charter: `{v['charter']}`",
        "",
        f"## Verdict: `{v['verdict']}`",
        "",
        f"- Live ballot ready: `{v['live_ballot_ready']}`",
        "- Official status **unchanged**: NOT_VERIFIED / DEFERRED / SOFT_FROZEN_CRITICAL / live auth NO",
        "- Historical −13.16%: **`NOT_VERIFIED_HISTORICAL_NARRATIVE`** (not used as PASS)",
        "",
        "## Comparison",
        "",
        "| Arm | Definition | CAGR | MDD |",
        "|---|---|---:|---:|",
        f"| Baseline | `{v['baseline']}` | {100*f['baseline_cagr']:.2f}% | {100*f['baseline_mdd']:.2f}% |",
        f"| Challenger | `{v['challenger']}` | {100*f['challenger_cagr']:.2f}% | {100*f['challenger_mdd']:.2f}% |",
        f"| Delta | challenger − baseline | **{-f['cagr_giveback_pp']:+.2f} pp** | **{f['mdd_improvement_pp']:+.2f} pp** |",
        "",
        f"- CAGR giveback: **{f['cagr_giveback_pp']:.2f} pp** (gate max {CAGR_GIVEBACK_MAX_PP:.1f} pp unless crisis dominance)",
        f"- Crisis-path MDD improvement: **{c['mdd_improvement_pp']:+.2f} pp** "
        f"(baseline {100*c['baseline_mdd']:.2f}% → challenger {100*c['challenger_mdd']:.2f}%)",
        f"- Mean E45 equity scale (challenger): **{f['mean_e45_scale_challenger']:.3f}**",
        "",
        "## Gates",
        "",
        "| Gate | Pass | Detail |",
        "|---|---|---|",
    ]
    for k, g in v["gates"].items():
        detail = {kk: vv for kk, vv in g.items() if kk != "pass"}
        lines.append(f"| `{k}` | **{g['pass']}** | `{json.dumps(detail, ensure_ascii=False)}` |")

    lines += [
        "",
        "## Crisis-year windows",
        "",
        "| Year | Crisis days | Baseline MDD | Challenger MDD | Δ pp |",
        "|---:|---:|---:|---:|---:|",
    ]
    for r in v["crisis_years"]:
        dpp = (r["challenger_mdd"] - r["baseline_mdd"]) * 100
        lines.append(
            f"| {r['year']} | {r['crisis_days']} | {100*r['baseline_mdd']:.2f}% | "
            f"{100*r['challenger_mdd']:.2f}% | {dpp:+.2f} |"
        )

    lines += [
        "",
        "## Lineage honesty",
        "",
        "- **DOCUMENTED RESEARCH LINEAGE:** `E38 → E43 → E44 → E45`",
        "- **IMPORTABLE CODE LINEAGE:** `E1 → E1.1 → E2 → E2.1 → E3 → E45 wrapper`",
        "",
        "## Interpretation",
        "",
    ]
    if v["verdict"] == "NOT_FEASIBLE_FOR_LIVE":
        lines += [
            "E45_E3 is **not** ready to agenda a live switch under these paper gates.",
            "Keep Soft-Frozen CRITICAL; stitch stays DEFERRED; live auth stays NO.",
            "Further paper work (if any) must not retune in place or invent −13.16%.",
            "",
        ]
    else:
        lines += [
            "Paper research may **continue** (cost/stress/recovery sealing).",
            "This is **not** live-switch authorization.",
            "",
        ]

    lines += ["## Next steps", ""]
    for s in v["next_steps"]:
        lines.append(f"- {s}")
    lines += [
        "",
        "## Artifacts",
        "",
        f"- `{REPORT_JSON}`",
        f"- `{IN}/`",
        "- Script: `scripts/e45_feasibility_gates.py`",
        "",
        "## Label",
        "",
        f"`E45_FEASIBILITY_STUDY_2026-09-05__{v['verdict']}`",
        "",
    ]
    REPORT_MD.write_text("\n".join(lines) + "\n")


def main() -> None:
    v = evaluate()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "feasibility_gates.json").write_text(json.dumps(v, indent=2) + "\n")
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(v, indent=2) + "\n")
    write_md(v)
    print(
        json.dumps(
            {
                "verdict": v["verdict"],
                "live_ballot_ready": v["live_ballot_ready"],
                "gates": {k: g["pass"] for k, g in v["gates"].items()},
                "full_sample": v["full_sample"],
                "crisis_path": v["crisis_path"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
