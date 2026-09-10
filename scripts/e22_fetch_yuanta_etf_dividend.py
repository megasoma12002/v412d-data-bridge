#!/usr/bin/env python3
"""Fetch official Yuanta ETF dividend history (ex / pay / amount).

Reverse-engineered from yuantafunds.com Nuxt ``$getAPI``:

  GET https://api.yuantafunds.com/ectranslation/api/trans
    APIType=EC2API  AppName=FundWeb  Device=4  Platform=YUANTAFUND
    FuncId=FundDividend/History  FundId=<internal id>

``0050`` maps to ``FundId=1066`` (via ``FuncId=FundList`` / ``STK_CD``).

Fields returned (no announcement_date):
  SHARE_DATE, PAY_DATE, DIVIDEN_PER_UNIT, BASE_DATE_GEN, ESTIMATEDATE, ...

Usage:
  python3 scripts/e22_fetch_yuanta_etf_dividend.py --stk 0050
  python3 scripts/e22_fetch_yuanta_etf_dividend.py --stk 0050 --compare-ledger
"""
from __future__ import annotations

import argparse
import csv
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIV_PATH = ROOT / "data" / "dividend_events" / "e22_dividend_events.csv"
OUT_DIR = ROOT / "research" / "ops"

API_BASE = "https://api.yuantafunds.com/ectranslation/api/trans"
COMMON = {
    "APIType": "EC2API",
    "CompanyName": "YUANTAFUNDS",
    "PageName": "/myfund/dividend/history",
    "DeviceId": "5eb1f95a-1d9b-4d14-9d33-fc0c88208363",
    "AppName": "FundWeb",
    "Device": "4",
    "Platform": "YUANTAFUND",
}
UA = "Mozilla/5.0 (compatible; e22-yuanta-div-fetch/1.0)"


def _get(params: dict) -> dict:
    url = API_BASE + "?" + urllib.parse.urlencode({**COMMON, **params})
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "application/json",
            "Referer": "https://www.yuantafunds.com/myfund/dividend/history",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    if payload.get("ResultCode") != 0:
        raise RuntimeError(
            f"Yuanta API error FuncId={params.get('FuncId')}: "
            f"{payload.get('ResultCode')} {payload.get('ResultMsg')}"
        )
    return payload.get("Data")


def resolve_fund_id(stk_cd: str) -> tuple[str, dict]:
    data = _get({"FuncId": "FundList"})
    hits: list[dict] = []

    def walk(obj: object) -> None:
        if isinstance(obj, dict):
            if str(obj.get("STK_CD") or "") == stk_cd:
                hits.append(obj)
            for value in obj.values():
                walk(value)
        elif isinstance(obj, list):
            for value in obj:
                walk(value)

    walk(data)
    if not hits:
        raise RuntimeError(f"STK_CD={stk_cd} not found in FundList")
    row = hits[0]
    fund_id = str(row.get("FUND_ID") or "").strip()
    if not fund_id:
        raise RuntimeError(f"STK_CD={stk_cd} has empty FUND_ID")
    return fund_id, row


def fetch_dividend_history(fund_id: str) -> list[dict]:
    data = _get({"FuncId": "FundDividend/History", "FundId": fund_id})
    rows = data.get("Data") if isinstance(data, dict) else data
    if not isinstance(rows, list):
        raise RuntimeError(f"unexpected FundDividend/History payload: {type(data)}")
    return rows


def norm_date(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    text = text.replace("/", "-")
    if len(text) == 8 and text.isdigit():
        return f"{text[:4]}-{text[4:6]}-{text[6:8]}"
    return text[:10]


def to_ledger_row(raw: dict, stk_cd: str) -> dict:
    return {
        "code": stk_cd,
        "fund_id": str(raw.get("FUND_ID") or ""),
        "cash_ex_date": norm_date(raw.get("SHARE_DATE")),
        "cash_payment_date": norm_date(raw.get("PAY_DATE")),
        "cash_dividend": raw.get("DIVIDEN_PER_UNIT"),
        "base_date_gen": norm_date(raw.get("BASE_DATE_GEN")),
        "estimate_date": norm_date(raw.get("ESTIMATEDATE")),
        "cycle_type": raw.get("CYCLE_TYPE"),
        "yyyy": raw.get("YYYY"),
        # Official API has no announcement_date field.
        "announcement_date": "",
    }


def compare_ledger(stk_cd: str, yu_rows: list[dict]) -> dict:
    by_ex = {r["cash_ex_date"]: r for r in yu_rows if r["cash_ex_date"]}
    with DIV_PATH.open(encoding="utf-8") as handle:
        led = [r for r in csv.DictReader(handle) if r.get("code") == stk_cd]
    matched = pay_diff = amt_diff = 0
    missing_in_yu: list[str] = []
    for row in led:
        ex = (row.get("cash_ex_date") or "")[:10]
        hit = by_ex.get(ex)
        if not hit:
            missing_in_yu.append(ex)
            continue
        matched += 1
        if hit["cash_payment_date"] != (row.get("cash_payment_date") or "")[:10]:
            pay_diff += 1
        try:
            if abs(float(hit["cash_dividend"]) - float(row.get("cash_dividend") or 0)) > 1e-9:
                amt_diff += 1
        except ValueError:
            amt_diff += 1
    extra_yu = sorted(set(by_ex) - {(r.get("cash_ex_date") or "")[:10] for r in led})
    announce_blank = sum(1 for r in led if not (r.get("announcement_date") or "").strip())
    return {
        "ledger_rows": len(led),
        "yuanta_rows": len(yu_rows),
        "matched_ex": matched,
        "missing_in_yuanta": missing_in_yu,
        "extra_in_yuanta": extra_yu,
        "payment_date_diffs": pay_diff,
        "amount_diffs": amt_diff,
        "ledger_announcement_blank": announce_blank,
        "api_has_announcement_date": False,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stk", default="0050", help="TW ticker / STK_CD")
    ap.add_argument("--fund-id", default="", help="Skip FundList resolve")
    ap.add_argument("--compare-ledger", action="store_true")
    ap.add_argument(
        "--out",
        default="",
        help="JSON output path (default research/ops/yuanta_etf_div_<stk>.json)",
    )
    args = ap.parse_args()
    stk = args.stk.strip()

    meta = {"stk_cd": stk, "fetched_at": datetime.now(timezone.utc).isoformat()}
    if args.fund_id:
        fund_id = args.fund_id.strip()
        meta["fund_meta"] = {"FUND_ID": fund_id}
    else:
        fund_id, fund_meta = resolve_fund_id(stk)
        meta["fund_meta"] = {
            k: fund_meta.get(k)
            for k in ("FUND_ID", "STK_CD", "FUND_SH_NM", "ISINCODE", "FUND_TYPE")
        }
    meta["fund_id"] = fund_id

    raw = fetch_dividend_history(fund_id)
    rows = [to_ledger_row(r, stk) for r in raw]
    payload = {"meta": meta, "rows": rows, "raw_field_names": sorted(raw[0].keys()) if raw else []}
    if args.compare_ledger:
        payload["ledger_compare"] = compare_ledger(stk, rows)

    out = Path(args.out) if args.out else OUT_DIR / f"yuanta_etf_div_{stk}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out} rows={len(rows)} fund_id={fund_id}")
    if args.compare_ledger:
        print(json.dumps(payload["ledger_compare"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
