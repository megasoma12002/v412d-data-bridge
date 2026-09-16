#!/usr/bin/env python3
"""Live Soft-Frozen wiring SSOT — RESEARCH/OPS config object.

Cutover still requires a human ACCEPT PR that edits these constants.
Soft-Frozen FIN clip itself lives in ``e16_soft_frozen_base`` (unchanged here).

Imported by ``e21_forward_pipeline`` (re-exported for backward compat) and
research guards that check ``KD_OPT`` / ``LIVE_E45_STITCH`` drift.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import e22_dividend_accounting as e22div
from portfolio_capital import DEFAULT_CAPITAL
from within_sleeve_alloc import FIN_PRE_EXDIV_KD

# Live FIN within-sleeve — human ACCEPT 2026-09-09: KD_OPT cutover
KD_OPT: dict[str, Any] = {
    "id": "KD_APR15_MAY15_Klt30_T15",
    "season_start": (4, 15),
    "season_end": (5, 15),
    "k_thresh": 30.0,
    "pre_days": 15,
    "active_score": 1.5,
}


@dataclass(frozen=True)
class LiveConfig:
    """Canonical live feature flags + books/capital defaults."""

    capital: float = DEFAULT_CAPITAL
    e22_books_version: str = e22div.DEFAULT_BOOKS_VERSION  # E22_v2s_tw_effex
    dividends_path: Path = field(
        default_factory=lambda: Path("data/dividend_events/e22_dividend_events.csv")
    )
    state_dir: Path = field(default_factory=lambda: Path("forward/e21"))
    market_path: Path = field(default_factory=lambda: Path("forward/e21/live_market.csv"))

    # Soft-Frozen FIN clip — Class D ACCEPT 2026-09-09: FINBAND → [0.60, 0.90]
    # (bounds owned by e16_soft_frozen_base; this only records within-sleeve policy)
    live_fin_within_sleeve: str = FIN_PRE_EXDIV_KD
    kd_opt: dict[str, Any] = field(default_factory=lambda: dict(KD_OPT))

    # E45 live stitch — ROLLBACK 2026-09-09: DROP_E45_A05
    live_e45_stitch: bool = False
    live_e45_book: str | None = None
    live_e45_profile: dict | None = None
    live_e45_blend_alpha: float | None = None

    # Live DH_dd06 + FUSE_ADDITIVE — human ACCEPT 2026-09-13
    live_fuse_additive: bool = True
    live_dh_exposure: bool = True
    live_dh_id: str = "DH_dd06_vz1p0"
    live_cutover_ballot: str = "ACCEPT Live cutover: DH_dd06 + FUSE_ADDITIVE"

    # Fill backend — default paper Exact T+1. Broker / dry_run via CLI or E21_FILL_PORT.
    # True broker routing requires a separate human ACCEPT PR (not this default).
    fill_port: str = "paper"


# Module-level singleton used by the live pipeline (edit + ACCEPT PR to cut over).
LIVE = LiveConfig()

# Backward-compat aliases (same names historically on e21_forward_pipeline).
LIVE_FIN_WITHIN_SLEEVE = LIVE.live_fin_within_sleeve
LIVE_E45_STITCH = LIVE.live_e45_stitch
LIVE_E45_BOOK = LIVE.live_e45_book
LIVE_E45_PROFILE = LIVE.live_e45_profile
LIVE_E45_BLEND_ALPHA = LIVE.live_e45_blend_alpha
LIVE_FUSE_ADDITIVE = LIVE.live_fuse_additive
LIVE_DH_EXPOSURE = LIVE.live_dh_exposure
LIVE_DH_ID = LIVE.live_dh_id
LIVE_CUTOVER_BALLOT = LIVE.live_cutover_ballot
E22_BOOKS_VERSION = LIVE.e22_books_version
DIV_PATH = LIVE.dividends_path
CAPITAL = LIVE.capital
