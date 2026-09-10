# Indicator Buy/Sell — Round-2: Buy-Low vs Sell-High (split)

Date: 2026-09-10  
Status: **OPEN / PAPER ONLY**  
Human: **「研究買跟賣兩個分開…低的買點跟高的賣點」**  
Parent: `INDICATOR_BUY_SELL_CHARTER.md` · R1 verdict `COEXIST_NO_LIFT_VS_LIVE`  
Soft-Frozen **KEEP** · live **KD_OPT KEEP** · E45 stitch **OFF**

## Clarification (binding)

Round-1 mixed “indicator soft-tilt” on both sides. Round-2 **separates**:

| Track | Question | Mechanism |
|---|---|---|
| **A · BUY_LOW** | Does buying only at *low* points improve MDD/CAGR? | `buy_ok` = low signal; sells stay equal among holders |
| **B · SELL_HIGH** | Does selling only at *high* points improve MDD/CAGR? | `sell_ok` = high signal (empty pool → **skip sell / hold**); buys stay equal |

Do **not** combine A+B in Round-2. Combination is Round-3 only if either track shows lift vs live.

## Low / high definitions (causal)

| Side | Signal | Rule |
|---|---|---|
| Low buy | `RSI14_LT30` | RSI(14) &lt; 30 |
| Low buy | `BB_LOWER` | close &lt; Bollinger lower(20,2) |
| Low buy | `K9_LT30` | Yahoo K9 &lt; 30 |
| Low buy | `BELOW_MA60` | close &lt; MA60 |
| High sell | `RSI14_GT70` | RSI(14) &gt; 70 |
| High sell | `BB_UPPER` | close &gt; Bollinger upper(20,2) |
| High sell | `K9_GT70` | Yahoo K9 &gt; 70 |
| High sell | `ABOVE_MA20` | close &gt; MA20 |

Ex-day skip still applies on buys (AND with low gate). Soft-Frozen sleeve + `TEL_EQUAL` fixed.

## Anchors

- `FIN_EQUAL` · `LIVE_KD_OPT` (live lock)

## Gates

Same as R1: tip YTD+1y PASS + held-out score &gt; 0 vs EQUAL; “beat live” needs held-out &gt; `LIVE_KD_OPT` and tip-clean.

## Alloc plumbing (paper)

`allocate_sleeve_orders(..., sell_ok=, sell_scores=)` · `simulate_core(..., fin_sell_ok=, fin_sell_scores=)`. Live `e21` untouched.

## Artifacts

- Screen script: `scripts/e16_indicator_buy_sell_split_screen.py`
- Results: `research/ops/INDICATOR_BUY_SELL_SCREEN_R2_SPLIT.md` (+ `.json`)
- Repro: `repro/indicator-buy-sell-screen-r2-split/`

## Non-actions

No Soft-Frozen / KD_OPT / TEL live change · no E45 stitch · no auto cutover.

## Label

`INDICATOR_BUY_SELL_R2_SPLIT_2026-09-10__BUY_LOW_VS_SELL_HIGH__PAPER_ONLY`
