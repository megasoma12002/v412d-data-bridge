# E22 TAX0 vs NHI211 — observe-only

Generated: `2026-09-20T08:50:50.659911+00:00`
Status: **OBSERVE** · Soft-Frozen **KEEP** · `promote_ready=false` · **no** live NHI wire

## Method

- Focused FIN cash-event walk (sealed_2023_plus+), not full sealed day-walk. Stage-E effective ex/pay via load_calendar_window; NHI via nhi_dividend_supplemental_premium on tip (or --shares) position sizes.
- TAX0 (live DEFAULT): `E22_v3_recv_pay_effdelay`
- NHI211 sandbox: `E22_v3_recv_pay_effdelay_nhi211`
- Window: cash events with `ex_date >= 2023-01-01` on FIN `2880, 2886, 2892, 5880`
- Shares: `tip_portfolio_state` → `{'2880': 2704000.0, '2886': 2293000.0, '2892': 3183000.0, '5880': 4281000.0}`
- NHI rule: single gross ≥ NT$20,000 → 2.11% on full base (cap 10M)

## Summary

| Metric | Value |
|---|---|
| Cash events | 16 |
| Events ≥ NHI threshold | 16 |
| Σ gross TAX0 | 49,593,280.00 |
| Σ net NHI211 | 48,546,861.79 |
| Σ NHI premium | 1,046,418.21 |
| Σ delta (NHI − TAX0) | -1,046,418.21 |

## Posture

- Live DEFAULT remains **TAX0 gross** Stage-E.
- Sandbox NHI211 is cashflow-precision research only.
- Tip history / Soft-Frozen untouched.

Peers: `NHI_DIVIDEND_SUPPLEMENTAL_PREMIUM_NOTE.md` · `TAX_FOR_CASHFLOW_PURPOSE.md`

## Label

`E22_TAX0_VS_NHI211_OBSERVE__2026-09-20`
