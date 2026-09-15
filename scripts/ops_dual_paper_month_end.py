#!/usr/bin/env python3
"""Parameterized dual-paper month-end monitor (ops / research).

Collapses near-copy ``*_month_end_monitor.py`` scripts into one runner +
``DualPaperMonitorSpec`` (and multi-challenger ``MultiPaperMonitorSpec``).
Soft-Frozen unchanged; no live wire.
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
GAPS = ROOT / "research/gaps"

DEFAULT_TRAIL_ALERT_PP = 3.0
DEFAULT_TRAIL_PAUSE_PP = 5.0
DEFAULT_DESIGN_GIVEBACK_PP = {"heldout_2019_plus": 0.5, "sealed_2023_plus": 0.8}
DEFAULT_STRUCTURAL_BUFFER_PP = 2.0
DEFAULT_WINDOWS = (
    "mtd",
    "ytd",
    "trailing_1y",
    "heldout_2019_plus",
    "sealed_2023_plus",
    "full",
)

# alert_policy values:
#   default     — trail on ytd/1y; design+buffer on design_giveback keys
#   flat_trail  — trail thresholds (incl PAUSE) on flat_trail_windows; no design path
#   l4          — research_gate_windows: MDD+giveback; ops_trail_windows: giveback only


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
    ops_stem: str | None = None  # writes {artifact_dir}/{stem}.{md,json}
    artifact_dir: Path = OPS
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
    window_keys: tuple[str, ...] = DEFAULT_WINDOWS
    # Extra fixed-end windows: (name, start_yyyy-mm-dd, end_yyyy-mm-dd)
    fixed_windows: tuple[tuple[str, str, str], ...] = ()
    alert_policy: str = "default"
    flat_trail_windows: tuple[str, ...] = (
        "heldout_2019_plus",
        "sealed_2023_plus",
        "ytd",
        "trailing_1y",
    )
    research_gate_windows: tuple[str, ...] = ("sealed_2023_plus", "validation_2019_2022")
    ops_trail_windows: tuple[str, ...] = ("ytd", "trailing_1y")
    coerce_none_cagr_to_zero: bool = False
    include_score: bool = True
    write_legacy_summary_names: bool = False  # MONTH_END_MONITOR.md + month_end_summary.json
    write_artifact_json: bool = True


@dataclass(frozen=True)
class MultiChallengerSpec:
    """One challenger sleeve inside a multi-paper month-end."""

    chal_id: str
    chal_nav: Path
    design_giveback_pp: dict[str, float] = field(
        default_factory=lambda: dict(DEFAULT_DESIGN_GIVEBACK_PP)
    )
    slug: str | None = None


@dataclass(frozen=True)
class MultiPaperMonitorSpec:
    """One BASE vs N challengers (FIN within-sleeve family)."""

    label: str
    base_id: str
    base_nav: Path
    challengers: tuple[MultiChallengerSpec, ...]
    default_out: Path
    ops_stem: str
    artifact_dir: Path = OPS
    status: str = "OPERATING_OBSERVE"
    ledger_hint: str = "dual_paper_ledgers"
    missing_msg: str = "Missing multi-paper observe NAV."
    non_actions: tuple[str, ...] = (
        "paper observe only",
        "no Soft-Frozen clip flip",
        "no live wire from this monitor",
    )
    extra_payload: dict = field(default_factory=dict)
    trail_alert_pp: float = DEFAULT_TRAIL_ALERT_PP
    trail_pause_pp: float = DEFAULT_TRAIL_PAUSE_PP
    structural_buffer_pp: float = DEFAULT_STRUCTURAL_BUFFER_PP
    md_title: str | None = None
    md_footer: tuple[str, ...] = ()
    legacy_rs_chal_id: str | None = None
    legacy_rs_csv_name: str = "month_end_windows_rs_legacy.csv"


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


def _window_bounds(
    keys: tuple[str, ...],
    fixed: tuple[tuple[str, str, str], ...],
    *,
    asof: pd.Timestamp,
    base_min: pd.Timestamp,
) -> dict[str, tuple[pd.Timestamp, pd.Timestamp]]:
    month_start = pd.Timestamp(asof.year, asof.month, 1)
    catalog = {
        "mtd": (month_start, asof),
        "ytd": (pd.Timestamp(asof.year, 1, 1), asof),
        "trailing_1y": (asof - pd.Timedelta(days=365), asof),
        "heldout_2019_plus": (pd.Timestamp("2019-01-01"), asof),
        "sealed_2023_plus": (pd.Timestamp("2023-01-01"), asof),
        "full": (base_min, asof),
    }
    for name, start, end in fixed:
        catalog[name] = (pd.Timestamp(start), pd.Timestamp(end))
    out: dict[str, tuple[pd.Timestamp, pd.Timestamp]] = {}
    for k in keys:
        if k not in catalog:
            raise SystemExit(f"unknown month-end window key: {k}")
        out[k] = catalog[k]
    for name, start, end in fixed:
        out[name] = (pd.Timestamp(start), pd.Timestamp(end))
    return out


def compare_windows(
    base: pd.DataFrame,
    chal: pd.DataFrame,
    asof: pd.Timestamp,
    *,
    window_keys: tuple[str, ...] = DEFAULT_WINDOWS,
    fixed_windows: tuple[tuple[str, str, str], ...] = (),
    coerce_none_cagr_to_zero: bool = False,
    include_score: bool = True,
    challenger_tag: str | None = None,
) -> list[dict]:
    bounds = _window_bounds(
        window_keys, fixed_windows, asof=asof, base_min=base["date"].min()
    )
    rows = []
    for wname, (ws, we) in bounds.items():
        b = _window(base, ws, we)
        c = _window(chal, ws, we)
        if len(b) < 2 or len(c) < 2:
            continue
        bnav = b["nav"] / float(b["nav"].iloc[0])
        cnav = c["nav"] / float(c["nav"].iloc[0])
        sb, sc = _stats(bnav), _stats(cnav)
        if coerce_none_cagr_to_zero:
            bc = 0.0 if sb["cagr"] is None else sb["cagr"]
            cc = 0.0 if sc["cagr"] is None else sc["cagr"]
            gb = (bc - cc) * 100.0
        else:
            gb = (
                None
                if sb["cagr"] is None or sc["cagr"] is None
                else (sb["cagr"] - sc["cagr"]) * 100.0
            )
        mdpp = mdd_delta_pp(sb["max_drawdown"], sc["max_drawdown"])
        row = {
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
            "rel_nav_end": float(cnav.iloc[-1] / bnav.iloc[-1]),
        }
        if include_score:
            row["score"] = (
                None if mdpp is None or gb is None else float(mdpp - 0.5 * abs(gb))
            )
        if challenger_tag is not None:
            row["challenger"] = challenger_tag
        rows.append(row)
    return rows


def _trail_alerts(
    *,
    chal_id: str,
    base_id: str,
    rows: list[dict],
    windows: tuple[str, ...],
    trail_alert_pp: float,
    trail_pause_pp: float,
    check_mdd: bool,
    pause_suffix: str = "",
    alert_tag: str = "",
) -> list[str]:
    out: list[str] = []
    tag = f" {alert_tag}" if alert_tag else ""
    for wname in windows:
        r = next((x for x in rows if x["window"] == wname), None)
        if not r:
            continue
        if check_mdd and r["mdd_improve_pp"] is not None and r["mdd_improve_pp"] < 0:
            out.append(f"ALERT: {chal_id} {wname} MDD worse than {base_id}{tag}")
        gb = r["cagr_giveback_pp"]
        if gb is None:
            continue
        if gb > trail_alert_pp:
            out.append(
                f"ALERT: {chal_id} {wname} CAGR giveback > {trail_alert_pp:.1f} pp{tag}"
            )
        if gb > trail_pause_pp:
            suffix = pause_suffix or f"{chal_id} {wname} giveback > {trail_pause_pp:.0f} pp"
            out.append(f"PAUSE_REVIEW: {suffix}")
    return out


def build_alerts(spec: DualPaperMonitorSpec, rows: list[dict]) -> list[str]:
    policy = spec.alert_policy
    if policy == "default":
        out = _trail_alerts(
            chal_id=spec.chal_id,
            base_id=spec.base_id,
            rows=rows,
            windows=("ytd", "trailing_1y"),
            trail_alert_pp=spec.trail_alert_pp,
            trail_pause_pp=spec.trail_pause_pp,
            check_mdd=True,
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

    if policy == "flat_trail":
        out = []
        for wname in spec.flat_trail_windows:
            r = next((x for x in rows if x["window"] == wname), None)
            if not r:
                continue
            if r["mdd_improve_pp"] is not None and r["mdd_improve_pp"] < 0:
                out.append(f"ALERT: {spec.chal_id} {wname} MDD worse than BASE (paper)")
            gb = r["cagr_giveback_pp"]
            if gb is None:
                continue
            if gb > spec.trail_alert_pp:
                out.append(
                    f"ALERT: {spec.chal_id} {wname} CAGR giveback > "
                    f"{spec.trail_alert_pp:.1f} pp (paper)"
                )
            if gb > spec.trail_pause_pp:
                out.append(
                    f"PAUSE_REVIEW: {wname} giveback > {spec.trail_pause_pp:.0f} pp — "
                    "extend observe; Soft-Frozen unchanged; no cutover talk"
                )
        return out

    if policy == "l4":
        out = []
        label_map = {
            "sealed_2023_plus": "sealed",
            "validation_2019_2022": "validation",
            "ytd": "ytd",
            "trailing_1y": "trailing_1y",
        }
        for wname in spec.research_gate_windows:
            r = next((x for x in rows if x["window"] == wname), None)
            if not r:
                continue
            label = label_map.get(wname, wname)
            if r["mdd_improve_pp"] is not None and r["mdd_improve_pp"] < 0:
                out.append(f"ALERT: {spec.chal_id} {label} MDD worse than BASE (paper)")
            gb = r["cagr_giveback_pp"]
            if gb is None:
                continue
            if gb > spec.trail_alert_pp:
                out.append(
                    f"ALERT: {spec.chal_id} {label} CAGR giveback > "
                    f"{spec.trail_alert_pp:.1f} pp (paper)"
                )
            if gb > spec.trail_pause_pp:
                out.append(
                    f"PAUSE_REVIEW: {label} giveback > {spec.trail_pause_pp:.0f} pp — "
                    "do not advance cutover discussion"
                )
        for wname in spec.ops_trail_windows:
            r = next((x for x in rows if x["window"] == wname), None)
            if not r:
                continue
            label = label_map.get(wname, wname)
            gb = r["cagr_giveback_pp"]
            if gb is None:
                continue
            if gb > spec.trail_alert_pp:
                out.append(
                    f"ALERT: {spec.chal_id} {label} CAGR giveback > "
                    f"{spec.trail_alert_pp:.1f} pp (paper ops)"
                )
            if gb > spec.trail_pause_pp:
                out.append(
                    f"PAUSE_REVIEW: {label} giveback > {spec.trail_pause_pp:.0f} pp — "
                    "extend observation; does not revoke PASS_HELDOUT_L4"
                )
        return out

    raise SystemExit(f"unknown alert_policy: {policy}")


def _write_md_compact(spec: DualPaperMonitorSpec, rows: list[dict], alerts: list[str], asof_ts: pd.Timestamp) -> str:
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
        score = r.get("score")
        lines.append(
            f"| {r['window']} | {r['mdd_improve_pp']} | {r['cagr_giveback_pp']} | "
            f"{score} | {r['rel_nav_end']:.4f} |"
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
    return "\n".join(lines) + "\n"


def run_monitor(spec: DualPaperMonitorSpec, *, asof: str | None = None, out: Path | None = None) -> dict:
    base, chal, nav_source = load_books(spec)
    asof_ts = (
        pd.Timestamp(asof) if asof else min(base["date"].max(), chal["date"].max())
    )
    base = base[base["date"] <= asof_ts]
    chal = chal[chal["date"] <= asof_ts]
    rows = compare_windows(
        base,
        chal,
        asof_ts,
        window_keys=spec.window_keys,
        fixed_windows=spec.fixed_windows,
        coerce_none_cagr_to_zero=spec.coerce_none_cagr_to_zero,
        include_score=spec.include_score,
    )
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
        "locked_id": spec.chal_id,
        "nav_source": nav_source,
        "live_wire": False,
        "soft_frozen_clips_unchanged": True,
        "soft_frozen_unchanged": True,
        "cutover_authorized": False,
        "alerts": alerts,
        "windows": rows,
        "gates": {
            "trail_alert_pp": spec.trail_alert_pp,
            "trail_pause_pp": spec.trail_pause_pp,
            "design_giveback_pp": dict(spec.design_giveback_pp),
            "structural_buffer_pp": spec.structural_buffer_pp,
            "alert_policy": spec.alert_policy,
        },
        "non_actions": list(spec.non_actions),
        **spec.extra_payload,
    }
    # Observe sleeves that always block cutover talk (L4 blocks only on PAUSE_REVIEW).
    if "cutover_blocked" not in payload:
        if spec.alert_policy == "l4":
            payload["cutover_blocked"] = any("PAUSE_REVIEW" in a for a in alerts)
        else:
            payload["cutover_blocked"] = True
    body = json.dumps(payload, indent=2, default=str) + "\n"
    (out_dir / "month_end_monitor.json").write_text(body, encoding="utf-8")
    if spec.write_legacy_summary_names:
        (out_dir / "month_end_summary.json").write_text(body, encoding="utf-8")

    stem = spec.ops_stem or spec.label
    art = Path(spec.artifact_dir)
    art.mkdir(parents=True, exist_ok=True)
    if spec.write_artifact_json:
        art.joinpath(f"{stem}.json").write_text(body, encoding="utf-8")

    md = _write_md_compact(spec, rows, alerts, asof_ts)
    (out_dir / "month_end_monitor.md").write_text(md, encoding="utf-8")
    if spec.write_legacy_summary_names:
        (out_dir / "MONTH_END_MONITOR.md").write_text(md, encoding="utf-8")
    art.joinpath(f"{stem}.md").write_text(md, encoding="utf-8")
    return {"asof": str(asof_ts.date()), "alerts": alerts, "n_windows": len(rows), "payload": payload}


def run_multi_monitor(
    spec: MultiPaperMonitorSpec, *, asof: str | None = None, out: Path | None = None
) -> dict:
    missing = [p for p in [spec.base_nav] + [c.chal_nav for c in spec.challengers] if not p.exists()]
    if missing:
        raise SystemExit(f"{spec.missing_msg} Missing: {missing}. Run {spec.ledger_hint}")

    base = _load(spec.base_nav)
    chal_dfs = {c.chal_id: _load(c.chal_nav) for c in spec.challengers}
    asof_ts = (
        pd.Timestamp(asof)
        if asof
        else min([base["date"].max()] + [d["date"].max() for d in chal_dfs.values()])
    )
    base = base[base["date"] <= asof_ts]
    for cid in list(chal_dfs):
        chal_dfs[cid] = chal_dfs[cid][chal_dfs[cid]["date"] <= asof_ts]

    all_rows: list[dict] = []
    alerts: list[str] = []
    by_chal: dict[str, list[dict]] = {}
    for c in spec.challengers:
        dual = DualPaperMonitorSpec(
            label=f"{spec.label}__{c.chal_id}",
            base_id=spec.base_id,
            chal_id=c.chal_id,
            default_out=spec.default_out,
            base_nav=spec.base_nav,
            chal_nav=c.chal_nav,
            design_giveback_pp=dict(c.design_giveback_pp),
            trail_alert_pp=spec.trail_alert_pp,
            trail_pause_pp=spec.trail_pause_pp,
            structural_buffer_pp=spec.structural_buffer_pp,
            include_score=False,
        )
        rows = compare_windows(
            base,
            chal_dfs[c.chal_id],
            asof_ts,
            include_score=False,
            challenger_tag=c.chal_id,
        )
        by_chal[c.chal_id] = rows
        all_rows.extend(rows)
        alerts.extend(build_alerts(dual, rows))

    out_dir = Path(out) if out is not None else spec.default_out
    out_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(all_rows).to_csv(out_dir / "month_end_windows.csv", index=False)

    if spec.legacy_rs_chal_id and spec.legacy_rs_chal_id in by_chal:
        legacy_rs = []
        for r in by_chal[spec.legacy_rs_chal_id]:
            legacy_rs.append(
                {
                    **{k: v for k, v in r.items() if k not in ("chal_cagr", "chal_mdd", "challenger")},
                    "fin_rs_soft_tilt_exdiv_cagr": r["chal_cagr"],
                    "fin_rs_soft_tilt_exdiv_mdd": r["chal_mdd"],
                }
            )
        if legacy_rs:
            pd.DataFrame(legacy_rs).to_csv(out_dir / spec.legacy_rs_csv_name, index=False)

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "asof": str(asof_ts.date()),
        "label": spec.label,
        "status": spec.status,
        "operating_observe": True,
        "base_id": spec.base_id,
        "challengers": [c.chal_id for c in spec.challengers],
        "live_wire": False,
        "soft_frozen_unchanged": True,
        "soft_frozen_clips_unchanged": True,
        "cutover_authorized": False,
        "cutover_blocked": True,
        "alerts": alerts,
        "windows": all_rows,
        "windows_by_challenger": by_chal,
        "gates": {
            "trail_alert_pp": spec.trail_alert_pp,
            "trail_pause_pp": spec.trail_pause_pp,
            "design_giveback_pp": {c.chal_id: dict(c.design_giveback_pp) for c in spec.challengers},
            "structural_buffer_pp": spec.structural_buffer_pp,
        },
        "non_actions": list(spec.non_actions),
        **spec.extra_payload,
    }
    body = json.dumps(payload, indent=2, default=str) + "\n"
    (out_dir / "month_end_monitor.json").write_text(body, encoding="utf-8")
    art = Path(spec.artifact_dir)
    art.mkdir(parents=True, exist_ok=True)
    art.joinpath(f"{spec.ops_stem}.json").write_text(body, encoding="utf-8")

    title = spec.md_title or f"{spec.label} month-end monitor (asof {asof_ts.date()})"
    lines = [
        f"# {title}",
        "",
        f"**Status:** `{spec.status}` — **paper only**",
        f"**Books:** `{spec.base_id}` ∥ "
        + " ∥ ".join(f"`{c.chal_id}`" for c in spec.challengers),
        "",
    ]
    for cid, rows in by_chal.items():
        lines += [
            f"## {cid} vs {spec.base_id}",
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
    lines += ["", "## Non-actions", ""]
    lines.extend(f"- {x}" for x in spec.non_actions)
    if spec.md_footer:
        lines += ["", *spec.md_footer]
    lines.append("")
    md = "\n".join(lines) + "\n"
    (out_dir / "month_end_monitor.md").write_text(md, encoding="utf-8")
    art.joinpath(f"{spec.ops_stem}.md").write_text(md, encoding="utf-8")
    return {
        "asof": str(asof_ts.date()),
        "alerts": alerts,
        "n_windows": len(all_rows),
        "payload": payload,
    }


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


def cli_main_multi(spec: MultiPaperMonitorSpec, argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=spec.label)
    ap.add_argument("--asof", default=None, help="YYYY-MM-DD (default: last common date)")
    ap.add_argument("--out", type=Path, default=spec.default_out)
    args = ap.parse_args(argv)
    summary = run_multi_monitor(spec, asof=args.asof, out=args.out)
    print(
        json.dumps(
            {
                "asof": summary["asof"],
                "alerts": summary["alerts"],
                "n_windows": summary["n_windows"],
                "challengers": [c.chal_id for c in spec.challengers],
            },
            indent=2,
        )
    )
    return 0
