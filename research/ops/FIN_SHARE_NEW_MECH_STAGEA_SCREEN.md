# FIN-share new-mechanism Stage A — Screen

Generated: `2026-09-27T05:25:38Z`
Status: **`SAT_REF_ONLY`** · Soft-Frozen **KEEP** · Exact T+1 **KEEP** · live wire **false**
Base `BASE_LIVE_CONF` mean FIN=**69.18%** · cool_exits=**38**

MECH_HIT: **1** (FIN-share HIT: **0**) · CAGR_SOFT: **9** / 11

## Ranked

| book | track | FIN↓pp | mean FIN | CAGR↑h | MDD↑h | MDD↑s | tip | hit |
|---|---|---:|---:|---:|---:|---:|---|---|
| `COND_BSIDE_F070` | COND | +5.75 | 63.43% | -0.18 | +0.06 | -0.24 | Y | N |
| `CLIP_F072` | CLIP | +4.56 | 64.62% | -0.11 | -0.07 | +0.08 | Y | N |
| `COND_BULL_F070` | COND | +5.03 | 64.15% | -0.11 | -0.07 | -0.40 | Y | N |
| `COND_BULL_F072` | COND | +3.86 | 65.32% | -0.07 | +0.23 | -0.16 | Y | N |
| `CLIP_F075` | CLIP | +2.82 | 66.36% | -0.08 | -0.14 | +0.23 | Y | N |
| `CLIP_F070` | CLIP | +5.93 | 63.25% | -0.26 | -0.06 | -0.30 | Y | N |
| `SAT_A20_H5` | SAT_REF | +0.23 | 68.95% | +0.33 | -0.31 | -0.10 | Y | Y |
| `SKEW_FIN_HEAVY` | SKEW | +0.00 | 69.18% | +0.03 | -0.34 | -0.26 | Y | N |
| `SKEW_FIN_ONLY` | SKEW | +0.00 | 69.18% | +0.09 | -0.76 | -0.56 | Y | N |
| `CASH_F10` | CASH | +6.71 | 62.47% | -1.60 | +0.58 | +0.74 | Y | N |
| `CASH_F05` | CASH | +3.36 | 65.82% | -0.95 | -0.15 | +0.44 | Y | N |

## Binding

1. Soft-Frozen live clips KEEP until dedicated CLIP ACCEPT.
2. Exact T+1 · L1=0.05 KEEP.
3. Even MECH_HIT → paper only; at most one track for ACCEPT discussion.

Repro: `PYTHONPATH=scripts python3 scripts/fin_share_new_mech_stagea.py`

Label: `FIN_SHARE_NEW_MECH_STAGEA_SCREEN_2026-09-27__SAT_REF_ONLY`
