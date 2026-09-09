#!/usr/bin/env python3
"""FIN within-sleeve month-end multi-paper monitor — OPERATING OBSERVE.

Compares FIN_EQUAL vs FIN_RS_SOFT_TILT_EXDIV, MIX_L75 (λ=0.75), and KD_OPT
(KD_APR15_MAY15_Klt30_T15) paper NAVs at month-end (or as-of).
Does NOT change Soft-Frozen. Does NOT place orders.
Live FIN equal-split untouched.
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
from e45_paper_harness import WINDOWS_STANDARD
from research_metric_helpers import mdd_delta_pp

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "repro/fin-within-sleeve-dual-paper-observe/month_end"
BASE_NAV = ROOT / "repro/fin-within-sleeve-dual-paper-observe/outputs/base_fin_equal_daily_nav.csv"
CHAL_RS_NAV = (
    ROOT / "repro/fin-within-sleeve-dual-paper-observe/outputs/fin_rs_soft_tilt_exdiv_daily_nav.csv"
)
CHAL_MIX_NAV = ROOT / "repro/fin-within-sleeve-dual-paper-observe/outputs/fin_mix_l75_daily_nav.csv"
CHAL_KD_NAV = ROOT / "repro/fin-within-sleeve-dual-paper-observe/outputs/fin_kd_opt_daily_nav.csv"
OPS = ROOT / "research/ops"

BASE_ID = "FIN_EQUAL"
CHAL_RS_ID = "FIN_RS_SOFT_TILT_EXDIV"
CHAL_MIX_ID = "MIX_L75"
CHAL_KD_ID = "KD_OPT"
STATUS = "OPERATING_OBSERVE"
TRAIL_ALERT_PP = 3.0
TRAIL_PAUSE_PP = 5.0
# Design giveback (BASE−CHAL) from Stage C / mix probe / KD optimize
DESIGN_GIVEBACK_PP = {
    CHAL_RS_ID: {
        "heldout_2019_plus": 1.5,
        "sealed_2023_plus": 2.0,
    },
    CHAL_MIX_ID: {
        "heldout_2019_plus": 0.5,
        "sealed_2023_plus": 0.8,
    },
    CHAL_KD_ID: {
        "heldout_2019_plus": 0.5,
        "sealed_2023_plus": 0.8,
    },
}
STRUCTURAL_BUFFER_PP = 2.0

CHALLENGERS = (
    {
        "id": CHAL_RS_ID,
        "slug": "fin_rs_soft_tilt_exdiv",
        "path": CHAL_RS_NAV,
    },
    {
        "id": CHAL_MIX_ID,
        "slug": "fin_mix_l75",
        "path": CHAL_MIX_NAV,
    },
    {
        "id": CHAL_KD_ID,
        "slug": "fin_kd_opt",
        "path": CHAL_KD_NAV,
    },
)


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


def _compare_windows(base: pd.DataFrame, chal: pd.DataFrame, asof: pd.Timestamp, chal_id: str) -> list[dict]:
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
        cagr_giveback_pp = (
            None if sb["cagr"] is None or sc["cagr"] is None else (sb["cagr"] - sc["cagr"]) * 100
        )
        mdd_improve_pp = mdd_delta_pp(sb["max_drawdown"], sc["max_drawdown"])
        rows.append(
            {
                "challenger": chal_id,
                "window": wname,
                "start": str(pd.Timestamp(ws).date()),
                "end": str(pd.Timestamp(we).date()),
                "n_days": int(min(len(b), len(c))),
                "base_cagr": sb["cagr"],
                "base_mdd": sb["max_drawdown"],
                "chal_cagr": sc["cagr"],
                "chal_mdd": sc["max_drawdown"],
                "mdd_improve_pp": mdd_improve_pp,
                "cagr_giveback_pp": cagr_giveback_pp,
                "rel_nav_end": float(cnav.iloc[-1] / bnav.iloc[-1]),
            }
        )
    return rows


def _alerts_for(rows: list[dict], chal_id: str) -> list[str]:
    alerts: list[str] = []
    for wname in ("ytd", "trailing_1y"):
        r = next((x for x in rows if x["window"] == wname), None)
        if not r:
            continue
        if r["mdd_improve_pp"] is not None and r["mdd_improve_pp"] < 0:
            alerts.append(f"ALERT: {chal_id} {wname} MDD worse than BASE (paper)")
        gb = r["cagr_giveback_pp"]
        if gb is None:
            continue
        if gb > TRAIL_ALERT_PP:
            alerts.append(f"ALERT: {chal_id} {wname} CAGR giveback > {TRAIL_ALERT_PP:.1f} pp (paper)")
        if gb > TRAIL_PAUSE_PP:
            alerts.append(
                f"PAUSE_REVIEW: {chal_id} {wname} giveback > {TRAIL_PAUSE_PP:.0f} pp — "
                "extend observe; Soft-Frozen unchanged; no live wire"
            )

    design = DESIGN_GIVEBACK_PP.get(chal_id, {})
    for wname in ("heldout_2019_plus", "sealed_2023_plus"):
        r = next((x for x in rows if x["window"] == wname), None)
        if not r:
            continue
        if r["mdd_improve_pp"] is not None and r["mdd_improve_pp"] < 0:
            alerts.append(
                f"ALERT: {chal_id} {wname} MDD worse than BASE "
                "(structural window; expected MDD improve)"
            )
        gb = r["cagr_giveback_pp"]
        design_gb = design.get(wname)
        if gb is None or design_gb is None:
            continue
        if gb > design_gb + STRUCTURAL_BUFFER_PP:
            alerts.append(
                f"ALERT: {chal_id} {wname} CAGR giveback {gb:.2f} pp exceeds "
                f"design {design_gb:.2f}+{STRUCTURAL_BUFFER_PP:.0f} pp "
                "(structural; live wire still forbidden)"
            )
    return alerts


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--asof", default=None, help="YYYY-MM-DD (default: last NAV date)")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    missing = [p for p in [BASE_NAV] + [c["path"] for c in CHALLENGERS] if not p.exists()]
    if missing:
        raise SystemExit(
            "Missing dual-paper NAVs "
            f"({', '.join(str(p) for p in missing)}). "
            "Run scripts/e16_fin_within_sleeve_dual_paper_ledgers.py first."
        )

    base = _load(BASE_NAV)
    chal_dfs = {c["id"]: _load(c["path"]) for c in CHALLENGERS}
    asof = pd.Timestamp(args.asof) if args.asof else min(
        [base["date"].max()] + [d["date"].max() for d in chal_dfs.values()]
    )
    base = base[base["date"] <= asof]
    for cid in list(chal_dfs):
        chal_dfs[cid] = chal_dfs[cid][chal_dfs[cid]["date"] <= asof]

    all_rows: list[dict] = []
    alerts: list[str] = []
    by_chal: dict[str, list[dict]] = {}
    for c in CHALLENGERS:
        rows = _compare_windows(base, chal_dfs[c["id"]], asof, c["id"])
        by_chal[c["id"]] = rows
        all_rows.extend(rows)
        alerts.extend(_alerts_for(rows, c["id"]))

    args.out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(all_rows).to_csv(args.out / "month_end_windows.csv", index=False)

    # Backward-compat wide columns for RS challenger (ops consumers)
    rs_rows = by_chal.get(CHAL_RS_ID, [])
    legacy_rs = []
    for r in rs_rows:
        legacy_rs.append(
            {
                **{k: v for k, v in r.items() if k not in ("chal_cagr", "chal_mdd", "challenger")},
                "fin_rs_soft_tilt_exdiv_cagr": r["chal_cagr"],
                "fin_rs_soft_tilt_exdiv_mdd": r["chal_mdd"],
            }
        )
    if legacy_rs:
        pd.DataFrame(legacy_rs).to_csv(args.out / "month_end_windows_rs_legacy.csv", index=False)

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "asof": str(asof.date()),
        "status": STATUS,
        "operating_observe": True,
        "base_id": BASE_ID,
        "challengers": [c["id"] for c in CHALLENGERS],
        "locked_id": CHAL_RS_ID,
        "mix_id": CHAL_MIX_ID,
        "kd_id": CHAL_KD_ID,
        "kd_optimal_id": "KD_APR15_MAY15_Klt30_T15",
        "soft_frozen_unchanged": True,
        "live_wire": False,
        "cutover_authorized": False,
        "alerts": alerts,
        "windows": all_rows,
        "windows_by_challenger": by_chal,
        "gates": {
            "trail_alert_pp": TRAIL_ALERT_PP,
            "trail_pause_pp": TRAIL_PAUSE_PP,
            "design_giveback_pp": DESIGN_GIVEBACK_PP,
            "structural_buffer_pp": STRUCTURAL_BUFFER_PP,
        },
        "non_actions": [
            "OPERATING_OBSERVE — paper only",
            "No Soft-Frozen flip",
            "No live e21 FIN within-sleeve wire",
        ],
    }
    (args.out / "month_end_monitor.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8"
    )
    OPS.joinpath("FIN_WITHIN_SLEEVE_MONTH_END_MONITOR.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8"
    )

    lines = [
        f"# FIN within-sleeve month-end monitor (asof {asof.date()})",
        "",
        f"**Status:** `{STATUS}` — **paper only**",
        f"**Books:** `{BASE_ID}` ∥ `{CHAL_RS_ID}` ∥ `{CHAL_MIX_ID}` ∥ `{CHAL_KD_ID}`",
        "",
    ]
    for cid, rows in by_chal.items():
        lines += [
            f"## {cid} vs {BASE_ID}",
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
        lines.append("")
    lines += ["## Alerts", ""]
    if alerts:
        lines.extend(f"- {a}" for a in alerts)
    else:
        lines.append("- (none)")
    lines += [
        "",
        "## Hard rules",
        "",
        "- Soft-Frozen KEEP · live FIN equal-split untouched · no cutover from this monitor",
        "",
    ]
    md = "\n".join(lines) + "\n"
    (args.out / "month_end_monitor.md").write_text(md, encoding="utf-8")
    OPS.joinpath("FIN_WITHIN_SLEEVE_MONTH_END_MONITOR.md").write_text(md, encoding="utf-8")
    print(
        json.dumps(
            {
                "status": STATUS,
                "asof": str(asof.date()),
                "challengers": [c["id"] for c in CHALLENGERS],
                "alerts": alerts,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
