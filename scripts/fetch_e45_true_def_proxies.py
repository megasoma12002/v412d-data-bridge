#!/usr/bin/env python3
"""Fetch true DEF proxies for E45 M2 v1 research (cash / short-duration / gov-bond).

Honesty:
  - TW bond ETFs (FinMind) are TWD-native duration proxies but list late (2017+).
  - USD BIL/SHY (Yahoo) give long history but need FX; not a TWD cash yield.
  - Does NOT merge into forward/e21/live_market.csv.
  - Does NOT open Soft-Frozen / DEFAULT / stitch / observe.

Side effects only under __main__.
"""
from __future__ import annotations

import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "def_proxies"
START = "2010-01-01"

# Primary TWD DEF candidates (gov / investment-grade bond ETFs on TWSE).
TW_BOND_ETFS = {
    "00679B": "Yuanta 20Y US IG (TW wrapper) — long duration, not cash",
    "00687B": "Cathay 20Y US bond (TW wrapper) — long duration, not cash",
    "00719B": "Yuanta 1-3Y US bond (TW wrapper) — short-duration candidate",
}

# USD cash / short-duration references (Yahoo); require FX join for TWD books.
USD_CASH_LIKE = {
    "BIL": "BIL",  # 1-3m T-bills
    "SHY": "SHY",  # 1-3y Treasuries
}


