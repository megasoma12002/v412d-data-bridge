#!/usr/bin/env python3
"""Crisis regime taxonomy Stage A (0kbk) — **cliff (急殺)** vs **grind (長期跌)**.

SOAK-SAFE · PARALLEL paper research — **signal ≠ apply**.

Parents 0kbj / 0kbi / 0kbh / 0kbf: hist OOS landed ``OVERFIT_2020`` on the 0kbi
AND champ. Question: do stress **regimes** differ — short cliffs vs long grinds —
in (a) shape metrics, (b) which lag-1 detectors fire, (c) whether cash-gate CF
helps held vs MDD?

Standalone: vendors minimal 0kbh/0kbi helpers via ``tipsoft_ip3_crisis_signal_helpers``
(PRs #427–429 may still be unmerged).

Verdict taxonomy:
- ``CLIFF_GRIND_SPLIT_HIT`` — detectors clearly specialize (cliff-strong & grind-weak
  or vice versa) with floors
- ``CLIFF_GRIND_SPLIT_WEAK`` — mild difference
- ``CLIFF_GRIND_NO_SPLIT`` — similar

Hard constraints:
- Soft KEEP · Path4 OFF · broker false · Exact T+1
- no LIVE · no tip Soft promote · no year-oracle · soak freeze unchanged

Repro: ``PYTHONPATH=scripts python3 scripts/tipsoft_ip3_crisis_cliff_vs_grind_stagea.py``
"""
from __future__ import annotations

import json
import re
import subprocess
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ops_repro_ssot import write_ops_and_repro_pointer, write_repro_pointer
from stagea_screen_helpers import load_nav_csv as _load_nav
from stagea_screen_helpers import utc_now_z as _utc
from tipsoft_ip3_crisis_signal_helpers import (
    ALERT_Q,
    ALIGN,
    LIVESTACK,
    MAR2020_END,
    MAR2020_START,
    PX_0050,
    _alert_mask,
    _binary_prf,
    _median_lead_days,
    build_detector_arms,
    build_panel,
    counterfactual_cash_gate,
)

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "tipsoft-ip3-crisis-cliff-vs-grind-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "TIPSOFT_IP3_CRISIS_CLIFF_VS_GRIND_STAGEA_CHARTER"
SCREEN_ID = "TIPSOFT_IP3_CRISIS_CLIFF_VS_GRIND_STAGEA_SCREEN"
DECISION_ID = "TIPSOFT_IP3_CRISIS_CLIFF_VS_GRIND_STAGEA_DECISION_PACK"
REGISTER = "0kbk"
PARENTS = ("0kbj", "0kbi", "0kbh", "0kbf")
MECH = "TIPSOFT_IP3_CRISIS_CLIFF_VS_GRIND"
LABEL_TAG = "CLIFF_GRIND_PARALLEL"

# Taxonomy grids
DEPTH_THRS = (0.08, 0.10)
CLIFF_N_DAYS = (10, 15, 20)
GRIND_MIN_DAYS = (40, 60)
# Velocity floor for CLIFF (pp/day as fraction, e.g. 0.004 = 0.4 pp/day)
CLIFF_VEL_FLOOR = 0.004
PRIMARY_DEPTH = 0.08
PRIMARY_CLIFF_N = 15
PRIMARY_GRIND_MIN = 40

# Detector lift floors (within-regime)
REGIME_IC_FLOOR = 0.08
REGIME_HIT_FLOOR = 0.55
REGIME_RECALL_FLOOR = 0.30
# Split floors
SPLIT_IC_DELTA = 0.05
SPLIT_HIT_DELTA = 0.10
SPLIT_HIT_STRONG_IC = 0.08
SPLIT_WEAK_IC = 0.04
MIN_REGIME_BARS = 40
MIN_IC_BARS = 40

CHAMP_ARM = "and::rvol63_l4&fuse_prem_neg5"
BASE_0KBH = "base::rvol20_l4"


@dataclass
class DdEpisode:
    eid: str
    series: str  # l4_nav | soft_nav | mkt_0050
    peak_date: str
    trough_date: str
    recovery_date: str | None
    depth: float  # positive fraction
    ttm_days: int  # peak→trough trading days
    duration_days: int  # peak→recovery (or trough if no recovery) trading days
    recovery_days: int | None  # trough→recovery
    velocity_pp_day: float  # depth*100 / ttm_days
    shape: str  # V | L | U_partial
    auto_label: str  # CLIFF | GRIND | OTHER
    cliff_n: int
    grind_min: int
    depth_thr: float
    ref_tags: list[str]


# Manual reference windows (soft tags; auto taxonomy still primary)
REF_WINDOWS: tuple[dict[str, Any], ...] = (
    {
        "tag": "MAR2020_CLIFF",
        "label": "Mar2020 cliff",
        "start": date(2020, 2, 20),
        "end": date(2020, 3, 23),
        "expect": "CLIFF",
    },
    {
        "tag": "TW_CN_2015",
        "label": "2015 TW/China",
        "start": date(2015, 6, 1),
        "end": date(2015, 8, 31),
        "expect": "CLIFF_OR_GRIND",
    },
    {
        "tag": "Q4_2018",
        "label": "2018 Q4",
        "start": date(2018, 10, 1),
        "end": date(2018, 12, 24),
        "expect": "GRIND_OR_CLIFF",
    },
    {
        "tag": "MID2020_RESIDUAL",
        "label": "mid-2020 residual (0kb4 census drag)",
        "start": date(2020, 6, 1),
        "end": date(2020, 7, 31),
        "expect": "GRIND",
    },
    {
        "tag": "LATE2020_RESIDUAL",
        "label": "late-2020 residual window",
        "start": date(2020, 9, 1),
        "end": date(2020, 10, 31),
        "expect": "GRIND_OR_OTHER",
    },
)


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


