#!/usr/bin/env python3
"""E45 next research batch (paper only).

1) Non-COVID multi-event search with alternate levers
   (TEL_ONLY / FIN+0050 denser α / E1_BINARY / crisis-gated blend).
   Does not re-run already-failed mild ALL / FIN_ONLY / HIGH_BETA grids.
2) COVID-ex held-out KPI for every challenger in this batch.
3) Observe trailing PAUSE diagnostics on OPERATING dual-paper ledgers.

Governance unchanged:
  Soft-Frozen [0.50, 0.95] KEEP · DEFAULT E22_v2s_tw KEEP · stitch FORBIDDEN ·
  claimed −13.16% RETIRED_HISTORICAL_NARRATIVE · HIGH_BETA stays DRAFT.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from e16_soft_frozen_base import SOFT_FROZEN_FIN_CLIP
from e45_paper_harness import (
    BOOK_BASE,
    BOOK_BLEND_A05,
    BOOK_BLEND_A25,
    BOOK_FULL,
    CLAIM_STATUS,
    E45_PROFILE_DEFAULT,
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

OUT = ROOT / "repro/e45-next-research-batch"
OPS = ROOT / "research/ops"
E45_DIR = ROOT / "research/e45"

CRISIS_YEARS = (2015, 2018, 2020, 2022)
NONCOVID_YEARS = (2015, 2018, 2022)
HELP_MIN_PP = 0.25
ALERT_PP = 3.0
PAUSE_PP = 5.0

OBSERVE_NAV = {
    "CHAL_E45_E3": {
        "base": ROOT / "repro/e45-dual-paper-observe/outputs/base_e16_e18_e22_v2s_daily_nav.csv",
        "chal": ROOT / "repro/e45-dual-paper-observe/outputs/chal_e45_e3_daily_nav.csv",
        "book": BOOK_FULL,
    },
    "BLEND_E45_A25": {
        "base": ROOT / "repro/e45-blend025-dual-paper-observe/outputs/base_e16_e18_e22_v2s_daily_nav.csv",
        "chal": ROOT / "repro/e45-blend025-dual-paper-observe/outputs/blend_e45_a25_daily_nav.csv",
        "book": BOOK_BLEND_A25,
    },
    "BLEND_E45_A05": {
        "base": ROOT / "repro/e45-blend005-dual-paper-observe/outputs/base_e16_e18_e22_v2s_daily_nav.csv",
        "chal": ROOT / "repro/e45-blend005-dual-paper-observe/outputs/blend_e45_a05_daily_nav.csv",
        "book": BOOK_BLEND_A05,
    },
    "SLEEVE_FIN_ONLY_A10": {
        "base": ROOT / "repro/e45-sleeve-local-dual-paper-observe/outputs/base_e16_e18_e22_v2s_daily_nav.csv",
        "chal": ROOT / "repro/e45-sleeve-local-dual-paper-observe/outputs/sleeve_fin_only_a10_daily_nav.csv",
        "book": "SLEEVE_FIN_ONLY_A10",
    },
}

ALT_SPECS: list[dict] = [
    {"book": "TEL_ONLY_A05", "alpha": 0.05, "sleeves": ("Telecom",), "profile": E45_PROFILE_DEFAULT, "gate": False},
    {"book": "TEL_ONLY_A10", "alpha": 0.10, "sleeves": ("Telecom",), "profile": E45_PROFILE_DEFAULT, "gate": False},
    {"book": "TEL_ONLY_A15", "alpha": 0.15, "sleeves": ("Telecom",), "profile": E45_PROFILE_DEFAULT, "gate": False},
    {"book": "FIN0050_A03", "alpha": 0.03, "sleeves": SLEEVE_FIN_0050, "profile": E45_PROFILE_DEFAULT, "gate": False},
    {"book": "FIN0050_A07", "alpha": 0.07, "sleeves": SLEEVE_FIN_0050, "profile": E45_PROFILE_DEFAULT, "gate": False},
    {"book": "FIN0050_A12", "alpha": 0.12, "sleeves": SLEEVE_FIN_0050, "profile": E45_PROFILE_DEFAULT, "gate": False},
    {"book": "FIN0050_A15", "alpha": 0.15, "sleeves": SLEEVE_FIN_0050, "profile": E45_PROFILE_DEFAULT, "gate": False},
    {"book": "E1BIN_A05", "alpha": 0.05, "sleeves": None, "profile": "E1_BINARY", "gate": False},
    {"book": "E1BIN_A10", "alpha": 0.10, "sleeves": None, "profile": "E1_BINARY", "gate": False},
    {"book": "E1BIN_A25", "alpha": 0.25, "sleeves": None, "profile": "E1_BINARY", "gate": False},
    {"book": "GATE085_A10", "alpha": 0.10, "sleeves": None, "profile": E45_PROFILE_DEFAULT, "gate": True, "gate_thr": 0.85},
    {"book": "GATE085_A25", "alpha": 0.25, "sleeves": None, "profile": E45_PROFILE_DEFAULT, "gate": True, "gate_thr": 0.85},
    {"book": "GATE090_FIN_A10", "alpha": 0.10, "sleeves": SLEEVE_FIN_ONLY, "profile": E45_PROFILE_DEFAULT, "gate": True, "gate_thr": 0.90},
    {"book": "REF_BLEND_E45_A05", "alpha": 0.05, "sleeves": None, "profile": E45_PROFILE_DEFAULT, "gate": False, "ref": True},
    {"book": "REF_FIN_ONLY_A10", "alpha": 0.10, "sleeves": SLEEVE_FIN_ONLY, "profile": E45_PROFILE_DEFAULT, "gate": False, "ref": True},
    {"book": "REF_CHAL_E3", "alpha": 1.00, "sleeves": None, "profile": E45_PROFILE_DEFAULT, "gate": False, "ref": True},
]


def fmt(x, digits: int = 2) -> str:
    if x is None or (isinstance(x, float) and (np.isnan(x) or np.isinf(x))):
        return "n/a"
    return f"{x:+.{digits}f}"


def year_mdd(nav: pd.DataFrame, year: int) -> float | None:
    d = nav.copy()
    d["date"] = pd.to_datetime(d["date"])
    part = d[d["date"].dt.year == year].reset_index(drop=True)
    if len(part) < 20:
        return None
    path = part["nav"].to_numpy(float)
    peak = np.maximum.accumulate(path)
    return float(np.min(path / peak - 1.0))


def year_mdd_improve_pp(base_nav: pd.DataFrame, chal_nav: pd.DataFrame, year: int) -> float | None:
    b, c = year_mdd(base_nav, year), year_mdd(chal_nav, year)
    if b is None or c is None:
        return None
    return (abs(b) - abs(c)) * 100.0


def covid_ex_heldout_stats(nav: pd.DataFrame) -> dict:
    d = nav.copy()
    d["date"] = pd.to_datetime(d["date"])
    start = pd.Timestamp(WINDOWS_STANDARD["heldout_2019_plus"][0])
    d = d[(d["date"] >= start) & (d["date"].dt.year != 2020)].reset_index(drop=True)
    if len(d) < 60:
        return {"cagr": None, "max_drawdown": None, "n_days": int(len(d))}
    tmp = pd.DataFrame({"date": d["date"].dt.date, "nav": d["nav"].to_numpy(float)})
    tmp["nav"] = tmp["nav"] / float(tmp["nav"].iloc[0])
    out = window_stats(tmp, None, None, min_days=60)
    out["n_days"] = int(len(tmp))
    return out


def gated_exposure(full: pd.Series, alpha: float, thr: float) -> pd.Series:
    blend = blend_exposure(full, alpha)
    assert blend is not None
    out = pd.Series(1.0, index=full.index, dtype=float)
    mask = full.reindex(out.index).fillna(1.0) < float(thr)
    out.loc[mask] = blend.reindex(out.index).fillna(1.0).loc[mask]
    return out


def build_exposure(market: pd.DataFrame, spec: dict, cache: dict) -> pd.Series | None:
    prof = spec["profile"]
    if prof not in cache:
        cache[prof] = e45_full_exposure(market, profile=prof)
    full = cache[prof]
    alpha = float(spec["alpha"])
    if spec.get("gate"):
        return gated_exposure(full, alpha, float(spec.get("gate_thr", 0.85)))
    return blend_exposure(full, alpha)


def gate_of(giveback_pp) -> str:
    if giveback_pp is None:
        return "INSUFFICIENT"
    if giveback_pp > PAUSE_PP:
        return "PAUSE_REVIEW"
    if giveback_pp > ALERT_PP:
        return "ALERT"
    return "PASS"


def cagr_series(nav: pd.Series):
    if len(nav) < 2 or float(nav.iloc[0]) <= 0:
        return None
    years = len(nav.pct_change().dropna()) / 252.0
    if years <= 0:
        return None
    return float((nav.iloc[-1] / nav.iloc[0]) ** (1.0 / years) - 1.0)


def mdd_series(nav: pd.Series):
    if len(nav) < 2:
        return None
    return float((nav / nav.cummax() - 1.0).min())


def giveback_at(base: pd.DataFrame, chal: pd.DataFrame, asof: pd.Timestamp, window: str) -> dict:
    start = pd.Timestamp(asof.year, 1, 1) if window == "ytd" else asof - pd.Timedelta(days=365)
    b = base[(base["date"] >= start) & (base["date"] <= asof)].reset_index(drop=True)
    c = chal[(chal["date"] >= start) & (chal["date"] <= asof)].reset_index(drop=True)
    if len(b) < 20 or len(c) < 20:
        return {
            "asof": asof.date().isoformat(),
            "window": window,
            "n_days": int(min(len(b), len(c))),
            "cagr_giveback_pp": None,
            "mdd_improve_pp": None,
            "gate": "INSUFFICIENT",
        }
    bn = b["nav"] / float(b["nav"].iloc[0])
    cn = c["nav"] / float(c["nav"].iloc[0])
    bc, cc = cagr_series(bn), cagr_series(cn)
    bm, cm = mdd_series(bn), mdd_series(cn)
    gb = None if bc is None or cc is None else (bc - cc) * 100.0
    mi = None if bm is None or cm is None else (abs(bm) - abs(cm)) * 100.0
    return {
        "asof": asof.date().isoformat(),
        "window": window,
        "n_days": int(min(len(b), len(c))),
        "cagr_giveback_pp": gb,
        "mdd_improve_pp": mi,
        "gate": gate_of(gb),
    }


def month_ends(nav: pd.DataFrame):
    d = nav.copy()
    d["ym"] = d["date"].dt.to_period("M")
    ends = d.groupby("ym", sort=True)["date"].max()
    return [ts for ts in ends.tolist() if ts >= pd.Timestamp("2023-01-01")]


def observe_pause_diagnostics() -> tuple[pd.DataFrame, dict]:
    rows: list[dict] = []
    summary: dict = {}
    for sleeve, meta in OBSERVE_NAV.items():
        if not meta["base"].exists() or not meta["chal"].exists():
            summary[sleeve] = {"ok": False, "reason": "missing_nav"}
            continue
        base = pd.read_csv(meta["base"])
        chal = pd.read_csv(meta["chal"])
        base["date"] = pd.to_datetime(base["date"])
        chal["date"] = pd.to_datetime(chal["date"])
        base = base.sort_values("date").reset_index(drop=True)
        chal = chal.sort_values("date").reset_index(drop=True)
        asofs = month_ends(chal)
        for asof in asofs:
            for w in ("ytd", "trailing_1y"):
                row = giveback_at(base, chal, asof, w)
                row.update({"sleeve": sleeve, "book": meta["book"]})
                rows.append(row)
        tip = asofs[-1] if asofs else None
        hist = [r for r in rows if r["sleeve"] == sleeve]
        tip_ytd = next(
            (r for r in hist if tip is not None and r["asof"] == tip.date().isoformat() and r["window"] == "ytd"),
            None,
        )
        tip_1y = next(
            (
                r
                for r in hist
                if tip is not None and r["asof"] == tip.date().isoformat() and r["window"] == "trailing_1y"
            ),
            None,
        )
        by_asof: dict[str, dict] = {}
        for r in hist:
            by_asof.setdefault(r["asof"], {})[r["window"]] = r
        first_clean = None
        near_clean = None
        months_pause_both = 0
        for a, gates in sorted(by_asof.items()):
            y = gates.get("ytd", {})
            t = gates.get("trailing_1y", {})
            if y.get("gate") == "PASS" and t.get("gate") == "PASS" and first_clean is None:
                first_clean = a
            if y.get("gate") in ("PASS", "ALERT") and t.get("gate") in ("PASS", "ALERT") and near_clean is None:
                near_clean = a
            if y.get("gate") == "PAUSE_REVIEW" and t.get("gate") == "PAUSE_REVIEW":
                months_pause_both += 1
        tip_need = {}
        for label, tip_row in (("ytd", tip_ytd), ("trailing_1y", tip_1y)):
            if not tip_row or tip_row.get("cagr_giveback_pp") is None:
                tip_need[label] = None
            else:
                tip_need[label] = {
                    "current_giveback_pp": tip_row["cagr_giveback_pp"],
                    "pp_above_alert": max(0.0, float(tip_row["cagr_giveback_pp"]) - ALERT_PP),
                    "pp_above_pause": max(0.0, float(tip_row["cagr_giveback_pp"]) - PAUSE_PP),
                    "gate": tip_row["gate"],
                }
        ytd_hist = [r for r in hist if r["window"] == "ytd"]
        y1_hist = [r for r in hist if r["window"] == "trailing_1y"]
        summary[sleeve] = {
            "ok": True,
            "book": meta["book"],
            "n_month_ends": len(asofs),
            "tip_asof": tip.date().isoformat() if tip is not None else None,
            "tip_ytd_gate": tip_ytd["gate"] if tip_ytd else None,
            "tip_trailing_1y_gate": tip_1y["gate"] if tip_1y else None,
            "share_pause_ytd": float(np.mean([r["gate"] == "PAUSE_REVIEW" for r in ytd_hist])) if ytd_hist else None,
            "share_pause_1y": float(np.mean([r["gate"] == "PAUSE_REVIEW" for r in y1_hist])) if y1_hist else None,
            "first_clean_both_asof": first_clean,
            "first_near_clean_both_asof": near_clean,
            "months_both_pause": months_pause_both,
            "tip_need": tip_need,
            "stitch": "FORBIDDEN",
        }
    return pd.DataFrame(rows), summary


def publish_all(name: str, text: str, out_r: Path) -> None:
    (out_r / name).write_text(text)
    (OPS / name).write_text(text)
    (E45_DIR / name).write_text(text)


def write_reports(
    *,
    generated: str,
    help_df: pd.DataFrame,
    window_df: pd.DataFrame,
    qualify_df: pd.DataFrame,
    pause_summary: dict,
    payload: dict,
) -> None:
    out_r = OUT / "reports"
    for d in (OUT / "outputs", out_r, OPS, E45_DIR):
        d.mkdir(parents=True, exist_ok=True)

    q_incl = qualify_df[qualify_df["rule"] == "incl_covid"]
    q_strict = qualify_df[qualify_df["rule"] == "strict_noncovid"]

    lines = [
        "# E45 Non-COVID Multi-Event — Alternate Levers",
        "",
        f"Generated: `{generated}`",
        "Status: **PAPER ONLY** — Soft-Frozen **KEEP** · DEFAULT **`E22_v2s_tw` KEEP** · stitch **FORBIDDEN**",
        f"Claimed −13.16%: **`{CLAIM_STATUS}`** (do not invent a replacement)",
        "",
        "## Scope",
        "",
        "Beyond already-failed mild ALL / FIN_ONLY / HIGH_BETA grids:",
        "TEL_ONLY densify · FIN+0050 denser α · E1_BINARY overlay · crisis-gated blend.",
        "",
        f"Help threshold: MDD help > **{HELP_MIN_PP} pp**.",
        "- `incl_covid`: ≥2 of {2015,2018,2020,2022}",
        "- `strict_noncovid`: ≥2 of {2015,2018,2022}",
        "",
        "## Qualifiers",
        "",
        f"- incl_covid qualifiers: **{int(q_incl['qualifies'].sum())}**",
        f"- strict_noncovid qualifiers: **{int(q_strict['qualifies'].sum())}**",
        "",
        "| Book | Rule | Years helped | N | Held-out score | COVID-ex held-out | Sealed score | Qualifies? |",
        "|---|---|---|---:|---:|---:|---:|:---:|",
    ]
    for _, r in qualify_df.sort_values(["rule", "book"]).iterrows():
        lines.append(
            f"| `{r['book']}` | {r['rule']} | {r['years_helped']} | {int(r['n_years'])} | "
            f"{fmt(r['heldout_score'])} | {fmt(r['covid_ex_heldout_score'])} | {fmt(r['sealed_score'])} | "
            f"{'YES' if r['qualifies'] else 'NO'} |"
        )
    lines += [
        "",
        "## Year MDD help (pp vs BASE)",
        "",
        "| Book | 2015 | 2018 | 2020 | 2022 |",
        "|---|---:|---:|---:|---:|",
    ]
    for bid in sorted(help_df["book"].unique()):
        cells = []
        for y in CRISIS_YEARS:
            sub = help_df[(help_df["book"] == bid) & (help_df["year"] == y)]
            cells.append(fmt(float(sub.iloc[0]["mdd_improve_pp"])) if len(sub) else "n/a")
        lines.append(f"| `{bid}` | " + " | ".join(cells) + " |")
    lines += [
        "",
        "## Read",
        "",
        "- 2020=COVID mega-DD help remains **expected**; honesty = non-COVID multi-event + COVID-ex held-out.",
        "- No Soft-Frozen / DEFAULT / stitch change. HIGH_BETA stays DRAFT.",
        "",
        f"Label: `E45_NONCOVID_MULTIEVENT_ALT_{generated[:10]}__STITCH_FORBIDDEN`",
        "",
    ]
    publish_all("E45_NONCOVID_MULTIEVENT_ALT_LEVERS.md", "\n".join(lines), out_r)

    best = window_df.dropna(subset=["covid_ex_heldout_score"]).sort_values(
        "covid_ex_heldout_score", ascending=False
    )
    top = best.iloc[0]["book"] if len(best) else "n/a"
    top_s = float(best.iloc[0]["covid_ex_heldout_score"]) if len(best) else None
    lines = [
        "# E45 COVID-Ex Held-Out KPI",
        "",
        f"Generated: `{generated}`",
        "Status: **PAPER KPI** — Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN",
        "",
        "Definition: `heldout_2019_plus` with **calendar-2020 removed**, NAV renormalized.",
        "Score = `mdd_improve_pp − 0.5·|cagr_giveback_pp|` vs BASE on the same COVID-ex window.",
        "",
        "| Book | Family | Held-out score | COVID-ex held-out score | Δ (ex − std) | Sealed score |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for _, r in window_df.sort_values("covid_ex_heldout_score", ascending=False).iterrows():
        delta = None
        if r["heldout_score"] is not None and r["covid_ex_heldout_score"] is not None:
            delta = float(r["covid_ex_heldout_score"]) - float(r["heldout_score"])
        lines.append(
            f"| `{r['book']}` | {r['family']} | {fmt(r['heldout_score'])} | "
            f"{fmt(r['covid_ex_heldout_score'])} | {fmt(delta)} | {fmt(r['sealed_score'])} |"
        )
    lines += [
        "",
        f"**Least-bad COVID-ex held-out:** `{top}` @ {fmt(top_s)}"
        + (" (still negative — no positive COVID-ex challenger)" if top_s is not None and top_s < 0 else ""),
        "",
        "## Binding use",
        "",
        "Any future OPEN-observe ballot densify **must** report both standard held-out and COVID-ex held-out scores.",
        "",
        f"Label: `E45_COVID_EX_HELDOUT_KPI_{generated[:10]}__STITCH_FORBIDDEN`",
        "",
    ]
    publish_all("E45_COVID_EX_HELDOUT_KPI.md", "\n".join(lines), out_r)

    lines = [
        "# E45 Observe Trailing PAUSE Diagnostics",
        "",
        f"Generated: `{generated}`",
        "Status: **OBSERVE DIAGNOSTIC ONLY** — does **not** authorize stitch",
        "Soft-Frozen KEEP · DEFAULT KEEP · stitch **FORBIDDEN**",
        "",
        "Gates: YTD / trailing_1y CAGR giveback vs BASE — ALERT >3pp · PAUSE_REVIEW >5pp.",
        "",
        "## Tip snapshot",
        "",
        "| Sleeve | Tip asof | YTD gate | 1y gate | Share PAUSE YTD | Share PAUSE 1y | First clean both | First near-clean | Months both PAUSE |",
        "|---|---|---|---|---:|---:|---|---|---:|",
    ]
    for sleeve, s in pause_summary.items():
        if not s.get("ok"):
            lines.append(f"| `{sleeve}` | n/a | missing | missing | n/a | n/a | n/a | n/a | n/a |")
            continue
        lines.append(
            f"| `{sleeve}` | {s['tip_asof']} | **{s['tip_ytd_gate']}** | **{s['tip_trailing_1y_gate']}** | "
            f"{s['share_pause_ytd']:.0%} | {s['share_pause_1y']:.0%} | "
            f"{s['first_clean_both_asof'] or 'none yet'} | {s['first_near_clean_both_asof'] or 'none yet'} | "
            f"{s['months_both_pause']} |"
        )
    lines += [
        "",
        "## Tip giveback vs ALERT/PAUSE thresholds",
        "",
        "| Sleeve | Window | Current giveback pp | pp above ALERT(3) | pp above PAUSE(5) | Gate |",
        "|---|---|---:|---:|---:|---|",
    ]
    for sleeve, s in pause_summary.items():
        if not s.get("ok"):
            continue
        for w, need in (s.get("tip_need") or {}).items():
            if not need:
                lines.append(f"| `{sleeve}` | {w} | n/a | n/a | n/a | n/a |")
                continue
            lines.append(
                f"| `{sleeve}` | {w} | {fmt(need['current_giveback_pp'])} | "
                f"{fmt(need['pp_above_alert'])} | {fmt(need['pp_above_pause'])} | {need['gate']} |"
            )
    lines += [
        "",
        "## Read",
        "",
        "- Tip PAUSE is **expected** while crisis giveback remains in trailing windows.",
        "- `first_clean_both_asof = none yet` ⇒ **no stitch discussion** from trailing gates.",
        "- Diagnostic only; stitch remains FORBIDDEN until a dedicated second human ACCEPT.",
        "",
        f"Label: `E45_OBSERVE_PAUSE_DIAG_{generated[:10]}__STITCH_FORBIDDEN`",
        "",
    ]
    publish_all("E45_OBSERVE_PAUSE_DIAGNOSTICS.md", "\n".join(lines), out_r)

    n_incl = int(q_incl["qualifies"].sum())
    n_strict = int(q_strict["qualifies"].sum())
    integ = [
        "# E45 Next Research Batch — Integrated (items 1–3)",
        "",
        f"Generated: `{generated}`",
        "Status: **PAPER / OBSERVE DIAG** — Soft-Frozen **KEEP** · DEFAULT **KEEP** · stitch **FORBIDDEN**",
        f"Claimed −13.16%: **`{CLAIM_STATUS}`**",
        "",
        "## What ran",
        "",
        "| # | Item | Artifact |",
        "|---|---|---|",
        "| 1 | Non-COVID multi-event alt levers | `E45_NONCOVID_MULTIEVENT_ALT_LEVERS.md` |",
        "| 2 | COVID-ex held-out KPI | `E45_COVID_EX_HELDOUT_KPI.md` |",
        "| 3 | Observe trailing PAUSE diagnostics | `E45_OBSERVE_PAUSE_DIAGNOSTICS.md` |",
        "",
        "## Cross-cut verdict",
        "",
        f"1. **Multi-event:** incl_covid qualifiers={n_incl}; strict_noncovid qualifiers={n_strict}.",
        f"2. **COVID-ex held-out least-bad:** `{top}` @ {fmt(top_s)}.",
        "3. **Observe:** tip PAUSE still common; no first_clean_both ⇒ stitch still blocked.",
        "",
        "## Explicit non-actions",
        "",
        "- No Soft-Frozen / DEFAULT flip · no live stitch · no −13.16% reinvention · no HIGH_BETA OPEN.",
        "",
        f"Label: `E45_NEXT_RESEARCH_BATCH_{generated[:10]}__STITCH_FORBIDDEN`",
        "",
    ]
    publish_all("E45_NEXT_RESEARCH_BATCH_INTEGRATED.md", "\n".join(integ), out_r)

    (OUT / "outputs" / "next_research_batch_summary.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )
    (OPS / "E45_NEXT_RESEARCH_BATCH_SUMMARY.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n"
    )


def main() -> int:
    out_o = OUT / "outputs"
    out_o.mkdir(parents=True, exist_ok=True)
    generated = datetime.now(timezone.utc).isoformat()

    print("==> (3) observe pause diagnostics", flush=True)
    pause_df, pause_summary = observe_pause_diagnostics()
    pause_df.to_csv(out_o / "observe_pause_timeseries.csv", index=False)
    for sleeve, s in pause_summary.items():
        if s.get("ok"):
            print(
                f"  {sleeve}: tip={s['tip_asof']} ytd={s['tip_ytd_gate']} "
                f"1y={s['tip_trailing_1y_gate']} clean={s['first_clean_both_asof']}",
                flush=True,
            )
        else:
            print(f"  {sleeve}: MISSING", flush=True)

    print("==> load market / features", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, _s, target, regime = e16_features(market)
    exp_cache: dict[str, pd.Series] = {}

    print("==> BASE sim", flush=True)
    base_nav, _bf, _bm = run_early_stack(market, target, regime, dividends, e45_exposure=None)
    books: dict[str, dict] = {
        BOOK_BASE: {"nav": base_nav, "family": "BASE", "alpha": 0.0, "sleeves": None, "ref": False}
    }

    for spec in ALT_SPECS:
        bid = spec["book"]
        print(
            f"sim {bid} alpha={spec['alpha']} sleeves={spec['sleeves']} "
            f"profile={spec['profile']} gate={spec.get('gate')}",
            flush=True,
        )
        exp = build_exposure(market, spec, exp_cache)
        nav, _f, _m = run_early_stack(
            market,
            target,
            regime,
            dividends,
            e45_exposure=exp,
            e45_sleeve_names=spec["sleeves"],
        )
        books[bid] = {
            "nav": nav,
            "family": bid.split("_")[0],
            "alpha": float(spec["alpha"]),
            "sleeves": list(spec["sleeves"]) if spec["sleeves"] else None,
            "ref": bool(spec.get("ref")),
            "profile": spec["profile"],
            "gate": bool(spec.get("gate")),
        }
        nav.to_csv(out_o / f"{bid.lower()}_daily_nav.csv", index=False)

    print("==> crisis help + windows + COVID-ex KPI", flush=True)
    help_rows = []
    window_rows = []
    held_bounds = WINDOWS_STANDARD["heldout_2019_plus"]
    sealed_bounds = WINDOWS_STANDARD["sealed_2023_plus"]
    for bid, pack in books.items():
        if bid == BOOK_BASE:
            continue
        for y in CRISIS_YEARS:
            hp = year_mdd_improve_pp(base_nav, pack["nav"], y)
            if hp is None:
                continue
            help_rows.append({"book": bid, "year": y, "mdd_improve_pp": hp, "is_2020": y == 2020})

        held = window_stats(pack["nav"], held_bounds[0], held_bounds[1])
        sealed = window_stats(pack["nav"], sealed_bounds[0], sealed_bounds[1])
        base_held = window_stats(base_nav, held_bounds[0], held_bounds[1])
        base_sealed = window_stats(base_nav, sealed_bounds[0], sealed_bounds[1])
        d_held = deltas_vs_base(base_held, held)
        d_sealed = deltas_vs_base(base_sealed, sealed)

        cex = covid_ex_heldout_stats(pack["nav"])
        base_cex = covid_ex_heldout_stats(base_nav)
        d_cex = deltas_vs_base(base_cex, cex)

        window_rows.append(
            {
                "book": bid,
                "family": pack["family"],
                "alpha": pack["alpha"],
                "ref_observe": pack["ref"],
                "heldout_score": d_held["score"],
                "heldout_mdd_improve_pp": d_held["mdd_improve_pp"],
                "heldout_cagr_giveback_pp": d_held["cagr_giveback_pp"],
                "covid_ex_heldout_score": d_cex["score"],
                "covid_ex_mdd_improve_pp": d_cex["mdd_improve_pp"],
                "covid_ex_cagr_giveback_pp": d_cex["cagr_giveback_pp"],
                "covid_ex_n_days": cex.get("n_days"),
                "sealed_score": d_sealed["score"],
                "sealed_mdd_improve_pp": d_sealed["mdd_improve_pp"],
                "sealed_cagr_giveback_pp": d_sealed["cagr_giveback_pp"],
            }
        )

    help_df = pd.DataFrame(help_rows)
    window_df = pd.DataFrame(window_rows)
    help_df.to_csv(out_o / "alt_lever_crisis_mdd_improve.csv", index=False)
    window_df.to_csv(out_o / "alt_lever_window_scores.csv", index=False)

    qualify_rows = []
    for _, wr in window_df.iterrows():
        bid = wr["book"]
        g = help_df[help_df["book"] == bid]
        for rule, years in (("incl_covid", CRISIS_YEARS), ("strict_noncovid", NONCOVID_YEARS)):
            helped = sorted(
                int(y)
                for y in years
                if len(g[(g["year"] == y) & (g["mdd_improve_pp"] > HELP_MIN_PP)])
            )
            multi_ok = len(helped) >= 2
            held_ok = wr["heldout_score"] is not None and float(wr["heldout_score"]) > 0
            sealed_ok = wr["sealed_score"] is not None and float(wr["sealed_score"]) > -1.0
            qualify_rows.append(
                {
                    "book": bid,
                    "rule": rule,
                    "years_helped": helped,
                    "n_years": len(helped),
                    "multi_event_ok": multi_ok,
                    "heldout_score": wr["heldout_score"],
                    "covid_ex_heldout_score": wr["covid_ex_heldout_score"],
                    "sealed_score": wr["sealed_score"],
                    "heldout_ok": held_ok,
                    "sealed_ok": sealed_ok,
                    "qualifies": bool(multi_ok and held_ok and sealed_ok),
                }
            )
    qualify_df = pd.DataFrame(qualify_rows)
    qualify_df.to_csv(out_o / "alt_lever_multievent_qualify.csv", index=False)

    payload = {
        "generated_at_utc": generated,
        "claim_status": CLAIM_STATUS,
        "soft_frozen_keep": list(SOFT_FROZEN_FIN_CLIP),
        "default_books_keep": "E22_v2s_tw",
        "stitch": "FORBIDDEN",
        "n_alt_challengers": int((~window_df["ref_observe"]).sum()) if len(window_df) else 0,
        "qualifiers_incl_covid": int(
            qualify_df[(qualify_df.rule == "incl_covid") & (qualify_df.qualifies)].shape[0]
        ),
        "qualifiers_strict_noncovid": int(
            qualify_df[(qualify_df.rule == "strict_noncovid") & (qualify_df.qualifies)].shape[0]
        ),
        "covid_ex_least_bad": (
            window_df.dropna(subset=["covid_ex_heldout_score"])
            .sort_values("covid_ex_heldout_score", ascending=False)
            .head(1)[["book", "covid_ex_heldout_score"]]
            .to_dict("records")
            or [None]
        )[0],
        "observe_pause_summary": pause_summary,
        "artifacts": {
            "alt_levers": "research/ops/E45_NONCOVID_MULTIEVENT_ALT_LEVERS.md",
            "covid_ex_kpi": "research/ops/E45_COVID_EX_HELDOUT_KPI.md",
            "pause_diag": "research/ops/E45_OBSERVE_PAUSE_DIAGNOSTICS.md",
            "integrated": "research/ops/E45_NEXT_RESEARCH_BATCH_INTEGRATED.md",
        },
    }

    write_reports(
        generated=generated,
        help_df=help_df,
        window_df=window_df,
        qualify_df=qualify_df,
        pause_summary=pause_summary,
        payload=payload,
    )
    print(
        f"DONE qualifiers incl={payload['qualifiers_incl_covid']} "
        f"strict={payload['qualifiers_strict_noncovid']} "
        f"covid_ex_least_bad={payload['covid_ex_least_bad']}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
