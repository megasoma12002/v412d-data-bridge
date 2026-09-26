#!/usr/bin/env python3
"""Live T3_COOL_INV_VOL20 TEL within-sleeve cutover (forward-only).

Human ballot (2026-09-26):
  ``請上live`` / intent: ACCEPT live ``T3_COOL_INV_VOL20``

Normalized:
  ``ACCEPT Live cutover: T3_COOL_INV_VOL20 (TEL within-sleeve under COOL)``

Paper twin (Stage A ``TEL_WITHIN_SOFT`` → densify ``TEL_NEARFLAT_READY``):
  - ``TEL_RS_SOFT_TILT`` + INV_VOL20 name scores
  - Active only when ``cool_exposure < 1`` (COOL defending)
  - Off-defense: behave as ``TEL_EQUAL``
  - held CAGR↑ +0.16pp · MDD/tip OK · near-flat floor +0.15

Soft-Frozen clips / KD_OPT / FUSE / COOL / SELL_a75 / FinPriv / CONF_RET3 **KEEP**.
Does **not** rewrite tip history · broker live-write still PREP-only.
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from e16_soft_frozen_base import TEL
from within_sleeve_alloc import TEL_EQUAL, TEL_RS_SOFT_TILT

HUMAN_ACCEPT = (
    "ACCEPT Live cutover: T3_COOL_INV_VOL20 (TEL within-sleeve under COOL)"
)
LIVE_RECIPE_ID = "LIVE_TEL_T3_COOL_INV_VOL20"
SCORE_FAMILY = "INV_VOL20"
OFF_DEFENSE_POLICY = TEL_EQUAL
DEFENSE_POLICY = TEL_RS_SOFT_TILT


def _xz(df: pd.DataFrame) -> pd.DataFrame:
    mu = df.mean(axis=1)
    sd = df.std(axis=1).replace(0.0, np.nan)
    return df.sub(mu, axis=0).div(sd, axis=0).fillna(0.0).clip(-3.0, 3.0)


def build_inv_vol20_scores(market: pd.DataFrame) -> pd.DataFrame:
    """Causal TEL cross-sectional inverse 20d return-vol scores (clipped z)."""
    m = market.copy()
    m["date"] = pd.to_datetime(m["date"])
    m["code"] = m["code"].astype(str)
    codes = list(TEL)
    adj = (
        m.pivot(index="date", columns="code", values="adj_close")
        .sort_index()
        .ffill()
    )
    for c in codes:
        if c not in adj.columns:
            raise ValueError(f"missing TEL code {c} in market adj_close")
    close = adj[codes]
    rets = close.pct_change()
    vol20 = rets.rolling(20, min_periods=10).std()
    return _xz(1.0 / (vol20 + 1e-8))


def scores_for_asof(
    market: pd.DataFrame, asof: pd.Timestamp
) -> tuple[dict[str, float] | None, dict[str, Any]]:
    """INV_VOL20 score map for asof, or None if insufficient."""
    meta: dict[str, Any] = {"score_family": SCORE_FAMILY, "asof": str(pd.Timestamp(asof).date())}
    try:
        panel = build_inv_vol20_scores(market)
    except Exception as exc:  # fail-closed → EQUAL
        meta["ok"] = False
        meta["reason"] = f"score_build_failed:{type(exc).__name__}"
        return None, meta
    asof = pd.Timestamp(asof).normalize()
    if asof not in panel.index:
        # nearest prior row
        prior = panel.index[panel.index <= asof]
        if len(prior) == 0:
            meta["ok"] = False
            meta["reason"] = "no_score_row_le_asof"
            return None, meta
        asof = prior[-1]
        meta["asof_used"] = str(asof.date())
    row = panel.loc[asof]
    out: dict[str, float] = {}
    for c in TEL:
        if c in row.index and pd.notna(row[c]):
            out[c] = float(row[c])
    if len(out) < 2:
        meta["ok"] = False
        meta["reason"] = "insufficient_tel_scores"
        return None, meta
    meta["ok"] = True
    meta["scores"] = {k: round(v, 6) for k, v in out.items()}
    return out, meta


def resolve_tel_policy(
    *,
    cool_exposure: float | None,
    scores_ok: bool,
) -> tuple[str, bool, dict[str, Any]]:
    """Return (policy_id, tilt_active, meta). Fail-closed to TEL_EQUAL."""
    meta: dict[str, Any] = {
        "recipe": LIVE_RECIPE_ID,
        "cool_exposure": None if cool_exposure is None else float(cool_exposure),
    }
    if cool_exposure is None:
        meta["defending"] = False
        meta["reason"] = "missing_cool_exposure"
        return OFF_DEFENSE_POLICY, False, meta
    cool = float(cool_exposure)
    defending = cool < 1.0 - 1e-12
    meta["defending"] = defending
    if not defending:
        meta["reason"] = "off_defense_equal"
        return OFF_DEFENSE_POLICY, False, meta
    if not scores_ok:
        meta["reason"] = "scores_fail_closed_equal"
        return OFF_DEFENSE_POLICY, False, meta
    meta["reason"] = "cool_defend_inv_vol20"
    return DEFENSE_POLICY, True, meta


__all__ = [
    "HUMAN_ACCEPT",
    "LIVE_RECIPE_ID",
    "SCORE_FAMILY",
    "OFF_DEFENSE_POLICY",
    "DEFENSE_POLICY",
    "build_inv_vol20_scores",
    "scores_for_asof",
    "resolve_tel_policy",
]
