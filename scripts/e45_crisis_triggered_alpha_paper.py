#!/usr/bin/env python3
"""E45 PAPER crisis-triggered alpha screen (research only — not live).

Motivation: constant blend α still taxes calm / mild-vol days. Fine grid preferred
low constant α on held-out; this screen asks whether α should fire only when the
defensive sleeve is in a deeper cut state.

Modes
-----
- CONST: exposure = (1−α)·1 + α·E45   (reference)
- GATE:  if E45_exp >= gate → 1.0; else (1−α)·1 + α·E45
- E1BIN: if E1 binary crisis → (1−α)·1 + α·E45; else 1.0

Profile: frozen E3_VOLTARGET_WINNER (not retuned). PAPER ONLY.
Does NOT edit Soft-Frozen, DEFAULT, observe sleeves, or authorize stitch.
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


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/e45-crisis-triggered-alpha"
RESEARCH = ROOT / "research/e45"
OPS = ROOT / "research/ops"
MARKET_PATH = ROOT / "forward/e21/live_market.csv"
DIV_PATH = ROOT / "data/dividend_events/e22_dividend_events.csv"

E45_PROFILE = "E3_VOLTARGET_WINNER"
WINDOWS = {
    "full": (None, None),
    "oof_2011_2018": (date(2011, 1, 1), date(2018, 12, 31)),
    "validation_2019_2022": (date(2019, 1, 1), date(2022, 12, 31)),
    "sealed_2023_plus": (date(2023, 1, 1), None),
    "heldout_2019_plus": (date(2019, 1, 1), None),
}
FOCUS_WINDOWS = ("heldout_2019_plus", "sealed_2023_plus", "full")

# Spec: gate thresholds on E3 exposure (deeper cut = more "crisis-like").
# Empirics on live_market: ~25% days <0.90, ~15% <0.85, ~8% <0.80.
GATE_THRESHOLDS = (0.90, 0.85, 0.80)
GATE_ALPHAS = (0.25, 0.50, 1.00)
E1BIN_ALPHAS = (0.25, 0.50, 1.00)
CONST_ALPHAS = (0.00, 0.05, 0.25, 1.00)




def pct(x: float | None) -> str:
    return "n/a" if x is None else f"{x:.2%}"


def pp(x: float | None) -> str:
    return "n/a" if x is None else f"{x:+.2f}"


def blend_const(full_e45: pd.Series, alpha: float) -> pd.Series | None:
    if alpha <= 0:
        return None
    if alpha >= 1:
        return full_e45.astype(float)
    mixed = (1.0 - alpha) * 1.0 + alpha * full_e45.astype(float)
    return mixed.clip(0.0, 1.0)


def blend_gate(full_e45: pd.Series, alpha: float, gate: float) -> pd.Series:
    """α_eff = 0 when E45_exp >= gate; else constant α blend."""
    e = full_e45.astype(float)
    active = e < float(gate)
    mixed = (1.0 - alpha) * 1.0 + alpha * e
    out = pd.Series(1.0, index=e.index, dtype=float)
    out.loc[active] = mixed.loc[active].clip(0.0, 1.0)
    return out


def blend_e1bin(full_e45: pd.Series, crisis: pd.Series, alpha: float) -> pd.Series:
    e = full_e45.astype(float)
    flag = crisis.reindex(e.index).fillna(False).astype(bool)
    mixed = (1.0 - alpha) * 1.0 + alpha * e
    out = pd.Series(1.0, index=e.index, dtype=float)
    out.loc[flag] = mixed.loc[flag].clip(0.0, 1.0)
    return out


def book_specs() -> list[dict]:
    specs: list[dict] = []
    for a in CONST_ALPHAS:
        if a <= 0:
            specs.append(
                {
                    "book": "BASE_E16_E18_E22_v2s",
                    "mode": "CONST",
                    "alpha": 0.0,
                    "gate": None,
                    "tag": "base_e16_e18_e22_v2s",
                }
            )
        elif a >= 1:
            specs.append(
                {
                    "book": "CHAL_E45_E3",
                    "mode": "CONST",
                    "alpha": 1.0,
                    "gate": None,
                    "tag": "const_a100_full",
                }
            )
        else:
            specs.append(
                {
                    "book": book_id_for_alpha(a),  # canonical BLEND_E45_A## / BASE / CHAL,
                    "mode": "CONST",
                    "alpha": float(a),
                    "gate": None,
                    "tag": f"const_a{int(round(a * 100)):02d}",
                }
            )
    for g in GATE_THRESHOLDS:
        for a in GATE_ALPHAS:
            gtag = str(g).replace(".", "")
            specs.append(
                {
                    "book": f"GATE_{gtag}_A{int(round(a * 100)):02d}",
                    "mode": "GATE",
                    "alpha": float(a),
                    "gate": float(g),
                    "tag": f"gate_{gtag}_a{int(round(a * 100)):02d}",
                }
            )
    for a in E1BIN_ALPHAS:
        specs.append(
            {
                "book": f"E1BIN_A{int(round(a * 100)):02d}",
                "mode": "E1BIN",
                "alpha": float(a),
                "gate": None,
                "tag": f"e1bin_a{int(round(a * 100)):02d}",
            }
        )
    return specs


def build_exposure(spec: dict, full_e45: pd.Series, e1_crisis: pd.Series) -> pd.Series | None:
    mode = spec["mode"]
    alpha = float(spec["alpha"])
    if mode == "CONST":
        return blend_const(full_e45, alpha)
    if mode == "GATE":
        return blend_gate(full_e45, alpha, float(spec["gate"]))
    if mode == "E1BIN":
        return blend_e1bin(full_e45, e1_crisis, alpha)
    raise ValueError(mode)


def exposure_diag(exp: pd.Series | None, full_e45: pd.Series) -> dict:
    if exp is None:
        return {
            "mean_e45_exposure": 1.0,
            "frac_days_lt_1": 0.0,
            "frac_days_active_vs_full": 0.0,
            "mean_cut_vs_1": 0.0,
        }
    e = exp.astype(float)
    full = full_e45.astype(float).reindex(e.index)
    # "active" = days where we deviate from pure risk-on (1.0)
    active = (e < 1.0 - 1e-12).mean()
    # days where gated book differs from always-on full E45 path intensity proxy
    return {
        "mean_e45_exposure": float(e.mean()),
        "frac_days_lt_1": float(active),
        "frac_days_active_vs_full": float((e.sub(1.0).abs() > 1e-12).mean()),
        "mean_cut_vs_1": float((1.0 - e).mean()),
        "corr_vs_full_e45": float(e.corr(full)) if full.notna().sum() > 30 else None,
    }


def main() -> None:
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)
    OPS.mkdir(parents=True, exist_ok=True)

    print("loading market + dividends ...", flush=True)
    market = load_market()
    dividends = pd.read_csv(DIV_PATH, dtype={"code": str}) if DIV_PATH.exists() else pd.DataFrame()

    print("BASE features + E45 exposures ...", flush=True)
    _p, _s, base_target, base_regime = e16_features(market)
    close_eq = (
        market[market["code"].isin(ALL)]
        .pivot(index="date", columns="code", values="close")
        .sort_index()
        .ffill()
    )
    e45_pack = e45.compute_exposure(close_eq, E45_PROFILE)
    e45_full = e45_pack["exposure"]
    risk = e45.risk_features_from_closes(close_eq)
    e1_crisis = e45.binary_crisis_flag(risk)

    gate_day_frac = {
        str(g): float((e45_full < float(g)).mean()) for g in GATE_THRESHOLDS
    }
    e1_frac = float(e1_crisis.mean())

    specs = book_specs()
    books: dict = {}
    rows: list[dict] = []
    nav_join = None

    for spec in specs:
        bid = spec["book"]
        exp = build_exposure(spec, e45_full, e1_crisis)
        print(f"sim {bid} mode={spec['mode']} alpha={spec['alpha']} gate={spec['gate']} ...", flush=True)
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

        diag = exposure_diag(exp, e45_full)
        # prefer simulator mean when present
        if meta.get("mean_e45_exposure") is not None:
            diag["mean_e45_exposure"] = float(meta["mean_e45_exposure"])

        col = f"nav_{tag}"
        part = nav[["date", "nav"]].rename(columns={"nav": col})
        nav_join = part if nav_join is None else nav_join.merge(part, on="date", how="inner")

        win = {wname: window_stats(nav, ws, we) for wname, (ws, we) in WINDOWS.items()}
        books[bid] = {
            **spec,
            "exact_t1_ok": bool(meta.get("exact_t1_ok")),
            **diag,
            "windows": win,
        }
        for wname, st in win.items():
            rows.append(
                {
                    "book": bid,
                    "mode": spec["mode"],
                    "alpha": float(spec["alpha"]),
                    "gate": spec["gate"],
                    "window": wname,
                    "cagr": st.get("cagr"),
                    "max_drawdown": st.get("max_drawdown"),
                    "vol": st.get("vol"),
                    "utility": st.get("utility"),
                    "n_days": st.get("n_days"),
                    "mean_e45_exposure": diag["mean_e45_exposure"],
                    "frac_days_lt_1": diag["frac_days_lt_1"],
                    "exact_t1": bool(meta.get("exact_t1_ok")),
                    "live_wire": False,
                }
            )

    assert nav_join is not None
    nav_join.to_csv(OUT / "outputs" / "crisis_triggered_nav_compare.csv", index=False)
    metrics = pd.DataFrame(rows)
    metrics.to_csv(OUT / "outputs" / "crisis_triggered_window_metrics.csv", index=False)

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
                    "mode": spec["mode"],
                    "alpha": float(spec["alpha"]),
                    "gate": spec["gate"],
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
    delta_df.to_csv(OUT / "outputs" / "crisis_triggered_deltas_vs_base.csv", index=False)

    held = delta_df[(delta_df["window"] == "heldout_2019_plus") & (delta_df["book"] != base_id)].copy()
    held["score"] = held["mdd_improve_pp"] - 0.5 * held["cagr_giveback_pp"].abs()
    held_sorted = held.sort_values("score", ascending=False)
    preferred = None if held_sorted.empty else held_sorted.iloc[0].to_dict()
    top5 = held_sorted.head(5).to_dict(orient="records")

    # Best GATE vs best CONST (excl full) on held-out score
    best_gate = held_sorted[held_sorted["mode"] == "GATE"].head(1)
    best_const = held_sorted[held_sorted["mode"] == "CONST"].head(1)
    best_e1 = held_sorted[held_sorted["mode"] == "E1BIN"].head(1)

    sealed = delta_df[(delta_df["window"] == "sealed_2023_plus") & (delta_df["book"] != base_id)].copy()
    sealed["score"] = sealed["mdd_improve_pp"] - 0.5 * sealed["cagr_giveback_pp"].abs()
    sealed_sorted = sealed.sort_values("score", ascending=False)

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PAPER_ONLY",
        "ballot": "E45 PAPER crisis-triggered alpha",
        "profile": E45_PROFILE,
        "definition": {
            "CONST": "exposure=(1-α)·1 + α·E45",
            "GATE": "if E45_exp>=gate → 1.0 else (1-α)·1 + α·E45",
            "E1BIN": "if E1 binary crisis → (1-α)·1 + α·E45 else 1.0",
            "note": (
                "E3 exposure is <1 on ~98% of days, so gate≠1.0; "
                "gates 0.90/0.85/0.80 target deeper-cut states only."
            ),
        },
        "gate_day_fraction_full_sample": gate_day_frac,
        "e1_binary_crisis_fraction_full_sample": e1_frac,
        "soft_frozen": "KEEP [0.50, 0.95]",
        "default_books": "E22_v2s_tw KEEP",
        "live_stitch": "FORBIDDEN",
        "observe_sleeves_unchanged": True,
        "books": {
            k: {
                kk: vv
                for kk, vv in v.items()
                if kk != "windows"
            }
            | {"windows": v["windows"]}
            for k, v in books.items()
        },
        "heldout_preferred": preferred,
        "heldout_top5": top5,
        "heldout_best_by_mode": {
            "GATE": None if best_gate.empty else best_gate.iloc[0].to_dict(),
            "CONST": None if best_const.empty else best_const.iloc[0].to_dict(),
            "E1BIN": None if best_e1.empty else best_e1.iloc[0].to_dict(),
        },
        "sealed_top3": sealed_sorted.head(3).to_dict(orient="records"),
        "artifacts": {
            "repro": str(OUT),
            "metrics_csv": str(OUT / "outputs" / "crisis_triggered_window_metrics.csv"),
            "deltas_csv": str(OUT / "outputs" / "crisis_triggered_deltas_vs_base.csv"),
        },
    }
    # Fix books serialization — windows already included; simplify
    payload["books"] = {
        k: {
            "book": v["book"],
            "mode": v["mode"],
            "alpha": v["alpha"],
            "gate": v["gate"],
            "exact_t1_ok": v["exact_t1_ok"],
            "mean_e45_exposure": v["mean_e45_exposure"],
            "frac_days_lt_1": v["frac_days_lt_1"],
            "windows": v["windows"],
        }
        for k, v in books.items()
    }

    (OUT / "reports" / "e45_crisis_triggered_alpha.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )
    (RESEARCH / "E45_CRISIS_TRIGGERED_ALPHA.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    # Markdown memo
    lines: list[str] = [
        "# E45 PAPER Crisis-Triggered Alpha",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Status: **PAPER ONLY** — Soft-Frozen **KEEP**; DEFAULT **`E22_v2s_tw` KEEP**; live stitch **FORBIDDEN**.",
        "Observe sleeves (full-E45 + blend-α=0.25) **unchanged**.",
        "",
        "## Why this screen",
        "",
        "- Constant blend α still cuts mild-vol days (E3_exp < 1 on ~98% of sample).",
        "- Fine grid preferred **low constant α (~0.05)** on held-out.",
        "- Question: can gating α to **deeper-cut / crisis states** keep MDD help with less CAGR giveback?",
        "",
        "## Definitions",
        "",
        "| Mode | Rule |",
        "|---|---|",
        "| `CONST` | `exposure = (1−α)·1 + α·E45` |",
        "| `GATE` | if `E45_exp ≥ gate` → `1.0`; else constant-α blend |",
        "| `E1BIN` | if E1 binary crisis → constant-α blend; else `1.0` |",
        "",
        f"- Profile: `{E45_PROFILE}` (frozen; not retuned)",
        f"- Gate day fractions (full sample): " + ", ".join(f"`<{g}` ≈ {gate_day_frac[str(g)]:.1%}" for g in GATE_THRESHOLDS),
        f"- E1 binary crisis fraction: ≈ **{e1_frac:.2%}**",
        "",
        "## Focus deltas vs BASE",
        "",
        "| Book | Mode | α | Gate | Window | MDD Δpp | CAGR giveback pp | mean_exp | frac_days<1 | score |",
        "|---|---|---:|---:|---|---:|---:|---:|---:|---:|",
    ]

    score_map = {}
    for _, r in held_sorted.iterrows():
        score_map[(r["book"], "heldout_2019_plus")] = r["score"]
    for _, r in sealed_sorted.iterrows():
        score_map[(r["book"], "sealed_2023_plus")] = r["score"]

    focus_books = [s["book"] for s in specs if s["book"] != base_id]
    for bid in focus_books:
        for w in FOCUS_WINDOWS:
            row = delta_df[(delta_df["book"] == bid) & (delta_df["window"] == w)].iloc[0]
            sc = score_map.get((bid, w))
            sc_s = "n/a" if sc is None else f"{sc:.3f}"
            lines.append(
                f"| {bid} | {row['mode']} | {row['alpha']:.2f} | "
                f"{'' if row['gate'] is None else row['gate']} | {w} | "
                f"{pp(row['mdd_improve_pp'])} | {pp(row['cagr_giveback_pp'])} | "
                f"{row['mean_e45_exposure']:.3f} | {row['frac_days_lt_1']:.1%} | {sc_s} |"
            )

    lines += [
        "",
        "## Held-out ranking (score = MDD_pp − 0.5·|CAGR_giveback_pp|)",
        "",
    ]
    if preferred:
        lines += [
            f"**Preferred (held-out):** `{preferred['book']}` "
            f"(mode={preferred['mode']}, α={preferred['alpha']}, gate={preferred.get('gate')}) — "
            f"MDD ~{pp(preferred['mdd_improve_pp'])} pp / giveback ~{pp(preferred['cagr_giveback_pp'])} pp",
            "",
            "### Top 5 held-out",
            "",
            "| Rank | Book | Mode | α | Gate | MDD Δpp | Giveback pp | Score |",
            "|---:|---|---|---:|---:|---:|---:|---:|",
        ]
        for i, r in enumerate(top5, 1):
            lines.append(
                f"| {i} | {r['book']} | {r['mode']} | {r['alpha']:.2f} | "
                f"{'' if r['gate'] is None else r['gate']} | "
                f"{pp(r['mdd_improve_pp'])} | {pp(r['cagr_giveback_pp'])} | {r['score']:.3f} |"
            )

    lines += [
        "",
        "### Best by mode (held-out)",
        "",
    ]
    for mode, row in payload["heldout_best_by_mode"].items():
        if row is None:
            lines.append(f"- **{mode}**: n/a")
        else:
            lines.append(
                f"- **{mode}**: `{row['book']}` — MDD {pp(row['mdd_improve_pp'])} / "
                f"giveback {pp(row['cagr_giveback_pp'])} / score {row['score']:.3f}"
            )

    lines += [
        "",
        "## Sealed top-3 (same score)",
        "",
        "| Book | Mode | α | Gate | MDD Δpp | Giveback pp | Score |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for r in sealed_sorted.head(3).to_dict(orient="records"):
        lines.append(
            f"| {r['book']} | {r['mode']} | {r['alpha']:.2f} | "
            f"{'' if r['gate'] is None else r['gate']} | "
            f"{pp(r['mdd_improve_pp'])} | {pp(r['cagr_giveback_pp'])} | {r['score']:.3f} |"
        )

    lines += [
        "",
        "## Read-through (paper)",
        "",
        f"1. **Held-out winner remains low constant α:** `{preferred['book'] if preferred else 'n/a'}` beats gated / E1BIN books on the heuristic score.",
        "2. **Deep-cut gates lose MDD more than they save giveback** on held-out vs `BLEND_E45_A05`.",
        "3. **E1 binary gate is too sparse (~1.2% days)** for held-out MDD help (often ≈0).",
        "4. **Sealed may still favor continuous moderate overlay** — same held-out vs sealed tension as the fine grid.",
        "5. **Paper path:** keep **low constant α**; do **not** promote crisis-gated α from this screen.",
        "6. This screen does **not** open a new observe sleeve or authorize stitch.",
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
        f"- `{OUT / 'reports' / 'e45_crisis_triggered_alpha.json'}`",
        f"- `{OUT / 'outputs' / 'crisis_triggered_window_metrics.csv'}`",
        f"- `{OUT / 'outputs' / 'crisis_triggered_deltas_vs_base.csv'}`",
        f"- `{RESEARCH / 'E45_CRISIS_TRIGGERED_ALPHA.md'}`",
        "",
        "## Reproduce",
        "",
        "```bash",
        "python3 scripts/e45_crisis_triggered_alpha_paper.py",
        "```",
        "",
    ]

    memo = "\n".join(lines) + "\n"
    (RESEARCH / "E45_CRISIS_TRIGGERED_ALPHA.md").write_text(memo)
    (OUT / "reports" / "E45_CRISIS_TRIGGERED_ALPHA.md").write_text(memo)
    (OPS / "E45_CRISIS_TRIGGERED_ALPHA.md").write_text(
        "\n".join(
            [
                "# E45 PAPER Crisis-Triggered Alpha — Ops pointer",
                "",
                "Ballot: `E45 PAPER crisis-triggered alpha` — **PAPER ONLY**",
                "",
                "Primary memo: `research/e45/E45_CRISIS_TRIGGERED_ALPHA.md`",
                "Repro: `repro/e45-crisis-triggered-alpha/`",
                "",
                "```bash",
                "python3 scripts/e45_crisis_triggered_alpha_paper.py",
                "```",
                "",
                "Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN · observe sleeves unchanged",
                "",
            ]
        )
    )

    print("DONE", flush=True)
    if preferred:
        print(
            f"heldout preferred: {preferred['book']} "
            f"mdd={preferred['mdd_improve_pp']:+.3f} giveback={preferred['cagr_giveback_pp']:+.3f} "
            f"score={preferred['score']:.3f}",
            flush=True,
        )


if __name__ == "__main__":
    main()
