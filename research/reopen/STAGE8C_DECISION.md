# Stage 8c Decision — Long-history ETF screen

Date: **2026-09-04**  
Filter: prefer listing ≤2016 (plus 2018 bond ETFs); skip leveraged L/R; skip 0050 (in stack) and 0056 (already STOP).  
Artifacts: `repro/stage8c-longhist-etf-20260904/`

## Results (window-matched vs BASE)

| ETF | Window | n days | BASE util | SLEEVE4 util | RISKOFF util | Beat? |
|---|---|---:|---:|---:|---:|---|
| 0051 | 2007-01-02→2026-09-04 | 3359 | -0.0037 | -0.0034 | -0.0127 | no |
| 0055 | 2007-07-16→2026-09-04 | 3359 | -0.0037 | -0.0151 | -0.0191 | no |
| 0061 | 2009-08-17→2026-09-04 | 3359 | -0.0037 | -0.0192 | -0.0090 | no |
| 006203 | 2011-04-14→2026-09-04 | 3359 | -0.0037 | -0.1462 | -0.0944 | no |
| 00646 | 2015-12-14→2026-09-04 | 2363 | 0.0265 | 0.0205 | 0.0230 | no |
| 00636 | 2015-04-01→2026-09-04 | 2538 | 0.0239 | 0.0116 | 0.0166 | no |
| 00719B | 2018-02-01→2026-09-04 | 1837 | 0.0285 | 0.0261 | 0.0287 | no |
| 00720B | 2018-02-01→2026-09-04 | 1837 | 0.0285 | -0.0045 | 0.0017 | no |
| 006208 | 2012-07-17→2026-09-04 | 3205 | -0.0038 | -0.1122 | -0.0837 | no |

## Decision: `STOP_STAGE8C_LONGHIST_ETF_SCREEN`

No long-history candidate clears SLEEVE4/RISKOFF util+MDD bar vs window-matched BASE.  
Includes mid-cap (0051), cross-border (0055), older sector (0061/006203), overseas (00646/00636), bonds (00719B/00720B), and 0050-clone control (006208).

Promotion: **false**. Official E22_v2 unchanged.

Interpretation: lengthening history removes the short-window false positives (00918/00896/00927); durable edge not found in this ETF sleeve design.
