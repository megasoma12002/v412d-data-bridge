#!/usr/bin/env python3
"""Crisis feature **despecialization** Stage A (0kbn) — detection / light gate only.

SOAK-SAFE · PARALLEL paper research — **signal ≠ apply**.

Parents 0kbm / 0kbl / 0kbk / 0kbj / 0kbf:
- 0kbi AND champ ``and::rvol63_l4&fuse_prem_neg5`` cleared Mar2020 HIT floors
- 0kbj hist OOS landed ``OVERFIT_2020`` on that AND
- 0kbl major-DD atlas ``PARTIAL`` (fuse_prem only partial cross-era)
- 0kbm regime-router ``OVERFIT`` (2020 MDD help, cross-era improve_n=0)

Question: can transforms / normalizations / confirms on **existing** features
(rvol20/63, atr_like, MA gap, dd63, fuse_prem_neg, fuse_neg_flag, cool_defend,
consec_down — **no new exotic data**) produce detectors or light gates that:
1. Keep signal quality on stress
2. Fire outside 2020 (2015 / 2018 / 2022 major DDs)
3. Avoid year-dummy / Mar2020-only routers

Forbidden specialization:
- No year dummies, calendar month features, or episode labels as inputs
- No optimize-for-Mar2020-only as primary rank
- Primary rank = **cross-era score** (mean/min OOS IC across 2015/2018/2022/2020)
  with leave-one-era-out discipline

Verdict taxonomy:
- ``CRISIS_FEAT_DESPEC_HIT`` — IC floors + fires ≥2 of {2015,2018,2022} with
  hit/recall floors + OOS IC ex-2020 OK + year-dummy ceil
- ``CRISIS_FEAT_DESPEC_PARTIAL`` — multi-era lift without full HIT floors
- ``CRISIS_FEAT_DESPEC_STILL_SPEC`` — still 2020-dominated
- ``CRISIS_FEAT_DESPEC_NO_EDGE``

Hard constraints:
- Soft KEEP · Path4 OFF · broker false · Exact T+1 lag-1
- soak freeze unchanged · signal≠apply default
- no tip Soft LIVE · no Soft FIN/TEL ACCEPT

Repro: ``PYTHONPATH=scripts python3 scripts/tipsoft_ip3_crisis_feat_despec_stagea.py``
"""
from __future__ import annotations

import itertools
import json
import re
import subprocess
from dataclasses import dataclass
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
    FA_OUTSIDE_2020_CEIL,
    IC_ABS_FLOOR,
    LIVESTACK,
    OOS_IC_ABS_FLOOR,
    YEAR_DUMMY_IC_ABS_CEIL,
    _alert_mask,
    _binary_prf,
    _pearson,
    _spearman,
    build_panel,
    counterfactual_cash_gate,
)

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "tipsoft-ip3-crisis-feat-despec-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "TIPSOFT_IP3_CRISIS_FEAT_DESPEC_STAGEA_CHARTER"
SCREEN_ID = "TIPSOFT_IP3_CRISIS_FEAT_DESPEC_STAGEA_SCREEN"
DECISION_ID = "TIPSOFT_IP3_CRISIS_FEAT_DESPEC_STAGEA_DECISION_PACK"
REGISTER = "0kbn"
PARENTS = ("0kbm", "0kbl", "0kbk", "0kbj", "0kbf")
MECH = "TIPSOFT_IP3_CRISIS_FEAT_DESPEC"
LABEL_TAG = "CRISIS_FEAT_DESPEC_PARALLEL"

# Existing features only (0kbh/0kbi inventory) — no exotic new series
BASE_FEATURES: tuple[str, ...] = (
    "rvol20_l4",
    "rvol63_l4",
    "rvol20_mkt",
    "rvol63_mkt",
    "atr_like_20",
    "neg_gap_ma60",
    "neg_gap_ma120",
    "neg_gap_ma200",
    "dd63_l4",
    "dd63_mkt",
    "dd63_soft",
    "fuse_prem_neg5",
    "fuse_neg_flag",
    "cool_defend_l1",
    "consec_down_mkt",
    "consec_down_l4",
)

RVOL_FEATURES = ("rvol20_l4", "rvol63_l4", "rvol20_mkt", "rvol63_mkt")

# Cross-era windows (major DD refs from 0kbl / 0kbj)
ERA_KEYS = ("2015", "2018", "2022", "2020")
NON2020_ERAS = ("2015", "2018", "2022")


@dataclass(frozen=True)
class EraWindow:
    key: str
    label: str
    start: date
    end: date
    eval_start: date
    eval_end: date


ERAS: tuple[EraWindow, ...] = (
    EraWindow(
        "2015",
        "2015 TW/China",
        date(2015, 6, 1),
        date(2015, 9, 30),
        date(2015, 4, 1),
        date(2015, 10, 31),
    ),
    EraWindow(
        "2018",
        "2018 Q4",
        date(2018, 10, 1),
        date(2018, 12, 24),
        date(2018, 8, 1),
        date(2019, 2, 28),
    ),
    EraWindow(
        "2022",
        "2022 bear",
        date(2022, 1, 1),
        date(2022, 10, 31),
        date(2021, 11, 1),
        date(2022, 12, 31),
    ),
    EraWindow(
        "2020",
        "Mar2020 cliff",
        date(2020, 2, 20),
        date(2020, 3, 23),
        date(2020, 1, 2),
        date(2020, 6, 30),
    ),
)

# Floors (detection) — HIT needs multi-era fire, not Mar-only
EP_IC_FLOOR = 0.08
EP_HIT_FLOOR = 0.55
EP_RECALL_FLOOR = 0.30
EP_WEAK_IC = 0.04
WEAK_HIT = 0.50
WEAK_RECALL = 0.20
MIN_EP_BARS = 12
MIN_IC_BARS = 40
GLOBAL_IC_FLOOR = IC_ABS_FLOOR
HIT_NON2020_MIN = 2  # fires on ≥2 of {2015,2018,2022}
ROLL_WINS = (252, 504)
CONFIRM_KS = (2, 3)
DELTA_LAGS = (5, 21)
AND_TOP_N = 8  # top despec singles by LOO for AND grid

# Frozen prior arms for explicit comparison
CHAMP_0KBI = "and::rvol63_l4&fuse_prem_neg5"
BASE_0KBH = "raw::rvol20_l4"
PRIOR_0KBM = {
    "register": "0kbm",
    "verdict": "CRISIS_REGIME_IMPROVE_OVERFIT",
    "champ": "R_RC_C00_G05",
    "held": 0.5277,
    "y2020_mdd_imp": 5.4852,
    "mar2020_mdd_imp": 5.5769,
    "cross_era_improve_n": 0,
    "note": "regime router OVERFIT — 2020 MDD help, cross-era improve_n=0",
}
PRIOR_0KBI = {
    "register": "0kbi",
    "verdict": "IP3_Y2020_CRISIS_SIGNAL_REFINE_HIT",
    "champ": CHAMP_0KBI,
    "note": "AND champ Mar2020 HIT; 0kbj hist OOS OVERFIT_2020",
}


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


def _spearman_n(x: pd.Series, y: pd.Series, *, min_n: int = MIN_IC_BARS) -> float | None:
    m = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(m) < int(min_n):
        return None
    rx = m["x"].rank(method="average")
    ry = m["y"].rank(method="average")
    v = float(rx.corr(ry, method="pearson"))
    return None if v != v else v


