# E22 Challenger Forward (paper parallel)

**Status:** `PAPER_EXPERIMENTAL` → promotion package awaiting approval

- Path: `forward/e22_challenger/`
- Same E16 targets / Exact T+1 as E21
- **Plus** cash dividend credits on `cash_ex_date`
- Does **not** edit `forward/e21/`
- Bootstrap from **2026-07-01** (covers 2026 cash ex-dates) through latest market date

## QC

PASS — Exact T+1, audit chain, universe checks

Dividend cash total (paper): ~84,353 on 3M capital (5 credit days)

## Promotion

See `research/e22/E22_PROMOTION_PACKAGE.md`  
Proposed: `E22_v2_CASH_EX_OFFICIAL_PATH`  
**Requires explicit human approval before cutover.**
