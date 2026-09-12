# E22 Dividend Amount Repair — Operating Note

Date: 2026-09-12  
Status: **OPERATING** (live load path)  
Soft-Frozen / Soft-assist / Sleeve-tilt / E45 / DEFAULT books: **UNCHANGED**

## What

If `data/dividend_events/e22_dividend_events.csv` has a non-empty `cash_dividend` /
`stock_dividend` cell that is not a float, live used to either:

- (old) silently treat as 0 and skip the event, or  
- (fail-closed only) stop the day with `ValueError`

Now live **repairs once**, then reloads fail-closed:

1. Scan dirty amount cells  
2. Refetch by code (FinMind → Yahoo TW → Yuanta ETF for `0050`)  
3. Patch only those cells; atomic CSV rewrite  
4. Write `research/ops/E22_DIVIDEND_AMOUNT_REPAIR.{json,md}`  
5. Reload with fail-closed amounts  

If still unparseable after repair → **still stop** (no silent 0).

## Paths

| Role | Path |
|---|---|
| Module / CLI | `scripts/e22_dividend_amount_repair.py` |
| Live wire | `scripts/e21_forward_pipeline.py` (default on) |
| Escape hatch | `python3 scripts/e21_forward_pipeline.py --no-div-amount-repair` |
| Manual ops | `python3 scripts/e22_dividend_amount_repair.py [--dry-run] [--codes 2880,0050]` |

## Non-actions

- No Soft-Frozen clip flip  
- No Soft-assist / Sleeve-tilt live wire  
- No Soft×Sleeve combo  
- No rewrite of `forward/e21` applied dividend history  
- Empty amount cells remain empty (not treated as dirty)

## Label

`E22_DIVIDEND_AMOUNT_REPAIR_OPERATING_2026-09-12__LIVE_LOAD_ONCE__FAIL_CLOSED`
