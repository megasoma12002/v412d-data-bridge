#!/usr/bin/env python3
"""Tip Soft Exact T+1 NEARPEAK3 × Path4 stack Stage A (0kax).

Question: on the live Soft+FUSE+COOL Exact T+1 shell, with Path3 already
gated by ``P3_THETA_NEARPEAK3`` (0kaw observe), can Path4 CASH_ETF premium
be detector-stacked without breaking sealed MDD / tip gates?

Method (Exact T+1 only — hybrid T+0 carve FORBIDDEN):
  r = r_L3
    + I_p3 * (r_LIVE_P3 − r_L3)
    + I_p4 * (r_LIVE_P3P4_CASH_00025 − r_LIVE_P3)

I_p3 default = NEARPEAK3 (|trail|≥θ ∧ Soft within 3% of 63d peak).
I_p4 screened under always / same-as-P3 / tighter peak / risk-on / defend.

Score vs ``BASE_LIVE_FUSE_COOL``; also report delta vs NEARPEAK3-only.

Soft KEEP · Path4 live OFF · broker false · no wire.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from cool_c8_proxy_observe_helpers import PROXY_X, build_cool_c8_exposure
from e45_paper_harness import WINDOWS_STANDARD, window_stats
from fin_sell_quality_helpers import cagr_lift_pp
from ops_repro_ssot import write_ops_and_repro_pointer, write_repro_pointer
from research_metric_helpers import mdd_delta_pp

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "tipsoft-nearpeak3-path4-stack-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

LIVESTACK = ROOT / "repro" / "fin-sat-path3-path4-livestack-twin-stageb" / "outputs"
ALIGN = ROOT / "repro" / "research-live-align-gap-stagea" / "outputs"
P3_SIG = (
    ROOT / "repro" / "fin-sat-path3-t0-dual-paper-observe" / "outputs" / "p3_t0_state_signal.csv"
)
HARDEN = ROOT / "repro" / "meta-detect-sealed-mdd-harden-stagea" / "outputs"

CHARTER_ID = "TIPSOFT_NEARPEAK3_PATH4_STACK_STAGEA_CHARTER"
SCREEN_ID = "TIPSOFT_NEARPEAK3_PATH4_STACK_STAGEA_SCREEN"
DECISION_ID = "TIPSOFT_NEARPEAK3_PATH4_STACK_STAGEA_DECISION_PACK"
REGISTER = "0kax"
PARENTS = ("0kaw", "0kau", "0kap")
MECH = "TIPSOFT_NEARPEAK3_PATH4_STACK"

BASE_ID = "BASE_LIVE_FUSE_COOL"
REF_NEARPEAK3 = "REF_P3_THETA_NEARPEAK3"
SEALED_MDD_FLOOR_PP = -0.25
TIP_Y_FLOOR_PP = -1.0
HELD_CAGR_FLOOR_PP = 0.10
P3_THETA = 0.005


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


def yearly_compare(nav_keep: pd.DataFrame, nav_chal: pd.DataFrame) -> list[dict[str, Any]]:
    def _yr(nav: pd.DataFrame) -> dict[int, float]:
        x = nav.copy()
        x["date"] = pd.to_datetime(x["date"])
        x["year"] = x["date"].dt.year
        out: dict[int, float] = {}
        for y, g in x.groupby("year"):
            g = g.reset_index(drop=True)
            if len(g) < 2:
                continue
            out[int(y)] = float(g["nav"].iloc[-1] / float(g["nav"].iloc[0]) - 1.0)
        return out

    a, b = _yr(nav_keep), _yr(nav_chal)
    rows = []
    for y in sorted(set(a) | set(b)):
        if y not in a or y not in b:
            continue
        rows.append(
            {
                "year": y,
                "ret_keep_pct": round(a[y] * 100, 4),
                "ret_chal_pct": round(b[y] * 100, 4),
                "ret_lift_pp": round((b[y] - a[y]) * 100, 4),
                "ret_win": bool(b[y] > a[y]),
            }
        )
    return rows


def _arm_verdict(delta: dict[str, Any], tip: dict[str, Any]) -> str:
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


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()

    nav_l3 = _load_nav(LIVESTACK / "nav_BASE_LIVE_FUSE_COOL.csv")
    nav_p3 = _load_nav(LIVESTACK / "nav_LIVE_P3_WITHIN.csv")
    nav_p3p4 = _load_nav(LIVESTACK / "nav_LIVE_P3_P4_CASH_00025.csv")
    nav_p4_only = _load_nav(LIVESTACK / "nav_LIVE_P4_ONLY_001.csv")
    soft_l1 = _load_nav(ALIGN / "nav_L1_SOFT_T1.csv")
    nav0 = float(nav_l3["nav"].iloc[0])

    r3 = _returns(nav_l3)
    r_p3 = _returns(nav_p3)
    r_p3p4 = _returns(nav_p3p4)
    r_p4o = _returns(nav_p4_only)
    panel = pd.concat(
        {"r3": r3, "rp3": r_p3, "rp3p4": r_p3p4, "rp4o": r_p4o},
        axis=1,
        join="inner",
    ).dropna(how="any")
    prem_p3 = panel["rp3"] - panel["r3"]
    prem_p4 = panel["rp3p4"] - panel["rp3"]  # Path4 incremental on tip Soft P3
    prem_p4_only = panel["rp4o"] - panel["r3"]

    proxy = _proxy_mdd63(soft_l1).reindex(panel.index).fillna(0.0)
    dd63 = _dd_from_peak(soft_l1, 63).reindex(panel.index).fillna(0.0)
    cool_exp = build_cool_c8_exposure(panel.index, proxy)
    risk_on = cool_exp >= 0.999
    defending = cool_exp < 0.999

    sig = pd.read_csv(P3_SIG, parse_dates=["date"])
    sig["date"] = pd.to_datetime(sig["date"]).dt.normalize()
    sig = sig.set_index("date").reindex(panel.index)
    trail = sig["trail_rel_63"].astype(float)
    p3_theta = (trail.abs() >= float(P3_THETA)).fillna(False)
    near_peak_3 = dd63 >= -0.03
    near_peak_5 = dd63 >= -0.05
    proxy_ok_05 = proxy > -0.05
    i_p3_near = p3_theta & near_peak_3
    ones = pd.Series(True, index=panel.index)
    zeros = pd.Series(False, index=panel.index)

    # Lagged Path4 premium health
    prem_p4_lag5 = prem_p4.shift(1).rolling(5, min_periods=3).sum().fillna(0.0)
    p4_not_bleeding = prem_p4_lag5 >= 0.0

    policies: dict[str, tuple[pd.Series, pd.Series, str]] = {
        # (I_p3, I_p4, note) — Path4-only uses separate compose
        "REF_P3_THETA_NEARPEAK3": (
            i_p3_near,
            zeros,
            "0kaw observe challenger: P3 NEARPEAK3 only (no Path4)",
        ),
        "REF_ALWAYS_P3": (ones, zeros, "Always-on tip Soft Path3 (0kap contrast)"),
        "REF_ALWAYS_P3P4": (ones, ones, "Always-on tip Soft P3+P4 CASH_00025 (0kap MDD_BLOCK ref)"),
        "P3NEAR_P4_ALWAYS": (
            i_p3_near,
            ones,
            "P3 NEARPEAK3 + Path4 always-on incremental",
        ),
        "P3NEAR_P4_SAME": (
            i_p3_near,
            i_p3_near,
            "P3 NEARPEAK3 + Path4 only when same NEARPEAK3 gate",
        ),
        "P3NEAR_P4_PEAK3": (
            i_p3_near,
            near_peak_3,
            "P3 NEARPEAK3 + Path4 whenever Soft near-peak3 (θ not required)",
        ),
        "P3NEAR_P4_PEAK5": (
            i_p3_near,
            near_peak_5,
            "P3 NEARPEAK3 + Path4 on Soft near-peak5",
        ),
        "P3NEAR_P4_RISKON": (
            i_p3_near,
            risk_on,
            "P3 NEARPEAK3 + Path4 only risk-on",
        ),
        "P3NEAR_P4_DEFEND": (
            i_p3_near,
            defending,
            "P3 NEARPEAK3 + Path4 only while COOL defending",
        ),
        "P3NEAR_P4_PROXY05": (
            i_p3_near,
            proxy_ok_05,
            "P3 NEARPEAK3 + Path4 when Soft proxy_mdd63 > −5%",
        ),
        "P3NEAR_P4_NOTBLEED": (
            i_p3_near,
            i_p3_near & p4_not_bleeding,
            "P3 NEARPEAK3 + Path4 same gate AND lagged 5d prem_p4 ≥ 0",
        ),
        "P3NEAR_P4_HARD": (
            i_p3_near,
            i_p3_near & risk_on & p4_not_bleeding,
            "P3 NEARPEAK3 + Path4 ∩ risk-on ∩ not-bleed",
        ),
        "P4_ONLY_NEARPEAK3": (
            zeros,
            i_p3_near,
            "Path4-only incremental vs L3 on NEARPEAK3 days (no Path3) — diagnostic",
        ),
    }

    arms: dict[str, pd.DataFrame] = {BASE_ID: nav_l3}
    metas: dict[str, dict[str, Any]] = {
        BASE_ID: {"note": "live Soft+FUSE+COOL Exact T+1", "pct_p3_on": 0.0, "pct_p4_on": 0.0}
    }
    nav_l3.to_csv(OUT / f"nav_{BASE_ID}.csv", index=False)

    # Prefer frozen 0kau NEARPEAK3 NAV if available for REF
    if (HARDEN / "nav_P3_THETA_NEARPEAK3.csv").exists():
        arms[REF_NEARPEAK3] = _load_nav(HARDEN / "nav_P3_THETA_NEARPEAK3.csv")
        arms[REF_NEARPEAK3].to_csv(OUT / f"nav_{REF_NEARPEAK3}.csv", index=False)
        metas[REF_NEARPEAK3] = {
            "note": "Frozen 0kau/0kaw Exact T+1 NEARPEAK3 NAV SSOT",
            "pct_p3_on": 50.83,
            "pct_p4_on": 0.0,
            "source": str(HARDEN / "nav_P3_THETA_NEARPEAK3.csv"),
        }

    gate_rows = []
    for arm, (i_p3, i_p4, note) in policies.items():
        if arm == REF_NEARPEAK3 and REF_NEARPEAK3 in arms:
            # keep frozen SSOT; still record duty
            gate_rows.append(
                {
                    "arm": arm,
                    "pct_p3_on": round(float(i_p3.mean()) * 100, 2),
                    "pct_p4_on": 0.0,
                    "note": note + " (frozen SSOT used)",
                }
            )
            continue
        if arm == "P4_ONLY_NEARPEAK3":
            r = panel["r3"] + i_p4.astype(float) * prem_p4_only
        else:
            r = panel["r3"] + i_p3.astype(float) * prem_p3 + i_p4.astype(float) * prem_p4
        nav = _nav_from_returns(r, nav0)
        arms[arm] = nav
        nav.to_csv(OUT / f"nav_{arm}.csv", index=False)
        meta = {
            "note": note,
            "pct_p3_on": round(float(i_p3.mean()) * 100, 2),
            "pct_p4_on": round(float(i_p4.mean()) * 100, 2),
            "p3_theta": P3_THETA,
            "proxy_x": PROXY_X,
            "path4_book": "LIVE_P3_P4_CASH_00025",
            "clock": "exact_t1",
            "hybrid_t0_carve": False,
        }
        metas[arm] = meta
        gate_rows.append({"arm": arm, **{k: meta[k] for k in ("pct_p3_on", "pct_p4_on", "note")}})

    pd.DataFrame(gate_rows).to_csv(OUT / "detector_duty_cycle.csv", index=False)
    pd.DataFrame(
        {
            "date": panel.index,
            "i_p3_nearpeak3": i_p3_near.astype(int).to_numpy(),
            "near_peak_3": near_peak_3.astype(int).to_numpy(),
            "risk_on": risk_on.astype(int).to_numpy(),
            "p4_not_bleeding": p4_not_bleeding.astype(int).to_numpy(),
            "prem_p3": prem_p3.to_numpy(),
            "prem_p4": prem_p4.to_numpy(),
            "trail_rel_63": trail.reindex(panel.index).to_numpy(),
        }
    ).to_csv(OUT / "detector_panel.csv", index=False)

    base = arms[BASE_ID]
    bw = _pack(base)
    ref_nav = arms.get(REF_NEARPEAK3)
    ref_w = _pack(ref_nav) if ref_nav is not None else None

    rows: list[dict[str, Any]] = []
    for arm, nav in arms.items():
        if arm == BASE_ID:
            continue
        delta = _delta(bw, _pack(nav))
        tip = _tip(base, nav)
        yearly = yearly_compare(base, nav)
        ret_w = int(sum(1 for r in yearly if r["ret_win"]))
        ret_l = int(sum(1 for r in yearly if not r["ret_win"]))
        v = _arm_verdict(delta, tip)
        vs_near = None
        if ref_w is not None and arm != REF_NEARPEAK3:
            d2 = _delta(ref_w, _pack(nav))
            t2 = _tip(ref_nav, nav)
            vs_near = {
                "held_cagr_lift_pp": d2["heldout_2019_plus"]["cagr_lift_pp"],
                "sealed_mdd_improve_pp": d2["sealed_2023_plus"]["mdd_improve_pp"],
                "tip_ytd_cagr_lift_pp": (t2.get("ytd") or {}).get("cagr_lift_pp"),
                "verdict_vs_nearpeak3": _arm_verdict(d2, t2),
            }
        rows.append(
            {
                "arm": arm,
                "verdict_vs_live": v,
                "full_cagr_lift_pp": delta["full"]["cagr_lift_pp"],
                "held_cagr_lift_pp": delta["heldout_2019_plus"]["cagr_lift_pp"],
                "sealed_mdd_improve_pp": delta["sealed_2023_plus"]["mdd_improve_pp"],
                "tip_ytd_cagr_lift_pp": (tip.get("ytd") or {}).get("cagr_lift_pp"),
                "tip_1y_cagr_lift_pp": (tip.get("trailing_1y") or {}).get("cagr_lift_pp"),
                "yearly_ret_wl": f"{ret_w}-{ret_l}",
                "vs_nearpeak3": vs_near,
                "meta": metas.get(arm, {}),
                "delta": delta,
                "tip": tip,
                "yearly": yearly,
            }
        )

    def _rank_key(r: dict[str, Any]) -> tuple:
        sealed = r["sealed_mdd_improve_pp"]
        sealed_ok = 0 if sealed is not None and float(sealed) >= SEALED_MDD_FLOOR_PP else 1
        v = r["verdict_vs_live"]
        hit_rank = {"HIT": 0, "HELD_HIT": 1, "SOFT": 2}.get(v, 3)
        has_p4 = 0 if float((r.get("meta") or {}).get("pct_p4_on") or 0) > 0 else 1
        vn = r.get("vs_nearpeak3") or {}
        vs_held = vn.get("held_cagr_lift_pp")
        # Prefer not destroying NEARPEAK3 held edge
        vs_held_ok = 0 if vs_held is not None and float(vs_held) >= -0.05 else 1
        return (
            hit_rank,
            sealed_ok,
            vs_held_ok,
            has_p4,
            -(sealed if sealed is not None else -999),
            -(r["held_cagr_lift_pp"] or -999),
            -(r["tip_ytd_cagr_lift_pp"] or -999),
        )

    p4_rows = [
        r
        for r in rows
        if float((r.get("meta") or {}).get("pct_p4_on") or 0) > 0
        and not str(r["arm"]).startswith("REF_")
    ]
    ref_rows = [r for r in rows if str(r["arm"]).startswith("REF_")]
    champion = sorted(p4_rows, key=_rank_key)[0] if p4_rows else None
    best_ref = sorted(ref_rows, key=_rank_key)[0] if ref_rows else None
    hit_p4 = [r for r in p4_rows if r["verdict_vs_live"] in ("HIT", "HELD_HIT", "SOFT")]

    # Also require not destroying NEARPEAK3 edge badly: vs_near sealed >= -0.25 and held not << 0
    if hit_p4:
        # Prefer those that also clear vs NEARPEAK3 or at least don't MDD_BLOCK vs it
        good = [
            r
            for r in hit_p4
            if (r.get("vs_nearpeak3") or {}).get("verdict_vs_nearpeak3")
            in ("HIT", "HELD_HIT", "SOFT", "NO_EDGE", None)
            or (
                (r.get("vs_nearpeak3") or {}).get("sealed_mdd_improve_pp") is not None
                and float((r["vs_nearpeak3"] or {})["sealed_mdd_improve_pp"]) >= SEALED_MDD_FLOOR_PP
            )
        ]
        champion = sorted(good or hit_p4, key=_rank_key)[0]
        verdict = "PATH4_STACK_HIT"
    elif champion and champion["verdict_vs_live"] == "MDD_BLOCK":
        verdict = "PATH4_STACK_MDD_BLOCK"
    elif champion and champion["verdict_vs_live"] == "TIP_BLOCK":
        verdict = "PATH4_STACK_TIP_BLOCK"
    elif champion:
        verdict = f"PATH4_STACK_{champion['verdict_vs_live']}"
    else:
        verdict = "PATH4_STACK_NO_EDGE"

    pd.DataFrame(
        [
            {
                "arm": r["arm"],
                "verdict": r["verdict_vs_live"],
                "held": r["held_cagr_lift_pp"],
                "full": r["full_cagr_lift_pp"],
                "sealed_mdd": r["sealed_mdd_improve_pp"],
                "tipY": r["tip_ytd_cagr_lift_pp"],
                "tip1y": r["tip_1y_cagr_lift_pp"],
                "ret_wl": r["yearly_ret_wl"],
                "pct_p3": (r["meta"] or {}).get("pct_p3_on"),
                "pct_p4": (r["meta"] or {}).get("pct_p4_on"),
                "vs_near_held": (r.get("vs_nearpeak3") or {}).get("held_cagr_lift_pp"),
                "vs_near_sealed": (r.get("vs_nearpeak3") or {}).get("sealed_mdd_improve_pp"),
                "vs_near_tipY": (r.get("vs_nearpeak3") or {}).get("tip_ytd_cagr_lift_pp"),
                "vs_near_verdict": (r.get("vs_nearpeak3") or {}).get("verdict_vs_nearpeak3"),
                "note": (r["meta"] or {}).get("note"),
            }
            for r in rows
        ]
    ).to_csv(OUT / "arms_vs_live.csv", index=False)

    if champion and champion.get("yearly"):
        pd.DataFrame(champion["yearly"]).to_csv(OUT / "yearly_champion_vs_live.csv", index=False)

    optimize = [
        "Stack Path4 only as Exact T+1 incremental on tip Soft shell; hybrid T+0 carve FORBIDDEN",
        (
            f"Path4 champion `{champion['arm']}` → {champion['verdict_vs_live']} held "
            f"{champion['held_cagr_lift_pp']} tipY {champion['tip_ytd_cagr_lift_pp']} "
            f"sealedMDD {champion['sealed_mdd_improve_pp']}"
            if champion
            else "No Path4 champion"
        ),
        (
            f"vs NEARPEAK3-only: held {(champion.get('vs_nearpeak3') or {}).get('held_cagr_lift_pp')} "
            f"tipY {(champion.get('vs_nearpeak3') or {}).get('tip_ytd_cagr_lift_pp')} "
            f"sealed {(champion.get('vs_nearpeak3') or {}).get('sealed_mdd_improve_pp')} "
            f"→ {(champion.get('vs_nearpeak3') or {}).get('verdict_vs_nearpeak3')}"
            if champion and champion.get("vs_nearpeak3")
            else "No vs-NEARPEAK3 delta"
        ),
        (
            f"0kaw ref `{best_ref['arm']}` → {best_ref['verdict_vs_live']}"
            if best_ref
            else "No ref"
        ),
        "Path4 live flag stays OFF; Soft KEEP; broker false; no wire this pack",
        "Next: Path4 clears live gates under NEARPEAK3 but vs NEARPEAK3-only is NO_EDGE — "
        "keep Path4 OFF on 0kaw observe unless a +held Path4 gate appears",
    ]

    screen = {
        "id": SCREEN_ID,
        "register": REGISTER,
        "parents": list(PARENTS),
        "generated_at_utc": generated,
        "mech": MECH,
        "verdict": verdict,
        "base": BASE_ID,
        "clock": "exact_t1",
        "hybrid_t0_carve": False,
        "champion": {
            "arm": champion["arm"],
            "verdict_vs_live": champion["verdict_vs_live"],
            "held_cagr_lift_pp": champion["held_cagr_lift_pp"],
            "full_cagr_lift_pp": champion["full_cagr_lift_pp"],
            "sealed_mdd_improve_pp": champion["sealed_mdd_improve_pp"],
            "tip_ytd_cagr_lift_pp": champion["tip_ytd_cagr_lift_pp"],
            "tip_1y_cagr_lift_pp": champion["tip_1y_cagr_lift_pp"],
            "vs_nearpeak3": champion.get("vs_nearpeak3"),
            "meta": champion["meta"],
        }
        if champion
        else None,
        "ref_nearpeak3": {
            "arm": best_ref["arm"],
            "verdict_vs_live": best_ref["verdict_vs_live"],
            "held_cagr_lift_pp": best_ref["held_cagr_lift_pp"],
            "sealed_mdd_improve_pp": best_ref["sealed_mdd_improve_pp"],
            "tip_ytd_cagr_lift_pp": best_ref["tip_ytd_cagr_lift_pp"],
        }
        if best_ref
        else None,
        "arms": [
            {
                "arm": r["arm"],
                "verdict_vs_live": r["verdict_vs_live"],
                "held_cagr_lift_pp": r["held_cagr_lift_pp"],
                "full_cagr_lift_pp": r["full_cagr_lift_pp"],
                "sealed_mdd_improve_pp": r["sealed_mdd_improve_pp"],
                "tip_ytd_cagr_lift_pp": r["tip_ytd_cagr_lift_pp"],
                "tip_1y_cagr_lift_pp": r["tip_1y_cagr_lift_pp"],
                "yearly_ret_wl": r["yearly_ret_wl"],
                "vs_nearpeak3": r.get("vs_nearpeak3"),
                "meta": r["meta"],
            }
            for r in rows
        ],
        "gates": {
            "held_cagr_floor_pp": HELD_CAGR_FLOOR_PP,
            "sealed_mdd_floor_pp": SEALED_MDD_FLOOR_PP,
            "tip_y_floor_pp": TIP_Y_FLOOR_PP,
            "p3_theta": P3_THETA,
        },
        "optimize_live": optimize,
        "soft_keep": True,
        "broker": False,
        "path4_live": False,
        "label": f"{SCREEN_ID}_{generated[:10]}__{verdict}",
    }
    (OUT / "screen.json").write_text(json.dumps(screen, indent=2) + "\n", encoding="utf-8")

    def _md_table(rs: list[dict[str, Any]]) -> str:
        lines = [
            "| Arm | vs live | held | sealed MDD↑ | tipY | p3% | p4% | vs NEAR held | vs NEAR sealed |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for r in rs:
            m = r.get("meta") or {}
            vn = r.get("vs_nearpeak3") or {}
            lines.append(
                f"| {r['arm']} | {r['verdict_vs_live']} | {r['held_cagr_lift_pp']} | "
                f"{r['sealed_mdd_improve_pp']} | {r['tip_ytd_cagr_lift_pp']} | "
                f"{m.get('pct_p3_on', '')} | {m.get('pct_p4_on', '')} | "
                f"{vn.get('held_cagr_lift_pp', '')} | {vn.get('sealed_mdd_improve_pp', '')} |"
            )
        return "\n".join(lines)

    charter_md = "\n".join(
        [
            f"# {CHARTER_ID}",
            "",
            f"Date: {generated[:10]}",
            "Status: **Stage A — tip Soft Exact T+1 NEARPEAK3 × Path4 stack**",
            f"Register: **{REGISTER}** · Parents: {', '.join(PARENTS)}",
            f"Mech: `{MECH}`",
            "",
            "## Question",
            "",
            "Can Path4 CASH_ETF incremental be detector-stacked on P3_THETA_NEARPEAK3 "
            "under tip Soft Exact T+1 without breaking sealed MDD / tip gates?",
            "",
            "## Method",
            "",
            "- `r = r_L3 + I_p3*(r_P3−r_L3) + I_p4*(r_P3P4−r_P3)` Exact T+1 only",
            "- I_p3 = NEARPEAK3; I_p4 screened (always / same / peak / risk-on / not-bleed)",
            "- Hybrid Soft-core T+0 carve FORBIDDEN",
            "",
            f"Label: `{CHARTER_ID}_{generated[:10]}__PATH4_STACK`",
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
                "clock": "exact_t1",
                "hybrid_t0_carve": False,
                "soft_keep": True,
                "path4_live": False,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    write_repro_pointer(OPS / f"{CHARTER_ID}.json", REP / f"{CHARTER_ID}.json", kind="charter")

    screen_md = "\n".join(
        [
            f"# {SCREEN_ID}",
            "",
            f"Date: {generated[:10]} · Verdict: **`{verdict}`** · "
            f"champion=**`{(champion or {}).get('arm')}`**",
            f"Register: **{REGISTER}** · mech=`{MECH}` · base=`{BASE_ID}` · clock Exact T+1",
            "",
            "## Arms vs live Soft+FUSE+COOL",
            "",
            _md_table(rows),
            "",
            "## Optimize / disposition",
            "",
            *[f"{i}. {x}" for i, x in enumerate(optimize, 1)],
            "",
            "Repro: `PYTHONPATH=scripts python3 "
            "scripts/tipsoft_nearpeak3_path4_stack_stagea.py`",
            "",
            f"Label: `{screen['label']}`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", screen_md, kind="screen"
    )
    (OPS / f"{SCREEN_ID}.json").write_text(
        json.dumps(screen, indent=2) + "\n", encoding="utf-8"
    )
    write_repro_pointer(OPS / f"{SCREEN_ID}.json", REP / f"{SCREEN_ID}.json", kind="screen")

    ch = screen["champion"] or {}
    decision = {
        "label": f"{DECISION_ID}_{generated[:10]}__{verdict}__NO_LIVE",
        "verdict": verdict,
        "register": REGISTER,
        "parents": list(PARENTS),
        "mech": MECH,
        "champion": screen["champion"],
        "ref_nearpeak3": screen.get("ref_nearpeak3"),
        "optimize_live": optimize,
        "soft_keep": True,
        "broker": False,
        "path4_live": False,
        "hybrid_t0_carve": False,
        "wire": False,
    }
    decision_md = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: {generated[:10]} · Verdict: **`{verdict}`** · champion=**`{ch.get('arm')}`**",
            f"Register: **{REGISTER}** · mech **`{MECH}`** · Exact T+1",
            "",
            "## Path4 stack champion vs live",
            "",
            f"- held CAGR lift: **{ch.get('held_cagr_lift_pp')}** pp",
            f"- sealed MDD improve: **{ch.get('sealed_mdd_improve_pp')}** pp",
            f"- tipY / tip1y: **{ch.get('tip_ytd_cagr_lift_pp')}** / "
            f"**{ch.get('tip_1y_cagr_lift_pp')}**",
            f"- vs NEARPEAK3-only: **{ch.get('vs_nearpeak3')}**",
            "",
            "## Rule",
            "",
            "- Path4 is optional Exact T+1 incremental on NEARPEAK3; not Soft-core T+0.",
            "- Path4 live flag OFF until a dedicated HIT + OPEN ballot.",
            "",
            "## Next",
            "",
            *[f"{i}. {x}" for i, x in enumerate(optimize, 1)],
            "",
            f"Label: `{decision['label']}`",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{DECISION_ID}.md",
        REP / f"{DECISION_ID}.md",
        decision_md,
        kind="decision pack",
    )
    (OPS / f"{DECISION_ID}.json").write_text(
        json.dumps(decision, indent=2) + "\n", encoding="utf-8"
    )
    write_repro_pointer(
        OPS / f"{DECISION_ID}.json", REP / f"{DECISION_ID}.json", kind="decision pack"
    )

    summary = {
        "verdict": verdict,
        "champion": (champion or {}).get("arm"),
        "held_cagr_lift_pp": (champion or {}).get("held_cagr_lift_pp"),
        "sealed_mdd_improve_pp": (champion or {}).get("sealed_mdd_improve_pp"),
        "tip_ytd_cagr_lift_pp": (champion or {}).get("tip_ytd_cagr_lift_pp"),
        "vs_nearpeak3": (champion or {}).get("vs_nearpeak3"),
        "optimize_live": optimize,
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
