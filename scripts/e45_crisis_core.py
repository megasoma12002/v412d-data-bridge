#!/usr/bin/env python3
"""E45 Crisis Protection Core — named module (CHALLENGER CANDIDATE).

Why this file exists
--------------------
Governance names E45 as SOFT_FROZEN_CRITICAL, but the repo historically had
only a *role* and a scattered lineage (E1 / E1.1 / E2 / E2.1 / E3), with no
importable ``e45`` package and an unverified retired handoff MDD narrative.

This module:
  - gives E45 a real, versioned Python surface
  - packages lineage controllers without editing E1/E11/E2–E3 scripts
  - records claim vs verified artifact status
  - does **NOT** self-promote to SOFT_FROZEN / SOFT_FROZEN_CRITICAL

Promotion still requires the higher E45 challenger bar in FROZEN_GOVERNANCE.md
(separate folder, preserved baseline, crisis stress, MC, explicit approval).

Default operational profile for integration experiments:
  ``E3_VOLTARGET_WINNER`` — the only lineage round that passed its frozen
  Validation gate (still *not* promoted over V4.12-D per research_decision.json).
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd

MODULE_ID = "E45"
MODULE_STATUS = "CHALLENGER_CANDIDATE_NOT_PROMOTED"
GOVERNANCE_CLASS_IF_PROMOTED = "SOFT_FROZEN_CRITICAL"
PROMOTION_ALLOWED = False

# Handoff / spec text claim — formally retired 2026-09-05 (human path A).
# Do NOT cite as verified baseline / Soft-Frozen proof / stitch gate.
from claim_labels import (  # noqa: E402
    EARLY_NON_RIGOROUS_RESEARCH_RESULT,
    RETIRED_HISTORICAL_NARRATIVE,
)

# Numeric handoff claim removed from module surface (residue cleanup 2026-09-06).
# Status + dated lineage only; full narrative lives in the MDD_1316 retirement pack.
RETIRED_MDD_NARRATIVE_DOC = "research/ops/E45_MDD_1316_NARRATIVE_RETIREMENT.md"
RETIRED_MDD_VERIFICATION_DOC = "research/e45/E45_MDD_1316_VERIFICATION.md"
CLAIMED_MDD = None  # intentionally absent — do not reintroduce a float claim
CLAIMED_MDD_STATUS = RETIRED_HISTORICAL_NARRATIVE
CLAIMED_MDD_INTERPRETATION = EARLY_NON_RIGOROUS_RESEARCH_RESULT
# Deprecated alias kept for older readers only:
CLAIMED_MDD_STATUS_LEGACY = "NOT_VERIFIED_NO_ARTIFACT_MATCH"

# Numbers taken from dated research reports / status JSON (not invented).
VERIFIED_LINEAGE_MDD = {
    "E1_validation_2012_2014": -0.1721,
    "E1_1_validation_2012_2014": -0.1581,
    "E3_validation_2021_2022": -0.1849,
    "V412D_validation_reported": -0.1891,
}
# Preferred comparable figure for paper/stitch discussion (dated lineage; not invented).
PRIMARY_COMPARABLE_MDD = VERIFIED_LINEAGE_MDD["E1_1_validation_2012_2014"]  # -15.81%
PRIMARY_COMPARABLE_SOURCE = "E1_1_validation_2012_2014"

FORMAL_STRATEGY_STILL = "V4.12-D"
E3_RESEARCH_DECISION = "validation_pass_but_not_promoted"

# Locked E3 winner from research/v412e2e3/e3_status.json (no retune).
E3_WINNER = {
    "mode": "voltarget",
    "max_cut": 0.5,
    "up_days": 20,
    "target_vol": 0.14,
    "blend": 0.5,
    "rank_buffer": 0,
    "cost_hurdle_mult": 5,
    "min_hold": 42,
    "source": "research/v412e2e3/e3_status.json",
}

# E1-style binary crisis defaults (from e1 crisis_defs family; representative).
E1_BINARY_DEFAULT = {
    "dd_cut": -0.18,
    "vol_cut": 0.30,
    "breadth_cut": 0.30,
    "crisis_scale": 0.50,
    "on_need": 2,
    "off_need": 5,
    "source": "scripts/v412e1_crisis_buffer.py risk_state + crisis_defs family",
}

ProfileName = Literal["PASSTHROUGH", "E1_BINARY", "E3_VOLTARGET_WINNER"]


@dataclass(frozen=True)
class E45Manifest:
    module_id: str
    module_status: str
    promotion_allowed: bool
    claimed_mdd: float | None
    claimed_mdd_status: str
    claimed_mdd_interpretation: str
    verified_lineage_mdd: dict
    primary_comparable_mdd: float
    primary_comparable_source: str
    formal_strategy_still: str
    e3_research_decision: str
    default_profile: str
    lineage_scripts: tuple[str, ...]
    note: str


MANIFEST = E45Manifest(
    module_id=MODULE_ID,
    module_status=MODULE_STATUS,
    promotion_allowed=PROMOTION_ALLOWED,
    claimed_mdd=CLAIMED_MDD,
    claimed_mdd_status=CLAIMED_MDD_STATUS,
    claimed_mdd_interpretation=CLAIMED_MDD_INTERPRETATION,
    verified_lineage_mdd=VERIFIED_LINEAGE_MDD,
    primary_comparable_mdd=PRIMARY_COMPARABLE_MDD,
    primary_comparable_source=PRIMARY_COMPARABLE_SOURCE,
    formal_strategy_still=FORMAL_STRATEGY_STILL,
    e3_research_decision=E3_RESEARCH_DECISION,
    default_profile="E3_VOLTARGET_WINNER",
    lineage_scripts=(
        "scripts/v412e1_crisis_buffer.py",
        "scripts/v412e11_graduated_crisis.py",
        "scripts/v412e2_e3_three_rounds.py",
    ),
    note=(
        "Named E45 surface for integration. Not an in-place freeze. "
        "retired handoff MDD narrative RETIRED_HISTORICAL_NARRATIVE (human 2026-09-05 path A). "
        "Use VERIFIED_LINEAGE_MDD / PRIMARY_COMPARABLE_MDD only; do not invent a replacement."
    ),
)


def manifest_dict() -> dict:
    d = asdict(MANIFEST)
    d["e3_winner"] = dict(E3_WINNER)
    d["e1_binary_default"] = dict(E1_BINARY_DEFAULT)
    d["governance_class_if_promoted"] = GOVERNANCE_CLASS_IF_PROMOTED
    return d


def _hysteresis(raw: pd.Series, on_need: int, off_need: int) -> pd.Series:
    state, on_count, off_count = False, 0, 0
    out = []
    for flag in raw.fillna(False).astype(bool):
        if flag:
            on_count += 1
            off_count = 0
            if on_count >= on_need:
                state = True
        else:
            off_count += 1
            on_count = 0
            if off_count >= off_need:
                state = False
        out.append(state)
    return pd.Series(out, index=raw.index, name="crisis")


def risk_features_from_closes(close: pd.DataFrame) -> pd.DataFrame:
    """Causal EW risk features on a wide close panel (columns = instruments).

    Mirrors v412e1_crisis_buffer.risk_state / e2 raw_risk_features math, without
    depending on the full V4.12-D router universe.
    """
    close = close.sort_index().ffill()
    ret = close.pct_change(fill_method=None)
    ew = (1 + ret.mean(axis=1, skipna=True).fillna(0)).cumprod()
    dd120 = ew / ew.rolling(120, min_periods=60).max() - 1
    vol20 = ret.mean(axis=1, skipna=True).rolling(20).std() * np.sqrt(252)
    breadth = (close > close.ewm(span=60, adjust=False).mean()).mean(axis=1)
    dd_risk = np.clip((-dd120 - 0.03) / 0.27, 0, 1)
    vol_risk = np.clip((vol20 - 0.16) / 0.24, 0, 1)
    breadth_risk = np.clip((0.60 - breadth) / 0.50, 0, 1)
    return pd.DataFrame(
        {
            "ew_raw_index": ew,
            "dd120": dd120,
            "vol20": vol20,
            "breadth60": breadth,
            "dd_risk": dd_risk,
            "vol_risk": vol_risk,
            "breadth_risk": breadth_risk,
        },
        index=close.index,
    )


def binary_crisis_flag(
    risk: pd.DataFrame,
    dd_cut: float = E1_BINARY_DEFAULT["dd_cut"],
    vol_cut: float = E1_BINARY_DEFAULT["vol_cut"],
    breadth_cut: float = E1_BINARY_DEFAULT["breadth_cut"],
    on_need: int = E1_BINARY_DEFAULT["on_need"],
    off_need: int = E1_BINARY_DEFAULT["off_need"],
) -> pd.Series:
    votes = (
        (risk["dd120"] <= dd_cut).astype(int)
        + (risk["vol20"] >= vol_cut).astype(int)
        + (risk["breadth60"] <= breadth_cut).astype(int)
    )
    raw = votes >= 2
    return _hysteresis(raw, on_need, off_need)


def _stateful_weekly(desired: pd.Series, up_days: int) -> pd.Series:
    """Fast down / slow up weekly exposure (from v412e2_e3_three_rounds)."""
    cur = 1.0
    out = []
    for i, x in enumerate(desired.fillna(1.0)):
        if i % 5 == 0:
            if x < cur:
                cur = float(x)
            else:
                cur = min(float(x), cur + (1 - cur) / max(up_days, 1))
        out.append(cur)
    return pd.Series(out, index=desired.index, name="exposure")


def exposure_e3_voltarget(
    risk: pd.DataFrame,
    max_cut: float = E3_WINNER["max_cut"],
    up_days: int = E3_WINNER["up_days"],
    target_vol: float = E3_WINNER["target_vol"],
    blend: float = E3_WINNER["blend"],
) -> pd.Series:
    avg = 0.4 * risk["dd_risk"] + 0.3 * risk["vol_risk"] + 0.3 * risk["breadth_risk"]
    vol_exp = (target_vol / risk["vol20"].replace(0, np.nan)).clip(0.2, 1).fillna(1)
    continuous = 1 - max_cut * avg
    desired = blend * continuous + (1 - blend) * vol_exp
    return _stateful_weekly(desired.clip(1 - max_cut, 1), up_days)


def exposure_e1_binary(
    risk: pd.DataFrame,
    crisis_scale: float = E1_BINARY_DEFAULT["crisis_scale"],
    **crisis_kwargs,
) -> pd.Series:
    crisis = binary_crisis_flag(risk, **crisis_kwargs)
    return pd.Series(
        np.where(crisis, float(crisis_scale), 1.0),
        index=risk.index,
        name="exposure",
    )


def compute_exposure(
    close: pd.DataFrame,
    profile: ProfileName = "E3_VOLTARGET_WINNER",
) -> pd.DataFrame:
    """Return risk features + exposure for the requested profile.

    ``close``: DatetimeIndex × instrument columns (no TAIEX required; include
    whatever equity universe the host book uses).
    """
    risk = risk_features_from_closes(close)
    if profile == "PASSTHROUGH":
        exp = pd.Series(1.0, index=risk.index, name="exposure")
    elif profile == "E1_BINARY":
        exp = exposure_e1_binary(risk)
    elif profile == "E3_VOLTARGET_WINNER":
        exp = exposure_e3_voltarget(risk)
    else:
        raise ValueError(f"unknown E45 profile: {profile}")
    out = risk.copy()
    out["exposure"] = exp
    out["profile"] = profile
    return out


def apply_exposure_to_sleeve_weights(
    sleeve_weights: dict[str, float],
    exposure: float,
    *,
    sleeve_names: tuple[str, ...] | None = None,
) -> dict[str, float]:
    """Scale sleeve target weights by equity exposure; residual stays cash.

    If ``sleeve_names`` is set, only those sleeves are scaled (paper sleeve-local
    overlays). Otherwise every sleeve is scaled (default whole-book E45).
    """
    e = float(np.clip(exposure, 0.0, 1.0))
    if sleeve_names is None:
        return {k: float(v) * e for k, v in sleeve_weights.items()}
    out = {k: float(v) for k, v in sleeve_weights.items()}
    for k in sleeve_names:
        if k in out:
            out[k] = out[k] * e
    return out


def apply_m2_def_relocate(
    sleeve_weights: dict[str, float],
    intensity: float,
    cut: float,
    mode: str,
) -> dict[str, float]:
    """M2 DEF actuator (frozen v0+v1): shrink / relocate-to-TEL|true-DEF / hybrid.

    ``intensity`` is lag-1 state intensity in [0,1]. ``cut`` is c in {0.5,0.75}.
    v0 modes: research/e45/E45_M2_DEF_SLEEVE_V0_FROZEN.md
    v1 modes: research/e45/E45_M2_DEF_SLEEVE_V1_FROZEN.md (adds DEF sleeve weight).
    """
    u = float(np.clip(float(cut) * float(intensity), 0.0, 1.0))
    w_fin = float(sleeve_weights.get("Financial", 0.0))
    w_tel = float(sleeve_weights.get("Telecom", 0.0))
    w_0050 = float(sleeve_weights.get("0050", 0.0))
    m = str(mode).upper()
    if m == "SHRINK":
        scale = 1.0 - u
        return {
            "Financial": w_fin * scale,
            "Telecom": w_tel * scale,
            "0050": w_0050 * scale,
            "DEF": 0.0,
        }
    if m == "RELOC_TEL":
        move_fin = w_fin * u
        move_0050 = w_0050 * u
        return {
            "Financial": w_fin - move_fin,
            "Telecom": w_tel + move_fin + move_0050,
            "0050": w_0050 - move_0050,
            "DEF": 0.0,
        }
    if m == "HYBRID_TEL":
        half = 0.5 * u
        w_fin_s = w_fin * (1.0 - half)
        w_tel_s = w_tel * (1.0 - half)
        w_0050_s = w_0050 * (1.0 - half)
        move_fin = w_fin * half
        move_0050 = w_0050 * half
        return {
            "Financial": w_fin_s - move_fin,
            "Telecom": w_tel_s + move_fin + move_0050,
            "0050": w_0050_s - move_0050,
            "DEF": 0.0,
        }
    if m in {"RELOC_719B", "RELOC_BIL_FX", "RELOC_TWD_720B"}:
        move_fin = w_fin * u
        move_0050 = w_0050 * u
        return {
            "Financial": w_fin - move_fin,
            "Telecom": w_tel,
            "0050": w_0050 - move_0050,
            "DEF": move_fin + move_0050,
        }
    if m == "HYBRID_719B":
        half = 0.5 * u
        w_fin_s = w_fin * (1.0 - half)
        w_tel_s = w_tel * (1.0 - half)
        w_0050_s = w_0050 * (1.0 - half)
        move_fin = w_fin * half
        move_0050 = w_0050 * half
        return {
            "Financial": w_fin_s - move_fin,
            "Telecom": w_tel_s,
            "0050": w_0050_s - move_0050,
            "DEF": move_fin + move_0050,
        }
    raise ValueError(f"unknown M2 mode: {mode}")


def build_m2_sleeve_schedule(
    base_targets: pd.DataFrame,
    intensity_lag1: pd.Series,
    cut: float,
    mode: str,
) -> pd.DataFrame:
    """Daily Soft-Frozen sleeve schedule under frozen M2 relocate rule."""
    rows = []
    idx = []
    for dt, row in base_targets.iterrows():
        if dt not in intensity_lag1.index:
            continue
        out = apply_m2_def_relocate(
            {
                "Financial": float(row["Financial"]),
                "Telecom": float(row["Telecom"]),
                "0050": float(row["0050"]),
            },
            float(intensity_lag1.loc[dt]),
            cut,
            mode,
        )
        rows.append(out)
        idx.append(dt)
    return pd.DataFrame(rows, index=pd.DatetimeIndex(idx))


# --- M3 three-state machine (frozen v0) ---------------------------------
M3_ENTER_SLOW = 0.45
M3_EXIT_SLOW = 0.32
M3_ENTER_CRASH = 0.70
M3_EXIT_CRASH = 0.52
M3_EXIT_CRASH_TO_NORMAL = 0.30
M3_CONFIRM_SLOW = 5
M3_CONFIRM_CRASH = 3
M3_CONFIRM_EXIT = 5
M3_ACTION_U = {"NORMAL": 0.0, "SLOW_BEAR": 0.40, "CRASH": 0.75}


def build_m3_state_series(intensity: pd.Series) -> pd.Series:
    """Frozen M3 hysteresis state path from M1 intensity s_t (close-t)."""
    s = intensity.astype(float).copy()
    states: list[str] = []
    state = "NORMAL"
    up_slow = up_crash = down_slow = down_crash = down_crash_norm = 0
    for v in s.tolist():
        x = float(v) if v == v else 0.0  # NaN -> 0
        if state == "NORMAL":
            up_slow = up_slow + 1 if x >= M3_ENTER_SLOW else 0
            up_crash = up_crash + 1 if x >= M3_ENTER_CRASH else 0
            down_slow = down_crash = down_crash_norm = 0
            if up_crash >= M3_CONFIRM_CRASH:
                state = "CRASH"
                up_slow = up_crash = 0
            elif up_slow >= M3_CONFIRM_SLOW:
                state = "SLOW_BEAR"
                up_slow = up_crash = 0
        elif state == "SLOW_BEAR":
            up_crash = up_crash + 1 if x >= M3_ENTER_CRASH else 0
            down_slow = down_slow + 1 if x <= M3_EXIT_SLOW else 0
            up_slow = down_crash = down_crash_norm = 0
            if up_crash >= M3_CONFIRM_CRASH:
                state = "CRASH"
                up_crash = down_slow = 0
            elif down_slow >= M3_CONFIRM_EXIT:
                state = "NORMAL"
                up_crash = down_slow = 0
        else:  # CRASH
            down_crash = down_crash + 1 if x <= M3_EXIT_CRASH else 0
            down_crash_norm = down_crash_norm + 1 if x <= M3_EXIT_CRASH_TO_NORMAL else 0
            up_slow = up_crash = down_slow = 0
            if down_crash_norm >= M3_CONFIRM_EXIT:
                state = "NORMAL"
                down_crash = down_crash_norm = 0
            elif down_crash >= M3_CONFIRM_EXIT:
                state = "SLOW_BEAR"
                down_crash = down_crash_norm = 0
        states.append(state)
    return pd.Series(states, index=s.index, name="m3_state")


def apply_m3_state_action(
    sleeve_weights: dict[str, float],
    state: str,
) -> dict[str, float]:
    """Apply frozen per-state RELOC_TEL action (u from M3_ACTION_U)."""
    st = str(state).upper()
    u = float(M3_ACTION_U.get(st, 0.0))
    if u <= 0.0 or st == "NORMAL":
        return {
            "Financial": float(sleeve_weights.get("Financial", 0.0)),
            "Telecom": float(sleeve_weights.get("Telecom", 0.0)),
            "0050": float(sleeve_weights.get("0050", 0.0)),
        }
    # intensity=1, cut=u => relocate fraction u (matches frozen action table)
    return apply_m2_def_relocate(sleeve_weights, intensity=1.0, cut=u, mode="RELOC_TEL")


def build_m3_sleeve_schedule(
    base_targets: pd.DataFrame,
    intensity: pd.Series,
) -> tuple[pd.DataFrame, pd.Series]:
    """Build Exact-T+1 M3 sleeve schedule from close-t states (action uses state_{t-1})."""
    state_t = build_m3_state_series(intensity.reindex(base_targets.index).fillna(0.0))
    state_lag = state_t.shift(1).fillna("NORMAL")
    rows = []
    idx = []
    for dt, row in base_targets.iterrows():
        out = apply_m3_state_action(
            {
                "Financial": float(row["Financial"]),
                "Telecom": float(row["Telecom"]),
                "0050": float(row["0050"]),
            },
            str(state_lag.loc[dt]),
        )
        rows.append(out)
        idx.append(dt)
    sched = pd.DataFrame(rows, index=pd.DatetimeIndex(idx))
    return sched, state_t


def write_status(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest_dict(), indent=2) + "\n")


if __name__ == "__main__":
    print(json.dumps(manifest_dict(), indent=2))
