#!/usr/bin/env python3
"""E45-C1: verified baseline + side-by-side vs V4.12-D (EXPERIMENTAL challenger).

Builds a reconstructed 12-stock raw panel from E50-A0 PIT (not the original
v412e0 artifact), runs:

  D          = FormalRouter signal weights, exposure=1 (preserved baseline role)
  E45_E3     = same weights × named-module E3_VOLTARGET_WINNER exposure
  E45_E1     = same weights × named-module E1_BINARY exposure
  E45_PASS   = passthrough control (=D)

Writes verified metrics (this panel) and a promotion recommendation A/B/C.
Does NOT promote SOFT_FROZEN_CRITICAL. Does NOT retune E3/E1 locks.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v412d_formal_router as d
import v412e11_graduated_crisis as e11
import e45_crisis_core as e45

STOCKS = [s for ids in d.GROUPS.values() for s in ids]
# Formal router default plateau winner used across E1/E11/E2–E3 baselines
FAM, REB, TOP_N, LOCK = 1, 21, 2, 75

WINDOWS = {
    "Train_2010_2018": ("2010-01-01", "2018-12-31"),
    "Validation_2019_2022": ("2019-01-01", "2022-12-31"),
    "Blind_2023_2025": ("2023-01-01", "2025-12-31"),
    "Final_2026": ("2026-01-01", "2099-12-31"),
    "Crisis_2008_2009": ("2008-01-01", "2009-12-31"),
    "Full": ("2005-01-01", "2099-12-31"),
}


def extract_raw_from_pit(pit_path: Path, out_csv: Path) -> dict:
    import polars as pl

    s = pl.scan_csv(pit_path, schema_overrides={"code": pl.String})
    df = (
        s.filter(pl.col("code").is_in(STOCKS))
        .select("date", "code", "open", "high", "low", "close", "volume")
        .collect(engine="streaming")
        .to_pandas()
    )
    df["date"] = pd.to_datetime(df["date"])
    df["code"] = df["code"].astype(str)
    df = df.dropna(subset=["open", "high", "low", "close"]).sort_values(["date", "code"])
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)
    coverage = df.groupby("code")["date"].agg(["min", "max", "count"]).to_dict("index")
    return {
        "path": str(out_csv),
        "n_rows": int(len(df)),
        "n_codes": int(df["code"].nunique()),
        "date_min": str(df["date"].min().date()),
        "date_max": str(df["date"].max().date()),
        "coverage": {k: {"min": str(v["min"].date()), "max": str(v["max"].date()), "n": int(v["count"])} for k, v in coverage.items()},
        "panel_note": "RECONSTRUCTED_FROM_E50A0_PIT_NOT_ORIGINAL_V412E0_ARTIFACT",
    }


def metrics(nav: pd.Series, start: str, end: str) -> dict:
    s = nav.loc[start:end].dropna()
    if len(s) < 2:
        return {"n": int(len(s)), "ret": None, "mdd": None, "sharpe": None, "vol": None}
    r = s.pct_change().dropna()
    return {
        "n": int(len(s)),
        "ret": float(s.iloc[-1] / s.iloc[0] - 1),
        "mdd": float((s / s.cummax() - 1).min()),
        "sharpe": float(r.mean() / r.std() * math.sqrt(252)) if r.std() > 0 else 0.0,
        "vol": float(r.std() * math.sqrt(252)),
    }


def block_bootstrap_mdd_better(
    chal_rets: np.ndarray,
    base_rets: np.ndarray,
    *,
    draws: int = 2000,
    block: int = 21,
    seed: int = 45001,
) -> float:
    """P(challenger |MDD| < baseline |MDD|) on paired block bootstrap paths."""
    n = min(len(chal_rets), len(base_rets))
    if n < block + 2:
        return float("nan")
    c, b = chal_rets[:n], base_rets[:n]
    rng = np.random.default_rng(seed)
    wins = 0
    n_blocks = int(math.ceil(n / block))
    max_start = max(n - block, 0)
    for _ in range(draws):
        starts = rng.integers(0, max_start + 1, size=n_blocks)
        def take(x):
            return np.concatenate([x[s:s + block] for s in starts])[:n]
        cr, br = take(c), take(b)
        cn = np.cumprod(1 + cr)
        bn = np.cumprod(1 + br)
        cm = float(np.min(cn / np.maximum.accumulate(cn) - 1))
        bm = float(np.min(bn / np.maximum.accumulate(bn) - 1))
        if abs(cm) + 1e-15 < abs(bm):
            wins += 1
    return wins / draws


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pit", type=Path, default=Path("/tmp/a0/point_in_time_universe.csv"))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--boot-draws", type=int, default=2000)
    args = ap.parse_args()
    out = args.out
    (out / "outputs").mkdir(parents=True, exist_ok=True)
    (out / "reports").mkdir(parents=True, exist_ok=True)
    Path("research/e45").mkdir(parents=True, exist_ok=True)

    print("extracting 12-stock raw panel from PIT ...", flush=True)
    raw_path = out / "outputs" / "e45c1_12stocks_raw_from_pit.csv"
    panel_meta = extract_raw_from_pit(args.pit, raw_path)
    print(json.dumps({k: panel_meta[k] for k in ("n_rows", "n_codes", "date_min", "date_max")}, indent=2), flush=True)

    raw = pd.read_csv(raw_path, dtype={"code": str})
    print("prep + FormalRouter scores/weights (D baseline locks) ...", flush=True)
    z = d.prep(raw)
    close = z.pivot(index="date", columns="stock_id", values="close").sort_index()
    op = z.pivot(index="date", columns="stock_id", values="open").reindex(close.index)
    scores = d.make_scores(z, FAM)
    signal_w, _state = d.targets(scores, list(close.index), REB, TOP_N, LOCK)

    # Eval on raw close/open (reconstructed panel; documented limitation)
    print("computing named E45 exposures ...", flush=True)
    exp_pass = pd.Series(1.0, index=close.index, name="exposure")
    exp_e3 = e45.compute_exposure(close, "E3_VOLTARGET_WINNER")["exposure"].reindex(close.index).ffill().fillna(1.0)
    exp_e1 = e45.compute_exposure(close, "E1_BINARY")["exposure"].reindex(close.index).ffill().fillna(1.0)

    profiles = {
        "D_FORMAL_ROUTER": exp_pass,
        "E45_PASSTHROUGH": exp_pass,
        "E45_E3_VOLTARGET_WINNER": exp_e3,
        "E45_E1_BINARY": exp_e1,
    }

    navs = {}
    costs = {}
    for name, exp in profiles.items():
        print(f"  nav {name} ...", flush=True)
        nav, w, cost, scaled = e11.nav_with_exposure(close, op, signal_w, exp)
        navs[name] = nav
        costs[name] = cost
        pd.DataFrame({"date": nav.index, "nav": nav.values, "cost": cost.values, "exposure": exp.reindex(nav.index).values}).to_csv(
            out / "outputs" / f"{name.lower()}_curve.csv", index=False
        )

    # Window metrics
    window_table = []
    for wname, (a, b) in WINDOWS.items():
        for name, nav in navs.items():
            m = metrics(nav, a, b)
            window_table.append({"window": wname, "strategy": name, **m})
    wt = pd.DataFrame(window_table)
    wt.to_csv(out / "outputs" / "e45c1_window_metrics.csv", index=False)

    # MC: P(better MDD) vs D on Validation and Full overlap returns
    mc = {}
    d_rets = navs["D_FORMAL_ROUTER"].pct_change().dropna().to_numpy()
    for name in ["E45_E3_VOLTARGET_WINNER", "E45_E1_BINARY"]:
        c_rets = navs[name].pct_change().dropna().to_numpy()
        mc[name] = {
            "p_better_mdd_full": block_bootstrap_mdd_better(c_rets, d_rets, draws=args.boot_draws),
        }
        # validation slice
        d_val = navs["D_FORMAL_ROUTER"].loc["2019-01-01":"2022-12-31"].pct_change().dropna().to_numpy()
        c_val = navs[name].loc["2019-01-01":"2022-12-31"].pct_change().dropna().to_numpy()
        mc[name]["p_better_mdd_validation"] = block_bootstrap_mdd_better(c_val, d_val, draws=args.boot_draws)
        print(f"  MC {name}: {mc[name]}", flush=True)

    def row(strategy: str, window: str) -> dict:
        r = wt[(wt.strategy == strategy) & (wt.window == window)]
        return r.iloc[0].to_dict() if len(r) else {}

    d_val = row("D_FORMAL_ROUTER", "Validation_2019_2022")
    e3_val = row("E45_E3_VOLTARGET_WINNER", "Validation_2019_2022")
    e1_val = row("E45_E1_BINARY", "Validation_2019_2022")
    d_full = row("D_FORMAL_ROUTER", "Full")
    e3_full = row("E45_E3_VOLTARGET_WINNER", "Full")
    d_crisis = row("D_FORMAL_ROUTER", "Crisis_2008_2009")
    e3_crisis = row("E45_E3_VOLTARGET_WINNER", "Crisis_2008_2009")

    # Higher-bar style checks vs D (documentation; not inventing new numeric freeze)
    def improves_mdd(chal, base) -> bool | None:
        if chal.get("mdd") is None or base.get("mdd") is None:
            return None
        return abs(chal["mdd"]) + 1e-15 < abs(base["mdd"])

    def keeps_ret_floor(chal, base, floor=0.80) -> bool | None:
        if chal.get("ret") is None or base.get("ret") is None or base["ret"] <= 0:
            return None
        return chal["ret"] >= floor * base["ret"]

    checks = {
        "e3_val_mdd_better": improves_mdd(e3_val, d_val),
        "e3_val_ret_ge_80pct_d": keeps_ret_floor(e3_val, d_val),
        "e3_val_sharpe_ge_d": (
            e3_val.get("sharpe") is not None and d_val.get("sharpe") is not None and e3_val["sharpe"] >= d_val["sharpe"]
        ),
        "e3_full_mdd_better": improves_mdd(e3_full, d_full),
        "e3_crisis_mdd_better": improves_mdd(e3_crisis, d_crisis) if e3_crisis.get("n", 0) > 10 else None,
        "e1_val_mdd_better": improves_mdd(e1_val, d_val),
        "mc_e3_p_better_mdd_val": mc["E45_E3_VOLTARGET_WINNER"]["p_better_mdd_validation"],
        "mc_e3_p_better_mdd_full": mc["E45_E3_VOLTARGET_WINNER"]["p_better_mdd_full"],
    }

    # Recommendation
    # A = promote E3 profile as E45_v1 candidate for governance approval
    # B = keep D as crisis baseline; E45 module stays API/documentation
    # C = reject / leave unpromoted without treating E3 as better
    e3_ok = (
        checks["e3_val_mdd_better"] is True
        and checks["e3_val_ret_ge_80pct_d"] is True
        and checks["mc_e3_p_better_mdd_val"] is not None
        and checks["mc_e3_p_better_mdd_val"] >= 0.55
    )
    e3_weak = checks["e3_val_mdd_better"] is True and checks["e3_val_ret_ge_80pct_d"] is False
    if e3_ok and checks.get("e3_val_sharpe_ge_d"):
        recommendation = "A_PROMOTE_E3_PROFILE_AS_E45_V1_CANDIDATE"
        rationale = (
            "On reconstructed PIT panel, E3 exposure improves Validation MDD vs D, "
            "keeps ≥80% of D return, and MC P(better MDD)≥0.55. Still requires explicit "
            "governance approval; panel is reconstructed (not original v412e0 artifact)."
        )
    elif e3_ok:
        recommendation = "A_PROMOTE_E3_PROFILE_AS_E45_V1_CANDIDATE_WEAK_SHARPE"
        rationale = (
            "MDD/return floor OK vs D on Validation; Sharpe not ≥ D. Eligible as cautious "
            "promotion candidate only after human review."
        )
    elif e3_weak or (checks["e3_val_mdd_better"] and checks["mc_e3_p_better_mdd_val"] and checks["mc_e3_p_better_mdd_val"] >= 0.55):
        recommendation = "B_KEEP_D_AS_BASELINE_E45_API_ONLY"
        rationale = (
            "E3 helps drawdown in places but fails return/Sharpe floor vs D on this panel. "
            "Keep V4.12-D as formal crisis baseline; named E45 remains API packaging."
        )
    else:
        recommendation = "C_REJECT_NO_PROMOTION"
        rationale = (
            "No E45 profile clears a higher-bar style improvement vs D on the reconstructed panel."
        )

    # Verified baseline artifact (this run) — replaces reliance on -13.16% text
    verified = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "panel": panel_meta,
        "signal_locks": {"family": FAM, "rebalance": REB, "top_n": TOP_N, "lock_days": LOCK},
        "eval_note": "Signals and evaluation both use raw OHLCV from PIT (no separate adjusted layer available in this environment).",
        "claimed_mdd_handoff": e45.CLAIMED_MDD,
        "claimed_mdd_status": e45.CLAIMED_MDD_STATUS,
        "verified_mdd_this_panel": {
            "D_FORMAL_ROUTER_validation": d_val.get("mdd"),
            "D_FORMAL_ROUTER_full": d_full.get("mdd"),
            "E45_E3_validation": e3_val.get("mdd"),
            "E45_E3_full": e3_full.get("mdd"),
            "E45_E1_validation": e1_val.get("mdd"),
        },
        "lineage_report_mdds_for_reference": e45.VERIFIED_LINEAGE_MDD,
        "recommendation": recommendation,
        "rationale": rationale,
        "checks": checks,
        "mc": mc,
        "promotion_allowed_by_module": False,
        "requires_explicit_governance_approval": True,
    }
    (out / "reports" / "e45_verified_baseline.json").write_text(json.dumps(verified, indent=2, default=str) + "\n")
    (Path("research/e45/e45_verified_baseline.json")).write_text(json.dumps(verified, indent=2, default=str) + "\n")

    # Update module status file without promoting
    status = e45.manifest_dict()
    status["e45_c1"] = {
        "recommendation": recommendation,
        "verified_baseline": "research/e45/e45_verified_baseline.json",
        "promoted": False,
    }
    Path("research/e45/e45_status.json").write_text(json.dumps(status, indent=2) + "\n")
    (out / "reports" / "e45_module_status_after_c1.json").write_text(json.dumps(status, indent=2) + "\n")

    decision_md = f"""# E45-C1 Decision Package

