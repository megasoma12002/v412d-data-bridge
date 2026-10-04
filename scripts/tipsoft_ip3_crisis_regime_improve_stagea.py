#!/usr/bin/env python3
"""Crisis regime-conditional strategy improve Stage A (0kbm).

SOAK-SAFE · PARALLEL paper research — **signal / strategy design ≠ apply**.

Parents 0kbl / 0kbk / 0kbj / 0kbf:
- 0kbk ``CLIFF_GRIND_SPLIT_HIT`` — champ was GRIND specialist; no cliff specialist
- 0kbj ``HIST_OOS_OVERFIT_2020`` — 0kbi AND gate overfit to 2020
- 0kbl ``MAJOR_DD_ATLAS_PARTIAL`` — fuse_prem only partial cross-era
- 0kbf ``SOAK_OPEN`` — no tip Soft LIVE apply / Soft FIN/TEL / Path4 / broker

Question: can a **regime-conditional** router (CLIFF_RISK / GRIND_RISK / NORMAL)
plus specialized sleeves improve held CAGR vs L4 while cutting Mar2020/y2020 MDD,
without torching sealed / tipY and without worsening every non-2020 major DD?

Arms (Exact T+1 lag-1 causal synthetic exposure on L4 returns · ≤40):
1. Router — classify bar via lag-1 dd velocity / rvol spike / duration-in-dd
2. Cliff sleeve — short-horizon detectors → cash/scale when CLIFF_RISK
3. Grind sleeve — cool_defend / fuse_prem / rvol63 → milder scale when GRIND_RISK
4. Baselines — always-off · full-sample 0kbi AND · cliff-only · grind-only · vol-target

Verdict taxonomy:
- ``CRISIS_REGIME_IMPROVE_HIT`` — held+ AND (Mar or y2020 MDD↑) AND sealed OK
  AND not worse on ≥1 non-2020 major DD
- ``CRISIS_REGIME_IMPROVE_MDD_ONLY`` / ``_HELD_BLOCK`` / ``_NO_EDGE`` / ``_OVERFIT``

Hard constraints:
- Soft KEEP · Path4 OFF · broker false · Exact T+1
- no LIVE · no tip Soft promote · no year-oracle · soak freeze unchanged
- does **not** unlock soak · research path only

Repro: ``PYTHONPATH=scripts python3 scripts/tipsoft_ip3_crisis_regime_improve_stagea.py``
"""
from __future__ import annotations

import json
import re
import subprocess
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from e45_paper_harness import window_stats
from ops_repro_ssot import write_ops_and_repro_pointer, write_repro_pointer
from research_metric_helpers import mdd_delta_pp
from stagea_screen_helpers import (
    load_nav_csv as _load_nav,
    nav_from_returns as _nav_from_returns,
    pack_nav_windows as _pack,
    returns_from_nav as _returns,
    tip_lift as _tip,
    utc_now_z as _utc,
    window_delta as _delta,
)
from tipsoft_ip3_crisis_signal_helpers import (
    ALERT_Q,
    ALIGN,
    LIVESTACK,
    MAR2020_END,
    MAR2020_START,
    Y2020_END,
    Y2020_START,
    _alert_mask,
    _ann_vol,
    build_panel,
)

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "tipsoft-ip3-crisis-regime-improve-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "TIPSOFT_IP3_CRISIS_REGIME_IMPROVE_STAGEA_CHARTER"
SCREEN_ID = "TIPSOFT_IP3_CRISIS_REGIME_IMPROVE_STAGEA_SCREEN"
DECISION_ID = "TIPSOFT_IP3_CRISIS_REGIME_IMPROVE_STAGEA_DECISION_PACK"
REGISTER = "0kbm"
PARENTS = ("0kbl", "0kbk", "0kbj", "0kbf")
MECH = "TIPSOFT_IP3_CRISIS_REGIME_IMPROVE"
LABEL_TAG = "CRISIS_REGIME_IMPROVE_PARALLEL"

BASE_ID = "L4_LIVE_P3_WITHIN"
CHAMP_0KBI = "and::rvol63_l4&fuse_prem_neg5"

# Floors (paper Exact T+1)
HELD_CAGR_FLOOR_PP = 0.10
Y2020_MDD_IMPROVE_FLOOR_PP = 0.50
MAR2020_MDD_IMPROVE_FLOOR_PP = 0.50
SEALED_MDD_FLOOR_PP = -0.25
TIP_Y_FLOOR_PP = -1.0
CROSS_ERA_NOT_WORSE_PP = 0.0  # "not worse" = MDD improve ≥ 0 on a window
CROSS_ERA_IMPROVE_PP = 1e-6  # strict positive improve for HIT generalization
CROSS_ERA_DESTROY_PP = -1.0  # held-destroy-like threshold on window MDD worsen

# Major DD windows (from 0kbl atlas refs)
MAJOR_DD_WINDOWS: tuple[dict[str, Any], ...] = (
    {
        "tag": "TW_CN_2015",
        "era": "2015",
        "start": date(2015, 6, 1),
        "end": date(2015, 8, 31),
    },
    {
        "tag": "Q4_2018",
        "era": "2018",
        "start": date(2018, 10, 1),
        "end": date(2018, 12, 24),
    },
    {
        "tag": "BEAR_2022",
        "era": "2022",
        "start": date(2022, 1, 1),
        "end": date(2022, 10, 31),
    },
)

# Router grid (0kbk-aligned velocity / duration)
ROUTER_SPECS: tuple[dict[str, Any], ...] = (
    {
        "id": "RA",
        "vel_floor": 0.004,
        "cliff_max_days": 20,
        "grind_min_days": 40,
        "dd_enter": 0.05,
        "rvol_spike_mult": 1.25,
    },
    {
        "id": "RB",
        "vel_floor": 0.005,
        "cliff_max_days": 15,
        "grind_min_days": 40,
        "dd_enter": 0.05,
        "rvol_spike_mult": 1.35,
    },
    {
        "id": "RC",
        "vel_floor": 0.004,
        "cliff_max_days": 20,
        "grind_min_days": 60,
        "dd_enter": 0.08,
        "rvol_spike_mult": 1.25,
    },
)

CLIFF_SCALES = (0.0, 0.25, 0.5)
GRIND_SCALES = (0.5, 0.7, 0.85)


def _git_sha() -> str:
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )
    except Exception:
        return "UNKNOWN"


def _window_mdd(nav: pd.DataFrame, start: date, end: date, *, min_days: int = 10) -> float | None:
    st = window_stats(nav, start, end, min_days=min_days)
    mdd = st.get("max_drawdown")
    return None if mdd is None else float(mdd)


def _apply_exposure(base_r: pd.Series, exposure: pd.Series) -> pd.Series:
    e = exposure.reindex(base_r.index).fillna(1.0).clip(0.0, 1.0)
    return (e * base_r).astype(float)


