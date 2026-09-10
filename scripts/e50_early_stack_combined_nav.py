#!/usr/bin/env python3
"""Early-stack combined NAV (research + formal E22_v2s books).

Market -> E16 Core (adj_close signals) -> E18 Exact T+1 -> E22 books (raw close)
  -> optional E45 crisis module (challenger candidate)

E22_v2s is formal books (cash + stock shares). E22_v2 cash-only is preserved for compare.
Does not promote e45_crisis_core.py to SOFT_FROZEN_CRITICAL.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e16_soft_frozen_base as soft_frozen
import e22_dividend_accounting as e22div
import e45_crisis_core as e45
from tw_share_lots import BOARD_LOT
from portfolio_capital import DEFAULT_CAPITAL
from within_sleeve_alloc import (
    FIN_EQUAL,
    FIN_ALLOC_POLICIES,
    FIN_DUAL_PUB_PRIV,
    FIN_MIX_EQUAL_PRE_EXDIV_KD,
    FIN_MIX_EQUAL_RS_EXDIV,
    FIN_PRE_EXDIV_KD,
    TEL_EQUAL,
    TEL_MIN_LOT_PACK,
    TEL_TOP1,
    TEL_TOP2_EQUAL,
    TEL_ALLOC_POLICIES,
    TEL_MIX_EQUAL_PRE_EXDIV_KD,
    TEL_MIX_EQUAL_RS_EXDIV,
    TEL_EXDIV_SKIP_BUY,
    TEL_RS_SOFT_TILT,
    TEL_RS_SOFT_TILT_EXDIV,
    TEL_PRE_EXDIV_KD,
    allocate_sleeve_orders,
    build_name_scores,
)

# Back-compat aliases for Stage B telecom challenger (#125)
TEL_ALLOC_EQUAL = TEL_EQUAL
TEL_ALLOC_MIN_LOT_PACK = TEL_MIN_LOT_PACK
TEL_ALLOC_TOP1 = TEL_TOP1
TEL_ALLOC_TOP2_EQUAL = TEL_TOP2_EQUAL

CLAIM_STATUS = e45.CLAIMED_MDD_STATUS
from research_metric_helpers import metric_delta, fmt_pct

# Mirror E21 SOFT_FROZEN membership / fees (read-only copy of constants; not an edit).
FIN = ["2880", "2886", "2892", "5880"]
TEL = ["2412", "3045", "4904"]
ALL = FIN + TEL + ["0050"]
BUY_FEE = 0.001425 * 0.6
SELL_FEE = 0.001425 * 0.6
TAX_STOCK = 0.003
TAX_ETF = 0.001
SLIP = 0.0005
CAPITAL = DEFAULT_CAPITAL
WARMUP_DAYS = 252


def build_tel_name_scores(market: pd.DataFrame):
    """Causal within-Telecom scores — delegates to shared within_sleeve_alloc."""
    return build_name_scores(market, TEL)


def e16_features(m: pd.DataFrame):
    """Causal Soft-Frozen E16 targets — delegates to `e16_soft_frozen_base`.

    Live clip [0.50, 0.95] lives in one module. Challenger clips use
    `e16_fin_cap_oof_challenger.e16_features_fin_cap` only.
    """
    p, sleeve, target, reg, _score = soft_frozen.build_soft_frozen_targets(m)
    return p, sleeve, target, reg


def lot_qty(value: float, price: float, lot_size: int = BOARD_LOT) -> int:
    """Share quantity from notional; default TW 整股 (一張=1000). Pass lot_size=1 for 1-share sensitivity."""
    if price <= 0 or not math.isfinite(price) or lot_size < 1:
        return 0
    raw = int(abs(value) / price)
    if lot_size == 1:
        return raw
    return (raw // lot_size) * lot_size


def simulate_core(
    market: pd.DataFrame,
    target: pd.DataFrame,
    regime: pd.Series,
    dividends: pd.DataFrame | None,
    *,
    apply_e22: bool,
    e22_version: str | None = None,
    apply_stock_div: bool | None = None,
    e45_exposure: pd.Series | None = None,
    e45_legacy_crisis_scale: float | None = None,
    e45_sleeve_names: tuple[str, ...] | None = None,
    sleeve_weight_schedule: pd.DataFrame | None = None,
    def_code: str | None = None,
    cost_multiple: float = 1.0,
    capital: float = CAPITAL,
    lot_size: int = BOARD_LOT,
    financial_alloc: str = FIN_EQUAL,
    telecom_alloc: str = TEL_EQUAL,
    fin_name_scores: pd.DataFrame | None = None,
    tel_name_scores: pd.DataFrame | None = None,
    fin_buy_ok: pd.DataFrame | None = None,
    tel_buy_ok: pd.DataFrame | None = None,
    fin_sell_ok: pd.DataFrame | None = None,
    fin_sell_scores: pd.DataFrame | None = None,
    fin_mix_lambda: float | None = None,
    tel_mix_lambda: float | None = None,
    fin_dual_pub_codes: list[str] | tuple[str, ...] | None = None,
    fin_dual_priv_codes: list[str] | tuple[str, ...] | None = None,
    fin_dual_pub_policy: str = FIN_PRE_EXDIV_KD,
    fin_dual_priv_policy: str = FIN_EQUAL,
    fin_pub_codes: list[str] | tuple[str, ...] | None = None,
    fin_priv_codes: list[str] | tuple[str, ...] | None = None,
    fin_pub_alloc: str | None = None,
    fin_priv_alloc: str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Exact T+1 open fills; E22 books on raw close; optional named-E45.

    Formal books default = E22_v2s_tw (cash + stock + 畸零股面額 CIL). E22_v2 remains cash-only.
    E16 features use adj_close elsewhere; NAV here always marks with raw close.
    lot_size: default ``BOARD_LOT`` (1000 = 一張 / 整股) for live-aligned paper.
    Pass ``lot_size=1`` only for explicit 1-share / 零股-capable sensitivity research.
    畸零股 (0.x) are not traded here — E22_v2s_tw cashes them at 面額.

    cost_multiple: scale BUY_FEE/SELL_FEE/SLIP/TAX_* for this run only (no module
    monkeypatch). e45_sleeve_names: if set, scale only those sleeves by exposure.
    sleeve_weight_schedule: optional daily Soft-Frozen sleeve targets with columns
    Financial/Telecom/0050 and optional DEF (paper M2 relocate / true-DEF v1),
    or FinPub/FinPriv/Telecom/0050 for Soft-Frozen 4-sleeve paper.
    When present for a date, it overrides e45_exposure / legacy crisis scale.
    def_code: optional synthetic/research DEF instrument code present in ``market``;
    required when schedule carries a DEF column > 0.
    financial_alloc / telecom_alloc: paper within-sleeve policies (default EQUAL).
    fin_mix_lambda / tel_mix_lambda: when *_alloc is a MIX_EQUAL_* policy, weight on
    EQUAL in λ·EQUAL+(1−λ)·challenger (required in [0,1]).
    For FIN_DUAL_PUB_PRIV, fin_mix_lambda is 金融公 share of Financial dollars;
    fin_dual_* codes/policies nest within-group alloc.
    For FinPub/FinPriv schedule: fin_pub_codes / fin_priv_codes required;
    fin_pub_alloc defaults to financial_alloc; fin_priv_alloc defaults to FIN_EQUAL.
    Live e21 unchanged until dedicated cutover ACCEPT.
    """
    if financial_alloc not in FIN_ALLOC_POLICIES:
        raise ValueError(f"financial_alloc must be one of {FIN_ALLOC_POLICIES}")
    if financial_alloc in (FIN_MIX_EQUAL_RS_EXDIV, FIN_MIX_EQUAL_PRE_EXDIV_KD, FIN_DUAL_PUB_PRIV):
        if fin_mix_lambda is None:
            raise ValueError(f"fin_mix_lambda required for {financial_alloc}")
        if not (0.0 <= float(fin_mix_lambda) <= 1.0):
            raise ValueError("fin_mix_lambda must be in [0,1]")
    if financial_alloc == FIN_DUAL_PUB_PRIV:
        if not fin_dual_pub_codes and not fin_dual_priv_codes:
            raise ValueError("fin_dual_pub_codes / fin_dual_priv_codes required for FIN_DUAL_PUB_PRIV")
    if telecom_alloc not in TEL_ALLOC_POLICIES:
        raise ValueError(f"telecom_alloc must be one of {TEL_ALLOC_POLICIES}")
    if telecom_alloc in (TEL_MIX_EQUAL_RS_EXDIV, TEL_MIX_EQUAL_PRE_EXDIV_KD):
        if tel_mix_lambda is None:
            raise ValueError(f"tel_mix_lambda required for {telecom_alloc}")
        if not (0.0 <= float(tel_mix_lambda) <= 1.0):
            raise ValueError("tel_mix_lambda must be in [0,1]")
    pub_codes = list(fin_pub_codes) if fin_pub_codes is not None else None
    priv_codes = list(fin_priv_codes) if fin_priv_codes is not None else None
    pub_alloc = str(fin_pub_alloc or financial_alloc)
    priv_alloc = str(fin_priv_alloc or FIN_EQUAL)
    if pub_alloc not in FIN_ALLOC_POLICIES:
        raise ValueError(f"fin_pub_alloc must be one of {FIN_ALLOC_POLICIES}")
    if priv_alloc not in FIN_ALLOC_POLICIES:
        raise ValueError(f"fin_priv_alloc must be one of {FIN_ALLOC_POLICIES}")
    if e22_version is None:
        if apply_stock_div is False:
            e22_version = e22div.E22_V2
        else:
            e22_version = e22div.DEFAULT_BOOKS_VERSION  # E22_v2s_tw (promoted live default)
    if apply_stock_div is None:
        apply_stock_div = e22_version in e22div.STOCK_SHARE_VERSIONS
    cm = float(cost_multiple)
    if cm < 0:
        raise ValueError("cost_multiple must be >= 0")
    buy_fee = BUY_FEE * cm
    sell_fee = SELL_FEE * cm
    slip = SLIP * cm
    tax_stock = TAX_STOCK * cm
    tax_etf = TAX_ETF * cm
    m = market.copy()
    m["date"] = pd.to_datetime(m["date"])
    closes = m.pivot(index="date", columns="code", values="close").sort_index().ffill()
    opens = m.pivot(index="date", columns="code", values="open").sort_index().ffill()
    dates = [d for d in closes.index if d in target.index]
    if len(dates) < WARMUP_DAYS + 10:
        raise RuntimeError("insufficient history for E16 warmup")

    def_c = str(def_code) if def_code else None
    if def_c is not None:
        if def_c in ALL:
            raise ValueError(f"def_code collides with equity universe: {def_c}")
        if def_c not in closes.columns or def_c not in opens.columns:
            raise ValueError(f"def_code {def_c} missing from market open/close")
    universe = list(ALL) + ([def_c] if def_c else [])

    events: list[e22div.DivEvent] = []
    if apply_e22 and dividends is not None and len(dividends):
        tmp = Path("/tmp/e50_e22_div_events.csv")
        dividends.to_csv(tmp, index=False)
        events = [e for e in e22div.load_dividend_events(tmp) if e.code in ALL]

    pos = {c: 0.0 for c in universe}
    cash = float(capital)
    pending: list[dict] = []
    nav_rows = []
    fill_rows = []
    trade_start = dates[WARMUP_DAYS]
    same_bar = 0
    div_cash_total = 0.0
    cil_cash_total = 0.0
    fractional_shares_cashed = 0.0
    stock_div_events = 0
    stock_div_shares_added = 0.0
    crisis_days = 0

    for i, dt in enumerate(dates):
        if dt < trade_start:
            continue
        op = opens.loc[dt]
        cl = closes.loc[dt]

        # 1) Fill pending orders at today's open (E18 Exact T+1)
        still = []
        for o in pending:
            if pd.Timestamp(o["signal_date"]) >= dt:
                still.append(o)
                continue
            side = o["side"]
            code = o["code"]
            q = int(o["quantity"])
            if lot_size > 1:
                q = (q // lot_size) * lot_size
            fp = float(op[code]) * (1 + slip if side == "BUY" else 1 - slip)
            gross = q * fp
            tax = tax_etf if code == "0050" or (def_c is not None and code == def_c) else tax_stock
            fee = gross * (buy_fee if side == "BUY" else sell_fee + tax)
            if side == "BUY" and gross + fee > cash:
                afford = int(cash / (fp * (1 + buy_fee)))
                if lot_size > 1:
                    afford = (afford // lot_size) * lot_size
                q = max(0, afford)
                gross = q * fp
                fee = gross * buy_fee
            if q < 1:
                continue
            if side == "BUY":
                pos[code] += q
                cash -= gross + fee
            else:
                held = int(pos[code]) if lot_size == 1 else int(pos[code] // lot_size) * lot_size
                q = min(q, held)
                if q < 1:
                    continue
                gross = q * fp
                fee = gross * (sell_fee + tax)
                pos[code] -= q
                cash += gross - fee
            sig_s = (
                o["signal_date"].date().isoformat()
                if hasattr(o["signal_date"], "date")
                else str(o["signal_date"])
            )
            fill_rows.append(
                {
                    "fill_date": dt.date().isoformat(),
                    "signal_date": sig_s,
                    "code": code,
                    "side": side,
                    "quantity": q,
                    "fill_price": fp,
                    "gross": gross,
                    "fees_tax": fee,
                }
            )
            # Exact T+1 audit on the recorded fill (filter above already requires signal < dt).
            if pd.Timestamp(sig_s).normalize() >= dt.normalize():
                same_bar += 1
        pending = still

        # 2) E22 books on ex-date via formal accounting module
        #    CIL marks fractional stock remainder at today's raw close.
        day_div = 0.0
        day_stock_shares = 0.0
        day_cil = 0.0
        if apply_e22:
            mark_prices = {c: float(cl[c]) for c in ALL}
            pos, cash, applied = e22div.apply_dividends_for_date(
                dt.date().isoformat(),
                pos,
                cash,
                events,
                version=e22_version,
                mark_prices=mark_prices,
            )
            day_div = applied.cash_credit
            day_stock_shares = applied.stock_shares_added
            day_cil = applied.cil_cash_credit
            div_cash_total += applied.cash_credit
            cil_cash_total += applied.cil_cash_credit
            fractional_shares_cashed += applied.fractional_shares_cashed
            stock_div_events += applied.stock_events
            stock_div_shares_added += applied.stock_shares_added

        # 3) Mark NAV at raw close (never adj_close here)
        vals = {c: pos[c] * float(cl[c]) for c in universe}
        nav = cash + sum(vals.values())
        rg = str(regime.loc[dt]) if dt in regime.index else "Sideways"
        if rg == "Crisis":
            crisis_days += 1

        # 4) Target weights (E16) × optional named E45 exposure (or legacy Crisis proxy)
        tw = target.loc[dt]
        four_sleeve = "FinPub" in getattr(tw, "index", [])
        if four_sleeve:
            if pub_codes is None or priv_codes is None:
                raise ValueError("FinPub target requires fin_pub_codes and fin_priv_codes")
            sleeve_w = {
                "FinPub": float(tw["FinPub"]),
                "FinPriv": float(tw["FinPriv"]),
                "Telecom": float(tw["Telecom"]),
                "0050": float(tw["0050"]),
            }
        else:
            sleeve_w = {
                "Financial": float(tw["Financial"]),
                "Telecom": float(tw["Telecom"]),
                "0050": float(tw["0050"]),
            }
        equity_scale = 1.0
        if sleeve_weight_schedule is not None and dt in sleeve_weight_schedule.index:
            row = sleeve_weight_schedule.loc[dt]
            if "FinPub" in row.index and "FinPriv" in row.index:
                if pub_codes is None or priv_codes is None:
                    raise ValueError("FinPub/FinPriv schedule requires fin_pub_codes and fin_priv_codes")
                four_sleeve = True
                sleeve_w = {
                    "FinPub": float(row["FinPub"]),
                    "FinPriv": float(row["FinPriv"]),
                    "Telecom": float(row["Telecom"]),
                    "0050": float(row["0050"]),
                }
            else:
                four_sleeve = False
                sleeve_w = {
                    "Financial": float(row["Financial"]),
                    "Telecom": float(row["Telecom"]),
                    "0050": float(row["0050"]),
                }
                if "DEF" in row.index:
                    sleeve_w["DEF"] = float(row["DEF"])
                elif def_c is not None:
                    sleeve_w["DEF"] = 0.0
            equity_scale = float(sum(sleeve_w.values()))
            if sleeve_w.get("DEF", 0.0) > 0 and def_c is None:
                raise ValueError("schedule has DEF>0 but def_code was not provided")
        elif e45_exposure is not None and dt in e45_exposure.index:
            if four_sleeve:
                raise ValueError("e45_exposure not supported with FinPub/FinPriv target")
            equity_scale = float(e45_exposure.loc[dt])
            sleeve_w = e45.apply_exposure_to_sleeve_weights(
                sleeve_w, equity_scale, sleeve_names=e45_sleeve_names
            )
        elif e45_legacy_crisis_scale is not None and rg == "Crisis":
            if four_sleeve:
                raise ValueError("e45_legacy_crisis_scale not supported with FinPub/FinPriv target")
            equity_scale = float(e45_legacy_crisis_scale)
            sleeve_w = e45.apply_exposure_to_sleeve_weights(
                sleeve_w, equity_scale, sleeve_names=e45_sleeve_names
            )

        if four_sleeve:
            sleeve_vals = {
                "FinPub": sum(vals[c] for c in pub_codes),
                "FinPriv": sum(vals[c] for c in priv_codes),
                "Telecom": sum(vals[c] for c in TEL),
                "0050": vals["0050"],
            }
            sleeve_names = ["FinPub", "FinPriv", "Telecom", "0050"]
            sleeve_codes = [
                ("FinPub", pub_codes),
                ("FinPriv", priv_codes),
                ("Telecom", TEL),
                ("0050", ["0050"]),
            ]
        else:
            sleeve_vals = {
                "Financial": sum(vals[c] for c in FIN),
                "Telecom": sum(vals[c] for c in TEL),
                "0050": vals["0050"],
            }
            if def_c is not None:
                sleeve_vals["DEF"] = float(vals.get(def_c, 0.0))
                sleeve_w.setdefault("DEF", 0.0)
            sleeve_names = ["Financial", "Telecom", "0050"] + (["DEF"] if def_c is not None else [])
            sleeve_codes = [("Financial", FIN), ("Telecom", TEL), ("0050", ["0050"])]
            if def_c is not None:
                sleeve_codes.append(("DEF", [def_c]))
        pre = {k: (v / nav if nav > 0 else 0.0) for k, v in sleeve_vals.items()}
        gap = {k: float(sleeve_w.get(k, 0.0)) - pre[k] for k in pre}
        trade = np.zeros(len(sleeve_names))
        if max(abs(v) for v in gap.values()) >= 0.015:
            trade = np.array([gap[n] for n in sleeve_names]) * 0.75
            if abs(trade).sum() > 0.20:
                trade *= 0.20 / abs(trade).sum()

        # 5) Create next-day orders (signal today → fill tomorrow open)
        sleeve_trade = dict(zip(sleeve_names, trade))
        fin_scores_today = None
        if fin_name_scores is not None and dt in fin_name_scores.index:
            fin_scores_today = {
                c: float(fin_name_scores.loc[dt, c])
                for c in FIN
                if c in fin_name_scores.columns and pd.notna(fin_name_scores.loc[dt, c])
            }
        fin_buy_ok_today = None
        if fin_buy_ok is not None and dt in fin_buy_ok.index:
            fin_buy_ok_today = {
                c: bool(fin_buy_ok.loc[dt, c])
                for c in FIN
                if c in fin_buy_ok.columns
            }
        fin_sell_ok_today = None
        if fin_sell_ok is not None and dt in fin_sell_ok.index:
            fin_sell_ok_today = {
                c: bool(fin_sell_ok.loc[dt, c])
                for c in FIN
                if c in fin_sell_ok.columns
            }
        fin_sell_scores_today = None
        if fin_sell_scores is not None and dt in fin_sell_scores.index:
            fin_sell_scores_today = {
                c: float(fin_sell_scores.loc[dt, c])
                for c in FIN
                if c in fin_sell_scores.columns and pd.notna(fin_sell_scores.loc[dt, c])
            }
        tel_scores_today = None
        if tel_name_scores is not None and dt in tel_name_scores.index:
            tel_scores_today = {
                c: float(tel_name_scores.loc[dt, c])
                for c in TEL
                if c in tel_name_scores.columns and pd.notna(tel_name_scores.loc[dt, c])
            }
        tel_buy_ok_today = None
        if tel_buy_ok is not None and dt in tel_buy_ok.index:
            tel_buy_ok_today = {
                c: bool(tel_buy_ok.loc[dt, c])
                for c in TEL
                if c in tel_buy_ok.columns
            }
        for sleeve_name, codes in sleeve_codes:
            if four_sleeve and sleeve_name in ("FinPub", "FinPriv"):
                alloc = pub_alloc if sleeve_name == "FinPub" else priv_alloc
                dollars = float(sleeve_trade[sleeve_name]) * nav
                if alloc != FIN_EQUAL:
                    if abs(dollars) >= 1e-9 or alloc in (
                        "FIN_TOP1",
                        "FIN_TOP2_EQUAL",
                        FIN_MIX_EQUAL_RS_EXDIV,
                        FIN_MIX_EQUAL_PRE_EXDIV_KD,
                        FIN_DUAL_PUB_PRIV,
                        FIN_PRE_EXDIV_KD,
                    ):
                        for c, side, qty in allocate_sleeve_orders(
                            dollars,
                            {x: float(cl[x]) for x in codes},
                            pos,
                            policy_id=alloc,
                            codes=codes,
                            lot_size=lot_size,
                            scores=fin_scores_today,
                            buy_ok=fin_buy_ok_today,
                            sell_ok=fin_sell_ok_today,
                            sell_scores=fin_sell_scores_today,
                            mix_lambda=fin_mix_lambda,
                            dual_pub_codes=fin_dual_pub_codes,
                            dual_priv_codes=fin_dual_priv_codes,
                            dual_pub_policy=fin_dual_pub_policy,
                            dual_priv_policy=fin_dual_priv_policy,
                        ):
                            if qty < 1:
                                continue
                            pending.append(
                                {"signal_date": dt, "code": c, "side": side, "quantity": qty}
                            )
                    continue
                # EQUAL within FinPub/FinPriv
                if not codes:
                    continue
                value = dollars / len(codes)
                for c in codes:
                    px = float(cl[c])
                    qty = lot_qty(value, px, lot_size=lot_size)
                    if qty < 1:
                        continue
                    side = "BUY" if value > 0 else "SELL"
                    if side == "SELL":
                        held = int(pos.get(c, 0)) if lot_size == 1 else int(pos.get(c, 0) // lot_size) * lot_size
                        qty = min(qty, held)
                    if qty < 1:
                        continue
                    pending.append(
                        {"signal_date": dt, "code": c, "side": side, "quantity": qty}
                    )
                continue
            if sleeve_name == "Financial" and financial_alloc != FIN_EQUAL:
                dollars = float(sleeve_trade[sleeve_name]) * nav
                if abs(dollars) >= 1e-9 or financial_alloc in (
                    "FIN_TOP1",
                    "FIN_TOP2_EQUAL",
                    FIN_MIX_EQUAL_RS_EXDIV,
                    FIN_MIX_EQUAL_PRE_EXDIV_KD,
                    FIN_DUAL_PUB_PRIV,
                ):
                    for c, side, qty in allocate_sleeve_orders(
                        dollars,
                        {x: float(cl[x]) for x in FIN},
                        pos,
                        policy_id=financial_alloc,
                        codes=FIN,
                        lot_size=lot_size,
                        scores=fin_scores_today,
                        buy_ok=fin_buy_ok_today,
                        sell_ok=fin_sell_ok_today,
                        sell_scores=fin_sell_scores_today,
                        mix_lambda=fin_mix_lambda,
                        dual_pub_codes=fin_dual_pub_codes,
                        dual_priv_codes=fin_dual_priv_codes,
                        dual_pub_policy=fin_dual_pub_policy,
                        dual_priv_policy=fin_dual_priv_policy,
                    ):
                        if qty < 1:
                            continue
                        pending.append(
                            {"signal_date": dt, "code": c, "side": side, "quantity": qty}
                        )
                continue
            if sleeve_name == "Telecom" and telecom_alloc != TEL_EQUAL:
                dollars = float(sleeve_trade[sleeve_name]) * nav
                if abs(dollars) >= 1e-9 or telecom_alloc in (
                    "TEL_TOP1",
                    "TEL_TOP2_EQUAL",
                    TEL_MIX_EQUAL_RS_EXDIV,
                    TEL_MIX_EQUAL_PRE_EXDIV_KD,
                    TEL_RS_SOFT_TILT,
                    TEL_EXDIV_SKIP_BUY,
                    TEL_RS_SOFT_TILT_EXDIV,
                    TEL_PRE_EXDIV_KD,
                ):
                    for c, side, qty in allocate_sleeve_orders(
                        dollars,
                        {x: float(cl[x]) for x in TEL},
                        pos,
                        policy_id=telecom_alloc,
                        codes=TEL,
                        lot_size=lot_size,
                        scores=tel_scores_today,
                        buy_ok=tel_buy_ok_today,
                        mix_lambda=tel_mix_lambda,
                    ):
                        if qty < 1:
                            continue
                        pending.append(
                            {"signal_date": dt, "code": c, "side": side, "quantity": qty}
                        )
                continue
            value = sleeve_trade[sleeve_name] * nav / len(codes)
            for c in codes:
                px = float(cl[c])
                qty = lot_qty(value, px, lot_size=lot_size)
                if qty < 1:
                    continue
                side = "BUY" if value > 0 else "SELL"
                if side == "SELL":
                    held = int(pos.get(c, 0)) if lot_size == 1 else int(pos.get(c, 0) // lot_size) * lot_size
                    qty = min(qty, held)
                if qty < 1:
                    continue
                pending.append(
                    {
                        "signal_date": dt,
                        "code": c,
                        "side": side,
                        "quantity": qty,
                    }
                )

        nav_rows.append(
            {
                "date": dt.date().isoformat(),
                "nav": nav,
                "cash": cash,
                "gross_equity": sum(vals.values()),
                "equity_weight": (sum(vals.values()) / nav) if nav else 0.0,
                "regime": rg,
                "e45_equity_scale": equity_scale,
                "dividend_credit": day_div,
                "stock_shares_added": day_stock_shares,
                "cil_cash_credit": day_cil,
                "pre_financial": float(pre.get("Financial", pre.get("FinPub", 0.0) + pre.get("FinPriv", 0.0))),
                "pre_fin_pub": float(pre.get("FinPub", 0.0)),
                "pre_fin_priv": float(pre.get("FinPriv", 0.0)),
                "pre_telecom": pre["Telecom"],
                "pre_0050": pre["0050"],
                "pre_def": pre.get("DEF", 0.0),
                "tgt_financial": float(
                    sleeve_w.get("Financial", sleeve_w.get("FinPub", 0.0) + sleeve_w.get("FinPriv", 0.0))
                ),
                "tgt_fin_pub": float(sleeve_w.get("FinPub", 0.0)),
                "tgt_fin_priv": float(sleeve_w.get("FinPriv", 0.0)),
                "tgt_telecom": sleeve_w["Telecom"],
                "tgt_0050": sleeve_w["0050"],
                "tgt_def": float(sleeve_w.get("DEF", 0.0)),
            }
        )

    nav_df = pd.DataFrame(nav_rows)
    fills_df = pd.DataFrame(fill_rows)
    meta = {
        "n_days": len(nav_df),
        "n_fills": len(fills_df),
        "same_bar_fills": same_bar,
        "exact_t1_ok": same_bar == 0,
        "e22_books_version": e22_version if apply_e22 else None,
        "dividend_cash_total": div_cash_total,
        "cil_cash_total": cil_cash_total,
        "fractional_shares_cashed": round(fractional_shares_cashed, 6),
        "stock_div_events": stock_div_events,
        "stock_div_shares_added": round(stock_div_shares_added, 4),
        "apply_stock_div": bool(apply_e22 and apply_stock_div),
        "crisis_days": crisis_days,
        "start": nav_df["date"].iloc[0] if len(nav_df) else None,
        "end": nav_df["date"].iloc[-1] if len(nav_df) else None,
        "mean_e45_exposure": float(nav_df["e45_equity_scale"].mean()) if len(nav_df) else None,
        "cost_multiple": float(cm),
        "e45_sleeve_names": list(e45_sleeve_names) if e45_sleeve_names else None,
        "def_code": def_c,
        "end_positions": {k: round(v, 4) for k, v in pos.items()},
        "lot_size": int(lot_size),
        "financial_alloc": str(financial_alloc),
        "fin_mix_lambda": None if fin_mix_lambda is None else float(fin_mix_lambda),
        "telecom_alloc": str(telecom_alloc),
        "e22_manifest": e22div.version_manifest(e22_version) if apply_e22 else None,
    }
    return nav_df, fills_df, meta


def nav_stats(nav: pd.DataFrame, col: str = "nav") -> dict:
    if nav is None or len(nav) < 2:
        return {"cagr": None, "max_drawdown": None, "utility": None, "vol": None}
    r = nav[col].pct_change().dropna().to_numpy()
    path = nav[col].to_numpy()
    years = len(r) / 252.0
    cagr = float((path[-1] / path[0]) ** (1.0 / years) - 1.0) if years > 0 and path[0] > 0 else None
    peak = np.maximum.accumulate(path)
    mdd = float(np.min(path / peak - 1.0))
    vol = float(np.std(r, ddof=1) * np.sqrt(252)) if len(r) > 2 else None
    util = (0.0 if cagr is None else cagr) - 0.5 * abs(0.0 if mdd is None else mdd)
    return {"cagr": cagr, "max_drawdown": mdd, "utility": util, "vol": vol, "n_days": len(nav)}


def verify_e45_claim(repo: Path) -> dict:
    """Pointer to retired handoff MDD narrative docs (no numeric restatement)."""
    import e45_crisis_core as e45_mod

    retirement = repo / "research" / "ops" / "E45_MDD_1316_NARRATIVE_RETIREMENT.md"
    verification = repo / "research" / "e45" / "E45_MDD_1316_VERIFICATION.md"
    return {
        "claim_mdd": None,
        "claim_status": CLAIM_STATUS,
        "retirement_doc": str(retirement.relative_to(repo)) if retirement.exists() else None,
        "verification_doc": str(verification.relative_to(repo)) if verification.exists() else None,
        "primary_comparable_mdd": e45_mod.PRIMARY_COMPARABLE_MDD,
        "primary_comparable_source": e45_mod.PRIMARY_COMPARABLE_SOURCE,
        "verified_lineage_mdd": dict(e45_mod.VERIFIED_LINEAGE_MDD),
        "e45_module_paths": [str(p.relative_to(repo)) for p in (repo / "scripts").glob("e45*")],
        "conclusion": (
            "Named module scripts/e45_crisis_core.py exists; live stitch remains DEFERRED. "
            "Handoff MDD narrative is RETIRED_HISTORICAL_NARRATIVE — see E45_MDD_1316 retirement/verification pack. "
            "Use dated lineage / PRIMARY_COMPARABLE_MDD only; do not invent a replacement. "
            "Formal live stack remains Soft-Frozen E16 + Exact T+1 E18 + E22_v2s_tw; E45 not live-wired."
        ),
    }



def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", type=Path, default=Path("forward/e21/live_market.csv"))
    ap.add_argument("--dividends", type=Path, default=Path("data/dividend_events/e22_dividend_events.csv"))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--capital", type=float, default=CAPITAL)
    ap.add_argument(
        "--e45-legacy-crisis-scale",
        type=float,
        default=0.70,
        help="Legacy ad-hoc Crisis-day scale (comparison only; not named E45)",
    )
    args = ap.parse_args()
    out = args.out
    (out / "outputs").mkdir(parents=True, exist_ok=True)
    (out / "reports").mkdir(parents=True, exist_ok=True)
    repo = Path(".").resolve()
    Path("research/e45").mkdir(parents=True, exist_ok=True)

    print("loading market / dividends ...", flush=True)
    market = pd.read_csv(args.market, dtype={"code": str})
    market["date"] = pd.to_datetime(market["date"])
    required = set(ALL + ["TAIEX"])
    complete = market.groupby("date")["code"].apply(lambda s: required.issubset(set(s)))
    keep = complete[complete].index
    market = market[market["date"].isin(keep)].sort_values(["date", "code"])
    dividends = pd.read_csv(args.dividends, dtype={"code": str}) if args.dividends.exists() else pd.DataFrame()

    print("building causal E16 targets ...", flush=True)
    _p, _sleeve, target, regime = e16_features(market)
    regime_share = regime.value_counts(normalize=True).to_dict()

    close_eq = (
        market[market["code"].isin(ALL)]
        .pivot(index="date", columns="code", values="close")
        .sort_index()
        .ffill()
    )
    print("computing named E45 exposures (E3 winner + E1 binary) ...", flush=True)
    e45_e3 = e45.compute_exposure(close_eq, "E3_VOLTARGET_WINNER")["exposure"]
    e45_e1 = e45.compute_exposure(close_eq, "E1_BINARY")["exposure"]
    e45.write_status(out / "reports" / "e45_module_status.json")
    e45.write_status(Path("research/e45/e45_status.json"))

    variants = {
        "E16_E18": dict(apply_e22=False, apply_stock_div=False, e45_exposure=None, e45_legacy_crisis_scale=None),
        # preserved cash-only baseline label (E22_v2)
        "E16_E18_E22_V2": dict(
            apply_e22=True, apply_stock_div=False, e45_exposure=None, e45_legacy_crisis_scale=None
        ),
        # formal books (E22_v2s): cash + stock share increase on stock_ex_date
        "E16_E18_E22": dict(apply_e22=True, apply_stock_div=True, e45_exposure=None, e45_legacy_crisis_scale=None),
        "E16_E18_E22_E45LEGACY": dict(
            apply_e22=True,
            apply_stock_div=True,
            e45_exposure=None,
            e45_legacy_crisis_scale=args.e45_legacy_crisis_scale,
        ),
        "E16_E18_E22_E45_E3": dict(
            apply_e22=True, apply_stock_div=True, e45_exposure=e45_e3, e45_legacy_crisis_scale=None
        ),
        "E16_E18_E22_E45_E1": dict(
            apply_e22=True, apply_stock_div=True, e45_exposure=e45_e1, e45_legacy_crisis_scale=None
        ),
    }
    results = {}
    for name, cfg in variants.items():
        print(f"simulating {name} ...", flush=True)
        nav, fills, meta = simulate_core(
            market, target, regime, dividends, capital=args.capital, **cfg
        )
        stats = nav_stats(nav)
        nav.to_csv(out / "outputs" / f"{name.lower()}_daily_nav.csv", index=False)
        fills.to_csv(out / "outputs" / f"{name.lower()}_fills.csv", index=False)
        results[name] = {
            "stats": stats,
            "meta": meta,
            "apply_e22": cfg["apply_e22"],
            "apply_stock_div": cfg.get("apply_stock_div", False),
            "e45_profile": (
                "E3_VOLTARGET_WINNER" if name.endswith("E45_E3")
                else "E1_BINARY" if name.endswith("E45_E1")
                else "LEGACY_CRISIS_SCALE" if name.endswith("E45LEGACY")
                else None
            ),
        }
        print(
            f"  {name}: CAGR={stats['cagr']:.4f} MDD={stats['max_drawdown']:.4f} "
            f"util={stats['utility']:.4f} fills={meta['n_fills']} "
            f"mean_exp={meta.get('mean_e45_exposure')}",
            flush=True,
        )

    e45_audit = verify_e45_claim(repo)
    e45_audit["named_module"] = "scripts/e45_crisis_core.py"
    e45_audit["named_module_status"] = e45.MODULE_STATUS
    e45_audit["promotion_allowed"] = e45.PROMOTION_ALLOWED
    a = results["E16_E18"]["stats"]
    b = results["E16_E18_E22"]["stats"]
    b_cash = results["E16_E18_E22_V2"]["stats"]
    e3s = results["E16_E18_E22_E45_E3"]["stats"]
    e1s = results["E16_E18_E22_E45_E1"]["stats"]

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "stage": "EARLY_STACK_COMBINED_NAV_WITH_NAMED_E45",
        "governance": {
            "modifies_soft_frozen_files": False,
            "e45_module_path": "scripts/e45_crisis_core.py",
            "e45_module_status": e45.MODULE_STATUS,
            "e45_promoted": False,
            "label": "EXPERIMENTAL_CHALLENGER_SANDBOX",
            "e22_formal_books": e22div.E22_V2S,
            "e22_preserved_cash_only": e22div.E22_V2,
        },
        "e45_manifest": e45.manifest_dict(),
        "inputs": {
            "market": str(args.market),
            "dividends": str(args.dividends),
            "capital": args.capital,
            "core_universe": ALL,
            "stock_div_unit": "FinMind_yuan_per_share",
            "stock_share_factor": "1 + stock_dividend/10",
        },
        "regime_share": {str(k): float(v) for k, v in regime_share.items()},
        "variants": results,
        "deltas": {
            "e22_minus_e16e18_cagr": metric_delta(b["cagr"], a["cagr"], missing_as_zero=True),
            "e22_stock_minus_cash_only_cagr": metric_delta(b["cagr"], b_cash["cagr"], missing_as_zero=True),
            "e22_stock_minus_cash_only_mdd": metric_delta(b["max_drawdown"], b_cash["max_drawdown"], missing_as_zero=True),
            "e45_e3_minus_e22_cagr": metric_delta(e3s["cagr"], b["cagr"], missing_as_zero=True),
            "e45_e3_minus_e22_mdd": metric_delta(e3s["max_drawdown"], b["max_drawdown"], missing_as_zero=True),
            "e45_e1_minus_e22_cagr": metric_delta(e1s["cagr"], b["cagr"], missing_as_zero=True),
            "e45_e1_minus_e22_mdd": metric_delta(e1s["max_drawdown"], b["max_drawdown"], missing_as_zero=True),
            "e22_dividend_cash_total": results["E16_E18_E22"]["meta"]["dividend_cash_total"],
            "e22_stock_div_events": results["E16_E18_E22"]["meta"]["stock_div_events"],
            "e22_stock_div_shares_added": results["E16_E18_E22"]["meta"]["stock_div_shares_added"],
        },
        "e45_verification": e45_audit,
        "decisions": {
            "e16_full_history_reconstruction": "DONE_IN_CHALLENGER",
            "e22_wired_into_nav_copy": "DONE_IN_CHALLENGER",
            "e22_stock_share_increase": "DONE_IN_CHALLENGER_ON_STOCK_EX_DATE",
            "e22_v2_official_cash_only_unchanged": True,
            "e45_named_module": "CREATED_CHALLENGER_CANDIDATE",
            "e45_promoted_to_soft_frozen_critical": False,
            "e45_mdd_claim_13_16": e45_audit["claim_status"],
            "combined_four_layer_engine": "CORE_EXEC_DIV_PLUS_NAMED_E45_CANDIDATE",
            "next": (
                "Named module scripts/e45_crisis_core.py exists and is wired. "
                "Stock dividends applied in challenger only. Promote stock-aware E22 "
                "only via explicit new version + governance approval."
            ),
        },
    }
    (out / "reports" / "early_stack_combined_nav_summary.json").write_text(
        json.dumps(report, indent=2, default=str) + "\n"
    )
    lines = [
        "# Early-Stack Combined NAV + Named E45 Module",
        "",
        "**EXPERIMENTAL.** Named E45 exists but is **not** promoted to SOFT_FROZEN_CRITICAL.",
        "",
        f"Module: `scripts/e45_crisis_core.py` — `{e45.MODULE_STATUS}`",
        "",
        "## Results",
        "",
        "| Variant | CAGR | MDD | Util | Mean E45 exp |",
        "|---|---:|---:|---:|---:|",
    ]
    for name in variants:
        s = results[name]["stats"]
        m = results[name]["meta"]
        lines.append(
            f"| {name} | {fmt_pct(s['cagr'])} | {fmt_pct(s['max_drawdown'])} | "
            f"{s['utility']:.4f} | {m.get('mean_e45_exposure')} |"
        )
    lines += [
        "",
        f"- E22 CAGR lift: `{report['deltas']['e22_minus_e16e18_cagr']:.4%}`",
        f"- Stock vs cash-only CAGR: `{report['deltas']['e22_stock_minus_cash_only_cagr']:.4%}`",
        f"- Stock div events / shares added: "
        f"`{report['deltas']['e22_stock_div_events']}` / `{report['deltas']['e22_stock_div_shares_added']}`",
        f"- E45-E3 MDD delta vs E22: `{report['deltas']['e45_e3_minus_e22_mdd']:.4%}`",
        f"- Retired MDD narrative: `{CLAIM_STATUS}`",
        "",
        "## Decisions",
        "",
    ]
    for k, v in report["decisions"].items():
        lines.append(f"- `{k}`: {v}")
    lines += ["", "See `research/e45/E45_MODULE_STATUS.md`.", ""]
    (out / "EARLY_STACK_COMBINED_NAV.md").write_text("\n".join(lines))
    print(json.dumps({"decisions": report["decisions"], "deltas": report["deltas"]}, indent=2, default=str))


if __name__ == "__main__":
    main()
