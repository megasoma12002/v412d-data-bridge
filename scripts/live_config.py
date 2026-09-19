#!/usr/bin/env python3
"""Live Soft-Frozen wiring SSOT — RESEARCH/OPS config object.

Cutover still requires a human ACCEPT PR that edits these constants.
Soft-Frozen FIN clip itself lives in ``e16_soft_frozen_base`` (unchanged here).

Imported by ``e21_forward_pipeline`` (re-exported for backward compat) and
research guards that check ``KD_OPT`` / E45 A05 DROP stamp.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

import e22_dividend_accounting as e22div
from portfolio_capital import DEFAULT_CAPITAL
from within_sleeve_alloc import FIN_PRE_EXDIV_KD

# Live FIN within-sleeve — human ACCEPT 2026-09-09: KD_OPT cutover
# Frozen MappingProxyType: runtime mutation cannot bypass ACCEPT narrative.
_KD_OPT_MUTABLE: dict[str, Any] = {
    "id": "KD_APR15_MAY15_Klt30_T15",
    "season_start": (4, 15),
    "season_end": (5, 15),
    "k_thresh": 30.0,
    "pre_days": 15,
    "active_score": 1.5,
}
KD_OPT: Mapping[str, Any] = MappingProxyType(_KD_OPT_MUTABLE)

# 民營 native KD — ACCEPT 2026-09-19 priv live cutover.
_PRIV_KD_MUTABLE: dict[str, Any] = {
    "id": "PRIV_KD_MAY_Klt25_T15",
    "season_start": (5, 1),
    "season_end": (5, 31),
    "k_thresh": 25.0,
    "pre_days": 15,
    "active_score": 1.5,
}
PRIV_KD: Mapping[str, Any] = MappingProxyType(_PRIV_KD_MUTABLE)

# E45 A05 live stitch — DROPPED 2026-09-09. No LiveConfig flip knob.
E45_STITCH_ROLLBACK = "ACCEPT_2026-09-09_DROP_E45_A05"
E45_A05_STITCH_DROPPED = True
LIVE_E45_STITCH = False  # frozen constant for landmine / research guards
LIVE_E45_BOOK = None
LIVE_E45_PROFILE = None
LIVE_E45_BLEND_ALPHA = None

CUTOVER_BUNDLE_BALLOT = (
    "ACCEPT_2026-09-19_CUTOVER_BUNDLE_L4_FIN50_BLEND_SOFT_SLEEVE_PRIV_TAX_BROKER"
)


@dataclass(frozen=True)
class LiveConfig:
    """Canonical live feature flags + books/capital defaults."""

    capital: float = DEFAULT_CAPITAL
    # Stage-B tax ACCEPT 2026-09-19 — recv_pay + flat 10% withhold.
    e22_books_version: str = e22div.DEFAULT_BOOKS_VERSION
    dividends_path: Path = field(
        default_factory=lambda: Path("data/dividend_events/e22_dividend_events.csv")
    )
    state_dir: Path = field(default_factory=lambda: Path("forward/e21"))
    market_path: Path = field(default_factory=lambda: Path("forward/e21/live_market.csv"))

    # Soft-Frozen FIN clip — Class D ACCEPT 2026-09-09: FINBAND → [0.60, 0.90]
    # (bounds owned by e16_soft_frozen_base; this only records within-sleeve policy)
    live_fin_within_sleeve: str = FIN_PRE_EXDIV_KD
    kd_opt: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType(dict(KD_OPT)))

    # Tip books align ACCEPT 2026-09-19 — next forward may advance tip to DEFAULT.
    tip_books_align_ballot: str = "ACCEPT_2026-09-19_TIP_BOOKS_ALIGN_V3"

    # Live DH_dd06 + FUSE_ADDITIVE — human ACCEPT 2026-09-13
    # Soft observe + Sleeve observe ACCEPTED 2026-09-19 as carried by FUSE (no independent wire).
    live_fuse_additive: bool = True
    live_dh_exposure: bool = True
    live_dh_id: str = "DH_dd06_vz1p0"
    live_cutover_ballot: str = "ACCEPT Live cutover: DH_dd06 + FUSE_ADDITIVE"
    fuse_carries_soft_observe: bool = True
    fuse_carries_sleeve_observe: bool = True

    # BLEND_025 + L4 + FIN50-as-component — ACCEPT 2026-09-19 cutover bundle.
    live_blend025: bool = True
    live_l4_dd_path: bool = True
    cutover_bundle_ballot: str = CUTOVER_BUNDLE_BALLOT

    # 民營 native — ACCEPT 2026-09-19.
    live_fin_priv_native: bool = True
    priv_kd: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType(dict(PRIV_KD)))

    # Fill backend — default paper Exact T+1. Broker / dry_run via CLI or E21_FILL_PORT.
    # True broker live write requires ALL of:
    #   broker_live_write_accepted=True (ACCEPT PR), E21_BROKER_WRITE_LIVE=1, and broker_safety gates.
    fill_port: str = "paper"
    broker_live_write_accepted: bool = True  # ACCEPT 2026-09-19 broker live-write


# Module-level singleton used by the live pipeline (edit + ACCEPT PR to cut over).
LIVE = LiveConfig()

# Backward-compat aliases (same names historically on e21_forward_pipeline).
LIVE_FIN_WITHIN_SLEEVE = LIVE.live_fin_within_sleeve
LIVE_FUSE_ADDITIVE = LIVE.live_fuse_additive
LIVE_DH_EXPOSURE = LIVE.live_dh_exposure
LIVE_DH_ID = LIVE.live_dh_id
LIVE_CUTOVER_BALLOT = LIVE.live_cutover_ballot
LIVE_BLEND025 = LIVE.live_blend025
LIVE_L4_DD_PATH = LIVE.live_l4_dd_path
LIVE_FIN_PRIV_NATIVE = LIVE.live_fin_priv_native
E22_BOOKS_VERSION = LIVE.e22_books_version
DIV_PATH = LIVE.dividends_path
CAPITAL = LIVE.capital
TIP_BOOKS_ALIGN_BALLOT = LIVE.tip_books_align_ballot
CUTOVER_BUNDLE_BALLOT_LIVE = LIVE.cutover_bundle_ballot
