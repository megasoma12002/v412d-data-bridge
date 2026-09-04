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

# --- PREDECLARED overlay risk-budget challengers (paper only; not live weights) ---
# Informed by failure-signature study; evaluated causally (use only prior complete months).
# FORBIDDEN: calendar month blacklists / sealed peeking for rule selection.
RISK_BUDGET_BASE_MIX = "CORE_80_OVL_20"  # predeclared working paper mix
RISK_BUDGET_RULES = [
    "STATIC",  # fixed mix weights, no throttle
    "TRAIL_3M_HALVE",  # if last 3 complete months all lose to proxy → overlay ×0.5
    "TRAIL_3M_ZERO",  # if last 3 complete months all lose to proxy → overlay ×0
    "COMBINED_DD15_CUT",  # if combined peak DD < -15% → overlay ×0 until new high
]

# E18 board-lot challenger policies (full fill re-sim under E22_v2s)
LOT_RESIM_POLICIES = [
    ("share_1", 1),
    ("board_lot_1000", 1000),
]


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


def chain_overlay_nav(overlay: pd.DataFrame) -> pd.DataFrame:
    """R1 daily_nav resets to 1.0 at sealed start — chain growth across periods."""
    o = overlay.copy()
    o["date"] = pd.to_datetime(o["date"])
    o = o.sort_values("date").drop_duplicates("date", keep="last").reset_index(drop=True)
    idx = [1.0]
    for i in range(1, len(o)):
        prev, cur = float(o.loc[i - 1, "nav"]), float(o.loc[i, "nav"])
        # period boundary reset (nav jumps down to ~1 while previous >> 1)
        if cur <= 1.0000001 and prev > 1.5:
            idx.append(idx[-1])
        else:
            idx.append(idx[-1] if prev == 0 else idx[-1] * (cur / prev))
    o["overlay_nav_chained"] = idx
    return o


def paper_combined(core: pd.DataFrame, overlay: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    c = core.copy()
    o = chain_overlay_nav(overlay)
    c["date"] = pd.to_datetime(c["date"])
    c = c.rename(columns={"nav": "core_nav"})
    m = c.merge(o[["date", "overlay_nav_chained"]], on="date", how="inner")
    m = m[m["date"] >= pd.Timestamp(OVERLAP_START)].sort_values("date")
    m["core_idx"] = m["core_nav"] / float(m["core_nav"].iloc[0])
    m["ovl_idx"] = m["overlay_nav_chained"] / float(m["overlay_nav_chained"].iloc[0])

    rows = []
    cols = ["date", "core_idx", "ovl_idx"]
    if "regime" in m.columns:
        cols.append("regime")
    out = m[cols].copy()
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
    """Monthly excess of chained R1 vs 0050 buy-hold (research proxy stand-in)."""
    o = chain_overlay_nav(overlay)
    px = (
        market[market["code"] == "0050"]
        .assign(date=lambda d: pd.to_datetime(d["date"]))
        .sort_values("date")
        .drop_duplicates("date")
    )
    px = px[["date", "close"]].rename(columns={"close": "px"})
    m = o.merge(px, on="date", how="inner").sort_values("date")
    m["ovl_ret"] = m["overlay_nav_chained"].pct_change()
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
    worst = monthly.nsmallest(8, "excess").reset_index()
    best = monthly.nlargest(8, "excess").reset_index()
    return {
        "proxy": "0050_buy_hold_close_approx",
        "overlay_series": "chained_across_val_sealed_boundary",
        "n_months": int(len(monthly)),
        "pct_months_lose_to_proxy": float(monthly["lose"].mean()) if len(monthly) else None,
        "mean_monthly_excess": float(monthly["excess"].mean()) if len(monthly) else None,
        "worst_months": worst.to_dict(orient="records"),
        "best_months": best.to_dict(orient="records"),
        "note": (
            "Stand-in proxy (0050), not the official PIT equal-weight proxy used in R1 gates. "
            "Overlay NAV chained across validation→sealed reset."
        ),
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
                "End-position stranding only. Full fill re-sim under board lots is in "
                "e18_board_lot_resim() below."
            ),
        }
    )
    return rows


