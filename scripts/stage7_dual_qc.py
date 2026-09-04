#!/usr/bin/env python3
"""Stage 7 dual QC — official E22_v2 + paper E22_v3 challenger."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e22_v2_forward_pipeline as v2
import e22_v3_challenger_forward_pipeline as v3


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--v2-dir", default="forward/e22_v2")
    ap.add_argument("--v3-dir", default="forward/e22_v3_challenger")
    ap.add_argument("--out", default="repro/stage7-tx-oi-timing-20260904/dual_qc.json")
    args = ap.parse_args()

    status_v2 = v2.run_qc(Path(args.v2_dir))
    status_v3 = v3.run_qc(Path(args.v3_dir))
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stage": 7,
        "e22_v2": status_v2,
        "e22_v3_challenger": status_v3,
        "dual_pass": status_v2.get("status") == "PASS" and status_v3.get("status") == "PASS",
        "promotion": False,
        "note": "Ops monitoring only — v3 remains EXPERIMENTAL_PAPER",
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if not report["dual_pass"]:
        raise SystemExit(1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
