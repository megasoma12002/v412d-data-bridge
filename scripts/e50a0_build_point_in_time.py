#!/usr/bin/env python3
"""V4.12-E50-A0 point-in-time Taiwan equity universe builder.

Raw and adjusted prices are deliberately stored separately.  Eligibility on a
date uses only observations available on or before that date.  Delisted names
are retained so a later alpha backtest does not silently become survivor-only.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

API = "https://api.finmindtrade.com/api/v4/data"
ETF_WORDS = ("ETF", "ETN", "指數股票型基金", "債券", "權證")


def api_get(dataset: str, *, stock_id: str | None = None,
            start: str | None = None, end: str | None = None,
            token: str = "", retries: int = 4) -> list[dict]:
    query = {"dataset": dataset}
    if stock_id:
        query["data_id"] = stock_id
    if start:
        query["start_date"] = start
    if end:
        query["end_date"] = end
    headers = {"User-Agent": "v412-e50a0/1.0"}
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
                raise RuntimeError(str(payload))
            return payload.get("data", [])
        except Exception:
            if attempt + 1 == retries:
                raise
            time.sleep(2 ** attempt)
    return []


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)


def canonical_master(info: pd.DataFrame, delisted: pd.DataFrame) -> pd.DataFrame:
    info = info.copy()
    for c in ("stock_id", "stock_name", "industry_category", "type"):
        info[c] = info[c].astype(str)
    ordinary = info.stock_id.str.fullmatch(r"\d{4}")
    ordinary &= info.type.isin(["twse", "tpex"])
    ordinary &= ~info.industry_category.str.contains("|".join(ETF_WORDS), na=False)
    ordinary &= ~info.stock_name.str.contains(r"-KY|KY|特別股|存託", regex=True, na=False)
    base = info.loc[ordinary].sort_values(
        ["stock_id", "industry_category"]
    ).drop_duplicates("stock_id", keep="first")
    dl = delisted.copy()
    dl["stock_id"] = dl.stock_id.astype(str)
    dl = dl[dl.stock_id.str.fullmatch(r"\d{4}")].sort_values("date")
    dl = dl.drop_duplicates("stock_id", keep="last").rename(
        columns={"date": "delisting_date", "stock_name": "delisted_name"}
    )
    master = base.merge(dl[["stock_id", "delisting_date"]], on="stock_id", how="outer")
    master["currently_listed"] = master.delisting_date.isna()
    master["eligible_security_type"] = master.stock_id.str.fullmatch(r"\d{4}")
    master["exclusion_reason"] = ""
    missing = master.stock_name.isna()
    master.loc[missing, "stock_name"] = "historical_delisted"
    master.loc[missing, "type"] = "historical_unknown"
    master.loc[missing, "industry_category"] = "historical_unknown"
    return master.sort_values("stock_id").reset_index(drop=True)


def normalize_price(rows: list[dict], adjusted: bool) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    d = pd.DataFrame(rows).rename(columns={"max": "high", "min": "low"})
    keep = ["date", "stock_id", "open", "high", "low", "close",
            "Trading_Volume", "Trading_money", "Trading_turnover"]
    for c in keep:
        if c not in d:
            d[c] = pd.NA
    d = d[keep].rename(columns={
        "stock_id": "code", "Trading_Volume": "volume",
        "Trading_money": "trading_money", "Trading_turnover": "trades"
    })
    d["date"] = pd.to_datetime(d.date)
    d["code"] = d.code.astype(str)
    for c in ["open", "high", "low", "close", "volume", "trading_money", "trades"]:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d["price_layer"] = "adjusted_research_only" if adjusted else "raw_execution"
    return d.sort_values(["date", "code"]).drop_duplicates(["date", "code"], keep="last")


def fetch_price_chunks(dataset: str, code: str, start: str, end: str,
                       token: str) -> list[dict]:
    """Fetch calendar-year chunks so large adjusted-price requests can resume reliably."""
    first = pd.Timestamp(start)
    last = pd.Timestamp(end)
    rows: list[dict] = []
    for year in range(first.year, last.year + 1):
        left = max(first, pd.Timestamp(year=year, month=1, day=1))
        right = min(last, pd.Timestamp(year=year, month=12, day=31))
        rows.extend(api_get(dataset, stock_id=code,
                            start=str(left.date()), end=str(right.date()), token=token))
        time.sleep(0.10)
    return rows


def fetch_shards(master: pd.DataFrame, out: Path, *, start: str, end: str,
                 token: str, limit: int, codes: list[str]) -> pd.DataFrame:
    selected = codes or master.loc[master.currently_listed, "stock_id"].tolist()
    if limit > 0:
        selected = selected[:limit]
    manifest_path = out / "download_manifest.csv"
    log = []
    for pos, code in enumerate(selected, 1):
        rec = {"code": code, "raw_status": "PENDING", "adjusted_status": "PENDING"}
        for dataset, folder, flag in [
            ("TaiwanStockPrice", "raw", False),
            ("TaiwanStockPriceAdj", "adjusted", True),
        ]:
            path = out / "shards" / folder / f"{code}.csv"
            try:
                if path.exists():
                    d = pd.read_csv(path, dtype={"code": str}, parse_dates=["date"])
                    if len(d) and str(d.date.min().date()) <= start and str(d.date.max().date()) >= end:
                        rec[f"{folder}_status"] = "CACHED"
                        rec[f"{folder}_rows"] = len(d)
                        continue
                rows = fetch_price_chunks(dataset, code, start, end, token)
                d = normalize_price(rows, flag)
                write_csv(d, path)
                rec[f"{folder}_status"] = "PASS" if len(d) else "EMPTY"
                rec[f"{folder}_rows"] = len(d)
                time.sleep(0.15)
            except Exception as exc:
                rec[f"{folder}_status"] = "FAIL"
                rec[f"{folder}_error"] = f"{type(exc).__name__}: {exc}"[:500]
        log.append(rec)
        write_csv(pd.DataFrame(log), manifest_path)
        print(f"[{pos}/{len(selected)}] {code} {rec['raw_status']} {rec['adjusted_status']}")
    return pd.DataFrame(log)


def load_shards(folder: Path) -> pd.DataFrame:
    frames = []
    for path in sorted(folder.glob("*.csv")):
        try:
            d = pd.read_csv(path, dtype={"code": str}, parse_dates=["date"])
            if len(d):
                frames.append(d)
        except pd.errors.EmptyDataError:
            pass
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def load_archive_market(input_dir: Path, start: str, end: str) -> tuple[pd.DataFrame, dict]:
    """Load official-derived daily archives in one pass for the whole market."""
    frames = []
    scanned = accepted = skipped = 0
    left, right = pd.Timestamp(start), pd.Timestamp(end)
    for path in sorted(input_dir.rglob("*.csv")):
        scanned += 1
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                names = {str(x).strip().lower().lstrip("\ufeff"): x for x in (reader.fieldnames or [])}
                if not {"date", "code", "open", "high", "low", "close", "volume"} <= set(names):
                    continue
                rows = []
                for raw in reader:
                    code = str(raw[names["code"]]).strip()
                    if not re.fullmatch(r"\d{4}", code) or int(code) < 1000:
                        continue
                    try:
                        raw_date = str(raw[names["date"]]).strip()
                        if re.fullmatch(r"\d{8}", raw_date):
                            dt = pd.to_datetime(raw_date, format="%Y%m%d", errors="raise")
                        else:
                            dt = pd.Timestamp(raw_date)
                        if dt < left or dt > right:
                            continue
                        vals = [float(str(raw[names[c]]).replace(",", ""))
                                for c in ("open", "high", "low", "close", "volume")]
                        if any(pd.isna(vals)):
                            raise ValueError("missing")
                        rows.append([dt, code, *vals])
                    except Exception:
                        skipped += 1
                if rows:
                    d = pd.DataFrame(rows, columns=["date", "code", "open", "high", "low", "close", "volume"])
                    d["trading_money"] = d.close * d.volume
                    d["trades"] = pd.NA
                    d["price_layer"] = "raw_execution"
                    frames.append(d)
                    accepted += len(d)
        except (UnicodeDecodeError, csv.Error):
            skipped += 1
    raw = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if len(raw):
        raw = raw.sort_values(["date", "code"]).drop_duplicates(["date", "code"], keep="last")
    return raw, {"source_files_scanned": scanned, "rows_accepted": accepted,
                 "rows_skipped": skipped}


def build_universe(raw: pd.DataFrame, master: pd.DataFrame, top_n: int,
                   min_price: float, min_history: int) -> pd.DataFrame:
    if raw.empty:
        return pd.DataFrame()
    d = raw.sort_values(["code", "date"]).copy()
    g = d.groupby("code", group_keys=False)
    d["sessions_observed"] = g.cumcount() + 1
    d["avg_money_20d"] = g.trading_money.transform(
        lambda x: x.rolling(20, min_periods=20).mean()
    )
    d["median_money_60d"] = g.trading_money.transform(
        lambda x: x.rolling(60, min_periods=40).median()
    )
    d = d.merge(master[["stock_id", "stock_name", "type", "industry_category",
                        "delisting_date"]], left_on="code", right_on="stock_id", how="left")
    d["delisting_date"] = pd.to_datetime(d.delisting_date, errors="coerce")
    d["listed_and_trading"] = d.delisting_date.isna() | (d.date < d.delisting_date)
    d["indicator_ready"] = d.sessions_observed >= min_history
    d["price_filter"] = d.close >= min_price
    d["liquidity_ready"] = d.avg_money_20d.notna()
    d["base_eligible"] = d[["listed_and_trading", "indicator_ready", "price_filter",
                             "liquidity_ready"]].all(axis=1)
    d["liquidity_rank"] = d.where(d.base_eligible).groupby("date")["avg_money_20d"].rank(
        ascending=False, method="first"
    )
    d["alpha_universe"] = d.base_eligible & d.liquidity_rank.le(top_n)
    cols = ["date", "code", "stock_name", "type", "industry_category",
            "open", "high", "low", "close",
            "volume", "trading_money", "sessions_observed", "avg_money_20d",
            "median_money_60d", "listed_and_trading", "indicator_ready",
            "price_filter", "liquidity_ready", "base_eligible", "liquidity_rank",
            "alpha_universe", "delisting_date"]
    return d[cols].sort_values(["date", "code"])


def qc(raw: pd.DataFrame, adj: pd.DataFrame, universe: pd.DataFrame,
       master: pd.DataFrame, log: pd.DataFrame) -> dict:
    dup_raw = int(raw.duplicated(["date", "code"]).sum()) if len(raw) else 0
    bad_ohlc = int(((raw.low > raw.high) | (raw.open < raw.low) |
                    (raw.open > raw.high) | (raw.close < raw.low) |
                    (raw.close > raw.high)).sum()) if len(raw) else 0
    common = raw[["date", "code"]].merge(adj[["date", "code"]], how="inner") if len(adj) else pd.DataFrame()
    fails = int(log.raw_status.eq("FAIL").sum() + log.adjusted_status.eq("FAIL").sum()) if len(log) else 0
    status = "PASS" if len(raw) and dup_raw == 0 and bad_ohlc == 0 and fails == 0 else "FAIL"
    return {
        "version": "V4.12-E50-A0",
        "status": status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "master_rows": int(len(master)),
        "raw_rows": int(len(raw)),
        "adjusted_rows": int(len(adj)),
        "raw_adjusted_common_keys": int(len(common)),
        "universe_rows": int(len(universe)),
        "universe_dates": int(universe.date.nunique()) if len(universe) else 0,
        "universe_codes": int(universe.code.nunique()) if len(universe) else 0,
        "alpha_eligible_rows": int(universe.alpha_universe.sum()) if len(universe) else 0,
        "duplicate_raw_keys": dup_raw,
        "invalid_ohlc_rows": bad_ohlc,
        "failed_downloads": fails,
        "execution_price_layer": "raw only",
        "ranking_price_layer": "adjusted only; never execution",
        "survivor_policy": "retain delisted securities and infer first tradable date from first raw observation",
        "known_limitations": [
            "Full-market free API requires per-security requests; completeness depends on shard manifest.",
            "FinMind stock master is a current snapshot; historical industry changes are not reconstructed.",
            "Listing eligibility is conservatively inferred from observed price history unless an official listing date is available.",
            "Monthly revenue release timestamps before 2026-04-21 require a separate causal-date policy in E50-A1.",
        ],
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="e50a0_data")
    p.add_argument("--start", default="2010-01-01")
    p.add_argument("--end", default=date.today().isoformat())
    p.add_argument("--token", default=os.environ.get("FINMIND_TOKEN", ""))
    p.add_argument("--limit", type=int, default=0, help="0 fetches every selected current security")
    p.add_argument("--codes", default="", help="comma-separated smoke-test or targeted codes")
    p.add_argument("--top-n", type=int, default=150)
    p.add_argument("--min-price", type=float, default=10.0)
    p.add_argument("--min-history", type=int, default=252)
    p.add_argument("--input-dir", type=Path,
                   help="Extracted all-market daily archives; bypasses per-security price API")
    a = p.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    info = pd.DataFrame(api_get("TaiwanStockInfo", token=a.token))
    delisted = pd.DataFrame(api_get("TaiwanStockDelisting", token=a.token))
    calendar = pd.DataFrame(api_get("TaiwanStockTradingDate", token=a.token))
    master = canonical_master(info, delisted)
    write_csv(master, out / "security_master.csv")
    write_csv(delisted, out / "delistings.csv")
    write_csv(calendar, out / "trading_calendar.csv")

    codes = [x.strip() for x in a.codes.split(",") if re.fullmatch(r"\d{4}", x.strip())]
    archive_meta = {}
    if a.input_dir:
        raw, archive_meta = load_archive_market(a.input_dir, a.start, a.end)
        adj = pd.DataFrame()
        log = pd.DataFrame([{"code": "ALL_MARKET_ARCHIVE", "raw_status": "PASS",
                             "raw_rows": len(raw), "adjusted_status": "PENDING_E50_A1"}])
    else:
        log = fetch_shards(master, out, start=a.start, end=a.end, token=a.token,
                           limit=a.limit, codes=codes)
        raw = load_shards(out / "shards" / "raw")
        adj = load_shards(out / "shards" / "adjusted")
    write_csv(log, out / "download_manifest.csv")
    universe = build_universe(raw, master, a.top_n, a.min_price, a.min_history)
    write_csv(universe, out / "point_in_time_universe.csv")

    status = qc(raw, adj, universe, master, log)
    status["archive_ingestion"] = archive_meta
    files = [out / "security_master.csv", out / "delistings.csv",
             out / "trading_calendar.csv", out / "download_manifest.csv",
             out / "point_in_time_universe.csv"]
    status["files"] = {str(x.relative_to(out)): {"bytes": x.stat().st_size,
                                                   "sha256": sha256(x)}
                       for x in files if x.exists()}
    (out / "qc_status.json").write_text(
        json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(status, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
