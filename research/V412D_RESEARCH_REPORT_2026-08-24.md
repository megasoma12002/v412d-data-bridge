# V4.12-D Financial Regime Router — Data Gate and Baseline Research

Date: 2026-08-24 (Asia/Taipei)  
Canonical prices: raw/unadjusted daily OHLCV

## 1. Data gate result

- GitHub data bridge is operational in `megasoma12002/v412d-data-bridge`.
- The 2880 single-stock gate passed after artifact download, extraction, local disk re-read, and QC.
- All 12 target stocks passed the same local re-read QC pipeline.
- Combined rows: 48,411.
- 2880 contains 4,074 rows from 2010-01-04 through 2026-08-21.
- 5880 begins on its actual available date, 2011-12-01.
- 2884 contains 4,073 valid rows; the official source row for 2025-11-05 had no OHLC and zero volume, so it was excluded and documented.
- Required columns, duplicates, nulls, OHLC inequalities, and non-negative volume checks passed.
- All 12 stocks matched official TWSE data on the 2026-08-21 spot check. The 2880 file additionally matched 2010-01-04 and 2018-04-10 exactly.

The current Work runtime does not expose `/mnt/data` and its root filesystem is read-only. Therefore the genuine downloaded files were materialized and re-read at the workspace-local path `mnt/data/12stocks/`; this is a mount-path difference, not a simulated data result.

## 2. Leakage and execution repair

The handed-off trainer claimed T+1 execution but originally changed positions at the T close. It also omitted the sell-side securities transaction tax. The repaired simulator now:

1. forms signals only with information available through the T close;
2. carries old holdings from the previous close to the next open;
3. executes the pending target at the T+1 open;
4. applies buy commission of 0.0855% and sell commission plus tax of 0.3855%;
5. applies the same T+1 rule to stop orders;
6. marks the new holdings from the execution-day open to close.

## 3. Frozen research split

| Period | Dates | Use |
|---|---|---|
| Train | 2010-01-01–2018-12-31 | parameter ranking |
| Validation | 2019-01-01–2022-12-31 | rejection only |
| Blind | 2023-01-01–2025-12-31 | untouched evaluation |
| Final OOS | 2026-01-01–2026-08-21 | untouched final evaluation |

## 4. R1–R4 baseline

Selected by Train ranking among Validation survivors, with fallback explicitly identified when no candidate survived:

| Router | Frozen config | Train return | Validation | Blind | Final OOS | Status |
|---|---:|---:|---:|---:|---:|---|
| R1 | R1C / top 1 / 21d | -2.65% | +39.68% | +20.94% | +8.94% | passed rejection gate narrowly |
| R2 | R2B / top 1 / 15d | -1.54% | -11.00% | +9.42% | +15.85% | **fallback; all candidates failed Validation** |
| R3 | R3B / top 2 / 21d | -9.40% | +28.23% | +41.47% | +46.33% | Validation max drawdown -29.90% fails the stated -25% gate; fallback |
| R4 | R4A / top 1 / 15d | -16.63% | +10.40% | +52.56% | +20.16% | Validation max drawdown -47.21% fails; fallback |

Although later-period returns are positive, every sleeve lost money in Train and three sleeves required fallback because the rejection gate had no survivor. This baseline is not production-ready evidence of edge.

## 5. Daily stock-level Dynamic Router baseline

The meta-router uses only trailing sleeve returns through T, ranks trailing risk-adjusted performance, and applies the selected weights to T+1 returns. Its parameter grid was searched on Train only; Validation could only reject.

- Train winner: 60-day lookback, 42-trading-day rebalance, top 2 sleeves.
- No top-five Train configuration satisfied both Validation return > -5% and max drawdown > -25%; the winner is therefore marked `validation_pass: false`.

| Strategy | Train | Validation | Blind | Final OOS |
|---|---:|---:|---:|---:|
| Dynamic Router | +36.51% | +58.56% | +46.94% | +19.13% |
| Equal-weight four sleeves | -2.17% | +18.05% | +32.13% | +23.23% |

Final OOS favors the simpler equal-weight control on both return (+23.23% vs +19.13%) and drawdown (-8.92% vs -13.04%). The dynamic router therefore does not establish incremental 2026 edge.

## 6. Transaction-cost sensitivity

Dynamic Router returns remain positive when its own switching costs are multiplied, but decay monotonically:

| Cost multiplier | Train | Validation | Blind | Final OOS |
|---:|---:|---:|---:|---:|
| 0× | +48.75% | +65.05% | +50.43% | +19.97% |
| 1× | +36.51% | +58.56% | +46.94% | +19.13% |
| 2× | +25.24% | +52.32% | +43.53% | +18.29% |
| 3× | +14.88% | +46.31% | +40.19% | +17.45% |

These are meta-switching costs in addition to costs already embedded in each sleeve.

## 7. Research verdict and unresolved risks

**Verdict: data gate passed; model gate not passed.** The result is a valid, reproducible baseline, not a deployable trading strategy.

Primary risks:

- Fixed present-day 12-stock universe creates survivorship/universe-selection risk for historical conclusions.
- Raw prices are appropriate for execution, but returns around dividends/corporate actions are not total returns. A separate adjusted/total-return series is needed for economic performance comparison.
- The same broad feature ideas and limited family definitions may encode regime assumptions that happen to fit later years.
- Four sleeves were selected independently, then reused by the meta-router; uncertainty compounds across both levels.
- Final OOS currently covers only 152 trading observations and must not be used for further tuning.

Recommended next iteration: freeze Blind and 2026 permanently, reconstruct point-in-time membership/corporate-action data, add a cash/risk-off state, benchmark against raw and total-return buy-and-hold portfolios, and require a genuine Validation survivor before another Blind evaluation.
