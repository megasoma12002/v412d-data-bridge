#!/usr/bin/env python3
"""TWSE session calendar — annual holidaySchedule + typhoon overlays.

Integrates:
  1) TWSE ``holidaySchedule`` year calendar (国定假 / 無交易日 / 開始交易標記)
  2) NCDR DGPA CAP typhoon **intent** (臺北市 full/AM)
  3) TWSE MIS delayed quote **intraday OPEN** (pre-MI_INDEX positive signal)
  4) MI_INDEX **fact** (post-close)
  5) Optional TAIFEX TX day-session **historical fact** (``futDataDown``)
  6) Optional ``session_overrides.csv``

TAIFEX OpenAPI ``DailyMarketReportFut`` / ``TimeAndSalesData`` are **latest
published day only** and lag like MI_INDEX during the cash morning — they do
**not** give an 08:45 early-open detector. Use MIS for intraday OPEN, CAP for
morning typhoon intent; use ``futDataDown`` TX ``一般`` for backfill.

Output SSOT shape: ``data/calendars/twse_sessions_YYYY.csv``
Soft-Frozen / LIVE_* unchanged. Observe / preflight only.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable, Sequence
from zoneinfo import ZoneInfo

TAIPEI = ZoneInfo("Asia/Taipei")
UA = {"User-Agent": "e21-ops-twse-session/1.0"}
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CALENDAR_DIR = ROOT / "data" / "calendars"

HOLIDAY_URL = "https://www.twse.com.tw/holidaySchedule/holidaySchedule?response=json"
MI_INDEX_URL = (
    "https://www.twse.com.tw/exchangeReport/MI_INDEX"
    "?response=json&date={yyyymmdd}&type=ALLBUT0999"
)
NCDR_ATOM_URL = "https://alerts.ncdr.nat.gov.tw/RssAtomFeed.ashx?AlertType=33"
ATOM_NS = {"a": "http://www.w3.org/2005/Atom"}

# TWSE MIS delayed quote — fills the intraday OPEN gap before MI_INDEX publishes.
MIS_STOCK_INFO_URL = (
    "https://mis.twse.com.tw/stock/api/getStockInfo.jsp"
    "?ex_ch={ex_ch}&json=1&delay=0&_{ts}"
)
# Align with forward universe anchors (TAIEX + 0050); 2330 is liquid corroboration.
MIS_OPEN_WATCHLIST = ("tse_t00.tw", "tse_0050.tw", "tse_2330.tw")
# Regular board opens 09:00; before ~09:05 empty open is expected on open days.
MIS_OPEN_READY = (9, 5)

TAIFEX_FUT_DATA_DOWN_URL = "https://www.taifex.com.tw/cht/3/futDataDown"
TAIFEX_OPENAPI_DAILY_FUT = "https://openapi.taifex.com.tw/v1/DailyMarketReportFut"
# Official TX day board close (Taipei); used as intraday report-lag cutoff.
# Day open is 08:45 — free daily APIs do not publish that early (see charter §4.2).
TAIFEX_TX_DAY_CLOSE = (13, 45)

_CLOSED_NAME_HINTS = (
    "放假",
    "休市",
    "無交易",
    "补假",
    "補假",
    "春節",
    "除夕",
    "紀念日",
    "勞動節",
    "端午節",
    "中秋",
    "國慶",
    "兒童節",
    "掃墓",
    "開國",
    "行憲",
    "光復",
    "和平",
    "孔子",
    "教師節",
)
_OPEN_NAME_HINTS = ("開始交易", "最後交易日")


@dataclass
class CapWorkStop:
    area: str
    sent: str
    effective: str
    expires: str
    headline: str
    description: str
    status: str
    msg_type: str
    href: str
    target_date: date | None
    class_: str
    is_taipei: bool


@dataclass
class DayRecord:
    """One row of the integrated annual session calendar."""

    date: date
    is_session: bool
    kind: str
    name: str = ""
    source: str = "planned"
    notes: str = ""

    def to_row(self) -> dict[str, str]:
        return {
            "date": self.date.isoformat(),
            "is_session": "1" if self.is_session else "0",
            "kind": self.kind,
            "name": self.name,
            "source": self.source,
            "notes": self.notes,
        }


@dataclass
class SessionProbe:
    asof: str
    weekday: int
    status: str
    broker_submit_allowed: bool
    is_session: bool
    sources: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


def _http_get(url: str, timeout: float = 60.0) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def fetch_holiday_schedule(*, year: int | None = None) -> dict[str, Any]:
    raw = json.loads(_http_get(HOLIDAY_URL).decode("utf-8"))
    _ = year  # API publishes one year blob; filter happens in build_annual_calendar
    return raw


def _schedule_index(schedule: dict[str, Any]) -> dict[str, tuple[str, str]]:
    """date ISO -> (name, note)."""
    out: dict[str, tuple[str, str]] = {}
    for row in schedule.get("data") or []:
        if not row or len(row) < 2:
            continue
        d_s, name = str(row[0]), str(row[1])
        note = str(row[2]) if len(row) > 2 else ""
        out[d_s] = (name, note)
    return out


def holiday_status_for(day: date, schedule: dict[str, Any] | None = None) -> str | None:
    sched = schedule if schedule is not None else fetch_holiday_schedule()
    idx = _schedule_index(sched)
    hit = idx.get(day.isoformat())
    if hit is None:
        return None
    name, _note = hit
    if any(h in name for h in _OPEN_NAME_HINTS):
        return "OPEN_MARKER"
    if any(h in name for h in _CLOSED_NAME_HINTS) or "市場無交易" in name:
        return "CLOSED_HOLIDAY"
    return "CLOSED_HOLIDAY"


def build_annual_calendar(
    year: int,
    schedule: dict[str, Any] | None = None,
) -> list[DayRecord]:
    """Build Mon–Sun year grid from TWSE holidaySchedule (no typhoon yet)."""
    sched = schedule if schedule is not None else fetch_holiday_schedule()
    idx = _schedule_index(sched)
    start = date(year, 1, 1)
    end = date(year, 12, 31)
    days: list[DayRecord] = []
    d = start
    while d <= end:
        name, note = idx.get(d.isoformat(), ("", ""))
        hstat = holiday_status_for(d, sched)
        if hstat == "CLOSED_HOLIDAY":
            kind = "CLOSED_HOLIDAY"
            is_sess = False
            source = "holidaySchedule"
            # weekend+holiday still closed for board
            if d.weekday() >= 5:
                notes = "weekend+holidaySchedule"
            else:
                notes = note
        elif hstat == "OPEN_MARKER":
            kind = "SESSION"
            is_sess = True
            source = "holidaySchedule"
            notes = note or name
        elif d.weekday() >= 5:
            kind = "WEEKEND"
            is_sess = False
            source = "weekend"
            notes = ""
        else:
            kind = "SESSION"
            is_sess = True
            source = "weekday_default"
            notes = ""
        days.append(
            DayRecord(
                date=d,
                is_session=is_sess,
                kind=kind,
                name=name,
                source=source,
                notes=notes,
            )
        )
        d += timedelta(days=1)
    return days


def load_overrides(path: Path) -> dict[date, tuple[str, str]]:
    """CSV: date,status,reason  status in {OPEN,CLOSED,...}."""
    if not path.exists():
        return {}
    out: dict[date, tuple[str, str]] = {}
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            d = date.fromisoformat(str(row["date"]))
            out[d] = (str(row.get("status") or "").upper(), str(row.get("reason") or ""))
    return out


def apply_overlays(
    calendar: list[DayRecord],
    *,
    caps: Sequence[CapWorkStop] | None = None,
    mi_closed: Iterable[date] | None = None,
    mi_open: Iterable[date] | None = None,
    taifex_closed: Iterable[date] | None = None,
    taifex_open: Iterable[date] | None = None,
    overrides: dict[date, tuple[str, str]] | None = None,
) -> list[DayRecord]:
    """Overlay typhoon intent/fact + manual overrides onto the annual plan."""
    by_date = {r.date: DayRecord(**{**asdict(r), "date": r.date}) for r in calendar}
    # deepcopy-ish via asdict
    for r in calendar:
        by_date[r.date] = DayRecord(
            date=r.date,
            is_session=r.is_session,
            kind=r.kind,
            name=r.name,
            source=r.source,
            notes=r.notes,
        )

    if caps:
        for c in caps:
            if not (c.is_taipei and c.status == "Actual" and c.target_date):
                continue
            if c.class_ not in ("FULL_DAY", "MORNING"):
                continue
            td = c.target_date
            if td not in by_date:
                continue
            rec = by_date[td]
            if rec.kind == "CLOSED_HOLIDAY":
                continue  # annual holiday already closed
            rec.is_session = False
            rec.kind = "CLOSED_TYPHOON_INTENT"
            rec.source = "dgpa_cap+annual"
            rec.notes = (rec.notes + ";" if rec.notes else "") + c.description[:80]

    for d in mi_closed or ():
        if d not in by_date:
            continue
        rec = by_date[d]
        if rec.kind in ("CLOSED_HOLIDAY", "WEEKEND"):
            continue
        # Only demote planned sessions
        if rec.is_session or rec.kind.startswith("SESSION") or rec.kind == "CLOSED_TYPHOON_INTENT":
            if rec.kind != "CLOSED_TYPHOON_INTENT":
                rec.kind = "CLOSED_TYPHOON_OR_NODATA"
            rec.is_session = False
            rec.source = (rec.source + "+mi_index").replace("++", "+")
            rec.notes = (rec.notes + ";" if rec.notes else "") + "mi_index_empty"

    for d in mi_open or ():
        if d not in by_date:
            continue
        rec = by_date[d]
        if rec.kind in ("CLOSED_HOLIDAY", "WEEKEND"):
            continue
        rec.is_session = True
        rec.kind = "SESSION"
        rec.source = (rec.source + "+mi_index_ok").replace("++", "+")

    for d in taifex_closed or ():
        if d not in by_date:
            continue
        rec = by_date[d]
        if rec.kind in ("CLOSED_HOLIDAY", "WEEKEND"):
            continue
        if rec.is_session or rec.kind.startswith("SESSION") or rec.kind == "CLOSED_TYPHOON_INTENT":
            if rec.kind != "CLOSED_TYPHOON_INTENT":
                rec.kind = "CLOSED_TYPHOON_OR_NODATA"
            rec.is_session = False
            rec.source = (rec.source + "+taifex_tx").replace("++", "+")
            rec.notes = (rec.notes + ";" if rec.notes else "") + "taifex_tx_day_absent"

    for d in taifex_open or ():
        if d not in by_date:
            continue
        rec = by_date[d]
        if rec.kind in ("CLOSED_HOLIDAY", "WEEKEND"):
            continue
        rec.is_session = True
        rec.kind = "SESSION"
        rec.source = (rec.source + "+taifex_tx_ok").replace("++", "+")
        rec.notes = (rec.notes + ";" if rec.notes else "") + "taifex_tx_day_present"

    for d, (status, reason) in (overrides or {}).items():
        if d not in by_date:
            continue
        rec = by_date[d]
        if status == "CLOSED":
            rec.is_session = False
            rec.kind = "CLOSED_OVERRIDE"
            rec.source = "override"
            rec.notes = reason
        elif status == "OPEN":
            rec.is_session = True
            rec.kind = "SESSION"
            rec.source = "override"
            rec.notes = reason

    return [by_date[k] for k in sorted(by_date)]


def session_dates(calendar: Sequence[DayRecord]) -> list[date]:
    return [r.date for r in calendar if r.is_session]


def nth_session_after(sessions: Sequence[date], start: date, n: int) -> date:
    """Return the n-th open session strictly after ``start`` (n>=1)."""
    if n < 1:
        raise ValueError("n must be >= 1")
    after = [d for d in sessions if d > start]
    if len(after) < n:
        raise ValueError(f"not enough sessions after {start}: need {n}, have {len(after)}")
    return after[n - 1]


def write_calendar_csv(calendar: Sequence[DayRecord], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["date", "is_session", "kind", "name", "source", "notes"]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in calendar:
            w.writerow(r.to_row())


def read_calendar_csv(path: Path) -> list[DayRecord]:
    rows: list[DayRecord] = []
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(
                DayRecord(
                    date=date.fromisoformat(row["date"]),
                    is_session=str(row.get("is_session")) in ("1", "true", "True"),
                    kind=str(row.get("kind") or ""),
                    name=str(row.get("name") or ""),
                    source=str(row.get("source") or ""),
                    notes=str(row.get("notes") or ""),
                )
            )
    return rows


def lookup_day(calendar: Sequence[DayRecord], day: date) -> DayRecord | None:
    for r in calendar:
        if r.date == day:
            return r
    return None


# --- CAP / MI_INDEX / TAIFEX (overlays) -----------------------------------------------


def fetch_mi_index(day: date) -> dict[str, Any]:
    url = MI_INDEX_URL.format(yyyymmdd=day.strftime("%Y%m%d"))
    return json.loads(_http_get(url).decode("utf-8"))


def mi_index_has_session(day: date, payload: dict[str, Any] | None = None) -> bool:
    obj = payload if payload is not None else fetch_mi_index(day)
    if obj.get("stat") != "OK":
        return False
    tables = obj.get("tables")
    return isinstance(tables, list) and len(tables) > 0


def _mis_is_numeric(value: Any) -> bool:
    s = str(value).strip() if value is not None else ""
    if s in ("", "-", "--"):
        return False
    try:
        float(s.replace(",", ""))
        return True
    except ValueError:
        return False


def fetch_mis_stock_info(ex_ch: str) -> dict[str, Any]:
    """One TWSE MIS quote row wrapper. Rate-limit externally (~1 req / few seconds)."""
    url = MIS_STOCK_INFO_URL.format(
        ex_ch=urllib.parse.quote(ex_ch, safe="|_."),
        ts=int(datetime.now(tz=TAIPEI).timestamp() * 1000),
    )
    req = urllib.request.Request(
        url,
        headers={**UA, "Referer": "https://mis.twse.com.tw/", "Accept": "*/*"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def mis_row_open_on(day: date, row: dict[str, Any] | None) -> bool:
    """True when MIS row is dated ``day`` and has a numeric open (``o``)."""
    if not row:
        return False
    d_raw = str(row.get("d") or "").strip()
    want = day.strftime("%Y%m%d")
    return d_raw == want and _mis_is_numeric(row.get("o"))


def probe_mis_intraday_open(
    day: date,
    *,
    watchlist: Sequence[str] = MIS_OPEN_WATCHLIST,
    payloads: Sequence[dict[str, Any]] | None = None,
    sleep_s: float = 1.2,
) -> dict[str, Any]:
    """Positive same-day OPEN via MIS delayed quotes (pre-MI_INDEX).

    Closed / holiday / typhoon: feed typically keeps prior session ``d`` → not OPEN.
    Empty ``msgArray`` / rate-limit → inconclusive (UNKNOWN), not CLOSED.
    """
    wl = list(watchlist)
    if payloads is not None:
        sources = list(payloads)
        # Pad/trim labels to match payload count
        while len(wl) < len(sources):
            wl.append("")
        wl = wl[: len(sources)]
    else:
        sources = []
        for i, ex in enumerate(wl):
            if i:
                time.sleep(sleep_s)
            try:
                sources.append(fetch_mis_stock_info(ex))
            except Exception as exc:  # noqa: BLE001 — probe must stay fail-closed
                sources.append({"rtcode": "ERR", "rtmessage": str(exc), "msgArray": []})

    rows: list[dict[str, Any]] = []
    hits = 0
    for payload, ex in zip(sources, wl):
        arr = payload.get("msgArray") if isinstance(payload, dict) else None
        row = (arr or [None])[0] if isinstance(arr, list) else None
        ok = mis_row_open_on(day, row)
        if ok:
            hits += 1
        rows.append(
            {
                "ex_ch": ex or (row or {}).get("ch"),
                "open_signal": ok,
                "c": (row or {}).get("c"),
                "d": (row or {}).get("d"),
                "o": (row or {}).get("o"),
                "t": (row or {}).get("t"),
                "v": (row or {}).get("v"),
                "rtcode": payload.get("rtcode") if isinstance(payload, dict) else None,
            }
        )
    return {
        "open": hits > 0,
        "n_hits": hits,
        "n_probed": len(rows),
        "rows": rows,
    }


def _decode_taifex_bytes(raw: bytes) -> str:
    for enc in ("cp950", "big5", "utf-8-sig", "utf-8"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin1")


def fetch_taifex_fut_data_down(
    start: date,
    end: date,
    *,
    commodity_id: str = "TX",
) -> str:
    """POST legacy TAIFEX daily CSV download (≤ ~30 calendar days per call)."""
    if end < start:
        raise ValueError("end before start")
    if (end - start).days > 31:
        raise ValueError("TAIFEX futDataDown span must be ≤ 31 days; chunk externally")
    form = {
        "down_type": "1",
        "commodity_id": commodity_id,
        "commodity_id2": "",
        "queryStartDate": start.strftime("%Y/%m/%d"),
        "queryEndDate": end.strftime("%Y/%m/%d"),
    }
    body = urllib.parse.urlencode(form).encode("utf-8")
    req = urllib.request.Request(
        TAIFEX_FUT_DATA_DOWN_URL,
        data=body,
        headers={
            **UA,
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": "https://www.taifex.com.tw/cht/3/futDailyMarketView",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return _decode_taifex_bytes(resp.read())


def parse_taifex_tx_day_session_dates(csv_text: str) -> set[date]:
    """Dates with TX regular (一般) day-session rows — cash-board proxy for backfill."""
    out: set[date] = set()
    reader = csv.reader(io.StringIO(csv_text))
    try:
        header = next(reader)
    except StopIteration:
        return out
    try:
        di = header.index("交易日期")
        ci = header.index("契約")
        si = header.index("交易時段")
    except ValueError:
        return out
    for row in reader:
        if len(row) <= max(di, ci, si):
            continue
        if row[ci].strip() != "TX":
            continue
        if row[si].strip() != "一般":
            continue
        raw_d = row[di].strip().replace("-", "/")
        try:
            y, m, d = (int(x) for x in raw_d.split("/"))
            out.add(date(y, m, d))
        except ValueError:
            continue
    return out


def fetch_taifex_tx_day_sessions(start: date, end: date) -> set[date]:
    """Chunked futDataDown → set of dates with TX 一般 session."""
    if end < start:
        return set()
    out: set[date] = set()
    cur = start
    while cur <= end:
        chunk_end = min(cur + timedelta(days=30), end)
        text = fetch_taifex_fut_data_down(cur, chunk_end)
        out |= parse_taifex_tx_day_session_dates(text)
        cur = chunk_end + timedelta(days=1)
    return out


def fetch_taifex_openapi_daily_fut() -> list[dict[str, Any]]:
    """Latest published day only — no historical date filter."""
    return json.loads(_http_get(TAIFEX_OPENAPI_DAILY_FUT).decode("utf-8"))


def taifex_openapi_tx_day_date(payload: list[dict[str, Any]] | None = None) -> date | None:
    rows = payload if payload is not None else fetch_taifex_openapi_daily_fut()
    dates: set[date] = set()
    for row in rows:
        if row.get("Contract") != "TX" or row.get("TradingSession") != "一般":
            continue
        raw = str(row.get("Date") or "")
        if len(raw) == 8 and raw.isdigit():
            dates.add(date(int(raw[:4]), int(raw[4:6]), int(raw[6:8])))
    if not dates:
        return None
    return max(dates)


def classify_taifex_day_fact(
    day: date,
    *,
    history_open_days: set[date] | None = None,
    openapi_payload: list[dict[str, Any]] | None = None,
    now_taipei: datetime | None = None,
) -> str:
    """Return OPEN / CLOSED / UNKNOWN for TX day board vs cash session day.

    UNKNOWN covers: intraday before reports publish; OpenAPI still on prior day.
    """
    now = (now_taipei or datetime.now(tz=TAIPEI)).astimezone(TAIPEI)
    if history_open_days is not None:
        # Intraday today: absence in history download is inconclusive (report lag).
        if day == now.date() and (now.hour, now.minute) < TAIFEX_TX_DAY_CLOSE:
            if day in history_open_days:
                return "OPEN"
            return "UNKNOWN"
        return "OPEN" if day in history_open_days else "CLOSED"

    published = taifex_openapi_tx_day_date(openapi_payload)
    if published is None:
        return "UNKNOWN"
    if published == day:
        return "OPEN"
    # Published day behind asof → inconclusive until report rolls (same class as empty MI).
    return "UNKNOWN"


def _cap_text(root: ET.Element, tag: str) -> str:
    for el in root.iter():
        if el.tag.split("}")[-1] == tag and el.text:
            return el.text.strip()
    return ""


def _parse_target_date(desc: str, sent: datetime) -> date | None:
    sent_d = sent.astimezone(TAIPEI).date()
    if re.search(r"今天|今日", desc):
        return sent_d
    if re.search(r"明天|明日", desc):
        return sent_d + timedelta(days=1)
    m = re.search(r"(?<!\d)(\d{1,2})/(\d{1,2})(?!\d)", desc)
    if m:
        mm, dd = int(m.group(1)), int(m.group(2))
        try:
            return date(sent_d.year, mm, dd)
        except ValueError:
            return None
    return None


def _classify_work_stop(text: str) -> str:
    if re.search(r"未達停止上班.*停止上課|照常上班.*停止上課", text):
        if "未達停止上班" in text:
            return "SCHOOL_ONLY"
    if re.search(r"下午.*停止上班|停止上班.*下午|下午已達停止上班", text):
        return "AFTERNOON"
    if re.search(r"上午.*停止上班|停止上班.*上午|上午已達停止上班", text):
        return "MORNING"
    if re.search(r"停止上班", text):
        return "FULL_DAY"
    return "UNKNOWN"


def _is_taipei(area: str, desc: str) -> bool:
    blob = f"{area} {desc}"
    if area.strip() in ("臺北市", "台北市"):
        return True
    if re.search(r"臺北市.+區|台北市.+區", area) and "全體" not in blob:
        return False
    if re.search(r"臺北市|台北市", blob) and not re.search(r"臺北市.+區|台北市.+區", area):
        return True
    return False


def fetch_dgpa_caps(*, atom_url: str = NCDR_ATOM_URL) -> list[CapWorkStop]:
    raw = _http_get(atom_url)
    feed = ET.fromstring(raw)
    out: list[CapWorkStop] = []
    for entry in feed.findall("a:entry", ATOM_NS):
        link = entry.find("a:link", ATOM_NS)
        href = link.attrib.get("href") if link is not None else None
        if not href:
            continue
        cap_root = ET.fromstring(_http_get(href))
        sent_s = _cap_text(cap_root, "sent")
        try:
            sent_dt = datetime.fromisoformat(sent_s)
        except ValueError:
            sent_dt = datetime.now(tz=TAIPEI)
        desc = _cap_text(cap_root, "description")
        area = _cap_text(cap_root, "areaDesc")
        out.append(
            CapWorkStop(
                area=area,
                sent=sent_s,
                effective=_cap_text(cap_root, "effective"),
                expires=_cap_text(cap_root, "expires"),
                headline=_cap_text(cap_root, "headline"),
                description=desc,
                status=_cap_text(cap_root, "status"),
                msg_type=_cap_text(cap_root, "msgType"),
                href=href,
                target_date=_parse_target_date(desc, sent_dt),
                class_=_classify_work_stop(desc + " " + _cap_text(cap_root, "headline")),
                is_taipei=_is_taipei(area, desc),
            )
        )
    return out


def taipei_typhoon_intent(asof: date, caps: list[CapWorkStop] | None = None) -> dict[str, Any]:
    items = caps if caps is not None else fetch_dgpa_caps()
    hits = [
        c
        for c in items
        if c.is_taipei
        and c.status == "Actual"
        and c.target_date == asof
        and c.class_ in ("FULL_DAY", "MORNING")
    ]
    afternoon = [
        c
        for c in items
        if c.is_taipei
        and c.status == "Actual"
        and c.target_date == asof
        and c.class_ == "AFTERNOON"
    ]
    return {
        "closes_twse": bool(hits),
        "afternoon_only": bool(afternoon) and not hits,
        "hits": [asdict(c) for c in hits],
        "afternoon_hits": [asdict(c) for c in afternoon],
    }


def probe_session(
    asof: date | None = None,
    *,
    use_network: bool = True,
    holiday_schedule: dict[str, Any] | None = None,
    calendar: Sequence[DayRecord] | None = None,
    caps: list[CapWorkStop] | None = None,
    mi_payload: dict[str, Any] | None = None,
    mis_payloads: Sequence[dict[str, Any]] | None = None,
    now_taipei: datetime | None = None,
) -> SessionProbe:
    """Verdict for one day — prefers integrated annual calendar when provided."""
    day = asof or datetime.now(tz=TAIPEI).date()
    now = now_taipei or datetime.now(tz=TAIPEI)
    notes: list[str] = []
    sources: dict[str, Any] = {}

    if calendar is not None:
        rec = lookup_day(calendar, day)
        if rec is not None:
            sources["annual_calendar"] = rec.to_row()
            if not rec.is_session:
                return SessionProbe(
                    asof=day.isoformat(),
                    weekday=day.weekday(),
                    status=rec.kind,
                    broker_submit_allowed=False,
                    is_session=False,
                    sources=sources,
                    notes=[f"annual:{rec.source}"],
                )
            # planned open — still confirm with live MI/CAP when networking
            notes.append("annual planned SESSION")

    # Build from schedule if no calendar row
    if calendar is None:
        sched = holiday_schedule
        if sched is None and use_network:
            sched = fetch_holiday_schedule()
        hstat = holiday_status_for(day, sched) if sched is not None else None
        if sched is not None:
            sources["holidaySchedule"] = {"status": hstat}

        if day.weekday() >= 5 and hstat != "OPEN_MARKER":
            if hstat == "CLOSED_HOLIDAY":
                return SessionProbe(
                    asof=day.isoformat(),
                    weekday=day.weekday(),
                    status="CLOSED_HOLIDAY",
                    broker_submit_allowed=False,
                    is_session=False,
                    sources=sources,
                    notes=["weekend+holidaySchedule"],
                )
            return SessionProbe(
                asof=day.isoformat(),
                weekday=day.weekday(),
                status="WEEKEND",
                broker_submit_allowed=False,
                is_session=False,
                sources=sources,
                notes=["weekend"],
            )

        if hstat == "CLOSED_HOLIDAY":
            return SessionProbe(
                asof=day.isoformat(),
                weekday=day.weekday(),
                status="CLOSED_HOLIDAY",
                broker_submit_allowed=False,
                is_session=False,
                sources=sources,
                notes=["listed on TWSE holidaySchedule as non-trade"],
            )

    if use_network or caps is not None:
        intent = taipei_typhoon_intent(day, caps)
        sources["dgpa_cap"] = {
            "closes_twse": intent["closes_twse"],
            "afternoon_only": intent["afternoon_only"],
            "n_hits": len(intent["hits"]),
        }
        if intent["closes_twse"]:
            return SessionProbe(
                asof=day.isoformat(),
                weekday=day.weekday(),
                status="CLOSED_TYPHOON_INTENT",
                broker_submit_allowed=False,
                is_session=False,
                sources=sources,
                notes=notes + ["Taipei FULL_DAY/MORNING 停班 via NCDR CAP"],
            )
        if intent["afternoon_only"]:
            notes.append("Taipei AFTERNOON 停班 only — board still opens")

    # Intraday positive OPEN (fills MI_INDEX morning gap)
    if use_network or mis_payloads is not None:
        mis = probe_mis_intraday_open(day, payloads=mis_payloads)
        sources["mis_quote"] = {
            "open": mis["open"],
            "n_hits": mis["n_hits"],
            "rows": mis["rows"],
        }
        if mis["open"]:
            return SessionProbe(
                asof=day.isoformat(),
                weekday=day.weekday(),
                status="OPEN",
                broker_submit_allowed=True,
                is_session=True,
                sources=sources,
                notes=notes + ["MIS delayed quote d==asof + open price"],
            )
        now_tp = now.astimezone(TAIPEI)
        if now_tp.date() == day and (now_tp.hour, now_tp.minute) < MIS_OPEN_READY:
            notes.append("MIS before 09:05 — open may still be forming")
        else:
            notes.append("MIS no same-day open yet")

    if use_network or mi_payload is not None:
        payload = mi_payload if mi_payload is not None else fetch_mi_index(day)
        mi_ok = mi_index_has_session(day, payload)
        sources["mi_index"] = {"stat": payload.get("stat"), "has_session": mi_ok}
        now_tp = now.astimezone(TAIPEI)
        after_close = (now_tp.date() > day) or (now_tp.date() == day and now_tp.hour >= 14)
        sources["mi_index"]["after_close_heuristic"] = after_close
        if mi_ok:
            return SessionProbe(
                asof=day.isoformat(),
                weekday=day.weekday(),
                status="OPEN",
                broker_submit_allowed=True,
                is_session=True,
                sources=sources,
                notes=notes + ["MI_INDEX OK"],
            )
        if after_close and not mi_ok:
            return SessionProbe(
                asof=day.isoformat(),
                weekday=day.weekday(),
                status="CLOSED_TYPHOON_OR_NODATA",
                broker_submit_allowed=False,
                is_session=False,
                sources=sources,
                notes=notes + ["MI_INDEX empty after close heuristic"],
            )
        notes.append("MI_INDEX empty before close heuristic → not conclusive")

    return SessionProbe(
        asof=day.isoformat(),
        weekday=day.weekday(),
        status="UNKNOWN",
        broker_submit_allowed=False,
        is_session=False,
        sources=sources,
        notes=notes + ["fail-closed for broker until OPEN confirmed"],
    )


def build_year_with_live_overlays(
    year: int,
    *,
    schedule: dict[str, Any] | None = None,
    fetch_caps: bool = True,
    mi_fact_dates: Sequence[date] | None = None,
    taifex_fact_dates: Sequence[date] | None = None,
    overrides_path: Path | None = None,
) -> list[DayRecord]:
    """Annual plan + optional live CAP + optional MI/TAIFEX facts for given dates."""
    base = build_annual_calendar(year, schedule)
    caps = fetch_dgpa_caps() if fetch_caps else []
    mi_closed: list[date] = []
    mi_open: list[date] = []
    now_tp = datetime.now(tz=TAIPEI)
    for d in mi_fact_dates or ():
        if d.year != year:
            continue
        try:
            ok = mi_index_has_session(d)
        except Exception:
            continue
        if ok:
            mi_open.append(d)
            continue
        rec = lookup_day(base, d)
        if not (rec and rec.is_session):
            continue
        # Intraday: today's empty MI_INDEX is inconclusive — do not pin typhoon on annual CSV.
        if d == now_tp.date() and now_tp.hour < 14:
            continue
        mi_closed.append(d)

    taifex_closed: list[date] = []
    taifex_open: list[date] = []
    fact_dates = [d for d in (taifex_fact_dates or ()) if d.year == year]
    if fact_dates:
        start, end = min(fact_dates), max(fact_dates)
        try:
            open_days = fetch_taifex_tx_day_sessions(start, end)
        except Exception:
            open_days = set()
        for d in fact_dates:
            verdict = classify_taifex_day_fact(
                d, history_open_days=open_days, now_taipei=now_tp
            )
            rec = lookup_day(base, d)
            if verdict == "OPEN":
                taifex_open.append(d)
            elif verdict == "CLOSED" and rec and rec.is_session:
                taifex_closed.append(d)

    overrides = load_overrides(overrides_path) if overrides_path else {}
    return apply_overlays(
        base,
        caps=caps,
        mi_closed=mi_closed,
        mi_open=mi_open,
        taifex_closed=taifex_closed,
        taifex_open=taifex_open,
        overrides=overrides,
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--asof", default=None, help="YYYY-MM-DD probe one day")
    ap.add_argument("--build-year", type=int, default=None, help="Build integrated annual CSV")
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="CSV path (default data/calendars/twse_sessions_YYYY.csv)",
    )
    ap.add_argument(
        "--mi-facts-from",
        default=None,
        help="YYYY-MM-DD: also probe MI_INDEX from this date through today for overlays",
    )
    ap.add_argument(
        "--taifex-facts-from",
        default=None,
        help="YYYY-MM-DD: overlay TX day-session presence via futDataDown through today",
    )
    ap.add_argument("--overrides", type=Path, default=None)
    ap.add_argument("--json-out", type=Path, default=None)
    ap.add_argument("--no-caps", action="store_true")
    a = ap.parse_args()

    if a.build_year:
        year = int(a.build_year)
        mi_dates: list[date] = []
        if a.mi_facts_from:
            start = date.fromisoformat(a.mi_facts_from)
            today = datetime.now(tz=TAIPEI).date()
            d = start
            while d <= today:
                mi_dates.append(d)
                d += timedelta(days=1)
        taifex_dates: list[date] = []
        if a.taifex_facts_from:
            start = date.fromisoformat(a.taifex_facts_from)
            today = datetime.now(tz=TAIPEI).date()
            d = start
            while d <= today:
                taifex_dates.append(d)
                d += timedelta(days=1)
        cal = build_year_with_live_overlays(
            year,
            fetch_caps=not a.no_caps,
            mi_fact_dates=mi_dates,
            taifex_fact_dates=taifex_dates,
            overrides_path=a.overrides,
        )
        out = a.out or (DEFAULT_CALENDAR_DIR / f"twse_sessions_{year}.csv")
        write_calendar_csv(cal, out)
        n_sess = sum(1 for r in cal if r.is_session)
        n_hol = sum(1 for r in cal if r.kind == "CLOSED_HOLIDAY")
        n_ty = sum(1 for r in cal if "TYPHOON" in r.kind)
        summary = {
            "year": year,
            "out": str(out),
            "n_days": len(cal),
            "n_sessions": n_sess,
            "n_closed_holiday": n_hol,
            "n_typhoon_overlay": n_ty,
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    asof = date.fromisoformat(a.asof) if a.asof else None
    cal = None
    year = (asof or datetime.now(tz=TAIPEI).date()).year
    pinned = DEFAULT_CALENDAR_DIR / f"twse_sessions_{year}.csv"
    if pinned.exists():
        cal = read_calendar_csv(pinned)
    result = probe_session(asof, calendar=cal)
    payload = asdict(result)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    print(text, end="")
    if a.json_out:
        a.json_out.parent.mkdir(parents=True, exist_ok=True)
        a.json_out.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
