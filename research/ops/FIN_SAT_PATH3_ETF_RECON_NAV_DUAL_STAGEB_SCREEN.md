# FIN_SAT_PATH3_ETF_RECON_NAV_DUAL_STAGEB_SCREEN

Date: 2026-09-30 · Verdict: **`ETF_NAV_DUAL_HIT`** · fill=**`t0`**
Register: **0kag** · parent 0kae · end=`2026-09-24` · flips KEEP/RATIO=199/199 · etf_moves RATIO=199

## Improvement (T+0): `LEDGER_SOFT_RATIO` − `KEEP` (pp)

| Window | CAGR lift pp | MDD improve pp | KEEP → RATIO CAGR |
|---|---:|---:|---|
| full | 0.9479 | 0.3091 | 0.074972 → 0.084451 |
| heldout_2019_plus | 1.6839 | 0.3091 | 0.099363 → 0.116202 |
| sealed_2023_plus | 2.7306 | 7.1272 | 0.114482 → 0.141788 |

## Tip (T+0)

- YTD CAGR lift pp: **3.7838** · MDD improve pp: 0.0912
- Trailing 1y CAGR lift pp: **1.4372** · MDD improve pp: 0.0912

## Sensitivity EOD/T+1 (prior timing)

- full CAGR lift pp: 0.8217 · held: 1.6469 · sealed MDD improve: 9.883
- tipY / tip1y: 1.882 / -0.4106

## Yearly (T+0) ret W–L / MDD improve W–L

- Ret **7–8** · MDD improve **8–7**

| Year | KEEP ret% | RATIO ret% | Ret lift pp | MDD improve pp |
|---:|---:|---:|---:|---:|
| 2012 | 1.07 | 1.07 | +0.00 | +0.00 |
| 2013 | 3.37 | 3.28 | -0.09 | -0.07 |
| 2014 | 4.78 | 4.46 | -0.32 | +0.00 |
| 2015 | -7.86 | -8.04 | -0.18 | +0.11 |
| 2016 | 11.98 | 11.44 | -0.54 | -0.41 |
| 2017 | 14.67 | 14.69 | +0.02 | -0.32 |
| 2018 | 3.64 | 5.15 | +1.51 | +0.35 |
| 2019 | 19.37 | 19.53 | +0.16 | -0.16 |
| 2020 | -1.14 | -2.65 | -1.52 | +0.31 |
| 2021 | 21.72 | 22.76 | +1.05 | +0.35 |
| 2022 | -4.19 | -0.61 | +3.58 | +0.79 |
| 2023 | 17.90 | 17.25 | -0.65 | -0.68 |
| 2024 | 6.81 | 1.89 | -4.91 | -0.13 |
| 2025 | -12.67 | -1.68 | +10.99 | +8.43 |
| 2026 | 32.55 | 34.86 | +2.31 | +0.09 |

## ETF turnover on flips

- KEEP sum |Δw_0050|: 0.0
- RATIO sum |Δw_0050|: 2.704911

## Context FULL_DAILY − KEEP (T+0)

| full | 3.4939 | 2.029 | 0.074972 → 0.109911 |
| held | 5.8263 | 2.029 | 0.099363 → 0.157626 |

Repro: `PYTHONPATH=scripts python3 scripts/fin_sat_path3_etf_recon_nav_dual_stageb.py`

Label: `FIN_SAT_PATH3_ETF_RECON_NAV_DUAL_STAGEB_SCREEN_2026-09-30__ETF_NAV_DUAL_HIT__T0`