def _vol_target_exposure(
    base_r: pd.Series,
    *,
    win: int,
    target: float,
    floor: float,
) -> pd.Series:
    vol = _ann_vol(base_r, win).replace(0.0, np.nan)
    return (float(target) / vol).clip(lower=float(floor), upper=1.0).fillna(1.0)


def _duration_in_dd(dd_mag: pd.Series, *, enter: float) -> pd.Series:
    """Lag-1 consecutive days with drawdown magnitude ≥ enter."""
    in_dd = (dd_mag >= float(enter)).astype(int)
    streak = np.zeros(len(in_dd), dtype=float)
    vals = in_dd.to_numpy()
    for i in range(len(vals)):
        if i == 0:
            streak[i] = float(vals[i])
        else:
            streak[i] = float(vals[i]) * (streak[i - 1] + 1.0) if vals[i] else 0.0
    return pd.Series(streak, index=dd_mag.index).shift(1)


def build_router_features(panel: pd.DataFrame) -> pd.DataFrame:
    """Causal lag-1 router inputs from crisis panel features."""
    p = panel.copy()
    p["date"] = pd.to_datetime(p["date"])
    p = p.set_index("date").sort_index()

    # dd63_* already lag-1 magnitudes (positive = stress)
    dd = p["dd63_l4"].fillna(0.0)
    # velocity of DD: deepening rate over ~5 bars (already lag-1 series → shift again for Δ)
    dd_vel = dd.diff(5).fillna(0.0) / 5.0
    # rvol spike vs rolling median of lag-1 rvol20
    r20 = p["rvol20_l4"].fillna(0.0)
    med = r20.rolling(252, min_periods=60).median()
    rvol_spike = (r20 / med.replace(0.0, np.nan)).fillna(1.0)

    out = pd.DataFrame(index=p.index)
    out["dd_mag"] = dd
    out["dd_vel"] = dd_vel
    out["rvol_spike"] = rvol_spike
    out["rvol20"] = r20
    out["rvol63"] = p["rvol63_l4"].fillna(0.0)
    out["atr"] = p["atr_like_20"].fillna(0.0)
    out["consec_down"] = p["consec_down_mkt"].fillna(0.0)
    out["below_ma200"] = p["below_ma200"].fillna(0.0)
    out["cool_defend"] = p["cool_defend_l1"].fillna(0.0)
    out["fuse_prem_neg5"] = p["fuse_prem_neg5"].fillna(0.0)
    out["neg_gap_ma200"] = p["neg_gap_ma200"].fillna(0.0)
    # duration uses enter=0.05 for feature table; routers recompute with their enter
    out["dur_dd_05"] = _duration_in_dd(dd, enter=0.05)
    out["dur_dd_08"] = _duration_in_dd(dd, enter=0.08)
    return out


def classify_regime(
    feats: pd.DataFrame,
    *,
    vel_floor: float,
    cliff_max_days: int,
    grind_min_days: int,
    dd_enter: float,
    rvol_spike_mult: float,
) -> pd.Series:
    """Bar-level CLIFF_RISK / GRIND_RISK / NORMAL — causal, no peek."""
    dur = feats["dur_dd_08"] if float(dd_enter) >= 0.08 - 1e-12 else feats["dur_dd_05"]
    # If enter differs from 05/08 presets, recompute
    if abs(float(dd_enter) - 0.05) > 1e-9 and abs(float(dd_enter) - 0.08) > 1e-9:
        dur = _duration_in_dd(feats["dd_mag"], enter=float(dd_enter))

    in_dd = feats["dd_mag"] >= float(dd_enter)
    cliff = (
        in_dd
        & (feats["dd_vel"] >= float(vel_floor))
        & (dur.fillna(0.0) <= float(cliff_max_days))
        & (feats["rvol_spike"] >= float(rvol_spike_mult))
    )
    grind = (
        in_dd
        & (dur.fillna(0.0) >= float(grind_min_days))
        & ~cliff
    )
    # Priority: CLIFF > GRIND > NORMAL
    lab = pd.Series("NORMAL", index=feats.index, dtype=object)
    lab = lab.mask(grind, "GRIND_RISK")
    lab = lab.mask(cliff, "CLIFF_RISK")
    return lab


def cliff_sleeve_alert(feats: pd.DataFrame) -> pd.Series:
    """Short-horizon cliff detectors (OR): rvol20, atr, consec_down, MA gap."""
    a_rvol = _alert_mask(feats["rvol20"], stress_high=True, q=ALERT_Q)
    a_atr = _alert_mask(feats["atr"], stress_high=True, q=ALERT_Q)
    a_consec = feats["consec_down"].fillna(0.0) >= 3.0
    a_ma = feats["below_ma200"].fillna(0.0) >= 0.5
    return (a_rvol | a_atr | a_consec | a_ma).fillna(False)


def grind_sleeve_alert(feats: pd.DataFrame) -> pd.Series:
    """Grind detectors (OR): cool_defend, fuse_prem, rvol63."""
    a_cool = feats["cool_defend"].fillna(0.0) >= 0.5
    a_fuse = _alert_mask(feats["fuse_prem_neg5"], stress_high=True, q=ALERT_Q)
    a_r63 = _alert_mask(feats["rvol63"], stress_high=True, q=ALERT_Q)
    return (a_cool | a_fuse | a_r63).fillna(False)


def and_0kbi_alert(panel: pd.DataFrame) -> pd.Series:
    """Full-sample 0kbi AND gate alert (rank-min of rvol63 & fuse_prem)."""
    p = panel.copy()
    p["date"] = pd.to_datetime(p["date"])
    p = p.set_index("date").sort_index()
    r63 = p["rvol63_l4"].rank(method="average", pct=True)
    fuse = p["fuse_prem_neg5"].rank(method="average", pct=True)
    score = pd.concat([r63, fuse], axis=1).min(axis=1)
    return _alert_mask(score, stress_high=True, q=ALERT_Q)


def regime_exposure(
    regime: pd.Series,
    *,
    cliff_alert: pd.Series,
    grind_alert: pd.Series,
    cliff_scale: float,
    grind_scale: float,
    cliff_only: bool = False,
    grind_only: bool = False,
) -> pd.Series:
    """Map regime + sleeve alerts → exposure in [0, 1]."""
    idx = regime.index
    exp = pd.Series(1.0, index=idx)
    c_fire = (regime == "CLIFF_RISK") & cliff_alert.reindex(idx).fillna(False)
    g_fire = (regime == "GRIND_RISK") & grind_alert.reindex(idx).fillna(False)
    if cliff_only:
        exp = exp.mask(c_fire, float(cliff_scale))
    elif grind_only:
        exp = exp.mask(g_fire, float(grind_scale))
    else:
        exp = exp.mask(g_fire, float(grind_scale))
        exp = exp.mask(c_fire, float(cliff_scale))  # cliff wins if both (shouldn't)
    return exp.clip(0.0, 1.0)


