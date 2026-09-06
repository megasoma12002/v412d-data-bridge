#!/usr/bin/env python3
"""Fail closed on E45 paper hygiene landmines.

Checks scripts/e45*.py for:
  - banned claim labels in new emitters
  - fee / sleeve monkeypatches
  - non-canonical book-ID string literals in emitters

Exit 0 = clean; exit 1 = violations.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

BANNED_CLAIM_PATTERNS = [
    re.compile(r'["\']NOT_VERIFIED["\']'),
    re.compile(r'["\']NOT_VERIFIED_NO_ARTIFACT_MATCH["\']'),
    re.compile(r'["\']E45_NOT_VERIFIED["\']'),
]

MONKEYPATCH_PATTERNS = [
    re.compile(r"setattr\(\s*stack\s*,"),
    re.compile(r"apply_exposure_to_sleeve_weights\s*="),
]

# Non-canonical book IDs that caused join/observe confusion
BAD_BOOK_IDS = [
    re.compile(r'["\']CONST_A\d{2}["\']'),  # use book_id_for_alpha / BLEND_E45_A##
    re.compile(r'["\']REF_BLEND_A\d{2}["\']'),
    re.compile(r'["\']ALL_FULL["\']'),
    re.compile(r'["\']FULL_E45["\']'),
    re.compile(r'["\']CHAL_E45_E3_FULL["\']'),
    re.compile(r'["\']BLEND_A\d{2}["\']'),  # bare BLEND_A05 — prefer BLEND_E45_A05
]

ALLOW_CLAIM_FILES = {
    # Historical verification narrative may still mention the old label in prose
    # but must not emit it as claim_status (checked separately below).
}



# --- Harness adoption / fork ban (O1/O8) ---
SKIP_HARNESS = {"e45_paper_harness.py", "check_e45_paper_hygiene.py"}
FORK_DEFS = re.compile(r"^def (load_market|window_stats|blend)\b", re.M)


def _is_paper_regenerator(name: str) -> bool:
    """Scripts that rebuild research ledgers/screens must use the harness."""
    if name in SKIP_HARNESS:
        return False
    if name.endswith("_paper.py"):
        return True
    if "_ledgers.py" in name or name.endswith("_ledgers.py"):
        return True
    if "_deep_dive" in name:
        return True
    if "_paper_screen" in name or "_grid_fine" in name or "_grid_" in name:
        return True
    return False


def _check_harness_adoption(path: Path, text: str, violations: list[str]) -> None:
    if path.name in SKIP_HARNESS:
        return
    forked = list(FORK_DEFS.finditer(text))
    requires = _is_paper_regenerator(path.name) or bool(forked)
    if not requires:
        return
    if "e45_paper_harness" not in text:
        violations.append(f"{path.relative_to(ROOT)}:1: missing e45_paper_harness import")
    for m in forked:
        line = text.count("\n", 0, m.start()) + 1
        violations.append(
            f"{path.relative_to(ROOT)}:{line}: forked `{m.group(1)}` — use e45_paper_harness"
        )



def main() -> int:
    violations: list[str] = []
    for path in sorted(SCRIPTS.glob("e45*.py")):
        text = path.read_text(encoding="utf-8")
        rel = str(path.relative_to(ROOT))
        _check_harness_adoption(path, text, violations)

        for pat in MONKEYPATCH_PATTERNS:
            for m in pat.finditer(text):
                line = text.count("\n", 0, m.start()) + 1
                violations.append(f"{rel}:{line}: monkeypatch `{pat.pattern}`")

        # claim_status / claim_mdd_status assignments to banned labels
        for m in re.finditer(
            r"(claim_mdd_status|claim_status)\s*[:=]\s*[\"'](NOT_VERIFIED[^\"']*)[\"']",
            text,
        ):
            line = text.count("\n", 0, m.start()) + 1
            violations.append(f"{rel}:{line}: banned claim emitter `{m.group(2)}`")

        for pat in BAD_BOOK_IDS:
            # harness may document banned labels in a tuple — allow BANNED_* blocks
            for m in pat.finditer(text):
                line = text.count("\n", 0, m.start()) + 1
                # skip lines that are clearly ban-lists
                line_txt = text.splitlines()[line - 1]
                if "BANNED" in line_txt or "banned" in line_txt.lower():
                    continue
                if path.name == "e45_paper_harness.py" and "BANNED_CLAIM" in text:
                    # still flag bad book IDs in harness if any
                    pass
                if path.name == "check_e45_paper_hygiene.py":
                    continue
                violations.append(f"{rel}:{line}: non-canonical book id `{m.group(0)}`")

    # harness must exist and expose canonical IDs
    harness = SCRIPTS / "e45_paper_harness.py"
    if not harness.exists():
        violations.append("scripts/e45_paper_harness.py: missing")
    else:
        h = harness.read_text(encoding="utf-8")
        for needle in (
            'BOOK_BASE = "BASE_E16_E18_E22_v2s"',
            'BOOK_FULL = "CHAL_E45_E3"',
            'BOOK_BLEND_A25 = "BLEND_E45_A25"',
            "CLAIM_STATUS = e45.CLAIMED_MDD_STATUS",
        ):
            if needle not in h:
                violations.append(f"scripts/e45_paper_harness.py: missing `{needle}`")

    if violations:
        print("E45 paper hygiene FAIL:")
        for v in violations:
            print(f"  - {v}")
        return 1
    print("E45 paper hygiene PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
