#!/usr/bin/env python3
"""Refresh E45 observe trailing PAUSE diagnostics (ops only).

Re-reads OPERATING dual-paper NAV tips. Does NOT authorize stitch.
Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN.
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
from e45_paper_harness import BOOK_BLEND_A05, BOOK_BLEND_A25, BOOK_FULL, CLAIM_STATUS

OUT = ROOT / "repro/e45-observe-pause-refresh"
OPS = ROOT / "research/ops"
E45_DIR = ROOT / "research/e45"

ALERT_PP = 3.0
PAUSE_PP = 5.0

OBSERVE_NAV = {
    "CHAL_E45_E3": {
        "base": ROOT / "repro/e45-dual-paper-observe/outputs/base_e16_e18_e22_v2s_daily_nav.csv",
        "chal": ROOT / "repro/e45-dual-paper-observe/outputs/chal_e45_e3_daily_nav.csv",
        "book": BOOK_FULL,
    },
    "BLEND_E45_A25": {
        "base": ROOT / "repro/e45-blend025-dual-paper-observe/outputs/base_e16_e18_e22_v2s_daily_nav.csv",
        "chal": ROOT / "repro/e45-blend025-dual-paper-observe/outputs/blend_e45_a25_daily_nav.csv",
        "book": BOOK_BLEND_A25,
    },
    "BLEND_E45_A05": {
        "base": ROOT / "repro/e45-blend005-dual-paper-observe/outputs/base_e16_e18_e22_v2s_daily_nav.csv",
        "chal": ROOT / "repro/e45-blend005-dual-paper-observe/outputs/blend_e45_a05_daily_nav.csv",
        "book": BOOK_BLEND_A05,
    },
    "SLEEVE_FIN_ONLY_A10": {
        "base": ROOT / "repro/e45-sleeve-local-dual-paper-observe/outputs/base_e16_e18_e22_v2s_daily_nav.csv",
        "chal": ROOT / "repro/e45-sleeve-local-dual-paper-observe/outputs/sleeve_fin_only_a10_daily_nav.csv",
        "book": "SLEEVE_FIN_ONLY_A10",
    },
    "M2_RELOC_BIL_FX_C35": {
        "base": ROOT / "repro/e45-m2-bil-fx-dual-paper-observe/outputs/base_e16_e18_e22_v2s_daily_nav.csv",
        "chal": ROOT / "repro/e45-m2-bil-fx-dual-paper-observe/outputs/m2_reloc_bil_fx_c35_daily_nav.csv",
        "book": "M2_RELOC_BIL_FX_C35",
    },
}


def gate_of(giveback_pp) -> str:
    if giveback_pp is None:
        return "INSUFFICIENT"
    if giveback_pp > PAUSE_PP:
        return "PAUSE_REVIEW"
    if giveback_pp > ALERT_PP:
        return "ALERT"
    return "PASS"


def cagr_series(nav: pd.Series):
    if len(nav) < 2 or float(nav.iloc[0]) <= 0:
        return None
    years = len(nav.pct_change().dropna()) / 252.0
    if years <= 0:
        return None
    return float((nav.iloc[-1] / nav.iloc[0]) ** (1.0 / years) - 1.0)


def giveback_at(base: pd.DataFrame, chal: pd.DataFrame, asof: pd.Timestamp, window: str) -> dict:
    start = pd.Timestamp(asof.year, 1, 1) if window == "ytd" else asof - pd.Timedelta(days=365)
    b = base[(base["date"] >= start) & (base["date"] <= asof)].reset_index(drop=True)
    c = chal[(chal["date"] >= start) & (chal["date"] <= asof)].reset_index(drop=True)
    if len(b) < 20 or len(c) < 20:
        return {
            "asof": asof.date().isoformat(),
            "window": window,
            "n_days": int(min(len(b), len(c))),
            "cagr_giveback_pp": None,
            "gate": "INSUFFICIENT",
        }
    bn = b["nav"] / float(b["nav"].iloc[0])
    cn = c["nav"] / float(c["nav"].iloc[0])
    bc, cc = cagr_series(bn), cagr_series(cn)
    gb = None if bc is None or cc is None else (bc - cc) * 100.0
    return {
        "asof": asof.date().isoformat(),
        "window": window,
        "n_days": int(min(len(b), len(c))),
        "cagr_giveback_pp": gb,
        "gate": gate_of(gb),
    }


def month_ends(nav: pd.DataFrame):
    d = nav.copy()
    d["ym"] = d["date"].dt.to_period("M")
    ends = d.groupby("ym", sort=True)["date"].max()
    return [ts for ts in ends.tolist() if ts >= pd.Timestamp("2023-01-01")]


def main() -> int:
    for d in (OUT / "outputs", OUT / "reports", OPS, E45_DIR):
        d.mkdir(parents=True, exist_ok=True)
    generated = datetime.now(timezone.utc).isoformat()

    rows: list[dict] = []
    tip_rows: list[dict] = []
    for sleeve, meta in OBSERVE_NAV.items():
        if not meta["base"].exists() or not meta["chal"].exists():
            tip_rows.append({"sleeve": sleeve, "ok": False, "reason": "missing_nav"})
            continue
        base = pd.read_csv(meta["base"])
        chal = pd.read_csv(meta["chal"])
        base["date"] = pd.to_datetime(base["date"])
        chal["date"] = pd.to_datetime(chal["date"])
        base = base.sort_values("date").reset_index(drop=True)
        chal = chal.sort_values("date").reset_index(drop=True)
        asofs = month_ends(chal)
        hist = []
        for asof in asofs:
            for w in ("ytd", "trailing_1y"):
                row = giveback_at(base, chal, asof, w)
                row.update({"sleeve": sleeve, "book": meta["book"]})
                rows.append(row)
                hist.append(row)
        tip = asofs[-1] if asofs else None
        by_asof: dict[str, dict] = {}
        for r in hist:
            by_asof.setdefault(r["asof"], {})[r["window"]] = r
        first_clean = None
        near_clean = None
        months_pause_both = 0
        for a, gates in sorted(by_asof.items()):
            y = gates.get("ytd", {})
            t = gates.get("trailing_1y", {})
            if y.get("gate") == "PASS" and t.get("gate") == "PASS" and first_clean is None:
                first_clean = a
            if y.get("gate") in ("PASS", "ALERT") and t.get("gate") in ("PASS", "ALERT") and near_clean is None:
                near_clean = a
            if y.get("gate") == "PAUSE_REVIEW" and t.get("gate") == "PAUSE_REVIEW":
                months_pause_both += 1
        tip_ytd = by_asof.get(tip.date().isoformat(), {}).get("ytd") if tip is not None else None
        tip_1y = by_asof.get(tip.date().isoformat(), {}).get("trailing_1y") if tip is not None else None
        ytd_hist = [r for r in hist if r["window"] == "ytd"]
        y1_hist = [r for r in hist if r["window"] == "trailing_1y"]
        tip_rows.append(
            {
                "sleeve": sleeve,
                "ok": True,
                "book": meta["book"],
                "tip_asof": tip.date().isoformat() if tip is not None else None,
                "tip_ytd_gate": tip_ytd["gate"] if tip_ytd else None,
                "tip_trailing_1y_gate": tip_1y["gate"] if tip_1y else None,
                "tip_ytd_giveback_pp": tip_ytd["cagr_giveback_pp"] if tip_ytd else None,
                "tip_1y_giveback_pp": tip_1y["cagr_giveback_pp"] if tip_1y else None,
                "share_pause_ytd": float(np.mean([r["gate"] == "PAUSE_REVIEW" for r in ytd_hist])) if ytd_hist else None,
                "share_pause_1y": float(np.mean([r["gate"] == "PAUSE_REVIEW" for r in y1_hist])) if y1_hist else None,
                "first_clean_both_asof": first_clean,
                "first_near_clean_both_asof": near_clean,
                "months_both_pause": months_pause_both,
            }
        )

    ts = pd.DataFrame(rows)
    tip_df = pd.DataFrame(tip_rows)
    ts.to_csv(OUT / "outputs/observe_pause_timeseries.csv", index=False)
    tip_df.to_csv(OUT / "outputs/observe_pause_tip_summary.csv", index=False)

    lines = [
        "# E45 Observe Trailing PAUSE Refresh",
        "",
        f"Generated: `{generated}`",
        "Status: **OBSERVE DIAGNOSTIC ONLY** — does **not** authorize stitch",
        f"Soft-Frozen `{list(SOFT_FROZEN_FIN_CLIP)}` KEEP · DEFAULT KEEP · stitch **FORBIDDEN**",
        f"Retired MDD narrative: **`{CLAIM_STATUS}`** (do not invent a replacement)",
        "",
        f"Gates: YTD / trailing_1y CAGR giveback vs BASE — ALERT >{ALERT_PP:.0f}pp · PAUSE_REVIEW >{PAUSE_PP:.0f}pp.",
        "",
        "## Tip snapshot",
        "",
        "| Sleeve | Tip asof | YTD gate | 1y gate | YTD giveback | 1y giveback | Share PAUSE YTD | Share PAUSE 1y | First clean both | Months both PAUSE |",
        "|---|---|---|---|---:|---:|---:|---:|---|---:|",
    ]
    for _, r in tip_df.iterrows():
        if not r.get("ok", True):
            lines.append(f"| `{r['sleeve']}` | n/a | MISSING | MISSING | n/a | n/a | n/a | n/a | n/a | n/a |")
            continue
        def fmt(x):
            return "n/a" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:+.2f}"
        lines.append(
            f"| `{r['sleeve']}` | {r['tip_asof']} | **{r['tip_ytd_gate']}** | **{r['tip_trailing_1y_gate']}** | "
            f"{fmt(r['tip_ytd_giveback_pp'])} | {fmt(r['tip_1y_giveback_pp'])} | "
            f"{100*r['share_pause_ytd']:.0f}% | {100*r['share_pause_1y']:.0f}% | "
            f"{r['first_clean_both_asof'] or 'none yet'} | {int(r['months_both_pause'])} |"
        )

    any_clean = any(bool(r.get("first_clean_both_asof")) for _, r in tip_df.iterrows() if r.get("ok"))
    tip_pauseish = tip_df[tip_df.get("ok", True) == True] if "ok" in tip_df else tip_df
    n_pause = int(
        tip_pauseish["tip_ytd_gate"].isin(["PAUSE_REVIEW", "ALERT"]).sum()
        if len(tip_pauseish) and "tip_ytd_gate" in tip_pauseish
        else 0
    )

    lines += [
        "",
        "## Read",
        "",
        f"- Tip still mostly ALERT/PAUSE on YTD ({n_pause}/{len(tip_pauseish)} sleeves).",
        (
            "- Historical `first_clean_both` exists on some sleeves then **relapsed** — not a live stitch signal."
            if any_clean
            else "- `first_clean_both_asof = none yet` on all sleeves ⇒ **no stitch discussion** from trailing gates."
        ),
        "- Diagnostic only; stitch remains FORBIDDEN until a dedicated second human ACCEPT.",
        "",
        "## Non-actions",
        "",
        "- No Soft-Frozen / DEFAULT flip · no HIGH_BETA OPEN · no invented replacement for the retired MDD narrative",
        "",
        f"Label: `E45_OBSERVE_PAUSE_REFRESH_{generated[:10]}__STITCH_FORBIDDEN`",
        "",
    ]
    md = "\n".join(lines)
    for dest in (
        OUT / "reports/E45_OBSERVE_PAUSE_REFRESH.md",
        OPS / "E45_OBSERVE_PAUSE_REFRESH.md",
        E45_DIR / "E45_OBSERVE_PAUSE_REFRESH.md",
        OPS / "E45_OBSERVE_PAUSE_DIAGNOSTICS.md",  # keep tip doc current
        E45_DIR / "E45_OBSERVE_PAUSE_DIAGNOSTICS.md",
    ):
        dest.write_text(md)

    payload = {
        "generated_at_utc": generated,
        "claim_status": CLAIM_STATUS,
        "soft_frozen_keep": list(SOFT_FROZEN_FIN_CLIP),
        "default_books_keep": "E22_v2s_tw",
        "stitch": "FORBIDDEN",
        "tips": tip_rows,
        "artifacts": {
            "report": "research/ops/E45_OBSERVE_PAUSE_REFRESH.md",
            "timeseries": str((OUT / "outputs/observe_pause_timeseries.csv").relative_to(ROOT)),
        },
    }
    (OUT / "outputs/observe_pause_refresh_summary.json").write_text(json.dumps(payload, indent=2) + "\n")
    (OPS / "E45_OBSERVE_PAUSE_REFRESH_SUMMARY.json").write_text(json.dumps(payload, indent=2) + "\n")
    print("DONE observe pause refresh", flush=True)
    for r in tip_rows:
        if r.get("ok"):
            print(r["sleeve"], r["tip_asof"], r["tip_ytd_gate"], r["tip_trailing_1y_gate"], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
