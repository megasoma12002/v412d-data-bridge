#!/usr/bin/env python3
"""Major historical drawdown atlas Stage A (0kbl).

SOAK-SAFE · PARALLEL paper research — **signal ≠ apply**.

Parents 0kbk / 0kbj / 0kbi / 0kbf: cliff-vs-grind landed ``CLIFF_GRIND_SPLIT_HIT``
and hist OOS landed ``OVERFIT_2020``. Question: across **all major drawdowns**
detectable on 0050 (2010+) and Soft/L4 NAV (2012-12+), how do cliffs vs grinds
differ, and which detectors generalize across eras?

Data coverage note: **no pre-2010 / GFC** OHLCV or NAV in-repo.

Verdict taxonomy:
- ``MAJOR_DD_ATLAS_ROBUST`` — ≥1 detector clears floors on ≥3 distinct major eras
  including ≥1 non-2020
- ``MAJOR_DD_ATLAS_PARTIAL`` — multi-era lift without ROBUST floors
- ``MAJOR_DD_ATLAS_ERA_SPECIFIC`` — only 2020 or a single era
- ``MAJOR_DD_ATLAS_NO_EDGE``

Hard constraints:
- Soft KEEP · Path4 OFF · broker false · Exact T+1
- no LIVE · no tip Soft promote · no year-oracle · soak freeze unchanged

Repro: ``PYTHONPATH=scripts python3 scripts/tipsoft_ip3_major_dd_atlas_stagea.py``
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
    PX_0050,
    _alert_mask,
    _binary_prf,
    _median_lead_days,
    build_detector_arms,
    build_panel,
)

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "tipsoft-ip3-major-dd-atlas-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"
TAIEX = ROOT / "forward" / "e10s2" / "e10s2_taiex.csv"

CHARTER_ID = "TIPSOFT_IP3_MAJOR_DD_ATLAS_STAGEA_CHARTER"
SCREEN_ID = "TIPSOFT_IP3_MAJOR_DD_ATLAS_STAGEA_SCREEN"
DECISION_ID = "TIPSOFT_IP3_MAJOR_DD_ATLAS_STAGEA_DECISION_PACK"
REGISTER = "0kbl"
PARENTS = ("0kbk", "0kbj", "0kbi", "0kbf")
MECH = "TIPSOFT_IP3_MAJOR_DD_ATLAS"
LABEL_TAG = "MAJOR_DD_ATLAS_PARALLEL"

# 0kbk taxonomy params (documented / reused)
DEPTH_THRS = (0.08, 0.10)
CLIFF_N = 20
GRIND_MIN = 40
CLIFF_VEL_FLOOR = 0.004  # fraction/day
PRIMARY_DEPTH_MINOR = 0.08
PRIMARY_DEPTH_MAJOR = 0.10

# Per-episode detector floors (mirror 0kbk regime floors)
EP_IC_FLOOR = 0.08
EP_HIT_FLOOR = 0.55
EP_RECALL_FLOOR = 0.30
EP_WEAK_IC = 0.04
MIN_EP_BARS = 12
MIN_IC_BARS = 12
ROBUST_MIN_ERAS = 3
CHAMP_ARM = "and::rvol63_l4&fuse_prem_neg5"

# Named historical refs (soft tags; auto taxonomy still primary)
REF_WINDOWS: tuple[dict[str, Any], ...] = (
    {
        "tag": "EU_US_2011",
        "label": "2011 EU/US debt stress",
        "start": date(2011, 7, 1),
        "end": date(2011, 10, 15),
        "era": "2011",
    },
    {
        "tag": "TW_CN_2015",
        "label": "2015 TW/China",
        "start": date(2015, 6, 1),
        "end": date(2015, 8, 31),
        "era": "2015",
    },
    {
        "tag": "Q4_2018",
        "label": "2018 Q4",
        "start": date(2018, 10, 1),
        "end": date(2018, 12, 24),
        "era": "2018",
    },
    {
        "tag": "MAR2020_CLIFF",
        "label": "Mar2020 cliff",
        "start": date(2020, 2, 20),
        "end": date(2020, 3, 23),
        "era": "2020_mar",
    },
    {
        "tag": "MID2020_RESIDUAL",
        "label": "mid-2020 residual",
        "start": date(2020, 6, 1),
        "end": date(2020, 7, 31),
        "era": "2020_mid",
    },
    {
        "tag": "BEAR_2022",
        "label": "2022 bear",
        "start": date(2022, 1, 1),
        "end": date(2022, 10, 31),
        "era": "2022",
    },
)


@dataclass
class DdEpisode:
    eid: str
    series: str  # mkt_0050 | l4_nav | soft_nav | taiex
    peak_date: str
    trough_date: str
    recovery_date: str | None
    depth: float
    ttm_days: int
    duration_days: int
    recovery_days: int | None
    velocity_pp_day: float
    shape: str
    auto_label: str  # CLIFF | GRIND | OTHER
    cliff_n: int
    grind_min: int
    depth_thr: float
    ref_tags: list[str]
    era: str
    is_major: bool  # depth ≥ 10%


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


def _era_for_dates(peak: date, trough: date, ref_tags: list[str]) -> str:
    for rw in REF_WINDOWS:
        if rw["tag"] in ref_tags:
            return str(rw["era"])
    # calendar-year bucket for unlabeled majors
    y = trough.year if trough.year == peak.year else trough.year
    if y == 2020:
        if trough <= date(2020, 4, 30):
            return "2020_mar"
        if trough <= date(2020, 8, 31):
            return "2020_mid"
        return "2020_late"
    return str(y)


def _local_maxima(vals: np.ndarray, *, order: int = 8) -> list[int]:
    n = len(vals)
    out: list[int] = []
    if n == 0:
        return out
    for i in range(n):
        lo = max(0, i - int(order))
        hi = min(n, i + int(order) + 1)
        window = vals[lo:hi]
        if vals[i] >= float(np.max(window)) - 1e-12:
            if out and i - out[-1] <= int(order) and abs(vals[i] - vals[out[-1]]) < 1e-12:
                out[-1] = i
            elif not out or i - out[-1] > int(order) // 2:
                out.append(i)
    return out


def detect_drawdown_episodes(
    nav: pd.Series,
    *,
    series: str,
    depth_thr: float,
    cliff_n: int = CLIFF_N,
    grind_min: int = GRIND_MIN,
    vel_floor: float = CLIFF_VEL_FLOOR,
    peak_order: int = 8,
) -> list[DdEpisode]:
    """Local peak→trough episodes with depth ≥ depth_thr; label CLIFF/GRIND/OTHER.

    Rules mirror 0kbk: CLIFF if ttm≤cliff_n AND (depth/ttm)≥vel_floor;
    GRIND if ttm≥grind_min; else OTHER.
    """
    s = nav.dropna().astype(float).sort_index()
    if len(s) < 30:
        return []
    vals = s.to_numpy(dtype=float)
    idx = s.index
    peaks = _local_maxima(vals, order=peak_order)
    if len(peaks) < 2:
        peaks = [int(np.argmax(vals[: max(1, len(vals) // 2)])), len(vals) - 1]
    episodes: list[DdEpisode] = []
    eid_i = 0
    for a, b in zip(peaks[:-1], peaks[1:]):
        if b <= a + 1:
            continue
        seg = vals[a : b + 1]
        rel = int(np.argmin(seg))
        trough_i = a + rel
        if trough_i <= a:
            continue
        peak_v = float(vals[a])
        trough_v = float(vals[trough_i])
        if peak_v <= 0:
            continue
        depth = 1.0 - trough_v / peak_v
        if depth < float(depth_thr):
            continue
        ttm = int(trough_i - a)
        if ttm < 1:
            continue
        reclaim = (float(vals[b]) - trough_v) / max(peak_v - trough_v, 1e-12)
        rec_i = b if reclaim >= 0.50 else None
        rec_days = int(b - trough_i) if rec_i is not None else None
        dur = int((rec_i if rec_i is not None else trough_i) - a)
        vel = (depth * 100.0) / float(ttm)
        if rec_i is not None and rec_days is not None and rec_days <= max(5, int(1.5 * ttm)):
            shape = "V"
        elif rec_i is None:
            shape = "L"
        else:
            shape = "U_partial"
        if ttm <= int(cliff_n) and (depth / ttm) >= float(vel_floor):
            auto = "CLIFF"
        elif ttm >= int(grind_min) and depth >= float(depth_thr):
            auto = "GRIND"
        else:
            auto = "OTHER"
        tags: list[str] = []
        p0 = pd.Timestamp(idx[a]).date()
        t0 = pd.Timestamp(idx[trough_i]).date()
        for rw in REF_WINDOWS:
            if p0 <= rw["end"] and t0 >= rw["start"]:
                tags.append(rw["tag"])
        era = _era_for_dates(p0, t0, tags)
        eid_i += 1
        episodes.append(
            DdEpisode(
                eid=f"{series}_d{int(depth_thr*100)}_{eid_i:02d}",
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
                era=era,
                is_major=bool(depth >= PRIMARY_DEPTH_MAJOR),
            )
        )
    return episodes


def measure_ref_episodes(
    nav: pd.Series,
    *,
    series: str,
    depth_thr: float = PRIMARY_DEPTH_MINOR,
) -> list[DdEpisode]:
    """Force-measure named reference windows on a series."""
    s = nav.dropna().astype(float).sort_index()
    out: list[DdEpisode] = []
    for rw in REF_WINDOWS:
        w = s.loc[(s.index.date >= rw["start"]) & (s.index.date <= rw["end"])]
        if len(w) < 5:
            continue
        trough_i = int(w.values.argmin())
        pre = w.iloc[: trough_i + 1]
        peak_i = int(pre.values.argmax())
        if trough_i - peak_i < 1:
            peak_i = int(w.values.argmax())
            post_peak = w.iloc[peak_i:]
            if len(post_peak) >= 2:
                trough_i = peak_i + int(post_peak.values.argmin())
            if trough_i - peak_i < 1:
                peak_i = 0
                trough_i = max(1, len(w) - 1)
        peak_v = float(w.iloc[peak_i])
        trough_v = float(w.iloc[trough_i])
        if peak_v <= 0:
            continue
        depth = max(0.0, 1.0 - trough_v / peak_v)
        ttm = max(1, int(trough_i - peak_i))
        post = w.iloc[trough_i:]
        rec_rel = None
        for j in range(len(post)):
            if float(post.iloc[j]) >= peak_v * 0.98:
                rec_rel = j
                break
        rec_days = None if rec_rel is None else int(rec_rel)
        vel = (depth * 100.0) / float(ttm)
        if rec_days is not None and rec_days <= max(5, int(1.5 * ttm)):
            shape = "V"
        elif rec_days is None:
            shape = "L"
        else:
            shape = "U_partial"
        if depth >= float(depth_thr) and ttm <= CLIFF_N and (depth / ttm) >= CLIFF_VEL_FLOOR:
            auto = "CLIFF"
        elif depth >= float(depth_thr) and ttm >= GRIND_MIN:
            auto = "GRIND"
        else:
            auto = "OTHER"
        # Named Mar2020 / mid2020 keep forced labels when depth clear
        if rw["tag"] == "MAR2020_CLIFF" and depth >= 0.05:
            auto = "CLIFF"
        if rw["tag"] == "MID2020_RESIDUAL" and depth >= 0.03:
            auto = "GRIND" if auto == "OTHER" else auto
        out.append(
            DdEpisode(
                eid=f"ref_{series}_{rw['tag']}",
                series=series,
                peak_date=str(pd.Timestamp(w.index[peak_i]).date()),
                trough_date=str(pd.Timestamp(w.index[trough_i]).date()),
                recovery_date=None
                if rec_rel is None
                else str(pd.Timestamp(post.index[rec_rel]).date()),
                depth=round(float(depth), 6),
                ttm_days=ttm,
                duration_days=int(ttm + (0 if rec_days is None else rec_days)),
                recovery_days=rec_days,
                velocity_pp_day=round(float(vel), 4),
                shape=shape,
                auto_label=auto,
                cliff_n=CLIFF_N,
                grind_min=GRIND_MIN,
                depth_thr=float(depth_thr),
                ref_tags=[rw["tag"]],
                era=str(rw["era"]),
                is_major=bool(depth >= PRIMARY_DEPTH_MAJOR),
            )
        )
    return out


def _load_series_bundle() -> dict[str, pd.Series]:
    l4_path = ALIGN / "nav_L4_LIVE_P3_WITHIN.csv"
    if not l4_path.exists():
        l4_path = LIVESTACK / "nav_LIVE_P3_WITHIN.csv"
    soft_path = ALIGN / "nav_L1_SOFT_T1.csv"
    l4 = _load_nav(l4_path).set_index("date")["nav"].astype(float).sort_index()
    soft = _load_nav(soft_path).set_index("date")["nav"].astype(float).sort_index()
    l4.index = pd.to_datetime(l4.index).normalize()
    soft.index = pd.to_datetime(soft.index).normalize()
    # Soft/L4 usable from 2012-12-04
    cut = pd.Timestamp("2012-12-04")
    l4 = l4.loc[l4.index >= cut]
    soft = soft.loc[soft.index >= cut]
    px = pd.read_csv(PX_0050, parse_dates=["date"])
    px["date"] = pd.to_datetime(px["date"]).dt.normalize()
    col = "adjusted_close" if "adjusted_close" in px.columns else "close"
    mkt = px.set_index("date")[col].astype(float).sort_index()
    out = {"mkt_0050": mkt, "l4_nav": l4, "soft_nav": soft}
    if TAIEX.exists():
        tx = pd.read_csv(TAIEX, parse_dates=["date"])
        tx["date"] = pd.to_datetime(tx["date"]).dt.normalize()
        if "close" in tx.columns:
            out["taiex"] = tx.set_index("date")["close"].astype(float).sort_index()
    return out


def _episode_to_row(e: DdEpisode) -> dict[str, Any]:
    d = asdict(e)
    d["ref_tags"] = list(e.ref_tags)
    return d


def _spearman_n(x: pd.Series, y: pd.Series, *, min_n: int = MIN_IC_BARS) -> float | None:
    m = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(m) < int(min_n):
        return None
    rx = m["x"].rank(method="average")
    ry = m["y"].rank(method="average")
    v = float(rx.corr(ry, method="pearson"))
    return None if v != v else v


def _episode_mask(idx: pd.DatetimeIndex, e: DdEpisode, *, pad: int = 5) -> pd.Series:
    p0 = pd.Timestamp(e.peak_date)
    t0 = pd.Timestamp(e.trough_date)
    # pad a few bars before peak for alert lead
    if pad > 0:
        loc = idx.get_indexer([p0], method="nearest")[0]
        loc0 = max(0, int(loc) - int(pad))
        p0 = idx[loc0]
    return pd.Series((idx >= p0) & (idx <= t0), index=idx)


def score_detector_on_episode(
    *,
    arm: str,
    family: str,
    xs: pd.Series,
    alert: pd.Series,
    p: pd.DataFrame,
    episode: DdEpisode,
) -> dict[str, Any]:
    """IC/hit/recall for one detector inside one major episode window."""
    y_mdd = p["fwd_mdd_10"]
    y_crash = p["fwd_ret_crash_10"]
    idx = p.index
    mask = _episode_mask(idx, episode, pad=5)
    n = int(mask.sum())
    soft_needed = any(
        k in arm
        for k in ("fuse_", "cool_", "soft", "l4", "proxy_mdd", "and::", "or::")
    )
    # Soft/L4 arms unavailable before Soft NAV start
    if soft_needed and date.fromisoformat(episode.trough_date) < date(2012, 12, 4):
        return {
            "arm": arm,
            "family": family,
            "eid": episode.eid,
            "series": episode.series,
            "era": episode.era,
            "regime": episode.auto_label,
            "n_bars": n,
            "ic_spearman_fwd_mdd_10": None,
            "ic_spearman_fwd_ret_crash_10": None,
            "hit_rate": None,
            "precision": None,
            "recall": None,
            "f1": None,
            "median_lead_days": None,
            "verdict": "NO_FEATURE",
        }
    if n < MIN_EP_BARS:
        return {
            "arm": arm,
            "family": family,
            "eid": episode.eid,
            "series": episode.series,
            "era": episode.era,
            "regime": episode.auto_label,
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
    ic = _spearman_n(xs[mask], y_mdd[mask], min_n=min(MIN_IC_BARS, max(8, n // 2)))
    ic_c = _spearman_n(xs[mask], y_crash[mask], min_n=min(MIN_IC_BARS, max(8, n // 2)))
    # Binary: episode days vs same-year non-episode (avoid TN flood)
    year = pd.Timestamp(episode.trough_date).year
    year_mask = pd.Series(idx.year == year, index=idx)
    prf = _binary_prf(mask.astype(bool)[year_mask], alert[year_mask])
    lead = _median_lead_days(
        alert,
        window_start=date.fromisoformat(episode.peak_date),
        trough=pd.Timestamp(episode.trough_date),
    )
    v = "MISS"
    if ic is not None and prf["hit_rate"] is not None:
        if (
            float(ic) >= EP_IC_FLOOR
            and float(prf["hit_rate"]) >= EP_HIT_FLOOR
            and prf["recall"] is not None
            and float(prf["recall"]) >= EP_RECALL_FLOOR
        ):
            v = "OOS_HIT"
        elif float(ic) >= EP_WEAK_IC and (
            float(prf["hit_rate"]) >= 0.50
            or (prf["recall"] is not None and float(prf["recall"]) >= 0.20)
        ):
            v = "WEAK"
    return {
        "arm": arm,
        "family": family,
        "eid": episode.eid,
        "series": episode.series,
        "era": episode.era,
        "regime": episode.auto_label,
        "depth": episode.depth,
        "n_bars": n,
        "ic_spearman_fwd_mdd_10": None if ic is None else round(float(ic), 4),
        "ic_spearman_fwd_ret_crash_10": None if ic_c is None else round(float(ic_c), 4),
        "hit_rate": prf["hit_rate"],
        "precision": prf["precision"],
        "recall": prf["recall"],
        "f1": prf["f1"],
        "median_lead_days": None if lead is None else round(float(lead), 2),
        "verdict": v,
    }


def _dedupe_major_episodes(eps: list[DdEpisode]) -> list[DdEpisode]:
    """Prefer one representative per (era, regime) preferring mkt_0050 then l4."""
    series_rank = {"mkt_0050": 0, "l4_nav": 1, "soft_nav": 2, "taiex": 3}
    majors = [e for e in eps if e.is_major and not e.eid.startswith("ref_")]
    # Keep refs that are major even if auto missed
    ref_majors = [e for e in eps if e.eid.startswith("ref_") and e.is_major]
    by_key: dict[tuple[str, str], DdEpisode] = {}
    for e in sorted(majors, key=lambda x: (series_rank.get(x.series, 9), -x.depth)):
        key = (e.era, e.auto_label if e.auto_label != "OTHER" else e.series)
        # Also key by overlapping calendar to collapse same episode across series
        cal_key = (e.era, e.peak_date[:7])  # year-month of peak
        if cal_key not in by_key:
            by_key[cal_key] = e
        else:
            cur = by_key[cal_key]
            if series_rank.get(e.series, 9) < series_rank.get(cur.series, 9):
                by_key[cal_key] = e
            elif e.depth > cur.depth and e.series == cur.series:
                by_key[cal_key] = e
    # Ensure named major refs present if not overlapped
    out = list(by_key.values())
    for r in ref_majors:
        if not any(
            abs((date.fromisoformat(e.peak_date) - date.fromisoformat(r.peak_date)).days) < 40
            and e.era == r.era
            for e in out
        ):
            out.append(r)
    out.sort(key=lambda e: e.peak_date)
    return out


def cross_era_score(
    per_ep: list[dict[str, Any]], *, exclude_mar2020: bool
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    arms = sorted({r["arm"] for r in per_ep})
    for arm in arms:
        xs = [r for r in per_ep if r["arm"] == arm]
        if exclude_mar2020:
            xs = [r for r in xs if r["era"] != "2020_mar"]
        # one verdict per era (best across series)
        by_era: dict[str, str] = {}
        for r in xs:
            if r["verdict"] in ("NO_DATA", "NO_FEATURE"):
                continue
            prev = by_era.get(r["era"])
            rank = {"OOS_HIT": 3, "WEAK": 2, "MISS": 1}
            if prev is None or rank.get(r["verdict"], 0) > rank.get(prev, 0):
                by_era[r["era"]] = r["verdict"]
        n_hit = sum(1 for v in by_era.values() if v == "OOS_HIT")
        n_weak = sum(1 for v in by_era.values() if v == "WEAK")
        n_miss = sum(1 for v in by_era.values() if v == "MISS")
        eras_hit = sorted([e for e, v in by_era.items() if v == "OOS_HIT"])
        eras_all = sorted(by_era.keys())
        non2020_hit = [e for e in eras_hit if not str(e).startswith("2020")]
        rows.append(
            {
                "arm": arm,
                "exclude_mar2020": exclude_mar2020,
                "n_eras_scored": len(by_era),
                "n_oos_hit": n_hit,
                "n_weak": n_weak,
                "n_miss": n_miss,
                "eras_oos_hit": eras_hit,
                "eras_scored": eras_all,
                "n_non2020_oos_hit": len(non2020_hit),
                "non2020_eras_oos_hit": non2020_hit,
            }
        )
    rows.sort(
        key=lambda r: (r["n_oos_hit"], r["n_non2020_oos_hit"], r["n_weak"]),
        reverse=True,
    )
    return rows


def _classify_from_cross(row: dict[str, Any] | None) -> str:
    """Map one cross-era score row to atlas verdict class."""
    if row is None:
        return "MAJOR_DD_ATLAS_NO_EDGE"
    n_hit = int(row["n_oos_hit"])
    n_weak = int(row["n_weak"])
    n_non2020 = int(row["n_non2020_oos_hit"])
    eras_hit = list(row.get("eras_oos_hit") or [])
    scored = list(row.get("eras_scored") or [])
    if n_hit >= ROBUST_MIN_ERAS and n_non2020 >= 1:
        return "MAJOR_DD_ATLAS_ROBUST"
    only_2020_hits = n_hit > 0 and n_non2020 == 0 and (
        not eras_hit or all(str(e).startswith("2020") for e in eras_hit)
    )
    if only_2020_hits or (n_hit >= 1 and len(eras_hit) <= 1 and n_weak == 0):
        return "MAJOR_DD_ATLAS_ERA_SPECIFIC"
    multi_signal = (n_hit + n_weak) >= 2 and len(scored) >= 2
    has_non2020 = n_non2020 >= 1 or any(not str(e).startswith("2020") for e in scored)
    if multi_signal and has_non2020:
        return "MAJOR_DD_ATLAS_PARTIAL"
    if n_hit >= 1 and len(eras_hit) <= 1:
        return "MAJOR_DD_ATLAS_ERA_SPECIFIC"
    if (n_hit + n_weak) >= 1:
        return "MAJOR_DD_ATLAS_PARTIAL"
    return "MAJOR_DD_ATLAS_NO_EDGE"


def global_verdict(
    cross_incl: list[dict[str, Any]],
    cross_excl: list[dict[str, Any]],
    *,
    regime_counts: dict[str, int],
) -> tuple[str, dict[str, Any]]:
    """Pick best detector under exclude-Mar2020 generalization view + with-Mar."""
    best_excl = cross_excl[0] if cross_excl else None
    best_incl = cross_incl[0] if cross_incl else None

    v_excl = _classify_from_cross(best_excl)
    v_incl = _classify_from_cross(best_incl)
    rank = {
        "MAJOR_DD_ATLAS_ROBUST": 4,
        "MAJOR_DD_ATLAS_PARTIAL": 3,
        "MAJOR_DD_ATLAS_ERA_SPECIFIC": 2,
        "MAJOR_DD_ATLAS_NO_EDGE": 1,
    }
    # Prefer exclude-Mar2020 when it is at least as strong; otherwise fall back to incl
    if rank[v_excl] >= rank[v_incl]:
        verdict, champ = v_excl, best_excl
    else:
        verdict, champ = v_incl, best_incl

    if verdict == "MAJOR_DD_ATLAS_ROBUST":
        implication = (
            "At least one detector clears floors across ≥3 major eras incl. non-2020 — "
            "0kbj OVERFIT_2020 is not the whole story; generalize beyond Mar cliff, "
            "while still respecting 0kbk cliff/grind specialization."
        )
    elif verdict == "MAJOR_DD_ATLAS_PARTIAL":
        implication = (
            "Some cross-era lift exists but floors are uneven — consistent with 0kbk "
            "SPLIT_HIT (regime tools differ) and 0kbj OVERFIT_2020 (Mar window strongest)."
        )
    elif verdict == "MAJOR_DD_ATLAS_ERA_SPECIFIC":
        implication = (
            "Detector edge concentrates in a single era (often 2020) — reinforces "
            "0kbj OVERFIT_2020; 0kbk cliff/grind split remains local taxonomy, not "
            "a multi-era cash-gate license."
        )
    else:
        implication = (
            "No usable multi-era detector edge on the in-repo major-DD atlas — "
            "do not generalize 0kbj/0kbk signals; soak freeze unchanged."
        )

    detail = {
        "best_arm_excl_mar2020": None if best_excl is None else best_excl["arm"],
        "best_excl": best_excl,
        "best_arm_incl_mar2020": None if best_incl is None else best_incl["arm"],
        "best_incl": best_incl,
        "verdict_excl_mar2020": v_excl,
        "verdict_incl_mar2020": v_incl,
        "champion": champ,
        "regime_counts_major": regime_counts,
        "implication": implication,
        "robust_min_eras": ROBUST_MIN_ERAS,
        "floors": {
            "ep_ic": EP_IC_FLOOR,
            "ep_hit": EP_HIT_FLOOR,
            "ep_recall": EP_RECALL_FLOOR,
            "taxonomy": {
                "cliff_n": CLIFF_N,
                "grind_min": GRIND_MIN,
                "vel_floor": CLIFF_VEL_FLOOR,
                "depth_major": PRIMARY_DEPTH_MAJOR,
                "depth_minor": PRIMARY_DEPTH_MINOR,
            },
        },
    }
    return verdict, detail


def _shape_by_regime(episodes: list[DdEpisode]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for label in ("CLIFF", "GRIND", "OTHER"):
        xs = [e for e in episodes if e.auto_label == label]
        if not xs:
            out[label] = {"n": 0}
            continue
        out[label] = {
            "n": len(xs),
            "median_depth": round(float(np.median([e.depth for e in xs])), 4),
            "median_ttm_days": float(np.median([e.ttm_days for e in xs])),
            "median_velocity_pp_day": round(
                float(np.median([e.velocity_pp_day for e in xs])), 4
            ),
            "median_recovery_days": (
                None
                if not [e.recovery_days for e in xs if e.recovery_days is not None]
                else float(
                    np.median([e.recovery_days for e in xs if e.recovery_days is not None])
                )
            ),
            "eras": sorted({e.era for e in xs}),
        }
    out["n_total"] = len(episodes)
    return out


def _patch_register(verdict: str, detail: dict[str, Any], day: str) -> None:
    reg = OPS / "HUMAN_DECISION_REGISTER.md"
    rt = reg.read_text(encoding="utf-8")
    champ = detail.get("champion") or {}
    rc = detail.get("regime_counts_major") or {}
    new_row = (
        f"| 0kbl | major historical **DD atlas** (cliff/grind cross-era, no apply) | "
        f"**STAGE A `{verdict}`** ({day}) | "
        f"Parents 0kbk/0kbj/0kbi/0kbf · **MAJOR_DD_ATLAS/PARALLEL** · Exact T+1 lag-1 · "
        f"best `{champ.get('arm')}` OOS_HIT eras **{champ.get('n_oos_hit')}** "
        f"(non2020 **{champ.get('n_non2020_oos_hit')}**) · "
        f"major CLIFF/GRIND/OTHER **{rc.get('CLIFF')}/{rc.get('GRIND')}/{rc.get('OTHER')}** · "
        f"**signal≠apply** · soak freeze unchanged · Soft KEEP · Path4 OFF · "
        f"broker false · no live · `{DECISION_ID}.md` |"
    )
    lines = rt.splitlines()
    out: list[str] = []
    replaced = False
    for line in lines:
        if line.startswith("| 0kbl |"):
            out.append(new_row)
            replaced = True
        else:
            out.append(line)
    if not replaced:
        insert_at = None
        for key in ("| 0kbk |", "| 0kbj |", "| 0kbi |", "| 0kbf |"):
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
    champ = detail.get("champion") or {}
    line = (
        f"**Major DD atlas (MAJOR_DD_ATLAS/PARALLEL {day}):** Stage A **`{verdict}`** · "
        f"register **0kbl** · best `{champ.get('arm')}` OOS_HIT eras "
        f"**{champ.get('n_oos_hit')}** (non2020 **{champ.get('n_non2020_oos_hit')}**) · "
        f"**signal≠apply** · soak freeze unchanged · Soft KEEP · Path4 OFF · no live · "
        f"`{DECISION_ID}.md`  "
    )
    ot2, n = re.subn(
        r"\*\*Major DD atlas \(MAJOR_DD_ATLAS/PARALLEL [^)]+\):\*\*.*",
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

    coverage = {
        "primary_market": str(PX_0050.relative_to(ROOT)),
        "market_start": "2010-01-04",
        "soft_l4_start": "2012-12-04",
        "taiex_optional": str(TAIEX.relative_to(ROOT)) if TAIEX.exists() else None,
        "no_pre_2010_gfc": True,
        "note": "No pre-2010 / GFC OHLCV or Soft/L4 NAV available in-repo.",
    }

    series_map = _load_series_bundle()
    all_eps: list[DdEpisode] = []
    for sname, nav in series_map.items():
        for depth in DEPTH_THRS:
            all_eps.extend(
                detect_drawdown_episodes(nav, series=sname, depth_thr=depth)
            )
        # named refs measured on each primary series (skip taiex refs for Soft)
        if sname in ("mkt_0050", "l4_nav", "soft_nav"):
            all_eps.extend(measure_ref_episodes(nav, series=sname))

    ep_rows = [_episode_to_row(e) for e in all_eps]
    pd.DataFrame(ep_rows).to_csv(OUT / "drawdown_episodes.csv", index=False)

    # Atlas tables: unique episodes at each depth (prefer auto, not ref duplicates)
    def _atlas(depth: float) -> list[DdEpisode]:
        auto = [
            e
            for e in all_eps
            if (not e.eid.startswith("ref_"))
            and abs(e.depth_thr - depth) < 1e-9
        ]
        return sorted(auto, key=lambda e: (e.series, e.peak_date))

    atlas_08 = _atlas(0.08)
    atlas_10 = _atlas(0.10)
    pd.DataFrame([_episode_to_row(e) for e in atlas_08]).to_csv(
        OUT / "atlas_depth_ge08.csv", index=False
    )
    pd.DataFrame([_episode_to_row(e) for e in atlas_10]).to_csv(
        OUT / "atlas_depth_ge10.csv", index=False
    )

    # Major set for detector scoring: ≥10% deduped + named major refs
    major_eps = _dedupe_major_episodes(all_eps)
    present_eras = {m.era for m in major_eps}
    for e in all_eps:
        if e.eid.startswith("ref_") and e.is_major and e.era not in present_eras:
            major_eps.append(e)
            present_eras.add(e.era)
    major_eps = sorted(major_eps, key=lambda e: e.peak_date)
    pd.DataFrame([_episode_to_row(e) for e in major_eps]).to_csv(
        OUT / "major_episodes_deduped.csv", index=False
    )

    regime_counts = {
        "CLIFF": sum(1 for e in major_eps if e.auto_label == "CLIFF"),
        "GRIND": sum(1 for e in major_eps if e.auto_label == "GRIND"),
        "OTHER": sum(1 for e in major_eps if e.auto_label == "OTHER"),
        "n_major": len(major_eps),
    }
    shape_major = _shape_by_regime(major_eps)
    shape_by_series = {
        s: _shape_by_regime([e for e in atlas_10 if e.series == s])
        for s in series_map
    }
    (OUT / "shape_summary.json").write_text(
        json.dumps(
            {
                "major_deduped": shape_major,
                "by_series_depth10": shape_by_series,
                "regime_counts_major": regime_counts,
                "coverage": coverage,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    # Ref coverage
    ref_cov = []
    for rw in REF_WINDOWS:
        hits = [
            e
            for e in all_eps
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
                "era": rw["era"],
                "n_overlap_episodes": len(hits),
                "auto_labels": sorted({e.auto_label for e in hits}),
                "series": sorted({e.series for e in hits}),
                "max_depth": None if not hits else round(max(e.depth for e in hits), 4),
            }
        )
    (OUT / "ref_window_coverage.json").write_text(
        json.dumps(ref_cov, indent=2) + "\n", encoding="utf-8"
    )

    # TAIEX corroboration: overlap of major 0050 eras with TAIEX ≥8% episodes
    taiex_corr: dict[str, Any] = {"available": "taiex" in series_map}
    if "taiex" in series_map:
        tx_eps = [e for e in atlas_08 if e.series == "taiex"]
        overlaps = []
        for m in major_eps:
            if m.series not in ("mkt_0050", "l4_nav"):
                continue
            hit = [
                t
                for t in tx_eps
                if date.fromisoformat(t.peak_date)
                <= date.fromisoformat(m.trough_date)
                and date.fromisoformat(t.trough_date)
                >= date.fromisoformat(m.peak_date)
            ]
            overlaps.append(
                {
                    "major_eid": m.eid,
                    "era": m.era,
                    "n_taiex_overlap": len(hit),
                    "taiex_depths": [t.depth for t in hit],
                }
            )
        taiex_corr["n_taiex_ge08"] = len(tx_eps)
        taiex_corr["major_overlaps"] = overlaps
    (OUT / "taiex_corroboration.json").write_text(
        json.dumps(taiex_corr, indent=2) + "\n", encoding="utf-8"
    )

    panel, meta = build_panel()
    panel.to_csv(OUT / "panel_major_dd.csv", index=False)
    arms, arm_meta = build_detector_arms(panel)
    p = panel.copy()
    p["date"] = pd.to_datetime(p["date"])
    p = p.set_index("date").sort_index()

    # Key arms for atlas (0kbh singles + 0kbi champ + useful ORs)
    key_arms = [
        a
        for a in arms
        if a.startswith("base::")
        or a == CHAMP_ARM
        or a.startswith("or::")
        or a.startswith("and::")
    ]

    per_ep_rows: list[dict[str, Any]] = []
    for ep in major_eps:
        for name in key_arms:
            xs = arms[name].reindex(p.index)
            alert = _alert_mask(xs, stress_high=True, q=ALERT_Q)
            per_ep_rows.append(
                score_detector_on_episode(
                    arm=name,
                    family=str(arm_meta[name].get("family")),
                    xs=xs,
                    alert=alert,
                    p=p,
                    episode=ep,
                )
            )
    pd.DataFrame(per_ep_rows).to_csv(OUT / "per_episode_detector_metrics.csv", index=False)

    cross_incl = cross_era_score(per_ep_rows, exclude_mar2020=False)
    cross_excl = cross_era_score(per_ep_rows, exclude_mar2020=True)
    pd.DataFrame(cross_incl).to_csv(OUT / "cross_era_score_incl_mar2020.csv", index=False)
    pd.DataFrame(cross_excl).to_csv(OUT / "cross_era_score_excl_mar2020.csv", index=False)

    # Cliff vs grind aggregate across major eras
    cliff_eps = [e for e in major_eps if e.auto_label == "CLIFF"]
    grind_eps = [e for e in major_eps if e.auto_label == "GRIND"]
    regime_compare = {
        "cliff_vs_grind_shape": {
            "CLIFF": shape_major.get("CLIFF"),
            "GRIND": shape_major.get("GRIND"),
            "OTHER": shape_major.get("OTHER"),
        },
        "n_major_cliff": len(cliff_eps),
        "n_major_grind": len(grind_eps),
        "note": (
            "0kbk rules: CLIFF if ttm≤20 & vel≥0.004/day; GRIND if ttm≥40; "
            "depth gates 8%/10%."
        ),
    }

    verdict, detail = global_verdict(
        cross_incl, cross_excl, regime_counts=regime_counts
    )

    compare = {
        "0kbk": {
            "register": "0kbk",
            "verdict": "CLIFF_GRIND_SPLIT_HIT",
            "note": "Cliff/grind taxonomy + GRIND_SPECIALIST champ — atlas extends to all eras.",
        },
        "0kbj": {
            "register": "0kbj",
            "verdict": "IP3_CRISIS_SIGNAL_HIST_OOS_OVERFIT_2020",
            "note": "Hist OOS overfit 2020 — atlas tests generalization excl/incl Mar2020.",
        },
        "0kbi": {
            "register": "0kbi",
            "verdict": "IP3_Y2020_CRISIS_SIGNAL_REFINE_HIT",
            "note": f"AND champ `{CHAMP_ARM}` reused when Soft features exist.",
        },
        "0kbf": {
            "register": "0kbf",
            "verdict": "SOAK_OPEN",
            "note": "Soak freeze unchanged — atlas Stage A does not unlock SOAK_PASS.",
        },
    }

    champ = detail.get("champion") or {}
    optimize = [
        "Objective: major historical DD atlas — cliff vs grind across eras + detector generalization",
        f"Coverage: 0050 from 2010-01-04 · Soft/L4 from 2012-12-04 · **no pre-2010/GFC in-repo**",
        (
            f"Taxonomy (0kbk): depth≥8%/10% · CLIFF ttm≤{CLIFF_N} vel≥{CLIFF_VEL_FLOOR} · "
            f"GRIND ttm≥{GRIND_MIN}"
        ),
        (
            f"Major (≥10%) regime counts: CLIFF={regime_counts['CLIFF']} · "
            f"GRIND={regime_counts['GRIND']} · OTHER={regime_counts['OTHER']} · "
            f"n={regime_counts['n_major']}"
        ),
        (
            f"Best excl-Mar2020: `{detail.get('best_arm_excl_mar2020')}` "
            f"OOS_HIT={None if not detail.get('best_excl') else detail['best_excl']['n_oos_hit']} "
            f"non2020={None if not detail.get('best_excl') else detail['best_excl']['n_non2020_oos_hit']}"
        ),
        (
            f"Best incl-Mar2020: `{detail.get('best_arm_incl_mar2020')}` "
            f"OOS_HIT={None if not detail.get('best_incl') else detail['best_incl']['n_oos_hit']}"
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
        "coverage": coverage,
        "meta": meta,
        "regime_counts_major": regime_counts,
        "shape_summary": shape_major,
        "regime_compare": regime_compare,
        "ref_window_coverage": ref_cov,
        "taiex_corroboration": taiex_corr,
        "n_atlas_ge08": len(atlas_08),
        "n_atlas_ge10": len(atlas_10),
        "n_major_deduped": len(major_eps),
        "n_arms": len(key_arms),
        "cross_era_excl_mar2020": cross_excl,
        "cross_era_incl_mar2020": cross_incl,
        "champion": champ,
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
    (OUT / "summary.json").write_text(
        json.dumps(
            {
                "verdict": verdict,
                "tip_sha": tip_sha,
                "regime_counts_major": regime_counts,
                "best_cross_era_detector": champ.get("arm"),
                "best_excl_mar2020": detail.get("best_excl"),
                "best_incl_mar2020": detail.get("best_incl"),
                "implication": detail["implication"],
                "coverage": coverage,
            },
            indent=2,
            default=str,
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
            "Across **all major drawdowns** detectable on 0050 (2010+) and Soft/L4 NAV "
            "(2012-12+), how do cliffs vs grinds differ, and which detectors generalize "
            "across eras?",
            "",
            "## Data",
            "",
            f"- Primary market: `{coverage['primary_market']}` (2010-01-04+)",
            f"- Optional TAIEX: `{coverage['taiex_optional']}` for corroboration",
            "- Soft/L4: align-gap NAVs from 2012-12-04",
            "- **No pre-2010 / GFC** series in-repo",
            "",
            "## Design",
            "",
            f"- Detect peak→trough episodes depth ≥ **8%** and ≥ **10%**",
            f"- Classify CLIFF / GRIND / OTHER with **0kbk rules**: "
            f"cliff_n≤{CLIFF_N}, grind_min≥{GRIND_MIN}, vel_floor={CLIFF_VEL_FLOOR}",
            "- Named refs: 2011 EU/US · 2015 TW/CN · 2018Q4 · Mar2020 · 2022 bear · mid-2020 residual",
            "- Per major (≥10%): detector IC/hit/recall (rvol20/63, atr, MA200 gap, dd63, "
            "fuse proxies, 0kbi AND champ when features exist)",
            "- Cross-era score with/without Mar2020",
            "- Verdicts: `MAJOR_DD_ATLAS_ROBUST` / `_PARTIAL` / `_ERA_SPECIFIC` / `_NO_EDGE`",
            "",
            "## Hard constraints",
            "",
            "- Soft KEEP · Path4 OFF · broker false · Exact T+1",
            "- **signal ≠ apply** · no tip Soft promote · no year-oracle",
            "- does **not** unlock soak freeze · no LIVE wire",
            "",
            f"Repro: `PYTHONPATH=scripts python3 scripts/tipsoft_ip3_major_dd_atlas_stagea.py`",
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
            "major DD atlas — cliffs vs grinds across eras; which detectors generalize"
        ),
        "coverage": coverage,
        "floors": detail["floors"],
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

    # --- SCREEN ---
    top_excl = cross_excl[:10]
    screen_md_lines = [
        f"# {SCREEN_ID}",
        "",
        f"Date: {day} · Register **{REGISTER}** · Verdict **`{verdict}`**",
        f"Tip SHA: `{tip_sha}`",
        "",
        "## Coverage",
        "",
        f"- 0050 from **2010-01-04** · Soft/L4 from **2012-12-04**",
        "- **No pre-2010 / GFC** in-repo",
        f"- Atlas n(≥8%)={len(atlas_08)} · n(≥10%)={len(atlas_10)} · "
        f"major deduped={len(major_eps)}",
        "",
        "## Major DDs by regime (deduped ≥10%)",
        "",
        f"- CLIFF: n={regime_counts['CLIFF']} · {shape_major.get('CLIFF')}",
        f"- GRIND: n={regime_counts['GRIND']} · {shape_major.get('GRIND')}",
        f"- OTHER: n={regime_counts['OTHER']} · {shape_major.get('OTHER')}",
        "",
        "## Named ref coverage",
        "",
    ]
    for rc in ref_cov:
        screen_md_lines.append(
            f"- `{rc['tag']}` ({rc['era']}): n={rc['n_overlap_episodes']} "
            f"labels={rc['auto_labels']} max_depth={rc['max_depth']}"
        )
    screen_md_lines += [
        "",
        "## Cross-era detector score (exclude Mar2020)",
        "",
        "| arm | eras | OOS_HIT | WEAK | MISS | non2020 HIT | eras_hit |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for r in top_excl:
        screen_md_lines.append(
            f"| `{r['arm']}` | {r['n_eras_scored']} | {r['n_oos_hit']} | "
            f"{r['n_weak']} | {r['n_miss']} | {r['n_non2020_oos_hit']} | "
            f"{','.join(r['eras_oos_hit']) or '—'} |"
        )
    screen_md_lines += [
        "",
        "## Best incl Mar2020",
        "",
    ]
    if detail.get("best_incl"):
        bi = detail["best_incl"]
        screen_md_lines.append(
            f"- `{bi['arm']}` OOS_HIT={bi['n_oos_hit']} eras={bi['eras_oos_hit']}"
        )
    screen_md_lines += [
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
            f"- Best cross-era detector (excl Mar2020): `{detail.get('best_arm_excl_mar2020')}` "
            f"OOS_HIT **{None if not detail.get('best_excl') else detail['best_excl']['n_oos_hit']}** "
            f"non2020 **{None if not detail.get('best_excl') else detail['best_excl']['n_non2020_oos_hit']}**",
            f"- Major regime counts: CLIFF **{regime_counts['CLIFF']}** · "
            f"GRIND **{regime_counts['GRIND']}** · OTHER **{regime_counts['OTHER']}**",
            f"- Implication: {detail['implication']}",
            "",
            "## Hard keeps",
            "",
            "- Soft KEEP · Path4 OFF · broker false · Exact T+1",
            "- **signal ≠ apply** · soak freeze unchanged · no LIVE · no tip Soft promote",
            "- No pre-2010/GFC claim — data not in-repo",
            "",
            "## Next (human)",
            "",
            "- If ROBUST: prefer multi-era detectors over Mar2020-only cash-gate narratives",
            "- If ERA_SPECIFIC/NO_EDGE: treat 0kbj OVERFIT_2020 as confirmed; do not unlock soak",
            "- Respect 0kbk cliff/grind specialization when designing any future Stage B",
            "",
            f"Screen: `{SCREEN_ID}.md` · Charter: `{CHARTER_ID}.md`",
            f"Repro: `PYTHONPATH=scripts python3 scripts/tipsoft_ip3_major_dd_atlas_stagea.py`",
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
        "champion": champ,
        "regime_counts_major": regime_counts,
        "shape_summary": shape_major,
        "signal_not_apply": True,
        "soak_unlock": False,
        "live_wire_recommend": False,
        "soft_keep": True,
        "path4_live": False,
        "broker": False,
        "exact_t1": True,
        "year_oracle": False,
        "coverage": coverage,
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

    print(
        json.dumps(
            {
                "verdict": verdict,
                "regime_counts_major": regime_counts,
                "best_cross_era_detector": champ.get("arm"),
                "tip_sha": tip_sha,
                "implication": detail["implication"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