def _arm_verdict(
    *,
    held: float | None,
    sealed: float | None,
    tip_y: float | None,
    y20_mdd_imp: float | None,
    mar_mdd_imp: float | None,
    cross_era_ok: bool,
    cross_era_any_improve: bool,
    cross_era_any_not_worse: bool,
    cross_era_all_worse_or_flat: bool,
) -> str:
    if held is None or sealed is None:
        return "INCOMPLETE"
    sealed_ok = float(sealed) >= SEALED_MDD_FLOOR_PP
    tip_ok = tip_y is None or float(tip_y) >= TIP_Y_FLOOR_PP
    held_ok = float(held) >= HELD_CAGR_FLOOR_PP
    y20_ok = y20_mdd_imp is not None and float(y20_mdd_imp) >= Y2020_MDD_IMPROVE_FLOOR_PP
    mar_ok = mar_mdd_imp is not None and float(mar_mdd_imp) >= MAR2020_MDD_IMPROVE_FLOOR_PP
    mdd_ok = bool(y20_ok or mar_ok)
    if not sealed_ok:
        return "MDD_BLOCK"
    if tip_y is not None and float(tip_y) < TIP_Y_FLOOR_PP:
        return "TIP_BLOCK"
    if (
        held_ok
        and mdd_ok
        and sealed_ok
        and tip_ok
        and cross_era_any_improve
        and cross_era_any_not_worse
        and cross_era_ok
    ):
        return "HIT"
    # OVERFIT (anti-0kbj): held+ & 2020 MDD help but no strict non-2020 major-DD improve
    if held_ok and mdd_ok and sealed_ok and tip_ok and cross_era_all_worse_or_flat:
        return "OVERFIT"
    if mdd_ok and not held_ok:
        return "MDD_ONLY"
    if held_ok and not mdd_ok:
        return "HELD_BLOCK"
    if float(held) < -0.05:
        return "HELD_DESTROY"
    return "NO_EDGE"


def global_verdict_from_counts(
    *,
    n_hit: int,
    n_mdd_only: int,
    n_held_block: int,
    n_overfit: int,
    champ_verdict: str | None,
) -> str:
    """Map arm-level clears → pack-level CRISIS_REGIME_IMPROVE_* label."""
    if n_hit > 0 or champ_verdict == "HIT":
        return "CRISIS_REGIME_IMPROVE_HIT"
    if champ_verdict == "OVERFIT" or (n_overfit > 0 and n_mdd_only == 0 and n_hit == 0):
        # Prefer OVERFIT when champion itself overfits, or only overfits clear
        if champ_verdict == "OVERFIT":
            return "CRISIS_REGIME_IMPROVE_OVERFIT"
    if n_mdd_only > 0 or champ_verdict == "MDD_ONLY":
        return "CRISIS_REGIME_IMPROVE_MDD_ONLY"
    if n_overfit > 0:
        return "CRISIS_REGIME_IMPROVE_OVERFIT"
    if n_held_block > 0 or champ_verdict == "HELD_BLOCK":
        return "CRISIS_REGIME_IMPROVE_HELD_BLOCK"
    return "CRISIS_REGIME_IMPROVE_NO_EDGE"


def _cross_era_flags(imps: dict[str, float | None]) -> tuple[bool, bool, bool, bool, int, int]:
    """Return (any_strict_improve, any_not_worse, all_worse_or_flat, ok_not_destroy, n_improve, n_worse).

    Strict improve (>0) is required for HIT generalization (anti-0kbj OVERFIT).
    Flat-zero on all scored non-2020 windows with 2020 MDD help → OVERFIT.
    """
    vals = [v for v in imps.values() if v is not None]
    if not vals:
        return False, False, False, True, 0, 0
    n_imp = sum(1 for v in vals if float(v) > CROSS_ERA_IMPROVE_PP)
    n_not_worse = sum(1 for v in vals if float(v) >= CROSS_ERA_NOT_WORSE_PP)
    n_worse = sum(1 for v in vals if float(v) < CROSS_ERA_NOT_WORSE_PP)
    any_strict = n_imp >= 1
    any_not_worse = n_not_worse >= 1
    # all worse OR all flat (no strict improve) — flat-only is 2020-era specialization risk
    all_worse_or_flat = (n_imp == 0) and len(vals) > 0
    ok = not all(float(v) < CROSS_ERA_DESTROY_PP for v in vals)
    return any_strict, any_not_worse, all_worse_or_flat, ok, n_imp, n_worse


