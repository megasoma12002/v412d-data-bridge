# Stage-3 Deep Autopsy: 2021–2022 Validation Excess

Diagnosis only for **C2 / C4 / C8**. **No retune. No promotion.**

## Headlines

- C4 weak-year mean daily excess -0.000314 vs other-years 0.000451
- C4 weak-year turnover 0.0230 vs other 0.0208
- Common negative-excess months across C2/C4/C8: 13
- C4 weak-year RISK_ON excess=-0.0004604064626040927, RISK_OFF=6.253160639969535e-05

## Common bad months (all three refs negative excess)

- 2021-02: C2=-0.0272, C4=-0.0301, C8=-0.0301
- 2021-03: C2=-0.0349, C4=-0.0380, C8=-0.0380
- 2021-06: C2=-0.0478, C4=-0.0515, C8=-0.0515
- 2021-07: C2=-0.0045, C4=-0.0009, C8=-0.0009
- 2021-09: C2=-0.0136, C4=-0.0224, C8=-0.0224
- 2021-12: C2=-0.0278, C4=-0.0245, C8=-0.0245
- 2022-02: C2=-0.0175, C4=-0.0212, C8=-0.0212
- 2022-03: C2=-0.0212, C4=-0.0272, C8=-0.0272
- 2022-04: C2=-0.0129, C4=-0.0184, C8=-0.0184
- 2022-05: C2=-0.0714, C4=-0.0567, C8=-0.0567
- 2022-06: C2=-0.0100, C4=-0.0139, C8=-0.0139
- 2022-08: C2=-0.0638, C4=-0.0397, C8=-0.0397
- 2022-12: C2=-0.0164, C4=-0.0163, C8=-0.0137
## C2

| | 2021–2022 | 2019–2020 |
|---|---:|---:|
| Mean daily excess | -0.000193 | 0.000281 |
| Hit rate | 47.8% | 49.8% |
| Avg turnover | 2.79% | 2.08% |
| Cost Δ | 0.0995 | 0.0416 |
| Min DD | -29.38% | -26.84% |

Regime split (weak years):

- RISK_ON: days=353, mean_excess=-0.000305284627187469, hit=0.4702549575070821, turnover=0.022896965341240253
- RISK_OFF: days=137, mean_excess=9.467209778311439e-05, hit=0.49635036496350365, turnover=0.04075217047410226

Corr(excess, ·) in weak years:

- breadth_63d: 0.01817159432413564
- market_median_mom_63d: 0.031550752639797966
- turnover: -0.09737101536949988
- drawdown: 0.03719684104457255

Top industries (buy gross, weak years):

- 電子工業: share=0.175, n=38
- 半導體業: share=0.162, n=29
- 金融保險: share=0.125, n=23
- None: share=0.076, n=11
- 光電業: share=0.075, n=11

## C4

| | 2021–2022 | 2019–2020 |
|---|---:|---:|
| Mean daily excess | -0.000314 | 0.000451 |
| Hit rate | 47.8% | 53.3% |
| Avg turnover | 2.30% | 2.08% |
| Cost Δ | 0.0869 | 0.0450 |
| Min DD | -31.87% | -26.29% |

Regime split (weak years):

- RISK_ON: days=353, mean_excess=-0.0004604064626040927, hit=0.47875354107648727, turnover=0.018951220271637363
- RISK_OFF: days=137, mean_excess=6.253160639969535e-05, hit=0.4744525547445255, turnover=0.03332553222574609

Corr(excess, ·) in weak years:

- breadth_63d: 0.02253837382098625
- market_median_mom_63d: 0.035857090395215924
- turnover: -0.0841312586423776
- drawdown: 0.02924357172603817

Top industries (buy gross, weak years):

- 半導體業: share=0.163, n=36
- 電子工業: share=0.140, n=34
- 金融保險: share=0.105, n=18
- 光電業: share=0.096, n=16
- None: share=0.094, n=15

## C8

| | 2021–2022 | 2019–2020 |
|---|---:|---:|
| Mean daily excess | -0.000322 | 0.000451 |
| Hit rate | 48.0% | 53.3% |
| Avg turnover | 2.28% | 2.08% |
| Cost Δ | 0.0862 | 0.0450 |
| Min DD | -31.87% | -26.29% |

Regime split (weak years):

- RISK_ON: days=353, mean_excess=-0.0004546194285895155, hit=0.48158640226628896, turnover=0.018950331750642934
- RISK_OFF: days=137, mean_excess=2.0773339286765257e-05, hit=0.4744525547445255, turnover=0.03266423057978882

Corr(excess, ·) in weak years:

- breadth_63d: 0.023483767598046483
- market_median_mom_63d: 0.036964748965751006
- turnover: -0.08406184416459576
- drawdown: 0.030559282340966273

Top industries (buy gross, weak years):

- 半導體業: share=0.165, n=36
- 電子工業: share=0.141, n=34
- 金融保險: share=0.105, n=18
- 光電業: share=0.097, n=16
- None: share=0.095, n=15

## Implication

2021–2022 excess failure is shared across C2/C4/C8 and concentrated in specific months; portfolio micro-differences do not remove it. Next leverage should be new alpha features / regime definitions selected on OOF, not retuning these locks.

Artifact: `reports/stage3_2021_2022_excess_autopsy.json`
