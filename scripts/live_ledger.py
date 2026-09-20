#!/usr/bin/env python3
"""Live ledger store — immutable CSV append + holdings helpers.

Execution/broker adapters should eventually write fills through the same
append_immutable contract. Soft-Frozen / live flags are not owned here.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from e16_soft_frozen_base import FIN, TEL
from portfolio_capital import DEFAULT_CAPITAL

ALL = FIN + TEL + ["0050"]

# Cost model shared by live session (paper Exact T+1). Broker port may override later.
BUY_FEE = 0.001425 * 0.6
SELL_FEE = 0.001425 * 0.6
TAX_STOCK = 0.003
TAX_ETF = 0.001
SLIP = 0.0005
# Broker 整股 floor (NT$). Commission only — sell tax is separate and not floored.
MIN_COMMISSION = 20.0


def commission(gross: float, rate: float, *, min_commission: float = MIN_COMMISSION) -> float:
    """Broker commission with NT$ floor. ``rate<=0`` → 0 (research 0× cost runs)."""
    g = float(gross)
    r = float(rate)
    if r <= 0 or g <= 0:
        return 0.0
    return max(g * r, float(min_commission))


def sell_tax(code: str, gross: float) -> float:
    tax = TAX_ETF if str(code) == "0050" else TAX_STOCK
    return float(gross) * tax


def fees_tax_for(*, side: str, code: str, gross: float) -> float:
    """Canonical live ``fees_tax``: BUY = commission; SELL = commission + 證交稅."""
    s = str(side).upper()
    g = float(gross)
    if s == "BUY":
        return commission(g, BUY_FEE)
    if s == "SELL":
        return commission(g, SELL_FEE) + sell_tax(code, g)
    raise ValueError(f"unknown side: {side!r}")


def max_affordable_buy_qty(cash: float, fp: float, *, lot: int = 1000) -> int:
    """Largest board-lot qty affordable including min commission.

    When ``gross * BUY_FEE >= MIN_COMMISSION``, same as ``cash / (fp*(1+BUY_FEE))``.
    Otherwise cash must cover ``gross + MIN_COMMISSION``.
    """
    from tw_share_lots import board_lots

    cash_f = float(cash)
    fp_f = float(fp)
    if cash_f <= 0 or fp_f <= 0:
        return 0
    # Threshold gross where rate equals floor
    thr = MIN_COMMISSION / BUY_FEE if BUY_FEE > 0 else 0.0
    q_rate = board_lots(int(cash_f / (fp_f * (1 + BUY_FEE))))
    if q_rate > 0 and q_rate * fp_f >= thr:
        return q_rate
    if cash_f <= MIN_COMMISSION:
        return 0
    return board_lots(int((cash_f - MIN_COMMISSION) / fp_f))


def make_order_id(*, signal_date: Any, code: str, side: str) -> str:
    """Stable Soft-Frozen ``order_id``: ``{YYYY-MM-DD}-{code}-{BUY|SELL}``.

    Quantity is intentionally NOT in the id — same day/code/side replay is a
    no-op via ``append_immutable`` (first write wins). Do not change this format
    without Soft-Frozen KEEP / ACCEPT; historical ``orders.csv`` / ``fills.csv``
    keys depend on it.
    """
    if hasattr(signal_date, "isoformat"):
        d = str(signal_date.isoformat())[:10]
    else:
        d = str(signal_date).strip()[:10]
    return f"{d}-{str(code).strip()}-{str(side).strip().upper()}"


def append_immutable(path: Path | str, row: dict[str, Any], key: str) -> bool:
    """Append one row if ``key`` is new. Never rewrite history. Returns True if written.

    CSV rewrite uses temp + ``os.replace`` so a crash mid-write cannot truncate the ledger.
    """
    import os
    import tempfile

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    new = pd.DataFrame([row])
    if p.exists():
        old = pd.read_csv(p, dtype={"code": str})
        hit = old[old[key].astype(str) == str(row[key])]
        if len(hit):
            return False
        new = pd.concat([old, new], ignore_index=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=p.name + ".", suffix=".tmp", dir=str(p.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as f:
            new.to_csv(f, index=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, p)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
    return True


def atomic_write_json(path: Path | str, obj: Any) -> None:
    """Write JSON via temp file + os.replace (crash-safe)."""
    import json
    import os
    import tempfile

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(obj, indent=2, ensure_ascii=False) + "\n"
    fd, tmp_name = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def assert_no_uncommitted_ledger(state_dir: Path | str, last_date: str | None) -> None:
    """Fail-closed if ledger CSVs advanced past portfolio_state.last_date.

    Detects crash after immutable append but before state commit (L3).
    Checks fills, dividends_applied, orders, signals, and nav.
    """
    sdir = Path(state_dir)
    last = pd.Timestamp(last_date).normalize() if last_date else None

    def _date_series(df: pd.DataFrame) -> pd.Series | None:
        for col in ("fill_date", "signal_date", "date", "asof"):
            if col in df.columns:
                return pd.to_datetime(df[col], errors="coerce").dt.normalize()
        return None

    def _check(path: Path, *, label: str, id_col: str | None = None) -> None:
        if not path.exists():
            return
        if path.name == "fills.csv":
            df = pd.read_csv(path, dtype={"code": str})
        else:
            df = pd.read_csv(path)
        if df.empty:
            return
        series = _date_series(df)
        if series is None:
            return
        if last is None:
            raise SystemExit(
                f"Uncommitted {label} present but portfolio_state.last_date is missing. "
                "Repair state or clear orphan rows before continuing."
            )
        if bool((series > last).any()):
            if id_col and id_col in df.columns:
                bad = df.loc[series > last, id_col].astype(str).head(5).tolist()
            else:
                bad = series.loc[series > last].astype(str).head(5).tolist()
            raise SystemExit(
                f"Uncommitted {label} after last_date={last_date}: {bad}. "
                "Crash between ledger append and portfolio_state commit — "
                "repair state or authorized replay before continuing."
            )

    fills_path = sdir / "fills.csv"
    if fills_path.exists():
        fills = pd.read_csv(fills_path, dtype={"code": str})
        if not fills.empty and "fill_date" in fills.columns:
            fd = pd.to_datetime(fills["fill_date"], errors="coerce").dt.normalize()
            if last is None:
                raise SystemExit(
                    "Uncommitted fills present but portfolio_state.last_date is missing. "
                    "Repair state or clear orphan fills before continuing."
                )
            if bool((fd > last).any()):
                bad = fills.loc[fd > last, "fill_id"].astype(str).head(5).tolist()
                raise SystemExit(
                    f"Uncommitted fills after last_date={last_date}: {bad}. "
                    "Crash between fills.csv append and portfolio_state commit — "
                    "repair state or authorized replay before continuing."
                )

    div_path = sdir / "dividends_applied.csv"
    if div_path.exists():
        divs = pd.read_csv(div_path)
        if not divs.empty and "date" in divs.columns:
            dd = pd.to_datetime(divs["date"], errors="coerce").dt.normalize()
            if last is None:
                raise SystemExit(
                    "Uncommitted dividends_applied present but portfolio_state.last_date "
                    "is missing. Repair before continuing."
                )
            if bool((dd > last).any()):
                bad = divs.loc[dd > last, "key"].astype(str).head(5).tolist()
                raise SystemExit(
                    f"Uncommitted dividends after last_date={last_date}: {bad}. "
                    "Repair state or authorized replay before continuing."
                )

    _check(sdir / "orders.csv", label="orders", id_col="order_id")
    _check(sdir / "signals.csv", label="signals", id_col="signal_id")
    _check(sdir / "nav.csv", label="nav")


def holdings(
    state: dict[str, Any],
    prices: dict[str, float],
    *,
    capital: float = DEFAULT_CAPITAL,
) -> tuple[dict[str, float], float, dict[str, float], float]:
    pos = {c: float(state.get("positions", {}).get(c, 0)) for c in ALL}
    cash = float(state.get("cash", capital))
    recv_map = state.get("e22_receivables") or {}
    receivable = float(sum(float(v) for v in recv_map.values()))
    vals = {c: pos[c] * prices[c] for c in ALL}
    # Wealth identity (Stage-B sealed compare): cash + receivable + marked equity
    nav = cash + receivable + sum(vals.values())
    return pos, cash, vals, nav


class LedgerStore:
    """Filesystem ledger under a state directory (canonical: forward/e21)."""

    def __init__(self, state_dir: Path | str):
        self.state_dir = Path(state_dir)

    def path(self, name: str) -> Path:
        return self.state_dir / name

    def append(self, name: str, row: dict[str, Any], key: str) -> bool:
        return append_immutable(self.path(name), row, key)
