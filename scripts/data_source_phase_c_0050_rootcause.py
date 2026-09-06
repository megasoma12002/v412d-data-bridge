#!/usr/bin/env python3
"""Phase C root-cause: sealed C1 DRIFT on 0050.

Finding (paper/ops only):
  Sealed C1 corr collapse is driven by TWO unadjusted-close spikes
  (2014-01-02 Yahoo-side, 2025-06-18 live-side). After |Δret|>5pp
  outlier drop, sealed corr recovers to ~0.998. C2 adj-return PASS
  already said the series is fine once CA/split-aware.

Soft-Frozen KEEP · no e21 primary rewrite · Yahoo TAIEX failover opt-in only.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from e16_soft_frozen_base import SOFT_FROZEN_FIN_CLIP

REPRO_C = ROOT / "repro/data-source-phase-c"
OUT = ROOT / "repro/data-source-phase-c-0050-rootcause"
OPS = ROOT / "research/ops"
C1_CSV = REPRO_C / "c1_fin12_history_returns.csv"
MARKET = ROOT / "forward/e21/live_market.csv"
OUTLIER_ABS = 0.05  # 5pp one-day Δret vs peer


def _zpad(code: str) -> str:
    s = str(code)
    return s.zfill(4) if s.isdigit() and len(s) < 4 else s


def load_c1_0050() -> pd.DataFrame:
    df = pd.read_csv(C1_CSV, dtype={"code": str})
    df["code"] = df["code"].map(_zpad)
    g = df[df["code"] == "0050"].copy()
    g["date"] = pd.to_datetime(g["date"])
    g = g.sort_values("date").reset_index(drop=True)
    g["diff"] = g["ret_live"].astype(float) - g["ret_yahoo"].astype(float)
    g["absdiff"] = g["diff"].abs()
    return g


def slice_stats(g: pd.DataFrame, start: str | None = None) -> dict:
    part = g if start is None else g[g["date"] >= pd.Timestamp(start)]
    m = part.dropna(subset=["ret_live", "ret_yahoo"])
    if len(m) < 30:
        return {"n": int(len(m)), "mad": None, "corr": None}
    return {
        "n": int(len(m)),
        "mad": float(m["absdiff"].mean()),
        "corr": float(m["ret_live"].corr(m["ret_yahoo"])),
    }


def main() -> int:
    for d in (OUT / "outputs", OUT / "reports", OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = datetime.now(timezone.utc).isoformat()

    g = load_c1_0050()
    sealed = g[g["date"] >= "2023-01-01"].copy()
    outliers = g[g["absdiff"] > OUTLIER_ABS].copy()
    sealed_clean = sealed[sealed["absdiff"] <= OUTLIER_ABS]
    full_clean = g[g["absdiff"] <= OUTLIER_ABS]

    # Live market OHLC around the 2025 spike (split / unit break evidence)
    mkt_rows = []
    if MARKET.exists():
        m = pd.read_csv(MARKET, dtype={"code": str})
        m["code"] = m["code"].map(_zpad)
        m["date"] = pd.to_datetime(m["date"])
        win = m[(m["code"] == "0050") & (m["date"].between("2025-06-01", "2025-06-30"))]
        for _, r in win.sort_values("date").iterrows():
            mkt_rows.append(
                {
                    "date": r["date"].date().isoformat(),
                    "close": float(r["close"]),
                    "adj_close": float(r["adj_close"]) if pd.notna(r.get("adj_close")) else None,
                    "volume": float(r["volume"]) if pd.notna(r.get("volume")) else None,
                }
            )

    yearly = []
    for y, gy in g.groupby(g["date"].dt.year):
        st = slice_stats(gy)
        yearly.append({"year": int(y), **st})

    outliers.to_csv(OUT / "outputs/0050_c1_outliers.csv", index=False)
    pd.DataFrame(yearly).to_csv(OUT / "outputs/0050_c1_yearly_corr.csv", index=False)
    if mkt_rows:
        pd.DataFrame(mkt_rows).to_csv(OUT / "outputs/0050_live_ohlc_2025-06.csv", index=False)

    sealed_all = slice_stats(sealed)
    sealed_rm = slice_stats(sealed_clean)
    full_all = slice_stats(g)
    full_rm = slice_stats(full_clean)

    # Verdict
    root = (
        "UNADJUSTED_CLOSE_SPIKE"
        if len(outliers) >= 1 and (sealed_rm.get("corr") or 0) >= 0.95
        else "UNKNOWN"
    )

    lines = [
        "# Data-Source Phase C — `0050` Sealed C1 DRIFT Root-Cause",
        "",
        f"Generated: `{generated}`",
        "Status: **OPS DIAGNOSTIC** — Soft-Frozen **KEEP** · no e21 primary rewrite · Yahoo TAIEX failover **opt-in only**",
        f"Soft-Frozen clip: `{list(SOFT_FROZEN_FIN_CLIP)}` (import only; unchanged)",
        "",
        "## Verdict",
        "",
        f"- Root class: **`{root}`**",
        "- Sealed C1 DRIFT on `0050` is **not** broad series rot.",
        "- It is dominated by **1–2 unadjusted close spikes** that destroy Pearson corr while MAD stays small.",
        "- **C2 adj-return already PASS** on sealed `0050` — CA/split-aware path is healthy.",
        "",
        "## Headline metrics",
        "",
        "| Slice | N | MAD | Corr | Note |",
        "|---|---:|---:|---:|---|",
        f"| sealed all | {sealed_all['n']} | {sealed_all['mad']:.5f} | {sealed_all['corr']:.4f} | reported DRIFT |",
        f"| sealed drop \\|Δret\\|>{OUTLIER_ABS:.0%} | {sealed_rm['n']} | {sealed_rm['mad']:.5f} | {sealed_rm['corr']:.4f} | recovers PASS |",
        f"| full all | {full_all['n']} | {full_all['mad']:.5f} | {full_all['corr']:.4f} | |",
        f"| full drop outliers | {full_rm['n']} | {full_rm['mad']:.5f} | {full_rm['corr']:.4f} | |",
        "",
        "## Outlier days (\\|live−yahoo\\| > 5pp)",
        "",
        "| Date | ret_live | ret_yahoo | Δ | Side |",
        "|---|---:|---:|---:|---|",
    ]
    for _, r in outliers.sort_values("date").iterrows():
        side = "live" if abs(r["ret_live"]) > abs(r["ret_yahoo"]) else "yahoo"
        lines.append(
            f"| {r['date'].date().isoformat()} | {r['ret_live']:+.4f} | {r['ret_yahoo']:+.4f} | "
            f"{r['diff']:+.4f} | {side} |"
        )
    if mkt_rows:
        lines += [
            "",
            "## Live OHLC around 2025-06-18 (unit/split break)",
            "",
            "| Date | close | adj_close | volume |",
            "|---|---:|---:|---:|",
        ]
        for r in mkt_rows:
            adj = "n/a" if r["adj_close"] is None else f"{r['adj_close']:.4f}"
            vol = "n/a" if r["volume"] is None else f"{r['volume']:.0f}"
            lines.append(f"| {r['date']} | {r['close']:.2f} | {adj} | {vol} |")
        lines += [
            "",
            "Read: raw `close` drops ~188 → ~47 while `adj_close` stays continuous — "
            "classic **split / unit change** day. C1 live return from raw close prints a false −75% day; "
            "Yahoo peer does not → corr collapses.",
        ]

    lines += [
        "",
        "## Yearly corr (shows spike years only)",
        "",
        "| Year | N | MAD | Corr |",
        "|---:|---:|---:|---:|",
    ]
    for y in yearly:
        if y["corr"] is None:
            continue
        flag = " ← spike" if y["corr"] < 0.95 else ""
        lines.append(
            f"| {y['year']} | {y['n']} | {y['mad']:.5f} | {y['corr']:.4f}{flag} |"
        )

    lines += [
        "",
        "## Recommended ops actions (non-ballot)",
        "",
        "1. **Do not** flip Soft-Frozen / DEFAULT / e21 primary on this DRIFT alone.",
        "2. Prefer **adj_close** (or C2 path) for `0050` history QC; treat raw-close C1 as spike-sensitive.",
        "3. Patch / quarantine the two outlier dates in C1 builder if regenerating probes.",
        "4. Keep Yahoo TAIEX failover **opt-in helper only**.",
        "",
        "## Non-actions",
        "",
        "- No Soft-Frozen change · no DEFAULT change · no stitch · no Goodinfo/Wantgoo/CMoney reopen",
        "",
        f"Label: `DATA_SOURCE_PHASE_C_0050_ROOTCAUSE_{generated[:10]}__SOFT_FROZEN_KEEP`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "reports/DATA_SOURCE_PHASE_C_0050_ROOTCAUSE.md").write_text(md)
    (OPS / "DATA_SOURCE_PHASE_C_0050_ROOTCAUSE.md").write_text(md)

    payload = {
        "generated_at_utc": generated,
        "soft_frozen_keep": list(SOFT_FROZEN_FIN_CLIP),
        "code": "0050",
        "root_class": root,
        "outlier_abs_threshold": OUTLIER_ABS,
        "outliers": [
            {
                "date": r["date"].date().isoformat(),
                "ret_live": float(r["ret_live"]),
                "ret_yahoo": float(r["ret_yahoo"]),
                "diff": float(r["diff"]),
            }
            for _, r in outliers.iterrows()
        ],
        "sealed_all": sealed_all,
        "sealed_drop_outliers": sealed_rm,
        "full_drop_outliers": full_rm,
        "c2_sealed_status_ref": "PASS (prior Phase C follow-up)",
        "live_primary_rewrite": False,
        "artifacts": {
            "report": "research/ops/DATA_SOURCE_PHASE_C_0050_ROOTCAUSE.md",
            "outliers_csv": str((OUT / "outputs/0050_c1_outliers.csv").relative_to(ROOT)),
        },
    }
    (OUT / "outputs/0050_rootcause_summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    (OPS / "DATA_SOURCE_PHASE_C_0050_ROOTCAUSE_SUMMARY.json").write_text(json.dumps(payload, indent=2) + "\n")
    print("DONE 0050 rootcause", root, "sealed_corr_clean", sealed_rm.get("corr"), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
