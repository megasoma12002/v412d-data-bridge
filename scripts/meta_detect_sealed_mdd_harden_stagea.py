#!/usr/bin/env python3
"""Meta-detect sealed-MDD harden Stage A (0kau).

Parent 0kat: DETECT_P3_THETA held↑ / tipY↑ but sealed MDD −0.50 → MDD_BLOCK.
This pack hardens detectors so optional blocks (esp. Path3 / FUSE) turn OFF
when Soft drawdown risk is elevated — aim to clear sealed MDD floor (−0.25pp).

Causal sealed-MDD gates (no lookahead):
  - Soft DD vs 63d peak (near-peak only)
  - Soft proxy_mdd63 floors (−5/−8/−10%）
  - COOL risk-on (not defending)
  - Lagged 5d Path3 premium sum ≥ 0 (recent carve not bleeding)

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

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "meta-detect-sealed-mdd-harden-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

ALIGN = ROOT / "repro" / "research-live-align-gap-stagea" / "outputs"
P3_SIG = (
    ROOT / "repro" / "fin-sat-path3-t0-dual-paper-observe" / "outputs" / "p3_t0_state_signal.csv"
)

CHARTER_ID = "META_DETECT_SEALED_MDD_HARDEN_STAGEA_CHARTER"
SCREEN_ID = "META_DETECT_SEALED_MDD_HARDEN_STAGEA_SCREEN"
DECISION_ID = "META_DETECT_SEALED_MDD_HARDEN_STAGEA_DECISION_PACK"
REGISTER = "0kau"
PARENTS = ("0kat", "0kas", "0kar")
MECH = "META_DETECT_SEALED_MDD_HARDEN"

BASE_ID = "STATIC_L3_LIVE_FUSE_COOL"
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


def _compose(
    r_l1: pd.Series,
    prem_fuse: pd.Series,
    prem_cool: pd.Series,
    prem_p3: pd.Series,
    i_fuse: pd.Series,
    i_cool: pd.Series,
    i_p3: pd.Series,
) -> pd.Series:
    return (
        r_l1
        + i_fuse.astype(float) * prem_fuse
        + i_cool.astype(float) * prem_cool
        + i_p3.astype(float) * prem_p3
    )


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()

    nav_l1 = _load_nav(ALIGN / "nav_L1_SOFT_T1.csv")
    nav_l2 = _load_nav(ALIGN / "nav_L2_SOFT_FUSE_T1.csv")
    nav_l3 = _load_nav(ALIGN / "nav_L3_LIVE_FUSE_COOL.csv")
    nav_l4 = _load_nav(ALIGN / "nav_L4_LIVE_P3_WITHIN.csv")
    nav0 = float(nav_l1["nav"].iloc[0])

    r1 = _returns(nav_l1)
    r2 = _returns(nav_l2)
    r3 = _returns(nav_l3)
    r4 = _returns(nav_l4)
    panel = pd.concat({"r1": r1, "r2": r2, "r3": r3, "r4": r4}, axis=1, join="inner").dropna(
        how="any"
    )
    prem_fuse = panel["r2"] - panel["r1"]
    prem_cool = panel["r3"] - panel["r2"]
    prem_p3 = panel["r4"] - panel["r3"]
    r_l1 = panel["r1"]

    proxy = _proxy_mdd63(nav_l1).reindex(panel.index).fillna(0.0)
    dd63 = _dd_from_peak(nav_l1, 63).reindex(panel.index).fillna(0.0)
    cool_exp = build_cool_c8_exposure(panel.index, proxy)
    risk_on = cool_exp >= 0.999
    defending = cool_exp < 0.999

    sig = pd.read_csv(P3_SIG, parse_dates=["date"])
    sig["date"] = pd.to_datetime(sig["date"]).dt.normalize()
    sig = sig.set_index("date").reindex(panel.index)
    trail = sig["trail_rel_63"].astype(float)
    p3_theta = (trail.abs() >= float(P3_THETA)).fillna(False)

    # Lagged Path3 premium health (causal: uses only past premiums)
    prem_p3_lag5 = prem_p3.shift(1).rolling(5, min_periods=3).sum().fillna(0.0)
    p3_not_bleeding = prem_p3_lag5 >= 0.0

    near_peak_3 = dd63 >= -0.03
    near_peak_5 = dd63 >= -0.05
    proxy_ok_05 = proxy > -0.05
    proxy_ok_08 = proxy > -0.08
    proxy_ok_10 = proxy > -0.10

    ones = pd.Series(True, index=panel.index)
    zeros = pd.Series(False, index=panel.index)

    policies: dict[str, tuple[pd.Series, pd.Series, pd.Series, str]] = {
        "STATIC_L3_LIVE_FUSE_COOL": (ones, ones, zeros, "Always Soft+FUSE+COOL (=live base)"),
        "REF_DETECT_P3_THETA": (
            ones,
            ones,
            p3_theta,
            "0kat baseline: live stack + P3 when |trail|≥θ (no MDD harden)",
        ),
        "REF_DETECT_FUSE_RISKON": (
            risk_on,
            ones,
            zeros,
            "0kat contrast: FUSE risk-on; COOL always; no P3",
        ),
        "P3_THETA_PROXY05": (
            ones,
            ones,
            p3_theta & proxy_ok_05,
            "P3 |trail|≥θ AND Soft proxy_mdd63 > −5%",
        ),
        "P3_THETA_PROXY08": (
            ones,
            ones,
            p3_theta & proxy_ok_08,
            "P3 |trail|≥θ AND Soft proxy_mdd63 > −8%",
        ),
        "P3_THETA_PROXY10": (
            ones,
            ones,
            p3_theta & proxy_ok_10,
            "P3 |trail|≥θ AND Soft proxy_mdd63 > −10%",
        ),
        "P3_THETA_NEARPEAK3": (
            ones,
            ones,
            p3_theta & near_peak_3,
            "P3 |trail|≥θ AND Soft within 3% of 63d peak",
        ),
        "P3_THETA_NEARPEAK5": (
            ones,
            ones,
            p3_theta & near_peak_5,
            "P3 |trail|≥θ AND Soft within 5% of 63d peak",
        ),
        "P3_THETA_RISKON": (
            ones,
            ones,
            p3_theta & risk_on,
            "P3 |trail|≥θ AND COOL risk-on (not defending)",
        ),
        "P3_THETA_NOT_BLEED": (
            ones,
            ones,
            p3_theta & p3_not_bleeding,
            "P3 |trail|≥θ AND lagged 5d prem_p3 sum ≥ 0",
        ),
        "P3_HARD_PEAK3_RISKON": (
            ones,
            ones,
            p3_theta & near_peak_3 & risk_on,
            "P3 |trail|≥θ AND near-peak3 AND risk-on",
        ),
        "P3_HARD_PEAK5_PROXY08": (
            ones,
            ones,
            p3_theta & near_peak_5 & proxy_ok_08,
            "P3 |trail|≥θ AND near-peak5 AND proxy > −8%",
        ),
        "P3_HARD_PEAK3_NOTBLEED": (
            ones,
            ones,
            p3_theta & near_peak_3 & p3_not_bleeding,
            "P3 |trail|≥θ AND near-peak3 AND not bleeding",
        ),
        "FUSE_RISKON_PROXY08": (
            risk_on & proxy_ok_08,
            ones,
            zeros,
            "FUSE only risk-on∩proxy>−8%; COOL always; no P3",
        ),
        "FUSE_RISKON_NEARPEAK5": (
            risk_on & near_peak_5,
            ones,
            zeros,
            "FUSE only risk-on∩near-peak5; COOL always; no P3",
        ),
        "COMBO_HARD_P3PEAK_FUSERISK": (
            risk_on & proxy_ok_08,
            ones,
            p3_theta & near_peak_3 & risk_on & p3_not_bleeding,
            "FUSE risk-on∩proxy08; COOL always; P3 peak3∩riskon∩notbleed",
        ),
        "COMBO_HARD_DEFEND_COOL": (
            risk_on & near_peak_5,
            defending | (~near_peak_5),
            p3_theta & near_peak_3 & risk_on,
            "FUSE riskon∩peak5; COOL when defending or not near-peak; P3 peak3∩riskon",
        ),
    }

    arms: dict[str, pd.DataFrame] = {}
    metas: dict[str, dict[str, Any]] = {}
    gate_rows: list[dict[str, Any]] = []

    for arm, (i_fuse, i_cool, i_p3, note) in policies.items():
        r = _compose(r_l1, prem_fuse, prem_cool, prem_p3, i_fuse, i_cool, i_p3)
        nav = _nav_from_returns(r, nav0)
        arms[arm] = nav
        nav.to_csv(OUT / f"nav_{arm}.csv", index=False)
        meta = {
            "note": note,
            "pct_fuse_on": round(float(i_fuse.mean()) * 100, 2),
            "pct_cool_on": round(float(i_cool.mean()) * 100, 2),
            "pct_p3_on": round(float(i_p3.mean()) * 100, 2),
            "n_days": int(len(panel)),
            "p3_theta": P3_THETA,
            "proxy_x": PROXY_X,
        }
        metas[arm] = meta
        gate_rows.append({"arm": arm, **meta})

    pd.DataFrame(gate_rows).to_csv(OUT / "detector_duty_cycle.csv", index=False)
    pd.DataFrame(
        {
            "date": panel.index,
            "proxy_mdd63": proxy.to_numpy(),
            "dd63_peak": dd63.to_numpy(),
            "cool_exp": cool_exp.to_numpy(),
            "risk_on": risk_on.astype(int).to_numpy(),
            "near_peak_3": near_peak_3.astype(int).to_numpy(),
            "near_peak_5": near_peak_5.astype(int).to_numpy(),
            "proxy_ok_08": proxy_ok_08.astype(int).to_numpy(),
            "p3_theta": p3_theta.astype(int).to_numpy(),
            "p3_not_bleeding": p3_not_bleeding.astype(int).to_numpy(),
            "prem_p3_lag5": prem_p3_lag5.to_numpy(),
            "trail_rel_63": trail.reindex(panel.index).to_numpy(),
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
        # Prefer sealed MDD first (this pack's objective), then held, then tip
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

    harden_rows = [r for r in rows if not str(r["arm"]).startswith("REF_")]
    ref_rows = [r for r in rows if str(r["arm"]).startswith("REF_")]
    champion = sorted(harden_rows, key=_rank_key)[0] if harden_rows else None
    best_ref = sorted(ref_rows, key=_rank_key)[0] if ref_rows else None

    hit_like = [r for r in harden_rows if r["verdict_vs_live"] in ("HIT", "HELD_HIT", "SOFT")]
    sealed_clear = [
        r
        for r in harden_rows
        if r["sealed_mdd_improve_pp"] is not None
        and float(r["sealed_mdd_improve_pp"]) >= SEALED_MDD_FLOOR_PP
    ]
    if hit_like:
        verdict = "SEALED_MDD_HARDEN_HIT"
    elif sealed_clear and champion and champion["verdict_vs_live"] != "MDD_BLOCK":
        verdict = f"SEALED_MDD_HARDEN_{champion['verdict_vs_live']}"
    elif sealed_clear:
        # cleared sealed floor but other gates fail
        verdict = "SEALED_MDD_CLEARED_OTHER_BLOCK"
    elif champion and champion["verdict_vs_live"] == "MDD_BLOCK":
        verdict = "SEALED_MDD_HARDEN_MDD_BLOCK"
    elif champion and champion["verdict_vs_live"] == "TIP_BLOCK":
        verdict = "SEALED_MDD_HARDEN_TIP_BLOCK"
    else:
        verdict = "SEALED_MDD_HARDEN_NO_EDGE"

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
                "pct_fuse": (r["meta"] or {}).get("pct_fuse_on"),
                "pct_cool": (r["meta"] or {}).get("pct_cool_on"),
                "pct_p3": (r["meta"] or {}).get("pct_p3_on"),
                "note": (r["meta"] or {}).get("note"),
            }
            for r in rows
        ]
    ).to_csv(OUT / "arms_vs_live.csv", index=False)

    if champion and champion.get("yearly"):
        pd.DataFrame(champion["yearly"]).to_csv(OUT / "yearly_champion_vs_live.csv", index=False)

    # Sealed improvement vs 0kat baseline
    ref_p3 = next((r for r in ref_rows if r["arm"] == "REF_DETECT_P3_THETA"), None)
    sealed_delta_vs_ref = None
    if champion and ref_p3:
        if (
            champion["sealed_mdd_improve_pp"] is not None
            and ref_p3["sealed_mdd_improve_pp"] is not None
        ):
            sealed_delta_vs_ref = round(
                float(champion["sealed_mdd_improve_pp"]) - float(ref_p3["sealed_mdd_improve_pp"]),
                4,
            )

    optimize = [
        "Objective: clear sealed MDD floor (−0.25pp) while keeping Soft shell + detector-gated blocks",
        (
            f"Harden champion `{champion['arm']}` → {champion['verdict_vs_live']} held "
            f"{champion['held_cagr_lift_pp']} tipY {champion['tip_ytd_cagr_lift_pp']} "
            f"sealedMDD {champion['sealed_mdd_improve_pp']}"
            if champion
            else "No harden champion"
        ),
        (
            f"0kat ref `{best_ref['arm']}` → {best_ref['verdict_vs_live']} "
            f"sealedMDD {best_ref['sealed_mdd_improve_pp']}"
            if best_ref
            else "No ref"
        ),
        (
            f"Sealed MDD delta vs REF_DETECT_P3_THETA = {sealed_delta_vs_ref} pp"
            if sealed_delta_vs_ref is not None
            else "No sealed delta vs ref"
        ),
        f"n_harden arms clearing sealed floor: {len(sealed_clear)} / {len(harden_rows)}",
        "Soft KEEP · Path4 OFF · broker false · no live wire this pack",
        "Next: if HIT/CLEARED → Stage B under hybrid promote twin; else tighter peak/bleed gates or Path3 OFF",
    ]

    screen = {
        "id": SCREEN_ID,
        "register": REGISTER,
        "parents": list(PARENTS),
        "generated_at_utc": generated,
        "mech": MECH,
        "verdict": verdict,
        "base": BASE_ID,
        "champion": {
            "arm": champion["arm"],
            "verdict_vs_live": champion["verdict_vs_live"],
            "held_cagr_lift_pp": champion["held_cagr_lift_pp"],
            "full_cagr_lift_pp": champion["full_cagr_lift_pp"],
            "sealed_mdd_improve_pp": champion["sealed_mdd_improve_pp"],
            "tip_ytd_cagr_lift_pp": champion["tip_ytd_cagr_lift_pp"],
            "tip_1y_cagr_lift_pp": champion["tip_1y_cagr_lift_pp"],
            "meta": champion["meta"],
        }
        if champion
        else None,
        "ref_0kat": {
            "arm": ref_p3["arm"],
            "verdict_vs_live": ref_p3["verdict_vs_live"],
            "held_cagr_lift_pp": ref_p3["held_cagr_lift_pp"],
            "sealed_mdd_improve_pp": ref_p3["sealed_mdd_improve_pp"],
            "tip_ytd_cagr_lift_pp": ref_p3["tip_ytd_cagr_lift_pp"],
        }
        if ref_p3
        else None,
        "sealed_delta_vs_ref_pp": sealed_delta_vs_ref,
        "n_sealed_clear": len(sealed_clear),
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
            "| Arm | vs live | held | full | sealed MDD↑ | tipY | fuse% | cool% | p3% |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for r in rs:
            m = r.get("meta") or {}
            lines.append(
                f"| {r['arm']} | {r['verdict_vs_live']} | {r['held_cagr_lift_pp']} | "
                f"{r['full_cagr_lift_pp']} | {r['sealed_mdd_improve_pp']} | "
                f"{r['tip_ytd_cagr_lift_pp']} | {m.get('pct_fuse_on', '')} | "
                f"{m.get('pct_cool_on', '')} | {m.get('pct_p3_on', '')} |"
            )
        return "\n".join(lines)

    charter_md = "\n".join(
        [
            f"# {CHARTER_ID}",
            "",
            f"Date: {generated[:10]}",
            "Status: **Stage A — sealed-MDD harden for meta-detect stack-select**",
            f"Register: **{REGISTER}** · Parents: {', '.join(PARENTS)}",
            f"Mech: `{MECH}`",
            "",
            "## Question",
            "",
            "Can causal drawdown / near-peak / bleed gates clear sealed MDD while "
            "keeping detector-selected FUSE/COOL/P3 blocks?",
            "",
            "## Method",
            "",
            "- Start from 0kat DETECT_P3_THETA / FUSE_RISKON baselines",
            "- AND-gate Path3/FUSE with Soft proxy_mdd63, near-peak DD63, risk-on, lagged prem_p3",
            "- Rank by sealed MDD first vs live Soft+FUSE+COOL",
            "",
            f"Label: `{CHARTER_ID}_{generated[:10]}__SEALED_MDD_HARDEN`",
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
            f"champion=**`{(champion or {}).get('arm')}`**",
            f"Register: **{REGISTER}** · mech=`{MECH}` · base=`{BASE_ID}`",
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
            "scripts/meta_detect_sealed_mdd_harden_stagea.py`",
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
        "ref_0kat": screen.get("ref_0kat"),
        "sealed_delta_vs_ref_pp": sealed_delta_vs_ref,
        "n_sealed_clear": len(sealed_clear),
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
            f"Date: {generated[:10]} · Verdict: **`{verdict}`** · champion=**`{ch.get('arm')}`**",
            f"Register: **{REGISTER}** · mech **`{MECH}`**",
            "",
            "## Harden champion vs live",
            "",
            f"- held CAGR lift: **{ch.get('held_cagr_lift_pp')}** pp",
            f"- full CAGR lift: **{ch.get('full_cagr_lift_pp')}** pp",
            f"- sealed MDD improve: **{ch.get('sealed_mdd_improve_pp')}** pp",
            f"- tipY / tip1y: **{ch.get('tip_ytd_cagr_lift_pp')}** / "
            f"**{ch.get('tip_1y_cagr_lift_pp')}**",
            f"- sealed Δ vs 0kat REF_DETECT_P3_THETA: **{sealed_delta_vs_ref}** pp",
            "",
            "## Rule",
            "",
            "- Soft always-on; optional blocks need MDD harden gates (near-peak / proxy / bleed).",
            "- Clearing sealed MDD is required before tip Soft promote.",
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
        "full_cagr_lift_pp": (champion or {}).get("full_cagr_lift_pp"),
        "sealed_mdd_improve_pp": (champion or {}).get("sealed_mdd_improve_pp"),
        "tip_ytd_cagr_lift_pp": (champion or {}).get("tip_ytd_cagr_lift_pp"),
        "sealed_delta_vs_ref_pp": sealed_delta_vs_ref,
        "n_sealed_clear": len(sealed_clear),
        "optimize_live": optimize,
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
