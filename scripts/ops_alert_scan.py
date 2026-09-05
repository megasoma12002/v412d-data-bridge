#!/usr/bin/env python3
"""Ops alert scan — RESEARCH / OPS only.

Reads live QC + latest month-end monitor JSONs and emits:
  research/ops/OPS_ALERTS.json
  research/ops/OPS_ALERTS.md

Severity:
  CRITICAL — live QC FAIL / Exact T+1 fail
  HIGH     — month-end PAUSE_REVIEW (cutover talk blocked; Soft-Frozen unchanged)
  INFO     — ALERT lines without PAUSE / thin recon overlap

Exit codes:
  0 — no CRITICAL/HIGH
  1 — HIGH present (PAUSE_REVIEW)
  2 — CRITICAL present

Never flips Soft-Frozen. Never cutover.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "research/ops"
QC_PATH = ROOT / "forward/e21/qc_status.json"
L4_JSON = ROOT / "research/gaps/L4_DD_PATH_MONTH_END_MONITOR.json"
FIN_JSON = ROOT / "research/gaps/FIN_CAP_50_MONTH_END_MONITOR.json"
BLEND_JSON = ROOT / "research/gaps/BLEND_025_MONTH_END_MONITOR.json"
RECON_JSON = ROOT / "research/ops/LIVE_PAPER_RECON.json"
GAP6_JSON = ROOT / "research/ops/E22_GAP6_FIDELITY_KPI.json"
E22_KPI_JSON = ROOT / "research/ops/E22_DATA_QUALITY_KPI.json"
RESILIENCE_JSON = ROOT / "research/ops/DATA_SOURCE_RESILIENCE_KPI.json"
SHADOW_JSON = ROOT / "research/ops/DATA_SOURCE_SHADOW_RECONCILE.json"

# Soft-Frozen clip — single source (never hardcode drift).
sys.path.insert(0, str(ROOT / "scripts"))
from e16_soft_frozen_base import SOFT_FROZEN_FIN_HI, SOFT_FROZEN_FIN_LO

SOFT_FROZEN_CLIP = [float(SOFT_FROZEN_FIN_LO), float(SOFT_FROZEN_FIN_HI)]


def _load(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR)
    ap.add_argument(
        "--report-only",
        action="store_true",
        help="Always exit 0 after writing OPS_ALERTS.* (month-end pack mode).",
    )
    ap.add_argument(
        "--fail-on",
        choices=("never", "critical", "high"),
        default="critical",
        help="Exit non-zero threshold when not --report-only (default: critical).",
    )
    args = ap.parse_args()

    alerts: list[dict] = []

    qc = _load(QC_PATH)
    if qc is None:
        alerts.append(
            {
                "severity": "CRITICAL",
                "source": "live_qc",
                "code": "QC_MISSING",
                "message": f"missing {QC_PATH}",
            }
        )
    else:
        status = str(qc.get("status", "")).upper()
        exact = qc.get("exact_t1_ok")
        if status != "PASS":
            alerts.append(
                {
                    "severity": "CRITICAL",
                    "source": "live_qc",
                    "code": "QC_FAIL",
                    "message": f"forward/e21 qc_status status={status!r}",
                }
            )
        if exact is False:
            alerts.append(
                {
                    "severity": "CRITICAL",
                    "source": "live_qc",
                    "code": "EXACT_T1_FAIL",
                    "message": "exact_t1_ok is false",
                }
            )
        if status == "PASS" and exact is True:
            alerts.append(
                {
                    "severity": "INFO",
                    "source": "live_qc",
                    "code": "QC_PASS",
                    "message": "live QC PASS; Exact T+1 ok",
                }
            )

    for label, path in (
        ("l4_month_end", L4_JSON),
        ("fincap50_month_end", FIN_JSON),
        ("blend025_month_end", BLEND_JSON),
    ):
        doc = _load(path)
        if doc is None:
            alerts.append(
                {
                    "severity": "INFO",
                    "source": label,
                    "code": "MONITOR_MISSING",
                    "message": f"missing {path} (run month-end pack)",
                }
            )
            continue
        for line in doc.get("alerts") or []:
            sev = "HIGH" if "PAUSE_REVIEW" in str(line) else "INFO"
            if str(line).startswith("ALERT"):
                sev = "HIGH" if "PAUSE_REVIEW" in str(line) else "INFO"
            if "PAUSE_REVIEW" in str(line):
                sev = "HIGH"
            alerts.append(
                {
                    "severity": sev,
                    "source": label,
                    "code": "PAUSE_REVIEW" if "PAUSE_REVIEW" in str(line) else "MONITOR_ALERT",
                    "message": str(line),
                }
            )
        if doc.get("cutover_blocked"):
            alerts.append(
                {
                    "severity": "INFO",
                    "source": label,
                    "code": "CUTOVER_BLOCKED_FLAG",
                    "message": "cutover_blocked=true (expected while Soft-Frozen KEEP)",
                }
            )

    recon = _load(RECON_JSON)
    if recon:
        for a in recon.get("alerts") or []:
            alerts.append(
                {
                    "severity": "INFO",
                    "source": "live_paper_recon",
                    "code": "RECON_NOTE",
                    "message": str(a),
                }
            )
        n = recon.get("overlap_n") or recon.get("overlap_sessions")
        if n is not None and int(n) < 60:
            alerts.append(
                {
                    "severity": "INFO",
                    "source": "live_paper_recon",
                    "code": "THIN_LIVE_HISTORY",
                    "message": f"overlap_n={n} (<60) — not decision-grade for cutover",
                }
            )

    e22_kpi = _load(E22_KPI_JSON)
    if e22_kpi is not None and e22_kpi.get("kpi_ok") is False:
        alerts.append(
            {
                "severity": "INFO",
                "source": "e22_data_quality_kpi",
                "code": "E22_DQ_FLAGS",
                "message": f"flags={e22_kpi.get('flags')}",
            }
        )

    gap6 = _load(GAP6_JSON)
    if gap6 is None:
        alerts.append(
            {
                "severity": "INFO",
                "source": "e22_gap6_fidelity_kpi",
                "code": "GAP6_KPI_MISSING",
                "message": f"missing {GAP6_JSON} (run month-end pack / e22_gap6_fidelity_kpi)",
            }
        )
    else:
        if gap6.get("code_ok") is False:
            alerts.append(
                {
                    "severity": "HIGH",
                    "source": "e22_gap6_fidelity_kpi",
                    "code": "E22_CODE_WIRE_FAIL",
                    "message": f"E22 code wire not OK; flags={gap6.get('flags')}",
                }
            )
        for flag in gap6.get("flags") or []:
            sev = "HIGH" if str(flag).startswith("DEFAULT_BOOKS") or "unexpectedly" in str(flag) else "INFO"
            if flag == "LIVE_LEDGER_E22_FIELDS_MISSING":
                sev = "INFO"
            alerts.append(
                {
                    "severity": sev,
                    "source": "e22_gap6_fidelity_kpi",
                    "code": str(flag),
                    "message": str(flag),
                }
            )

    resilience = _load(RESILIENCE_JSON)
    if resilience is None:
        alerts.append(
            {
                "severity": "INFO",
                "source": "data_source_resilience_kpi",
                "code": "RESILIENCE_KPI_MISSING",
                "message": f"missing {RESILIENCE_JSON} (run data_source_resilience_kpi)",
            }
        )
    else:
        n_sp = int(resilience.get("n_critical_without_backup") or 0)
        if n_sp > 0:
            alerts.append(
                {
                    "severity": "INFO",
                    "source": "data_source_resilience_kpi",
                    "code": "SINGLE_POINT_STREAMS",
                    "message": (
                        f"n_critical_without_backup={n_sp}; "
                        f"flags={resilience.get('flags')}"
                    ),
                }
            )
        if resilience.get("kpi_ok") is False:
            alerts.append(
                {
                    "severity": "HIGH",
                    "source": "data_source_resilience_kpi",
                    "code": "PAYMENT_DATE_BACKUP_REGRESSION",
                    "message": "dividend payment-date backup path regressed",
                }
            )

    shadow = _load(SHADOW_JSON)
    if shadow is None:
        alerts.append(
            {
                "severity": "INFO",
                "source": "data_source_shadow_reconcile",
                "code": "SHADOW_RECONCILE_MISSING",
                "message": f"missing {SHADOW_JSON} (run data_source_shadow_reconcile)",
            }
        )
    else:
        for c in shadow.get("checks") or []:
            st = str(c.get("status") or "")
            if st == "DRIFT":
                alerts.append(
                    {
                        "severity": "INFO",
                        "source": "data_source_shadow_reconcile",
                        "code": f"SHADOW_DRIFT_{c.get('id')}".upper(),
                        "message": f"{c.get('id')}: {st} detail={c.get('detail_csv') or c.get('note')}",
                    }
                )
            elif st in {"NO_OVERLAP", "YAHOO_EMPTY", "MISSING_LEDGER"}:
                alerts.append(
                    {
                        "severity": "INFO",
                        "source": "data_source_shadow_reconcile",
                        "code": f"SHADOW_FAIL_{c.get('id')}".upper(),
                        "message": f"{c.get('id')}: {st}",
                    }
                )

    # Rank
    rank = {"CRITICAL": 0, "HIGH": 1, "INFO": 2}
    alerts.sort(key=lambda x: rank.get(x["severity"], 9))

    has_crit = any(a["severity"] == "CRITICAL" for a in alerts)
    has_high = any(a["severity"] == "HIGH" for a in alerts)
    overall = "CRITICAL" if has_crit else ("HIGH" if has_high else "CLEAR")

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "OPS_ALERT_SCAN",
        "live_wire": False,
        "soft_frozen_unchanged": True,
        "soft_frozen_clip": list(SOFT_FROZEN_CLIP),
        "overall": overall,
        "n_critical": sum(1 for a in alerts if a["severity"] == "CRITICAL"),
        "n_high": sum(1 for a in alerts if a["severity"] == "HIGH"),
        "n_info": sum(1 for a in alerts if a["severity"] == "INFO"),
        "alerts": alerts,
        "routing_note": (
            "Annotate CI job summary / upload OPS_ALERTS.* as artifact. "
            "HIGH=PAUSE_REVIEW blocks cutover talk only. CRITICAL fails live QC smoke."
        ),
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "OPS_ALERTS.json").write_text(json.dumps(payload, indent=2) + "\n")

    lines = [
        "# Ops Alerts",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Overall: **{overall}**",
        f"Soft-Frozen **[{SOFT_FROZEN_CLIP[0]:.2f}, {SOFT_FROZEN_CLIP[1]:.2f}] unchanged**. No auto cutover.",
        "",
        f"- CRITICAL: {payload['n_critical']}",
        f"- HIGH (PAUSE_REVIEW etc.): {payload['n_high']}",
        f"- INFO: {payload['n_info']}",
        "",
        "| Severity | Source | Code | Message |",
        "|---|---|---|---|",
    ]
    for a in alerts:
        msg = a["message"].replace("|", "\\|")
        lines.append(f"| {a['severity']} | `{a['source']}` | `{a['code']}` | {msg} |")
    lines += [
        "",
        "## Routing",
        "",
        "- CRITICAL → fail `e21-live-qc-smoke` / block live confidence",
        "- HIGH → month-end pack annotates PAUSE; cutover checklists stay blocked",
        "- INFO → recorded only",
        "",
        "Re-run: `python3 scripts/ops_alert_scan.py`",
        "",
    ]
    (args.out_dir / "OPS_ALERTS.md").write_text("\n".join(lines))
    print(json.dumps(payload, indent=2))

    if args.report_only:
        return 0
    if args.fail_on == "never":
        return 0
    if has_crit:
        return 2
    if args.fail_on == "high" and has_high:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
