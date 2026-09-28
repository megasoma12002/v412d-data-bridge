# FIN_SAT_MUTEX_FEAT_STAGEA_SCREEN

Date: 2026-09-28 · Generated `2026-09-28T13:18:57Z`
Status: **TIP_MDD_ONLY** · Soft-Frozen **KEEP** · parent observes **KEEP** · live wire **false**

Year mutex features → pre-registered lag-1 switches · HIT: tip-clean + held≥+0.10 + vs SAT +0.05.

## Yearly COMP vs SAT

| year | winner | ΔCOMP−SAT | COMP% | SAT% | %Bull | %Bear | %Crisis | minMDD0050_63 |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 2012 | COMP | 0.65 | 1.2 | 0.55 | 100.0 | 0.0 | 0.0 | -7.06 |
| 2013 | SAT | -1.33 | 5.93 | 7.26 | 97.97 | 2.03 | 0.0 | -9.71 |
| 2014 | COMP | 1.69 | 8.89 | 7.2 | 85.89 | 14.11 | 0.0 | -9.24 |
| 2015 | SAT | -4.2 | -5.76 | -1.56 | 44.26 | 24.18 | 31.56 | -19.58 |
| 2016 | SAT | -1.6 | 13.25 | 14.85 | 78.28 | 1.23 | 20.49 | -14.87 |
| 2017 | COMP | 3.62 | 21.36 | 17.74 | 100.0 | 0.0 | 0.0 | -5.45 |
| 2018 | SAT | -0.76 | 6.79 | 7.55 | 58.7 | 38.46 | 2.43 | -15.8 |
| 2019 | COMP | 0.14 | 20.96 | 20.82 | 80.17 | 18.18 | 1.65 | -13.37 |
| 2020 | COMP | 2.77 | 9.17 | 6.4 | 75.51 | 12.24 | 11.02 | -28.22 |
| 2021 | SAT | -1.15 | 20.84 | 21.99 | 86.89 | 2.46 | 0.0 | -10.44 |
| 2022 | SAT | -5.6 | 0.7 | 6.3 | 19.51 | 23.58 | 56.91 | -20.84 |
| 2023 | COMP | 10.46 | 23.09 | 12.63 | 87.39 | 1.26 | 11.34 | -10.46 |
| 2024 | SAT | -0.42 | 9.88 | 10.3 | 86.78 | 0.0 | 8.26 | -21.3 |
| 2025 | COMP | 4.45 | 16.15 | 11.7 | 71.73 | 18.14 | 10.13 | -27.48 |
| 2026 | SAT | -8.66 | 26.45 | 35.11 | 37.5 | 0.0 | 27.27 | -15.37 |

## Feature contrast (mean COMP-win − SAT-win)

```json
{
  "pct_bull": 22.077,
  "pct_bear": -2.359,
  "pct_crisis": -13.488,
  "pct_sideways": -6.232,
  "mean_mdd0050_63": 2.011,
  "min_mdd0050_63": 1.52,
  "mean_r0050_63": 0.145,
  "comp_minus_sat_pp": 6.362
}
```

COMP-win years: [2012, 2014, 2017, 2019, 2020, 2023, 2025] · SAT-win years: [2013, 2015, 2016, 2018, 2021, 2022, 2024, 2026]

## Books

| ID | fam | %SAT | flips | heldCAGR↑ | tipCAGR↑ | tipClean | vsSAT | HIT |
|---|---|---:|---:|---:|---:|---|---|---|
| CTRL_LIVE_A10 | ctrl | 0.0 | 0 | -0.0 | 0.0 | True | False | False |
| REF_SAT_RELAX | ref | 100.0 | 0 | 0.3343 | 0.6801 | True | False | False |
| REF_COMP_H150_A20 | ref | 0.0 | 0 | 0.5415 | -13.3591 | False | True | False |
| SW_CRISIS_SAT | switch | 12.57 | 52 | -0.3302 | -18.7345 | False | False | False |
| SW_BEARCRISIS_SAT | switch | 23.89 | 90 | -0.5931 | -18.7345 | False | False | False |
| SW_BULL_COMP | switch | 27.01 | 107 | 0.2813 | -10.0776 | False | False | False |
| SW_0050DD08_SAT | switch | 35.39 | 33 | 1.4626 | -5.7836 | False | True | False |
| SW_0050DD12_SAT | switch | 15.3 | 17 | 0.0688 | -7.8897 | False | False | False |
| SW_0050RET63NEG_SAT | switch | 26.18 | 170 | -0.3212 | -13.3423 | False | False | False |
| ORACLE_YEAR | diag | 56.14 | 11 | 2.7486 | 0.6801 | True | True | False |

Verdict: **`TIP_MDD_ONLY`**

Label: `FIN_SAT_MUTEX_FEAT_STAGEA_SCREEN_2026-09-28__TIP_MDD_ONLY`
