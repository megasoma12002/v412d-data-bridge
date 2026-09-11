#!/usr/bin/env python3
"""Sleeve-tilt dual-paper month-end monitor — OPERATING OBSERVE.

Compares LIVE_STACK vs SLEEVE_BELOW_MA60_a01.
Paper-only; Soft-Frozen clips KEEP; no live wire; Soft-assist observe unchanged.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from research_metric_helpers import mdd_delta_pp
from sleeve_tilt_helpers import BASE_ID, CHAMPION_ID

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "repro/sleeve-tilt-dual-paper-observe/month_end"
BASE_NAV = ROOT / "repro/sleeve-tilt-dual-paper-observe/outputs/live_stack_daily_nav.csv"
CHAL_NAV = (
    ROOT / "repro/sleeve-tilt-dual-paper-observe/outputs/sleeve_below_ma60_a01_daily_nav.csv"
)
COMPARE_NAV = ROOT / "repro/sleeve-tilt-dual-paper-observe/outputs/dual_paper_nav_compare.csv"
OPS = ROOT / "research/ops"

STATUS = "OPERATING_OBSERVE"
TRAIL_ALERT_PP = 3.0
TRAIL_PAUSE_PP = 5.0
DESIGN_GIVEBACK_PP = {"heldout_2019_plus": 0.5, "sealed_2023_plus": 0.8}
STRUCTURAL_BUFFER_PP = 2.0


def _load(path: Path) -> pd.DataFrame:
    d = pd.read_csv(path)
    d["date"] = pd.to_datetime(d["date"])
    return d.sort_values("date").reset_index(drop=True)


def _load_books() -> tuple[pd.DataFrame, pd.DataFrame, str]:
    if BASE_NAV.exists() and CHAL_NAV.exists():
        return _load(BASE_NAV), _load(CHAL_NAV), "daily_nav"
    if COMPARE_NAV.exists():
        d = pd.read_csv(COMPARE_NAV)
        d["date"] = pd.to_datetime(d["date"])
        if not {"nav_base", "nav_chal"}.issubset(d.columns):
            raise SystemExit(
                f"{COMPARE_NAV} missing nav_base/nav_chal; "
                "run scripts/e16_sleeve_tilt_dual_paper_ledgers.py"
            )
        base = d[["date", "nav_base"]].rename(columns={"nav_base": "nav"})
        chal = d[["date", "nav_chal"]].rename(columns={"nav_chal": "nav"})
        return (
            base.sort_values("date").reset_index(drop=True),
            chal.sort_values("date").reset_index(drop=True),
            "dual_paper_nav_compare",
        )
    raise SystemExit(
        "Missing Sleeve-tilt observe NAV. Run scripts/e16_sleeve_tilt_dual_paper_ledgers.py"
    )


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


def _window(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    return df[(df["date"] >= start) & (df["date"] <= end)].reset_index(drop=True)


def _compare_windows(base: pd.DataFrame, chal: pd.DataFrame, asof: pd.Timestamp) -> list[dict]:
    month_start = pd.Timestamp(asof.year, asof.month, 1)
    windows = {
        "mtd": (month_start, asof),
        "ytd": (pd.Timestamp(asof.year, 1, 1), asof),
        "trailing_1y": (asof - pd.Timedelta(days=365), asof),
        "heldout_2019_plus": (pd.Timestamp("2019-01-01"), asof),
        "sealed_2023_plus": (pd.Timestamp("2023-01-01"), asof),
        "full": (base["date"].min(), asof),
    }
    rows = []
    for wname, (ws, we) in windows.items():
        b = _window(base, ws, we)
        c = _window(chal, ws, we)
        if len(b) < 2 or len(c) < 2:
            continue
        bnav = b["nav"] / float(b["nav"].iloc[0])
        cnav = c["nav"] / float(c["nav"].iloc[0])
        sb, sc = _stats(bnav), _stats(cnav)
        gb = None if sb["cagr"] is None or sc["cagr"] is None else (sb["cagr"] - sc["cagr"]) * 100.0
        mdpp = mdd_delta_pp(sb["max_drawdown"], sc["max_drawdown"])
        rows.append(
            {
                "window": wname,
                "start": str(pd.Timestamp(ws).date()),
                "end": str(pd.Timestamp(we).date()),
                "n_days": int(min(len(b), len(c))),
                "base_cagr": sb["cagr"],
                "base_mdd": sb["max_drawdown"],
                "chal_cagr": sc["cagr"],
                "chal_mdd": sc["max_drawdown"],
                "mdd_improve_pp": mdpp,
                "cagr_giveback_pp": gb,
                "score": None if mdpp is None or gb is None else float(mdpp - 0.5 * abs(gb)),
                "rel_nav_end": float(cnav.iloc[-1] / bnav.iloc[-1]),
            }
        )
    return rows


def _alerts(rows: list[dict]) -> list[str]:
    out = []
    for wname in ("ytd", "trailing_1y"):
        r = next((x for x in rows if x["window"] == wname), None)
        if not r:
            continue
        if r["mdd_improve_pp"] is not None and r["mdd_improve_pp"] < 0:
            out.append(f"ALERT: {CHAMPION_ID} {wname} MDD worse than {BASE_ID}")
        gb = r["cagr_giveback_pp"]
        if gb is None:
            continue
        if gb > TRAIL_ALERT_PP:
            out.append(f"ALERT: {CHAMPION_ID} {wname} CAGR giveback > {TRAIL_ALERT_PP:.1f} pp")
        if gb > TRAIL_PAUSE_PP:
            out.append(f"PAUSE_REVIEW: {CHAMPION_ID} {wname} giveback > {TRAIL_PAUSE_PP:.0f} pp")
    for wname in ("heldout_2019_plus", "sealed_2023_plus"):
        r = next((x for x in rows if x["window"] == wname), None)
        if not r:
            continue
        if r["mdd_improve_pp"] is not None and r["mdd_improve_pp"] < 0:
            out.append(f"ALERT: {CHAMPION_ID} {wname} MDD worse than {BASE_ID}")
        gb = r["cagr_giveback_pp"]
        tgt = DESIGN_GIVEBACK_PP[wname]
        if gb is not None and gb > tgt + STRUCTURAL_BUFFER_PP:
            out.append(
                f"ALERT: {CHAMPION_ID} {wname} giveback {gb:.2f} > design {tgt:.2f}+{STRUCTURAL_BUFFER_PP:.0f}"
            )
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--asof", default=None, help="YYYY-MM-DD (default: last common date)")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    base, chal, nav_source = _load_books()
    asof = pd.Timestamp(args.asof) if args.asof else min(base["date"].max(), chal["date"].max())
    base = base[base["date"] <= asof]
    chal = chal[chal["date"] <= asof]
    rows = _compare_windows(base, chal, asof)
    alerts = _alerts(rows)

    args.out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(args.out / "month_end_windows.csv", index=False)
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "asof": str(asof.date()),
        "label": "SLEEVE_LAYER_TILT_MONTH_END_MONITOR",
        "status": STATUS,
        "base_id": BASE_ID,
        "challenger_id": CHAMPION_ID,
        "nav_source": nav_source,
        "live_wire": False,
        "soft_frozen_clips_unchanged": True,
        "soft_assist_observe": "UNCHANGED",
        "alerts": alerts,
        "windows": rows,
        "gates": {
            "trail_alert_pp": TRAIL_ALERT_PP,
            "trail_pause_pp": TRAIL_PAUSE_PP,
            "design_giveback_pp": DESIGN_GIVEBACK_PP,
            "structural_buffer_pp": STRUCTURAL_BUFFER_PP,
        },
        "non_actions": [
            "paper observe only",
            "no Soft-Frozen clip flip",
            "no live Sleeve-tilt wire",
            "Soft-assist observe unchanged",
        ],
    }
    (args.out / "month_end_monitor.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8"
    )
    OPS.joinpath("SLEEVE_LAYER_TILT_MONTH_END_MONITOR.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8"
    )
    lines = [
        f"# Sleeve-tilt month-end monitor (asof {asof.date()})",
        "",
        f"Status: `{STATUS}` · paper only · base `{BASE_ID}` vs `{CHAMPION_ID}`",
        "",
        "| Window | MDD dpp | Giveback pp | Score | Rel NAV |",
        "|---|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['window']} | {r['mdd_improve_pp']} | {r['cagr_giveback_pp']} | {r['score']} | {r['rel_nav_end']:.4f} |"
        )
    lines += ["", "## Alerts", ""]
    if alerts:
        lines.extend(f"- {a}" for a in alerts)
    else:
        lines.append("- none")
    lines += [
        "",
        "## Non-actions",
        "",
        "- No live Sleeve-tilt wire / Soft-Frozen clip flip / Soft-assist combo",
        "",
    ]
    md = "\n".join(lines) + "\n"
    (args.out / "month_end_monitor.md").write_text(md, encoding="utf-8")
    OPS.joinpath("SLEEVE_LAYER_TILT_MONTH_END_MONITOR.md").write_text(md, encoding="utf-8")
    print(json.dumps({"asof": str(asof.date()), "alerts": alerts, "n_windows": len(rows)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
