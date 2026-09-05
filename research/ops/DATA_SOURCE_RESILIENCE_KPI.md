# Data Source Resilience KPI

Generated: `2026-09-05T09:13:16.968459+00:00`
Status: **OPS** — Soft-Frozen unchanged; no live-wire.

- Critical streams: **7**
- Critical **without** backup: **5**
- Grade A / D: **2** / **4**
- `kpi_ok`: **True** (fails only on payment-date backup regression)

| Stream | Grade | Primary | Backup | Critical |
|---|:---:|---|---|:---:|
| Fin-12 history OHLCV | D | `github_tw_stock_data_release` | — | Y |
| Fin-12 recent OHLCV | B | `twse_mi_index` | — | Y |
| Telecom / 0050 raw OHLCV | A | `finmind_taiwan_stock_price` | `yahoo_finance` | Y |
| TAIEX | D | `finmind_taiwan_stock_price_TAIEX` | — | Y |
| Adj / corporate-action factors | D | `finmind_div_result_capred_split` | — | Y |
| Dividend amount / ex-date | C | `finmind_taiwan_stock_dividend` | — | Y |
| Dividend payment date | A | `finmind_then_mops` | `yahoo_tw_quote_dividend` | Y |
| E50 fundamentals | D | `finmind` | — | n |

## Flags

- `SINGLE_POINT:fin12_history_ohlcv`
- `SINGLE_POINT:fin12_recent_ohlcv`
- `SINGLE_POINT:taiex`
- `SINGLE_POINT:adj_corporate_actions`
- `SINGLE_POINT:dividend_amount_ex`

## Phase B next

- TAIEX FinMind vs Yahoo/^TWII shadow diff
- Dividend amount FinMind vs Yahoo reconcile (flag-only)
- Fin-12 recent Yahoo vs TWSE shadow

Authority: `research/ops/DATA_SOURCE_RESILIENCE.md`