def build_arm_grid(
    base_r: pd.Series,
    panel: pd.DataFrame,
    feats: pd.DataFrame,
) -> tuple[dict[str, tuple[str, pd.Series, dict[str, Any]]], dict[str, Any]]:
    """Build ≤40 interpretable arms → (family, returns, meta)."""
    arms: dict[str, tuple[str, pd.Series, dict[str, Any]]] = {}
    c_alert = cliff_sleeve_alert(feats)
    g_alert = grind_sleeve_alert(feats)
    and_alert = and_0kbi_alert(panel)

    # --- Baselines ---
    arms["BASE_ALWAYS_OFF"] = (
        "BASE",
        base_r,
        {"router": None, "cliff_scale": None, "grind_scale": None},
    )
    exp_and_cash = pd.Series(np.where(and_alert.reindex(base_r.index).fillna(False), 0.0, 1.0), index=base_r.index)
    arms["BASE_AND_0KBI_CASH"] = (
        "BASE_AND",
        _apply_exposure(base_r, exp_and_cash),
        {"router": None, "note": CHAMP_0KBI},
    )
    exp_and_s50 = pd.Series(np.where(and_alert.reindex(base_r.index).fillna(False), 0.5, 1.0), index=base_r.index)
    arms["BASE_AND_0KBI_S50"] = (
        "BASE_AND",
        _apply_exposure(base_r, exp_and_s50),
        {"router": None, "note": CHAMP_0KBI},
    )

    # Cliff-only / grind-only under primary router RA
    ra = ROUTER_SPECS[0]
    reg_ra = classify_regime(feats, **{k: ra[k] for k in (
        "vel_floor", "cliff_max_days", "grind_min_days", "dd_enter", "rvol_spike_mult"
    )})
    for cs in (0.0, 0.25):
        name = f"BASE_CLIFFONLY_C{str(cs).replace('.', '')}"
        exp = regime_exposure(
            reg_ra, cliff_alert=c_alert, grind_alert=g_alert,
            cliff_scale=cs, grind_scale=1.0, cliff_only=True,
        )
        arms[name] = ("BASE_CLIFF", _apply_exposure(base_r, exp), {"router": "RA", "cliff_scale": cs})
    for gs in (0.5, 0.7):
        name = f"BASE_GRINDONLY_G{str(gs).replace('.', '')}"
        exp = regime_exposure(
            reg_ra, cliff_alert=c_alert, grind_alert=g_alert,
            cliff_scale=1.0, grind_scale=gs, grind_only=True,
        )
        arms[name] = ("BASE_GRIND", _apply_exposure(base_r, exp), {"router": "RA", "grind_scale": gs})

    arms["BASE_VOL_W20_T012_F03"] = (
        "BASE_VOL",
        _apply_exposure(base_r, _vol_target_exposure(base_r, win=20, target=0.12, floor=0.30)),
        {"router": None},
    )
    arms["BASE_VOL_W63_T014_F04"] = (
        "BASE_VOL",
        _apply_exposure(base_r, _vol_target_exposure(base_r, win=63, target=0.14, floor=0.40)),
        {"router": None},
    )

    # --- Regime-conditional router × sleeve scales ---
    regime_cache: dict[str, pd.Series] = {"RA": reg_ra}
    for rs in ROUTER_SPECS[1:]:
        regime_cache[rs["id"]] = classify_regime(
            feats,
            vel_floor=rs["vel_floor"],
            cliff_max_days=rs["cliff_max_days"],
            grind_min_days=rs["grind_min_days"],
            dd_enter=rs["dd_enter"],
            rvol_spike_mult=rs["rvol_spike_mult"],
        )

    for rs in ROUTER_SPECS:
        rid = rs["id"]
        reg = regime_cache[rid]
        for cs in CLIFF_SCALES:
            for gs in GRIND_SCALES:
                name = (
                    f"R_{rid}_C{str(cs).replace('.', '')}"
                    f"_G{str(gs).replace('.', '')}"
                )
                exp = regime_exposure(
                    reg,
                    cliff_alert=c_alert,
                    grind_alert=g_alert,
                    cliff_scale=cs,
                    grind_scale=gs,
                )
                arms[name] = (
                    "ROUTER",
                    _apply_exposure(base_r, exp),
                    {
                        "router": rid,
                        "cliff_scale": cs,
                        "grind_scale": gs,
                        "pct_cliff": round(float((reg == "CLIFF_RISK").mean()) * 100, 2),
                        "pct_grind": round(float((reg == "GRIND_RISK").mean()) * 100, 2),
                    },
                )

    # Count check
    n = len(arms)
    assert n <= 40, f"arm grid too large: {n}"
    meta = {
        "n_arms": n,
        "n_router": sum(1 for _, (fam, _, _) in arms.items() if fam == "ROUTER"),
        "n_base": sum(1 for _, (fam, _, _) in arms.items() if fam.startswith("BASE")),
        "routers": list(ROUTER_SPECS),
        "cliff_scales": list(CLIFF_SCALES),
        "grind_scales": list(GRIND_SCALES),
        "regime_pct": {
            rid: {
                "CLIFF_RISK": round(float((regime_cache[rid] == "CLIFF_RISK").mean()) * 100, 2),
                "GRIND_RISK": round(float((regime_cache[rid] == "GRIND_RISK").mean()) * 100, 2),
                "NORMAL": round(float((regime_cache[rid] == "NORMAL").mean()) * 100, 2),
            }
            for rid in regime_cache
        },
    }
    # Persist primary regime mask
    regime_df = pd.DataFrame({"date": feats.index})
    for rid, reg in regime_cache.items():
        regime_df[f"regime_{rid}"] = reg.reindex(feats.index).to_numpy()
    regime_df["cliff_alert"] = c_alert.reindex(feats.index).fillna(False).astype(int).to_numpy()
    regime_df["grind_alert"] = g_alert.reindex(feats.index).fillna(False).astype(int).to_numpy()
    regime_df["and_0kbi_alert"] = and_alert.reindex(feats.index).fillna(False).astype(int).to_numpy()
    meta["_regime_df"] = regime_df
    meta["_regime_cache"] = regime_cache
    return arms, meta


def _patch_register(verdict: str, champ: dict[str, Any] | None, day: str, tip_sha: str) -> None:
    reg = OPS / "HUMAN_DECISION_REGISTER.md"
    rt = reg.read_text(encoding="utf-8")
    c = champ or {}
    new_row = (
        f"| 0kbm | crisis **regime-conditional** improve (router×cliff/grind sleeves) | "
        f"**STAGE A `{verdict}`** ({day}) | "
        f"Parents 0kbl/0kbk/0kbj/0kbf · **CRISIS_REGIME_IMPROVE/PARALLEL** · Exact T+1 lag-1 · "
        f"champ `{c.get('arm')}` held **{c.get('held_vs_base')}** · "
        f"y2020 MDD↑ **{c.get('y2020_mdd_improve_pp')}** · "
        f"Mar2020 MDD↑ **{c.get('mar2020_mdd_improve_pp')}** · "
        f"sealed **{c.get('sealed_vs_base')}** · cross-era improve_n **{c.get('cross_era_n_improve')}** · "
        f"**does not unlock soak** · Soft KEEP · Path4 OFF · no live · tip `{tip_sha[:12]}` · "
        f"`{DECISION_ID}.md` |"
    )
    lines = rt.splitlines()
    out: list[str] = []
    replaced = False
    for line in lines:
        if line.startswith("| 0kbm |"):
            out.append(new_row)
            replaced = True
        else:
            out.append(line)
    if not replaced:
        # Insert after 0kbf row when present
        row_0kbf = None
        for i, line in enumerate(out):
            if line.startswith("| 0kbf |"):
                row_0kbf = i
                break
        if row_0kbf is not None:
            out.insert(row_0kbf + 1, new_row)
        else:
            # fallback: after header separator
            for i, line in enumerate(out):
                if line.startswith("|---"):
                    out.insert(i + 1, new_row)
                    break
    reg.write_text("\n".join(out) + "\n", encoding="utf-8")


