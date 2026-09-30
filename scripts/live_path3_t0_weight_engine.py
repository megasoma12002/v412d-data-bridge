#!/usr/bin/env python3
"""Path3 COMP↔SAT weight engine — Stage B asof recon (0ka9).

Engine ID: ``P3_COMP_SAT_ASOF_RECON_B``

- Flip → SAT: freeze Soft sleeve $ → FIN RELAX (KD + pre-ex buy_ok, no HARD) + TEL equal
- Flip → COMP: freeze Soft sleeve $ → FIN OR_K9×HARD150 + TEL equal
- 0050 KEEP

Stage A equal-recon remains available as ``plan_sat_equal_recon`` fallback helper.
Soft-Frozen KEEP · broker false · cutover BLOCKED · emit/fill ON (0ka7).
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

from e16_soft_frozen_base import FIN, TEL
from fin_buy_quality_helpers import (
    and_buy_ok,
    below_ma_ok,
    catalog_gate,
    not_gate,
    or_buy_ok,
    raw_close_panel,
)
from live_config import KD_OPT
from live_path3_t0_switch_emitter import (
    BOOK_COMP,
    BOOK_SAT,
    switch_meta_for_asof,
)
from ta_indicator_catalog import build_low_high_catalog
from tw_share_lots import BOARD_LOT, board_lots
from within_sleeve_alloc import build_kd_season_tilt_scores, build_pre_exdiv_window_buy_ok

ROOT = Path(__file__).resolve().parents[1]
ENGINE_ID = "P3_COMP_SAT_ASOF_RECON_B"
ENGINE_ID_STAGEA = "P3_SOFT_SLEEVE_EQ_RECON_PROXY"
ETF_CODE = "0050"
MARKET_DEFAULT = ROOT / "forward/e21/live_market.csv"
DIV_DEFAULT = ROOT / "data/dividend_events/e22_dividend_events.csv"


def _fpos(pos: Mapping[str, float]) -> dict[str, float]:
    return {str(k): float(v) for k, v in pos.items() if abs(float(v)) > 1e-12}


def _fpx(prices: Mapping[str, float]) -> dict[str, float]:
    return {str(k): float(v) for k, v in prices.items() if float(v) > 0}


def sleeve_notional(
    codes: list[str] | tuple[str, ...], pos: Mapping[str, float], prices: Mapping[str, float]
) -> float:
    return float(
        sum(
            float(pos.get(c, 0.0)) * float(prices[c])
            for c in codes
            if c in prices and float(prices[c]) > 0
        )
    )


def equal_target_shares(
    codes: list[str] | tuple[str, ...],
    *,
    sleeve_dollars: float,
    prices: Mapping[str, float],
) -> dict[str, float]:
    names = [c for c in codes if c in prices and float(prices[c]) > 0]
    if not names or sleeve_dollars <= 1e-9:
        return {c: 0.0 for c in names}
    per = float(sleeve_dollars) / len(names)
    return {c: float(board_lots(per / float(prices[c]))) for c in names}


def score_target_shares(
    codes: list[str],
    *,
    sleeve_dollars: float,
    prices: Mapping[str, float],
    scores: Mapping[str, float] | None,
) -> dict[str, float]:
    names = [c for c in codes if c in prices and float(prices[c]) > 0]
    if not names or sleeve_dollars <= 1e-9:
        return {c: 0.0 for c in names}
    if scores:
        raw = {c: max(float(scores.get(c, 1.0)), 0.05) for c in names}
    else:
        raw = {c: 1.0 for c in names}
    s = sum(raw.values()) or 1.0
    out: dict[str, float] = {}
    for c in names:
        dol = float(sleeve_dollars) * (raw[c] / s)
        out[c] = float(board_lots(dol / float(prices[c])))
    return out


def plan_sat_equal_recon(
    *,
    pos: Mapping[str, float],
    prices: Mapping[str, float],
) -> tuple[dict[str, float], dict[str, Any]]:
    """Stage A helper: SAT dest = FIN_EQUAL + TEL_EQUAL; 0050 KEEP."""
    p = _fpos(pos)
    px = _fpx(prices)
    fin_dol = sleeve_notional(FIN, p, px)
    tel_dol = sleeve_notional(TEL, p, px)
    fin_t = equal_target_shares(FIN, sleeve_dollars=fin_dol, prices=px)
    tel_t = equal_target_shares(TEL, sleeve_dollars=tel_dol, prices=px)
    dest = dict(p)
    for c in FIN:
        dest[c] = float(fin_t.get(c, 0.0))
    for c in TEL:
        dest[c] = float(tel_t.get(c, 0.0))
    if ETF_CODE in p:
        dest[ETF_CODE] = float(p[ETF_CODE])
    delta = {
        c: float(dest.get(c, 0.0)) - float(p.get(c, 0.0))
        for c in sorted(set(dest) | set(p))
        if abs(float(dest.get(c, 0.0)) - float(p.get(c, 0.0))) >= float(BOARD_LOT) - 1e-9
    }
    meta = {
        "engine_id": ENGINE_ID_STAGEA,
        "dest_book": BOOK_SAT,
        "fin_notional": round(fin_dol, 2),
        "tel_notional": round(tel_dol, 2),
        "n_delta_names": len(delta),
        "delta_shares": {k: round(v, 1) for k, v in delta.items()},
    }
    return delta, meta


@lru_cache(maxsize=2)
def _load_overlay_panels(
    market_path: str, div_path: str
) -> tuple[pd.DatetimeIndex, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return cal, kd_scores, base_buy_ok, or_k9_buy_ok, hard150_sell_ok (FIN columns)."""
    market = pd.read_csv(market_path, dtype={"code": str})
    market["date"] = pd.to_datetime(market["date"])
    div = (
        pd.read_csv(div_path, dtype={"code": str})
        if Path(div_path).exists()
        else pd.DataFrame()
    )
    cal = pd.DatetimeIndex(pd.to_datetime(market["date"]).drop_duplicates().sort_values())
    lows, _highs = build_low_high_catalog(market, cal, list(FIN))
    raw = raw_close_panel(market, cal, list(FIN))
    kd = build_kd_season_tilt_scores(
        market,
        div,
        list(FIN),
        k_thresh=float(KD_OPT["k_thresh"]),
        season_start=KD_OPT["season_start"],
        season_end=KD_OPT["season_end"],
        pre_days=int(KD_OPT["pre_days"]),
        active_score=float(KD_OPT["active_score"]),
    )
    base_buy = build_pre_exdiv_window_buy_ok(
        cal, div, list(FIN), pre_days=int(KD_OPT["pre_days"]), also_stock_ex=True
    )
    extra = or_buy_ok(catalog_gate(lows["BELOW_MA120"]), catalog_gate(lows["K9_LT30"]))
    or_k9 = and_buy_ok(base_buy, extra)
    hard = not_gate(below_ma_ok(raw, 150))
    return cal, kd, base_buy, or_k9, hard


