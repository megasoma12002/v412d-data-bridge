#!/usr/bin/env python3
"""Load dual-paper NAV books for month-end monitors.

``*_daily_nav.csv`` under ``repro/**/outputs/`` is gitignored; fresh clones /
CI without ``--refresh-ledgers`` only have committed ``dual_paper_nav_compare.csv``.
Prefer daily_nav when present; fall back to compare columns.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd


def _as_nav_frame(df: pd.DataFrame, date_col: str, nav_col: str) -> pd.DataFrame:
    out = df[[date_col, nav_col]].rename(columns={nav_col: "nav"}).copy()
    out["date"] = pd.to_datetime(out["date"])
    return out.sort_values("date").reset_index(drop=True)


def load_daily_nav_csv(path: Path) -> pd.DataFrame:
    d = pd.read_csv(path)
    if "nav" not in d.columns:
        raise SystemExit(f"{path} missing 'nav' column")
    d["date"] = pd.to_datetime(d["date"])
    return d.sort_values("date").reset_index(drop=True)


def load_pair_nav(
    base_path: Path,
    chal_path: Path,
    compare_path: Path,
    *,
    base_col: str = "nav_base",
    chal_col: str = "nav_chal",
    refresh_hint: str = "dual-paper ledgers",
) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    """Return (base, chal, nav_source)."""
    if base_path.exists() and chal_path.exists():
        return load_daily_nav_csv(base_path), load_daily_nav_csv(chal_path), "daily_nav"
    if compare_path.exists():
        d = pd.read_csv(compare_path)
        need = {base_col, chal_col}
        if not need.issubset(d.columns):
            raise SystemExit(
                f"{compare_path} missing {sorted(need)}; have={sorted(d.columns)}; "
                f"run {refresh_hint}"
            )
        return (
            _as_nav_frame(d, "date", base_col),
            _as_nav_frame(d, "date", chal_col),
            "dual_paper_nav_compare",
        )
    raise SystemExit(
        f"Missing dual-paper NAV ({base_path.name} / {chal_path.name} or "
        f"{compare_path.name}). Run {refresh_hint}."
    )


def load_multi_nav(
    paths: dict[str, Path],
    compare_path: Path,
    compare_cols: dict[str, str],
    *,
    refresh_hint: str,
) -> tuple[dict[str, pd.DataFrame], str]:
    """Load named NAV frames. ``paths`` / ``compare_cols`` share the same keys."""
    if all(p.exists() for p in paths.values()):
        return {k: load_daily_nav_csv(p) for k, p in paths.items()}, "daily_nav"
    if compare_path.exists():
        d = pd.read_csv(compare_path)
        need = set(compare_cols.values())
        if not need.issubset(d.columns):
            raise SystemExit(
                f"{compare_path} missing {sorted(need - set(d.columns))}; "
                f"run {refresh_hint}"
            )
        return (
            {k: _as_nav_frame(d, "date", col) for k, col in compare_cols.items()},
            "dual_paper_nav_compare",
        )
    raise SystemExit(
        f"Missing dual-paper NAVs ({', '.join(p.name for p in paths.values())} or "
        f"{compare_path.name}). Run {refresh_hint}."
    )
