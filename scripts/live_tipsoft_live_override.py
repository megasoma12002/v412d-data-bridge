#!/usr/bin/env python3
"""tip Soft Exact T+1 LIVE_OVERRIDE — live wire (0kb2 ACCEPT).

Policy: default tip Soft stack = 0kb1 MUTE_S3_SAT 3-state; force LIVE Soft+FUSE+COOL
Exact T+1 shell when lag-1 42d cumret(live−champ) > 0.005 for K=3 consecutive days.

Coexistence (ACCEPT explicit):
- Path3 WITHIN_SLEEVE KEEP · Soft FIN/TEL Exact T+1 stay OFF
- Soft clips + Soft 0050 Exact T+1 KEEP
- T0_CARVE_FIN_SAT_SWITCH KEEP · Path4 OFF · broker false
- Dual-paper observe KEEP

This module is live SSOT for the tip Soft Exact T+1 override gate + session stamps.
It does **not** re-enable Soft FIN/TEL or undo Path3 WITHIN.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

MECHANISM_ID = "TIPSOFT_P3_LIVE_OVERRIDE_W42_M05_K3"
POLICY_ID = "TIPSOFT_P3_LIVE_OVERRIDE_W42_M05_K3"
CLOCK = "exact_t1"
WINDOW = 42
MARGIN = 0.005
CONFIRM_K = 3

ACCEPT_BALLOT = (
    "ACCEPT live wire: TIPSOFT_P3_LIVE_OVERRIDE_W42_M05_K3\n"
    "(Exact T+1 · 0kb1 MUTE_S3_SAT + force LIVE when lag42 live leads champ by >0.5% for 3d ·\n"
    " Path3 WITHIN_SLEEVE KEEP · Soft FIN/TEL stay OFF · Soft clips+0050 KEEP ·\n"
    " T0_CARVE_FIN_SAT_SWITCH KEEP · Path4 OFF · broker false · dual-paper observe KEEP)"
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LIVE_NAV = (
    ROOT / "repro/tipsoft-ip3-live-override-paper-observe/outputs/nav_BASE_LIVE_FUSE_COOL.csv"
)
DEFAULT_POLICY_NAV = (
    ROOT
    / "repro/tipsoft-ip3-live-override-paper-observe/outputs/nav_OVERRIDE_LIVE_W42_M05_K3.csv"
)
DEFAULT_CHAMP_NAV = (
    ROOT / "repro/tipsoft-ip3-live-stack-race-stagea/outputs/nav_REF_MUTE_S3_SAT_W63.csv"
)


def is_on() -> bool:
    try:
        from live_config import LIVE

        return bool(getattr(LIVE, "live_tipsoft_live_override", False))
    except Exception:
        return False


def _trail_sum(x: pd.Series, w: int) -> pd.Series:
    return x.shift(1).rolling(int(w), min_periods=max(2, int(w) // 3)).sum()


def override_mask(
    live_r: pd.Series,
    champ_r: pd.Series,
    *,
    window: int = WINDOW,
    margin: float = MARGIN,
    k: int = CONFIRM_K,
) -> pd.Series:
    """Causal force-LIVE mask: lagW cumret(live−champ) > margin for k days."""
    lead = (_trail_sum(live_r, window) - _trail_sum(champ_r, window)).fillna(0.0)
    conf = lead > float(margin)
    for j in range(1, int(k)):
        conf = conf & (lead.shift(j).fillna(0.0) > float(margin))
    return conf.fillna(False).astype(bool)


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


def compute_gate_state(
    asof: str | pd.Timestamp | None = None,
    *,
    live_nav_path: Path = DEFAULT_LIVE_NAV,
    champ_nav_path: Path = DEFAULT_CHAMP_NAV,
    policy_nav_path: Path = DEFAULT_POLICY_NAV,
) -> dict[str, Any]:
    """Compute tip Soft LIVE_OVERRIDE gate for ``asof`` (default = latest NAV date)."""
    out: dict[str, Any] = {
        "mechanism_id": MECHANISM_ID,
        "policy_id": POLICY_ID,
        "clock": CLOCK,
        "window": WINDOW,
        "margin": MARGIN,
        "confirm_k": CONFIRM_K,
        "enabled": is_on(),
        "path3_within_sleeve_keep": True,
        "soft_fin_tel_stay_off": True,
        "path4_live": False,
        "broker": False,
    }
    if not live_nav_path.is_file() or not champ_nav_path.is_file():
        out.update({"ok": False, "reason": "missing_nav", "override_on": None})
        return out

    live_nav = _load_nav(live_nav_path)
    champ_nav = _load_nav(champ_nav_path)
    live_r = _returns(live_nav)
    champ_r = _returns(champ_nav)
    panel = pd.concat({"live": live_r, "champ": champ_r}, axis=1, join="inner").dropna(
        how="any"
    )
    if panel.empty:
        out.update({"ok": False, "reason": "empty_panel", "override_on": None})
        return out

    mask = override_mask(panel["live"], panel["champ"])
    if asof is None:
        ts = panel.index.max()
    else:
        ts = pd.Timestamp(asof).normalize()
        if ts not in mask.index:
            # nearest prior session
            prior = mask.index[mask.index <= ts]
            if len(prior) == 0:
                out.update(
                    {
                        "ok": False,
                        "reason": "asof_before_panel",
                        "asof": str(ts.date()),
                        "override_on": None,
                    }
                )
                return out
            ts = prior.max()

    override_on = bool(mask.loc[ts])
    # policy NAV diagnostic: days where policy == live (force LIVE active)
    policy_eq_live = None
    if policy_nav_path.is_file():
        pol_r = _returns(_load_nav(policy_nav_path)).reindex(panel.index).fillna(0.0)
        eps = 1e-12
        policy_eq_live = bool(
            abs(float(pol_r.loc[ts]) - float(panel["live"].loc[ts])) <= eps
        )

    out.update(
        {
            "ok": True,
            "asof": str(pd.Timestamp(ts).date()),
            "override_on": override_on,
            "force_live_shell": override_on,
            "stack_mute_s3_sat_active": (not override_on),
            "policy_nav_equals_live_diag": policy_eq_live,
            "pct_override_hist": round(float(mask.mean()) * 100.0, 4),
        }
    )
    return out


def session_meta(asof: str | pd.Timestamp | None = None) -> dict[str, Any]:
    """Pipeline / tip-meta stamp block."""
    gate = compute_gate_state(asof)
    return {
        "tipsoft_live_override_live": bool(is_on()),
        "tipsoft_live_override_policy": POLICY_ID if is_on() else None,
        "tipsoft_live_override_ballot": ACCEPT_BALLOT if is_on() else None,
        "tipsoft_live_override_cutover": (
            "ACCEPT_2026-09-30_TIPSOFT_P3_LIVE_OVERRIDE_W42_M05_K3" if is_on() else None
        ),
        "tipsoft_live_override_rollback": (
            "Set LIVE.live_tipsoft_live_override=False "
            "(live_config.live_tipsoft_live_override); tip Soft Exact T+1 "
            "LIVE_OVERRIDE gate stamps off; Path3 WITHIN / Soft FIN/TEL unchanged"
            if is_on()
            else None
        ),
        "tipsoft_live_override_gate": gate if is_on() else {"enabled": False},
        "tipsoft_live_override_path3_within_keep": True,
        "tipsoft_live_override_soft_fin_tel_stay_off": True,
        "tipsoft_live_override_path4_live": False,
    }
