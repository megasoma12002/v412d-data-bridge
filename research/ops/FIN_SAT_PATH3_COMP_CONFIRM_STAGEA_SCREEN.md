# FIN_SAT_PATH3_COMP_CONFIRM_STAGEA_SCREEN

Date: 2026-09-29 · generated `2026-09-29T03:22:04Z`
Verdict: **`COMP_CONFIRM_NO_EDGE`** · Soft-Frozen KEEP · Path3 observe KEEP · fill/emit OFF · no live

## Head-to-head

| Book | fam | held↑ | tipY↑ | tip1y↑ | tipClean | shaped | y2022% | y2022−BASE | flips | %SAT | score |
|---|---|---:|---:|---:|---|---|---:|---:|---:|---:|---:|
| `CTRL_LIVE_A10` | ctrl | -0.0 | 0.0 | 0.0 | True | False | 6.5 | 0.0 | 0 | 0.0 | 1.0 |
| `P3_T0_STATE` | path_ref | 3.4758 | 2.7325 | 1.7356 | True | True | 5.75 | -0.75 | 153 | 24.16 | 8.2493 |
| `COMP_CONFIRM_D1` | confirm | 3.4758 | 2.7325 | 1.7356 | True | True | 5.75 | -0.75 | 153 | 24.16 | 8.2493 |
| `COMP_CONFIRM_D2` | confirm | 2.6991 | -2.9826 | -2.0482 | False | False | 5.57 | -0.93 | 115 | 26.42 | -1.19 |
| `COMP_CONFIRM_D3` | confirm | 2.3799 | -4.1267 | -2.8104 | False | False | 4.81 | -1.69 | 99 | 28.11 | -3.6054 |
| `COMP_CONFIRM_D5` | confirm | 2.2123 | -6.2285 | -4.2147 | False | False | 4.91 | -1.59 | 69 | 30.79 | -5.0329 |
| `SAT_MINSTAY_5` | minstay | 3.0478 | 0.7621 | 0.4354 | True | True | 5.73 | -0.77 | 115 | 27.01 | 4.8558 |
| `SAT_MINSTAY_10` | minstay | 2.7075 | -1.9644 | -1.3712 | False | False | 5.54 | -0.96 | 97 | 29.81 | 0.3307 |
| `SAT_MINSTAY_21` | minstay | 2.5997 | -0.4617 | -0.3744 | False | False | 5.76 | -0.74 | 73 | 35.3 | 2.5869 |
| `COMBO_D2_S10` | combo | 2.461 | -5.7791 | -3.914 | False | False | 5.46 | -1.04 | 87 | 30.34 | -4.5092 |
| `COMBO_D3_S10` | combo | 2.3073 | -6.2705 | -4.2428 | False | False | 4.89 | -1.61 | 79 | 30.82 | -4.9479 |
| `COMBO_D2_S21` | combo | 2.4845 | -2.2419 | -1.5557 | False | False | 5.74 | -0.76 | 67 | 35.22 | -0.2085 |
| `COMBO_D3_S21` | combo | 2.1996 | -3.8466 | -2.6236 | False | False | 4.59 | -1.91 | 61 | 34.62 | -3.4755 |

Best by score: `COMP_CONFIRM_D1` · Best 2022 gap: `SAT_MINSTAY_21`

Repro: `repro/fin-sat-path3-comp-confirm-stagea/`

