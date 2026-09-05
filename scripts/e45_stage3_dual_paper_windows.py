#!/usr/bin/env python3
"""E45 Stage-3 dual-paper window design metrics (RESEARCH ONLY).

Compares Soft-Frozen early-stack BASE (E16+E18+E22_v2s) vs E45_E3 overlay
across fixed calendar windows. Does NOT live-wire, Soft-Frozen flip, or
rewrite forward/e21 history.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from e50_early_stack_combined_nav import ALL, e16_features, simulate_core, nav_stats
import e45_crisis_core as e45

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/e45-dual-paper-observe-design"
REPORT = ROOT / "research/e45/E45_DUAL_PAPER_OBSERVE_DESIGN.md"

WINDOWS = {
    "full": (None, None),
    "oof_2011_2018": ("2011-01-01", "2018-12-31"),
    "validation_2019_2022": ("2019-01-01", "2022-12-31"),
    "sealed_2023_plus": ("2023-01-01", None),
    "heldout_2019_plus": ("2019-01-01", None),
}


def _slice(nav: pd.DataFrame, start: str | None, end: str | None) -> pd.DataFrame:
    d = nav.copy()
    d["date"] = pd.to_datetime(d["date"])
    if start:
        d = d[d["date"] >= pd.Timestamp(start)]
    if end:
        d = d[d["date"] <= pd.Timestamp(end)]
    return d.reset_index(drop=True)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)

    market = pd.read_csv(ROOT / "forward/e21/live_market.csv", dtype={"code": str})
    market["date"] = pd.to_datetime(market["date"])
    req = set(ALL + ["TAIEX"])
    ok = market.groupby("date")["code"].apply(lambda s: req.issubset(set(s)))
    market = market[market["date"].isin(ok[ok].index)].sort_values(["date", "code"])

    div_path = ROOT / "data/dividend_events/e22_dividend_events.csv"
    div = pd.read_csv(div_path, dtype={"code": str}) if div_path.exists() else pd.DataFrame()

    _p, _s, target, regime = e16_features(market)
    close_eq = (
        market[market["code"].isin(ALL)]
        .pivot(index="date", columns="code", values="close")
        .sort_index()
        .ffill()
    )
    e45_e3 = e45.compute_exposure(close_eq, "E3_VOLTARGET_WINNER")["exposure"]

    books = {
        "BASE_E16_E18_E22_v2s": dict(apply_e22=True, apply_stock_div=True, e45_exposure=None),
        "CHAL_E45_E3": dict(apply_e22=True, apply_stock_div=True, e45_exposure=e45_e3),
    }

    rows: list[dict] = []
    for book, cfg in books.items():
        nav, _fills, _meta = simulate_core(market, target, regime, div, **cfg)
        for wname, (start, end) in WINDOWS.items():
            part = _slice(nav, start, end)
            st = nav_stats(part)
            rows.append(
                {
                    "book": book,
                    "window": wname,
                    "cagr": st.get("cagr"),
                    "mdd": st.get("max_drawdown"),
                    "vol": st.get("vol"),
                    "utility": st.get("utility"),
                    "n_days": st.get("n_days"),
                    "exact_t1": True,
                    "live_wire": False,
                }
            )

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "outputs" / "dual_paper_window_metrics.csv", index=False)

    def _get(book: str, window: str, field: str):
        hit = df[(df.book == book) & (df.window == window)]
        return None if hit.empty else hit.iloc[0][field]

    deltas = {}
    for w in ("heldout_2019_plus", "sealed_2023_plus", "full"):
        b_mdd = _get("BASE_E16_E18_E22_v2s", w, "mdd")
        c_mdd = _get("CHAL_E45_E3", w, "mdd")
        b_cagr = _get("BASE_E16_E18_E22_v2s", w, "cagr")
        c_cagr = _get("CHAL_E45_E3", w, "cagr")
        deltas[w] = {
            # MDD is negative; challenger - base > 0 means shallower drawdown
            "mdd_improve_pp": None
            if b_mdd is None or c_mdd is None
            else (c_mdd - b_mdd) * 100.0,
            "cagr_giveback_pp": None
            if b_cagr is None or c_cagr is None
            else (b_cagr - c_cagr) * 100.0,
        }

    cost_src = ROOT / "research/v412e2e3/e3_cost_sensitivity.csv"
    if not cost_src.exists():
        cost_src = ROOT / "research/v412e2e3/e3_cost_sensitivity.csv"
    cost_out = None
    if cost_src.exists():
        cost = pd.read_csv(cost_src)
        cost_out = OUT / "outputs" / "lineage_e3_cost_sensitivity.csv"
        cost.to_csv(cost_out, index=False)

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "E45_DUAL_PAPER_OBSERVE_DESIGN",
        "status": "DESIGN_ONLY_NOT_OPERATING",
        "live_wire": False,
        "soft_frozen_keep": [0.50, 0.95],
        "default_books_keep": "E22_v2s_tw",
        "claim_mdd_status": "NOT_VERIFIED",
        "books": list(books),
        "windows": list(WINDOWS),
        "deltas_vs_base": deltas,
        "metrics_csv": str(OUT.relative_to(ROOT) / "outputs/dual_paper_window_metrics.csv"),
        "cost_csv": str(cost_out.relative_to(ROOT)) if cost_out else None,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    def pct(x):
        return "n/a" if x is None else f"{100 * x:.2f}%"

    def pp(x):
        return "n/a" if x is None else f"{x:.2f}"

    lines = [
        "# E45 Dual-Paper Observe — Design Pack (Stage 3)",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        "Status: **DESIGN ONLY — NOT OPERATING**",
        "Live stitch: **FORBIDDEN** · Soft-Frozen **[0.50, 0.95] KEEP** · DEFAULT books **`E22_v2s_tw` KEEP**",
        "Claimed MDD ≈ −13.16%: **`NOT_VERIFIED`** (do not invent a replacement)",
        "",
        "## Locked paper books",
        "",
        "| Book | Definition |",
        "|---|---|",
        "| `BASE_E16_E18_E22_v2s` | Soft-Frozen early-stack Exact T+1 + E22_v2s formal books |",
        "| `CHAL_E45_E3` | Same stack + E45 `E3_VOLTARGET_WINNER` exposure overlay (challenger) |",
        "",
        "## Window metrics (Exact T+1; paper only)",
        "",
        "| Book | Window | CAGR | MDD | n_days |",
        "|---|---|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['book']} | {r['window']} | {pct(r['cagr'])} | {pct(r['mdd'])} | {r['n_days']} |"
        )
    lines += [
        "",
        "## Deltas vs BASE (challenger − base)",
        "",
        "| Window | MDD Δ (pp; + = shallower drawdown) | CAGR giveback (pp) |",
        "|---|---:|---:|",
    ]
    for w, d in deltas.items():
        lines.append(f"| {w} | {pp(d['mdd_improve_pp'])} | {pp(d['cagr_giveback_pp'])} |")
    lines += [
        "",
        "## Ops checklist (design → future observe)",
        "",
        "1. Soft-Frozen live default stays BASE until a **separate** human cutover/stitch PR",
        "2. If observe is opened later: run BASE + CHAL_E45_E3 paper ledgers in parallel month-end",
        "3. Re-check trailing YTD / 1y PAUSE gates each month-end (observe ≠ promote)",
        "4. Do **not** silent-edit Soft-Frozen; do **not** rewrite `forward/e21` history",
        "5. Observe sleeve ≠ stitch license; V1–V6 still gate any live stitch",
        "6. Never cite −13.16% as verified; use dated lineage / challenger MDDs only",
        "",
        "## Explicit non-goals",
        "",
        "- Auto live-wire from this design pack",
        "- Soft-Frozen clip flip",
        "- Four-layer live stitch",
        "- Bundling FIN50 / L4 / BLEND / odd-lot / tax DEFAULT promote",
        "- Closing V1 by inventing an MDD",
        "",
        "## V4 / V5 attachment",
        "",
        f"- V4: lineage E3 cost sensitivity attached → `{summary['cost_csv']}` (E45-named seal still open)",
        "- V5: multi-window table above; lineage multi-val windows already dated — E45-named multi-crisis seal still open",
        "",
        "## Artifacts",
        "",
        f"- `{summary['metrics_csv']}`",
        "- `repro/e45-dual-paper-observe-design/summary.json`",
        "- This memo: `research/e45/E45_DUAL_PAPER_OBSERVE_DESIGN.md`",
        "- Checklist: `research/ops/E45_DUAL_PAPER_OBSERVE_CHECKLIST.md`",
        "",
        "## Label",
        "",
        "`E45_DUAL_PAPER_OBSERVE_DESIGN_2026-09-05__NOT_OPERATING__STITCH_FORBIDDEN`",
        "",
    ]
    REPORT.write_text("\n".join(lines) + "\n")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
