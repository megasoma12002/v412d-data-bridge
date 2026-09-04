# E22 Dividend Ledger Completeness (Cash + Stock)

Date: 2026-09-04  
File: `data/dividend_events/e22_dividend_events.csv`  
Governance: Does **not** rewrite SOFT_FROZEN E22_v2 (cash credit on `cash_ex_date` only).

## Cash dividends — completed

| Field | Status (n=144 cash events) |
|---|---|
| `cash_ex_date` | Complete |
| `cash_dividend` (元/股) | Complete (FinMind) |
| `cash_payment_date` | Complete — **0 missing** |

- **main** still had **29** blank `cash_payment_date` rows (mostly 2010–2014 FinMind/MOPS gaps).
- This branch filled all 29 from Yahoo TW「現金股利發放日」 (`scripts/e22_backfill_payment_dates_yahoo.py` / combined `e22_backfill_div_payment_dates_yahoo.py`).
- Provenance: `data/dividend_events/e22_payment_date_yahoo_backfill.json` (`n_updated=29`, `n_still_missing=0`).

### Cash timing convention

| Date | Use |
|---|---|
| `cash_ex_date` | E22_v2 / challenger cash credit (economic ex-date) |
| `cash_payment_date` | Settlement / delivery; ledger completeness; E22_v3 payment-date experiments |

## Stock dividends — completed

| Field | Status (n=52 stock events) |
|---|---|
| `stock_ex_date` | Complete |
| `stock_dividend` (元/股) | Complete (FinMind) |
| `stock_payment_date` | Complete — **0 missing** (Yahoo; ±3d near-match for FinMind/Yahoo ex drift) |

Share factor on `stock_ex_date`: `1 + stock_dividend / 10` (par 10).  
Detail: `research/e22/STOCK_DIVIDEND_LEDGER.md`.

## Artifacts

| Path | Role |
|---|---|
| `e22_div_payment_backfill_status.json` | Combined cash+stock gap status |
| `e22_payment_date_yahoo_backfill.json` | Cash fill audit (29 rows) |
| `yahoo_tw_dividend_history.csv` | Yahoo source extract |
| `scripts/e22_backfill_div_payment_dates_yahoo.py` | Re-runnable backfill |

## Official vs challenger

| Path | Cash | Stock shares |
|---|---|---|
| E22_v2 SOFT_FROZEN | Credit on `cash_ex_date` | Not applied |
| Challenger early-stack | Same cash credit | Optional share increase on `stock_ex_date` |
