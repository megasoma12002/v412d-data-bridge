#!/usr/bin/env python3
"""Fetch point-in-time corporate action fields for the frozen E21 universe."""
import csv
import json
import urllib.parse
import urllib.request
from pathlib import Path

UNIVERSE = ["2880", "2886", "2892", "5880", "2412", "3045", "4904", "0050"]
URL = "https://api.finmindtrade.com/api/v4/data"


def fetch(code):
    query = urllib.parse.urlencode({
        "dataset": "TaiwanStockDividend",
        "data_id": code,
        "start_date": "2010-01-01",
        "end_date": "2026-12-31",
    })
    req = urllib.request.Request(URL + "?" + query, headers={"User-Agent": "v412e22/1.0"})
    with urllib.request.urlopen(req, timeout=120) as response:
        payload = json.load(response)
    if payload.get("status") != 200:
        raise RuntimeError(f"FinMind {code}: {payload}")
    return payload.get("data", [])


def number(row, *keys):
    total = 0.0
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            total += float(value)
    return total


def main():
    outdir = Path("data/dividend_events")
    outdir.mkdir(parents=True, exist_ok=True)
    normalized = []
    raw = {}
    for code in UNIVERSE:
        rows = fetch(code)
        raw[code] = rows
        for row in rows:
            normalized.append({
                "code": code,
                "fiscal_year": row.get("year", ""),
                "record_date": row.get("date", ""),
                "announcement_date": row.get("AnnouncementDate", ""),
                "announcement_time": row.get("AnnouncementTime", ""),
                "cash_ex_date": row.get("CashExDividendTradingDate", ""),
                "cash_payment_date": row.get("CashDividendPaymentDate", ""),
                "cash_dividend": number(row, "CashEarningsDistribution", "CashStatutorySurplus"),
                "stock_ex_date": row.get("StockExDividendTradingDate", ""),
                "stock_payment_date": row.get("StockDividendPaymentDate", row.get("StockDividendPaymentDate", "")),
                "stock_dividend": number(row, "StockEarningsDistribution", "StockStatutorySurplus"),
            })
    fields = list(normalized[0].keys()) if normalized else ["code"]
    with (outdir / "e22_dividend_events.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(normalized)
    (outdir / "e22_dividend_raw.json").write_text(
        json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    counts = {code: len(raw[code]) for code in UNIVERSE}
    status = {"status": "PASS", "universe": UNIVERSE, "row_counts": counts, "rows": len(normalized)}
    (outdir / "e22_dividend_fetch_status.json").write_text(
        json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(status, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
