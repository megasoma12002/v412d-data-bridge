# E22_v3 H1 — Payment Date vs Ex Date

Date: **2026-09-04**  
Baseline: **`E22_v2_CASH_EX_OFFICIAL_PATH`** (unchanged)  
Sandbox: `repro/e22-v3-h1-20260904`

## Coverage

| Metric | Value |
|---|---|
| Cash events | 144 |
| With payment date | 144 (100.0%) |
| Missing | 0 |

## H1 result (TAX0)

| Book | CAGR | MDD | Util |
|---|---:|---:|---:|
| EX_DATE (v2 rule) | 11.2488% | -22.1095% | 0.001941 |
| PAY_DATE (H1) | 11.5065% | -22.1829% | 0.004151 |
| Δ (pay − ex) | 0.2577% | | 0.002210 |

Pre-registered bar: util lift > **0.002** and MDD not worse by > **0.005**.  
`pay_beats_ex` = **True**  
Exact T+1 all books: **True**

## Decision

**`H1_PAY_DATE_INTERESTING_CONTINUE_SANDBOX`**

Challenger payment-date credit clears pre-registered bar vs ex-date; still NO auto-promote.

- Promotion: **False** (needs explicit approval even if interesting)
- Official path remains ex-date credit under `forward/e22_v2/`
