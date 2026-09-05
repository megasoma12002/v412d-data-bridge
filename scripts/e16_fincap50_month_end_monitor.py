#!/usr/bin/env python3
"""FIN_CAP_50 month-end dual-paper monitor (ops review — not live).

Compares BASE_E16 vs FIN_CAP_50 paper NAVs at month-end (or as-of date).
Does NOT change Soft-Frozen clips. Does NOT place orders.

Inputs (from dual-paper harness):
  repro/fincap50-dual-paper/outputs/base_e16_daily_nav.csv
  repro/fincap50-dual-paper/outputs/fincap50_daily_nav.csv

Optional: re-run `scripts/e16_fincap50_dual_paper_ledgers.py` first to refresh.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "repro/fincap50-dual-paper/month_end"
BASE_NAV = ROOT / "repro/fincap50-dual-paper/outputs/base_e16_daily_nav.csv"
CAP_NAV = ROOT / "repro/fincap50-dual-paper/outputs/fincap50_daily_nav.csv"
RESEARCH = ROOT / "research/gaps"


def _load(path: Path) -> pd.DataFrame:
    d = pd.read_csv(path)
    d["date"] = pd.to_datetime(d["date"])
    return d.sort_values("date").reset_index(drop=True)


def _stats(nav: pd.Series) -> dict:
    r = nav.pct_change().dropna()
    if len(nav) < 2:
        return {"cagr": None, "max_drawdown": None, "vol": None, "n_days": int(len(nav))}
    years = len(r) / 252.0
    cagr = (
        float((nav.iloc[-1] / nav.iloc[0]) ** (1 / years) - 1)
        if years > 0 and nav.iloc[0] > 0
        else None
    )
    peak = nav.cummax()
    mdd = float((nav / peak - 1.0).min())
    vol = float(r.std(ddof=1) * np.sqrt(252)) if len(r) > 2 else None
    return {"cagr": cagr, "max_drawdown": mdd, "vol": vol, "n_days": int(len(nav))}


def _pct(x: float | None) -> str:
    """Format a ratio; treat only None as missing (0.0 is a valid MDD/CAGR)."""
    if x is None:
        return "n/a"
    return f"{x:.2%}"


def _abs_or(x: float | None, default: float) -> float:
    """abs(x) with None→default; do not treat 0.0 as missing via `or`."""
    return abs(default if x is None else x)


def _window(df: pd.DataFrame, start, end) -> pd.DataFrame:
    m = (df["date"] >= start) & (df["date"] <= end)
    return df.loc[m].reset_index(drop=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--asof", default=None, help="YYYY-MM-DD (default: last NAV date)")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    if not BASE_NAV.exists() or not CAP_NAV.exists():
        raise SystemExit(
            "Missing dual-paper NAVs. Run scripts/e16_fincap50_dual_paper_ledgers.py first."
        )

    base = _load(BASE_NAV)
    cap = _load(CAP_NAV)
    asof = pd.Timestamp(args.asof) if args.asof else min(base["date"].max(), cap["date"].max())
    base = base[base["date"] <= asof]
    cap = cap[cap["date"] <= asof]

    month_start = pd.Timestamp(asof.year, asof.month, 1)
    windows = {
        "mtd": (month_start, asof),
        "ytd": (pd.Timestamp(asof.year, 1, 1), asof),
        "trailing_1y": (asof - pd.Timedelta(days=365), asof),
        "heldout_2019_plus": (pd.Timestamp("2019-01-01"), asof),
        "full": (base["date"].min(), asof),
    }

    rows = []
    for wname, (ws, we) in windows.items():
        b = _window(base, ws, we)
        c = _window(cap, ws, we)
        if len(b) < 2 or len(c) < 2:
            continue
        bnav = b["nav"] / float(b["nav"].iloc[0])
        cnav = c["nav"] / float(c["nav"].iloc[0])
        sb, sc = _stats(bnav), _stats(cnav)
        mdd_improve_pp = (_abs_or(sb["max_drawdown"], 9.0) - _abs_or(sc["max_drawdown"], 9.0)) * 100
        base_cagr = 0.0 if sb["cagr"] is None else sb["cagr"]
        cap_cagr = 0.0 if sc["cagr"] is None else sc["cagr"]
        cagr_giveback_pp = (base_cagr - cap_cagr) * 100
        rows.append(
            {
                "window": wname,
                "start": str(pd.Timestamp(ws).date()),
                "end": str(pd.Timestamp(we).date()),
                "base_cagr": sb["cagr"],
                "base_mdd": sb["max_drawdown"],
                "fincap50_cagr": sc["cagr"],
                "fincap50_mdd": sc["max_drawdown"],
                "mdd_improve_pp": mdd_improve_pp,
                "cagr_giveback_pp": cagr_giveback_pp,
                "rel_nav_end": float(cnav.iloc[-1] / bnav.iloc[-1]),
            }
        )

    held = next((r for r in rows if r["window"] == "heldout_2019_plus"), None)
    alerts = []
    if held:
        if held["mdd_improve_pp"] < 0:
            alerts.append("ALERT: FIN_CAP_50 held-out MDD worse than BASE (paper)")
        if held["cagr_giveback_pp"] > 3.0:
            alerts.append("ALERT: FIN_CAP_50 held-out CAGR giveback > 3.0 pp (paper)")
        if held["cagr_giveback_pp"] > 5.0:
            alerts.append("PAUSE_REVIEW: giveback > 5 pp — do not advance cutover discussion")

    args.out.mkdir(parents=True, exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "asof": str(asof.date()),
        "live_wire": False,
        "soft_frozen_default_unchanged": True,
        "label": "FIN_CAP_50_MONTH_END_PAPER_MONITOR",
        "windows": rows,
        "alerts": alerts,
        "cutover_blocked": any("PAUSE_REVIEW" in a for a in alerts),
        "note": "Paper monitor only. Soft-Frozen Financial clip remains [0.50,0.95].",
    }
    (args.out / "month_end_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    pd.DataFrame(rows).to_csv(args.out / "month_end_windows.csv", index=False)

    lines = [
        f"# FIN_CAP_50 Month-End Paper Monitor — asof {asof.date()}",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        "Status: **PAPER ONLY** — Soft-Frozen live default unchanged.",
        "",
        "| Window | BASE CAGR | BASE MDD | FIN_CAP_50 CAGR | FIN_CAP_50 MDD | MDD Δpp | CAGR giveback pp | Rel NAV |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['window']} | {_pct(r['base_cagr'])} | {_pct(r['base_mdd'])} | "
            f"{_pct(r['fincap50_cagr'])} | {_pct(r['fincap50_mdd'])} | "
            f"{r['mdd_improve_pp']:+.2f} | {r['cagr_giveback_pp']:+.2f} | {r['rel_nav_end']:.4f} |"
        )
    lines += ["", "## Alerts", ""]
    if alerts:
        for a in alerts:
            lines.append(f"- {a}")
    else:
        lines.append("- None")
    lines += [
        "",
        "## Ops note",
        "",
        "- Refresh NAVs: `python3 scripts/e16_fincap50_dual_paper_ledgers.py`",
        "- Re-run monitor: `python3 scripts/e16_fincap50_month_end_monitor.py`",
        "- Cutover still requires a **separate human PR**; this monitor never flips Soft-Frozen.",
        "",
    ]
    md = "\n".join(lines)
    (args.out / "MONTH_END_MONITOR.md").write_text(md)
    (RESEARCH / "FIN_CAP_50_MONTH_END_MONITOR.md").write_text(md)
    (RESEARCH / "FIN_CAP_50_MONTH_END_MONITOR.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"asof": summary["asof"], "alerts": alerts, "n_windows": len(rows)}, indent=2))
    print("EXIT:0")


if __name__ == "__main__":
    main()