def _load_series_bundle() -> dict[str, pd.Series]:
    l4_path = ALIGN / "nav_L4_LIVE_P3_WITHIN.csv"
    if not l4_path.exists():
        l4_path = LIVESTACK / "nav_LIVE_P3_WITHIN.csv"
    soft_path = ALIGN / "nav_L1_SOFT_T1.csv"
    l4 = _load_nav(l4_path).set_index("date")["nav"].astype(float).sort_index()
    soft = _load_nav(soft_path).set_index("date")["nav"].astype(float).sort_index()
    l4.index = pd.to_datetime(l4.index).normalize()
    soft.index = pd.to_datetime(soft.index).normalize()
    px = pd.read_csv(PX_0050, parse_dates=["date"])
    px["date"] = pd.to_datetime(px["date"]).dt.normalize()
    col = "adjusted_close" if "adjusted_close" in px.columns else "close"
    mkt = px.set_index("date")[col].astype(float).sort_index()
    # Align market onto L4 calendar (ffill)
    mkt = mkt.reindex(l4.index).ffill()
    soft = soft.reindex(l4.index).ffill()
    return {"l4_nav": l4, "soft_nav": soft, "mkt_0050": mkt}


def detect_drawdown_episodes(
    nav: pd.Series,
    *,
    series: str,
    depth_thr: float = PRIMARY_DEPTH,
    cliff_n: int = PRIMARY_CLIFF_N,
    grind_min: int = PRIMARY_GRIND_MIN,
    vel_floor: float = CLIFF_VEL_FLOOR,
    recovery_tol: float = 0.02,
) -> list[DdEpisode]:
    """Peak-to-trough episodes with depth ≥ depth_thr; label CLIFF/GRIND/OTHER."""
    s = nav.dropna().astype(float).sort_index()
    if len(s) < 60:
        return []
    vals = s.to_numpy(dtype=float)
    idx = s.index
    episodes: list[DdEpisode] = []
    i = 0
    n = len(vals)
    eid_i = 0
    while i < n - 2:
        # Advance while making new highs
        peak_i = i
        peak_v = vals[i]
        j = i + 1
        while j < n and vals[j] >= peak_v * (1.0 - 1e-12):
            peak_v = vals[j]
            peak_i = j
            j += 1
        if j >= n:
            break
        # Drawdown path from this peak
        trough_i = peak_i
        trough_v = peak_v
        k = peak_i + 1
        crossed = False
        while k < n:
            if vals[k] < trough_v:
                trough_v = vals[k]
                trough_i = k
            depth = 1.0 - trough_v / peak_v
            if depth >= depth_thr:
                crossed = True
            # Recovery: back within recovery_tol of peak (or new high)
            if crossed and vals[k] >= peak_v * (1.0 - recovery_tol):
                break
            # New cycle peak after material recovery attempt fails — stop if
            # we've been below thr and then made a local rebound >50% of depth
            if crossed and k > trough_i + 3:
                rebound = (vals[k] - trough_v) / max(peak_v - trough_v, 1e-12)
                # Allow long grind; only cut if rebound strong and then re-peak search
                if rebound >= 0.85 and vals[k] > trough_v * 1.02:
                    # treat as recovered enough to close episode without full peak
                    break
            k += 1
        if not crossed:
            i = peak_i + 1
            continue
        # Close episode at k (recovery) or end
        rec_i = k if k < n and vals[k] >= peak_v * (1.0 - recovery_tol) else None
        end_i = k if k < n else n - 1
        depth = 1.0 - trough_v / peak_v
        ttm = int(trough_i - peak_i)
        if ttm < 1:
            i = trough_i + 1
            continue
        dur = int(end_i - peak_i)
        rec_days = int(end_i - trough_i) if rec_i is not None else None
        vel = (depth * 100.0) / float(ttm)  # pp/day
        # Shape: V if recovers within 1.5× ttm; L if no recovery or recovery ≫ ttm
        if rec_i is not None and rec_days is not None and rec_days <= max(5, int(1.5 * ttm)):
            shape = "V"
        elif rec_i is None:
            shape = "L"
        else:
            shape = "U_partial"
        # Label
        if ttm <= int(cliff_n) and (depth / ttm) >= float(vel_floor):
            auto = "CLIFF"
        elif ttm >= int(grind_min) and depth >= depth_thr:
            auto = "GRIND"
        else:
            auto = "OTHER"
        # Ref tags by trough/peak overlap
        tags: list[str] = []
        p0 = pd.Timestamp(idx[peak_i]).date()
        t0 = pd.Timestamp(idx[trough_i]).date()
        for rw in REF_WINDOWS:
            # overlap [peak, trough] with ref window
            if p0 <= rw["end"] and t0 >= rw["start"]:
                tags.append(rw["tag"])
        eid_i += 1
        episodes.append(
            DdEpisode(
                eid=f"{series}_{eid_i:02d}",
                series=series,
                peak_date=str(p0),
                trough_date=str(t0),
                recovery_date=None
                if rec_i is None
                else str(pd.Timestamp(idx[rec_i]).date()),
                depth=round(float(depth), 6),
                ttm_days=ttm,
                duration_days=dur,
                recovery_days=rec_days,
                velocity_pp_day=round(float(vel), 4),
                shape=shape,
                auto_label=auto,
                cliff_n=int(cliff_n),
                grind_min=int(grind_min),
                depth_thr=float(depth_thr),
                ref_tags=tags,
            )
        )
        # Continue after trough (avoid re-detecting same episode)
        i = trough_i + 1
    return episodes


def _episode_to_row(e: DdEpisode) -> dict[str, Any]:
    d = asdict(e)
    d["ref_tags"] = list(e.ref_tags)
    return d


def _mask_for_episodes(
    idx: pd.DatetimeIndex, episodes: list[DdEpisode], *, label: str
) -> pd.Series:
    m = pd.Series(False, index=idx)
    for e in episodes:
        if e.auto_label != label:
            continue
        p0 = pd.Timestamp(e.peak_date)
        t0 = pd.Timestamp(e.trough_date)
        m = m | ((idx >= p0) & (idx <= t0))
    return m


def _spearman_n(x: pd.Series, y: pd.Series, *, min_n: int = MIN_IC_BARS) -> float | None:
    m = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(m) < int(min_n):
        return None
    rx = m["x"].rank(method="average")
    ry = m["y"].rank(method="average")
    v = float(rx.corr(ry, method="pearson"))
    return None if v != v else v


