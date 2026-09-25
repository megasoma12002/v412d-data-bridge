#!/usr/bin/env python3
"""Fetch point-in-time corporate action fields for the frozen E21 universe.

Hard rules:
  - Does **not** rewrite Soft-Frozen ``forward/e21`` tip / NAV.
  - FinMind often leaves early-year ``CashDividendPaymentDate`` /
    ``StockDividendPaymentDate`` blank; on refresh we **preserve** prior
    non-blank payment dates keyed by ``(code, cash_ex_date)`` /
    ``(code, stock_ex_date)`` so Soft-Frozen DQ / paper-hygiene stay green.
  - Prefer FinMind when it returns a non-blank payment date (live source).

FinMind quota (official; see ``research/ops/FINMIND_API_QUOTA_AND_RETRY.md``):
  - Free + token: **600 req/hour**; no token: **300/hour**
  - Backer 1,600 · Sponsor 6,000 · Sponsor Pro 20,000 / hour
  - Over quota → HTTP **402** ``Requests reach the upper limit``
  - This job: ``len(UNIVERSE)`` requests (~16) per run — fine alone; 402 usually
    means shared hourly budget with E50 / other FinMind jobs.
"""
from __future__ import annotations

import csv
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# Soft-Frozen live + TEL/0050 + FIN research extras (民營金控 / R2 banks).
# Live e21 membership still Soft-Frozen only; extras feed paper / E22 ledger.
UNIVERSE = [
    "2880",
    "2886",
    "2892",
    "5880",
    "2412",
    "3045",
    "4904",
    "0050",
    "2884",
    "2885",
    "2890",
    "2891",
    "2881",
    "2882",
    "2801",
    "2834",
]
URL = "https://api.finmindtrade.com/api/v4/data"
USER_INFO_URL = "https://api.web.finmindtrade.com/v2/user_info"
OUTDIR = Path("data/dividend_events")
EVENTS_CSV = OUTDIR / "e22_dividend_events.csv"
RAW_JSON = OUTDIR / "e22_dividend_raw.json"
STATUS_JSON = OUTDIR / "e22_dividend_fetch_status.json"

# Retry policy: transient network / 5xx / timeout; 402 = hourly quota.
DEFAULT_RETRIES = 5
DEFAULT_PACING_SEC = 0.35
# 402 waits: short retries won't clear an hourly cap — fail closed with a clear
# status after a few spaced attempts (GHA job timeout is 15m).
QUOTA_402_SLEEPS = (30, 60, 90)


def _blank(value) -> bool:
    return value is None or str(value).strip() == "" or str(value).strip().lower() == "nan"


def _norm_code(code) -> str:
    return str(code or "").strip().zfill(4)


def _norm_day(value) -> str:
    return str(value or "").strip()[:10]


def load_prior_payment_maps(path: Path) -> tuple[dict[tuple[str, str], str], dict[tuple[str, str], str]]:
    """Load prior cash/stock payment dates keyed by (code, ex_date)."""
    cash: dict[tuple[str, str], str] = {}
    stock: dict[tuple[str, str], str] = {}
    if not path.is_file():
        return cash, stock
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            code = _norm_code(row.get("code"))
            cex = _norm_day(row.get("cash_ex_date"))
            cpay = _norm_day(row.get("cash_payment_date"))
            sex = _norm_day(row.get("stock_ex_date"))
            spay = _norm_day(row.get("stock_payment_date"))
            if code and cex and not _blank(cpay):
                cash[(code, cex)] = cpay
            if code and sex and not _blank(spay):
                stock[(code, sex)] = spay
    return cash, stock


def apply_prior_payment_dates(
    rows: list[dict],
    prior_cash: dict[tuple[str, str], str],
    prior_stock: dict[tuple[str, str], str],
) -> dict:
    """Fill blank FinMind payment dates from prior ledger (exact ex-date keys)."""
    n_cash = n_stock = 0
    for row in rows:
        code = _norm_code(row.get("code"))
        row["code"] = code
        cex = _norm_day(row.get("cash_ex_date"))
        sex = _norm_day(row.get("stock_ex_date"))
        if _blank(row.get("cash_payment_date")) and cex:
            hit = prior_cash.get((code, cex))
            if hit:
                row["cash_payment_date"] = hit
                n_cash += 1
        if _blank(row.get("stock_payment_date")) and sex:
            hit = prior_stock.get((code, sex))
            if hit:
                row["stock_payment_date"] = hit
                n_stock += 1
    return {
        "preserved_cash_payment_dates": n_cash,
        "preserved_stock_payment_dates": n_stock,
        "prior_cash_keys": len(prior_cash),
        "prior_stock_keys": len(prior_stock),
    }


