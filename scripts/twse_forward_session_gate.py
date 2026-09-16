#!/usr/bin/env python3
"""Paper forward session gate (P2).

Calls ``probe_session``; when the board is not a trading session, writes
``session_skip.json`` and exits 0 so GHA can skip expensive forward steps.

Does not mutate Soft-Frozen books. Broker submit gating is P4 (FillPort).
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from twse_session_sources import (
    DEFAULT_CALENDAR_DIR,
    probe_session,
    read_calendar_csv,
)

TAIPEI = ZoneInfo("Asia/Taipei")
ROOT = Path(__file__).resolve().parents[1]


def should_skip_forward(*, is_session: bool, status: str) -> bool:
    """Skip paper noise when there is no trading session."""
    _ = status
    return not bool(is_session)


def run_gate(
    *,
    asof: date,
    out_dir: Path,
    use_network: bool,
    calendar_path: Path | None,
) -> dict:
    calendar = None
    if calendar_path and calendar_path.exists():
        calendar = read_calendar_csv(calendar_path)
    probe = probe_session(asof, use_network=use_network, calendar=calendar)
    skip = should_skip_forward(is_session=probe.is_session, status=probe.status)
    payload = {
        "asof": probe.asof,
        "status": probe.status,
        "is_session": probe.is_session,
        "broker_submit_allowed": probe.broker_submit_allowed,
        "skipped": skip,
        "reason": (
            f"no trading session ({probe.status})"
            if skip
            else "session open or confirmed"
        ),
        "notes": list(probe.notes),
        "sources": probe.sources,
        "generated_at": datetime.now(tz=TAIPEI).isoformat(),
        "soft_frozen_untouched": True,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    skip_path = out_dir / "session_skip.json"
    probe_path = out_dir / "session_probe.json"
    skip_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    probe_path.write_text(
        json.dumps({**payload, "probe": asdict(probe)}, ensure_ascii=False, indent=2, default=str)
        + "\n",
        encoding="utf-8",
    )
    # GHA-friendly machine line
    print(f"session_skip={str(skip).lower()}")
    print(json.dumps({"asof": probe.asof, "status": probe.status, "skipped": skip}, ensure_ascii=False))
    return payload


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--asof",
        default="",
        help="YYYY-MM-DD (default: Taipei today)",
    )
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "forward",
    )
    ap.add_argument(
        "--calendar",
        type=Path,
        default=DEFAULT_CALENDAR_DIR / "twse_sessions_2026.csv",
    )
    ap.add_argument("--no-network", action="store_true")
    ap.add_argument(
        "--github-output",
        type=Path,
        default=None,
        help="Write skip=true|false for GHA outputs",
    )
    a = ap.parse_args()
    if a.asof:
        asof = date.fromisoformat(a.asof)
    else:
        asof = datetime.now(tz=TAIPEI).date()
    payload = run_gate(
        asof=asof,
        out_dir=a.out_dir,
        use_network=not a.no_network,
        calendar_path=a.calendar,
    )
    if a.github_output is not None:
        a.github_output.parent.mkdir(parents=True, exist_ok=True)
        with a.github_output.open("a", encoding="utf-8") as f:
            f.write(f"skip={str(payload['skipped']).lower()}\n")
            f.write(f"status={payload['status']}\n")
            f.write(f"asof={payload['asof']}\n")
    # Always exit 0 — skip is signaled via artifact / GHA output, not nonzero.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
