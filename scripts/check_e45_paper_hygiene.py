#!/usr/bin/env python3
"""Fail closed on E45 paper hygiene landmines.

Checks scripts/e45*.py for:
  - banned claim labels in new emitters
  - fee / sleeve monkeypatches
  - non-canonical book-ID string literals in emitters
  - dual book/window/harness aliases in the same paper regenerator

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
    # Multi-item research batches (same landmine surface as paper regenerators)
    if "research_batch" in name or name.endswith("_batch.py"):
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




# Canonical naming forks banned in e45 paper scripts (use harness names).
NAMING_FORK_BANS = (
    (r"^E45_PROFILE\s*=", "Use E45_PROFILE_DEFAULT from e45_paper_harness (do not fork E45_PROFILE)"),
    (r"\bmdd_help_pp\b", "Use mdd_improve_pp (harness deltas_vs_base key)"),
    (
        r"\bmdd_help_(?:2020|covid_year|non2020_positive|non_covid_positive|threshold)_pp\b",
        "Use mdd_improve_* keys (not mdd_help_*)",
    ),
    (r"Observe lock `FIN_ONLY_A10`", "Observe OPERATING id is SLEEVE_FIN_ONLY_A10"),
    (r"\bsealed_2023_latest\b", "Use sealed_2023_plus (WINDOWS_STANDARD)"),
)


def _id_token_re(token: str) -> re.Pattern[str]:
    """Match an identifier/book/window token without prefix/suffix glue (v2s vs v2)."""
    return re.compile(rf"(?<![A-Za-z0-9_]){re.escape(token)}(?![A-Za-z0-9_])")


# Dual-alias families: a paper regenerator may use at most ONE spelling per family.
# Canonical token is first. Hitting canonical + any alias (or two aliases) = FAIL.
# This blocks the agent landmine of mixing Soft-Frozen tip names with invented forks
# in the same script mid-edit.
WINDOW_DUAL_ALIAS_FAMILIES: tuple[tuple[str, ...], ...] = (
    (
        "heldout_2019_plus",
        "held_out_2019_plus",
        "holdout_2019_plus",
        "heldout_2019",
        "held_out_2019",
        "oos_2019_plus",
    ),
    (
        "sealed_2023_plus",
        "sealed_2023_latest",
        "sealed_2023",
        "sealed_2023_plus_latest",
        "seal_2023_plus",
    ),
    (
        "oof_2011_2018",
        "oos_2011_2018",
        "oof_2011_18",
        "train_2011_2018",
    ),
    (
        "validation_2019_2022",
        "val_2019_2022",
        "valid_2019_2022",
        "validation_2019_22",
    ),
)

BOOK_DUAL_ALIAS_FAMILIES: tuple[tuple[str, ...], ...] = (
    (
        "BASE_E16_E18_E22_v2s",
        "BASE_E16_E18_E22",
        "BASE_SOFT_FROZEN",
        "BASE_E16_E18",
        "BASE_E16_E18_E22_V2S",
    ),
    (
        "CHAL_E45_E3",
        "FULL_E45",
        "CHAL_E45_E3_FULL",
        "ALL_FULL",
        "FULL_E45_BOOK",
    ),
    (
        "BLEND_E45_A05",
        "BLEND_A05",
        "CONST_A05",
        "REF_BLEND_A05",
    ),
    (
        "BLEND_E45_A10",
        "BLEND_A10",
        "CONST_A10",
    ),
    (
        "BLEND_E45_A25",
        "BLEND_A25",
        "CONST_A25",
    ),
)

HARNESS_DUAL_ALIAS_FAMILIES: tuple[tuple[str, ...], ...] = (
    (
        "WINDOWS_STANDARD",
        "WINDOWS_STD",
        "WINDOW_STANDARD",
        "STANDARD_WINDOWS",
        "WINDOWS_CANONICAL",
    ),
    (
        "BOOK_BASE",
        "BOOK_BASELINE",
        "BASE_BOOK",
        "BOOK_BASE_ID",
    ),
    (
        "BOOK_FULL",
        "BOOK_CHAL",
        "BOOK_FULL_E45",
        "BOOK_CHALLENGER",
    ),
    (
        "max_drawdown",
        "max_dd",
        "maxdd",
        "max_drawdown_pct",
    ),
)


def _check_dual_alias_families(path: Path, text: str, violations: list[str]) -> None:
    """Fail if a paper regenerator mixes two spellings of the same book/window concept."""
    if path.name in SKIP_HARNESS:
        return
    if not _is_paper_regenerator(path.name):
        return
    rel = str(path.relative_to(ROOT))
    families = (
        ("window", WINDOW_DUAL_ALIAS_FAMILIES),
        ("book", BOOK_DUAL_ALIAS_FAMILIES),
        ("harness", HARNESS_DUAL_ALIAS_FAMILIES),
    )
    for kind, fams in families:
        for family in fams:
            hits: list[str] = []
            first_line: int | None = None
            for tok in family:
                m = _id_token_re(tok).search(text)
                if not m:
                    continue
                line = text.count("\n", 0, m.start()) + 1
                line_txt = text.splitlines()[line - 1]
                # allow ban-list / documentation lines that name aliases on purpose
                if (
                    "DUAL_ALIAS" in line_txt
                    or "NAMING_FORK" in line_txt
                    or "banned" in line_txt.lower()
                    or "alias family" in line_txt.lower()
                ):
                    continue
                hits.append(tok)
                if first_line is None:
                    first_line = line
            # unique while preserving order
            uniq: list[str] = []
            for h in hits:
                if h not in uniq:
                    uniq.append(h)
            if len(uniq) >= 2:
                canon = family[0]
                violations.append(
                    f"{rel}:{first_line}: dual {kind} aliases {uniq} — "
                    f"use only canonical `{canon}` (no second spelling in the same paper script)"
                )

def main() -> int:
    violations: list[str] = []
    for path in sorted(SCRIPTS.glob("e45*.py")):
        text = path.read_text(encoding="utf-8")
        rel = str(path.relative_to(ROOT))
        _check_harness_adoption(path, text, violations)
        _check_dual_alias_families(path, text, violations)

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

        # Canonical naming forks (claim/profile/window/metric dual names)
        if path.name != "check_e45_paper_hygiene.py":
            for pat_s, msg in NAMING_FORK_BANS:
                pat = re.compile(pat_s, re.M)
                for m in pat.finditer(text):
                    line = text.count("\n", 0, m.start()) + 1
                    line_txt = text.splitlines()[line - 1]
                    # allow legacy archive read fallbacks
                    if "sealed_2023_latest" in m.group(0) and (
                        "or" in line_txt and "sealed_2023_plus" in line_txt
                    ):
                        continue
                    if "NAMING_FORK" in line_txt or "banned" in line_txt.lower():
                        continue
                    violations.append(f"{rel}:{line}: naming fork `{m.group(0)}` — {msg}")

    # harness must exist and expose canonical IDs + truthful __all__
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
            "def load_market(",
            "def e45_full_exposure(",
            "def window_stats(",
            "def run_early_stack(",
        ):
            if needle not in h:
                violations.append(f"scripts/e45_paper_harness.py: missing `{needle}`")
        # __all__ must not advertise names the module does not define (agent landmine)
        try:
            ns: dict = {"__file__": str(harness), "__name__": "e45_paper_harness"}
            exec(compile(h, str(harness), "exec"), ns, ns)
            exported = ns.get("__all__")
            if not isinstance(exported, (list, tuple)):
                violations.append("scripts/e45_paper_harness.py: __all__ missing or not a list")
            else:
                for name in exported:
                    if name not in ns:
                        violations.append(
                            f"scripts/e45_paper_harness.py: __all__ lists `{name}` but name is undefined"
                        )
        except Exception as exc:  # noqa: BLE001 — surface as hygiene failure
            violations.append(f"scripts/e45_paper_harness.py: failed __all__ exec check: {exc}")


    # Stale regenerator report JSON still emitting retired book IDs (join landmine)
    ARTIFACT_GLOBS = [
        "repro/e45-alpha-cost-turnover/reports/*.json",
        "repro/e45-crisis-year-attribution/reports/*.json",
        "repro/e45-crisis-triggered-alpha/reports/*.json",
        "repro/e45-blend-alpha-grid-fine/reports/*.json",
        "repro/e45-blend-alpha-screen/reports/*.json",
        "repro/e45-maxcut-mild-profile/reports/*.json",
        "repro/e45-five-research-batch/outputs/*.json",
        "repro/e45-five-research-batch/reports/*.json",
        "repro/e45-sleeve-local/reports/*.json",
        "research/e45/E45_ALPHA_COST_TURNOVER.json",
        "research/e45/E45_CRISIS_YEAR_ATTRIBUTION.json",
        "research/e45/E45_CRISIS_TRIGGERED_ALPHA.json",
        "research/e45/E45_BLEND_ALPHA_GRID_FINE.json",
        "research/e45/E45_BLEND_ALPHA_PAPER_SCREEN.json",
        "research/e45/E45_MAXCUT_MILD_PROFILE.json",
        "research/e45/E45_SLEEVE_LOCAL.json",
        "research/e45/E45_FIVE_RESEARCH_BATCH_SUMMARY.json",
        "research/ops/E45_FIVE_RESEARCH_BATCH_INTEGRATED.json",
    ]
    ARTIFACT_BAD = (
        re.compile(r'"FULL_E45"'),
        re.compile(r'"BLEND_A\d{2}"'),
        re.compile(r'"ALL_FULL"'),
        re.compile(r'"CHAL_E45_E3_FULL"'),
        re.compile(r'"CONST_A\d{2}"'),
        re.compile(r'"REF_BLEND_A\d{2}"'),
    )
    for pattern in ARTIFACT_GLOBS:
        for apath in sorted(ROOT.glob(pattern)):
            body = apath.read_text(encoding="utf-8", errors="ignore")
            for pat in ARTIFACT_BAD:
                if pat.search(body):
                    violations.append(
                        f"{apath.relative_to(ROOT)}: stale non-canonical book id matching {pat.pattern}"
                    )


    # Live/paper fills+orders must preserve code as str (0050 -> 50 landmine)
    for path in sorted((ROOT / "scripts").glob("e21*.py")) + sorted((ROOT / "scripts").glob("e45*.py")):
        text = path.read_text(encoding="utf-8")
        for m in re.finditer(r"read_csv\(([^\n]{0,160})\)", text):
            call = m.group(0)
            args = m.group(1)
            if "fills.csv" not in args and "orders.csv" not in args and "fills.csv" not in call and "orders.csv" not in call:
                # also catch Path / "fills.csv" nearby — require fills/orders token in call
                if "fills.csv" not in call and "orders.csv" not in call:
                    continue
            if "dtype" not in call or ("code" not in call and "str" not in call):
                line = text.count("\n", 0, m.start()) + 1
                # allow if dtype=str for whole frame
                if re.search(r"dtype\s*=\s*str", call):
                    continue
                if re.search(r"dtype\s*=\s*\{[^}]*code[^}]*str", call):
                    continue
                violations.append(
                    f"{path.relative_to(ROOT)}:{line}: read_csv fills/orders without dtype code=str (0050 landmine)"
                )

    if violations:
        print("E45 paper hygiene FAIL:")
        for v in violations:
            print(f"  - {v}")
        return 1
    print("E45 paper hygiene PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
