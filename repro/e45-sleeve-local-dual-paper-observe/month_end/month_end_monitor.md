# E45_SLEEVE_LOCAL_MONTH_END_PAPER_MONITOR month-end monitor (asof 2026-09-16)

Status: `OPERATING_OBSERVE` · paper only · base `BASE_E16_E18_E22_v2s` vs `SLEEVE_FIN_ONLY_A10`

| Window | MDD dpp | Giveback pp | Score | Rel NAV |
|---|---:|---:|---:|---:|
| mtd | -0.09188999932676634 | 72.86941180117256 | -36.52659589991305 | 0.9943 |
| ytd | -0.030235628080566013 | 11.857224040612536 | -5.9588476483868345 | 0.9505 |
| trailing_1y | -0.030235628080543808 | 4.818740511224329 | -2.439605883692708 | 0.9677 |
| heldout_2019_plus | 1.9236674731567316 | 1.3915178770534942 | 1.2279085346299845 | 0.9142 |
| sealed_2023_plus | 0.06230744262424315 | 3.27089998511505 | -1.5731425499332818 | 0.9076 |
| full | 1.9236674731567205 | 0.6699753149190135 | 1.5886798156972137 | 0.9234 |

## Alerts

- ALERT: SLEEVE_FIN_ONLY_A10 ytd MDD worse than BASE_E16_E18_E22_v2s
- ALERT: SLEEVE_FIN_ONLY_A10 ytd CAGR giveback > 3.0 pp
- PAUSE_REVIEW: SLEEVE_FIN_ONLY_A10 ytd giveback > 5 pp
- ALERT: SLEEVE_FIN_ONLY_A10 trailing_1y MDD worse than BASE_E16_E18_E22_v2s
- ALERT: SLEEVE_FIN_ONLY_A10 trailing_1y CAGR giveback > 3.0 pp

## Non-actions

- paper observe only
- no Soft-Frozen clip flip
- no E45 stitch
- no live wire from this monitor

