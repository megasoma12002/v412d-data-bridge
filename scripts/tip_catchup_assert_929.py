#!/usr/bin/env python3
"""Assert tip catch-up after 2026-09-29 open session (holidays 9/25–28).

Fails closed until ``portfolio_state.last_date == 2026-09-29`` with live stamps.
Soft-Frozen KEEP — never invent tip rows.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "forward" / "e21" / "portfolio_state.json"
TARGET = "2026-09-29"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--state", type=Path, default=STATE)
    ap.add_argument(
        "--expect-date",
        default=TARGET,
        help="Expected tip last_date after first post-holiday session",
    )
    a = ap.parse_args()
    if not a.state.exists():
        print(json.dumps({"ok": False, "error": "missing_portfolio_state"}))
        return 2
    ps = json.loads(a.state.read_text(encoding="utf-8"))
    last = str(ps.get("last_date") or "")
    checks = {
        "last_date": last == a.expect_date,
        "e22_books": ps.get("e22_books_version") == "E22_v3_recv_pay_effdelay",
        "cool_live": bool(ps.get("cool_exposure_live")) is True,
        "dh_off": ps.get("dh_exposure_live") is False,
        "conf_live": bool(ps.get("conf_ret3_631l_live")) is True,
        "finpriv_live": bool(ps.get("fin_priv_v7_f05_live")) is True,
        "clip_beta": ("BETA" in str(ps.get("soft_frozen_clip_flip") or ""))
        or ("F0.60-0.80" in str(ps.get("soft_frozen_clip_flip") or "")),
    }
    ok = bool(last == a.expect_date and all(checks.values()))
    out = {
        "ok": ok,
        "expect_date": a.expect_date,
        "last_date": last,
        "pending_holiday_gap": last < a.expect_date,
        "checks": checks,
        "soft_frozen_clip_flip": ps.get("soft_frozen_clip_flip"),
        "note": (
            "Tip still pre-holiday — wait for 2026-09-29 forward"
            if last < a.expect_date
            else ("PASS" if ok else "stamp_mismatch")
        ),
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))
    if last < a.expect_date:
        return 1  # pending — not a hard infra fail
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
