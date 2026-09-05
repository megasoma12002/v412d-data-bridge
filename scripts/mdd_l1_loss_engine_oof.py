#!/usr/bin/env python3
"""L1 MDD loss-engine Exact T+1 OOF screen (RESEARCH_ONLY).

Frozen before peeking held-out (charter: research/gaps/MDD_LOSS_ENGINE_CHARTER.md):
  BASE: E16 + E18 Exact T+1 + E22_v2s (e45 scale=1)
  L1-CRISIS-EQ: equity scale on E16 Crisis regime days
  L1-STRESS-DET: equity scale on vol/DD/combo stress flags (!= Crisis alone)
  L1-FINCAP-STACK: FIN_CAP_50 targets + crisis/combo scale
  L1-GROSS-FLOOR: hard equity scale under combo flag

OOF window: 2012-12-04 .. 2018-12-31
Pass: Exact T+1 AND MDD improve >=3.0pp vs BASE AND CAGR giveback <=2.5pp
No live-wire. No cut retune after this peek. Held-out not used for selection.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from e50_early_stack_combined_nav import ALL, FIN, TEL, e16_features, nav_stats, simulate_core
import e22_dividend_accounting as e22div

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/mdd-loss-engine/l1_oof"
RESEARCH = ROOT / "research/gaps"
MARKET_PATH = ROOT / "forward/e21/live_market.csv"
DIV_PATH = ROOT / "data/dividend_events/e22_dividend_events.csv"

OOF_START, OOF_END = date(2012, 12, 4), date(2018, 12, 31)
COVID_PEAK, COVID_TROUGH = date(2020, 1, 20), date(2020, 3, 19)

MDD_IMPROVE_MIN = 0.03
CAGR_GIVEBACK_MAX = 0.025

# Predeclared challengers — do not edit after first OOF peek
CANDIDATES: list[dict] = [
    {"id": "BASE", "family": "BASE", "fin_lo": 0.50, "fin_hi": 0.95, "flag": "NONE", "scale": 1.0},
    {"id": "L1_CRISIS_EQ_70", "family": "L1-CRISIS-EQ", "fin_lo": 0.50, "fin_hi": 0.95, "flag": "CRISIS", "scale": 0.70},
    {"id": "L1_CRISIS_EQ_50", "family": "L1-CRISIS-EQ", "fin_lo": 0.50, "fin_hi": 0.95, "flag": "CRISIS", "scale": 0.50},
    {"id": "L1_CRISIS_EQ_30", "family": "L1-CRISIS-EQ", "fin_lo": 0.50, "fin_hi": 0.95, "flag": "CRISIS", "scale": 0.30},
    {"id": "L1_STRESS_VOL80_50", "family": "L1-STRESS-DET", "fin_lo": 0.50, "fin_hi": 0.95, "flag": "VOL80", "scale": 0.50},
    {"id": "L1_STRESS_DD10_50", "family": "L1-STRESS-DET", "fin_lo": 0.50, "fin_hi": 0.95, "flag": "DD10", "scale": 0.50},
    {"id": "L1_STRESS_COMBO_70", "family": "L1-STRESS-DET", "fin_lo": 0.50, "fin_hi": 0.95, "flag": "COMBO", "scale": 0.70},
    {"id": "L1_STRESS_COMBO_50", "family": "L1-STRESS-DET", "fin_lo": 0.50, "fin_hi": 0.95, "flag": "COMBO", "scale": 0.50},
    {"id": "L1_STRESS_COMBO_30", "family": "L1-STRESS-DET", "fin_lo": 0.50, "fin_hi": 0.95, "flag": "COMBO", "scale": 0.30},
    {"id": "L1_GROSS_FLOOR_60_COMBO", "family": "L1-GROSS-FLOOR", "fin_lo": 0.50, "fin_hi": 0.95, "flag": "COMBO", "scale": 0.60},
    {"id": "L1_FINCAP50_CRISIS_50", "family": "L1-FINCAP-STACK", "fin_lo": 0.35, "fin_hi": 0.50, "flag": "CRISIS", "scale": 0.50},
    {"id": "L1_FINCAP50_COMBO_50", "family": "L1-FINCAP-STACK", "fin_lo": 0.35, "fin_hi": 0.50, "flag": "COMBO", "scale": 0.50},
]


def e16_features_fin_cap(market: pd.DataFrame, fin_lo: float, fin_hi: float):
    """Causal E16 router with Financial hard clip [fin_lo, fin_hi]; residual -> Telecom/0050."""
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


def build_stress_flags(prices: pd.DataFrame, regime: pd.Series) -> dict[str, pd.Series]:
    tc = prices["TAIEX"].astype(float)
    ret = tc.pct_change()
    vol60 = ret.rolling(60, min_periods=40).std() * np.sqrt(252)
    vol_pctl = vol60.rolling(252, min_periods=120).apply(
        lambda x: pd.Series(x).rank(pct=True).iloc[-1], raw=False
    )
    vol80 = (vol_pctl >= 0.80).fillna(False)
    peak252 = tc.rolling(252, min_periods=60).max()
    dd = tc / peak252 - 1.0
    dd10 = (dd <= -0.10).fillna(False)
    crisis = (regime.astype(str) == "Crisis").reindex(prices.index).fillna(False)
    combo = crisis | vol80 | dd10
    return {
        "NONE": pd.Series(False, index=prices.index),
        "CRISIS": crisis,
        "VOL80": vol80,
        "DD10": dd10,
        "COMBO": combo,
    }


def exposure_from_flag(flag: pd.Series, scale: float) -> pd.Series:
    return pd.Series(np.where(flag.to_numpy(), float(scale), 1.0), index=flag.index, name="exposure")


def window_nav_stats(nav: pd.DataFrame, start: date, end: date) -> dict:
    d = nav.copy()
    d["date"] = pd.to_datetime(d["date"]).dt.date
    g = d[(d["date"] >= start) & (d["date"] <= end)].reset_index(drop=True)
    if len(g) < 30:
        return {"cagr": None, "max_drawdown": None, "utility": None, "vol": None, "n_days": int(len(g))}
    g = g.copy()
    g["nav"] = g["nav"] / float(g["nav"].iloc[0])
    out = nav_stats(g)
    out["n_days"] = int(len(g))
    return out


def flag_coverage(flag: pd.Series, start: date, end: date) -> float:
    idx = pd.to_datetime(flag.index).date
    m = (idx >= start) & (idx <= end)
    sub = flag.loc[m]
    if len(sub) == 0:
        return 0.0
    return float(sub.mean())


def load_market() -> pd.DataFrame:
    market = pd.read_csv(MARKET_PATH, dtype={"code": str})
    market["date"] = pd.to_datetime(market["date"])
    required = set(ALL + ["TAIEX"])
    complete = market.groupby("date")["code"].apply(lambda s: required.issubset(set(s)))
    return market[market["date"].isin(complete[complete].index)].sort_values(["date", "code"])


def main() -> None:
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)

    print("loading market + dividends ...", flush=True)
    market = load_market()
    dividends = pd.read_csv(DIV_PATH, dtype={"code": str}) if DIV_PATH.exists() else pd.DataFrame()

    print("building BASE E16 features + stress flags ...", flush=True)
    prices, _sleeve, base_target, base_regime = e16_features(market)
    flags = build_stress_flags(prices, base_regime)

    print("building FIN_CAP_50 targets ...", flush=True)
    _p, _s, fin50_target, fin50_regime = e16_features_fin_cap(market, 0.35, 0.50)

    rows: list[dict] = []
    for cand in CANDIDATES:
        cid = cand["id"]
        print(f"simulating {cid} ...", flush=True)
        if cand["fin_lo"] == 0.50 and cand["fin_hi"] == 0.95:
            target, regime = base_target, base_regime
        else:
            target, regime = fin50_target, fin50_regime

        flag_series = flags[cand["flag"]]
        if cand["flag"] == "NONE" or cand["scale"] >= 1.0 - 1e-12:
            exposure = None
        else:
            exposure = exposure_from_flag(flag_series, cand["scale"])

        nav, fills, meta = simulate_core(
            market,
            target,
            regime,
            dividends,
            apply_e22=True,
            e22_version=e22div.E22_V2S,
            apply_stock_div=True,
            e45_exposure=exposure,
            e45_legacy_crisis_scale=None,
        )
        nav.to_csv(OUT / "outputs" / f"{cid.lower()}_daily_nav.csv", index=False)
        fills.to_csv(OUT / "outputs" / f"{cid.lower()}_fills.csv", index=False)

        oof = window_nav_stats(nav, OOF_START, OOF_END)
        full = nav_stats(nav)
        mean_scale = float(nav["e45_equity_scale"].mean()) if "e45_equity_scale" in nav.columns else 1.0
        row = {
            "id": cid,
            "family": cand["family"],
            "fin_lo": cand["fin_lo"],
            "fin_hi": cand["fin_hi"],
            "flag": cand["flag"],
            "scale": cand["scale"],
            "exact_t1_ok": bool(meta.get("exact_t1_ok")),
            "same_bar_fills": int(meta.get("same_bar_fills", -1)),
            "oof_cagr": oof.get("cagr"),
            "oof_mdd": oof.get("max_drawdown"),
            "oof_n_days": oof.get("n_days"),
            "full_cagr": full.get("cagr"),
            "full_mdd": full.get("max_drawdown"),
            "mean_e45_equity_scale": mean_scale,
            "oof_flag_day_share": flag_coverage(flag_series, OOF_START, OOF_END),
            "covid_flag_day_share_descriptive": flag_coverage(flag_series, COVID_PEAK, COVID_TROUGH),
            "n_fills": meta.get("n_fills"),
        }
        rows.append(row)
        print(
            f"  {cid}: OOF CAGR={oof.get('cagr')} MDD={oof.get('max_drawdown')} "
            f"exact_t1={row['exact_t1_ok']} covid_flag_share={row['covid_flag_day_share_descriptive']:.3f}",
            flush=True,
        )

    base = next(r for r in rows if r["id"] == "BASE")
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
                }
            )
            continue
        mdd_improve = abs(base["oof_mdd"] or 9) - abs(r["oof_mdd"] or 9)
        cagr_giveback = (base["oof_cagr"] or 0) - (r["oof_cagr"] or 0)
        pass_oof = bool(
            r["exact_t1_ok"]
            and r["oof_mdd"] is not None
            and r["oof_cagr"] is not None
            and mdd_improve >= MDD_IMPROVE_MIN
            and cagr_giveback <= CAGR_GIVEBACK_MAX
        )
        scored.append(
            {
                **r,
                "mdd_improve_pp": mdd_improve * 100.0,
                "cagr_giveback_pp": cagr_giveback * 100.0,
                "pass_oof": pass_oof,
                "is_baseline": False,
                "base_oof_cagr": base["oof_cagr"],
                "base_oof_mdd": base["oof_mdd"],
            }
        )

    passers = [r for r in scored if r.get("pass_oof")]
    winner = None
    if passers:
        winner = sorted(
            passers,
            key=lambda x: (-x["mdd_improve_pp"], x["cagr_giveback_pp"], x["id"]),
        )[0]

    decision = "OOF_L1_READY_FOR_ADV_LITE" if winner else "STOP_L1_OOF_NO_PASSER"
    locked = winner["id"] if winner else None

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": decision,
        "live_wire": False,
        "research_only": True,
        "retune_allowed": False,
        "oof_window": {"start": str(OOF_START), "end": str(OOF_END)},
        "gates": {
            "mdd_improve_pp_min": MDD_IMPROVE_MIN * 100,
            "cagr_giveback_pp_max": CAGR_GIVEBACK_MAX * 100,
            "exact_t1": True,
        },
        "base": {
            "oof_cagr": base["oof_cagr"],
            "oof_mdd": base["oof_mdd"],
            "exact_t1_ok": base["exact_t1_ok"],
        },
        "candidates": scored,
        "n_passers": len(passers),
        "locked_winner": locked,
        "winner_row": winner,
        "next_if_pass": "adversarial-lite (placebo flag scramble); only then one held-out",
        "next_if_stop": "keep BASE / Track A; do not retune L1 cuts; new charter required",
        "covid_coverage_note": "covid_flag_day_share is descriptive only (held-out calendar); not an OOF gate",
    }

    (OUT / "reports" / "l1_oof_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (RESEARCH / "MDD_L1_OOF_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n")
    pd.DataFrame(scored).to_csv(OUT / "outputs" / "l1_oof_candidates.csv", index=False)

    lines = [
        "# L1 MDD Loss-Engine — OOF Screen",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        "Status: **RESEARCH_ONLY** — no live-wire, no Soft-Frozen edit, no held-out selection.",
        "",
        f"## Decision: `{decision}`",
        "",
        f"- Locked winner: **{locked or 'NONE'}**",
        f"- OOF window: `{OOF_START}` → `{OOF_END}`",
        f"- Gates: Exact T+1; MDD improve ≥ **{MDD_IMPROVE_MIN*100:.1f} pp**; CAGR giveback ≤ **{CAGR_GIVEBACK_MAX*100:.1f} pp**",
        "",
        f"BASE OOF: CAGR={base['oof_cagr']:.4%} MDD={base['oof_mdd']:.4%} exact_t1={base['exact_t1_ok']}",
        "",
        "| ID | Family | Flag | Scale | OOF CAGR | OOF MDD | MDD Δpp | CAGR giveback pp | Exact T+1 | COVID flag share* | PASS |",
        "|---|---|---|---:|---:|---:|---:|---:|---|---:|---|",
    ]
    for r in scored:
        lines.append(
            f"| {r['id']} | {r['family']} | {r['flag']} | {r['scale']:.2f} | "
            f"{(r['oof_cagr'] or float('nan')):.2%} | {(r['oof_mdd'] or float('nan')):.2%} | "
            f"{r.get('mdd_improve_pp', 0):+.2f} | {r.get('cagr_giveback_pp', 0):+.2f} | "
            f"{r['exact_t1_ok']} | {r.get('covid_flag_day_share_descriptive', 0):.1%} | "
            f"{'Y' if r.get('pass_oof') else '—'} |"
        )
    lines += [
        "",
        "\\* COVID flag share is **descriptive only** (2020-01-20→03-19); not used for OOF pass.",
        "",
        "## Aftermath",
        "",
    ]
    if winner:
        lines += [
            f"- Proceed to **adversarial-lite** on locked `{locked}` (placebo flag scramble P&lt;0.50).",
            "- Do **not** open held-out until adv-lite PASS.",
            "- Do **not** live-wire; dual paper ledgers on any later promote.",
        ]
    else:
        lines += [
            "- **STOP** this L1 cut grid — no passer under frozen gates.",
            "- Keep BASE E22_v2s / Track A monitor.",
            "- New charter required for any further loss-engine family (no silent cut retune).",
        ]
    lines += [
        "",
        "Artifacts:",
        f"- `{OUT / 'reports' / 'l1_oof_summary.json'}`",
        f"- `{OUT / 'outputs' / 'l1_oof_candidates.csv'}`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "MDD_L1_OOF.md").write_text(md)
    (RESEARCH / "MDD_L1_OOF.md").write_text(md)
    print(json.dumps({"decision": decision, "locked": locked, "n_passers": len(passers)}, indent=2))
    print("EXIT:0")


if __name__ == "__main__":
    main()
