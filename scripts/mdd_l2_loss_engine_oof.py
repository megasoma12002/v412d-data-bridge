#!/usr/bin/env python3
"""L2 MDD loss-engine Exact T+1 OOF screen (RESEARCH_ONLY).

Charter: research/gaps/MDD_L2_LOSS_ENGINE_CHARTER.md
L1 cut retune forbidden.

Frozen candidates (do not edit after first OOF peek):
  BASE, L2_FINCAP_ONLY, L2_DD_PATH_*, L2_SPIKE_SHORT_*, L2_ASYM_*, L2_FINCAP_DD_*

OOF: 2012-12-04 .. 2018-12-31
Pass: Exact T+1
  AND MDD improve >= 3.0pp
  AND CAGR giveback <= 2.5pp
  AND bull-day CAGR giveback <= 1.5pp
  AND bull-day flag share <= 20%
No live-wire. Held-out not used for selection.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from e50_early_stack_combined_nav import e16_features, nav_stats, simulate_core
import e22_dividend_accounting as e22div
import mdd_l1_loss_engine_oof as oof

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/mdd-loss-engine/l2_oof"
RESEARCH = ROOT / "research/gaps"

OOF_START, OOF_END = date(2012, 12, 4), date(2018, 12, 31)
MDD_IMPROVE_MIN = 0.03
CAGR_GIVEBACK_MAX = 0.025
BULL_CAGR_GIVEBACK_MAX = 0.015
BULL_FLAG_SHARE_MAX = 0.20

# Predeclared — freeze after first OOF peek
CANDIDATES: list[dict] = [
    {"id": "BASE", "family": "BASE", "fin_cap": False, "mode": "NONE", "params": {}},
    {"id": "L2_FINCAP_ONLY", "family": "L2-FINCAP-ONLY", "fin_cap": True, "mode": "NONE", "params": {}},
    {"id": "L2_DD_PATH_08_70", "family": "L2-DD-PATH", "fin_cap": False, "mode": "DD_PATH",
     "params": {"dd_thr": -0.08, "scale": 0.70}},
    {"id": "L2_DD_PATH_08_50", "family": "L2-DD-PATH", "fin_cap": False, "mode": "DD_PATH",
     "params": {"dd_thr": -0.08, "scale": 0.50}},
    {"id": "L2_DD_PATH_10_50", "family": "L2-DD-PATH", "fin_cap": False, "mode": "DD_PATH",
     "params": {"dd_thr": -0.10, "scale": 0.50}},
    {"id": "L2_DD_PATH_05_70", "family": "L2-DD-PATH", "fin_cap": False, "mode": "DD_PATH",
     "params": {"dd_thr": -0.05, "scale": 0.70}},
    {"id": "L2_SPIKE_SHORT_90_3_70", "family": "L2-SPIKE-SHORT", "fin_cap": False, "mode": "SPIKE_SHORT",
     "params": {"vol_pctl": 0.90, "hold_days": 3, "scale": 0.70}},
    {"id": "L2_SPIKE_SHORT_90_5_50", "family": "L2-SPIKE-SHORT", "fin_cap": False, "mode": "SPIKE_SHORT",
     "params": {"vol_pctl": 0.90, "hold_days": 5, "scale": 0.50}},
    {"id": "L2_ASYM_CRISIS_DD_50_5", "family": "L2-ASYM-SCALE", "fin_cap": False, "mode": "ASYM",
     "params": {"scale": 0.50, "clear_days": 5}},
    {"id": "L2_ASYM_CRISIS_DD_50_10", "family": "L2-ASYM-SCALE", "fin_cap": False, "mode": "ASYM",
     "params": {"scale": 0.50, "clear_days": 10}},
    {"id": "L2_FINCAP_DD_08_70", "family": "L2-FINCAP+DD", "fin_cap": True, "mode": "DD_PATH",
     "params": {"dd_thr": -0.08, "scale": 0.70}},
    {"id": "L2_FINCAP_DD_10_50", "family": "L2-FINCAP+DD", "fin_cap": True, "mode": "DD_PATH",
     "params": {"dd_thr": -0.10, "scale": 0.50}},
]

FAMILY_PRIORITY = {
    "L2-FINCAP-ONLY": 0,
    "L2-DD-PATH": 1,
    "L2-FINCAP+DD": 2,
    "L2-SPIKE-SHORT": 3,
    "L2-ASYM-SCALE": 4,
}


def taiex_dd_from_peak(prices: pd.DataFrame, win: int = 252) -> pd.Series:
    tc = prices["TAIEX"].astype(float)
    peak = tc.rolling(win, min_periods=60).max()
    return tc / peak - 1.0


def vol_pctl_60_252(prices: pd.DataFrame) -> pd.Series:
    tc = prices["TAIEX"].astype(float)
    ret = tc.pct_change()
    vol60 = ret.rolling(60, min_periods=40).std() * np.sqrt(252)
    return vol60.rolling(252, min_periods=120).apply(
        lambda x: pd.Series(x).rank(pct=True).iloc[-1], raw=False
    )


def build_flag(mode: str, params: dict, prices: pd.DataFrame, regime: pd.Series) -> pd.Series:
    idx = prices.index
    if mode == "NONE":
        return pd.Series(False, index=idx)

    if mode == "DD_PATH":
        dd = taiex_dd_from_peak(prices)
        return (dd <= float(params["dd_thr"])).fillna(False)

    if mode == "SPIKE_SHORT":
        vp = vol_pctl_60_252(prices)
        raw = (vp >= float(params["vol_pctl"])).fillna(False).to_numpy()
        hold = int(params["hold_days"])
        on = np.zeros(len(raw), dtype=bool)
        left = 0
        for i, hit in enumerate(raw):
            if hit:
                left = hold
            if left > 0:
                on[i] = True
                left -= 1
        return pd.Series(on, index=idx)

    if mode == "ASYM":
        dd = taiex_dd_from_peak(prices)
        crisis = (regime.astype(str) == "Crisis").reindex(idx).fillna(False)
        raw = (crisis | (dd <= -0.10)).fillna(False).to_numpy()
        clear_need = int(params["clear_days"])
        on = np.zeros(len(raw), dtype=bool)
        state = False
        clear = 0
        for i, hit in enumerate(raw):
            if hit:
                state = True
                clear = 0
            elif state:
                clear += 1
                if clear >= clear_need:
                    state = False
                    clear = 0
            on[i] = state
        return pd.Series(on, index=idx)

    raise ValueError(f"unknown mode {mode}")


def bull_day_metrics(
    nav_base: pd.DataFrame,
    nav_cand: pd.DataFrame,
    regime: pd.Series,
    flag: pd.Series,
    start: date,
    end: date,
) -> dict:
    rb = nav_base.copy()
    rc = nav_cand.copy()
    rb["date"] = pd.to_datetime(rb["date"])
    rc["date"] = pd.to_datetime(rc["date"])
    rb = rb[(rb["date"].dt.date >= start) & (rb["date"].dt.date <= end)].copy()
    rc = rc[(rc["date"].dt.date >= start) & (rc["date"].dt.date <= end)].copy()
    rb["ret"] = rb["nav"].pct_change()
    rc["ret"] = rc["nav"].pct_change()

    rmap = {pd.Timestamp(i).normalize(): str(v) for i, v in regime.items()}
    fmap = {pd.Timestamp(i).normalize(): bool(v) for i, v in flag.items()}
    cmap = {pd.Timestamp(d).normalize(): r for d, r in zip(rc["date"], rc["ret"])}

    rb["regime"] = rb["date"].dt.normalize().map(lambda x: rmap.get(x, "Sideways"))
    rb["flag"] = rb["date"].dt.normalize().map(lambda x: fmap.get(x, False))
    bull = rb[rb["regime"] == "Bull"].copy()
    rets_b = bull["ret"].to_numpy()
    rets_c = np.array([cmap.get(pd.Timestamp(d).normalize(), np.nan) for d in bull["date"]])
    flags = bull["flag"].to_numpy()
    mask = np.isfinite(rets_b) & np.isfinite(rets_c)
    rets_b, rets_c, flags = rets_b[mask], rets_c[mask], flags[mask]
    n = int(len(rets_b))
    if n < 20:
        return {
            "n_bull_days": n,
            "bull_ann_base": None,
            "bull_ann_cand": None,
            "bull_cagr_giveback_pp": None,
            "bull_flag_share": float(flags.mean()) if len(flags) else 0.0,
        }
    cum_b = float(np.prod(1.0 + rets_b) - 1.0)
    cum_c = float(np.prod(1.0 + rets_c) - 1.0)
    ann_b = float((1.0 + cum_b) ** (252.0 / n) - 1.0)
    ann_c = float((1.0 + cum_c) ** (252.0 / n) - 1.0)
    return {
        "n_bull_days": n,
        "bull_ann_base": ann_b,
        "bull_ann_cand": ann_c,
        "bull_cagr_giveback_pp": (ann_b - ann_c) * 100.0,
        "bull_flag_share": float(flags.mean()),
    }


def main() -> None:
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)

    print("loading market + BASE/FINCAP targets ...", flush=True)
    market = oof.load_market()
    dividends = (
        pd.read_csv(oof.DIV_PATH, dtype={"code": str}) if oof.DIV_PATH.exists() else pd.DataFrame()
    )
    prices, _s, base_target, base_regime = e16_features(market)
    _p, _s2, fin50_target, fin50_regime = oof.e16_features_fin_cap(market, 0.35, 0.50)

    rows: list[dict] = []
    navs: dict[str, pd.DataFrame] = {}
    flags_by_id: dict[str, pd.Series] = {}

    for cand in CANDIDATES:
        cid = cand["id"]
        print(f"simulating {cid} ...", flush=True)
        target = fin50_target if cand["fin_cap"] else base_target
        regime = fin50_regime if cand["fin_cap"] else base_regime
        flag = build_flag(cand["mode"], cand["params"], prices, base_regime)
        flags_by_id[cid] = flag
        if cand["mode"] == "NONE":
            exposure = None
        else:
            exposure = oof.exposure_from_flag(flag, float(cand["params"]["scale"]))

        nav, fills, meta = simulate_core(
            market,
            target,
            regime,
            dividends,
            apply_e22=True,
            e22_version=e22div.E22_V2S,
            apply_stock_div=True,
            e45_exposure=exposure,
        )
        navs[cid] = nav
        nav.to_csv(OUT / "outputs" / f"{cid.lower()}_daily_nav.csv", index=False)
        if cid in {"BASE", "L2_FINCAP_ONLY", "L2_DD_PATH_08_50", "L2_FINCAP_DD_10_50"}:
            fills.to_csv(OUT / "outputs" / f"{cid.lower()}_fills.csv", index=False)

        oof_stats = oof.window_nav_stats(nav, OOF_START, OOF_END)
        full = nav_stats(nav)
        mean_scale = (
            float(nav["e45_equity_scale"].mean()) if "e45_equity_scale" in nav.columns else 1.0
        )
        rows.append(
            {
                "id": cid,
                "family": cand["family"],
                "fin_cap": cand["fin_cap"],
                "mode": cand["mode"],
                "params": cand["params"],
                "exact_t1_ok": bool(meta.get("exact_t1_ok")),
                "same_bar_fills": int(meta.get("same_bar_fills", -1)),
                "oof_cagr": oof_stats.get("cagr"),
                "oof_mdd": oof_stats.get("max_drawdown"),
                "oof_n_days": oof_stats.get("n_days"),
                "full_cagr": full.get("cagr"),
                "full_mdd": full.get("max_drawdown"),
                "mean_e45_equity_scale": mean_scale,
                "oof_flag_share": float(oof.flag_coverage(flag, OOF_START, OOF_END)),
                "n_fills": meta.get("n_fills"),
            }
        )
        print(
            f"  {cid}: OOF CAGR={oof_stats.get('cagr')} MDD={oof_stats.get('max_drawdown')} "
            f"flag_share={rows[-1]['oof_flag_share']:.3f}",
            flush=True,
        )

    base_nav = navs["BASE"]
    base_row = next(r for r in rows if r["id"] == "BASE")
    for r in rows:
        bull = bull_day_metrics(
            base_nav, navs[r["id"]], base_regime, flags_by_id[r["id"]], OOF_START, OOF_END
        )
        r.update(bull)

    scored: list[dict] = []
    for r in rows:
        if r["id"] == "BASE":
            scored.append(
                {
                    **r,
                    "mdd_improve_pp": 0.0,
                    "cagr_giveback_pp": 0.0,
                    "pass_oof": False,
                    "is_baseline": True,
                    "fail_reasons": [],
                }
            )
            continue
        mdd_improve = abs(base_row["oof_mdd"] or 9) - abs(r["oof_mdd"] or 9)
        cagr_gb = (base_row["oof_cagr"] or 0) - (r["oof_cagr"] or 0)
        bull_gb = r.get("bull_cagr_giveback_pp")
        bull_share = r.get("bull_flag_share")
        reasons: list[str] = []
        if not r["exact_t1_ok"]:
            reasons.append("exact_t1")
        if r["oof_mdd"] is None or mdd_improve < MDD_IMPROVE_MIN:
            reasons.append("mdd_improve")
        if r["oof_cagr"] is None or cagr_gb > CAGR_GIVEBACK_MAX:
            reasons.append("cagr_giveback")
        if bull_gb is None or bull_gb > BULL_CAGR_GIVEBACK_MAX * 100.0:
            reasons.append("bull_cagr_giveback")
        if bull_share is None or bull_share > BULL_FLAG_SHARE_MAX:
            reasons.append("bull_flag_share")
        scored.append(
            {
                **r,
                "mdd_improve_pp": mdd_improve * 100.0,
                "cagr_giveback_pp": cagr_gb * 100.0,
                "pass_oof": len(reasons) == 0,
                "is_baseline": False,
                "fail_reasons": reasons,
                "base_oof_cagr": base_row["oof_cagr"],
                "base_oof_mdd": base_row["oof_mdd"],
            }
        )

    passers = [r for r in scored if r.get("pass_oof")]
    winner = None
    if passers:
        winner = sorted(
            passers,
            key=lambda x: (
                FAMILY_PRIORITY.get(x["family"], 9),
                -x["mdd_improve_pp"],
                x["cagr_giveback_pp"],
                x.get("bull_cagr_giveback_pp") or 9,
                x["id"],
            ),
        )[0]

    decision = "OOF_L2_READY_FOR_ADV_LITE" if winner else "STOP_L2_OOF_NO_PASSER"
    locked = winner["id"] if winner else None

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": decision,
        "live_wire": False,
        "research_only": True,
        "retune_allowed": False,
        "l1_retune_forbidden": True,
        "oof_window": {"start": str(OOF_START), "end": str(OOF_END)},
        "gates": {
            "mdd_improve_pp_min": MDD_IMPROVE_MIN * 100,
            "cagr_giveback_pp_max": CAGR_GIVEBACK_MAX * 100,
            "bull_cagr_giveback_pp_max": BULL_CAGR_GIVEBACK_MAX * 100,
            "bull_flag_share_max": BULL_FLAG_SHARE_MAX,
            "exact_t1": True,
        },
        "base": {
            "oof_cagr": base_row["oof_cagr"],
            "oof_mdd": base_row["oof_mdd"],
            "exact_t1_ok": base_row["exact_t1_ok"],
        },
        "candidates": scored,
        "n_passers": len(passers),
        "locked_winner": locked,
        "winner_row": winner,
        "next_if_pass": "adversarial-lite (placebo + bull-day check); then one held-out",
        "next_if_stop": "keep BASE; do not retune L2 cuts; new charter required",
    }

    (OUT / "reports" / "l2_oof_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (RESEARCH / "MDD_L2_OOF_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n")

    flat = []
    for r in scored:
        item = {k: v for k, v in r.items() if k not in {"params", "fail_reasons"}}
        item["params_json"] = json.dumps(r.get("params") or {})
        item["fail_reasons"] = ",".join(r.get("fail_reasons") or [])
        flat.append(item)
    pd.DataFrame(flat).to_csv(OUT / "outputs" / "l2_oof_candidates.csv", index=False)

    lines = [
        "# L2 MDD Loss-Engine — OOF Screen",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        "Status: **RESEARCH_ONLY** — no live-wire, no Soft-Frozen edit, no held-out selection.",
        "Parent: L1 STOPPED — L1 cut retune forbidden.",
        "",
        f"## Decision: `{decision}`",
        "",
        f"- Locked winner: **{locked or 'NONE'}**",
        f"- OOF: `{OOF_START}` → `{OOF_END}`",
        (
            f"- Gates: Exact T+1; MDD ≥**{MDD_IMPROVE_MIN*100:.1f}pp**; "
            f"CAGR giveback ≤**{CAGR_GIVEBACK_MAX*100:.1f}pp**; "
            f"bull CAGR giveback ≤**{BULL_CAGR_GIVEBACK_MAX*100:.1f}pp**; "
            f"bull flag share ≤**{BULL_FLAG_SHARE_MAX:.0%}**"
        ),
        "",
        f"BASE OOF: CAGR={base_row['oof_cagr']:.4%} MDD={base_row['oof_mdd']:.4%} exact_t1={base_row['exact_t1_ok']}",
        "",
        "| ID | Family | MDD Δpp | CAGR gb pp | Bull gb pp | Bull flag | Exact T+1 | PASS | Fail |",
        "|---|---|---:|---:|---:|---:|---|---|---|",
    ]
    for r in scored:
        bg = r.get("bull_cagr_giveback_pp")
        bg_s = f"{bg:+.2f}" if bg is not None else "nan"
        lines.append(
            f"| {r['id']} | {r['family']} | {r.get('mdd_improve_pp', 0):+.2f} | "
            f"{r.get('cagr_giveback_pp', 0):+.2f} | {bg_s} | "
            f"{(r.get('bull_flag_share') or 0):.1%} | {r['exact_t1_ok']} | "
            f"{'Y' if r.get('pass_oof') else '—'} | {','.join(r.get('fail_reasons') or []) or '—'} |"
        )
    lines += ["", "## Aftermath", ""]
    if winner:
        lines += [
            f"- Proceed to **adversarial-lite** on locked `{locked}`.",
            "- Do **not** open held-out until adv-lite PASS.",
            "- Do **not** live-wire.",
        ]
    else:
        lines += [
            "- **STOP** this L2 cut grid — no passer under sealed-aware OOF gates.",
            "- Keep BASE / Track A / FIN_CAP_50 paper monitor.",
            "- New charter required (no silent cut retune).",
        ]
    lines += [
        "",
        "Artifacts:",
        f"- `{OUT / 'reports' / 'l2_oof_summary.json'}`",
        f"- `{OUT / 'outputs' / 'l2_oof_candidates.csv'}`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "MDD_L2_OOF.md").write_text(md)
    (RESEARCH / "MDD_L2_OOF.md").write_text(md)
    print(json.dumps({"decision": decision, "locked": locked, "n_passers": len(passers)}, indent=2))
    print("EXIT:0")


if __name__ == "__main__":
    main()
