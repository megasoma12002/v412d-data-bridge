#!/usr/bin/env python3
"""L4 MDD Path/FINCAP Exact T+1 OOF screen (RESEARCH_ONLY).

Charter: research/gaps/MDD_L4_PATH_FINCAP_CHARTER.md
Gates: research/gaps/MDD_L4_PATH_FINCAP_GATES.json

Parents frozen-stopped: L1 / L2 / L3. Soft-Frozen live clip stays [0.50, 0.95].

Screen first: L4-CRISIS-ONLY + L4-FINCAP-70 + L4-BLEND-LIGHT (+ L4-DD-PATH).
Selection: util = MDD_improve_pp − 0.5×late_bull_cagr_gb  (NO harsh-cap family priority).

OOF: 2012-12-04 .. 2018-12-31
Pass: Exact T+1
  AND MDD improve >= 1.5pp
  AND CAGR giveback <= 1.5pp
  AND late-bull (2017-2018) CAGR giveback <= 1.5pp
No live-wire. Held-out not used for selection.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from research_metric_helpers import mdd_delta_pp, cagr_delta_pp
import e22_dividend_accounting as e22div
import mdd_l1_loss_engine_oof as oof
import mdd_l2_loss_engine_oof as l2

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/mdd-loss-engine/l4_oof"
RESEARCH = ROOT / "research/gaps"

OOF_START, OOF_END = date(2012, 12, 4), date(2018, 12, 31)
LATE_BULL_START, LATE_BULL_END = date(2017, 1, 1), date(2018, 12, 31)
MDD_IMPROVE_MIN = 0.015
CAGR_GIVEBACK_MAX = 0.015
LATE_BULL_CAGR_GIVEBACK_MAX = 0.015

# Predeclared — freeze after first OOF peek
CANDIDATES: list[dict] = [
    {"id": "BASE", "family": "BASE", "kind": "base", "params": {}, "lockable": False},
    # references (not lockable) — blocked / stopped parents
    {
        "id": "FIN_CAP_50_REF",
        "family": "REF-STOPPED",
        "kind": "fin_cap",
        "params": {"fin_lo": 0.35, "fin_hi": 0.50},
        "lockable": False,
    },
    {
        "id": "L3_MILD_35_60_REF",
        "family": "REF-STOPPED",
        "kind": "fin_cap",
        "params": {"fin_lo": 0.35, "fin_hi": 0.60},
        "lockable": False,
    },
    # L4-CRISIS-ONLY
    {
        "id": "L4_CRISIS_ONLY_50",
        "family": "L4-CRISIS-ONLY",
        "kind": "crisis_only",
        "params": {"fin_lo": 0.35, "fin_hi": 0.50},
        "lockable": True,
    },
    # L4-FINCAP-70
    {
        "id": "L4_FINCAP_70_35",
        "family": "L4-FINCAP-70",
        "kind": "fin_cap",
        "params": {"fin_lo": 0.35, "fin_hi": 0.70},
        "lockable": True,
    },
    {
        "id": "L4_FINCAP_70_50",
        "family": "L4-FINCAP-70",
        "kind": "fin_cap",
        "params": {"fin_lo": 0.50, "fin_hi": 0.70},
        "lockable": True,
    },
    # L4-BLEND-LIGHT
    {
        "id": "L4_BLEND_025",
        "family": "L4-BLEND-LIGHT",
        "kind": "blend",
        "params": {"alpha": 0.25},
        "lockable": True,
    },
    {
        "id": "L4_BLEND_050",
        "family": "L4-BLEND-LIGHT",
        "kind": "blend",
        "params": {"alpha": 0.50},
        "lockable": True,
    },
    # L4-DD-PATH (true TAIEX path DD)
    {
        "id": "L4_DD_PATH_08_50",
        "family": "L4-DD-PATH",
        "kind": "dd_path",
        "params": {"dd_thr": -0.08, "fin_lo": 0.35, "fin_hi": 0.50},
        "lockable": True,
    },
    {
        "id": "L4_DD_PATH_10_50",
        "family": "L4-DD-PATH",
        "kind": "dd_path",
        "params": {"dd_thr": -0.10, "fin_lo": 0.35, "fin_hi": 0.50},
        "lockable": True,
    },
]


def blend_targets(base: pd.DataFrame, fin50: pd.DataFrame, alpha: float) -> pd.DataFrame:
    common = base.index.intersection(fin50.index)
    cols = ["Financial", "Telecom", "0050"]
    out = alpha * fin50.loc[common, cols].astype(float) + (1.0 - alpha) * base.loc[
        common, cols
    ].astype(float)
    s = out.sum(axis=1).replace(0.0, 1.0)
    return out.div(s, axis=0)


def crisis_only_target(base: pd.DataFrame, cap: pd.DataFrame, regime: pd.Series) -> tuple[pd.DataFrame, pd.Series]:
    """FIN_CAP weights only on Crisis regime days; else Soft-Frozen BASE."""
    common = base.index.intersection(cap.index)
    cols = ["Financial", "Telecom", "0050"]
    use_cap = (regime.reindex(common).astype(str) == "Crisis").fillna(False)
    out = base.loc[common, cols].astype(float).copy()
    out.loc[use_cap, cols] = cap.loc[use_cap, cols].astype(float)
    s = out.sum(axis=1).replace(0.0, 1.0)
    return out.div(s, axis=0), use_cap


def dd_path_target(
    base: pd.DataFrame,
    cap: pd.DataFrame,
    prices: pd.DataFrame,
    dd_thr: float,
) -> tuple[pd.DataFrame, pd.Series]:
    """FIN_CAP only while TAIEX active DD from 252d peak <= dd_thr; else BASE."""
    common = base.index.intersection(cap.index)
    cols = ["Financial", "Telecom", "0050"]
    dd = l2.taiex_dd_from_peak(prices).reindex(common)
    use_cap = (dd <= float(dd_thr)).fillna(False)
    out = base.loc[common, cols].astype(float).copy()
    out.loc[use_cap, cols] = cap.loc[use_cap, cols].astype(float)
    s = out.sum(axis=1).replace(0.0, 1.0)
    return out.div(s, axis=0), use_cap


def mean_fin_weight(target: pd.DataFrame, start: date, end: date) -> float:
    idx = pd.to_datetime(target.index).date
    m = (idx >= start) & (idx <= end)
    return float(target.loc[m, "Financial"].mean()) if m.any() else float("nan")


def util_score(mdd_improve_pp: float, late_bull_gb_pp: float) -> float:
    """Charter util: maximize MDD improve − 0.5×late_bull_cagr_gb."""
    return float(mdd_improve_pp) - 0.5 * float(late_bull_gb_pp)


def main() -> None:
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)

    print("loading market + BASE/FIN50 targets ...", flush=True)
    market = oof.load_market()
    dividends = (
        pd.read_csv(oof.DIV_PATH, dtype={"code": str}) if oof.DIV_PATH.exists() else pd.DataFrame()
    )
    prices, _s, base_target, base_regime = oof.e16_features(market)
    _p2, _s2, fin50_target, fin50_regime = oof.e16_features_fin_cap(market, 0.35, 0.50)

    fin_cache: dict[tuple[float, float], tuple[pd.DataFrame, pd.Series]] = {
        (0.35, 0.50): (fin50_target, fin50_regime)
    }

    rows: list[dict] = []
    flag_share: dict[str, float] = {}

    for cand in CANDIDATES:
        cid = cand["id"]
        print(f"simulating {cid} ...", flush=True)
        kind = cand["kind"]
        params = cand["params"]
        flag = None

        if kind == "base":
            target, regime = base_target, base_regime
        elif kind == "fin_cap":
            key = (float(params["fin_lo"]), float(params["fin_hi"]))
            if key not in fin_cache:
                _px, _sl, tgt, reg = oof.e16_features_fin_cap(market, key[0], key[1])
                fin_cache[key] = (tgt, reg)
            target, regime = fin_cache[key]
        elif kind == "blend":
            target = blend_targets(base_target, fin50_target, float(params["alpha"]))
            regime = base_regime
        elif kind == "crisis_only":
            key = (float(params["fin_lo"]), float(params["fin_hi"]))
            if key not in fin_cache:
                _px, _sl, tgt, reg = oof.e16_features_fin_cap(market, key[0], key[1])
                fin_cache[key] = (tgt, reg)
            cap_t, _ = fin_cache[key]
            target, flag = crisis_only_target(base_target, cap_t, base_regime)
            regime = base_regime
        elif kind == "dd_path":
            key = (float(params["fin_lo"]), float(params["fin_hi"]))
            if key not in fin_cache:
                _px, _sl, tgt, reg = oof.e16_features_fin_cap(market, key[0], key[1])
                fin_cache[key] = (tgt, reg)
            cap_t, _ = fin_cache[key]
            target, flag = dd_path_target(
                base_target, cap_t, prices, float(params["dd_thr"])
            )
            regime = base_regime
        else:
            raise ValueError(f"unknown kind {kind}")

        nav, fills, meta = oof.simulate_core(
            market,
            target,
            regime,
            dividends,
            apply_e22=True,
            e22_version=e22div.E22_V2S,
            apply_stock_div=True,
            e45_exposure=None,
        )
        nav.to_csv(OUT / "outputs" / f"{cid.lower()}_daily_nav.csv", index=False)
        if cid in {
            "BASE",
            "L4_CRISIS_ONLY_50",
            "L4_FINCAP_70_50",
            "L4_BLEND_050",
            "L4_DD_PATH_08_50",
        }:
            fills.to_csv(OUT / "outputs" / f"{cid.lower()}_fills.csv", index=False)

        oof_stats = oof.window_nav_stats(nav, OOF_START, OOF_END)
        late = oof.window_nav_stats(nav, LATE_BULL_START, LATE_BULL_END)
        fs = float("nan")
        if flag is not None:
            idx = pd.to_datetime(flag.index).date
            m = (idx >= OOF_START) & (idx <= OOF_END)
            fs = float(flag.loc[m].mean()) if m.any() else float("nan")
            flag_share[cid] = fs

        rows.append(
            {
                "id": cid,
                "family": cand["family"],
                "kind": kind,
                "params": params,
                "lockable": bool(cand["lockable"]),
                "exact_t1_ok": bool(meta.get("exact_t1_ok")),
                "same_bar_fills": int(meta.get("same_bar_fills", -1)),
                "oof_cagr": oof_stats.get("cagr"),
                "oof_mdd": oof_stats.get("max_drawdown"),
                "oof_n_days": oof_stats.get("n_days"),
                "late_bull_cagr": late.get("cagr"),
                "late_bull_mdd": late.get("max_drawdown"),
                "late_bull_n_days": late.get("n_days"),
                "mean_fin_w_oof": mean_fin_weight(target, OOF_START, OOF_END),
                "oof_flag_share": fs,
                "n_fills": meta.get("n_fills"),
            }
        )
        print(
            f"  {cid}: OOF CAGR={oof_stats.get('cagr')} MDD={oof_stats.get('max_drawdown')} "
            f"late_bull_cagr={late.get('cagr')} fin_w={rows[-1]['mean_fin_w_oof']:.3f}",
            flush=True,
        )

    base_row = next(r for r in rows if r["id"] == "BASE")
    scored: list[dict] = []
    for r in rows:
        if r["id"] == "BASE":
            scored.append(
                {
                    **r,
                    "mdd_improve_pp": 0.0,
                    "cagr_giveback_pp": 0.0,
                    "late_bull_cagr_giveback_pp": 0.0,
                    "util": 0.0,
                    "pass_oof": False,
                    "is_baseline": True,
                    "fail_reasons": [],
                }
            )
            continue

        mdd_improve = mdd_delta_pp(base_row["oof_mdd"], r["oof_mdd"]) / 100.0
        _cgb = cagr_delta_pp(base_row["oof_cagr"], r["oof_cagr"], missing_as_zero=True); cagr_gb = 0.0 if _cgb is None else _cgb / 100.0
        _lgb = cagr_delta_pp(base_row["late_bull_cagr"], r["late_bull_cagr"], missing_as_zero=True); late_gb = 0.0 if _lgb is None else _lgb / 100.0
        reasons: list[str] = []
        if not r["exact_t1_ok"]:
            reasons.append("exact_t1")
        if r["oof_mdd"] is None or mdd_improve < MDD_IMPROVE_MIN:
            reasons.append("mdd_improve")
        if r["oof_cagr"] is None or cagr_gb > CAGR_GIVEBACK_MAX:
            reasons.append("cagr_giveback")
        if r["late_bull_cagr"] is None or late_gb > LATE_BULL_CAGR_GIVEBACK_MAX:
            reasons.append("late_bull_cagr_giveback")
        if not r["lockable"] and not reasons:
            reasons.append("not_lockable_reference")

        mdd_pp = mdd_improve * 100.0
        late_pp = late_gb * 100.0
        scored.append(
            {
                **r,
                "mdd_improve_pp": mdd_pp,
                "cagr_giveback_pp": cagr_gb * 100.0,
                "late_bull_cagr_giveback_pp": late_pp,
                "util": util_score(mdd_pp, late_pp),
                "pass_oof": len(reasons) == 0,
                "is_baseline": False,
                "fail_reasons": reasons,
                "base_oof_cagr": base_row["oof_cagr"],
                "base_oof_mdd": base_row["oof_mdd"],
                "base_late_bull_cagr": base_row["late_bull_cagr"],
            }
        )

    passers = [r for r in scored if r.get("pass_oof")]
    winner = None
    if passers:
        # util-rank only — no family priority to harsher caps (L3 trap)
        winner = sorted(
            passers,
            key=lambda x: (
                -x["util"],
                -x["mdd_improve_pp"],
                x["late_bull_cagr_giveback_pp"],
                x["cagr_giveback_pp"],
                x["mean_fin_w_oof"],  # lower FIN cut = higher mean fin weight preferred on ties
                x["id"],
            ),
        )[0]

    decision = "OOF_L4_READY_FOR_ADV_LITE" if winner else "STOP_L4_OOF_NO_PASSER"
    locked = winner["id"] if winner else None

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": decision,
        "live_wire": False,
        "research_only": True,
        "retune_allowed": False,
        "l1_l2_l3_retune_forbidden": True,
        "soft_frozen_live_clip": [0.50, 0.95],
        "oof_window": {"start": str(OOF_START), "end": str(OOF_END)},
        "late_bull_window": {"start": str(LATE_BULL_START), "end": str(LATE_BULL_END)},
        "gates": {
            "mdd_improve_pp_min": MDD_IMPROVE_MIN * 100,
            "cagr_giveback_pp_max": CAGR_GIVEBACK_MAX * 100,
            "late_bull_cagr_giveback_pp_max": LATE_BULL_CAGR_GIVEBACK_MAX * 100,
            "exact_t1": True,
            "selection": "util_mdd_minus_0_5_late_bull_gb_no_harsh_family_priority",
        },
        "screen_families": [
            "L4-CRISIS-ONLY",
            "L4-FINCAP-70",
            "L4-BLEND-LIGHT",
            "L4-DD-PATH",
        ],
        "base": {
            "oof_cagr": base_row["oof_cagr"],
            "oof_mdd": base_row["oof_mdd"],
            "late_bull_cagr": base_row["late_bull_cagr"],
            "exact_t1_ok": base_row["exact_t1_ok"],
            "mean_fin_w_oof": base_row["mean_fin_w_oof"],
        },
        "candidates": scored,
        "n_passers": len(passers),
        "locked_winner": locked,
        "winner_row": winner,
        "next_if_pass": "adversarial-lite (placebo FIN intensity / crisis-mask scramble + year-split); then one held-out",
        "next_if_stop": "keep BASE; do not retune L1/L2/L3 or FIN_CAP_50; Soft-Frozen unchanged",
    }

    (OUT / "reports" / "l4_oof_summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n"
    )
    (RESEARCH / "MDD_L4_OOF_SUMMARY.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n"
    )

    flat = []
    for r in scored:
        item = {k: v for k, v in r.items() if k not in {"params", "fail_reasons"}}
        item["params_json"] = json.dumps(r.get("params") or {})
        item["fail_reasons"] = ",".join(r.get("fail_reasons") or [])
        flat.append(item)
    pd.DataFrame(flat).to_csv(OUT / "outputs" / "l4_oof_candidates.csv", index=False)

    lines = [
        "# L4 MDD Path/FINCAP — OOF Screen",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        "Status: **RESEARCH_ONLY** — no live-wire, no Soft-Frozen edit, no held-out selection.",
        "Parents: L1/L2/L3 STOPPED — cut retune forbidden.",
        "",
        f"## Decision: `{decision}`",
        "",
        f"- Locked winner: **{locked or 'NONE'}**",
        f"- OOF: `{OOF_START}` → `{OOF_END}`",
        f"- Late-bull proxy: `{LATE_BULL_START}` → `{LATE_BULL_END}`",
        (
            f"- Gates: Exact T+1; MDD ≥**{MDD_IMPROVE_MIN*100:.1f}pp**; "
            f"CAGR giveback ≤**{CAGR_GIVEBACK_MAX*100:.1f}pp**; "
            f"late-bull CAGR giveback ≤**{LATE_BULL_CAGR_GIVEBACK_MAX*100:.1f}pp**"
        ),
        "- Selection: **util = MDD_improve_pp − 0.5×late_bull_gb** (no harsh-cap family priority)",
        f"- Passers: **{len(passers)}** → {', '.join(p['id'] for p in passers) or '(none)'}",
        "",
        (
            f"BASE OOF: CAGR={base_row['oof_cagr']:.4%} MDD={base_row['oof_mdd']:.4%} "
            f"exact_t1={base_row['exact_t1_ok']} mean_fin_w={base_row['mean_fin_w_oof']:.1%}"
        ),
        "",
        "| ID | Family | MDD Δpp | CAGR gb pp | Late-bull gb pp | Util | Fin w | Exact T+1 | PASS | Fail |",
        "|---|---|---:|---:|---:|---:|---:|---|---|---|",
    ]
    for r in sorted(
        scored,
        key=lambda x: (0 if x.get("is_baseline") else 1, -(x.get("util") or -1e9), x["id"]),
    ):
        fail = ",".join(r.get("fail_reasons") or []) or "—"
        if r.get("is_baseline"):
            pass_cell = "—"
        else:
            pass_cell = "Y" if r.get("pass_oof") else ""
        lines.append(
            f"| {r['id']} | {r['family']} | {r['mdd_improve_pp']:+.2f} | "
            f"{r['cagr_giveback_pp']:+.2f} | {r['late_bull_cagr_giveback_pp']:+.2f} | "
            f"{r.get('util', 0):+.2f} | {r['mean_fin_w_oof']:.1%} | {r['exact_t1_ok']} | "
            f"{pass_cell} | {fail} |"
        )

    lines += ["", "## Aftermath", ""]
    if winner:
        lines += [
            f"- Proceed to **adversarial-lite** on locked `{locked}` "
            f"(util={winner['util']:.2f}; MDD {winner['mdd_improve_pp']:+.2f}pp; "
            f"late-bull gb {winner['late_bull_cagr_giveback_pp']:+.2f}pp).",
            "- Do **not** open held-out until adv-lite PASS.",
            "- Do **not** live-wire. Soft-Frozen stays **[0.50, 0.95]**.",
        ]
    else:
        lines += [
            "- **STOP OOF** — no lockable L4 passer under sealed-aware gates.",
            "- Keep BASE. Do not retune L1/L2/L3 or FIN_CAP_50.",
            "- Soft-Frozen stays **[0.50, 0.95]**.",
        ]
    lines += [
        "",
        "Artifacts:",
        f"- `{OUT / 'reports/l4_oof_summary.json'}`",
        f"- `{OUT / 'outputs/l4_oof_candidates.csv'}`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "MDD_L4_OOF.md").write_text(md)
    (RESEARCH / "MDD_L4_OOF.md").write_text(md)
    print(json.dumps({"label": decision, "locked": locked, "n_passers": len(passers)}, indent=2))


if __name__ == "__main__":
    main()
