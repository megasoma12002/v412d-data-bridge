# E22 Challenger Forward (paper parallel)

**Status:** `PAPER_EXPERIMENTAL`

- Path: `forward/e22_challenger/`
- Same E16 targets / Exact T+1 as E21
- **Plus** cash dividend credits on `cash_ex_date`
- Does **not** edit `forward/e21/`

## QC

`PASS`

Compare vs E21: `{"n_overlap_sessions": 9, "final_e21_nav": 3187508.279090027, "final_e22_challenger_nav": 3187508.279090027, "final_nav_lift": 0.0, "total_dividend_cash": 0.0}`

## Next (governance)

1. Keep paper-running beside live E21
2. Explicit approval → new SOFT_FROZEN E22 version
3. Never rewrite historical E21 fills
