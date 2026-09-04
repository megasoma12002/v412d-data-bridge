# Stage 8b Decision — Multi defensive ETF screen

Date: **2026-09-04**  
Candidates: `00713, 00918, 00896, 00878, 00927`  
Artifacts: `repro/stage8b-multi-etf-20260904/`

## Per-ETF full-window results (CAGR / MDD / Util)

| ETF | Window | BASE util | SLEEVE4 util | RISKOFF util | Beat? |
|---|---|---:|---:|---:|---|
| 00713 | 2017-09-27→2026-09-04 | 0.0249 | 0.0135 | 0.0078 | no |
| 00918 | 2022-11-24→2026-09-04 | 0.1144 | 0.1465 | 0.1130 | SLEEVE4 |
| 00896 | 2021-09-16→2026-09-04 | 0.0974 | 0.1252 | 0.1008 | SLEEVE4 |
| 00878 | 2020-07-20→2026-09-04 | 0.0603 | 0.0550 | 0.0488 | no |
| 00927 | 2023-06-06→2026-09-04 | 0.1026 | 0.1305 | 0.1047 | SLEEVE4,RISKOFF |

## Decision: `STAGE8B_MULTI_ETF_INTERESTING_CONTINUE_SANDBOX`

Interesting: 00918:SLEEVE4, 00896:SLEEVE4, 00927:SLEEVE4, 00927:RISKOFF. Still NO auto-promote; would need cost/liquidity + dividend-adj ranking before any paper sleeve.

### Caveats (why this is not a promote)
- **Short listing windows** (00918/00896/00927) overlap a strong post-2022 equity regime; easy to look good vs BASE.
- **Longer windows fail:** 00713 (~9y) and 00878 (~6y) do **not** clear the bar.
- Raw close only (no adj_close) — still, do not promote on short-window util alone.

Promotion: **false**. Official E22_v2 universe unchanged.

Note: each ETF compared only on its own listing window vs BASE on the same dates.
