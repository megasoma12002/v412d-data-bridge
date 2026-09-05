#!/usr/bin/env python3
"""E16 FIN_CAP weight-budget OOF challenger (RESEARCH_ONLY).

Predeclared before looking at held-out:
  - Baseline: E16 clips Financial∈[0.50,0.95] + E22_v2s books
  - FIN_CAP_60: Financial∈[0.40,0.60]; residual to Telecom/0050 (same relative mix)
  - FIN_CAP_50: Financial∈[0.35,0.50]
  - Selection window: OOF 2011-01-01 .. 2018-12-31 ONLY
  - Held-out 2019+ reported informationally; does NOT choose the winner

Pass (OOF): finance mean weight ≤ cap_hi + 1e-6
        AND max_drawdown strictly better than baseline by ≥1.0 pp
        AND CAGR not worse than baseline by >2.0 pp
If none pass → STOP_FIN_CAP_OOF (keep live E16).
No live-wire. No Soft-Frozen edit.
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
from research_metric_helpers import abs_mdd, cagr_value
import e22_dividend_accounting as e22div
from e16_soft_frozen_base import SOFT_FROZEN_FIN_HI, SOFT_FROZEN_FIN_LO

OUT = Path("repro/gap-cagr-finance-concentration/fin_cap_oof")
OOF_START, OOF_END = date(2011, 1, 1), date(2018, 12, 31)
HOLD_START = date(2019, 1, 1)

# Predeclared challengers (do not edit after first OOF peek).
# BASE clip bounds come from Soft-Frozen single source — challenger caps stay named.
CHALLENGERS = {
    "BASE_E16": {
        "fin_lo": float(SOFT_FROZEN_FIN_LO),
        "fin_hi": float(SOFT_FROZEN_FIN_HI),
        "is_baseline": True,
    },
    "FIN_CAP_60": {"fin_lo": 0.40, "fin_hi": 0.60, "is_baseline": False},
    "FIN_CAP_50": {"fin_lo": 0.35, "fin_hi": 0.50, "is_baseline": False},
}
MDD_IMPROVE_MIN = 0.01  # 1 pp less deep
CAGR_GIVEBACK_MAX = 0.02  # 2 pp


def e16_features_fin_cap(market: pd.DataFrame, fin_lo: float, fin_hi: float):
    """Same causal E16 router as live, with Financial hard clip replaced by [fin_lo, fin_hi].

    Priors unchanged; only the post-prior Financial clip changes. After clip, residual
    mass is renormalized onto Telecom/0050 so weights still sum to 1.
    """
    from e50_early_stack_combined_nav import FIN, TEL

    p = market.pivot(index="date", columns="code", values="adj_close").sort_index().ffill()
    r = p.pct_change(fill_method=None).fillna(0)
    sleeve = pd.DataFrame(
        {"Financial": r[FIN].mean(1), "Telecom": r[TEL].mean(1), "0050": r["0050"]}
    )
    tc = p["TAIEX"]
    tr = tc.pct_change()
    ma = tc.rolling(200).mean()
    vol = tr.rolling(20).std() * np.sqrt(252)
    dd = tc / tc.rolling(252, min_periods=120).max() - 1
    reg = pd.Series("Sideways", index=p.index)
    reg[(tc > ma) & (vol < 0.25)] = "Bull"
    reg[tc < ma] = "Bear"
    reg[(vol > 0.35) | (dd < -0.15)] = "Crisis"
    nav = (1 + sleeve).cumprod()
    m20 = nav / nav.shift(20) - 1
    m60 = nav / nav.shift(60) - 1
    sv = sleeve.rolling(20).std() * np.sqrt(252)
    d60 = nav / nav.rolling(60, min_periods=20).max() - 1

    def z(x):
        return x.sub(x.mean(1), axis=0).div(x.std(1).replace(0, np.nan), axis=0).fillna(0)

    score = 0.35 * z(m20) + 0.35 * z(m60) - 0.20 * z(sv) + 0.10 * z(d60)
    out = []
    # Start inside the new band (live starts at 0.9 which would violate FIN_CAP_60/50).
    start_fin = float(np.clip(0.90, fin_lo, fin_hi))
    rem = 1.0 - start_fin
    cur = np.array([start_fin, rem * 0.7, rem * 0.3])
    for i, _dt in enumerate(p.index):
        rg = reg.iloc[i]
        pri = {
            "Bull": np.array([0.85, 0.05, 0.10]),
            "Crisis": np.array([0.60, 0.35, 0.05]),
            "Bear": np.array([0.70, 0.25, 0.05]),
            "Sideways": np.array([0.85, 0.10, 0.05]),
        }[rg]
        cand = np.maximum(pri + 0.10 * np.clip(score.iloc[i].to_numpy(), -2, 2), 0)
        cand[0] = np.clip(cand[0], fin_lo, fin_hi)
        cand[1] = np.clip(cand[1], 0.03, 0.35)
        cand[2] = np.clip(cand[2], 0, 0.35)
        others = cand[1] + cand[2]
        if others <= 1e-12:
            cand[1], cand[2] = 0.5 * (1 - cand[0]), 0.5 * (1 - cand[0])
        else:
            scale = (1.0 - cand[0]) / others
            cand[1] *= scale
            cand[2] *= scale
        cand = np.maximum(cand, 0)
        cand /= cand.sum()
        desired = 0.75 * cur + 0.25 * cand
        desired[0] = float(np.clip(desired[0], fin_lo, fin_hi))
        oth = desired[1] + desired[2]
        if oth <= 1e-12:
            desired[1], desired[2] = 0.5 * (1 - desired[0]), 0.5 * (1 - desired[0])
        else:
            scale = (1.0 - desired[0]) / oth
            desired[1] *= scale
            desired[2] *= scale
        desired = np.maximum(desired, 0)
        desired /= desired.sum()
        if np.abs(desired - cur).sum() >= 0.02:
            cur = desired
        out.append(cur.copy())
    target = pd.DataFrame(out, index=p.index, columns=["Financial", "Telecom", "0050"])
    return p, sleeve, target, reg


def window_stats(nav: pd.DataFrame, start: date, end: date | None = None) -> dict:
    d = nav.copy()
    d["date"] = pd.to_datetime(d["date"]).dt.date
    if end is None:
        g = d[d["date"] >= start]
    else:
        g = d[(d["date"] >= start) & (d["date"] <= end)]
    if len(g) < 30:
        return {"cagr": None, "max_drawdown": None, "utility": None, "vol": None, "n_days": int(len(g))}
    return nav_stats(g.reset_index(drop=True))


def target_weight_stats(target: pd.DataFrame, start: date, end: date) -> dict:
    idx = pd.to_datetime(target.index).date
    m = (idx >= start) & (idx <= end)
    t = target.loc[m]
    fin = t["Financial"]
    return {
        "mean_financial": float(fin.mean()),
        "median_financial": float(fin.median()),
        "max_financial": float(fin.max()),
        "min_financial": float(fin.min()),
        "pct_ge_070": float((fin >= 0.70).mean()),
        "mean_telecom": float(t["Telecom"].mean()),
        "mean_0050": float(t["0050"].mean()),
        "n_days": int(len(t)),
    }


def main() -> None:
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(parents=True, exist_ok=True)

    market = pd.read_csv("forward/e21/live_market.csv", dtype={"code": str})
    market["date"] = pd.to_datetime(market["date"])
    required = set(ALL + ["TAIEX"])
    complete = market.groupby("date")["code"].apply(lambda s: required.issubset(set(s)))
    market = market[market["date"].isin(complete[complete].index)].sort_values(["date", "code"])
    dividends = pd.read_csv("data/dividend_events/e22_dividend_events.csv", dtype={"code": str})

    rows = []
    navs = {}
    targets = {}
    for name, cfg in CHALLENGERS.items():
        print(f"building targets {name} fin=[{cfg['fin_lo']},{cfg['fin_hi']}] ...", flush=True)
        if cfg["is_baseline"]:
            _p, _s, target, regime = e16_features(market)
        else:
            _p, _s, target, regime = e16_features_fin_cap(market, cfg["fin_lo"], cfg["fin_hi"])
        targets[name] = target
        print(f"simulating {name} under E22_v2s ...", flush=True)
        nav, fills, meta = simulate_core(
            market,
            target,
            regime,
            dividends,
            apply_e22=True,
            apply_stock_div=True,
            e22_version=e22div.E22_V2S,
        )
        nav.to_csv(OUT / "outputs" / f"{name.lower()}_daily_nav.csv", index=False)
        fills.to_csv(OUT / "outputs" / f"{name.lower()}_fills.csv", index=False)
        target.to_csv(OUT / "outputs" / f"{name.lower()}_targets.csv")
        navs[name] = nav

        full = nav_stats(nav)
        oof = window_stats(nav, OOF_START, OOF_END)
        held = window_stats(nav, HOLD_START, None)
        w_oof = target_weight_stats(target, OOF_START, OOF_END)
        w_full = target_weight_stats(
            target,
            date(pd.to_datetime(target.index.min()).year, 1, 1)
            if False
            else pd.to_datetime(target.index.min()).date(),
            pd.to_datetime(target.index.max()).date(),
        )
        row = {
            "name": name,
            "is_baseline": cfg["is_baseline"],
            "fin_lo": cfg["fin_lo"],
            "fin_hi": cfg["fin_hi"],
            "full": full,
            "oof_2011_2018": oof,
            "heldout_2019_plus": held,
            "weights_oof": w_oof,
            "weights_full": w_full,
            "meta": {
                "n_fills": meta.get("n_fills"),
                "stock_div_events": meta.get("stock_div_events"),
            },
        }
        rows.append(row)
        print(
            f"  {name} OOF CAGR={oof['cagr']:.4%} MDD={oof['max_drawdown']:.4%} "
            f"fin_mean={w_oof['mean_financial']:.3f}",
            flush=True,
        )

    base = next(r for r in rows if r["is_baseline"])
    b_oof = base["oof_2011_2018"]
    candidates = []
    for r in rows:
        if r["is_baseline"]:
            continue
        o = r["oof_2011_2018"]
        w = r["weights_oof"]
        cap_ok = w["mean_financial"] <= r["fin_hi"] + 1e-6 and w["max_financial"] <= r["fin_hi"] + 1e-6
        mdd_improve = abs_mdd(b_oof["max_drawdown"]) - abs_mdd(o["max_drawdown"])
        cagr_giveback = (cagr_value(b_oof["cagr"]) or 0.0) - (cagr_value(o["cagr"]) or 0.0)
        pass_oof = bool(
            cap_ok
            and o["max_drawdown"] is not None
            and mdd_improve >= MDD_IMPROVE_MIN
            and cagr_giveback <= CAGR_GIVEBACK_MAX
        )
        entry = {
            **{k: r[k] for k in ("name", "fin_lo", "fin_hi")},
            "cap_ok": cap_ok,
            "mdd_improve_pp": mdd_improve * 100,
            "cagr_giveback_pp": cagr_giveback * 100,
            "oof_cagr": o["cagr"],
            "oof_mdd": o["max_drawdown"],
            "oof_util": o["utility"],
            "base_oof_cagr": b_oof["cagr"],
            "base_oof_mdd": b_oof["max_drawdown"],
            "mean_financial_oof": w["mean_financial"],
            "pass_oof": pass_oof,
            "heldout_cagr": r["heldout_2019_plus"]["cagr"],
            "heldout_mdd": r["heldout_2019_plus"]["max_drawdown"],
            "heldout_used_for_selection": False,
        }
        candidates.append(entry)

    winners = [c for c in candidates if c["pass_oof"]]
    winners = sorted(winners, key=lambda c: (-c["mdd_improve_pp"], -c["oof_util"] if c["oof_util"] is not None else -9))
    recommended = winners[0] if winners else None
    decision = (
        "OOF_FIN_CAP_PASS_READY_FOR_HELDOUT"
        if recommended
        else "STOP_FIN_CAP_OOF"
    )

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "RESEARCH_ONLY",
        "live_wire": False,
        "soft_frozen_edit": False,
        "selection_window": "2011-2018 OOF only",
        "heldout_policy": "report_only_no_selection",
        "books": "E22_v2s",
        "predeclared_pass_rule": {
            "finance_mean_and_max_le_cap_hi": True,
            "mdd_improve_min_pp": MDD_IMPROVE_MIN * 100,
            "cagr_giveback_max_pp": CAGR_GIVEBACK_MAX * 100,
        },
        "baseline": {
            "name": base["name"],
            "oof": base["oof_2011_2018"],
            "heldout": base["heldout_2019_plus"],
            "weights_oof": base["weights_oof"],
        },
        "challengers": candidates,
        "n_oof_pass": len(winners),
        "recommended": recommended,
        "research_decision": decision,
        "next_if_pass": "one held-out evaluation; only PASS_HELDOUT may propose live prior change",
        "next_if_stop": "keep live E16 clips; pursue orthogonal alpha / loss engine instead of FIN_CAP retune",
        "rows": rows,
    }
    (OUT / "reports" / "fin_cap_oof_summary.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")

    # Flat CSV for challengers
    pd.DataFrame(candidates).to_csv(OUT / "outputs" / "fin_cap_oof_candidates.csv", index=False)

    research = Path("research/gaps")
    research.mkdir(parents=True, exist_ok=True)
    (research / "FIN_CAP_OOF_SUMMARY.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")

    lines = [
        "# E16 FIN_CAP Weight-Budget OOF Challenger",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        "",
        "**RESEARCH_ONLY.** No live-wire. Selection = 2011–2018 OOF only.",
        "",
        f"## Decision: `{decision}`",
        "",
        "### Predeclared pass rule",
        "",
        f"- Finance mean & max weight ≤ cap_hi",
        f"- OOF MDD improve ≥ **{MDD_IMPROVE_MIN*100:.0f} pp** vs BASE_E16",
        f"- OOF CAGR giveback ≤ **{CAGR_GIVEBACK_MAX*100:.0f} pp**",
        "",
        "### Baseline (OOF)",
        "",
        f"- CAGR `{b_oof['cagr']}` MDD `{b_oof['max_drawdown']}` util `{b_oof['utility']}`",
        f"- Mean Financial weight `{base['weights_oof']['mean_financial']:.3f}`",
        "",
        "| name | fin_hi | fin_mean | OOF CAGR | OOF MDD | MDDΔ pp | CAGR giveback pp | pass |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for c in candidates:
        lines.append(
            f"| {c['name']} | {c['fin_hi']} | {c['mean_financial_oof']:.3f} | "
            f"{c['oof_cagr']} | {c['oof_mdd']} | {c['mdd_improve_pp']:.2f} | "
            f"{c['cagr_giveback_pp']:.2f} | {c['pass_oof']} |"
        )
    if recommended:
        lines += [
            "",
            "## Recommended (OOF only)",
            "",
            f"- `{recommended['name']}` fin_hi={recommended['fin_hi']}",
            f"- MDD improve `{recommended['mdd_improve_pp']:.2f}` pp; CAGR giveback `{recommended['cagr_giveback_pp']:.2f}` pp",
            "",
            "Held-out numbers below are **informational only** (not used to pick).",
            "",
            f"- Held-out CAGR `{recommended['heldout_cagr']}` MDD `{recommended['heldout_mdd']}`",
            "",
            "Next: one held-out gate. Only `PASS_HELDOUT` may propose changing live E16 clips.",
            "",
        ]
    else:
        lines += [
            "",
            "`STOP_FIN_CAP_OOF`: no challenger cleared the predeclared OOF bar.",
            "**Keep live E16.** Do not retune finance priors on held-out.",
            "Return to dual-track B / separate loss-engine research for the MDD target.",
            "",
        ]
    # Informational held-out table
    lines += [
        "### Informational held-out (2019+)",
        "",
        "| name | held CAGR | held MDD |",
        "|---|---:|---:|",
        f"| BASE_E16 | {base['heldout_2019_plus']['cagr']} | {base['heldout_2019_plus']['max_drawdown']} |",
    ]
    for c in candidates:
        lines.append(f"| {c['name']} | {c['heldout_cagr']} | {c['heldout_mdd']} |")
    lines += [
        "",
        "Artifacts:",
        f"- `{OUT / 'reports' / 'fin_cap_oof_summary.json'}`",
        f"- `{OUT / 'outputs' / 'fin_cap_oof_candidates.csv'}`",
        "",
        "Label: `RESEARCH_FIN_CAP_OOF__NO_LIVE_WIRE`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "FIN_CAP_OOF.md").write_text(md)
    (research / "FIN_CAP_OOF.md").write_text(md)
    print(json.dumps({"research_decision": decision, "n_pass": len(winners), "recommended": recommended}, indent=2, default=str))


if __name__ == "__main__":
    main()
