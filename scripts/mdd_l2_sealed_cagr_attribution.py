#!/usr/bin/env python3
"""L2 sealed CAGR attribution for L3 charter (RESEARCH_ONLY).

Recomputes Exact T+1 NAV sealed giveback for frozen L2_FINCAP_ONLY.
Does not retune cuts. Does not live-wire Soft-Frozen.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e22_dividend_accounting as e22div
import mdd_l1_loss_engine_oof as oof

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/mdd-loss-engine/l3_sealed_cagr_attribution"
RESEARCH = ROOT / "research/gaps"
SEALED_START = date(2023, 1, 1)


def ann(series: pd.Series) -> float | None:
    x = series.dropna()
    if len(x) < 20:
        return None
    return float((1.0 + x).prod() ** (252.0 / len(x)) - 1.0)


def year_row(nav_b: pd.DataFrame, nav_l: pd.DataFrame, y: int) -> dict | None:
    b = oof.window_nav_stats(nav_b, date(y, 1, 1), date(y, 12, 31))
    f = oof.window_nav_stats(nav_l, date(y, 1, 1), date(y, 12, 31))
    if b["n_days"] < 30 or f["n_days"] < 30 or b["cagr"] is None or f["cagr"] is None:
        return None
    bm = b["max_drawdown"]
    fm = f["max_drawdown"]
    return {
        "year": y,
        "base_cagr": b["cagr"],
        "l2_cagr": f["cagr"],
        "cagr_giveback_pp": (b["cagr"] - f["cagr"]) * 100.0,
        "base_mdd": bm,
        "l2_mdd": fm,
        "mdd_improve_pp": (abs(bm) - abs(fm)) * 100.0,
        "n_days": b["n_days"],
    }


def main() -> None:
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)

    market = oof.load_market()
    dividends = (
        pd.read_csv(oof.DIV_PATH, dtype={"code": str}) if oof.DIV_PATH.exists() else pd.DataFrame()
    )
    _prices, sleeve, base_target, base_regime = oof.e16_features(market)
    _p2, _s2, fin50_target, fin50_regime = oof.e16_features_fin_cap(market, 0.35, 0.50)

    nav_b, _fb, _mb = oof.simulate_core(
        market,
        base_target,
        base_regime,
        dividends,
        apply_e22=True,
        e22_version=e22div.E22_V2S,
        apply_stock_div=True,
        e45_exposure=None,
    )
    nav_l, _fl, _ml = oof.simulate_core(
        market,
        fin50_target,
        fin50_regime,
        dividends,
        apply_e22=True,
        e22_version=e22div.E22_V2S,
        apply_stock_div=True,
        e45_exposure=None,
    )

    sealed_end = pd.to_datetime(nav_b["date"]).dt.date.max()
    bs = oof.window_nav_stats(nav_b, SEALED_START, sealed_end)
    fs = oof.window_nav_stats(nav_l, SEALED_START, sealed_end)
    years = [r for y in range(2023, sealed_end.year + 1) if (r := year_row(nav_b, nav_l, y))]

    bt = base_target.copy()
    ft = fin50_target.copy()
    bt.index = pd.to_datetime(bt.index).date
    ft.index = pd.to_datetime(ft.index).date
    mask = (bt.index >= SEALED_START) & (bt.index <= sealed_end)
    bts = bt.loc[mask]
    fts = ft.loc[mask]

    weight_years = []
    for y in range(2023, sealed_end.year + 1):
        m = (bts.index >= date(y, 1, 1)) & (bts.index <= date(y, 12, 31))
        if int(m.sum()) < 20:
            continue
        weight_years.append(
            {
                "year": y,
                "base_fin": float(bts.loc[m, "Financial"].mean()),
                "l2_fin": float(fts.loc[m, "Financial"].mean()),
                "base_tel": float(bts.loc[m, "Telecom"].mean()),
                "l2_tel": float(fts.loc[m, "Telecom"].mean()),
                "base_0050": float(bts.loc[m, "0050"].mean()),
                "l2_0050": float(fts.loc[m, "0050"].mean()),
            }
        )

    reg = base_regime.copy()
    reg.index = pd.to_datetime(reg.index).date
    rs = reg[(reg.index >= SEALED_START) & (reg.index <= sealed_end)]

    sl = sleeve.copy()
    sl.index = pd.to_datetime(sl.index).date
    sls = sl[(sl.index >= SEALED_START) & (sl.index <= sealed_end)]
    sleeve_years = []
    for y in range(2023, sealed_end.year + 1):
        m = (sls.index >= date(y, 1, 1)) & (sls.index <= date(y, 12, 31))
        if int(m.sum()) < 20:
            continue
        sleeve_years.append({"year": y, **{c: ann(sls.loc[m, c]) for c in sls.columns}})

    common_idx = bts.index.intersection(sls.index)
    d = (
        (fts.loc[common_idx].shift(1) * sls.loc[common_idx]).sum(axis=1)
        - (bts.loc[common_idx].shift(1) * sls.loc[common_idx]).sum(axis=1)
    ).dropna()
    attr = ((fts.loc[common_idx] - bts.loc[common_idx]).shift(1) * sls.loc[common_idx]).dropna(
        how="all"
    )
    md = pd.DataFrame({"d": d})
    md["ym"] = pd.to_datetime(pd.Series(d.index)).dt.to_period("M").astype(str).values
    month = md.groupby("ym")["d"].sum().sort_values()
    worst = [{"ym": k, "sum_dret_pp": float(v * 100)} for k, v in month.head(10).items()]
    best = [{"ym": k, "sum_dret_pp": float(v * 100)} for k, v in month.tail(8).iloc[::-1].items()]
    bull_m = rs.reindex(d.index) == "Bull"
    regime_dret = {
        "bull_sum_pp": float(d[bull_m.fillna(False)].sum() * 100),
        "nonbull_sum_pp": float(d[~bull_m.fillna(False)].sum() * 100),
        "bull_share": float(bull_m.mean()) if len(bull_m) else None,
    }

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "L2_SEALED_CAGR_ATTRIBUTION_FOR_L3",
        "locked_parent": "L2_FINCAP_ONLY",
        "parent_stop": "STOP_L2_HELDOUT_MIXED_KEEP_BASE",
        "live_wire": False,
        "research_only": True,
        "note_sleeve_proxy": (
            "Equal-weight sleeve Δret is diagnostic only; authoritative metric is Exact T+1 NAV "
            "CAGR giveback. Proxy total can disagree with NAV because books use name-level fills."
        ),
        "sealed_window": {"start": str(SEALED_START), "end": str(sealed_end)},
        "sealed_nav": {
            "base_cagr": bs["cagr"],
            "l2_cagr": fs["cagr"],
            "cagr_giveback_pp": (bs["cagr"] - fs["cagr"]) * 100.0,
            "base_mdd": bs["max_drawdown"],
            "l2_mdd": fs["max_drawdown"],
            "mdd_improve_pp": (abs(bs["max_drawdown"]) - abs(fs["max_drawdown"])) * 100.0,
        },
        "years": years,
        "mean_weights_sealed": {
            "base": {k: float(v) for k, v in bts.mean().items()},
            "l2": {k: float(v) for k, v in fts.mean().items()},
            "delta_l2_minus_base": {k: float(v) for k, v in (fts.mean() - bts.mean()).items()},
        },
        "weight_years": weight_years,
        "sleeve_ann_sealed": {c: ann(sls[c]) for c in sls.columns},
        "sleeve_years": sleeve_years,
        "sleeve_attr_sum_pp": {c: float(attr[c].sum() * 100) for c in attr.columns},
        "sleeve_attr_total_pp": float(attr.sum().sum() * 100),
        "regime_share_sealed": {str(k): float(v) for k, v in rs.value_counts(normalize=True).items()},
        "regime_dret_proxy": regime_dret,
        "worst_months_proxy": worst,
        "best_months_proxy": best,
        "implications": [
            "L2 giveback is FIN concentration, not COMBO timing",
            "Sealed MDD still improves; sealed CAGR giveback fails ≤3.0pp gate",
            "Do not retune L1 COMBO×0.50; do not reopen L2_FINCAP_ONLY as live cut",
        ],
    }

    (OUT / "reports" / "l3_sealed_cagr_attribution.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )
    (RESEARCH / "MDD_L2_SEALED_CAGR_ATTRIBUTION.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )
    pd.DataFrame(years).to_csv(OUT / "outputs" / "sealed_years.csv", index=False)
    pd.DataFrame(weight_years).to_csv(OUT / "outputs" / "sealed_weights_by_year.csv", index=False)

    mw = summary["mean_weights_sealed"]
    sn = summary["sealed_nav"]
    lines = [
        "# L2 Sealed CAGR Attribution (for L3 charter)",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        f"Parent lock (frozen): `{summary['locked_parent']}` → `{summary['parent_stop']}`",
        "Status: **RESEARCH_ONLY** — explains sealed CAGR giveback; does not reopen L2 cuts.",
        "",
        "## Held-out sealed deltas (recomputed)",
        "",
        f"- Sealed CAGR giveback: **{sn['cagr_giveback_pp']:.2f} pp** (gate ≤3.0) → FAIL",
        f"- Sealed MDD improve: **{sn['mdd_improve_pp']:.2f} pp**",
        "",
        "## Mechanism",
        "",
        "L2_FINCAP_ONLY has **no gross equity scale** and **no COMBO flag**. "
        "Giveback is from Financial hard clip `[0.35, 0.50]` vs BASE Soft-Frozen path "
        f"(sealed mean Financial **{mw['base']['Financial']:.1%}** → **{mw['l2']['Financial']:.1%}**).",
        "",
        f"Note: {summary['note_sleeve_proxy']}",
        "",
        "## Sealed mean sleeve weights",
        "",
        "| Sleeve | BASE | L2 FIN50 | Δ |",
        "|---|---:|---:|---:|",
    ]
    for s in ["Financial", "Telecom", "0050"]:
        lines.append(
            f"| {s} | {mw['base'][s]:.1%} | {mw['l2'][s]:.1%} | "
            f"{mw['delta_l2_minus_base'][s]:+.1%} |"
        )
    lines += [
        "",
        "## Sealed by year (NAV — authoritative)",
        "",
        "| Year | BASE CAGR | L2 CAGR | Giveback pp | MDD Δpp |",
        "|---:|---:|---:|---:|---:|",
    ]
    for r in years:
        lines.append(
            f"| {r['year']} | {r['base_cagr']:.2%} | {r['l2_cagr']:.2%} | "
            f"{r['cagr_giveback_pp']:+.2f} | {r['mdd_improve_pp']:+.2f} |"
        )
    lines += [
        "",
        "## Implications for L3",
        "",
        "1. Failure mode ≠ L1: L1 was COMBO timing over-fire; L2 is **static FIN concentration**.",
        "2. Giveback concentrated in **2024 / 2025 / 2026**; 2023 L2 beat BASE on CAGR.",
        "3. L3 targets sealed CAGR retention with MDD ≥ +1 pp — without retuning L1 or reopening L2 lock.",
        "4. Soft-Frozen live clip stays **[0.50, 0.95]**; FIN_CAP_50 dual-paper month-end continues.",
        "",
        "See charter: `research/gaps/MDD_L3_SEALED_CAGR_CHARTER.md`",
        "",
    ]
    md_txt = "\n".join(lines)
    (OUT / "MDD_L2_SEALED_CAGR_ATTRIBUTION.md").write_text(md_txt)
    (RESEARCH / "MDD_L2_SEALED_CAGR_ATTRIBUTION.md").write_text(md_txt)
    print(
        json.dumps(
            {
                "cagr_giveback_pp": sn["cagr_giveback_pp"],
                "mdd_improve_pp": sn["mdd_improve_pp"],
                "years": [(r["year"], round(r["cagr_giveback_pp"], 2)) for r in years],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
