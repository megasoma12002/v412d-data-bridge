#!/usr/bin/env python3
"""Stage A: Path3 OFF-day FIN∪TEL ownership fill lock (ACCEPT precondition).

Question (human): before ACCEPT apply / intermittent Path3, which OFF-day fill
unlocks tip Soft tipY under Soft FIN/TEL Exact T+1 stay OFF?

Two clocks (explicit):
1. Tip Soft Exact T+1 attribution — Soft-refill ceiling = MUTE_S3_SAT vs L4
   (FORBIDDEN under Path3 WITHIN KEEP; tipY target).
2. Soft-core T+0 carve sim — WITHIN_DAILY ON + mute OFF fills:
   FREEZE / FT→0050 / FT→CASH (feasible under Soft FIN/TEL OFF).

Gate: frozen 0kb1 MUTE_S3_SAT (W63, thr −0.01) · Path4 OFF in Soft-core arms.
Soft KEEP · Path4 live OFF · broker false · no year-cut · no live wire.
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
from ops_repro_ssot import write_ops_and_repro_pointer
from path3_comp_sat_daily_share_ssot import load_book_shares
from research_metric_helpers import mdd_delta_pp

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "tipsoft-ip3-fill-lock-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"
MARKET = ROOT / "forward/e21/live_market.csv"
ALIGN = ROOT / "repro" / "research-live-align-gap-stagea" / "outputs"
LIVESTACK = ROOT / "repro" / "fin-sat-path3-path4-livestack-twin-stageb" / "outputs"
STACK = ROOT / "repro" / "tipsoft-ip3-live-stack-race-stagea" / "outputs"
P3_SIG = ROOT / "repro" / "fin-sat-path3-t0-dual-paper-observe" / "outputs" / "p3_t0_state_signal.csv"

CHARTER_ID = "TIPSOFT_IP3_FILL_LOCK_STAGEA_CHARTER"
SCREEN_ID = "TIPSOFT_IP3_FILL_LOCK_STAGEA_SCREEN"
DECISION_ID = "TIPSOFT_IP3_FILL_LOCK_STAGEA_DECISION_PACK"
REGISTER = "0kb7"
PARENTS = ("0kb6", "0kb2", "0kb1", "0kac")
MECH = "TIPSOFT_IP3_FILL_LOCK"

ETF = "0050"
SOFT_CORE = list(FIN) + list(TEL) + [ETF]
P3_THETA = 0.005
MUTE_W = 63
MUTE_THR = -0.01
SEALED_MDD_FLOOR_PP = -0.25
TIP_Y_FLOOR_PP = -1.0
HELD_EDGE_PP = 0.05


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_nav(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"])
    return (
        df[["date", "nav"]]
        .assign(
            date=lambda x: pd.to_datetime(x["date"]).dt.normalize(),
            nav=lambda x: x["nav"].astype(float),
        )
        .sort_values("date")
        .reset_index(drop=True)
    )


def _returns(nav: pd.DataFrame) -> pd.Series:
    s = nav.set_index("date")["nav"].astype(float).sort_index()
    return s.pct_change().fillna(0.0)


def _trail_sum(x: pd.Series, w: int) -> pd.Series:
    return x.shift(1).rolling(int(w), min_periods=max(3, int(w) // 3)).sum()


def _dd_from_peak(nav: pd.DataFrame, w: int) -> pd.Series:
    s = nav.set_index("date")["nav"].astype(float).sort_index()
    peak = s.cummax()
    dd = s / peak - 1.0
    return dd.rolling(int(w), min_periods=1).min()


def _three_state_mute_sat(
    nearpeak3: pd.Series,
    sat_lead: pd.Series,
    prem_p3: pd.Series,
    w: int = MUTE_W,
    thr: float = MUTE_THR,
) -> pd.Series:
    tr = _trail_sum(prem_p3, w).fillna(0.0)
    mute = ((tr < float(thr)) & sat_lead).to_numpy(dtype=bool)
    want_p3 = nearpeak3.to_numpy(dtype=bool)
    want_p4 = (nearpeak3 & sat_lead).to_numpy(dtype=bool)
    n = len(want_p3)
    i3 = np.zeros(n, dtype=float)
    state = 0
    for i in range(n):
        if mute[i] or not want_p3[i]:
            state = 0
        else:
            if state == 0:
                state = 1
            if state >= 1 and want_p4[i] and not mute[i]:
                state = 2
            elif state == 2 and (not want_p4[i] or mute[i]):
                state = 1
        i3[i] = 1.0 if state >= 1 else 0.0
    return pd.Series(i3, index=nearpeak3.index)


def _close_panel(codes: list[str]) -> pd.DataFrame:
    m = pd.read_csv(MARKET, dtype={"code": str}, parse_dates=["date"])
    m = m[m["code"].isin(codes)]
    return (
        m.pivot_table(index="date", columns="code", values="close", aggfunc="last")
        .sort_index()
        .astype(float)
        .reindex(columns=codes)
    )


def _book_soft_weights(panel: pd.DataFrame, px: pd.DataFrame) -> pd.DataFrame:
    dates = panel.index.intersection(px.index)
    w = pd.DataFrame(0.0, index=dates, columns=SOFT_CORE)
    for c in SOFT_CORE:
        if c not in panel.columns or c not in px.columns:
            continue
        dol = panel.loc[dates, c].astype(float) * px.loc[dates, c].astype(float)
        w[c] = dol.clip(lower=0.0)
    s = w.sum(axis=1).replace(0.0, np.nan)
    return w.div(s, axis=0).fillna(0.0)


def _apply_keep0050(
    w_prev: np.ndarray,
    w_dest: np.ndarray,
    etf_idx: int,
    fin_tel_idx: list[int],
) -> np.ndarray:
    etf_w = float(min(max(w_prev[etf_idx], 0.0), 1.0))
    out = np.zeros_like(w_prev, dtype=float)
    out[etf_idx] = etf_w
    ft = w_dest[fin_tel_idx].astype(float).copy()
    ft_sum = float(ft.sum())
    if ft_sum > 1e-12 and etf_w < 1.0 - 1e-12:
        out[fin_tel_idx] = ft / ft_sum * (1.0 - etf_w)
    elif etf_w >= 1.0 - 1e-12:
        out[etf_idx] = 1.0
    else:
        prev_ft = w_prev[fin_tel_idx]
        psum = float(prev_ft.sum())
        if psum > 1e-12:
            out[fin_tel_idx] = prev_ft / psum * (1.0 - etf_w)
        else:
            out[etf_idx] = 1.0
    s = float(out.sum())
    return out / s if s > 1e-12 else w_prev.copy()


def _fill_ft_to_0050(w: np.ndarray, etf_idx: int, fin_tel_idx: list[int]) -> np.ndarray:
    out = w.copy()
    ft = float(out[fin_tel_idx].sum())
    out[fin_tel_idx] = 0.0
    out[etf_idx] = float(out[etf_idx]) + ft
    s = float(out.sum())
    return out / s if s > 1e-12 else out


def _fill_ft_to_cash(w: np.ndarray, fin_tel_idx: list[int]) -> np.ndarray:
    """Zero FIN∪TEL; leave residual invested (0050) + implicit cash (1−sum)."""
    out = w.copy()
    out[fin_tel_idx] = 0.0
    # do not renormalize — cash earns 0
    return out


def simulate_fill(
    *,
    fill: str,
    weights_by_book: dict[str, pd.DataFrame],
    px: pd.DataFrame,
    signal: pd.DataFrame,
    i3_on: pd.Series,
    share_events: dict | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Soft-core T+0: Path3 ON→WITHIN recon; OFF→fill policy."""
    sig = signal.copy()
    sig["date"] = pd.to_datetime(sig["date"]).dt.normalize()
    sig = sig.sort_values("date").reset_index(drop=True)
    dates = sig["date"]
    for wdf in weights_by_book.values():
        dates = dates[dates.isin(wdf.index)]
    dates = dates[dates.isin(px.index)].reset_index(drop=True)
    if len(dates) < 100:
        raise RuntimeError("insufficient overlap")

    rets = px.pct_change().reindex(dates).fillna(0.0)
    for date, events in (share_events or {}).items():
        day = pd.Timestamp(date)
        if day in rets.index:
            for code, factor in events.items():
                if code in rets:
                    rets.loc[day, code] = (1.0 + rets.loc[day, code]) * float(factor) - 1.0
    etf_idx = SOFT_CORE.index(ETF)
    fin_tel_idx = [SOFT_CORE.index(c) for c in list(FIN) + list(TEL)]
    sig_i = sig.set_index("date")
    i3 = i3_on.reindex(pd.to_datetime(dates)).fillna(0.0)

    row0 = sig[sig["date"] == dates.iloc[0]].iloc[0]
    book0 = str(row0.get("book") or BOOK_COMP)
    if book0 not in weights_by_book:
        book0 = BOOK_COMP
    w = weights_by_book[book0].loc[dates.iloc[0], SOFT_CORE].to_numpy(dtype=float)
    w = w / w.sum() if w.sum() > 1e-12 else np.ones(len(SOFT_CORE)) / len(SOFT_CORE)

    nav = [1.0]
    n_recon = 0
    n_off = 0
    n_fill = 0

    for i in range(1, len(dates)):
        d = dates.iloc[i]
        r = rets.loc[d, SOFT_CORE].to_numpy(dtype=float)
        srow = sig_i.loc[d] if d in sig_i.index else None
        if isinstance(srow, pd.DataFrame):
            srow = srow.iloc[-1]
        book = str(srow.get("book") or BOOK_COMP) if srow is not None else BOOK_COMP
        if book not in weights_by_book:
            book = BOOK_COMP

        on = bool(float(i3.loc[d]) >= 0.5) if d in i3.index else True
        if fill == "ALWAYS_WITHIN":
            on = True

        if on:
            if d in weights_by_book[book].index:
                w_dest = weights_by_book[book].loc[d, SOFT_CORE].to_numpy(dtype=float)
                if w_dest.sum() > 1e-12:
                    w_dest = w_dest / w_dest.sum()
                    w = _apply_keep0050(w, w_dest, etf_idx, fin_tel_idx)
                    n_recon += 1
        else:
            n_off += 1
            if fill == "FREEZE":
                pass
            elif fill == "FT_TO_0050":
                w = _fill_ft_to_0050(w, etf_idx, fin_tel_idx)
                n_fill += 1
            elif fill == "FT_TO_CASH":
                w = _fill_ft_to_cash(w, fin_tel_idx)
                n_fill += 1
            elif fill == "SOFT_REFILL_DIAG":
                # Diagnostic: equal FIN∪TEL among Soft-core FT, sticky 0050
                # (not Soft Exact T+1 KD — labeled diagnostic only)
                etf_w = float(min(max(w[etf_idx], 0.0), 1.0))
                out = np.zeros_like(w)
                out[etf_idx] = etf_w
                n_ft = len(fin_tel_idx)
                if etf_w < 1.0 - 1e-12 and n_ft:
                    out[fin_tel_idx] = (1.0 - etf_w) / n_ft
                else:
                    out[etf_idx] = 1.0
                w = out
                n_fill += 1
            else:
                raise ValueError(fill)

        invested = float(np.clip(w.sum(), 0.0, 1.0))
        if invested > 1e-12:
            w_n = w / invested
            port_r = float(np.dot(w_n, r)) * invested  # cash sleeve earns 0
        else:
            port_r = 0.0
        nav.append(nav[-1] * (1.0 + port_r))
        w = w * (1.0 + r)
        # cash residual stays out of w; renormalize only invested mass drift
        inv = float(np.clip(w.sum(), 0.0, None))
        if inv > 1e-12 and fill == "FT_TO_CASH" and invested < 1.0 - 1e-12:
            # preserve cash fraction after drift of invested names
            cash_frac = max(0.0, 1.0 - invested)
            w = w / inv * (1.0 - cash_frac)
        elif inv > 1e-12:
            w = w / inv

    out = pd.DataFrame({"date": dates.to_numpy(), "nav": np.asarray(nav, dtype=float)})
    meta = {
        "fill": fill,
        "clock": "softcore_t0",
        "n_days": int(len(out)),
        "n_recon_days": int(n_recon),
        "n_off_days": int(n_off),
        "n_fill_actions": int(n_fill),
        "pct_off": round(100.0 * n_off / max(1, len(out) - 1), 4),
        "start": str(pd.Timestamp(out["date"].iloc[0]).date()),
        "end": str(pd.Timestamp(out["date"].iloc[-1]).date()),
    }
    return out, meta


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
            "cagr_lift_pp": None
            if cagr_lift_pp(bc, cc) is None
            else round(float(cagr_lift_pp(bc, cc)), 4),
            "mdd_improve_pp": round(float(mdd_delta_pp(b_mdd, c_mdd)), 4),
        }
    return out


