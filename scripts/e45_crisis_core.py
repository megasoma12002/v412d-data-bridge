#!/usr/bin/env python3
"""E45 Crisis Protection Core — named module (CHALLENGER CANDIDATE).

Why this file exists
--------------------
Governance names E45 as SOFT_FROZEN_CRITICAL, but the repo historically had
only a *role* and a scattered lineage (E1 / E1.1 / E2 / E2.1 / E3), with no
importable ``e45`` package and an unverified MDD≈-13.16% text claim.

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
MODULE_STATUS = "CHALLENGER_CANDIDATE_NOT_PROMOTED"  # Soft-Frozen CRITICAL class; stitch DEFERRED; live auth NO
GOVERNANCE_CLASS_IF_PROMOTED = "SOFT_FROZEN_CRITICAL"
PROMOTION_ALLOWED = False

# Handoff / spec text claim — verification 2026-09-04: NOT FOUND in any research MDD artifact.
CLAIMED_MDD = -0.1316
CLAIMED_MDD_STATUS = "NOT_VERIFIED_HISTORICAL_NARRATIVE"
E45_ARTIFACT_STATUS = "NOT_VERIFIED"
E45_STITCH_STATUS = "DEFERRED"
E45_GOVERNANCE_CLASS = "SOFT_FROZEN_CRITICAL"
E45_LIVE_AUTHORIZATION = "NO"
# Documented research lineage: E38→E43→E44→E45
# Importable code lineage: E1→E1.1→E2→E2.1→E3→E45 wrapper
# Canonical doc: research/e45/E45_OFFICIAL_STATUS.md

# Numbers taken from dated research reports / status JSON (not invented).
VERIFIED_LINEAGE_MDD = {
    "E1_validation_2012_2014": -0.1721,
    "E1_1_validation_2012_2014": -0.1581,
    "E3_validation_2021_2022": -0.1849,
    "V412D_validation_reported": -0.1891,
}

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
    claimed_mdd: float
    claimed_mdd_status: str
    verified_lineage_mdd: dict
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
    verified_lineage_mdd=VERIFIED_LINEAGE_MDD,
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
        "CLAIMED_MDD (-13.16%) = NOT_VERIFIED_HISTORICAL_NARRATIVE (2026-09-04/05). Use dated lineage MDDs (-15.81% / -18.49% / -20.76%). "
        "Prefer VERIFIED_LINEAGE_MDD from dated E1/E1.1/E3/V4.12-D artifacts."
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
) -> dict[str, float]:
    """Scale sleeve target weights by equity exposure; residual stays cash."""
    e = float(np.clip(exposure, 0.0, 1.0))
    return {k: float(v) * e for k, v in sleeve_weights.items()}


def write_status(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest_dict(), indent=2) + "\n")


if __name__ == "__main__":
    print(json.dumps(manifest_dict(), indent=2))
