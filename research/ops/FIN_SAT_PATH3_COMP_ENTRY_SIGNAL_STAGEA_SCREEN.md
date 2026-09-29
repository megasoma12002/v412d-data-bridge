# FIN_SAT_PATH3_COMP_ENTRY_SIGNAL_STAGEA_SCREEN

Date: 2026-09-29 · generated `2026-09-29T03:39:03Z`
Verdict: **`SIGNAL_WEAK`** · Soft-Frozen KEEP · Path3 observe KEEP · fill/emit OFF · no live

## COMP-entry labels

- n entries: **76** · good **55** (72.37%) · bad **21** · mean ep days **32.72**
- 2022 entries: **7** · good **4**

## Feature screen (ranked |IC|)

| feature | IC full | IC≤2018 | IC≥2019 | hit med | side | mean_good | mean_bad |
|---|---:|---:|---:|---:|---|---:|---:|
| `rel_5` | 0.1713 | -0.0075 | 0.3508 | 0.5921 | high→good | 0.00027 | 0.00014 |
| `vol_rel_21` | 0.1555 | 0.1393 | 0.2157 | 0.5132 | high→good | 0.00262 | 0.00244 |
| `trail_slope_21` | -0.057 | -0.0834 | 0.0411 | 0.6267 | low→good | -0.00095 | 0.00341 |
| `trail_slope_5` | -0.0443 | -0.1166 | 0.0484 | 0.6267 | low→good | 0.00231 | 0.00523 |
| `comp_minus_sat_21` | 0.0052 | -0.0519 | 0.1093 | 0.5395 | high→good | -0.00288 | -0.00143 |
| `rel_21` | 0.0037 | -0.0515 | 0.1093 | 0.5132 | high→good | -0.00278 | -0.00136 |
| `rel_63` | 0.0022 | 0.0904 | -0.0722 | 0.5395 | low→good | -0.00688 | -0.00654 |
| `trail_rel_63` | -0.0002 | 0.0843 | -0.0927 | 0.5132 | low→good | -0.00708 | -0.00677 |
| `trail_gap_to_theta` | -0.0002 | 0.0843 | -0.0927 | 0.5132 | low→good | 0.00292 | 0.00323 |
| `abs_trail` | 0.0002 | -0.0843 | 0.0927 | 0.5132 | high→good | 0.00713 | 0.00677 |

## Threshold probe `BLOCK_rel_5`

- rule: block COMP when feature `rel_5` is on risk side (`high→good`), thr=0.000527059
- 2022: BASE 6.5 · P3 5.75 (-0.75) · probe 7.29 (0.79)
- held↑ P3 3.4758 · probe 3.6722
- tipY↑ P3 2.7325 · probe 2.1769
- flips P3 153 · probe 121 · %SAT 24.16→27.4

## 2022 COMP entries

| date | end | n | COMP% | SAT% | Δ | good | trail63 |
|---|---|---:|---:|---:|---:|---:|---:|
| 2022-03-10 | 2022-03-31 | 16 | 4.1369 | 5.6282 | -1.4914 | 0 | -0.0028 |
| 2022-05-09 | 2022-05-13 | 5 | -1.328 | -1.9875 | 0.6595 | 1 | -0.0085 |
| 2022-05-18 | 2022-05-18 | 1 | 3.1209 | 3.2007 | -0.0798 | 0 | -0.0085 |
| 2022-05-27 | 2022-06-06 | 6 | 0.5326 | -0.0242 | 0.5568 | 1 | -0.0088 |
| 2022-06-08 | 2022-06-10 | 3 | -0.1854 | -0.2544 | 0.0691 | 1 | -0.0081 |
| 2022-06-16 | 2022-06-17 | 2 | -0.589 | -0.6263 | 0.0374 | 1 | -0.01 |
| 2022-06-21 | 2022-09-26 | 69 | -1.8769 | -1.5275 | -0.3493 | 0 | -0.0065 |

Repro: `repro/fin-sat-path3-comp-entry-signal-stagea/`

