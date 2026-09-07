# E45 true DEF proxies (research ingest)

Fetched by `scripts/fetch_e45_true_def_proxies.py`.

- **TWD bond ETFs** (`00679B`, `00687B`, `00719B`): FinMind `TaiwanStockPrice`.
- **USD cash-like** (`BIL`, `SHY`): Yahoo Finance.
- **FX** (`USDTWD_finmind.csv`): FinMind `TaiwanExchangeRate` USD spot mid.

Do **not** merge into `forward/e21/live_market.csv` without a dedicated paper pack + freeze.
Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN.

Also ingested for M2 BIL_FX improve pack: `00720B`, `00740B`, `00751B` (TWD short-bond ETF proxies).

## Tradable TWD cash-like honesty (2026-09-07)

- `00740B` / `00751B`: listed TW short-bond ETFs (research DEF destination) — **not** bank deposits.
- Retail deposit-rate / deposit-NAV series: **unavailable on free FinMind tier** (sponsor gate).
- CBC rediscount (`cbc_rediscount_rate_*.csv`): policy carry upper bound only.
- Do not merge into `live_market.csv`. Soft-Frozen KEEP · stitch FORBIDDEN.
