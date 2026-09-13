#!/usr/bin/env python3
"""Ops month-end paper pack — RESEARCH / OPS cadence only.

Runs (by default, fast path):
  1) L4 month-end monitor
  2) FIN50 month-end monitor
  3) Track A S9A1 archive monitor
  4) Live ↔ Soft-Frozen paper BASE recon

Optional --refresh-ledgers also rebuilds L4/FIN50/BLEND_025/E45 dual-paper ledgers
(slow; Exact T+1 full history).

Never edits Soft-Frozen clip.
Never live-wires challengers.
Never rewrites forward/e21 history.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "research/ops"
SUMMARY_JSON = OUT_DIR / "MONTH_END_PAPER_PACK.json"
SUMMARY_MD = OUT_DIR / "MONTH_END_PAPER_PACK.md"

sys.path.insert(0, str(ROOT / "scripts"))
from e16_soft_frozen_base import SOFT_FROZEN_FIN_CLIP

CLIP_TXT = f"[{SOFT_FROZEN_FIN_CLIP[0]:.2f}, {SOFT_FROZEN_FIN_CLIP[1]:.2f}]"

STEPS_MONITOR = [
    ("l4_month_end", ["python3", "scripts/e16_l4_dd_path_month_end_monitor.py"]),
    ("fincap50_month_end", ["python3", "scripts/e16_fincap50_month_end_monitor.py"]),
    ("blend025_month_end", ["python3", "scripts/e16_blend025_month_end_monitor.py"]),
    ("e45_month_end", ["python3", "scripts/e45_month_end_monitor.py"]),
    ("e45_blend025_month_end", ["python3", "scripts/e45_blend025_month_end_monitor.py"]),
    ("e45_blend005_month_end", ["python3", "scripts/e45_blend005_month_end_monitor.py"]),
    ("e45_sleeve_local_month_end", ["python3", "scripts/e45_sleeve_local_month_end_monitor.py"]),
    ("e45_m2_bil_fx_month_end", ["python3", "scripts/e45_m2_bil_fx_month_end_monitor.py"]),
    (
        "fin_within_sleeve_month_end",
        ["python3", "scripts/e16_fin_within_sleeve_month_end_monitor.py"],
    ),
    (
        "fin_priv_native_month_end",
        ["python3", "scripts/e16_fin_priv_native_month_end_monitor.py"],
    ),
    (
        "soft_assist_month_end",
        ["python3", "scripts/e16_soft_assist_month_end_monitor.py"],
    ),
    (
        "sleeve_tilt_month_end",
        ["python3", "scripts/e16_sleeve_tilt_month_end_monitor.py"],
    ),
    (
        "fuse_additive_month_end",
        ["python3", "scripts/e16_fuse_additive_month_end_monitor.py"],
    ),
    (
        "e45_defend_handoff_month_end",
        ["python3", "scripts/e45_defend_handoff_month_end_monitor.py"],
    ),
    (
        "soft_sleeve_observe_overlap",
        ["python3", "scripts/e16_soft_sleeve_observe_overlap.py"],
    ),
    ("track_a_s9a1", ["python3", "scripts/e50a_dual_track_s9a1_monitor.py"]),
    ("live_paper_recon", ["python3", "scripts/e21_live_vs_paper_recon.py"]),
    ("e22_data_quality_kpi", ["python3", "scripts/e22_data_quality_kpi.py"]),
    ("e22_gap6_fidelity_kpi", ["python3", "scripts/e22_gap6_fidelity_kpi.py"]),
    ("data_source_shadow_reconcile", ["python3", "scripts/data_source_shadow_reconcile.py"]),
    ("data_source_phase_c_probes", ["python3", "scripts/data_source_phase_c_probes.py"]),
    ("data_source_resilience_kpi", ["python3", "scripts/data_source_resilience_kpi.py"]),
    (
        "fincap50_sealed_cagr_charter_screen",
        ["python3", "scripts/fincap50_sealed_cagr_charter_screen.py"],
    ),
    ("ops_alert_scan", ["python3", "scripts/ops_alert_scan.py", "--report-only"]),  # swapped in main if fail-on-critical
]

STEPS_REFRESH = [
    ("l4_dual_paper_ledgers", ["python3", "scripts/e16_l4_dd_path_dual_paper_ledgers.py"]),
    ("fincap50_dual_paper_ledgers", ["python3", "scripts/e16_fincap50_dual_paper_ledgers.py"]),
    ("blend025_dual_paper_ledgers", ["python3", "scripts/e16_blend025_dual_paper_ledgers.py"]),
    ("e45_dual_paper_ledgers", ["python3", "scripts/e45_dual_paper_ledgers.py"]),
    ("e45_blend025_dual_paper_ledgers", ["python3", "scripts/e45_blend025_dual_paper_ledgers.py"]),
    ("e45_blend005_dual_paper_ledgers", ["python3", "scripts/e45_blend005_dual_paper_ledgers.py"]),
    ("e45_sleeve_local_dual_paper_ledgers", ["python3", "scripts/e45_sleeve_local_dual_paper_ledgers.py"]),
    ("e45_m2_bil_fx_dual_paper_ledgers", ["python3", "scripts/e45_m2_bil_fx_dual_paper_ledgers.py"]),
    (
        "fin_within_sleeve_dual_paper_ledgers",
        ["python3", "scripts/e16_fin_within_sleeve_dual_paper_ledgers.py"],
    ),
    (
        "fin_priv_native_dual_paper_ledgers",
        ["python3", "scripts/e16_fin_priv_native_dual_paper_ledgers.py"],
    ),
    (
        "soft_assist_dual_paper_ledgers",
        ["python3", "scripts/e16_soft_assist_dual_paper_ledgers.py"],
    ),
    (
        "sleeve_tilt_dual_paper_ledgers",
        ["python3", "scripts/e16_sleeve_tilt_dual_paper_ledgers.py"],
    ),
    (
        "fuse_additive_dual_paper_ledgers",
        ["python3", "scripts/e16_fuse_additive_dual_paper_ledgers.py"],
    ),
    (
        "e45_defend_handoff_dual_paper_ledgers",
        ["python3", "scripts/e45_defend_handoff_dual_paper_ledgers.py"],
    ),
]


def run_step(name: str, cmd: list[str]) -> dict:
    print(f"==> {name}: {' '.join(cmd)}", flush=True)
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    out = {
        "name": name,
        "cmd": cmd,
        "returncode": int(proc.returncode),
        "ok": proc.returncode == 0,
        "stdout_tail": (proc.stdout or "")[-2000:],
        "stderr_tail": (proc.stderr or "")[-1000:],
    }
    if proc.returncode != 0:
        print(proc.stdout[-1500:] if proc.stdout else "", flush=True)
        print(proc.stderr[-1500:] if proc.stderr else "", flush=True)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Ops month-end paper pack (no Soft-Frozen change)")
    ap.add_argument(
        "--refresh-ledgers",
        action="store_true",
        help="Also rebuild L4/FIN50/BLEND_025/E45 dual-paper ledgers before monitors (slow).",
    )
    ap.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Run remaining steps even if one fails (still exit non-zero).",
    )
    ap.add_argument(
        "--fail-on-critical",
        action="store_true",
        help="Run ops_alert_scan without --report-only so CRITICAL exits non-zero.",
    )
    args = ap.parse_args()

    steps = []
    if args.refresh_ledgers:
        steps.extend(STEPS_REFRESH)
    monitor_steps = list(STEPS_MONITOR)
    if args.fail_on_critical:
        monitor_steps = [
            (n, [c for c in cmd if c != "--report-only"]) if n == "ops_alert_scan" else (n, cmd)
            for n, cmd in monitor_steps
        ]
    steps.extend(monitor_steps)

    results = []
    failed = False
    for name, cmd in steps:
        row = run_step(name, cmd)
        results.append(row)
        if not row["ok"]:
            failed = True
            if not args.continue_on_error:
                break

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "OPS_MONTH_END_PAPER_PACK",
        "live_wire": False,
        "soft_frozen_clip": list(SOFT_FROZEN_FIN_CLIP),
        "soft_frozen_unchanged": True,
        "refresh_ledgers": bool(args.refresh_ledgers),
        "continue_on_error": bool(args.continue_on_error),
        "partial_pack": bool(args.continue_on_error and failed),
        "all_ok": not failed and all(r["ok"] for r in results),
        "steps": [
            {"name": r["name"], "ok": r["ok"], "returncode": r["returncode"]} for r in results
        ],
        "cutover_note": (
            f"Paper/ops cadence only. Soft-Frozen live clip {CLIP_TXT} (FINBAND). "
            "Live stack: Soft-Frozen FINBAND + KD_OPT (E45 A05 stitch rolled back DROP_E45_A05). "
            "FIN50 remains NOT_READY_SEALED_CAGR; L4 / BLEND_025 cutover still human-PR gated. "
            "Paper observe sleeves (E45 FULL/A25/A05/FIN_A10/C35, FIN within-sleeve quartet, "
            "Soft-assist SOFT_CHAMP_PLUS_K9_LT30_a10__SELL_a05, Sleeve-tilt SLEEVE_RSI14_LT30_a0225, FUSE_ADDITIVE, "
            "E45 defend-handoff DH_dd06_vz1p0) "
            "remain paper monitors beside live — no auto-combo, no live wire, no E45 stitch."
        ),
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_JSON.write_text(json.dumps(payload, indent=2) + "\n")

    lines = [
        "# Ops Month-End Paper Pack",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Status: **RESEARCH / OPS** — Soft-Frozen **{CLIP_TXT} unchanged**; no cutover.",
        "",
        f"- Refresh ledgers: **{payload['refresh_ledgers']}**",
        f"- All steps OK: **{payload['all_ok']}**",
        "",
        "| Step | OK | Exit |",
        "|---|---|---:|",
    ]
    for r in results:
        lines.append(f"| `{r['name']}` | {r['ok']} | {r['returncode']} |")
    lines += [
        "",
        "## Hard rules",
        "",
        "- No Soft-Frozen flip",
        "- Dual-paper / held-out PASS ≠ cutover license",
        "- Never rewrite `forward/e21` history",
        "",
        "## Re-run",
        "",
        "```bash",
        "python3 scripts/ops_month_end_paper_pack.py",
        "python3 scripts/ops_month_end_paper_pack.py --refresh-ledgers  # slow",
        "```",
        "",
        "Authority: `research/STRATEGY_DEBT_BOARD.md`",
        "",
    ]
    SUMMARY_MD.write_text("\n".join(lines))
    print(json.dumps(payload, indent=2))
    return 0 if payload["all_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