Date: {datetime.now(timezone.utc).date().isoformat()}  
Panel: reconstructed 12-stock raw OHLCV from E50-A0 PIT (**not** original v412e0 artifact)  
Signal: FormalRouter locks family={FAM}, reb={REB}, top_n={TOP_N}, lock={LOCK}

## Recommendation: `{recommendation}`

{rationale}

## Verified MDDs (this panel)

| Strategy | Validation MDD | Full MDD |
|---|---:|---:|
| D_FORMAL_ROUTER | {d_val.get('mdd')} | {d_full.get('mdd')} |
| E45_E3_VOLTARGET_WINNER | {e3_val.get('mdd')} | {e3_full.get('mdd')} |
| E45_E1_BINARY | {e1_val.get('mdd')} | {row('E45_E1_BINARY','Full').get('mdd')} |

Handoff claim MDD ≈ −13.16%: still **`{e45.CLAIMED_MDD_STATUS}`** (not found as matching artifact).

## Checks vs D

```json
{json.dumps(checks, indent=2)}
```

## Monte Carlo P(better MDD vs D)

```json
{json.dumps(mc, indent=2)}
```

## Options

- **A** — Promote E3 profile as `E45_v1` after explicit approval; retire −13.16% text; publish verified MDD from this (or original) panel.
- **B** — Keep **V4.12-D** as crisis baseline; named `e45_crisis_core.py` stays API / packaging only.
- **C** — Reject promotion; leave `CHALLENGER_CANDIDATE_NOT_PROMOTED`.

## Explicit non-actions

- No in-place SOFT_FROZEN_CRITICAL edit
- No retune of E3 winner parameters
- No claim that reconstructed PIT panel equals the original E3 research panel

Artifacts: `reports/e45_verified_baseline.json`, `outputs/e45c1_window_metrics.csv`
"""
    (out / "E45_C1_DECISION.md").write_text(decision_md)
    Path("research/e45/E45_C1_DECISION.md").write_text(decision_md)

    print(json.dumps({"recommendation": recommendation, "checks": checks, "mc": mc}, indent=2, default=str))


if __name__ == "__main__":
    main()
