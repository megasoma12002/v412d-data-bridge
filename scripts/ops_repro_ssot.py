#!/usr/bin/env python3
"""SSOT helpers: keep decision packs in ``research/ops``; repro/reports get pointers.

Soft-Frozen / live tip untouched. Avoid byte-identical dual-writes of
``*DECISION_PACK*`` into ``repro/*/reports/``.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def repo_rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve())).replace("\\", "/")
    except ValueError:
        return str(path)


def pointer_body(canonical: Path, *, kind: str = "decision pack") -> str:
    rel = repo_rel(canonical)
    return (
        f"# Pointer — {kind} SSOT\n\n"
        f"Canonical copy: `{rel}`\n\n"
        "Do not dual-write the full artifact into `repro/*/reports/` "
        "(see `research/ops/REPRO_DEDUPE_HYGIENE.md`).\n"
    )


def write_repro_pointer(canonical: Path, repro_path: Path, *, kind: str = "decision pack") -> None:
    """Write a short pointer file at ``repro_path`` pointing at ``canonical``."""
    repro_path.parent.mkdir(parents=True, exist_ok=True)
    repro_path.write_text(pointer_body(canonical, kind=kind), encoding="utf-8")


def write_ops_and_repro_pointer(
    ops_path: Path,
    repro_path: Path,
    body: str,
    *,
    kind: str = "decision pack",
) -> None:
    """Write full body to ops SSOT; pointer-only under repro/reports."""
    ops_path.parent.mkdir(parents=True, exist_ok=True)
    ops_path.write_text(body, encoding="utf-8")
    write_repro_pointer(ops_path, repro_path, kind=kind)
