# E22_v2s Historical Research Recompute

Generated: `2026-09-04T17:19:11.214023+00:00`

**Research only.** Does **not** rewrite `forward/e21/` live ledgers.

## Purpose

Recompute full-history early-stack NAV under formal books (E22_v2s) and keep
E22_v2 cash-only as a labeled baseline side-by-side.

## Method

- Engine: `scripts/e50_early_stack_combined_nav.py` + `e22_dividend_accounting.py`
- Signals: E16 on `adj_close`
- Books: raw `close`; Exact T+1 fills
- E22_v2: cash on `cash_ex_date` only
- E22_v2s: cash + stock share increase on `stock_ex_date`

## Results

| Variant | CAGR | MDD | Start NAV | End NAV | Stock events |
|---|---:|---:|---:|---:|---:|
| E16_E18_NO_DIV | 7.29% | -22.77% | 3,000,000 | 7,647,343 | 0 |
| E22_v2 | 11.25% | -22.11% | 3,000,000 | 12,375,276 | 0 |
| E22_v2s | 13.78% | -22.64% | 3,000,000 | 16,695,202 | 42 |

### Deltas (v2s − v2)

- CAGR: **2.53 pp**
- MDD: `-0.53 pp`
- End NAV: `4,319,926`
- Stock events / shares added: `42` / `78,250.2`

## Calendar-year returns

| Year | E22_v2 | E22_v2s | Δ |
|---:|---:|---:|---:|
| 2012 | 0.36% | 0.36% | 0.00 pp |
| 2013 | 6.76% | 10.64% | 3.89 pp |
| 2014 | 4.87% | 7.84% | 2.97 pp |
| 2015 | -5.37% | -3.21% | 2.16 pp |
| 2016 | 14.36% | 17.65% | 3.29 pp |
| 2017 | 9.15% | 11.76% | 2.61 pp |
| 2018 | 6.90% | 9.18% | 2.28 pp |
| 2019 | 23.72% | 28.45% | 4.73 pp |
| 2020 | -5.92% | -3.69% | 2.23 pp |
| 2021 | 19.15% | 20.86% | 1.71 pp |
| 2022 | 2.10% | 5.53% | 3.43 pp |
| 2023 | 8.83% | 7.02% | -1.81 pp |
| 2024 | 18.68% | 21.24% | 2.56 pp |
| 2025 | 16.27% | 17.87% | 1.59 pp |
| 2026 | 37.81% | 39.44% | 1.63 pp |

## Decision

- Live historical NAV: `DO_NOT_REWRITE`
- Research total return: `USE_E22_V2S_SIDE_BY_SIDE`
- Published v2 label: `KEEP_AS_CASH_ONLY_BASELINE`
- Formal books figure: `E22_v2s`

## Artifacts

- `repro/e22-v2s-historical-recompute/summary.json`
- `repro/e22-v2s-historical-recompute/outputs/`
- `research/e22/E22_V2S_HISTORICAL_RECOMPUTE.json`

