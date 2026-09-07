#!/usr/bin/env python3
"""Authorized live ledger replay — clears forward/e21 books and rebuilds day-by-day.

Human authorization required: --confirm-history-rewrite
Keeps live_market.csv. Rebuilds signals/orders/fills/nav/audit/portfolio_state/qc.
Soft-Frozen clip unchanged. Does not stitch / cutover.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / "forward/e21"
KEEP = {"live_market.csv"}
CLEAR = [
    "fills.csv",
    "orders.csv",
    "signals.csv",
    "nav.csv",
    "audit_chain.jsonl",
    "portfolio_state.json",
    "qc_status.json",
    "pipeline_t1_audit.json",
    "dividends_applied.csv",
    "E21_forward_dashboard.xlsx",
]


def main() -> int:
    ap = argparse.ArgumentParser(description="Replay forward/e21 ledgers (authorized rewrite)")
    ap.add_argument(
        "--confirm-history-rewrite",
        action="store_true",
        help="Required. Human authorized clearing historical live fills/NAV and replaying.",
    )
    ap.add_argument("--start-date", default="2026-08-24")
    sys.path.insert(0, str(ROOT / "scripts"))
    from portfolio_capital import DEFAULT_CAPITAL

    ap.add_argument("--capital", type=float, default=DEFAULT_CAPITAL)
    a = ap.parse_args()
    if not a.confirm_history_rewrite:
        raise SystemExit("Refusing replay without --confirm-history-rewrite")

    market = pd.read_csv(LIVE / "live_market.csv", dtype={"code": str})
    market["date"] = pd.to_datetime(market["date"])
    from e16_soft_frozen_base import FIN, TEL

    required = set(FIN + TEL + ["0050", "TAIEX"])
    available = market.groupby("date").code.apply(lambda x: required.issubset(set(x)))
    common = available[available].index
    dates = sorted(
        d.date().isoformat() for d in common if d >= pd.Timestamp(a.start_date)
    )
    if not dates:
        raise SystemExit("no complete trading dates to replay")

    cleared = []
    for name in CLEAR:
        p = LIVE / name
        if p.exists():
            p.unlink()
            cleared.append(name)

    note = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "E21_LIVE_TEL_ETF_FLOOR_10_REPLAY",
        "authority": "human ACCEPT 「電信 0050下限 10%」 2026-09-07",
        "cleared": cleared,
        "kept": sorted(KEEP),
        "start_date": a.start_date,
        "capital": float(a.capital),
        "board_lot": 1000,
        "soft_frozen_fin_clip": [0.50, 0.95],
        "soft_frozen_tel_clip": [0.10, 0.35],
        "soft_frozen_etf_clip": [0.10, 0.35],
        "soft_frozen_unchanged": False,
        "stitch_authorized": False,
        "prior_authority": "capital 15M + board-lot 1000 2026-09-07",
        "note": "Soft-Frozen TEL+0050 floors → 10%; see research/ops/SOFT_FROZEN_TEL_ETF_FLOOR_10_2026-09-07.md",
    }
    (LIVE / "REPLAY_AUTHORITY.json").write_text(json.dumps(note, indent=2) + "\n")

    replayed = []
    for d in dates:
        cmd = [
            sys.executable,
            str(ROOT / "scripts/e21_forward_pipeline.py"),
            "--market",
            "forward/e21/live_market.csv",
            "--state-dir",
            "forward/e21",
            "--capital",
            str(a.capital),
            "--asof",
            d,
        ]
        print(f"==> replay {d}", flush=True)
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        if proc.returncode != 0:
            sys.stderr.write(proc.stdout[-2000:] + "\n" + proc.stderr[-2000:] + "\n")
            raise SystemExit(f"pipeline failed on {d} exit={proc.returncode}")
        replayed.append(d)

    qc = subprocess.run(
        [sys.executable, str(ROOT / "scripts/e21_qc.py"), "--state-dir", "forward/e21"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    print(qc.stdout)
    if qc.returncode != 0:
        raise SystemExit("e21_qc FAIL after replay")

    gap = subprocess.run(
        [sys.executable, str(ROOT / "scripts/e22_gap6_fidelity_kpi.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    print(gap.stdout[-1500:])
    if gap.returncode != 0:
        raise SystemExit("gap6 FAIL after replay")

    note["replayed_dates"] = replayed
    note["qc_ok"] = True
    note["gap6_ok"] = True
    (LIVE / "REPLAY_AUTHORITY.json").write_text(json.dumps(note, indent=2) + "\n")
    print(json.dumps({"status": "OK", "n_days": len(replayed), "last": replayed[-1] if replayed else None}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
