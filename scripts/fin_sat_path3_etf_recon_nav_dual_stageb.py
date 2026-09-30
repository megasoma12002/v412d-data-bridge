#!/usr/bin/env python3
"""Path3 0050 ETF recon — Stage B paper NAV dual (improvement vs KEEP).

Parent 0kae: champion ``LEDGER_SOFT_RATIO`` on flip probes.
This pack rebuilds Soft-core (FIN∪TEL∪0050) path NAV under Path3 flips:

- ``KEEP`` — on flip, recon FIN∪TEL to dest Soft-core mix; **sticky 0050 weight**
- ``LEDGER_SOFT_RATIO`` — on flip, full Soft-core weights → dest book (incl. 0050)
- ``FULL_DAILY`` — context: every day Soft-core weights = active book (cutover-like)

**Fill timing (default ``t0``):** flip-day recon **before** same-day close-to-close
return — aligns with live ``T0_CARVE_FIN_SAT_SWITCH`` same-bar / MOC Path3 fill.
Optional ``eod_t1``: earn with old weights then EOD recon (prior pack).

Between flips: hold Soft-core weights (Path3-carve-only paper; no Soft Exact T+1).
Soft-Frozen KEEP · broker false · cutover BLOCKED · no live.
Register: 0kag
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from e16_soft_frozen_base import FIN, TEL
from e45_paper_harness import WINDOWS_STANDARD, window_stats
from fin_sell_quality_helpers import cagr_lift_pp
from live_path3_t0_switch_emitter import BOOK_COMP, BOOK_SAT, load_or_build_signal
from ops_repro_ssot import write_ops_and_repro_pointer, write_repro_pointer
from path3_comp_sat_daily_share_ssot import load_book_shares
from research_metric_helpers import mdd_delta_pp

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "fin-sat-path3-etf-recon-nav-dual-stageb"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "FIN_SAT_PATH3_ETF_RECON_NAV_DUAL_STAGEB_CHARTER"
SCREEN_ID = "FIN_SAT_PATH3_ETF_RECON_NAV_DUAL_STAGEB_SCREEN"
DECISION_ID = "FIN_SAT_PATH3_ETF_RECON_NAV_DUAL_STAGEB_DECISION_PACK"
REGISTER = "0kag"

ETF = "0050"
SOFT_CORE = list(FIN) + list(TEL) + [ETF]
MARKET = ROOT / "forward/e21/live_market.csv"
CTRL_NAV = ROOT / "repro/fin-sat-composite-dual-paper-observe/outputs/ctrl_live_a10_daily_nav.csv"
P3_NAV = ROOT / "repro/fin-sat-path3-t0-dual-paper-observe/outputs/p3_t0_state_daily_nav.csv"

# Gates (paper HIT): held lift>0 · sealed MDD not worse than -0.25pp vs KEEP · tipY not < -1pp
SEALED_MDD_FLOOR_PP = -0.25
TIP_Y_FLOOR_PP = -1.0


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _close_panel(codes: list[str]) -> pd.DataFrame:
    m = pd.read_csv(MARKET, dtype={"code": str}, parse_dates=["date"])
    m = m[m["code"].isin(codes)]
    px = (
        m.pivot_table(index="date", columns="code", values="close", aggfunc="last")
        .sort_index()
        .astype(float)
    )
    return px.reindex(columns=codes)


def _book_soft_weights(panel: pd.DataFrame, px: pd.DataFrame) -> pd.DataFrame:
    """EOD Soft-core dollar weights by date (rows sum≈1)."""
    dates = panel.index.intersection(px.index)
    w = pd.DataFrame(0.0, index=dates, columns=SOFT_CORE)
    for c in SOFT_CORE:
        if c not in panel.columns or c not in px.columns:
            continue
        w[c] = panel.loc[dates, c].astype(float) * px.loc[dates, c].astype(float)
    tot = w.sum(axis=1).replace(0.0, np.nan)
    w = w.div(tot, axis=0).fillna(0.0)
    return w


def _pack(nav: pd.DataFrame) -> dict[str, Any]:
    out = {}
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


def _tip(base: pd.DataFrame, chal: pd.DataFrame) -> dict[str, Any]:
    asof = pd.Timestamp(pd.to_datetime(base["date"]).max())
    b_dates = pd.to_datetime(base["date"])
    c_dates = pd.to_datetime(chal["date"])
    out: dict[str, Any] = {}
    for wname, start in (
        ("ytd", pd.Timestamp(asof.year, 1, 1)),
        ("trailing_1y", asof - pd.Timedelta(days=365)),
    ):
        b = base[(b_dates >= start) & (b_dates <= asof)].reset_index(drop=True)
        c = chal[(c_dates >= start) & (c_dates <= asof)].reset_index(drop=True)
        if len(b) < 20 or len(c) < 20:
            out[wname] = {"cagr_lift_pp": None, "mdd_improve_pp": None}
            continue
        bn = b["nav"].astype(float) / float(b["nav"].iloc[0])
        cn = c["nav"].astype(float) / float(c["nav"].iloc[0])
        b_mdd = float((bn / bn.cummax() - 1.0).min())
        c_mdd = float((cn / cn.cummax() - 1.0).min())
        years = (len(b) - 1) / 252.0
        bc = float(bn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        cc = float(cn.iloc[-1]) ** (1 / years) - 1 if years > 0 else None
        out[wname] = {
            "cagr_lift_pp": None if cagr_lift_pp(bc, cc) is None else round(float(cagr_lift_pp(bc, cc)), 4),
            "mdd_improve_pp": round(float(mdd_delta_pp(b_mdd, c_mdd)), 4),
        }
    return out


def _apply_flip_weights(
    *,
    policy: str,
    w_prev: np.ndarray,
    w_dest: np.ndarray,
    etf_idx: int,
    fin_tel_idx: list[int],
) -> np.ndarray:
    """Return new Soft-core weights after Path3 flip."""
    if policy == "LEDGER_SOFT_RATIO":
        out = w_dest.astype(float).copy()
        s = out.sum()
        return out / s if s > 1e-12 else w_prev.copy()

    if policy == "KEEP":
        etf_w = float(w_prev[etf_idx])
        etf_w = min(max(etf_w, 0.0), 1.0)
        ft = w_dest[fin_tel_idx].astype(float).copy()
        ft_sum = float(ft.sum())
        out = np.zeros_like(w_prev, dtype=float)
        out[etf_idx] = etf_w
        if ft_sum > 1e-12 and etf_w < 1.0 - 1e-12:
            out[fin_tel_idx] = ft / ft_sum * (1.0 - etf_w)
        elif etf_w >= 1.0 - 1e-12:
            out[etf_idx] = 1.0
        else:
            # no FIN/TEL in dest — keep prev FIN∪TEL mass
            prev_ft = w_prev[fin_tel_idx]
            psum = float(prev_ft.sum())
            if psum > 1e-12:
                out[fin_tel_idx] = prev_ft / psum * (1.0 - etf_w)
            else:
                out[etf_idx] = 1.0
        s = out.sum()
        return out / s if s > 1e-12 else w_prev.copy()

    raise ValueError(policy)


def _maybe_flip_recon(
    *,
    d: pd.Timestamp,
    w: np.ndarray,
    policy: str,
    sig_by_date: pd.DataFrame,
    weights_by_book: dict[str, pd.DataFrame],
    etf_idx: int,
    fin_tel_idx: list[int],
) -> tuple[np.ndarray, bool, float]:
    """Apply flip recon if signal says flip on ``d``. Returns (w, flipped, |Δw_etf|)."""
    if d not in sig_by_date.index:
        return w, False, 0.0
    srow = sig_by_date.loc[d]
    if isinstance(srow, pd.DataFrame):
        srow = srow.iloc[-1]
    if not bool(srow.get("flip", False)):
        return w, False, 0.0
    book = str(srow.get("book") or BOOK_COMP)
    if book not in weights_by_book or d not in weights_by_book[book].index:
        return w, False, 0.0
    w_dest = weights_by_book[book].loc[d, SOFT_CORE].to_numpy(dtype=float)
    if w_dest.sum() <= 1e-12:
        return w, False, 0.0
    w_dest = w_dest / w_dest.sum()
    w_before = w.copy()
    w_new = _apply_flip_weights(
        policy=policy, w_prev=w, w_dest=w_dest, etf_idx=etf_idx, fin_tel_idx=fin_tel_idx
    )
    dw = abs(float(w_new[etf_idx] - w_before[etf_idx]))
    return w_new, True, dw


def simulate_soft_core_nav(
    *,
    weights_by_book: dict[str, pd.DataFrame],
    px: pd.DataFrame,
    signal: pd.DataFrame,
    policy: str,
    fill_timing: str = "t0",
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Path3-carve Soft-core NAV under KEEP or LEDGER_SOFT_RATIO (flip-only recon).

    ``fill_timing``:
    - ``t0``: recon on flip day **before** same-day return (live T+0 same-bar / MOC).
    - ``eod_t1``: earn with old weights, then EOD recon (effective next-day for new mix).
    """
    timing = str(fill_timing or "t0").lower()
    if timing not in {"t0", "eod_t1"}:
        raise ValueError(f"fill_timing must be t0|eod_t1, got {fill_timing!r}")

    sig = signal.copy()
    sig["date"] = pd.to_datetime(sig["date"]).dt.normalize()
    sig = sig.sort_values("date").reset_index(drop=True)

    # Align to intersection of signal, px, both books
    dates = sig["date"]
    for wdf in weights_by_book.values():
        dates = dates[dates.isin(wdf.index)]
    dates = dates[dates.isin(px.index)].reset_index(drop=True)
    if len(dates) < 100:
        raise RuntimeError("insufficient overlap for Soft-core NAV sim")

    rets = px.pct_change().reindex(dates).fillna(0.0)
    etf_idx = SOFT_CORE.index(ETF)
    fin_tel_idx = [SOFT_CORE.index(c) for c in list(FIN) + list(TEL)]

    # Start on first date with book from signal
    row0 = sig[sig["date"] == dates.iloc[0]].iloc[0]
    book0 = str(row0.get("book") or BOOK_COMP)
    if book0 not in weights_by_book:
        book0 = BOOK_COMP
    w = weights_by_book[book0].loc[dates.iloc[0], SOFT_CORE].to_numpy(dtype=float)
    if w.sum() <= 1e-12:
        w = np.ones(len(SOFT_CORE)) / len(SOFT_CORE)
    else:
        w = w / w.sum()

    nav = [1.0]
    n_flip = 0
    n_etf_move = 0
    etf_turnover = 0.0  # sum |Δw_etf| on flips

    sig_by_date = sig.set_index("date")
    for i in range(1, len(dates)):
        d = dates.iloc[i]
        r = rets.loc[d, SOFT_CORE].to_numpy(dtype=float)

        if timing == "t0":
            # Same-bar Path3: recon first, then earn today's close-to-close on new mix.
            w, flipped, dw = _maybe_flip_recon(
                d=d,
                w=w,
                policy=policy,
                sig_by_date=sig_by_date,
                weights_by_book=weights_by_book,
                etf_idx=etf_idx,
                fin_tel_idx=fin_tel_idx,
            )
            if flipped:
                n_flip += 1
                etf_turnover += dw
                if dw > 1e-6:
                    n_etf_move += 1
            port_r = float(np.dot(w, r))
            nav.append(nav[-1] * (1.0 + port_r))
            w = w * (1.0 + r)
            s = float(w.sum())
            w = w / s if s > 1e-12 else w
        else:
            # EOD / effective T+1: earn on old mix, recon after close.
            port_r = float(np.dot(w, r))
            nav.append(nav[-1] * (1.0 + port_r))
            w = w * (1.0 + r)
            s = float(w.sum())
            w = w / s if s > 1e-12 else w
            w, flipped, dw = _maybe_flip_recon(
                d=d,
                w=w,
                policy=policy,
                sig_by_date=sig_by_date,
                weights_by_book=weights_by_book,
                etf_idx=etf_idx,
                fin_tel_idx=fin_tel_idx,
            )
            if flipped:
                n_flip += 1
                etf_turnover += dw
                if dw > 1e-6:
                    n_etf_move += 1

    out = pd.DataFrame({"date": dates.to_numpy(), "nav": np.asarray(nav, dtype=float)})
    meta = {
        "policy": policy,
        "fill_timing": timing,
        "n_days": int(len(out)),
        "n_flips_applied": int(n_flip),
        "n_flips_etf_weight_moved": int(n_etf_move),
        "sum_abs_etf_weight_delta_on_flips": round(float(etf_turnover), 6),
        "start": str(pd.Timestamp(out["date"].iloc[0]).date()),
        "end": str(pd.Timestamp(out["date"].iloc[-1]).date()),
    }
    return out, meta


