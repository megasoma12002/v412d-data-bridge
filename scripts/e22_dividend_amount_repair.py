#!/usr/bin/env python3
"""Repair unparseable cash/stock dividend amounts in the E22 events ledger.

When live/e21 loads ``data/dividend_events/e22_dividend_events.csv`` with
fail-closed amounts and finds non-empty cells that are not floats
(e.g. ``N/A``, ``abc``), this module:

1. Scans bad cells (code, field, ex_date, line)
2. Re-fetches amounts (FinMind → Yahoo TW → Yuanta ETF for ``0050``)
3. Patches **only** the bad amount cells
4. Atomically rewrites the CSV + writes ``research/ops/E22_DIVIDEND_AMOUNT_REPAIR.*``

Does **not** flip Soft-Frozen / Soft-assist / Sleeve-tilt / E45 / DEFAULT books.
Does **not** rewrite ``forward/e21`` applied dividend history.

Usage:
  python3 scripts/e22_dividend_amount_repair.py --dry-run
  python3 scripts/e22_dividend_amount_repair.py
  python3 scripts/e22_dividend_amount_repair.py --codes 2880,0050
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import tempfile
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
DIV_PATH_DEFAULT = ROOT / "data/dividend_events/e22_dividend_events.csv"
REPORT_DIR_DEFAULT = ROOT / "research/ops"

FINMIND = "https://api.finmindtrade.com/api/v4/data"
YUANTA_API = "https://api.yuantafunds.com/ectranslation/api/trans"
UA = "Mozilla/5.0 (compatible; e22-div-amount-repair/1.0)"
ETF_CODES = {"0050"}

FetchFn = Callable[[str], list[dict]]


@dataclass(frozen=True)
class BadCell:
    line: int
    code: str
    field: str
    ex_date: str
    raw: str


@dataclass(frozen=True)
class RepairHit:
    line: int
    code: str
    field: str
    ex_date: str
    old: str
    new: str
    source: str


@dataclass
class RepairReport:
    path: str
    scanned_at_utc: str
    dry_run: bool = False
    wrote_csv: bool = False
    bad_before: list[dict] = field(default_factory=list)
    repaired: list[dict] = field(default_factory=list)
    unresolved: list[dict] = field(default_factory=list)
    fetch_errors: list[dict] = field(default_factory=list)


def _parse_float(raw: object) -> float | None:
    if raw is None:
        return None
    text = str(raw).strip().replace(",", "")
    if text == "":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _http_json(url: str, *, timeout: int = 120) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def _http_text(url: str, *, timeout: int = 60) -> str:
    req = urllib.request.Request(
        url, headers={"User-Agent": UA, "Accept-Language": "zh-TW,zh;q=0.9"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def scan_bad_amount_cells(path: Path | str) -> list[BadCell]:
    path = Path(path)
    bad: list[BadCell] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for line_i, row in enumerate(csv.DictReader(handle), start=2):
            code = str(row.get("code") or "").strip()
            for field_name, ex_key in (
                ("cash_dividend", "cash_ex_date"),
                ("stock_dividend", "stock_ex_date"),
            ):
                raw = row.get(field_name)
                if raw is None or str(raw).strip() == "":
                    continue
                if _parse_float(raw) is None:
                    bad.append(
                        BadCell(
                            line=line_i,
                            code=code,
                            field=field_name,
                            ex_date=str(row.get(ex_key) or "").strip()[:10],
                            raw=str(raw),
                        )
                    )
    return bad


def fetch_finmind_dividend_rows(code: str, *, start: str = "2005-01-01") -> list[dict]:
    q = {
        "dataset": "TaiwanStockDividend",
        "data_id": code,
        "start_date": start,
        "end_date": date.today().isoformat(),
    }
    payload = _http_json(FINMIND + "?" + urllib.parse.urlencode(q))
    if int(payload.get("status") or 0) != 200:
        raise RuntimeError(f"FinMind TaiwanStockDividend {code}: {payload}")
    out: list[dict] = []
    for row in payload.get("data") or []:
        cash = 0.0
        stock = 0.0
        for key in ("CashEarningsDistribution", "CashStatutorySurplus"):
            if row.get(key) not in (None, ""):
                cash += float(row[key])
        for key in ("StockEarningsDistribution", "StockStatutorySurplus"):
            if row.get(key) not in (None, ""):
                stock += float(row[key])
        cash_ex = str(
            row.get("CashExDividendTradingDay")
            or row.get("CashExDividendTradingDate")
            or ""
        )[:10]
        stock_ex = str(
            row.get("StockExDividendTradingDay")
            or row.get("StockExDividendTradingDate")
            or ""
        )[:10]
        out.append(
            {
                "code": code,
                "cash_ex_date": cash_ex,
                "stock_ex_date": stock_ex,
                "cash_dividend": cash,
                "stock_dividend": stock,
                "source": "FinMind_TaiwanStockDividend",
            }
        )
    return out


def fetch_yahoo_tw_dividend_rows(code: str) -> list[dict]:
    from bs4 import BeautifulSoup

    html = _http_text(f"https://tw.stock.yahoo.com/quote/{code}.TW/dividend")
    text = BeautifulSoup(html, "lxml").get_text("\n", strip=True)
    idx = text.find("現金股利發放日")
    if idx < 0:
        idx = text.find("除息日")
    if idx < 0:
        return []
    start = text.find("填息天數", idx)
    if start < 0:
        start = idx
    body = text[start:].strip().split("\n")
    while body and not re.fullmatch(r"\d{4}", body[0] or ""):
        body = body[1:]
        if len(body) < 11:
            break

    def _iso(value: str) -> str:
        value = (value or "").strip().replace("-", "/")
        parts = value.split("/")
        if len(parts) != 3:
            return ""
        try:
            y, m, d = map(int, parts)
        except ValueError:
            return ""
        return f"{y:04d}-{m:02d}-{d:02d}"

    rows: list[dict] = []
    i = 0
    stop = {"相關新聞", "熱門股", "技術分析", "登入", "隱私"}
    while i + 10 < len(body):
        chunk = body[i : i + 11]
        if any(any(s in x for s in stop) for x in chunk):
            break
        if not re.fullmatch(r"\d{4}", chunk[0] or ""):
            i += 1
            continue
        cash_v = _parse_float(chunk[2])
        stock_v = _parse_float(chunk[3])
        rows.append(
            {
                "code": code,
                "cash_ex_date": _iso(chunk[6]),
                "stock_ex_date": _iso(chunk[7]),
                "cash_dividend": cash_v if cash_v is not None else "",
                "stock_dividend": stock_v if stock_v is not None else "",
                "source": "YahooTW_quote_dividend",
            }
        )
        i += 11
    return rows


def fetch_yuanta_etf_dividend_rows(code: str) -> list[dict]:
    common = {
        "APIType": "EC2API",
        "CompanyName": "YUANTAFUNDS",
        "PageName": "/myfund/dividend/history",
        "DeviceId": "e22-div-amount-repair",
        "AppName": "FundWeb",
        "Device": "4",
        "Platform": "YUANTAFUND",
    }

    def _get(params: dict) -> dict:
        return _http_json(YUANTA_API + "?" + urllib.parse.urlencode({**common, **params}))

    listing = _get({"FuncId": "FundList"})
    data = listing.get("Data") if isinstance(listing, dict) else listing
    fund_id = ""
    if isinstance(data, list):
        for row in data:
            if str(row.get("STK_CD") or "").strip() == code:
                fund_id = str(row.get("FUND_ID") or "").strip()
                break
    if not fund_id:
        raise RuntimeError(f"Yuanta FundId not found for STK_CD={code}")
    hist = _get({"FuncId": "FundDividend/History", "FundId": fund_id})
    rows = hist.get("Data") if isinstance(hist, dict) else hist
    if not isinstance(rows, list):
        raise RuntimeError(f"Yuanta history unexpected for {code}: {type(rows)}")
    out: list[dict] = []
    for raw in rows:
        ex = str(raw.get("SHARE_DATE") or "").replace("/", "-")
        if len(ex) == 8 and ex.isdigit():
            ex = f"{ex[:4]}-{ex[4:6]}-{ex[6:8]}"
        else:
            ex = ex[:10]
        amt = _parse_float(raw.get("DIVIDEN_PER_UNIT"))
        out.append(
            {
                "code": code,
                "cash_ex_date": ex,
                "stock_ex_date": "",
                "cash_dividend": amt if amt is not None else "",
                "stock_dividend": "",
                "source": "Yuanta_FundDividend_History",
            }
        )
    return out


def _lookup_amount(
    source_rows: list[dict],
    *,
    code: str,
    field: str,
    ex_date: str,
) -> tuple[float, str] | None:
    if not ex_date:
        return None
    ex_key = "cash_ex_date" if field == "cash_dividend" else "stock_ex_date"
    try:
        target = datetime.strptime(ex_date[:10], "%Y-%m-%d").date()
    except ValueError:
        return None
    candidates: list[tuple[int, float, str]] = []
    for row in source_rows:
        if str(row.get("code") or "") != code:
            continue
        raw_ex = str(row.get(ex_key) or "")[:10]
        if not raw_ex:
            continue
        try:
            src_d = datetime.strptime(raw_ex, "%Y-%m-%d").date()
        except ValueError:
            continue
        delta = abs((src_d - target).days)
        if delta > 1:
            continue
        amt = _parse_float(row.get(field))
        if amt is None:
            continue
        candidates.append((delta, float(amt), str(row.get("source") or "unknown")))
    if not candidates:
        return None
    candidates.sort(key=lambda x: (x[0], -abs(x[1])))
    _d, amt, source = candidates[0]
    return amt, source


def _write_report(report: RepairReport, report_dir: Path) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "E22_DIVIDEND_AMOUNT_REPAIR.json").write_text(
        json.dumps(asdict(report), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# E22 Dividend Amount Repair",
        "",
        f"Scanned: `{report.scanned_at_utc}`",
        f"Ledger: `{report.path}`",
        f"Dry-run: **{report.dry_run}** · Wrote CSV: **{report.wrote_csv}**",
        "",
        f"- Bad cells before: **{len(report.bad_before)}**",
        f"- Repaired: **{len(report.repaired)}**",
        f"- Unresolved: **{len(report.unresolved)}**",
        f"- Fetch errors: **{len(report.fetch_errors)}**",
        "",
        "## Repaired",
        "",
    ]
    if report.repaired:
        lines += [
            "| Line | Code | Field | Ex | Old | New | Source |",
            "|---:|---|---|---|---|---|---|",
        ]
        for h in report.repaired:
            lines.append(
                f"| {h['line']} | `{h['code']}` | `{h['field']}` | {h['ex_date']} | "
                f"`{h['old']}` | `{h['new']}` | {h['source']} |"
            )
    else:
        lines.append("_none_")
    lines += ["", "## Unresolved", ""]
    if report.unresolved:
        for u in report.unresolved:
            lines.append(
                f"- line {u['line']} `{u['code']}` `{u['field']}` "
                f"ex={u['ex_date']} raw=`{u['raw']}`"
            )
    else:
        lines.append("_none_")
    (report_dir / "E22_DIVIDEND_AMOUNT_REPAIR.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def repair_dividend_amount_ledger(
    path: Path | str = DIV_PATH_DEFAULT,
    *,
    dry_run: bool = False,
    network: bool = True,
    codes: set[str] | None = None,
    fetchers: dict[str, FetchFn] | None = None,
    report_dir: Path | str = REPORT_DIR_DEFAULT,
) -> RepairReport:
    path = Path(path)
    report = RepairReport(
        path=str(path),
        scanned_at_utc=datetime.now(timezone.utc).isoformat(),
        dry_run=dry_run,
    )
    bad = scan_bad_amount_cells(path)
    if codes:
        bad = [b for b in bad if b.code in codes]
    report.bad_before = [asdict(b) for b in bad]
    if not bad:
        _write_report(report, Path(report_dir))
        return report

    cache: dict[str, list[dict]] = {}
    for code in sorted({b.code for b in bad}):
        rows: list[dict] = []
        chain: list[tuple[str, FetchFn]] = []
        if fetchers is not None:
            chain = list(fetchers.items())
        else:
            if code in ETF_CODES:
                chain.append(("yuanta", fetch_yuanta_etf_dividend_rows))
            chain.append(("finmind", fetch_finmind_dividend_rows))
            chain.append(("yahoo", fetch_yahoo_tw_dividend_rows))
        for name, fn in chain:
            if not network and fetchers is None:
                continue
            try:
                rows.extend(fn(code))
            except Exception as exc:  # noqa: BLE001
                report.fetch_errors.append(
                    {"code": code, "source": name, "error": str(exc)}
                )
        cache[code] = rows

    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = list(reader.fieldnames or [])
        table = list(reader)

    hits: list[RepairHit] = []
    unresolved: list[BadCell] = []
    for cell in bad:
        idx = cell.line - 2
        if idx < 0 or idx >= len(table):
            unresolved.append(cell)
            continue
        found = _lookup_amount(
            cache.get(cell.code) or [],
            code=cell.code,
            field=cell.field,
            ex_date=cell.ex_date,
        )
        if found is None:
            unresolved.append(cell)
            continue
        new_amt, source = found
        new_s = f"{new_amt:.10g}"
        hits.append(
            RepairHit(
                line=cell.line,
                code=cell.code,
                field=cell.field,
                ex_date=cell.ex_date,
                old=cell.raw,
                new=new_s,
                source=source,
            )
        )
        if not dry_run:
            table[idx][cell.field] = new_s

    report.repaired = [asdict(h) for h in hits]
    report.unresolved = [asdict(u) for u in unresolved]

    if not dry_run and hits:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w",
            newline="",
            encoding="utf-8",
            delete=False,
            dir=str(path.parent),
            prefix=path.name + ".",
            suffix=".tmp",
        ) as tmp:
            writer = csv.DictWriter(tmp, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(table)
            tmp_name = tmp.name
        Path(tmp_name).replace(path)
        report.wrote_csv = True

    _write_report(report, Path(report_dir))
    return report


def load_dividend_events_with_repair(
    path: Path | str,
    *,
    require_exists: bool = True,
    network: bool = True,
    load_fn=None,
):
    """Repair once on bad amounts, then fail-closed load (live helper)."""
    path = Path(path)
    if load_fn is None:
        from e22_dividend_accounting import load_dividend_events as load_fn

    if path.exists() and scan_bad_amount_cells(path):
        report = repair_dividend_amount_ledger(path, dry_run=False, network=network)
        if report.unresolved:
            detail = ", ".join(
                f"{u['code']}:{u['field']}@{u['ex_date']}={u['raw']!r}"
                for u in report.unresolved[:8]
            )
            raise ValueError(
                f"dividend amount repair left {len(report.unresolved)} "
                f"unresolved cell(s): {detail}"
            )
    return load_fn(path, require_exists=require_exists, fail_closed_amounts=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--path", type=Path, default=DIV_PATH_DEFAULT)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-network", action="store_true")
    ap.add_argument("--codes", default="", help="Comma-separated code filter")
    ap.add_argument("--report-dir", type=Path, default=REPORT_DIR_DEFAULT)
    args = ap.parse_args()
    codes = {c.strip() for c in args.codes.split(",") if c.strip()} or None
    report = repair_dividend_amount_ledger(
        args.path,
        dry_run=args.dry_run,
        network=not args.no_network,
        codes=codes,
        report_dir=args.report_dir,
    )
    print(
        json.dumps(
            {
                "bad_before": len(report.bad_before),
                "repaired": len(report.repaired),
                "unresolved": len(report.unresolved),
                "wrote_csv": report.wrote_csv,
                "fetch_errors": len(report.fetch_errors),
            },
            indent=2,
        )
    )
    return 1 if report.unresolved else 0


if __name__ == "__main__":
    raise SystemExit(main())
