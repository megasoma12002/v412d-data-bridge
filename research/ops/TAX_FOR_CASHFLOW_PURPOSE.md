# Tax purpose = precise cashflow

Date: 2026-09-20  
Status: **OPS POLICY** — Soft-Frozen **KEEP**  
Human (2026-09-20):「稅的目的是要有精準的現金流」  
SSOT peers: `CASHFLOW_THREE_VIEWS.md` · `NHI_DIVIDEND_SUPPLEMENTAL_PREMIUM_NOTE.md` · ballot A `E22_V3_WITHHOLDING_RESIDENT_NOTE.md`

## Policy

In this stack, **tax / withholding modeling exists to make cashflow numbers match custody**, not to decorate Soft-Frozen NAV with year-end 所得稅 theater.

| Layer | In scope for cashflow precision? | This cycle |
|---|---|---|
| Stage-E timing (recv on effective ex → cash on effective pay) | **Yes** — already live DEFAULT | `E22_v3_recv_pay_effdelay` |
| Trade T+2 settled cash (R4) | **Yes** — liquidity view ≠ NAV | observe |
| **NHI 補充保費** 單次股利 ≥ NT$20k → 2.11% 就源扣 | **Yes** — changes pay-day cash | research sandbox `E22_v3_recv_pay_effdelay_nhi211` · **not** live |
| Flat `tax10`/`tax20` sandboxes | Sensitivity only | research-only |
| 本國人股利所得稅（合併／分開 28%） | **No** for daily books | ballot **A KEEP TAX0** — year-end outside NAV |

## Implication

- Ballot A does **not** mean “ignore all tax for cashflow.” It means **year-end personal income tax stays outside daily NAV**.  
- Cash-affecting withholdings (NHI) are the **next** cashflow-precision candidates.  
- Promote NHI (or any haircut) into live DEFAULT only with a **dedicated** human ballot + PR — never silent.

## Sandbox for NHI cashflow precision

```text
E22_v3_recv_pay_effdelay_nhi211
```

- Same Stage-E clocks as live DEFAULT.  
- On cash-div accrual: if single gross credit ≥ 20,000 → receivable/net = gross − 2.11%×min(gross, 1e7).  
- Below threshold → TAX0 gross (same as live).  
- `promote_ready=false`.

## Label

`TAX_FOR_CASHFLOW_PURPOSE__2026-09-20`
