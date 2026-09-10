# 指標買賣機制 Charter — 第一輪 Screen

日期：2026-09-10  
狀態：**OPEN／僅 paper**  
人令：**「請開指標買賣 charter 並先做第一輪 screen」**  
Soft-Frozen **[0.60, 0.90] KEEP** · live **KD_OPT + TEL_EQUAL** KEEP · E45 stitch **OFF**

## 目的

在 **不改 live** 前提下，測試各類技術指標（相對現行 TAIEX regime + Yahoo K9）能否改善 **MDD** 與 **投報／tip giveback**。

屬 **新機制** 路線，**不是** FIN within-sleeve KD 微調重開。

## Round-1 範圍

- Soft-Frozen sleeve 固定；電信 **`TEL_EQUAL`**
- 只換 **金融四檔** 的分數／買入閘（RSI／MACD／均線／布林／量能等）
- Exact T+1 · 500M · lot 1000
- 錨點：`FIN_EQUAL` · `LIVE_KD_OPT` · `FIN_RS_SOFT_TILT_EXDIV`

## 通過條件

Tip YTD+1y **PASS** 且 held-out score **&gt; 0**；若還要談 live，須 **不差於** `LIVE_KD_OPT`。

## 禁止

- 不改 Soft-Frozen／live KD_OPT／TEL_EQUAL  
- 不 stitch E45  
- 不因 screen 綠燈自動上 live  

全文：`INDICATOR_BUY_SELL_CHARTER.md`
