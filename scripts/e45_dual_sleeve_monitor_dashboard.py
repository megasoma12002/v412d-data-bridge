#!/usr/bin/env python3
"""E45 dual-sleeve long monitor dashboard (roadmap #7).

Joins operating FULL_E45 + BLEND_A25 month-end monitors and adds a paper-only
α=0.10 companion series (NOT an OPEN observe sleeve).

Does NOT edit Soft-Frozen / DEFAULT / authorize stitch / open new observe.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from research_metric_helpers import mdd_delta_pp, cagr_delta_pp
from e50_early_stack_combined_nav import ALL, e16_features, nav_stats, simulate_core
import e45_crisis_core as e45

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/e45-dual-sleeve-monitor-dashboard"
RESEARCH = ROOT / "research/e45"
OPS = ROOT / "research/ops"
MARKET_PATH = ROOT / "forward/e21/live_market.csv"
DIV_PATH = ROOT / "data/dividend_events/e22_dividend_events.csv"
FULL_JSON = ROOT / "research/gaps/E45_MONTH_END_MONITOR.json"
BLEND_JSON = ROOT / "research/gaps/E45_BLEND025_MONTH_END_MONITOR.json"
FULL_CSV = ROOT / "repro/e45-dual-paper-observe/month_end/month_end_windows.csv"
BLEND_CSV = ROOT / "repro/e45-blend025-dual-paper-observe/month_end/month_end_windows.csv"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text()) if path.exists() else {}


def pp(x):
    return "n/a" if x is None else f"{x:+.2f}"


def slice_stats(nav: pd.DataFrame, start, end) -> dict:
    d = nav.copy()
    d["date"] = pd.to_datetime(d["date"])
    d = d[(d["date"] >= start) & (d["date"] <= end)].reset_index(drop=True)
    if len(d) < 30:
        return {"cagr": None, "max_drawdown": None, "n_days": int(len(d))}
    d = d.copy()
    d["nav"] = d["nav"] / float(d["nav"].iloc[0])
    st = nav_stats(d)
    st["n_days"] = int(len(d))
    return st


def main() -> None:
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)
    OPS.mkdir(parents=True, exist_ok=True)

    full = load_json(FULL_JSON)
    blend = load_json(BLEND_JSON)

    rows = []
    for label, path in [("FULL_E45", FULL_CSV), ("BLEND_A25", BLEND_CSV)]:
        if path.exists():
            d = pd.read_csv(path)
            d["sleeve"] = label
            rows.append(d)
    win_df = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    if len(win_df):
        win_df.to_csv(OUT / "outputs" / "observe_sleeves_month_end_windows.csv", index=False)

    print("sim paper companion A10 (not observe) ...", flush=True)
    market = pd.read_csv(MARKET_PATH, dtype={"code": str})
    market["date"] = pd.to_datetime(market["date"])
    req = set(ALL + ["TAIEX"])
    ok = market.groupby("date")["code"].apply(lambda s: req.issubset(set(s)))
    market = market[market["date"].isin(ok[ok].index)].sort_values(["date", "code"])
    div = pd.read_csv(DIV_PATH, dtype={"code": str}) if DIV_PATH.exists() else pd.DataFrame()
    _p, _s, target, regime = e16_features(market)
    close = (
        market[market["code"].isin(ALL)]
        .pivot(index="date", columns="code", values="close")
        .sort_index()
        .ffill()
    )
    e45_full = e45.compute_exposure(close, "E3_VOLTARGET_WINNER")["exposure"]
    exp = ((1 - 0.10) + 0.10 * e45_full.astype(float)).clip(0.0, 1.0)
    nav_base, _, _ = simulate_core(
        market, target, regime, div, apply_e22=True, apply_stock_div=True, e45_exposure=None
    )
    nav_a10, _, _ = simulate_core(
        market, target, regime, div, apply_e22=True, apply_stock_div=True, e45_exposure=exp
    )
    nav_base.to_csv(OUT / "outputs" / "paper_base_daily_nav.csv", index=False)
    nav_a10.to_csv(OUT / "outputs" / "paper_blend_a10_daily_nav.csv", index=False)

    asof = min(pd.to_datetime(nav_base["date"]).max(), pd.to_datetime(nav_a10["date"]).max())
    dyn = {
        "ytd": (pd.Timestamp(asof.year, 1, 1), asof),
        "trailing_1y": (asof - pd.Timedelta(days=365), asof),
        "heldout_2019_plus": (pd.Timestamp("2019-01-01"), asof),
        "sealed_2023_plus": (pd.Timestamp("2023-01-01"), asof),
    }
    a10_rows = []
    for w, (a, b) in dyn.items():
        sb, sc = slice_stats(nav_base, a, b), slice_stats(nav_a10, a, b)
        gb = cagr_delta_pp(sb.get("cagr"), sc.get("cagr"), missing_as_zero=True)
        flag = "n/a"
        if w in ("ytd", "trailing_1y") and gb is not None:
            flag = "PAUSE_REVIEW" if gb > 5 else ("ALERT" if gb > 3 else "OK")
        a10_rows.append(
            {
                "sleeve": "PAPER_BLEND_A10",
                "window": w,
                "asof": str(asof.date()),
                "mdd_improve_pp": mdd_delta_pp(sb.get("max_drawdown"), sc.get("max_drawdown")),
                "cagr_giveback_pp": gb,
                "flag": flag,
                "observe_operating": False,
            }
        )
    pd.DataFrame(a10_rows).to_csv(OUT / "outputs" / "paper_a10_pause_windows.csv", index=False)

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PAPER_DASHBOARD",
        "ballot": "E45 PAPER dual-sleeve long monitor dashboard",
        "roadmap_priority": 7,
        "operating_observe_sleeves": ["FULL_E45", "BLEND_A25"],
        "paper_companion_not_observe": ["BLEND_A10"],
        "asof_paper_a10": str(asof.date()),
        "full_observe_asof": full.get("asof"),
        "blend025_observe_asof": blend.get("asof"),
        "full_alerts": full.get("alerts", []),
        "blend025_alerts": blend.get("alerts", []),
        "paper_a10_windows": a10_rows,
        "soft_frozen": "KEEP",
        "live_stitch": "FORBIDDEN",
        "note": "Dashboard only. Does not OPEN α=0.10 observe sleeve.",
    }
    (OUT / "reports" / "e45_dual_sleeve_monitor_dashboard.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )
    (RESEARCH / "E45_DUAL_SLEEVE_MONITOR_DASHBOARD.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    lines = [
        "# E45 Dual-Sleeve Long Monitor Dashboard",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Status: **PAPER DASHBOARD** — Soft-Frozen **KEEP**; stitch **FORBIDDEN**.",
        "Operating observe: **FULL_E45** + **BLEND_A25**. Paper companion **A10** is NOT an OPEN observe sleeve.",
        "",
        "## Operating observe — latest alerts",
        "",
        f"- FULL_E45 asof `{full.get('asof')}`:",
    ]
    for a in full.get("alerts", []) or ["(none)"]:
        lines.append(f"  - {a}")
    lines.append(f"- BLEND_A25 asof `{blend.get('asof')}`:")
    for a in blend.get("alerts", []) or ["(none)"]:
        lines.append(f"  - {a}")

    if len(win_df):
        lines += [
            "",
            "## Operating observe — window table",
            "",
            "| Sleeve | Window | MDD Δpp | Giveback pp |",
            "|---|---|---:|---:|",
        ]
        cols = set(win_df.columns)
        for _, r in win_df.iterrows():
            mdd = r["mdd_improve_pp"] if "mdd_improve_pp" in cols else None
            gb = r["cagr_giveback_pp"] if "cagr_giveback_pp" in cols else None
            lines.append(f"| {r['sleeve']} | {r.get('window')} | {pp(mdd)} | {pp(gb)} |")

    lines += [
        "",
        f"## Paper companion BLEND_A10 (asof {asof.date()}) — NOT OBSERVE",
        "",
        "| Window | MDD Δpp | Giveback pp | Flag |",
        "|---|---:|---:|---|",
    ]
    for r in a10_rows:
        lines.append(
            f"| {r['window']} | {pp(r['mdd_improve_pp'])} | {pp(r['cagr_giveback_pp'])} | **{r['flag']}** |"
        )

    lines += [
        "",
        "## Read-through",
        "",
        "1. Keep FULL vs A25 observe on month-end cadence; both feed stitch gates.",
        "2. A10 companion is research-only after low-α deep-dive; **no OPEN ballot** here.",
        "3. Dashboard does not authorize stitch.",
        "",
        "## Governance",
        "",
        "- Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN · −13.16% RETIRED",
        "- Observe OPEN sleeves unchanged (FULL + A25 only)",
        "",
        "## Reproduce",
        "",
        "```bash",
        "python3 scripts/e45_dual_sleeve_monitor_dashboard.py",
        "```",
        "",
    ]
    memo = "\n".join(lines) + "\n"
    (RESEARCH / "E45_DUAL_SLEEVE_MONITOR_DASHBOARD.md").write_text(memo)
    (OUT / "reports" / "E45_DUAL_SLEEVE_MONITOR_DASHBOARD.md").write_text(memo)
    (OPS / "E45_DUAL_SLEEVE_MONITOR_DASHBOARD.md").write_text(
        "# E45 Dual-Sleeve Monitor Dashboard — Ops pointer\n\n"
        "Ballot: `E45 PAPER dual-sleeve long monitor dashboard` — roadmap #7\n\n"
        "Primary: `research/e45/E45_DUAL_SLEEVE_MONITOR_DASHBOARD.md`\n"
        "Repro: `repro/e45-dual-sleeve-monitor-dashboard/`\n\n"
        "```bash\npython3 scripts/e45_dual_sleeve_monitor_dashboard.py\n```\n"
    )
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
