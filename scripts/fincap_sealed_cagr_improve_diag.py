#!/usr/bin/env python3
"""FIN concentration sealed-CAGR improvement diagnostics (RESEARCH_ONLY).

Explains why FIN_CAP_50 / L3_MILD fail sealed CAGR, and compares
path-conditional alternatives WITHOUT selecting on sealed.

Selection-safe windows for ranking improvement ideas:
  - OOF 2012-12-04 .. 2018-12-31
  - Late-bull proxy 2017-01-01 .. 2018-12-31

Sealed 2023+ / val 2019-2022 are DIAGNOSTIC ONLY (reported, not used to pick).

Forbidden: Soft-Frozen flip; retune FIN_CAP_50 / L1 / L2 / L3 locks as live cuts.
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

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/fincap-sealed-cagr-improve"
RESEARCH = ROOT / "research/gaps"
MARKET_PATH = ROOT / "forward/e21/live_market.csv"
DIV_PATH = ROOT / "data/dividend_events/e22_dividend_events.csv"

OOF = (date(2012, 12, 4), date(2018, 12, 31))
LATE_BULL = (date(2017, 1, 1), date(2018, 12, 31))
VAL = (date(2019, 1, 1), date(2022, 12, 31))
SEALED_START = date(2023, 1, 1)


def load_market() -> pd.DataFrame:
    market = pd.read_csv(MARKET_PATH, dtype={"code": str})
    market["date"] = pd.to_datetime(market["date"])
    required = set(ALL + ["TAIEX"])
    complete = market.groupby("date")["code"].apply(lambda s: required.issubset(set(s)))
    return market[market["date"].isin(complete[complete].index)].sort_values(["date", "code"])


def window_stats(nav: pd.DataFrame, start: date, end: date) -> dict:
    d = nav.copy()
    d["date"] = pd.to_datetime(d["date"]).dt.date
    d = d[(d["date"] >= start) & (d["date"] <= end)].reset_index(drop=True)
    if len(d) < 30:
        return {"cagr": None, "max_drawdown": None, "n_days": int(len(d))}
    d = d.copy()
    d["nav"] = d["nav"] / float(d["nav"].iloc[0])
    out = nav_stats(d)
    out["n_days"] = int(len(d))
    return out


def score(nav_b, nav_x, start, end, name: str) -> dict:
    b = window_stats(nav_b, start, end)
    x = window_stats(nav_x, start, end)
    if b["cagr"] is None or x["cagr"] is None:
        return {
            "window": name,
            "pass_diag": False,
            "mdd_improve_pp": None,
            "cagr_giveback_pp": None,
            "n_days": b["n_days"],
        }
    mdd_pp = (abs(b["max_drawdown"]) - abs(x["max_drawdown"])) * 100.0
    gb_pp = (b["cagr"] - x["cagr"]) * 100.0
    return {
        "window": name,
        "base_cagr": b["cagr"],
        "base_mdd": b["max_drawdown"],
        "cand_cagr": x["cagr"],
        "cand_mdd": x["max_drawdown"],
        "mdd_improve_pp": mdd_pp,
        "cagr_giveback_pp": gb_pp,
        "n_days": b["n_days"],
        # diagnostic gate mirrors live-verify (not used for selection here)
        "pass_diag": (mdd_pp >= 1.0 and gb_pp <= 3.0),
    }


def mean_fin(target: pd.DataFrame, start: date, end: date) -> float:
    idx = pd.to_datetime(target.index).date
    m = (idx >= start) & (idx <= end)
    return float(target.loc[m, "Financial"].mean()) if m.any() else float("nan")


def blend_targets(base: pd.DataFrame, cap: pd.DataFrame, alpha: float) -> pd.DataFrame:
    common = base.index.intersection(cap.index)
    cols = ["Financial", "Telecom", "0050"]
    out = alpha * cap.loc[common, cols].astype(float) + (1.0 - alpha) * base.loc[common, cols].astype(
        float
    )
    s = out.sum(axis=1).replace(0.0, 1.0)
    return out.div(s, axis=0)


def path_conditional_target(
    base: pd.DataFrame,
    cap: pd.DataFrame,
    regime: pd.Series,
    mode: str,
    dd_thr: float = -0.08,
) -> pd.DataFrame:
    """Use CAP weights only on stressed days; else BASE Soft-Frozen path."""
    common = base.index.intersection(cap.index)
    cols = ["Financial", "Telecom", "0050"]
    reg = regime.reindex(common)
    if mode == "bull_restore":
        # clip only outside Bull
        use_cap = reg.astype(str) != "Bull"
    elif mode == "dd_only":
        # approximate TAIEX DD from regime Crisis OR Bear with simple path:
        # prefer Crisis label + Bear as stressed; also if available use rolling —
        # here: apply CAP on Crisis/Bear only (conservative proxy for DD path)
        use_cap = reg.astype(str).isin(["Crisis", "Bear"])
    elif mode == "crisis_only":
        use_cap = reg.astype(str) == "Crisis"
    else:
        raise ValueError(mode)
    use_cap = use_cap.fillna(False)
    out = base.loc[common, cols].astype(float).copy()
    out.loc[use_cap, cols] = cap.loc[use_cap, cols].astype(float)
    s = out.sum(axis=1).replace(0.0, 1.0)
    return out.div(s, axis=0), use_cap


def year_givebacks(nav_b, nav_x, start_y: int, end_y: int) -> list[dict]:
    rows = []
    for y in range(start_y, end_y + 1):
        r = score(nav_b, nav_x, date(y, 1, 1), date(y, 12, 31), f"y{y}")
        if r.get("cagr_giveback_pp") is None:
            continue
        rows.append(
            {
                "year": y,
                "cagr_giveback_pp": r["cagr_giveback_pp"],
                "mdd_improve_pp": r["mdd_improve_pp"],
                "cand_cagr": r["cand_cagr"],
                "base_cagr": r["base_cagr"],
            }
        )
    return rows


def main() -> None:
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)

    print("loading market ...", flush=True)
    market = load_market()
    dividends = pd.read_csv(DIV_PATH, dtype={"code": str}) if DIV_PATH.exists() else pd.DataFrame()

    print("BASE + FIN50/60/70 targets ...", flush=True)
    _p, _s, base_t, base_reg = e16_features(market)
    _p50, _s50, fin50_t, fin50_reg = e16_features_fin_cap(market, 0.35, 0.50)
    _p60, _s60, fin60_t, fin60_reg = e16_features_fin_cap(market, 0.35, 0.60)
    _p70, _s70, fin70_t, _ = e16_features_fin_cap(market, 0.50, 0.70)

    # path-conditional variants (improvement hypotheses)
    br50_t, br50_flag = path_conditional_target(base_t, fin50_t, base_reg, "bull_restore")
    br60_t, br60_flag = path_conditional_target(base_t, fin60_t, base_reg, "bull_restore")
    dd50_t, dd50_flag = path_conditional_target(base_t, fin50_t, base_reg, "dd_only")
    cr50_t, cr50_flag = path_conditional_target(base_t, fin50_t, base_reg, "crisis_only")
    blend25_t = blend_targets(base_t, fin50_t, 0.25)
    blend50_t = blend_targets(base_t, fin50_t, 0.50)

    candidates = [
        ("BASE", base_t, base_reg, None, "baseline"),
        ("FIN_CAP_50_REF", fin50_t, fin50_reg, None, "blocked_static_ref"),
        ("L3_MILD_35_60_REF", fin60_t, fin60_reg, None, "failed_l3_static_ref"),
        ("FIN_CAP_70_STATIC", fin70_t, base_reg, None, "milder_static"),
        ("BLEND_025", blend25_t, base_reg, None, "static_blend"),
        ("BLEND_050", blend50_t, base_reg, None, "static_blend"),
        ("BULL_RESTORE_50", br50_t, base_reg, br50_flag, "path_conditional"),
        ("BULL_RESTORE_60", br60_t, base_reg, br60_flag, "path_conditional"),
        ("DD_BEAR_CRISIS_50", dd50_t, base_reg, dd50_flag, "path_conditional"),
        ("CRISIS_ONLY_50", cr50_t, base_reg, cr50_flag, "path_conditional"),
    ]

    asof = None
    navs = {}
    rows = []
    for cid, target, regime, flag, family in candidates:
        print(f"simulating {cid} ...", flush=True)
        nav, _f, meta = simulate_core(
            market,
            target,
            regime,
            dividends,
            apply_e22=True,
            e22_version=e22div.E22_V2S,
            apply_stock_div=True,
        )
        navs[cid] = nav
        if asof is None:
            asof = pd.to_datetime(nav["date"]).dt.date.max()
        oof = score(navs["BASE"] if cid != "BASE" else nav, nav, OOF[0], OOF[1], "oof")
        late = score(navs["BASE"] if cid != "BASE" else nav, nav, LATE_BULL[0], LATE_BULL[1], "late_bull")
        val = score(navs["BASE"] if cid != "BASE" else nav, nav, VAL[0], VAL[1], "val")
        sealed = score(navs["BASE"] if cid != "BASE" else nav, nav, SEALED_START, asof, "sealed")
        # for BASE, recompute vs itself after BASE nav exists
        if cid == "BASE":
            oof = score(nav, nav, OOF[0], OOF[1], "oof")
            late = score(nav, nav, LATE_BULL[0], LATE_BULL[1], "late_bull")
            val = score(nav, nav, VAL[0], VAL[1], "val")
            sealed = score(nav, nav, SEALED_START, asof, "sealed")

        flag_share_oof = None
        flag_share_sealed = None
        if flag is not None:
            idx = pd.to_datetime(flag.index).date
            mo = (idx >= OOF[0]) & (idx <= OOF[1])
            ms = (idx >= SEALED_START) & (idx <= asof)
            flag_share_oof = float(flag.loc[mo].mean()) if mo.any() else None
            flag_share_sealed = float(flag.loc[ms].mean()) if ms.any() else None

        # selection-safe score: prefer low late-bull giveback, require OOF MDD>=1 and OOF CAGR gb<=1.5
        oof_ok = (
            cid != "BASE"
            and oof["mdd_improve_pp"] is not None
            and oof["mdd_improve_pp"] >= 1.0
            and oof["cagr_giveback_pp"] <= 1.5
            and late["cagr_giveback_pp"] is not None
            and late["cagr_giveback_pp"] <= 1.5
            and bool(meta.get("exact_t1_ok"))
        )
        rows.append(
            {
                "id": cid,
                "family": family,
                "exact_t1_ok": bool(meta.get("exact_t1_ok")),
                "mean_fin_oof": mean_fin(target, OOF[0], OOF[1]),
                "mean_fin_sealed": mean_fin(target, SEALED_START, asof),
                "flag_share_oof": flag_share_oof,
                "flag_share_sealed": flag_share_sealed,
                "oof_mdd_improve_pp": oof["mdd_improve_pp"],
                "oof_cagr_giveback_pp": oof["cagr_giveback_pp"],
                "late_bull_cagr_giveback_pp": late["cagr_giveback_pp"],
                "val_mdd_improve_pp": val["mdd_improve_pp"],
                "val_cagr_giveback_pp": val["cagr_giveback_pp"],
                "val_pass_diag": val["pass_diag"],
                "sealed_mdd_improve_pp": sealed["mdd_improve_pp"],
                "sealed_cagr_giveback_pp": sealed["cagr_giveback_pp"],
                "sealed_pass_diag": sealed["pass_diag"],
                "selection_safe_oof_ok": oof_ok,
                "sealed_years": year_givebacks(navs["BASE"], nav, 2023, asof.year)
                if cid != "BASE"
                else [],
                "windows": {"oof": oof, "late_bull": late, "val": val, "sealed": sealed},
            }
        )
        print(
            f"  {cid}: OOF MDD {oof['mdd_improve_pp']:+.2f} CAGR gb {oof['cagr_giveback_pp']:+.2f} | "
            f"late gb {late['cagr_giveback_pp']:+.2f} | sealed gb {sealed['cagr_giveback_pp']:+.2f} "
            f"pass_diag={sealed['pass_diag']} sel_ok={oof_ok}",
            flush=True,
        )

    # After BASE exists, fix BASE-relative scores for others already computed correctly
    # Rank improvement hypotheses by selection-safe then diagnostic sealed (report only)
    challengers = [r for r in rows if r["id"] != "BASE"]
    sel_ok = [r for r in challengers if r["selection_safe_oof_ok"]]
    # diagnostic Pareto: sealed pass_diag among selection-safe
    sealed_ok_sel = [r for r in sel_ok if r["sealed_pass_diag"]]

    implications = [
        "Static FIN caps (50/60) improve MDD but leak sealed CAGR in 2024–2026 bull stretch.",
        "Path-conditional caps (Bull-restore / Crisis-only) aim to keep Soft-Frozen finance beta in Bull while cutting only in stress.",
        "Do not retune FIN_CAP_50 / L3_MILD_35_60 locks; screen new path-conditional family under a frozen L4 charter.",
        "Soft-Frozen live stays [0.50, 0.95] until human cutover after sealed-aware PASS.",
    ]

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "FINCAP_SEALED_CAGR_IMPROVE_DIAGNOSTIC",
        "live_wire": False,
        "research_only": True,
        "asof": str(asof),
        "selection_policy": {
            "used_for_ranking": ["oof", "late_bull"],
            "diagnostic_only": ["val", "sealed"],
            "note": "Sealed metrics reported for mechanism insight; must not pick a live cut.",
        },
        "n_selection_safe": len(sel_ok),
        "n_selection_safe_and_sealed_diag_pass": len(sealed_ok_sel),
        "selection_safe_ids": [r["id"] for r in sel_ok],
        "selection_safe_and_sealed_diag_pass_ids": [r["id"] for r in sealed_ok_sel],
        "candidates": rows,
        "implications": implications,
        "recommended_next_families": [
            "L4-BULL-RESTORE (FIN50/60 only outside Bull)",
            "L4-CRISIS-ONLY (FIN50 only in Crisis)",
            "L4-DD-PATH (FIN cap only in active index DD; stricter than Bear/Crisis proxy)",
        ],
        "forbidden": [
            "retune FIN_CAP_50 lock",
            "retune L3_MILD_35_60",
            "reopen L1 COMBO",
            "silent Soft-Frozen flip",
        ],
    }

    (OUT / "reports" / "fincap_sealed_cagr_improve.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )
    (RESEARCH / "FINCAP_SEALED_CAGR_IMPROVE_DIAGNOSTIC.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )
    flat = []
    for r in rows:
        flat.append({k: v for k, v in r.items() if k not in {"windows", "sealed_years"}})
    pd.DataFrame(flat).to_csv(OUT / "outputs" / "improve_candidates.csv", index=False)

    lines = [
        "# FIN Concentration — Sealed CAGR Improvement Diagnostics",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        f"As-of: `{asof}`",
        "Status: **RESEARCH_ONLY** — no Soft-Frozen edit; sealed used diagnostically only.",
        "",
        "## Problem",
        "",
        "FIN_CAP_50 / L3 static mild caps clear combined 2019+ or OOF, but **sealed 2023+ CAGR giveback** "
        "fails live-aware gates (~4.1–4.3 pp). Go-live verify also tripped PAUSE_REVIEW on trailing windows.",
        "",
        "## Candidates (Exact T+1)",
        "",
        "| ID | Family | OOF MDDΔ | OOF CAGRgb | Late-bull gb | Sealed MDDΔ | Sealed CAGRgb | Sealed diag | Sel-safe |",
        "|---|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['id']} | {r['family']} | "
            f"{(r['oof_mdd_improve_pp'] if r['oof_mdd_improve_pp'] is not None else float('nan')):+.2f} | "
            f"{(r['oof_cagr_giveback_pp'] if r['oof_cagr_giveback_pp'] is not None else float('nan')):+.2f} | "
            f"{(r['late_bull_cagr_giveback_pp'] if r['late_bull_cagr_giveback_pp'] is not None else float('nan')):+.2f} | "
            f"{(r['sealed_mdd_improve_pp'] if r['sealed_mdd_improve_pp'] is not None else float('nan')):+.2f} | "
            f"{(r['sealed_cagr_giveback_pp'] if r['sealed_cagr_giveback_pp'] is not None else float('nan')):+.2f} | "
            f"{'Y' if r['sealed_pass_diag'] else ('—' if r['id']=='BASE' else '')} | "
            f"{'Y' if r['selection_safe_oof_ok'] else ('—' if r['id']=='BASE' else '')} |"
        )

    lines += [
        "",
        "### Selection-safe (OOF MDD≥1 & OOF/late CAGR gb≤1.5)",
        "",
        f"- Count: **{len(sel_ok)}** → `{[r['id'] for r in sel_ok]}`",
        f"- Of which sealed-diag PASS: **{len(sealed_ok_sel)}** → `{[r['id'] for r in sealed_ok_sel]}`",
        "",
        "## Implications",
        "",
    ]
    for i, t in enumerate(implications, 1):
        lines.append(f"{i}. {t}")
    lines += [
        "",
        "## Recommended next research",
        "",
        "Freeze **L4 path-conditional FIN charter**: Bull-restore / Crisis-only / true DD-path first.",
        "Do **not** retune FIN_CAP_50 or L3_MILD_35_60. Soft-Frozen stays [0.50, 0.95].",
        "",
        "See: `research/gaps/MDD_L4_PATH_FINCAP_CHARTER.md`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "FINCAP_SEALED_CAGR_IMPROVE_DIAGNOSTIC.md").write_text(md)
    (RESEARCH / "FINCAP_SEALED_CAGR_IMPROVE_DIAGNOSTIC.md").write_text(md)
    print(
        json.dumps(
            {
                "n_selection_safe": len(sel_ok),
                "selection_safe": [r["id"] for r in sel_ok],
                "sealed_diag_pass_among_safe": [r["id"] for r in sealed_ok_sel],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
