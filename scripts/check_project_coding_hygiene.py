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
CLIP_JSON = re.compile(
    r"""['\"]soft_frozen_(?:live_)?clip['\"]\s*:\s*\[\s*0\.50\s*,\s*0\.95\s*\]"""
)
CLIP_KEEP = re.compile(
    r"""['\"]soft_frozen_keep['\"]\s*:\s*\[\s*0\.50\s*,\s*0\.95\s*\]"""
)

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
