# E22 Stock Dividend Ledger Completeness

Date: 2026-09-04  
Scope: Core universe dividend events in `data/dividend_events/e22_dividend_events.csv`  
Governance: Does **not** rewrite SOFT_FROZEN E22_v2 fill loop (cash-only on cash_ex_date).

## Why this matters

Stock dividends increase share count (`持股變多`). Ignoring them understates holdings and mis-marks NAV when prices adjust on the stock ex-date.

## Ledger status (after Yahoo backfill)

| Field | Cash events (n=144) | Stock events (n=52) |
|---|---|---|
| Ex-date | Complete | Complete |
| Payment date | Complete (0 missing) | Complete (0 missing) |
| Amount | FinMind cash_dividend | FinMind stock_dividend (元/股) |

Source for payment dates: Yahoo TW quote dividend pages (`yahoo_tw_dividend_history.csv`).  
Script: `scripts/e22_backfill_div_payment_dates_yahoo.py` (cash ±1d exact/near; stock ±3d near-match for FinMind/Yahoo ex drift, e.g. 2892 2019-08-09 vs 2019-08-12).

Status artifact: `data/dividend_events/e22_div_payment_backfill_status.json`.

## Unit / share factor

- FinMind `stock_dividend` = 元/股 (par 10).
- Share multiplier on `stock_ex_date`: `1 + stock_dividend / 10`.
- Example: 0.5 元/股 → +5% shares.

## Economic timing

| Event | Research convention |
|---|---|
| `stock_ex_date` | Holdings increase (economic ownership; NAV continuous with price drop) |
| `stock_payment_date` | Delivery / settlement date (ledger completeness; not used for NAV mark) |

## Wiring

| Path | Behavior |
|---|---|
| Official E22_v2 (SOFT_FROZEN) | Cash credit only on `cash_ex_date` — **unchanged** |
| Challenger `scripts/e50_early_stack_combined_nav.py` | Optional `apply_stock_div=True`: share increase on `stock_ex_date` |
| Compare variant | `E16_E18_E22_CASH_ONLY` vs `E16_E18_E22` (cash+stock) |

Promotion of stock-aware E22 requires an explicit new version label and governance approval — do not silently rewrite E22_v2.
