# Soft-Frozen clip top-K — 500M rescreen (paper)

Generated: `2026-09-09T11:17:49.056920+00:00`
Status: **PAPER_RESCREEN** · Soft-Frozen **KEEP** · live wire **false**
Stack: capital **500,000,000** · lot **1000** · FIN within-sleeve **`KD_APR15_MAY15_Klt30_T15`**

## BASE (live Soft-Frozen + KD_OPT)

| window | CAGR | MDD |
|---|---:|---:|
| `full` | 13.94% | -21.77% |
| `heldout_2019_plus` | 18.26% | -21.77% |
| `sealed_2023_plus` | 25.22% | -12.95% |

## Challengers (Stage B top-K @ 500M)

| id | heldout score | MDD↑pp | CAGR gb | YTD | 1y | tip_clean |
|---|---:|---:|---:|---|---|---|
| `CLIP_SEARCH_F0.50-0.95_T0.10-0.35_E0.00-0.35` | -0.020 | 0.335 | 0.711 | PASS | ALERT | False |
| `CLIP_SEARCH_F0.50-0.95_T0.08-0.35_E0.00-0.35` | -0.030 | 0.173 | 0.405 | PASS | PASS | True |
| `CLIP_SEARCH_F0.50-0.95_T0.08-0.35_E0.05-0.35` | -0.338 | 0.055 | 0.786 | PASS | PASS | True |

## Verdict

Best @500M+KD_OPT `CLIP_SEARCH_F0.50-0.95_T0.10-0.35_E0.00-0.35` held-out=-0.020 tip_clean=False. Soft-Frozen KEEP · Class D flip needs ACCEPT.

Recommended Stage E observe id: **`CLIP_SEARCH_F0.50-0.95_T0.10-0.35_E0.00-0.35`**

## Hard rules

- Soft-Frozen live constants untouched
- Passing ≠ Class D flip
- Flip ballot: `SOFT_FROZEN_CLIP_FLIP_BALLOT_DRAFT.md`

Repro: `repro/clip-search-500m-rescreen-20260909/`
