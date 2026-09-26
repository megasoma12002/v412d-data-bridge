#!/usr/bin/env python3
"""Fail-closed tip-write gate before GHA pushes Soft-Frozen forward/ (ACCEPT 2026-09-25).

Defense-in-depth (arch-sec residual fix 2026-09-26):
  - post-forward verify ok=true
  - tip books == Stage-E DEFAULT
  - qc_status.json status=PASS and exact_t1_ok=true

Cash clocks (never merge into this gate): Exact T+1 cash · R4 settled estimate ·
cash+receivables — see CASHFLOW_THREE_VIEWS.md. Tip push only requires ledger QC +
post-forward + books identity.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POST = ROOT / "research/ops/POST_FORWARD_E22_VERIFY.json"
TIP = ROOT / "forward/e21/portfolio_state.json"
QC = ROOT / "forward/e21/qc_status.json"
STAGE_E = "E22_v3_recv_pay_effdelay"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate(
    *,
    post_path: Path = POST,
    tip_path: Path = TIP,
    qc_path: Path = QC,
    stage_e: str = STAGE_E,
) -> tuple[bool, list[str]]:
    """Return (ok, failure_messages). Fail-closed on any missing/bad artifact."""
    failures: list[str] = []
    if not post_path.is_file():
        failures.append(f"missing {post_path}")
        return False, failures
    d = _load_json(post_path)
    if d.get("ok") is not True:
        failures.append(f"post-forward ok!=true ok={d.get('ok')!r} failures={d.get('failures')!r}")

    if not tip_path.is_file():
        failures.append(f"missing {tip_path}")
    else:
        tip = _load_json(tip_path)
        books = tip.get("e22_books_version")
        if books != stage_e:
            failures.append(f"tip books drift: {books!r} != {stage_e!r}")

    if not qc_path.is_file():
        failures.append(f"missing {qc_path}")
    else:
        qc = _load_json(qc_path)
        status = str(qc.get("status") or "").upper()
        if status != "PASS":
            failures.append(f"qc_status status={status!r} (require PASS)")
        exact = qc.get("exact_t1_ok")
        if exact is not True:
            failures.append(f"qc_status exact_t1_ok={exact!r} (require True)")

    return (len(failures) == 0), failures


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Fail-closed Soft-Frozen tip-write gate")
    ap.add_argument("--post", type=Path, default=POST)
    ap.add_argument("--tip", type=Path, default=TIP)
    ap.add_argument("--qc", type=Path, default=QC)
    args = ap.parse_args(argv)
    ok, failures = evaluate(post_path=args.post, tip_path=args.tip, qc_path=args.qc)
    if not ok:
        for msg in failures:
            print(f"FATAL: {msg}", file=sys.stderr)
        return 1
    print("tip-write gate PASS ok=true books=Stage-E qc=PASS exact_t1_ok=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