def asof_fin_overlays(
    asof: pd.Timestamp | str,
    *,
    market_path: Path | str = MARKET_DEFAULT,
    div_path: Path | str = DIV_DEFAULT,
) -> dict[str, Any]:
    """FIN asof maps: kd scores, base_buy_ok, or_k9_buy_ok, hard150_sell_ok."""
    asof_ts = pd.Timestamp(asof).normalize()
    cal, kd, base_buy, or_k9, hard = _load_overlay_panels(str(market_path), str(div_path))
    # nearest prior date on calendar
    prior = cal[cal <= asof_ts]
    if len(prior) == 0:
        return {
            "ok": False,
            "reason": "asof_before_market",
            "asof": str(asof_ts.date()),
        }
    d = prior[-1]

    def _row_bool(df: pd.DataFrame) -> dict[str, bool]:
        if d not in df.index:
            return {c: True for c in FIN}
        return {c: bool(df.loc[d, c]) if c in df.columns and pd.notna(df.loc[d, c]) else True for c in FIN}

    def _row_score(df: pd.DataFrame) -> dict[str, float]:
        if d not in df.index:
            return {c: 1.0 for c in FIN}
        return {
            c: float(df.loc[d, c]) if c in df.columns and pd.notna(df.loc[d, c]) else 1.0 for c in FIN
        }

    return {
        "ok": True,
        "asof_used": str(pd.Timestamp(d).date()),
        "kd_scores": _row_score(kd),
        "base_buy_ok": _row_bool(base_buy),
        "or_k9_buy_ok": _row_bool(or_k9),
        "hard150_sell_ok": _row_bool(hard),
    }


def _delta_from_dest(
    pos: Mapping[str, float], dest: Mapping[str, float]
) -> dict[str, float]:
    p = _fpos(pos)
    keys = sorted(set(p) | set(dest))
    out: dict[str, float] = {}
    for c in keys:
        d = float(dest.get(c, 0.0)) - float(p.get(c, 0.0))
        if abs(d) >= float(BOARD_LOT) - 1e-9:
            out[c] = d
    return out