def score_detector_by_regime(
    *,
    arm: str,
    family: str,
    xs: pd.Series,
    alert: pd.Series,
    p: pd.DataFrame,
    cliff_mask: pd.Series,
    grind_mask: pd.Series,
) -> dict[str, Any]:
    """IC/hit/recall within CLIFF vs GRIND episode bars (+ lead to local trough)."""
    y_mdd = p["fwd_mdd_10"]
    y_crash = p["fwd_ret_crash_10"]
    idx = p.index

    def _block(mask: pd.Series, regime: str) -> dict[str, Any]:
        n = int(mask.sum())
        if n < MIN_REGIME_BARS:
            return {
                "regime": regime,
                "n_bars": n,
                "ic_spearman_fwd_mdd_10": None,
                "ic_spearman_fwd_ret_crash_10": None,
                "hit_rate": None,
                "precision": None,
                "recall": None,
                "f1": None,
                "median_lead_days": None,
                "verdict": "NO_DATA",
            }
        # Expand eval window: episode ±10 trading days for IC stability
        # but keep binary labels as episode days
        # Use full sample IC restricted to mask for purity
        ic = _spearman_n(xs[mask], y_mdd[mask], min_n=min(MIN_IC_BARS, max(25, n // 2)))
        ic_c = _spearman_n(xs[mask], y_crash[mask], min_n=min(MIN_IC_BARS, max(25, n // 2)))
        # Binary: positive = in-regime day; eval on union of regime + buffer decade?
        # Local: score alert vs regime label on [mask | nearby], but hit/recall on
        # calendar covering regime years only to avoid TN flood.
        years = sorted({pd.Timestamp(d).year for d in idx[mask]})
        year_mask = pd.Series(idx.year.isin(years), index=idx)
        y_true = mask.astype(bool)
        prf = _binary_prf(y_true[year_mask], alert[year_mask])
        # Lead: first alert before each episode trough (median)
        leads: list[float] = []
        # Reconstruct episodes from contiguous True runs in mask
        arr = mask.fillna(False).to_numpy()
        starts = np.where(arr & ~np.r_[False, arr[:-1]])[0]
        ends = np.where(arr & ~np.r_[arr[1:], False])[0]
        for a, b in zip(starts, ends):
            trough = idx[b]
            lead = _median_lead_days(
                alert, window_start=pd.Timestamp(idx[a]).date(), trough=pd.Timestamp(trough)
            )
            if lead is not None:
                leads.append(float(lead))
        med_lead = float(np.median(leads)) if leads else None
        # Regime verdict (detection strength inside this regime)
        v = "REGIME_MISS"
        if ic is not None and prf["hit_rate"] is not None:
            if (
                float(ic) >= REGIME_IC_FLOOR
                and float(prf["hit_rate"]) >= REGIME_HIT_FLOOR
                and prf["recall"] is not None
                and float(prf["recall"]) >= REGIME_RECALL_FLOOR
            ):
                v = "REGIME_HIT"
            elif float(ic) >= SPLIT_WEAK_IC or (
                float(prf["hit_rate"]) >= 0.50
                and prf["recall"] is not None
                and float(prf["recall"]) >= 0.20
            ):
                v = "REGIME_WEAK"
        return {
            "regime": regime,
            "n_bars": n,
            "ic_spearman_fwd_mdd_10": None if ic is None else round(float(ic), 4),
            "ic_spearman_fwd_ret_crash_10": None if ic_c is None else round(float(ic_c), 4),
            "hit_rate": prf["hit_rate"],
            "precision": prf["precision"],
            "recall": prf["recall"],
            "f1": prf["f1"],
            "median_lead_days": None if med_lead is None else round(med_lead, 2),
            "verdict": v,
        }

    cliff = _block(cliff_mask, "CLIFF")
    grind = _block(grind_mask, "GRIND")
    return {
        "arm": arm,
        "family": family,
        "cliff": cliff,
        "grind": grind,
        "ic_delta_cliff_minus_grind": (
            None
            if cliff["ic_spearman_fwd_mdd_10"] is None
            or grind["ic_spearman_fwd_mdd_10"] is None
            else round(
                float(cliff["ic_spearman_fwd_mdd_10"]) - float(grind["ic_spearman_fwd_mdd_10"]),
                4,
            )
        ),
        "hit_delta_cliff_minus_grind": (
            None
            if cliff["hit_rate"] is None or grind["hit_rate"] is None
            else round(float(cliff["hit_rate"]) - float(grind["hit_rate"]), 4)
        ),
        "recall_delta_cliff_minus_grind": (
            None
            if cliff["recall"] is None or grind["recall"] is None
            else round(float(cliff["recall"]) - float(grind["recall"]), 4)
        ),
    }


def _specialize(row: dict[str, Any]) -> str:
    """Per-arm specialization tag."""
    c = row["cliff"]
    g = row["grind"]
    if c["verdict"] == "NO_DATA" or g["verdict"] == "NO_DATA":
        return "INCOMPLETE"
    cic, gic = c["ic_spearman_fwd_mdd_10"], g["ic_spearman_fwd_mdd_10"]
    ch, gh = c["hit_rate"], g["hit_rate"]
    if cic is None or gic is None:
        return "INCOMPLETE"
    ic_d = float(cic) - float(gic)
    hit_d = (0.0 if ch is None or gh is None else float(ch) - float(gh))
    cliff_strong = c["verdict"] == "REGIME_HIT" or (
        float(cic) >= SPLIT_HIT_STRONG_IC and c["verdict"] == "REGIME_WEAK"
    )
    grind_strong = g["verdict"] == "REGIME_HIT" or (
        float(gic) >= SPLIT_HIT_STRONG_IC and g["verdict"] == "REGIME_WEAK"
    )
    cliff_weakish = c["verdict"] in ("REGIME_MISS",) or float(cic) < SPLIT_WEAK_IC
    grind_weakish = g["verdict"] in ("REGIME_MISS",) or float(gic) < SPLIT_WEAK_IC
    if cliff_strong and grind_weakish and (
        abs(ic_d) >= SPLIT_IC_DELTA or abs(hit_d) >= SPLIT_HIT_DELTA
    ):
        return "CLIFF_SPECIALIST"
    if grind_strong and cliff_weakish and (
        abs(ic_d) >= SPLIT_IC_DELTA or abs(hit_d) >= SPLIT_HIT_DELTA
    ):
        return "GRIND_SPECIALIST"
    if abs(ic_d) >= SPLIT_IC_DELTA or abs(hit_d) >= SPLIT_HIT_DELTA:
        return "MILD_SPLIT"
    return "NO_SPLIT"


def global_verdict(rows: list[dict[str, Any]]) -> tuple[str, dict[str, Any]]:
    for r in rows:
        r["specialize"] = _specialize(r)
    specs = [r["specialize"] for r in rows]
    n_cliff = sum(1 for s in specs if s == "CLIFF_SPECIALIST")
    n_grind = sum(1 for s in specs if s == "GRIND_SPECIALIST")
    n_mild = sum(1 for s in specs if s == "MILD_SPLIT")
    n_none = sum(1 for s in specs if s == "NO_SPLIT")
    champ = next((r for r in rows if r["arm"] == CHAMP_ARM), rows[0] if rows else None)
    base = next((r for r in rows if r["arm"] == BASE_0KBH), None)
    detail = {
        "n_cliff_specialist": n_cliff,
        "n_grind_specialist": n_grind,
        "n_mild_split": n_mild,
        "n_no_split": n_none,
        "champ_arm": CHAMP_ARM,
        "champ_specialize": None if champ is None else champ["specialize"],
        "champ_cliff_ic": None
        if champ is None
        else champ["cliff"]["ic_spearman_fwd_mdd_10"],
        "champ_grind_ic": None
        if champ is None
        else champ["grind"]["ic_spearman_fwd_mdd_10"],
        "base_0kbh_specialize": None if base is None else base["specialize"],
        "implication": (
            "0kbj OVERFIT_2020 may be cliff-specific; grind needs different tools "
            "(already seen in 0kb4 defend residual)."
        ),
    }
    # HIT: ≥2 clear specialists of same polarity OR champ is clear specialist
    # with floors, and opposite regime weak
    clear = n_cliff + n_grind
    if clear >= 2 or (
        champ is not None
        and champ["specialize"] in ("CLIFF_SPECIALIST", "GRIND_SPECIALIST")
        and (
            (
                champ["specialize"] == "CLIFF_SPECIALIST"
                and champ["cliff"]["verdict"] in ("REGIME_HIT", "REGIME_WEAK")
                and champ["grind"]["verdict"] in ("REGIME_MISS", "REGIME_WEAK")
                and (champ.get("ic_delta_cliff_minus_grind") or 0) >= SPLIT_IC_DELTA
            )
            or (
                champ["specialize"] == "GRIND_SPECIALIST"
                and champ["grind"]["verdict"] in ("REGIME_HIT", "REGIME_WEAK")
                and champ["cliff"]["verdict"] in ("REGIME_MISS", "REGIME_WEAK")
                and (champ.get("ic_delta_cliff_minus_grind") or 0) <= -SPLIT_IC_DELTA
            )
        )
    ):
        # Require at least one REGIME_HIT on the strong side for SPLIT_HIT
        strong_hit = any(
            (r["specialize"] == "CLIFF_SPECIALIST" and r["cliff"]["verdict"] == "REGIME_HIT")
            or (r["specialize"] == "GRIND_SPECIALIST" and r["grind"]["verdict"] == "REGIME_HIT")
            for r in rows
        )
        if strong_hit or (
            champ is not None
            and champ["specialize"] in ("CLIFF_SPECIALIST", "GRIND_SPECIALIST")
            and abs(float(champ.get("ic_delta_cliff_minus_grind") or 0)) >= SPLIT_IC_DELTA + 0.03
        ):
            return "CLIFF_GRIND_SPLIT_HIT", detail
        return "CLIFF_GRIND_SPLIT_WEAK", detail
    if n_mild >= 2 or (champ is not None and champ["specialize"] == "MILD_SPLIT"):
        return "CLIFF_GRIND_SPLIT_WEAK", detail
    return "CLIFF_GRIND_NO_SPLIT", detail


def _shape_summary(episodes: list[DdEpisode]) -> dict[str, Any]:
    def _agg(label: str) -> dict[str, Any]:
        xs = [e for e in episodes if e.auto_label == label]
        if not xs:
            return {"n": 0}
        depths = [e.depth for e in xs]
        ttms = [e.ttm_days for e in xs]
        vels = [e.velocity_pp_day for e in xs]
        recs = [e.recovery_days for e in xs if e.recovery_days is not None]
        shapes = {s: sum(1 for e in xs if e.shape == s) for s in ("V", "L", "U_partial")}
        return {
            "n": len(xs),
            "median_depth": round(float(np.median(depths)), 4),
            "mean_depth": round(float(np.mean(depths)), 4),
            "median_ttm_days": float(np.median(ttms)),
            "mean_ttm_days": round(float(np.mean(ttms)), 2),
            "median_velocity_pp_day": round(float(np.median(vels)), 4),
            "median_recovery_days": None if not recs else float(np.median(recs)),
            "shape_counts": shapes,
        }

    return {
        "CLIFF": _agg("CLIFF"),
        "GRIND": _agg("GRIND"),
        "OTHER": _agg("OTHER"),
        "n_total": len(episodes),
    }


def _grid_sensitivity(
    series_map: dict[str, pd.Series],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for series_name, nav in series_map.items():
        for depth in DEPTH_THRS:
            for cn in CLIFF_N_DAYS:
                for gmin in GRIND_MIN_DAYS:
                    eps = detect_drawdown_episodes(
                        nav,
                        series=series_name,
                        depth_thr=depth,
                        cliff_n=cn,
                        grind_min=gmin,
                    )
                    rows.append(
                        {
                            "series": series_name,
                            "depth_thr": depth,
                            "cliff_n": cn,
                            "grind_min": gmin,
                            "n_cliff": sum(1 for e in eps if e.auto_label == "CLIFF"),
                            "n_grind": sum(1 for e in eps if e.auto_label == "GRIND"),
                            "n_other": sum(1 for e in eps if e.auto_label == "OTHER"),
                            "n_total": len(eps),
                        }
                    )
    return rows


def _patch_register(verdict: str, detail: dict[str, Any], day: str) -> None:
    reg = OPS / "HUMAN_DECISION_REGISTER.md"
    rt = reg.read_text(encoding="utf-8")
    new_row = (
        f"| 0kbk | crisis **cliff vs grind** regime taxonomy (no apply) | "
        f"**STAGE A `{verdict}`** ({day}) | "
        f"Parents 0kbj/0kbi/0kbh/0kbf · **CLIFF_GRIND/PARALLEL** · Exact T+1 lag-1 · "
        f"champ `{CHAMP_ARM}` specialize **{detail.get('champ_specialize')}** · "
        f"cliffIC **{detail.get('champ_cliff_ic')}** · grindIC **{detail.get('champ_grind_ic')}** · "
        f"n_cliff_spec **{detail.get('n_cliff_specialist')}** · "
        f"n_grind_spec **{detail.get('n_grind_specialist')}** · "
        f"**signal≠apply** · soak freeze unchanged · Soft KEEP · Path4 OFF · "
        f"broker false · no live · `{DECISION_ID}.md` |"
    )
    lines = rt.splitlines()
    out: list[str] = []
    replaced = False
    for line in lines:
        if line.startswith("| 0kbk |"):
            out.append(new_row)
            replaced = True
        else:
            out.append(line)
    if not replaced:
        insert_at = None
        for key in ("| 0kbj |", "| 0kbi |", "| 0kbh |", "| 0kbf |"):
            for i, line in enumerate(out):
                if line.startswith(key):
                    insert_at = i + 1
                    break
            if insert_at is not None:
                break
        if insert_at is not None:
            out.insert(insert_at, new_row)
        else:
            out.append(new_row)
    reg.write_text("\n".join(out) + "\n", encoding="utf-8")


def _patch_ops_status(verdict: str, detail: dict[str, Any], day: str) -> None:
    ops = OPS / "OPS_STATUS.md"
    ot = ops.read_text(encoding="utf-8")
    line = (
        f"**Crisis cliff vs grind (CLIFF_GRIND/PARALLEL {day}):** Stage A **`{verdict}`** · "
        f"register **0kbk** · champ `{CHAMP_ARM}` specialize **{detail.get('champ_specialize')}** · "
        f"cliffIC **{detail.get('champ_cliff_ic')}** · grindIC **{detail.get('champ_grind_ic')}** · "
        f"**signal≠apply** · soak freeze unchanged · Soft KEEP · Path4 OFF · no live · "
        f"`{DECISION_ID}.md`  "
    )
    ot2, n = re.subn(
        r"\*\*Crisis cliff vs grind \(CLIFF_GRIND/PARALLEL [^)]+\):\*\*.*",
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
        needle = "2020 defend/off-peak knife"
        idx = ot.find(needle)
    if idx >= 0:
        end = ot.find("\n", idx) + 1
        ops.write_text(ot[:end] + line + "\n" + ot[end:], encoding="utf-8")
    else:
        ops.write_text(line + "\n" + ot, encoding="utf-8")


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()
    day = generated[:10]
    tip_sha = _git_sha()

    series_map = _load_series_bundle()
    # Primary taxonomy on L4 NAV (+ Soft + 0050 for shape tables)
    primary_eps: list[DdEpisode] = []
    for sname in ("l4_nav", "soft_nav", "mkt_0050"):
        primary_eps.extend(
            detect_drawdown_episodes(
                series_map[sname],
                series=sname,
                depth_thr=PRIMARY_DEPTH,
                cliff_n=PRIMARY_CLIFF_N,
                grind_min=PRIMARY_GRIND_MIN,
            )
        )
    ep_rows = [_episode_to_row(e) for e in primary_eps]
    pd.DataFrame(ep_rows).to_csv(OUT / "drawdown_episodes.csv", index=False)

    # Prefer L4 for regime masks (tipsoft world); fall back Soft
    l4_eps = [e for e in primary_eps if e.series == "l4_nav"]
    soft_eps = [e for e in primary_eps if e.series == "soft_nav"]
    regime_eps = l4_eps if l4_eps else soft_eps
    shape = _shape_summary(regime_eps)
    shape_all = {
        "l4_nav": _shape_summary([e for e in primary_eps if e.series == "l4_nav"]),
        "soft_nav": _shape_summary([e for e in primary_eps if e.series == "soft_nav"]),
        "mkt_0050": _shape_summary([e for e in primary_eps if e.series == "mkt_0050"]),
        "primary_series": "l4_nav" if l4_eps else "soft_nav",
    }
    (OUT / "shape_summary.json").write_text(
        json.dumps(shape_all, indent=2) + "\n", encoding="utf-8"
    )

    grid = _grid_sensitivity(series_map)
    pd.DataFrame(grid).to_csv(OUT / "taxonomy_grid.csv", index=False)

    # Ref tag coverage
    ref_cov = []
    for rw in REF_WINDOWS:
        hits = [
            e
            for e in regime_eps
            if rw["tag"] in e.ref_tags
            or (
                date.fromisoformat(e.peak_date) <= rw["end"]
                and date.fromisoformat(e.trough_date) >= rw["start"]
            )
        ]
        ref_cov.append(
            {
                "tag": rw["tag"],
                "label": rw["label"],
                "expect": rw["expect"],
                "n_overlap_episodes": len(hits),
                "auto_labels": sorted({e.auto_label for e in hits}),
                "depths": [e.depth for e in hits],
                "ttm_days": [e.ttm_days for e in hits],
            }
        )
    (OUT / "ref_window_coverage.json").write_text(
        json.dumps(ref_cov, indent=2) + "\n", encoding="utf-8"
    )

    panel, meta = build_panel()
    panel.to_csv(OUT / "panel_cliff_grind.csv", index=False)
    arms, arm_meta = build_detector_arms(panel)
    p = panel.copy()
    p["date"] = pd.to_datetime(p["date"])
    p = p.set_index("date").sort_index()

    cliff_mask = _mask_for_episodes(p.index, regime_eps, label="CLIFF")
    grind_mask = _mask_for_episodes(p.index, regime_eps, label="GRIND")
    (OUT / "regime_masks.csv").write_text(
        pd.DataFrame(
            {
                "date": p.index,
                "cliff": cliff_mask.astype(int).to_numpy(),
                "grind": grind_mask.astype(int).to_numpy(),
            }
        ).to_csv(index=False),
        encoding="utf-8",
    )

    rows: list[dict[str, Any]] = []
    for name, xs in arms.items():
        alert = _alert_mask(xs.reindex(p.index), stress_high=True, q=ALERT_Q)
        ov = arm_meta[name].get("alert_override")
        if ov is not None:
            alert = ov.reindex(p.index).fillna(False).astype(bool)
        row = score_detector_by_regime(
            arm=name,
            family=str(arm_meta[name].get("family")),
            xs=xs.reindex(p.index),
            alert=alert,
            p=p,
            cliff_mask=cliff_mask,
            grind_mask=grind_mask,
        )
        rows.append(row)
    verdict, detail = global_verdict(rows)
    rows.sort(
        key=lambda r: (
            r["specialize"] in ("CLIFF_SPECIALIST", "GRIND_SPECIALIST"),
            r["specialize"] == "MILD_SPLIT",
            abs(float(r.get("ic_delta_cliff_minus_grind") or 0)),
        ),
        reverse=True,
    )
    pd.DataFrame(
        [
            {
                "arm": r["arm"],
                "family": r["family"],
                "specialize": r["specialize"],
                "cliff_ic": r["cliff"]["ic_spearman_fwd_mdd_10"],
                "cliff_hit": r["cliff"]["hit_rate"],
                "cliff_recall": r["cliff"]["recall"],
                "cliff_verdict": r["cliff"]["verdict"],
                "grind_ic": r["grind"]["ic_spearman_fwd_mdd_10"],
                "grind_hit": r["grind"]["hit_rate"],
                "grind_recall": r["grind"]["recall"],
                "grind_verdict": r["grind"]["verdict"],
                "ic_delta": r["ic_delta_cliff_minus_grind"],
                "hit_delta": r["hit_delta_cliff_minus_grind"],
            }
            for r in rows
        ]
    ).to_csv(OUT / "detector_lift_by_regime.csv", index=False)

    # Illustrative CF: cash-gate on champ — full / cliff-only / grind-only alerts
    l4_path = ROOT / meta["base_path"]
    base_nav = _load_nav(l4_path)
    champ_xs = arms[CHAMP_ARM].reindex(p.index)
    champ_alert = _alert_mask(champ_xs, stress_high=True, q=ALERT_Q)
    # Restrict alerts to regime days for differential efficacy
    alert_cliff = champ_alert & cliff_mask
    alert_grind = champ_alert & grind_mask
    cf_full = counterfactual_cash_gate(
        panel, champ_xs, base_nav=base_nav, alert=champ_alert, label="full_champ_alert"
    )
    cf_cliff = counterfactual_cash_gate(
        panel,
        champ_xs,
        base_nav=base_nav,
        alert=alert_cliff,
        window_start=MAR2020_START,
        window_end=MAR2020_END,
        label="cliff_only_alert",
    )
    # Grind CF window: union of grind episode calendar span
    grind_eps = [e for e in regime_eps if e.auto_label == "GRIND"]
    if grind_eps:
        g0 = min(date.fromisoformat(e.peak_date) for e in grind_eps)
        g1 = max(date.fromisoformat(e.trough_date) for e in grind_eps)
    else:
        g0, g1 = date(2018, 10, 1), date(2018, 12, 24)
    cf_grind = counterfactual_cash_gate(
        panel,
        champ_xs,
        base_nav=base_nav,
        alert=alert_grind,
        window_start=g0,
        window_end=g1,
        label="grind_only_alert",
    )
    cf = {
        "champ_arm": CHAMP_ARM,
        "full": cf_full,
        "cliff_only": cf_cliff,
        "grind_only": cf_grind,
        "differential": {
            "held_cliff_minus_grind_pp": (
                None
                if cf_cliff.get("held_cagr_lift_pp") is None
                or cf_grind.get("held_cagr_lift_pp") is None
                else round(
                    float(cf_cliff["held_cagr_lift_pp"])
                    - float(cf_grind["held_cagr_lift_pp"]),
                    4,
                )
            ),
            "note": (
                "Illustrative only — cash-gate on regime-restricted champ alerts; "
                "not promote / not DD_SWITCH tip Soft."
            ),
        },
    }
    (OUT / "counterfactual_illustrative.json").write_text(
        json.dumps(cf, indent=2) + "\n", encoding="utf-8"
    )

    floors = {
        "primary_depth": PRIMARY_DEPTH,
        "primary_cliff_n": PRIMARY_CLIFF_N,
        "primary_grind_min": PRIMARY_GRIND_MIN,
        "cliff_vel_floor": CLIFF_VEL_FLOOR,
        "depth_thrs": list(DEPTH_THRS),
        "cliff_n_grid": list(CLIFF_N_DAYS),
        "grind_min_grid": list(GRIND_MIN_DAYS),
        "regime_ic_floor": REGIME_IC_FLOOR,
        "regime_hit_floor": REGIME_HIT_FLOOR,
        "regime_recall_floor": REGIME_RECALL_FLOOR,
        "split_ic_delta": SPLIT_IC_DELTA,
        "split_hit_delta": SPLIT_HIT_DELTA,
        "alert_q": ALERT_Q,
    }

    compare = {
        "0kbj": {
            "register": "0kbj",
            "verdict": "IP3_CRISIS_SIGNAL_HIST_OOS_OVERFIT_2020",
            "note": "Hist OOS overfit 2020 — this pack tests if that is cliff-specific.",
        },
        "0kbi": {
            "register": "0kbi",
            "verdict": "IP3_Y2020_CRISIS_SIGNAL_REFINE_HIT",
            "note": f"AND champ `{CHAMP_ARM}` reused for regime lift.",
        },
        "0kbh": {
            "register": "0kbh",
            "verdict": "IP3_Y2020_CRISIS_SIGNAL_WEAK",
            "note": "Singles (rvol/atr/dd/fuse) reused as baseline arms.",
        },
        "0kbf": {
            "register": "0kbf",
            "verdict": "SOAK_OPEN",
            "note": "Soak freeze unchanged — cliff/grind Stage A does not unlock SOAK_PASS.",
        },
        "0kb4": {
            "register": "0kb4",
            "verdict": "IP3_Y2020_DEFEND_NO_EDGE",
            "note": "Defend residual mid/late 2020 tagged as grind-like reference windows.",
        },
    }

    champ_row = next((r for r in rows if r["arm"] == CHAMP_ARM), None)
    optimize = [
        "Objective: cliff(急殺) vs grind(長期跌) regime taxonomy + detector lift + illustrative CF",
        (
            f"Primary taxonomy depth≥{PRIMARY_DEPTH} cliff_n≤{PRIMARY_CLIFF_N} "
            f"grind_min≥{PRIMARY_GRIND_MIN} on {shape_all['primary_series']}"
        ),
        (
            f"Shape: cliff n={shape['CLIFF'].get('n')} med_depth={shape['CLIFF'].get('median_depth')} "
            f"med_ttm={shape['CLIFF'].get('median_ttm_days')} · "
            f"grind n={shape['GRIND'].get('n')} med_depth={shape['GRIND'].get('median_depth')} "
            f"med_ttm={shape['GRIND'].get('median_ttm_days')}"
        ),
        (
            f"Champ `{CHAMP_ARM}` specialize={detail.get('champ_specialize')} "
            f"cliffIC={detail.get('champ_cliff_ic')} grindIC={detail.get('champ_grind_ic')}"
        ),
        (
            f"Specialists: cliff={detail['n_cliff_specialist']} · "
            f"grind={detail['n_grind_specialist']} · mild={detail['n_mild_split']} · "
            f"none={detail['n_no_split']}"
        ),
        (
            f"Illustrative CF held cliff={cf_cliff.get('held_cagr_lift_pp')} "
            f"grind={cf_grind.get('held_cagr_lift_pp')} "
            f"Δ={cf['differential']['held_cliff_minus_grind_pp']} (NOT promote)"
        ),
        f"Implication: {detail['implication']}",
        "Disposition: signal≠apply · soak freeze unchanged · no LIVE · no tip Soft · no year-oracle",
        "Soft KEEP · Path4 OFF · broker false · Exact T+1",
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
        "verdict_detail": detail,
        "signal_not_apply": True,
        "soak_unlock": False,
        "live_wire_recommend": False,
        "size_overlay_promote": False,
        "year_oracle": False,
        "floors": floors,
        "meta": meta,
        "shape_summary": shape_all,
        "ref_window_coverage": ref_cov,
        "n_episodes_primary": len(regime_eps),
        "n_cliff_bars": int(cliff_mask.sum()),
        "n_grind_bars": int(grind_mask.sum()),
        "n_arms": len(rows),
        "detector_lift": rows,
        "champion": champ_row,
        "counterfactual_illustrative": cf,
        "compare_parents": compare,
        "optimize_live": optimize,
        "soft_keep": True,
        "path4_live": False,
        "broker": False,
        "exact_t1": True,
        "label": f"{SCREEN_ID}_{day}__{verdict}__{LABEL_TAG}",
    }
    (OUT / "screen.json").write_text(
        json.dumps(screen, indent=2, default=str) + "\n", encoding="utf-8"
    )
    (OUT / "base_diag.json").write_text(
        json.dumps(
            {
                "meta": meta,
                "floors": floors,
                "tip_sha": tip_sha,
                "n_cliff_bars": int(cliff_mask.sum()),
                "n_grind_bars": int(grind_mask.sum()),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    # --- CHARTER ---
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
            "How do stress **regimes** differ — short cliffs (急殺) vs long grinds "
            "(長期跌) — in (a) shape metrics, (b) which lag-1 detectors fire, "
            "(c) whether size overlays / DD_SWITCH-like cash gates help held vs MDD?",
            "",
            "## Taxonomy",
            "",
            f"- Auto-detect drawdown episodes on Soft/L4 NAV + 0050 (depth ≥ {PRIMARY_DEPTH} / grid {DEPTH_THRS})",
            f"- **CLIFF** if time-to-trough ≤ N (grid {CLIFF_N_DAYS}) AND velocity ≥ {CLIFF_VEL_FLOOR} (fraction/day)",
            f"- **GRIND** if ttm ≥ {GRIND_MIN_DAYS} with similar depth",
            "- Manual ref tags: Mar2020 cliff · 2015 · 2018Q4 · mid/late 2020 residual (0kb4)",
            "",
            "## Metrics / verdict",
            "",
            "- Shape table: depth · duration · velocity · recovery · V/L shape",
            "- Detector lift by regime (0kbh singles + 0kbi AND champ): IC/hit/recall within CLIFF vs GRIND",
            "- Illustrative cash-gate CF only (not promote)",
            "- `CLIFF_GRIND_SPLIT_HIT` / `_WEAK` / `_NO_SPLIT`",
            "",
            "## Hard constraints",
            "",
            "- Soft KEEP · Path4 OFF · broker false · Exact T+1",
            "- **signal ≠ apply** · no tip Soft promote · no year-oracle",
            "- does **not** unlock soak freeze · no LIVE wire",
            "",
            f"Repro: `PYTHONPATH=scripts python3 scripts/tipsoft_ip3_crisis_cliff_vs_grind_stagea.py`",
            "",
        ]
    )
    charter_json = {
        "id": CHARTER_ID,
        "register": REGISTER,
        "parents": list(PARENTS),
        "generated_at_utc": generated,
        "tip_sha": tip_sha,
        "label_tag": LABEL_TAG,
        "question": (
            "cliff(急殺) vs grind(長期跌) — shape, detector lift, illustrative cash-gate CF"
        ),
        "floors": floors,
        "signal_not_apply": True,
        "soft_keep": True,
        "path4_live": False,
        "broker": False,
        "exact_t1": True,
        "year_oracle": False,
        "soak_unlock": False,
    }
    write_ops_and_repro_pointer(
        OPS / f"{CHARTER_ID}.md", REP / f"{CHARTER_ID}.md", charter_md, kind="charter"
    )
    (OPS / f"{CHARTER_ID}.json").write_text(
        json.dumps(charter_json, indent=2) + "\n", encoding="utf-8"
    )
    write_repro_pointer(OPS / f"{CHARTER_ID}.json", REP / f"{CHARTER_ID}.json", kind="charter")

    # --- SCREEN md ---
    def _fmt_shape(block: dict[str, Any]) -> str:
        if not block.get("n"):
            return "n=0"
        return (
            f"n={block['n']} · med_depth={block.get('median_depth')} · "
            f"med_ttm={block.get('median_ttm_days')}d · "
            f"med_vel={block.get('median_velocity_pp_day')}pp/d · "
            f"med_rec={block.get('median_recovery_days')} · "
            f"shapes={block.get('shape_counts')}"
        )

    top = rows[:12]
    screen_md_lines = [
        f"# {SCREEN_ID}",
        "",
        f"Date: {day} · Register **{REGISTER}** · Verdict **`{verdict}`**",
        f"Tip SHA: `{tip_sha}`",
        "",
        "## Shape (primary L4)",
        "",
        f"- CLIFF: {_fmt_shape(shape['CLIFF'])}",
        f"- GRIND: {_fmt_shape(shape['GRIND'])}",
        f"- OTHER: {_fmt_shape(shape['OTHER'])}",
        "",
        "## Ref window coverage",
        "",
    ]
    for rc in ref_cov:
        screen_md_lines.append(
            f"- `{rc['tag']}`: n={rc['n_overlap_episodes']} labels={rc['auto_labels']} "
            f"expect={rc['expect']}"
        )
    screen_md_lines += [
        "",
        "## Detector lift (CLIFF vs GRIND)",
        "",
        "| arm | specialize | cliff IC/hit/R | grind IC/hit/R | ΔIC |",
        "|---|---|---|---|---|",
    ]
    for r in top:
        screen_md_lines.append(
            f"| `{r['arm']}` | {r['specialize']} | "
            f"{r['cliff']['ic_spearman_fwd_mdd_10']}/"
            f"{r['cliff']['hit_rate']}/{r['cliff']['recall']} | "
            f"{r['grind']['ic_spearman_fwd_mdd_10']}/"
            f"{r['grind']['hit_rate']}/{r['grind']['recall']} | "
            f"{r['ic_delta_cliff_minus_grind']} |"
        )
    screen_md_lines += [
        "",
        "## Counterfactual (illustrative only)",
        "",
        f"- full champ cash-gate held **{cf_full.get('held_cagr_lift_pp')}** · "
        f"sealedMDD↑ **{cf_full.get('sealed_mdd_improve_pp')}**",
        f"- cliff-only held **{cf_cliff.get('held_cagr_lift_pp')}** · "
        f"MarMDD↑ **{cf_cliff.get('window_mdd_improve_pp')}**",
        f"- grind-only held **{cf_grind.get('held_cagr_lift_pp')}** · "
        f"windowMDD↑ **{cf_grind.get('window_mdd_improve_pp')}**",
        f"- held Δ(cliff−grind) **{cf['differential']['held_cliff_minus_grind_pp']}**",
        "",
        "## Parents",
        "",
    ]
    for k, v in compare.items():
        screen_md_lines.append(f"- {k}: {v['note']}")
    screen_md_lines += [
        "",
        "## Optimize / disposition",
        "",
        *[f"- {x}" for x in optimize],
        "",
    ]
    screen_md = "\n".join(screen_md_lines)
    write_ops_and_repro_pointer(
        OPS / f"{SCREEN_ID}.md", REP / f"{SCREEN_ID}.md", screen_md, kind="screen"
    )
    (OPS / f"{SCREEN_ID}.json").write_text(
        json.dumps(screen, indent=2, default=str) + "\n", encoding="utf-8"
    )
    write_repro_pointer(OPS / f"{SCREEN_ID}.json", REP / f"{SCREEN_ID}.json", kind="screen")

    # --- DECISION ---
    decision_md = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: {day}",
            f"Register: **{REGISTER}** · Parents: {', '.join(PARENTS)} · **{LABEL_TAG}**",
            f"Verdict: **`{verdict}`**",
            f"Tip SHA: `{tip_sha}`",
            "",
            "## Bottom line",
            "",
            f"- Champ `{CHAMP_ARM}` specialize **{detail.get('champ_specialize')}** "
            f"(cliffIC **{detail.get('champ_cliff_ic')}** · grindIC **{detail.get('champ_grind_ic')}**)",
            f"- Specialists: cliff **{detail['n_cliff_specialist']}** · "
            f"grind **{detail['n_grind_specialist']}** · mild **{detail['n_mild_split']}**",
            f"- Shape primary: CLIFF {_fmt_shape(shape['CLIFF'])}",
            f"- Shape primary: GRIND {_fmt_shape(shape['GRIND'])}",
            f"- Implication: {detail['implication']}",
            "",
            "## Hard keeps",
            "",
            "- Soft KEEP · Path4 OFF · broker false · Exact T+1",
            "- **signal ≠ apply** · soak freeze unchanged · no LIVE · no tip Soft promote",
            "- Illustrative CF is **not** a promote path",
            "",
            "## Next (human)",
            "",
            "- If SPLIT_HIT and cliff-specialist: treat 0kbj OVERFIT_2020 as cliff-local; "
            "do not generalize cash-gate to grind residuals",
            "- Grind tools remain open research (0kb4 defend residual already NO_EDGE)",
            "- Do **not** unlock soak on this pack",
            "",
            f"Screen: `{SCREEN_ID}.md` · Charter: `{CHARTER_ID}.md`",
            f"Repro: `PYTHONPATH=scripts python3 scripts/tipsoft_ip3_crisis_cliff_vs_grind_stagea.py`",
            "",
        ]
    )
    decision_json = {
        "id": DECISION_ID,
        "register": REGISTER,
        "parents": list(PARENTS),
        "generated_at_utc": generated,
        "tip_sha": tip_sha,
        "verdict": verdict,
        "verdict_detail": detail,
        "champion": champ_row,
        "shape_summary": shape_all,
        "counterfactual_illustrative": cf,
        "signal_not_apply": True,
        "soak_unlock": False,
        "live_wire_recommend": False,
        "soft_keep": True,
        "path4_live": False,
        "broker": False,
        "exact_t1": True,
        "year_oracle": False,
        "optimize_live": optimize,
    }
    write_ops_and_repro_pointer(
        OPS / f"{DECISION_ID}.md", REP / f"{DECISION_ID}.md", decision_md, kind="decision pack"
    )
    (OPS / f"{DECISION_ID}.json").write_text(
        json.dumps(decision_json, indent=2, default=str) + "\n", encoding="utf-8"
    )
    write_repro_pointer(
        OPS / f"{DECISION_ID}.json", REP / f"{DECISION_ID}.json", kind="decision pack"
    )

    _patch_register(verdict, detail, day)
    _patch_ops_status(verdict, detail, day)

    print(json.dumps({"verdict": verdict, "detail": detail, "tip_sha": tip_sha}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
