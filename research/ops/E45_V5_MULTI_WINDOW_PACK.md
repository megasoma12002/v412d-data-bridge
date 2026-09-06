# E45 V5 Multi-Window / Crisis-Year Pack (E45-named)

Generated: `2026-09-05T18:26:14.920671+00:00`
Status: **PASS** (E45-named crisis-year attribution + Stage-3 multi-window)
Live stitch: **FORBIDDEN** (V1 still FAIL) · Soft-Frozen **KEEP** · DEFAULT **`E22_v2s_tw` KEEP**
Claimed MDD ≈ −13.16%: **`NOT_VERIFIED`**

## Data coverage

- Market span: **2011-12-01 → 2026-09-04**
- **2008: N/A** (before sample start) — documented
- Crisis years scored: 2011 (partial), 2015, 2018, 2020, 2022

## Crisis-year attribution (1× costs, Exact T+1)

| Book | Year | avail | n_days | ret | MDD | note |
|---|---:|---|---:|---:|---:|---|
| BASE_E16_E18_E22_v2s | 2011 | False | 0 | n/a | n/a | no data |
| BASE_E16_E18_E22_v2s | 2015 | True | 244 | -3.21% | -13.65% |  |
| BASE_E16_E18_E22_v2s | 2018 | True | 247 | 9.18% | -6.98% |  |
| BASE_E16_E18_E22_v2s | 2020 | True | 245 | -3.69% | -22.64% |  |
| BASE_E16_E18_E22_v2s | 2022 | True | 246 | 5.53% | -16.71% |  |
| BASE_E16_E18_E22_v2s | 2008 | False | 0 | n/a | n/a | market starts 2011-12-01; 2008 N/A |
| CHAL_E45_E3 | 2011 | False | 0 | n/a | n/a | no data |
| CHAL_E45_E3 | 2015 | True | 244 | -3.87% | -12.80% |  |
| CHAL_E45_E3 | 2018 | True | 247 | 7.59% | -6.14% |  |
| CHAL_E45_E3 | 2020 | True | 245 | -4.94% | -20.76% |  |
| CHAL_E45_E3 | 2022 | True | 246 | 3.44% | -16.53% |  |
| CHAL_E45_E3 | 2008 | False | 0 | n/a | n/a | market starts 2011-12-01; 2008 N/A |

## Crisis deltas vs BASE

| Year | avail | MDD Δ (pp) | ret Δ (pp) | note |
|---:|---|---:|---:|---|
| 2011 | False | n/a | n/a | no data |
| 2015 | True | 0.85 | -0.66 |  |
| 2018 | True | 0.84 | -1.58 |  |
| 2020 | True | 1.88 | -1.25 |  |
| 2022 | True | 0.19 | -2.09 |  |
| 2008 | False | n/a | n/a | market starts 2011-12-01; 2008 N/A |

## Stage-3 multi-window design (also required)

- `research/e45/E45_DUAL_PAPER_OBSERVE_DESIGN.md`
- `repro/e45-dual-paper-observe-design/outputs/dual_paper_window_metrics.csv`

## V5 checks

| Check | Result |
|---|---|
| `has_e45_named_crisis_table` | **True** |
| `years_available` | **4** |
| `years_with_mdd_improve` | **4** |
| `max_share_of_positive_mdd_improve` | **0.501** |
| `not_single_year_gt_80pct` | **True** |
| `at_least_two_crisis_years_improve` | **True** |
| `year_2008_documented_unavailable` | **True** |
| `stage3_multiwindow_design_present` | **True** |

**V5 verdict: `PASS`**

## Artifacts

- `repro/e45-v4v5-named-packs/outputs/e45_named_crisis_year_attribution.csv`
- `repro/e45-v4v5-named-packs/outputs/e45_named_crisis_year_delta.csv`
- `repro/e45-v4v5-named-packs/summary.json`
- Script: `scripts/e45_v4v5_named_packs.py`

## Non-actions

- No live-wire / Soft-Frozen flip / history rewrite
- No invented −13.16%
- V5 PASS ≠ stitch authorization (V1 still FAIL)

## Label

`E45_V5_MULTI_WINDOW_PACK_2026-09-05__PASS`

