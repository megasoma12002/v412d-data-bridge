#!/usr/bin/env python3
"""R5 observe auto — run T+2 reconcile when a custody fixture is present.

Observe-only. Soft-Frozen KEEP · never flips fill_port / broker live-write.
Default out-dir is under fixtures/ (not forward/e21) unless --allow-live-tree-out.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
EST = ROOT / "forward" / "e21" / "settlement_cash_estimate.csv"
DROPIN = ROOT / "fixtures" / "r5_custody_dropin.csv"
SYNTH = ROOT / "fixtures" / "r5_custody_synthetic.csv"
OUT_DEFAULT = ROOT / "fixtures" / "r5_reconcile_observe"


def resolve_custody(*, prefer_dropin: bool = True) -> Path | None:
    if prefer_dropin and DROPIN.is_file() and DROPIN.stat().st_size > 0:
        return DROPIN
    if SYNTH.is_file():
        return SYNTH
    return None


def run_r5_observe(
    *,
    prefer_dropin: bool = True,
    asof: str | None = None,
    out_dir: Path | None = None,
    allow_live_tree_out: bool = False,
) -> dict[str, Any]:
    """Return status dict; does not raise on mismatch (observe)."""
    custody = resolve_custody(prefer_dropin=prefer_dropin)
    out: dict[str, Any] = {
        "reconcile_ran": False,
        "reconcile_all_ok": None,
        "reconcile_out": None,
        "custody": str(custody) if custody else None,
        "estimate_present": EST.is_file(),
        "mode": "dropin" if custody == DROPIN else ("synthetic" if custody == SYNTH else "none"),
        "execute_blocked": True,
        "observe_only": True,
    }
    if not EST.is_file() or custody is None:
        out["skip_reason"] = "missing_estimate_or_custody"
        return out

    dest = Path(out_dir) if out_dir is not None else OUT_DEFAULT
    dest.mkdir(parents=True, exist_ok=True)
    if asof is None:
        ps = ROOT / "forward" / "e21" / "portfolio_state.json"
        if ps.is_file():
            asof = str(json.loads(ps.read_text()).get("last_date") or "") or None
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "twse_t2_broker_reconcile.py"),
        "--estimate",
        str(EST),
        "--custody",
        str(custody),
        "--out-dir",
        str(dest),
    ]
    if asof:
        cmd.extend(["--asof", asof])
    if allow_live_tree_out:
        cmd.append("--allow-live-tree-out")
    rc = subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    latest = dest / "t2_broker_reconcile_latest.json"
    all_ok = None
    if latest.is_file():
        pack = json.loads(latest.read_text(encoding="utf-8"))
        all_ok = bool(pack.get("all_ok"))
    out.update(
        {
            "reconcile_ran": True,
            "reconcile_rc": int(rc),
            "reconcile_all_ok": all_ok,
            "reconcile_out": str(dest),
        }
    )
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--asof", default=None)
    ap.add_argument("--out-dir", type=Path, default=OUT_DEFAULT)
    ap.add_argument(
        "--require-dropin",
        action="store_true",
        help="Exit 0 without running if fixtures/r5_custody_dropin.csv missing.",
    )
    ap.add_argument("--allow-live-tree-out", action="store_true")
    a = ap.parse_args()
    if a.require_dropin and not DROPIN.is_file():
        print(json.dumps({"skipped": True, "reason": "no_dropin", "observe_only": True}))
        return 0
    report = run_r5_observe(
        prefer_dropin=True,
        asof=a.asof,
        out_dir=a.out_dir,
        allow_live_tree_out=bool(a.allow_live_tree_out),
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    # Observe: never fail tip; synthetic must be ok when that was the source.
    if report.get("mode") == "synthetic" and report.get("reconcile_all_ok") is False:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
