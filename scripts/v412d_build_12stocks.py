#!/usr/bin/env python3
"""Build all 12 V4.12-D canonical stock files in one archive scan."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path

from v412d_build_ohlcv import (
    Row,
    normalize_fieldnames,
    parse_date,
    parse_number,
    qc,
    read_canonical,
    write_csv,
    write_qc,
)


TARGETS = (
    "2880",
    "2886",
    "2892",
    "5880",
    "2801",
    "2834",
    "2884",
    "2885",
    "2890",
    "2891",
    "2881",
    "2882",
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--start-date", default="2010-01-04")
    args = parser.parse_args()

    start_date = parse_date(args.start_date)
    target_set = set(TARGETS)
    rows_by_code: dict[str, dict[date, Row]] = {code: {} for code in TARGETS}
    exact_duplicates = {code: 0 for code in TARGETS}
    skipped_missing_ohlcv: dict[str, list[dict[str, str]]] = {
        code: [] for code in TARGETS
    }
    source_files = 0

    for path in sorted(args.input_dir.rglob("*.csv")):
        source_files += 1
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            names = normalize_fieldnames(reader.fieldnames)
            needed = {"date", "code", "open", "high", "low", "close", "volume"}
            if not needed.issubset(names):
                continue
            for line_number, raw in enumerate(reader, start=2):
                code = str(raw[names["code"]]).strip()
                if code not in target_set:
                    continue
                trading_date = parse_date(str(raw[names["date"]]))
                if trading_date < start_date:
                    continue
                try:
                    row = Row(
                        date=trading_date,
                        open=parse_number(str(raw[names["open"]])),
                        high=parse_number(str(raw[names["high"]])),
                        low=parse_number(str(raw[names["low"]])),
                        close=parse_number(str(raw[names["close"]])),
                        volume=parse_number(str(raw[names["volume"]])),
                    )
                except (TypeError, ValueError) as exc:
                    if str(exc) == "missing numeric value":
                        skipped_missing_ohlcv[code].append(
                            {
                                "date": trading_date.isoformat(),
                                "open": str(raw[names["open"]]),
                                "high": str(raw[names["high"]]),
                                "low": str(raw[names["low"]]),
                                "close": str(raw[names["close"]]),
                                "volume": str(raw[names["volume"]]),
                            }
                        )
                        continue
                    raise ValueError(f"{path}:{line_number}: {exc}") from exc

                previous = rows_by_code[code].get(trading_date)
                if previous is None:
                    rows_by_code[code][trading_date] = row
                elif previous == row:
                    exact_duplicates[code] += 1
                else:
                    raise ValueError(
                        f"conflicting duplicate {code} {trading_date}: "
                        f"{previous.values()} != {row.values()}"
                    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "status": "PASS",
        "targets": list(TARGETS),
        "source_csv_files_scanned": source_files,
        "stocks": {},
    }
    canonical_by_code: dict[str, list[Row]] = {}
    for code in TARGETS:
        rows = sorted(rows_by_code[code].values(), key=lambda row: row.date)
        output_path = args.output_dir / f"{code}_2010_2026.csv"
        write_csv(rows, output_path)
        reread = read_canonical(output_path)
        canonical_by_code[code] = reread
        result = qc(
            reread,
            output_path,
            start_date,
            {
                "source_csv_files_scanned": source_files,
                "exact_duplicate_rows_removed": exact_duplicates[code],
                "conflicting_duplicate_dates": 0,
                "missing_ohlcv_source_rows_skipped": len(
                    skipped_missing_ohlcv[code]
                ),
                "missing_ohlcv_examples": skipped_missing_ohlcv[code][:20],
            },
        )
        write_qc(
            result,
            args.output_dir / f"{code}_qc.json",
            args.output_dir / f"{code}_qc.txt",
        )
        summary["stocks"][code] = {
            "status": result["status"],
            "row_count": result["row_count"],
            "first_date": result["first_date"],
            "last_date": result["last_date"],
            "missing_ohlcv_source_rows_skipped": len(
                skipped_missing_ohlcv[code]
            ),
            "missing_ohlcv_examples": skipped_missing_ohlcv[code][:20],
        }
        if result["status"] != "PASS":
            summary["status"] = "FAIL"

    combined_path = args.output_dir / "v412d_12stocks_2010_2026.csv"
    with combined_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(("code", "date", "open", "high", "low", "close", "volume"))
        for code in TARGETS:
            for row in canonical_by_code[code]:
                writer.writerow(
                    (
                        code,
                        row.date.isoformat(),
                        format(row.open, ".10g"),
                        format(row.high, ".10g"),
                        format(row.low, ".10g"),
                        format(row.close, ".10g"),
                        format(row.volume, ".10g"),
                    )
                )
    summary["combined_file"] = str(combined_path)
    summary["combined_row_count"] = sum(
        len(rows) for rows in canonical_by_code.values()
    )
    summary_path = args.output_dir / "v412d_12stocks_qc_summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if summary["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
