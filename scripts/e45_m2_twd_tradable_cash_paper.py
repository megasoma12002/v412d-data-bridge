#!/usr/bin/env python3
"""E45 M2 tradable TWD short-bond twin paper (00740B / 00751B / basket).

Freeze: research/e45/E45_M2_C35_TWDCASH_HIGHBETA_V0_FROZEN.md §B
Retail deposit NAV unavailable on free FinMind — listed short-bond ETFs only.
Does NOT OPEN observe / Soft-Frozen / stitch.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from e45_crisis_core import build_m2_sleeve_schedule
from e45_m1_state_signal_paper import (
    HELP_PP,
    STRESS_YEARS,
    build_m1_state,
    covid_ex_stats,
    pp,
    qualify_row,
    turnover_metrics,
    year_mdd_help_pp,
    yn,
)
from e45_paper_harness import (
    BOOK_BASE,
    CLAIM_STATUS,
    MARKET_PATH,
    ROOT,
    WINDOWS_STANDARD,
    deltas_vs_base,
    e16_features,
    load_dividends,
    load_market,
    run_early_stack,
    window_stats,
)

OUT = ROOT / "repro/e45-m2-twd-tradable-cash"
DEF_DIR = ROOT / "data/def_proxies"
RESEARCH = ROOT / "research/e45"
OPS = ROOT / "research/ops"
FREEZE = RESEARCH / "E45_M2_C35_TWDCASH_HIGHBETA_V0_FROZEN.md"

LISTING_720B = pd.Timestamp("2018-02-01")
LISTING_740B = pd.Timestamp("2018-06-08")
LISTING_751B = pd.Timestamp("2018-10-03")
COST_MULTS = (1, 2)
FEE_KEYS = ("BUY_FEE", "SELL_FEE", "SLIP", "TAX_STOCK", "TAX_ETF")
FOCUS = ("heldout_2019_plus", "sealed_2023_plus", "full")
WINDOWS = {k: WINDOWS_STANDARD[k] for k in FOCUS}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_ohlcv(path: Path) -> pd.DataFrame:
    d = pd.read_csv(path, parse_dates=["date"])
    d["date"] = pd.to_datetime(d["date"])
    for c in ("open", "high", "low", "close", "adj_close", "volume"):
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors="coerce")
    return d.sort_values("date")


def _tr_level(adj: pd.Series, start: float = 100.0) -> pd.Series:
    a = adj.astype(float).replace(0.0, np.nan).ffill()
    return (1.0 + a.pct_change().fillna(0.0)).cumprod() * float(start)


def _bars_from_level(code: str, lvl: pd.Series) -> pd.DataFrame:
    rows = []
    prev = lvl.shift(1)
    for dt, close in lvl.items():
        if pd.isna(close):
            continue
        o = float(prev.loc[dt]) if pd.notna(prev.loc[dt]) else float(close)
        rows.append(
            {
                "date": dt,
                "code": code,
                "open": o,
                "high": max(o, float(close)),
                "low": min(o, float(close)),
                "close": float(close),
                "adj_close": float(close),
                "volume": 0.0,
            }
        )
    return pd.DataFrame(rows)


def build_def_bars(equity_cal: pd.DatetimeIndex) -> pd.DataFrame:
    bil = _load_ohlcv(DEF_DIR / "BIL_ohlcv.csv").set_index("date")
    fx = pd.read_csv(DEF_DIR / "USDTWD_finmind.csv", parse_dates=["date"]).sort_values("date")
    fx["date"] = pd.to_datetime(fx["date"])
    fx = fx.set_index("date")
    b720 = _load_ohlcv(DEF_DIR / "00720B_ohlcv.csv").set_index("date")
    b740 = _load_ohlcv(DEF_DIR / "00740B_ohlcv.csv").set_index("date")
    b751 = _load_ohlcv(DEF_DIR / "00751B_ohlcv.csv").set_index("date")
    cbc = pd.read_csv(DEF_DIR / "cbc_rediscount_rate_daily.csv", parse_dates=["date"])
    cbc["date"] = pd.to_datetime(cbc["date"])
    cbc = cbc.set_index("date")["rediscount_pct"].astype(float)

    cal = pd.DatetimeIndex(sorted(equity_cal))
    frames: list[pd.DataFrame] = []

    bil_fx = _tr_level(bil["adj_close"].reindex(cal).ffill() * fx["usdtwd_mid"].astype(float).reindex(cal).ffill())
    frames.append(_bars_from_level("BIL_FX", bil_fx))

    rate = cbc.reindex(cal).ffill()
    daily = ((rate / 100.0) / 252.0).fillna(0.0)
    frames.append(_bars_from_level("TWD_CASH_CBC", (1.0 + daily).cumprod() * 100.0))
    frames.append(_bars_from_level("TWD_CASH0", pd.Series(100.0, index=cal, dtype=float)))

    def listed_lvl(ohlcv: pd.DataFrame, listing: pd.Timestamp) -> pd.Series:
        r = ohlcv["adj_close"].reindex(cal).ffill().pct_change().fillna(0.0)
        active = pd.Series(np.where(cal >= listing, r.to_numpy(), 0.0), index=cal)
        return (1.0 + active).cumprod() * 100.0

    frames.append(_bars_from_level("TWD_720B", listed_lvl(b720, LISTING_720B)))
    frames.append(_bars_from_level("TWD_740B", listed_lvl(b740, LISTING_740B)))
    frames.append(_bars_from_level("TWD_751B", listed_lvl(b751, LISTING_751B)))

    # Equal-weight 740+751 after both listed; before that cash0
    r740 = b740["adj_close"].reindex(cal).ffill().pct_change().fillna(0.0)
    r751 = b751["adj_close"].reindex(cal).ffill().pct_change().fillna(0.0)
    both = cal >= LISTING_751B
    basket_r = pd.Series(np.where(both, 0.5 * (r740.to_numpy() + r751.to_numpy()), 0.0), index=cal)
    frames.append(_bars_from_level("TWD_SHORT_BASKET", (1.0 + basket_r).cumprod() * 100.0))
    return pd.concat(frames, ignore_index=True)


def main() -> None:
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)

    print("loading market ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, _s, target, regime = e16_features(market)
    cal = pd.DatetimeIndex(sorted(market["date"].unique()))

    print("building M1 intensity ...", flush=True)
    state = build_m1_state(market)
    intensity_lag1 = state["s_t"].shift(1).fillna(0.0)

    print("building tradable TWD DEF bars ...", flush=True)
    def_bars = build_def_bars(cal)
    def_bars.to_csv(OUT / "outputs" / "twd_tradable_def_bars.csv", index=False)
    market_aug = pd.concat([market, def_bars], ignore_index=True)

    specs = [
        ("M2_RELOC_BIL_FX_C50", "RELOC_BIL_FX", 0.50, "ref_bil", "BIL_FX"),
        ("M2_RELOC_TWD_CASH_CBC_C50", "RELOC_TWD_720B", 0.50, "ref_cbc", "TWD_CASH_CBC"),
        ("M2_RELOC_TWD_CASH0_C50", "RELOC_TWD_720B", 0.50, "ref_cash0", "TWD_CASH0"),
        ("M2_RELOC_TWD_720B_C50", "RELOC_TWD_720B", 0.50, "ref_720", "TWD_720B"),
        ("M2_RELOC_TWD_740B_C50", "RELOC_TWD_720B", 0.50, "twd_740", "TWD_740B"),
        ("M2_RELOC_TWD_740B_C75", "RELOC_TWD_720B", 0.75, "twd_740", "TWD_740B"),
        ("M2_RELOC_TWD_751B_C50", "RELOC_TWD_720B", 0.50, "twd_751", "TWD_751B"),
        ("M2_RELOC_TWD_751B_C75", "RELOC_TWD_720B", 0.75, "twd_751", "TWD_751B"),
        ("M2_RELOC_TWD_SHORT_BASKET_C50", "RELOC_TWD_720B", 0.50, "twd_basket", "TWD_SHORT_BASKET"),
        ("M2_RELOC_TWD_SHORT_BASKET_C75", "RELOC_TWD_720B", 0.75, "twd_basket", "TWD_SHORT_BASKET"),
    ]

    books: list[dict] = [{"book": BOOK_BASE, "kind": "ref", "mode": None, "cut": None, "schedule": None, "def_code": None}]
    for book, mode, cut, kind, def_code in specs:
        sched = build_m2_sleeve_schedule(target, intensity_lag1, cut, mode)
        sched.to_csv(OUT / "outputs" / f"{book.lower()}_sleeve_schedule.csv")
        books.append({"book": book, "kind": kind, "mode": mode, "cut": cut, "schedule": sched, "def_code": def_code})

    rows: list[dict] = []
    navs: dict[tuple[str, int], pd.DataFrame] = {}
    for spec in books:
        for mult in COST_MULTS:
            print(f"sim {spec['book']} costx{mult} ...", flush=True)
            if spec["book"] == BOOK_BASE:
                nav, fills, meta = run_early_stack(market, target, regime, dividends, cost_multiple=float(mult))
            else:
                nav, fills, meta = run_early_stack(
                    market_aug, target, regime, dividends,
                    sleeve_weight_schedule=spec["schedule"],
                    def_code=spec["def_code"],
                    cost_multiple=float(mult),
                )
            navs[(spec["book"], int(mult))] = nav
            to = turnover_metrics(nav, fills)
            for w, (a, b_) in WINDOWS.items():
                st = window_stats(nav, a, b_)
                rows.append({
                    "book": spec["book"], "kind": spec["kind"], "mode": spec["mode"], "cut": spec["cut"],
                    "def_code": spec.get("def_code"), "cost_multiple": int(mult), "window": w,
                    "cagr": st.get("cagr"), "max_drawdown": st.get("max_drawdown"),
                    "utility": st.get("utility"), "vol": st.get("vol"), "n_days": st.get("n_days"),
                    "n_fills": to["n_fills"], "fees_tax_sum": to["fees_tax_sum"],
                    "turnover_per_year": to["turnover_per_year"],
                    "exact_t1_ok": bool(meta.get("exact_t1_ok")),
                })
    metrics = pd.DataFrame(rows)
    metrics.to_csv(OUT / "outputs" / "twd_tradable_metrics.csv", index=False)

    deltas: list[dict] = []
    for mult in COST_MULTS:
        base_nav = navs[(BOOK_BASE, int(mult))]
        for spec in books:
            book = spec["book"]
            book_nav = navs[(book, int(mult))]
            year_helps = {y: year_mdd_help_pp(base_nav, book_nav, y) for y in STRESS_YEARS}
            years_helped = [y for y, h in year_helps.items() if h is not None and h > HELP_PP]
            cex_d = deltas_vs_base(covid_ex_stats(base_nav), covid_ex_stats(book_nav))
            for w in FOCUS:
                bstat = metrics[(metrics.book == BOOK_BASE) & (metrics.cost_multiple == mult) & (metrics.window == w)].iloc[0]
                cstat = metrics[(metrics.book == book) & (metrics.cost_multiple == mult) & (metrics.window == w)].iloc[0]
                dlt = deltas_vs_base(
                    {"cagr": bstat["cagr"], "max_drawdown": bstat["max_drawdown"]},
                    {"cagr": cstat["cagr"], "max_drawdown": cstat["max_drawdown"]},
                )
                deltas.append({
                    "book": book, "kind": spec["kind"], "mode": spec["mode"], "cut": spec["cut"],
                    "def_code": spec.get("def_code"), "cost_multiple": int(mult), "window": w,
                    "mdd_improve_pp": dlt["mdd_improve_pp"], "cagr_giveback_pp": dlt["cagr_giveback_pp"],
                    "score": dlt["score"],
                    "covid_ex_score": cex_d["score"] if w == "heldout_2019_plus" else None,
                    "years_helped": ",".join(str(y) for y in years_helped),
                    "n_years_helped": len(years_helped),
                })
    delta_df = pd.DataFrame(deltas)
    delta_df.to_csv(OUT / "outputs" / "twd_tradable_deltas.csv", index=False)

    qual_rows: list[dict] = []
    for spec in books:
        book = spec["book"]
        if book == BOOK_BASE:
            continue
        d1 = delta_df[(delta_df.book == book) & (delta_df.cost_multiple == 1) & (delta_df.window == "heldout_2019_plus")].iloc[0]
        d1s = delta_df[(delta_df.book == book) & (delta_df.cost_multiple == 1) & (delta_df.window == "sealed_2023_plus")].iloc[0]
        d2 = delta_df[(delta_df.book == book) & (delta_df.cost_multiple == 2) & (delta_df.window == "heldout_2019_plus")].iloc[0]
        years = [int(y) for y in str(d1["years_helped"]).split(",") if y]
        cost_ok = (
            d1["score"] is not None and float(d1["score"]) >= 0
            and d1["mdd_improve_pp"] is not None and float(d1["mdd_improve_pp"]) > 0
            and d2["score"] is not None and float(d2["score"]) >= 0
            and d2["mdd_improve_pp"] is not None and float(d2["mdd_improve_pp"]) > 0
        )
        q = qualify_row(years, d1["score"], d1s["score"], d1["covid_ex_score"], cost_ok)
        qual_rows.append({
            "book": book, "kind": spec["kind"], "mode": spec["mode"], "cut": spec["cut"],
            "def_code": spec.get("def_code"),
            "heldout_1x_score": d1["score"], "sealed_1x_score": d1s["score"],
            "covid_ex_heldout_1x_score": d1["covid_ex_score"], "heldout_2x_score": d2["score"],
            "heldout_1x_giveback_pp": d1["cagr_giveback_pp"],
            "heldout_1x_mdd_improve_pp": d1["mdd_improve_pp"],
            "qualifies_section2": bool(q.get("qualifies_section2")),
            **{k: v for k, v in q.items() if k != "years_helped"},
            "years_helped": years,
        })
    qual_df = pd.DataFrame(qual_rows)
    qual_df.to_csv(OUT / "outputs" / "twd_tradable_section2.csv", index=False)

    def _q(book: str) -> dict:
        return next(r for r in qual_rows if r["book"] == book)

    challengers = [r for r in qual_rows if r["kind"] in {"twd_740", "twd_751", "twd_basket"}]
    pass_ch = [r for r in challengers if r["qualifies_section2"]]
    best = sorted(pass_ch, key=lambda r: (r["heldout_1x_giveback_pp"] is None, r["heldout_1x_giveback_pp"] or 9e9))
    best_row = best[0] if best else None

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PAPER_ONLY",
        "freeze": str(FREEZE.relative_to(ROOT)),
        "claim_status": CLAIM_STATUS,
        "market_path": str(MARKET_PATH.relative_to(ROOT)),
        "retail_deposit_nav": "UNAVAILABLE_FREE_FINMIND_TIER",
        "tradable_listed": ["00740B", "00751B", "TWD_SHORT_BASKET"],
        "inputs_sha256": {
            "00740B": sha256_file(DEF_DIR / "00740B_ohlcv.csv"),
            "00751B": sha256_file(DEF_DIR / "00751B_ohlcv.csv"),
            "00720B": sha256_file(DEF_DIR / "00720B_ohlcv.csv"),
            "BIL": sha256_file(DEF_DIR / "BIL_ohlcv.csv"),
            "USDTWD": sha256_file(DEF_DIR / "USDTWD_finmind.csv"),
            "cbc_rediscount_daily": sha256_file(DEF_DIR / "cbc_rediscount_rate_daily.csv"),
        },
        "cost_multiples": list(COST_MULTS),
        "fee_keys_scaled": list(FEE_KEYS),
        "section2_qualification": qual_rows,
        "challenger_section2_pass": [r["book"] for r in pass_ch],
        "best_challenger_by_giveback": best_row,
        "hard_non_actions": [
            "Soft-Frozen / DEFAULT KEEP; stitch FORBIDDEN",
            "00740B/00751B ≠ retail TWD deposit",
            "No invent MDD; no live_market merge; no observe OPEN from this paper",
        ],
    }
    (RESEARCH / "E45_M2_TWD_TRADABLE_CASH.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8"
    )
    (OUT / "reports" / "E45_M2_TWD_TRADABLE_CASH.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8"
    )

    lines = [
        "# E45 M2 Tradable TWD Cash-like Twin Paper",
        "",
        f"- Generated: `{payload['generated_at_utc']}`",
        f"- Freeze: `{payload['freeze']}`",
        f"- Retail deposit NAV: **`UNAVAILABLE_FREE_FINMIND_TIER`**",
        "- Listed proxies: `00740B`, `00751B`, equal-weight short basket",
        f"- Claim status: `{CLAIM_STATUS}`",
        "",
        "## §2 qualification",
        "",
        "| Book | §2 | Held score | Giveback pp | MDD improve pp |",
        "|---|---|---:|---:|---:|",
    ]
    for book in [
        "M2_RELOC_BIL_FX_C50",
        "M2_RELOC_TWD_CASH_CBC_C50",
        "M2_RELOC_TWD_CASH0_C50",
        "M2_RELOC_TWD_720B_C50",
        "M2_RELOC_TWD_740B_C50",
        "M2_RELOC_TWD_740B_C75",
        "M2_RELOC_TWD_751B_C50",
        "M2_RELOC_TWD_751B_C75",
        "M2_RELOC_TWD_SHORT_BASKET_C50",
        "M2_RELOC_TWD_SHORT_BASKET_C75",
    ]:
        r = _q(book)
        lines.append(
            f"| `{book}` | {yn(r['qualifies_section2'])} | {pp(r['heldout_1x_score'])} | "
            f"{pp(r['heldout_1x_giveback_pp'])} | {pp(r['heldout_1x_mdd_improve_pp'])} |"
        )
    lines += [
        "",
        f"**Challenger §2 PASS:** `{', '.join(payload['challenger_section2_pass']) or 'none'}`",
        (
            f"**Best challenger by giveback:** `{best_row['book']}` · giveback `{pp(best_row['heldout_1x_giveback_pp'])}`"
            if best_row else "**Best challenger by giveback:** none"
        ),
        "",
        "## Honesty",
        "",
        "- `00740B` / `00751B` are **listed short-bond ETFs**, not bank deposits / MM funds.",
        "- CBC rediscount remains a **policy** upper-bound carry proxy.",
        "- Free FinMind cannot supply dated retail deposit-rate series for a true cash NAV.",
        "",
        "## Governance",
        "",
        "- Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN",
        "- No observe OPEN / no C50 lock change from this paper",
        "- No invent MDD replacement · no `live_market.csv` merge",
        "",
        "## Reproduce",
        "",
        "```bash",
        "python3 scripts/e45_m2_twd_tradable_cash_paper.py",
        "```",
        "",
    ]
    md = "\n".join(lines) + "\n"
    (RESEARCH / "E45_M2_TWD_TRADABLE_CASH.md").write_text(md, encoding="utf-8")
    (OUT / "reports" / "E45_M2_TWD_TRADABLE_CASH.md").write_text(md, encoding="utf-8")
    print(json.dumps({
        "ok": True,
        "challenger_pass": payload["challenger_section2_pass"],
        "best": None if not best_row else best_row["book"],
    }, indent=2))


if __name__ == "__main__":
    main()
