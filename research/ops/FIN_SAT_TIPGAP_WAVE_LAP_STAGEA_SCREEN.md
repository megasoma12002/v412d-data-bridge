# FIN_SAT_TIPGAP_WAVE_LAP_STAGEA_SCREEN

Date: 2026-09-28 · Generated `2026-09-28T13:40:20Z`
Status: **WAVE_LAP_SIGNAL** · Soft-Frozen **KEEP** · parents **KEEP** · live wire **false**

Morlet CWT + numerical unilateral Laplace on tip-gap series · lag-1 IC vs fwd_rel_21.

## Wavelet (global mean power)

| series | top periods (tdays) | max_frac | tip top |
|---|---|---:|---|
| daily_rel | [53.0, 57.0, 216.0] | 0.02656 | [18.0, 19.0, 16.0] |
| trail_rel_63 | [234.0, 216.0, 200.0] | 0.09024 | [320.0, 115.0, 107.0] |

## Laplace peaks (trail_rel_63)

| period | sigma | mag_frac |
|---:|---:|---:|
| 230.94 | 0.0 | 1.0 |
| 177.78 | 0.0 | 0.68395 |
| 114.95 | 0.0 | 0.49949 |
| 300.0 | 0.0 | 0.4246 |
| 81.1 | 0.0 | 0.1731 |

## Lag-1 IC features

| method | series | feature | IC | gate |
|---|---|---|---:|---|
| wavelet | daily_rel | ridge | 0.0148 | False |
| wavelet | daily_rel | band_85_128 | -0.0347 | False |
| wavelet | daily_rel | band_200_280 | -0.0288 | False |
| wavelet | trail_rel_63 | ridge | -0.0558 | True |
| wavelet | trail_rel_63 | band_85_128 | -0.03 | False |
| wavelet | trail_rel_63 | band_200_280 | -0.0252 | False |
| laplace | daily_rel | osc_p230.94_s0.0 | 0.0695 | True |
| laplace | daily_rel | osc_p114.95_s0.0 | 0.0475 | True |
| laplace | daily_rel | osc_p177.78_s0.0 | -0.0015 | False |
| laplace | trail_rel_63 | osc_p230.94_s0.0 | 0.0686 | True |
| laplace | trail_rel_63 | osc_p177.78_s0.0 | 0.0263 | False |
| laplace | trail_rel_63 | osc_p114.95_s0.0 | 0.0079 | False |

Verdict: **`WAVE_LAP_SIGNAL`**

Label: `FIN_SAT_TIPGAP_WAVE_LAP_STAGEA_SCREEN_2026-09-28__WAVE_LAP_SIGNAL`
