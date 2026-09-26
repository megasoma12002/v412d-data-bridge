#!/usr/bin/env python3
"""Live strategy targets — Soft-Frozen + FUSE / COOL (or legacy DH) overlays.

E45 A05 live stitch is DROPPED (no re-enable path). Separates target
construction from ledger/fill execution so a future broker adapter can
consume the same sleeve weights + within-sleeve panels.

2026-09-25: COOL_c8 replaces DH_dd06 on live (keep FUSE). DH+COOL stack is refused.
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
      tw, e20w, tw_pre_risk, risk_exposure_today, e45_exposure_today, fuse_meta, risk_meta

    ``e45_exposure_today`` is always 1.0 — A05 live stitch is DROPPED (no flip path).
    ``risk_exposure_today`` is COOL or legacy DH scale (1.0 when neither live).
    """
    if bool(cfg.live_dh_exposure) and bool(cfg.live_cool_exposure):
        raise SystemExit(
            "Refuse live stack: LIVE_DH_EXPOSURE and LIVE_COOL_EXPOSURE both True "
            "(stacking FORBIDDEN — replace DH or keep DH, not both)."
        )

    fuse_meta: dict[str, Any] = {"enabled": bool(cfg.live_fuse_additive)}
    if cfg.live_fuse_additive:
        import live_cool_c8_cutover as cool_cut
        import live_dh_fuse_cutover as live_cut

        target = live_cut.fuse_target_for_market(m)
        recipe = (
            cool_cut.LIVE_RECIPE_ID
            if cfg.live_cool_exposure
            else live_cut.LIVE_RECIPE_ID
        )
        accept = (
            cool_cut.HUMAN_ACCEPT
            if cfg.live_cool_exposure
            else live_cut.HUMAN_ACCEPT
        )
        fuse_meta = {
            "enabled": True,
            "recipe": recipe,
            "human_accept": accept,
        }
    tw = target.iloc[-1]
    tw_pre_risk = {
        "Financial": float(tw.Financial),
        "Telecom": float(tw.Telecom),
        "0050": float(tw["0050"]),
    }
    risk_exposure_today = 1.0
    risk_meta: dict[str, Any] = {"enabled": False, "overlay": None}

    if cfg.live_cool_exposure:
        import live_cool_c8_cutover as cool_cut
        import e45_crisis_core as e45

        div_for_cool = (
            pd.read_csv(dividends_path, dtype={"code": str})
            if Path(dividends_path).exists()
            else pd.DataFrame()
        )
        risk_exposure_today, risk_meta = cool_cut.cool_exposure_today(
            m, div_for_cool, latest
        )
        risk_meta = {**risk_meta, "enabled": True, "overlay": "COOL"}
        tw = pd.Series(
            e45.apply_exposure_to_sleeve_weights(
                dict(tw_pre_risk), float(risk_exposure_today)
            )
        )
    elif cfg.live_dh_exposure:
        import live_dh_fuse_cutover as live_cut
        import e45_crisis_core as e45

        div_for_dh = (
            pd.read_csv(dividends_path, dtype={"code": str})
            if Path(dividends_path).exists()
            else pd.DataFrame()
        )
        risk_exposure_today, risk_meta = live_cut.dh_exposure_today(
            m, div_for_dh, latest
        )
        risk_meta = {**risk_meta, "enabled": True, "overlay": "DH"}
        tw = pd.Series(
            e45.apply_exposure_to_sleeve_weights(
                dict(tw_pre_risk), float(risk_exposure_today)
            )
        )

    # CONF_RET3_A10_H5 × 00631L — scale Soft after COOL/DH (paper twin soft_scale).
    if bool(getattr(cfg, "live_conf_ret3_631l", False)):
        import live_conf_ret3_631l_cutover as conf_ret3

        div_for_off = (
            pd.read_csv(dividends_path, dtype={"code": str})
            if Path(dividends_path).exists()
            else pd.DataFrame()
        )
        off_w, off_meta = conf_ret3.off_weight_today(m, div_for_off, latest)
        tw = pd.Series(conf_ret3.apply_off_to_soft_targets(tw, off_w))
        risk_meta = {
            **risk_meta,
            "conf_ret3_631l": True,
            "conf_ret3_off_weight": float(off_w),
            "conf_ret3_meta": off_meta,
            "conf_ret3_ballot": conf_ret3.HUMAN_ACCEPT,
        }

    # A05 stitch DROPPED — exposure placeholder kept for call-site unpack stability.
    e45_exposure_today = 1.0
    e20w = tw  # unused when caller keeps e20; kept for API symmetry
    return tw, e20w, tw_pre_risk, risk_exposure_today, e45_exposure_today, fuse_meta, risk_meta
