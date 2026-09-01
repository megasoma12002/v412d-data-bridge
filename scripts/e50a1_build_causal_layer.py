#!/usr/bin/env python3
"""Build resumable E50-A1 corporate-action and causal-fundamental shards.

The period date supplied by a vendor is never treated as the knowledge date.
Every normalized record receives an explicit conservative available_date.
"""
from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

API = "https://api.finmindtrade.com/api/v4/data"
PER_CODE = {
    "income": "TaiwanStockFinancialStatements",
    "balance": "TaiwanStockBalanceSheet",
    "cashflow": "TaiwanStockCashFlowsStatement",
    "revenue": "TaiwanStockMonthRevenue",
    "dividend_policy": "TaiwanStockDividend",
    "dividend_result": "TaiwanStockDividendResult",
    "capital_reduction": "TaiwanStockCapitalReductionReferencePrice",
}
ALL_MARKET = {
    "split": "TaiwanStockSplitPrice",
    "par_value_change": "TaiwanStockParValueChange",
}


def api_get(dataset: str, token: str, stock_id: str | None = None,
            start: str | None = None, end: str | None = None,
            retries: int = 4) -> list[dict]:
    query = {"dataset": dataset}
    if stock_id:
        query["data_id"] = stock_id
    if start:
        query["start_date"] = start
    if end:
        query["end_date"] = end
    headers = {"User-Agent": "v412-e50a1/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    url = API + "?" + urllib.parse.urlencode(query)
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(
                urllib.request.Request(url, headers=headers), timeout=120
            ) as response:
                payload = json.load(response)
            if payload.get("status") != 200:
                raise RuntimeError(f"FinMind status={payload.get('status')} msg={payload.get('msg')}")
            return payload.get("data") or []
        except Exception:
            if attempt + 1 == retries:
                raise
            time.sleep(2 ** attempt)
    return []


def write_frame(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, compression="gzip")


def load_frames(folder: Path) -> pd.DataFrame:
    files = sorted(folder.glob("*.csv.gz"))
    frames = []
    for path in files:
        try:
            frame = pd.read_csv(path, dtype={"stock_id": str})
        except pd.errors.EmptyDataError:
            continue
        if not frame.empty:
            frames.append(frame)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def next_trading_day(values: pd.Series, calendar: np.ndarray) -> pd.Series:
    parsed = pd.to_datetime(values, errors="coerce")
    out = []
    for value in parsed:
        if pd.isna(value):
            out.append(pd.NaT)
            continue
        pos = np.searchsorted(calendar, np.datetime64(value.normalize()), side="right")
        out.append(pd.Timestamp(calendar[pos]) if pos < len(calendar) else pd.NaT)
    return pd.Series(out, index=values.index)


def financial_deadline(period_end: pd.Series) -> pd.Series:
    d = pd.to_datetime(period_end, errors="coerce")
    result = []
    for x in d:
        if pd.isna(x):
            result.append(pd.NaT)
        elif x.month == 3:
            result.append(pd.Timestamp(x.year, 5, 15))
        elif x.month == 6:
            result.append(pd.Timestamp(x.year, 8, 14))
        elif x.month == 9:
            result.append(pd.Timestamp(x.year, 11, 14))
        elif x.month == 12:
            result.append(pd.Timestamp(x.year + 1, 3, 31))
        else:
            result.append(pd.NaT)
    return pd.Series(result, index=period_end.index)


def normalize_financials(raw_root: Path, calendar: np.ndarray) -> pd.DataFrame:
    frames = []
    for statement in ("income", "balance", "cashflow"):
        d = load_frames(raw_root / statement)
        if d.empty:
            continue
        d["statement"] = statement
        d["period_end"] = pd.to_datetime(d["date"], errors="coerce")
        d["knowledge_date_basis"] = financial_deadline(d["period_end"])
        d["available_date"] = next_trading_day(d["knowledge_date_basis"], calendar)
        d["availability_policy"] = "statutory_deadline_plus_next_trading_day"
        d["value"] = pd.to_numeric(d.get("value"), errors="coerce")
        d["eps_cross_period_addition_safe"] = d.get("type", "").astype(str).ne("EPS")
        frames.append(d[["stock_id", "statement", "period_end", "type", "value",
                         "origin_name", "knowledge_date_basis", "available_date",
                         "availability_policy", "eps_cross_period_addition_safe"]])
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True).drop_duplicates(
        ["stock_id", "statement", "period_end", "type"], keep="last"
    ).sort_values(["available_date", "stock_id", "statement", "type"])


