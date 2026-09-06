#!/usr/bin/env python3
"""E45 PAPER blend-alpha screen (research only — not live).

Compares Soft-Frozen early-stack BASE vs partial E45 overlays:
  exposure_α = (1−α)·1 + α·E3_VOLTARGET_WINNER

Fine grid: α = 0.00, 0.05, …, 1.00 (step 0.05). PAPER ONLY.

Does NOT edit Soft-Frozen, DEFAULT books, or authorize stitch.
Does NOT retune the frozen E3 winner lock — only scales overlay intensity.
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

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/e45-blend-alpha-grid-fine"
RESEARCH = ROOT / "research/e45"
OPS = ROOT / "research/ops"
MARKET_PATH = ROOT / "forward/e21/live_market.csv"
DIV_PATH = ROOT / "data/dividend_events/e22_dividend_events.csv"

E45_PROFILE = "E3_VOLTARGET_WINNER"
ALPHAS = tuple(round(i * 0.05, 2) for i in range(0, 21))  # 0.00..1.00 step 0.05
WINDOWS = {
    "full": (None, None),
    "oof_2011_2018": (date(2011, 1, 1), date(2018, 12, 31)),
    "validation_2019_2022": (date(2019, 1, 1), date(2022, 12, 31)),
    "sealed_2023_plus": (date(2023, 1, 1), None),
    "heldout_2019_plus": (date(2019, 1, 1), None),
}
FOCUS_WINDOWS = ("heldout_2019_plus", "sealed_2023_plus", "full")


def load_market() -> pd.DataFrame:
    market = pd.read_csv(MARKET_PATH, dtype={"code": str})
    market["date"] = pd.to_datetime(market["date"])
    required = set(ALL + ["TAIEX"])
    complete = market.groupby("date")["code"].apply(lambda s: required.issubset(set(s)))
    return market[market["date"].isin(complete[complete].index)].sort_values(["date", "code"])


def window_stats(nav: pd.DataFrame, start: date | None, end: date | None) -> dict:
    d = nav.copy()
    d["date"] = pd.to_datetime(d["date"]).dt.date
    if start is not None:
        d = d[d["date"] >= start]
    if end is not None:
        d = d[d["date"] <= end]
    d = d.reset_index(drop=True)
    if len(d) < 30:
        return {
            "cagr": None,
            "max_drawdown": None,
            "utility": None,
            "vol": None,
            "n_days": int(len(d)),
        }
    d = d.copy()
    d["nav"] = d["nav"] / float(d["nav"].iloc[0])
    out = nav_stats(d)
    out["n_days"] = int(len(d))
    return out


def book_id(alpha: float) -> str:
    if alpha <= 0:
        return "BASE_E16_E18_E22_v2s"
    if alpha >= 1:
        return "CHAL_E45_E3"
    return f"BLEND_E45_A{int(round(alpha * 100)):02d}"


def blend_exposure(full_e45: pd.Series, alpha: float) -> pd.Series | None:
    """exposure = (1−α)·1 + α·E45. α=0 → None (pure BASE)."""
    if alpha <= 0:
        return None
    if alpha >= 1:
        return full_e45.astype(float)
    mixed = (1.0 - alpha) * 1.0 + alpha * full_e45.astype(float)
    return mixed.clip(0.0, 1.0).rename(f"e45_blend_a{int(round(alpha * 100)):02d}")


def pct(x: float | None) -> str:
    return "n/a" if x is None else f"{x:.2%}"


def pp(x: float | None) -> str:
    return "n/a" if x is None else f"{x:+.2f}"


def main() -> None:
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)
    OPS.mkdir(parents=True, exist_ok=True)

    print("loading market + dividends ...", flush=True)
    market = load_market()
    dividends = pd.read_csv(DIV_PATH, dtype={"code": str}) if DIV_PATH.exists() else pd.DataFrame()

    print("BASE features ...", flush=True)
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
    nav_join.to_csv(OUT / "outputs" / "blend_alpha_nav_compare.csv", index=False)
    metrics = pd.DataFrame(rows)
    metrics.to_csv(OUT / "outputs" / "blend_alpha_window_metrics.csv", index=False)

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
                }
            )
    delta_df = pd.DataFrame(deltas)
    delta_df.to_csv(OUT / "outputs" / "blend_alpha_deltas_vs_base.csv", index=False)

    held = delta_df[(delta_df["window"] == "heldout_2019_plus") & (delta_df["alpha"] > 0)].copy()
    held["score"] = held["mdd_improve_pp"] - 0.5 * held["cagr_giveback_pp"].abs()
    held_sorted = held.sort_values("score", ascending=False)
    preferred = None if held_sorted.empty else held_sorted.iloc[0].to_dict()

    # Top-5 held-out by score + Pareto note (non-dominated on MDD improve vs giveback)
    top5 = held_sorted.head(5).to_dict(orient="records")
    pareto = []
    # sort by giveback ascending; keep improving MDD
    cand = held.sort_values(["cagr_giveback_pp", "mdd_improve_pp"], ascending=[True, False])
    best_mdd = -1e9
    for _, row in cand.iterrows():
        if row["mdd_improve_pp"] > best_mdd + 1e-12:
            pareto.append(row.to_dict())
            best_mdd = float(row["mdd_improve_pp"])

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "label": "E45_BLEND_ALPHA_GRID_FINE",
        "status": "PAPER_ONLY",
        "live_wire": False,
        "stitch_authorized": False,
        "soft_frozen_unchanged": True,
        "default_books_unchanged": True,
        "e45_profile": E45_PROFILE,
        "blend_definition": "exposure_alpha = (1-alpha)*1 + alpha*E3_VOLTARGET_WINNER",
        "alphas": list(ALPHAS),
        "claimed_mdd_status": e45.CLAIMED_MDD_STATUS,
        "primary_comparable_mdd": e45.PRIMARY_COMPARABLE_MDD,
        "books": books,
        "focus_deltas_vs_base": deltas,
        "preferred_partial_alpha_heldout": preferred,
        "heldout_top5_by_score": top5 if preferred is not None else [],
        "heldout_pareto_mdd_vs_giveback": pareto if preferred is not None else [],
        "parent_artifacts": [
            "research/ops/E45_LIVE_STITCH_CHARTER.md",
            "research/ops/E45_DUAL_PAPER_OBSERVE_OPEN.md",
            "research/e45/E45_DUAL_PAPER_OBSERVE.md",
            "research/ops/E45_STITCH_CHECKLIST.md",
            "research/e45/E45_BLEND_ALPHA_PAPER_SCREEN.md",
            "research/ops/E45_BLEND025_OBSERVE_OPEN.md",
        ],
        "non_goals": [
            "Live stitch / Soft-Frozen flip / DEFAULT flip",
            "Retune frozen E3_VOLTARGET_WINNER lock in place",
            "Invent replacement for retired -13.16% narrative",
            "Treat screen winner as stitch license",
        ],
    }
    (OUT / "reports" / "e45_blend_alpha_grid_fine.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )
    (RESEARCH / "E45_BLEND_ALPHA_GRID_FINE.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )

    lines = [
        "# E45 PAPER Blend-Alpha Fine Grid (step 0.05)",
        "",
        f"Generated: `{summary['generated_at_utc']}`",
        "Status: **PAPER ONLY** — Soft-Frozen **KEEP**; DEFAULT **`E22_v2s_tw` KEEP**; live stitch **FORBIDDEN**.",
        "",
        "## Definition",
        "",
        f"- Profile: E45 `{E45_PROFILE}` (frozen winner lock **not** retuned)",
        "- Blend: `exposure_α = (1−α)·1 + α·E45_exposure`",
        "- Alphas: " + ", ".join(f"{a:.2f}" for a in ALPHAS),
        "- α=0 → BASE; α=1 → full CHAL_E45_E3 (same as operating observe challenger)",
        "",
        "## Window metrics",
        "",
        "| Book | α | Window | CAGR | MDD | mean_exp | n_days |",
        "|---|---:|---|---:|---:|---:|---:|",
    ]
    for r in rows:
        mean_exp = r["mean_e45_exposure"]
        mean_s = "n/a" if mean_exp is None else f"{mean_exp:.3f}"
        lines.append(
            f"| {r['book']} | {r['alpha']:.2f} | {r['window']} | "
            f"{pct(r['cagr'])} | {pct(r['max_drawdown'])} | {mean_s} | {r['n_days']} |"
        )

    lines += [
        "",
        "## Deltas vs BASE (focus windows)",
        "",
        "| Book | α | Window | MDD improve pp | CAGR giveback pp | MDD/giveback |",
        "|---|---:|---|---:|---:|---:|",
    ]
    for d in deltas:
        if d["alpha"] == 0:
            continue
        lines.append(
            f"| {d['book']} | {d['alpha']:.2f} | {d['window']} | "
            f"{pp(d['mdd_improve_pp'])} | {pp(d['cagr_giveback_pp'])} | "
            f"{pp(d['mdd_pp_per_cagr_giveback_pp'])} |"
        )

    if preferred:
        lines += [
            "",
            "## Held-out heuristic pick (paper only)",
            "",
            f"- Preferred partial α on held-out score `MDD_improve − 0.5·|CAGR_giveback|`: "
            f"**α={preferred['alpha']:.2f}** (`{preferred['book']}`)",
            f"- Held-out MDD improve **{preferred['mdd_improve_pp']:+.2f} pp**; "
            f"CAGR giveback **{preferred['cagr_giveback_pp']:+.2f} pp**",
            "- This is a **screen hint**, not a stitch / Soft-Frozen license.",
            "",
            "### Held-out top-5 by score",
            "",
            "| α | Book | MDD improve pp | CAGR giveback pp | score |",
            "|---:|---|---:|---:|---:|",
        ]
        for r in top5:
            lines.append(
                f"| {r['alpha']:.2f} | {r['book']} | {r['mdd_improve_pp']:+.2f} | "
                f"{r['cagr_giveback_pp']:+.2f} | {r['score']:+.2f} |"
            )
        lines += [
            "",
            "### Held-out Pareto (higher MDD improve for given/lower giveback)",
            "",
            "| α | MDD improve pp | CAGR giveback pp |",
            "|---:|---:|---:|",
        ]
        for r in pareto:
            lines.append(
                f"| {r['alpha']:.2f} | {r['mdd_improve_pp']:+.2f} | {r['cagr_giveback_pp']:+.2f} |"
            )

    lines += [
        "",
        "## Ops / governance",
        "",
        "1. Soft-Frozen live default stays BASE until a separate stitch PR",
        "2. Operating observe sleeve remains full CHAL_E45_E3 unless human opens a new blend observe",
        "3. Do not silent-edit Soft-Frozen; do not rewrite `forward/e21` history",
        "4. Screen ≠ stitch; second human stitch ACCEPT still required for any live attach",
        "5. Never cite −13.16%; use dated lineage / challenger MDDs only",
        "",
        "## Explicit non-goals",
        "",
    ]
    for item in summary["non_goals"]:
        lines.append(f"- {item}")
    lines += [
        "",
        "## Label",
        "",
        "`E45_BLEND_ALPHA_GRID_FINE_2026-09-06__STEP0P05__PAPER_ONLY__STITCH_FORBIDDEN`",
        "",
        "Artifacts:",
        f"- `{OUT / 'reports' / 'e45_blend_alpha_grid_fine.json'}`",
        f"- `{OUT / 'outputs' / 'blend_alpha_window_metrics.csv'}`",
        f"- `{OUT / 'outputs' / 'blend_alpha_deltas_vs_base.csv'}`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "E45_BLEND_ALPHA_GRID_FINE.md").write_text(md)
    (RESEARCH / "E45_BLEND_ALPHA_GRID_FINE.md").write_text(md)
    (OPS / "E45_BLEND_ALPHA_GRID_FINE.md").write_text(
        "# E45 Blend-Alpha Fine Grid (pointer)\n\n"
        "Status: **PAPER ONLY** — see `research/e45/E45_BLEND_ALPHA_GRID_FINE.md`.\n\n"
        "Run:\n\n"
        "```bash\n"
        "python3 scripts/e45_blend_alpha_grid_fine.py\n"
        "```\n\n"
        "Live stitch: **FORBIDDEN**. Soft-Frozen / DEFAULT: **KEEP**.\n"
    )

    print(
        json.dumps(
            {
                "label": summary["label"],
                "status": summary["status"],
                "live_wire": False,
                "preferred_partial_alpha_heldout": None
                if preferred is None
                else {
                    "alpha": preferred["alpha"],
                    "book": preferred["book"],
                    "mdd_improve_pp": preferred["mdd_improve_pp"],
                    "cagr_giveback_pp": preferred["cagr_giveback_pp"],
                },
            },
            indent=2,
        )
    )
    print("EXIT:0")


if __name__ == "__main__":
    main()
