#!/usr/bin/env python3
"""Live Soft-Frozen (forward/e21) vs dual-paper BASE recon — RESEARCH / OPS only.

Compares overlapping calendar dates between:
  - live:  forward/e21/nav.csv (+ signals weights when present)
  - paper: repro/l4-dd-path-dual-paper/outputs/base_e16_daily_nav.csv

Does NOT change Soft-Frozen clip.
Does NOT live-wire challengers.
Does NOT rewrite forward/e21 history.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LIVE_NAV = ROOT / "forward/e21/nav.csv"
LIVE_SIG = ROOT / "forward/e21/signals.csv"
PAPER_NAV = ROOT / "repro/l4-dd-path-dual-paper/outputs/base_e16_daily_nav.csv"
OUT_DIR = ROOT / "research/ops"


def _load_nav(path: Path, nav_col: str) -> pd.DataFrame:
    d = pd.read_csv(path)
    d["date"] = pd.to_datetime(d["date"]).dt.normalize()
    d = d.sort_values("date").drop_duplicates("date", keep="last")
    d["nav"] = pd.to_numeric(d[nav_col], errors="coerce")
    return d[["date", "nav"]].dropna()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live-nav", type=Path, default=LIVE_NAV)
    ap.add_argument("--paper-nav", type=Path, default=PAPER_NAV)
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = ap.parse_args()

    if not args.live_nav.exists():
        raise SystemExit(f"missing live nav: {args.live_nav}")
    if not args.paper_nav.exists():
        raise SystemExit(f"missing paper nav: {args.paper_nav}")

    live = _load_nav(args.live_nav, "nav_e16_e18")
    paper = _load_nav(args.paper_nav, "nav")

    # Index each book to 1.0 on first overlap date for return comparison.
    merged = live.merge(paper, on="date", how="inner", suffixes=("_live", "_paper"))
    n_overlap = int(len(merged))

    weight_note = None
    if LIVE_SIG.exists():
        sig = pd.read_csv(LIVE_SIG)
        wcols = [c for c in sig.columns if c.startswith("e16_") or c in ("financial", "telecom", "etf_0050")]
        weight_note = {
            "signal_rows": int(len(sig)),
            "signal_date_min": str(pd.to_datetime(sig["date"]).min().date()) if len(sig) else None,
            "signal_date_max": str(pd.to_datetime(sig["date"]).max().date()) if len(sig) else None,
            "weight_cols_present": wcols[:12],
        }

    rel = None
    live_ret = None
    paper_ret = None
    max_abs_nav_gap = None
    if n_overlap >= 2:
        m = merged.copy()
        m["live_idx"] = m["nav_live"] / float(m["nav_live"].iloc[0])
        m["paper_idx"] = m["nav_paper"] / float(m["nav_paper"].iloc[0])
        m["idx_gap"] = m["live_idx"] - m["paper_idx"]
        live_ret = float(m["live_idx"].iloc[-1] - 1.0)
        paper_ret = float(m["paper_idx"].iloc[-1] - 1.0)
        max_abs_nav_gap = float(m["idx_gap"].abs().max())
        rel = {
            "overlap_start": str(m["date"].iloc[0].date()),
            "overlap_end": str(m["date"].iloc[-1].date()),
            "live_cum_return": live_ret,
            "paper_cum_return": paper_ret,
            "cum_return_gap": live_ret - paper_ret,
            "max_abs_indexed_nav_gap": max_abs_nav_gap,
        }

    # Soft expectation: books are related but not identical (live may use
    # different capital path / pending fills). Flag large indexed drift only.
    alerts: list[str] = []
    if n_overlap == 0:
        alerts.append("NO_OVERLAP: live and paper BASE share no calendar dates")
    elif n_overlap < 5:
        alerts.append(f"THIN_OVERLAP: only {n_overlap} shared sessions — not decision-grade")
    if max_abs_nav_gap is not None and max_abs_nav_gap > 0.02:
        alerts.append(
            f"INDEX_DRIFT: max |live_idx-paper_idx|={max_abs_nav_gap:.4%} > 2% on overlap"
        )

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "LIVE_VS_PAPER_SOFT_FROZEN_RECON",
        "live_wire": False,
        "soft_frozen_clip": [0.50, 0.95],
        "soft_frozen_unchanged": True,
        "paths": {
            "live_nav": str(args.live_nav),
            "paper_nav": str(args.paper_nav),
        },
        "live": {
            "n": int(len(live)),
            "start": str(live["date"].min().date()) if len(live) else None,
            "end": str(live["date"].max().date()) if len(live) else None,
            "last_nav": float(live["nav"].iloc[-1]) if len(live) else None,
        },
        "paper_base": {
            "n": int(len(paper)),
            "start": str(paper["date"].min().date()) if len(paper) else None,
            "end": str(paper["date"].max().date()) if len(paper) else None,
            "last_nav": float(paper["nav"].iloc[-1]) if len(paper) else None,
        },
        "overlap_n": n_overlap,
        "overlap_stats": rel,
        "signals": weight_note,
        "alerts": alerts,
        "note": (
            "Research/ops recon only. Short live windows are expected. "
            "Do not use thin overlap for cutover. Soft-Frozen clip untouched."
        ),
    }

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / "LIVE_PAPER_RECON.json"
    out_md = out_dir / "LIVE_PAPER_RECON.md"
    out_json.write_text(json.dumps(payload, indent=2) + "\n")

    lines = [
        "# Live vs Paper Soft-Frozen Recon",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Status: **RESEARCH / OPS** — Soft-Frozen clip **[0.50, 0.95] unchanged**.",
        "",
        "## Coverage",
        "",
        "| Book | Start | End | N | Last NAV |",
        "|---|---|---|---:|---:|",
        f"| Live `forward/e21` | {payload['live']['start']} | {payload['live']['end']} | {payload['live']['n']} | {payload['live']['last_nav']} |",
        f"| Paper BASE | {payload['paper_base']['start']} | {payload['paper_base']['end']} | {payload['paper_base']['n']} | {payload['paper_base']['last_nav']} |",
        f"| Overlap | | | **{n_overlap}** | |",
        "",
    ]
    if rel:
        lines += [
            "## Overlap indexed returns (rebased to 1.0 on first overlap date)",
            "",
            f"- Window: `{rel['overlap_start']}` → `{rel['overlap_end']}`",
            f"- Live cum return: **{rel['live_cum_return']:.4%}**",
            f"- Paper BASE cum return: **{rel['paper_cum_return']:.4%}**",
            f"- Gap (live − paper): **{rel['cum_return_gap']:.4%}**",
            f"- Max |indexed NAV gap|: **{rel['max_abs_indexed_nav_gap']:.4%}**",
            "",
        ]
    lines += ["## Alerts", ""]
    if alerts:
        for a in alerts:
            lines.append(f"- `{a}`")
    else:
        lines.append("- None")
    lines += [
        "",
        "## Ops note",
        "",
        "- Re-run: `python3 scripts/e21_live_vs_paper_recon.py`",
        "- Charter: `research/ops/OPS_CONVERGENCE_CHARTER.md`",
        "- Cutover authority remains `research/STRATEGY_DEBT_BOARD.md` — this recon never flips Soft-Frozen.",
        "",
    ]
    out_md.write_text("\n".join(lines))
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
