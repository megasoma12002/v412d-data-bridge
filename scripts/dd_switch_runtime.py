"""Versioned DD_SWITCH dependencies; never read a half-published generation."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIR = ROOT / "data/dd_switch_runtime"


def runtime_dir() -> Path:
    return Path(os.environ.get("E21_DD_INPUTS_DIR", str(DEFAULT_DIR))).resolve()


def inputs(required: bool = False) -> dict[str, Path]:
    pointer = runtime_dir() / "current.json"
    if not pointer.exists():
        if required:
            raise RuntimeError("DD_SWITCH runtime missing; run dd_switch_rebuild.py --publish")
        return {}
    meta = json.loads(pointer.read_text())
    generation = (runtime_dir() / meta["generation"]).resolve()
    if runtime_dir() not in generation.parents:
        raise RuntimeError("DD_SWITCH generation outside runtime directory")
    result = {key: (generation / name).resolve() for key, name in meta["files"].items()}
    if any(generation not in path.parents for path in result.values()):
        raise RuntimeError("DD_SWITCH file outside generation")
    return result


def preflight(asof: str | pd.Timestamp) -> dict:
    paths = inputs(required=True)
    meta = json.loads((runtime_dir() / "current.json").read_text())
    wanted = pd.Timestamp(asof).date().isoformat()
    if meta["asof"] != wanted:
        raise RuntimeError(f"DD_SWITCH inputs stale: {meta['asof']} != {wanted}")
    for key, path in paths.items():
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != meta["hashes"][key]:
            raise RuntimeError(f"DD_SWITCH input checksum mismatch: {key}")
        frame = pd.read_csv(path, usecols=["date"])
        if frame.empty or str(frame.date.max())[:10] != wanted:
            raise RuntimeError(f"DD_SWITCH input tip mismatch: {key}")
    return {"ok": True, "asof": wanted, "generation": meta["generation"]}
