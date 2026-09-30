#!/usr/bin/env python3
"""Meta-detect × hybrid twin Stage B (0kav).

Parent 0kau HIT ``P3_THETA_NEARPEAK3`` was tip Soft Exact T+1 layer-premium.
This Stage B re-scores the same sealed-MDD gates under the default promote twin
``TIP_SOFT_HYBRID_T1_OVERLAY_T0_CARVE``:

  r = r_shell_T1 + I_gate * (r_softcore_T0 − r_softcore_T1lag)

Gates (causal, Soft L1): |trail_rel_63|≥θ AND near-peak / proxy / risk-on
(same family as 0kau HIT arms).

Soft KEEP · broker false · Path4 live OFF · no wire.
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
from tip_soft_hybrid_runner import (
    CARVE_OUT_ID,
    DEFAULT_LIVE_BASE,
    DEFAULT_LIVE_P3_T1,
    DEFAULT_SOFTCORE_P3_T0,
    DEFAULT_SOFTCORE_P3P4_T0,
    RUNNER_ID,
    align_returns,
    load_nav,
    nav_returns,
    softcore_t1_lag_nav,
)

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "meta-detect-hybrid-nearpeak3-stageb"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

ALIGN = ROOT / "repro" / "research-live-align-gap-stagea" / "outputs"
HARDEN = ROOT / "repro" / "meta-detect-sealed-mdd-harden-stagea" / "outputs"
P3_SIG = (
    ROOT / "repro" / "fin-sat-path3-t0-dual-paper-observe" / "outputs" / "p3_t0_state_signal.csv"
)

CHARTER_ID = "META_DETECT_HYBRID_NEARPEAK3_STAGEB_CHARTER"
SCREEN_ID = "META_DETECT_HYBRID_NEARPEAK3_STAGEB_SCREEN"
DECISION_ID = "META_DETECT_HYBRID_NEARPEAK3_STAGEB_DECISION_PACK"
REGISTER = "0kav"
PARENTS = ("0kau", "0kas", "0kat")
MECH = "META_DETECT_HYBRID_NEARPEAK3"

BASE_ID = "BASE_LIVE_FUSE_COOL"
SEALED_MDD_FLOOR_PP = -0.25
TIP_Y_FLOOR_PP = -1.0
HELD_CAGR_FLOOR_PP = 0.10
P3_THETA = 0.005


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


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


def build_gated_hybrid(
    *,
    shell_nav: pd.DataFrame,
    softcore_t0_nav: pd.DataFrame,
    gate: pd.Series,
) -> tuple[pd.DataFrame, pd.Series, dict[str, Any]]:
    """r = r_shell + I_gate * (r_t0 − r_t1lag)."""
    shell_r = nav_returns(shell_nav).rename("r_shell")
    t0_r = nav_returns(softcore_t0_nav).rename("r_t0")
    t1_r = nav_returns(softcore_t1_lag_nav(softcore_t0_nav)).rename("r_t1lag")
    m = align_returns(shell_r, t0_r, t1_r)
    g = gate.reindex(m.index).fillna(False).astype(bool)
    prem = (m["r_t0"] - m["r_t1lag"]).rename("r_t0_premium")
    r_h = (m["r_shell"] + g.astype(float) * prem).rename("r_hybrid")
    nav = (1.0 + r_h).cumprod() * float(shell_nav["nav"].iloc[0])
    out = pd.DataFrame({"date": r_h.index, "nav": nav.to_numpy()}).reset_index(drop=True)
    meta = {
        "runner_id": RUNNER_ID,
        "carve_out_id": CARVE_OUT_ID,
        "shell_fill_timing": "exact_t1",
        "carve_fill_timing": "t0",
        "pct_gate_on": round(float(g.mean()) * 100, 2),
        "n_days": int(len(out)),
        "mean_gated_premium": round(float((g.astype(float) * prem).mean()), 6),
        "sum_gated_premium": round(float((g.astype(float) * prem).sum()), 6),
        "mean_ungated_premium": round(float(prem.mean()), 6),
        "start": str(pd.Timestamp(out["date"].iloc[0]).date()),
        "end": str(pd.Timestamp(out["date"].iloc[-1]).date()),
    }
    return out, g, meta


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()

    shell = load_nav(DEFAULT_LIVE_BASE)
    soft_l1 = load_nav(ALIGN / "nav_L1_SOFT_T1.csv")
    core_p3 = load_nav(DEFAULT_SOFTCORE_P3_T0)
    core_p3p4 = load_nav(DEFAULT_SOFTCORE_P3P4_T0)

    proxy = _proxy_mdd63(soft_l1)
    dd63 = _dd_from_peak(soft_l1, 63)
    cool_exp = build_cool_c8_exposure(proxy.index, proxy)
    risk_on = cool_exp >= 0.999

    sig = pd.read_csv(P3_SIG, parse_dates=["date"])
    sig["date"] = pd.to_datetime(sig["date"]).dt.normalize()
    sig = sig.set_index("date")
    trail = sig["trail_rel_63"].astype(float)
    p3_theta = (trail.abs() >= float(P3_THETA)).fillna(False)

    # Align gate features to a common index via shell returns
    idx = nav_returns(shell).index
    p3_theta = p3_theta.reindex(idx).fillna(False)
    near_peak_3 = (dd63.reindex(idx).fillna(0.0) >= -0.03)
    near_peak_5 = (dd63.reindex(idx).fillna(0.0) >= -0.05)
    proxy_ok_05 = proxy.reindex(idx).fillna(0.0) > -0.05
    risk_on_a = risk_on.reindex(idx).fillna(True)
    always = pd.Series(True, index=idx)

    gates: dict[str, tuple[pd.Series, str]] = {
        "UNGATED": (always, "0kas-style always-on T+0 carve premium"),
        "NEARPEAK3": (p3_theta & near_peak_3, "0kau champion: |trail|≥θ AND Soft within 3% of 63d peak"),
        "PROXY05": (p3_theta & proxy_ok_05, "0kau HIT: |trail|≥θ AND proxy_mdd63 > −5%"),
        "PEAK3_RISKON": (
            p3_theta & near_peak_3 & risk_on_a,
            "0kau HIT: |trail|≥θ AND near-peak3 AND risk-on",
        ),
        "NEARPEAK5": (p3_theta & near_peak_5, "looser near-peak5 contrast"),
    }

    arms: dict[str, pd.DataFrame] = {BASE_ID: shell}
    metas: dict[str, dict[str, Any]] = {
        BASE_ID: {
            "kind": "tip_soft_shell",
            "runner_id": RUNNER_ID,
            "note": "live Soft+FUSE+COOL Exact T+1 shell",
        }
    }

    # Dual-track tip Soft Exact T+1 NEARPEAK3 from 0kau (P1)
    tip_near = HARDEN / "nav_P3_THETA_NEARPEAK3.csv"
    if tip_near.exists():
        arms["TIPSOFT_P3_THETA_NEARPEAK3"] = load_nav(tip_near)
        metas["TIPSOFT_P3_THETA_NEARPEAK3"] = {
            "kind": "tip_soft_exact_t1_0kau",
            "runner_id": RUNNER_ID,
            "shell_fill_timing": "exact_t1",
            "carve_fill_timing": "exact_t1",
            "note": "0kau HIT arm (tip Soft L4−L3 gated) — dual-track contrast, not hybrid T+0",
            "pct_gate_on": None,
        }

    if Path(DEFAULT_LIVE_P3_T1).exists():
        arms["TIPSOFT_P3_WITHIN_T1"] = load_nav(DEFAULT_LIVE_P3_T1)
        metas["TIPSOFT_P3_WITHIN_T1"] = {
            "kind": "tip_soft_p3_exact_t1_ref",
            "note": "0kap always-on tip Soft Path3 Exact T+1",
        }

    gate_rows: list[dict[str, Any]] = []
    for gname, (gate, note) in gates.items():
        for core_name, core_nav, path4 in (
            ("P3", core_p3, False),
            ("P3P4", core_p3p4, True),
        ):
            arm = f"HYBRID_{core_name}_{gname}"
            nav, g, meta = build_gated_hybrid(
                shell_nav=shell, softcore_t0_nav=core_nav, gate=gate
            )
            arms[arm] = nav
            nav.to_csv(OUT / f"nav_{arm}.csv", index=False)
            full_meta = {
                **meta,
                "kind": "tip_soft_hybrid_gated",
                "gate": gname,
                "path3": True,
                "path4": path4,
                "note": f"{note} · softcore={'P3_WITHIN' if not path4 else 'P3_P4_CASH_00025'}",
                "proxy_x": PROXY_X,
                "p3_theta": P3_THETA,
            }
            metas[arm] = full_meta
            gate_rows.append(
                {
                    "arm": arm,
                    "gate": gname,
                    "path4": path4,
                    "pct_gate_on": meta["pct_gate_on"],
                    "mean_gated_premium": meta["mean_gated_premium"],
                    "sum_gated_premium": meta["sum_gated_premium"],
                    "note": full_meta["note"],
                }
            )

    pd.DataFrame(gate_rows).to_csv(OUT / "gate_duty_cycle.csv", index=False)
    shell.to_csv(OUT / f"nav_{BASE_ID}.csv", index=False)
    for arm in ("TIPSOFT_P3_THETA_NEARPEAK3", "TIPSOFT_P3_WITHIN_T1"):
        if arm in arms:
            arms[arm].to_csv(OUT / f"nav_{arm}.csv", index=False)

    # Detector panel snapshot
    pd.DataFrame(
        {
            "date": idx,
            "p3_theta": p3_theta.astype(int).to_numpy(),
            "near_peak_3": near_peak_3.astype(int).to_numpy(),
            "near_peak_5": near_peak_5.astype(int).to_numpy(),
            "proxy_ok_05": proxy_ok_05.astype(int).to_numpy(),
            "risk_on": risk_on_a.astype(int).to_numpy(),
            "gate_NEARPEAK3": (p3_theta & near_peak_3).astype(int).to_numpy(),
        }
    ).to_csv(OUT / "detector_panel.csv", index=False)

    base = arms[BASE_ID]
    bw = _pack(base)
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
                "meta": metas.get(arm, {}),
                "delta": delta,
                "tip": tip,
                "yearly": yearly,
            }
        )

    def _rank_key(r: dict[str, Any]) -> tuple:
        sealed = r["sealed_mdd_improve_pp"]
        sealed_ok = 0 if sealed is not None and float(sealed) >= SEALED_MDD_FLOOR_PP else 1
        hit = 0 if r["verdict_vs_live"] in ("HIT", "HELD_HIT", "SOFT") else 1
        return (
            hit,
            sealed_ok,
            -(sealed if sealed is not None else -999),
            -(r["held_cagr_lift_pp"] or -999),
            -(r["tip_ytd_cagr_lift_pp"] or -999),
        )

    hybrid_rows = [r for r in rows if str(r["arm"]).startswith("HYBRID_")]
    # Primary: NEARPEAK3 hybrid P3 (the asked Stage B target)
    target = next((r for r in hybrid_rows if r["arm"] == "HYBRID_P3_NEARPEAK3"), None)
    champion = sorted(hybrid_rows, key=_rank_key)[0] if hybrid_rows else None
    tipsoft_near = next((r for r in rows if r["arm"] == "TIPSOFT_P3_THETA_NEARPEAK3"), None)
    ungated = next((r for r in hybrid_rows if r["arm"] == "HYBRID_P3_UNGATED"), None)

    hit_like = [r for r in hybrid_rows if r["verdict_vs_live"] in ("HIT", "HELD_HIT", "SOFT")]
    if target and target["verdict_vs_live"] == "HIT":
        verdict = "HYBRID_NEARPEAK3_HIT"
    elif target and target["verdict_vs_live"] in ("HELD_HIT", "SOFT"):
        verdict = f"HYBRID_NEARPEAK3_{target['verdict_vs_live']}"
    elif hit_like:
        verdict = "HYBRID_GATE_HIT_OTHER"
    elif target and target["verdict_vs_live"] == "MDD_BLOCK":
        verdict = "HYBRID_NEARPEAK3_MDD_BLOCK"
    elif target and target["verdict_vs_live"] == "TIP_BLOCK":
        verdict = "HYBRID_NEARPEAK3_TIP_BLOCK"
    elif target:
        verdict = f"HYBRID_NEARPEAK3_{target['verdict_vs_live']}"
    else:
        verdict = "HYBRID_NEARPEAK3_INCOMPLETE"

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
                "pct_gate": (r["meta"] or {}).get("pct_gate_on"),
                "note": (r["meta"] or {}).get("note"),
            }
            for r in rows
        ]
    ).to_csv(OUT / "arms_vs_live.csv", index=False)

    focus = target or champion
    if focus and focus.get("yearly"):
        pd.DataFrame(focus["yearly"]).to_csv(OUT / "yearly_champion_vs_live.csv", index=False)

    sealed_delta_vs_ungated = None
    if target and ungated:
        if (
            target["sealed_mdd_improve_pp"] is not None
            and ungated["sealed_mdd_improve_pp"] is not None
        ):
            sealed_delta_vs_ungated = round(
                float(target["sealed_mdd_improve_pp"]) - float(ungated["sealed_mdd_improve_pp"]),
                4,
            )

    optimize = [
        f"Stage B target `HYBRID_P3_NEARPEAK3` → "
        f"{(target or {}).get('verdict_vs_live')} held {(target or {}).get('held_cagr_lift_pp')} "
        f"tipY {(target or {}).get('tip_ytd_cagr_lift_pp')} sealedMDD "
        f"{(target or {}).get('sealed_mdd_improve_pp')}",
        (
            f"Ungated hybrid ref `HYBRID_P3_UNGATED` → {ungated['verdict_vs_live']} "
            f"sealedMDD {ungated['sealed_mdd_improve_pp']} · sealed Δ vs ungated = "
            f"{sealed_delta_vs_ungated} pp"
            if ungated
            else "No ungated ref"
        ),
        (
            f"Dual-track tip Soft `TIPSOFT_P3_THETA_NEARPEAK3` → "
            f"{tipsoft_near['verdict_vs_live']} held {tipsoft_near['held_cagr_lift_pp']} "
            f"sealedMDD {tipsoft_near['sealed_mdd_improve_pp']}"
            if tipsoft_near
            else "No tip Soft dual-track"
        ),
        (
            f"Best hybrid overall `{champion['arm']}` → {champion['verdict_vs_live']}"
            if champion
            else "No hybrid champion"
        ),
        "Promote only if hybrid NEARPEAK3 clears tip Soft gates; Soft-core HIT alone insufficient",
        "Soft KEEP · Path4 OFF · broker false · no live wire this pack",
    ]

    screen = {
        "id": SCREEN_ID,
        "register": REGISTER,
        "parents": list(PARENTS),
        "generated_at_utc": generated,
        "mech": MECH,
        "runner_id": RUNNER_ID,
        "verdict": verdict,
        "base": BASE_ID,
        "target": {
            "arm": target["arm"],
            "verdict_vs_live": target["verdict_vs_live"],
            "held_cagr_lift_pp": target["held_cagr_lift_pp"],
            "full_cagr_lift_pp": target["full_cagr_lift_pp"],
            "sealed_mdd_improve_pp": target["sealed_mdd_improve_pp"],
            "tip_ytd_cagr_lift_pp": target["tip_ytd_cagr_lift_pp"],
            "tip_1y_cagr_lift_pp": target["tip_1y_cagr_lift_pp"],
            "meta": target["meta"],
        }
        if target
        else None,
        "champion_hybrid": {
            "arm": champion["arm"],
            "verdict_vs_live": champion["verdict_vs_live"],
            "held_cagr_lift_pp": champion["held_cagr_lift_pp"],
            "sealed_mdd_improve_pp": champion["sealed_mdd_improve_pp"],
            "tip_ytd_cagr_lift_pp": champion["tip_ytd_cagr_lift_pp"],
        }
        if champion
        else None,
        "ungated_ref": {
            "arm": ungated["arm"],
            "verdict_vs_live": ungated["verdict_vs_live"],
            "held_cagr_lift_pp": ungated["held_cagr_lift_pp"],
            "sealed_mdd_improve_pp": ungated["sealed_mdd_improve_pp"],
            "tip_ytd_cagr_lift_pp": ungated["tip_ytd_cagr_lift_pp"],
        }
        if ungated
        else None,
        "tipsoft_dual_track": {
            "arm": tipsoft_near["arm"],
            "verdict_vs_live": tipsoft_near["verdict_vs_live"],
            "held_cagr_lift_pp": tipsoft_near["held_cagr_lift_pp"],
            "sealed_mdd_improve_pp": tipsoft_near["sealed_mdd_improve_pp"],
            "tip_ytd_cagr_lift_pp": tipsoft_near["tip_ytd_cagr_lift_pp"],
        }
        if tipsoft_near
        else None,
        "sealed_delta_vs_ungated_pp": sealed_delta_vs_ungated,
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
            "| Arm | vs live | held | full | sealed MDD↑ | tipY | gate% |",
            "|---|---|---:|---:|---:|---:|---:|",
        ]
        for r in rs:
            m = r.get("meta") or {}
            lines.append(
                f"| {r['arm']} | {r['verdict_vs_live']} | {r['held_cagr_lift_pp']} | "
                f"{r['full_cagr_lift_pp']} | {r['sealed_mdd_improve_pp']} | "
                f"{r['tip_ytd_cagr_lift_pp']} | {m.get('pct_gate_on', '')} |"
            )
        return "\n".join(lines)

    charter_md = "\n".join(
        [
            f"# {CHARTER_ID}",
            "",
            f"Date: {generated[:10]}",
            "Status: **Stage B — hybrid twin verify P3_THETA_NEARPEAK3**",
            f"Register: **{REGISTER}** · Parents: {', '.join(PARENTS)}",
            f"Mech: `{MECH}` · Runner: `{RUNNER_ID}`",
            "",
            "## Question",
            "",
            "Under Soft Exact T+1 FUSE+COOL shell, does Soft-core T+0 carve premium "
            "gated by P3_THETA_NEARPEAK3 clear tip Soft promote gates?",
            "",
            "## Method",
            "",
            f"`r = r_shell_T1 + I_NEARPEAK3 * (r_softcore_T0 − r_softcore_T1lag)`",
            "- Dual-track: tip Soft Exact T+1 NEARPEAK3 (0kau) vs hybrid gated T+0",
            "- Contrast ungated hybrid (0kas MDD_BLOCK)",
            "",
            f"Label: `{CHARTER_ID}_{generated[:10]}__HYBRID_NEARPEAK3`",
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
                "runner_id": RUNNER_ID,
                "soft_keep": True,
                "broker": False,
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
            f"target=**`HYBRID_P3_NEARPEAK3`**",
            f"Register: **{REGISTER}** · runner=`{RUNNER_ID}` · base=`{BASE_ID}`",
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
            "scripts/meta_detect_hybrid_nearpeak3_stageb.py`",
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

    tgt = screen["target"] or {}
    decision = {
        "label": f"{DECISION_ID}_{generated[:10]}__{verdict}__NO_LIVE",
        "verdict": verdict,
        "register": REGISTER,
        "parents": list(PARENTS),
        "mech": MECH,
        "runner_id": RUNNER_ID,
        "target": screen["target"],
        "champion_hybrid": screen.get("champion_hybrid"),
        "ungated_ref": screen.get("ungated_ref"),
        "tipsoft_dual_track": screen.get("tipsoft_dual_track"),
        "sealed_delta_vs_ungated_pp": sealed_delta_vs_ungated,
        "optimize_live": optimize,
        "soft_keep": True,
        "broker": False,
        "path4_live": False,
        "wire": False,
    }
    decision_md = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: {generated[:10]} · Verdict: **`{verdict}`** · "
            f"target=**`{tgt.get('arm')}`**",
            f"Register: **{REGISTER}** · runner **`{RUNNER_ID}`**",
            "",
            "## HYBRID_P3_NEARPEAK3 vs live",
            "",
            f"- held CAGR lift: **{tgt.get('held_cagr_lift_pp')}** pp",
            f"- full CAGR lift: **{tgt.get('full_cagr_lift_pp')}** pp",
            f"- sealed MDD improve: **{tgt.get('sealed_mdd_improve_pp')}** pp",
            f"- tipY / tip1y: **{tgt.get('tip_ytd_cagr_lift_pp')}** / "
            f"**{tgt.get('tip_1y_cagr_lift_pp')}**",
            f"- sealed Δ vs ungated hybrid: **{sealed_delta_vs_ungated}** pp",
            "",
            "## Rule",
            "",
            "- Promote-gate twin remains Soft Exact T+1 + gated Soft-core T+0 carve.",
            "- 0kau tip Soft Exact T+1 HIT is dual-track evidence, not alone sufficient.",
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
        "target": "HYBRID_P3_NEARPEAK3",
        "target_verdict": (target or {}).get("verdict_vs_live"),
        "held_cagr_lift_pp": (target or {}).get("held_cagr_lift_pp"),
        "full_cagr_lift_pp": (target or {}).get("full_cagr_lift_pp"),
        "sealed_mdd_improve_pp": (target or {}).get("sealed_mdd_improve_pp"),
        "tip_ytd_cagr_lift_pp": (target or {}).get("tip_ytd_cagr_lift_pp"),
        "sealed_delta_vs_ungated_pp": sealed_delta_vs_ungated,
        "champion_hybrid": (champion or {}).get("arm"),
        "optimize_live": optimize,
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
