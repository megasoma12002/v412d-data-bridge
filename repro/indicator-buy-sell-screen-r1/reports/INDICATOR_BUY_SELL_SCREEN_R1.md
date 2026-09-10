# Indicator Buy/Sell Screen — Round 1

Generated: `2026-09-10T11:09:52.119869+00:00`
Asof NAV: **2026-09-09** · Soft-Frozen **[0.6, 0.9]** KEEP
Charter: `INDICATOR_BUY_SELL_CHARTER.md`
Verdict: **`COEXIST_NO_LIFT_VS_LIVE`**

## Summary

- Books screened: **11**
- Coexist (tip PASS + held-out&gt;0 vs EQUAL): **4** → `['LIVE_KD_OPT', 'BB_LOWER_SEASON', 'RSI14_OS_ALWAYS', 'VOL_UP_ALWAYS']`
- Beat live KD_OPT on held-out (and tip-clean): **0** → `[]`

## Scoreboard (held-out vs FIN_EQUAL)

| ID | Family | Tip YTD | Tip 1y | Held score | MDDΔpp | CAGRΔpp | vs live held Δ | Coexist |
|---|---|---|---|---:|---:|---:|---:|:---:|
| `LIVE_KD_OPT` | anchor | PASS | PASS | 0.541 | 0.666 | 0.252 | 0.000 | Y |
| `BB_LOWER_SEASON` | season | PASS | PASS | 0.517 | 0.746 | 0.458 | -0.023 | Y |
| `RSI14_OS_ALWAYS` | always | PASS | PASS | 0.363 | 0.559 | 0.393 | -0.178 | Y |
| `VOL_UP_ALWAYS` | always | PASS | PASS | 0.128 | 0.259 | 0.262 | -0.412 | Y |
| `MACD_HIST_SEASON` | season | PASS | ALERT | 0.640 | 0.930 | 0.579 | 0.100 |  |
| `RSI14_OS_SEASON` | season | PASS | ALERT | 0.505 | 0.771 | 0.534 | -0.036 |  |
| `MA_GOLD_SEASON` | season | PASS | ALERT | 0.433 | 0.717 | 0.567 | -0.107 |  |
| `MA_GOLD_ALWAYS` | always | ALERT | ALERT | 0.422 | 0.758 | 0.672 | -0.119 |  |
| `MACD_HIST_ALWAYS` | always | PASS | ALERT | 0.378 | 0.657 | 0.558 | -0.162 |  |
| `FIN_EQUAL` | anchor | PASS | PASS | 0.000 | 0.000 | 0.000 | -0.541 |  |
| `FIN_RS_SOFT_TILT_EXDIV` | anchor | ALERT | PAUSE_REVIEW | 0.403 | 0.893 | 0.979 | -0.138 |  |

## Reading

- Coexist ≠ live promote.
- Beat-live list empty → keep live KD_OPT; Round-2 only if human OPEN (e.g. TEL indicators / sleeve-router).
- Soft-Frozen / live wire unchanged.

## Non-actions

- No Soft-Frozen flip / no live KD_OPT retune / no E45 stitch / no auto cutover

## Label

`INDICATOR_BUY_SELL_SCREEN_R1_2026-09-10`
