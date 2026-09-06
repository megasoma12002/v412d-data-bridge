#!/usr/bin/env python3
"""Phase C follow-up: quarantine unadjusted-close spikes on 0050 C1.

Ops / research only. Soft-Frozen KEEP · no e21 primary rewrite.

Produces:
  - quarantine date list for C1 builder
  - C1 metrics before/after quarantine
  - adj_close return probe vs raw-close C1 (if live_market has adj_close)
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT / "scripts"))
from e16_soft_frozen_base import SOFT_FROZEN_FIN_CLIP

REPRO_C = ROOT / "repro/data-source-phase-c"
OUT = ROOT / "repro/data-source-phase-c-0050-quarantine"
OPS = ROOT / "research/ops"
C1_CSV = REPRO_C / "c1_fin12_history_returns.csv"
MARKET = ROOT / "forward/e21/live_market.csv"
OUTLIER_ABS = 0.05
CODE = "0050"


def zpad(code: str) -> str:
    s = str(code)
    return s.zfill(4) if s.isdigit() and len(s) < 4 else s


def stats(live: pd.Series, peer: pd.Series) -> dict:
    m = pd.DataFrame({"a": live, "b": peer}).dropna()
    if len(m) < 30:
        return {"n": int(len(m)), "mad": None, "corr": None}
    d = (m["a"] - m["b"]).abs()
    return {"n": int(len(m)), "mad": float(d.mean()), "corr": float(m["a"].corr(m["b"]))}


def main() -> int:
    for d in (OUT / "outputs", OUT / "reports", OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = datetime.now(timezone.utc).isoformat()

    df = pd.read_csv(C1_CSV, dtype={"code": str})
    df["code"] = df["code"].map(zpad)
    g = df[df["code"] == CODE].copy()
    g["date"] = pd.to_datetime(g["date"])
    g = g.sort_values("date").reset_index(drop=True)
    g["diff"] = g["ret_live"].astype(float) - g["ret_yahoo"].astype(float)
    g["absdiff"] = g["diff"].abs()

    sealed = g[g["date"] >= "2023-01-01"].copy()
    outliers = g[g["absdiff"] > OUTLIER_ABS].copy()
    q_dates = sorted(outliers["date"].dt.strftime("%Y-%m-%d").unique().tolist())
    clean = g[~g["date"].isin(outliers["date"])].copy()
    sealed_clean = sealed[~sealed["date"].isin(outliers["date"])].copy()

    # adj_close probe from live market (optional)
    adj_probe = {"available": False}
    if MARKET.exists():
        m = pd.read_csv(MARKET, dtype={"code": str})
        m["code"] = m["code"].map(zpad)
        m["date"] = pd.to_datetime(m["date"])
        m50 = m[m["code"] == CODE].sort_values("date")
        if "adj_close" in m50.columns and m50["adj_close"].notna().sum() > 100:
            m50 = m50.dropna(subset=["adj_close", "close"]).copy()
            m50["ret_raw"] = m50["close"].astype(float).pct_change()
            m50["ret_adj"] = m50["adj_close"].astype(float).pct_change()
            # join yahoo peer from C1
            peer = g[["date", "ret_yahoo"]].copy()
            j = m50.merge(peer, on="date", how="inner")
            sealed_j = j[j["date"] >= "2023-01-01"]
            adj_probe = {
                "available": True,
                "sealed_raw_vs_yahoo": stats(sealed_j["ret_raw"], sealed_j["ret_yahoo"]),
                "sealed_adj_vs_yahoo": stats(sealed_j["ret_adj"], sealed_j["ret_yahoo"]),
                "n_join_sealed": int(len(sealed_j.dropna(subset=["ret_raw", "ret_adj", "ret_yahoo"]))),
            }

    summary = {
        "generated_utc": generated,
        "code": CODE,
        "soft_frozen_clip": list(SOFT_FROZEN_FIN_CLIP),
        "outlier_abs_threshold": OUTLIER_ABS,
        "quarantine_dates": q_dates,
        "sealed_before": stats(sealed["ret_live"], sealed["ret_yahoo"]),
        "sealed_after_quarantine": stats(sealed_clean["ret_live"], sealed_clean["ret_yahoo"]),
        "full_before": stats(g["ret_live"], g["ret_yahoo"]),
        "full_after_quarantine": stats(clean["ret_live"], clean["ret_yahoo"]),
        "adj_close_probe": adj_probe,
        "recommendation": {
            "prefer_adj_close_or_c2_for_qc": True,
            "quarantine_dates_in_c1_builder": q_dates,
            "flip_soft_frozen": False,
            "rewrite_e21_primary": False,
        },
        "governance": {
            "soft_frozen": "KEEP",
            "default": "KEEP",
            "stitch": "FORBIDDEN",
        },
    }

    outliers.to_csv(OUT / "outputs/0050_c1_quarantine_outliers.csv", index=False)
    pd.DataFrame({"date": q_dates, "action": "QUARANTINE_FROM_C1"}).to_csv(
        OUT / "outputs/0050_c1_quarantine_dates.csv", index=False
    )
    (OUT / "outputs/0050_c1_quarantine_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )

    sb = summary["sealed_before"]
    sa = summary["sealed_after_quarantine"]
    lines = [
        "# Data-Source Phase C — `0050` C1 Quarantine / adj_close Probe",
        "",
        f"Generated: `{generated}`",
        "Status: **OPS PATCH RESEARCH** — Soft-Frozen **KEEP** · no e21 primary rewrite",
        f"Soft-Frozen clip: `{list(SOFT_FROZEN_FIN_CLIP)}` (import only)",
        "",
        "## Quarantine list (C1 builder)",
        "",
        "Drop these dates from raw-close C1 correlation probes (spike days):",
        "",
    ]
    for d in q_dates:
        lines.append(f"- `{d}`")
    lines += [
        "",
        "## Sealed C1 before / after quarantine",
        "",
        "| Slice | N | MAD | Corr |",
        "|---|---:|---:|---:|",
        f"| sealed before | {sb['n']} | {sb['mad']} | {sb['corr']} |",
        f"| sealed after quarantine | {sa['n']} | {sa['mad']} | {sa['corr']} |",
        "",
        "## adj_close probe",
        "",
    ]
    if adj_probe.get("available"):
        rr = adj_probe["sealed_raw_vs_yahoo"]
        ra = adj_probe["sealed_adj_vs_yahoo"]
        lines += [
            "| Probe | N | MAD | Corr |",
            "|---|---:|---:|---:|",
            f"| sealed raw close vs Yahoo | {rr['n']} | {rr['mad']} | {rr['corr']} |",
            f"| sealed adj_close vs Yahoo | {ra['n']} | {ra['mad']} | {ra['corr']} |",
            "",
            "Read: prefer **adj_close / C2** for history QC; raw-close C1 remains spike-sensitive.",
        ]
    else:
        lines.append("_adj_close not available on live_market join — skip probe._")
    lines += [
        "",
        "## Non-actions",
        "",
        "- No Soft-Frozen / DEFAULT flip · no e21 primary rewrite · no stitch · no vendor reopen",
        "",
        f"Label: `DATA_SOURCE_PHASE_C_0050_QUARANTINE_{generated[:10]}__SOFT_FROZEN_KEEP`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "reports/DATA_SOURCE_PHASE_C_0050_QUARANTINE.md").write_text(md)
    (OPS / "DATA_SOURCE_PHASE_C_0050_QUARANTINE.md").write_text(md)
    (OPS / "DATA_SOURCE_PHASE_C_0050_QUARANTINE_SUMMARY.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )
    print(json.dumps({"quarantine_dates": q_dates, "sealed_after": sa}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
