#!/usr/bin/env python3
"""Refresh ``data/market/private_fin_adjusted.csv`` tip from FinMind TaiwanStockPrice.

Research / Class D hygiene — extends PRIV (+ R2 bank) rows past the last panel date
using the last known ``backward_adjustment_factor``. Does **not** rewrite Soft-Frozen
``forward/e21/live_market.csv``.

Used so Class D FinPriv fail-closed freshness (lag ≤ 5d) stays green on live asof.

Usage:
  PYTHONPATH=scripts python3 scripts/private_fin_adj_tip_refresh.py
  PYTHONPATH=scripts python3 scripts/private_fin_adj_tip_refresh.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ADJ = ROOT / "data/market/private_fin_adjusted.csv"
STATUS = ROOT / "data/dividend_events/e22_private_fin_tip_refresh_status.json"
PRIV_R3R4 = ["2884", "2885", "2890", "2891", "2881", "2882"]
BANKS_R2 = ["2801", "2834"]
FILL_CODES = PRIV_R3R4 + BANKS_R2
FINMIND = "https://api.finmindtrade.com/api/v4/data"


def _finmind_headers() -> dict[str, str]:
    import os

    headers = {"User-Agent": "v412-private-fin-tip-refresh/1.0"}
    token = (os.environ.get("FINMIND_TOKEN") or "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def finmind_price(sid: str, start: str) -> list[dict]:
    q = {
        "dataset": "TaiwanStockPrice",
        "data_id": sid,
        "start_date": start,
        "end_date": date.today().isoformat(),
    }
    req = urllib.request.Request(
        FINMIND + "?" + urllib.parse.urlencode(q),
        headers=_finmind_headers(),
    )
    with urllib.request.urlopen(req, timeout=120) as response:
        payload = json.load(response)
    if payload.get("status") != 200:
        raise RuntimeError(f"FinMind TaiwanStockPrice {sid}: {payload}")
    return payload.get("data") or []


def refresh(*, dry_run: bool = False, sleep_s: float = 0.35) -> dict:
    if not ADJ.exists():
        raise SystemExit(f"missing {ADJ}")
    adj = pd.read_csv(ADJ, dtype={"code": str})
    adj["date"] = pd.to_datetime(adj["date"])
    last = adj.sort_values("date").groupby("code", sort=False).tail(1).set_index("code")
    new_rows: list[dict] = []
    for i, code in enumerate(FILL_CODES, 1):
        if code not in last.index:
            print(f"skip missing panel code {code}", flush=True)
            continue
        dmax = pd.Timestamp(last.loc[code, "date"]).normalize()
        start = (dmax + pd.Timedelta(days=1)).date().isoformat()
        factor = float(last.loc[code, "backward_adjustment_factor"])
        print(f"[{i}/{len(FILL_CODES)}] {code} from {start} factor={factor}", flush=True)
        rows = finmind_price(code, start)
        for r in rows:
            d = str(r["date"])
            if pd.Timestamp(d) <= dmax:
                continue
            o, h, lo, c = float(r["open"]), float(r["max"]), float(r["min"]), float(r["close"])
            new_rows.append(
                {
                    "code": code,
                    "date": d,
                    "adjusted_open": o * factor,
                    "adjusted_high": h * factor,
                    "adjusted_low": lo * factor,
                    "adjusted_close": c * factor,
                    "volume": r.get("Trading_Volume", ""),
                    "backward_adjustment_factor": factor,
                    "raw_close": c,
                }
            )
        time.sleep(float(sleep_s))

    status = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "PRIVATE_FIN_ADJ_TIP_REFRESH_FINMIND",
        "new_rows": len(new_rows),
        "codes": FILL_CODES,
        "dry_run": bool(dry_run),
        "adj_path": str(ADJ.relative_to(ROOT)),
    }
    if new_rows and not dry_run:
        add = pd.DataFrame(new_rows)
        add["date"] = pd.to_datetime(add["date"])
        out = pd.concat([adj, add], ignore_index=True)
        out = out.sort_values(["date", "code"]).drop_duplicates(["date", "code"], keep="last")
        out["date"] = out["date"].dt.strftime("%Y-%m-%d")
        out.to_csv(ADJ, index=False)
        status["written"] = True
        status["max_date_by_code"] = (
            out.groupby("code")["date"].max().to_dict()
        )
    else:
        status["written"] = False
        status["max_date_by_code"] = (
            adj.assign(date=adj["date"].dt.strftime("%Y-%m-%d"))
            .groupby("code")["date"]
            .max()
            .to_dict()
        )
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(status, indent=2))
    return status


def main() -> int:
    ap = argparse.ArgumentParser(description="Refresh private_fin_adjusted tip via FinMind")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--sleep", type=float, default=0.35)
    args = ap.parse_args()
    refresh(dry_run=bool(args.dry_run), sleep_s=float(args.sleep))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
