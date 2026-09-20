# E22_v3 withholding — resident / non-resident note (sandbox)

Date: 2026-09-06 · **amended 2026-09-20**  
Status: **SANDBOX RESEARCH NOTE** — Soft-Frozen **KEEP** · live DEFAULT **`E22_v3_recv_pay_effdelay` (TAX0)** · **no tax promote**  
Related: `FORMAL_TAX_RECEIVABLE_BOOKS_CHARTER.md` · `E22_V3_TAX_RECV_STAGE_B_STATUS.md` · register #6b

## Purpose

Stage B has sealed evidence for **flat** sandbox haircuts (`tax10` / `tax20` and combined `recv_pay_tax10` / `recv_pay_tax20`).  
Flat haircuts are **not** by themselves a Taiwan resident tax opinion. This note records what must be written before any **tax** DEFAULT promote ballot.

## Human decisions recorded

| Topic | Decision | When | Source |
|---|---|---|---|
| Holder residency | **本國居住者（本國人）** — portfolio modeled as Taiwan **domestic resident** holder | 2026-09-20 | Human message in ops thread |

**Effect of residency = 本國人：** non-resident withholding / treaty tables are **out of scope** for the first tax promote path. Sandbox `tax10`/`tax20` remain **sensitivity probes only** until a resident-appropriate rate + timing rule is chosen (TW resident dividend tax is **not** automatically the same as flat non-resident withholding).

## What the sandbox does today

| Version | Cash timing | Withholding model |
|---|---|---|
| `E22_v3_tax10` / `tax20` | Cash on ex | Flat 10% / 20% of gross |
| `E22_v3_recv_pay_tax10` / `tax20` | Receivable on ex (net); cash on pay | Same flat net on receivable |

Assumptions baked in (still):

- One flat rate for **all** names (no per-issuer branch yet)
- No treaty relief, no tax ID branching, no credit/refund ledger
- Stock / CIL path remains TW odd-lot family

## Promote gate checklist

| Topic | Status | Promote gate |
|---|---|---|
| Holder residency | **DECIDED** — 本國居住者（本國人） | ✓ |
| Treaty overlays | **N/A for v1 path** (resident-only) — confirm “ignore treaties in resident v1” | Needs explicit KEEP / waive line |
| Resident tax **rate / method** | **OPEN** — consolidated income vs optional separate taxation vs modeling haircut; cite rule | Written rule + source cite |
| Timing | **OPEN** — withhold/recognize on ex vs on payment | Must match chosen book version |
| Refunds / credits | **OPEN** — over-withheld amounts receivable? | Yes/No + ledger fields |
| Issuer exceptions | **OPEN** — Financials / ETFs / special distributions | Include/exclude list |

Until **rate/method + timing + refunds + exceptions** are answered (and treaty waive confirmed), **`promote_ready=false`** for every `E22_v3_*tax*` sandbox version.

Live timing DEFAULT (`E22_v3_recv_pay_effdelay`, **TAX0**) is **unchanged** by this residency decision.

## Non-actions

- No tax DEFAULT flip · no Soft-Frozen flip · no live ledger rewrite · no backfill of `forward/e21` history  
- Do **not** treat human「本國人」as ACCEPT of `tax10` or `tax20` DEFAULT

## Next human ballot (when ready)

One of:

1. **KEEP TAX0** (timing-only live; tax stays sandbox forever this cycle)  
2. **Pick resident modeling rule** (rate/method + timing + refunds) → then dedicated tax promote checklist + PR  

## Label

`E22_V3_WITHHOLDING_RESIDENT_NOTE__RESIDENT_DOMESTIC_2026-09-20__PROMOTE_READY_FALSE`
