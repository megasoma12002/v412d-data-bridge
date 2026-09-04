# Stage 8b Decision — Multi defensive ETF screen

Date: **2026-09-04**  
Candidates: `0051, 0055, 0061, 006203, 00646, 00636, 00719B, 00720B, 006208`  
Artifacts: `repro/stage8c-longhist-etf-20260904/`

## Per-ETF full-window results (CAGR / MDD / Util)

| ETF | Window | BASE util | SLEEVE4 util | RISKOFF util | Beat? |
|---|---|---:|---:|---:|---|
| 0051 | 2007-01-02→2026-09-04 | -0.0037 | -0.0034 | -0.0127 | no |
| 0055 | 2007-07-16→2026-09-04 | -0.0037 | -0.0151 | -0.0191 | no |
| 0061 | 2009-08-17→2026-09-04 | -0.0037 | -0.0192 | -0.0090 | no |
| 006203 | 2011-04-14→2026-09-04 | -0.0037 | -0.1462 | -0.0944 | no |
| 00646 | 2015-12-14→2026-09-04 | 0.0265 | 0.0205 | 0.0230 | no |
| 00636 | 2015-04-01→2026-09-04 | 0.0239 | 0.0116 | 0.0166 | no |
| 00719B | 2018-02-01→2026-09-04 | 0.0285 | 0.0261 | 0.0287 | no |
| 00720B | 2018-02-01→2026-09-04 | 0.0285 | -0.0045 | 0.0017 | no |
| 006208 | 2012-07-17→2026-09-04 | -0.0038 | -0.1122 | -0.0837 | no |

## Decision: `STOP_STAGE8B_MULTI_DEFENSIVE_ETF`

No named ETF (00713/00918/00896/00878/00927) clears SLEEVE4 or RISKOFF bar vs window-matched BASE. Do not retune priors after the fact.

### Caveats (why this is not a promote)
- **Short listing windows** (00918/00896/00927) overlap a strong post-2022 equity regime; easy to look good vs BASE.
- **Longer windows fail:** 00713 (~9y) and 00878 (~6y) do **not** clear the bar.
- Raw close only (no adj_close) — still, do not promote on short-window util alone.

Promotion: **false**. Official E22_v2 universe unchanged.

Note: each ETF compared only on its own listing window vs BASE on the same dates.
