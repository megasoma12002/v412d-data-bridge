# Stage-2 Validation Excess Diagnosis (C2 / C4 / C8)

Diagnosis only. **No retune. No promotion.**

## Purpose

Explain why references that pass validation turnover still fail bootstrap ≥ 0.70 on 2019–2022.

## C2

- Mean daily excess: `0.000043`
- Excess hit rate: `0.488`
- Mean turnover: `2.43%`, total cost `0.1429`
- Max DD: `-29.38%`
- Top10 name gross share: `0.195`
- Industry top share: `0.17959147511009027` (半導體業)

| Year | Strat | Proxy | Excess≈ | Mean d.excess | Hit | Turnover | CostΔ |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2019 | 36.0% | 25.3% | 10.7% | 0.00036 | 49.8% | 1.94% | 0.016 |
| 2020 | 35.8% | 29.6% | 6.2% | 0.00021 | 49.8% | 2.21% | 0.025 |
| 2021 | 33.5% | 34.9% | -1.3% | -0.00003 | 50.4% | 2.06% | 0.038 |
| 2022 | -14.0% | -5.2% | -8.9% | -0.00036 | 45.1% | 3.51% | 0.061 |

Worst excess months:

- 2022-05: sum_excess=-0.0714, turnover=0.00%
- 2022-08: sum_excess=-0.0638, turnover=8.23%
- 2020-08: sum_excess=-0.0563, turnover=0.00%
- 2021-06: sum_excess=-0.0478, turnover=2.56%
- 2019-08: sum_excess=-0.0417, turnover=0.00%

## C4

- Mean daily excess: `0.000067`
- Excess hit rate: `0.505`
- Mean turnover: `2.19%`, total cost `0.1338`
- Max DD: `-31.87%`
- Top10 name gross share: `0.189`
- Industry top share: `0.1813514159857523` (半導體業)

| Year | Strat | Proxy | Excess≈ | Mean d.excess | Hit | Turnover | CostΔ |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2019 | 45.7% | 25.3% | 20.4% | 0.00069 | 53.9% | 1.89% | 0.017 |
| 2020 | 36.3% | 29.6% | 6.7% | 0.00022 | 52.7% | 2.27% | 0.028 |
| 2021 | 29.7% | 34.9% | -5.1% | -0.00015 | 51.2% | 2.14% | 0.042 |
| 2022 | -17.1% | -5.2% | -11.9% | -0.00047 | 44.3% | 2.45% | 0.045 |

Worst excess months:

- 2022-09: sum_excess=-0.0919, turnover=0.00%
- 2019-05: sum_excess=-0.0760, turnover=0.79%
- 2022-05: sum_excess=-0.0567, turnover=0.00%
- 2020-08: sum_excess=-0.0544, turnover=0.00%
- 2021-06: sum_excess=-0.0515, turnover=2.76%

## C8

- Mean daily excess: `0.000063`
- Excess hit rate: `0.506`
- Mean turnover: `2.18%`, total cost `0.1332`
- Max DD: `-31.87%`
- Top10 name gross share: `0.190`
- Industry top share: `0.182149732501127` (半導體業)

| Year | Strat | Proxy | Excess≈ | Mean d.excess | Hit | Turnover | CostΔ |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2019 | 45.7% | 25.3% | 20.4% | 0.00069 | 53.9% | 1.89% | 0.017 |
| 2020 | 36.3% | 29.6% | 6.7% | 0.00022 | 52.7% | 2.27% | 0.028 |
| 2021 | 29.7% | 34.9% | -5.1% | -0.00015 | 51.2% | 2.14% | 0.042 |
| 2022 | -17.4% | -5.2% | -12.2% | -0.00049 | 44.7% | 2.41% | 0.044 |

Worst excess months:

- 2022-09: sum_excess=-0.0919, turnover=0.00%
- 2019-05: sum_excess=-0.0760, turnover=0.79%
- 2022-05: sum_excess=-0.0567, turnover=0.00%
- 2020-08: sum_excess=-0.0544, turnover=0.00%
- 2021-06: sum_excess=-0.0515, turnover=2.76%

## Synthesis

Do not retune C2/C4/C8. Next stage should change the alpha/model hypothesis on OOF (feature family / regime / lambda), because portfolio-rule variants that already clear validation turnover still fail excess bootstrap in the same weak years.

Artifact: `reports/stage2_val_excess_diagnosis.json`
