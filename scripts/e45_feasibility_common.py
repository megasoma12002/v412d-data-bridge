#!/usr/bin/env python3
"""Shared E45 feasibility helpers (claim labels, manifests, metrics)."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

# Canonical −13.16% claim vocabulary — must match research/e45/E45_OFFICIAL_STATUS.*
CLAIMED_MDD = -0.1316
CLAIMED_MDD_LABEL = "NOT_VERIFIED_HISTORICAL_NARRATIVE"
CLAIMED_MDD_INTERPRETATION = "EARLY_NON_RIGOROUS_RESEARCH_RESULT"
CLAIMED_MDD_NOTE = (
    "−13.16% is an early, non-rigorous research narrative — not a verified baseline. "
    "No dated CSV/JSON equals −0.1316. Prefer dated lineage MDDs "
    "(−15.81% / −18.49% / early-stack −20.76%)."
)

E45_ARTIFACT_STATUS = "NOT_VERIFIED"
E45_STITCH_STATUS = "DEFERRED"
E45_GOVERNANCE_CLASS = "SOFT_FROZEN_CRITICAL"
E45_LIVE_AUTHORIZATION = "NO"

VERIFIED_CLOSEST_LINEAGE_VAL_MDD = -0.1581
VERIFIED_E3_LOCKED_VAL_MDD = -0.1849
VERIFIED_EARLY_STACK_PLUS_E45_E3_MDD = -0.2076

DEFAULT_LIVE_BOOKS = "E22_v2s_tw"
SUPERSEDED_PACK_NAMES = {
    "e45-feasibility-study",
    "repro/e45-feasibility-study",
}

REQUIRED_OUTPUT_FILES = (
    "e16_e18_e22_daily_nav.csv",
    "e16_e18_e22_e45_e3_daily_nav.csv",
    "e16_e18_e22_fills.csv",
    "e16_e18_e22_e45_e3_fills.csv",
)

LOCKED_E3_WINNER = {
    "mode": "voltarget",
    "max_cut": 0.5,
    "up_days": 20,
    "target_vol": 0.14,
    "blend": 0.5,
    "rank_buffer": 0,
    "cost_hurdle_mult": 5,
    "min_hold": 42,
}


def claim_dict() -> dict:
    return {
        "mdd": CLAIMED_MDD,
        "label": CLAIMED_MDD_LABEL,
        "interpretation": CLAIMED_MDD_INTERPRETATION,
        "note": CLAIMED_MDD_NOTE,
    }


def official_status_dict() -> dict:
    return {
        "E45_ARTIFACT_STATUS": E45_ARTIFACT_STATUS,
        "E45_STITCH_STATUS": E45_STITCH_STATUS,
        "E45_GOVERNANCE_CLASS": E45_GOVERNANCE_CLASS,
        "E45_LIVE_AUTHORIZATION": E45_LIVE_AUTHORIZATION,
        "DEFAULT_BOOKS_VERSION": DEFAULT_LIVE_BOOKS,
    }


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def dumps_json(obj: Any) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def mdd(nav: pd.Series) -> float:
    x = nav.astype(float)
    return float((x / x.cummax() - 1.0).min())


def cagr_calendar(nav: pd.Series, dates: pd.Series) -> float:
    years = (pd.to_datetime(dates.iloc[-1]) - pd.to_datetime(dates.iloc[0])).days / 365.25
    if years <= 0 or float(nav.iloc[0]) <= 0:
        return float("nan")
    return float((float(nav.iloc[-1]) / float(nav.iloc[0])) ** (1.0 / years) - 1.0)


def refuse_superseded_pack(pack: Path) -> None:
    pack = Path(pack).resolve()
    if (pack / "SUPERSEDED.md").exists() or (pack / "ARCHIVED.md").exists():
        raise SystemExit(f"Refuse superseded/archived pack: {pack}")
    if pack.name in SUPERSEDED_PACK_NAMES or str(pack).endswith("/e45-feasibility-study"):
        raise SystemExit(
            f"Refuse pack {pack}: superseded path. Use regen dir with manifests."
        )


def write_manifests(
    out_dir: Path,
    *,
    inputs: dict[str, Path],
    output_files: Iterable[str] | None = None,
    purpose: str = "fresh_regen",
) -> None:
    out_dir = Path(out_dir)
    outputs_dir = out_dir / "outputs"
    output_files = list(output_files or REQUIRED_OUTPUT_FILES)
    now = datetime.now(timezone.utc).isoformat()
    input_manifest: dict[str, Any] = {
        "generated_at_utc": now,
        "purpose": purpose,
        "inputs": {},
    }
    for key, path in inputs.items():
        p = Path(path)
        input_manifest["inputs"][key] = {
            "path": str(p),
            "sha256": sha256_file(p) if p.exists() else None,
            "bytes": p.stat().st_size if p.exists() else None,
            "exists": p.exists(),
        }
    output_manifest: dict[str, Any] = {
        "generated_at_utc": now,
        "purpose": purpose,
        "outputs": {},
    }
    for name in output_files:
        p = outputs_dir / name
        if p.exists():
            output_manifest["outputs"][name] = {
                "path": f"outputs/{name}",
                "sha256": sha256_file(p),
                "bytes": p.stat().st_size,
            }
    for p in sorted(outputs_dir.glob("*.csv")):
        if p.name not in output_manifest["outputs"]:
            output_manifest["outputs"][p.name] = {
                "path": f"outputs/{p.name}",
                "sha256": sha256_file(p),
                "bytes": p.stat().st_size,
            }
    (out_dir / "INPUT_MANIFEST.json").write_text(dumps_json(input_manifest), encoding="utf-8")
    (out_dir / "OUTPUT_MANIFEST.json").write_text(dumps_json(output_manifest), encoding="utf-8")


def verify_output_manifest(in_dir: Path, required: Iterable[str] | None = None) -> dict:
    """Fail-closed sha256 verify of OUTPUT_MANIFEST entries (not presence-only)."""
    in_dir = Path(in_dir)
    refuse_superseded_pack(in_dir)
    man_path = in_dir / "OUTPUT_MANIFEST.json"
    if not (in_dir / "INPUT_MANIFEST.json").exists() or not man_path.exists():
        raise SystemExit(
            f"Refuse pack {in_dir}: missing INPUT_MANIFEST.json / OUTPUT_MANIFEST.json"
        )
    man = load_json(man_path)
    required = list(required or REQUIRED_OUTPUT_FILES)
    mismatches: list[dict] = []
    missing: list[str] = []
    for name in required:
        meta = man.get("outputs", {}).get(name)
        p = in_dir / "outputs" / name
        if meta is None or not p.exists():
            missing.append(name)
            continue
        dig = sha256_file(p)
        if dig != meta.get("sha256"):
            mismatches.append({"file": name, "manifest": meta.get("sha256"), "actual": dig})
    ok = not missing and not mismatches
    result = {
        "ok": ok,
        "purpose": man.get("purpose"),
        "n_outputs_checked": len(required),
        "manifest_generated_at_utc": man.get("generated_at_utc"),
        "missing": missing,
        "mismatches": mismatches,
    }
    if not ok:
        raise SystemExit(
            dumps_json({"error": "OUTPUT_MANIFEST hash verification failed", **result})
        )
    return result
