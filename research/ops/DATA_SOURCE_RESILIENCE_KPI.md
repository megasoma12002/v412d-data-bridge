# Data Source Resilience KPI

Generated: `2026-09-05T17:50:35.279957+00:00`
Status: **OPS** — Soft-Frozen unchanged; no live-wire.

- Critical streams: **7**
- Critical **without** backup: **0**
- Grade A / D: **2** / **1**
- `kpi_ok`: **True** (fails only on payment-date backup regression)
- Phase C probes: **PASS** (`phase_c_done=True`)

| Stream | Grade | Primary | Backup | Critical |
|---|:---:|---|---|:---:|
| Fin-12 history OHLCV | C | `github_tw_stock_data_release` | `yahoo_tw_shadow_phase_c` | Y |
| Fin-12 recent OHLCV | B | `twse_mi_index` | `yahoo_tw_shadow_phase_b` | Y |
| Telecom / 0050 raw OHLCV | A | `finmind_taiwan_stock_price` | `yahoo_finance` | Y |
| TAIEX | C | `finmind_taiwan_stock_price_TAIEX` | `yahoo_twii_opt_in_failover` | Y |
| Adj / corporate-action factors | C | `live_market_adj_close` | `yahoo_adj_close_shadow_phase_c` | Y |
| Dividend amount / ex-date | B | `finmind_taiwan_stock_dividend` | `yahoo_amount_shadow_phase_b` | Y |
| Dividend payment date | A | `finmind_then_mops` | `yahoo_tw_quote_dividend` | Y |
| E50 fundamentals | D | `finmind` | — | n |

## Flags

- None

## Phase status

- Phase A: **DONE**
- Phase B: **DONE** (`research/ops/DATA_SOURCE_SHADOW_RECONCILE.json`)
- Phase C: **DONE** (`research/ops/DATA_SOURCE_PHASE_C_PROBES.json`; overall=PASS)

Prep DONE when probes PASS; TAIEX Yahoo failover remains opt-in (not silent e21 primary switch)

Authority: `research/ops/DATA_SOURCE_RESILIENCE.md`
