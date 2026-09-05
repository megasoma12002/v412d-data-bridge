#!/usr/bin/env python3
"""Canonical claim / status vocabulary (shared by agents & scripts).

Prefer these labels over ad-hoc aliases like NOT_FOUND / UNVERIFIED_TEXT_ONLY.
"""
from __future__ import annotations

# Historical narrative numbers (e.g. retired E45 −13.16%)
NOT_VERIFIED_HISTORICAL_NARRATIVE = "NOT_VERIFIED_HISTORICAL_NARRATIVE"
RETIRED_HISTORICAL_NARRATIVE = "RETIRED_HISTORICAL_NARRATIVE"
EARLY_NON_RIGOROUS_RESEARCH_RESULT = "EARLY_NON_RIGOROUS_RESEARCH_RESULT"

# Artifact / module status
NOT_VERIFIED = "NOT_VERIFIED"
DEFERRED = "DEFERRED"
SOFT_FROZEN_CRITICAL = "SOFT_FROZEN_CRITICAL"
LIVE_AUTH_NO = "NO"

DEPRECATED_CLAIM_ALIASES = {
    "NOT_FOUND",
    "NOT_FOUND_IN_ARTIFACTS",
    "NOT_VERIFIED_NO_ARTIFACT_MATCH",
    "UNVERIFIED",
    "UNVERIFIED_TEXT_ONLY",
    "E45_NOT_VERIFIED",
    "FAIL_NOT_VERIFIED",
}


def normalize_claim_label(label: str) -> str:
    if label in DEPRECATED_CLAIM_ALIASES or label.startswith("NOT_FOUND"):
        return NOT_VERIFIED_HISTORICAL_NARRATIVE
    return label
