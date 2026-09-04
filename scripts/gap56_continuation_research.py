#!/usr/bin/env python3
"""Gap #5/#6 continuation research (EXPERIMENTAL, no live wire).

Predeclared before looking at results:
  - Overlay capital mixes: 100/0, 90/10, 80/20, 70/30 (core / overlay)
  - Lot policies: 1-share (baseline), floor after stock-div, board-lot 1000

Does NOT modify forward/e21 or promote R1.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from e50_early_stack_combined_nav import ALL, FIN, TEL, e16_features, nav_stats, simulate_core, lot_qty
import e22_dividend_accounting as e22div

OUT = Path("repro/gap5-6-continuation")
REPORT = Path("research/gaps/GAP5_6_CONTINUATION.md")
SUMMARY = Path("research/gaps/GAP5_6_CONTINUATION.json")

# --- PREDECLARED (do not change after first sealed peek in this run) ---
OVERLAY_MIXES = [
    ("CORE_100", 1.00, 0.00),
    ("CORE_90_OVL_10", 0.90, 0.10),
    ("CORE_80_OVL_20", 0.80, 0.20),
    ("CORE_70_OVL_30", 0.70, 0.30),
]
OVERLAP_START = "2019-01-02"  # R1 validation start
VAL_END = "2022-12-30"
SEALED_START = "2023-01-03"
BOARD_LOT = 1000


def cagr_mdd(nav: pd.Series) -> dict:
    nav = nav.dropna()
    if len(nav) < 5 or float(nav.iloc[0]) <= 0:
        return {"cagr": None, "max_drawdown": None, "end": None}
    r = nav.pct_change().dropna().to_numpy()
    years = len(r) / 252.0
    cagr = float((nav.iloc[-1] / nav.iloc[0]) ** (1 / years) - 1) if years > 0 else None
    peak = np.maximum.accumulate(nav.to_numpy())
    mdd = float(np.min(nav.to_numpy() / peak - 1.0))
    return {"cagr": cagr, "max_drawdown": mdd, "end": float(nav.iloc[-1]), "n_days": int(len(nav))}


def window_stats(df: pd.DataFrame, start: str, end: str, col: str = "nav") -> dict:
    w = df[(df["date"] >= start) & (df["date"] <= end)].copy()
    if len(w) < 5:
        return {"cagr": None, "max_drawdown": None, "n_days": 0}
    # rebase
    w = w.sort_values("date")
    base = float(w[col].iloc[0])
    s = w[col] / base
    out = cagr_mdd(s)
    out["start"] = start
    out["end"] = end
    return out


def paper_combined(core: pd.DataFrame, overlay: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    c = core.copy()
    o = overlay.copy()
    c["date"] = pd.to_datetime(c["date"])
    o["date"] = pd.to_datetime(o["date"])
    # stitch full R1 path (validation then sealed) as one series
    o = o.sort_values("date").drop_duplicates("date", keep="last")
    m = c.merge(o[["date", "nav"]].rename(columns={"nav": "overlay_nav"}), on="date", how="inner")
    m = m[m["date"] >= pd.Timestamp(OVERLAP_START)].sort_values("date")
    m["core_idx"] = m["nav"] / float(m["nav"].iloc[0])
    m["ovl_idx"] = m["overlay_nav"] / float(m["overlay_nav"].iloc[0])

    rows = []
    out = m[["date", "core_idx", "ovl_idx", "regime"]].copy() if "regime" in m.columns else m[["date", "core_idx", "ovl_idx"]].copy()
    for name, wc, wo in OVERLAY_MIXES:
        col = f"nav_{name.lower()}"
        out[col] = wc * m["core_idx"] + wo * m["ovl_idx"]
        rows.append(
            {
                "mix": name,
                "w_core": wc,
                "w_overlay": wo,
                "full_overlap": cagr_mdd(out[col]),
                "validation_2019_2022": window_stats(out.assign(nav=out[col]), OVERLAP_START, VAL_END),
                "sealed_2023_latest": window_stats(
                    out.assign(nav=out[col]), SEALED_START, out["date"].max().date().isoformat()
                ),
            }
        )
    return out, rows


def failure_signature(overlay: pd.DataFrame, market: pd.DataFrame) -> dict:
    """Monthly excess of R1 vs 0050 buy-hold (research proxy stand-in)."""
    o = overlay.copy()
    o["date"] = pd.to_datetime(o["date"])
    px = (
        market[market["code"] == "0050"]
        .assign(date=lambda d: pd.to_datetime(d["date"]))
        .sort_values("date")
        .drop_duplicates("date")
    )
    px = px[["date", "close"]].rename(columns={"close": "px"})
    m = o.merge(px, on="date", how="inner").sort_values("date")
    m["ovl_ret"] = m["nav"].pct_change()
    m["px_ret"] = m["px"].pct_change()
    m["excess"] = m["ovl_ret"] - m["px_ret"]
    m["ym"] = m["date"].dt.to_period("M").astype(str)
    monthly = m.groupby("ym").agg(
        excess=("excess", "sum"),
        ovl=("ovl_ret", "sum"),
        px=("px_ret", "sum"),
        n=("excess", "count"),
    )
    monthly["lose"] = monthly["excess"] < 0
    # tag crisis months via core regime if available later
    worst = monthly.nsmallest(8, "excess").reset_index()
    best = monthly.nlargest(8, "excess").reset_index()
    return {
        "proxy": "0050_buy_hold_close_approx",
        "n_months": int(len(monthly)),
        "pct_months_lose_to_proxy": float(monthly["lose"].mean()) if len(monthly) else None,
        "mean_monthly_excess": float(monthly["excess"].mean()) if len(monthly) else None,
        "worst_months": worst.to_dict(orient="records"),
        "best_months": best.to_dict(orient="records"),
        "note": "Stand-in proxy (0050), not the official PIT equal-weight proxy used in R1 gates.",
    }


def lot_policy_sensitivity(market: pd.DataFrame, dividends: pd.DataFrame) -> list[dict]:
    """Compare sell flooring policies on end positions from the v2s early-stack path."""
    m = market.copy()
    m["date"] = pd.to_datetime(m["date"])
    required = set(ALL + ["TAIEX"])
    complete = m.groupby("date")["code"].apply(lambda s: required.issubset(set(s)))
    m = m[m["date"].isin(complete[complete].index)].sort_values(["date", "code"])
    _p, _s, target, regime = e16_features(m)
    nav, _fills, meta = simulate_core(
        m,
        target,
        regime,
        dividends,
        apply_e22=True,
        apply_stock_div=True,
        e22_version=e22div.E22_V2S,
    )
    pos = meta.get("end_positions") or {}
    rows = []
    for name, fn in [
        ("float_keep", lambda x: float(x)),
        ("floor_int", lambda x: float(np.floor(x))),
        ("board_lot_1000", lambda x: float(np.floor(x / BOARD_LOT) * BOARD_LOT)),
    ]:
        adj = {k: fn(v) for k, v in pos.items()}
        stranded = {k: float(pos[k]) - adj[k] for k in pos}
        rows.append(
            {
                "policy": name,
                "end_positions": adj,
                "stranded_shares": stranded,
                "stranded_total_shares": float(sum(stranded.values())),
                "sim_end_nav_ref": float(nav["nav"].iloc[-1]),
                "stock_div_shares_added_in_sim": meta.get("stock_div_shares_added"),
            }
        )
    rows.append(
        {
            "policy": "note",
            "text": (
                "Board-lot 1000 zeros small telecom sleeves; floor_int only drops fractional dust. "
                "Full fill re-sim under board lots left as follow-on E18 challenger."
            ),
        }
    )
    return rows


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)

    core = pd.read_csv("repro/e22-v2s-historical-recompute/outputs/e22_v2s_daily_nav.csv")
    overlay = pd.read_csv("repro/e50a3r1-audit-20260903/outputs/a3r1/daily_nav.csv")
    market = pd.read_csv("forward/e21/live_market.csv", dtype={"code": str})
    dividends = pd.read_csv("data/dividend_events/e22_dividend_events.csv", dtype={"code": str})

    print("paper combined ...", flush=True)
    combined_nav, mix_rows = paper_combined(core, overlay)
    combined_nav.to_csv(OUT / "outputs" / "paper_combined_daily_nav.csv", index=False)
    pd.DataFrame(
        [
            {
                "mix": r["mix"],
                "w_core": r["w_core"],
                "w_overlay": r["w_overlay"],
                "full_cagr": r["full_overlap"]["cagr"],
                "full_mdd": r["full_overlap"]["max_drawdown"],
                "val_cagr": r["validation_2019_2022"]["cagr"],
                "val_mdd": r["validation_2019_2022"]["max_drawdown"],
                "sealed_cagr": r["sealed_2023_latest"]["cagr"],
                "sealed_mdd": r["sealed_2023_latest"]["max_drawdown"],
            }
            for r in mix_rows
        ]
    ).to_csv(OUT / "outputs" / "paper_combined_mix_summary.csv", index=False)

    print("failure signature ...", flush=True)
    fail = failure_signature(overlay, market)
    pd.DataFrame(fail["worst_months"]).to_csv(OUT / "outputs" / "failure_worst_months.csv", index=False)
    pd.DataFrame(fail["best_months"]).to_csv(OUT / "outputs" / "failure_best_months.csv", index=False)

    print("lot policy sensitivity ...", flush=True)
    # Restrict market to speed? full history ok ~2s
    lot_rows = lot_policy_sensitivity(market, dividends)
    Path(OUT / "outputs" / "lot_policy_sensitivity.json").write_text(
        json.dumps(lot_rows, indent=2, default=str) + "\n"
    )

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "GAP5_6_CONTINUATION",
        "governance": {
            "live_wire_overlay": False,
            "promotes_r1": False,
            "rewrites_forward_e21_history": False,
            "label": "EXPERIMENTAL_RESEARCH",
            "predeclared_mixes": [list(x) for x in OVERLAY_MIXES],
            "predeclared_overlap_start": OVERLAP_START,
        },
        "paper_combined": mix_rows,
        "failure_signature": fail,
        "lot_policy": lot_rows,
        "decision": {
            "overlay_live": "STILL_NO",
            "best_paper_mix_not_for_promotion": True,
            "next": [
                "Use failure months to design overlay risk budget (not live weights)",
                "E18 board-lot full re-sim challenger if capacity questions arise",
                "Keep E22_v2s as formal books; fractional floor+CIL optional follow-on",
            ],
        },
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
    SUMMARY.write_text(json.dumps(summary, indent=2, default=str) + "\n")

    lines = [
        "# Gap #5 / #6 Continuation Research",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        "",
        "**EXPERIMENTAL.** No live overlay wire. No R1 promotion. No live NAV history rewrite.",
        "",
        "## Predeclared controls",
        "",
        f"- Overlay mixes: `{OVERLAY_MIXES}`",
        f"- Overlap start: `{OVERLAP_START}` (R1 validation start)",
        f"- Core books: E22_v2s historical recompute NAV",
        f"- Overlay: A3-R1 `daily_nav.csv` (standalone sleeve)",
        "",
        "## Paper combined book (capital-weighted index stitch)",
        "",
        "| Mix | Full CAGR | Full MDD | Val CAGR | Val MDD | Sealed CAGR | Sealed MDD |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for r in mix_rows:
        f, v, s = r["full_overlap"], r["validation_2019_2022"], r["sealed_2023_latest"]
        lines.append(
            f"| {r['mix']} | {100*(f['cagr'] or 0):.2f}% | {100*(f['max_drawdown'] or 0):.2f}% | "
            f"{100*(v['cagr'] or 0):.2f}% | {100*(v['max_drawdown'] or 0):.2f}% | "
            f"{100*(s['cagr'] or 0):.2f}% | {100*(s['max_drawdown'] or 0):.2f}% |"
        )
    lines += [
        "",
        "Interpretation: sealed strength of R1 lifts mixes with more overlay weight, but validation",
        "still shows deep MDD and does **not** clear R1 gates. Paper stitch ≠ promotion.",
        "",
        "## Failure signature (R1 vs 0050 stand-in)",
        "",
        f"- Months losing to proxy: `{fail['pct_months_lose_to_proxy']}`",
        f"- Mean monthly excess: `{fail['mean_monthly_excess']}`",
        f"- Proxy note: {fail['note']}",
        "",
        "Worst months (by excess):",
        "",
        "| Month | Excess | Ovl | 0050 |",
        "|---|---:|---:|---:|",
    ]
    for w in fail["worst_months"][:8]:
        lines.append(
            f"| {w['ym']} | {100*w['excess']:.2f}% | {100*w['ovl']:.2f}% | {100*w['px']:.2f}% |"
        )
    lines += [
        "",
        "## Lot / fractional sensitivity (end positions from E22_v2s sim)",
        "",
    ]
    for row in lot_rows:
        if row.get("policy") == "note":
            lines.append(f"- Note: {row['text']}")
            continue
        lines.append(
            f"- `{row['policy']}`: stranded_total_shares=`{row['stranded_total_shares']:.4f}`"
        )
    lines += [
        "",
        "## Decision",
        "",
        f"- Live overlay: `{summary['decision']['overlay_live']}`",
        "- Do not promote any mix from this paper stitch",
        "- Next: " + "; ".join(summary["decision"]["next"]),
        "",
        "## Artifacts",
        "",
        f"- `{SUMMARY}`",
        f"- `{OUT}/`",
        "",
    ]
    REPORT.write_text("\n".join(lines) + "\n")
    print(json.dumps({"mixes": [r["mix"] for r in mix_rows], "fail_lose_pct": fail["pct_months_lose_to_proxy"]}, indent=2))
    print(f"wrote {REPORT}", flush=True)


if __name__ == "__main__":
    main()
