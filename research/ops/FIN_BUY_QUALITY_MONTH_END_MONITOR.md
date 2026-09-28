# FIN_BUY_QUALITY_MONTH_END_MONITOR month-end monitor (asof 2026-09-24)

**Status:** `OPERATING_OBSERVE` — **paper only**
**Books:** `BASE_LIVE_FUSE_COOL` ∥ `A_SEED_MA120` ∥ `B_MA120_OR_K9` ∥ `C_OR_K9_AND_BELOW_MA60`

## A_SEED_MA120 vs BASE_LIVE_FUSE_COOL

| Window | MDD dpp | Giveback pp | Rel NAV |
|---|---:|---:|---:|
| mtd | 1.2843388674878775 | 125.34295128972941 | 0.9576 |
| ytd | 0.6645015890345274 | 20.3257350396552 | 0.9052 |
| trailing_1y | 0.6645015890345607 | 13.837877569737778 | 0.9042 |
| heldout_2019_plus | 0.891254089012794 | 1.6253323774457984 | 0.9004 |
| sealed_2023_plus | 0.06997832732350551 | 2.91934413625754 | 0.9158 |
| full | 0.8912540890128051 | 0.7047358408561522 | 0.9195 |

## B_MA120_OR_K9 vs BASE_LIVE_FUSE_COOL

| Window | MDD dpp | Giveback pp | Rel NAV |
|---|---:|---:|---:|
| mtd | -0.004007693396046452 | 67.56994115247521 | 0.9803 |
| ytd | 0.19081392556772325 | 9.847234155588303 | 0.9546 |
| trailing_1y | 0.19081392556772325 | 6.086655512187744 | 0.9579 |
| heldout_2019_plus | 2.049328926176852 | 0.6716045044482533 | 0.9578 |
| sealed_2023_plus | 0.07808474678340227 | 0.6768092831108907 | 0.9800 |
| full | 2.04932892617683 | 0.2036864490963186 | 0.9761 |

## C_OR_K9_AND_BELOW_MA60 vs BASE_LIVE_FUSE_COOL

| Window | MDD dpp | Giveback pp | Rel NAV |
|---|---:|---:|---:|
| mtd | -0.11392016122070414 | 100.06260138132829 | 0.9684 |
| ytd | 0.6644544066672253 | 14.219941759007583 | 0.9341 |
| trailing_1y | 0.6644544066672142 | 9.681928087402447 | 0.9330 |
| heldout_2019_plus | 0.0631714759508406 | 1.4172968157049493 | 0.9127 |
| sealed_2023_plus | -0.01691535665352406 | 1.9507755290893547 | 0.9431 |
| full | 0.06317147595086281 | 0.6902924170141489 | 0.9211 |

## Alerts

- ALERT: A_SEED_MA120 ytd CAGR giveback > 3.0 pp
- PAUSE_REVIEW: A_SEED_MA120 ytd giveback > 5 pp
- ALERT: A_SEED_MA120 trailing_1y CAGR giveback > 3.0 pp
- PAUSE_REVIEW: A_SEED_MA120 trailing_1y giveback > 5 pp
- ALERT: B_MA120_OR_K9 ytd CAGR giveback > 3.0 pp
- PAUSE_REVIEW: B_MA120_OR_K9 ytd giveback > 5 pp
- ALERT: B_MA120_OR_K9 trailing_1y CAGR giveback > 3.0 pp
- PAUSE_REVIEW: B_MA120_OR_K9 trailing_1y giveback > 5 pp
- ALERT: C_OR_K9_AND_BELOW_MA60 ytd CAGR giveback > 3.0 pp
- PAUSE_REVIEW: C_OR_K9_AND_BELOW_MA60 ytd giveback > 5 pp
- ALERT: C_OR_K9_AND_BELOW_MA60 trailing_1y CAGR giveback > 3.0 pp
- PAUSE_REVIEW: C_OR_K9_AND_BELOW_MA60 trailing_1y giveback > 5 pp
- ALERT: C_OR_K9_AND_BELOW_MA60 sealed_2023_plus MDD worse than BASE_LIVE_FUSE_COOL

## Non-actions

- paper observe only
- no Soft-Frozen clip flip
- no live buy-quality wire from this monitor
- A/B/C observe posture only · cutover BLOCKED

- Soft-Frozen KEEP · cutover BLOCKED · FIN buy-quality A/B/C observe

