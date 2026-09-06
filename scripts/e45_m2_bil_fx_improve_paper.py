#!/usr/bin/env python3
"""E45 M2 BIL_FX improve pack: FX mark sensitivity + TWD twin + observe prep.

Freeze: research/e45/E45_M2_BIL_FX_IMPROVE_V0_FROZEN.md
Does NOT cast observe ACCEPT / OPEN / Soft-Frozen / stitch.
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
    BOOK_BLEND_A05,
    CLAIM_STATUS,
    MARKET_PATH,
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

OUT = ROOT / "repro/e45-m2-bil-fx-improve"
DEF_DIR = ROOT / "data/def_proxies"
RESEARCH = ROOT / "research/e45"
OPS = ROOT / "research/ops"
FREEZE = RESEARCH / "E45_M2_BIL_FX_IMPROVE_V0_FROZEN.md"
OBS_MD = OPS / "E45_M2_BIL_FX_OBSERVE_OPEN_AWAITING_ACCEPT.md"
OBS_ZH = OPS / "E45_M2_BIL_FX_OBSERVE_OPEN_AWAITING_ACCEPT.zh-TW.md"

LISTING_720B = pd.Timestamp("2018-02-01")
COST_MULTS = (1, 2)
FEE_KEYS = ("BUY_FEE", "SELL_FEE", "SLIP", "TAX_STOCK", "TAX_ETF")
FOCUS = ("heldout_2019_plus", "sealed_2023_plus", "full")
WINDOWS = {k: WINDOWS_STANDARD[k] for k in FOCUS}

FX_MARKS = (
    ("MID", "usdtwd_mid", 0.0),
    ("SPOT_BUY", "spot_buy", 0.0),
    ("SPOT_SELL", "spot_sell", 0.0),
    ("MID_H5", "usdtwd_mid", 5.0),
    ("MID_H10", "usdtwd_mid", 10.0),
    ("MID_H25", "usdtwd_mid", 25.0),
    ("MID_H50", "usdtwd_mid", 50.0),
)


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


def build_improve_def_bars(equity_cal: pd.DatetimeIndex) -> pd.DataFrame:
    bil = _load_ohlcv(DEF_DIR / "BIL_ohlcv.csv").set_index("date")
    fx = pd.read_csv(DEF_DIR / "USDTWD_finmind.csv", parse_dates=["date"]).sort_values("date")
    fx["date"] = pd.to_datetime(fx["date"])
    fx = fx.set_index("date")
    b720 = _load_ohlcv(DEF_DIR / "00720B_ohlcv.csv").set_index("date")
    cal = pd.DatetimeIndex(sorted(equity_cal))
    bil_adj = bil["adj_close"].reindex(cal).ffill()

    frames: list[pd.DataFrame] = []
    for mark_id, col, haircut_bps in FX_MARKS:
        fx_s = fx[col].astype(float).reindex(cal).ffill()
        if haircut_bps:
            fx_s = fx_s * (1.0 - haircut_bps / 10_000.0)
        frames.append(_bars_from_level(f"BIL_FX_{mark_id}", _tr_level(bil_adj * fx_s)))

    mid = next(f for f in frames if f["code"].iloc[0] == "BIL_FX_MID")
    alias = mid.copy()
    alias["code"] = "BIL_FX"
    frames.append(alias)

    frames.append(_bars_from_level("TWD_CASH0", pd.Series(100.0, index=cal, dtype=float)))

    r_720 = b720["adj_close"].reindex(cal).ffill().pct_change().fillna(0.0)
    active = pd.Series(np.where(cal >= LISTING_720B, r_720.to_numpy(), 0.0), index=cal)
    frames.append(_bars_from_level("TWD_720B", (1.0 + active).cumprod() * 100.0))
    return pd.concat(frames, ignore_index=True)


def write_observe_awaiting() -> None:
    OBS_MD.write_text(
        """# E45 M2 BIL_FX observe OPEN — AWAITING HUMAN ACCEPT

**Status:** `AWAITING_HUMAN_ACCEPT` — **NOT OPEN** / **NOT OPERATING**

**Candidate (default lock):** `M2_RELOC_BIL_FX_C50`

**Related draft ballot:** `research/ops/E45_M2_RELOC_OBSERVE_OPEN_BALLOT_DRAFT.md`

## What is ready (prep only)

