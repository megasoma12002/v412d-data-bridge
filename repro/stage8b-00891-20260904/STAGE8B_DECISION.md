# Stage 8b Decision — Multi defensive ETF screen

Date: **2026-09-04**  
Candidates: `00891`  
Artifacts: `repro/stage8b-00891-20260904/`

## Per-ETF full-window results (CAGR / MDD / Util)

| ETF | Window | BASE util | SLEEVE4 util | RISKOFF util | Beat? |
|---|---|---:|---:|---:|---|
| 00891 | 2021-05-28→2026-09-04 | 0.0720 | 0.0816 | 0.0659 | no |

## Decision: `STOP_STAGE8B_MULTI_DEFENSIVE_ETF`

No named ETF (00713/00918/00896/00878/00927) clears SLEEVE4 or RISKOFF bar vs window-matched BASE. Do not retune priors after the fact.

### Caveats (why this is not a promote)
- **Short listing windows** (00918/00896/00927) overlap a strong post-2022 equity regime; easy to look good vs BASE.
- **Longer windows fail:** 00713 (~9y) and 00878 (~6y) do **not** clear the bar.
- Raw close only (no adj_close) — still, do not promote on short-window util alone.

Promotion: **false**. Official E22_v2 universe unchanged.

Note: each ETF compared only on its own listing window vs BASE on the same dates.
