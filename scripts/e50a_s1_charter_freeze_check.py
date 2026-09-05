#!/usr/bin/env python3
"""Validate Track B charter gates JSON is frozen and coherent (no screening)."""
from __future__ import annotations

import json
from pathlib import Path

GATES = Path("research/e50a/E50A_S1_STRESS_ENGINE_GATES.json")
CHARTER = Path("research/e50a/E50A_S1_STRESS_ENGINE_CHARTER.md")


def main() -> None:
    assert GATES.exists() and CHARTER.exists()
    g = json.loads(GATES.read_text())
    assert g["version_id"] == "E50-A3-S1"
    assert g["status"] == "CHARTER_FROZEN_FOR_SCREENING"
    assert g["live_wire"] is False
    assert "TECH2_PRICE8_F1_remix_as_stress_engine" in g["forbidden"]
    assert set(g["allowed_families"]) == {"S1-QRES", "S1-DEFRES", "S1-VALRES"}
    assert 42 in g["portfolio_shell_grid"]["rebalance_every"]
    assert 5 not in g["portfolio_shell_grid"]["rebalance_every"]
    out = Path("repro/e50a-dual-track/track_b_s1_charter/charter_freeze_check.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "ok": True,
        "version_id": g["version_id"],
        "allowed_families": g["allowed_families"],
        "screening_started": False,
        "note": "Charter frozen; screening is a follow-on PR after this lands.",
    }
    out.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
