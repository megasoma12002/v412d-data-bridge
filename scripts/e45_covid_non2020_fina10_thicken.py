#!/usr/bin/env python3
"""E45 paper follow-up #2 + #3.

#2 COVID-framed non-2020 / multi-event empirics
#3 Thicken FIN_ONLY densify around observe lock alpha=0.10

Framing: 2020 is COVID-19 — mega-drawdown there is expected.
Honesty is whether protection shows outside that COVID year/episode.

PAPER ONLY. Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN.
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from e45_paper_harness import (
    BOOK_BASE,
    BOOK_BLEND_A05,
    CLAIM_STATUS,
    E45_PROFILE_DEFAULT,
    ROOT,
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

OUT = ROOT / "repro/e45-covid-non2020-fina10"
RESEARCH = ROOT / "research/e45"
OPS = ROOT / "research/ops"

STRESS_EVENTS = {
    2015: {"tag": "TW_EQUITY_STRESS_2015", "label": "2015 TW equity stress (China/EM spillover)", "covid": False},
    2018: {"tag": "TRADE_WAR_EM_2018", "label": "2018 trade-war / EM stress", "covid": False},
    2020: {"tag": "COVID19_MEGA_DD_2020", "label": "2020 COVID-19 mega-drawdown (expected large story)", "covid": True},
    2022: {"tag": "RATE_INFLATION_2022", "label": "2022 rate / inflation stress", "covid": False},
}
NON_COVID_YEARS = tuple(y for y, m in STRESS_EVENTS.items() if not m["covid"])
COVID_YEAR = 2020
COVID_EPISODE = (date(2020, 1, 20), date(2020, 3, 19))
FIN_ALPHAS = (0.05, 0.08, 0.10, 0.12, 0.15)
COST_MULTS = (1.0, 2.0, 3.0)
ROLL_ENDS = (
    date(2020, 12, 31), date(2021, 12, 31), date(2022, 12, 31),
    date(2023, 12, 31), date(2024, 12, 31), date(2026, 9, 4),
)
HELP_THRESHOLD_PP = 0.25
FOCUS_WINDOWS = ("heldout_2019_plus", "sealed_2023_plus", "full")


def fmt(x, digits=2):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "n/a"
    return f"{x:+.{digits}f}"


def pct(x):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "n/a"
    return f"{x:.0%}"


def year_path_stats(nav: pd.DataFrame, year: int) -> dict:
    d = nav.copy()
    d["date"] = pd.to_datetime(d["date"])
    part = d[d["date"].dt.year == year].reset_index(drop=True)
    if len(part) < 20:
        return {"year": year, "n_days": int(len(part)), "ret": None, "max_drawdown": None, "available": False}
    path = part["nav"].to_numpy(float)
    peak = np.maximum.accumulate(path)
    return {
        "year": year,
        "n_days": int(len(part)),
        "ret": float(path[-1] / path[0] - 1.0),
        "max_drawdown": float(np.min(path / peak - 1.0)),
        "available": True,
    }


def turnover_from_fills(fills: pd.DataFrame, nav: pd.DataFrame) -> dict:
    if fills is None or fills.empty or nav.empty:
        return {"n_fills": 0, "gross_traded": 0.0, "ann_turnover_approx": None}
    if "gross" in fills.columns:
        gross = float(fills["gross"].abs().sum())
    else:
        gross = float((fills["quantity"].abs() * fills["fill_price"]).sum())
    n = nav.copy()
    n["date"] = pd.to_datetime(n["date"])
    years = max((n["date"].iloc[-1] - n["date"].iloc[0]).days / 365.25, 1e-9)
    mean_nav = float(n["nav"].mean())
    ann = (gross / mean_nav / years / 2.0) if mean_nav > 0 else None
    return {"n_fills": int(len(fills)), "gross_traded": gross, "ann_turnover_approx": ann}


def publish(name: str, text: str, out_r: Path) -> None:
    for d in (out_r, RESEARCH, OPS):
        d.mkdir(parents=True, exist_ok=True)
        (d / name).write_text(text, encoding="utf-8")


def main() -> None:
    generated = datetime.now(timezone.utc).isoformat()
    out_o = OUT / "outputs"
    out_r = OUT / "reports"
    out_o.mkdir(parents=True, exist_ok=True)
    out_r.mkdir(parents=True, exist_ok=True)

    print("loading market / features ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, _s, target, regime = e16_features(market)
    e45_full = e45_full_exposure(market, E45_PROFILE_DEFAULT)

    books: dict[str, dict] = {}

    def put(bid, family, alpha, sleeves, cost, nav, fills, meta):
        books[bid] = {
            "book": bid,
            "family": family,
            "alpha": float(alpha),
            "sleeves": list(sleeves) if sleeves else None,
            "cost_multiple": float(cost),
            "nav": nav,
            "fills": fills,
            "meta": meta,
            "windows": {w: window_stats(nav, a, b) for w, (a, b) in WINDOWS_STANDARD.items()},
            "turnover": turnover_from_fills(fills, nav),
        }

    def sim(label, alpha, sleeves, cost=1.0):
        exp = blend_exposure(e45_full, alpha)
        print(f"sim {label} a={alpha} sleeves={sleeves} cost={cost}x ...", flush=True)
        return run_early_stack(
            market, target, regime, dividends,
            e45_exposure=exp, e45_sleeve_names=sleeves, cost_multiple=cost,
        )

    for cost in COST_MULTS:
        print(f"sim BASE cost={cost}x ...", flush=True)
        nav, fills, meta = run_early_stack(
            market, target, regime, dividends, e45_exposure=None, cost_multiple=cost
        )
        put(f"{BOOK_BASE}_C{int(cost)}x", "BASE", 0.0, None, cost, nav, fills, meta)

    base_key = f"{BOOK_BASE}_C1x"
    core = [(BOOK_BLEND_A05, 0.05, None, "ALL"), ("BLEND_E45_A10", 0.10, None, "ALL")]
    for a in FIN_ALPHAS:
        core.append((f"FIN_ONLY_A{int(round(a * 100)):02d}", a, SLEEVE_FIN_ONLY, "FIN_ONLY"))

    for label, alpha, sleeves, family in core:
        nav, fills, meta = sim(label, alpha, sleeves, 1.0)
        put(label, family, alpha, sleeves, 1.0, nav, fills, meta)
        nav.to_csv(out_o / f"{label.lower()}_daily_nav.csv", index=False)

    for label, alpha, sleeves in (
        (BOOK_BLEND_A05, 0.05, None),
        ("FIN_ONLY_A08", 0.08, SLEEVE_FIN_ONLY),
        ("FIN_ONLY_A10", 0.10, SLEEVE_FIN_ONLY),
        ("FIN_ONLY_A12", 0.12, SLEEVE_FIN_ONLY),
    ):
        for cost in (2.0, 3.0):
            key = f"{label}_C{int(cost)}x"
            nav, fills, meta = sim(key, alpha, sleeves, cost)
            put(key, label, alpha, sleeves, cost, nav, fills, meta)

    candidates = [BOOK_BLEND_A05, "BLEND_E45_A10"] + [
        f"FIN_ONLY_A{int(round(a * 100)):02d}" for a in FIN_ALPHAS
    ]

    print("==> (#2) COVID-framed crisis / episode attribution", flush=True)
    crisis_rows = []
    for bid in [base_key] + candidates:
        for y, meta in STRESS_EVENTS.items():
            st = year_path_stats(books[bid]["nav"], y)
            st.update({
                "book": bid, "event_tag": meta["tag"], "event_label": meta["label"],
                "is_covid": meta["covid"], "alpha": books[bid]["alpha"],
                "sleeves": ",".join(books[bid]["sleeves"] or []) or "ALL",
            })
            crisis_rows.append(st)
    crisis_df = pd.DataFrame(crisis_rows)
    crisis_df.to_csv(out_o / "stress_year_book_metrics.csv", index=False)

    help_rows = []
    for bid in candidates:
        for y, meta in STRESS_EVENTS.items():
            b = crisis_df[(crisis_df.book == base_key) & (crisis_df.year == y)].iloc[0]
            c = crisis_df[(crisis_df.book == bid) & (crisis_df.year == y)].iloc[0]
            if not b["available"] or not c["available"]:
                continue
            help_rows.append({
                "book": bid, "year": y, "event_tag": meta["tag"], "event_label": meta["label"],
                "is_covid": meta["covid"],
                "mdd_improve_pp": (abs(float(b["max_drawdown"])) - abs(float(c["max_drawdown"]))) * 100.0,
                "ret_delta_pp": (float(c["ret"]) - float(b["ret"])) * 100.0,
            })
    help_df = pd.DataFrame(help_rows)
    help_df.to_csv(out_o / "stress_year_mdd_improve_vs_base.csv", index=False)

    b_ep = window_stats(books[base_key]["nav"], *COVID_EPISODE, min_days=15)
    ep_rows = []
    for bid in candidates:
        c_ep = window_stats(books[bid]["nav"], *COVID_EPISODE, min_days=15)
        dlt = deltas_vs_base(b_ep, c_ep)
        ep_rows.append({
            "book": bid, "episode": "COVID19_2020-01-20_2020-03-19",
            "base_mdd": b_ep.get("max_drawdown"), "chal_mdd": c_ep.get("max_drawdown"),
            "mdd_improve_pp": dlt["mdd_improve_pp"], "cagr_giveback_pp": dlt["cagr_giveback_pp"],
            "score": dlt["score"], "n_days": c_ep.get("n_days"),
        })
    ep_df = pd.DataFrame(ep_rows)
    ep_df.to_csv(out_o / "covid_episode_mdd_improve.csv", index=False)

    conc = []
    for bid, g in help_df.groupby("book"):
        pos = g[g["mdd_improve_pp"] > 0]
        total_pos = float(pos["mdd_improve_pp"].sum()) if len(pos) else 0.0
        covid_help = float(g.loc[g["is_covid"], "mdd_improve_pp"].sum())
        non_covid_pos = float(pos.loc[~pos["is_covid"], "mdd_improve_pp"].sum()) if len(pos) else 0.0
        years_all = sorted(g.loc[g["mdd_improve_pp"] > HELP_THRESHOLD_PP, "year"].tolist())
        years_non_covid = sorted(g.loc[(~g["is_covid"]) & (g["mdd_improve_pp"] > HELP_THRESHOLD_PP), "year"].tolist())
        conc.append({
            "book": bid,
            "mdd_improve_covid_year_pp": covid_help,
            "mdd_improve_non_covid_positive_pp": non_covid_pos,
            "share_of_positive_help_in_covid_year": (covid_help / total_pos) if total_pos > 1e-9 else None,
            "n_stress_years_helped_gt_0_25pp": len(years_all),
            "years_helped": years_all,
            "n_non_covid_years_helped_gt_0_25pp": len(years_non_covid),
            "non_covid_years_helped": years_non_covid,
            "multi_event_incl_covid": len(years_all) >= 2,
            "multi_event_non_covid_only": len(years_non_covid) >= 2,
        })
    conc_df = pd.DataFrame(conc)
    conc_df.to_csv(out_o / "covid_vs_noncovid_concentration.csv", index=False)

    thr_rows = []
    for bid in candidates:
        years_helped = sorted(help_df.loc[(help_df.book == bid) & (help_df.mdd_improve_pp > HELP_THRESHOLD_PP), "year"].tolist())
        non_covid_helped = [y for y in years_helped if y != COVID_YEAR]
        held = deltas_vs_base(books[base_key]["windows"]["heldout_2019_plus"], books[bid]["windows"]["heldout_2019_plus"])
        sealed = deltas_vs_base(books[base_key]["windows"]["sealed_2023_plus"], books[bid]["windows"]["sealed_2023_plus"])
        multi_ok = len(years_helped) >= 2
        multi_non_covid_ok = len(non_covid_helped) >= 2
        held_ok = held["score"] is not None and held["score"] > 0
        sealed_ok = sealed["score"] is not None and sealed["score"] > -1.0
        thr_rows.append({
            "book": bid, "years_helped": years_helped, "n_years_helped": len(years_helped),
            "non_covid_years_helped": non_covid_helped, "n_non_covid_years_helped": len(non_covid_helped),
            "multi_event_incl_covid_ge_2": multi_ok, "multi_event_non_covid_ge_2": multi_non_covid_ok,
            "heldout_score": held["score"], "sealed_score": sealed["score"],
            "qualifies_incl_covid_rule": bool(multi_ok and held_ok and sealed_ok),
            "qualifies_non_covid_strict_rule": bool(multi_non_covid_ok and held_ok and sealed_ok),
        })
    thr_df = pd.DataFrame(thr_rows)
    thr_df.to_csv(out_o / "multi_event_covid_framed_threshold.csv", index=False)

    print("==> (#3) thicken FIN_ONLY densify / rolling / COVID-ex", flush=True)
    densify_rows = []
    for bid in candidates:
        for w in FOCUS_WINDOWS:
            dlt = deltas_vs_base(books[base_key]["windows"][w], books[bid]["windows"][w])
            densify_rows.append({
                "book": bid, "alpha": books[bid]["alpha"],
                "sleeves": ",".join(books[bid]["sleeves"] or []) or "ALL", "window": w,
                "mdd_improve_pp": dlt["mdd_improve_pp"], "cagr_giveback_pp": dlt["cagr_giveback_pp"],
                "score": dlt["score"], "chal_cagr": books[bid]["windows"][w].get("cagr"),
                "chal_mdd": books[bid]["windows"][w].get("max_drawdown"),
                "ann_turnover_approx": books[bid]["turnover"].get("ann_turnover_approx"),
            })
    densify_df = pd.DataFrame(densify_rows)
    densify_df.to_csv(out_o / "fin_only_alpha_densify_windows.csv", index=False)

    covid_ex_rows = []
    for bid in [base_key] + candidates:
        nav = books[bid]["nav"].copy()
        nav["date"] = pd.to_datetime(nav["date"])
        part = nav[(nav["date"].dt.year != 2020) & (nav["date"] >= pd.Timestamp("2019-01-01"))].reset_index(drop=True)
        if len(part) < 60:
            st = {"cagr": None, "max_drawdown": None, "n_days": int(len(part))}
        else:
            part = part.copy()
            part["nav"] = part["nav"] / float(part["nav"].iloc[0])
            path = part["nav"].to_numpy(float)
            years = len(part) / 252.0
            cagr = float((path[-1] / path[0]) ** (1.0 / years) - 1.0) if years > 0 and path[0] > 0 else None
            peak = np.maximum.accumulate(path)
            mdd = float(np.min(path / peak - 1.0))
            st = {"cagr": cagr, "max_drawdown": mdd, "n_days": int(len(part))}
        covid_ex_rows.append({"book": bid, "window": "heldout_2019_plus_ex_covid_year", **st})
    covid_ex_df = pd.DataFrame(covid_ex_rows)
    covid_ex_delta = []
    b_ex = covid_ex_df[covid_ex_df.book == base_key].iloc[0]
    for bid in candidates:
        c_ex = covid_ex_df[covid_ex_df.book == bid].iloc[0]
        dlt = deltas_vs_base(
            {"cagr": b_ex["cagr"], "max_drawdown": b_ex["max_drawdown"]},
            {"cagr": c_ex["cagr"], "max_drawdown": c_ex["max_drawdown"]},
        )
        covid_ex_delta.append({
            "book": bid, "window": "heldout_2019_plus_ex_covid_year", "n_days": int(c_ex["n_days"]),
            "mdd_improve_pp": dlt["mdd_improve_pp"], "cagr_giveback_pp": dlt["cagr_giveback_pp"], "score": dlt["score"],
        })
    covid_ex_delta_df = pd.DataFrame(covid_ex_delta)
    covid_ex_delta_df.to_csv(out_o / "heldout_ex_covid_year_deltas.csv", index=False)

    roll_rows, roll_delta = [], []
    for end in ROLL_ENDS:
        start = date(end.year - 3, 1, 1)
        for bid in [base_key] + candidates:
            st = window_stats(books[bid]["nav"], start, end)
            roll_rows.append({
                "book": bid, "window_start": start.isoformat(), "window_end": end.isoformat(),
                **{k: st.get(k) for k in ("cagr", "max_drawdown", "utility", "vol", "n_days")},
            })
        b = next(r for r in roll_rows if r["book"] == base_key and r["window_end"] == end.isoformat())
        for bid in candidates:
            c = next(r for r in roll_rows if r["book"] == bid and r["window_end"] == end.isoformat())
            dlt = deltas_vs_base(
                {"cagr": b["cagr"], "max_drawdown": b["max_drawdown"]},
                {"cagr": c["cagr"], "max_drawdown": c["max_drawdown"]},
            )
            roll_delta.append({
                "book": bid, "window_start": start.isoformat(), "window_end": end.isoformat(),
                "mdd_improve_pp": dlt["mdd_improve_pp"], "cagr_giveback_pp": dlt["cagr_giveback_pp"], "score": dlt["score"],
            })
    pd.DataFrame(roll_rows).to_csv(out_o / "rolling_3y_window_metrics.csv", index=False)
    roll_delta_df = pd.DataFrame(roll_delta)
    roll_delta_df.to_csv(out_o / "rolling_3y_deltas_vs_base.csv", index=False)

    cost_rows = []
    for cost in COST_MULTS:
        bk = f"{BOOK_BASE}_C{int(cost)}x"
        for label in (BOOK_BLEND_A05, "FIN_ONLY_A08", "FIN_ONLY_A10", "FIN_ONLY_A12"):
            ck = label if cost == 1.0 else f"{label}_C{int(cost)}x"
            if ck not in books:
                continue
            for w in FOCUS_WINDOWS:
                dlt = deltas_vs_base(books[bk]["windows"][w], books[ck]["windows"][w])
                cost_rows.append({
                    "book": ck, "family": label, "cost_multiple": cost, "window": w,
                    "mdd_improve_pp": dlt["mdd_improve_pp"], "cagr_giveback_pp": dlt["cagr_giveback_pp"],
                    "score": dlt["score"], "ann_turnover_approx": books[ck]["turnover"].get("ann_turnover_approx"),
                })
    cost_df = pd.DataFrame(cost_rows)
    cost_df.to_csv(out_o / "fin_densify_cost_turnover.csv", index=False)

    held = densify_df[densify_df.window == "heldout_2019_plus"].sort_values("score", ascending=False)
    preferred = held.iloc[0].to_dict() if not held.empty else None
    tip = roll_delta_df[roll_delta_df.window_end == "2026-09-04"].sort_values("score", ascending=False)
    tip_winner = tip.iloc[0]["book"] if not tip.empty else "n/a"
    fin_held = held[held.book.str.startswith("FIN_ONLY_")].sort_values("score", ascending=False)
    fin_pref = fin_held.iloc[0]["book"] if not fin_held.empty else "n/a"
    lock_holds = fin_pref == "FIN_ONLY_A10"
    quals_incl = [r["book"] for _, r in thr_df.iterrows() if r["qualifies_incl_covid_rule"]]
    quals_strict = [r["book"] for _, r in thr_df.iterrows() if r["qualifies_non_covid_strict_rule"]]
    covid_ex_top = covid_ex_delta_df.sort_values("score", ascending=False).iloc[0]["book"] if len(covid_ex_delta_df) else "n/a"

    print("==> writing reports", flush=True)
    lines = [
        "# E45 COVID-Framed Non-2020 / Multi-Event Empirics", "",
        f"Generated: `{generated}`",
        "Status: **PAPER ONLY** — Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN",
        f"Retired MDD narrative: **`{CLAIM_STATUS}`** (do not invent a replacement)", "",
        "## Framing", "",
        "- **2020 = COVID-19.** A mega-drawdown story in 2020 is **expected**, not a surprise.",
        "- Calendar-year concentration in 2020 therefore does **not** by itself prove general crisis protection.",
        "- Honesty check = help outside COVID: years **2015 / 2018 / 2022**, plus COVID peak->trough episode.",
        f"- COVID episode window: **{COVID_EPISODE[0]} -> {COVID_EPISODE[1]}** (descriptive; not a retune gate).", "",
        "## Stress-year lexicon", "",
        "| Year | Tag | COVID? | Label |", "|---:|---|:---:|---|",
    ]
    for y, m in STRESS_EVENTS.items():
        lines.append(f"| {y} | `{m['tag']}` | {'Y' if m['covid'] else 'N'} | {m['label']} |")
    lines += ["", "## Concentration (COVID-year vs non-COVID)", "",
              "| Book | COVID-year help pp | Non-COVID +help pp | Share of +help in COVID year | # years >0.25pp | Non-COVID years >0.25pp | Multi>=2 (incl COVID) | Multi>=2 (non-COVID only) |",
              "|---|---:|---:|---:|---:|---|:---:|:---:|"]
    for _, r in conc_df.sort_values("share_of_positive_help_in_covid_year", ascending=False).iterrows():
        lines.append(
            f"| `{r['book']}` | {fmt(r['mdd_improve_covid_year_pp'])} | {fmt(r['mdd_improve_non_covid_positive_pp'])} | "
            f"{pct(r['share_of_positive_help_in_covid_year'])} | {int(r['n_stress_years_helped_gt_0_25pp'])} | "
            f"{r['non_covid_years_helped']} | {'Y' if r['multi_event_incl_covid'] else 'N'} | "
            f"{'Y' if r['multi_event_non_covid_only'] else 'N'} |"
        )
    lines += ["", "## Year detail (MDD help pp vs BASE)", "",
              "| Book | 2015 | 2018 | 2020 COVID | 2022 |", "|---|---:|---:|---:|---:|"]
    for bid in candidates:
        cells = []
        for y in (2015, 2018, 2020, 2022):
            sub = help_df[(help_df.book == bid) & (help_df.year == y)]
            cells.append(fmt(float(sub.iloc[0]["mdd_improve_pp"])) if len(sub) else "n/a")
        lines.append(f"| `{bid}` | " + " | ".join(cells) + " |")
    lines += ["", "## COVID episode help (peak->trough)", "",
              "| Book | MDD improve pp | CAGR giveback pp | Score | Episode days |",
              "|---|---:|---:|---:|---:|"]
    for _, r in ep_df.sort_values("mdd_improve_pp", ascending=False).iterrows():
        lines.append(
            f"| `{r['book']}` | {fmt(r['mdd_improve_pp'])} | {fmt(r['cagr_giveback_pp'])} | "
            f"{fmt(r['score'])} | {int(r['n_days']) if r['n_days'] is not None else 'n/a'} |"
        )
    lines += ["", "## Multi-event threshold (COVID-aware)", "",
              "Existing ballot rule still uses >=2 of {2015,2018,2020,2022} (COVID year allowed).",
              "Strict honesty variant requires >=2 **non-COVID** years among {2015,2018,2022}.", "",
              "| Book | Years helped | Non-COVID helped | Multi>=2 incl COVID | Multi>=2 non-COVID | Held-out score | Sealed score | Qualifies (incl) | Qualifies (strict non-COVID) |",
              "|---|---|---|:---:|:---:|---:|---:|:---:|:---:|"]
    for _, r in thr_df.sort_values("heldout_score", ascending=False).iterrows():
        lines.append(
            f"| `{r['book']}` | {r['years_helped']} | {r['non_covid_years_helped']} | "
            f"{'Y' if r['multi_event_incl_covid_ge_2'] else 'N'} | {'Y' if r['multi_event_non_covid_ge_2'] else 'N'} | "
            f"{fmt(r['heldout_score'])} | {fmt(r['sealed_score'])} | "
            f"**{'YES' if r['qualifies_incl_covid_rule'] else 'NO'}** | "
            f"**{'YES' if r['qualifies_non_covid_strict_rule'] else 'NO'}** |"
        )
    lines += ["",
              f"**Qualifiers (incl COVID year):** {', '.join(f'`{x}`' for x in quals_incl) if quals_incl else '_none_'}",
              f"**Qualifiers (strict non-COVID):** {', '.join(f'`{x}`' for x in quals_strict) if quals_strict else '_none_'}",
              "", "## Verdict", "",
              "- Treat 2020 help as **COVID mega-DD repayment**, not as proof of multi-regime defense.",
              "- Future OPEN ballots should report both the existing multi-event rule **and** the non-COVID-strict count.",
              "- Soft-Frozen / DEFAULT / stitch unchanged; HIGH_BETA stays DRAFT.", "",
              f"Label: `E45_COVID_NON2020_MULTI_{generated[:10]}__STITCH_FORBIDDEN`", ""]
    publish("E45_COVID_NON2020_MULTI_EVENT.md", "\n".join(lines), out_r)

    lines = [
        "# E45 FIN_ONLY densify thicken (around observe lock a=0.10)", "",
        f"Generated: `{generated}`",
        "Status: **PAPER ONLY** — observe lock unchanged unless densify clearly flips",
        "Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN · HIGH_BETA remains DRAFT", "",
        "## Held-out ranking (score = MDD improve - 0.5*|CAGR giveback|)", "",
        "| Book | a | Scope | MDD improve pp | CAGR giveback pp | Score | Ann. turnover |",
        "|---|---:|---|---:|---:|---:|---:|",
    ]
    for _, r in held.iterrows():
        to = r["ann_turnover_approx"]
        lines.append(
            f"| `{r['book']}` | {r['alpha']:.2f} | {r['sleeves']} | {fmt(r['mdd_improve_pp'])} | "
            f"{fmt(r['cagr_giveback_pp'])} | {fmt(r['score'])} | {'n/a' if to is None else f'{to:.2f}'} |"
        )
    lines += ["",
              f"**Held-out preferred (all candidates):** `{preferred['book'] if preferred else 'n/a'}`",
              f"**Held-out preferred among FIN_ONLY densify:** `{fin_pref}`",
              f"**Observe lock `SLEEVE_FIN_ONLY_A10` still preferred among FIN densify (paper densify id `FIN_ONLY_A10`)?** **{'YES' if lock_holds else 'NO — paper flag only; do not auto-flip'}**",
              "", "## COVID-year-excluded held-out (2019+ minus all 2020 days)", "",
              "Removes the COVID mega-DD year from the held-out path so sleeve-local edge is not COVID-only.", "",
              "| Book | MDD improve pp | CAGR giveback pp | Score | n_days |", "|---|---:|---:|---:|---:|"]
    for _, r in covid_ex_delta_df.sort_values("score", ascending=False).iterrows():
        lines.append(
            f"| `{r['book']}` | {fmt(r['mdd_improve_pp'])} | {fmt(r['cagr_giveback_pp'])} | "
            f"{fmt(r['score'])} | {int(r['n_days'])} |"
        )
    lines += ["", "## Rolling 3y tip window (end 2026-09-04)", "",
              f"Latest rolling-3y winner vs BASE: **`{tip_winner}`**", "",
              "| Book | MDD improve pp | CAGR giveback pp | Score |", "|---|---:|---:|---:|"]
    for _, r in tip.iterrows():
        lines.append(f"| `{r['book']}` | {fmt(r['mdd_improve_pp'])} | {fmt(r['cagr_giveback_pp'])} | {fmt(r['score'])} |")
    lines += ["", "## Cost stress (1-3x) @ heldout_2019_plus", "",
              "| Book | Cost | MDD improve pp | CAGR giveback pp | Score | Ann. turnover |",
              "|---|---:|---:|---:|---:|---:|"]
    sub = cost_df[cost_df.window == "heldout_2019_plus"].sort_values(["family", "cost_multiple"])
    for _, r in sub.iterrows():
        to = r["ann_turnover_approx"]
        lines.append(
            f"| `{r['book']}` | {r['cost_multiple']:.0f}x | {fmt(r['mdd_improve_pp'])} | "
            f"{fmt(r['cagr_giveback_pp'])} | {fmt(r['score'])} | {'n/a' if to is None else f'{to:.2f}'} |"
        )
    lines += ["", "## Verdict", "",
              "- Thicken densify around FIN_ONLY a in {0.05,0.08,0.10,0.12,0.15} + cost 1-3x + COVID-year-excluded held-out.",
              "- Observe sleeve stays **`SLEEVE_FIN_ONLY_A10`** unless a dedicated ballot flips it (this paper does not).",
              "- Pair with COVID-framed multi-event report: COVID help is expected; non-COVID multi-event remains the hard gate.", "",
              f"Label: `E45_FINA10_THICKEN_{generated[:10]}__STITCH_FORBIDDEN`", ""]
    publish("E45_FINA10_THICKEN.md", "\n".join(lines), out_r)

    integ = [
        "# E45 COVID Non-2020 + FIN_ONLY_A10 Thicken — Integrated", "",
        f"Generated: `{generated}`",
        "Status: **PAPER / OBSERVE OPS** — Soft-Frozen **KEEP** · DEFAULT **KEEP** · live stitch **FORBIDDEN**",
        f"Retired MDD narrative: **`{CLAIM_STATUS}`** (do not invent a replacement)", "",
        "## What ran", "",
        "| # | Item | Artifact |", "|---|---|---|",
        "| 2 | COVID-framed non-2020 / multi-event empirics | `E45_COVID_NON2020_MULTI_EVENT.md` |",
        "| 3 | FIN_ONLY densify thicken (a grid + cost + COVID-ex held-out) | `E45_FINA10_THICKEN.md` |", "",
        "## Cross-cut verdict", "",
        "1. **2020 = COVID-19 mega-DD** — large 2020 help is an expected story, not diversified crisis proof.",
        "2. **Non-COVID multi-event** remains weak for mild a / FIN_ONLY sleeves under the strict >=2 non-COVID-year rule.",
        f"3. **FIN densify preferred:** `{fin_pref}` · lock hold vs A10: **{'YES' if lock_holds else 'NO (paper flag only)'}**.",
        f"4. **COVID-ex held-out preferred:** `{covid_ex_top}`.",
        "5. No Soft-Frozen flip · no DEFAULT rewrite · no live stitch · no HIGH_BETA OPEN · no retired-narrative reinvention.", "",
        "## Machine summary", "",
        "`repro/e45-covid-non2020-fina10/outputs/covid_non2020_fina10_summary.json`", "",
        f"Label: `E45_COVID_NON2020_FINA10_{generated[:10]}__STITCH_FORBIDDEN`", "",
    ]
    publish("E45_COVID_NON2020_FINA10_INTEGRATED.md", "\n".join(integ), out_r)

    summary = {
        "generated_at_utc": generated,
        "status": "PAPER_ONLY",
        "soft_frozen": "KEEP",
        "default_books": "KEEP",
        "live_stitch": "FORBIDDEN",
        "claim_status": CLAIM_STATUS,
        "framing": {
            "covid_year": COVID_YEAR,
            "covid_episode": [COVID_EPISODE[0].isoformat(), COVID_EPISODE[1].isoformat()],
            "non_covid_years": list(NON_COVID_YEARS),
            "note": "2020 is COVID-19 mega-drawdown; large help there is expected",
        },
        "fin_densify_heldout_preferred": fin_pref,
        "observe_lock_fina10_holds_among_fin": lock_holds,
        "rolling_tip_winner": tip_winner,
        "multi_event_qualifiers_incl_covid": quals_incl,
        "multi_event_qualifiers_non_covid_strict": quals_strict,
        "covid_ex_heldout_top": covid_ex_top,
        "covid_ex_heldout_ranking": covid_ex_delta_df.sort_values("score", ascending=False)[
            ["book", "mdd_improve_pp", "cagr_giveback_pp", "score"]
        ].to_dict(orient="records"),
        "concentration": conc_df.to_dict(orient="records"),
    }
    (out_o / "covid_non2020_fina10_summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n", encoding="utf-8"
    )
    print(json.dumps({k: summary[k] for k in (
        "fin_densify_heldout_preferred", "observe_lock_fina10_holds_among_fin",
        "rolling_tip_winner", "multi_event_qualifiers_incl_covid",
        "multi_event_qualifiers_non_covid_strict", "covid_ex_heldout_top",
    )}, indent=2), flush=True)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
