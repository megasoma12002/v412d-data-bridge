#!/usr/bin/env python3
"""Round-1 analyses for authorized multi-track research reopen.

Challenger-only. Does not edit SOFT_FROZEN ledgers or promote anything.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


def nav_stats(nav: pd.Series) -> dict:
    nav = nav.dropna()
    if len(nav) < 3:
        return {"cagr": None, "mdd": None, "util": None, "n": int(len(nav))}
    r = nav.pct_change().dropna()
    years = max(len(r) / 252.0, 1e-9)
    cagr = float((nav.iloc[-1] / nav.iloc[0]) ** (1 / years) - 1)
    mdd = float((nav / nav.cummax() - 1).min())
    return {"cagr": cagr, "mdd": mdd, "util": cagr - 0.5 * abs(mdd), "n": int(len(nav))}


def load_nav_csv(path: Path, col: str = "nav") -> pd.Series:
    d = pd.read_csv(path, parse_dates=["date"])
    return d.set_index("date")[col].astype(float).sort_index()


def e22_v3_payment_vs_ex(out: Path) -> dict:
    """H1 proxy: compare early-stack books already computed; note payment-date needs event field.

    Uses dividend_events cash_payment_date when present to estimate delayed credit
    drag vs ex-date credit on a simple buy-and-hold sleeve proxy of E16 names.
    """
    div = pd.read_csv("data/dividend_events/e22_dividend_events.csv", dtype={"code": str})
    div["cash_ex_date"] = pd.to_datetime(div["cash_ex_date"], errors="coerce")
    div["cash_payment_date"] = pd.to_datetime(div["cash_payment_date"], errors="coerce")
    div["cash_dividend"] = pd.to_numeric(div["cash_dividend"], errors="coerce")
    codes = ["2880", "2886", "2892", "5880", "2412", "3045", "4904", "0050"]
    div = div[div["code"].isin(codes)].dropna(subset=["cash_ex_date", "cash_dividend"])
    has_pay = div["cash_payment_date"].notna().mean()
    lag_days = (div["cash_payment_date"] - div["cash_ex_date"]).dt.days
    summary = {
        "hypothesis": "H1_payment_date_vs_ex_date",
        "n_events": int(len(div)),
        "frac_with_payment_date": float(has_pay),
        "lag_days_median": float(lag_days.dropna().median()) if lag_days.notna().any() else None,
        "lag_days_p90": float(lag_days.dropna().quantile(0.9)) if lag_days.notna().any() else None,
        "note": (
            "Most events lack cash_payment_date in ledger; Round-1 cannot fairly simulate "
            "payment-date credits until payment dates are backfilled. "
            "Ex-date credit (E22_v2) remains baseline. Flagged as DATA_GAP for E22_v3 H1."
        ),
        "decision": "INCONCLUSIVE_DATA_GAP" if has_pay < 0.5 else "READY_FOR_SANDBOX_SIM",
    }
    # Tax haircut static impact on early-stack E22 lift (H2 documentation)
    core = Path("repro/early-stack-combined-nav-20260904/outputs/e16_e18_daily_nav.csv")
    core_e22 = Path("repro/early-stack-combined-nav-20260904/outputs/e16_e18_e22_daily_nav.csv")
    if core.exists() and core_e22.exists():
        a, b = load_nav_csv(core), load_nav_csv(core_e22)
        sa, sb = nav_stats(a), nav_stats(b)
        lift = (sb["cagr"] or 0) - (sa["cagr"] or 0)
        summary["e22_full_cagr_lift_vs_no_div"] = lift
        summary["h2_tax_haircut_illustrative"] = {
            t: {"approx_cagr_lift_if_linear": lift * (1 - t), "tax": t}
            for t in (0.0, 0.1, 0.2)
        }
    (out / "e22_v3_round1.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def e45_tradeoff(out: Path) -> dict:
    metrics = Path("repro/e45-c1-v412e0-original-20260904/outputs/e45c1_window_metrics.csv")
    if not metrics.exists():
        return {"status": "MISSING_C1_ARTIFACT"}
    m = pd.read_csv(metrics)
    rows = []
    for w in ["Validation_2019_2022", "Full", "Crisis_2008_2009"]:
        for s in ["D_FORMAL_ROUTER", "E45_E3_VOLTARGET_WINNER", "E45_E1_BINARY"]:
            r = m[(m.window == w) & (m.strategy == s)]
            if len(r):
                rows.append(r.iloc[0].to_dict())
    d_val = next(x for x in rows if x["window"] == "Validation_2019_2022" and x["strategy"] == "D_FORMAL_ROUTER")
    e3_val = next(x for x in rows if x["window"] == "Validation_2019_2022" and x["strategy"] == "E45_E3_VOLTARGET_WINNER")
    report = {
        "status": "TRADEOFF_TABLE",
        "panel": "ORIGINAL_V412E0_ACTIONS_ARTIFACT",
        "validation": {
            "D_ret": d_val.get("ret"),
            "D_mdd": d_val.get("mdd"),
            "D_sharpe": d_val.get("sharpe"),
            "E3_ret": e3_val.get("ret"),
            "E3_mdd": e3_val.get("mdd"),
            "E3_sharpe": e3_val.get("sharpe"),
            "ret_ratio_e3_over_d": (e3_val["ret"] / d_val["ret"]) if d_val.get("ret") else None,
            "mdd_improvement_abs": abs(d_val["mdd"]) - abs(e3_val["mdd"]),
        },
        "governance_fork": {
            "keep_B": "Retain D; E45 API only (current)",
            "promote_A_accept_tradeoff": "Promote E3-locked profile knowing return/Sharpe below D floors",
            "requires_phrase": "APPROVE E45_v1_E3_LOCKED_ACCEPT_RETURN_TRADEOFF",
        },
        "rows": rows,
        "decision": "AWAITING_GOVERNANCE_CHOICE_A_OR_B",
    }
    (out / "e45_rereview_round1.json").write_text(json.dumps(report, indent=2) + "\n")
    md = f"""# E45 Re-review Round-1 Tradeoff

