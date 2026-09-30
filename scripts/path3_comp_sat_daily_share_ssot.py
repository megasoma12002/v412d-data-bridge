#!/usr/bin/env python3
"""Path3 COMP↔SAT daily share SSOT (0kab).

Engine ID: ``P3_COMP_SAT_DAILY_POS_LEDGER_A``

Builds path-dependent paper share ledgers for ``COMP_H150_x_A20`` and
``SAT_A20_RELAX`` by snapshotting ``simulate_core`` end-of-day Soft holdings.

Flip planning uses **ledger-shaped recon**: freeze live Soft sleeve dollars,
apply paper within-sleeve mix from the ledger, ``delta = dest − live_pos``.
0050 KEEP by default (Path3 engine convention). Soft KEEP · broker false · cutover BLOCKED.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from e16_soft_frozen_base import FIN, TEL
from live_path3_t0_switch_emitter import BOOK_COMP, BOOK_SAT
from live_path3_t0_weight_engine import equal_target_shares, sleeve_notional
from tw_share_lots import BOARD_LOT, board_lots

ROOT = Path(__file__).resolve().parents[1]
ENGINE_ID = "P3_COMP_SAT_DAILY_POS_LEDGER_A"
REGISTER = "0kab"
ETF_CODE = "0050"
DEFAULT_LEDGER_DIR = ROOT / "repro" / "fin-sat-path3-daily-share-ssot-stagea" / "outputs"
SOFT_CODES = list(FIN) + list(TEL) + [ETF_CODE]


def ledger_path(book: str, *, out_dir: Path | str = DEFAULT_LEDGER_DIR) -> Path:
    safe = str(book).replace("/", "_")
    return Path(out_dir) / f"daily_shares_{safe}.csv"


def shares_panel_from_long(df: pd.DataFrame) -> pd.DataFrame:
    """Long ``date,code,shares`` → wide panel indexed by date."""
    if df is None or df.empty:
        return pd.DataFrame()
    x = df.copy()
    x["date"] = pd.to_datetime(x["date"])
    x["code"] = x["code"].astype(str)
    x["shares"] = x["shares"].astype(float)
    return (
        x.pivot_table(index="date", columns="code", values="shares", aggfunc="sum")
        .sort_index()
        .fillna(0.0)
    )


def load_book_shares(
    book: str,
    *,
    out_dir: Path | str = DEFAULT_LEDGER_DIR,
) -> pd.DataFrame:
    path = ledger_path(book, out_dir=out_dir)
    if not path.exists():
        raise FileNotFoundError(path)
    return shares_panel_from_long(pd.read_csv(path, dtype={"code": str}))


def shares_asof(
    book: str,
    asof: pd.Timestamp | str,
    *,
    panel: pd.DataFrame | None = None,
    out_dir: Path | str = DEFAULT_LEDGER_DIR,
) -> dict[str, float]:
    """Nearest prior (or equal) date share map for Soft universe codes."""
    shares, _ledger_asof, _ = shares_asof_detail(
        book, asof, panel=panel, out_dir=out_dir
    )
    return shares


def shares_asof_detail(
    book: str,
    asof: pd.Timestamp | str,
    *,
    panel: pd.DataFrame | None = None,
    out_dir: Path | str = DEFAULT_LEDGER_DIR,
) -> tuple[dict[str, float], pd.Timestamp | None, pd.Timestamp | None]:
    """Return ``(shares, ledger_asof, panel_end)``.

    ``ledger_asof`` is the panel row date used; ``panel_end`` is the last
    available ledger date (for stale checks).
    """
    pan = panel if panel is not None else load_book_shares(book, out_dir=out_dir)
    if pan.empty:
        return {}, None, None
    asof_ts = pd.Timestamp(asof).normalize()
    panel_end = pd.Timestamp(pan.index.max()).normalize()
    prior = pan.index[pan.index <= asof_ts]
    if len(prior) == 0:
        return {}, None, panel_end
    row_date = pd.Timestamp(prior[-1]).normalize()
    row = pan.loc[prior[-1]]
    shares = {str(c): float(row[c]) for c in row.index if abs(float(row[c])) > 1e-12}
    return shares, row_date, panel_end


def dollar_mix(
    shares: Mapping[str, float],
    prices: Mapping[str, float],
    codes: list[str] | tuple[str, ...],
) -> dict[str, float]:
    """Within-sleeve dollar weights (sum≈1) from share map."""
    dol = {
        c: float(shares.get(c, 0.0)) * float(prices[c])
        for c in codes
        if c in prices and float(prices[c]) > 0 and abs(float(shares.get(c, 0.0))) > 1e-12
    }
    s = sum(dol.values())
    if s <= 1e-9:
        return {}
    return {c: v / s for c, v in dol.items()}


def scale_mix_to_shares(
    mix: Mapping[str, float],
    *,
    sleeve_dollars: float,
    prices: Mapping[str, float],
) -> dict[str, float]:
    if sleeve_dollars <= 1e-9 or not mix:
        return {}
    out: dict[str, float] = {}
    for c, w in mix.items():
        if c not in prices or float(prices[c]) <= 0:
            continue
        out[c] = float(board_lots(float(sleeve_dollars) * float(w) / float(prices[c])))
    return out


def plan_delta_ledger_scaled(
    *,
    live_pos: Mapping[str, float],
    prices: Mapping[str, float],
    ledger_shares: Mapping[str, float],
    keep_0050: bool = True,
    allow_equal_fallback: bool = False,
) -> tuple[dict[str, float], dict[str, Any]]:
    """Freeze live Soft sleeve $; apply ledger within-sleeve mix; delta vs live.

    When ledger has sleeve names but mix is empty (e.g. missing prices), default
    is fail-closed (leave sleeve unchanged) — not equal-weight recon — unless
    ``allow_equal_fallback=True``.
    """
    p = {str(k): float(v) for k, v in live_pos.items() if abs(float(v)) > 1e-12}
    px = {str(k): float(v) for k, v in prices.items() if float(v) > 0}
    fin_dol = sleeve_notional(FIN, p, px)
    tel_dol = sleeve_notional(TEL, p, px)
    fin_mix = dollar_mix(ledger_shares, px, FIN)
    tel_mix = dollar_mix(ledger_shares, px, TEL)
    fin_fallback = False
    tel_fallback = False
    if not fin_mix:
        if allow_equal_fallback or not any(c in ledger_shares for c in FIN):
            fin_t = equal_target_shares(FIN, sleeve_dollars=fin_dol, prices=px)
            fin_fallback = bool(allow_equal_fallback and any(c in ledger_shares for c in FIN))
        else:
            fin_t = {c: float(p.get(c, 0.0)) for c in FIN}
            fin_fallback = False
            # fail-closed: keep live FIN weights
    else:
        fin_t = scale_mix_to_shares(fin_mix, sleeve_dollars=fin_dol, prices=px)
    if not tel_mix:
        if allow_equal_fallback or not any(c in ledger_shares for c in TEL):
            tel_t = equal_target_shares(TEL, sleeve_dollars=tel_dol, prices=px)
            tel_fallback = bool(allow_equal_fallback and any(c in ledger_shares for c in TEL))
        else:
            tel_t = {c: float(p.get(c, 0.0)) for c in TEL}
    else:
        tel_t = scale_mix_to_shares(tel_mix, sleeve_dollars=tel_dol, prices=px)

    dest = dict(p)
    for c in FIN:
        dest[c] = float(fin_t.get(c, 0.0))
    for c in TEL:
        dest[c] = float(tel_t.get(c, 0.0))
    if keep_0050 and ETF_CODE in p:
        dest[ETF_CODE] = float(p[ETF_CODE])
    elif not keep_0050:
        etf_dol = sleeve_notional([ETF_CODE], p, px)
        etf_mix = dollar_mix(ledger_shares, px, [ETF_CODE])
        if etf_mix:
            dest[ETF_CODE] = float(
                scale_mix_to_shares(etf_mix, sleeve_dollars=etf_dol, prices=px).get(ETF_CODE, 0.0)
            )

    delta: dict[str, float] = {}
    for c in sorted(set(dest) | set(p)):
        d = float(dest.get(c, 0.0)) - float(p.get(c, 0.0))
        if abs(d) >= float(BOARD_LOT) - 1e-9:
            delta[c] = d

    meta = {
        "engine_id": ENGINE_ID,
        "policy": "LEDGER_SCALED_RECON",
        "fin_notional": round(fin_dol, 2),
        "tel_notional": round(tel_dol, 2),
        "fin_mix": {k: round(v, 6) for k, v in fin_mix.items()},
        "tel_mix": {k: round(v, 6) for k, v in tel_mix.items()},
        "fin_mix_empty": not bool(fin_mix),
        "tel_mix_empty": not bool(tel_mix),
        "equal_fallback": bool(fin_fallback or tel_fallback),
        "n_delta_names": len(delta),
        "delta_shares": {k: round(v, 1) for k, v in delta.items()},
        "keep_0050": bool(keep_0050),
        "ledger_n_names": len(ledger_shares),
    }
    return delta, meta


def plan_delta_shares_ledger(
    *,
    asof: pd.Timestamp | str,
    dest_book: str,
    live_pos: Mapping[str, float],
    prices: Mapping[str, float],
    panels: Mapping[str, pd.DataFrame] | None = None,
    out_dir: Path | str = DEFAULT_LEDGER_DIR,
    keep_0050: bool = True,
    max_stale_calendar_days: int = 0,
    allow_equal_fallback: bool = False,
) -> tuple[dict[str, float] | None, dict[str, Any]]:
    """Ledger-scaled recon for ``dest_book`` asof.

    ``max_stale_calendar_days``: if ``asof`` is more than this many calendar days
    after the ledger row date, return ``None`` with ``reason=ledger_stale``
    (default 0 = require exact ledger date match / same-day tip).
    """
    book = str(dest_book)
    asof_ts = pd.Timestamp(asof).normalize()
    meta: dict[str, Any] = {
        "engine_id": ENGINE_ID,
        "dest_book": book,
        "asof": str(asof_ts.date()),
    }
    try:
        panel = None if panels is None else panels.get(book)
        led, ledger_asof, panel_end = shares_asof_detail(
            book, asof, panel=panel, out_dir=out_dir
        )
    except FileNotFoundError as exc:
        meta["reason"] = f"ledger_missing:{exc}"
        return None, meta
    if panel_end is not None:
        meta["ledger_panel_end"] = str(panel_end.date())
    if ledger_asof is not None:
        meta["ledger_asof"] = str(ledger_asof.date())
        lag = int((asof_ts - ledger_asof).days)
        meta["ledger_lag_calendar_days"] = lag
        meta["ledger_stale"] = bool(lag > int(max_stale_calendar_days))
        if meta["ledger_stale"]:
            meta["reason"] = "ledger_stale"
            return None, meta
    if not led:
        meta["reason"] = "ledger_empty_asof"
        return None, meta
    meta["ledger_asof_names"] = sorted(led)
    delta, plan_meta = plan_delta_ledger_scaled(
        live_pos=live_pos,
        prices=prices,
        ledger_shares=led,
        keep_0050=keep_0050,
        allow_equal_fallback=allow_equal_fallback,
    )
    meta.update(plan_meta)
    meta["reason"] = "ledger_scaled_recon" if delta else "ledger_scaled_empty"
    return delta, meta


def write_ledger_csv(
    rows: list[dict[str, Any]],
    book: str,
    *,
    out_dir: Path | str = DEFAULT_LEDGER_DIR,
) -> Path:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = ledger_path(book, out_dir=out)
    pd.DataFrame(rows).to_csv(path, index=False)
    # sidecar meta
    meta_path = path.with_suffix(".meta.json")
    dates = sorted({str(r["date"]) for r in rows}) if rows else []
    meta_path.write_text(
        json.dumps(
            {
                "book": book,
                "engine_id": ENGINE_ID,
                "register": REGISTER,
                "n_rows": len(rows),
                "n_days": len(dates),
                "start": dates[0] if dates else None,
                "end": dates[-1] if dates else None,
                "codes": sorted({str(r["code"]) for r in rows}),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def book_ids() -> tuple[str, str]:
    return BOOK_COMP, BOOK_SAT
