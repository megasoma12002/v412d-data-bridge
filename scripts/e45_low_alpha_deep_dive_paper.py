#!/usr/bin/env python3
"""E45 PAPER low-alpha deep-dive (research only — not live).

Dense band after fine grid + crisis-triggered screens:
  α ∈ {0.00, 0.05, 0.08, 0.10, 0.12, 0.15} (+ 0.25 observe reference)

Adds held-out/sealed ranking, adjacent-α stability, and month-end-style
YTD / trailing_1y PAUSE sensitivity (ALERT 3pp / PAUSE 5pp).

Does NOT edit Soft-Frozen, DEFAULT, operating observe sleeves, or authorize stitch.
Does NOT retune frozen E3_VOLTARGET_WINNER — only scales constant blend α.
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
book_id = book_id_for_alpha  # harness alias


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/e45-low-alpha-deep-dive"
RESEARCH = ROOT / "research/e45"
OPS = ROOT / "research/ops"
MARKET_PATH = ROOT / "forward/e21/live_market.csv"
DIV_PATH = ROOT / "data/dividend_events/e22_dividend_events.csv"

E45_PROFILE = "E3_VOLTARGET_WINNER"
ALPHAS = (0.00, 0.05, 0.08, 0.10, 0.12, 0.15, 0.25)
WINDOWS = {
    "full": (None, None),
    "oof_2011_2018": (date(2011, 1, 1), date(2018, 12, 31)),
    "validation_2019_2022": (date(2019, 1, 1), date(2022, 12, 31)),
    "sealed_2023_plus": (date(2023, 1, 1), None),
    "heldout_2019_plus": (date(2019, 1, 1), None),
}
FOCUS_WINDOWS = ("heldout_2019_plus", "sealed_2023_plus", "full")
TRAIL_ALERT_PP = 3.0
TRAIL_PAUSE_PP = 5.0






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

    print("loading market + dividends ...", flush=True)
    market = load_market()
    dividends = pd.read_csv(DIV_PATH, dtype={"code": str}) if DIV_PATH.exists() else pd.DataFrame()

    print("BASE features + E45 exposure ...", flush=True)
    _p, _s, base_target, base_regime = e16_features(market)
    close_eq = (
        market[market["code"].isin(ALL)]
        .pivot(index="date", columns="code", values="close")
        .sort_index()
        .ffill()
    )
    e45_full = e45.compute_exposure(close_eq, E45_PROFILE)["exposure"]

    books: dict = {}
    rows: list[dict] = []
    navs: dict[str, pd.DataFrame] = {}
    nav_join = None

    for alpha in ALPHAS:
        bid = book_id(alpha)
        exp = blend_exposure(e45_full, alpha)
        print(f"sim {bid} alpha={alpha:.2f} ...", flush=True)
        nav, fills, meta = simulate_core(
            market,
            base_target,
            base_regime,
            dividends,
            apply_e22=True,
            apply_stock_div=True,
            e45_exposure=exp,
        )
        tag = bid.lower()
        nav.to_csv(OUT / "outputs" / f"{tag}_daily_nav.csv", index=False)
        fills.to_csv(OUT / "outputs" / f"{tag}_fills.csv", index=False)
        if exp is not None:
            exp.to_csv(OUT / "outputs" / f"{tag}_exposure.csv")
        navs[bid] = nav

        col = f"nav_{tag}"
        part = nav[["date", "nav"]].rename(columns={"nav": col})
        nav_join = part if nav_join is None else nav_join.merge(part, on="date", how="inner")

        win = {wname: window_stats(nav, ws, we) for wname, (ws, we) in WINDOWS.items()}
        books[bid] = {
            "alpha": float(alpha),
            "exact_t1_ok": bool(meta.get("exact_t1_ok")),
            "mean_e45_exposure": meta.get("mean_e45_exposure"),
            "windows": win,
        }
        for wname, st in win.items():
            rows.append(
                {
                    "book": bid,
                    "alpha": float(alpha),
                    "window": wname,
                    "cagr": st.get("cagr"),
                    "max_drawdown": st.get("max_drawdown"),
                    "vol": st.get("vol"),
                    "utility": st.get("utility"),
                    "n_days": st.get("n_days"),
                    "mean_e45_exposure": meta.get("mean_e45_exposure"),
                    "exact_t1": bool(meta.get("exact_t1_ok")),
                    "live_wire": False,
                }
            )

    assert nav_join is not None
    nav_join.to_csv(OUT / "outputs" / "low_alpha_nav_compare.csv", index=False)
    pd.DataFrame(rows).to_csv(OUT / "outputs" / "low_alpha_window_metrics.csv", index=False)

    base_id = book_id(0.0)
    deltas: list[dict] = []
    for alpha in ALPHAS:
        bid = book_id(alpha)
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
                    "alpha": float(alpha),
                    "window": w,
                    "base_cagr": b.get("cagr"),
                    "book_cagr": c.get("cagr"),
                    "base_mdd": b.get("max_drawdown"),
                    "book_mdd": c.get("max_drawdown"),
                    "mdd_improve_pp": mdd_pp,
                    "cagr_giveback_pp": cagr_pp,
                    "mdd_pp_per_cagr_giveback_pp": eff,
                    "mean_e45_exposure": books[bid]["mean_e45_exposure"],
                }
            )
    delta_df = pd.DataFrame(deltas)
    delta_df.to_csv(OUT / "outputs" / "low_alpha_deltas_vs_base.csv", index=False)

    held = delta_df[(delta_df["window"] == "heldout_2019_plus") & (delta_df["alpha"] > 0)].copy()
    held["score"] = held["mdd_improve_pp"] - 0.5 * held["cagr_giveback_pp"].abs()
    held_sorted = held.sort_values(["score", "mdd_improve_pp"], ascending=False)
    preferred = None if held_sorted.empty else held_sorted.iloc[0].to_dict()

    sealed = delta_df[(delta_df["window"] == "sealed_2023_plus") & (delta_df["alpha"] > 0)].copy()
    sealed["score"] = sealed["mdd_improve_pp"] - 0.5 * sealed["cagr_giveback_pp"].abs()
    sealed_sorted = sealed.sort_values(["score", "mdd_improve_pp"], ascending=False)

    dense = [a for a in ALPHAS if 0 < a <= 0.15]
    stability: list[dict] = []
    for a0, a1 in zip(dense, dense[1:]):
        r0 = held[held["alpha"] == a0].iloc[0]
        r1 = held[held["alpha"] == a1].iloc[0]
        s0 = float(r0["mdd_improve_pp"] - 0.5 * abs(r0["cagr_giveback_pp"]))
        s1 = float(r1["mdd_improve_pp"] - 0.5 * abs(r1["cagr_giveback_pp"]))
        stability.append(
            {
                "from_alpha": float(a0),
                "to_alpha": float(a1),
                "delta_mdd_improve_pp": float(r1["mdd_improve_pp"] - r0["mdd_improve_pp"]),
                "delta_cagr_giveback_pp": float(r1["cagr_giveback_pp"] - r0["cagr_giveback_pp"]),
                "delta_score": s1 - s0,
            }
        )
    pd.DataFrame(stability).to_csv(OUT / "outputs" / "low_alpha_adjacent_stability.csv", index=False)

    tip = min(
        pd.to_datetime(navs[base_id]["date"]).max(),
        pd.to_datetime(navs[book_id(0.05)]["date"]).max(),
    )
    pause_rows: list[dict] = []
    for alpha in ALPHAS:
        bid = book_id(alpha)
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
                    "alpha": float(alpha),
                    "asof": str(tip.date()),
                    "window": wname,
                    "base_cagr": sb.get("cagr"),
                    "book_cagr": sc.get("cagr"),
                    "base_mdd": sb.get("max_drawdown"),
                    "book_mdd": sc.get("max_drawdown"),
                    "mdd_improve_pp": mdd_pp,
                    "cagr_giveback_pp": cagr_pp,
                    "flag": pause_flag(cagr_pp),
                    "n_days": int(min(len(b), len(c))),
                }
            )
    pause_df = pd.DataFrame(pause_rows)
    pause_df.to_csv(OUT / "outputs" / "low_alpha_pause_sensitivity.csv", index=False)

    clear = []
    for alpha in dense + [0.25]:
        sub = pause_df[pause_df["alpha"] == alpha]
        flags = set(sub["flag"].tolist())
        clear.append(
            {
                "alpha": float(alpha),
                "book": book_id(alpha),
                "ytd_flag": sub[sub["window"] == "ytd"]["flag"].iloc[0],
                "trailing_1y_flag": sub[sub["window"] == "trailing_1y"]["flag"].iloc[0],
                "both_ok": flags == {"OK"},
                "any_pause": "PAUSE_REVIEW" in flags,
            }
        )

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PAPER_ONLY",
        "ballot": "E45 PAPER low-alpha deep-dive",
        "roadmap_priority": 1,
        "profile": E45_PROFILE,
        "alphas": list(ALPHAS),
        "definition": "exposure_α = (1−α)·1 + α·E45_exposure",
        "soft_frozen": "KEEP [0.50, 0.95]",
        "default_books": "E22_v2s_tw KEEP",
        "live_stitch": "FORBIDDEN",
        "observe_sleeves_unchanged": True,
        "pause_policy": {
            "alert_pp": TRAIL_ALERT_PP,
            "pause_pp": TRAIL_PAUSE_PP,
            "asof": str(tip.date()),
            "windows": ["ytd", "trailing_1y"],
        },
        "heldout_preferred": preferred,
        "heldout_ranking": held_sorted.to_dict(orient="records"),
        "sealed_top": sealed_sorted.head(5).to_dict(orient="records"),
        "adjacent_stability": stability,
        "pause_clearance": clear,
        "books": {
            k: {
                "alpha": v["alpha"],
                "exact_t1_ok": v["exact_t1_ok"],
                "mean_e45_exposure": v["mean_e45_exposure"],
                "windows": v["windows"],
            }
            for k, v in books.items()
        },
    }
    (OUT / "reports" / "e45_low_alpha_deep_dive.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )
    (RESEARCH / "E45_LOW_ALPHA_DEEP_DIVE.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    lines = [
        "# E45 PAPER Low-Alpha Deep-Dive (0.05–0.15)",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Status: **PAPER ONLY** — Soft-Frozen **KEEP**; DEFAULT **`E22_v2s_tw` KEEP**; live stitch **FORBIDDEN**.",
        "Observe sleeves (full-E45 + blend-α=0.25) **unchanged**.",
        "",
        "## Roadmap context",
        "",
        "- Priority **#1** on the E45 paper research list (dense band after fine grid; #2 crisis-triggered already run).",
        "- Dense α: **0.05 / 0.08 / 0.10 / 0.12 / 0.15** (+ 0.00 BASE, + 0.25 observe ref).",
        f"- Profile: frozen `{E45_PROFILE}` (not retuned).",
        "",
        "## Held-out deltas vs BASE",
        "",
        "| Book | α | MDD Δpp | CAGR giveback pp | Efficiency | Score | mean_exp |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for _, r in held_sorted.iterrows():
        lines.append(
            f"| {r['book']} | {r['alpha']:.2f} | {pp(r['mdd_improve_pp'])} | "
            f"{pp(r['cagr_giveback_pp'])} | {pp(r['mdd_pp_per_cagr_giveback_pp'])} | "
            f"{r['score']:.3f} | {r['mean_e45_exposure']:.3f} |"
        )

    lines += [
        "",
        "## Sealed deltas vs BASE",
        "",
        "| Book | α | MDD Δpp | CAGR giveback pp | Score |",
        "|---|---:|---:|---:|---:|",
    ]
    for _, r in sealed_sorted.iterrows():
        lines.append(
            f"| {r['book']} | {r['alpha']:.2f} | {pp(r['mdd_improve_pp'])} | "
            f"{pp(r['cagr_giveback_pp'])} | {r['score']:.3f} |"
        )

    if preferred:
        lines += [
            "",
            f"**Held-out preferred:** `{preferred['book']}` (α={preferred['alpha']:.2f}) — "
            f"MDD {pp(preferred['mdd_improve_pp'])} / giveback {pp(preferred['cagr_giveback_pp'])}",
        ]

    lines += [
        "",
        "## Adjacent-α stability (held-out)",
        "",
        "| From α | To α | Δ MDD pp | Δ giveback pp | Δ score |",
        "|---:|---:|---:|---:|---:|",
    ]
    for s in stability:
        lines.append(
            f"| {s['from_alpha']:.2f} | {s['to_alpha']:.2f} | "
            f"{pp(s['delta_mdd_improve_pp'])} | {pp(s['delta_cagr_giveback_pp'])} | "
            f"{s['delta_score']:+.3f} |"
        )

    lines += [
        "",
        f"## Month-end PAUSE sensitivity (asof {tip.date()})",
        "",
        f"Policy: ALERT >{TRAIL_ALERT_PP:.0f}pp / PAUSE_REVIEW >{TRAIL_PAUSE_PP:.0f}pp CAGR giveback on YTD / trailing_1y.",
        "",
        "| Book | α | Window | MDD Δpp | Giveback pp | Flag |",
        "|---|---:|---|---:|---:|---|",
    ]
    for _, r in pause_df.sort_values(["alpha", "window"]).iterrows():
        lines.append(
            f"| {r['book']} | {r['alpha']:.2f} | {r['window']} | "
            f"{pp(r['mdd_improve_pp'])} | {pp(r['cagr_giveback_pp'])} | **{r['flag']}** |"
        )

    lines += [
        "",
        "### Dense-band + observe-ref PAUSE clearance",
        "",
        "| α | YTD | Trailing 1y | Both OK? |",
        "|---:|---|---|---|",
    ]
    for c in clear:
        lines.append(
            f"| {c['alpha']:.2f} | {c['ytd_flag']} | {c['trailing_1y_flag']} | "
            f"{'YES' if c['both_ok'] else 'NO'} |"
        )

    any_clear = any(c["both_ok"] for c in clear if c["alpha"] <= 0.15)
    lines += ["", "## Read-through (paper)", ""]
    if preferred:
        lines.append(
            f"1. Held-out dense-band pick: **α={preferred['alpha']:.2f}** "
            f"({pp(preferred['mdd_improve_pp'])} MDD / {pp(preferred['cagr_giveback_pp'])} giveback)."
        )
    else:
        lines.append("1. No preferred α.")
    lines += [
        "2. Use adjacent-α table to judge whether 0.05→0.15 is smooth or cliffy.",
        "3. PAUSE clearance at current tip: "
        + (
            "**≥1 dense α clears both YTD/1y** — only a future OPEN ballot may retarget observe."
            if any_clear
            else "**no dense α clears both YTD/1y PAUSE** at current tip — do not retarget observe on PAUSE grounds."
        ),
        "4. α=0.25 remains the operating blend observe sleeve until a new OPEN ballot.",
        "5. This screen does **not** open/retarget observe or authorize stitch.",
        "",
        "## Governance",
        "",
        "- Soft-Frozen FIN clip **[0.50, 0.95] KEEP**",
        "- Live DEFAULT **`E22_v2s_tw` KEEP**",
        "- Live E45 stitch **FORBIDDEN**",
        "- −13.16% remains **RETIRED_HISTORICAL_NARRATIVE**",
        "",
        "## Artifacts",
        "",
        f"- `{OUT / 'reports' / 'e45_low_alpha_deep_dive.json'}`",
        f"- `{OUT / 'outputs' / 'low_alpha_window_metrics.csv'}`",
        f"- `{OUT / 'outputs' / 'low_alpha_deltas_vs_base.csv'}`",
        f"- `{OUT / 'outputs' / 'low_alpha_adjacent_stability.csv'}`",
        f"- `{OUT / 'outputs' / 'low_alpha_pause_sensitivity.csv'}`",
        f"- `{RESEARCH / 'E45_LOW_ALPHA_DEEP_DIVE.md'}`",
        "",
        "## Reproduce",
        "",
        "```bash",
        "python3 scripts/e45_low_alpha_deep_dive_paper.py",
        "```",
        "",
    ]
    memo = "\n".join(lines) + "\n"
    (RESEARCH / "E45_LOW_ALPHA_DEEP_DIVE.md").write_text(memo)
    (OUT / "reports" / "E45_LOW_ALPHA_DEEP_DIVE.md").write_text(memo)
    (OPS / "E45_LOW_ALPHA_DEEP_DIVE.md").write_text(
        "\n".join(
            [
                "# E45 PAPER Low-Alpha Deep-Dive — Ops pointer",
                "",
                "Ballot: `E45 PAPER low-alpha deep-dive` — **PAPER ONLY** (roadmap priority #1)",
                "",
                "Primary memo: `research/e45/E45_LOW_ALPHA_DEEP_DIVE.md`",
                "Repro: `repro/e45-low-alpha-deep-dive/`",
                "",
                "```bash",
                "python3 scripts/e45_low_alpha_deep_dive_paper.py",
                "```",
                "",
                "Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN · observe unchanged",
                "",
            ]
        )
    )

    print("DONE", flush=True)
    if preferred:
        print(
            f"heldout preferred: {preferred['book']} "
            f"mdd={preferred['mdd_improve_pp']:+.3f} "
            f"giveback={preferred['cagr_giveback_pp']:+.3f} "
            f"score={preferred['score']:.3f}",
            flush=True,
        )
    for c in clear:
        print(
            f"pause α={c['alpha']:.2f}: ytd={c['ytd_flag']} "
            f"1y={c['trailing_1y_flag']} both_ok={c['both_ok']}",
            flush=True,
        )


if __name__ == "__main__":
    main()
