# Within-sleeve 公股金／電信微調 × Soft+Sleeve+COOL — 紙上憲章 Stage A

日期：2026-09-25  
狀態：**PAPER STAGE A OPEN** · Soft-Frozen tip **KEEP** · 不上 live  
Live：Soft-Frozen **F[0.60,0.80] T[0.03,0.35] E[0.00,0.50]** + Soft sell + Sleeve RSI14 α=0.225 + `COOL_c8` + FUSE  
Within-sleeve：FIN=`KD_OPT`（Apr15–May15 K\<30 T−15）· TEL=`TEL_EQUAL`  
研究順序：β densify clip LIVE（#284）之後 — **只動袖內微調**（不動 clip · 不混公+民）

標籤：`WITHIN_SLEEVE_COOL_MICRO_STAGEA_CHARTER_2026-09-25__OPEN__NO_LIVE_WIRE`

## 理念

Soft-Frozen **clip** 與 **COOL** 凍結。問有限的 FinPub KD 季窗／電信配置微調，能否在 live Soft+Sleeve+COOL 下 tip-clean 抬 held CAGR。

## 問題

相對 `BASE_LIVE_FUSE_COOL`，有限袖內挑戰者能否同時：

1. held CAGR ≥ base **+0.20pp**  
2. held MDD↑ ≥ **0**  
3. tip YTD／1y MDD↑ ≥ **0**  
4. held \|MDD\| ≤ **15%**

## 禁止

不動 Soft-Frozen tip／clip；不混民股；不調 COOL／DH；Stage A 不上 live。

## 有限網格

- **FIN_KD_MICRO**（TEL 維持 EQUAL）：12 本 — 季窗 {Apr15–May15, May1–May31, Apr1–May15} × K∈{25,30,35} × T−∈{10,15,20} 子集；**排除** live `KD_OPT` 完全重複。  
- **TEL_MICRO**（FIN 維持 KD_OPT）：`TEL_RS_SOFT`／`TEL_MIN_LOT`／`TEL_RS_SOFT_EXDIV`／`TEL_TOP2`（跳過 EQUAL 對照）。

腳本：`scripts/within_sleeve_cool_micro_stagea.py`  
復現：`repro/within-sleeve-cool-micro-stagea/`

## 裁決

`WITHIN_SLEEVE_MICRO_HIT`／`CAGR_SOFT`／`HELD_FLAT_TIP_FAIL`／`NO_FLAT_LIFT`  
HIT → 只開 paper observe；live KD／TEL 翻轉要獨立 ACCEPT。
