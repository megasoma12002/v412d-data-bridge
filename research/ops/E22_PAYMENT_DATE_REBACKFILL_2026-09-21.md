# E22 payment-date re-backfill (2026-09-21)

Status: **DONE** — Soft-Frozen **KEEP** · no tip / history rewrite · no live wire  
Cause: dividend ledger refresh (`5ae7d94`) re-dropped cash/stock payment dates that restore `#172` / Yahoo backfill / `2891` CNYES fill had completed.

## What we did

1. Re-ran `scripts/e22_backfill_div_payment_dates_yahoo.py --skip-fetch` against `yahoo_tw_dividend_history.csv`.
2. Restored documented residual **`2891` / cash ex `2010-07-29` → pay `2010-08-23`** (`E22_2891_CASH_PAYMENT_FILL_2010-08-23.md` / CNYES `#3283475`).
3. Regenerated `E22_DATA_QUALITY_KPI.*` → **`kpi_ok=true`**, Soft-Frozen cash/stock pay blank **0%**, private cash/stock pay blank **0%**.

## Result

| Scope | Cash pay blank | Stock pay blank |
|---|---:|---:|
| Soft-Frozen (KPI gate) | **0%** | **0%** |
| Private FIN (research) | **0%** | **0%** |

## Non-actions

- No Soft-Frozen membership / Stage-E DEFAULT / tip invent.
- Stock-pay completeness remains ops completeness (DQ does not flag stock blank; now filled anyway).

## Label

`E22_PAYMENT_DATE_REBACKFILL_2026-09-21__SF_PRIV_ZERO_BLANK`
