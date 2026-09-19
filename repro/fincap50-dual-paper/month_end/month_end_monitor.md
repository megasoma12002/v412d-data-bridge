# FIN_CAP_50_MONTH_END_PAPER_MONITOR month-end monitor (asof 2026-09-16)

Status: `OPERATING_OBSERVE` · paper only · base `BASE_E16` vs `FIN_CAP_50`

| Window | MDD dpp | Giveback pp | Score | Rel NAV |
|---|---:|---:|---:|---:|
| mtd | 0.8650617542240613 | 397.1032498910552 | None | 0.9722 |
| ytd | 1.2675664643313156 | 18.528555905153212 | None | 0.9271 |
| trailing_1y | 1.2675664643312823 | 7.715801476656159 | None | 0.9519 |
| heldout_2019_plus | -0.3471534419341227 | 1.9030232777466516 | None | 0.8857 |
| full | -0.34715344193410047 | 1.7414775644005953 | None | 0.8134 |

## Alerts

- ALERT: FIN_CAP_50 heldout_2019_plus MDD worse than BASE (paper)
- ALERT: FIN_CAP_50 ytd CAGR giveback > 3.0 pp (paper)
- PAUSE_REVIEW: ytd giveback > 5 pp — extend observe; Soft-Frozen unchanged; no cutover talk
- ALERT: FIN_CAP_50 trailing_1y CAGR giveback > 3.0 pp (paper)
- PAUSE_REVIEW: trailing_1y giveback > 5 pp — extend observe; Soft-Frozen unchanged; no cutover talk

## Non-actions

- paper monitor only
- no Soft-Frozen clip flip
- go-live stays NOT_READY_SEALED_CAGR until human re-verify

