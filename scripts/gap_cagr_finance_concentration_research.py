#!/usr/bin/env python3
"""Research probe: CAGR/MDD gap vs targets + E16 finance concentration.

Read-only vs live. Writes under repro/gap-cagr-finance-concentration/.
Does not modify Soft-Frozen rules or forward/e21 ledgers.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from e21_forward_pipeline import features  # noqa: E402

OUT = ROOT / "repro/gap-cagr-finance-concentration"
FIN = {"2880", "2886", "2892", "5880"}
TEL = {"2412", "3045", "4904"}


def live_sleeve_weights(state_path: Path, market_path: Path) -> dict:
    ps = json.loads(state_path.read_text())
    m = pd.read_csv(market_path, dtype={"code": str})
    last = m["date"].max()
    px = dict(zip(m.loc[m["date"] == last, "code"], m.loc[m["date"] == last, "close"].astype(float)))
    rows = []
    total = float(ps["cash"])
    for code, sh in ps["positions"].items():
        mv = float(px[code]) * float(sh)
        sleeve = (
            "Financial"
            if code in FIN
            else "Telecom"
            if code in TEL
            else "0050"
            if code == "0050"
            else "Other"
        )
        rows.append({"code": code, "shares": sh, "px": float(px[code]), "mv": mv, "sleeve": sleeve})
        total += mv
    df = pd.DataFrame(rows)
    df["w"] = df["mv"] / total
    sleeve = df.groupby("sleeve")["w"].sum().to_dict()
    return {
        "asof": str(last),
        "nav": total,
        "cash_w": float(ps["cash"]) / total,
        "positions": df.to_dict(orient="records"),
        "sleeve_weights": sleeve,
    }


def e16_weight_stats(market_path: Path) -> tuple[dict, pd.DataFrame]:
    m = pd.read_csv(market_path, dtype={"code": str})
    _, sleeve, target, _, _ = features(m)
    t = target.dropna()
    fin = t["Financial"]
    nav_fin = (1 + sleeve["Financial"]).cumprod()
    fin2 = fin.reindex(sleeve.index).dropna()
    dd = nav_fin.reindex(fin2.index) / nav_fin.reindex(fin2.index).cummax() - 1
    sm = dd <= -0.10
    rc = sleeve.loc[t.index].corr()
    stats = {
        "n_days": int(len(t)),
        "start": str(pd.Timestamp(t.index.min()).date()),
        "end": str(pd.Timestamp(t.index.max()).date()),
        "financial": {
            "mean": float(fin.mean()),
            "median": float(fin.median()),
            "p10": float(fin.quantile(0.10)),
            "p25": float(fin.quantile(0.25)),
            "p75": float(fin.quantile(0.75)),
            "p90": float(fin.quantile(0.90)),
            "min": float(fin.min()),
            "max": float(fin.max()),
            "pct_ge_070": float((fin >= 0.70).mean()),
            "pct_ge_080": float((fin >= 0.80).mean()),
            "pct_ge_085": float((fin >= 0.85).mean()),
            "hard_clip": [0.50, 0.95],
            "bull_prior": 0.85,
            "crisis_prior": 0.60,
        },
        "telecom": {
            "mean": float(t["Telecom"].mean()),
            "median": float(t["Telecom"].median()),
            "min": float(t["Telecom"].min()),
            "max": float(t["Telecom"].max()),
        },
        "etf_0050": {
            "mean": float(t["0050"].mean()),
            "median": float(t["0050"].median()),
            "min": float(t["0050"].min()),
            "max": float(t["0050"].max()),
        },
        "sleeve_return_corr": {
            "Financial_Telecom": float(rc.loc["Financial", "Telecom"]),
            "Financial_0050": float(rc.loc["Financial", "0050"]),
            "Telecom_0050": float(rc.loc["Telecom", "0050"]),
        },
        "during_fin_dd_le_10pct": {
            "n_days": int(sm.sum()),
            "mean_financial_w": float(fin2[sm].mean()),
            "mean_telecom_w": float(t["Telecom"].reindex(fin2.index)[sm].mean()),
            "mean_0050_w": float(t["0050"].reindex(fin2.index)[sm].mean()),
        },
    }
    return stats, t


def gap_table() -> list[dict]:
    # Numbers from repro/e22-v2s-historical-recompute/summary.json (2012-12-04→2026-09-04)
    # and repro/gap5-6-continuation/outputs/paper_combined_mix_summary.csv
    rows = [
        {"book": "E16_E18_NO_DIV", "cagr": 0.0729, "mdd": -0.2277, "live_path": True},
        {"book": "E22_v2_cash", "cagr": 0.1125, "mdd": -0.2211, "live_path": False},
        {"book": "E22_v2s_formal", "cagr": 0.1378, "mdd": -0.2264, "live_path": True},
        {
            "book": "PAPER_CORE80_OVL20_stitch",
            "cagr": 0.204273,
            "mdd": -0.239566,
            "live_path": False,
            "note": "research stitch; overlay not live-eligible",
        },
    ]
    for r in rows:
        r["cagr_gap_to_20_pp"] = round((0.20 - r["cagr"]) * 100, 2)
        r["mdd_depth_beyond_15_pp"] = round((abs(r["mdd"]) - 0.15) * 100, 2)
        r["cagr_meets_20"] = r["cagr"] >= 0.20
        r["mdd_meets_15"] = abs(r["mdd"]) <= 0.15
    return rows


def main() -> None:
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    market = ROOT / "forward/e21/live_market.csv"
    state = ROOT / "forward/e21/portfolio_state.json"

    live = live_sleeve_weights(state, market)
    stats, series = e16_weight_stats(market)
    gaps = gap_table()

    series.to_csv(OUT / "outputs/e16_target_weights_daily.csv")
    (OUT / "outputs/live_sleeve_weights.json").write_text(json.dumps(live, indent=2) + "\n")
    (OUT / "outputs/e16_weight_concentration_stats.json").write_text(json.dumps(stats, indent=2) + "\n")
    (OUT / "outputs/cagr_mdd_gap_vs_targets.json").write_text(json.dumps(gaps, indent=2) + "\n")

    summary = {
        "generated_note": "RESEARCH_ONLY",
        "live_wire": False,
        "targets": {"cagr_ge": 0.20, "mdd_abs_le": 0.15},
        "live_sleeve_weights": live["sleeve_weights"],
        "live_asof": live["asof"],
        "e16_financial_mean": stats["financial"]["mean"],
        "e16_financial_pct_ge_070": stats["financial"]["pct_ge_070"],
        "formal_core_cagr": 0.1378,
        "formal_core_mdd": -0.2264,
        "verdict": (
            "Core cannot hit CAGR≥20% and MDD≤15% together; "
            "E16 finance concentration is structural (clip+priors), not a one-off."
        ),
        "gaps": gaps,
        "concentration": stats,
    }
    (OUT / "reports/summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"asof": live["asof"], "live_fin_w": live["sleeve_weights"].get("Financial"),
                      "e16_fin_mean": stats["financial"]["mean"],
                      "formal_cagr": 0.1378, "formal_mdd": -0.2264}, indent=2))


if __name__ == "__main__":
    main()
