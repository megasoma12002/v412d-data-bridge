#!/usr/bin/env python3
"""FIN residual research Stage A — SLEEVE / EXEC / WITHIN / REBAL / CLOSE (paper).

Exact T+1 KEEP · Soft-Frozen live KEEP · no live wire.
Charter: research/ops/FIN_RESIDUAL_RESEARCH_STAGEA_CHARTER.md
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import e16_soft_frozen_base as soft
import e22_dividend_accounting as e22div
import live_cool_c8_cutover as cool_cut
import live_dh_fuse_cutover as fuse_cut
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, load_market, window_stats
from e50_early_stack_combined_nav import FIN, TEL, e16_features, simulate_core
from fuse_additive_helpers import SLEEVE_ALPHA
from live_fill_extreme_audit import _window_ext
from portfolio_capital import DEFAULT_CAPITAL
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp
from sleeve_tilt_helpers import (
    ALPHA,
    SIGN,
    SIGNAL_KIND,
    SIGNAL_WINDOW,
    rebuild_targets_from_score,
    sleeve_signal_panel,
)
from soft_assist_helpers import (
    LIVE_KD,
    build_observe_buy_scores,
    build_observe_sell_panel,
)
from ta_indicator_catalog import build_low_high_catalog
from tw_share_lots import BOARD_LOT
from within_sleeve_alloc import (
    FIN_EQUAL,
    FIN_PRE_EXDIV_KD,
    FIN_TOP2_EQUAL,
    TEL_EQUAL,
    TEL_PRE_EXDIV_KD,
    build_kd_season_tilt_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "fin-residual-research-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_RESIDUAL_RESEARCH_STAGEA_CHARTER"
SCREEN_ID = "FIN_RESIDUAL_RESEARCH_STAGEA_SCREEN"
DECISION_ID = "FIN_RESIDUAL_RESEARCH_STAGEA_DECISION_PACK"
BOOK_ID = "LIVE_FUSE_ADDITIVE_SELL_a75_COOL_c8"
HELDOUT = "heldout_2019_plus"
SEALED = "sealed_2023_plus"
SEALED_START = date(2023, 1, 1)

FILL_IMPROVE_PP = 0.25
MDD_SLACK_PP = -0.50
CAGR_GIVEBACK_MAX_PP = 0.50


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ohlc_panel_raw(market: pd.DataFrame, code: str) -> pd.DataFrame:
    m = market[market["code"].astype(str) == str(code)].copy()
    m["date"] = pd.to_datetime(m["date"]).dt.normalize()
    m = m.drop_duplicates("date").sort_values("date").set_index("date")
    for col in ("open", "high", "low", "close"):
        if col not in m.columns:
            m[col] = np.nan
    if m["high"].isna().all() and "adj_close" in m.columns:
        m["high"] = m["adj_close"]
        m["low"] = m["adj_close"]
        m["close"] = m["adj_close"]
        m["open"] = m["adj_close"]
    return m[["open", "high", "low", "close"]].astype(float)


def _ohlc_panel(market: pd.DataFrame, code: str) -> pd.DataFrame:
    m = market[market["code"].astype(str) == str(code)].copy()
    m["date"] = pd.to_datetime(m["date"]).dt.normalize()
    m = m.drop_duplicates("date").sort_values("date").set_index("date")
    for col in ("open", "high", "low", "close", "adj_close"):
        if col not in m.columns:
            m[col] = np.nan
    close = m["close"].astype(float)
    adj = m["adj_close"].astype(float)
    if adj.notna().any() and close.notna().any():
        factor = adj / close.replace(0, np.nan)
        factor = factor.ffill().bfill().fillna(1.0)
        out = pd.DataFrame(index=m.index)
        for col in ("open", "high", "low", "close"):
            out[col] = m[col].astype(float) * factor
        out["close"] = adj.where(adj.notna(), out["close"])
        return out
    return _ohlc_panel_raw(market, code)


def _fill_px_on_panel(
    raw_px: float,
    fill_d: pd.Timestamp,
    raw_panel: pd.DataFrame,
    adj_panel: pd.DataFrame,
) -> float:
    if fill_d in adj_panel.index and fill_d in raw_panel.index:
        raw_c = float(raw_panel.loc[fill_d, "close"])
        adj_c = float(adj_panel.loc[fill_d, "close"])
        if raw_c > 0 and np.isfinite(raw_c) and np.isfinite(adj_c):
            return float(raw_px) * (adj_c / raw_c)
    return float(raw_px)


def _sleeve(code: str) -> str:
    c = str(code)
    if c in set(FIN):
        return "FIN"
    if c in set(TEL):
        return "TEL"
    if c == "0050":
        return "0050"
    return "OTHER"


def _kd_panels(market: pd.DataFrame, dividends: pd.DataFrame):
    cal = pd.DatetimeIndex(pd.to_datetime(market["date"]).drop_duplicates().sort_values())
    kd = build_kd_season_tilt_scores(
        market,
        dividends,
        FIN,
        k_thresh=float(LIVE_KD["k_thresh"]),
        season_start=LIVE_KD["season_start"],
        season_end=LIVE_KD["season_end"],
        pre_days=int(LIVE_KD["pre_days"]),
        active_score=float(LIVE_KD["active_score"]),
    )
    buy_ok = build_pre_exdiv_window_buy_ok(
        cal,
        dividends,
        FIN,
        pre_days=int(LIVE_KD["pre_days"]),
        also_stock_ex=True,
    )
    lows, highs = build_low_high_catalog(market, cal, list(FIN))
    buy = build_observe_buy_scores(kd, lows)
    sell = build_observe_sell_panel(highs, boost=float(fuse_cut.SELL_BOOST_LIVE))
    # TEL KD scores for TEL_PRE_EXDIV_KD policy (optional)
    kd_tel = build_kd_season_tilt_scores(
        market,
        dividends,
        TEL,
        k_thresh=float(LIVE_KD["k_thresh"]),
        season_start=LIVE_KD["season_start"],
        season_end=LIVE_KD["season_end"],
        pre_days=int(LIVE_KD["pre_days"]),
        active_score=float(LIVE_KD["active_score"]),
    )
    buy_ok_tel = build_pre_exdiv_window_buy_ok(
        cal,
        dividends,
        TEL,
        pre_days=int(LIVE_KD["pre_days"]),
        also_stock_ex=True,
    )
    return kd, buy_ok, buy, sell, kd_tel, buy_ok_tel


def _rebuild_with_l1(
    score: pd.DataFrame,
    regime: pd.Series,
    *,
    l1_min: float,
    blend_old: float = soft.BLEND_OLD,
    blend_new: float = soft.BLEND_NEW,
) -> pd.DataFrame:
    out = []
    cur = soft.apply_soft_frozen_clips(soft.START_WEIGHTS.copy())
    for i, _dt in enumerate(score.index):
        pri = soft.REGIME_PRIORS[str(regime.iloc[i])]
        cand = np.maximum(pri + 0.10 * np.clip(score.iloc[i].to_numpy(), -2.0, 2.0), 0.0)
        cand = soft.apply_soft_frozen_clips(cand)
        desired = float(blend_old) * cur + float(blend_new) * cand
        desired = soft.apply_soft_frozen_clips(desired)
        if float(np.abs(desired - cur).sum()) >= float(l1_min):
            cur = desired
        out.append(cur.copy())
    return pd.DataFrame(out, index=score.index, columns=["Financial", "Telecom", "0050"])


def _champion_score(market: pd.DataFrame, sleeve: pd.DataFrame, *, alpha: float) -> pd.DataFrame:
    _p, _s, _t, _r, base_score = soft.build_soft_frozen_targets(market)
    tilt = sleeve_signal_panel(sleeve, SIGNAL_KIND, SIGNAL_WINDOW)
    return base_score + float(SIGN) * float(alpha) * tilt


def _run_book(
    market: pd.DataFrame,
    dividends: pd.DataFrame,
    *,
    target: pd.DataFrame,
    regime: pd.Series,
    buy: pd.DataFrame,
    buy_ok: pd.DataFrame,
    sell: pd.DataFrame,
    exposure: pd.Series | None,
    financial_alloc: str = FIN_PRE_EXDIV_KD,
    telecom_alloc: str = TEL_EQUAL,
    tel_scores: pd.DataFrame | None = None,
    tel_buy_ok: pd.DataFrame | None = None,
    cost_multiple: float = 1.0,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    kwargs: dict[str, Any] = dict(
        apply_e22=True,
        e22_version=e22div.PRESERVED_CASH_ON_EX,
        apply_stock_div=True,
        capital=float(DEFAULT_CAPITAL),
        lot_size=int(BOARD_LOT),
        financial_alloc=financial_alloc,
        telecom_alloc=telecom_alloc,
        fin_name_scores=buy,
        fin_buy_ok=buy_ok,
        fin_sell_scores=sell,
        cost_multiple=float(cost_multiple),
    )
    if tel_scores is not None:
        kwargs["tel_name_scores"] = tel_scores
    if tel_buy_ok is not None:
        kwargs["tel_buy_ok"] = tel_buy_ok
    if exposure is not None:
        kwargs["e45_exposure"] = exposure.astype(float)
    nav, fills, meta = simulate_core(market, target, regime, dividends, **kwargs)
    if not bool(meta.get("exact_t1_ok")):
        raise RuntimeError("exact_t1_ok failed")
    return nav, fills, meta


def _pack_windows(nav: pd.DataFrame) -> dict[str, Any]:
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


def _fin_buy_n5_sealed(fills: pd.DataFrame, market: pd.DataFrame) -> dict[str, Any]:
    if fills is None or fills.empty:
        return {"n": 0, "mean_n5": None, "fin_minus_tel_n5": None}
    f = fills.copy()
    f["fill_date"] = pd.to_datetime(f["fill_date"]).dt.normalize()
    f = f[f["fill_date"].dt.date >= SEALED_START].reset_index(drop=True)
    codes = sorted({str(c) for c in f["code"].astype(str)})
    panels = {c: _ohlc_panel(market, c) for c in codes}
    panels_raw = {c: _ohlc_panel_raw(market, c) for c in codes}
    rows = []
    for _, r in f.iterrows():
        code = str(r["code"])
        side = str(r["side"]).upper()
        fill_d = pd.Timestamp(r["fill_date"]).normalize()
        panel = panels.get(code, pd.DataFrame())
        raw = panels_raw.get(code, pd.DataFrame())
        px = _fill_px_on_panel(float(r["fill_price"]), fill_d, raw, panel)
        lo, hi, _ = _window_ext(panel, fill_d, 5)
        if lo is None or hi is None or lo <= 0 or hi <= 0:
            continue
        dist = (px - lo) / lo * 100.0 if side == "BUY" else (hi - px) / hi * 100.0
        rows.append({"sleeve": _sleeve(code), "side": side, "n5": float(dist)})
    if not rows:
        return {"n": 0, "mean_n5": None, "fin_minus_tel_n5": None}
    d = pd.DataFrame(rows)
    fin_buy = d[(d["sleeve"] == "FIN") & (d["side"] == "BUY")]
    tel_all = d[d["sleeve"] == "TEL"]
    fin_mean = float(fin_buy["n5"].mean()) if len(fin_buy) else None
    tel_mean = float(tel_all["n5"].mean()) if len(tel_all) else None
    gap = (
        round(fin_mean - tel_mean, 4)
        if fin_mean is not None and tel_mean is not None
        else None
    )
    return {
        "n": int(len(fin_buy)),
        "mean_n5": None if fin_mean is None else round(fin_mean, 4),
        "tel_mean_n5": None if tel_mean is None else round(tel_mean, 4),
        "fin_minus_tel_n5": gap,
        "n_all_sealed": int(len(d)),
    }


def _vs_nav(base_w: dict, chal_w: dict, key: str) -> dict[str, Any]:
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
    }


def _eval(
    *,
    track: str,
    cid: str,
    fill: dict[str, Any],
    base_fill: dict[str, Any],
    nav_vs: dict[str, Any],
) -> dict[str, Any]:
    b_n5, c_n5 = base_fill.get("mean_n5"), fill.get("mean_n5")
    improve = (
        round(float(b_n5) - float(c_n5), 4)
        if b_n5 is not None and c_n5 is not None
        else None
    )
    fill_gate = improve is not None and float(improve) >= FILL_IMPROVE_PP
    gb, md = nav_vs.get("cagr_giveback_pp"), nav_vs.get("mdd_improve_pp")
    nav_gate = (
        md is not None
        and float(md) >= MDD_SLACK_PP
        and gb is not None
        and float(gb) <= CAGR_GIVEBACK_MAX_PP
    )
    return {
        "track": track,
        "id": cid,
        "fill": fill,
        "fill_improve_pp": improve,
        "fill_gate": bool(fill_gate),
        "nav_heldout": nav_vs,
        "nav_gate": bool(nav_gate),
        "hit": bool(fill_gate and nav_gate),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    REP.mkdir(parents=True, exist_ok=True)
    OPS.mkdir(parents=True, exist_ok=True)

    print("loading market ...", flush=True)
    market = load_market()
    dividends = load_dividends()
    _prices, sleeve, _lt, regime = e16_features(market)
    kd, buy_ok, buy, sell, kd_tel, buy_ok_tel = _kd_panels(market, dividends)
    target_live = fuse_cut.fuse_target_for_market(market)
    live_score = _champion_score(market, sleeve, alpha=float(ALPHA))

    print("building BASE_FUSE_COOL ...", flush=True)
    fuse_nav, _, _ = fuse_cut.build_fuse_offense_sim(market, dividends)
    cool_live = cool_cut.build_cool_exposure_from_offense(market, fuse_nav)
    base_nav, base_fills, base_meta = _run_book(
        market,
        dividends,
        target=target_live,
        regime=regime,
        buy=buy,
        buy_ok=buy_ok,
        sell=sell,
        exposure=cool_live,
    )
    base_win = _pack_windows(base_nav)
    base_fill = _fin_buy_n5_sealed(base_fills, market)
    print(
        f"BASE sealed FIN_BUY n5={base_fill.get('mean_n5')} n={base_fill.get('n')}",
        flush=True,
    )

    specs: list[dict[str, Any]] = [
        {"track": "SLEEVE", "id": "S_ALPHA_0", "kind": "alpha0"},
        {"track": "SLEEVE", "id": "S_TEL_PRE_EXDIV_KD", "kind": "tel_kd"},
        {"track": "EXEC", "id": "E_COST_0", "kind": "cost", "cm": 0.0},
        {"track": "EXEC", "id": "E_COST_2", "kind": "cost", "cm": 2.0},
        {"track": "WITHIN", "id": "W_FIN_EQUAL", "kind": "fin_alloc", "alloc": FIN_EQUAL},
        {
            "track": "WITHIN",
            "id": "W_FIN_TOP2_EQUAL",
            "kind": "fin_alloc",
            "alloc": FIN_TOP2_EQUAL,
        },
        {"track": "REBAL", "id": "R_L1_05", "kind": "l1", "l1": 0.05},
        {"track": "REBAL", "id": "R_L1_10", "kind": "l1", "l1": 0.10},
    ]

    rows: list[dict[str, Any]] = []
    for spec in specs:
        cid = spec["id"]
        print(f"building {cid} ...", flush=True)
        target = target_live
        buy_u, buy_ok_u, sell_u = buy, buy_ok, sell
        exposure: pd.Series | None = cool_live
        fin_alloc = FIN_PRE_EXDIV_KD
        tel_alloc = TEL_EQUAL
        tel_scores = None
        tel_buy_ok = None
        cm = 1.0

        if spec["kind"] == "alpha0":
            score0 = _champion_score(market, sleeve, alpha=0.0)
            target = rebuild_targets_from_score(score0, regime)
            off_nav, _, _ = _run_book(
                market,
                dividends,
                target=target,
                regime=regime,
                buy=buy_u,
                buy_ok=buy_ok_u,
                sell=sell_u,
                exposure=None,
            )
            exposure = cool_cut.build_cool_exposure_from_offense(market, off_nav)
        elif spec["kind"] == "tel_kd":
            tel_alloc = TEL_PRE_EXDIV_KD
            tel_scores = kd_tel
            tel_buy_ok = buy_ok_tel
            off_nav, _, _ = _run_book(
                market,
                dividends,
                target=target,
                regime=regime,
                buy=buy_u,
                buy_ok=buy_ok_u,
                sell=sell_u,
                exposure=None,
                telecom_alloc=tel_alloc,
                tel_scores=tel_scores,
                tel_buy_ok=tel_buy_ok,
            )
            exposure = cool_cut.build_cool_exposure_from_offense(market, off_nav)
        elif spec["kind"] == "cost":
            cm = float(spec["cm"])
            # cool path unchanged (cost is fill/NAV only)
        elif spec["kind"] == "fin_alloc":
            fin_alloc = str(spec["alloc"])
            off_nav, _, _ = _run_book(
                market,
                dividends,
                target=target,
                regime=regime,
                buy=buy_u,
                buy_ok=buy_ok_u,
                sell=sell_u,
                exposure=None,
                financial_alloc=fin_alloc,
            )
            exposure = cool_cut.build_cool_exposure_from_offense(market, off_nav)
        elif spec["kind"] == "l1":
            target = _rebuild_with_l1(live_score, regime, l1_min=float(spec["l1"]))
            off_nav, _, _ = _run_book(
                market,
                dividends,
                target=target,
                regime=regime,
                buy=buy_u,
                buy_ok=buy_ok_u,
                sell=sell_u,
                exposure=None,
            )
            exposure = cool_cut.build_cool_exposure_from_offense(market, off_nav)
        else:
            raise ValueError(spec["kind"])

        nav, fills, meta = _run_book(
            market,
            dividends,
            target=target,
            regime=regime,
            buy=buy_u,
            buy_ok=buy_ok_u,
            sell=sell_u,
            exposure=exposure,
            financial_alloc=fin_alloc,
            telecom_alloc=tel_alloc,
            tel_scores=tel_scores,
            tel_buy_ok=tel_buy_ok,
            cost_multiple=cm,
        )
        win = _pack_windows(nav)
        fill = _fin_buy_n5_sealed(fills, market)
        nav_vs = _vs_nav(base_win, win, HELDOUT)
        row = _eval(
            track=spec["track"],
            cid=cid,
            fill=fill,
            base_fill=base_fill,
            nav_vs=nav_vs,
        )
        row["spec"] = {k: v for k, v in spec.items() if k != "kind"}
        row["n_fills"] = int(len(fills))
        row["exact_t1_ok"] = bool(meta.get("exact_t1_ok"))
        row["cost_multiple"] = cm
        row["windows"] = {HELDOUT: win.get(HELDOUT), SEALED: win.get(SEALED)}
        rows.append(row)
        print(
            f"  {cid}: fill_improve={row['fill_improve_pp']} "
            f"fill_gate={row['fill_gate']} nav_gate={row['nav_gate']} hit={row['hit']}",
            flush=True,
        )

    hits = [r for r in rows if r["hit"]]
    fill_only = [r for r in rows if r["fill_gate"] and not r["nav_gate"]]
    nav_only = [r for r in rows if r["nav_gate"] and not r["fill_gate"]]
    any_fill = any(r["fill_gate"] for r in rows)

    track_verdicts: dict[str, str] = {}
    for track in ("SLEEVE", "EXEC", "WITHIN", "REBAL"):
        tr = [r for r in rows if r["track"] == track]
        if any(r["hit"] for r in tr):
            track_verdicts[track] = f"{track}_HIT"
        elif any(r["fill_gate"] for r in tr):
            track_verdicts[track] = f"{track}_FILL_ONLY"
        else:
            track_verdicts[track] = f"{track}_NO_LIFT"

    if hits:
        verdict = "SIGNAL_HIT"
        close_rec = False
    elif fill_only:
        verdict = "FILL_BETTER_NAV_COST"
        close_rec = False
    elif not any_fill:
        verdict = "CLOSE_OBSERVE_RECOMMENDED"
        close_rec = True
    elif nav_only:
        verdict = "NAV_ONLY"
        close_rec = False
    else:
        verdict = "NO_LIFT"
        close_rec = False

    track_verdicts["CLOSE"] = (
        "CLOSE_OBSERVE_RECOMMENDED" if close_rec else "CLOSE_NOT_YET"
    )

    generated = _utc()
    payload: dict[str, Any] = {
        "schema_version": "fin_residual_research_stagea_v1",
        "id": SCREEN_ID,
        "generated_at": generated,
        "status": verdict,
        "live_wire": False,
        "exact_t1": "KEEP",
        "soft_frozen_live": "KEEP",
        "ohlc_basis": "adj_close_scaled",
        "book_id": BOOK_ID,
        "sleeve_alpha_live": float(SLEEVE_ALPHA),
        "gates": {
            "fill_improve_pp": FILL_IMPROVE_PP,
            "mdd_slack_pp": MDD_SLACK_PP,
            "cagr_giveback_max_pp": CAGR_GIVEBACK_MAX_PP,
            "fill_window": SEALED,
            "nav_window": HELDOUT,
        },
        "base": {
            "id": "BASE_FUSE_COOL",
            "n_fills": int(len(base_fills)),
            "exact_t1_ok": bool(base_meta.get("exact_t1_ok")),
            "fill_sealed_fin_buy": base_fill,
            "windows": {
                HELDOUT: base_win.get(HELDOUT),
                SEALED: base_win.get(SEALED),
            },
        },
        "challengers": rows,
        "track_verdicts": track_verdicts,
        "close_observe_recommended": bool(close_rec),
        "binding": [
            "Soft-Frozen live KEEP",
            "Exact T+1 KEEP",
            "No tip rewrite",
            "No live wire from this Stage A",
            "At most one track for follow-up ACCEPT discussion",
        ],
    }

    lines = [
        "# FIN residual research Stage A — Screen",
        "",
        f"Generated: `{generated}`",
        f"Status: **`{verdict}`** · Soft-Frozen KEEP · Exact T+1 KEEP · **no live wire** · `{BOOK_ID}`",
        "",
        "## Track verdicts",
        "",
        "| track | verdict |",
        "|---|---|",
    ]
    for t, v in track_verdicts.items():
        lines.append(f"| `{t}` | `{v}` |")
    lines += [
        "",
        "## Base (sealed FIN BUY fill)",
        "",
        f"n={base_fill.get('n')} · ±5d mean **{base_fill.get('mean_n5')}%** · "
        f"FIN−TEL **{base_fill.get('fin_minus_tel_n5')}pp**",
        "",
        "## Challengers",
        "",
        "| id | track | fill Δpp | fill gate | MDD Δpp | CAGR gb | nav gate | HIT |",
        "|---|---|---:|:---:|---:|---:|:---:|:---:|",
    ]
    for r in rows:
        nv = r["nav_heldout"]
        lines.append(
            f"| `{r['id']}` | `{r['track']}` | {r['fill_improve_pp']} | "
            f"{'Y' if r['fill_gate'] else 'n'} | {nv.get('mdd_improve_pp')} | "
            f"{nv.get('cagr_giveback_pp')} | {'Y' if r['nav_gate'] else 'n'} | "
            f"{'Y' if r['hit'] else 'n'} |"
        )
    read = {
        "SIGNAL_HIT": "≥1 residual challenger clears fill + NAV.",
        "FILL_BETTER_NAV_COST": "fill improves; NAV outside band.",
        "NAV_ONLY": "NAV near-flat; fill gate not cleared.",
        "NO_LIFT": "no fill gate clearance.",
        "CLOSE_OBSERVE_RECOMMENDED": (
            "Tracks 1–4 all miss fill gate → recommend close this residual "
            "observe menu; tip monitor only; Exact T+1 KEEP."
        ),
    }[verdict]
    lines += [
        "",
        "### Read",
        "",
        read,
        "",
        "Repro: `PYTHONPATH=scripts python3 scripts/fin_residual_research_stagea.py`",
        "",
        f"Label: `{SCREEN_ID}_{generated[:10].replace('-', '')}__{verdict}`",
        "",
    ]
    screen_md = "\n".join(lines)

    decision = {
        "schema_version": "fin_residual_research_stagea_decision_v1",
        "id": DECISION_ID,
        "generated_at": generated,
        "status": verdict,
        "track_verdicts": track_verdicts,
        "live_wire": False,
        "exact_t1": "KEEP",
        "hits": [r["id"] for r in hits],
        "fill_only": [r["id"] for r in fill_only],
        "close_observe_recommended": bool(close_rec),
        "binding": payload["binding"],
        "next": (
            "CLOSE_OBSERVE — tip monitor only; do not reopen C/D/B signal grid "
            "or this residual menu without a new human lever"
            if close_rec
            else "Discussion only — pick ZERO or ONE track; Exact T+1 KEEP"
        ),
        "label": f"{DECISION_ID}_{generated[:10].replace('-', '')}__{verdict}",
    }
    decision_md = "\n".join(
        [
            "# FIN residual research Stage A — Decision Pack",
            "",
            f"Date: 2026-09-26 · Generated `{generated}`",
            f"Status: **{verdict}** · Soft-Frozen **KEEP** · Exact T+1 **KEEP** · live wire **false**",
            "",
            "Tracks: "
            + " · ".join(f"`{track_verdicts[t]}`" for t in track_verdicts),
            "",
            "## Binding",
            "",
            "1. Soft-Frozen live KEEP",
            "2. Exact T+1 KEEP",
            "3. No tip rewrite",
            "4. No live wire from this Stage A",
            "5. At most one track for follow-up ACCEPT discussion",
            "",
            f"Next: {decision['next']}",
            "",
            f"Label: `{decision['label']}`",
            "",
        ]
    )

    for path, obj in (
        (OUT / f"{SCREEN_ID}.json", payload),
        (REP / f"{SCREEN_ID}.json", payload),
        (OPS / f"{SCREEN_ID}.json", payload),
        (OUT / f"{DECISION_ID}.json", decision),
        (REP / f"{DECISION_ID}.json", decision),
        (OPS / f"{DECISION_ID}.json", decision),
    ):
        path.write_text(json.dumps(obj, indent=2) + "\n")
    for path, text in (
        (OUT / f"{SCREEN_ID}.md", screen_md),
        (REP / f"{SCREEN_ID}.md", screen_md),
        (OPS / f"{SCREEN_ID}.md", screen_md),
        (OUT / f"{DECISION_ID}.md", decision_md),
        (REP / f"{DECISION_ID}.md", decision_md),
        (OPS / f"{DECISION_ID}.md", decision_md),
    ):
        path.write_text(text)

    (REPRO / "README.md").write_text(
        "\n".join(
            [
                "# FIN residual research Stage A",
                "",
                "SLEEVE / EXEC / WITHIN / REBAL / CLOSE · Exact T+1 KEEP.",
                "",
                "```bash",
                "PYTHONPATH=scripts python3 scripts/fin_residual_research_stagea.py",
                "```",
                "",
            ]
        )
    )
    print(
        json.dumps(
            {
                "verdict": verdict,
                "tracks": track_verdicts,
                "hits": decision["hits"],
                "close_observe_recommended": close_rec,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
