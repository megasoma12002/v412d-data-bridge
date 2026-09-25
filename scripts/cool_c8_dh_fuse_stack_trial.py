#!/usr/bin/env python3
"""Paper trial: stack vs replace COOL_c8 on live DH_dd06 + FUSE_ADDITIVE.

Finite books (Stage-E DEFAULT · Soft-Frozen KEEP · no live wire):
  LIVE_STACK          Soft-Frozen + KD_OPT + TEL_EQUAL
  FUSE_ONLY           FUSE_ADDITIVE offense (no risk overlay)
  FUSE_DH             live recipe = FUSE + DH_dd06
  FUSE_COOL           不疊 = FUSE + COOL_c8 (replace DH)
  FUSE_DH_x_COOL      疊 = FUSE + (DH × COOL)
  FUSE_DH_min_COOL    疊 = FUSE + min(DH, COOL)
  LIVE_COOL           observe twin (LIVE_STACK + COOL) for reference

Primary window: heldout_2019_plus. Tip YTD / 1y vs FUSE_DH.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

import e16_soft_frozen_base as soft
import e21_forward_pipeline as e21
import e22_dividend_accounting as e22div
import e45_defend_handoff_stagea_screen as stagea
from cool_c8_proxy_observe_helpers import (
    COOL,
    EXIT_X,
    FLOOR,
    MAX_DWELL,
    PROXY_X,
    build_cool_c8_exposure,
)
from e45_defend_handoff_helpers import DD_THRESHOLD, SHRINK, VOL_Z_THRESHOLD
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, load_market, window_stats
from e50_early_stack_combined_nav import FIN, e16_features, simulate_core
from fuse_additive_helpers import (
    LIVE_KD,
    build_champion_target,
    build_observe_buy_scores,
    build_observe_sell_panel,
)
from portfolio_capital import DEFAULT_CAPITAL
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp
from sleeve_tilt_helpers import ALPHA as SLEEVE_ALPHA
from ta_indicator_catalog import build_low_high_catalog
from tw_share_lots import BOARD_LOT
from within_sleeve_alloc import (
    FIN_PRE_EXDIV_KD,
    TEL_EQUAL,
    build_kd_season_tilt_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "repro/cool-c8-dh-fuse-stack-trial"
OPS = ROOT / "research/ops"
CAPITAL = float(DEFAULT_CAPITAL)
LOT = int(BOARD_LOT)
FOCUS = ("full", "heldout_2019_plus", "sealed_2023_plus")
E22_VERSION = e22div.DEFAULT_BOOKS_VERSION
TRIAL_ID = "COOL_C8_DH_FUSE_STACK_TRIAL"
BASE_LIVE = "FUSE_DH"  # compare deltas vs current live recipe


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_book(
    market,
    target,
    regime,
    dividends,
    *,
    scores,
    buy_ok,
    sell_scores=None,
    exposure=None,
):
    kwargs: dict[str, Any] = dict(
        apply_e22=True,
        apply_stock_div=True,
        capital=CAPITAL,
        lot_size=LOT,
        financial_alloc=FIN_PRE_EXDIV_KD,
        telecom_alloc=TEL_EQUAL,
        fin_name_scores=scores,
        fin_buy_ok=buy_ok,
        e22_version=E22_VERSION,
    )
    if sell_scores is not None:
        kwargs["fin_sell_scores"] = sell_scores
    if exposure is not None:
        kwargs["e45_exposure"] = exposure.astype(float)
    nav, fills, meta = simulate_core(market, target, regime, dividends, **kwargs)
    if not bool(meta.get("exact_t1_ok")):
        raise RuntimeError("exact_t1_ok failed")
    return {"nav": nav, "n_fills": int(len(fills)), "meta": meta}


def make_dh_exposure(market, offense_nav: pd.DataFrame) -> pd.Series:
    nav_s = stagea._nav_series(offense_nav)
    feat = stagea._risk_features(market, nav_s)
    dates = pd.DatetimeIndex(nav_s.index)
    return stagea._build_exposure(dates, feat, DD_THRESHOLD, VOL_Z_THRESHOLD)


def make_cool_exposure(market, offense_nav: pd.DataFrame) -> pd.Series:
    nav_s = stagea._nav_series(offense_nav)
    feat = stagea._risk_features(market, nav_s)
    dates = pd.DatetimeIndex(nav_s.index)
    return build_cool_c8_exposure(dates, feat["proxy_mdd63"])


def pack_windows(nav: pd.DataFrame) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, (a, b) in WINDOWS_STANDARD.items():
        st = window_stats(nav, a, b)
        out[k] = {
            "cagr": None if st.get("cagr") is None else round(float(st["cagr"]), 6),
            "max_drawdown": None
            if st.get("max_drawdown") is None
            else round(float(st["max_drawdown"]), 6),
            "n_days": int(st.get("n_days") or 0),
        }
    return out


def vs_base(base_w: dict, chal_w: dict, key: str) -> dict[str, Any]:
    b, c = base_w[key], chal_w[key]
    gb = cagr_delta_pp(b.get("cagr"), c.get("cagr"), missing_as_zero=True)
    md = mdd_delta_pp(b.get("max_drawdown"), c.get("max_drawdown"))
    return {
        "base_cagr": b.get("cagr"),
        "chal_cagr": c.get("cagr"),
        "base_mdd": b.get("max_drawdown"),
        "chal_mdd": c.get("max_drawdown"),
        "cagr_giveback_pp": None if gb is None else round(float(gb), 4),
        "mdd_improve_pp": round(float(md), 4),
        "score": round(float(md) - 0.5 * abs(float(gb or 0.0)), 4),
    }


def tip_vs(base_nav: pd.DataFrame, chal_nav: pd.DataFrame) -> dict[str, Any]:
    asof = pd.Timestamp(pd.to_datetime(base_nav["date"]).max())
    b_dates = pd.to_datetime(base_nav["date"])
    c_dates = pd.to_datetime(chal_nav["date"])
    out: dict[str, Any] = {}
    for wname, start in (
        ("ytd", pd.Timestamp(asof.year, 1, 1)),
        ("trailing_1y", asof - pd.Timedelta(days=365)),
    ):
        b = base_nav[(b_dates >= start) & (b_dates <= asof)].reset_index(drop=True)
        c = chal_nav[(c_dates >= start) & (c_dates <= asof)].reset_index(drop=True)
        if len(b) < 20 or len(c) < 20:
            out[wname] = {
                "mdd_improve_pp": None,
                "cagr_giveback_pp": None,
                "gate": "INSUFFICIENT",
            }
            continue
        bn = b["nav"].astype(float) / float(b["nav"].iloc[0])
        cn = c["nav"].astype(float) / float(c["nav"].iloc[0])
        b_mdd = float((bn / bn.cummax() - 1.0).min())
        c_mdd = float((cn / cn.cummax() - 1.0).min())
        years = (len(b) - 1) / 252.0
        bc = float(bn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        cc = float(cn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        gb = cagr_delta_pp(bc, cc)
        out[wname] = {
            "base_mdd": round(b_mdd, 6),
            "chal_mdd": round(c_mdd, 6),
            "mdd_improve_pp": round(float(mdd_delta_pp(b_mdd, c_mdd)), 4),
            "cagr_giveback_pp": None if gb is None else round(float(gb), 4),
            "gate": "PASS",
        }
    return out


def fmt_pct(x) -> str:
    return "n/a" if x is None else f"{100.0 * float(x):.2f}%"


def fmt_pp(x) -> str:
    return "n/a" if x is None else f"{float(x):+.2f}pp"


def frac_defense(exp: pd.Series) -> float:
    return float((exp.astype(float) < 0.999).mean())


def main() -> int:
    (OUT / "outputs").mkdir(parents=True, exist_ok=True)
    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    OPS.mkdir(parents=True, exist_ok=True)

    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.8]
    for k in ("season_start", "season_end", "k_thresh", "pre_days", "active_score"):
        if LIVE_KD[k] != e21.KD_OPT[k]:
            raise SystemExit(f"LIVE_KD[{k}] drift vs e21.KD_OPT")
    if e21.LIVE_E45_STITCH:
        raise SystemExit("Refuse while LIVE_E45_STITCH is True")

    print("loading ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _prices, sleeve, target_live, regime = e16_features(market)
    cal = pd.DatetimeIndex(pd.to_datetime(market["date"]).drop_duplicates().sort_values())
    lows, highs = build_low_high_catalog(market, cal, list(FIN))

    kd_scores = build_kd_season_tilt_scores(
        market,
        dividends,
        FIN,
        k_thresh=float(LIVE_KD["k_thresh"]),
        season_start=LIVE_KD["season_start"],
        season_end=LIVE_KD["season_end"],
        pre_days=int(LIVE_KD["pre_days"]),
        active_score=float(LIVE_KD["active_score"]),
    )
    kd_ok = build_pre_exdiv_window_buy_ok(
        cal, dividends, FIN, pre_days=int(LIVE_KD["pre_days"]), also_stock_ex=True
    )
    soft_buy = build_observe_buy_scores(kd_scores, lows)
    soft_sell = build_observe_sell_panel(highs)
    target_fuse = build_champion_target(market, sleeve, regime)

    books: dict[str, Any] = {}
    exposures: dict[str, pd.Series] = {}

    print("LIVE_STACK ...", flush=True)
    live = run_book(market, target_live, regime, dividends, scores=kd_scores, buy_ok=kd_ok)
    books["LIVE_STACK"] = live

    print("LIVE_COOL (observe twin) ...", flush=True)
    exp_live_cool = make_cool_exposure(market, live["nav"])
    exposures["LIVE_COOL"] = exp_live_cool
    books["LIVE_COOL"] = run_book(
        market,
        target_live,
        regime,
        dividends,
        scores=kd_scores,
        buy_ok=kd_ok,
        exposure=exp_live_cool,
    )

    print("FUSE_ONLY ...", flush=True)
    fuse_off = run_book(
        market,
        target_fuse,
        regime,
        dividends,
        scores=soft_buy,
        buy_ok=kd_ok,
        sell_scores=soft_sell,
    )
    books["FUSE_ONLY"] = fuse_off

    print("exposures on FUSE offense (DH / COOL / stack) ...", flush=True)
    exp_dh = make_dh_exposure(market, fuse_off["nav"])
    exp_cool = make_cool_exposure(market, fuse_off["nav"])
    aligned = exp_dh.align(exp_cool, join="inner")
    dh_a, cool_a = aligned[0].astype(float), aligned[1].astype(float)
    exp_prod = (dh_a * cool_a).clip(lower=0.0, upper=1.0)
    exp_min = pd.concat([dh_a, cool_a], axis=1).min(axis=1)

    exposures["FUSE_DH"] = exp_dh
    exposures["FUSE_COOL"] = exp_cool
    exposures["FUSE_DH_x_COOL"] = exp_prod
    exposures["FUSE_DH_min_COOL"] = exp_min

    for name, exp in (
        ("FUSE_DH", exp_dh),
        ("FUSE_COOL", exp_cool),
        ("FUSE_DH_x_COOL", exp_prod),
        ("FUSE_DH_min_COOL", exp_min),
    ):
        print(f"  {name} frac_defense={frac_defense(exp):.4f} ...", flush=True)
        books[name] = run_book(
            market,
            target_fuse,
            regime,
            dividends,
            scores=soft_buy,
            buy_ok=kd_ok,
            sell_scores=soft_sell,
            exposure=exp,
        )

    for name, book in books.items():
        book["nav"].to_csv(OUT / "outputs" / f"nav_{name}.csv", index=False)
    for tag, exp in exposures.items():
        exp.rename("e45_exposure").to_frame().to_csv(
            OUT / "outputs" / f"exposure_{tag}.csv"
        )

    win = {name: pack_windows(book["nav"]) for name, book in books.items()}
    base_w = win[BASE_LIVE]
    compare_ids = [
        "LIVE_STACK",
        "LIVE_COOL",
        "FUSE_ONLY",
        "FUSE_COOL",
        "FUSE_DH_x_COOL",
        "FUSE_DH_min_COOL",
    ]
    compare = {
        mid: {w: vs_base(base_w, win[mid], w) for w in FOCUS} for mid in compare_ids
    }
    # also self-row for FUSE_DH absolute levels
    tip = {
        mid: tip_vs(books[BASE_LIVE]["nav"], books[mid]["nav"]) for mid in compare_ids
    }

    exp_meta = {
        tag: {
            "frac_defense": round(frac_defense(exp), 6),
            "mean_exposure": round(float(exp.astype(float).mean()), 6),
            "min_exposure": round(float(exp.astype(float).min()), 6),
        }
        for tag, exp in exposures.items()
    }

    payload = {
        "schema_version": "cool_c8_dh_fuse_stack_trial_v1",
        "trial_id": TRIAL_ID,
        "generated_at_utc": _utc(),
        "status": "PAPER_TRIAL_ONLY",
        "live_wire": False,
        "e22_books_version": E22_VERSION,
        "soft_frozen_fin_clip": list(soft.SOFT_FROZEN_FIN_CLIP),
        "compare_base": BASE_LIVE,
        "recipe": {
            "fuse_sleeve_alpha": float(SLEEVE_ALPHA),
            "dh_dd": float(DD_THRESHOLD),
            "dh_vol_z": float(VOL_Z_THRESHOLD),
            "dh_shrink": float(SHRINK),
            "cool_proxy_x": float(PROXY_X),
            "cool_floor": float(FLOOR),
            "cool_exit_x": float(EXIT_X),
            "cool_max_dwell": int(MAX_DWELL),
            "cool_cool": int(COOL),
        },
        "books": {
            name: {
                "n_fills": book.get("n_fills"),
                "windows": win[name],
            }
            for name, book in books.items()
        },
        "exposure_meta": exp_meta,
        "vs_fuse_dh": compare,
        "tip_vs_fuse_dh": tip,
        "construction": {
            "LIVE_STACK": "Soft-Frozen + KD_OPT + TEL_EQUAL · e45=None",
            "LIVE_COOL": "LIVE_STACK + COOL_c8 (observe twin)",
            "FUSE_ONLY": "FUSE_ADDITIVE offense · e45=None",
            "FUSE_DH": "FUSE + DH_dd06 (= current live)",
            "FUSE_COOL": "不疊 · FUSE + COOL_c8 (replace DH)",
            "FUSE_DH_x_COOL": "疊 · FUSE + (DH × COOL)",
            "FUSE_DH_min_COOL": "疊 · FUSE + min(DH, COOL)",
        },
        "non_actions": [
            "Paper diagnose only — no live wire / Soft-Frozen flip",
            "Does not authorize cutover; checklist stays BLOCKED",
        ],
    }

    order = [
        "LIVE_STACK",
        "LIVE_COOL",
        "FUSE_ONLY",
        "FUSE_DH",
        "FUSE_COOL",
        "FUSE_DH_min_COOL",
        "FUSE_DH_x_COOL",
    ]

    def row(name: str) -> str:
        h = win[name]["heldout_2019_plus"]
        if name == BASE_LIVE:
            dlt = "—"
            md = "—"
        else:
            v = compare[name]["heldout_2019_plus"]
            dlt = fmt_pp(v["cagr_giveback_pp"])
            md = fmt_pp(v["mdd_improve_pp"])
        tag = {
            "FUSE_DH": "live 現況",
            "FUSE_COOL": "不疊",
            "FUSE_DH_min_COOL": "疊 min",
            "FUSE_DH_x_COOL": "疊 ×",
            "LIVE_COOL": "observe",
            "FUSE_ONLY": "offense",
            "LIVE_STACK": "base",
        }.get(name, "")
        return (
            f"| `{name}` | {tag} | {fmt_pct(h['cagr'])} | {fmt_pct(h['max_drawdown'])} "
            f"| {dlt} | {md} |"
        )

    lines = [
        "# COOL_c8 × DH_dd06+FUSE — stack vs replace paper trial",
        "",
        f"Generated: `{payload['generated_at_utc']}`  ",
        f"Books: Stage-E `{E22_VERSION}` · Soft-Frozen KEEP · **no live wire**  ",
        f"Compare base: `{BASE_LIVE}` (= current live FUSE+DH)",
        "",
        "## Construction",
        "",
        "| ID | Meaning |",
        "|---|---|",
        "| `FUSE_DH` | live 現況 = FUSE + DH |",
        "| `FUSE_COOL` | **不疊** = FUSE + COOL（取代 DH） |",
        "| `FUSE_DH_min_COOL` | **疊** = FUSE + min(DH, COOL) |",
        "| `FUSE_DH_x_COOL` | **疊** = FUSE + (DH × COOL) |",
        "| `LIVE_COOL` | observe twin（無 FUSE） |",
        "",
        "## Held-out 2019+ (primary)",
        "",
        "| book | role | CAGR | MDD | vs FUSE_DH CAGR giveback | vs FUSE_DH MDD↑ |",
        "|---|---|---:|---:|---:|---:|",
    ]
    lines += [row(n) for n in order]

    lines += [
        "",
        "## Sealed 2023+",
        "",
        "| book | CAGR | MDD | vs FUSE_DH gb | vs FUSE_DH MDD↑ |",
        "|---|---:|---:|---:|---:|",
    ]
    for name in order:
        h = win[name]["sealed_2023_plus"]
        if name == BASE_LIVE:
            lines.append(
                f"| `{name}` | {fmt_pct(h['cagr'])} | {fmt_pct(h['max_drawdown'])} | — | — |"
            )
        else:
            v = compare[name]["sealed_2023_plus"]
            lines.append(
                f"| `{name}` | {fmt_pct(h['cagr'])} | {fmt_pct(h['max_drawdown'])} "
                f"| {fmt_pp(v['cagr_giveback_pp'])} | {fmt_pp(v['mdd_improve_pp'])} |"
            )

    lines += [
        "",
        "## Exposure duty",
        "",
        "| exposure | frac_defense | mean | min |",
        "|---|---:|---:|---:|",
    ]
    for tag in (
        "LIVE_COOL",
        "FUSE_DH",
        "FUSE_COOL",
        "FUSE_DH_min_COOL",
        "FUSE_DH_x_COOL",
    ):
        m = exp_meta[tag]
        lines.append(
            f"| `{tag}` | {m['frac_defense']:.4f} | {m['mean_exposure']:.4f} | {m['min_exposure']:.4f} |"
        )

    lines += [
        "",
        "## Tip vs FUSE_DH (YTD / trailing 1y)",
        "",
        "| book | ytd MDD↑ | ytd gb | 1y MDD↑ | 1y gb |",
        "|---|---:|---:|---:|---:|",
    ]
    for name in ("FUSE_COOL", "FUSE_DH_min_COOL", "FUSE_DH_x_COOL", "LIVE_COOL"):
        t = tip[name]
        y, o = t["ytd"], t["trailing_1y"]
        lines.append(
            f"| `{name}` | {fmt_pp(y.get('mdd_improve_pp'))} | {fmt_pp(y.get('cagr_giveback_pp'))} "
            f"| {fmt_pp(o.get('mdd_improve_pp'))} | {fmt_pp(o.get('cagr_giveback_pp'))} |"
        )

    lines += [
        "",
        "## Reading",
        "",
        "- **不疊 (`FUSE_COOL`)**：用 COOL 換掉 DH；對齊 |MDD|≤17% 路線的單層 PROXY。",
        "- **疊 min**：兩層都開時仍只縮到 50%；防衛日取聯集。",
        "- **疊 ×**：兩層同時防衛可縮到 25%；防衛更深、giveback 通常更大。",
        "- 本 trial **不**授權 live；cutover 仍 BLOCKED。",
        "",
        f"Repro: `repro/cool-c8-dh-fuse-stack-trial/`",
        "",
        f"Label: `{TRIAL_ID}_{_utc()[:10]}__PAPER_ONLY__NO_LIVE_WIRE`",
        "",
    ]

    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    (OUT / "outputs" / "stack_trial_summary.json").write_text(text, encoding="utf-8")
    (OUT / "reports" / f"{TRIAL_ID}.json").write_text(text, encoding="utf-8")
    (OPS / f"{TRIAL_ID}.json").write_text(text, encoding="utf-8")
    md = "\n".join(lines) + "\n"
    (OUT / "reports" / f"{TRIAL_ID}.md").write_text(md, encoding="utf-8")
    (OPS / f"{TRIAL_ID}.md").write_text(md, encoding="utf-8")
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
