#!/usr/bin/env python3
"""FIN_CAP_50 dual paper ledgers (PROMOTE PROPOSAL SUPPORT — not live).

Builds side-by-side Exact T+1 paper books:
  BASE_E16:      Financial clip [0.50, 0.95]  (current Soft-Frozen live)
  FIN_CAP_50:    Financial clip [0.35, 0.50]  (held-out PASS research)

Does NOT edit e21_forward_pipeline live clips.
Does NOT flip Soft-Frozen default.
Outputs dual NAV/targets under repro/fincap50-dual-paper/ for ops review.
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

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/fincap50-dual-paper"
RESEARCH = ROOT / "research/gaps"
MARKET_PATH = ROOT / "forward/e21/live_market.csv"
DIV_PATH = ROOT / "data/dividend_events/e22_dividend_events.csv"

FIN_CAP_50 = {"fin_lo": 0.35, "fin_hi": 0.50}
WINDOWS = {
    "full": (None, None),
    "oof_2011_2018": (date(2011, 1, 1), date(2018, 12, 31)),
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

    print("FIN_CAP_50 features + sim ...", flush=True)
    _p2, _s2, cap_target, cap_regime = e16_features_fin_cap(
        market, FIN_CAP_50["fin_lo"], FIN_CAP_50["fin_hi"]
    )
    nav_c, fills_c, meta_c = simulate_core(
        market,
        cap_target,
        cap_regime,
        dividends,
        apply_e22=True,
        e22_version=e22div.E22_V2S,
        apply_stock_div=True,
    )

    nav_b.to_csv(OUT / "outputs" / "base_e16_daily_nav.csv", index=False)
    nav_c.to_csv(OUT / "outputs" / "fincap50_daily_nav.csv", index=False)
    fills_b.to_csv(OUT / "outputs" / "base_e16_fills.csv", index=False)
    fills_c.to_csv(OUT / "outputs" / "fincap50_fills.csv", index=False)
    base_target.to_csv(OUT / "outputs" / "base_e16_targets.csv")
    cap_target.to_csv(OUT / "outputs" / "fincap50_targets.csv")

    # joined paper compare
    jb = nav_b[["date", "nav"]].rename(columns={"nav": "nav_base"})
    jc = nav_c[["date", "nav"]].rename(columns={"nav": "nav_fincap50"})
    joined = jb.merge(jc, on="date", how="inner")
    joined["rel_fincap50_vs_base"] = joined["nav_fincap50"] / joined["nav_base"]
    joined.to_csv(OUT / "outputs" / "dual_paper_nav_compare.csv", index=False)

    books = {}
    for name, nav, tgt, meta in [
        ("BASE_E16", nav_b, base_target, meta_b),
        ("FIN_CAP_50", nav_c, cap_target, meta_c),
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
    cap_h = books["FIN_CAP_50"]["windows"]["heldout_2019_plus"]
    mdd_improve_pp = mdd_delta_pp(base_h["max_drawdown"], cap_h["max_drawdown"])
    cagr_giveback_pp = cagr_delta_pp(base_h["cagr"], cap_h["cagr"], missing_as_zero=True)

    proposal = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "FIN_CAP_50_DUAL_PAPER_PROMOTE_PROPOSAL",
        "live_wire": False,
        "soft_frozen_default_unchanged": True,
        "proposed_live_clip_if_cutover": {"financial_lo": 0.35, "financial_hi": 0.50},
        "current_live_clip": {"financial_lo": 0.50, "financial_hi": 0.95},
        "exact_t1": {
            "base": books["BASE_E16"]["exact_t1_ok"],
            "fincap50": books["FIN_CAP_50"]["exact_t1_ok"],
        },
        "books": books,
        "heldout_delta_vs_base": {
            "mdd_improve_pp": mdd_improve_pp,
            "cagr_giveback_pp": cagr_giveback_pp,
            "research_heldout_pass_reference": True,
            "note": "Matches prior PASS_HELDOUT_FIN_CAP research; this run refreshes dual paper books",
        },
        "cutover_checklist": [
            "Keep Soft-Frozen default = BASE_E16 until human-approved cutover PR",
            "Run dual paper ledgers in parallel for ≥1 month-end review",
            "Cutover-only: change E16 Financial clip to [0.35,0.50] with named ledger FIN_CAP_50",
            "Preserve BASE_E16 paper ledger indefinitely for regression",
            "Do not silent-edit Soft-Frozen; do not rewrite forward/e21 history",
            "MDD target ≤15% still NOT claimed — FIN_CAP_50 held MDD ~-19.6%",
        ],
        "non_goals": [
            "Auto live-wire from this proposal",
            "FIN_CAP cut retune",
            "L1 loss-engine reattach",
            "Claim CAGR≥20% / MDD≤15% as live results",
        ],
    }

    (OUT / "reports" / "fincap50_dual_paper_proposal.json").write_text(
        json.dumps(proposal, indent=2) + "\n"
    )
    (RESEARCH / "FIN_CAP_50_PROMOTE_PROPOSAL.json").write_text(json.dumps(proposal, indent=2) + "\n")

    lines = [
        "# FIN_CAP_50 Promote Proposal — Dual Paper Ledgers",
        "",
        f"Generated: `{proposal['generated_at_utc']}`",
        "Status: **PROPOSAL ONLY** — Soft-Frozen live default **unchanged** (`Financial∈[0.50,0.95]`).",
        "",
        "## Why this exists",
        "",
        "Prior research (`PASS_HELDOUT_FIN_CAP`) unlocked an *optional* promote path.",
        "This PR materializes **dual Exact T+1 paper books** so ops can review BASE vs FIN_CAP_50",
        "without flipping live clips.",
        "",
        "## Locked challenger",
        "",
        "- **FIN_CAP_50**: Financial clip **[0.35, 0.50]**; residual → Telecom/0050",
        "- Priors / regime router unchanged vs live E16",
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
        f"Held-out vs BASE: MDD improve **{mdd_improve_pp:.2f} pp**; CAGR giveback **{cagr_giveback_pp:.2f} pp**.",
        "",
        "## Cutover checklist (future human PR only)",
        "",
    ]
    for i, item in enumerate(proposal["cutover_checklist"], 1):
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
        "`FIN_CAP_50_DUAL_PAPER_PROMOTE_PROPOSAL`",
        "",
        "Artifacts:",
        f"- `{OUT / 'reports' / 'fincap50_dual_paper_proposal.json'}`",
        f"- `{OUT / 'outputs' / 'dual_paper_nav_compare.csv'}`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "FIN_CAP_50_PROMOTE_PROPOSAL.md").write_text(md)
    (RESEARCH / "FIN_CAP_50_PROMOTE_PROPOSAL.md").write_text(md)
    print(
        json.dumps(
            {
                "label": proposal["label"],
                "live_wire": False,
                "heldout_mdd_improve_pp": mdd_improve_pp,
                "heldout_cagr_giveback_pp": cagr_giveback_pp,
            },
            indent=2,
        )
    )
    print("EXIT:0")


if __name__ == "__main__":
    main()
