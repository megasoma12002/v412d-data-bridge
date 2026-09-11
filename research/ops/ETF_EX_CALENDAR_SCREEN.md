# ETF Ex-Calendar Screen — Stage A (paper only)

Generated: `2026-09-11T05:19:16.562910+00:00` · asof **2026-09-10**
Charter: `ETF_EX_CALENDAR_STAGE_A_CHARTER.md`
Verdict: **`NEAR_NO_BEAT`** · decision **`STOP_ARCHIVE`** · books **13** · **no live wire**

## Question

Does rules-based 0050 ex-calendar timing tip-clean beat **BUY_HOLD_0050** and/or coexist with **LIVE_STACK** after costs?

## Summary

- Beat live: **0** → `[]`
- Coexist live: **0** → `[]`
- Beat BH: **0** → `[]`
- Tip-clean vs live: **5**
- Ex dates: **25** in market range / 32 ledger
- Note: CAL_OVER_BH is 100% 0050 every day under long-only Stage A rules (≡ BUY_HOLD_0050); informative lift must come from CAL_LONG_*.

## Scoreboard

| ID | Src | Tip live YTD/1y | Tip BH YTD/1y | Held vs live | Held vs BH | Held CAGR | Held MDD | Sealed CAGR | Sealed MDD | Active% | Label |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| `LIVE_STACK` | LIVE | PASS/PASS | PAUSE_REVIEW/PAUSE_REVIEW | 0.000 | 50.216 | 18.07% | -21.72% | 24.86% | -12.81% | 0.0% | `BASELINE` |
| `BUY_HOLD_0050` | BH | PASS/PASS | PASS/PASS | -59.254 | 0.000 | 9.03% | -76.46% | 2.81% | -76.46% | 100.0% | `BASELINE` |
| `MONTH_PROXY_W10_CAL_OVER_BH` | MONTH_PROXY | PASS/PASS | PASS/PASS | -59.254 | 0.000 | 9.03% | -76.46% | 2.81% | -76.46% | 100.0% | `NO_LIFT` |
| `MONTH_PROXY_W15_CAL_OVER_BH` | MONTH_PROXY | PASS/PASS | PASS/PASS | -59.254 | 0.000 | 9.03% | -76.46% | 2.81% | -76.46% | 100.0% | `NO_LIFT` |
| `EXACT_EX_N10_CAL_OVER_BH` | EXACT_EX | PASS/PASS | PASS/PASS | -59.254 | 0.000 | 9.03% | -76.46% | 2.81% | -76.46% | 100.0% | `NO_LIFT` |
| `EXACT_EX_N20_CAL_OVER_BH` | EXACT_EX | PASS/PASS | PASS/PASS | -59.254 | 0.000 | 9.03% | -76.46% | 2.81% | -76.46% | 100.0% | `NO_LIFT` |
| `EXACT_EX_N40_CAL_OVER_BH` | EXACT_EX | PASS/PASS | PASS/PASS | -59.254 | 0.000 | 9.03% | -76.46% | 2.81% | -76.46% | 100.0% | `NO_LIFT` |
| `MONTH_PROXY_W10_CAL_LONG_0050` | MONTH_PROXY | PAUSE_REVIEW/PAUSE_REVIEW | PAUSE_REVIEW/PAUSE_REVIEW | 6.028 | 65.282 | 3.61% | -8.46% | 3.10% | -8.46% | 7.2% | `NO_LIFT` |
| `EXACT_EX_N10_CAL_LONG_0050` | EXACT_EX | PAUSE_REVIEW/PAUSE_REVIEW | PAUSE_REVIEW/PAUSE_REVIEW | 3.552 | 62.806 | 2.62% | -10.44% | 3.30% | -9.94% | 6.9% | `NO_LIFT` |
| `EXACT_EX_N20_CAL_LONG_0050` | EXACT_EX | PAUSE_REVIEW/PAUSE_REVIEW | PAUSE_REVIEW/PAUSE_REVIEW | 2.706 | 61.960 | 7.31% | -13.64% | 8.34% | -9.17% | 13.9% | `NO_LIFT` |
| `EXACT_EX_N20_HOLD_THRU_T5_CAL_LONG_0050` | EXACT_EX | PAUSE_REVIEW/PAUSE_REVIEW | PAUSE_REVIEW/PAUSE_REVIEW | 1.896 | 61.150 | 8.04% | -14.81% | 7.22% | -14.81% | 18.2% | `NO_LIFT` |
| `MONTH_PROXY_W15_CAL_LONG_0050` | MONTH_PROXY | PAUSE_REVIEW/PAUSE_REVIEW | PAUSE_REVIEW/PAUSE_REVIEW | 1.307 | 60.561 | 4.06% | -13.41% | 2.79% | -13.41% | 10.8% | `NO_LIFT` |
| `EXACT_EX_N40_CAL_LONG_0050` | EXACT_EX | PAUSE_REVIEW/PAUSE_REVIEW | PAUSE_REVIEW/PAUSE_REVIEW | -63.632 | -4.378 | -3.74% | -74.45% | -18.23% | -74.45% | 27.7% | `NO_LIFT` |

## Baselines

- `LIVE_STACK` heldout CAGR/MDD: 18.07% / -21.72%
- `BUY_HOLD_0050` heldout CAGR/MDD: 9.03% / -76.46%

## Reading

- Held score = MDD↑pp − 0.5·|CAGRΔpp| vs each baseline.
- Sealed is report-only in Stage A.
- `CAL_OVER_BH` under Stage A long-only rules matches `BUY_HOLD_0050` (charter grid retained).
- Announce dates were **not** invented; EXACT_EX uses realized `cash_ex_date` only.

## Non-actions

- No Soft-Frozen / live KD / TEL / E45 / Soft-assist / sleeve-tilt wire from this screen

## Next

- **STOP / archive**; live + observes unchanged.

## Label

`ETF_EX_CALENDAR_SCREEN_STAGE_A_2026-09-11__NEAR_NO_BEAT`