def plan_comp_or_k9_hard150(
    *,
    pos: Mapping[str, float],
    prices: Mapping[str, float],
    overlays: Mapping[str, Any],
) -> tuple[dict[str, float], dict[str, Any]]:
    """COMP dest: FIN scored among OR_K9∧HARD150; HARD fail → 0; TEL equal; 0050 KEEP."""
    p = _fpos(pos)
    px = _fpx(prices)
    fin_dol = sleeve_notional(FIN, p, px)
    tel_dol = sleeve_notional(TEL, p, px)
    buy_ok = overlays.get("or_k9_buy_ok") or {}
    sell_ok = overlays.get("hard150_sell_ok") or {}
    scores = overlays.get("kd_scores") or {}

    # Force out names that fail HARD150
    forced_zero = [c for c in FIN if not bool(sell_ok.get(c, True))]
    eligible = [
        c
        for c in FIN
        if c in px
        and bool(sell_ok.get(c, True))
        and (bool(buy_ok.get(c, False)) or float(p.get(c, 0.0)) > 0)
    ]
    if not eligible:
        # fail-open to sell_ok holders so recon still moves
        eligible = [c for c in FIN if c in px and bool(sell_ok.get(c, True))]
    if not eligible:
        eligible = [c for c in FIN if c in px]

    fin_t = score_target_shares(eligible, sleeve_dollars=fin_dol, prices=px, scores=scores)
    for c in FIN:
        if c not in fin_t:
            fin_t[c] = 0.0
    for c in forced_zero:
        fin_t[c] = 0.0

    tel_t = equal_target_shares(TEL, sleeve_dollars=tel_dol, prices=px)
    dest = dict(p)
    for c in FIN:
        dest[c] = float(fin_t.get(c, 0.0))
    for c in TEL:
        dest[c] = float(tel_t.get(c, 0.0))
    if ETF_CODE in p:
        dest[ETF_CODE] = float(p[ETF_CODE])

    delta = _delta_from_dest(p, dest)
    meta = {
        "engine_id": ENGINE_ID,
        "dest_book": BOOK_COMP,
        "policy": "OR_K9xHARD150",
        "fin_notional": round(fin_dol, 2),
        "tel_notional": round(tel_dol, 2),
        "n_eligible_fin": len(eligible),
        "forced_zero_hard": forced_zero,
        "n_delta_names": len(delta),
        "delta_shares": {k: round(v, 1) for k, v in delta.items()},
        "asof_used": overlays.get("asof_used"),
    }
    return delta, meta


def plan_sat_relax_kd(
    *,
    pos: Mapping[str, float],
    prices: Mapping[str, float],
    overlays: Mapping[str, Any],
) -> tuple[dict[str, float], dict[str, Any]]:
    """SAT dest: FIN KD + base pre-ex buy_ok (no HARD); TEL equal; 0050 KEEP."""
    p = _fpos(pos)
    px = _fpx(prices)
    fin_dol = sleeve_notional(FIN, p, px)
    tel_dol = sleeve_notional(TEL, p, px)
    buy_ok = overlays.get("base_buy_ok") or {}
    scores = overlays.get("kd_scores") or {}

    eligible = [
        c
        for c in FIN
        if c in px and (bool(buy_ok.get(c, True)) or float(p.get(c, 0.0)) > 0)
    ]
    if not eligible:
        eligible = [c for c in FIN if c in px]

    fin_t = score_target_shares(eligible, sleeve_dollars=fin_dol, prices=px, scores=scores)
    for c in FIN:
        if c not in fin_t:
            fin_t[c] = 0.0
    tel_t = equal_target_shares(TEL, sleeve_dollars=tel_dol, prices=px)
    dest = dict(p)
    for c in FIN:
        dest[c] = float(fin_t.get(c, 0.0))
    for c in TEL:
        dest[c] = float(tel_t.get(c, 0.0))
    if ETF_CODE in p:
        dest[ETF_CODE] = float(p[ETF_CODE])

    delta = _delta_from_dest(p, dest)
    meta = {
        "engine_id": ENGINE_ID,
        "dest_book": BOOK_SAT,
        "policy": "SAT_RELAX_KD",
        "fin_notional": round(fin_dol, 2),
        "tel_notional": round(tel_dol, 2),
        "n_eligible_fin": len(eligible),
        "n_delta_names": len(delta),
        "delta_shares": {k: round(v, 1) for k, v in delta.items()},
        "asof_used": overlays.get("asof_used"),
    }
    return delta, meta


