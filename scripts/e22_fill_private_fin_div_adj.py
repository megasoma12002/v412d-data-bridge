#!/usr/bin/env python3
"""Fill private FIN (民營金控 + R2 banks) dividend events + adj_close panel.

Research / data hygiene — does NOT expand Soft-Frozen live e21 membership.

- Merges FinMind ``TaiwanStockDividend`` rows for FILL_CODES into
  ``data/dividend_events/e22_dividend_events.csv`` (Soft-Frozen rows kept).
- Builds backward ``adj_close`` for FILL_CODES from TW12 OHLCV × FinMind
  DividendResult / capital-reduction / split factors →
  ``data/market/private_fin_adjusted.csv``.
- Soft-Frozen live ``adj_close`` stays in ``forward/e21/live_market.csv``.

Usage:
  python3 scripts/e22_fill_private_fin_div_adj.py
  python3 scripts/e22_fill_private_fin_div_adj.py --skip-adj
"""
from __future__ import annotations

import argparse
import csv
import json
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIV_PATH = ROOT / "data/dividend_events/e22_dividend_events.csv"
RAW_JSON = ROOT / "data/dividend_events/e22_dividend_raw_private.json"
STATUS = ROOT / "data/dividend_events/e22_private_fin_fill_status.json"
ADJ_OUT = ROOT / "data/market/private_fin_adjusted.csv"
ACTIONS_OUT = ROOT / "data/market/private_fin_corporate_actions.csv"
TW12_CANDIDATES = [
    Path("/tmp/tw12/artifact/v412d_12stocks_2010_2026.csv"),
    ROOT / "artifact/v412d_12stocks_2010_2026.csv",
    ROOT / "artifact/v412e0_12stocks_history_raw.csv",
]

# Soft-Frozen live FIN stays out of FILL — already in e22 ledger + live_market.
PUB_R1 = ["2880", "2886", "2892", "5880"]
PRIV_R3R4 = ["2884", "2885", "2890", "2891", "2881", "2882"]
BANKS_R2 = ["2801", "2834"]
FILL_CODES = PRIV_R3R4 + BANKS_R2

FINMIND = "https://api.finmindtrade.com/api/v4/data"


def number(row: dict, *keys: str) -> float:
    total = 0.0
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            total += float(value)
    return total


def finmind(dataset: str, sid: str | None = None, *, start: str = "2010-01-01") -> list[dict]:
    q: dict[str, str] = {"dataset": dataset, "start_date": start, "end_date": date.today().isoformat()}
    if sid:
        q["data_id"] = sid
    req = urllib.request.Request(
        FINMIND + "?" + urllib.parse.urlencode(q),
        headers={"User-Agent": "v412-private-fin-fill/1.0"},
    )
    with urllib.request.urlopen(req, timeout=120) as response:
        payload = json.load(response)
    if payload.get("status") != 200:
        raise RuntimeError(f"FinMind {dataset} {sid}: {payload}")
    return payload.get("data") or []


def normalize_div_row(code: str, row: dict) -> dict:
    return {
        "code": code,
        "fiscal_year": row.get("year", ""),
        "record_date": row.get("date", ""),
        "announcement_date": row.get("AnnouncementDate", ""),
        "announcement_time": row.get("AnnouncementTime", ""),
        "cash_ex_date": row.get("CashExDividendTradingDate", ""),
        "cash_payment_date": row.get("CashDividendPaymentDate", ""),
        "cash_dividend": number(row, "CashEarningsDistribution", "CashStatutorySurplus"),
        "stock_ex_date": row.get("StockExDividendTradingDate", ""),
        "stock_payment_date": row.get("StockDividendPaymentDate", "") or "",
        "stock_dividend": number(row, "StockEarningsDistribution", "StockStatutorySurplus"),
    }


def merge_dividends(fill_rows: list[dict]) -> dict:
    fields = [
        "code",
        "fiscal_year",
        "record_date",
        "announcement_date",
        "announcement_time",
        "cash_ex_date",
        "cash_payment_date",
        "cash_dividend",
        "stock_ex_date",
        "stock_payment_date",
        "stock_dividend",
    ]
    existing = []
    if DIV_PATH.exists():
        with DIV_PATH.open(encoding="utf-8") as handle:
            existing = [r for r in csv.DictReader(handle) if str(r.get("code", "")).zfill(4) not in set(FILL_CODES)]
    # normalize existing codes to 4-digit strings
    kept = []
    for r in existing:
        row = {k: r.get(k, "") for k in fields}
        row["code"] = str(row["code"]).zfill(4)
        kept.append(row)
    merged = kept + fill_rows
    merged.sort(key=lambda r: (r["code"], str(r.get("cash_ex_date") or r.get("record_date") or "")))
    DIV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DIV_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(merged)
    by_code: dict[str, int] = {}
    for r in merged:
        by_code[r["code"]] = by_code.get(r["code"], 0) + 1
    return {"n_rows": len(merged), "row_counts": by_code, "fill_codes": FILL_CODES}


