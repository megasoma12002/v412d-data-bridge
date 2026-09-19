#!/usr/bin/env python3
"""MOPS payment-date amendment overlay (D4 / Gap 6.9b + 6.9c stock observe).

Observe-only. Does **not** rewrite Soft-Frozen books or ``e22_dividend_events.csv``.
This CLI has no ``--write-ledger`` flag — overlay CSV updates are separate ops.

Sources:
  1. Ops overlay CSV (manual / typhoon 重大訊息)
  2. Fixture / announcement text parser (offline tests)
  3. Optional live t108sb27 vs ledger diff (scheduled pay ≠ FinMind)

Schema ``mops_payment_amendments.csv``:
  code,original_payment_date,amended_payment_date,source,note[,leg]
  ``leg`` optional: ``cash`` (default) | ``stock`` | ``both`` (Gap 6.9c).
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OVERLAY = ROOT / "data" / "dividend_events" / "mops_payment_amendments.csv"
DEFAULT_EVENTS = ROOT / "data" / "dividend_events" / "e22_dividend_events.csv"
MOPS_URL = "https://mopsov.twse.com.tw/mops/web/ajax_t108sb27"

# (code, original ISO pay[, leg]) → amended ISO pay
# Legacy 2-tuples are treated as cash/both for lookup compatibility.
AmendmentMap = dict[tuple[str, str] | tuple[str, str, str], str]

_AMEND_PATTERNS = (
    # 原訂…發放日…2026年7月10日…顺延…7月13日
    re.compile(
        r"原[訂定].{0,24}?(?:發放|給付|配發|股票股利|現金股利|除權|除息).{0,40}?"
        r"(?P<y1>\d{2,4})\s*年\s*(?P<m1>\d{1,2})\s*月\s*(?P<d1>\d{1,2})\s*日"
        r".{0,40}?(?:顺延|改為|變更為|延至|延期至).{0,40}?"
        r"(?:(?P<y2>\d{2,4})\s*年\s*)?(?P<m2>\d{1,2})\s*月\s*(?P<d2>\d{1,2})\s*日",
        re.DOTALL,
    ),
    # ISO-ish: 原發放日 2026-07-10 → 2026-07-13
    re.compile(
        r"原(?:訂)?(?:發放|給付|股票股利|現金股利)?日?\s*(?P<o>\d{4}-\d{2}-\d{2})"
        r".{0,20}?(?:→|->|顺延|改為|變更為|延至)\s*(?P<a>\d{4}-\d{2}-\d{2})",
        re.DOTALL,
    ),
)


def _infer_leg_from_text(text: str) -> str:
    t = text or ""
    has_stock = bool(re.search(r"股票股利|除權|配股|股票發放", t))
    has_cash = bool(re.search(r"現金股利|除息|現金發放|現金給付", t))
    if has_stock and not has_cash:
        return "stock"
    if has_cash and not has_stock:
        return "cash"
    if has_stock and has_cash:
        return "both"
    return "cash"


def _roc_year_to_ad(y: int) -> int:
    return y + 1911 if y < 1911 else y


def _ymd_to_iso(y: str, m: str, d: str) -> str:
    yi = _roc_year_to_ad(int(y))
    return f"{yi:04d}-{int(m):02d}-{int(d):02d}"


def parse_amendment_text(text: str, *, default_code: str = "") -> list[dict[str, str]]:
    """Extract original→amended payment pairs from announcement body."""
    out: list[dict[str, str]] = []
    leg = _infer_leg_from_text(text or "")
    for pat in _AMEND_PATTERNS:
        for m in pat.finditer(text or ""):
            gd = m.groupdict()
            if "o" in gd and gd.get("o"):
                orig, amd = gd["o"], gd["a"]
            else:
                y2 = gd.get("y2") or gd["y1"]
                orig = _ymd_to_iso(gd["y1"], gd["m1"], gd["d1"])
                amd = _ymd_to_iso(y2, gd["m2"], gd["d2"])
            if orig == amd:
                continue
            out.append(
                {
                    "code": default_code,
                    "original_payment_date": orig,
                    "amended_payment_date": amd,
                    "source": "announcement_text",
                    "note": "parsed",
                    "leg": leg,
                }
            )
    return out


def load_amendments(path: Path | None = None) -> AmendmentMap:
    path = path or DEFAULT_OVERLAY
    if not path.exists():
        return {}
    out: AmendmentMap = {}
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            code = str(row.get("code") or "").strip()
            orig = str(row.get("original_payment_date") or "").strip()[:10]
            amd = str(row.get("amended_payment_date") or "").strip()[:10]
            leg = str(row.get("leg") or "cash").strip().lower() or "cash"
            if code and orig and amd:
                out[(code, orig)] = amd  # legacy cash/both key
                out[(code, orig, leg)] = amd
                if leg == "both":
                    out[(code, orig, "cash")] = amd
                    out[(code, orig, "stock")] = amd
    return out


def save_amendments(rows: Iterable[Mapping[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "code",
        "original_payment_date",
        "amended_payment_date",
        "source",
        "note",
        "leg",
    ]
    rows_l = [dict(r) for r in rows]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows_l:
            w.writerow({k: r.get(k, "cash" if k == "leg" else "") for k in fields})


def lookup_amendment(
    amendments: AmendmentMap,
    code: str,
    original_payment_date: str,
    *,
    leg: str = "cash",
) -> date | None:
    code_s = str(code).strip()
    orig = str(original_payment_date).strip()[:10]
    raw = None
    for key in ((code_s, orig, leg), (code_s, orig, "both"), (code_s, orig)):
        if key in amendments:
            raw = amendments[key]
            break
    if not raw:
        return None
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return None


def merge_amendment_rows(*groups: Iterable[Mapping[str, str]]) -> list[dict[str, str]]:
    by_key: dict[tuple[str, str, str], dict[str, str]] = {}
    for group in groups:
        for r in group:
            code = str(r.get("code") or "").strip()
            orig = str(r.get("original_payment_date") or "").strip()[:10]
            amd = str(r.get("amended_payment_date") or "").strip()[:10]
            leg = str(r.get("leg") or "cash").strip().lower() or "cash"
            if not (code and orig and amd):
                continue
            by_key[(code, orig, leg)] = {
                "code": code,
                "original_payment_date": orig,
                "amended_payment_date": amd,
                "source": str(r.get("source") or ""),
                "note": str(r.get("note") or ""),
                "leg": leg,
            }
    return sorted(
        by_key.values(),
        key=lambda x: (x["code"], x["original_payment_date"], x["leg"]),
    )


def roc_to_iso(s: str) -> str:
    s = (s or "").strip()
    if not s:
        return ""
    parts = s.replace("-", "/").split("/")
    if len(parts) != 3:
        return ""
    y, m, d = (int(parts[0]), int(parts[1]), int(parts[2]))
    return f"{y + 1911:04d}-{m:02d}-{d:02d}"


def fetch_mops_t108_html(roc_year: int, *, retries: int = 3, timeout: float = 120.0) -> str:
    """Live t108sb27 fetch with retries (network harden)."""
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
    last_err: Exception | None = None
    for attempt in range(max(1, retries)):
        try:
            req = urllib.request.Request(
                MOPS_URL,
                data=body,
                headers={
                    "User-Agent": "v412-mops-payment-amendments/1.0",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Referer": "https://mopsov.twse.com.tw/mops/web/t108sb27",
                    "Accept": "text/html,application/xhtml+xml,*/*",
                },
            )
            with urllib.request.urlopen(req, timeout=timeout) as response:
                raw = response.read().decode("utf-8", errors="ignore")
            if not raw or len(raw) < 40:
                raise RuntimeError("MOPS empty/short response")
            return raw
        except (urllib.error.URLError, TimeoutError, RuntimeError) as exc:
            last_err = exc
            if attempt + 1 < retries:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(
        f"MOPS t108sb27 fetch failed after {retries} tries (roc_year={roc_year})"
    ) from last_err


def parse_mops_t108_payments(raw: str, *, codes: set[str] | None = None) -> list[dict[str, str]]:
    try:
        from bs4 import BeautifulSoup
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("BeautifulSoup required for MOPS HTML parse") from exc
    soup = BeautifulSoup(raw, "lxml")
    table = None
    for candidate in soup.find_all("table"):
        if "現金股利發放日" in candidate.get_text():
            table = candidate
            break
    if table is None:
        return []
    out: list[dict[str, str]] = []
    for row in table.find_all("tr"):
        cells = [c.get_text(" ", strip=True) for c in row.find_all(["td", "th"])]
        if not cells or len(cells) < 15:
            continue
        code = cells[0]
        if codes is not None and code not in codes:
            continue
        cash_pay = roc_to_iso(cells[14])
        cash_ex = roc_to_iso(cells[13])
        if not cash_pay:
            continue
        out.append(
            {
                "code": code,
                "cash_ex_date": cash_ex,
                "cash_payment_date": cash_pay,
            }
        )
    return out


def amendments_from_mops_vs_ledger(
    mops_rows: Iterable[Mapping[str, str]],
    ledger_rows: Iterable[Mapping[str, str]],
) -> list[dict[str, str]]:
    """When MOPS scheduled pay ≠ ledger pay for same code+ex, emit amendment."""
    led_by_ex: dict[tuple[str, str], str] = {}
    for r in ledger_rows:
        code = str(r.get("code") or "").strip()
        ex = str(r.get("cash_ex_date") or "").strip()[:10]
        pay = str(r.get("cash_payment_date") or "").strip()[:10]
        if code and ex and pay:
            led_by_ex[(code, ex)] = pay
    out: list[dict[str, str]] = []
    for r in mops_rows:
        code = str(r.get("code") or "").strip()
        ex = str(r.get("cash_ex_date") or "").strip()[:10]
        mops_pay = str(r.get("cash_payment_date") or "").strip()[:10]
        led_pay = led_by_ex.get((code, ex), "")
        if code and mops_pay and led_pay and mops_pay != led_pay:
            out.append(
                {
                    "code": code,
                    "original_payment_date": led_pay,
                    "amended_payment_date": mops_pay,
                    "source": "mops_t108sb27_vs_ledger",
                    "note": f"ex={ex}",
                    "leg": "cash",
                }
            )
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--overlay", type=Path, default=DEFAULT_OVERLAY)
    ap.add_argument("--events", type=Path, default=DEFAULT_EVENTS)
    ap.add_argument("--fixture-text", type=Path, default=None, help="Announcement text file")
    ap.add_argument("--fixture-code", default="")
    ap.add_argument("--from-mops-html", type=Path, default=None, help="Offline t108 HTML")
    ap.add_argument("--fetch-mops-year", type=int, default=0, help="ROC year live fetch")
    ap.add_argument("--merge-existing", action="store_true", default=True)
    ap.add_argument("--no-merge-existing", action="store_false", dest="merge_existing")
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()

    existing = []
    if a.merge_existing and a.overlay.exists():
        with a.overlay.open(encoding="utf-8") as f:
            existing = list(csv.DictReader(f))

    new_rows: list[dict[str, str]] = []
    if a.fixture_text and a.fixture_text.exists():
        text = a.fixture_text.read_text(encoding="utf-8")
        new_rows.extend(parse_amendment_text(text, default_code=a.fixture_code))

    mops_rows: list[dict[str, str]] = []
    if a.from_mops_html and a.from_mops_html.exists():
        codes = None
        if a.events.exists():
            with a.events.open(encoding="utf-8") as f:
                codes = {str(r.get("code") or "").strip() for r in csv.DictReader(f)}
        mops_rows = parse_mops_t108_payments(
            a.from_mops_html.read_text(encoding="utf-8"), codes=codes
        )
    elif a.fetch_mops_year > 0:
        html = fetch_mops_t108_html(a.fetch_mops_year)
        codes = None
        if a.events.exists():
            with a.events.open(encoding="utf-8") as f:
                codes = {str(r.get("code") or "").strip() for r in csv.DictReader(f)}
        mops_rows = parse_mops_t108_payments(html, codes=codes)

    if mops_rows and a.events.exists():
        with a.events.open(encoding="utf-8") as f:
            ledger = list(csv.DictReader(f))
        new_rows.extend(amendments_from_mops_vs_ledger(mops_rows, ledger))

    merged = merge_amendment_rows(existing, new_rows)
    out = a.out or a.overlay
    save_amendments(merged, out)
    summary: dict[str, Any] = {
        "n_amendments": len(merged),
        "out": str(out),
        "note": "observe overlay; Soft-Frozen ledger not rewritten",
        "sample": merged[:10],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
