#!/usr/bin/env python3
"""2020 crisis signal **refine** Stage A (0kbi) — try WEAK→HIT (detection only).

SOAK-SAFE · PARALLEL paper research — **signal ≠ apply**.

Parent 0kbh landed ``IP3_Y2020_CRISIS_SIGNAL_WEAK`` (top ``rvol20_l4`` IC≈0.12 /
hit(Mar)≈0.52). User follow-up: 訊號有弱邊，可以研究出強邊嗎？ — screen refine
families (AND/OR combos · k-confirm · adaptive thresholds · dual-horizon ·
enter/exit episodes) that *try* to clear SIGNAL_HIT floors.

Still detection-only:
- Soft KEEP · Path4 OFF · broker false · Exact T+1 lag-1
- no LIVE apply · no tip Soft promote · no year-oracle · no soak unlock

Verdict taxonomy (REFINE Stage A):
- ``IP3_Y2020_CRISIS_SIGNAL_REFINE_HIT`` — any arm clears SIGNAL_HIT floors
- ``…_WEAK`` / ``…_NO_EDGE`` / ``…_OVERFIT`` (year-dummy or Mar-only)

Floors match 0kbh for comparability.

Repro: ``PYTHONPATH=scripts python3 scripts/tipsoft_ip3_y2020_crisis_signal_refine_stagea.py``
"""
from __future__ import annotations

import itertools
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ops_repro_ssot import write_ops_and_repro_pointer, write_repro_pointer
from stagea_screen_helpers import utc_now_z as _utc
from tipsoft_ip3_y2020_crisis_signal_stagea import (
    ALERT_Q,
    FA_OUTSIDE_2020_CEIL,
    HIT_FLOOR,
    IC_ABS_FLOOR,
    LEAD_DAYS_FLOOR,
    MAR2020_END,
    MAR2020_START,
    MAR_EVAL_END,
    MAR_EVAL_START,
    OOS_IC_ABS_FLOOR,
    RECALL_MAR_FLOOR,
    YEAR_DUMMY_IC_ABS_CEIL,
    _alert_mask,
    _binary_prf,
    _champ_key,
    _detector_verdict,
    _median_lead_days,
    _pearson,
    _spearman,
    build_panel,
)

ROOT = Path(__file__).resolve().parents[1]
REPRO = ROOT / "repro" / "tipsoft-ip3-y2020-crisis-signal-refine-stagea"
OUT = REPRO / "outputs"
REP = REPRO / "reports"
OPS = ROOT / "research" / "ops"

CHARTER_ID = "TIPSOFT_IP3_Y2020_CRISIS_SIGNAL_REFINE_STAGEA_CHARTER"
SCREEN_ID = "TIPSOFT_IP3_Y2020_CRISIS_SIGNAL_REFINE_STAGEA_SCREEN"
DECISION_ID = "TIPSOFT_IP3_Y2020_CRISIS_SIGNAL_REFINE_STAGEA_DECISION_PACK"
REGISTER = "0kbi"
PARENTS = ("0kbh", "0kbg", "0kbf")
MECH = "TIPSOFT_IP3_Y2020_CRISIS_SIGNAL_REFINE"
LABEL_TAG = "SIGNAL_REFINE_PARALLEL"

# Top singles from 0kbh screen (stress-oriented candidates for refine)
TOP_SINGLES = (
    "rvol20_l4",
    "atr_like_20",
    "fuse_neg_flag",
    "cool_defend_l1",
    "rvol63_l4",
    "neg_gap_ma200",
    "dd63_l4",
    "fuse_prem_neg5",
    "proxy_mdd63_soft",
    "rvol20_mkt",
    "consec_down_mkt",
    "neg_gap_ma120",
)

# Adaptive threshold source columns (vol / ATR / dd family)
ADAPTIVE_SOURCES = (
    "rvol20_l4",
    "rvol63_l4",
    "atr_like_20",
    "dd63_l4",
    "dd63_mkt",
    "proxy_mdd63_soft",
)

ROLL_WIN = 252
ADAPT_QS = (0.80, 0.90, 0.95)
CONFIRM_KS = (2, 3)
EPISODE_HOLDS = (3, 5, 10)
PARENT_0KBH_CHAMP = {
    "detector": "rvol20_l4",
    "ic_spearman_primary": 0.1249,
    "hit_rate_mar": 0.5172,
    "recall_mar": 0.3182,
    "median_lead_days": 32.0,
    "fa_rate_outside_2020": 0.0865,
    "ic_spearman_oos_ex2020": 0.1193,
    "verdict": "SIGNAL_WEAK",
}


def _rank_pct(s: pd.Series) -> pd.Series:
    return s.rank(method="average", pct=True)


def _orient_stress(x: pd.Series, y_primary: pd.Series) -> tuple[pd.Series, bool]:
    sp = _spearman(x, y_primary)
    stress_high = True if sp is None else (float(sp) >= 0)
    return (x if stress_high else -x), stress_high


