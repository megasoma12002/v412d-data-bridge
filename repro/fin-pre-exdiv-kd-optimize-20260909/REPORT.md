# FIN_PRE_EXDIV_KD — parameter optimize (paper NAV)

Generated: `2026-09-09T00:56:46.650792+00:00`
Status: **OPTIMAL_SELECTED** · Soft-Frozen **KEEP** · live wire **false**

## Objective

1. tip-clean (YTD+1y PASS) **and** held-out score > 0
2. else no tip PAUSE · max held-out
3. else max held-out

## Optimal: `KD_APR15_MAY15_Klt30_T15`

- Selection rule: **coexist (tip PASS + heldout>0)**
- Held-out score: **+0.647**
- Tip: YTD **PASS** (1.2988977782536715) · 1y **PASS** (1.5872881136167694)

- Season: `APR15_MAY15` [4, 15]–[5, 15]
- K thresh: **< 30.0** · pre-ex skip: **T−15…T0**

## Top 12 (ranked)

| id | heldout | MDD↑ | CAGR gb | YTD | 1y | tip-clean |
|---|---:|---:|---:|---|---|---|
| `KD_APR15_MAY15_Klt30_T15` | 0.647 | 0.807 | 0.319 | PASS | PASS | True |
| `KD_APR_MAY_Klt30_T15` | 0.629 | 0.844 | 0.430 | PASS | PASS | True |
| `KD_APR_MAY_Klt30_T10` | 0.625 | 0.866 | 0.483 | PASS | PASS | True |
| `KD_APR15_MAY15_Klt30_T10` | 0.624 | 0.815 | 0.383 | PASS | PASS | True |
| `KD_MAY15_JUN10_Klt20_T15` | 0.590 | 0.833 | 0.487 | PASS | PASS | True |
| `KD_APR15_MAY15_Klt30_T5` | 0.534 | 0.735 | 0.403 | PASS | PASS | True |
| `KD_MAY_Klt25_T15` | 0.526 | 0.689 | 0.327 | PASS | PASS | True |
| `KD_APR_MAY_Klt30_T5` | 0.522 | 0.769 | 0.493 | PASS | PASS | True |
| `KD_MAY_Klt30_T15` | 0.481 | 0.602 | 0.242 | PASS | PASS | True |
| `KD_APR15_MAY31_Klt30_T15` | 0.478 | 0.605 | 0.254 | PASS | PASS | True |
| `KD_MAY_Klt25_T10` | 0.474 | 0.678 | 0.410 | PASS | PASS | True |
| `KD_MAY_Klt20_T10` | 0.467 | 0.629 | 0.326 | PASS | PASS | True |

## Anchors

| id | heldout | MDD↑ | CAGR gb | YTD | 1y | tip-clean |
|---|---:|---:|---:|---|---|---|
| `MIX_L75` | 0.127 | 0.303 | 0.351 | PASS | PASS | True |
| `FIN_RS_SOFT_TILT_EXDIV` | 0.530 | 1.112 | 1.163 | PAUSE_REVIEW | PAUSE_REVIEW | False |

## Verdict

Optimal under paper objective: `KD_APR15_MAY15_Klt30_T15` (rule=coexist (tip PASS + heldout>0)) heldout=+0.647 tip YTD=PASS 1y=PASS. Soft-Frozen KEEP · no live wire.

## Hard rules

- Soft-Frozen KEEP · no live wire · optimize ≠ observe OPEN / cutover

Repro: `repro/fin-pre-exdiv-kd-optimize-20260909/`
