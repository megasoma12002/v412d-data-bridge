#!/usr/bin/env python3
"""Build a free-tier industry PIT *challenger* pack (events + sparse snapshots).

This does NOT replace TWT58U daily archive and must NOT silently patch E50-A0.
Outputs under ``data/research_advanced/industry_pit_challenger/``.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

UA = "v412-industry-pit-challenger/1.0"
OUT = Path("data/research_advanced/industry_pit_challenger")


# Curated public reclassification events (TWSE listed + TPEx OTC when known).
# Sources: TWSE announcement / 證券市場月訊 / Chinatimes / CNA / MoneyDJ.
CURATED_EVENTS: list[dict] = [
    # --- 2021-06-01 TWSE (Chinatimes 2021-05-04) ---
    {"effective_date": "2021-06-01", "market": "TWSE", "stock_id": "1443", "name": "立益", "old_industry": "紡織纖維", "new_industry": "其他", "source": "chinatimes_20210504", "confidence": "HIGH"},
    {"effective_date": "2021-06-01", "market": "TWSE", "stock_id": "1453", "name": "大將", "old_industry": "紡織纖維", "new_industry": "建材營造", "source": "chinatimes_20210504", "confidence": "HIGH"},
    {"effective_date": "2021-06-01", "market": "TWSE", "stock_id": "1456", "name": "怡華", "old_industry": "紡織纖維", "new_industry": "建材營造", "source": "chinatimes_20210504", "confidence": "HIGH"},
    {"effective_date": "2021-06-01", "market": "TWSE", "stock_id": "2241", "name": "艾姆勒", "old_industry": "電機機械", "new_industry": "汽車工業", "source": "chinatimes_20210504", "confidence": "HIGH"},
    {"effective_date": "2021-06-01", "market": "TWSE", "stock_id": "2429", "name": "銘旺科", "old_industry": "電子零組件業", "new_industry": "光電業", "source": "chinatimes_20210504", "confidence": "HIGH"},
    {"effective_date": "2021-06-01", "market": "TWSE", "stock_id": "2459", "name": "敦吉", "old_industry": "電子通路業", "new_industry": "其他電子業", "source": "chinatimes_20210504", "confidence": "HIGH"},
    {"effective_date": "2021-06-01", "market": "TWSE", "stock_id": "2614", "name": "東森", "old_industry": "貿易百貨", "new_industry": "其他", "source": "chinatimes_20210504", "confidence": "HIGH"},
    {"effective_date": "2021-06-01", "market": "TWSE", "stock_id": "3450", "name": "聯鈞", "old_industry": "其他電子業", "new_industry": "半導體業", "source": "chinatimes_20210504", "confidence": "HIGH"},
    {"effective_date": "2021-06-01", "market": "TWSE", "stock_id": "3669", "name": "圓展", "old_industry": "光電業", "new_industry": "通信網路業", "source": "chinatimes_20210504", "confidence": "HIGH"},
    {"effective_date": "2021-06-01", "market": "TWSE", "stock_id": "6165", "name": "浪凡", "old_industry": "電子零組件業", "new_industry": "其他", "source": "chinatimes_20210504", "confidence": "HIGH"},
    {"effective_date": "2021-06-01", "market": "TWSE", "stock_id": "8499", "name": "鼎炫-KY", "old_industry": "其他", "new_industry": "其他電子業", "source": "chinatimes_20210504", "confidence": "HIGH"},
    # --- 2022-06-01 TWSE (Chinatimes 2022-05-09) ---
    {"effective_date": "2022-06-01", "market": "TWSE", "stock_id": "2340", "name": "台亞", "old_industry": "光電業", "new_industry": "半導體業", "source": "chinatimes_20220509", "confidence": "HIGH"},
    {"effective_date": "2022-06-01", "market": "TWSE", "stock_id": "2495", "name": "普安", "old_industry": "其他電子業", "new_industry": "電腦及週邊設備業", "source": "chinatimes_20220509", "confidence": "HIGH"},
    {"effective_date": "2022-06-01", "market": "TWSE", "stock_id": "6431", "name": "光麗-KY", "old_industry": "光電業", "new_industry": "生技醫療業", "source": "chinatimes_20220509", "confidence": "HIGH"},
    # --- 2023-07-03 TWSE mega reclass (TWSE ann. + 證券市場月訊#76) ---
    # 綠能環保
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "3708", "name": "上緯投控", "old_industry": "化學工業", "new_industry": "綠能環保", "source": "twse_ann_1121802250+monthly76", "confidence": "HIGH"},
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "6581", "name": "鋼聯", "old_industry": "其他", "new_industry": "綠能環保", "source": "twse_ann_1121802250+monthly76", "confidence": "HIGH"},
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "6641", "name": "基士德-KY", "old_industry": "其他", "new_industry": "綠能環保", "source": "twse_ann_1121802250+monthly76", "confidence": "HIGH"},
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "6806", "name": "森崴能源", "old_industry": "其他", "new_industry": "綠能環保", "source": "twse_ann_1121802250+monthly76", "confidence": "HIGH"},
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "6869", "name": "雲豹能源", "old_industry": "其他", "new_industry": "綠能環保", "source": "twse_ann_1121802250+monthly76", "confidence": "HIGH"},
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "6873", "name": "泓德能源", "old_industry": "其他", "new_industry": "綠能環保", "source": "twse_ann_1121802250+monthly76", "confidence": "HIGH"},
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "8341", "name": "日友", "old_industry": "其他", "new_industry": "綠能環保", "source": "twse_ann_1121802250+monthly76", "confidence": "HIGH"},
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "8422", "name": "可寧衛", "old_industry": "其他", "new_industry": "綠能環保", "source": "twse_ann_1121802250+monthly76", "confidence": "HIGH"},
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "8438", "name": "昶昕", "old_industry": "其他", "new_industry": "綠能環保", "source": "twse_ann_1121802250+monthly76", "confidence": "HIGH"},
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "8473", "name": "山林水", "old_industry": "其他", "new_industry": "綠能環保", "source": "twse_ann_1121802250+monthly76", "confidence": "HIGH"},
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "9930", "name": "中聯資源", "old_industry": "其他", "new_industry": "綠能環保", "source": "twse_ann_1121802250+monthly76", "confidence": "HIGH"},
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "9955", "name": "佳龍", "old_industry": "其他", "new_industry": "綠能環保", "source": "twse_ann_1121802250+monthly76", "confidence": "HIGH"},
    # 數位雲端
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "3130", "name": "一零四", "old_industry": "資訊服務業", "new_industry": "數位雲端", "source": "twse_ann_1121802250+monthly76", "confidence": "HIGH"},
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "6165", "name": "浪凡", "old_industry": "其他", "new_industry": "數位雲端", "source": "twse_ann_1121802250+monthly76", "confidence": "HIGH"},
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "6689", "name": "伊雲谷", "old_industry": "其他電子業", "new_industry": "數位雲端", "source": "twse_ann_1121802250+monthly76", "confidence": "HIGH"},
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "8454", "name": "富邦媒", "old_industry": "貿易百貨", "new_industry": "數位雲端", "source": "twse_ann_1121802250+monthly76", "confidence": "HIGH"},
    # 運動休閒
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "1432", "name": "大魯閣", "old_industry": "貿易百貨", "new_industry": "運動休閒", "source": "twse_ann_1121802250+monthly76", "confidence": "HIGH"},
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "1598", "name": "岱宇", "old_industry": "生技醫療業", "new_industry": "運動休閒", "source": "twse_ann_1121802250+monthly76", "confidence": "HIGH"},
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "1736", "name": "喬山", "old_industry": "生技醫療業", "new_industry": "運動休閒", "source": "twse_ann_1121802250+monthly76", "confidence": "HIGH"},
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "4536", "name": "拓凱", "old_industry": "其他", "new_industry": "運動休閒", "source": "twse_ann_1121802250+monthly76", "confidence": "HIGH"},
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "5306", "name": "桂盟", "old_industry": "其他", "new_industry": "運動休閒", "source": "twse_ann_1121802250+monthly76", "confidence": "HIGH"},
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "6670", "name": "復盛應用", "old_industry": "其他", "new_industry": "運動休閒", "source": "twse_ann_1121802250+monthly76", "confidence": "HIGH"},
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "6768", "name": "志強-KY", "old_industry": "其他", "new_industry": "運動休閒", "source": "twse_ann_1121802250+monthly76", "confidence": "HIGH"},
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "8462", "name": "柏文", "old_industry": "觀光事業", "new_industry": "運動休閒", "source": "twse_ann_1121802250+monthly76", "confidence": "HIGH"},
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "8467", "name": "波力-KY", "old_industry": "其他", "new_industry": "運動休閒", "source": "twse_ann_1121802250+monthly76", "confidence": "HIGH"},
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "8478", "name": "東哥遊艇", "old_industry": "其他", "new_industry": "運動休閒", "source": "twse_ann_1121802250+monthly76", "confidence": "HIGH"},
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "9802", "name": "鈺齊-KY", "old_industry": "其他", "new_industry": "運動休閒", "source": "twse_ann_1121802250+monthly76", "confidence": "HIGH"},
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "9904", "name": "寶成", "old_industry": "其他", "new_industry": "運動休閒", "source": "twse_ann_1121802250+monthly76", "confidence": "HIGH"},
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "9910", "name": "豐泰", "old_industry": "其他", "new_industry": "運動休閒", "source": "twse_ann_1121802250+monthly76", "confidence": "HIGH"},
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "9914", "name": "美利達", "old_industry": "其他", "new_industry": "運動休閒", "source": "twse_ann_1121802250+monthly76", "confidence": "HIGH"},
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "9921", "name": "巨大", "old_industry": "其他", "new_industry": "運動休閒", "source": "twse_ann_1121802250+monthly76", "confidence": "HIGH"},
    # 居家生活
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "2062", "name": "橋椿", "old_industry": "其他", "new_industry": "居家生活", "source": "twse_ann_1121802250+monthly76", "confidence": "HIGH"},
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "3557", "name": "嘉威", "old_industry": "其他", "new_industry": "居家生活", "source": "twse_ann_1121802250+monthly76", "confidence": "HIGH"},
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "6671", "name": "三能-KY", "old_industry": "其他", "new_industry": "居家生活", "source": "twse_ann_1121802250+monthly76", "confidence": "HIGH"},
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "6754", "name": "匯僑設計", "old_industry": "其他", "new_industry": "居家生活", "source": "twse_ann_1121802250+monthly76", "confidence": "HIGH"},
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "6807", "name": "峰源-KY", "old_industry": "其他", "new_industry": "居家生活", "source": "twse_ann_1121802250+monthly76", "confidence": "HIGH"},
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "8464", "name": "億豐", "old_industry": "其他", "new_industry": "居家生活", "source": "twse_ann_1121802250+monthly76", "confidence": "HIGH"},
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "8482", "name": "商億-KY", "old_industry": "其他", "new_industry": "居家生活", "source": "twse_ann_1121802250+monthly76", "confidence": "HIGH"},
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "9911", "name": "櫻花", "old_industry": "其他", "new_industry": "居家生活", "source": "twse_ann_1121802250+monthly76", "confidence": "HIGH"},
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "9924", "name": "福興", "old_industry": "其他", "new_industry": "居家生活", "source": "twse_ann_1121802250+monthly76", "confidence": "HIGH"},
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "9934", "name": "成霖", "old_industry": "其他", "new_industry": "居家生活", "source": "twse_ann_1121802250+monthly76", "confidence": "HIGH"},
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "9935", "name": "慶豐富", "old_industry": "其他", "new_industry": "居家生活", "source": "twse_ann_1121802250+monthly76", "confidence": "HIGH"},
    # other 2023 moves (old industries from Yahoo TW stock news reprint of TWSE list)
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "1439", "name": "雋揚", "old_industry": "紡織纖維", "new_industry": "建材營造", "source": "twse_ann_1121802250+yahoo_news", "confidence": "HIGH"},
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "1472", "name": "三洋實業", "old_industry": "紡織纖維", "new_industry": "建材營造", "source": "twse_ann_1121802250+yahoo_news", "confidence": "HIGH"},
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "2442", "name": "新美齊", "old_industry": "電腦及週邊設備業", "new_industry": "建材營造", "source": "twse_ann_1121802250+yahoo_news", "confidence": "HIGH"},
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "2424", "name": "隴華", "old_industry": "電腦及週邊設備業", "new_industry": "通信網路業", "source": "twse_ann_1121802250+yahoo_news", "confidence": "HIGH"},
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "3054", "name": "立萬利", "old_industry": "半導體業", "new_industry": "食品工業", "source": "twse_ann_1121802250+yahoo_news", "confidence": "HIGH"},
    # taxonomy rename (not a company move, but PIT-relevant label change)
    {"effective_date": "2023-07-03", "market": "TWSE", "stock_id": "*", "name": "TAXONOMY", "old_industry": "觀光事業", "new_industry": "觀光餐旅", "source": "twse_ann_1120004601", "confidence": "HIGH", "event_type": "TAXONOMY_RENAME"},
    # --- 2026-06-01 TWSE (CNA 2026-05-08) ---
    {"effective_date": "2026-06-01", "market": "TWSE", "stock_id": "2601", "name": "益航", "old_industry": "貿易百貨", "new_industry": "航運業", "source": "cna_20260508", "confidence": "HIGH"},
    # --- 2026-06-01 TPEx (MoneyDJ / CNA) ---
    {"effective_date": "2026-06-01", "market": "TPEx", "stock_id": "1595", "name": "川寶", "old_industry": "電子零組件業", "new_industry": "半導體業", "source": "moneydj_20260520", "confidence": "HIGH"},
    {"effective_date": "2026-06-01", "market": "TPEx", "stock_id": "2230", "name": "泰茂", "old_industry": "電機機械", "new_industry": "居家生活", "source": "moneydj_20260520", "confidence": "HIGH"},
    {"effective_date": "2026-06-01", "market": "TPEx", "stock_id": "3067", "name": "全域", "old_industry": "其他電子業", "new_industry": "居家生活", "source": "moneydj_20260520", "confidence": "HIGH"},
    {"effective_date": "2026-06-01", "market": "TPEx", "stock_id": "3131", "name": "弘塑", "old_industry": "其他電子業", "new_industry": "半導體業", "source": "moneydj_20260520", "confidence": "HIGH"},
    {"effective_date": "2026-06-01", "market": "TPEx", "stock_id": "3313", "name": "斐成", "old_industry": "其他", "new_industry": "建材營造", "source": "moneydj_20260520", "confidence": "HIGH"},
    {"effective_date": "2026-06-01", "market": "TPEx", "stock_id": "4905", "name": "台聯電訊", "old_industry": "通信網路業", "new_industry": "生技醫療", "source": "moneydj_20260520", "confidence": "HIGH"},
    {"effective_date": "2026-06-01", "market": "TPEx", "stock_id": "4924", "name": "欣厚", "old_industry": "電腦及週邊設備業", "new_industry": "綠能環保", "source": "moneydj_20260520", "confidence": "HIGH"},
    {"effective_date": "2026-06-01", "market": "TPEx", "stock_id": "5381", "name": "光譜電工", "old_industry": "電子零組件業", "new_industry": "電機機械", "source": "moneydj_20260520", "confidence": "HIGH"},
    {"effective_date": "2026-06-01", "market": "TPEx", "stock_id": "6125", "name": "廣運", "old_industry": "光電業", "new_industry": "電機機械", "source": "moneydj_20260520", "confidence": "HIGH"},
    {"effective_date": "2026-06-01", "market": "TPEx", "stock_id": "6163", "name": "華電聯網", "old_industry": "通信網路業", "new_industry": "資訊服務業", "source": "moneydj_20260520", "confidence": "HIGH"},
    {"effective_date": "2026-06-01", "market": "TPEx", "stock_id": "6236", "name": "中湛", "old_industry": "其他", "new_industry": "數位雲端", "source": "moneydj_20260520", "confidence": "HIGH"},
    {"effective_date": "2026-06-01", "market": "TPEx", "stock_id": "7718", "name": "友鋮", "old_industry": "鋼鐵工業", "new_industry": "電機機械", "source": "moneydj_20260520", "confidence": "HIGH"},
    {"effective_date": "2026-06-01", "market": "TPEx", "stock_id": "8932", "name": "智通科創", "old_industry": "其他", "new_industry": "數位雲端", "source": "moneydj_20260520", "confidence": "HIGH"},
]


class _TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag, attrs):
        t = tag.lower()
        if t == "tr":
            self._row = []
        elif t in ("td", "th") and self._row is not None:
            self._cell = []

    def handle_endtag(self, tag):
        t = tag.lower()
        if t in ("td", "th") and self._cell is not None and self._row is not None:
            text = re.sub(r"\s+", " ", "".join(self._cell)).strip()
            self._row.append(text)
            self._cell = None
        elif t == "tr" and self._row is not None:
            if self._row:
                self.rows.append(self._row)
            self._row = None

    def handle_data(self, data):
        if self._cell is not None:
            self._cell.append(data)


def http_bytes(url: str, timeout: int = 90) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read()


def http_json(url: str, timeout: int = 90):
    return json.loads(http_bytes(url, timeout=timeout).decode("utf-8-sig", errors="ignore"))


def save_csv(rows: list[dict], path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return 0
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def normalize_industry(label: str) -> str:
    """Collapse common TWSE/ISIN naming variants for QC joins."""
    s = (label or "").strip()
    aliases = {
        "建材營造業": "建材營造",
        "金融保險業": "金融保險",
        "貿易百貨業": "貿易百貨",
        "其他業": "其他",
        "生技醫療": "生技醫療業",
        "觀光事業": "觀光餐旅",  # post-2023-07 rename for QC against current
    }
    return aliases.get(s, s)


def parse_class_main(html: str, as_of_date: str, source: str) -> list[dict]:
    parser = _TableParser()
    parser.feed(html)
    rows: list[dict] = []
    for cells in parser.rows:
        if len(cells) < 7:
            continue
        sid = cells[2].strip()
        if not re.fullmatch(r"\d{4}", sid):
            continue
        rows.append(
            {
                "as_of_date": as_of_date,
                "stock_id": sid,
                "name": cells[3].strip(),
                "market": cells[4].strip(),
                "security_type": cells[5].strip(),
                "industry": cells[6].strip(),
                "industry_norm": normalize_industry(cells[6]),
                "listing_date": cells[7].strip() if len(cells) > 7 else "",
                "source": source,
                "pit_note": "CURRENT_SNAPSHOT_NAMED",
            }
        )
    return rows


def fetch_isin_class_main(out: Path, status: dict) -> list[dict]:
    """Full named industry map from ISIN class_main (listed equities)."""
    as_of = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    url = (
        "https://isin.twse.com.tw/isin/class_main.jsp?"
        "owncode=&stockname=&isincode=&market=1&issuetype=1&industry_code=&Page=1&chklike=Y"
    )
    raw = http_bytes(url)
    html = raw.decode("cp950", errors="ignore")
    if "台泥" not in html:
        html = raw.decode("utf-8", errors="ignore")
    rows = parse_class_main(html, as_of, "ISIN_class_main_listed")
    n = save_csv(rows, out / "snapshot_isin_class_main_listed.csv")
    status["snapshot_isin_class_main"] = {"status": "PASS" if n else "EMPTY", "rows": n}
    return rows


def fetch_current_twse_snapshot(out: Path, status: dict, named: list[dict]) -> list[dict]:
    url = "https://openapi.twse.com.tw/v1/opendata/t187ap03_L"
    raw = http_json(url)
    named_map = {r["stock_id"]: r for r in named}
    rows = []
    code_map: dict[str, str] = {}
    for item in raw:
        sid = str(item.get("公司代號") or "").strip()
        code = str(item.get("產業別") or "").strip()
        name = str(item.get("公司簡稱") or item.get("公司名稱") or "").strip()
        industry_name = named_map.get(sid, {}).get("industry", "")
        if code and industry_name:
            code_map[code] = industry_name
        rows.append(
            {
                "as_of_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "stock_id": sid,
                "name": name,
                "industry_code": code,
                "industry": industry_name or code,
                "industry_norm": normalize_industry(industry_name) if industry_name else code,
                "listing_date": str(item.get("上市日期") or "").strip(),
                "source": "TWSE_openapi_t187ap03_L+ISIN_name",
                "pit_note": "CURRENT_SNAPSHOT",
            }
        )
    n = save_csv(rows, out / "snapshot_twse_current.csv")
    code_rows = [{"industry_code": k, "industry": v, "industry_norm": normalize_industry(v)} for k, v in sorted(code_map.items())]
    save_csv(code_rows, out / "industry_code_map.csv")
    status["snapshot_twse_current"] = {"status": "PASS" if n else "EMPTY", "rows": n}
    status["industry_code_map"] = {"status": "PASS" if code_rows else "EMPTY", "rows": len(code_rows)}
    return rows


def cdx_isin_timestamps(limit: int = 12) -> list[tuple[str, str]]:
    """Return (timestamp, original_url) for ISIN public list pages."""
    query = urllib.parse.urlencode(
        {
            "url": "isin.twse.com.tw/isin/C_public.jsp?strMode=1",
            "output": "json",
            "fl": "timestamp,original,statuscode",
            "filter": "statuscode:200",
            "collapse": "timestamp:6",
            "limit": str(limit),
        }
    )
    url = "http://web.archive.org/cdx/search/cdx?" + query
    data = http_json(url, timeout=60)
    out = []
    for row in data[1:]:
        out.append((row[0], row[1]))
    return out


def parse_isin_html(html: str, as_of_date: str, source: str) -> list[dict]:
    parser = _TableParser()
    parser.feed(html)
    rows: list[dict] = []
    for cells in parser.rows:
        if len(cells) < 4:
            continue
        # header-ish
        joined = "".join(cells)
        if "產業別" in joined or "有價證券代號" in joined or "國際證券編碼" in joined:
            continue
        code_name = cells[0]
        m = re.match(r"^(\d{4})\s*(.*)$", code_name)
        if not m:
            # some pages use fullwidth space
            m = re.match(r"^(\d{4})\u3000(.*)$", code_name)
        if not m:
            continue
        industry = cells[3] if len(cells) > 3 else ""
        if not industry or industry in ("ESVUFR", "ESVUFR "):
            # shifted columns sometimes
            for cell in cells[1:]:
                if any(k in cell for k in ("工業", "業", "其他", "金融", "半導體", "光電", "水泥")):
                    industry = cell
                    break
        rows.append(
            {
                "as_of_date": as_of_date,
                "stock_id": m.group(1),
                "name": m.group(2).strip(),
                "industry": industry.strip(),
                "source": source,
                "pit_note": "WAYBACK_SPARSE_SNAPSHOT",
            }
        )
    return rows


def fetch_wayback_isin_snapshots(out: Path, status: dict, max_snaps: int = 4) -> dict[str, dict[str, str]]:
    """Fetch a few archived ISIN industry maps. Returns as_of -> {stock_id: industry}."""
    snaps_dir = out / "wayback_isin_snapshots"
    snaps_dir.mkdir(parents=True, exist_ok=True)
    maps: dict[str, dict[str, str]] = {}
    try:
        stamps = cdx_isin_timestamps(limit=20)
    except Exception as exc:  # noqa: BLE001
        status["wayback_cdx"] = {"status": "FAIL", "error": str(exc)}
        return maps

    status["wayback_cdx"] = {"status": "PASS", "candidates": len(stamps)}
    # prefer spread across years
    picked = []
    seen_years = set()
    for ts, original in stamps:
        year = ts[:4]
        if year in seen_years and len(picked) >= max_snaps:
            continue
        if year not in seen_years or len(picked) < max_snaps:
            if year not in seen_years:
                seen_years.add(year)
                picked.append((ts, original))
        if len(picked) >= max_snaps:
            break
    if not picked:
        picked = stamps[:max_snaps]

    all_rows: list[dict] = []
    snap_meta = []
    for ts, original in picked:
        as_of = f"{ts[0:4]}-{ts[4:6]}-{ts[6:8]}"
        archive_url = f"https://web.archive.org/web/{ts}id_/{original}"
        try:
            raw = http_bytes(archive_url, timeout=90)
            # ISIN historically big5/cp950
            html = raw.decode("cp950", errors="ignore")
            if "產業別" not in html and "水泥" not in html:
                html = raw.decode("utf-8", errors="ignore")
            rows = parse_isin_html(html, as_of, f"wayback_isin_{ts}")
            path = snaps_dir / f"isin_industry_{as_of}.csv"
            save_csv(rows, path)
            maps[as_of] = {r["stock_id"]: r["industry"] for r in rows if r["industry"]}
            all_rows.extend(rows)
            snap_meta.append({"as_of_date": as_of, "rows": len(rows), "path": str(path), "archive_url": archive_url})
            time.sleep(1.0)
        except Exception as exc:  # noqa: BLE001
            snap_meta.append({"as_of_date": as_of, "error": str(exc), "archive_url": archive_url})

    save_csv(all_rows, out / "wayback_isin_sparse_all.csv")
    status["wayback_isin_snapshots"] = {
        "status": "PASS" if maps else "FAIL",
        "snapshots": snap_meta,
        "combined_rows": len(all_rows),
    }
    return maps


def fill_missing_old_industries(events: list[dict], maps: dict[str, dict[str, str]]) -> None:
    """Fill blank old_industry from the latest Wayback snapshot before effective_date."""
    ordered = sorted(maps.keys())
    for ev in events:
        if ev.get("old_industry") or ev.get("stock_id") == "*":
            continue
        eff = ev["effective_date"]
        priors = [d for d in ordered if d < eff]
        if not priors:
            continue
        industry = maps[priors[-1]].get(ev["stock_id"], "")
        if industry:
            ev["old_industry"] = industry
            ev["old_industry_fill"] = f"wayback_isin_{priors[-1]}"
            if ev.get("confidence") == "MED":
                ev["confidence"] = "MED_FILLED"


def build_event_asof_overlay(events: list[dict], current: list[dict], out: Path) -> list[dict]:
    """For event-touched tickers only: reconstruct industry at each event effective date.

    Non-event tickers are NOT backfilled — that would invent false PIT.
    """
    company_events = [e for e in events if e.get("stock_id") != "*" and e.get("event_type") != "TAXONOMY_RENAME"]
    by_id: dict[str, list[dict]] = {}
    for ev in company_events:
        by_id.setdefault(ev["stock_id"], []).append(ev)
    for sid in by_id:
        by_id[sid].sort(key=lambda x: x["effective_date"])

    current_map = {r["stock_id"]: r for r in current if r.get("stock_id")}
    rows: list[dict] = []
    for sid, evs in sorted(by_id.items()):
        # start from earliest known old, then apply
        industry = evs[0].get("old_industry") or ""
        name = evs[0].get("name") or (current_map.get(sid) or {}).get("name", "")
        market = evs[0].get("market", "")
        # day before first event (if old known)
        if industry:
            rows.append(
                {
                    "as_of_date": _day_before(evs[0]["effective_date"]),
                    "stock_id": sid,
                    "name": name,
                    "market": market,
                    "industry": industry,
                    "source": "event_reconstructed_pre",
                    "pit_note": "EVENT_TOUCHED_ONLY_NOT_FULL_UNIVERSE",
                }
            )
        for ev in evs:
            industry = ev.get("new_industry") or industry
            rows.append(
                {
                    "as_of_date": ev["effective_date"],
                    "stock_id": sid,
                    "name": ev.get("name") or name,
                    "market": ev.get("market") or market,
                    "industry": industry,
                    "source": "event_reconstructed",
                    "pit_note": "EVENT_TOUCHED_ONLY_NOT_FULL_UNIVERSE",
                }
            )
        # stamp current if available
        if sid in current_map:
            rows.append(
                {
                    "as_of_date": current_map[sid]["as_of_date"],
                    "stock_id": sid,
                    "name": current_map[sid].get("name") or name,
                    "market": market or "TWSE",
                    "industry": current_map[sid].get("industry") or industry,
                    "source": "current_overlay",
                    "pit_note": "EVENT_TOUCHED_ONLY_NOT_FULL_UNIVERSE",
                }
            )
    save_csv(rows, out / "event_touched_sparse_pit.csv")
    return rows


def _day_before(ymd: str) -> str:
    y, m, d = map(int, ymd.split("-"))
    from datetime import date, timedelta

    return (date(y, m, d) - timedelta(days=1)).isoformat()


def write_readme(out: Path, status: dict) -> None:
    text = f"""# Industry PIT Challenger (free / sparse)