def normalize_revenue(raw_root: Path, calendar: np.ndarray) -> pd.DataFrame:
    d = load_frames(raw_root / "revenue")
    if d.empty:
        return d
    d["revenue_year"] = pd.to_numeric(d["revenue_year"], errors="coerce").astype("Int64")
    d["revenue_month"] = pd.to_numeric(d["revenue_month"], errors="coerce").astype("Int64")
    d["period_end"] = pd.to_datetime(
        d.revenue_year.astype(str) + "-" + d.revenue_month.astype(str) + "-01", errors="coerce"
    ) + pd.offsets.MonthEnd(0)
    d["statutory_deadline"] = d.period_end + pd.offsets.MonthBegin(1) + pd.Timedelta(days=9)
    create = pd.to_datetime(d.get("create_time", ""), errors="coerce")
    valid_create = create.where(create.gt(pd.Timestamp("2026-04-21")))
    d["knowledge_date_basis"] = pd.concat(
        [d.statutory_deadline, valid_create.rename("create")], axis=1
    ).max(axis=1)
    d["available_date"] = next_trading_day(d.knowledge_date_basis, calendar)
    d["availability_policy"] = np.where(
        valid_create.notna(), "later_of_statutory_deadline_or_vendor_create_time",
        "statutory_deadline_plus_next_trading_day"
    )
    d["revenue"] = pd.to_numeric(d.revenue, errors="coerce")
    return d[["stock_id", "period_end", "revenue_year", "revenue_month", "revenue",
              "create_time", "knowledge_date_basis", "available_date",
              "availability_policy"]].drop_duplicates(
        ["stock_id", "period_end"], keep="last"
    ).sort_values(["available_date", "stock_id"])


