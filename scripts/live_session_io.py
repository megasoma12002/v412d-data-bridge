#!/usr/bin/env python3
"""Live session path helpers — resolve canonical paths / load market / gates."""
from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from live_config import LIVE
from live_ledger import ALL, assert_no_uncommitted_ledger

REPO_ROOT = Path(__file__).resolve().parents[1]
CANON_STATE = (REPO_ROOT / "forward" / "e21").resolve()
CANON_MARKET = (CANON_STATE / "live_market.csv").resolve()


def resolve_repo_path(path: Path | str) -> Path:
    p = Path(path)
    if not p.is_absolute():
        return (REPO_ROOT / p).resolve()
    return p.resolve()


def resolve_fill_port_name(cli_fill_port: str | None) -> str:
    return (
        cli_fill_port
        or os.environ.get("E21_FILL_PORT")
        or LIVE.fill_port
        or "paper"
    ).strip().lower()


def assert_canonical_live_paths(
    *,
    state_dir: Path,
    market_path: Path,
    fill_port_name: str,
    allow_noncanonical: bool,
) -> None:
    if allow_noncanonical:
        return
    if state_dir != CANON_STATE or market_path != CANON_MARKET:
        raise SystemExit(
            "Refusing non-canonical live paths. Use --market forward/e21/live_market.csv "
            "and --state-dir forward/e21, or pass --allow-noncanonical-paths for research."
        )
    if fill_port_name != "paper":
        raise SystemExit(
            f"Refusing fill port {fill_port_name!r} on canonical live path. "
            "Use --fill-port paper (default), or --allow-noncanonical-paths for dry_run research."
        )


def load_market_session(
    market_path: Path, *, asof: str | None
) -> tuple[pd.DataFrame, pd.Timestamp, pd.DataFrame]:
    """Return (market_to_latest, latest, day_indexed_by_code)."""
    m = pd.read_csv(market_path, dtype={"code": str})
    m.date = pd.to_datetime(m.date)
    m = m.sort_values(["date", "code"])
    required = set(ALL + ["TAIEX"])
    available = m.groupby("date").code.apply(lambda x: required.issubset(set(x)))
    common = available[available].index
    if len(common) == 0:
        raise RuntimeError("no complete common trading date for all required instruments")
    if asof:
        asof_ts = pd.Timestamp(asof).normalize()
        if asof_ts not in common:
            raise SystemExit(f"--asof {asof} is not a complete common trading date in market")
        latest = asof_ts
    else:
        latest = common.max()
    m = m[m.date <= latest]
    day = m[m.date == latest].set_index("code")
    missing = [c for c in ALL + ["TAIEX"] if c not in day.index]
    if missing:
        raise RuntimeError(f"latest snapshot incomplete {latest.date()}: {missing}")
    return m, latest, day


def load_portfolio_state(state_dir: Path, *, capital: float) -> dict:
    state_path = Path(state_dir) / "portfolio_state.json"
    if state_path.exists():
        import json

        return json.loads(state_path.read_text(encoding="utf-8"))
    return {"cash": capital, "positions": {}, "last_date": None}


def assert_session_preflight(
    state_dir: Path, state: dict, latest: pd.Timestamp
) -> None:
    assert_no_uncommitted_ledger(state_dir, state.get("last_date"))
    prior_last = state.get("last_date")
    if prior_last:
        prior_ts = pd.Timestamp(prior_last).normalize()
        if latest < prior_ts:
            raise SystemExit(
                f"Refusing session {latest.date()} behind portfolio last_date={prior_last}. "
                "Replay/rebuild requires an explicit wipe path; --asof cannot silently rewind."
            )
