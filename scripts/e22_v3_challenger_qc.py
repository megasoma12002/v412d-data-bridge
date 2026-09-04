#!/usr/bin/env python3
"""Fail-closed QC for E22_v3 paper challenger ledgers (not official)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e22_v3_challenger_forward_pipeline as e22v3


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--state-dir", default="forward/e22_v3_challenger")
    args = ap.parse_args()
    status = e22v3.run_qc(Path(args.state_dir))
    print(json.dumps(status, indent=2))
    if status["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