Generated: {status.get("generated_at")}

## What this is
- **Event table** of TWSE/TPEx industry reclassifications assembled from public
  announcements / reputable media reprints.
- **Sparse Wayback ISIN snapshots** (`C_public.jsp?strMode=1`) for a few years.
- **Event-touched sparse PIT** for tickers that appear in the event table only.

## What this is NOT
- Not TWT58U daily archive.
- Not a full-universe historical industry map.
- Not a silent patch to E50-A0 / A0 security_master.

## Files
| File | Meaning |
|---|---|
| `industry_reclass_events.csv` | old→new on effective_date |
| `snapshot_isin_class_main_listed.csv` | live ISIN named industries (listed) |
| `snapshot_twse_current.csv` | TWSE OpenAPI codes + ISIN names |
| `industry_code_map.csv` | 2-digit code → industry name |
| `wayback_isin_snapshots/` | sparse archived ISIN maps (partial universe) |
| `wayback_isin_sparse_all.csv` | combined Wayback rows |
| `event_touched_sparse_pit.csv` | reconstructed as-of for event tickers only |
| `fetch_status.json` | machine status |

## Still required for true industry-neutral alpha
1. Buy/archive TWSE E-Shop **TWT58U** (from 2019-12-23), or
2. TEJ company-attribute PIT (from ~2013), with lineage QC vs TWSE codes.
"""
    (out / "README.md").write_text(text)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(OUT))
    parser.add_argument("--max-wayback", type=int, default=4)
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    status: dict = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "contract": "CHALLENGER_SPARSE_NOT_TWT58U",
        "a0_untouched": True,
    }

    events = [dict(e) for e in CURATED_EVENTS]
    for ev in events:
        ev.setdefault("event_type", "COMPANY_RECLASS")

    named = fetch_isin_class_main(out, status)
    current = fetch_current_twse_snapshot(out, status, named)
    maps = fetch_wayback_isin_snapshots(out, status, max_snaps=args.max_wayback)
    fill_missing_old_industries(events, maps)

    n_events = save_csv(events, out / "industry_reclass_events.csv")
    status["industry_reclass_events"] = {
        "status": "PASS",
        "rows": n_events,
        "twse_company_rows": sum(1 for e in events if e.get("market") == "TWSE" and e.get("stock_id") != "*"),
        "tpex_company_rows": sum(1 for e in events if e.get("market") == "TPEx"),
        "missing_old_industry": sum(1 for e in events if e.get("stock_id") != "*" and not e.get("old_industry")),
    }

    overlay = build_event_asof_overlay(events, current, out)
    status["event_touched_sparse_pit"] = {"status": "PASS", "rows": len(overlay)}

    # QC: event new_industry vs current for TWSE names where current exists
    mismatches = []
    cur = {r["stock_id"]: normalize_industry(r.get("industry_norm") or r.get("industry") or "") for r in current}
    latest: dict[str, str] = {}
    for ev in sorted(events, key=lambda x: x["effective_date"]):
        if ev.get("stock_id") in (None, "*"):
            continue
        if ev.get("market") != "TWSE":
            continue
        latest[ev["stock_id"]] = normalize_industry(ev.get("new_industry") or latest.get(ev["stock_id"], ""))
    for sid, ind in latest.items():
        if sid in cur and cur[sid] and ind and cur[sid] != ind:
            mismatches.append({"stock_id": sid, "event_new": ind, "current": cur[sid]})
    status["qc_event_vs_current"] = {
        "checked": len([s for s in latest if s in cur and cur[s]]),
        "mismatches": len(mismatches),
        "examples": mismatches[:10],
        "note": "Compares normalized labels; delisted/renamed residual mismatches are OK",
    }

    write_readme(out, status)
    (out / "fetch_status.json").write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