def build_adj(tw12: Path) -> dict:
    events: dict[str, list[tuple[str, float, str]]] = {c: [] for c in FILL_CODES}
    actions: list[list] = []
    for sid in FILL_CODES:
        for r in finmind("TaiwanStockDividendResult", sid, start="2004-01-01"):
            before = float(r["before_price"])
            after = float(r["after_price"])
            if before > 0 and after > 0:
                factor = after / before
                events[sid].append((r["date"], factor, "dividend_or_rights"))
                actions.append(
                    [
                        sid,
                        r["date"],
                        "dividend_or_rights",
                        before,
                        after,
                        factor,
                        r.get("stock_and_cache_dividend"),
                        r.get("stock_or_cache_dividend"),
                    ]
                )
        time.sleep(0.35)
        for r in finmind("TaiwanStockCapitalReductionReferencePrice", sid, start="2004-01-01"):
            before = float(r["ClosingPriceonTheLastTradingDay"])
            after = float(r["OpeningReferencePrice"])
            if before > 0 and after > 0:
                factor = after / before
                events[sid].append((r["date"], factor, "capital_reduction"))
                actions.append(
                    [
                        sid,
                        r["date"],
                        "capital_reduction",
                        before,
                        after,
                        factor,
                        "",
                        r.get("ReasonforCapitalReduction"),
                    ]
                )
        time.sleep(0.35)
    for r in finmind("TaiwanStockSplitPrice", start="2004-01-01"):
        sid = str(r.get("stock_id", "")).zfill(4)
        if sid not in events:
            continue
        before = float(r["before_price"])
        after = float(r["after_price"])
        if before > 0 and after > 0:
            factor = after / before
            events[sid].append((r["date"], factor, "split_or_par_change"))
            actions.append(
                [sid, r["date"], "split_or_par_change", before, after, factor, "", r.get("type")]
            )
    for sid in events:
        events[sid].sort()

    adjusted: list[list] = []
    with tw12.open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for r in reader:
            sid = str(r["code"]).zfill(4)
            if sid not in events:
                continue
            factor = 1.0
            for event_date, event_factor, _ in events[sid]:
                if event_date > r["date"]:
                    factor *= event_factor
            close = float(r["close"])
            adjusted.append(
                [
                    sid,
                    r["date"],
                    float(r["open"]) * factor,
                    float(r["high"]) * factor,
                    float(r["low"]) * factor,
                    close * factor,
                    r.get("volume", ""),
                    factor,
                    close,
                ]
            )
    adjusted.sort(key=lambda x: (x[1], x[0]))
    actions.sort(key=lambda x: (x[1], x[0]))
    ADJ_OUT.parent.mkdir(parents=True, exist_ok=True)
    with ADJ_OUT.open("w", newline="", encoding="utf-8") as handle:
        w = csv.writer(handle)
        w.writerow(
            [
                "code",
                "date",
                "adjusted_open",
                "adjusted_high",
                "adjusted_low",
                "adjusted_close",
                "volume",
                "backward_adjustment_factor",
                "raw_close",
            ]
        )
        w.writerows(adjusted)
    with ACTIONS_OUT.open("w", newline="", encoding="utf-8") as handle:
        w = csv.writer(handle)
        w.writerow(
            ["code", "date", "action_type", "before_price", "after_price", "factor", "distribution", "detail"]
        )
        w.writerows(actions)
    return {
        "adj_rows": len(adjusted),
        "n_actions": len(actions),
        "event_count_by_stock": {s: len(events[s]) for s in FILL_CODES},
        "tw12_path": str(tw12),
        "adj_path": str(ADJ_OUT.relative_to(ROOT)),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-adj", action="store_true")
    ap.add_argument("--skip-div", action="store_true")
    args = ap.parse_args()

    status: dict = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "E22_PRIVATE_FIN_DIV_ADJ_FILL",
        "fill_codes": FILL_CODES,
        "soft_frozen_pub_r1_unchanged": PUB_R1,
        "live_wire": False,
    }

    if not args.skip_div:
        raw = {}
        fill_rows = []
        for i, code in enumerate(FILL_CODES, 1):
            print(f"div [{i}/{len(FILL_CODES)}] {code} ...", flush=True)
            rows = finmind("TaiwanStockDividend", code)
            raw[code] = rows
            for row in rows:
                fill_rows.append(normalize_div_row(code, row))
            time.sleep(0.4)
        RAW_JSON.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        status["dividends"] = merge_dividends(fill_rows)
        status["dividends"]["raw_path"] = str(RAW_JSON.relative_to(ROOT))
        print("dividends merged:", status["dividends"]["n_rows"], flush=True)

    if not args.skip_adj:
        tw12 = next((p for p in TW12_CANDIDATES if p.exists()), None)
        if tw12 is None:
            raise SystemExit(f"missing TW12/raw OHLCV; tried {TW12_CANDIDATES}")
        print(f"adj from {tw12} ...", flush=True)
        status["adjusted"] = build_adj(tw12)
        print("adj rows:", status["adjusted"]["adj_rows"], flush=True)

    STATUS.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