def simulate_full_daily(
    weights_by_book: dict[str, pd.DataFrame],
    px: pd.DataFrame,
    signal: pd.DataFrame,
    *,
    fill_timing: str = "t0",
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Every day Soft-core weights = active Path3 book (context upper bound)."""
    timing = str(fill_timing or "t0").lower()
    sig = signal.copy()
    sig["date"] = pd.to_datetime(sig["date"]).dt.normalize()
    dates = sig["date"]
    for wdf in weights_by_book.values():
        dates = dates[dates.isin(wdf.index)]
    dates = dates[dates.isin(px.index)].reset_index(drop=True)
    rets = px.pct_change().reindex(dates).fillna(0.0)
    sig_i = sig.set_index("date")
    nav = [1.0]
    w = None
    for i, d in enumerate(dates):
        book = str(sig_i.loc[d, "book"]) if d in sig_i.index else BOOK_COMP
        if isinstance(book, pd.Series):
            book = str(book.iloc[-1])
        if book not in weights_by_book:
            book = BOOK_COMP
        w_new = weights_by_book[book].loc[d, SOFT_CORE].to_numpy(dtype=float)
        if w_new.sum() > 1e-12:
            w_new = w_new / w_new.sum()
        else:
            w_new = np.ones(len(SOFT_CORE)) / len(SOFT_CORE)
        if i == 0:
            w = w_new
            continue
        r = rets.loc[d, SOFT_CORE].to_numpy(dtype=float)
        if timing == "t0":
            w = w_new
            port_r = float(np.dot(w, r))
            nav.append(nav[-1] * (1.0 + port_r))
            w = w * (1.0 + r)
            s = float(w.sum())
            w = w / s if s > 1e-12 else w
        else:
            port_r = float(np.dot(w, r))
            nav.append(nav[-1] * (1.0 + port_r))
            w = w_new
    out = pd.DataFrame({"date": dates.to_numpy(), "nav": np.asarray(nav, dtype=float)})
    return out, {"policy": "FULL_DAILY", "fill_timing": timing, "n_days": int(len(out))}


def yearly_compare(nav_keep: pd.DataFrame, nav_chal: pd.DataFrame) -> list[dict[str, Any]]:
    """Calendar-year total return / MDD for KEEP vs chal."""

    def _yr(nav: pd.DataFrame) -> dict[int, dict[str, float]]:
        x = nav.copy()
        x["date"] = pd.to_datetime(x["date"])
        x["year"] = x["date"].dt.year
        out: dict[int, dict[str, float]] = {}
        for y, g in x.groupby("year"):
            g = g.reset_index(drop=True)
            if len(g) < 2:
                continue
            n0 = float(g["nav"].iloc[0])
            bn = g["nav"].astype(float) / n0
            out[int(y)] = {
                "n_days": float(len(g)),
                "ret": float(bn.iloc[-1] - 1.0),
                "mdd": float((bn / bn.cummax() - 1.0).min()),
            }
        return out

    a, b = _yr(nav_keep), _yr(nav_chal)
    years = sorted(set(a) | set(b))
    rows = []
    for y in years:
        ka, kb = a.get(y), b.get(y)
        if not ka or not kb:
            continue
        rows.append(
            {
                "year": y,
                "n_days": int(ka["n_days"]),
                "ret_keep_pct": round(ka["ret"] * 100, 4),
                "mdd_keep_pct": round(ka["mdd"] * 100, 4),
                "ret_chal_pct": round(kb["ret"] * 100, 4),
                "mdd_chal_pct": round(kb["mdd"] * 100, 4),
                "ret_lift_pp": round((kb["ret"] - ka["ret"]) * 100, 4),
                "mdd_improve_pp": round((kb["mdd"] - ka["mdd"]) * 100, 4),
                "ret_win": bool(kb["ret"] > ka["ret"]),
                "mdd_win": bool(kb["mdd"] > ka["mdd"]),
            }
        )
    return rows

def _delta_windows(base_w: dict, chal_w: dict) -> dict[str, Any]:
    keys = ("full", "heldout_2019_plus", "sealed_2023_plus")
    out = {}
    for k in keys:
        b, c = base_w.get(k) or {}, chal_w.get(k) or {}
        out[k] = {
            "cagr_lift_pp": None
            if cagr_lift_pp(b.get("cagr"), c.get("cagr")) is None
            else round(float(cagr_lift_pp(b.get("cagr"), c.get("cagr"))), 4),
            "mdd_improve_pp": None
            if b.get("max_drawdown") is None or c.get("max_drawdown") is None
            else round(float(mdd_delta_pp(b["max_drawdown"], c["max_drawdown"])), 4),
            "base_cagr": b.get("cagr"),
            "chal_cagr": c.get("cagr"),
            "base_mdd": b.get("max_drawdown"),
            "chal_mdd": c.get("max_drawdown"),
        }
    return out


def _verdict(delta: dict[str, Any], tip: dict[str, Any]) -> str:
    held = delta["heldout_2019_plus"]
    sealed = delta["sealed_2023_plus"]
    full = delta["full"]
    tip_y = (tip.get("ytd") or {}).get("cagr_lift_pp")
    if held.get("cagr_lift_pp") is None or sealed.get("mdd_improve_pp") is None:
        return "INCOMPLETE"
    held_ok = float(held["cagr_lift_pp"]) > 0
    sealed_ok = float(sealed["mdd_improve_pp"]) >= SEALED_MDD_FLOOR_PP
    tip_ok = tip_y is None or float(tip_y) >= TIP_Y_FLOOR_PP
    if held_ok and sealed_ok and tip_ok and float(full.get("cagr_lift_pp") or 0) > 0:
        return "ETF_NAV_DUAL_HIT"
    if held_ok and sealed_ok and tip_ok:
        return "ETF_NAV_DUAL_HELD_HIT"
    if (not held_ok) and sealed_ok and tip_ok and float(held["cagr_lift_pp"]) > -0.5:
        return "ETF_NAV_DUAL_SOFT"
    if float(sealed["mdd_improve_pp"]) < SEALED_MDD_FLOOR_PP:
        return "ETF_NAV_DUAL_MDD_BLOCK"
    if tip_y is not None and float(tip_y) < TIP_Y_FLOOR_PP:
        return "ETF_NAV_DUAL_TIP_BLOCK"
    return "ETF_NAV_DUAL_NO_EDGE"


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()

    comp = load_book_shares(BOOK_COMP)
    sat = load_book_shares(BOOK_SAT)
    px = _close_panel(SOFT_CORE)
    w_comp = _book_soft_weights(comp, px)
    w_sat = _book_soft_weights(sat, px)
    weights = {BOOK_COMP: w_comp, BOOK_SAT: w_sat}
    sig = load_or_build_signal()

    FILL_TIMING = "t0"  # live Path3 same-bar; set eod_t1 for prior EOD probe

    nav_keep, meta_keep = simulate_soft_core_nav(
        weights_by_book=weights,
        px=px,
        signal=sig,
        policy="KEEP",
        fill_timing=FILL_TIMING,
    )
    nav_ratio, meta_ratio = simulate_soft_core_nav(
        weights_by_book=weights,
        px=px,
        signal=sig,
        policy="LEDGER_SOFT_RATIO",
        fill_timing=FILL_TIMING,
    )
    nav_full, meta_full = simulate_full_daily(
        weights, px, sig, fill_timing=FILL_TIMING
    )

    # Side probe: prior EOD/T+1 timing for sensitivity
    nav_keep_eod, meta_keep_eod = simulate_soft_core_nav(
        weights_by_book=weights,
        px=px,
        signal=sig,
        policy="KEEP",
        fill_timing="eod_t1",
    )
    nav_ratio_eod, meta_ratio_eod = simulate_soft_core_nav(
        weights_by_book=weights,
        px=px,
        signal=sig,
        policy="LEDGER_SOFT_RATIO",
        fill_timing="eod_t1",
    )

    nav_keep.to_csv(OUT / "nav_KEEP_0050.csv", index=False)
    nav_ratio.to_csv(OUT / "nav_LEDGER_SOFT_RATIO.csv", index=False)
    nav_full.to_csv(OUT / "nav_FULL_DAILY.csv", index=False)
    nav_keep_eod.to_csv(OUT / "nav_KEEP_0050_eod_t1.csv", index=False)
    nav_ratio_eod.to_csv(OUT / "nav_LEDGER_SOFT_RATIO_eod_t1.csv", index=False)

    win_keep = _pack(nav_keep)
    win_ratio = _pack(nav_ratio)
    win_full = _pack(nav_full)
    delta = _delta_windows(win_keep, win_ratio)
    tip = _tip(nav_keep, nav_ratio)
    delta_full_ctx = _delta_windows(win_keep, win_full)
    verdict = _verdict(delta, tip)

    win_keep_eod = _pack(nav_keep_eod)
    win_ratio_eod = _pack(nav_ratio_eod)
    delta_eod = _delta_windows(win_keep_eod, win_ratio_eod)
    tip_eod = _tip(nav_keep_eod, nav_ratio_eod)
    yearly = yearly_compare(nav_keep, nav_ratio)
    yearly_df = pd.DataFrame(yearly)
    yearly_df.to_csv(OUT / "yearly_KEEP_vs_RATIO_t0.csv", index=False)
    yearly_df.to_csv(OUT / "yearly_KEEP_vs_RATIO.csv", index=False)  # primary alias (t0)

    # Context vs published Path3 blend / CTRL if available
    context = {}
    if CTRL_NAV.exists() and P3_NAV.exists():
        ctrl = pd.read_csv(CTRL_NAV, parse_dates=["date"])
        p3 = pd.read_csv(P3_NAV, parse_dates=["date"])
        context = {
            "ctrl_windows": _pack(ctrl),
            "p3_blend_windows": _pack(p3),
            "note": "CTRL/P3_T0_STATE are full-book NAVs (incl DEF/overlays); Soft-core dual is carve-only",
        }

    ret_wl = (
        int(sum(1 for r in yearly if r["ret_win"])),
        int(sum(1 for r in yearly if not r["ret_win"])),
    )
    mdd_wl = (
        int(sum(1 for r in yearly if r["mdd_win"])),
        int(sum(1 for r in yearly if not r["mdd_win"])),
    )

    screen = {
        "generated_at_utc": generated,
        "register": REGISTER,
        "parent": "0kae",
        "verdict": verdict,
        "fill_timing_primary": FILL_TIMING,
        "method": {
            "universe": SOFT_CORE,
            "fill_timing": FILL_TIMING,
            "fill_timing_note": (
                "t0: flip recon before same-day return (live T0_CARVE same-bar/MOC); "
                "eod_t1 sensitivity retained in delta_eod_t1_ratio_minus_keep"
            ),
            "between_flips": "hold Soft-core weights",
            "KEEP": "flip: FIN∪TEL → dest Soft-core mix; sticky 0050 weight",
            "LEDGER_SOFT_RATIO": "flip: full Soft-core → dest book",
            "FULL_DAILY": "context: daily Soft-core = active book",
        },
        "meta_keep": meta_keep,
        "meta_ratio": meta_ratio,
        "meta_full_daily": meta_full,
        "meta_keep_eod_t1": meta_keep_eod,
        "meta_ratio_eod_t1": meta_ratio_eod,
        "windows_keep": win_keep,
        "windows_ratio": win_ratio,
        "windows_full_daily": win_full,
        "delta_ratio_minus_keep": delta,
        "delta_full_minus_keep": delta_full_ctx,
        "tip_ratio_minus_keep": tip,
        "delta_eod_t1_ratio_minus_keep": delta_eod,
        "tip_eod_t1_ratio_minus_keep": tip_eod,
        "yearly_ratio_minus_keep": yearly,
        "yearly_ret_wl": {"w": ret_wl[0], "l": ret_wl[1]},
        "yearly_mdd_improve_wl": {"w": mdd_wl[0], "l": mdd_wl[1]},
        "gates": {
            "sealed_mdd_floor_pp": SEALED_MDD_FLOOR_PP,
            "tip_y_floor_pp": TIP_Y_FLOOR_PP,
        },
        "context": context,
    }
    (OUT / "screen.json").write_text(json.dumps(screen, indent=2) + "\n", encoding="utf-8")

    charter = "\n".join(
        [
            f"# {CHARTER_ID}",
            "",
            f"Date: {generated[:10]}",
            "Status: **Stage B — Path3 0050 ETF recon paper NAV dual** · Soft **KEEP** · "
            "broker **false** · cutover **BLOCKED** · no live",
            "Parent: 0kae `ETF_POLICY_LEDGER_RATIO_HIT`",
            f"Register: **{REGISTER}**",
            "",
            "## Question",
            "",
            "Does flip-day `LEDGER_SOFT_RATIO` (move Soft 0050 toward dest book Soft-core weight) "
            "**improve** Path3 Soft-core tip/held/sealed vs status-quo sticky-0050 `KEEP`?",
            "",
            "## Method",
            "",
            "- Soft-core = FIN∪TEL∪0050 from COMP/SAT daily share ledgers × close",
            "- Path3 flips from `p3_t0_state` signal",
            "- **Fill timing `t0` (primary):** flip recon **before** same-day return "
            "(aligns live `T0_CARVE_FIN_SAT_SWITCH` same-bar / MOC)",
            "- Sensitivity: also report `eod_t1` (earn old mix, then EOD recon)",
            "- Between flips: **hold** Soft-core weights (carve-only paper)",
            "- Arms: `KEEP` vs `LEDGER_SOFT_RATIO` (+ `FULL_DAILY` context)",
            "- Metrics: WINDOWS_STANDARD + tip YTD/1y + yearly W–L · lift = chal − KEEP",
            "",
            "## Gates",
            "",
            f"- held CAGR lift > 0",
            f"- sealed MDD improve ≥ {SEALED_MDD_FLOOR_PP} pp",
            f"- tip YTD CAGR lift ≥ {TIP_Y_FLOOR_PP} pp (or null)",
            "",
            "## Non-goals",
            "",
            "- Live wire · mute expand · Soft Exact T+1 between flips · satellite · broker",
            "",
            f"Label: `{CHARTER_ID}_{generated[:10]}__NAV_DUAL__NO_LIVE`",
            "",
        ]
    )
    write_ops_and_repro_pointer(OPS / f"{CHARTER_ID}.md", REP / f"{CHARTER_ID}.md", charter, kind="charter")
    (OPS / f"{CHARTER_ID}.json").write_text(
        json.dumps(
            {
                "id": CHARTER_ID,
                "register": REGISTER,
                "parent": "0kae",
                "fill_timing_primary": "t0",
                "base": "KEEP",
                "chal": "LEDGER_SOFT_RATIO",
                "soft_keep": True,
                "broker": False,
                "cutover_blocked": True,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    write_repro_pointer(OPS / f"{CHARTER_ID}.json", REP / f"{CHARTER_ID}.json", kind="charter")

    def _row(name: str, d: dict) -> str:
        return (
            f"| {name} | {d.get('cagr_lift_pp')} | {d.get('mdd_improve_pp')} | "
            f"{d.get('base_cagr')} → {d.get('chal_cagr')} |"
        )

    screen_md = "\n".join(
        [
            f"# {SCREEN_ID}",
            "",
            f"Date: {generated[:10]} · Verdict: **`{verdict}`** · fill=**`{FILL_TIMING}`**",
            f"Register: **{REGISTER}** · parent 0kae · end=`{meta_keep['end']}` · "
            f"flips KEEP/RATIO={meta_keep['n_flips_applied']}/{meta_ratio['n_flips_applied']} · "
            f"etf_moves RATIO={meta_ratio['n_flips_etf_weight_moved']}",
            "",
            "## Improvement (T+0): `LEDGER_SOFT_RATIO` − `KEEP` (pp)",
            "",
            "| Window | CAGR lift pp | MDD improve pp | KEEP → RATIO CAGR |",
            "|---|---:|---:|---|",
            _row("full", delta["full"]),
            _row("heldout_2019_plus", delta["heldout_2019_plus"]),
            _row("sealed_2023_plus", delta["sealed_2023_plus"]),
            "",
            "## Tip (T+0)",
            "",
            f"- YTD CAGR lift pp: **{(tip.get('ytd') or {}).get('cagr_lift_pp')}** · "
            f"MDD improve pp: {(tip.get('ytd') or {}).get('mdd_improve_pp')}",
            f"- Trailing 1y CAGR lift pp: **{(tip.get('trailing_1y') or {}).get('cagr_lift_pp')}** · "
            f"MDD improve pp: {(tip.get('trailing_1y') or {}).get('mdd_improve_pp')}",
            "",
            "## Sensitivity EOD/T+1 (prior timing)",
            "",
            f"- full CAGR lift pp: {(delta_eod.get('full') or {}).get('cagr_lift_pp')} · "
            f"held: {(delta_eod.get('heldout_2019_plus') or {}).get('cagr_lift_pp')} · "
            f"sealed MDD improve: {(delta_eod.get('sealed_2023_plus') or {}).get('mdd_improve_pp')}",
            f"- tipY / tip1y: {(tip_eod.get('ytd') or {}).get('cagr_lift_pp')} / "
            f"{(tip_eod.get('trailing_1y') or {}).get('cagr_lift_pp')}",
            "",
            "## Yearly (T+0) ret W–L / MDD improve W–L",
            "",
            f"- Ret **{ret_wl[0]}–{ret_wl[1]}** · MDD improve **{mdd_wl[0]}–{mdd_wl[1]}**",
            "",
            "| Year | KEEP ret% | RATIO ret% | Ret lift pp | MDD improve pp |",
            "|---:|---:|---:|---:|---:|",
            *[
                f"| {r['year']} | {r['ret_keep_pct']:.2f} | {r['ret_chal_pct']:.2f} | "
                f"{r['ret_lift_pp']:+.2f} | {r['mdd_improve_pp']:+.2f} |"
                for r in yearly
            ],
            "",
            "## ETF turnover on flips",
            "",
            f"- KEEP sum |Δw_0050|: {meta_keep['sum_abs_etf_weight_delta_on_flips']}",
            f"- RATIO sum |Δw_0050|: {meta_ratio['sum_abs_etf_weight_delta_on_flips']}",
            "",
            "## Context FULL_DAILY − KEEP (T+0)",
            "",
            _row("full", delta_full_ctx["full"]),
            _row("held", delta_full_ctx["heldout_2019_plus"]),
            "",
            f"Repro: `PYTHONPATH=scripts python3 scripts/fin_sat_path3_etf_recon_nav_dual_stageb.py`",
            "",
            f"Label: `{SCREEN_ID}_{generated[:10]}__{verdict}__T0`",
            "",
        ]
    )
    write_ops_and_repro_pointer(OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", screen_md, kind="screen")
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(screen, indent=2) + "\n", encoding="utf-8")
    write_repro_pointer(OPS / f"{SCREEN_ID}.json", REP / f"{SCREEN_ID}.json", kind="screen")

    next_steps = []
    if verdict in {"ETF_NAV_DUAL_HIT", "ETF_NAV_DUAL_HELD_HIT"}:
        next_steps.append(
            "Optional Stage C: add Soft Exact T+1 between flips / e21 coexistence smoke — still no live"
        )
        next_steps.append("Human ballot only after coexistence pack; default still KEEP until ACCEPT")
    elif verdict == "ETF_NAV_DUAL_SOFT":
        next_steps.append("Borderline — require tip/held disposition before any ballot")
    else:
        next_steps.append("Keep live Path3 `keep_0050=True` — no ETF recon promote")
    next_steps.append("0kac PAPER_WITHIN_HIT remains primary Path3 roadmap")

    decision = {
        "label": f"{DECISION_ID}_{generated[:10]}__{verdict}__T0__NO_LIVE",
        "verdict": verdict,
        "register": REGISTER,
        "parent": "0kae",
        "fill_timing_primary": FILL_TIMING,
        "base": "KEEP",
        "chal": "LEDGER_SOFT_RATIO",
        "delta_ratio_minus_keep": delta,
        "tip_ratio_minus_keep": tip,
        "delta_eod_t1_ratio_minus_keep": delta_eod,
        "tip_eod_t1_ratio_minus_keep": tip_eod,
        "yearly_ret_wl": {"w": ret_wl[0], "l": ret_wl[1]},
        "meta_ratio": meta_ratio,
        "soft_keep": True,
        "broker": False,
        "cutover_blocked": True,
        "live_wire": False,
        "next": next_steps,
    }
    decision_md = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: {generated[:10]} · Verdict: **`{verdict}`** · fill=**`{FILL_TIMING}`**",
            f"Register: **{REGISTER}** · Parent: **0kae**",
            "",
            "## Improvement T+0 (`LEDGER_SOFT_RATIO` − `KEEP`)",
            "",
            f"- full CAGR lift: **{delta['full']['cagr_lift_pp']}** pp · "
            f"MDD improve: {delta['full']['mdd_improve_pp']} pp",
            f"- held CAGR lift: **{delta['heldout_2019_plus']['cagr_lift_pp']}** pp · "
            f"MDD improve: {delta['heldout_2019_plus']['mdd_improve_pp']} pp",
            f"- sealed CAGR lift: **{delta['sealed_2023_plus']['cagr_lift_pp']}** pp · "
            f"MDD improve: {delta['sealed_2023_plus']['mdd_improve_pp']} pp",
            f"- tip YTD CAGR lift: **{(tip.get('ytd') or {}).get('cagr_lift_pp')}** pp",
            f"- tip 1y CAGR lift: **{(tip.get('trailing_1y') or {}).get('cagr_lift_pp')}** pp",
            f"- yearly ret W–L: **{ret_wl[0]}–{ret_wl[1]}**",
            "",
            "## Sensitivity EOD/T+1",
            "",
            f"- full / held CAGR lift: {(delta_eod.get('full') or {}).get('cagr_lift_pp')} / "
            f"{(delta_eod.get('heldout_2019_plus') or {}).get('cagr_lift_pp')} pp",
            f"- tip YTD / 1y: {(tip_eod.get('ytd') or {}).get('cagr_lift_pp')} / "
            f"{(tip_eod.get('trailing_1y') or {}).get('cagr_lift_pp')} pp",
            "",
            "## Disposition",
            "",
            "- Paper Soft-core carve-only dual under **T+0** fill (flip recon before same-day return).",
            "- Live Path3 remains `keep_0050=True` unless human ACCEPT after stronger pack.",
            "",
            "## Next",
            "",
            *[f"{i+1}. {s}" for i, s in enumerate(next_steps)],
            "",
            f"Label: `{decision['label']}`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{DECISION_ID}.md", REP / f"{DECISION_ID}.md", decision_md, kind="decision pack"
    )
    (OPS / f"{DECISION_ID}.json").write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    write_repro_pointer(OPS / f"{DECISION_ID}.json", REP / f"{DECISION_ID}.json", kind="decision pack")

    print(
        json.dumps(
            {
                "verdict": verdict,
                "fill_timing": FILL_TIMING,
                "full_cagr_lift_pp": delta["full"]["cagr_lift_pp"],
                "held_cagr_lift_pp": delta["heldout_2019_plus"]["cagr_lift_pp"],
                "sealed_mdd_improve_pp": delta["sealed_2023_plus"]["mdd_improve_pp"],
                "tip_ytd_cagr_lift_pp": (tip.get("ytd") or {}).get("cagr_lift_pp"),
                "tip_1y_cagr_lift_pp": (tip.get("trailing_1y") or {}).get("cagr_lift_pp"),
                "yearly_ret_wl": f"{ret_wl[0]}-{ret_wl[1]}",
                "eod_t1_held_cagr_lift_pp": (delta_eod.get("heldout_2019_plus") or {}).get(
                    "cagr_lift_pp"
                ),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