Panel: original v412e0

| | D | E3 |
|---|---:|---:|
| Validation ret | {d_val.get('ret')} | {e3_val.get('ret')} |
| Validation MDD | {d_val.get('mdd')} | {e3_val.get('mdd')} |
| Validation Sharpe | {d_val.get('sharpe')} | {e3_val.get('sharpe')} |
| E3/D ret ratio | | {report['validation']['ret_ratio_e3_over_d']} |

To promote despite floors, approve: `APPROVE E45_v1_E3_LOCKED_ACCEPT_RETURN_TRADEOFF`
"""
    (out / "E45_REREVIEW_ROUND1.md").write_text(md)
    Path("research/reopen/E45_REREVIEW_ROUND1.md").write_text(md)
    return report


def g4_cash_deleverage(out: Path) -> dict:
    """H1: scale combined book equity by min(e45_exposure, k) extra cash cut."""
    mix = Path("forward/e50_stack/nav_combined.csv")
    if not mix.exists():
        return {"status": "MISSING_E50_STACK"}
    d = pd.read_csv(mix, parse_dates=["date"]).set_index("date")
    # Reconstruct a deep-deleverage path: apply additional scale on daily ret by exposure
    # ret_combined already alpha-cut; H1 further scales residual equity toward cash when exposure low
    r = d["ret_combined"].astype(float)
    exp = d["exposure_e45"].astype(float)
    base_nav = (1 + r).cumprod()
    # Extra cut: multiply day's equity return by exposure again (deeper cash)
    deep_r = r * exp
    deep_nav = (1 + deep_r).cumprod()
    # Mild hedge proxy H2: allocate 10% to -1x of core-like return approx using ret_combined when exp<0.85
    hedge = r.copy()
    crash = exp < 0.85
    hedge_r = r * 0.90 + np.where(crash, -0.10 * r, 0.0)  # naive antithetic on combined — illustrative only
    hedge_nav = (1 + pd.Series(hedge_r, index=r.index)).cumprod()
    report = {
        "status": "ROUND1_ILLUSTRATIVE",
        "baseline_alpha_cut_first": nav_stats(base_nav),
        "h1_deeper_cash_scale_by_exposure": nav_stats(deep_nav),
        "h2_synthetic_10pct_antithetic_in_crisis": nav_stats(hedge_nav),
        "warning": "H2 is a toy antithetic on combined returns, not a tradable short index. For research framing only.",
        "decision": "CONTINUE_H1_PREFERRED; H2 needs real instrument book in next round",
    }
    (out / "g4_hedge_round1.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def alpha_3a_menu(out: Path) -> dict:
    report = {
        "status": "MENU_ONLY_NO_MODEL",
        "forbidden": ["TECH2 remix", "PRICE8 remix", "S9A1 cut retune", "same-panel top_k grids"],
        "round1_pick": ["CA_dilution_aware_income", "causal_amihud_liquidity"],
        "protocol": "OOF→cost→stability→one-shot held-out→adversarial-lite→stop",
        "bar": "beat C4 or locked 80/20 util AND stress",
        "next_engineering": [
            "Build feature parquet with available_date<=T from A1 income + share_multiplier",
            "Amihud = |ret|/dollar_volume on PIT raw, shifted by label horizon",
            "Do not touch A3-R1 frozen repair model",
        ],
        "decision": "PROCEED_TO_FEATURE_BUILD_NEXT_ROUND",
    }
    (out / "alpha_3a_round1.json").write_text(json.dumps(report, indent=2) + "\n")
    Path("research/reopen/ALPHA_3A_ROUND1_MENU.md").write_text(
        "# Alpha 3A Round-1 Menu\n\n"
        + "\n".join(f"- {x}" for x in report["round1_pick"])
        + "\n\nForbidden: TECH2/PRICE8 remix, S9A1 retune.\n"
    )
    return report


def e16_e18_register(out: Path) -> dict:
    core = Path("repro/early-stack-combined-nav-20260904/outputs/e16_e18_e22_daily_nav.csv")
    base = nav_stats(load_nav_csv(core)) if core.exists() else {}
    report = {
        "baseline_book": "E16_E18_E22 early-stack",
        "baseline_stats": base,
        "pre_registered_variants_next": [
            {"id": "E16_V1", "change": "Crisis FIN floor 0.60→0.55 / TEL 0.35→0.40"},
            {"id": "E16_V2", "change": "gap trigger 0.015→0.020"},
            {"id": "E16_V3", "change": "trade fraction 0.75→0.60"},
            {"id": "E18_C1", "change": "cost_mult 1.0 / 1.5 / 2.0 stress only"},
        ],
        "decision": "VARIANTS_REGISTERED_NO_RUN_YET",
    }
    (out / "e16_e18_round1.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("repro/research-reopen-round1-20260904"))
    args = ap.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    Path("research/reopen").mkdir(parents=True, exist_ok=True)

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "authorization": "AUTHORIZE_RESEARCH_ALL_TRACKS_CHALLENGER_ONLY",
        "tracks": {
            "e22_v3": e22_v3_payment_vs_ex(out),
            "e45_rereview": e45_tradeoff(out),
            "g4_hedge": g4_cash_deleverage(out),
            "alpha_3a": alpha_3a_menu(out),
            "e16_e18": e16_e18_register(out),
        },
    }
    (out / "ROUND1_SUMMARY.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
    Path("research/reopen/ROUND1_SUMMARY.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")

    lines = [
        "# Research Reopen — Round 1 Summary",
        "",
        "Authorized challenger research started. No SOFT_FROZEN in-place edits. No promotions.",
        "",
        "| Track | Round-1 decision |",
        "|---|---|",
    ]
    for k, v in summary["tracks"].items():
        lines.append(f"| {k} | `{v.get('decision', v.get('status'))}` |")
    lines += [
        "",
        "Details: `repro/research-reopen-round1-20260904/`",
        "",
    ]
    md = "\n".join(lines)
    (out / "ROUND1_SUMMARY.md").write_text(md)
    Path("research/reopen/ROUND1_SUMMARY.md").write_text(md)
    print(json.dumps({k: v.get("decision", v.get("status")) for k, v in summary["tracks"].items()}, indent=2))


if __name__ == "__main__":
    main()
