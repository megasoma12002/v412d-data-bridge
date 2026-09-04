#!/usr/bin/env python3
"""Fetch advanced research datasets that are optional for ops but needed for next probes.

Writes under ``data/research_advanced/`` + status JSON. Does not touch frozen ledgers.
"""
from __future__ import annotations

import argparse
import csv
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

UA = "v412-adv-research/1.0"
OUT = Path("data/research_advanced")
UNIVERSE = ["2880", "2886", "2892", "5880", "2412", "3045", "4904", "0050", "2330", "2317", "2454"]


def http_json(url: str, timeout: int = 120):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        raw = response.read()
    text = raw.decode("utf-8-sig", errors="ignore")
    return json.loads(text)


def finmind(dataset: str, data_id: str | None = None, start: str = "2018-01-01", end: str = "2026-09-04"):
    q = {"dataset": dataset, "start_date": start, "end_date": end}
    if data_id:
        q["data_id"] = data_id
    url = "https://api.finmindtrade.com/api/v4/data?" + urllib.parse.urlencode(q)
    return http_json(url)


def save_csv(rows: list[dict], path: Path) -> int:
    if not rows:
        path.write_text("")
        return 0
    fields = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def fetch_twse_company_profile(out: Path, status: dict) -> None:
    url = "https://openapi.twse.com.tw/v1/opendata/t187ap03_L"
    rows = http_json(url)
    # normalize keys of interest
    slim = []
    for r in rows:
        slim.append(
            {
                "code": str(r.get("公司代號") or "").strip(),
                "name": str(r.get("公司簡稱") or r.get("公司名稱") or "").strip(),
                "industry": str(r.get("產業別") or "").strip(),
                "listing_date": str(r.get("上市日期") or "").strip(),
                "asof_table_date": str(r.get("出表日期") or "").strip(),
                "source": "TWSE_openapi_t187ap03_L",
                "pit_note": "CURRENT_SNAPSHOT_NOT_HISTORICAL_RECLASS",
            }
        )
    n = save_csv(slim, out / "twse_company_industry_snapshot.csv")
    status["twse_company_industry_snapshot"] = {
        "status": "PASS" if n else "EMPTY",
        "rows": n,
        "path": str(out / "twse_company_industry_snapshot.csv"),
        "limitation": "Snapshot only — not historical industry PIT (T3 still open for TWT58U archive)",
    }


