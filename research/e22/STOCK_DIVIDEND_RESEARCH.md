# E22 Stock Dividend Research

Generated: `2026-09-04T16:51:16.705155+00:00`

**EXPERIMENTAL / challenger only.** Does not rewrite SOFT_FROZEN E22_v2.

## Question

If portfolio NAV is marked on raw `close` and only cash dividends are credited,
do we need to recompute research backtests after applying stock-dividend share increases?

## Method

- Engine: `scripts/e50_early_stack_combined_nav.py` (E16 targets + Exact T+1 fills)
- Cash credit on `cash_ex_date` (E22_v2 convention)
- Stock-aware: on `stock_ex_date`, `shares *= 1 + stock_dividend/10` (FinMind 元/股, par 10)
- Compare: `E16_E18_NO_DIV` / `E22_CASH_ONLY` / `E22_CASH_PLUS_STOCK`

## Ledger inventory

- Stock events in universe: **52** (`2880, 2886, 2892, 5880`)

| Code | Events | Mean 元/股 |
|---|---:|---:|
| 2880 | 16 | 0.4156 |
| 2886 | 5 | 0.1960 |
| 2892 | 16 | 0.3594 |
| 5880 | 15 | 0.3933 |

## Results

| Variant | CAGR | MDD | End NAV | Stock events |
|---|---:|---:|---:|---:|
| E16_E18_NO_DIV | 7.29% | -22.77% | nan | 0 |
| E22_CASH_ONLY | 11.25% | -22.11% | 12,375,276 | 0 |
| E22_CASH_PLUS_STOCK | 13.78% | -22.64% | 16,695,202 | 42 |

### Deltas

- Stock-aware − cash-only CAGR: **2.53 pp**
- Stock-aware − cash-only MDD: `-0.53 pp`
- Stock-aware − cash-only end NAV: `4,319,926`
- Cash-only − no-div CAGR: `3.96 pp`
- Applied stock events / shares added: `42` / `78,250.2`

### Ex-date NAV continuity

- Stock ex-dates overlapping NAV window: `42`
- Mean (stock-aware − cash-only) NAV return on ex-day: `0.007857863689548203`
- Median gap: `0.004424232051308097`
- Share of ex-days where stock-aware NAV ret is higher: `0.9285714285714286`
- Mean underlying price return on those ex-days: `-0.06218807106475192`

By code (mean NAV-ret gap on stock ex-day):

| Code | n | Mean gap | Median gap |
|---|---:|---:|---:|
| 2880 | 13 | 1.71 pp | 1.85 pp |
| 2886 | 3 | 0.91 pp | 0.57 pp |
| 2892 | 12 | 0.29 pp | 0.04 pp |
| 5880 | 14 | 0.33 pp | 0.05 pp |

Interpretation: raw-close prices typically gap down on stock ex-date. Cash-only keeps share count
flat → NAV drop. Stock-aware adds shares → NAV closer to continuous total return.

### End share delta (stock-aware − cash-only)

| Code | Δ shares |
|---|---:|
| 2880 | 81,316.7229 |
| 2886 | -1,772.2918 |
| 2892 | -24.5566 |
| 5880 | 1.3211 |
| 2412 | 3,347.0000 |
| 3045 | 0.0000 |
| 4904 | 0.0000 |
| 0050 | 3,009.0000 |

## Decision

- Official E22_v2: `KEEP_CASH_ONLY_SOFT_FROZEN`
- Research finding: `MATERIAL_POSITIVE_TOTAL_RETURN_CORRECTION`
- Promote now: `False`
- Reason: Stock share increase on stock_ex_date lifts challenger CAGR by ~2.5pp vs cash-only when marking with raw close. This corrects understated NAV on stock ex-dates; it is not a new alpha signal. Promote only via explicit new E22 version + approval.

### Next

- Keep E22_v2 published numbers labeled cash-only
- Use E22_CASH_PLUS_STOCK as research total-return challenger
- If promoting: new version id (e.g. E22_v2_stock or E22_v3_stock) with Exact T+1 unchanged

## Artifacts

- `repro/e22-stock-div-research/summary.json`
- `repro/e22-stock-div-research/outputs/`
- `research/e22/STOCK_DIVIDEND_RESEARCH_SUMMARY.json`

