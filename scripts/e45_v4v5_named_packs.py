#!/usr/bin/env python3
"""E45-named V4 cost multiples + V5 crisis-year attribution (RESEARCH ONLY).

Books: BASE_E16_E18_E22_v2s vs CHAL_E45_E3 on Exact T+1 early-stack.
Cost multiples scale BUY_FEE/SELL_FEE/SLIP/TAX_* by 0×/1×/2×/3× (monkeypatch).
Crisis years: 2011(partial)/2015/2018/2020/2022; 2008 documented N/A
(market starts ~2011-12).

No live-wire, Soft-Frozen flip, or forward/e21 rewrite. V1 remains FAIL.
"""
from __future__ import annotations

import json
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e50_early_stack_combined_nav as stack
from e50_early_stack_combined_nav import ALL, e16_features, simulate_core, nav_stats
import e45_crisis_core as e45

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/e45-v4v5-named-packs"
V4_MD = ROOT / "research/ops/E45_V4_COST_STRESS_PACK.md"
V5_MD = ROOT / "research/ops/E45_V5_MULTI_WINDOW_PACK.md"

COST_MULTS = (0, 1, 2, 3)
CRISIS_YEARS = (2011, 2015, 2018, 2020, 2022)
FEE_KEYS = ("BUY_FEE", "SELL_FEE", "SLIP", "TAX_STOCK", "TAX_ETF")


@contextmanager
def fee_multiple(mult: float):
    saved = {k: getattr(stack, k) for k in FEE_KEYS}
    try:
        for k, v in saved.items():
            setattr(stack, k, float(v) * float(mult))
        yield
    finally:
        for k, v in saved.items():
            setattr(stack, k, v)


def year_stats(nav: pd.DataFrame, year: int) -> dict:
    d = nav.copy()
    d["date"] = pd.to_datetime(d["date"])
    part = d[d["date"].dt.year == year].reset_index(drop=True)
    if len(part) < 5:
        return {
            "year": year,
            "n_days": int(len(part)),
            "ret": None,
            "mdd": None,
            "available": False,
            "note": "insufficient days" if len(part) else "no data",
        }
    path = part["nav"].to_numpy(dtype=float)
    ret = float(path[-1] / path[0] - 1.0) if path[0] > 0 else None
    peak = np.maximum.accumulate(path)
    mdd = float(np.min(path / peak - 1.0))
    return {
        "year": year,
        "n_days": int(len(part)),
        "ret": ret,
        "mdd": mdd,
        "available": True,
        "note": "partial_year" if year == 2011 else "",
    }


def pct(x) -> str:
    if x is None or (isinstance(x, float) and (np.isnan(x) or np.isinf(x))):
        return "n/a"
    return f"{100.0 * x:.2f}%"


