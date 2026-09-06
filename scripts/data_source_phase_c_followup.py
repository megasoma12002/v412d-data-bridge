#!/usr/bin/env python3
"""Data-source Phase C follow-up: time-sliced shadow drift + adj-CA deepen.

Reuses committed C1/C2 CSVs from repro/data-source-phase-c (no e21 rewrite).
Optionally re-runs phase_c probes when --refresh is passed.

Soft-Frozen KEEP · no silent primary switch · Yahoo TAIEX failover stays opt-in.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro/data-source-phase-c"
OUT = ROOT / "repro/data-source-phase-c-followup"
OPS = ROOT / "research/ops"

C1_CSV = REPRO / "c1_fin12_history_returns.csv"
C2_CSV = REPRO / "c2_adj_returns.csv"

SLICES = {
    "full": None,
    "pre_2020": ("2011-01-01", "2019-12-31"),
    "covid_2020": ("2020-01-01", "2020-12-31"),
    "heldout_2019_plus": ("2019-01-01", None),
    "sealed_2023_plus": ("2023-01-01", None),
}


def slice_frame(df: pd.DataFrame, start: str | None, end: str | None) -> pd.DataFrame:
    d = df.copy()
    d["date"] = pd.to_datetime(d["date"])
    if start:
        d = d[d["date"] >= pd.Timestamp(start)]
    if end:
        d = d[d["date"] <= pd.Timestamp(end)]
    return d


def corr_safe(a: pd.Series, b: pd.Series) -> float | None:
    if len(a) < 30:
        return None
    if a.std() == 0 or b.std() == 0:
        return None
    return float(a.corr(b))


def analyze_c1(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for name, bounds in SLICES.items():
        part = df if bounds is None else slice_frame(df, bounds[0], bounds[1])
        for code, g in part.groupby("code"):
            a = g["ret_live"].astype(float)
            b = g["ret_yahoo"].astype(float)
            m = pd.concat([a, b], axis=1).dropna()
            if len(m) < 30:
                rows.append(
                    {
                        "slice": name,
                        "code": code,
                        "n": int(len(m)),
                        "mad": None,
                        "corr": None,
                        "status": "INSUFFICIENT",
                    }
                )
                continue
            mad = float((m.iloc[:, 0] - m.iloc[:, 1]).abs().mean())
            corr = corr_safe(m.iloc[:, 0], m.iloc[:, 1])
            status = "PASS"
            if mad > 0.008 or (corr is not None and corr < 0.95):
                status = "DRIFT"
            rows.append(
                {
                    "slice": name,
                    "code": code,
                    "n": int(len(m)),
                    "mad": mad,
                    "corr": corr,
                    "status": status,
                }
            )
    return pd.DataFrame(rows)


def analyze_c2(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for name, bounds in SLICES.items():
        part = df if bounds is None else slice_frame(df, bounds[0], bounds[1])
        for code, g in part.groupby("code"):
            a = g["ret_live_adj"].astype(float)
            b = g["ret_yahoo_adj"].astype(float)
            m = pd.concat([a, b], axis=1).dropna()
            if len(m) < 30:
                rows.append(
                    {
                        "slice": name,
                        "code": code,
                        "n": int(len(m)),
                        "mad": None,
                        "corr": None,
                        "status": "INSUFFICIENT",
                    }
                )
                continue
            mad = float((m.iloc[:, 0] - m.iloc[:, 1]).abs().mean())
            corr = corr_safe(m.iloc[:, 0], m.iloc[:, 1])
            status = "PASS" if mad <= 0.015 else "WARN"
            rows.append(
                {
                    "slice": name,
                    "code": code,
                    "n": int(len(m)),
                    "mad": mad,
                    "corr": corr,
                    "status": status,
                }
            )
    return pd.DataFrame(rows)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="Re-run data_source_phase_c_probes.py first")
    ap.add_argument("--skip-c3", action="store_true", help="Pass --skip-c3 to probes on refresh")
    args = ap.parse_args()

    if args.refresh:
        cmd = [sys.executable, str(ROOT / "scripts/data_source_phase_c_probes.py")]
        if args.skip_c3:
            cmd.append("--skip-c3")
        print("refresh probes:", " ".join(cmd), flush=True)
        subprocess.run(cmd, check=False)

    out_o = OUT / "outputs"
    out_r = OUT / "reports"
    for d in (out_o, out_r, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = datetime.now(timezone.utc).isoformat()

    if not C1_CSV.exists() or not C2_CSV.exists():
        raise SystemExit(f"missing phase-C CSVs under {REPRO} — run probes first")

    c1 = pd.read_csv(C1_CSV, dtype={"code": str})
    c2 = pd.read_csv(C2_CSV, dtype={"code": str})
    # Preserve ETF zero-padding (0050) if upstream ever emitted bare ints.
    c1["code"] = c1["code"].map(lambda x: str(x).zfill(4) if str(x).isdigit() and len(str(x)) < 4 else str(x))
    c2["code"] = c2["code"].map(lambda x: str(x).zfill(4) if str(x).isdigit() and len(str(x)) < 4 else str(x))
    c1_s = analyze_c1(c1)
    c2_s = analyze_c2(c2)
    c1_s.to_csv(out_o / "c1_slice_drift.csv", index=False)
    c2_s.to_csv(out_o / "c2_slice_adj_drift.csv", index=False)

    # Focus: sealed_2023_plus offenders
    c1_sealed = c1_s[c1_s["slice"] == "sealed_2023_plus"].sort_values("mad", ascending=False)
    c2_sealed = c2_s[c2_s["slice"] == "sealed_2023_plus"].sort_values("mad", ascending=False)
    c1_drift = c1_sealed[c1_sealed["status"] == "DRIFT"]
    c2_warn = c2_sealed[c2_sealed["status"] == "WARN"]

    lines = [
        "# Data-Source Phase C Follow-up — Slice Drift / Adj-CA",
        "",
        f"Generated: `{generated}`",
        "Status: **OPS RESEARCH** — Soft-Frozen **KEEP** · no e21 primary rewrite · Yahoo TAIEX failover **opt-in only**",
        "",
        "## Inputs",
        "",
        f"- C1: `{C1_CSV.relative_to(ROOT)}`",
        f"- C2: `{C2_CSV.relative_to(ROOT)}`",
        "",
        "## Sealed_2023_plus C1 (live close vs Yahoo)",
        "",
        "| Code | N | MAD | Corr | Status |",
        "|---|---:|---:|---:|---|",
    ]
    for _, r in c1_sealed.iterrows():
        lines.append(
            f"| `{r['code']}` | {int(r['n'])} | "
            f"{'n/a' if pd.isna(r['mad']) else f'{r['mad']:.5f}'} | "
            f"{'n/a' if pd.isna(r['corr']) else f'{r['corr']:.4f}'} | {r['status']} |"
        )
    lines += [
        "",
        f"**C1 sealed DRIFT count:** {len(c1_drift)}"
        + (f" → `{', '.join(c1_drift['code'].astype(str))}`" if len(c1_drift) else " (none)"),
        "",
        "## Sealed_2023_plus C2 (adj returns)",
        "",
        "| Code | N | MAD | Corr | Status |",
        "|---|---:|---:|---:|---|",
    ]
    for _, r in c2_sealed.iterrows():
        lines.append(
            f"| `{r['code']}` | {int(r['n'])} | "
            f"{'n/a' if pd.isna(r['mad']) else f'{r['mad']:.5f}'} | "
            f"{'n/a' if pd.isna(r['corr']) else f'{r['corr']:.4f}'} | {r['status']} |"
        )
    lines += [
        "",
        f"**C2 sealed WARN count:** {len(c2_warn)}"
        + (f" → `{', '.join(c2_warn['code'].astype(str))}`" if len(c2_warn) else " (none)"),
        "",
        "## Slice rollup (any DRIFT/WARN)",
        "",
        "| Slice | C1 DRIFT codes | C2 WARN codes |",
        "|---|---|---|",
    ]
    for name in SLICES:
        d1 = c1_s[(c1_s.slice == name) & (c1_s.status == "DRIFT")]["code"].astype(str).tolist()
        d2 = c2_s[(c2_s.slice == name) & (c2_s.status == "WARN")]["code"].astype(str).tolist()
        lines.append(f"| `{name}` | {', '.join(d1) if d1 else '—'} | {', '.join(d2) if d2 else '—'} |")
    lines += [
        "",
        "## Non-actions",
        "",
        "- Soft-Frozen KEEP · no silent e21 primary switch · no Goodinfo/Wantgoo/CMoney reopen",
        "- TAIEX Yahoo failover remains **opt-in helper only**",
        "",
        f"Label: `DATA_SOURCE_PHASE_C_FOLLOWUP_{generated[:10]}__SOFT_FROZEN_KEEP`",
        "",
    ]
    md = "\n".join(lines)
    (out_r / "DATA_SOURCE_PHASE_C_FOLLOWUP.md").write_text(md)
    (OPS / "DATA_SOURCE_PHASE_C_FOLLOWUP.md").write_text(md)

    payload = {
        "generated_at_utc": generated,
        "soft_frozen_keep": True,
        "live_wire": False,
        "c1_sealed_drift_codes": c1_drift["code"].astype(str).tolist(),
        "c2_sealed_warn_codes": c2_warn["code"].astype(str).tolist(),
        "artifacts": {
            "c1_slice": str((out_o / "c1_slice_drift.csv").relative_to(ROOT)),
            "c2_slice": str((out_o / "c2_slice_adj_drift.csv").relative_to(ROOT)),
            "report": "research/ops/DATA_SOURCE_PHASE_C_FOLLOWUP.md",
        },
    }
    (out_o / "phase_c_followup_summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    (OPS / "DATA_SOURCE_PHASE_C_FOLLOWUP_SUMMARY.json").write_text(json.dumps(payload, indent=2) + "\n")
    print("DONE phase-C followup", payload["c1_sealed_drift_codes"], payload["c2_sealed_warn_codes"], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
