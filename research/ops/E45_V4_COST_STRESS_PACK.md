# E45 V4 Cost / Stress Pack (E45-named)

Generated: `2026-09-05T18:26:14.920671+00:00`
Status: **PASS** (E45-named Exact T+1 cost multiples)
Live stitch: **FORBIDDEN** (V1 still FAIL) · Soft-Frozen **[0.50, 0.95] KEEP** · DEFAULT **`E22_v2s_tw` KEEP**
Claimed MDD ≈ −13.16%: **`NOT_VERIFIED`**

## Method

- Books: `BASE_E16_E18_E22_v2s` vs `CHAL_E45_E3` (`E3_VOLTARGET_WINNER` overlay)
- Exact T+1 early-stack; scale `BUY_FEE`/`SELL_FEE`/`SLIP`/`TAX_*` by 0×/1×/2×/3×
- Sample: `2011-12-01` → `2026-09-04`

## E45-named cost multiples

| Book | ×cost | CAGR | MDD | fills | fees+tax |
|---|---:|---:|---:|---:|---:|
| BASE_E16_E18_E22_v2s | 0 | 14.40% | -22.49% | 6256 | 0.00 |
| CHAL_E45_E3 | 0 | 11.49% | -20.60% | 6930 | 0.00 |
| BASE_E16_E18_E22_v2s | 1 | 13.78% | -22.64% | 6271 | 400789.84 |
| CHAL_E45_E3 | 1 | 10.79% | -20.76% | 6931 | 394842.78 |
| BASE_E16_E18_E22_v2s | 2 | 13.15% | -22.81% | 6228 | 764499.76 |
| CHAL_E45_E3 | 2 | 10.11% | -20.91% | 6937 | 752828.41 |
| BASE_E16_E18_E22_v2s | 3 | 12.54% | -22.99% | 6252 | 1092640.81 |
| CHAL_E45_E3 | 3 | 9.44% | -21.07% | 6929 | 1076272.06 |

## Deltas vs BASE

| ×cost | MDD Δ (pp; + = shallower) | CAGR giveback (pp) |
|---:|---:|---:|
| 0 | 1.89 | 2.92 |
| 1 | 1.88 | 2.99 |
| 2 | 1.90 | 3.03 |
| 3 | 1.92 | 3.11 |

## V4 checks

| Check | Result |
|---|---|
| `has_e45_named_cost_table` | **True** |
| `multiples` | **[0, 1, 2, 3]** |
| `at_1x_chal_mdd_not_worse_than_base` | **True** |
| `at_2x_chal_still_shallower_or_within_5pp` | **True** |
| `at_3x_chal_still_shallower_or_within_5pp` | **True** |

**V4 verdict: `PASS`**

## Artifacts

- `repro/e45-v4v5-named-packs/outputs/e45_named_cost_multiples.csv`
- `repro/e45-v4v5-named-packs/outputs/e45_named_cost_multiples_delta.csv`
- `repro/e45-v4v5-named-packs/summary.json`
- Script: `scripts/e45_v4v5_named_packs.py`

## Non-actions

- No live-wire / Soft-Frozen flip / history rewrite
- No invented −13.16%
- V4 PASS ≠ stitch authorization (V1 still FAIL)

## Label

`E45_V4_COST_STRESS_PACK_2026-09-05__PASS`

