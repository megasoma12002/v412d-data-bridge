# Data Source Shadow Reconcile — Phase B

Generated: `2026-09-05T09:19:53.033597+00:00`
Status: **OPS SHADOW** — Soft-Frozen unchanged; no ledger overwrite.

- Lookback days: **40**
- All OK: **True**
- Drift checks: **0**

| Check | Status | OK | Notes |
|---|---|:---:|---|
| `taiex` | PASS | True | repro/data-source-shadow/taiex_live_vs_yahoo.csv (ret_mae=2.535e-08, corr=1) |
| `fin12_recent` | PASS | True | repro/data-source-shadow/fin_sleeve_recent_live_vs_yahoo.csv |
| `dividend_amount` | PASS | True | repro/data-source-shadow/dividend_amount_live_vs_yahoo.csv (flagged=0/114, max|rel|=6.978e-06) |

## Hard rules

- Dividend amounts: **flag-only**
- No Soft-Frozen flip
- No `forward/e21` rewrite

Authority: `research/ops/DATA_SOURCE_RESILIENCE.md`
