# FIN_SAT_FFT_EXOG_AND_STAGEA_SCREEN

Date: 2026-09-29 · `2026-09-29T04:50:57Z` · Verdict **`EXOG_FFT_WEAK`**

## Entry feature screen

| feature | IC | OOF | held | hit | side |
|---|---:|---:|---:|---:|---|
| `rel_5` | 0.1713 | -0.0075 | 0.3508 | 0.5921 | high→good |
| `endo_dphase` | 0.1277 | 0.1274 | 0.1548 | 0.5467 | high→good |
| `exog_dphase` | -0.1215 | 0.0474 | -0.4327 | 0.52 | low→good |
| `exog_recon` | 0.089 | 0.1292 | 0.071 | 0.6 | high→good |
| `endo_recon` | -0.0846 | -0.2266 | 0.1242 | 0.5467 | low→good |
| `exog_phase` | 0.0689 | 0.0506 | 0.0915 | 0.52 | low→good |
| `r0050_63` | 0.0113 | -0.0671 | 0.127 | 0.5395 | high→good |
| `exog_amp` | -0.0102 | -0.0063 | 0.0673 | 0.52 | low→good |

## Books

| id | fam | held↑ | tipY↑ | tipClean | y2022 | shaped |
|---|---|---:|---:|---|---:|---|
| `P3_T0_STATE` | ref | 3.4758 | 2.7325 | True | -0.75 | True |
| `AND_TD_R0050` | and | 1.8763 | -11.0737 | False | -0.7 | False |
| `AND_EXOG_exog_recon` | and | 1.7007 | -3.4475 | False | -4.52 | False |
| `AND_EXOG_exog_amp` | and | 2.1266 | -3.6757 | False | -5.06 | False |
| `AND_EXOG_exog_dphase` | and | 2.0253 | 1.4879 | True | -5.29 | True |
| `AND_EXOG_exog_phase` | and | 1.9518 | -4.3627 | False | -6.72 | False |
| `BLOCK_EXOG_BEST` | block | 3.1951 | -1.1323 | False | 0.76 | False |

Repro: `repro/fin-sat-fft-exog-tilt-stagea/`

