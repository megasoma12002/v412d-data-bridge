# Odd-Lot Promote Checklist — `E22_v2s_tw`

Date: 2026-09-05  
Status: **DEFERRED** — named research books only; Soft-Frozen default remains **`E22_v2s`**.

Authority: `research/e22/GAP65_ODD_LOT_CLOSEOUT.md` · `scripts/e22_dividend_accounting.py` · Gap #6 brief: `research/e22/EXECUTION_DETAIL_GAP6_BRIEF.md`

## What this is

Taiwan corporate-practice odd-lot cash-in-lieu books:

- Floor whole shares on stock ex
- CIL = `floor(frac × par NT$10)` (元以下捨去)
- Does **not** force board-lot 1000

## Promote gates (all required)

| # | Gate | Pass when |
|---|---|---|
| 1 | Explicit human governance approval | Written OK to change `DEFAULT_BOOKS_VERSION` |
| 2 | Separate PR (this checklist green) | PR title names promote; not buried in ops cleanup |
| 3 | Cutover-forward only | Idempotent `dividends_applied` keys; **no** `forward/e21` history rewrite |
| 4 | Exact T+1 unchanged | No fill-clock edit |
| 5 | Soft-Frozen clip unchanged | Financial **[0.50, 0.95]** KEEP unless separate clip PR |
| 6 | Ops note | One-line update in `OPS_STATUS.md` + `FROZEN_STRATEGY_SPEC` books line |
| 7 | Side-by-side evidence attached | Point at `repro/e22-tw-odd-lot-apply/` (CAGR ≈ −0.0005 pp vs v2s) |

## Explicit non-promote

- Do **not** silently set `DEFAULT_BOOKS_VERSION = E22_v2s_tw`
- Do **not** treat Gap #6.5 research closeout as live cutover license
- Board-lot 1000 remains E18 challenger only

## After promote (ops)

1. Re-run `scripts/e22_gap6_fidelity_kpi.py` — expect default = `E22_v2s_tw`
2. Month-end pack should show live evidence fields on next forward session
3. Update five-layer Layer 3: odd-lot **DONE** (promoted)
