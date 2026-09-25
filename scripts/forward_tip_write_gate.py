#!/usr/bin/env python3
"""Fail-closed tip-write gate before GHA pushes Soft-Frozen forward/ (ACCEPT 2026-09-25)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POST = ROOT / "research/ops/POST_FORWARD_E22_VERIFY.json"
TIP = ROOT / "forward/e21/portfolio_state.json"
STAGE_E = "E22_v3_recv_pay_effdelay"


def main() -> int:
    if not POST.is_file():
        print("FATAL: missing POST_FORWARD_E22_VERIFY.json before tip push", file=sys.stderr)
        return 1
    d = json.loads(POST.read_text(encoding="utf-8"))
    if d.get("ok") is not True:
        print(
            "FATAL: post-forward ok!=true — refusing tip push",
            d.get("ok"),
            d.get("failures"),
            file=sys.stderr,
        )
        return 1
    if not TIP.is_file():
        print("FATAL: missing portfolio_state.json", file=sys.stderr)
        return 1
    tip = json.loads(TIP.read_text(encoding="utf-8"))
    books = tip.get("e22_books_version")
    if books != STAGE_E:
        print("FATAL: tip books drift before push:", books, file=sys.stderr)
        return 1
    print(f"tip-write gate PASS ok=true books={books}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
