# E22 payment-date restore (2026-09-10)

Human: Soft-Frozen first, then private — restore from prior complete state / Yahoo backfill; correct KPI.

## Cause

`#166` private FIN dividend merge rewrote `e22_dividend_events.csv` and **dropped Soft-Frozen cash/stock payment dates** that had been completed in `69bb0f4` (and Yahoo-filled early cash gaps in `8c7ae13`). Committed Soft-Frozen KPI still claimed 0% blank while CSV had ~25% cash-pay blank and **100% stock-pay blank**.

## What we did

1. **Soft-Frozen restore** from git snapshot `69bb0f4` (`data/dividend_events/e22_dividend_events.csv`):
   - Restored **29** cash payment dates + **52** stock payment dates onto matching Soft-Frozen keys.
2. **Universe Yahoo TW backfill** via `scripts/e22_backfill_div_payment_dates_yahoo.py`:
   - cash updates **30**, stock updates **91**.
3. Regenerated Soft-Frozen-scoped KPI: `scripts/e22_data_quality_kpi.py` → **`kpi_ok=true`**.

## Resulting blank rates

| Scope | Cash pay blank | Stock pay blank |
|---|---:|---:|
| Soft-Frozen (KPI gate) | **0 / 144 (0%)** | **0 / 52 (0%)** |
| Private FIN (research) | **1 / 129 (~0.78%)** | **0 / 91 (0%)** |

### Residual (documented, not invented)

- `2891` fiscal `98年` cash ex `2010-07-29` amount `0.64` — Yahoo TW page itself has empty 「現金股利發放日」 for that row (stock pay on same Yahoo row is present). Left blank; not a Soft-Frozen gate.

## Non-actions

- Soft-Frozen membership / live wire / formal ex-date books **unchanged**.
- No weekday-forward history rewrite; remaining thin-live / `dividends_applied` evidence still accumulates on cadence.

## Artifacts

- Ledger: `data/dividend_events/e22_dividend_events.csv`
- Yahoo cache: `data/dividend_events/yahoo_tw_dividend_history.csv`
- Backfill status: `data/dividend_events/e22_div_payment_backfill_status.json`
- KPI: `research/ops/E22_DATA_QUALITY_KPI.{md,json}`

## Label

`E22_PAYMENT_DATE_RESTORE_2026-09-10__SF_ZERO_BLANK__PRIV_ONE_YAHOO_GAP`
