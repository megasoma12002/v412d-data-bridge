#!/usr/bin/env python3
"""FIN signal improve Stage A — C_CLIP / D_COOL / B_KD (paper only).

Exact T+1 KEEP · Soft-Frozen live KEEP · no live wire.
Charter: research/ops/FIN_SIGNAL_CLIP_COOL_KD_STAGEA_CHARTER.md
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import e16_clip_search_challenger as clip
import e16_soft_frozen_base as soft
import e22_dividend_accounting as e22div
import live_cool_c8_cutover as cool_cut
import live_dh_fuse_cutover as fuse_cut
from cool_c8_proxy_observe_helpers import (
    COOL,
    EXIT_X,
    MAX_DWELL,
    PROXY_X,
    build_cool_c8_exposure,
)
from e45_paper_harness import WINDOWS_STANDARD, load_dividends, load_market, window_stats
from e50_early_stack_combined_nav import FIN, TEL, e16_features, simulate_core
from fuse_additive_helpers import SLEEVE_ALPHA
from live_fill_extreme_audit import _in_kd_season, _window_ext
from portfolio_capital import DEFAULT_CAPITAL
from research_metric_helpers import cagr_delta_pp, mdd_delta_pp
from sleeve_tilt_helpers import (
    ALPHA,
    SIGN,
    SIGNAL_KIND,
    SIGNAL_WINDOW,
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
    FIN_PRE_EXDIV_KD,
    TEL_EQUAL,
    build_kd_season_tilt_scores,
    build_pre_exdiv_window_buy_ok,
)

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "fin-signal-clip-cool-kd-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_SIGNAL_CLIP_COOL_KD_STAGEA_CHARTER"
SCREEN_ID = "FIN_SIGNAL_CLIP_COOL_KD_STAGEA_SCREEN"
DECISION_ID = "FIN_SIGNAL_CLIP_COOL_KD_STAGEA_DECISION_PACK"
BOOK_ID = "LIVE_FUSE_ADDITIVE_SELL_a75_COOL_c8"
HELDOUT = "heldout_2019_plus"
SEALED = "sealed_2023_plus"
SEALED_START = date(2023, 1, 1)

FILL_IMPROVE_PP = 0.25
MDD_SLACK_PP = -0.50
CAGR_GIVEBACK_MAX_PP = 0.50

LIVE_TEL = (float(soft.SOFT_FROZEN_TEL_LO), float(soft.SOFT_FROZEN_TEL_HI))
LIVE_ETF = (float(soft.SOFT_FROZEN_ETF_LO), float(soft.SOFT_FROZEN_ETF_HI))
LIVE_FIN_LO = float(soft.SOFT_FROZEN_FIN_LO)
LIVE_FIN_HI = float(soft.SOFT_FROZEN_FIN_HI)


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
    """adj_close-scaled OHLC (authoritative for fill-distance gates)."""
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
    return kd, buy_ok, buy, sell


def _champion_target_with_clips(
    market: pd.DataFrame,
    sleeve: pd.DataFrame,
    regime: pd.Series,
    *,
    fin_lo: float,
    fin_hi: float,
) -> pd.DataFrame:
    _p, _s, _t, _r, base_score = soft.build_soft_frozen_targets(market)
    tilt = sleeve_signal_panel(sleeve, SIGNAL_KIND, SIGNAL_WINDOW)
    new_score = base_score + float(SIGN) * float(ALPHA) * tilt
    return clip.build_targets_with_clips(
        regime=regime,
        score=new_score,
        fin_lo=float(fin_lo),
        fin_hi=float(fin_hi),
        tel_lo=LIVE_TEL[0],
        tel_hi=LIVE_TEL[1],
        etf_lo=LIVE_ETF[0],
        etf_hi=LIVE_ETF[1],
    )


def _cool_floor(dates: pd.DatetimeIndex, proxy_mdd63: pd.Series, floor: float) -> pd.Series:
    """COOL_c8 circuit with challenger floor (live PROXY/EXIT/dwell/cool frozen)."""
    px = proxy_mdd63.reindex(dates).fillna(0.0)
    out = pd.Series(1.0, index=dates, dtype=float)
    defending = False
    dwell = 0
    cool_left = 0
    floor_f = float(floor)
    for i in range(len(dates)):
        v = float(px.iloc[i])
        if cool_left > 0:
            out.iloc[i] = 1.0
            cool_left -= 1
            defending = False
            dwell = 0
            continue
        if not defending:
            if v <= -float(PROXY_X):
                defending = True
                dwell = 1
                out.iloc[i] = floor_f
            else:
                out.iloc[i] = 1.0
        else:
            dwell += 1
            if v >= -float(EXIT_X) or dwell >= int(MAX_DWELL):
                defending = False
                dwell = 0
                cool_left = int(COOL)
                out.iloc[i] = 1.0
            else:
                out.iloc[i] = floor_f
    return out


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
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    kwargs: dict[str, Any] = dict(
        apply_e22=True,
        e22_version=e22div.PRESERVED_CASH_ON_EX,
        apply_stock_div=True,
        capital=float(DEFAULT_CAPITAL),
        lot_size=int(BOARD_LOT),
        financial_alloc=FIN_PRE_EXDIV_KD,
        telecom_alloc=TEL_EQUAL,
        fin_name_scores=buy,
        fin_buy_ok=buy_ok,
        fin_sell_scores=sell,
    )
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


def _fin_buy_n5_sealed(
    fills: pd.DataFrame, market: pd.DataFrame
) -> dict[str, Any]:
    if fills is None or fills.empty:
        return {"n": 0, "mean_n5": None, "fin_minus_tel_n5": None}
    f = fills.copy()
    f["signal_date"] = pd.to_datetime(f["signal_date"]).dt.normalize()
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
        if side == "BUY":
            dist = (px - lo) / lo * 100.0
        else:
            dist = (hi - px) / hi * 100.0
        rows.append({"sleeve": _sleeve(code), "side": side, "n5": float(dist)})
    if not rows:
        return {"n": 0, "mean_n5": None, "fin_minus_tel_n5": None}
    d = pd.DataFrame(rows)
    fin_buy = d[(d["sleeve"] == "FIN") & (d["side"] == "BUY")]
    tel_all = d[d["sleeve"] == "TEL"]
    fin_mean = float(fin_buy["n5"].mean()) if len(fin_buy) else None
    tel_mean = float(tel_all["n5"].mean()) if len(tel_all) else None
    gap = None
    if fin_mean is not None and tel_mean is not None:
        gap = round(fin_mean - tel_mean, 4)
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


def _eval_chal(
    *,
    track: str,
    cid: str,
    fill: dict[str, Any],
    base_fill: dict[str, Any],
    nav_vs: dict[str, Any],
) -> dict[str, Any]:
    b_n5 = base_fill.get("mean_n5")
    c_n5 = fill.get("mean_n5")
    improve = None
    if b_n5 is not None and c_n5 is not None:
        improve = round(float(b_n5) - float(c_n5), 4)
    fill_gate = improve is not None and float(improve) >= FILL_IMPROVE_PP
    gb = nav_vs.get("cagr_giveback_pp")
    md = nav_vs.get("mdd_improve_pp")
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
    _prices, sleeve, _live_target, regime = e16_features(market)
    kd, buy_ok_live, buy_live, sell_live = _kd_panels(market, dividends)
    target_live = fuse_cut.fuse_target_for_market(market)

    print("building BASE_FUSE_COOL ...", flush=True)
    fuse_nav, _, _ = fuse_cut.build_fuse_offense_sim(market, dividends)
    cool_live = cool_cut.build_cool_exposure_from_offense(market, fuse_nav)
    base_nav, base_fills, base_meta = _run_book(
        market,
        dividends,
        target=target_live,
        regime=regime,
        buy=buy_live,
        buy_ok=buy_ok_live,
        sell=sell_live,
        exposure=cool_live,
    )
    base_win = _pack_windows(base_nav)
    base_fill = _fin_buy_n5_sealed(base_fills, market)
    print(
        f"BASE sealed FIN_BUY n5={base_fill.get('mean_n5')} n={base_fill.get('n')}",
        flush=True,
    )

    challengers_spec: list[dict[str, Any]] = [
        {
            "track": "C_CLIP",
            "id": "C_FIN_HI_075",
            "kind": "clip",
            "fin_hi": 0.75,
        },
        {
            "track": "C_CLIP",
            "id": "C_FIN_HI_090",
            "kind": "clip",
            "fin_hi": 0.90,
        },
        {"track": "D_COOL", "id": "D_COOL_OFF", "kind": "cool_off"},
        {
            "track": "D_COOL",
            "id": "D_COOL_FLOOR_070",
            "kind": "cool_floor",
            "floor": 0.70,
        },
        {
            "track": "B_KD",
            "id": "B_KD_BUYOK_ALWAYS",
            "kind": "kd_buyok_always",
        },
        {
            "track": "B_KD",
            "id": "B_KD_OFFSEASON_NO_BUY",
            "kind": "kd_offseason_no_buy",
        },
    ]

    rows: list[dict[str, Any]] = []
    for spec in challengers_spec:
        cid = spec["id"]
        print(f"building {cid} ...", flush=True)
        target = target_live
        buy = buy_live
        buy_ok = buy_ok_live
        sell = sell_live
        exposure: pd.Series | None = cool_live

        if spec["kind"] == "clip":
            target = _champion_target_with_clips(
                market,
                sleeve,
                regime,
                fin_lo=LIVE_FIN_LO,
                fin_hi=float(spec["fin_hi"]),
            )
            # rebuild cool from clip offense
            off_nav, _, _ = _run_book(
                market,
                dividends,
                target=target,
                regime=regime,
                buy=buy,
                buy_ok=buy_ok,
                sell=sell,
                exposure=None,
            )
            exposure = cool_cut.build_cool_exposure_from_offense(market, off_nav)
        elif spec["kind"] == "cool_off":
            exposure = None
        elif spec["kind"] == "cool_floor":
            off_nav, _, _ = _run_book(
                market,
                dividends,
                target=target,
                regime=regime,
                buy=buy,
                buy_ok=buy_ok,
                sell=sell,
                exposure=None,
            )
            import e45_defend_handoff_stagea_screen as stagea

            nav_s = stagea._nav_series(off_nav)
            feat = stagea._risk_features(market, nav_s)
            dates = pd.DatetimeIndex(nav_s.index)
            exposure = _cool_floor(dates, feat["proxy_mdd63"], float(spec["floor"]))
        elif spec["kind"] == "kd_buyok_always":
            buy_ok = pd.DataFrame(
                True, index=buy_ok_live.index, columns=buy_ok_live.columns
            )
            off_nav, _, _ = _run_book(
                market,
                dividends,
                target=target,
                regime=regime,
                buy=buy,
                buy_ok=buy_ok,
                sell=sell,
                exposure=None,
            )
            exposure = cool_cut.build_cool_exposure_from_offense(market, off_nav)
        elif spec["kind"] == "kd_offseason_no_buy":
            mask = pd.Series(
                [_in_kd_season(pd.Timestamp(i)) for i in buy_ok_live.index],
                index=buy_ok_live.index,
            )
            buy_ok = buy_ok_live.copy()
            for col in buy_ok.columns:
                buy_ok.loc[~mask, col] = False
            off_nav, _, _ = _run_book(
                market,
                dividends,
                target=target,
                regime=regime,
                buy=buy,
                buy_ok=buy_ok,
                sell=sell,
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
            buy=buy,
            buy_ok=buy_ok,
            sell=sell,
            exposure=exposure,
        )
        win = _pack_windows(nav)
        fill = _fin_buy_n5_sealed(fills, market)
        nav_vs = _vs_nav(base_win, win, HELDOUT)
        row = _eval_chal(
            track=spec["track"],
            cid=cid,
            fill=fill,
            base_fill=base_fill,
            nav_vs=nav_vs,
        )
        row["spec"] = {k: v for k, v in spec.items() if k != "kind"}
        row["n_fills"] = int(len(fills))
        row["exact_t1_ok"] = bool(meta.get("exact_t1_ok"))
        row["has_cool"] = exposure is not None
        row["windows"] = {
            HELDOUT: win.get(HELDOUT),
            SEALED: win.get(SEALED),
        }
        rows.append(row)
        print(
            f"  {cid}: fill_improve={row['fill_improve_pp']} "
            f"fill_gate={row['fill_gate']} nav_gate={row['nav_gate']} hit={row['hit']}",
            flush=True,
        )

    hits = [r for r in rows if r["hit"]]
    fill_only = [r for r in rows if r["fill_gate"] and not r["nav_gate"]]
    nav_only = [r for r in rows if r["nav_gate"] and not r["fill_gate"]]

    if hits:
        verdict = "SIGNAL_HIT"
    elif fill_only:
        verdict = "FILL_BETTER_NAV_COST"
    elif nav_only and not any(r["fill_gate"] for r in rows):
        verdict = "NAV_ONLY"
    else:
        verdict = "NO_LIFT"

    track_verdicts: dict[str, str] = {}
    for track in ("C_CLIP", "D_COOL", "B_KD"):
        tr = [r for r in rows if r["track"] == track]
        if any(r["hit"] for r in tr):
            track_verdicts[track] = f"{track}_HIT"
        elif any(r["fill_gate"] for r in tr):
            track_verdicts[track] = f"{track}_FILL_ONLY"
        else:
            track_verdicts[track] = f"{track}_NO_LIFT"

    generated = _utc()
    payload: dict[str, Any] = {
        "schema_version": "fin_signal_clip_cool_kd_stagea_v1",
        "id": SCREEN_ID,
        "generated_at": generated,
        "status": verdict,
        "live_wire": False,
        "exact_t1": "KEEP",
        "soft_frozen_live": "KEEP",
        "ohlc_basis": "adj_close_scaled",
        "book_id": BOOK_ID,
        "sleeve_alpha": float(SLEEVE_ALPHA),
        "live_fin_clip": [LIVE_FIN_LO, LIVE_FIN_HI],
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
        "binding": [
            "Soft-Frozen live KEEP",
            "Exact T+1 KEEP",
            "No tip rewrite",
            "No live wire from this Stage A",
            "At most one track for follow-up ACCEPT discussion",
        ],
    }

    # markdown screen
    lines = [
        "# FIN signal improve Stage A — Screen",
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
    lines += [
        "",
        "### Read",
        "",
        {
            "SIGNAL_HIT": "≥1 paper signal challenger clears fill + NAV gates.",
            "FILL_BETTER_NAV_COST": "fill improves but NAV outside band.",
            "NAV_ONLY": "NAV near-flat/better; fill gate not cleared.",
            "NO_LIFT": "no challenger clears fill gate.",
        }[verdict],
        "",
        "Repro: `PYTHONPATH=scripts python3 scripts/fin_signal_clip_cool_kd_stagea.py`",
        "",
        f"Label: `{SCREEN_ID}_{generated[:10].replace('-', '')}__{verdict}`",
        "",
    ]
    screen_md = "\n".join(lines)

    decision = {
        "schema_version": "fin_signal_clip_cool_kd_stagea_decision_v1",
        "id": DECISION_ID,
        "generated_at": generated,
        "status": verdict,
        "track_verdicts": track_verdicts,
        "live_wire": False,
        "exact_t1": "KEEP",
        "hits": [r["id"] for r in hits],
        "fill_only": [r["id"] for r in fill_only],
        "binding": payload["binding"],
        "next": (
            "Discussion only — pick ZERO or ONE track for follow-up; "
            "do not batch-retune Soft-Frozen / COOL / KD from this Stage A; "
            "Exact T+1 stays KEEP"
        ),
        "label": f"{DECISION_ID}_{generated[:10].replace('-', '')}__{verdict}",
    }
    decision_md = "\n".join(
        [
            "# FIN signal improve Stage A — Decision Pack",
            "",
            f"Date: 2026-09-26 · Generated `{generated}`",
            f"Status: **{verdict}** · Soft-Frozen **KEEP** · Exact T+1 **KEEP** · live wire **false**",
            "",
            f"Tracks: `{track_verdicts.get('C_CLIP')}` · `{track_verdicts.get('D_COOL')}` · "
            f"`{track_verdicts.get('B_KD')}`",
            "",
            "## Binding",
            "",
            "1. Soft-Frozen live KEEP",
            "2. Exact T+1 KEEP",
            "3. No tip rewrite",
            "4. No live wire from this Stage A",
            "5. At most one track for follow-up ACCEPT discussion",
            "",
            "Next: Discussion only — pick ZERO or ONE track; do not batch-retune",
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
                "# FIN signal improve Stage A (C_CLIP / D_COOL / B_KD)",
                "",
                "Exact T+1 KEEP · Soft-Frozen live KEEP · no live wire.",
                "",
                "```bash",
                "PYTHONPATH=scripts python3 scripts/fin_signal_clip_cool_kd_stagea.py",
                "```",
                "",
            ]
        )
    )
    print(json.dumps({"verdict": verdict, "tracks": track_verdicts, "hits": decision["hits"]}, indent=2))


if __name__ == "__main__":
    main()