def normalize_actions(raw_root: Path, calendar: np.ndarray) -> tuple[pd.DataFrame, pd.DataFrame]:
    policy = load_frames(raw_root / "dividend_policy")
    ledger = []
    if not policy.empty:
        announce = pd.to_datetime(policy.get("AnnouncementDate"), errors="coerce")
        available = next_trading_day(announce, calendar)
        cash = (pd.to_numeric(policy.get("CashEarningsDistribution"), errors="coerce").fillna(0)
                + pd.to_numeric(policy.get("CashStatutorySurplus"), errors="coerce").fillna(0))
        stock_amount = (pd.to_numeric(policy.get("StockEarningsDistribution"), errors="coerce").fillna(0)
                        + pd.to_numeric(policy.get("StockStatutorySurplus"), errors="coerce").fillna(0))
        for kind, effective_col in (("cash_dividend", "CashExDividendTradingDate"),
                                    ("stock_dividend", "StockExDividendTradingDate")):
            amount = cash if kind == "cash_dividend" else stock_amount
            x = pd.DataFrame({
                "stock_id": policy.stock_id.astype(str), "event_type": kind,
                "announcement_date": announce, "available_date": available,
                "effective_date": pd.to_datetime(policy.get(effective_col), errors="coerce"),
                "cash_payment_date": pd.to_datetime(policy.get("CashDividendPaymentDate"), errors="coerce") if kind == "cash_dividend" else pd.NaT,
                "cash_per_old_share": amount if kind == "cash_dividend" else 0.0,
                "share_multiplier": 1.0 if kind == "cash_dividend" else 1.0 + amount / 10.0,
                "availability_policy": "announcement_plus_next_trading_day",
                "source_dataset": "TaiwanStockDividend",
            })
            ledger.append(x[(amount.ne(0)) | x.effective_date.notna()])
    for folder, kind, source in [
        ("split", "split_or_reverse_split", "TaiwanStockSplitPrice"),
        ("par_value_change", "par_value_change", "TaiwanStockParValueChange"),
        ("capital_reduction", "capital_reduction", "TaiwanStockCapitalReductionReferencePrice"),
    ]:
        d = load_frames(raw_root / folder)
        if d.empty:
            continue
        before_col = "before_price" if "before_price" in d else ("before_close" if "before_close" in d else "ClosingPriceonTheLastTradingDay")
        after_col = "after_price" if "after_price" in d else ("after_ref_close" if "after_ref_close" in d else "PostReductionReferencePrice")
        before = pd.to_numeric(d[before_col], errors="coerce")
        after = pd.to_numeric(d[after_col], errors="coerce")
        effective = pd.to_datetime(d.date, errors="coerce")
        ledger.append(pd.DataFrame({
            "stock_id": d.stock_id.astype(str), "event_type": kind,
            "announcement_date": pd.NaT, "available_date": effective,
            "effective_date": effective, "cash_payment_date": pd.NaT,
            "cash_per_old_share": 0.0, "share_multiplier": before / after,
            "availability_policy": "effective_date_only_not_pre_event_signal",
            "source_dataset": source,
        }))
    events = pd.concat(ledger, ignore_index=True) if ledger else pd.DataFrame()
    if not events.empty:
        events = events.drop_duplicates(
            ["stock_id", "event_type", "effective_date", "cash_per_old_share", "share_multiplier"],
            keep="last"
        ).sort_values(["effective_date", "stock_id", "event_type"])
    results = load_frames(raw_root / "dividend_result")
    if not results.empty:
        results["effective_date"] = pd.to_datetime(results.date, errors="coerce")
        results["information_role"] = "ex_post_execution_adjustment_only"
        results = results.drop_duplicates(["stock_id", "effective_date"], keep="last")
    return events, results


