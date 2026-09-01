#!/usr/bin/env python3
"""Probe E50-A1 FinMind permissions and schemas without exposing the token."""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

API = "https://api.finmindtrade.com/api/v4/data"
OUT = Path("e50a1_probe")
DATASETS = [
    "TaiwanStockFinancialStatements",
    "TaiwanStockBalanceSheet",
    "TaiwanStockCashFlowsStatement",
    "TaiwanStockMonthRevenue",
    "TaiwanStockDividend",
    "TaiwanStockDividendResult",
    "TaiwanStockCapitalReductionReferencePrice",
    "TaiwanStockSplitPrice",
    "TaiwanStockParValueChange",
]


def request(dataset: str, stock_id: str | None) -> dict:
    query = {"dataset": dataset, "start_date": "2024-01-01", "end_date": date.today().isoformat()}
    if stock_id:
        query["data_id"] = stock_id
    token = os.environ.get("FINMIND_TOKEN", "")
    headers = {"User-Agent": "v412-e50a1-probe/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    url = API + "?" + urllib.parse.urlencode(query)
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=120) as response:
            payload = json.load(response)
        rows = payload.get("data") or []
        return {
            "http_ok": True,
            "api_status": payload.get("status"),
            "message": str(payload.get("msg", ""))[:300],
            "rows": len(rows),
            "columns": sorted({k for row in rows[:100] for k in row}),
            "sample": rows[0] if rows else {},
        }
    except Exception as exc:
        return {"http_ok": False, "error_type": type(exc).__name__, "message": str(exc)[:300],
                "rows": 0, "columns": [], "sample": {}}


def main() -> None:
    OUT.mkdir(exist_ok=True)
    result = {
        "version": "V4.12-E50-A1-PROBE",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "token_present": bool(os.environ.get("FINMIND_TOKEN")),
        "datasets": {},
    }
    for dataset in DATASETS:
        result["datasets"][dataset] = {
            "all_market": request(dataset, None),
            "sample_2330": request(dataset, "2330"),
        }
    (OUT / "schema_probe.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "version": result["version"],
        "token_present": result["token_present"],
        "summary": {d: {m: {k: v for k, v in x.items() if k != "sample"}
                         for m, x in modes.items()}
                    for d, modes in result["datasets"].items()},
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
