# Odd-Lot Promote Checklist — `E22_v2s_tw`

Date: 2026-09-05  
Status: **PROMOTED** — human **ACCEPT promote** 2026-09-05; Soft-Frozen clip **[0.50, 0.95] KEEP**.  
Decision pack (ballot): `research/ops/ODD_LOT_PROMOTE_DECISION_PACK.md` — **ACCEPT promote**  
Live default books: **`E22_v2s_tw`** (forward-only; no `forward/e21` history rewrite)

Authority: `research/e22/GAP65_ODD_LOT_CLOSEOUT.md` · `scripts/e22_dividend_accounting.py` · Gap #6 brief: `research/e22/EXECUTION_DETAIL_GAP6_BRIEF.md`

## What this is

Taiwan corporate-practice odd-lot cash-in-lieu books:

- Floor whole shares on stock ex
- CIL = `floor(frac × per-code par)` (元以下捨去; Soft-Frozen FIN+telecom VERIFIED NT$10)
- Does **not** force board-lot 1000

## Promote gates (all required)

| # | Gate | Pass when | Status |
|---|---|---|---|
| 1 | Explicit human governance approval | Written OK to change `DEFAULT_BOOKS_VERSION` | **YES** — ACCEPT promote 2026-09-05 |
| 2 | Separate PR (this checklist green) | PR title names promote; not buried in ops cleanup | **YES** — this promote PR |
| 3 | Cutover-forward only | Idempotent `dividends_applied` keys; **no** `forward/e21` history rewrite | **YES** |
| 4 | Exact T+1 unchanged | No fill-clock edit | **YES** |
| 5 | Soft-Frozen clip unchanged | Financial **[0.50, 0.95]** KEEP | **YES** |
| 6 | Ops note | One-line update in `OPS_STATUS.md` + `FROZEN_STRATEGY_SPEC` books line | **YES** |
| 7 | Side-by-side evidence attached | Point at `repro/e22-tw-odd-lot-apply/` (CAGR ≈ −0.0005 pp vs v2s) | **YES** |
| 8 | Par inventory promote-gate | Soft-Frozen FIN + telecom VERIFIED | **YES** — TWSE 2026-09-04 |

## Explicit non-actions (still forbidden)

- Soft-Frozen clip flip  
- Tax / receivable formal books (Item 2 — still queued)  
- E45 live stitch (Item 3 — still queued)  
- `forward/e21` history rewrite  
- Board-lot 1000 as formal books  

## After promote (ops)

1. Re-run `scripts/e22_gap6_fidelity_kpi.py` — expect default = `E22_v2s_tw` (**done on promote PR**)
2. Month-end pack should show live evidence fields on next forward session
3. Five-layer Layer 3: odd-lot **DONE** (promoted)
4. Park Register #6 Item 1 → Item 2 may open next