def qc(financial: pd.DataFrame, revenue: pd.DataFrame, events: pd.DataFrame,
       result: pd.DataFrame, manifest: pd.DataFrame) -> dict:
    future_fin = int((financial.available_date <= financial.period_end).sum()) if len(financial) else 0
    future_rev = int((revenue.available_date <= revenue.period_end).sum()) if len(revenue) else 0
    bad_event = int((pd.to_numeric(events.share_multiplier, errors="coerce") <= 0).sum()) if len(events) else 0
    failed = int(manifest.status.eq("FAIL").sum()) if len(manifest) else 0
    duplicate_fin = int(financial.duplicated(["stock_id", "statement", "period_end", "type"]).sum()) if len(financial) else 0
    duplicate_rev = int(revenue.duplicated(["stock_id", "period_end"]).sum()) if len(revenue) else 0
    status = "PASS" if not any([future_fin, future_rev, bad_event, failed, duplicate_fin, duplicate_rev]) else "FAIL"
    return {
        "version": "V4.12-E50-A1",
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "codes_attempted": int(manifest.stock_id.nunique()) if len(manifest) else 0,
        "requests": int(len(manifest)), "failed_requests": failed,
        "financial_rows": int(len(financial)), "revenue_rows": int(len(revenue)),
        "corporate_action_rows": int(len(events)), "dividend_result_rows": int(len(result)),
        "financial_lookahead_violations": future_fin,
        "revenue_lookahead_violations": future_rev,
        "nonpositive_share_multipliers": bad_event,
        "duplicate_financial_keys": duplicate_fin, "duplicate_revenue_keys": duplicate_rev,
        "availability_contract": {
            "quarterly_financials": "statutory deadline, usable next trading day",
            "monthly_revenue": "later of statutory deadline or reliable vendor create_time, usable next trading day",
            "dividend_policy": "announcement, usable next trading day",
            "dividend_result": "ex-post adjustment only; never a pre-event signal",
        },
        "known_limitations": [
            "FinMind free-tier all-market fundamentals are unavailable; full history is batch-resumable.",
            "Exact historical MOPS filing timestamps are not present in FinMind statements; conservative statutory deadlines are used.",
            "Monthly revenue create_time before 2026-04-21 is unavailable and is replaced by the statutory deadline.",
            "The layer emits adjustment events; a causal total-return price index is built only after full event backfill.",
        ],
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="e50a1_data")
    p.add_argument("--codes-file", type=Path)
    p.add_argument("--codes", default="")
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--start", default="2004-01-01")
    p.add_argument("--end", default=date.today().isoformat())
    p.add_argument("--throttle-seconds", type=float, default=0.1)
    p.add_argument("--refresh", action="store_true")
    p.add_argument("--normalize-only", action="store_true",
                   help="normalize already downloaded shards without per-code API requests")
    a = p.parse_args()
    out = Path(a.out); raw_root = out / "raw"; out.mkdir(parents=True, exist_ok=True)
    token = os.environ.get("FINMIND_TOKEN", "")
    codes = [x.strip() for x in a.codes.split(",") if x.strip()]
    if a.codes_file:
        codes.extend(x.strip() for x in a.codes_file.read_text().splitlines() if x.strip())
    codes = sorted(set(x for x in codes if x.isdigit() and len(x) == 4))
    if a.offset:
        codes = codes[a.offset:]
    if a.limit:
        codes = codes[:a.limit]
    manifest = []
    for code in ([] if a.normalize_only else codes):
        for folder, dataset in PER_CODE.items():
            path = raw_root / folder / f"{code}.csv.gz"
            if path.exists() and not a.refresh:
                manifest.append({"stock_id": code, "dataset": dataset, "status": "CACHED", "rows": -1})
                continue
            try:
                rows = api_get(dataset, token, code, a.start, a.end)
                write_frame(pd.DataFrame(rows), path)
                manifest.append({"stock_id": code, "dataset": dataset, "status": "PASS", "rows": len(rows)})
            except Exception as exc:
                manifest.append({"stock_id": code, "dataset": dataset, "status": "FAIL", "rows": 0,
                                 "error": f"{type(exc).__name__}: {str(exc)[:200]}"})
            time.sleep(a.throttle_seconds)
    for folder, dataset in ([] if a.normalize_only else ALL_MARKET.items()):
        path = raw_root / folder / "ALL.csv.gz"
        if path.exists() and not a.refresh:
            continue
        try:
            rows = api_get(dataset, token, start=a.start, end=a.end)
            write_frame(pd.DataFrame(rows), path)
            manifest.append({"stock_id": "ALL", "dataset": dataset, "status": "PASS", "rows": len(rows)})
        except Exception as exc:
            manifest.append({"stock_id": "ALL", "dataset": dataset, "status": "FAIL", "rows": 0,
                             "error": f"{type(exc).__name__}: {str(exc)[:200]}"})
    calendar_rows = api_get("TaiwanStockTradingDate", token)
    calendar_frame = pd.DataFrame(calendar_rows)
    calendar_col = "date" if "date" in calendar_frame else calendar_frame.columns[0]
    calendar = np.sort(pd.to_datetime(calendar_frame[calendar_col], errors="coerce").dropna().values)
    manifest_path = out / "download_manifest.csv"
    if a.normalize_only and manifest_path.exists():
        manifest_frame = pd.read_csv(manifest_path, dtype={"stock_id": str})
    else:
        manifest_frame = pd.DataFrame(manifest, columns=["stock_id", "dataset", "status", "rows", "error"])
    financial = normalize_financials(raw_root, calendar)
    revenue = normalize_revenue(raw_root, calendar)
    events, results = normalize_actions(raw_root, calendar)
    write_frame(financial, out / "causal_financials.csv.gz")
    write_frame(revenue, out / "causal_monthly_revenue.csv.gz")
    write_frame(events, out / "corporate_action_ledger.csv.gz")
    write_frame(results, out / "dividend_results_ex_post.csv.gz")
    manifest_frame.to_csv(manifest_path, index=False)
    status = qc(financial, revenue, events, results, manifest_frame)
    (out / "qc_status.json").write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(status, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
