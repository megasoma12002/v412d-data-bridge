#!/usr/bin/env python3
"""Live rebalance → Soft-Frozen order rows (SELL-before-BUY sorted)."""
from __future__ import annotations

from datetime import date
from typing import Any, Mapping

import numpy as np
import pandas as pd

from e16_soft_frozen_base import FIN, TEL
from live_config import (
    KD_OPT,
    LIVE_FIN_WITHIN_SLEEVE,
    LIVE_FUSE_ADDITIVE,
)
from live_ledger import make_order_id
from tw_share_lots import BOARD_LOT, board_lots
from within_sleeve_alloc import (
    allocate_sleeve_orders,
    build_kd_season_tilt_scores,
    build_pre_exdiv_window_buy_ok,
)


def sleeve_trade_from_gap(
    pre: Mapping[str, float], target: Mapping[str, float]
) -> tuple[dict[str, float], float]:
    gap = {k: float(target[k] - pre[k]) for k in pre}
    l1 = sum(abs(v) for v in gap.values())
    trade = np.zeros(3)
    if max(abs(v) for v in gap.values()) >= 0.015:
        trade = np.array([gap["Financial"], gap["Telecom"], gap["0050"]]) * 0.75
        if abs(trade).sum() > 0.20:
            trade *= 0.20 / abs(trade).sum()
    sleeve_trade = dict(zip(["Financial", "Telecom", "0050"], trade))
    return sleeve_trade, l1


def build_live_order_rows(
    *,
    market: pd.DataFrame,
    latest: pd.Timestamp,
    prices: dict[str, float],
    pos: dict[str, float],
    nav: float,
    sleeve_trade: Mapping[str, float],
    dividends_path: str | Any,
) -> list[dict[str, Any]]:
    """Allocate FIN (KD_OPT ± FUSE softs) + TEL/0050 equal-split; SELL-first sort."""
    div_df = (
        pd.read_csv(dividends_path, dtype={"code": str})
        if __import__("pathlib").Path(dividends_path).exists()
        else pd.DataFrame()
    )
    cal = pd.to_datetime(market["date"]).drop_duplicates().sort_values()
    kd_scores = build_kd_season_tilt_scores(
        market,
        div_df,
        FIN,
        k_thresh=float(KD_OPT["k_thresh"]),
        season_start=KD_OPT["season_start"],
        season_end=KD_OPT["season_end"],
        pre_days=int(KD_OPT["pre_days"]),
        active_score=float(KD_OPT["active_score"]),
    )
    kd_buy_ok = build_pre_exdiv_window_buy_ok(
        cal,
        div_df,
        FIN,
        pre_days=int(KD_OPT["pre_days"]),
        also_stock_ex=True,
    )
    fin_scores_today = None
    if latest in kd_scores.index:
        fin_scores_today = {
            c: float(kd_scores.loc[latest, c])
            for c in FIN
            if c in kd_scores.columns and pd.notna(kd_scores.loc[latest, c])
        }
    fin_buy_ok_today = None
    if latest in kd_buy_ok.index:
        fin_buy_ok_today = {
            c: bool(kd_buy_ok.loc[latest, c])
            for c in FIN
            if c in kd_buy_ok.columns
        }
    fin_sell_scores_today = None
    if LIVE_FUSE_ADDITIVE:
        import live_dh_fuse_cutover as live_cut

        soft_scores, soft_ok, soft_sell = live_cut.fuse_soft_panels_for_asof(
            market, div_df, latest
        )
        if soft_scores is not None:
            fin_scores_today = soft_scores
        if soft_ok is not None:
            fin_buy_ok_today = soft_ok
        fin_sell_scores_today = soft_sell

    order_rows: list[dict[str, Any]] = []
    sig_d = latest.date() if hasattr(latest, "date") else date.fromisoformat(str(latest)[:10])
    fin_dollars = float(sleeve_trade["Financial"]) * nav
    if abs(fin_dollars) >= 1e-9:
        for c, side, qty in allocate_sleeve_orders(
            fin_dollars,
            {x: float(prices[x]) for x in FIN},
            pos,
            policy_id=LIVE_FIN_WITHIN_SLEEVE,
            codes=FIN,
            lot_size=BOARD_LOT,
            scores=fin_scores_today,
            buy_ok=fin_buy_ok_today,
            sell_scores=fin_sell_scores_today,
        ):
            if qty < BOARD_LOT or qty % BOARD_LOT != 0:
                continue
            oid = make_order_id(signal_date=sig_d, code=c, side=side)
            order_rows.append(
                {
                    "order_id": oid,
                    "signal_date": sig_d.isoformat(),
                    "code": c,
                    "side": side,
                    "quantity": int(qty),
                    "reference_close": prices[c],
                }
            )
    for sleeve_name, codes in [("Telecom", TEL), ("0050", ["0050"])]:
        value = sleeve_trade[sleeve_name] * nav / len(codes)
        for c in codes:
            qty = board_lots(abs(value) / prices[c])
            if qty < BOARD_LOT:
                continue
            side = "BUY" if value > 0 else "SELL"
            if side == "SELL":
                qty = min(qty, board_lots(pos.get(c, 0)))
            if qty < BOARD_LOT:
                continue
            oid = make_order_id(signal_date=sig_d, code=c, side=side)
            order_rows.append(
                {
                    "order_id": oid,
                    "signal_date": sig_d.isoformat(),
                    "code": c,
                    "side": side,
                    "quantity": qty,
                    "reference_close": prices[c],
                }
            )
    order_rows.sort(key=lambda o: (0 if o["side"] == "SELL" else 1, o["code"]))
    return order_rows
