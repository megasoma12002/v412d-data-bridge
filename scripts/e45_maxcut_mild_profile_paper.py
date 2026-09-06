#!/usr/bin/env python3
"""E45 PAPER mild max_cut profile screen (research only — not live).

Roadmap #3: build *new paper profiles* with lower max_cut than the frozen
E3_VOLTARGET_WINNER (max_cut=0.5), without editing the frozen winner lock.

Compares:
  BASE
  REF: winner full (mc=0.50), blend-α=0.05, blend-α=0.25
  MILD paper profiles: max_cut ∈ {0.25, 0.35, 0.40} at full intensity
  Optional mild×blend: mc=0.25 @ α=0.50, mc=0.35 @ α=0.50

Does NOT edit Soft-Frozen / DEFAULT / observe sleeves / authorize stitch.
Does NOT mutate E3_WINNER or ProfileName — overrides max_cut only at call site.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from research_metric_helpers import mdd_delta_pp, cagr_delta_pp
from e50_early_stack_combined_nav import ALL, e16_features, nav_stats, simulate_core
import e45_crisis_core as e45

from e45_paper_harness import (
    BOOK_BASE,
    BOOK_BLEND_A25,
    BOOK_FULL,
    CLAIM_STATUS,
    E45_PROFILE_DEFAULT,
    MARKET_PATH,
    DIV_PATH,
    ROOT,
    WINDOWS_STANDARD,
    blend_exposure,
    book_id_for_alpha,
    deltas_vs_base,
    e16_features,
    e45_full_exposure,
    load_dividends,
    load_market,
    run_early_stack,
    window_stats,
)
blend = blend_exposure  # harness alias


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/e45-maxcut-mild-profile"
RESEARCH = ROOT / "research/e45"
OPS = ROOT / "research/ops"
MARKET_PATH = ROOT / "forward/e21/live_market.csv"
DIV_PATH = ROOT / "data/dividend_events/e22_dividend_events.csv"

FROZEN_PROFILE = "E3_VOLTARGET_WINNER"
FROZEN_MAX_CUT = float(e45.E3_WINNER["max_cut"])  # 0.5 — reference only
WINDOWS = WINDOWS_STANDARD
FOCUS_WINDOWS = ("heldout_2019_plus", "sealed_2023_plus", "full")
TRAIL_ALERT_PP = 3.0
TRAIL_PAUSE_PP = 5.0





def mild_exposure(risk: pd.DataFrame, max_cut: float) -> pd.Series:
    """Paper-only mild profile: same E3 voltarget math, lower max_cut."""
    return e45.exposure_e3_voltarget(
        risk,
        max_cut=float(max_cut),
        up_days=int(e45.E3_WINNER["up_days"]),
        target_vol=float(e45.E3_WINNER["target_vol"]),
        blend=float(e45.E3_WINNER["blend"]),
    ).rename(f"e45_mild_mc{int(round(max_cut * 100)):02d}")


def book_specs(winner_full: pd.Series, risk: pd.DataFrame) -> list[dict]:
    mild25 = mild_exposure(risk, 0.25)
    mild35 = mild_exposure(risk, 0.35)
    mild40 = mild_exposure(risk, 0.40)
    return [
        {"book": "BASE_E16_E18_E22_v2s", "family": "BASE", "max_cut": None, "alpha": 0.0, "tag": "base", "exposure": None},
        {"book": "REF_WINNER_MC50_FULL", "family": "REF_WINNER", "max_cut": FROZEN_MAX_CUT, "alpha": 1.0, "tag": "ref_winner_mc50_full", "exposure": winner_full.astype(float)},
        {"book": "BLEND_E45_A05", "family": "REF_BLEND", "max_cut": FROZEN_MAX_CUT, "alpha": 0.05, "tag": "ref_blend_a05", "exposure": blend(winner_full, 0.05)},
        {"book": "BLEND_E45_A25", "family": "REF_BLEND", "max_cut": FROZEN_MAX_CUT, "alpha": 0.25, "tag": "ref_blend_a25", "exposure": blend(winner_full, 0.25)},
        {"book": "MILD_MC25_FULL", "family": "MILD", "max_cut": 0.25, "alpha": 1.0, "tag": "mild_mc25_full", "exposure": mild25},
        {"book": "MILD_MC35_FULL", "family": "MILD", "max_cut": 0.35, "alpha": 1.0, "tag": "mild_mc35_full", "exposure": mild35},
        {"book": "MILD_MC40_FULL", "family": "MILD", "max_cut": 0.40, "alpha": 1.0, "tag": "mild_mc40_full", "exposure": mild40},
        {"book": "MILD_MC25_A50", "family": "MILD_BLEND", "max_cut": 0.25, "alpha": 0.50, "tag": "mild_mc25_a50", "exposure": blend(mild25, 0.50)},
        {"book": "MILD_MC35_A50", "family": "MILD_BLEND", "max_cut": 0.35, "alpha": 0.50, "tag": "mild_mc35_a50", "exposure": blend(mild35, 0.50)},
    ]


def pp(x: float | None) -> str:
    return "n/a" if x is None else f"{x:+.2f}"


def dynamic_windows(asof: pd.Timestamp) -> dict[str, tuple[pd.Timestamp, pd.Timestamp]]:
    return {
        "ytd": (pd.Timestamp(asof.year, 1, 1), asof),
        "trailing_1y": (asof - pd.Timedelta(days=365), asof),
    }


def slice_nav(nav: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    d = nav.copy()
    d["date"] = pd.to_datetime(d["date"])
    d = d[(d["date"] >= start) & (d["date"] <= end)].reset_index(drop=True)
    if len(d) < 2:
        return d
    d = d.copy()
    d["nav"] = d["nav"] / float(d["nav"].iloc[0])
    return d


def pause_flag(giveback_pp: float | None) -> str:
    if giveback_pp is None:
        return "n/a"
    if giveback_pp > TRAIL_PAUSE_PP:
        return "PAUSE_REVIEW"
    if giveback_pp > TRAIL_ALERT_PP:
        return "ALERT"
    return "OK"


def main() -> None:
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)
    OPS.mkdir(parents=True, exist_ok=True)

    # Sanity: frozen lock untouched
    assert float(e45.E3_WINNER["max_cut"]) == 0.5

    print("loading market + dividends ...", flush=True)
    market = load_market()
    dividends = pd.read_csv(DIV_PATH, dtype={"code": str}) if DIV_PATH.exists() else pd.DataFrame()

    print("BASE features + exposures ...", flush=True)
    _p, _s, base_target, base_regime = e16_features(market)
    close_eq = (
        market[market["code"].isin(ALL)]
        .pivot(index="date", columns="code", values="close")
        .sort_index()
        .ffill()
    )
    risk = e45.risk_features_from_closes(close_eq)
    winner_full = e45.compute_exposure(close_eq, FROZEN_PROFILE)["exposure"]
    # Confirm winner path matches max_cut=0.5 call
    winner_direct = mild_exposure(risk, FROZEN_MAX_CUT)
    corr = float(winner_full.astype(float).corr(winner_direct.astype(float)))

    specs = book_specs(winner_full, risk)
    books: dict = {}
    rows: list[dict] = []
    navs: dict[str, pd.DataFrame] = {}
    nav_join = None

    for spec in specs:
        bid = spec["book"]
        exp = spec["exposure"]
        print(
            f"sim {bid} family={spec['family']} max_cut={spec['max_cut']} alpha={spec['alpha']} ...",
            flush=True,
        )
        nav, fills, meta = simulate_core(
            market,
            base_target,
            base_regime,
            dividends,
            apply_e22=True,
            apply_stock_div=True,
            e45_exposure=exp,
        )
        tag = spec["tag"]
        nav.to_csv(OUT / "outputs" / f"{tag}_daily_nav.csv", index=False)
        fills.to_csv(OUT / "outputs" / f"{tag}_fills.csv", index=False)
        if exp is not None:
            exp.to_csv(OUT / "outputs" / f"{tag}_exposure.csv")
            mean_exp = float(exp.mean())
            frac_lt1 = float((exp.astype(float) < 1.0 - 1e-12).mean())
            mean_cut = float((1.0 - exp.astype(float)).mean())
        else:
            mean_exp, frac_lt1, mean_cut = 1.0, 0.0, 0.0
        if meta.get("mean_e45_exposure") is not None:
            mean_exp = float(meta["mean_e45_exposure"])

        navs[bid] = nav
        col = f"nav_{tag}"
        part = nav[["date", "nav"]].rename(columns={"nav": col})
        nav_join = part if nav_join is None else nav_join.merge(part, on="date", how="inner")

        win = {wname: window_stats(nav, ws, we) for wname, (ws, we) in WINDOWS.items()}
        books[bid] = {
            "book": bid,
            "family": spec["family"],
            "max_cut": spec["max_cut"],
            "alpha": float(spec["alpha"]),
            "exact_t1_ok": bool(meta.get("exact_t1_ok")),
            "mean_e45_exposure": mean_exp,
            "frac_days_lt_1": frac_lt1,
            "mean_cut_vs_1": mean_cut,
            "windows": win,
        }
        for wname, st in win.items():
            rows.append(
                {
                    "book": bid,
                    "family": spec["family"],
                    "max_cut": spec["max_cut"],
                    "alpha": float(spec["alpha"]),
                    "window": wname,
                    "cagr": st.get("cagr"),
                    "max_drawdown": st.get("max_drawdown"),
                    "vol": st.get("vol"),
                    "utility": st.get("utility"),
                    "n_days": st.get("n_days"),
                    "mean_e45_exposure": mean_exp,
                    "frac_days_lt_1": frac_lt1,
                    "exact_t1": bool(meta.get("exact_t1_ok")),
                    "live_wire": False,
                }
            )

    assert nav_join is not None
    nav_join.to_csv(OUT / "outputs" / "maxcut_mild_nav_compare.csv", index=False)
    pd.DataFrame(rows).to_csv(OUT / "outputs" / "maxcut_mild_window_metrics.csv", index=False)

    base_id = "BASE_E16_E18_E22_v2s"
    deltas: list[dict] = []
    for spec in specs:
        bid = spec["book"]
        for w in FOCUS_WINDOWS:
            b = books[base_id]["windows"][w]
            c = books[bid]["windows"][w]
            mdd_pp = mdd_delta_pp(b.get("max_drawdown"), c.get("max_drawdown"))
            cagr_pp = cagr_delta_pp(b.get("cagr"), c.get("cagr"), missing_as_zero=True)
            eff = None
            if cagr_pp is not None and abs(cagr_pp) > 1e-9:
                eff = mdd_pp / cagr_pp
            deltas.append(
                {
                    "book": bid,
                    "family": spec["family"],
                    "max_cut": spec["max_cut"],
                    "alpha": float(spec["alpha"]),
                    "window": w,
                    "base_cagr": b.get("cagr"),
                    "book_cagr": c.get("cagr"),
                    "base_mdd": b.get("max_drawdown"),
                    "book_mdd": c.get("max_drawdown"),
                    "mdd_improve_pp": mdd_pp,
                    "cagr_giveback_pp": cagr_pp,
                    "mdd_pp_per_cagr_giveback_pp": eff,
                    "mean_e45_exposure": books[bid]["mean_e45_exposure"],
                    "frac_days_lt_1": books[bid]["frac_days_lt_1"],
                }
            )
    delta_df = pd.DataFrame(deltas)
    delta_df.to_csv(OUT / "outputs" / "maxcut_mild_deltas_vs_base.csv", index=False)

    held = delta_df[(delta_df["window"] == "heldout_2019_plus") & (delta_df["book"] != base_id)].copy()
    held["score"] = held["mdd_improve_pp"] - 0.5 * held["cagr_giveback_pp"].abs()
    held_sorted = held.sort_values(["score", "mdd_improve_pp"], ascending=False)
    preferred = None if held_sorted.empty else held_sorted.iloc[0].to_dict()

    sealed = delta_df[(delta_df["window"] == "sealed_2023_plus") & (delta_df["book"] != base_id)].copy()
    sealed["score"] = sealed["mdd_improve_pp"] - 0.5 * sealed["cagr_giveback_pp"].abs()
    sealed_sorted = sealed.sort_values(["score", "mdd_improve_pp"], ascending=False)

    best_by_family = {}
    for fam in ("REF_BLEND", "REF_WINNER", "MILD", "MILD_BLEND"):
        sub = held_sorted[held_sorted["family"] == fam]
        best_by_family[fam] = None if sub.empty else sub.iloc[0].to_dict()

    tip = min(pd.to_datetime(navs[base_id]["date"]).max(), pd.to_datetime(navs["BLEND_E45_A05"]["date"]).max())
    pause_rows: list[dict] = []
    for spec in specs:
        bid = spec["book"]
        for wname, (ws, we) in dynamic_windows(tip).items():
            b = slice_nav(navs[base_id], ws, we)
            c = slice_nav(navs[bid], ws, we)
            if len(b) < 30 or len(c) < 30:
                sb = sc = {"cagr": None, "max_drawdown": None}
            else:
                sb, sc = nav_stats(b), nav_stats(c)
            mdd_pp = mdd_delta_pp(sb.get("max_drawdown"), sc.get("max_drawdown"))
            cagr_pp = cagr_delta_pp(sb.get("cagr"), sc.get("cagr"), missing_as_zero=True)
            pause_rows.append(
                {
                    "book": bid,
                    "family": spec["family"],
                    "max_cut": spec["max_cut"],
                    "alpha": float(spec["alpha"]),
                    "asof": str(tip.date()),
                    "window": wname,
                    "mdd_improve_pp": mdd_pp,
                    "cagr_giveback_pp": cagr_pp,
                    "flag": pause_flag(cagr_pp),
                    "n_days": int(min(len(b), len(c))),
                }
            )
    pause_df = pd.DataFrame(pause_rows)
    pause_df.to_csv(OUT / "outputs" / "maxcut_mild_pause_sensitivity.csv", index=False)

    # Still frozen?
    frozen_ok = float(e45.E3_WINNER["max_cut"]) == 0.5

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PAPER_ONLY",
        "ballot": "E45 PAPER max_cut mild profile",
        "roadmap_priority": 3,
        "frozen_profile": FROZEN_PROFILE,
        "frozen_max_cut": FROZEN_MAX_CUT,
        "frozen_lock_untouched": frozen_ok,
        "winner_vs_direct_mc50_corr": corr,
        "definition": {
            "winner": "compute_exposure(..., E3_VOLTARGET_WINNER) — frozen max_cut=0.5",
            "mild": "exposure_e3_voltarget(..., max_cut∈{0.25,0.35,0.40}) — paper-only override at call site",
            "blend": "exposure = (1−α)·1 + α·profile_exposure",
        },
        "soft_frozen": "KEEP [0.50, 0.95]",
        "default_books": "E22_v2s_tw KEEP",
        "live_stitch": "FORBIDDEN",
        "observe_sleeves_unchanged": True,
        "heldout_preferred": preferred,
        "heldout_ranking": held_sorted.to_dict(orient="records"),
        "heldout_best_by_family": best_by_family,
        "sealed_top": sealed_sorted.head(5).to_dict(orient="records"),
        "pause_asof": str(tip.date()),
        "pause_rows": pause_rows,
        "books": {
            k: {kk: vv for kk, vv in v.items() if kk != "windows"} | {"windows": v["windows"]}
            for k, v in books.items()
        },
    }
    (OUT / "reports" / "e45_maxcut_mild_profile.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )
    (RESEARCH / "E45_MAXCUT_MILD_PROFILE.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    lines = [
        "# E45 PAPER Mild max_cut Profile Screen",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Status: **PAPER ONLY** — Soft-Frozen **KEEP**; DEFAULT **`E22_v2s_tw` KEEP**; live stitch **FORBIDDEN**.",
        "Observe sleeves (full-E45 + blend-α=0.25) **unchanged**.",
        f"Frozen `E3_WINNER.max_cut` untouched: **{frozen_ok}** (still {FROZEN_MAX_CUT}).",
        "",
        "## Roadmap context",
        "",
        "- Priority **#3**: milder defense via **new paper profile** (lower max_cut), not in-place winner retune.",
        "- Compare mild profiles vs blend-α refs from #1/#2 lineage.",
        "",
        "## Definitions",
        "",
        "| Family | Rule |",
        "|---|---|",
        "| `REF_WINNER` | frozen `E3_VOLTARGET_WINNER` (max_cut=0.50) full |",
        "| `REF_BLEND` | `(1−α)·1 + α·winner` |",
        "| `MILD` | E3 voltarget math with max_cut ∈ {0.25,0.35,0.40}, α=1 |",
        "| `MILD_BLEND` | `(1−α)·1 + α·mild_exposure` |",
        "",
        f"Winner vs direct mc=0.50 series corr: **{corr:.6f}** (sanity).",
        "",
        "## Held-out deltas vs BASE",
        "",
        "| Book | Family | max_cut | α | MDD Δpp | Giveback pp | Score | mean_exp |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for _, r in held_sorted.iterrows():
        mc = "" if pd.isna(r["max_cut"]) else f"{r['max_cut']:.2f}"
        lines.append(
            f"| {r['book']} | {r['family']} | {mc} | {r['alpha']:.2f} | "
            f"{pp(r['mdd_improve_pp'])} | {pp(r['cagr_giveback_pp'])} | "
            f"{r['score']:.3f} | {r['mean_e45_exposure']:.3f} |"
        )

    lines += [
        "",
        "## Sealed top (same score)",
        "",
        "| Book | Family | max_cut | α | MDD Δpp | Giveback pp | Score |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for _, r in sealed_sorted.head(6).iterrows():
        mc = "" if pd.isna(r["max_cut"]) else f"{r['max_cut']:.2f}"
        lines.append(
            f"| {r['book']} | {r['family']} | {mc} | {r['alpha']:.2f} | "
            f"{pp(r['mdd_improve_pp'])} | {pp(r['cagr_giveback_pp'])} | {r['score']:.3f} |"
        )

    if preferred:
        lines += [
            "",
            f"**Held-out preferred:** `{preferred['book']}` "
            f"(family={preferred['family']}, max_cut={preferred.get('max_cut')}, α={preferred['alpha']}) — "
            f"MDD {pp(preferred['mdd_improve_pp'])} / giveback {pp(preferred['cagr_giveback_pp'])}",
        ]

    lines += ["", "### Best by family (held-out)", ""]
    for fam, row in best_by_family.items():
        if row is None:
            lines.append(f"- **{fam}**: n/a")
        else:
            lines.append(
                f"- **{fam}**: `{row['book']}` — MDD {pp(row['mdd_improve_pp'])} / "
                f"giveback {pp(row['cagr_giveback_pp'])} / score {row['score']:.3f}"
            )

    lines += [
        "",
        f"## Month-end PAUSE sensitivity (asof {tip.date()})",
        "",
        f"Policy: ALERT >{TRAIL_ALERT_PP:.0f}pp / PAUSE_REVIEW >{TRAIL_PAUSE_PP:.0f}pp on YTD / trailing_1y.",
        "",
        "| Book | Family | Window | MDD Δpp | Giveback pp | Flag |",
        "|---|---|---|---:|---:|---|",
    ]
    for _, r in pause_df.sort_values(["family", "book", "window"]).iterrows():
        lines.append(
            f"| {r['book']} | {r['family']} | {r['window']} | "
            f"{pp(r['mdd_improve_pp'])} | {pp(r['cagr_giveback_pp'])} | **{r['flag']}** |"
        )

    # Compare mild full vs blend refs on held-out
    ref_a05 = held[held["book"] == "BLEND_E45_A05"]
    mild_best = held_sorted[held_sorted["family"] == "MILD"]
    lines += [
        "",
        "## Read-through (paper)",
        "",
        "1. Mild max_cut profiles are **new paper challengers**, not edits to frozen winner.",
        "2. Compare best `MILD` / `MILD_BLEND` vs `BLEND_E45_A05` / `BLEND_E45_A25` on held-out score.",
    ]
    if preferred:
        lines.append(
            f"3. Held-out preferred this screen: **`{preferred['book']}`** "
            f"(score {preferred['score']:.3f})."
        )
    if not mild_best.empty and not ref_a05.empty:
        mb = mild_best.iloc[0]
        ra = ref_a05.iloc[0]
        if mb["score"] > ra["score"]:
            lines.append(
                f"4. Best mild (`{mb['book']}`) **beats** BLEND_E45_A05 on held-out score "
                f"({mb['score']:.3f} vs {ra['score']:.3f})."
            )
        else:
            lines.append(
                f"4. Best mild (`{mb['book']}`) does **not** beat BLEND_E45_A05 on held-out score "
                f"({mb['score']:.3f} vs {ra['score']:.3f}) — blend-α remains stronger paper path."
            )
    lines += [
        "5. This screen does **not** open a new observe sleeve or authorize stitch.",
        "",
        "## Governance",
        "",
        "- Soft-Frozen FIN clip **[0.50, 0.95] KEEP**",
        "- Live DEFAULT **`E22_v2s_tw` KEEP**",
        "- Live E45 stitch **FORBIDDEN**",
        "- Frozen `E3_WINNER.max_cut=0.5` **untouched**",
        "- −13.16% remains **RETIRED_HISTORICAL_NARRATIVE**",
        "",
        "## Artifacts",
        "",
        f"- `{OUT / 'reports' / 'e45_maxcut_mild_profile.json'}`",
        f"- `{OUT / 'outputs' / 'maxcut_mild_window_metrics.csv'}`",
        f"- `{OUT / 'outputs' / 'maxcut_mild_deltas_vs_base.csv'}`",
        f"- `{OUT / 'outputs' / 'maxcut_mild_pause_sensitivity.csv'}`",
        f"- `{RESEARCH / 'E45_MAXCUT_MILD_PROFILE.md'}`",
        "",
        "## Reproduce",
        "",
        "```bash",
        "python3 scripts/e45_maxcut_mild_profile_paper.py",
        "```",
        "",
    ]
    memo = "\n".join(lines) + "\n"
    (RESEARCH / "E45_MAXCUT_MILD_PROFILE.md").write_text(memo)
    (OUT / "reports" / "E45_MAXCUT_MILD_PROFILE.md").write_text(memo)
    (OPS / "E45_MAXCUT_MILD_PROFILE.md").write_text(
        "\n".join(
            [
                "# E45 PAPER Mild max_cut Profile — Ops pointer",
                "",
                "Ballot: `E45 PAPER max_cut mild profile` — **PAPER ONLY** (roadmap priority #3)",
                "",
                "Primary memo: `research/e45/E45_MAXCUT_MILD_PROFILE.md`",
                "Repro: `repro/e45-maxcut-mild-profile/`",
                "",
                "```bash",
                "python3 scripts/e45_maxcut_mild_profile_paper.py",
                "```",
                "",
                "Frozen E3_WINNER untouched · Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN",
                "",
            ]
        )
    )

    print("DONE", flush=True)
    print(f"frozen_lock_untouched={frozen_ok} corr_mc50={corr:.6f}", flush=True)
    if preferred:
        print(
            f"heldout preferred: {preferred['book']} "
            f"mdd={preferred['mdd_improve_pp']:+.3f} "
            f"giveback={preferred['cagr_giveback_pp']:+.3f} "
            f"score={preferred['score']:.3f}",
            flush=True,
        )


if __name__ == "__main__":
    main()
