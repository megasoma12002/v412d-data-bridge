#!/usr/bin/env python3
"""E45 paper cost/stress/recovery seal F8–F10 (no retune; no live edits).

Requires freshly regenerated early-stack dir with INPUT/OUTPUT manifests.
Loads F1–F7 from reports/f1_f7_gates.json (re-run gates if missing/stale).
Writes SEAL_LOCK.json + study; gates script must not overwrite these.
"""
from __future__ import annotations

import argparse
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from e45_feasibility_common import (  # noqa: E402
    claim_dict,
    dumps_json,
    load_json,
    mdd,
    official_status_dict,
    refuse_superseded_pack,
    verify_output_manifest,
)

DEFAULT_IN = ROOT / "repro/e45-feasibility-study-regen-20260905"
CHARTER = ROOT / "research/e45/E45_FEASIBILITY_CHARTER.md"
STUDY_MD = ROOT / "research/e45/E45_FEASIBILITY_STUDY_2026-09-05.md"
STUDY_JSON = ROOT / "research/e45/E45_FEASIBILITY_STUDY_2026-09-05.json"

STRESS_WINDOWS = {
    "2015_china_shock": ("2015-06-01", "2015-09-30"),
    "2018_trade_war": ("2018-09-01", "2019-01-31"),
    "2020_covid": ("2020-02-01", "2020-04-30"),
    "2022_bear": ("2022-01-01", "2022-10-31"),
}


def resolve_paths(in_dir: Path) -> dict[str, Path]:
    in_dir = in_dir.resolve()
    refuse_superseded_pack(in_dir)
    verify_output_manifest(in_dir)  # fail-closed hash check
    return {
        "IN": in_dir,
        "OUT": in_dir / "reports",
        "BASE_NAV": in_dir / "outputs" / "e16_e18_e22_daily_nav.csv",
        "CHAL_NAV": in_dir / "outputs" / "e16_e18_e22_e45_e3_daily_nav.csv",
        "BASE_FILLS": in_dir / "outputs" / "e16_e18_e22_fills.csv",
        "CHAL_FILLS": in_dir / "outputs" / "e16_e18_e22_e45_e3_fills.csv",
        "INPUT_MANIFEST": in_dir / "INPUT_MANIFEST.json",
        "OUTPUT_MANIFEST": in_dir / "OUTPUT_MANIFEST.json",
        "F1F7": in_dir / "reports" / "f1_f7_gates.json",
        "SEAL_LOCK": in_dir / "SEAL_LOCK.json",
    }


def total_return(nav: pd.Series) -> float:
    if len(nav) < 2:
        return float("nan")
    return float(nav.iloc[-1] / nav.iloc[0] - 1.0)


def recovery_stats(nav: pd.Series, dates: pd.Series) -> dict:
    x = nav.astype(float).reset_index(drop=True)
    d = pd.to_datetime(dates).reset_index(drop=True)
    peak = x.cummax()
    dd = x / peak - 1.0
    trough_i = int(dd.idxmin())
    after = x.iloc[trough_i:]
    recovered = after[after >= float(peak.iloc[trough_i])]
    days_to_recover = None
    if len(recovered):
        rec_i = int(recovered.index[0])
        days_to_recover = int((d.iloc[rec_i] - d.iloc[trough_i]).days)
    underwater = dd < -1e-12
    longest = cur = 0
    for flag in underwater:
        if flag:
            cur += 1
            longest = max(longest, cur)
        else:
            cur = 0
    return {
        "trough_date": str(d.iloc[trough_i].date()),
        "trough_mdd": float(dd.iloc[trough_i]),
        "days_to_recover": days_to_recover,
        "longest_underwater_days": int(longest),
    }


