#!/usr/bin/env python3
"""L4_DD_PATH_08_50 dual paper ledgers (PROMOTE SUPPORT — not live).

Side-by-side Exact T+1 paper books:
  BASE_E16:         Soft-Frozen Financial clip [0.50, 0.95] (current live)
  L4_DD_PATH_08_50: FIN_CAP_50 weights only while TAIEX DD from 252d peak <= -8%;
                    else Soft-Frozen BASE (held-out PASS_HELDOUT_L4)

Does NOT edit e21_forward_pipeline live clips.
Does NOT flip Soft-Frozen default.
Does NOT auto live-wire path-dependent logic.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from e50_early_stack_combined_nav import ALL, e16_features, nav_stats, simulate_core
import e22_dividend_accounting as e22div
from e16_fin_cap_oof_challenger import e16_features_fin_cap
from mdd_l4_loss_engine_oof import dd_path_target

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/l4-dd-path-dual-paper"
RESEARCH = ROOT / "research/gaps"
MARKET_PATH = ROOT / "forward/e21/live_market.csv"
DIV_PATH = ROOT / "data/dividend_events/e22_dividend_events.csv"

LOCKED_ID = "L4_DD_PATH_08_50"
LOCKED_DD_THR = -0.08
LOCKED_FIN_LO, LOCKED_FIN_HI = 0.35, 0.50
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


def flag_share(flag: pd.Series, start: date | None, end: date | None) -> float | None:
    idx = pd.to_datetime(flag.index).date
    m = np.ones(len(idx), dtype=bool)
    if start is not None:
        m &= idx >= start
    if end is not None:
        m &= idx <= end
    sub = flag.loc[m]
    if len(sub) == 0:
        return None
    return float(sub.astype(bool).mean())


def main() -> None:
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)

    print("loading market + dividends ...", flush=True)
    market = load_market()
    dividends = pd.read_csv(DIV_PATH, dtype={"code": str}) if DIV_PATH.exists() else pd.DataFrame()

    print("BASE_E16 features + sim ...", flush=True)
    prices, _s, base_target, base_regime = e16_features(market)
    nav_b, fills_b, meta_b = simulate_core(
        market,
        base_target,
        base_regime,
        dividends,
        apply_e22=True,
        e22_version=e22div.E22_V2S,
        apply_stock_div=True,
    )

    print(f"{LOCKED_ID} features + sim ...", flush=True)
    _p2, _s2, fin50_target, _ = e16_features_fin_cap(market, LOCKED_FIN_LO, LOCKED_FIN_HI)
    l4_target, l4_flag = dd_path_target(base_target, fin50_target, prices, LOCKED_DD_THR)
    nav_l, fills_l, meta_l = simulate_core(
        market,
        l4_target,
        base_regime,
        dividends,
        apply_e22=True,
        e22_version=e22div.E22_V2S,
        apply_stock_div=True,
    )

    nav_b.to_csv(OUT / "outputs" / "base_e16_daily_nav.csv", index=False)
    nav_l.to_csv(OUT / "outputs" / "l4_dd_path_daily_nav.csv", index=False)
    fills_b.to_csv(OUT / "outputs" / "base_e16_fills.csv", index=False)
    fills_l.to_csv(OUT / "outputs" / "l4_dd_path_fills.csv", index=False)
    base_target.to_csv(OUT / "outputs" / "base_e16_targets.csv")
    l4_target.to_csv(OUT / "outputs" / "l4_dd_path_targets.csv")
    pd.DataFrame({"date": l4_flag.index, "dd_path_cap_on": l4_flag.astype(bool).values}).to_csv(
        OUT / "outputs" / "l4_dd_path_cap_flag.csv", index=False
    )

    jb = nav_b[["date", "nav"]].rename(columns={"nav": "nav_base"})
    jl = nav_l[["date", "nav"]].rename(columns={"nav": "nav_l4"})
    joined = jb.merge(jl, on="date", how="inner")
    joined["rel_l4_vs_base"] = joined["nav_l4"] / joined["nav_base"]
    joined.to_csv(OUT / "outputs" / "dual_paper_nav_compare.csv", index=False)

    books = {}
    for name, nav, tgt, meta, flag in [
        ("BASE_E16", nav_b, base_target, meta_b, None),
        (LOCKED_ID, nav_l, l4_target, meta_l, l4_flag),
    ]:
        win = {}
        for wname, (ws, we) in WINDOWS.items():
            st = window_stats(nav, ws, we)
            wt = target_fin_stats(tgt, ws, we)
            row = {**st, "fin_mean": wt["mean"], "fin_max": wt["max"]}
            if flag is not None:
                row["dd_path_on_share"] = flag_share(flag, ws, we)
            win[wname] = row
        books[name] = {
            "exact_t1_ok": bool(meta.get("exact_t1_ok")),
            "same_bar_fills": int(meta.get("same_bar_fills", -1)),
            "windows": win,
        }

    # Prefer sealed window for ops delta (matches held-out sealed gate); also report heldout_2019+
    sealed_b = books["BASE_E16"]["windows"]["sealed_2023_plus"]
    sealed_l = books[LOCKED_ID]["windows"]["sealed_2023_plus"]
    sealed_mdd_pp = (abs(sealed_b["max_drawdown"] or 9) - abs(sealed_l["max_drawdown"] or 9)) * 100
    sealed_cagr_gb_pp = ((sealed_b["cagr"] or 0) - (sealed_l["cagr"] or 0)) * 100

    val_b = books["BASE_E16"]["windows"]["validation_2019_2022"]
    val_l = books[LOCKED_ID]["windows"]["validation_2019_2022"]
    val_mdd_pp = (abs(val_b["max_drawdown"] or 9) - abs(val_l["max_drawdown"] or 9)) * 100
    val_cagr_gb_pp = ((val_b["cagr"] or 0) - (val_l["cagr"] or 0)) * 100

    proposal = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "L4_DD_PATH_DUAL_PAPER_PROMOTE_PROPOSAL",
        "locked_id": LOCKED_ID,
        "mechanism": {
            "type": "dd_path",
            "dd_thr": LOCKED_DD_THR,
            "fin_lo_when_on": LOCKED_FIN_LO,
            "fin_hi_when_on": LOCKED_FIN_HI,
            "else": "Soft-Frozen BASE Financial [0.50, 0.95]",
        },
        "live_wire": False,
        "soft_frozen_default_unchanged": True,
        "research_heldout_pass_reference": "PASS_HELDOUT_L4",
        "current_live_clip": {"financial_lo": 0.50, "financial_hi": 0.95},
        "exact_t1": {
            "base": books["BASE_E16"]["exact_t1_ok"],
            "l4": books[LOCKED_ID]["exact_t1_ok"],
        },
        "books": books,
        "validation_delta_vs_base": {
            "mdd_improve_pp": val_mdd_pp,
            "cagr_giveback_pp": val_cagr_gb_pp,
        },
        "sealed_delta_vs_base": {
            "mdd_improve_pp": sealed_mdd_pp,
            "cagr_giveback_pp": sealed_cagr_gb_pp,
        },
        "cutover_checklist": [
            "Keep Soft-Frozen default = BASE_E16 until human-approved cutover PR",
            "Run dual paper ledgers in parallel for ≥1 month-end review",
            "Cutover would wire path-dependent DD-path logic (not a static clip swap)",
            "Preserve BASE_E16 paper ledger indefinitely for regression",
            "Do not silent-edit Soft-Frozen; do not rewrite forward/e21 history",
            "FIN_CAP_50 static promote remains separately NOT_READY_SEALED_CAGR — do not conflate",
        ],
        "non_goals": [
            "Auto live-wire from this proposal",
            "Soft-Frozen flip",
            "L4 lock retune / reopen L1–L3 / FIN50 static promote",
            "Claim CAGR≥20% / MDD≤15% as live results",
        ],
    }

    (OUT / "reports" / "l4_dd_path_dual_paper_proposal.json").write_text(
        json.dumps(proposal, indent=2) + "\n"
    )
    (RESEARCH / "L4_DD_PATH_PROMOTE_PROPOSAL.json").write_text(json.dumps(proposal, indent=2) + "\n")

    lines = [
        "# L4_DD_PATH_08_50 Promote Proposal — Dual Paper Ledgers",
        "",
        f"Generated: `{proposal['generated_at_utc']}`",
        "Status: **PROPOSAL ONLY** — Soft-Frozen live default **unchanged** (`Financial∈[0.50,0.95]`).",
        "",
        "## Why this exists",
        "",
        "Held-out research (`PASS_HELDOUT_L4`) unlocked an *optional* dual-paper observation path.",
        "This PR materializes **dual Exact T+1 paper books** (BASE vs path-dependent L4)",
        "without flipping live clips.",
        "",
        "## Locked challenger",
        "",
        f"- **{LOCKED_ID}**: apply FIN_CAP **[0.35, 0.50]** only while TAIEX active drawdown",
        "  from 252d peak **≤ −8%**; else Soft-Frozen BASE",
        "- Priors / regime router unchanged vs live E16",
        "",
        "## Dual paper metrics",
        "",
        "| Book | Window | CAGR | MDD | Fin mean | Fin max | DD-path on | Exact T+1 |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for book, payload in books.items():
        for wname, st in payload["windows"].items():
            on_share = st.get("dd_path_on_share")
            on_s = "—" if on_share is None else f"{on_share:.1%}"
            lines.append(
                f"| {book} | {wname} | "
                f"{(st['cagr'] or float('nan')):.2%} | {(st['max_drawdown'] or float('nan')):.2%} | "
                f"{(st['fin_mean'] or float('nan')):.1%} | {(st['fin_max'] or float('nan')):.1%} | "
                f"{on_s} | {payload['exact_t1_ok']} |"
            )
    lines += [
        "",
        f"Validation vs BASE: MDD improve **{val_mdd_pp:.2f} pp**; CAGR giveback **{val_cagr_gb_pp:.2f} pp**.",
        f"Sealed vs BASE: MDD improve **{sealed_mdd_pp:.2f} pp**; CAGR giveback **{sealed_cagr_gb_pp:.2f} pp**.",
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
        "`L4_DD_PATH_DUAL_PAPER_PROMOTE_PROPOSAL`",
        "",
        "Artifacts:",
        f"- `{OUT / 'reports' / 'l4_dd_path_dual_paper_proposal.json'}`",
        f"- `{OUT / 'outputs' / 'dual_paper_nav_compare.csv'}`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "L4_DD_PATH_PROMOTE_PROPOSAL.md").write_text(md)
    (RESEARCH / "L4_DD_PATH_PROMOTE_PROPOSAL.md").write_text(md)
    print(
        json.dumps(
            {
                "label": proposal["label"],
                "live_wire": False,
                "validation_mdd_improve_pp": val_mdd_pp,
                "validation_cagr_giveback_pp": val_cagr_gb_pp,
                "sealed_mdd_improve_pp": sealed_mdd_pp,
                "sealed_cagr_giveback_pp": sealed_cagr_gb_pp,
            },
            indent=2,
        )
    )
    print("EXIT:0")


if __name__ == "__main__":
    main()
