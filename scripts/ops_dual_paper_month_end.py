#!/usr/bin/env python3
"""Parameterized dual-paper month-end monitor (ops / research).

Collapses near-copy ``*_month_end_monitor.py`` scripts into one runner +
``DualPaperMonitorSpec``. Soft-Frozen unchanged; no live wire.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd

from research_metric_helpers import mdd_delta_pp

ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "research/ops"

DEFAULT_TRAIL_ALERT_PP = 3.0
DEFAULT_TRAIL_PAUSE_PP = 5.0
DEFAULT_DESIGN_GIVEBACK_PP = {"heldout_2019_plus": 0.5, "sealed_2023_plus": 0.8}
DEFAULT_STRUCTURAL_BUFFER_PP = 2.0


@dataclass(frozen=True)
class DualPaperMonitorSpec:
    """Config for one BASE vs CHAL month-end observe."""

    label: str
    base_id: str
    chal_id: str
    default_out: Path
    base_nav: Path
    chal_nav: Path
    compare_nav: Path | None = None
    ops_stem: str | None = None  # writes research/ops/{stem}.{md,json}
    status: str = "OPERATING_OBSERVE"
    ledger_hint: str = "dual_paper_ledgers"
    missing_msg: str = "Missing dual-paper observe NAV."
    non_actions: tuple[str, ...] = (
        "paper observe only",
        "no Soft-Frozen clip flip",
        "no live wire from this monitor",
    )
    extra_payload: dict = field(default_factory=dict)
    trail_alert_pp: float = DEFAULT_TRAIL_ALERT_PP
    trail_pause_pp: float = DEFAULT_TRAIL_PAUSE_PP
    design_giveback_pp: dict[str, float] = field(
        default_factory=lambda: dict(DEFAULT_DESIGN_GIVEBACK_PP)
    )
    structural_buffer_pp: float = DEFAULT_STRUCTURAL_BUFFER_PP
    md_title: str | None = None
    md_footer: tuple[str, ...] = ()


def _load(path: Path) -> pd.DataFrame:
    d = pd.read_csv(path)
    d["date"] = pd.to_datetime(d["date"])
    return d.sort_values("date").reset_index(drop=True)


def load_books(spec: DualPaperMonitorSpec) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    if spec.base_nav.exists() and spec.chal_nav.exists():
        return _load(spec.base_nav), _load(spec.chal_nav), "daily_nav"
    if spec.compare_nav is not None and spec.compare_nav.exists():
        d = pd.read_csv(spec.compare_nav)
        d["date"] = pd.to_datetime(d["date"])
        if not {"nav_base", "nav_chal"}.issubset(d.columns):
            raise SystemExit(
                f"{spec.compare_nav} missing nav_base/nav_chal; run {spec.ledger_hint}"
            )
        base = d[["date", "nav_base"]].rename(columns={"nav_base": "nav"})
        chal = d[["date", "nav_chal"]].rename(columns={"nav_chal": "nav"})
        return (
            base.sort_values("date").reset_index(drop=True),
            chal.sort_values("date").reset_index(drop=True),
            "dual_paper_nav_compare",
        )
    raise SystemExit(f"{spec.missing_msg} Run {spec.ledger_hint}")


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


def compare_windows(
    base: pd.DataFrame, chal: pd.DataFrame, asof: pd.Timestamp
) -> list[dict]:
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


def build_alerts(spec: DualPaperMonitorSpec, rows: list[dict]) -> list[str]:
    out: list[str] = []
    for wname in ("ytd", "trailing_1y"):
        r = next((x for x in rows if x["window"] == wname), None)
        if not r:
            continue
        if r["mdd_improve_pp"] is not None and r["mdd_improve_pp"] < 0:
            out.append(f"ALERT: {spec.chal_id} {wname} MDD worse than {spec.base_id}")
        gb = r["cagr_giveback_pp"]
        if gb is None:
            continue
        if gb > spec.trail_alert_pp:
            out.append(
                f"ALERT: {spec.chal_id} {wname} CAGR giveback > {spec.trail_alert_pp:.1f} pp"
            )
        if gb > spec.trail_pause_pp:
            out.append(
                f"PAUSE_REVIEW: {spec.chal_id} {wname} giveback > {spec.trail_pause_pp:.0f} pp"
            )
    for wname, tgt in spec.design_giveback_pp.items():
        r = next((x for x in rows if x["window"] == wname), None)
        if not r:
            continue
        if r["mdd_improve_pp"] is not None and r["mdd_improve_pp"] < 0:
            out.append(f"ALERT: {spec.chal_id} {wname} MDD worse than {spec.base_id}")
        gb = r["cagr_giveback_pp"]
        if gb is not None and gb > tgt + spec.structural_buffer_pp:
            out.append(
                f"ALERT: {spec.chal_id} {wname} giveback {gb:.2f} > design "
                f"{tgt:.2f}+{spec.structural_buffer_pp:.0f}"
            )
    return out


def run_monitor(spec: DualPaperMonitorSpec, *, asof: str | None = None, out: Path | None = None) -> dict:
    base, chal, nav_source = load_books(spec)
    asof_ts = (
        pd.Timestamp(asof) if asof else min(base["date"].max(), chal["date"].max())
    )
    base = base[base["date"] <= asof_ts]
    chal = chal[chal["date"] <= asof_ts]
    rows = compare_windows(base, chal, asof_ts)
    alerts = build_alerts(spec, rows)

    out_dir = Path(out) if out is not None else spec.default_out
    out_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out_dir / "month_end_windows.csv", index=False)
    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "asof": str(asof_ts.date()),
        "label": spec.label,
        "status": spec.status,
        "base_id": spec.base_id,
        "challenger_id": spec.chal_id,
        "nav_source": nav_source,
        "live_wire": False,
        "soft_frozen_clips_unchanged": True,
        "alerts": alerts,
        "windows": rows,
        "gates": {
            "trail_alert_pp": spec.trail_alert_pp,
            "trail_pause_pp": spec.trail_pause_pp,
            "design_giveback_pp": dict(spec.design_giveback_pp),
            "structural_buffer_pp": spec.structural_buffer_pp,
        },
        "non_actions": list(spec.non_actions),
        **spec.extra_payload,
    }
    body = json.dumps(payload, indent=2, default=str) + "\n"
    (out_dir / "month_end_monitor.json").write_text(body, encoding="utf-8")
    stem = spec.ops_stem or spec.label
    OPS.mkdir(parents=True, exist_ok=True)
    OPS.joinpath(f"{stem}.json").write_text(body, encoding="utf-8")

    title = spec.md_title or f"{spec.label} month-end monitor (asof {asof_ts.date()})"
    lines = [
        f"# {title}",
        "",
        f"Status: `{spec.status}` · paper only · base `{spec.base_id}` vs `{spec.chal_id}`",
        "",
        "| Window | MDD dpp | Giveback pp | Score | Rel NAV |",
        "|---|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['window']} | {r['mdd_improve_pp']} | {r['cagr_giveback_pp']} | "
            f"{r['score']} | {r['rel_nav_end']:.4f} |"
        )
    lines += ["", "## Alerts", ""]
    if alerts:
        lines.extend(f"- {a}" for a in alerts)
    else:
        lines.append("- none")
    lines += ["", "## Non-actions", ""]
    lines.extend(f"- {x}" for x in spec.non_actions)
    if spec.md_footer:
        lines += ["", *spec.md_footer]
    lines.append("")
    md = "\n".join(lines) + "\n"
    (out_dir / "month_end_monitor.md").write_text(md, encoding="utf-8")
    OPS.joinpath(f"{stem}.md").write_text(md, encoding="utf-8")
    return {"asof": str(asof_ts.date()), "alerts": alerts, "n_windows": len(rows), "payload": payload}


def cli_main(spec: DualPaperMonitorSpec, argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=spec.label)
    ap.add_argument("--asof", default=None, help="YYYY-MM-DD (default: last common date)")
    ap.add_argument("--out", type=Path, default=spec.default_out)
    args = ap.parse_args(argv)
    summary = run_monitor(spec, asof=args.asof, out=args.out)
    print(
        json.dumps(
            {
                "asof": summary["asof"],
                "alerts": summary["alerts"],
                "n_windows": summary["n_windows"],
            },
            indent=2,
        )
    )
    return 0
