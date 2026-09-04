#!/usr/bin/env python3
"""Backfill E22 cash + stock payment dates from Yahoo TW dividend pages.

Also refreshes ``yahoo_tw_dividend_history.csv``. Does not rewrite A0/E21.
Stock dividend amounts stay FinMind (元／股); payment dates from Yahoo
「股票股利發放日」.

Usage:
  python3 scripts/e22_backfill_div_payment_dates_yahoo.py
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from e22_backfill_payment_dates_yahoo import (
    DIV_PATH,
    OUT_DIR,
    UNIVERSE,
    blank,
    get,
    parse_yahoo,
)

NEAR_DAYS_CASH = 1
NEAR_DAYS_STOCK = 3  # FinMind vs Yahoo stock ex occasionally drifts >1d (e.g. 2892 2019)


def parse_day(value: str) -> datetime | None:
    value = (value or "").strip()[:10]
    if blank(value):
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None


def near_hit(index: dict, code: str, ex: str, pay_field: str, near_days: int) -> tuple[dict | None, str]:
    key = (code, ex[:10])
    if key in index and not blank(index[key].get(pay_field)):
        return index[key], "EXACT"
    d0 = parse_day(ex)
    if d0 is None:
        return None, ""
    candidates = []
    for (c, ex2), payload in index.items():
        if c != code or blank(payload.get(pay_field)):
            continue
        d1 = parse_day(ex2)
        if d1 is None:
            continue
        delta = abs((d1 - d0).days)
        if delta <= near_days:
            candidates.append((delta, payload))
    if not candidates:
        return None, ""
    candidates.sort(key=lambda x: x[0])
    tag = "EXACT" if candidates[0][0] == 0 else f"NEAR{candidates[0][0]}D"
    return candidates[0][1], tag


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip-fetch", action="store_true", help="Reuse existing yahoo_tw_dividend_history.csv")
    args = ap.parse_args()

    hist_path = OUT_DIR / "yahoo_tw_dividend_history.csv"
    if args.skip_fetch and hist_path.exists():
        with hist_path.open(encoding="utf-8") as handle:
            yahoo_rows = list(csv.DictReader(handle))
    else:
        yahoo_rows = []
        for code in UNIVERSE:
            try:
                html = get(f"https://tw.stock.yahoo.com/quote/{code}.TW/dividend")
                yahoo_rows.extend(parse_yahoo(code, html))
                print(json.dumps({"code": code, "yahoo_rows": sum(1 for r in yahoo_rows if r["code"] == code)}))
            except Exception as exc:  # noqa: BLE001
                print(json.dumps({"code": code, "error": str(exc)}))

    cash_index = {
        (r["code"], r["cash_ex_date"][:10]): r
        for r in yahoo_rows
        if not blank(r.get("cash_ex_date")) and not blank(r.get("cash_payment_date"))
    }
    stock_index = {
        (r["code"], r["stock_ex_date"][:10]): r
        for r in yahoo_rows
        if not blank(r.get("stock_ex_date")) and not blank(r.get("stock_payment_date"))
    }

    with DIV_PATH.open(encoding="utf-8") as handle:
        div_rows = list(csv.DictReader(handle))

    cash_updates = []
    stock_updates = []
    for row in div_rows:
        try:
            cash = float(row.get("cash_dividend") or 0)
        except ValueError:
            cash = 0.0
        try:
            stock = float(row.get("stock_dividend") or 0)
        except ValueError:
            stock = 0.0

        if cash > 0 and not blank(row.get("cash_ex_date")) and blank(row.get("cash_payment_date")):
            hit, match = near_hit(cash_index, row["code"], row["cash_ex_date"], "cash_payment_date", NEAR_DAYS_CASH)
            if hit:
                if not args.dry_run:
                    row["cash_payment_date"] = hit["cash_payment_date"]
                cash_updates.append(
                    {
                        "code": row["code"],
                        "cash_ex_date": row["cash_ex_date"],
                        "cash_payment_date": hit["cash_payment_date"],
                        "match": match,
                        "yahoo_ex": hit["cash_ex_date"],
                    }
                )

        if stock > 0 and not blank(row.get("stock_ex_date")) and blank(row.get("stock_payment_date")):
            hit, match = near_hit(stock_index, row["code"], row["stock_ex_date"], "stock_payment_date", NEAR_DAYS_STOCK)
            if hit:
                if not args.dry_run:
                    row["stock_payment_date"] = hit["stock_payment_date"]
                stock_updates.append(
                    {
                        "code": row["code"],
                        "stock_ex_date": row["stock_ex_date"],
                        "stock_payment_date": hit["stock_payment_date"],
                        "match": match,
                        "yahoo_ex": hit["stock_ex_date"],
                        "stock_dividend": stock,
                    }
                )

    if not args.dry_run:
        fields = list(div_rows[0].keys())
        # surgical write preserving CRLF if present
        raw = DIV_PATH.read_bytes()
        nl = "\r\n" if b"\r\n" in raw else "\n"
        with DIV_PATH.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator=nl)
            writer.writeheader()
            writer.writerows(div_rows)

        if yahoo_rows:
            with hist_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(yahoo_rows[0].keys()))
                writer.writeheader()
                writer.writerows(yahoo_rows)

    # coverage summary
    def blank_row(r, k):
        return blank(r.get(k))

    cash_n = sum(1 for r in div_rows if float(r.get("cash_dividend") or 0) > 0)
    cash_miss = sum(
        1
        for r in div_rows
        if float(r.get("cash_dividend") or 0) > 0 and blank_row(r, "cash_payment_date")
    )
    stock_n = sum(1 for r in div_rows if float(r.get("stock_dividend") or 0) > 0)
    stock_miss = sum(
        1
        for r in div_rows
        if float(r.get("stock_dividend") or 0) > 0 and blank_row(r, "stock_payment_date")
    )
    stock_ex_miss = sum(
        1 for r in div_rows if float(r.get("stock_dividend") or 0) > 0 and blank_row(r, "stock_ex_date")
    )

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dry_run": args.dry_run,
        "cash_updates": len(cash_updates),
        "stock_updates": len(stock_updates),
        "cash_events": cash_n,
        "cash_payment_missing_after": cash_miss,
        "stock_events": stock_n,
        "stock_ex_missing_after": stock_ex_miss,
        "stock_payment_missing_after": stock_miss,
        "stock_updates_detail": stock_updates,
        "cash_updates_detail": cash_updates,
        "remaining_stock_gaps": [
            {
                "code": r["code"],
                "stock_ex_date": r.get("stock_ex_date"),
                "stock_dividend": r.get("stock_dividend"),
            }
            for r in div_rows
            if float(r.get("stock_dividend") or 0) > 0 and blank_row(r, "stock_payment_date")
        ],
        "unit_note": "stock_dividend is FinMind 元/股; share factor = 1 + stock_dividend/10",
    }
    (OUT_DIR / "e22_div_payment_backfill_status.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    )
    print(json.dumps({k: report[k] for k in report if k.endswith("after") or k.endswith("updates") or k in ("cash_events", "stock_events", "remaining_stock_gaps")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