def _monthly_excess_series(overlay: pd.DataFrame, market: pd.DataFrame) -> pd.DataFrame:
    o = chain_overlay_nav(overlay)
    px = (
        market[market["code"] == "0050"]
        .assign(date=lambda d: pd.to_datetime(d["date"]))
        .sort_values("date")
        .drop_duplicates("date")
    )
    px = px[["date", "close"]].rename(columns={"close": "px"})
    m = o.merge(px, on="date", how="inner").sort_values("date")
    m["ovl_ret"] = m["overlay_nav_chained"].pct_change()
    m["px_ret"] = m["px"].pct_change()
    m["excess"] = m["ovl_ret"] - m["px_ret"]
    m["ym"] = m["date"].dt.to_period("M").astype(str)
    monthly = (
        m.groupby("ym")
        .agg(excess=("excess", "sum"), ovl=("ovl_ret", "sum"), px=("px_ret", "sum"), n=("excess", "count"))
        .reset_index()
    )
    monthly["lose"] = monthly["excess"] < 0
    return monthly


def overlay_risk_budget_paper(
    combined: pd.DataFrame, overlay: pd.DataFrame, market: pd.DataFrame
) -> tuple[pd.DataFrame, list[dict]]:
    """Causal paper risk-budget scalers on predeclared CORE_80/20 mix.

    Scale applies to overlay sleeve only; core stays 0.80 of capital index.
    Effective: nav = 0.80*core_idx + 0.20*scale*ovl_idx  (then rebase for stats windows).
    """
    monthly = _monthly_excess_series(overlay, market)
    lose_by_ym = dict(zip(monthly["ym"], monthly["lose"].astype(bool)))
    ym_order = list(monthly["ym"])

    base = combined.copy()
    base["date"] = pd.to_datetime(base["date"])
    base = base.sort_values("date").reset_index(drop=True)
    wc, wo = 0.80, 0.20
    assert RISK_BUDGET_BASE_MIX == "CORE_80_OVL_20"

    # Precompute daily scale series per rule
    scales = {r: [] for r in RISK_BUDGET_RULES}
    peak_combined = None
    cut_active = False
    for i, row in base.iterrows():
        dt = row["date"]
        ym = dt.to_period("M").strftime("%Y-%m")
        # prior complete months only
        prior = [y for y in ym_order if y < ym]
        trail3 = prior[-3:] if len(prior) >= 3 else prior
        all_lose = bool(trail3) and all(lose_by_ym.get(y, False) for y in trail3)

        # STATIC
        scales["STATIC"].append(1.0)

        # TRAIL rules
        scales["TRAIL_3M_HALVE"].append(0.5 if all_lose and len(trail3) == 3 else 1.0)
        scales["TRAIL_3M_ZERO"].append(0.0 if all_lose and len(trail3) == 3 else 1.0)

        # COMBINED_DD15_CUT uses running static combined peak (causal on STATIC path)
        static_nav = wc * float(row["core_idx"]) + wo * float(row["ovl_idx"])
        if peak_combined is None:
            peak_combined = static_nav
        peak_combined = max(peak_combined, static_nav)
        dd = static_nav / peak_combined - 1.0
        if dd < -0.15:
            cut_active = True
        if cut_active and static_nav >= peak_combined * 0.999:
            cut_active = False
            peak_combined = static_nav
        scales["COMBINED_DD15_CUT"].append(0.0 if cut_active else 1.0)

    out = base[["date", "core_idx", "ovl_idx"]].copy()
    rows = []
    for rule in RISK_BUDGET_RULES:
        col = f"nav_rb_{rule.lower()}"
        sc = np.array(scales[rule], dtype=float)
        out[f"scale_{rule.lower()}"] = sc
        # keep core weight fixed; shrink overlay notionally (cash drag implicit as missing ovl)
        out[col] = wc * out["core_idx"] + wo * sc * out["ovl_idx"]
        # normalize so day-0 = 1 for fair CAGR
        out[col] = out[col] / float(out[col].iloc[0])
        rows.append(
            {
                "rule": rule,
                "base_mix": RISK_BUDGET_BASE_MIX,
                "w_core": wc,
                "w_overlay_max": wo,
                "mean_overlay_scale": float(sc.mean()),
                "pct_days_scale_lt_1": float((sc < 1.0 - 1e-12).mean()),
                "full_overlap": cagr_mdd(out[col]),
                "validation_2019_2022": window_stats(out.assign(nav=out[col]), OVERLAP_START, VAL_END),
                "sealed_2023_latest": window_stats(
                    out.assign(nav=out[col]), SEALED_START, out["date"].max().date().isoformat()
                ),
                "governance": "EXPERIMENTAL_PAPER_ONLY",
            }
        )
    return out, rows


