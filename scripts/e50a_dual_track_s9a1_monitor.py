#!/usr/bin/env python3
"""Track A — S9A1 paper/monitor harness (Option-2).

Default: bootstrap KPI dashboard from locked Stage-9A held-out archive.
Optional --refresh: re-run e50a3r1_stage9a_s9a1_heldout.py (expensive; needs /tmp/a*).

EXPERIMENTAL / RESEARCH ONLY. No live wire. No cut retune.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARCHIVE = ROOT / "repro/e50a3r1-turnover-diagnosis-20260903"
OUT = ROOT / "repro/e50a-dual-track/track_a_s9a1_monitor"
REPORT = ROOT / "research/e50a/TRACK_A_S9A1_MONITOR_STATUS.md"


def kpi_row(tag: str, d: dict) -> dict:
    return {
        "window": tag,
        "cagr": d.get("cagr"),
        "max_drawdown": d.get("max_drawdown"),
        "utility": d.get("utility"),
        "average_daily_turnover": d.get("average_daily_turnover"),
        "bootstrap": d.get("block_bootstrap_positive_probability"),
        "turnover_gate_pass": d.get("turnover_gate_pass"),
        "bootstrap_gate_pass": d.get("bootstrap_gate_pass"),
        "beats_market_proxy": d.get("beats_market_proxy"),
        "stress_flag_share": d.get("stress_flag_share"),
        "stress_mean_excess": d.get("s_crisis_mean_excess"),
        "stress_compound": d.get("s_crisis_strategy_compound"),
    }


def write_status(archive_decision: dict, mode: str) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)
    locked = archive_decision.get("locked_config") or {}
    val = archive_decision.get("validation_2019_2022") or {}
    sealed = archive_decision.get("sealed_2023_latest") or {}
    c4_val = (archive_decision.get("reference_c4") or {}).get("validation_2019_2022") or {}
    # stage9a file may nest C4 under different keys — fall back to known baseline table
    if not c4_val:
        c4_val = {
            "cagr": 0.217,
            "max_drawdown": -0.319,
            "block_bootstrap_positive_probability": 0.559,
            "s_crisis_mean_excess": 0.00035,
            "note": "runbook_baseline_snapshot_approx_if_missing",
        }

    stress_edge_val = None
    if val.get("s_crisis_mean_excess") is not None and c4_val.get("s_crisis_mean_excess") is not None:
        stress_edge_val = float(val["s_crisis_mean_excess"]) - float(c4_val["s_crisis_mean_excess"])

    status = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "track": "A_S9A1_PAPER_MONITOR",
        "mode": mode,
        "governance": "OPTION2_S9A1_PAPER_MONITOR",
        "live_wire": False,
        "retune_allowed": False,
        "locked_config": locked,
        "research_decision_at_lock": archive_decision.get("research_decision"),
        "kpi_s9a1": {
            "validation_2019_2022": kpi_row("val", val),
            "sealed_2023_latest": kpi_row("sealed", sealed),
        },
        "kpi_ref_c4_baseline": c4_val,
        "monitor_alerts": {
            "stress_mean_excess_edge_vs_c4_val": stress_edge_val,
            "stress_edge_positive": (stress_edge_val is not None and stress_edge_val > 0),
            "bootstrap_soft_warning_val": bool(
                (val.get("block_bootstrap_positive_probability") or 0) < 0.70
            ),
            "pause_rule": "If stress edge vs C4 negative for two consecutive review periods → pause paper overlay; do not retune.",
        },
        "cadence": "month_end_or_panel_refresh",
        "next_review_actions": [
            "Rebuild REF_C4 and PAPER_S9A1 NAVs (see runbook)",
            "Fill KPI table vs prior review",
            "If stress edge flipped negative two periods → pause and reopen research (Track B)",
        ],
    }
    (OUT / "monitor_status.json").write_text(json.dumps(status, indent=2, default=str) + "\n")
    SUMMARY = ROOT / "research/e50a/TRACK_A_S9A1_MONITOR_STATUS.json"
    SUMMARY.write_text(json.dumps(status, indent=2, default=str) + "\n")

    lines = [
        "# Track A — S9A1 Paper Monitor Status",
        "",
        f"Generated: `{status['generated_at_utc']}`",
        f"Mode: `{mode}`",
        "",
        "**Paper/monitor only.** No live wire. No cut retune.",
        "",
        "## Locked config",
        "",
        "```json",
        json.dumps(locked, indent=2),
        "```",
        "",
        f"Lock decision: `{archive_decision.get('research_decision')}`",
        "",
        "## KPI snapshot (S9A1)",
        "",
        "| Window | CAGR | MDD | TO | Boot | Stress share | Stress mean excess |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for tag, block in status["kpi_s9a1"].items():
        lines.append(
            f"| {tag} | {100*(block['cagr'] or 0):.2f}% | {100*(block['max_drawdown'] or 0):.2f}% | "
            f"{100*(block['average_daily_turnover'] or 0):.2f}% | {block['bootstrap']} | "
            f"{100*(block['stress_flag_share'] or 0):.1f}% | {block['stress_mean_excess']} |"
        )
    lines += [
        "",
        "## Monitor alerts",
        "",
        f"- Stress edge vs C4 (val): `{stress_edge_val}` (positive={status['monitor_alerts']['stress_edge_positive']})",
        f"- Bootstrap soft warning (val &lt; 0.70): `{status['monitor_alerts']['bootstrap_soft_warning_val']}`",
        f"- Pause rule: {status['monitor_alerts']['pause_rule']}",
        "",
        "## Artifacts",
        "",
        f"- `{OUT / 'monitor_status.json'}`",
        f"- Runbook: `repro/e50a3r1-turnover-diagnosis-20260903/S9A1_PAPER_MONITOR_RUNBOOK.md`",
        "",
    ]
    REPORT.write_text("\n".join(lines) + "\n")
    return status


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive-root", type=Path, default=DEFAULT_ARCHIVE)
    ap.add_argument("--refresh", action="store_true", help="Re-run Stage-9A S9A1 held-out (slow)")
    ap.add_argument("--panel", default="/tmp/a2/causal_factor_panel.parquet")
    ap.add_argument("--labels", default="/tmp/a2/forward_labels_research_only.parquet")
    ap.add_argument("--prices", default="/tmp/a0/point_in_time_universe.csv")
    ap.add_argument("--actions", default="/tmp/a1/corporate_action_ledger.csv.gz")
    ap.add_argument("--a2-qc", default="/tmp/a2/qc_status.json")
    args = ap.parse_args()

    decision_path = args.archive_root / "reports" / "stage9a_s9a1_heldout_decision.json"
    if not decision_path.exists():
        raise SystemExit(f"missing archive decision: {decision_path}")

    mode = "ARCHIVE_BOOTSTRAP"
    if args.refresh:
        cmd = [
            sys.executable,
            str(ROOT / "scripts" / "e50a3r1_stage9a_s9a1_heldout.py"),
            "--panel", args.panel,
            "--labels", args.labels,
            "--prices", args.prices,
            "--actions", args.actions,
            "--a2-qc", args.a2_qc,
            "--stage9a-summary",
            str(args.archive_root / "reports" / "stage9a_e45c1_freeze_orth_oof_summary.json"),
            "--out", str(args.archive_root),
        ]
        print("refresh:", " ".join(cmd), flush=True)
        subprocess.check_call(cmd, cwd=str(ROOT), env={**dict(**{k: v for k, v in __import__("os").environ.items()}), "PYTHONPATH": str(ROOT / "scripts")})
        mode = "REFRESH_HELDOUT_RERUN"

    decision = json.loads(decision_path.read_text())
    if "c4_full_reference_validation" in decision:
        decision["reference_c4"] = {
            "validation_2019_2022": {
                **decision["c4_full_reference_validation"],
                "s_crisis_mean_excess": (decision.get("stress_vs_c4_validation") or {}).get("c4_stress_ex"),
            }
        }
    status = write_status(decision, mode)
    print(json.dumps({"mode": mode, "decision": status["research_decision_at_lock"], "out": str(OUT)}, indent=2))


if __name__ == "__main__":
    main()
