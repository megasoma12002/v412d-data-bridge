# E22_v3 withholding — resident / non-resident note (sandbox)

Date: 2026-09-06  
Status: **SANDBOX RESEARCH NOTE** — Soft-Frozen **KEEP** · DEFAULT **`E22_v2s_tw` KEEP** · no promote  
Related: `FORMAL_TAX_RECEIVABLE_BOOKS_CHARTER.md` · `E22_V3_TAX_RECV_STAGE_B_STATUS.md`

## Purpose

Stage B now has sealed evidence for **flat** sandbox haircuts (`tax10` / `tax20` and combined `recv_pay_tax10` / `recv_pay_tax20`).  
Flat haircuts are **not** a Taiwan resident/non-resident tax opinion. This note records what must be written before any promote ballot.

## What the sandbox does today

| Version | Cash timing | Withholding model |
|---|---|---|
| `E22_v3_tax10` / `tax20` | Cash on ex | Flat 10% / 20% of gross |
| `E22_v3_recv_pay_tax10` / `tax20` | Receivable on ex (net); cash on pay | Same flat net on receivable |

Assumptions baked in:

- One flat rate for **all** names / all holders
- No treaty relief, no tax ID branching, no credit/refund ledger
- Stock / CIL path remains `E22_v2s_tw` odd-lot

## Resident vs non-resident (required before promote)

| Topic | Open question | Promote gate |
|---|---|---|
| Holder residency | TW resident vs non-resident withholding base rate | Written rule + source cite |
| Treaty overlays | Which domiciles get reduced rates | Explicit table or “ignore treaties in v3” |
| Timing | Withhold on ex vs on payment | Must match chosen book version |
| Refunds / credits | Are over-withheld amounts receivable? | Yes/No + ledger fields |
| Issuer exceptions | Financials / ETFs / special distributions | Include/exclude list |

Until those are answered in a human-accepted appendix, **`promote_ready=false`** for every `E22_v3_*` sandbox version.

## Non-actions

- No DEFAULT flip · no Soft-Frozen flip · no live ledger rewrite · no backfill of `forward/e21` history

## Label

`E22_V3_WITHHOLDING_RESIDENT_NOTE_2026-09-06__SANDBOX_ONLY`
