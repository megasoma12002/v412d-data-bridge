#!/usr/bin/env python3
"""Broker / R5 / OCO PREP status — observe-only, never opens live gates.

Reports readiness for three tracks without flipping:
  Soft-Frozen fill_port · broker_live_write_accepted · API_WIRED · SendAlgo.

Tracks:
  1) 真下單 (StockOrder INTENT_ONLY)
  2) T+2 R5 custody reconcile (observe)
  3) 條件單 OCO (StrategyType=3 INTENT_ONLY)
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _gate_snapshot() -> dict[str, Any]:
    from live_config import LIVE
    import yuanta_spark_adapter as spark

    env_live = os.environ.get("E21_BROKER_WRITE_LIVE", "")
    ballot = ROOT / "forward" / "e21" / "broker_live_write_accept.json"
    ballot_accepted = False
    if ballot.exists():
        try:
            ballot_accepted = bool(json.loads(ballot.read_text()).get("accepted"))
        except (json.JSONDecodeError, OSError):
            ballot_accepted = False
    return {
        "fill_port": LIVE.fill_port,
        "broker_live_write_accepted": bool(LIVE.broker_live_write_accepted),
        "E21_BROKER_WRITE_LIVE": env_live,
        "broker_live_write_accept_json": ballot_accepted,
        "spark_api_wired": bool(spark.API_WIRED),
        "execute_open": False,  # this script never opens
    }


def _assert_still_closed(gates: dict[str, Any]) -> list[str]:
    errs: list[str] = []
    if gates["fill_port"] != "paper":
        errs.append(f"fill_port={gates['fill_port']!r} (expected paper)")
    if gates["broker_live_write_accepted"]:
        errs.append("broker_live_write_accepted=True")
    if str(gates["E21_BROKER_WRITE_LIVE"]).strip() in {"1", "true", "TRUE", "yes"}:
        errs.append("E21_BROKER_WRITE_LIVE set")
    if gates["broker_live_write_accept_json"]:
        errs.append("broker_live_write_accept.json accepted=true")
    if gates["spark_api_wired"]:
        errs.append("yuanta_spark_adapter.API_WIRED=True")
    return errs


def build_prep_report(*, run_r5: bool = False) -> dict[str, Any]:
    gates = _gate_snapshot()
    closed_errs = _assert_still_closed(gates)
    r5 = {
        "estimate_present": (ROOT / "forward/e21/settlement_cash_estimate.csv").exists(),
        "synthetic_fixture": (ROOT / "fixtures/r5_custody_synthetic.csv").exists(),
        "dropin_fixture": (ROOT / "fixtures/r5_custody_dropin.csv").exists(),
        "reconcile_ran": False,
        "reconcile_all_ok": None,
        "reconcile_out": None,
    }
    if run_r5 and r5["estimate_present"]:
        from ops_r5_observe_auto import run_r5_observe

        r5_out = run_r5_observe(prefer_dropin=True)
        r5.update(r5_out)

    import yuanta_spark_adapter as spark

    oco = {
        "strategy_type": spark.OCO_STRATEGY_TYPE,
        "send_algo_blocked": True,
        "build_intent_ok": False,
    }
    try:
        from datetime import date

        intent = spark.build_oco_strategy_intent(
            code="0050",
            asof=date(2026, 9, 26),
            shares=1000,
            trigger_price_1=140.0,
            order_price_1=139.5,
            trigger_price_2=120.0,
            order_price_2=119.5,
        )
        oco["build_intent_ok"] = intent.status == "INTENT_ONLY" and not intent.api_wired
        try:
            spark.send_algo_oco_live(intent)
            oco["send_algo_blocked"] = False
        except spark.SparkNotWiredError:
            oco["send_algo_blocked"] = True
    except Exception as exc:  # noqa: BLE001 — status report
        oco["error"] = str(exc)

    stock = {
        "send_stock_blocked": True,
        "intent_only": True,
    }
    try:
        spark.send_stock_order_live()
        stock["send_stock_blocked"] = False
    except spark.SparkNotWiredError:
        stock["send_stock_blocked"] = True

    prep_ok = (
        not closed_errs
        and stock["send_stock_blocked"]
        and oco["send_algo_blocked"]
        and oco.get("build_intent_ok") is True
    )
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "BROKER_R5_OCO_PREP_NOT_OPEN",
        "status": "PREP_OK_NOT_OPEN" if prep_ok else "PREP_FAIL_OR_GATES_OPEN",
        "execute_blocked": True,
        "gates": gates,
        "gate_violations": closed_errs,
        "tracks": {
            "real_submit_stock_order": stock,
            "t2_r5_reconcile": r5,
            "conditional_oco": oco,
        },
        "human_execute_requires": [
            "ACCEPT EXECUTE broker live-write ballot",
            "UAT Login MsgCode 0001/00001",
            "LiveConfig.broker_live_write_accepted=True",
            "E21_BROKER_WRITE_LIVE=1",
            "broker_live_write_accept.json accepted=true",
            "yuanta_spark_adapter.API_WIRED=True (separate wire PR)",
        ],
        "soft_frozen_keep": True,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--run-r5",
        action="store_true",
        help="Also run observe R5 if custody drop-in or synthetic exists.",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "research" / "ops" / "BROKER_R5_OCO_PREP_STATUS.json",
    )
    ap.add_argument(
        "--fail-if-gates-open",
        action="store_true",
        help="Exit 2 if any live-write gate is already open (unexpected).",
    )
    a = ap.parse_args()
    report = build_prep_report(run_r5=bool(a.run_r5))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if a.fail_if_gates_open and report["gate_violations"]:
        return 2
    return 0 if report["status"] == "PREP_OK_NOT_OPEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