class FinMindQuotaError(RuntimeError):
    """HTTP 402 / Requests reach the upper limit."""


def _finmind_headers() -> tuple[dict[str, str], bool]:
    headers = {"User-Agent": "v412e22/1.1"}
    token = (os.environ.get("FINMIND_TOKEN") or "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers, bool(token)


def probe_user_info() -> dict | None:
    """Optional quota snapshot when token is set (best-effort; never fails the job)."""
    headers, has_token = _finmind_headers()
    if not has_token:
        return None
    try:
        req = urllib.request.Request(USER_INFO_URL, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            payload = json.load(response)
        return {
            "user_count": payload.get("user_count"),
            "api_request_limit": payload.get("api_request_limit"),
        }
    except Exception as exc:  # noqa: BLE001 — probe only
        return {"error": str(exc)}


def fetch(code: str, *, retries: int = DEFAULT_RETRIES) -> list:
    """Fetch one code with retries. Raises after exhausted attempts."""
    query = urllib.parse.urlencode(
        {
            "dataset": "TaiwanStockDividend",
            "data_id": code,
            "start_date": "2010-01-01",
            "end_date": "2026-12-31",
        }
    )
    headers, _ = _finmind_headers()
    url = URL + "?" + query
    last_err: Exception | None = None
    quota_i = 0
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=120) as response:
                payload = json.load(response)
            status = payload.get("status")
            msg = str(payload.get("msg") or "")
            if status == 402 or "upper limit" in msg.lower():
                raise FinMindQuotaError(f"FinMind {code}: {payload}")
            if status != 200:
                raise RuntimeError(f"FinMind {code}: {payload}")
            return payload.get("data", [])
        except (FinMindQuotaError, urllib.error.HTTPError) as exc:
            last_err = exc
            is_402 = isinstance(exc, FinMindQuotaError) or (
                isinstance(exc, urllib.error.HTTPError) and exc.code == 402
            )
            if is_402:
                if quota_i >= len(QUOTA_402_SLEEPS):
                    raise FinMindQuotaError(
                        f"FinMind quota exceeded (HTTP 402) for {code} after "
                        f"{attempt + 1} attempts; hourly limit — wait or raise tier. "
                        f"See research/ops/FINMIND_API_QUOTA_AND_RETRY.md"
                    ) from exc
                time.sleep(QUOTA_402_SLEEPS[quota_i])
                quota_i += 1
                continue
            if (
                isinstance(exc, urllib.error.HTTPError)
                and exc.code in (429, 500, 502, 503, 504)
                and attempt + 1 < retries
            ):
                time.sleep(2 ** attempt)
                continue
            raise
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_err = exc
            if attempt + 1 < retries:
                time.sleep(2 ** attempt)
                continue
            raise
    if last_err:
        raise last_err
    return []


def number(row, *keys):
    total = 0.0
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            total += float(value)
    return total


def normalize_row(code: str, row: dict) -> dict:
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


def main():
    OUTDIR.mkdir(parents=True, exist_ok=True)
    prior_cash, prior_stock = load_prior_payment_maps(EVENTS_CSV)
    _, has_token = _finmind_headers()
    usage_before = probe_user_info()

    normalized: list[dict] = []
    raw: dict = {}
    for i, code in enumerate(UNIVERSE):
        if i > 0 and DEFAULT_PACING_SEC > 0:
            time.sleep(DEFAULT_PACING_SEC)
        rows = fetch(code)
        raw[code] = rows
        for row in rows:
            normalized.append(normalize_row(code, row))

    preserve = apply_prior_payment_dates(normalized, prior_cash, prior_stock)

    fields = list(normalized[0].keys()) if normalized else ["code"]
    with EVENTS_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(normalized)
    RAW_JSON.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    counts = {code: len(raw[code]) for code in UNIVERSE}
    usage_after = probe_user_info()
    status = {
        "status": "PASS",
        "universe": UNIVERSE,
        "row_counts": counts,
        "rows": len(normalized),
        "finmind_token_used": has_token,
        "finmind_usage_before": usage_before,
        "finmind_usage_after": usage_after,
        "payment_date_preserve": preserve,
        "retries_default": DEFAULT_RETRIES,
        "pacing_sec": DEFAULT_PACING_SEC,
        "quota_note": (
            "Free+token 600/hr; no-token 300/hr; HTTP 402 = hourly cap. "
            f"This run ≈ {len(UNIVERSE)} requests."
        ),
    }
    STATUS_JSON.write_text(
        json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(status, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