def plan_delta_shares(
    *,
    asof: pd.Timestamp | str,
    pos: Mapping[str, float],
    prices: Mapping[str, float],
    signal: pd.DataFrame | None = None,
    require_flip: bool = True,
    market_path: Path | str = MARKET_DEFAULT,
    div_path: Path | str = DIV_DEFAULT,
) -> tuple[dict[str, float] | None, dict[str, Any]]:
    """Stage B: both-direction asof recon. None = not applicable (keep fail-closed)."""
    sw = switch_meta_for_asof(asof, signal=signal)
    meta: dict[str, Any] = {
        "engine_id": ENGINE_ID,
        "switch": sw,
        "asof": str(pd.Timestamp(asof).date()),
    }
    if not sw.get("ok"):
        meta["reason"] = sw.get("reason") or "signal_unavailable"
        return None, meta
    if require_flip and not sw.get("flip"):
        meta["reason"] = "no_flip"
        return None, meta

    book = str(sw.get("book") or "")
    meta["dest_book"] = book
    overlays = asof_fin_overlays(asof, market_path=market_path, div_path=div_path)
    if not overlays.get("ok"):
        meta["reason"] = overlays.get("reason") or "overlay_unavailable"
        return None, meta
    meta["overlay_asof"] = overlays.get("asof_used")

    if book == BOOK_SAT or "SAT" in book:
        delta, plan_meta = plan_sat_relax_kd(pos=pos, prices=prices, overlays=overlays)
        meta.update(plan_meta)
        meta["reason"] = "sat_relax_kd" if delta else "sat_relax_kd_empty"
        return delta, meta

    if book == BOOK_COMP or "COMP" in book:
        delta, plan_meta = plan_comp_or_k9_hard150(pos=pos, prices=prices, overlays=overlays)
        meta.update(plan_meta)
        meta["reason"] = "comp_or_k9_hard150" if delta else "comp_or_k9_hard150_empty"
        return delta, meta

    meta["reason"] = "unknown_book"
    return None, meta


def plan_or_none_for_pipeline(
    *,
    asof: pd.Timestamp | str,
    pos: Mapping[str, float],
    prices: Mapping[str, float],
    signal: pd.DataFrame | None = None,
) -> tuple[dict[str, float] | None, dict[str, Any]]:
    """Pipeline entry: dispatch by ``LIVE.live_path3_weight_engine_mode``.

    - ``ledger`` (ACCEPT 0kab): ledger-scaled recon from daily share SSOT
    - ``asof_b``: Stage B OR_K9×HARD150 / SAT RELAX asof overlays
    """
    try:
        from live_config import LIVE

        mode = str(getattr(LIVE, "live_path3_weight_engine_mode", "asof_b") or "asof_b")
    except Exception:
        mode = "asof_b"

    daily_ok = False
    try:
        from live_path3_strategy_cutover import daily_path3_recon_enabled

        daily_ok = bool(daily_path3_recon_enabled())
    except Exception:
        daily_ok = False

    if mode == "ledger":
        from path3_comp_sat_daily_share_ssot import plan_delta_shares_ledger

        sw = switch_meta_for_asof(asof, signal=signal)
        meta: dict[str, Any] = {
            "weight_engine_mode": mode,
            "switch": sw,
            "asof": str(pd.Timestamp(asof).date()),
            "path3_strategy_cutover_daily": daily_ok,
        }
        if not sw.get("ok"):
            meta["reason"] = sw.get("reason") or "signal_unavailable"
            meta["engine_id"] = None
            return None, meta
        if not sw.get("flip") and not daily_ok:
            meta["reason"] = "no_flip"
            meta["engine_id"] = None
            return None, meta
        book = str(sw.get("book") or "")
        delta, plan_meta = plan_delta_shares_ledger(
            asof=asof,
            dest_book=book,
            live_pos=pos,
            prices=prices,
        )
        meta.update(plan_meta)
        meta["weight_engine_mode"] = mode
        meta["switch"] = sw
        meta["path3_strategy_cutover_daily"] = daily_ok
        if not sw.get("flip") and daily_ok:
            meta["recon_mode"] = "daily_cutover"
        if delta is None:
            return None, meta
        return delta, meta

    delta, meta = plan_delta_shares(
        asof=asof,
        pos=pos,
        prices=prices,
        signal=signal,
        require_flip=not daily_ok,
    )
    meta = dict(meta)
    meta["weight_engine_mode"] = mode
    if delta is None:
        return None, meta
    return delta, meta
