# Telecom Within-Sleeve Optimize — Stage C

Generated: `2026-09-08T02:29:53.368533+00:00`
Ballot: **電信優化再研究** · Soft-Frozen **KEEP** · live wire **false** (no auto flip of #126)

New challengers: `TEL_SCORE_LOT_PACK` (score-first pack) · `TEL_DIVERSIFY_PACK` (1張覆蓋後餘額均分)

## Primary @ 500M

Status vs EQUAL: **IMPROVE_VS_EQUAL** · beat EQUAL: `['TEL_DIVERSIFY_PACK', 'TEL_SCORE_LOT_PACK', 'TEL_MIN_LOT_PACK', 'TEL_TOP2_EQUAL']` · beat MIN_LOT: `['TEL_DIVERSIFY_PACK', 'TEL_SCORE_LOT_PACK']`

| id | heldout score vs EQ | MDD↑pp | CAGRΔpp | sealed MDD↑pp | tip TEL w | #names | HHI | pct TEL=0 | fills |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `TEL_EQUAL` | 0.000 | 0.000 | 0.000 | 0.000 | 0.0901 | 1 | 1.000 | 0.000 | 6112 |
| `TEL_DIVERSIFY_PACK` | 0.331 | 0.726 | 0.790 | 2.253 | 0.0734 | 1 | 1.000 | 0.000 | 6033 |
| `TEL_SCORE_LOT_PACK` | 0.325 | 0.690 | 0.729 | 2.205 | 0.0667 | 1 | 1.000 | 0.000 | 5799 |
| `TEL_MIN_LOT_PACK` | 0.177 | 0.514 | 0.674 | 2.555 | 0.0667 | 1 | 1.000 | 0.000 | 5665 |
| `TEL_TOP2_EQUAL` | 0.115 | 0.928 | 1.627 | 3.019 | 0.0667 | 1 | 1.000 | 0.012 | 7370 |
| `TEL_TOP1` | -1.646 | 0.715 | 4.722 | 2.832 | 0.0674 | 1 | 1.000 | 0.094 | 8071 |

### vs live-intent `TEL_MIN_LOT_PACK` (held-out)

| id | score vs MIN_LOT | MDD↑pp | CAGRΔpp | tip positions |
|---|---:|---:|---:|---|
| `TEL_EQUAL` | -0.851 | -0.514 | -0.674 | `{'2412': 1835000.0, '3045': 0.0, '4904': 0.0}` |
| `TEL_SCORE_LOT_PACK` | 0.148 | 0.175 | 0.055 | `{'2412': 0.0, '3045': 0.0, '4904': 1742000.0}` |
| `TEL_DIVERSIFY_PACK` | 0.154 | 0.212 | 0.116 | `{'2412': 1430000.0, '3045': 0.0, '4904': 0.0}` |
| `TEL_TOP2_EQUAL` | -0.062 | 0.414 | 0.953 | `{'2412': 0.0, '3045': 0.0, '4904': 1595000.0}` |
| `TEL_TOP1` | -1.823 | 0.201 | 4.048 | `{'2412': 0.0, '3045': 1034000.0, '4904': 0.0}` |

## Sensitivity @ 3M

Status vs EQUAL: **NO_IMPROVE_VS_EQUAL** · beat EQUAL: `[]` · beat MIN_LOT: `[]`

| id | heldout score vs EQ | MDD↑pp | CAGRΔpp | sealed MDD↑pp | tip TEL w | #names | HHI | pct TEL=0 | fills |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `TEL_EQUAL` | 0.000 | 0.000 | 0.000 | 0.000 | 0.0976 | 2 | 0.847 | 0.040 | 1895 |
| `TEL_DIVERSIFY_PACK` | -0.361 | -0.334 | -0.054 | 0.500 | 0.0726 | 2 | 0.802 | 0.001 | 2208 |
| `TEL_MIN_LOT_PACK` | -0.400 | -0.334 | -0.132 | 0.616 | 0.0779 | 2 | 0.580 | 0.001 | 2220 |
| `TEL_SCORE_LOT_PACK` | -0.770 | -0.748 | 0.044 | 0.630 | 0.0748 | 1 | 1.000 | 0.001 | 2178 |
| `TEL_TOP2_EQUAL` | -0.878 | -0.676 | 0.405 | 1.019 | 0.0707 | 1 | 1.000 | 0.176 | 3211 |
| `TEL_TOP1` | -3.315 | -1.145 | 4.339 | 2.492 | 0.0725 | 1 | 1.000 | 0.121 | 3431 |

### vs live-intent `TEL_MIN_LOT_PACK` (held-out)

| id | score vs MIN_LOT | MDD↑pp | CAGRΔpp | tip positions |
|---|---:|---:|---:|---|
| `TEL_EQUAL` | 0.268 | 0.334 | 0.132 | `{'2412': 11000.0, '3045': 1000.0, '4904': 0.0}` |
| `TEL_SCORE_LOT_PACK` | -0.501 | -0.413 | 0.176 | `{'2412': 9000.0, '3045': 0.0, '4904': 0.0}` |
| `TEL_DIVERSIFY_PACK` | -0.039 | 0.000 | 0.077 | `{'2412': 8000.0, '3045': 1000.0, '4904': 0.0}` |
| `TEL_TOP2_EQUAL` | -0.610 | -0.341 | 0.537 | `{'2412': 0.0, '3045': 0.0, '4904': 11000.0}` |
| `TEL_TOP1` | -3.046 | -0.811 | 4.470 | `{'2412': 0.0, '3045': 7000.0, '4904': 0.0}` |

## Verdict guide

- held-out score > 0 vs `TEL_EQUAL` ⇒ metric improve on charter objective
- HHI↓ / #names↑ ⇒ less concentration than cheapest-pack
- Passing ≠ Soft-Frozen flip ≠ auto live cutover change

Repro: `repro/telecom-sleeve-optimize-20260908/`
