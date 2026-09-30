#!/usr/bin/env python3
"""Live-year residual episode Stage A (0kb3).

Parent 0kb2 ``OVERRIDE_LIVE_W42_M0005_K3`` still loses 2013 / 2019–20 vs live.
This pack does **not** re-grid full race space. It:

1. DIAG census of residual drag episodes in those years (feature only)
2. Focused causal overlays on the frozen 0kb2 champion aimed at those shapes:
   - short-window live-lead override (2013/2019 chop + sat)
   - defend / off-peak force-LIVE (2020 shape)
   - longer sticky LIVE after override

Exact T+1 · Soft KEEP · Path4 live OFF · hybrid T+0 FORBIDDEN · no year-cut.
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
REPRO = ROOT / "repro" / "tipsoft-ip3-live-year-residual-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

LIVESTACK = ROOT / "repro" / "fin-sat-path3-path4-livestack-twin-stageb" / "outputs"
ALIGN = ROOT / "repro" / "research-live-align-gap-stagea" / "outputs"
P3_SIG = (
    ROOT / "repro" / "fin-sat-path3-t0-dual-paper-observe" / "outputs" / "p3_t0_state_signal.csv"
)
PARENT_NAV = (
    ROOT
    / "repro"
    / "tipsoft-ip3-live-stack-race-stagea"
    / "outputs"
    / "nav_OVERRIDE_LIVE_W42_M0005_K3.csv"
)

CHARTER_ID = "TIPSOFT_IP3_LIVE_YEAR_RESIDUAL_STAGEA_CHARTER"
SCREEN_ID = "TIPSOFT_IP3_LIVE_YEAR_RESIDUAL_STAGEA_SCREEN"
DECISION_ID = "TIPSOFT_IP3_LIVE_YEAR_RESIDUAL_STAGEA_DECISION_PACK"
REGISTER = "0kb3"
PARENTS = ("0kb2", "0kb1", "0kaw")
MECH = "TIPSOFT_IP3_LIVE_YEAR_RESIDUAL"

BASE_ID = "BASE_LIVE_FUSE_COOL"
PARENT_ID = "REF_OVERRIDE_W42_M05_K3"
CHAMP0_ID = "REF_MUTE_S3_SAT_W63"
SEALED_MDD_FLOOR_PP = -0.25
TIP_Y_FLOOR_PP = -1.0
HELD_CAGR_FLOOR_PP = 0.10
P3_THETA = 0.005
HELD_EPS_VS_PARENT = -0.05
TARGET_YEARS = (2013, 2019, 2020)


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


def _year_table(policy_r, live_r, near_r, p34_r) -> dict[str, Any]:
    yp, yl, yn, y4 = map(_year_rets, (policy_r, live_r, near_r, p34_r))
    years = sorted(set(yp.index) & set(yl.index) & set(yn.index) & set(y4.index))
    rows = []
    wins = 0
    beats = 0
    for y in years:
        live_v, near_v, p34_v, pol_v = float(yl[y]), float(yn[y]), float(y4[y]), float(yp[y])
        oracle = max(live_v, near_v, p34_v)
        base_best = max(
            [("live", live_v), ("P3", near_v), ("P3+P4", p34_v)], key=lambda t: t[1]
        )[0]
        if pol_v >= oracle - 1e-6:
            wins += 1
        if pol_v > live_v + 1e-9:
            beats += 1
        rows.append(
            {
                "year": y,
                "live": round(live_v, 4),
                "P3": round(near_v, 4),
                "P3+P4": round(p34_v, 4),
                "policy": round(pol_v, 4),
                "oracle": round(oracle, 4),
                "gap": round(oracle - pol_v, 4),
                "delta_vs_live": round(pol_v - live_v, 4),
                "base_best": base_best,
                "target_residual": y in TARGET_YEARS,
                "beats_live": bool(pol_v > live_v + 1e-9),
                "policy_wins": bool(pol_v >= oracle - 1e-6),
            }
        )
    mean_pol = float(np.mean([r["policy"] for r in rows]))
    mean_ora = float(np.mean([r["oracle"] for r in rows]))
    tgt = [r for r in rows if r["target_residual"]]
    return {
        "mean_policy": round(mean_pol, 4),
        "mean_oracle": round(mean_ora, 4),
        "gap_to_oracle_pp": round(mean_ora - mean_pol, 4),
        "year_wins": wins,
        "n_beats_live": beats,
        "n_years": len(rows),
        "target_sum_delta_vs_live_pp": round(sum(r["delta_vs_live"] for r in tgt), 4),
        "target_n_beats_live": int(sum(1 for r in tgt if r["beats_live"])),
        "years": rows,
    }


def _trail_sum(x: pd.Series, w: int) -> pd.Series:
    return x.shift(1).rolling(int(w), min_periods=max(2, int(w) // 3)).sum()


def _three_state_mute_sat(nearpeak3, sat_lead, prem_p3, w=63, thr=-0.01):
    tr = _trail_sum(prem_p3, w).fillna(0.0)
    mute = ((tr < float(thr)) & sat_lead).to_numpy(dtype=bool)
    want_p3 = nearpeak3.to_numpy(dtype=bool)
    want_p4 = (nearpeak3 & sat_lead).to_numpy(dtype=bool)
    n = len(want_p3)
    i3 = np.zeros(n)
    i4 = np.zeros(n)
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
        i4[i] = 1.0 if state >= 2 else 0.0
    idx = nearpeak3.index
    return pd.Series(i3, index=idx), pd.Series(i4, index=idx)


def _override_live_confirm(live_r, champ_r, w=42, margin=0.005, k=3) -> pd.Series:
    lead = (_trail_sum(live_r, w) - _trail_sum(champ_r, w)).fillna(0.0)
    conf = lead > float(margin)
    for j in range(1, int(k)):
        conf = conf & (lead.shift(j).fillna(0.0) > float(margin))
    return pd.Series(np.where(conf.to_numpy(), live_r, champ_r), index=live_r.index)


def _episodes(mask: np.ndarray, dates, drag: pd.Series) -> list[dict]:
    out = []
    i = 0
    n = len(mask)
    while i < n:
        if not mask[i]:
            i += 1
            continue
        j = i
        while j < n and mask[j]:
            j += 1
        seg = drag.iloc[i:j]
        out.append(
            {
                "start": str(pd.Timestamp(dates[i]).date()),
                "end": str(pd.Timestamp(dates[j - 1]).date()),
                "n_days": int(j - i),
                "sum_delta_pp": round(float(seg.sum()) * 100, 4),
                "year": int(pd.Timestamp(dates[i]).year),
            }
        )
        i = j
    return out


def _apply_force_live(
    base_r: pd.Series,
    live_r: pd.Series,
    force: np.ndarray,
    sticky: int = 0,
) -> pd.Series:
    """When force True use live; optional sticky keep LIVE for sticky days after force drops."""
    n = len(base_r)
    out = np.zeros(n)
    cool = 0
    for i in range(n):
        if force[i]:
            out[i] = float(live_r.iloc[i])
            cool = int(sticky)
        elif cool > 0:
            out[i] = float(live_r.iloc[i])
            cool -= 1
        else:
            out[i] = float(base_r.iloc[i])
    return pd.Series(out, index=base_r.index)


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()

    nav_l3 = _load_nav(LIVESTACK / "nav_BASE_LIVE_FUSE_COOL.csv")
    nav_p3 = _load_nav(LIVESTACK / "nav_LIVE_P3_WITHIN.csv")
    soft_l1 = _load_nav(ALIGN / "nav_L1_SOFT_T1.csv")
    p4_book = _load_nav(LIVESTACK / "nav_LIVE_P3_P4_CASH_001.csv")
    parent_file = _load_nav(PARENT_NAV)
    nav0 = float(nav_l3["nav"].iloc[0])

    panel = pd.concat(
        {
            "r3": _returns(nav_l3),
            "rp3": _returns(nav_p3),
            "rp4": _returns(p4_book),
        },
        axis=1,
        join="inner",
    ).dropna(how="any")
    live_r = panel["r3"]
    prem_p3 = panel["rp3"] - panel["r3"]
    prem_p4 = panel["rp4"] - panel["rp3"]

    dd63 = _dd_from_peak(soft_l1, 63).reindex(panel.index).fillna(0.0)
    proxy = _proxy_mdd63(soft_l1).reindex(panel.index).fillna(0.0)
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
    offpeak3 = dd63 < -0.03
    offpeak5 = dd63 < -0.05

    near_r = live_r + nearpeak3.astype(float) * prem_p3
    p34_r = (
        live_r
        + nearpeak3.astype(float) * prem_p3
        + (nearpeak3 & sat_lead).astype(float) * prem_p4
    )

    i3, i4 = _three_state_mute_sat(nearpeak3, sat_lead, prem_p3)
    s3_r = live_r + i3 * prem_p3 + i4 * prem_p4
    parent_r = _override_live_confirm(live_r, s3_r, w=42, margin=0.005, k=3)
    # prefer reconstructed parent; file as sanity
    parent_file_r = _returns(parent_file).reindex(panel.index).fillna(0.0)

    # --- residual census (DIAG) ---
    drag = parent_r - live_r
    years = pd.Series(panel.index.year, index=panel.index)
    census_years = {}
    all_eps = []
    for y in TARGET_YEARS:
        m = years == y
        dm = (m & (drag < 0)).to_numpy()
        eps = _episodes(dm, panel.index, drag)
        all_eps.extend(eps)
        drag_m = m & (drag < 0)
        help_m = m & (drag > 0)

        def feat(mask: pd.Series) -> dict:
            if int(mask.sum()) == 0:
                return {"n_days": 0}
            return {
                "n_days": int(mask.sum()),
                "pct_sat": round(float(sat_lead[mask].mean()) * 100, 2),
                "pct_risk_on": round(float(risk_on[mask].mean()) * 100, 2),
                "pct_defend": round(float(defending[mask].mean()) * 100, 2),
                "mean_dd63": round(float(dd63[mask].mean()), 4),
                "mean_trail": round(float(trail[mask].mean()), 4),
                "sum_delta_pp": round(float(drag[mask].sum()) * 100, 4),
            }

        census_years[str(y)] = {
            "sum_delta_pp": round(float(drag[m].sum()) * 100, 4),
            "drag": feat(drag_m),
            "help": feat(help_m),
            "top_episodes": sorted(eps, key=lambda e: e["sum_delta_pp"])[:6],
        }
    census = {
        "target_years": list(TARGET_YEARS),
        "years": census_years,
        "top_episodes_all": sorted(all_eps, key=lambda e: e["sum_delta_pp"])[:15],
        "note": (
            "2013/2019 drag: higher sat + risk_on; short chops. "
            "2020 drag: low sat + more defend/off-peak. Gates below are causal, not year-labeled."
        ),
    }
    (OUT / "residual_episode_census.json").write_text(
        json.dumps(census, indent=2) + "\n", encoding="utf-8"
    )
    pd.DataFrame(all_eps).to_csv(OUT / "residual_episodes.csv", index=False)

    base_w = _pack(nav_l3)
    parent_nav = _nav_from_returns(parent_r, nav0)
    s3_nav = _nav_from_returns(s3_r, nav0)
    parent_w = _pack(parent_nav)
    nav_l3.to_csv(OUT / f"nav_{BASE_ID}.csv", index=False)
    parent_nav.to_csv(OUT / f"nav_{PARENT_ID}.csv", index=False)
    s3_nav.to_csv(OUT / f"nav_{CHAMP0_ID}.csv", index=False)

    parent_yg = _year_table(parent_r, live_r, near_r, p34_r)
    live_yg = _year_table(live_r, live_r, near_r, p34_r)
    pd.DataFrame(parent_yg["years"]).to_csv(OUT / "year_oracle_parent.csv", index=False)

    # focused force masks (causal)
    lead10 = (_trail_sum(live_r, 10) - _trail_sum(parent_r, 10)).fillna(0.0)
    lead21 = (_trail_sum(live_r, 21) - _trail_sum(parent_r, 21)).fillna(0.0)
    lead5 = (_trail_sum(live_r, 5) - _trail_sum(parent_r, 5)).fillna(0.0)
    # stack intent proxy: parent differs from live (using lag parent==champ days via prem exposure)
    # Use nearpeak3 as stack-desire proxy for overlay
    stackish = nearpeak3.to_numpy(dtype=bool)

    arms: dict[str, tuple[str, pd.Series]] = {
        "REF_LIVE": ("REF", live_r),
        "REF_PARENT_0kb2": ("REF", parent_r),
        "REF_S3SAT_0kb1": ("REF", s3_r),
        "REF_PARENT_FILE": ("REF", parent_file_r),
    }

    # A) short live-lead + sat (2013/2019 shape)
    for w, lead in ((5, lead5), (10, lead10), (21, lead21)):
        for margin in (0.0, 0.002, 0.005):
            for k in (1, 2, 3):
                conf = lead > float(margin)
                for j in range(1, k):
                    conf = conf & (lead.shift(j).fillna(0.0) > float(margin))
                force = (conf & sat_lead).to_numpy(dtype=bool)
                for sticky in (0, 3, 5, 8):
                    if sticky > 0 and k == 1 and margin == 0.0 and w != 10:
                        continue  # keep grid tight
                    name = f"SHORT_SAT_W{w}_M{str(margin).replace('.', '')}_K{k}_ST{sticky}"
                    arms[name] = (
                        "SHORT_SAT",
                        _apply_force_live(parent_r, live_r, force, sticky=sticky),
                    )

    # B) defend / off-peak force live while stackish (2020 shape)
    for shape, mask in (
        ("DEFEND", defending.to_numpy(dtype=bool)),
        ("OFFPEAK3", offpeak3.to_numpy(dtype=bool)),
        ("OFFPEAK5", offpeak5.to_numpy(dtype=bool)),
        ("DEFEND_or_OFF3", (defending | offpeak3).to_numpy(dtype=bool)),
        ("DEFEND_and_STACK", (defending & nearpeak3).to_numpy(dtype=bool)),
        ("OFF3_and_STACK", (offpeak3 & nearpeak3).to_numpy(dtype=bool)),
    ):
        for sticky in (0, 5, 8, 13):
            arms[f"SHAPE_{shape}_ST{sticky}"] = (
                "SHAPE20",
                _apply_force_live(parent_r, live_r, mask, sticky=sticky),
            )

    # C) combo: short-sat OR defend shape
    for w, margin, k in ((10, 0.002, 2), (10, 0.005, 2), (21, 0.002, 2), (5, 0.0, 2)):
        lead = {5: lead5, 10: lead10, 21: lead21}[w]
        conf = lead > float(margin)
        for j in range(1, k):
            conf = conf & (lead.shift(j).fillna(0.0) > float(margin))
        force = (conf & sat_lead).to_numpy(dtype=bool) | defending.to_numpy(dtype=bool)
        for sticky in (0, 5, 8):
            arms[f"COMBO_SHORTSAT_or_DEF_W{w}_M{str(margin).replace('.', '')}_K{k}_ST{sticky}"] = (
                "COMBO",
                _apply_force_live(parent_r, live_r, force, sticky=sticky),
            )

    # D) soft shrink stack prem when short lead (not hard live)
    parent_prem = parent_r - live_r
    for w, lead in ((10, lead10), (21, lead21)):
        for scale in (20.0, 50.0):
            # alpha=1 when champ leads; →0 when live leads
            edge = (-lead).fillna(0.0)  # positive when parent ahead
            alpha = (0.5 + scale * edge).clip(0.0, 1.0)
            arms[f"SOFTSHRINK_W{w}_S{int(scale)}"] = (
                "SOFT",
                live_r + alpha * parent_prem,
            )

    # Oracle DIAG: in target years pick live else parent — FORBIDDEN promote
    ymask = years.isin(TARGET_YEARS).to_numpy()
    arms["ORACLE_TARGET_LIVE_DIAG"] = (
        "ORACLE",
        pd.Series(np.where(ymask, live_r, parent_r), index=panel.index),
    )

    rows = []
    arms_nav = {BASE_ID: nav_l3, PARENT_ID: parent_nav, CHAMP0_ID: s3_nav}
    for name, (fam, r) in arms.items():
        r = r.reindex(panel.index).fillna(0.0)
        nav = _nav_from_returns(r, nav0)
        arms_nav[name] = nav
        chal_w = _pack(nav)
        d_live = _delta(base_w, chal_w)
        d_par = _delta(parent_w, chal_w)
        tip = _tip(nav_l3, nav)
        yg = _year_table(r, live_r, near_r, p34_r)
        sealed = d_live["sealed_2023_plus"]["mdd_improve_pp"]
        tip_y = (tip.get("ytd") or {}).get("cagr_lift_pp")
        held_live = d_live["heldout_2019_plus"]["cagr_lift_pp"]
        held_par = d_par["heldout_2019_plus"]["cagr_lift_pp"]
        sealed_ok = sealed is not None and float(sealed) >= SEALED_MDD_FLOOR_PP
        tip_ok = tip_y is None or float(tip_y) >= TIP_Y_FLOOR_PP
        live_held_ok = held_live is not None and float(held_live) >= HELD_CAGR_FLOOR_PP
        tgt_improve = (
            yg["target_sum_delta_vs_live_pp"] - parent_yg["target_sum_delta_vs_live_pp"]
        )
        tgt_beats_lift = yg["target_n_beats_live"] - parent_yg["target_n_beats_live"]
        held_pos = held_par is not None and float(held_par) > 0 and sealed_ok and tip_ok
        residual_obj = (
            live_held_ok
            and sealed_ok
            and tip_ok
            and held_par is not None
            and float(held_par) >= HELD_EPS_VS_PARENT
            and (float(tgt_improve) >= 0.15 or tgt_beats_lift >= 1)
        )
        # also require not wrecking global beats/regret badly
        global_ok = (
            yg["n_beats_live"] >= parent_yg["n_beats_live"] - 0
            or (
                yg["gap_to_oracle_pp"] is not None
                and yg["gap_to_oracle_pp"] <= parent_yg["gap_to_oracle_pp"] + 0.05
            )
        )
        strong = bool(held_pos and residual_obj and global_ok)
        rows.append(
            {
                "arm": name,
                "family": fam,
                "verdict_vs_live": _arm_verdict_vs_live(d_live, tip),
                "held_vs_live": held_live,
                "held_vs_parent": held_par,
                "sealed_vs_live": sealed,
                "tipY_vs_live": tip_y,
                "year_gap_to_oracle_pp": yg["gap_to_oracle_pp"],
                "year_regret_improve_vs_parent_pp": None
                if yg["gap_to_oracle_pp"] is None
                else round(parent_yg["gap_to_oracle_pp"] - yg["gap_to_oracle_pp"], 4),
                "year_wins": yg["year_wins"],
                "year_wins_vs_parent": yg["year_wins"] - parent_yg["year_wins"],
                "n_beats_live": yg["n_beats_live"],
                "n_beats_live_vs_parent": yg["n_beats_live"] - parent_yg["n_beats_live"],
                "target_sum_delta_vs_live_pp": yg["target_sum_delta_vs_live_pp"],
                "target_delta_improve_vs_parent_pp": round(float(tgt_improve), 4),
                "target_n_beats_live": yg["target_n_beats_live"],
                "target_beats_lift": int(tgt_beats_lift),
                "held_pos_vs_parent": bool(held_pos),
                "residual_obj_clear": bool(residual_obj),
                "strong_clear": bool(strong),
                "oracle": fam == "ORACLE",
                "is_ref": fam == "REF",
            }
        )

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "arms_live_year_residual.csv", index=False)
    mech = df[(~df.oracle) & (~df.is_ref)].copy()
    hits = mech[mech.strong_clear | mech.held_pos_vs_parent | mech.residual_obj_clear]
    hits.to_csv(OUT / "residual_hits.csv", index=False)
    by_fam = (
        mech.groupby("family")
        .agg(
            n=("arm", "count"),
            n_strong=("strong_clear", "sum"),
            n_held=("held_pos_vs_parent", "sum"),
            n_resid=("residual_obj_clear", "sum"),
            max_held_vs_parent=("held_vs_parent", "max"),
            max_tgt_improve=("target_delta_improve_vs_parent_pp", "max"),
            max_tgt_beats=("target_beats_lift", "max"),
            max_beats_live=("n_beats_live", "max"),
        )
        .reset_index()
    )
    by_fam.to_csv(OUT / "family_summary.csv", index=False)
    ranked = mech.sort_values(
        by=[
            "strong_clear",
            "held_pos_vs_parent",
            "residual_obj_clear",
            "target_beats_lift",
            "target_delta_improve_vs_parent_pp",
            "held_vs_parent",
            "n_beats_live_vs_parent",
            "year_regret_improve_vs_parent_pp",
        ],
        ascending=[False, False, False, False, False, False, False, False],
    )
    top = ranked.head(20)
    top.to_csv(OUT / "top_arms.csv", index=False)

    strong = mech[mech.strong_clear]
    held = mech[mech.held_pos_vs_parent]
    resid = mech[mech.residual_obj_clear]
    # Prefer arms that do not give back global beats_live vs parent
    def _pick(frame: pd.DataFrame) -> pd.Series:
        return frame.sort_values(
            by=[
                "n_beats_live_vs_parent",
                "target_beats_lift",
                "target_delta_improve_vs_parent_pp",
                "held_vs_parent",
                "year_regret_improve_vs_parent_pp",
            ],
            ascending=[False, False, False, False, False],
        ).iloc[0]

    if len(strong):
        crow = _pick(strong)
        verdict = "IP3_LIVE_YEAR_RESIDUAL_HIT"
    elif len(held):
        crow = _pick(held)
        verdict = "IP3_LIVE_YEAR_RESIDUAL_HIT"
    elif len(resid):
        crow = _pick(resid)
        verdict = "IP3_LIVE_YEAR_RESIDUAL_SOFT"
    else:
        verdict = "IP3_LIVE_YEAR_RESIDUAL_NO_EDGE"
        crow = ranked.iloc[0] if len(ranked) else None

    n_strong = int(mech.strong_clear.sum())
    n_held = int(mech.held_pos_vs_parent.sum())
    n_resid = int(mech.residual_obj_clear.sum())
    champ = None if crow is None else crow.to_dict()
    if champ:
        arms_nav[champ["arm"]].to_csv(OUT / f"nav_{champ['arm']}.csv", index=False)
        yg_c = _year_table(_returns(arms_nav[champ["arm"]]), live_r, near_r, p34_r)
        pd.DataFrame(yg_c["years"]).to_csv(OUT / "year_oracle_champion.csv", index=False)

    optimize = [
        "Objective: focused causal overlays on 0kb2 to close residual 2013/2019/2020 live gaps without full re-grid or year-cut",
        (
            f"Champion `{champ['arm']}` fam={champ['family']} held_vs_parent={champ['held_vs_parent']} "
            f"tgtΔimprove={champ['target_delta_improve_vs_parent_pp']} tgt_beats_lift={champ['target_beats_lift']} "
            f"beats_live={champ['n_beats_live']} sealed={champ['sealed_vs_live']} tipY={champ['tipY_vs_live']}"
            if champ
            else "No champion"
        ),
        f"Clears: strong={n_strong} · held+={n_held} · residual_obj={n_resid} / mech={len(mech)}",
        f"Parent target sumΔlive={parent_yg['target_sum_delta_vs_live_pp']} · tgt_beats={parent_yg['target_n_beats_live']} · beats_live={parent_yg['n_beats_live']}",
        f"Census: { {y: census_years[str(y)]['sum_delta_pp'] for y in TARGET_YEARS} }",
        "If HIT → draft observe; SOFT → note; NO_EDGE → KEEP 0kb2 DRAFT",
        "Soft KEEP · Path4 live OFF · no year-cut · no hybrid T+0",
    ]
    screen = {
        "id": SCREEN_ID,
        "register": REGISTER,
        "parents": list(PARENTS),
        "generated_at_utc": generated,
        "mech": MECH,
        "verdict": verdict,
        "n_mech_screened": len(mech),
        "n_strong_clear": n_strong,
        "n_held_pos_vs_parent": n_held,
        "n_residual_obj_clear": n_resid,
        "parent": {
            "arm": "OVERRIDE_LIVE_W42_M0005_K3",
            "target_sum_delta_vs_live_pp": parent_yg["target_sum_delta_vs_live_pp"],
            "target_n_beats_live": parent_yg["target_n_beats_live"],
            "n_beats_live": parent_yg["n_beats_live"],
            "gap_to_oracle_pp": parent_yg["gap_to_oracle_pp"],
        },
        "census_summary": {
            "target_years": list(TARGET_YEARS),
            "year_sum_delta": {y: census_years[str(y)]["sum_delta_pp"] for y in TARGET_YEARS},
            "note": census["note"],
        },
        "family_summary": by_fam.to_dict(orient="records"),
        "champion": champ,
        "top_arms": top.to_dict(orient="records"),
        "optimize_live": optimize,
        "soft_keep": True,
        "path4_live": False,
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
            "Can focused causal overlays (short sat-chop live-lead / defend-offpeak force-LIVE / sticky) "
            "on frozen 0kb2 close residual **2013 / 2019 / 2020** live gaps without re-scanning the "
            "full race grid or using year dummies?",
            "",
            "## Design",
            "",
            "- Parent: 0kb2 `OVERRIDE_LIVE_W42_M0005_K3`",
            "- DIAG census of residual drag episodes → feature-shaped gates only",
            "- Families: SHORT_SAT · SHAPE20 · COMBO · SOFT",
            "- Success: held+ vs parent, or residual_obj (target-year Δlive improve ≥0.15pp or +1 target beat) with floors",
            "- Forbidden: year-cut · lookahead · hybrid T+0 · Path4 live · full 0kb2 re-grid",
            "",
            f"Label: `{CHARTER_ID}_{generated[:10]}`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{CHARTER_ID}.md", REP / f"{CHARTER_ID}.md", charter_md, kind="charter"
    )
    (OPS / f"{CHARTER_ID}.json").write_text(
        json.dumps(
            {
                "id": CHARTER_ID,
                "register": REGISTER,
                "parents": list(PARENTS),
                "mech": MECH,
                "date": generated[:10],
                "target_years": list(TARGET_YEARS),
                "forbidden": [
                    "year_cut",
                    "lookahead_promote",
                    "hybrid_t0",
                    "path4_live",
                    "full_0kb2_regrid",
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    write_repro_pointer(OPS / f"{CHARTER_ID}.json", REP / f"{CHARTER_ID}.json", kind="charter")

    screen_md = [
        f"# {SCREEN_ID}",
        "",
        f"Date: {generated[:10]} · Verdict: **`{verdict}`** · champion=**`{(champ or {}).get('arm')}`**",
        f"Register: **{REGISTER}** · mech={len(mech)} · strong={n_strong} · held+={n_held} · resid={n_resid}",
        "",
        "## Residual census (DIAG)",
        "",
        f"- target years `{TARGET_YEARS}` parent sumΔlive **{parent_yg['target_sum_delta_vs_live_pp']}**",
        *[
            f"- {y}: sumΔ **{census_years[str(y)]['sum_delta_pp']}** · drag `{census_years[str(y)]['drag']}`"
            for y in TARGET_YEARS
        ],
        f"- note: {census['note']}",
        "",
        "## Family summary",
        "",
        "| Family | n | strong | resid | held+ | maxΔparent | max tgtΔ↑ | max tgt beats↑ | max beatsL |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in by_fam.to_dict(orient="records"):
        screen_md.append(
            f"| {r['family']} | {r['n']} | {int(r['n_strong'])} | {int(r['n_resid'])} | "
            f"{int(r['n_held'])} | {r['max_held_vs_parent']} | {r['max_tgt_improve']} | "
            f"{int(r['max_tgt_beats'])} | {int(r['max_beats_live'])} |"
        )
    screen_md += [
        "",
        "## Top arms",
        "",
        "| Arm | fam | heldΔparent | tgtΔ↑ | tgt beats↑ | beatsLΔ | sealed | tipY | vs live |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for r in top.to_dict(orient="records"):
        screen_md.append(
            f"| {r['arm']} | {r['family']} | {r['held_vs_parent']} | "
            f"{r['target_delta_improve_vs_parent_pp']} | {r['target_beats_lift']} | "
            f"{r['n_beats_live_vs_parent']} | {r['sealed_vs_live']} | {r['tipY_vs_live']} | "
            f"{r['verdict_vs_live']} |"
        )
    screen_md += [
        "",
        "## Optimize / disposition",
        "",
        *[f"{i}. {line}" for i, line in enumerate(optimize, 1)],
        "",
        "Repro: `PYTHONPATH=scripts python3 scripts/tipsoft_ip3_live_year_residual_stagea.py`",
        "",
        f"Label: `{screen['label']}`",
        "",
    ]
    write_ops_and_repro_pointer(
        OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", "\n".join(screen_md), kind="screen"
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
                f"- held vs 0kb2 parent: **{(champ or {}).get('held_vs_parent')}**\n"
                f"- target(2013/19/20) Δlive improve: **{(champ or {}).get('target_delta_improve_vs_parent_pp')}**\n"
                f"- target beats_live lift: **{(champ or {}).get('target_beats_lift')}**\n"
                f"- global beats_live: **{(champ or {}).get('n_beats_live')}** "
                f"(Δ **{(champ or {}).get('n_beats_live_vs_parent')}**)\n"
                f"- sealed **{(champ or {}).get('sealed_vs_live')}** · tipY **{(champ or {}).get('tipY_vs_live')}**\n"
                f"- clears: strong **{n_strong}** · held+ **{n_held}** · resid **{n_resid}** / {len(mech)}"
                if champ
                else f"- No clear · mech={len(mech)}"
            ),
            "",
            "## Disposition",
            "",
            "- Promote observe only on `IP3_LIVE_YEAR_RESIDUAL_HIT`",
            "- `IP3_LIVE_YEAR_RESIDUAL_SOFT` → note · KEEP 0kb2 DRAFT",
            "- `IP3_LIVE_YEAR_RESIDUAL_NO_EDGE` → KEEP 0kb2 · Soft KEEP · Path4 OFF",
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
    (OPS / f"{DECISION_ID}.json").write_text(
        json.dumps(
            {
                "id": DECISION_ID,
                "register": REGISTER,
                "parents": list(PARENTS),
                "verdict": verdict,
                "champion": champ,
                "n_strong_clear": n_strong,
                "n_held_pos_vs_parent": n_held,
                "n_residual_obj_clear": n_resid,
                "soft_keep": True,
                "path4_live": False,
                "label": f"{DECISION_ID}_{generated[:10]}__{verdict}__NO_LIVE",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    write_repro_pointer(
        OPS / f"{DECISION_ID}.json", REP / f"{DECISION_ID}.json", kind="decision pack"
    )

    print(
        json.dumps(
            {
                "verdict": verdict,
                "champion": None if not champ else champ["arm"],
                "family": None if not champ else champ["family"],
                "held_vs_parent": None if not champ else champ["held_vs_parent"],
                "target_delta_improve_vs_parent_pp": None
                if not champ
                else champ["target_delta_improve_vs_parent_pp"],
                "target_beats_lift": None if not champ else champ["target_beats_lift"],
                "n_beats_live": None if not champ else champ["n_beats_live"],
                "n_strong": n_strong,
                "n_held": n_held,
                "n_resid": n_resid,
                "n_mech": len(mech),
                "parent_target_sum_delta": parent_yg["target_sum_delta_vs_live_pp"],
                "census_year_deltas": {
                    y: census_years[str(y)]["sum_delta_pp"] for y in TARGET_YEARS
                },
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
