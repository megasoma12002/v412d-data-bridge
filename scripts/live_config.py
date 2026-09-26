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

# E45 A05 live stitch — DROPPED 2026-09-09. No LiveConfig flip knob.
E45_STITCH_ROLLBACK = "ACCEPT_2026-09-09_DROP_E45_A05"
E45_A05_STITCH_DROPPED = True
LIVE_E45_STITCH = False  # frozen constant for landmine / research guards
LIVE_E45_BOOK = None
LIVE_E45_PROFILE = None
LIVE_E45_BLEND_ALPHA = None


@dataclass(frozen=True)
class LiveConfig:
    """Canonical live feature flags + books/capital defaults."""

    capital: float = DEFAULT_CAPITAL
    e22_books_version: str = e22div.DEFAULT_BOOKS_VERSION  # E22_v3_recv_pay_effdelay
    dividends_path: Path = field(
        default_factory=lambda: Path("data/dividend_events/e22_dividend_events.csv")
    )
    state_dir: Path = field(default_factory=lambda: Path("forward/e21"))
    market_path: Path = field(default_factory=lambda: Path("forward/e21/live_market.csv"))

    # Soft-Frozen clips — Class D ACCEPT 2026-09-25: β densify
    # F[0.60,0.80] T[0.03,0.35] E[0.00,0.50] (bounds in e16_soft_frozen_base)
    # Prior FINBAND ACCEPT 2026-09-09: FIN [0.60, 0.90] / ETF [0.00, 0.35]
    live_fin_within_sleeve: str = FIN_PRE_EXDIV_KD
    kd_opt: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType(dict(KD_OPT)))

    # Tip books align ACCEPT 2026-09-19 — next forward may advance tip to DEFAULT.
    tip_books_align_ballot: str = "ACCEPT_2026-09-19_TIP_BOOKS_ALIGN_V3"

    # Live FUSE_ADDITIVE KEEP + COOL_c8 replace DH — human ACCEPT 2026-09-25
    # Prior: DH_dd06 + FUSE ACCEPT 2026-09-13 (DH retired forward-only by this ballot).
    live_fuse_additive: bool = True
    live_dh_exposure: bool = False  # replaced by COOL — do not re-enable without new ballot
    live_dh_id: str = "DH_dd06_vz1p0"
    live_cool_exposure: bool = True
    live_cool_id: str = "COOL_c8_f50_d21"
    live_cutover_ballot: str = (
        "ACCEPT Live cutover: COOL_c8_f50_d21 (replace DH, keep FUSE)"
    )

    # Class D FinPriv V7 Bull+Side F05 carve-out — human ACCEPT 2026-09-25/26
    # Soft-Frozen 3-sleeve router KEEP (公股 features); within-Financial dual carve only.
    # Gate REG_BULL_SIDE · priv_frac=0.05 · PRIV_KD_MAY; fail-closed on stale PRIV px.
    live_fin_priv_v7_f05: bool = True
    live_fin_priv_ballot: str = "ACCEPT Class D: FinPriv V7 F05"

    # FUSE Soft sell amp under COOL — human ACCEPT 2026-09-26 live cutover
    # Prior near-flat paper: SELL_a75 floor +0.15; live raises sell boost 0.50→0.75.
    # Coexists with COOL_c8 + FUSE_ADDITIVE (does not replace defense).
    live_fuse_soft_sell_boost: float = 0.75  # SELL_a75
    live_fuse_soft_sell_ballot: str = (
        "ACCEPT Live cutover: SELL_a75 under COOL (keep FUSE+COOL)"
    )

    # CONF_RET3_A10_H5 × 00631L short-assist — human ACCEPT 2026-09-26
    # COOL exit + 0050 RET3>0 · α=0.10 · H=5 · OFF=00631L (forward-only Class D membership).
    # Soft-Frozen / FUSE / COOL / SELL_a75 / FinPriv V7 KEEP; broker PREP-only.
    live_conf_ret3_631l: bool = True
    live_conf_ret3_ballot: str = (
        "ACCEPT Live cutover: CONF_RET3_A10_H5 (00631L short-assist under COOL)"
    )

    # Fill backend — default paper Exact T+1. Broker / dry_run via CLI or E21_FILL_PORT.
    # True broker live write requires ALL of:
    #   broker_live_write_accepted=True (ACCEPT PR), E21_BROKER_WRITE_LIVE=1, and broker_safety gates.
    fill_port: str = "paper"
    broker_live_write_accepted: bool = False  # Soft-Frozen KEEP until ACCEPT PR


# Module-level singleton used by the live pipeline (edit + ACCEPT PR to cut over).
LIVE = LiveConfig()

# Backward-compat aliases (same names historically on e21_forward_pipeline).
LIVE_FIN_WITHIN_SLEEVE = LIVE.live_fin_within_sleeve
LIVE_FUSE_ADDITIVE = LIVE.live_fuse_additive
LIVE_DH_EXPOSURE = LIVE.live_dh_exposure
LIVE_DH_ID = LIVE.live_dh_id
LIVE_COOL_EXPOSURE = LIVE.live_cool_exposure
LIVE_COOL_ID = LIVE.live_cool_id
LIVE_CUTOVER_BALLOT = LIVE.live_cutover_ballot
LIVE_FIN_PRIV_V7_F05 = LIVE.live_fin_priv_v7_f05
LIVE_FIN_PRIV_BALLOT = LIVE.live_fin_priv_ballot
LIVE_FUSE_SOFT_SELL_BOOST = LIVE.live_fuse_soft_sell_boost
LIVE_FUSE_SOFT_SELL_BALLOT = LIVE.live_fuse_soft_sell_ballot
LIVE_CONF_RET3_631L = LIVE.live_conf_ret3_631l
LIVE_CONF_RET3_BALLOT = LIVE.live_conf_ret3_ballot
E22_BOOKS_VERSION = LIVE.e22_books_version
DIV_PATH = LIVE.dividends_path
CAPITAL = LIVE.capital
TIP_BOOKS_ALIGN_BALLOT = LIVE.tip_books_align_ballot
