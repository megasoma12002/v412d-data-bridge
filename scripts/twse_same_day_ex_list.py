#!/usr/bin/env python3
"""S3 — TWSE same-day / forecast ex-list overlay (observe-only).

Fetches:
  - TWT48U 除權除息預告表 (upcoming scheduled ex)
  - TWT49U 除權除息計算結果表 (actual traded ex window)

Compares TWSE ex dates to ``e22_dividend_events.csv`` ledger legs and emits
``ex_date_amendments.csv`` when TWSE ≠ ledger (e.g. typhoon postpone).

Does **not** rewrite Soft-Frozen books or the ledger CSV.
This CLI has no ``--write-ledger`` flag — overlay writes are separate ops.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVENTS = ROOT / "data" / "dividend_events" / "e22_dividend_events.csv"
DEFAULT_OVERLAY = ROOT / "data" / "dividend_events" / "ex_date_amendments.csv"
TWT48U_URL = "https://www.twse.com.tw/exchangeReport/TWT48U?response=json"
TWT49U_URL = "https://www.twse.com.tw/exchangeReport/TWT49U?response=json"
UA = {"User-Agent": "v412-twse-same-day-ex-list/1.0"}
TAIPEI = ZoneInfo("Asia/Taipei")

# (code, original_ex_iso, leg) -> amended_ex_iso
ExAmendmentMap = dict[tuple[str, str, str], str]

_ROC_DATE = re.compile(
    r"(?P<y>\d{2,4})\s*年\s*(?P<m>\d{1,2})\s*月\s*(?P<d>\d{1,2})\s*日"
)


def roc_date_to_iso(text: str) -> str:
    """Parse ``115年07月10日`` / ISO / YYYYMMDD detail field → ISO date."""
    s = (text or "").strip()
    if not s:
        return ""
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return s
    m = _ROC_DATE.search(s)
    if m:
        y = int(m.group("y"))
        if y < 1911:
            y += 1911
        return f"{y:04d}-{int(m.group('m')):02d}-{int(m.group('d')):02d}"
    # detail field often ``code,YYYYMMDD``
    if "," in s:
        tail = s.split(",")[-1].strip()
        if re.fullmatch(r"\d{8}", tail):
            return f"{tail[:4]}-{tail[4:6]}-{tail[6:8]}"
    if re.fullmatch(r"\d{8}", s):
        return f"{s[:4]}-{s[4:6]}-{s[6:8]}"
    return ""


def _http_get_json(url: str, *, timeout: float = 60.0, retries: int = 3) -> dict[str, Any]:
    last_err: Exception | None = None
    for attempt in range(max(1, retries)):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8", errors="ignore"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_err = exc
            if attempt + 1 < retries:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"TWSE fetch failed after {retries} tries: {url}") from last_err


def parse_twt48u_rows(payload: Mapping[str, Any]) -> list[dict[str, str]]:
    """Upcoming / scheduled ex rows from TWT48U JSON."""
    out: list[dict[str, str]] = []
    for row in payload.get("data") or []:
        if not row or len(row) < 4:
            continue
        code = str(row[1]).strip()
        ex = roc_date_to_iso(str(row[0]))
        if not code or not ex:
            # fall back to detail field ``code,YYYYMMDD``
            if len(row) > 8:
                detail = str(row[8])
                if "," in detail:
                    parts = detail.split(",", 1)
                    code = code or parts[0].strip()
                    ex = ex or roc_date_to_iso(parts[1])
        if not code or not ex:
            continue
        kind = str(row[3]).strip() if len(row) > 3 else ""
        out.append(
            {
                "code": code,
                "ex_date": ex,
                "ex_kind": kind,
                "source": "twt48u",
                "name": str(row[2]).strip() if len(row) > 2 else "",
            }
        )
    return out


def parse_twt49u_rows(payload: Mapping[str, Any]) -> list[dict[str, str]]:
    """Actual traded ex rows from TWT49U JSON (資料日期 = board ex day)."""
    out: list[dict[str, str]] = []
    for row in payload.get("data") or []:
        if not row or len(row) < 3:
            continue
        code = str(row[1]).strip()
        ex = roc_date_to_iso(str(row[0]))
        if not ex and len(row) > 11:
            ex = roc_date_to_iso(str(row[11]))
        if not code or not ex:
            continue
        kind = str(row[6]).strip() if len(row) > 6 else ""
        out.append(
            {
                "code": code,
                "ex_date": ex,
                "ex_kind": kind,
                "source": "twt49u",
                "name": str(row[2]).strip() if len(row) > 2 else "",
            }
        )
    return out


def fetch_twt48u(*, use_network: bool = True, payload: Mapping[str, Any] | None = None) -> list[dict[str, str]]:
    if payload is not None:
        return parse_twt48u_rows(payload)
    if not use_network:
        return []
    return parse_twt48u_rows(_http_get_json(TWT48U_URL))


def fetch_twt49u(
    start: date,
    end: date,
    *,
    use_network: bool = True,
    payload: Mapping[str, Any] | None = None,
) -> list[dict[str, str]]:
    if payload is not None:
        return parse_twt49u_rows(payload)
    if not use_network:
        return []
    url = (
        f"{TWT49U_URL}&startDate={start.strftime('%Y%m%d')}"
        f"&endDate={end.strftime('%Y%m%d')}"
    )
    return parse_twt49u_rows(_http_get_json(url))


def load_ex_amendments(path: Path | None = None) -> ExAmendmentMap:
    path = path or DEFAULT_OVERLAY
    if not path.exists():
        return {}
    out: ExAmendmentMap = {}
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            code = str(row.get("code") or "").strip()
            orig = str(row.get("original_ex_date") or "").strip()[:10]
            amd = str(row.get("amended_ex_date") or "").strip()[:10]
            leg = str(row.get("leg") or "both").strip().lower() or "both"
            if code and orig and amd:
                out[(code, orig, leg)] = amd
    return out


def lookup_ex_amendment(
    amendments: ExAmendmentMap,
    code: str,
    original_ex_date: str,
    *,
    leg: str = "cash",
) -> date | None:
    """Prefer leg-specific overlay, else ``both``."""
    code = str(code).strip()
    orig = str(original_ex_date).strip()[:10]
    for key_leg in (leg, "both"):
        raw = amendments.get((code, orig, key_leg))
        if raw:
            try:
                return date.fromisoformat(raw[:10])
            except ValueError:
                return None
    return None


def save_ex_amendments(rows: Iterable[Mapping[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "code",
        "original_ex_date",
        "amended_ex_date",
        "leg",
        "source",
        "note",
    ]
    rows_l = [dict(r) for r in rows]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows_l:
            w.writerow({k: r.get(k, "") for k in fields})


def merge_ex_amendment_rows(*groups: Iterable[Mapping[str, str]]) -> list[dict[str, str]]:
    by_key: dict[tuple[str, str, str], dict[str, str]] = {}
    for group in groups:
        for r in group:
            code = str(r.get("code") or "").strip()
            orig = str(r.get("original_ex_date") or "").strip()[:10]
            amd = str(r.get("amended_ex_date") or "").strip()[:10]
            leg = str(r.get("leg") or "both").strip().lower() or "both"
            if not (code and orig and amd):
                continue
            by_key[(code, orig, leg)] = {
                "code": code,
                "original_ex_date": orig,
                "amended_ex_date": amd,
                "leg": leg,
                "source": str(r.get("source") or ""),
                "note": str(r.get("note") or ""),
            }
    return sorted(
        by_key.values(),
        key=lambda x: (x["code"], x["original_ex_date"], x["leg"]),
    )


def _leg_from_ex_kind(ex_kind: str) -> str:
    k = (ex_kind or "").strip()
    if k in ("權", "除權"):
        return "stock"
    if k in ("息", "除息"):
        return "cash"
    if "權" in k and "息" in k:
        return "both"
    return "both"


def amendments_from_twse_vs_ledger(
    twse_rows: Iterable[Mapping[str, str]],
    ledger_rows: Iterable[Mapping[str, str]],
    *,
    match_window_days: int = 14,
) -> list[dict[str, str]]:
    """When TWSE shows an ex for a code near a ledger ex but dates differ → overlay.

    Matching: same code; TWSE ex within ``match_window_days`` after ledger ex
    (typical typhoon postpone). Prefer closest future TWSE date.
    """
    by_code: dict[str, list[dict[str, str]]] = {}
    for r in twse_rows:
        code = str(r.get("code") or "").strip()
        if code:
            by_code.setdefault(code, []).append(dict(r))

    out: list[dict[str, str]] = []
    for led in ledger_rows:
        code = str(led.get("code") or "").strip()
        if not code or code not in by_code:
            continue
        for leg, field in (("cash", "cash_ex_date"), ("stock", "stock_ex_date")):
            raw = str(led.get(field) or "").strip()[:10]
            if not raw:
                continue
            try:
                led_d = date.fromisoformat(raw)
            except ValueError:
                continue
            cands: list[tuple[int, dict[str, str]]] = []
            for tw in by_code[code]:
                tex = str(tw.get("ex_date") or "").strip()[:10]
                if not tex or tex == raw:
                    continue
                try:
                    tw_d = date.fromisoformat(tex)
                except ValueError:
                    continue
                delta = (tw_d - led_d).days
                if 0 < delta <= match_window_days:
                    # Prefer matching leg kind when TWSE labels 權/息
                    tw_leg = _leg_from_ex_kind(str(tw.get("ex_kind") or ""))
                    if tw_leg not in (leg, "both"):
                        continue
                    cands.append((delta, tw))
            if not cands:
                continue
            cands.sort(key=lambda x: x[0])
            best = cands[0][1]
            out.append(
                {
                    "code": code,
                    "original_ex_date": raw,
                    "amended_ex_date": str(best["ex_date"])[:10],
                    "leg": leg,
                    "source": str(best.get("source") or "twse_ex_list"),
                    "note": f"ledger_{field}_vs_twse;kind={best.get('ex_kind','')}",
                }
            )
    return out


def apply_ex_overlay_to_row(
    row: Mapping[str, Any],
    amendments: ExAmendmentMap,
) -> dict[str, Any]:
    """Return a shallow copy with cash/stock ex dates replaced when overlay hits."""
    out = dict(row)
    code = str(out.get("code") or "").strip()
    notes: list[str] = []
    for leg, field in (("cash", "cash_ex_date"), ("stock", "stock_ex_date")):
        raw = str(out.get(field) or "").strip()[:10]
        if not raw:
            continue
        amd = lookup_ex_amendment(amendments, code, raw, leg=leg)
        if amd is not None and amd.isoformat() != raw:
            out[field] = amd.isoformat()
            notes.append(f"{leg}_ex_date_amendment:{raw}->{amd.isoformat()}")
    if notes:
        prev = str(out.get("overlay_notes") or "")
        out["overlay_notes"] = ";".join(x for x in [prev, *notes] if x)
    return out


def run_refresh(
    *,
    events_path: Path,
    overlay_path: Path,
    start: date | None = None,
    end: date | None = None,
    use_network: bool = True,
    twt48_payload: Mapping[str, Any] | None = None,
    twt49_payload: Mapping[str, Any] | None = None,
    merge_existing: bool = True,
    codes: set[str] | None = None,
) -> dict[str, Any]:
    today = datetime.now(tz=TAIPEI).date()
    end = end or today
    start = start or (end - timedelta(days=21))

    ledger: list[dict[str, str]] = []
    if events_path.exists():
        with events_path.open(encoding="utf-8") as f:
            ledger = list(csv.DictReader(f))
    if codes is not None:
        ledger = [r for r in ledger if str(r.get("code") or "").strip() in codes]

    twse_rows: list[dict[str, str]] = []
    twse_rows.extend(fetch_twt48u(use_network=use_network, payload=twt48_payload))
    twse_rows.extend(
        fetch_twt49u(start, end, use_network=use_network, payload=twt49_payload)
    )
    if codes is not None:
        twse_rows = [r for r in twse_rows if r["code"] in codes]

    new_rows = amendments_from_twse_vs_ledger(twse_rows, ledger)
    existing: list[dict[str, str]] = []
    if merge_existing and overlay_path.exists():
        with overlay_path.open(encoding="utf-8") as f:
            existing = list(csv.DictReader(f))
    merged = merge_ex_amendment_rows(existing, new_rows)
    save_ex_amendments(merged, overlay_path)
    return {
        "n_twse_rows": len(twse_rows),
        "n_new_amendments": len(new_rows),
        "n_amendments": len(merged),
        "window": {"start": start.isoformat(), "end": end.isoformat()},
        "out": str(overlay_path),
        "note": "observe overlay; Soft-Frozen ledger not rewritten",
        "sample": merged[:15],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--events", type=Path, default=DEFAULT_EVENTS)
    ap.add_argument("--overlay", type=Path, default=DEFAULT_OVERLAY)
    ap.add_argument("--start", default=None, help="TWT49U start YYYY-MM-DD")
    ap.add_argument("--end", default=None, help="TWT49U end YYYY-MM-DD")
    ap.add_argument("--from-twt48-json", type=Path, default=None)
    ap.add_argument("--from-twt49-json", type=Path, default=None)
    ap.add_argument("--no-network", action="store_true")
    ap.add_argument("--merge-existing", action="store_true", default=True)
    ap.add_argument("--no-merge-existing", action="store_false", dest="merge_existing")
    ap.add_argument("--codes", default="", help="Comma-separated code filter")
    a = ap.parse_args()

    twt48 = (
        json.loads(a.from_twt48_json.read_text(encoding="utf-8"))
        if a.from_twt48_json and a.from_twt48_json.exists()
        else None
    )
    twt49 = (
        json.loads(a.from_twt49_json.read_text(encoding="utf-8"))
        if a.from_twt49_json and a.from_twt49_json.exists()
        else None
    )
    code_set = {c.strip() for c in a.codes.split(",") if c.strip()} or None
    summary = run_refresh(
        events_path=a.events,
        overlay_path=a.overlay,
        start=date.fromisoformat(a.start) if a.start else None,
        end=date.fromisoformat(a.end) if a.end else None,
        use_network=not a.no_network,
        twt48_payload=twt48,
        twt49_payload=twt49,
        merge_existing=a.merge_existing,
        codes=code_set,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
