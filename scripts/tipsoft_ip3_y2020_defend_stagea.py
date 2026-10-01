#!/usr/bin/env python3
"""2020-only defend/off-peak knife Stage A (0kb4).

Parent 0kb2 ``OVERRIDE_LIVE_W42_M0005_K3``; 0kb3 SHORT_SAT closed 2013/19 a bit but
**2020 untouched** (defend/off-peak, not sat). This pack:

- Does **not** re-scan SHORT_SAT / full race grids
- Only COOL-defend / dd63 off-peak / proxy / FUSE-prem shaped force-LIVE or soft-α
- Success focused on 2020 Δlive + global floors vs 0kb2
- Stop-gate: if no held+ and cannot flip 2020 to beat live → freeze 0kb2 observe line

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
REPRO = ROOT / "repro" / "tipsoft-ip3-y2020-defend-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

LIVESTACK = ROOT / "repro" / "fin-sat-path3-path4-livestack-twin-stageb" / "outputs"
ALIGN = ROOT / "repro" / "research-live-align-gap-stagea" / "outputs"
P3_SIG = (
    ROOT / "repro" / "fin-sat-path3-t0-dual-paper-observe" / "outputs" / "p3_t0_state_signal.csv"
)

CHARTER_ID = "TIPSOFT_IP3_Y2020_DEFEND_STAGEA_CHARTER"
SCREEN_ID = "TIPSOFT_IP3_Y2020_DEFEND_STAGEA_SCREEN"
DECISION_ID = "TIPSOFT_IP3_Y2020_DEFEND_STAGEA_DECISION_PACK"
REGISTER = "0kb4"
PARENTS = ("0kb3", "0kb2", "0kb1")
MECH = "TIPSOFT_IP3_Y2020_DEFEND"

BASE_ID = "BASE_LIVE_FUSE_COOL"
PARENT_ID = "REF_OVERRIDE_W42_M05_K3"
SEALED_MDD_FLOOR_PP = -0.25
TIP_Y_FLOOR_PP = -1.0
HELD_CAGR_FLOOR_PP = 0.10
P3_THETA = 0.005
HELD_EPS_VS_PARENT = -0.05
TARGET_YEAR = 2020


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
    wins = beats = 0
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
                "is_2020": y == TARGET_YEAR,
                "beats_live": bool(pol_v > live_v + 1e-9),
                "policy_wins": bool(pol_v >= oracle - 1e-6),
            }
        )
    y20 = next(r for r in rows if r["year"] == TARGET_YEAR)
    mean_pol = float(np.mean([r["policy"] for r in rows]))
    mean_ora = float(np.mean([r["oracle"] for r in rows]))
    return {
        "mean_policy": round(mean_pol, 4),
        "mean_oracle": round(mean_ora, 4),
        "gap_to_oracle_pp": round(mean_ora - mean_pol, 4),
        "year_wins": wins,
        "n_beats_live": beats,
        "n_years": len(rows),
        "y2020_delta_vs_live_pp": y20["delta_vs_live"],
        "y2020_beats_live": y20["beats_live"],
        "y2020_policy": y20["policy"],
        "y2020_live": y20["live"],
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


def _force_live(base_r, live_r, force: np.ndarray, sticky: int = 0) -> pd.Series:
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


def _soft_alpha(base_r, live_r, force: np.ndarray, alpha: float) -> pd.Series:
    """On force days: live + alpha*(base-live); else base."""
    prem = base_r - live_r
    a = np.where(force, float(alpha), 1.0)
    return live_r + pd.Series(a, index=base_r.index) * prem


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()

    nav_l3 = _load_nav(LIVESTACK / "nav_BASE_LIVE_FUSE_COOL.csv")
    nav_p3 = _load_nav(LIVESTACK / "nav_LIVE_P3_WITHIN.csv")
    soft_l1 = _load_nav(ALIGN / "nav_L1_SOFT_T1.csv")
    soft_fuse = _load_nav(ALIGN / "nav_L2_SOFT_FUSE_T1.csv")
    p4_book = _load_nav(LIVESTACK / "nav_LIVE_P3_P4_CASH_001.csv")
    nav0 = float(nav_l3["nav"].iloc[0])

    panel = pd.concat(
        {
            "r3": _returns(nav_l3),
            "rp3": _returns(nav_p3),
            "rp4": _returns(p4_book),
            "r1": _returns(soft_l1),
            "r2": _returns(soft_fuse),
        },
        axis=1,
        join="inner",
    ).dropna(how="any")
    live_r = panel["r3"]
    prem_p3 = panel["rp3"] - panel["r3"]
    prem_p4 = panel["rp4"] - panel["rp3"]
    prem_fuse = panel["r2"] - panel["r1"]

    dd63 = _dd_from_peak(soft_l1, 63).reindex(panel.index).fillna(0.0)
    proxy = _proxy_mdd63(soft_l1).reindex(panel.index).fillna(0.0)
    cool_exp = build_cool_c8_exposure(panel.index, proxy)
    risk_on = cool_exp >= 0.999
    defending = ~risk_on

    sig = pd.read_csv(P3_SIG, parse_dates=["date"])
    sig["date"] = pd.to_datetime(sig["date"]).dt.normalize()
    sig = sig.set_index("date").reindex(panel.index)
    sat_lead = sig["sat_lead"].fillna(False).astype(bool)
    trail = sig["trail_rel_63"].astype(float)
    p3_theta = (trail.abs() >= float(P3_THETA)).fillna(False)
    nearpeak3 = p3_theta & (dd63 >= -0.03)

    near_r = live_r + nearpeak3.astype(float) * prem_p3
    p34_r = (
        live_r
        + nearpeak3.astype(float) * prem_p3
        + (nearpeak3 & sat_lead).astype(float) * prem_p4
    )

    i3, i4 = _three_state_mute_sat(nearpeak3, sat_lead, prem_p3)
    s3_r = live_r + i3 * prem_p3 + i4 * prem_p4
    parent_r = _override_live_confirm(live_r, s3_r, w=42, margin=0.005, k=3)

    # FUSE / defend features (causal)
    fuse_trail5 = _trail_sum(prem_fuse, 5).fillna(0.0)
    fuse_trail21 = _trail_sum(prem_fuse, 21).fillna(0.0)
    fuse_pos = fuse_trail5 > 0  # recent FUSE premium positive (SELL_a75 bite)
    fuse_neg = fuse_trail5 < 0
    proxy08 = proxy <= -0.08
    proxy05 = proxy <= -0.05
    off3 = dd63 < -0.03
    off5 = dd63 < -0.05
    off2 = dd63 < -0.02
    # stack-on proxy: parent != live recently — use nearpeak3 or |parent-live|>eps lag
    stack_on = (parent_r.shift(1) - live_r.shift(1)).abs().fillna(0.0) > 1e-12
    stack_on = stack_on | nearpeak3

    # 2020 episode census DIAG
    years = pd.Series(panel.index.year, index=panel.index)
    m20 = years == TARGET_YEAR
    drag = parent_r - live_r
    drag20 = m20 & (drag < 0)
    help20 = m20 & (drag > 0)

    def feat(mask: pd.Series) -> dict:
        if int(mask.sum()) == 0:
            return {"n_days": 0}
        return {
            "n_days": int(mask.sum()),
            "pct_defend": round(float(defending[mask].mean()) * 100, 2),
            "pct_off3": round(float(off3[mask].mean()) * 100, 2),
            "pct_off5": round(float(off5[mask].mean()) * 100, 2),
            "pct_proxy08": round(float(proxy08[mask].mean()) * 100, 2),
            "pct_fuse_pos5": round(float(fuse_pos[mask].mean()) * 100, 2),
            "pct_sat": round(float(sat_lead[mask].mean()) * 100, 2),
            "mean_dd63": round(float(dd63[mask].mean()), 4),
            "sum_delta_pp": round(float(drag[mask].sum()) * 100, 4),
        }

    census = {
        "target_year": TARGET_YEAR,
        "parent_y2020_delta_vs_live_pp": round(float(drag[m20].sum()) * 100, 4),
        "drag_2020": feat(drag20),
        "help_2020": feat(help20),
        "note": "2020 drag: defend/off-peak/proxy heavy, sat low — knife uses those only (no SHORT_SAT).",
    }
    (OUT / "y2020_defend_census.json").write_text(
        json.dumps(census, indent=2) + "\n", encoding="utf-8"
    )

    base_w = _pack(nav_l3)
    parent_nav = _nav_from_returns(parent_r, nav0)
    parent_w = _pack(parent_nav)
    nav_l3.to_csv(OUT / f"nav_{BASE_ID}.csv", index=False)
    parent_nav.to_csv(OUT / f"nav_{PARENT_ID}.csv", index=False)
    parent_yg = _year_table(parent_r, live_r, near_r, p34_r)
    pd.DataFrame(parent_yg["years"]).to_csv(OUT / "year_oracle_parent.csv", index=False)

    arms: dict[str, tuple[str, pd.Series]] = {
        "REF_LIVE": ("REF", live_r),
        "REF_PARENT_0kb2": ("REF", parent_r),
        "REF_S3SAT_0kb1": ("REF", s3_r),
    }

    shapes: dict[str, np.ndarray] = {
        "DEFEND": defending.to_numpy(dtype=bool),
        "OFF3": off3.to_numpy(dtype=bool),
        "OFF5": off5.to_numpy(dtype=bool),
        "OFF2": off2.to_numpy(dtype=bool),
        "PROXY08": proxy08.to_numpy(dtype=bool),
        "PROXY05": proxy05.to_numpy(dtype=bool),
        "DEFEND_or_OFF3": (defending | off3).to_numpy(dtype=bool),
        "DEFEND_or_OFF5": (defending | off5).to_numpy(dtype=bool),
        "DEFEND_and_OFF3": (defending & off3).to_numpy(dtype=bool),
        "DEFEND_or_PROXY08": (defending | proxy08).to_numpy(dtype=bool),
        "FUSEPOS5": fuse_pos.to_numpy(dtype=bool),
        "FUSENEG5": fuse_neg.to_numpy(dtype=bool),
        "DEFEND_or_FUSEPOS": (defending | fuse_pos).to_numpy(dtype=bool),
        "OFF3_or_FUSEPOS": (off3 | fuse_pos).to_numpy(dtype=bool),
        "DEFEND_and_STACK": (defending & stack_on).to_numpy(dtype=bool),
        "OFF3_and_STACK": (off3 & stack_on).to_numpy(dtype=bool),
        "PROXY08_and_STACK": (proxy08 & stack_on).to_numpy(dtype=bool),
        "DEFEND_or_OFF3_and_STACK": ((defending | off3) & stack_on).to_numpy(dtype=bool),
    }

    for sname, mask in shapes.items():
        for sticky in (0, 5, 8, 13, 21):
            # keep sticky light on broad masks
            if sticky > 8 and sname in ("OFF2", "FUSEPOS5", "FUSENEG5"):
                continue
            arms[f"HARD_{sname}_ST{sticky}"] = (
                "HARD",
                _force_live(parent_r, live_r, mask, sticky=sticky),
            )
        for a in (0.0, 0.25, 0.5):
            arms[f"SOFT_{sname}_A{str(a).replace('.', '')}"] = (
                "SOFT",
                _soft_alpha(parent_r, live_r, mask, alpha=a),
            )

    # Confirm defend for K days before force
    for k in (2, 3, 5):
        conf = defending.copy()
        for j in range(1, k):
            conf = conf & defending.shift(j).fillna(False)
        for sticky in (0, 8, 13):
            arms[f"HARD_DEFEND_CONF_K{k}_ST{sticky}"] = (
                "HARD_CONF",
                _force_live(parent_r, live_r, conf.to_numpy(dtype=bool), sticky=sticky),
            )

    # Oracle DIAG: 2020=live else parent — never promote
    ymask = (years == TARGET_YEAR).to_numpy()
    arms["ORACLE_2020_LIVE_DIAG"] = (
        "ORACLE",
        pd.Series(np.where(ymask, live_r, parent_r), index=panel.index),
    )

    rows = []
    arms_nav = {BASE_ID: nav_l3, PARENT_ID: parent_nav}
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
        y20_imp = yg["y2020_delta_vs_live_pp"] - parent_yg["y2020_delta_vs_live_pp"]
        y20_flip = bool(yg["y2020_beats_live"] and not parent_yg["y2020_beats_live"])
        held_pos = held_par is not None and float(held_par) > 0 and sealed_ok and tip_ok
        y20_obj = (
            live_held_ok
            and sealed_ok
            and tip_ok
            and held_par is not None
            and float(held_par) >= HELD_EPS_VS_PARENT
            and (float(y20_imp) >= 0.15 or y20_flip)
        )
        global_ok = yg["n_beats_live"] >= parent_yg["n_beats_live"]
        strong = bool(held_pos and y20_obj and global_ok)
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
                "year_regret_improve_vs_parent_pp": round(
                    parent_yg["gap_to_oracle_pp"] - yg["gap_to_oracle_pp"], 4
                ),
                "year_wins": yg["year_wins"],
                "n_beats_live": yg["n_beats_live"],
                "n_beats_live_vs_parent": yg["n_beats_live"] - parent_yg["n_beats_live"],
                "y2020_delta_vs_live_pp": yg["y2020_delta_vs_live_pp"],
                "y2020_improve_vs_parent_pp": round(float(y20_imp), 4),
                "y2020_beats_live": bool(yg["y2020_beats_live"]),
                "y2020_flip": bool(y20_flip),
                "held_pos_vs_parent": bool(held_pos),
                "y2020_obj_clear": bool(y20_obj),
                "strong_clear": bool(strong),
                "oracle": fam == "ORACLE",
                "is_ref": fam == "REF",
            }
        )

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "arms_y2020_defend.csv", index=False)
    mech = df[(~df.oracle) & (~df.is_ref)].copy()
    hits = mech[mech.strong_clear | mech.held_pos_vs_parent | mech.y2020_obj_clear]
    hits.to_csv(OUT / "y2020_hits.csv", index=False)
    by_fam = (
        mech.groupby("family")
        .agg(
            n=("arm", "count"),
            n_strong=("strong_clear", "sum"),
            n_held=("held_pos_vs_parent", "sum"),
            n_y20=("y2020_obj_clear", "sum"),
            n_flip=("y2020_flip", "sum"),
            max_held_vs_parent=("held_vs_parent", "max"),
            max_y20_imp=("y2020_improve_vs_parent_pp", "max"),
            max_beats=("n_beats_live", "max"),
        )
        .reset_index()
    )
    by_fam.to_csv(OUT / "family_summary.csv", index=False)
    ranked = mech.sort_values(
        by=[
            "strong_clear",
            "y2020_flip",
            "held_pos_vs_parent",
            "y2020_obj_clear",
            "n_beats_live_vs_parent",
            "y2020_improve_vs_parent_pp",
            "held_vs_parent",
        ],
        ascending=[False, False, False, False, False, False, False],
    )
    top = ranked.head(20)
    top.to_csv(OUT / "top_arms.csv", index=False)

    strong = mech[mech.strong_clear]
    held = mech[mech.held_pos_vs_parent]
    y20 = mech[mech.y2020_obj_clear]
    flips = mech[mech.y2020_flip]

    def _pick(frame: pd.DataFrame) -> pd.Series:
        return frame.sort_values(
            by=[
                "y2020_flip",
                "n_beats_live_vs_parent",
                "y2020_improve_vs_parent_pp",
                "held_vs_parent",
            ],
            ascending=[False, False, False, False],
        ).iloc[0]

    # HIT requires held+ AND a real 2020 win (flip or >=+0.15pp). Disjoint
    # held+/flip sets are NOT a HIT (e.g. OFF3 held+ with y20_imp=0, or FUSE
    # flip with held << 0).
    held_y20 = held[
        held.y2020_flip | (held.y2020_improve_vs_parent_pp >= 0.15)
    ]
    if len(strong):
        crow = _pick(strong)
        verdict = "IP3_Y2020_DEFEND_HIT"
    elif len(held_y20):
        crow = _pick(held_y20)
        verdict = "IP3_Y2020_DEFEND_HIT"
    elif len(y20):
        crow = _pick(y20)
        verdict = "IP3_Y2020_DEFEND_SOFT"
    else:
        verdict = "IP3_Y2020_DEFEND_NO_EDGE"
        # Prefer near-miss that actually moves 2020 (for report), else vacuous held+
        near = mech[
            (mech.y2020_flip | (mech.y2020_improve_vs_parent_pp >= 0.15))
            & (mech.held_vs_parent >= HELD_EPS_VS_PARENT)
        ]
        if len(near):
            crow = _pick(near)
        elif len(flips):
            crow = _pick(flips)
        elif len(held):
            crow = _pick(held)
        else:
            crow = ranked.iloc[0] if len(ranked) else None

    # Stop-gate: no held+ that improves 2020, no y20_obj clear → freeze 0kb2
    n_strong = int(mech.strong_clear.sum())
    n_held = int(mech.held_pos_vs_parent.sum())
    n_held_y20 = int(len(held_y20))
    n_y20 = int(mech.y2020_obj_clear.sum())
    n_flip = int(mech.y2020_flip.sum())
    stop_freeze_0kb2 = (n_strong == 0) and (n_held_y20 == 0) and (n_y20 == 0)

    champ = None if crow is None else crow.to_dict()
    if champ:
        arms_nav[champ["arm"]].to_csv(OUT / f"nav_{champ['arm']}.csv", index=False)
        yg_c = _year_table(_returns(arms_nav[champ["arm"]]), live_r, near_r, p34_r)
        pd.DataFrame(yg_c["years"]).to_csv(OUT / "year_oracle_champion.csv", index=False)

    optimize = [
        "Objective: 2020 defend/off-peak/FUSE-shaped force-LIVE or soft-α on 0kb2; flip or cut 2020 live gap; no SHORT_SAT re-grid",
        (
            f"Champion `{champ['arm']}` fam={champ['family']} held_vs_parent={champ['held_vs_parent']} "
            f"y2020_imp={champ['y2020_improve_vs_parent_pp']} flip={champ['y2020_flip']} "
            f"beats_live={champ['n_beats_live']} sealed={champ['sealed_vs_live']} tipY={champ['tipY_vs_live']}"
            if champ
            else "No champion"
        ),
        f"Clears: strong={n_strong} · held+={n_held} · held+∧y20={n_held_y20} · "
        f"y2020_obj={n_y20} · flips={n_flip} / mech={len(mech)}",
        f"Parent y2020 Δlive={parent_yg['y2020_delta_vs_live_pp']} beats_live={parent_yg['n_beats_live']}",
        f"Census drag2020={census['drag_2020']}",
        (
            "STOP_GATE: freeze 0kb2 as observe mainline — no more residual paper stacks"
            if stop_freeze_0kb2
            else "If HIT → draft observe refine; else evaluate feature-swap only after STOP"
        ),
        "Soft KEEP · Path4 live OFF · no year-cut · no hybrid T+0 · OPEN observe is human-only",
    ]
    screen = {
        "id": SCREEN_ID,
        "register": REGISTER,
        "parents": list(PARENTS),
        "generated_at_utc": generated,
        "mech": MECH,
        "verdict": verdict,
        "stop_freeze_0kb2_observe_mainline": bool(stop_freeze_0kb2),
        "n_mech_screened": len(mech),
        "n_strong_clear": n_strong,
        "n_held_pos_vs_parent": n_held,
        "n_held_pos_and_y2020": n_held_y20,
        "n_y2020_obj_clear": n_y20,
        "n_y2020_flip": n_flip,
        "parent": {
            "arm": "OVERRIDE_LIVE_W42_M0005_K3",
            "y2020_delta_vs_live_pp": parent_yg["y2020_delta_vs_live_pp"],
            "n_beats_live": parent_yg["n_beats_live"],
            "gap_to_oracle_pp": parent_yg["gap_to_oracle_pp"],
        },
        "census": census,
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
            "Can **COOL-defend / dd63 off-peak / proxy / FUSE-prem** force-LIVE or soft-α "
            "on frozen 0kb2 close the **2020** live gap (flip or ≥+0.15pp) without SHORT_SAT "
            "re-grids or year dummies?",
            "",
            "## Stop-gate",
            "",
            "If no held+ that also improves/flips 2020 (held+∧y20=0) → **freeze 0kb2** as "
            "observe mainline; no further residual paper stacks (feature-swap only if human wants).",
            "",
            "## Design",
            "",
            "- Parent: 0kb2 `OVERRIDE_LIVE_W42_M0005_K3`",
            "- Families: HARD / SOFT / HARD_CONF on defend·offpeak·proxy·fuse shapes",
            "- Forbidden: year-cut · SHORT_SAT re-grid · hybrid T+0 · Path4 live",
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
                "target_year": TARGET_YEAR,
                "forbidden": [
                    "year_cut",
                    "short_sat_regrid",
                    "hybrid_t0",
                    "path4_live",
                    "lookahead_promote",
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
        f"Register: **{REGISTER}** · mech={len(mech)} · strong={n_strong} · held+={n_held} · "
        f"held+∧y20={n_held_y20} · y20_obj={n_y20} · flip={n_flip} · "
        f"**stop_freeze_0kb2={stop_freeze_0kb2}**",
        "",
        "## 2020 census (DIAG)",
        "",
        f"- parent y2020 Δlive **{parent_yg['y2020_delta_vs_live_pp']}**",
        f"- drag `{census['drag_2020']}`",
        f"- help `{census['help_2020']}`",
        f"- {census['note']}",
        "",
        "## Family summary",
        "",
        "| Family | n | strong | y20_obj | flip | held+ | maxΔparent | max y20↑ | max beatsL |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in by_fam.to_dict(orient="records"):
        screen_md.append(
            f"| {r['family']} | {r['n']} | {int(r['n_strong'])} | {int(r['n_y20'])} | "
            f"{int(r['n_flip'])} | {int(r['n_held'])} | {r['max_held_vs_parent']} | "
            f"{r['max_y20_imp']} | {int(r['max_beats'])} |"
        )
    screen_md += [
        "",
        "## Top arms",
        "",
        "| Arm | fam | heldΔparent | y2020↑ | flip | beatsLΔ | sealed | tipY | vs live |",
        "|---|---|---:|---:|---|---:|---:|---:|---|",
    ]
    for r in top.to_dict(orient="records"):
        screen_md.append(
            f"| {r['arm']} | {r['family']} | {r['held_vs_parent']} | "
            f"{r['y2020_improve_vs_parent_pp']} | {r['y2020_flip']} | "
            f"{r['n_beats_live_vs_parent']} | {r['sealed_vs_live']} | {r['tipY_vs_live']} | "
            f"{r['verdict_vs_live']} |"
        )
    screen_md += [
        "",
        "## Optimize / disposition",
        "",
        *[f"{i}. {line}" for i, line in enumerate(optimize, 1)],
        "",
        "Repro: `PYTHONPATH=scripts python3 scripts/tipsoft_ip3_y2020_defend_stagea.py`",
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
                f"- held vs 0kb2: **{(champ or {}).get('held_vs_parent')}**\n"
                f"- 2020 Δlive improve: **{(champ or {}).get('y2020_improve_vs_parent_pp')}** · "
                f"flip **{(champ or {}).get('y2020_flip')}**\n"
                f"- beats_live: **{(champ or {}).get('n_beats_live')}** "
                f"(Δ **{(champ or {}).get('n_beats_live_vs_parent')}**)\n"
                f"- sealed **{(champ or {}).get('sealed_vs_live')}** · tipY **{(champ or {}).get('tipY_vs_live')}**\n"
                f"- clears: strong **{n_strong}** · held+ **{n_held}** · held+∧y20 **{n_held_y20}** · "
                f"y20_obj **{n_y20}** · flip **{n_flip}**\n"
                f"- **stop_freeze_0kb2_observe_mainline: {stop_freeze_0kb2}**"
                if champ
                else f"- No clear · stop_freeze={stop_freeze_0kb2}"
            ),
            "",
            "## Disposition",
            "",
            "- Promote refine observe only on `IP3_Y2020_DEFEND_HIT`",
            "- `IP3_Y2020_DEFEND_SOFT` → note",
            "- `IP3_Y2020_DEFEND_NO_EDGE` or stop_freeze → **KEEP/OPEN 0kb2** as observe mainline; "
            "no more residual paper stacks",
            "- Soft KEEP · Path4 live OFF · OPEN is human-only",
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
                "stop_freeze_0kb2_observe_mainline": bool(stop_freeze_0kb2),
                "n_strong_clear": n_strong,
                "n_held_pos_vs_parent": n_held,
                "n_held_pos_and_y2020": n_held_y20,
                "n_y2020_obj_clear": n_y20,
                "n_y2020_flip": n_flip,
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
                "y2020_improve_vs_parent_pp": None
                if not champ
                else champ["y2020_improve_vs_parent_pp"],
                "y2020_flip": None if not champ else champ["y2020_flip"],
                "n_beats_live": None if not champ else champ["n_beats_live"],
                "n_strong": n_strong,
                "n_held": n_held,
                "n_held_y20": n_held_y20,
                "n_y20": n_y20,
                "n_flip": n_flip,
                "n_mech": len(mech),
                "stop_freeze_0kb2_observe_mainline": bool(stop_freeze_0kb2),
                "parent_y2020_delta": parent_yg["y2020_delta_vs_live_pp"],
                "census_drag": census["drag_2020"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
