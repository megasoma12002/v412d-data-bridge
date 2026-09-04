#!/usr/bin/env python3
"""Backfill missing E22 cash_payment_date from Yahoo Taiwan dividend pages.

GoodInfo / Wantgoo are Cloudflare-blocked from this environment; CMoney pages
do not expose a payment-date column. Yahoo TW quote dividend tables include
「現金股利發放日」and cover the early-year FinMind blanks.

Usage:
  python3 scripts/e22_backfill_payment_dates_yahoo.py
  python3 scripts/e22_backfill_payment_dates_yahoo.py --dry-run
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)
UNIVERSE = ["2880", "2886", "2892", "5880", "2412", "3045", "4904", "0050"]
DIV_PATH = Path("data/dividend_events/e22_dividend_events.csv")
OUT_DIR = Path("data/dividend_events")


def get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "zh-TW"})
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read().decode("utf-8", errors="ignore")


def to_iso(value: str) -> str:
    value = (value or "").strip()
    if not value or value in {"-", "--", "—"}:
        return ""
    parts = value.replace("-", "/").split("/")
    if len(parts) != 3:
        return ""
    year, month, day = map(int, parts)
    return f"{year:04d}-{month:02d}-{day:02d}"


def parse_yahoo(code: str, html: str) -> list[dict]:
    text = BeautifulSoup(html, "lxml").get_text("\n", strip=True)
    idx = text.find("現金股利發放日")
    if idx < 0:
        return []
    start = text.find("填息天數", idx)
    if start < 0:
        return []
    body = text[start + len("填息天數") :].strip().split("\n")
    stop_words = {"相關新聞", "熱門股", "技術分析", "登入", "隱私"}
    rows: list[dict] = []
    i = 0
    while i + 10 < len(body):
        chunk = body[i : i + 11]
        if any(any(sw in x for sw in stop_words) for x in chunk):
            break
        if not re.fullmatch(r"\d{4}", chunk[0] or "") or not re.fullmatch(r"\d{4}", chunk[1] or ""):
            i += 1
            continue
        _period, _belong, cash, _stock, _yld, _prev, ex_cash, ex_stock, pay_cash, pay_stock, _fill = chunk
        cash_v = ""
        try:
            if cash not in {"-", "--", ""}:
                cash_v = str(float(cash.replace(",", "")))
        except ValueError:
            cash_v = cash
        rows.append(
            {
                "code": code,
                "cash_ex_date": to_iso(ex_cash),
                "cash_payment_date": to_iso(pay_cash),
                "cash_dividend": cash_v,
                "stock_ex_date": to_iso(ex_stock),
                "stock_payment_date": to_iso(pay_stock),
                "source": "YahooTW_quote_dividend",
                "source_url": f"https://tw.stock.yahoo.com/quote/{code}.TW/dividend",
            }
        )
        i += 11
    return rows


def blank(value: str | None) -> bool:
    return value is None or str(value).strip() == "" or str(value).strip().lower() == "nan"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    yahoo_rows: list[dict] = []
    for code in UNIVERSE:
        try:
            html = get(f"https://tw.stock.yahoo.com/quote/{code}.TW/dividend")
            yahoo_rows.extend(parse_yahoo(code, html))
        except Exception as exc:  # noqa: BLE001
            print(json.dumps({"code": code, "error": str(exc)}))

    by_exact = {
        (r["code"], r["cash_ex_date"]): r
        for r in yahoo_rows
        if r["cash_ex_date"] and r["cash_payment_date"]
    }

    with DIV_PATH.open(encoding="utf-8") as handle:
        div_rows = list(csv.DictReader(handle))

    updates = []
    for row in div_rows:
        try:
            cash = float(row.get("cash_dividend") or 0)
        except ValueError:
            cash = 0.0
        if cash <= 0 or blank(row.get("cash_ex_date")) or not blank(row.get("cash_payment_date")):
            continue
        key = (row["code"], row["cash_ex_date"][:10])
        hit = by_exact.get(key)
        match = "EXACT"
        if hit is None:
            # allow ±1 day ex-date mismatch (seen for 5880 2012)
            candidates = []
            for (code, ex), payload in by_exact.items():
                if code != row["code"]:
                    continue
                d0 = datetime.strptime(row["cash_ex_date"][:10], "%Y-%m-%d")
                d1 = datetime.strptime(ex, "%Y-%m-%d")
                delta = abs((d1 - d0).days)
                if delta <= 1:
                    candidates.append((delta, payload))
            if candidates:
                candidates.sort(key=lambda x: x[0])
                hit = candidates[0][1]
                match = "NEAR1D"
        if hit is None:
            continue
        if not args.dry_run:
            row["cash_payment_date"] = hit["cash_payment_date"]
        updates.append(
            {
                "code": row["code"],
                "cash_ex_date": row["cash_ex_date"],
                "cash_payment_date": hit["cash_payment_date"],
                "match": match,
                "yahoo_ex": hit["cash_ex_date"],
                "source": hit["source"],
                "source_url": hit["source_url"],
            }
        )

    if not args.dry_run and updates:
        fields = list(div_rows[0].keys())
        with DIV_PATH.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(div_rows)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with (OUT_DIR / "yahoo_tw_dividend_history.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = list(yahoo_rows[0].keys()) if yahoo_rows else [
            "code",
            "cash_ex_date",
            "cash_payment_date",
            "cash_dividend",
            "source",
            "source_url",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(yahoo_rows)

    with (OUT_DIR / "web_scrape_payment_dates.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["code", "cash_ex_date", "cash_payment_date", "cash_dividend", "source", "source_url", "raw_note"],
        )
        writer.writeheader()
        for item in updates:
            writer.writerow(
                {
                    "code": item["code"],
                    "cash_ex_date": item["cash_ex_date"],
                    "cash_payment_date": item["cash_payment_date"],
                    "cash_dividend": "",
                    "source": item["source"],
                    "source_url": item["source_url"],
                    "raw_note": f"match={item['match']}; yahoo_ex={item['yahoo_ex']}",
                }
            )

    still = 0
    for row in div_rows:
        try:
            cash = float(row.get("cash_dividend") or 0)
        except ValueError:
            cash = 0.0
        if cash > 0 and blank(row.get("cash_payment_date")):
            still += 1

    report = {
        "status": "PASS" if still == 0 else "PARTIAL",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "n_yahoo_rows": len(yahoo_rows),
        "n_updated": len(updates),
        "n_still_missing": still,
        "blocked_sources": {
            "goodinfo": "cloudflare_403",
            "wantgoo": "403_or_404",
            "cmoney": "no_payment_date_column",
        },
        "working_source": "YahooTW_quote_dividend",
        "updates": updates,
        "dry_run": args.dry_run,
    }
    (OUT_DIR / "e22_payment_date_yahoo_backfill.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (OUT_DIR / "e22_payment_date_gap_report.json").write_text(
        json.dumps(
            {
                "status": report["status"],
                "generated_at_utc": report["generated_at_utc"],
                "n_still_missing_official": still,
                "n_filled_yahoo_tw": len(updates),
                "blocked_sources": report["blocked_sources"],
                "working_source": "https://tw.stock.yahoo.com/quote/{code}.TW/dividend",
                "conclusion": "Early FinMind/MOPS blanks filled from Yahoo TW 現金股利發放日.",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({k: report[k] for k in report if k != "updates"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
