# Stage 4 Decision — STOP

Date: 2026-09-04  
Family: `z(rev_yoy_12m) + z(cfo_yoy)`  
Artifact: `repro/stage4-rev-cfo-20260904/`

## Decision: `STOP_STAGE4_FEATURE_SET`

| Gate | Result |
|---|---|
| Dev net40 mean excess | +0.017%/mo (barely > 0) |
| No 3y consecutive neg (net40) | **FAIL** (2020–2022) |
| LOYO not fragile | **FAIL** |
| Industry cap | Pass |
| Sealed 2025+ net40 | Positive — **not used to rescue** |

## Binding

- Do **not** retune this score.  
- Do **not** blend back Amihud/OI from Stage 3.  
- 3A cross-sectional monthly sleeve: **two feature families stopped in a row**.

## Stage posture after Stage 4

Recommend **pause further 3A monthly CS experiments** until a materially different information source exists (alt-data / options / microstructure PIT).  

Near-term EV returns to **E22_v2 operations** (dividend completeness, daily QC), not another close cousin of fundamental YoY.
