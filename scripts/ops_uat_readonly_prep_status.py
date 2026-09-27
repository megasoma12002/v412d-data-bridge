#!/usr/bin/env python3
"""UAT readonly PREP status — no network Login; assert repo gates stay closed.

Optional: read gitignored ``fixtures/uat_readonly_evidence.json`` (redacted).
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "fixtures" / "uat_readonly_evidence.json"


def build_report() -> dict[str, Any]:
    from live_config import LIVE
    import yuanta_spark_adapter as spark

    env_live = os.environ.get("E21_BROKER_WRITE_LIVE", "")
    gates = {
        "fill_port": LIVE.fill_port,
        "broker_live_write_accepted": bool(LIVE.broker_live_write_accepted),
        "E21_BROKER_WRITE_LIVE": env_live,
        "spark_api_wired": bool(spark.API_WIRED),
    }
    violations = []
    if gates["fill_port"] != "paper":
        violations.append("fill_port")
    if gates["broker_live_write_accepted"]:
        violations.append("broker_live_write_accepted")
    if str(env_live).strip() in {"1", "true", "TRUE", "yes"}:
        violations.append("E21_BROKER_WRITE_LIVE")
    if gates["spark_api_wired"]:
        violations.append("API_WIRED")

    send_blocked = True
    try:
        spark.send_stock_order_live()
        send_blocked = False
    except spark.SparkNotWiredError:
        send_blocked = True
    oco_blocked = True
    try:
        spark.send_algo_oco_live()
        oco_blocked = False
    except spark.SparkNotWiredError:
        oco_blocked = True

    evidence = None
    if EVIDENCE.is_file():
        try:
            evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            evidence = {"error": str(exc)}

    login_ok = bool(evidence and evidence.get("login_ok") and not evidence.get("orders_sent"))
    if violations:
        status = "PREP_FAIL_GATES_OPEN"
    elif login_ok:
        status = "PREP_OK_UAT_EVIDENCE_PRESENT"
    else:
        status = "PREP_OK_WAITING_OPERATOR"

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "YUANTA_SPARK_UAT_READONLY_PREP",
        "status": status,
        "execute_blocked": True,
        "gates": gates,
        "gate_violations": violations,
        "send_stock_blocked": send_blocked,
        "send_algo_blocked": oco_blocked,
        "evidence_path": str(EVIDENCE) if EVIDENCE.is_file() else None,
        "evidence_login_ok": login_ok,
        "checklist": "research/ops/YUANTA_SPARK_UAT_READONLY_CHECKLIST.md",
        "human_still_needs": [
            "UAT firewall + Login MsgCode 0001/00001 on jump VM",
            "Redacted fixtures/uat_readonly_evidence.json (optional)",
            "Separate ACCEPT EXECUTE before any SendStockOrder",
        ],
        "soft_frozen_keep": True,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "research" / "ops" / "UAT_READONLY_PREP_STATUS.json",
    )
    ap.add_argument("--fail-if-gates-open", action="store_true")
    a = ap.parse_args()
    report = build_report()
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if a.fail_if_gates_open and report["gate_violations"]:
        return 2
    return 0 if report["status"].startswith("PREP_OK") else 1


if __name__ == "__main__":
    raise SystemExit(main())
