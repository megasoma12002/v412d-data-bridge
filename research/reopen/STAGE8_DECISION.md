# Stage 8 Decision — Defensive ETF sleeve (0056)

Date: **2026-09-04**  
Probe: add high-div ETF **0056** vs official 3-sleeve early-stack (E16+E18+E22)  
Artifacts: `repro/stage8-defensive-etf-20260904/`

## Pre-registered books
| Book | Rule |
|---|---|
| BASE | Financial / Telecom / 0050 |
| SLEEVE4_0056 | 4th sleeve DEF=0056; Bear/Crisis priors up to ~25–35% |
| RISKOFF_0056 | In Bear/Crisis shift 25% of Financial weight → 0056 |

Bar: util > BASE + 0.002, |MDD| ≤ |BASE MDD| + 0.005. Exact T+1 required.

## Full-sample (CAGR | MDD | Util)

| Book | CAGR \| MDD \| Util | mean tgt DEF |
|---|---|---:|
| BASE | 0.1069 | -0.2211 | -0.0037 | 0 |
| SLEEVE4_0056 | 0.1037 | -0.2328 | -0.0127 | 0.105 |
| RISKOFF_0056 | 0.0978 | -0.2197 | -0.0120 | 0.060 |

Exact T+1: **PASS**

## Sealed 2025+ util (diagnostic)

| Book | Util |
|---|---:|
| BASE | 0.2282 |
| SLEEVE4_0056 | 0.2244 |
| RISKOFF_0056 | 0.1856 |

## Decision: `STOP_STAGE8_DEFENSIVE_ETF_SLEEVE`

Neither SLEEVE4_0056 nor RISKOFF_0056 clears pre-registered bar vs BASE (or Exact T+1 failed). Do not retune priors/shift after sealed look.

Promotion: **false**. Official path remains E22_v2 (8 names).  
Limitation: 0056 ranking/execution uses raw close (no adj_close) — conservative for high-div ETF.
