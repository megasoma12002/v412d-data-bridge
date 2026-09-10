# Indicator Buy/Sell — Round-3: Market TA Catalog + Combinations

Date: 2026-09-10  
Status: **OPEN / PAPER ONLY**  
Human: **「請把現有市場上所有的技術指標都拿來組合分析」**  
Parent: `INDICATOR_BUY_SELL_CHARTER.md` · R2 split DONE  
Soft-Frozen **KEEP** · live **KD_OPT KEEP** · E45 stitch **OFF**

## Scope honesty

「市場上所有技術指標」在字面上是無限集。本輪定義 **有限、可重現的市場常用 TA 目錄**（震盪／趨勢／通道／量能／乖離），在 **BUY_LOW × SELL_HIGH** 架構下做：

1. **Singles** — 每個低點／高點訊號單獨測  
2. **Cross** — 全部 `BUY_LOW_i × SELL_HIGH_j` 兩兩組合  
3. **Aggregate gates** — OR／majority／精選 AND（同側多訊號）

不是任意子集幂集（2^n 不可行）。

## Catalog (causal daily OHLCV)

### Low (buy gate = True)

| ID | Rule |
|---|---|
| RSI14_LT30 / RSI6_LT20 | RSI oversold |
| K9_LT20 / K9_LT30 / D9_LT20 | Yahoo Stoch |
| WILLR14_LT_N80 | Williams %R &lt; −80 |
| CCI20_LT_N100 | CCI(20) &lt; −100 |
| BB_LOWER / BB_PCTB_LT0 | Bollinger |
| BELOW_MA20 / MA60 / MA120 | Price below MA |
| MACD_HIST_NEG | MACD histogram &lt; 0 |
| BIAS20_LT_N5 | 乖離率 &lt; −5% |
| MFI14_LT20 | Money Flow Index |
| ROC10_LT_N5 | Rate of change |

### High (sell gate = True)

| ID | Rule |
|---|---|
| RSI14_GT70 / RSI6_GT80 | RSI overbought |
| K9_GT70 / K9_GT80 / D9_GT80 | Yahoo Stoch |
| WILLR14_GT_N20 | Williams %R &gt; −20 |
| CCI20_GT100 | CCI(20) &gt; 100 |
| BB_UPPER / BB_PCTB_GT1 | Bollinger |
| ABOVE_MA20 / MA60 | Price above MA |
| MACD_HIST_POS | MACD histogram &gt; 0 |
| BIAS20_GT5 | 乖離率 &gt; 5% |
| MFI14_GT80 | MFI |
| ROC10_GT5 | ROC |

## Combination matrix

| Layer | What |
|---|---|
| A singles | each low → BUY_LOW only |
| B singles | each high → SELL_HIGH only |
| C cross | every low × every high (buy gate × sell gate) |
| D aggregate | `BUY_OR_ALL`, `BUY_MAJ3`, `SELL_OR_ALL`, `SELL_MAJ3`, `AND_RSI_BB_K` |

Anchors: `FIN_EQUAL`, `LIVE_KD_OPT`.

## Gates

Tip YTD+1y PASS + held-out score &gt; 0 vs EQUAL; beat-live = tip-clean and held-out &gt; live KD_OPT.

## Artifacts

- Script: `scripts/e16_indicator_combo_catalog_screen.py`  
- Catalog helper: `scripts/ta_indicator_catalog.py`  
- Results: `research/ops/INDICATOR_COMBO_CATALOG_SCREEN_R3.md` (+ `.json`)  
- Repro: `repro/indicator-combo-catalog-r3/`

## Non-actions

No Soft-Frozen / KD_OPT / TEL live change · no E45 stitch · no auto cutover from screen green.

## Label

`INDICATOR_COMBO_CATALOG_R3_2026-09-10__FINITE_MARKET_TA__BUY_X_SELL__PAPER_ONLY`
