#!/usr/bin/env python3
"""Project-wide coding-standards hygiene (fail closed).

Covers:
  - E45 paper landmines (delegates to check_e45_paper_hygiene)
  - metric ``or 0`` / ``or 9`` on cagr/mdd/max_drawdown
  - fee/sleeve monkeypatches anywhere under scripts/
  - banned claim_status emitters
  - Soft-Frozen clip list literals outside e16_soft_frozen_base.py
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

OR_METRIC = re.compile(
    r"""(\[['\"](?:cagr|max_drawdown|mdd)['\"]\]|\b(?:cagr|mdd)\b)\s*or\s*0"""
)
OR9_MDD = re.compile(r"""\[['\"]max_drawdown['\"]\][^\n]{0,40}or\s*9""")
MONKEY = [
    re.compile(r"setattr\(\s*\w+\s*,\s*['\"]?(BUY_FEE|SELL_FEE|SLIP|TAX_)"),
    re.compile(r"apply_exposure_to_sleeve_weights\s*="),
    re.compile(r"def fee_multiple\(|with fee_multiple\("),
]
CLAIM = re.compile(
    r"(claim_mdd_status|claim_status)\s*[:=]\s*['\"]NOT_VERIFIED"
)
CLAIM_KEY_FORK = re.compile(r"""['\"](?:claim_mdd_status|claimed_mdd_status)['\"]\s*:""")
SOFT_ALIAS = re.compile(r"^SOFT_FROZEN_CLIP\s*=", re.M)
ABS_OR9 = re.compile(r"_abs_or\s*\([^\n]{0,80}9\.0")
SOFT_KEEP_STR = re.compile(r"""['\"]soft_frozen['\"]\s*:\s*['\"]KEEP \[0\.50, 0\.95\]['\"]""")

# Local date-literal WINDOWS copies (allow WINDOWS = WINDOWS_STANDARD / dict-comps).
WINDOWS_LITERAL = re.compile(
    r"^WINDOWS\s*=\s*\{[^}]*date\s*\(",
    re.M | re.S,
)
CLIP_JSON = re.compile(
    r"""['\"]soft_frozen_(?:live_)?clip['\"]\s*:\s*\[\s*0\.50\s*,\s*0\.95\s*\]"""
)
CLIP_KEEP = re.compile(
    r"""['\"]soft_frozen_keep['\"]\s*:\s*\[\s*0\.50\s*,\s*0\.95\s*\]"""
)
ALLOW_WINDOWS_LITERAL = {
    "e45_paper_harness.py",  # WINDOWS_STANDARD definition site may use date()
    "v412e0_historical_stress.py",  # intentional non-E45 stress windows
}

ALLOW_OR_FILES = {
    # intentional non-metric or-0 (positions, cash amounts, rates) — none currently
}


def main() -> int:
    violations: list[str] = []

    # Delegate E45 paper checks
    e45 = subprocess.run(
        [sys.executable, str(SCRIPTS / "check_e45_paper_hygiene.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if e45.returncode != 0:
        violations.append("e45_paper_hygiene:\n" + (e45.stdout or e45.stderr))

    for path in sorted(SCRIPTS.glob("*.py")):
        if path.name in {"check_project_coding_hygiene.py", "check_e45_paper_hygiene.py"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        rel = str(path.relative_to(ROOT))

        for pat in MONKEY:
            for m in pat.finditer(text):
                line = text.count("\n", 0, m.start()) + 1
                violations.append(f"{rel}:{line}: monkeypatch `{pat.pattern}`")

        for m in CLAIM.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            violations.append(f"{rel}:{line}: banned claim emitter")

        for m in CLAIM_KEY_FORK.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            violations.append(
                f"{rel}:{line}: JSON key `claim_mdd_status` — emit `claim_status`"
            )

        for m in SOFT_ALIAS.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            violations.append(
                f"{rel}:{line}: alias SOFT_FROZEN_CLIP — import SOFT_FROZEN_FIN_CLIP"
            )

        if path.name not in ALLOW_WINDOWS_LITERAL:
            for m in WINDOWS_LITERAL.finditer(text):
                line = text.count("\n", 0, m.start()) + 1
                violations.append(
                    f"{rel}:{line}: local WINDOWS date literals — use WINDOWS_STANDARD"
                )

        for m in ABS_OR9.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            violations.append(f"{rel}:{line}: `_abs_or(..., 9.0)` — use abs_mdd/mdd_delta_pp")

        for m in SOFT_KEEP_STR.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            violations.append(
                f"{rel}:{line}: Soft-Frozen KEEP string hardcode — emit list(SOFT_FROZEN_FIN_CLIP)"
            )

        if path.name != "e16_soft_frozen_base.py":
            for pat in (CLIP_JSON, CLIP_KEEP):
                for m in pat.finditer(text):
                    line = text.count("\n", 0, m.start()) + 1
                    violations.append(
                        f"{rel}:{line}: hardcode Soft-Frozen clip — import SOFT_FROZEN_FIN_CLIP"
                    )

        if path.name in ALLOW_OR_FILES:
            continue
        for m in OR_METRIC.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            # skip comments
            if text.splitlines()[line - 1].lstrip().startswith("#"):
                continue
            violations.append(f"{rel}:{line}: metric `or 0` — use research_metric_helpers")
        for m in OR9_MDD.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            if text.splitlines()[line - 1].lstrip().startswith("#"):
                continue
            violations.append(f"{rel}:{line}: max_drawdown `or 9` — use abs_mdd()")

    if violations:
        print("Project coding hygiene FAIL:")
        for v in violations:
            print(f"  - {v}")
        return 1
    print("Project coding hygiene PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
