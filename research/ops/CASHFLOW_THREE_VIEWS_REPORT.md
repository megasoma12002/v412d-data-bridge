# Cashflow three-views report

Generated: `2026-09-20T03:14:07.493841+00:00`
Tip `last_date`: `2026-09-16` · Soft-Frozen **KEEP**
Human priority: **計算好現金流的數字** (TAX0; tax outside daily NAV)

## Views

| View | Meaning | Number |
|---|---|---|
| **A** | Exact T+1 paper cash | `50415.51358572836` |
| **B** | R4 settled_cash_estimate | `1022.172182977898` |
| **B′** | R4 unsettled_net | `49393.34140275046` |
| **C** | Stage-E cash | `50415.51358572836` |
| **C′** | e22_receivables total | `0.0` |
| **C″** | cash + receivable | `50415.51358572836` |

- tip books: `E22_v2s_tw_effex` · tip_lag: **True**
- R4 identity_ok: `True` · present: `True`

## Warnings

- TIP_LAG: tip books=E22_v2s_tw_effex (preserved cash-on-ex) vs DEFAULT=E22_v3_recv_pay_effdelay; View C receivable clock not on tip yet — weekday forward catch-up required
- TIP still cash-on-ex: e22_receivables empty/absent is expected until Stage-E tip

## Next ops

- Weekday tip → E22_v3_recv_pay_effdelay (Phase 2) so View C receivable lands
- Keep R4 daily observe — View B is liquidity SSOT
- When custody export exists → R5 reconcile vs View B (observe-only)
- Do not merge A/B/C clocks; do not after-tax DEFAULT this cycle

Re-run: `python3 scripts/cashflow_three_views_report.py --write`

Label: `CASHFLOW_THREE_VIEWS_REPORT`
