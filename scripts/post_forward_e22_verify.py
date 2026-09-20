#!/usr/bin/env python3
"""Post-forward E22 verify — Phase 0–1 realism automation (observe / evidence).

Runs the POST_FORWARD_E22_VERIFY_RUNBOOK chain for unattended ops:

  R4 artifact assert (Phase 0) → optional QC → Gap6 → DQ KPI → ops alert scan

Fail-closed only on:
  - missing R4 estimate when --require-r4
  - QC FAIL (when QC is run)
  - Gap6 code_ok / ci_smoke_ok false
  - CRITICAL alerts (default --fail-on critical)

Never fails on:
  - tip books ≠ Stage-E DEFAULT (tip lag INFO — authorized until weekday catch-up)
  - Gap6 exit 2 (live evidence debt)
  - DQ kpi_ok false (report-only completeness)
  - HIGH PAUSE_REVIEW (challenger observe ≠ cutover)

Soft-Frozen KEEP · no history rewrite · no Soft/alpha/broker promote.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "research" / "ops"
OUT_JSON = OUT_DIR / "POST_FORWARD_E22_VERIFY.json"
OUT_MD = OUT_DIR / "POST_FORWARD_E22_VERIFY.md"
GAP6_JSON = OUT_DIR / "E22_GAP6_FIDELITY_KPI.json"
DQ_JSON = OUT_DIR / "E22_DATA_QUALITY_KPI.json"
ALERTS_JSON = OUT_DIR / "OPS_ALERTS.json"
STAGE_E_DEFAULT = "E22_v3_recv_pay_effdelay"


def _run(cmd: list[str]) -> int:
    print("+", " ".join(cmd), flush=True)
    return subprocess.call(cmd, cwd=str(ROOT))


def _load(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def assert_r4(state_dir: Path) -> dict:
    csv_p = state_dir / "settlement_cash_estimate.csv"
    json_p = state_dir / "settlement_cash_estimate.json"
    ok = csv_p.is_file() and json_p.is_file() and csv_p.stat().st_size > 0 and json_p.stat().st_size > 0
    detail = {
        "csv_exists": csv_p.is_file(),
        "json_exists": json_p.is_file(),
        "csv_bytes": csv_p.stat().st_size if csv_p.is_file() else 0,
        "json_bytes": json_p.stat().st_size if json_p.is_file() else 0,
        "ok": ok,
    }
    if not ok:
        raise SystemExit(
            "Phase 0 R4 assert FAILED — missing/empty "
            f"{csv_p.name} / {json_p.name} under {state_dir}"
        )
    # Light schema: JSON must expose liquidity summary keys (not NAV).
    payload = json.loads(json_p.read_text(encoding="utf-8"))
    summary = payload.get("summary") if isinstance(payload, dict) else None
    if not isinstance(summary, dict):
        # older / flat shapes: accept top-level keys
        summary = payload if isinstance(payload, dict) else {}
    for key in ("settling_today_net", "unsettled_net", "paper_cash", "settled_cash_estimate"):
        if key not in summary and key not in payload:
            # soft: record missing but do not fail — schema evolved; presence of files is Phase 0 gate
            detail.setdefault("schema_notes", []).append(f"missing_key:{key}")
    detail["label"] = "liquidity_view_not_nav"
    return detail


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--state-dir", type=Path, default=ROOT / "forward" / "e21")
    ap.add_argument(
        "--require-r4",
        action="store_true",
        help="Phase 0: require settlement_cash_estimate.{csv,json}",
    )
    ap.add_argument(
        "--skip-qc",
        action="store_true",
        help="Skip e21_qc (when caller already ran fail-closed QC)",
    )
    ap.add_argument(
        "--fail-on",
        choices=("critical", "never"),
        default="critical",
        help="Alert fail policy (HIGH/PAUSE never fails this gate)",
    )
    ap.add_argument(
        "--report-only",
        action="store_true",
        help="Never non-zero exit (still writes verify pack)",
    )
    args = ap.parse_args()

    state_dir = args.state_dir.resolve()
    steps: dict = {}
    failures: list[str] = []

    if args.require_r4:
        steps["r4_assert"] = assert_r4(state_dir)
    else:
        steps["r4_assert"] = {"skipped": True}

    if not args.skip_qc:
        qc_rc = _run([sys.executable, str(ROOT / "scripts" / "e21_qc.py"), "--state-dir", str(state_dir)])
        steps["e21_qc"] = {"rc": qc_rc}
        if qc_rc != 0:
            failures.append("e21_qc_fail")
    else:
        steps["e21_qc"] = {"skipped": True}

    g6_rc = _run([sys.executable, str(ROOT / "scripts" / "e22_gap6_fidelity_kpi.py")])
    g6 = _load(GAP6_JSON) or {}
    code_ok = bool(g6.get("code_ok") and g6.get("ci_smoke_ok", g6.get("code_ok")))
    observed = (g6.get("live_ledger") or {}).get("observed_books_version")
    default = (g6.get("code_wire") or {}).get("default_books_version") or STAGE_E_DEFAULT
    tip_lag = bool(observed and default and observed != default)
    steps["gap6"] = {
        "rc": g6_rc,
        "code_ok": code_ok,
        "live_evidence_ok": g6.get("live_evidence_ok"),
        "kpi_ok": g6.get("kpi_ok"),
        "observed_books_version": observed,
        "default_books_version": default,
        "tip_lag": tip_lag,
    }
    # rc 1 = code fail; rc 2 = evidence debt (allowed); tip lag must not fail.
    if g6_rc == 1 or not code_ok:
        failures.append("gap6_code_wire_fail")

    dq_rc = _run([sys.executable, str(ROOT / "scripts" / "e22_data_quality_kpi.py")])
    dq = _load(DQ_JSON) or {}
    steps["data_quality"] = {
        "rc": dq_rc,
        "kpi_ok": dq.get("kpi_ok"),
        "flags": dq.get("flags") or [],
        "fail_closed": False,  # report-only for forward gate
    }

    alert_cmd = [
        sys.executable,
        str(ROOT / "scripts" / "ops_alert_scan.py"),
    ]
    if args.fail_on == "never" or args.report_only:
        alert_cmd.append("--report-only")
    else:
        alert_cmd.extend(["--fail-on", "critical"])
    alert_rc = _run(alert_cmd)
    alerts = _load(ALERTS_JSON) or {}
    steps["ops_alert_scan"] = {
        "rc": alert_rc,
        "overall": alerts.get("overall"),
        "n_critical": alerts.get("n_critical"),
        "n_high": alerts.get("n_high"),
        "n_info": alerts.get("n_info"),
    }
    if args.fail_on == "critical" and not args.report_only and alert_rc == 2:
        failures.append("ops_alert_critical")

    # Cashflow three views (report-only attach — never fail this gate).
    cashflow: dict = {}
    try:
        from cashflow_three_views_report import (
            OUT_JSON as CF_JSON,
            OUT_MD as CF_MD,
            build_report,
            render_md,
        )

        cashflow = build_report(state_dir)
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        CF_JSON.write_text(json.dumps(cashflow, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        CF_MD.write_text(render_md(cashflow), encoding="utf-8")
        steps["cashflow_three_views"] = {
            "ok": True,
            "tip_lag": cashflow.get("cross_checks", {}).get("tip_lag"),
            "r4_identity_ok": cashflow.get("cross_checks", {}).get("r4_identity_ok"),
            "n_warnings": len(cashflow.get("warnings") or []),
            "view_a_cash": (cashflow.get("views") or {}).get("A_paper_exact_t1", {}).get("cash"),
            "view_b_settled": (cashflow.get("views") or {})
            .get("B_r4_settled_liquidity", {})
            .get("settled_cash_estimate"),
            "view_c_cash_plus_recv": (cashflow.get("views") or {})
            .get("C_stage_e_div_cashflow", {})
            .get("cash_plus_receivable"),
        }
    except Exception as exc:  # noqa: BLE001 — attach best-effort; never fail gate
        steps["cashflow_three_views"] = {"ok": False, "error": str(exc)}
        cashflow = {}

    notes = []
    if tip_lag:
        notes.append(
            f"TIP_LAG_INFO: observed={observed} default={default} — "
            "authorized until next weekday forward catch-up; not a second DEFAULT; "
            "does not fail this gate (ACCEPT_TIP_BOOKS_ALIGN_V3)."
        )
    if steps["data_quality"].get("flags"):
        notes.append("DQ_FLAGS_REPORT_ONLY: " + ", ".join(steps["data_quality"]["flags"]))
    if cashflow.get("warnings"):
        notes.append("CASHFLOW_WARNINGS: " + "; ".join(cashflow["warnings"][:3]))

    ok = len(failures) == 0
    if args.report_only:
        ok = True

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "POST_FORWARD_E22_VERIFY",
        "phase": "0_1",
        "live_wire": False,
        "soft_frozen_keep": True,
        "state_dir": str(state_dir),
        "stage_e_default": STAGE_E_DEFAULT,
        "tip_lag": tip_lag,
        "ok": ok,
        "failures": failures,
        "notes": notes,
        "steps": steps,
        "cashflow_three_views": {
            "views": (cashflow.get("views") if cashflow else None),
            "cross_checks": (cashflow.get("cross_checks") if cashflow else None),
            "warnings": (cashflow.get("warnings") if cashflow else None),
        },
        "non_actions": [
            "no Soft-Frozen clip flip",
            "no history rewrite",
            "no tax Stage-B / broker live-write promote",
            "no L4/FIN50/BLEND/Soft/Sleeve alpha cutover",
            "settled_cash_estimate is liquidity view not NAV",
            "do not merge Exact T+1 / R4 / Stage-E cash clocks",
        ],
        "authority": [
            "research/ops/POST_FORWARD_E22_VERIFY_RUNBOOK.md",
            "research/ops/CASHFLOW_THREE_VIEWS.md",
            "research/ops/REALISM_AUTOMATION_GAP_CLOSE_2026-09-20.md",
            "research/ops/ACCEPT_TIP_BOOKS_ALIGN_V3.md",
        ],
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Post-forward E22 verify (Phase 0–1)",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Status: **{'PASS' if ok else 'FAIL'}** · Soft-Frozen KEEP · observe/evidence only",
        "",
        f"- tip_lag: **{tip_lag}** (observed `{observed}` vs default `{default}`)",
        f"- failures: `{', '.join(failures) or 'none'}`",
        "",
        "## Steps",
        "",
        f"- R4 assert: `{json.dumps(steps.get('r4_assert'))}`",
        f"- e21_qc: `{json.dumps(steps.get('e21_qc'))}`",
        f"- Gap6: code_ok={steps['gap6'].get('code_ok')} rc={steps['gap6'].get('rc')} tip_lag={tip_lag}",
        f"- DQ KPI: kpi_ok={steps['data_quality'].get('kpi_ok')} (report-only)",
        f"- Alerts: overall={steps['ops_alert_scan'].get('overall')} "
        f"crit={steps['ops_alert_scan'].get('n_critical')} high={steps['ops_alert_scan'].get('n_high')}",
        f"- Cashflow 3-views: `{json.dumps(steps.get('cashflow_three_views'))}`",
        "",
        "## Cashflow (A / B / C″)",
        "",
        f"- A paper cash: `{(payload.get('cashflow_three_views') or {}).get('views', {}) and (payload['cashflow_three_views']['views'] or {}).get('A_paper_exact_t1', {}).get('cash')}`",
        f"- B settled: `{steps.get('cashflow_three_views', {}).get('view_b_settled')}`",
        f"- C″ cash+recv: `{steps.get('cashflow_three_views', {}).get('view_c_cash_plus_recv')}`",
        "",
        "## Notes",
        "",
    ]
    if notes:
        for n in notes:
            lines.append(f"- {n}")
    else:
        lines.append("- None")
    lines += [
        "",
        "## Non-actions",
        "",
    ]
    for n in payload["non_actions"]:
        lines.append(f"- {n}")
    lines += [
        "",
        "Re-run: `python3 scripts/post_forward_e22_verify.py --require-r4`",
        "",
        "Label: `POST_FORWARD_E22_VERIFY__PHASE_0_1`",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
