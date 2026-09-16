#!/usr/bin/env python3
"""Automated TWSE session / typhoon-close signal acquisition (research + ops).

Sources (no broker secrets):
  1) TWSE holidaySchedule JSON — planned 国定假 / special non-trade days
  2) NCDR CAP ATOM (DGPA 停班停課) — typhoon intent; **臺北市** full/AM → TWSE close
  3) TWSE MI_INDEX JSON — ex-post fact (reliable **after** daily close; empty intraday ≠ closed)

Soft-Frozen / LIVE_* unchanged. Observe / preflight only.
"""
from __future__ import annotations

import argparse
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

TAIPEI = ZoneInfo("Asia/Taipei")
UA = {"User-Agent": "e21-ops-twse-session/1.0"}

HOLIDAY_URL = "https://www.twse.com.tw/holidaySchedule/holidaySchedule?response=json"
MI_INDEX_URL = (
    "https://www.twse.com.tw/exchangeReport/MI_INDEX"
    "?response=json&date={yyyymmdd}&type=ALLBUT0999"
)
NCDR_ATOM_URL = "https://alerts.ncdr.nat.gov.tw/RssAtomFeed.ashx?AlertType=33"

ATOM_NS = {"a": "http://www.w3.org/2005/Atom"}
CAP_NS = "urn:oasis:names:tc:emergency:cap:1.2"

# holidaySchedule rows that mean no continuous board (name contains)
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
    class_: str  # FULL_DAY | MORNING | AFTERNOON | SCHOOL_ONLY | UNKNOWN
    is_taipei: bool


@dataclass
class SessionProbe:
    asof: str
    weekday: int
    status: str
    broker_submit_allowed: bool
    sources: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


def _http_get(url: str, timeout: float = 60.0) -> bytes:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def fetch_holiday_schedule(*, year: int | None = None) -> dict[str, Any]:
    """TWSE planned open/close calendar (no typhoon rows)."""
    raw = json.loads(_http_get(HOLIDAY_URL).decode("utf-8"))
    if year is not None and int(raw.get("queryYear") or 0) != int(year):
        # API returns current published year; filter client-side if needed.
        pass
    return raw


def holiday_status_for(day: date, schedule: dict[str, Any] | None = None) -> str | None:
    """Return CLOSED_HOLIDAY / OPEN_MARKER / None (not listed)."""
    sched = schedule if schedule is not None else fetch_holiday_schedule()
    for row in sched.get("data") or []:
        if not row or len(row) < 2:
            continue
        d_s, name = str(row[0]), str(row[1])
        if d_s != day.isoformat():
            continue
        if any(h in name for h in _OPEN_NAME_HINTS):
            return "OPEN_MARKER"
        if any(h in name for h in _CLOSED_NAME_HINTS) or "市場無交易" in name:
            return "CLOSED_HOLIDAY"
        # unnamed special — treat as closed if not explicitly start-trade
        return "CLOSED_HOLIDAY"
    return None


def fetch_mi_index(day: date) -> dict[str, Any]:
    url = MI_INDEX_URL.format(yyyymmdd=day.strftime("%Y%m%d"))
    return json.loads(_http_get(url).decode("utf-8"))


def mi_index_has_session(day: date, payload: dict[str, Any] | None = None) -> bool:
    obj = payload if payload is not None else fetch_mi_index(day)
    if obj.get("stat") != "OK":
        return False
    tables = obj.get("tables")
    return isinstance(tables, list) and len(tables) > 0


def _cap_text(root: ET.Element, tag: str) -> str:
    for el in root.iter():
        if el.tag.split("}")[-1] == tag and el.text:
            return el.text.strip()
    return ""


def _parse_target_date(desc: str, sent: datetime) -> date | None:
    """Map CAP description date phrases onto a calendar date (Taipei)."""
    sent_d = sent.astimezone(TAIPEI).date()
    if re.search(r"今天|今日", desc):
        return sent_d
    if re.search(r"明天|明日", desc):
        return sent_d + timedelta(days=1)
    # M/D or MM/DD relative to sent year
    m = re.search(r"(?<!\d)(\d{1,2})/(\d{1,2})(?!\d)", desc)
    if m:
        mm, dd = int(m.group(1)), int(m.group(2))
        try:
            return date(sent_d.year, mm, dd)
        except ValueError:
            return None
    return None