def fee_turnover(fills: pd.DataFrame, nav: pd.DataFrame) -> dict:
    fee_col = "fees_tax" if "fees_tax" in fills.columns else "fee_tax"
    gross_col = "gross" if "gross" in fills.columns else "notional"
    fees = float(fills[fee_col].sum())
    notional = float(fills[gross_col].abs().sum())
    years = (
        pd.to_datetime(nav["date"].iloc[-1]) - pd.to_datetime(nav["date"].iloc[0])
    ).days / 365.25
    avg_nav = float(nav["nav"].mean())
    return {
        "n_fills": int(len(fills)),
        "fee_sum": fees,
        "gross_notional": notional,
        "annualized_turnover_approx": (notional / avg_nav / years) if years > 0 else float("nan"),
        "fee_bps_per_year_vs_avg_nav": (fees / avg_nav / years * 1e4) if years > 0 else float("nan"),
    }


def window_stats(nav: pd.DataFrame, start: str, end: str) -> dict:
    m = (nav["date"] >= start) & (nav["date"] <= end)
    g = nav.loc[m]
    if len(g) < 5:
        return {"n": int(len(g)), "mdd": float("nan"), "total_return": float("nan")}
    return {
        "n": int(len(g)),
        "mdd": mdd(g["nav"]),
        "total_return": total_return(g["nav"]),
        "start": str(pd.to_datetime(g["date"].iloc[0]).date()),
        "end": str(pd.to_datetime(g["date"].iloc[-1]).date()),
    }


def scale_col(df: pd.DataFrame) -> pd.Series:
    for c in ("e45_equity_scale", "e45_exposure", "equity_scale"):
        if c in df.columns:
            return df[c].astype(float)
    raise SystemExit(f"No E45 scale column in {list(df.columns)}")


def load_f1_f7(paths: dict[str, Path]) -> dict:
    fpath = paths["F1F7"]
    # also accept repo reports/
    alt = ROOT / "reports" / "f1_f7_gates.json"
    if not fpath.exists() and alt.exists():
        fpath = alt
    if not fpath.exists():
        raise SystemExit(
            f"Missing F1–F7 gates at {paths['F1F7']} (and {alt}). "
            "Run scripts/e45_feasibility_gates.py on this pack first."
        )
    payload = load_json(fpath)
    if not payload.get("all_pass"):
        raise SystemExit("F1–F7 not all_pass; refuse seal.")
    # normalize to F{n}_* keys with pass bool
    gates = {}
    for k, v in payload.get("gates", {}).items():
        gates[k] = dict(v)
        if "pass" not in gates[k]:
            raise SystemExit(f"Gate {k} missing pass field")
    # require F1..F7 present
    for i in range(1, 8):
        if not any(k.startswith(f"F{i}_") for k in gates):
            raise SystemExit(f"Missing F{i} in gates file {fpath}")
    return {
        "gates": gates,
        "full_sample": payload.get("full_sample"),
        "crisis_path": payload.get("crisis_path"),
        "source": str(fpath),
        "all_pass": True,
    }


