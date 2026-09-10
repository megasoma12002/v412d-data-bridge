# Indicator Buy/Sell Screen — Round 2 (Buy-Low vs Sell-High)

Generated: `2026-09-10T11:34:53.378042+00:00`
Asof: **2026-09-09** · Soft-Frozen **[0.6, 0.9]** KEEP
Charter: `INDICATOR_BUY_SELL_SCREEN_R2_SPLIT_CHARTER.md`
Verdict: **`COEXIST_NO_LIFT_VS_LIVE`**

## Design

- **BUY_LOW**: only buy when low signal (RSI&lt;30 / BB lower / K9&lt;30 / below MA60); sells equal.
- **SELL_HIGH**: only sell when high signal (RSI&gt;70 / BB upper / K9&gt;70 / above MA20); else **hold**.

## Summary

- Coexist: **1** → `['LIVE_KD_OPT']`
- Beat live KD_OPT: **0** → `[]`
- Best BUY_LOW rank: `BUY_LOW_BELOW_MA60`
- Best SELL_HIGH rank: `SELL_HIGH_RSI14_GT70`

## Scoreboard (held-out vs FIN_EQUAL)

| ID | Track | Tip YTD | Tip 1y | Held score | MDDΔpp | CAGRΔpp | vs live held Δ | Coexist |
|---|---|---|---|---:|---:|---:|---:|:---:|
| `LIVE_KD_OPT` | anchor | PASS | PASS | 0.541 | 0.666 | 0.252 | 0.000 | Y |
| `FIN_EQUAL` | anchor | PASS | PASS | 0.000 | 0.000 | 0.000 | -0.541 |  |
| `SELL_HIGH_RSI14_GT70` | SELL_HIGH | PASS | PASS | -0.958 | -0.869 | -0.178 | -1.499 |  |
| `BUY_LOW_BELOW_MA60` | BUY_LOW | ALERT | ALERT | -1.731 | -1.245 | 0.972 | -2.271 |  |
| `SELL_HIGH_K9_GT70` | SELL_HIGH | PASS | PASS | -1.851 | -1.700 | -0.301 | -2.391 |  |
| `SELL_HIGH_BB_UPPER` | SELL_HIGH | PASS | PASS | -2.137 | -1.940 | -0.394 | -2.678 |  |
| `SELL_HIGH_ABOVE_MA20` | SELL_HIGH | PASS | PASS | -2.491 | -2.375 | -0.232 | -3.032 |  |
| `BUY_LOW_BB_LOWER` | BUY_LOW | PAUSE_REVIEW | PAUSE_REVIEW | -1.468 | 1.154 | 5.245 | -2.009 |  |
| `BUY_LOW_K9_LT30` | BUY_LOW | PAUSE_REVIEW | PAUSE_REVIEW | -3.434 | -1.671 | 3.527 | -3.975 |  |
| `BUY_LOW_RSI14_LT30` | BUY_LOW | PAUSE_REVIEW | PAUSE_REVIEW | -3.733 | -1.461 | 4.544 | -4.274 |  |

## Reading

- Tracks are **separate**; do not stitch buy+sell winners without Round-3 OPEN.
- Empty beat-live → keep live KD_OPT.

## Non-actions

- No Soft-Frozen / KD_OPT / TEL live change · no E45 stitch · no auto cutover

## Label

`INDICATOR_BUY_SELL_SCREEN_R2_SPLIT_2026-09-10`