def _classify_work_stop(text: str) -> str:
    """Classify DGPA 停班 wording for TWSE impact."""
    if re.search(r"未達停止上班.*停止上課|照常上班.*停止上課|停止上課(?!.*停止上班)", text):
        if "停止上班" not in text or "未達停止上班" in text:
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
    # Whole city only — 區級 alone should not close TWSE; still flag Taipei districts
    # but TWSE rule is 臺北市全體公教. Prefer exact city.
    if re.search(r"臺北市(?!.*區)|台北市(?!.*區)", blob):
        # If only a district is named without city-wide, areaDesc is often "臺北市中正區"
        if re.search(r"臺北市.+區|台北市.+區", area) and "全體" not in blob:
            # District-level: still Taipei geography but NOT city-wide — do not auto-close
            return False
        return True
    if area.strip() in ("臺北市", "台北市"):
        return True
    return False


def fetch_dgpa_caps(*, atom_url: str = NCDR_ATOM_URL) -> list[CapWorkStop]:
    """Pull NCDR ATOM AlertType=33 and parse each CAP."""
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
    """Early intent: Taipei city-wide full/morning 停班 for ``asof`` → TWSE full close."""
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
    caps: list[CapWorkStop] | None = None,
    mi_payload: dict[str, Any] | None = None,
    now_taipei: datetime | None = None,
) -> SessionProbe:
    """Combine holiday + CAP intent + MI_INDEX fact into a session verdict."""
    day = asof or datetime.now(tz=TAIPEI).date()
    now = now_taipei or datetime.now(tz=TAIPEI)
    notes: list[str] = []
    sources: dict[str, Any] = {}

    if day.weekday() >= 5:
        return SessionProbe(
            asof=day.isoformat(),
            weekday=day.weekday(),
            status="WEEKEND",
            broker_submit_allowed=False,
            sources=sources,
            notes=["weekend"],
        )

    # --- planned holiday ---
    if use_network or holiday_schedule is not None:
        sched = holiday_schedule if holiday_schedule is not None else fetch_holiday_schedule()
        hstat = holiday_status_for(day, sched)
        sources["holidaySchedule"] = {"status": hstat}
        if hstat == "CLOSED_HOLIDAY":
            return SessionProbe(
                asof=day.isoformat(),
                weekday=day.weekday(),
                status="CLOSED_HOLIDAY",
                broker_submit_allowed=False,
                sources=sources,
                notes=["listed on TWSE holidaySchedule as non-trade"],
            )

    # --- typhoon intent (Taipei CAP) ---
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
                sources=sources,
                notes=["Taipei FULL_DAY/MORNING 停班 via NCDR CAP"],
            )
        if intent["afternoon_only"]:
            notes.append("Taipei AFTERNOON 停班 only — board still opens")

    # --- MI_INDEX fact (after close; intraday empty is ambiguous) ---
    # Daily MI_INDEX is typically published after the session; before ~14:00 Taipei
    # an empty response on an otherwise open day is common → UNKNOWN not CLOSED.
    mi_ok: bool | None = None
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
                sources=sources,
                notes=notes + ["MI_INDEX OK"],
            )
        if after_close and mi_ok is False:
            return SessionProbe(
                asof=day.isoformat(),
                weekday=day.weekday(),
                status="CLOSED_TYPHOON_OR_NODATA",
                broker_submit_allowed=False,
                sources=sources,
                notes=notes + ["MI_INDEX empty after close heuristic"],
            )
        notes.append("MI_INDEX empty before close heuristic → not conclusive")

    return SessionProbe(
        asof=day.isoformat(),
        weekday=day.weekday(),
        status="UNKNOWN",
        broker_submit_allowed=False,
        sources=sources,
        notes=notes + ["fail-closed for broker until OPEN confirmed"],
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--asof", default=None, help="YYYY-MM-DD (default: Taipei today)")
    ap.add_argument("--json-out", type=Path, default=None)
    a = ap.parse_args()
    asof = date.fromisoformat(a.asof) if a.asof else None
    result = probe_session(asof)
    payload = asdict(result)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    print(text, end="")
    if a.json_out:
        a.json_out.parent.mkdir(parents=True, exist_ok=True)
        a.json_out.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
