# Indicator Combo Catalog Screen — Round 3

Generated: `2026-09-10T11:47:53.332172+00:00`
Asof: **2026-09-09** · Soft-Frozen **[0.6, 0.9]** KEEP
Charter: `INDICATOR_COMBO_CATALOG_CHARTER.md`
Verdict: **`COEXIST_NO_LIFT_VS_LIVE`**

## Scope

- Low gates: **16** · High gates: **15** · Cross: **240**
- Total books: **278** (singles + aggregates + full buy×sell cross + anchors)
- Finite market-standard TA catalog (not unbounded universe).

## Summary

- Coexist: **1**
- Beat live KD_OPT: **0** → `[]`
- Top overall: `['LIVE_KD_OPT', 'SELL_HIGH_WILLR14_GT_N20', 'X__CCI20_LT_N100__MFI14_GT80', 'SELL_HIGH_RSI14_GT70', 'X__CCI20_LT_N100__D9_GT80', 'X__MACD_HIST_NEG__MACD_HIST_POS', 'SELL_HIGH_K9_GT80', 'SELL_MAJ3', 'SELL_HIGH_D9_GT80', 'X__MACD_HIST_NEG__RSI6_GT80']`

## Top 20 scoreboard

| ID | Layer | Tip YTD | Tip 1y | Held | MDDΔpp | CAGRΔpp | vs live Δ | Coexist |
|---|---|---|---|---:|---:|---:|---:|:---:|
| `LIVE_KD_OPT` | anchor | PASS | PASS | 0.541 | 0.666 | 0.252 | 0.000 | Y |
| `SELL_HIGH_WILLR14_GT_N20` | SELL_HIGH | PASS | PASS | -0.655 | -0.498 | 0.314 | -1.196 |  |
| `X__CCI20_LT_N100__MFI14_GT80` | CROSS | ALERT | ALERT | -0.677 | -0.418 | 0.518 | -1.217 |  |
| `SELL_HIGH_RSI14_GT70` | SELL_HIGH | PASS | PASS | -0.958 | -0.869 | -0.178 | -1.499 |  |
| `X__CCI20_LT_N100__D9_GT80` | CROSS | ALERT | ALERT | -0.977 | -0.723 | 0.507 | -1.517 |  |
| `X__MACD_HIST_NEG__MACD_HIST_POS` | CROSS | ALERT | PASS | -1.088 | -0.754 | 0.669 | -1.629 |  |
| `SELL_HIGH_K9_GT80` | SELL_HIGH | PASS | ALERT | -1.166 | -0.830 | 0.672 | -1.706 |  |
| `SELL_MAJ3` | AGG | PASS | PASS | -1.259 | -1.202 | -0.114 | -1.800 |  |
| `SELL_HIGH_D9_GT80` | SELL_HIGH | PASS | PASS | -1.268 | -0.958 | -0.620 | -1.809 |  |
| `X__MACD_HIST_NEG__RSI6_GT80` | CROSS | PASS | PASS | -1.300 | -1.219 | 0.162 | -1.841 |  |
| `SELL_HIGH_MFI14_GT80` | SELL_HIGH | PASS | PASS | -1.411 | -1.088 | -0.645 | -1.951 |  |
| `SELL_HIGH_RSI6_GT80` | SELL_HIGH | PASS | PASS | -1.461 | -1.091 | -0.741 | -2.002 |  |
| `X__MACD_HIST_NEG__D9_GT80` | CROSS | PASS | PASS | -1.513 | -1.221 | 0.583 | -2.053 |  |
| `SELL_HIGH_CCI20_GT100` | SELL_HIGH | PASS | PASS | -1.673 | -1.667 | 0.012 | -2.214 |  |
| `X__MACD_HIST_NEG__MFI14_GT80` | CROSS | PASS | PASS | -1.683 | -1.494 | 0.379 | -2.224 |  |
| `BUY_LOW_BELOW_MA60` | BUY_LOW | ALERT | ALERT | -1.731 | -1.245 | 0.972 | -2.271 |  |
| `X__MACD_HIST_NEG__ABOVE_MA20` | CROSS | ALERT | PASS | -1.797 | -1.273 | 1.048 | -2.338 |  |
| `SELL_HIGH_K9_GT70` | SELL_HIGH | PASS | PASS | -1.851 | -1.700 | -0.301 | -2.391 |  |
| `SELL_OR_ALL` | AGG | PASS | PASS | -2.061 | -2.013 | 0.098 | -2.602 |  |
| `X__MACD_HIST_NEG__CCI20_GT100` | CROSS | ALERT | ALERT | -2.137 | -1.765 | 0.744 | -2.677 |  |

### Top BUY_LOW singles

