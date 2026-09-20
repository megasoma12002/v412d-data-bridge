# Phase 3 + 5 landed — R4/tip alerts + dividend cron

Date: 2026-09-20  
Status: **LANDED (this PR)** — Soft-Frozen **KEEP** · no tax/broker/alpha promote  
Roadmap: `REALISM_AUTOMATION_GAP_CLOSE_2026-09-20.md`

## Phase 3 — R4 continuous observe

`scripts/ops_alert_scan.py` now emits:

| Code | Severity | Meaning |
|---|---|---|
| `R4_ESTIMATE_MISSING` | HIGH | CSV/JSON missing or empty |
| `R4_ESTIMATE_PRESENT` | INFO | Present; **liquidity ≠ NAV** |
| `R4_SUMMARY_SCHEMA` | INFO | Summary keys incomplete |
| `TIP_LAG_BOOKS` | INFO | Tip ≠ Stage-E DEFAULT (authorized) |

## Phase 5 — Dividend data cadence

`.github/workflows/v412e22-dividend-events.yml`: weekday cron `0 7 * * 1-5` (≈15:00 Taipei), fetch-only `data/dividend_events/`.  
Optional alert `DIV_APPLIED_MISSING_IN_RECV_WINDOW` when Stage-E tip + receivable window open + no `dividends_applied.csv`.

## Non-actions

No Soft-Frozen flip · no forward history rewrite · no R5/tax/broker promote · no Phase 2 tip invent on weekend.

## Label

`PHASE_3_5_REALISM_AUTOMATION_LANDED_2026-09-20`