def _rank_pct(s: pd.Series) -> pd.Series:
    return s.rank(method="average", pct=True)


def _orient_stress(x: pd.Series, y_primary: pd.Series) -> tuple[pd.Series, bool]:
    sp = _spearman(x, y_primary)
    stress_high = True if sp is None else (float(sp) >= 0)
    return (x if stress_high else -x), stress_high


def _rolling_z(x: pd.Series, win: int) -> pd.Series:
    """Causal z-score vs trailing window ending yesterday (x already lag-1)."""
    mu = x.shift(1).rolling(int(win), min_periods=max(40, int(win) // 5)).mean()
    sd = x.shift(1).rolling(int(win), min_periods=max(40, int(win) // 5)).std()
    return (x - mu) / sd.replace(0.0, np.nan)


def _rolling_pct(x: pd.Series, win: int) -> pd.Series:
    """Causal percentile rank of x[t] in trailing window x[t-win:t-1].

    Uses a compact numpy loop (faster than rolling.apply for long panels).
    """
    vals = x.to_numpy(dtype=float)
    n = len(vals)
    out = np.full(n, np.nan)
    w = int(win)
    min_hist = max(20, w // 10)
    for i in range(n):
        v = vals[i]
        if v != v:  # NaN
            continue
        lo = max(0, i - w)
        hist = vals[lo:i]  # excludes today → causal vs trailing
        hist = hist[~np.isnan(hist)]
        if len(hist) < min_hist:
            continue
        out[i] = float((hist <= v).mean())
    return pd.Series(out, index=x.index)


def _vs_long_median(x: pd.Series, win: int) -> pd.Series:
    med = x.shift(1).rolling(int(win), min_periods=max(40, int(win) // 5)).median()
    return x - med


def _k_confirm(flag: pd.Series, k: int) -> pd.Series:
    f = flag.fillna(0.0).astype(float)
    out = f.copy()
    for i in range(1, int(k)):
        out = out * f.shift(i).fillna(0.0)
    return (out >= 0.999).astype(float)


def _delta(x: pd.Series, lag: int) -> pd.Series:
    return x - x.shift(int(lag))


def build_despec_arms(
    panel: pd.DataFrame,
) -> tuple[dict[str, pd.Series], dict[str, dict[str, Any]]]:
    """Build raw + despec transforms + small AND grid (lag-1 causal)."""
    p = panel.copy()
    p["date"] = pd.to_datetime(p["date"])
    p = p.set_index("date").sort_index()
    y_primary = p["fwd_mdd_10"]

    oriented: dict[str, pd.Series] = {}
    for col in BASE_FEATURES:
        if col not in p.columns:
            continue
        xs, _ = _orient_stress(p[col], y_primary)
        oriented[col] = xs

    arms: dict[str, pd.Series] = {}
    meta: dict[str, dict[str, Any]] = {}

    # 1) Raw baselines
    for col, xs in oriented.items():
        name = f"raw::{col}"
        arms[name] = xs
        meta[name] = {"family": "raw", "base": col, "transform": "raw"}

    # Frozen 0kbi AND (rank-min) for comparison
    if "rvol63_l4" in oriented and "fuse_prem_neg5" in oriented:
        ranks = {
            "rvol63_l4": _rank_pct(oriented["rvol63_l4"]),
            "fuse_prem_neg5": _rank_pct(oriented["fuse_prem_neg5"]),
        }
        arms[CHAMP_0KBI] = pd.concat(
            [ranks["rvol63_l4"], ranks["fuse_prem_neg5"]], axis=1
        ).min(axis=1)
        meta[CHAMP_0KBI] = {
            "family": "prior_0kbi",
            "base": "rvol63_l4&fuse_prem_neg5",
            "transform": "and_rankmin",
            "is_0kbi_champ": True,
        }

    # 2–4) Rolling z / pct / vs-median + 3) vol-of-vol / delta on rvol
    transformed: dict[str, pd.Series] = {}
    for col, xs in oriented.items():
        for w in ROLL_WINS:
            zname = f"z{w}::{col}"
            transformed[zname] = _rolling_z(xs, w)
            meta[zname] = {"family": "zscore", "base": col, "transform": f"z{w}", "win": w}

            pname = f"pct{w}::{col}"
            transformed[pname] = _rolling_pct(xs, w)
            meta[pname] = {
                "family": "pct_rank",
                "base": col,
                "transform": f"pct{w}",
                "win": w,
            }

            mname = f"vsmed{w}::{col}"
            transformed[mname] = _vs_long_median(xs, w)
            meta[mname] = {
                "family": "vs_median",
                "base": col,
                "transform": f"vsmed{w}",
                "win": w,
            }

        if col in RVOL_FEATURES:
            for lag in DELTA_LAGS:
                dname = f"d{lag}::{col}"
                transformed[dname] = _delta(xs, lag)
                meta[dname] = {
                    "family": "delta_rvol",
                    "base": col,
                    "transform": f"d{lag}",
                    "lag": lag,
                }

    for name, xs in transformed.items():
        arms[name] = xs

    # 5) k-confirm on transformed continuous → alert-then-confirm
    # Use causal top-quantile flag then k-confirm (keeps score = confirmed flag)
    confirm_src = [
        n
        for n, m in meta.items()
        if m["family"] in ("zscore", "pct_rank", "vs_median", "delta_rvol", "raw")
        and m.get("base")
        in (
            "rvol20_l4",
            "rvol63_l4",
            "atr_like_20",
            "neg_gap_ma200",
            "dd63_l4",
            "fuse_prem_neg5",
            "fuse_neg_flag",
            "cool_defend_l1",
            "consec_down_mkt",
        )
    ]
    # Prefer 252-window transforms + raw for confirm grid (keep small)
    confirm_src = [
        n
        for n in confirm_src
        if n.startswith("raw::")
        or n.startswith("z252::")
        or n.startswith("pct252::")
        or n.startswith("vsmed252::")
        or n.startswith("d5::")
        or n.startswith("d21::")
    ]
    for src in confirm_src:
        xs = arms[src]
        uniq = xs.dropna().unique()
        if len(uniq) <= 4 and set(np.round(uniq, 6)).issubset({0.0, 1.0}):
            base_flag = (xs >= 0.5).astype(float)
        else:
            base_flag = _alert_mask(xs, stress_high=True, q=ALERT_Q).astype(float)
        for k in CONFIRM_KS:
            cname = f"k{k}::{src}"
            arms[cname] = _k_confirm(base_flag, k)
            meta[cname] = {
                "family": "k_confirm",
                "base": meta[src].get("base"),
                "transform": f"k{k}:{meta[src].get('transform')}",
                "src": src,
                "k": k,
            }

    # 6) Simple AND of two despec'd continuous features (filled after first-pass
    # ranking in main — placeholder returns current arms; AND added later)
    return arms, meta


def _era_masks(idx: pd.DatetimeIndex) -> dict[str, dict[str, pd.Series]]:
    out: dict[str, dict[str, pd.Series]] = {}
    for era in ERAS:
        ep = pd.Series(
            (idx.date >= era.start) & (idx.date <= era.end),
            index=idx,
        )
        ev = pd.Series(
            (idx.date >= era.eval_start) & (idx.date <= era.eval_end),
            index=idx,
        )
        out[era.key] = {"episode": ep, "eval": ev, "era": era}
    return out


def score_arm_on_era(
    *,
    name: str,
    family: str,
    xs: pd.Series,
    p: pd.DataFrame,
    era: EraWindow,
    masks: dict[str, pd.Series],
) -> dict[str, Any]:
    """IC / hit / recall inside one era (eval-local binary labels)."""
    y = p["fwd_mdd_10"]
    idx = p.index
    ep = masks["episode"]
    ev = masks["eval"]
    n_ep = int(ep.sum())
    if n_ep < MIN_EP_BARS:
        return {
            "arm": name,
            "family": family,
            "era": era.key,
            "n_bars": n_ep,
            "ic_spearman": None,
            "hit_rate": None,
            "recall": None,
            "f1": None,
            "precision": None,
            "verdict": "NO_DATA",
        }

    # Continuous orientation already stress-high
    ic = _spearman_n(xs[ep], y[ep], min_n=min(MIN_IC_BARS, max(8, n_ep // 2)))

    uniq = xs.dropna().unique()
    if len(uniq) <= 4 and set(np.round(uniq, 6)).issubset({0.0, 1.0}):
        alert = (xs >= 0.5).fillna(False)
    else:
        # Era-local quantile on eval window (causal feature values; threshold
        # fitted only on eval-window distribution for fair era score — not a
        # year-dummy input)
        local = xs[ev].dropna()
        if len(local) < 20:
            alert = _alert_mask(xs, stress_high=True, q=ALERT_Q)
        else:
            thr = float(local.quantile(ALERT_Q))
            alert = (xs >= thr).fillna(False)

    prf = _binary_prf(ep[ev].astype(bool), alert[ev])
    v = "MISS"
    if ic is not None and prf["hit_rate"] is not None:
        if (
            float(ic) >= EP_IC_FLOOR
            and float(prf["hit_rate"]) >= EP_HIT_FLOOR
            and prf["recall"] is not None
            and float(prf["recall"]) >= EP_RECALL_FLOOR
        ):
            v = "ERA_HIT"
        elif float(ic) >= EP_WEAK_IC and (
            float(prf["hit_rate"]) >= WEAK_HIT
            or (prf["recall"] is not None and float(prf["recall"]) >= WEAK_RECALL)
        ):
            v = "ERA_WEAK"
    return {
        "arm": name,
        "family": family,
        "era": era.key,
        "n_bars": n_ep,
        "ic_spearman": None if ic is None else round(float(ic), 4),
        "hit_rate": prf["hit_rate"],
        "recall": prf["recall"],
        "f1": prf["f1"],
        "precision": prf["precision"],
        "verdict": v,
    }


def score_arm_global(
    *,
    name: str,
    family: str,
    xs: pd.Series,
    p: pd.DataFrame,
    meta_row: dict[str, Any],
) -> dict[str, Any]:
    """Full-sample IC + OOS ex-2020 + year-dummy abs IC (diagnostic only)."""
    y = p["fwd_mdd_10"]
    y_year = p["year2020_dummy"] if "year2020_dummy" in p.columns else p["in_y2020"]
    ex2020 = y_year < 0.5
    sp = _spearman(xs, y)
    pe = _pearson(xs, y)
    sp_oos = _spearman(xs[ex2020], y[ex2020])
    yd = _spearman(xs, y_year)
    yd_abs = None if yd is None else abs(float(yd))

    uniq = xs.dropna().unique()
    if len(uniq) <= 4 and set(np.round(uniq, 6)).issubset({0.0, 1.0}):
        alert = (xs >= 0.5).fillna(False)
    else:
        alert = _alert_mask(xs, stress_high=True, q=ALERT_Q)

    # Stress label: L4 dd cross 8%
    y_stress = (
        p["l4_dd_cross_8"].astype(bool)
        if "l4_dd_cross_8" in p.columns
        else (y >= y.quantile(0.90))
    )
    prf = _binary_prf(y_stress, alert)
    fa_n = int((alert & ex2020).sum())
    n_out = int(ex2020.sum())
    fa = (fa_n / n_out) if n_out else None

    return {
        "arm": name,
        "family": family,
        "base": meta_row.get("base"),
        "transform": meta_row.get("transform"),
        "ic_spearman_primary": None if sp is None else round(float(sp), 4),
        "ic_pearson_primary": None if pe is None else round(float(pe), 4),
        "ic_spearman_oos_ex2020": None if sp_oos is None else round(float(sp_oos), 4),
        "year2020_dummy_abs_ic": None if yd_abs is None else round(float(yd_abs), 4),
        "hit_rate_stress": prf["hit_rate"],
        "recall_stress": prf["recall"],
        "f1_stress": prf["f1"],
        "fa_rate_outside_2020": None if fa is None else round(float(fa), 4),
        "pct_alert": round(float(alert.mean()) * 100, 2) if len(alert) else None,
    }


def cross_era_aggregate(per_era: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Primary rank key: mean/min era IC + non-2020 HIT count (not Mar-only)."""
    arms = sorted({r["arm"] for r in per_era})
    rows: list[dict[str, Any]] = []
    for arm in arms:
        xs = [r for r in per_era if r["arm"] == arm and r["verdict"] != "NO_DATA"]
        if not xs:
            continue
        ics = [float(r["ic_spearman"]) for r in xs if r["ic_spearman"] is not None]
        by_era = {r["era"]: r for r in xs}
        hits = [e for e, r in by_era.items() if r["verdict"] == "ERA_HIT"]
        weaks = [e for e, r in by_era.items() if r["verdict"] == "ERA_WEAK"]
        non2020_hits = [e for e in hits if e in NON2020_ERAS]
        non2020_weaks = [e for e in weaks if e in NON2020_ERAS]
        mean_ic = float(np.mean(ics)) if ics else None
        min_ic = float(np.min(ics)) if ics else None
        # Cross-era score: prefer mean IC, break ties with min IC + non2020 hits
        score = (mean_ic or -1.0) + 0.25 * (min_ic or -1.0) + 0.15 * len(non2020_hits)
        rows.append(
            {
                "arm": arm,
                "family": xs[0].get("family"),
                "n_eras_scored": len(by_era),
                "mean_ic": None if mean_ic is None else round(mean_ic, 4),
                "min_ic": None if min_ic is None else round(min_ic, 4),
                "cross_era_score": round(float(score), 4),
                "n_era_hit": len(hits),
                "n_era_weak": len(weaks),
                "eras_hit": hits,
                "eras_weak": weaks,
                "n_non2020_hit": len(non2020_hits),
                "non2020_eras_hit": non2020_hits,
                "n_non2020_weak": len(non2020_weaks),
                "era_ics": {
                    e: (None if by_era[e]["ic_spearman"] is None else by_era[e]["ic_spearman"])
                    for e in ERA_KEYS
                    if e in by_era
                },
                "era_verdicts": {e: by_era[e]["verdict"] for e in ERA_KEYS if e in by_era},
            }
        )
    rows.sort(
        key=lambda r: (
            r["cross_era_score"],
            r["n_non2020_hit"],
            r["mean_ic"] or -1.0,
            r["min_ic"] or -1.0,
        ),
        reverse=True,
    )
    return rows


def leave_one_era_out(
    per_era: list[dict[str, Any]],
    *,
    candidate_arms: list[str] | None = None,
) -> list[dict[str, Any]]:
    """For each held-out era, pick best arm on the other eras; score held-out."""
    arms = candidate_arms or sorted({r["arm"] for r in per_era})
    rows: list[dict[str, Any]] = []
    for held in ERA_KEYS:
        train_eras = [e for e in ERA_KEYS if e != held]
        best_arm = None
        best_score = -1e9
        for arm in arms:
            xs = [
                r
                for r in per_era
                if r["arm"] == arm
                and r["era"] in train_eras
                and r["verdict"] != "NO_DATA"
                and r["ic_spearman"] is not None
            ]
            if len(xs) < 2:
                continue
            ics = [float(r["ic_spearman"]) for r in xs]
            non2020_hits = sum(
                1
                for r in xs
                if r["verdict"] == "ERA_HIT" and r["era"] in NON2020_ERAS
            )
            score = float(np.mean(ics)) + 0.25 * float(np.min(ics)) + 0.15 * non2020_hits
            if score > best_score:
                best_score = score
                best_arm = arm
        held_row = next(
            (r for r in per_era if r["arm"] == best_arm and r["era"] == held),
            None,
        )
        rows.append(
            {
                "held_out_era": held,
                "train_eras": train_eras,
                "selected_arm": best_arm,
                "train_score": None if best_arm is None else round(float(best_score), 4),
                "held_verdict": None if held_row is None else held_row["verdict"],
                "held_ic": None if held_row is None else held_row["ic_spearman"],
                "held_hit": None if held_row is None else held_row["hit_rate"],
                "held_recall": None if held_row is None else held_row["recall"],
            }
        )
    return rows


def _arm_despec_verdict(
    cross: dict[str, Any],
    glob: dict[str, Any],
) -> str:
    """Per-arm despec class."""
    ic = glob.get("ic_spearman_primary")
    oos = glob.get("ic_spearman_oos_ex2020")
    yd = glob.get("year2020_dummy_abs_ic")
    n_non = int(cross.get("n_non2020_hit") or 0)
    n_hit = int(cross.get("n_era_hit") or 0)
    n_weak = int(cross.get("n_era_weak") or 0)
    eras_hit = list(cross.get("eras_hit") or [])
    year_dummy = yd is not None and float(yd) >= YEAR_DUMMY_IC_ABS_CEIL
    oos_ok = oos is not None and abs(float(oos)) >= OOS_IC_ABS_FLOOR
    ic_ok = ic is not None and abs(float(ic)) >= GLOBAL_IC_FLOOR
    fa = glob.get("fa_rate_outside_2020")
    fa_ok = fa is None or float(fa) <= FA_OUTSIDE_2020_CEIL

    only_2020 = n_hit > 0 and n_non == 0 and (
        not eras_hit or all(str(e) == "2020" for e in eras_hit)
    )
    if only_2020 or (year_dummy and n_non == 0):
        return "STILL_SPEC"

    if (
        ic_ok
        and oos_ok
        and (not year_dummy)
        and fa_ok
        and n_non >= HIT_NON2020_MIN
    ):
        return "HIT"

    mean_ic = cross.get("mean_ic")
    mean_ok = mean_ic is not None and float(mean_ic) >= EP_WEAK_IC
    multi = (n_hit + n_weak) >= 2 and (
        n_non >= 1
        or any(e in NON2020_ERAS for e in (cross.get("eras_weak") or []))
    )
    # PARTIAL: multi-era non-2020 lift with either global/OOS IC or solid mean era IC
    if multi and n_non >= 1 and (
        ic_ok
        or (oos is not None and abs(float(oos)) >= EP_WEAK_IC)
        or mean_ok
    ):
        return "PARTIAL"

    if n_hit + n_weak == 0:
        return "NO_EDGE"
    if n_non == 0:
        return "STILL_SPEC"
    # Single non-2020 era with positive mean IC → weak PARTIAL; else no edge
    if n_non >= 1 and mean_ok and n_hit >= 1:
        return "PARTIAL"
    return "NO_EDGE"


def global_verdict(
    arm_rows: list[dict[str, Any]],
) -> tuple[str, dict[str, Any] | None]:
    if not arm_rows:
        return "CRISIS_FEAT_DESPEC_NO_EDGE", None
    hits = [r for r in arm_rows if r.get("despec_verdict") == "HIT"]
    partials = [r for r in arm_rows if r.get("despec_verdict") == "PARTIAL"]
    specs = [r for r in arm_rows if r.get("despec_verdict") == "STILL_SPEC"]

    def _key(r: dict[str, Any]) -> tuple:
        return (
            float(r.get("cross_era_score") or -1),
            int(r.get("n_non2020_hit") or 0),
            float(r.get("mean_ic") or -1),
            float(r.get("ic_spearman_oos_ex2020") or -1),
        )

    if hits:
        champ = sorted(hits, key=_key, reverse=True)[0]
        return "CRISIS_FEAT_DESPEC_HIT", champ
    if partials:
        champ = sorted(partials, key=_key, reverse=True)[0]
        return "CRISIS_FEAT_DESPEC_PARTIAL", champ
    if specs:
        champ = sorted(specs, key=_key, reverse=True)[0]
        return "CRISIS_FEAT_DESPEC_STILL_SPEC", champ
    champ = sorted(arm_rows, key=_key, reverse=True)[0]
    return "CRISIS_FEAT_DESPEC_NO_EDGE", champ


def _add_and_grid(
    arms: dict[str, pd.Series],
    meta: dict[str, dict[str, Any]],
    top_singles: list[str],
) -> None:
    """In-place: simple AND of two despec'd features (rank-min)."""
    pairs = list(itertools.combinations(top_singles[:AND_TOP_N], 2))
    for a, b in pairs:
        if a not in arms or b not in arms:
            continue
        # skip if either is already AND / k-confirm binary-only prior
        if meta.get(a, {}).get("family") == "and_despec":
            continue
        ra = _rank_pct(arms[a])
        rb = _rank_pct(arms[b])
        name = f"and::{a}&{b}"
        if name in arms:
            continue
        arms[name] = pd.concat([ra, rb], axis=1).min(axis=1)
        meta[name] = {
            "family": "and_despec",
            "base": f"{meta.get(a, {}).get('base')}|{meta.get(b, {}).get('base')}",
            "transform": f"and({meta.get(a, {}).get('transform')},{meta.get(b, {}).get('transform')})",
            "src_a": a,
            "src_b": b,
        }


def _patch_register(verdict: str, champ: dict[str, Any] | None, day: str, tip: str) -> None:
    reg = OPS / "HUMAN_DECISION_REGISTER.md"
    rt = reg.read_text(encoding="utf-8")
    c = champ or {}
    new_row = (
        f"| {REGISTER} | crisis **feature despec** (transforms on existing feats) | "
        f"**STAGE A `{verdict}`** ({day}) | "
        f"Parents {'/'.join(PARENTS)} · **{LABEL_TAG}** · Exact T+1 lag-1 · "
        f"top `{c.get('arm')}` cross-era **{c.get('cross_era_score')}** · "
        f"non2020_HIT **{c.get('n_non2020_hit')}** · "
        f"meanIC **{c.get('mean_ic')}** · OOS ex-2020 **{c.get('ic_spearman_oos_ex2020')}** · "
        f"vs 0kbi AND / 0kbm OVERFIT · **signal≠apply** · soak freeze unchanged · "
        f"Soft KEEP · Path4 OFF · no live · tip `{tip[:12]}` · `{DECISION_ID}.md` |"
    )
    lines = rt.splitlines()
    out: list[str] = []
    replaced = False
    for line in lines:
        if line.startswith(f"| {REGISTER} |"):
            out.append(new_row)
            replaced = True
        else:
            out.append(line)
    if not replaced:
        insert_at = None
        for i, line in enumerate(out):
            if line.startswith("| 0kbf |") or line.startswith("| 0kbe |"):
                insert_at = i
                break
        if insert_at is None:
            for i, line in enumerate(out):
                if line.startswith("| 0kbd |"):
                    insert_at = i
                    break
        if insert_at is not None:
            out.insert(insert_at, new_row)
        else:
            out.append(new_row)
    reg.write_text("\n".join(out) + "\n", encoding="utf-8")


def _patch_ops_status(verdict: str, champ: dict[str, Any] | None, day: str, tip: str) -> None:
    ops = OPS / "OPS_STATUS.md"
    ot = ops.read_text(encoding="utf-8")
    c = champ or {}
    line = (
        f"**Crisis feature despec (CRISIS_FEAT_DESPEC/PARALLEL {day}):** Stage A "
        f"**`{verdict}`** · register **{REGISTER}** · top `{c.get('arm')}` "
        f"cross-era **{c.get('cross_era_score')}** · non2020_HIT **{c.get('n_non2020_hit')}** · "
        f"vs 0kbi AND / 0kbm OVERFIT · **signal≠apply** · soak freeze unchanged · "
        f"Soft KEEP · Path4 OFF · no live · tip `{tip[:12]}` · `{DECISION_ID}.md`  "
    )
    ot2, n = re.subn(
        r"\*\*Crisis feature despec \(CRISIS_FEAT_DESPEC/PARALLEL [^)]+\):\*\*.*",
        line,
        ot,
        count=1,
    )
    if n:
        ops.write_text(ot2, encoding="utf-8")
        return
    needle = "DD_SWITCH soak gate (2026-10-03 cadence):"
    idx = ot.find(needle)
    if idx >= 0:
        end = ot.find("\n", idx) + 1
        ops.write_text(ot[:end] + line + "\n" + ot[end:], encoding="utf-8")
        return
    ops.write_text(ot.rstrip() + "\n\n" + line + "\n", encoding="utf-8")


def run() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    REP.mkdir(parents=True, exist_ok=True)
    OPS.mkdir(parents=True, exist_ok=True)

    panel, panel_meta = build_panel()
    p = panel.copy()
    p["date"] = pd.to_datetime(p["date"])
    p = p.set_index("date").sort_index()

    arms, meta = build_despec_arms(panel)
    era_masks = _era_masks(p.index)

    # First pass: score all non-AND arms per era
    per_era: list[dict[str, Any]] = []
    for name, xs in arms.items():
        fam = meta.get(name, {}).get("family", "unknown")
        xs2 = xs.reindex(p.index)
        for era in ERAS:
            per_era.append(
                score_arm_on_era(
                    name=name,
                    family=fam,
                    xs=xs2,
                    p=p,
                    era=era,
                    masks=era_masks[era.key],
                )
            )

    cross1 = cross_era_aggregate(per_era)
    # Prefer despec families (not raw-only / prior) for AND parents
    despec_singles = [
        r["arm"]
        for r in cross1
        if meta.get(r["arm"], {}).get("family")
        in ("zscore", "pct_rank", "vs_median", "delta_rvol", "k_confirm")
    ]
    if len(despec_singles) < 4:
        despec_singles = [r["arm"] for r in cross1 if r["arm"] != CHAMP_0KBI]

    n_before_and = len(arms)
    _add_and_grid(arms, meta, despec_singles)
    # Score new AND arms
    for name, xs in arms.items():
        if meta.get(name, {}).get("family") != "and_despec":
            continue
        xs2 = xs.reindex(p.index)
        for era in ERAS:
            per_era.append(
                score_arm_on_era(
                    name=name,
                    family="and_despec",
                    xs=xs2,
                    p=p,
                    era=era,
                    masks=era_masks[era.key],
                )
            )

    cross = cross_era_aggregate(per_era)
    cross_by_arm = {r["arm"]: r for r in cross}

    # Global metrics + despec verdict
    arm_rows: list[dict[str, Any]] = []
    for name, xs in arms.items():
        m = meta.get(name, {})
        glob = score_arm_global(
            name=name, family=m.get("family", "unknown"), xs=xs.reindex(p.index), p=p, meta_row=m
        )
        c = cross_by_arm.get(name)
        if c is None:
            continue
        row = {**glob, **{k: v for k, v in c.items() if k not in ("arm", "family")}}
        row["family"] = m.get("family", glob.get("family"))
        row["despec_verdict"] = _arm_despec_verdict(c, glob)
        arm_rows.append(row)

    # Primary rank already in cross; re-sort arm_rows by cross-era score
    arm_rows.sort(
        key=lambda r: (
            float(r.get("cross_era_score") or -1),
            int(r.get("n_non2020_hit") or 0),
            float(r.get("mean_ic") or -1),
        ),
        reverse=True,
    )

    verdict, champ = global_verdict(arm_rows)

    # LOO discipline on top candidates (exclude prior_0kbi from selection pool
    # when ranking despec — but still report LOO including it as baseline)
    despec_pool = [
        r["arm"]
        for r in arm_rows
        if r.get("family") not in ("prior_0kbi",)
        and r.get("despec_verdict") in ("HIT", "PARTIAL", "STILL_SPEC")
    ][:40]
    if len(despec_pool) < 5:
        despec_pool = [r["arm"] for r in arm_rows if r.get("family") != "prior_0kbi"][:40]
    loo = leave_one_era_out(per_era, candidate_arms=despec_pool)
    loo_incl_prior = leave_one_era_out(
        per_era, candidate_arms=[r["arm"] for r in arm_rows[:60]]
    )

    # Explicit comparisons
    row_0kbi = next((r for r in arm_rows if r["arm"] == CHAMP_0KBI), None)
    row_0kbh = next((r for r in arm_rows if r["arm"] == BASE_0KBH), None)

    # Optional light cash-gate CF on best despec arm (not primary HIT path)
    l4_path = ALIGN / "nav_L4_LIVE_P3_WITHIN.csv"
    if not l4_path.exists():
        l4_path = LIVESTACK / "nav_LIVE_P3_WITHIN.csv"
    base_nav = _load_nav(l4_path)
    cf: dict[str, Any] | None = None
    if champ is not None:
        score = arms[champ["arm"]].reindex(p.index)
        uniq = score.dropna().unique()
        if len(uniq) <= 4 and set(np.round(uniq, 6)).issubset({0.0, 1.0}):
            alert = (score >= 0.5).fillna(False)
        else:
            alert = _alert_mask(score, stress_high=True, q=ALERT_Q)
        cf = counterfactual_cash_gate(
            panel.reset_index() if "date" not in panel.columns else panel,
            score,
            base_nav=base_nav,
            alert=alert,
            window_start=date(2020, 2, 20),
            window_end=date(2020, 3, 23),
            label="champ_despec_cf",
        )
        # Cross-era MDD for CF
        from e45_paper_harness import window_stats
        from research_metric_helpers import mdd_delta_pp
        from stagea_screen_helpers import (
            nav_from_returns as _nav_from_returns,
            returns_from_nav as _returns,
        )

        r = _returns(base_nav)
        exp = pd.Series(
            np.where(alert.reindex(r.index).fillna(False), 0.0, 1.0), index=r.index
        )
        chal = _nav_from_returns((exp * r).astype(float), float(base_nav["nav"].iloc[0]))
        era_mdd: dict[str, float | None] = {}
        for era in ERAS:
            b = window_stats(base_nav, era.start, era.end, min_days=5).get("max_drawdown")
            c = window_stats(chal, era.start, era.end, min_days=5).get("max_drawdown")
            if b is None or c is None:
                era_mdd[era.key] = None
            else:
                era_mdd[era.key] = round(float(mdd_delta_pp(float(b), float(c))), 4)
        cf["cross_era_mdd_improve_pp"] = era_mdd
        held_ok = (cf.get("held_cagr_lift_pp") or 0) > 0
        multi_era_mdd = sum(1 for e in NON2020_ERAS if (era_mdd.get(e) or 0) > 0)
        cf["held_pos"] = bool(held_ok)
        cf["non2020_mdd_improve_n"] = int(multi_era_mdd)
        cf["primary_hit_path"] = bool(held_ok and multi_era_mdd >= 1)

    tip = _git_sha()
    day = date.today().isoformat()

    # Counts
    counts = {
        "HIT": sum(1 for r in arm_rows if r["despec_verdict"] == "HIT"),
        "PARTIAL": sum(1 for r in arm_rows if r["despec_verdict"] == "PARTIAL"),
        "STILL_SPEC": sum(1 for r in arm_rows if r["despec_verdict"] == "STILL_SPEC"),
        "NO_EDGE": sum(1 for r in arm_rows if r["despec_verdict"] == "NO_EDGE"),
        "n_arms": len(arm_rows),
        "n_arms_pre_and": n_before_and,
    }

    specialization_reduced = False
    if champ is not None and row_0kbi is not None:
        specialization_reduced = int(champ.get("n_non2020_hit") or 0) > int(
            row_0kbi.get("n_non2020_hit") or 0
        ) or (
            float(champ.get("cross_era_score") or -1)
            > float(row_0kbi.get("cross_era_score") or -1)
            and int(champ.get("n_non2020_hit") or 0) >= 1
        )

    # Write CSVs
    arms_df = pd.DataFrame(arm_rows)
    arms_df.to_csv(OUT / "arms_crisis_feat_despec.csv", index=False)
    pd.DataFrame(per_era).to_csv(OUT / "per_era_scores.csv", index=False)
    pd.DataFrame(cross).to_csv(OUT / "cross_era_rank.csv", index=False)
    pd.DataFrame(loo).to_csv(OUT / "loo_despec.csv", index=False)
    pd.DataFrame(loo_incl_prior).to_csv(OUT / "loo_incl_prior.csv", index=False)
    top = arms_df.head(25)
    top.to_csv(OUT / "top_arms.csv", index=False)

    family_summary = (
        arms_df.groupby("family")
        .agg(
            n=("arm", "count"),
            n_hit=("despec_verdict", lambda s: int((s == "HIT").sum())),
            n_partial=("despec_verdict", lambda s: int((s == "PARTIAL").sum())),
            n_still_spec=("despec_verdict", lambda s: int((s == "STILL_SPEC").sum())),
            best_cross=("cross_era_score", "max"),
            best_non2020=("n_non2020_hit", "max"),
        )
        .reset_index()
    )
    family_summary.to_csv(OUT / "family_summary.csv", index=False)

    # Cross-era table for champ + priors
    def _era_table(row: dict[str, Any] | None) -> dict[str, Any]:
        if row is None:
            return {}
        return {
            "arm": row.get("arm"),
            "despec_verdict": row.get("despec_verdict"),
            "cross_era_score": row.get("cross_era_score"),
            "mean_ic": row.get("mean_ic"),
            "min_ic": row.get("min_ic"),
            "n_non2020_hit": row.get("n_non2020_hit"),
            "eras_hit": row.get("eras_hit"),
            "eras_weak": row.get("eras_weak"),
            "era_ics": row.get("era_ics"),
            "era_verdicts": row.get("era_verdicts"),
            "ic_primary": row.get("ic_spearman_primary"),
            "ic_oos_ex2020": row.get("ic_spearman_oos_ex2020"),
            "year2020_dummy_abs_ic": row.get("year2020_dummy_abs_ic"),
        }

    cross_era_table = {
        "champ_despec": _era_table(champ),
        "prior_0kbi_and": _era_table(row_0kbi),
        "prior_0kbh_rvol20": _era_table(row_0kbh),
        "prior_0kbm_router": PRIOR_0KBM,
    }

    summary = {
        "register": REGISTER,
        "parents": list(PARENTS),
        "mech": MECH,
        "label": LABEL_TAG,
        "verdict": verdict,
        "tip_sha": tip,
        "day": day,
        "counts": counts,
        "champ": champ,
        "cross_era_table": cross_era_table,
        "specialization_reduced": specialization_reduced,
        "loo_despec": loo,
        "cash_gate_cf": cf,
        "floors": {
            "global_ic": GLOBAL_IC_FLOOR,
            "oos_ic_ex2020": OOS_IC_ABS_FLOOR,
            "year_dummy_ceil": YEAR_DUMMY_IC_ABS_CEIL,
            "ep_ic": EP_IC_FLOOR,
            "ep_hit": EP_HIT_FLOOR,
            "ep_recall": EP_RECALL_FLOOR,
            "hit_non2020_min": HIT_NON2020_MIN,
            "fa_outside_2020_ceil": FA_OUTSIDE_2020_CEIL,
        },
        "forbidden": {
            "year_dummy_inputs": False,
            "calendar_month_features": False,
            "episode_label_inputs": False,
            "mar2020_primary_rank": False,
        },
        "constraints": {
            "soft_keep": True,
            "path4_off": True,
            "broker_false": True,
            "soak_freeze_unchanged": True,
            "signal_ne_apply": True,
            "no_tip_soft_live": True,
            "no_soft_fin_tel_accept": True,
        },
        "panel_meta": panel_meta,
        "vs_priors": {
            "0kbi": PRIOR_0KBI,
            "0kbm": PRIOR_0KBM,
            "0kbi_row": _era_table(row_0kbi),
            "champ_vs_0kbi_non2020_delta": (
                None
                if champ is None or row_0kbi is None
                else int(champ.get("n_non2020_hit") or 0)
                - int(row_0kbi.get("n_non2020_hit") or 0)
            ),
            "champ_vs_0kbi_cross_era_delta": (
                None
                if champ is None or row_0kbi is None
                else round(
                    float(champ.get("cross_era_score") or 0)
                    - float(row_0kbi.get("cross_era_score") or 0),
                    4,
                )
            ),
        },
        "utc": _utc(),
    }
    (OUT / "summary.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n", encoding="utf-8"
    )
    (OUT / "screen.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n", encoding="utf-8"
    )

    # ---- Charter / Screen / Decision packs ----
    charter_md = "\n".join(
        [
            f"# {CHARTER_ID}",
            "",
            f"Date: {day}",
            f"Register: **{REGISTER}** · Parents: {', '.join(PARENTS)}",
            f"Mech: **{MECH}** · Label: **{LABEL_TAG}**",
            "",
            "## Question",
            "",
            "Can transforms / normalizations / confirms on **existing** crisis features",
            "(rvol20/63, atr_like, MA gap, dd63, fuse_prem_neg, fuse_neg_flag, cool_defend,",
            "consec_down — no new exotic data) produce detectors or light gates that keep",
            "stress signal quality, fire outside 2020 (2015/2018/2022), and avoid",
            "year-dummy / Mar2020-only routers?",
            "",
            "## Motivation (parents)",
            "",
            "- 0kbi SIGNAL_HIT refine AND `and::rvol63_l4&fuse_prem_neg5`",
            "- 0kbj HIST_OOS_OVERFIT_2020 on that AND",
            "- 0kbl MAJOR_DD_ATLAS_PARTIAL — fuse_prem only partial cross-era",
            "- 0kbk CLIFF_GRIND_SPLIT_HIT — regime tools differ",
            "- 0kbm CRISIS_REGIME_IMPROVE_OVERFIT — router 2020 MDD help, cross-era 0",
            "",
            "## Screen families (lag-1 causal)",
            "",
            "1. Raw baseline (0kbh/0kbi arms)",
            "2. Rolling z-score / percentile rank (252/504d)",
            "3. Vol-of-vol / change in rvol (delta 5/21)",
            "4. Feature vs own long median (252/504d)",
            "5. k-confirm on transformed features",
            "6. Simple AND of two despec'd features (small grid)",
            "7. Optional light cash-gate CF on best despec — report held + cross-era MDD",
            "",
            "## Ranking / floors",
            "",
            "- Primary rank = **cross-era score** (mean/min OOS IC across 2015/2018/2022/2020)",
            "- Leave-one-era-out discipline (select on 3, evaluate held-out)",
            "- HIT: global IC floors + ≥2 non-2020 era ERA_HIT + OOS ex-2020 OK + year-dummy ceil",
            "- Forbidden: year/month/episode-label inputs; Mar2020-only primary rank",
            "",
            "## Constraints",
            "",
            "- Soft KEEP · Path4 OFF · broker false · soak freeze unchanged",
            "- signal≠apply · no tip Soft LIVE · no Soft FIN/TEL ACCEPT",
            "",
        ]
    )
    charter_json = {
        "id": CHARTER_ID,
        "register": REGISTER,
        "parents": list(PARENTS),
        "mech": MECH,
        "label": LABEL_TAG,
        "day": day,
        "base_features": list(BASE_FEATURES),
        "eras": [e.key for e in ERAS],
        "floors": summary["floors"],
        "forbidden": summary["forbidden"],
        "constraints": summary["constraints"],
    }
    write_ops_and_repro_pointer(
        OPS / f"{CHARTER_ID}.md",
        REP / f"{CHARTER_ID}.md",
        charter_md,
        kind="charter",
    )
    (OPS / f"{CHARTER_ID}.json").write_text(
        json.dumps(charter_json, indent=2) + "\n", encoding="utf-8"
    )
    write_repro_pointer(
        OPS / f"{CHARTER_ID}.json", REP / f"{CHARTER_ID}.json", kind="charter json"
    )

    # Screen MD
    top_lines = []
    for _, r in top.head(12).iterrows():
        top_lines.append(
            f"| `{r['arm']}` | {r['family']} | {r['despec_verdict']} | "
            f"{r.get('cross_era_score')} | {r.get('n_non2020_hit')} | "
            f"{r.get('mean_ic')} | {r.get('min_ic')} | "
            f"{r.get('ic_spearman_oos_ex2020')} | {r.get('year2020_dummy_abs_ic')} |"
        )
    loo_lines = [
        f"- held-out **{r['held_out_era']}**: select `{r['selected_arm']}` → "
        f"{r['held_verdict']} IC={r['held_ic']}"
        for r in loo
    ]
    screen_md = "\n".join(
        [
            f"# {SCREEN_ID}",
            "",
            f"Date: {day}",
            f"Register: **{REGISTER}** · **{LABEL_TAG}** · arms={counts['n_arms']} · "
            f"HIT={counts['HIT']} · PARTIAL={counts['PARTIAL']} · "
            f"STILL_SPEC={counts['STILL_SPEC']} · NO_EDGE={counts['NO_EDGE']}",
            f"Verdict: **`{verdict}`**",
            f"Tip SHA: `{tip}`",
            "",
            "## Champion (cross-era rank)",
            "",
            f"- arm: `{champ.get('arm') if champ else None}`",
            f"- family: **{(champ or {}).get('family')}**",
            f"- despec_verdict: **{(champ or {}).get('despec_verdict')}**",
            f"- cross_era_score: **{(champ or {}).get('cross_era_score')}**",
            f"- mean/min IC: **{(champ or {}).get('mean_ic')}** / **{(champ or {}).get('min_ic')}**",
            f"- non2020 ERA_HIT: **{(champ or {}).get('n_non2020_hit')}** "
            f"`{(champ or {}).get('non2020_eras_hit')}`",
            f"- eras_hit: `{(champ or {}).get('eras_hit')}` · weak: `{(champ or {}).get('eras_weak')}`",
            f"- IC primary / OOS ex-2020 / year-dummy|IC|: "
            f"**{(champ or {}).get('ic_spearman_primary')}** / "
            f"**{(champ or {}).get('ic_spearman_oos_ex2020')}** / "
            f"**{(champ or {}).get('year2020_dummy_abs_ic')}**",
            f"- specialization_reduced vs 0kbi AND: **{specialization_reduced}**",
            "",
            "## Cross-era table (champ vs priors)",
            "",
            f"- despec champ: `{json.dumps(cross_era_table.get('champ_despec'), default=str)}`",
            f"- 0kbi AND: `{json.dumps(cross_era_table.get('prior_0kbi_and'), default=str)}`",
            f"- 0kbh rvol20: `{json.dumps(cross_era_table.get('prior_0kbh_rvol20'), default=str)}`",
            f"- 0kbm router (apply OVERFIT prior): `{json.dumps(PRIOR_0KBM)}`",
            "",
            "## Leave-one-era-out (despec pool)",
            "",
            *loo_lines,
            "",
            "## Top arms",
            "",
            "| arm | family | verdict | cross | n_non2020 | meanIC | minIC | OOSex2020 | yd|IC| |",
            "|---|---|---|---|---|---|---|---|---|",
            *top_lines,
            "",
            "## Cash-gate CF (illustrative; not primary HIT path)",
            "",
            f"```json\n{json.dumps(cf, indent=2, default=str)}\n```" if cf else "- n/a",
            "",
            "## Family summary",
            "",
            family_summary.to_string(index=False),
            "",
            "## Constraints kept",
            "",
            "- Soft KEEP · Path4 OFF · broker false · Exact T+1",
            "- **signal ≠ apply** · soak freeze unchanged · no LIVE · no tip Soft promote",
            "- No year/month/episode-label inputs · primary rank = cross-era (not Mar-only)",
            "",
        ]
    )
    write_ops_and_repro_pointer(
        OPS / f"{SCREEN_ID}.md",
        REP / f"{SCREEN_ID}.md",
        screen_md,
        kind="screen",
    )
    (OPS / f"{SCREEN_ID}.json").write_text(
        json.dumps(summary, indent=2, default=str) + "\n", encoding="utf-8"
    )
    write_repro_pointer(
        OPS / f"{SCREEN_ID}.json", REP / f"{SCREEN_ID}.json", kind="screen json"
    )

    # Decision pack
    next_lines = [
        "1. Objective: despec existing crisis features for cross-era fire (2015/2018/2022) without year-dummies",
        f"2. Champion `{(champ or {}).get('arm')}` fam={(champ or {}).get('family')} "
        f"cross={((champ or {}).get('cross_era_score'))} non2020_HIT="
        f"{(champ or {}).get('n_non2020_hit')} meanIC={(champ or {}).get('mean_ic')} "
        f"OOSex2020={(champ or {}).get('ic_spearman_oos_ex2020')} "
        f"verdict={(champ or {}).get('despec_verdict')}",
        f"3. Clears: HIT={counts['HIT']} · PARTIAL={counts['PARTIAL']} · "
        f"STILL_SPEC={counts['STILL_SPEC']} · NO_EDGE={counts['NO_EDGE']} / n={counts['n_arms']}",
        f"4. specialization_reduced vs 0kbi AND: {specialization_reduced} "
        f"(Δnon2020={summary['vs_priors']['champ_vs_0kbi_non2020_delta']}, "
        f"Δcross={summary['vs_priors']['champ_vs_0kbi_cross_era_delta']})",
        "5. vs priors: 0kbi AND Mar HIT / 0kbj OVERFIT_2020 · 0kbl PARTIAL · 0kbm OVERFIT router",
        "6. Disposition: does **not** unlock soak freeze · does **not** recommend LIVE wire · research path only",
        "7. Soft KEEP · Path4 OFF · broker false · no tip Soft promote · no year-oracle",
    ]
    decision_md = "\n".join(
        [
            f"# {DECISION_ID}",
            "",
            f"Date: {day} · Verdict: **`{verdict}`** · "
            f"champion=**`{(champ or {}).get('arm')}`**",
            f"Register: **{REGISTER}** · Parents: {', '.join(PARENTS)} · **{LABEL_TAG}**",
            f"Tip SHA: `{tip}`",
            "",
            "## Result",
            "",
            f"- family: **{(champ or {}).get('family')}** · transform "
            f"**{(champ or {}).get('transform')}**",
            f"- cross-era score: **{(champ or {}).get('cross_era_score')}** "
            f"(meanIC **{(champ or {}).get('mean_ic')}** · minIC **{(champ or {}).get('min_ic')}**)",
            f"- non2020 ERA_HIT n: **{(champ or {}).get('n_non2020_hit')}** "
            f"`{(champ or {}).get('non2020_eras_hit')}`",
            f"- eras_hit: `{(champ or {}).get('eras_hit')}` · weak: `{(champ or {}).get('eras_weak')}`",
            f"- IC primary **{(champ or {}).get('ic_spearman_primary')}** · "
            f"OOS ex-2020 **{(champ or {}).get('ic_spearman_oos_ex2020')}** · "
            f"year-dummy|IC| **{(champ or {}).get('year2020_dummy_abs_ic')}**",
            f"- specialization_reduced: **{specialization_reduced}**",
            f"- clears: HIT **{counts['HIT']}** · PARTIAL **{counts['PARTIAL']}** · "
            f"STILL_SPEC **{counts['STILL_SPEC']}** · NO_EDGE **{counts['NO_EDGE']}**",
            "",
            "## vs 0kbi AND / 0kbm OVERFIT router",
            "",
            f"- vs 0kbi `{CHAMP_0KBI}`: non2020_HIT "
            f"**{(row_0kbi or {}).get('n_non2020_hit')}** → champ "
            f"**{(champ or {}).get('n_non2020_hit')}** "
            f"(Δ={summary['vs_priors']['champ_vs_0kbi_non2020_delta']}); "
            f"cross-era Δ={summary['vs_priors']['champ_vs_0kbi_cross_era_delta']}",
            f"- vs 0kbm `{PRIOR_0KBM['champ']}` OVERFIT: held **{PRIOR_0KBM['held']}** · "
            f"y2020 MDD↑ **{PRIOR_0KBM['y2020_mdd_imp']}** · cross-era improve_n "
            f"**{PRIOR_0KBM['cross_era_improve_n']}** — despec is detection-side "
            f"response (feature transforms), not another 2020 router",
            "",
            "## Disposition",
            "",
            f"- **{LABEL_TAG}** — research path only; **signal ≠ apply**",
            "- HIT only if global IC floors + ≥2 non-2020 era fires + OOS ex-2020 + year-dummy ceil",
            "- STILL_SPEC if fires remain 2020-dominated",
            "- Does **not** unlock soak freeze · does **not** recommend LIVE wire",
            "- Soft KEEP · Path4 OFF · broker false · no tip Soft promote · no year-oracle",
            "",
            "## Next",
            "",
            *next_lines,
            "",
            f"Label: `{DECISION_ID}_{day}__{verdict}__{LABEL_TAG}__NO_LIVE`",
            "",
            f"Screen: `{SCREEN_ID}.md` · Charter: `{CHARTER_ID}.md`",
            f"Repro: `PYTHONPATH=scripts python3 scripts/tipsoft_ip3_crisis_feat_despec_stagea.py`",
            "",
        ]
    )
    decision_json = {
        "id": DECISION_ID,
        "register": REGISTER,
        "parents": list(PARENTS),
        "verdict": verdict,
        "champ": champ,
        "cross_era_table": cross_era_table,
        "specialization_reduced": specialization_reduced,
        "counts": counts,
        "vs_priors": summary["vs_priors"],
        "cash_gate_cf": cf,
        "loo_despec": loo,
        "tip_sha": tip,
        "day": day,
        "constraints": summary["constraints"],
    }
    write_ops_and_repro_pointer(
        OPS / f"{DECISION_ID}.md",
        REP / f"{DECISION_ID}.md",
        decision_md,
        kind="decision pack",
    )
    (OPS / f"{DECISION_ID}.json").write_text(
        json.dumps(decision_json, indent=2, default=str) + "\n", encoding="utf-8"
    )
    write_repro_pointer(
        OPS / f"{DECISION_ID}.json",
        REP / f"{DECISION_ID}.json",
        kind="decision pack json",
    )

    _patch_register(verdict, champ, day, tip)
    _patch_ops_status(verdict, champ, day, tip)

    # REPRO readme
    (REPRO / "README.md").write_text(
        "\n".join(
            [
                "# tipsoft-ip3-crisis-feat-despec-stagea",
                "",
                f"Register **{REGISTER}** · Stage A crisis feature despecialization.",
                "",
                "## Repro",
                "",
                "```bash",
                "PYTHONPATH=scripts python3 scripts/tipsoft_ip3_crisis_feat_despec_stagea.py",
                "PYTHONPATH=scripts python3 -m unittest tests.test_tipsoft_ip3_crisis_feat_despec_stagea -v",
                "```",
                "",
                "SOAK-SAFE · signal≠apply · Soft KEEP · Path4 OFF · no live.",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print(json.dumps({"verdict": verdict, "champ": (champ or {}).get("arm"), "tip": tip[:12]}, indent=2))
    return summary


if __name__ == "__main__":
    run()
