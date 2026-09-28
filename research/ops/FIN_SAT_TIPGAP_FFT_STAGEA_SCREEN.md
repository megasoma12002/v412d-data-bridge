# FIN_SAT_TIPGAP_FFT_STAGEA_SCREEN

Date: 2026-09-28 · Generated `2026-09-28T13:35:42Z`
Status: **FFT_SIGNAL** · Soft-Frozen **KEEP** · parents **KEEP** · live wire **false**

FFT/Welch on tip-gap related series · bandpass lag-1 IC vs fwd_rel_21.

## Spectra (top period / power frac)

| series | n | method | top_period_tdays | power_frac |
|---|---:|---|---:|---:|
| daily_rel | 3365 | periodogram | 2.89 | 0.00493 |
| trail_rel_21 | 3345 | welch | 128.0 | 0.18204 |
| trail_rel_63 | 3303 | welch | 256.0 | 0.43131 |
| trail_drag | 3365 | welch | 256.0 | 0.30944 |
| r0050 | 3365 | periodogram | 16.58 | 0.00438 |
| monthly_rel | 166 | periodogram_monthly | 53.5 | 0.0432 |
| tip_daily_rel | 242 | periodogram | 2.92 | 0.03738 |
| tip_trail_rel_63 | 242 | periodogram | 121.0 | 0.68947 |

## Bandpass lag-1 IC

| src | period | power_frac | IC | gate |
|---|---:|---:|---:|---|
| trail_rel_63 | 256.0 | 0.43131 | 0.132 | True |
| trail_rel_63 | 128.0 | 0.3261 | -0.206 | True |
| trail_rel_21 | 85.33 | 0.13276 | -0.3783 | True |

Verdict: **`FFT_SIGNAL`**

Label: `FIN_SAT_TIPGAP_FFT_STAGEA_SCREEN_2026-09-28__FFT_SIGNAL`
