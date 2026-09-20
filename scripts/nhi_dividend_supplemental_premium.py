#!/usr/bin/env python3
"""NHI dividend supplemental premium (二代健保補充保費) — research helper.

Human note (2026-09-20): 股利單次給付達 NT$20,000 需扣補充保費.

This is **not** year-end 所得稅 (ballot A KEEP TAX0). It is a **withholding at
pay** that can change custody cash vs Stage-E TAX0 gross credits.

Live books: **not wired** — Soft-Frozen KEEP · research / cashflow fidelity only.
Authority: ``research/ops/NHI_DIVIDEND_SUPPLEMENTAL_PREMIUM_NOTE.md``.
"""
from __future__ import annotations

from dataclasses import dataclass

# NHI published personal supplemental rate (since 2021-01-01; still cited 114 宣導).
NHI_SUPPLEMENTAL_RATE = 0.0211
# Single payment threshold: 達 20,000 → full base × rate (not excess-only).
NHI_DIVIDEND_THRESHOLD_TWD = 20_000.0
# Single payment base cap.
NHI_DIVIDEND_BASE_CAP_TWD = 10_000_000.0


@dataclass(frozen=True)
class NhiDividendPremium:
    gross_twd: float
    threshold_twd: float
    rate: float
    base_cap_twd: float
    applies: bool
    taxable_base_twd: float
    premium_twd: float
    net_cash_twd: float


def nhi_dividend_premium(
    gross_twd: float,
    *,
    rate: float = NHI_SUPPLEMENTAL_RATE,
    threshold_twd: float = NHI_DIVIDEND_THRESHOLD_TWD,
    base_cap_twd: float = NHI_DIVIDEND_BASE_CAP_TWD,
) -> NhiDividendPremium:
    """Estimate personal NHI supplemental premium on one dividend payment.

    Rule (健保署): 單次股利給付達 2 萬 → 就源扣繳；達門檻以**全額**計費
    （非僅超過部分）；單次計費上限 1,000 萬。

    ``gross_twd`` should be the same-payer / same-base-date cash+stock dividend
    base the withholder uses (stock typically at par for NHI — see note).
    """
    g = float(gross_twd)
    if g < 0:
        raise ValueError("gross_twd must be >= 0")
    applies = g >= float(threshold_twd)
    base = min(g, float(base_cap_twd)) if applies else 0.0
    premium = base * float(rate) if applies else 0.0
    return NhiDividendPremium(
        gross_twd=g,
        threshold_twd=float(threshold_twd),
        rate=float(rate),
        base_cap_twd=float(base_cap_twd),
        applies=applies,
        taxable_base_twd=base,
        premium_twd=premium,
        net_cash_twd=g - premium,
    )
