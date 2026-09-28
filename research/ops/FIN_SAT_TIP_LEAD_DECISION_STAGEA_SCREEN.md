# FIN_SAT_TIP_LEAD_DECISION_STAGEA_SCREEN

Date: 2026-09-28 · Generated `2026-09-28T14:29:12Z`
Status: **LEAD_SIGNAL** · Soft-Frozen **KEEP** · parents **KEEP** · live wire **false**

## Lead diagnosis

- enters=813 (tip 137) · exits=76 · lead_signal=`True`

| feat | k | IC | lift |
|---|---:|---:|---:|
| trail_rel_63 | 1 | -0.7273 | 2.032 |
| trail_rel_63 | 2 | -0.7147 | 2.022 |
| trail_rel_63 | 3 | -0.7004 | 2.008 |
| trail_rel_63 | 5 | -0.6805 | 1.994 |
| comp_sells_21 | 5 | 0.1784 | 1.255 |
| comp_sells_21 | 3 | 0.1735 | 1.251 |
| comp_sells_21 | 2 | 0.1721 | 1.243 |
| comp_sells_21 | 1 | 0.1702 | 1.242 |

## Pre-enter (−5..−1) deltas

| feat | pre | base | Δ |
|---|---:|---:|---:|
| comp_sells_21 | 24.202214 | 19.158098 | 5.044116 |
| bearcrisis | 0.355474 | 0.23893 | 0.116543 |
| crisis | 0.219926 | 0.125706 | 0.09422 |
| zz08_bear | 0.214268 | 0.180089 | 0.034179 |
| trail_rel_63 | -0.021821 | 3.2e-05 | -0.021853 |
| mdd0050_63 | -0.085695 | -0.078973 | -0.006722 |

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

Verdict: **`LEAD_SIGNAL`**

Label: `FIN_SAT_TIP_LEAD_DECISION_STAGEA_SCREEN_2026-09-28__LEAD_SIGNAL`