def _patch_ops_status(verdict: str, champ: dict[str, Any] | None, day: str) -> None:
    ops = OPS / "OPS_STATUS.md"
    ot = ops.read_text(encoding="utf-8")
    c = champ or {}
    line = (
        f"**Crisis regime improve (CRISIS_REGIME_IMPROVE/PARALLEL {day}):** Stage A **`{verdict}`** · "
        f"register **0kbm** · champ `{c.get('arm')}` held **{c.get('held_vs_base')}** · "
        f"y2020 MDD↑ **{c.get('y2020_mdd_improve_pp')}** · "
        f"Mar2020 MDD↑ **{c.get('mar2020_mdd_improve_pp')}** · "
        f"cross-era improve_n **{c.get('cross_era_n_improve')}** · "
        f"**does not unlock soak freeze** · Soft KEEP · Path4 OFF · no live · "
        f"`{DECISION_ID}.md`  "
    )
    ot2, n = re.subn(
        r"\*\*Crisis regime improve \(CRISIS_REGIME_IMPROVE/PARALLEL [^)]+\):\*\*.*",
        line,
        ot,
        count=1,
    )
    if n:
        ops.write_text(ot2, encoding="utf-8")
        return
    needle = "DD_SWITCH soak gate (2026-10-03 cadence):"
    idx = ot.find(needle)
    if idx < 0:
        needle = "tip Soft LIVE STABILIZE"
        idx = ot.find(needle)
    if idx >= 0:
        end = ot.find("\n", idx) + 1
        ops.write_text(ot[:end] + line + "\n" + ot[end:], encoding="utf-8")


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()
    day = generated[:10]
    tip_sha = _git_sha()

    l4_path = ALIGN / "nav_L4_LIVE_P3_WITHIN.csv"
    if not l4_path.exists():
        l4_path = LIVESTACK / "nav_LIVE_P3_WITHIN.csv"
    base_nav = _load_nav(l4_path)
    nav0 = float(base_nav["nav"].iloc[0])
    base_r = _returns(base_nav)
    base_w = _pack(base_nav)

    panel, panel_meta = build_panel()
    feats = build_router_features(panel)
    feats.to_csv(OUT / "router_features.csv")

    arms, grid_meta = build_arm_grid(base_r, panel, feats)
    regime_df: pd.DataFrame = grid_meta.pop("_regime_df")
    grid_meta.pop("_regime_cache", None)
    regime_df.to_csv(OUT / "regime_masks.csv", index=False)
    (OUT / "grid_meta.json").write_text(
        json.dumps({k: v for k, v in grid_meta.items() if not str(k).startswith("_")}, indent=2)
        + "\n",
        encoding="utf-8",
    )

    base_y20_mdd = _window_mdd(base_nav, Y2020_START, Y2020_END)
    base_mar_mdd = _window_mdd(base_nav, MAR2020_START, MAR2020_END, min_days=10)
    base_era_mdd = {
        w["era"]: _window_mdd(base_nav, w["start"], w["end"], min_days=10)
        for w in MAJOR_DD_WINDOWS
    }

    rows: list[dict[str, Any]] = []
    arms_nav: dict[str, pd.DataFrame] = {BASE_ID: base_nav}
    base_nav.to_csv(OUT / f"nav_{BASE_ID}.csv", index=False)

    for name, (fam, r, meta) in arms.items():
        r = r.reindex(base_r.index).fillna(0.0)
        nav = _nav_from_returns(r, nav0)
        arms_nav[name] = nav
        chal_w = _pack(nav)
        d_base = _delta(base_w, chal_w)
        tip = _tip(base_nav, nav)
        y20_mdd = _window_mdd(nav, Y2020_START, Y2020_END)
        mar_mdd = _window_mdd(nav, MAR2020_START, MAR2020_END, min_days=10)
        y20_imp = (
            None
            if base_y20_mdd is None or y20_mdd is None
            else round(float(mdd_delta_pp(base_y20_mdd, y20_mdd)), 4)
        )
        mar_imp = (
            None
            if base_mar_mdd is None or mar_mdd is None
            else round(float(mdd_delta_pp(base_mar_mdd, mar_mdd)), 4)
        )
        era_imps: dict[str, float | None] = {}
        for w in MAJOR_DD_WINDOWS:
            era = w["era"]
            bm = base_era_mdd[era]
            cm = _window_mdd(nav, w["start"], w["end"], min_days=10)
            era_imps[era] = (
                None
                if bm is None or cm is None
                else round(float(mdd_delta_pp(bm, cm)), 4)
            )
        any_imp, any_nw, all_flat, era_ok, n_imp, n_worse = _cross_era_flags(era_imps)
        held = d_base["heldout_2019_plus"]["cagr_lift_pp"]
        sealed = d_base["sealed_2023_plus"]["mdd_improve_pp"]
        tip_y = (tip.get("ytd") or {}).get("cagr_lift_pp")
        full_cagr = d_base["full"]["cagr_lift_pp"]
        verd = _arm_verdict(
            held=held,
            sealed=sealed,
            tip_y=tip_y,
            y20_mdd_imp=y20_imp,
            mar_mdd_imp=mar_imp,
            cross_era_ok=era_ok,
            cross_era_any_improve=any_imp,
            cross_era_any_not_worse=any_nw,
            cross_era_all_worse_or_flat=all_flat,
        )
        nz = base_r.abs() > 1e-12
        mean_exp = (
            float((r[nz] / base_r[nz]).clip(-0.01, 1.5).mean()) if int(nz.sum()) else 1.0
        )
        rows.append(
            {
                "arm": name,
                "family": fam,
                "verdict": verd,
                "held_vs_base": held,
                "full_cagr_vs_base": full_cagr,
                "sealed_vs_base": sealed,
                "tipY_vs_base": tip_y,
                "y2020_mdd": None if y20_mdd is None else round(float(y20_mdd), 6),
                "y2020_mdd_improve_pp": y20_imp,
                "mar2020_mdd": None if mar_mdd is None else round(float(mar_mdd), 6),
                "mar2020_mdd_improve_pp": mar_imp,
                "mdd_2015_improve_pp": era_imps.get("2015"),
                "mdd_2018_improve_pp": era_imps.get("2018"),
                "mdd_2022_improve_pp": era_imps.get("2022"),
                "cross_era_n_improve": n_imp,
                "cross_era_n_worse": n_worse,
                "cross_era_any_improve": any_imp,
                "cross_era_any_not_worse": any_nw,
                "cross_era_all_worse_or_flat": all_flat,
                "mean_exposure": round(mean_exp, 4),
                "router": meta.get("router"),
                "cliff_scale": meta.get("cliff_scale"),
                "grind_scale": meta.get("grind_scale"),
                "is_ref": name == "BASE_ALWAYS_OFF",
                "hit_clear": verd == "HIT",
                "mdd_help": bool(
                    (y20_imp is not None and y20_imp >= Y2020_MDD_IMPROVE_FLOOR_PP)
                    or (mar_imp is not None and mar_imp >= MAR2020_MDD_IMPROVE_FLOOR_PP)
                ),
                "held_ok": held is not None and float(held) >= HELD_CAGR_FLOOR_PP,
                "sealed_ok": sealed is not None and float(sealed) >= SEALED_MDD_FLOOR_PP,
            }
        )

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "arms_crisis_regime_improve.csv", index=False)
    mech = df[~df.is_ref].copy()
    by_fam = (
        mech.groupby("family")
        .agg(
            n=("arm", "count"),
            n_hit=("hit_clear", "sum"),
            n_mdd_help=("mdd_help", "sum"),
            n_held_ok=("held_ok", "sum"),
            max_held=("held_vs_base", "max"),
            max_y20_mdd_imp=("y2020_mdd_improve_pp", "max"),
            max_mar_mdd_imp=("mar2020_mdd_improve_pp", "max"),
            max_sealed=("sealed_vs_base", "max"),
            max_cross_era_n=("cross_era_n_improve", "max"),
        )
        .reset_index()
    )
    by_fam.to_csv(OUT / "family_summary.csv", index=False)

    ranked = mech.sort_values(
        by=[
            "hit_clear",
            "held_ok",
            "mdd_help",
            "cross_era_any_improve",
            "held_vs_base",
            "mar2020_mdd_improve_pp",
            "y2020_mdd_improve_pp",
            "cross_era_n_improve",
            "sealed_vs_base",
        ],
        ascending=[False, False, False, False, False, False, False, False, False],
    )
    top = ranked.head(25)
    top.to_csv(OUT / "top_arms.csv", index=False)
    hits = mech[mech.verdict == "HIT"]
    hits.to_csv(OUT / "hits.csv", index=False)
    mdd_only = mech[mech.verdict == "MDD_ONLY"]
    mdd_only.to_csv(OUT / "mdd_only.csv", index=False)
    overfit = mech[mech.verdict == "OVERFIT"]
    overfit.to_csv(OUT / "overfit.csv", index=False)

    hits_n = int(hits.shape[0])
    mdd_only_n = int(mdd_only.shape[0])
    held_block_n = int((mech.verdict == "HELD_BLOCK").sum())
    overfit_n = int(overfit.shape[0])
    no_edge_n = int((mech.verdict == "NO_EDGE").sum())

    if hits_n > 0:
        crow = hits.sort_values(
            by=["held_vs_base", "mar2020_mdd_improve_pp", "cross_era_n_improve"],
            ascending=[False, False, False],
        ).iloc[0]
    elif mdd_only_n > 0:
        crow = mdd_only.sort_values(
            by=["held_vs_base", "mar2020_mdd_improve_pp", "cross_era_n_improve"],
            ascending=[False, False, False],
        ).iloc[0]
    elif overfit_n > 0:
        crow = overfit.sort_values(
            by=["held_vs_base", "mar2020_mdd_improve_pp"], ascending=[False, False]
        ).iloc[0]
    elif held_block_n > 0:
        crow = mech[mech.verdict == "HELD_BLOCK"].sort_values(
            by=["held_vs_base"], ascending=[False]
        ).iloc[0]
    else:
        crow = ranked.iloc[0] if len(ranked) else None

    champ = None if crow is None else crow.to_dict()
    if champ:
        arms_nav[champ["arm"]].to_csv(OUT / f"nav_{champ['arm']}.csv", index=False)

    verdict = global_verdict_from_counts(
        n_hit=hits_n,
        n_mdd_only=mdd_only_n,
        n_held_block=held_block_n,
        n_overfit=overfit_n,
        champ_verdict=None if not champ else str(champ.get("verdict")),
    )

    prior = {
        "0kbl": {
            "register": "0kbl",
            "verdict": "MAJOR_DD_ATLAS_PARTIAL",
            "note": "fuse_prem only partial cross-era; signal≠apply",
        },
        "0kbk": {
            "register": "0kbk",
            "verdict": "CLIFF_GRIND_SPLIT_HIT",
            "note": "champ GRIND specialist; no cliff specialist — motivates regime sleeves",
        },
        "0kbj": {
            "register": "0kbj",
            "verdict": "IP3_CRISIS_SIGNAL_HIST_OOS_OVERFIT_2020",
            "note": "0kbi AND gate hist OOS overfit 2020 — motivates cross-era floors",
        },
        "0kbi": {
            "register": "0kbi",
            "verdict": "IP3_Y2020_CRISIS_SIGNAL_REFINE_HIT",
            "note": f"AND champ `{CHAMP_0KBI}` reused as full-sample baseline",
        },
        "0kbf": {
            "register": "0kbf",
            "verdict": "SOAK_OPEN",
            "note": "soak freeze unchanged — this pack does not unlock SOAK_PASS",
        },
        "0kbg": {
            "register": "0kbg",
            "verdict": "IP3_Y2020_CRISIS_SANDBOX_MDD_ONLY",
            "note": "uniform overlays hurt held — regime-conditional is the design bet",
        },
    }

    base_diag = {
        "base_id": BASE_ID,
        "base_path": str(l4_path.relative_to(ROOT)),
        "base_y2020_mdd": base_y20_mdd,
        "base_mar2020_mdd": base_mar_mdd,
        "base_era_mdd": base_era_mdd,
        "mar2020_window": [str(MAR2020_START), str(MAR2020_END)],
        "major_dd_windows": [
            {
                "tag": w["tag"],
                "era": w["era"],
                "start": str(w["start"]),
                "end": str(w["end"]),
            }
            for w in MAJOR_DD_WINDOWS
        ],
        "held_floor_pp": HELD_CAGR_FLOOR_PP,
        "y2020_mdd_improve_floor_pp": Y2020_MDD_IMPROVE_FLOOR_PP,
        "mar2020_mdd_improve_floor_pp": MAR2020_MDD_IMPROVE_FLOOR_PP,
        "sealed_mdd_floor_pp": SEALED_MDD_FLOOR_PP,
        "tip_y_floor_pp": TIP_Y_FLOOR_PP,
        "panel_meta": panel_meta,
        "grid_meta": grid_meta,
    }
    (OUT / "base_diag.json").write_text(json.dumps(base_diag, indent=2, default=str) + "\n", encoding="utf-8")

    optimize = [
        "Objective: regime-conditional crisis sleeves on L4 — held+ with Mar/y2020 MDD↑ and ≥1 non-2020 major DD not-worse",
        (
            f"Champion `{champ['arm']}` fam={champ['family']} held={champ['held_vs_base']} "
            f"y2020MDD↑={champ['y2020_mdd_improve_pp']} Mar2020MDD↑={champ['mar2020_mdd_improve_pp']} "
            f"sealed={champ['sealed_vs_base']} tipY={champ['tipY_vs_base']} "
            f"cross_era_imp={champ['cross_era_n_improve']} verdict={champ['verdict']}"
            if champ
            else "No champion"
        ),
        f"Clears: HIT={hits_n} · MDD_ONLY={mdd_only_n} · OVERFIT={overfit_n} · "
        f"HELD_BLOCK={held_block_n} · NO_EDGE={no_edge_n} / mech={len(mech)} (grid≤40)",
        f"Router pct RA cliff/grind/normal={grid_meta['regime_pct'].get('RA')}",
        "vs priors: 0kbk SPLIT_HIT (regime tools differ) · 0kbj OVERFIT_2020 · 0kbl PARTIAL · 0kbg MDD_ONLY",
        "Disposition: does **not** unlock soak freeze · does **not** recommend LIVE wire · research path only",
        "Soft KEEP · Path4 OFF · broker false · no tip Soft promote · no year-oracle",
    ]

    screen = {
        "id": SCREEN_ID,
        "register": REGISTER,
        "parents": list(PARENTS),
        "generated_at_utc": generated,
        "tip_sha": tip_sha,
        "mech": MECH,
        "label_tag": LABEL_TAG,
        "verdict": verdict,
        "soak_unlock": False,
        "live_wire_recommend": False,
        "signal_not_apply": True,
        "n_mech_screened": len(mech),
        "n_hit": hits_n,
        "n_mdd_only": mdd_only_n,
        "n_overfit": overfit_n,
        "n_held_block": held_block_n,
        "n_no_edge": no_edge_n,
        "base": base_diag,
        "prior_chain": prior,
        "family_summary": by_fam.to_dict(orient="records"),
        "champion": champ,
        "top_arms": top.to_dict(orient="records"),
        "optimize_live": optimize,
        "soft_keep": True,
        "path4_live": False,
        "broker": False,
        "label": f"{SCREEN_ID}_{day}__{verdict}__{LABEL_TAG}",
    }
    (OUT / "screen.json").write_text(json.dumps(screen, indent=2, default=str) + "\n", encoding="utf-8")

    charter_md = "\n".join(
        [
            f"# {CHARTER_ID}",
            "",
            f"Date: {day}",
            f"Register: **{REGISTER}** · Parents: {', '.join(PARENTS)}",
            f"Label: **{LABEL_TAG}** · SOAK-SAFE parallel · **signal ≠ apply**",
            f"Tip SHA: `{tip_sha}`",
            "",
            "## Question",
            "",
            "Can a **regime-conditional** router (CLIFF_RISK / GRIND_RISK / NORMAL) plus "
            "specialized cliff/grind sleeves improve held CAGR vs L4 while cutting "
            "Mar2020/y2020 MDD, without torching sealed/tipY and without worsening "
            "every non-2020 major DD (2015 / 2018 / 2022)?",
            "",
            "## Prior chain (do not contradict)",
            "",
            "- 0kbg overlays MDD_ONLY (hurt held)",
            "- 0kbi SIGNAL_HIT refine but 0kbj HIST_OOS_OVERFIT_2020",
            "- 0kbk CLIFF_GRIND_SPLIT_HIT — different tools; champ was GRIND specialist; no cliff specialist",
            "- 0kbl MAJOR_DD_ATLAS_PARTIAL — fuse_prem only partial cross-era",
            "- Soak 0kbf SOAK_OPEN: no tip Soft LIVE apply / Soft FIN/TEL / Path4 / broker / year-oracle",
            "",
            "## Design (paper / Exact T+1 lag-1)",
            "",
            "1. **Router** — lag-1 dd velocity · rvol spike · duration-in-dd → CLIFF_RISK / GRIND_RISK / NORMAL",
            "2. **Cliff sleeve** — rvol20 / atr / consec_down / MA gap → cash/scale when CLIFF_RISK",
            "3. **Grind sleeve** — cool_defend / fuse_prem / rvol63 → milder scale when GRIND_RISK",
            "4. **Baselines** — always-off · full-sample 0kbi AND · cliff-only · grind-only · vol-target",
            f"5. Grid small & interpretable (n_arms={grid_meta['n_arms']} ≤ 40)",
            "",
            "## Floors",
            "",
            f"- held CAGR vs L4 ≥ **+{HELD_CAGR_FLOOR_PP}** pp",
            f"- Mar2020 or y2020 MDD improve ≥ **{MAR2020_MDD_IMPROVE_FLOOR_PP}** / "
            f"**{Y2020_MDD_IMPROVE_FLOOR_PP}** pp",
            f"- sealed MDD floor ≥ **{SEALED_MDD_FLOOR_PP}** pp · tipY ≥ **{TIP_Y_FLOOR_PP}** pp",
            "- Cross-era: ≥1 of 2015/2018/2022 MDD **strict improve (>0)** for HIT; "
            "flat/all-worse with 2020 MDD help → OVERFIT (anti-0kbj)",
            "",
            "## Hard constraints",
            "",
            "- Soft KEEP · Path4 OFF · broker false · Exact T+1",
            "- no LIVE · no tip Soft promote · no year-oracle",
            "- does **not** unlock soak freeze · research path only",
            "",
            f"Label: `{CHARTER_ID}_{day}__{LABEL_TAG}`",
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
                "label_tag": LABEL_TAG,
                "date": day,
                "tip_sha": tip_sha,
                "n_arms": grid_meta["n_arms"],
                "forbidden": [
                    "live_wire",
                    "tip_soft_promote",
                    "soft_fin_tel_accept",
                    "path4_live",
                    "broker",
                    "year_oracle",
                    "soak_unlock",
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
        f"Date: {day} · Verdict: **`{verdict}`** · champion=**`{(champ or {}).get('arm')}`**",
        f"Register: **{REGISTER}** · **{LABEL_TAG}** · mech={len(mech)} · "
        f"HIT={hits_n} · MDD_ONLY={mdd_only_n} · OVERFIT={overfit_n} · "
        f"HELD_BLOCK={held_block_n} · NO_EDGE={no_edge_n}",
        f"Tip SHA: `{tip_sha}`",
        "",
        "## Base",
        "",
        f"- `{BASE_ID}` path `{base_diag['base_path']}`",
        f"- y2020 MDD **{base_y20_mdd}** · Mar2020 MDD **{base_mar_mdd}** "
        f"({MAR2020_START}→{MAR2020_END})",
        f"- era MDD base: 2015={base_era_mdd.get('2015')} · "
        f"2018={base_era_mdd.get('2018')} · 2022={base_era_mdd.get('2022')}",
        f"- floors: held≥**{HELD_CAGR_FLOOR_PP}** · y2020/Mar MDD↑≥**{Y2020_MDD_IMPROVE_FLOOR_PP}** · "
        f"sealed≥**{SEALED_MDD_FLOOR_PP}** · tipY≥**{TIP_Y_FLOOR_PP}**",
        f"- router RA pct: {grid_meta['regime_pct'].get('RA')}",
        "",
        "## Prior chain",
        "",
    ]
    for k, v in prior.items():
        screen_md.append(f"- {k}: `{v['verdict']}` — {v['note']}")
    screen_md += [
        "",
        "## Family summary",
        "",
        "| Family | n | HIT | MDD help | held+ | max held | max y20 MDD↑ | max Mar MDD↑ | max sealed | max cross-era n |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in by_fam.to_dict(orient="records"):
        screen_md.append(
            f"| {r['family']} | {r['n']} | {int(r['n_hit'])} | {int(r['n_mdd_help'])} | "
            f"{int(r['n_held_ok'])} | {r['max_held']} | {r['max_y20_mdd_imp']} | "
            f"{r['max_mar_mdd_imp']} | {r['max_sealed']} | {int(r['max_cross_era_n'])} |"
        )
    screen_md += [
        "",
        "## Top arms",
        "",
        "| Arm | fam | held | y2020 MDD↑ | Mar2020 MDD↑ | 2015 | 2018 | 2022 | sealed | tipY | verdict |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for r in top.to_dict(orient="records"):
        screen_md.append(
            f"| {r['arm']} | {r['family']} | {r['held_vs_base']} | "
            f"{r['y2020_mdd_improve_pp']} | {r['mar2020_mdd_improve_pp']} | "
            f"{r['mdd_2015_improve_pp']} | {r['mdd_2018_improve_pp']} | "
            f"{r['mdd_2022_improve_pp']} | {r['sealed_vs_base']} | "
            f"{r['tipY_vs_base']} | {r['verdict']} |"
        )
    screen_md += [
        "",
        "## Optimize / disposition",
        "",
        *[f"{i}. {line}" for i, line in enumerate(optimize, 1)],
        "",
        "Repro: `PYTHONPATH=scripts python3 scripts/tipsoft_ip3_crisis_regime_improve_stagea.py`",
        "",
        f"Label: `{screen['label']}`",
        "",
    ]
    write_ops_and_repro_pointer(
        OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", "\n".join(screen_md), kind="screen"
    )
    (OPS / f"{SCREEN_ID}.json").write_text(
        json.dumps(screen, indent=2, default=str) + "\n", encoding="utf-8"
    )
    write_repro_pointer(OPS / f"{SCREEN_ID}.json", REP / f"{SCREEN_ID}.json", kind="screen")

    decision_md = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: {day} · Verdict: **`{verdict}`** · champion=**`{(champ or {}).get('arm')}`**",
            f"Register: **{REGISTER}** · Parents: {', '.join(PARENTS)} · **{LABEL_TAG}**",
            f"Tip SHA: `{tip_sha}`",
            "",
            "## Result",
            "",
            (
                f"- family: **{(champ or {}).get('family')}** · router **{(champ or {}).get('router')}**\n"
                f"- held vs L4: **{(champ or {}).get('held_vs_base')}**\n"
                f"- y2020 MDD improve: **{(champ or {}).get('y2020_mdd_improve_pp')}** "
                f"(base MDD {base_y20_mdd})\n"
                f"- Mar2020 MDD improve: **{(champ or {}).get('mar2020_mdd_improve_pp')}** "
                f"(base MDD {base_mar_mdd}; window {MAR2020_START}→{MAR2020_END})\n"
                f"- cross-era MDD↑: 2015 **{(champ or {}).get('mdd_2015_improve_pp')}** · "
                f"2018 **{(champ or {}).get('mdd_2018_improve_pp')}** · "
                f"2022 **{(champ or {}).get('mdd_2022_improve_pp')}** "
                f"(improve_n **{(champ or {}).get('cross_era_n_improve')}**)\n"
                f"- sealed **{(champ or {}).get('sealed_vs_base')}** · "
                f"tipY **{(champ or {}).get('tipY_vs_base')}**\n"
                f"- clears: HIT **{hits_n}** · MDD_ONLY **{mdd_only_n}** · OVERFIT **{overfit_n}** · "
                f"HELD_BLOCK **{held_block_n}** · NO_EDGE **{no_edge_n}**"
                if champ
                else f"- No clear · mech={len(mech)}"
            ),
            "",
            "## vs L4 / prior overlays",
            "",
            "- vs L4: synthetic exposure challengers on Exact T+1 lag-1 returns",
            "- vs 0kbg uniform overlays (MDD_ONLY / held hurt): regime sleeves only fire in classified risk",
            "- vs 0kbi AND full-sample gate: AND kept as baseline; router specializes cliff vs grind",
            "- vs 0kbk: design response to GRIND-specialist / no-cliff-specialist split",
            "- vs 0kbj/0kbl: cross-era floors explicit to catch 2020-only overfit / partial atlas",
            "",
            "## Disposition",
            "",
            "- **CRISIS_REGIME_IMPROVE / PARALLEL** — research path only; **signal ≠ apply**",
            "- HIT only if held+ (≥+0.10pp) AND (Mar or y2020 MDD↑) AND sealed OK AND ≥1 non-2020 major DD strict MDD↑",
            "- OVERFIT if 2020 MDD help but non-2020 major DD windows are flat or all-worse",
            "- Does **not** unlock soak freeze · does **not** recommend LIVE wire",
            "- Soft KEEP · Path4 OFF · broker false · no tip Soft promote · no year-oracle",
            "",
            "## Next",
            "",
            *[f"{i}. {line}" for i, line in enumerate(optimize, 1)],
            "",
            f"Label: `{DECISION_ID}_{day}__{verdict}__{LABEL_TAG}__NO_LIVE`",
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
                "label_tag": LABEL_TAG,
                "verdict": verdict,
                "tip_sha": tip_sha,
                "champion": champ,
                "n_hit": hits_n,
                "n_mdd_only": mdd_only_n,
                "n_overfit": overfit_n,
                "n_held_block": held_block_n,
                "prior_chain": prior,
                "soak_unlock": False,
                "live_wire_recommend": False,
                "signal_not_apply": True,
                "soft_keep": True,
                "path4_live": False,
                "broker": False,
                "label": f"{DECISION_ID}_{day}__{verdict}__{LABEL_TAG}__NO_LIVE",
            },
            indent=2,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )
    write_repro_pointer(
        OPS / f"{DECISION_ID}.json", REP / f"{DECISION_ID}.json", kind="decision pack"
    )

    _patch_register(verdict, champ, day, tip_sha)
    _patch_ops_status(verdict, champ, day)

    summary = {
        "verdict": verdict,
        "champion": None if not champ else champ["arm"],
        "family": None if not champ else champ["family"],
        "router": None if not champ else champ.get("router"),
        "held_vs_base": None if not champ else champ["held_vs_base"],
        "y2020_mdd_improve_pp": None if not champ else champ["y2020_mdd_improve_pp"],
        "mar2020_mdd_improve_pp": None if not champ else champ["mar2020_mdd_improve_pp"],
        "mdd_2015_improve_pp": None if not champ else champ["mdd_2015_improve_pp"],
        "mdd_2018_improve_pp": None if not champ else champ["mdd_2018_improve_pp"],
        "mdd_2022_improve_pp": None if not champ else champ["mdd_2022_improve_pp"],
        "cross_era_n_improve": None if not champ else champ["cross_era_n_improve"],
        "sealed_vs_base": None if not champ else champ["sealed_vs_base"],
        "tipY_vs_base": None if not champ else champ["tipY_vs_base"],
        "n_hit": hits_n,
        "n_mdd_only": mdd_only_n,
        "n_overfit": overfit_n,
        "n_held_block": held_block_n,
        "n_mech": len(mech),
        "n_arms_grid": grid_meta["n_arms"],
        "base_y2020_mdd": base_y20_mdd,
        "base_mar2020_mdd": base_mar_mdd,
        "soak_unlock": False,
        "live_wire_recommend": False,
        "signal_not_apply": True,
        "label_tag": LABEL_TAG,
        "register": REGISTER,
        "tip_sha": tip_sha,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