def _delta(base_w: dict, chal_w: dict) -> dict[str, Any]:
    out = {}
    for k in ("full", "heldout_2019_plus", "sealed_2023_plus"):
        b, c = base_w.get(k) or {}, chal_w.get(k) or {}
        out[k] = {
            "cagr_lift_pp": None
            if cagr_lift_pp(b.get("cagr"), c.get("cagr")) is None
            else round(float(cagr_lift_pp(b.get("cagr"), c.get("cagr"))), 4),
            "mdd_improve_pp": None
            if b.get("max_drawdown") is None or c.get("max_drawdown") is None
            else round(float(mdd_delta_pp(b["max_drawdown"], c["max_drawdown"])), 4),
        }
    return out


def _row(
    name: str,
    role: str,
    clock: str,
    nav: pd.DataFrame,
    base_nav: pd.DataFrame,
    base_w: dict,
    *,
    feasible: bool,
    soft_fin_tel_required: bool,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    w = _pack(nav)
    d = _delta(base_w, w)
    tip = _tip(base_nav, nav)
    held = d["heldout_2019_plus"]
    sealed = d["sealed_2023_plus"]
    return {
        "arm": name,
        "role": role,
        "clock": clock,
        "feasible_under_soft_fin_tel_off": feasible,
        "soft_fin_tel_required": soft_fin_tel_required,
        "held_cagr_lift_pp": held["cagr_lift_pp"],
        "held_mdd_improve_pp": held["mdd_improve_pp"],
        "sealed_cagr_lift_pp": sealed["cagr_lift_pp"],
        "sealed_mdd_improve_pp": sealed["mdd_improve_pp"],
        "tipY_pp": (tip.get("ytd") or {}).get("cagr_lift_pp"),
        "tip1y_pp": (tip.get("trailing_1y") or {}).get("cagr_lift_pp"),
        "meta": meta or {},
    }


def _path3_panel() -> tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    """Returns live_r, prem_p3, nearpeak3, sat_lead on tip Soft panel index."""
    nav_l3 = _load_nav(LIVESTACK / "nav_BASE_LIVE_FUSE_COOL.csv")
    nav_p3 = _load_nav(LIVESTACK / "nav_LIVE_P3_WITHIN.csv")
    soft_l1 = _load_nav(ALIGN / "nav_L1_SOFT_T1.csv")
    r3 = _returns(nav_l3)
    rp3 = _returns(nav_p3)
    panel = pd.concat({"r3": r3, "rp3": rp3}, axis=1, join="inner").dropna(how="any")
    prem_p3 = panel["rp3"] - panel["r3"]
    dd63 = _dd_from_peak(soft_l1, 63).reindex(panel.index).fillna(0.0)
    sig = pd.read_csv(P3_SIG, parse_dates=["date"])
    sig["date"] = pd.to_datetime(sig["date"]).dt.normalize()
    sig = sig.set_index("date").reindex(panel.index)
    trail = sig["trail_rel_63"].astype(float)
    sat_lead = sig["sat_lead"].fillna(False).astype(bool)
    nearpeak3 = (trail.abs() >= float(P3_THETA)).fillna(False) & (dd63 >= -0.03)
    return panel["r3"], prem_p3, nearpeak3, sat_lead


def _mute_i3_series() -> tuple[pd.Series, dict[str, Any]]:
    _live_r, prem_p3, nearpeak3, sat_lead = _path3_panel()
    i3 = _three_state_mute_sat(nearpeak3, sat_lead, prem_p3)
    info = {
        "pct_path3_on": round(float(i3.mean()) * 100.0, 4),
        "pct_nearpeak3_on": round(float(nearpeak3.mean()) * 100.0, 4),
        "n_days": int(len(i3)),
        "gate": f"MUTE_S3_SAT_W{MUTE_W}_T{MUTE_THR}",
    }
    return i3, info


def _nearpeak3_series() -> pd.Series:
    _live_r, _prem, nearpeak3, _sat = _path3_panel()
    return nearpeak3.astype(float)


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()

    # --- Tip Soft Exact T+1 attribution panel ---
    l4 = _load_nav(ALIGN / "nav_L4_LIVE_P3_WITHIN.csv")
    mute_nav = _load_nav(STACK / "nav_REF_MUTE_S3_SAT_W63.csv")
    ov_nav = _load_nav(
        ROOT
        / "repro/tipsoft-ip3-live-override-paper-observe/outputs/nav_OVERRIDE_LIVE_W42_M05_K3.csv"
    )
    l4_w = _pack(l4)
    tip_rows = [
        _row(
            "TIP_L4_ALWAYS_WITHIN",
            "live tip twin / stamps baseline",
            "tipsoft_exact_t1",
            l4,
            l4,
            l4_w,
            feasible=True,
            soft_fin_tel_required=False,
        ),
        _row(
            "TIP_CEIL_SOFT_REFILL_MUTE",
            "MUTE_S3_SAT Soft refill on Path3 OFF (FORBIDDEN ceiling)",
            "tipsoft_exact_t1",
            mute_nav,
            l4,
            l4_w,
            feasible=False,
            soft_fin_tel_required=True,
        ),
        _row(
            "TIP_CEIL_OVERRIDE",
            "paper OVERRIDE blend ceiling",
            "tipsoft_exact_t1",
            ov_nav,
            l4,
            l4_w,
            feasible=False,
            soft_fin_tel_required=True,
        ),
    ]
    l4.to_csv(OUT / "nav_TIP_L4_ALWAYS_WITHIN.csv", index=False)
    mute_nav.to_csv(OUT / "nav_TIP_CEIL_SOFT_REFILL_MUTE.csv", index=False)
    ov_nav.to_csv(OUT / "nav_TIP_CEIL_OVERRIDE.csv", index=False)

    # --- Soft-core fill sim ---
    i3, gate_info = _mute_i3_series()
    px = _close_panel(SOFT_CORE)
    weights = {
        BOOK_COMP: _book_soft_weights(load_book_shares(BOOK_COMP), px),
        BOOK_SAT: _book_soft_weights(load_book_shares(BOOK_SAT), px),
    }
    sig = load_or_build_signal()

    fills = (
        ("ALWAYS_WITHIN", "status-quo Soft-core daily Path3 (WITHIN)", True, False),
        ("FREEZE", "Path3 OFF → freeze last FIN∪TEL weights", True, False),
        ("FT_TO_0050", "Path3 OFF → park FIN∪TEL mass into 0050", True, False),
        ("FT_TO_CASH", "Path3 OFF → park FIN∪TEL into cash (0 earn)", True, False),
        (
            "SOFT_REFILL_DIAG",
            "Path3 OFF → equal Soft-core FT + sticky 0050 (diag ≠ Exact T+1 KD)",
            False,
            True,
        ),
    )
    # Primary gate = MUTE_S3_SAT; sensitivity = raw NEARPEAK3 (similar ON%).
    gate_series = {
        "MUTE": i3,
        "NEAR": _nearpeak3_series(),
    }
    soft_navs: dict[str, pd.DataFrame] = {}
    soft_meta: dict[str, dict[str, Any]] = {}
    soft_rows = []
    for gname, gser in gate_series.items():
        for fill, role, feas, sreq in fills:
            arm = f"SC_{gname}_{fill}"
            nav, meta = simulate_fill(
                fill=fill,
                weights_by_book=weights,
                px=px,
                signal=sig,
                i3_on=gser,
            )
            meta = dict(meta)
            meta["gate_family"] = gname
            soft_navs[arm] = nav
            soft_meta[arm] = meta
            nav.to_csv(OUT / f"nav_{arm}.csv", index=False)

    base_sc = soft_navs["SC_MUTE_ALWAYS_WITHIN"]
    base_sc_w = _pack(base_sc)
    for gname in gate_series:
        for fill, role, feas, sreq in fills:
            arm = f"SC_{gname}_{fill}"
            soft_rows.append(
                _row(
                    arm,
                    f"[{gname}] {role}",
                    "softcore_t0",
                    soft_navs[arm],
                    base_sc,
                    base_sc_w,
                    feasible=feas and fill != "SOFT_REFILL_DIAG",
                    soft_fin_tel_required=sreq,
                    meta=soft_meta[arm],
                )
            )

    rows = tip_rows + soft_rows
    df = pd.DataFrame([{k: v for k, v in r.items() if k != "meta"} for r in rows])
    df.to_csv(OUT / "fill_lock_arms.csv", index=False)

    tip_ceil = next(r for r in tip_rows if r["arm"] == "TIP_CEIL_SOFT_REFILL_MUTE")
    tip_gap_held = float(tip_ceil["held_cagr_lift_pp"] or 0.0)
    tip_gap_tipy = float(tip_ceil["tipY_pp"] or 0.0)

    feas_soft = [
        r
        for r in soft_rows
        if (not r["arm"].endswith("_ALWAYS_WITHIN"))
        and r["feasible_under_soft_fin_tel_off"]
        and r["held_cagr_lift_pp"] is not None
    ]
    clears = []
    for r in feas_soft:
        held = float(r["held_cagr_lift_pp"])
        sealed_mdd = r["sealed_mdd_improve_pp"]
        tipy = r["tipY_pp"]
        sealed_ok = sealed_mdd is None or float(sealed_mdd) >= SEALED_MDD_FLOOR_PP
        tip_ok = tipy is None or float(tipy) >= TIP_Y_FLOOR_PP
        held_ok = held > HELD_EDGE_PP
        if held_ok and sealed_ok and tip_ok:
            clears.append(r)

    best = None
    if clears:
        best = max(clears, key=lambda x: float(x["held_cagr_lift_pp"]))
    elif feas_soft:
        # best non-blocked by sealed/tip among held+
        cand = [
            r
            for r in feas_soft
            if float(r["held_cagr_lift_pp"]) > 0
            and (
                r["sealed_mdd_improve_pp"] is None
                or float(r["sealed_mdd_improve_pp"]) >= SEALED_MDD_FLOOR_PP
            )
        ]
        if cand:
            best = max(cand, key=lambda x: float(x["held_cagr_lift_pp"]))

    freeze = next(r for r in soft_rows if r["arm"] == "SC_MUTE_FREEZE")
    to0050 = next(r for r in soft_rows if r["arm"] == "SC_MUTE_FT_TO_0050")
    tocash = next(r for r in soft_rows if r["arm"] == "SC_MUTE_FT_TO_CASH")

    if clears:
        verdict = "FILL_LOCK_HIT"
    elif best is not None and float(best["held_cagr_lift_pp"]) > 0:
        # soft clear without full tip floor
        tipy = best["tipY_pp"]
        if tipy is not None and float(tipy) < TIP_Y_FLOOR_PP:
            verdict = "FILL_LOCK_TIP_BLOCK"
        elif best["sealed_mdd_improve_pp"] is not None and float(
            best["sealed_mdd_improve_pp"]
        ) < SEALED_MDD_FLOOR_PP:
            verdict = "FILL_LOCK_MDD_BLOCK"
        else:
            verdict = "FILL_LOCK_SOFT"
    else:
        # all feasible fills ≤ always-within
        verdict = "FILL_LOCK_BLOCK"

    optimize = [
        "Question: which Path3 OFF-day FIN∪TEL fill unlocks ACCEPT under Soft FIN/TEL OFF?",
        (
            f"Verdict `{verdict}`: tip Soft Soft-refill ceiling vs L4 held "
            f"**+{tip_gap_held}** tipY **+{tip_gap_tipy}** (FORBIDDEN under WITHIN KEEP)"
        ),
        (
            f"Gate MUTE_S3_SAT Path3-ON only **{gate_info['pct_path3_on']}%** "
            f"(NEARPEAK3 **{gate_info.get('pct_nearpeak3_on')}%**) — OFF ≈90%"
        ),
        (
            f"Soft-core MUTE×FREEZE vs ALWAYS_WITHIN held **{freeze['held_cagr_lift_pp']}** "
            f"tipY **{freeze['tipY_pp']}** sealedMDD **{freeze['sealed_mdd_improve_pp']}** "
            f"· off **{freeze['meta'].get('pct_off')}%**"
        ),
        (
            f"Soft-core MUTE×FT→0050 held **{to0050['held_cagr_lift_pp']}** tipY "
            f"**{to0050['tipY_pp']}** sealedMDD **{to0050['sealed_mdd_improve_pp']}**"
        ),
        (
            f"Soft-core MUTE×FT→CASH held **{tocash['held_cagr_lift_pp']}** tipY "
            f"**{tocash['tipY_pp']}** sealedMDD **{tocash['sealed_mdd_improve_pp']}**"
        ),
        (
            "Best feasible Soft-core fill: "
            + (
                f"**{best['arm']}** held **{best['held_cagr_lift_pp']}** tipY "
                f"**{best['tipY_pp']}**"
                if best
                else "none — freeze/0050/cash all lose held vs ALWAYS_WITHIN"
            )
        ),
        (
            "Lock: tip Soft tipY needs Soft FIN/TEL refill on OFF days; "
            "non-Soft fills under ~90% OFF destroy Soft-core held"
        ),
        (
            "Disposition: "
            + (
                "promote Soft-core fill champion to tip Soft twin Stage B / ACCEPT ballot draft"
                if verdict == "FILL_LOCK_HIT"
                else "KEEP stamps · **no ACCEPT apply** — fill lock not cleared without Soft FIN/TEL"
                if verdict == "FILL_LOCK_BLOCK"
                else "fill has Soft-core edge but tip/MDD gate blocks ACCEPT — harden or KEEP stamps"
            )
        ),
        "Soft KEEP · Path4 OFF · broker false · Soft FIN/TEL stay OFF · no live wire",
    ]

    screen = {
        "id": SCREEN_ID,
        "register": REGISTER,
        "parents": list(PARENTS),
        "generated_at_utc": generated,
        "mech": MECH,
        "verdict": verdict,
        "gate": gate_info,
        "tip_soft_ceiling": {
            "held_vs_L4_pp": tip_gap_held,
            "tipY_vs_L4_pp": tip_gap_tipy,
            "feasible": False,
            "note": "Soft refill = MUTE_S3_SAT; FORBIDDEN under Path3 WITHIN KEEP",
        },
        "floors": {
            "sealed_mdd_improve_pp": SEALED_MDD_FLOOR_PP,
            "tipY_pp": TIP_Y_FLOOR_PP,
            "held_edge_pp": HELD_EDGE_PP,
        },
        "arms": rows,
        "n_softcore_clears": int(len(clears)),
        "best_feasible_softcore": best,
        "optimize_live": optimize,
        "soft_keep": True,
        "path4_live": False,
        "broker": False,
        "live_wire": False,
        "label": f"{SCREEN_ID}_{generated[:10]}__{verdict}",
    }
    (OUT / "screen.json").write_text(json.dumps(screen, indent=2, default=str) + "\n")

    # Charter
    charter_md = "\n".join(
        [
            f"# {CHARTER_ID}",
            "",
            f"Date: {generated[:10]}",
            f"Register: **{REGISTER}** · Parents: {', '.join(PARENTS)}",
            "",
            "## Question",
            "",
            "Before ACCEPT for intermittent Path3 (to close tip Soft tipY gap), which "
            "**Path3 OFF-day FIN∪TEL ownership fill** works under Soft FIN/TEL Exact T+1 "
            "stay OFF · Path3 WITHIN KEEP intent?",
            "",
            "## Method",
            "",
            "- Tip Soft Exact T+1: Soft-refill ceiling = `MUTE_S3_SAT` vs L4 (FORBIDDEN)",
            "- Soft-core T+0 carve: MUTE_S3_SAT gate · ON=`WITHIN_DAILY` · OFF fills "
            "`FREEZE` / `FT_TO_0050` / `FT_TO_CASH`",
            "- Score held / sealed MDD / tipY vs Soft-core ALWAYS_WITHIN",
            "",
            "## Forbidden",
            "",
            "- Soft FIN/TEL Exact T+1 re-enable · Path4 live · year-cut · hybrid T+0 "
            "promote · broker · live apply wire without ACCEPT",
            "",
            f"Label: `{CHARTER_ID}_{generated[:10]}`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{CHARTER_ID}.md", REP / f"{CHARTER_ID}.md", charter_md, kind="charter"
    )
    write_ops_and_repro_pointer(
        OPS / f"{CHARTER_ID}.json",
        REP / f"{CHARTER_ID}.json",
        json.dumps(
            {
                "id": CHARTER_ID,
                "register": REGISTER,
                "parents": list(PARENTS),
                "question": "Path3 OFF-day FIN∪TEL fill lock before ACCEPT",
                "label": f"{CHARTER_ID}_{generated[:10]}",
            },
            indent=2,
        )
        + "\n",
        kind="charter json",
    )

    # Screen MD
    lines = [
        f"# {SCREEN_ID}",
        "",
        f"Date: {generated[:10]} · Register: **{REGISTER}** · Verdict: **`{verdict}`**",
        "",
        f"Gate: `{gate_info['gate']}` · Path3-ON **{gate_info['pct_path3_on']}%**",
        "",
        f"Tip Soft Soft-refill ceiling vs L4: held **+{tip_gap_held}** · tipY **+{tip_gap_tipy}** (FORBIDDEN)",
        "",
        "| Arm | clock | held | tipY | sealedMDD | feasible | Soft FIN/TEL |",
        "|---|---|---:|---:|---:|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| `{r['arm']}` | {r['clock']} | {r['held_cagr_lift_pp']} | {r['tipY_pp']} | "
            f"{r['sealed_mdd_improve_pp']} | "
            f"{'Y' if r['feasible_under_soft_fin_tel_off'] else 'N'} | "
            f"{'Y' if r['soft_fin_tel_required'] else 'N'} |"
        )
    lines += ["", "## Optimize live", ""]
    for i, line in enumerate(optimize, 1):
        lines.append(f"{i}. {line}")
    lines += ["", f"Label: `{screen['label']}`", ""]
    write_ops_and_repro_pointer(
        OPS / f"{SCREEN_ID}.md",
        REP / f"{SCREEN_ID}.md",
        "\n".join(lines),
        kind="screen",
    )
    write_ops_and_repro_pointer(
        OPS / f"{SCREEN_ID}.json",
        REP / f"{SCREEN_ID}.json",
        json.dumps(screen, indent=2, default=str) + "\n",
        kind="screen json",
    )

    # Decision
    decision_md = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: {generated[:10]} · Verdict: **`{verdict}`**",
            f"Register: **{REGISTER}** · Parents: {', '.join(PARENTS)}",
            "",
            "## Answer",
            "",
            (
                "**A Soft-core OFF-day fill clears vs ALWAYS_WITHIN — candidate for tip Soft twin / ACCEPT draft.**"
                if verdict == "FILL_LOCK_HIT"
                else "**No Soft-core OFF-day fill clears the ACCEPT precondition under Soft FIN/TEL OFF.**"
                if verdict == "FILL_LOCK_BLOCK"
                else f"**Soft-core fill shows partial edge (`{verdict}`) — not yet ACCEPT-ready.**"
            ),
            "",
            f"- Tip Soft Soft-refill ceiling (FORBIDDEN): held **+{tip_gap_held}** tipY **+{tip_gap_tipy}**",
            f"- Soft-core FREEZE: held **{freeze['held_cagr_lift_pp']}** tipY **{freeze['tipY_pp']}**",
            f"- Soft-core FT→0050: held **{to0050['held_cagr_lift_pp']}** tipY **{to0050['tipY_pp']}**",
            f"- Soft-core FT→CASH: held **{tocash['held_cagr_lift_pp']}** tipY **{tocash['tipY_pp']}**",
            (
                f"- Best feasible: **`{best['arm']}`**"
                if best
                else "- Best feasible: none"
            ),
            "",
            "## Disposition",
            "",
            "- Soft FIN/TEL Exact T+1 stay OFF · Path3 WITHIN intent KEEP",
            (
                "- Next: tip Soft Exact T+1 twin of Soft-core fill champion → observe / ACCEPT ballot"
                if verdict == "FILL_LOCK_HIT"
                else "- Next: KEEP `gate_stamps_telemetry` · no apply ACCEPT · optional harden fill/gate"
            ),
            "- Path4 OFF · broker false · no live wire this pack",
            "",
            "## Next (optimize list)",
            "",
        ]
    )
    for i, line in enumerate(optimize, 1):
        decision_md += f"{i}. {line}\n"
    decision_md += f"\nLabel: `{DECISION_ID}_{generated[:10]}__{verdict}__NO_LIVE`\n"
    write_ops_and_repro_pointer(
        OPS / f"{DECISION_ID}.md",
        REP / f"{DECISION_ID}.md",
        decision_md,
        kind="decision pack",
    )
    write_ops_and_repro_pointer(
        OPS / f"{DECISION_ID}.json",
        REP / f"{DECISION_ID}.json",
        json.dumps(
            {
                "id": DECISION_ID,
                "register": REGISTER,
                "parents": list(PARENTS),
                "verdict": verdict,
                "generated_at_utc": generated,
                "tip_soft_ceiling": screen["tip_soft_ceiling"],
                "best_feasible_softcore": best,
                "n_softcore_clears": int(len(clears)),
                "optimize_live": optimize,
                "live_wire": False,
                "label": f"{DECISION_ID}_{generated[:10]}__{verdict}__NO_LIVE",
            },
            indent=2,
            default=str,
        )
        + "\n",
        kind="decision pack json",
    )

    print(
        json.dumps(
            {
                "verdict": verdict,
                "tip_gap_held": tip_gap_held,
                "tip_gap_tipy": tip_gap_tipy,
                "gate": gate_info,
                "best": None
                if best is None
                else {
                    "arm": best["arm"],
                    "held": best["held_cagr_lift_pp"],
                    "tipY": best["tipY_pp"],
                    "sealed_mdd": best["sealed_mdd_improve_pp"],
                },
                "freeze": {
                    "held": freeze["held_cagr_lift_pp"],
                    "tipY": freeze["tipY_pp"],
                    "pct_off": freeze["meta"].get("pct_off"),
                },
                "ft_0050": {
                    "held": to0050["held_cagr_lift_pp"],
                    "tipY": to0050["tipY_pp"],
                },
                "ft_cash": {
                    "held": tocash["held_cagr_lift_pp"],
                    "tipY": tocash["tipY_pp"],
                },
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
