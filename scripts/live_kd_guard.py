#!/usr/bin/env python3
"""Shared live KD / E45-stitch guards for dual-paper observe ledgers."""
from __future__ import annotations

from typing import Mapping


def assert_live_kd_aligned(live_kd: Mapping[str, object], *, refuse_if_e45_stitch: bool = True) -> None:
    """Fail closed when research LIVE_KD drifts from live_config / e21 KD_OPT."""
    import e21_forward_pipeline as e21

    for k in live_kd:
        if live_kd[k] != e21.KD_OPT[k]:
            raise SystemExit(f"LIVE_KD[{k}] drift vs e21.KD_OPT ({live_kd[k]!r} != {e21.KD_OPT[k]!r})")
    if refuse_if_e45_stitch and e21.LIVE_E45_STITCH:
        raise SystemExit("Refuse dual-paper observe while LIVE_E45_STITCH is True")
