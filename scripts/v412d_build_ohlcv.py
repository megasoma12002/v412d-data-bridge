#!/usr/bin/env python3
"""Build and verify canonical raw/unadjusted OHLCV for V4.12-D."""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Iterable


REQUIRED = ("date", "open", "high", "low", "close", "volume")
MIN_ROWS = 3500


@dataclass(frozen=True)
class Row:
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: float

    def values(self) -> tuple[float, ...]:
        return (self.open, self.high, self.low, self.close, self.volume)


def parse_date(value: str) -> date:
    value = value.strip()
    for fmt in ("%Y%m%d", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"unsupported date: {value!r}")


def parse_number(value: str) -> float:
    cleaned = value.strip().replace(",", "")
    if cleaned in {"", "--", "---", "-", "N/A", "null", "None"}:
        raise ValueError("missing numeric value")
    number = float(cleaned)
    if not math.isfinite(number):
        raise ValueError("non-finite numeric value")
    return number


def normalize_fieldnames(fieldnames: Iterable[str] | None) -> dict[str, str]:
    if not fieldnames:
        return {}
    return {name.strip().lower().lstrip("\ufeff"): name for name in fieldnames}


def load_source_rows(input_dir: Path, code: str, start_date: date) -> tuple[list[Row], dict]:
    by_date: dict[date, Row] = {}
    exact_duplicates = 0
    conflicts: list[str] = []
    scanned_files = 0
    matched_rows = 0

    for path in sorted(input_dir.rglob("*.csv")):
        scanned_files += 1
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            names = normalize_fieldnames(reader.fieldnames)
            needed = {"date", "code", "open", "high", "low", "close", "volume"}
            if not needed.issubset(names):
                continue
            for line_number, raw in enumerate(reader, start=2):
                if str(raw[names["code"]]).strip() != code:
                    continue
                matched_rows += 1
                try:
                    trading_date = parse_date(str(raw[names["date"]]))
                    if trading_date < start_date:
                        continue
                    row = Row(
                        date=trading_date,
                        open=parse_number(str(raw[names["open"]])),
                        high=parse_number(str(raw[names["high"]])),
                        low=parse_number(str(raw[names["low"]])),
                        close=parse_number(str(raw[names["close"]])),
                        volume=parse_number(str(raw[names["volume"]])),
                    )
                except (TypeError, ValueError) as exc:
                    raise ValueError(f"{path}:{line_number}: {exc}") from exc

                previous = by_date.get(trading_date)
                if previous is None:
                    by_date[trading_date] = row
                elif previous == row:
                    exact_duplicates += 1
                else:
                    conflicts.append(
                        f"{trading_date.isoformat()}: {previous.values()} != {row.values()}"
                    )

    if conflicts:
        raise ValueError("conflicting duplicate dates:\n" + "\n".join(conflicts[:20]))

    return sorted(by_date.values(), key=lambda row: row.date), {
        "source_csv_files_scanned": scanned_files,
        "source_rows_matching_code": matched_rows,
        "exact_duplicate_rows_removed": exact_duplicates,
        "conflicting_duplicate_dates": len(conflicts),
    }


def write_csv(rows: list[Row], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(REQUIRED)
        for row in rows:
            writer.writerow(
                (
                    row.date.isoformat(),
                    format(row.open, ".10g"),
                    format(row.high, ".10g"),
                    format(row.low, ".10g"),
                    format(row.close, ".10g"),
                    format(row.volume, ".10g"),
                )
            )


def read_canonical(path: Path) -> list[Row]:
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"missing or empty file: {path}")

    rows: list[Row] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = tuple(reader.fieldnames or ())
        if fields != REQUIRED:
            raise ValueError(f"required columns/order {REQUIRED}; found {fields}")
        for line_number, raw in enumerate(reader, start=2):
            try:
                rows.append(
                    Row(
                        date=parse_date(raw["date"]),
                        open=parse_number(raw["open"]),
                        high=parse_number(raw["high"]),
                        low=parse_number(raw["low"]),
                        close=parse_number(raw["close"]),
                        volume=parse_number(raw["volume"]),
                    )
                )
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{path}:{line_number}: {exc}") from exc
    return rows


