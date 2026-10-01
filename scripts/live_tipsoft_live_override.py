#!/usr/bin/env python3
"""tip Soft Exact T+1 LIVE_OVERRIDE — live gate stamps / telemetry (0kb2 ACCEPT).

Wire mode: **gate_stamps_telemetry** (PROJECT_CODE_REVIEW_2026-10-01).

Computes the causal LIVE_OVERRIDE gate (lag-1 42d cumret(live−champ) > 0.005
for K=3 days) and stamps it on the live session. It does **not** apply the
research return blend ``r = where(conf, live_r, champ_r)`` to ``order_rows``.

Coexistence (ACCEPT explicit):
- Path3 WITHIN_SLEEVE KEEP · Soft FIN/TEL Exact T+1 stay OFF
- Soft clips + Soft 0050 Exact T+1 KEEP
- T0_CARVE_FIN_SAT_SWITCH KEEP · Path4 OFF · broker false
- Dual-paper observe KEEP

Stage A arm alias: ``OVERRIDE_LIVE_W42_M0005_K3`` (margin 0.005) ≡ policy ``…_M05_K3``.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

MECHANISM_ID = "TIPSOFT_P3_LIVE_OVERRIDE_W42_M05_K3"
POLICY_ID = "TIPSOFT_P3_LIVE_OVERRIDE_W42_M05_K3"
STAGE_A_ARM_ID = "OVERRIDE_LIVE_W42_M0005_K3"  # str(0.005) → M0005
CLOCK = "exact_t1"
WIRE_MODE = "gate_stamps_telemetry"
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
STAGE_A_POLICY_NAV = (
    ROOT
    / "repro/tipsoft-ip3-live-stack-race-stagea/outputs/nav_OVERRIDE_LIVE_W42_M0005_K3.csv"
)


def is_on() -> bool:
    try:
        from live_config import LIVE

        return bool(getattr(LIVE, "live_tipsoft_live_override", False))
    except ImportError:
        return False


def _live_safety_stamps() -> dict[str, Any]:
    """Assert coexistence from LIVE SSOT (not hardcoded wishful stamps)."""
    try:
        from live_config import LIVE

        path3_on = bool(getattr(LIVE, "live_path3_strategy_cutover", False))
        broker = bool(getattr(LIVE, "broker_live_write_accepted", False))
        path4 = bool(getattr(LIVE, "live_path4", False))  # absent → False
    except ImportError:
        path3_on, broker, path4 = False, False, False
    return {
        "path3_within_sleeve_keep": path3_on,
        "soft_fin_tel_stay_off": path3_on,  # WITHIN cutover suppresses Soft FIN/TEL
        "path4_live": path4,
        "broker": broker,
    }


def _trail_sum(x: pd.Series, w: int) -> pd.Series:
    # Match Stage A research helper: min_periods = max(3, w // 3)
    return x.shift(1).rolling(int(w), min_periods=max(3, int(w) // 3)).sum()


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
    market_tip: str | pd.Timestamp | None = None,
) -> dict[str, Any]:
    """Compute tip Soft LIVE_OVERRIDE gate for ``asof``.

    Fail-loud when NAV panel tip is behind ``market_tip`` / requested asof
    (``reason=nav_stale`` · ``override_on=None``).
    """
    safety = _live_safety_stamps()
    out: dict[str, Any] = {
        "mechanism_id": MECHANISM_ID,
        "policy_id": POLICY_ID,
        "stage_a_arm_id": STAGE_A_ARM_ID,
        "clock": CLOCK,
        "wire_mode": WIRE_MODE,
        "window": WINDOW,
        "margin": MARGIN,
        "confirm_k": CONFIRM_K,
        "enabled": is_on(),
        "return_blend_applied": False,
        **safety,
    }
    if not live_nav_path.is_file() or not champ_nav_path.is_file():
        out.update(
            {
                "ok": False,
                "stale": None,
                "reason": "missing_nav",
                "override_on": None,
            }
        )
        return out

    live_nav = _load_nav(live_nav_path)
    champ_nav = _load_nav(champ_nav_path)
    live_r = _returns(live_nav)
    champ_r = _returns(champ_nav)
    panel = pd.concat({"live": live_r, "champ": champ_r}, axis=1, join="inner").dropna(
        how="any"
    )
    if panel.empty:
        out.update(
            {
                "ok": False,
                "stale": None,
                "reason": "empty_panel",
                "override_on": None,
            }
        )
        return out

    panel_tip = pd.Timestamp(panel.index.max()).normalize()
    req = None if asof is None else pd.Timestamp(asof).normalize()
    mtip = None if market_tip is None else pd.Timestamp(market_tip).normalize()
    # Stale if caller tip (market or asof) is strictly after panel tip.
    compare_tip = mtip if mtip is not None else req
    if compare_tip is not None and compare_tip > panel_tip:
        out.update(
            {
                "ok": False,
                "stale": True,
                "reason": "nav_stale",
                "asof": str(compare_tip.date()),
                "panel_tip": str(panel_tip.date()),
                "override_on": None,
                "force_live_shell_diag": None,
                "stack_mute_s3_sat_diag": None,
            }
        )
        return out

    mask = override_mask(panel["live"], panel["champ"])
    if req is None:
        ts = panel_tip
    else:
        if req not in mask.index:
            prior = mask.index[mask.index <= req]
            if len(prior) == 0:
                out.update(
                    {
                        "ok": False,
                        "stale": False,
                        "reason": "asof_before_panel",
                        "asof": str(req.date()),
                        "panel_tip": str(panel_tip.date()),
                        "override_on": None,
                    }
                )
                return out
            ts = prior.max()
        else:
            ts = req

    override_on = bool(mask.loc[ts])
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
            "stale": False,
            "reason": "ok",
            "asof": str(pd.Timestamp(ts).date()),
            "panel_tip": str(panel_tip.date()),
            "override_on": override_on,
            # Diagnostic only — Soft FIN/TEL stay OFF under Path3 WITHIN.
            "force_live_shell_diag": override_on,
            "stack_mute_s3_sat_diag": (not override_on),
            "policy_nav_equals_live_diag": policy_eq_live,
            "pct_override_hist": round(float(mask.mean()) * 100.0, 4),
        }
    )
    return out


def session_meta(
    asof: str | pd.Timestamp | None = None,
    *,
    market_tip: str | pd.Timestamp | None = None,
) -> dict[str, Any]:
    """Pipeline / tip-meta stamp block — flat columns for signals.csv."""
    on = is_on()
    gate = compute_gate_state(asof, market_tip=market_tip if market_tip is not None else asof)
    safety = _live_safety_stamps()
    return {
        "tipsoft_live_override_live": bool(on),
        "tipsoft_live_override_wire_mode": WIRE_MODE if on else None,
        "tipsoft_live_override_policy": POLICY_ID if on else None,
        "tipsoft_live_override_stage_a_arm": STAGE_A_ARM_ID if on else None,
        "tipsoft_live_override_ballot": ACCEPT_BALLOT if on else None,
        "tipsoft_live_override_cutover": (
            "ACCEPT_2026-09-30_TIPSOFT_P3_LIVE_OVERRIDE_W42_M05_K3" if on else None
        ),
        "tipsoft_live_override_rollback": (
            "Set LIVE.live_tipsoft_live_override=False "
            "(live_config.live_tipsoft_live_override); tip Soft Exact T+1 "
            "LIVE_OVERRIDE gate stamps off; Path3 WITHIN / Soft FIN/TEL unchanged"
            if on
            else None
        ),
        # Flattened gate (M1) — no nested dict in signals.csv
        "tipsoft_override_on": gate.get("override_on") if on else None,
        "tipsoft_override_asof": gate.get("asof") if on else None,
        "tipsoft_override_ok": gate.get("ok") if on else None,
        "tipsoft_override_stale": gate.get("stale") if on else None,
        "tipsoft_override_reason": gate.get("reason") if on else None,
        "tipsoft_override_panel_tip": gate.get("panel_tip") if on else None,
        "tipsoft_override_return_blend_applied": False,
        "tipsoft_live_override_path3_within_keep": bool(
            safety["path3_within_sleeve_keep"]
        ),
        "tipsoft_live_override_soft_fin_tel_stay_off": bool(
            safety["soft_fin_tel_stay_off"]
        ),
        "tipsoft_live_override_path4_live": bool(safety["path4_live"]),
        "tipsoft_live_override_broker": bool(safety["broker"]),
    }