- Dual-ledger prep: `scripts/e45_m2_bil_fx_dual_paper_ledgers.py`
- Month-end monitor prep: `scripts/e45_m2_bil_fx_month_end_monitor.py`
- Improve pack paper: `research/e45/E45_M2_BIL_FX_IMPROVE.md`
- Freeze: `research/e45/E45_M2_BIL_FX_IMPROVE_V0_FROZEN.md`

## What is NOT done

- No human **ACCEPT OPEN** cast on the observe ballot
- Not added to `ops_month_end_paper_pack.py` live observe roster
- No Soft-Frozen / DEFAULT / stitch change
- `BIL_FX` remains FX-marked USD T-bill proxy — **not** TWD cash

## Human gate

Cast on the draft ballot (HOLD / ACCEPT OPEN / REJECT). Until **ACCEPT OPEN**,
this pack stays **AWAITING_HUMAN_ACCEPT**.
""",
        encoding="utf-8",
    )
    OBS_ZH.write_text(
        """# E45 M2 BIL_FX observe OPEN — 等候人類 ACCEPT

**狀態：** `AWAITING_HUMAN_ACCEPT` — **尚未 OPEN** / **尚未 OPERATING**

**候選（預設鎖定）：** `M2_RELOC_BIL_FX_C50`

**相關草案票：** `research/ops/E45_M2_RELOC_OBSERVE_OPEN_BALLOT_DRAFT.md`

## 已就緒（僅 prep）

- 雙帳本 prep：`scripts/e45_m2_bil_fx_dual_paper_ledgers.py`
- 月底監看 prep：`scripts/e45_m2_bil_fx_month_end_monitor.py`
- Improve pack：`research/e45/E45_M2_BIL_FX_IMPROVE.md`
- Freeze：`research/e45/E45_M2_BIL_FX_IMPROVE_V0_FROZEN.md`

## 尚未完成

- 人類尚未在 observe 票投下 **ACCEPT OPEN**
- 尚未加入 `ops_month_end_paper_pack.py` 活體 observe 名冊
- Soft-Frozen／DEFAULT／stitch 不變
- `BIL_FX` 仍是 FX 標記的美元短債代理 — **不是**台幣現金

## 人類門檻