def qc(rows: list[Row], path: Path, start_date: date, build_stats: dict | None = None) -> dict:
    dates = [row.date for row in rows]
    duplicate_dates = len(dates) - len(set(dates))
    strictly_increasing = all(a < b for a, b in zip(dates, dates[1:]))
    null_count = sum(not math.isfinite(value) for row in rows for value in row.values())
    high_violations = sum(
        row.high < max(row.open, row.close, row.low) for row in rows
    )
    low_violations = sum(
        row.low > min(row.open, row.close, row.high) for row in rows
    )
    negative_volume_rows = sum(row.volume < 0 for row in rows)

    first_date = dates[0] if dates else None
    last_date = dates[-1] if dates else None
    checks = {
        "file_exists": path.is_file(),
        "file_non_empty": path.is_file() and path.stat().st_size > 0,
        "required_columns_exact": True,
        "row_count_plausible": len(rows) >= MIN_ROWS,
        "first_date_near_requested_start": bool(
            first_date and start_date <= first_date <= date(2010, 1, 8)
        ),
        "latest_date_in_2026": bool(last_date and last_date.year == 2026),
        "dates_strictly_increasing": strictly_increasing,
        "duplicate_dates_zero": duplicate_dates == 0,
        "null_count_zero": null_count == 0,
        "high_invariant": high_violations == 0,
        "low_invariant": low_violations == 0,
        "volume_non_negative": negative_volume_rows == 0,
    }
    sample_indices = sorted({0, len(rows) // 2, len(rows) - 1}) if rows else []
    result = {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "file": str(path),
        "file_size_bytes": path.stat().st_size if path.is_file() else 0,
        "row_count": len(rows),
        "first_date": first_date.isoformat() if first_date else None,
        "last_date": last_date.isoformat() if last_date else None,
        "duplicate_dates": duplicate_dates,
        "null_count": null_count,
        "high_violations": high_violations,
        "low_violations": low_violations,
        "negative_volume_rows": negative_volume_rows,
        "checks": checks,
        "spot_check_candidates": [
            {
                "date": rows[i].date.isoformat(),
                "open": rows[i].open,
                "high": rows[i].high,
                "low": rows[i].low,
                "close": rows[i].close,
                "volume": rows[i].volume,
            }
            for i in sample_indices
        ],
    }
    if build_stats:
        result["build_stats"] = build_stats
    return result


def write_qc(result: dict, json_path: Path, text_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        f"status={result['status']}",
        f"file={result['file']}",
        f"row_count={result['row_count']}",
        f"first_date={result['first_date']}",
        f"last_date={result['last_date']}",
    ]
    lines.extend(f"{key}={value}" for key, value in result["checks"].items())
    text_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path)
    parser.add_argument("--code", default="2880")
    parser.add_argument("--start-date", default="2010-01-04")
    parser.add_argument("--output-dir", type=Path, default=Path("artifact"))
    parser.add_argument("--verify-only", type=Path)
    parser.add_argument("--qc-json", type=Path)
    parser.add_argument("--qc-text", type=Path)
    args = parser.parse_args()

    start_date = parse_date(args.start_date)
    if args.verify_only:
        output_path = args.verify_only
        rows = read_canonical(output_path)
        result = qc(rows, output_path, start_date)
        qc_json = args.qc_json or output_path.with_suffix(".qc.json")
        qc_text = args.qc_text or output_path.with_suffix(".qc.txt")
    else:
        if not args.input_dir:
            parser.error("--input-dir is required unless --verify-only is used")
        rows, build_stats = load_source_rows(args.input_dir, args.code, start_date)
        output_path = args.output_dir / f"{args.code}_2010_2026.csv"
        write_csv(rows, output_path)
        rows = read_canonical(output_path)
        result = qc(rows, output_path, start_date, build_stats)
        qc_json = args.qc_json or args.output_dir / f"{args.code}_qc.json"
        qc_text = args.qc_text or args.output_dir / f"{args.code}_qc.txt"

    write_qc(result, qc_json, qc_text)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