def evaluate(paths: dict[str, Path]) -> dict:
    base = pd.read_csv(paths["BASE_NAV"])
    chal = pd.read_csv(paths["CHAL_NAV"])
    base["date"] = pd.to_datetime(base["date"])
    chal["date"] = pd.to_datetime(chal["date"])
    fb = pd.read_csv(paths["BASE_FILLS"])
    fc = pd.read_csv(paths["CHAL_FILLS"])

    prior = load_f1_f7(paths)

    cost_base = fee_turnover(fb, base)
    cost_chal = fee_turnover(fc, chal)
    fee_ratio = cost_chal["fee_bps_per_year_vs_avg_nav"] / max(
        cost_base["fee_bps_per_year_vs_avg_nav"], 1e-9
    )
    # Tightened F8: AND (was OR)
    f8_pass = bool(
        cost_chal["fee_sum"] <= cost_base["fee_sum"] * 1.05 + 1e-9
        and fee_ratio <= 1.25 + 1e-12
    )

    stress: dict = {}
    better = worse = 0
    bad: list[str] = []
    for name, (s, e) in STRESS_WINDOWS.items():
        b = window_stats(base, s, e)
        c = window_stats(chal, s, e)
        imp = (
            (c["mdd"] - b["mdd"]) * 100
            if np.isfinite(b["mdd"]) and np.isfinite(c["mdd"])
            else float("nan")
        )
        retd = (
            c["total_return"] - b["total_return"]
            if np.isfinite(b["total_return"]) and np.isfinite(c["total_return"])
            else float("nan")
        )
        if np.isfinite(imp):
            if imp > 0:
                better += 1
            elif imp < 0:
                worse += 1
            if imp < -1.0:
                bad.append(name)
        stress[name] = {
            "baseline": b,
            "challenger": c,
            "mdd_improvement_pp": imp,
            "return_delta": retd,
        }
    n_windows = len(STRESS_WINDOWS)
    # Tightened F9: strict majority (better > n/2), better > worse, no bad windows
    f9_pass = bool(better > (n_windows / 2.0) and better > worse and len(bad) == 0)

    rec_b = recovery_stats(base["nav"], base["date"])
    rec_c = recovery_stats(chal["nav"], chal["date"])
    scale = scale_col(chal)
    exposure = {
        "mean": float(scale.mean()),
        "min": float(scale.min()),
        "p10": float(scale.quantile(0.10)),
        "frac_below_0_85": float((scale < 0.85).mean()),
    }
    db, dc = rec_b["days_to_recover"], rec_c["days_to_recover"]
    if db is None and dc is None:
        days_ok = True
    elif db is None or dc is None:
        days_ok = False
    else:
        # Tightened F10: no undocumented +5d buffer
        days_ok = dc <= db * 1.15 + 1e-9
    uw_ok = rec_c["longest_underwater_days"] <= rec_b["longest_underwater_days"] + 60
    trough_ok = rec_c["trough_mdd"] >= rec_b["trough_mdd"] - 1e-12
    f10_pass = bool(days_ok and uw_ok and trough_ok)

    gates = dict(prior["gates"])
    gates["F8_cost"] = {
        "pass": f8_pass,
        "baseline": cost_base,
        "challenger": cost_chal,
        "fee_bps_ratio_chal_over_base": fee_ratio,
        "rule": "fee_sum<=1.05x baseline AND fee_bps_ratio<=1.25 (tightened from OR)",
    }
    gates["F9_stress"] = {
        "pass": f9_pass,
        "windows_better": better,
        "windows_worse": worse,
        "bad_windows_gt_1pp_worse": bad,
        "detail": stress,
        "rule": "strict majority stress MDD better; better>worse; no window worse by >1pp",
    }
    gates["F10_recovery"] = {
        "pass": f10_pass,
        "baseline": rec_b,
        "challenger": rec_c,
        "exposure": exposure,
        "rule": "recover days<=1.15x baseline (no +5d); underwater<=+60d; trough MDD not deeper",
    }

    prior_ok = all(
        bool(g.get("pass"))
        for k, g in gates.items()
        if k[0] == "F" and len(k) > 1 and k[1].isdigit() and int(k[1]) <= 7
    )
    seal_ok = f8_pass and f9_pass and f10_pass
    if prior_ok and seal_ok:
        verdict, live_ready = "FEASIBLE_READY_FOR_LIVE_BALLOT", True
    elif any(
        not bool(g.get("pass"))
        for k, g in gates.items()
        if k.startswith(("F3_", "F4_"))
    ):
        verdict, live_ready = "NOT_FEASIBLE_FOR_LIVE", False
    else:
        verdict, live_ready = "FEASIBLE_CONTINUE_PAPER", False

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "charter": str(CHARTER.relative_to(ROOT)) if CHARTER.exists() else str(CHARTER),
        "pack": "cost_stress_recovery_seal",
        "schema": "e45_feasibility_seal.v2",
        "provenance": {
            "in_dir": str(paths["IN"]),
            "input_manifest": load_json(paths["INPUT_MANIFEST"]),
            "output_manifest": load_json(paths["OUTPUT_MANIFEST"]),
            "f1_f7_source": prior["source"],
            "method": "fresh_regen_required_hash_verified_no_reuse_of_prior_pack",
            "output_manifest_hash_verified": True,
        },
        "baseline": "E16_E18_E22_v2s",
        "challenger": "E16_E18_E22_v2s_E45_E3",
        "full_sample": prior.get("full_sample"),
        "crisis_path": prior.get("crisis_path"),
        "cost": {"baseline": cost_base, "challenger": cost_chal},
        "stress_windows": stress,
        "recovery": {"baseline": rec_b, "challenger": rec_c, "exposure": exposure},
        "gates": gates,
        "verdict": verdict,
        "live_ballot_ready": live_ready,
        "official_status_unchanged": official_status_dict(),
        "historical_claim": claim_dict(),
        "lineage": {
            "documented_research": ["E38", "E43", "E44", "E45"],
            "importable_code": ["E1", "E1.1", "E2", "E2.1", "E3", "E45_wrapper"],
        },
        "next_steps": (
            [
                "Human may open a separate live-switch ballot; this pack does not flip live",
                "Keep DEFAULT_BOOKS_VERSION = E22_v2s_tw until ballot ACCEPT",
            ]
            if live_ready
            else [
                "Address failing gates with paper diagnostics (no in-place retune)",
                "Do not open live-switch ballot yet",
                "Keep live DEFAULT_BOOKS_VERSION = E22_v2s_tw",
            ]
        ),
    }


