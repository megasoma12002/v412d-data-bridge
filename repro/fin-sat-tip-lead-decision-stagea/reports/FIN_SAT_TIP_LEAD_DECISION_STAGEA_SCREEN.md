# FIN_SAT_TIP_LEAD_DECISION_STAGEA_SCREEN

Date: 2026-09-28 · Generated `2026-09-28T14:30:48Z`
Status: **TIP_LAG_BLOCK** · Soft-Frozen **KEEP** · parents **KEEP** · live wire **false**

## Lead diagnosis

- enters=77 (tip 8) · exits=76 · lead_signal=`True`

| feat | k | IC | lift |
|---|---:|---:|---:|
| trail_rel_63 | 2 | -0.1067 | 1.933 |
| trail_rel_63 | 1 | -0.1004 | 1.96 |
| trail_rel_63 | 5 | -0.0998 | 1.777 |
| trail_rel_63 | 3 | -0.0987 | 1.855 |
| zz08_bear | 2 | 0.0369 | 1.514 |
| zz08_bear | 3 | 0.0368 | 1.514 |
| zz08_bear | 5 | 0.0368 | 1.514 |
| crisis | 3 | -0.0341 | 0.413 |

## Pre-enter (−5..−1) deltas

| feat | pre | base | Δ |
|---|---:|---:|---:|
| comp_sells_21 | 18.54026 | 19.158098 | -0.617838 |
| zz08_bear | 0.27013 | 0.180089 | 0.090041 |
| crisis | 0.062338 | 0.125706 | -0.063368 |
| bearcrisis | 0.223377 | 0.23893 | -0.015554 |
| mdd0050_63 | -0.070579 | -0.078973 | 0.008394 |
| trail_rel_63 | -0.007265 | 3.2e-05 | -0.007297 |

## Books

| ID | fam | %SAT | heldCAGR↑ | tipCAGR↑ | tipClean | shaped | mark |
|---|---|---:|---:|---:|---|---|---|
| CTRL_LIVE_A10 | ctrl | 0.0 | -0.0 | 0.0 | True | False | · |
| REF_SAT_RELAX | ref | 100.0 | 0.3343 | 0.6801 | True | False | · |
| REF_COMP_H150_A20 | ref | 0.0 | 0.5415 | -13.3591 | False | False | · |
| UB_ENTER_M1 | ub | 26.45 | 3.4426 | 1.7875 | True | True | UB |
| UB_STATE_SD | ub | 24.16 | 3.4758 | 2.7325 | True | True | UB |
| R_SAT_LEAD_L1 | switch | 24.13 | 1.2962 | -8.4925 | False | False | · |
| R_HALF_THETA_L1 | switch | 34.86 | 1.4528 | -5.9029 | False | False | · |
| R_SLOPE_EARLY_L1 | switch | 17.89 | 0.8112 | -6.1698 | False | False | · |
| R_CONF_EARLY_L1 | switch | 35.57 | 2.0233 | -3.636 | False | False | · |
| R_LEAD_OR_STATE_L1 | switch | 24.78 | 1.3752 | -8.4925 | False | False | · |

Verdict: **`TIP_LAG_BLOCK`**

Label: `FIN_SAT_TIP_LEAD_DECISION_STAGEA_SCREEN_2026-09-28__TIP_LAG_BLOCK`
