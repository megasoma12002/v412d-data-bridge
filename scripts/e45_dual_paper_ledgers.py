#!/usr/bin/env python3
"""E45 dual-paper ledgers (OPERATING OBSERVE — not live).

Side-by-side Exact T+1 paper books:
  BASE_E16_E18_E22_v2s — Soft-Frozen early-stack + formal E22_v2s
  CHAL_E45_E3          — same stack + E45 E3_VOLTARGET_WINNER overlay

Opened by human ballot: ``E45 OPEN dual-paper observe``.
Does NOT edit e21 forward live clips, Soft-Frozen default, or authorize stitch.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from research_metric_helpers import mdd_delta_pp, cagr_delta_pp
from e50_early_stack_combined_nav import ALL, e16_features, nav_stats, simulate_core
import e45_crisis_core as e45

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/e45-dual-paper-observe"
RESEARCH = ROOT / "research/e45"
MARKET_PATH = ROOT / "forward/e21/live_market.csv"
DIV_PATH = ROOT / "data/dividend_events/e22_dividend_events.csv"

BASE_ID = "BASE_E16_E18_E22_v2s"
CHAL_ID = "CHAL_E45_E3"
E45_PROFILE = "E3_VOLTARGET_WINNER"
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
        return {
            "cagr": None,
            "max_drawdown": None,
            "utility": None,
            "vol": None,
            "n_days": int(len(d)),
        }
    d = d.copy()
    d["nav"] = d["nav"] / float(d["nav"].iloc[0])
    out = nav_stats(d)
    out["n_days"] = int(len(d))
    return out


def main() -> None:
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)

    print("loading market + dividends ...", flush=True)
    market = load_market()
    dividends = pd.read_csv(DIV_PATH, dtype={"code": str}) if DIV_PATH.exists() else pd.DataFrame()

    print(f"{BASE_ID} features + sim ...", flush=True)
    _p, _s, base_target, base_regime = e16_features(market)
    nav_b, fills_b, meta_b = simulate_core(
        market,
        base_target,
        base_regime,
        dividends,
        apply_e22=True,
        apply_stock_div=True,
        e45_exposure=None,
    )

    print(f"{CHAL_ID} {E45_PROFILE} + sim ...", flush=True)
    close_eq = (
        market[market["code"].isin(ALL)]
        .pivot(index="date", columns="code", values="close")
        .sort_index()
        .ffill()
    )
    e45_e3 = e45.compute_exposure(close_eq, E45_PROFILE)["exposure"]
    nav_c, fills_c, meta_c = simulate_core(
        market,
        base_target,
        base_regime,
        dividends,
        apply_e22=True,
        apply_stock_div=True,
        e45_exposure=e45_e3,
    )

    nav_b.to_csv(OUT / "outputs" / "base_e16_e18_e22_v2s_daily_nav.csv", index=False)
    nav_c.to_csv(OUT / "outputs" / "chal_e45_e3_daily_nav.csv", index=False)
    fills_b.to_csv(OUT / "outputs" / "base_e16_e18_e22_v2s_fills.csv", index=False)
    fills_c.to_csv(OUT / "outputs" / "chal_e45_e3_fills.csv", index=False)
    base_target.to_csv(OUT / "outputs" / "base_targets.csv")
    e45_e3.rename("e45_e3_exposure").to_csv(OUT / "outputs" / "chal_e45_e3_exposure.csv")

    jb = nav_b[["date", "nav"]].rename(columns={"nav": "nav_base"})
    jc = nav_c[["date", "nav"]].rename(columns={"nav": "nav_chal_e45_e3"})
    joined = jb.merge(jc, on="date", how="inner")
    joined["rel_chal_vs_base"] = joined["nav_chal_e45_e3"] / joined["nav_base"]
    joined.to_csv(OUT / "outputs" / "dual_paper_nav_compare.csv", index=False)

    books: dict = {}
    for name, nav, meta in [
        (BASE_ID, nav_b, meta_b),
        (CHAL_ID, nav_c, meta_c),
    ]:
        win = {wname: window_stats(nav, ws, we) for wname, (ws, we) in WINDOWS.items()}
        books[name] = {
            "exact_t1_ok": bool(meta.get("exact_t1_ok")),
            "same_bar_fills": int(meta.get("same_bar_fills", -1)),
            "mean_e45_exposure": meta.get("mean_e45_exposure"),
            "windows": win,
        }

    base_h = books[BASE_ID]["windows"]["heldout_2019_plus"]
    chal_h = books[CHAL_ID]["windows"]["heldout_2019_plus"]
    base_s = books[BASE_ID]["windows"]["sealed_2023_plus"]
    chal_s = books[CHAL_ID]["windows"]["sealed_2023_plus"]
    mdd_improve_pp = mdd_delta_pp(base_h["max_drawdown"], chal_h["max_drawdown"])
    cagr_giveback_pp = cagr_delta_pp(base_h["cagr"], chal_h["cagr"], missing_as_zero=True)
    sealed_mdd_improve_pp = mdd_delta_pp(base_s["max_drawdown"], chal_s["max_drawdown"])
    sealed_cagr_giveback_pp = cagr_delta_pp(
        base_s["cagr"], chal_s["cagr"], missing_as_zero=True
    )

    proposal = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "E45_DUAL_PAPER_OBSERVE_SLEEVE",
        "status": "OPERATING_OBSERVE",
        "live_wire": False,
        "soft_frozen_default_unchanged": True,
        "stitch_authorized": False,
        "cutover_authorized": False,
        "ballot": "E45 OPEN dual-paper observe",
        "base_id": BASE_ID,
        "locked_challenger": CHAL_ID,
        "e45_profile": E45_PROFILE,
        "claimed_mdd_status": e45.CLAIMED_MDD_STATUS,
        "primary_comparable_mdd": e45.PRIMARY_COMPARABLE_MDD,
        "current_live_clip": {"financial_lo": 0.50, "financial_hi": 0.95},
        "exact_t1": {
            "base": books[BASE_ID]["exact_t1_ok"],
            "chal_e45_e3": books[CHAL_ID]["exact_t1_ok"],
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
            "research/ops/E45_LIVE_STITCH_CHARTER.md",
            "research/ops/E45_STAGE12_STATUS.md",
            "research/e45/E45_DUAL_PAPER_OBSERVE_DESIGN.md",
            "research/ops/E45_DUAL_PAPER_OBSERVE_CHECKLIST.md",
            "research/ops/E45_MDD_1316_NARRATIVE_RETIREMENT.md",
            "research/ops/E45_DUAL_PAPER_OBSERVE_OPEN.md",
        ],
        "ops_checklist": [
            "Keep Soft-Frozen live default = BASE until a separate stitch / cutover PR",
            "Run BASE + CHAL_E45_E3 paper ledgers in parallel with month-end monitor",
            "Re-check YTD / trailing_1y PAUSE gates each month-end (observe ≠ promote)",
            "Do not silent-edit Soft-Frozen; do not rewrite forward/e21 history",
            "Observe sleeve ≠ stitch license; second human stitch ACCEPT still required",
            "Never cite −13.16%; use dated lineage / challenger MDDs only",
        ],
        "non_goals": [
            "Auto live-wire / four-layer stitch from this observe sleeve",
            "Soft-Frozen clip flip",
            "DEFAULT books flip away from E22_v2s_tw",
            "Invent a replacement for retired −13.16% narrative",
            "Bundle FIN50 / L4 / BLEND / odd-lot / tax DEFAULT promote",
        ],
    }

    (OUT / "reports" / "e45_dual_paper_observe.json").write_text(
        json.dumps(proposal, indent=2) + "\n"
    )
    (RESEARCH / "E45_DUAL_PAPER_OBSERVE.json").write_text(json.dumps(proposal, indent=2) + "\n")

    lines = [
        "# E45 Dual-Paper Observe Sleeve",
        "",
        f"Generated: `{proposal['generated_at_utc']}`",
        "Status: **OPERATING OBSERVE** — Soft-Frozen live default **unchanged** "
        "(`Financial∈[0.50,0.95]`); live stitch **FORBIDDEN**.",
        "",
        "## Locked paper books",
        "",
        f"- **{BASE_ID}**: Soft-Frozen early-stack Exact T+1 + E22_v2s formal books",
        f"- **{CHAL_ID}**: same stack + E45 `{E45_PROFILE}` exposure overlay",
        f"- Claimed −13.16%: **`{e45.CLAIMED_MDD_STATUS}`** (do not cite)",
        f"- Primary comparable MDD: E1.1 val **{e45.PRIMARY_COMPARABLE_MDD:.2%}** (dated lineage)",
        "",
        "## Dual paper metrics",
        "",
        "| Book | Window | CAGR | MDD | n_days | Exact T+1 |",
        "|---|---|---:|---:|---:|---|",
    ]
    for book, payload in books.items():
        for wname, st in payload["windows"].items():
            cagr = st["cagr"]
            mdd = st["max_drawdown"]
            lines.append(
                f"| {book} | {wname} | "
                f"{(cagr if cagr is not None else float('nan')):.2%} | "
                f"{(mdd if mdd is not None else float('nan')):.2%} | "
                f"{st['n_days']} | {payload['exact_t1_ok']} |"
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
    lines += ["", "## Explicit non-goals", ""]
    for item in proposal["non_goals"]:
        lines.append(f"- {item}")
    lines += [
        "",
        "## Label",
        "",
        "`E45_DUAL_PAPER_OBSERVE_SLEEVE`",
        "",
        "Artifacts:",
        f"- `{OUT / 'reports' / 'e45_dual_paper_observe.json'}`",
        f"- `{OUT / 'outputs' / 'dual_paper_nav_compare.csv'}`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "E45_DUAL_PAPER_OBSERVE.md").write_text(md)
    (RESEARCH / "E45_DUAL_PAPER_OBSERVE.md").write_text(md)
    print(
        json.dumps(
            {
                "label": proposal["label"],
                "status": proposal["status"],
                "live_wire": False,
                "stitch_authorized": False,
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