def fetch_twse_margin_snapshot(out: Path, status: dict) -> None:
    url = "https://openapi.twse.com.tw/v1/exchangeReport/MI_MARGN"
    rows = http_json(url)
    n = save_csv(rows, out / "twse_mi_margn_snapshot.json.csv")
    # also json
    (out / "twse_mi_margn_snapshot.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
    status["twse_mi_margn_snapshot"] = {
        "status": "PASS" if n else "EMPTY",
        "rows": n,
        "path": str(out / "twse_mi_margn_snapshot.json"),
        "limitation": "Daily snapshot endpoint — historical series via FinMind margin table",
    }


def fetch_finmind_info(out: Path, status: dict) -> None:
    payload = finmind("TaiwanStockInfo")
    rows = payload.get("data") or []
    n = save_csv(rows, out / "finmind_taiwan_stock_info_snapshot.csv")
    status["finmind_stock_info"] = {
        "status": "PASS" if payload.get("status") == 200 and n else "FAIL",
        "rows": n,
        "api_status": payload.get("status"),
        "limitation": "Current industry_category snapshot; multi-tag rows possible",
    }


def fetch_finmind_per_code(
    out: Path,
    status: dict,
    *,
    dataset: str,
    key: str,
    codes: list[str],
    start: str,
    sleep: float,
) -> None:
    chunks = []
    errors = []
    for i, code in enumerate(codes):
        try:
            payload = finmind(dataset, code, start=start)
            rows = payload.get("data") or []
            for r in rows:
                r = dict(r)
                r.setdefault("stock_id", code)
                chunks.append(r)
            print(f"  {dataset} {i+1}/{len(codes)} {code} n={len(rows)}", flush=True)
        except Exception as exc:  # noqa: BLE001
            errors.append({"code": code, "error": f"{type(exc).__name__}:{exc}"})
            print(f"  {dataset} FAIL {code}: {exc}", flush=True)
        time.sleep(sleep)
    path = out / f"finmind_{key}_history.csv"
    n = save_csv(chunks, path)
    status[f"finmind_{key}"] = {
        "status": "PASS" if n else "EMPTY",
        "rows": n,
        "codes_ok": len(codes) - len(errors),
        "errors": errors[:20],
        "path": str(path),
        "start_date": start,
    }


def fetch_futures_oi(out: Path, status: dict) -> None:
    # TX near contracts
    try:
        payload = finmind("TaiwanFuturesDaily", "TX", start="2018-01-01")
        rows = payload.get("data") or []
        n = save_csv(rows, out / "finmind_tx_futures_daily.csv")
        status["finmind_tx_futures_daily"] = {
            "status": "PASS" if n else "EMPTY",
            "rows": n,
            "has_open_interest": bool(rows and "open_interest" in rows[0]),
            "path": str(out / "finmind_tx_futures_daily.csv"),
        }
    except Exception as exc:  # noqa: BLE001
        status["finmind_tx_futures_daily"] = {"status": "FAIL", "error": str(exc)}


def fetch_options_probe(out: Path, status: dict) -> None:
    # Probe common option dataset names; record which work
    probes = []
    for dataset, data_id in [
        ("TaiwanOptionPrice", "TXO"),
        ("TaiwanOptionDaily", "TXO"),
        ("TaiwanStockOptionPrice", "TXO"),
    ]:
        try:
            payload = finmind(dataset, data_id, start="2024-01-02", end="2024-01-05")
            n = len(payload.get("data") or [])
            probes.append({"dataset": dataset, "data_id": data_id, "status": payload.get("status"), "rows": n, "msg": payload.get("msg")})
            if n:
                save_csv(payload["data"], out / f"finmind_{dataset.lower()}_sample.csv")
        except Exception as exc:  # noqa: BLE001
            probes.append({"dataset": dataset, "data_id": data_id, "status": "ERR", "error": f"{type(exc).__name__}:{exc}"})
        time.sleep(0.2)
    status["finmind_options_probe"] = {
        "status": "PASS" if any((p.get("rows") or 0) > 0 for p in probes) else "UNAVAILABLE_OR_MEMBER",
        "probes": probes,
        "limitation": "Full option chains often require FinMind paid tier",
    }


def fetch_tick_probe(out: Path, status: dict) -> None:
    probes = []
    for dataset in ["TaiwanStockPriceTick", "TaiwanStockTick"]:
        try:
            payload = finmind(dataset, "2330", start="2024-01-02", end="2024-01-02")
            n = len(payload.get("data") or [])
            probes.append({"dataset": dataset, "status": payload.get("status"), "rows": n, "msg": payload.get("msg")})
            if n:
                save_csv(payload["data"][:5000], out / f"finmind_{dataset.lower()}_2330_sample.csv")
        except Exception as exc:  # noqa: BLE001
            probes.append({"dataset": dataset, "status": "ERR", "error": f"{type(exc).__name__}:{exc}"})
        time.sleep(0.2)
    status["finmind_tick_probe"] = {
        "status": "PASS" if any((p.get("rows") or 0) > 0 for p in probes) else "UNAVAILABLE_OR_MEMBER",
        "probes": probes,
        "limitation": "Tick usually Backer/Sponsor; free tier often blocked",
    }


def fetch_e6_board_announce_proxy(out: Path, status: dict) -> None:
    """Use FinMind dividend AnnouncementDate as conservative board/announce proxy + flag gap."""
    rows = []
    for code in ["2880", "2886", "2892", "5880", "2412", "3045", "4904", "0050"]:
        payload = finmind("TaiwanStockDividend", code, start="2010-01-01")
        for r in payload.get("data") or []:
            rows.append(
                {
                    "code": code,
                    "fiscal_year": r.get("year"),
                    "announcement_date": r.get("AnnouncementDate"),
                    "announcement_time": r.get("AnnouncementTime"),
                    "cash_ex_date": r.get("CashExDividendTradingDate"),
                    "cash_payment_date": r.get("CashDividendPaymentDate"),
                    "cash_dividend": r.get("CashEarningsDistribution"),
                    "source": "FinMind_TaiwanStockDividend",
                    "board_date_quality": "ANNOUNCEMENT_DATE_PROXY_NOT_FIRST_BOARD_PROPOSAL",
                }
            )
        time.sleep(0.12)
    n = save_csv(rows, out / "e6_announcement_date_proxy.csv")
    status["e6_announcement_proxy"] = {
        "status": "PASS" if n else "EMPTY",
        "rows": n,
        "path": str(out / "e6_announcement_date_proxy.csv"),
        "limitation": "AnnouncementDate ≠ guaranteed earliest board dividend-proposal date; E6 remains shadow until MOPS full-text board-date challenger",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--sleep", type=float, default=0.12)
    ap.add_argument("--start", default="2018-01-01")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    status: dict = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "advanced_research_optional_datasets",
        "modifies_frozen_ledgers": False,
    }

    print("TWSE company profile / industry snapshot ...", flush=True)
    fetch_twse_company_profile(out, status)

    print("TWSE MI_MARGN snapshot ...", flush=True)
    fetch_twse_margin_snapshot(out, status)

    print("FinMind TaiwanStockInfo ...", flush=True)
    fetch_finmind_info(out, status)

    print("FinMind margin purchase/short sale history ...", flush=True)
    fetch_finmind_per_code(
        out,
        status,
        dataset="TaiwanStockMarginPurchaseShortSale",
        key="margin_short",
        codes=UNIVERSE,
        start=args.start,
        sleep=args.sleep,
    )

    print("FinMind securities lending history ...", flush=True)
    fetch_finmind_per_code(
        out,
        status,
        dataset="TaiwanStockSecuritiesLending",
        key="securities_lending",
        codes=UNIVERSE,
        start=args.start,
        sleep=args.sleep,
    )

    print("FinMind institutional investors ...", flush=True)
    fetch_finmind_per_code(
        out,
        status,
        dataset="TaiwanStockInstitutionalInvestorsBuySell",
        key="institutional",
        codes=UNIVERSE,
        start=args.start,
        sleep=args.sleep,
    )

    print("FinMind TX futures OI ...", flush=True)
    fetch_futures_oi(out, status)

    print("Options probe ...", flush=True)
    fetch_options_probe(out, status)

    print("Tick probe ...", flush=True)
    fetch_tick_probe(out, status)

    print("E6 announcement proxy ...", flush=True)
    fetch_e6_board_announce_proxy(out, status)

    # summary README
    (out / "README.md").write_text(
        f"""# Advanced research data pack

Generated: `{status['generated_at_utc']}`

This folder holds **optional** datasets for Stage-7+ probes. It does **not** change E22_v2 / E21 ledgers.

## Fetched

See `fetch_status.json` for per-source PASS/FAIL and limitations.

## Still not free / not PIT-safe here

| Need | Gap |
|---|---|
| Historical industry reclassification | TWSE E-Shop **TWT58U** daily archive (paid) — snapshot only in this pack |
| Full option chains / ticks | Often FinMind member tier |
| True first board dividend proposal date | Needs MOPS full-text NLP challenger beyond AnnouncementDate proxy |

## Suggested next probes

1. TX open_interest timing overlay (data: `finmind_tx_futures_daily.csv`)
2. Margin/short + lending capacity book for G4 H2 paper (margin + lending CSVs)
3. Industry-neutral alpha only after TWT58U PIT lands
"""
    )

    (out / "fetch_status.json").write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: (v.get("status") if isinstance(v, dict) else v) for k, v in status.items()}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
