# Cashflow three-views report

Generated: `2026-09-21T15:23:20.160146+00:00`
Tip `last_date`: `2026-09-21` · Soft-Frozen **KEEP**
Human priority: **計算好現金流的數字** (TAX0; tax outside daily NAV)

## Views

| View | Meaning | Number |
|---|---|---|
| **A** | Exact T+1 paper cash | `50415.51358572836` |
| **B** | R4 settled_cash_estimate | `50415.51358572836` |
| **B′** | R4 unsettled_net | `0.0` |
| **C** | Stage-E cash | `50415.51358572836` |
| **C′** | e22_receivables total | `0.0` |
| **C″** | cash + receivable | `50415.51358572836` |

- tip books: `E22_v3_recv_pay_effdelay` · tip_lag: **False**
- R4 identity_ok: `True` · present: `True`

## Warnings

- None

## Next ops

- Phase 2 tip catch-up CONFIRMED — tip == Stage-E DEFAULT; View C clock live
- On dividend ex→pay days: watch e22_receivables + dividends_applied (Gap6 G7)
- Keep R4 daily observe — View B is liquidity SSOT
- When custody export exists → R5 reconcile vs View B (observe-only)
- Do not merge A/B/C clocks; do not after-tax DEFAULT this cycle
- NHI 2.11% on single div pay ≥20k is custody haircut research-only — see NHI_DIVIDEND_SUPPLEMENTAL_PREMIUM_NOTE.md

Re-run: `python3 scripts/cashflow_three_views_report.py --write`

Label: `CASHFLOW_THREE_VIEWS_REPORT`
