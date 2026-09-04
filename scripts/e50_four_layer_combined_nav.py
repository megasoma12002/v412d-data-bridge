#!/usr/bin/env python3
"""Four-layer combined NAV challenger (EXPERIMENTAL).

Wires the frozen *roles* into one capital book without editing SOFT_FROZEN files:

  E16+E18(+E22) core sleeve
+ optional named E45 exposure (already baked into core NAV variants)
+ E50-A alpha sleeve (A3-R1 research NAV, separate capital)
+ operating rule: cut Alpha before Core in stress

Uses precomputed NAV series (core sandbox + A3-R1 audit outputs).
Does NOT retune E16/E18/E22/E45/A3 parameters. Does NOT promote anything.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e45_crisis_core as e45


def load_nav(path: Path, value_col: str = "nav") -> pd.Series:
    d = pd.read_csv(path)
    d["date"] = pd.to_datetime(d["date"])
    s = d.set_index("date")[value_col].astype(float).sort_index()
    # drop duplicate dates if any (A3R1 has val then sealed)
    s = s[~s.index.duplicated(keep="last")]
    return s


def to_returns(nav: pd.Series) -> pd.Series:
    return nav.pct_change().fillna(0.0)


def stats_from_nav(nav: pd.Series) -> dict:
    if len(nav) < 2:
        return {"cagr": None, "max_drawdown": None, "utility": None, "vol": None, "n_days": len(nav)}
    r = nav.pct_change().dropna().to_numpy()
    path = nav.to_numpy()
    years = len(r) / 252.0
    cagr = float((path[-1] / path[0]) ** (1.0 / years) - 1.0) if years > 0 and path[0] > 0 else None
    peak = np.maximum.accumulate(path)
    mdd = float(np.min(path / peak - 1.0))
    vol = float(np.std(r, ddof=1) * np.sqrt(252)) if len(r) > 2 else None
    return {
        "cagr": cagr,
        "max_drawdown": mdd,
        "utility": (cagr or 0.0) - 0.5 * abs(mdd),
        "vol": vol,
        "n_days": int(len(nav)),
        "start": str(nav.index[0].date()),
        "end": str(nav.index[-1].date()),
    }


def combine_sleeves(
    core_ret: pd.Series,
    alpha_ret: pd.Series,
    *,
    core_weight: float,
    alpha_weight: float,
    e45_exposure: pd.Series | None,
    alpha_cut_first: bool,
    alpha_stress_mult: float = 0.0,
) -> pd.DataFrame:
    """Daily combined returns with optional alpha-first stress cut using E45 exposure."""
    idx = core_ret.index.intersection(alpha_ret.index)
    if e45_exposure is not None:
        idx = idx.intersection(e45_exposure.index)
    idx = idx.sort_values()
    cr = core_ret.loc[idx]
    ar = alpha_ret.loc[idx]
    rows = []
    cw0, aw0 = float(core_weight), float(alpha_weight)
    s = cw0 + aw0
    cw0, aw0 = cw0 / s, aw0 / s
    for dt in idx:
        cw, aw = cw0, aw0
        exp = 1.0
        if e45_exposure is not None:
            exp = float(e45_exposure.loc[dt])
        if alpha_cut_first and exp < 0.999:
            # Spec: Alpha weakening / crisis → cut alpha before core.
            # Scale alpha sleeve by exposure^k (default k→ cash alpha when exp low via stress_mult floor).
            aw = aw0 * max(exp, alpha_stress_mult)
            # residual capital stays in cash (0 return) — not forced into core
            cash_w = cw0 + aw0 - cw - aw
        else:
            cash_w = 0.0
            # optional: also scale core if exposure baked-in already in core NAV — do not double-apply
        r = cw * float(cr.loc[dt]) + aw * float(ar.loc[dt]) + cash_w * 0.0
        rows.append(
            {
                "date": dt,
                "ret": r,
                "core_w": cw,
                "alpha_w": aw,
                "cash_w": cash_w,
                "e45_exposure": exp,
            }
        )
    out = pd.DataFrame(rows).set_index("date")
    out["nav"] = (1.0 + out["ret"]).cumprod()
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--core-nav",
        type=Path,
        default=Path("repro/early-stack-combined-nav-20260904/outputs/e16_e18_e22_daily_nav.csv"),
    )
    ap.add_argument(
        "--core-nav-e45",
        type=Path,
        default=Path("repro/early-stack-combined-nav-20260904/outputs/e16_e18_e22_e45_e3_daily_nav.csv"),
        help="Core NAV that already embeds named E45-E3 (for core-only compare)",
    )
    ap.add_argument(
        "--alpha-nav",
        type=Path,
        default=Path("repro/e50a3r1-audit-20260903/outputs/a3r1/daily_nav.csv"),
    )
    ap.add_argument("--market", type=Path, default=Path("forward/e21/live_market.csv"))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--core-weight", type=float, default=0.80)
    ap.add_argument("--alpha-weight", type=float, default=0.20)
    args = ap.parse_args()
    out = args.out
    (out / "outputs").mkdir(parents=True, exist_ok=True)
    (out / "reports").mkdir(parents=True, exist_ok=True)

    core = load_nav(args.core_nav)
    core_e45 = load_nav(args.core_nav_e45)
    alpha = load_nav(args.alpha_nav)
    core_ret, alpha_ret = to_returns(core), to_returns(alpha)
    core_e45_ret = to_returns(core_e45)

    # E45 exposure series from named module on core equities (for alpha-cut-first rule)
    m = pd.read_csv(args.market, dtype={"code": str})
    m["date"] = pd.to_datetime(m["date"])
    codes = ["2880", "2886", "2892", "5880", "2412", "3045", "4904", "0050"]
    close_eq = m[m["code"].isin(codes)].pivot(index="date", columns="code", values="close").sort_index().ffill()
    e45_exp = e45.compute_exposure(close_eq, "E3_VOLTARGET_WINNER")["exposure"]

    books = {}
    # 1) Core only / Alpha only on overlap
    overlap = core_ret.index.intersection(alpha_ret.index).sort_values()
    books["CORE_ONLY"] = pd.DataFrame({"nav": (1 + core_ret.loc[overlap]).cumprod()}, index=overlap)
    books["CORE_E45_ONLY"] = pd.DataFrame({"nav": (1 + core_e45_ret.loc[overlap]).cumprod()}, index=overlap)
    books["ALPHA_ONLY"] = pd.DataFrame({"nav": (1 + alpha_ret.loc[overlap]).cumprod()}, index=overlap)

    # 2) Static mix (no alpha-cut-first) — alpha on top of plain core
    static = combine_sleeves(
        core_ret, alpha_ret,
        core_weight=args.core_weight, alpha_weight=args.alpha_weight,
        e45_exposure=None, alpha_cut_first=False,
    )
    books["MIX_STATIC_80_20"] = static

    # 3) Alpha-cut-first using named E45 exposure; core remains plain E16+E18+E22
    #    (E45 applied as *operating overlay on alpha*, not double-applied to core)
    cut = combine_sleeves(
        core_ret, alpha_ret,
        core_weight=args.core_weight, alpha_weight=args.alpha_weight,
        e45_exposure=e45_exp, alpha_cut_first=True, alpha_stress_mult=0.0,
    )
    books["MIX_ALPHA_CUT_FIRST"] = cut

    # 4) Full stack narrative: core already has E45-E3, plus alpha-cut-first
    full = combine_sleeves(
        core_e45_ret, alpha_ret,
        core_weight=args.core_weight, alpha_weight=args.alpha_weight,
        e45_exposure=e45_exp, alpha_cut_first=True, alpha_stress_mult=0.0,
    )
    books["FULL_CORE_E45_PLUS_ALPHA_CUT"] = full

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "FOUR_LAYER_COMBINED_NAV_CHALLENGER",
        "governance": {
            "modifies_soft_frozen_files": False,
            "e45_promoted": False,
            "alpha_promoted": False,
            "label": "EXPERIMENTAL_CHALLENGER_SANDBOX",
            "architecture": "E16+E18+E22 core | named E45 candidate | E50-A alpha sleeve | alpha-cut-first",
        },
        "inputs": {
            "core_nav": str(args.core_nav),
            "core_nav_e45": str(args.core_nav_e45),
            "alpha_nav": str(args.alpha_nav),
            "core_weight": args.core_weight,
            "alpha_weight": args.alpha_weight,
            "overlap_start": str(overlap[0].date()),
            "overlap_end": str(overlap[-1].date()),
            "n_overlap_days": int(len(overlap)),
        },
        "e45_module": {
            "path": "scripts/e45_crisis_core.py",
            "status": e45.MODULE_STATUS,
            "profile": "E3_VOLTARGET_WINNER",
        },
        "books": {},
        "decisions": {},
    }

    for name, df in books.items():
        nav = df["nav"] if "nav" in df.columns else df.iloc[:, 0]
        st = stats_from_nav(nav)
        summary["books"][name] = st
        out_df = df.reset_index().rename(columns={"index": "date"})
        if "date" not in out_df.columns:
            out_df = df.copy()
            out_df.insert(0, "date", df.index)
            out_df = out_df.reset_index(drop=True)
        else:
            out_df["date"] = pd.to_datetime(out_df["date"]).dt.strftime("%Y-%m-%d")
        out_df.to_csv(out / "outputs" / f"{name.lower()}_daily.csv", index=False)
        print(
            f"{name}: CAGR={st['cagr']:.4f} MDD={st['max_drawdown']:.4f} util={st['utility']:.4f}",
            flush=True,
        )

    # Decision heuristics (documentation only — no promotion)
    full_st = summary["books"]["FULL_CORE_E45_PLUS_ALPHA_CUT"]
    core_st = summary["books"]["CORE_ONLY"]
    alpha_st = summary["books"]["ALPHA_ONLY"]
    static_st = summary["books"]["MIX_STATIC_80_20"]
    cut_st = summary["books"]["MIX_ALPHA_CUT_FIRST"]
    summary["decisions"] = {
        "four_layer_engine": "IMPLEMENTED_IN_CHALLENGER_SANDBOX",
        "alpha_is_separate_sleeve": True,
        "alpha_cut_before_core": True,
        "e45_promoted": False,
        "alpha_promoted": False,
        "note": (
            "Combined book exists for the overlap window where A3-R1 alpha NAV is available "
            f"({summary['inputs']['overlap_start']} → {summary['inputs']['overlap_end']}). "
            "Core-only history remains longer (from early-stack sandbox). "
            "Do not treat this as a frozen four-layer production engine."
        ),
        "compare": {
            "full_minus_core_util": (full_st["utility"] or 0) - (core_st["utility"] or 0),
            "cut_minus_static_util": (cut_st["utility"] or 0) - (static_st["utility"] or 0),
            "cut_minus_static_mdd": (cut_st["max_drawdown"] or 0) - (static_st["max_drawdown"] or 0),
            "alpha_only_util": alpha_st["utility"],
        },
    }

    (out / "reports" / "four_layer_combined_nav_summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n"
    )

    lines = [
        "# Four-Layer Combined NAV Challenger",
        "",
        "**EXPERIMENTAL.** Roles → one capital book. No SOFT_FROZEN edits. No promotion.",
        "",
        "```",
        "E16 + E18 + E22   core sleeve",
        "E45 (named cand.) optional on core / alpha-cut signal",
        "E50-A (A3-R1)     alpha sleeve (separate capital)",
        "Rule              cut Alpha before Core when E45 exposure < 1",
        "```",
        "",
        f"Overlap window: `{summary['inputs']['overlap_start']}` → `{summary['inputs']['overlap_end']}` "
        f"({summary['inputs']['n_overlap_days']} days). Split `{args.core_weight:.0%}` core / `{args.alpha_weight:.0%}` alpha.",
        "",
        "| Book | CAGR | MDD | Util | Vol |",
        "|---|---:|---:|---:|---:|",
    ]
    for name in books:
        s = summary["books"][name]
        lines.append(
            f"| {name} | {100*(s['cagr'] or 0):.2f}% | {100*(s['max_drawdown'] or 0):.2f}% | "
            f"{s['utility']:.4f} | {100*(s['vol'] or 0):.2f}% |"
        )
    lines += [
        "",
        "## Decisions",
        "",
    ]
    for k, v in summary["decisions"].items():
        if k == "compare":
            lines.append(f"- `compare`: `{json.dumps(v)}`")
        else:
            lines.append(f"- `{k}`: {v}")
    lines += [
        "",
        "## Explicit non-actions",
        "",
        "- Does not promote E45 or A3-R1",
        "- Does not overwrite `forward/e21/`",
        "- Does not retune sleeve weights as a new frozen router",
        "",
        "Artifact: `reports/four_layer_combined_nav_summary.json`",
        "",
    ]
    (out / "FOUR_LAYER_COMBINED_NAV.md").write_text("\n".join(lines))
    print(json.dumps(summary["decisions"], indent=2, default=str))


if __name__ == "__main__":
    main()