def _rolling_pct_flag(x: pd.Series, *, q: float, win: int = ROLL_WIN) -> pd.Series:
    """Causal flag: ``x[t]`` vs trailing quantile of ``x[t-win : t-1]``.

    ``x`` is expected to already be lag-1 (parent feature convention); do **not**
    shift ``x`` again (that would become lag-2).
    """
    thr = x.shift(1).rolling(int(win), min_periods=max(40, int(win) // 5)).quantile(float(q))
    return (x >= thr).astype(float)


def _k_confirm(flag: pd.Series, k: int) -> pd.Series:
    """Require k consecutive True flags ending today (flag already lag-1 causal)."""
    f = flag.fillna(0.0).astype(float)
    out = f.copy()
    for i in range(1, int(k)):
        out = out * f.shift(i).fillna(0.0)
    return (out >= 0.999).astype(float)


def _episode_hold(enter: pd.Series, hold: int) -> pd.Series:
    """Enter on spike; hold at least ``hold`` calendar business bars (causal)."""
    e = enter.fillna(False).astype(bool).to_numpy()
    out = np.zeros(len(e), dtype=float)
    remaining = 0
    for i in range(len(e)):
        if e[i]:
            remaining = max(remaining, int(hold))
        if remaining > 0:
            out[i] = 1.0
            remaining -= 1
    return pd.Series(out, index=enter.index)


def _is_overfit(row: dict[str, Any]) -> bool:
    yd = row.get("year2020_dummy_abs_ic")
    oos = row.get("ic_spearman_oos_ex2020")
    ic = row.get("ic_spearman_primary")
    hit = row.get("hit_rate_mar")
    year_dummy = yd is not None and float(yd) >= YEAR_DUMMY_IC_ABS_CEIL
    mar_only = (
        hit is not None
        and float(hit) >= HIT_FLOOR
        and ic is not None
        and abs(float(ic)) >= 0.04
        and (oos is None or abs(float(oos)) < OOS_IC_ABS_FLOOR)
    )
    return bool(year_dummy or mar_only)


def _arm_verdict(row: dict[str, Any]) -> str:
    base = _detector_verdict(row)
    if _is_overfit(row):
        # Distinct from WEAK: looks good in Mar / year-2020 but fails OOS / year-dummy
        if base != "SIGNAL_HIT":
            return "SIGNAL_OVERFIT"
    return base


def _score_arm(
    name: str,
    family: str,
    x_stress: pd.Series,
    *,
    p: pd.DataFrame,
    y_primary: pd.Series,
    y_mar: pd.Series,
    y_stress: pd.Series,
    y_year: pd.Series,
    local: np.ndarray,
    trough: pd.Timestamp,
    alert_override: pd.Series | None = None,
    primary_label: str = "fwd_mdd_10",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ex2020 = y_year < 0.5
    sp_s = _spearman(x_stress, y_primary)
    pe_s = _pearson(x_stress, y_primary)
    sp_mar = _spearman(x_stress, y_mar)
    sp_stress = _spearman(x_stress, y_stress)
    sp_oos = _spearman(x_stress[ex2020], y_primary[ex2020])
    yd = _spearman(x_stress, y_year)
    yd_abs = None if yd is None else abs(float(yd))

    if alert_override is not None:
        alert = alert_override.reindex(p.index).fillna(False).astype(bool)
    else:
        # Binary/sparse arms: if mostly 0/1, use >0.5; else top-quantile
        uniq = x_stress.dropna().unique()
        if len(uniq) <= 4 and set(np.round(uniq, 6)).issubset({0.0, 1.0}):
            alert = (x_stress >= 0.5).fillna(False)
        else:
            alert = _alert_mask(x_stress, stress_high=True, q=ALERT_Q)

    prf_mar = _binary_prf(y_mar[local].astype(bool), alert[local])
    prf_stress = _binary_prf(y_stress.astype(bool), alert)
    alert_out = alert & (y_year < 0.5)
    n_alert_out = int(alert_out.sum())
    n_out = int((y_year < 0.5).sum())
    fa = (n_alert_out / n_out) if n_out else None
    out_prf = _binary_prf(y_stress[ex2020].astype(bool), alert[ex2020])
    lead = _median_lead_days(alert, window_start=MAR2020_START, trough=trough)

    # Dual-horizon diagnostics (always recorded)
    sp5 = _spearman(x_stress, p["fwd_mdd_5"]) if "fwd_mdd_5" in p.columns else None
    sp_crash = (
        _spearman(x_stress, p["fwd_ret_crash_10"]) if "fwd_ret_crash_10" in p.columns else None
    )

    row: dict[str, Any] = {
        "detector": name,
        "family": family,
        "stress_high_orientation": True,
        "ic_spearman_primary": None if sp_s is None else round(float(sp_s), 4),
        "ic_pearson_primary": None if pe_s is None else round(float(pe_s), 4),
        "ic_spearman_mar": None if sp_mar is None else round(float(sp_mar), 4),
        "ic_spearman_ddcross8": None if sp_stress is None else round(float(sp_stress), 4),
        "ic_spearman_oos_ex2020": None if sp_oos is None else round(float(sp_oos), 4),
        "ic_spearman_fwd_mdd_5": None if sp5 is None else round(float(sp5), 4),
        "ic_spearman_fwd_ret_crash_10": None if sp_crash is None else round(float(sp_crash), 4),
        "year2020_dummy_abs_ic": None if yd_abs is None else round(float(yd_abs), 4),
        "hit_rate_mar": prf_mar["hit_rate"],
        "precision_mar": prf_mar["precision"],
        "recall_mar": prf_mar["recall"],
        "f1_mar": prf_mar["f1"],
        "hit_rate_ddcross8": prf_stress["hit_rate"],
        "f1_ddcross8": prf_stress["f1"],
        "fa_rate_outside_2020": None if fa is None else round(float(fa), 4),
        "precision_stress_ex2020": out_prf["precision"],
        "median_lead_days": None if lead is None else round(float(lead), 2),
        "primary_label": primary_label,
        "alert_q": ALERT_Q,
        "n_alert": int(alert.sum()),
    }
    if extra:
        row.update(extra)
    row["overfit_flag"] = _is_overfit(row)
    row["verdict"] = _arm_verdict(row)
    return row


def build_refine_arms(panel: pd.DataFrame) -> tuple[dict[str, pd.Series], dict[str, dict[str, Any]]]:
    """Return continuous/binary refine scores + metadata (family, alert override)."""
    p = panel.copy()
    p["date"] = pd.to_datetime(p["date"])
    p = p.set_index("date").sort_index()
    y_primary = p["fwd_mdd_10"]

    # Orient base singles
    oriented: dict[str, pd.Series] = {}
    for col in TOP_SINGLES:
        if col not in p.columns:
            continue
        xs, _ = _orient_stress(p[col], y_primary)
        oriented[col] = xs

    arms: dict[str, pd.Series] = {}
    meta: dict[str, dict[str, Any]] = {}

    # --- baseline singles (comparability) ---
    for col, xs in oriented.items():
        name = f"base::{col}"
        arms[name] = xs
        meta[name] = {"family": "baseline", "alert_override": None, "primary_label": "fwd_mdd_10"}

    # Rank-pct for combos
    ranks = {c: _rank_pct(xs) for c, xs in oriented.items()}
    combo_pool = [c for c in TOP_SINGLES if c in ranks][:8]

    # --- AND / OR pairwise + select triples ---
    for a, b in itertools.combinations(combo_pool, 2):
        and_name = f"and::{a}&{b}"
        or_name = f"or::{a}|{b}"
        arms[and_name] = pd.concat([ranks[a], ranks[b]], axis=1).min(axis=1)
        arms[or_name] = pd.concat([ranks[a], ranks[b]], axis=1).max(axis=1)
        meta[and_name] = {"family": "and_combo", "alert_override": None, "primary_label": "fwd_mdd_10"}
        meta[or_name] = {"family": "or_combo", "alert_override": None, "primary_label": "fwd_mdd_10"}

        # Binary alert AND/OR at fixed q
        aa = _alert_mask(oriented[a], stress_high=True, q=ALERT_Q)
        bb = _alert_mask(oriented[b], stress_high=True, q=ALERT_Q)
        and_flag = (aa & bb).astype(float)
        or_flag = (aa | bb).astype(float)
        af = f"andflag::{a}&{b}"
        of = f"orflag::{a}|{b}"
        arms[af] = and_flag
        arms[of] = or_flag
        meta[af] = {"family": "and_combo", "alert_override": and_flag.astype(bool), "primary_label": "fwd_mdd_10"}
        meta[of] = {"family": "or_combo", "alert_override": or_flag.astype(bool), "primary_label": "fwd_mdd_10"}

    # Triple AND on strongest 0kbh trio
    trio = [c for c in ("rvol20_l4", "atr_like_20", "fuse_neg_flag") if c in ranks]
    if len(trio) == 3:
        tname = f"and::{'&'.join(trio)}"
        arms[tname] = pd.concat([ranks[c] for c in trio], axis=1).min(axis=1)
        meta[tname] = {"family": "and_combo", "alert_override": None, "primary_label": "fwd_mdd_10"}
        flags = [_alert_mask(oriented[c], stress_high=True, q=ALERT_Q) for c in trio]
        tf = flags[0] & flags[1] & flags[2]
        tf_name = f"andflag::{'&'.join(trio)}"
        arms[tf_name] = tf.astype(float)
        meta[tf_name] = {
            "family": "and_combo",
            "alert_override": tf,
            "primary_label": "fwd_mdd_10",
        }

    # --- k-confirm ---
    for col, xs in list(oriented.items())[:8]:
        base_alert = _alert_mask(xs, stress_high=True, q=ALERT_Q)
        for k in CONFIRM_KS:
            name = f"kconfirm{k}::{col}"
            conf = _k_confirm(base_alert.astype(float), k)
            arms[name] = conf
            meta[name] = {
                "family": "k_confirm",
                "alert_override": conf.astype(bool),
                "primary_label": "fwd_mdd_10",
                "k": k,
            }

    # --- adaptive rolling percentile thresholds ---
    for col in ADAPTIVE_SOURCES:
        if col not in p.columns:
            continue
        xs, _ = _orient_stress(p[col], y_primary)
        for q in ADAPT_QS:
            name = f"adapt_p{int(q*100)}::{col}"
            flag = _rolling_pct_flag(xs, q=q, win=ROLL_WIN)
            # Continuous score: excess over causal rolling threshold (no double lag)
            thr = xs.shift(1).rolling(ROLL_WIN, min_periods=max(40, ROLL_WIN // 5)).quantile(q)
            score = (xs - thr).fillna(0.0)
            arms[name] = score
            meta[name] = {
                "family": "adaptive_threshold",
                "alert_override": flag.astype(bool),
                "primary_label": "fwd_mdd_10",
                "adapt_q": q,
            }

    # --- dual-horizon score arms ---
    # Label blend: 0.5*fwd_mdd_5 + 0.5*fwd_mdd_10 (+ optional crash)
    dual_label = 0.5 * p["fwd_mdd_5"] + 0.5 * p["fwd_mdd_10"]
    dual_crash = 0.4 * p["fwd_mdd_5"] + 0.4 * p["fwd_mdd_10"] + 0.2 * p["fwd_ret_crash_10"]
    for col, xs in list(oriented.items())[:8]:
        # Feature stays the single; we score against dual primary label
        name = f"dual_mdd::{col}"
        arms[name] = xs
        meta[name] = {
            "family": "dual_horizon",
            "alert_override": None,
            "primary_label": "dual_fwd_mdd_5_10",
            "y_primary_override": dual_label,
        }
        name2 = f"dual_crash::{col}"
        arms[name2] = xs
        meta[name2] = {
            "family": "dual_horizon",
            "alert_override": None,
            "primary_label": "dual_fwd_mdd_crash",
            "y_primary_override": dual_crash,
        }

    # --- enter/exit episode rules ---
    for col, xs in list(oriented.items())[:8]:
        enter = _alert_mask(xs, stress_high=True, q=ALERT_Q)
        for hold in EPISODE_HOLDS:
            name = f"episode_h{hold}::{col}"
            ep = _episode_hold(enter, hold)
            arms[name] = ep
            meta[name] = {
                "family": "episode",
                "alert_override": ep.astype(bool),
                "primary_label": "fwd_mdd_10",
                "hold_days": hold,
            }

    return arms, meta


def score_refine_arms(panel: pd.DataFrame) -> list[dict[str, Any]]:
    p = panel.copy()
    p["date"] = pd.to_datetime(p["date"])
    p = p.set_index("date").sort_index()
    trough = pd.Timestamp(MAR2020_END)
    local = (p.index.date >= MAR_EVAL_START) & (p.index.date <= MAR_EVAL_END)
    y_mar = p["in_mar2020"]
    y_stress = p["l4_dd_cross_8"]
    y_year = p["year2020_dummy"]
    default_primary = p["fwd_mdd_10"]

    arms, meta = build_refine_arms(panel)
    rows: list[dict[str, Any]] = []
    for name, series in arms.items():
        m = meta[name]
        y_primary = m.get("y_primary_override", default_primary)
        xs = series.reindex(p.index)
        # Ensure stress-high orientation vs chosen primary
        xs, _ = _orient_stress(xs, y_primary)
        alert_ov = m.get("alert_override")
        if alert_ov is not None:
            alert_ov = alert_ov.reindex(p.index)
        row = _score_arm(
            name,
            m["family"],
            xs,
            p=p,
            y_primary=y_primary,
            y_mar=y_mar,
            y_stress=y_stress,
            y_year=y_year,
            local=local,
            trough=trough,
            alert_override=alert_ov,
            primary_label=m.get("primary_label", "fwd_mdd_10"),
            extra={k: v for k, v in m.items() if k not in ("alert_override", "y_primary_override", "family", "primary_label")},
        )
        rows.append(row)

    rows.sort(
        key=lambda r: (
            r["verdict"] == "SIGNAL_HIT",
            r["verdict"] == "SIGNAL_WEAK",
            r["verdict"] != "SIGNAL_OVERFIT",
            *_champ_key(r),
        ),
        reverse=True,
    )
    return rows


def _global_verdict(rows: list[dict[str, Any]]) -> tuple[str, dict[str, Any] | None]:
    if not rows:
        return "IP3_Y2020_CRISIS_SIGNAL_REFINE_NO_EDGE", None
    hits = [r for r in rows if r.get("verdict") == "SIGNAL_HIT"]
    weaks = [r for r in rows if r.get("verdict") == "SIGNAL_WEAK"]
    overfits = [r for r in rows if r.get("verdict") == "SIGNAL_OVERFIT"]
    if hits:
        champ = sorted(hits, key=_champ_key, reverse=True)[0]
        return "IP3_Y2020_CRISIS_SIGNAL_REFINE_HIT", champ
    if weaks:
        champ = sorted(weaks, key=_champ_key, reverse=True)[0]
        return "IP3_Y2020_CRISIS_SIGNAL_REFINE_WEAK", champ
    if overfits:
        champ = sorted(overfits, key=_champ_key, reverse=True)[0]
        return "IP3_Y2020_CRISIS_SIGNAL_REFINE_OVERFIT", champ
    champ = sorted(rows, key=_champ_key, reverse=True)[0]
    return "IP3_Y2020_CRISIS_SIGNAL_REFINE_NO_EDGE", champ


def _disposition(verdict: str, n_hit: int) -> list[str]:
    lines = [
        "**SIGNAL_REFINE / PARALLEL** — detection only; **signal ≠ apply**",
        "Does **not** unlock soak freeze · does **not** recommend LIVE wire",
        "No tip Soft promote · no year-oracle · Soft KEEP · Path4 OFF · broker false",
        "Floors reused from 0kbh for comparability (no tighten)",
    ]
    if n_hit == 0 and "HIT" not in verdict:
        lines.append(
            "Honest disposition: strong edge **not found** under current feature set; "
            "next needs new data (breadth, VIX.tw, order-flow) or accept WEAK as ceiling for now"
        )
    elif "HIT" in verdict:
        lines.append(
            "Refine cleared SIGNAL_HIT floors — still **no LIVE apply**; next would be "
            "observe-only ballot if human wants (SOAK freeze unchanged)"
        )
    return lines


def _patch_register(verdict: str, champ: dict[str, Any] | None, day: str) -> None:
    reg = OPS / "HUMAN_DECISION_REGISTER.md"
    rt = reg.read_text(encoding="utf-8")
    c = champ or {}
    new_row = (
        f"| 0kbi | 2020 crisis signal **refine** (WEAK→HIT try, no apply) | "
        f"**STAGE A `{verdict}`** ({day}) | "
        f"Parents 0kbh/0kbg/0kbf · **SIGNAL_REFINE/PARALLEL** · Exact T+1 lag-1 · "
        f"top `{c.get('detector')}` family `{c.get('family')}` IC **{c.get('ic_spearman_primary')}** · "
        f"hit(Mar) **{c.get('hit_rate_mar')}** · lead **{c.get('median_lead_days')}**d · "
        f"vs 0kbh champ `rvol20_l4` · **signal≠apply** · soak freeze unchanged · Soft KEEP · "
        f"Path4 OFF · broker false · no live · `{DECISION_ID}.md` |"
    )
    lines = rt.splitlines()
    out: list[str] = []
    replaced = False
    for line in lines:
        if line.startswith("| 0kbi |"):
            out.append(new_row)
            replaced = True
        else:
            out.append(line)
    if not replaced:
        insert_at = None
        for i, line in enumerate(out):
            if line.startswith("| 0kbh |"):
                insert_at = i + 1
                break
        if insert_at is None:
            for i, line in enumerate(out):
                if line.startswith("| 0kbf |") or line.startswith("| 0kbg |"):
                    insert_at = i + 1
                    break
        if insert_at is not None:
            out.insert(insert_at, new_row)
        else:
            out.append(new_row)
    reg.write_text("\n".join(out) + "\n", encoding="utf-8")


def _patch_ops_status(verdict: str, champ: dict[str, Any] | None, day: str) -> None:
    ops = OPS / "OPS_STATUS.md"
    ot = ops.read_text(encoding="utf-8")
    c = champ or {}
    line = (
        f"**Y2020 crisis signal refine (SIGNAL_REFINE/PARALLEL {day}):** Stage A **`{verdict}`** · "
        f"register **0kbi** · top `{c.get('detector')}` family `{c.get('family')}` IC "
        f"**{c.get('ic_spearman_primary')}** · hit(Mar) **{c.get('hit_rate_mar')}** · "
        f"lead **{c.get('median_lead_days')}**d · vs 0kbh `rvol20_l4` WEAK · "
        f"**signal≠apply** · soak freeze unchanged · Soft KEEP · Path4 OFF · no live · "
        f"`{DECISION_ID}.md`  "
    )
    ot2, n = re.subn(
        r"\*\*Y2020 crisis signal refine \(SIGNAL_REFINE/PARALLEL [^)]+\):\*\*.*",
        line,
        ot,
        count=1,
    )
    if n:
        ops.write_text(ot2, encoding="utf-8")
        return
    needle = "Y2020 crisis signal detect (SIGNAL/PARALLEL"
    idx = ot.find(needle)
    if idx < 0:
        needle = "DD_SWITCH soak gate"
        idx = ot.find(needle)
    if idx >= 0:
        # insert after the matched status line
        end = ot.find("\n", idx) + 1
        ops.write_text(ot[:end] + line + "\n" + ot[end:], encoding="utf-8")
    else:
        ops.write_text(line + "\n" + ot, encoding="utf-8")


def main() -> int:
    for d in (OUT, REP, OPS):
        d.mkdir(parents=True, exist_ok=True)
    generated = _utc()
    day = generated[:10]

    panel, meta = build_panel()
    panel.to_csv(OUT / "panel_crisis_signal_refine.csv", index=False)
    rows = score_refine_arms(panel)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "refine_arms_scored.csv", index=False)

    verdict, champ = _global_verdict(rows)
    n_hit = int(sum(1 for r in rows if r["verdict"] == "SIGNAL_HIT"))
    n_weak = int(sum(1 for r in rows if r["verdict"] == "SIGNAL_WEAK"))
    n_over = int(sum(1 for r in rows if r["verdict"] == "SIGNAL_OVERFIT"))
    n_no = int(sum(1 for r in rows if r["verdict"] == "SIGNAL_NO_EDGE"))

    by_fam: dict[str, dict[str, int]] = {}
    for r in rows:
        fam = str(r.get("family") or "?")
        by_fam.setdefault(fam, {"n": 0, "hit": 0, "weak": 0, "overfit": 0, "no_edge": 0})
        by_fam[fam]["n"] += 1
        key = {
            "SIGNAL_HIT": "hit",
            "SIGNAL_WEAK": "weak",
            "SIGNAL_OVERFIT": "overfit",
            "SIGNAL_NO_EDGE": "no_edge",
        }.get(str(r["verdict"]), "no_edge")
        by_fam[fam][key] += 1

    # Best per family
    best_by_fam: dict[str, dict[str, Any]] = {}
    for fam in sorted(by_fam):
        fam_rows = [r for r in rows if r.get("family") == fam]
        if fam_rows:
            best_by_fam[fam] = sorted(fam_rows, key=_champ_key, reverse=True)[0]

    top = rows[:20]
    floors = {
        "ic_abs_floor": IC_ABS_FLOOR,
        "hit_floor": HIT_FLOOR,
        "recall_mar_floor": RECALL_MAR_FLOOR,
        "lead_days_floor": LEAD_DAYS_FLOOR,
        "fa_outside_2020_ceil": FA_OUTSIDE_2020_CEIL,
        "year_dummy_ic_abs_ceil": YEAR_DUMMY_IC_ABS_CEIL,
        "oos_ic_abs_floor": OOS_IC_ABS_FLOOR,
        "alert_q": ALERT_Q,
        "primary_label_default": "fwd_mdd_10",
        "mar_eval_window": [str(MAR_EVAL_START), str(MAR_EVAL_END)],
        "floors_source": "0kbh (reused, no tighten)",
    }

    compare = {
        "0kbh": {
            "register": "0kbh",
            "verdict": "IP3_Y2020_CRISIS_SIGNAL_WEAK",
            "champion": PARENT_0KBH_CHAMP,
            "note": (
                "0kbh single-feature screen: top rvol20_l4 WEAK (IC 0.1249 / hit 0.5172). "
                "This pack screens refine combinations trying to clear SIGNAL_HIT floors."
            ),
        },
        "0kbg": {
            "register": "0kbg",
            "verdict": "IP3_Y2020_CRISIS_SANDBOX_MDD_ONLY",
            "note": "Size overlays cut Mar MDD but held≪0 — refine stays signal-only.",
        },
        "0kbf": {
            "register": "0kbf",
            "verdict": "SOAK_OPEN",
            "note": "Soak freeze unchanged — refine Stage A does not unlock SOAK_PASS.",
        },
    }

    vs_parent = None
    if champ is not None:
        vs_parent = {
            "refine_detector": champ.get("detector"),
            "refine_family": champ.get("family"),
            "refine_ic": champ.get("ic_spearman_primary"),
            "refine_hit_mar": champ.get("hit_rate_mar"),
            "refine_recall_mar": champ.get("recall_mar"),
            "refine_lead": champ.get("median_lead_days"),
            "refine_fa": champ.get("fa_rate_outside_2020"),
            "refine_oos_ic": champ.get("ic_spearman_oos_ex2020"),
            "refine_verdict": champ.get("verdict"),
            "parent_0kbh_detector": PARENT_0KBH_CHAMP["detector"],
            "parent_0kbh_ic": PARENT_0KBH_CHAMP["ic_spearman_primary"],
            "parent_0kbh_hit_mar": PARENT_0KBH_CHAMP["hit_rate_mar"],
            "parent_0kbh_recall_mar": PARENT_0KBH_CHAMP["recall_mar"],
            "parent_0kbh_lead": PARENT_0KBH_CHAMP["median_lead_days"],
            "ic_delta_vs_0kbh": round(
                float(champ.get("ic_spearman_primary") or 0)
                - float(PARENT_0KBH_CHAMP["ic_spearman_primary"]),
                4,
            ),
            "hit_delta_vs_0kbh": round(
                float(champ.get("hit_rate_mar") or 0) - float(PARENT_0KBH_CHAMP["hit_rate_mar"]),
                4,
            ),
            "signal_hit_achieved": n_hit > 0,
        }

    disp = _disposition(verdict, n_hit)
    optimize = [
        "Objective: refine 0kbh WEAK singles → try SIGNAL_HIT via combo/confirm/adapt/dual/episode",
        (
            f"Top `{champ['detector']}` family={champ.get('family')} "
            f"IC={champ.get('ic_spearman_primary')} hit(Mar)={champ.get('hit_rate_mar')} "
            f"lead={champ.get('median_lead_days')}d FA≠2020={champ.get('fa_rate_outside_2020')} "
            f"verdict={champ.get('verdict')}"
            if champ
            else "No arm scored"
        ),
        (
            f"vs 0kbh champ `rvol20_l4`: IC Δ={vs_parent['ic_delta_vs_0kbh'] if vs_parent else None} · "
            f"hit Δ={vs_parent['hit_delta_vs_0kbh'] if vs_parent else None} · "
            f"SIGNAL_HIT achieved={n_hit > 0}"
        ),
        f"Clears: HIT={n_hit} · WEAK={n_weak} · OVERFIT={n_over} · NO_EDGE={n_no} / n={len(rows)}",
        "Families: baseline · and/or_combo · k_confirm · adaptive_threshold · dual_horizon · episode",
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
        "n_arms": len(rows),
        "n_signal_hit": n_hit,
        "n_signal_weak": n_weak,
        "n_signal_overfit": n_over,
        "n_signal_no_edge": n_no,
        "floors": floors,
        "meta": meta,
        "compare_parents": compare,
        "vs_0kbh_champ": vs_parent,
        "champion": champ,
        "best_by_family": best_by_fam,
        "family_counts": by_fam,
        "top_arms": top,
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
        json.dumps({"meta": meta, "floors": floors, "family_counts": by_fam}, indent=2, default=str)
        + "\n",
        encoding="utf-8",
    )

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
            "訊號有弱邊，可以研究出強邊嗎？ — Can refine families (combos / confirms / "
            "adaptive thresholds / dual-horizon / episodes) upgrade 0kbh SIGNAL_WEAK "
            "singles to SIGNAL_HIT on Mar2020 / 2020 crisis detection — without apply?",
            "",
            "## Refine families",
            "",
            "1. AND/OR combos of top 0kbh singles (rvol20, atr_like_20, fuse_neg, cool_defend, …)",
            "2. k-confirm (2–3 consecutive lag-1 alert flags)",
            "3. Adaptive thresholds (rolling p80/p90/p95 of vol/ATR/dd)",
            "4. Dual-horizon score (IC vs fwd_mdd_5 ∧ fwd_mdd_10 / crash)",
            "5. Enter/exit episode rules (enter on spike, hold min days)",
            "",
            "## Floors (match 0kbh)",
            "",
            f"- |IC|≥{IC_ABS_FLOOR} · hit≥{HIT_FLOOR} · recall≥{RECALL_MAR_FLOOR} · "
            f"lead≥{LEAD_DAYS_FLOOR}d · FA≤{FA_OUTSIDE_2020_CEIL} · "
            f"OOS|IC|≥{OOS_IC_ABS_FLOOR} · year-dummy|IC|<{YEAR_DUMMY_IC_ABS_CEIL}",
            "",
            "## Hard constraints",
            "",
            "- Soft KEEP · Path4 OFF · broker false · Exact T+1 lag-1",
            "- **signal ≠ apply** · no tip Soft promote · no year-oracle",
            "- does **not** unlock soak freeze · no LIVE wire",
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
                "signal_not_apply": True,
                "floors": floors,
                "refine_families": [
                    "and_combo",
                    "or_combo",
                    "k_confirm",
                    "adaptive_threshold",
                    "dual_horizon",
                    "episode",
                ],
                "forbidden": [
                    "live_wire",
                    "tip_apply",
                    "soft_fin_tel_accept",
                    "path4_live",
                    "broker",
                    "year_oracle",
                    "size_overlay_promote",
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
        f"Date: {day} · Verdict: **`{verdict}`** · top=**`{(champ or {}).get('detector')}`**",
        f"Register: **{REGISTER}** · **{LABEL_TAG}** · n={len(rows)} · "
        f"HIT={n_hit} · WEAK={n_weak} · OVERFIT={n_over} · NO_EDGE={n_no}",
        "",
        "## Meta",
        "",
        f"- base `{meta['base_id']}` `{meta['base_path']}` · soft `{meta['soft_id']}`",
        f"- Mar2020 {MAR2020_START}→{MAR2020_END} · floors from 0kbh (no tighten)",
        f"- skipped parent detectors: {', '.join(meta['skipped_detectors']) or '(none)'}",
        "",
        "## Floors (0kbh)",
        "",
        f"- |IC|≥**{IC_ABS_FLOOR}** · hit(H1'20)≥**{HIT_FLOOR}** · recall(Mar)≥**{RECALL_MAR_FLOOR}** · "
        f"lead≥**{LEAD_DAYS_FLOOR}**d · FA≠2020≤**{FA_OUTSIDE_2020_CEIL}** · "
        f"OOS|IC|≥**{OOS_IC_ABS_FLOOR}** · year-dummy|IC|<**{YEAR_DUMMY_IC_ABS_CEIL}**",
        "",
        "## vs 0kbh champ",
        "",
    ]
    if vs_parent:
        screen_md += [
            f"- 0kbh: `{PARENT_0KBH_CHAMP['detector']}` IC **{PARENT_0KBH_CHAMP['ic_spearman_primary']}** · "
            f"hit **{PARENT_0KBH_CHAMP['hit_rate_mar']}** · lead **{PARENT_0KBH_CHAMP['median_lead_days']}**d",
            f"- refine: `{vs_parent['refine_detector']}` IC **{vs_parent['refine_ic']}** · "
            f"hit **{vs_parent['refine_hit_mar']}** · lead **{vs_parent['refine_lead']}**d",
            f"- Δ IC **{vs_parent['ic_delta_vs_0kbh']}** · Δ hit **{vs_parent['hit_delta_vs_0kbh']}** · "
            f"SIGNAL_HIT achieved **{vs_parent['signal_hit_achieved']}**",
            "",
        ]
    screen_md += [
        "## Family counts",
        "",
        "| Family | n | HIT | WEAK | OVERFIT | NO_EDGE |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for fam, c in sorted(by_fam.items()):
        screen_md.append(
            f"| {fam} | {c['n']} | {c['hit']} | {c['weak']} | {c['overfit']} | {c['no_edge']} |"
        )
    screen_md += [
        "",
        "## Top refine arms",
        "",
        "| Arm | Family | IC(sp) | IC OOS | hit(Mar) | recall | lead d | FA≠2020 | verdict |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for r in top:
        screen_md.append(
            f"| {r['detector']} | {r['family']} | {r['ic_spearman_primary']} | "
            f"{r['ic_spearman_oos_ex2020']} | {r['hit_rate_mar']} | {r['recall_mar']} | "
            f"{r['median_lead_days']} | {r['fa_rate_outside_2020']} | {r['verdict']} |"
        )
    screen_md += [
        "",
        "## Best by family",
        "",
    ]
    for fam, r in sorted(best_by_fam.items()):
        screen_md.append(
            f"- **{fam}**: `{r['detector']}` IC={r['ic_spearman_primary']} "
            f"hit={r['hit_rate_mar']} lead={r['median_lead_days']} · {r['verdict']}"
        )
    screen_md += [
        "",
        "## Optimize / disposition",
        "",
        *[f"{i}. {line}" for i, line in enumerate(optimize, 1)],
        "",
        "Repro: `PYTHONPATH=scripts python3 scripts/tipsoft_ip3_y2020_crisis_signal_refine_stagea.py`",
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
            f"Date: {day} · Verdict: **`{verdict}`** · top=**`{(champ or {}).get('detector')}`**",
            f"Register: **{REGISTER}** · Parents: {', '.join(PARENTS)} · **{LABEL_TAG}**",
            "",
            "## Result",
            "",
            (
                f"- refine arm: `{champ.get('detector')}` family **{champ.get('family')}**\n"
                f"- IC (Spearman): **{champ.get('ic_spearman_primary')}** "
                f"(OOS ex-2020 **{champ.get('ic_spearman_oos_ex2020')}**)\n"
                f"- hit(Mar) **{champ.get('hit_rate_mar')}** · recall **{champ.get('recall_mar')}** · "
                f"F1 **{champ.get('f1_mar')}**\n"
                f"- median lead: **{champ.get('median_lead_days')}**d · "
                f"FA≠2020 **{champ.get('fa_rate_outside_2020')}**\n"
                f"- vs 0kbh `rvol20_l4`: IC Δ **{(vs_parent or {}).get('ic_delta_vs_0kbh')}** · "
                f"hit Δ **{(vs_parent or {}).get('hit_delta_vs_0kbh')}**\n"
                f"- SIGNAL_HIT achieved: **{n_hit > 0}** · "
                f"clears HIT **{n_hit}** · WEAK **{n_weak}** · OVERFIT **{n_over}** · NO_EDGE **{n_no}**"
                if champ
                else f"- No clear · n={len(rows)}"
            ),
            "",
            "## Disposition",
            "",
            *[f"- {line}" for line in disp],
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
                "champion": champ,
                "vs_0kbh_champ": vs_parent,
                "n_signal_hit": n_hit,
                "n_signal_weak": n_weak,
                "n_signal_overfit": n_over,
                "n_signal_no_edge": n_no,
                "signal_hit_achieved": n_hit > 0,
                "signal_not_apply": True,
                "soak_unlock": False,
                "live_wire_recommend": False,
                "size_overlay_promote": False,
                "compare_parents": compare,
                "best_by_family": best_by_fam,
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

    _patch_register(verdict, champ, day)
    _patch_ops_status(verdict, champ, day)

    summary = {
        "verdict": verdict,
        "champion": None if not champ else champ["detector"],
        "champion_family": None if not champ else champ.get("family"),
        "ic_spearman_primary": None if not champ else champ.get("ic_spearman_primary"),
        "hit_rate_mar": None if not champ else champ.get("hit_rate_mar"),
        "recall_mar": None if not champ else champ.get("recall_mar"),
        "median_lead_days": None if not champ else champ.get("median_lead_days"),
        "fa_rate_outside_2020": None if not champ else champ.get("fa_rate_outside_2020"),
        "ic_spearman_oos_ex2020": None if not champ else champ.get("ic_spearman_oos_ex2020"),
        "n_signal_hit": n_hit,
        "n_signal_weak": n_weak,
        "n_signal_overfit": n_over,
        "n_signal_no_edge": n_no,
        "n_arms": len(rows),
        "signal_hit_achieved": n_hit > 0,
        "vs_0kbh_champ": vs_parent,
        "signal_not_apply": True,
        "soak_unlock": False,
        "live_wire_recommend": False,
        "label_tag": LABEL_TAG,
        "register": REGISTER,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
