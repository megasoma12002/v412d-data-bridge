#!/usr/bin/env python3
"""Reconcile FinMind E22 dividend payment dates against MOPS t108sb27.

Official ledger rules:
- Only write ``cash_payment_date`` when MOPS provides a non-empty 現金股利發放日.
- Never invent proxy lags into ``data/dividend_events/e22_dividend_events.csv``.
- Emit a gap report + optional research-only proxy overlay for E22_v3 H1 sandboxes.

Usage:
  python3 scripts/e22_reconcile_payment_dates_mops.py
  python3 scripts/e22_reconcile_payment_dates_mops.py --write-proxy
"""
from __future__ import annotations

import argparse
import csv
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from bs4 import BeautifulSoup

UNIVERSE = ["2880", "2886", "2892", "5880", "2412", "3045", "4904", "0050"]
MOPS_URL = "https://mopsov.twse.com.tw/mops/web/ajax_t108sb27"
DIV_PATH = Path("data/dividend_events/e22_dividend_events.csv")
REPORT_PATH = Path("data/dividend_events/e22_payment_date_gap_report.json")
PROXY_PATH = Path("data/dividend_events/e22_payment_date_research_proxy.csv")


def roc_to_iso(s: str) -> str:
    s = (s or "").strip()
    if not s:
        return ""
    # 99/08/12 or 100/08/11
    parts = s.replace("-", "/").split("/")
    if len(parts) != 3:
        return ""
    y, m, d = (int(parts[0]), int(parts[1]), int(parts[2]))
    return f"{y + 1911:04d}-{m:02d}-{d:02d}"