請在草案票投下 HOLD／ACCEPT OPEN／REJECT。在 **ACCEPT OPEN** 之前，本包維持 **AWAITING_HUMAN_ACCEPT**。
""",
        encoding="utf-8",
    )


def main() -> None:
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    RESEARCH.mkdir(parents=True, exist_ok=True)
    OPS.mkdir(parents=True, exist_ok=True)

    print("loading market ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _p, _s, target, regime = e16_features(market)

    print("building M1 intensity (frozen sensor, lag-1) ...", flush=True)
    state = build_m1_state(market)
    intensity_lag1 = state["s_t"].shift(1).fillna(0.0)
    state.to_csv(OUT / "outputs" / "m2_sensor_state_features.csv")
    intensity_lag1.rename("s_lag1").to_csv(OUT / "outputs" / "m2_intensity_lag1.csv", header=True)

    print("building improve DEF bars (FX marks + TWD twins) ...", flush=True)
    def_bars = build_improve_def_bars(pd.DatetimeIndex(sorted(market["date"].unique())))
    def_bars.to_csv(OUT / "outputs" / "improve_def_proxy_bars.csv", index=False)
    market_aug = pd.concat([market, def_bars], ignore_index=True)

    e45_full = e45_full_exposure(market)

    m2_specs = [
        ("M2_SHRINK_C50", "SHRINK", 0.50, "m2_shrink", None),
        ("M2_RELOC_TEL_C50", "RELOC_TEL", 0.50, "m2_reloc_tel", None),
        ("M2_RELOC_BIL_FX_MID_C50", "RELOC_BIL_FX", 0.50, "fx_mid", "BIL_FX_MID"),
        ("M2_RELOC_BIL_FX_MID_C75", "RELOC_BIL_FX", 0.75, "fx_mid", "BIL_FX_MID"),
        ("M2_RELOC_BIL_FX_SPOT_BUY_C50", "RELOC_BIL_FX", 0.50, "fx_spot_buy", "BIL_FX_SPOT_BUY"),
        ("M2_RELOC_BIL_FX_SPOT_SELL_C50", "RELOC_BIL_FX", 0.50, "fx_spot_sell", "BIL_FX_SPOT_SELL"),
        ("M2_RELOC_BIL_FX_H5_C50", "RELOC_BIL_FX", 0.50, "fx_h5", "BIL_FX_MID_H5"),
        ("M2_RELOC_BIL_FX_H10_C50", "RELOC_BIL_FX", 0.50, "fx_h10", "BIL_FX_MID_H10"),
        ("M2_RELOC_BIL_FX_H25_C50", "RELOC_BIL_FX", 0.50, "fx_h25", "BIL_FX_MID_H25"),
        ("M2_RELOC_BIL_FX_H50_C50", "RELOC_BIL_FX", 0.50, "fx_h50", "BIL_FX_MID_H50"),
        ("M2_RELOC_BIL_FX_H25_C75", "RELOC_BIL_FX", 0.75, "fx_h25", "BIL_FX_MID_H25"),
        ("M2_RELOC_BIL_FX_C50", "RELOC_BIL_FX", 0.50, "fx_mid_alias", "BIL_FX"),
        ("M2_RELOC_TWD_CASH0_C50", "RELOC_TWD_720B", 0.50, "twd_cash0", "TWD_CASH0"),
        ("M2_RELOC_TWD_720B_C50", "RELOC_TWD_720B", 0.50, "twd_720b", "TWD_720B"),
        ("M2_RELOC_TWD_720B_C75", "RELOC_TWD_720B", 0.75, "twd_720b", "TWD_720B"),
    ]

    books: list[dict] = [
        {
            "book": BOOK_BASE,
            "kind": "ref",
            "mode": None,
            "cut": None,
            "exposure": None,
            "sleeves": None,
            "schedule": None,
            "def_code": None,
        },
        {
            "book": BOOK_BLEND_A05,
            "kind": "ref_e45",
            "mode": None,
            "cut": None,
            "exposure": blend_exposure(e45_full, 0.05),
            "sleeves": None,
            "schedule": None,
            "def_code": None,
        },
        {
            "book": "SLEEVE_FIN_ONLY_A10",
            "kind": "ref_e45_sleeve",
            "mode": None,
            "cut": None,
            "exposure": blend_exposure(e45_full, 0.10),
            "sleeves": SLEEVE_FIN_ONLY,
            "schedule": None,
            "def_code": None,
        },
    ]
    for book, mode, cut, kind, def_code in m2_specs:
        sched = build_m2_sleeve_schedule(target, intensity_lag1, cut, mode)
        sched.to_csv(OUT / "outputs" / f"{book.lower()}_sleeve_schedule.csv")
        books.append(
            {
                "book": book,
                "kind": kind,
                "mode": mode,
                "cut": cut,
                "exposure": None,
                "sleeves": None,
                "schedule": sched,
                "def_code": def_code,
            }
        )

    rows: list[dict] = []
    navs: dict[tuple[str, int], pd.DataFrame] = {}
    for spec in books:
        for mult in COST_MULTS:
            print(f"sim {spec['book']} costx{mult} ...", flush=True)
            use_mkt = market_aug if spec.get("def_code") else market
            nav, fills, meta = run_early_stack(
                use_mkt,
                target,
                regime,
                dividends,
                e45_exposure=spec["exposure"],
                e45_sleeve_names=spec["sleeves"],
                sleeve_weight_schedule=spec["schedule"],
                def_code=spec.get("def_code"),
                cost_multiple=float(mult),
            )
            # Summaries only in repro (no per-book daily NAV/fills — keeps pack small)
            navs[(spec["book"], int(mult))] = nav
            to = turnover_metrics(nav, fills)
            for w, (a, b_) in WINDOWS.items():
                st = window_stats(nav, a, b_)
                rows.append(
                    {
                        "book": spec["book"],
                        "kind": spec["kind"],
                        "mode": spec["mode"],
                        "cut": spec["cut"],
                        "def_code": spec.get("def_code"),
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
    metrics.to_csv(OUT / "outputs" / "improve_metrics.csv", index=False)

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
                        "def_code": spec.get("def_code"),
                        "cost_multiple": int(mult),
                        "window": w,
                        "mdd_improve_pp": dlt["mdd_improve_pp"],
                        "cagr_giveback_pp": dlt["cagr_giveback_pp"],
                        "score": dlt["score"],
                        "covid_ex_mdd_improve_pp": cex_d["mdd_improve_pp"],
                        "covid_ex_cagr_giveback_pp": cex_d["cagr_giveback_pp"],
                        "covid_ex_score": cex_d["score"],
                        "help_2015_pp": year_helps.get(2015),
                        "help_2018_pp": year_helps.get(2018),
                        "help_2020_pp": year_helps.get(2020),
                        "help_2022_pp": year_helps.get(2022),
                        "years_helped": ",".join(str(y) for y in years_helped),
                        "n_years_helped": len(years_helped),
                        "turnover_per_year": cstat["turnover_per_year"],
                        "fees_tax_sum": cstat["fees_tax_sum"],
                    }
                )
    delta_df = pd.DataFrame(deltas)
    delta_df.to_csv(OUT / "outputs" / "improve_deltas.csv", index=False)

    qual_rows: list[dict] = []
    for spec in books:
        book = spec["book"]
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
        qual_rows.append(
            {
                "book": book,
                "kind": spec["kind"],
                "mode": spec["mode"],
                "cut": spec["cut"],
                "def_code": spec.get("def_code"),
                "heldout_1x_score": d1["score"],
                "sealed_1x_score": d1s["score"],
                "covid_ex_heldout_1x_score": d1["covid_ex_score"],
                "heldout_2x_score": d2["score"],
                "heldout_1x_giveback_pp": d1["cagr_giveback_pp"],
                **q,
            }
        )
    qual_df = pd.DataFrame(qual_rows)
    qual_df.to_csv(OUT / "outputs" / "improve_section2_qualification.csv", index=False)

    held1 = delta_df[
        (delta_df.window == "heldout_2019_plus") & (delta_df.cost_multiple == 1)
    ].sort_values("score", ascending=False)

    fx_kinds = {
        "fx_mid",
        "fx_mid_alias",
        "fx_spot_buy",
        "fx_spot_sell",
        "fx_h5",
        "fx_h10",
        "fx_h25",
        "fx_h50",
    }
    twd_kinds = {"twd_cash0", "twd_720b"}
    fx_pass = qual_df[qual_df.kind.isin(fx_kinds) & qual_df.qualifies_section2]["book"].tolist()
    twd_pass = qual_df[qual_df.kind.isin(twd_kinds) & qual_df.qualifies_section2]["book"].tolist()

    def _q(book: str) -> dict:
        return next(r for r in qual_rows if r["book"] == book)

    mid_c50 = _q("M2_RELOC_BIL_FX_MID_C50")
    spot_buy = _q("M2_RELOC_BIL_FX_SPOT_BUY_C50")
    h25 = _q("M2_RELOC_BIL_FX_H25_C50")
    twd720 = _q("M2_RELOC_TWD_720B_C50")
    cash0 = _q("M2_RELOC_TWD_CASH0_C50")
    bil_alias = _q("M2_RELOC_BIL_FX_C50")

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PAPER_ONLY",
        "observe_status": "AWAITING_HUMAN_ACCEPT",
        "freeze": str(FREEZE.relative_to(ROOT)),
        "freeze_sha256": sha256_file(FREEZE) if FREEZE.exists() else None,
        "claim_status": CLAIM_STATUS,
        "market_path": str(MARKET_PATH.relative_to(ROOT)),
        "inputs_sha256": {
            "BIL": sha256_file(DEF_DIR / "BIL_ohlcv.csv"),
            "USDTWD": sha256_file(DEF_DIR / "USDTWD_finmind.csv"),
            "00720B": sha256_file(DEF_DIR / "00720B_ohlcv.csv"),
        },
        "cost_multiples": list(COST_MULTS),
        "fee_keys_scaled": list(FEE_KEYS),
        "books": [b["book"] for b in books],
        "section2_qualification": qual_rows,
        "fx_section2_qualifiers": fx_pass,
        "twd_twin_section2_qualifiers": twd_pass,
        "informational_gates": {
            "mid_c50_section2": bool(mid_c50["qualifies_section2"]),
            "bil_fx_c50_alias_section2": bool(bil_alias["qualifies_section2"]),
            "spot_buy_c50_section2": bool(spot_buy["qualifies_section2"]),
            "mid_h25_c50_section2": bool(h25["qualifies_section2"]),
            "twd_720b_c50_section2": bool(twd720["qualifies_section2"]),
            "twd_cash0_c50_section2": bool(cash0["qualifies_section2"]),
        },
        "heldout_1x_ranking": held1[
            [
                "book",
                "kind",
                "score",
                "mdd_improve_pp",
                "cagr_giveback_pp",
                "covid_ex_score",
                "years_helped",
            ]
        ].to_dict(orient="records"),
        "soft_frozen": "KEEP",
        "live_default": "KEEP",
        "live_stitch": "FORBIDDEN",
        "non_actions": [
            "No Soft-Frozen / DEFAULT / stitch / HIGH_BETA ballot",
            "No observe ACCEPT/OPEN cast",
            "No merge DEF into live_market.csv",
            "Haircut/spot marks are research FX friction proxies — not bank quotes",
            "TWD_CASH0 is 0% yield bound; 00720B is short-bond ETF — not pure TWD cash",
            "No invented replacement for retired claimed-MDD narrative",
        ],
    }
    (OUT / "reports" / "e45_m2_bil_fx_improve.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8"
    )
    (RESEARCH / "E45_M2_BIL_FX_IMPROVE.json").write_text(
        json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8"
    )

    lines = [
        "# E45 M2 BIL_FX improve pack (FX sensitivity + TWD twin)",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        "Status: **PAPER ONLY** — Soft-Frozen **KEEP**; DEFAULT **KEEP**; stitch **FORBIDDEN**.",
        f"Observe wiring: **`AWAITING_HUMAN_ACCEPT`** — see `{OBS_MD.relative_to(ROOT)}`.",
        f"Freeze: `{FREEZE.relative_to(ROOT)}`",
        "",
        "## Non-claims",
        "",
        "- No Soft-Frozen / DEFAULT / stitch change",
        "- No observe ACCEPT / OPEN cast",
        "- Haircut / spot marks are research FX friction proxies (not bank quotes)",
        "- `TWD_CASH0` = flat 0% bound; `00720B` = short-bond ETF — neither is pure bank cash",
        f"- Claimed MDD: `{CLAIM_STATUS}` — no invented replacement",
        "",
        "## ① FX mark sensitivity (`RELOC_BIL_FX`)",
        "",
        "| Book | §2 | Held score | COVID-ex score | Giveback pp | Years |",
        "|---|---|---:|---:|---:|---|",
    ]
    for book in [
        "M2_RELOC_BIL_FX_C50",
        "M2_RELOC_BIL_FX_MID_C50",
        "M2_RELOC_BIL_FX_SPOT_BUY_C50",
        "M2_RELOC_BIL_FX_SPOT_SELL_C50",
        "M2_RELOC_BIL_FX_H5_C50",
        "M2_RELOC_BIL_FX_H10_C50",
        "M2_RELOC_BIL_FX_H25_C50",
        "M2_RELOC_BIL_FX_H50_C50",
        "M2_RELOC_BIL_FX_MID_C75",
        "M2_RELOC_BIL_FX_H25_C75",
    ]:
        r = _q(book)
        lines.append(
            f"| `{book}` | {'PASS' if r['qualifies_section2'] else 'FAIL'} | "
            f"{pp(r['heldout_1x_score'])} | {pp(r['covid_ex_heldout_1x_score'])} | "
            f"{pp(r['heldout_1x_giveback_pp'])} | "
            f"{','.join(str(y) for y in r['years_helped']) or '—'} |"
        )

    lines += [
        "",
        f"**Informational gate (freeze):** SPOT_BUY C50 §2 = "
        f"**{'PASS' if spot_buy['qualifies_section2'] else 'FAIL'}**; "
        f"MID_H25 C50 §2 = **{'PASS' if h25['qualifies_section2'] else 'FAIL'}**.",
        f"FX §2 PASS books: `{', '.join(fx_pass) if fx_pass else 'none'}`.",
        "",
        "## ② TWD twin vs BIL_FX MID",
        "",
        "| Book | §2 | Held score | COVID-ex score | Giveback pp | Years |",
        "|---|---|---:|---:|---:|---|",
    ]
    for book in [
        "M2_RELOC_BIL_FX_MID_C50",
        "M2_RELOC_TWD_720B_C50",
        "M2_RELOC_TWD_720B_C75",
        "M2_RELOC_TWD_CASH0_C50",
        "M2_SHRINK_C50",
        "M2_RELOC_TEL_C50",
    ]:
        r = _q(book)
        lines.append(
            f"| `{book}` | {'PASS' if r['qualifies_section2'] else 'FAIL'} | "
            f"{pp(r['heldout_1x_score'])} | {pp(r['covid_ex_heldout_1x_score'])} | "
            f"{pp(r['heldout_1x_giveback_pp'])} | "
            f"{','.join(str(y) for y in r['years_helped']) or '—'} |"
        )

    lines += [
        "",
        f"TWD twin §2 PASS: `{', '.join(twd_pass) if twd_pass else 'none'}`.",
        "",
        "## ③ Observe OPEN prep",
        "",
        "Status remains **AWAITING_HUMAN_ACCEPT** (ballot still DRAFT).",
        f"Prep doc: `{OBS_MD.relative_to(ROOT)}`.",
        "Scripts: `scripts/e45_m2_bil_fx_dual_paper_ledgers.py`, "
        "`scripts/e45_m2_bil_fx_month_end_monitor.py`.",
        "",
        "## Held-out deltas @1x (all books)",
        "",
        "| Book | Kind | MDD dpp | Giveback | Score | COVID-ex | Years |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for _, r in held1.iterrows():
        lines.append(
            f"| {r['book']} | {r['kind']} | {pp(r['mdd_improve_pp'])} | "
            f"{pp(r['cagr_giveback_pp'])} | {pp(r['score'])} | "
            f"{pp(r['covid_ex_score'])} | {r['years_helped'] or '—'} |"
        )

    lines += [
        "",
        "## Governance",
        "",
        "- Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN",
        f"- Claimed MDD: `{CLAIM_STATUS}`",
        "- Do not add to `ops_month_end_paper_pack.py` until human ACCEPT OPEN",
        "",
        "## Reproduce",
        "",
        "```bash",
        "python3 scripts/e45_m2_bil_fx_improve_paper.py",
        "```",
        "",
        f"Repro: `{OUT.relative_to(ROOT)}/` · Market: `{MARKET_PATH.relative_to(ROOT)}`",
        f"Inputs sha256: BIL=`{payload['inputs_sha256']['BIL'][:12]}…`, "
        f"USDTWD=`{payload['inputs_sha256']['USDTWD'][:12]}…`, "
        f"00720B=`{payload['inputs_sha256']['00720B'][:12]}…`",
        "",
    ]
    md = "\n".join(lines) + "\n"
    (OUT / "reports" / "E45_M2_BIL_FX_IMPROVE.md").write_text(md, encoding="utf-8")
    (RESEARCH / "E45_M2_BIL_FX_IMPROVE.md").write_text(md, encoding="utf-8")
    write_observe_awaiting()

    ballot = OPS / "E45_M2_RELOC_OBSERVE_OPEN_BALLOT_DRAFT.md"
    if ballot.exists():
        text = ballot.read_text(encoding="utf-8")
        if "E45_M2_BIL_FX_IMPROVE.md" not in text:
            ballot.write_text(
                text.rstrip()
                + "\n\n## Improve pack cross-link\n\n"
                + "- FX sensitivity + TWD twin paper: `research/e45/E45_M2_BIL_FX_IMPROVE.md`\n"
                + "- Observe OPEN prep (await ACCEPT): "
                "`research/ops/E45_M2_BIL_FX_OBSERVE_OPEN_AWAITING_ACCEPT.md`\n"
                + "- Status: **DRAFT / NOT OPEN** unchanged until human ACCEPT\n\n",
                encoding="utf-8",
            )
        ballot_zh = OPS / "E45_M2_RELOC_OBSERVE_OPEN_BALLOT_DRAFT.zh-TW.md"
        if ballot_zh.exists():
            z = ballot_zh.read_text(encoding="utf-8")
            if "E45_M2_BIL_FX_IMPROVE.md" not in z:
                ballot_zh.write_text(
                    z.rstrip()
                    + "\n\n## Improve pack 交叉連結\n\n"
                    + "- FX／TWD twin 論文：`research/e45/E45_M2_BIL_FX_IMPROVE.md`\n"
                    + "- Observe OPEN prep（等候 ACCEPT）："
                    "`research/ops/E45_M2_BIL_FX_OBSERVE_OPEN_AWAITING_ACCEPT.md`\n"
                    + "- 狀態：人類 ACCEPT 前維持 **DRAFT / NOT OPEN**\n\n",
                    encoding="utf-8",
                )

    roadmap = OPS / "E45_PAPER_RESEARCH_ROADMAP.md"
    if roadmap.exists():
        rt = roadmap.read_text(encoding="utf-8")
        if "E45_M2_BIL_FX_IMPROVE" not in rt:
            roadmap.write_text(
                rt.rstrip()
                + "\n\n| — | M2 BIL_FX improve (FX sens + TWD twin + observe prep) | "
                "**DONE — PAPER / AWAITING_HUMAN_ACCEPT** | "
                "`E45_M2_BIL_FX_IMPROVE.md` · freeze `E45_M2_BIL_FX_IMPROVE_V0_FROZEN.md` |\n",
                encoding="utf-8",
            )

    print(
        json.dumps(
            {
                "fx_pass": fx_pass,
                "twd_pass": twd_pass,
                "gates": payload["informational_gates"],
                "observe": "AWAITING_HUMAN_ACCEPT",
            },
            indent=2,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
