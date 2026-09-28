# FIN_SAT_LOCAL_MUTEX_STAGEA_SCREEN

Date: 2026-09-28 · Generated `2026-09-28T14:18:26Z`
Status: **TIP_LAG_BLOCK** · Soft-Frozen **KEEP** · parents **KEEP** · live wire **false**

## Diagnosis

- local_mutex_diag=`True` · score=`0.6162`
- P(SAT_LEAD|tip)=56.61% vs pre=18.73% · Δ=37.88
- P(COMP_LEAD|tip)=8.26% vs pre=32.0% · Δpre−tip=23.74
- tip damage frac from SAT_LEAD=`1.0755` · tip COMP_LEAD conflict=`8.26%`
- P(drag|tip)=69.42% vs pre=41.71%

## Books

| ID | fam | %SAT | flips | heldCAGR↑ | tipCAGR↑ | tipClean | shaped | HIT/UB |
|---|---|---:|---:|---:|---:|---|---|---|
| CTRL_LIVE_A10 | ctrl | 0.0 | 0 | -0.0 | 0.0 | True | False | · |
| REF_SAT_RELAX | ref | 100.0 | 0 | 0.3343 | 0.6801 | True | False | · |
| REF_COMP_H150_A20 | ref | 0.0 | 0 | 0.5415 | -13.3591 | False | False | · |
| UB_TIPWIN_SAT | ub | 7.19 | 1 | 1.632 | 0.6801 | True | True | UB |
| UB_STATE_SD | ub | 24.16 | 153 | 3.4758 | 2.7325 | True | True | UB |
| R_SAT_LEAD_L1 | switch | 24.13 | 153 | 1.2962 | -8.4925 | False | False | · |
| R_DRAG_L1 | switch | 47.22 | 189 | 1.1905 | -5.1372 | False | False | · |
| R_TIPLIKE_L1 | switch | 18.54 | 107 | 0.3413 | -10.2087 | False | False | · |
| R_PRE_COMP_TIP_SAT_L1 | switch | 44.96 | 25 | -0.0905 | -2.7973 | False | False | · |

Verdict: **`TIP_LAG_BLOCK`**

Label: `FIN_SAT_LOCAL_MUTEX_STAGEA_SCREEN_2026-09-28__TIP_LAG_BLOCK`
