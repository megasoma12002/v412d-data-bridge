#!/usr/bin/env python3
"""Historical crisis **signal** OOS Stage A (0kbj) — detection only.

SOAK-SAFE · PARALLEL paper research — **signal ≠ apply**.

Parents 0kbi / 0kbh landed Mar2020 refine SIGNAL_HIT arms (champ
``and::rvol63_l4&fuse_prem_neg5``). User follow-up: multi-arm overfitting risk —
do those HIT / k-confirm arms still detect stress in **historical** TWSE-relevant
crisis windows (GFC ~2008, 2015, optional 2011 / 2018 Q4) with lag-1 causal
metrics, or are they 2020-only / overfit?

Still detection-only:
- Soft KEEP · Path4 OFF · broker false · Exact T+1 lag-1
- no LIVE apply · no tip Soft promote · no year-oracle · no soak unlock
- no size-apply promote

Global verdict taxonomy:
- ``IP3_CRISIS_SIGNAL_HIST_OOS_ROBUST`` — champ clears OOS floors on ≥2 of {2008,2015}
- ``…_PARTIAL`` — one historical episode only (of {2008,2015})
- ``…_OVERFIT_2020`` — strong on 2020 / weak-miss on 2008 & 2015
- ``…_NO_DATA`` — history too short for required episodes

Per arm×episode: ``OOS_HIT`` / ``OOS_WEAK`` / ``OOS_MISS`` / ``NO_DATA``.

Repro: ``PYTHONPATH=scripts python3 scripts/tipsoft_ip3_crisis_signal_hist_oos_stagea.py``
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ops_repro_ssot import write_ops_and_repro_pointer, write_repro_pointer
from stagea_screen_helpers import load_nav_csv as _load_nav
from stagea_screen_helpers import utc_now_z as _utc
from tipsoft_ip3_y2020_crisis_signal_refine_stagea import (
    build_refine_arms,
    _orient_stress,
)
from tipsoft_ip3_y2020_crisis_signal_stagea import (
    ALERT_Q,
    ALIGN,
    BASE_ID,
    LIVESTACK,
    PX_0050,
    SOFT_ID,
    _alert_mask,
    _binary_prf,
    _median_lead_days,
    _pearson,
    build_panel,
)

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "tipsoft-ip3-crisis-signal-hist-oos-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "TIPSOFT_IP3_CRISIS_SIGNAL_HIST_OOS_STAGEA_CHARTER"
SCREEN_ID = "TIPSOFT_IP3_CRISIS_SIGNAL_HIST_OOS_STAGEA_SCREEN"
DECISION_ID = "TIPSOFT_IP3_CRISIS_SIGNAL_HIST_OOS_STAGEA_DECISION_PACK"
REGISTER = "0kbj"
PARENTS = ("0kbi", "0kbh", "0kbf")
MECH = "TIPSOFT_IP3_CRISIS_SIGNAL_HIST_OOS"
LABEL_TAG = "SIGNAL_HIST_OOS_PARALLEL"

# Floors for historical OOS episode detection (slightly softer than in-sample HIT)
OOS_IC_ABS_FLOOR = 0.05
OOS_HIT_FLOOR = 0.55
OOS_RECALL_FLOOR = 0.30
OOS_F1_FLOOR = 0.20
OOS_LEAD_DAYS_FLOOR = 3.0
OOS_FA_CEIL = 0.15
# Weak band
WEAK_IC_ABS = 0.03
WEAK_HIT = 0.50
WEAK_RECALL = 0.20

# Min coverage inside episode window (trading days)
MIN_EPISODE_BARS = 20
MIN_IC_BARS = 40

# 0kbi SIGNAL_HIT arms + 0kbh champ baseline (fixed freeze for hist OOS)
CHAMP_ARM = "and::rvol63_l4&fuse_prem_neg5"
TARGET_ARMS: tuple[str, ...] = (
    CHAMP_ARM,
    "or::rvol20_l4|atr_like_20",
    "or::rvol20_l4|dd63_l4",
    "or::rvol20_l4|fuse_prem_neg5",
    "or::neg_gap_ma200|fuse_prem_neg5",
    "or::atr_like_20|dd63_l4",
    "or::neg_gap_ma200|dd63_l4",
    "or::cool_defend_l1|fuse_prem_neg5",
    "andflag::fuse_neg_flag&fuse_prem_neg5",
    "or::atr_like_20|fuse_prem_neg5",
    "kconfirm2::fuse_prem_neg5",
    "kconfirm2::fuse_neg_flag",
    "base::rvol20_l4",  # 0kbh champ
)

# Known crisis years by decade (for FA denominator)
CRISIS_YEARS_BY_DECADE: dict[int, set[int]] = {
    2000: {2008, 2009},
    2010: {2011, 2015, 2018},
    2020: {2020, 2022},
}


@dataclass(frozen=True)
class Episode:
    eid: str
    label: str
    start: date
    end: date
    eval_start: date
    eval_end: date
    crisis_years: frozenset[int]
    decade_start: int
    required_for_global: bool  # counts toward {2008,2015} ROBUST rule
    in_sample_ref: bool
    optional: bool = False


EPISODES: tuple[Episode, ...] = (
    Episode(
        eid="GFC_2008",
        label="GFC / 金融海嘯",
        start=date(2008, 9, 1),
        end=date(2009, 3, 31),
        eval_start=date(2008, 7, 1),
        eval_end=date(2009, 6, 30),
        crisis_years=frozenset({2008, 2009}),
        decade_start=2000,
        required_for_global=True,
        in_sample_ref=False,
    ),
    Episode(
        eid="TW_CN_2015",
        label="2015 TW/China crash",
        start=date(2015, 6, 1),
        end=date(2015, 9, 30),
        eval_start=date(2015, 4, 1),
        eval_end=date(2015, 10, 31),
        crisis_years=frozenset({2015}),
        decade_start=2010,
        required_for_global=True,
        in_sample_ref=False,
    ),
    Episode(
        eid="EU_US_2011",
        label="2011 EU/US stress",
        start=date(2011, 7, 1),
        end=date(2011, 10, 31),
        eval_start=date(2011, 5, 1),
        eval_end=date(2011, 12, 31),
        crisis_years=frozenset({2011}),
        decade_start=2010,
        required_for_global=False,
        in_sample_ref=False,
        optional=True,
    ),
    Episode(
        eid="Q4_2018",
        label="2018 Q4 stress",
        start=date(2018, 10, 1),
        end=date(2018, 12, 24),
        eval_start=date(2018, 8, 1),
        eval_end=date(2019, 2, 28),
        crisis_years=frozenset({2018}),
        decade_start=2010,
        required_for_global=False,
        in_sample_ref=False,
        optional=True,
    ),
    Episode(
        eid="MAR2020",
        label="Mar2020 cliff (in-sample ref)",
        start=date(2020, 2, 20),
        end=date(2020, 3, 23),
        eval_start=date(2020, 1, 2),
        eval_end=date(2020, 6, 30),
        crisis_years=frozenset({2020}),
        decade_start=2020,
        required_for_global=False,
        in_sample_ref=True,
    ),
)


def _spearman_n(x: pd.Series, y: pd.Series, *, min_n: int = MIN_IC_BARS) -> float | None:
    m = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(m) < int(min_n):
        return None
    rx = m["x"].rank(method="average")
    ry = m["y"].rank(method="average")
    v = float(rx.corr(ry, method="pearson"))
    return None if v != v else v


def _load_nav_series() -> tuple[pd.Series, str, Path]:
    l4_path = ALIGN / "nav_L4_LIVE_P3_WITHIN.csv"
    base_note = BASE_ID
    if not l4_path.exists():
        l4_path = LIVESTACK / "nav_LIVE_P3_WITHIN.csv"
        base_note = "LIVE_P3_WITHIN"
    nav = _load_nav(l4_path)
    s = nav.set_index("date")["nav"].astype(float).sort_index()
    s.index = pd.to_datetime(s.index).normalize()
    return s, base_note, l4_path


def _load_0050_close() -> pd.Series:
    px = pd.read_csv(PX_0050, parse_dates=["date"])
    px["date"] = pd.to_datetime(px["date"]).dt.normalize()
    col = "adjusted_close" if "adjusted_close" in px.columns else "close"
    return px.set_index("date")[col].astype(float).sort_index()


def _data_coverage_report(
    panel_idx: pd.DatetimeIndex,
    nav_s: pd.Series,
    px_s: pd.Series,
) -> dict[str, Any]:
    return {
        "panel_start": str(panel_idx.min().date()) if len(panel_idx) else None,
        "panel_end": str(panel_idx.max().date()) if len(panel_idx) else None,
        "nav_start": str(nav_s.dropna().index.min().date()) if len(nav_s.dropna()) else None,
        "nav_end": str(nav_s.dropna().index.max().date()) if len(nav_s.dropna()) else None,
        "mkt_0050_start": str(px_s.dropna().index.min().date()) if len(px_s.dropna()) else None,
        "mkt_0050_end": str(px_s.dropna().index.max().date()) if len(px_s.dropna()) else None,
        "base_id": BASE_ID,
        "soft_id": SOFT_ID,
        "gfc_2008_available": False,  # NAV 2012-12 / 0050 2010-01 — fail loud
        "note": (
            "L4/Soft NAV panel starts ~2012-12; 0050 OHLCV starts 2010-01. "
            "GFC ~2008 and 2011 NAV-twin episodes are NO_DATA (fail loud). "
            "Longest available twin world used for 2015 / 2018 / 2020."
        ),
    }


def _episode_coverage(
    ep: Episode,
    panel_idx: pd.DatetimeIndex,
    *,
    coverage: dict[str, Any],
) -> dict[str, Any]:
    """Return coverage verdict; fail loud when required episode has no data."""
    if not len(panel_idx):
        return {
            "available": False,
            "n_bars_episode": 0,
            "n_bars_eval": 0,
            "reason": "empty_panel",
            "fail_loud": bool(ep.required_for_global),
        }
    p0 = panel_idx.min().date()
    p1 = panel_idx.max().date()
    # Episode must overlap panel; need enough bars inside [start, end]
    in_ep = panel_idx[(panel_idx.date >= ep.start) & (panel_idx.date <= ep.end)]
    in_ev = panel_idx[(panel_idx.date >= ep.eval_start) & (panel_idx.date <= ep.eval_end)]
    if ep.end < p0 or ep.start > p1:
        reason = (
            f"episode {ep.start}→{ep.end} precedes panel_start={p0} "
            f"(nav_start={coverage.get('nav_start')}, "
            f"mkt_0050_start={coverage.get('mkt_0050_start')})"
        )
        return {
            "available": False,
            "n_bars_episode": 0,
            "n_bars_eval": 0,
            "reason": reason,
            "fail_loud": bool(ep.required_for_global),
            "panel_start": str(p0),
            "panel_end": str(p1),
        }
    n_ep = int(len(in_ep))
    n_ev = int(len(in_ev))
    if n_ep < MIN_EPISODE_BARS:
        return {
            "available": False,
            "n_bars_episode": n_ep,
            "n_bars_eval": n_ev,
            "reason": f"insufficient episode bars ({n_ep}<{MIN_EPISODE_BARS})",
            "fail_loud": bool(ep.required_for_global),
            "panel_start": str(p0),
            "panel_end": str(p1),
        }
    return {
        "available": True,
        "n_bars_episode": n_ep,
        "n_bars_eval": n_ev,
        "reason": None,
        "fail_loud": False,
        "panel_start": str(p0),
        "panel_end": str(p1),
    }


def _local_trough(price: pd.Series, start: date, end: date) -> pd.Timestamp | None:
    w = price.loc[(price.index.date >= start) & (price.index.date <= end)].dropna()
    if len(w) < 5:
        return None
    return pd.Timestamp(w.idxmin())


def _decade_noncrisis_mask(
    idx: pd.DatetimeIndex,
    *,
    decade_start: int,
    crisis_years: set[int],
) -> np.ndarray:
    decade_end = decade_start + 9
    years = pd.Series(idx.year, index=idx)
    known = set(CRISIS_YEARS_BY_DECADE.get(decade_start, set())) | set(crisis_years)
    return (
        (years >= decade_start)
        & (years <= decade_end)
        & (~years.isin(known))
    ).to_numpy()


def _oos_verdict(row: dict[str, Any]) -> str:
    """Episode verdict for stress-high oriented arms.

    IC must be **positive** (aligned with fwd stress). Negative IC means the
    full-sample orientation anti-predicts in this episode → not WEAK credit.
    """
    if row.get("coverage_available") is False:
        return "NO_DATA"
    ic = row.get("ic_spearman_fwd_mdd_10")
    hit = row.get("hit_rate_episode")
    recall = row.get("recall_episode")
    f1 = row.get("f1_episode")
    lead = row.get("median_lead_days")
    fa = row.get("fa_rate_decade_noncrisis")
    if ic is None or hit is None:
        return "NO_DATA"
    hit_ok = float(hit) >= OOS_HIT_FLOOR and (
        recall is not None and float(recall) >= OOS_RECALL_FLOOR
    )
    f1_ok = f1 is not None and float(f1) >= OOS_F1_FLOOR
    lead_ok = lead is not None and float(lead) >= OOS_LEAD_DAYS_FLOOR
    fa_ok = fa is None or float(fa) <= OOS_FA_CEIL
    # Stress-high: require positive IC (not abs) for HIT
    ic_ok = float(ic) >= OOS_IC_ABS_FLOOR
    if ic_ok and hit_ok and f1_ok and fa_ok and lead_ok:
        return "OOS_HIT"
    # WEAK: partial positive detection — not anti-IC with zero recall
    weak_ic = float(ic) >= WEAK_IC_ABS
    weak_hit = (
        hit is not None
        and float(hit) >= WEAK_HIT
        and recall is not None
        and float(recall) >= WEAK_RECALL
    )
    if weak_ic or weak_hit:
        return "OOS_WEAK"
    return "OOS_MISS"


def _score_arm_episode(
    *,
    arm: str,
    family: str,
    xs: pd.Series,
    alert: pd.Series,
    ep: Episode,
    p: pd.DataFrame,
    nav_s: pd.Series,
    px_s: pd.Series,
    cov: dict[str, Any],
) -> dict[str, Any]:
    base = {
        "arm": arm,
        "family": family,
        "episode": ep.eid,
        "episode_label": ep.label,
        "episode_start": str(ep.start),
        "episode_end": str(ep.end),
        "eval_start": str(ep.eval_start),
        "eval_end": str(ep.eval_end),
        "required_for_global": ep.required_for_global,
        "in_sample_ref": ep.in_sample_ref,
        "optional": ep.optional,
        "coverage_available": bool(cov.get("available")),
        "coverage_reason": cov.get("reason"),
        "fail_loud": bool(cov.get("fail_loud")),
        "n_bars_episode": cov.get("n_bars_episode"),
        "n_bars_eval": cov.get("n_bars_eval"),
        "base_id": BASE_ID,
    }
    if not cov.get("available"):
        base["verdict"] = "NO_DATA"
        return base

    idx = p.index
    ep_mask = (idx.date >= ep.start) & (idx.date <= ep.end)
    ev_mask = (idx.date >= ep.eval_start) & (idx.date <= ep.eval_end)
    y_ep = pd.Series(ep_mask.astype(float), index=idx)
    y_mdd = p["fwd_mdd_10"]
    y_crash = p["fwd_ret_crash_10"]

    xs_e = xs.reindex(idx)
    alert_e = alert.reindex(idx).fillna(False).astype(bool)

    ic_mdd = _spearman_n(xs_e[ev_mask], y_mdd[ev_mask])
    ic_crash = _spearman_n(xs_e[ev_mask], y_crash[ev_mask])
    pe_mdd = None
    m = pd.DataFrame({"x": xs_e[ev_mask], "y": y_mdd[ev_mask]}).dropna()
    if len(m) >= MIN_IC_BARS:
        pe_mdd = _pearson(m["x"], m["y"])

    prf = _binary_prf(y_ep[ev_mask].astype(bool), alert_e[ev_mask])

    # Local trough: prefer L4 NAV, else 0050
    trough = _local_trough(nav_s.reindex(idx).ffill(), ep.start, ep.end)
    trough_src = "l4_nav"
    if trough is None:
        trough = _local_trough(px_s.reindex(idx).ffill(), ep.start, ep.end)
        trough_src = "0050"
    lead = None
    if trough is not None:
        lead = _median_lead_days(alert_e, window_start=ep.start, trough=trough)

    fa_mask = _decade_noncrisis_mask(
        idx,
        decade_start=ep.decade_start,
        crisis_years=set(ep.crisis_years),
    )
    n_fa = int(fa_mask.sum())
    fa = (float(alert_e.to_numpy()[fa_mask].sum()) / n_fa) if n_fa else None

    row = {
        **base,
        "ic_spearman_fwd_mdd_10": None if ic_mdd is None else round(float(ic_mdd), 4),
        "ic_pearson_fwd_mdd_10": None if pe_mdd is None else round(float(pe_mdd), 4),
        "ic_spearman_fwd_ret_crash_10": None if ic_crash is None else round(float(ic_crash), 4),
        "hit_rate_episode": prf["hit_rate"],
        "precision_episode": prf["precision"],
        "recall_episode": prf["recall"],
        "f1_episode": prf["f1"],
        "n_eval_prf": prf["n"],
        "median_lead_days": None if lead is None else round(float(lead), 2),
        "trough_date": None if trough is None else str(pd.Timestamp(trough).date()),
        "trough_source": trough_src if trough is not None else None,
        "fa_rate_decade_noncrisis": None if fa is None else round(float(fa), 4),
        "n_decade_noncrisis": n_fa,
        "n_alert_episode": int(alert_e[ep_mask].sum()),
        "n_alert_eval": int(alert_e[ev_mask].sum()),
        "alert_q": ALERT_Q,
    }
    row["verdict"] = _oos_verdict(row)
    return row


def _build_arm_series(
    panel: pd.DataFrame,
) -> tuple[dict[str, pd.Series], dict[str, dict[str, Any]], dict[str, pd.Series]]:
    """Continuous scores, meta, and alert masks for TARGET_ARMS."""
    arms, meta = build_refine_arms(panel)
    p = panel.copy()
    p["date"] = pd.to_datetime(p["date"])
    p = p.set_index("date").sort_index()
    y_primary = p["fwd_mdd_10"]

    scores: dict[str, pd.Series] = {}
    alerts: dict[str, pd.Series] = {}
    arm_meta: dict[str, dict[str, Any]] = {}
    missing: list[str] = []

    for name in TARGET_ARMS:
        if name not in arms:
            missing.append(name)
            continue
        m = meta[name]
        xs = arms[name].reindex(p.index)
        xs, _ = _orient_stress(xs, y_primary)
        alert_ov = m.get("alert_override")
        if alert_ov is not None:
            alert = alert_ov.reindex(p.index).fillna(False).astype(bool)
        else:
            alert = _alert_mask(xs, stress_high=True, q=ALERT_Q)
        scores[name] = xs
        alerts[name] = alert
        arm_meta[name] = {
            "family": m.get("family"),
            "is_champ": name == CHAMP_ARM,
            "is_0kbh_champ": name == "base::rvol20_l4",
        }
    if missing:
        raise RuntimeError(
            "TARGET_ARMS missing from build_refine_arms — refine script drift? "
            f"missing={missing}"
        )
    return scores, arm_meta, alerts


def _global_verdict(
    rows: list[dict[str, Any]],
    *,
    episode_cov: dict[str, dict[str, Any]],
) -> tuple[str, dict[str, Any]]:
    """Champ-centric global hist-OOS verdict on {GFC_2008, TW_CN_2015}."""
    champ_rows = [r for r in rows if r.get("arm") == CHAMP_ARM]
    by_ep = {r["episode"]: r for r in champ_rows}

    # Required episode availability
    gfc_cov = episode_cov.get("GFC_2008", {})
    y2015_cov = episode_cov.get("TW_CN_2015", {})
    gfc_avail = bool(gfc_cov.get("available"))
    y2015_avail = bool(y2015_cov.get("available"))

    if not gfc_avail and not y2015_avail:
        return "IP3_CRISIS_SIGNAL_HIST_OOS_NO_DATA", {
            "champ": CHAMP_ARM,
            "hist_hits": [],
            "hist_weaks": [],
            "hist_misses": [],
            "no_data": ["GFC_2008", "TW_CN_2015"],
            "note": "Both required historical episodes lack panel coverage",
        }

    def _v(eid: str) -> str:
        r = by_ep.get(eid)
        return str(r.get("verdict") if r else "NO_DATA")

    gfc_v = _v("GFC_2008")
    y2015_v = _v("TW_CN_2015")
    mar_v = _v("MAR2020")
    y2018_v = _v("Q4_2018")
    y2011_v = _v("EU_US_2011")

    hist_core = {"GFC_2008": gfc_v, "TW_CN_2015": y2015_v}
    hits = [e for e, v in hist_core.items() if v == "OOS_HIT"]
    weaks = [e for e, v in hist_core.items() if v == "OOS_WEAK"]
    misses = [e for e, v in hist_core.items() if v == "OOS_MISS"]
    no_data = [e for e, v in hist_core.items() if v == "NO_DATA"]

    mar_strong = mar_v in ("OOS_HIT", "OOS_WEAK")
    detail = {
        "champ": CHAMP_ARM,
        "champ_by_episode": {
            "GFC_2008": gfc_v,
            "TW_CN_2015": y2015_v,
            "EU_US_2011": y2011_v,
            "Q4_2018": y2018_v,
            "MAR2020": mar_v,
        },
        "hist_hits": hits,
        "hist_weaks": weaks,
        "hist_misses": misses,
        "no_data": no_data,
        "n_hist_oos_hit": len(hits),
        "mar2020_ref": mar_v,
    }

    if len(hits) >= 2:
        return "IP3_CRISIS_SIGNAL_HIST_OOS_ROBUST", detail
    if len(hits) == 1:
        return "IP3_CRISIS_SIGNAL_HIST_OOS_PARTIAL", detail
    # No OOS_HIT on {2008,2015}
    if mar_strong and (set(misses) | set(weaks) | set(no_data)) == {"GFC_2008", "TW_CN_2015"}:
        # Strong 2020 + weak/miss/no_data on both hist → overfit / no hist prove
        if misses or weaks:
            return "IP3_CRISIS_SIGNAL_HIST_OOS_OVERFIT_2020", detail
        # both NO_DATA only
        return "IP3_CRISIS_SIGNAL_HIST_OOS_NO_DATA", detail
    if not gfc_avail and y2015_v in ("OOS_MISS", "OOS_WEAK") and mar_strong:
        return "IP3_CRISIS_SIGNAL_HIST_OOS_OVERFIT_2020", detail
    if not gfc_avail and not y2015_avail:
        return "IP3_CRISIS_SIGNAL_HIST_OOS_NO_DATA", detail
    if mar_strong and not hits:
        return "IP3_CRISIS_SIGNAL_HIST_OOS_OVERFIT_2020", detail
    return "IP3_CRISIS_SIGNAL_HIST_OOS_NO_DATA", detail


def _floors() -> dict[str, Any]:
    return {
        "oos_ic_abs_floor": OOS_IC_ABS_FLOOR,
        "oos_hit_floor": OOS_HIT_FLOOR,
        "oos_recall_floor": OOS_RECALL_FLOOR,
        "oos_f1_floor": OOS_F1_FLOOR,
        "oos_lead_days_floor": OOS_LEAD_DAYS_FLOOR,
        "oos_fa_ceil": OOS_FA_CEIL,
        "weak_ic_abs": WEAK_IC_ABS,
        "weak_hit": WEAK_HIT,
        "weak_recall": WEAK_RECALL,
        "min_episode_bars": MIN_EPISODE_BARS,
        "min_ic_bars": MIN_IC_BARS,
        "alert_q": ALERT_Q,
        "primary_label": "fwd_mdd_10",
        "crash_label": "fwd_ret_crash_10",
        "global_rule": "champ OOS_HIT on ≥2 of {GFC_2008, TW_CN_2015} → ROBUST",
    }


def _patch_register(verdict: str, detail: dict[str, Any], day: str) -> None:
    reg = OPS / "HUMAN_DECISION_REGISTER.md"
    rt = reg.read_text(encoding="utf-8")
    by = detail.get("champ_by_episode") or {}
    new_row = (
        f"| 0kbj | hist crisis **signal** OOS (2008/2015/…, no apply) | "
        f"**STAGE A `{verdict}`** ({day}) | "
        f"Parents 0kbi/0kbh/0kbf · **SIGNAL_HIST_OOS/PARALLEL** · Exact T+1 lag-1 · "
        f"champ `{CHAMP_ARM}` · "
        f"GFC `{by.get('GFC_2008')}` · 2015 `{by.get('TW_CN_2015')}` · "
        f"2018 `{by.get('Q4_2018')}` · Mar2020 `{by.get('MAR2020')}` · "
        f"**signal≠apply** · soak freeze unchanged · Soft KEEP · Path4 OFF · "
        f"broker false · no live · `{DECISION_ID}.md` |"
    )
    lines = rt.splitlines()
    out: list[str] = []
    replaced = False
    for line in lines:
        if line.startswith("| 0kbj |"):
            out.append(new_row)
            replaced = True
        else:
            out.append(line)
    if not replaced:
        insert_at = None
        for i, line in enumerate(out):
            if line.startswith("| 0kbi |"):
                insert_at = i + 1
                break
        if insert_at is None:
            for i, line in enumerate(out):
                if line.startswith("| 0kbh |"):
                    insert_at = i + 1
                    break
        if insert_at is not None:
            out.insert(insert_at, new_row)
        else:
            out.append(new_row)
    reg.write_text("\n".join(out) + "\n", encoding="utf-8")


def _patch_ops_status(verdict: str, detail: dict[str, Any], day: str) -> None:
    ops = OPS / "OPS_STATUS.md"
    ot = ops.read_text(encoding="utf-8")
    by = detail.get("champ_by_episode") or {}
    line = (
        f"**Crisis signal hist OOS (SIGNAL_HIST_OOS/PARALLEL {day}):** Stage A "
        f"**`{verdict}`** · register **0kbj** · champ `{CHAMP_ARM}` · "
        f"GFC `{by.get('GFC_2008')}` · 2015 `{by.get('TW_CN_2015')}` · "
        f"2018 `{by.get('Q4_2018')}` · Mar2020-ref `{by.get('MAR2020')}` · "
        f"**signal≠apply** · soak freeze unchanged · Soft KEEP · Path4 OFF · "
        f"no live · `{DECISION_ID}.md`  "
    )
    ot2, n = re.subn(
        r"\*\*Crisis signal hist OOS \(SIGNAL_HIST_OOS/PARALLEL [^)]+\):\*\*.*",
        line,
        ot,
        count=1,
    )
    if n:
        ops.write_text(ot2, encoding="utf-8")
        return
    needle = "Y2020 crisis signal refine (SIGNAL_REFINE/PARALLEL"
    idx = ot.find(needle)
    if idx < 0:
        needle = "Y2020 crisis signal detect (SIGNAL/PARALLEL"
        idx = ot.find(needle)
    if idx >= 0:
        end = ot.find("\n", idx) + 1
        ops.write_text(ot[:end] + line + "\n" + ot[end:], encoding="utf-8")
        return
    ops.write_text(ot.rstrip() + "\n" + line + "\n", encoding="utf-8")


def _md_table(rows: list[dict[str, Any]], cols: list[tuple[str, str]]) -> list[str]:
    header = "| " + " | ".join(h for h, _ in cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    lines = [header, sep]
    for r in rows:
        cells = []
        for _, k in cols:
            v = r.get(k)
            cells.append("" if v is None else str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()
    day = generated[:10]

    panel, panel_meta = build_panel()
    panel.to_csv(OUT / "panel_crisis_signal_hist_oos.csv", index=False)

    p = panel.copy()
    p["date"] = pd.to_datetime(p["date"])
    p = p.set_index("date").sort_index()

    nav_s, base_note, nav_path = _load_nav_series()
    px_s = _load_0050_close()
    coverage = _data_coverage_report(p.index, nav_s, px_s)
    coverage["base_note"] = base_note
    coverage["nav_path"] = str(nav_path.relative_to(ROOT))

    scores, arm_meta, alerts = _build_arm_series(panel)

    episode_cov: dict[str, dict[str, Any]] = {}
    fail_loud_notes: list[str] = []
    for ep in EPISODES:
        cov = _episode_coverage(ep, p.index, coverage=coverage)
        episode_cov[ep.eid] = {**cov, "label": ep.label, "window": [str(ep.start), str(ep.end)]}
        if cov.get("fail_loud"):
            fail_loud_notes.append(
                f"FAIL_LOUD {ep.eid}: {cov.get('reason')} "
                f"(required hist episode; marking NO_DATA)"
            )

    rows: list[dict[str, Any]] = []
    for arm, xs in scores.items():
        for ep in EPISODES:
            row = _score_arm_episode(
                arm=arm,
                family=str(arm_meta[arm].get("family") or "?"),
                xs=xs,
                alert=alerts[arm],
                ep=ep,
                p=p,
                nav_s=nav_s,
                px_s=px_s,
                cov=episode_cov[ep.eid],
            )
            row["is_champ"] = bool(arm_meta[arm].get("is_champ"))
            row["is_0kbh_champ"] = bool(arm_meta[arm].get("is_0kbh_champ"))
            rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "hist_oos_arm_episode.csv", index=False)

    verdict, detail = _global_verdict(rows, episode_cov=episode_cov)
    floors = _floors()

    # Champ + top HIT summary tables
    champ_rows = [r for r in rows if r["arm"] == CHAMP_ARM]
    # Rank non-ref arms by n OOS_HIT across hist episodes (excl Mar2020)
    hist_eps = {e.eid for e in EPISODES if not e.in_sample_ref}
    arm_rank: list[dict[str, Any]] = []
    for arm in TARGET_ARMS:
        ar = [r for r in rows if r["arm"] == arm and r["episode"] in hist_eps]
        n_hit = sum(1 for r in ar if r.get("verdict") == "OOS_HIT")
        n_weak = sum(1 for r in ar if r.get("verdict") == "OOS_WEAK")
        n_miss = sum(1 for r in ar if r.get("verdict") == "OOS_MISS")
        n_nd = sum(1 for r in ar if r.get("verdict") == "NO_DATA")
        mar = next((r for r in rows if r["arm"] == arm and r["episode"] == "MAR2020"), None)
        arm_rank.append(
            {
                "arm": arm,
                "family": arm_meta[arm].get("family"),
                "is_champ": arm == CHAMP_ARM,
                "n_hist_oos_hit": n_hit,
                "n_hist_oos_weak": n_weak,
                "n_hist_oos_miss": n_miss,
                "n_hist_no_data": n_nd,
                "mar2020_verdict": None if mar is None else mar.get("verdict"),
                "mar2020_ic": None if mar is None else mar.get("ic_spearman_fwd_mdd_10"),
                "mar2020_hit": None if mar is None else mar.get("hit_rate_episode"),
            }
        )
    arm_rank.sort(
        key=lambda r: (
            int(r["is_champ"]),
            r["n_hist_oos_hit"],
            r["n_hist_oos_weak"],
            -(r["n_hist_oos_miss"]),
        ),
        reverse=True,
    )

    # Per-episode champ slice for screen
    per_ep_champ = {r["episode"]: r for r in champ_rows}

    counts = {
        "n_arm_episode": len(rows),
        "n_oos_hit": int(sum(1 for r in rows if r["verdict"] == "OOS_HIT")),
        "n_oos_weak": int(sum(1 for r in rows if r["verdict"] == "OOS_WEAK")),
        "n_oos_miss": int(sum(1 for r in rows if r["verdict"] == "OOS_MISS")),
        "n_no_data": int(sum(1 for r in rows if r["verdict"] == "NO_DATA")),
    }

    compare = {
        "0kbi": {
            "register": "0kbi",
            "verdict": "IP3_Y2020_CRISIS_SIGNAL_REFINE_HIT",
            "champ": CHAMP_ARM,
            "note": "In-sample Mar2020 refine HIT — this pack stress-tests hist OOS.",
        },
        "0kbh": {
            "register": "0kbh",
            "verdict": "IP3_Y2020_CRISIS_SIGNAL_WEAK",
            "champ": "rvol20_l4",
            "note": "Parent singles WEAK; included as base::rvol20_l4 reference arm.",
        },
        "0kbf": {
            "register": "0kbf",
            "verdict": "SOAK_OPEN",
            "note": "Soak freeze unchanged — hist OOS does not unlock SOAK_PASS.",
        },
    }

    disp = [
        "**SIGNAL_HIST_OOS / PARALLEL** — detection only; **signal ≠ apply**",
        "Does **not** unlock soak freeze · does **not** recommend LIVE wire",
        "No tip Soft promote · no year-oracle · Soft KEEP · Path4 OFF · broker false",
        (
            f"Data limitation: panel/NAV start {coverage.get('nav_start')}; "
            f"0050 start {coverage.get('mkt_0050_start')} — GFC 2008 = NO_DATA (fail loud)"
        ),
    ]
    if "ROBUST" in verdict:
        disp.append("Champ clears ≥2 hist cores — still no LIVE apply")
    elif "PARTIAL" in verdict:
        disp.append("Champ clears only one of {2008,2015} — treat as partial hist evidence")
    elif "OVERFIT" in verdict:
        disp.append(
            "Champ selected on Mar2020 (0kbi) fails OOS floors on available hist cores "
            "(2015 miss / 2008 no-data) — overfit-2020 risk elevated; do not promote "
            "signal→apply"
        )
    else:
        disp.append("Insufficient hist coverage / no OOS clear — no promote")

    optimize = [
        "Objective: hist OOS stress-test 0kbi SIGNAL_HIT arms on GFC/2015/(2011)/2018 + Mar2020 ref",
        f"Global `{verdict}` · champ `{CHAMP_ARM}` · by_ep={detail.get('champ_by_episode')}",
        f"Counts: HIT={counts['n_oos_hit']} WEAK={counts['n_oos_weak']} "
        f"MISS={counts['n_oos_miss']} NO_DATA={counts['n_no_data']} / n={counts['n_arm_episode']}",
        *fail_loud_notes,
        *disp,
    ]

    screen = {
        "id": SCREEN_ID,
        "register": REGISTER,
        "parents": list(PARENTS),
        "generated_at_utc": generated,
        "mech": MECH,
        "label_tag": LABEL_TAG,
        "verdict": verdict,
        "signal_not_apply": True,
        "soak_unlock": False,
        "live_wire_recommend": False,
        "size_overlay_promote": False,
        "year_oracle": False,
        "floors": floors,
        "coverage": coverage,
        "episode_coverage": episode_cov,
        "fail_loud_notes": fail_loud_notes,
        "target_arms": list(TARGET_ARMS),
        "champion_arm": CHAMP_ARM,
        "global_detail": detail,
        "counts": counts,
        "compare_parents": compare,
        "champ_by_episode": per_ep_champ,
        "arm_hist_rank": arm_rank,
        "rows": rows,
        "optimize_live": optimize,
        "soft_keep": True,
        "path4_live": False,
        "broker": False,
        "exact_t1": True,
        "panel_meta": panel_meta,
        "label": f"{SCREEN_ID}_{day}__{verdict}__{LABEL_TAG}",
    }
    (OUT / "screen.json").write_text(
        json.dumps(screen, indent=2, default=str) + "\n", encoding="utf-8"
    )
    (OUT / "summary.json").write_text(
        json.dumps(
            {
                "verdict": verdict,
                "detail": detail,
                "coverage": coverage,
                "episode_coverage": episode_cov,
                "fail_loud_notes": fail_loud_notes,
                "counts": counts,
                "floors": floors,
                "arm_hist_rank": arm_rank,
            },
            indent=2,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )
    (OUT / "base_diag.json").write_text(
        json.dumps(
            {
                "coverage": coverage,
                "episode_coverage": episode_cov,
                "floors": floors,
                "target_arms": list(TARGET_ARMS),
                "fail_loud_notes": fail_loud_notes,
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
            "",
            "## Question",
            "",
            "Do 0kbi SIGNAL_HIT refine arms (esp. champ `and::rvol63_l4&fuse_prem_neg5` "
            "and other HIT/k-confirm arms) still detect stress in **historical crisis "
            "windows** with lag-1 causal metrics, or are they 2020-only / overfit?",
            "",
            "## Episodes (TWSE-relevant)",
            "",
            "1. **GFC / 金融海嘯**: 2008-09 → 2009-03 (fail loud if missing)",
            "2. **2015**: TW/China crash 2015-06 → 2015-09 (eval 2015-04→2015-10)",
            "3. Optional: **2011** EU/US stress · **2018 Q4**",
            "4. **Mar2020** kept as in-sample reference (selection window)",
            "",
            "## Arms under test",
            "",
            f"- Champ: `{CHAMP_ARM}`",
            "- Other 0kbi SIGNAL_HIT arms (OR/AND/k-confirm) + `base::rvol20_l4` (0kbh)",
            "",
            "## Metrics (detection only)",
            "",
            "- IC vs fwd stress (`fwd_mdd_10` / `fwd_ret_crash_10`) in eval window",
            "- hit / recall / F1 inside episode (eval-window balanced)",
            "- median lead into local trough (L4 NAV, else 0050)",
            "- FA rate in non-crisis years of same decade",
            "- Per arm×episode: `OOS_HIT` / `OOS_WEAK` / `OOS_MISS` / `NO_DATA`",
            "",
            "## Global verdict rule",
            "",
            "- `IP3_CRISIS_SIGNAL_HIST_OOS_ROBUST` if champ clears OOS floors on ≥2 of {2008,2015}",
            "- `…_PARTIAL` if one historical episode only",
            "- `…_OVERFIT_2020` if strong on 2020 / weak-miss on available 2008&2015",
            "- `…_NO_DATA` if history too short",
            "",
            "## Hard constraints",
            "",
            "- Soft KEEP · Path4 OFF · broker false · Exact T+1 lag-1",
            "- **signal ≠ apply** · no LIVE · no tip Soft promote · no year-oracle",
            "- no size-apply promote · soak freeze unchanged",
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
                "signal_not_apply": True,
                "episodes": [
                    {
                        "id": e.eid,
                        "label": e.label,
                        "start": str(e.start),
                        "end": str(e.end),
                        "required_for_global": e.required_for_global,
                        "in_sample_ref": e.in_sample_ref,
                        "optional": e.optional,
                    }
                    for e in EPISODES
                ],
                "target_arms": list(TARGET_ARMS),
                "floors": floors,
                "label": f"{CHARTER_ID}_{day}__{LABEL_TAG}",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    write_repro_pointer(OPS / f"{CHARTER_ID}.json", REP / f"{CHARTER_ID}.json", kind="charter")

    # --- SCREEN md ---
    champ_table_cols = [
        ("episode", "episode"),
        ("verdict", "verdict"),
        ("IC_mdd10", "ic_spearman_fwd_mdd_10"),
        ("IC_crash10", "ic_spearman_fwd_ret_crash_10"),
        ("hit", "hit_rate_episode"),
        ("recall", "recall_episode"),
        ("F1", "f1_episode"),
        ("lead_d", "median_lead_days"),
        ("FA_dec", "fa_rate_decade_noncrisis"),
        ("trough", "trough_date"),
        ("note", "coverage_reason"),
    ]
    # Top HITs: pick a few non-champ with best hist rank for compact table
    top_hit_arms = [a["arm"] for a in arm_rank if not a["is_champ"]][:6]
    top_hit_rows = [
        r
        for r in rows
        if r["arm"] in top_hit_arms or r["arm"] == CHAMP_ARM
    ]
    # Pivot-ish markdown: one row per arm×episode for champ + top
    focus_arms = [CHAMP_ARM] + top_hit_arms
    focus_rows = [r for r in rows if r["arm"] in focus_arms]
    focus_rows.sort(
        key=lambda r: (
            0 if r["arm"] == CHAMP_ARM else 1,
            focus_arms.index(r["arm"]) if r["arm"] in focus_arms else 99,
            r["episode"],
        )
    )

    screen_md_lines = [
        f"# {SCREEN_ID}",
        "",
        f"Date: {day} · Verdict: **`{verdict}`** · champ=**`{CHAMP_ARM}`**",
        f"Register: **{REGISTER}** · **{LABEL_TAG}** · "
        f"HIT={counts['n_oos_hit']} · WEAK={counts['n_oos_weak']} · "
        f"MISS={counts['n_oos_miss']} · NO_DATA={counts['n_no_data']}",
        "",
        "## Data coverage (fail loud)",
        "",
        f"- NAV (`{coverage.get('base_id')}`): **{coverage.get('nav_start')}** → "
        f"{coverage.get('nav_end')}",
        f"- 0050 market: **{coverage.get('mkt_0050_start')}** → {coverage.get('mkt_0050_end')}",
        f"- Panel: {coverage.get('panel_start')} → {coverage.get('panel_end')}",
        f"- Note: {coverage.get('note')}",
    ]
    for note in fail_loud_notes:
        screen_md_lines.append(f"- **{note}**")
    screen_md_lines += [
        "",
        "## Floors (hist OOS)",
        "",
        f"- IC≥{OOS_IC_ABS_FLOOR} (positive / stress-high) · hit≥{OOS_HIT_FLOOR} · "
        f"recall≥{OOS_RECALL_FLOOR} · F1≥{OOS_F1_FLOOR} · lead≥{OOS_LEAD_DAYS_FLOOR}d · "
        f"FA≤{OOS_FA_CEIL}",
        "",
        "## Champ by episode",
        "",
    ]
    screen_md_lines += _md_table(champ_rows, champ_table_cols)
    screen_md_lines += [
        "",
        "## Champ + top HIT arms × episode",
        "",
    ]
    screen_md_lines += _md_table(
        focus_rows,
        [
            ("arm", "arm"),
            ("episode", "episode"),
            ("verdict", "verdict"),
            ("IC", "ic_spearman_fwd_mdd_10"),
            ("hit", "hit_rate_episode"),
            ("recall", "recall_episode"),
            ("F1", "f1_episode"),
            ("lead", "median_lead_days"),
            ("FA", "fa_rate_decade_noncrisis"),
        ],
    )
    screen_md_lines += [
        "",
        "## Arm hist rank (excl Mar2020 ref)",
        "",
    ]
    screen_md_lines += _md_table(
        arm_rank,
        [
            ("arm", "arm"),
            ("family", "family"),
            ("n_HIT", "n_hist_oos_hit"),
            ("n_WEAK", "n_hist_oos_weak"),
            ("n_MISS", "n_hist_oos_miss"),
            ("n_NO_DATA", "n_hist_no_data"),
            ("Mar2020", "mar2020_verdict"),
        ],
    )
    screen_md_lines += [
        "",
        "## Optimize / disposition",
        "",
    ]
    for i, line in enumerate(optimize, 1):
        screen_md_lines.append(f"{i}. {line}")
    screen_md_lines += [
        "",
        f"Label: `{SCREEN_ID}_{day}__{verdict}__{LABEL_TAG}`",
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
            f"Date: {day} · Verdict: **`{verdict}`** · top=**`{CHAMP_ARM}`**",
            f"Register: **{REGISTER}** · Parents: {', '.join(PARENTS)} · **{LABEL_TAG}**",
            "",
            "## Answer",
            "",
            f"- Global: **`{verdict}`**",
            f"- Champ `{CHAMP_ARM}` by episode: `{detail.get('champ_by_episode')}`",
            f"- Hist OOS_HIT cores: {detail.get('hist_hits')} · WEAK {detail.get('hist_weaks')} · "
            f"MISS {detail.get('hist_misses')} · NO_DATA {detail.get('no_data')}",
            f"- Mar2020 ref (in-sample): `{detail.get('mar2020_ref')}`",
            f"- Data start: NAV **{coverage.get('nav_start')}** · 0050 **{coverage.get('mkt_0050_start')}**",
            "",
            "## Constraints kept",
            "",
            "- Soft KEEP · Path4 OFF · broker false · Exact T+1",
            "- **signal ≠ apply** · no LIVE · no tip Soft promote · no year-oracle",
            "- soak freeze unchanged · no size-apply promote",
            "",
            "## Disposition",
            "",
        ]
        + [f"- {d}" for d in disp]
        + [
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
                "generated_at_utc": generated,
                "verdict": verdict,
                "champion_arm": CHAMP_ARM,
                "global_detail": detail,
                "coverage": coverage,
                "episode_coverage": episode_cov,
                "fail_loud_notes": fail_loud_notes,
                "counts": counts,
                "floors": floors,
                "arm_hist_rank": arm_rank,
                "champ_by_episode": per_ep_champ,
                "signal_not_apply": True,
                "soak_unlock": False,
                "live_wire_recommend": False,
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

    _patch_register(verdict, detail, day)
    _patch_ops_status(verdict, detail, day)

    print(json.dumps({"verdict": verdict, "detail": detail, "coverage": coverage}, indent=2, default=str))
    for note in fail_loud_notes:
        print(f"!! {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
