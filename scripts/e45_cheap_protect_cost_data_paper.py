#!/usr/bin/env python3
"""E45 PAPER cheap-protect × cost realism × data-clean (research only).

Crosses lean protection books (A05 / sleeve-local) with fee multiples 0×–3×,
and attaches a 0050 C1 quarantine + adj_close QC gate (no e21 rewrite).

Books:
  BASE_E16_E18_E22_v2s     — no E45
  BLEND_E45_A05            — mild α=0.05 whole-book
  FIN_ONLY_A05             — α=0.05 Financial sleeve only
  SLEEVE_FIN_ONLY_A10      — α=0.10 Financial sleeve (observe OPERATING id)
  FIN_0050_A05             — α=0.05 Financial+0050

Score: MDD improve pp − 0.5·|CAGR giveback pp| vs BASE at the same cost ×.

Does NOT edit Soft-Frozen / DEFAULT / observe / stitch / HIGH_BETA.
Does NOT invent a replacement for retired claimed-MDD narrative.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from e50_early_stack_combined_nav import ALL
from e45_paper_harness import (
    BOOK_BASE,
    BOOK_BLEND_A05,
    CLAIM_STATUS,
    DIV_PATH,
    E45_PROFILE_DEFAULT,
    MARKET_PATH,
    ROOT,
    SLEEVE_FIN_0050,
    SLEEVE_FIN_ONLY,
    WINDOWS_STANDARD,
    blend_exposure,
    deltas_vs_base,
    e16_features,
    e45_full_exposure,
    load_dividends,
    load_market,
    run_early_stack,
    window_stats,
)

OUT = ROOT / "repro/e45-cheap-protect-cost-data"
RESEARCH = ROOT / "research/e45"
OPS = ROOT / "research/ops"

COST_MULTS = (0, 1, 2, 3)
FEE_KEYS = ("BUY_FEE", "SELL_FEE", "SLIP", "TAX_STOCK", "TAX_ETF")
FOCUS = ("heldout_2019_plus", "sealed_2023_plus", "full")
WINDOWS = {k: WINDOWS_STANDARD[k] for k in FOCUS}

# Phase C sealed C1 DRIFT outliers (UNADJUSTED_CLOSE_SPIKE) — quarantine for QC only.
QUARANTINE_0050_C1_DATES = (date(2014, 1, 2), date(2025, 6, 18))
SPIKE_ABS_RET_PP = 0.05  # |close_ret − adj_ret| > 5pp → spike candidate

# Lean protection morphologies under cost stress (paper densify + observe sleeve id).
BOOKS: list[dict] = [
    {"book": BOOK_BASE, "alpha": 0.0, "scope": None, "sleeves": None},
    {"book": BOOK_BLEND_A05, "alpha": 0.05, "scope": "ALL", "sleeves": None},
    {"book": "FIN_ONLY_A05", "alpha": 0.05, "scope": "FIN_ONLY", "sleeves": SLEEVE_FIN_ONLY},
    {
        "book": "SLEEVE_FIN_ONLY_A10",
        "alpha": 0.10,
        "scope": "FIN_ONLY",
        "sleeves": SLEEVE_FIN_ONLY,
    },
    {"book": "FIN_0050_A05", "alpha": 0.05, "scope": "FIN_0050", "sleeves": SLEEVE_FIN_0050},
]


def turnover_metrics(nav: pd.DataFrame, fills: pd.DataFrame) -> dict:
    n = nav.copy()
    n["date"] = pd.to_datetime(n["date"])
    years = max((n["date"].iloc[-1] - n["date"].iloc[0]).days / 365.25, 1e-9)
    mean_nav = float(n["nav"].mean()) if len(n) else None
    if fills is None or len(fills) == 0:
        return {
            "n_fills": 0,
            "fees_tax_sum": 0.0,
            "gross_traded": 0.0,
            "turnover_per_year": 0.0,
            "years": float(years),
            "mean_nav": mean_nav,
        }
    f = fills.copy()
    fee_col = None
    for c in ("fees_tax", "fee_tax", "fees"):
        if c in f.columns:
            fee_col = c
            break
    gross_col = "gross" if "gross" in f.columns else None
    fees = float(pd.to_numeric(f[fee_col], errors="coerce").fillna(0).sum()) if fee_col else 0.0
    gross = (
        float(pd.to_numeric(f[gross_col], errors="coerce").fillna(0).abs().sum())
        if gross_col
        else 0.0
    )
    to = (gross / mean_nav / years) if mean_nav and mean_nav > 0 else None
    return {
        "n_fills": int(len(f)),
        "fees_tax_sum": fees,
        "gross_traded": gross,
        "turnover_per_year": to,
        "years": float(years),
        "mean_nav": mean_nav,
    }


def pp(x) -> str:
    return "n/a" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:+.2f}"


def yn(flag: bool) -> str:
    return "Y" if flag else "N"


def qc_0050_adj_close(market: pd.DataFrame) -> dict:
    """Local 0050 cleanliness: prefer adj_close; quarantine known C1 spike dates."""
    sub = market[market["code"] == "0050"].copy().sort_values("date")
    if sub.empty:
        return {
            "status": "MISSING_0050",
            "quarantine_dates": [d.isoformat() for d in QUARANTINE_0050_C1_DATES],
            "note": "0050 absent from live_market — skip QC",
        }
    sub["date_d"] = pd.to_datetime(sub["date"]).dt.date
    has_adj = "adj_close" in sub.columns and sub["adj_close"].notna().any()
    close = pd.to_numeric(sub["close"], errors="coerce")
    adj = pd.to_numeric(sub["adj_close"], errors="coerce") if has_adj else None
    close_ret = close.pct_change()
    adj_ret = adj.pct_change() if adj is not None else None

    spike_rows = []
    if adj_ret is not None:
        delta = (close_ret - adj_ret).abs()
        for i, (d, dr, ar, dd) in enumerate(
            zip(sub["date_d"], close_ret, adj_ret, delta, strict=False)
        ):
            if pd.isna(dd) or float(dd) <= SPIKE_ABS_RET_PP:
                continue
            spike_rows.append(
                {
                    "date": d.isoformat() if hasattr(d, "isoformat") else str(d),
                    "close_ret": None if pd.isna(dr) else float(dr),
                    "adj_ret": None if pd.isna(ar) else float(ar),
                    "abs_delta": float(dd),
                }
            )

    qset = {d.isoformat() for d in QUARANTINE_0050_C1_DATES}
    found_q = [r for r in spike_rows if r["date"] in qset]
    extra = [r for r in spike_rows if r["date"] not in qset]

    # Continuity: adj_close should not print |ret|>50% on quarantine days
    adj_ok_on_q = True
    close_spike_on_q = False
    q_detail = []
    for qd in QUARANTINE_0050_C1_DATES:
        row = sub[sub["date_d"] == qd]
        if row.empty:
            q_detail.append({"date": qd.isoformat(), "present": False})
            continue
        idx = row.index[0]
        loc = sub.index.get_loc(idx)
        cr = float(close_ret.iloc[loc]) if loc > 0 and pd.notna(close_ret.iloc[loc]) else None
        ar = (
            float(adj_ret.iloc[loc])
            if adj_ret is not None and loc > 0 and pd.notna(adj_ret.iloc[loc])
            else None
        )
        if cr is not None and abs(cr) > SPIKE_ABS_RET_PP:
            close_spike_on_q = True
        if ar is not None and abs(ar) > 0.50:
            adj_ok_on_q = False
        q_detail.append(
            {
                "date": qd.isoformat(),
                "present": True,
                "close": float(row["close"].iloc[0]),
                "adj_close": None
                if not has_adj or pd.isna(row["adj_close"].iloc[0])
                else float(row["adj_close"].iloc[0]),
                "close_ret": cr,
                "adj_ret": ar,
            }
        )

    status = "PASS"
    if not has_adj:
        status = "WARN_NO_ADJ_CLOSE"
    elif not adj_ok_on_q:
        status = "FAIL_ADJ_SPIKE"
    elif close_spike_on_q and found_q:
        status = "PASS_QUARANTINE_COVERS_C1"
    elif extra:
        status = "WARN_EXTRA_SPIKES"
    elif close_spike_on_q:
        status = "WARN_C1_SPIKE_UNQUARANTINED"
    else:
        status = "PASS"

    return {
        "status": status,
        "code": "0050",
        "has_adj_close": bool(has_adj),
        "prefer_path": "adj_close_or_C2",
        "c1_raw_close": "spike_sensitive_do_not_use_for_history_qc",
        "quarantine_dates": [d.isoformat() for d in QUARANTINE_0050_C1_DATES],
        "quarantine_detail": q_detail,
        "spike_threshold_abs_ret": SPIKE_ABS_RET_PP,
        "spikes_vs_adj": spike_rows,
        "spikes_on_quarantine": found_q,
        "extra_spikes_beyond_quarantine": extra,
        "n_spikes": len(spike_rows),
        "e21_primary_rewrite": False,
        "yahoo_taiex_failover": "opt_in_helper_only",
        "phase_c_root_class": "UNADJUSTED_CLOSE_SPIKE",
        "ops_actions": [
            "Prefer adj_close (or C2) for 0050 history QC",
            "Quarantine C1 outlier dates when regenerating probes",
            "Do not flip Soft-Frozen / DEFAULT / e21 primary on C1 DRIFT alone",
        ],
    }


def main() -> None:
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)
    OPS.mkdir(parents=True, exist_ok=True)

    print("loading ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, _s, target, regime = e16_features(market)
    e45_full = e45_full_exposure(market)

    print("0050 adj_close / quarantine QC ...", flush=True)
    data_qc = qc_0050_adj_close(market)
    (OUT / "outputs" / "0050_quarantine_adj_qc.json").write_text(
        json.dumps(data_qc, indent=2, default=str) + "\n"
    )

    rows = []
    for spec in BOOKS:
        book = spec["book"]
        alpha = float(spec["alpha"])
        sleeves = spec["sleeves"]
        exp = blend_exposure(e45_full, alpha)
        for mult in COST_MULTS:
            print(
                f"sim {book} α={alpha:.2f} scope={spec['scope']} "
                f"sleeves={sleeves} cost×{mult} ...",
                flush=True,
            )
            nav, fills, meta = run_early_stack(
                market,
                target,
                regime,
                dividends,
                e45_exposure=exp,
                e45_sleeve_names=sleeves,
                cost_multiple=float(mult),
            )
            tag = f"{book.lower()}_x{mult}"
            nav.to_csv(OUT / "outputs" / f"{tag}_daily_nav.csv", index=False)
            fills.to_csv(OUT / "outputs" / f"{tag}_fills.csv", index=False)
            to = turnover_metrics(nav, fills)
            wins = {w: window_stats(nav, a, b) for w, (a, b) in WINDOWS.items()}
            for w, st in wins.items():
                rows.append(
                    {
                        "book": book,
                        "alpha": alpha,
                        "scope": spec["scope"],
                        "sleeves": ",".join(sleeves) if sleeves else "",
                        "cost_multiple": int(mult),
                        "window": w,
                        "cagr": st.get("cagr"),
                        "max_drawdown": st.get("max_drawdown"),
                        "utility": st.get("utility"),
                        "vol": st.get("vol"),
                        "n_days": st.get("n_days"),
                        "n_fills": to["n_fills"],
                        "fees_tax_sum": to["fees_tax_sum"],
                        "turnover_per_year": to["turnover_per_year"],
                        "mean_e45_exposure": meta.get("mean_e45_exposure"),
                        "exact_t1_ok": bool(meta.get("exact_t1_ok")),
                    }
                )

    metrics = pd.DataFrame(rows)
    metrics.to_csv(OUT / "outputs" / "cheap_protect_cost_metrics.csv", index=False)

    deltas = []
    for mult in COST_MULTS:
        base = metrics[(metrics.book == BOOK_BASE) & (metrics.cost_multiple == mult)]
        for spec in BOOKS:
            book = spec["book"]
            for w in FOCUS:
                b = base[base.window == w]
                c = metrics[
                    (metrics.book == book)
                    & (metrics.cost_multiple == mult)
                    & (metrics.window == w)
                ]
                if b.empty or c.empty:
                    continue
                b0, c0 = b.iloc[0], c.iloc[0]
                dlt = deltas_vs_base(
                    {
                        "cagr": b0["cagr"],
                        "max_drawdown": b0["max_drawdown"],
                    },
                    {
                        "cagr": c0["cagr"],
                        "max_drawdown": c0["max_drawdown"],
                    },
                )
                deltas.append(
                    {
                        "book": book,
                        "alpha": float(spec["alpha"]),
                        "scope": spec["scope"],
                        "sleeves": ",".join(spec["sleeves"]) if spec["sleeves"] else "",
                        "cost_multiple": int(mult),
                        "window": w,
                        "mdd_improve_pp": dlt["mdd_improve_pp"],
                        "cagr_giveback_pp": dlt["cagr_giveback_pp"],
                        "score": dlt["score"],
                        "turnover_per_year": c0["turnover_per_year"],
                        "fees_tax_sum": c0["fees_tax_sum"],
                        "n_fills": c0["n_fills"],
                        "book_cagr": c0["cagr"],
                        "base_cagr": b0["cagr"],
                        "book_mdd": c0["max_drawdown"],
                        "base_mdd": b0["max_drawdown"],
                    }
                )
    delta_df = pd.DataFrame(deltas)
    delta_df.to_csv(OUT / "outputs" / "cheap_protect_cost_deltas.csv", index=False)

    # Held-out ranking among protect books (exclude BASE) at each cost
    preferred_by_cost = {}
    for mult in COST_MULTS:
        held = delta_df[
            (delta_df.window == "heldout_2019_plus")
            & (delta_df.cost_multiple == mult)
            & (delta_df.book != BOOK_BASE)
        ].sort_values("score", ascending=False)
        preferred_by_cost[str(mult)] = None if held.empty else held.iloc[0].to_dict()

    # Survival: score≥0 and MDD>0 across cost × for each protect book
    survival = []
    for spec in BOOKS:
        if spec["book"] == BOOK_BASE:
            continue
        for mult in COST_MULTS:
            for w in ("heldout_2019_plus", "sealed_2023_plus"):
                r = delta_df[
                    (delta_df.book == spec["book"])
                    & (delta_df.cost_multiple == mult)
                    & (delta_df.window == w)
                ].iloc[0]
                survival.append(
                    {
                        "book": spec["book"],
                        "alpha": float(spec["alpha"]),
                        "scope": spec["scope"],
                        "cost_multiple": int(mult),
                        "window": w,
                        "mdd_improve_pp": r["mdd_improve_pp"],
                        "cagr_giveback_pp": r["cagr_giveback_pp"],
                        "score": r["score"],
                        "score_nonneg": r["score"] is not None and r["score"] >= 0,
                        "mdd_still_helps": r["mdd_improve_pp"] is not None
                        and r["mdd_improve_pp"] > 0,
                    }
                )

    # Sleeve vs ALL at same α=0.05 under cost stress (held-out)
    sleeve_vs_all = []
    for mult in COST_MULTS:
        all05 = delta_df[
            (delta_df.book == BOOK_BLEND_A05)
            & (delta_df.cost_multiple == mult)
            & (delta_df.window == "heldout_2019_plus")
        ].iloc[0]
        fin05 = delta_df[
            (delta_df.book == "FIN_ONLY_A05")
            & (delta_df.cost_multiple == mult)
            & (delta_df.window == "heldout_2019_plus")
        ].iloc[0]
        sleeve_vs_all.append(
            {
                "cost_multiple": int(mult),
                "all_score": all05["score"],
                "fin_only_score": fin05["score"],
                "fin_beats_all": fin05["score"] is not None
                and all05["score"] is not None
                and fin05["score"] > all05["score"],
                "all_giveback_pp": all05["cagr_giveback_pp"],
                "fin_giveback_pp": fin05["cagr_giveback_pp"],
                "all_mdd_improve_pp": all05["mdd_improve_pp"],
                "fin_mdd_improve_pp": fin05["mdd_improve_pp"],
            }
        )

    held1_pref = preferred_by_cost.get("1")
    cheap_survives_3x = all(
        s["score_nonneg"] and s["mdd_still_helps"]
        for s in survival
        if s["window"] == "heldout_2019_plus"
        and s["cost_multiple"] == 3
        and s["book"] in {BOOK_BLEND_A05, "FIN_ONLY_A05", "SLEEVE_FIN_ONLY_A10", "FIN_0050_A05"}
    )

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PAPER_ONLY",
        "ballot": "E45 PAPER cheap-protect × cost × data-clean",
        "profile": E45_PROFILE_DEFAULT,
        "claim_status": CLAIM_STATUS,
        "books": [b["book"] for b in BOOKS],
        "cost_multiples": list(COST_MULTS),
        "fee_keys_scaled": list(FEE_KEYS),
        "score_formula": "mdd_improve_pp - 0.5 * abs(cagr_giveback_pp)",
        "market_path": str(MARKET_PATH.relative_to(ROOT)),
        "div_path": str(DIV_PATH.relative_to(ROOT)),
        "preferred_heldout_by_cost": preferred_by_cost,
        "heldout_1x_preferred": held1_pref,
        "sleeve_vs_all_heldout": sleeve_vs_all,
        "survival": survival,
        "cheap_forms_survive_heldout_3x": cheap_survives_3x,
        "data_qc_0050": data_qc,
        "soft_frozen": "KEEP",
        "live_default": "KEEP",
        "live_stitch": "FORBIDDEN",
        "high_beta_observe": "DRAFT_NOT_OPEN",
        "observe_sleeves_unchanged": True,
        "non_actions": [
            "No Soft-Frozen / DEFAULT / stitch / HIGH_BETA ballot",
            "No invented replacement for retired claimed-MDD narrative",
            "No e21 primary rewrite from C1 DRIFT alone",
        ],
    }
    (OUT / "reports" / "e45_cheap_protect_cost_data.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )
    (RESEARCH / "E45_CHEAP_PROTECT_COST_DATA.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )

    lines = [
        "# E45 PAPER Cheap-Protect × Cost Realism × Data-Clean",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Status: **PAPER ONLY** — Soft-Frozen **KEEP**; DEFAULT **KEEP**; stitch **FORBIDDEN**; "
        "HIGH_BETA observe **DRAFT / NOT OPEN**; observe sleeves unchanged.",
        "",
        "## Thesis",
        "",
        "Remaining E45 research lever is **cheaper protection** (mild A05 / sleeve-local), "
        "not denser mild-α grids or crisis gates. Stress those forms under **realistic cost ×** "
        "and keep **0050 history QC** on adj_close with C1 quarantine.",
        "",
        "## Setup",
        "",
        f"- Profile: frozen `{E45_PROFILE_DEFAULT}`",
        f"- Books: `{', '.join(b['book'] for b in BOOKS)}`",
        f"- Cost multiples: {', '.join(str(m) + '×' for m in COST_MULTS)} on `{', '.join(FEE_KEYS)}`",
        "- Score: `mdd_improve_pp − 0.5·|cagr_giveback_pp|` vs BASE at same cost ×",
        "",
        "## Data clean — 0050 C1 quarantine + adj_close QC",
        "",
        f"- QC status: **`{data_qc['status']}`**",
        f"- Prefer path: `{data_qc.get('prefer_path')}` (raw-close C1 is spike-sensitive)",
        f"- Quarantine dates: `{', '.join(data_qc.get('quarantine_dates') or [])}`",
        f"- Spikes vs adj (|Δret|>{SPIKE_ABS_RET_PP:.0%}): **{data_qc.get('n_spikes', 0)}** "
        f"(on quarantine: {len(data_qc.get('spikes_on_quarantine') or [])}; "
        f"extra: {len(data_qc.get('extra_spikes_beyond_quarantine') or [])})",
        "- Phase C root class: `UNADJUSTED_CLOSE_SPIKE` — **no e21 primary rewrite**",
        "",
        "| Date | close | adj_close | close_ret | adj_ret |",
        "|---|---:|---:|---:|---:|",
    ]
    for r in data_qc.get("quarantine_detail") or []:
        if not r.get("present"):
            lines.append(f"| {r['date']} | n/a | n/a | n/a | n/a |")
            continue
        adj = "n/a" if r.get("adj_close") is None else f"{r['adj_close']:.4f}"
        cr = "n/a" if r.get("close_ret") is None else f"{r['close_ret']:+.2%}"
        ar = "n/a" if r.get("adj_ret") is None else f"{r['adj_ret']:+.2%}"
        lines.append(
            f"| {r['date']} | {r['close']:.2f} | {adj} | {cr} | {ar} |"
        )

    lines += [
        "",
        "## Held-out deltas vs BASE (cheap forms × cost)",
        "",
        "| Book | Scope | α | ×cost | MDD Δpp | Giveback pp | Score | TO/yr | fees |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    sub = delta_df[delta_df.window == "heldout_2019_plus"].sort_values(
        ["cost_multiple", "alpha", "book"]
    )
    for _, r in sub.iterrows():
        scope = r["scope"] or "—"
        to = "n/a" if pd.isna(r["turnover_per_year"]) else f"{r['turnover_per_year']:.3f}"
        fees = "n/a" if pd.isna(r["fees_tax_sum"]) else f"{r['fees_tax_sum']:.0f}"
        lines.append(
            f"| {r['book']} | {scope} | {r['alpha']:.2f} | {r['cost_multiple']} | "
            f"{pp(r['mdd_improve_pp'])} | {pp(r['cagr_giveback_pp'])} | {pp(r['score'])} | "
            f"{to} | {fees} |"
        )

    lines += [
        "",
        "## Sealed deltas vs BASE (cheap forms × cost)",
        "",
        "| Book | Scope | α | ×cost | MDD Δpp | Giveback pp | Score |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    sealed = delta_df[delta_df.window == "sealed_2023_plus"].sort_values(
        ["cost_multiple", "score"], ascending=[True, False]
    )
    for _, r in sealed.iterrows():
        scope = r["scope"] or "—"
        lines.append(
            f"| {r['book']} | {scope} | {r['alpha']:.2f} | {r['cost_multiple']} | "
            f"{pp(r['mdd_improve_pp'])} | {pp(r['cagr_giveback_pp'])} | {pp(r['score'])} |"
        )

    lines += [
        "",
        "## FIN_ONLY_A05 vs BLEND_E45_A05 (held-out, by cost ×)",
        "",
        "| ×cost | ALL score | FIN_ONLY score | FIN beats ALL? | ALL giveback | FIN giveback |",
        "|---:|---:|---:|:---:|---:|---:|",
    ]
    for r in sleeve_vs_all:
        lines.append(
            f"| {r['cost_multiple']} | {pp(r['all_score'])} | {pp(r['fin_only_score'])} | "
            f"{yn(r['fin_beats_all'])} | {pp(r['all_giveback_pp'])} | {pp(r['fin_giveback_pp'])} |"
        )

    lines += [
        "",
        "## Survival (held-out): score≥0 and MDD helps",
        "",
        "| Book | α | ×cost | MDD Δpp | Giveback | Score | score≥0 | MDD>0 |",
        "|---|---:|---:|---:|---:|---:|:---:|:---:|",
    ]
    for s in survival:
        if s["window"] != "heldout_2019_plus":
            continue
        lines.append(
            f"| {s['book']} | {s['alpha']:.2f} | {s['cost_multiple']} | "
            f"{pp(s['mdd_improve_pp'])} | {pp(s['cagr_giveback_pp'])} | {pp(s['score'])} | "
            f"{yn(s['score_nonneg'])} | {yn(s['mdd_still_helps'])} |"
        )

    pref1 = held1_pref or {}
    lines += [
        "",
        "## Read-through (paper)",
        "",
        f"1. Held-out @1× preferred among protect books: "
        f"**`{pref1.get('book', 'n/a')}`** "
        f"(score {pp(pref1.get('score'))}; scope={pref1.get('scope')}).",
        f"2. Cheap forms survive held-out @3× (score≥0 & MDD>0 for A05/sleeve set): "
        f"**{'YES' if cheap_survives_3x else 'NO'}**.",
        (
            "3. **FIN_ONLY_A05 beats BLEND_E45_A05** on held-out score at every cost × "
            f"({yn(all(r['fin_beats_all'] for r in sleeve_vs_all))}) — prefer sleeve-local "
            "over whole-book mild α for giveback control."
        ),
        f"4. Data QC `{data_qc['status']}` — keep C1 quarantine + adj_close preference; "
        "do not rewrite e21 primary.",
        "5. Does **not** open Soft-Frozen / DEFAULT / stitch / HIGH_BETA ballots.",
        "",
        "## Governance",
        "",
        "- Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN · HIGH_BETA DRAFT/NOT OPEN",
        f"- Claimed MDD status: `{CLAIM_STATUS}` — no invented replacement",
        "",
        "## Reproduce",
        "",
        "```bash",
        "python3 scripts/e45_cheap_protect_cost_data_paper.py",
        "```",
        "",
        f"Repro: `repro/e45-cheap-protect-cost-data/` · Market: `{MARKET_PATH.relative_to(ROOT)}`",
        "",
    ]
    md = "\n".join(lines)
    (OUT / "reports" / "e45_cheap_protect_cost_data.md").write_text(md + "\n")
    (RESEARCH / "E45_CHEAP_PROTECT_COST_DATA.md").write_text(md + "\n")
    (OPS / "E45_CHEAP_PROTECT_COST_DATA.md").write_text(
        "\n".join(
            [
                "# E45 PAPER Cheap-Protect × Cost × Data-Clean — Ops pointer",
                "",
                "Ballot: `E45 PAPER cheap-protect × cost × data-clean` — **PAPER ONLY**",
                "",
                "Primary: `research/e45/E45_CHEAP_PROTECT_COST_DATA.md`",
                "Repro: `repro/e45-cheap-protect-cost-data/`",
                "0050 QC: `repro/e45-cheap-protect-cost-data/outputs/0050_quarantine_adj_qc.json`",
                "",
                "```bash",
                "python3 scripts/e45_cheap_protect_cost_data_paper.py",
                "```",
                "",
                "Governance: Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN · "
                "HIGH_BETA DRAFT/NOT OPEN · no e21 primary rewrite",
                "",
            ]
        )
    )
    print("done", flush=True)
    print(f"heldout_1x_preferred={pref1.get('book')} score={pref1.get('score')}", flush=True)
    print(f"data_qc={data_qc['status']}", flush=True)


if __name__ == "__main__":
    main()
