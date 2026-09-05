#!/usr/bin/env python3
"""TAIEX fetch with optional Yahoo failover — OPS tool (default FinMind).

Default: FinMind TaiwanStockPrice / TAIEX only.
Optional: --enable-yahoo-failover uses Yahoo ^TWII if FinMind fails
          --force-yahoo uses Yahoo only (probe).

Never writes forward/e21. Soft-Frozen unchanged.
"""
from __future__ import annotations

import argparse
import json
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FINMIND = "https://api.finmindtrade.com/api/v4/data"
DEFAULT_OUT = ROOT / "repro/data-source-phase-c/taiex_failover_probe.csv"


def fetch_finmind_taiex(start: str, end: str | None = None) -> pd.DataFrame:
    end = end or date.today().isoformat()
    q = {
        "dataset": "TaiwanStockPrice",
        "data_id": "TAIEX",
        "start_date": start,
        "end_date": end,
    }
    req = urllib.request.Request(
        FINMIND + "?" + urllib.parse.urlencode(q),
        headers={"User-Agent": "v412d-taiex-failover/1.0"},
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        obj = json.load(r)
    if obj.get("status") != 200:
        raise RuntimeError(f"FinMind TAIEX status={obj.get('status')} msg={obj.get('msg')}")
    rows = obj.get("data") or []
    if not rows:
        raise RuntimeError("FinMind TAIEX empty")
    d = pd.DataFrame(rows)
    d["date"] = pd.to_datetime(d["date"]).dt.strftime("%Y-%m-%d")
    d["close"] = pd.to_numeric(d["close"], errors="coerce")
    out = d[["date", "close"]].dropna().sort_values("date")
    out["source"] = "finmind_TAIEX"
    return out


def fetch_yahoo_twii(start: str) -> pd.DataFrame:
    import yfinance as yf

    d = yf.download("^TWII", start=start, auto_adjust=False, progress=False, threads=False)
    if d is None or d.empty:
        raise RuntimeError("Yahoo ^TWII empty")
    if isinstance(d.columns, pd.MultiIndex):
        d.columns = d.columns.get_level_values(0)
    out = d.reset_index().rename(columns={"Date": "date", "Close": "close"})
    out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
    out["close"] = pd.to_numeric(out["close"], errors="coerce")
    out = out[["date", "close"]].dropna().sort_values("date")
    out["source"] = "yahoo_^TWII"
    return out


def fetch_taiex(
    start: str,
    *,
    enable_yahoo_failover: bool = False,
    force_yahoo: bool = False,
) -> tuple[pd.DataFrame, dict]:
    meta: dict = {
        "start": start,
        "enable_yahoo_failover": enable_yahoo_failover,
        "force_yahoo": force_yahoo,
        "primary_attempt": None,
        "failover_used": False,
        "source": None,
        "error_primary": None,
    }
    if force_yahoo:
        df = fetch_yahoo_twii(start)
        meta["primary_attempt"] = "yahoo_forced"
        meta["source"] = "yahoo_^TWII"
        return df, meta

    try:
        df = fetch_finmind_taiex(start)
        meta["primary_attempt"] = "finmind"
        meta["source"] = "finmind_TAIEX"
        return df, meta
    except Exception as ex:  # noqa: BLE001
        meta["primary_attempt"] = "finmind"
        meta["error_primary"] = f"{type(ex).__name__}:{ex}"
        if not enable_yahoo_failover:
            raise
        df = fetch_yahoo_twii(start)
        meta["failover_used"] = True
        meta["source"] = "yahoo_^TWII"
        return df, meta


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2020-01-01")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument(
        "--enable-yahoo-failover",
        action="store_true",
        help="If FinMind fails, fall back to Yahoo ^TWII (opt-in).",
    )
    ap.add_argument(
        "--force-yahoo",
        action="store_true",
        help="Probe Yahoo path only (does not change e21 defaults).",
    )
    ap.add_argument(
        "--simulate-finmind-fail",
        action="store_true",
        help="Force primary failure to demonstrate failover (requires --enable-yahoo-failover).",
    )
    args = ap.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)

    if args.simulate_finmind_fail:
        if not args.enable_yahoo_failover:
            raise SystemExit("--simulate-finmind-fail requires --enable-yahoo-failover")
        # Monkey-patch primary to fail
        global fetch_finmind_taiex

        def _boom(*_a, **_k):
            raise RuntimeError("simulated_finmind_failure")

        fetch_finmind_taiex = _boom  # type: ignore

    df, meta = fetch_taiex(
        args.start,
        enable_yahoo_failover=args.enable_yahoo_failover,
        force_yahoo=args.force_yahoo,
    )
    df.to_csv(args.out, index=False)
    meta.update(
        {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "n_rows": int(len(df)),
            "out": str(args.out.relative_to(ROOT)) if args.out.is_relative_to(ROOT) else str(args.out),
            "soft_frozen_unchanged": True,
            "e21_default_unchanged": True,
            "note": "Opt-in tool only; e21 forward does not auto-call this without human wiring PR",
        }
    )
    meta_path = args.out.with_suffix(".meta.json")
    meta_path.write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps(meta, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