def e18_board_lot_resim(market: pd.DataFrame, dividends: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    """Full Exact-T+1 re-sim under E22_v2s with lot_size=1 vs board-lot 1000."""
    m = market.copy()
    m["date"] = pd.to_datetime(m["date"])
    required = set(ALL + ["TAIEX"])
    complete = m.groupby("date")["code"].apply(lambda s: required.issubset(set(s)))
    m = m[m["date"].isin(complete[complete].index)].sort_values(["date", "code"])
    _p, _s, target, regime = e16_features(m)

    nav_wide = None
    rows = []
    for name, ls in LOT_RESIM_POLICIES:
        print(f"  e18 resim lot_size={ls} ...", flush=True)
        nav, fills, meta = simulate_core(
            m,
            target,
            regime,
            dividends,
            apply_e22=True,
            apply_stock_div=True,
            e22_version=e22div.E22_V2S,
            lot_size=ls,
        )
        stats = nav_stats(nav)
        pos = meta.get("end_positions") or {}
        stranded_board = {
            k: float(pos[k]) - float(np.floor(pos[k] / BOARD_LOT) * BOARD_LOT) for k in pos
        }
        row = {
            "policy": name,
            "lot_size": ls,
            "cagr": stats.get("cagr"),
            "max_drawdown": stats.get("max_drawdown"),
            "vol": stats.get("vol"),
            "utility": stats.get("utility"),
            "n_fills": meta.get("n_fills"),
            "exact_t1_ok": meta.get("exact_t1_ok"),
            "stock_div_shares_added": meta.get("stock_div_shares_added"),
            "dividend_cash_total": meta.get("dividend_cash_total"),
            "end_nav": float(nav["nav"].iloc[-1]) if len(nav) else None,
            "end_cash": float(nav["cash"].iloc[-1]) if len(nav) else None,
            "end_positions": pos,
            "stranded_vs_board_lot_at_end": stranded_board,
            "stranded_total_vs_board_lot": float(sum(stranded_board.values())),
            "start": meta.get("start"),
            "end": meta.get("end"),
        }
        rows.append(row)
        piece = nav[["date", "nav"]].rename(columns={"nav": f"nav_{name}"})
        piece["date"] = pd.to_datetime(piece["date"])
        nav_wide = piece if nav_wide is None else nav_wide.merge(piece, on="date", how="outer")

        fills.to_csv(OUT / "outputs" / f"e18_fills_{name}.csv", index=False)

    if nav_wide is not None and "nav_share_1" in nav_wide.columns and "nav_board_lot_1000" in nav_wide.columns:
        a = nav_wide["nav_share_1"]
        b = nav_wide["nav_board_lot_1000"]
        delta = {
            "end_nav_ratio_board_over_share1": float(b.iloc[-1] / a.iloc[-1]) if a.iloc[-1] else None,
            "cagr_delta_pp": None,
        }
        c0 = rows[0]["cagr"]
        c1 = rows[1]["cagr"]
        if c0 is not None and c1 is not None:
            delta["cagr_delta_pp"] = float((c1 - c0) * 100.0)
            delta["mdd_delta_pp"] = float((rows[1]["max_drawdown"] - rows[0]["max_drawdown"]) * 100.0)
        rows.append({"policy": "delta_board_vs_share1", **delta})

    return nav_wide if nav_wide is not None else pd.DataFrame(), rows


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

    print("overlay risk budget paper ...", flush=True)
    rb_nav, rb_rows = overlay_risk_budget_paper(combined_nav, overlay, market)
    rb_nav.to_csv(OUT / "outputs" / "overlay_risk_budget_daily_nav.csv", index=False)
    pd.DataFrame(
        [
            {
                "rule": r["rule"],
                "mean_overlay_scale": r["mean_overlay_scale"],
                "pct_days_scale_lt_1": r["pct_days_scale_lt_1"],
                "full_cagr": r["full_overlap"]["cagr"],
                "full_mdd": r["full_overlap"]["max_drawdown"],
                "val_cagr": r["validation_2019_2022"]["cagr"],
                "val_mdd": r["validation_2019_2022"]["max_drawdown"],
                "sealed_cagr": r["sealed_2023_latest"]["cagr"],
                "sealed_mdd": r["sealed_2023_latest"]["max_drawdown"],
            }
            for r in rb_rows
        ]
    ).to_csv(OUT / "outputs" / "overlay_risk_budget_summary.csv", index=False)

    print("e18 board-lot full re-sim ...", flush=True)
    lot_nav, lot_resim_rows = e18_board_lot_resim(market, dividends)
    if len(lot_nav):
        lot_nav.to_csv(OUT / "outputs" / "e18_board_lot_daily_nav.csv", index=False)
    Path(OUT / "outputs" / "e18_board_lot_resim.json").write_text(
        json.dumps(lot_resim_rows, indent=2, default=str) + "\n"
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
            "predeclared_risk_budget_rules": list(RISK_BUDGET_RULES),
            "predeclared_risk_budget_base_mix": RISK_BUDGET_BASE_MIX,
            "predeclared_lot_resim": [list(x) for x in LOT_RESIM_POLICIES],
        },
        "paper_combined": mix_rows,
        "failure_signature": fail,
        "lot_policy": lot_rows,
        "overlay_risk_budget": rb_rows,
        "e18_board_lot_resim": lot_resim_rows,
        "decision": {
            "overlay_live": "STILL_NO",
            "best_paper_mix_not_for_promotion": True,
            "risk_budget_live": "STILL_NO",
            "board_lot_live": "STILL_NO_CHALLENGER_ONLY",
            "next": [
                "Alpha-repair track: E50-A3-R1 turnover/held-out diagnosis (separate branch)",
                "Optional: fractional floor + cash-in-lieu formal books challenger",
                "Do not live-wire risk budget or board-lot until governance PR",
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
        f"- Risk-budget base mix: `{RISK_BUDGET_BASE_MIX}` rules=`{RISK_BUDGET_RULES}`",
        f"- E18 lot re-sim: `{LOT_RESIM_POLICIES}`",
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
        "## Overlay risk budget (paper, causal throttles on CORE_80/20)",
        "",
        "Rules use only **prior complete months** (or running combined DD). "
        "No calendar blacklists. Not live weights.",
        "",
        "| Rule | Mean scale | % days scaled | Full CAGR | Full MDD | Val CAGR | Val MDD | Sealed CAGR | Sealed MDD |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rb_rows:
        f, v, s = r["full_overlap"], r["validation_2019_2022"], r["sealed_2023_latest"]
        lines.append(
            f"| {r['rule']} | {r['mean_overlay_scale']:.3f} | {100*r['pct_days_scale_lt_1']:.1f}% | "
            f"{100*(f['cagr'] or 0):.2f}% | {100*(f['max_drawdown'] or 0):.2f}% | "
            f"{100*(v['cagr'] or 0):.2f}% | {100*(v['max_drawdown'] or 0):.2f}% | "
            f"{100*(s['cagr'] or 0):.2f}% | {100*(s['max_drawdown'] or 0):.2f}% |"
        )
    lines += [
        "",
        "Interpretation: throttles can trim overlay exposure after losing streaks / deep combined DD, "
        "but do **not** create a promotion path while R1 itself fails gates.",
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
        "## E18 board-lot full re-sim (E22_v2s books)",
        "",
        "| Policy | lot_size | CAGR | MDD | n_fills | end_nav | stranded_vs_1000 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in lot_resim_rows:
        if row.get("policy") == "delta_board_vs_share1":
            lines.append(
                f"- Delta board vs 1-share: CAGR Δ=`{row.get('cagr_delta_pp')}` pp; "
                f"MDD Δ=`{row.get('mdd_delta_pp')}` pp; "
                f"end_nav ratio=`{row.get('end_nav_ratio_board_over_share1')}`"
            )
            continue
        lines.append(
            f"| {row['policy']} | {row['lot_size']} | {100*(row['cagr'] or 0):.2f}% | "
            f"{100*(row['max_drawdown'] or 0):.2f}% | {row['n_fills']} | "
            f"{row['end_nav']:.2f} | {row['stranded_total_vs_board_lot']:.2f} |"
        )
    lines += [
        "",
        "Interpretation: board-lot 1000 is a capacity/fill challenger for small sleeves; "
        "do not silently replace 1-share research books without a named E18 version.",
        "",
        "## Decision",
        "",
        f"- Live overlay: `{summary['decision']['overlay_live']}`",
        f"- Risk budget live: `{summary['decision']['risk_budget_live']}`",
        f"- Board-lot live: `{summary['decision']['board_lot_live']}`",
        "- Do not promote any mix / throttle / lot policy from this paper work",
        "- Next: " + "; ".join(summary["decision"]["next"]),
        "",
        "## Artifacts",
        "",
        f"- `{SUMMARY}`",
        f"- `{OUT}/`",
        "",
    ]
    REPORT.write_text("\n".join(lines) + "\n")
    print(
        json.dumps(
            {
                "mixes": [r["mix"] for r in mix_rows],
                "fail_lose_pct": fail["pct_months_lose_to_proxy"],
                "risk_budget_rules": [r["rule"] for r in rb_rows],
                "lot_resim": [r.get("policy") for r in lot_resim_rows],
            },
            indent=2,
        )
    )
    print(f"wrote {REPORT}", flush=True)


if __name__ == "__main__":
    main()
