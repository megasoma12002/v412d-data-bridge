#!/usr/bin/env python3
"""E45 M2 BIL_FX optimize pack: path FX friction + CBC cash twin + cut/κ grid.

Freeze: research/e45/E45_M2_BIL_FX_OPTIMIZE_V0_FROZEN.md
Observe OPEN for M2_RELOC_BIL_FX_C50 authorized by human 「請全做」.
Does NOT flip Soft-Frozen / DEFAULT / stitch. Does NOT invent MDD.
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

OUT = ROOT / "repro/e45-m2-bil-fx-optimize"
DEF_DIR = ROOT / "data/def_proxies"
RESEARCH = ROOT / "research/e45"
OPS = ROOT / "research/ops"
FREEZE = RESEARCH / "E45_M2_BIL_FX_OPTIMIZE_V0_FROZEN.md"

LISTING_720B = pd.Timestamp("2018-02-01")
COST_MULTS = (1, 2)
FEE_KEYS = ("BUY_FEE", "SELL_FEE", "SLIP", "TAX_STOCK", "TAX_ETF")
FOCUS = ("heldout_2019_plus", "sealed_2023_plus", "full")
WINDOWS = {k: WINDOWS_STANDARD[k] for k in FOCUS}

CUT_GRID = (0.35, 0.40, 0.45, 0.50, 0.55, 0.60)
KAPPA_AT_C50 = (0.60, 0.80, 1.00)
CONST_HALF = (0.0, 0.001, 0.0025, 0.005)  # fraction; 0/10/25/50 bp



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

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()



def load_fx_half_spread(cal: pd.DatetimeIndex) -> pd.Series:
    """h_t = (spot_sell - spot_buy) / (2 * usdtwd_mid)."""
    fx = pd.read_csv(DEF_DIR / "USDTWD_finmind.csv", parse_dates=["date"]).sort_values("date")
    fx["date"] = pd.to_datetime(fx["date"])
    fx = fx.set_index("date")
    mid = fx["usdtwd_mid"].astype(float).reindex(cal).ffill()
    buy = fx["spot_buy"].astype(float).reindex(cal).ffill()
    sell = fx["spot_sell"].astype(float).reindex(cal).ffill()
    h = (sell - buy) / (2.0 * mid.replace(0.0, np.nan))
    return h.fillna(0.0).clip(lower=0.0)


def build_optimize_def_bars(equity_cal: pd.DatetimeIndex) -> pd.DataFrame:
    bil = _load_ohlcv(DEF_DIR / "BIL_ohlcv.csv").set_index("date")
    fx = pd.read_csv(DEF_DIR / "USDTWD_finmind.csv", parse_dates=["date"]).sort_values("date")
    fx["date"] = pd.to_datetime(fx["date"])
    fx = fx.set_index("date")
    b720 = _load_ohlcv(DEF_DIR / "00720B_ohlcv.csv").set_index("date")
    cbc = pd.read_csv(DEF_DIR / "cbc_rediscount_rate_daily.csv", parse_dates=["date"])
    cbc["date"] = pd.to_datetime(cbc["date"])
    cbc = cbc.set_index("date")["rediscount_pct"].astype(float)

    cal = pd.DatetimeIndex(sorted(equity_cal))
    bil_adj = bil["adj_close"].reindex(cal).ffill()
    fx_mid = fx["usdtwd_mid"].astype(float).reindex(cal).ffill()

    frames: list[pd.DataFrame] = []
    bil_fx_lvl = _tr_level(bil_adj * fx_mid)
    frames.append(_bars_from_level("BIL_FX_MID", bil_fx_lvl))
    alias = frames[-1].copy()
    alias["code"] = "BIL_FX"
    frames.append(alias)

    # CBC rediscount cash carry (ACT/252 research convention)
    rate = cbc.reindex(cal).ffill()
    daily = (rate / 100.0) / 252.0
    daily = daily.fillna(0.0)
    cbc_lvl = (1.0 + daily).cumprod() * 100.0
    frames.append(_bars_from_level("TWD_CASH_CBC", cbc_lvl))
    frames.append(_bars_from_level("TWD_CASH0", pd.Series(100.0, index=cal, dtype=float)))

    r_720 = b720["adj_close"].reindex(cal).ffill().pct_change().fillna(0.0)
    active = pd.Series(np.where(cal >= LISTING_720B, r_720.to_numpy(), 0.0), index=cal)
    frames.append(_bars_from_level("TWD_720B", (1.0 + active).cumprod() * 100.0))
    return pd.concat(frames, ignore_index=True)


def apply_path_fx_drag(
    nav: pd.DataFrame,
    sleeve: pd.DataFrame,
    half_spread: pd.Series | float,
) -> pd.DataFrame:
    """Rebuild NAV: r_adj = (1+r)*(1-|Δw|*h)-1 on mid-marked path."""
    d = nav.copy()
    d["date"] = pd.to_datetime(d["date"])
    d = d.sort_values("date").reset_index(drop=True)
    idx = pd.DatetimeIndex(d["date"])
    w = sleeve["DEF"].astype(float).reindex(idx).fillna(0.0)
    dw = w.diff().abs().fillna(0.0)
    if isinstance(half_spread, (int, float)):
        h = pd.Series(float(half_spread), index=idx)
    else:
        h = half_spread.reindex(idx).fillna(0.0).astype(float)
    drag = (dw.to_numpy() * h.to_numpy()).clip(0.0, 0.99)
    r = d["nav"].astype(float).pct_change().fillna(0.0).to_numpy()
    adj = (1.0 + r) * (1.0 - drag) - 1.0
    out_nav = np.empty_like(adj)
    out_nav[0] = float(d["nav"].iloc[0])
    for i in range(1, len(adj)):
        out_nav[i] = out_nav[i - 1] * (1.0 + adj[i])
    out = d.copy()
    out["nav"] = out_nav
    return out


def intensity_with_kappa(intensity_lag1: pd.Series, kappa: float) -> pd.Series:
    if kappa >= 1.0 - 1e-12:
        return intensity_lag1
    return intensity_lag1.astype(float).clip(upper=float(kappa))


def main() -> None:
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)
    OPS.mkdir(parents=True, exist_ok=True)

    print("loading market ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, _s, target, regime = e16_features(market)
    cal = pd.DatetimeIndex(sorted(market["date"].unique()))

    print("building M1 intensity (frozen sensor, lag-1) ...", flush=True)
    state = build_m1_state(market)
    intensity_lag1 = state["s_t"].shift(1).fillna(0.0)
    state.to_csv(OUT / "outputs" / "m2_sensor_state_features.csv")
    intensity_lag1.rename("s_lag1").to_csv(OUT / "outputs" / "m2_intensity_lag1.csv", header=True)

    print("building optimize DEF bars (BIL_FX + CBC + TWD twins) ...", flush=True)
    def_bars = build_optimize_def_bars(cal)
    def_bars.to_csv(OUT / "outputs" / "optimize_def_proxy_bars.csv", index=False)
    market_aug = pd.concat([market, def_bars], ignore_index=True)
    h_path = load_fx_half_spread(cal)
    h_path.rename("h_t").to_csv(OUT / "outputs" / "usdtwd_half_spread_daily.csv", header=True)

    # Specs: book, mode, cut, kappa, kind, def_code, path_fx
    specs: list[tuple] = []
    for cut in CUT_GRID:
        tag = f"{int(round(cut * 100)):02d}"
        specs.append((f"M2_RELOC_BIL_FX_C{tag}", "RELOC_BIL_FX", cut, 1.0, "cut_grid", "BIL_FX", None))
    for kappa in KAPPA_AT_C50:
        if abs(kappa - 1.0) < 1e-12:
            continue
        tag = f"{int(round(kappa * 100)):02d}"
        specs.append((f"M2_RELOC_BIL_FX_C50_K{tag}", "RELOC_BIL_FX", 0.50, kappa, "kappa_grid", "BIL_FX", None))
    for cut, ctag in ((0.50, "50"), (0.75, "75")):
        specs.append((f"M2_RELOC_TWD_CASH_CBC_C{ctag}", "RELOC_TWD_720B", cut, 1.0, "twd_cbc", "TWD_CASH_CBC", None))
    specs.append(("M2_RELOC_TWD_CASH0_C50", "RELOC_TWD_720B", 0.50, 1.0, "twd_cash0", "TWD_CASH0", None))
    specs.append(("M2_RELOC_TWD_720B_C50", "RELOC_TWD_720B", 0.50, 1.0, "twd_720b", "TWD_720B", None))
    specs.append(("M2_RELOC_BIL_FX_C50_FXPATH", "RELOC_BIL_FX", 0.50, 1.0, "path_fx", "BIL_FX", "path"))
    for hs in CONST_HALF:
        if hs == 0.0:
            continue
        bps = int(round(hs * 10_000))
        specs.append((f"M2_RELOC_BIL_FX_C50_FXH{bps}", "RELOC_BIL_FX", 0.50, 1.0, "path_fx_const", "BIL_FX", hs))

    schedule_cache: dict[tuple, pd.DataFrame] = {}
    books: list[dict] = [
        {
            "book": BOOK_BASE,
            "kind": "ref",
            "mode": None,
            "cut": None,
            "kappa": None,
            "schedule": None,
            "def_code": None,
            "path_fx": None,
        }
    ]
    for book, mode, cut, kappa, kind, def_code, path_fx in specs:
        key = (float(cut), float(kappa), str(mode))
        if key not in schedule_cache:
            inten = intensity_with_kappa(intensity_lag1, float(kappa))
            schedule_cache[key] = build_m2_sleeve_schedule(target, inten, float(cut), mode)
        sched = schedule_cache[key]
        sched.to_csv(OUT / "outputs" / f"{book.lower()}_sleeve_schedule.csv")
        books.append(
            {
                "book": book,
                "kind": kind,
                "mode": mode,
                "cut": cut,
                "kappa": kappa,
                "schedule": sched,
                "def_code": def_code,
                "path_fx": path_fx,
            }
        )

    mid_sched = schedule_cache[(0.50, 1.0, "RELOC_BIL_FX")]
    mid_navs: dict[int, pd.DataFrame] = {}

    rows: list[dict] = []
    navs: dict[tuple[str, int], pd.DataFrame] = {}
    for spec in books:
        for mult in COST_MULTS:
            print(f"sim {spec['book']} costx{mult} ...", flush=True)
            if spec["book"] == BOOK_BASE:
                nav, fills, meta = run_early_stack(
                    market, target, regime, dividends, cost_multiple=float(mult)
                )
            elif spec["path_fx"] is not None:
                if mult not in mid_navs:
                    nav_mid, _, _ = run_early_stack(
                        market_aug,
                        target,
                        regime,
                        dividends,
                        sleeve_weight_schedule=mid_sched,
                        def_code="BIL_FX",
                        cost_multiple=float(mult),
                    )
                    mid_navs[mult] = nav_mid
                hs = spec["path_fx"]
                if hs == "path":
                    nav = apply_path_fx_drag(mid_navs[mult], mid_sched, h_path)
                else:
                    nav = apply_path_fx_drag(mid_navs[mult], mid_sched, float(hs))
                fills = pd.DataFrame()
                meta = {"mean_e45_exposure": None, "exact_t1_ok": True, "path_fx": True}
            else:
                nav, fills, meta = run_early_stack(
                    market_aug,
                    target,
                    regime,
                    dividends,
                    sleeve_weight_schedule=spec["schedule"],
                    def_code=spec["def_code"],
                    cost_multiple=float(mult),
                )
                if spec["book"] == "M2_RELOC_BIL_FX_C50":
                    mid_navs[mult] = nav

            navs[(spec["book"], int(mult))] = nav
            to = turnover_metrics(nav, fills) if len(fills) else {
                "n_fills": None,
                "fees_tax_sum": None,
                "turnover_per_year": None,
            }
            for w, (a, b_) in WINDOWS.items():
                st = window_stats(nav, a, b_)
                rows.append(
                    {
                        "book": spec["book"],
                        "kind": spec["kind"],
                        "mode": spec["mode"],
                        "cut": spec["cut"],
                        "kappa": spec["kappa"],
                        "def_code": spec.get("def_code"),
                        "path_fx": str(spec["path_fx"]),
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
    metrics.to_csv(OUT / "outputs" / "optimize_metrics.csv", index=False)

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
                bstat = metrics[
                    (metrics.book == BOOK_BASE)
                    & (metrics.cost_multiple == mult)
                    & (metrics.window == w)
                ].iloc[0]
                cstat = metrics[
                    (metrics.book == book)
                    & (metrics.cost_multiple == mult)
                    & (metrics.window == w)
                ].iloc[0]
                dlt = deltas_vs_base(
                    {"cagr": bstat["cagr"], "max_drawdown": bstat["max_drawdown"]},
                    {"cagr": cstat["cagr"], "max_drawdown": cstat["max_drawdown"]},
                )
                deltas.append(
                    {
                        "book": book,
                        "kind": spec["kind"],
                        "mode": spec["mode"],
                        "cut": spec["cut"],
                        "kappa": spec["kappa"],
                        "def_code": spec.get("def_code"),
                        "path_fx": str(spec["path_fx"]),
                        "cost_multiple": int(mult),
                        "window": w,
                        "mdd_improve_pp": dlt["mdd_improve_pp"],
                        "cagr_giveback_pp": dlt["cagr_giveback_pp"],
                        "score": dlt["score"],
                        "covid_ex_score": cex_d["score"] if w == "heldout_2019_plus" else None,
                        "years_helped": ",".join(str(y) for y in years_helped),
                        "n_years_helped": len(years_helped),
                        **{f"help_{y}_pp": year_helps[y] for y in STRESS_YEARS},
                    }
                )
    delta_df = pd.DataFrame(deltas)
    delta_df.to_csv(OUT / "outputs" / "optimize_deltas.csv", index=False)

    # Giveback vs mid C50 for path-FX books
    path_vs_mid: list[dict] = []
    for mult in COST_MULTS:
        mid_nav = navs.get(("M2_RELOC_BIL_FX_C50", int(mult)))
        if mid_nav is None:
            mid_nav = mid_navs.get(mult)
        if mid_nav is None:
            continue
        for book in (
            "M2_RELOC_BIL_FX_C50_FXPATH",
            "M2_RELOC_BIL_FX_C50_FXH10",
            "M2_RELOC_BIL_FX_C50_FXH25",
            "M2_RELOC_BIL_FX_C50_FXH50",
        ):
            if (book, int(mult)) not in navs:
                continue
            alt = navs[(book, int(mult))]
            for w, (a, b_) in WINDOWS.items():
                ms = window_stats(mid_nav, a, b_)
                als = window_stats(alt, a, b_)
                gb = None
                if ms.get("cagr") is not None and als.get("cagr") is not None:
                    gb = (float(ms["cagr"]) - float(als["cagr"])) * 100.0
                path_vs_mid.append(
                    {
                        "book": book,
                        "cost_multiple": int(mult),
                        "window": w,
                        "giveback_vs_mid_cagr_pp": gb,
                        "mid_cagr": ms.get("cagr"),
                        "alt_cagr": als.get("cagr"),
                        "mid_mdd": ms.get("max_drawdown"),
                        "alt_mdd": als.get("max_drawdown"),
                    }
                )
    path_vs_mid_df = pd.DataFrame(path_vs_mid)
    path_vs_mid_df.to_csv(OUT / "outputs" / "path_fx_vs_mid.csv", index=False)

    qual_rows: list[dict] = []
    for spec in books:
        book = spec["book"]
        if book == BOOK_BASE:
            continue
        d1 = delta_df[
            (delta_df.book == book)
            & (delta_df.cost_multiple == 1)
            & (delta_df.window == "heldout_2019_plus")
        ].iloc[0]
        d1s = delta_df[
            (delta_df.book == book)
            & (delta_df.cost_multiple == 1)
            & (delta_df.window == "sealed_2023_plus")
        ].iloc[0]
        d2 = delta_df[
            (delta_df.book == book)
            & (delta_df.cost_multiple == 2)
            & (delta_df.window == "heldout_2019_plus")
        ].iloc[0]
        years = [int(y) for y in str(d1["years_helped"]).split(",") if y]
        cost_ok = (
            d1["score"] is not None
            and float(d1["score"]) >= 0
            and d1["mdd_improve_pp"] is not None
            and float(d1["mdd_improve_pp"]) > 0
            and d2["score"] is not None
            and float(d2["score"]) >= 0
            and d2["mdd_improve_pp"] is not None
            and float(d2["mdd_improve_pp"]) > 0
        )
        q = qualify_row(years, d1["score"], d1s["score"], d1["covid_ex_score"], cost_ok)
        # normalize key name
        sec2 = q.get("qualifies_section2")
        qual_rows.append(
            {
                "book": book,
                "kind": spec["kind"],
                "mode": spec["mode"],
                "cut": spec["cut"],
                "kappa": spec["kappa"],
                "def_code": spec.get("def_code"),
                "path_fx": str(spec["path_fx"]),
                "heldout_1x_score": d1["score"],
                "sealed_1x_score": d1s["score"],
                "covid_ex_heldout_1x_score": d1["covid_ex_score"],
                "heldout_2x_score": d2["score"],
                "heldout_1x_giveback_pp": d1["cagr_giveback_pp"],
                "heldout_1x_mdd_improve_pp": d1["mdd_improve_pp"],
                "qualifies_section2": bool(sec2),
                **{k: v for k, v in q.items() if k != "years_helped"},
                "years_helped": years,
            }
        )
    qual_df = pd.DataFrame(qual_rows)
    qual_df.to_csv(OUT / "outputs" / "optimize_section2_qualification.csv", index=False)

    def _q(book: str) -> dict:
        return next(r for r in qual_rows if r["book"] == book)

    bil_c50 = _q("M2_RELOC_BIL_FX_C50")
    fxpath = _q("M2_RELOC_BIL_FX_C50_FXPATH")
    cbc50 = _q("M2_RELOC_TWD_CASH_CBC_C50")
    cash0 = _q("M2_RELOC_TWD_CASH0_C50")
    twd720 = _q("M2_RELOC_TWD_720B_C50")

    cut_pass = qual_df[qual_df.kind == "cut_grid"]
    cut_ok = cut_pass[cut_pass.qualifies_section2].sort_values("heldout_1x_giveback_pp", ascending=True)
    if len(cut_ok):
        best_cut = cut_ok.iloc[0].to_dict()
    elif len(cut_pass):
        best_cut = cut_pass.sort_values("heldout_1x_score", ascending=False).iloc[0].to_dict()
    else:
        best_cut = None

    fxpath_vs_mid = None
    if len(path_vs_mid_df):
        row = path_vs_mid_df[
            (path_vs_mid_df.book == "M2_RELOC_BIL_FX_C50_FXPATH")
            & (path_vs_mid_df.cost_multiple == 1)
            & (path_vs_mid_df.window == "heldout_2019_plus")
        ]
        if len(row):
            fxpath_vs_mid = float(row.iloc[0]["giveback_vs_mid_cagr_pp"] or 0)
    path_fx_material = fxpath_vs_mid is not None and abs(fxpath_vs_mid) >= 0.10
    mean_h = float(h_path.mean()) if len(h_path) else None

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "schema_version": "e45_m2_bil_fx_optimize_v0",
        "status": "PAPER_PLUS_OBSERVE_OPEN_AUTHORIZED",
        "observe_open": {
            "variant": "M2_RELOC_BIL_FX_C50",
            "authorization": "請全做",
            "status": "OPERATING_OBSERVE",
            "not_live_default": True,
            "stitch_forbidden": True,
            "c75_auto_open": False,
        },
        "freeze": str(FREEZE.relative_to(ROOT)),
        "freeze_sha256": sha256_file(FREEZE) if FREEZE.exists() else None,
        "claim_status": CLAIM_STATUS,
        "market_path": str(MARKET_PATH.relative_to(ROOT)),
        "inputs_sha256": {
            "BIL": sha256_file(DEF_DIR / "BIL_ohlcv.csv"),
            "USDTWD": sha256_file(DEF_DIR / "USDTWD_finmind.csv"),
            "00720B": sha256_file(DEF_DIR / "00720B_ohlcv.csv"),
            "cbc_rediscount_daily": sha256_file(DEF_DIR / "cbc_rediscount_rate_daily.csv"),
            "cbc_rediscount_steps": sha256_file(DEF_DIR / "cbc_rediscount_rate_steps.csv"),
        },
        "cost_multiples": list(COST_MULTS),
        "fee_keys_scaled": list(FEE_KEYS),
        "books": [b["book"] for b in books],
        "path_fx": {
            "method": "|Δw_DEF| × h_t on mid-marked NAV",
            "h_t_definition": "(spot_sell - spot_buy) / (2 * usdtwd_mid)",
            "mean_h_t": mean_h,
            "material_vs_mid_held_10bp": path_fx_material,
            "held_giveback_vs_mid_pp": fxpath_vs_mid,
            "fxpath_section2": bool(fxpath["qualifies_section2"]),
            "fxpath_held_score": fxpath["heldout_1x_score"],
            "mid_c50_held_score": bil_c50["heldout_1x_score"],
        },
        "twd_cbc_twin": {
            "cbc_c50_section2": bool(cbc50["qualifies_section2"]),
            "cbc_c50_held_score": cbc50["heldout_1x_score"],
            "cash0_c50_section2": bool(cash0["qualifies_section2"]),
            "twd720_c50_section2": bool(twd720["qualifies_section2"]),
            "bil_c50_held_score": bil_c50["heldout_1x_score"],
        },
        "cut_kappa_grid": {
            "cuts": list(CUT_GRID),
            "kappas_at_c50": list(KAPPA_AT_C50),
            "best_cut_row": best_cut,
            "c50_k1": bil_c50,
        },
        "section2_qualification": qual_rows,
        "hard_non_actions": [
            "Soft-Frozen FIN clip [0.50, 0.95] KEEP",
            "Live DEFAULT E22_v2s_tw KEEP",
            "Live E45 stitch FORBIDDEN",
            "No invent MDD replacement",
            "CBC rediscount ≠ retail TWD cash product",
            "C75 remains ballot-gated (not auto-OPEN)",
        ],
    }
    (RESEARCH / "E45_M2_BIL_FX_OPTIMIZE.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    (OUT / "reports" / "E45_M2_BIL_FX_OPTIMIZE.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )

    md_lines = [
        "# E45 M2 BIL_FX Optimize Paper",
        "",
        f"- Generated: `{payload['generated_at_utc']}`",
        f"- Freeze: `{payload['freeze']}`",
        f"- Repro: `repro/e45-m2-bil-fx-optimize/`",
        f"- Claim status: `{CLAIM_STATUS}`",
        "",
        "## A) Path-dependent FX friction (C50 mid-marked)",
        "",
        "Method: `|Δw_DEF| · h_t` with `h_t = (spot_sell − spot_buy) / (2 · usdtwd_mid)` "
        "applied to mid-marked early-stack returns.",
        "",
        f"- Mean `h_t`: `{mean_h}`",
        f"- Held giveback vs mid @ FXPATH: `{fxpath_vs_mid}` pp",
        f"- Material (≥0.10 pp vs mid)? **`{path_fx_material}`**",
        f"- FXPATH §2: `{fxpath['qualifies_section2']}` · held score `{pp(fxpath['heldout_1x_score'])}`",
        f"- MID C50 §2: `{bil_c50['qualifies_section2']}` · held score `{pp(bil_c50['heldout_1x_score'])}`",
        "",
        "| Book | held score | giveback pp | MDD improve pp | §2 |",
        "|---|---:|---:|---:|---|",
    ]
    for bname in (
        "M2_RELOC_BIL_FX_C50",
        "M2_RELOC_BIL_FX_C50_FXPATH",
        "M2_RELOC_BIL_FX_C50_FXH10",
        "M2_RELOC_BIL_FX_C50_FXH25",
        "M2_RELOC_BIL_FX_C50_FXH50",
    ):
        r = _q(bname)
        md_lines.append(
            f"| `{bname}` | {pp(r['heldout_1x_score'])} | {pp(r['heldout_1x_giveback_pp'])} | "
            f"{pp(r['heldout_1x_mdd_improve_pp'])} | {yn(r['qualifies_section2'])} |"
        )

    md_lines += [
        "",
        "## B) TWD CBC cash twin vs BIL_FX / cash0 / 00720B",
        "",
        "CBC rediscount is a **policy-rate cash carry proxy** (not retail deposit / MM).",
        "",
        "| Book | held score | giveback pp | §2 |",
        "|---|---:|---:|---|",
    ]
    for bname in (
        "M2_RELOC_BIL_FX_C50",
        "M2_RELOC_TWD_CASH_CBC_C50",
        "M2_RELOC_TWD_CASH_CBC_C75",
        "M2_RELOC_TWD_CASH0_C50",
        "M2_RELOC_TWD_720B_C50",
    ):
        r = _q(bname)
        md_lines.append(
            f"| `{bname}` | {pp(r['heldout_1x_score'])} | {pp(r['heldout_1x_giveback_pp'])} | "
            f"{yn(r['qualifies_section2'])} |"
        )

    md_lines += [
        "",
        "## C) Cut × intensity-cap grid (BIL_FX mid)",
        "",
        f"Cuts `{list(CUT_GRID)}` @ κ=1; κ `{list(KAPPA_AT_C50)}` @ c=0.50.",
        "",
    ]
    if best_cut:
        md_lines.append(
            f"**Preferred among cut grid:** `{best_cut.get('book')}` · "
            f"held score `{pp(best_cut.get('heldout_1x_score'))}` · "
            f"giveback `{pp(best_cut.get('heldout_1x_giveback_pp'))}` · "
            f"§2 `{yn(bool(best_cut.get('qualifies_section2')))}`"
        )
    md_lines += [
        "",
        "| Book | cut | κ | held score | giveback pp | §2 |",
        "|---|---:|---:|---:|---:|---|",
    ]
    grid_books = qual_df[qual_df.kind.isin(["cut_grid", "kappa_grid"])].sort_values(["cut", "kappa"])
    for _, r in grid_books.iterrows():
        md_lines.append(
            f"| `{r['book']}` | {r['cut']} | {r['kappa']} | {pp(r['heldout_1x_score'])} | "
            f"{pp(r['heldout_1x_giveback_pp'])} | {yn(bool(r['qualifies_section2']))} |"
        )

    md_lines += [
        "",
        "## D) Observe OPEN (user-authorized)",
        "",
        "- Variant: **`M2_RELOC_BIL_FX_C50`**",
        "- Authorization: human 「請全做」 (2026-09-06)",
        "- Status: **OPERATING_OBSERVE** (dual-ledger + month-end monitor)",
        "- **NOT** live DEFAULT; stitch still **FORBIDDEN**; C75 remains ballot-gated",
        "",
        "## Hard non-actions",
        "",
        "- Soft-Frozen FIN clip [0.50, 0.95] KEEP",
        "- Live DEFAULT `E22_v2s_tw` KEEP",
        "- Live E45 stitch FORBIDDEN",
        "- No invent MDD replacement",
        "- CBC rediscount ≠ retail TWD cash",
        "",
        "## Reproduce",
        "",
        "```bash",
        "python3 scripts/e45_m2_bil_fx_optimize_paper.py",
        "```",
        "",
    ]
    md = "\n".join(md_lines) + "\n"
    (RESEARCH / "E45_M2_BIL_FX_OPTIMIZE.md").write_text(md, encoding="utf-8")
    (OUT / "reports" / "E45_M2_BIL_FX_OPTIMIZE.md").write_text(md, encoding="utf-8")

    print(
        json.dumps(
            {
                "ok": True,
                "path_fx_material": path_fx_material,
                "fxpath_vs_mid_pp": fxpath_vs_mid,
                "mean_h_t": mean_h,
                "bil_c50_score": bil_c50["heldout_1x_score"],
                "cbc_c50_score": cbc50["heldout_1x_score"],
                "best_cut_book": None if not best_cut else best_cut.get("book"),
            },
            indent=2,
            default=str,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