def write_md(v: dict) -> None:
    f = v.get("full_sample") or {}
    hc = v["historical_claim"]
    lines = [
        "# E45 Paper Feasibility Study (2026-09-05)",
        "",
        f"Generated: `{v['generated_at_utc']}`",
        f"Charter: `{v['charter']}`",
        f"Pack: `{v['pack']}`",
        f"Provenance in_dir: `{v['provenance']['in_dir']}`",
        "",
        f"## Verdict: `{v['verdict']}`",
        "",
        f"- Live ballot ready: `{v['live_ballot_ready']}`",
        "- Official status **unchanged** until human ballot: NOT_VERIFIED / DEFERRED / SOFT_FROZEN_CRITICAL / live auth NO",
        f"- Historical −13.16%: **`{hc['label']}`** / interpretation **`{hc['interpretation']}`** (not PASS)",
        "- Seal on **fresh regen** with OUTPUT_MANIFEST **sha256 verified**; F8–F10 tightened (AND / strict majority / no +5d)",
        "",
        "## Comparison (full sample)",
        "",
        "| Arm | CAGR | MDD |",
        "|---|---:|---:|",
    ]
    if f:
        lines += [
            f"| Baseline | {100 * f.get('baseline_cagr', float('nan')):.2f}% | {100 * f.get('baseline_mdd', float('nan')):.2f}% |",
            f"| Challenger | {100 * f.get('challenger_cagr', float('nan')):.2f}% | {100 * f.get('challenger_mdd', float('nan')):.2f}% |",
            f"| Delta | **{-f.get('cagr_giveback_pp', float('nan')):+.2f} pp** | **{f.get('mdd_improvement_pp', float('nan')):+.2f} pp** |",
            "",
        ]
    lines += ["## Gates F1–F10", "", "| Gate | Pass |", "|---|---|"]
    for k, g in v["gates"].items():
        lines.append(f"| `{k}` | **{g.get('pass')}** |")

    cb, cc = v["cost"]["baseline"], v["cost"]["challenger"]
    lines += [
        "",
        "## F8 Cost (from regenerated fills)",
        "",
        "| Arm | Fills | Fee sum | Fee bps/yr | Ann. turnover approx |",
        "|---|---:|---:|---:|---:|",
        f"| Baseline | {cb['n_fills']} | {cb['fee_sum']:.0f} | {cb['fee_bps_per_year_vs_avg_nav']:.1f} | {cb['annualized_turnover_approx']:.2f} |",
        f"| Challenger | {cc['n_fills']} | {cc['fee_sum']:.0f} | {cc['fee_bps_per_year_vs_avg_nav']:.1f} | {cc['annualized_turnover_approx']:.2f} |",
        "",
        "## F9 Named stress windows (from regenerated NAV)",
        "",
        "| Window | Baseline MDD | Challenger MDD | Δ pp | Return Δ |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, s in v["stress_windows"].items():
        lines.append(
            f"| {name} | {100 * s['baseline']['mdd']:.2f}% | {100 * s['challenger']['mdd']:.2f}% | "
            f"{s['mdd_improvement_pp']:+.2f} | {100 * s['return_delta']:+.2f}% |"
        )
    rb, rc = v["recovery"]["baseline"], v["recovery"]["challenger"]
    exp = v["recovery"]["exposure"]
    lines += [
        "",
        "## F10 Recovery (from regenerated NAV)",
        "",
        "| Arm | Trough date | Trough MDD | Days to recover | Longest underwater |",
        "|---|---|---:|---:|---:|",
        f"| Baseline | {rb['trough_date']} | {100 * rb['trough_mdd']:.2f}% | {rb['days_to_recover']} | {rb['longest_underwater_days']} |",
        f"| Challenger | {rc['trough_date']} | {100 * rc['trough_mdd']:.2f}% | {rc['days_to_recover']} | {rc['longest_underwater_days']} |",
        "",
        f"- Mean E45 scale: **{exp['mean']:.3f}** (min {exp['min']:.3f}; frac<0.85 = {exp['frac_below_0_85']:.1%})",
        "",
        "## Lineage honesty",
        "",
        "- **DOCUMENTED RESEARCH LINEAGE:** `E38 → E43 → E44 → E45`",
        "- **IMPORTABLE CODE LINEAGE:** `E1 → E1.1 → E2 → E2.1 → E3 → E45 wrapper`",
        "",
        "## Next steps",
        "",
    ]
    for s in v["next_steps"]:
        lines.append(f"- {s}")
    lines += [
        "",
        "## Artifacts",
        "",
        f"- `{STUDY_JSON.relative_to(ROOT)}`",
        f"- `{v['provenance']['in_dir']}/`",
        "- Scripts: `scripts/e45_feasibility_gates.py`, `scripts/e45_feasibility_seal_pack.py`",
        "",
        "## Label",
        "",
        f"`E45_FEASIBILITY_STUDY_2026-09-05__{v['verdict']}__FRESH_REGEN_HASH_VERIFIED`",
        "",
    ]
    STUDY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--in", dest="in_dir", type=Path, default=DEFAULT_IN)
    args = ap.parse_args()
    paths = resolve_paths(args.in_dir)
    v = evaluate(paths)
    paths["OUT"].mkdir(parents=True, exist_ok=True)

    seal_body = dumps_json(v)
    (paths["OUT"] / "cost_stress_recovery_seal.json").write_text(seal_body, encoding="utf-8")
    # SEAL_LOCK owned by seal — gates must not overwrite
    lock = {
        "schema": "e45_feasibility_seal_lock.v1",
        "generated_at_utc": v["generated_at_utc"],
        "verdict": v["verdict"],
        "live_ballot_ready": v["live_ballot_ready"],
        "pack_dir": str(paths["IN"]),
        "gates_pass": {k: bool(g.get("pass")) for k, g in v["gates"].items()},
        "note": "Authoritative seal lock. e45_feasibility_gates.py must not overwrite this file or the study verdict.",
    }
    paths["SEAL_LOCK"].write_text(dumps_json(lock), encoding="utf-8")
    STUDY_JSON.write_text(seal_body, encoding="utf-8")
    write_md(v)
    # Convenience alias (does not replace SEAL_LOCK)
    (paths["IN"] / "feasibility_gates.json").write_text(seal_body, encoding="utf-8")

    print(
        dumps_json(
            {
                "verdict": v["verdict"],
                "live_ballot_ready": v["live_ballot_ready"],
                "in_dir": str(paths["IN"]),
                "F8": v["gates"]["F8_cost"]["pass"],
                "F9": v["gates"]["F9_stress"]["pass"],
                "F10": v["gates"]["F10_recovery"]["pass"],
                "historical_interpretation": v["historical_claim"]["interpretation"],
            }
        )
    )
    if not v["live_ballot_ready"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
