# KD_OPT + Indicator Assist Screen

Generated: `2026-09-10T12:22:17.056577+00:00` · asof **2026-09-09**
Charter: `KD_OPT_INDICATOR_ASSIST_CHARTER.md`
Verdict: **`ASSIST_NO_LIFT`**

## Question

Does adding low-buy / high-sell indicator **assists on top of LIVE_KD_OPT** beat plain live KD_OPT?

## Summary

- Books: **272** (base + buy assists + sell assists + both cross)
- Coexist: **1**
- Beat live: **0** → `[]`
- Near (tip-clean, vs live Δ &gt; −0.05): `[]`

## Top 20

| ID | Mode | Tip YTD | Tip 1y | Held | MDDΔpp | CAGRΔpp | vs live Δ | Coexist |
|---|---|---|---|---:|---:|---:|---:|:---:|
| `LIVE_KD_OPT` | base | PASS | PASS | 0.541 | 0.666 | 0.252 | 0.000 | Y |
| `KD+SELL_WILLR14_GT_N20` | KD+SELL_HIGH | PASS | PASS | -1.135 | -0.916 | 0.437 | -1.675 |  |
| `KD+SELL_RSI14_GT70` | KD+SELL_HIGH | ALERT | ALERT | -1.252 | -1.116 | 0.273 | -1.793 |  |
| `KD+SELL_RSI6_GT80` | KD+SELL_HIGH | PASS | PASS | -1.395 | -1.124 | -0.541 | -1.935 |  |
| `KD+SELL_D9_GT80` | KD+SELL_HIGH | PASS | PASS | -1.483 | -1.371 | -0.224 | -2.023 |  |
| `KD+SELL_K9_GT80` | KD+SELL_HIGH | PASS | PASS | -1.484 | -1.184 | 0.600 | -2.025 |  |
| `KD+SELL_MFI14_GT80` | KD+SELL_HIGH | PASS | PASS | -1.537 | -1.337 | -0.400 | -2.078 |  |
| `KD+BUY_AND_BELOW_MA60` | KD+BUY_AND_LOW | ALERT | ALERT | -1.731 | -1.157 | 1.149 | -2.272 |  |
| `KD+BOTH__MACD_HIST_NEG__MACD_HIST_POS` | KD+BOTH | PASS | PASS | -1.844 | -1.405 | 0.878 | -2.385 |  |
| `KD+SELL_MACD_HIST_POS` | KD+SELL_HIGH | PASS | PASS | -2.052 | -1.799 | -0.507 | -2.593 |  |
| `KD+SELL_CCI20_GT100` | KD+SELL_HIGH | PASS | PASS | -2.071 | -2.064 | 0.014 | -2.612 |  |
| `KD+BOTH__MACD_HIST_NEG__RSI6_GT80` | KD+BOTH | ALERT | ALERT | -2.166 | -1.818 | 0.697 | -2.707 |  |
| `KD+SELL_K9_GT70` | KD+SELL_HIGH | PASS | PASS | -2.197 | -2.140 | -0.113 | -2.737 |  |
| `KD+SELL_BB_UPPER` | KD+SELL_HIGH | PASS | PASS | -2.342 | -2.158 | -0.369 | -2.883 |  |
| `KD+SELL_BB_PCTB_GT1` | KD+SELL_HIGH | PASS | PASS | -2.342 | -2.158 | -0.369 | -2.883 |  |
| `KD+BOTH__MACD_HIST_NEG__MFI14_GT80` | KD+BOTH | ALERT | ALERT | -2.426 | -2.117 | 0.618 | -2.967 |  |
| `KD+SELL_ABOVE_MA20` | KD+SELL_HIGH | PASS | PASS | -2.576 | -2.471 | -0.211 | -3.117 |  |
| `KD+BOTH__BELOW_MA60__MFI14_GT80` | KD+BOTH | PASS | PASS | -2.816 | -2.663 | -0.307 | -3.357 |  |
| `KD+SELL_ABOVE_MA60` | KD+SELL_HIGH | PASS | PASS | -2.857 | -2.636 | -0.441 | -3.397 |  |
| `KD+BOTH__BELOW_MA60__RSI6_GT80` | KD+BOTH | ALERT | PASS | -3.097 | -3.017 | 0.160 | -3.637 |  |

## Reading

- If beat-live empty → **no evidenced assist lift** in this catalog; keep live KD_OPT.
- Soft assist / different thresholds would need a new OPEN.

## Non-actions

- No Soft-Frozen / live KD change / E45 stitch from this screen alone

## Label

`KD_OPT_INDICATOR_ASSIST_SCREEN_2026-09-10`