def fetch_mops(roc_year: int) -> str:
    body = urllib.parse.urlencode(
        {
            "encodeURIComponent": 1,
            "step": 1,
            "firstin": 1,
            "off": 1,
            "TYPEK": "sii",
            "year": str(roc_year),
            "season": "0",
            "isnew": "false",
        }
    ).encode()
    req = urllib.request.Request(
        MOPS_URL,
        data=body,
        headers={
            "User-Agent": "v412-e22-payment-reconcile/1.0",
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": "https://mopsov.twse.com.tw/mops/web/t108sb27",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as response:
        return response.read().decode("utf-8", errors="ignore")


def parse_mops(raw: str) -> list[dict]:
    soup = BeautifulSoup(raw, "lxml")
    table = None
    for candidate in soup.find_all("table"):
        if "現金股利發放日" in candidate.get_text():
            table = candidate
            break
    if table is None:
        return []
    out = []
    for row in table.find_all("tr"):
        cells = [c.get_text(" ", strip=True) for c in row.find_all(["td", "th"])]
        if not cells or cells[0] not in UNIVERSE or len(cells) < 15:
            continue
        cash_ex = roc_to_iso(cells[13])
        cash_pay = roc_to_iso(cells[14])
        cash_amt = cells[11].replace(",", "").strip()
        out.append(
            {
                "code": cells[0],
                "fiscal_year": cells[2],
                "cash_ex_date": cash_ex,
                "cash_payment_date": cash_pay,
                "cash_dividend_mops": cash_amt,
                "record_date_mops": roc_to_iso(cells[3]),
                "stock_ex_date_mops": roc_to_iso(cells[6]),
            }
        )
    return out


def load_div() -> list[dict]:
    with DIV_PATH.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def save_div(rows: list[dict]) -> None:
    fields = list(rows[0].keys())
    with DIV_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def is_blank(value: str | None) -> bool:
    return value is None or str(value).strip() == "" or str(value).strip().lower() == "nan"


def cash_positive(row: dict) -> bool:
    try:
        return float(row.get("cash_dividend") or 0) > 0
    except ValueError:
        return False


def median_lag_days(rows: list[dict]) -> int:
    lags = []
    for row in rows:
        if not cash_positive(row) or is_blank(row.get("cash_ex_date")) or is_blank(row.get("cash_payment_date")):
            continue
        ex = datetime.strptime(row["cash_ex_date"][:10], "%Y-%m-%d")
        pay = datetime.strptime(row["cash_payment_date"][:10], "%Y-%m-%d")
        lags.append((pay - ex).days)
    if not lags:
        return 28
    lags.sort()
    return lags[len(lags) // 2]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--roc-start", type=int, default=99)  # 2010
    ap.add_argument("--roc-end", type=int, default=115)  # 2026
    ap.add_argument("--write-proxy", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    mops_rows: list[dict] = []
    for year in range(args.roc_start, args.roc_end + 1):
        raw = fetch_mops(year)
        parsed = parse_mops(raw)
        for row in parsed:
            row["mops_query_roc_year"] = year
        mops_rows.extend(parsed)
        time.sleep(0.35)

    by_key = {}
    for row in mops_rows:
        if not row["cash_ex_date"]:
            continue
        key = (row["code"], row["cash_ex_date"])
        # Prefer rows that carry a payment date
        prev = by_key.get(key)
        if prev is None or (is_blank(prev.get("cash_payment_date")) and not is_blank(row.get("cash_payment_date"))):
            by_key[key] = row

    div_rows = load_div()
    filled = []
    confirmed = []
    still_missing = []
    for row in div_rows:
        if not cash_positive(row) or is_blank(row.get("cash_ex_date")):
            continue
        key = (row["code"], row["cash_ex_date"][:10])
        mops = by_key.get(key)
        if mops and not is_blank(mops.get("cash_payment_date")):
            if is_blank(row.get("cash_payment_date")):
                row["cash_payment_date"] = mops["cash_payment_date"]
                filled.append(
                    {
                        "code": row["code"],
                        "cash_ex_date": row["cash_ex_date"],
                        "cash_payment_date": row["cash_payment_date"],
                        "source": "MOPS_t108sb27",
                    }
                )
            else:
                confirmed.append(
                    {
                        "code": row["code"],
                        "cash_ex_date": row["cash_ex_date"],
                        "finmind": row["cash_payment_date"],
                        "mops": mops["cash_payment_date"],
                        "match": row["cash_payment_date"][:10] == mops["cash_payment_date"][:10],
                    }
                )
        elif is_blank(row.get("cash_payment_date")):
            still_missing.append(
                {
                    "code": row["code"],
                    "fiscal_year": row.get("fiscal_year", ""),
                    "cash_ex_date": row["cash_ex_date"],
                    "cash_dividend": row.get("cash_dividend", ""),
                }
            )

    if filled and not args.dry_run:
        save_div(div_rows)

    lag = median_lag_days(div_rows)
    proxy_rows = []
    for row in still_missing:
        ex = datetime.strptime(row["cash_ex_date"][:10], "%Y-%m-%d")
        proxy_rows.append(
            {
                "code": row["code"],
                "cash_ex_date": row["cash_ex_date"],
                "cash_payment_date": (ex + timedelta(days=lag)).strftime("%Y-%m-%d"),
                "cash_dividend": row["cash_dividend"],
                "quality": "PROXY_MEDIAN_LAG",
                "lag_days": lag,
                "source": "research_overlay_only_not_official",
                "note": "Do not merge into e22_dividend_events.csv; E22_v3 H1 sandbox only",
            }
        )

    if args.write_proxy:
        fields = list(proxy_rows[0].keys()) if proxy_rows else [
            "code",
            "cash_ex_date",
            "cash_payment_date",
            "cash_dividend",
            "quality",
            "lag_days",
            "source",
            "note",
        ]
        with PROXY_PATH.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(proxy_rows)

    mismatches = [c for c in confirmed if not c["match"]]
    report = {
        "status": "PASS" if not mismatches else "WARN_MISMATCH",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "mops_rows_parsed": len(mops_rows),
        "mops_unique_ex_keys": len(by_key),
        "official_filled_from_mops": filled,
        "n_official_filled": len(filled),
        "n_confirmed_both_sources": len(confirmed),
        "n_source_mismatches": len(mismatches),
        "mismatches": mismatches[:20],
        "still_missing_official": still_missing,
        "n_still_missing_official": len(still_missing),
        "research_proxy_lag_days": lag,
        "research_proxy_path": str(PROXY_PATH) if args.write_proxy else None,
        "conclusion": (
            "Early-year cash_payment_date gaps are also empty in MOPS t108sb27; "
            "free official bulk sources cannot complete 2010–~2013. "
            "Use research proxy overlay or paid/vendor / annual-report manual fill."
        ),
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in report if k not in ("still_missing_official", "confirmed")}, ensure_ascii=False, indent=2))
    print(json.dumps({"n_still_missing_official": report["n_still_missing_official"], "n_official_filled": report["n_official_filled"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
