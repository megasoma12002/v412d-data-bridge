#!/usr/bin/env python3
"""Ops month-end paper pack — RESEARCH / OPS cadence only.

Runs (by default, fast path):
  1) L4 month-end monitor
  2) FIN50 month-end monitor
  3) Track A S9A1 archive monitor
  4) Live ↔ Soft-Frozen paper BASE recon

Optional --refresh-ledgers also rebuilds L4/FIN50 dual-paper ledgers
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
from e16_soft_frozen_base import SOFT_FROZEN_FIN_HI, SOFT_FROZEN_FIN_LO

SOFT_FROZEN_CLIP = [float(SOFT_FROZEN_FIN_LO), float(SOFT_FROZEN_FIN_HI)]
CLIP_TXT = f"[{SOFT_FROZEN_CLIP[0]:.2f}, {SOFT_FROZEN_CLIP[1]:.2f}]"

STEPS_MONITOR = [
    ("l4_month_end", ["python3", "scripts/e16_l4_dd_path_month_end_monitor.py"]),
    ("fincap50_month_end", ["python3", "scripts/e16_fincap50_month_end_monitor.py"]),
    ("track_a_s9a1", ["python3", "scripts/e50a_dual_track_s9a1_monitor.py"]),
    ("live_paper_recon", ["python3", "scripts/e21_live_vs_paper_recon.py"]),
    ("e22_data_quality_kpi", ["python3", "scripts/e22_data_quality_kpi.py"]),
    ("e22_gap6_fidelity_kpi", ["python3", "scripts/e22_gap6_fidelity_kpi.py"]),
    (
        "fincap50_sealed_cagr_charter_screen",
        ["python3", "scripts/fincap50_sealed_cagr_charter_screen.py"],
    ),
    ("ops_alert_scan", ["python3", "scripts/ops_alert_scan.py", "--report-only"]),
]

STEPS_REFRESH = [
    ("l4_dual_paper_ledgers", ["python3", "scripts/e16_l4_dd_path_dual_paper_ledgers.py"]),
    ("fincap50_dual_paper_ledgers", ["python3", "scripts/e16_fincap50_dual_paper_ledgers.py"]),
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
        help="Also rebuild L4/FIN50 dual-paper ledgers before monitors (slow).",
    )
    ap.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Run remaining steps even if one fails (still exit non-zero).",
    )
    args = ap.parse_args()

    steps = []
    if args.refresh_ledgers:
        steps.extend(STEPS_REFRESH)
    steps.extend(STEPS_MONITOR)

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
        "soft_frozen_clip": list(SOFT_FROZEN_CLIP),
        "soft_frozen_unchanged": True,
        "refresh_ledgers": bool(args.refresh_ledgers),
        "all_ok": not failed and all(r["ok"] for r in results),
        "steps": [
            {"name": r["name"], "ok": r["ok"], "returncode": r["returncode"]} for r in results
        ],
        "cutover_note": (
            f"Paper/ops cadence only. Soft-Frozen {CLIP_TXT} unchanged. "
            "FIN50 remains NOT_READY_SEALED_CAGR; L4 cutover stays human-PR gated."
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
