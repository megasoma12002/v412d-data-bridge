# Stage-8A Failure Signature (Diagnosis Only)

Shared 13 C2/C4/C8 bad months. **No selection. No retune. E45 untouched.**

## Headlines

- Bad-month days: 264; other val days: 713
- ALPHA_STRESS_V1 coverage: bad=0.3106060606060606, other_val=0.23842917251051893, oof=0.17697768762677485
- Thresholds (diagnosis centers): mom_ic_lag21≤0.0057, mom_minus_val≥-0.0005

## Top discriminating features (|bad − other val|)

| feature | bad | other val | Δ | OOF |
|---|---:|---:|---:|---:|
| crisis_vote2 | 0.0000 | 0.0870 | -0.0870 | 0.1379 |
| risk_on | 0.7652 | 0.8303 | -0.0651 | 0.7601 |
| mkt_vol_60d | 0.5075 | 0.4497 | 0.0578 | 0.3772 |
| val_ic_same_day | 0.0824 | 0.0248 | 0.0576 | 0.0382 |
| breadth_63d | 0.6610 | 0.7036 | -0.0426 | 0.6263 |
| crisis_strict | 0.0000 | 0.0407 | -0.0407 | 0.1207 |
| mom_ic_lag21 | -0.0119 | -0.0409 | 0.0290 | -0.0010 |
| val_ic_lag21 | 0.0608 | 0.0320 | 0.0288 | 0.0390 |
| mkt_mom_63d | 0.0948 | 0.1157 | -0.0209 | 0.0515 |
| mom_ic_same_day | -0.0230 | -0.0407 | 0.0176 | -0.0009 |
| vol20 | 0.1543 | 0.1493 | 0.0050 | 0.1398 |
| dd120 | -0.0376 | -0.0408 | 0.0032 | -0.0552 |
| disp_mom_fam | 0.2406 | 0.2415 | -0.0008 | 0.2439 |
| mean_grw_fam | 0.4985 | 0.4990 | -0.0005 | 0.5010 |
| grw_minus_val | -0.0020 | -0.0015 | -0.0005 | 0.0003 |

## Proposed detector for Stage-8B (causal)

- `ALPHA_STRESS_V1`: risk_on AND mom_ic_lag21 <= bad_month_p50(mom_ic_lag21) AND mom_minus_val >= other_val_p50(mom_minus_val) AND crisis_vote2 == False
- 8B screens threshold grid on **OOF only**; do not refit cuts on 2021–22.

## Top OOF analog months (by ALPHA_STRESS_V1 share)

- 2016-09: stress_share=1.00, mom_ic_lag21=-0.1232027137809159, risk_on=1.00
- 2018-01: stress_share=1.00, mom_ic_lag21=-0.09460920294174534, risk_on=1.00
- 2017-05: stress_share=1.00, mom_ic_lag21=-0.08687321068047558, risk_on=1.00
- 2016-07: stress_share=1.00, mom_ic_lag21=-0.09190162021690007, risk_on=1.00
- 2016-05: stress_share=0.86, mom_ic_lag21=-0.028201695124820784, risk_on=0.86
- 2018-08: stress_share=0.78, mom_ic_lag21=-0.2077262999832301, risk_on=1.00
- 2016-03: stress_share=0.78, mom_ic_lag21=-0.1410549621444921, risk_on=1.00
- 2016-02: stress_share=0.77, mom_ic_lag21=-0.28392684444161065, risk_on=0.77

## Implication

Bad months are RISK_ON / non-EW-crisis with weak trailing momentum IC and elevated mom-vs-value style spread. Stage-8B should OOF-select controllers on ALPHA_STRESS detectors, not EW-crisis cash.

Artifact: `reports/stage8a_failure_signature.json`
