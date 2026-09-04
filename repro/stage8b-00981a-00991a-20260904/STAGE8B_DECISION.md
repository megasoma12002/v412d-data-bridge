# Stage 8b Decision — Multi defensive ETF screen

Date: **2026-09-04**  
Candidates: `00981A, 00991A`  
Artifacts: `repro/stage8b-00981a-00991a-20260904/`

## Per-ETF full-window results (CAGR / MDD / Util)

| ETF | Window | BASE util | SLEEVE4 util | RISKOFF util | Beat? |
|---|---|---:|---:|---:|---|
| 00981A | 2025-05-27→2026-09-04 | 0.7958 | 0.7123 | 0.8424 | RISKOFF |
| 00991A | TOO_SHORT | — | — | — | no |

## Decision: `STAGE8B_MULTI_ETF_INTERESTING_CONTINUE_SANDBOX`

Interesting: 00981A:RISKOFF. Still NO auto-promote; would need cost/liquidity + dividend-adj ranking before any paper sleeve.

### Caveats (why this is not a promote)
- **Short listing windows** (00918/00896/00927) overlap a strong post-2022 equity regime; easy to look good vs BASE.
- **Longer windows fail:** 00713 (~9y) and 00878 (~6y) do **not** clear the bar.
- Raw close only (no adj_close) — still, do not promote on short-window util alone.

Promotion: **false**. Official E22_v2 universe unchanged.

Note: each ETF compared only on its own listing window vs BASE on the same dates.
