#!/usr/bin/env python3
"""I_p3 asymmetric gate Stage A (0kb0).

After 0kaz exhausted same-family AND confirms/mutes (held+ vs NEAR = 0), change the
gate *mechanism*:

1. Asymmetric enter≠exit latch (enter=NEAR / NEAR∧sat; exit=bleed/defend/off-peak)
2. Hysteresis / min-stay / cooldown
3. Soft α∈[0,1] tilt on P3 premium (hard 0/1 already hit the wall)
4. Layer mutex: COOL defending → force I_p3=0

Goal: daily signal chooses live / P3 / P3+P4, close year-oracle gap, held ≥ NEARPEAK3.

Exact T+1 only · hybrid T+0 FORBIDDEN · Soft KEEP · Path4 live OFF · no year-cut.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from cool_c8_proxy_observe_helpers import build_cool_c8_exposure
from e45_paper_harness import WINDOWS_STANDARD, window_stats
from fin_sell_quality_helpers import cagr_lift_pp
from ops_repro_ssot import write_ops_and_repro_pointer, write_repro_pointer
from research_metric_helpers import mdd_delta_pp

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "tipsoft-ip3-asymm-gate-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

LIVESTACK = ROOT / "repro" / "fin-sat-path3-path4-livestack-twin-stageb" / "outputs"
ALIGN = ROOT / "repro" / "research-live-align-gap-stagea" / "outputs"
HARDEN = ROOT / "repro" / "meta-detect-sealed-mdd-harden-stagea" / "outputs"
P3_SIG = (
    ROOT / "repro" / "fin-sat-path3-t0-dual-paper-observe" / "outputs" / "p3_t0_state_signal.csv"
)

CHARTER_ID = "TIPSOFT_IP3_ASYMM_GATE_STAGEA_CHARTER"
SCREEN_ID = "TIPSOFT_IP3_ASYMM_GATE_STAGEA_SCREEN"
DECISION_ID = "TIPSOFT_IP3_ASYMM_GATE_STAGEA_DECISION_PACK"
REGISTER = "0kb0"
PARENTS = ("0kaz", "0kay", "0kaw", "0kau")
MECH = "TIPSOFT_IP3_ASYMM_GATE"

BASE_ID = "BASE_LIVE_FUSE_COOL"
NEAR_ID = "REF_P3_THETA_NEARPEAK3"
P34_ID = "REF_P4_C001_NEAR_AND_SAT"
SEALED_MDD_FLOOR_PP = -0.25
TIP_Y_FLOOR_PP = -1.0
HELD_CAGR_FLOOR_PP = 0.10
P3_THETA = 0.005
VS_NEAR_HELD_FLOOR = 0.0
YEAR_GAP_IMPROVE_FLOOR = 0.05


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


def _nav_from_returns(r: pd.Series, nav0: float) -> pd.DataFrame:
    nav = (1.0 + r.fillna(0.0)).cumprod() * float(nav0)
    return pd.DataFrame({"date": nav.index, "nav": nav.to_numpy()}).reset_index(drop=True)


def _dd_from_peak(nav: pd.DataFrame, win: int = 63) -> pd.Series:
    s = nav.set_index("date")["nav"].astype(float).sort_index()
    peak = s.rolling(win, min_periods=5).max()
    return (s / peak - 1.0).fillna(0.0)


def _proxy_mdd63(nav: pd.DataFrame) -> pd.Series:
    s = nav.set_index("date")["nav"].astype(float).sort_index()
    peak = s.cummax()
    dd = s / peak - 1.0
    return dd.rolling(63, min_periods=5).min().fillna(0.0)


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


def _arm_verdict_vs_live(delta: dict[str, Any], tip: dict[str, Any]) -> str:
    held = delta["heldout_2019_plus"]
    sealed = delta["sealed_2023_plus"]
    tip_y = (tip.get("ytd") or {}).get("cagr_lift_pp")
    if held.get("cagr_lift_pp") is None or sealed.get("mdd_improve_pp") is None:
        return "INCOMPLETE"
    held_ok = float(held["cagr_lift_pp"]) >= HELD_CAGR_FLOOR_PP
    sealed_ok = float(sealed["mdd_improve_pp"]) >= SEALED_MDD_FLOOR_PP
    tip_ok = tip_y is None or float(tip_y) >= TIP_Y_FLOOR_PP
    full_ok = float(delta["full"].get("cagr_lift_pp") or 0) > 0
    if held_ok and sealed_ok and tip_ok and full_ok:
        return "HIT"
    if held_ok and sealed_ok and tip_ok:
        return "HELD_HIT"
    if sealed_ok and tip_ok and float(held["cagr_lift_pp"]) > 0.02:
        return "SOFT"
    if float(sealed["mdd_improve_pp"]) < SEALED_MDD_FLOOR_PP:
        return "MDD_BLOCK"
    if tip_y is not None and float(tip_y) < TIP_Y_FLOOR_PP:
        return "TIP_BLOCK"
    return "NO_EDGE"


def _year_rets(r: pd.Series) -> pd.Series:
    df = r.copy().to_frame("r")
    df["year"] = df.index.year
    out = {}
    for y, g in df.groupby("year"):
        if len(g) < 2:
            continue
        out[int(y)] = float((1.0 + g["r"]).prod() - 1.0) * 100.0
    return pd.Series(out, dtype=float)


def _year_oracle_gap(
    policy_r: pd.Series, live_r: pd.Series, near_r: pd.Series, p34_r: pd.Series
) -> dict[str, Any]:
    yp = _year_rets(policy_r)
    yl = _year_rets(live_r)
    yn = _year_rets(near_r)
    y4 = _year_rets(p34_r)
    years = sorted(set(yp.index) & set(yl.index) & set(yn.index) & set(y4.index))
    if not years:
        return {
            "mean_policy": None,
            "mean_oracle": None,
            "gap_to_oracle_pp": None,
            "n_years": 0,
            "best_counts": {},
        }
    rows = []
    best_counts = {"live": 0, "P3": 0, "P3+P4": 0, "policy": 0}
    for y in years:
        live_v, near_v, p34_v, pol_v = float(yl[y]), float(yn[y]), float(y4[y]), float(yp[y])
        oracle = max(live_v, near_v, p34_v)
        base_best = max(
            [("live", live_v), ("P3", near_v), ("P3+P4", p34_v)], key=lambda t: t[1]
        )[0]
        best_counts[base_best] += 1
        if pol_v >= oracle - 1e-9:
            best_counts["policy"] += 1
        rows.append(
            {
                "year": y,
                "live": round(live_v, 4),
                "P3": round(near_v, 4),
                "P3+P4": round(p34_v, 4),
                "policy": round(pol_v, 4),
                "oracle": round(oracle, 4),
                "gap": round(oracle - pol_v, 4),
                "base_best": base_best,
            }
        )
    mean_pol = float(sum(r["policy"] for r in rows) / len(rows))
    mean_ora = float(sum(r["oracle"] for r in rows) / len(rows))
    return {
        "mean_policy": round(mean_pol, 4),
        "mean_oracle": round(mean_ora, 4),
        "gap_to_oracle_pp": round(mean_ora - mean_pol, 4),
        "n_years": len(rows),
        "best_counts": best_counts,
        "years": rows,
    }


def _asymm_latch(
    enter: np.ndarray,
    exit_sig: np.ndarray,
    *,
    min_stay: int = 0,
    cooldown: int = 0,
) -> np.ndarray:
    """Causal latch: enter when off+enter; leave when on+exit after min_stay; cooldown blocks re-enter."""
    n = len(enter)
    out = np.zeros(n, dtype=float)
    on = False
    age = 0
    cool_left = 0
    for i in range(n):
        if cool_left > 0:
            cool_left -= 1
        if not on:
            if cool_left == 0 and bool(enter[i]):
                on = True
                age = 1
                out[i] = 1.0
            else:
                out[i] = 0.0
            continue
        # currently on
        age += 1
        if bool(exit_sig[i]) and age > int(min_stay):
            on = False
            age = 0
            cool_left = int(cooldown)
            out[i] = 0.0
        else:
            out[i] = 1.0
    return out


def _soft_peak_alpha(dd63: pd.Series, p3_theta: pd.Series, lo: float, hi: float) -> pd.Series:
    """α ramps 0→1 as Soft dd63 moves from lo (farther from peak) to hi (nearer)."""
    # dd63 is negative drawdown; nearer peak ⇒ dd closer to 0.
    # Map dd in [lo, hi] → α in [0, 1]; dd>=hi → 1; dd<=lo → 0.
    span = max(float(hi) - float(lo), 1e-9)
    raw = ((dd63.astype(float) - float(lo)) / span).clip(0.0, 1.0)
    return (raw * p3_theta.astype(float)).fillna(0.0)


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()

    nav_l3 = _load_nav(LIVESTACK / "nav_BASE_LIVE_FUSE_COOL.csv")
    nav_p3 = _load_nav(LIVESTACK / "nav_LIVE_P3_WITHIN.csv")
    soft_l1 = _load_nav(ALIGN / "nav_L1_SOFT_T1.csv")
    near_nav = _load_nav(HARDEN / "nav_P3_THETA_NEARPEAK3.csv")
    p34_path = (
        ROOT
        / "repro"
        / "tipsoft-path4-held-pos-gate-stagea"
        / "outputs"
        / "nav_P4_C001_NEAR_AND_SAT.csv"
    )
    if not p34_path.exists():
        p34_path = (
            ROOT
            / "repro"
            / "tipsoft-path4-held-pos-gate-stagea"
            / "outputs"
            / "nav_P4_C001_NEAR&SAT.csv"
        )
    p34_nav = _load_nav(p34_path)
    nav0 = float(nav_l3["nav"].iloc[0])
    p4_book = _load_nav(LIVESTACK / "nav_LIVE_P3_P4_CASH_001.csv")

    r3 = _returns(nav_l3)
    rp3 = _returns(nav_p3)
    r_p4 = _returns(p4_book)
    panel = pd.concat({"r3": r3, "rp3": rp3, "rp4": r_p4}, axis=1, join="inner").dropna(
        how="any"
    )
    prem_p3 = panel["rp3"] - panel["r3"]
    prem_p4 = panel["rp4"] - panel["rp3"]
    live_r = panel["r3"]

    proxy = _proxy_mdd63(soft_l1).reindex(panel.index).fillna(0.0)
    dd63 = _dd_from_peak(soft_l1, 63).reindex(panel.index).fillna(0.0)
    cool_exp = build_cool_c8_exposure(panel.index, proxy)
    risk_on = cool_exp >= 0.999
    defending = ~risk_on

    sig = pd.read_csv(P3_SIG, parse_dates=["date"])
    sig["date"] = pd.to_datetime(sig["date"]).dt.normalize()
    sig = sig.set_index("date").reindex(panel.index)
    trail = sig["trail_rel_63"].astype(float)
    sat_lead = sig["sat_lead"].fillna(False).astype(bool)
    p3_theta = (trail.abs() >= float(P3_THETA)).fillna(False)
    nearpeak3 = p3_theta & (dd63 >= -0.03)

    soft_r = _returns(soft_l1).reindex(panel.index).fillna(0.0)
    soft_r5 = soft_r.shift(1).rolling(5, min_periods=3).sum().fillna(0.0)
    prem_p3_lag5 = prem_p3.shift(1).rolling(5, min_periods=3).sum().fillna(0.0)
    not_bleed = prem_p3_lag5 >= 0.0
    bleed = ~not_bleed
    soft_r5_neg = soft_r5 < 0
    offpeak3 = dd63 < -0.03
    offpeak5 = dd63 < -0.05
    trail_fade = trail.abs() < float(P3_THETA)
    trail_fade2 = trail.abs() < 0.002

    near_r = live_r + nearpeak3.astype(float) * prem_p3
    p34_r = live_r + nearpeak3.astype(float) * prem_p3 + (nearpeak3 & sat_lead).astype(
        float
    ) * prem_p4

    # --- build alpha / I_p3 candidates ---
    enter_map: dict[str, np.ndarray] = {
        "NEAR": nearpeak3.to_numpy(dtype=bool),
        "NEAR_SAT": (nearpeak3 & sat_lead).to_numpy(dtype=bool),
        "NEAR_RISKON": (nearpeak3 & risk_on).to_numpy(dtype=bool),
    }
    exit_map: dict[str, np.ndarray] = {
        "OFFPEAK3": offpeak3.to_numpy(dtype=bool),
        "OFFPEAK5": offpeak5.to_numpy(dtype=bool),
        "BLEED": bleed.to_numpy(dtype=bool),
        "DEFEND": defending.to_numpy(dtype=bool),
        "R5NEG": soft_r5_neg.to_numpy(dtype=bool),
        "TRAILFADE": trail_fade.to_numpy(dtype=bool),
        "TRAILFADE2": trail_fade2.to_numpy(dtype=bool),
        "NOTSAT": (~sat_lead).to_numpy(dtype=bool),
    }

    alpha_arms: dict[str, tuple[str, pd.Series]] = {}
    # Refs (symmetric hard)
    alpha_arms["REF_NEAR_HARD"] = ("REF", nearpeak3.astype(float))
    alpha_arms["REF_NEAR_SAT_HARD"] = ("REF", (nearpeak3 & sat_lead).astype(float))
    alpha_arms["REF_MUTEX_RISKON"] = ("MUTEX", (nearpeak3 & risk_on).astype(float))

    # Soft α tilts (hard switch wall → continuous premium)
    for a in (0.25, 0.5, 0.75):
        alpha_arms[f"SOFT_NEAR_A{str(a).replace('.', '')}"] = (
            "SOFT",
            nearpeak3.astype(float) * float(a),
        )
        alpha_arms[f"SOFT_NEARSAT_A{str(a).replace('.', '')}"] = (
            "SOFT",
            (nearpeak3 & sat_lead).astype(float) * float(a),
        )
    alpha_arms["SOFT_PEAK_RAMP_0503"] = (
        "SOFT",
        _soft_peak_alpha(dd63, p3_theta, lo=-0.05, hi=-0.00),
    )
    alpha_arms["SOFT_PEAK_RAMP_0300"] = (
        "SOFT",
        _soft_peak_alpha(dd63, p3_theta, lo=-0.03, hi=-0.00),
    )
    alpha_arms["SOFT_NEAR_x_RISKON"] = (
        "MUTEX",
        nearpeak3.astype(float) * risk_on.astype(float),
    )
    alpha_arms["SOFT_NEAR_A05_x_RISKON"] = (
        "MUTEX",
        nearpeak3.astype(float) * 0.5 * risk_on.astype(float),
    )
    # Force off under COOL defend (layer mutex on top of NEAR)
    alpha_arms["MUTEX_NEAR_FORCEOFF_DEFEND"] = (
        "MUTEX",
        (nearpeak3 & (~defending)).astype(float),
    )

    # Asymmetric latches (enter ≠ exit)
    for ename, earr in enter_map.items():
        for xname, xarr in exit_map.items():
            # Skip degenerate: enter NEAR + exit OFFPEAK3 ≈ symmetric nearpeak3
            if ename == "NEAR" and xname == "OFFPEAK3":
                continue
            # NOTSAT exit only meaningful when enter includes sat
            if xname == "NOTSAT" and ename == "NEAR":
                continue
            for ms in (0, 3, 5, 8):
                for cd in (0, 3, 5):
                    # Keep grid finite: only vary cooldown when min_stay>0 or ms=0/cd=0 primary
                    if cd > 0 and ms == 0 and xname not in ("BLEED", "DEFEND", "OFFPEAK5"):
                        continue
                    if ms > 5 and cd > 3:
                        continue
                    if ename != "NEAR" and ms not in (0, 5):
                        continue
                    if ename != "NEAR" and cd not in (0, 3):
                        continue
                    name = f"ASYMM_{ename}__X_{xname}__MS{ms}_CD{cd}"
                    latch = _asymm_latch(earr, xarr, min_stay=ms, cooldown=cd)
                    # Layer-mutex variant: force off while defending
                    alpha_arms[name] = ("ASYMM", pd.Series(latch, index=panel.index))
                    if xname != "DEFEND" and ms in (0, 5) and cd in (0, 3):
                        muted = latch.copy()
                        muted[defending.to_numpy(dtype=bool)] = 0.0
                        alpha_arms[f"{name}__MUTEXDEF"] = (
                            "ASYMM_MUTEX",
                            pd.Series(muted, index=panel.index),
                        )

    # Hysteresis band: enter peak3, exit peak5 (enter≠exit by design)
    for ms in (0, 3, 5, 8):
        for cd in (0, 3, 5):
            latch = _asymm_latch(
                enter_map["NEAR"],
                exit_map["OFFPEAK5"],
                min_stay=ms,
                cooldown=cd,
            )
            alpha_arms[f"HYST_PEAK3IN_PEAK5OUT_MS{ms}_CD{cd}"] = (
                "HYST",
                pd.Series(latch, index=panel.index),
            )

    # Soft α on asymmetric champion-shaped enter/exit (selected combos)
    for ename, xname, a in (
        ("NEAR", "BLEED", 0.5),
        ("NEAR", "DEFEND", 0.5),
        ("NEAR", "OFFPEAK5", 0.5),
        ("NEAR", "BLEED", 0.75),
        ("NEAR_SAT", "BLEED", 0.5),
        ("NEAR_SAT", "NOTSAT", 0.5),
        ("NEAR_RISKON", "DEFEND", 0.5),
    ):
        for ms in (0, 5):
            latch = _asymm_latch(
                enter_map[ename], exit_map[xname], min_stay=ms, cooldown=0
            )
            alpha_arms[
                f"SOFTASYMM_{ename}__X_{xname}__A{str(a).replace('.', '')}_MS{ms}"
            ] = (
                "SOFT_ASYMM",
                pd.Series(latch, index=panel.index) * float(a),
            )

    # Lookahead DIAG only
    alpha_arms["ORACLE_POS_DIAG"] = (
        "ORACLE",
        (nearpeak3 & (prem_p3 > 0)).astype(float),
    )

    p4_modes = {
        "P4OFF": lambda a3: pd.Series(0.0, index=panel.index),
        "P4_SAT": lambda a3: (a3 > 1e-12) & sat_lead,
        "P4_ON_ALPHA": lambda a3: ((a3 > 1e-12) & sat_lead).astype(float) * a3.clip(0, 1),
    }

    base_w = _pack(nav_l3)
    near_nav_r = _nav_from_returns(near_r, nav0)
    p34_nav_r = _nav_from_returns(p34_r, nav0)
    near_w = _pack(near_nav_r)
    near_nav_r.to_csv(OUT / f"nav_{NEAR_ID}.csv", index=False)
    p34_nav_r.to_csv(OUT / f"nav_{P34_ID}.csv", index=False)
    nav_l3.to_csv(OUT / f"nav_{BASE_ID}.csv", index=False)

    near_year_gap = _year_oracle_gap(near_r, live_r, near_r, p34_r)
    live_year_gap = _year_oracle_gap(live_r, live_r, near_r, p34_r)
    p34_year_gap = _year_oracle_gap(p34_r, live_r, near_r, p34_r)

    rows: list[dict[str, Any]] = []
    arms_nav: dict[str, pd.DataFrame] = {
        BASE_ID: nav_l3,
        NEAR_ID: near_nav_r,
        P34_ID: p34_nav_r,
    }

    for gname, (fam, a3) in alpha_arms.items():
        a3 = a3.reindex(panel.index).fillna(0.0).astype(float).clip(0.0, 1.0)
        for p4name, p4fn in p4_modes.items():
            if gname == "ORACLE_POS_DIAG" and p4name not in ("P4OFF", "P4_SAT"):
                continue
            # Soft-α Path4 only for SOFT / SOFT_ASYMM / MUTEX families to limit grid
            if p4name == "P4_ON_ALPHA" and fam not in ("SOFT", "SOFT_ASYMM", "MUTEX", "REF"):
                continue
            i4_raw = p4fn(a3)
            if isinstance(i4_raw, pd.Series) and i4_raw.dtype == bool:
                i4 = i4_raw.astype(float)
            else:
                i4 = pd.Series(i4_raw, index=panel.index).astype(float)
            i4 = i4.reindex(panel.index).fillna(0.0).clip(0.0, 1.0)
            # Path4 never without Path3 intent
            i4 = i4 * (a3 > 1e-12).astype(float)
            arm = f"{gname}__{p4name}"
            r = live_r + a3 * prem_p3 + i4 * prem_p4
            nav = _nav_from_returns(r, nav0)
            arms_nav[arm] = nav
            chal_w = _pack(nav)
            d_live = _delta(base_w, chal_w)
            d_near = _delta(near_w, chal_w)
            tip_live = _tip(nav_l3, nav)
            tip_near = _tip(near_nav_r, nav)
            yg = _year_oracle_gap(r, live_r, near_r, p34_r)
            held_vs_near = d_near["heldout_2019_plus"]["cagr_lift_pp"]
            sealed_vs_live = d_live["sealed_2023_plus"]["mdd_improve_pp"]
            tip_vs_live = (tip_live.get("ytd") or {}).get("cagr_lift_pp")
            gap = yg["gap_to_oracle_pp"]
            near_gap = near_year_gap["gap_to_oracle_pp"]
            gap_improve = (
                None
                if gap is None or near_gap is None
                else round(float(near_gap) - float(gap), 4)
            )
            held_pos = (
                held_vs_near is not None
                and float(held_vs_near) > VS_NEAR_HELD_FLOOR
                and sealed_vs_live is not None
                and float(sealed_vs_live) >= SEALED_MDD_FLOOR_PP
                and (tip_vs_live is None or float(tip_vs_live) >= TIP_Y_FLOOR_PP)
            )
            gap_close = (
                gap_improve is not None
                and float(gap_improve) >= YEAR_GAP_IMPROVE_FLOOR
                and sealed_vs_live is not None
                and float(sealed_vs_live) >= SEALED_MDD_FLOOR_PP
                and (tip_vs_live is None or float(tip_vs_live) >= TIP_Y_FLOOR_PP)
                and d_live["heldout_2019_plus"]["cagr_lift_pp"] is not None
                and float(d_live["heldout_2019_plus"]["cagr_lift_pp"]) >= HELD_CAGR_FLOOR_PP
            )
            rows.append(
                {
                    "arm": arm,
                    "gate": gname,
                    "family": fam,
                    "i_p4": p4name,
                    "mean_alpha": round(float(a3.mean()), 4),
                    "pct_p3_on": round(float((a3 > 1e-12).mean()) * 100, 2),
                    "pct_p4_on": round(float((i4 > 1e-12).mean()) * 100, 2),
                    "mean_i4": round(float(i4.mean()), 4),
                    "verdict_vs_live": _arm_verdict_vs_live(d_live, tip_live),
                    "held_vs_live": d_live["heldout_2019_plus"]["cagr_lift_pp"],
                    "full_vs_live": d_live["full"]["cagr_lift_pp"],
                    "sealed_vs_live": sealed_vs_live,
                    "tipY_vs_live": tip_vs_live,
                    "held_vs_near": held_vs_near,
                    "sealed_vs_near": d_near["sealed_2023_plus"]["mdd_improve_pp"],
                    "tipY_vs_near": (tip_near.get("ytd") or {}).get("cagr_lift_pp"),
                    "year_gap_to_oracle_pp": gap,
                    "year_gap_improve_vs_near_pp": gap_improve,
                    "year_mean_policy": yg["mean_policy"],
                    "held_pos_vs_near": bool(held_pos),
                    "year_gap_close": bool(gap_close),
                    "oracle": fam == "ORACLE",
                    "is_ref": fam == "REF",
                }
            )

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "arms_asymm_gate.csv", index=False)

    causal = df[~df["oracle"]].copy()
    mech = causal[~causal["is_ref"]].copy()  # exclude plain REF_NEAR* (0kaw/0kay shape)
    hits = mech[mech["held_pos_vs_near"] | mech["year_gap_close"]].copy()
    hits.to_csv(OUT / "asymm_hits.csv", index=False)

    by_fam = (
        mech.groupby("family")
        .agg(
            n=("arm", "count"),
            n_held_pos=("held_pos_vs_near", "sum"),
            n_gap_close=("year_gap_close", "sum"),
            max_held_vs_near=("held_vs_near", "max"),
            max_gap_improve=("year_gap_improve_vs_near_pp", "max"),
        )
        .reset_index()
    )
    by_fam.to_csv(OUT / "family_summary.csv", index=False)

    causal_sorted = mech.sort_values(
        by=[
            "held_pos_vs_near",
            "year_gap_close",
            "held_vs_near",
            "year_gap_improve_vs_near_pp",
            "sealed_vs_live",
            "tipY_vs_live",
        ],
        ascending=[False, False, False, False, False, False],
    )
    top = causal_sorted.head(20)
    top.to_csv(OUT / "top_arms.csv", index=False)

    champion_row = None
    soft_row = None
    held_hits = mech[mech["held_pos_vs_near"]]
    gap_hits = mech[mech["year_gap_close"]]
    if len(held_hits):
        champion_row = held_hits.sort_values(
            by=["held_vs_near", "year_gap_improve_vs_near_pp", "sealed_vs_live", "tipY_vs_live"],
            ascending=[False, False, False, False],
        ).iloc[0]
    if len(gap_hits):
        soft_row = gap_hits.sort_values(
            by=["held_vs_near", "year_gap_improve_vs_near_pp", "sealed_vs_live", "tipY_vs_live"],
            ascending=[False, False, False, False],
        ).iloc[0]

    n_held = int(mech["held_pos_vs_near"].sum())
    n_gap = int(mech["year_gap_close"].sum())
    oracle_rows = df[df["oracle"]]
    ref_rows = causal[causal["is_ref"]]

    if champion_row is not None and bool(champion_row["held_pos_vs_near"]):
        verdict = "IP3_ASYMM_HIT"
    elif (
        soft_row is not None
        and bool(soft_row["year_gap_close"])
        and float(soft_row["held_vs_near"] or 0) > -0.25
        and n_held == 0
    ):
        verdict = "IP3_ASYMM_YEAR_SOFT"
        champion_row = soft_row
    elif n_held == 0:
        verdict = "IP3_ASYMM_NO_EDGE"
        if soft_row is not None and champion_row is None:
            champion_row = soft_row
        elif champion_row is None and len(mech):
            champion_row = causal_sorted.iloc[0]
    else:
        verdict = "NO_EDGE_KEEP_NEAR"

    champ = None if champion_row is None else champion_row.to_dict()
    if champ:
        arms_nav[champ["arm"]].to_csv(OUT / f"nav_{champ['arm']}.csv", index=False)

    fam_note = "; ".join(
        f"{r.family}:held+={int(r.n_held_pos)}/gap={int(r.n_gap_close)}/maxΔ={r.max_held_vs_near}"
        for r in by_fam.itertuples()
    )

    optimize = [
        "Objective: asymmetric enter≠exit / hysteresis / soft-α / COOL-mutex gates so daily stack select closes year-oracle gap without year dummies; held ≥ NEARPEAK3",
        (
            f"Champion `{champ['arm']}` fam={champ['family']} held_vs_near={champ['held_vs_near']} "
            f"gap_improve={champ['year_gap_improve_vs_near_pp']} "
            f"sealed_vs_live={champ['sealed_vs_live']} tipY={champ['tipY_vs_live']} "
            f"live={champ['verdict_vs_live']}"
            if champ
            else "No mechanism champion"
        ),
        f"Mechanism held_pos clears: n={n_held} · year_gap_close n={n_gap} / screened_mech={len(mech)}",
        f"By family: {fam_note}",
        (
            f"NEAR year gap_to_oracle={near_year_gap['gap_to_oracle_pp']} · "
            f"live gap={live_year_gap['gap_to_oracle_pp']} · "
            f"P34 gap={p34_year_gap['gap_to_oracle_pp']} · "
            f"best_counts={near_year_gap['best_counts']}"
        ),
        (
            f"Oracle DIAG best held_vs_near="
            f"{None if oracle_rows.empty else oracle_rows['held_vs_near'].max()} "
            f"(lookahead — never promote)"
        ),
        (
            "Refs: "
            + (
                "; ".join(
                    f"{r['arm']} heldΔNEAR={r['held_vs_near']}"
                    for r in ref_rows.to_dict(orient="records")[:6]
                )
                if len(ref_rows)
                else "none"
            )
        ),
        "If IP3_ASYMM_HIT → draft observe; IP3_ASYMM_YEAR_SOFT → note only; "
        "IP3_ASYMM_NO_EDGE → KEEP 0kaw NEARPEAK3 · Path4 DRAFT 0kay only",
        "Soft KEEP · Path4 live OFF · hybrid T+0 FORBIDDEN · no year-cut · no wire",
    ]

    screen = {
        "id": SCREEN_ID,
        "register": REGISTER,
        "parents": list(PARENTS),
        "generated_at_utc": generated,
        "mech": MECH,
        "verdict": verdict,
        "n_gates_screened": len(causal),
        "n_mech_screened": len(mech),
        "n_held_pos_vs_near": n_held,
        "n_year_gap_close": n_gap,
        "family_summary": by_fam.to_dict(orient="records"),
        "champion": champ,
        "near_year_oracle": {
            k: near_year_gap[k]
            for k in ("mean_policy", "mean_oracle", "gap_to_oracle_pp", "n_years", "best_counts")
        },
        "live_year_oracle": {
            k: live_year_gap[k]
            for k in ("mean_policy", "mean_oracle", "gap_to_oracle_pp", "n_years", "best_counts")
        },
        "oracle_diag": None
        if oracle_rows.empty
        else oracle_rows.sort_values("held_vs_near", ascending=False).iloc[0].to_dict(),
        "top_arms": top.to_dict(orient="records"),
        "optimize_live": optimize,
        "soft_keep": True,
        "path4_live": False,
        "hybrid_t0_carve": False,
        "broker": False,
        "label": f"{SCREEN_ID}_{generated[:10]}__{verdict}",
    }
    (OUT / "screen.json").write_text(json.dumps(screen, indent=2) + "\n", encoding="utf-8")

    charter_md = "\n".join(
        [
            f"# {CHARTER_ID}",
            "",
            f"Date: {generated[:10]}",
            f"Register: **{REGISTER}** · Parents: {', '.join(PARENTS)}",
            "",
            "## Question",
            "",
            "Can **asymmetric enter≠exit**, **hysteresis / min-stay / cooldown**, "
            "**soft α∈[0,1] P3 tilt**, or **COOL-defend mutex** beat hard NEARPEAK3 "
            "on held while closing the year-book oracle gap — without year dummies "
            "or repeating 0kaz AND-confirm scans?",
            "",
            "## Design",
            "",
            "- Base: `BASE_LIVE_FUSE_COOL` Exact T+1",
            "- Ref: `I_p3=NEARPEAK3` (0kaw) · Path4 `NEAR∧sat_lead` CASH_001 (0kay DRAFT)",
            "- Families: ASYMM latch · HYST peak3→peak5 · SOFT α · MUTEX defend-off · SOFT_ASYMM",
            "- Optional Path4: OFF / SAT / α-scaled SAT",
            "- Success: `held_vs_near > 0` + live sealed/tip floors **or** year_gap_improve ≥ "
            f"{YEAR_GAP_IMPROVE_FLOOR}pp with live held floor",
            "- Forbidden: year cuts · lookahead promote · hybrid T+0 · Path4 live wire · "
            "re-grid 0kaz AND confirms",
            "",
            f"Label: `{CHARTER_ID}_{generated[:10]}`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{CHARTER_ID}.md", REP / f"{CHARTER_ID}.md", charter_md, kind="charter"
    )
    charter_json = {
        "id": CHARTER_ID,
        "register": REGISTER,
        "parents": list(PARENTS),
        "mech": MECH,
        "date": generated[:10],
        "families": ["ASYMM", "HYST", "SOFT", "MUTEX", "SOFT_ASYMM", "ASYMM_MUTEX"],
        "forbidden": [
            "year_cut",
            "lookahead_promote",
            "hybrid_t0",
            "path4_live",
            "repeat_0kaz_and_confirm",
        ],
    }
    (OPS / f"{CHARTER_ID}.json").write_text(
        json.dumps(charter_json, indent=2) + "\n", encoding="utf-8"
    )
    write_repro_pointer(OPS / f"{CHARTER_ID}.json", REP / f"{CHARTER_ID}.json", kind="charter")

    screen_md_lines = [
        f"# {SCREEN_ID}",
        "",
        f"Date: {generated[:10]} · Verdict: **`{verdict}`** · champion=**`{(champ or {}).get('arm')}`**",
        f"Register: **{REGISTER}** · screened_mech={len(mech)} · held_pos={n_held} · year_gap_close={n_gap}",
        "",
        "## Year-oracle baseline",
        "",
        f"- live gap_to_oracle **{live_year_gap['gap_to_oracle_pp']}** pp · "
        f"NEAR **{near_year_gap['gap_to_oracle_pp']}** · P34 **{p34_year_gap['gap_to_oracle_pp']}**",
        f"- base_best counts (live/P3/P3+P4): `{near_year_gap['best_counts']}`",
        "",
        "## Family summary",
        "",
        "| Family | n | held+ | gap_close | max heldΔNEAR | max gap↑ |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for r in by_fam.to_dict(orient="records"):
        screen_md_lines.append(
            f"| {r['family']} | {r['n']} | {int(r['n_held_pos'])} | {int(r['n_gap_close'])} | "
            f"{r['max_held_vs_near']} | {r['max_gap_improve']} |"
        )
    screen_md_lines += [
        "",
        "## Top causal mechanism arms",
        "",
        "| Arm | fam | heldΔNEAR | gap↑vsNEAR | sealedΔlive | tipYΔlive | vs live | ᾱ | p3% | p4% |",
        "|---|---|---:|---:|---:|---:|---|---:|---:|---:|",
    ]
    for r in top.to_dict(orient="records"):
        screen_md_lines.append(
            f"| {r['arm']} | {r['family']} | {r['held_vs_near']} | {r['year_gap_improve_vs_near_pp']} | "
            f"{r['sealed_vs_live']} | {r['tipY_vs_live']} | {r['verdict_vs_live']} | "
            f"{r['mean_alpha']} | {r['pct_p3_on']} | {r['pct_p4_on']} |"
        )
    if not oracle_rows.empty:
        o = oracle_rows.sort_values("held_vs_near", ascending=False).iloc[0]
        screen_md_lines += [
            "",
            "## Oracle DIAG (lookahead)",
            "",
            f"| {o['arm']} | heldΔNEAR {o['held_vs_near']} | gap↑ {o['year_gap_improve_vs_near_pp']} | "
            f"sealed {o['sealed_vs_live']} | tipY {o['tipY_vs_live']} |",
        ]
    screen_md_lines += [
        "",
        "## Optimize / disposition",
        "",
        *[f"{i}. {line}" for i, line in enumerate(optimize, 1)],
        "",
        "Repro: `PYTHONPATH=scripts python3 scripts/tipsoft_ip3_asymm_gate_stagea.py`",
        "",
        f"Label: `{screen['label']}`",
        "",
    ]
    screen_md = "\n".join(screen_md_lines)
    write_ops_and_repro_pointer(
        OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", screen_md, kind="screen"
    )
    (OPS / f"{SCREEN_ID}.json").write_text(json.dumps(screen, indent=2) + "\n", encoding="utf-8")
    write_repro_pointer(OPS / f"{SCREEN_ID}.json", REP / f"{SCREEN_ID}.json", kind="screen")

    decision_md = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: {generated[:10]} · Verdict: **`{verdict}`** · champion=**`{(champ or {}).get('arm')}`**",
            f"Register: **{REGISTER}** · Parents: {', '.join(PARENTS)}",
            "",
            "## Result",
            "",
            (
                f"- family: **{(champ or {}).get('family')}**\n"
                f"- held vs NEARPEAK3: **{(champ or {}).get('held_vs_near')}** pp\n"
                f"- year_gap improve vs NEAR: **{(champ or {}).get('year_gap_improve_vs_near_pp')}** pp\n"
                f"- sealed vs live: **{(champ or {}).get('sealed_vs_live')}** pp\n"
                f"- tipY vs live: **{(champ or {}).get('tipY_vs_live')}** pp\n"
                f"- held_pos clears: **{n_held}** · year_gap_close: **{n_gap}** / {len(mech)}"
                if champ
                else f"- No arm cleared · screened_mech={len(mech)}"
            ),
            "",
            "## Disposition",
            "",
            "- Promote observe only on `IP3_ASYMM_HIT`",
            "- `IP3_ASYMM_YEAR_SOFT` → research note only · KEEP 0kaw NEARPEAK3",
            "- `IP3_ASYMM_NO_EDGE` → KEEP NEARPEAK3 observe · Path4 DRAFT (0kay) · no gate replace",
            "- Soft KEEP · Path4 live OFF · hybrid T+0 FORBIDDEN · no year-cut",
            "",
            "## Next",
            "",
            *[f"{i}. {line}" for i, line in enumerate(optimize, 1)],
            "",
            f"Label: `{DECISION_ID}_{generated[:10]}__{verdict}__NO_LIVE`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{DECISION_ID}.md", REP / f"{DECISION_ID}.md", decision_md, kind="decision pack"
    )
    decision_json = {
        "id": DECISION_ID,
        "register": REGISTER,
        "parents": list(PARENTS),
        "verdict": verdict,
        "champion": champ,
        "n_held_pos_vs_near": n_held,
        "n_year_gap_close": n_gap,
        "family_summary": by_fam.to_dict(orient="records"),
        "soft_keep": True,
        "path4_live": False,
        "hybrid_t0_carve": False,
        "label": f"{DECISION_ID}_{generated[:10]}__{verdict}__NO_LIVE",
    }
    (OPS / f"{DECISION_ID}.json").write_text(
        json.dumps(decision_json, indent=2) + "\n", encoding="utf-8"
    )
    write_repro_pointer(
        OPS / f"{DECISION_ID}.json", REP / f"{DECISION_ID}.json", kind="decision pack"
    )

    pd.DataFrame(near_year_gap["years"]).to_csv(OUT / "year_oracle_near.csv", index=False)
    if champ:
        yg_c = _year_oracle_gap(_returns(arms_nav[champ["arm"]]), live_r, near_r, p34_r)
        pd.DataFrame(yg_c["years"]).to_csv(OUT / "year_oracle_champion.csv", index=False)

    print(
        json.dumps(
            {
                "verdict": verdict,
                "champion": None if not champ else champ["arm"],
                "family": None if not champ else champ["family"],
                "held_vs_near": None if not champ else champ["held_vs_near"],
                "year_gap_improve_vs_near_pp": None
                if not champ
                else champ["year_gap_improve_vs_near_pp"],
                "n_held_pos": n_held,
                "n_year_gap_close": n_gap,
                "n_mech": len(mech),
                "near_gap_to_oracle": near_year_gap["gap_to_oracle_pp"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
