# E45 Observe Month-End PAUSE Time-Series

Generated: `2026-09-06T04:17:39.744934+00:00`
Status: **PAPER / OPS OBSERVE** — Soft-Frozen KEEP · DEFAULT KEEP · stitch FORBIDDEN

Gates: YTD / trailing_1y CAGR giveback vs BASE — ALERT >3pp · PAUSE_REVIEW >5pp.

## Tip gates (four OPERATING sleeves)

| Sleeve | Tip asof | YTD | Trailing 1y | Share PAUSE (YTD) | Share PAUSE (1y) | First clean both |
|---|---|---|---|---:|---:|---|
| `FULL_E45` | 2026-09-04 | **PAUSE_REVIEW** | **PAUSE_REVIEW** | 62% | 62% | 2023-02-24 |
| `BLEND_A25` | 2026-09-04 | **PAUSE_REVIEW** | **PAUSE_REVIEW** | 53% | 56% | 2023-02-24 |
| `BLEND_A05` | 2026-09-04 | **ALERT** | **PAUSE_REVIEW** | 7% | 9% | 2023-02-24 |
| `SLEEVE_FIN_ONLY_A10` | 2026-09-04 | **PAUSE_REVIEW** | **PAUSE_REVIEW** | 13% | 16% | 2023-02-24 |

## Read

- Tip PAUSE_REVIEW across sleeves is **expected** while observe accumulates; it does **not** revoke held-out paper scores.
- `first_clean_both_asof = none yet` ⇒ no stitch talk from trailing gates.
- Cadence: refresh ledgers → month-end monitors → this time-series.

CSV: `repro/e45-five-research-batch/outputs/observe_month_end_pause_timeseries.csv`

Label: `E45_OBSERVE_PAUSE_TS_2026-09-06__STITCH_FORBIDDEN`
