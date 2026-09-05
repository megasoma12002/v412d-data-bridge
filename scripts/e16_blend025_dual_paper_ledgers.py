#!/usr/bin/env python3
"""BLEND_025 dual paper ledgers (OBSERVE SLEEVE — not live).

Side-by-side Exact T+1 paper books:
  BASE_E16:   Soft-Frozen Financial clip [0.50, 0.95] (current live)
  BLEND_025:  α=0.25·FIN_CAP_50([0.35,0.50]) + 0.75·BASE, renormalized

Opened from FINCAP50_SEALED_CAGR_CHARTER_SCREEN → PAPER_PROMOTE_PROPOSAL_ONLY.
Does NOT edit e21_forward_pipeline live clips.
Does NOT flip Soft-Frozen default.
Does NOT authorize cutover.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from research_metric_helpers import mdd_delta_pp, cagr_delta_pp
from e50_early_stack_combined_nav import ALL, e16_features, nav_stats, simulate_core
import e22_dividend_accounting as e22div
from e16_fin_cap_oof_challenger import e16_features_fin_cap
from fincap_sealed_cagr_improve_diag import blend_targets

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/blend025-dual-paper"
RESEARCH = ROOT / "research/gaps"
MARKET_PATH = ROOT / "forward/e21/live_market.csv"
DIV_PATH = ROOT / "data/dividend_events/e22_dividend_events.csv"

LOCKED_ID = "BLEND_025"
BLEND_ALPHA = 0.25
FIN_CAP_50 = {"fin_lo": 0.35, "fin_hi": 0.50}
WINDOWS = {
    "full": (None, None),
    "oof_2011_2018": (date(2011, 1, 1), date(2018, 12, 31)),
    "validation_2019_2022": (date(2019, 1, 1), date(2022, 12, 31)),
    "sealed_2023_plus": (date(2023, 1, 1), None),
    "heldout_2019_plus": (date(2019, 1, 1), None),
}


def load_market() -> pd.DataFrame:
    market = pd.read_csv(MARKET_PATH, dtype={"code": str})
    market["date"] = pd.to_datetime(market["date"])
    required = set(ALL + ["TAIEX"])
    complete = market.groupby("date")["code"].apply(lambda s: required.issubset(set(s)))
    return market[market["date"].isin(complete[complete].index)].sort_values(["date", "code"])


def window_stats(nav: pd.DataFrame, start: date | None, end: date | None) -> dict:
    d = nav.copy()
    d["date"] = pd.to_datetime(d["date"]).dt.date
    if start is not None:
        d = d[d["date"] >= start]
    if end is not None:
        d = d[d["date"] <= end]
    d = d.reset_index(drop=True)
    if len(d) < 30:
        return {"cagr": None, "max_drawdown": None, "utility": None, "vol": None, "n_days": int(len(d))}
    d = d.copy()
    d["nav"] = d["nav"] / float(d["nav"].iloc[0])
    out = nav_stats(d)
    out["n_days"] = int(len(d))
    return out


def target_fin_stats(target: pd.DataFrame, start: date | None, end: date | None) -> dict:
    idx = pd.to_datetime(target.index).date
    m = np.ones(len(idx), dtype=bool)
    if start is not None:
        m &= idx >= start
    if end is not None:
        m &= idx <= end
    fin = target.loc[m, "Financial"]
    if len(fin) == 0:
        return {"mean": None, "max": None, "n": 0}
    return {"mean": float(fin.mean()), "max": float(fin.max()), "n": int(len(fin))}


def main() -> None:
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)

    print("loading market + dividends ...", flush=True)
    market = load_market()
    dividends = pd.read_csv(DIV_PATH, dtype={"code": str}) if DIV_PATH.exists() else pd.DataFrame()

    print("BASE_E16 features + sim ...", flush=True)
    _p, _s, base_target, base_regime = e16_features(market)
    nav_b, fills_b, meta_b = simulate_core(
        market,
        base_target,
        base_regime,
        dividends,
        apply_e22=True,
        e22_version=e22div.E22_V2S,
        apply_stock_div=True,
    )

    print(f"{LOCKED_ID} blend targets + sim (α={BLEND_ALPHA}) ...", flush=True)
    _p2, _s2, fin50_target, _ = e16_features_fin_cap(
        market, FIN_CAP_50["fin_lo"], FIN_CAP_50["fin_hi"]
    )
    blend_target = blend_targets(base_target, fin50_target, BLEND_ALPHA)
    nav_c, fills_c, meta_c = simulate_core(
        market,
        blend_target,
        base_regime,
        dividends,
        apply_e22=True,
        e22_version=e22div.E22_V2S,
        apply_stock_div=True,
    )

    nav_b.to_csv(OUT / "outputs" / "base_e16_daily_nav.csv", index=False)
    nav_c.to_csv(OUT / "outputs" / "blend025_daily_nav.csv", index=False)
    fills_b.to_csv(OUT / "outputs" / "base_e16_fills.csv", index=False)
    fills_c.to_csv(OUT / "outputs" / "blend025_fills.csv", index=False)
    base_target.to_csv(OUT / "outputs" / "base_e16_targets.csv")
    blend_target.to_csv(OUT / "outputs" / "blend025_targets.csv")

    jb = nav_b[["date", "nav"]].rename(columns={"nav": "nav_base"})
    jc = nav_c[["date", "nav"]].rename(columns={"nav": "nav_blend025"})
    joined = jb.merge(jc, on="date", how="inner")
    joined["rel_blend025_vs_base"] = joined["nav_blend025"] / joined["nav_base"]
    joined.to_csv(OUT / "outputs" / "dual_paper_nav_compare.csv", index=False)

    books = {}
    for name, nav, tgt, meta in [
        ("BASE_E16", nav_b, base_target, meta_b),
        (LOCKED_ID, nav_c, blend_target, meta_c),
    ]:
        win = {}
        for wname, (ws, we) in WINDOWS.items():
            st = window_stats(nav, ws, we)
            wt = target_fin_stats(tgt, ws, we)
            win[wname] = {**st, "fin_mean": wt["mean"], "fin_max": wt["max"]}
        books[name] = {
            "exact_t1_ok": bool(meta.get("exact_t1_ok")),
            "same_bar_fills": int(meta.get("same_bar_fills", -1)),
            "windows": win,
        }

    base_h = books["BASE_E16"]["windows"]["heldout_2019_plus"]
    blend_h = books[LOCKED_ID]["windows"]["heldout_2019_plus"]
    base_s = books["BASE_E16"]["windows"]["sealed_2023_plus"]
    blend_s = books[LOCKED_ID]["windows"]["sealed_2023_plus"]
    mdd_improve_pp = mdd_delta_pp(base_h["max_drawdown"], blend_h["max_drawdown"])
    cagr_giveback_pp = cagr_delta_pp(base_h["cagr"], blend_h["cagr"], missing_as_zero=True)
    sealed_mdd_improve_pp = mdd_delta_pp(base_s["max_drawdown"], blend_s["max_drawdown"])
    sealed_cagr_giveback_pp = cagr_delta_pp(base_s["cagr"], blend_s["cagr"], missing_as_zero=True)

    proposal = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "BLEND_025_DUAL_PAPER_OBSERVE_SLEEVE",
        "status": "OPERATING_OBSERVE",
        "live_wire": False,
        "soft_frozen_default_unchanged": True,
        "cutover_authorized": False,
        "locked_id": LOCKED_ID,
        "definition": {
            "alpha": BLEND_ALPHA,
            "formula": "α·FIN_CAP_50([0.35,0.50]) + (1-α)·Soft-Frozen BASE([0.50,0.95]), renormalized",
            "fin_cap_50_lock": FIN_CAP_50,
            "base_clip": {"financial_lo": 0.50, "financial_hi": 0.95},
        },
        "current_live_clip": {"financial_lo": 0.50, "financial_hi": 0.95},
        "exact_t1": {
            "base": books["BASE_E16"]["exact_t1_ok"],
            "blend025": books[LOCKED_ID]["exact_t1_ok"],
        },
        "books": books,
        "heldout_delta_vs_base": {
            "mdd_improve_pp": mdd_improve_pp,
            "cagr_giveback_pp": cagr_giveback_pp,
        },
        "sealed_delta_vs_base": {
            "mdd_improve_pp": sealed_mdd_improve_pp,
            "cagr_giveback_pp": sealed_cagr_giveback_pp,
        },
        "parent_artifacts": [
            "research/gaps/FINCAP50_SEALED_CAGR_IMPROVE_CHARTER.md",
            "research/gaps/FINCAP50_SEALED_CAGR_CHARTER_SCREEN.md",
            "research/gaps/FINCAP_BLEND025_DUAL_PAPER_PROMOTE_PROPOSAL.md",
        ],
        "ops_checklist": [
            "Keep Soft-Frozen default = BASE_E16 until human-approved cutover PR",
            "Run BLEND_025 dual paper ledgers in parallel with month-end monitor",
            "Re-check charter trailing gates (ytd / trailing_1y) each month-end",
            "Do not silent-edit Soft-Frozen; do not rewrite forward/e21 history",
            "Observe sleeve ≠ cutover license; FIN50/L4 cutover stays FROZEN",
        ],
        "non_goals": [
            "Auto live-wire from this observe sleeve",
            "Retune FIN_CAP_50 lock [0.35,0.50]",
            "Retune Soft-Frozen [0.50,0.95]",
            "Close or replace FIN50 / L4 dual-paper sleeves",
            "Claim CAGR≥20% / MDD≤15% as live results",
        ],
    }

    (OUT / "reports" / "blend025_dual_paper_observe.json").write_text(
        json.dumps(proposal, indent=2) + "\n"
    )
    (RESEARCH / "BLEND_025_DUAL_PAPER_OBSERVE.json").write_text(
        json.dumps(proposal, indent=2) + "\n"
    )

    lines = [
        "# BLEND_025 Dual-Paper Observe Sleeve",
        "",
        f"Generated: `{proposal['generated_at_utc']}`",
        "Status: **OPERATING OBSERVE** — Soft-Frozen live default **unchanged** "
        "(`Financial∈[0.50,0.95]`).",
        "",
        "## Locked challenger",
        "",
        f"- **{LOCKED_ID}**: α={BLEND_ALPHA}·FIN_CAP_50([0.35,0.50]) + "
        f"{1.0 - BLEND_ALPHA:.2f}·Soft-Frozen BASE, renormalized",
        "- Regime router / Exact T+1 / E22_v2s unchanged vs live E16",
        "",
        "## Dual paper metrics",
        "",
        "| Book | Window | CAGR | MDD | Fin mean | Fin max | Exact T+1 |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for book, payload in books.items():
        for wname, st in payload["windows"].items():
            lines.append(
                f"| {book} | {wname} | "
                f"{(st['cagr'] or float('nan')):.2%} | {(st['max_drawdown'] or float('nan')):.2%} | "
                f"{(st['fin_mean'] or float('nan')):.1%} | {(st['fin_max'] or float('nan')):.1%} | "
                f"{payload['exact_t1_ok']} |"
            )
    lines += [
        "",
        f"Held-out vs BASE: MDD improve **{mdd_improve_pp:.2f} pp**; "
        f"CAGR giveback **{cagr_giveback_pp:.2f} pp**.",
        f"Sealed vs BASE: MDD improve **{sealed_mdd_improve_pp:.2f} pp**; "
        f"CAGR giveback **{sealed_cagr_giveback_pp:.2f} pp**.",
        "",
        "## Ops checklist",
        "",
    ]
    for i, item in enumerate(proposal["ops_checklist"], 1):
        lines.append(f"{i}. {item}")
    lines += [
        "",
        "## Explicit non-goals",
        "",
    ]
    for item in proposal["non_goals"]:
        lines.append(f"- {item}")
    lines += [
        "",
        "## Label",
        "",
        "`BLEND_025_DUAL_PAPER_OBSERVE_SLEEVE`",
        "",
        "Artifacts:",
        f"- `{OUT / 'reports' / 'blend025_dual_paper_observe.json'}`",
        f"- `{OUT / 'outputs' / 'dual_paper_nav_compare.csv'}`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "BLEND_025_DUAL_PAPER_OBSERVE.md").write_text(md)
    (RESEARCH / "BLEND_025_DUAL_PAPER_OBSERVE.md").write_text(md)
    print(
        json.dumps(
            {
                "label": proposal["label"],
                "status": proposal["status"],
                "live_wire": False,
                "heldout_mdd_improve_pp": mdd_improve_pp,
                "heldout_cagr_giveback_pp": cagr_giveback_pp,
                "sealed_mdd_improve_pp": sealed_mdd_improve_pp,
                "sealed_cagr_giveback_pp": sealed_cagr_giveback_pp,
            },
            indent=2,
        )
    )
    print("EXIT:0")


if __name__ == "__main__":
    main()
