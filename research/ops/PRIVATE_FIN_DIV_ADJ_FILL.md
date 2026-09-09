# Private FIN dividend + adj_close fill

Date: 2026-09-09  
Status: **DONE** — research data hygiene; Soft-Frozen live membership **unchanged**  
Label: `E22_PRIVATE_FIN_DIV_ADJ_FILL_2026-09-09`

## What was filled

| Gap | Fill |
|---|---|
| E22 dividend events for 民營 + R2 (`2884/2885/2890/2891/2881/2882/2801/2834`) | Merged into `data/dividend_events/e22_dividend_events.csv` via FinMind `TaiwanStockDividend` |
| Payment dates | Yahoo TW backfill (`e22_backfill_div_payment_dates_yahoo.py`) — private cash blank pay ~**0.8%**; stock ex/pay **0** blank |
| `adj_close` | `data/market/private_fin_adjusted.csv` — FinMind DividendResult / capital-reduction / split factors × TW12 OHLCV |
| Par value | TWSE openapi → `par_value_by_code.csv` (all eight **VERIFIED** 10.0) |

## Scripts

- `scripts/e22_fill_private_fin_div_adj.py` — fetch + merge dividends + build adj panel  
- `scripts/v412e22_fetch_dividend_events.py` — UNIVERSE extended for future full re-fetch  
- `scripts/e22_backfill_payment_dates_yahoo.py` — UNIVERSE extended  
- `scripts/e22_data_quality_kpi.py` — Soft-Frozen KPI scoped; private reported under `private_fin_research`  
- `scripts/e16_private_fin_holdings_rescreen.py` — joins private adj panel

## Soft-Frozen / live

- Live `e21` universe **not** expanded  
- Soft-Frozen ledger rows kept; KPI `kpi_ok` still Soft-Frozen-scoped  
- Status: `data/dividend_events/e22_private_fin_fill_status.json`

## Re-screen after fill

`PRIVATE_FIN_HOLDINGS_RESCREEN` still **STOP_NO_POSITIVE_HELDOUT_VS_LIVE_PUB_KD** (0 coexist). Data gaps were not the reason for STOP.