| ID | Tip YTD | Tip 1y | Held | vs live Δ | Coexist |
|---|---|---|---:|---:|:---:|
| `BUY_LOW_BELOW_MA60` | ALERT | ALERT | -1.731 | -2.271 |  |
| `BUY_LOW_MACD_HIST_NEG` | PAUSE_REVIEW | PAUSE_REVIEW | -0.089 | -0.629 |  |
| `BUY_LOW_K9_LT20` | PAUSE_REVIEW | PAUSE_REVIEW | -0.226 | -0.767 |  |
| `BUY_LOW_CCI20_LT_N100` | PAUSE_REVIEW | PAUSE_REVIEW | -0.672 | -1.212 |  |
| `BUY_LOW_BB_LOWER` | PAUSE_REVIEW | PAUSE_REVIEW | -1.468 | -2.009 |  |
| `BUY_LOW_BB_PCTB_LT0` | PAUSE_REVIEW | PAUSE_REVIEW | -1.468 | -2.009 |  |
| `BUY_LOW_BELOW_MA120` | PAUSE_REVIEW | PAUSE_REVIEW | -1.689 | -2.229 |  |
| `BUY_LOW_BELOW_MA20` | PAUSE_REVIEW | PAUSE_REVIEW | -1.920 | -2.461 |  |

### Top SELL_HIGH singles

| ID | Tip YTD | Tip 1y | Held | vs live Δ | Coexist |
|---|---|---|---:|---:|:---:|
| `SELL_HIGH_WILLR14_GT_N20` | PASS | PASS | -0.655 | -1.196 |  |
| `SELL_HIGH_RSI14_GT70` | PASS | PASS | -0.958 | -1.499 |  |
| `SELL_HIGH_K9_GT80` | PASS | ALERT | -1.166 | -1.706 |  |
| `SELL_HIGH_D9_GT80` | PASS | PASS | -1.268 | -1.809 |  |
| `SELL_HIGH_MFI14_GT80` | PASS | PASS | -1.411 | -1.951 |  |
| `SELL_HIGH_RSI6_GT80` | PASS | PASS | -1.461 | -2.002 |  |
| `SELL_HIGH_CCI20_GT100` | PASS | PASS | -1.673 | -2.214 |  |
| `SELL_HIGH_K9_GT70` | PASS | PASS | -1.851 | -2.391 |  |

### Top CROSS (buy×sell)

| ID | Tip YTD | Tip 1y | Held | vs live Δ | Coexist |
|---|---|---|---:|---:|:---:|
| `X__CCI20_LT_N100__MFI14_GT80` | ALERT | ALERT | -0.677 | -1.217 |  |
| `X__CCI20_LT_N100__D9_GT80` | ALERT | ALERT | -0.977 | -1.517 |  |
| `X__MACD_HIST_NEG__MACD_HIST_POS` | ALERT | PASS | -1.088 | -1.629 |  |
| `X__MACD_HIST_NEG__RSI6_GT80` | PASS | PASS | -1.300 | -1.841 |  |
| `X__MACD_HIST_NEG__D9_GT80` | PASS | PASS | -1.513 | -2.053 |  |
| `X__MACD_HIST_NEG__MFI14_GT80` | PASS | PASS | -1.683 | -2.224 |  |
| `X__MACD_HIST_NEG__ABOVE_MA20` | ALERT | PASS | -1.797 | -2.338 |  |
| `X__MACD_HIST_NEG__CCI20_GT100` | ALERT | ALERT | -2.137 | -2.677 |  |
| `X__CCI20_LT_N100__BIAS20_GT5` | ALERT | PASS | -2.291 | -2.831 |  |
| `X__MACD_HIST_NEG__BB_UPPER` | ALERT | ALERT | -2.489 | -3.030 |  |
| `X__MACD_HIST_NEG__BB_PCTB_GT1` | ALERT | ALERT | -2.489 | -3.030 |  |
| `X__BELOW_MA60__MFI14_GT80` | PASS | PASS | -2.896 | -3.437 |  |
| `X__BELOW_MA20__MACD_HIST_POS` | ALERT | PASS | -2.914 | -3.455 |  |
| `X__BELOW_MA60__K9_GT70` | ALERT | ALERT | -3.043 | -3.584 |  |
| `X__BELOW_MA60__RSI6_GT80` | ALERT | PASS | -3.088 | -3.629 |  |

## Reading

- Beat-live empty → keep live KD_OPT.
- Full CSV: `repro/indicator-combo-catalog-r3/reports/combo_scoreboard.csv`

## Non-actions

- No Soft-Frozen / KD_OPT / TEL live change · no E45 stitch · no auto cutover

## Label

`INDICATOR_COMBO_CATALOG_SCREEN_R3_2026-09-10`