def pp(x) -> str:
    if x is None or (isinstance(x, float) and (np.isnan(x) or np.isinf(x))):
        return "n/a"
    return f"{x:.2f}"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)

    market = pd.read_csv(ROOT / "forward/e21/live_market.csv", dtype={"code": str})
    market["date"] = pd.to_datetime(market["date"])
    req = set(ALL + ["TAIEX"])
    ok = market.groupby("date")["code"].apply(lambda s: req.issubset(set(s)))
    market = market[market["date"].isin(ok[ok].index)].sort_values(["date", "code"])
    data_start = str(market["date"].min().date())
    data_end = str(market["date"].max().date())

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
    books = {"BASE_E16_E18_E22_v2s": None, "CHAL_E45_E3": e45_e3}

    # ---------- V4 cost multiples ----------
    cost_rows: list[dict] = []
    for mult in COST_MULTS:
        with fee_multiple(mult):
            for book, expo in books.items():
                nav, fills, _meta = simulate_core(
                    market,
                    target,
                    regime,
                    div,
                    apply_e22=True,
                    apply_stock_div=True,
                    e45_exposure=expo,
                )
                st = nav_stats(nav)
                fee_sum = (
                    float(pd.to_numeric(fills["fees_tax"], errors="coerce").fillna(0).sum())
                    if len(fills) and "fees_tax" in fills.columns
                    else 0.0
                )
                cost_rows.append(
                    {
                        "book": book,
                        "cost_multiple": int(mult),
                        "cagr": st.get("cagr"),
                        "mdd": st.get("max_drawdown"),
                        "vol": st.get("vol"),
                        "utility": st.get("utility"),
                        "n_days": st.get("n_days"),
                        "n_fills": int(len(fills)),
                        "fees_tax_sum": fee_sum,
                        "exact_t1": True,
                        "live_wire": False,
                    }
                )

    cost_df = pd.DataFrame(cost_rows)
    cost_csv = OUT / "outputs" / "e45_named_cost_multiples.csv"
    cost_df.to_csv(cost_csv, index=False)

    cost_delta: list[dict] = []
    for mult in COST_MULTS:
        b = cost_df[(cost_df.book == "BASE_E16_E18_E22_v2s") & (cost_df.cost_multiple == mult)].iloc[0]
        c = cost_df[(cost_df.book == "CHAL_E45_E3") & (cost_df.cost_multiple == mult)].iloc[0]
        cost_delta.append(
            {
                "cost_multiple": int(mult),
                "mdd_improve_pp": (c["mdd"] - b["mdd"]) * 100.0,
                "cagr_giveback_pp": (b["cagr"] - c["cagr"]) * 100.0,
                "base_cagr": b["cagr"],
                "chal_cagr": c["cagr"],
                "base_mdd": b["mdd"],
                "chal_mdd": c["mdd"],
            }
        )
    cost_delta_df = pd.DataFrame(cost_delta)
    cost_delta_csv = OUT / "outputs" / "e45_named_cost_multiples_delta.csv"
    cost_delta_df.to_csv(cost_delta_csv, index=False)

    def _delta(mult: int, col: str) -> float:
        return float(cost_delta_df.loc[cost_delta_df.cost_multiple == mult, col].iloc[0])

    v4_checks = {
        "has_e45_named_cost_table": True,
        "multiples": list(COST_MULTS),
        "at_1x_chal_mdd_not_worse_than_base": _delta(1, "mdd_improve_pp") >= 0.0,
        "at_2x_chal_still_shallower_or_within_5pp": _delta(2, "mdd_improve_pp") >= -5.0,
        "at_3x_chal_still_shallower_or_within_5pp": _delta(3, "mdd_improve_pp") >= -5.0,
    }
    v4_pass = all(v4_checks[k] for k in v4_checks if k != "multiples")

    # ---------- V5 crisis years at 1× ----------
    crisis_rows: list[dict] = []
    with fee_multiple(1):
        for book, expo in books.items():
            nav, _f, _m = simulate_core(
                market,
                target,
                regime,
                div,
                apply_e22=True,
                apply_stock_div=True,
                e45_exposure=expo,
            )
            for y in CRISIS_YEARS:
                st = year_stats(nav, y)
                st["book"] = book
                crisis_rows.append(st)
            crisis_rows.append(
                {
                    "book": book,
                    "year": 2008,
                    "n_days": 0,
                    "ret": None,
                    "mdd": None,
                    "available": False,
                    "note": f"market starts {data_start}; 2008 N/A",
                }
            )

    crisis_df = pd.DataFrame(crisis_rows)
    crisis_csv = OUT / "outputs" / "e45_named_crisis_year_attribution.csv"
    crisis_df.to_csv(crisis_csv, index=False)

    crisis_delta: list[dict] = []
    for y in list(CRISIS_YEARS) + [2008]:
        b = crisis_df[(crisis_df.book == "BASE_E16_E18_E22_v2s") & (crisis_df.year == y)].iloc[0]
        c = crisis_df[(crisis_df.book == "CHAL_E45_E3") & (crisis_df.year == y)].iloc[0]
        if not bool(b["available"]) or not bool(c["available"]):
            crisis_delta.append(
                {
                    "year": int(y),
                    "available": False,
                    "mdd_improve_pp": None,
                    "ret_delta_pp": None,
                    "note": b.get("note") or c.get("note") or "",
                }
            )
            continue
        crisis_delta.append(
            {
                "year": int(y),
                "available": True,
                "mdd_improve_pp": (c["mdd"] - b["mdd"]) * 100.0,
                "ret_delta_pp": (c["ret"] - b["ret"]) * 100.0,
                "base_ret": b["ret"],
                "chal_ret": c["ret"],
                "base_mdd": b["mdd"],
                "chal_mdd": c["mdd"],
                "note": b.get("note") or "",
            }
        )
    crisis_delta_df = pd.DataFrame(crisis_delta)
    crisis_delta_csv = OUT / "outputs" / "e45_named_crisis_year_delta.csv"
    crisis_delta_df.to_csv(crisis_delta_csv, index=False)

    avail = crisis_delta_df[crisis_delta_df["available"] == True]  # noqa: E712
    pos = avail[avail["mdd_improve_pp"] > 0]
    total_pos = float(pos["mdd_improve_pp"].sum()) if len(pos) else 0.0
    max_pos = float(pos["mdd_improve_pp"].max()) if len(pos) else 0.0
    max_share = None if total_pos <= 0 else max_pos / total_pos
    v5_checks = {
        "has_e45_named_crisis_table": True,
        "years_available": int(avail.shape[0]),
        "years_with_mdd_improve": int((avail["mdd_improve_pp"] > 0).sum()),
        "max_share_of_positive_mdd_improve": max_share,
        "not_single_year_gt_80pct": True if total_pos <= 0 else max_share <= 0.80,
        "at_least_two_crisis_years_improve": int((avail["mdd_improve_pp"] > 0).sum()) >= 2,
        "year_2008_documented_unavailable": True,
        "stage3_multiwindow_design_present": (
            ROOT / "repro/e45-dual-paper-observe-design/outputs/dual_paper_window_metrics.csv"
        ).exists(),
    }
    v5_pass = all(
        [
            v5_checks["has_e45_named_crisis_table"],
            v5_checks["at_least_two_crisis_years_improve"],
            v5_checks["not_single_year_gt_80pct"],
            v5_checks["year_2008_documented_unavailable"],
            v5_checks["years_available"] >= 3,
            v5_checks["stage3_multiwindow_design_present"],
        ]
    )

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "E45_NAMED_V4_V5_PACKS",
        "live_wire": False,
        "soft_frozen_keep": [0.50, 0.95],
        "default_books_keep": "E22_v2s_tw",
        "claim_mdd_status": "NOT_VERIFIED",
        "v1_status": "FAIL",
        "stitch_forbidden": True,
        "data_start": data_start,
        "data_end": data_end,
        "v4": {
            "status": "PASS" if v4_pass else "FAIL",
            "checks": v4_checks,
            "cost_csv": str(cost_csv.relative_to(ROOT)),
            "delta_csv": str(cost_delta_csv.relative_to(ROOT)),
        },
        "v5": {
            "status": "PASS" if v5_pass else "FAIL",
            "checks": v5_checks,
            "crisis_csv": str(crisis_csv.relative_to(ROOT)),
            "delta_csv": str(crisis_delta_csv.relative_to(ROOT)),
        },
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    # ----- markdown packs -----
    v4_lines = [
        "# E45 V4 Cost / Stress Pack (E45-named)",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        f"Status: **{summary['v4']['status']}** (E45-named Exact T+1 cost multiples)",
        "Live stitch: **FORBIDDEN** (V1 still FAIL) · Soft-Frozen **[0.50, 0.95] KEEP** · DEFAULT **`E22_v2s_tw` KEEP**",
        "Claimed MDD ≈ −13.16%: **`NOT_VERIFIED`**",
        "",
        "## Method",
        "",
        "- Books: `BASE_E16_E18_E22_v2s` vs `CHAL_E45_E3` (`E3_VOLTARGET_WINNER` overlay)",
        "- Exact T+1 early-stack; scale `BUY_FEE`/`SELL_FEE`/`SLIP`/`TAX_*` by 0×/1×/2×/3×",
        f"- Sample: `{data_start}` → `{data_end}`",
        "",
        "## E45-named cost multiples",
        "",
        "| Book | ×cost | CAGR | MDD | fills | fees+tax |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for r in cost_rows:
        v4_lines.append(
            f"| {r['book']} | {r['cost_multiple']} | {pct(r['cagr'])} | {pct(r['mdd'])} | "
            f"{r['n_fills']} | {r['fees_tax_sum']:.2f} |"
        )
    v4_lines += [
        "",
        "## Deltas vs BASE",
        "",
        "| ×cost | MDD Δ (pp; + = shallower) | CAGR giveback (pp) |",
        "|---:|---:|---:|",
    ]
    for r in cost_delta:
        v4_lines.append(
            f"| {r['cost_multiple']} | {pp(r['mdd_improve_pp'])} | {pp(r['cagr_giveback_pp'])} |"
        )
    v4_lines += ["", "## V4 checks", "", "| Check | Result |", "|---|---|"]
    for k, v in v4_checks.items():
        v4_lines.append(f"| `{k}` | **{v}** |")
    v4_lines += [
        "",
        f"**V4 verdict: `{summary['v4']['status']}`**",
        "",
        "## Artifacts",
        "",
        f"- `{summary['v4']['cost_csv']}`",
        f"- `{summary['v4']['delta_csv']}`",
        "- `repro/e45-v4v5-named-packs/summary.json`",
        "- Script: `scripts/e45_v4v5_named_packs.py`",
        "",
        "## Non-actions",
        "",
        "- No live-wire / Soft-Frozen flip / history rewrite",
        "- No invented −13.16%",
        "- V4 PASS ≠ stitch authorization (V1 still FAIL)",
        "",
        "## Label",
        "",
        f"`E45_V4_COST_STRESS_PACK_2026-09-05__{summary['v4']['status']}`",
        "",
    ]
    V4_MD.write_text("\n".join(v4_lines) + "\n")

    v5_lines = [
        "# E45 V5 Multi-Window / Crisis-Year Pack (E45-named)",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        f"Status: **{summary['v5']['status']}** (E45-named crisis-year attribution + Stage-3 multi-window)",
        "Live stitch: **FORBIDDEN** (V1 still FAIL) · Soft-Frozen **KEEP** · DEFAULT **`E22_v2s_tw` KEEP**",
        "Claimed MDD ≈ −13.16%: **`NOT_VERIFIED`**",
        "",
        "## Data coverage",
        "",
        f"- Market span: **{data_start} → {data_end}**",
        "- **2008: N/A** (before sample start) — documented",
        "- Crisis years scored: 2011 (partial), 2015, 2018, 2020, 2022",
        "",
        "## Crisis-year attribution (1× costs, Exact T+1)",
        "",
        "| Book | Year | avail | n_days | ret | MDD | note |",
        "|---|---:|---|---:|---:|---:|---|",
    ]
    for r in crisis_rows:
        v5_lines.append(
            f"| {r['book']} | {r['year']} | {r['available']} | {r['n_days']} | "
            f"{pct(r['ret'])} | {pct(r['mdd'])} | {r.get('note') or ''} |"
        )
    v5_lines += [
        "",
        "## Crisis deltas vs BASE",
        "",
        "| Year | avail | MDD Δ (pp) | ret Δ (pp) | note |",
        "|---:|---|---:|---:|---|",
    ]
    for r in crisis_delta:
        v5_lines.append(
            f"| {r['year']} | {r['available']} | {pp(r['mdd_improve_pp'])} | "
            f"{pp(r['ret_delta_pp'])} | {r.get('note') or ''} |"
        )
    v5_lines += [
        "",
        "## Stage-3 multi-window design (also required)",
        "",
        "- `research/e45/E45_DUAL_PAPER_OBSERVE_DESIGN.md`",
        "- `repro/e45-dual-paper-observe-design/outputs/dual_paper_window_metrics.csv`",
        "",
        "## V5 checks",
        "",
        "| Check | Result |",
        "|---|---|",
    ]
    for k, v in v5_checks.items():
        if isinstance(v, float):
            v5_lines.append(f"| `{k}` | **{v:.3f}** |")
        else:
            v5_lines.append(f"| `{k}` | **{v}** |")
    v5_lines += [
        "",
        f"**V5 verdict: `{summary['v5']['status']}`**",
        "",
        "## Artifacts",
        "",
        f"- `{summary['v5']['crisis_csv']}`",
        f"- `{summary['v5']['delta_csv']}`",
        "- `repro/e45-v4v5-named-packs/summary.json`",
        "- Script: `scripts/e45_v4v5_named_packs.py`",
        "",
        "## Non-actions",
        "",
        "- No live-wire / Soft-Frozen flip / history rewrite",
        "- No invented −13.16%",
        "- V5 PASS ≠ stitch authorization (V1 still FAIL)",
        "",
        "## Label",
        "",
        f"`E45_V5_MULTI_WINDOW_PACK_2026-09-05__{summary['v5']['status']}`",
        "",
    ]
    V5_MD.write_text("\n".join(v5_lines) + "\n")

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
