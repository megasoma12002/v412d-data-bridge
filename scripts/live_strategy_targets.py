#!/usr/bin/env python3
"""Live strategy targets — Soft-Frozen + FUSE / DH overlays.

E45 A05 live stitch is DROPPED (no re-enable path). Separates target
construction from ledger/fill execution so a future broker adapter can
consume the same sleeve weights + within-sleeve panels.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

import e16_soft_frozen_base as soft_frozen
from e16_soft_frozen_base import FIN, TEL
from live_config import LiveConfig, LIVE

ALL = FIN + TEL + ["0050"]


def features(m: pd.DataFrame):
    """Live Soft-Frozen E16 targets (+ E19/E20 diagnostics).

    Clip/prior/blend: ``e16_soft_frozen_base`` SSOT (shared with research).
    """
    p, sleeve, target, reg, score = soft_frozen.build_soft_frozen_targets(m)
    tc = p["TAIEX"]
    vol = tc.pct_change().rolling(20).std() * np.sqrt(252)
    defensive = (sleeve.Financial + sleeve["0050"]) / 2
    corr = sleeve.Telecom.rolling(20).corr(defensive)
    te = (1 + sleeve.Telecom).rolling(20).apply(np.prod, raw=True) - 1
    me = (1 + defensive).rolling(20).apply(np.prod, raw=True) - 1
    tv = sleeve.Telecom.rolling(20).std()
    mv = defensive.rolling(20).std()
    pts = (
        (corr > 0.55).astype(int)
        + (te - me < -0.02).astype(int)
        + (tv > mv * 1.15).astype(int)
        + (te < -0.04).astype(int)
    )
    alert = pts >= 2
    price_ok = tc > tc.rolling(20).mean()
    vol_ok = vol < vol.shift(10)
    rel = (1 + sleeve.Financial).cumprod() / (1 + sleeve["0050"]).cumprod()
    rs_ok = rel / rel.shift(20) - 1 >= 0
    conf = price_ok.astype(int) + vol_ok.astype(int) + rs_ok.astype(int)
    streak = []
    n = 0
    for v in (conf >= 3).fillna(False):
        n = n + 1 if v else 0
        streak.append(n)
    e20 = target.copy()
    latest = len(e20) - 1
    req = 6 if alert.iloc[latest] else 3
    if reg.iloc[latest] == "Crisis" and streak[latest] < req:
        release = max(0, e20.iloc[latest, 0] - 0.75)
        e20.iloc[latest, 0] -= release
        e20.iloc[latest, 1] += release
    diag = {
        "regime": reg.iloc[-1],
        "score_financial": score.iloc[-1, 0],
        "score_telecom": score.iloc[-1, 1],
        "score_0050": score.iloc[-1, 2],
        "e19_points": int(pts.iloc[-1]),
        "e19_alert": bool(alert.iloc[-1]),
        "e20_confirmations": int(conf.iloc[-1]),
        "e20_streak": int(streak[-1]),
    }
    return p, sleeve, target, e20, diag


def resolve_session_targets(
    m: pd.DataFrame,
    target: pd.DataFrame,
    latest: pd.Timestamp,
    dividends_path: Path | str,
    cfg: LiveConfig = LIVE,
) -> tuple[pd.Series, pd.Series, dict[str, float], float, float, dict[str, Any], dict[str, Any]]:
    """Apply live overlays to Soft-Frozen targets for one session date.

    Returns:
      tw, e20w, tw_pre_dh, dh_exposure_today, e45_exposure_today, fuse_meta, dh_meta

    ``e45_exposure_today`` is always 1.0 — A05 live stitch is DROPPED (no flip path).
    """
    fuse_meta: dict[str, Any] = {"enabled": bool(cfg.live_fuse_additive)}
    if cfg.live_fuse_additive:
        import live_dh_fuse_cutover as live_cut

        target = live_cut.fuse_target_for_market(m)
        fuse_meta = {
            "enabled": True,
            "recipe": live_cut.LIVE_RECIPE_ID,
            "human_accept": live_cut.HUMAN_ACCEPT,
        }
    tw = target.iloc[-1]
    # e20 still from Soft-Frozen path caller; recompute not needed here.
    tw_pre_dh = {
        "Financial": float(tw.Financial),
        "Telecom": float(tw.Telecom),
        "0050": float(tw["0050"]),
    }
    dh_exposure_today = 1.0
    dh_meta: dict[str, Any] = {"enabled": False}
    if cfg.live_dh_exposure:
        import live_dh_fuse_cutover as live_cut
        import e45_crisis_core as e45

        div_for_dh = (
            pd.read_csv(dividends_path, dtype={"code": str})
            if Path(dividends_path).exists()
            else pd.DataFrame()
        )
        dh_exposure_today, dh_meta = live_cut.dh_exposure_today(m, div_for_dh, latest)
        dh_meta = {**dh_meta, "enabled": True}
        tw = pd.Series(
            e45.apply_exposure_to_sleeve_weights(dict(tw_pre_dh), float(dh_exposure_today))
        )

    # A05 stitch DROPPED — exposure placeholder kept for call-site unpack stability.
    e45_exposure_today = 1.0
    e20w = tw  # unused when caller keeps e20; kept for API symmetry
    return tw, e20w, tw_pre_dh, dh_exposure_today, e45_exposure_today, fuse_meta, dh_meta
