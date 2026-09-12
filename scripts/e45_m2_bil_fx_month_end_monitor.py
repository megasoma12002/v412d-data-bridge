#!/usr/bin/env python3
"""E45 M2 BIL_FX month-end dual-paper monitor — OPERATING (OPERATING_OBSERVE).

Compares BASE vs M2_RELOC_BIL_FX_C35 paper NAVs at month-end (or as-of).
Does NOT change Soft-Frozen. Does NOT place orders. Stitch always blocked.
Status OPERATING_OBSERVE — lock retarget ACCEPT C35 (2026-09-07 via 「請優化」).
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
from dual_paper_nav_io import load_pair_nav
from e45_paper_harness import WINDOWS_STANDARD
from research_metric_helpers import mdd_delta_pp

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "repro/e45-m2-bil-fx-dual-paper-observe/month_end"
BASE_NAV = ROOT / "repro/e45-m2-bil-fx-dual-paper-observe/outputs/base_e16_e18_e22_v2s_daily_nav.csv"
CHAL_NAV = ROOT / "repro/e45-m2-bil-fx-dual-paper-observe/outputs/m2_reloc_bil_fx_c35_daily_nav.csv"
COMPARE_NAV = ROOT / "repro/e45-m2-bil-fx-dual-paper-observe/outputs/dual_paper_nav_compare.csv"
OPS = ROOT / "research/ops"

LOCKED_ID = "M2_RELOC_BIL_FX_C35"
STATUS = "OPERATING_OBSERVE"
TRAIL_ALERT_PP = 3.0
TRAIL_PAUSE_PP = 5.0
DESIGN_GIVEBACK_PP = {
    "heldout_2019_plus": 2.5,  # C35 design giveback ~2.23
    "sealed_2023_plus": 6.0,
}
STRUCTURAL_BUFFER_PP = 2.0


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


def _window(df: pd.DataFrame, start, end) -> pd.DataFrame:
    m = (df["date"] >= start) & (df["date"] <= end)
    return df.loc[m].reset_index(drop=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--asof", default=None, help="YYYY-MM-DD (default: last NAV date)")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    base, chal, nav_source = load_pair_nav(
        BASE_NAV,
        CHAL_NAV,
        COMPARE_NAV,
        chal_col="nav_m2_reloc_bil_fx_c35",
        refresh_hint="scripts/e45_m2_bil_fx_dual_paper_ledgers.py",
    )
    asof = pd.Timestamp(args.asof) if args.asof else min(base["date"].max(), chal["date"].max())
    base = base[base["date"] <= asof]
    chal = chal[chal["date"] <= asof]

    month_start = pd.Timestamp(asof.year, asof.month, 1)
    windows = {
        "mtd": (month_start, asof),
        "ytd": (pd.Timestamp(asof.year, 1, 1), asof),
        "trailing_1y": (asof - pd.Timedelta(days=365), asof),
        "sealed_2023_plus": (pd.Timestamp(WINDOWS_STANDARD["sealed_2023_plus"][0]), asof),
        "heldout_2019_plus": (pd.Timestamp(WINDOWS_STANDARD["heldout_2019_plus"][0]), asof),
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
        cagr_giveback_pp = None if sb["cagr"] is None or sc["cagr"] is None else (sb["cagr"] - sc["cagr"]) * 100
        mdd_improve_pp = mdd_delta_pp(sb["max_drawdown"], sc["max_drawdown"])
        rows.append(
            {
                "window": wname,
                "start": str(pd.Timestamp(ws).date()),
                "end": str(pd.Timestamp(we).date()),
                "n_days": int(min(len(b), len(c))),
                "base_cagr": sb["cagr"],
                "base_mdd": sb["max_drawdown"],
                "m2_reloc_bil_fx_c35_cagr": sc["cagr"],
                "m2_reloc_bil_fx_c35_mdd": sc["max_drawdown"],
                "mdd_improve_pp": mdd_improve_pp,
                "cagr_giveback_pp": cagr_giveback_pp,
                "rel_nav_end": float(cnav.iloc[-1] / bnav.iloc[-1]),
            }
        )

    alerts: list[str] = []
    for wname in ("ytd", "trailing_1y"):
        r = next((x for x in rows if x["window"] == wname), None)
        if not r:
            continue
        if r["mdd_improve_pp"] is not None and r["mdd_improve_pp"] < 0:
            alerts.append(f"ALERT: {LOCKED_ID} {wname} MDD worse than BASE (paper)")
        gb = r["cagr_giveback_pp"]
        if gb is None:
            continue
        if gb > TRAIL_ALERT_PP:
            alerts.append(f"ALERT: {LOCKED_ID} {wname} CAGR giveback > {TRAIL_ALERT_PP:.1f} pp (paper)")
        if gb > TRAIL_PAUSE_PP:
            alerts.append(
                f"PAUSE_REVIEW: {wname} giveback > {TRAIL_PAUSE_PP:.0f} pp — "
                "extend observe; Soft-Frozen unchanged; no stitch talk"
            )

    for wname in ("heldout_2019_plus", "sealed_2023_plus"):
        r = next((x for x in rows if x["window"] == wname), None)
        if not r:
            continue
        if r["mdd_improve_pp"] is not None and r["mdd_improve_pp"] < 0:
            alerts.append(
                f"ALERT: {LOCKED_ID} {wname} MDD worse than BASE "
                "(structural window; design expected MDD improve)"
            )
        gb = r["cagr_giveback_pp"]
        design_gb = DESIGN_GIVEBACK_PP.get(wname)
        if gb is None or design_gb is None:
            continue
        if gb > design_gb + STRUCTURAL_BUFFER_PP:
            alerts.append(
                f"ALERT: {LOCKED_ID} {wname} CAGR giveback {gb:.2f} pp exceeds "
                f"design {design_gb:.2f}+{STRUCTURAL_BUFFER_PP:.0f} pp "
                "(structural; stitch still forbidden)"
            )

    args.out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(args.out / "month_end_windows.csv", index=False)

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "asof": str(asof.date()),
        "label": "E45_M2_BIL_FX_MONTH_END_MONITOR",
        "status": STATUS,
        "operating_observe": True,
        "nav_source": nav_source,
        "locked_id": LOCKED_ID,
        "def_honesty": "BIL × USDTWD mid — FX risk; mid optimistic; not TWD cash",
        "soft_frozen_unchanged": True,
        "stitch_authorized": False,
        "alerts": alerts,
        "windows": rows,
        "gates": {
            "trail_alert_pp": TRAIL_ALERT_PP,
            "trail_pause_pp": TRAIL_PAUSE_PP,
            "design_giveback_pp": DESIGN_GIVEBACK_PP,
            "structural_buffer_pp": STRUCTURAL_BUFFER_PP,
        },
        "non_actions": [
            "OPERATING_OBSERVE — OPERATING (paper only)",
            "No Soft-Frozen / DEFAULT / stitch",
            "No live orders",
        ],
    }
    (args.out / "month_end_monitor.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8"
    )
    OPS.mkdir(parents=True, exist_ok=True)
    (OPS / "E45_M2_BIL_FX_MONTH_END_MONITOR.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8"
    )

    lines = [
        f"# E45 M2 BIL_FX month-end monitor (asof {asof.date()})",
        "",
        f"**Status:** `{STATUS}` — **OPERATING (paper only)**",
        f"**Locked:** `{LOCKED_ID}` vs BASE",
        "",
        "| Window | MDD dpp | Giveback pp | Rel NAV |",
        "|---|---:|---:|---:|",
    ]
    for r in rows:
        mdpp = r["mdd_improve_pp"]
        gb = r["cagr_giveback_pp"]
        lines.append(
            f"| {r['window']} | {mdpp if mdpp is not None else 'n/a'} | "
            f"{gb if gb is not None else 'n/a'} | {r['rel_nav_end']:.4f} |"
        )
    lines += ["", "## Alerts", ""]
    if alerts:
        lines.extend(f"- {a}" for a in alerts)
    else:
        lines.append("- (none)")
    lines += [
        "",
        "## Honesty",
        "",
        "- BIL_FX = USD T-bill × USDTWD mid (FX risk; mid optimistic; not TWD cash)",
        "- Soft-Frozen KEEP · stitch FORBIDDEN · no live wire",
        "",
    ]
    md = "\n".join(lines) + "\n"
    (args.out / "month_end_monitor.md").write_text(md, encoding="utf-8")
    (OPS / "E45_M2_BIL_FX_MONTH_END_MONITOR_OPERATING.md").write_text(md, encoding="utf-8")
    print(json.dumps({"asof": str(asof.date()), "status": STATUS, "n_alerts": len(alerts)}, indent=2))


if __name__ == "__main__":
    main()