def main() -> None:
    import pandas as pd
    import requests
    import yfinance as yf

    OUT.mkdir(parents=True, exist_ok=True)
    qc: dict = {"start": START, "out": str(OUT.relative_to(REPO))}
    diagnostics: dict = {}
    frames: list[pd.DataFrame] = []

    def finmind_tw(code: str) -> pd.DataFrame:
        url = "https://api.finmindtrade.com/api/v4/data"
        r = requests.get(
            url,
            params={"dataset": "TaiwanStockPrice", "data_id": code, "start_date": START},
            timeout=120,
        )
        r.raise_for_status()
        payload = r.json()
        rows = payload.get("data") or []
        if not rows:
            raise RuntimeError(f"FinMind empty: status={payload.get('status')} msg={payload.get('msg')}")
        d = pd.DataFrame(rows).rename(
            columns={"max": "high", "min": "low", "Trading_Volume": "volume", "stock_id": "code"}
        )
        d["date"] = pd.to_datetime(d["date"]).dt.strftime("%Y-%m-%d")
        for c in ["open", "high", "low", "close", "volume"]:
            d[c] = pd.to_numeric(d[c], errors="coerce")
        d["code"] = code
        d["adj_close"] = d["close"]
        d["source"] = "FinMind TaiwanStockPrice"
        d["source_symbol"] = code
        d["currency"] = "TWD"
        d["proxy_class"] = "tw_bond_etf"
        return d[
            [
                "date",
                "code",
                "open",
                "high",
                "low",
                "close",
                "adj_close",
                "volume",
                "source",
                "source_symbol",
                "currency",
                "proxy_class",
            ]
        ].sort_values("date").drop_duplicates("date", keep="last")

    def yahoo_ohlc(code: str, ticker: str, proxy_class: str, currency: str) -> pd.DataFrame:
        raw = yf.download(
            ticker,
            start=START,
            auto_adjust=False,
            progress=False,
            threads=False,
            timeout=60,
        )
        if raw.empty:
            raise RuntimeError(f"Yahoo empty for {ticker}")
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.get_level_values(0)
        d = raw.reset_index().rename(
            columns={
                "Date": "date",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Adj Close": "adj_close",
                "Volume": "volume",
            }
        )
        d["date"] = pd.to_datetime(d["date"]).dt.strftime("%Y-%m-%d")
        for c in ["open", "high", "low", "close", "adj_close", "volume"]:
            d[c] = pd.to_numeric(d[c], errors="coerce")
        d["code"] = code
        d["source"] = "Yahoo Finance"
        d["source_symbol"] = ticker
        d["currency"] = currency
        d["proxy_class"] = proxy_class
        return d[
            [
                "date",
                "code",
                "open",
                "high",
                "low",
                "close",
                "adj_close",
                "volume",
                "source",
                "source_symbol",
                "currency",
                "proxy_class",
            ]
        ].sort_values("date").drop_duplicates("date", keep="last")

    def finmind_usd_twd() -> pd.DataFrame:
        url = "https://api.finmindtrade.com/api/v4/data"
        r = requests.get(
            url,
            params={"dataset": "TaiwanExchangeRate", "data_id": "USD", "start_date": START},
            timeout=120,
        )
        r.raise_for_status()
        payload = r.json()
        rows = payload.get("data") or []
        if not rows:
            raise RuntimeError(f"FinMind FX empty: {payload.get('msg')}")
        d = pd.DataFrame(rows)
        d["date"] = pd.to_datetime(d["date"]).dt.strftime("%Y-%m-%d")
        for c in ["cash_buy", "cash_sell", "spot_buy", "spot_sell"]:
            d[c] = pd.to_numeric(d[c], errors="coerce")
        # Mid of spot for research join (not a tradable fill).
        d["usdtwd_mid"] = (d["spot_buy"] + d["spot_sell"]) / 2.0
        d["source"] = "FinMind TaiwanExchangeRate"
        return d[["date", "cash_buy", "cash_sell", "spot_buy", "spot_sell", "usdtwd_mid", "source"]].sort_values(
            "date"
        ).drop_duplicates("date", keep="last")

    # --- TW bond ETFs ---
    for code, note in TW_BOND_ETFS.items():
        errors: list[str] = []
        try:
            d = finmind_tw(code)
            path = OUT / f"{code}_ohlcv.csv"
            d.to_csv(path, index=False)
            frames.append(d)
            qc[code] = {
                "pass": bool(len(d) > 500 and d["close"].notna().all()),
                "rows": int(len(d)),
                "first_date": str(d["date"].min()),
                "last_date": str(d["date"].max()),
                "currency": "TWD",
                "proxy_class": "tw_bond_etf",
                "note": note,
                "path": str(path.relative_to(REPO)),
            }
            diagnostics[code] = {"errors": errors, "selected_source": "FinMind"}
        except Exception as e:
            errors.append(repr(e))
            qc[code] = {"pass": False, "rows": 0, "errors": errors}
            diagnostics[code] = {"errors": errors}

    # --- USD cash-like ---
    for code, ticker in USD_CASH_LIKE.items():
        errors = []
        try:
            d = yahoo_ohlc(code, ticker, proxy_class="usd_cash_like", currency="USD")
            path = OUT / f"{code}_ohlcv.csv"
            d.to_csv(path, index=False)
            frames.append(d)
            qc[code] = {
                "pass": bool(len(d) > 2000 and d["adj_close"].notna().all()),
                "rows": int(len(d)),
                "first_date": str(d["date"].min()),
                "last_date": str(d["date"].max()),
                "currency": "USD",
                "proxy_class": "usd_cash_like",
                "path": str(path.relative_to(REPO)),
            }
            diagnostics[code] = {"errors": errors, "selected_source": "Yahoo"}
        except Exception as e:
            errors.append(repr(e))
            qc[code] = {"pass": False, "rows": 0, "errors": errors}
            diagnostics[code] = {"errors": errors}

    # --- FX ---
    try:
        fx = finmind_usd_twd()
        fx_path = OUT / "USDTWD_finmind.csv"
        fx.to_csv(fx_path, index=False)
        qc["USDTWD"] = {
            "pass": bool(len(fx) > 2000 and fx["usdtwd_mid"].notna().all()),
            "rows": int(len(fx)),
            "first_date": str(fx["date"].min()),
            "last_date": str(fx["date"].max()),
            "path": str(fx_path.relative_to(REPO)),
            "note": "spot mid = (spot_buy+spot_sell)/2; research join only",
        }
        diagnostics["USDTWD"] = {"selected_source": "FinMind TaiwanExchangeRate"}
    except Exception as e:
        qc["USDTWD"] = {"pass": False, "errors": [repr(e)]}
        diagnostics["USDTWD"] = {"errors": [repr(e)]}

    if frames:
        combined = pd.concat(frames, ignore_index=True).sort_values(["date", "code"])
        cpath = OUT / "def_proxies_combined_ohlcv.csv"
        combined.to_csv(cpath, index=False)
        qc["combined"] = {
            "rows": int(len(combined)),
            "codes": sorted(combined["code"].astype(str).unique().tolist()),
            "path": str(cpath.relative_to(REPO)),
        }
    else:
        qc["combined"] = {"rows": 0, "codes": []}

    primary_ok = all(qc.get(c, {}).get("pass") for c in ["00719B", "BIL", "SHY", "USDTWD"])
    qc["overall_pass"] = bool(primary_ok)
    qc["honesty"] = {
        "not_merged_into_live_market": True,
        "tw_bond_listing_lag": "00679B/00687B/00719B start 2017–2018; pre-list = no TWD bond DEF",
        "usd_proxies_need_fx": True,
        "00679B_00687B_are_long_duration": True,
        "preferred_short_duration_twd": "00719B",
        "preferred_cash_like_usd": "BIL",
        "def_tel_still_equity_proxy": True,
    }

    (OUT / "qc_summary.json").write_text(json.dumps(qc, indent=2, ensure_ascii=False) + "\n")
    (OUT / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, ensure_ascii=False) + "\n")
    (OUT / "README.md").write_text(
        "# E45 true DEF proxies (research ingest)\n\n"
        "Fetched by `scripts/fetch_e45_true_def_proxies.py`.\n\n"
        "- **TWD bond ETFs** (`00679B`, `00687B`, `00719B`): FinMind `TaiwanStockPrice`.\n"
        "- **USD cash-like** (`BIL`, `SHY`): Yahoo Finance.\n"
        "- **FX** (`USDTWD_finmind.csv`): FinMind `TaiwanExchangeRate` USD spot mid.\n\n"
        "Do **not** merge into `forward/e21/live_market.csv` without a dedicated paper pack + freeze.\n"
        "Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN.\n"
    )
    print(json.dumps(qc, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
