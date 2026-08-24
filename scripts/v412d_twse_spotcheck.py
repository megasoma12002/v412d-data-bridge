#!/usr/bin/env python3
"""Spot-check canonical OHLCV against the official TWSE MI_INDEX API."""

from __future__ import annotations

import argparse
import csv
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path


REQUIRED_FIELDS = {
    "code": ("證券代號", "股票代號"),
    "volume": ("成交股數",),
    "open": ("開盤價",),
    "high": ("最高價",),
    "low": ("最低價",),
    "close": ("收盤價",),
}


def number(value: str) -> float:
    return float(str(value).strip().replace(",", ""))


def load_canonical(path: Path) -> dict[str, dict[str, float]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return {
            row["date"]: {
                key: number(row[key])
                for key in ("open", "high", "low", "close", "volume")
            }
            for row in csv.DictReader(handle)
        }


def fetch_json(date_iso: str, attempts: int = 5) -> dict:
    query = urllib.parse.urlencode(
        {
            "response": "json",
            "date": date_iso.replace("-", ""),
            "type": "ALLBUT0999",
        }
    )
    request = urllib.request.Request(
        f"https://www.twse.com.tw/exchangeReport/MI_INDEX?{query}",
        headers={
            "User-Agent": "Mozilla/5.0 V412D-Official-Spotcheck/1.0",
            "Accept": "application/json,text/plain,*/*",
        },
    )
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode("utf-8-sig"))
        except Exception:
            if attempt == attempts - 1:
                raise
            time.sleep(2**attempt)
    raise AssertionError("unreachable")


def find_official_row(payload: dict, code: str) -> dict[str, float]:
    tables: list[tuple[list[str], list[list[str]]]] = []
    for table in payload.get("tables", []):
        tables.append((table.get("fields", []), table.get("data", [])))
    for suffix in ("", "8", "9"):
        fields = payload.get(f"fields{suffix}")
        data = payload.get(f"data{suffix}")
        if fields and data:
            tables.append((fields, data))

    for fields, data in tables:
        cleaned = [str(field).strip() for field in fields]
        indices: dict[str, int] = {}
        for key, aliases in REQUIRED_FIELDS.items():
            for alias in aliases:
                if alias in cleaned:
                    indices[key] = cleaned.index(alias)
                    break
        if set(indices) != set(REQUIRED_FIELDS):
            continue
        for row in data:
            if str(row[indices["code"]]).strip() == code:
                return {
                    key: number(row[index])
                    for key, index in indices.items()
                    if key != "code"
                }
    raise ValueError(f"code {code} not found in TWSE response")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--code", default="2880")
    parser.add_argument("--dates", nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    canonical = load_canonical(args.csv)
    comparisons = []
    for date_iso in args.dates:
        if date_iso not in canonical:
            raise ValueError(f"date missing from canonical CSV: {date_iso}")
        official = find_official_row(fetch_json(date_iso), args.code)
        local = canonical[date_iso]
        fields_match = {key: official[key] == local[key] for key in official}
        comparisons.append(
            {
                "date": date_iso,
                "official_twse": official,
                "canonical_csv": local,
                "fields_match": fields_match,
                "status": "PASS" if all(fields_match.values()) else "FAIL",
            }
        )

    result = {
        "source": "TWSE MI_INDEX official API",
        "code": args.code,
        "status": (
            "PASS"
            if all(item["status"] == "PASS" for item in comparisons)
            else "FAIL"
        ),
        "comparisons": comparisons,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
