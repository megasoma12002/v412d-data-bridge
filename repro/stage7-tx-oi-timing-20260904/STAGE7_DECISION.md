# Stage 7 Decision — TX OI timing overlay

Date: **2026-09-04**  
Probe: front-month TX `open_interest` Δ z-score → equity exposure overlay on early-stack (E16+E18+E22 ex-date)  
Artifacts: `repro/stage7-tx-oi-timing-20260904/`

## Pre-registered params
- z-window=60, |z| threshold=1.0, delever exposure=0.7
- OI lag=1 trading day; Exact T+1 preserved
- Bar: util > BASE + 0.002 and |MDD| ≤ |BASE MDD| + 0.005

## Dual QC
Official E22_v2 + paper E22_v3: **PASS** (`dual_qc.json`)

## Full-sample results

| Book | CAGR | MDD | Util | Delever days |
|---|---:|---:|---:|---:|
| BASE | 0.1125 | -0.2211 | 0.0019 | 0 |
| OI_UP_DELEVER | 0.0983 | -0.2143 | -0.0089 | 104 |
| OI_DOWN_DELEVER | 0.0977 | -0.2096 | -0.0071 | 216 |

Exact T+1: **PASS**

## Sealed 2025+ (diagnostic only — no retune)

| Book | Util |
|---|---:|
| BASE | 0.2921 |
| OI_UP_DELEVER | 0.2528 |
| OI_DOWN_DELEVER | 0.2366 |

## Decision: `STOP_STAGE7_TX_OI_TIMING_OVERLAY`

Neither OI delever overlay clears util+MDD bar vs BASE (or Exact T+1 failed). Do not retune thresholds after sealed look.

Promotion: **false**. Official path remains E22_v2. Do not reopen stopped 3A/Stage4/Stage6 feature sets.
