#!/usr/bin/env python3
"""BLEND_025 month-end dual-paper monitor (ops observe — not live).

Compares BASE_E16 vs BLEND_025 paper NAVs at month-end (or as-of date).
Does NOT change Soft-Frozen clips. Does NOT place orders. Cutover always blocked.

Inputs (from dual-paper harness):
  repro/blend025-dual-paper/outputs/base_e16_daily_nav.csv
  repro/blend025-dual-paper/outputs/blend025_daily_nav.csv

Optional: re-run `scripts/e16_blend025_dual_paper_ledgers.py` first to refresh.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "repro/blend025-dual-paper/month_end"
BASE_NAV = ROOT / "repro/blend025-dual-paper/outputs/base_e16_daily_nav.csv"
BLEND_NAV = ROOT / "repro/blend025-dual-paper/outputs/blend025_daily_nav.csv"
RESEARCH = ROOT / "research/gaps"

LOCKED_ID = "BLEND_025"
# Charter trailing gates (FINCAP50_SEALED_CAGR_IMPROVE_CHARTER)
TRAIL_ALERT_PP = 3.0
TRAIL_PAUSE_PP = 5.0


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
    if x is None:
        return "n/a"
    return f"{x:.2%}"


def _abs_or(x: float | None, default: float) -> float:
    return abs(default if x is None else x)


def _window(df: pd.DataFrame, start, end) -> pd.DataFrame:
    m = (df["date"] >= start) & (df["date"] <= end)
    return df.loc[m].reset_index(drop=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--asof", default=None, help="YYYY-MM-DD (default: last NAV date)")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    if not BASE_NAV.exists() or not BLEND_NAV.exists():
        raise SystemExit(
            "Missing dual-paper NAVs. Run scripts/e16_blend025_dual_paper_ledgers.py first."
        )

    base = _load(BASE_NAV)
    blend = _load(BLEND_NAV)
    asof = pd.Timestamp(args.asof) if args.asof else min(base["date"].max(), blend["date"].max())
    base = base[base["date"] <= asof]
    blend = blend[blend["date"] <= asof]

    month_start = pd.Timestamp(asof.year, asof.month, 1)
    windows = {
        "mtd": (month_start, asof),
        "ytd": (pd.Timestamp(asof.year, 1, 1), asof),
        "trailing_1y": (asof - pd.Timedelta(days=365), asof),
        "sealed_2023_plus": (pd.Timestamp("2023-01-01"), asof),
        "heldout_2019_plus": (pd.Timestamp("2019-01-01"), asof),
        "full": (base["date"].min(), asof),
    }

    rows = []
    for wname, (ws, we) in windows.items():
        b = _window(base, ws, we)
        c = _window(blend, ws, we)
        if len(b) < 2 or len(c) < 2:
            continue
        bnav = b["nav"] / float(b["nav"].iloc[0])
        cnav = c["nav"] / float(c["nav"].iloc[0])
        sb, sc = _stats(bnav), _stats(cnav)
        if sb["cagr"] is None or sc["cagr"] is None:
            cagr_giveback_pp = None
        else:
            cagr_giveback_pp = (sb["cagr"] - sc["cagr"]) * 100
        mdd_improve_pp = (_abs_or(sb["max_drawdown"], 9.0) - _abs_or(sc["max_drawdown"], 9.0)) * 100
        rows.append(
            {
                "window": wname,
                "start": str(pd.Timestamp(ws).date()),
                "end": str(pd.Timestamp(we).date()),
                "n_days": int(min(len(b), len(c))),
                "base_cagr": sb["cagr"],
                "base_mdd": sb["max_drawdown"],
                "blend025_cagr": sc["cagr"],
                "blend025_mdd": sc["max_drawdown"],
                "mdd_improve_pp": mdd_improve_pp,
                "cagr_giveback_pp": cagr_giveback_pp,
                "rel_nav_end": float(cnav.iloc[-1] / bnav.iloc[-1]),
            }
        )

    # Charter / ops alert windows — mtd is display-only.
    ALERT_WINDOWS = ("heldout_2019_plus", "sealed_2023_plus", "ytd", "trailing_1y")
    alerts = []
    for wname in ALERT_WINDOWS:
        r = next((x for x in rows if x["window"] == wname), None)
        if not r:
            continue
        if r["mdd_improve_pp"] < 0:
            alerts.append(f"ALERT: {LOCKED_ID} {wname} MDD worse than BASE (paper)")
        gb = r["cagr_giveback_pp"]
        if gb is None:
            continue
        if gb > TRAIL_ALERT_PP:
            alerts.append(
                f"ALERT: {LOCKED_ID} {wname} CAGR giveback > {TRAIL_ALERT_PP:.1f} pp (paper)"
            )
        if gb > TRAIL_PAUSE_PP:
            alerts.append(
                f"PAUSE_REVIEW: {wname} giveback > {TRAIL_PAUSE_PP:.0f} pp — "
                "extend observe; Soft-Frozen unchanged; no cutover talk"
            )

    args.out.mkdir(parents=True, exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "asof": str(asof.date()),
        "live_wire": False,
        "soft_frozen_default_unchanged": True,
        "locked_id": LOCKED_ID,
        "label": "BLEND_025_MONTH_END_PAPER_MONITOR",
        "status": "OPERATING_OBSERVE",
        "cutover_authorized": False,
        "windows": rows,
        "alerts": alerts,
        "cutover_blocked": True,  # observe sleeve never unlocks cutover
        "non_decision_windows": ["mtd"],
        "decision_alert_windows": list(ALERT_WINDOWS),
        "note": (
            "Paper observe only. Soft-Frozen Financial clip remains [0.50,0.95]. "
            "BLEND_025 dual-paper ≠ cutover license. "
            "mtd CAGR is display-only (not a cutover gate)."
        ),
    }
    (args.out / "month_end_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    pd.DataFrame(rows).to_csv(args.out / "month_end_windows.csv", index=False)

    lines = [
        f"# BLEND_025 Month-End Paper Monitor — asof {asof.date()}",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        "Status: **OPERATING OBSERVE / PAPER ONLY** — Soft-Frozen live default unchanged.",
        f"Locked: **{LOCKED_ID}** (α=0.25·FIN50 + 0.75·BASE)",
        "",
        "> **Alert windows:** `heldout_2019_plus`, `sealed_2023_plus`, `ytd`, `trailing_1y`.  ",
        "> **`mtd` CAGR is display-only** — **not** a cutover gate.  ",
        "> **Cutover:** always blocked on this observe sleeve.",
        "",
        "| Window | BASE CAGR | BASE MDD | BLEND_025 CAGR | BLEND_025 MDD | MDD Δpp | CAGR giveback pp | Rel NAV | Decision? |",
        "|---|---:|---:|---:|---:|---:|---:|---:|:---:|",
    ]
    for r in rows:
        decision = "no" if r["window"] == "mtd" else "yes"
        cagr_note = _pct(r["base_cagr"])
        blend_cagr_note = _pct(r["blend025_cagr"])
        if r["window"] == "mtd":
            cagr_note = f"{cagr_note}*"
            blend_cagr_note = f"{blend_cagr_note}*"
        gb = r["cagr_giveback_pp"]
        gb_s = "n/a" if gb is None else f"{gb:+.2f}"
        lines.append(
            f"| {r['window']} | {cagr_note} | {_pct(r['base_mdd'])} | "
            f"{blend_cagr_note} | {_pct(r['blend025_mdd'])} | "
            f"{r['mdd_improve_pp']:+.2f} | {gb_s} | {r['rel_nav_end']:.4f} | {decision} |"
        )
    lines += [
        "",
        "\\* `mtd` CAGR annualized from a short sample — **non-decision / display-only**.",
        "",
        "## Alerts",
        "",
    ]
    if alerts:
        for a in alerts:
            lines.append(f"- {a}")
    else:
        lines.append("- None (trailing/charter windows clean; cutover still blocked)")
    lines += [
        "",
        "## Cutover status",
        "",
        f"- `cutover_blocked`: **{summary['cutover_blocked']}** (always on observe sleeve)",
        f"- `cutover_authorized`: **{summary['cutover_authorized']}**",
        "- Soft-Frozen live clip stays **[0.50, 0.95]** — this monitor never flips it.",
        "",
        "## Ops note",
        "",
        "- Refresh NAVs: `python3 scripts/e16_blend025_dual_paper_ledgers.py`",
        "- Re-run monitor: `python3 scripts/e16_blend025_month_end_monitor.py`",
        "- Or month-end pack: `python3 scripts/ops_month_end_paper_pack.py`",
        "- Live cutover still requires a **separate human PR** after checklist gates.",
        "",
    ]
    md = "\n".join(lines)
    (args.out / "MONTH_END_MONITOR.md").write_text(md)
    (RESEARCH / "BLEND_025_MONTH_END_MONITOR.md").write_text(md)
    (RESEARCH / "BLEND_025_MONTH_END_MONITOR.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(
        json.dumps(
            {
                "asof": summary["asof"],
                "status": summary["status"],
                "alerts": alerts,
                "n_windows": len(rows),
                "cutover_blocked": True,
            },
            indent=2,
        )
    )
    print("EXIT:0")


if __name__ == "__main__":
    main()
