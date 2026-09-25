#!/usr/bin/env python3
"""COOL defending → buy 00632R (台50反1); cool ends → sell. Stage A paper only.

Charter: research/ops/COOL_T50_INV_SATELLITE_CHARTER.md
Soft-Frozen live KEEP · COOL_c8 params frozen · no live wire.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

import e16_clip_search_challenger as clip
import e16_soft_frozen_base as soft
import e22_dividend_accounting as e22div
import e45_defend_handoff_stagea_screen as stagea
from cool_c8_proxy_observe_helpers import FLOOR, build_cool_c8_exposure
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, load_market, window_stats
from e50_early_stack_combined_nav import FIN, TEL, e16_features, simulate_core
from portfolio_capital import DEFAULT_CAPITAL
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp
from sleeve_tilt_helpers import ALPHA as LIVE_SLEEVE_ALPHA, sleeve_signal_panel
from soft_assist_helpers import (
    BUY_LOW_ID,
    LIVE_KD,
    SELL_HIGH_ID,
    soft_boost_scores,
    soft_sell_panel,
)
from ta_indicator_catalog import build_low_high_catalog
from tw_share_lots import BOARD_LOT
from within_sleeve_alloc import (
    FIN_PRE_EXDIV_KD,
    TEL_EQUAL,
    build_kd_season_tilt_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "cool-t50-inv-satellite-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"
DEF_PRICE = ROOT / "data" / "def_proxies" / "00632R_ohlcv.csv"

CHARTER_ID = "COOL_T50_INV_SATELLITE_CHARTER"
SCREEN_ID = "COOL_T50_INV_SATELLITE_STAGEA_SCREEN"
HELDOUT = "heldout_2019_plus"
SEALED = "sealed_2023_plus"
E22_VERSION = e22div.DEFAULT_BOOKS_VERSION
BASE_ID = "BASE_LIVE_FUSE_COOL"
DEF_CODE = "00632R"

CAGR_FLOOR_PP = 0.20
HELD_MDD_MIN_PP = -0.25
SEALED_MDD_MIN_PP = 0.0
TIP_MDD_TOL_PP = -0.5
ALPHAS = (0.25, 0.50, 1.00)


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _pack(nav: pd.DataFrame) -> dict[str, Any]:
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


def _tip(base_nav: pd.DataFrame, chal_nav: pd.DataFrame) -> dict[str, Any]:
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
            out[wname] = {"mdd_improve_pp": None, "cagr_giveback_pp": None, "gate": "INSUFFICIENT"}
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
            "mdd_improve_pp": round(float(mdd_delta_pp(b_mdd, c_mdd)), 4),
            "cagr_giveback_pp": None if gb is None else round(float(gb), 4),
            "gate": "PASS",
        }
    return out


def _buy(kd, lows, k9_amp: float = 1.0) -> pd.DataFrame:
    out = soft_boost_scores(kd, lows[BUY_LOW_ID], 1.0)
    return soft_boost_scores(out, lows["K9_LT30"], float(k9_amp))


def _sell(highs, amp: float = 0.50) -> pd.DataFrame:
    return soft_sell_panel(highs[SELL_HIGH_ID], boost=float(amp))


def _sleeve_score(market, sleeve, alpha: float) -> pd.DataFrame:
    _p, _s, _t, _r, base_score = soft.build_soft_frozen_targets(market)
    tilt = sleeve_signal_panel(sleeve, "rsi_lt30", 14)
    return base_score + float(alpha) * tilt


def _target_live(score: pd.DataFrame, regime: pd.Series) -> pd.DataFrame:
    return clip.build_targets_with_clips(
        regime=regime,
        score=score,
        fin_lo=float(soft.SOFT_FROZEN_FIN_LO),
        fin_hi=float(soft.SOFT_FROZEN_FIN_HI),
        tel_lo=float(soft.SOFT_FROZEN_TEL_LO),
        tel_hi=float(soft.SOFT_FROZEN_TEL_HI),
        etf_lo=float(soft.SOFT_FROZEN_ETF_LO),
        etf_hi=float(soft.SOFT_FROZEN_ETF_HI),
    )


def _cool_from_offense(market, offense_nav: pd.DataFrame) -> pd.Series:
    nav_s = stagea._nav_series(offense_nav)
    feat = stagea._risk_features(market, nav_s)
    dates = pd.DatetimeIndex(nav_s.index)
    return build_cool_c8_exposure(dates, feat["proxy_mdd63"])


def load_inv_bars() -> pd.DataFrame:
    raw = pd.read_csv(DEF_PRICE, parse_dates=["date"])
    raw["code"] = DEF_CODE
    for c in ("open", "high", "low", "close", "adj_close"):
        if c not in raw.columns:
            raise ValueError(f"missing {c} in {DEF_PRICE}")
    raw["volume"] = raw.get("volume", 0)
    return raw[["date", "code", "open", "high", "low", "close", "adj_close", "volume"]]


def attach_inv(market: pd.DataFrame, inv: pd.DataFrame) -> tuple[pd.DataFrame, pd.Timestamp]:
    """Append 00632R on full equity calendar; pre-list = flat first close (DEF weight 0)."""
    m = market.copy()
    m["date"] = pd.to_datetime(m["date"])
    inv = inv.copy()
    inv["date"] = pd.to_datetime(inv["date"])
    eq_dates = pd.DatetimeIndex(sorted(m["date"].unique()))
    piv_o = inv.set_index("date")["open"].reindex(eq_dates)
    piv_c = inv.set_index("date")["close"].reindex(eq_dates)
    piv_a = inv.set_index("date")["adj_close"].reindex(eq_dates)
    first = piv_c.first_valid_index()
    if first is None:
        raise RuntimeError("00632R has no valid bars on equity calendar")
    # Forward-fill after list; back-fill flat pre-list so def_code exists every day.
    piv_o = piv_o.ffill().bfill()
    piv_c = piv_c.ffill().bfill()
    piv_a = piv_a.ffill().bfill()
    rows = pd.DataFrame(
        {
            "date": eq_dates,
            "code": DEF_CODE,
            "open": piv_o.to_numpy(),
            "high": piv_c.to_numpy(),
            "low": piv_c.to_numpy(),
            "close": piv_c.to_numpy(),
            "adj_close": piv_a.to_numpy(),
            "volume": 0.0,
        }
    )
    out = pd.concat([m, rows], ignore_index=True).sort_values(["date", "code"])
    return out, pd.Timestamp(first)


def build_schedule(
    target3: pd.DataFrame,
    cool: pd.Series,
    *,
    alpha: float,
    mode: str,
    listed_from: pd.Timestamp,
) -> pd.DataFrame:
    """mode=defending: DEF only when cool<1; mode=always: constant α*0.5 DEF abuse control."""
    idx = target3.index
    c = cool.reindex(idx).fillna(1.0).astype(float).clip(0.0, 1.0)
    listed = pd.Series(idx >= listed_from, index=idx)
    if mode == "defending":
        defending = (c < 1.0 - 1e-12) & listed
        residual = (1.0 - c).clip(lower=0.0)
        def_w = (float(alpha) * residual).where(defending, 0.0)
        eq_scale = c
    elif mode == "always":
        # Sanity: hold α*FLOOR-like weight every listed day (not promote path)
        def_w = pd.Series(float(alpha) * float(FLOOR), index=idx).where(listed, 0.0)
        eq_scale = pd.Series(1.0, index=idx)  # full Soft equity + extra DEF → may sum>1
        # Renormal note: simulate_core uses weights as equity scales; keep Soft unscaled
        # and let DEF sit on top only if sum<=1. Cap Soft to 1-def.
        eq_scale = (1.0 - def_w).clip(lower=0.0)
    else:
        raise ValueError(mode)
    sched = pd.DataFrame(
        {
            "Financial": target3["Financial"].astype(float) * eq_scale,
            "Telecom": target3["Telecom"].astype(float) * eq_scale,
            "0050": target3["0050"].astype(float) * eq_scale,
            "DEF": def_w.astype(float),
        },
        index=idx,
    )
    return sched


def _sim(market, target_or_sched, regime, dividends, *, scores, buy_ok, sell, exposure=None, schedule=None):
    kw: dict[str, Any] = dict(
        apply_e22=True,
        apply_stock_div=True,
        capital=float(DEFAULT_CAPITAL),
        lot_size=int(BOARD_LOT),
        financial_alloc=FIN_PRE_EXDIV_KD,
        telecom_alloc=TEL_EQUAL,
        fin_name_scores=scores,
        fin_buy_ok=buy_ok,
        fin_sell_scores=sell,
        e22_version=E22_VERSION,
    )
    if schedule is not None:
        kw["sleeve_weight_schedule"] = schedule
        kw["def_code"] = DEF_CODE
        # target still required; use Soft columns as placeholder
        tgt = target_or_sched[["Financial", "Telecom", "0050"]].copy()
    else:
        tgt = target_or_sched
        if exposure is not None:
            kw["e45_exposure"] = exposure.astype(float)
    nav, fills, meta = simulate_core(market, tgt, regime, dividends, **kw)
    if not bool(meta.get("exact_t1_ok")):
        raise RuntimeError("exact_t1_ok failed")
    return nav, int(len(fills)), meta


def _score_row(base_w, chal_w, tip, *, rid, alpha, mode, n_fills, mean_def, defend_frac):
    h, s = chal_w[HELDOUT], chal_w[SEALED]
    bh, bs = base_w[HELDOUT], base_w[SEALED]
    held_cagr_lift = cagr_delta_pp(bh.get("cagr"), h.get("cagr"), missing_as_zero=True)
    sealed_cagr_lift = cagr_delta_pp(bs.get("cagr"), s.get("cagr"), missing_as_zero=True)
    if held_cagr_lift is not None:
        held_cagr_lift = -float(held_cagr_lift)
    if sealed_cagr_lift is not None:
        sealed_cagr_lift = -float(sealed_cagr_lift)
    held_mdd_up = float(mdd_delta_pp(bh.get("max_drawdown"), h.get("max_drawdown")))
    sealed_mdd_up = float(mdd_delta_pp(bs.get("max_drawdown"), s.get("max_drawdown")))
    tip_clean = tip.get("ytd", {}).get("gate") == "PASS" and tip.get("trailing_1y", {}).get("gate") == "PASS"
    tip_mdd_ok = tip_clean and float(tip["ytd"].get("mdd_improve_pp") or -9) >= TIP_MDD_TOL_PP and float(
        tip["trailing_1y"].get("mdd_improve_pp") or -9
    ) >= TIP_MDD_TOL_PP
    gates = {
        "tip_clean": bool(tip_clean),
        "tip_mdd_ok": bool(tip_mdd_ok),
        "sealed_mdd": sealed_mdd_up >= SEALED_MDD_MIN_PP,
        "held_mdd": held_mdd_up >= HELD_MDD_MIN_PP,
        "held_cagr_floor": held_cagr_lift is not None and held_cagr_lift >= CAGR_FLOOR_PP,
    }
    score = (
        0.50 * ((held_cagr_lift or 0.0) + (sealed_cagr_lift or 0.0))
        + 0.50 * (held_mdd_up + sealed_mdd_up)
        - 0.25 * max(0.0, -(held_cagr_lift or 0.0))
    )
    return {
        "id": rid,
        "alpha": alpha,
        "mode": mode,
        "n_fills": n_fills,
        "mean_def": round(float(mean_def), 6),
        "defend_frac": round(float(defend_frac), 6),
        "windows": chal_w,
        "held_cagr_lift_pp": None if held_cagr_lift is None else round(held_cagr_lift, 4),
        "sealed_cagr_lift_pp": None if sealed_cagr_lift is None else round(sealed_cagr_lift, 4),
        "held_mdd_improve_pp": round(held_mdd_up, 4),
        "sealed_mdd_improve_pp": round(sealed_mdd_up, 4),
        "tip": tip,
        "gates": gates,
        "coexist": all(gates.values()),
        "score": round(float(score), 4),
    }


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    assert soft.SOFT_FROZEN_FIN_CLIP == [0.6, 0.8]
    assert DEF_PRICE.exists(), DEF_PRICE

    print("loading ...", flush=True)
    market0 = load_market()
    dividends = load_dividends()
    inv = load_inv_bars()
    market, listed_from = attach_inv(market0, inv)
    print(f"00632R listed_from={listed_from.date()} rows={len(inv)}", flush=True)

    _p, sleeve, _tgt, regime = e16_features(market0)  # Soft features from equity-only calendar
    # Align target/regime to market0 dates; schedule uses same index
    cal = pd.DatetimeIndex(pd.to_datetime(market0["date"]).drop_duplicates().sort_values())
    lows, highs = build_low_high_catalog(market0, cal, list(FIN))
    kd = build_kd_season_tilt_scores(
        market0,
        dividends,
        FIN,
        k_thresh=float(LIVE_KD["k_thresh"]),
        season_start=LIVE_KD["season_start"],
        season_end=LIVE_KD["season_end"],
        pre_days=int(LIVE_KD["pre_days"]),
        active_score=float(LIVE_KD["active_score"]),
    )
    buy_ok = build_pre_exdiv_window_buy_ok(
        cal, dividends, FIN, pre_days=int(LIVE_KD["pre_days"]), also_stock_ex=True
    )
    buy_live = _buy(kd, lows)
    sell_live = _sell(highs)
    score_live = _sleeve_score(market0, sleeve, float(LIVE_SLEEVE_ALPHA))
    tgt_live = _target_live(score_live, regime)

    print("offense NAV for cool ...", flush=True)
    fuse_off, _, _ = _sim(
        market0,
        tgt_live,
        regime,
        dividends,
        scores=buy_live,
        buy_ok=buy_ok,
        sell=sell_live,
        exposure=pd.Series(1.0, index=tgt_live.index),
    )
    cool = _cool_from_offense(market0, fuse_off)
    cool.to_frame("cool_exposure").to_csv(OUT / "exposure_cool.csv")
    defend_frac = float((cool < 1.0 - 1e-12).mean())
    print(f"cool defend_frac={defend_frac:.4f} floor={FLOOR}", flush=True)

    print(f"{BASE_ID} ...", flush=True)
    base_nav, n_base, _ = _sim(
        market0,
        tgt_live,
        regime,
        dividends,
        scores=buy_live,
        buy_ok=buy_ok,
        sell=sell_live,
        exposure=cool,
    )
    base_nav.to_csv(OUT / f"nav_{BASE_ID}.csv", index=False)
    base_w = _pack(base_nav)

    books: list[tuple[str, float, str]] = [(BASE_ID, 0.0, "base")]
    for a in ALPHAS:
        books.append((f"COOL_INV_A{int(a*100):02d}", float(a), "defending"))
    books.append(("ALWAYS_A50", 0.50, "always"))

    rows = []
    for i, (bid, alpha, mode) in enumerate(books, 1):
        print(f"  [{i}/{len(books)}] {bid} ...", flush=True)
        if mode == "base":
            tip = _tip(base_nav, base_nav)
            row = _score_row(
                base_w,
                base_w,
                tip,
                rid=bid,
                alpha=0.0,
                mode=mode,
                n_fills=n_base,
                mean_def=0.0,
                defend_frac=defend_frac,
            )
            row["coexist"] = False
            rows.append(row)
            continue
        sched = build_schedule(tgt_live, cool, alpha=alpha, mode=mode, listed_from=listed_from)
        sched.to_csv(OUT / f"schedule_{bid}.csv")
        nav, n_fills, _ = _sim(
            market,
            tgt_live,
            regime,
            dividends,
            scores=buy_live,
            buy_ok=buy_ok,
            sell=sell_live,
            schedule=sched,
        )
        nav.to_csv(OUT / f"nav_{bid}.csv", index=False)
        tip = _tip(base_nav, nav)
        row = _score_row(
            base_w,
            _pack(nav),
            tip,
            rid=bid,
            alpha=alpha,
            mode=mode,
            n_fills=n_fills,
            mean_def=float(sched["DEF"].mean()),
            defend_frac=defend_frac,
        )
        rows.append(row)

    chal = [r for r in rows if r["id"] != BASE_ID and r["mode"] == "defending"]
    hits = [r for r in chal if r["coexist"]]
    softs = [
        r
        for r in chal
        if r["gates"]["sealed_mdd"]
        and r["gates"]["held_mdd"]
        and r["gates"]["tip_mdd_ok"]
        and not r["gates"]["held_cagr_floor"]
    ]
    if hits:
        verdict = "COOL_INV_HIT"
    elif softs:
        verdict = "COOL_INV_SOFT"
    elif any(r["gates"]["tip_clean"] for r in chal):
        verdict = "MDD_BLOCK"
    else:
        verdict = "NO_LIFT"

    ranked = sorted(chal, key=lambda r: -float(r["score"]))
    payload = {
        "generated_at_utc": _utc(),
        "label": SCREEN_ID,
        "charter": f"research/ops/{CHARTER_ID}.md",
        "status": verdict,
        "live_wire": False,
        "soft_frozen_keep": True,
        "def_code": DEF_CODE,
        "cool_defend_frac": round(defend_frac, 6),
        "listed_from": str(listed_from.date()),
        "baseline": BASE_ID,
        "baseline_windows": base_w,
        "n_challengers": len(chal),
        "n_coexist": len(hits),
        "coexist_ids": [r["id"] for r in sorted(hits, key=lambda r: -r["score"])],
        "soft_ids": [r["id"] for r in softs],
        "best": (sorted(hits, key=lambda r: -r["score"])[0] if hits else (ranked[0] if ranked else None)),
        "ranked": ranked,
        "controls": [r for r in rows if r["mode"] in ("base", "always")],
    }
    (REP / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2) + "\n")
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(payload, indent=2) + "\n")

    lines = [
        f"# COOL × 台50反1 — Stage A Screen",
        "",
        f"Generated: `{payload['generated_at_utc']}`",
        f"Status: **{verdict}** · baseline `{BASE_ID}` · Soft-Frozen **KEEP** · live wire **false**",
        f"DEF=`{DEF_CODE}` · cool defend_frac=**{defend_frac:.2%}** · listed_from **{listed_from.date()}**",
        "",
        f"Coexist / HIT: **{len(hits)}** / {len(chal)}",
        "",
        "## Ranked (defending books)",
        "",
        "| book | α | CAGR↑ held | CAGR↑ seal | MDD↑ held | MDD↑ seal | tip | coexist |",
        "|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for r in ranked:
        tip_ok = "Y" if r["gates"]["tip_mdd_ok"] else "N"
        lines.append(
            f"| `{r['id']}` | {r['alpha']:.2f} | {r['held_cagr_lift_pp']:+.2f} | "
            f"{r['sealed_cagr_lift_pp']:+.2f} | {r['held_mdd_improve_pp']:+.2f} | "
            f"{r['sealed_mdd_improve_pp']:+.2f} | {tip_ok} | {'Y' if r['coexist'] else 'N'} |"
        )
    always = next(r for r in rows if r["id"] == "ALWAYS_A50")
    lines += [
        "",
        "## Sanity control",
        "",
        f"`ALWAYS_A50`: held CAGR↑ {always['held_cagr_lift_pp']:+.2f} · sealed MDD↑ {always['sealed_mdd_improve_pp']:+.2f} · tip={'Y' if always['gates']['tip_mdd_ok'] else 'N'} (not promote)",
        "",
        "## Binding",
        "",
        "1. Soft-Frozen live + COOL_c8 params **KEEP**.",
        "2. Even HIT → paper observe only; live `00632R` needs Class D ACCEPT.",
        "",
        "Repro: `PYTHONPATH=scripts python3 scripts/cool_t50_inv_satellite_stagea.py`",
        "",
        f"Label: `{SCREEN_ID}_{payload['generated_at_utc'][:10]}__{verdict}`",
        "",
    ]
    md = "\n".join(lines)
    (REP / f"{SCREEN_ID}.md").write_text(md)
    (OPS / f"{SCREEN_ID}.md").write_text(md)

    decision = {
        "label": "COOL_T50_INV_SATELLITE_DECISION",
        "generated_at_utc": _utc(),
        "status": verdict,
        "live_wire": False,
        "n_coexist": len(hits),
        "coexist_ids": payload["coexist_ids"],
        "soft_ids": payload["soft_ids"],
        "best": None if not payload["best"] else payload["best"]["id"],
        "charter": f"research/ops/{CHARTER_ID}.md",
        "stage_a": f"research/ops/{SCREEN_ID}.md",
    }
    dlines = [
        "# COOL × 台50反1 — Decision Pack (Stage A)",
        "",
        f"Date: 2026-09-25 · Generated `{decision['generated_at_utc']}`",
        f"Status: **{verdict}** · Soft-Frozen **KEEP** · live wire **false**",
        "",
        f"Human rule: Cool 成立買 `00632R`；結束賣出 · α grid {list(ALPHAS)}",
        "",
        f"Coexist / HIT: **{len(hits)}**.",
        "",
    ]
    if hits:
        b = sorted(hits, key=lambda r: -r["score"])[0]
        dlines += [
            f"Best: `{b['id']}` · held CAGR↑ **{b['held_cagr_lift_pp']:+.2f}** · "
            f"sealed MDD↑ **{b['sealed_mdd_improve_pp']:+.2f}**",
            "",
            "Next: paper observe ballot — not live.",
            "",
        ]
    elif softs:
        b = softs[0]
        dlines += [
            f"SOFT best: `{b['id']}` · held CAGR↑ {b['held_cagr_lift_pp']:+.2f} · "
            f"sealed MDD↑ {b['sealed_mdd_improve_pp']:+.2f} (CAGR floor miss).",
            "",
            "Binding: Soft-Frozen KEEP · no live `00632R` without new ACCEPT / objective change.",
            "",
        ]
    else:
        dlines += [
            "No tip-clean MDD-safe lift under predeclared gates.",
            "",
            "Binding: Soft-Frozen KEEP · reopen only with new mechanism or human objective change.",
            "",
        ]
    dlines += [f"Label: `COOL_T50_INV_SATELLITE_DECISION_2026-09-25__{verdict}`", ""]
    (OPS / "COOL_T50_INV_SATELLITE_DECISION_PACK.json").write_text(json.dumps(decision, indent=2) + "\n")
    (OPS / "COOL_T50_INV_SATELLITE_DECISION_PACK.md").write_text("\n".join(dlines))
    print(json.dumps({"verdict": verdict, "n_coexist": len(hits), "soft_ids": payload["soft_ids"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
