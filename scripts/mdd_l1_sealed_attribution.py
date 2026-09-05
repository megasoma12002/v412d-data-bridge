#!/usr/bin/env python3
"""L1 sealed-window failure attribution (RESEARCH_ONLY).

Replays BASE vs locked L1_FINCAP50_COMBO_50 and attributes the sealed
(2023+) CAGR giveback that caused STOP_L1_HELDOUT_MIXED.

No cut retune. No live-wire. Feeds L2 charter.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from e50_early_stack_combined_nav import e16_features, nav_stats, simulate_core
import e22_dividend_accounting as e22div
import mdd_l1_loss_engine_oof as oof

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/mdd-loss-engine/l1_sealed_attribution"
RESEARCH = ROOT / "research/gaps"

LOCKED_SCALE = 0.50
SEALED_START = date(2023, 1, 1)
VAL_START, VAL_END = date(2019, 1, 1), date(2022, 12, 31)
OOF_START, OOF_END = date(2012, 12, 4), date(2018, 12, 31)


def year_stats(nav: pd.DataFrame, year: int) -> dict:
    d = nav.copy()
    d["date"] = pd.to_datetime(d["date"])
    g = d[d["date"].dt.year == year].reset_index(drop=True)
    if len(g) < 20:
        return {"year": year, "cagr": None, "max_drawdown": None, "n_days": int(len(g))}
    g = g.copy()
    g["nav"] = g["nav"] / float(g["nav"].iloc[0])
    st = nav_stats(g)
    return {
        "year": year,
        "cagr": st.get("cagr"),
        "max_drawdown": st.get("max_drawdown"),
        "n_days": int(len(g)),
    }


def main() -> None:
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)

    print("loading + simulating BASE and L1 locked ...", flush=True)
    market = oof.load_market()
    dividends = (
        pd.read_csv(oof.DIV_PATH, dtype={"code": str}) if oof.DIV_PATH.exists() else pd.DataFrame()
    )
    prices, _s, base_target, base_regime = e16_features(market)
    _p, _s2, fin50_target, fin50_regime = oof.e16_features_fin_cap(market, 0.35, 0.50)
    flags = oof.build_stress_flags(prices, base_regime)
    combo = flags["COMBO"].astype(bool)
    crisis = flags["CRISIS"].astype(bool)
    exposure = oof.exposure_from_flag(combo, LOCKED_SCALE)

    nav_b, _fb, meta_b = simulate_core(
        market,
        base_target,
        base_regime,
        dividends,
        apply_e22=True,
        e22_version=e22div.E22_V2S,
        apply_stock_div=True,
        e45_exposure=None,
    )
    nav_l, _fl, meta_l = simulate_core(
        market,
        fin50_target,
        fin50_regime,
        dividends,
        apply_e22=True,
        e22_version=e22div.E22_V2S,
        apply_stock_div=True,
        e45_exposure=exposure,
    )
    assert meta_b.get("exact_t1_ok") and meta_l.get("exact_t1_ok")

    sealed_end = pd.to_datetime(nav_b["date"]).dt.date.max()
    year_rows = []
    for y in range(SEALED_START.year, sealed_end.year + 1):
        zb = year_stats(nav_b, y)
        zl = year_stats(nav_l, y)
        if zb["cagr"] is None or zl["cagr"] is None:
            continue
        year_rows.append(
            {
                "year": y,
                "base_cagr": zb["cagr"],
                "l1_cagr": zl["cagr"],
                "cagr_giveback_pp": (zb["cagr"] - zl["cagr"]) * 100.0,
                "base_mdd": zb["max_drawdown"],
                "l1_mdd": zl["max_drawdown"],
                "mdd_improve_pp": (abs(zb["max_drawdown"]) - abs(zl["max_drawdown"])) * 100.0,
            }
        )

    coverage = {
        "oof_2012_2018": {
            "combo": oof.flag_coverage(combo, OOF_START, OOF_END),
            "crisis": oof.flag_coverage(crisis, OOF_START, OOF_END),
        },
        "val_2019_2022": {
            "combo": oof.flag_coverage(combo, VAL_START, VAL_END),
            "crisis": oof.flag_coverage(crisis, VAL_START, VAL_END),
        },
        "sealed_2023_plus": {
            "combo": oof.flag_coverage(combo, SEALED_START, sealed_end),
            "crisis": oof.flag_coverage(crisis, SEALED_START, sealed_end),
        },
    }

    fmap = {pd.Timestamp(i).normalize(): bool(v) for i, v in combo.items()}

    def day_cond(nav: pd.DataFrame) -> dict:
        d = nav.copy()
        d["date"] = pd.to_datetime(d["date"])
        d = d[d["date"].dt.date >= SEALED_START].copy()
        d["ret"] = d["nav"].pct_change()
        d["flag"] = d["date"].dt.normalize().map(lambda x: fmap.get(x, False))
        on = d.loc[d["flag"], "ret"].dropna()
        off = d.loc[~d["flag"], "ret"].dropna()
        out = {
            "flag_share": float(d["flag"].mean()) if len(d) else 0.0,
            "mean_ret_flag_on": float(on.mean()) if len(on) else None,
            "mean_ret_flag_off": float(off.mean()) if len(off) else None,
            "n_flag_on": int(len(on)),
            "n_flag_off": int(len(off)),
        }
        if "e45_equity_scale" in d.columns:
            out["mean_e45_scale"] = float(d["e45_equity_scale"].mean())
            out["mean_e45_scale_flag_on"] = (
                float(d.loc[d["flag"], "e45_equity_scale"].mean()) if d["flag"].any() else None
            )
        return out

    sealed_b = oof.window_nav_stats(nav_b, SEALED_START, sealed_end)
    sealed_l = oof.window_nav_stats(nav_l, SEALED_START, sealed_end)
    val_b = oof.window_nav_stats(nav_b, VAL_START, VAL_END)
    val_l = oof.window_nav_stats(nav_l, VAL_START, VAL_END)

    implications = [
        "COMBO flag stays elevated in sealed bull years; equity scale 0.50 truncates upside more than it saves drawdown.",
        "Validation had negative CAGR giveback (L1 beat BASE) because stress episodes repaid the cut; sealed did not.",
        "L2 must separate FIN_CAP (concentration) from gross-cut (timing), cap flag share, and require asymmetric restore.",
        "Do not retune L1_FINCAP50_COMBO_50 — axis STOPPED; new L2 charter required.",
    ]

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "locked_id": "L1_FINCAP50_COMBO_50",
        "live_wire": False,
        "retune_allowed": False,
        "heldout_reference": {
            "val_cagr_giveback_pp": (val_b["cagr"] - val_l["cagr"]) * 100.0,
            "val_mdd_improve_pp": (abs(val_b["max_drawdown"]) - abs(val_l["max_drawdown"])) * 100.0,
            "sealed_cagr_giveback_pp": (sealed_b["cagr"] - sealed_l["cagr"]) * 100.0,
            "sealed_mdd_improve_pp": (abs(sealed_b["max_drawdown"]) - abs(sealed_l["max_drawdown"])) * 100.0,
            "sealed_gate_cagr_max_pp": 3.0,
            "sealed_fail_reason": "cagr_giveback_pp > 3.0",
        },
        "flag_coverage": coverage,
        "sealed_day_conditionals_base": day_cond(nav_b),
        "sealed_day_conditionals_l1": day_cond(nav_l),
        "sealed_by_year": year_rows,
        "implications": implications,
        "label": "L1_SEALED_ATTRIBUTION_READY_FOR_L2_CHARTER",
    }

    (OUT / "reports" / "l1_sealed_attribution.json").write_text(json.dumps(payload, indent=2) + "\n")
    (RESEARCH / "MDD_L1_SEALED_ATTRIBUTION.json").write_text(json.dumps(payload, indent=2) + "\n")
    pd.DataFrame(year_rows).to_csv(OUT / "outputs" / "l1_sealed_by_year.csv", index=False)

    lines = [
        "# L1 Sealed-Window Attribution (for L2 charter)",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Locked (frozen, no retune): `L1_FINCAP50_COMBO_50`",
        "Status: **RESEARCH_ONLY** — explains `STOP_L1_HELDOUT_MIXED`; does not reopen L1 cuts.",
        "",
        "## Held-out deltas (recomputed)",
        "",
        f"- Val CAGR giveback: **{payload['heldout_reference']['val_cagr_giveback_pp']:.2f} pp** (negative = L1 better)",
        f"- Val MDD improve: **{payload['heldout_reference']['val_mdd_improve_pp']:.2f} pp**",
        f"- Sealed CAGR giveback: **{payload['heldout_reference']['sealed_cagr_giveback_pp']:.2f} pp** (gate ≤3.0) → **FAIL**",
        f"- Sealed MDD improve: **{payload['heldout_reference']['sealed_mdd_improve_pp']:.2f} pp**",
        "",
        "## Flag coverage",
        "",
        "| Window | COMBO share | CRISIS share |",
        "|---|---:|---:|",
    ]
    for w, v in coverage.items():
        lines.append(f"| {w} | {v['combo']:.1%} | {v['crisis']:.1%} |")
    sb = payload["sealed_day_conditionals_base"]
    sl = payload["sealed_day_conditionals_l1"]
    lines += [
        "",
        "## Sealed day conditionals",
        "",
        f"- BASE mean ret flag-on / off: `{sb.get('mean_ret_flag_on')}` / `{sb.get('mean_ret_flag_off')}`",
        f"- L1 mean ret flag-on / off: `{sl.get('mean_ret_flag_on')}` / `{sl.get('mean_ret_flag_off')}`",
        f"- L1 mean E45 scale (sealed / flag-on): `{sl.get('mean_e45_scale')}` / `{sl.get('mean_e45_scale_flag_on')}`",
        "",
        "## Sealed by year",
        "",
        "| Year | BASE CAGR | L1 CAGR | Giveback pp | MDD Δpp |",
        "|---:|---:|---:|---:|---:|",
    ]
    for r in year_rows:
        lines.append(
            f"| {r['year']} | {r['base_cagr']:.2%} | {r['l1_cagr']:.2%} | "
            f"{r['cagr_giveback_pp']:+.2f} | {r['mdd_improve_pp']:+.2f} |"
        )
    lines += ["", "## Implications for L2", ""]
    for i, s in enumerate(implications, 1):
        lines.append(f"{i}. {s}")
    lines += [
        "",
        "See charter: `research/gaps/MDD_L2_LOSS_ENGINE_CHARTER.md`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "MDD_L1_SEALED_ATTRIBUTION.md").write_text(md)
    (RESEARCH / "MDD_L1_SEALED_ATTRIBUTION.md").write_text(md)
    print(
        json.dumps(
            {
                "label": payload["label"],
                "sealed_cagr_giveback_pp": payload["heldout_reference"]["sealed_cagr_giveback_pp"],
                "sealed_combo_share": coverage["sealed_2023_plus"]["combo"],
            },
            indent=2,
        )
    )
    print("EXIT:0")


if __name__ == "__main__":
    main()
