#!/usr/bin/env python3
"""tip Soft Exact T+1 TRAIL42⇄L4 DD_SWITCH — tip apply wire (0kbd ACCEPT).

Wire mode: **path3_gate_ft_cash_apply** (not stamps-only · not research return-blend).

Rule (Stage A champ ``SW_TRAIL_WHEN_TR_DD_GTE_L4`` / policy
``TIPSOFT_P3_TRAIL42_L4_DD_SWITCH``):

- Dual-book: each day prefer TRAIL42 tip Soft twin if TRAIL DD ≥ L4 DD, else L4.
- On TRAIL-selected days: Path3 ON when trail42d prem_p3 ≥ −0.01; OFF → FIN∪TEL→cash
  via ``-P3T0`` flatten deltas (Soft FIN/TEL Exact T+1 stay OFF).
- On L4-selected days: Path3 WITHIN daily recon KEEP (current live).

Coexistence (ACCEPT explicit):
- Path3 WITHIN_SLEEVE cutover KEEP · Soft FIN/TEL Exact T+1 stay OFF
- Soft clips + Soft 0050 Exact T+1 KEEP
- T0_CARVE_FIN_SAT_SWITCH KEEP · Path4 OFF · broker false
- Dual-paper observe 0kbd/0kba/0kbb KEEP · year-switch FORBIDDEN
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from e16_soft_frozen_base import FIN, TEL

MECHANISM_ID = "TIPSOFT_P3_TRAIL42_L4_DD_SWITCH"
POLICY_ID = "TIPSOFT_P3_TRAIL42_L4_DD_SWITCH"
STAGE_A_ARM_ID = "SW_TRAIL_WHEN_TR_DD_GTE_L4"
CLOCK = "exact_t1"
WIRE_MODE = "path3_gate_ft_cash_apply"
TRAIL_WINDOW = 42
TRAIL_THR = -0.01

ACCEPT_BALLOT = (
    "ACCEPT tip apply: TIPSOFT_P3_TRAIL42_L4_DD_SWITCH\n"
    "(tip Soft Exact T+1 · dual-book DD switch · Soft FIN/TEL stay OFF ·\n"
    " Path3 WITHIN KEEP · Path4 OFF · broker false · NOT year-switch · NOT stamps-only)"
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_L4_NAV = (
    ROOT / "repro/tipsoft-ip3-trail42-l4-switch-paper-observe/outputs/nav_L4_LIVE_P3_WITHIN.csv"
)
DEFAULT_TRAIL_NAV = (
    ROOT / "repro/tipsoft-ip3-trail42-cash-paper-observe/outputs/nav_TRAIL42_FT_CASH.csv"
)
FALLBACK_L4_NAV = ROOT / "repro/research-live-align-gap-stagea/outputs/nav_L4_LIVE_P3_WITHIN.csv"
FALLBACK_TRAIL_NAV = (
    ROOT / "repro/tipsoft-ip3-highon-cash-twin-stageb/outputs/nav_TWIN_TRAIL42_CASH.csv"
)
LIVESTACK_L3 = ROOT / "repro/fin-sat-path3-path4-livestack-twin-stageb/outputs/nav_BASE_LIVE_FUSE_COOL.csv"
LIVESTACK_P3 = ROOT / "repro/fin-sat-path3-path4-livestack-twin-stageb/outputs/nav_LIVE_P3_WITHIN.csv"
SOFT_CORE_CODES = list(FIN) + list(TEL)


def is_on() -> bool:
    try:
        from live_config import LIVE

        return bool(getattr(LIVE, "live_tipsoft_dd_switch", False))
    except ImportError:
        return False


def _live_safety_stamps() -> dict[str, Any]:
    try:
        from live_config import LIVE

        path3_on = bool(getattr(LIVE, "live_path3_strategy_cutover", False))
        broker = bool(getattr(LIVE, "broker_live_write_accepted", False))
        path4 = bool(getattr(LIVE, "live_path4", False))
    except ImportError:
        path3_on, broker, path4 = False, False, False
    return {
        "path3_within_sleeve_keep": path3_on,
        "soft_fin_tel_stay_off": path3_on,
        "path4_live": path4,
        "broker": broker,
    }


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


def _trail_sum(x: pd.Series, w: int) -> pd.Series:
    return x.shift(1).rolling(int(w), min_periods=max(3, int(w) // 3)).sum()


def _resolve_nav(primary: Path, fallback: Path) -> Path:
    if primary.is_file():
        return primary
    return fallback


def trail42_on_series(
    *,
    l3_nav_path: Path = LIVESTACK_L3,
    p3_nav_path: Path = LIVESTACK_P3,
    window: int = TRAIL_WINDOW,
    thr: float = TRAIL_THR,
) -> pd.Series:
    """Causal TRAIL42_GE_m001: lag-1 rolling sum(prem_p3) ≥ thr."""
    if not l3_nav_path.is_file() or not p3_nav_path.is_file():
        return pd.Series(dtype=bool)
    r3 = _returns(_load_nav(l3_nav_path))
    rp3 = _returns(_load_nav(p3_nav_path))
    panel = pd.concat({"r3": r3, "rp3": rp3}, axis=1, join="inner").dropna(how="any")
    if panel.empty:
        return pd.Series(dtype=bool)
    prem = panel["rp3"] - panel["r3"]
    return (_trail_sum(prem, window).fillna(0.0) >= float(thr)).astype(bool)


def want_trail_series(
    *,
    l4_nav_path: Path | None = None,
    trail_nav_path: Path | None = None,
) -> pd.Series:
    """Causal dual-book: TRAIL if TRAIL_DD ≥ L4_DD else L4 (want_trail True)."""
    l4_path = l4_nav_path or _resolve_nav(DEFAULT_L4_NAV, FALLBACK_L4_NAV)
    tr_path = trail_nav_path or _resolve_nav(DEFAULT_TRAIL_NAV, FALLBACK_TRAIL_NAV)
    if not l4_path.is_file() or not tr_path.is_file():
        return pd.Series(dtype=bool)
    r_l4 = _returns(_load_nav(l4_path))
    r_tr = _returns(_load_nav(tr_path))
    panel = pd.concat({"l4": r_l4, "tr": r_tr}, axis=1, join="inner").dropna(how="any")
    if panel.empty:
        return pd.Series(dtype=bool)
    l4_nav = (1.0 + panel["l4"]).cumprod()
    tr_nav = (1.0 + panel["tr"]).cumprod()
    l4_dd = l4_nav / l4_nav.cummax() - 1.0
    tr_dd = tr_nav / tr_nav.cummax() - 1.0
    return (tr_dd >= l4_dd).astype(bool)


def path3_active_series(
    want_trail: pd.Series,
    trail42_on: pd.Series,
) -> pd.Series:
    """Path3 active on L4 days, or TRAIL days when TRAIL42 ON."""
    idx = want_trail.index.intersection(trail42_on.index)
    wt = want_trail.reindex(idx).fillna(False).astype(bool)
    t42 = trail42_on.reindex(idx).fillna(False).astype(bool)
    return ((~wt) | t42).astype(bool)


def flatten_fin_tel_deltas(pos: Mapping[str, float]) -> dict[str, float]:
    """Path3 OFF → FIN∪TEL→cash: sell live Soft-core FIN∪TEL shares."""
    out: dict[str, float] = {}
    for code in SOFT_CORE_CODES:
        q = float(pos.get(code, 0.0) or 0.0)
        if abs(q) > 1e-9:
            out[str(code)] = -q
    return out


def _pick_asof(
    series: pd.Series,
    asof: str | pd.Timestamp | None,
    *,
    market_tip: str | pd.Timestamp | None,
) -> tuple[pd.Timestamp | None, str | None, bool | None]:
    """Return (ts, reason, stale). reason None means ok."""
    if series.empty:
        return None, "empty_panel", None
    panel_tip = pd.Timestamp(series.index.max()).normalize()
    req = None if asof is None else pd.Timestamp(asof).normalize()
    mtip = None if market_tip is None else pd.Timestamp(market_tip).normalize()
    compare_tip = mtip if mtip is not None else req
    if compare_tip is not None and compare_tip > panel_tip:
        return None, "nav_stale", True
    if req is None:
        return panel_tip, None, False
    if req in series.index:
        return req, None, False
    prior = series.index[series.index <= req]
    if len(prior) == 0:
        return None, "asof_before_panel", False
    return prior.max(), None, False


def compute_gate_state(
    asof: str | pd.Timestamp | None = None,
    *,
    market_tip: str | pd.Timestamp | None = None,
    l4_nav_path: Path | None = None,
    trail_nav_path: Path | None = None,
) -> dict[str, Any]:
    """Compute DD_SWITCH Path3 gate for ``asof`` (fail-loud on stale NAV)."""
    safety = _live_safety_stamps()
    out: dict[str, Any] = {
        "mechanism_id": MECHANISM_ID,
        "policy_id": POLICY_ID,
        "stage_a_arm_id": STAGE_A_ARM_ID,
        "clock": CLOCK,
        "wire_mode": WIRE_MODE,
        "trail_window": TRAIL_WINDOW,
        "trail_thr": TRAIL_THR,
        "enabled": is_on(),
        "return_blend_applied": False,
        "tip_apply": True,
        **safety,
    }
    want = want_trail_series(l4_nav_path=l4_nav_path, trail_nav_path=trail_nav_path)
    t42 = trail42_on_series()
    if want.empty or t42.empty:
        out.update(
            {
                "ok": False,
                "stale": None,
                "reason": "missing_nav",
                "want_trail": None,
                "trail42_on": None,
                "path3_active": None,
                "fill": None,
            }
        )
        return out

    active = path3_active_series(want, t42)
    ts, reason, stale = _pick_asof(active, asof, market_tip=market_tip)
    if reason is not None:
        out.update(
            {
                "ok": False,
                "stale": stale,
                "reason": reason,
                "asof": None if asof is None else str(pd.Timestamp(asof).date()),
                "panel_tip": str(pd.Timestamp(active.index.max()).date()),
                "want_trail": None,
                "trail42_on": None,
                "path3_active": None,
                "fill": None,
            }
        )
        return out

    assert ts is not None
    wt = bool(want.reindex(active.index).fillna(False).loc[ts])
    t42_on = bool(t42.reindex(active.index).fillna(False).loc[ts])
    p3_on = bool(active.loc[ts])
    fill = "WITHIN" if p3_on else "FT_TO_CASH"
    out.update(
        {
            "ok": True,
            "stale": False,
            "reason": "ok",
            "asof": str(pd.Timestamp(ts).date()),
            "panel_tip": str(pd.Timestamp(active.index.max()).date()),
            "want_trail": wt,
            "trail42_on": t42_on,
            "path3_active": p3_on,
            "fill": fill,
            "pct_days_trail_hist": round(float(want.mean()) * 100.0, 4),
            "pct_path3_active_hist": round(float(active.mean()) * 100.0, 4),
        }
    )
    return out


def apply_to_path3_deltas(
    path3_deltas: Mapping[str, float] | None,
    pos: Mapping[str, float],
    asof: str | pd.Timestamp | None = None,
    *,
    market_tip: str | pd.Timestamp | None = None,
) -> tuple[dict[str, float] | None, dict[str, Any]]:
    """Mutate Path3 plan: WITHIN keep deltas, or FIN∪TEL→cash flatten on OFF days.

    Fail-closed: if gate not ok / flag OFF, return input deltas unchanged.
    """
    meta: dict[str, Any] = {
        "tipsoft_dd_switch_live": is_on(),
        "wire_mode": WIRE_MODE if is_on() else None,
        "applied": False,
        "fill": None,
    }
    if not is_on():
        meta["reason"] = "flag_off"
        return (dict(path3_deltas) if path3_deltas is not None else None), meta

    gate = compute_gate_state(asof, market_tip=market_tip if market_tip is not None else asof)
    meta["gate"] = {
        k: gate.get(k)
        for k in (
            "ok",
            "stale",
            "reason",
            "asof",
            "want_trail",
            "trail42_on",
            "path3_active",
            "fill",
        )
    }
    if not gate.get("ok"):
        meta["reason"] = gate.get("reason") or "gate_not_ok"
        # Fail-closed: keep WITHIN deltas (do not invent flatten on stale/missing)
        return (dict(path3_deltas) if path3_deltas is not None else None), meta

    if gate.get("path3_active"):
        meta.update({"applied": True, "fill": "WITHIN", "reason": "path3_within"})
        return (dict(path3_deltas) if path3_deltas is not None else None), meta

    flat = flatten_fin_tel_deltas(pos)
    meta.update(
        {
            "applied": True,
            "fill": "FT_TO_CASH",
            "reason": "path3_off_ft_to_cash",
            "n_flatten_codes": len(flat),
        }
    )
    return flat, meta


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
        "tipsoft_dd_switch_live": bool(on),
        "tipsoft_dd_switch_wire_mode": WIRE_MODE if on else None,
        "tipsoft_dd_switch_policy": POLICY_ID if on else None,
        "tipsoft_dd_switch_stage_a_arm": STAGE_A_ARM_ID if on else None,
        "tipsoft_dd_switch_ballot": ACCEPT_BALLOT if on else None,
        "tipsoft_dd_switch_cutover": (
            "ACCEPT_2026-10-01_TIPSOFT_P3_TRAIL42_L4_DD_SWITCH" if on else None
        ),
        "tipsoft_dd_switch_rollback": (
            "Set LIVE.live_tipsoft_dd_switch=False "
            "(live_config.live_tipsoft_dd_switch); tip Soft Exact T+1 "
            "DD_SWITCH Path3 gate apply off; Path3 WITHIN / Soft FIN/TEL unchanged"
            if on
            else None
        ),
        "tipsoft_dd_want_trail": gate.get("want_trail") if on else None,
        "tipsoft_dd_trail42_on": gate.get("trail42_on") if on else None,
        "tipsoft_dd_path3_active": gate.get("path3_active") if on else None,
        "tipsoft_dd_fill": gate.get("fill") if on else None,
        "tipsoft_dd_asof": gate.get("asof") if on else None,
        "tipsoft_dd_ok": gate.get("ok") if on else None,
        "tipsoft_dd_stale": gate.get("stale") if on else None,
        "tipsoft_dd_reason": gate.get("reason") if on else None,
        "tipsoft_dd_panel_tip": gate.get("panel_tip") if on else None,
        "tipsoft_dd_return_blend_applied": False,
        "tipsoft_dd_switch_path3_within_keep": bool(safety["path3_within_sleeve_keep"]),
        "tipsoft_dd_switch_soft_fin_tel_stay_off": bool(safety["soft_fin_tel_stay_off"]),
        "tipsoft_dd_switch_path4_live": bool(safety["path4_live"]),
        "tipsoft_dd_switch_broker": bool(safety["broker"]),
    }
